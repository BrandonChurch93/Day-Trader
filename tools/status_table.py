"""Writes the results table in docs/STATUS.md from the output files, so no result on the status page is typed by hand.
Run from the repo root:  python3 tools/status_table.py --write     (tools/check_repo.py fails if the table is out of date)
To add a test: add a function that returns one table row, and add it to ROWS."""
import json, sys, re, os
RR = "research_rig/"; J = lambda f: json.load(open(RR + f)); ls = lambda x: ", ".join(x) if x else "none"
START, END = "<!-- results:start (written by tools/status_table.py, do not edit by hand) -->", "<!-- results:end -->"
pc = lambda x: f"{x*100:+.1f}%"
def crypto_trend():
    c = J("compare_v1_v2.json"); n = c["counts"]; both = [x for x in c["both_histories"] if x["both"]]; ven = sorted({x["venue"] for x in both})
    coins = sorted({x["asset"][:3] for x in both}); v = J("results_v2.json"); th = v["thresholds"]
    k = [x for x in c["pbo"] if x["run"] == "X2" and x["asset"] == "BTCUSD" and x["venue"] in ven]; d = [x for x in c["pbo"] if x["run"] == "DIAG" and x["asset"] == "BTCUSD" and x["venue"] in ven]
    edge = f" Knife edge: the overfitting estimate on Kraken prices is {k[0]['rerun']:.4f} against a bar of {th['backtest_max_pbo']} (`backtest_max_pbo`), and {d[0]['rerun']:.4f} on Bitstamp prices from the same start date, which fails." if k and d else ""
    return ("Replay 01 with cross-check X2, rerun after the audits", "Nine slow trend rules on bitcoin and on ether, daily, five venue costs, two price histories",
            f"{n['R01']['passed_rerun']} of {n['R01']['trials']} rule and venue pairs pass on Bitstamp prices and {n['X2']['passed_rerun']} of {n['X2']['trials']} on Kraken prices. "
            f"Pass on both histories: {ls([x['rule'] for x in both])} on {ls(coins)}, at {ls(ven)} cost only. First run before the audit fixes: {len([x for x in c['both_histories'] if x['first_both']])} on both." + edge,
            "`docs/research/16_rig_audit.md`")
def crypto_intraday():
    n = J("compare_v1_v2.json")["counts"]["R03"]
    return ("Replay 03, rerun after the audits", "Eight day trading rules on hourly bitcoin and ether, five venue costs", f"{n['passed_rerun']} of {n['trials']} rule, coin and venue combinations pass.", "`docs/research/16_rig_audit.md`, rule definitions in `docs/research/15_replay_03_intraday_crypto.md`")
def pilot():
    r = J("results_02.json")
    return ("Pilot 02", "Six AI model runs making one call a day on bitcoin and ether", f"Inconclusive, as the plan said before it ran. {len(r['n_decisions'])} model runs, {max(r['n_decisions'].values())} calls each. Too few days to tell skill from luck.", "`docs/research/14_ai_calls_pilot_02.md`")
def basket():
    r = J("results_04.json"); V = r["venues"]; tot = sum(len(v["rules"]) for v in V.values()); p = [(n, vn) for vn, v in V.items() for n, x in v["rules"].items() if x["marks"]["passed"]]
    b = V["Binance.US"]; hold = b["bench"]["HOLD_BTC"]["slices"]["held"]; k1 = b["rules"]["K1"]["slices"]["held"]; best = max(((x["dsr"], n, vn) for vn, v in V.items() for n, x in v["rules"].items()))
    s = f"{len(p)} of {tot} rule and venue pairs pass. Highest deflated Sharpe {best[0]:.3f} ({best[1]} at {best[2]}) against a bar of {r['thresholds']['replay_min_deflated_sharpe']} (`replay_min_deflated_sharpe`). "
    s += f"Held-back years at Binance.US cost: the top 10 coin rule K1 grew {pc(k1['cagr'])} a year, holding bitcoin grew {pc(hold['cagr'])}. "
    s += "An independent audit rebuilt the result and found faults that do not change it."
    return ("Replay 04", "Trend rules on a wide basket of coins, dead coins kept", s, "`docs/research/23_replay_04_coin_basket.md`")
def stocks():
    a = J("results_05.json"); b = J("results_05b.json"); L = ["low", "base", "high"]; N = list(b["costs"]["base"]["rules"])
    P = lambda r, lab: [n for n in N if r["costs"][lab]["rules"][n]["marks"]["passed"]]; cb = lambda lab: f"{b['costs'][lab]['cost_bps_per_side']} bps"
    both = [n for n in N if all(n in P(a, l) and n in P(b, l) for l in L)]; h = b["costs"]["base"]["bench"]["HOLD"]["held"]; t1 = b["costs"]["base"]["rules"]["T1"]["held"]
    return ("Replay 05, first run and corrected run", "Eight slow trend rules on the US stock market index from 1927, three cost levels",
            "First run: " + "; ".join(f"{ls(P(a, l))} at {cb(l)}" for l in L) + ". Corrected run, after an audit found one rule did not match the plan: " + "; ".join(f"{ls(P(b, l))} at {cb(l)}" for l in L)
            + f". Pass in both runs at every cost: {ls(both)}. Held-back years at 5 bps: the ten-month rule T1 grew {pc(t1['cagr'])} a year with a largest drop of {pc(t1['maxdd'])}, holding the market grew {pc(h['cagr'])} with {pc(h['maxdd'])}.",
            "`docs/research/22_replay_05_stock_trend.md`")
def books():
    b = J("books_summary.json"); P = b["pairs"]; k = P["Kraken|XXBTZUSD"]; n = P["Binance.US|BTCUSD"]; slip = J("results_04.json")["slippage_bps"]["XBTUSD_ETHUSD"]
    return ("Order-book samples", "What it cost to trade a small size at once, sampled overnight on two venues",
            f"{b['rounds']} rounds from {b['first_sample_utc']} to {b['last_sample_utc']} UTC. Bitcoin, middle cost of one order, fees not included: $1,000 cost {k['cost_1k_bps']['median']:.1f} bps on Kraken and {n['cost_1k_bps']['median']:.1f} bps on Binance.US; "
            f"$10,000 cost {k['cost_10k_bps']['median']:.1f} and {n['cost_10k_bps']['median']:.1f} bps. The crypto replays assume {slip} bps for this on bitcoin and ether. One night only.",
            "`docs/research/24_order_book_costs.md`")
ROWS = [crypto_trend, crypto_intraday, pilot, basket, stocks, books]
def table():
    t = "| Test | What was asked | Result, MEASURED | Full write-up |\n|---|---|---|---|\n"
    for f in ROWS:
        try: t += "| " + " | ".join(f()) + " |\n"
        except FileNotFoundError as e: t += f"| {f.__name__} | | Output file missing: {os.path.basename(e.filename)} | |\n"
    return t
def block(): return START + "\n" + table() + END
def in_sync():
    s = open("docs/STATUS.md").read(); m = re.search(re.escape(START) + r".*?" + re.escape(END), s, re.S); return bool(m) and m.group(0) == block()
if __name__ == "__main__":
    if "--write" in sys.argv:
        s = open("docs/STATUS.md").read(); m = re.search(re.escape(START) + r".*?" + re.escape(END), s, re.S)
        assert m, "docs/STATUS.md has no results markers"; open("docs/STATUS.md", "w").write(s[:m.start()] + block() + s[m.end():]); print("docs/STATUS.md results table written")
    else: print(table())
