"""Shared pieces for draft plan 12 (following stock purchases disclosed by members of Congress): paths, config, events,
the trading calendar, prices, entry days and the calendar portfolio. Only score_12.py reads prices through it.

Raw files stay under ~/workspace/rig/ and are never committed. The four environment variables in ENV_OVERRIDES move them
for the tests; a real scoring run refuses while any is set.

Words used here:
  event      one member buying (or selling) one stock in filings of one day, whatever the number of rows
  entry      the open of a trading day chosen by the entry version (main, late5, cal30); exit is the close N trading days
             later counting the entry day as day 1
  position   one held stock in the portfolio: the events of one member in one stock whose holds overlap are one position
             (by member), or of all members in one stock (by stock)"""
import os, re, csv, json, hashlib, datetime as dt
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RIG = os.path.join(os.path.expanduser("~"), "workspace", "rig")
ENV_OVERRIDES = ("CONGRESS_12_TRADES", "CONGRESS_12_DETAILS", "CONGRESS_12_BARS", "RESULTS_12_DIR")
TRADES = os.environ.get("CONGRESS_12_TRADES", os.path.join(RIG, "congress", "trades.csv"))
DETAILS = os.environ.get("CONGRESS_12_DETAILS", os.path.join(RIG, "congress", "trades_source_details.csv"))
BARS = os.environ.get("CONGRESS_12_BARS", os.path.join(RIG, "data", "congress_12", "bars"))
OUTDIR = os.environ.get("RESULTS_12_DIR", HERE)
VARIANTS = ("main", "late5", "cal30")

_TH = yaml.safe_load(open(os.path.join(REPO, "config", "thresholds.yaml")))
def th(key): return _TH[key]["value"]
P = th("replay_12_plan")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def symbol_for(ticker):
    return ticker.strip().upper().replace("-", ".")

RENAMES_FILE = os.path.join(HERE, "renames_12.csv")

def load_renames(path=RENAMES_FILE):
    """The frozen rename list. Returns (maps, dated).
    maps: old ticker to new ticker for lines marked mapped (the same company under a new ticker). The feed keeps the
    whole history under the new ticker, so these apply on every date.
    dated: old ticker to its dated lines [(effective_date, target)], sorted. A line marked mapped_before sends rows filed
    before effective_date to target; left_out_before leaves them out (target None, counted as no price). The first line
    whose date is after the filing day applies; on or after the last date the ticker is its own. The filing day decides,
    never transaction_date. Lines marked left_out are records only."""
    maps, dated = {}, {}
    for r in csv.DictReader(open(path, newline="")):
        o, n, st = symbol_for(r["old_ticker"]), symbol_for(r["new_ticker"]), r["status"]
        if st == "mapped":
            if not o or not n or o in maps or o in dated: raise SystemExit(f"refused: bad or repeated line for {o!r} in {os.path.basename(path)}")
            maps[o] = n
        elif st in ("mapped_before", "left_out_before"):
            d = r["effective_date"]
            if not o or o in maps or (st == "mapped_before") != bool(n) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) or d in [x for x, _ in dated.get(o, [])]:
                raise SystemExit(f"refused: bad dated line for {o!r} in {os.path.basename(path)}")
            dated.setdefault(o, []).append((d, n if st == "mapped_before" else None))
    return maps, {k: sorted(v) for k, v in dated.items()}

def priced_symbol(own, filed, renames=None):
    """(priced ticker, rename line or None) for a row's own ticker filed on filed. A left-out dated line gives a ticker
    with no price file, so the event is counted as no price."""
    maps, dated = RENAMES_ALL if renames is None else renames
    for d, t in dated.get(own, ()):
        if filed < d: return (t if t else own + "~LEFT_OUT"), f"{own}<{d}"
    if own in maps: return maps[own], own
    return own, None

RENAMES_ALL = load_renames(); RENAMES = RENAMES_ALL[0]

# A call option, or the exercise of one, named in a row's two text fields. Used only for side lines and the named table,
# never to decide what the judged groups hold.
CALL_WORDS = re.compile(r"(?i)\b(calls?|exercis\w*)\b")
CALL_ONLY = re.compile(r"(?i)\bcalls?\b"); PUT_WORDS = re.compile(r"(?i)\bputs?\b")

def load_rows():
    """trades.csv rows, each with the two text fields from trades_source_details.csv (the same rows in the same order;
    refused if any of the shared columns differ)."""
    T = list(csv.DictReader(open(TRADES, newline="")))
    D = list(csv.DictReader(open(DETAILS, newline="")))
    if len(T) != len(D): raise SystemExit(f"refused: trades.csv has {len(T)} rows and the details file {len(D)}")
    for i, (a, b) in enumerate(zip(T, D)):
        if any(a[k] != b[k] for k in a): raise SystemExit(f"refused: row {i + 2} of the details file is not row {i + 2} of trades.csv")
        a["text"] = (b.get("asset_description") or "") + " " + (b.get("description_note") or "")
    return T

