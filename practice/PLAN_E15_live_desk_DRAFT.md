# Plan E15 (DRAFT): a live desk where scouts propose and code decides

Status: DRAFT for the lead agent's rulings. Nothing here is registered, built or started. No venue request and no model session was made to write it. Labels: MEASURED (read in repo code or a repo record), STATED (a claim in a card, ledger row or the lead's request), UNKNOWN, INFERENCE (my reading).

What it is: pretend money, forward in real time, on Binance.US public data only. Cheap model scouts read a packet that plain code builds, and each one proposes a candidate. The criteria gate (`practice/gate.py`) recomputes every check from prices it fetches itself. If the checks pass, code books a pretend fill at the walked book price plus the stated fee. Code also exits at a fixed time. No model sets size, entry or exit. Each scout-chosen line runs beside a rule-only twin on the same wake, with the same timing and the same book, so the two can be compared trade for trade. The question it answers: does a scout's choice beat the bare rule?

## 1. Inputs the scouts may see

Recommendation: the scouts open nothing themselves. Plain code fetches a packet each wake and hands it to the scout. The scout has no web access and no tools. This keeps every request inside the shared request gate and keeps the barred sources out by construction.

Packet contents (all from Binance.US public REST through `practice/venue_binance_us.py`, the only paths that file allows: `/api/v3/klines`, `/api/v3/depth`, `/api/v3/exchangeInfo`, `/api/v3/aggTrades`, MEASURED from `PUBLIC_ENDPOINTS`):

- Closed hourly candles for the 20 USD coins in `COINS` (MEASURED: AAVE ADA AVAX BCH BNB BTC DOGE DOT ETH HBAR LINK LTC NEAR PEPE SHIB SOL SUI XLM XRP ZEC), the last 48 hours. The current open hour never counts.
- Pair status for each coin from `exchangeInfo`.
- For coins that pass the card's fixed pre-filter only: one depth snapshot, reduced to the spread and the walked cost of a $250 buy and sell (the existing `ticket()` output). Raw levels are not sent.
- Derived numbers computed by code: one-hour and two-hour returns, volume against the 24-hour mean, BTC's same-window return.

Binance.US terms (doc 194, MEASURED): "UNKNOWN (full Terms of Use unreadable; history page bars commercial use only)". The API docs mark `NONE` endpoints "can be accessed freely" under IP rate limits. The standing rule from doc 194 applies: detail stays off the repo, and use stops at once if the full terms bar it.

Other feeds doc 194 allows. Each could be added later. None is in the recommended first version.

- AlphaGrowth token unlocks: "ALLOWED WITH LIMITS". Its terms grant use "for any lawful purpose, including in AI agent responses, research, and commercial products", with credit "Data: AlphaGrowth (alphagrowth.io)", at 60 requests/min. It is the one non-price feed with a clear crypto use: a scheduled unlock is a dated fact a scout can cite. This is the alternative I would add first.
- GDELT: "ALLOWED WITH LIMITS", "unlimited and unrestricted use", with a citation needed on redistribution. INFERENCE: usable only as counts or tone by coin name. Its rows link to publisher pages, and many of those publishers are on the project's do-not-collect list, so no linked page may be opened.
- DefiLlama stablecoin data: "ALLOWED WITH LIMITS", "personal, non-commercial licence; may not republish the data in any form without permission". Slow-moving, and of little use hour to hour.
- SEC EDGAR: "ALLOWED WITH LIMITS", 10 requests a second, "does not allow 'unclassified' bots". Of little use for these coins.
- Treasury Fiscal Data: "ALLOWED". Macro only.
- Bitstamp and Gemini public prices: "ALLOWED WITH LIMITS" for private use. Possible as a cross-venue check on a single stale print. Left out to keep one venue.

Not allowed: Coinbase, Kalshi, CoinMarketCap and Polymarket ("BARRED WITHOUT CONSENT" in doc 194), and the listed crypto news publishers. Binance global announcements are "UNKNOWN" and on the known-refusal list.

Said plainly: the scouts will have no news text, no headlines, no social posts and no exchange notices beyond pair status. They see the same prices the rule sees, plus a book summary. Any edge they add has to come from reading that better than a fixed rule does.

## 2. How scouts run without the lead

Recommendation: a plain script calls a model API directly, with no tools. One call per triggered wake per scout: a fixed prompt template, the packet as JSON, and a reply limited to the candidate form. No call is made on a wake where the card's pre-filter finds nothing.

Option A, a script calling models directly (recommended).

- What it needs:
  - A model API key from the owner, entered as a secret, never in the repo.
  - A pinned model ID.
  - A frozen prompt template (its hash is logged).
  - The same long-running loop host the E12 to E14 loggers use.
