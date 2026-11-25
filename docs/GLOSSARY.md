# Glossary

Status: CURRENT. Written 2026-11-25.

Plain definitions of the terms, test names and rule names used in this repo. This page defines words. It holds no results and no numbers that belong in `config/thresholds.yaml`. Results are in `docs/STATUS.md`. Where a definition and a test plan disagree, the plan (`research_rig/PREREG_*.md`) is right for that test.

## Measures

| Term | Meaning |
|---|---|
| bps | Basis points. Hundredths of a percent. 30 bps is 0.30% |
| Cost per side | What one buy or one sell costs: the venue's taker fee plus an allowance for the spread and for moving the price |
| Round trip | One buy and the sell that closes it. It costs two sides |
| Trade side | One buy or one sell. A rule's count of trade sides is how often it paid the cost per side |
| Hold, buy and hold | Buy once at the start and never sell |
| Comparison | What a rule is measured against: holding the same thing over the same dates and paying the same cost. A plan can name a different comparison for one rule, and says so |
| Yearly growth | The steady yearly rate that would turn the starting balance into the ending balance |
| Largest drop | The biggest fall from a high point to a later low point. Also called drawdown |
| Sharpe ratio | Average return divided by how bumpy the ride was, per year. Higher is better. The crypto replays count cash as earning nothing. Replay 05 measures it above the Treasury bill return |
| Deflated Sharpe ratio | The chance that a rule's Sharpe ratio is above what the best of many worthless rules would show by luck. It falls as the number of trials rises. [Bailey and Lopez de Prado](https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf) |
| Overfitting estimate, PBO | Probability of backtest overfitting. The history is cut into blocks. For each way of splitting the blocks in two, the rule that looked best on one half is checked on the other. The estimate is how often it landed in the bottom half there. Lower is better. [Bailey and others](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) |
| Shuffle percentile | The rule's own in and out spells are put in random order many times. The percentile is the share of those random orders that the real rule beat. It asks whether the timing did anything |
| Break-even cost | The cost per side at which the rule stops beating its comparison |
| Break-even multiple | Break-even cost divided by the cost the test assumed |
| Knife edge | A result that passes or fails on a small change that should not matter, such as the start date |

## How a test is run

| Term | Meaning |
|---|---|
| Replay | A rule run over past prices with costs. Also called a backtest. It is not a practice account and not live trading |
| Plan, PREREG | The file that fixes a test's rules, data, costs, slices and pass marks before the test runs. `research_rig/PREREG_*.md` |
| Amendment | A dated file that records a correction after a fault was proved. Whether a rerun may follow depends on the kind of fault (see Rerun) |
| Development slice | The earlier part of the history. Free to look at |
| Held-back slice | The later part of the history, kept unseen until the rules are fixed. Each frozen rule is meant to be run on it once. Also called out of sample |
| Trial | One rule variant that was run. Every trial is counted, because the more rules are tried, the more likely one looks good by luck |
| Trial ledger | The list of every trial and rerun. `research_rig/TRIAL_LEDGER.md`. A result with no row there does not count |
| Rerun | A second run of the held-back slice. The owner allows one case, in his words: "when a machine check proves the engine itself was wrong, the slice is rerun once the fix is in. That rerun is written in the trial ledger, counted as a trial and reported as a rerun" (`docs/quality/01_the_bar.md`). Research read R1 as that case: two code audits by other models found faults in how trades were simulated and how the pass marks were worked out. Whether a code audit is a "machine check", and whether the pass-mark code is "the engine itself", is research's reading and has not been put to the owner before (question 18c). R2 was not that case: the engine was right and one rule was coded differently from its plan (questions 18a and 18b in `docs/decisions/morning_list_2026-11-25.md`). He wrote the rule for the Builder; research applies it to its own tests |
| Machine check | The owner's words in his rerun rule. He does not define them. Research's reading: a check a machine can repeat with the same answer each time, such as a fixture with a known answer (`research_rig/fixtures2.py`) or a second model rebuilding a result from the raw data in its own code. A model reading code and giving an opinion is weaker than that. Not settled (question 18c) |
| Pass marks | The five tests a replay must pass, listed in `research_rig/README.md`. The numbers are keys in `config/thresholds.yaml` |
| Replay pass | All five marks met in a replay. It earns a place in a practice account test and nothing more |
| Practice account pass | The bars a rule must meet in a practice account before live money is discussed. Not fully defined yet. The keys that start with `paper_` in `config/thresholds.yaml` set only the least number of days and trades. The playbook also asks for slippage and errors "within tolerance", and no number exists for that. Until the owner sets one, no rule can pass this gate. No rule has been run in a practice account yet |
| Practice account | A broker account that trades with pretend money at real prices. Also called paper trading |
| Fresh | Said of a held-back slice no rule has been run on. Once a rule has been run on it and the result seen, it is no longer fresh for that rule |
| First run, corrected run | Where a test was run twice because of a proved fault. Both are kept and both are reported. After an engine fault (R1) the rerun is the one judged, on research's reading of the owner's rule (question 18c). After a fault in one rule's code (R2, replay 05) which run is judged is not settled: the first run stands until the owner answers questions 18a and 18b in `docs/decisions/morning_list_2026-11-25.md` |