def low(r):
    try: return float(r["amount_range_low"])
    except ValueError: return 0.0

def events(rows, side, asset="stock", renames=None):
    """One event per (member, priced ticker, filed day) for the side. The priced ticker is the record's ticker, or the one
    the rename list gives for it on the filing day (priced_symbol); ticker keeps the record's own, and renamed and
    rename_line say which line moved it. large: any row's range starts at
    large_buy_min_usd or more. call_rows: any row's text names a call or an exercise (side lines only)."""
    E = {}
    for r in rows:
        if r["side"] != side or r["asset_type"] != asset or not r["ticker"].strip(): continue
        own = symbol_for(r["ticker"]); sym, line = priced_symbol(own, r["filed_date"], renames); k = (r["member"], sym, r["filed_date"])
        e = E.setdefault(k, dict(eid=hashlib.sha256("|".join((side, asset) + k).encode()).hexdigest()[:12], member=k[0], sym=k[1],
                                 ticker=r["ticker"], filed=k[2], side=side, asset=asset, large=False, call_rows=False, rows=0,
                                 renamed=False, rename_line=None))
        e["rows"] += 1; e["renamed"] |= line is not None; e["rename_line"] = e["rename_line"] or line; e["large"] |= low(r) >= P["large_buy_min_usd"]; e["call_rows"] |= bool(CALL_WORDS.search(r["text"]))
    return sorted(E.values(), key=lambda e: (e["filed"], e["member"], e["sym"]))

def call_buy_events(rows):
    """Option purchases whose text says call and not put, as events on the underlying stock (named table only)."""
    keep = [r for r in rows if r["side"] == "buy" and r["asset_type"] == "option" and CALL_ONLY.search(r["text"]) and not PUT_WORDS.search(r["text"])]
    return events(keep, "buy", "option")

def calendar():
    """The trading days: the dates of the SPY file."""
    return [r["date"] for r in csv.DictReader(open(os.path.join(BARS, "SPY.csv"), newline=""))]

def ordinal(day): return dt.date.fromisoformat(day).toordinal()

class Prices:
    """Opens and closes of the given symbols on the SPY calendar, cut at the first n days (the design run never loads a
    later day). CF is the close carried over a missing day; LV[s, i] is the last day at or before i with a close."""
    def __init__(self, days, syms, n=None):
        self.days = list(days[:n] if n else days); self.n = len(self.days); idx = {d: i for i, d in enumerate(self.days)}
        self.ord = np.array([ordinal(d) for d in self.days])
        self.syms = sorted(set(syms)); self.si = {}; self.read = []
        O, Cl = [], []
        for s in self.syms:
            p = os.path.join(BARS, s + ".csv")
            if not os.path.exists(p): continue
            self.read.append(p)
            o = np.full(self.n, np.nan); c = np.full(self.n, np.nan)
            for r in csv.DictReader(open(p, newline="")):
                i = idx.get(r["date"])
                if i is not None: o[i] = float(r["open"]); c[i] = float(r["close"])
            if np.isnan(c).all(): continue
            self.si[s] = len(O); O.append(o); Cl.append(c)
        self.O = np.array(O).reshape(len(O), self.n); self.C = np.array(Cl).reshape(len(O), self.n)
        self._derive()
    def _derive(self):
        """LV, CF and FB: FB[s] is the first day index with a close (px.n if none)."""
        ok = ~np.isnan(self.C); i = np.where(ok, np.arange(self.n), -1); self.LV = np.maximum.accumulate(i, axis=1)
        self.CF = np.where(self.LV >= 0, np.take_along_axis(np.nan_to_num(self.C), np.maximum(self.LV, 0), axis=1), np.nan)
        self.FB = np.where(ok.any(axis=1), ok.argmax(axis=1), self.n) if ok.size else np.zeros(len(ok), int)
    def digest(self):
        h = hashlib.sha256()
        for p in sorted(set(self.read), key=os.path.basename): h.update(os.path.basename(p).encode() + b"\0" + open(p, "rb").read() + b"\0")
        return dict(files=len(set(self.read)), sha256=h.hexdigest(), last_day_loaded=self.days[-1])

    @classmethod
    def from_arrays(cls, days, data):
        """For the tests: data is {symbol: (opens, closes)} on days, NaN where there is no bar."""
        self = cls.__new__(cls); self.days = list(days); self.n = len(days); self.ord = np.array([ordinal(d) for d in days])
        self.syms = sorted(data); self.si = {s: i for i, s in enumerate(self.syms)}; self.read = []
        self.O = np.array([data[s][0] for s in self.syms], float); self.C = np.array([data[s][1] for s in self.syms], float)
        self._derive(); return self

