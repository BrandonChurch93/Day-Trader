"""Replay 04 helpers: many coins, one account, shared cash. Long or cash only. Not the product.
Signals use bars up to and including day t. Fills happen at the open of day t+1."""
import numpy as np, pandas as pd, glob, os
KDIR="/home/user/workspace/rig/kraken/daily"
OTHER_QUOTE=("PYUSD","RLUSD")           # files whose name ends in USD but whose quote is another coin
def load_all():
    """Returns dict pair -> DataFrame(open, close, dv) on a full daily calendar from the pair's first to last bar.
    Days with no trades are filled with the last close and zero volume."""
    out={}
    for f in sorted(glob.glob(f"{KDIR}/*USD_1440.csv")):
        p=os.path.basename(f)[:-9]
        if any(p.endswith(q) and p!=q for q in OTHER_QUOTE): continue
        d=pd.read_csv(f,header=None,names=["ts","open","high","low","close","volume","n"])
        if len(d)<2: continue
        d.index=pd.to_datetime(d.ts,unit="s"); d=d[~d.index.duplicated()].sort_index()
        full=pd.date_range(d.index[0],d.index[-1],freq="D"); d=d.reindex(full)
        d["close"]=d.close.ffill(); d["open"]=d.open.fillna(d.close); d["volume"]=d.volume.fillna(0.0)
        d["dv"]=d.close*d.volume; out[p]=d[["open","close","dv"]]
    return out
def panel(data, start, end):
    idx=pd.date_range(start,end,freq="D"); P=sorted(data)
    O=pd.DataFrame({p:data[p].open.reindex(idx) for p in P}); C=pd.DataFrame({p:data[p].close.reindex(idx) for p in P}); DV=pd.DataFrame({p:data[p].dv.reindex(idx) for p in P})
    return O,C,DV
def simulate_basket(O, C, W, cost_bps, band, last_day=None, delist_haircut=0.0):
    """O, C: T x N arrays of open and close (nan where the pair does not trade). W: T x N target weights decided at close of t.
    cost_bps: length-N array of cost per side. A coin is traded at the open of t+1 when it is a full switch (to or from zero)
    or when its weight is off target by more than band[i]. last_day[i]: index of the pair's last bar; a position still held
    after that bar is sold at that bar's close, less cost and less delist_haircut. Returns equity at each close, weights, traded notional, events."""
    T,N=C.shape; units=np.zeros(N); cash=1.0; eq=np.empty(T); wt=np.zeros((T,N)); traded=np.zeros((T,N)); k=np.asarray(cost_bps)/1e4; ev=[]
    lastpx=np.full(N,np.nan)
    for t in range(T):
        if t>0:
            # forced exits for pairs whose data ended at t-1
            if last_day is not None:
                for i in np.flatnonzero((units>0)&(last_day==t-1)):
                    v=units[i]*lastpx[i]*(1-delist_haircut); cash+=v*(1-k[i]); traded[t,i]+=v; units[i]=0.0; ev.append((t,i,v))
            o=O[t]; ok=~np.isnan(o); val=np.where(ok,units*np.where(ok,o,0.0),units*np.nan_to_num(lastpx)); e=cash+val.sum()
            tw=np.nan_to_num(W[t-1],nan=0.0); cur=val/e if e>0 else np.zeros(N)
            need=ok&((((tw==0)&(cur>0))|((tw>0)&(cur==0)))|(np.abs(tw-cur)>band))
            # sells first, then buys with the cash there is
            for i in np.flatnonzero(need&(tw<cur)):
                x=min(val[i]-tw[i]*e, val[i]) if tw[i]>0 else val[i]
                units[i]-=x/o[i]; cash+=x*(1-k[i]); traded[t,i]+=x
                if tw[i]==0: units[i]=0.0
            buy=np.flatnonzero(need&(tw>cur))
            if len(buy):
                x=np.maximum(tw[buy]*e-val[buy],0.0); spend=(x*(1+k[buy])).sum()
                if spend>cash and spend>0: x=x*max(cash,0.0)/spend      # not enough cash: scale every buy down by the same share
                units[buy]+=x/o[buy]; cash-=(x*(1+k[buy])).sum(); traded[t,buy]+=x
        c=C[t]; okc=~np.isnan(c); lastpx=np.where(okc,c,lastpx)
        v=units*np.nan_to_num(lastpx); eq[t]=cash+v.sum(); wt[t]=v/eq[t] if eq[t]>0 else 0.0
    return eq, wt, traded, ev

