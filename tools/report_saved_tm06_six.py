"""Render the TM06 six-model result page (docs/research/102_time_machine_tm06_six_models.md) from the pinned saved outputs.
Reads three files kept off repo: the six-model result file written by timemachine/score_tm06.py over the six models' sessions and
the control, the April-to-June and July-to-November split built from it by the operator's tm06_p_split.py, and arm g's result file
(the same one pinned by tools/report_saved_tm06r.py). Does not open prices or score anything. Every figure on the page comes from
these files; the split and the Fable 5.2 comparison are worked out again here and checked against the files.
Run from the repo root:  python3 tools/report_saved_tm06_six.py FOLDER > docs/research/102_time_machine_tm06_six_models.md
Stops with TM06SIX_REPORT_PIN if a file differs from its fingerprint below."""
import argparse, json, re
from hashlib import sha256
from pathlib import Path

PINS = {
    "results_tm06_six_fast.json": "e50d82af23f731158bee11eaebbd0ed367fb56ebeeec41cdfdec87123cb35412",
    "tm06_six_p_split.json": "42311c02156e343a70522a1c8f7a3e9daa0bf33aca03effed5bf62255b7929e4",
    "results_tm06_g.json": "cd49fb4c86a74f02bd24866f18c3a07b5508a79e3edf32d04aa5a130aa2fdef5",
}
SPANS = [("2026-04_to_2026-06", "April to June"), ("2026-07_to_2026-11", "July to November")]
MAKER_JUNE = ["Claude Fable 5.2", "Claude Opus 5.5", "GPT-6.2 Sol"]
MON = {"2026-04": "April", "2026-05": "May", "2026-06": "June", "2026-07": "July", "2026-08": "August",
       "2026-09": "September", "2026-10": "October", "2026-11": "November"}
pc = lambda x: f"{x:+.2f}%"
row = lambda *c: "| " + " | ".join(map(str, c)) + " |"
yes = lambda b: "yes" if b else "no"


def config_value(key):
    m = re.search(rf"^{key}:\n  value: (.+)$", open("config/thresholds.yaml").read(), re.M)
    assert m, f"config key {key} not found"
    return m.group(1).strip()


def plan_value(key):
    m = re.search(rf"\b{key}: (\d+)", config_value("tm06_plan"))
    assert m, f"tm06_plan.{key} not found"
    return int(m.group(1))


def chain(gs):
    v = 1.0
    for g in gs:
        v *= 1 + g / 100.0
    return (v - 1) * 100


def ycol(d, name):
    return next(v for k, v in d.items() if k == name or k.startswith(name))


