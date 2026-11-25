# Why the AI traders lost: a reading of every written reason in TM01 to TM04

Made by `timemachine/autopsy/autopsy.py` from the stored session folders of the finished and already scored time machine plans TM01, TM02, TM03 and TM04, and written to `timemachine/autopsy/autopsy_results.json` on 2026-11-25 at 21:56 UTC. Every figure below is MEASURED by that script unless it says otherwise. Pretend money only. How to rerun it is in `timemachine/autopsy/README.md`.

Checked by the lead 2026-11-25 21:47 UTC: the script was rerun and gave the same results file. The labels were not re-read by a second reader.

This is an after-the-fact look at finished tests. It is not a test. It has no pass mark, it changes no result already scored, and anything it suggests is a hypothesis for a new test on months not yet traded.

## What the owner asked and the short answer

- Why do they fail so much? In the crypto plans the market direction and costs explain most of it. 355 round trips made a net -$780.81; costs paid were $678.96, 87.0% of that loss. Before costs the total was -$101.85.
- Was it a stop loss? Mostly yes, their own. 245 of 355 round trips (69.0%) ended when the stop the model had set was reached, 210 of them at a loss.
- Why did they buy where they did? 81.2% of 373 buys came after a 24-hour rise, mean +2.59%. Most reasons describe a breakout, a pullback that held, or a bounce off a floor.
- Did the reasons pick good moments? No more than chance. Five days after a buy the coin was up +0.27%, +0.10% more than the average hour that month. Random twins buying a random coin at the same moments did better: +0.94%.
- Did they sell near lows? A little. After the 210 stop-outs at a loss, the coin was higher a day later 55.6% of the time (207 measured), mean +0.31%.
- Did they cut winners and hold losers? No, the reverse. Winners were held 92.0 hours on average, losers 68.4 hours.
- TM03 (daily bitcoin share): 96.3% of 135 cuts came after a down day and 98.7% of 76 raises after an up day. Against the same month's trend, cuts were followed by -0.06% over five days: no timing skill.
- TM04 (weekly stock basket): added stocks beat the 38-stock average the next week by +0.36% (183 measured), dropped ones lagged by -0.62% (183). Over four weeks the added stocks lagged by -1.01% (165).

## What was read

- Session folders TM01-B01-*, TM02-B02-* (6 models, 5 months each), TM03-D01-* (6 models, 8 months), TM04-D02-* (6 models, 2 runs), and the 1,200 random twin folders TWIN-TM01-* and TWIN-TM02-*, all in the off-repo run folder named in `timemachine/autopsy/settings.py`. No TM06 or VOID folder was opened.
- Prices: 1-minute closes from the recorded tape, read only. Changes after 24, 48 and 120 hours and before 24 hours and 7 days are from the minute at or before each time.
- Costs as stored in each session's config: fee `practice_crypto_fee_bps_added` and half-spread `tm_crypto_half_spread_bps`, both sides. The script adds fee plus spread for every fill in a round trip.
- Base rate: for crypto, every hour of the same session month for the same coin; for TM03, every daily wake of the same month; for TM04, the equal average of all 38 symbols over the same weeks.

## How many answers there are (MEASURED)

| Plan | Sessions | Answers | No-pick answers | Picks | Filled buys | Filled sells |
|---|---:|---:|---:|---:|---:|---:|
| TM01 crypto, prices only | 30 | 1,764 | 1,485 | 279 | 189 | 180 |
| TM02 crypto, with news | 30 | 1,764 | 1,513 | 251 | 184 | 177 |

| Plan | Sessions | Answers | Changes made | Written reasons classified |
|---|---:|---:|---:|---|
| TM03 bitcoin share | 48 | 1,428 | 262 (135 cuts, 76 raises after the opening) | 211 |
| TM04 stock basket | 12 | 300 | 169 | 585 per-stock reasons: 282 added, 186 dropped, 117 kept |

- Per model, buys in TM01 and TM02 together: OPUS 88, KIMI 96, NEON 88, SOL 42, SONNET 37, GROK 22. GROK made 22 buys in 10 months, so every GROK cell below is under 30 and no conclusion is drawn about it.

## The categories and how they were placed (MEASURED)

