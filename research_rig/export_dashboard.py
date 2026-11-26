"""Writes dashboard/data.json for the owner's read-only screen.

Every figure comes from the second rig (rig2.py) and its outputs: results_v2.json and compare_v1_v2.json, plus
results_02.json for the AI pilot, and results_05.json / results_04.json when they exist. Nothing is typed by hand
except labels and plain-words wording. The output holds derived curves and is not committed.

The five charts need curves and trade lists that the output files do not hold. Making them replays five stored runs, of three rules, on raw
prices that include the held-back years, so that step is a held-back run (research_rig/README.md, "Held-back scripts").
By default this script does NOT do that: it reads the curves from dashboard/curves_cache.json, which is not committed.
With --resimulate it replays those five runs with rig2 and rewrites the cache. What it checks against results_v2.json
is exactly this: growth a year, Sharpe ratio, largest drop and total return over the whole sample, for the rule and for
holding, and for the three daily charts the number of trades. The curves, the year-by-year figures and the trade lists
are derived in that replay and are compared with nothing; no stored output holds them. See AGENTS.md, "Honest testing",
before considering a run on held-back dates.

Usage: python3 export_dashboard.py                 (run from research_rig/; reads the cache, touches no raw prices)
       python3 export_dashboard.py --resimulate    (held-back run; see above)
"""
import json, os, re, sys, copy, hashlib, datetime, numpy as np, pandas as pd
import rig2 as R
import run_v2 as V2
import report_34 as M34
import replay_cards as RC
from rules import RULES
from dashboard_status import SCORECARD_PATH, parse_status, scoreboard, validate_status_runs

GH = "https://github.com/BrandonChurch93/Day-Trader/blob/main/"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "dashboard", "data.json")
CACHE = os.path.join(HERE, "..", "dashboard", "curves_cache.json")
RESIM = "--resimulate" in sys.argv
V2_SHA = hashlib.sha256(open(os.path.join(HERE, "results_v2.json"), "rb").read()).hexdigest()
_cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
if _cache.get("results_v2_sha256") != V2_SHA: _cache = {"results_v2_sha256": V2_SHA, "series": {}}


def cached(sid, make, max_trades=None):
    """Curves for one chart. From the cache unless --resimulate is given; see the note at the top of this file."""
    if not RESIM:
        if sid not in _cache["series"]:
            sys.exit(f"No cached curves for {sid} in dashboard/curves_cache.json (or results_v2.json has changed since they were made). "
                     "Making them replays rules on raw prices that include the held-back years. That is a held-back run: read the note "
                     "at the top of this file and research_rig/README.md before passing --resimulate.")
        return copy.deepcopy(_cache["series"][sid])
    s = make(); tl = s.pop("trades")
    s["trades"] = tl[-max_trades:] if max_trades else tl; s["trades_total"] = len(tl)
    _cache["series"][sid] = copy.deepcopy(s)
    return s
STATUS = os.path.join(HERE, "..", "docs", "STATUS.md")
VEN = list(R.VENUES)                                   # Binance.US, Alpaca, Kraken $10k tier, Kraken entry, Coinbase entry
COST = {v: R.VENUES[v] + R.SLIP for v in VEN}          # cost per side, fee plus slippage, bps
AN = {"BTCUSD": "Bitcoin", "ETHUSD": "Ether"}
MARK = {"m1": "1 (held-back years)", "m2": "2 (break-even cost)", "m3": "3 (deflated Sharpe)",
        "m4": "4 (overfitting)", "m5": "5 (random timing)"}
RULE_WORDS = {"P1": "P1", "P2": "P2", "S50": "S50", "D20": "D20"}
TOL = 1e-9

v2 = json.load(open(os.path.join(HERE, "results_v2.json")))
cmp_ = json.load(open(os.path.join(HERE, "compare_v1_v2.json")))
TH = v2["thresholds"]


def plist(xs, conj="and"):
    xs = list(xs)
    if not xs: return "none"
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + f" {conj} " + xs[-1]


def pct(x, d=1): return f"{x*100:.{d}f}%".replace("-", "\u2212")


# ------------------------------------------------------------------ curves
def yearly(eqp, hp):
    """Return of each calendar year. Position 0 is the starting cash, one bar before the first bar."""
    out = []; yrs = eqp.index.year; E = eqp.values; H = hp.values
    for y in sorted(set(yrs[1:])):
        pos = np.flatnonzero(yrs == y); pos = pos[pos > 0]; i0, i1 = pos[0], pos[-1]
        out.append([int(y), float(E[i1] / E[i0 - 1] - 1), float(H[i1] / H[i0 - 1] - 1)])
    return out


def curves(eqp, hp):
    wk = eqp.index[::7].union([eqp.index[-1]])
    dd = lambda s: s / s.cummax() - 1
    D, DH = dd(eqp), dd(hp)
    return ([[str(d)[:10], float(eqp[d] / eqp.iloc[0]), float(hp[d] / hp.iloc[0])] for d in wk],
            [[str(d)[:10], float(D[d]), float(DH[d])] for d in wk])


def trade_list(idx, opens, eq, wt, traded, cost, hourly):
    prev = np.r_[1.0, eq[:-1]]; out = []
    for t in np.flatnonzero(traded > R.DUST * prev):
        w0 = wt[t - 1] if t > 0 else 0.0
        out.append(dict(time=str(idx[t])[:16 if hourly else 10], action="Buy" if wt[t] > w0 else "Sell", price=float(opens[t]),
                        share_of_account=float(traded[t] / prev[t]), weight_after=float(wt[t]),
                        cost_share_of_account=float(traded[t] * cost / 1e4 / prev[t])))
    return out


