"""Render the TM06-R result page (docs/research/78_time_machine_tm06r_fable_repeat.md) from the pinned saved outputs.
Reads four files kept off repo: the three picker result files written by timemachine/score_tm06.py (run 1 arm g, run 2 g2,
run 3 g3) and the shown-items file built from them. Does not open prices or score anything.
Run from the repo root:  python3 tools/report_saved_tm06r.py FOLDER > docs/research/78_time_machine_tm06r_fable_repeat.md
Stops with TM06R_REPORT_PIN if a file differs from its fingerprint below."""
import argparse, json, re, statistics
from hashlib import sha256
from pathlib import Path

PINS = {
    "results_tm06_g.json": "cd49fb4c86a74f02bd24866f18c3a07b5508a79e3edf32d04aa5a130aa2fdef5",
    "results_tm06_g2.json": "d442db3874d3d39efe056546d4ef1532a896ab97fd322dd82a12d66d4b3b482c",
    "results_tm06_g3.json": "4dceedfa5d727734fb6e08b508be986476eb5919cefc60ff48a5ecc871c8c5b5",
    "results_tm06_r_shown.json": "e8693ea0baedba729d0c71987f31f3bfd0fcf9d607a9f54d90696d24f5353231",
}
RUNS = [("run1_g", "results_tm06_g.json", "Run 1 (arm g)"), ("run2_g2", "results_tm06_g2.json", "Run 2 (g2)"),
        ("run3_g3", "results_tm06_g3.json", "Run 3 (g3)")]
MODEL = "Claude Fable 5.2"
pc = lambda x: f"{x:+.2f}%"
row = lambda *c: "| " + " | ".join(map(str, c)) + " |"
yes = lambda b: "yes" if b else "no"


def config_value(key):
    text = open("config/thresholds.yaml").read()
    m = re.search(rf"^{key}:\n  value: (.+)$", text, re.M)
    assert m, f"config key {key} not found"
    return m.group(1).strip()


