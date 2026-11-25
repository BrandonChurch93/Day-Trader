"""Gap and sanity check of the price files collected through the workspace's own price lookup on 2026-11-25.
Reads data/platform_bars/ (or PLATFORM_BARS_DIR) and writes integrity.json and INTEGRITY.md there, outside the repo.
Runs no rule and works out no return. Written by a collection agent; the holiday calendar in it was written from memory.
Checks only counts, dates, gaps, duplicates, timestamps, zero/missing values, high/low sanity and sha256.
No returns or price-move statistics are computed."""
import csv, glob, hashlib, json, math, os, datetime as dt
from collections import defaultdict, Counter
from zoneinfo import ZoneInfo

OUT = os.environ.get("PLATFORM_BARS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "platform_bars"))
NY, UTC = ZoneInfo("America/New_York"), ZoneInfo("UTC")


# ---- rule-based NYSE calendar (written from memory; used only to label gaps; its accuracy is UNKNOWN) ----
def easter(y):
    a = y % 19; b = y // 100; c = y % 100; d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451; mo = (h + l - 7 * m + 114) // 31; da = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, mo, da)


def nth(y, m, wd, n):
    d = dt.date(y, m, 1); d += dt.timedelta((wd - d.weekday()) % 7); return d + dt.timedelta(7 * (n - 1))


def last(y, m, wd):
    d = dt.date(y, m + 1, 1) - dt.timedelta(1) if m < 12 else dt.date(y, 12, 31)
    return d - dt.timedelta((d.weekday() - wd) % 7)


def obs(d):
    return d + dt.timedelta(1) if d.weekday() == 6 else (d - dt.timedelta(1) if d.weekday() == 5 else d)


SPECIAL = {dt.date(1994, 4, 27): "Nixon funeral", dt.date(2001, 9, 11): "9/11", dt.date(2001, 9, 12): "9/11", dt.date(2001, 9, 13): "9/11",
           dt.date(2001, 9, 14): "9/11", dt.date(2004, 6, 11): "Reagan funeral", dt.date(2007, 1, 2): "Ford funeral",
           dt.date(2012, 10, 29): "Hurricane Sandy", dt.date(2012, 10, 30): "Hurricane Sandy",
           dt.date(2018, 12, 5): "Bush funeral", dt.date(2025, 1, 9): "Carter funeral"}


def holidays(y):
    h = {obs(dt.date(y, 1, 1)): "New Year", nth(y, 2, 0, 3): "Presidents",
         easter(y) - dt.timedelta(2): "Good Friday", last(y, 5, 0): "Memorial", obs(dt.date(y, 7, 4)): "July 4",
         nth(y, 9, 0, 1): "Labor", nth(y, 11, 3, 4): "Thanksgiving", obs(dt.date(y, 12, 25)): "Christmas"}
    if y >= 1998:  # NYSE first closed for MLK day in 1998
        h[nth(y, 1, 0, 3)] = "MLK"
    if y >= 2022:
        h[obs(dt.date(y, 6, 19))] = "Juneteenth"
    h = {d: n for d, n in h.items() if d.year == y}  # New Year on Sat is not observed on Dec 31
    h.update({d: n for d, n in SPECIAL.items() if d.year == y})
    return h


def early_closes(y):
    e = {nth(y, 11, 3, 4) + dt.timedelta(1): "day after Thanksgiving"}
    for d, n in [(dt.date(y, 12, 24), "Christmas Eve"), (dt.date(y, 7, 3), "July 3")]:
        if d.weekday() < 5:
            e[d] = n
    hol = holidays(y)   # added after an outside check: a day the market is shut is not an early close (2020-07-03, 2021-12-24, 2026-07-03)
    return {d: n for d, n in e.items() if d not in hol}


HOL, EARLY = {}, {}
for y in range(1990, 2028):
    HOL.update(holidays(y)); EARLY.update(early_closes(y))
# Added after an outside check. One early close the rules above miss, from the exchange's own record of special closings
# (https://www.ltadvisors.net/Info/research/closings.pdf, "closed at 1:00 pm, Friday after Christmas Day").
# That record runs to December 2007. For September 2003 to December 2007 the rules above now give the same early closes as it does.
# After 2007 the early closes here are still from memory.
EARLY[dt.date(2003, 12, 26)] = "Friday after Christmas (exchange record)"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def num(x):
    try:
        return float(x)
    except Exception:
        return None


def value_checks(rows):
    """rows: list of [ts, o, h, l, c, v] strings. Returns counts and examples."""
    c = Counter(); ex = defaultdict(list)
    for r in rows:
        o, h, l, cl, v = (num(x) for x in r[1:6])
        def flag(k):
            c[k] += 1
            if len(ex[k]) < 20: ex[k].append(r[0])
        if len(r) != 6: flag("row_without_six_fields")
        if any(x is not None and (not math.isfinite(x) or x < 0) for x in (o, h, l, cl, v)): flag("value_not_a_number_or_below_zero")
        if any(x is None for x in (o, h, l, cl)): flag("price_missing")
        elif any(x == 0 for x in (o, h, l, cl)): flag("price_zero")
        if v is None: flag("volume_missing")
        elif v == 0: flag("volume_zero")
        if h is not None and l is not None and h < l: flag("high_lt_low")
        if None not in (o, h, l, cl) and (h < max(o, cl) or l > min(o, cl)): flag("open_or_close_outside_high_low")
    return dict(c), dict(ex)


def weekday_gaps(dates):
    s = set(dates); d = min(dates); out = []
    while d <= max(dates):
        if d.weekday() < 5 and d not in s:
            out.append(d)
        d += dt.timedelta(1)
    return out


def read(paths):
    rows = []
    for p in paths:
        with open(p, newline="") as fh:
            r = csv.reader(fh); next(r)
            rows += [x for x in r if x]
    return rows


def files_info(paths):
    return [{"file": os.path.relpath(p, OUT), "bytes": os.path.getsize(p), "sha256": sha(p)} for p in sorted(paths)]


def check_1min(sym):
    paths = sorted(glob.glob(f"{OUT}/1min/{sym}_1min_*.csv"))
    if not paths: return None
    rows = read(paths)
    ts = [r[0] for r in rows]
    dup = [t for t, n in Counter(ts).items() if n > 1]
    per_day = defaultdict(list)
    for t in ts:
        per_day[dt.date.fromisoformat(t[:10])].append(t)
    days = sorted(per_day)
    eq, fewer, more = 0, [], []
    off_hours_days, first_not_0930, last_not_1559 = [], [], []
    first_utc = {}
    off_minute = [t for t in ts if not t.endswith(":00") or len(t) != 19]
    for d in days:
        L = sorted(per_day[d]); n = len(set(L))
        if n == 390: eq += 1
        elif n < 390: fewer.append({"date": str(d), "rows": n, "known_early_close": EARLY.get(d)})
        else: more.append({"date": str(d), "rows": n})
        loc = [dt.datetime.fromisoformat(t).replace(tzinfo=UTC).astimezone(NY) for t in L]
        if any(not (dt.time(9, 30) <= x.time() <= dt.time(15, 59)) or x.date() != d for x in loc):
            off_hours_days.append(str(d))
        if loc[0].time() != dt.time(9, 30): first_not_0930.append({"date": str(d), "first_ny": loc[0].strftime("%H:%M")})
        exp_last = dt.time(12, 59) if d in EARLY else dt.time(15, 59)
        if loc[-1].time() != exp_last: last_not_1559.append({"date": str(d), "last_ny": loc[-1].strftime("%H:%M")})
        first_utc[d] = L[0][11:16]
    # DST: expected first-bar UTC time is 09:30 New York converted to UTC for that date
    mism = []
    for d in days:
        exp = dt.datetime.combine(d, dt.time(9, 30), NY).astimezone(UTC).strftime("%H:%M")
        if first_utc[d] != exp: mism.append({"date": str(d), "first_utc": first_utc[d], "expected_utc": exp})
    switches = []
    for a, b in zip(days, days[1:]):
        oa = dt.datetime.combine(a, dt.time(12), NY).utcoffset(); ob = dt.datetime.combine(b, dt.time(12), NY).utcoffset()
        if oa != ob:
            switches.append({"last_day_before": str(a), "first_utc_before": first_utc[a],
                             "first_day_after": str(b), "first_utc_after": first_utc[b]})
    gaps = weekday_gaps(days)
    gl = [{"date": str(g), "calendar_holiday": HOL.get(g)} for g in gaps]
    vc, vex = value_checks(rows)
    return {"first_date": str(days[0]), "last_date": str(days[-1]), "trading_days": len(days), "rows": len(rows),
            "days_with_390_rows": eq, "days_with_fewer": fewer, "days_with_more": more,
            "days_fewer_not_known_early_close": [x for x in fewer if not x["known_early_close"]],
            "weekdays_without_data": gl,
            "weekdays_without_data_not_calendar_holiday": [x["date"] for x in gl if not x["calendar_holiday"]],
            "calendar_holidays_with_data": [str(d) for d in days if d in HOL],
            "timestamps_not_on_whole_minute": off_minute,
            "duplicate_timestamps": len(dup), "duplicate_examples": dup[:20],
            "value_checks": vc, "value_check_examples": vex,
            "days_with_bars_outside_0930_1559_ny": off_hours_days,
            "days_first_bar_not_0930_ny": first_not_0930,
            "days_last_bar_not_expected_close": last_not_1559,
            "days_first_bar_utc_not_matching_dst": mism,
            "dst_switches": switches, "files": files_info(paths)}


def check_1day(sym):
    p = f"{OUT}/1day/{sym}_1day.csv"
    if not os.path.exists(p): return None
    rows = read([p])
    ds = [r[0] for r in rows]
    bad_fmt = [d for d in ds if len(d) != 10]
    dates = sorted(dt.date.fromisoformat(d[:10]) for d in ds)
    dup = [t for t, n in Counter(ds).items() if n > 1]
    gaps = weekday_gaps(dates)
    gl = [{"date": str(g), "calendar_holiday": HOL.get(g)} for g in gaps]
    vc, vex = value_checks(rows)
    first = min(rows, key=lambda r: r[0])
    return {"first_date": str(dates[0]), "last_date": str(dates[-1]), "rows": len(rows),
            "weekdays_without_row": len(gl), "weekdays_without_row_not_calendar_holiday": [x["date"] for x in gl if not x["calendar_holiday"]],
            "weekend_rows": [str(d) for d in dates if d.weekday() >= 5],
            "calendar_holidays_with_row": [str(d) for d in dates if d in HOL],
            "duplicate_dates": len(dup), "non_plain_date_format": len(bad_fmt),
            "value_checks": vc, "value_check_examples": vex,
            "first_close": first[4], "files": files_info([p])}


def main():
    from platform_bars_consolidate import SYMS_1MIN, SYMS_1DAY
    rep = {"one_minute": {s: check_1min(s) for s in SYMS_1MIN}, "daily": {s: check_1day(s) for s in SYMS_1DAY}}
    for name in ["sources.json", "conflicts_summary.json"]:
        p = os.path.join(OUT, name)
        if os.path.exists(p):
            rep[name.split(".")[0]] = json.load(open(p))
    json.dump(rep, open(os.path.join(OUT, "integrity.json"), "w"), indent=1)
    write_md(rep)
    print("wrote integrity.json and INTEGRITY.md")


def fmt_list(xs, n=60):
    xs = list(xs)
    return ", ".join(xs[:n]) + (f" ... ({len(xs) - n} more, see integrity.json)" if len(xs) > n else "") if xs else "none"


def write_md(rep):
    M = "MEASURED"
    L = ["# Integrity report: platform price bars", "",
         "Every line marked MEASURED was printed by platform_bars_integrity.py from the consolidated files.",
         "Lines marked UNKNOWN are not established by this script.", "",
         "UNKNOWN: whether the daily prices are adjusted for dividends. Split adjustment is also not verified here.",
         "UNKNOWN: the holiday labels come from a rule-based NYSE calendar written from memory, not from an exchange source.",
         "UNKNOWN: whether the provider's data is complete or correct beyond the checks below.", "",
         "## Pull notes", "",
         "These lines come from the pull run logs (exec cell output), not from this script. They are MEASURED in those logs.", "",
         "- MEASURED (pull log): SPY one-minute requests for windows before 2003-09-08 returned no in-range rows. Probes back to 1993 returned rows dated 2026-11-23 instead.",
         "- MEASURED (pull log): QQQ one-minute requests before the 2011-03-21 week returned no in-range rows. Probes back to 1999 returned rows dated 2026-11-23.",
         "- MEASURED (pull log): single-day SPY one-minute requests for 2004-12-31 and 2010-12-31 returned only out-of-range rows. The SPY daily file does have rows for both dates.",
         "- MEASURED (pull log): daily requests for 1993-2004 returned no rows for DBC, BIL, XLC, XLRE, and for 2005-2016 for XLC. These are before each fund's first date.",
         "- MEASURED (pull log): rate-limit replies started around the 2022 SPY windows. Two windows failed after all retries and were pulled again later with success. The pull then ran one call at a time with a 1 s pause.",
         "- MEASURED (pull log): 13 older SPY and 10 older QQQ probe files hold only date, close, volume (or date, open, close, volume for two daily files). They are skipped. The SPY windows they covered were pulled again with all fields.",
         "- MEASURED: one SPY daily row (2026-11-24) differs between two pulls in volume only. Both are in conflicts.csv. The row from the file written last was kept. Nothing checked that it is the right one.",
         ""]
    src = rep.get("sources", {})
    conf = rep.get("conflicts_summary", {})
    L += ["## One-minute bars", ""]
    for s, r in rep["one_minute"].items():
        L.append(f"### {s} one-minute")
        if not r:
            L += [f"{M}: no consolidated file.", ""]; continue
        sk = src.get(f"{s}_1min", {}); ck = conf.get(f"{s}_1min", {})
        vc = r["value_checks"]
        L += [f"- {M}: first day {r['first_date']}, last day {r['last_date']}.",
              f"- {M}: {r['trading_days']} trading days, {r['rows']} rows.",
              f"- {M}: {r['days_with_390_rows']} days have exactly 390 rows. {len(r['days_with_fewer'])} days have fewer. {len(r['days_with_more'])} days have more.",
              f"- {M}: days with fewer rows (date:rows): " + fmt_list(f"{x['date']}:{x['rows']}" + ("(early close)" if x['known_early_close'] else "") for x in r['days_with_fewer']),
              f"- {M}: days with fewer rows that are not a known early close: " + fmt_list(f"{x['date']}:{x['rows']}" for x in r['days_fewer_not_known_early_close']),
              f"- {M}: days with more rows: " + fmt_list(f"{x['date']}:{x['rows']}" for x in r['days_with_more']),
              f"- {M}: {len(r['weekdays_without_data'])} weekdays inside the span have no data. Not a calendar holiday: " + fmt_list(r['weekdays_without_data_not_calendar_holiday']),
              f"- {M}: weekdays without data (all): " + fmt_list((x['date'] + (f"({x['calendar_holiday']})" if x['calendar_holiday'] else "") for x in r['weekdays_without_data']), 400),
              f"- {M}: calendar holidays that do have data: " + fmt_list(r['calendar_holidays_with_data']),
              f"- {M}: duplicate timestamps in the consolidated files: {r['duplicate_timestamps']}.",
              f"- {M}: timestamps not on a whole minute (seconds not 00): {len(r['timestamps_not_on_whole_minute'])}: " + fmt_list(r['timestamps_not_on_whole_minute']),
              f"- {M}: exact duplicate rows removed during consolidation: {ck.get('exact_duplicates_removed')}. Timestamps where two pulls disagreed: {ck.get('conflicting_timestamps')} (listed in conflicts.csv; the most recently written pull was kept).",
              f"- {M}: zero volume rows {vc.get('volume_zero', 0)}, missing volume rows {vc.get('volume_missing', 0)}.",
              f"- {M}: rows with high below low {vc.get('high_lt_low', 0)}. Rows with a zero price {vc.get('price_zero', 0)}. Rows with a missing price {vc.get('price_missing', 0)}. Rows where open or close lies outside high-low {vc.get('open_or_close_outside_high_low', 0)}.",
              f"- {M}: days with a bar outside 09:30-15:59 New York time: " + fmt_list(r['days_with_bars_outside_0930_1559_ny']),
              f"- {M}: days whose first bar is not 09:30 New York time: " + fmt_list(f"{x['date']}({x['first_ny']})" for x in r['days_first_bar_not_0930_ny']),
              f"- {M}: days whose last bar is not 15:59 (12:59 on known early closes) New York time: " + fmt_list(f"{x['date']}({x['last_ny']})" for x in r['days_last_bar_not_expected_close']),
              f"- {M}: days whose first bar in UTC does not match the daylight-saving rule (14:30 UTC in winter, 13:30 UTC in summer): " + fmt_list(f"{x['date']}({x['first_utc']} vs {x['expected_utc']})" for x in r['days_first_bar_utc_not_matching_dst']),
              f"- {M}: {len(r['dst_switches'])} daylight-saving switches inside the span. First bar UTC before and after each: " + fmt_list((f"{x['last_day_before']} {x['first_utc_before']} -> {x['first_day_after']} {x['first_utc_after']}" for x in r['dst_switches']), 100),
              f"- {M}: pull windows that never returned in-range rows: {len(sk.get('windows_never_in_range', []))}: " + fmt_list(sk.get('windows_never_in_range', []), 100),
              f"- {M}: source files skipped because their columns are not date,open,high,low,close,volume (older probes): {len(sk.get('bad_header_files', []))}.",
              "", "Files (MEASURED):", ""]
        L += [f"- {f['file']} {f['bytes']} bytes sha256 {f['sha256']}" for f in r["files"]]
        L.append("")
    L += ["## Daily bars", "",
          "| symbol | first date | last date | rows | first close | weekdays without row (not calendar holiday) | duplicates | zero/missing values | high<low | bytes | sha256 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    notes = []
    for s, r in rep["daily"].items():
        if not r:
            L.append(f"| {s} | no file | | | | | | | | | |"); continue
        vc = r["value_checks"]; zm = sum(vc.get(k, 0) for k in ("price_zero", "price_missing", "volume_zero", "volume_missing"))
        f = r["files"][0]
        L.append(f"| {s} | {r['first_date']} | {r['last_date']} | {r['rows']} | {r['first_close']} | {r['weekdays_without_row']} ({len(r['weekdays_without_row_not_calendar_holiday'])}) | {r['duplicate_dates']} | {zm} | {vc.get('high_lt_low', 0)} | {f['bytes']} | {f['sha256']} |")
        if r['weekdays_without_row_not_calendar_holiday']:
            notes.append(f"- {M}: {s} weekdays without a row that are not calendar holidays: " + fmt_list(r['weekdays_without_row_not_calendar_holiday']))
        if r['calendar_holidays_with_row'] or r['weekend_rows']:
            notes.append(f"- {M}: {s} rows on calendar holidays: {fmt_list(r['calendar_holidays_with_row'])}; rows on weekends: {fmt_list(r['weekend_rows'])}")
        if zm or vc.get('open_or_close_outside_high_low'):
            notes.append(f"- {M}: {s} value checks: {json.dumps(vc)}")
        sk = src.get(f"{s}_1day", {})
        if sk.get("windows_never_in_range"):
            notes.append(f"- {M}: {s} daily pull windows with no in-range rows: {fmt_list(sk['windows_never_in_range'])}")
    L += ["", "All table values are MEASURED.", ""] + notes
    open(os.path.join(OUT, "INTEGRITY.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
