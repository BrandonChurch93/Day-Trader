"""Count ex-day feasibility from sealed dates, actions and volume flags; no returns."""
import argparse
from bisect import bisect_left
from collections import Counter
from datetime import datetime
from pathlib import Path
import re
import runpy
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
p = SimpleNamespace(**runpy.run_path(str(ROOT / "research_rig/score_43.py")))
IDS = "4bae6362ed717f9f8b0dd33b896c4aa86d600af678325c4b5cb215bce8faa0a0"
ACTIONS = "ad72767cc3a17fefdd0dfc1ccf7cf48fe6ba5574905b9e91cb4dc3bea5c81129"
BARS = "0551005330a84c44b18caf77ad73a709bacc0c7b52a82445384f5ee0b9beefe1"
PADDING = 5
# Match the sealed compact, sorted serialization. Never capture, convert, print
# or decode OHLC fields. Only the timestamp and zero/nonzero flag survive.
ROW = re.compile(rb'\{"c":"[^"\\]*","h":"[^"\\]*","l":"[^"\\]*","o":"[^"\\]*",'
                 rb'"t":("[0-9TZ:+.\-]+"),"v":(0|[1-9][0-9]*)\}')
FIELD = re.compile(rb'"[ohlcvt]"\s*:')


def strip_bars(blob, indexed=False):
    def redact(m):
        pos = b',"offset":' + str(m.start()).encode("ascii") if indexed else b""
        return b'{"session":' + m[1] + b',"positive":' + (b"false" if m[2] == b"0" else b"true") + pos + b"}"
    clean, n = ROW.subn(redact, blob)
    p.need(n > 0 and not FIELD.search(clean), "P61_PRESENCE_SHAPE")
    return p.parse(clean)


def date_rows(view, scope, indexed=False):
    seen = {}
    fields = {"session", "positive"} | ({"offset"} if indexed else set())
    for row in view:
        p.need(set(row) == fields and type(row["positive"]) is bool, "P61_PRESENCE_SHAPE")
        stamp = datetime.fromisoformat(row["session"].replace("Z", "+00:00"))
        p.need(stamp.tzinfo is not None, "P61_PRESENCE_DATE")
        et = stamp.astimezone(p.ET)
        day = et.date()
        p.need(et.time() == datetime.min.time() and day in scope and day not in seen, "P61_PRESENCE_DATE")
        seen[day] = row
    return seen


def ex_clock(e, target, days):
    if target is None:
        return "no_verified_cash_ex_date", None, None
    idx = bisect_left(days, target)
    if not 0 < idx < len(days) or days[idx] != target or not e.start <= days[idx - 1] < target <= e.end:
        return "clock_outside_sealed_window", None, None
    entry = days[idx - 1]
    close = days.closes.get(entry)
    if close is None or e.at >= close:
        return "filing_not_public_before_entry_close", None, None
    if entry < e.early:
        return "padding_not_complete_before_entry", None, None
    return None, entry, target


def screening(q, days, verified, bars, indexed=False):
    _, actions, modeled = verified
    p.need(set(bars["records"]) == modeled, "P61_PRESENCE_UNIVERSE")
    for e in q:
        if e.a not in modeled:
            yield e, "noncash_skip", None, None, None
            continue
        reason, start, end = ex_clock(e, actions[e.a]["stock"][1], days)
        if reason:
            yield e, reason, None, None, None
            continue
        scope = set(days[bisect_left(days, e.start):bisect_left(days, e.end) + 1])
        legs = bars["records"][e.a]
        raw = {leg: date_rows(legs[leg]["raw"], scope, indexed) for leg in ("stock", "IWM")}
        stock, iwm = ({d for d, row in rows.items() if row["positive"]} for rows in raw.values())
        pad = {d for d in scope if d < e.early}
        p.need(len(pad) == PADDING, "P61_PRESENCE_PADDING")
        if not pad <= stock:
            reason = "stock_padding_volume_unavailable"
        elif not {start, end} <= stock:
            reason = "stock_clock_volume_unavailable"
        elif not {start, end} <= iwm:
            reason = "iwm_clock_volume_unavailable"
        else:
            reason = "price_blind_upper_bound"
        yield e, reason, start, end, raw


def count(q, days, verified, bars):
    counts, years, clusters = Counter(), Counter(), Counter()
    for _, reason, _, end, _ in screening(q, days, verified, bars):
        counts[reason] += 1
        if reason == "price_blind_upper_bound":
            years[end.year] += 1
            clusters[end] += 1
    p.need(sum(counts.values()) == len(q), "P61_PRESENCE_COUNTS")
    cluster_sizes = {}
    for year in sorted(years):
        cluster_sizes[year] = dict(sorted(Counter(n for d, n in clusters.items() if d.year == year).items()))
    return {"docket_events": len(q), "terminal_counts": dict(sorted(counts.items())),
            "ex_year_candidates": dict(sorted(years.items())), "distinct_ex_dates": len(clusters),
            "ex_date_cluster_size_counts_by_year": cluster_sizes}


def sealed():
    cfg = p.config((ROOT / p.CONFIG).read_bytes())
    days = p.calendar((ROOT / name).read_bytes() for name in p.CALENDARS)
    q = p.events(p.file_bytes(p.DOCKET, cfg["docket_sha256"], 12 * 2**20, private=True), days, cfg)
    ids = p.parse(p.file_bytes(p.INPUT / "identities.json", IDS, 8 * 2**20, private=True))
    actions = p.parse(p.file_bytes(p.INPUT / "actions.json", ACTIONS, 32 * 2**20, private=True))
    verified = p.identity_actions(q, days, cfg, ids, actions)
    return q, days, verified, p.file_bytes(p.INPUT / "bars.json", BARS, 96 * 2**20, private=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    q, days, verified, blob = sealed()
    out = p.render(count(q, days, verified, strip_bars(blob)))
    if args.output:
        args.output.write_bytes(out)
    else:
        sys.stdout.buffer.write(out)


if __name__ == "__main__":
    try:
        main()
    except (p.Refused, OSError, ValueError, KeyError, TypeError):
        sys.exit("P61_COUNT_REFUSED")
