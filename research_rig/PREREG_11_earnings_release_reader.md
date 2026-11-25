# Pre-registration 11: an AI reads each earnings release and says buy or skip for the next open

Status: frozen 2026-11-25 17:56 UTC by the lead. Built 2026-11-25 by `build_prereg_11.py` from `events_11_summary.json`, `extraction_check_11.json` and the replay_11_* keys in `config/thresholds.yaml`. Do not edit by hand. Ledger rows 121 to 134 in `research_rig/TRIAL_LEDGER.md` were pushed in the same commit as this file, before any reader saw a release and before any return after any event was worked out. The code was audited twice by a second model before the freeze (the faults found were fixed, each with a test in `test_11.py`; one, about half-days and market holidays, is noted below and not changed). From here only faults in code may be fixed. Queue row 9b in `docs/QUEUE.md`.

## The claim

When a company files its quarterly results with the SEC, an AI that reads the press release can tell which stocks will do better after the next regular-session open. Only the move after that open can be traded by this desk, so only that move is judged. The jump between the filing and the open is not ours and is not counted.

## Why now: the readers cannot know the outcome

Every release used is filed on or after 2026-04-01. Each reader's knowledge line, quoted from `docs/research/31_model_knowledge_lines.md` (MEASURED on crypto month-end prices; columns: latest month it says it knows, last month it got right, replay months answered, replay months right, later hits by carrying forward):

- `claude_sonnet_5_5`: `| Claude Sonnet 5.5 | 2025-11 | 2025-11 | 0 of 5 | 0 of 5 | 1 |`
  Its own words: "Values for 2025-01 to 2025-06 are fairly solid to within a few percent; July to October 2025 are rougher recollections, and the 2025-11 figures are vague. I remember nothing reliable after November 2025, so everything later is null."
- `grok_4_7`: `| Grok 4.7 | 2025-01 | none | 0 of 5 | 0 of 5 | 0 |`
  Its own words: "I do not remember a month-end price for BTC, ETH, or SOL in any of these months, so every close is null. I only remember that bitcoin was around the $100,000 level after late 2024, and nothing reliable after early 2025."
- `kimi_k3`: `| Kimi K3 | 2025-07 | 2025-06 | 0 of 5 | 0 of 5 | 0 |`
  Its own words: "My memory is a rough approximation for early-to-mid 2025 (within a few thousand dollars on BTC, less certain on ETH and SOL), and it gets genuinely thin after about July 2025, so everything from 2025-08 onward is honestly unknown to me."
- `claude_opus_5_5`: `| Claude Opus 5.5 | 2026-01 | 2025-12 | 0 of 5 | 0 of 5 | 0 |`
  Its own words: "Fairly confident in early-to-mid 2025 month-ends (within a few percent); Oct-Dec 2025 are approximate, and I only have vague impressions of a further sell-off in January 2026 with no reliable month-end figures from 2026 onward."

All four lines are before 2026-04-01. The line was measured on prices, not company news. A model may still know company news from before its line; that was public before the filing, so it is fair.

## Stock lists (MEASURED, saved before any price was read)

- S&P 500 (500): List of S&P 500 companies, revision 1345606266, 2026-03-27 01:30 UTC. 500 companies after one row per CIK.
- S&P MidCap 400 (400): List of S&P 400 companies, revision 1346242889, 2026-03-30 19:25 UTC. 400 companies after one row per CIK.
- S&P SmallCap 600 (600): List of S&P 600 companies, revision 1346175333, 2026-03-30 10:21 UTC. 600 companies after one row per CIK.
- CIKs: 1,202 from the tables, 290 from the SEC's company_tickers.json saved 2026-11-25 (most 400 rows give a ticker, not a CIK), 8 by name with EDGAR's company search on 2026-11-25 because their tickers have left that file. Members with no CIK: 0. A CIK in two lists is kept in the first (500, 400, 600).
- Wikipedia is dated but anyone can edit it. S&P's own dated lists were not found. Companies that left an index between April and November stay in (no survivorship filter).

## Events (MEASURED by `fetch_11_edgar.py`, counted by `prep_11.py summary`)

