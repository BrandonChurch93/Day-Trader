"""Collects daily bars for draft plan 12 (following stock purchases disclosed by members of Congress).

Every ticker in the buy and sell rows of trades.csv (stocks and options, both chambers), plus SPY, QQQ and NANC, from
2018-12-01 to 2026-11-24, adjusted for splits and dividends (Alpaca, adjustment=all, feed=sip), in one collection so one
adjustment date applies. Reads no return and computes none.

Raw bars go to ~/workspace/rig/data/congress_12/bars/<symbol>.csv (never committed). Writes research_rig/prices_12_summary.json
with counts and dates only.

Usage, from research_rig/:  python3 fetch_12_prices.py            (resumes; finished batches are not fetched again)
                            python3 fetch_12_prices.py --summary  (rewrites the summary from the stored files)

The trades file is read only: ~/workspace/rig/congress/trades.csv, built by another helper. Its ticker is mapped to the
feed's symbol by symbol_for(): a share class written with "-" (BRK-B) is written with "." (BRK.B)."""
import sys, os, json, csv, time, subprocess, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.expanduser("~"), "workspace", "rig", "data", "congress_12")
BARS = os.path.join(DATA, "bars")
TRADES = os.path.join(os.path.expanduser("~"), "workspace", "rig", "congress", "trades.csv")
CRED = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
START, END = "2018-12-01", "2026-11-24"
SCALE = ("SPY", "QQQ", "NANC")
BATCH = 100
SUMMARY = os.path.join(HERE, "prices_12_summary.json")

def symbol_for(ticker):
    return ticker.strip().upper().replace("-", ".")

def tickers():
    rows = csv.DictReader(open(TRADES, newline=""))
    return sorted({r["ticker"] for r in rows if r["side"] in ("buy", "sell") and r["ticker"].strip()})

def get(url):
    for attempt in range(6):
        r = subprocess.run(["pplx", "credentials", "run", CRED, "--", "curl", "-s", "--max-time", "120", url], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            if "bars" in d: return d
            msg = d.get("message", r.stdout[:200])
        except Exception: msg = r.stdout[:200] + r.stderr[:200]
        print("retry", attempt, msg, flush=True); time.sleep(5 * (attempt + 1))
    raise SystemExit(f"stopped: the feed failed 6 times on {url[:120]}")

def fetch_batch(syms):
    out = {s: [] for s in syms}; token = None
    while True:
        url = (f"https://data.alpaca.markets/v2/stocks/bars?symbols={','.join(syms)}&timeframe=1Day&start={START}&end={END}"
               f"&adjustment=all&limit=10000&feed=sip" + (f"&page_token={token}" if token else ""))
        d = get(url)
        for s, bars in (d.get("bars") or {}).items(): out.setdefault(s, []).extend(bars)
        token = d.get("next_page_token")
        if not token: return out
        time.sleep(0.35)

def main():
    os.makedirs(BARS, exist_ok=True); done_dir = os.path.join(DATA, "batches_done"); os.makedirs(done_dir, exist_ok=True)
    T = tickers(); syms = sorted({symbol_for(t) for t in T} | set(SCALE))
    meta_p = os.path.join(DATA, "collection.json")
    meta = json.load(open(meta_p)) if os.path.exists(meta_p) else dict(started_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                                                                       start=START, end=END, adjustment="all", feed="sip", symbols=len(syms))
    json.dump(meta, open(meta_p, "w"), indent=1)
    batches = [syms[i:i + BATCH] for i in range(0, len(syms), BATCH)]
    for n, b in enumerate(batches):
        mark = os.path.join(done_dir, f"{n:03d}.json")
        if os.path.exists(mark) and json.load(open(mark))["symbols"] == b: continue
        got = fetch_batch(b)
        for s in b:
            bars = sorted(got.get(s, []), key=lambda x: x["t"])
            with open(os.path.join(BARS, s + ".csv"), "w", newline="") as f:
                w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close", "volume"])
                for x in bars: w.writerow([x["t"][:10], x["o"], x["h"], x["l"], x["c"], x["v"]])
        json.dump(dict(symbols=b, bars={s: len(got.get(s, [])) for s in b}), open(mark, "w"))
        print(f"batch {n + 1}/{len(batches)}: {sum(bool(got.get(s)) for s in b)} of {len(b)} with bars", flush=True)
    meta["finished_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"); json.dump(meta, open(meta_p, "w"), indent=1)
    summary()

def summary():
    """Counts and dates only. Which symbols have bars, and over which span; no price is printed."""
    meta = json.load(open(os.path.join(DATA, "collection.json")))
    T = tickers(); have, first, last, rows = {}, [], [], 0
    for t in T:
        p = os.path.join(BARS, symbol_for(t) + ".csv")
        d = [r["date"] for r in csv.DictReader(open(p))] if os.path.exists(p) else []
        have[t] = bool(d); rows += len(d)
        if d: first.append(d[0]); last.append(d[-1])
    missing = sorted(t for t in T if not have[t])
    json.dump(dict(tickers=len(T), missing=missing), open(os.path.join(DATA, "missing_tickers.json"), "w"), indent=1)
    scale = {}
    for s in SCALE:
        d = [r["date"] for r in csv.DictReader(open(os.path.join(BARS, s + ".csv")))]
        scale[s] = dict(bars=len(d), first=d[0], last=d[-1])
    S = dict(made_by="research_rig/fetch_12_prices.py", collection=meta, tickers_in_buy_and_sell_rows=len(T),
             tickers_with_bars=len(T) - len(missing), tickers_without_bars=len(missing), bar_rows=rows,
             tickers_whose_bars_start_after_2019_01_02=sum(f > "2019-01-02" for f in first),
             tickers_whose_bars_end_before_2026_11_24=sum(l < END for l in last), scale_funds=scale,
             note="Counts and dates only. The list of tickers without bars is in ~/workspace/rig/data/congress_12/missing_tickers.json.")
    json.dump(S, open(SUMMARY, "w"), indent=1); open(SUMMARY, "a").write("\n")
    print(json.dumps({k: v for k, v in S.items() if k != "collection"}, indent=1))

if __name__ == "__main__":
    summary() if "--summary" in sys.argv[1:] else main()
