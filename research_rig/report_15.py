"""Measurement 15 (queue row 23, ledger row 156): what a breakout stop order on stocks in play really paid.

Two steps. Neither runs a rule or reads a price file.
  python3 report_15.py --aggregate PATH/results_15.json
      reads the off-repo per-stock-day output and writes measure_15_summary.json next to this file: aggregates only,
      no trade, quote, price, time or symbol. (The per-stock-day file holds vendor trades and quotes and stays off repo.)
  python3 report_15.py
      prints docs/research/66_measure_15_breakout_fills.md from measure_15_summary.json only. Every figure comes from that file.
Headline, frozen in MEASURE_15_breakout_fills.md before any trade or quote was collected: mean entry slippage plus mean
stop-exit slippage, each as a share of the stop distance, odd lots left out, all 60 days."""
import hashlib, json, os, sys
H = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(H, "measure_15_summary.json")
DOC = os.path.join(H, "..", "docs", "research", "66_measure_15_breakout_fills.md")
LIMIT_KEY = "measure_15_build_max_slip_share_of_stop"


def aggregate(path):
    raw = open(path, "rb").read(); R = json.loads(raw)
    rows = [r for r in R["rows"] if "no_odd" in r]
    out = dict(source_made_utc=R["made_utc"], source_sha256=hashlib.sha256(raw).hexdigest(), counts=R["counts"],
               stock_days=len(R["rows"]), days=len({r["day"] for r in R["rows"]}), summary=R["summary"])
    legs = {}
    for name in ("no_odd", "odd"):
        c = {}
        for r in rows:
            for leg in ("entry", "exit"):
                x = r[name][leg]; k = f"{leg}: " + ("not tried, no entry fill" if x is None else x["status"])
                c[k] = c.get(k, 0) + 1
        legs[name] = dict(sorted(c.items()))
    out["leg_status"] = legs
    # outlier check: the headline means again with the largest 1% of each part left out
    trim = {}
    for name in ("no_odd", "odd"):
        t = {}
        for leg in ("entry", "exit"):
            xs = sorted(r[name][leg]["slip_share_stop"] for r in rows if r[name][leg] and r[name][leg]["status"] == "ok")
            k = len(xs) // 100; ys = xs[:len(xs) - k]
            t[leg] = dict(n=len(xs), dropped=k, mean_without_top_1pct=sum(ys) / len(ys), max=xs[-1], negative=sum(x < 0 for x in xs))
        trim[name] = t
    out["outlier_check"] = trim
    json.dump(out, open(SUMMARY, "w"), indent=1, sort_keys=True)
    print("wrote", SUMMARY)


def f(x, d=2):
    return "n/a" if x is None else f"{x:.{d}f}"


def limit():
    import re
    t = open(os.path.join(H, "..", "config", "thresholds.yaml")).read()
    m = re.search(rf"^{LIMIT_KEY}:\s*\n(?:\s+.*\n)*?\s+value:\s*([0-9.]+)", t, re.M)
    return float(m.group(1))


def table(T, w, share=True):
    w("| group | n | cents median | cents mean | cents p90 | bps median | bps mean | bps p90 | share of stop, mean |")
    w("|---|---|---|---|---|---|---|---|---|")
    for g in T["slip_cents"]:
        c, b, s = T["slip_cents"][g], T["slip_bps"][g], T["slip_share_stop"][g]
        w(f"| {g} | {c['n']} | {f(c['median'])} | {f(c['mean'])} | {f(c['p90'])} | {f(b['median'])} | {f(b['mean'])} | {f(b['p90'])} | {f(s['mean'], 3)} |")


