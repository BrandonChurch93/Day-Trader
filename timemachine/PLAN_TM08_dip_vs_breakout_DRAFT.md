# Time machine plan 08, draft: dip entries against breakout entries

Draft written 2026-11-26 12:23 UTC by a helper (decision autopsy analyst) for the lead agent, for queue row 30. No session has been made, no tape has been recorded for it, and no price or result for any month it names has been read. Pretend money. This draft is not a registration: it has no ledger row, and the queue, status and config pages are unchanged.

Recommendation, stated up front: close row 30 on count and power, before any session. The reasons are in "Months", "Power" and "Recommendation" below.

## What is asked

Queue row 30 asks whether the AI crypto trader does better when the desk lets it buy only near a floor after a week-long fall than when the desk lets it buy only on a break upward. It is the same card twice with one line changed, on months no model has traded, each card with random twins.

Where the idea comes from (MEASURED, [doc 59](../docs/research/59_why_the_ai_traders_lost.md), TM01 and TM02, 355 round trips):

- Round trips whose first buy was at "a price floor" made +$75.62 on 35 trips (48.6% won). They were the only entry group in the black.
- "Chasing a rise" made -$117.47 on 101 trips.
- Against that: random twins that bought a random coin at the same moments as the floor buys did better than the models did, +3.69% against +3.12% after 120 hours (35 paired). So most of the floor buys' gain came from when they were made, not which coin was picked.
- "Bounce after a fall" (75 trips, -$234.17) is also a buy after a fall, and it lost.
- The groups were named after reading these same trades, so the +$75.62 is a figure that suggested the idea. It is not a test of it.

## The two cards, word for word

They are to be copied byte for byte into `practice/traders/` at registration. They are not in the repo as cards yet. They are the TM01 card `practice/traders/B01_crypto_swing_price_only.md` with the header, the status line and fixed line 7 changed. Everything else is unchanged so that only the entry rule differs.

Card 1, `practice/traders/B03_crypto_dip_entry.md`:

```text
# B03 crypto_dip_entry

Status: draft for plan TM08, 2026-11-26. Untested. Market: the eight crypto pairs on the recorded tape, against USD. Holding time: hours to days. Price only, no news.

## What it tries to do

It lets a model trade crypto swings from prices alone, with its own judgment, inside a few fixed lines. One line differs from card B04: this card may only buy a coin that has fallen for a week and sits near its floor.

## What it looks at each time it wakes

- The packet: time, its cash and holdings, the feed of prices for the eight pairs, and for each pair whether the desk allows a buy now and why.
- Lookups of daily and minute bars for any of the eight pairs, within the lookup limit.
- Nothing else. No web, no news, no memory of what happened after the packet date.

## How it decides

- Its own judgment. It writes its reasoning in the pick's thesis in plain words, and one reason per action.
- It may hold cash. Doing nothing is a valid answer.

## Fixed lines

1. Only the eight pairs on the tape: BTC/USD, ETH/USD, SOL/USD, XRP/USD, DOGE/USD, AVAX/USD, LINK/USD, LTC/USD.
2. At most three holdings at once.
3. One buy is at most 40% of the starting budget.
4. Every buy carries a stop price in the pick's exits. A target price and an exit-by time are optional.
5. Long only. No borrowing.
6. It counts the cost before it trades: the fee is `practice_crypto_fee_bps_added` per side and the spread assumed is `tm_crypto_half_spread_bps` per side. A trade that needs a move smaller than twice that to pay off is not worth making.
7. Dip entries only. It may buy a coin, or add to one, only when the packet shows the dip gate open for that coin: the coin's last hourly close is at least 5% below its hourly close 7 days earlier, and no more than 3% above its lowest hourly low of the last 14 days. The desk refuses any other buy. Sells and exits are never limited.

## When it wakes

- At the hours in `tm_crypto_wake_hours_utc`. Exits are checked by the desk between wakes.

## How it is judged

- Written in `timemachine/PLAN_TM08_dip_vs_breakout_DRAFT.md` before any session ran.
```

Card 2, `practice/traders/B04_crypto_breakout_entry.md`. Every line is as in card 1 except these three:

```text
# B04 crypto_breakout_entry
```

```text
It lets a model trade crypto swings from prices alone, with its own judgment, inside a few fixed lines. One line differs from card B03: this card may only buy a coin that has broken upward through its high of the week before.
```

