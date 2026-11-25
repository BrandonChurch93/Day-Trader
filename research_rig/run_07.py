"""Replay 07: day trading rules N1 to N8 on SPY and QQQ one-minute bars. Plan: PREREG_07_intraday_spy_qqq.md (frozen before any run).
Reads the one-minute and daily files collected through the workspace's own price lookup (data/platform_bars/ or PLATFORM_BARS_DIR).
Prints no price and stores no price. Every number that is not part of a rule's definition is read from config/thresholds.yaml.

Usage, from research_rig/:
  python3 run_07.py --fixtures   checks only, reads no price
  python3 run_07.py --dev        development slice only: reads no file after replay_07_dates.dev_end and cuts every series there.
                                 Writes /tmp/results_07_dev.json, outside the repo
  python3 run_07.py --full       the one run of the held-back years. Writes results_07.json
"""
import sys, os, json, math, glob, hashlib, subprocess, datetime as dt
import numpy as np, pandas as pd
import rig2 as R
from platform_bars_integrity import HOL, EARLY   # rule-based NYSE calendar, written from memory (UNKNOWN accuracy)

HERE = os.path.dirname(os.path.abspath(__file__))
BARS = os.environ.get("PLATFORM_BARS_DIR", os.path.join(HERE, "data", "platform_bars"))
CO = R.th("replay_07_costs"); DA = R.th("replay_07_data"); DT = R.th("replay_07_dates"); ST = R.th("replay_07_statistics")
LIQ = R.th("cost_model_bps_per_side_liquid_etf")
COSTS = {"low": float(CO["low_bps_per_side"]), "lower": float(LIQ[0]), "upper": float(LIQ[1])}
JUDGED = ("lower", "upper")
PPY = ST["days_per_year"]; SEED = ST["seed"]; NSHUF = ST["shuffles"]; N_TRIALS = ST["trial_count"]; BLOCKS = ST["pbo_blocks"]
WARM = DA["warmup_days"]; GAP = DA["max_gap_vs_daily_bps"]
RULES = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]
SYMS = ["SPY", "QQQ"]
FIRST_ID = {"SPY": ST["first_trial_id"], "QQQ": ST["first_trial_id"] + len(RULES)}
FULL, HALF = 390, 210   # regular minutes on a full day and on an early close

# ------------------------------------------------------------------ stock-calendar bar check
def check_day(date, ts_ny, o, h, l, c, v):
    """One day of one-minute bars. ts_ny: New York times (pandas Timestamps, tz aware). Returns (kind, reason, keep) where
    kind is 'full', 'early' or None (day not used), and keep is a boolean mask of the bars kept (only on a used day)."""
    if date.weekday() >= 5: return None, "weekend", None
    if date in HOL: return None, "holiday", None
    secs = np.array([t.second for t in ts_ny]) + np.array([t.microsecond for t in ts_ny])
    mins = np.array([t.hour * 60 + t.minute for t in ts_ny]) - 570
    early = date in EARLY; last = HALF if early else FULL
    keep = np.ones(len(mins), bool)
    if early: keep = mins < HALF          # bars after 12:59 on an early close are outside regular hours and are dropped
    if (secs[keep] != 0).any(): return None, "timestamp not on a whole minute", None
    m = mins[keep]
    if len(m) != last or len(np.unique(m)) != last or m.min() != 0 or m.max() != last - 1: return None, "not every regular minute exactly once", None
    oo, hh, ll, cc = o[keep], h[keep], l[keep], c[keep]
    if not ((oo > 0) & (hh > 0) & (ll > 0) & (cc > 0)).all(): return None, "price not positive", None
    if not ((hh >= np.maximum(oo, cc)) & (ll <= np.minimum(oo, cc))).all(): return None, "high or low inconsistent", None
    if not (np.isfinite(v[keep]) & (v[keep] >= 0)).all(): return None, "volume missing", None
    return ("early" if early else "full"), "", keep

def gap_ok(hi, lo, last_close, drow):
    """drow: (high, low, close) of the daily file, or None. True if the one-minute day agrees within the band."""
    if drow is None: return False, "no daily row"
    dh, dl, dc = drow; b = GAP / 1e4
    if hi > dh * (1 + b): return False, "one-minute high above daily high"
    if lo < dl * (1 - b): return False, "one-minute low below daily low"
    if abs(last_close / dc - 1) > b: return False, "last one-minute close away from daily close"
    return True, ""

# ------------------------------------------------------------------ loading
def sha(p):
    x = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""): x.update(ch)
    return x.hexdigest()

