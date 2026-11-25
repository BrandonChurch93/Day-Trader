"""Replay 04: slow trend on a wider basket of Kraken USD pairs, dead pairs kept. Plan: PREREG_04_coin_basket_trend.md,
measured per AMENDMENT_2026-11-25_audit_fixes.md. Writes results_04.json. Not the product.
Signals use closes up to and including day t. Orders fill at the open of the next day the pair really traded."""
import numpy as np, pandas as pd, json, sys, os, subprocess, math, time, hashlib
import multiprocessing as mp
import rig2 as R
import basket as BK
from rules import p1 as rule_p1

PPY = 365; NSHUF = 1000; N_TRIALS = 49; SEED = 7; CHUNK = 50; NPROC = 4
SL = {"dev": (None, "2022-12-31"), "held": ("2023-01-01", "2026-06-30"), "post": ("2026-07-01", "2026-09-30"), "all": (None, "2026-09-30")}
RULES = ["K1", "K2", "K3", "K4", "K5"]; BENCH = ["HOLD_BTC", "HOLD_BASKET"]
BIG = ("XBTUSD", "ETHUSD"); SLIP_BIG = 5; SLIP_ALT = 25; SLIP_ALT_SENS = 50; HAIRCUT_SENS = 0.5; DEAD_BEFORE = "2026-09-25"
SLOT = {"K1": 0.10, "K2": 0.20, "K3": 0.05, "K4": 0.50, "K5": 1.0}