The categories were fixed in `timemachine/autopsy/categories.md` at 21:27 UTC from a seeded blind sample of 151 texts, before any outcome was joined. A script places a text by rule when exactly one category's words match (`timemachine/autopsy/classify.py`); otherwise the analyst read it and stored a label in `timemachine/autopsy/labels_by_hand.jsonl`. The labels and the hand checks in `timemachine/autopsy/hand_checks.json` carry ids only, no text; the script joins them to the stored answers by id and reports any id it cannot find (none were missing).

| Texts | By rule | By the analyst | Unclear |
|---|---:|---:|---:|
| Crypto buys | 132 | 241 | 0 |
| Crypto sells | 346 | 11 | 0 |
| TM03 dial changes | 22 | 189 | 0 |
| TM04 stock reasons | 512 | 73 | 0 |

Checks of the labels:

- The analyst relabelled a random 60 of the hand labels blind: 60 of 60 agree. This only shows the analyst is consistent minutes later, not that the labels are right.
- The rules against a blind analyst label on a random 60 rule-placed texts: 46 of 60 at first. Two rule faults were then fixed (dropped stocks named only by trailing returns were called momentum; the indicator rule matched the word "small"). The same 60 then agree 55 of 60, but that sample was used for the fix. A fresh sample of 60: 44 of 60 (73.3%). Most disagreements are between neighbours: price only against price plus news for TM04 adds, falling price against bad news for TM04 drops. Read the TM04 category rows with that in mind.

## Crypto round trips (TM01 and TM02), MEASURED

A round trip is the desk's own closed trade: from the first buy of a coin to the sell that brings it back to zero. Gains are after costs. 12 positions were still open at the end of their sessions and are not in these rows.

| Group | Round trips | Made money | Mean result | Median result | Net | Mean hold | Costs paid | Costs as share of the net loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 355 | 121 (34.1%) | -0.80% (-$2.20) | -$5.29 | -$780.81 | 76.5 h | $678.96 | 87.0% |
| TM01 prices only | 179 | 58 (32.4%) | -0.93% | -$6.05 | -$549.57 | 79.7 h | $355.00 | 64.6% |
| TM02 with news | 176 | 63 (35.8%) | -0.67% | -$4.84 | -$231.24 | 73.1 h | $323.96 | 140.1% (gross before costs +$92.72) |

| Model | Round trips | Made money | Net | Costs | Note |
|---|---:|---:|---:|---:|---|
| OPUS | 86 | 30 (34.9%) | -$215.20 | $164.86 | |
| KIMI | 87 | 23 (26.4%) | -$352.84 | $156.50 | lowest share of winners |
| NEON | 81 | 32 (39.5%) | -$8.69 | $173.23 | gross before costs +$164.54 |
| SOL | 42 | 14 (33.3%) | -$62.24 | $64.66 | |
| SONNET | 37 | 15 (40.5%) | -$73.54 | $69.92 | |
| GROK | 22 | 7 (31.8%) | -$68.30 | $49.80 | under 30, no conclusion |

| Month | Round trips | Made money | Net |
|---|---:|---:|---:|
| July | 72 | 28 (38.9%) | -$48.81 |
| August | 72 | 44 (61.1%) | +$534.57 |
| September | 87 | 36 (41.4%) | -$101.63 |
| October | 63 | 4 (6.3%) | -$752.97 |
| November 1 to 24 | 61 | 9 (14.8%) | -$411.97 |

What it shows:

- The month decides more than the model. October and November together lost $1,164.94, more than the whole net loss of $780.81.
- A typical trade risks a stop a median 3.53% below the fill (373 buys, every one had a stop) for a target a median 6.56% above (352 had a target, 166 a time limit). At that ratio a trader needs a little over a third of trades to win before costs; 34.1% did. Costs then turn about even into a loss.
- Limits: costs here are the assumed fee and spread from config; real fills on thin minutes could be worse. Round trips overlap in time and share one market, so the 355 are not 355 independent tries.

## Why they got out (MEASURED)

| How the trade ended | Round trips | Made money | Net |
|---|---:|---:|---:|
| Own stop reached (desk sold) | 245 | 35 (14.3%) | -$1,883.36 |
| Own target reached (desk sold) | 75 | 75 (100%) | +$1,184.47 |
| Own time limit reached | 17 | 7 | +$0.62 (under 30) |
| Model sold by hand, view changed on price | 11 | 1 | -$58.38 (under 30) |
| Model sold by hand on a headline or macro news | 5 | 2 | -$22.80 (under 30) |
| Small gain taken early, rebalancing | 2 | 1 | under 30 |

