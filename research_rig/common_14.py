"""Shared pieces for plan 14 (plain momentum on large stocks): paths, settings, the member list, the trading calendar,
prices, ranking, baskets and the monthly portfolio. Every setting comes from replay_14_plan in config/thresholds.yaml.

Raw files stay under ~/workspace/rig/data/replay_14/ and are never committed. The environment variables in
ENV_OVERRIDES move them for the tests; a real run refuses while any is set.

Words used here:
  line        one row of members.csv: a stock in the index from date_from up to, not including, date_to, under the
              ticker it had then (ticker_then), priced from the file ticker_feed between feed_from and feed_to
  series      the prices one line reads: (ticker_feed, feed_from, feed_to). Renamed lines of one company share a series.
  month-end   the last SPY trading day of a calendar month (the final month counts only if it is complete)
  ranking day a month-end with lookback_months month-ends before it; the purchase is at the next trading day's open
  period      from one purchase open to the next purchase open; the last runs to the close of the last day"""
import os, csv, json, hashlib, datetime as dt
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RIG = os.path.join(os.path.expanduser("~"), "workspace", "rig")
DATA_DEFAULT = os.path.join(RIG, "data", "replay_14")
ENV_OVERRIDES = ("REPLAY_14_MEMBERS", "REPLAY_14_BARS", "RESULTS_14_DIR", "REPLAY_14_LOCK_DIR")
MEMBERS = os.environ.get("REPLAY_14_MEMBERS", os.path.join(DATA_DEFAULT, "members.csv"))
BARS = os.environ.get("REPLAY_14_BARS", os.path.join(DATA_DEFAULT, "bars"))
OUTDIR = os.environ.get("RESULTS_14_DIR", HERE)
OFF_REPO_LOCK_DIR = os.environ.get("REPLAY_14_LOCK_DIR", DATA_DEFAULT)
SCALE = ("SPY", "SPMO", "MTUM")

_TH = yaml.safe_load(open(os.path.join(REPO, "config", "thresholds.yaml")))
P = _TH["replay_14_plan"]["value"]
PLAN_SOURCE = _TH["replay_14_plan"]["source"]

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def sha256_json(x): return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()

# ------------------------------------------------------------------------------------------------ members, calendar
def load_members(path=None):
    with open(path or MEMBERS, newline="") as fh: rows = list(csv.DictReader(fh))
    for r in rows:
        r["series"] = f"{r['ticker_feed']}|{r['feed_from']}|{r['feed_to']}" if r["ticker_feed"] else ""
    return rows

def calendar(bars=None, start=None, end=None):
    """Trading days: the dates of the SPY file between the plan's start and end."""
    start, end = str(start or P["start"]), str(end or P["end"])
    with open(os.path.join(bars or BARS, "SPY.csv"), newline="") as fh: d = [r["date"] for r in csv.DictReader(fh)]
    return [x for x in d if start <= x <= end]

def month_end_index(days):
    """Indexes of month-ends in days. The month of the last day counts only if no weekday of that month is left after it."""
    out = [i for i in range(len(days) - 1) if days[i + 1][:7] != days[i][:7]]
    last = dt.date.fromisoformat(days[-1]); d = last + dt.timedelta(days=1); complete = True
    while d.month == last.month:
        if d.weekday() < 5: complete = False; break
        d += dt.timedelta(days=1)
    if complete: out.append(len(days) - 1)
    return out

def ranking_index(days):
    """(ranking day index, its position in the month-end list) for every month-end with lookback_months month-ends
    before it and a next trading day for the purchase."""
    me = month_end_index(days); L = P["lookback_months"]
    return [(me[k], k) for k in range(L, len(me)) if me[k] + 1 < len(days)], me