def figs(m): return dict(growth_per_year=m["cagr"], sharpe=m["sharpe"], largest_drop=m["maxdd"], total_return=m["total"])


def check(label, a, b):
    for k in ("cagr", "sharpe", "maxdd", "total"):
        if not (abs(a[k] - b[k]) <= TOL * max(1.0, abs(b[k]))):
            raise SystemExit(f"{label}: re-simulated {k} {a[k]} does not match results_v2.json {b[k]}")


def both_status(venue, asset, rule):
    x = next((z for z in cmp_["both_histories"] if z["venue"] == venue and z["asset"] == asset and z["rule"] == rule), None)
    if x is None: return dict(passed=False, text="Not judged on both price histories.")
    if x["both"]: return dict(passed=True, tone="mixed", label="Cleared the marks in a rerun. Not a counted pass", text="Cleared all five pass marks on both price histories in the rerun after the audit fixes. That rerun also carried a stricter pass mark and a changed cost for holding. Those marks are a measurement, not a counted pass.")
    parts = []
    if x["bitstamp_failed"]: parts.append("Marks failed on Bitstamp prices: " + ", ".join(MARK[m] for m in x["bitstamp_failed"]) + ".")
    if x["kraken_failed"]: parts.append("Marks failed on Kraken prices: " + ", ".join(MARK[m] for m in x["kraken_failed"]) + ".")
    return dict(passed=False, text="Did not pass. " + " ".join(parts))


def daily_series(asset, rule, venue):
    """Kraken daily prices, as in cross-check X2."""
    starts = v2["X2"]["starts"]; c = COST[venue]
    d = V2.daily("Kraken", asset); m = d.index >= starts[asset]; dd = d[m]; idx = dd.index
    o, cl, cf = dd.open.values, dd.close.values, dd.volume.values > 0
    t = np.nan_to_num(RULES[rule](d.close)[m].values, nan=0.0)
    eq, wt, tr = R.simulate(o, cl, t, c, can_fill=cf); ep = R.with_base(eq, idx)
    hp = R.with_base(R.simulate(o, cl, np.ones(len(dd)), c, can_fill=cf)[0], idx)
    J = v2["X2"]["venues"][venue][asset]; jr = J["rules"][rule]
    check(f"X2 {venue} {asset} {rule}", R.metrics(R.cut(ep, *R.SL["all"]).values), jr["all"])
    check(f"X2 {venue} {asset} hold", R.metrics(R.cut(hp, *R.SL["all"]).values), J["hold"]["all"])
    tl = trade_list(idx, o, eq, wt, tr, c, False)
    assert len(tl) == jr["all"]["sides"], (len(tl), jr["all"]["sides"])
    eqc, ddc = curves(ep, hp); years = jr["all"]["n"] / 365
    lo, hi = R.SL["held"]
    return dict(rule=dict(figs(jr["all"]), time_invested=jr["all"]["share_of_bars_with_position"], avg_weight=jr["all"]["avg_weight"],
                          trades=jr["all"]["sides"], trades_per_year=jr["all"]["sides"] / years,
                          cost_paid_share=float(sum(x["cost_share_of_account"] for x in tl))),
                hold=figs(J["hold"]["all"]),
                since_2023=dict(rule=figs(jr["held"]), hold=figs(J["hold"]["held"]), start=lo, end=hi, label="Held-back years"),
                equity=eqc, drawdown=ddc, yearly=yearly(ep, hp), trades=tl, start=str(idx[0])[:10], end=str(idx[-1])[:10],
                status=both_status(venue, asset, rule))


_H = {}
def hourly_series(asset, rule, venue):
    """Bitstamp hourly prices, as in replay 03. The day's value is read at the 23:00 bar."""
    if asset not in _H: _H[asset] = V2.hourly_setup(asset)
    x = _H[asset]; c = COST[venue]; idx = x["d"].index
    eq, wt, tr = R.simulate(x["o"], x["c"], x["T"][rule], c, can_fill=x["cf"])
    hq = R.simulate(x["o"], x["c"], np.ones(len(idx)), c, can_fill=x["cf"])[0]
    ep, hp = V2.eod_series(x, eq), V2.eod_series(x, hq)
    J = v2["R03"]["venues"][venue][asset]; jr = J["rules"][rule]
    check(f"R03 {venue} {asset} {rule}", R.metrics(R.cut(ep, *R.SL["all"]).values), jr["all"])
    check(f"R03 {venue} {asset} hold", R.metrics(R.cut(hp, *R.SL["all"]).values), J["hold"]["all"])
    tl = trade_list(idx, x["o"], eq, wt, tr, c, True)
    eqc, ddc = curves(ep, hp); years = jr["all"]["n"] / 365; lo, hi = R.SL["held"]
    st = hourly_status(asset, rule, venue)
    return dict(rule=dict(figs(jr["all"]), time_invested=jr["share_of_hours_in_position"], trades=len(tl), trades_per_year=len(tl) / years,
                          cost_paid_share=float(sum(z["cost_share_of_account"] for z in tl))),
                hold=figs(J["hold"]["all"]),
                since_2023=dict(rule=figs(jr["held"]), hold=figs(J["hold"]["held"]), start=lo, end=hi, label="Held-back years"),
                equity=eqc, drawdown=ddc, yearly=yearly(ep, hp), trades=tl, start=str(ep.index[1])[:10], end=str(ep.index[-1])[:10], status=st)


def hourly_status(asset, rule, venue):
    mk = v2["R03"]["venues"][venue][asset]["rules"][rule]["marks"]
    return dict(passed=bool(mk["passed"]), text=("Passed all five pass marks on Bitstamp hourly prices." if mk["passed"] else
                "Did not pass. Marks failed on Bitstamp hourly prices: " + ", ".join(MARK[k] for k in ("m1", "m2", "m3", "m4", "m5") if not mk[k]) + "."))


