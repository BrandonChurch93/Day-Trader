# Categories for the decision autopsy

Copied into the repo on 2026-11-25 at 21:53 UTC. The only changes from the version written at 21:27 UTC: the names of the off-repo sample file and sampling script are replaced by plain words, and the labels file is named by its repo path.

Written 2026-11-25 21:27 UTC, before any outcome (price after, gain, loss, holding time) was joined to any answer. Fixed from reading a seeded blind sample (151 texts: 90 crypto buys, all 21 written crypto sells, 20 TM03 dial changes, 20 TM04 basket reasons; seed 59, made by a sampling script in the off-repo working area). The sample file held text only; it is not in the repo, and its ids are in `timemachine/autopsy/hand_checks.json`.

## What was seen in the sample, in plain words

- Crypto buys (TM01, TM02) are almost all chart readings: a break above a level, a pullback that held, a floor that held, a bounce after a flush. Many name a stop and a target. In TM02 about half also quote a headline, usually as support for a price reason.
- Crypto sells are mostly not written by the model at all. The desk sells when a stop, target or time limit set in an earlier pick is reached, and writes "Exit set in pick X: the stop price was reached". Only 21 sells in TM01 and TM02 carry the model's own words.
- TM03 dial changes read as reactions to the last day: a cut after a close under a level, often with ETF outflows or a macro headline; a raise after a rebound.
- TM04 basket reasons are trailing returns over 7, 30 and 91 days plus news: upgrades, results, approvals, deals.

## BUY categories (crypto buys, TM01 and TM02), one per buy

| Code | Name | What it means | Typical words |
|---|---|---|---|
| B_BREAKOUT | Chasing a rise | Buys because price broke above a level, made a new high, or keeps rising | breakout, broke above, new high, bull flag, higher highs, continuation, pressing |
| B_PULLBACK | Pullback in a rise | Buys a dip that held after a breakout or inside an uptrend | retest, pullback, held its first pullback, consolidation above |
| B_SUPPORT | A price floor | Buys at a floor, range low or a level tested more than once | support, range low, floor, double bottom, held twice, shelf held |
| B_REVERSAL | Bounce after a fall | Buys a rebound after a flush, sweep or crash | flush, capitulation, V-reversal, sweep, hammer, rebound, reclaim, false breakdown |
| B_RELSTRENGTH | Strongest coin | Buys the leader against the others | relative strength, leader, strongest, outperforming |
| B_HEADLINE | A headline first | A headline or catalyst is the main reason; price is secondary or absent | headline quoted first, catalyst, merger, approval, ETF inflows as the lead |
| B_INDICATOR | An indicator reading | Moving average, RSI or similar is the main reason | SMA, EMA, MA20, RSI |
| B_OTHER | Other or no reason | Top-up of an existing buy, re-entry with no new reason, or empty | top up, re-enter, adding |

Rule: the script looks for the words of each group in the buy's own reason. If exactly one group matches, that is the label (placed by rule). If none match it tries the pick's thesis the same way. If two or more groups match, or none, the text goes to hand labelling, read by the analyst and stored in `timemachine/autopsy/labels_by_hand.jsonl`.

## SELL categories (crypto sells, TM01 and TM02), one per sell

| Code | Name | What it means |
|---|---|---|
| S_STOP | Own stop | The desk sold because the stop set in a pick was reached |
| S_TARGET | Target reached | The desk sold because the target set in a pick was reached |
| S_TIME | Time ran out | The desk sold because the exit time set in a pick was reached, or the model says its own time limit or the session end |
| S_VIEW_PRICE | View changed on price | The model sold by hand because a level broke or the thesis failed on the chart, often "before the stop" |
| S_HEADLINE | Headline or macro | The model sold by hand mainly because of news or a macro event |
| S_EARLY_GAIN | Small gain taken early | The model banked a gain or part of it before the target |
| S_ROTATE | Rebalancing | Cut a laggard to free cash or move to another coin |
| S_SESSION_END | Desk closed it | Position closed by the desk at the end of the session with no pick behind it |
| S_UNCLEAR | Unclear | None of the above |

"Fear of a further fall" did not appear as a separate kind of text in the sample; it shows as the words "before the stop" inside S_VIEW_PRICE and S_HEADLINE and is kept as a flag.

## TM03 dial changes (daily bitcoin share), one per change

Direction (raise or cut) comes from the number asked, not from the text.

| Code | Name | What it means |
|---|---|---|
| D_PRICE_BREAK | Level broken or lower lows | A close under a floor, a new low, a failed bounce |
| D_PRICE_RECOVER | Rebound or reclaim | A close back above a level, up days, momentum confirmed |
| D_FLOWS_NEWS | Flows or headline | ETF flows, miner or company selling, a crypto headline is the main reason |
| D_MACRO_EVENT | Macro or event ahead | Fed, rates, tariffs, war, a vote or data due |
| D_STRETCHED | Move stretched, bank part | Trim after a big rise |
| D_OTHER | Other | None of the above |

## TM04 basket reasons (weekly stock basket), one per stock per change

Kind (added, dropped, kept) comes from the text prefix and the weights.

| Code | Name | What it means |
|---|---|---|
| K_MOMENTUM | Trailing returns | Price up over 7, 30 or 91 days, uptrend, strongest on the list |
| K_NEWS | Good news | Upgrade, results beat, approval, deal, contract |
| K_MOM_NEWS | Both | Trailing returns and good news together |
| K_DIVERSIFY | Exposure or defence | Added for a sector, defence, balance |
| K_WEAKNESS | Falling price | Dropped because price fell, trend broke, laggard |
| K_BAD_NEWS | Bad news | Dropped on a downgrade, miss, sale, legal or security news |
| K_OTHER | Other | None of the above |

## Flags, on every buy text (reason plus thesis)

- states_target: a target price or "target" is written. yes/no.
- states_stop_in_text: a stop or invalidation level is written. yes/no. (Separately, the pick's exit fields show whether a stop and target were set as numbers.)
- cites_headline: a quoted headline, a dated news item or the word headline. yes/no.
- size_or_confidence: words about size or conviction (small, starter, half size, modest, high conviction). yes/no; no numeric confidence was seen in the sample.
- exit_before_stop (sells only): the model says it is leaving before the stop.
