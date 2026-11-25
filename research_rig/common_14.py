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

# ------------------------------------------------------------------------------------------------------- data checks
def not_trades(rows, run=5):
    """Dates of a member file's bars that are not real trades: zero volume, or inside a run of `run` or more rows in a
    row with identical open, high, low and close (the feed pads some files with a frozen last price after a takeover,
    a failure or under a reused ticker). Such bars are treated as no bar, so a run cuts the file like a gap."""
    bad = {r["date"] for r in rows if not float(r.get("volume") or 0) > 0}
    i = 0
    while i < len(rows):
        j = i; key = tuple(rows[i][k] for k in ("open", "high", "low", "close"))
        while j + 1 < len(rows) and tuple(rows[j + 1][k] for k in ("open", "high", "low", "close")) == key: j += 1
        if j - i + 1 >= run: bad |= {rows[t]["date"] for t in range(i, j + 1)}
        i = j + 1
    return bad

ASOF = os.path.join(os.path.dirname(BARS), "bars_asof")
STALE_RUN = 5            # sessions in a row, flat and with zero volume

def _read(p):
    out = {}
    if os.path.exists(p):
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh): out[r["date"]] = r
    return out

def _in_window(r, d):
    """Whether day d is one a row's file can touch: from 400 calendar days before the row starts (the twelve-month
    ranking look-back) to the day before the row ends, inside feed_from..feed_to."""
    a = (dt.date.fromisoformat(r["date_from"]) - dt.timedelta(days=400)).isoformat()
    return a <= d < r["date_to"] and (not r["feed_from"] or d >= r["feed_from"]) and (not r["feed_to"] or d <= r["feed_to"])

def asof_names(r):
    """The feed's files for the company that had ticker_then on the row's first usable day and on the first day of
    its window (the ranking look-back), named ticker_then@day. Labels that are not feed symbols (UA.C) use the feed
    ticker. Where the ticker did not exist on that day the file is empty or short: those days stay unchecked."""
    t = r["ticker_then"]
    sym = t if "." not in t or t in ("BRK.B", "BF.B") else r["ticker_feed"].split("@")[0]
    first = max(r["date_from"], r["feed_from"] or r["date_from"], str(P["start"]))
    w0 = max((dt.date.fromisoformat(r["date_from"]) - dt.timedelta(days=400)).isoformat(), r["feed_from"] or "0", str(P["start"]))
    return sorted({f"{sym}@{first}", f"{sym}@{w0}"})

# Extra asof files for rows whose label is a later ticker (the ticker then was another) or whose ticker passed to
# another security: the company's own earlier ticker on a day inside the window. Checked like the others.
EXTRA_ASOF = {
    "BKNG@2016-01-04": ["PCLN@2016-01-04"], "CBRE@2016-01-04": ["CBG@2016-01-04"], "JEF@2016-01-04": ["LUK@2016-01-04"],
    "TPR@2016-01-04": ["COH@2016-01-04"], "WELL@2016-01-04": ["HCN@2016-01-04"], "GL@2019-08-08": ["TMK@2018-07-05"],
    "BKR@2017-07-07": ["BHGE@2017-07-07"], "SPGI@2016-01-04": ["MHFI@2016-01-04"],
    "LMT@2016-01-04": ["LMT@2016-09-01"], "WMB@2016-01-04": ["WMB@2017-01-03"], "XL@2016-01-04": ["XL@2017-01-03"],
    "CB@2016-01-04": ["ACE@2016-01-04", "CB@2016-02-01"], "META@2022-06-09": ["FB@2021-05-05"], "BNY@2026-05-21": ["BK@2025-04-16"],
    "DOC@2024-03-04": ["PEAK@2023-01-29"], "IR@2020-03-03": ["GDI@2019-01-28"], "CZR@2021-03-22": ["ERI@2020-02-16"],
}