def series(sid, label, note, asset, venue, make, status, max_trades=None):
    """The curves come from the cache. The verdict is worked out now from the stored outputs, so it cannot go stale in the cache."""
    s = cached(sid, make, max_trades); shown = s.pop("trades"); s["status"] = status()
    return dict(id=sid, label=label, note=note, asset=AN[asset], kind="Past-price test", cost_bps_per_side=COST[venue], **s,
                trades_shown=len(shown), trades_list=shown[::-1])


P1_NOTE = ("Holds {coin} in quarters: one quarter for each of its 20, 50, 100 and 200 day averages the price is above. "
           "Sits in cash otherwise. Kraken's published daily prices. Fee and slippage {c} bps a side.")
S = [
    series("btc_trend_binance", "Bitcoin: slow trend rule P1, at Binance.US cost", P1_NOTE.format(coin="bitcoin", c=COST["Binance.US"]),
           "BTCUSD", "Binance.US", lambda: daily_series("BTCUSD", "P1", "Binance.US"), lambda: both_status("Binance.US", "BTCUSD", "P1")),
    series("btc_trend_alpaca", "Bitcoin: slow trend rule P1, at Alpaca cost", P1_NOTE.format(coin="bitcoin", c=COST["Alpaca"]),
           "BTCUSD", "Alpaca", lambda: daily_series("BTCUSD", "P1", "Alpaca"), lambda: both_status("Alpaca", "BTCUSD", "P1")),
    series("eth_trend_alpaca", "Ether: slow trend rule P1, at Alpaca cost", P1_NOTE.format(coin="ether", c=COST["Alpaca"]),
           "ETHUSD", "Alpaca", lambda: daily_series("ETHUSD", "P1", "Alpaca"), lambda: both_status("Alpaca", "ETHUSD", "P1")),
    series("btc_day_h1_alpaca", "Bitcoin: day trading rule H1, at Alpaca cost",
           f"Each day at 12:00 UTC, buys if the price is above the day's open, sells at the end of the day. Bitstamp hourly prices. Fee and slippage {COST['Alpaca']} bps a side.",
           "BTCUSD", "Alpaca", lambda: hourly_series("BTCUSD", "H1", "Alpaca"), lambda: hourly_status("BTCUSD", "H1", "Alpaca"), max_trades=400),
    series("btc_day_h7_binance", "Bitcoin: day trading rule H7, at Binance.US cost",
           f"The same day trading rule, only on days when the slow trend is up. Bitstamp hourly prices. Fee and slippage {COST['Binance.US']} bps a side.",
           "BTCUSD", "Binance.US", lambda: hourly_series("BTCUSD", "H7", "Binance.US"), lambda: hourly_status("BTCUSD", "H7", "Binance.US"), max_trades=400),
]
if RESIM: json.dump(_cache, open(CACHE, "w"), allow_nan=False)

# ------------------------------------------------------------------ counts, all read from the JSON
BOTH = [x for x in cmp_["both_histories"] if x["both"]]
BOTH0 = [x for x in cmp_["both_histories"] if x["first_both"]]
both_venues = sorted({x["venue"] for x in BOTH}, key=VEN.index)
both_assets = sorted({x["asset"] for x in BOTH})
no_pass_venues = [v for v in VEN if v not in both_venues]
eth_pass = any(x["asset"] == "ETHUSD" for x in BOTH)
n_pairs = len(cmp_["both_histories"])
cn = cmp_["counts"]
kb = next(x for x in cmp_["pbo"] if x["run"] == "X2" and x["venue"] == "Binance.US" and x["asset"] == "BTCUSD")
kd = next((x for x in cmp_["pbo"] if x["run"] == "DIAG" and x["venue"] == "Binance.US" and x["asset"] == "BTCUSD"), None)
R3 = v2["R03"]
r03_n = sum(1 for vn in VEN for a in AN for _ in R3["venues"][vn][a]["rules"])
r03_pass = sum(x["marks"]["passed"] for vn in VEN for a in AN for x in R3["venues"][vn][a]["rules"].values())
r03_k = sum(1 for a in AN for _ in R3["venues"]["Alpaca"][a]["rules"])
r03_lose = sum(x["all"]["cagr"] < 0 for a in AN for x in R3["venues"]["Alpaca"][a]["rules"].values())
r03_rules = [n for n in R3["per_rule"]["BTCUSD"] if n != "C1"]
r03_gross_up = sum(R3["per_rule"][a][n]["gross_trips"]["avg_bps"] > 0 for a in AN for n in r03_rules)
r03_be = [R3["per_rule"][a][n]["vs_hold"] for a in AN for n in r03_rules]
r03_be_max = max(b["bps"] for b in r03_be if b["status"] == "bracketed")
r03_never = sum(b["status"] == "below_at_zero" for b in r03_be)


def venue_names(vs):
    """Plain names for a list of venue cost levels, grouping the two Kraken levels."""
    out = []
    for v in vs:
        n = "Kraken" if v.startswith("Kraken") else v.replace(" entry", "")
        if n not in out: out.append(n)
    return out


pass_rules = [x["rule"] for x in BOTH]
if BOTH:
    pass_phrase = (f"{len(BOTH)} {plist(AN[a].lower() for a in both_assets)} slow trend rules ({plist(pass_rules)}) pass on both "
                   f"price histories, at {plist(both_venues)} cost only.")
    hl2 = f"After the audit fixes, {pass_phrase} That is a reason to test them in the practice account, not proof that they work."
else:
    pass_phrase = "no rule passes on both price histories."
    hl2 = "After the audit fixes, no rule passes on both price histories."
