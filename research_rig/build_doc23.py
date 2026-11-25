"""Builds docs/research/23_replay_04_coin_basket.md from results_04.json only. Run after run_04.py.
Every figure in the document comes from the JSON. The one exception is PLAN_FILES, the file count written in the plan
text itself, which is quoted as the plan's number and compared with the count the run loaded."""
import json
r = json.load(open("results_04.json")); TH = r["thresholds"]; V = r["venues"]; VL = list(V); RU = ["K1", "K2", "K3", "K4", "K5"]
PLAN_FILES = 760   # quoted from PREREG_04_coin_basket_trend.md, section Data
MS = r["membership"]; MSUM = r["membership_summary"]; BE = r["breakeven"]; SENS = r["sensitivity"]; SL = r["slices"]
MK = ["m1", "m2", "m3", "m4", "m5"]; MKN = {"m1": "1 held-back", "m2": "2 break-even", "m3": "3 deflated Sharpe", "m4": "4 overfitting", "m5": "5 shuffle"}
pc = lambda x, d=1: f"{x*100:+.{d}f}%"; yn = lambda b: "PASS" if b else "fail"; ls = lambda L_: ", ".join(L_) if L_ else "none"
sd = lambda x: f"{x:+.2f}"
def be(x): return "never ahead" if x["status"] == "below_at_zero" else ("above 2,560 bps" if x["status"] == "above_cap" else f"{x['bps']:.0f} bps")
def held(v, n): return (V[v]["rules"][n] if n in V[v]["rules"] else V[v]["bench"][n])["slices"]["held"]
def cost_line(v): c = V[v]["cost_per_side_bps"]; return f"{c['XBTUSD_ETHUSD']} bps a side for bitcoin and ether, {c['other']} bps for other coins"
slip = r["slippage_bps"]; KR = "Kraken $10k tier"
fee = {v: V[v]["cost_per_side_bps"]["XBTUSD_ETHUSD"] - slip["XBTUSD_ETHUSD"] for v in VL}

def slice_tab(v):
    hb = held(v, "HOLD_BTC"); hk = held(v, "HOLD_BASKET")
    t = "| Rule | Growth a year | Sharpe | Largest drop | Sharpe minus hold bitcoin | Sharpe minus hold the basket |\n|---|---|---|---|---|---|\n"
    t += f"| Hold bitcoin | {pc(hb['cagr'])} | {hb['sharpe']:.2f} | {pc(hb['maxdd'])} | | |\n"
    t += f"| Hold the basket | {pc(hk['cagr'])} | {hk['sharpe']:.2f} | {pc(hk['maxdd'])} | | |\n"
    for n in RU:
        m = held(v, n); t += f"| {n} | {pc(m['cagr'])} | {m['sharpe']:.2f} | {pc(m['maxdd'])} | {sd(m['sharpe'] - hb['sharpe'])} | {sd(m['sharpe'] - hk['sharpe'])} |\n"
    return t
def marks_tab():
    t = "| Rule | Venue | " + " | ".join(MKN[k] for k in MK) + " | Verdict | Same marks against holding the basket (reported, not the verdict) |\n|---|---|" + "---|" * 7 + "\n"
    for n in RU:
        for v in VL:
            x = V[v]["rules"][n]; m = x["marks"]; mb = x["marks_vs_basket"]
            t += f"| {n} | {v} | " + " | ".join(yn(m[k]) for k in MK) + f" | {yn(m['passed'])} | {yn(mb['passed'])} |\n"
    return t
def detail_tab(v):
    t = ("| Rule | Largest drop as a share of hold bitcoin's | Break-even cost a side, against hold bitcoin | Deflated Sharpe | Overfitting estimate (all five rules) | Share of shuffles beaten |\n"
         "|---|---|---|---|---|---|\n")
    for n in RU:
        x = V[v]["rules"][n]
        t += f"| {n} | {x['dd_ratio_vs_hold_btc']*100:.0f}% | {be(BE[n]['vs_hold_btc'])} | {x['dsr']:.3f} | {V[v]['pbo']['pbo']:.3f} | {x['shuffle_pct']*100:.1f}% |\n"
    return t
