"""Coverage of the price files collected through the workspace's own price lookup, with nothing typed by hand.
  python3 tools/bars_coverage.py --summarise   reads research_rig/data/platform_bars/integrity.json (outside the repo, or
                                               PLATFORM_BARS_DIR) and writes research_rig/platform_bars_coverage.json:
                                               dates, counts and file fingerprints only, no price
  python3 tools/bars_coverage.py --write       writes the tables in docs/research/10_historical_data_and_practice.md from that file
  python3 tools/bars_coverage.py               says whether the tables in the document are what --write would write
Runs no rule and reads no price. tools/check_repo.py calls in_sync()."""
import json, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COV = os.path.join(R, "research_rig", "platform_bars_coverage.json"); DOC = os.path.join(R, "docs", "research", "10_historical_data_and_practice.md")
A, B = "<!-- bars:start (written by tools/bars_coverage.py, do not edit by hand) -->", "<!-- bars:end -->"

def summarise():
    d = os.environ.get("PLATFORM_BARS_DIR", os.path.join(R, "research_rig", "data", "platform_bars"))
    I = json.load(open(os.path.join(d, "integrity.json"))); out = {"made_from": "integrity.json, written by research_rig/platform_bars_integrity.py", "one_minute": {}, "daily": {}}
    for s, v in I["one_minute"].items():
        out["one_minute"][s] = {
            "first_date": v["first_date"], "last_date": v["last_date"], "trading_days": v["trading_days"], "rows": v["rows"],
            "days_with_390_rows": v["days_with_390_rows"], "days_with_fewer": len(v["days_with_fewer"]), "days_with_more": len(v["days_with_more"]),
            "short_days_not_known_early_close": [[x["date"], x["rows"]] for x in v["days_fewer_not_known_early_close"]],
            "weekdays_without_data_not_calendar_holiday": v["weekdays_without_data_not_calendar_holiday"],
            "timestamps_not_on_whole_minute": v["timestamps_not_on_whole_minute"], "duplicate_timestamps": v["duplicate_timestamps"],
            "zero_volume_rows": v["value_checks"].get("volume_zero", 0), "other_value_faults": {k: n for k, n in v["value_checks"].items() if k != "volume_zero"},
            "days_with_bars_outside_regular_hours": len(v["days_with_bars_outside_0930_1559_ny"]), "days_first_bar_not_0930": len(v["days_first_bar_not_0930_ny"]),
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
         "| Fund | First day | Last day | Trading days | Rows | Days with all 390 minutes | Short days that are not a known early close | Weekdays with no data that are not a holiday | Repeated times |", "|---|---|---|---|---|---|---|---|---|"]
    for s, v in M.items():
        L.append(f"| {s} | {v['first_date']} | {v['last_date']} | {n(v['trading_days'])} | {n(v['rows'])} | {n(v['days_with_390_rows'])} | {len(v['short_days_not_known_early_close'])} | {len(v['weekdays_without_data_not_calendar_holiday'])} | {v['duplicate_timestamps']} |")
    L += ["", "Daily prices:", "", "| Fund | First day | Last day | Rows | Weekdays with no row that are not a holiday | Repeated days | Days with zero volume | Days where two pulls disagreed |", "|---|---|---|---|---|---|---|---|"]
    for s, v in D.items():
        L.append(f"| {s} | {v['first_date']} | {v['last_date']} | {n(v['rows'])} | {len(v['weekdays_without_row_not_calendar_holiday'])} | {v['duplicate_dates']} | {v['zero_volume_rows']} | {v['conflicts_between_pulls']} |")
    L += ["", "What the check found that looks wrong:", ""]
    for s, v in M.items():
        if v["weekdays_without_data_not_calendar_holiday"]: L.append(f"- {s} one-minute: no data on {', '.join(v['weekdays_without_data_not_calendar_holiday'])}, which the check's calendar has as trading days.")
        sd = v["short_days_not_known_early_close"]
        if sd: L.append(f"- {s} one-minute: {len(sd)} short days that are not a known early close, the first on {sd[0][0]} with {sd[0][1]} rows and the last on {sd[-1][0]} with {sd[-1][1]}. Every date is in `research_rig/platform_bars_coverage.json`.")
        if v["timestamps_not_on_whole_minute"]: L.append(f"- {s} one-minute: rows that are not on a whole minute: {len(v['timestamps_not_on_whole_minute'])}. Days with more than 390 rows because of it: {v['days_with_more']}.")
        if v["zero_volume_rows"]: L.append(f"- {s} one-minute: rows with zero volume: {n(v['zero_volume_rows'])}.")
        if v["other_value_faults"]: L.append(f"- {s} one-minute: other value faults: {json.dumps(v['other_value_faults'])}.")
        if v["days_first_bar_not_0930"]: L.append(f"- {s} one-minute: days that do not start at 09:30 New York time: {v['days_first_bar_not_0930']}.")
        L.append(f"- {s} one-minute: {v['requests_with_no_rows_in_range']} requests returned no row inside the dates asked for. Of those, {v['of_those_before_first_day']} were for dates before the first day in the table.")
    for s, v in D.items():
        if v["weekdays_without_row_not_calendar_holiday"] or v["weekend_rows"] or v["other_value_faults"]:
            L.append(f"- {s} daily: weekdays missing {v['weekdays_without_row_not_calendar_holiday']}, weekend rows {v['weekend_rows']}, value faults {json.dumps(v['other_value_faults'])}.")
    cz = [s for s, v in D.items() if v["conflicts_between_pulls"]]
    if cz: L.append(f"- Daily: two pulls of the same day gave different values for {', '.join(cz)}. The later pull was kept.")
    clean = all(v["duplicate_timestamps"] == 0 and not v["other_value_faults"] and v["days_with_bars_outside_regular_hours"] == 0 for v in M.values()) and all(v["duplicate_dates"] == 0 and not v["other_value_faults"] and not v["weekend_rows"] for v in D.values())
    if clean: L += ["", "What the check did not find in any file: a repeated time or day, a missing or zero price, a high below a low, a weekend row, or a bar outside the regular session."]
    L += ["", B]
    return "\n".join(L)

def in_sync():
    t = open(DOC).read(); m = re.search(re.escape(A) + r".*?" + re.escape(B), t, re.S)
    return bool(m) and m.group(0) == block()

if __name__ == "__main__":
    if "--summarise" in sys.argv: summarise()
    elif "--write" in sys.argv:
        t = open(DOC).read(); m = re.search(re.escape(A) + r".*?" + re.escape(B), t, re.S)
        if not m: sys.exit("markers not found in " + DOC)
        open(DOC, "w").write(t[:m.start()] + block() + t[m.end():]); print("coverage tables written")
    else:
        print("in sync" if in_sync() else "out of date: run python3 tools/bars_coverage.py --write"); sys.exit(0 if in_sync() else 1)
