"""Plan 11 split check: are the daily price files adjusted for stock splits? Run from research_rig/.

For list members that split between 2026-03-02 and 2026-11-24, compares our daily file with the cited pages:
  - our close on the last day before the split, times the split ratio, against the as-traded close a page gives (STATED
    by that page), and
  - our open on the first split-adjusted day against our close the day before. An unadjusted file would jump by the ratio.
Reads only the two bars around each split. Works out no event return. Writes research_rig/split_check_11.json.
Usage:  python3 split_check_11.py"""
import os, json
import common_11 as C

ST_URL = "https://www.stocktitan.net/articles/stock-splits-2026-list-big-companies"
SX_URL = "https://www.stocksxray.com/stock-splits"
# symbol, new shares per old share, first split-adjusted trading day, as-traded close before the split (None: not given),
# sources. Typed from the pages on 2026-11-25; STATED by them.
SPLITS = [
    ("BKNG", 25, "2026-04-06", 4194.31, [SX_URL, ST_URL]),
    ("CVNA", 5, "2026-05-08", 400.02, [SX_URL, ST_URL]),
    ("KLAC", 10, "2026-06-12", 2411.64, [SX_URL, ST_URL]),
    ("DD", 1 / 3, "2026-06-24", 46.67, [SX_URL]),
    ("HON", 1 / 2, "2026-06-29", None, ["https://www.honeywell.com/us/en/news/press-releases/2026/06/honeywell-board-of-directors-sets-record-date-and-announces-expected-timing-for-spin-off-of-honeywell-aerospace-and-honeywell-reverse-stock-split"]),
    ("MLI", 2, "2026-07-01", 122.93, ["https://www.sec.gov/Archives/edgar/data/89439/000008943926000025/ex-99_16302026stocksplit.htm", ST_URL]),
    ("CRWD", 4, "2026-07-02", 772.74, [SX_URL, ST_URL]),
    ("MNST", 2, "2026-08-11", 91.43, [SX_URL, ST_URL]),
    ("APH", 2, "2026-09-03", 160.08, [SX_URL, ST_URL]),
    ("SNDK", 8, "2026-11-20", 755.16, ["https://www.stocktitan.net/sec-filings/SNDK/8-k-sandisk-corp-reports-material-event-8248455531a3.html", ST_URL]),
]

def check(rows_of=C.price_rows, splits=SPLITS):
    out = []
    for sym, ratio, day, traded, src in splits:
        P = rows_of(sym)
        if not P or day not in P: out.append(dict(symbol=sym, found=False)); continue
        prev = max(d for d in P if d < day)
        r = dict(symbol=sym, found=True, ratio=round(ratio, 4), first_adjusted_day=day, day_before=prev, our_close_before=P[prev][1],
                 our_open_after_over_close_before=round(P[day][0] / P[prev][1], 3), sources=src)
        if traded is not None: r.update(as_traded_close_before=traded, our_close_times_ratio_over_as_traded=round(P[prev][1] * ratio / traded, 4))
        # adjusted: no jump near the ratio overnight, and our earlier close equals the as-traded close divided by the ratio
        jump = abs(r["our_open_after_over_close_before"] * ratio - 1) < 0.25 if ratio != 1 else False
        r["adjusted"] = (not jump) and (traded is None or abs(r["our_close_times_ratio_over_as_traded"] - 1) < 0.002)
        out.append(r)
    return out

def main():
    R = check()
    S = dict(made_by="research_rig/split_check_11.py", splits_checked=len(R), found=sum(r["found"] for r in R),
             adjusted=sum(r.get("adjusted", False) for r in R),
             with_as_traded_close=sum("as_traded_close_before" in r for r in R),
             close_match_within_0_2pct=sum(abs(r.get("our_close_times_ratio_over_as_traded", 9) - 1) < 0.002 for r in R),
             rows=R)
    p = os.path.join(C.HERE, "split_check_11.json"); json.dump(S, open(p, "w"), indent=1); open(p, "a").write("\n")
    print({k: v for k, v in S.items() if k != "rows"})

if __name__ == "__main__": main()
