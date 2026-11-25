"""Rerun of replay 01, cross-check X2, sensitivity S2, the X2 diagnostic and replay 03 with the audit fixes.
Plan: AMENDMENT_2026-11-25_audit_fixes.md. Writes results_v2.json. Usage: python3 run_v2.py [R01 X2 S2 DIAG R03]"""
import numpy as np, pandas as pd, json, sys, subprocess, os, math
from multiprocessing import Pool
import rig2 as R
from rules import RULES
import common_03 as c3
K = os.environ.get("KRAKEN_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kraken"))
BIN = [r for r in RULES if r not in ("P1", "P2")]
NSHUF = 1000

# ------------------------------------------------------------------ data
def daily(src, a):
    f = f"data/bitstamp_{a}.csv" if src == "Bitstamp" else f"data/krakenfull_{a}.csv"
    d = pd.read_csv(f, parse_dates=["date"]).set_index("date"); d = d[d.index <= "2026-11-24"]; R.check_bars(d, "1D"); return d
def hourly_raw(src, a):
    if src == "Bitstamp":
        h = pd.read_csv(f"data/bitstamp_{a}_1h.csv")
    else:
        h = pd.read_csv(f"{K}/full_{'XBTUSD' if a == 'BTCUSD' else a}_60.csv", header=None, names=["ts", "open", "high", "low", "close", "volume", "trades"])
    h.index = pd.to_datetime(h.ts, unit="s"); h = h[~h.index.duplicated()].sort_index(); return h[h.index <= "2026-11-24 23:00"]
def late_open(src, a, idx, dopen):
    """Open of the venue's own 01:00 UTC bar, or the next traded hour that day. Days after the hourly file ends
    use the daily open and are counted."""
    h = hourly_raw(src, a); h = h[(h.volume > 0) & (h.index.hour >= 1)]; g = h.groupby(h.index.normalize()).open.first()
    o1 = g.reindex(idx); last = h.index[-1].normalize(); after = idx > last
    can = o1.notna().values | after; o1 = o1.where(~pd.Series(after, index=idx), dopen)
    return o1.fillna(dopen).values, can, int(after.sum()), int((~can).sum())

