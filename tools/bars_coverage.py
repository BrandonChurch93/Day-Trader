"""Coverage of the price files collected through the workspace's own price lookup, with nothing typed by hand.
  python3 tools/bars_coverage.py --summarise   reads research_rig/data/platform_bars/integrity.json (outside the repo, or
                                               PLATFORM_BARS_DIR) and writes research_rig/platform_bars_coverage.json:
                                               dates, counts and file fingerprints only, no price
  python3 tools/bars_coverage.py --write       writes the tables in docs/research/10_historical_data_and_practice.md from that file
  python3 tools/bars_coverage.py               says whether the tables in the document are what --write would write
The tables also take the one-minute against daily comparison from research_rig/platform_bars_crosscheck.json (written by
research_rig/platform_bars_crosscheck.py).
Runs no rule. --write and the plain check read the two summary files only, which hold no price. --summarise loads the whole of
integrity.json, which does hold a few prices (the first close of each daily file), and copies none of them.
tools/check_repo.py calls in_sync() and fingerprints_agree()."""
import json, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COV = os.path.join(R, "research_rig", "platform_bars_coverage.json"); XC = os.path.join(R, "research_rig", "platform_bars_crosscheck.json"); DOC = os.path.join(R, "docs", "research", "10_historical_data_and_practice.md")
A, B = "<!-- bars:start (written by tools/bars_coverage.py, do not edit by hand) -->", "<!-- bars:end -->"

def summarise():
    d = os.environ.get("PLATFORM_BARS_DIR", os.path.join(R, "research_rig", "data", "platform_bars"))
    I = json.load(open(os.path.join(d, "integrity.json"))); out = {"made_from": "integrity.json, written by research_rig/platform_bars_integrity.py", "one_minute": {}, "daily": {}}
    for s, v in I["one_minute"].items():
        out["one_minute"][s] = {
            "first_date": v["first_date"], "last_date": v["last_date"], "trading_days": v["trading_days"], "rows": v["rows"],
            "days_with_390_rows": v["days_with_390_rows"], "days_with_exactly_the_390_expected_minutes": v["days_with_exactly_the_390_expected_minutes"],
            "weekend_days": v["weekend_days"], "days_with_fewer": len(v["days_with_fewer"]), "days_with_more": len(v["days_with_more"]),
            "short_days_not_known_early_close": [[x["date"], x["rows"]] for x in v["days_fewer_not_known_early_close"]],
            "weekdays_without_data_not_calendar_holiday": v["weekdays_without_data_not_calendar_holiday"],
            "timestamps_not_on_whole_minute": v["timestamps_not_on_whole_minute"], "duplicate_timestamps": v["duplicate_timestamps"],
            "zero_volume_rows": v["value_checks"].get("volume_zero", 0), "other_value_faults": {k: n for k, n in v["value_checks"].items() if k != "volume_zero"},
            "days_with_bars_outside_regular_hours": len(v["days_with_bars_outside_0930_1559_ny"]), "days_first_bar_not_0930": len(v["days_first_bar_not_0930_ny"]),
            "days_last_bar_not_at_expected_time": [[x["date"], x["last_ny"]] for x in v["days_last_bar_not_expected_close"]],
            "calendar_early_closes_with_data": sum(1 for x in v["days_with_fewer"] if x["known_early_close"]),
            "calendar_early_closes_not_210_rows": [[x["date"], x["rows"]] for x in v["days_with_fewer"] if x["known_early_close"] and x["rows"] != 210],
            "calendar_holidays_with_data": v["calendar_holidays_with_data"], "days_first_bar_not_matching_clock_change": len(v["days_first_bar_utc_not_matching_dst"]),
            "requests_with_no_rows_in_range": len(I["sources"][s + "_1min"]["windows_never_in_range"]),
            "of_those_before_first_day": sum(1 for w in I["sources"][s + "_1min"]["windows_never_in_range"] if w.split("_")[1] < v["first_date"]),
            "conflicts_between_pulls": I["conflicts_summary"][s + "_1min"]["conflicting_timestamps"],
            "files": [[f["file"], f["sha256"]] for f in v["files"]]}
    for s, v in I["daily"].items():
        out["daily"][s] = {
            "first_date": v["first_date"], "last_date": v["last_date"], "rows": v["rows"],
            "weekdays_without_row_not_calendar_holiday": v["weekdays_without_row_not_calendar_holiday"], "weekend_rows": len(v["weekend_rows"]),
            "duplicate_dates": v["duplicate_dates"], "zero_volume_rows": v["value_checks"].get("volume_zero", 0),
            "other_value_faults": {k: n for k, n in v["value_checks"].items() if k != "volume_zero"},
            "conflicts_between_pulls": I["conflicts_summary"][s + "_1day"]["conflicting_timestamps"],
            "files": [[f["file"], f["sha256"]] for f in v["files"]]}
    json.dump(out, open(COV, "w"), indent=1); print("research_rig/platform_bars_coverage.json written")

