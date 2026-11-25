"""Replay 06: cash-funded ETF trend rules; no broker access."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

import numpy as np

import rig2 as rig


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = Path("/home/user/workspace/rig/data/funds_daily")
CONFIG = "config/thresholds.yaml"
PLAN = "research_rig/PREREG_06_fund_trend_paid_data.md"
DRAFT = PLAN.replace(".md", "_DRAFT.md")
LEDGER = "research_rig/TRIAL_LEDGER.md"
AUDIT = "research_rig/fund_adjustments_06.json"
RULES = ("G1", "G2", "G3", "G4", "G5", "G6")
MONTHLY = {"G1", "G3", "G4", "G5"}
KEYS = (*rig.thresholds_used(), "replay_06_data", "replay_06_rules", "replay_06_statistics",
        "cost_model_bps_per_side_liquid_etf", "practice_rebalance_band",
        "replay_07_statistics", "replay_09_statistics")
NY = ZoneInfo("America/New_York")
BPS = 10_000


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def has_ledger_rows(ledger):
    rows = [re.split(r"\s*\|\s*", line.strip("| ")) for line in ledger.splitlines()
            if line.startswith("|") and PLAN.rsplit("/", 1)[1] in line
            and "_DRAFT" not in line]
    found = set()
    for row in rows:
        if len(row) >= 4 and re.match(r"^\d+(?:\s|$)", row[0].strip()):
            found.update(re.findall(r"\bG[1-6]\b", " ".join(row[2:])))
            if re.search(r"\bG1\s+(?:to|through)\s+G6\b", " ".join(row[2:])):
                found.update(RULES)
    return found == set(RULES)


def authorize(repo, held=False, commit=None):
    if (repo / DRAFT).exists() or not (repo / PLAN).is_file():
        raise ValueError("Builder must rename the draft and freeze replay 06 before any real run.")
    if not has_ledger_rows((repo / LEDGER).read_text()):
        raise ValueError("Frozen replay 06 needs ledger rows naming G1 through G6.")
    if not held:
        return None
    if not commit:
        raise ValueError("--held requires --prereg-commit from the builder.")
    commit = git("rev-parse", "--verify", commit + "^{commit}")
    if not git("branch", "-r", "--contains", commit):
        raise ValueError("Preregistration commit is not on a locally known remote branch.")
    if git("show", f"{commit}:{PLAN}") != (repo / PLAN).read_text().strip():
        raise ValueError("Working plan differs from the pushed copy.")
    if not has_ledger_rows(git("show", f"{commit}:{LEDGER}")):
        raise ValueError("Pushed preregistration is missing the replay 06 ledger rows.")
    frozen = rig.yaml.safe_load(git("show", f"{commit}:{CONFIG}"))
    if any(frozen[k]["value"] != rig.th(k) for k in KEYS):
        raise ValueError("Working configuration differs from the pushed replay settings.")
    calibration = repo / AUDIT
    if git("show", f"{commit}:{AUDIT}") != calibration.read_text().strip():
        raise ValueError("Working adjustment calibration differs from the pushed calibration.")
    return commit


def reserve_holdout(folder, output, commit):
    if output.exists():
        raise FileExistsError("Replay 06 held result already exists; do not rerun.")
    # An attempt that errors is still an attempt. Never automatically delete this lock.
    path = folder / "replay06_held_attempt.json"
    with path.open("x") as handle:
        json.dump(dict(started=datetime.now(timezone.utc).isoformat(), prereg_commit=commit), handle)


@dataclass(frozen=True)
class Market:
    dates: tuple
    symbols: tuple
    opening: np.ndarray
    close: np.ndarray


def read_market(folder, end, data):
    from exchange_calendars import get_calendar

    start = data["first_bar"]
    # Calendar may look beyond the last bar; prices may not.
    cal = get_calendar("XNYS", start=start, end=end[:4] + "-12-31")
    schedule = tuple(d.date().isoformat() for d in cal.sessions)
    expected = tuple(d for d in schedule if start <= d <= end)
    symbols = tuple(data["symbols"])
    opens, closes, hashes = [], [], {}
    for sym in symbols:
        path = folder / f"{sym}.all.json"
        raw = path.read_bytes()
        page = json.loads(raw)
        if page["next_page_token"] is not None:
            raise ValueError(f"Input is paginated: {sym}")
        stamps, op, cl = [], [], []
        for bar in page["bars"][sym]:
            if bar["t"][:10] > end:
                break
            ny = datetime.fromisoformat(bar["t"]).astimezone(NY)
            if any((ny.hour, ny.minute, ny.second, ny.microsecond)):
                raise ValueError(f"Off-grid NY date: {sym} {bar['t']}")
            day = ny.date().isoformat()
            o, h, l, c, v = (bar[key] for key in ("o", "h", "l", "c", "v"))
            if (not np.isfinite((o, h, l, c, v)).all() or min(o, h, l, c, v) <= 0
                    or h < max(o, l, c) or l > min(o, h, c)):
                raise ValueError(f"Invalid or nontraded OHLCV: {sym} {day}")
            stamps.append(day)
            op.append(o)
            cl.append(c)
        if tuple(stamps) != expected:
            raise ValueError(f"NYSE session mismatch: {sym}")
        hashes[sym] = dict(file=path.name, sha256=hashlib.sha256(raw).hexdigest(),
                           used_rows=len(stamps), first=stamps[0], last=stamps[-1])
        split_path = folder / f"{sym}.split.json"
        hashes[sym]["audit_split_sha256"] = digest(split_path)
        opens.append(op)
        closes.append(cl)
    last_ms = {a for a, b in zip(schedule, schedule[1:]) if a[:7] != b[:7]}
    return Market(expected, symbols, np.asarray(opens).T, np.asarray(closes).T), last_ms, hashes


def one(n, i):
    v = np.zeros(n)
    v[i] = 1
    return v


def targets(market, start, stop, month_ends, p, cash_symbol):
    """Return sparse next-session target instructions, indexed by fill day."""
    dates = market.dates
    c = market.close
    sym = market.symbols
    n = len(sym)
    sp, bond, bill = (sym.index(s) for s in ("SPY", "IEF", cash_symbol))
    core = tuple(sym.index(s) for s in p["g1_g2_funds"])
    universe = tuple(i for i in range(n) if i != bill)
    monthly = [i for i, d in enumerate(dates[:stop]) if d in month_ends]
    monthly_pos = {i: j for j, i in enumerate(monthly)}
    n_sleeves = {"G1": len(core), "G2": len(core)}
    ids = (*RULES, "SPY", "HOLD_CORE", "HOLD_ALL", "SPY_IEF")
    out = {r: np.full((stop - start, n_sleeves.get(r, 1), n), np.nan) for r in ids}
    vector = lambda ix: sum((one(n, i) for i in ix), np.zeros(n)) / len(ix)
    static = {"G6": p["g6_spy_weight"] * one(n, sp) + (1 - p["g6_spy_weight"]) * one(n, bond),
              "SPY": one(n, sp), "HOLD_CORE": vector(core), "HOLD_ALL": vector(universe),
              "SPY_IEF": vector((sp, bond))}
    for i in range(start, stop):
        k = i - start
        prior = i - 1
        if prior < 0:
            raise ValueError("Must have a preceding session for the first decision.")
        if k == 0 or dates[i][:4] != dates[prior][:4]:
            for r, weight in static.items():
                if r != "SPY" or k == 0:
                    out[r][k, 0] = weight
        for j, asset in enumerate(core):
            basket = p["ensemble_sessions"]
            if prior + 1 < max(basket):
                raise ValueError("Insufficient daily warm-up.")
            f = sum(c[prior, asset] > c[prior - d + 1:prior + 1, asset].mean()
                    for d in basket) / len(basket)
            out["G2"][k, j] = f * one(n, asset) + (1 - f) * one(n, bill)
        if k != 0 and prior not in monthly_pos:
            continue
        if k == 0:
            eligible = [m for m in monthly if m <= prior]
            if not eligible:
                raise ValueError("Missing first month-end decision.")
            prior = eligible[-1]
        pos = monthly_pos[prior]
        window, look = p["trend_months"], p["momentum_months"]
        if pos < max(window - 1, look):
            raise ValueError("Insufficient monthly warm-up.")
        trend = c[prior] > c[monthly[pos - window + 1:pos + 1]].mean(axis=0)
        momentum = c[prior] / c[monthly[pos - look]] - 1
        for j, asset in enumerate(core):
            out["G1"][k, j] = one(n, asset if trend[asset] else bill)
        out["G3"][k, 0] = one(n, sp if momentum[sp] > momentum[bill] else bond)
        out["G4"][k, 0] = one(n, sp if trend[sp] else bill)
        ranked = sorted((a for a in universe if trend[a]), key=lambda a: (-momentum[a], sym[a]))
        slots = p["leader_slots"]
        picks = ranked[:slots]
        out["G5"][k, 0] = vector(picks + [bill] * (slots - len(picks)))
    return out


def rebalance(old, cash, target, rate):
    """Find post-fee capital at target weights; credit sells before funding buys."""
    pre = old.sum() + cash
    post = pre
    for _ in range(100):
        delta = target * post - old
        following = pre - rate * np.abs(delta).sum()
        if abs(following - post) <= 1e-13 * pre:
            post = following
            break
        post = following
    else:
        raise ValueError("Could not allocate cash after fees.")
    goal = target * post
    order = goal - old
    sells = -np.minimum(order, 0).sum()
    buys = np.maximum(order, 0).sum()
    left = cash + sells * (1 - rate) - buys * (1 + rate)
    if left < -1e-11 * pre:
        raise ValueError("Unfunded buy.")
    return goal, max(0.0, left), order


def simulate(plan, opening, close, bill, bps, band=None, fixed=None, late=False):
    periods, sleeves, assets = plan.shape
    eq = np.ones(periods + 1)
    weights = np.zeros((periods, assets))
    fill = close if late else opening
    shares = np.zeros((sleeves, assets))
    cash = np.full(sleeves, 1 / sleeves)
    instructions = np.zeros((periods, sleeves), dtype=bool)
    sides, turnover = 0, 0.0
    for i in range(periods):
        for j in np.flatnonzero(np.isfinite(plan[i, :, 0])):
            target = plan[i, j]
            if fixed is not None and not fixed[i, j]:
                continue
            if band is not None and i and fixed is None:
                past = shares[j] * close[i - 1]
                old_w = past / (past.sum() + cash[j])
                if np.max(np.abs(target - old_w)) <= band + 1e-12:
                    continue
            instructions[i, j] = True
            value = shares[j] * fill[i]
            goal, cash[j], order = rebalance(value, cash[j], target, bps / BPS)
            shares[j] = goal / fill[i]
            sides += int((np.abs(order) > rig.DUST * eq[i]).sum())
            turnover += np.abs(order).sum() / eq[i]
        marks = shares.sum(axis=0) * close[i]
        eq[i + 1] = cash.sum() + marks.sum()
        weights[i] = marks / eq[i + 1]
    return dict(eq=eq, sides=sides, turnover=turnover, weight=weights.mean(axis=0),
                risk_weight=float((weights.sum(axis=1) - weights[:, bill]).mean()),
                instructions=instructions)


HOLD = dict(G1="HOLD_CORE", G2="HOLD_CORE", G3="SPY", G4="SPY", G5="HOLD_ALL", G6="SPY")


class Slice:
    def __init__(self, market, start, end, month_ends, cfg):
        i, j = market.dates.index(start), market.dates.index(end) + 1
        self.dates = market.dates[i:j]
        self.open, self.close = market.opening[i:j], market.close[i:j]
        self.symbols = market.symbols
        self.bill = market.symbols.index(cfg["data"]["cash_fund"])
        self.rf = market.close[i:j, self.bill] / market.close[i - 1:j - 1, self.bill] - 1
        self.plan = targets(market, i, j, month_ends, cfg["rules"], cfg["data"]["cash_fund"])
        self.cost, self.band, self.ppy = cfg["cost"], cfg["band"], cfg["ppy"]
        self.base = {r: self.run(r, self.cost) for r in self.plan}

    def run(self, r, cost, fixed=None, late=False, plan=None):
        return simulate(self.plan[r] if plan is None else plan, self.open, self.close, self.bill,
                        cost, self.band if r == "G2" else None, fixed=fixed, late=late)

    def metrics(self, row):
        return dict(rig.metrics(row["eq"], ppy=self.ppy, rf=self.rf), sides=row["sides"],
                    turnover_py=row["turnover"] * self.ppy / len(self.dates),
                    risk_weight=row["risk_weight"],
                    average_weights=dict(zip(self.symbols, row["weight"].tolist())))

    @lru_cache(maxsize=None)
    def priced(self, r, cost, late=False):
        if cost == self.cost and not late:
            return self.metrics(self.base[r])
        return self.metrics(self.run(r, cost, self.base[r]["instructions"], late=late))

    def matched(self, r):
        weight = float(np.clip(self.base[r]["risk_weight"], 0, 1))
        p = self.plan[HOLD[r]].copy()
        mask = np.isfinite(p[:, :, 0])
        p[mask] *= weight
        p[:, :, self.bill][mask] += 1 - weight
        return self.metrics(simulate(p, self.open, self.close, self.bill, self.cost))


def cfg():
    return dict(data=rig.th("replay_06_data"), rules=rig.th("replay_06_rules"),
                stats=rig.th("replay_06_statistics"), null=rig.th("replay_09_statistics"),
                cost=rig.th("cost_model_bps_per_side_liquid_etf")[-1],
                ppy=rig.th("replay_07_statistics")["days_per_year"],
                band=rig.th("practice_rebalance_band"),
                multiple=rig.th("backtest_min_breakeven_cost_multiple"))


def timing(r, phases, config, rng):
    if r == "G6":
        return None
    span = config["stats"]["shuffle_min_monthly_shift" if r in MONTHLY else "shuffle_min_daily_shift"]
    draws = config["null"]["draws"]
    controls, audit = [], []
    for phase in phases:
        base = phase.plan[r]
        slots = np.flatnonzero(np.isfinite(base[:, 0, 0]))
        if len(slots) < 2 * span or np.all(base[slots] == base[slots[0]]):
            return None
        offsets = rng.integers(span, len(slots) - span + 1, size=draws)
        memo = {}
        for offset in set(offsets.tolist()):
            p = base.copy()
            p[slots] = np.roll(base[slots], offset, axis=0)
            row = phase.run(r, phase.cost, plan=p)
            memo[offset] = (row["eq"][-1], row["turnover"], row["risk_weight"], row["sides"])
        v = np.asarray([memo[k] for k in offsets])
        audit.append(dict(mean_turnover=float(v[:, 1].mean()), mean_risk_weight=float(v[:, 2].mean()),
                          mean_sides=float(v[:, 3].mean()), random_twin_total=float(v[0, 0] - 1)))
        controls.append(v[:, 0])
    actual = np.prod([p.base[r]["eq"][-1] for p in phases])
    null = np.prod(controls, axis=0)
    return dict(percentile=float(((null < actual) & ~np.isclose(null, actual, rtol=1e-12, atol=0)).mean()),
                matching="target timing rotations; realized turnover may differ", slices=audit)


def score(phases, config):
    cost = config["cost"]
    stress = cost * config["multiple"]
    result = {}
    for name, sl in phases.items():
        result[name] = dict(
            dates=[sl.dates[0], sl.dates[-1]], rules={
                r: dict(base=sl.priced(r, cost), at_zero_cost=sl.priced(r, 0),
                        at_stress_cost=sl.priced(r, stress), next_close=sl.priced(r, cost, True))
                for r in sl.plan},
            exposure_matched={r: sl.matched(r) for r in RULES})
    if "held" not in phases:
        return dict(slices=result, costs_bps_per_side=dict(base=cost, stress=stress, zero=0))
    windows = tuple(phases.values())
    dates = tuple(d for sl in windows for d in sl.dates)
    excess = {r: np.concatenate([rig.rets(sl.base[r]["eq"]) - sl.rf for sl in windows]) for r in RULES}
    srs = np.asarray([rig.sharpe_pp(excess[r]) for r in RULES])
    finite = srs[np.isfinite(srs)]
    spread = finite.std(ddof=1) if finite.size > 1 else np.nan
    starts = [config["data"]["design_start"], *config["stats"]["pbo_later_starts"]]
    blocks = config["null"]["pbo_blocks"]
    pbo = {}
    for start in starts:
        if start not in dates or len(dates) - dates.index(start) < 2 * blocks:
            pbo[start] = None
        else:
            at = dates.index(start)
            pbo[start] = rig.pbo_cscv(np.column_stack([excess[r][at:] for r in RULES]), S=blocks)
    worst = max(x["pbo"] for x in pbo.values()) if all(x is not None for x in pbo.values()) else None
    trials = config["stats"]["prior_count_at_draft"] + config["stats"]["new_trials"]
    rng = np.random.default_rng(config["null"]["seed"])
    marks = {}
    for r in RULES:
        def growth(name, bps):
            return np.prod([1 + sl.priced(name, bps)["total"] for sl in windows])
        be = rig.breakeven(lambda b: growth(r, b) - growth(HOLD[r], b))
        dsr, ref = rig.deflated_sharpe(excess[r], trials, spread)
        twin = timing(r, windows, config, rng)
        hold = result["held"]["rules"][HOLD[r]]["base"]
        actual = result["held"]["rules"][r]["base"]
        marks[r] = dict(primary=HOLD[r], break_even=be, deflated_sharpe=dsr, dsr_reference=ref,
                        shuffle=twin, marks=rig.five_marks(actual, hold, be, cost, dsr, worst,
                                                          None if twin is None else twin["percentile"]))
    return dict(slices=result, costs_bps_per_side=dict(base=cost, stress=stress, zero=0),
                rules=marks, pbo=pbo, max_pbo=worst, trial_count=trials, daily_sharpe_spread=spread)


def clean(obj):
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        return float(obj) if np.isfinite(obj) else None
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dev", action="store_true", help="Design only (default).")
    mode.add_argument("--held", action="store_true", help="One use only, builder runs.")
    mode.add_argument("--fixtures", action="store_true", help="Invented data only.")
    parser.add_argument("--prereg-commit")
    args = parser.parse_args()
    if args.fixtures:
        import fixtures_06
        return fixtures_06.run()
    if args.prereg_commit and not args.held:
        parser.error("--prereg-commit applies only with --held")
    commit = authorize(REPO, args.held, args.prereg_commit)
    config = cfg()
    d = config["data"]
    calibration = json.loads((REPO / AUDIT).read_bytes())
    checks = [*calibration["checks"].values(), calibration["iwm_additional_year"]]
    if (calibration["check_tolerance_bps"] != d["adjustment_max_error_bps"]
            or any(not np.isfinite(r["all_minus_issuer_bps"])
                   or abs(r["all_minus_issuer_bps"]) > d["adjustment_max_error_bps"] for r in checks)):
        raise ValueError("Fund adjustment calibration failed.")
    if config["stats"]["new_trials"] != len(RULES):
        raise ValueError("Frozen trial count does not match the configured rule list.")
    output = HERE / "results_06.json" if args.held else DATA / "results_06_design.json"
    if args.held:
        reserve_holdout(DATA, output, commit)
    from exchange_calendars import __version__ as calendar_version, get_calendar
    cal = get_calendar("XNYS", start=d["first_bar"], end=d["last_bar"])
    dev_end = max(t.date().isoformat() for t in cal.sessions if t.date().isoformat() < d["held_start"])
    end = d["last_bar"] if args.held else dev_end
    market, month_ends, hashes = read_market(DATA, end, d)
    phases = {"design": Slice(market, d["design_start"], dev_end, month_ends, config)}
    if args.held:
        phases["held"] = Slice(market, d["held_start"], end, month_ends, config)
    out = score(phases, config)
    out["provenance"] = dict(mode="held" if args.held else "design", prereg_commit=commit,
                             git_head=git("rev-parse", "HEAD"), input_files=hashes,
                             exchange_calendars_version=calendar_version,
                             sha256={str(p.relative_to(REPO)): digest(p) for p in
                                     (REPO / CONFIG, REPO / PLAN, REPO / LEDGER, REPO / AUDIT,
                                      HERE / "run_06.py", HERE / "fixtures_06.py", HERE / "rig2.py")},
                             thresholds={k: rig.th(k) for k in KEYS})
    with output.open("x" if args.held else "w") as handle:
        json.dump(clean(out), handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
