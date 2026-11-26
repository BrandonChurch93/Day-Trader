"""Price-blind Plan 63 scheduling and logical request counts, no market inputs."""
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from hashlib import sha256
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
EVENTS = Path("/home/user/workspace/rig/data/count_102/events_102.json")
EVENTS_SHA = "b907ff0e296799200ad203dfa81af464285d622b5f378c6c9d4230061fd00ae8"
NY = ZoneInfo("America/New_York")
CUTOFF = date(2026, 11, 25)
SIP_START = date(2016, 1, 1)
HOLDS = (5, 20, 60)
SABA = "Saba Capital Management"


def parse_date_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def schedule():
    # Historical session dates come from the pinned repository calendars.
    past = json.loads((ROOT / "calendar_26.json").read_bytes())
    days = json.loads((ROOT / "calendar_25.json").read_bytes())
    clocks = json.loads((ROOT / "calendar_50.json").read_bytes())
    assert past["calendar"] == days["calendar"] == clocks["calendar"] == "XNYS"
    sessions = {date.fromisoformat(d): None for d in past["sessions"] + days["sessions"]}
    for d, _, close in clocks["sessions"]:
        assert date.fromisoformat(d) in sessions
        sessions[date.fromisoformat(d)] = parse_date_time(close)
    assert max(sessions) == date(2026, 11, 24)
    # Published NYSE extension: https://www.nyse.com/trade/hours-calendars
    closed = {"2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15"}
    early = {"2026-11-27", "2026-12-24"}
    for i in range(1, (date(2027, 3, 1) - max(sessions)).days + 1):
        d = date(2026, 11, 24) + timedelta(days=i)
        if d.weekday() < 5 and d.isoformat() not in closed:
            sessions[d] = datetime.combine(d, time(13 if d.isoformat() in early else 16), NY)
    return sessions


def counts(rows):
    groups = {(r["day"], r["filer"]) for r in rows}
    out = dict(fund_days=len(rows), filer_days=len(groups), filing_dates=len({d for d, _ in groups}))
    out.update(saba_fund_days=sum(r["filer"] == SABA for r in rows),
               non_saba_fund_days=sum(r["filer"] != SABA for r in rows),
               saba_filer_days=sum(f == SABA for _, f in groups),
               non_saba_filer_days=sum(f != SABA for _, f in groups))
    return out


def first_entry(closes, accepted):
    return bisect_left(closes, accepted + timedelta(minutes=60))


def candidates(raw, sessions):
    active = [(d, t) for d, t in sessions.items() if t is not None]
    days, close = zip(*active)
    assert list(sessions) == sorted(sessions) and list(close) == sorted(close)
    rows = []
    for r in raw:
        at = parse_date_time(r["acceptanceDateTime"])
        day = at.astimezone(NY).date()
        assert at.tzinfo is not None and str(day) == r["et_date"]
        assert r["is_cef_subject"] and not r["is_preferred"]
        idx = first_entry(close, at)
        rows.append(dict(at=at, day=day, fund=r["cef_cik"], filer=r["filer_group"],
                         accession=r["accession"], entry=idx))
    seen = set()
    unique = []
    for r in sorted(rows, key=lambda v: (v["at"], v["accession"])):
        k = r["fund"], r["day"]
        if k not in seen:
            unique.append(r)
            seen.add(k)
    return rows, unique, days, close


def select(rows, closes, n, at_filing=True):
    prior_exit = {}
    placed = []
    for row in rows:
        i = row["entry"]
        j = prior_exit.get(row["fund"])
        # Earliest accepted event wins, including two filing days that
        # resolve to the same entry close. Do not recycle skipped filings.
        if j is not None and (i <= j or (at_filing and row["at"] < closes[j])):
            continue
        prior_exit[row["fund"]] = i + n
        placed.append(dict(row, exit=i+n))
    return placed


def merged_n(intervals):
    total = rows = 0
    for spans in intervals.values():
        last = None
        for start, end in sorted(spans):
            if last is None or start > last + 1:
                total += 1
                rows += end - start + 1
                last = end
            elif end > last:
                rows += end - last
                last = end
    return total, rows


