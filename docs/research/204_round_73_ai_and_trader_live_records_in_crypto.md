# 204. Round 73: AI and trader live records in crypto

What this is: an idea-round check (dated 2026-11-27 UTC) of who holds a dated, public, checkable live record of making money trading crypto with an AI model or a fully stated rule set, what exactly they did, whether the record rests on method or on leverage plus one lucky stretch, and whether any piece can be rebuilt as fixed rules and tested on data we may use.

This note builds on three earlier repo pages and does not repeat them:

- `docs/research/18_ai_systems_with_live_records.md` (already covers Nof1 Alpha Arena press headlines for Seasons 1 and 1.5, OKX three-stage study, BingX snapshot, AIEQ, Numerai, Renaissance, TradeRank Seasons 0 to 8, Rallies, StockBench, DeepFund, AMA, AI-Trader, LiveTradeBench, FinRL, FINSABER, TradingAgents, and academic LLM papers).
- `docs/research/17_verified_traders_and_their_methods.md` (already covers USIC, Minervini, Kell, Luk, J Law, Sean and David Ryan, Zanger, Turtles, Kullamagi, Darvas, Warrior Trading, Raging Bull, and IBD 50).
- `docs/research/188_round_62_career_winners_by_mechanism.md` and `docs/141_idea_round_40.md` (already cover Thorp, Renaissance, Buffett, Greenblatt, Benter, Virtu, Jane Street, Jump, CTAs, WCTC, Hyperliquid HLP and user vaults, Ethena sUSDe, exchange copy-trading leaderboards, Collective2, and Darwinex).

Labels used here: MEASURED (verified directly from an opened primary filing, on-chain reconstruction, or venue page, or counted directly from repo files), STATED (reported by an operator or exchange announcement without independent trade-log audit), INFERENCE (reasoning drawn from those numbers), UNKNOWN (not disclosed or not verifiable from opened sources). No market prices or returns were pulled or computed in this round.

## Bottom line

Nothing to register. Across every new or unchecked real-money AI crypto contest since Doc 18, every exchange-run crypto contest, every API-verified exchange track record found, and the one SEC-audited systematic crypto fund family with a stated rule, zero records show a durable, rule-stated, cost-surviving edge that is not already covered by our live work. Only two methods are stated clearly enough to write as fixed rules: the Bitwise Trendwise daily 10-day and 20-day EMA cash-rotation rule (already overlapped by our running daily trend card `E13` on Binance.US, and its audited 2025 live record underperformed BTC by 14.00% and BTC/ETH by 12.27%), and a deterministic no-LLM version of the low-turnover "Monk Mode" filter that merely lost less than higher-turnover AI prompts in Alpha Arena Season 1.5.

## New and unchecked AI crypto records since Doc 18

### Nof1 Alpha Arena: on-chain fill audit and Season 2 status

Doc 18 reported only press headline returns for Alpha Arena Season 1 and Season 1.5. An October 29, 2026 third-party on-chain reconstruction (last updated November 23, 2026) by TradingAgentStack (author metadata: Ahsen Rajab; no company named; independent of Nof1) from Hyperliquid public fill and funding history audited all 38 real-money accounts ($10,000 starting capital each) and found that 31 of 38 accounts lost money (STATED by [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/), noting open-end marks use 4-hour candle interpolation that can shift returns by a point or two).

Season 1 (crypto perpetuals on Hyperliquid, ended November 3, 2025, six models at $10,000 each) recomputed results (MEASURED from [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)):

- Qwen3 Max: +20.3% (+$2,035 PnL), $1,669 fees paid, 456 fills, -45.2% closed-trade realized drawdown.
- DeepSeek Chat V3.1: +6.9% (+$685 PnL), $719 fees paid, 341 fills, -55.4% closed-trade realized drawdown.
- Claude Sonnet 4.5: -29.9% (-$2,994 PnL), $590 fees paid, 320 fills, -43.0% closed-trade realized drawdown.
- Grok 4: -45.1% (-$4,514 PnL), $391 fees paid, 346 fills, -53.0% closed-trade realized drawdown.
- Gemini 2.5 Pro: -57.7% (-$5,766 PnL), $1,347 fees paid, 1,286 fills, -75.6% closed-trade realized drawdown.
- GPT-5: -63.4% (-$6,341 PnL), $545 fees paid, 684 fills, -76.0% closed-trade realized drawdown.