# ------------------------------------------------------------------ one daily replay at one venue
def venue_job(args):
    src, starts, v, fee = args; c = fee + R.SLIP; out = {}; Rr = {}; port = []
    for a in ["BTCUSD", "ETHUSD"]:
        d = daily(src, a); m = d.index >= starts[a]; dd = d[m]; idx = dd.index
        o = dd.open.values; cl = dd.close.values; cf = (dd.volume.values > 0)
        o1, cf1, n_after, n_nofill = late_open(src, a, idx, dd.open)
        hb = R.with_base(R.simulate(o, cl, np.ones(len(dd)), c, can_fill=cf)[0], idx)
        A = {"hold": {k: R.metrics(R.cut(hb, lo, hi).values) for k, (lo, hi) in R.SL.items()}, "rules": {},
             "bars": int(len(dd)), "bars_that_cannot_fill": int((~cf).sum()), "late_fill_days_using_daily_open": n_after, "late_fill_days_no_traded_hour": n_nofill}
        rb = R.rets(hb.values); T = {}
        for r in RULES:
            t = np.nan_to_num(RULES[r](d.close)[m].values, nan=0.0); T[r] = t
            eq, wt, tr = R.simulate(o, cl, t, c, can_fill=cf); ep = R.with_base(eq, idx)
            eq1, wt1, tr1 = R.simulate(o1, cl, t, c, can_fill=cf1); ep1 = R.with_base(eq1, idx)
            waited = int(((np.r_[0, np.abs(np.diff(np.r_[0.0, t[:-1]]))] > 0)[:len(t)] & ~cf).sum())
            rr = {k: dict(R.metrics(R.cut(ep, lo, hi).values), **R.activity(eq, wt, tr, idx, lo, hi)) for k, (lo, hi) in R.SL.items()}
            rr["late"] = {k: R.metrics(R.cut(ep1, *R.SL[k]).values) for k in ("held", "all")}
            rr["orders_that_waited"] = waited; rr["in_position_at_end"] = bool(wt[-1] > 1e-6)
            A["rules"][r] = rr; Rr[(a, r)] = R.rets(ep.values)
        A["_T"] = T; A["_o"] = o; A["_c"] = cl; A["_cf"] = cf; A["_rb"] = rb; out[a] = A
    # portfolios, half each, from 2018-03-05
    for r in ["P1", "P2"]:
        es = []; hs = []
        for a in ["BTCUSD", "ETHUSD"]:
            d = daily(src, a); m = d.index >= "2018-03-05"; dd = d[m]; t = np.nan_to_num(RULES[r](d.close)[m].values, nan=0.0); cf = dd.volume.values > 0
            es.append(R.with_base(R.simulate(dd.open.values, dd.close.values, t, c, start_cash=0.5, can_fill=cf)[0], dd.index, 0.5))
            hs.append(R.with_base(R.simulate(dd.open.values, dd.close.values, np.ones(len(dd)), c, start_cash=0.5, can_fill=cf)[0], dd.index, 0.5))
        pe = es[0] + es[1]; ph = hs[0] + hs[1]; port.append(R.rets(pe.values))
        out.setdefault("port", {})[r] = {k: {"rule": R.metrics(R.cut(pe, lo, hi).values), "hold": R.metrics(R.cut(ph, lo, hi).values)} for k, (lo, hi) in R.SL.items()}
    allr = list(Rr.values()) + port; sd = float(np.std([R.sharpe_pp(x) for x in allr], ddof=1)); out["trial_sharpe_std_per_period"] = sd; out["n_trials"] = len(allr)
    for i, r in enumerate(["P1", "P2"]): out["port"][r]["dsr"] = R.deflated_sharpe(port[i], 20, sd)[0]
    for a in ["BTCUSD", "ETHUSD"]:
        A = out[a]; M = np.column_stack([Rr[(a, r)] for r in RULES])
        A["pbo"] = R.pbo_cscv(M, 16, "earliest"); A["pbo_drop_latest"] = R.pbo_cscv(M, 16, "latest")
        o, cl, cf = A["_o"], A["_c"], A["_cf"]
        for r in RULES:
            rng = np.random.default_rng(7); x = Rr[(a, r)]; s_real = R.sharpe_pp(x); cnt = 0; sides = []; wts = []
            for i in range(NSHUF):
                if r in BIN:
                    eq, held = R.sim_fast(o, cl, R.null_binary(A["_T"][r], rng), c, can_fill=cf); sides.append(int((np.diff(held) != 0).sum())); wts.append(float(held.mean()))
                else:
                    eq, wt, tr = R.simulate(o, cl, R.null_circular(A["_T"][r], rng), c, can_fill=cf); sides.append(int((tr > R.DUST * np.r_[1.0, eq[:-1]]).sum())); wts.append(float(wt.mean()))
                cnt += R.sharpe_pp(R.rets(np.r_[1.0, eq])) < s_real
            rr = A["rules"][r]; dsr, sr0 = R.deflated_sharpe(x, 20, sd)
            rr["dsr"] = dsr; rr["shuffle_pct"] = cnt / NSHUF; rr["shuffle_kind"] = "spells kept, order shuffled within kind" if r in BIN else "whole sequence shifted"
            rr["shuffle_mean_sides"] = float(np.mean(sides)); rr["shuffle_mean_avg_weight"] = float(np.mean(wts))
            rr["boot_sharpe_diff_vs_hold"] = R.block_bootstrap_sharpe_diff(x, A["_rb"])
            h = rr["held"]; hl = rr["late"]["held"]; b = A["hold"]["held"]
            worse = hl if (hl["sharpe"] < h["sharpe"]) else h
            rr["held_worse_of_two_fills"] = dict(sharpe=worse["sharpe"], maxdd=min(h["maxdd"], hl["maxdd"]), which="one hour late" if worse is hl else "base")
            rr["dd_ratio"] = abs(min(h["maxdd"], hl["maxdd"])) / abs(b["maxdd"])
            late_ok = hl["sharpe"] > b["sharpe"] and abs(hl["maxdd"]) <= R.th("replay_max_drop_ratio_vs_hold") * abs(b["maxdd"])
            rr["_m1late"] = bool(late_ok)
    for a in ["BTCUSD", "ETHUSD"]:
        for k in [k for k in out[a] if k.startswith("_")]: del out[a][k]
    print(src, starts, v, "done", flush=True)
    return v, out, {f"{a}|{r}": Rr[(a, r)].tolist() for (a, r) in Rr} | {f"PORT|{r}": port[i].tolist() for i, r in enumerate(["P1", "P2"])}