def self_check(sessions):
    early = date(2026, 11, 27)
    clocks = tuple(sessions[d] for d in sorted(sessions) if d >= early)
    assert clocks[0].hour == 13 and clocks[1].hour == 16
    at_cut = clocks[0] - timedelta(minutes=60)
    assert first_entry(clocks, at_cut) == 0
    assert first_entry(clocks, at_cut + timedelta(seconds=1)) == 1
    before, at = clocks[1] - timedelta(seconds=1), clocks[1]
    initial = dict(fund="test", at=at_cut, entry=0)
    assert len(select([initial, dict(fund="test", at=before, entry=2)], clocks, 1)) == 1
    assert len(select([initial, dict(fund="test", at=at, entry=2)], clocks, 1)) == 2
    assert len(select([initial, dict(fund="test", at=at, entry=1)], clocks, 1)) == 1
    assert merged_n({"test": [(1, 5), (2, 4), (6, 7), (10, 10)]}) == (2, 8)


def measure(raw, sessions):
    rows, deduped, days, close = candidates(raw, sessions)
    base = counts(rows)
    base["filing_rows"] = base.pop("fund_days")
    for subgroup in ("saba", "non_saba"):
        base[f"{subgroup}_filing_rows"] = base.pop(f"{subgroup}_fund_days")
    base.update(unique_fund_ciks=len({r["fund"] for r in rows}), unique_filers=len({r["filer"] for r in rows}))
    result = {"raw": base, "after_fund_day_dedup": counts(deduped), "as_of": str(CUTOFF), "holds": {}}
    mature, scheduled = {}, {}
    for n in HOLDS:
        all_calc = select(deduped, close, n)
        mature[n] = [r for r in all_calc if days[r["exit"]] <= CUTOFF]
        scheduled[n] = all_calc
        result["holds"][str(n)] = {
            "all_scheduled": counts(all_calc),
            "scheduled_close_overlap_only_sensitivity": counts(select(deduped, close, n, at_filing=False)),
            "mature_as_of": counts(mature[n]),
            "all_scheduled_by_filing_year": {str(y): counts([r for r in all_calc if r["day"].year == y])
                                             for y in range(2016, 2027)},
            "mature_by_filing_year": {str(y): counts([r for r in mature[n] if r["day"].year == y])
                                      for y in range(2016, 2027)},
            "last_scheduled_exit": str(max(days[r["exit"]] for r in all_calc)),
        }
    all_days = list(sessions)
    first_sip = bisect_left(all_days, SIP_START)
    result["union_request_shape"] = {}
    for label, pool in [("mature", mature), ("all_scheduled", scheduled)]:
        intervals = defaultdict(list)
        quotes = set()
        losses = {}
        for n, events in pool.items():
            usable, missing = [], []
            for r in events:
                i, j = r["entry"], r["exit"]
                quotes.update(((r["fund"], days[i]), (r["fund"], days[j])))
                # One proposed placebo: latest close that is the fifth fully
                # completed session before acceptance. This requires the
                # exact historical clock only near the 2016+ filing itself.
                p_end = bisect_left(close, r["at"]) - 5
                placebo_end = bisect_left(all_days, days[p_end])
                target_start = bisect_left(all_days, days[i])
                assert target_start >= first_sip
                if placebo_end - n < first_sip:
                    missing.append(r)
                    left = target_start
                else:
                    usable.append(r)
                    left = min(placebo_end - n, target_start)
                right = bisect_left(all_days, days[j])
                intervals[r["fund"]].append((left, right))
            losses[str(n)] = {"fund_windows": len(missing),
                              "entire_filer_day_windows": counts(events)["filer_days"] - counts(usable)["filer_days"]}
        lo = min(i for spans in intervals.values() for i, _ in spans)
        hi = max(j for spans in intervals.values() for _, j in spans)
        intervals["PCEF"] = [(lo, hi)]
        segments, bar_days = merged_n(intervals)
        result["union_request_shape"][label] = {
            "unique_census_fund_ciks": len(intervals) - 1, "fund_and_control_session_rows_bound": bar_days,
            "merged_fund_and_control_segments_before_alias_splits": segments,
            "fund_close_quote_symbol_sessions_before_alias_splits": len(quotes),
            "earliest_bar": str(all_days[lo]), "latest_bar": str(all_days[hi]),
            "placebo_windows_lost_at_sip_start": losses,
        }
    return result


if __name__ == "__main__":
    blob = EVENTS.read_bytes()
    assert sha256(blob).hexdigest() == EVENTS_SHA
    calendar = schedule()
    self_check(calendar)
    result = measure(json.loads(blob), calendar)
    assert tuple(result["raw"][k] for k in ("filing_rows", "filer_days", "unique_fund_ciks", "unique_filers")) == (437, 337, 229, 38)
    print(json.dumps(result, sort_keys=True, indent=2))
