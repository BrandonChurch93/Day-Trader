# Replay 20: short the jump after an Upbit won listing

Status DRAFT. Queue 29, ledger 157. No real score is authorized. All dates have already been viewed. This is a per-trade check, not a simulated account.

## What the source says

STATED. [Dima's write-up](https://dimaquant.substack.com/p/a-15-sharpe-crypto-short-strategy) gives this rule. Its red-day wait is not the earlier hourly entry we first proposed.

- Pump: “pump high: the highest price since the Upbit notice”.
- Signal: “red day: close(d) < close(d−1), with daily closes at 00:00 UTC”. “Wait for the first red day: the listing day or either of the next 2 days”.
- Entry: “Short at 01:00 UTC the next morning”.
- Stop: “Put the stop at the pump high, but never more than 25% above entry, and place it on the exchange straight away”.
- Exit: “Close after 3 days, with no profit target”.
- Ordinary jumps: “other Binance coins that jumped 25% or more without an Upbit notice”. The article does not give their trigger clock or reference close. For its comparison it says “All three groups use the same fixed 25% stop, and funding is left out so they compare fairly.”

STATED. One write-up reports +2.8% per trade at 15 bps a side with funding. Its −0.2% other-pump comparison used the fixed stop and left funding out. There is no 25% listing-trade screen in the rule. We keep the source timing, but use the same pump-high stop, fees and funding on listings and ordinary jumps. This does not reproduce the author's portfolio sizing, leverage, concurrency cap or equity curve. The source chose the hold after viewing data and tried many variants.

## What counts

- Use notices from 2020-01-01 through the 2026-10-31 UTC close. Take the first KRW notice per coin in the file before checking the contract flag, not a later repeat that happens to have a contract. Keep dead coins. Use the first-published UTC minute, not the planned trading start. The file was rebuilt today from Upbit's API, which shows edited notices with their first-published time, not necessarily the exact original text. Completeness and ticker-based historical identity are not guaranteed.
- The file has 271 KRW rows and 106 candidates flagged by archive path metadata. A contract with no trade candle in the notice hour is not trading for this test and is not an event. Exclude it, count it and list the coin. The pinned matches include scaled contracts and a BEAM alias. The universe is Plan 16's viewed and held USD-M store.
- Use the UTC day containing the notice. Compare its last hourly close with the previous day's last hourly close. Wait for the first strict decline on the listing day or either of the next two. If none is red, do not trade. Enter at the next UTC day's 01:00 open. The pump high is the highest hourly high from the notice candle through the last candle before entry. There is no minimum pump size.
- Cover at the first hourly high that reaches the lower of the pump high and 25% above entry, filled at the worse of that level and that hour's open. A gap can lose more than 25%. The stop can trigger inside the entry candle. Otherwise cover at the hourly open 72 hours after entry, without using the later high of that candle. Hourly bars cannot order intrahour events. Including the whole notice candle and assuming the adverse stop fill are deliberately pessimistic conventions.
- No leverage or compounding. Equal notional per trade, overlapping trades allowed, sized independently. Charge 15 bps on entry and exit notional, with 30 bps shown only. A positive settled funding rate pays the short. Apply the rate to mark open times fixed quantity, normalized by entry notional. Pay a short exiting on the settlement boundary, not one entering then. Intrahour stop timing is an approximation. Do not impute funding.
- A zero-volume entry cannot fill. A zero-volume candle cannot trigger a stop, and a zero-volume timed exit waits for the next positive-volume open. Daily closes still count when the final candle has zero volume. If the contract tape ends before the exit can fill and before the sample ends, book the last hourly close at its completion boundary, include funding through that point and flag the trade. It is a terminal-archive proxy, not a verified delisting fill. An internal gap or the sample cutoff is not a terminal close.
- Reconcile all flagged notices as trades, no red day, not trading at publication, no entry fill or other unavailable windows. Do not impute missing bars or settlements.

## Ordinary jumps and marks

- In the same store, find hourly opens where the higher high of the previous two candles is at least 25% above the close three candles back. Exclude a trigger with a KRW notice in the previous seven days, including the trigger minute, or no actual trade candle at the trigger hour. Count missing trigger candles by contract. Keep the first eligible trigger and suppress further triggers in that contract for seven elapsed days, even if the first does not trade. Start the red-day wait on the UTC day containing the trigger. Include the two pump candles in the high, then use the same 01:00 entry, stop, exit, zero-volume and terminal-close rules, fees and funding. No retrospective exclusion for later news.
- Draw 1,000 sets without replacement within each set, matching UTC notice year to UTC trigger year. Controls can reappear across sets. Use the fixed seed and linear interpolation for the 95th percentile. If a year has too few controls, the placebo mark cannot pass. Dependence and overlap mean this is not a significance test.
- All five marks are required: at least 30 judged trades, mean net above zero, mean strictly above the 95th percentile of ordinary-jump set means, mean still above zero after removing the best three, and a trade-mean t-statistic of at least 2.0. Divide the mean by the sample standard deviation over the square root of trade count. If undefined, the mark does not pass. This is a mark, not a probability statement about dependent trades.
- Shown only: median, winners, stops, worst loss, funding contribution, by year, terminal closes, delayed timed exits, higher fee sensitivity and the subset on the [November 25 US shortable list](../docs/research/60_us_venue_costs_checked.md). This is today's list, using exact unscaled ticker and contract matches, not historical US access. Almost none of these coins can be shorted from the US. Binance execution and funding do not establish US fills.
- Lead's hourly proxy, shown only: reference the last hourly close at or before publication. Enter at the first open at least 60 minutes after publication if the high from the notice candle through the last completed candle is at least 25% higher. Also show that entry without the jump screen and the screened entry one candle earlier, using only highs available by the earlier entry. If there is no notice-period high before that entry, do not trade. Keep the same stop, exit and costs.

## Offline inputs and one shot

- Notice CSV SHA-256 `6d7e4a67f7964d394a9412551369df27c2317b21a156d2cb5cd73f34040baec7`. No notice rows or bars in the repo.
- Plan 16 futures manifest SHA-256 `07a28ae776606bb1430aa91ab94ae69b5cfeec37e0f48c9f2d342ab745e8b94d`; held extension `d2949c130e4d98d13ed4bf376abee0700e4122fbf76af80a7d8fcf695a1e9afd`. Keep disjoint daily repairs beside truncated monthly archives. Supplement missing coin-months only by path and checksum from the public bulk archive and pin them separately before freeze. No live venue prices or funding.
- `--clock-scan` reads clocks, settlement intervals and byte-level field categories on the selected ZIPs. It does not numerically decode prices or rates, calculate returns or acquire a lock. Numeric OHLC consistency, coverage for a particular trade and whether a zero-volume candle supplied a judged signal or fill are not clock-scan findings.
- MEASURED, clocks and field categories only. The scan checked 37,531 ZIPs across 280 symbols with no file refusals. It read 9,008,240 trade rows, 9,090,663 mark rows and 1,412,514 settlement rows. There were 515,585 zero-volume trade rows. Of 106 first-notice flags, 17 had no trade candle at publication, all before the first archived trade hour. Possible signal, entry, timed-exit and stop roles touched zero-volume candles in 2, 2, 2 and 3 candidates, respectively. Counts overlap and do not identify the actual signal or exit.
- A separately authorized run at a clean freeze first verifies pins and silently loads and validates each symbol. Refusals print only a fixed code and path. The exclusive off-repo lock is acquired just before scoring. The scorer then rereads the same hash-pinned bytes one symbol at a time to fit the memory cap. No price-derived output or lock before full validation. This draft cannot score real data.

## Made-up checks

The fixtures exercise a planted edge, no edge and three unusual winners. The calibration uses 60 synthetic after-cost trades per seed, shared year noise and a heavy-tailed trade noise mixture. This is a judgment check, not a real-world power estimate.

MEASURED on invented returns. The initial four marks cleared 3 of 20 seeds at a 0% plant. Before reading prices, the lead raised the placebo cutoff from the 90th to the 95th percentile and added the t-statistic mark. With unchanged seeds and noise, 0%, 1%, 2% and 4% net plants cleared all five in 0, 3, 5 and 17 of 20 seeds, respectively.

UNKNOWN. Whether the edge works on this store or in a US account. One publication, all viewed dates, notice and archive coverage and hourly fill approximations do not establish live performance.
