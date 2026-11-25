# 0005 - Overnight research run, 2026-11-25

Date: 2026-11-25 (UTC). The night of 2026-11-24 in Idaho.
Status: proposed by the research team. Nothing here is an owner decision.

What the owner said, 2026-11-24: "Feel free to continue doing your research, anything else that would benefit the project". Later the same night: "you free to do anything that will benefit the project and the overall goal of you being successful at making money day trading crypto and stocks. Free for you to look up to penny stocks and high-risk, high-return crypto as well".

What research did with that, and what it kept to: research only. No account was opened, no key was requested, no order was placed and no product code was written. A small research rig was built to test ideas on past prices. It is kept apart from the product in `research_rig/`. `AGENTS.md` was not changed.

## What was added

| Item | Where |
|---|---|
| The research rig: replay engine, engine checks, written test plans, trial ledger | `research_rig/` |
| Replay 01: slow trend rules on bitcoin and ether with real fees | `docs/research/12_replay_01_crypto_trend.md` |
| Pilot 02: six AI model runs making daily calls on past prices | `docs/research/14_ai_calls_pilot_02.md` |

## Numbers added to the config

Three house numbers were used as pass marks in replay 01. They were fixed in writing before the replay ran. They are now in `config/thresholds.yaml` with status `proposed`, so that documents can name them:

| Key | What it is |
|---|---|
| `replay_max_drop_ratio_vs_hold` | Pass mark 1: how large the rule's biggest drop may be, as a share of the biggest drop from holding |
| `replay_min_deflated_sharpe` | Pass mark 3: the smallest deflated Sharpe ratio that passes |
| `replay_min_shuffle_percentile` | Pass mark 5: the share of shuffled timings the rule must beat |

These are research's own choices, not published cutoffs. The owner can confirm, change or decline each one. If one changes, replay 01's pass table must be worked out again with `run_01b.py`.

## What the evidence now says, in short

The detail and every limit are in the two research files.

- Slow trend rules on bitcoin passed all five marks at Binance.US cost and, for three of nine rules, at Alpaca cost. The rule named in advance as the main one failed narrowly at Alpaca cost. Nothing passed at Kraken or Coinbase entry cost.
- No trend rule on ether passed at any venue.
- The rules cut the worst falls roughly in half and gave up much of the gain in strong years.
- Six AI model runs on 147 days of prices all behaved like trend followers and were not distinguishable from a four-line trend rule. The pilot was declared inconclusive before it ran.

## Proposals for the owner, one at a time

None is approved. Each is stated in the research file it comes from.

| # | Proposal | From |
|---|---|---|
| 1 | Carry bitcoin rules P2, S50 and D20 into practice trading as candidates, with P1 alongside and labelled as failed at Alpaca cost | research 12 |
| 2 | Run ether in practice for observation only, labelled as failed | research 12 |
| 3 | Keep the three new pass marks as they are | this note |
| 4 | Keep the one-day-at-a-time harness as the way to test AI calls, and run it forward in the practice account only if he wants that question answered | research 14 |
