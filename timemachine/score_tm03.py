"""Scores plan TM03 (the model sets how much bitcoin to hold) from the finished session folders. Pretend money only.

python3 timemachine/score_tm03.py           writes timemachine/results_tm03.json and docs/research/34_time_machine_tm03_bitcoin_dial.md
python3 timemachine/score_tm03.py --check   exits 1 if the stored files differ from what the session folders give now

For every finished session named TM03-D01-<MODEL>-<YYYY-MM> under $TM_RUNS it runs the weights scorer
(timemachine/score_weights.py), which reads only the run records and the tape and stops if a replay of the model's answers
does not give the recorded final value to the cent. It changes nothing in the session folders.

A month counts for a model when its session has a result.json. The months, the symbol and the two method counts come from
tm03_plan in config/thresholds.yaml, the pass percentile from tm_weights_pass_percentile. The judged set is shuffle_runs.
shuffle (day by day) and shuffle_decisions are printed and not judged. The pass lines are said as "not finished" until every
month of a model is in; the method line until every model is finished.

The gain split by driver: the month is cut where the model's target changed (the opening position is the first stretch).
Each stretch runs from the book value just before its change is filled to the book value just before the next change (or the
end). Its gain is that difference, so the stretches add up to the month's gain. Its gain against holding is the stretch's gain
less what the same starting value would have made holding bitcoin over the same stretch. Each stretch is filed under the
driver the model gave with the answer that started it ("opening" for the first stretch when the model kept the opening
position, "not given" if it gave none)."""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S, weights as W, score_weights as SW
from timemachine.tape import Tape

OUT, DOC = "timemachine/results_tm03.json", "docs/research/34_time_machine_tm03_bitcoin_dial.md"
PLAN, CARD, BRIEF = "timemachine/PLAN_TM03_bitcoin_dial.md", "practice/traders/D01_bitcoin_dial.md", "timemachine/TRADER_BRIEF_WEIGHTS.md"
MODELS = [("OPUS", "Claude Opus 5.5"), ("SOL", "GPT-6.2 Sol"), ("NEON", "Gemini Neon"), ("SONNET", "Claude Sonnet 5.5"), ("KIMI", "Kimi K3"), ("GROK", "Grok 4.7")]
MONTH_NAMES = {"01": "January", "02": "February", "03": "March", "04": "April", "05": "May", "06": "June", "07": "July", "08": "August",
               "09": "September", "10": "October", "11": "November", "12": "December"}


def flow(text):
    """Reads a one-line YAML flow value such as {symbol: BTC/USD, months: ["2026-04", "2026-05"], wake_hour_utc: 0}."""
    i = 0

    def ws():
        nonlocal i
        while i < len(text) and text[i] in " \t":
            i += 1

    def val():
        nonlocal i
        ws(); c = text[i]
        if c == "{":
            i += 1; out = {}
            while True:
                ws()
                if text[i] == "}":
                    i += 1; return out
                k = scalar(":"); i += 1; out[k] = val(); ws()
                if text[i] == ",":
                    i += 1
        if c == "[":
            i += 1; out = []
            while True:
                ws()
                if text[i] == "]":
                    i += 1; return out
                out.append(val()); ws()
                if text[i] == ",":
                    i += 1
        return scalar(",]}")

    def scalar(stops):
        nonlocal i
        ws()
        if text[i] in "\"'":
            q = text[i]; j = text.index(q, i + 1); v = text[i + 1:j]; i = j + 1; return v
        j = i
        while j < len(text) and text[j] not in stops:
            j += 1
        v = text[i:j].strip(); i = j
        for f in (int, float):
            try:
                return f(v)
            except ValueError:
                pass
        return {"true": True, "false": False}.get(v, v)
    return val()


def plan_config(name="tm03_plan", path=ROOT / "config" / "thresholds.yaml"):
    key = None
    for line in open(path):
        if line[:1].isalpha():
            key = line.split(":")[0]
        elif key == name and line.startswith("  value:"):
            return flow(line.split("value:", 1)[1].strip())
    raise KeyError(f"{name} is not in config/thresholds.yaml")