# ======================================================================== replay 04 additions (2026-11-25)
# Added for run_04.py. simulate_basket above is left unchanged; see sim_batch for the A12 band reading.
END_DATE = "2026-09-30"
def load_raw(end=END_DATE):
    """dict pair -> DataFrame on a full daily calendar from the pair's first to last bar (cut at `end`), with
    open: the raw open, nan on days that were filled in (no row in the raw file, so no trade);
    close: the last close carried forward; dv: close * volume (0 on filled days); traded: True where a raw row exists.
    Input checks (A17): sorted, unique, 00:00 UTC, positive prices, volume above zero on every raw row."""
    out = {}
    for f in sorted(glob.glob(f"{KDIR}/*USD_1440.csv")):
        p = os.path.basename(f)[:-9]
        if any(p.endswith(q) and p != q for q in OTHER_QUOTE): continue
        d = pd.read_csv(f, header=None, names=["ts", "open", "high", "low", "close", "volume", "n"])
        assert d.ts.is_monotonic_increasing and d.ts.is_unique and (d.ts % 86400 == 0).all(), p
        assert (d[["open", "high", "low", "close"]] > 0).all().all() and (d.volume > 0).all(), p
        d.index = pd.to_datetime(d.ts, unit="s"); d = d[d.index <= pd.Timestamp(end)]
        if len(d) < 2: continue
        full = pd.date_range(d.index[0], d.index[-1], freq="D"); tr = pd.Series(True, index=d.index).reindex(full, fill_value=False)
        d = d.reindex(full); x = pd.DataFrame(index=full)
        x["open"] = d.open; x["close"] = d.close.ffill(); x["dv"] = (d.close * d.volume).fillna(0.0); x["traded"] = tr.values
        out[p] = x
    return out

def big_panel(raw, end=END_DATE):
    """Arrays on one calendar from the earliest first bar to `end`. C: close carried forward inside the pair's
    history, nan before the first and after the last bar. CM: like C but carried forward after the last bar too
    (used only by the membership tests, where a pair that stopped trading simply shows no trades). O: raw open
    (nan when no trade). DV, TR. first/last: row of the first and last bar."""
    names = sorted(raw); idx = pd.date_range(min(raw[p].index[0] for p in names), end, freq="D")
    def col(f, fill): return np.column_stack([raw[p][f].reindex(idx).values if fill is None else raw[p][f].reindex(idx).fillna(fill).values for p in names])
    C = col("close", None).astype(float); O = col("open", None).astype(float); DV = col("dv", 0.0).astype(float)
    TR = np.column_stack([raw[p]["traded"].reindex(idx, fill_value=False).values.astype(bool) for p in names])
    first = np.array([idx.get_loc(raw[p].index[0]) for p in names]); last = np.array([idx.get_loc(raw[p].index[-1]) for p in names])
    CM = pd.DataFrame(C).ffill().values
    return dict(idx=idx, names=names, C=C, CM=CM, O=O, DV=DV, TR=TR, first=first, last=last)

def month_members(P, d, min_hist=200, win=90, max_notrade=10, peg_vol=0.20, copy_corr=0.98, ppy=365):
    """Ranked list of qualifying pairs (column numbers, highest median dollar volume first) for the month that starts
    at row d, using rows strictly before d only. Reading of each test is written in run_04.py READING."""
    if d - win - 1 < 0: return [], {}
    first = P["first"]; hist = (first < d) & ((d - first) >= min_hist)
    notr = (~P["TR"][d - win:d]).sum(0); active = notr <= max_notrade
    w = P["CM"][d - win - 1:d]
    with np.errstate(invalid="ignore", divide="ignore"):
        r = w[1:] / w[:-1] - 1
    cand = np.flatnonzero(hist & active & np.isfinite(r).all(0))
    vol = r[:, cand].std(0, ddof=1) * np.sqrt(ppy); cand = cand[vol >= peg_vol]
    med = np.median(P["DV"][d - win:d], axis=0)
    order = sorted(cand.tolist(), key=lambda j: (-med[j], P["names"][j]))
    keep = []; dropped = {}
    if order:
        rr = r[:, order]; cm = np.corrcoef(rr, rowvar=False) if len(order) > 1 else np.ones((1, 1)); cm = np.atleast_2d(cm)
        for a, j in enumerate(order):
            hi = [order[b] for b in range(a) if np.isfinite(cm[a, b]) and cm[a, b] > copy_corr]
            if hi: dropped[P["names"][j]] = P["names"][hi[0]]
            else: keep.append(j)
    return keep, dict(med_dv={P["names"][j]: float(med[j]) for j in keep}, copies_dropped=dropped)

