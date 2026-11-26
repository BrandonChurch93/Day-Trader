# E06: Forward watch of the hot-coin rules R1, R2 and R3

Status: written 2026-11-26 at the lead's request, after the TM06 six-model result ([page 102](../../docs/research/102_time_machine_tm06_six_models.md)). Pretend money only: no AI, no broker, no account, no orders. The card id E05 was already taken by the Plan 51 record, so this is E06.

## Why forward

STATED. In TM06 the six AI pickers behaved like the plain top 7-day rise rule. R2 came out of the TM06 reasons and was found in-sample. Every date up to 2026-11-23 has been read, including all TM07 weeks, so the TM07 plan shows R1, R2 and R3 only, with no claims. The test on unseen dates is this forward watch.

## The rules

Each rule uses the TM06 code in `timemachine/tm06.py` (`listed`, `change_pct`, `volume_row` and the `top_7d_rise` ranking) on candles fetched at the time, with the TM06 settings named here.

- The coins are the 20 of `tm06_plan.coins`. A coin counts as listed at a wake if it has a recorded minute in the `tm06_pick_listed_hours` before the wake.
- R1: at each daily wake (`tm06_plan.picker_wake_hour_utc`, UTC) hold, in equal parts and long only, the `tm06_plan.picker_max_names` listed coins with the largest rise over `tm06_plan.picker_rise_days` days. Ties go to the earlier symbol.
- R2: R1, then drop any pick whose 24-hour change at the wake is below zero and whose `volume_row` ratio (last 24 hours of dollar volume against the mean of the `tm06_pick_volume_usual_days` days before) is at least 1.5. A missing ratio does not drop a pick. Dropped picks are not refilled. The rest are held in equal parts; no picks means cash.
- R3: buy all 20 coins in equal parts at the first recorded wake and hold them, with no rebalancing (the TM06 `equal_all_held` yardstick).

## Pretend fills

- Each arm starts with 1,000 pretend dollars.
- The fill price is the open of the first recorded Coinbase minute at or after the wake, within 15 minutes.
- Costs: the fee `tm06_plan.main_fee_bps` per side plus each coin's half spread (`tm_perp_half_spread_bps`, else `tm_crypto_half_spread_bps_by_coin`, via `timemachine/perp.py`), charged on traded notional. These are the same fee and spread as TM06.
- No funding is charged, because these are spot-style holdings. This differs from TM06, which charged perpetual funding.
- An arm trades only when its set of names changes, back to equal parts of the new set, scaled once so the book stays fully paid. An unchanged set drifts.

## Data and rate limits

The logger reads only the public Coinbase Exchange candles endpoint (`https://api.exchange.coinbase.com/products/{COIN}-USD/candles`), with no key.

- At most 2.5 requests a second, which is below the venue's public limit. It backs off on 429 and stops on 401, 403 or 451.
- About 160 requests a day.
- It does not use CoinGecko or any scheduled keyless logging.
- The candles used are those available at the record time, all stamped at or before the wake, apart from the fill minute.

## Freeze, schedule and records

- Frozen by the commit that adds this card and `practice/forward_e06.py`. `python3 practice/forward_e06.py start` writes the header once. The header holds both files' SHA-256, the freeze commit, and the first wake: the first wake strictly after the freeze commit's time.
- `record` refuses to run if either file has changed.
- The watch runs 20 full weeks: 141 daily wakes, the first plus 140.
- The log is append-only and hash-chained, off repo, at `/home/user/workspace/rig/data/forward_e06/log.jsonl` (folder mode 0700, file mode 0600). It holds prices and picks, so it stays out of Git.
- A wake is recorded between 20 minutes and 3 hours after it. Several things make a wake void: no record in that window, any coin without a fill minute, or a refused fetch. A void wake is never back-filled from later data. Void wakes are logged when seen, and a wake with no record is void too.
- On a void wake no arm trades, and each arm keeps its holdings.

## How it is kept running

`record` is safe to call at any time: it does nothing unless a wake is inside its window and not yet recorded. Run it hourly, from a scheduled task or cron (`python3 practice/forward_e06.py record`). `loop` calls `record` every 10 minutes for as long as the process lives. If a long-lived process is fragile, use the hourly call. Either way, a missed window makes that day void.

## What would count, fixed now

- Weeks are seven wakes long. Week k runs from wake 7(k-1) to wake 7k, using each arm's value marked at the fill opens before trading. A week whose start or end wake is void is void.
- Two judged claims. R1 beats R3, and R2 beats R3: each needs a weekly gain strictly above R3's in at least 16 of the 20 weeks. A void week or a tie is not a win. Under a fair coin with independent weeks, the one-sided tail is 0.5909% (the TM07 table).
- R2 against R1 is shown only.
- The lead scores once, at the end (`score` refuses before then).
- Before the end, the only allowed look is `alive`. It prints counts only: wakes due, recorded, void, and the last record clock. Nobody reads picks, prices, values or returns in between.

## Limits

- Coinbase spot candles are not fills. A minute with no trade has no candle, and a fill minute can come up to 15 minutes late.
- The coin list is today's 20 and is fixed. A coin that stops trading makes every later wake void, which stops the watch; the card is not changed.
- Twenty weeks is a short window, and the weeks are not independent.
- The record time is up to 3 hours after the wake. Coinbase can revise recent candles: two fetches of the same range have returned slightly different minute counts. What the logger saw is what counts.