Every 8-K or 8-K/A with item 2.02 from these companies, filing date 2026-04-01 to 2026-11-20, from `data.sec.gov/submissions`, with the SEC acceptance time to the second put in New York time. The press release is the exhibit typed EX-99.1, EX-99.01 or EX-99 on the filing's index page, else its first EX-99 of any number.

| List | Item 2.02 filings | Companies | 8-K/A | With an EX-99 | Text at least min_text_chars | Before open | During hours | After close |
|---|---|---|---|---|---|---|---|---|
| 500 | 1,511 | 496 | 5 | 1,487 | 1,484 | 807 | 32 | 672 |
| 400 | 1,178 | 395 | 7 | 1,170 | 1,168 | 509 | 27 | 642 |
| 600 | 1,757 | 584 | 6 | 1,742 | 1,741 | 681 | 55 | 1,021 |

Filters, fixed now (replay_11_events): 8-K only; exhibit text at least 1500 characters (shorter is usually a cover note); one event per company per 20 days, the first kept; a daily bar on the entry day. No filter on size, sector or the text's content.

Dropped: text short or no exhibit 52; second within min_days_between 83; no bar on entry day 8; amendment (8-K/A) 18.

| List | Used events | Companies | Design half | Held-back half |
|---|---|---|---|---|
| 500 | 1,454 | 496 | 767 | 687 |
| 400 | 1,141 | 394 | 559 | 582 |
| 600 | 1,690 | 582 | 813 | 877 |
| all | 4,285 | | 2,139 | 2,146 |

Split by date on all three lists pooled: the used events sorted by acceptance time, cut at the change of entry day nearest the middle by count, so that no entry day (and no open) is in both halves. The halves are therefore not exactly equal. The last design event was accepted 2026-07-30 09:22:24 New York time (entry 2026-07-30) and the first held-back event 2026-07-30 09:30:23 (entry 2026-07-31). By month: 2026-04 729, 2026-05 670, 2026-06 76, 2026-07 765, 2026-08 626, 2026-09 73, 2026-10 733, 2026-11 613.

## Prices (MEASURED, coverage only)

Daily open, close and volume from the workspace's built-in price history, 2026-03-02 to 2026-11-24, 187 trading days (the SPY daily file's days). Saved under `~/workspace/rig/data/stock_daily_11/`, never in the repo. Adjustment: see the next list.