def ret_lookback(P, d, L=90):
    """Return over the last L days known before row d: close of d-1 over close of d-1-L."""
    return P["CM"][d - 1] / P["CM"][d - 1 - L] - 1

def k5_weight(close, halflives=((1, 5), (2.5, 10), (5, 20), (10, 40)), n=180):
    """CoinDesk-style trend weight from closes up to each day: for each half-life pair, weighted averages over the last
    n closes with weights 2^(-i/h), i = 0 (latest) .. n-1, normalised. Share of pairs with short >= long. nan until n closes."""
    c = np.asarray(close, float); T = len(c); out = np.full(T, np.nan)
    if T < n: return out
    win = np.lib.stride_tricks.sliding_window_view(c, n)[:, ::-1]      # row j: closes j+n-1, j+n-2, ..., j
    i = np.arange(n); s = np.zeros(win.shape[0])
    for hs, hl in halflives:
        ws = 2.0 ** (-i / hs); ws /= ws.sum(); wl = 2.0 ** (-i / hl); wl /= wl.sum()
        s += (win @ ws >= win @ wl)
    out[n - 1:] = s / len(halflives); return out

def hold_on_weekday(w, dates, weekday=2):
    """Target changed only at the close of the given UTC weekday, held otherwise (nan before the first such day)."""
    s = pd.Series(np.where(pd.DatetimeIndex(dates).weekday == weekday, w, np.nan), index=dates)
    return s.ffill().values

