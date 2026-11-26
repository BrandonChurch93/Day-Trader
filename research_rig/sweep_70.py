"""Plan 70 SEARCH ONLY. No vault, network, orders, or trade-level output."""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import numpy as np
import yaml
from numpy.lib.stride_tricks import sliding_window_view

from coverage_70 import HOUR_MS, ROOTS as ARCHIVES, WRONG_CLOSE_CLOCK, has_hour_close, read_snapshot


HERE = Path(__file__).resolve().parent
HOUR = 3600
START = 1577836800  # 2020-01-01 00:00 UTC
HALF = 1640995200   # 2022-01-01 00:00 UTC
STOP = 1704067200  # 2024-01-01 00:00 UTC, exclusive
HOURS = np.arange(START, STOP, HOUR, dtype=np.int64)
DAY = (HOURS - START) // 86400
UTC_HOUR = HOURS // HOUR % 24
WEEKEND = (HOURS // 86400 + 3) % 7 >= 5  # 1970-01-01 Thursday
HALF_INDEX = (HALF - START) // HOUR
ET = ZoneInfo("America/New_York")
DAYS = len(HOURS) // 24
YEARS = 4
ALLOWED = tuple("AAVE ADA AVAX BCH BNB BTC DOGE DOT ETH HBAR LINK LTC NEAR PEPE SHIB SOL SUI XLM XRP ZEC".split())
CUSTODY = Path("/home/user/workspace/rig/data")
MANIFEST_REL = Path("sweep_70/coverage.json")
GRID_PATH = "research_rig/GRID_70.json"
SETTINGS_PATH = "config/thresholds.yaml"
COVERAGE_PATH = "research_rig/COVERAGE_70.json"


def maintenance(t):
    dt = datetime.fromtimestamp(int(t), timezone.utc).astimezone(ET)
    return dt.weekday() == 4 and dt.hour == 17


MAINT = np.array([maintenance(t) for t in HOURS])
LONDON = ZoneInfo("Europe/London")
LONDON_CLOSE = np.array([datetime.fromtimestamp(int(t), timezone.utc).astimezone(LONDON).hour == 16
                         for t in HOURS])


def read_hour_rows(stream, start=START, stop=STOP, ticks_per_ms=1):
    """Yield each in-range physical row; None means the clocked hour is missing."""
    per_second = 1000 * ticks_per_ms
    for wire in stream:
        stamp, _, payload = wire.partition(b",")
        opening = int(stamp)
        if not start * per_second <= opening < stop * per_second:
            continue
        if opening % (HOUR_MS * ticks_per_ms):
            raise ValueError("unaligned retained hourly bar")
        i = (opening // per_second - start) // HOUR
        fields = [stamp, *payload.split(b",", 6)]
        if not has_hour_close(fields, opening, ticks_per_ms):
            yield i, None
            continue
        row = tuple(float(x) for x in fields[1:6])  # open, high, low, close, base volume
        if not all(map(math.isfinite, row)) or not (0 < row[2] <= min(row[0], row[3])
                                                  <= max(row[0], row[3]) <= row[1] and row[4] >= 0):
            raise ValueError("malformed retained bar")
        yield i, row


def load_frozen(root, manifest, config):
    if manifest != root / MANIFEST_REL:
        raise ValueError("not the allowed timestamp-only manifest path")
    if tuple(config["coins"]) != ALLOWED:
        raise ValueError("roster differs from hard allow-list")
    raw = read_snapshot(root, MANIFEST_REL)
    if hashlib.sha256(raw).hexdigest() != config["private_manifest_sha256"]:
        raise ValueError("not the preregistered timestamp-only manifest")
    roster = json.loads(raw)
    panel = np.full((len(config["coins"]), len(HOURS), 5), np.nan)
    kept = dict.fromkeys(config["coins"], 0)
    dropped = dict.fromkeys(config["coins"], 0)
    for j, coin in enumerate(config["coins"]):
        physical = set()
        for record in roster[coin]["files"]:
            tag = record["month"]
            y, m = map(int, tag.split("-"))
            if not (2020 <= y <= 2023 and 1 <= m <= 12):
                raise ValueError("only pre-vault monthly files may be opened")
            expected_name = f"{coin}USDT-1h-{tag}"
            rel = f"archives/data/spot/monthly/klines/{coin}USDT/1h/{expected_name}.zip"
            if record["path"] not in {f"{s}/{rel}" for s in ARCHIVES}:
                raise ValueError("not an allowlisted archive path")
            archive_bytes = read_snapshot(root, record["path"])
            if hashlib.sha256(archive_bytes).hexdigest() != record["sha256"]:
                raise ValueError("retained archive identity changed")
            seen = 0
            with ZipFile(BytesIO(archive_bytes)) as z, z.open(expected_name + ".csv") as stream:
                for i, row in read_hour_rows(stream):
                    if i in physical or not record["first_utc_seconds"] <= HOURS[i] <= record["last_utc_seconds"]:
                        raise ValueError("duplicate or unexpected retained row")
                    physical.add(i)
                    seen += 1
                    if row is None:
                        dropped[coin] += 1
                    else:
                        kept[coin] += 1
                        panel[j, i] = row
            if seen != record["rows"]:
                raise ValueError("pinned physical row count changed")
    counts = {"rows_kept_by_coin": kept, "rows_dropped_by_reason": {WRONG_CLOSE_CLOCK: sum(dropped.values())},
              "rows_dropped_by_reason_and_coin": {WRONG_CLOSE_CLOCK: dropped}}
    return panel, counts


def shift(x, n):
    out = np.full_like(x, np.nan, dtype=float)
    if n:
        out[:, n:] = x[:, :-n]
    else:
        out[:] = x
    return out


def trailing(x, n, reduce):
    out = np.full_like(x, np.nan, dtype=float)
    out[:, n:] = reduce(sliding_window_view(x, n, axis=1)[:, :-1, :], axis=-1)
    return out


@dataclass
class Tape:
    coins: list
    bars: np.ndarray
    hours: np.ndarray = None
    split: int = HALF_INDEX

    def __post_init__(self):
        if self.hours is None:
            self.hours, self.clock, self.weekend, self.maintenance, self.london = (
                HOURS, UTC_HOUR, WEEKEND, MAINT, LONDON_CLOSE)
        else:
            self.clock = self.hours // HOUR % 24
            self.weekend = (self.hours // 86400 + 3) % 7 >= 5
            self.maintenance = np.array([maintenance(t) for t in self.hours])
            self.london = np.array([datetime.fromtimestamp(int(t), timezone.utc).astimezone(LONDON).hour == 16
                                    for t in self.hours])
        if self.bars.shape != (len(self.coins), len(self.hours), 5):
            raise ValueError("time axis differs from tape")
        self.o, self.high, self.low, self.close, self.volume = self.bars.transpose(2, 0, 1)
        self.btc = self.coins.index("BTC")
        self.logc = np.log(self.close)
        self.c1 = shift(self.logc, 1)
        self.c2 = shift(self.logc, 2)
        self.h1, self.l1 = shift(np.log(self.high), 1), shift(np.log(self.low), 1)
        self.open_to_close1 = shift(np.log(self.close / self.o), 1)
        self.v1 = shift(self.volume, 1)
        self.ret_cache, self.ref_cache, self.exec_cache = {}, {}, {}
        self.missing = np.c_[np.zeros(len(self.coins), dtype=np.int64),
                            (~np.isfinite(self.o)).cumsum(axis=1)]

    def signal_valid(self, n):
        idx = np.arange(len(self.hours))
        return ((self.missing[:, idx] - self.missing[:, np.maximum(0, idx - n)]) == 0) & (idx >= n)

    def lag(self, n):
        if n not in self.ret_cache:
            self.ret_cache[n] = np.where(self.signal_valid(n + 1), self.c1 - shift(self.logc, n + 1), np.nan)
        return self.ret_cache[n]

    def ref(self, kind, n):
        key = (kind, n)
        if key not in self.ref_cache:
            seq, fn = {"max": (np.log(self.high), np.max), "min": (np.log(self.low), np.min),
                       "vol": (self.volume, np.mean)}[kind]
            self.ref_cache[key] = shift(trailing(seq, n, fn), 1)
        return self.ref_cache[key]

    def fill(self, hold):
        if hold not in self.exec_cache:
            gross = np.full_like(self.o, np.nan, dtype=float)
            length = len(self.hours) - hold
            idx = np.arange(length)
            eligible = self.missing[:, idx + hold + 1] == self.missing[:, idx]
            # No position or clock baseline straddles the CDE weekly maintenance hour.
            for h in range(hold + 1):
                eligible &= ~self.maintenance[idx + h]
            ratio = self.o[:, hold:] / self.o[:, :length] - 1
            gross[:, :length] = np.where(eligible, ratio, np.nan)
            baselines = []
            blocks = [(0, len(self.hours))]
            if self.split is not None:
                blocks.extend(((0, self.split), (self.split, len(self.hours))))
            for lo, hi in blocks:
                # For half blocks both entry and exit must be inside that block.
                b = gross[:, lo:hi - hold].copy()
                clock = self.clock[lo:hi - hold]
                samples = np.full((len(self.coins), 24), np.nan)
                for h in range(24):
                    matches = b[:, clock == h]
                    n = np.isfinite(matches).sum(axis=1)
                    np.divide(np.nansum(matches, axis=1), n, out=samples[:, h], where=n > 0)
                baselines.append(samples)
            self.exec_cache[hold] = (gross, baselines)
        return self.exec_cache[hold]


def score_signal(tape, rule):
    f, p, side = rule["family"], rule["parameters"], rule["side"]
    cut = p.get("threshold", 0.)
    if f in ("clock_after_move", "hourly_shock", "midnight_stop_run", "volume_shock"):
        strength = -side * tape.lag(p["lag"])
        ok = strength >= cut
        if f == "clock_after_move":
            ok &= (tape.clock == p["entry_hour"]) & (tape.weekend == (p["day_type"] == "weekend"))
        if f in ("hourly_shock", "midnight_stop_run", "volume_shock"):
            with np.errstate(invalid="ignore", divide="ignore"):
                prior = tape.ref("vol", p["volume_lookback"])
                ratio = tape.v1 / prior
            ok &= (prior > 0) & (ratio >= p["ratio"])
        if f == "midnight_stop_run":
            pierce = (tape.l1 < tape.ref("min", p["lag_range"]) if side == 1
                      else tape.h1 > tape.ref("max", p["lag_range"]))
            ok &= (tape.clock == 0) & pierce
    elif f == "london_brr_fade":
        strength = -side * tape.open_to_close1
        ok = (strength >= cut) & tape.london
        ok[np.arange(len(tape.coins)) != tape.btc] = False
    elif f == "btc_overextension_fade":
        signed = -side * tape.lag(p["lag"])
        direction = signed[tape.btc]
        strength = signed - p["multiple"] * direction
        ok = (direction >= cut) & (strength > 0)
        ok[tape.btc] = False
    elif f in ("bitcoin_lead", "hedged_relative"):
        lag = tape.lag(p["lag"])
        rel = side * (lag - lag[tape.btc])
        if f == "bitcoin_lead":
            direction = side * lag[tape.btc]
            ok = (direction >= cut) & (side * lag <= p["fraction"] * direction)
            strength = -rel
        else:
            strength = rel
            ok = rel >= cut
        ok[tape.btc] = False
    elif f in ("range_rejection", "round_rejection"):
        if f == "range_rejection":
            level = tape.ref("min" if side == 1 else "max", p["lag"])
        else:
            prev = np.exp(tape.c2)
            step = p["multiple"] * 10 ** np.floor(np.log10(prev))
            with np.errstate(invalid="ignore", divide="ignore"):
                level = np.log(np.floor(prev / step + .5) * step)
        strength = side * (tape.c1 - level)
        pierce = tape.l1 < level if side == 1 else tape.h1 > level
        ok = pierce & (strength >= cut)
    elif f == "_always_long_fixture":
        return np.where(np.isfinite(tape.c1), 1., np.nan)
    else:
        raise ValueError("unknown preregistered family")
    return np.where(ok & np.isfinite(strength), strength, np.nan)


def order_times(tape, rule, signal):
    hold = rule["hold_hours"]
    # Rank as-of signal only, then take one gross-1x ticket. Do not choose
    # another coin using exit observability or exit prices.
    signal = np.where(np.isfinite(signal), signal, -np.inf)
    j = np.argmax(signal, axis=0)  # coins sorted; stable ties
    n = len(tape.hours)
    valid_clock = np.ones(n, dtype=bool)
    for h in range(hold + 1):
        valid_clock[:n - h] &= ~tape.maintenance[h:]
    valid_clock[n - hold:] = False
    schedule = np.flatnonzero(np.isfinite(signal[j, np.arange(n)]) & valid_clock)
    accepted = []
    next_free = 0
    for i in schedule:
        if i < next_free:
            continue
        accepted.append(i)
        next_free = i + hold
    times = np.array(accepted, dtype=np.int64)
    return j[times], times


def t_cluster(x, day):
    if len(x) < 2:
        return None
    cnt = np.bincount(day)
    groups = np.count_nonzero(cnt)
    if groups < 2:
        return None
    scale = float(np.max(np.abs(x)))
    if not scale or not np.isfinite(scale):
        return None
    scaled = x / scale
    mean = float(scaled.mean())
    sums = np.bincount(day, weights=scaled - mean, minlength=len(cnt))
    if np.max(np.abs(sums)) <= np.finfo(float).eps * cnt.max():
        return None
    se = math.sqrt(groups / (groups - 1) * (sums @ sums)) / len(x)
    return mean / se


def mean_or_null(x):
    return float(x.mean()) if len(x) else None


def too_thin(n, active_days, half_days, marks):
    return (n < marks["min_trades"] or active_days < marks["min_days"]
            or any(d < marks["min_days_each_half"] for d in half_days))


def registered_marks(plain, full_t, halves, trimmed, annual, marks):
    return (plain is not None and plain > 0
            and full_t is not None and full_t >= marks["full_t"]
            and all(h is not None and h >= marks["half_t"] for h in halves)
            and trimmed is not None and trimmed > 0 and annual >= marks["annual_min"])


def ticket_legs(tape, rule, costs, funding):
    side, hold = rule["side"], rule["hold_hours"]
    hedge = rule["btc_hedge"]
    j, i = order_times(tape, rule, score_signal(tape, rule))
    gross, baselines = tape.fill(hold)
    known = np.isfinite(gross[j, i])
    if hedge:
        known &= np.isfinite(gross[tape.btc, i])
    unresolved = int((~known).sum())
    j, i = j[known], i[known]
    signs = side * gross[j, i]
    fixed = costs[j]
    if hedge:
        signs = .5 * (signs - side * gross[tape.btc, i])
        fixed = .5 * (fixed + costs[tape.btc])
    net = signs - (fixed + hold * funding) / 10000

    def adjust(which, loc):
        c, ix = j[loc], i[loc]
        b = side * baselines[which][c, tape.clock[ix]]
        if hedge:
            b = .5 * (b - side * baselines[which][tape.btc, tape.clock[ix]])
        return b

    whole = np.ones(len(i), dtype=bool)
    reference = adjust(0, whole)
    if not np.all(np.isfinite(net)) or not np.all(np.isfinite(reference)):
        raise ValueError("matched baseline absent for a retained own-clock ticket")
    return j, i, signs, net, reference, unresolved, adjust


def evaluate(tape, rule, costs, funding, stress, spot, marks):
    hold = rule["hold_hours"]
    j, i, signs, net, reference, unresolved, adjust = ticket_legs(tape, rule, costs, funding)
    paired = net - reference
    half_ts, half_means, half_plain, half_n, half_days = [], [], [], [], []
    for idx, mask in enumerate((i + hold < HALF_INDEX, i >= HALF_INDEX), 1):
        x = net[mask] - adjust(idx, mask)
        half_ts.append(t_cluster(x, DAY[i[mask]]))
        half_means.append(mean_or_null(x))
        half_plain.append(mean_or_null(net[mask]))
        half_n.append(int(mask.sum()))
        half_days.append(int(np.unique(DAY[i[mask]]).size))
    n = len(net)
    active_days = int(np.unique(DAY[i]).size)
    thin = too_thin(n, active_days, half_days, marks)
    trim_n = n - math.ceil(n * marks["trim_share"])
    trimmed = mean_or_null(np.sort(net)[:trim_n]) if n else None
    t = t_cluster(paired, DAY[i])
    mean = mean_or_null(net)
    annual = float(net.sum()) / YEARS
    daily = np.bincount(DAY[i], weights=net, minlength=DAYS)
    return ({"rule": rule["id"], "family": rule["family"], "trades": n, "active_days": active_days,
             "half_active_days": half_days, "too_thin": thin,
             "unresolved_selected_tickets": unresolved, "plain_mean": mean,
             "paired_mean": mean_or_null(paired), "paired_day_t": t, "half_paired_day_t": half_ts,
             "half_paired_mean": half_means, "half_plain_mean": half_plain, "half_trades": half_n,
             "plain_trimmed_mean": trimmed, "simple_net_annual": annual,
             "simple_spot_taker_fee_only_annual": float((signs - spot / 10000).sum()) / YEARS,
             "funding_stress_simple_annual": {str(r): float((net - hold * (r - funding) / 10000).sum()) / YEARS for r in stress},
             "meets_search_marks": bool(not thin and registered_marks(mean, t, half_ts, trimmed, annual, marks)
                                        and all(m is not None and m > 0 for m in half_plain)),
             "finalist_rank": None, "duplicate_of": None}, daily)


def duplicate_corr(a, b):
    a, b = a - a.mean(), b - b.mean()
    den = math.sqrt((a @ a) * (b @ b))
    return float((a @ b) / den) if den else 0.


def sweep(coins, panel, rules, costs, config):
    if not (1 <= len(rules) <= 300) or len({rule["id"] for rule in rules}) != len(rules):
        raise ValueError("rule count or identity")
    if coins != sorted(set(coins)) or "BTC" not in coins:
        raise ValueError("roster order or required BTC reference")
    tape = Tape(coins, panel)
    marks = config["search_marks"]
    outputs = [evaluate(tape, r, costs, config["funding_adverse_bp_per_hour"],
                        config["funding_stress_bp_per_hour"], config["spot_taker_round_trip_bp"],
                        marks) for r in rules]
    qualifiers = sorted(((r, d) for r, d in outputs if r["meets_search_marks"]),
                        key=lambda item: (-item[0]["paired_day_t"], item[0]["rule"]))
    finalists = []
    for row, daily in qualifiers:
        dup = next((r["rule"] for r, d in finalists if duplicate_corr(daily, d) > marks["duplicate_corr"]), None)
        if dup is not None:
            row["duplicate_of"] = dup
        elif len(finalists) < marks["finalist_cap"]:
            finalists.append((row, daily))
            row["finalist_rank"] = len(finalists)
    return [row for row, _ in outputs]


def rows_bytes(rows):
    return ("".join(json.dumps(row, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n" for row in rows)).encode()


def checked_freeze(repo, commit, grid_pin, settings_pin, extra_paths=(), ancestor=None):
    """Refuse before any custody I/O unless the caller supplies the exact freeze."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        raise ValueError("full frozen commit SHA required")
    if not all(re.fullmatch(r"[0-9a-f]{64}", x or "") for x in (grid_pin, settings_pin)):
        raise ValueError("independent grid and settings SHA-256 pins required")
    git_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    git_env["GIT_NO_REPLACE_OBJECTS"] = "1"

    def git(*args):
        return subprocess.check_output(["git", "--no-optional-locks", "-C", str(repo), *args],
                                       env=git_env)

    if (git("rev-parse", "--show-toplevel").decode().strip() != str(repo)
            or git("rev-parse", "HEAD").decode().strip() != commit
            or git("status", "--porcelain=v1", "--untracked-files=all")):
        raise ValueError("checkout must be clean and exactly at the lead's frozen commit")
    if ancestor is not None and git("merge-base", ancestor, commit).decode().strip() != ancestor:
        raise ValueError("runner freeze must descend from the audited search freeze")
    blobs = {}
    for path in ("research_rig/sweep_70.py", "research_rig/coverage_70.py", GRID_PATH,
                 SETTINGS_PATH, COVERAGE_PATH, *extra_paths):
        frozen = git("show", f"{commit}:{path}")
        if read_snapshot(repo, path) != frozen:
            raise ValueError("checked-out bytes differ from frozen commit")
        blobs[path] = frozen
    for path, pin in ((GRID_PATH, grid_pin), (SETTINGS_PATH, settings_pin)):
        if hashlib.sha256(blobs[path]).hexdigest() != pin:
            raise ValueError("supplied freeze hash differs from committed bytes")
    return blobs


def parse_config(coverage_bytes, settings_bytes, grid_bytes):
    coverage = json.loads(coverage_bytes)
    settings = yaml.safe_load(settings_bytes)["replay_70_plan"]["value"]
    if coverage.keys() != {"coins", "private_manifest_sha256", "grid_sha256"} or coverage.keys() & settings.keys():
        raise ValueError("settings must not override source, roster or grid pins")
    if hashlib.sha256(grid_bytes).hexdigest() != coverage["grid_sha256"]:
        raise ValueError("grid differs from preregistration")
    return {**coverage, **settings}


def render_run(root, manifest, config, rules, *, validation_only):
    panel, counts = load_frozen(root, manifest, config)
    header = {"input_counts": counts}
    if validation_only:
        return rows_bytes([header])
    coins = config["coins"]
    costs = np.array([config["futures_round_trip_bp"][c] for c in coins])
    return rows_bytes([header, *sweep(coins, panel, rules, costs, config)])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic", action="store_true")
    mode.add_argument("--audited-search", action="store_true")
    mode.add_argument("--validate-inputs", action="store_true")
    ap.add_argument("--root", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--freeze-commit")
    ap.add_argument("--grid-sha256")
    ap.add_argument("--settings-sha256")
    args = ap.parse_args()
    repo = HERE.parent
    if args.synthetic:
        if any((args.root, args.manifest, args.freeze_commit, args.grid_sha256, args.settings_sha256)):
            ap.error("synthetic has no real inputs")
        blobs = {path: (repo / path).read_bytes() for path in (COVERAGE_PATH, SETTINGS_PATH, GRID_PATH)}
    else:
        if args.root != CUSTODY or args.manifest != CUSTODY / MANIFEST_REL:
            ap.error("custody modes require the exact canonical custody and manifest paths")
        if not (sys.flags.ignore_environment and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null"):
            ap.error("custody modes require python -E -B -X pycache_prefix=/dev/null")
        blobs = checked_freeze(repo, args.freeze_commit, args.grid_sha256, args.settings_sha256)
    config = parse_config(blobs[COVERAGE_PATH], blobs[SETTINGS_PATH], blobs[GRID_PATH])
    rules = json.loads(blobs[GRID_PATH])
    if args.synthetic:
        from synthetic_70 import synthetic_main
        synthetic_main(rules, config)
        return
    sys.stdout.buffer.write(render_run(args.root, args.manifest, config, rules,
                                       validation_only=args.validate_inputs))


if __name__ == "__main__":
    main()
