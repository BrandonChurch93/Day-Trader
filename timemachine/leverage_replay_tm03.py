"""Leverage replay of plan TM03 (BTC/USD, one dial a day). Pretend money only. Looked at after the fact.

Each finished TM03 session's stored daily answers are replayed through the weights book (timemachine/weights.py,
run_answers with lev) at the multiples in tm_lev_replay_multiples: every answer and the opening times the multiple.
The same is done for holding (1.0 times the multiple) and for dials B and C of timemachine/dial_rules_tm03.py.
1x is run through the same leverage path and must equal the stored session to the cent; that is the check.

The models did not know they were leveraged; they answered for a 1x account. This is not a counted trial and not
part of any plan's mark. It shows what leverage does to the same decisions, nothing more.

Per model, summed over the months it has: gain, largest drop (on minute lows, the worst month), forced close-outs,
financing paid, and months that ended below tm_lev_replay_low_share of the starting account.

python3 timemachine/leverage_replay_tm03.py            print the page
python3 timemachine/leverage_replay_tm03.py --write    write timemachine/leverage_replay_tm03.json and docs/research/39_leverage_replay_tm03.md
python3 timemachine/leverage_replay_tm03.py --check    exit 1 if either is missing or stale
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S, weights as W, score_tm03 as ST, dial_rules_tm03 as DR
from timemachine.tape import Tape

OUT_JSON = ROOT / "timemachine" / "leverage_replay_tm03.json"
OUT_DOC = ROOT / "docs" / "research" / "39_leverage_replay_tm03.md"
REPLAY_KEYS = ["tm_lev_replay_multiples", "tm_lev_replay_low_share"]
DIALS = ["B", "C"]


def scaled(w, m):
    return None if w is None else {s: v * m for s, v in w.items()}


def replay(meta, table, minutes, answers, cfg, lc, m):
    """One month at multiple m. answers: weights dicts or None, at 1x. The opening is scaled too."""
    mt = dict(meta, opening=scaled(meta.get("opening") or {}, m))
    lev = W.lev_params(meta["market"], meta["symbols"], max(1.0, float(m)), lc)
    book, recs, final = W.run_answers(mt, table, [scaled(a, m) for a in answers], cfg, lev=lev, minutes=minutes)
    start = cfg["tm_account_start_usd"]
    return dict(gain_usd=final - start, final_usd=final, largest_drop_pct=book["lev_largest_drop"] * 100, closeouts=len(book["closeouts"]),
                financing_usd=book["financing_usd"], penalty_usd=book["penalty_usd"], shortfall_usd=book["shortfall_usd"],
                costs_usd=book["spread_usd"] + book["fee_usd"], fixed_rate_hours=sum(r["lev"]["fixed_hours"] for r in recs))


def total(rows, start, low):
    """rows in month order. carried: one account taken through the months in order, each month's growth applied to the last."""
    v = float(start)
    for r in rows:
        v *= r["final_usd"] / start
    return dict(months=len(rows), carried_gain_usd=v - start, gain_usd=sum(r["gain_usd"] for r in rows), worst_month_drop_pct=min(r["largest_drop_pct"] for r in rows),
                closeouts=sum(r["closeouts"] for r in rows), financing_usd=sum(r["financing_usd"] for r in rows),
                penalty_usd=sum(r["penalty_usd"] for r in rows), shortfall_usd=sum(r["shortfall_usd"] for r in rows),
                months_below_low=sum(1 for r in rows if r["final_usd"] < low * start), fixed_rate_hours=sum(r["fixed_rate_hours"] for r in rows))


