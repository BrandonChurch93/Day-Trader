"""Lists every mark and verdict that differs between the first run and the rerun after the audit fixes, in both directions.
Reads passmarks_01.json, results_01x2.json, results_03.json, diag_x2_pbo.json and results_v2.json. Writes compare_v1_v2.json."""
import json
MK = ["m1", "m2", "m3", "m4", "m5", "passed"]; A = ["BTCUSD", "ETHUSD"]
v2 = json.load(open("results_v2.json")); out = {"changes": [], "counts": {}, "pbo": [], "both_histories": [], "passes": {}}
def diff(run, venue, asset, rule, old, new):
    d = {k: [bool(old[k]), bool(new[k])] for k in MK if bool(old[k]) != bool(new[k])}
    if d: out["changes"].append(dict(run=run, venue=venue, asset=asset, rule=rule, marks=d))
def count(run, olds, news):
    out["counts"][run] = dict(trials=len(olds), passed_first=sum(o["passed"] for o in olds), passed_rerun=sum(n["passed"] for n in news),
                              marks_changed=sum(bool(o[k]) != bool(n[k]) for o, n in zip(olds, news) for k in MK[:5]))
# replay 01
p0 = json.load(open("passmarks_01.json")); o_, n_ = [], []
for vn, o in v2["R01"]["venues"].items():
    for a in A:
        for r, x in o[a]["rules"].items():
            diff("R01", vn, a, r, p0[f"{vn}|{a}|{r}"], x["marks"]); o_.append(p0[f"{vn}|{a}|{r}"]); n_.append(x["marks"])
count("R01", o_, n_)
# cross-check X2 and sensitivity S2 (ether from 2016)
x0 = json.load(open("results_01x2.json")); o_, n_ = [], []
for vn, o in v2["X2"]["venues"].items():
    for a in A:
        for r, x in o[a]["rules"].items():
            old = x0["X2"][a]["rules"][r]["venues"][vn]["marks"]; diff("X2", vn, a, r, old, x["marks"]); o_.append(old); n_.append(x["marks"])
count("X2", o_, n_); o_, n_ = [], []
for vn, o in v2["S2"]["venues"].items():
    for r, x in o["ETHUSD"]["rules"].items():
        old = x0["S2_ETH"]["rules"][r]["venues"][vn]["marks"]; diff("S2", vn, "ETHUSD", r, old, x["marks"]); o_.append(old); n_.append(x["marks"])
count("S2", o_, n_)
# replay 03
if "R03" in v2:
    r0 = json.load(open("results_03.json")); o_, n_ = [], []
    for vn, o in v2["R03"]["venues"].items():
        for a in A:
            for r, x in o[a]["rules"].items():
                old = r0["assets"][a]["rules"][r]["venues"][vn]["marks"]; diff("R03", vn, a, r, old, x["marks"]); o_.append(old); n_.append(x["marks"])
    count("R03", o_, n_)
# overfitting estimate, first run against rerun, with the other readings
d0 = json.load(open("diag_x2_pbo.json"))
def first_pbo(run, vn, a):
    if run == "R01": return d0.get(f"Bitstamp|2013-01-01|{vn}", {}).get("pbo") if a == "BTCUSD" else None
    if run == "X2": return x0["X2"][a]["pbo"][vn]
    if run == "S2": return x0["S2_ETH"]["pbo"][vn] if a == "ETHUSD" else None
    if run == "DIAG": return d0.get(f"Bitstamp|2014-05-01|{vn}", {}).get("pbo") if a == "BTCUSD" else None
    if run == "R03": return r0["assets"][a]["pbo"][vn]
for run in ["R01", "X2", "S2", "DIAG", "R03"]:
    if run not in v2: continue
    for vn, o in v2[run]["venues"].items():
        for a in A:
            if run == "S2" and a == "BTCUSD": continue
            if run == "DIAG" and a == "ETHUSD": continue
            p = o[a]["pbo"]; out["pbo"].append(dict(run=run, venue=vn, asset=a, first=first_pbo(run, vn, a), rerun=p["pbo"], ties_not_overfit=p["pbo_strict"], ties_half=p["pbo_half"],
                                                    tie_share=p["tie_share"], latest_days_dropped=o[a]["pbo_drop_latest"]["pbo"], rows_dropped=p["rows_dropped"], zero_variance_cases=p["zero_variance_cases"]))
# a rule passes for a venue only if it passes on both price histories
for vn in v2["R01"]["venues"]:
    for a in A:
        for r in v2["R01"]["venues"][vn][a]["rules"]:
            b = v2["R01"]["venues"][vn][a]["rules"][r]["marks"]; k = v2["X2"]["venues"][vn][a]["rules"][r]["marks"]
            b0 = p0[f"{vn}|{a}|{r}"]; k0 = x0["X2"][a]["rules"][r]["venues"][vn]["marks"]
            out["both_histories"].append(dict(venue=vn, asset=a, rule=r, bitstamp=b["passed"], kraken=k["passed"], both=b["passed"] and k["passed"],
                                              first_bitstamp=b0["passed"], first_kraken=k0["passed"], first_both=b0["passed"] and k0["passed"],
                                              bitstamp_failed=[m for m in MK[:5] if not b[m]], kraken_failed=[m for m in MK[:5] if not k[m]]))
json.dump(out, open("compare_v1_v2.json", "w"), indent=1)
print(out["counts"]); print(len(out["changes"]), "rows with a change")
for c in out["changes"]: print(c["run"], c["venue"], c["asset"], c["rule"], c["marks"])
print("both:", [(x["venue"], x["asset"], x["rule"]) for x in out["both_histories"] if x["both"]])