# ------------------------------------------------------------------------------------------------------------ prices
class Prices:
    """Opens and closes of each series on the calendar, NaN where there is no bar or outside feed_from..feed_to.
    last[s] is the last day index with a close."""
    def __init__(self, days, members, bars=None, extra=SCALE):
        self.days = list(days); self.n = len(days); idx = {d: i for i, d in enumerate(self.days)}
        keys = sorted({r["series"] for r in members if r["series"]} | {f"{s}||" for s in extra})
        self.keys = []; self.si = {}; O, Cl = [], []; self.read = set()
        for k in keys:
            feed, ff, ft = k.split("|"); p = os.path.join(bars or BARS, feed + ".csv")
            o = np.full(self.n, np.nan); c = np.full(self.n, np.nan)
            if os.path.exists(p):
                self.read.add(p)
                with open(p, newline="") as fh:
                    for r in csv.DictReader(fh):
                        d = r["date"]; i = idx.get(d)
                        if i is None or (ff and d < ff) or (ft and d > ft): continue
                        o[i] = float(r["open"]); c[i] = float(r["close"])
            self.si[k] = len(O); self.keys.append(k); O.append(o); Cl.append(c)
        self._finish(np.array(O).reshape(len(O), self.n), np.array(Cl).reshape(len(O), self.n))

    def _finish(self, O, C):
        self.O, self.C = O, C
        ok = ~np.isnan(C); ar = np.where(ok, np.arange(self.n), -1)
        self.LV = np.maximum.accumulate(ar, axis=1)                  # last day <= i with a close
        self.last = self.LV[:, -1] if self.n else np.array([], int)
        self.CF = np.where(self.LV >= 0, np.take_along_axis(np.nan_to_num(C), np.maximum(self.LV, 0), axis=1), np.nan)

    @classmethod
    def from_arrays(cls, days, data):
        """For the tests: data is {series key: (opens, closes)} on days, NaN where there is no bar."""
        self = cls.__new__(cls); self.days = list(days); self.n = len(days); self.read = set()
        self.keys = sorted(data); self.si = {k: i for i, k in enumerate(self.keys)}
        self._finish(np.array([data[k][0] for k in self.keys], float).reshape(len(data), self.n),
                     np.array([data[k][1] for k in self.keys], float).reshape(len(data), self.n))
        return self

    def digest(self):
        h = hashlib.sha256()
        for p in sorted(self.read, key=os.path.basename):
            with open(p, "rb") as fh: h.update(os.path.basename(p).encode() + b"\0" + fh.read() + b"\0")
        return dict(files=len(self.read), sha256=h.hexdigest(), first_day=self.days[0], last_day=self.days[-1])

# ----------------------------------------------------------------------------------------------- who is in, ranking
def members_on(members, day):
    return [r for r in members if r["date_from"] <= day < r["date_to"]]

def one_class(rows):
    """Two share classes of one company: only the first by ticker_then in alphabetical order stays."""
    best = {}
    for r in rows:
        k = r["company_id"]
        if k not in best or r["ticker_then"] < best[k]["ticker_then"]: best[k] = r
    return sorted(best.values(), key=lambda r: r["ticker_then"])

def universe(members, px, day):
    """Lines in the index on the day, one share class per company, with a series. Sorted by ticker_then."""
    return [r for r in one_class(members_on(members, day)) if r["series"]]

def rankable(members, px, days, me, k):
    """[(gain, ticker_then, series index)] for the ranking day me[k]: close at month-end k-skip over close at month-end
    k-lookback, minus one, both closes on those exact days. Also returns the tickers that could not be ranked."""
    i = me[k]; a = me[k - P["skip_months"]]; b = me[k - P["lookback_months"]]
    out, unr = [], []
    for r in universe(members, px, days[i]):
        s = px.si.get(r["series"])
        if s is None: unr.append(r["ticker_then"]); continue
        ca, cb = px.C[s, a], px.C[s, b]
        if np.isnan(ca) or np.isnan(cb) or cb <= 0: unr.append(r["ticker_then"]); continue
        out.append((ca / cb - 1.0, r["ticker_then"], s))
    return out, unr

def top_n(ranked, px, fill, n):
    """The top n by gain (ties by ticker), skipping any with no open on the purchase day for the next one down."""
    picks = []
    for g, t, s in sorted(ranked, key=lambda x: (-x[0], x[1])):
        if len(picks) == n: break
        if not np.isnan(px.O[s, fill]): picks.append(s)
    return picks