def block():
    C = json.load(open(COV)); M, D = C["one_minute"], C["daily"]; n = lambda x: f"{x:,}"
    L = [A, "", "One-minute prices, regular session only:", "",
         "| Fund | First day | Last day | Trading days | Rows | Days with 390 different times | Days with exactly the 390 minutes of a full session | Short days that are not a known early close | Weekdays with no data that are not a holiday | Repeated times |", "|---|---|---|---|---|---|---|---|---|---|"]
    for s, v in M.items():
        L.append(f"| {s} | {v['first_date']} | {v['last_date']} | {n(v['trading_days'])} | {n(v['rows'])} | {n(v['days_with_390_rows'])} | {n(v['days_with_exactly_the_390_expected_minutes'])} | {len(v['short_days_not_known_early_close'])} | {len(v['weekdays_without_data_not_calendar_holiday'])} | {v['duplicate_timestamps']} |")
    L += ["", "Daily prices:", "", "| Fund | First day | Last day | Rows | Weekdays with no row that are not a holiday | Repeated days | Days with zero volume | Days where two pulls disagreed |", "|---|---|---|---|---|---|---|---|"]
    for s, v in D.items():
        L.append(f"| {s} | {v['first_date']} | {v['last_date']} | {n(v['rows'])} | {len(v['weekdays_without_row_not_calendar_holiday'])} | {v['duplicate_dates']} | {v['zero_volume_rows']} | {v['conflicts_between_pulls']} |")
    L += ["", "What the check found that looks wrong:", ""]
    for s, v in M.items():
        if v["weekdays_without_data_not_calendar_holiday"]: L.append(f"- {s} one-minute: no data on {', '.join(v['weekdays_without_data_not_calendar_holiday'])}, which the check's calendar has as trading days.")
        sd = v["short_days_not_known_early_close"]
        if sd: L.append(f"- {s} one-minute: {len(sd)} short days that are not a known early close, the first on {sd[0][0]} with {sd[0][1]} rows and the last on {sd[-1][0]} with {sd[-1][1]}. Every date is in `research_rig/platform_bars_coverage.json`.")
        if v["timestamps_not_on_whole_minute"]: L.append(f"- {s} one-minute: rows that are not on a whole minute: {len(v['timestamps_not_on_whole_minute'])}. Days with more than 390 rows: {v['days_with_more']}.")
        if v["zero_volume_rows"]: L.append(f"- {s} one-minute: rows with zero volume: {n(v['zero_volume_rows'])}.")
        if v["weekend_days"]: L.append(f"- {s} one-minute: data on weekend days: {', '.join(v['weekend_days'])}.")
        if v["other_value_faults"]: L.append(f"- {s} one-minute: other value faults: {json.dumps(v['other_value_faults'])}.")
        lb = v["days_last_bar_not_at_expected_time"]
        if lb: L.append(f"- {s} one-minute: days whose last bar is not at the expected time (15:59 New York time, or 12:59 on a day the check's calendar has as an early close): {len(lb)}. Every date is in the same file.")
        ec = v["calendar_early_closes_not_210_rows"]
        if ec: L.append(f"- {s} one-minute: of the {v['calendar_early_closes_with_data']} days the check's calendar has as early closes, {len(ec)} do not have the 210 rows of a 13:00 close. The most rows on one is {max(r for _, r in ec)}.")
        if v["calendar_holidays_with_data"]: L.append(f"- {s} one-minute: data on days the check's calendar has as holidays: {', '.join(v['calendar_holidays_with_data'])}.")
        if v["days_first_bar_not_0930"]: L.append(f"- {s} one-minute: days that do not start at 09:30 New York time: {v['days_first_bar_not_0930']}.")
        L.append(f"- {s} one-minute: {v['requests_with_no_rows_in_range']} request windows never returned a row inside the dates asked for, as the join script recorded them. Of those, {v['of_those_before_first_day']} were for dates before the first day in the table.")
    for s, v in D.items():
        if v["weekdays_without_row_not_calendar_holiday"] or v["weekend_rows"] or v["other_value_faults"]:
            L.append(f"- {s} daily: weekdays missing {v['weekdays_without_row_not_calendar_holiday']}, weekend rows {v['weekend_rows']}, value faults {json.dumps(v['other_value_faults'])}.")
    cz = [s for s, v in D.items() if v["conflicts_between_pulls"]]
    if cz: L.append(f"- Daily: two pulls of the same day gave different values for {', '.join(cz)}. The join script kept the row from the file written last. Nothing checked that the later one is the right one.")
    clean = all(v["duplicate_timestamps"] == 0 and not v["other_value_faults"] and v["days_with_bars_outside_regular_hours"] == 0 and not v["weekend_days"] for v in M.values()) and all(v["duplicate_dates"] == 0 and not v["other_value_faults"] and not v["weekend_rows"] for v in D.values())
    if clean: L += ["", "What the check counted and found none of: a repeated time in a one-minute file, a repeated day in a daily file, a weekend row in any file, a missing or zero price (text that is not a number counts as missing), a high below a low, an open or close outside the bar's high and low, a row without six fields, a value that is not finite or is below zero, or a one-minute bar outside the regular session."]
    L += cross() + ["", B]
    return "\n".join(L)