def breakevens(src, starts):
    be = {}
    for a in ["BTCUSD", "ETHUSD"]:
        d = daily(src, a); m = d.index >= starts[a]; dd = d[m]; o = dd.open.values; cl = dd.close.values; cf = dd.volume.values > 0
        def sh(t, c): return R.metrics(np.r_[1.0, R.simulate(o, cl, t, c, can_fill=cf)[0]])
        for r in RULES:
            t = np.nan_to_num(RULES[r](d.close)[m].values, nan=0.0); hold = np.ones(len(dd))
            be[f"{a}|{r}"] = dict(vs_hold=R.breakeven(lambda c: sh(t, c)["sharpe"] - sh(hold, c)["sharpe"]), zero_growth=R.breakeven(lambda c: sh(t, c)["cagr"]))
    return be

def daily_replay(src, starts, pool):
    be = breakevens(src, starts)
    res = pool.map(venue_job, [(src, starts, v, fee) for v, fee in R.VENUES.items()])
    out = {"source": src, "starts": starts, "venues": {}, "breakeven": be}; rets = {}
    for v, o, rr in res:
        c = R.VENUES[v] + R.SLIP
        for a in ["BTCUSD", "ETHUSD"]:
            for r in RULES:
                x = o[a]["rules"][r]
                x["marks"] = R.five_marks(x["held"], o[a]["hold"]["held"], be[f"{a}|{r}"]["vs_hold"], c, x["dsr"], o[a]["pbo"]["pbo"], x["shuffle_pct"], extra_m1=x.pop("_m1late"))
        out["venues"][v] = o; rets[v] = rr
    return out, rets

# ------------------------------------------------------------------ replay 03
NAMES = ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]
def hourly_setup(a):
    d = c3.load_h(a); R.check_bars(d[["open", "high", "low", "close", "volume"]], "1h")
    bad = d.missing | (d.volume == 0); q = bad.groupby(d.index.year).mean(); first = d.index[0]; s = None
    for y in sorted(q.index):
        s0 = pd.Timestamp(f"{y}-01-01")
        if s0 < first + pd.Timedelta(hours=4800): continue
        if all(q[z] < 0.01 for z in q.index if z >= y): s = s0; break
    if s is None:
        if a != "ETHUSD": raise SystemExit(f"no start date qualifies for {a}")
        s = (first + pd.Timedelta(hours=4800)).ceil("D")
    T = c3.rules_h(d, a); m = d.index >= s; dd = d[m]
    qual = {"start": str(s.date()), "missing_hours_by_year": {int(k): int(v) for k, v in dd.missing.groupby(dd.index.year).sum().items()},
            "zero_volume_hours_by_year": {int(k): int(v) for k, v in ((dd.volume == 0) & ~dd.missing).groupby(dd.index.year).sum().items()}, "hours": int(len(dd))}
    return dict(d=dd, o=dd.open.values, c=dd.close.values, T={k: np.asarray(v, float)[m] for k, v in T.items()}, eod=(dd.index.hour == 23), cf=(~dd.missing & (dd.volume > 0)).values, qual=qual)
_D = {}
def eod_series(x, eq):
    idx = x["d"].index[x["eod"]].normalize(); return pd.Series(np.r_[1.0, eq[x["eod"]]], index=idx.insert(0, idx[0] - pd.Timedelta(days=1)))
