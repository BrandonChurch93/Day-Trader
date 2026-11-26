# Brokers and venues: where to trade, what it costs, how to set it up

Last verified: 2026-11-24. Asked by the owner on 2026-11-24.

Scope: a US retail individual in Nampa, Idaho, trading only his own money through his own programs. No account was opened, no key was requested and no order was placed for this research.

How it was made: six researchers each wrote a report from primary pages. Four fresh checkers, on three different models, then re-opened the primary pages for 55 load-bearing figures and tried to prove them wrong. The raw reports and the four check tables are in `docs/research/09_raw/`. This file is the corrected summary. Where a checker changed a figure, this file carries the checker's figure.

Tags: MEASURED means read on the firm's or regulator's own page on the date above, or measured from a public endpoint. STATED means someone's claim, not confirmed on a primary page. UNKNOWN means not found, which is not the same as absent.

Status of everything recommended here: proposed by the research team. Nothing in this file is an owner decision.

## Bottom line

| # | Question | Recommendation | Main reason | What it costs him |
|---|---|---|---|---|
| 1 | Stock and ETF broker | Alpaca, individual account | The only stock broker checked that has all of: a free practice account on the same connection as live, keys that do not force a person to log in again, no account minimum, and the old $25,000 day trading rule already switched off | Free data covers one exchange only. Full data is $99 a month. Personal keys cannot be locked to one address or set to expire |
| 2 | Practice trading, stocks and crypto | Alpaca practice account | One connection covers both. Needs an email only | Practice fills are kinder than real fills. Crypto fees may not be simulated (UNKNOWN) |
| 3 | Live crypto venue | Not chosen yet. Leading candidate is Binance.US. The fallback that needs no crypto account is spot bitcoin and ether funds held in the Alpaca stock account | Binance.US fees are 4 basis points for a round trip against 50 at Alpaca, 160 at Kraken and 180 at Coinbase. For rules that trade weekly, fees decide the result | Binance.US has no practice environment that was found, no numeric reserve report that was found, and a hard regulatory history from 2023 to 2025 |
| 4 | Account type | Individual, in his own name. Not an LLC | An LLC raises data costs and account minimums and adds nothing for trading his own money | None found. Revisit only with a tax professional |
| 5 | Leverage and shorting | Do not use at the start | The $2,000 floor only matters for borrowing. Own-cash trading has no dollar floor at Alpaca | No shorting, no borrowed buying power |

Interactive Brokers is the stock broker to revisit later. Its full real-time data costs $4.50 a month instead of $99, but an individual must log in by hand about daily on one of its connections, or weekly on the other, so it cannot run unattended.

## How much money is needed