def build(tape=None):
    tape = tape or Tape(); cfg0 = ST.tm03_config(); plan = cfg0["tm03_plan"]; sym = plan["symbol"]
    lc = W.lev_config(); rk = W.lev_config(keys=REPLAY_KEYS)
    mults = [1] + [int(x) if float(x).is_integer() else float(x) for x in rk["tm_lev_replay_multiples"]]; low = float(rk["tm_lev_replay_low_share"])
    start = cfg0["tm_account_start_usd"]
    months = {}
    for mo in plan["months"]:  # the month's clock, prices and minutes, built as dial_rules_tm03.py builds them
        a, b = DR.month_window(mo, plan.get("last_day"))
        wakes, end = W.make_wakes(tape, "crypto", a, b, [{"every": "day", "utc_hours": [plan["wake_hour_utc"]]}])
        meta = dict(market="crypto", symbols=[sym], benchmark=sym, opening={sym: float(plan["opening_weight"])}, wakes=[W.iso(w) for w in wakes],
                    end_utc=W.iso(end), window=dict(start=a, end=b))
        months[mo] = dict(meta=meta, table=W.price_table(tape, meta), minutes=W.lev_minutes(tape, [sym], wakes[0], end), wakes=wakes)
    out = dict(note="Looked at after the fact. The models answered for a 1x account and did not know they were leveraged. Not a counted trial.",
               symbol=sym, multiples=mults, low_share=low, account_start_usd=start, keys_from={**lc["_from"], **rk["_from"]},
               funding_source=W.lev_params("crypto", [sym], 2.0, lc)["source"][sym], models={}, months_with_every_model=[])
    base = {}  # hold and dials per month and multiple
    for mo, md in months.items():
        base[mo] = {"hold": {m: replay(md["meta"], md["table"], md["minutes"], [None] * len(md["wakes"]), cfg0, lc, m) for m in mults}}
        bars = {w: DR.closed_daily_bars_before(tape, sym, w) for w in md["wakes"]}
        for d in DIALS:
            seq = DR.decide_series(d, md["wakes"], lambda w: bars[w])
            ans = [{sym: x} if x > 0 else {} for x in seq]
            base[mo][d] = {m: replay(md["meta"], md["table"], md["minutes"], ans, cfg0, lc, m) for m in mults}
    for tag, name in ST.MODELS:
        rows = {}
        for mo, md in months.items():
            d = S.runs_dir() / ST.sid(tag, mo)
            if not (d / "result.json").exists():
                continue
            meta = json.loads((d / "session.json").read_text()); res = json.loads((d / "result.json").read_text()); cfg = res["config"]
            assert meta["wakes"] == md["meta"]["wakes"] and meta["end_utc"] == md["meta"]["end_utc"], f"{d.name}: wakes differ from the month's clock"
            table = W.price_table(tape, meta); answers = [st["asked"] for st in res["steps"]]
            rr = {m: replay(meta, table, md["minutes"], answers, cfg, lc, m) for m in mults}
            stored = res["final"]["value_usd"] - start
            assert round(rr[1]["gain_usd"], 2) == round(stored, 2), f"{d.name}: 1x replay {rr[1]['gain_usd']:.4f} differs from the session {stored:.4f}"
            rows[mo] = rr
        if not rows:
            out["models"][tag] = dict(name=name, months=[])
            continue
        ms = sorted(rows)
        out["models"][tag] = dict(name=name, months=ms, per_month={mo: {str(m): rows[mo][m] for m in mults} for mo in ms},
                                  sums={key: {str(m): total([src[mo][m] for mo in ms], start, low) for m in mults}
                                        for key, src in (("model", rows), ("hold", {mo: base[mo]["hold"] for mo in ms}), *((f"dial_{d}", {mo: base[mo][d] for mo in ms}) for d in DIALS))})
    every = [mo for mo in months if all(mo in out["models"][t]["months"] for t, _ in ST.MODELS)]
    out["months_with_every_model"] = every
    out["all_months"] = {key: {str(m): total([base[mo][k2][m] for mo in months], start, low) for m in mults} for key, k2 in (("hold", "hold"), ("dial_B", "B"), ("dial_C", "C"))}
    out["months"] = list(months)
    return out


def usd(x):
    return ST.usd(x)