READING = [
    "Data: every Kraken file ending USD_1440 except names ending PYUSD or RLUSD (basket.OTHER_QUOTE), cut at 2026-09-30. A day with no row in the raw file is a filled-in day: close carried forward for valuation and signals, open set to nan so nothing fills, dollar volume 0, counted as a day with no trades. Every raw row has volume above zero (checked).",
    "Membership for the month starting on day D uses rows strictly before D (D-1 is the latest). History: at least 200 calendar days from the pair's first bar to D-1 inclusive. Activity: at most 10 days without a raw row among D-90..D-1; days after a pair's last bar count as days without trades. Peg test: sample standard deviation (ddof 1) of the 90 close-to-close returns D-90..D-1 (closes carried forward, also after a last bar), times sqrt(365), below 0.20 is left out. Copies: among pairs that pass the first three tests, ranked by median daily dollar volume over D-90..D-1 (zero on days without trades), a pair is dropped if the correlation of its 90 returns with any higher-ranked pair is above 0.98 (the higher pair is compared whether or not it is itself dropped). Ties in ranking broken by pair name. Top 10 / top 20 are the first 10 / 20 of what remains; if fewer than 20 qualify, K3 holds what qualifies, still one twentieth each.",
    "Start: the first month start at which at least 10 pairs qualify, worked out from the data before any rule is run. The simulation calendar starts the day before (D-1) with all cash, so the equity series starts from the cash put in one bar before the first bar (A02), and the first orders fill at the open of D.",
    "The target set at the close of day t uses the membership of the month containing day t+1, so a pair leaving the basket is sold at the first traded open of the new month.",
    "P1 is rules.p1 (share of close above its 20, 50, 100, 200 day simple average, closes to day t, strictly above), computed on each pair's own filled daily calendar; nan (fewer than 200 closes) is weight 0.",
    "K2: at each month start, the 5 of that month's top 10 with the highest return over the last 90 days (close D-1 over close D-91), ties by name. Slot one fifth each.",
    "K4: XBTUSD and ETHUSD always (no membership test), half each times P1. K5: XBTUSD only, slot = whole account. K5 averages use the last 180 closes with weights 2^(-i/h), i = 0 (latest) .. 179, normalised; a half-life pair is true when short >= long; the weight is set at the close of each UTC Wednesday (weekday 2, bar dated Wednesday) and held otherwise.",
    "Band (A12 reading, agreed with the lead): a pair is traded when |target - weight| > slot/8 with no exception for moves to or from zero, except where the plan says 'is sold': a pair that has left its basket (target 0 because not a member) is sold whatever the band, and a pair whose history ends is sold at its last close. simulate_basket (old engine) is left unchanged; run_04 uses basket.sim_batch (alias simulate_basket2). The number of pair-days on which the old to/from-zero exception would have traded and the new engine did not is reported as old_exception_would_fire_pair_days (a lingering position counts on every day it lingers).",
    "Weights are fractions of the whole account. Buys are sized as target * account - holding with cost on top; if cash runs short every buy that day is scaled down by the same share and cash is set to exactly zero (A04). Sells happen before buys.",
    "Hold bitcoin: XBTUSD bought once with all cash at the first traded open (fee + 5 bps), never traded again. Hold the basket: the month's top 10, one tenth each, rebalanced exactly (band 0) at each month start; each pair's order waits until it trades; never traded between month starts; same per-pair costs.",
    "Cost per side per pair = venue fee + slippage (5 bps XBTUSD and ETHUSD, 25 bps all other pairs).",
    "Slices per the amendment: each slice starts from the last equity value before it; dev from the start; all = start to 2026-09-30. Daily returns over the whole test feed the deflated Sharpe, overfitting estimate, bootstrap and shuffles (as run_v2).",
    "Break-even cost (R.breakeven convention as in run_v2, where c is the full per-side cost of bitcoin): c is added to every pair's slippage excess, so XBTUSD/ETHUSD pay c and every other pair pays c + 20 bps; the benchmark pays the same per-pair costs. Mark 2 compares the break-even with the venue's bitcoin cost (fee + 5 bps), as run_v2 compares with fee + SLIP. Searched vs hold bitcoin (used for marks), vs hold the basket (used for marks_vs_basket) and for zero growth (reported).",
    "Deflated Sharpe: 49 trials; the spread is the sample standard deviation (ddof 1) of the per-day Sharpe of K1..K5 at that venue. Overfitting estimate: R.pbo_cscv on the five rules' daily returns, 16 equal blocks, drop earliest (verdict) and drop latest (reported).",
    "Bootstrap: R.block_bootstrap_sharpe_diff with its defaults (block 30, 2000 draws, seed 7), rule minus benchmark daily returns over the whole test.",
    "Shuffles: 1,000 per rule per venue, rng seed 7 created fresh for each rule at each venue. For each draw, each pair the rule can hold (ever a member for K1..K3; XBTUSD and ETHUSD for K4; XBTUSD for K5), in column order, has its own weight signal (P1, or the Wednesday-held K5 weight) shifted by R.null_circular inside that pair's own rows within the test calendar (first to last bar, clipped to the test); membership, slots and band are left as they were. Pairs with fewer than 61 rows in the test are not shifted (counted). Percentile = share of shuffles whose whole-test daily Sharpe is below the rule's.",
    "Marks: R.five_marks(held slice of rule, held slice of hold bitcoin, break-even vs hold bitcoin, fee + 5, deflated Sharpe, pbo, shuffle percentile), as run_05 calls it (no one-hour-late fill: not in this plan). marks_vs_basket: the same with hold the basket and break-even vs hold the basket. Reported, not the verdict.",
    "Sensitivities (reported, not marked): alt slippage 50 bps; forced exits lose half of the last value (haircut 0.5). Each changes one thing from the base run.",
    "Pairs ever held: pairs with a position above one millionth of the account on any day. Dead: last raw bar before 2026-09-25.",
]