def everyone(members, px, days, i, fill):
    """Yardstick (b): every line in the index on the ranking day with a close that day and an open on the purchase day."""
    out = []
    for r in universe(members, px, days[i]):
        s = px.si.get(r["series"])
        if s is not None and not np.isnan(px.C[s, i]) and not np.isnan(px.O[s, fill]): out.append(s)
    return out

def random_baskets(periods, px, n, draws, rng):
    """Yardstick (c): an array (draws, periods, n) of series indexes, -1 where a basket is short. For each ranking day
    in order, the stocks the rule could rank are sorted by ticker; each path gets one uniform number per stock and takes
    the n stocks with the smallest numbers that have an open on the purchase day (a fresh draw each month in each path)."""
    out = np.full((draws, len(periods), n), -1, int)
    for k, p in enumerate(periods):
        pool = np.array([s for _, t, s in sorted(p["ranked"], key=lambda x: x[1])], int)
        if len(pool) == 0: continue
        ok = ~np.isnan(px.O[pool, p["fill"]])
        order = np.argsort(rng.random((draws, len(pool))), axis=1)
        good = ok[order]; rank = np.cumsum(good, axis=1)
        take = good & (rank <= n)
        rows, cols = np.nonzero(take)
        slot = rank[rows, cols] - 1
        out[rows, k, slot] = pool[order[rows, cols]]
    return out

# ------------------------------------------------------------------------------------------------------- portfolio
def simulate(px, fills, baskets, cost_bps, daily=False):
    """One account through the periods. fills[k] is the purchase day index of period k, baskets[k] the series indexes
    bought in equal parts at that open. Period k runs to the next fill's open; the last runs to the close of the last
    day and is then sold. Inside a period parts drift with prices. A held stock with no bar on or after the next
    re-form day (or after the last day, for the last period) is sold at its last close, flagged, and the money sits in
    cash. A held stock with no open at the re-form is valued at its last close (a gap with prices later).
    Cost: cost_bps per side on the sum of |new part - drifted part| at each re-form; the first purchase counts as all
    traded; a stop sale and the final sale are charged on what is sold.

    Returns dict: value (final, start 1), at_fill (value at each fill open before that re-form's cost), turnover (per
    re-form), flags (list of (period, series index, last close day)), daily (close values) if daily."""
    c = cost_bps / 1e4; n = px.n; K = len(fills)
    V = 1.0; held = {}                     # series -> value now
    at_fill, turn, flags = [], [], []
    dv = np.full(n, np.nan) if daily else None
    cash = 1.0                             # the account starts as cash worth 1
    for k in range(K):
        f = fills[k]; end = fills[k + 1] if k + 1 < K else n      # period days f .. end-1
        V_open = cash + sum(held.values())
        at_fill.append(V_open)
        drift = {s: v / V_open for s, v in held.items()} if V_open > 0 else {}
        b = list(dict.fromkeys(baskets[k])); w = 1.0 / len(b) if b else 0.0
        target = {s: w for s in b}
        T = sum(abs(target.get(s, 0.0) - drift.get(s, 0.0)) for s in set(target) | set(drift))
        if k == 0: T = 1.0 if b else 0.0
        turn.append(T)
        V = V_open * (1 - c * T)
        cash = 0.0 if b else V
        # buy at the open; positions in "units of value at the open"
        pos = {s: V * w for s in b}
        base = {s: px.O[s, f] for s in b}
        need = end if k + 1 < K else n - 1      # a bar on or after this day means the prices go on
        stopped = {s: int(px.last[s]) for s in b if px.last[s] < need}
        if daily:
            for t in range(f, end):
                tot = 0.0
                for s in b:
                    if s in stopped and t > stopped[s]: tot += pos[s] * px.C[s, stopped[s]] / base[s] * (1 - c)
                    else: tot += pos[s] * px.CF[s, t] / base[s]
                dv[t] = tot + cash
        # carry to the next open (or the last close)
        newheld = {}; add_cash = 0.0
        for s in b:
            if s in stopped:
                v = pos[s] * px.C[s, stopped[s]] / base[s]
                add_cash += v * (1 - c); flags.append((k, s, stopped[s]))
            elif k + 1 < K:
                nf = fills[k + 1]; p = px.O[s, nf]
                if np.isnan(p): p = px.CF[s, nf - 1]
                newheld[s] = pos[s] * p / base[s]
            else:
                newheld[s] = pos[s] * px.CF[s, n - 1] / base[s]
        cash += add_cash; held = newheld
    final_sale = sum(held.values())
    V_end = cash + final_sale * (1 - c)
    if daily: dv[n - 1] = V_end
    return dict(value=V_end, at_fill=at_fill, turnover=turn, flags=flags, daily=dv)