hl3 = (f"Nothing passes at {plist(venue_names(no_pass_venues), 'or')} cost. " + ("" if eth_pass else "Ether passes nowhere. ")
       + f"Day trading rules: {r03_pass} of {r03_n} pass.")

# ------------------------------------------------------------------ test cards
amend = open(os.path.join(HERE, "AMENDMENT_2026-11-25_audit_fixes.md")).read()
n_fixes = len(re.findall(r"^\| [AB]\d\d", amend, flags=re.M))
r2 = json.load(open(os.path.join(HERE, "results_02.json")))
pil_names = {"P1": "Simple trend rule", "hold": "Just holding bitcoin", "r_fable_a": "Fable, run 1", "r_fable_b": "Fable, run 2",
             "r_fable_c": "Fable, run 3", "r_opus": "Opus", "r_sol": "Sol", "r_neon": "Neon"}
pil = [dict(name=pil_names[k], is_ai=k.startswith("r_"), net_return=x["net_return"], largest_drop=x["max_drop"], trades=x["trades"],
            time_invested=x["exposure"]) for k, x in r2["runs"].items()]
n_ai = sum(p["is_ai"] for p in pil)

tests = [
    dict(id="audit", title="Audit of the test rig", date="2026-11-25", verdict="Faults fixed, tests rerun", tone="info",
         basis="STATED by the two audit reports. MEASURED counts from compare_v1_v2.json.",
         summary=("Two AI models read the rig code separately. Neither found any use of future prices. Both found faults in how "
                  "results were measured. The fixes were written down before the rerun. Most fixed the shared test code. Two did more: one pass mark was made stricter, and holding was made to pay the same cost as the rule in another. "
                  "The crypto rule tests below use the rerun."),
         numbers=[["Fixes listed in the written plan", str(n_fixes)],
                  ["Single pass marks that changed in the rerun", str(sum(x["marks_changed"] for x in cn.values()))],
                  [f"Rule, coin and fee combinations passing on both price histories (of {n_pairs}), first run", str(len(BOTH0))],
                  ["The same, after the fixes", str(len(BOTH))]],
         links=[["Audit and rerun", GH + "docs/research/16_rig_audit.md"], ["Plan for the fixes", GH + "research_rig/AMENDMENT_2026-11-25_audit_fixes.md"]]),
    dict(id="replay01", title="Slow trend rules on bitcoin and ether", date="2026-11-25",
         verdict="Clears the marks at the lowest fee only, in a rerun. Not credited yet" if BOTH and len(both_venues) == 1 else ("Clears the marks in a rerun. Not credited yet" if BOTH else "No pass"),
         tone="mixed" if BOTH else "fail", basis="MEASURED by run_v2.py, read from results_v2.json and compare_v1_v2.json.",
         summary=(f"Nine rules that hold a coin while its trend is up, tested on two price histories, Bitstamp and Kraken. "
                  f"A rule counts only if it passes all five pass marks on both. After the audit fixes, {pass_phrase} "
                  f"Nothing passes at {plist(venue_names(no_pass_venues), 'or')} cost." + ("" if eth_pass else " No ether rule passes.") +
                  f" The pass is on a knife edge: the overfitting estimate is {kb['rerun']:.3f} against a limit of {TH['backtest_max_pbo']}, "
                  f"and {kb['latest_days_dropped']:.3f}, a fail, when the latest days are dropped instead of the earliest. "
                  + (f"On Bitstamp prices from the same start date it is {kd['rerun']:.3f}, a fail. " if kd and kd["rerun"] >= TH["backtest_max_pbo"] else "") +
                  "It came in a rerun that carried a stricter pass mark and a changed cost for holding as well as engine fixes, so research recommends it is not credited as a pass (question 18b on your list). It is a reason to watch the rule in the practice account, not proof that it works."),
         numbers=[[f"Passes on Bitstamp prices (of {cn['R01']['trials']})", str(cn["R01"]["passed_rerun"])],
                  [f"Passes on Kraken prices (of {cn['X2']['trials']})", str(cn["X2"]["passed_rerun"])],
                  [f"Passes on both (of {n_pairs})", str(len(BOTH))],
                  ["Passes on both in the first run", str(len(BOTH0))],
                  ["Overfitting estimate, bitcoin, Kraken prices, Binance.US cost", f"{kb['rerun']:.3f}"],
                  ["Limit for the overfitting estimate", str(TH["backtest_max_pbo"])]],
         links=[["Audit and rerun", GH + "docs/research/16_rig_audit.md"], ["Replay 01", GH + "docs/research/12_replay_01_crypto_trend.md"],
                ["Cross-check", GH + "docs/research/12b_replay_01_kraken_crosscheck.md"]]),
    dict(id="replay03", title="Day trading rules on bitcoin and ether", date="2026-11-25", verdict="Failed" if r03_pass == 0 else "Some passes",
         tone="fail" if r03_pass == 0 else "mixed", basis="MEASURED by run_v2.py, read from results_v2.json.",
         summary=(f"Eight rules that get in and out inside one day, on Bitstamp hourly prices. After the audit fixes, {r03_pass} of {r03_n} "
                  f"rule, coin and fee combinations pass. {r03_lose} of {r03_k} lose money over the whole test at Alpaca cost. "
                  f"Before any fee, {r03_gross_up} of {len(r03_be)} gain on an average round trip. "
                  f"The highest cost at which any of them still keeps up with holding is {r03_be_max:.1f} bps a side."),
         numbers=[[f"Passes (of {r03_n} rule, coin and fee combinations)", str(r03_pass)],
                  [f"Lose money at Alpaca cost (of {r03_k})", str(r03_lose)],
                  [f"Never keep up with holding, even with no fee (of {len(r03_be)})", str(r03_never)],
                  ["Highest break-even cost against holding", f"{r03_be_max:.1f} bps a side"]],
         links=[["Audit and rerun", GH + "docs/research/16_rig_audit.md"], ["Replay 03", GH + "docs/research/15_replay_03_intraday_crypto.md"]]),
    dict(id="pilot02", title="AI models making the daily call", date="2026-11-25", verdict="Inconclusive", tone="unknown",
         basis="MEASURED by score_02.py, read from results_02.json. Not part of the audit rerun.",
         summary=(f"{n_ai} AI runs each made {r2['n_decisions']['r_opus']} daily decisions on past bitcoin prices. All behaved like a simple "
                  "trend rule. The sample is far too small to tell skill from luck, and that was stated before it ran."),
         numbers=[["Daily decisions per run", str(r2["n_decisions"]["r_opus"])]],
         links=[["Pilot 02", GH + "docs/research/14_ai_calls_pilot_02.md"]], table=pil),
]