Season 1.5 (US stock perpetuals and crypto on Hyperliquid, November 19 to December 3, 2025, eight models across four rule-set accounts of $10,000 each, 32 accounts total) recomputed aggregate results by model and rule set (MEASURED from [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)):

- Only one model finished net positive across its four accounts: Grok 4.20 at +13.0% (+$5,206 PnL, $1,514 fees paid across 5,686 fills).
- Both Season 1 winners collapsed in Season 1.5: Qwen3 Max finished at -29.7% (-$11,793 PnL, $6,209 fees paid) and DeepSeek Chat V3.1 finished at -32.9% (-$13,169 PnL, $6,091 fees paid).
- The remaining models all lost money: GPT-5.1 (-6.0%, $3,133 fees), Gemini 3 Pro (-30.1%, $4,463 fees), Kimi K2 Thinking (-34.2%, $6,171 fees), Claude Sonnet 4.5 (-39.1%, $4,845 fees), and Grok 4 (-58.7%, $5,248 fees).
- Across all eight models, the four prompt rule sets all lost money combined: Monk Mode -9.5% (1 of 8 accounts up), New Baseline -28.6% (1 of 8 up), Max Leverage -28.8% (2 of 8 up), and Situational Awareness -41.8% (1 of 8 up).

What remains missing and whether trade logs can still be opened:

- Holding times, exact leverage caps, and Season 1.5 realized drawdowns are UNKNOWN in the reconstruction; the Season 1 drawdown figures exclude unrealized intraday swings, so true peak-to-trough drops were at least as deep ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)).
- The account addresses were taken from archived `nof1.ai` pages for Season 1 and `alphaarena.ai` for Season 1.5, and matched against Hyperliquid's public fill and funding history, with an open JSON export referenced by the auditor; whether the original Nof1 web pages still serve live logs is UNKNOWN, while Hyperliquid on-chain history remains public by address ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)).
- Season 2 had not launched as of October 2026, even though Nof1 raised $15 million in May 2026 (STATED in [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)).

### WEEX Global AI Trading Hackathon (January to March 2026)

