"""Scores plan TM04 (the model picks which stocks to hold) from the finished session folders. Pretend money only.

python3 timemachine/score_tm04.py           writes timemachine/results_tm04.json and docs/research/36_time_machine_tm04_stock_basket.md
python3 timemachine/score_tm04.py --check   exits 1 if the stored files differ from what the session folders give now

For every finished session TM04-D02-<MODEL>-r1 and -r2 under $TM_RUNS it runs the weights scorer (timemachine/score_weights.py),
which reads only the run records and the tape and stops if a replay of the model's answers does not give the recorded final value
to the cent. It changes nothing in the session folders.

Judged, from the plan: for one run, its final gain is above the equal-weight hold of the list and above percentile
tm_weights_pass_percentile of its random baskets (a tie counts against the model). For the method, on run 1 of each model:
at least tm04_plan.method_min_models_above_median runs above the median of their random baskets and at least
tm04_plan.method_min_models_above_percentile above the pass percentile. Not judged and printed: SPY held, the shuffles
(shuffle_runs, shuffle, shuffle_decisions), and run 2 against run 1.

Adds and drops (after the fact, not judged). Prices are taken at the weekly wakes (the open of the fill minute, as the book
paid), with tm_adds_drops_before_weeks extra weekly wakes before the first one, made by the same wake rule, and the end marks.
For each swap (a week where the model's basket changed): an added stock's return over the tm_adds_drops_before_weeks wakes before
it was added and over the wakes it was held; a dropped stock's return over each count in tm_adds_drops_after_weeks after it was
dropped, and to the end. Each is also given less the equal-weight list (the mean return of all listed stocks over the same
dates). The random swaps: at each of the model's swap weeks, as many of the stocks held before the swap are dropped at random,
and as many stocks not held are added at random; an added one is held for as many wakes as the model's add it stands for.
tm_weights_twin_draws draws, seeded from tm_weights_twin_seed and the session id. The model's mean is placed in the draws'
means, per run, per model (both runs) and pooled (all runs)."""
import datetime as dt
import json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S, weights as W, score_weights as SW
from timemachine.score_tm03 import plan_config, MODELS, usd, pc, yn
from timemachine.tape import Tape

OUT, DOC = "timemachine/results_tm04.json", "docs/research/36_time_machine_tm04_stock_basket.md"
PLAN, CARD, BRIEF = "timemachine/PLAN_TM04_stock_basket.md", "practice/traders/D02_stock_basket.md", "timemachine/TRADER_BRIEF_WEIGHTS.md"
RUNS_PER_MODEL = ("r1", "r2")
STATS = ("add_before", "add_held", "drop_after", "drop_to_end")


def sid(tag, run):
    return f"TM04-D02-{tag}-{run}"


def cents(x):
    return None if x is None else round(x, 2)


def r4(x):
    return None if x is None else round(x, 4)


def tm04_config():
    cfg = W.full_config(); cfg["tm04_plan"] = plan_config("tm04_plan")
    for k in ("tm_adds_drops_before_weeks", "tm_adds_drops_after_weeks", "tm_adds_drops_chance_pct"):
        cfg[k] = plan_config(k)
    return cfg


# ---- prices on the weekly grid
def grid(meta, table, tape, before):
    """Prices of every listed stock at each weekly wake, with `before` extra wakes ahead of the first (same rule), and the end.
    Returns (prices list of dicts, index of the session's first wake in it)."""
    w0 = S.parse(meta["wakes"][0]); d0 = (w0 - dt.timedelta(days=7 * (before + 2))).date().isoformat(); d1 = (w0 - dt.timedelta(days=1)).date().isoformat()
    pre, _ = W.make_wakes(tape, meta["market"], d0, d1, meta["wake_rules"])
    pre = [w for w in pre if w < w0][-before:] if before else []
    pre_meta = dict(meta, wakes=[S.iso(w) for w in pre], end_utc=meta["wakes"][0])
    pre_rows = W.price_table(tape, pre_meta)["rows"] if pre else []

    def at(row):
        return {s: (row["fills"][s][1] if row["fills"].get(s) else row["marks"].get(s)) for s in meta["symbols"]}
    px = [at(r) for r in pre_rows] + [at(r) for r in table["rows"]] + [{s: table["end_marks"].get(s) for s in meta["symbols"]}]
    return px, len(pre_rows)