def sim_batch(O, C, W, cost_bps, band, last_day=None, delist_haircut=0.0, member=None, rebal=None, zero_exception=False,
              detail=False, dust=1e-9):
    """Batched shared-cash engine. O, C: T x N (nan open = the pair did not trade that day, so no fill; nan close =
    outside the pair's history). W: B x T x N or T x N target weights decided at the close of t, acted on at the
    open of the next day the pair trades (an order waits and then uses the newest target, A07).
    Trades when |target - weight| > band[i] (A12, no exception) or, when member is given, when the target is zero
    and the pair has left its basket (member[t-1, i] False): such a pair is sold whatever the band.
    zero_exception=True reproduces simulate_basket exactly (any move to or from zero trades), used only by the check.
    rebal: length-T bool; if given, trades happen only on orders placed on those fill days (all pairs, band 0),
    each waiting until its pair trades. Used by the two hold benchmarks. A full sale leaves exactly zero units;
    a buy that uses all the cash leaves exactly zero cash (A04).
    Returns dict with eq (B x T) and counters; with detail=True also wt, traded (B x T x N), forced exits, waits."""
    T, N = C.shape; W = np.asarray(W, float); single = W.ndim == 2
    if single: W = W[None]
    B = W.shape[0]; k = np.broadcast_to(np.asarray(cost_bps, float) / 1e4, (B, N)) if np.ndim(cost_bps) == 2 else np.broadcast_to(np.asarray(cost_bps, float) / 1e4, (N,))[None].repeat(B, 0)
    band = np.broadcast_to(np.asarray(band, float), (N,))
    units = np.zeros((B, N)); cash = np.ones(B); eq = np.empty((B, T)); lastpx = np.full(N, np.nan)
    sides = np.zeros(B, int); wsum = np.zeros(B); held_days = np.zeros(B); old_exc = np.zeros(B, int)
    if detail: wt = np.zeros((B, T, N)); traded = np.zeros((B, T, N)); ev = []; waits = np.zeros(B, int); waiting = np.zeros((B, N), bool)
    pending = np.zeros((B, N), bool)
    ld = None if last_day is None else np.asarray(last_day)
    for t in range(T):
        if t > 0:
            tr_t = np.zeros((B, N)); pe = eq[:, t - 1]
            if ld is not None:
                f = (ld == t - 1)
                if f.any():
                    fm = (units > 0) & f[None]
                    if fm.any():
                        v = np.where(fm, units * np.nan_to_num(lastpx) * (1 - delist_haircut), 0.0)
                        cash = cash + (v * (1 - k)).sum(1); tr_t += v; units = np.where(fm, 0.0, units)
                        if detail: ev += [(t, int(i), int(b), float(v[b, i])) for b, i in zip(*np.nonzero(fm))]
            o = O[t]; ok = ~np.isnan(o); oo = np.where(ok, o, 1.0)
            px = np.where(ok, o, np.nan_to_num(lastpx)); val = units * px[None]; e = cash + val.sum(1)
            tw = np.nan_to_num(W[:, t - 1, :], nan=0.0)
            cur = np.where(e[:, None] > 0, val / np.where(e > 0, e, 1.0)[:, None], 0.0)
            if rebal is not None:
                if rebal[t]: pending[:] = True
                want = pending & (np.abs(tw - cur) > 0)
            elif zero_exception:
                want = ((tw == 0) & (cur > 0)) | ((tw > 0) & (cur == 0)) | (np.abs(tw - cur) > band[None])
            else:
                want = np.abs(tw - cur) > band[None]
                if member is not None: want |= (tw == 0) & (cur > 0) & ~member[t - 1][None]
            need = want & ok[None]
            if rebal is None and not zero_exception:   # days on which simulate_basket's to/from-zero exception would have traded and this engine does not
                old_exc += (ok[None] & ~want & (((tw == 0) & (cur > 0)) | ((tw > 0) & (cur == 0)))).sum(1)
            if detail:
                nw = want & ~ok[None]; waits += (nw & ~waiting).sum(1); waiting = nw
            if rebal is not None: pending &= ~ok[None]
            s = need & (tw < cur)
            if s.any():
                x = np.where(s, np.where(tw > 0, np.minimum(val - tw * e[:, None], val), val), 0.0)
                units = units - x / oo[None]; units = np.where(s & (tw == 0), 0.0, units)
                cash = cash + (x * (1 - k)).sum(1); tr_t += x
            bm = need & (tw > cur)
            if bm.any():
                x = np.where(bm, np.maximum(tw * e[:, None] - val, 0.0), 0.0); spend = (x * (1 + k)).sum(1)
                sc = (spend > cash) & (spend > 0); x = np.where(sc[:, None], x * (np.maximum(cash, 0.0) / np.where(spend > 0, spend, 1.0))[:, None], x)
                units = units + x / oo[None]; cash = np.where(sc, 0.0, cash - (x * (1 + k)).sum(1)); tr_t += x
            sides += (tr_t > dust * pe[:, None]).sum(1)
            if detail: traded[:, t] = tr_t
        c = C[t]; lastpx = np.where(~np.isnan(c), c, lastpx)
        v = units * np.nan_to_num(lastpx)[None]; eq[:, t] = cash + v.sum(1)
        ws = v.sum(1) / np.where(eq[:, t] > 0, eq[:, t], 1.0); wsum += ws; held_days += ws > 1e-6
        if detail: wt[:, t] = v / np.where(eq[:, t] > 0, eq[:, t], 1.0)[:, None]
    out = dict(eq=eq, sides=sides, avg_weight=wsum / T, share_days_with_position=held_days / T, old_exception_would_fire=old_exc)
    if detail: out.update(wt=wt, traded=traded, ev=ev, waits=waits)
    if single: out = {kk: (vv[0] if isinstance(vv, np.ndarray) and vv.ndim >= 1 and vv.shape[0] == 1 else vv) for kk, vv in out.items()}
    return out

simulate_basket2 = sim_batch   # name agreed with the lead: literal band, exceptions only where the plan says "sold"

def circular_shift_in_span(x, a, b, rng, min_shift=30):
    """x: full column of a weight series; [a, b] the pair's own rows. The part inside [a, b] is shifted by
    rig2.null_circular (random start, wrapped around, shift >= min_shift); rows outside are left as they are.
    Spans too short to shift (fewer than 2 * min_shift + 1 rows) are returned unchanged and flagged."""
    import rig2 as R
    y = np.array(x, float); n = b - a + 1
    if n < 2 * min_shift + 1: return y, False
    y[a:b + 1] = R.null_circular(y[a:b + 1], rng, min_shift); return y, True
