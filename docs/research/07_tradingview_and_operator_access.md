# TradingView, direct connections and who operates the system

Last verified: 2026-11-24. Asked by the owner on 2026-11-24.

## Bottom line

Connect the service directly to the broker and the exchange. Do not use TradingView as a data source or a signal source for the service, and do not buy a TradingView plan for this project. The trading service runs by itself. Claude Code and Perplexity are both able to build, research and review from this repo.

## TradingView

| Item | Finding | Tag | Source |
|---|---|---|---|
| Connector in Perplexity | A TradingView connector is listed in Perplexity. It was not connected on the owner's account on 2026-11-24 | MEASURED, by looking it up in the product | [TradingView MCP docs](https://www.tradingview.com/mcp/docs) |
| Plan needed | "MCP access is included in Essential and all higher plans." "Trial plans do not include MCP access." | MEASURED | [TradingView help page](https://www.tradingview.com/support/solutions/43000795699-mcp-server-connect-your-ai-assistant-to-tradingview/) |
| What it does | Price history, screener, news, fundamentals, filings, calendars, watchlists and simple price alerts. No tool places a trade | MEASURED | [TradingView help page](https://www.tradingview.com/support/solutions/43000795699-mcp-server-connect-your-ai-assistant-to-tradingview/) |
| Automated use | Not permitted: "Unattended, scheduled or bulk data collection, and feeding MCP data into automated trading or decision systems." | MEASURED | [TradingView help page](https://www.tradingview.com/support/solutions/43000795699-mcp-server-connect-your-ai-assistant-to-tradingview/) |
| Trading decisions | "Don't use the MCP Server for automated trading or trading decisions, don't let an AI client place, change or cancel broker orders, and don't connect MCP alerts to webhooks or bots that trade." | MEASURED | [TradingView MCP docs](https://www.tradingview.com/mcp/docs) |
| Call limits | 10 calls a day on Essential, 20 on Plus, 50 on Premium, 500 on Ultimate or with the AI subscription | MEASURED | [TradingView MCP docs](https://www.tradingview.com/mcp/docs) |
| Data timing | The help page says market data is delayed. The docs page says delay and depth follow the user's plan and exchange subscriptions. The two pages differ | UNKNOWN | Both pages above |
| Status | Public beta | MEASURED | [TradingView help page](https://www.tradingview.com/support/solutions/43000795699-mcp-server-connect-your-ai-assistant-to-tradingview/) |
| Webhook alerts | A separate feature. Needs two-factor authentication. Only ports 80 and 443. A request is cancelled if the receiver takes longer than three seconds. "Webhooks may occasionally fail to reach the specified URL." | MEASURED | [TradingView webhook page](https://www.tradingview.com/support/solutions/43000529348-about-webhooks/) |
| Plan needed for webhooks | Paid plans only, from Essential up. The official webhook page does not state the plan | STATED, third-party guides | [CrossTrade guide](https://blog.crosstrade.io/tradingview-plan-for-webhook-alerts/) |

What this means:

- The connector is for the owner looking at markets himself and asking questions by hand. Its own terms rule out feeding the service.
- A paid plan does not change that. Premium raises the call limit and removes alert expiry. It does not permit automated use.
- Webhook alerts could carry a signal from a chart to our service, but delivery is not guaranteed and the signal logic would live outside the repo, where it cannot be tested, versioned or backtested by our engine. Not recommended as a signal path. [STATED] our recommendation
- Direct broker and exchange connections are where orders go anyway. Paper trading runs over the same connection, and the data terms are the broker's. See `docs/playbook/04_brokers_data_rules.md`.

## Who operates the system

| Piece | What runs it | Needs Perplexity or Claude Code? |
|---|---|---|
| Trading: data, scanners, risk engine, orders | The service on its own server | No |
| Model calls made by the running service | An API key, billed by use | No chat product. Anthropic's consumer terms do not allow automated access on a subscription ([consumer terms](https://www.anthropic.com/legal/consumer-terms)). MEASURED |
| Building, research, review, keeping docs current | An agent working from this repo | Either one |
| Status, pause and kill | The service's own commands | No. The owner or any agent uses the same commands |

Facts about the agents:

- Claude Code reads `AGENTS.md` as project instructions when the repo has no `CLAUDE.md`, from version 2.1.277. If a `CLAUDE.md` exists, it reads that file only, unless the file imports `AGENTS.md` ([Claude Code docs](https://code.claude.com/docs/en/claude-md)). MEASURED
- So this repo works in Claude Code as it stands. If a `CLAUDE.md` is ever added, it must import `AGENTS.md` or the hard rules stop loading.
- Perplexity Computer can be called from Claude Code as an MCP server, so a task can be handed to it from there. STATED, from Perplexity's product documentation. Not tested by us.

Open for the owner (hand-over 10 in `archive/quality/04_research_to_build.md`): which agent is the Builder for the unattended build, and on which machine it runs.