# ------------------------------------------------------------------ setup
D = None
def setup():
    t0 = time.time(); raw = BK.load_raw(); P = BK.big_panel(raw); idx = P["idx"]; names = P["names"]
    ms = [i for i, d in enumerate(idx) if d.day == 1]
    mem = {}; start = None
    for d in ms:
        keep, info = BK.month_members(P, d)
        if start is None and len(keep) >= 10: start = d
        if start is not None: mem[d] = (keep, info)
    assert start is not None, "no month start has 10 qualifying pairs"
    s0 = start - 1; T = len(idx) - s0; dates = idx[s0:]
    # K2 top five by 90-day return among the month's top 10
    top5 = {}
    for d, (keep, _) in mem.items():
        r90 = BK.ret_lookback(P, d, 90); t10 = keep[:10]; top5[d] = sorted(t10, key=lambda j: (-r90[j], names[j]))[:5]
    ucols = sorted(set(j for k, _ in mem.values() for j in k[:20]) | {names.index(b) for b in BIG})
    cn = [names[j] for j in ucols]; N = len(ucols); col = {j: i for i, j in enumerate(ucols)}
    O = P["O"][s0:, ucols]; C = P["C"][s0:, ucols]
    last = P["last"][ucols] - s0; last_day = np.where(P["last"][ucols] >= len(idx) - 1, 10 ** 9, last)
    first = np.maximum(P["first"][ucols] - s0, 0); lastc = np.minimum(last, T - 1)
    # membership per row: target at the close of t uses the month that contains day t+1
    nxt = dates + pd.Timedelta(days=1); mrow = {idx[d].to_period("M"): d for d in mem}
    keys = sorted(mrow); M10 = np.zeros((T, N), bool); M20 = np.zeros((T, N), bool); M5 = np.zeros((T, N), bool)
    for t in range(T):
        p = nxt[t].to_period("M"); p = p if p in mrow else max(k for k in keys if k <= p); d = mrow[p]; k = mem[d][0]
        M10[t, [col[j] for j in k[:10]]] = True; M20[t, [col[j] for j in k[:20]]] = True; M5[t, [col[j] for j in top5[d]]] = True
    # signals on each pair's own calendar, closes to day t
    P1 = np.zeros((T, N))
    for i, p in enumerate(cn):
        P1[:, i] = np.nan_to_num(rule_p1(raw[p].close).reindex(dates).values, nan=0.0)
    btc = cn.index("XBTUSD"); eth = cn.index("ETHUSD")
    bc = raw["XBTUSD"].close; k5 = BK.hold_on_weekday(BK.k5_weight(bc.values), bc.index, 2)
    K5 = np.zeros((T, N)); K5[:, btc] = np.nan_to_num(pd.Series(k5, index=bc.index).reindex(dates).values, nan=0.0)
    big = np.zeros((T, N), bool); big[:, [btc, eth]] = True; onlyb = np.zeros((T, N), bool); onlyb[:, btc] = True
    SIG = {"K1": P1, "K2": P1, "K3": P1, "K4": P1, "K5": K5}; MEM = {"K1": M10, "K2": M5, "K3": M20, "K4": big, "K5": onlyb}
    rb_month = np.array([d.day == 1 for d in dates]); rb_month[0] = False; rb_once = np.zeros(T, bool); rb_once[1] = True
    slip = np.array([SLIP_BIG if p in BIG else SLIP_ALT for p in cn], float)
    months_out = {}
    for d, (keep, info) in mem.items():
        months_out[str(idx[d].date())] = dict(qualifying=len(keep), top10=[names[j] for j in keep[:10]], top20=[names[j] for j in keep[:20]],
                                             k2_top5=[names[j] for j in top5[d]], copies_dropped=info["copies_dropped"])
    print(f"setup {time.time() - t0:.1f}s start {idx[start].date()} rows {T} pairs in panel {N}", flush=True)
    return dict(raw_pairs=len(raw), dates=dates, start=idx[start], O=O, C=C, cn=cn, N=N, T=T, last_day=last_day, first=first, lastc=lastc,
                SIG=SIG, MEM=MEM, rb_month=rb_month, rb_once=rb_once, slip=slip, months=months_out, btc=btc, eth=eth,
                last_date={p: str(raw[p].index[-1].date()) for p in cn})

def cols_of(name):
    """Columns a run can ever hold (restricting to them changes nothing and is faster)."""
    if name == "HOLD_BTC": return np.array([D["btc"]])
    if name == "HOLD_BASKET": return np.flatnonzero(D["MEM"]["K1"].any(0))
    return np.flatnonzero(D["MEM"][name].any(0))
def target(name, sig=None):
    if name == "HOLD_BTC": W = np.zeros((D["T"], D["N"])); W[:, D["btc"]] = 1.0; return W
    if name == "HOLD_BASKET": return D["MEM"]["K1"] * 0.10
    s = D["SIG"][name] if sig is None else sig
    return D["MEM"][name] * s * SLOT[name]
def costs(fee, alt_slip=SLIP_ALT):
    return fee + np.where(D["slip"] == SLIP_BIG, SLIP_BIG, alt_slip)
