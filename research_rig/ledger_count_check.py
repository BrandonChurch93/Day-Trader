"""Works out pass mark 3 (deflated Sharpe) again with a larger count of trials, from the stored outputs only. Runs no rule and reads no prices.
Why: the owner's rule says a rerun after an engine fault is counted as a trial (docs/quality/01, docs/decisions/0003 row T6).
The rerun after the audits and the corrected run of replay 05 were not counted when they ran (TRIAL_LEDGER.md, rows R1 and R2).
A larger count can only lower a deflated Sharpe, so it can turn a pass into a fail and never the other way.
Method: deflated Sharpe = Phi((sr - sr0) * k), where sr0 = spread * g(count) and k depends on the return series only.
The stored value gives k, so the value at another count follows. Output: ledger_count_check.json. Usage: python3 ledger_count_check.py"""
import json, math
from scipy import stats
import rig2 as R
EM = 0.5772156649; BAR = R.th("replay_min_deflated_sharpe")
COUNT_ALL = 93   # 49 rule trials (rows 1 to 20, 27 to 42, 43 to 55) + 36 for rerun R1 + 8 for rerun R2, TRIAL_LEDGER.md
def g(n): return (1 - EM) * stats.norm.ppf(1 - 1 / n) + EM * stats.norm.ppf(1 - 1 / (n * math.e))
def redo(dsr, sr_pp, spread, n_old, n_new):
    """Deflated Sharpe at n_new, given its value at n_old. None when the stored value is too close to 0 or 1 to invert."""
    if dsr is None or not (1e-12 < dsr < 1 - 1e-12) or not math.isfinite(sr_pp): return None
    d = sr_pp - spread * g(n_old)
    if abs(d) < 1e-12: return None
    return float(stats.norm.cdf((sr_pp - spread * g(n_new)) * stats.norm.ppf(dsr) / d))
rows = []
def add(test, where, rule, m, dsr, sr_pp, spread, n_old):
    new = redo(dsr, sr_pp, spread, n_old, COUNT_ALL); others = all(m[k] for k in ("m1", "m2", "m4", "m5"))
    rows.append(dict(test=test, where=where, rule=rule, count_as_run=n_old, dsr_as_run=dsr, dsr_at_count_all=new, passed_as_run=bool(m["passed"]),
                     mark3_as_run=bool(m["m3"]), mark3_at_count_all=(None if new is None else bool(new > BAR)),
                     passed_at_count_all=(None if new is None else bool(others and new > BAR))))
v = json.load(open("results_v2.json"))
for t in ("R01", "X2", "S2"):
    for ven, A in v[t]["venues"].items():
        for a in (("ETHUSD",) if t == "S2" else ("BTCUSD", "ETHUSD")):   # S2 is the longer ether sample only; its bitcoin rows are the X2 rows again
            for n, r in A[a]["rules"].items(): add(t, f"{ven}, {a}", n, r["marks"], r["dsr"], r["all"]["sharpe"] / math.sqrt(365), A["trial_sharpe_std_per_period"], A["n_trials"])
for ven, A in v["R03"]["venues"].items():
    for a in ("BTCUSD", "ETHUSD"):
        for n, r in A[a]["rules"].items(): add("R03", f"{ven}, {a}", n, r["marks"], r["dsr"], r["all"]["sharpe"] / math.sqrt(365 * 24), A["trial_sharpe_std_per_period"], v["R03"]["n_trials"])
for f, t in (("results_05.json", "R05 first run"), ("results_05b.json", "R05 corrected run")):
    d = json.load(open(f))
    for c, A in d["costs"].items():
        for n, r in A["rules"].items(): add(t, f"{A['cost_bps_per_side']} bps", n, r["marks"], r["dsr"], r["all"]["sharpe"] / math.sqrt(252), A["trial_sharpe_std_per_period"], d["n_trials"])
d = json.load(open("results_04.json"))
for ven, A in d["venues"].items():
    for n, r in A["rules"].items(): add("R04", ven, n, r["marks"], r["dsr"], r["sharpe_per_period_all"], A["trial_sharpe_std_per_period"], d["n_trials"])
flip = [r for r in rows if r["passed_as_run"] and r["passed_at_count_all"] is False]
unknown = [r for r in rows if r["passed_as_run"] and r["passed_at_count_all"] is None]
m3flip = [r for r in rows if r["mark3_as_run"] and r["mark3_at_count_all"] is False]
passes = [r for r in rows if r["passed_as_run"]]
low = min((r for r in passes if r["dsr_at_count_all"] is not None), key=lambda r: r["dsr_at_count_all"], default=None)
nowork = [r for r in rows if r["dsr_at_count_all"] is None]
out = dict(bar=BAR, bar_key="replay_min_deflated_sharpe", count_all=COUNT_ALL, rows_checked=len(rows), passes_as_run=len(passes),
           rows_not_worked_out=len(nowork), rows_not_worked_out_that_passed_mark3_as_run=sum(r["mark3_as_run"] for r in nowork),
           passes_by_test={t: sum(r["test"] == t for r in passes) for t in sorted({r["test"] for r in rows})},
           passes_that_become_fails=flip, passes_that_could_not_be_worked_out=unknown, mark3_passes_that_become_fails=m3flip,
           lowest_dsr_among_passes_at_count_all=low, rows=rows)
json.dump(out, open("ledger_count_check.json", "w"), indent=1)
print("rows", len(rows), "passes as run", len(passes), "become fails", len(flip), "not worked out", len(unknown), "mark 3 alone flips", len(m3flip))
if low: print("lowest among passes at", COUNT_ALL, ":", low["test"], low["where"], low["rule"], round(low["dsr_at_count_all"], 4))
for r in m3flip: print("  mark 3 flips:", r["test"], r["where"], r["rule"], round(r["dsr_as_run"], 4), "->", round(r["dsr_at_count_all"], 4), "passed as run:", r["passed_as_run"])
