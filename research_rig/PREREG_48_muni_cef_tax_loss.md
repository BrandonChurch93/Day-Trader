# Plan 48: year-end tax-loss selling and the January rebound in municipal closed-end funds

Status DRAFT.

Queue 86, ledger 182. One window, one rule, ten yearly turns. All numeric controls are in `replay_48_plan` in `config/thresholds.yaml`. Validation is not permission to score; only the lead agent may authorize and run the score. No price, bar or quote has been read for this plan.

## What this tests

STATED. [Starks, Yong and Zheng, Journal of Finance 61(6), 2006](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2006.01011.x) ([PDF](https://repec.udesa.edu.ar/pub/Finanzas/Journals/Journal%20of%20Finance/61/6/23646357.pdf)) study 168 municipal bond closed-end funds from 1990 to 2000. Average January return was 2.21% against -0.19% in the other eleven months (p. 3052). Funds with larger earlier-year losses had larger January returns, measured against February to October returns (pp. 3056 to 3061), and the effect shows in the first five trading days of January (p. 3056). Small-trade buy-sell ratios averaged 0.85 just before year-end and 1.37 just after (p. 3062).

STATED. [Carrion and Zhang, Journal of Financial Research 47(4), 2024](https://onlinelibrary.wiley.com/doi/10.1111/jfir.12384) ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3907044), [working paper PDF](https://bondcasebriefs.com/wp-content/uploads/2021/08/SSRN-id3907044.pdf)) cover 1990 to 2019 with 512 closed-end funds and 93 ETFs. For closed-end funds in 2007 to 2019 they report a January mean of 3.32% against -0.27% in other months. They find the December dummy insignificant (p. 12), selling no longer concentrated in the fourth quarter (p. 17), and the five-day volume link absent in 2007 to 2019 (p. 13). Their year-to-date loss is measured to the last November trading day (p. 10).

This plan takes the published direction (prior-year losers rebound in January) and tests a small whole-share version of it. It is not a replication of either paper's regressions. Turns 2016 to 2019 overlap the Carrion and Zhang sample; turns 2020 to 2025 do not overlap either paper.

## Window and reasons

Decided by the lead before any price was read.

- Ranking: price return from the first January NYSE session close of year Y to the formation close. Ranking uses price, not total return, because tax-loss selling responds to the holder's price loss.
- Formation: the second-to-last NYSE session close of December. It is as late as possible to catch the selling Starks, Yong and Zheng find just before year-end, while leaving one session to trade.
- Entry: the last December session close. This is a close-to-close proxy for buying into the end of the selling pressure.
- Judged exit: the last January session close of Y+1. Both papers report a full-January effect, and Carrion and Zhang find the short-window volume link gone in recent years, so a full month is the less fragile choice.
- Shown only: an exit at the 5th January session close (Starks, Yong and Zheng p. 3056 five-day window). It cannot replace the judged exit.

MEASURED from `research_rig/calendar_25.json` by the tests: the first turn anchors at 2016-01-04, forms 2016-12-29, enters 2016-12-30 and exits 2017-01-31; the last turn forms 2025-12-30, enters 2025-12-31, exits 2026-01-30 and shows the 5th session exit on 2026-01-08.

## Universe

- Each turn Y uses the muni closed-end funds on the [SEC closed-end fund roster](https://www.sec.gov/data-research/sec-markets-data/closed-end-fund-information) for year Y, exchange-listed, mapped to tickers as of that year. No fund is chosen with later knowledge. The point-in-time roster is built by /root/idea_scout at /home/user/workspace/rig/inventories/row86_muni_cef_roster.csv and enters the packet as `roster.csv` with at least columns `turn_year` and `ticker`. MEASURED in queue row 86: 130 muni or tax-free registrants on the 2026 roster.
- Eligible in a turn: a raw SIP daily bar on every session from the first January session through entry, and at least one whole share affordable from a $100 sleeve at the judged entry cost.
- Bars after entry may stop (merger, liquidation, delisting). A held fund with no bar at the exit is valued at its last close at or before the exit, charged max(entry half-spread, 50 bp proxy) plus 5 bp, and counted. It is not dropped.
- The benchmark is MUB. It must have every bar through the exit or validation refuses.

## Rule and sizing

- At the formation close, rank eligible funds by price return, lowest first. Ties go to the ticker in alphabetical order.
- Buy the worst five: $100 each, largest whole-share count that fits after the entry cost, at the entry close. Leftover cash is idle with no yield. Zero commission.
- Sell at the judged exit close less the exit cost.
- Distributions are credited per share held when the ex-date is after entry and on or before the exit (or the last held close for a fund that stops). Cash is not reinvested. Sources are dated issuer or exchange records, one HTTPS source per fund per turn.
- The yearly portfolio return is net dollars over $500.
- MUB is one $500 whole-share sleeve on the same clock, cost rule and distribution rule.
- The roster comparison is the mean of $100 sleeves over all eligible funds in that turn (equal weight), with the same rules.

## Cost

STATED, plan 36 convention. Per fund, per clock (entry, exit, shown exit): the duration-weighted median relative spread of uncrossed SIP quotes over the five minutes ending one minute before the close (15:54:00 to 15:59:00 New York time), each quote valid 60 seconds, at least 180 seconds of valid coverage. Quotes from 15:53:00 are accepted so a quote alive at 15:54:00 counts. The charge per side is half that spread plus 5 bp. The exit side uses the larger of the entry and exit half-spreads. If coverage is short, a 50 bp half-spread proxy is used for that side and counted in the results.

Shown only: the same turns at zero cost (same share counts).

## Judged marks

All seven must pass at judged cost over the ten turns December 2016 to January 2026. Zero is not positive.

| Mark | Rule |
|---|---|
| Turns | all ten turns scored |
| Net mean | yearly portfolio mean above zero |
| Positive years | at least 8 of 10 years above zero |
| Against MUB, mean | mean of portfolio minus MUB above zero |
| Against MUB, years | at least 7 of 10 years ahead of MUB |
| Without best year | mean above zero after removing the single best year |
| Loser effect | mean of portfolio minus roster equal weight above zero |

Shown only: the 5th-session exit table, the zero-cost table, per-year counts of roster, eligible, held funds with a missing exit and proxied cost sides. None can replace a failed mark.

## What ten turns can and cannot show

MEASURED on synthetic data by `research_rig/score_48.py --calibrate`, saved in `research_rig/CALIBRATION_48.json` (10,000 trials, seed 48001). The yearly spreads behind it are STATED assumptions, not estimates from market data: MUB 1.5% sd, roster beta 1.5 to MUB plus 3% residual sd, worst five 3% residual sd around the roster.

| Synthetic world | Pass rate |
|---|---|
| Zero edge (no roster premium, no loser excess) | 0.0439 |
| Roster premium of 2% a year, no loser excess (beta only) | 0.2065 |
| Premium plus loser excess of 1% a year | 0.4514 |
| Premium plus loser excess of 2% a year | 0.6614 |
| Premium plus loser excess of 3% a year | 0.8201 |

- The zero-edge false-pass rate is at or below the 0.10 ceiling.
- In the beta-only world the loser mark is close to a coin flip, so about one in five such worlds passes. A pass therefore cannot by itself separate a loser effect from a year-end rally across all muni funds.
- A real loser excess of 1% a year fails more often than it passes. A fail is weak evidence against a small effect.
- Ten turns span one rate cycle. Years are not independent draws of tax conditions, and the same funds may be picked in several years.
- The test cannot say who sold or why; it does not observe tax lots or trade flow.
- Closing prints are a fill proxy. A $100 order in a thin fund may not get the close.

## Packet and custody

The custodian stages, only after the lead approves the freeze, an owner-only directory /home/user/workspace/rig/data/plan48_inputs (mode 0700) with mode 0600 files and nothing else:

- `manifest.json`: exact keys `schema` (1), `mode` (`plan48_raw_sip_v1`), `feed` (`sip`), `adjustment` (`raw`), `first_turn`, `last_turn`, `collected_utc` (UTC Z, after the last exit), `files` (SHA-256 of every other file).
- `roster.csv`: the point-in-time roster.
- `bars_Y.json` for each turn: `turn`, `symbols` (every roster ticker for that turn) and `benchmark`, each a list of raw SIP daily bars `t`, `o`, `h`, `l`, `c`, `v`, with `t` at midnight New York, sessions from the first January session of Y to the last January session of Y+1.
- `quotes_Y.json` for each turn: `turn`, `sessions` (entry, exit, shown exit dates), and per symbol and for the benchmark the SIP quotes `t`, `bp`, `ap` from 15:53:00 to before 15:59:00 New York time on each of the three sessions.
- `distributions.json`: `schema` 1 and per turn per symbol a `source` URL and `cash` rows `id`, `ex_date`, `amount` with ex-dates after entry and on or before the exit.

JSON numbers are read as exact decimals. Gaps before entry make a fund ineligible; malformed rows, extra files or a wrong hash refuse the whole packet. The custodian and an independent reviewer check distribution coverage before approval. No prices, quotes or distribution amounts go in the repository.

## Gate

No return, ranking or payout before the lock. `research_rig/score_48.py --validate-inputs` checks shape, clocks, coverage and hashes and prints counts only. It needs a clean checkout of an approval commit with one parent that descends from the freeze and adds only `research_rig/APPROVAL_48.md`, one line:

    Approved by the lead: plan 48, validation and one scored run, freeze commit <sha>, freeze SHA-256 <digest>, input SHA-256 <digest>, roster SHA-256 <digest>, distributions SHA-256 <digest>.

The freeze pins this plan, `research_rig/common_48.py`, `research_rig/score_48.py`, `research_rig/test_48.py`, `config/thresholds.yaml`, `research_rig/calendar_25.json` and `research_rig/CALIBRATION_48.json` in `research_rig/PINNED_48.json`; ledger row 182 and queue row 86 must link this plan in both commits. The scorer reruns the calibration and refuses if it does not match the pinned file. The lead creates an empty owner-only /home/user/workspace/rig/data/replay_48 and runs `python3 -I -B research_rig/score_48.py --validate-inputs` with the five pin flags, then `--go` once. The go claims `score_48.lock` before any return and writes `results_48.json`; a second go refuses, and a failure after the lock consumes the run. Runs use nice 10 and a 480 MiB address cap.

`research_rig/test_48.py` runs every real-mode path as a subprocess in a temporary Git repository: validation, go and a refused second go, plus a changed roster refused on its pin. It copies the real scorer, engine, test, calendar and config; only the scorer's data path line and the calibration trial count are rewritten, and the plan, ledger and queue rows there are stubs. All numbers in it are synthetic.

## Forward watch

The December 2026 turn is watched with pretend money under these same rules in `practice/traders/E04_muni_cef_january_watch.md`, whatever the back-test says. It is not one of the ten judged turns.