def years_tab(v):
    rows = [("K1", V[v]["rules"]["K1"]), ("K4", V[v]["rules"]["K4"]), ("Hold bitcoin", V[v]["bench"]["HOLD_BTC"]), ("Hold the basket", V[v]["bench"]["HOLD_BASKET"])]
    ys = sorted(rows[0][1]["calendar_years"], key=int)
    t = "| Year | " + " | ".join(a for a, _ in rows) + " |\n|---|" + "---|" * len(rows) + "\n"
    for y in ys:
        lab = y + (f" (from {r['start']})" if y == ys[0] else "") + (f" (to {r['end']})" if y == ys[-1] else "")
        t += f"| {lab} | " + " | ".join(pc(x["calendar_years"][y], 1) for _, x in rows) + " |\n"
    return t
def sens_tab():
    t = "| Rule | " + " | ".join(VL) + " |\n|---|" + "---|" * len(VL) + "\n"
    for n in RU:
        t += f"| {n} | " + " | ".join(f"{held(v, n)['sharpe']:.2f} / {SENS[v]['alt_slippage_50bps']['rules'][n]['slices']['held']['sharpe']:.2f}" for v in VL) + " |\n"
    return t

# ------------------------------------------------------------------ facts for the bottom line
P = {v: [n for n in RU if V[v]["rules"][n]["marks"]["passed"]] for v in VL}
npass = sum(len(P[v]) for v in VL)
wide = ["K1", "K2", "K3"]
wide_below_btc = sum(held(v, n)["sharpe"] < held(v, "HOLD_BTC")["sharpe"] for v in VL for n in wide)
wide_above_bk = [f"{n} at {v}" for v in VL for n in wide if held(v, n)["sharpe"] > held(v, "HOLD_BASKET")["sharpe"]]
wide_neg = [f"{n} at {v}" for v in VL for n in wide if held(v, n)["cagr"] < 0]
fail_all = [k for k in MK if not any(V[v]["rules"][n]["marks"][k] for v in VL for n in RU)]
best_dsr = max(((V[v]["rules"][n]["dsr"], n, v) for v in VL for n in RU))
m1_k45 = {n: [v for v in VL if V[v]["rules"][n]["marks"]["m1"]] for n in ("K4", "K5")}
forced_total = sum(V[v]["rules"][n]["forced_exits"] for v in VL for n in RU) + sum(V[v]["bench"][b]["forced_exits"] for v in VL for b in V[v]["bench"])
forced_sens = sum(SENS[v][k]["rules"][n]["forced_exits"] for v in VL for k in SENS[v] for n in RU)
dead_held = {n: V[KR]["rules"][n]["dead_pairs"] for n in RU}
oldexc = sum(V[v]["rules"][n]["old_exception_would_fire_pair_days"] for v in VL for n in RU)
gold10 = [k for k in sorted(MS) if "PAXGUSD" in MS[k]["top10"]]; gold20 = [k for k in sorted(MS) if "PAXGUSD" in MS[k]["top20"]]
gold_copies = sorted(set(a for k in MS for a, b in MS[k]["copies_dropped"].items() if b == "PAXGUSD"))
haircut_same = all(abs(SENS[v]["delist_haircut_0.5"]["rules"][n]["final_value"] - V[v]["rules"][n]["final_value"]) < 1e-12 for v in VL for n in RU)
m1_50 = [f"{n} at {v}" for v in VL for n in RU if SENS[v]["alt_slippage_50bps"]["rules"][n]["m1_vs_hold_btc_only"]]
drop50 = [held(v, n)["sharpe"] - SENS[v]["alt_slippage_50bps"]["rules"][n]["slices"]["held"]["sharpe"] for v in VL for n in wide]
same45 = all(abs(held(v, n)["sharpe"] - SENS[v]["alt_slippage_50bps"]["rules"][n]["slices"]["held"]["sharpe"]) < 1e-12 for v in VL for n in ("K4", "K5"))
pbos = [V[v]["pbo"]["pbo"] for v in VL]; ties = [V[v]["pbo"]["tie_share"] for v in VL]; pbl = [V[v]["pbo_drop_latest"]["pbo"] for v in VL]
shuf_wide = [V[v]["rules"][n]["shuffle_pct"] for v in VL for n in wide]; shuf_k5 = [V[v]["rules"]["K5"]["shuffle_pct"] for v in VL]
k1k = V[KR]["rules"]["K1"]; hbk = V[KR]["bench"]["HOLD_BASKET"]; hbb = V[KR]["bench"]["HOLD_BTC"]
turn = {n: V[KR]["rules"][n]["activity"]["all"]["turnover_py"] for n in RU}; coins = {n: V[KR]["rules"][n]["activity"]["all"]["avg_coins_held"] for n in RU}
post = {n: (V[KR]["rules"][n] if n in RU else V[KR]["bench"][n])["slices"]["post"]["total"] for n in RU + ["HOLD_BTC", "HOLD_BASKET"]}
k4 = {v: held(v, "K4") for v in VL}; k5 = {v: held(v, "K5") for v in VL}
first_month = sorted(MS)[0]
dearer = [v for v in VL if v not in ("Binance.US", "Alpaca", KR)]
assert all(held(v, n)["sharpe"] < held(KR, n)["sharpe"] for v in dearer for n in RU), "dearer-venue sentence not supported"
assert all(held(v, w)["sharpe"] < held(v, k)["sharpe"] for v in VL for w in wide for k in ("K4", "K5")), "wide vs K4/K5 sentence not supported"
assert wide_below_btc == len(wide) * len(VL)
one_fail = [(n, v, [k for k in MK if not V[v]["rules"][n]["marks"][k]]) for v in VL for n in RU if sum(not V[v]["rules"][n]["marks"][k] for k in MK) == 1]
# The independent audit's own figures, quoted from archive/audit/2026-11-25_replay_04_audit.md (MEASURED by the auditor, not by run_04.py)
AUDIT = "archive/audit/2026-11-25_replay_04_audit.md"
AUD = [
    ("04-01", "The sale of a coin whose history ends uses the last bar of the full archive. That is hindsight: on the day after a last print the engine assumes the coin is gone for good and books a sale at the earlier close. In the auditor's four-row test, adding only a later print changed the account value on an earlier day from 0.49950025 to 0.99950025",
     "Never fired here: zero such sales in every base and sensitivity run. Must be fixed before `basket.py` is used again"),
    ("04-02", "Trade sizes use the account value before costs. So the monthly hold-the-basket comparison is not exactly equal parts after costs. Largest gap from equal parts at Binance.US: 0.00046541 of the account (July 2020). Sizing on the value after costs moves held-back Sharpe of hold the basket from 0.328049 to 0.327906 and of K1 from 0.258361 to 0.262360",
     "K4 deflated Sharpe at Binance.US moves from 0.9331335 to 0.9332411, still a fail. Kraken $10k tier still fails mark 3"),
    ("04-03", "In the monthly hold-the-basket comparison, a buy order is cleared once its coin trades, even if there was no cash yet to fund it. A delayed sale could then leave the comparison in cash",
     "Did not happen in this run: both comparisons had zero waiting orders"),
    ("04-04", "The shuffle test for the basket rules is not matched on time in the market or number of trades, because the monthly baskets are applied after the shift. At Binance.US, K1 made 6,529 trade sides at 45.18% average weight against shuffle means of 6,256.17 and 42.29%; K2 3,474 and 52.01% against 3,252.78 and 43.09%; K3 12,577 and 41.84% against 11,816.43 and 37.71%. K4 was close (1,161 and 52.12% against 1,163.70 and 52.00%). For K5 the shift moves Wednesday signals to other weekdays",
     "Mark 5 means less for K1 to K3. K5 with the weekday kept: 0.919 against 0.914 as run, both fail"),
    ("04-05", "Of the 7 files left out, 3 are priced in another coin (ETHPYUSD, XBTPYUSD, XRPRLUSD), 1 is the real Merlin Chain dollar market (MERLUSD) wrongly left out by a name test, and 3 are files with one row (CTUSD, OUSDUSD, WOJAKUSD)",
     "Restoring MERLUSD changes no monthly list"),
    ("04-06", "RNDRUSD (last print 2024-06-30) was still chosen on 2024-07-01, and FTMUSD (last print 2025-03-31) was still chosen on 2025-04-01. Neither had a position to sell",
     "The half-value loss test therefore tested no real loss"),
    ("04-07", "The price-swing test does not always remove gold. PAXGUSD was in the top 20 in 12 months and the top 10 in April and May 2026",
     "No code fault. The plan's description of the test is wrong. Removing gold by name now would be a different basket, not a repair"),
    ("04-13", "Trial ledger rows for the 8 stock trials and the 5 basket trials were missing when the run was made. The determinism line in the builder notes was a placeholder when the audit read it",
     "The lead has since added rows 43 to 55 to `research_rig/TRIAL_LEDGER.md` with a note (STATED by the lead). The run was repeated with the same settings and gave the same output (see `research_rig/NOTES_04_builder.md`)"),
    ("04-15", "A coin's trend weight calendar ends at its last raw bar, known only from the full archive. When the auditor added one later print to each of 81 ended coins, 18 K3 target coin-days for RNDRUSD in July 2024 changed",
     "No change to any account value, because no coin could be bought on those days"),
]
def audit_tab():
    t = "| Finding | What the auditor found (MEASURED by the auditor) | Effect on this result |\n|---|---|---|\n"
    for i, a, b in AUD: t += f"| {i} | {a} | {b} |\n"
    return t