# ------------------------------------------------------------------ optional cards, only when their files exist
def J(f):
    p = os.path.join(HERE, f)
    return json.load(open(p)) if os.path.exists(p) else None


def card_05():
    """Replay 05, stocks. results_05.json is the first run; results_05b.json is the corrected run (I2 fixed to match its plan)."""
    a, b = J("results_05.json"), J("results_05b.json")
    if a is None: return None
    L = [l for l in ("low", "base", "high") if l in a["costs"]]; N = list(a["costs"][L[0]]["rules"])
    P = lambda r, l: [n for n in N if r["costs"][l]["rules"][n]["marks"]["passed"]]
    bps = lambda l: a["costs"][l]["cost_bps_per_side"]
    cnt = lambda r, l: f"{len(P(r, l))}: {plist(P(r, l))}" if P(r, l) else "0"
    pb = lambda r: ", ".join(f"{r['costs'][l]['pbo']['pbo']:.3f}" for l in L) + f" (limit {TH['backtest_max_pbo']})"
    rows = [[f"First run, passes at {bps(l)} bps a side (of {len(N)})", cnt(a, l)] for l in L]
    rows += [[f"First run, overfitting estimate at {', '.join(str(bps(l)) for l in L)} bps", pb(a)]]
    if b is not None:
        rows += [[f"Corrected run, passes at {bps(l)} bps a side (of {len(N)})", cnt(b, l)] for l in L]
        rows += [[f"Corrected run, overfitting estimate at {', '.join(str(bps(l)) for l in L)} bps", pb(b)]]
        per = []
        for l in L:
            bo = [z for z in P(b, l) if z in P(a, l)]; ob = [z for z in P(b, l) if z not in P(a, l)]
            per.append(f"At {bps(l)} bps, " + (f"{plist(bo)} {'passes' if len(bo) == 1 else 'pass'} in both runs" if bo else "no rule passes in both runs")
                       + (f"; {plist(ob)} {'passes' if len(ob) == 1 else 'pass'} only in the corrected run." if ob else "."))
        late = (" ".join(per) + " A pass that appears only in the corrected run came after a correction whose effect was already known, "
                "so it counts for less than a pass in both runs. The correction was to one rule's code, not to the engine, and your rerun rule names the engine only. "
                "The first run has a slip too: its ledger row was added after it started. Research recommends that no pass from either run is credited (question 18b on your list).")
    else:
        late = "The corrected run is not in yet, so its result is UNKNOWN."
    base = "base" if "base" in a["costs"] else L[0]; cb = a["costs"][base]["cost_bps_per_side"]
    x = a["costs"][base]["rules"]["T1"]["held"]; h = a["costs"][base]["bench"]["HOLD"]["held"]
    rows += [[f"Example, T1 ten-month rule, held-back growth a year (first run, {cb} bps)", pct(x["cagr"])], ["Holding the market, same years", pct(h["cagr"])],
             [f"Example, T1, held-back largest drop (first run, {cb} bps)", pct(x["maxdd"])], ["Holding the market, same years", pct(h["maxdd"])]]
    na = len(P(a, base)); nb = len(P(b, base)) if b is not None else None
    first = f"{na or 'None'} of {len(N)} pass at {cb} bps in the first run"
    return dict(id="replay05", title="Slow trend rules on the US stock market", date=None,
                verdict=(first + f"; {nb or 'none'} of {len(N)} in the corrected run. No pass credited yet" if b is not None else first),
                tone="mixed" if na else "fail",
                basis="MEASURED by run_05.py, read from results_05.json" + (" and results_05b.json." if b is not None else ". Corrected run UNKNOWN, not in yet."),
                summary=(f"{len(N)} rules that hold the stock market while its trend is up, tested on free daily data from {str(a.get('start', ''))[:4] or 'the start'} on, "
                         "at three cost levels. An audit found that rule I2 did not match its plan, so the test was run again with only that fixed. " + late +
                         " The plan names no main rule; T1 is shown only as an example. A pass means worth testing in the practice account, not that it makes money."),
                numbers=rows, links=[["Replay 05", GH + "docs/research/22_replay_05_stock_trend.md"], ["Plan", GH + "research_rig/PREREG_05_stock_trend_free_data.md"]])


