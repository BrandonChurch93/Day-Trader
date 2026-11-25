"""Replay the frozen Alpaca crypto methods. No orders, no keys, no live data."""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import rig2 as rig
from fetch_09_alpaca import ENDPOINT, HOME, INVENTORY, PAIRS, filename

HERE = Path(__file__).resolve().parent
PLAN = "research_rig/PREREG_09_crypto_methods.md"
LEDGER = "research_rig/TRIAL_LEDGER.md"
CONFIG = "config/thresholds.yaml"
RULES = ("ASIA", "WKND", "MOM", "REV", "LEAD", "VOL", "CAP")
SYMBOLS = tuple(sorted(rig.th("replay_09_basket")))
BTC = "BTC/USD"
DATES, CAL, LIQ, LEAD, VOL, CAP, STATS = [
    rig.th("replay_09_" + k) for k in ("dates", "calendar", "liquidity", "lead", "vol", "capit", "statistics")
]
TAKER_KEY, SPREAD_KEY = "practice_crypto_fee_bps_added", "tm_crypto_half_spread_bps"
FEE, SPREAD = rig.th(TAKER_KEY), rig.th(SPREAD_KEY)
COST = FEE + SPREAD
HOUR = pd.Timedelta(hours=1)
DAY = pd.Timedelta(days=1)
TAPE = HOME.parent.parent / "tm_store/tape.sqlite"


