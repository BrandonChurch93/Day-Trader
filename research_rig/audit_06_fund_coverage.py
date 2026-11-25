"""Emit only fund bar counts and NYSE session dates. No prices, returns or rules."""

from datetime import datetime, time
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars
import yaml


HERE = Path(__file__).resolve().parent
ROOT = Path("/home/user/workspace/rig/data/funds_daily")
ADJUSTMENTS = ("all", "split")
NY = ZoneInfo("America/New_York")


def config(key):
    return yaml.safe_load((HERE.parent / "config" / "thresholds.yaml").read_text())[key]["value"]


def read_bars(symbol, adjust):
    path = ROOT / f"{symbol}.{adjust}.json"
    page = json.loads(path.read_bytes())
    if page["next_page_token"] is not None:
        raise ValueError(f"Uncollected page for {symbol} {adjust}")
    bars = page["bars"][symbol]
    if not bars:
        raise ValueError(f"No bars for {symbol} {adjust}")
    return bars


def coverage(bars, expected):
    stamps = [datetime.fromisoformat(row["t"]).astimezone(NY) for row in bars]
    days = [t.date().isoformat() for t in stamps]
    actual = set(days)
    return dict(rows=len(days), first_ny=min(days), last_ny=max(days),
                duplicate_dates=len(days) - len(actual),
                non_midnight_bars=sum(t.time() != time() for t in stamps),
                non_increasing_pairs=sum(a >= b for a, b in zip(days, days[1:])),
                missing_sessions=sorted(expected - actual), unexpected_dates=sorted(actual - expected))


def main():
    ds = config("replay_06_data")
    start, end = ds["first_bar"], ds["last_bar"]
    cal = exchange_calendars.get_calendar("XNYS", start=start, end=end[:4] + "-12-31")
    nyse = [d.date().isoformat() for d in cal.sessions]
    sessions = [d for d in nyse if start <= d <= end]
    panes = {}
    for name, days in {
        "warmup": [d for d in sessions if d < ds["design_start"]],
        "design": [d for d in sessions if ds["design_start"] <= d < ds["held_start"]],
        "held": [d for d in sessions if ds["held_start"] <= d],
    }.items():
        day_set = set(days)
        n_month_ends = sum(a in day_set for a, b in zip(nyse, nyse[1:]) if a[:7] != b[:7])
        panes[name] = dict(first_ny=days[0], last_ny=days[-1], sessions=len(days),
                           complete_month_end_sessions=n_month_ends)
    funds = {s: {a: coverage(read_bars(s, a), set(sessions)) for a in ADJUSTMENTS}
             for s in ds["symbols"]}
    print(json.dumps(dict(expected_sessions=len(sessions), slices=panes, funds=funds), indent=2))
    if any(row["duplicate_dates"] or row["non_midnight_bars"] or row["non_increasing_pairs"]
           or row["missing_sessions"] or row["unexpected_dates"]
           for fund in funds.values() for row in fund.values()):
        raise SystemExit("At least one bar file disagrees with the NYSE session calendar.")


if __name__ == "__main__":
    main()