def run(name, cost_vec, haircut=0.0, detail=True, W=None):
    """cost_vec: length-N per side bps (or B x N). W: T x N or B x T x N target, default the rule's own."""
    c = cols_of(name); W = target(name) if W is None else W
    W = W[..., c]; cv = np.asarray(cost_vec)[..., c]
    kw = dict(last_day=D["last_day"][c], delist_haircut=haircut, detail=detail)
    if name == "HOLD_BTC": return sim(D["O"][:, c], D["C"][:, c], W, cv, np.zeros(len(c)), rebal=D["rb_once"], **kw), c
    if name == "HOLD_BASKET": return sim(D["O"][:, c], D["C"][:, c], W, cv, np.zeros(len(c)), rebal=D["rb_month"], **kw), c
    return sim(D["O"][:, c], D["C"][:, c], W, cv, np.full(len(c), SLOT[name] / 8), member=D["MEM"][name][:, c], **kw), c
sim = BK.sim_batch

# ------------------------------------------------------------------ measures
def eqp_of(eq): return pd.Series(eq, index=D["dates"])
def slice_metrics(eq): ep = eqp_of(eq); return {k: R.metrics(R.cut(ep, lo, hi).values, PPY) for k, (lo, hi) in SL.items()}
def slice_activity(o, eq):
    wt = o["wt"]; tr = o["traded"]; idx = D["dates"]; prev = np.r_[1.0, eq[:-1]]; out = {}
    for k, (lo, hi) in SL.items():
        m = (idx >= (D["start"] if lo is None else pd.Timestamp(lo))) & (idx <= pd.Timestamp(hi)); yrs = m.sum() / PPY; ws = wt[m].sum(1)
        out[k] = dict(avg_weight=float(ws.mean()), share_of_days_with_position=float((ws > 1e-6).mean()),
                      avg_coins_held=float((wt[m] > 1e-6).sum(1).mean()), sides=int((tr[m] > R.DUST * prev[m][:, None]).sum()),
                      turnover_py=float((tr[m].sum(1) / prev[m]).sum() / yrs))
    return out
def calendar_years(eq):
    ep = eqp_of(eq); ye = ep.groupby(ep.index.year).last(); prev = np.r_[ep.iloc[0], ye.values[:-1]]
    return {int(y): float(v / p - 1) for y, v, p in zip(ye.index, ye.values, prev)}
def describe(name, o, c):
    eq = o["eq"]; held = (o["wt"] > 1e-6).any(0); ever = [D["cn"][c[i]] for i in np.flatnonzero(held)]
    dead = [p for p in ever if D["last_date"][p] < DEAD_BEFORE]
    x = dict(slices=slice_metrics(eq), activity=slice_activity(o, eq), calendar_years=calendar_years(eq),
             forced_exits=len(o["ev"]), forced_exit_pairs=sorted(set(D["cn"][c[i]] for (_, i, _, _) in o["ev"])),
             orders_that_waited=int(o["waits"]), old_exception_would_fire_pair_days=int(o["old_exception_would_fire"]),
             in_position_at_end=bool(o["wt"][-1].sum() > 1e-6), pairs_ever_held=len(ever), dead_pairs_ever_held=len(dead), dead_pairs=dead,
             final_value=float(eq[-1]))
    return x

# ------------------------------------------------------------------ jobs
def shuffle_job(args):
    """Shuffled timing for one rule at one venue."""
    v, name = args; fee = R.VENUES[v]; cv = costs(fee); o, c = run(name, cv, detail=False); s_real = R.sharpe_pp(R.rets(o["eq"]))
    rng = np.random.default_rng(SEED); sig = D["SIG"][name]; cnt = 0; sides = []; wts = []; unshifted = 0; done = 0
    while done < NSHUF:
        b = min(CHUNK, NSHUF - done); WB = np.empty((b, D["T"], D["N"]))
        for j in range(b):
            s = sig.copy()
            for i in c:
                s[:, i], did = BK.circular_shift_in_span(sig[:, i], int(D["first"][i]), int(D["lastc"][i]), rng); unshifted += (not did)
            WB[j] = target(name, s)
        ob, _ = run(name, cv, detail=False, W=WB)
        for j in range(b): cnt += R.sharpe_pp(R.rets(ob["eq"][j])) < s_real
        sides += ob["sides"].tolist(); wts += ob["avg_weight"].tolist(); done += b
    print("shuffle", v, name, "done", flush=True)
    return (v, name), dict(shuffle_pct=cnt / NSHUF, shuffle_mean_sides=float(np.mean(sides)), shuffle_mean_avg_weight=float(np.mean(wts)),
                           rule_sides=int(o["sides"]), rule_avg_weight=float(o["avg_weight"]), pair_draws_not_shifted=int(unshifted))