def same_stock(F, G, days):
    """Whether two files are the same stock on their common traded days: the ratio of their volumes stays the same
    from one common day to the next (within 1%) on at least 98% of steps. Adjustments scale volume by a constant that
    can step at a corporate action; two different stocks' volumes do not keep a fixed ratio."""
    q = np.array([float(F[d]["volume"]) / float(G[d]["volume"]) for d in days])
    if len(q) < 2: return len(q) == 0 or True
    return float(np.mean(np.abs(q[1:] / q[:-1] - 1) < 0.01)) >= 0.98

def data_checks(members, days, bars=None, asof=None):
    """Three checks on the bar files, using dates and volumes (never a return). Each flag is keyed ticker_then@date_from.
    stale: the row's file has STALE_RUN or more sessions in a row that are flat with zero volume inside the window.
    identity: the row's file, inside the window, is not the same stock (same_stock) as the feed's file for the company
    that had ticker_then on the row's first usable day or on its window's first day (asof_names). Days no asof file
    covers (the ticker did not exist then, for a label the list uses for earlier days) are reported as unchecked.
    duplicate: two rows of different companies whose files show the same volume on the same month-end three or more
    times (one company counted twice)."""
    B = bars or BARS; A = asof or ASOF
    stale, ident, dup, unchecked = [], [], [], []
    cache = {}
    def get(f): 
        if f not in cache: cache[f] = _read(os.path.join(B, f + ".csv"))
        return cache[f]
    for r in members:
        if not r["ticker_feed"]: continue
        key = f"{r['ticker_then']}@{r['date_from']}"
        F = get(r["ticker_feed"]); ds = sorted(d for d in F if _in_window(r, d))
        run = 0; pc = None
        for d in ds:
            x = F[d]; flat = x["open"] == x["high"] == x["low"] == x["close"] and not float(x["volume"] or 0) > 0
            run = run + 1 if flat and run and x["close"] == pc else (1 if flat else 0)
            pc = x["close"]
            if run == STALE_RUN: stale.append(dict(key=key, file=r["ticker_feed"], run_ends=d)); break
        traded = [d for d in ds if float(F[d]["volume"] or 0) > 0]
        if not traded: continue
        checked = set()
        for an in asof_names(r) + EXTRA_ASOF.get(key, []):
            G = _read(os.path.join(A, an + ".csv"))
            common = [d for d in traded if d in G and float(G[d]["volume"] or 0) > 0]
            if not same_stock(F, G, common):
                ident.append(dict(key=key, file=r["ticker_feed"], asof=an, why=f"not the same stock on {len(common)} common trading days"))
            checked |= set(common)
        un = [d for d in traded if d not in checked]
        if un: unchecked.append(dict(key=key, file=r["ticker_feed"], days=len(un), first=un[0], last=un[-1]))
    me = [days[i] for i in month_end_index(days)]
    seen = {}
    for r in members:
        if not r["ticker_feed"]: continue
        F = get(r["ticker_feed"])
        for d in me:
            if r["date_from"] <= d < r["date_to"] and d in F and float(F[d]["volume"] or 0) > 0 and (not r["feed_from"] or d >= r["feed_from"]) and (not r["feed_to"] or d <= r["feed_to"]):
                seen.setdefault((d, F[d]["volume"]), set()).add((r["company_id"], f"{r['ticker_then']}@{r['date_from']}"))
    pairs = {}
    for v in seen.values():
        cids = {c for c, _ in v}
        if len(cids) > 1:
            k = tuple(sorted(x for _, x in v)); pairs[k] = pairs.get(k, 0) + 1
    dup = [dict(keys=list(k), month_ends=n) for k, n in sorted(pairs.items()) if n >= 3]
    return dict(stale=stale, identity=ident, duplicate=dup, identity_unchecked=unchecked)

def flags_listed(checks, plan_text):
    """Flags not named in the plan. A flag counts as listed when its key (ticker_then@date_from) appears on a plan line
    that also says why (any line containing the key and the word 'because')."""
    lines = [l for l in plan_text.splitlines() if "because" in l.lower()]
    keys = [f["key"] for f in checks["stale"] + checks["identity"]] + ["+".join(f["keys"]) for f in checks["duplicate"]]
    return [k for k in keys if not any(all(part in l for part in k.split("+")) for l in lines)]