def trips(eq, held, idx, lo, hi):
    prev = np.r_[0, held[:-1]]; ent = np.flatnonzero((held == 1) & (prev == 0)); ex = np.flatnonzero((held == 0) & (prev == 1))
    k = min(len(ent), len(ex)); open_end = len(ent) > len(ex); ent = ent[:k]; ex = ex[:k]
    base = np.where(ent > 0, eq[np.maximum(ent - 1, 0)], 1.0); r = eq[ex] / base - 1; t = idx[ent]
    lo_ = pd.Timestamp(lo) if lo else idx[0]; hi_ = pd.Timestamp(hi) + pd.Timedelta(days=1)
    mk = (t >= lo_) & (t < hi_); r = r[mk]; yrs = max(1e-9, (min(hi_, idx[-1] + pd.Timedelta(hours=1)) - max(lo_, idx[0])) / pd.Timedelta(days=365))
    return dict(n=int(len(r)), per_year=float(len(r) / yrs), avg_bps=float(r.mean() * 1e4) if len(r) else 0.0, win=float((r > 0).mean()) if len(r) else 0.0,
                hours=float((ex - ent)[mk].mean()) if len(r) else 0.0, in_position_at_end=bool(open_end))
def r03_venue(args):
    v, fee, old = args; c = fee + R.SLIP; out = {}; Rr = {}; old = [np.array(z) for z in old]
    for a in ["BTCUSD", "ETHUSD"]:
        x = _D[a]; idx = x["d"].index; ones = np.ones(len(idx)); A = {"rules": {}}
        def run(t): eq, held = R.sim_fast(x["o"], x["c"], t, c, can_fill=x["cf"]); return eod_series(x, eq), eq, held
        hb, _, _ = run(ones); A["hold"] = {k: R.metrics(R.cut(hb, lo, hi).values) for k, (lo, hi) in R.SL.items()}
        e, _, _ = run(x["T"]["C1"]); A["C1"] = {k: R.metrics(R.cut(e, lo, hi).values) for k, (lo, hi) in R.SL.items()}
        for n in NAMES:
            e, eqh, held = run(x["T"][n]); Rr[(a, n)] = R.rets(e.values)
            A["rules"][n] = {k: dict(R.metrics(R.cut(e, lo, hi).values), trips=trips(eqh, held, idx, lo, hi)) for k, (lo, hi) in R.SL.items()}
            A["rules"][n]["orders_that_waited"] = int(((np.diff(np.r_[0.0, 0.0, x["T"][n][:-1]]) != 0) & ~x["cf"]).sum())
            A["rules"][n]["share_of_hours_in_position"] = float(held.mean())
        A["pbo"] = R.pbo_cscv(np.column_stack([Rr[(a, n)] for n in NAMES]), 16, "earliest"); A["pbo_drop_latest"] = R.pbo_cscv(np.column_stack([Rr[(a, n)] for n in NAMES]), 16, "latest")
        A["_rb"] = R.rets(hb.values); out[a] = A
    new = list(Rr.values()); assert len(old) + len(new) == 36
    sd = float(np.std([R.sharpe_pp(z) for z in old + new], ddof=1)); out["trial_sharpe_std_per_period"] = sd
    for a in ["BTCUSD", "ETHUSD"]:
        x = _D[a]; A = out[a]
        for n in NAMES:
            r = Rr[(a, n)]; rng = np.random.default_rng(7); s_real = R.sharpe_pp(r); cnt = 0; sides = []
            for i in range(NSHUF):
                eq, held = R.sim_fast(x["o"], x["c"], R.null_binary(x["T"][n], rng), c, can_fill=x["cf"]); sides.append(int((np.diff(held) != 0).sum()))
                cnt += R.sharpe_pp(R.rets(np.r_[1.0, eq[x["eod"]]])) < s_real
            rr = A["rules"][n]; rr["dsr"] = R.deflated_sharpe(r, 36, sd)[0]; rr["shuffle_pct"] = cnt / NSHUF; rr["shuffle_mean_sides"] = float(np.mean(sides))
            rr["boot_sharpe_diff_vs_hold"] = R.block_bootstrap_sharpe_diff(r, A["_rb"]); rr["dd_ratio"] = abs(rr["held"]["maxdd"]) / abs(A["hold"]["held"]["maxdd"])
        del A["_rb"]
    print("R03", v, "done", flush=True); return v, out