def render(res, shown):
    pass_pct = config_value("tm_weights_pass_percentile")
    main_fee = {r["main_fee_bps"] for _, f, _ in RUNS for r in [next(iter(res[f]["scores"].values()))]}
    assert len(main_fee) == 1; fee = main_fee.pop(); fk = f"{fee:g}"
    joined = {k: res[f]["joined"]["picker"]["models"][MODEL] for k, f, _ in RUNS}
    S = shown["runs"]
    for k, f, _ in RUNS:
        assert joined[k]["missing"] == [] and len(joined[k]["sessions"]) == 8, f"{k} is not complete"
        assert S[k]["clears"] == joined[k]["clears_all_marks"] and abs(S[k]["joined_gain_pct"] - joined[k]["gain_pct"]) < 1e-9
        assert S[k]["clears"] == (joined[k]["above"]["equal_all_held"] and joined[k]["above"]["twins_pass_percentile"]), f"{k}: clears is not the addendum's two marks"
    clears = [S[k]["clears"] for k, _, _ in RUNS[1:]]
    outcome = "repeats" if all(clears) else "did not repeat" if not any(clears) else "mixed"
    assert outcome == shown["outcome"], "outcome in the shown file differs from the addendum's rule"
    hold = {k: joined[k]["yardsticks_gain_pct"]["equal_all_held"] for k in joined}
    top7 = {k: joined[k]["yardsticks_gain_pct"]["top_7d_rise"] for k in joined}
    assert len({round(v, 9) for v in hold.values()}) == 1 and len({round(v, 9) for v in top7.values()}) == 1, "yardsticks differ between runs"
    hold, top7 = hold["run1_g"], top7["run1_g"]
    months = sorted(shown["per_month_median"])
    per = {}
    for k, f, _ in RUNS:
        for sid, s in res[f]["scores"].items():
            if s["part"] != "P": continue
            m = s["window"]["start"][:7]; b = s["by_fee"][fk]
            per.setdefault(m, {})[k] = b["model"]["final_gain_pct"]
            y = (b["yardsticks"]["equal_all_held"]["stats"]["final_gain_pct"], b["yardsticks"]["top_7d_rise"]["stats"]["final_gain_pct"])
            per[m].setdefault("y", y); assert per[m]["y"] == y, f"yardsticks differ in {m}"
    for m in months:
        assert abs(statistics.median(per[m][k] for k, _, _ in RUNS) - shown["per_month_median"][m]["median_gain_pct"]) < 1e-9
    spreads = [v for _, f, _ in RUNS for s in res[f]["scores"].values() if s["part"] == "P" for c, v in s["half_spread_bps"].items() if c != "BTC/USD"]
    best = {S[k]["best_month"] for k, _, _ in RUNS}
    bm = best.pop() if len(best) == 1 else None
    bname = {"2026-05": "May"}.get(bm, bm) if bm else "its best month"
    neg = sum(S[k]["joined_without_best_month_gain_pct"] < 0 for k, _, _ in RUNS)
    above7 = sum(S[k]["may"]["model_above_top_7d_rise"] for k, _, _ in RUNS)
    may_rule = {round(S[k]["may"]["top_7d_rise_gain_pct"], 9) for k, _, _ in RUNS}
    assert len(may_rule) == 1
    n_clear = sum(S[k]["clears"] for k, _, _ in RUNS)
    L = ["# Time machine TM06-R: does the Claude Fable 5.2 picker repeat", ""]
    L.append(f"MEASURED. TM06-R {outcome}: of the two repeat runs of the {MODEL} picker on the same eight months, "
             f"{sum(clears)} cleared both marks (above holding all 20 coins and strictly above the {pass_pct}th percentile of its random twins) "
             f"and {len(clears) - sum(clears)} did not; with run 1, {n_clear} of 3 runs cleared. "
             f"All three runs were {'negative' if neg == 3 else f'negative in {neg} of 3'} without {bname}. "
             f"Same months, so this measures run-to-run luck only. Fee {fk} bps per side.")
    L += ["", "STATED. The rule was set before runs 2 and 3 started, in `timemachine/TM06R_addendum.md` and ledger row TM06-R "
          "(`research_rig/TRIAL_LEDGER.md`): repeats if both new runs clear above `equal_all_held` and above the twins' pass percentile "
          "(`tm_weights_pass_percentile`), did not repeat if neither does, mixed if one does. Run 1 is arm g of plan TM06 "
          "(`timemachine/PLAN_TM06_hot_coin_swing.md`), read before the rule was written. Each run is 8 fresh one-month sessions "
          "with the same card, config, briefs, server and twin settings; runs 2 and 3 were told arm g's folders were off limits. "
          "Each run was scored on its own by `timemachine/score_tm06.py`, unchanged. STATED by the operator: run 1 ran the scorer as is; runs 2 and 3 ran it through an off-repo wrapper that scores sessions in parallel, whose output was byte-identical to the serial scorer on three checks, including the committed control run.", "",
          "## Each run joined over eight months", "",
          f"MEASURED. Main fee `tm06_plan` main_fee_bps, {fk} bps per side, plus each coin's half spread "
          f"({min(spreads):.0f} to {max(spreads):.0f} bps, as stored with each session) and perpetual funding, as the scorer charges. "
          "Months are joined by chaining each month's gain.", "",
          row("Run", "Joined gain", "Holding all 20", "Above holding all 20", "Top 7-day rise rule", "Twin median", "Twin percentile",
              f"Above {pass_pct}th percentile", "Clears both marks"),
          row("---", "---:", "---:", "---", "---:", "---:", "---:", "---", "---")]
    for k, _, name in RUNS:
        j = joined[k]
        L.append(row(name, pc(j["gain_pct"]), pc(hold), yes(j["above"]["equal_all_held"]), pc(top7), pc(j["twin_median_gain_pct"]), f"{j['twin_percentile']:.1f}",
                     yes(j["above"]["twins_pass_percentile"]), yes(j["clears_all_marks"])))
    L += ["", f"MEASURED. Holding all 20 coins and the top 7-day rise rule are the same in every run, because the months and coins are the same.", "",
          "## Month by month", "", f"MEASURED. Each month's gain at {fk} bps per side.", "",
          row("Month", "Run 1", "Run 2", "Run 3", "Median of three", "Holding all 20", "Top 7-day rise rule"),
          row("---", "---:", "---:", "---:", "---:", "---:", "---:")]
    for m in months:
        p = per[m]
        L.append(row(m, *(pc(p[k]) for k, _, _ in RUNS), pc(shown["per_month_median"][m]["median_gain_pct"]), pc(p["y"][0]), pc(p["y"][1])))
    L += ["", f"## Without {bname}", ""]
    L.append(f"MEASURED. Best month of each run: {', '.join(f'{n} {S[k]['best_month']}' for k, _, n in RUNS)}. Joined without it: "
             + "; ".join(f"{n} {pc(S[k]['joined_without_best_month_gain_pct'])}" for k, _, n in RUNS) + ".")
    L += ["", "## May against the simple rule", ""]
    L.append(f"MEASURED. In May the top 7-day rise rule (hold the coins that rose most over the last 7 days) made {pc(may_rule.pop())}. "
             "The model made " + "; ".join(f"{n} {pc(S[k]['may']['gain_pct'])}" for k, _, n in RUNS)
             + f". The model was above the rule in {above7} of 3 runs.")
    L += ["", "## Limits", "", f"STATED. {shown['limit']}", "",
          "STATED. Three runs is a small count. A model may still know this period if it falls before its knowledge line; UNKNOWN how much that helps it. "
          "The six-model comparison of plan TM06 is still being scored and is not part of this page.", "",
          "## Run record", "",
          "MEASURED. The figures above come from these saved files, kept off repo, checked against their fingerprints by `tools/report_saved_tm06r.py`:", ""]
    L += [f"- {f}, SHA-256 `{PINS[f]}`" for f in PINS]
    L += ["", f"MEASURED. Each result file holds 8 of 8 picker sessions with no session missing and {res['results_tm06_g2.json']['twin_draws']} twin draws "
          "per session. Sessions TM06-P-g-*, TM06-P-g2-* and TM06-P-g3-* are listed in `timemachine/SESSIONS.jsonl`.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", type=Path, help="off-repo folder holding the four saved files")
    a = ap.parse_args()
    data = {}
    for f, h in PINS.items():
        b = (a.folder / f).read_bytes()
        if sha256(b).hexdigest() != h: ap.exit(1, f"TM06R_REPORT_PIN {f}\n")
        data[f] = json.loads(b)
    print(render({f: data[f] for _, f, _ in RUNS}, data["results_tm06_r_shown.json"]), end="")


if __name__ == "__main__":
    main()
