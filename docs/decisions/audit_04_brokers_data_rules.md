# Audit of `docs/playbook/04_brokers_data_rules.md`

Audited against: `docs/research/04_brokers_data_compliance.md`
Audit date: 2026-11-24

## Spot-Verification of 3 Load-Bearing Claims (via `fetch_url`)

- PASS: FINRA RN 26-10 (`https://www.finra.org/sites/default/files/2026-04/Regulatory-Notice-26-10.pdf`) confirms effective date June 4, 2026, broker phase-in until October 20, 2027, and full replacement of the day-trade-count test and $25,000 PDT minimum.
- PASS: Alpaca Market Data API (`https://docs.alpaca.markets/us/docs/about-market-data-api`) confirms Basic free tier is IEX only, 30 WebSocket symbols, 200 historical calls/min, and Algo Trader Plus (all US exchanges / SIP) is $99/month.
- PASS: IRS 2026 inflation adjustments (`https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill`) confirms 2026 single-filer brackets of 24% over $105,700 and 32% over $201,775.

## Findings

### 1. [BLOCKER] Dropped operational-safety gotchas on IBKR AI Partition, Robinhood MCP, and browser-login agents (money safety)
Report §7 (line 100) notes that revoking IBKR AI Partition access does NOT cancel pending orders, §1 (line 26) notes Robinhood external-agent MCP accounts have trade approvals OFF by default, and §1 (line 32) warns that linking browser-based agents to a regular IBKR login gives full unrestricted account control. Leaving these out risks an operator assuming revocation flattens exposure or expecting manual approval prompts.

Suggested replacement for `## Rules for the build` bullet 7 (line 16):
```markdown
- Fund live bots only via a dedicated account or sub-account (Robinhood MCP account — approvals OFF by default; IBKR AI Partition — revoking access does not cancel open orders; single-portfolio Coinbase key). [MEASURED] (research §1, §7)
```
And add to `## Do not do` (or fold into bullet 3):
```markdown
- Do not link browser-based agents to a regular broker login (gives unrestricted account control) or enable withdraw/transfer/add-withdrawal-address on bot keys.
```

### 2. [FIX] Overstated evidence tag and wrong section pointer on deterministic risk limits (line 13)
Line 13 cites `(research §5)` and tags the entire engineering rule `[MEASURED]`. In the report, §5 only covers legal rules on spoofing/layering and wash/self-trades; the deterministic risk controls (max daily loss, max orders/minute, max notional per symbol) come from §7 and Implications #3 as engineering recommendations, not measured primary facts.

Suggested replacement for line 13:
```markdown
- Enforce in code: max daily loss, max orders/minute, max notional per symbol, cancel-to-fill cap, and self-trade prevention across all agents (spoofing/self-trade rules are MEASURED; limits are recommended controls). [STATED] (research §5, §7)
```

### 3. [FIX] Dropped build rule on free IEX feed limitations and survivorship bias (research §3)
The Key numbers table notes IEX is about 4% of US equity volume, but the playbook drops the report's core build implication (§3 line 67 and Recommended stacks (b)): free IEX is misleading for spread, volume, and breakout signals and must be upgraded to SIP ($99/mo) before relying on those signals. It also omits survivorship bias in cheap/free historical feeds (§3 line 68).

Suggested replacement for `## Rules for the build` bullet 8 (line 17) (combining both paper/backtest data caveats tightly):
```markdown
- Add modeled fees and slippage to every paper fill, treat free IEX data as plumbing-only (upgrade to $99/mo SIP before trading spread/volume/breakout signals), and check for survivorship bias in historical data. [STATED] (research §3, Recommended stacks)
```

### 4. [FIX] Dropped hard Section 475(f) election deadline (2027-04-15), IRA wash-sale risk, and Form 1099-DA basis caveat (tax/money safety)
Report §6 (lines 90, 93, 94) establishes three actionable tax constraints omitted from the playbook: (1) Section 475(f) mark-to-market election for 2027 is due by April 15, 2027 (hard statutory deadline); (2) stock wash sales apply across IRA/Roth IRA accounts; (3) Form 1099-DA applies to crypto sold after 2025, and brokers may not report cost basis using your acquisition data.

Suggested replacement for `## Rules for the build` bullet 9 (line 18):
```markdown
- Log every stock and crypto fill (time, venue, lot, fees) for cross-account/IRA wash sales, Form 8949, and Form 1099-DA (brokers may omit basis); evaluate any 2027 Section 475(f) election with a CPA before 2027-04-15. [MEASURED] (research §6)
```

### 5. [NOTE] Slight precision omissions in Key numbers table (lines 25, 31)
- Line 25 (`Alpaca free data`): `200 calls/min` applies specifically to historical API calls/min (and SIP history is restricted for the latest 15 minutes).
- Line 31 (`IBKR Autonomous AI limits`): Report §1 (line 32) specifies `10 human-approved trades over two weeks` and `stocks and equity options only` (no crypto, no fractional).

Suggested replacement for line 31:
```markdown
| IBKR Autonomous AI limits | Cash only, stocks/options only, no shorts/fractional, day orders only, 10 human-approved trades over 2 weeks | 2026-11 | MEASURED | [IBKR AI integrations](https://portal.interactivebrokers.com/en/trading/ai-integrations.php) |
```

### 6. [NOTE] Minor tag precision on key-hygiene rule (line 14)
Report §7 (line 101) qualifies key hygiene as `MEASURED for vendor features` (e.g., Coinbase scopes, Kraken withdrawal warnings), whereas "one key per agent tier; keep secrets out of prompts and logs" is a best-practice engineering rule.

Suggested replacement for line 14:
```markdown
- Use trade-only keys (no withdraw/transfer), IP allowlists, one key per agent tier; keep secrets out of prompts and logs (vendor key controls MEASURED). [STATED] (research §7)
```