This is a new real-money AI crypto contest not covered in Doc 18. WEEX ran "AI Wars: WEEX Alpha Awakens" with a January 12 to February 2, 2026 preliminary round featuring 788 teams starting with 1,000 USDT each, followed by Dubai finals starting January 30, 2026 (STATED in [AP News / GlobeNewswire](https://apnews.com/press-release/globenewswire-mobile/weex-global-ai-trading-hackathon-enters-final-sprint-of-preliminary-round-as-788-teams-battle-for-finals-qualification-8a07108fc34d2771d2f9556900f38f0c)).

Finals results self-reported by WEEX (`By: weex`, exchange's own promotional news posts, not an independent audit; the February 26 post explicitly notes the leaderboard was unreviewed at the time of writing) on February 26 and March 9, 2026 (STATED in [WEEX finals summary](https://www.weex.com/news/detail/how-weex-ai-trading-hackathon-tested-real-market-ai-strategies-349019) and [WEEX champions notice](https://www.weex.com/news/detail/weex-ai-hackathon-champions-crowned-revealing-future-of-ai-trading-362100)):

- Only 8 of 37 finalists ended the 15-day finals in profit (21.6%).
- Top five final ROIs were 100.27%, 91.97%, 74.08%, 43.86%, and 28.44%.
- Across all finalists, WEEX reported 20,251 API calls, a single largest winning trade of +$12,662, and a maximum drawdown of $21,977.
- First place went to `todd` ($600,000 prize package including a Bentley Bentayga S), with `Shadow Trading AI` and `奥印AI量化系统` taking second place.
- Finals starting capital per account, per-team trade counts, holding times, leverage used, fees paid, exact strategy rules, and public trade logs are all UNKNOWN; neither WEEX announcement publishes trade logs or fixed rules.

### Bybit WSOT 2026 AI Showdown (November to December 2026)

Bybit added a dedicated AI Showdown inside WSOT 2026 running from November 13, 2026 10:00 UTC to December 2, 2026 10:00 UTC with a 1,000,000 USDT prize pool paid to the top 200 accounts ranked by P&L using a Bybit AI Subaccount (STATED in [Bybit WSOT 2026 announcement](https://announcements.bybit.com/en/article/wsot-2026-battle-on-main-competition-is-live--art0dfef555c6ff/)).

Key constraints and unknowns (STATED in [Bybit WSOT 2026 announcement](https://announcements.bybit.com/en/article/wsot-2026-battle-on-main-competition-is-live--art0dfef555c6ff/)):

- Users may register 1 main UTA account plus up to 6 UTA subaccounts.
- Market Makers, Institutional users, and VIP Pro 3+ accounts are excluded.
- Because the contest is still live through December 2, 2026 and the announcement states no trade-log or strategy publication, final returns, trade counts, holding times, leverage, fees, and public trade logs are UNKNOWN.

### TradeRank Seasons 9 to 11 update (paper control, not real money)

Doc 18 covered TradeRank through Season 8. TradeRank (operator unnamed, no independent audit stated; site's own simulated benchmark) uses $10,000 of simulated capital per model on live crypto and US stocks, so it is a paper control rather than a real-money record, but its multi-season persistence test is directly relevant (STATED by [TradeRank](https://www.traderank.ai/llm-for-trading)):

- Across 11 completed seasons (78 LLM competitors, 3,131 total trades; 131 model-seasons, with settled-season persistence findings drawn from 10 settled seasons, Seasons 0 to 6 and 8 to 10), only 38.9% of model-seasons finished profitable.
- Across 8 consecutive-season transitions, pooled rank correlation was +0.054 (interval -0.2 to +0.3), and a top-half finish was followed by another top-half finish 17 times in 39 tries versus 18.15 expected by chance.
- In Season 11 (refreshed November 26, 2026), only 1 of 22 live paper models was in profit, at +0.24% (STATED by [TradeRank Leaderboard](https://www.traderank.ai/ai-trading-leaderboard)).

## Verified crypto fund, contest, and API-linked trader records

### Bitwise Trendwise SEC-filed systematic crypto ETFs (`BITC`, `BTOP`, `AETH`)

Outside the records already in Docs 17, 141, and 188, the cleanest dated, public, audited live systematic crypto record is the Bitwise Trendwise ETF suite regulated under the Investment Company Act of 1940 (`BITC`, `BTOP`, `AETH`).

Stated fixed-rule design in SEC Form 485BPOS filed April 30, 2026 (MEASURED from [SEC Form 485BPOS](https://www.sec.gov/Archives/edgar/data/1928561/000121390026049948/ea0287769-01_485bpos.htm)):

- `BITC` observes and compares bitcoin's 10-day and 20-day exponential moving average (EMA) price and rotates between 100% notional exposure to CME front-month bitcoin futures and 100% US Treasury securities, exiting to cash rather than shorting on downward trends.
- `BTOP` uses the same bitcoin 10-day and 20-day EMA signal to rotate between 100% notional futures (initially 50% CME bitcoin futures and 50% CME ether futures) and 100% US Treasuries.
- `AETH` applies the 10-day and 20-day EMA signal to ether price to rotate between 100% notional CME ether futures and 100% US Treasuries.
- Net annual operating expense ratios after contractual fee waivers (effective until May 1, 2027) are 0.88% for `BITC` and `BTOP` and 0.89% for `AETH` (0.85% management fee).
- Exact crossover buffer or confirmation threshold, exact conversion date to Trendwise, exact trade count, and holding times are UNKNOWN from the prospectus (SEC portfolio turnover is reported as 0% because short-term Treasuries and futures contracts are excluded from statutory securities turnover).

Audited full-year 2025 live results in SEC Form N-CSR filed March 9, 2026 (independently audited by KPMG LLP, opinion dated February 27, 2026; MEASURED from [SEC Form N-CSR](https://www.sec.gov/Archives/edgar/data/1928561/000119312526098141/d87694dncsr.htm)):

- `BITC`: -20.56% total return in 2025, underperforming its spot bitcoin benchmark by 14.00%.
- `BTOP`: -16.00% total return in 2025, underperforming its equal-weighted BTC/ETH benchmark by 12.27%.
- `AETH`: -0.05% total return in 2025, outperforming its ether benchmark by 11.00%.

### Bybit WSOT 2026 Individual and Squad Showdowns

Bybit's flagship real-money derivatives contest runs November 13 to December 2, 2026 with a 3,200,000 USDT Squad Showdown pool and up to 2,000,000 USDT Individual Showdown pool across three asset tiers (100 USDT minimum balance to compete) (STATED in [Bybit WSOT 2026 announcement](https://announcements.bybit.com/en/article/wsot-2026-battle-on-main-competition-is-live--art0dfef555c6ff/)). As in earlier exchange contests reviewed in Doc 141, entrants may run up to 1 main account plus 6 subaccounts, and no per-trade logs, fees, holding times, or methods are published (STATED in [Bybit WSOT 2026 announcement](https://announcements.bybit.com/en/article/wsot-2026-battle-on-main-competition-is-live--art0dfef555c6ff/)).

### ChainRated read-only API exchange verification

ChainRated (operator entity unnamed on page; third-party API-verification site) verifies live exchange accounts via read-only API keys computed strictly from closed trades and enforces all-or-nothing publication so a trader cannot hide a losing stretch once published, while warning plainly that opting in is voluntary so losing traders can remain unlisted (STATED by [ChainRated](https://chainrated.com/track/)).

The sole published live crypto account on the page as of November 24, 2026 (`tahtrade` on Bybit, verified from July 1, 2025 across 338 days) illustrates why headline win rates mislead (STATED by [ChainRated](https://chainrated.com/track/)):

- 24,641 closed trades, 88.1% win rate, 60 liquidations, profit factor 0.81, -70.2% total return, and 79% maximum drawdown.

## Method versus leverage and one lucky stretch

Every record above fails the test for a proven, transferable trading edge once independent trade count, leverage, and selection across entrants are checked (INFERENCE):

| Record | Dates and money | Independent trades | Method or leverage plus luck? | No-skill matched-leverage baseline |
|---|---|---|---|---|
| Alpha Arena S1 ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)) | Ended Nov 3, 2025; 6 accounts at $10k | 320 to 1,286 fills per model over ~2.5 weeks, mostly clustered on the same BTC/ETH/altcoin swings (far fewer than 30 independent regimes) | Leverage plus one lucky stretch. Both winners suffered -45.2% to -55.4% closed-trade drawdowns and lost -29.7% and -32.9% immediately in S1.5 | With 6 leveraged accounts over a 2.5-week crypto swing, having 2 of 6 finish +7% to +20% while paying $719 to $1,669 in fees is routine random dispersion |
| Alpha Arena S1.5 ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)) | Nov 19 to Dec 3, 2025; 32 accounts at $10k | 14 days total; 739 to 11,676 fills per account; fees of $197 to $3,257 per $10k account | Overtrading plus selection across 32 accounts. Only 5 of 32 accounts finished positive; all four rule sets lost -9.5% to -41.8% combined | Across 32 leveraged accounts running 2 weeks, picking the single best account (+33.7%) while 27 of 32 lose is consistent with zero skill minus fees |
| WEEX AI Hackathon ([WEEX](https://www.weex.com/news/detail/how-weex-ai-trading-hackathon-tested-real-market-ai-strategies-349019)) | Jan to Feb 2026; 788 teams -> 37 finalists, 15-day finals | UNKNOWN per team (20,251 total API calls across 37 finalists over 15 days) | Extreme selection plus leverage. 788 teams filtered to 37, and only 8 of 37 ended profitable; +$12,662 single-trade profit and $21,977 max drawdown confirm high-variance leveraged bets | Filtering 788 high-leverage entrants over two rounds of 15 to 21 days guarantees several +70% to +100% survivors by pure coin-flip variance |
| Bybit WSOT 2026 ([Bybit](https://announcements.bybit.com/en/article/wsot-2026-battle-on-main-competition-is-live--art0dfef555c6ff/)) | Nov 13 to Dec 2, 2026; live | UNKNOWN (19-day window) | Structurally designed to reward extreme leverage and multi-account lottery tickets (up to 7 accounts per user: 1 main + 6 subaccounts) | Running up to 7 leveraged subaccounts in a 19-day ROI/P&L sprint lets a zero-skill trader enter opposite directional bets and publish the surviving tail |
| TradeRank S0 to S11 ([TradeRank](https://www.traderank.ai/llm-for-trading)) | 11 completed seasons through Nov 2026; $10k paper | 3,131 trades across 131 model-seasons (~24 trades per model-season) | Zero measurable skill carryover: 38.9% profitable overall, rank correlation +0.054 across 8 transitions, 17 of 39 repeat top-half vs 18.15 chance | Indistinguishable from a no-skill baseline |
| Bitwise Trendwise `BITC`/`BTOP`/`AETH` ([SEC N-CSR](https://www.sec.gov/Archives/edgar/data/1928561/000119312526098141/d87694dncsr.htm)) | Full year 2025 audited; regulated ETFs | UNKNOWN exact count (a daily 10d/20d EMA typically triggers ~6 to 15 round trips per year, far below statistical power in 1 year) | Unlevered fixed rule, not leverage luck, but 2025 live whipsaw cost `BITC` 14.00% vs BTC and `BTOP` 12.27% vs BTC/ETH while `AETH` caught one ETH down-trend (+11.00% vs ETH) | One year with roughly a dozen correlated BTC/ETH regime switches cannot separate a real trend edge from single-year path luck |
| ChainRated `tahtrade` ([ChainRated](https://chainrated.com/track/)) | Jul 1, 2025 onward (338 days); Bybit | 24,641 closed trades | Anti-martingale/grid-like high win rate (88.1%) destroyed by 60 liquidations (-70.2% return, 79% max drawdown) | Worse than no-skill due to negative skew plus exchange fees |

## Practical end: rebuildable fixed rules, costs, and permitted data

Only two methods in the entire set are stated clearly enough to write as fixed rules without guessing hidden prompts or black-box weights. A third candidate (high-frequency exchange-contest AI bots) cannot be rebuilt because neither WEEX nor Bybit publishes rules or trade logs.

Cost baseline we must clear:

- Kraken Pro entry-tier spot fees are 0.40% maker and 0.80% taker (80 bp to 160 bp round trip before spread) (MEASURED from [Kraken Pro fees](https://www.kraken.com/pro/fees)).
- Binance.US entry-tier spot fees are 0.00% maker and 0.02% taker on Tier I pairs (0 bp to 4 bp round trip in exchange fees before book spread and slippage, with real book cost still unmeasured until Measurement 134 completes; Measurement 133 stopped unread and was replaced) (MEASURED from [Binance.US fees](https://www.binance.us/fees)).

Permitted data per `docs/research/194_data_source_terms_audit.md`:

- Permitted with limits for private non-commercial research: Kraken downloadable OHLCVT (`assets.kraken.com`), Bitstamp public price history (`www.bitstamp.net`), Gemini private analysis (`api.gemini.com`), Binance Vision archive for personal non-production backtesting only (`data.binance.vision`, CC BY-NC-SA 4.0, no live trading), and Binance.US public API/history (`api.binance.us`, pending full Terms of Use read).
- Barred without consent and excluded here: Coinbase market data, Kalshi, CoinMarketCap, and Polymarket.

### Ranked candidates and count-first steps

Rank 1: Daily 10-day and 20-day EMA long-only cash-rotation rule (from Bitwise Trendwise `BITC` and `AETH`, [SEC Form 485BPOS](https://www.sec.gov/Archives/edgar/data/1928561/000121390026049948/ea0287769-01_485bpos.htm))

- Fixed rule: on daily 00:00 UTC closes of BTC/USD and ETH/USD, hold 100% spot when the 10-day EMA is above the 20-day EMA and hold 100% cash when at or below; no leverage, no shorting.
- Holding period: multi-week (roughly 2 to 6 weeks per regime leg, INFERENCE).
- Cost survival needed: at roughly 8 to 15 round trips per year, the rule must clear ~0.6% to 2.4% annual drag on Kraken Pro (80 to 160 bp round trip plus spread) or ~0.1% to 0.5% on Binance.US (4 bp taker fee plus unmeasured book spread). The real hurdle is whipsaw drag, not exchange fees: `BITC` lagged BTC by 14.00% in 2025 even with institutional CME futures execution ([SEC Form N-CSR](https://www.sec.gov/Archives/edgar/data/1928561/000119312526098141/d87694dncsr.htm)).
- Permitted data: Kraken downloadable daily OHLCVT (`assets.kraken.com`) or Bitstamp daily USD history (`www.bitstamp.net`).
- Repo overlap and verdict: do not register. This directly overlaps our already-running daily trend card `E13` (Plan 75 rebuilt on Binance.US, 10/20/30-day legs, queue row 136).
- Count-first step (if ever revisited after `E13` completes): count exact annual crossover flips and whipsaw flips (exits within 5 calendar days of entry) on Kraken daily BTC/USD and ETH/USD OHLCVT with zero returns computed, to verify whether the sample has enough independent regime flips per decade to reach statistical power.

Rank 2: Low-turnover cooldown / turnover cap ("Monk Mode" deterministic filter from Alpha Arena Season 1.5, [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/))

- Fixed rule: in Alpha Arena Season 1.5, the only prompt change that materially cut losses across all eight models was forcing fewer trades ("Monk Mode" -9.5% combined vs "Situational Awareness" -41.8%, cutting fees from $508 to $3,257 per $10k account in Situational Awareness down to $197 to $1,286 in Monk Mode). Written deterministically, this is not a standalone signal; it is a minimum holding-time / trade-count cap layered onto an existing entry rule.
- Holding period: multi-day to multi-week to keep fee drag below 100 bp/month.
- Cost survival needed: on Kraken Pro (80 to 160 bp round trip), any rule firing more than once or twice a week is mathematically dead without a multi-percent per-trade edge; on Binance.US (4 bp taker fee plus unmeasured spread), turnover still binds through spread and adverse selection.
- Permitted data: Kraken downloadable OHLCVT (`assets.kraken.com`) or Binance.US public quotes once Measurement 134 reports real book spread.
- Repo overlap and verdict: do not register. Cutting turnover reduces losses on bad signals but does not create a positive edge where none exists (Monk Mode still lost money in 7 of 8 accounts).
- Count-first step: none standalone; only measure fill-count reduction inside an already-registered forward card after Measurement 134 finishes.

Rank 3: Exchange-contest AI bots (WEEX AI Hackathon, Bybit WSOT AI Showdown) and high-win-rate leveraged grid/scalping (`tahtrade` on ChainRated)

- Fixed rule: NONE. Neither WEEX nor Bybit publishes entry/exit rules, risk limits, or trade logs, and ChainRated's sole published live Bybit account lost -70.2% across 24,641 trades with 60 liquidations.
- Holding period, cost survival, and permitted data: not applicable because there is no stated rule to rebuild, and high-frequency perp/scalping cannot survive US retail spot fees (Kraken Pro 80 to 160 bp round trip; Binance.US unmeasured thin-book spread) without leverage or maker rebates.
- Verdict: kill / do not register.
- Count-first step: none; do not test unless an operator publishes audited, survivorship-free, full-account trade logs and an exact fixed rule set.

## Verdict

Nothing to register. Do not open a new plan or queue row from Round 73. Keep `E13` and Measurement 134 running unchanged on Binance.US (Measurement 133 is closed unread; `E12` and `E14` also continue unchanged).

## Second Check

Checked 2026-11-27 by directly re-opening all 12 external URLs and checking our live card status in `docs/QUEUE.md`. Zero pages were blocked, zero barred news sites in `AGENTS.md` are cited, and no market prices or returns were pulled.

Tally across 13 checks (12 outside URLs plus 1 repo card-status check): 10 CONFIRMED, 3 CORRECTED, 0 NOT FOUND.

- CONFIRMED: AP/GlobeNewswire WEEX preliminary (788 teams, 1,000 USDT), WEEX finals summary (8 of 37 profitable, top 5 ROIs, 20,251 API calls, +$12,662 trade, $21,977 max drawdown; self-reported by WEEX and marked unreviewed at publication), WEEX champions (`todd`, Bentley package), Bybit WSOT 2026 (1M AI / 3.2M Squad / 2M Individual pools, 1+6 UTA accounts), TradeRank Season 11 leaderboard (1 of 22 at +0.24%), Bitwise SEC Form 485BPOS (10d/20d EMA cash-rotation rule, 0.88%/0.89% net expenses, 0% turnover), Bitwise SEC Form N-CSR (KPMG LLP audited 2025 returns: `BITC` -20.56% / -14.00% vs BTC, `BTOP` -16.00% / -12.27% vs BTC/ETH, `AETH` -0.05% / +11.00% vs ETH), ChainRated `tahtrade` (-70.2%, 24,641 trades, 88.1% win rate, 60 liquidations, 0.81 PF, 79% max DD), Kraken Pro fees (0.40%/0.80%), and Binance.US fees (0.00%/0.02% Tier I).
- CORRECTED (fixed in place above): (1) TradingAgentStack Season 1.5 Situational Awareness fees were $508 to $3,257 per $10k account (not $2,291 to $3,257), while all 31-of-38, Season 1, and Season 1.5 totals are confirmed; (2) TradeRank's settled-seasons wording does not state all 131 model-seasons came strictly from the 10 settled seasons (Seasons 0 to 6 and 8 to 10), and TradeRank and ChainRated figures were relabeled STATED with operator/independence caveats; (3) all four stale "Measurement 133" references were updated to Measurement 134 (Measurement 133 is closed unread). Round 73's no-registration verdict stands.