## Evidence labels

| Label | Meaning |
|---|---|
| MEASURED | Independent data, official rule text, a published price page, or our own logged test |
| STATED | Claimed by a vendor, author or promoter and not independently verified |
| UNKNOWN | Could not be verified. A thing to test, not a fact |
| OWNER | In `docs/quality/`: the owner's own rule |
| TRANSLATED | In `docs/quality/`: a proposal that applies the owner's method to this project. Not a rule until he confirms it |
| CURRENT, RECORD, DRAFT, RAW | Page status used in `docs/INDEX.md`, defined at the top of that file. A page that a later one corrects is marked RECORD. CURRENT means not replaced. It does not mean approved or proven |

## Tests

| Name | What it is | Plan |
|---|---|---|
| Replay 01 | Nine daily trend rules on bitcoin and ether, at five venue costs | `PREREG_01_daily_crypto_trend.md` |
| X1 | Replay 01's main rules on a second price source over a short recent window. A cross-check, not a new trial | Amendment 1, a section at the end of the replay 01 plan |
| S1 | Replay 01 with the fill moved one hour and one day later. A sensitivity check | `PREREG_01_S1_fill_delay.md` |
| X2 | Replay 01's rules on Kraken's full published history | `PREREG_01_X2_kraken_full_history.md` |
| S2 | The same on a longer ether history. A sensitivity check | Same file as X2 |
| Diagnostic, DIAG | One pass mark worked out on Bitstamp prices from the Kraken start date, to tell a price effect from a date effect. Written after seeing X2. Changes no verdict | None |
| Pilot 02 | A small trial of AI models making the daily call. Inconclusive by design | `PREREG_02_ai_calls_pilot.md` |
| Replay 03 | Eight hourly rules on bitcoin and ether | `PREREG_03_intraday_crypto.md` |
| Replay 04 | Trend rules on a wide basket of coins | `PREREG_04_coin_basket_trend.md` |
| Replay 05 | Eight trend and sizing rules on the US stock market index from 1927 | `PREREG_05_stock_trend_free_data.md` |
| Replays 06 and 07 | Draft plans. Not run | `PREREG_06_*`, `PREREG_07_*` |
| R1 | The rerun of replays 01 and 03 with the cross-checks, after two code audits | `AMENDMENT_2026-11-25_audit_fixes.md` |
| R2 | The corrected run of replay 05 | `AMENDMENT_05_I2_equal_thirds.md` |
| v1, v2 | The first engine and the engine after the audit fixes. v2 results are the ones judged | `research_rig/README.md` |

## Rules tested

The plan of each test holds the exact wording. These lines are for recognition only.

| Id | Rule | Test |
|---|---|---|
| P1 | Trend ensemble. The share of four checks that are true: close above its 20, 50, 100 and 200 day average | 01 |
| P2 | P1, sized down when recent volatility is high | 01 |
| S50, S100, S200 | In when the close is above its 50, 100 or 200 day average, else cash | 01 |
| D20, D55 | In on a new 20 or 55 day high. Out on a new 10 or 20 day low | 01 |
| M30, M90 | In when the close is above the close 30 or 90 days ago, else cash | 01 |
| PORT-P1, PORT-P2 | Half the account on bitcoin and half on ether, each running P1 or P2. The mixed portfolios | 01 |
| H1 | Half-day momentum: buy at midday if the day is up, exit at day end | 03 |
| H2 | Opening range breakout | 03 |
| H3 | Last hour timing | 03 |
| H4, H5 | Buy a sharp hourly dip and hold four hours. H5 only in an up trend | 03 |
| H6 | Hourly trend with no day-end exit | 03 |
| H7 | H1 only on days when P1 is at least half in | 03 |
| H8 | Noise band breakout, after a published rule for SPY | 03 |
| K1, K3 | Top 10 or top 20 coins by volume, equal slots, each slot times its own P1 | 04 |
| K2 | The 5 strongest of the top 10 over 90 days, each times P1 | 04 |
| K4 | Bitcoin and ether, half each, times P1 | 04 |
| K5 | A published weekly trend rule on bitcoin | 04 |
| T1 | Ten-month rule: hold the market when it is above its 10 month average, else cash. Checked monthly | 05 |
| T2 | 200-day rule, checked daily | 05 |
| T3 | Twelve-month momentum against the bill return | 05 |
| T4 | P1 on the stock index | 05 |
| T5 | Trendpilot, the first version of a published fund rule | 05 |
| V1 | Size by volatility only, no trend | 05 |
| I1 | Twelve industry groups, each following T1 | 05 |
| I2 | The three leading industry groups, held only when T1 says hold the market | 05 |