```text
7. Breakout entries only. It may buy a coin, or add to one, only when the packet shows the breakout gate open for that coin: the coin's last hourly close is above the highest hourly high of the 7 days that ended 24 hours before the wake. The desk refuses any other buy. Sells and exits are never limited.
```

Full text of card 2, for the record:

```text
# B04 crypto_breakout_entry

Status: draft for plan TM08, 2026-11-26. Untested. Market: the eight crypto pairs on the recorded tape, against USD. Holding time: hours to days. Price only, no news.

## What it tries to do

It lets a model trade crypto swings from prices alone, with its own judgment, inside a few fixed lines. One line differs from card B03: this card may only buy a coin that has broken upward through its high of the week before.

## What it looks at each time it wakes

- The packet: time, its cash and holdings, the feed of prices for the eight pairs, and for each pair whether the desk allows a buy now and why.
- Lookups of daily and minute bars for any of the eight pairs, within the lookup limit.
- Nothing else. No web, no news, no memory of what happened after the packet date.

## How it decides

- Its own judgment. It writes its reasoning in the pick's thesis in plain words, and one reason per action.
- It may hold cash. Doing nothing is a valid answer.

## Fixed lines

1. Only the eight pairs on the tape: BTC/USD, ETH/USD, SOL/USD, XRP/USD, DOGE/USD, AVAX/USD, LINK/USD, LTC/USD.
2. At most three holdings at once.
3. One buy is at most 40% of the starting budget.
4. Every buy carries a stop price in the pick's exits. A target price and an exit-by time are optional.
5. Long only. No borrowing.
6. It counts the cost before it trades: the fee is `practice_crypto_fee_bps_added` per side and the spread assumed is `tm_crypto_half_spread_bps` per side. A trade that needs a move smaller than twice that to pay off is not worth making.
7. Breakout entries only. It may buy a coin, or add to one, only when the packet shows the breakout gate open for that coin: the coin's last hourly close is above the highest hourly high of the 7 days that ended 24 hours before the wake. The desk refuses any other buy. Sells and exits are never limited.

## When it wakes

- At the hours in `tm_crypto_wake_hours_utc`. Exits are checked by the desk between wakes.

## How it is judged

- Written in `timemachine/PLAN_TM08_dip_vs_breakout_DRAFT.md` before any session ran.
```

STATED: the numbers in line 7 (5% over 7 days, 3% above the 14-day low, the 7-day high ending 24 hours back) were chosen for this draft without looking at any price. They are not fitted. They would go in a `tm08_plan` config block at registration. No such block is added now.

## How the desk, not the model, enforces the gate

Engine: the TM01 pick engine (`timemachine/session.py`, `simbroker.py`, `simdata.py`, the practice desk code unchanged), not the TM07 desk. The TM07 desk (`TM07_REGISTRATION.md`, engine `058a543`) trades a long-short weight vector on five coins a week and has no separate buy entry to gate. The doc-59 finding came from the pick engine, so the test stays on it. Nothing in the TM07 engine or its pinned files is changed.

The gate is plain code on the desk side, a new module (proposed `timemachine/entry_gate_tm08.py`, not written in this draft). At each wake t it does the following:

- It builds hourly bars for each of the eight pairs from the tape's one-minute rows. It uses only buckets that ended by t, through the same `simdata` path that serves the packet and the lookups. The engine already builds hour bars this way and never includes a bucket still open.
- Dip gate for a coin: (a) its last completed hourly close is at most 0.95 times the hourly close 168 hours earlier, and (b) that close is at most 1.03 times the lowest hourly low among the last 336 completed hourly bars.
- Breakout gate for a coin: its last completed hourly close is above the highest hourly high among the 168 completed hourly bars that ended between 192 and 24 hours before t.
- Coverage: if fewer than 90% of the hourly bars a gate needs exist (a bucket with no minute row counts as missing), that gate is closed for that coin at that wake.
- The packet carries, for every pair, `buy_allowed` (true or false) and the figures behind it (the 7-day change, the distance from the 14-day low, the prior-week high). So the model sees exactly what the desk decided, and from the same rows it could look up itself.
- When a pick is checked, a buy action on a coin whose gate is closed refuses the whole pick, with the reason "entry gate closed". This is like every other refusal in `TRADER_BRIEF.md`: nothing in the pick is traded, and the model may send a fixed pick. A buy of a coin already held is a buy and is gated the same way. Sells, stops, targets and exit-by times are not gated.
- Every gate decision is written to the session record (wake, coin, open or closed, figures), so the scorer can recount it from the tape.

