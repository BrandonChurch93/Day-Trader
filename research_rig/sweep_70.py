"""Plan 70 SEARCH ONLY. No vault, network, orders, or trade-level output."""
import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import numpy as np
import yaml
from numpy.lib.stride_tricks import sliding_window_view


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
ARCHIVES = ("replay_13", "replay_22", "replay_16")


def maintenance(t):
    dt = datetime.fromtimestamp(int(t), timezone.utc).astimezone(ET)
    return dt.weekday() == 4 and dt.hour == 17


MAINT = np.array([maintenance(t) for t in HOURS])
LONDON = ZoneInfo("Europe/London")
LONDON_CLOSE = np.array([datetime.fromtimestamp(int(t), timezone.utc).astimezone(LONDON).hour == 16
                         for t in HOURS])


def read_hour_rows(stream):
    """Only opening timestamp is read before the inclusive/exclusive date cut."""
    for wire in stream:
        stamp, _, payload = wire.partition(b",")
        t_ms = int(stamp)
        if not START * 1000 <= t_ms < STOP * 1000:
            continue
        if t_ms % (HOUR * 1000):
            raise ValueError("unaligned retained hourly bar")
        vals = payload.split(b",")
        if int(vals[5]) != t_ms + HOUR * 1000 - 1:
            raise ValueError("retained bar has wrong close clock")
        row = tuple(float(x) for x in vals[:5])  # open, high, low, close, base volume
        if not all(map(math.isfinite, row)) or not (0 < row[2] <= min(row[0], row[3])
                                                  <= max(row[0], row[3]) <= row[1] and row[4] >= 0):
            raise ValueError("malformed retained bar")
        yield (t_ms // 1000 - START) // HOUR, row


def load_frozen(root, manifest, config):
    root = root.resolve()
    expected = root / "sweep_70/coverage.json"
    if manifest.absolute() != expected or expected.resolve(strict=True) != expected:
        raise ValueError("not the allowed timestamp-only manifest path")
    raw = manifest.read_bytes()
    if hashlib.sha256(raw).hexdigest() != config["private_manifest_sha256"]:
        raise ValueError("not the preregistered timestamp-only manifest")
    roster = json.loads(raw)
    if tuple(config["coins"]) != ALLOWED:
        raise ValueError("roster differs from hard allow-list")
    panel = np.full((len(config["coins"]), len(HOURS), 5), np.nan)
    for j, coin in enumerate(config["coins"]):
        for record in roster[coin]["files"]:
            tag = record["month"]
            y, m = map(int, tag.split("-"))
            if not (2020 <= y <= 2023 and 1 <= m <= 12):
                raise ValueError("only pre-vault monthly files may be opened")
            expected_name = f"{coin}USDT-1h-{tag}"
            rel = f"archives/data/spot/monthly/klines/{coin}USDT/1h/{expected_name}.zip"
            if record["path"] not in {f"{s}/{rel}" for s in ARCHIVES}:
                raise ValueError("not an allowlisted archive path")
            path = root / record["path"]
            if path.resolve(strict=True) != path:
                raise ValueError("archive path must not redirect")
            # Check archive identity before reading any row values.
            with path.open("rb") as wire:
                if hashlib.file_digest(wire, "sha256").hexdigest() != record["sha256"]:
                    raise ValueError("retained archive identity changed")
            seen = 0
            with ZipFile(path) as z, z.open(expected_name + ".csv") as stream:
                for i, row in read_hour_rows(stream):
                    if not np.isnan(panel[j, i, 0]) or not record["first_utc_seconds"] <= HOURS[i] <= record["last_utc_seconds"]:
                        raise ValueError("duplicate or unexpected retained row")
                    panel[j, i] = row
                    seen += 1
            if seen != record["rows"]:
                raise ValueError("retained coverage changed")
    return panel


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

    def __post_init__(self):
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
        idx = np.arange(len(HOURS))
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
            length = len(HOURS) - hold
            idx = np.arange(length)
            eligible = self.missing[:, idx + hold + 1] == self.missing[:, idx]
            # No position or clock baseline straddles the CDE weekly maintenance hour.
            for h in range(hold + 1):
                eligible &= ~MAINT[idx + h]
            ratio = self.o[:, hold:] / self.o[:, :length] - 1
            gross[:, :length] = np.where(eligible, ratio, np.nan)
            baselines = []
            for lo, hi in ((0, len(HOURS)), (0, HALF_INDEX), (HALF_INDEX, len(HOURS))):
                # For half blocks both entry and exit must be inside that block.
                b = gross[:, lo:hi - hold].copy()
                clock = UTC_HOUR[lo:hi - hold]
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
            ok &= (UTC_HOUR == p["entry_hour"]) & (WEEKEND == (p["day_type"] == "weekend"))
        if f in ("hourly_shock", "midnight_stop_run", "volume_shock"):
            with np.errstate(invalid="ignore", divide="ignore"):
                prior = tape.ref("vol", p["volume_lookback"])
                ratio = tape.v1 / prior
            ok &= (prior > 0) & (ratio >= p["ratio"])
        if f == "midnight_stop_run":
            pierce = (tape.l1 < tape.ref("min", p["lag_range"]) if side == 1
                      else tape.h1 > tape.ref("max", p["lag_range"]))
            ok &= (UTC_HOUR == 0) & pierce
    elif f == "london_brr_fade":
        strength = -side * tape.open_to_close1
        ok = (strength >= cut) & LONDON_CLOSE
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
    valid_clock = np.ones(len(HOURS), dtype=bool)
    for h in range(hold + 1):
        valid_clock[:len(HOURS) - h] &= ~MAINT[h:]
    valid_clock[len(HOURS) - hold:] = False
    schedule = np.flatnonzero(np.isfinite(signal[j, np.arange(len(HOURS))]) & valid_clock)
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
    mean = float(x.mean())
    sums = np.bincount(day, weights=x, minlength=len(cnt)) - mean * cnt
    se = math.sqrt(groups / (groups - 1) * (sums @ sums)) / len(x)
    return mean / se if se > 1e-14 else None


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


def evaluate(tape, rule, costs, funding, stress, spot, marks):
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
        b = side * baselines[which][c, UTC_HOUR[ix]]
        if hedge:
            b = .5 * (b - side * baselines[which][tape.btc, UTC_HOUR[ix]])
        return net[loc] - b

    whole = np.ones(len(i), dtype=bool)
    paired = adjust(0, whole)
    if not np.all(np.isfinite(paired)):
        raise ValueError("matched baseline absent for a retained own-clock ticket")
    half_ts, half_means, half_plain, half_n, half_days = [], [], [], [], []
    for idx, mask in enumerate((i + hold < HALF_INDEX, i >= HALF_INDEX), 1):
        x = adjust(idx, mask)
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic", action="store_true")
    mode.add_argument("--audited-search", action="store_true")
    ap.add_argument("--root", type=Path)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()
    config = json.loads((HERE / "COVERAGE_70.json").read_text())
    config.update(yaml.safe_load((HERE.parent / "config/thresholds.yaml").read_text())["replay_70_plan"]["value"])
    grid_bytes = (HERE / "GRID_70.json").read_bytes()
    if hashlib.sha256(grid_bytes).hexdigest() != config["grid_sha256"]:
        raise ValueError("grid differs from preregistration")
    rules = json.loads(grid_bytes)
    if args.synthetic:
        if args.root or args.manifest:
            ap.error("synthetic has no real inputs")
        from synthetic_70 import synthetic_main
        synthetic_main(rules, config)
        return
    if args.root is None or args.manifest is None:
        ap.error("audited search needs explicit existing custody and manifest")
    panel = load_frozen(args.root, args.manifest, config)
    coins = config["coins"]
    print(rows_bytes(sweep(coins, panel, rules, np.array([config["futures_round_trip_bp"][c] for c in coins]),
                           config)).decode(), end="")


if __name__ == "__main__":
    main()