def hold_one(px, s, f0, cost_bps):
    """One fund (SPY, SPMO, MTUM) bought at the open of day f0 and sold at the last close, one buy and one sell charged.
    Returns (final value, value at each later open as a function, daily closes)."""
    c = cost_bps / 1e4
    units = (1 - c) / px.O[s, f0]
    daily = units * px.CF[s]; daily[:f0] = np.nan
    final = units * px.CF[s, -1] * (1 - c)
    return final, units, daily

def max_drop(x):
    x = x[~np.isnan(x)]
    if len(x) == 0: return float("nan")
    peak = np.maximum.accumulate(x); return float((x / peak - 1).min())

def period_moves(px, fills):
    """For each period k and series s: mult[k, s] = exit value / purchase open, and stopped[k, s]. Exit is the next
    re-form open (the last close carried over if there is no open then), or the last close of the last day; for a
    series with no bar on or after that day it is the series' last close (a stop)."""
    K = len(fills); n = px.n
    mult = np.full((K, len(px.keys)), np.nan); stopped = np.zeros((K, len(px.keys)), bool)
    for k in range(K):
        f = fills[k]; end = fills[k + 1] if k + 1 < K else n
        need = end if k + 1 < K else n - 1
        st = px.last < need
        if k + 1 < K: ex = np.where(np.isnan(px.O[:, end]), px.CF[:, end - 1], px.O[:, end])
        else: ex = px.CF[:, n - 1]
        lastc = px.C[np.arange(len(px.keys)), np.maximum(px.last, 0)]
        ex = np.where(st, lastc, ex)
        with np.errstate(invalid="ignore", divide="ignore"): mult[k] = ex / px.O[:, f]
        stopped[k] = st
    return mult, stopped

def fast_values(mult, stopped, baskets, cost_bps):
    """Final values (start 1) of many accounts at once, the same rules as simulate(). baskets: (paths, periods, n)
    series indexes, -1 for an empty slot."""
    c = cost_bps / 1e4; Pn, K, N = baskets.shape
    prev_val = np.zeros((Pn, N)); prevB = np.full((Pn, N), -1); cash = np.zeros(Pn); V = np.ones(Pn)
    for k in range(K):
        B = baskets[:, k, :]; valid = B >= 0; cnt = valid.sum(1); w = np.where(cnt > 0, 1.0 / np.maximum(cnt, 1), 0.0)
        if k == 0:
            V_open = np.ones(Pn); T = np.where(cnt > 0, 1.0, 0.0)
        else:
            V_open = cash + prev_val.sum(1)
            d = prev_val / V_open[:, None]
            held = prev_val > 0
            match = (B[:, :, None] == prevB[:, None, :]) & valid[:, :, None] & held[:, None, :]
            dnew = (match * d[:, None, :]).sum(2)
            gone = ~match.any(1)
            T = (valid * np.abs(w[:, None] - dnew)).sum(1) + (d * gone).sum(1)
        V = V_open * (1 - c * T)
        pos = V[:, None] * w[:, None] * valid
        Bc = np.maximum(B, 0)
        m = np.where(valid, mult[k][Bc], 0.0); st = np.where(valid, stopped[k][Bc], False)
        val = pos * m
        cash = (val * st).sum(1) * (1 - c) + np.where(cnt > 0, 0.0, V)
        prev_val = np.where(st | ~valid, 0.0, val); prevB = np.where(st | ~valid, -1, B)
    return cash + prev_val.sum(1) * (1 - c)