def tm03_config():
    cfg = W.full_config(); cfg["tm03_plan"] = plan_config(); return cfg


def sid(tag, month):
    return f"TM03-D01-{tag}-{month}"


def cents(x):
    return None if x is None else round(x, 2)


def stretches(meta, res, cfg, tape):
    """The month cut at each change of target. Returns rows with driver, wakes, gain_usd and gain_vs_hold_usd."""
    table = W.price_table(tape, meta); sym = meta["benchmark"]
    book, recs, final = W.run_answers(meta, table, [st["asked"] for st in res["steps"]], cfg)
    opening = W.norm(meta.get("opening") or {}); targets = [W.norm(st["target"]) for st in res["steps"]]

    def px(k):  # bitcoin at wake k, at the same prices the book was valued at (the fill opens), or the end marks after the last wake
        if k >= len(targets):
            return table["end_marks"][sym]
        f = table["rows"][k]["fills"].get(sym)
        return f[1] if f else table["rows"][k]["marks"][sym]
    cuts = [k for k in range(len(targets)) if (targets[k] != (targets[k - 1] if k else opening))]
    starts = ([0] if not cuts or cuts[0] != 0 else []) + cuts; out = []
    for j, k in enumerate(starts):
        nxt = starts[j + 1] if j + 1 < len(starts) else len(targets)
        v0 = recs[k]["value_before"]; v1 = recs[nxt]["value_before"] if nxt < len(targets) else final
        changed = k in cuts
        drv = (res["steps"][k].get("driver") or "not given") if changed else "opening"
        out.append(dict(start_utc=meta["wakes"][k], wakes=nxt - k, changed=changed, driver=drv, target=targets[k].get(sym, 0.0),
                        gain_usd=v1 - v0, gain_vs_hold_usd=(v1 - v0) - v0 * (px(nxt) / px(k) - 1)))
    return out, len(cuts)


def month_row(tag, month, plan, cfg_all, tape):
    s = sid(tag, month); d = S.runs_dir() / s
    if not (d / "result.json").exists():
        return dict(session=s, finished=False, started=(d / "session.json").exists()), None
    meta = json.loads((d / "session.json").read_text()); res = json.loads((d / "result.json").read_text())
    sc = SW.score(s, tape=tape); cfg = res["config"]; start = cfg["tm_account_start_usd"]
    hold = sc["twins"][f"hold_{meta['benchmark']}"]["stats"]; m = sc["model_stats"]
    st, changes = stretches(meta, res, cfg, tape)
    tw = {k: {a: b for a, b in sc["twins"][k].items() if not a.startswith("_")} for k in ("shuffle_runs", "shuffle", "shuffle_decisions")}
    row = dict(session=s, finished=True, wakes=sc["wakes"], gain_usd=cents(m["final_value_usd"] - start), hold_gain_usd=cents(hold["final_value_usd"] - start),
               above_hold=m["final_value_usd"] > hold["final_value_usd"], avg_weight=round(m["avg_weight"], 4), changes=changes,
               costs_usd=cents(m["costs_paid_usd"]), largest_drop_pct=round(m["largest_drop_pct"], 2), hold_largest_drop_pct=round(hold["largest_drop_pct"], 2),
               shuffle_runs=dict(model_percentile=tw["shuffle_runs"]["model_percentile"], above_pass_percentile=tw["shuffle_runs"]["model_above_pass_percentile"],
                                 runs=tw["shuffle_runs"]["runs"], distinct_orders=tw["shuffle_runs"]["distinct_orders"], note=tw["shuffle_runs"].get("note"),
                                 median_gain_usd=cents(tw["shuffle_runs"]["final_gain_pct"]["median"] * start / 100)),
               shuffle_not_judged=dict(model_percentile=tw["shuffle"]["model_percentile"], median_costs_usd=cents(tw["shuffle"]["costs_paid_usd"]["median"])),
               shuffle_decisions_not_judged=dict(model_percentile=tw["shuffle_decisions"]["model_percentile"], median_costs_usd=cents(tw["shuffle_decisions"]["costs_paid_usd"]["median"])),
               drivers={}, config_hash=meta.get("config_hash"), git_commit=(meta.get("git") or {}).get("commit"))
    for x in st:
        g = row["drivers"].setdefault(x["driver"], dict(stretches=0, wakes=0, gain_usd=0.0, gain_vs_hold_usd=0.0))
        g["stretches"] += 1; g["wakes"] += x["wakes"]; g["gain_usd"] += x["gain_usd"]; g["gain_vs_hold_usd"] += x["gain_vs_hold_usd"]
    for g in row["drivers"].values():
        g["gain_usd"] = cents(g["gain_usd"]); g["gain_vs_hold_usd"] = cents(g["gain_vs_hold_usd"])
    return row, sc


