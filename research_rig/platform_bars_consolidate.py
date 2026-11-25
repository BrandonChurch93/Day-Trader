"""Joins the files returned by the workspace's own price lookup into one file per fund. Runs no rule.
Only useful on the research machine, where the pulls were made on 2026-11-25. Kept as the record of how the files were built.

Source: /home/user/workspace/.tool_artifacts/finance/*/*/<SYM>_price_history_<start>_<end>_<interval>_<tag>.csv
Rules:
- keep only rows whose date (first 10 chars of the timestamp) lies inside the requested window in the file name
- remove exact duplicate rows
- if two pulls give different values for the same timestamp: list every case in conflicts.csv;
  the row from the most recently written source file is kept (explicit rule, counted in conflicts_summary.json)
Output: data/platform_bars/ (or PLATFORM_BARS_DIR), outside the repo
  1min/<SYM>_1min_<YYYY>.csv   (timestamps in UTC as delivered)
  1day/<SYM>_1day.csv
  sources.json  (per symbol/interval: files read, files with in-range rows, windows with no in-range rows)
"""
import csv, glob, json, os, re, sys
from collections import defaultdict

# Where the workspace wrote each pull, and where the consolidated files go. Both can be moved with a variable.
SRC = os.environ.get("PLATFORM_PULLS_GLOB", "/home/user/workspace/.tool_artifacts/finance/*/*/*.csv")
OUT = os.environ.get("PLATFORM_BARS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "platform_bars"))
SYMS_1MIN = ["SPY", "QQQ"]
SYMS_1DAY = ["SPY", "QQQ", "EFA", "IEF", "VNQ", "DBC", "BIL", "GLD", "TLT", "VTI", "IWM",
             "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLC", "XLRE"]
PAT = re.compile(r"^([A-Z]+)_price_history_(\d{4}-\d\d-\d\d)_(\d{4}-\d\d-\d\d)_(1min|1day)_[0-9a-f]+\.csv$")
COLS = ["date", "open", "high", "low", "close", "volume"]


def main():
    wanted = {("1min", s) for s in SYMS_1MIN} | {("1day", s) for s in SYMS_1DAY}
    files = defaultdict(list)
    for f in glob.glob(SRC):
        m = PAT.match(os.path.basename(f))
        if not m:
            continue
        sym, s, e, iv = m.groups()
        if (iv, sym) in wanted:
            files[(iv, sym)].append((os.path.getmtime(f), f, s, e))
    sources, conflicts_all, summary = {}, [], {}
    for (iv, sym), fl in sorted(files.items()):
        fl.sort()  # oldest first; later files overwrite on conflict
        rows = {}
        n_exact_dup = 0
        conf = []
        in_range_windows, empty_windows = set(), set()
        bad_header = []
        for mt, f, s, e in fl:
            with open(f, newline="") as fh:
                r = csv.reader(fh)
                hdr = next(r, None)
                if hdr is None or [h.strip() for h in hdr] != COLS:
                    bad_header.append(f)
                    continue
                k = 0
                for row in r:
                    if not row:
                        continue
                    row = [x.strip() for x in row]
                    d = row[0][:10]
                    if not (s <= d <= e):
                        continue
                    k += 1
                    ts = row[0]
                    vals = tuple(row[1:])
                    if ts in rows:
                        if rows[ts][0] == vals:
                            n_exact_dup += 1
                        else:
                            conf.append({"symbol": sym, "interval": iv, "timestamp": ts,
                                         "kept_file": f, "kept": list(vals),
                                         "dropped_file": rows[ts][1], "dropped": list(rows[ts][0])})
                            rows[ts] = (vals, f)
                    else:
                        rows[ts] = (vals, f)
            (in_range_windows if k else empty_windows).add(s + "_" + e)
        empty_only = sorted(empty_windows - in_range_windows)
        sources[f"{sym}_{iv}"] = {"files_read": len(fl), "windows_with_in_range_rows": len(in_range_windows),
                                  "windows_never_in_range": empty_only, "bad_header_files": bad_header}
        summary[f"{sym}_{iv}"] = {"rows_kept": len(rows), "exact_duplicates_removed": n_exact_dup,
                                  "conflicting_timestamps": len(conf)}
        conflicts_all += conf
        od = os.path.join(OUT, iv)
        os.makedirs(od, exist_ok=True)
        keys = sorted(rows)
        if iv == "1min":
            for old in glob.glob(os.path.join(od, f"{sym}_1min_*.csv")):
                os.remove(old)
            by_year = defaultdict(list)
            for ts in keys:
                by_year[ts[:4]].append(ts)
            for y, ks in by_year.items():
                write(os.path.join(od, f"{sym}_1min_{y}.csv"), ks, rows)
        else:
            write(os.path.join(od, f"{sym}_1day.csv"), keys, rows)
    with open(os.path.join(OUT, "sources.json"), "w") as fh:
        json.dump(sources, fh, indent=1)
    with open(os.path.join(OUT, "conflicts_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    with open(os.path.join(OUT, "conflicts.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["symbol", "interval", "timestamp", "kept", "dropped", "kept_file", "dropped_file"])
        for c in conflicts_all:
            w.writerow([c["symbol"], c["interval"], c["timestamp"], "|".join(c["kept"]), "|".join(c["dropped"]),
                        c["kept_file"], c["dropped_file"]])
    missing = sorted(f"{s}_{iv}" for iv, s in wanted if (iv, s) not in files)
    print(json.dumps({"consolidated": summary, "no_source_files": missing}, indent=0))


def write(path, keys, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(COLS)
        for ts in keys:
            w.writerow([ts, *rows[ts][0]])


if __name__ == "__main__":
    main()