- The model wrote only 20 of the 357 sells itself. 8 of those 20 say it is leaving before the stop.
- 210 sells were stop-outs at a loss. In the 24 hours before them the coin had fallen in 93.8% of the 210 (mean -2.78%). In the 24 hours after, it rose in 55.6% (207 measured, mean +0.31%, +0.43% above the month's hourly base); after 48 hours, 52.7% higher, mean +0.12%. So stops were hit near short-term lows slightly more often than not, but the bounce was small next to the 3.78% average loss on a stopped trade.
- 35 stop sells closed at a gain: these are stops the model had raised above its entry.

Did the trade follow the exit plan written at entry?

| What closed the trade | Round trips | Made money | Net |
|---|---:|---:|---:|
| The stop, target or time written in the buying pick, unchanged | 200 | 42 (21.0%) | -$1,318.56 |
| Numbers from a later pick (the plan was revised) | 137 | 75 (54.7%) | +$620.29 |
| A sell the model wrote by hand | 18 | 4 (22.2%) | -$82.54 (under 30) |

- In the 137 revised trades the stop was raised 123 times and left the same 14 times. It was never lowered. The models did not widen stops on losers.
- Limit: a trade can only be revised if it survives to a later wake, so the revised group is made of trades that were already working. This table does not show that revising helps.

## Where they bought (MEASURED)

| Buy reason | Buys | 24 h before the buy | 7 days before | 120 h after, minus the month's base | Twin buys at the same moments, 120 h after |
|---|---:|---:|---:|---:|---:|
| Chasing a rise (breakout) | 107 | +4.67%, up in 98.1% | +7.18% | -0.78%, above base in 39.3% | AI +0.67%, twins +1.63% |
| Pullback in a rise | 81 | +3.27% | +6.72% | +0.57%, 46.3% (80 measured) | AI +1.49%, twins +2.76% |
| A price floor (support) | 36 | +0.41% | -1.70%, up in 25.0% | +2.79%, 52.8% | AI +3.12%, twins +3.69% (35 paired) |
| Bounce after a fall (reversal) | 80 | +0.27% | -2.63%, up in 30.0% | +1.01%, 60.3% (73 measured) | AI -1.03%, twins -1.01% |
| Strongest coin | 29 | +3.10% | +4.15% | -1.32% | under 30 |
| Headline first | 28 | +1.84% | +3.72% | -0.83% | under 30 |
| Indicator reading | 9 | | | | under 30 |
| All buys | 373 | +2.59%, up in 81.2% | +3.44%, up in 60.3% | +0.10%, 46.0% (365 measured) | AI +0.29%, twins +0.94% (371 paired) |

Grouped: 217 buys after a rise (breakout, pullback, strongest coin) were up +3.94% in the day before and then -0.35% against the base over five days (42.6% above base, 216 measured). 116 buys after a fall (floor, reversal) were down -2.34% over the 7 days before and then +1.60% against the base (57.8%, 109 measured).

Round trips by the reason for the first buy:

| Entry reason | Round trips | Made money | Net |
|---|---:|---:|---:|
| Chasing a rise | 101 | 34 (33.7%) | -$117.47 |
| Pullback in a rise | 78 | 26 (33.3%) | -$174.40 |
| Bounce after a fall | 75 | 24 (32.0%) | -$234.17 |
| A price floor | 35 | 17 (48.6%) | +$75.62 |
| Strongest coin | 29 | 7 | -$190.67 (under 30) |
| Headline first | 28 | 11 | -$94.62 (under 30) |

What it shows:

- The written reasons are chart readings, and the same readings appear in winners and losers. Breakouts, pullbacks and reversals each won about a third of the time.
- Most buys follow a rise. After the buy, the coin did no better than an ordinary hour of the same month, and a random coin bought at the same moment did better. The choice of coin, not only the moment, cost them.
- Buys at a floor after a weekly fall are the one group in the black, on 35 round trips. That is just above the 30 line and from one reading of past months.
- Limits: the 120-hour windows overlap and cluster in the same weeks, so the counts overstate independent evidence. Twin buys use the same dollars and wakes but a random coin; their exits differ, so the twin row compares only the price path after entry, not trade results.

Stated plans and confidence:

- 74.0% of buys state a target and 94.1% name a stop in the text; every pick carried a stop number. 42.1% use size words (small, starter, half size). No numeric confidence was seen in the 151-text blind sample; this was not counted over all texts.
- In TM02, 155 of 184 buys (84.2%) cite a headline. Their round trips: 148, of which 37.2% made money, net -$209.84. The 28 round trips without a headline are under 30.

## Were the reasons true? (MEASURED by hand)

- A seeded sample of 60 buys was checked by hand against the minute prices up to the decision time (the same data the model could ask for) and the headlines in its packet. 58 had a checkable price claim. 3 were contradicted (5.2%), 2 more were borderline.
- The three: a coin said to have held a level "for a week" when its 7-day low was below it; a shelf said to be "defended this week" when the week's low was 1.3116 against a shelf of 1.38; a base at 9.5 to 9.8 with a stop at 9.45 when the price had traded at 9.26 within the previous 24 hours.
- So the models mostly describe the chart correctly. The problem is not false reasons; it is that true descriptions of the last few days do not predict the next few.

## TM03: raising and cutting the bitcoin share (MEASURED)

| Change | Count | Bitcoin in the 24 h before | 120 h after, raw | 120 h after, minus the same month's base | 24 h after, minus month base |
|---|---:|---:|---:|---:|---:|
| Cut | 135 | -2.28%, down in 96.3% | -1.39% (134) | -0.06%, above base in 51.5% | +0.17%, 60.0% |
| Raise | 76 | +2.75%, up in 98.7% | +0.58% (73) | +0.59% mean, -0.91% median, 38.4% | -0.16% |

| Cut reason | Count | 120 h after, minus month base |
|---|---:|---:|
| Level broken or lower lows | 100 | -0.42% (99), 52.5% above base |
| Macro or event ahead | 21 | under 30 |
| Flows or headline | 11 | under 30 |

- The dial follows yesterday. Cuts came after down days, raises after up days. Raw numbers make the cuts look right (bitcoin fell after them) only because most cuts happened in falling months: November's daily base over five days was -6.35%, August's +3.84%. Measured against its own month, a cut was followed by almost exactly the month's average move, and on the next day by a small bounce.
- Raises after a rebound were above the month's base in only 38.4% of 73 cases.
- Limits: one run per model per month; the six models read the same headlines and often moved on the same days, so the 135 cuts are far fewer independent decisions.

## TM04: picking and dropping stocks (MEASURED)

| Call | Count | Next week, minus the 38-stock average | Next 4 weeks, minus the average |
|---|---:|---:|---:|
| Added after the first week | 186 | +0.36% (183), beat the average in 55.7% | -1.01% (165), 49.7% |
| Dropped | 186 | -0.62% (183), beat the average in 45.4% | -0.56% (165), 39.4% |
| Kept (only KIMI wrote these) | 117 | -0.68% | -3.63% (103), 38.8% |

| Added for | Count | Next week, minus average |
|---|---:|---:|
| Trailing returns only | 95 | +0.49% (94) |
| Trailing returns and good news | 149 | -0.46%, beat the average in 50.3% |
| Good news only | 24 | under 30 |

- Dropped stocks were mostly falling (166 of 186 by label) and kept lagging the next week and over four weeks, so the drops were mildly right. The adds helped for a week and then gave it back over four.
- Adding news to a momentum reason did not improve the next week.
- Limits: two runs per model over one stretch of months; the category labels for TM04 agreed with a blind reading less often than the others (see the label checks).

## Twelve quotes (from the stored records, checked word for word by the script)

The script also checks that no quote holds a quoted title or shares a run of five words with any headline or summary in its session's packets; all 12 pass.

1. Winning buy, target reached. OPUS, August, TM01: "Range breakout above 67k that held for eight hours."
2. Winning buy, target reached. NEON, August, TM01: "High-volume 30-day breakout above 8.90 resistance with strong 7-day relative strength (+9.47%) and clean hourly uptrend."
3. Losing buy, same pattern, stopped out. SONNET, October, TM01: "Strongest 7d momentum (+16%), holding near highs"
4. Losing buy on an indicator, stopped out within a day. NEON, October, TM01: "Relative-strength leader reclaiming SMA5 (10.56), SMA10 (10.86), and SMA20 (10.84) at 10.937 on expanding volume; stop at 10.05."
5. A stated fact the data contradicts. KIMI, October, TM01: "Base at the 9.5-9.8 support after full washout; tight stop 9.45 gives ~3% risk for swing back to 10.7+."
6. Buying a falling coin on a news item. KIMI, October, TM02: "Re-entering XRP at 1.404 as the Evernorth Nasdaq merger completed (headline 2026-10-10T07:31:15Z) with price still depressed near 1.39-1.40; the old 1.50-1.57 range is the magnet."
7. The same level bought again and again. KIMI, October, TM02: "Sweep-reclaim trade #7 of the month: hack-triggered $1.5B liquidation cascade printed its low at 76k"
8. The model naming its own fault. OPUS, August, TM02: "My stops sat inside normal noise for a market moving 3-5% a day."
9. The model naming its own fault. OPUS, September, TM01: "The ETH and SOL time exits on Sep 26 were a guess I made at entry"
10. Selling by hand before the stop. KIMI, July, TM01: "momentum thesis failed; five sessions of relative weakness versus BTC; taking the small loss before the stop makes it bigger"
11. A dial cut after a down day. GROK, May, TM03: "Cut to half. Bitcoin closed at 78.1k after trading down to 77.6k, and US bitcoin ETFs shed about $1B as inflation fears reversed the inflow streak."
12. Holding a falling stock into results. KIMI, TM04 run 2: "selling before earnings has been my repeated mistake"

## Faults found in the stored records (MEASURED)

- One answer appears word for word in two sessions of the same model run at the same time: "The push through 84k has already faded back to the level..." in TM01-B01-GROK-2026-08 at 2026-08-28 00:00 UTC and in TM02-B02-GROK-2026-10 at 2026-10-22 00:00 UTC. It fits October (bitcoin near 84k) and not late August (near 78k), and it cites stablecoin supply in a plan with no headlines. Most likely one answer reached two concurrent sessions. It was a no-pick answer, so no trade came from it.
- Answers naming a later date: 49 found by the scan; read by hand, 38 name an event scheduled in advance (CPI, FOMC, payrolls, results, an upgrade, a vote, a headline's deadline) and 11 the trader's own time exit or the session close. None reports something that had not happened yet. Timestamps after the wake: 1, the session close time.
- Missing reasons: none. Every buy action has a reason and every pick a thesis; every TM03 and TM04 answer has a why.
- Repeated texts within one session: 16, mostly the same no-pick sentence on consecutive wakes.
- TM02 quoted headlines: 139 quoted in buy reasons, 117 found in that wake's packet. The other 22 may come from news looks the model made; looks are logged without their content, so this is not counted as a fault.
- Faults in this script, found and fixed before the final run: the indicator rule matched the word "small"; the headline flag counted text between two apostrophes and flagged price-only TM01 buys (fixed: 155 flagged, all in TM02); TM03 treated an empty target (all cash) as unchanged, which mislabelled one raise as a cut.

## What this does not show

- It is one look at months already traded and already scored. Nothing here is a pass or a reason to trade.
- Categories come from one analyst. The hand labels were checked only for self-consistency; the rules agreed with a blind reading on 44 of a fresh 60.
- Price changes after a buy or a cut are measured on overlapping windows in a handful of months; many decisions are not independent.
- The contradiction check covers 60 buys and only the claims that can be checked from prices and packet headlines.
- Costs are the assumed fee and spread; 12 positions open at session end are left out of the round trips.

## Three hypotheses worth a new test on months not yet traded

1. Buying only at a floor after a weekly fall does better than buying breakouts. Test: the crypto card with entries limited to price within a set distance of a multi-touch low after a 7-day decline, against the same card limited to breakouts, on new months, with twins. How it could fool us: 35 round trips is barely above the line, floor buys may have clustered in rising weeks, and the label is the analyst's reading of the text.
2. The coin choice costs more than the timing. Test: keep the model's buy times and exits but trade bitcoin only, against the model's own coin, on new months. How it could fool us: twins and the model differ in exits as well as coins, bitcoin may simply trend differently in the new months, and fewer coins means fewer trades and more noise.
3. The bitcoin dial reacts to the last day and adds nothing; a dial that may change only on weekly closes would keep the same view and pay less. Test: the TM03 card with changes allowed once a week, against the daily card and against hold, on new months. How it could fool us: a week of cash in a sharp rise or fall swamps everything else, six models moving together look like six results, and one run per month leaves run-to-run variation unmeasured.
