"""Scores one finished weights session against its twins. Pretend money only. No server, no model.

python3 timemachine/score_weights.py SESSION [--draws N] [--seed S] [--json]
python3 timemachine/score_weights.py --sum SESSION SESSION ... [--json]   (one model's sessions, summed; see sum_sessions)

Numbers come only from the run records (session.json, result.json) and the tape. The tape is read again for every
wake (the same reads the session made), and the model's own answers are run again through the same book function
(timemachine/weights.py: step_book). The script stops if that replay does not give the recorded final value to the cent.

Printed for the model and each twin set:
  final gain        book value at the end against tm_account_start_usd, in percent
  largest drop      the largest fall from a high, over the book values at each wake and at the end, in percent
  average weight    time-weighted share of the book held in symbols (not cash), from the weights after each wake's fills
  turnover          dollars traded (at the open price) divided by tm_account_start_usd
  costs paid        spread and fee dollars paid
  percentile        for a twin set: the share of draws that ended strictly below the model, in percent (a tie counts
                    against the model); also whether the model is above the median and above tm_weights_pass_percentile
Twin sets (tm_weights_twin_draws draws each, seeded from tm_weights_twin_seed and the session id; same costs, same fill minutes):
  shuffle            the model's target at every wake (new or standing) put in a random order across the same wakes. It keeps
                     how much was held on average and takes away when (plan TM03). It moves at more wakes than the model,
                     so it pays more costs; its costs are printed next to it
  shuffle_decisions  only the model's own decisions (first wake and each wake where it set a new target) put in a random
                     order across those same wakes; the other wakes keep the standing target. Same number of moves
  shuffle_runs       the model's runs (consecutive wakes with one target; the first run starts at the opening wake) put back
                     in a random order, each keeping its length. Same targets for the same number of wakes, different timing.
                     A model with one run has no timing to judge, and no percentile is given. When the number of distinct
                     orders is under the draw count it is printed, so a reader sees when the percentile is coarse
  random_basket      stock sessions: the same number of names as the model, drawn at random; at each later wake as many
                     names swapped as the model swapped (plan TM04)
  hold_<benchmark>   the session's benchmark (BTC/USD or SPY) held from the first wake, bought with costs
  hold_equal_weight  equal shares of the allowed list held from the first wake
"""
import argparse, json, math, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S, weights as W
from timemachine.tape import Tape


def drawdown(values):
    hi, worst = None, 0.0
    for v in values:
        hi = v if hi is None or v > hi else hi
        if hi and hi > 0:
            worst = min(worst, v / hi - 1)
    return worst * 100


def stats(meta, recs, book, final, cfg):
    wakes = [S.parse(w) for w in meta["wakes"]]; end = S.parse(meta["end_utc"]); start = cfg["tm_account_start_usd"]
    times = [(wakes[i + 1] if i + 1 < len(wakes) else end) - w for i, w in enumerate(wakes)]
    tw = sum(sum(r["weights_after"].values()) * t.total_seconds() for r, t in zip(recs, times)) / sum(t.total_seconds() for t in times)
    return dict(final_value_usd=final, final_gain_pct=(final / start - 1) * 100, largest_drop_pct=drawdown([r["value_before"] for r in recs] + [final]),
                avg_weight=tw, turnover=book["traded_usd"] / start, traded_usd=book["traded_usd"], costs_paid_usd=book["spread_usd"] + book["fee_usd"],
                trade_wakes=sum(1 for r in recs if r["trades"]))


def pct_below(x, xs):
    """Share of draws that ended strictly below x, in percent. A tie counts against the model."""
    return 100.0 * sum(1 for v in xs if v < x) / len(xs) if xs else None