def render(six, split, g):
    pass_pct = int(config_value("tm_weights_pass_percentile"))
    need_med, need_all = plan_value("method_min_models_above_median"), plan_value("method_min_models_above_percentile")
    fees = six["fee_levels_bps"]
    sc = six["scores"]
    main = {s["main_fee_bps"] for s in sc.values() if s.get("part") in ("P", "S")}
    assert len(main) == 1 and plan_value("main_fee_bps") == main.copy().pop(); fee = main.pop(); fk = f"{fee:g}"
    P, S = six["joined"]["picker"], six["joined"]["swing"]
    models = sorted(P["models"])
    assert len(models) == 6 and sorted(S["models"]) == models
    assert len(six["sessions"]) == 73 and set(six["sessions"]) == set(sc), "not 73 scored sessions"
    assert P["need_above_median"] == need_med == S["need_above_median"] and P["need_all_marks"] == need_all == S["need_all_marks"]
    for part, J, n in (("picker", P, 8), ("swing", S, 4)):
        for m in models:
            r = J["models"][m]
            assert r["missing"] == [] and len(r["sessions"]) == n, f"{part} {m} is not complete"
        med = sum(J["models"][m]["above"]["twins_median"] for m in models)
        clr = sum(J["models"][m]["clears_all_marks"] for m in models)
        assert med == J["models_above_twin_median"] and clr == J["models_clearing_all_marks"]
        assert J["verdict"] == ("shown" if med >= need_med and clr >= need_all else "not shown"), f"{part}: verdict differs from the plan's rule"
    for m in models:
        a = P["models"][m]["above"]
        assert P["models"][m]["clears_all_marks"] == (a["equal_all_held"] and a["top_7d_rise"] and a["twins_pass_percentile"])
        a = S["models"][m]["above"]
        assert S["models"][m]["clears_all_marks"] == (ycol(a, "equal_hold") and a["twins_pass_percentile"])

    # Per session, picker
    pm = {}
    for sid, s in sc.items():
        if s.get("part") != "P": continue
        b = s["by_fee"][fk]; mon = s["window"]["start"][:7]
        y = (ycol(b["yardsticks"], "equal_all_held")["stats"]["final_gain_pct"], ycol(b["yardsticks"], "top_7d_rise")["stats"]["final_gain_pct"])
        pm.setdefault(mon, {"y": y})[s["model"]] = dict(gain=b["model"]["final_gain_pct"], pct=b["random_swap_twins"]["model_percentile"],
                                                        fees={f: s["by_fee"][f"{f:g}"]["model"]["final_gain_pct"] for f in fees})
        assert pm[mon]["y"] == y, f"yardsticks differ between models in {mon}"
    months = sorted(pm)
    assert len(months) == 8 and all(len(pm[x]) == 7 for x in months)
    for m in models:
        assert abs(chain(pm[x][m]["gain"] for x in months) - P["models"][m]["gain_pct"]) < 1e-6, f"{m}: months do not chain to the joined gain"
    hold = chain(pm[x]["y"][0] for x in months); top7 = chain(pm[x]["y"][1] for x in months)
    for m in models:
        assert abs(P["models"][m]["yardsticks_gain_pct"]["equal_all_held"] - hold) < 1e-6 and abs(P["models"][m]["yardsticks_gain_pct"]["top_7d_rise"] - top7) < 1e-6

    # Split, worked out again and checked against the split file
    assert split["shown_only"] and split["not_a_plan_mark"] and split["main_fee_bps"] == [fee]
    sp = {}
    for m in models:
        for key, _ in SPANS:
            a, z = split["spans"][key]; ms = [x for x in months if a <= x <= z]
            g_ = chain(pm[x][m]["gain"] for x in ms); h = chain(pm[x]["y"][0] for x in ms); t = chain(pm[x]["y"][1] for x in ms)
            f = split["models"][m][key]
            assert f["months"] == ms and abs(f["gain_pct"] - g_) < 1e-6 and abs(f["yardsticks_gain_pct"]["equal_all_held"] - h) < 1e-6 \
                and abs(f["yardsticks_gain_pct"]["top_7d_rise"] - t) < 1e-6, f"split file differs for {m} {key}"
            sp[(m, key)] = dict(gain=g_, hold=h, top7=t, above_hold=g_ > h, above_top7=g_ > t, months=ms)
    early, late = SPANS[0][0], SPANS[1][0]
    n_early_pos = sum(sp[(m, early)]["gain"] > 0 for m in models)
    n_late_neg = sum(sp[(m, late)]["gain"] < 0 for m in models)
    n_late_above_any = sum(sp[(m, late)]["above_hold"] or sp[(m, late)]["above_top7"] for m in models)
    n_early_both = sum(sp[(m, early)]["above_hold"] and sp[(m, early)]["above_top7"] for m in models)
    n_early_gt_joined = sum(sp[(m, early)]["gain"] > P["models"][m]["gain_pct"] for m in models)
    may100 = [m for m in models if pm["2026-05"][m]["pct"] >= 100.0]
    early_not_pos = [m for m in models if sp[(m, early)]["gain"] <= 0]

    # Swing, per session
    sw = {}
    for sid, s in sc.items():
        if s.get("part") != "S": continue
        sw[sid] = s
    for m in models:
        assert abs(chain(sw[x]["by_multiple"]["1x"][fk]["model"]["final_gain_pct"] for x in S["models"][m]["sessions"]) - S["models"][m]["gain_pct"]) < 1e-6

    # Fable 5.2 against the best of the six (plan: shown apart, not judged), worked out again
    cmp_ = {}
    for part, J in (("picker", P), ("swing", S)):
        (gname, gr), = g["joined"][part]["models"].items()
        assert gname == "Claude Fable 5.2" and gr["missing"] == []
        best = max(models, key=lambda m: J["models"][m]["gain_pct"])
        cmp_[part] = dict(g=gr, best=best, best_gain=J["models"][best]["gain_pct"], above=gr["gain_pct"] > J["models"][best]["gain_pct"])
    assert {s["window"]["start"][:7] for s in g["scores"].values() if s.get("part") == "P"} == set(months)
    assert g["scores"][next(k for k in g["scores"] if g["scores"][k].get("part") == "P")]["main_fee_bps"] == fee

    spreads = [v for s in sc.values() if s.get("part") in ("P", "S") for c, v in s["half_spread_bps"].items() if c != "BTC/USD"]
    clearP = [m for m in models if P["models"][m]["clears_all_marks"]]
    clearS = [m for m in models if S["models"][m]["clears_all_marks"]]
    medP = sum(P["models"][m]["above"]["twins_median"] for m in models)
    medS = sum(S["models"][m]["above"]["twins_median"] for m in models)
    names = lambda xs: ", ".join(xs) if xs else "none"

    L = ["# Time machine TM06: six models as hot-coin picker and swing trader", ""]
    L.append(f"MEASURED. Formal verdict by the marks fixed in `timemachine/PLAN_TM06_hot_coin_swing.md`: part P, the daily picker, is "
             f"{P['verdict']}; part S, the hourly swing trader, is {S['verdict']}. Picker: {medP} of 6 models ended above the median of their "
             f"random twins (needed `tm06_plan.method_min_models_above_median`, {need_med}) and {len(clearP)} cleared all three marks "
             f"(needed `tm06_plan.method_min_models_above_percentile`, {need_all}): {names(clearP)}. Both counts sit exactly at the minimum. "
             f"Swing: {medS} of 6 above the twin median, {len(clearS)} cleared both marks. Fee {fk} bps per side.")
    L += ["", f"MEASURED. What the split by month shows, in plain words: where the picker made money, it made it in April to June. In July to November "
          f"{'all six' if n_late_neg == 6 else f'{n_late_neg} of 6'} models lost money and "
          f"{'none' if n_late_above_any == 0 else f'{n_late_above_any}'} ended above either yardstick. "
          f"In April to June {n_early_pos} of 6 gained"
          + (f" ({names(early_not_pos)} did not)" if early_not_pos else "")
          + f" and {n_early_both} of 6 were above both yardsticks. In May {'all six' if len(may100) == 6 else f'{len(may100)} of 6'} models were at the "
          f"100th percentile of their random twins. The split is shown only and changes no mark; it was fixed in advance for the reason given below.", ""]
    L += ["STATED. The plan was logged before any session (ledger rows TM06-P-a to TM06-P-f and TM06-S-a to TM06-S-f, "
          "`research_rig/TRIAL_LEDGER.md`). Part P: 48 monthly sessions, six models, eight months April to November 2026, once a day up to "
          "`tm06_plan.picker_max_names` of 20 coins in equal parts at 1x, long only. Part S: 24 one-week sessions, six models, four fixed weeks "
          "(two falling, two rising), hourly, long or short, on the week's five coins. A first start of part P was void (shared working files) "
          "and is not scored here (`docs/STATUS.md`). All 73 sessions (48 P, 24 S and the control) were scored once by `timemachine/score_tm06.py`. "
          "STATED by the operator: through the off-repo wrapper that scores sessions in parallel, as for TM06-R; its side check found the "
          "result of each of the 72 trader sessions the same as that session's own score file, with 0 differing and 1 absent.", ""]

    L += ["## Part P: the picker, each model over eight months", "",
          f"MEASURED. Months joined by chaining each month's gain. Marks for one model: above yardstick 1 (holding all 20 coins, `equal_all_held`), "
          f"above yardstick 2 (holding the coins that rose most over the last 7 days, `top_7d_rise`), and strictly above the {pass_pct}th percentile "
          f"(`tm_weights_pass_percentile`) of {six['twin_draws']} twins that swap the picks at random.", "",
          row("Model", "Joined gain", "Above holding all 20", "Above top 7-day rise", "Twin median", "Twin percentile", f"Above {pass_pct}th percentile",
              "Above twin median", "Clears all marks"),
          row("---", "---:", "---", "---", "---:", "---:", "---", "---", "---")]
    for m in models:
        r = P["models"][m]; a = r["above"]
        L.append(row(m, pc(r["gain_pct"]), yes(a["equal_all_held"]), yes(a["top_7d_rise"]), pc(r["twin_median_gain_pct"]), f"{r['twin_percentile']:.1f}",
                     yes(a["twins_pass_percentile"]), yes(a["twins_median"]), yes(r["clears_all_marks"])))
    L += ["", f"MEASURED. Yardsticks over the same eight months: holding all 20 coins {pc(hold)}; top 7-day rise rule {pc(top7)}. "
          f"Method count: {medP} of 6 above the twin median (need {need_med}), {len(clearP)} of 6 clear all marks (need {need_all}). Verdict: {P['verdict']}.", ""]

    L += ["## Part P month by month", "", f"MEASURED. Each month's gain at {fk} bps per side.", "",
          row("Month", *models, "Holding all 20", "Top 7-day rise"), row("---", *["---:"] * (len(models) + 2))]
    for x in months:
        L.append(row(MON[x], *(pc(pm[x][m]["gain"]) for m in models), pc(pm[x]["y"][0]), pc(pm[x]["y"][1])))
    L += ["", f"MEASURED. Each month's percentile among its {six['twin_draws']} random twins.", "",
          row("Month", *models), row("---", *["---:"] * len(models))]
    for x in months:
        L.append(row(MON[x], *(f"{pm[x][m]['pct']:.1f}" for m in models)))
    L += ["", f"Why May happened, model by model: [doc 110](110_tm06_why_may.md). MEASURED: the six models bought coins already at the top of the screen; "
          f"May was the month the plain top_7d_rise rule paid by far the most ({pm['2026-05']['y'][1]:+.1f}%). Verdict: screen-based for all six, memory not ruled out."]

    L += ["", "## Part P split: April to June against July to November", "",
          "STATED. Why this split, fixed before any result was read: when the Claude Fable 5.2 arm was added (2026-11-25, before any g session "
          "and before any TM06 model score was read), the plan recorded that the maker states June 2026 as the reliable knowledge cutoff for "
          f"{', '.join(MAKER_JUNE[:-1])} and {MAKER_JUNE[-1]} (`docs/research/11_ai_trader_experiment_design.md`), so for those three the April to June "
          "sessions lie before the maker's stated knowledge line. Each model's picker months are therefore also shown split at that line "
          "(plan section \"Added arm: Claude Fable 5.2\"). For Claude Sonnet 5.5, Gemini Neon, Grok 4.7 and Kimi K3 that page gives no maker "
          "statement (UNKNOWN). The split is shown only and changes no mark. Twin percentiles are not split, because the result file holds no per-draw lists.", "",
          row("Model", "Span", "Gain", "Holding all 20", "Top 7-day rise", "Above holding all 20", "Above top 7-day rise"),
          row("---", "---", "---:", "---:", "---:", "---", "---")]
    for m in models:
        for key, lab in SPANS:
            d = sp[(m, key)]
            L.append(row(m, lab, pc(d["gain"]), pc(d["hold"]), pc(d["top7"]), yes(d["above_hold"]), yes(d["above_top7"])))
    L += ["", f"MEASURED. April to June: {n_early_pos} of 6 gained, {n_early_both} of 6 above both yardsticks; for {n_early_gt_joined} of 6 the April to June gain "
          f"is larger than the gain over all eight months. July to November: {n_late_neg} of 6 lost, {n_late_above_any} of 6 above either yardstick. "
          f"Of the models that cleared all picker marks ({names(clearP)}), {sum(m in MAKER_JUNE for m in clearP)} have a maker's stated June 2026 cutoff in `docs/research/11_ai_trader_experiment_design.md`.", ""]

    L += ["## Part S: the swing trader, each model over four weeks", "",
          f"MEASURED. Weeks joined by chaining, at 1x and {fk} bps per side. Marks for one model: above holding the week's five coins in equal parts, "
          f"and strictly above the {pass_pct}th percentile of {six['twin_draws']} twins that play the model's own answers in shuffled order.", "",
          row("Model", "Joined gain", "Holding the five", "Above holding the five", "Twin median", "Twin percentile", f"Above {pass_pct}th percentile",
              "Above twin median", "Clears both marks", "Rising weeks", "Falling weeks"),
          row("---", "---:", "---:", "---", "---:", "---:", "---", "---", "---", "---:", "---:")]
    for m in models:
        r = S["models"][m]; a = r["above"]; w = r["by_week_direction"]
        L.append(row(m, pc(r["gain_pct"]), pc(ycol(r["yardsticks_gain_pct"], "equal_hold")), yes(ycol(a, "equal_hold")), pc(r["twin_median_gain_pct"]),
                     f"{r['twin_percentile']:.1f}", yes(a["twins_pass_percentile"]), yes(a["twins_median"]), yes(r["clears_all_marks"]),
                     pc(w["rising"]["gain_pct"]), pc(w["falling"]["gain_pct"])))
    L += ["", f"MEASURED. Method count: {medS} of 6 above the twin median (need {need_med}), {len(clearS)} of 6 clear both marks (need {need_all}). Verdict: {S['verdict']}.", "",
          f"MEASURED, shown and not judged: trades, share of time in the market, and the answers carried at 2x and 3x at {fk} bps, joined over the four weeks.", "",
          row("Model", "Trades", "Mean time in market", "Carried 2x", "Carried 3x", "Forced close-outs 2x / 3x"), row("---", "---:", "---:", "---:", "---:", "---:")]
    for m in models:
        ss = [sw[x] for x in S["models"][m]["sessions"]]
        t = sum(s["by_multiple"]["1x"][fk]["model"]["trades"] for s in ss)
        tim = sum(s["by_multiple"]["1x"][fk]["model"]["time_in_market_share"] for s in ss) / len(ss)
        c2 = chain(s["by_multiple"]["2x"][fk]["model"]["final_gain_pct"] for s in ss); c3 = chain(s["by_multiple"]["3x"][fk]["model"]["final_gain_pct"] for s in ss)
        k2 = sum(s["by_multiple"]["2x"][fk]["model"]["closeouts"] for s in ss); k3 = sum(s["by_multiple"]["3x"][fk]["model"]["closeouts"] for s in ss)
        L.append(row(m, t, f"{tim * 100:.0f}%", pc(c2), pc(c3), f"{k2} / {k3}"))

    L += ["", "## Fees", "",
          f"MEASURED. Main fee `tm06_plan` main_fee_bps, {fk} bps per side; the other levels in `tm_perp_fee_levels_bps` are shown, not judged. "
          f"Every level also charges each coin's half spread ({min(spreads):.0f} to {max(spreads):.0f} bps, as stored with each session) and funding. "
          "Joined by chaining each session's gain at that fee.", "",
          row("Model", *(f"Picker at {f:g} bps" for f in fees), *(f"Swing at {f:g} bps" for f in fees)), row("---", *["---:"] * (2 * len(fees)))]
    for m in models:
        pf = [chain(pm[x][m]["fees"][f] for x in months) for f in fees]
        sf = [chain(sw[x]["by_multiple"]["1x"][f"{f:g}"]["model"]["final_gain_pct"] for x in S["models"][m]["sessions"]) for f in fees]
        L.append(row(m, *map(pc, pf), *map(pc, sf)))

    L += ["", "## Claude Fable 5.2 against the six", "",
          "STATED. Plan section \"Added arm: Claude Fable 5.2\": arm g was scored apart and never enters the six-model counts. Shown apart and not "
          f"judged: whether its joined result ends above the best of the six on the same months and weeks, at {fk} bps and 1x. Arm g itself is on "
          "page 78 (`docs/research/78_time_machine_tm06r_fable_repeat.md`).", ""]
    for part, lab in (("picker", "Picker, eight months"), ("swing", "Swing, four weeks")):
        c = cmp_[part]
        L.append(f"- MEASURED. {lab}: Claude Fable 5.2 {pc(c['g']['gain_pct'])}; best of the six {c['best']} {pc(c['best_gain'])}. Above the best of the six: {yes(c['above'])}.")

    L += ["", "## Limits", "",
          "STATED. Plan TM06's own list (\"How this can fool us\") applies in full. The points that matter most here, as written there or measured on this page:", "",
          "- One stretch of one year. The picker's result rests on April to June; July to November lost for every model.",
          "- Six models tend to like the same coins. If those led, all six look good together, and that is one bet, not six. In May all six were at the top of their twins.",
          "- The coin list is today's survivors. Coins that died are missing, which flatters every buyer; the yardsticks share the flattery, so only the comparisons mean anything, not the gains.",
          "- For three of the six the April to June months lie before the maker's stated knowledge line. UNKNOWN how much a model knows of that period, and UNKNOWN for the four models with no maker statement.",
          "- The picker's verdict met both method counts at exactly the minimum.",
          "- Four weeks is a small sample for part S."]
    L += ["", "STATED. The limits the scorer writes into the result file:", ""]
    L += [f"- {x}" for x in six["limits"]]
    L += ["", "## What the plan says follows", "",
          "STATED, from the plan: a pass in either part earns a longer test of that part on dates not used here, and does not earn real money. "
          "If a part does not pass, the write-up names which yardstick each model lost to: in part S each model's marks are in the table above.", "",
          "## Run record", "",
          "MEASURED. The figures above come from these saved files, kept off repo, checked against their fingerprints by `tools/report_saved_tm06_six.py`:", ""]
    L += [f"- {f}, SHA-256 `{PINS[f]}`" for f in PINS]
    L += ["", f"MEASURED. The six-model file holds {len(six['sessions'])} sessions (48 picker, 24 swing, 1 control), every model with all eight months "
          f"and all four weeks and none missing, and {six['twin_draws']} twin draws per session. The sessions are listed in `timemachine/SESSIONS.jsonl`.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", type=Path, help="off-repo folder holding the three saved files")
    a = ap.parse_args()
    data = {}
    for f, h in PINS.items():
        b = (a.folder / f).read_bytes()
        if sha256(b).hexdigest() != h: ap.exit(1, f"TM06SIX_REPORT_PIN {f}\n")
        data[f] = json.loads(b)
    print(render(data["results_tm06_six_fast.json"], data["tm06_six_p_split.json"], data["results_tm06_g.json"]), end="")


if __name__ == "__main__":
    main()
