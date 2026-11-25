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
| Rerun | A second run of the held-back slice. The owner allows one case, in his words: "when a machine check proves the engine itself was wrong, the slice is rerun once the fix is in. That rerun is written in the trial ledger, counted as a trial and reported as a rerun" (`archive/quality/01_the_bar.md`). Research read R1 as that case: two code audits by other models found faults in how trades were simulated and how the pass marks were worked out. R1 also carried two changes that were not engine faults (a stricter pass mark 1, and what holding pays when the break-even cost is worked out), listed in `docs/STATUS.md` under "Known faults and slips". Whether a code audit is a "machine check", and whether the pass-mark code is "the engine itself", is research's reading and has not been put to the owner before (question 18c). R2 was not that case: the engine was right and one rule was coded differently from its plan (questions 18a and 18b in `archive/decisions/morning_list_2026-11-25.md`). He wrote the rule for the Builder; research applies it to its own tests |
| Machine check | The owner's words in his rerun rule. He does not define them. Research's reading: a check a machine can repeat with the same answer each time, such as a fixture with a known answer (`research_rig/fixtures2.py`) or a second model rebuilding a result from the raw data in its own code. A model reading code and giving an opinion is weaker than that. Not settled (question 18c) |
| Pass marks | The five tests a replay must pass, listed in `research_rig/README.md`. The numbers are keys in `config/thresholds.yaml` |
| Replay pass | All five marks met in a replay. When credited, it earns a place in a practice account test and nothing more. A pass is credited only when the run that made it followed the rules: plan and ledger row before the run, no change to a rule, cost or pass mark after a result was seen. Research recommends that no pass from 2026-11-25 is credited (question 18b in `archive/decisions/morning_list_2026-11-25.md`). The owner has not answered |
| Practice account pass | The bars a rule must meet in a practice account before live money is discussed. Not fully defined yet. The keys that start with `paper_` in `config/thresholds.yaml` set only the least number of days and trades. The playbook also asks for slippage and errors "within tolerance". What is measured, in what unit, and how much is allowed are all undefined (question 17). The live gate that follows, "live results track paper within tolerance", is a separate gate and is undefined in the same way. Until the owner sets one, no rule can pass this gate. No rule has been run in a practice account yet |
| Practice account | A broker account that trades with pretend money at real prices. Also called paper trading |
| Fresh | Said of a held-back slice no rule has been run on. Once a rule has been run on it and the result seen, it is no longer fresh for that rule |
| First run, corrected run | Where a test was run twice because of a proved fault. Both are kept and both are reported. Both are measurements. Which is credited is the owner's to say. After the code audits (R1) research judged the rerun, on its own reading of the owner's rule (question 18c). After a fault in one rule's code (R2, replay 05) research reran before asking. Research now recommends that no pass from either pair of runs is credited (question 18b in `archive/decisions/morning_list_2026-11-25.md`). Fails stand |

## Evidence labels

| Label | Meaning |
|---|---|
| MEASURED | Independent data, official rule text, a published price page, or our own logged test |
| STATED | Claimed by a vendor, author or promoter and not independently verified |
| UNKNOWN | Could not be verified. A thing to test, not a fact |
| OWNER | In `archive/quality/`: the owner's own rule |
| TRANSLATED | In `archive/quality/`: a proposal that applies the owner's method to this project. Not a rule until he confirms it |
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
| v1, v2 | The first engine and the engine after the audit fixes. v2 results are the ones research reports. Whether their passes are credited is the owner's to say, and research recommends not (question 18b) | `research_rig/README.md` |

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

Some terms came from the historical build notes in `archive/quality/`. The builder and trader roles in force are defined in `AGENTS.md`.