class Ev:
    """Events as arrays, aligned with the list E."""
    def __init__(self, E, px):
        self.E = E; self.members = sorted({e["member"] for e in E}); mi = {m: i for i, m in enumerate(self.members)}
        self.member = np.array([mi[e["member"]] for e in E], int)
        self.sym = np.array([px.si.get(e["sym"], -1) for e in E], int)
        self.filed = np.array([ordinal(e["filed"]) for e in E], int)
        self.large = np.array([e["large"] for e in E], bool); self.call_rows = np.array([e["call_rows"] for e in E], bool)
        self.year = np.array([int(e["filed"][:4]) for e in E], int)
    def __len__(self): return len(self.E)

def entries(px, filed_ord, variant):
    """Entry day index per event: the first trading day after the filing day (main), that plus late_entry_trading_days
    (late5), or the first trading day after the filing day plus late_entry_calendar_days (cal30). px.n means none."""
    a = np.searchsorted(px.ord, filed_ord, side="right")
    if variant == "late5": a = a + P["late_entry_trading_days"]
    elif variant == "cal30": a = np.searchsorted(px.ord, filed_ord + P["late_entry_calendar_days"], side="right")
    elif variant != "main": raise ValueError(variant)
    return np.minimum(a, px.n)

NOPRICE, UNFINISHED, TRADED = 1, 2, 0

def trades(px, ev, n, variant, filed_ord=None):
    """Per event at hold n: status (TRADED, NOPRICE, UNFINISHED: prices end first), entry a, exit b and stopped (bars end
    inside the hold: sold at the last close). NOPRICE: no file, no bar on the entry day, the stock's first bar after the
    filing day (plan: "whose prices start after its filing day"), or a filing day before the first day of the calendar
    (its true entry day may fall before the first loaded day; this happens only to shifted days of yardstick (c))."""
    f = ev.filed if filed_ord is None else filed_ord
    a = entries(px, f, variant); b = a + n - 1
    st = np.full(len(f), TRADED); st[b >= px.n] = UNFINISHED
    s = ev.sym; live = st == TRADED
    bad = live & (s < 0); st[bad] = NOPRICE; live &= ~bad
    bad = live & (f < px.ord[0]); st[bad] = NOPRICE; live &= ~bad
    k = np.where(live)[0]
    late = px.ord[np.minimum(px.FB[s[k]], px.n - 1)] > f[k]; st[k[late]] = NOPRICE; k = k[~late]
    nob = np.isnan(px.O[s[k], a[k]]) | np.isnan(px.C[s[k], a[k]]); st[k[nob]] = NOPRICE; k = k[~nob]
    last = b.copy(); last[k] = px.LV[s[k], b[k]]
    stopped = np.zeros(len(f), bool); stopped[k] = last[k] < b[k]
    return dict(status=st, a=a, b=np.where(st == TRADED, last, b), stopped=stopped)

def merge(member, sym, a, b, by):
    """One position per member and stock (by 'member') or per stock (by 'stock') while holds overlap.
    Returns arrays (member, sym, a, b) of positions."""
    if len(a) == 0: return (np.array([], int),) * 4
    key = member.astype(np.int64) * (int(sym.max()) + 1) + sym if by == "member" else sym
    o = np.lexsort((a, key)); key, member, sym, a, b = key[o], member[o], sym[o], a[o], b[o]
    _, kk = np.unique(key, return_inverse=True); big = 10 ** 6
    run = np.maximum.accumulate(b + kk * big)                      # running last exit within each key
    new = np.r_[True, (kk[1:] != kk[:-1]) | (a[1:] + kk[1:] * big > run[:-1])]
    g = np.cumsum(new) - 1
    pa = a[new]; pb = np.zeros(g[-1] + 1, int); np.maximum.at(pb, g, b)
    return member[new], sym[new], pa, pb

