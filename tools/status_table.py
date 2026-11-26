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
    edge = f" Knife edge: the overfitting estimate on Kraken prices is {k[0]['rerun']:.4f} against a bar of {th['backtest_max_pbo']} when it was run (`backtest_max_pbo`), and {d[0]['rerun']:.4f} on Bitstamp prices from the same start date, which fails." if k and d else ""
    return ("Replay 01 with cross-check X2, rerun after the audits", "Nine slow trend rules on bitcoin and on ether, daily, five venue costs, two price histories",
            f"{n['R01']['passed_rerun']} of {n['R01']['trials']} rule, coin and venue combinations pass on Bitstamp prices and {n['X2']['passed_rerun']} of {n['X2']['trials']} on Kraken prices. "
            f"Pass on both histories: {ls([x['rule'] for x in both])} on {ls(coins)}, at {ls(ven)} cost only. Not credited as passes: the rerun also carried a stricter pass mark and a change to what holding pays (question 18b in the morning list). In the first run, before the audit fixes, {len([x for x in c['both_histories'] if x['first_both']]) or 'none'} passed on both histories ({n['R01']['passed_first']} on Bitstamp prices, {n['X2']['passed_first']} on Kraken prices)." + edge,
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
    s = f"{len(p)} of {tot} rule and venue combinations pass. Highest deflated Sharpe {best[0]:.3f} ({best[1]} at {best[2]}) against a bar of {r['thresholds']['replay_min_deflated_sharpe']} when it was run (`replay_min_deflated_sharpe`). "
    s += f"Held-back years at Binance.US cost: the top 10 coin rule K1 grew {pc(k1['cagr'])} a year, holding bitcoin grew {pc(hold['cagr'])}. "
    s += "An independent audit rebuilt the result and found faults that do not change it."
    return ("Replay 04", "Trend rules on a wide basket of coins, dead coins kept", s, "`docs/research/23_replay_04_coin_basket.md`")
def stocks():
    a = J("results_05.json"); b = J("results_05b.json"); L = ["low", "base", "high"]; N = list(b["costs"]["base"]["rules"])
    P = lambda r, lab: [n for n in N if r["costs"][lab]["rules"][n]["marks"]["passed"]]; cb = lambda lab: f"{b['costs'][lab]['cost_bps_per_side']} bps"
    both = [n for n in N if all(n in P(a, l) and n in P(b, l) for l in L)]; h = a["costs"]["base"]["bench"]["HOLD"]["held"]; t1 = a["costs"]["base"]["rules"]["T1"]["held"]
    assert all(t1[k] == b["costs"]["base"]["rules"]["T1"]["held"][k] and h[k] == b["costs"]["base"]["bench"]["HOLD"]["held"][k] for k in ("cagr", "maxdd")), "T1 or hold differs between the two runs"
    return ("Replay 05, first run and corrected run", "Eight slow trend rules on the US stock market index from 1927, three cost levels",
            "First run: " + "; ".join(f"{ls(P(a, l))} at {cb(l)}" for l in L) + ". Corrected run, after an audit found one rule did not match the plan: " + "; ".join(f"{ls(P(b, l))} at {cb(l)}" for l in L)
            + f". Pass in both runs at every cost: {ls(both)}. Not credited as passes in either run: the first run's ledger row was late and the corrected run was made before asking the owner (question 18b in the morning list). Fails stand. Held-back years at 5 bps, the same in both runs: the ten-month rule T1 grew {pc(t1['cagr'])} a year with a largest drop of {pc(t1['maxdd'])}, holding the market grew {pc(h['cagr'])} with {pc(h['maxdd'])}.",
            "`docs/research/22_replay_05_stock_trend.md`")
def books():
    b = J("books_summary.json"); P = b["pairs"]; k = P["Kraken|XXBTZUSD"]; n = P["Binance.US|BTCUSD"]; slip = J("results_04.json")["slippage_bps"]["XBTUSD_ETHUSD"]
    import datetime as dt
    t = lambda s: dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S"); mins = round((t(b["last_sample_utc"]) - t(b["first_sample_utc"])).total_seconds() / 60)
    span = f"{mins} minutes" if mins < 120 else f"{mins / 60:.1f} hours"
    return ("Order-book samples", "What it cost to trade a small size at once, sampled on two venues on one day",
            f"{b['rounds']} rounds from {b['first_sample_utc']} to {b['last_sample_utc']} UTC. Bitcoin, middle cost of one order, fees not included: $1,000 cost {k['cost_1k_bps']['median']:.1f} bps on Kraken and {n['cost_1k_bps']['median']:.1f} bps on Binance.US; "
            f"$10,000 cost {k['cost_10k_bps']['median']:.1f} and {n['cost_10k_bps']['median']:.1f} bps. Replay 04 assumed {slip} bps for this on bitcoin and ether (read from its output). The rerun of replays 01 and 03 used the same figure, set in `research_rig/rig2.py` and not stored in its output. One sample of {span} only. The sampler was set to stop by itself at about 16:30 UTC on 2026-11-25, so a last time here before that means this is an interim summary.",
            "`docs/research/24_order_book_costs.md`")
def smaller():
    s2 = J("compare_v1_v2.json")["counts"]["S2"]
    return ("Smaller checks: X1, S1, S2, the diagnostic, two mixed portfolios", "The same rules on other prices, start dates and fill times, and bitcoin and ether held together",
            f"Not separate tests and not in the trial count. S2, ether from an earlier start on Kraken prices: {s2['passed_rerun']} of {s2['trials']} combinations pass. X1 and S1 carry no pass marks. The diagnostic is the Bitstamp figure in the first row. "
            "The two mixed portfolios are reported with growth and largest drop and are not judged on the five marks. Each name is defined in `docs/GLOSSARY.md`.",
            "`docs/research/12_replay_01_crypto_trend.md`, `docs/research/12b_replay_01_kraken_crosscheck.md`, `docs/research/16_rig_audit.md`")
def count_check():
    c = J("ledger_count_check.json"); low = c["lowest_dsr_among_passes_at_count_all"]; n3 = len(c["mark3_passes_that_become_fails"])
    return ("Trial count check", "The owner's rule counts a rerun after an engine fault as a trial. The two reruns were not counted when they ran. Does counting them change a result",
            f"Worked out from the stored outputs with {c['count_all']} trials counted. It covers the outputs now judged: the rerun of replays 01 and 03 with its cross-checks, replay 04, and both runs of replay 05. The first-run outputs of replays 01 and 03 came from the engine with the faults and are not worked out again. Of {c['passes_as_run']} passes in those outputs, across all cost levels, {len(c['passes_that_become_fails']) or 'none'} become fails. {c['rows_not_worked_out']} of {c['rows_checked']} rows could not be worked out again from what was stored, and {c['rows_not_worked_out_that_passed_mark3_as_run'] or 'none'} of those had passed mark 3. "
            f"The closest is {low['rule']} on {low['where']} in {low['test']}, at {low['dsr_at_count_all']:.3f} against a bar of {c['bar']} (`replay_min_deflated_sharpe`). "
            f"Pass mark 3 alone changes from pass to fail in {n3} rows that had already failed another mark.",
            "`research_rig/TRIAL_LEDGER.md`, `research_rig/ledger_count_check.json`")
def crypto_methods():
    r = J("results_09.json"); rules = r["rules"]; h = r["hold"]["held"]; dates = r["dates"]["held"]
    passes = sum(x["marks"]["passed"] for x in rules.values())
    growth = max(rules, key=lambda n: rules[n]["held"]["total"])
    return ("Replay 09", "New timing, rank, lead and risk rules on Alpaca crypto bars",
            f"{passes} of {len(rules)} pass at {r['fee']['total_bps']} bps per side "
            "(`practice_crypto_fee_bps_added` plus `tm_crypto_half_spread_bps`). "
            f"Held back {dates[0]} to {dates[1]}: best rule {growth} grew {pc(rules[growth]['held']['total'])}; "
            f"holding bitcoin grew {pc(h['total'])}.", "`docs/research/28_replay_09_crypto_methods.md`")
def intraday_stocks():
    r = J("results_07.json"); S = r["symbols"]; J2 = r["judged"]; cs = lambda l: f"{r['costs'][l]:g} bps"
    s = "; ".join(f"{k}: {sum(o['passed_both_judged_costs'].values())} of {len(o['passed_both_judged_costs'])} rules pass all five marks at both {' and '.join(cs(l) for l in J2)} per side" for k, o in S.items())
    be = [(o["breakeven"][n]["vs_hold_round_trip_bps"], n, k) for k, o in S.items() for n in o["breakeven"] if o["breakeven"][n]["vs_hold_per_side"]["status"] != "below_at_zero"]
    s += ". " + (f"Highest break-even cost against holding, round trip, whole sample: {max(be)[0]:.1f} bps ({max(be)[1]} on {max(be)[2]})." if be else "No rule beats holding even at zero cost.")
    s += " Prices from the workspace's own price lookup, dividend adjustment UNKNOWN, days that failed the bar check not used."
    return ("Replay 07", "Eight day trading rules on SPY and QQQ one-minute bars, judged at 2 and 5 bps per side", s, "`docs/research/27_replay_07_intraday_spy_qqq.md`")
def fund_trend():
    r = J("results_06.json"); R = r["rules"]; H = r["slices"]["held"]; d = H["dates"]; y = lambda o: o["base"]["cagr"]
    passes = sum(x["marks"]["passed"] for x in R.values()); best = max(R, key=lambda n: y(H["rules"][n]))
    marks = sum(v for k, v in R[best]["marks"].items() if k != "passed")
    spy = f" Holding SPY grew {pc(y(H['rules']['SPY']))} a year; the best rule's own yardstick grew {pc(y(H['rules'][R[best]['primary']]))}."
    return ("Replay 06", "Six slow trend and allocation rules on nine funds that can be bought, daily bars with dividends",
            f"{passes} of {len(R)} pass at {r['costs_bps_per_side']['base']} bps per side. Held back {d[0]} to {d[1]}, run once: "
            f"best rule {best} grew {pc(y(H['rules'][best]))} a year and passed {marks} of 5 marks.{spy}", "`docs/research/35_replay_06_fund_trend.md`")
ROWS = [crypto_trend, crypto_intraday, pilot, basket, stocks, books, smaller, count_check]
REPLAY24 = "docs/research/68_replay_24_same_coin_carry.md"
def same_coin_carry():
    # The detail page is generated from the one-shot data kept off repo.
    with open(REPLAY24) as f:
        summary = next(line.removeprefix("MEASURED. Replay 24 ").strip() for line in f
                       if line.startswith("MEASURED. Replay 24 "))
    return ("Replay 24", "Buy spot and short its own perpetual on lagged funding, viewed dates only",
            summary,f"`{REPLAY24}`")
if os.path.exists(REPLAY24):
    ROWS.insert(ROWS.index(books), same_coin_carry)
if os.path.exists(RR + "results_09.json"):
    ROWS.insert(5, crypto_methods)
if os.path.exists(RR + "results_07.json"):
    ROWS.insert(ROWS.index(books), intraday_stocks)
if os.path.exists(RR + "results_06.json"):
    ROWS.insert(ROWS.index(books), fund_trend)
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