def ret(px, s, a, b):
    """Return of stock s from grid point a to b, or None if either end is missing or out of range."""
    if a < 0 or b >= len(px) or a >= b:
        return None
    p0, p1 = px[a].get(s), px[b].get(s)
    return None if not p0 or not p1 else p1 / p0 - 1


def list_ret(px, syms, a, b):
    xs = [ret(px, s, a, b) for s in syms]; xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def events(targets, px, off, syms, before, afters, picks=None):
    """The add and drop events of a run. With picks (for a random draw) the added and dropped names are given per swap.
    Each event: stat name, raw return, return less the list. Grid point of session wake k is off + k; the end is len(px) - 1."""
    n = len(targets); end = len(px) - 1; out = {k: [] for k in STATS}; out.update({f"drop_after_{a}": [] for a in afters})
    names = [sorted(t) for t in targets]
    held_until = {}  # for the model: wake index at which each add was dropped (or the end)
    swaps = [k for k in range(1, n) if set(names[k]) != set(names[k - 1])]
    for j, k in enumerate(swaps):
        old, new = set(names[k - 1]), set(names[k])
        adds, drops = (sorted(new - old), sorted(old - new)) if picks is None else (picks[j][0], picks[j][1])
        for i, s in enumerate(adds):
            a = off + k
            if picks is None:
                stop = next((m for m in range(k + 1, n) if s not in names[m]), None)
                span = (off + stop) if stop is not None else end
            else:
                span = a + picks[j][2][i]
            add_ev(out, "add_before", px, syms, s, a - before, a)
            add_ev(out, "add_held", px, syms, s, a, span)
        for s in drops:
            d = off + k
            for w in afters:
                add_ev(out, f"drop_after_{w}", px, syms, s, d, d + w)
            add_ev(out, "drop_to_end", px, syms, s, d, end)
    out.pop("drop_after")
    return out, swaps


def add_ev(out, key, px, syms, s, a, b):
    r = ret(px, s, a, b); l = list_ret(px, syms, a, b)
    if r is not None and l is not None:
        out[key].append((r, r - l))


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def adds_drops(meta, res, table, tape, cfg, draws, seed):
    before, afters = int(cfg["tm_adds_drops_before_weeks"]), [int(a) for a in cfg["tm_adds_drops_after_weeks"]]
    px, off = grid(meta, table, tape, before); syms = meta["symbols"]; targets = [W.norm(st["target"]) for st in res["steps"]]; n = len(targets)
    model, swaps = events(targets, px, off, syms, before, afters)
    names = [sorted(t) for t in targets]; end = len(px) - 1
    spans = []  # per swap: the hold length (in grid points) of each model add, in the order of the sorted adds
    for k in swaps:
        adds = sorted(set(names[k]) - set(names[k - 1])); sp = []
        for s in adds:
            stop = next((m for m in range(k + 1, n) if s not in names[m]), None)
            sp.append(((off + stop) if stop is not None else end) - (off + k))
        spans.append((len(adds), len(set(names[k - 1]) - set(names[k])), sp))
    rand = []
    for i in range(draws):
        r = random.Random(f"adds_drops:{seed}:{meta['session']}:{i}"); picks = []
        for j, k in enumerate(swaps):
            na, nd, sp = spans[j]; old = names[k - 1]
            drops = r.sample(old, nd); adds = r.sample([s for s in syms if s not in old], na); picks.append((adds, drops, sp))
        ev, _ = events(targets, px, off, syms, before, afters, picks=picks); rand.append(ev)
    return dict(model=model, rand=rand, swaps=len(swaps), keys=[k for k in model])