| Term | Meaning |
|---|---|
| Kit | The set of files a builder model works from with no memory of any chat. `archive/quality/02_how_we_build.md` |
| Builder | The lead agent and its helpers. They build tools, run tests, set pretend-money limits and make day-to-day choices (`AGENTS.md`, "Who is who") |
| Trader | An AI agent or fixed rule trading pretend money on the practice desk or in the time machine under its own method and `AGENTS.md`, "How a trader behaves" |
| Partner | In the archived build method, the interactive mode that reviewed builds and wrote fix prompts. Today the builder is the owner's partner |
| Gate | A checkable line at the end of a build phase |
| Engine | Two meanings. In the owner's rerun rule and in `research_rig/`: the test code that simulates trades on past prices and works out the pass marks (`engine.py`, then `rig2.py`). It is not the code of any one rule, and it is not the definition of a pass mark. That meaning is research's reading and the owner has not confirmed it (question 18c). In the planned product: see the next row |
| Engine, service | In the planned product: the always-on program that reads prices, applies rules and risk limits, and places orders. It works with every model switched off |
| Escalation gate | In the old product plan, plain code that would decide when a finding was worth showing a stronger model |
| Research rig | `research_rig/`. The code that ran the replays. Not product code |
| Moonshot sleeve | A small, capped share of the account for high-risk ideas. Its size is an open owner number |
| Owner decision | Something the owner said, recorded with the date in `docs/DECISIONS.md`. Older records are in `archive/decisions/` |
| Trade intent, `TradeIntent` | A decision to buy or sell a stated amount of an asset. An AI trader expresses this decision in a pick, not a broker order (`AGENTS.md`, "How a trader behaves", item 1) |
| Pick | The trader's written decision to buy, sell or do nothing, with the reasons and sources. The form is in `practice/picks.py` |
| Practice desk | The pretend-money desk in `practice/` that trades on live prices through a practice account |
| Time machine | The replay system in `timemachine/`. Traders use pretend money on past days and cannot see beyond the current replay date |
| Tape | The time machine's recorded, dated market data and news. A replay only releases what the trader could see by the current date |
| Queue | The builder's work list in `docs/QUEUE.md`: what is running, what's next, and what finished |
| D1, D2, D3, D4 | Short labels the playbook pages use for four proposals in `archive/decisions/0001-starting-decisions.md`. That file says which row each one is |
| v1 | Two meanings. In the playbook and `archive/quality/`: the first version of the product, which is not built. In `research_rig/`: the first test engine, replaced by v2 |

## Other short names

| Term | Meaning |
|---|---|
| CSCV | The method behind the overfitting estimate: the history is cut into blocks and every half-and-half split is tried. Named in the Bailey paper above |
| CPCV | A related way to split history for testing, which leaves gaps between the parts so they do not leak into each other. Named in the playbook. Not used in any test here |
| DSR, PBO | Deflated Sharpe ratio, and the overfitting estimate. Both defined under "Measures" |
| Durbl, BusEq and the other industry names | The French library's short names for its twelve industry groups: NoDur consumer nondurables, Durbl consumer durables (cars, TVs, furniture, appliances), Manuf manufacturing, Enrgy oil, gas and coal, Chems chemicals, BusEq business equipment (computers, software, electronics), Telcm telephone and television, Utils utilities, Shops wholesale and retail, Hlth healthcare and drugs, Money finance, Other everything else. MEASURED from the library's [definitions file](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Siccodes12.zip) |
| Shadow, shadow mode | A model or rule runs and its output is logged, and nothing acts on it. Older playbook pages describe it as a build phase |
| Order path | The code that turns a trade decision into an order. On the practice desk and in the time machine an AI trader decides by writing a pick; a plain program checks and places the order (`AGENTS.md`, "What the order program always does") |
| Fill | The price and size at which an order was actually done. A replay has to assume one |
| Fixture | A tiny hand-worked case with a known right answer, used to check the engine before a test runs (`fixtures.py`, `fixtures2.py`) |
| Fingerprint | A SHA-256 hash of a file. Two files with the same fingerprint are the same, byte for byte. Stored in `research_rig/provenance.json` |
| Scope call | A choice about what the product is or is not. Two were made by research on 2026-11-24 and never put to the owner (questions 14 and 15) |
| Training cutoff | The last date covered by a model's training data. A replay counts only on days after its knowledge line (`AGENTS.md`, "Honest testing", item 4) |
| Knowledge line | Another name for training cutoff in this repo; the date after which an AI replay can count. The builder estimates it when the exact cutoff is not known |
| Dust | A leftover holding worth under one cent that cannot be sold. It stays on the books so the account check adds up |
| Effective spread | What a trade really cost against the middle price at that moment, as reported by venues. Often smaller than the quoted gap between bid and ask |
| SIP, IEX | Two kinds of US stock price feed. The SIP is the combined feed from every exchange. IEX is one exchange, a small share of trading, and is the feed on Alpaca's free plan |
| Rule 605 | An SEC rule that makes trading venues publish monthly figures on how well they filled orders. A source for real costs |
| Dead-coin problem | A price source that drops coins which stopped trading shows only the survivors, so a basket built from it looks better than it was |
| Resampled range (bootstrap) | A range for a figure, made by redrawing the history at random many times and measuring again each time |
| Derby | The owner's word: three directions for a screen over the same content, published so he can pick one or mix. From `archive/quality/01_the_bar.md` |
| G1 to G6, N1 to N7 | Rule names in the two draft plans, replays 06 and 07. Defined in those drafts. Not run |