def card_04():
    """Replay 04, coin basket. Layout: venues[venue]['rules'][K1..K5]['slices'|'marks'|'dsr'], venues[venue]['bench']['HOLD_BTC'|'HOLD_BASKET']['slices']."""
    r = J("results_04.json")
    if r is None: return None
    V = r["venues"]; tot = sum(len(v["rules"]) for v in V.values())
    npass = sum(bool(x["marks"]["passed"]) for v in V.values() for x in v["rules"].values())
    rows = [[f"Passes, all rule and venue pairs (of {tot})", str(npass)]]
    rows += [[f"Passes at {vn} cost (of {len(v['rules'])})", str(sum(bool(x["marks"]["passed"]) for x in v["rules"].values()))] for vn, v in V.items()]
    vn = "Binance.US" if "Binance.US" in V else next(iter(V)); u = V[vn]
    x = u["rules"]["K1"]["slices"]["held"]; hb = u["bench"]["HOLD_BTC"]["slices"]["held"]; hk = u["bench"]["HOLD_BASKET"]["slices"]["held"]
    rows += [[f"K1, held-back growth a year, {vn} cost", pct(x["cagr"])], ["Holding bitcoin, same years", pct(hb["cagr"])], ["Holding the basket, same years", pct(hk["cagr"])],
             [f"K1, held-back largest drop, {vn} cost", pct(x["maxdd"])], ["Holding bitcoin, same years", pct(hb["maxdd"])], ["Holding the basket, same years", pct(hk["maxdd"])]]
    nr = len(next(iter(V.values()))["rules"])
    return dict(id="replay04", title="Slow trend rules on a basket of coins", date=None, verdict="Failed" if npass == 0 else f"{npass} of {tot} pass",
                tone="fail" if npass == 0 else "mixed", basis="MEASURED by the replay 04 run, read from results_04.json.",
                summary=(f"{nr} rules that hold the largest coins while each one's trend is up, with coins that later died kept in. "
                         f"{npass} of {tot} rule and venue pairs pass. K1, the main rule named in the plan, is shown against holding bitcoin and holding the basket."),
                numbers=rows, links=[["Replay 04", GH + "docs/research/23_replay_04_coin_basket.md"], ["Plan", GH + "research_rig/PREREG_04_coin_basket_trend.md"]])


c5, c4 = card_05(), card_04()
if c5: tests.append(c5)
else:
    tests.append(dict(id="stocks", title="Stocks", date=None, verdict="Not tested yet", tone="unknown", basis="STATED by the plan.",
                      summary="A test of slow trend rules on free stock market data has a written plan. Its results are not in yet.", numbers=[],
                      links=[["Plan", GH + "research_rig/PREREG_05_stock_trend_free_data.md"]]))
if c4: tests.append(c4)
if M34.RESULT.is_file():
    tests.append(M34.dashboard_card(M34.load(), GH))
tests += RC.cards(GH)   # Saved replay result pages (replay_cards.py)


# ------------------------------------------------------------------ current owner-only items, read from docs/STATUS.md at export time
def waiting():
    """Read the listed actions under "Waiting on the owner". Return (items, problem)."""
    try:
        with open(STATUS, encoding="utf-8") as f:
            txt = f.read()
    except OSError:
        return [], "The status page could not be opened."
    m = re.search(r"^##[ \t]+Waiting on the owner[ \t]*\n(?P<body>.*?)(?=^##[ \t]|\Z)", txt, flags=re.M | re.S)
    if not m: return [], "The status page has no Waiting on the owner section."
    out = []
    for it in re.findall(r"^[ \t]*(?:\d+\.|[-*])[ \t]+(.+)$", m.group("body"), flags=re.M):
        plain = re.sub(r"`([^`]*)`|\[([^\]]+)\]\([^)]*\)", r"\1\2", it).replace("**", "")
        title, _, note = plain.partition(". ")
        out.append([title.strip().rstrip("."), note.strip(), ""])
    return out, None


def findings_and_scoreboard():
    with open(STATUS, encoding="utf-8") as f:
        status = f.read()
    findings = parse_status(status, GH)
    exported = [{k: item[k] for k in ("lead", "body", "links", "utc", "source_lines")} for item in findings]
    validate_status_runs(status, exported)
    with open(os.path.join(HERE, "..", SCORECARD_PATH), encoding="utf-8") as f:
        score = scoreboard(f.read(), findings, GH)
    for item in exported:
        del item["source_lines"]
    return exported, score




# ------------------------------------------------------------------ where things stand: the same rows as docs/STATUS.md, from tools/status_table.py
def status_rows():
    import sys
    root = os.path.abspath(os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(root, "tools"))
    import status_table as ST
    clean = lambda t: re.sub(r"`([^`]*)`", r"\1", re.sub(r"\s*\(`[^`]*`\)", "", t)).strip()
    cwd = os.getcwd(); os.chdir(root); rows = []
    try:
        for f in ST.ROWS:
            try:
                t = f()
                links = [[os.path.basename(pth), GH + pth] for pth in re.findall(r"`([^`]+\.md)`", t[3])]
                rows.append(dict(test=clean(t[0]), asked=clean(t[1]), result=clean(t[2]), links=links))
            except FileNotFoundError as e:   # same handling as status_table.table()
                rows.append(dict(test=f.__name__, asked="", result=f"Output file missing: {os.path.basename(e.filename)}", links=[]))
    finally:
        os.chdir(cwd)
    return rows


# ------------------------------------------------------------------ sentence under the comparison section, only if true
notes = []
ahead_fail = [s["label"] for s in S if s["rule"]["growth_per_year"] > s["hold"]["growth_per_year"] and not s["status"]["passed"]]
if ahead_fail:
    notes.append("A rule can grow faster than holding here and still fail its pass marks.")
pass_less = [s["label"] for s in S if s["status"]["passed"] and s["since_2023"]["rule"]["growth_per_year"] < s["since_2023"]["hold"]["growth_per_year"]]
if pass_less:
    notes.append("A rule can pass and still grow less than holding in the held-back years. The first pass mark asks for a better Sharpe and a much smaller drop, not more growth.")

ntest = sum(s["trades_total"] for s in S)
WAIT = waiting()