def portfolio(px, member, sym, a, b, by, cost, bench=("SPY", "QQQ", "NANC")):
    """The calendar portfolio of positions (already merged). Each day every member with a position gets an equal share,
    split equally among that member's positions (by 'member'), or every position an equal share (by 'stock'). Weights are
    reset each day and cost is charged on turnover, the sum of |target weight - drifted weight| with entries and exits.
    no_reset_net: the same days and weights with cost charged on entries and exits only (not judged). Days with no
    position are left out. Each benchmark's mirror holds the same weights with each stock swapped for the benchmark."""
    if len(a) == 0: return None
    L = b - a + 1; P_ = np.repeat(np.arange(len(a)), L); start = np.repeat(np.cumsum(L) - L, L)
    T = np.repeat(a, L) + (np.arange(L.sum()) - start); S = sym[P_]; M = member[P_]; FIRST = T == a[P_]
    nd = px.n
    def rets(si):
        r = np.empty(len(T)); f = FIRST
        r[f] = px.CF[si[f], T[f]] / px.O[si[f], T[f]] - 1
        r[~f] = px.CF[si[~f], T[~f]] / px.CF[si[~f], T[~f] - 1] - 1
        return r
    R = rets(S)
    if by == "member":
        nm = int(M.max()) + 1; key = T.astype(np.int64) * nm + M
        uk, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
        n_members = np.bincount(uk // nm, minlength=nd)
        w = 1.0 / (n_members[T] * cnt[inv])
    else:
        w = 1.0 / np.bincount(T, minlength=nd)[T]
    rp = np.bincount(T, weights=w * R, minlength=nd)
    drift = np.zeros(len(T)); k = np.where(~FIRST)[0]              # pairs are in position order, days in order
    drift[k] = w[k - 1] * (1 + R[k - 1]) / (1 + rp[T[k - 1]])
    last = np.r_[P_[1:] != P_[:-1], True]
    sells = np.bincount(T[last], weights=w[last] * (1 + R[last]) / (1 + rp[T[last]]), minlength=nd)
    turn = np.bincount(T, weights=np.abs(w - drift), minlength=nd) + sells
    entr = np.bincount(T[FIRST], weights=w[FIRST], minlength=nd) + sells
    held = np.bincount(T, minlength=nd) > 0; c = cost / 1e4
    out = dict(days=np.where(held)[0], gross=rp[held], net=(rp - c * turn)[held], no_reset_net=(rp - c * entr)[held],
               turnover=float(turn[held].sum()), positions=len(a), bench={})
    for s in bench:
        if s not in px.si: continue
        bi = np.full(len(T), px.si[s]); rb = rets(bi); ok = ~np.isnan(rb)
        out["bench"][s] = dict(r=np.bincount(T, weights=w * np.nan_to_num(rb), minlength=nd)[held],
                               ok=(np.bincount(T, weights=(~ok).astype(float), minlength=nd) == 0)[held])
    return out

def growth(r): return float(np.prod(1 + r))

def per_year(g, n): return (g ** (252 / n) - 1) if n else None

def block_months(hold_days):
    """Bootstrap block length in months: the hold in trading days over bootstrap_days_per_month, rounded up."""
    return -(-int(hold_days) // int(P["bootstrap_days_per_month"]))

def bootstrap_p5(diff, draws, seed, block=1):
    """5th percentile of the mean monthly difference. Circular block bootstrap: each draw strings together blocks of
    `block` consecutive months, each block starting at a random month and wrapping from the last month to the first,
    until it is as long as the series, then cuts it to that length."""
    M = len(diff)
    if M < 2: return None
    L = max(1, int(block)); k = -(-M // L)
    rng = np.random.default_rng(seed); start = rng.integers(0, M, size=(draws, k))
    pick = ((start[:, :, None] + np.arange(L)[None, None, :]) % M).reshape(draws, k * L)[:, :M]
    return float(np.percentile(diff[pick].mean(axis=1), 5))

def summarize(px, pf, bench="SPY"):
    """Growth of the portfolio after cost and of its mirror on the portfolio's days, the per-year excess, the monthly
    differences and each year apart."""
    if pf is None: return dict(days=0, growth=None, spy_growth=None, ends_above_spy=False, per_year_excess=None, months=0, monthly_diff=np.array([]), years={})
    r, m = pf["net"], pf["bench"][bench]["r"]; n = len(pf["days"])
    g, gm = growth(r), growth(m)
    mo = np.array([px.days[i][:7] for i in pf["days"]]); um = sorted(set(mo))
    diff = np.array([growth(r[mo == x]) - growth(m[mo == x]) for x in um])
    yr = np.array([x[:4] for x in mo])
    years = {y: dict(days=int((yr == y).sum()), growth=growth(r[yr == y]), spy_growth=growth(m[yr == y])) for y in sorted(set(yr))}
    return dict(days=n, first_day=px.days[pf["days"][0]], last_day=px.days[pf["days"][-1]], positions=pf["positions"], growth=g, spy_growth=gm,
                ends_above_spy=g > gm, per_year_excess=per_year(g / gm, n), gross_growth=growth(pf["gross"]),
                no_reset_growth_not_judged=growth(pf["no_reset_net"]), turnover=pf["turnover"], months=len(um), monthly_diff=diff, years=years)

def scale(pf, s):
    """Growth against another fund on the held days where it has a bar (QQQ; NANC from 2023-02-07). Shown for scale."""
    if pf is None or s not in pf["bench"]: return None
    b = pf["bench"][s]; k = b["ok"]
    if not k.any(): return None
    g, gb = growth(pf["net"][k]), growth(b["r"][k])
    return dict(days=int(k.sum()), growth=g, fund_growth=gb, per_year_excess=per_year(g / gb, int(k.sum())))
