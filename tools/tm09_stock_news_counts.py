"""Count stock news from approved JSONL; only verification metadata and counts leave."""
import argparse
from bisect import bisect_right
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from hashlib import file_digest
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPORT = Path("/home/user/workspace/rig/data/tm09_stock_export")
PINS = {
    "stock_news.jsonl": (12232, "19a356620ecc6a97ce90d7d0cbce44bf17fbd9c536457cdf8140e6ea09c59288"),
    "stock_sessions.jsonl": (226, "4223b3dfd5be58a26b70459e00dc902cf67145140c1ef53803ada0096be95e91"),
    "stock_universe.jsonl": (10065, "97ec7721d7ce09cb4d441f5ae55310ce792920c8f0be973349adf6561c649a12"),
}
NY = ZoneInfo("America/New_York")
UTC = timezone.utc
SOURCES = ("alpaca", "sec_edgar")
START, END = date(2026, 4, 1), date(2026, 11, 24)
SHARED_START = date(2026, 4, 29)
DELAY_SECONDS = 3600
# Maker's stated later bound, as recorded in Doc 11 and TM06 plan.
MAKER_FIRST = date(2026, 7, 1)


def next_month(month):
    d = date.fromisoformat(month + "-01")
    return (d.replace(day=28) + timedelta(days=4)).replace(day=1)


def clock_config():
    cfg = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    stock_list = cfg["tm04_plan"]["value"]["symbols"]
    wake_hours = cfg["tm_stock_wake_times_ny"]["value"]
    probe = json.loads((ROOT / "timemachine/knowledge_lines.json").read_text())["models"]
    knowledge = {k: {field: probe[k][field] for field in ("stated_latest_month", "last_hit")}
                 for k in ("FABLE", "OPUS")}
    if len(stock_list) != 38 or len(set(stock_list)) != 38 or sorted(wake_hours) != wake_hours:
        raise ValueError("unexpected stock roster or wake clock")
    return stock_list, wake_hours, knowledge


