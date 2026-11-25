"""Summarises the order-book samples (data/books/books.csv, not in the repo) into books_summary.json.
Cost is in bps against the mid price for buying or selling a given dollar amount at once. One side."""
import pandas as pd, numpy as np, json, sys, os
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "books", "books.csv")
d = pd.read_csv(src); err = d[d.mid == "ERR"]; d = d[d.mid != "ERR"].copy()
for c in d.columns[3:]: d[c] = pd.to_numeric(d[c], errors="coerce")
out = {"first_sample_utc": str(pd.to_datetime(d.ts.min(), unit="s")), "last_sample_utc": str(pd.to_datetime(d.ts.max(), unit="s")),
       "rounds": int(d.ts.nunique()), "error_rows": int(len(err)), "pairs": {}}
for (v, p), g in d.groupby(["venue", "pair"]):
    r = {"samples": int(len(g)), "mid_last": float(g.mid.iloc[-1])}
    r["spread_bps"] = {"median": float(g.spread_bps.median()), "p95": float(g.spread_bps.quantile(.95)), "max": float(g.spread_bps.max())}
    for k, a, b in (("100", "buy100", "sell100"), ("1k", "buy1k", "sell1k"), ("10k", "buy10k", "sell10k")):
        x = pd.concat([g[a], g[b]]); n_thin = int(x.isna().sum()); x = x.dropna()
        r[f"cost_{k}_bps"] = {"median": float(x.median()) if len(x) else None, "p95": float(x.quantile(.95)) if len(x) else None,
                              "max": float(x.max()) if len(x) else None, "book_too_thin": n_thin, "sides_sampled": int(len(x) + n_thin)}
    out["pairs"][f"{v}|{p}"] = r
json.dump(out, open("books_summary.json", "w"), indent=1)
print(out["rounds"], "rounds", len(out["pairs"]), "pairs", out["first_sample_utc"], out["last_sample_utc"])
