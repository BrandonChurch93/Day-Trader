<!-- Built from pinned aggregates by research_rig/build_doc157_plan73_diagnosis.py. -->
# Plan 73: about half the search gain was gone after the first minute

MEASURED: On the 182 search trades with every Coinbase clock available, mean net fell from +75.6 basis points at the hourly open to +39.4 one minute after the hour. The fixed reading was **REACHABLE**, but the one-minute mean cleared its line by just 1.16 bp. This was a diagnosis, not a pass. No money follows.

## What was asked

STATED: Could the over-extension rule's search gain survive an entry price someone could plausibly reach? Plan 72's earlier-date test closed at the power check before requesting minutes. [Doc 153](153_overextension_lead_outside_evidence.md) had warned that a sharp hourly open print might not be a price people could trade. Plan 73 therefore repriced rule 71-013's own already-searched trades instead of opening a new dated test.

## What was compared

MEASURED: 182 of 382 frozen search trades, on 142 UTC entry days, had every clock and entered every mean below. They covered 17 coins out of 19 candidate USD pairs. The request plan contained 1,845 bounded requests: 736 hourly and 1,109 minute requests.

- **No Coinbase print in any requested window:** 185 trades, or 48.4% of the original search trades.
- **Named outage dates:** 11 trades were set aside before requests were planned.
- **Missing prices after those exclusions:** 4 trades were missing an hourly open; 0 more were dropped for a missing minute.

STATED: Every Coinbase clock uses the same judged costs and funding. The one-minute line uses the midpoint of that minute's high and low, with the fixed fallback for a missing candle. The two late-entry lines keep the same exit. Worst-of-minute buys at the high and sells at the low.

| Clock | Mean net, bp | Share of same-ticket search mean |
| --- | --- | --- |
| Saved search net | +76.5 | 100.0% |
| Coinbase hourly open print | +75.6 | 98.8% |
| One minute after the hour | +39.4 | 51.5% |
| Enter five minutes late | +37.0 | 48.4% |
| Enter fifteen minutes late | +28.4 | 37.1% |
| Worst price inside the minute | -28.1 | -36.7% |

MEASURED: On the same trades, the one-minute price gave up 36.2 bp against Coinbase's hourly open (paired t -3.97, clustered by UTC entry day). It gave up 37.1 bp against the saved search net (paired day-clustered t -3.15).

| UTC entry year | Compared trades | One-minute mean net, bp |
| --- | --- | --- |
| 2020 | 28 | -49.6 |
| 2021 | 70 | +48.2 |
| 2022 | 60 | +64.9 |
| 2023 | 24 | +54.0 |

MEASURED: The fixed reading required at least 150 complete trades, a one-minute mean at least 50% of the same trades' search mean, and positive net at the five-minute entry. The one-minute mean kept 51.5% against that 50% line (+38.3 bp). The margin was 1.16 bp; the five-minute mean was +37.0 bp.

## What it does not show

- **STATED, selection:** These are the search's own selected trades. Selection flatters every figure here; the diagnosis is not fresh evidence that the rule earns money.
- **UNKNOWN, fills:** A candle midpoint is not an order fill. The worst-of-minute line lost money, and actual spreads, depth and prices reached are not measured here.
- **UNKNOWN, coverage:** About half of the search trades were in coins for which Coinbase showed no print at their ticket time. Empty windows do not prove a coin was unlisted. The result cannot tell us what those trades would have earned on Coinbase.

## Follow-on sum, not a test

STATED: To reproduce the sum in [ledger row 221](../../research_rig/TRIAL_LEDGER.md), take rule 71-013's plain search mean of 84.0654 bp, its matched day t rounded to 3.52, and its 267 active days from the [pinned Plan 71 search summary used for Doc 154](154_plan_71_second_coin_grid.md). Dividing that mean by the t and multiplying by the square root of the search days gives a rough day spread of about 390 bp. The t is for matched net, not the plain mean, so this is a scale estimate, not a direct measurement of daily standard deviation.

STATED: Taking 50% of the reachable mean gives an assumed edge of 19.7 bp. With independent signal days and a normal approximation for clearing a one-sided t line of 2.0, the sum gives about 7% power on the 115 days counted for Plan 72, and 13% even on 315 days. It takes about 954 separate signal days to reach 33% on that measure. This is a planning sum for the t line alone, not a scored return or a forecast of meeting every test mark.

STATED: No pooled dated test was opened because the available unspent history does not supply enough signal days. The 2017 to 2019 dates and the coin vault remain unspent; the [E09 pretend-money forward log](../../practice/traders/E09_overextension_dip_buy.md) continues. No reading is a pass or authorizes money.

STATED: The builder reads only the Plan 73 go and count aggregates and the Plan 71 search summary. Their SHA-256 pins are `096c68b3abf97def82c6c65d75463cefe71685a0e5abac367d248e5ab00cdf8f`, `1184602c216b6867c188307ed49d3f049e0bb2ca3a6b1dae6e07127817c0a633` and `babd3544e7ae86bd13b9cbfeca7b4d3b72ee8b33fda4492c6ef6fab1a2dd5558`, respectively.