def calendar(rows, wake_hours):
    result = []
    for d, op, cl in rows:
        local = date.fromisoformat(d)
        monday = local - timedelta(days=local.weekday())
        if local.weekday() >= 5 or not START <= local <= END or not op < cl:
            raise ValueError("unexpected stock session calendar")
        for h in wake_hours:
            mins = round(h * 60)
            wake = int(datetime.combine(local, time(mins // 60, mins % 60), NY).timestamp())
            if op <= wake < cl:
                result.append((wake, monday.isoformat()))
    if not result or any(a[0] >= b[0] for a, b in zip(result, result[1:])):
        raise ValueError("missing or unordered stock wakes")
    return result


def admitted_weekly(calendar_rows, news_rows):
    stocks, hours, knowledge = clock_config()
    ix = {s: i for i, s in enumerate(stocks)}
    last_probe = max(next_month(m["stated_latest_month"]) for m in knowledge.values())
    sessions = sorted(row for row in calendar_rows if START.isoformat() <= row[0] <= END.isoformat())
    session_dates = {date.fromisoformat(r[0]) for r in sessions}
    if START not in session_dates or END not in session_dates:
        raise ValueError("export does not cover documented calendar endpoints")
    wakes = calendar(sessions, hours)
    wake_stamps = [w for w, _ in wakes]
    floor = int(datetime.combine(START, time(), NY).timestamp())
    ceiling = int(datetime.combine(END + timedelta(days=1), time(), NY).timestamp())
    buckets = [[Counter(), Counter()] for _ in wakes]
    quality, admitted_unique, roster_unique = {s: Counter() for s in SOURCES}, Counter(), Counter()
    for src, created, updated, edited, tags in news_rows:
        if src not in SOURCES:
            continue
        q = quality[src]
        q["source_items"] += 1
        if type(created) is not int or type(updated) is not int or type(edited) is not bool:
            q["invalid_clock"] += 1
            continue
        if edited or updated > created:
            q["edited_later"] += 1
            continue
        if updated < created:
            q["invalid_clock"] += 1
            continue
        q["unchanged_clock"] += 1
        if not floor <= created < ceiling:
            q["outside_calendar_date_span"] += 1
            continue
        if not isinstance(tags, list):
            raise ValueError("invalid source symbols array")
        symbols_here = {ix[s] for s in tags if isinstance(s, str) and s in ix}
        w = bisect_right(wake_stamps, created + DELAY_SECONDS)
        if w == len(wakes):
            q["after_final_wake"] += 1
            continue
        q["items_before_a_wake"] += 1
        if not symbols_here:
            q["no_roster_tag"] += 1
            continue
        q["items_with_roster_tag"] += 1
        target = buckets[w][SOURCES.index(src)]
        target.update(symbols_here)
        admitted_unique[wakes[w][1], src] += 1
        roster_unique[src] += 1
    weekly, wake_out = {}, []
    for (wake, week), bucket in zip(wakes, buckets):
        weekly.setdefault(week, [Counter(), Counter()])
        for j, b in enumerate(bucket):
            weekly[week][j].update(b)
        # Sparse per-wake first admissions: [ticker index, Alpaca count, SEC count].
        counts = [[i, bucket[0][i], bucket[1][i]] for i in sorted(set(bucket[0]) | set(bucket[1]))]
        wake_out.append([wake, counts])
    week_out, coverage = [], Counter()
    for week, by_source in weekly.items():
        monday = date.fromisoformat(week)
        full = START <= monday and monday + timedelta(days=6) <= END
        after_probe = full and monday >= last_probe
        after_maker = full and monday >= MAKER_FIRST
        full_shared = full and monday >= SHARED_START
        cats = ("all",) + (("full",) if full else ()) + (("probe_full",) if after_probe else ()) + (
            ("maker_full",) if after_maker else ()) + (("joint_source_full",) if full_shared else ())
        empty = sum(not by_source[0][i] and not by_source[1][i] for i in range(len(stocks)))
        for cat in cats:
            coverage[cat + "_weeks"] += 1
            coverage[cat + "_empty_stock_weeks"] += empty
        week_out.append({"monday_ny": week, "full": full, "after_probe": after_probe,
                         "after_maker": after_maker, "wake_count": sum(wk == week for _, wk in wakes),
                         "empty_stock_weeks": empty,
                         "distinct_tagged_items": [admitted_unique[week, s] for s in SOURCES],
                         "counts_by_stock": [[c[i] for c in by_source] for i in range(len(stocks))]})
    for cat in ("all", "full", "probe_full", "maker_full", "joint_source_full"):
        denominator = coverage[cat + "_weeks"] * len(stocks)
        coverage[cat + "_stock_weeks"] = denominator
        if denominator:
            coverage[cat + "_empty_share"] = coverage[cat + "_empty_stock_weeks"] / denominator
    return {
        "sources": SOURCES, "stock_order": stocks, "wake_times_ny_hours": hours,
        "delay_seconds": DELAY_SECONDS, "session_count": len(sessions), "knowledge_lines": knowledge,
        "probe_first": last_probe.isoformat(), "maker_first": MAKER_FIRST.isoformat(),
        "coverage": dict(coverage), "source_quality": {s: dict(quality[s]) for s in SOURCES},
        "distinct_tagged_items": dict(roster_unique), "weeks": week_out, "wakes_utc_first_admissions": wake_out,
    }


def verified_files():
    for name, (_, expected) in PINS.items():
        p = EXPORT / name
        if EXPORT.resolve() != EXPORT or p.is_symlink() or not p.is_file():
            raise ValueError("only the standalone approved export is allowed")
        with p.open("rb") as f:
            if file_digest(f, "sha256").hexdigest() != expected:
                raise ValueError("export hash differs from the approved manifest")


def projected(rows, fields):
    """Project immediately; do not use or emit vendor text, not even on errors."""
    for line in rows:
        try:
            obj = json.loads(line)
            yield tuple(obj[k] for k in fields)
        except (ValueError, KeyError, TypeError):
            raise ValueError("invalid stock export row metadata") from None


def read_fields(name, fields):
    with (EXPORT / name).open(encoding="utf-8") as f:
        result = list(projected(f, fields))
    if len(result) != PINS[name][0]:
        raise ValueError("export row count differs from the approved manifest")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--weekly", action="store_true", help="emit only aggregate weekly rows and stock counts")
    args = p.parse_args()
    verified_files()
    schedule = read_fields("stock_sessions.jsonl", ("date", "open_utc", "close_utc"))
    news = read_fields("stock_news.jsonl", ("source", "stated_time", "updated_time", "edited_later", "symbols"))
    result = admitted_weekly(schedule, news)
    result["export_sha256"] = {k: h for k, (_, h) in PINS.items()}
    if args.weekly:
        result.pop("wakes_utc_first_admissions")
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