def venue_job(v):
    fee = R.VENUES[v]; cv = costs(fee); out = {"cost_per_side_bps": {"XBTUSD_ETHUSD": fee + SLIP_BIG, "other": fee + SLIP_ALT}, "bench": {}, "rules": {}}; X = {}
    for b in BENCH:
        o, c = run(b, cv); out["bench"][b] = describe(b, o, c); X[b] = R.rets(o["eq"])
    for n in RULES:
        o, c = run(n, cv); out["rules"][n] = describe(n, o, c); X[n] = R.rets(o["eq"])
    sd = float(np.std([R.sharpe_pp(X[n]) for n in RULES], ddof=1)); out["trial_sharpe_std_per_period"] = sd
    Mx = np.column_stack([X[n] for n in RULES]); out["pbo"] = R.pbo_cscv(Mx, 16, "earliest"); out["pbo_drop_latest"] = R.pbo_cscv(Mx, 16, "latest")
    for n in RULES:
        rr = out["rules"][n]; dsr, sr0 = R.deflated_sharpe(X[n], N_TRIALS, sd); rr["dsr"] = dsr; rr["dsr_sr0_per_period"] = sr0
        rr["sharpe_per_period_all"] = float(R.sharpe_pp(X[n]))
        rr["boot_sharpe_diff_vs_hold_btc"] = R.block_bootstrap_sharpe_diff(X[n], X["HOLD_BTC"])
        rr["boot_sharpe_diff_vs_hold_basket"] = R.block_bootstrap_sharpe_diff(X[n], X["HOLD_BASKET"])
        for b, key in (("HOLD_BTC", "dd_ratio_vs_hold_btc"), ("HOLD_BASKET", "dd_ratio_vs_hold_basket")):
            rr[key] = abs(rr["slices"]["held"]["maxdd"]) / abs(out["bench"][b]["slices"]["held"]["maxdd"])
    print("venue", v, "done", flush=True); return v, out
def be_job(name):
    """Break-even cost, venue free: c bps per side on XBTUSD/ETHUSD, c + 20 on every other pair, same for the benchmark."""
    extra = np.where(D["slip"] == SLIP_BIG, 0.0, SLIP_ALT - SLIP_BIG); cache = {}
    def eq(n, cst):
        key = (n, float(cst))
        if key not in cache: cache[key] = run(n, cst + extra, detail=False)[0]["eq"]
        return cache[key]
    sh = lambda n, cst: R.metrics(eq(n, cst), PPY)["sharpe"]
    out = dict(vs_hold_btc=R.breakeven(lambda cst: sh(name, cst) - sh("HOLD_BTC", cst)),
               vs_hold_basket=R.breakeven(lambda cst: sh(name, cst) - sh("HOLD_BASKET", cst)),
               zero_growth=R.breakeven(lambda cst: R.metrics(eq(name, cst), PPY)["cagr"]))
    print("breakeven", name, "done", flush=True); return name, out
def sens_job(v):
    fee = R.VENUES[v]; out = {}
    for lab, cv, hc in (("alt_slippage_50bps", costs(fee, SLIP_ALT_SENS), 0.0), ("delist_haircut_0.5", costs(fee), HAIRCUT_SENS)):
        o_b = {b: run(b, cv, haircut=hc) for b in BENCH}; res = {"bench": {b: dict(slices=slice_metrics(o[0]["eq"]), forced_exits=len(o[0]["ev"])) for b, o in o_b.items()}, "rules": {}}
        hb = res["bench"]["HOLD_BTC"]["slices"]["held"]
        for n in RULES:
            o, c = run(n, cv, haircut=hc); s = slice_metrics(o["eq"])
            res["rules"][n] = dict(slices=s, forced_exits=len(o["ev"]), final_value=float(o["eq"][-1]),
                                   m1_vs_hold_btc_only=bool(np.isfinite(s["held"]["sharpe"]) and s["held"]["sharpe"] > hb["sharpe"] and abs(s["held"]["maxdd"]) <= R.th("replay_max_drop_ratio_vs_hold") * abs(hb["maxdd"])))
        out[lab] = res
    print("sensitivity", v, "done", flush=True); return v, out