def r03_gross(_):
    out = {}
    for a in ["BTCUSD", "ETHUSD"]:
        x = _D[a]; idx = x["d"].index; ones = np.ones(len(idx)); out[a] = {}
        def sh(t, c): return R.metrics(eod_series(x, R.sim_fast(x["o"], x["c"], t, c, can_fill=x["cf"])[0]).values)
        for n in NAMES + ["C1"]:
            t = x["T"][n]; eq, held = R.sim_fast(x["o"], x["c"], t, 0.0, can_fill=x["cf"]); e = eod_series(x, eq)
            out[a][n] = dict(gross={k: R.metrics(R.cut(e, lo, hi).values) for k, (lo, hi) in R.SL.items()}, gross_trips=trips(eq, held, idx, None, "2026-11-24"),
                             vs_hold=R.breakeven(lambda c: sh(t, c)["sharpe"] - sh(ones, c)["sharpe"]), zero_growth=R.breakeven(lambda c: sh(t, c)["cagr"]))
    return out

if __name__ == "__main__":
    if subprocess.run([sys.executable, "fixtures2.py"], capture_output=True).returncode != 0: raise SystemExit("fixtures2.py failed; nothing was run")
    want = sys.argv[1:] or ["R01", "X2", "S2", "DIAG", "R03"]
    path = "results_v2.json"; res = json.load(open(path)) if os.path.exists(path) else {}
    res["thresholds"] = R.thresholds_used(); res["shuffles"] = NSHUF; res["seed"] = 7
    plan = {"R01": ("Bitstamp", {"BTCUSD": "2013-01-01", "ETHUSD": "2018-03-05"}), "X2": ("Kraken", {"BTCUSD": "2014-05-01", "ETHUSD": "2018-03-05"}),
            "S2": ("Kraken", {"BTCUSD": "2014-05-01", "ETHUSD": "2016-03-01"}), "DIAG": ("Bitstamp", {"BTCUSD": "2014-05-01", "ETHUSD": "2018-03-05"})}
    with Pool(4) as pool:
        for k in ["R01", "X2", "S2", "DIAG"]:
            if k not in want: continue
            out, rets = daily_replay(*plan[k], pool); res[k] = out
            if k == "R01": json.dump(rets, open("data/v2_r01_returns.json", "w"))
            json.dump(res, open(path, "w"), indent=1, default=float); print(k, "written", flush=True)
    if "R03" in want:
        old = json.load(open("data/v2_r01_returns.json"))
        for a in ["BTCUSD", "ETHUSD"]: _D[a] = hourly_setup(a)
        import multiprocessing as _mp
        with _mp.get_context("fork").Pool(4) as pool:   # fork, so the workers inherit the hourly data loaded above
            g = pool.apply_async(r03_gross, (0,))
            rr = pool.map(r03_venue, [(v, fee, list(old[v].values())) for v, fee in R.VENUES.items()])
            gross = g.get()
        out = {"quality": {a: _D[a]["qual"] for a in _D}, "venues": {}, "per_rule": gross, "n_trials": 36}
        for v, o in rr:
            c = R.VENUES[v] + R.SLIP
            for a in ["BTCUSD", "ETHUSD"]:
                for n in NAMES:
                    x = o[a]["rules"][n]; x["marks"] = R.five_marks(x["held"], o[a]["hold"]["held"], gross[a][n]["vs_hold"], c, x["dsr"], o[a]["pbo"]["pbo"], x["shuffle_pct"])
            out["venues"][v] = o
        res["R03"] = out; json.dump(res, open(path, "w"), indent=1, default=float); print("R03 written", flush=True)
    print("done")