# ------------------------------------------------------------------------------------------------------------ prices
class Prices:
    """Opens and closes of each series on the calendar, NaN where there is no bar or outside feed_from..feed_to.
    A member's bar that is not a real trade (not_trades: zero volume, or a run of five or more identical rows) is treated
    as no bar; SPY, SPMO and MTUM are read as they are. last[s] is the last day with a close."""
    def __init__(self, days, members, bars=None, extra=SCALE):
        self.days = list(days); self.n = len(days); idx = {d: i for i, d in enumerate(self.days)}
        keys = sorted({r["series"] for r in members if r["series"]} | {f"{s}||" for s in extra})
        self.keys = []; self.si = {}; O, Cl = [], []; self.read = set()
        for k in keys:
            feed, ff, ft = k.split("|"); p = os.path.join(bars or BARS, feed + ".csv"); fund = feed in extra and not ff and not ft
            o = np.full(self.n, np.nan); c = np.full(self.n, np.nan)
            if os.path.exists(p):
                self.read.add(p)
                with open(p, newline="") as fh: rows = list(csv.DictReader(fh))
                bad = set() if fund else not_trades(rows)
                for r in rows:
                    d = r["date"]; i = idx.get(d)
                    if i is None or (ff and d < ff) or (ft and d > ft) or d in bad: continue
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

def _ranks(u):
    """Rank of each entry within its row (0 = smallest), one sort."""
    o = np.argsort(u, axis=1); r = np.empty_like(o)
    np.put_along_axis(r, o, np.broadcast_to(np.arange(u.shape[1]), u.shape), axis=1)
    return r

def random_baskets(periods, px, n, draws, rng, kept=None, stopped=None):
    """Yardstick (c), turnover-matched: an array (draws, periods, n) of series indexes, -1 where a basket is short.
    Eligible on a ranking day: the stocks the rule could rank that have an open on the purchase day, sorted by ticker.
    On the first ranking day each path draws n of them at random. On each later one it keeps exactly as many of its
    holdings as the rule kept that day (kept[k]; fewer if it has fewer eligible holdings left), chosen at random among
    its holdings that are still eligible and were not stopped, and draws the rest at random from the eligible stocks it
    did not hold. Without kept, every month is a fresh draw. stopped: period_moves()[2]."""
    K = len(periods); out = np.full((draws, K, n), -1, int); S = len(px.keys)
    for k, p in enumerate(periods):
        pool = np.array([s for _, t, s in sorted(p["ranked"], key=lambda x: x[1])], int)
        elig = pool[~np.isnan(px.O[pool, p["fill"]])] if len(pool) else pool
        if len(elig) == 0: continue
        is_el = np.zeros(S, bool); is_el[elig] = True
        if k == 0 or kept is None:
            keep_ids = np.full((draws, 0), -1, int); kt = np.zeros(draws, int)
        else:
            prev = out[:, k - 1, :]; pc = np.maximum(prev, 0)
            alive = (prev >= 0) & is_el[pc] & ~stopped[k - 1][pc]
            kt = np.minimum(kept[k], alive.sum(1))
            u = np.where(alive, rng.random(prev.shape), np.inf)
            rk = _ranks(u)
            keep_ids = np.where(rk < kt[:, None], prev, -1)
        held = np.zeros((draws, S), bool)                 # every holding, kept or let go, is out of the new draw
        if k > 0 and kept is not None:
            r_, c_ = np.nonzero(prev >= 0); held[r_, prev[r_, c_]] = True
        need = np.minimum(n, len(elig)) - kt
        u2 = np.where(held[:, elig], np.inf, rng.random((draws, len(elig))))
        rk2 = _ranks(u2)
        new_ids = np.where(rk2 < need[:, None], elig[None, :], -1)
        allv = np.concatenate([keep_ids, new_ids], axis=1)
        idx = np.argsort(allv < 0, axis=1, kind="stable")[:, :n]
        got = np.take_along_axis(allv, idx, 1)
        out[:, k, :got.shape[1]] = got
    return out