- Splits (MEASURED by `split_check_11.py`): 10 list members that split between 2026-03-02 and 2026-11-24, from company filings and two split tables. BKNG 25-for-1 (2026-04-06), CVNA 5-for-1 (2026-05-08), KLAC 10-for-1 (2026-06-12), DD 1-for-3 (2026-06-24), HON 1-for-2 (2026-06-29), MLI 2-for-1 (2026-07-01), CRWD 4-for-1 (2026-07-02), MNST 2-for-1 (2026-08-11), APH 2-for-1 (2026-09-03), SNDK 8-for-1 (2026-11-20). In 10 of 10 our file shows no jump on the split day. In 9 of the 9 with an as-traded close before the split, our close times the ratio equals it within 0.2%. So the files are split-adjusted. Sources: [Mueller Industries 8-K exhibit](https://www.sec.gov/Archives/edgar/data/89439/000008943926000025/ex-99_16302026stocksplit.htm), [Honeywell press release](https://www.honeywell.com/us/en/news/press-releases/2026/06/honeywell-board-of-directors-sets-record-date-and-announces-expected-timing-for-spin-off-of-honeywell-aerospace-and-honeywell-reverse-stock-split), [Sandisk 8-K](https://www.stocktitan.net/sec-filings/SNDK/8-k-sandisk-corp-reports-material-event-8248455531a3.html), [StocksXray split table](https://www.stocksxray.com/stock-splits) and [Stock Titan split list](https://www.stocktitan.net/articles/stock-splits-2026-list-big-companies) (as-traded closes, STATED by those pages). No split fix is needed, so none is applied.
- Dividends: the same closes match the as-traded close divided by the ratio to the cent months after the split, for companies that pay dividends (BKNG, KLAC, DD, APH), so ordinary dividends do not look adjusted out. Ex-dividend dates were not checked: STATED, not MEASURED. A trade that holds over an ex-dividend day loses the dividend; on a 5-day hold that is small and the same for set-ups and yardsticks. A special dividend would show as a large overnight move (next list).
- Prices collected again for the held-back exits must be collected for every symbol at once, so all files share one adjustment date. A split between two collections would otherwise mix adjusted and unadjusted bars.
- 500: 494 of 500 companies have every day. Short: AVB (122 days, 2026-03-02 to 2026-08-24), CTRA (48 days, 2026-03-02 to 2026-05-07), EA (112 days, 2026-03-02 to 2026-08-10), HOLX (26 days, 2026-03-02 to 2026-04-07), KVUE (170 days, 2026-03-02 to 2026-10-30), WBD (151 days, 2026-03-02 to 2026-10-05).
- 400: 389 of 400 companies have every day. Short: BLD (86 days, 2026-03-02 to 2026-07-02), CFR (185 days, 2026-03-02 to 2026-11-24), GTLS (95 days, 2026-03-02 to 2026-07-16), IBOC (168 days, 2026-03-02 to 2026-11-16), JHG (86 days, 2026-03-02 to 2026-07-02), MASI (73 days, 2026-03-02 to 2026-06-12), NSA (98 days, 2026-03-02 to 2026-07-21), NWE (181 days, 2026-03-02 to 2026-11-16), TCBI (154 days, 2026-03-02 to 2026-10-08), TMHC (100 days, 2026-03-02 to 2026-07-23), WBS (120 days, 2026-03-02 to 2026-08-20).
- 600: 571 of 600 companies have every day. Short: ACA (164 days, 2026-03-02 to 2026-10-22), AL (27 days, 2026-03-02 to 2026-04-08), AMWD (62 days, 2026-03-02 to 2026-05-28), APLS (54 days, 2026-03-02 to 2026-05-15), ARI (184 days, 2026-03-02 to 2026-11-19), AVNS (101 days, 2026-03-02 to 2026-07-24), BLFS (152 days, 2026-03-02 to 2026-10-07), CPRX (98 days, 2026-03-02 to 2026-07-21), CSGS (54 days, 2026-03-02 to 2026-05-15), GDEN (49 days, 2026-03-02 to 2026-05-15), HLX (146 days, 2026-03-02 to 2026-09-28), ITGR (181 days, 2026-03-02 to 2026-11-16), KW (74 days, 2026-03-02 to 2026-06-15), LEG (125 days, 2026-03-02 to 2026-08-27), LXP (171 days, 2026-03-02 to 2026-11-03), MCW (59 days, 2026-03-02 to 2026-06-08), NVRI (127 days, 2026-05-27 to 2026-11-24), PCRX (182 days, 2026-03-02 to 2026-11-18), PRA (86 days, 2026-03-02 to 2026-07-02), QRVO (150 days, 2026-03-02 to 2026-10-02), RAMP (170 days, 2026-03-02 to 2026-10-30), SEE (28 days, 2026-03-02 to 2026-04-09), SEM (84 days, 2026-03-02 to 2026-06-30), SNCY (54 days, 2026-03-02 to 2026-05-15), STEL (84 days, 2026-03-02 to 2026-06-30), TPH (52 days, 2026-03-02 to 2026-05-13), TWO (122 days, 2026-03-02 to 2026-08-24), VRE (60 days, 2026-03-02 to 2026-05-26), WSR (92 days, 2026-03-02 to 2026-07-13).
- Used events whose stock's bars stop or start somewhere in 2026-03-02 to 2026-11-24: 56. Of those, the bars stop inside the event's own hold for H1 0, H5 1 (counted on dates only). A trade whose stock has no bar on the exit day sells at the last close in the file, and is flagged and counted. The scorer prints the result without these trades beside the judged one, not judged.
- Large overnight move inside the hold, fixed now (replay_11_overnight): a trade is flagged when a close-to-next-open ratio between two days of its hold (entry day to exit day) is below 0.7 or above 1.45. The judged result keeps every trade; the result without flagged trades is printed beside it, not judged, with the list of flagged trades. Measured on the files to 2026-11-24: 25 such ratios on any day in the used events' stocks; inside a used event's hold: H1 0, H5 0. Held-back H5 holds that run past the last price day and are not yet counted: 25. None of the large ratios falls on a split day from the list above. Their causes (earnings gaps before entry, special payouts, deals) were not looked up: UNKNOWN, and not needed while none is inside a hold.
- Price files under a new ticker for the same CIK (closes agree on every shared day, or the old ticker has no bars): BK to BNY, PSTG to P, ASGN to EFOR, ATGE to CVSA, AXL to DCH, EXPI to AGNT, FDP to DMC, IAC to PPLI, VSCO to VSXY, EQR to VMRK, PSKY to SKYD, SATS to ECHO. The rule and the two exceptions are written in `common_11.py`.
- No return after any event has been worked out. The only returns worked out are open-to-5th-close moves in windows that start and end in March 2026, to size the test.

## What a reader is shown

- The instruction in `reader_instruction_11.txt`, the same for every reader, word for word. Then one file per release: its event id (the first 12 characters of the SHA-256 of the accession number), the SHA-256 of the text below it, the acceptance time in New York time and the extracted release text. The header carries no ticker, list, price, chart, news, other filing or estimate. The release text names the company, and in 96.7% of texts the ticker (as a whole word in the first replay_11_readers.text_cap_chars characters; MEASURED by `prep_11.py summary`).
- Text cap: replay_11_readers.text_cap_chars = 20000 characters, cut at the last line break before it, with a note saying it was cut. Measured on the 4,285 used texts: median 31,324 characters (10th percentile 17,348, 90th 52,730); medians by list 500 33,494, 400 30,698, 600 29,758. The cap cuts 85.0% of texts. A line headed outlook or guidance was found in 2,747 texts; its median start is character 4,466 and its 90th percentile 11,185. In 2.0% of those it starts after the cap and is lost.
- Other caps considered, share of texts cut and share of guidance headings lost: 10000: 96.4% and 12.9%; 15000: 93.3% and 4.1%; 20000: 85.0% and 2.0%; 25000: 71.5% and 1.2%; 30000: 53.8% and 0.6%.
- What gets cut is the end of the text. The headline, the highlights, the chief executive's quote and, in most releases, the guidance come first. The cut part is the financial tables (statements, reconciliations, segment detail) and also non-GAAP definitions, the forward-looking statements notice and the company description; in a few texts it is part of the guidance. So "the tables at the end are what gets cut" is only about half true. In the extraction check below, table rows are 45.2% of the cut part on average and 23.3% of the kept part.
- Answer: one JSON line per release with event_id, input_sha256, score (a whole number from -2 to 2) and reason (one line, at most 200 characters, naming what in the release drove the score).
- Buy: a final score of 1 or 2. Skip: 0, -1 or -2. The desk cannot sell short, so -1 and -2 are only skips.

## How the readers run, and the gap

- The lead can run models only as helper agents, and helpers have tools. Each reader is one helper given one folder of at most replay_11_readers.batch_max = 20 releases and told, in `READER_BRIEF_11.md`, to read only that folder, write one answers file, and use nothing else.
- Gap: no tools is an instruction, not enforced. A helper could search the web for the stock's move or open another reader's folder, and the checker could not tell from the answers file. Lowered, not removed, by: no ticker in the header (the text itself usually names it, above), folders that hold only prompts, a fresh helper for each folder with no other context, the instruction to say so and score 0 if it remembers the move (the checker sets such an answer to 0, stores the flag and counts it in the results), and the lead looking at the helper's tool calls where the platform shows them.
- The model is not checked either: the folder names the reader and the lead spawns that model. The answers file does not prove which model wrote it.
- `prep_11.py design` writes every prompt once to `~/workspace/rig/data/edgar_11/prompts/` and copies it into one folder per reader per batch: `INSTRUCTION.txt`, `manifest.json` (reader, batch number b001, b002 and so on, the instruction's SHA-256, each event id and text hash; no phase) and `events/`. What each folder must hold is kept outside the reader's folders, in `reading/<phase>/<reader>.expected.json`. Batches are dealt from a seeded shuffle, so each mixes companies and dates, and never holds two releases from one company. Every reader gets the same batches, each in its own seeded order.
- `check_11_answers.py FOLDER` refuses a file with a wrong hash, a missing or unknown or repeated event, a score that is not a whole number from -2 to 2, a bad reason (empty, over 200 characters, or a line break), extra keys, a changed instruction, or a folder copy of a release that differs from the stored prompt. A refused file goes back to the same helper once. After that, `--second-try` sets each answer still missing or bad to 0 and flags it; an event answered twice is set to 0. A changed instruction or release copy is refused even then. A reason that says the reader remembers the move is set to 0, and `remembered` is stored and counted. The pattern is a backstop for the instruction, which already tells the reader to give 0, so both lines are printed: the judged one with these answers set to 0, and beside it, not judged, the same set-up with the scores as given, with the list of event ids that were set to 0. A match with a negation in the three words before it is skipped; a reason under 4 words is stored as `short_reason` and counted. `--collect PHASE` refuses unless every expected reader, folder and event is there (for the held-back `cascade`, the strong reader on exactly the disagreements and the audit), joins the checked folders into one file per reader and writes `answers_11_<phase>_hashes.json` (written for each phase; it does not exist yet).

## The design sample and the six set-ups

- A seeded draw (replay_11_statistics.seed = 11) of replay_11_design.sample_per_list = 150 design-half events from each list, 450 in all. Every one is read by all three small readers (`claude_sonnet_5_5`, `grok_4_7`, `kimi_k3`) and by the strong reader (`claude_opus_5_5`). That is 23 folders per reader, 92 helper runs.
- The set-ups, fixed now, in the order replay_11_design.setups lists them, cheapest first: each small reader alone (3); the strong reader alone; `middle`, the middle of the three small scores; `cascade`, the middle of the three where they agree and the strong reader's score where they disagree. They disagree when their buy-or-skip answers are not all the same, or their scores differ by 2 or more.
- Trials: 6 set-ups times 2 holds = 12, plus yardstick (c) at 2 holds = 14 ledger rows (replay_11_statistics.new_trials = 14).
- Choosing rule, fixed now: on the design sample, the set-up with the highest mean H5 return after costs minus yardstick (a), among those that buy between replay_11_design.buy_share_min = 20% and buy_share_max = 60% of events. Means are compared rounded to 0.01 percentage points; a tie goes to the set-up earlier in the list. If none qualifies, the held-back half is not read and the result is a fail. `score_11.py --design` writes the choice into `results_11_design.json` (written by that run; it does not exist yet).
- Only the chosen set-up reads the held-back half, once, all events. For `cascade` the strong reader reads the disagreements and a seeded replay_11_readers.audit_share = 10% of the agreed events (the audit is reported, not judged).
- Agreement, reported for the design sample and, where there is more than one reader, the held-back half: share of events where the three small readers agree on buy or skip, Fleiss' kappa on buy or skip, the rank correlation of scores for each pair of the four readers, the share sent to the strong reader, how often the strong reader agrees with the small readers' agreed answer, and each reader's buy share. Low agreement is a result, not a fault.

## Trades

- Entry: the open of the first regular session after the acceptance time. Before 09:30 on a trading day, that day's open; at or after 09:30, the next trading day's open. In practice a market-on-open order placed before the open, so the reader never sees the open.
- Exits (replay_11_statistics.holds): H1 sells at the close of trading day 1 counting the entry day as day 1, H5 sells at the close of trading day 5 counting the entry day as day 1. H5 is the main test.
- Cost per side by list, an assumption fixed now (replay_11_costs.bps_per_side): 500 5 bps, 400 10 bps, 600 20 bps. A buy fills at open times (1 + cost) and a sale at close times (1 - cost). Commission 0. Sensitivities at 0 times, 0.5 times, 2 times every list's cost are reported, not judged.
- A check on the assumption, read by this builder from another helper's file on the research machine (`~/workspace/rig/stock_spreads_measured.md`, Alpaca SIP quotes, June to November 2026, 56 large stocks and funds): the median half-spread in the first 30 minutes after the open is 2.422 bps and its 90th percentile 10.055 bps, from 3129 observations (MEASURED by that helper). So 5 bps for the 500 sits between the two. Nothing was measured for the 400 or the 600, and an opening auction can cost more than the quoted spread: UNKNOWN.
- The prices on file end on 2026-11-24. Held-back H5 trades entered after the fifth-last trading day have no exit yet, so prices are collected again before the held-back half is scored. `score_11.py` refuses if the SPY file does not reach the last exit day.
- Equal weight per trade; the result is the mean return per trade after costs. No account curve, because trades overlap.

## Yardsticks

- (a) Every release: buy every event in the same set (design sample or held-back half), each at its list's cost.
- (b) Random picks: replay_11_statistics.draws = 1000 draws, seeded, each picking without replacement as many events as the set-up bought, from the same set. Reported: the 95th percentile of the draws' means and the share of draws the set-up beat.
- (c) Opening jump, no AI: buy when the entry open is more than replay_11_gap.min_up_pct = 2.0% above the last close before the filing. It decides on the price it fills at, which the desk could not quite do, so it is a favourable yardstick.
- Reported, not judged: each mean minus SPY's move over the same open-to-close window, and each list alone.

## The pass mark (held-back half, all three lists pooled)

- Pass at a hold: the chosen set-up's buys have a higher mean return after costs than (a), and higher than the 95th percentile of (b), with at least replay_11_statistics.min_buys = 100 buys. Fewer is "too few to judge", not a pass.
- H5 is the main test. A pass at the other hold only is reported as a pass at the second exit and is not enough to start practice trading.
- Each list alone is reported and not judged.
- Only faults in code may be fixed after the design sample is seen. A change to the instruction, the models, the batch size, the cap, the buy threshold, the exits, the costs or the pass mark is a new trial with new ledger rows.
- `score_11.py --heldback` is run once, by the lead. It refuses unless the held-back answer hashes and `results_11_design.json` are in origin/main byte for byte. It refuses if `results_11_heldback.json` or its lock record `score_11_heldback.lock` exists locally or in origin/main; it writes the lock after its checks and before it reads a held-back price, so a deleted output does not let it run again. `--design` refuses if `results_11_design.json` exists locally or in origin/main. Both modes refuse unless this plan is `research_rig/PREREG_11_earnings_release_reader.md` and is in origin/main byte for byte, and the replay_11_* keys in `config/thresholds.yaml` equal those in origin/main; `--heldback` also needs them equal to the keys stored in `results_11_design.json`. The real run reads and writes `research_rig/` and refuses if EDGAR_11_DIR, STOCK_DAILY_11_DIR, SPY_DAILY_11_FILE or RESULTS_11_DIR is set; only the tests set them. Both modes refuse unless the hashes file lists exactly one collected answers file for each reader the set-up needs, and they score only those files. Each result file holds one SHA-256 over the names and bytes of the price files it read, SPY included.
- A pass means worth trying on the practice desk with pretend money. It does not mean it makes money.

## Size: can this tell skill from luck

MEASURED, open to 5th close, windows inside March 2026 (before the first event): 500 sd 4.32% from 8,928 windows, 400 sd 4.96% from 7,092 windows, 600 sd 5.53% from 10,476 windows. Weighted by the held-back counts, 5.01%. After earnings the spread is wider by an amount UNKNOWN; the second column assumes 1.5 times.

The edge over random picks that clears the 95th percentile of (b) 80% of the time, with N = 2,146 held-back events. Standard error sd x sqrt(1/b - 1/N), edge (1.645 + 0.842) x standard error:

| Buy share | Buys | Edge at the March sd | Edge at 1.5 x March sd |
|---|---|---|---|
| 20% | 429 | 0.54% | 0.81% |
| 40% | 858 | 0.33% | 0.49% |
| 60% | 1,288 | 0.22% | 0.33% |

To show a 0.5% edge 80% of the time when half the events are bought: about 622 held-back events at the March sd, 1,400 at 1.5 times. Events cluster in the same weeks and share the market's move, so the real sample behaves as fewer independent bets and these edges are a lower bound.

The design sample is smaller. With 450 events, a set-up's edge has a standard error several times larger than on the held-back half, so the choice among six set-ups is mostly noise unless their true edges differ by about 1% or more. That is a weak choice, not a biased one: the held-back half is read by one set-up only.

## Extraction check (MEASURED by `extract_check_11.py`; reading notes in `EXTRACTION_CHECK_11.md`)

- 20 texts, a seeded pick across the three lists, against each filing's raw exhibit. Number tokens kept: 100.0% on average, lowest 100.0%. Texts with images (charts, logos), which a reader never sees: 14. Cut by the cap: 18. Guidance heading found: 16, before the cap: 15.
- The first extractor split words wherever a style tag sat mid-word and broke table rows. It was replaced on 2026-11-25, before any reader saw a text (`fetch_11_edgar.py`, extractor version 2). The check then found footnote marks glued to numbers ("$0.81" with footnote 1 read "$0.811"). Versions 3 to 5, the same day and still before any reader saw a text, write such marks as "[1]". All texts were re-extracted from the saved raw exhibits. Images (charts, logos, letter-style panels) are still lost.

## How this can fool us

- The code takes the close as 16:00 New York time on every trading day and does not know the early closes. No early close falls inside the event window (2026-04-01 to 2026-11-20), so no event is mislabeled by this. A later test with other dates must fix it first.
- The open already prices the release. Most of the reaction is between the filing and the open, which is not counted. The test is whether anything is left.
- The release is not the whole story. Guidance is often given on the call, after the release, and the open already holds the call.
- Remembered context: the models know each company up to their line, including old guidance and consensus. That is public and fair, but stale by the later quarters. A model that remembers a 2026 event from before its line could get the direction from memory. The line was measured on crypto prices only.
- Readers with tools (above). A reader that looked up the move would look skilled. The checker cannot see it.
- Clustering: hundreds of events in the same few weeks. The random-pick yardstick draws from the same events, which helps, but the real sample is smaller than its count.
- The cap loses the end of most texts (tables, definitions, the safe-harbor notice, and in a few texts part of the guidance), and the extraction loses anything shown only as an image. Footnote marks are kept as "[1]", which a reader must not take as a number.
- Filing time is not release time. Many companies put the release on a newswire minutes before the 8-K is accepted. When the newswire is before 09:30 and the 8-K after it, entry is a day later than it could have been. This is counted by session and reported.
- Costs for the 400 and the 600 are assumptions, not measured.
- Choosing on the design sample is noisy (above). The 12 design trials are counted in the ledger all the same.
- In `cascade`, the strong reader sees mixed folders on the design sample but only disagreements and the audit on the held-back half. The context differs, which can change its scores.

## Order of work for the lead

1. Freeze: done, see the status line at the top.
2. `python3 prep_11.py design`, spawn one reader helper per folder with `READER_BRIEF_11.md`, check each folder, `python3 check_11_answers.py --collect design`.
3. Commit and push `answers_11_design_hashes.json`. Then `python3 score_11.py --design`. Commit and push `results_11_design.json`.
4. `python3 prep_11.py heldback 1`; spawn and check; for `cascade` only, `python3 prep_11.py heldback 2`, spawn and check; `python3 check_11_answers.py --collect heldback`. Commit and push `answers_11_heldback_hashes.json`.
5. Collect prices again to past the last exit day, for every symbol at once, and run `python3 split_check_11.py` again (add any split after 2026-11-24 to its list first). Then, once, `python3 score_11.py --heldback`.

## Files

- `fetch_11_edgar.py` collects the filings and texts; `common_11.py` holds paths, the calendar and the price-file map; `prep_11.py` filters, splits, samples and builds the folders; `reader_instruction_11.txt` and `READER_BRIEF_11.md` are what readers see; `check_11_answers.py` checks and collects answers; `score_11.py` scores; `test_11.py` tests them on made-up data; `extract_check_11.py` and `EXTRACTION_CHECK_11.md` are the extraction check; `split_check_11.py` is the split check; `events_11_summary.json`, `extraction_check_11.json` and `split_check_11.json` hold every count above.