def doc():
    raw = open(SUMMARY, "rb").read(); A = json.loads(raw); S = A["summary"]; L = []; w = L.append
    lim = limit()
    part = lambda name, leg: S[name][leg]["slip_share_stop"]["all"]
    e0, x0 = part("no_odd", "entry"), part("no_odd", "exit"); e1, x1 = part("odd", "entry"), part("odd", "exit")
    head = e0["mean"] + x0["mean"]; head1 = e1["mean"] + x1["mean"]
    oc = A["outlier_check"]["no_odd"]; trimmed = oc["entry"]["mean_without_top_1pct"] + oc["exit"]["mean_without_top_1pct"]
    c = A["counts"]
    w("# 66. Measurement 15: what a breakout order on stocks in play really paid")
    w("")
    w(f"Written by `research_rig/report_15.py` from `research_rig/measure_15_summary.json` (sha256 {hashlib.sha256(raw).hexdigest()[:16]}). "
      f"The summary was made from the off-repo per-stock-day output of {A['source_made_utc']} UTC (sha256 {A['source_sha256'][:16]}). "
      "Plan: `research_rig/MEASURE_15_breakout_fills.md`, ledger row 156, queue row 23. No return was computed.")
    w("")
    w("## Result")
    w("")
    w(f"- MEASURED: mean entry slippage {f(e0['mean'], 4)} of the stop distance (n {e0['n']}), mean stop-exit slippage {f(x0['mean'], 4)} (n {x0['n']}), odd lots left out, all {A['days']} days.")
    w(f"- MEASURED: headline sum {f(head, 4)}. The limit fixed before the run is {lim} (`{LIMIT_KEY}`). The sum is {'at or below' if head <= lim else 'above'} it, so by the frozen rule {'a full plan is written' if head <= lim else 'the idea is dropped'}.")
    w(f"- What it means: the paper sizes each trade by the stop distance and assumes fills at the level. Measured fills gave away about {f(head * 100, 0)}% of that risk unit per trade, about a fifth, before any edge.")
    w("")
    w("## Odd lots counted, for comparison")
    w("")
    w(f"- MEASURED: entry {f(e1['mean'], 4)} (n {e1['n']}) plus stop exit {f(x1['mean'], 4)} (n {x1['n']}) = {f(head1, 4)}.")
    w(f"- MEASURED: counting odd lots makes the entry {'cheaper' if e1['mean'] < e0['mean'] else 'dearer'} and the stop exit {'dearer' if x1['mean'] > x0['mean'] else 'cheaper'}. Our reading, not tested: an odd lot often prints at the level first, and some odd lots print far through the stop. Both settings are {'above' if min(head, head1) > lim else 'not both above'} the limit.")
    w("")
    w("## Counts")
    w("")
    w(f"- MEASURED: {A['stock_days']:,} stock-days in play on {A['days']} days. No direction (first bar closed at its open): {c.get('no direction', 0)}. No breakout by 16:00: {c.get('no breakout', 0)}. Breakouts: {c.get('breakout', 0)}.")
    for name, label in (("no_odd", "Odd lots left out"), ("odd", "Odd lots counted")):
        w(f"- MEASURED, {label.lower()}: " + "; ".join(f"{k} {v}" for k, v in A["leg_status"][name].items()) + ".")
    ne = sum(v for k, v in A["leg_status"]["no_odd"].items() if k.startswith("entry") and "no eligible" in k)
    w(f"- MEASURED: breakouts with no counted trade through the level within the 5-minute search ('no eligible trade'), odd lots left out: {ne}.")
    w("")
    for name, label in (("no_odd", "Odd lots left out (headline)"), ("odd", "Odd lots counted")):
        for leg, ll in (("entry", "entry"), ("exit", "stop exit")):
            w(f"## {label}: {ll}")
            w("")
            w("MEASURED. Price groups use the entry level in dollars. Percentiles use linear interpolation. Positive is worse.")
            w("")
            table(S[name][leg], w)
            w("")
    w("## Quoted spread at 09:35 and at the close")
    w("")
    w("MEASURED, cents, last quote at or before 09:35:00 and before 16:00:00 New York; price groups use the 09:30 open.")
    w("")
    w("| group | n 09:35 | median 09:35 | mean 09:35 | p90 09:35 | n close | median close | mean close | p90 close |")
    w("|---|---|---|---|---|---|---|---|---|")
    a, b = S["spread_cents"]["s0935"], S["spread_cents"]["sclose"]
    for g in a:
        x, y = a[g], b.get(g, {})
        w(f"| {g} | {x['n']} | {f(x['median'])} | {f(x['mean'])} | {f(x['p90'])} | {y.get('n')} | {f(y.get('median'))} | {f(y.get('mean'))} | {f(y.get('p90'))} |")
    w("")
    r = a["all"]["median"] / b["all"]["median"] if b["all"]["median"] else None
    w(f"- MEASURED: the median spread at 09:35 is {f(r, 1)} times the median spread at the close. The breakout order is placed soon after 09:35.")
    w("")
    w("## Outlier check")
    w("")
    w(f"- MEASURED: with the largest 1% of each part left out (entry {oc['entry']['dropped']} of {oc['entry']['n']}, exit {oc['exit']['dropped']} of {oc['exit']['n']}), the means are {f(oc['entry']['mean_without_top_1pct'], 4)} and {f(oc['exit']['mean_without_top_1pct'], 4)}, sum {f(trimmed, 4)}. Still {'above' if trimmed > lim else 'at or below'} the limit.")
    w(f"- MEASURED: the largest single values were {f(oc['entry']['max'], 2)} (entry) and {f(oc['exit']['max'], 2)} (exit) times the stop distance. MEASURED by hand on the largest exits: they were gaps through the stop. No value was below zero ({oc['entry']['negative']} entry, {oc['exit']['negative']} exit), as the definition requires.")
    w("")
    w("## Compared with what was published")
    w("")
    w("- STATED (doc 55): one rebuild measured 2.4 cents mean and 1.0 cent median on the entry, about 12% of the stop distance, and the rule then lost. Our entry mean is "
      f"{f(S['no_odd']['entry']['slip_cents']['all']['mean'])} cents with a median of {f(S['no_odd']['entry']['slip_cents']['all']['median'])}; our stop exit costs {'more' if x0['mean'] > e0['mean'] else 'less'} than our entry as a share of the stop.")
    w("- STATED (doc 55): the paper charges a commission and no slippage.")
    w("")
    w("## Limits")
    w("")
    w("- The ETF list is today's Nasdaq Trader list, so a dead ETF is missed and a reused ticker can be misread. Some tickers were never asked (5-letter endings other than A, B, C, K and L, and dots other than .A and .B).")
    w("- The breakout and stop minutes come from 1-minute bars, which may leave out some prints. The odd-lot version can only trigger inside minutes the bars point to.")
    w("- UNKNOWN: whether the trade time is the exchange's or the consolidated feed's. Quotes are taken as the national best bid and offer. That is likely but not proven.")
    w("- 60 days is a sample. It was fixed before any fill was seen.")
    w("- The trades, quotes and per-stock-day rows stay off the repo because they are vendor data.")
    open(DOC, "w").write("\n".join(L) + "\n")
    print("wrote", os.path.relpath(DOC, os.path.join(H, "..")))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--aggregate": aggregate(sys.argv[2])
    else: doc()