- What can break:
  - The key expires or the API is down. That wake's scout line is void and counted, and the rule twin still runs.
  - A malformed reply is refused by the gate's form check.
  - The provider changes the model behind an ID. A pinned dated ID and a logged response header guard against this; a change ends the attempt.
  - Host restart. Missed wakes are void and never backfilled.
- UNKNOWN: whether a usable API key and endpoint exist today for the cheap models we want.

Option B, scheduled helper agents.

- What it needs: an automation that starts an agent session each wake, a brief, and a way to hand the packet in and the candidate out.
- What can break:
  - Start time drifts, so the request window can be missed.
  - Each session rereads its brief and carries tool overhead.
  - An agent could open the web against the rules, and we would have to audit command lists as in TM07.
  - Sessions can fail to start or stop part way.
  - Output is harder to pin to one template.

Fewer and smaller calls: Option A, called only on wakes where the pre-filter fires. INFERENCE from Plan 76's record (83 qualifying trades in about 2.9 years on 11 coins): the washout card would trigger a call well under once a day on average. An hourly open-scan scout (alternative) would make 24 calls a day per scout.

## 3. The decision path

The path: scout candidate, then card, then `gate.decide()` recomputes every entry check from closed bars it fetches itself, then a fresh post-decision book is walked for $250 and the STATED 2 bp taker fee is charged (BNB 1 bp, as in E12), then code exits at the card's fixed hold with a fresh bid walk.

Each step:

- The scout's candidate keeps the eight-field form in `practice/criteria/SCOUT_BRIEF.md`. Fields that carry a price, size, target or stop are refused (MEASURED, `CANDIDATE_TOP`).
- The rule twin uses the same card. Code picks the candidate the bare rule would pick (for example the largest faller), and the gate decides it the same way.
- One slot per line per card. A new signal is passed while that line holds.
- Exits are time only, no stop or target, because that is what E12 and E14 test (STATED in their cards). A missing or late exit book retries at the next wake and is never filled at an assumed price.

Missing in `gate.py` for live use (MEASURED from the code):

- Live prices come from `practice/market.py` (Alpaca). A Binance.US price source is needed: a new adapter on `PublicPages.klines` plus `closed_klines`. `venue_binance_us.py` stays unchanged (blob ccd1e045).
- Checks are per symbol only (`enough_bars`, `fell_at_least`, `rose_at_least`, `volume_above_mean`, `close_above_high`, `close_above_mean`). New checks are needed:
  - BTC's own fall over the lookback.
  - An alt's fall beyond a multiple of BTC's (for the E12 rule).
  - For the rule twin only, "largest faller in the roster".
- The candidate's `source` must be an `https` link. Here the evidence is a desk packet row, so the form needs an internal evidence id (for example `desk:<packet sha>#<coin>`).
- No fill model. The gate writes a pick for `trader.py`, which places orders on the Alpaca practice account. The desk needs its own pretend executor: fresh depth after the decision, `walk()` on asks, the same base amount sold into bids at exit, with fee, thin, late and missing books counted as void.
- No slot or position state, and no one-at-a-time rule.
- No handling of a busy, cooling or stopped request gate (see section 7).
- The decision log stores full bar rows. Under doc 194 it must sit in a private 0700 folder off the repo, with only counts in public.

## 4. Which criteria cards run first

Each card is fixed before the first trade. Each runs three lines on the same wakes, sharing books where the coin is the same: scout, rule-only and random control. The random line picks uniformly among the qualifying coins with a seed fixed at registration. It shows whether the rule or the scout beats blind choice among the same qualifiers.

Card W, washout pick. Built from E14 and Plan 76.

- Filter: the E14 roster (AAVE ADA BCH BTC ETH HBAR LINK LTC SHIB XLM XRP), last closed hour at least 5% below the prior close.
- Hold: 24 hours. Size: $250.
- Rule-only: the largest fall, ties in roster order. This is E14's rule.
- What the scout adds: it chooses which qualifier to buy, or passes. It can see volume, book depth and spread, BTC's move, and whether the fall rests on one hour of thin volume (Plan 76's own warning: "a 5% hourly move on a thin pair can be one stale print", STATED in STATUS).
- Basis (MEASURED in STATUS): Plan 76 gave +0.36% a trade at 75 bp a side, 83 trades. It failed the mark without each year's best trade. It met all four marks at 15 bp a side.

Card F, BTC-shock alt fade. Built from E12's judged rule 70-102.