Tests to write before registration, on a made-up tape, in the style of `test_sim.py`:

- The gate never changes when tape rows after t are edited (no look-ahead).
- Bucket edges: a bucket ending exactly at t counts, and one ending after t does not.
- The 90% coverage rule.
- Boundary values: exactly 0.95 and exactly 1.03 open the dip gate, and a close equal to the prior high does not open the breakout gate.
- A gated buy is refused whole while a sell in the same session goes through.
- The recount from the session record equals the live decisions.

## Months

MEASURED from `timemachine/SESSIONS.jsonl` (1,503 session lines and one void note) on 2026-11-26 at about 12:20 UTC. I counted months only and read no price or result for them.

- The crypto minute tape covers 2026-01-01 to 2026-11-24 (STATED in `timemachine/README.md`). That is 11 calendar months, the last one partial.
- Months in which at least one AI model has a crypto session: 2026-04 to 2026-11, 8 months (TM01, TM02, TM03 and TM06 together). Every one of the eight has sessions from all seven models.
- Recorded months that no model has traded: 3 (2026-01, 2026-02, 2026-03).
- Of those 3, months after every model's knowledge line: 0. In `timemachine/knowledge_lines.json`, Gemini Neon gives 2026-03 as its latest month and its last hit is 2026-02, and Claude Fable 5.2 gives 2026-02. The maker's stated reliable cutoff for Claude Fable 5.2, Claude Opus 5.5 and GPT-6.2 Sol is June 2026 (`docs/research/11_ai_trader_experiment_design.md`, as quoted in the TM06 plan).
- The TM07 registered weeks (2026-05-11 and 2026-07-06 to 2026-11-16) fall inside months already traded, so they change none of these counts.

So the count of usable months today is 0. The first one that could count is December 2026, after it ends and is recorded to a new TM08 store (no earlier than 2027-01-01). Six usable months would be December 2026 to May 2027, complete no earlier than 2027-06-01.

## Models and runs

- Six models, the TM01 set: `claude_opus_5_5`, `gpt_6_2_sol`, `gemini_neon`, `claude_sonnet_5_5`, `kimi_k3`, `grok_4_7`. `claude_fable_5_2` may be run as a seventh, shown-only arm. It never enters the judged figure.
- Each model runs each card twice in each month: 2 cards × 2 runs × 6 models = 24 sessions a month. Each session is one calendar month with a fresh `tm_account_start_usd` ($1,000) and 2 wakes a day (about 62 answers). Six months is 144 sessions and about 8,900 answers.
- The brief is `timemachine/TRADER_BRIEF.md` unchanged. There is one hand-off per month at day 15, as in TM06, with the same split for every session.

## Twins

For each AI session there are two sets of 20 twins. They are run with the existing twin runner (`run_code_trader.py twin`), extended so that it can draw only from coins whose gate was open. Seeds 1 to 20.

- Gate twins. At each wake where the AI bought, the twin buys a coin drawn at random from the coins whose gate was open at that wake. It uses the same dollars, the same stop and target distances and the same exit-by time. If only the coin the AI bought was open, the twin buys that coin, and that wake is counted as "no choice". This keeps the gate and the timing and breaks only the model's choice of coin.
- Free twins. The same, but drawn from all eight coins, as in TM01. This keeps the timing and drops the gate.
- Shown only, a gate rule with no model. Buy every coin at every wake where its gate opens, up to the card's three holdings and 40% caps, with a fixed stop 3.5% below and a target 6.5% above. Those are the medians in doc 59. Run once per card per month.

The twins are shown only. They are not part of the judged mark.

## The judged comparison and its pass mark

One comparison: dip card minus breakout card, net monthly gain in percent of the starting account, at the main costs.

