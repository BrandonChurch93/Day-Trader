"""Collects daily bars for draft plan 14 (plain momentum on large stocks).

Every feed ticker in the member list, plus SPY, SPMO and MTUM, plus any symbol in the off-repo check list
candidates.txt (old and new tickers looked at while rebuilding the member list), adjusted for splits and dividends
(Alpaca, adjustment=all, feed=sip), from replay_14_plan.start to replay_14_plan.end, in one collection so one adjustment
date applies. Reads no return and computes none. Prints counts only, never a price.

Raw bars go to ~/workspace/rig/data/replay_14/bars/<symbol>.csv (never committed). A name SYM@YYYY-MM-DD in the member
list is fetched with the feed's asof setting: the company that had ticker SYM on that day.

Usage, from research_rig/:  python3 fetch_14.py            (resumes; finished batches are not fetched again)
                            python3 fetch_14.py --summary  (counts and date spans from the stored files)
                            python3 fetch_14.py --identity (for the identity check: each member row's company as of
                                                            its first day, into bars_asof/)

The credential is used only through `pplx credentials run`; it is never read, printed or stored here."""
import sys, os, json, csv, time, subprocess, datetime as dt
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(os.path.expanduser("~"), "workspace", "rig", "data", "replay_14")
BARS = os.path.join(DATA, "bars")
MEMBERS = os.path.join(DATA, "members.csv")
CANDIDATES = os.path.join(DATA, "candidates.txt")
CRED = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
P = yaml.safe_load(open(os.path.join(REPO, "config", "thresholds.yaml")))["replay_14_plan"]["value"]
START, END = str(P["start"]), str(P["end"])
SCALE = ("SPY", "SPMO", "MTUM")
BATCH = 1   # one symbol per request: a 100-symbol request lost every bar of DOW in the first collection

def symbols():
    s = set(SCALE)
    if os.path.exists(MEMBERS): s |= {r["ticker_feed"] for r in csv.DictReader(open(MEMBERS, newline="")) if r["ticker_feed"]}
    if os.path.exists(CANDIDATES): s |= {l.strip() for l in open(CANDIDATES) if l.strip()}
    return sorted(s)

def get(url):
    for attempt in range(6):
        r = subprocess.run(["pplx", "credentials", "run", CRED, "--", "curl", "-s", "--max-time", "120", url], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            if "bars" in d: return d
            msg = str(d.get("message", ""))[:200]
        except Exception: msg = "unreadable reply"
        print("retry", attempt, msg, flush=True); time.sleep(5 * (attempt + 1))
    raise SystemExit("stopped: the feed failed 6 times")

def fetch_batch(syms):
    """A name SYM@YYYY-MM-DD asks the feed for the company that had ticker SYM on that day (Alpaca's asof setting);
    plain SYM means the company that has the ticker now. Stored under the full name."""
    out = {s: [] for s in syms}; token = None
    sym = [x.split("@")[0] for x in syms]; asof = {x.split("@")[1] for x in syms if "@" in x}
    if len(asof) > 1 or (asof and len(syms) > 1): raise SystemExit("one asof name per request")
    while True:
        url = (f"https://data.alpaca.markets/v2/stocks/bars?symbols={','.join(sym)}&timeframe=1Day&start={START}&end={END}"
               f"&adjustment=all&limit=10000&feed=sip" + (f"&asof={next(iter(asof))}" if asof else "") + (f"&page_token={token}" if token else ""))
        d = get(url)
        for s, bars in (d.get("bars") or {}).items(): out.setdefault(syms[0] if asof else s, []).extend(bars)
        token = d.get("next_page_token")
        if not token: return out
        time.sleep(0.35)

def main():
    os.makedirs(BARS, exist_ok=True); done_dir = os.path.join(DATA, "batches_done"); os.makedirs(done_dir, exist_ok=True)
    syms = symbols()
    meta_p = os.path.join(DATA, "collection.json")
    meta = json.load(open(meta_p)) if os.path.exists(meta_p) else dict(started_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                                                                       start=START, end=END, adjustment="all", feed="sip")
    done = {f[:-5] for f in os.listdir(done_dir)}
    todo = [s for s in syms if s not in done]
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    for n, b in enumerate(batches):
        got = fetch_batch(b)
        for s in b:
            bars = sorted(got.get(s, []), key=lambda x: x["t"])
            with open(os.path.join(BARS, s + ".csv"), "w", newline="") as f:
                w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close", "volume"])
                for x in bars: w.writerow([x["t"][:10], x["o"], x["h"], x["l"], x["c"], x["v"]])
        json.dump(dict(symbols=b, bars={s: len(got.get(s, [])) for s in b}), open(os.path.join(done_dir, f"{b[0]}.json"), "w"))
        if n % 50 == 0: print(f"{n + 1}/{len(batches)} symbols fetched", flush=True)
    meta["symbols"] = len(syms); meta["finished_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    json.dump(meta, open(meta_p, "w"), indent=1)
    summary()

ASOF = os.path.join(DATA, "bars_asof")

def asof_names():
    """For the identity check (common_14.asof_names): each member row's company as of its first day and as of the first
    day of its ranking look-back."""
    sys.path.insert(0, HERE); import common_14 as C
    return sorted({n for r in C.load_members(MEMBERS) if r["ticker_feed"] for n in C.asof_names(r)} | {n for v in C.EXTRA_ASOF.values() for n in v})

def identity():
    os.makedirs(ASOF, exist_ok=True)
    names = [x for x in asof_names() if not os.path.exists(os.path.join(ASOF, x + ".csv"))]
    for n, x in enumerate(names):
        got = fetch_batch([x])
        bars = sorted(got.get(x, []), key=lambda b: b["t"])
        with open(os.path.join(ASOF, x + ".csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close", "volume"])
            for b in bars: w.writerow([b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]])
        if n % 50 == 0: print(f"{n + 1}/{len(names)} asof names fetched", flush=True)
    print("asof files:", len(os.listdir(ASOF)))

def spans():
    """{symbol: (first date, last date, rows)} from the stored files; dates and counts only."""
    out = {}
    for f in sorted(os.listdir(BARS)):
        d = [r["date"] for r in csv.DictReader(open(os.path.join(BARS, f)))]
        out[f[:-4]] = (d[0], d[-1], len(d)) if d else (None, None, 0)
    return out

def summary():
    S = spans()
    json.dump({k: list(v) for k, v in S.items()}, open(os.path.join(DATA, "bar_spans.json"), "w"), indent=0)
    print(json.dumps(dict(files=len(S), with_bars=sum(v[2] > 0 for v in S.values()),
                          scale={s: S.get(s) for s in SCALE}), indent=1))

if __name__ == "__main__":
    if "--summary" in sys.argv[1:]: summary()
    elif "--identity" in sys.argv[1:]: identity()
    else: main()