def build(cfg=None, tape=None):
    cfg = cfg or tm03_config(); plan = cfg["tm03_plan"]; pp = cfg["tm_weights_pass_percentile"]; months = plan["months"]
    tape = tape or Tape(); start = cfg["tm_account_start_usd"]
    o = dict(plan=PLAN, months=months, pass_percentile=pp, judged_set="shuffle_runs", account_start_usd=start,
             method_min_models_beating_hold=plan["method_min_models_beating_hold"], method_min_models_beating_shuffles=plan["method_min_models_beating_shuffles"], models={})
    for tag, name in MODELS:
        rows, scs = {}, []
        for mo in months:
            r, sc = month_row(tag, mo, plan, cfg, tape); rows[mo] = r
            if sc:
                scs.append(sc)
        done = [mo for mo in months if rows[mo]["finished"]]; complete = len(done) == len(months)
        m = dict(name=name, months=rows, months_counted=done, complete=complete)
        if scs:
            su = SW.sum_results(scs); sr = su["sets"]["shuffle_runs"]; h = su["sets"][f"hold_{plan['symbol']}"]
            drv = {}
            for mo in done:
                for k, g in rows[mo]["drivers"].items():
                    t = drv.setdefault(k, dict(stretches=0, wakes=0, gain_usd=0.0, gain_vs_hold_usd=0.0))
                    for f in t:
                        t[f] += g[f]
            m.update(sum_gain_usd=cents(su["model_gain_pct_sum"] * start / 100), sum_hold_usd=cents(h["gain_pct_sum"] * start / 100),
                     sum_costs_usd=cents(su["model_costs_paid_usd_sum"]), sum_changes=sum(rows[mo]["changes"] for mo in done),
                     sum_shuffle_runs=dict(model_percentile=sr["model_percentile"], above_median=sr["model_above_median"], above_pass_percentile=sr["model_above_pass_percentile"],
                                           median_gain_usd=cents(sr["median_gain_pct_sum"] * start / 100), distinct_orders=sr.get("distinct_orders"), note=sr.get("note")),
                     sum_shuffle_not_judged=dict(model_percentile=su["sets"]["shuffle"]["model_percentile"]),
                     sum_shuffle_decisions_not_judged=dict(model_percentile=su["sets"]["shuffle_decisions"]["model_percentile"]),
                     drivers={k: dict(v, gain_usd=cents(v["gain_usd"]), gain_vs_hold_usd=cents(v["gain_vs_hold_usd"])) for k, v in sorted(drv.items())})
            l1 = m["sum_gain_usd"] > m["sum_hold_usd"]; l2 = bool(sr["model_above_pass_percentile"])
            m.update(line1_so_far=l1, line2_so_far=l2)
        if complete:
            m.update(line1=m["line1_so_far"], line2=m["line2_so_far"])
            m["verdict"] = "passes both lines" if (m["line1"] and m["line2"]) else "passes line 1 only" if m["line1"] else "passes line 2 only" if m["line2"] else "passes neither line"
        else:
            m.update(line1="not finished", line2="not finished", verdict="not finished")
        o["models"][tag] = m
    rows_all = [r for m in o["models"].values() for r in m["months"].values()]
    o["sessions"] = dict(planned=len(rows_all), finished=sum(1 for r in rows_all if r["finished"]),
                         running=sum(1 for r in rows_all if not r["finished"] and r["started"]), not_started=sum(1 for r in rows_all if not r["finished"] and not r["started"]))
    all_done = all(m["complete"] for m in o["models"].values())
    n1 = sum(1 for m in o["models"].values() if m.get("line1_so_far")); n2 = sum(1 for m in o["models"].values() if m.get("line2_so_far"))
    o["method"] = dict(complete=all_done, models_line1_so_far=n1, models_line2_so_far=n2,
                       verdict=("shown" if (n1 >= o["method_min_models_beating_hold"] and n2 >= o["method_min_models_beating_shuffles"]) else "not shown") if all_done else "not finished")
    return o