- Cell: for one model, one run and one month, the B03 gain minus the B04 gain. Run 1 is paired with run 1 and run 2 with run 2.
- Month figure: the mean of the 12 cells of that month (6 models × 2 runs). The month is the unit, because all models trade the same month and share its moves.
- Pass, fixed now for a six-month design: over the 6 month figures, a one-sided t (mean over its standard error, ddof 1) of at least 2.57, and a mean above zero after dropping the best month. Both must hold.
- A missing or voided session leaves its month incomplete, and an incomplete month means the comparison cannot pass. Months are never replaced.
- MEASURED zero-edge pass rate of this mark, on made-up data (`timemachine/POWER_TM08.json`): 2.48% under normal noise, 2.49% with twice the shared month noise, 2.25% under t4 noise and about 0.8% under resampled noise. The cutoff of 2.57 is the smallest on a 0.01 grid that keeps every one of those at or under 2.5%.

Why this replaces the queue row's mark. The row proposed "the dip card above the breakout card in at least 5 of 6 models and above the 75th percentile of its twins in at least 4". Its first half alone passes about 27.7% of the time with no edge in the same made-up world (6 months, 2 runs, normal noise), because the six models share each month's moves. Its twin half was not modelled. [Doc 140](../docs/research/140_false_pass_audit.md) found the same looseness in the TM01 to TM06 marks (any one of six models above its 80th or 90th percentile twins), with a no-edge rate up to 73.79%.

## Power

MEASURED on made-up data by `timemachine/power_tm08.py` (sha256 3f7324ed7587e001f7838d3545727f75949e2539a628003f383a677318105c62). The saved output is `timemachine/POWER_TM08.json` (sha256 e4038f72c929b0311448fe1efc9c086d8d47bbb81ac9646cb766021eab806b3a). It used 20,000 simulated sets per cell, seed 8008, and took 24 seconds at nice 10. It reads no market data.