| Step | Money needed | Tag | Source |
|---|---|---|---|
| Alpaca practice account | $0. Email sign-up only. Starts with $100,000 of pretend money | MEASURED | [Alpaca paper trading](https://docs.alpaca.markets/docs/paper-trading) |
| Open a live Alpaca account | $0. "No, Alpaca does not require a minimum deposit to fund your account." | MEASURED | [Alpaca minimum deposit](https://alpaca.markets/support/alpaca-minimum-deposit) |
| Smallest stock order | $1 for stocks that allow fractional shares | MEASURED | [Alpaca fractional](https://alpaca.markets/fractional) |
| Day trading stocks with own cash | No dollar floor under the new rules at Alpaca. Under $2,000 the account has 1x buying power | MEASURED | [Alpaca margin docs](https://docs.alpaca.markets/us/docs/margin-and-short-selling) |
| Borrowing or short selling | $2,000 of equity | MEASURED | [FINRA frequent intraday trading](https://www.finra.org/investors/insights/frequent-intraday-trading) |
| Smallest crypto order at Alpaca | $10 on one Alpaca page, $1 on another. Read the minimum from the asset endpoint at run time | MEASURED, pages conflict | [Broker API crypto docs](https://docs.alpaca.markets/us/docs/crypto-trading-1), [coin pair FAQ](https://alpaca.markets/support/alpaca-crypto-coin-pair-faq) |
| Full real-time stock data at Alpaca | $99 a month. Optional | MEASURED | [Alpaca market data plans](https://docs.alpaca.markets/us/docs/about-market-data-api) |
| Interactive Brokers real-time data | $4.50 a month, and needs $500 of equity in the account | MEASURED | [IBKR market data pricing](https://www.interactivebrokers.com/en/pricing/market-data-pricing.php) |
| Alpaca account for an LLC | $30,000 on the account page dated July 2026. A newer comparison table shows $0 for commission-free business accounts. The two pages conflict | MEASURED, pages conflict | [Alpaca account plans](https://docs.alpaca.markets/us/docs/account-plans) |

The owner's own starting amount is still an open owner number. The keys `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd` and `live_max_total_loss_usd` in `config/thresholds.yaml` carry a recommendation only.

The data bill, not the broker minimum, sets the practical floor for intraday stock trading. This is arithmetic from the prices above, not a forecast:

| Account size | $99 a month as a share of the account per year | $4.50 a month as a share of the account per year |
|---|---|---|
| $1,000 | 118.8% | 5.4% |
| $5,000 | 23.8% | 1.1% |
| $10,000 | 11.9% | 0.5% |
| $25,000 | 4.8% | 0.2% |
| $50,000 | 2.4% | 0.1% |

So on a small account, rules that need the full real-time feed cannot pay for it. Rules that trade on daily bars do not need it: on the free plan, full-market history is available as long as the request ends at least 15 minutes ago ([Alpaca market data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq), MEASURED). This supports starting with multi-day rules.

## The day trading rule

- FINRA replaced the pattern day trader rule and its $25,000 minimum with intraday margin standards. Effective June 4, 2026. Brokers may phase in until October 20, 2027. MEASURED. [FINRA Notice 26-10](https://www.finra.org/rules-guidance/notices/26-10)
- $2,000 of equity is still needed to trade with borrowed money. MEASURED. [FINRA frequent intraday trading](https://www.finra.org/investors/insights/frequent-intraday-trading)
- Alpaca switched on June 4, 2026: "We have officially lifted the Pattern Day Trader rule". MEASURED. [Alpaca announcement](https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/)
- tastytrade also switched on June 4, 2026. MEASURED. [tastytrade support](https://support.tastytrade.com/support/s/solutions/articles/43000435180)
- Interactive Brokers: "your account may still be subject to the pattern day trading (PDT) rules during the implementation period". MEASURED. [IBKR FAQ](https://www.interactivebrokers.com/support/faq/articles/30120575)
- Tradier: its support page still describes the old rule, and its June 5, 2026 blog describes the industry change without saying Tradier has switched. UNKNOWN whether it has. [Tradier support](https://support.tradier.com/what-are-the-pattern-day-trading-rules-that-apply-to-margin-accounts), [Tradier blog](https://blog.tradier.com/blog/the-pattern-day-trader-pdt-rule-is-gone-what-active-traders-need-to-know)
- Cash accounts at other brokers have no day trading dollar floor, but each purchase must be paid with settled money, and most stock trades settle the next business day. MEASURED. [FINRA frequent intraday trading](https://www.finra.org/investors/insights/frequent-intraday-trading)

## Stock brokers compared

All four firms in the first table list Idaho on FINRA BrokerCheck. MEASURED. Links to each firm's BrokerCheck file are in `09_raw/stock_api_brokers.md`.

| Item | Alpaca | Interactive Brokers Pro | Tradier | tastytrade |
|---|---|---|---|---|
| Account minimum | $0 | $0. Lite accounts cannot use the API | $0 | $0 |
| Stock commission | $0. Alpaca is paid for order flow | Fixed: $0.005 a share, $1.00 minimum per order. Tiered: $0.0035 a share, $0.35 minimum | $0 plus $0.35 a trade on Lite, or $10 a month on Pro | $0 plus $0.0008 a share clearing fee |
| Real-time data | Free plan: IEX exchange only, 30 streaming symbols. Full feed $99 a month | $4.50 a month for all three US networks, needs $500 equity | Included. Whether it is the full consolidated feed is UNKNOWN | Included. Exact coverage UNKNOWN |
| Practice environment | Free, email only, same connection, separate keys | Only after a live Pro account is open and funded | Sandbox with 15-minute delayed data | Sandbox that resets every day |
| Unattended login | Keys do not expire. No forced login | Individuals must log in by hand: daily on the web gateway, weekly on the desktop gateway | Token does not expire | Refresh grant does not expire |
| Duplicate order protection | A repeated order ID is rejected with HTTP 422 while the first order is active | Order ID must be unique for 24 hours | Not deduplicated (STATED) | "The API does not deduplicate retried submissions" |
| Old day trading rule | Switched off June 4, 2026 | May still apply to an account | UNKNOWN | Switched off June 4, 2026 |
| Key limits | No expiry, no trade-only setting, no address lock found for personal keys. Keys cannot move cash, and the crypto withdrawal endpoint was removed in October 2026 | No scoped keys for individuals | Token gives full account access | Read and trade scopes. No address lock found |
| Recent enforcement | SEC, September 24, 2024: censure and $400,000 for not keeping staff messages | Not researched in depth | FINRA, March 2, 2026: $75,000, complaint reporting | FINRA, July 21, 2026: $850,000, best-execution reviews |
| Protection | SIPC $500,000 including $250,000 cash, plus an excess policy | SIPC | SIPC through Apex | SIPC through Apex |

Sources for this table, all MEASURED unless marked: [Alpaca paper trading](https://docs.alpaca.markets/docs/paper-trading), [Alpaca market data plans](https://docs.alpaca.markets/us/docs/about-market-data-api), [Alpaca Form CRS](https://files.alpaca.markets/disclosures/library/FormCRS.pdf), [Alpaca common API errors](https://alpaca.markets/learn/how-to-fix-common-trading-api-errors-at-alpaca), [Alpaca key security guide](https://alpaca.markets/learn/api-key-security-best-practices-for-alpaca-builders), [Alpaca crypto withdrawal removal](https://docs.alpaca.markets/us/changelog/2026-10-22-crypto-withdrawals-276facd), [SEC order against Alpaca](https://www.sec.gov/files/litigation/admin/2024/34-101137.pdf), [IBKR Lite API FAQ](https://www.interactivebrokers.com/support/faq/content/use-api-ibkr-lite-account-76128095), [IBKR commissions](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php), [IBKR market data pricing](https://www.interactivebrokers.com/en/pricing/market-data-pricing.php), [IBKR manual login](https://www.interactivebrokers.com/support/faq/content/automate-web-api-authentication-process-629305686), [IBKR weekly login](https://www.interactivebrokers.com/docs/third-party-integrations/tws-settings/daily-weekly-reauthentication), [Tradier pricing](https://tradier.com/pricing), [tastytrade retries](https://developer.tastytrade.com/docs/guides/idempotency-and-retries/), [tastytrade fees](https://support.tastytrade.com/support/s/solutions/articles/43000435233).

Household-name brokers, for an unattended program:

| Broker | Usable? | Why | Tag |
|---|---|---|---|
| Public.com | Yes, with care | $0 minimum, official program access, keys that renew by themselves. No practice mode: "All orders are live. There is no paper trading mode." Public says it accepts payment for order flow on program trades | MEASURED. [Public guide](https://public.com/learn/trade-stocks-options-crypto-using-claude), [Public on order flow](https://help.public.com/en/articles/4847508-public-s-approach-to-pfof) |
| Webull | Yes, with care | Practice environment and official Python kit. Real-time data for programs is a paid extra. FINRA fined it $4.2 million in November 2026 for anti-money-laundering and best-execution failures | MEASURED. [FINRA release](https://www.finra.org/media-center/newsreleases/2026/finra-fines-webull-42-million-anti-money-laundering-and-best) |
| moomoo | Yes, with care | Practice for stocks, not crypto. Can be moved to per-share fees | STATED, not re-checked |
| TradeStation | Only with $10,000 | $10,000 minimum for program access | STATED, not re-checked |
| Charles Schwab | No | Login must be renewed by hand every 7 days, and no practice mode for programs. The current page needs a sign-in to read, so this rests on Schwab's 2024 documentation | STATED |
| E*TRADE | No | Login expires every night | STATED, not re-checked |
| Fidelity | No | No program access for retail accounts | STATED, not re-checked |
| Robinhood | No for this design | No stock order connection for programs. Its product is a tool for AI agents on a separate account, with trade approvals off by default for outside agents | MEASURED. [Robinhood agent trading](https://robinhood.com/us/en/support/articles/trading-with-your-agent/) |
| TradeZero | No | Its terms exclude fully unattended systems | STATED, not re-checked |

## Crypto venues compared

Every venue in this table accepts Idaho residents. Fees are for the lowest tier, which is where a small account sits. A round trip is one buy plus one sell. A taker order takes a price already in the book. A maker order rests in the book and waits.

| Venue | Maker | Taker | Round trip, both taker | Round trip, both maker | Tag and source |
|---|---|---|---|---|---|
| Binance.US, BTC/USD and ETH/USD | 0% | 0.02% | 4 bps | 0 bps | MEASURED. [Binance.US fees](https://www.binance.us/fees) |
| Interactive Brokers crypto | 0.18% | 0.18% | 36 bps, with a $1.75 minimum per order capped at 1% | same | MEASURED. [IBKR crypto commissions](https://portal.interactivebrokers.com/en/pricing/commissions-cryptocurrencies.php) |
| Alpaca | 0.15% | 0.25% | 50 bps | 30 bps | MEASURED. [Alpaca crypto fees](https://docs.alpaca.markets/us/docs/crypto-fees) |
| OKX US | 0.20% | 0.35% | 70 bps | 40 bps | MEASURED. [OKX US fees](https://www.okx.com/en-us/help/updates-to-us-fee-framework-2026) |
| Kraken Pro, with $20,000 held there or $10,000 of monthly volume | 0.22% | 0.38% | 76 bps | 44 bps | MEASURED. [Kraken Pro fees](https://www.kraken.com/pro/fees) |
| Crypto.com Exchange | 0.25% | 0.50% | 100 bps | 50 bps | MEASURED. [Crypto.com fees](https://crypto.com/exchange/document/fees-limits) |
| Kraken Pro, entry tier | 0.40% | 0.80% | 160 bps | 80 bps | MEASURED. [Kraken Pro fees](https://www.kraken.com/pro/fees) |
| Coinbase Advanced, entry tier | 0.50% | 0.90% | 180 bps | 100 bps | MEASURED. [Coinbase announcement, September 16, 2026](https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced) |
| Robinhood crypto API, version 2 | 0.95% charged on every order today | 0.95% | 190 bps | 190 bps | MEASURED. [Robinhood crypto fee schedule](https://cdn.robinhood.com/assets/robinhood/legal/rhc-fee-schedule.pdf) |
| Gemini ActiveTrader | 0.60% | 1.20% | 240 bps | 120 bps | MEASURED. [Gemini fee schedule](https://www.gemini.com/fees/activetrader-fee-schedule) |

Correction recorded here: the research reports used Coinbase's separate Exchange product (0.40% and 0.60%) as a stand-in for Coinbase Advanced. A checker found Coinbase's own announcement, and the true entry rates are higher. The stand-in figures are not used anywhere in this file.

What fees do to a rule over a year. Crypto fees are a percentage, so account size does not shrink them. How often the rule trades does. This is arithmetic, with every round trip filled as a taker, and it leaves out the spread:

| Venue | One round trip a month | One a week | One a day |
|---|---|---|---|
| Binance.US | 0.5% of the account a year | 2.1% | 14.6% |
| Alpaca | 6.0% | 26.0% | 182.5% |
| Kraken, entry tier | 19.2% | 83.2% | 584.0% |
| Coinbase Advanced, entry tier | 21.6% | 93.6% | 657.0% |
| Gemini | 28.8% | 124.8% | 876.0% |

Other facts that decide the choice:

| Item | Binance.US | Alpaca | Kraken | Coinbase Advanced |
|---|---|---|---|---|
| Idaho | Yes. Idaho licence MTL-306. US dollar bank transfers supported and free | Yes | Yes. Only Maine and New York are excluded | Yes. Idaho licence MTL-169 |
| Key that can trade but not withdraw | Yes | Keys cannot move cash. Crypto withdrawal by key was removed in October 2026 | Yes | Yes. View and Trade without Transfer |
| Key locked to chosen addresses | Yes | Not found for personal keys | Yes | Yes |
| Separate pot for the program | Not found | Not for individuals | Not for individuals. Spot sub-accounts are for managed institutional clients | Yes. A key can be tied to one portfolio |
| Practice environment | A test-order check that does not simulate fills. No practice exchange found | Yes, the practice account covers crypto | Practice trading on live prices in its official command line tool | Static canned responses only |
| Official Python kit | Not found | Yes | Not yet. Official Go and Rust | Yes |
| Reserve evidence | A statement that holdings are 1 to 1, and a controls audit. No numeric reserve report found | Custody statement. No reserve report found | Reserve report dated September 30, 2026: bitcoin 103.2%, ether 100.7% | Custody statement. No reserve report found |
| Regulatory history | SEC sued in June 2023. A joint filing to dismiss with prejudice was made May 29, 2025. The 2023 criminal plea was by Binance Holdings, the foreign parent. Dollar transfers were lost and came back in 2025 | Sister firm's 2024 SEC record-keeping order | SEC case dismissed in 2025 | SEC case dismissed in 2025. Data breach in May 2025 |
| Bank deposit hold | Tradable at once. Cannot withdraw for 7 days | Up to $3,000 tradable at once | Tradable at once. Cannot withdraw for 7 days | Varies by account |

Sources for this table, all MEASURED: [Binance.US supported states](https://support.binance.us/en/articles/9842798-list-of-supported-and-unsupported-states-and-regions), [Binance.US key setup](https://support.binance.us/en/articles/9842800-how-to-create-an-api-key-on-binance-us), [Binance.US API docs](https://docs.binance.us/), [Binance.US trust page](https://www.binance.us/trust), [SEC litigation release](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26316), [Binance.US bank transfers](https://support.binance.us/en/articles/10197427-how-to-link-a-bank-account-deposit-via-ach), [Kraken key permissions](https://docs.kraken.com/exchange/guides/rest/api-keys), [Kraken account FAQ](https://support.kraken.com/articles/account-management-faq), [Kraken bank deposits](https://support.kraken.com/articles/8795459449492-how-do-i-fund-my-account-with-usd-using-ach-via-plaid-), [Coinbase key setup](https://docs.cdp.coinbase.com/coinbase-business/authentication-authorization/api-key-authentication), [Alpaca key security guide](https://alpaca.markets/learn/api-key-security-best-practices-for-alpaca-builders), [Alpaca funding guide](https://alpaca.markets/learn/fund-live-trading-account). Kraken's reserve figures and both "dismissed in 2025" entries come from `09_raw/crypto_major_venues.md` and the check tables.

Two claims in this table say something was not found. Nobody can prove a thing does not exist. Treat "not found" as UNKNOWN until it is tested with an account.

Do not build on these:

- Bitstamp USA. US retail accounts become close-only on February 1, 2027. MEASURED. [Bitstamp migration FAQ](https://www.bitstamp.net/faq/moving-from-bitstamp-by-robinhood-to-robinhood/)
- Bybit, KuCoin, MEXC and the Hyperliquid interface. Their own terms bar US residents. MEASURED. Links in `09_raw/crypto_other_venues.md`. Never work around a venue's country rules.

### The route that needs no crypto account

Spot bitcoin and ether funds trade like stocks in the Alpaca account.

- BlackRock's IBIT and ETHA each charge a 0.25% yearly sponsor fee. MEASURED. [IBIT](https://www.ishares.com/us/products/333011/ishares-bitcoin-trust), [ETHA](https://www.ishares.com/us/products/337614/)
- Stock commission at Alpaca is $0, so the trading cost is the spread.
- They sit in a stock account, so stock account protection and stock tax forms apply. The stock wash sale rule applies to them.
- They do not trade on weekends. A rule cannot act on a Saturday move until the market opens. How much that hurts a multi-day rule is a question for the replay test, not for opinion. UNKNOWN until measured.
- Only bitcoin and ether, and a few other coins with funds. No small coins.

### Measured: what the order book adds on top of fees

Method: the public order books of four venues were read without an account, once about every 30 seconds, and the cost of buying then at once selling a fixed dollar amount was worked out from the resting orders. This is one quiet window late on a Tuesday night US time. It says nothing about busy or stressed markets. Alpaca's crypto book is not in this table.

Window: 61 samples per pair, 06:19 to 06:49 UTC on 2026-11-25 (late evening of November 24 in Idaho). Figures are basis points of the amount traded, for buying and at once selling: median, with the 90th percentile in brackets. MEASURED by us.

| Venue | Pair | Quoted spread | $100 round trip | $1,000 round trip | $10,000 round trip |
|---|---|---|---|---|---|
| Binance.US | BTC/USD | 0.00 (0.10) | 0.40 (0.83) | 1.29 (1.81) | 2.97 (3.72) |
| Binance.US | BTC/USDT | 0.04 (0.07) | 0.04 (0.77) | 0.66 (1.22) | 2.01 (2.58) |
| Binance.US | ETH/USD | 0.30 (0.66) | 0.95 (1.30) | 1.21 (1.86) | 3.05 (3.56) |
| Gemini | BTC/USD | 1.33 (2.40) | 1.33 (2.40) | 1.34 (2.44) | 3.57 (4.17) |
| Gemini | ETH/USD | 0.06 (0.06) | 0.06 (0.06) | 0.06 (0.30) | 1.15 (2.04) |
| Kraken | BTC/USD | 0.02 (0.02) | 0.02 (0.16) | 0.05 (1.12) | 0.23 (1.43) |
| Kraken | ETH/USD | 0.06 (0.84) | 0.06 (1.09) | 0.06 (1.30) | 0.66 (1.77) |

Coinbase was measured in the same window and its book was among the deepest of the four. Its figures are left out of this file because Coinbase's [market data terms](https://www.coinbase.com/legal/market_data) (last updated February 6, 2023) bar passing on work derived from its data to third parties, and this repo is public. The owner has them in the project thread.

A second, separate measurement by the practice-environment researcher the same evening agrees: under about 2 basis points per side for $1,000 to $10,000 on these venues, and about 4 to 5 basis points per side on Alpaca's own crypto book before its fee (`docs/research/10_raw/practice_environments.md`).

What it shows: at the sizes this project would trade, the book costs a few basis points at most on every venue. Binance.US has the thinnest book of the four, but the gap is small beside the fee gap. Fees, not spreads, separate these venues for a small account. The raw sample rows were taken out of the repo on 2026-11-26 under the data terms rule in AGENTS.md and are kept privately.

## Which are best to use with AI

This project's proposed design has fixed rules placing the orders and AI building, researching and reviewing. For that design the things that matter are a real practice environment, complete machine-readable documentation, an official Python kit, protection against duplicate orders, and keys that work unattended.

| Rank | Firm | Why |
|---|---|---|
| 1 | Alpaca, for stocks | All five. Also publishes documentation written for AI coding agents |
| 2 | Kraken, for crypto | Scoped keys, address lock, practice trading on live prices. No official Python kit yet. Entry fees are high |
| 3 | Coinbase, for crypto | Official Python kit, scoped keys, one-portfolio keys. Practice mode returns canned data only. Entry fees are high |
| Low | Binance.US | Cheapest by far, but no AI tooling, no practice exchange found, no official Python kit found. More of the connection must be written and tested by hand |
| Not usable unattended | Interactive Brokers, Schwab, E*TRADE | Forced manual logins |

Ten of the twelve firms checked now offer an official tool that lets an AI agent place trades directly. The defaults differ a lot. MEASURED on each firm's own pages. Details and links are in `09_raw/ai_integration.md`.

- Kraken's tool leaves trading and funding switched off until asked.
- Alpaca's tool defaults to the practice account.
- tastytrade's tool defaults to the live account.
- Robinhood's trade approvals are off by default for outside agents.
- Interactive Brokers lets an agent trade alone only inside a cash-only pot. The pot is capped at 10% of the account, between $1,000 and $25,000, as a lifetime total that losses do not reset. Margin accounts, Lite accounts and LLC accounts are not eligible. Ten approved trades on at least three separate days come first. [IBKR AI integrations](https://brokerage.ibkr.com/en/trading/ai-integrations.php)

What the model makers allow:

| Provider | Rule, quoted | In force | Source |
|---|---|---|---|
| Anthropic | Treats "a personalized recommendation to buy, sell, hold, or allocate among specific investment products" as high risk needing review by a qualified person. Outside that: "Internal drafting, research, summarization, or analysis that is not the ultimate High-risk AI Recommendation delivered" and "Carrying out a decision a person has already made, or applying a fixed rule, formula, or algorithm where the model exercises no judgment about the individual" | November 12, 2026 | [Anthropic usage policy](https://www.anthropic.com/legal/aup) |
| OpenAI | Prohibits "automation of high-stakes actions in sensitive areas without human review", and lists "financial activities and credit" | November 20, 2026 | [OpenAI usage policies](https://openai.com/policies/usage-policies) |
| Perplexity, today | Prohibits use to "Make automated decisions about individuals that materially impact them (e.g., decisions regarding their employment, healthcare, finances, housing or insurance)". No human-oversight exception in this version | July 8, 2025 | [Perplexity policy, current version](https://www.perplexity.ai/hub/legal/aup-prior-2025-07-08) |
| Perplexity, next | Prohibits use to "Make high-risk or consequential automated decisions ... without human oversight", including "finances or credit" | January 1, 2027 | [Perplexity policy, next version](https://www.perplexity.ai/hub/legal/aup) |

Correction recorded here: the research quoted the Perplexity wording that takes effect on January 1, 2027 as if it were in force. The version in force today is stricter. How these rules apply to a model making calls in a practice account, where no money moves, is not stated by any provider. UNKNOWN.

## Sign-up, step by step

Timelines below are the firms' own statements, not a forecast.

Alpaca ([US sign-up guide](https://alpaca.markets/learn/live-trading-account-us-resident), MEASURED unless marked):

1. Sign up with an email and turn on two-step login. This creates the practice account only. Up to 3 practice accounts and 1 live account.
2. Apply for the live individual account. Needs: US tax residence, age 18 or over, Social Security number, a government photo ID, a live selfie, address, employment and a financial profile. It asks about ties to a broker, to a public company, and to political office.
3. Wait for approval. Alpaca's guide gives no time. A staff forum reply says "Generally, live accounts take 24 hours to be reviewed." STATED. [Alpaca forum](https://forum.alpaca.markets/t/account-taking-longer-than-usual-to-approve/3627)
4. Link a bank and deposit. "up to 3000 USD may be made available instantly". An older page says under $1,000. The $3,000 page is newer. [Funding guide](https://alpaca.markets/learn/fund-live-trading-account)
5. Create the live keys in the dashboard. They are separate from the practice keys and point at a separate address.
6. Money put in by bank transfer cannot be taken out again for about six business days on one page and 5 to 10 on a newer disclosure. [Alpaca funding FAQ](https://alpaca.markets/support/deposits-and-withdraws-faqs)

Crypto venues (MEASURED, links in `09_raw/account_setup_and_rules.md` and `09_raw/crypto_other_venues.md`):

- Binance.US: email and phone check, then identity check with the last four digits of the Social Security number and a home address. Keys are made under API Management with two-step confirmation. Start with read and spot trading only, withdrawals off, and lock the key to the server's address.
- Kraken: Intermediate level needs Social Security number, ID and proof of address. "Verification processing times can take up to 45 minutes for Intermediate level".
- Coinbase: US photo ID. "you'll typically receive notification of the review status within 4 hours."

## Keeping it legitimate

Registration. Trading only his own money does not make him an investment adviser, a commodity trading adviser or a money transmitter. Each of those definitions needs advising others, or handling other people's money. MEASURED on the statute and ruling texts: [SEC on investment advisers](https://www.sec.gov/resources-small-businesses/capital-raising-building-blocks/investment-advisers), [Idaho Code 30-14-102](https://legislature.idaho.gov/statutesrules/idstat/title30/t30ch14/sect30-14-102/), [7 USC 1a](https://www.law.cornell.edu/uscode/text/7/1a), [FinCEN ruling FIN-2014-R002](https://www.fincen.gov/resources/statutes-regulations/administrative-rulings/application-fincens-regulations-virtual/). This changes the moment he trades for anyone else, pools money, or sells signals. A securities lawyer is needed before any of those.

Taxes. A tax professional who works with active traders is needed for the first three rows.

| Topic | What the source says | Tag | Source |
|---|---|---|---|
| Trader tax status | The default is investor. Trader status needs substantial, regular, continuous trading that seeks profit from daily price moves | MEASURED | [IRS Topic 429](https://www.irs.gov/taxtopics/tc429) |
| Mark-to-market election | Must be made by the due date, without extensions, of the return for the year before it takes effect. For 2027 that is April 15, 2027. It turns gains and losses into ordinary income and removes the capital loss limit and the wash sale rule | MEASURED rule. The date is the rule applied to a calendar-year filer | [IRS Topic 429](https://www.irs.gov/taxtopics/tc429) |
| Does that election cover crypto? | The IRS page speaks of securities. Not settled | UNKNOWN | Ask the tax professional |
| Short-term gains | Held a year or less: taxed at ordinary rates | MEASURED | [IRS Topic 409](https://www.irs.gov/taxtopics/tc409) |
| Capital loss limit | $3,000 a year against other income | MEASURED | [IRS Publication 550](https://www.irs.gov/publications/p550) |
| Stock wash sales | A loss is disallowed if the same stock is bought within 30 days before or after. Counts all his accounts, a spouse's and an IRA. A broker cannot see all of that, so the program's own ledger must | MEASURED | [IRS Publication 550](https://www.irs.gov/publications/p550) |
| Crypto wash sales | The rule covers "shares of stock or securities". Congress's tax staff write that digital assets "are not expressly within the scope". A bill to change this, H.R. 10357, was ordered reported by committee 38 to 5 on September 16, 2026 and is not law. Shares of a spot fund are securities and are covered today | MEASURED | [26 USC 1091](https://uscode.house.gov/us/usc/t26/s1091/), [H.R. 10357](https://www.congress.gov/bill/119th-congress/house-bill/10357/all-actions) |
| Crypto tax form | Venues report sale proceeds on Form 1099-DA. Cost basis must be reported only for coins bought after 2025 and kept at that venue. He must keep his own basis records for everything else | MEASURED | [IRS 1099-DA instructions](https://www.irs.gov/instructions/i1099da) |
| Idaho | Flat 5.3% on the Tax Commission's page for 2025. Idaho's capital gains deduction does not cover stocks | MEASURED | [Idaho Tax Commission](https://tax.idaho.gov/wp-content/uploads/forms/EIN00046/EIN00046_03-02-2026.pdf), [Idaho capital gains](https://tax.idaho.gov/taxes/income-tax/individual-income/popular-credits-and-deductions/capital-gains/) |

Market conduct. These apply to him as well as to firms. The program needs controls so it cannot create these patterns by accident. Rule texts and links are in `09_raw/account_setup_and_rules.md` section 6.

- No orders placed with the intent to cancel them before they fill. No stacking orders on one side to move the price.
- No trading with himself. Two rules in one account must not take each other's orders.
- Limits on order size, distance from the market price, open order count, duplicates and request rate.
- A reason logged for every cancel.

Honest account forms. Alpaca's application asks about employment and affiliations. Answer them as they are.

## What the fresh check changed

55 figures were checked. Each of the two claim files went to two checkers on different models.

| Outcome | Count | Which |
|---|---|---|
| Held with both checkers | 38 | |
| Wrong | 1 | Coinbase Advanced entry fee. Corrected above |
| Overstated or missing a material detail | 12 | Alpaca duplicate order behaviour, Alpaca LLC minimum, Alpaca deposit timings, Public.com order flow, IBKR AI pot limits, Perplexity policy date, SEC and Binance dismissal wording, Kraken sub-accounts, Alpaca crypto order limits, IBKR crypto fee detail, crypto wash sale wording, 1099-DA basis wording. All corrected above |
| Not found in any source | 3 | Alpaca personal key controls, Binance.US practice environment and Python kit, Binance.US reserve report. Carried as UNKNOWN or "not found" |
| Could not be opened | 1 | Schwab's current login rule, which sits behind a sign-in. Carried as STATED |

The four check tables are in `docs/research/09_raw/check/`.

## Still unknown

- Whether Alpaca's practice account simulates crypto fees.
- Whether Alpaca personal keys can be limited in any way beyond what is documented.
- Binance.US: practice environment, reserve figures, and how it behaves in a stressed market.
- Coinbase Advanced: the full tier table, which shows only after sign-in.
- Alpaca's exact crypto order minimum and maximum for a personal account.
- Real fill quality at Alpaca on small stock orders.
- Whether the mark-to-market election can cover crypto.
- How provider rules treat a model making calls in a practice account.

## Must measure ourselves

- Order book cost on each crypto venue across busy and stressed hours, not one quiet window.
- Practice fills against real fills at our sizes, once a live account exists.
- The cost of losing weekends if crypto is held through spot funds, in the replay test.