def cross():
    X = json.load(open(XC)); C = json.load(open(COV)); bands = X["bands_bps"]; top = bands[-1]; n = lambda x: f"{x:,}"
    head = ["Up to %d bps" % bands[0]] + ["Over %d, up to %d bps" % (a, b) for a, b in zip(bands, bands[1:])] + ["Over %d bps" % top, "Largest gap"]
    L = ["", "Do the one-minute files and the daily files agree with each other? For every day in both, the day's open, high, low and close were rebuilt from the one-minute bars and compared with the daily row. The gap is in basis points of the daily figure (1 bps is 0.01%). Each cell is a count of days, except in the last column:", "",
         "| Fund | Figure | Days compared | " + " | ".join(head) + " |", "|---|---|---|" + "---|" * len(head)]
    for s, v in X["funds"].items():
        for f, x in v["fields"].items():
            big = max(x[f"dates_over_{top}_bps"], key=lambda p: abs(p[1])) if x[f"dates_over_{top}_bps"] else None
            L.append(f"| {s} | {f} | {n(v['days_in_both'])} | " + " | ".join(n(c) for c in x["days_by_size_of_gap"].values()) + f" | {n(x[f'days_over_{top}_bps'])} | " + (f"{big[1]:+,.1f} bps on {big[0]}" if big else "none over the last band") + " |")
    L += ["", "What that comparison found:", ""]
    for s, v in X["funds"].items():
        ys = v["median_close_gap_bps_by_year"]; lo = min(ys, key=ys.get); hi = max(ys, key=ys.get)
        far = max(ys, key=lambda y: abs(ys[y]))
        L.append(f"- {s}: the middle close gap for each year lies between {ys[lo]:+.2f} bps ({lo}) and {ys[hi]:+.2f} bps ({hi}). The year furthest from zero is {far}.")
        L.append(f"- {s}: days where the one-minute high is above the daily high by more than 1 bps: {v['days_one_minute_high_above_daily_high_by_over_1_bps']}. Days where the one-minute low is below the daily low by more than 1 bps: {v['days_one_minute_low_below_daily_low_by_over_1_bps']}. Neither should happen if both files are right, cover the same session and are adjusted the same way. The comparison does not show which of those fails, or which file is off.")
        short = {d for d, _ in C["one_minute"][s]["short_days_not_known_early_close"]}
        L.append(f"- {s}: the comparison did not leave out the short days that are not a known early close, where minutes are missing from the one-minute files. The yearly middle gaps above include them. Days over {top} bps that are such short days: " + ", ".join(f"{f} {sum(1 for d, _ in x[f'dates_over_{top}_bps'] if d in short)} of {x[f'days_over_{top}_bps']}" for f, x in v["fields"].items()) + ".")
        if v["days_in_one_minute_only"]: L.append(f"- {s}: days in the one-minute files and not in the daily file: {len(v['days_in_one_minute_only'])}.")
    L.append(f"- Every date with a gap over {top} bps is in `research_rig/platform_bars_crosscheck.json`, with the gap and no price.")
    return L

def in_sync():
    t = open(DOC).read(); m = re.search(re.escape(A) + r".*?" + re.escape(B), t, re.S)
    return bool(m) and t.count(A) == 1 and t.count(B) == 1 and m.group(0) == block()   # one block only: a second, hand-made one would not be checked

def fingerprints_agree():
    """The file fingerprints listed in the coverage summary, joined the way research_rig/provenance.py joins them, must give
    the two fingerprints that provenance.json holds for the price files. This ties the summary to the same files, by name
    and content. It does not show that the counts in the summary were worked out from them."""
    import hashlib
    C = json.load(open(COV)); P = json.load(open(os.path.join(R, "research_rig", "provenance.json")))["inputs"]
    for part, key in (("one_minute", "data/platform_bars/1min/*.csv"), ("daily", "data/platform_bars/1day/*.csv")):
        fs = sorted((f, s) for v in C[part].values() for f, s in v["files"])
        lines = "".join(f"{os.path.basename(f)} {s}\n" for f, s in fs)
        if key not in P or P[key]["files"] != len(fs) or P[key]["sha256_of_name_and_sha256_lines"] != hashlib.sha256(lines.encode()).hexdigest(): return False
    return True

if __name__ == "__main__":
    if "--summarise" in sys.argv: summarise()
    elif "--write" in sys.argv:
        t = open(DOC).read(); m = re.search(re.escape(A) + r".*?" + re.escape(B), t, re.S)
        if not m: sys.exit("markers not found in " + DOC)
        open(DOC, "w").write(t[:m.start()] + block() + t[m.end():]); print("coverage tables written")
    else:
        print("in sync" if in_sync() else "out of date: run python3 tools/bars_coverage.py --write"); sys.exit(0 if in_sync() else 1)