def load(sym, end):
    """Returns the used days as arrays (n, 390) with NaN past the last minute of an early close, and the record of days not used."""
    files = sorted(glob.glob(os.path.join(BARS, "1min", f"{sym}_1min_*.csv")))
    files = [f for f in files if int(f[-8:-4]) <= int(end[:4])]
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    ts = pd.to_datetime(df["date"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    df["ny"] = ts; df["d"] = ts.dt.date
    df = df[df["d"] <= dt.date.fromisoformat(end)].sort_values("ny")
    dfile = os.path.join(BARS, "1day", f"{sym}_1day.csv"); dd = pd.read_csv(dfile)
    dd = dd[pd.to_datetime(dd["date"]).dt.date <= dt.date.fromisoformat(end)]
    daily = {dt.date.fromisoformat(r.date): (r.high, r.low, r.close) for r in dd.itertuples()}
    days, kinds, O, H, L, C, V, dropped = [], [], [], [], [], [], [], []
    for d, g in df.groupby("d", sort=True):
        a = [g[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")]
        kind, why, keep = check_day(d, list(g["ny"]), *a)
        if kind is None: dropped.append((str(d), why)); continue
        o, h, l, c, v = [x[keep] for x in a]
        ok, why = gap_ok(h.max(), l.min(), c[-1], daily.get(d))
        if not ok: dropped.append((str(d), why)); continue
        pad = lambda x: np.r_[x, np.full(FULL - len(x), np.nan)]
        days.append(d); kinds.append(kind); O.append(pad(o)); H.append(pad(h)); L.append(pad(l)); C.append(pad(c)); V.append(pad(v))
    # weekdays inside the span that are not holidays and have no data at all
    have = set(df["d"].unique()); first, lastd = min(have), max(have); x = first
    while x <= lastd:
        if x.weekday() < 5 and x not in HOL and x not in have: dropped.append((str(x), "no one-minute data"))
        x += dt.timedelta(1)
    D = dict(days=days, kind=np.array([k == "early" for k in kinds]), O=np.array(O), H=np.array(H), L=np.array(L), C=np.array(C), V=np.array(V))
    D["last"] = np.where(D["kind"], HALF - 1, FULL - 1)
    D["inputs"] = {os.path.relpath(f, BARS): sha(f) for f in files + [dfile]}
    return D, sorted(dropped)

# ------------------------------------------------------------------ derived series
def vwap(D):
    tp = (D["H"] + D["L"] + D["C"]) / 3; v = np.nan_to_num(D["V"]); pv = np.cumsum(np.nan_to_num(tp) * v, 1); cv = np.cumsum(v, 1)
    out = np.where(cv > 0, pv / np.where(cv > 0, cv, 1), D["C"]); out[np.isnan(D["C"])] = np.nan; return out

def last_close(D): return D["C"][np.arange(len(D["days"])), D["last"]]
def prev_close(D): lc = last_close(D); return np.r_[np.nan, lc[:-1]]

def sigma(D, lookback=14):
    """Average size of the move from the open to the close of each minute over the previous `lookback` used days that have that minute."""
    mv = np.abs(D["C"] / D["O"][:, :1] - 1); n, T = mv.shape; out = np.full((n, T), np.nan)
    for t in range(T):
        col = mv[:, t]; idx = np.flatnonzero(~np.isnan(col))
        if len(idx) <= lookback: continue
        cs = np.r_[0, np.cumsum(col[idx])]; rm = (cs[lookback:-1] - cs[:-lookback - 1]) / lookback   # mean of the previous lookback values
        out[idx[lookback:], t] = rm
    return out

# ------------------------------------------------------------------ rules: each returns trades as arrays
# day: the day the trade ends on; e_min, e_kind: entry minute and kind ('o' open of that minute, 'c' close of that minute);
# x_min, x_kind: exit minute and kind ('o', 'c' or 's' stop price); stop: stop price (nan if none). N5 entries are on the day before.
KC = {"o": 0, "c": 1, "s": 2}   # kinds are stored as codes
def T(day, em, ek, xm, xk, stop=None, overnight=False):
    n = len(day); code = lambda k: np.array([KC[x] for x in k], int) if len(k) else np.zeros(0, int)
    return dict(day=np.asarray(day, int), em=np.asarray(em, int), ek=code(ek), xm=np.asarray(xm, int), xk=code(xk),
                              stop=np.full(n, np.nan) if stop is None else np.asarray(stop, float), overnight=overnight)

def r_n1(D, lag=0):
    O, L, C = D["O"], D["L"], D["C"]; n = len(O); e = 5 + lag
    stop = L[:, :5].min(1); go = (C[:, 4] > O[:, 0]) & (O[:, e] > stop)
    day, em, ek, xm, xk, sp = [], [], [], [], [], []
    for d in np.flatnonzero(go):
        lst = D["last"][d]; hit = np.flatnonzero(L[d, e:lst + 1] <= stop[d])
        if len(hit):
            m = e + hit[0]; k = "o" if O[d, m] <= stop[d] else "s"
            day.append(d); em.append(e); ek.append("o"); xm.append(m); xk.append(k); sp.append(stop[d])
        else:
            day.append(d); em.append(e); ek.append("o"); xm.append(lst); xk.append("c"); sp.append(stop[d])
    return T(day, em, ek, xm, xk, sp)

def r_n2(D, lag=0, SG=None, VW=None):
    O, C = D["O"], D["C"]; n = len(O); pc = prev_close(D); base = np.maximum(O[:, 0], pc)
    SG = sigma(D) if SG is None else SG; VW = vwap(D) if VW is None else VW
    day, em, xm = [], [], []
    for d in range(n):
        if np.isnan(pc[d]): continue
        lst = D["last"][d]; checks = [t for t in range(29, 360, 30) if t + 1 + lag <= lst]; pos = False; ent = None
        for t in checks:
            s = SG[d, t]
            if np.isnan(s): continue
            ub = base[d] * (1 + s)
            if not pos and C[d, t] > ub: pos = True; ent = t + 1 + lag
            elif pos and (C[d, t] < ub or C[d, t] < VW[d, t]):
                pos = False; day.append(d); em.append(ent); xm.append(t + 1 + lag)
        if pos: day.append(d); em.append(ent); xm.append(-1)
    xm = np.array(xm, int); day = np.array(day, int); xk = np.where(xm < 0, "c", "o"); xm = np.where(xm < 0, D["last"][day] if len(day) else 0, xm)
    return T(day, em, ["o"] * len(day), xm, xk)

def r_lasthalf(D, t_sig, lag=0):
    pc = prev_close(D); full = ~D["kind"]; go = full & ~np.isnan(pc) & (D["C"][:, t_sig] > pc)
    d = np.flatnonzero(go); return T(d, np.full(len(d), 360 + lag), ["o"] * len(d), np.full(len(d), FULL - 1), ["c"] * len(d))

def r_n4(D, lag=0, VW=None):
    C = D["C"]; VW = vwap(D) if VW is None else VW; n = len(C); day, em, xm, xk = [], [], [], []
    for d in range(n):
        lst = D["last"][d]; sig = np.zeros(FULL, bool); ms = np.arange(4, lst)   # decisions on closes 09:34 to the minute before the last
        sig[ms] = C[d, ms] > VW[d, ms]
        pos = np.zeros(FULL + 1, bool); tgt = ms + 1 + lag; okm = tgt <= lst; pos[tgt[okm]] = sig[ms[okm]]
        pos = pos[:lst + 1]; ch = np.diff(np.r_[0, pos.astype(int), 0])
        starts = np.flatnonzero(ch == 1); ends = np.flatnonzero(ch == -1)   # held minutes starts..ends-1
        for s0, e0 in zip(starts, ends):
            day.append(d); em.append(s0)
            if e0 <= lst: xm.append(e0); xk.append("o")
            else: xm.append(lst); xk.append("c")
    return T(day, em, ["o"] * len(day), xm, xk)

def r_n5(D, lag=0):
    n = len(D["days"]); d = np.arange(1, n); return T(d, D["last"][d - 1], ["c"] * len(d), np.full(len(d), 1 + lag), ["o"] * len(d), overnight=True)

def r_n6(D, lag=0, mask=None):
    d = np.arange(len(D["days"])) if mask is None else np.flatnonzero(mask)
    return T(d, np.full(len(d), 1 + lag), ["o"] * len(d), D["last"][d], ["c"] * len(d))

def coin(D): return np.random.default_rng(SEED).random(len(D["days"])) < 0.5

def all_rules(D, lag=0):
    SG = sigma(D); VW = vwap(D)
    return {"N1": r_n1(D, lag), "N2": r_n2(D, lag, SG, VW), "N3": r_lasthalf(D, 29, lag), "N4": r_n4(D, lag, VW), "N5": r_n5(D, lag),
            "N6": r_n6(D, lag), "N7": r_n6(D, lag, coin(D)), "N8": r_lasthalf(D, 359, lag)}

# ------------------------------------------------------------------ pricing
def px(D, day, m, kind, stop):
    out = np.where(kind == 0, D["O"][day, m], D["C"][day, m])
    return np.where(kind == 2, stop, out)

def gross_log(D, tr, perm=None):
    """Log gross return of each trade. perm: map from day to the day whose bars price it (shuffles). A stop becomes the close."""
    day = tr["day"]
    if perm is None:
        if tr["overnight"]: ep = D["C"][day - 1, tr["em"]]
        else: ep = px(D, day, tr["em"], tr["ek"], tr["stop"])
        xp = px(D, day, tr["xm"], tr["xk"], tr["stop"])
    else:
        nd = perm[day]; xk = np.where(tr["xk"] == 2, 1, tr["xk"])
        ep = px(D, nd, tr["em"], tr["ek"], tr["stop"]); xp = px(D, nd, tr["xm"], xk, tr["stop"])
    return np.log(xp / ep)

def daily(D, tr, cost, glog=None, extra_stop_cost=False):
    k = cost / 1e4; g = gross_log(D, tr) if glog is None else glog
    lr = g + math.log((1 - k) / (1 + k))
    if extra_stop_cost: lr = lr + np.where(tr["xk"] == 2, math.log(1 - k), 0.0)
    return np.expm1(np.bincount(tr["day"], weights=lr, minlength=len(D["days"])))

def hold_daily(D, cost, s):
    lc = last_close(D); r = np.r_[0.0, lc[1:] / lc[:-1] - 1]; r[:s] = 0.0; r[s] = (1 + r[s]) / (1 + cost / 1e4) - 1; return r

# ------------------------------------------------------------------ measures
def met(r): return R.metrics(np.r_[1.0, np.cumprod(1 + r)], PPY)
def sharpe_ann(r): s = R.sharpe_pp(r); return s * math.sqrt(PPY)

def slices(days, dev_only):
    d = np.array(days, dtype="datetime64[D]"); out = {"dev": d <= np.datetime64(DT["dev_end"])}
    if not dev_only:
        out["held"] = (d >= np.datetime64(DT["held_start"])) & (d <= np.datetime64(DT["held_end"]))
        out["post"] = (d >= np.datetime64(DT["post_start"])) & (d <= np.datetime64(DT["last_day"]))
    out["all"] = d <= np.datetime64(DT["last_day"]); return out

def prior_sharpes():
    """Yearly whole-sample Sharpe ratios of every stored row of the counted trials (mark 3 spread, plan 07). Reads stored outputs only."""
    xs = []; v = json.load(open(os.path.join(HERE, "results_v2.json")))
    for ven, A in v["R01"]["venues"].items():
        for a in ("BTCUSD", "ETHUSD"): xs += [r["all"]["sharpe"] for r in A[a]["rules"].values()]
    for ven, A in v["R03"]["venues"].items():
        for a in ("BTCUSD", "ETHUSD"): xs += [r["all"]["sharpe"] for r in A[a]["rules"].values()]
    for f in ("results_05.json", "results_05b.json"):
        for A in json.load(open(os.path.join(HERE, f)))["costs"].values(): xs += [r["all"]["sharpe"] for r in A["rules"].values()]
    for A in json.load(open(os.path.join(HERE, "results_04.json")))["venues"].values():
        xs += [r["sharpe_per_period_all"] * math.sqrt(365) for r in A["rules"].values()]
    return [float(x) for x in xs if x is not None and np.isfinite(x)]

def best10_share(r):
    lr = np.log1p(r); tot = lr.sum()
    return float(np.sort(lr)[-10:].sum() / tot) if tot > 0 else None

def yearly(days, r):
    y = np.array([d.year for d in days]); return {int(k): float(np.prod(1 + r[y == k]) - 1) for k in np.unique(y)}

# ------------------------------------------------------------------ one fund
def run_symbol(sym, end, dev_only):
    D, dropped = load(sym, end); n = len(D["days"]); s = WARM
    TR = all_rules(D); TR1 = all_rules(D, lag=1); G = {k: gross_log(D, t) for k, t in TR.items()}
    res_mask = np.arange(n) >= s; days = [d for d in D["days"]]; SL = slices(days, dev_only)
    SL = {k: m & res_mask for k, m in SL.items()}
    # check on the prices: N6 and N5 together equal holding before costs
    comb = (1 + daily(D, TR["N5"], 0, G["N5"])) * (1 + daily(D, TR["N6"], 0, G["N6"])) - 1; h0 = hold_daily(D, 0, s)
    chk = float(np.max(np.abs(np.log1p(comb[res_mask][1:]) - np.log1p(h0[res_mask][1:]))))
    assert chk < 1e-6, f"N5 plus N6 does not equal holding on {sym}: {chk}"
    perm_kind = D["kind"][res_mask]; res_idx = np.flatnonzero(res_mask)
    out = dict(symbol=sym, trial_ids={r: FIRST_ID[sym] + i for i, r in enumerate(RULES)}, used_days=int(n), result_days=int(res_mask.sum()),
               first_result_day=str(D["days"][s]), last_day=str(D["days"][-1]), early_close_days_used=int(D["kind"].sum()),
               days_not_used=len(dropped), days_not_used_by_reason={}, days_not_used_list=dropped, n5_plus_n6_vs_hold_max_log_gap=chk,
               slice_days={k: int(m.sum()) for k, m in SL.items()}, inputs=D["inputs"], costs={})
    for _, why in dropped: out["days_not_used_by_reason"][why] = out["days_not_used_by_reason"].get(why, 0) + 1
    # break-even per side, on the whole sample (mark 2 against holding; also against zero)
    out["breakeven"] = {}
    for r in RULES:
        f_h = lambda c, r=r: sharpe_ann(daily(D, TR[r], c, G[r])[SL["all"]]) - sharpe_ann(hold_daily(D, c, s)[SL["all"]])
        f_z = lambda c, r=r: float(np.mean(daily(D, TR[r], c, G[r])[SL["all"]]))
        bh, bz = R.breakeven(f_h), R.breakeven(f_z)
        out["breakeven"][r] = dict(vs_hold_per_side=bh, vs_zero_per_side=bz, vs_hold_round_trip_bps=2 * bh["bps"], vs_zero_round_trip_bps=2 * bz["bps"])
    out["prior_sharpe_rows"] = len(prior_sharpes()); keep_all = {}
    for lab, c in COSTS.items():
        X = {r: daily(D, TR[r], c, G[r]) for r in RULES}; H = hold_daily(D, c, s)
        co = dict(cost_bps_per_side=c, judged=lab in JUDGED, hold={k: met(H[m]) for k, m in SL.items()}, hold_yearly=yearly(np.array(days)[res_mask], H[res_mask]), rules={})
        ours = [sharpe_ann(X[r][SL["all"]]) for r in RULES]
        co["sharpe_ann_whole"] = dict(zip(RULES, ours)); sd_ours = float(np.std(ours, ddof=1)) / math.sqrt(PPY)
        co["spread_per_day_this_fund_only"] = sd_ours
        # mark 4 over fixed start dates
        starts = DT["pbo_starts_spy"] if sym == "SPY" else DT["pbo_starts_qqq"]; pb = {}
        for st in starts:
            m = SL["all"] & (np.array(days, dtype="datetime64[D]") >= np.datetime64(st))
            if m.sum() >= 2 * BLOCKS: pb[st] = R.pbo_cscv(np.column_stack([X[r][m] for r in RULES]), BLOCKS, "earliest")
        co["pbo_by_start"] = pb; co["pbo_largest"] = max(v["pbo"] for v in pb.values()) if pb else float("nan")
        for r in RULES:
            x = X[r]; tr = TR[r]
            rr = {k: met(x[m]) for k, m in SL.items()}
            in_res = res_mask[tr["day"]]
            rr["trades_whole"] = int(in_res.sum()); rr["days_with_a_trade_whole"] = int(len(np.unique(tr["day"][in_res])))
            rr["share_of_days_with_a_trade"] = rr["days_with_a_trade_whole"] / int(res_mask.sum())
            rr["yearly"] = yearly(np.array(days)[res_mask], x[res_mask]); rr["best10_share_of_log_growth"] = best10_share(x[SL["all"]])
            rr["dsr_spread_this_fund_only"] = R.deflated_sharpe(x[SL["all"]], N_TRIALS, sd_ours)[0]
            keep_all.setdefault(lab, {})[r] = x[SL["all"]]   # marks 3 and the pass are set in main, once both funds are in (plan 07: spread over these 16)
            rr["lag1"] = {k: met(daily(D, TR1[r], c)[m]) for k, m in SL.items() if k in ("held", "all", "dev")}
            if r == "N1": rr["stop_extra_cost"] = {k: met(daily(D, tr, c, G[r], extra_stop_cost=True)[m]) for k, m in SL.items() if k in ("held", "all", "dev")}
            if lab in JUDGED:
                rng = np.random.default_rng(SEED); real = R.sharpe_pp(x[SL["all"]]); cnt = 0
                for i in range(NSHUF):
                    if r == "N5": nx = x   # every night is traded, so every draw equals the rule (plan 07, mark 5)
                    else:
                        perm = np.arange(n)
                        for kd in (False, True):
                            ids = res_idx[perm_kind == kd]; perm[ids] = rng.permutation(ids)
                        nx = daily(D, tr, c, gross_log(D, tr, perm))   # warm-up days map to themselves and are outside the results
                    cnt += R.sharpe_pp(nx[SL["all"]]) < real
                rr["shuffle_pct"] = cnt / NSHUF
                hold_key = "held" if "held" in SL else "dev"
                rr["hold_key"] = hold_key
                rr["dd_ratio_vs_hold"] = abs(rr[hold_key]["maxdd"]) / abs(co["hold"][hold_key]["maxdd"]) if co["hold"][hold_key]["maxdd"] else None
            co["rules"][r] = rr
        out["costs"][lab] = co
        print(sym, lab, "done", flush=True)
    out["_returns_whole"] = keep_all
    return out

def finish(sym_outs):
    """Mark 3 needs the spread over all counted trials, which includes the 16 of this plan (both funds), so it is set here."""
    prior = prior_sharpes()
    for lab in COSTS:
        ours16 = [v for o in sym_outs for v in o["costs"][lab]["sharpe_ann_whole"].values()]
        sd_all = float(np.std(prior + ours16, ddof=1)) / math.sqrt(PPY); sd_16 = float(np.std(ours16, ddof=1)) / math.sqrt(PPY)
        for o in sym_outs:
            co = o["costs"][lab]; co["spread_per_day_all_counted"] = sd_all; co["spread_per_day_these_16"] = sd_16
            for r in RULES:
                rr = co["rules"][r]; x = o["_returns_whole"][lab][r]
                rr["dsr"] = R.deflated_sharpe(x, N_TRIALS, sd_all)[0]; rr["dsr_spread_these_16_only"] = R.deflated_sharpe(x, N_TRIALS, sd_16)[0]
                if lab in JUDGED:
                    hk = rr["hold_key"]
                    rr["marks"] = R.five_marks(rr[hk], co["hold"][hk], o["breakeven"][r]["vs_hold_per_side"], co["cost_bps_per_side"], rr["dsr"], co["pbo_largest"], rr["shuffle_pct"])
    for o in sym_outs:
        o.pop("_returns_whole")
        o["passed_both_judged_costs"] = {r: all(o["costs"][l]["rules"][r]["marks"]["passed"] for l in JUDGED) for r in RULES}

# ------------------------------------------------------------------ fixtures
def fixtures():
    ok = True
    def check(name, cond, detail=""):
        nonlocal ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name, detail)
    NY = "America/New_York"
    def day_ts(date, n=FULL, start="09:30"):
        return list(pd.date_range(f"{date} {start}", periods=n, freq="1min", tz=NY))
    def bars(n, p=100.0):
        o = np.full(n, p); return o, o + 0.1, o - 0.1, o.copy(), np.full(n, 10.0)
    full = dt.date(2019, 3, 5); summer = dt.date(2019, 7, 9); early = dt.date(2019, 11, 29)
    k, _, _ = check_day(full, day_ts(full), *bars(FULL)); check("C1 full winter day passes", k == "full")
    ts = list(pd.date_range("2019-07-09 13:30", periods=FULL, freq="1min", tz="UTC").tz_convert(NY))
    k, _, _ = check_day(summer, ts, *bars(FULL)); check("C2 summer day from UTC 13:30 is 09:30 New York and passes", k == "full")
    ts = list(pd.date_range("2019-03-05 14:30", periods=FULL, freq="1min", tz="UTC").tz_convert(NY))
    k, _, _ = check_day(full, ts, *bars(FULL)); check("C3 winter day from UTC 14:30 is 09:30 New York and passes", k == "full")
    ts = day_ts(full); del ts[100]; k, w, _ = check_day(full, ts, *bars(FULL - 1)); check("C4 missing minute fails", k is None, w)
    ts = day_ts(full); ts[101] = ts[100]; k, w, _ = check_day(full, ts, *bars(FULL)); check("C5 repeated minute fails", k is None, w)
    ts = day_ts(full) + [pd.Timestamp(f"{full} 12:00:30", tz=NY)]; k, w, _ = check_day(full, ts, *bars(FULL + 1)); check("C6 timestamp off the whole minute fails", k is None, w)
    ts = day_ts(full) + [pd.Timestamp(f"{full} 16:00", tz=NY)]; k, w, _ = check_day(full, ts, *bars(FULL + 1)); check("C7 bar at 16:00 fails", k is None, w)
    sat = dt.date(2019, 3, 9); k, w, _ = check_day(sat, day_ts(sat), *bars(FULL)); check("C8 weekend fails", k is None and w == "weekend")
    hol = dt.date(2019, 12, 25); k, w, _ = check_day(hol, day_ts(hol), *bars(FULL)); check("C9 holiday fails", k is None and w == "holiday")
    ts = day_ts(early, HALF + 15); k, w, keep = check_day(early, ts, *bars(HALF + 15))
    kept = [t for t, x in zip(ts, keep) if x] if keep is not None else []
    check("C10 early close with bars after 12:59 passes once they are dropped and ends at 12:59", k == "early" and len(kept) == HALF and kept[-1].strftime("%H:%M") == "12:59")
    k, w, _ = check_day(early, day_ts(early), *bars(FULL)); check("C11 early close day with a full session of bars keeps 210", k == "early")
    k, w, _ = check_day(full, day_ts(full, HALF), *bars(HALF)); check("C12 a 210-bar day that is not an early close fails", k is None, w)
    okg, w = gap_ok(100.3, 99.0, 100.0, (100.0, 99.0, 100.0)); check("C13 one-minute high 30 bps above daily high fails the day", not okg and GAP < 30, w)
    okg, w = gap_ok(100.2, 99.0, 100.0, (100.0, 99.0, 100.0)); check("C14 a gap of 20 bps is inside the band", okg and GAP >= 20)
    # N1 hand-worked days
    def mk(nd):
        O = np.full((nd, FULL), 100.0); H = O + 0.05; L = O - 0.05; C = O.copy(); V = np.ones((nd, FULL))
        return dict(days=[dt.date(2019, 1, 2) + dt.timedelta(i) for i in range(nd)], kind=np.zeros(nd, bool), O=O, H=H, L=L, C=C, V=V, last=np.full(nd, FULL - 1))
    D = mk(3)
    for d in range(3): D["C"][d, 4] = 100.4; D["L"][d, 2] = 99.5; D["O"][d, 5] = 100.4; D["H"][d, 5] = 100.45; D["L"][d, 5] = 100.3
    D["O"][0, 6:] = 100.6; D["H"][0, 6:] = 100.7; D["L"][0, 6:] = 100.5; D["C"][0, 6:] = 100.6
    D["O"][0, 50] = 100.0; D["L"][0, 50] = 99.4; D["C"][0, 50] = 99.6          # day 0: bar opens above the stop and trades through it
    D["O"][1, 6:] = 100.6; D["H"][1, 6:] = 100.7; D["L"][1, 6:] = 100.5; D["C"][1, 6:] = 100.6
    D["O"][1, 80] = 99.0; D["L"][1, 80] = 98.9; D["H"][1, 80] = 99.1; D["C"][1, 80] = 99.0   # day 1: opens below the stop
    D["O"][2, 6:] = 101.0; D["H"][2, 6:] = 101.1; D["L"][2, 6:] = 100.9; D["C"][2, 6:] = 101.0; D["C"][2, -1] = 102.0   # day 2: to the close
    tr = r_n1(D); k = 2.0 / 1e4; r = daily(D, tr, 2.0)
    e0 = 99.5 / 100.4 * (1 - k) / (1 + k) - 1; e1 = 99.0 / 100.4 * (1 - k) / (1 + k) - 1; e2 = 102.0 / 100.4 * (1 - k) / (1 + k) - 1
    check("N1a stop hit inside a bar fills at the stop", abs(r[0] - e0) < 1e-12 and tr["xk"][0] == 2 and tr["xm"][0] == 50, f"{r[0]:.6f} expected {e0:.6f}")
    check("N1b gap through the stop fills at the bar's open", abs(r[1] - e1) < 1e-12 and tr["xk"][1] == 0, f"{r[1]:.6f} expected {e1:.6f}")
    check("N1c no stop: sold at the session's close", abs(r[2] - e2) < 1e-12 and tr["xk"][2] == 1, f"{r[2]:.6f} expected {e2:.6f}")
    D["C"][2, 4] = 99.9; check("N1d first bar down: no trade", 2 not in set(r_n1(D)["day"]))
    # N5 plus N6 equal holding on a synthetic history with an early close
    rg = np.random.default_rng(3); nd = 40; Dz = mk(nd); p = 100 * np.exp(np.cumsum(rg.normal(0, 1e-3, (nd, FULL)), 1) + np.cumsum(rg.normal(0, 0.01, nd))[:, None])
    Dz["O"] = p * np.exp(rg.normal(0, 2e-4, p.shape)); Dz["C"] = p; Dz["H"] = np.maximum(Dz["O"], p) + 0.01; Dz["L"] = np.minimum(Dz["O"], p) - 0.01
    Dz["kind"][10] = True; Dz["last"][10] = HALF - 1
    for a in ("O", "H", "L", "C", "V"): Dz[a][10, HALF:] = np.nan
    comb = (1 + daily(Dz, r_n5(Dz), 0)) * (1 + daily(Dz, r_n6(Dz), 0)) - 1; h0 = hold_daily(Dz, 0, 0)
    check("H1 N5 and N6 together equal holding before costs", np.max(np.abs(comb[1:] - h0[1:])) < 1e-12)
    TRz = all_rules(Dz); check("H2 no rule trades past the last minute of an early close", all((t["xm"][t["day"] == 10] <= HALF - 1).all() for t in TRz.values()))
    check("H3 N3 and N8 do not trade on an early close", 10 not in set(TRz["N3"]["day"]) and 10 not in set(TRz["N8"]["day"]))
    # VWAP and N4 timing on a hand-worked day
    Dv = mk(1); Dv["C"][0, 10] = 101; Dv["H"][0, 10] = 101.05
    trv = r_n4(Dv); check("N4a above VWAP on the 10th minute's close buys at the 11th minute's open, sells the minute after", list(trv["em"]) == [11] and list(trv["xm"]) == [12])
    # shuffle keeps the trades and their minutes
    perm = np.random.default_rng(1).permutation(nd); perm[10] = 10
    check("S1 a shuffle draw keeps the number of trades", len(gross_log(Dz, TRz["N4"], perm)) == len(TRz["N4"]["day"]))
    # peeking is visible: a rule that knows the day's close beats N6 by far
    peekd = np.flatnonzero(Dz["C"][:, -1] > Dz["O"][:, 1]); pk = daily(Dz, r_n6(Dz, mask=np.isin(np.arange(nd), peekd)), 0)
    check("P1 peeking is visible", np.prod(1 + pk) > np.prod(1 + daily(Dz, r_n6(Dz), 0)) * 1.05)
    return ok

def git_info():
    g = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, cwd=HERE).stdout.strip()
    return dict(commit=g("rev-parse", "HEAD"), code_changed_since_commit=bool(g("status", "--porcelain", "run_07.py", "rig2.py")))

if __name__ == "__main__":
    mode = (sys.argv[1:] or [""])[0]
    if mode not in ("--fixtures", "--dev", "--full"): raise SystemExit(__doc__)
    if subprocess.run([sys.executable, "fixtures2.py"], capture_output=True, cwd=HERE).returncode != 0: raise SystemExit("fixtures2.py failed; nothing was run")
    if not fixtures(): raise SystemExit("checks failed; nothing was run")
    if mode == "--fixtures": raise SystemExit(0)
    dev = mode == "--dev"; end = DT["dev_end"] if dev else DT["last_day"]
    out = dict(plan="PREREG_07_intraday_spy_qqq.md", command="python3 run_07.py " + mode, run_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
               git=git_info(), price_source="one-minute and daily bars from the workspace's own price lookup, collected 2026-11-25; dividend and split adjustment UNKNOWN; calendar from memory",
               thresholds=R.thresholds_used(), config={k: R.th(k) for k in ("replay_07_costs", "replay_07_data", "replay_07_dates", "replay_07_statistics", "cost_model_bps_per_side_liquid_etf", "intraday_trend_max_round_trip_bps")},
               costs=COSTS, judged=list(JUDGED), n_trials=N_TRIALS, shuffles=NSHUF, seed=SEED, dev_only=dev, symbols={})
    import multiprocessing as mp
    with mp.get_context("fork").Pool(2) as pool:
        outs = pool.starmap(run_symbol, [(s, end, dev) for s in SYMS])
    finish(outs)
    for o in outs: out["symbols"][o["symbol"]] = o
    path = "/tmp/results_07_dev.json" if dev else os.path.join(HERE, "results_07.json")
    json.dump(out, open(path, "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)); print("wrote", path)
