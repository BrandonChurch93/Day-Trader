# Check log for 18. AI trading systems with a live record

Date: 2026-11-25. Source report: research2/live_ai_traders/REPORT.md. Every source below was opened by the checker.

| # | Claim | Verdict | Source opened |
|---|---|---|---|
| 1 | OKX paper and funded dates, 14 paper methods | Confirmed. Added that the wider backtest has 32 methods | [OKX](https://arxiv.org/html/2609.34510v1) |
| 2 | OKX paper returns: BTC 30.35, MacroHFT 38.12, Qwen 37.77, LSTM 34.08, XGBoost 27.53 | Confirmed | [OKX](https://arxiv.org/html/2609.34510v1) |
| 3 | OKX funded returns: BTC 11.63, Qwen 3.72, LSTM -0.33, XGBoost -0.79, TRA -14.74 | Confirmed | [OKX](https://arxiv.org/html/2609.34510v1) |
| 4 | OKX 6.38 point gap | Confirmed. Clarified: Qwen 10.10% paper vs 3.72% live over the same funded window | [OKX](https://arxiv.org/html/2609.34510v1) |
| 5 | OKX executor 2x, 15%, 60%, 300 s, 10 USDT, risk_usd and stops not enforced; prompt quote | Confirmed | [OKX](https://arxiv.org/html/2609.34510v1) |
| 6 | Nof1 S1 leverage 1 to 20x, attributed to the reconstruction | Corrected. The reconstruction gives no leverage. 1 to 20x comes only from the unofficial gist | [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/), [gist](https://gist.github.com/wquguru/7d268099b8c04b7e5b6ad6fae922ae83) |
| 7 | Nof1 S1 per-model returns, fills, fees | Confirmed. Added the omitted Claude Sonnet 4.5 row: -29.9%, 320 fills, $590 | [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/) |
| 8 | Nof1 S1.5 official winner +12.11%, $4,844, end December 3, 2025 | Confirmed. The page gives no starting capital | [Nof1](https://alphaarena.ai) |
| 9 | Reconstruction: Grok 4.20 +13.0% $5,206, Qwen -29.7%, 31 of 38 lost, $43k fees, best account +33.7% with 1,613 fills and $508 fees | Confirmed | [TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/) |
| 10 | Nof1 blog: $10k each, same prompt and harness, differences in risk, sizing and holding time | Confirmed | [Nof1 blog](https://alphaarena.ai/blog) |
| 11 | TradeRank Gemini +27.65% vs SPY +16.53% and BTC -16.93%, nine seasons, four versions, resets | Confirmed | [TradeRank](https://www.traderank.ai/blog/can-ai-beat-the-market) |
| 12 | TradeRank best Season 8 model +12.82% vs ETH +34.5% | Corrected. ETH +34.5% is not on the page. The page gives BTC +22.63% for Season 8 and Gemini +8.60%, 3rd of 14. The ETH figure was removed | [TradeRank](https://www.traderank.ai/blog/can-ai-beat-the-market) |
| 13 | TradeRank 3,131 trades across 131 model-seasons; rules (0.1%, 1x, no slippage, one entry, 10 holdings, 0.80 confidence, 15-minute stops) | Confirmed. Added that these cover 11 seasons and 78 competitors | [TradeRank methods](https://www.traderank.ai/how-it-works) |
| 14 | Season 7 records lost | Confirmed. Added the rank persistence result (pooled +0.03) | [TradeRank study](https://www.traderank.ai/blog/nine-seasons-llm-paper-trading) |
| 15 | BingX snapshot values | Confirmed. Added DeepSeek $9.44k and Gemini $9.14k | [BingX](https://bingx.com/en/blog/article/bingx-ai-arena-ranking-the-six-llm-traders-after-a-big-week) |
| 16 | AIEQ FY2025 and December 2025 returns, 0.75%, 804%, index switch January 29, 2024, method | Confirmed | [AIEQ report](https://amplifyetfs.com/wp-content/uploads/files/AIEQ_Annual_Report.pdf), [SEC](https://www.sec.gov/Archives/edgar/data/1633061/000121390026008328/ea0273008-02_497k.htm) |
| 17 | Rallies "possible options described in support" | Corrected. Options are listed as "coming soon". GPT +58.31% confirmed, with no period or benchmark shown | [Rallies support](https://support.rallies.ai/ai-arena/overview), [Rallies arena](https://rallies.ai/arena) |
| 18 | StockBench: hold +0.4%, eight models above, Qwen3-235B-Think +2.5%, Kimi +0.6% without news and fundamentals, all models trail hold in the downturn | Confirmed | [StockBench](https://arxiv.org/html/2510.02209) |
| 19 | DeepFund Grok +1.1% vs -3.09% and -6.91%, 8 of 9 lost, 1,059 of 1,080 valid, ~60% cash, decision counts | Confirmed | [DeepFund](https://arxiv.org/html/2505.11065v1) |
| 20 | AMA returns, architecture quote, HOLD means flat in code | Confirmed | [AMA paper](https://arxiv.org/html/2510.11695), [AMA code](https://github.com/The-FinAI/Agent_Market_Arena) |
| 21 | AI-Trader capital $10,000 US, 100,000 CNY, 50,000 USDT; DeepSeek ahead of QQQ; crypto averaged two trades | Corrected to UNKNOWN. The paper and repo state no capital. Only MiniMax-M2 was confirmed ahead of QQQ (+9.56% vs +1.87%). The crypto trade counts were not confirmed and were removed. Crypto -12.18% vs -14.30% confirmed | [AI-Trader paper](https://arxiv.org/html/2512.10971), [repo](https://github.com/HKUDS/AI-Trader) |
| 22 | LiveTradeBench figures | Confirmed | [LiveTradeBench](https://arxiv.org/html/2511.03628) |
| 23 | FinRL-Meta dates and returns, coin universe chosen by October 2021 market cap | Confirmed | [FinRL-Meta](https://arxiv.org/html/2112.06753v2) |
| 24 | FinRL contests: 2023 windows, 2024 +134.05% vs +72.71%, 2025 +191.14% vs +164.52%, captions flag wrong figures | Confirmed, with one fix. The 2025 wrong-Rachev caption refers to Queen's Gambit, not the winner | [FinRL contests](https://arxiv.org/html/2504.02281v3) |
| 25 | FINSABER: hold beats FinMem and FinAgent, "paired p at most 0.0117", "p above 0.34" | Corrected. No p-values appear in the paper text that was opened. Replaced with the reported Sharpe ratios | [FINSABER](https://arxiv.org/html/2505.07078) |
| 26 | GKX periods, R squared, NN4 Sharpe 1.35 and 2.45, timing 0.77 vs 0.51 | Confirmed. The 1.69 Sharpe excluding small stocks and the 143.53% boosted-tree turnover could not be verified and were removed. NN4 turnover of 126.81% a month was added | [GKX](https://academic.oup.com/rfs/article/33/5/2223/5758276) |
| 27 | Tiberga net Sharpes, 18 to 28 bp, post-availability alphas, LightGBM significant, pooled shift not significant | Confirmed | [Tiberga](https://afajof.org/management/viewp.php?n=265916) |
| 28 | Lopez-Lira and Tang Sharpes by cost, turnover, subperiods | Confirmed. The authors label costs as round trip. The report's own "9.5 bp a day drag" reading was removed | [Lopez-Lira and Tang](https://arxiv.org/html/2304.07619) |
| 29 | Blinded news test correlations, no surviving strategy, 62 to 74% identification | Confirmed. The name "OLIVIA" was not checked and was dropped | [Blinded test](https://arxiv.org/html/2611.03985) |
| 30 | rta-bench: 91 runs with no significant alpha, 30% cash instruction effects, 5.2 point seed spread, news join +32.0 vs -6.7 bp, +0.34% drift with t = 2.2, Appendix A prompt, v0.8.0 | Confirmed. Added that the 30% cash rule changed return by -5.6 points (interval -19.4 to +4.5). The author name "Wang" was not checked and was dropped | [rta-bench](https://arxiv.org/html/2611.19530v1) |
| 31 | ECC Analyzer "direct return prediction around chance" | Corrected. Its main targets are volatility and value at risk. The "around chance" wording was not found and was removed | [ECC](https://arxiv.org/html/2404.18470v1) |
| 32 | Numerai $500m capacity, meta model, staking | Confirmed across the fund page and the tournament docs | [Numerai](https://numer.ai/fund), [docs](https://docs.numer.ai/numerai-tournament) |
| 33 | Renaissance testimony content | Confirmed. No return figures and no bet counts | [Testimony](https://www.hsgac.senate.gov/wp-content/uploads/imo/media/doc/STMT%20-%20Renaissance%20%28July%2022%202014%29.pdf) |
| 34 | TradingAgents README quote | Confirmed | [TradingAgents](https://github.com/TauricResearch/TradingAgents) |

Other edits:

- The 0.30% cost written into the project adaptation prompt is not a key in config/thresholds.yaml. It was replaced with a placeholder.
- Project thresholds are now named by key only.
- Report residue was removed.
- The section headers were renamed to match the brief.