# ------------------------------------------------------------------------------------------------------- portfolio
def simulate(px, fills, baskets, cost_bps, daily=False):
    """One account through the periods. fills[k] is the purchase day index of period k, baskets[k] the series indexes
    bought in equal parts at that open. Period k runs to the next fill's open; the last runs to the close of the last
    day and is then sold. Inside a period parts drift with prices.
    A held stock with no bar on or after the next re-form day (or after the last day, for the last period) is sold at
    its last close that day, flagged, and the money sits in cash until the next re-form.
    A held stock with no open at a re-form but prices later (a gap) cannot be traded that day: it is valued at its last
    close, kept as it is (not sold, not topped up) and carried through the next period on its own prices; only the rest
    of the account is re-formed.
    Cost: cost_bps per side on what is traded at each re-form (the sum of |new part - drifted part| over the stocks that
    can be traded; the first purchase is all traded); a stop sale and the final sale are charged on what is sold.

    Returns dict: value (final, start 1), at_fill (value at each fill open before that re-form's cost), turnover (traded
    share of the account at each re-form), flags (list of (period, series index, last close day)), carried (list of
    (period, series index) held through a gap), daily (close values) if daily."""
    c = cost_bps / 1e4; n = px.n; K = len(fills)
    cash = 1.0; held = {}                  # series -> value at this re-form (open, or last close for a gap)
    at_fill, turn, flags, carried = [], [], [], []
    dv = np.full(n, np.nan) if daily else None
    for k in range(K):
        f = fills[k]; end = fills[k + 1] if k + 1 < K else n      # period days f .. end-1
        V_open = cash + sum(held.values())
        at_fill.append(V_open)
        frozen = {s: v for s, v in held.items() if np.isnan(px.O[s, f])}
        trade = {s: v for s, v in held.items() if s not in frozen}
        Vt = cash + sum(trade.values())
        b = [s for s in dict.fromkeys(baskets[k]) if s not in frozen]
        w = 1.0 / len(b) if b else 0.0
        tv = {s: Vt * w for s in b}
        T = sum(abs(tv.get(s, 0.0) - trade.get(s, 0.0)) for s in set(tv) | set(trade)) / V_open if V_open > 0 else 0.0
        turn.append(T)
        V_tr = Vt - c * T * V_open
        cash = 0.0 if b else V_tr
        # positions: (series, value at start, price at start); bought at the open, or carried from the last close
        P_ = [(s, V_tr * w, px.O[s, f]) for s in b] + [(s, v, px.CF[s, f - 1]) for s, v in frozen.items()]
        carried += [(k, s) for s in frozen]
        need = end if k + 1 < K else n - 1      # a bar on or after this day means the prices go on
        stp = {s: int(px.last[s]) for s, _, _ in P_ if px.last[s] < need}
        if daily:
            for t in range(f, end):
                tot = cash
                for s, v, p0 in P_:
                    if s in stp and t >= stp[s]: tot += v * px.C[s, stp[s]] / p0 * (1 - c)
                    else: tot += v * px.CF[s, t] / p0
                dv[t] = tot
        newheld = {}; add_cash = 0.0
        for s, v, p0 in P_:
            if s in stp:
                add_cash += v * px.C[s, stp[s]] / p0 * (1 - c); flags.append((k, s, stp[s]))
            elif k + 1 < K:
                nf = fills[k + 1]; p = px.O[s, nf]
                if np.isnan(p): p = px.CF[s, nf - 1]
                newheld[s] = v * p / p0
            else:
                newheld[s] = v * px.CF[s, n - 1] / p0
        cash += add_cash; held = newheld
    V_end = cash + sum(held.values()) * (1 - c)
    if daily: dv[n - 1] = V_end
    return dict(value=V_end, at_fill=at_fill, turnover=turn, flags=flags, carried=carried, daily=dv)

def hold_one(px, s, f0, cost_bps):
    """One fund (SPY, SPMO, MTUM) bought at the open of day f0 and sold at the last close, one buy and one sell charged.
    Returns (final value, value at each later open as a function, daily closes)."""
    c = cost_bps / 1e4
    units = (1 - c) / px.O[s, f0]
    daily = units * px.CF[s]; daily[:f0] = np.nan
    final = units * px.CF[s, -1] * (1 - c)
    daily[-1] = final                       # the last mark includes the sale, so the year table and the total agree
    return final, units, daily