Noise (MEASURED from the repo's already scored `results_tm01.json` and `results_tm02.json`): the gain of the same model on two cards in the same month (TM02 minus TM01), over 6 models and 5 months (2026-07 to 2026-11).

- The part shared by all models in a month has a standard deviation of 1.61% of the account.
- The rest has 2.42% per cell.
- STATED: this is a proxy. B03 and B04 differ more from each other than B01 and B02 do. The dip gate opens in falling markets and the breakout gate in rising ones, so the shared month part is likely larger for TM08. That is why the twice-shared-noise row is there.

Effect sizes:

- Doc 59 gives floor trips +$2.16 each and breakout trips -$1.16 each, about $3.32 a trip on a $1,000 account. Models made about 6.2 buys a session-month (MEASURED, same files). If every trip of the dip card earned that gap, the edge would be about 2% of the account a month.
- That 2% is the ceiling. The groups were named after the trades were seen, and the same-moment twins did as well as the models on floor buys. The gate will also cut the number of trades.
- STATED, the defensible central figure is 1% a month, with 0.5% as the low case.

Chance to pass the judged mark (MEASURED, 2 runs a card), in percent:

| Months | Noise | Edge 0 | 0.5% a month | 1% a month | 2% a month |
|---:|---|---:|---:|---:|---:|
| 6 | normal | 2.48 | 8.24 | 20.77 | 61.41 |
| 6 | shared month noise × 2 | 2.49 | 5.06 | 8.89 | 22.59 |
| 6 | t4 | 2.25 | 9.42 | 24.62 | 68.03 |
| 6 | resampled | 0.8 | 2.94 | 11.58 | 65.01 |
| 12 | normal | 2.42 | 13.86 | 43.15 | 94.62 |
| 12 | shared month noise × 2 | 2.50 | 7.07 | 15.83 | 48.32 |
| 3 | normal | 2.49 | 4.92 | 8.81 | 21.62 |

More points from the same file:

- More runs barely help. At 6 months and 1% a month under normal noise, the chance is 18.85% with 1 run, 20.77% with 2 and 20.42% with 3. The shared month noise does not shrink as runs are added.
- Shown only: if each week were an independent draw (26 weeks, cutoff 2.09), the 1% chance would be 25.84%. Weeks inside a month are not independent in a trending market, so this is a ceiling.
- In plain words: at the defensible 1% a month, six months pass 9% to 25% of the time and twelve months 16% to 50%. A pass is more likely than not only near the 2% ceiling, and only under normal noise.

## Costs

- Main line: the pick-engine costs as in TM01. The fee is `practice_crypto_fee_bps_added` (25 bp) per side and the half spread `tm_crypto_half_spread_bps` (10 bp) per side, so 35 bp a side and 70 bp a round trip. Fills are at the open of the next recorded minute, and there is no volume cap.
- Shown only: the same picks re-booked at a 12 bp fee (the TM06 perp main line) plus the same spread.
- Doc 59 found that costs were 87% of the TM01 and TM02 net loss. A gate that cuts trades also cuts costs, which favours whichever card trades less. The trade counts are shown next to the result.

## Shown only, cannot count

- Each card against its gate twins and its free twins: the percentile and the median gap, for each model and pooled.
- The gate rule with no model, for each card.
- Per model and per run: the dip minus breakout gain, buys, round trips, win share, time in cash, refused picks and gate-open coin-wakes per month.
- The judged figure without the best month, by month, and at the 12 bp fee.
- The Claude Fable 5.2 arm, if run.

## What would make us stop early

None of these reads a gain or a loss.

- Machinery. The gate tests fail, a recount of gate decisions differs from the live record, a look-ahead check fails, or the books differ from the broker record by more than a cent.
- Too few chances. In the first month, either gate is open on fewer than 20 of the 496 coin-wakes (8 coins × 62 wakes). Or the dip card fills fewer than 2 buys in at least 4 of the 6 models (run-averaged). Either way, stop and close as untestable on these settings. The settings are not loosened after this has been seen.
- Integrity. More than 2 sessions in a month are voided (a web or price lookup, or a reply to a wake not asked for). A voided session makes its month incomplete in any case.
- Host. TM07 needs the machine, free disk falls under 2 GiB, or a TM07 path or port would have to be touched.

## Machine load next to TM07

MEASURED on 2026-11-26 at about 12:21 UTC: 4 cores, 5.3 GiB free disk on `/`, about 5 GiB of memory available. Listening ports: 7523, 8786, 8787, 8791, 8811, 8812, 8872. The TM07 ports 8784 and 8785 must not be touched whether or not they are up.

- No TM07 path is read. The old tape (`rig/tm_store/tape.sqlite`) is now a symlink to a copy behind `tm07desk` (STATED in `TM07_REGISTRATION.md`), and `rig/tm_runs` is not on its old path (MEASURED by `ls`). TM08 cannot and does not use either.
- TM08 uses a new store and runs folder, `rig/tm08_store` and `rig/tm08_runs`, set through `TM_STORE` and `TM_RUNS`. The store holds only the new months, recorded by `record.py crypto` after each month ends.
- Disk per month (tape plus 24 session folders): UNKNOWN, because the old folders cannot be measured now. Cap: 1 GiB for all of TM08, checked with `du` after each month. Stop if free disk is under 2 GiB.
- CPU: one desk server at `nice -n 10`, on a port checked free at launch, outside 8784 and 8785 and the ports listed above (for example 8796). There are at most 2 sessions at a time while TM07 runs. The model calls run at the provider, so the local load is the server and curl.
- Twins: 144 sessions × 40 twins = 5,760 twin runs. At the 43 seconds a twin that TM01 STATED, that is about 69 hours in one process at nice 10, never at the same time as a TM07 week. Memory under 1.5 GiB.

## Recommendation

Close queue row 30 on count and power, before any session. There are three reasons:

1. Count: 0 recorded months today are both untraded and after every model's knowledge line. Six such months do not exist before 2027-06-01.
2. Power: at the defensible edge of 1% of the account a month, the six-month design passes 9% to 25% of the time (MEASURED, made-up data). That is under the 33% floor. Doubling the months to twelve gives 16% to 50%, and stays under the floor when the shared month noise is doubled, which is the likely case for two gates that open in opposite markets. Only the in-sample 2% ceiling reaches more than half, and only under normal noise.
3. The signal is weak before power. The same-moment twins matched the models' floor buys in doc 59, so what the floor buys showed was mostly timing, which the gate rule with no model can test more cheaply.

A cheaper way to ask the same thing: run the two gate rules with no model as a fixed-rule replay in `research_rig/` on long coin history the rig already holds, such as the Binance archives behind Replay 22, with a power screen first under doc 117. That needs no new months and no model sessions.

UNKNOWN: whether the gate figures chosen here open often enough on new months. That would only be learned by recording them.