# ------------------------------------------------------------------ practice trader records, read from the practice-records branch. No price is touched.
PRACTICE_LIVE = "https://raw.githubusercontent.com/BrandonChurch93/Day-Trader/practice-records/records/summary.json"  # Works only while the repo is public. Set to None if it is made private; the page then shows the copy saved when it was last built.
def practice():
    """The newest summary.json the practice desk wrote (Run.summary in practice/trader.py, all traders in one file), or None if the branch cannot be read."""
    import subprocess; root = os.path.abspath(os.path.join(HERE, ".."))
    try:
        subprocess.run(["git", "fetch", "-q", "origin", "practice-records"], cwd=root, check=True, capture_output=True, timeout=60)
        return json.loads(subprocess.run(["git", "show", "FETCH_HEAD:records/summary.json"], cwd=root, check=True, capture_output=True, timeout=60).stdout)
    except Exception as e:
        print("practice records not read:", type(e).__name__); return None
def timemachine():
    """The stored scores of the time machine plans (timemachine/results_tm01.json to results_tm04.json), shaped for the page. Reads no prices and runs nothing."""
    root = os.path.abspath(os.path.join(HERE, "..")); plans = []
    names = {"07": "July", "08": "August", "09": "September", "10": "October", "11": "November 1 to 24"}
    for pid, label, f, doc, plan in (("TM01", "Prices alone", "results_tm01.json", "docs/research/29_time_machine_tm01_crypto_price_only.md", "timemachine/PLAN_TM01_crypto_price_only.md"),
                                     ("TM02", "Prices and dated headlines", "results_tm02.json", "docs/research/30_time_machine_tm02_crypto_with_news.md", "timemachine/PLAN_TM02_crypto_with_news.md")):
        fp = os.path.join(root, "timemachine", f)
        if not os.path.exists(fp):
            continue
        o = json.load(open(fp)); models, sessions, total = [], [], 0
        for tag, m in o["models"].items():
            models.append(dict(name=m["name"], months_counted=len(m["months_counted"]), months=len(m["months"]), gain=m.get("sum_gain_usd"), hold=m.get("sum_hold_usd"),
                               twin_p80=m.get("sum_twin_p80_usd"), verdict=m["verdict"]))
            for mo, r in m["months"].items():
                total += 1
                if not r["finished"]:
                    continue
                why = []
                for w in r["why"]:
                    ex = w["exit_reason"] or ""
                    end = ("stop reached" if "stop" in ex else "target reached" if "target" in ex else "time limit" if "time" in ex or "by_utc" in ex else "sold by the trader") if w["closed_utc"] else "open at the end"
                    looked = ", ".join((f"{k} bars x{v}" if k not in ("news", "price") else f"{k} x{v}") for k, v in sorted(w["looked"].items())) or "packet only"
                    why.append(dict(wake=w["wake_utc"][:16].replace("T", " "), coin=w["symbol"], looked=looked, reason=w["reason"] or "", sources=w.get("sources") or [],
                                    ended=end + (" " + w["closed_utc"][:16].replace("T", " ") if w["closed_utc"] else ""), result=w["result"], gain=w["gain_usd"], gain_pct=w["gain_pct"]))
                sessions.append(dict(mo=mo, month=names[mo], model=m["name"], gain=r["gain_usd"], hold=r["hold_gain_usd"], twin_p80=r.get("twin_p80_usd"), twins_beaten=r.get("twins_beaten"),
                                     twins_done=r["twins_done"], buys=r["buys"], wins=r["wins"], losses=r["losses"], max_drop=r["max_drop"], why=why))
        sessions.sort(key=lambda x: (x["mo"], x["model"]))
        plans.append(dict(id=pid, label=label, models=models, sessions=sessions, sessions_total=total, news_test=o.get("news_test"), doc=GH + doc, plan=GH + plan))
    plans += [x for x in (tm03_plan(root), tm04_plan(root)) if x]
    return dict(start_usd=R.th("tm_account_start_usd"), plans=plans) if plans else None
def tm03_plan(root):
    """TM03, the bitcoin dial, from timemachine/results_tm03.json (score_tm03.py). A model whose months are not all in gets no figures, only "not finished".
    The plain-rule line comes from timemachine/dial_rules_tm03.json when that file exists."""
    fp = os.path.join(root, "timemachine", "results_tm03.json")
    if not os.path.exists(fp):
        return None
    o = json.load(open(fp)); n = len(o["months"]); models = []
    for tag, m in o["models"].items():
        done = bool(m.get("complete")); sr = m.get("sum_shuffle_runs") or {}
        models.append(dict(name=m["name"], months_in=len(m.get("months_counted") or []), months=n, complete=done,
                           gain=m.get("sum_gain_usd") if done else None, hold=m.get("sum_hold_usd") if done else None,
                           percentile=sr.get("model_percentile") if done else None, verdict=m["verdict"] if done else "not finished"))
    rule = None; fr = os.path.join(root, "timemachine", "dial_rules_tm03.json")
    if os.path.exists(fr):
        dr = json.load(open(fr))
        plain = [d for d in dr["dials"].values() if not d.get("hindsight") and "constant" not in d.get("description", "").lower()]
        done = [dr["models"][t] for t in dr.get("complete_models", []) if t in dr["models"]]
        if plain and done:
            bm = max(done, key=lambda x: x["sum_gain_usd"])
            rule = dict(rule_gain=round(max(d["sum_gain_usd"] for d in plain), 2), model_gain=round(bm["sum_gain_usd"], 2), model=bm["name"],
                        doc=GH + "docs/research/37_tm03_plain_dials.md")
    return dict(id="TM03", kind="dial", label="Bitcoin dial", models=models, sessions=o.get("sessions"), months=n, pass_percentile=o.get("pass_percentile"),
                method=(o.get("method") or {}).get("verdict"), rule=rule, start_usd=o.get("account_start_usd"),
                doc=GH + "docs/research/34_time_machine_tm03_bitcoin_dial.md", plan=GH + "timemachine/PLAN_TM03_bitcoin_dial.md")
