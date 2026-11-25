"""Audit public funding timestamps, then count design entries without reading price values."""

from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import gzip
import json
from math import ceil
from pathlib import Path
import sys
from zipfile import ZipFile

import yaml


HERE = Path(__file__).resolve().parent
DATA = Path("/home/user/workspace/rig/data")
UTC = timezone.utc
HOUR_MS = 3_600_000
BPS = 10_000


def split(cfg):
    start, end = (date.fromisoformat(cfg[key]) for key in ("start", "end"))
    total = (end - start).days + 1
    held_days = ceil(total * Decimal(str(cfg["held_fraction"])))
    if not 0 < held_days < total:
        raise ValueError("Both slices must contain days")
    return start, end - timedelta(days=held_days - 1), end, total, held_days


def day_hour(d):
    return int(datetime.combine(d, time(), tzinfo=UTC).timestamp()) // 3600


def iso(raw_ms):
    return datetime.fromtimestamp(raw_ms / 1000, UTC).isoformat()


def inventory(times):
    return {
        "rows": len(times),
        "first_utc": iso(times[0]),
        "last_utc": iso(times[-1]),
        "duplicate_timestamps": len(times) - len(set(times)),
        "gaps_seconds": dict(sorted(Counter(
            (b - a) // 1000 for a, b in zip(times, times[1:])
        ).items())),
    }