def summary(xs):
    xs = sorted(xs); n = len(xs)
    return dict(n=n, median=(xs[(n - 1) // 2] + xs[n // 2]) / 2 if n else None, low=xs[0] if n else None, high=xs[-1] if n else None)


def twin_set(name, runs, final, cfg):
    """runs: list of (book, final value) for one set of draws."""
    start = cfg["tm_account_start_usd"]; vals = [f for _, f in runs]; med = summary(vals)["median"]; pp = cfg.get("tm_weights_pass_percentile")
    xs = sorted(vals); cut = xs[min(len(xs) - 1, int(len(xs) * pp / 100.0))] if (pp is not None and xs) else None
    return dict(final_gain_pct=summary([(v / start - 1) * 100 for v in vals]), costs_paid_usd=summary([b["spread_usd"] + b["fee_usd"] for b, _ in runs]),
                model_percentile=pct_below(final, vals), model_above_median=final > med, model_above_pass_percentile=None if cut is None else final > cut,
                _draw_gains_pct=[(v / start - 1) * 100 for v in vals])


def judge(xs, x, pp):
    """Percentile (strictly below; a tie counts against the model), above median, above the pass percentile, for x against draws xs."""
    ys = sorted(xs); n = len(ys); med = (ys[(n - 1) // 2] + ys[n // 2]) / 2
    cut = ys[min(n - 1, int(n * pp / 100.0))] if pp is not None else None
    return dict(model_percentile=pct_below(x, ys), model_above_median=x > med, model_above_pass_percentile=None if cut is None else x > cut)


def key(t):
    return json.dumps(t, sort_keys=True)


def runs_of(targets):
    """Cuts a target series into runs: consecutive wakes with the same target. Returns [(target, length)]."""
    out = []
    for t in targets:
        if out and key(out[-1][0]) == key(t):
            out[-1][1] += 1
        else:
            out.append([t, 1])
    return [(t, n) for t, n in out]


def shuffle_runs_series(runs, seed, sid, i):
    """Draw i of the shuffle_runs twin: the runs in a random order, written back out as one target per wake."""
    t = list(runs); random.Random(f"shuffle_runs:{seed}:{sid}:{i}").shuffle(t)
    return [x for x, m in t for _ in range(m)]


def distinct_orders(runs):
    """How many different wake-by-wake series the runs can make when put in another order: L! / (product of c! over identical runs).
    Two runs are identical when they have the same target and the same length. (Orders that place equal targets next to each other
    are counted as made, so this is an upper bound on the distinct series.)"""
    c = {}
    for t, n in runs:
        c[(key(t), n)] = c.get((key(t), n), 0) + 1
    out = math.factorial(len(runs))
    for v in c.values():
        out //= math.factorial(v)
    return out


def score(session_id, tape=None, draws=None, seed=None):
    d = S.runs_dir() / session_id
    meta = json.loads((d / "session.json").read_text()); assert meta.get("kind") == "weights", "not a weights session"
    res = json.loads((d / "result.json").read_text()); cfg = res["config"]
    draws = int(draws if draws is not None else cfg["tm_weights_twin_draws"]); seed = int(seed if seed is not None else cfg["tm_weights_twin_seed"])
    tape = tape or Tape(meta.get("tape")); table = W.price_table(tape, meta)
    assert [st["row"] for st in res["steps"]] == table["rows"], "the tape gives other prices than the session recorded: it was changed after the run"
    answers = [st["asked"] for st in res["steps"]]; n = len(answers)
    book, recs, final = W.run_answers(meta, table, answers, cfg)
    assert round(final, 2) == round(res["final"]["value_usd"], 2), "the replay of the model's answers does not match the recorded final value"
    out = dict(session=session_id, model=meta["model"], trader=meta["trader"], market=meta["market"], wakes=n, window=meta["window"], costs=res["costs"],
               pass_percentile=cfg.get("tm_weights_pass_percentile"), model_stats=stats(meta, recs, book, final, cfg), twins={})
    run = lambda ans, m=meta: (lambda r: (r[0], r[2]))(W.run_answers(m, table, ans, cfg))
    targets = [st["target"] for st in res["steps"]]
    # shuffle: the model's target at every wake, in a random order across the same wakes (plan TM03, yardstick 2)
    sh = []
    for i in range(draws):
        t = list(targets); random.Random(f"shuffle:{seed}:{session_id}:{i}").shuffle(t); sh.append(run(t))
    out["twins"]["shuffle"] = twin_set("shuffle", sh, final, cfg)
    # shuffle_decisions: only the wakes where the model set a new target; the same number of moves at the same times
    cw = [k for k, st in enumerate(res["steps"]) if k == 0 or st["changed"]]; dec = [targets[k] for k in cw]; sd = []
    for i in range(draws):
        t = list(dec); random.Random(f"shuffle_decisions:{seed}:{session_id}:{i}").shuffle(t); pos = dict(zip(cw, t)); sd.append(run([pos.get(k) for k in range(n)]))
    out["twins"]["shuffle_decisions"] = twin_set("shuffle_decisions", sd, final, cfg); out["twins"]["shuffle_decisions"]["decision_wakes"] = len(cw)
    # shuffle_runs: the model's runs (consecutive wakes with one target, the first run starting at the opening wake) put back in a
    # random order, each keeping its length. Same targets held for the same number of wakes; different timing.
    rs = runs_of(targets); orders = distinct_orders(rs); sr = []
    for i in range(draws):
        sr.append(run(shuffle_runs_series(rs, seed, session_id, i)))
    out["twins"]["shuffle_runs"] = tr = twin_set("shuffle_runs", sr, final, cfg)
    tr["runs"] = len(rs); tr["distinct_orders"] = orders if orders < draws else None
    if orders <= 1:
        tr.update(model_percentile=None, model_above_median=None, model_above_pass_percentile=None, note="no timing to judge")
    if meta["market"] == "stocks":
        # random basket (plan TM04, yardstick 2): first wake, the same number of names as the model at random; each later wake,
        # as many names swapped as the model swapped (dropped at random from the twin's basket, added at random from the rest).
        # The twin's weights are the model's own weights that wake, given to its names in random order.
        rb = []
        for i in range(draws):
            r = random.Random(f"basket:{seed}:{session_id}:{i}"); ans, cur, prev = [], [], None
            for k, tg in enumerate(targets):
                names = sorted(x for x, v in tg.items() if v > 0)
                if prev is None:
                    cur = r.sample(meta["symbols"], len(names))
                elif set(names) != set(prev):
                    keep = len(set(names) & set(prev)); stay = r.sample(cur, min(keep, len(cur)))
                    cur = stay + r.sample([x for x in meta["symbols"] if x not in stay], len(names) - len(stay))
                elif tg == targets[k - 1]:
                    ans.append(None); prev = names; continue
                vals = [tg[x] for x in names]; r.shuffle(vals); ans.append(dict(zip(cur, vals))); prev = names
            rb.append(run(ans))
        out["twins"]["random_basket"] = twin_set("random_basket", rb, final, cfg)
    holds = {f"hold_{meta['benchmark']}": {meta["benchmark"]: 1.0}} if meta.get("benchmark") else {}
    holds["hold_equal_weight"] = {s: 1.0 / len(meta["symbols"]) for s in meta["symbols"]}
    for name, w in holds.items():
        m2 = dict(meta, opening=w); b2, r2, f2 = W.run_answers(m2, table, [None] * n, cfg)
        out["twins"][name] = dict(stats=stats(m2, r2, b2, f2, cfg), model_above=final > f2)
    return out


def public(r):
    """The output without the per-draw lists."""
    return dict(r, twins={k: {a: b for a, b in v.items() if not a.startswith("_")} for k, v in r["twins"].items()})


def sum_sessions(ids, tape=None, draws=None, seed=None):
    """Sums one model's sessions (for example its months): the model's gains added up, and for each twin set, draw by draw,
    draw i of the first session plus draw i of the second and so on. The percentile is of the summed model gain against the
    summed draws. Each session's draws are seeded from tm_weights_twin_seed and the session id, so the months draw independently and the sum is fixed by the session ids."""
    rs = [score(i, tape=tape, draws=draws, seed=seed) for i in ids]
    pp = rs[0]["pass_percentile"]; model = sum(r["model_stats"]["final_gain_pct"] for r in rs)
    out = dict(sessions=list(ids), model=sorted({r["model"] for r in rs}), pass_percentile=pp, model_gain_pct_sum=model,
               model_costs_paid_usd_sum=sum(r["model_stats"]["costs_paid_usd"] for r in rs), sets={})
    names = [n for n in rs[0]["twins"] if all(n in r["twins"] for r in rs)]
    for n in names:
        ts = [r["twins"][n] for r in rs]
        if "stats" in ts[0]:
            g = sum(t["stats"]["final_gain_pct"] for t in ts); out["sets"][n] = dict(gain_pct_sum=g, model_above=model > g); continue
        k = {len(t["_draw_gains_pct"]) for t in ts}; assert len(k) == 1, f"{n}: the sessions have different draw counts"
        xs = [sum(v) for v in zip(*[t["_draw_gains_pct"] for t in ts])]
        o = dict(summary(xs), **judge(xs, model, pp)); o = dict(o, median_gain_pct_sum=o.pop("median"))
        if n == "shuffle_runs":
            d = [t["distinct_orders"] for t in ts]; prod = 1
            for x in d:
                prod = None if (prod is None or x is None) else prod * x
            o["distinct_orders"] = prod if (prod is not None and prod < len(xs)) else None
            if all(t.get("note") == "no timing to judge" for t in ts):
                o.update(model_percentile=None, model_above_median=None, model_above_pass_percentile=None, note="no timing to judge")
        out["sets"][n] = o
    return out


def main(argv=None):
    a = argparse.ArgumentParser(description="Scores a finished weights session against its twins, or sums several sessions of one model (--sum).")
    a.add_argument("session", nargs="+"); a.add_argument("--draws", type=int); a.add_argument("--seed", type=int); a.add_argument("--json", action="store_true")
    a.add_argument("--sum", action="store_true", help="sum the model's gains and each twin set's gains draw by draw across the sessions")
    x = a.parse_args(argv)
    if x.sum or len(x.session) > 1:
        r = sum_sessions(x.session, draws=x.draws, seed=x.seed)
        if x.json:
            print(json.dumps(r, indent=1, sort_keys=True)); return
        print(f"sessions {len(r['sessions'])}  model {', '.join(r['model'])}  summed model gain {r['model_gain_pct_sum']:.2f}%  summed costs {r['model_costs_paid_usd_sum']:.2f} USD")
        for n, t in r["sets"].items():
            if "gain_pct_sum" in t:
                print(f"{n}: summed gain {t['gain_pct_sum']:.2f}%  model above: {t['model_above']}"); continue
            tail = t.get("note") or f"model percentile {t['model_percentile']:.1f}  above median {t['model_above_median']}  above pass percentile {t['model_above_pass_percentile']}"
            extra = f"  distinct orders {t['distinct_orders']}" if t.get("distinct_orders") else ""
            print(f"{n} ({t['n']} summed draws): median summed gain {t['median_gain_pct_sum']:.2f}%  range {t['low']:.2f}% to {t['high']:.2f}%  {tail}{extra}")
        return
    r = public(score(x.session[0], draws=x.draws, seed=x.seed))
    if x.json:
        print(json.dumps(r, indent=1, sort_keys=True)); return
    m = r["model_stats"]
    print(f"session {r['session']}  model {r['model']}  market {r['market']}  wakes {r['wakes']}  window {r['window']['start']} to {r['window']['end']}")
    print(f"costs assumed: {json.dumps(r['costs'], sort_keys=True)}")
    print(f"model: final gain {m['final_gain_pct']:.2f}%  largest drop {m['largest_drop_pct']:.2f}%  average weight {m['avg_weight']:.3f}  "
          f"turnover {m['turnover']:.2f}  costs paid {m['costs_paid_usd']:.2f} USD  wakes with trades {m['trade_wakes']}")
    for name, t in r["twins"].items():
        if "stats" in t:
            s = t["stats"]
            print(f"{name}: final gain {s['final_gain_pct']:.2f}%  largest drop {s['largest_drop_pct']:.2f}%  costs paid {s['costs_paid_usd']:.2f} USD  model above: {t['model_above']}")
        else:
            g = t["final_gain_pct"]; c = t["costs_paid_usd"]
            tail = t.get("note") or f"model percentile {t['model_percentile']:.1f}  above median {t['model_above_median']}  above pass percentile {t['model_above_pass_percentile']}"
            extra = f"  runs {t['runs']}" if "runs" in t else ""
            extra += f"  distinct orders {t['distinct_orders']}" if t.get("distinct_orders") else ""
            print(f"{name} ({g['n']} draws): median final gain {g['median']:.2f}%  range {g['low']:.2f}% to {g['high']:.2f}%  median costs {c['median']:.2f} USD  {tail}{extra}")


if __name__ == "__main__":
    main()