- Filter: BTC's two-hour close move at or below -1.5%, and the alt's two-hour fall more than 2 times BTC's.
- Hold: 2 hours. Universe: alts only (MEASURED in `GRID_70.json`: lag 2, threshold 0.015, multiple 2.0, hold 2).
- Rule-only: the strongest excess, as `sweep_70` ranks it.
- What the scout adds: the same choose-or-pass on the same packet.
- Note: E12 runs this rule on its own wakes. The desk's rule-only line is a separate twin at the desk's own timing, so the comparison is fair.

Card S (alternative, shown only, not judged), open scan.

- Every 4 hours the scout may name one coin and one event word from a fixed list.
- The gate requires a fixed liquidity filter (walked $250 buy cost under a set number of basis points) plus `volume_above_mean`.
- Hold: 24 hours.
- No rule twin exists, so only the random line compares. This is the nearest thing to "scouts watch and propose" freely. Our record does not support it as a rule, so it should not be judged.

Recommendation: run W and F as judged cards with scout, rule-only and random lines, and hold S until the lead rules.

## 5. Marks fixed before the start

- Primary per card: the paired difference, scout line minus rule-only line, in net return per signal. When the scout passes and the rule enters, the scout's return is 0.
- The desk beats the rule only if all four hold:
  - Mean paired difference above zero.
  - Mean above zero after dropping the best two differences.
  - t of at least 2.0, clustered by UTC entry day.
  - The scout line's own net mean above zero after fees.
  These are the same marks E12 and E14 use (STATED).
- Judging count:
  - Card W: 60 paired signals, under 30 too few. This mirrors E14's `judging_count` and `judging_floor` (MEASURED in config).
  - Card F: 150, under 60 too few. This mirrors E12 (STATED).
  - Each card also has a fixed last date, to be ruled.
- Signals where only one coin qualifies are counted separately, because there the scout can only pass or match the rule. The judged figure uses all signals. The share with two or more qualifiers is reported.
- Early stops are operational only. No profit is read before judging, as with E12 and E14.
  - A venue stop (HTTP 418, 401, 403, 451) or an unresolved in-flight marker ends the run, and a new start needs a ruling.
  - Binance.US terms found to bar the use end it.
  - Scout replies that fail the form or the model call on more than a set share of the first 20 triggered wakes stop it for repair, and the repaired build is a new attempt.
  - A changed model ID or prompt hash ends the attempt.

## 6. What is logged

Everything goes into one private, hash-chained log per card, in the anchored style of E14, under `/home/user/workspace/rig/data/desk_e15` (0700 folder, 0600 files). In public there are only counts and status.

Per wake:

- Clock checks.
- Each request with its gate outcome (ok, busy, cooldown, stop, late).
- The candle panel's hash.
- The pre-filter's measured values for every coin.
- The qualifiers.
- The packet hash and the packet.

Per scout call:

- Model ID, prompt template hash, packet hash.
- Raw reply, token counts, latency, error.
- The candidate file.

Per proposal: the candidate, plus tags from a fixed list that the scout must pick from to say what it relied on (for example `volume_spike`, `thin_book`, `btc_also_fell`, `single_hour_print`, `wide_spread`, `pass_no_edge`). Free text is kept but never parsed.

Per gate decision (accept or refusal), what the gate already writes (MEASURED): every check with its measured value, the bars used and their hash, the criterion that failed, card hash and settings. Also the rule twin's and the random line's choices on the same wake.

Per fill or exit:

- Book receipt time and hash.
- Midpoint, walked price, cost in basis points, fee.
- Void reason (missing, late, thin, cooldown, busy).
- Base amount, exit time, net.

This lets a later read say, for each trade, what the scout saw, which tags it cited, which check had the most room, and how it did against the rule's pick on the same hour.

## 7. Request timing and a busy gate

Occupied times after each hour, as given by the lead (STATED):

- E12: from +5 s to as late as +899 s when it has a signal.
- E14: +195 s to +290 s (MEASURED in config: `wake_offset_s` 195, `book_cutoff_s` 290).
- Measurement 134: +480 s to +600 s (MEASURED in its plan, doc 202: wake at HH:08:00, no dispatch at or after HH:10:00).
- E13: 00:00:10 to 00:15:00 UTC daily (MEASURED in its card).

Recommendation: the desk window is HH:20:00 to HH:25:00 UTC (+1200 s to +1500 s). Candles start at +1200 s. The scout call runs with a 120 s cap. Entry and exit books must arrive before +1490 s, and nothing is sent at or after +1500 s. Hold times are counted wake to wake, so a 24-hour exit falls in the same window. This leaves 301 s clear after the latest scheduled use (E12 at +899 s) and 35 minutes before the next hour's +5 s. Alternative: HH:40 to HH:45, which leaves more margin after the others but enters 20 minutes later still.