def archive(symbol, cfg, min_hour, stop_hour, full_end):
    step, tolerance = cfg["settlement_hours"], cfg["timestamp_tolerance_ms"]
    expected_month = None
    samples, times, raw_times = {}, [], []
    files = sorted((DATA / "funding" / "binance").glob(f"{symbol}-fundingRate-*.zip"))
    jitter = 0
    for path in files:
        month = date.fromisoformat(path.stem[-7:] + "-01")
        if expected_month is not None and month != expected_month:
            raise ValueError(f"Archive month missing: {expected_month}")
        expected_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        with ZipFile(path) as zipped, zipped.open(path.stem + ".csv") as rows:
            if next(rows).strip() != b"calc_time,funding_interval_hours,last_funding_rate":
                raise ValueError(f"Unexpected columns in {path.name}")
            for row in rows:
                stamp, interval, value = row.split(b",", maxsplit=2)
                raw = int(stamp)
                hour = (raw + HOUR_MS // 2) // HOUR_MS
                jitter = max(jitter, abs(raw - hour * HOUR_MS))
                if int(interval) != step or hour % step or jitter > tolerance:
                    raise ValueError(f"Unexpected settlement grid in {path.name}: {raw}")
                raw_times.append(raw)
                times.append(hour * HOUR_MS)
                # Values outside design plus warm-up are never parsed, logged or used.
                if min_hour <= hour < stop_hour:
                    rate = Decimal(value.strip().decode("ascii"))
                    if not rate.is_finite():
                        raise ValueError(f"Invalid design rate at {raw}")
                    samples[hour] = rate * BPS
    expected_last = day_hour(full_end + timedelta(days=1)) - step
    if not times or times[0] > min_hour * HOUR_MS or times[-1] != expected_last * HOUR_MS:
        raise ValueError(f"Unexpected archive bounds: {symbol}")
    meta = inventory(times)
    if meta["gaps_seconds"] != {step * 3600: len(times) - 1}:
        raise ValueError(f"Gap, duplicate or ordering error: {symbol}")
    return samples, dict(meta, monthly_files=len(files), max_abs_settlement_offset_ms=jitter,
                         first_raw_utc=iso(raw_times[0]), last_raw_utc=iso(raw_times[-1]))


def traded_hours(symbol, start_hour, stop_hour):
    result = []
    with gzip.open(DATA / "alpaca_crypto" / f"{symbol}_1Hour.csv.gz", "rb") as rows:
        if next(rows).strip() != b"t,o,h,l,c,v,n":
            raise ValueError(f"Unexpected Alpaca columns: {symbol}")
        last = None
        for row in rows:
            stamp, _, volume, trades = row.rstrip().rsplit(b",", 3)
            stamp = stamp.split(b",", 1)[0]  # skip the OHLC bytes without parsing them
            dt = datetime.fromisoformat(stamp.decode("ascii").replace("Z", "+00:00"))
            hour = int(dt.timestamp()) // 3600
            if hour >= stop_hour:
                break
            if last is not None and hour <= last:
                raise ValueError(f"Non-increasing Alpaca hourly timestamps: {symbol}")
            if dt.minute or dt.second or dt.microsecond:
                raise ValueError(f"Alpaca bar is off the hour: {symbol}")
            if hour >= start_hour and Decimal(volume.decode("ascii")) > 0 and int(trades) > 0:
                result.append(hour)
            last = hour
    if not result:
        raise ValueError(f"No traded design bars: {symbol}")
    return result


def count_entries(samples, traded, start, stop, funding, rules, band):
    step, lag = funding["settlement_hours"], funding["fill_lag_hours"]
    lookback, hold = rules["lookback_hours"], rules["max_hold_hours"]
    if lookback % step or not 0 < lag < step:
        raise ValueError("Lookback and lag do not fit the funding grid")
    traded_set = set(traded)
    positives = sorted(t for t, rate in samples.items() if rate > rules["positive_exit_bps"])
    totals = {t: sum(samples[h] for h in range(t - lookback + step, t + 1, step))
              for t in samples
              if all(h in samples for h in range(t - lookback + step, t + 1, step))}
    result = dict(threshold_crossings=0, beyond_max_hold_boundary=0, in_position=0,
                  no_traded_entry_bar=0, entries=0, completed=0)
    busy_through = start - 1
    for t in sorted(totals):
        entry = t + lag
        if not start <= entry < stop or t - step not in totals:
            continue
        if not totals[t - step] > band >= totals[t]:
            continue
        result["threshold_crossings"] += 1
        deadline = entry + hold
        if deadline >= stop:
            result["beyond_max_hold_boundary"] += 1
        elif entry <= busy_through:
            result["in_position"] += 1
        elif entry not in traded_set:
            result["no_traded_entry_bar"] += 1
        else:
            result["entries"] += 1
            positive = bisect_right(positives, entry)
            if positive < len(positives):
                deadline = min(deadline, positives[positive] + lag)
            exit_idx = bisect_left(traded, deadline)
            busy_through = traded[exit_idx] if exit_idx < len(traded) else stop
            result["completed"] += busy_through < stop
    return result


def self_test():
    funding = {"settlement_hours": 8, "fill_lag_hours": 1}
    rules = {"lookback_hours": 24, "max_hold_hours": 48, "positive_exit_bps": 0}
    # Entry at hour 1, positive reading at hour 8, delayed exit at hour 10.
    samples = {-24: 0, -16: 0, -8: 0, 0: -5, 8: 1, 16: -2, 24: -5}
    traded = [t for t in range(100) if t != 9]
    count = count_entries(samples, traded, 0, 100, funding, rules, -5)
    assert count["threshold_crossings"] == count["entries"] == count["completed"] == 2, count
    count = count_entries(samples, traded, 0, 55, funding, rules, -5)
    assert count["entries"] == count["beyond_max_hold_boundary"] == 1, count
    count = count_entries(samples, traded[2:], 0, 100, funding, rules, -5)
    assert count["entries"] == count["no_traded_entry_bar"] == 1, count
    gaps = {t: v for t, v in samples.items() if t != -8}
    count = count_entries(gaps, traded, 0, 100, funding, rules, -5)
    assert count["threshold_crossings"] == 0, count
    samples = {-24: 6, -16: 0, -8: 0, 0: -5, 8: 0, 16: 0, 24: -5, 32: 0}
    count = count_entries(samples, traded, 0, 100, funding, rules, -5)
    assert count["threshold_crossings"] == 1, count
    samples = {-24: 6, -16: 0, -8: 0, 0: -5, 8: 0, 16: 0, 24: 0, 32: -5}
    count = count_entries(samples, traded, 0, 100, funding, rules, -5)
    assert count["threshold_crossings"] == 2 and count["in_position"] == 1, count


def main():
    cfg = yaml.safe_load((HERE.parent / "config" / "thresholds.yaml").read_text())

    def value(key):
        return cfg[key]["value"]

    dates, funding, rules, stats = (value("replay_10_" + k)
                                    for k in ("dates", "funding", "rules", "statistics"))
    start, held_start, end, days, held_days = split(dates)
    first, stop = day_hour(start), day_hour(held_start)
    cover, counts = {}, []
    for symbol in ("PF_XBTUSD", "PF_ETHUSD", "PI_XBTUSD", "PI_ETHUSD"):
        payload = json.loads((DATA / "funding" / f"kraken_{symbol}.json").read_bytes())
        times = [int(datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                     .timestamp() * 1000) for item in payload["rates"]]
        cover["Kraken " + symbol] = inventory(times)
    for perpetual, spot in sorted(funding["symbols"].items()):
        samples, cover["Binance " + perpetual] = archive(
            perpetual, funding, first - rules["lookback_hours"], stop, end)
        traded = traded_hours(spot, first, stop)
        for band in rules["entry_bps"]:
            counts.append(dict(
                id=stats["first_trial_id"] + len(counts), symbol=spot, entry_bps=band,
                **count_entries(samples, traded, first, stop, funding, rules, band),
            ))
    spread = value("tm_crypto_half_spread_bps")
    alpaca_fee, kraken_fee = (value("practice_crypto_fee_bps_added"),
                              value("replay_10_kraken_spot_taker_bps"))
    print(json.dumps(dict(
        design=[start.isoformat(), (held_start - timedelta(days=1)).isoformat()],
        held_unread=[held_start.isoformat(), end.isoformat()],
        calendar_days=days, design_days=days - held_days, held_days=held_days,
        min_design_entries=rules["min_design_entries"],
        rule_trial_count=stats["previous_trials"] + len(counts),
        costs_bps_per_side=dict(assumed_half_spread=spread, alpaca_taker=alpaca_fee,
                                alpaca_total=alpaca_fee + spread, kraken_taker=kraken_fee,
                                kraken_total=kraken_fee + spread),
        funding_timestamp_coverage=cover, design_signal_counts=counts,
    ), indent=2))


if __name__ == "__main__":
    self_test()
    if sys.argv[1:] == []:
        main()
    elif sys.argv[1:] == ["--self-test"]:
        print("Replay 10 design-count fixtures passed.")
    else:
        raise SystemExit("Usage: count_10_design.py [--self-test]")