def max_drop(x):
    x = x[~np.isnan(x)]
    if len(x) == 0: return float("nan")
    peak = np.maximum.accumulate(x); return float((x / peak - 1).min())

def period_moves(px, fills):
    """For each period k and series s: mult[k, s] = exit value / purchase open; multg[k, s] = exit value / last close
    before the fill (for a stock carried through a gap); stopped[k, s]; noopen[k, s] (no open on the fill day). Exit is
    the next re-form open (the last close carried over if there is no open then), or the last close of the last day;
    for a series with no bar on or after that day it is the series' last close (a stop)."""
    K = len(fills); n = px.n; S = len(px.keys)
    mult = np.full((K, S), np.nan); multg = np.full((K, S), np.nan)
    stopped = np.zeros((K, S), bool); noopen = np.zeros((K, S), bool)
    lastc = px.C[np.arange(S), np.maximum(px.last, 0)]
    for k in range(K):
        f = fills[k]; end = fills[k + 1] if k + 1 < K else n
        need = end if k + 1 < K else n - 1
        st = px.last < need
        if k + 1 < K: ex = np.where(np.isnan(px.O[:, end]), px.CF[:, end - 1], px.O[:, end])
        else: ex = px.CF[:, n - 1]
        ex = np.where(st, lastc, ex)
        with np.errstate(invalid="ignore", divide="ignore"):
            mult[k] = ex / px.O[:, f]
            if f > 0: multg[k] = ex / px.CF[:, f - 1]
        stopped[k] = st; noopen[k] = np.isnan(px.O[:, f])
    return mult, multg, stopped, noopen

def fast_values(moves, baskets, cost_bps):
    """Final values (start 1) of many accounts at once, the same rules as simulate() (checked in test_14.py).
    moves: period_moves(). baskets: (paths, periods, n) series indexes, -1 for an empty slot."""
    mult, multg, stopped, noopen = moves
    c = cost_bps / 1e4; Pn, K, N = baskets.shape
    pv = np.zeros((Pn, 0)); pid = np.full((Pn, 0), -1); cash = np.ones(Pn)
    for k in range(K):
        B = baskets[:, k, :]; valid = B >= 0; cnt = valid.sum(1); w = np.where(cnt > 0, 1.0 / np.maximum(cnt, 1), 0.0)
        has = pid >= 0; pc = np.maximum(pid, 0)
        Fz = has & noopen[k][pc]
        trv = np.where(Fz, 0.0, pv)
        V_open = cash + pv.sum(1); Vt = cash + trv.sum(1)
        live = has & ~Fz
        match = (B[:, :, None] == pid[:, None, :]) & valid[:, :, None] & live[:, None, :]
        dnew = (match * trv[:, None, :]).sum(2)
        gone = live & ~match.any(1)
        tv = Vt * w
        T = ((valid * np.abs(tv[:, None] - dnew)).sum(1) + (trv * gone).sum(1)) / np.where(V_open > 0, V_open, 1.0)
        V_tr = Vt - c * T * V_open
        Bc = np.maximum(B, 0)
        vals = np.concatenate([V_tr[:, None] * w[:, None] * valid * np.where(valid, mult[k][Bc], 0.0),
                               np.where(Fz, pv * np.where(Fz, multg[k][pc], 0.0), 0.0)], axis=1)
        ids = np.concatenate([np.where(valid, B, -1), np.where(Fz, pid, -1)], axis=1)
        st = np.concatenate([valid & stopped[k][Bc], Fz & stopped[k][pc]], axis=1)
        cash = (vals * st).sum(1) * (1 - c) + np.where(cnt > 0, 0.0, V_tr)
        keep = ~st & (ids >= 0)
        pv = np.where(keep, vals, 0.0); pid = np.where(keep, ids, -1)
        cols = keep.any(0); pv, pid = pv[:, cols], pid[:, cols]
    return cash + pv.sum(1) * (1 - c)