def fingerprint(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_bars(path, end, freq):
    limit = (pd.Timestamp(end) + DAY).strftime("%Y-%m-%d")
    chunks = []
    with pd.read_csv(path, chunksize=512, dtype={"t": "str"}) as reader:
        for frame in reader:
            keep = frame["t"] < limit
            chunks.append(frame.loc[keep])
            if not keep.all():
                break
    bars = pd.concat(chunks, ignore_index=True)
    bars["t"] = pd.to_datetime(bars["t"], format="ISO8601", utc=True).dt.tz_convert(None)
    bars = bars.set_index("t")
    n = len(bars)
    if not n:
        return bars, dict(rows=0, sha256=fingerprint(path))
    if not bars.index.is_monotonic_increasing or not bars.index.is_unique:
        raise ValueError(f"unsorted or duplicate bars: {path.name}")
    if not bars.index.floor(freq).equals(bars.index):
        raise ValueError(f"off-grid bars: {path.name}")
    prices, v = bars[["o", "h", "l", "c"]], bars["v"]
    valid = (np.isfinite(prices).all(axis=1) & (prices > 0).all(axis=1) & np.isfinite(v) & (v >= 0)
             & (bars.h >= bars[["o", "c", "l"]].max(axis=1))
             & (bars.l <= bars[["o", "c", "h"]].min(axis=1)))
    if not valid.all():
        raise ValueError(f"invalid OHLC or volume: {path.name}: {(~valid).sum()}")
    stride = pd.Timedelta(freq)
    gaps = (bars.index.to_series().diff().dropna() // stride - 1).astype(int)
    return bars, dict(rows=n, first=str(bars.index[0]), last=str(bars.index[-1]),
                      internal_missing=int(gaps.sum()), longest_internal_gap=int(gaps.max()) if len(gaps) else 0,
                      zero_volume=int((v == 0).sum()), sha256=fingerprint(path))


def input_path(folder, sym, tf):
    path = filename(folder, sym, tf)
    if not path.exists() and sym in SYMBOLS and tf == "1Hour":
        alternate = filename(folder / "replay_window", sym, tf)
        if alternate.exists():
            return alternate
    return path


def data(folder, end, symbols):
    audit = {}
    samples = {"1Day": {}, "1Hour": {}}
    for tf, stride in (("1Day", "1D"), ("1Hour", "1h")):
        for sym in symbols:
            path = input_path(folder, sym, tf)
            if not path.exists() and sym not in SYMBOLS:
                audit.setdefault(sym, {})[tf] = dict(status="not yet downloaded")
                continue
            source, notes = read_bars(path, end, stride)
            notes["status"] = "replay window only" if path.parent.name == "replay_window" else "full query"
            notes["file"] = str(path.relative_to(folder))
            if sym in SYMBOLS:
                if source.empty:
                    raise ValueError(f"required input missing: {sym} {tf}")
                samples[tf][sym] = source
            audit.setdefault(sym, {})[tf] = notes
            if not source.empty:
                recent = source.loc[:end].tail(LIQ["days"]) if tf == "1Day" else None
                if recent is not None and len(recent) == LIQ["days"]:
                    previous = pd.date_range(pd.Timestamp(end) - (LIQ["days"] - 1) * DAY, end, freq="D")
                    notes["recent_daily_liquidity_screen"] = bool(
                        recent.index.equals(previous) and float((recent.c * recent.v).median()) >= LIQ["min_median_usd"]
                    )
    return samples, audit


def tape_audit(end):
    """Coverage only; the tape is not a replay input."""
    until = int((pd.Timestamp(end, tz="UTC") + DAY).timestamp())
    rows = []
    with sqlite3.connect(f"{TAPE.as_uri()}?mode=ro", uri=True) as conn:
        for sym in SYMBOLS:
            for tf, stride in (("1Min", 60), ("1Day", 86400)):
                count, first, last, zero = conn.execute(
                    "SELECT count(*),min(t),max(t),sum(v=0) FROM bars WHERE symbol=? AND tf=? AND t<?",
                    (sym, tf, until),
                ).fetchone()
                if not count:
                    continue
                stamp = lambda t: datetime.fromtimestamp(t, timezone.utc).isoformat()
                rows.append(dict(symbol=sym, frame=tf, rows=count, first=stamp(first), last=stamp(last),
                                 internal_missing=(last - first) // stride + 1 - count, zero_volume=zero))
    return rows


@dataclass(frozen=True)
class Cycle:
    entries: tuple
    actual: int
    duration: int
    bound: int


@dataclass(frozen=True)
class Fill:
    symbol: str
    weight: float
    start: int
    end: int | None
    buy: float
    sell: float


def cycles(rule, index):
    days = pd.date_range(index[0].normalize(), index[-1].normalize(), freq="D")
    weekly = rule in ("WKND", "MOM", "VOL")
    anchors = days[days.day_of_week == 0]
    if weekly and days[0].day_of_week:
        anchors = anchors.insert(0, days[0] - days[0].day_of_week * DAY)
    if rule == "ASIA":
        offsets, actual, dur, interval = (CAL["asia_control_entries"], CAL["asia_entry"], CAL["asia_hours"], 24)
    elif rule == "WKND":
        offsets = [d * 24 + CAL["daily_entry"] for d in CAL["weekend_control_days"]]
        actual, dur, interval = CAL["weekend_day"] * 24 + CAL["daily_entry"], CAL["weekend_hours"], 168
    elif rule in ("MOM", "VOL"):
        offsets, actual, dur, interval = [CAL["daily_entry"]], CAL["daily_entry"], CAL["weekly_hours"], 168
    elif rule in ("REV", "CAP"):
        offsets, actual, dur, interval = ([CAL["daily_entry"]], CAL["daily_entry"],
                                          CAL["daily_exit"] - CAL["daily_entry"], 24)
    else:
        offsets, actual, dur, interval = [0], 0, LEAD["hold_hours"], LEAD["every_hours"]
    if not weekly:
        anchors = index[::interval] if rule == "LEAD" else days
    pos = lambda t: int((t - index[0]) // HOUR)
    return [Cycle(tuple(pos(d) + k for k in offsets if 0 <= pos(d) + k < len(index)),
                  pos(d) + actual, dur, min(len(index) - 1, pos(d) + interval + min(offsets)))
            for d in anchors]


def signals(bars, end):
    days = pd.date_range(min(x.index[0] for x in bars["1Day"].values()), end, freq="D")
    closes = pd.DataFrame({s: bars["1Day"][s].c for s in SYMBOLS}, index=days)
    volume = pd.DataFrame({s: bars["1Day"][s].v for s in SYMBOLS}, index=days)
    ret = closes.pct_change(fill_method=None)
    available = ((closes * volume).rolling(LIQ["days"]).median() >= LIQ["min_median_usd"])
    n = CAL["momentum_days"]
    mom = closes.pct_change(n, fill_method=None).where(closes.rolling(n + 1).count() == n + 1)
    vol = ret[BTC].rolling(VOL["lookback_days"]).std()
    caps = volume[BTC].shift().rolling(LIQ["days"]).median()
    capit = ((caps > 0) & (volume[BTC] >= CAP["min_volume_multiple"] * caps)
             & (ret[BTC] <= CAP["max_daily_return"]))
    opening = bars["1Hour"]
    moves = pd.DataFrame({s: (opening[s].c / opening[s].o - 1).where(opening[s].v > 0)
                          for s in (BTC, *LEAD["symbols"])})
    # All indexed daily signal rows are moved one day forward. Hourly changes are separately lagged.
    return dict(mom=mom.where(available).shift(), rev=ret.where(available).shift(), vol=vol.shift(),
                cap=capit.shift(fill_value=False), lead=moves)


def decision(rule, t, sig):
    day = t.normalize()
    if rule in ("ASIA", "WKND"):
        return BTC, 1.0
    if rule in ("MOM", "REV"):
        row = sig[rule.lower()].loc[day].dropna()
        if not row.empty:
            return (row.idxmax() if rule == "MOM" else row.idxmin()), 1.0
    if rule == "LEAD":
        lags = sig["lead"]
        at = t - LEAD["signal_lag_bars"] * HOUR
        if at in lags.index and lags.at[at, BTC] > LEAD["btc_min_return"]:
            row = lags.loc[at, sorted(LEAD["symbols"])].dropna()
            row = row[row <= LEAD["alt_max_return"]]
            if not row.empty:
                return row.idxmin(), 1.0
    if rule == "VOL":
        sd = sig["vol"].at[day]
        if np.isfinite(sd):
            return BTC, min(1.0, VOL["target_daily_sd"] / sd) if sd else 1.0
    if rule == "CAP" and sig["cap"].at[day]:
        return BTC, 1.0
    return None


class Market:
    def __init__(self, bars, start, end):
        self.index = pd.date_range(start, pd.Timestamp(end) + DAY - HOUR, freq="h")
        self.opens, self.marks, self.traded = {}, {}, {}
        for sym, frame in bars.items():
            live = frame.reindex(self.index)
            self.opens[sym] = live.o.to_numpy()
            self.marks[sym] = frame.c.reindex(self.index, method="ffill").to_numpy()
            self.traded[sym] = np.flatnonzero(live.v.to_numpy() > 0)

    def is_traded(self, sym, i):
        indices = self.traded[sym]
        n = np.searchsorted(indices, i)
        return n < len(indices) and indices[n] == i

    def fill(self, sym, weight, at, exit_at):
        if not self.is_traded(sym, at):
            return None
        marks, indices, opens = self.marks[sym], self.traded[sym], self.opens[sym]
        j = np.searchsorted(indices, exit_at)
        end = int(indices[j]) if j < len(indices) else None
        sell = float(opens[end] if end is not None else marks[-1])
        return Fill(sym, weight, at, end, float(opens[at]), sell)


def fit_fills(rule, market, sig):
    all_cycles = cycles(rule, market.index)
    fills, next_free = [], 0
    counts = dict(signal_count=0, entry_missed=0, delayed_exit=0, blocked_while_held=0)
    for cycle in all_cycles:
        at, exit_at = cycle.actual, cycle.actual + cycle.duration
        if at < 0 or exit_at >= len(market.index):
            continue
        pick = decision(rule, market.index[at], sig)
        if pick is None:
            continue
        counts["signal_count"] += 1
        if at < next_free:
            counts["blocked_while_held"] += 1
            continue
        fill = market.fill(*pick, at, exit_at)
        if fill is None:
            counts["entry_missed"] += 1
            continue
        fills.append(fill)
        counts["delayed_exit"] += int(fill.end != exit_at)
        next_free = len(market.index) if fill.end is None else fill.end
    return fills, all_cycles, counts


def costs(bps):
    fee, spread = bps * FEE / COST / 10000, bps * SPREAD / COST / 10000
    return (1 - fee) / (1 + spread), (1 - fee) * (1 - spread)


def terminal(fills, bps):
    buy_side, sell_side = costs(bps)
    return float(np.prod([1 + e.weight * (e.sell / e.buy * buy_side *
                         (sell_side if e.end is not None else 1.0) - 1) for e in fills]))


def equity(fills, market, bps):
    buy_side, sell_side = costs(bps)
    out = np.full(len(market.index), 1.0)
    cash, previous = 1.0, 0
    for e in fills:
        out[previous:e.start] = cash
        stop = len(out) if e.end is None else e.end
        residual = cash * (1 - e.weight)
        qty = cash * e.weight * buy_side / e.buy
        out[e.start:stop] = residual + qty * market.marks[e.symbol][e.start:stop]
        cash = residual + qty * e.sell * sell_side
        previous = stop
    out[previous:] = cash
    return np.r_[1.0, out[23::24]]


def metrics_for(fills, market):
    eq = equity(fills, market, COST)
    assert np.isclose(eq[-1], terminal(fills, COST))
    return dict(rig.metrics(eq), sides=sum(1 + (f.end is not None) for f in fills),
                closed=sum(f.end is not None for f in fills), open=sum(f.end is None for f in fills)), rig.rets(eq)


def windows(market, all_cycles, sym, duration):
    result = {}
    for j, cy in enumerate(all_cycles):
        for entry in cy.entries:
            exit_at = entry + duration
            if exit_at <= cy.bound and market.is_traded(sym, entry) and market.is_traded(sym, exit_at):
                result.setdefault(j, []).append(float(market.opens[sym][exit_at] / market.opens[sym][entry]))
    return result


def shuffled(fills, market, all_cycles, rng):
    """Reprice exactly matched completed tickets on random non-overlapping windows."""
    n = len(fills)
    draws = STATS["draws"]
    if not n:
        return np.ones(draws)
    if any(f.end is None for f in fills):
        return None
    category = [(f.symbol, f.end - f.start) for f in fills]
    pools = {c: windows(market, all_cycles, *c) for c in sorted(set(category))}
    k = len(all_cycles)
    if any(not v for v in pools.values()) or k < n:
        return None
    mask = np.zeros((n, k), dtype=bool)
    buy, sell = costs(COST)
    gross = np.full((n, k, max(len(c.entries) for c in all_cycles)), np.nan)
    lengths = np.zeros((n, k), int)
    for i, c in enumerate(category):
        for col, prices in pools[c].items():
            mask[i, col], lengths[i, col] = True, len(prices)
            gross[i, col, :len(prices)] = prices
    arr = np.arange(n)
    weights = np.asarray([f.weight for f in fills])
    out = []
    for _ in range(draws):
        for _ in range(64):
            order = rng.permutation(k)
            # Repair infeasible assignments by swapping windows, including spare cycles.
            for i in np.flatnonzero(~mask[arr, order[:n]]):
                if mask[i, order[i]]:
                    continue
                can = mask[i, order].copy()
                can[:n] &= mask[arr, order[i]]
                options = np.flatnonzero(can)
                if len(options):
                    j = rng.choice(options)
                    order[i], order[j] = order[j], order[i]
            selected = order[:n]
            if mask[arr, selected].all():
                alt = rng.integers(lengths[arr, selected])
                ratios = gross[arr, selected, alt]
                out.append(float(np.prod(1 + weights * (ratios * buy * sell - 1))))
                break
        else:
            return None
    return np.asarray(out)


def slice_run(bars, start, end):
    signal = signals(bars, end)
    market = Market(bars["1Hour"], start, end)
    result = {}
    for rule in RULES:
        fills, all_cycles, counts = fit_fills(rule, market, signal)
        metrics, daily = metrics_for(fills, market)
        result[rule] = dict(metrics=dict(metrics, **counts), daily=daily, cycles=all_cycles, fills=fills)
    first = int(market.traded[BTC][0])
    hold = market.fill(BTC, 1.0, first, len(market.index))
    metrics, daily = metrics_for([hold], market)
    result["HOLD"] = dict(metrics=metrics, daily=daily, fills=[hold])
    return result, market


def joined_return(phases, rule, bps):
    return float(np.prod([terminal(run[rule]["fills"], bps) for run in phases.values()]))


def score(phases, markets, marks):
    daily = {rule: np.concatenate([run[rule]["daily"] for run in phases.values()]) for rule in (*RULES, "HOLD")}
    sr = np.array([rig.sharpe_pp(daily[r]) for r in RULES])
    finite = sr[np.isfinite(sr)]
    spread = float(finite.std(ddof=1)) if len(finite) > 1 else float("nan")
    pbo = {}
    for start in DATES["pbo_starts"]:
        first = (pd.Timestamp(start) - markets["dev"].index[0]).days
        R = np.column_stack([daily[r][first:] for r in RULES])
        if len(R) >= STATS["pbo_blocks"] * 2:
            pbo[start] = rig.pbo_cscv(R, S=STATS["pbo_blocks"])
    max_pbo = max((v["pbo"] for v in pbo.values()), default=float("nan"))
    rng = np.random.default_rng(STATS["seed"])
    out = {}
    for rule in RULES:
        actual = joined_return(phases, rule, COST)
        null_slices = {name: shuffled(run[rule]["fills"], markets[name], run[rule]["cycles"], rng)
                       for name, run in phases.items()}
        known = not any(draws is None for draws in null_slices.values()) and any(p[rule]["fills"] for p in phases.values())
        if known:
            control = np.prod(list(null_slices.values()), axis=0)
            pct = float(((control < actual) & ~np.isclose(control, actual, atol=0, rtol=1e-12)).mean())
        else:
            pct = None
        be = rig.breakeven(lambda bps: joined_return(phases, rule, bps) - joined_return(phases, "HOLD", bps))
        dsr, sr0 = rig.deflated_sharpe(daily[rule], STATS["trial_count"], spread)
        row = {name: run[rule]["metrics"] for name, run in phases.items()}
        twins = {name: dict(total=float(draws[0] - 1), sides=row[name]["sides"])
                 for name, draws in null_slices.items() if draws is not None}
        if not any(p[rule]["fills"] for p in phases.values()):
            twins = {}
        row.update(break_even=be, dsr=dsr, deflated_reference_sharpe=sr0, shuffle_percentile=pct, twin=twins)
        if marks:
            row["marks"] = rig.five_marks(row["held"], phases["held"]["HOLD"]["metrics"], be,
                                           COST, dsr, max_pbo, pct)
        out[rule] = row
    return dict(rules=out, hold={name: run["HOLD"]["metrics"] for name, run in phases.items()},
                pbo=pbo, max_pbo=max_pbo, trial_sharpe_std_daily=spread)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=HERE.parent, text=True).strip()


def authorize(commit):
    if not commit:
        raise ValueError("--held requires --prereg-commit from the lead")
    commit = git("rev-parse", commit)
    if not git("branch", "-r", "--contains", commit):
        raise ValueError("preregistration commit is not on a locally known remote branch")
    text = git("show", f"{commit}:{PLAN}")
    if text != (HERE.parent / PLAN).read_text().strip():
        raise ValueError("working preregistration differs from pushed copy")
    ledger = git("show", f"{commit}:{LEDGER}")
    if f"| {STATS['first_trial_id']} to {STATS['first_trial_id'] + STATS['new_trials'] - 1} |" not in ledger:
        raise ValueError("pushed ledger does not include replay")
    yaml = rig.yaml.safe_load(git("show", f"{commit}:{CONFIG}"))
    keys = [*rig.thresholds_used(), TAKER_KEY, SPREAD_KEY]
    keys.extend("replay_09_" + s for s in ("dates", "basket", "calendar", "liquidity", "lead", "vol", "capit", "statistics"))
    if any(yaml[k]["value"] != rig.th(k) for k in keys):
        raise ValueError("working settings differ from pushed settings")
    return commit


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, (float, np.floating)) and not np.isfinite(x):
        return None
    return x


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dev", action="store_true")
    mode.add_argument("--held", action="store_true")
    parser.add_argument("--prereg-commit")
    args = parser.parse_args()
    folder = HOME
    modes = ("dev", "held") if args.held else ("dev",)
    end = DATES[modes[-1]][1]
    commit = authorize(args.prereg_commit) if args.held else None
    dev_result = HOME / "results_09_dev.json"
    output = HERE / "results_09.json" if args.held else dev_result
    manifest = {name: fingerprint(HERE / name) for name in ("run_09.py", "rig2.py", "fetch_09_alpaca.py", "fixtures_09.py")}
    if args.held:
        if output.exists():
            raise FileExistsError(output)
        if not dev_result.exists() or json.loads(dev_result.read_text())["provenance"]["code_sha256"] != manifest:
            raise ValueError("run and verify --dev on this version of the code first")
        pending = [input_path(folder, sym, frame) for sym in SYMBOLS for frame in ("1Day", "1Hour")
                   if not input_path(folder, sym, frame).exists()]
        if pending:
            raise FileNotFoundError(f"wait for {len(pending)} Alpaca files before opening held-back data")
    bars, coverage = data(folder, end, PAIRS if args.held else SYMBOLS)
    tape = tape_audit(end)
    phases, markets = {}, {}
    for s in modes:
        # The two independent simulations cannot read data after their own end.
        bounded = {f: {sym: frame.loc[:DATES[s][1]] for sym, frame in panels.items()} for f, panels in bars.items()}
        if s == "held":
            with (HOME / "replay_09_held_started.json").open("x") as marker:
                json.dump(dict(prereg_commit=commit, code_sha256=manifest, utc=datetime.now(timezone.utc).isoformat()), marker)
        phases[s], markets[s] = slice_run(bounded, *DATES[s])
    out = score(phases, markets, args.held)
    out.update(mode="held" if args.held else "dev", dates=DATES, stats=STATS, coverage=coverage, tape=tape,
               source=ENDPOINT, inventory=INVENTORY, symbols=SYMBOLS, thresholds=rig.thresholds_used(),
               liquidity=LIQ, fee={TAKER_KEY: FEE, SPREAD_KEY: SPREAD, "total_bps": COST},
               provenance=dict(prereg_commit=commit, plan_path=PLAN, code_head=git("rev-parse", "HEAD"),
                               command=sys.argv, code_sha256=manifest,
                               completed_utc=datetime.now(timezone.utc).isoformat()))
    with output.open("x" if args.held else "w") as f:
        f.write(json.dumps(clean(out), indent=2, allow_nan=False) + "\n")
    print(output)


if __name__ == "__main__":
    main()