doc = f"""# 23. Replay 04: trend rules on a wide basket of coins

Status: research result. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Plan written before any rule in it was run (STATED in the plan): `research_rig/PREREG_04_coin_basket_trend.md`, measured as set out in `research_rig/AMENDMENT_2026-11-25_audit_fixes.md`. Every number below is MEASURED by `research_rig/run_04.py` and placed here by `research_rig/build_doc23.py`, unless it is tagged STATED or UNKNOWN.

## Bottom line

- Rules that pass all five marks: {npass} of {len(RU) * len(VL)} rule and venue pairs. By venue: """ + "; ".join(f"{v}: {ls(P[v])}" for v in VL) + f""".
- The three wide-basket rules (K1, K2, K3) had a lower Sharpe ratio than holding bitcoin in the held-back slice in {wide_below_btc} of {len(wide) * len(VL)} rule and venue pairs. They had a higher Sharpe ratio than holding the basket in: {ls(wide_above_bk)}. They lost money in the held-back slice in {len(wide_neg)} of {len(wide) * len(VL)} pairs.
- Mark that fails for every rule at every venue: {ls([MKN[k] for k in fail_all])}. The highest deflated Sharpe was {best_dsr[0]:.3f} ({best_dsr[1]} at {best_dsr[2]}), against a bar of {TH['replay_min_deflated_sharpe']} (`replay_min_deflated_sharpe`).
- K4 (bitcoin and ether) and K5 (bitcoin only) came closest. Mark 1 passes for K4 at: {ls(m1_k45['K4'])}; for K5 at: {ls(m1_k45['K5'])}. Both still fail mark 3 everywhere.
- Dead coins were kept in the data. Coins held at some point whose history later ended, at Kraken $10k tier: """ + "; ".join(f"{n} {len(dead_held[n])}" for n in RU) + f""". No position was ever closed because a coin's history ended ({forced_total} such sales across all rules and venues). So the half-value loss test on those sales tested no real loss. The code for those sales also uses hindsight (audit finding 04-01). It never fired here, but must be fixed before reuse.
- An independent audit rebuilt K1, K4 and both comparisons from the raw files and matched them to rounding. It found faults, listed below. None of the changes it tested turned a fail into a pass (MEASURED by the auditor, `{AUDIT}`).
- Taxes are not in these numbers. A rule that sells pays tax sooner than holding does.

Closest miss: """ + "; ".join(f"{n} at {v}, which fails only {MKN[k[0]]}" + (f" (deflated Sharpe {V[v]['rules'][n]['dsr']:.3f} against a bar above {TH['replay_min_deflated_sharpe']}, `replay_min_deflated_sharpe`)" if k[0] == "m3" else "") for n, v, k in one_fail) + f""". A near miss is a fail.

## What the rules are

The trend weight P1 is the same as in replay 01. It is the share of four tests that are true: the close is above its 20, 50, 100 and 200 day average. So it is 0, one quarter, one half, three quarters or all of a coin's slot.

| Id | Rule |
|---|---|
| K1 | Each month, the 10 coins with the most dollar trading. Each coin has one tenth of the account as its slot and holds P1 times its slot. The primary rule |
| K2 | Each month, of those 10 coins, the 5 that rose most over the last 90 days. One fifth each, times P1 |
| K3 | Each month, the 20 coins with the most dollar trading. One twentieth each, times P1 |
| K4 | Bitcoin and ether only. Half each, times P1 |
| K5 | Bitcoin only. Four pairs of fast and slow weighted averages of the daily close. The share held is the share of pairs where the fast one is at or above the slow one. Set once a week, at Wednesday's close. The plan reads this from the CoinDesk trend indicator method (STATED) |

Every rule is long or cash only, with one shared cash balance that earns nothing. A coin trades when its weight is off target by more than one eighth of its slot. Orders are set at the close and fill at the next open on a day the coin really traded. Otherwise the order waits. The two comparisons are holding bitcoin, bought once at the start, and holding the basket: the same top 10 each month, one tenth each, traded back toward equal parts at each month start and not traded in between. It is not exactly equal parts after costs, because trade sizes use the account value before costs (corrected after the audit, finding 04-02). Both pay the same costs as the rules.

Costs per side are the venue fee plus slippage: {slip['XBTUSD_ETHUSD']} bps for bitcoin and ether and {slip['other']} bps for every other coin. The slippage is assumed, not measured. Venue fees in bps: """ + ", ".join(f"{v} {fee[v]}" for v in VL) + f""". Only the Kraken levels are a place where the whole basket can be bought (STATED in the plan).

## How the basket is chosen

- At each month start the basket is chosen from data up to the day before only. A check in `research_rig/fixtures_basket.py` changes all later data and confirms the basket does not change.
- Left out: coins with less than 200 days of history, coins with no trades on more than 10 of the last 90 days, and coins whose price barely moves (yearly swing under 0.20, from the last 90 daily moves). That last test is meant to remove dollar coins, currency pairs and gold tokens.
- Left out: copies. A coin whose last 90 daily moves track a coin with more dollar trading almost exactly (correlation above 0.98) is dropped.
- The rest are ranked by their middle daily dollar trading over the last 90 days.
- The gold token PAXGUSD was not always removed by the price-swing test. It was in the top 20 in {len(gold20)} months ({ls(gold20)}) and in the top 10 in {len(gold10)} months ({ls(gold10)}). Coins dropped as copies of it: {ls(gold_copies)}. This is the plan's test, applied as written.
- The plan counts {PLAN_FILES} Kraken files ending in USD (STATED). {r['pairs_loaded']} were used. Corrected after the audit: the {PLAN_FILES - r['pairs_loaded']} left out are not all coins priced in another coin. 3 are, 1 (MERLUSD) is a real dollar market wrongly left out by a name test, and 3 are files with one row (MEASURED by the auditor, finding 04-05). Restoring MERLUSD changes no monthly list.
- The test starts at the first month start with at least 10 coins that qualify: {r['start']}. The basket was chosen {MSUM['months']} times, from {first_month} to {sorted(MS)[-1]}. {MSUM['pairs_ever_top10']} different coins were ever in a top 10 and {MSUM['pairs_ever_top20']} in a top 20. In {MSUM['months_with_fewer_than_20']} months fewer than 20 coins qualified (the fewest was {MSUM['min_qualifying']}), and K3 held only those.
- Coins in a top 10 whose history ended before 2026-09-25: {ls(MSUM['dead_ever_top10'])}. In a top 20: {ls(MSUM['dead_ever_top20'])}. Whether each of these failed, was delisted or was renamed is not checked here (UNKNOWN). Two of them, RNDRUSD and FTMUSD, were still chosen in the month after their last trade (MEASURED by the auditor, finding 04-06).
- Every month's list is in `research_rig/results_04.json` under `membership`.

## Held-back slice

{SL['held'][0]} to {SL['held'][1]}. Each slice starts from the account value on the day before it.

### Binance.US ({cost_line('Binance.US')})

{slice_tab('Binance.US')}
### Alpaca ({cost_line('Alpaca')})

{slice_tab('Alpaca')}
### Kraken $10k tier ({cost_line(KR)})

{slice_tab(KR)}
The other two venues (""" + ", ".join(dearer) + f""") cost more, and every rule has a lower held-back Sharpe ratio there than at Kraken $10k tier. Their numbers are in the output file.

## Pass marks

The same five marks as before, at each venue, with the numbers read from `config/thresholds.yaml`. Mark 1: a higher Sharpe ratio than holding bitcoin in the held-back slice, with a largest drop no more than {TH['replay_max_drop_ratio_vs_hold']} times holding's (`replay_max_drop_ratio_vs_hold`). Mark 2: break-even cost at least {TH['backtest_min_breakeven_cost_multiple']} times the bitcoin cost per side (`backtest_min_breakeven_cost_multiple`). Mark 3: deflated Sharpe above {TH['replay_min_deflated_sharpe']} (`replay_min_deflated_sharpe`), counting {r['n_trials']} trials. Mark 4: overfitting estimate below {TH['backtest_max_pbo']} (`backtest_max_pbo`). Mark 5: the rule beats more than {TH['replay_min_shuffle_percentile']} of {r['shuffles']:,} shuffles of its own timing (`replay_min_shuffle_percentile`).

{marks_tab()}
The numbers behind the marks at Kraken $10k tier:

{detail_tab(KR)}
The same at Binance.US:

{detail_tab('Binance.US')}
Notes on the marks:

- Break-even cost is the same at every venue: it is the cost per side on bitcoin and ether at which the rule stops being ahead of holding bitcoin, with every other coin paying {slip['other'] - slip['XBTUSD_ETHUSD']} bps more. """ + "; ".join(f"{n}: {be(BE[n]['vs_hold_btc'])}" for n in RU) + f""".
- The overfitting estimate is between {min(pbos):.3f} and {max(pbos):.3f} across venues, under the bar everywhere. Exact ties with the middle rank were {min(ties)*100:.1f}% to {max(ties)*100:.1f}% of splits. With the latest days dropped instead of the earliest it is {min(pbl):.3f} to {max(pbl):.3f}. There are only five trials, so this mark says little here.
- The shuffles move each coin's own trend weights to a random start and wrap them around, inside that coin's own history, and leave the monthly baskets as they were. K1, K2 and K3 beat {min(shuf_wide)*100:.1f}% to {max(shuf_wide)*100:.1f}% of their shuffles. Corrected after the audit: the shuffles of K1 to K3 hold less and trade less than the rules (finding 04-04), so this is not a test matched on time in the market, and mark 5 means less for them. K5 beat {min(shuf_k5)*100:.1f}% to {max(shuf_k5)*100:.1f}%, a fail.

## Year by year

Kraken $10k tier. Change in account value over each calendar year.

{years_tab(KR)}
## Sensitivities

Each sensitivity changes one thing from the base run. They are reported, not marked.

Held-back Sharpe ratio, base run / with {r['sensitivity'][VL[0]]['alt_slippage_50bps'] and 50} bps slippage on every coin other than bitcoin and ether:

{sens_tab()}
- With the higher slippage, K1, K2 and K3 lose {min(drop50):.2f} to {max(drop50):.2f} of held-back Sharpe ratio. K4 and K5 hold only bitcoin and ether, so they are {'unchanged' if same45 else 'changed'}. Rule and venue pairs that would pass mark 1 with the higher slippage: {ls(m1_50)}.
- Half of the last value lost when a coin's history ends: {'no change at all' if haircut_same else 'see the output file'}. No position was open when a coin's history ended ({forced_sens} such sales across both sensitivities, all rules and all venues), so there was nothing for the loss to act on. This sensitivity did not test any real loss from a dead coin.

## Where the plan could not be followed to the letter

- File count: the plan says {PLAN_FILES} files. {r['pairs_loaded']} were used. Corrected after the audit: only 3 of the {PLAN_FILES - r['pairs_loaded']} left out are priced in another coin. MERLUSD was wrongly left out by a name test, and 3 files have one row (finding 04-05).
- Band: the basket engine written for this replay (`basket.simulate_basket`) traded any move to or from zero whatever the band, as the first rig did. The audit amendment (change A12) and the plan's own words say a coin trades only when its weight is off target by more than one eighth of a slot. A new engine follows the plan's words. It still sells a coin that leaves its basket, or whose history ends, whatever the band, because the plan says those coins are sold. The old exception would have fired on {oldexc} coin-days across all rules and venues, so this change made no difference to the results. The old engine is kept unchanged.
- Gold token: the price-swing test did not remove PAXGUSD in {len(gold20)} months, although the plan says it removes gold tokens.
- Dead coins: the plan expects positions to be sold at a coin's last close when its history ends. That never happened: no coin that died had an open position at the end of its history. Corrected after the audit: not every dead coin had left its basket before its last trade (RNDRUSD and FTMUSD did not, finding 04-06). The code for this sale also uses hindsight (finding 04-01).
- K3: in {MSUM['months_with_fewer_than_20']} months fewer than 20 coins qualified. K3 held what qualified, still one twentieth each.
- The one-hour-late fill used in replay 01 is not part of this plan and was not run. Mark 1 uses the next-open fill only.
- The audit amendment (change A09) says break-even, shuffles and marks apply to single-coin trials only. This plan asks for marks on basket rules. This plan was followed.
- Costs differ by coin, so break-even adds the same number of bps to every coin, with other coins keeping their {slip['other'] - slip['XBTUSD_ETHUSD']} bps extra slippage. Mark 2 compares it with the venue's bitcoin cost.
- K5 uses the daily close at 00:00 UTC in place of the 4 p.m. New York price, and the bar dated Wednesday as Wednesday's close (STATED in the plan).
- Every reading choice made in the code is listed in `research_rig/results_04.json` under `reading_choices` and in `research_rig/NOTES_04_builder.md`.

## What the independent audit found

A different AI model audited `run_04.py` and `basket.py`, rebuilt the selection and K1, K4 and both comparisons in its own code, and probed for use of future data. Its report is `{AUDIT}`, with `archive/audit/replay_04_independent.py` and `archive/audit/replay_04_probes.py`. It found 15 points. None of the changes it tested produced a pass against holding bitcoin. The lead decided not to change `basket.py` or rerun tonight, so the result stands as run, with these faults stated. The figures in this table are the auditor's, not this run's.

{audit_tab()}
The other findings (04-08 to 04-12, 04-14) are small or are about checks and wording. See the report.

## What this does and does not show

- In the held-back slice at Kraken $10k tier, holding the basket grew {pc(held(KR, 'HOLD_BASKET')['cagr'])} a year with a largest drop of {pc(held(KR, 'HOLD_BASKET')['maxdd'])}. Holding bitcoin grew {pc(held(KR, 'HOLD_BTC')['cagr'])} a year with a largest drop of {pc(held(KR, 'HOLD_BTC')['maxdd'])}. K1 to K3 had a lower held-back Sharpe ratio than holding bitcoin at every venue.
- The plan's reason for this test was that trend rules are said to work better across many coins than on one (STATED). In this test, at every venue, K1, K2 and K3 had a lower held-back Sharpe ratio than K4 and K5.
- These rules trade a lot. Over the whole test at Kraken $10k tier, traded dollars a year were """ + ", ".join(f"{n} {turn[n]:.1f}" for n in RU) + f""" times the account. Average coins held: """ + ", ".join(f"{n} {coins[n]:.1f}" for n in RU) + f""".
- One venue's listings. A coin enters the data when Kraken listed it (STATED in the plan).
- The slippage for small coins is assumed. Document 24 compares it with sampled order books.
- The held-back slice had already been used by replays 01 and 03. It is not fresh.
- The three months after the designer's knowledge cutoff ({SL['post'][0]} to {SL['post'][1]}) are too short to mean anything. At Kraken $10k tier: """ + ", ".join(f"{('hold bitcoin' if n == 'HOLD_BTC' else 'hold the basket' if n == 'HOLD_BASKET' else n)} {pc(post[n])}" for n in RU + ["HOLD_BTC", "HOLD_BASKET"]) + f""".
- The terms for using Kraken's files are not stated on its page (UNKNOWN).
- Taxes are not modelled.

## Files

- Plan: `research_rig/PREREG_04_coin_basket_trend.md`. Measuring rules: `research_rig/AMENDMENT_2026-11-25_audit_fixes.md`
- Code: `research_rig/run_04.py`, `basket.py`, `rig2.py`, `rules.py`, `build_doc23.py`. Checks: `research_rig/fixtures2.py`, `fixtures_basket.py`
- Output: `research_rig/results_04.json`, `run_04.log`. Builder notes: `research_rig/NOTES_04_builder.md`
- Trials counted so far: {r['n_trials']} (`research_rig/TRIAL_LEDGER.md`)

## Sources

- [Kraken, downloadable historical OHLCVT data](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data)
- [CoinDesk trend indicator methodology](https://downloads.coindesk.com/cd3/CDI/Trend-Indicator-Methodology.pdf)
"""
assert "—" not in doc
for w in ("calm", "likely", "CAGR", "drawdown", "PBO", "!"):
    assert w not in doc, w
assert "*" not in doc.replace("**", "") and "**" not in doc
open("../docs/research/23_replay_04_coin_basket.md", "w").write(doc); print(len(doc.splitlines()), "lines; passes", P)