def doc(o):
    mults = o["multiples"]; low = o["low_share"]; start = o["account_start_usd"]
    L = ["# Leverage replay of plan TM03: the same bitcoin dials at 2x, 3x and 5x", "",
         "Made by `timemachine/leverage_replay_tm03.py` from the finished TM03 sessions. Do not edit by hand. Pretend money.", "",
         "Looked at after the fact. The models answered for a 1x account and did not know they were leveraged. This is not a counted trial and not part of any plan's mark.", "",
         "## What was done", "",
         "- Every stored daily answer of every finished TM03 session was replayed through the weights book with each weight, and the opening, times the multiple (`tm_lev_replay_multiples`). Holding (1.0 times the multiple) and dials B and C of `timemachine/dial_rules_tm03.py` were replayed the same way.",
         "- 1x goes through the same leverage path and matches every stored session to the cent. The script stops if it does not.",
         f"- Borrowed dollars pay financing at each whole UTC hour. For {o['symbol']} the rate is the stored hourly perpetual funding ({o['funding_source']}; key `tm_lev_funding_files`), paid by longs when positive and received when negative. Hours the file lacks use `tm_lev_fixed_rate_per_day`.",
         "- On every recorded minute between wakes, if the account value at the minute's low is below `tm_lev_maintenance_crypto` of the position's value, the whole book is sold at that low, less the half spread, the fee and `tm_lev_closeout_penalty`. It stays in cash until the next wake, then the standing dial is bought again.",
         "- Each month starts from the same account, as in TM03. A month that ends at zero does not carry into the next.",
         "- \"Gain, months summed\" adds each month's gain, every month starting again from the same account, as TM03 scores it. \"One account carried\" takes one account through the months in order, so a month that ends near zero leaves little for the next. A real account works the second way.",
         f"- \"Months below\" counts months that ended below `tm_lev_replay_low_share` ({low:g}) of the {usd(start)} start. Largest drop: the worst month, measured on minute lows.",
         "- Keys read: " + ", ".join(f"`{k}` from {v}" for k, v in sorted(o["keys_from"].items())) + ".", ""]
    L += ["## Holding and the dials, every month", "",
          "MEASURED, summed over " + str(len(o["months"])) + " months.", "",
          "| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |", "|---|---|---|---|---|---|---|---|"]
    for key, label in (("hold", "hold"), ("dial_B", "dial B"), ("dial_C", "dial C")):
        for m in mults:
            t = o["all_months"][key][str(m)]
            L.append(f"| {label} | {m}x | {usd(t['gain_usd'])} | {usd(t['carried_gain_usd'])} | {t['worst_month_drop_pct']:.1f}% | {t['closeouts']} | {usd(t['financing_usd'])} | {t['months_below_low']} of {t['months']} |")
    L += ["", "## Each model, over the months it has", "",
          "MEASURED. Each model's rows are against holding and the dials over the same months.", ""]
    for tag, name in ST.MODELS:
        mm = o["models"][tag]
        if not mm["months"]:
            L += [f"### {name}", "", "No finished month.", ""]; continue
        L += [f"### {name}", "", f"{len(mm['months'])} months.", "",
              "| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |", "|---|---|---|---|---|---|---|---|"]
        for key, label in (("model", "the model's dials"), ("hold", "hold"), ("dial_B", "dial B"), ("dial_C", "dial C")):
            for m in mults:
                t = mm["sums"][key][str(m)]
                L.append(f"| {label} | {m}x | {usd(t['gain_usd'])} | {usd(t['carried_gain_usd'])} | {t['worst_month_drop_pct']:.1f}% | {t['closeouts']} | {usd(t['financing_usd'])} | {t['months_below_low']} of {t['months']} |")
        L.append("")
    # plain lines, from the numbers above
    L += ["## What it shows", ""]
    ahead = {}
    for tag, name in ST.MODELS:
        mm = o["models"][tag]
        if mm["months"]:
            ahead[tag] = [mm["sums"]["model"][str(m)]["gain_usd"] > mm["sums"]["hold"][str(m)]["gain_usd"] for m in mults]
    same = sum(1 for v in ahead.values() if len(set(v)) == 1)
    hb = o["all_months"]["hold"]; top = str(mults[-1])
    L += [f"- {sum(1 for v in ahead.values() if v[0])} of {len(ahead)} models were ahead of holding at 1x. In {same} of {len(ahead)} the side of holding was the same at every multiple. Leverage made the gaps bigger in dollars; it did not turn a gap around." if ahead else "- No model has a finished month.",
          f"- Holding over all {len(o['months'])} months, summed: {usd(hb['1']['gain_usd'])} at 1x; " + "; ".join(f"{usd(hb[str(m)]['gain_usd'])} at {m}x ({hb[str(m)]['closeouts']} close-outs, {hb[str(m)]['months_below_low']} months below)" for m in mults[1:]) + ".",
          f"- Holding, one account carried: {usd(hb['1']['carried_gain_usd'])} at 1x; " + "; ".join(f"{usd(hb[str(m)]['carried_gain_usd'])} at {m}x" for m in mults[1:]) + ". The summed figure at high multiples looks better than the carried one because each month starts again from a full account, which a real account does not.",
          f"- The models' worst month drop: between {max(o['models'][t]['sums']['model']['1']['worst_month_drop_pct'] for t in ahead):.0f}% and {min(o['models'][t]['sums']['model']['1']['worst_month_drop_pct'] for t in ahead):.0f}% at 1x, between {max(o['models'][t]['sums']['model'][top]['worst_month_drop_pct'] for t in ahead):.0f}% and {min(o['models'][t]['sums']['model'][top]['worst_month_drop_pct'] for t in ahead):.0f}% at {top}x." if ahead else "",
          f"- One account carried, at 1x and at {top}x: " + "; ".join(f"{o['models'][t]['name']} {usd(o['models'][t]['sums']['model']['1']['carried_gain_usd'])} and {usd(o['models'][t]['sums']['model'][top]['carried_gain_usd'])}" for t in ahead) + "." if ahead else "",
          "- The gain at a multiple is not the 1x gain times the multiple: financing, close-outs and the month-by-month reset take from it, and a month closed out at a low does not get the rebound.",
          "- The models chose their dials for a 1x account. A model that knew it was leveraged might have chosen otherwise. This replay cannot say how.", "",
          "## What it does not show", "",
          "- Eight months of one coin. A different stretch could show more or fewer close-outs.",
          "- Funding is the stored perpetual rate applied to borrowed dollars only. A real perpetual contract charges it on the whole position, and a real broker's margin rate differs.",
          "- Close-outs are assumed at the minute's low, less a fixed penalty. A real exchange may close out in parts, earlier or later.",
          "- Fills are assumed from recorded minute bars.", "",
          "## Files", "",
          "- `timemachine/leverage_replay_tm03.py` writes this page and `timemachine/leverage_replay_tm03.json`.",
          "- `timemachine/weights.py`: the book with `max_gross`, financing and the maintenance rule (`lev_scan`).",
          "- `timemachine/dial_rules_tm03.py`: dials B and C.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    o = build(); js = json.dumps(o, indent=1, sort_keys=True) + "\n"; md = doc(o)
    if a.check:
        stale = [str(p.relative_to(ROOT)) for p, t in ((OUT_JSON, js), (OUT_DOC, md)) if not p.is_file() or p.read_text() != t]
        if stale:
            print("stale: " + ", ".join(stale), file=sys.stderr); return 1
        print("ok"); return 0
    if a.write:
        OUT_JSON.write_text(js); OUT_DOC.write_text(md); print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_DOC.relative_to(ROOT)}"); return 0
    print(md); return 0


if __name__ == "__main__":
    raise SystemExit(main())