Load: about 20 candle requests plus a few books per wake. Pacing is 0.4 s per host, MEASURED in `PublicPages.get`, so about 10 s of requests.

The shared gate, MEASURED from `Gate.mutex`: it waits up to 0.5 s for the lock, then raises `Failure("shared_gate_busy")`. Measurement 133 died because that error was unhandled (STATED in STATUS). The desk's behaviour:

- An unsent request that gets `shared_gate_busy` retries in short steps for at most 20 s of monotonic time and only inside the window cutoff, as E14 and Measurement 134 do (`busy_wait_s` 20). After that the request is counted as lost. It never crashes the loop.
- A lost candle page voids new decisions for that wake on every line. Due exits are still tried.
- A lost entry book voids that line's entry, which takes no slot. If the scout line and rule line need different books and only one arrives, that signal's paired difference is void and counted.
- A lost exit book means the exit waits for the next wake's window and the delay is logged. It is never filled at an assumed price.
- A shared cooldown (after HTTP 429 or a request with no status) is respected. If it ends after the cutoff, the wake is void.
- `Blocked`, `GateStorage`, `GateUncertain` and `GateGeneration` stop the desk cleanly with a status line, as the gate requires. Nothing is retried.
- The desk holds the gate per request only, never across the model call.

## 8. What the owner sees

One card on the local dashboard. It reads `data.json`, which is git-ignored (MEASURED), so detail stays off the public repo. All times are shown in Mountain Time.

- Status: running or stopped with the reason, last wake, next wake, and the gate state (ok, cooling until a time, stopped).
- Open pretend positions: card, line (scout, rule, random), coin, entry time, exit due.
- The last 10 proposals: time, card, coin or pass, the scout's tags, and the outcome. Outcomes are accepted, refused (with the named check and its measured value, for example "fell_at_least: change -0.041 against -0.05"), or void (with the reason).
- Counts so far: triggered wakes, scout calls, accepts, refusals by reason, voids by reason, and closed trades against the judging count.
- Recommended: no running profit on the card before judging, as with E12 and E14. This needs a ruling (below).

## 9. Risks, and what would make it uninformative

- Too few trades. INFERENCE from Plan 76's 83 trades in about 2.9 years: Card W may take about a year to reach 30 paired signals. Card F's rate on Binance.US is UNKNOWN.
- Often only one coin qualifies. Then scout and rule pick the same coin, and the only lever is passing. If most signals have one qualifier, the comparison mostly measures the value of passing.
- Same information. Without news, the scout sees what the rule sees. A tie is a likely and still useful outcome. It would mean the cheap scouts add nothing on price data alone.
- Thin books after a crash. Voids would cluster in the hours that matter and bias what is left. Void counts are reported for every line.
- Model drift. A changed model behind an ID, or a changed prompt, breaks the record. Both are pinned and logged, and a change is a new attempt.
- Shared gate side effects. Our 429 or no-status cooldown is shared. A 900 s cooldown starting at the end of our window ends before the next hour's E12 wake, but a long `Retry-After` from the venue could reach other loggers (UNKNOWN).
- Terms. The full Binance.US terms are UNKNOWN. A bar there ends the desk.
- Family counting. Card W counts with Plan 76 and E14, and Card F with E12 and its family. Neither is a fresh test of the rule. Only the scout-against-rule question is new.
- Host uptime and clock. Missed wakes are void, and a bad clock is refused. Long downtime shrinks the sample without biasing it, as long as it is unrelated to the market.
- Timing. The desk enters about 20 minutes after the hour, while Plan 76 entered at the hourly open. The rule twin has the same delay, so the paired comparison stays fair, but the rule's own figure is not Plan 76's.

## Choices for the lead to rule on

1. How scouts run: direct model API script (recommended) or scheduled helper agents. If it is the script, the owner must provide a key, and someone must name the model ID.
2. How many scouts: one scout model (recommended) or two models, each with its own line.
3. When scouts are called: only when the pre-filter fires (recommended) or an hourly open scan.
4. Cards: W and F judged (recommended), and whether Card S runs as shown only.
5. Whether to add the random control line (recommended).
6. Whether to add AlphaGrowth unlocks as a second input (recommended for the second version, not the first).
7. The desk window: HH:20 to HH:25 UTC (recommended) or HH:40 to HH:45.
8. Judging counts and last dates for W and F.
9. Running profit on the dashboard: hidden until judging (recommended) or shown.
10. The early-stop share for failed scout replies in the first 20 triggered wakes.