def place(model_lists, rand_lists, chance):
    """model_lists: list of (raw, less list) events; rand_lists: per draw, the same. Returns the model's means and where they sit."""
    if not model_lists:
        return dict(events=0)
    mr, ml = mean([x[0] for x in model_lists]), mean([x[1] for x in model_lists])
    dm = [mean([x[1] for x in d]) for d in rand_lists if d]; dr = [mean([x[0] for x in d]) for d in rand_lists if d]
    below = 100.0 * sum(1 for v in dm if v < ml) / len(dm); above = 100.0 * sum(1 for v in dm if v > ml) / len(dm)
    dm_s = sorted(dm); med = (dm_s[(len(dm_s) - 1) // 2] + dm_s[len(dm_s) // 2]) / 2
    side = "higher than chance" if (100 - below) < chance else "lower than chance" if (100 - above) < chance else "within chance"
    return dict(events=len(model_lists), mean_raw_pct=r4(mr * 100), mean_less_list_pct=r4(ml * 100), random_median_less_list_pct=r4(med * 100),
                random_median_raw_pct=r4(sorted(dr)[len(dr) // 2] * 100), pct_random_below=round(below, 1), pct_random_above=round(above, 1), reading=side)


def pool(parts, key):
    """parts: list of adds_drops results; pools the model's events and, draw by draw, the random events."""
    m = [e for p in parts for e in p["model"][key]]
    nd = min(len(p["rand"]) for p in parts)
    r = [[e for p in parts for e in p["rand"][i][key]] for i in range(nd)]
    return m, r


# ---- the plan
def run_row(tag, run, cfg, tape):
    s = sid(tag, run); d = S.runs_dir() / s
    if not (d / "result.json").exists():
        return dict(session=s, finished=False, started=(d / "session.json").exists()), None
    meta = json.loads((d / "session.json").read_text()); res = json.loads((d / "result.json").read_text())
    sc = SW.score(s, tape=tape); rc = res["config"]; start = rc["tm_account_start_usd"]; m = sc["model_stats"]; tw = sc["twins"]
    hew = tw["hold_equal_weight"]["stats"]; spy = tw[f"hold_{meta['benchmark']}"]["stats"]; rb = tw["random_basket"]
    targets = [W.norm(st["target"]) for st in res["steps"]]
    swaps = sum(len(set(targets[k]) - set(targets[k - 1])) for k in range(1, len(targets)))
    row = dict(session=s, finished=True, wakes=sc["wakes"], gain_usd=cents(m["final_value_usd"] - start), gain_pct=r4(m["final_gain_pct"]),
               equal_weight_gain_usd=cents(hew["final_value_usd"] - start), spy_gain_usd_not_judged=cents(spy["final_value_usd"] - start),
               random_basket=dict(median_gain_usd=cents(rb["final_gain_pct"]["median"] * start / 100), model_percentile=rb["model_percentile"],
                                  above_median=rb["model_above_median"], above_pass_percentile=rb["model_above_pass_percentile"]),
               above_equal_weight=m["final_value_usd"] > hew["final_value_usd"],
               not_judged={k: dict(model_percentile=tw[k].get("model_percentile"), median_gain_usd=cents(tw[k]["final_gain_pct"]["median"] * start / 100), note=tw[k].get("note"))
                           for k in ("shuffle_runs", "shuffle", "shuffle_decisions")},
               names_swapped=swaps, costs_usd=cents(m["costs_paid_usd"]), largest_drop_pct=round(m["largest_drop_pct"], 2),
               equal_weight_largest_drop_pct=round(hew["largest_drop_pct"], 2), avg_weight=round(m["avg_weight"], 4),
               config_hash=meta.get("config_hash"), git_commit=(meta.get("git") or {}).get("commit"))
    row["passes"] = bool(row["above_equal_weight"] and row["random_basket"]["above_pass_percentile"])
    table = W.price_table(tape, meta)
    ac = dict(rc, **{k: cfg[k] for k in ("tm_adds_drops_before_weeks", "tm_adds_drops_after_weeks")})
    ad = adds_drops(meta, res, table, tape, ac, int(rc["tm_weights_twin_draws"]), int(rc["tm_weights_twin_seed"]))
    return row, dict(ad=ad, targets=targets)


def build(cfg=None, tape=None):
    cfg = cfg or tm04_config(); plan = cfg["tm04_plan"]; pp = cfg["tm_weights_pass_percentile"]; tape = tape or Tape(); chance = cfg["tm_adds_drops_chance_pct"]
    o = dict(plan=PLAN, pass_percentile=pp, judged_set="random_basket", runs_per_model=list(RUNS_PER_MODEL),
             method_min_models_above_median=plan["method_min_models_above_median"], method_min_models_above_percentile=plan["method_min_models_above_percentile"],
             adds_drops=dict(before_weeks=cfg["tm_adds_drops_before_weeks"], after_weeks=cfg["tm_adds_drops_after_weeks"], chance_pct=chance, per_run={}, per_model={}, pooled={}),
             models={})
    keep, allparts = {}, []
    for tag, name in MODELS:
        runs, parts = {}, []
        for run in RUNS_PER_MODEL:
            r, extra = run_row(tag, run, cfg, tape); runs[run] = r
            if extra:
                keep[(tag, run)] = extra; parts.append(extra["ad"]); allparts.append(extra["ad"])
                o["adds_drops"]["per_run"][r["session"]] = dict(swaps=extra["ad"]["swaps"], **{k: place(extra["ad"]["model"][k], [d[k] for d in extra["ad"]["rand"]], chance) for k in extra["ad"]["keys"]})
        m = dict(name=name, runs=runs)
        for run in RUNS_PER_MODEL:
            r = runs[run]; r["verdict"] = ("passes" if r["passes"] else "does not pass") if r["finished"] else ("running" if r["started"] else "not started")
        if all(runs[x]["finished"] for x in RUNS_PER_MODEL):
            a, b = keep[(tag, "r1")]["targets"], keep[(tag, "r2")]["targets"]; k_ = min(len(a), len(b)); bs = plan["basket_size"]
            m["run_spread"] = dict(gain_gap_usd=cents(runs["r1"]["gain_usd"] - runs["r2"]["gain_usd"]),
                                   mean_names_in_common=r4(sum(len(set(a[i]) & set(b[i])) for i in range(k_)) / k_),
                                   mean_share_in_common=r4(sum(len(set(a[i]) & set(b[i])) for i in range(k_)) / k_ / bs),
                                   percentile_gap=None if runs["r1"]["random_basket"]["model_percentile"] is None else round(runs["r1"]["random_basket"]["model_percentile"] - runs["r2"]["random_basket"]["model_percentile"], 1))
        if parts:
            o["adds_drops"]["per_model"][tag] = {k: place(*pool(parts, k), chance) for k in parts[0]["keys"]}
        o["models"][tag] = m
    if allparts:
        o["adds_drops"]["pooled"] = {k: place(*pool(allparts, k), chance) for k in allparts[0]["keys"]}
    rows = [r for m in o["models"].values() for r in m["runs"].values()]
    o["sessions"] = dict(planned=len(rows), finished=sum(1 for r in rows if r["finished"]), running=sum(1 for r in rows if not r["finished"] and r["started"]),
                         not_started=sum(1 for r in rows if not r["finished"] and not r["started"]))
    r1 = [m["runs"]["r1"] for m in o["models"].values()]; done = all(r["finished"] for r in r1)
    na = sum(1 for r in r1 if r["finished"] and r["random_basket"]["above_median"]); npp = sum(1 for r in r1 if r["finished"] and r["random_basket"]["above_pass_percentile"])
    o["method"] = dict(complete=done, run1_finished=sum(1 for r in r1 if r["finished"]), run1_above_median=na, run1_above_pass_percentile=npp,
                       verdict=("shown" if (na >= o["method_min_models_above_median"] and npp >= o["method_min_models_above_percentile"]) else "not shown") if done else "not finished")
    return o


STAT_LABEL = {"add_before": "added stock, weeks before it was added", "add_held": "added stock, while held", "drop_to_end": "dropped stock, to the end of the window"}


def label(k):
    n = k.split("_")[-1]
    return STAT_LABEL.get(k) or f"dropped stock, {n} week{'' if n == '1' else 's'} after it was dropped"


def order(block):
    """Measures in reading order: adds, then drops by weeks after, then to the end."""
    rank = lambda k: (0, 0) if k == "add_before" else (1, 0) if k == "add_held" else (3, 0) if k == "drop_to_end" else (2, int(k.split("_")[-1]))
    return sorted((k for k in block if isinstance(block[k], dict)), key=rank)


def pgap(x):
    return "n/a" if x is None else f"{x:+.1f}"


def pct(x):
    return "n/a" if x is None else f"{x:+.2f}%"


def doc(o, cfg):
    pp = o["pass_percentile"]; se = o["sessions"]; me = o["method"]; ad = o["adds_drops"]
    L = ["# Time machine plan TM04: six AI models pick which stocks to hold", "",
         f"Made by `timemachine/score_tm04.py` from `{OUT}`. Do not edit by hand. Pretend money. The plan, with its pass mark fixed before any session ran, is `{PLAN}`.", "",
         f"Sessions in: {se['finished']} of {se['planned']} are finished and scored here. Still running: {se['running']}. Not started: {se['not_started']}. Those are left out until they finish.", "",
         "## What was asked", "",
         "- Can a model that reads a week of prices, company filings and headlines choose a basket of stocks that does better than baskets drawn at random from the same list?",
         "- The account is always fully invested, so the test is of choosing, not of timing or of how much to hold.", "",
         "## How it ran", "",
         f"- Each model follows the card `{CARD}` and the brief `{BRIEF}`. One session per model covers the whole period. Each model runs twice with fresh agents, run 1 and run 2.",
         "- The list is `tm04_plan.symbols`. The period is `tm04_plan.start` to `tm04_plan.end`.",
         "- One wake a week, on the last regular trading day of the week at `tm04_plan.wake_time_ny` New York time. The model names exactly `tm04_plan.basket_size` stocks, held in equal shares. The desk trades only the difference, at the open of the next minute. A change smaller than `tm_weights_min_change` is not traded.",
         "- Costs: the spread `tm_stock_half_spread_bps` on what is traded. The account starts in cash.",
         "- Yardsticks. Judged: equal shares of the whole list held from the first wake, and random baskets (`random_basket`, `tm_weights_twin_draws` draws, swapping as many names each week as the model did). For scale only: SPY held. Also printed and not judged: the model's own baskets in shuffled order (`shuffle_runs`, `shuffle`, `shuffle_decisions`).", "",
         "## What would count", "",
         "From the plan, fixed before any session ran.", "",
         f"- For one run: its final gain is above the equal-weight hold of the list and above percentile `tm_weights_pass_percentile` ({pp}) of its random baskets. A tie counts against the model.",
         f"- For the method, on run 1 of each model: at least `tm04_plan.method_min_models_above_median` ({o['method_min_models_above_median']}) runs end above the median of their random baskets and at least `tm04_plan.method_min_models_above_percentile` ({o['method_min_models_above_percentile']}) end above the pass percentile. Fewer, and it is reported as not shown.",
         "- Run 2 is not part of the mark. It shows how much one model's answer changes from run to run.", "",
         "## Each run", "",
         "MEASURED, pretend money, in dollars on the account. \"Percentile\" is the share of random baskets that ended strictly below the run.", "",
         "| Model | Run | Gain | Equal-weight hold | Random baskets: median | Percentile | Above median | Above pass percentile | Passes | SPY (scale only) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for tag, _ in MODELS:
        m = o["models"][tag]
        for run in o["runs_per_model"]:
            r = m["runs"][run]
            if not r["finished"]:
                L.append(f"| {m['name']} | {run} | {r['verdict']} | | | | | | | |"); continue
            rb = r["random_basket"]
            L.append(f"| {m['name']} | {run} | {usd(r['gain_usd'])} | {usd(r['equal_weight_gain_usd'])} | {usd(rb['median_gain_usd'])} | {pc(rb['model_percentile'])} | {yn(rb['above_median'])} | {yn(rb['above_pass_percentile'])} | {r['verdict']} | {usd(r['spy_gain_usd_not_judged'])} |")
    L += ["", f"Method, on run 1: {me['verdict']}. {me['run1_finished']} of {len(MODELS)} first runs are in; {me['run1_above_median']} are above the median of their random baskets and {me['run1_above_pass_percentile']} above the pass percentile.", "",
          "## Not judged", "",
          "MEASURED. The model's own baskets put in another order: `shuffle_runs` (stretches with the same basket), `shuffle` (week by week) and `shuffle_decisions` (new baskets among the model's change weeks). These test when, not which. Also: names swapped over the run, costs paid, and the largest drop of the run and of the equal-weight hold.", "",
          "| Model | Run | Shuffled stretches | Week by week | Change weeks | Names swapped | Costs | Largest drop | Equal-weight largest drop |", "|---|---|---|---|---|---|---|---|---|"]
    for tag, _ in MODELS:
        m = o["models"][tag]
        for run in o["runs_per_model"]:
            r = m["runs"][run]
            if not r["finished"]:
                continue
            nj = r["not_judged"]; cell = lambda k: nj[k]["note"] or f"{pc(nj[k]['model_percentile'])} (median {usd(nj[k]['median_gain_usd'])})"
            L.append(f"| {m['name']} | {run} | {cell('shuffle_runs')} | {cell('shuffle')} | {cell('shuffle_decisions')} | {r['names_swapped']} | {usd(r['costs_usd'])} | {r['largest_drop_pct']:.1f}% | {r['equal_weight_largest_drop_pct']:.1f}% |")
    L += ["", "## Run 1 against run 2", "", "MEASURED, for models with both runs finished. Names in common: the mean, over the weeks, of how many of the basket's names the two runs held at the same time.", "",
          "| Model | Gain, run 1 less run 2 | Names in common each week | Share in common | Percentile, run 1 less run 2 |", "|---|---|---|---|---|"]
    for tag, _ in MODELS:
        m = o["models"][tag]; sp = m.get("run_spread")
        if sp:
            L.append(f"| {m['name']} | {usd(sp['gain_gap_usd'])} | {sp['mean_names_in_common']:.2f} | {sp['mean_share_in_common']:.2f} | {pgap(sp['percentile_gap'])} |")
    L += ["", "## Adds and drops", "",
          "Looked at after the fact, not judged, and not part of the plan's mark. It asks whether the stocks a model added had already risen, and whether the stocks it dropped then fell more than any dropped stock would.", "",
          f"- An added stock: its return over the `tm_adds_drops_before_weeks` ({ad['before_weeks']}) weekly wakes before it was added, and over the wakes it was held.",
          f"- A dropped stock: its return over each count of weekly wakes in `tm_adds_drops_after_weeks` ({', '.join(str(x) for x in ad['after_weeks'])}) after it was dropped, and to the end of the window.",
          "- \"Less the list\" is that return minus the mean return of all listed stocks over the same dates.",
          "- Random swaps: at each of the model's swap weeks, the same number of held stocks dropped at random and the same number of stocks not held added at random, `tm_weights_twin_draws` draws. \"Random below\" is the share of draws whose mean less the list is below the model's.",
          f"- The reading says \"lower than chance\" or \"higher than chance\" when fewer than `tm_adds_drops_chance_pct` ({ad['chance_pct']}) percent of draws reach the model's mean on that side, and \"within chance\" otherwise. It is a reading aid, not a mark.", ""]

    def table(title, block):
        if not block:
            return
        L.extend([f"### {title}", "", "| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |", "|---|---|---|---|---|---|---|---|"])
        for k in order(block):
            v = block[k]
            if not v.get("events"):
                continue
            L.append(f"| {label(k)} | {v['events']} | {pct(v['mean_raw_pct'])} | {pct(v['random_median_raw_pct'])} | {pct(v['mean_less_list_pct'])} | {pct(v['random_median_less_list_pct'])} | {v['pct_random_below']:.1f}% | {v['reading']} |")
        L.append("")
    table("All runs pooled", ad["pooled"])
    for tag, name in MODELS:
        done = [r for r, x in o["models"][tag]["runs"].items() if x["finished"]]
        table(f"{name}, {'both runs' if len(done) == 2 else 'run ' + ', '.join(d[1:] for d in done) + ' only'}", ad["per_model"].get(tag))
    pooled = ad["pooled"] or {}
    d_keys = [k for k in order(pooled) if k.startswith("drop_")]
    fell_more = [k for k in d_keys if pooled[k].get("reading") == "lower than chance"]
    fell_less = [k for k in d_keys if pooled[k].get("reading") == "higher than chance"]
    L += ["What the pooled table says about drops, in plain words:", ""]
    if not d_keys:
        L.append("- No finished run has a swap yet.")
    else:
        for k in d_keys:
            v = pooled[k]
            if not v.get("events"):
                continue
            L.append(f"- {label(k).capitalize()}: the model's drops moved {pct(v['mean_raw_pct'])}, random drops at the same weeks {pct(v['random_median_raw_pct'])} (median). Against the list: {pct(v['mean_less_list_pct'])} and {pct(v['random_median_less_list_pct'])}. {v['pct_random_below']:.1f}% of random draws did worse than the model's drops. Reading: {v['reading']}.")
        L.append(f"- The model's drops fell by more than random drops, beyond chance, on {len(fell_more)} of {len(d_keys)} drop measures. They fell by less than random drops, beyond chance, on {len(fell_less)}.")
        L.append("- So the plain answer: " + ("on these measures, what the model drops then falls about as much as any stock dropped from its basket at the same weeks would. The fall matches the falling market and the basket, not the choice." + (" At " + ", ".join(label(k).split(", ")[1].replace(" after it was dropped", "").replace("to the end of the window", "the end") for k in fell_less) + " after the drop, the model's drops did better than random drops, so the model let go of stocks that later recovered." if fell_less else "") if not fell_more else "on some measures the model's drops fell by more than random drops would; see which above, and note that many measures were looked at."))
    adds = [k for k in ("add_before", "add_held") if pooled.get(k, {}).get("events")]
    if adds:
        L += ["", "What the pooled table says about adds, in plain words:", ""]
        for k in adds:
            v = pooled[k]
            L.append(f"- {label(k).capitalize()}: {pct(v['mean_less_list_pct'])} against the list, random adds {pct(v['random_median_less_list_pct'])} (median). {v['pct_random_below']:.1f}% of random draws were below. Reading: {v['reading']}.")
    L += ["", "Many measures are looked at here, per model and pooled. At the 5 percent reading, about one in twenty would read beyond chance by luck alone.".replace("5 percent", f"`tm_adds_drops_chance_pct` ({ad['chance_pct']}) percent").replace("one in twenty", "that share")]
    L += ["", "## What it shows so far", "",
          f"- {se['finished']} of {se['planned']} sessions are finished. {me['run1_finished']} of {len(MODELS)} first runs are in.",
          f"- Of the runs finished, {sum(1 for m in o['models'].values() for r in m['runs'].values() if r['finished'] and r['passes'])} pass the plan's line for a run.",
          "- No method verdict is given until every first run is in." if not me["complete"] else f"- The method verdict is: {me['verdict']}.", "",
          "## What it does not show", "",
          "- About 25 weekly choices over one stretch of one market. One strong sector can carry a basket. A pass earns a longer test; it is not proof.",
          "- The list was picked with hindsight. Random baskets share that lean; SPY does not, so SPY is for scale only.",
          "- Models may like the same names. Six runs that agree are closer to one bet than to six.",
          "- The adds and drops section was chosen after the runs were seen. It can suggest a next test; it cannot pass or fail this one.",
          "- Fills are assumed from recorded minute bars. The rule against outside knowledge is given by instruction.", "",
          "## Files", "",
          f"- `{PLAN}`: the plan and its pass mark.", f"- `{CARD}` and `{BRIEF}`: what each trader was given.",
          "- `timemachine/weights.py`: the session and the book. `timemachine/score_weights.py`: the scorer and its twins.",
          f"- `timemachine/score_tm04.py`: writes this page and `{OUT}` from the session folders TM04-D02-<MODEL>-r1 and -r2 under `$TM_RUNS`.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cfg = tm04_config(); o = build(cfg); js = json.dumps(o, indent=1, sort_keys=True) + "\n"; md = doc(o, cfg)
    out, dc = ROOT / OUT, ROOT / DOC
    if "--check" in argv:
        bad = [str(p.relative_to(ROOT)) for p, t in ((out, js), (dc, md)) if not p.exists() or p.read_text() != t]
        print("stale: " + ", ".join(bad) if bad else "ok"); sys.exit(1 if bad else 0)
    if "--out" in argv:
        base = Path(argv[argv.index("--out") + 1]); out, dc = base / Path(OUT).name, base / Path(DOC).name
    out.write_text(js); dc.write_text(md)
    se = o["sessions"]; print(f"sessions finished {se['finished']} of {se['planned']}, running {se['running']}, not started {se['not_started']}")
    for tag, _ in MODELS:
        for run in RUNS_PER_MODEL:
            r = o["models"][tag]["runs"][run]
            print(tag, run, r.get("gain_usd"), r.get("equal_weight_gain_usd"), (r.get("random_basket") or {}).get("model_percentile"), r["verdict"])


if __name__ == "__main__":
    main()