def tm04_plan(root):
    """TM04, the stock basket, from timemachine/results_tm04.json (score_tm04.py). Until that file exists the plan shows as being scored.
    A run that is not finished carries only its verdict ("running" or "not started"), never a figure."""
    doc = "docs/research/36_time_machine_tm04_stock_basket.md"
    base = dict(id="TM04", kind="basket", label="Stock basket", doc=GH + doc if os.path.exists(os.path.join(root, doc)) else None, plan=GH + "timemachine/PLAN_TM04_stock_basket.md")
    fp = os.path.join(root, "timemachine", "results_tm04.json")
    if not os.path.exists(fp):
        return dict(base, scored=False)
    o = json.load(open(fp)); rows = []
    for tag, m in o["models"].items():
        for run in o.get("runs_per_model") or sorted(m["runs"]):
            r = m["runs"].get(run) or {}; fin = bool(r.get("finished")); rb = r.get("random_basket") or {}
            rows.append(dict(name=m["name"], run=run, finished=fin, verdict=r.get("verdict") or "not started",
                             gain=r.get("gain_usd") if fin else None, equal=r.get("equal_weight_gain_usd") if fin else None,
                             percentile=rb.get("model_percentile") if fin else None))
    return dict(base, scored=True, rows=rows, sessions=o.get("sessions"), pass_percentile=o.get("pass_percentile"), method=(o.get("method") or {}).get("verdict"))
PR = practice()
findings, research_scoreboard = findings_and_scoreboard()
pr_on = bool(PR) and PR.get("status") in ("running", "halted")
pr_n = PR["totals"]["orders"] if pr_on else 0
pr_card = (dict(id="practice", label="Practice account", trades=pr_n, state="Running" if PR["status"] == "running" else "Stopped, needs you",
                why="Pretend money. Several traders, some fixed rules and some AI, share one practice account. A plain program checks and places every order. They are listed at the top of this page.") if pr_on else
           dict(id="practice", label="Practice account", trades=0, state="Not connected", why="Needs the practice key from you."))
out = dict(
    generated_utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"),
    accounts=[dict(id="live", label="Real money", trades=0, state="Not started", why="No real account is connected. Nothing has been bought or sold."),
              pr_card,
              dict(id="tests", label="Past-price tests", trades=ntest, state="Has results",
                   why=f"Pretend trades on old prices, in the {len(S)} comparisons below. Not real money.")],
    headline=[("No real trade has been made. " + (f"The practice account has sent {pr_n} pretend-money order" + ("" if pr_n == 1 else "s") + "." if pr_n else "The practice desk is running and has sent no order yet.")) if pr_on
              else "No real or practice trade has been made."],
    practice=PR, practice_live_url=PRACTICE_LIVE,
    timemachine=timemachine(),
    believed=findings, scoreboard=research_scoreboard,
    status_rows=status_rows(), status_link=GH + "docs/STATUS.md",
    tests=tests, series=S, compare_notes=notes,
    waiting_on_you=WAIT[0], waiting_problem=WAIT[1], waiting_link=GH + "docs/STATUS.md#waiting-on-the-owner",
    glossary=[["Past-price test", "Running a rule over old prices to see how it would have done. Also called a replay or backtest."],
              ["Just holding", "Buying once at the start and never selling. The rule has to beat this to be worth anything."],
              ["Price history", "One venue's record of past prices. Bitcoin and ether are tested on two, Bitstamp's and Kraken's, and a rule must pass on both."],
              ["Pass marks", (f"Five checks every rule must pass. 1: in the held-back years, a better Sharpe than holding and a largest drop at most {TH['replay_max_drop_ratio_vs_hold']:.0%} of holding's. "
                             f"2: still keeps up with holding at {TH['backtest_min_breakeven_cost_multiple']} times the fee. 3: deflated Sharpe above {TH['replay_min_deflated_sharpe']}. "
                             f"4: overfitting estimate under {TH['backtest_max_pbo']}. 5: beats at least {TH['replay_min_shuffle_percentile']:.0%} of random timings.")],
              ["Held-back years", f"{R.SL['held'][0]} to {R.SL['held'][1]}. Kept apart from the years used to look at the rules, then used to judge them."],
              ["Overfitting", "A rule that fits the past by luck and will not repeat. The overfitting estimate is the chance the best rule on one half of the history lands in the bottom half on the other."],
              ["Deflated Sharpe", "The Sharpe ratio after allowing for how many rules were tried. Trying many rules makes a lucky one likely."],
              ["Growth a year", "The steady yearly rate that gives the same end result."],
              ["Largest drop", "The biggest fall from a high point to a later low point."],
              ["Sharpe", "Return divided by how bumpy the ride was. Higher is better. Around 1 is good for one asset."],
              ["bps", "Hundredths of one percent. 30 bps is 0.30%."],
              ["Fees", "What the venue charges on each buy and each sell, plus a small allowance for a worse price."],
              ["Time invested", "Share of days the rule held any of the coin and was not all in cash."],
              ["Audit", "A separate check of the test code by two other AI models, looking for mistakes and for any use of future prices."]],
)
json.dump(out, open(OUT, "w"), allow_nan=False)
print(os.path.getsize(OUT), "bytes;", [(s["id"], round(s["rule"]["growth_per_year"], 3), round(s["hold"]["growth_per_year"], 3), s["trades_total"], s["status"]["passed"]) for s in S])
print("both:", [(x["venue"], x["asset"], x["rule"]) for x in BOTH], "r03", r03_pass, r03_n, "cards:", [t["id"] for t in tests])