## Venues and data

| Term | Meaning |
|---|---|
| Venue | A broker or exchange where an order is placed |
| Venue cost levels | Binance.US, Alpaca, Kraken at its $10k a month fee tier, Kraken entry tier, Coinbase entry tier. The replays use each venue's fee as a cost level. Only Bitstamp and Kraken prices were used |
| Bitstamp history, Kraken history | The two price histories the crypto replays ran on. "Both histories" means both |
| French library | Kenneth French's public data library: daily US stock market and industry returns from 1926 |
| Taker fee | The fee for an order that fills at once against resting orders |
| Slippage | The gap between the price expected and the price paid |
| Order book | The list of resting buy and sell orders at a venue. Its depth says how large an order can be before it moves the price |

## Build method words

These come from the owner's files in `docs/quality/`. Read them there. Nothing is being built yet.

| Term | Meaning |
|---|---|
| Kit | The set of files a builder model works from with no memory of any chat. `docs/quality/02_how_we_build.md` |
| Builder | The mode that builds unattended from the kit |
| Partner | The interactive mode that reviews a build with the owner and writes fix prompts. It writes no product code |
| Gate | A checkable line at the end of a build phase |
| Engine | Two meanings. In the owner's rerun rule and in `research_rig/`: the test code that simulates trades on past prices and works out the pass marks (`rig.py`, then `rig2.py`). It is not the code of any one rule. In the planned product: see the next row |
| Engine, service | In the planned product: the always-on program that reads prices, applies rules and risk limits, and places orders. It works with every model switched off |
| Escalation gate | In the planned product: plain code that decides when a finding is worth sending to the top model. `AGENTS.md`, "Model tiers" |
| Research rig | `research_rig/`. The code that ran the replays. Not product code |
| Moonshot sleeve | A small, capped share of the account for high-risk ideas. Its size is an open owner number |
| Owner decision | Something the owner said, recorded in `docs/decisions/` with the date. Nothing else is approved |
| Trade intent, `TradeIntent` | In the planned product: the record that says "buy or sell this much of this". Only fixed-rule code may make one. A model never does (`AGENTS.md` hard rule 1) |
| D1, D2, D3, D4 | Short labels the playbook pages use for four proposals in `docs/decisions/0001-starting-decisions.md`. That file says which row each one is |
| v1 | Two meanings. In the playbook and `docs/quality/`: the first version of the product, which is not built. In `research_rig/`: the first test engine, replaced by v2 |

## Other short names

| Term | Meaning |
|---|---|
| CSCV | The method behind the overfitting estimate: the history is cut into blocks and every half-and-half split is tried. Named in the Bailey paper above |
| CPCV | A related way to split history for testing, which leaves gaps between the parts so they do not leak into each other. Named in the playbook. Not used in any test here |
| DSR, PBO | Deflated Sharpe ratio, and the overfitting estimate. Both defined under "Measures" |
| Durbl, BusEq and the other industry names | The French library's short names for its twelve industry groups: NoDur consumer nondurables, Durbl consumer durables (cars, TVs, furniture, appliances), Manuf manufacturing, Enrgy oil, gas and coal, Chems chemicals, BusEq business equipment (computers, software, electronics), Telcm telephone and television, Utils utilities, Shops wholesale and retail, Hlth healthcare and drugs, Money finance, Other everything else. MEASURED from the library's [definitions file](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Siccodes12.zip) |
| G1 to G6, N1 to N7 | Rule names in the two draft plans, replays 06 and 07. Defined in those drafts. Not run |