def usd(x):
    return "n/a" if x is None else (f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}")


def pc(x):
    return "n/a" if x is None else f"{x:.1f}"


def yn(x):
    return "n/a" if x is None else x if isinstance(x, str) else ("yes" if x else "no")


def runs_cell(r):
    t = r["shuffle_runs"]
    if t["note"]:
        return t["note"]
    return pc(t["model_percentile"]) + (f" (of {t['distinct_orders']} orders)" if t["distinct_orders"] else "")


def month_label(mo, cfg):
    if "-" not in mo:
        return mo
    y, m = mo.split("-")[:2]; last = str(cfg["tm03_plan"].get("last_day", ""))
    name = MONTH_NAMES.get(m, mo)
    return f"{name} 1 to {int(last[8:10])}, {y}" if (last.startswith(f"{y}-{m}") and len(last) >= 10) else f"{name} {y}"


def doc(o, cfg):
    plan = cfg["tm03_plan"]; n_months = len(o["months"]); pp = o["pass_percentile"]
    L = ["# Time machine plan TM03: six AI models set how much bitcoin to hold", "",
         f"Made by `timemachine/score_tm03.py` from `{OUT}`. Do not edit by hand. Pretend money. The plan, with its pass mark fixed before any session ran, is `{PLAN}`.", "",
         f"Sessions in: {o['sessions']['finished']} of {o['sessions']['planned']} are finished and scored here. {o['sessions']['running']} are running and {o['sessions']['not_started']} are not started; those are left out until they finish.", "",
         "## What was asked", "",
         "- Can a model that reads prices and dated headlines once a day decide well how much bitcoin to hold, starting fully invested?",
         "- It does not pick trades. It answers one number at each wake: the share of the account to hold in BTC/USD. The rest is cash.", "",
         "## How it ran", "",
         f"- Each model follows the card `{CARD}` and the brief `{BRIEF}`, one session per month, a fresh agent per session, a fresh account of `tm_account_start_usd` each month.",
         f"- Months: `tm03_plan.months` ({n_months} months, from {month_label(o['months'][0], cfg)} to {month_label(o['months'][-1], cfg)}).",
         "- The account starts fully in bitcoin, bought at the first minute of the month with costs.",
         "- One wake a day at `tm03_plan.wake_hour_utc`. The desk moves the book to the answer at the open of the next recorded minute. A change smaller than `tm_weights_min_change` is not traded. Nothing happens between wakes.",
         "- Costs on the part traded: the fee `practice_crypto_fee_bps_added` and the spread `tm_crypto_half_spread_bps`.",
         "- Each packet holds prices, trailing returns from closed daily bars, the book, and the crypto headlines since the last wake. The trader may look up more bars and headlines.",
         "- Yardsticks. Hold: the same account never changed after the first minute. Shuffled stretches (`shuffle_runs`, the judged set): the model's month cut into stretches of days with the same share, put back in a random order, `tm_weights_twin_draws` times, with the same costs.",
         "- Also printed and not judged: `shuffle` (the daily shares one by one in random order, which trades far more and pays more costs) and `shuffle_decisions` (the model's new shares moved among its own change days).", "",
         "## What would count", "",
         "From the plan, fixed before any session ran. For one model, over all months added up:", "",
         "- Line 1: its gain in dollars is above the gain from holding.",
         f"- Line 2: its gain is above percentile `tm_weights_pass_percentile` ({pp}) of its own shuffled stretches, added up draw by draw over the same months. A tie counts against the model. A model that never moves ties with everything and has shown nothing.",
         f"- For the method: at least `tm03_plan.method_min_models_beating_hold` ({o['method_min_models_beating_hold']}) of the models meet line 1 and at least `tm03_plan.method_min_models_beating_shuffles` ({o['method_min_models_beating_shuffles']}) meet line 2. Fewer, and it is reported as not shown.",
         "- A line is said as not finished until every month of that model is in.", "",
         "## Where each model stands", "",
         "MEASURED, pretend money, months finished so far, added up. \"Percentile\" is the share of summed shuffled-stretch draws that ended strictly below the model.", "",
         "| Model | Months counted | Gain summed | Holding, same months | Shuffled stretches: median | Percentile | Line 1 | Line 2 | Verdict |", "|---|---|---|---|---|---|---|---|---|"]
    for tag, _ in MODELS:
        m = o["models"][tag]; n = len(m["months_counted"])
        if not n:
            L.append(f"| {m['name']} | 0 of {n_months} | n/a | n/a | n/a | n/a | not finished | not finished | not finished |"); continue
        sr = m["sum_shuffle_runs"]; pcell = sr["note"] or pc(sr["model_percentile"]) + (f" (of {sr['distinct_orders']} orders)" if sr["distinct_orders"] else "")
        l1 = m["line1"] if m["complete"] else f"not finished (so far {yn(m['line1_so_far'])})"
        l2 = m["line2"] if m["complete"] else f"not finished (so far {yn(m['line2_so_far'])})"
        L.append(f"| {m['name']} | {n} of {n_months} | {usd(m['sum_gain_usd'])} | {usd(m['sum_hold_usd'])} | {usd(sr['median_gain_usd'])} | {pcell} | {yn(l1)} | {yn(l2)} | {m['verdict']} |")
    me = o["method"]
    L += ["", f"Method: {me['verdict']}. So far {me['models_line1_so_far']} of {len(MODELS)} models are above holding and {me['models_line2_so_far']} of {len(MODELS)} are above the pass percentile of their shuffled stretches, on the months each has finished.", ""]
    L += ["## Each model, month by month", "",
          "MEASURED. Gain and hold are in dollars on the month's account. \"Shuffled stretches\" is the judged percentile; when the number of different orders is under the draw count it is shown, and the percentile is coarse. \"Day by day\" and \"change days\" are the two shuffles that are not judged. \"Changes\" counts the wakes where the asked share differs from the one before, the opening position included.", ""]
    for tag, _ in MODELS:
        m = o["models"][tag]
        L += [f"### {m['name']}", "", "| Month | Gain | Hold | Shuffled stretches | Day by day (not judged) | Change days (not judged) | Average share held | Changes | Costs | Largest drop | Hold's largest drop |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for mo in o["months"]:
            r = m["months"][mo]
            if not r["finished"]:
                L.append(f"| {month_label(mo, cfg)} | {'running' if r['started'] else 'not started'} | | | | | | | | | |"); continue
            L.append(f"| {month_label(mo, cfg)} | {usd(r['gain_usd'])} | {usd(r['hold_gain_usd'])} | {runs_cell(r)} | {pc(r['shuffle_not_judged']['model_percentile'])} | "
                     f"{pc(r['shuffle_decisions_not_judged']['model_percentile'])} | {r['avg_weight']:.2f} | {r['changes']} | {usd(r['costs_usd'])} | {r['largest_drop_pct']:.1f}% | {r['hold_largest_drop_pct']:.1f}% |")
        L.append("")
    L += ["## Gain by what the model said drove each change", "",
          "MEASURED, months finished so far. The month is cut where the asked share changed. A stretch runs from just before its change is filled to just before the next change, so the stretches add up to the gain. \"Against holding\" is the stretch's gain less what holding bitcoin would have made on the same money over the same wakes. \"Opening\" is the first stretch when the model kept the opening position.", "",
          "| Model | Driver | Stretches | Wakes | Gain | Against holding |", "|---|---|---|---|---|---|"]
    for tag, _ in MODELS:
        m = o["models"][tag]
        for k, g in (m.get("drivers") or {}).items():
            L.append(f"| {m['name']} | {k} | {g['stretches']} | {g['wakes']} | {usd(g['gain_usd'])} | {usd(g['gain_vs_hold_usd'])} |")
    L += ["", "## What it shows so far", "",
          f"- {o['sessions']['finished']} of {o['sessions']['planned']} sessions (one per model per month) are finished. {sum(1 for m in o['models'].values() if m['complete'])} of {len(MODELS)} models have all months in.",
          f"- On the months finished, {me['models_line1_so_far']} of {len(MODELS)} models gained more than holding, and {me['models_line2_so_far']} of {len(MODELS)} are above the pass percentile of their shuffled stretches.",
          "- No verdict is given for a model until all its months are in, and none for the method until every model is." if not me["complete"] else f"- The method verdict is: {me['verdict']}.", "",
          "## What it does not show", "",
          "- If bitcoin fell over these months, holding less beats holding without any skill. Line 1 alone is not a pass; line 2 is the test of timing.",
          "- When a model makes few changes, its stretches can be put in only a few orders, and its percentile can take only a few values. The tables show the number of orders when it is under the draw count.",
          "- The models read the same headlines and may move together. Six answers are then closer to one, and the counts are easier to reach by luck than they look.",
          "- Some headlines were edited after they were published. Those are marked `edited_later`, and the card says not to act on them.",
          "- Fills are assumed from recorded minute bars, not real. The rule against outside knowledge is given by instruction; lookups are logged, memory is not.",
          "- One run per model per month. Run-to-run variation is not measured.",
          "- The split by driver is what the model said, not a measure of what it used.", "",
          "## Files", "",
          f"- `{PLAN}`: the plan and its pass mark.",
          f"- `{CARD}` and `{BRIEF}`: what each trader was given.",
          "- `timemachine/weights.py`: the session and the book. `timemachine/score_weights.py`: the scorer and its twins.",
          f"- `timemachine/score_tm03.py`: writes this page and `{OUT}` from the session folders TM03-D01-<MODEL>-<YYYY-MM> under `$TM_RUNS`.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cfg = tm03_config(); o = build(cfg); js = json.dumps(o, indent=1, sort_keys=True) + "\n"; md = doc(o, cfg)
    out, dc = ROOT / OUT, ROOT / DOC
    if "--check" in argv:
        bad = [str(p.relative_to(ROOT)) for p, t in ((out, js), (dc, md)) if not p.exists() or p.read_text() != t]
        print("stale: " + ", ".join(bad) if bad else "ok"); sys.exit(1 if bad else 0)
    if "--out" in argv:  # for tests: write somewhere else
        base = Path(argv[argv.index("--out") + 1]); out, dc = base / Path(OUT).name, base / Path(DOC).name
    out.write_text(js); dc.write_text(md)
    print(f"sessions finished {o['sessions']['finished']} of {o['sessions']['planned']}, running {o['sessions']['running']}, not started {o['sessions']['not_started']}")
    for tag, _ in MODELS:
        m = o["models"][tag]
        print(tag, len(m["months_counted"]), m.get("sum_gain_usd"), m.get("sum_hold_usd"), (m.get("sum_shuffle_runs") or {}).get("model_percentile"), m["verdict"])


if __name__ == "__main__":
    main()