def dispatch(job):
    kind, arg = job
    return kind, {"venue": venue_job, "be": be_job, "shuffle": shuffle_job, "sens": sens_job}[kind](arg)

# ------------------------------------------------------------------ main
if __name__ == "__main__":
    t0 = time.time()
    for f in ("fixtures2.py", "fixtures_basket.py"):
        p = subprocess.run([sys.executable, f], capture_output=True, text=True)
        if p.returncode != 0 or "ALL PASS" not in p.stdout: print(p.stdout, p.stderr); raise SystemExit(f"{f} failed; nothing was run")
        print(f, "ALL PASS", flush=True)
    D = setup()
    jobs = [("shuffle", (v, n)) for n in ["K3", "K1", "K2", "K4", "K5"] for v in R.VENUES] + [("be", n) for n in RULES] + [("venue", v) for v in R.VENUES] + [("sens", v) for v in R.VENUES]
    with mp.get_context("fork").Pool(NPROC) as pool:   # fork so workers inherit the loaded data
        res = pool.map(dispatch, jobs, chunksize=1)
    be = {}; ven = {}; shf = {}; sens = {}
    for kind, (k, o) in res:
        {"be": be, "venue": ven, "shuffle": shf, "sens": sens}[kind][k] = o
    out = {"plan": "PREREG_04_coin_basket_trend.md", "measured_per": "AMENDMENT_2026-11-25_audit_fixes.md", "thresholds": R.thresholds_used(),
           "reading_choices": READING, "start": str(D["start"].date()), "first_row_cash_only": str(D["dates"][0].date()), "end": str(D["dates"][-1].date()),
           "days_including_base": int(D["T"]), "pairs_loaded": D["raw_pairs"], "pairs_in_panel": D["N"], "slices": SL, "ppy": PPY,
           "n_trials": N_TRIALS, "shuffles": NSHUF, "seed": SEED, "slippage_bps": {"XBTUSD_ETHUSD": SLIP_BIG, "other": SLIP_ALT},
           "membership": D["months"], "breakeven": be, "venues": {}, "sensitivity": sens}
    ever10 = sorted(set(p for m in D["months"].values() for p in m["top10"])); ever20 = sorted(set(p for m in D["months"].values() for p in m["top20"]))
    out["membership_summary"] = dict(months=len(D["months"]), pairs_ever_top10=len(ever10), pairs_ever_top20=len(ever20),
                                     dead_ever_top10=[p for p in ever10 if D["last_date"][p] < DEAD_BEFORE], dead_ever_top20=[p for p in ever20 if D["last_date"][p] < DEAD_BEFORE],
                                     min_qualifying=min(m["qualifying"] for m in D["months"].values()), months_with_fewer_than_20=sum(m["qualifying"] < 20 for m in D["months"].values()))
    for v, fee in R.VENUES.items():
        o = ven[v]; cost = fee + SLIP_BIG
        for n in RULES:
            x = o["rules"][n]; x.update(shf[(v, n)])
            x["marks"] = R.five_marks(x["slices"]["held"], o["bench"]["HOLD_BTC"]["slices"]["held"], be[n]["vs_hold_btc"], cost, x["dsr"], o["pbo"]["pbo"], x["shuffle_pct"])
            x["marks_vs_basket"] = R.five_marks(x["slices"]["held"], o["bench"]["HOLD_BASKET"]["slices"]["held"], be[n]["vs_hold_basket"], cost, x["dsr"], o["pbo"]["pbo"], x["shuffle_pct"])
        out["venues"][v] = o
    out["runtime_seconds"] = round(time.time() - t0, 1)
    s = json.dumps(out, indent=1, default=float); open("results_04.json", "w").write(s)
    body = json.loads(s); body.pop("runtime_seconds")
    print("sha256 without runtime", hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]); print("done", round(time.time() - t0, 1), "s", flush=True)
