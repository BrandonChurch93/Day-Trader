# Claims to check: stock brokers and AI

S1. Alpaca has no minimum account size or deposit for an individual US account.
S2. Alpaca paper trading is free, needs only an email sign-up (no funding), uses the same API as live with separate keys, and starts with $100,000 of pretend money. Paper trading also covers crypto.
S3. Alpaca's free market data plan (Basic) gives real-time data from the IEX exchange only. The full consolidated feed from all US exchanges (SIP) is the Algo Trader Plus plan at $99 a month.
S4. On the free Basic plan, historical consolidated (SIP) bars are available except for the most recent 15 minutes.
S5. Alpaca switched to FINRA's new intraday margin rules on June 4, 2026: no pattern day trader designation, no $25,000 minimum. $2,000 equity is needed for leverage and short selling. Below $2,000 the account has 1x buying power.
S6. Alpaca US stock and ETF trades through the Trading API are commission-free, and Alpaca receives payment for order flow.
S7. Alpaca Trading API: 200 requests per minute per account. An order sent with a client_order_id that was already used is rejected (state the exact behaviour and status code if documented).
S8. Alpaca individual Trading API keys do not expire. State whether an individual key can be restricted (trade-only, IP allowlist) and whether the Trading API can withdraw cash or crypto at all.
S9. SEC order of September 24, 2024 against Alpaca Securities: censure and $400,000 penalty (state what it was for).
S10. Alpaca business (LLC) accounts need a $30,000 minimum deposit.
S11. Alpaca fractional share orders start at $1.
S12. Interactive Brokers: the API is not available on IBKR Lite accounts.
S13. Interactive Brokers: an individual (retail) client using the Web API must log in by hand through the Client Portal Gateway, the session lasts at most about 24 hours, and automated login (OAuth) is not offered to ordinary individual accounts. TWS or IB Gateway needs a daily restart and a fresh login about weekly.
S14. Interactive Brokers non-professional real-time US stock data costs $1.50 a month each for NYSE (Network A), Network B and Nasdaq (Network C), $4.50 together, and needs $500 of account equity. The same three for a professional (which includes any LLC) cost $95 a month.
S15. IBKR Pro stock commissions: Fixed $0.005 per share with a $1.00 minimum per order; Tiered $0.0035 per share with a $0.35 minimum.
S16. FINRA Regulatory Notice 26-10: new intraday margin standards replace the pattern day trader rules and the $25,000 minimum, effective June 4, 2026, with a broker phase-in that ends October 20, 2027. $2,000 remains the minimum equity for leveraged trading.
S17. Interactive Brokers says an account may still be subject to pattern day trader rules during the phase-in.
S18. Tradier's support site still describes the old pattern day trader rule ($25,000, 3 day trades in 5 days) and Tradier has not said in writing that it has switched.
S19. Charles Schwab individual Trader API: the refresh token expires after 7 days and needs a manual browser login to renew; there is no paper trading through the API.
S20. Public.com's trading API has no paper or sandbox environment (all orders are live), has a $0 minimum, and stock trades are $0 commission with an optional $0.003 per share route that avoids payment for order flow.
S21. Robinhood has no official REST API for stock trading by retail customers; its official product for programmatic stock trading is an MCP server for AI agents with a separate agentic account, where trade approvals are off by default for external MCP clients.
S22. tastytrade's API does not deduplicate retried order submissions (no idempotency).
S23. Interactive Brokers Autonomous Trading: an AI agent can trade without per-order confirmation inside a separate cash-only "AI Partition"; transfers into it are capped (stated as 10% of equity, minimum $1,000, maximum $25,000); the client must first have 10 qualifying trades over two weeks.
S24. Anthropic Usage Policy (state its effective date): treats a personalised recommendation to buy or sell specific investments as high-risk needing human review, and excludes from that (a) internal research and analysis that is not the final recommendation and (b) carrying out a decision a person already made or applying a fixed rule where the model exercises no judgment.
S25. OpenAI usage policies prohibit automating high-stakes financial actions without human review; Perplexity's Acceptable Use Policy prohibits high-risk automated decisions about finances without human oversight. Quote the exact text and dates.
S26. Alpaca instant ACH: how much of a deposit is tradable at once ($1,000 or $3,000; two Alpaca pages are said to disagree). Withdrawal hold of six business days on ACH deposits.
S27. Webull: FINRA fined Webull $4.2 million on or about November 4, 2026.
