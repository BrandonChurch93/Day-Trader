# Round 48: What News Adds to an AI Trader Over Prices Only

- Written: 2026-11-26 17:04 UTC
- Status: CURRENT
- Scope: Controlled 2023 to 2026 ablations measuring what news or text adds to an LLM trader over the same trader with prices only, plus news-feeding format comparisons, run-to-run dispersion across repeated runs or seeds, detectability of +20 bp a week over 20 weeks, and design risks in `timemachine/TM09_REGISTRATION.md`.
- Already covered in repo and not repeated: `docs/research/03_llm_trading_agents_evidence.md` (FinCon, FinAgent, FINSABER, FinPanel, Alpha Arena, AgentRouter, Glasserman & Lin), `docs/research/11_ai_trader_experiment_design.md` (bias and protocol rules), `docs/research/18_ai_systems_with_live_records.md` (live tracks, `rta-bench-1` headline -0.3 pp news removal and 5.2 to 5.4 pp seed gaps), `docs/playbook/03_role_of_ai.md`, and `docs/research/59_why_the_ai_traders_lost.md`. Only new studies or sharper numbers from directly opened links are reported below.
- Limits: No price data was fetched and no model or return calculation was run beyond converting each paper's reported total return and test length into basis points a week.

## Short Answer

Across post-cutoff controlled US equity ablations published through November 2026, adding news to an LLM trader produces a near-zero or slightly negative net difference over the same trader with prices only: `0.0` to `+3.0 bp` a week in [StockBench](https://arxiv.org/html/2510.02209), `-0.8` to `-3.8 bp` a week in [Inside the Trading Loop](https://arxiv.org/html/2611.11657), `-0.12` Sharpe inside a `±0.42` noise band in [CLQT](https://arxiv.org/html/2606.29771v3), and `-9 bp` per 5-day decision week in [rta-bench-1](https://arxiv.org/html/2611.19530) (all MEASURED by the papers). The only large positive news or reflection gains appear in pre-cutoff single-seed runs ([CryptoTrade](https://arxiv.org/html/2407.09546), [FinAgent](https://arxiv.org/html/2402.18485v3)) that failed to survive later out-of-knowledge or long-horizon tests. Measured run-to-run dispersion across identical settings is large (`4.3%` to `9.4%` SD over 3 months in [ACM TradingAgents](https://dl.acm.org/doi/10.1145/3800973.3801029), `0.27%` to `3.19%` SD over 82 days in [StockBench](https://arxiv.org/html/2510.02209), `±0.42` Sharpe in [CLQT](https://arxiv.org/html/2606.29771v3), `5.2` to `5.4 pp` in [rta-bench-1](https://arxiv.org/html/2611.19530)), which makes a `+20 bp` a week effect over 20 weeks unlikely to be reliably detectable in TM09 (INFERENCE).

## Controlled News and Component Ablations (2024 to 2026)

### StockBench (Chen et al., arXiv:2510.02209)

- Link: [StockBench](https://arxiv.org/html/2510.02209)
- What was compared: Same LLM trading agent run in three modes in Table 4: full inputs (price, fundamentals, news), without news (`w/o News`), and without news and fundamentals (`w/o News & Fund`), tested on `Kimi-K2` and `GPT-OSS-120B`.
- Instruments and dates: 20 highest-weight Dow Jones Industrial Average stocks, March 3, 2025 to June 30, 2025 (82 trading days, 16.4 trading weeks), `$100,000` starting cash, daily decisions at market open.
- Post-cutoff status: STATED post-cutoff by date comparison: "falls after the knowledge cutoff of mainstream LLMs, ensuring no data leakage" ([StockBench](https://arxiv.org/html/2510.02209)). No anonymization or ticker-masking probe was run.
- Size of difference (MEASURED): Over 82 trading days, `Kimi-K2` returned `+1.9%` with full inputs versus `+1.4%` without news (news minus no-news `+0.5 pp`, about `+3.0 bp` a week) and `+0.6%` without news and fundamentals. `GPT-OSS-120B` returned `-1.2%` with full inputs versus `-1.2%` without news (`0.0 pp`, `0.0 bp` a week) and `-3.4%` without news and fundamentals ([StockBench](https://arxiv.org/html/2510.02209)).
- Repeated runs and seeds (MEASURED): Each model ran 3 independent seeds. Table 5 reports return variance (`Var x 10^-4`) across 14 models ranging from `0.074` (`DeepSeek-V3`, SD `0.27%`), `0.153` (`Claude-4-Sonnet`, SD `0.39%`), and `0.210` (`GPT-5`, SD `0.46%`) up to `1.866` (`Kimi-K2`, SD `1.37%`), `3.250` (`Openai-O3`, SD `1.80%`), and `10.19` (`GPT-OSS-120B`, SD `3.19%`). Appendix B labels Table 5 "the variance of model returns for various LLMs" without explicitly confirming that variance is computed across the 3 seeds ([StockBench](https://arxiv.org/html/2510.02209)).
- Costs assumed: Zero trading friction. "we do not model trading costs, slippage, or liquidity limits, which makes trading easier than in real markets." ([StockBench](https://arxiv.org/html/2510.02209)).
- News feeding: Finnhub API providing "news articles released within the previous 48 hours on a daily basis" and keeping "the top five relevant news articles each time the search engine returns results" ([StockBench](https://arxiv.org/html/2510.02209)). No separate summarization or story-clustering step is stated.
- Replication or live survival: UNKNOWN; no later replication or live-capital run is reported.

### CLQT (arXiv:2606.29771v3)

- Link: [CLQT](https://arxiv.org/html/2606.29771v3)
- What was compared: Same multi-agent portfolio system (`gemini-2.5-flash-lite` anchor) with its news-sentiment module enabled versus disabled (`no-news-sentiment`), plus ablations of debate and memory.
- Instruments and dates: About 72 US equities from a point-in-time S&P 100 universe, 26 bi-weekly rebalance rounds from June 16, 2025 to June 12, 2026 (52 weeks), `$1M` initial capital.
- Post-cutoff status: STATED post-cutoff by model training cutoff dates: "Every model's training cutoff precedes the 2025-06-16 start" (`gemini-2.5-flash-lite` cutoff January 2025) ([CLQT](https://arxiv.org/html/2606.29771v3)).
- Size of difference (MEASURED): Full pipeline Sharpe `2.26` (volatility `11.0%`, max drawdown `-4.1%`, IR vs SPY `-0.04`) versus `no-news-sentiment` Sharpe `2.38`, so news minus no-news is `-0.12` Sharpe (removing news gave `+0.12`, run range `[-0.34, +0.59]`, which the authors classify as "within the noise band") ([CLQT](https://arxiv.org/html/2606.29771v3)). Exact cumulative return for the no-news arm is not printed (bp a week UNKNOWN).
- Repeated runs and seeds (MEASURED): 5 seeds per anchor configuration. Repeated-run noise band on the anchor is `±0.42` Sharpe (`±1 sigma`); across system configurations, repeated runs shifted Sharpe by up to `2.3` units and composite score by up to `25` points ([CLQT](https://arxiv.org/html/2606.29771v3)).
- Costs assumed: LOW cost tier models `2.0 bp` spread, `0.5 bp` commission, `1.0 bp` slippage, plus square-root market impact ([CLQT](https://arxiv.org/html/2606.29771v3)).
- News feeding: Multi-source feed (Alpha Vantage, Polygon, RSS, NewsAPI) with dynamic lookback `max(7, rebalance_gap + 1 day)`, deduplicated into a per-symbol daily table (mean sentiment, article count, most-extreme headline) and reduced to a 3-day `IMPROVING`, `DETERIORATING`, or `STABLE` trajectory (`delta_thresh = 0.1`) ([CLQT](https://arxiv.org/html/2606.29771v3)).
- Replication or live survival: A 4-week broker paper track (June 15 to July 10, 2026, 18 NYSE days) was run as indicative only and did not validate a news-vs-no-news return spread ([CLQT](https://arxiv.org/html/2606.29771v3)).

### Inside the Trading Loop (arXiv:2611.11657)

- Link: [Inside the Trading Loop](https://arxiv.org/html/2611.11657)
- What was compared: Same quant-and-LLM portfolio architecture (`claude-haiku-4-5` at default temperature) across `L0 Quant-only` (no LLM text), `L1 sentiment-only` (company news headlines only), `L1 macro-only` (macro headlines only), and `L1 Advisory` (both news and macro).
- Instruments and dates: 157 available of 161 US stocks, target 10-stock portfolio on an Alpaca paper account, 119 run dates from March 12, 2026 to August 31, 2026 (118 close-to-close intervals, 23.6 trading weeks).
- Post-cutoff status: NOT post-cutoff clean. "Model responses were collected after most decision dates, so timestamps do not restore historical model knowledge" ([Inside the Trading Loop](https://arxiv.org/html/2611.11657)).
- Size of difference (MEASURED): `L0 Quant-only` returned `59.9%` (Sharpe `2.09`, max drawdown `-26.4%`). `L1 sentiment-only` returned `59.7%` (Sharpe `2.09`, news minus no-news `-0.2 pp`, about `-0.8 bp` a week; zero days had an allocation change above `1 pp`, mean allocation distance `0.1 pp`). `L1 macro-only` returned `59.2%` (`-0.7 pp`, about `-3.0 bp` a week). `L1 Advisory` returned `59.0%`, a paired difference of `-0.9 pp` (`95% CI [-4.7, +3.6] pp`, about `-3.8 bp` a week, `95% CI [-19.9, +15.3] bp` a week) ([Inside the Trading Loop](https://arxiv.org/html/2611.11657)).
- Repeated runs and seeds: Two samples per prompt were collected; numerical return spread between the two samples is UNKNOWN (not printed in the text).
- Costs assumed: `5 bp` per side (`10 bp` round trip).
- News feeding: Sentiment agent received "at most 20 dated headlines with age and publisher, plus one-month price context and sector" and the macro agent received 15 market headlines, with no pre-summarization. The authors flag an archive defect directly relevant to Alpaca feeds: "Original Yahoo headline sets were not archived; publication-time-filtered Benzinga substitutes do not recover historical revisions" ([Inside the Trading Loop](https://arxiv.org/html/2611.11657)).
- Replication or live survival: No independent replication; paper-account reconstruction showed the news agent rarely moved weights.

### rta-bench-1 (arXiv:2611.19530, sharper per-week numbers beyond doc 18)

- Link: [rta-bench-1](https://arxiv.org/html/2611.19530)
- What adds to doc 18: Doc 18 already reported the total-return news removal difference (`-0.3 pp`, `95% CI [-3.4, +2.7] pp`) and seed gap (`5.2 pp` different seeds, `5.4 pp` same seed). What is sharper for weekly conversion is the per-decision 5-day return ablation across 56 US stocks and 3 periods (18 paired runs, 5 bp plus gap and market-impact costs): removing news changed 5-day decision return by `+0.09 pp` (`95% CI [-0.08, +0.24] pp`), meaning news minus no-news was `-9 bp` per 5-day decision week (`95% CI [-24, +8] bp` a week, MEASURED). Swapping in another stock's headlines changed total return by `-2.2 pp` (`[-5.3, +1.1]`) and 5-day decision return by `+0.15 pp` (`[-0.05, +0.38]`) ([rta-bench-1](https://arxiv.org/html/2611.19530)).

### Multi-Axis News Decomposition (arXiv:2605.06730v1)

- Link: [Multi-Axis News Decomposition](https://arxiv.org/html/2605.06730v1)
- What was compared: Supervised price-only forecaster versus price plus LLM news sentiment, price plus 4 LLM semantic axes (sentiment, risk, confidence, volatility), and price plus semantic tilt; also a 21-seed `DP-PPO` RL agent evaluated with full LLM signals versus LLM signals masked to neutral.
- Instruments and dates: 30 NASDAQ-100 stocks, out-of-sample test January 2, 2019 to December 29, 2023 (1,258 trading days, 251.6 weeks).
- Post-cutoff status: PRE-CUTOFF. News was scored with `gpt-4o-2024-08-06` in August to October 2024, after the 2019 to 2023 test window had ended ([Multi-Axis News Decomposition](https://arxiv.org/html/2605.06730v1)).
- Size of difference (MEASURED): Supervised price-only returned `126.40%` (Sharpe `0.653`) versus price plus sentiment `122.24%` (`0.641`, `-4.16 pp` over 5 years, about `-1.7 bp` a week) and price plus 4 semantic scores `111.84%` (`0.614`). Price plus semantic tilt reached `133.89%` (Sharpe `0.674`), a paired daily difference of `+0.234 bp` a day (`95% CI [-1.198, +1.497]`, Wilcoxon `p = 0.568`, or `+1.2 bp` a week). In 21-seed `DP-PPO`, full signals returned `195.04 ± 44.18%` (Sharpe `0.920 ± 0.096`) versus neutral-masked `190.93 ± 42.57%` (`0.907 ± 0.094`, Wilcoxon `p` around `0.25` to `0.31`) ([Multi-Axis News Decomposition](https://arxiv.org/html/2605.06730v1)).
- Repeated runs and seeds (MEASURED): 21 seeds for `DP-PPO` had a cross-seed SD of `±44.18 pp` cumulative return (`±0.096` Sharpe), ten times larger than the `+4.11 pp` news difference.
- Costs assumed: `0.10%` (`10 bp`) per trade.
- News feeding: 39,995 FNSPID articles, batched up to 20 articles per LLM call into 4 integer scores (1 to 5) aggregated over a `[d-3, d]` lookback window ([Multi-Axis News Decomposition](https://arxiv.org/html/2605.06730v1)).
- Replication or live survival: UNKNOWN; no post-cutoff or live replication.

### Sota (arXiv:2610.10407)

- Link: [Sota](https://arxiv.org/html/2610.10407)
- What was compared: Same RL-trained LLM options trader (`Seed = 0`) trained and tested without news versus with contemporaneous news and filing summaries.
- Instruments and dates: SPY plus 9 large-cap US stock options, test March 3, 2025 to August 29, 2025 (about 26 weeks).
- Post-cutoff status: UNKNOWN for base LLM weights; chronological train-test split only (SFT Sep to Nov 2024, RL Dec 2024 to Feb 2025, test Mar to Aug 2025).
- Size of difference (MEASURED): RL without news returned `+18.32%` (Sharpe `1.60`, max drawdown `8.96%`). RL with news returned `-2.72%` (Sharpe `-0.16`, max drawdown `31.69%`), a news-minus-no-news difference of `-21.04 pp` over 26 weeks (about `-80.9 bp` a week, leveraged options). "Retaining news during reinforcement learning lowers total return to -2.72% and raises maximum drawdown to 31.69%." ([Sota](https://arxiv.org/html/2610.10407)).
- Repeated runs and seeds: Single seed (`Seed = 0`); multi-seed spread UNKNOWN.
- Costs assumed: Full quoted half-spread (`1.0x`), `$0.65` per contract per leg, `$0.005` per share, `1 bp` equity half-spread.
- News feeding: Massive.com news API and SEC EDGAR "point-in-time textual summaries of news and filings" ([Sota](https://arxiv.org/html/2610.10407)).
- Replication or live survival: UNKNOWN.

### LiveOption (arXiv:2609.33470)

- Link: [LiveOption](https://arxiv.org/html/2609.33470)
- What was compared: Baseline options trading agent versus `No News` ablation in Table 29 across three models (`DeepSeek-V4-Flash`, `GPT-OSS-120B`, `Qwen3-235B-A22B`).
- Instruments and dates: 24 US single-name equity options around scheduled 2025 earnings (`T-2` to `T+2`, 4 trading days per episode, 24 paired episodes per model).
- Post-cutoff status: NOT a contamination control. "The evaluation window is therefore not a contamination control for this panel, and we do not present it as one" ([LiveOption](https://arxiv.org/html/2609.33470)).
- Size of difference (MEASURED): Negating Table 29 (`No News` minus `Baseline`) to get news minus no-news per 4-day options episode: `DeepSeek-V4-Flash` `+2.46 pp` (`95% CI [-2.87, +7.44]`, `p_Holm = 1.000`), `GPT-OSS-120B` `-0.82 pp` (`[-7.41, +5.96]`, `p_Holm = 1.000`), `Qwen3-235B-A22B` `-0.72 pp` (`[-5.40, +5.46]`, `p_Holm = 1.000`) ([LiveOption](https://arxiv.org/html/2609.33470)). None is distinguishable from zero.
- Repeated runs and seeds: Single rollout per case; run-to-run dispersion UNKNOWN.
- Costs assumed: `$0.65` per contract, `1.0 bp` slippage, zero explicit spread ("should be read as excluding spread cost") ([LiveOption](https://arxiv.org/html/2609.33470)).
- News feeding: Benzinga via QFinZero, "Last-five-day news sentiment" gated by timestamp ([LiveOption](https://arxiv.org/html/2609.33470)).
- Replication or live survival: UNKNOWN.

### CryptoTrade (arXiv:2407.09546) and FinAgent Reflection Ablation (arXiv:2402.18485v3)

- Links: [CryptoTrade](https://arxiv.org/html/2407.09546) and [FinAgent](https://arxiv.org/html/2402.18485v3)
- What was compared: `CryptoTrade` Table 5 ablated news and reflection on ETH (`Full`, `w/o News`, `w/o Reflection`, `Base`). `FinAgent` Table 5 ablated Market Intelligence (`M`), Low-level reflection (`L`), High-level reflection (`H`), and Tools (`T`) on TSLA and ETHUSD.
- Instruments and dates: `CryptoTrade` ETH bullish split October 1 to December 1, 2023 (61 days, 8.71 weeks). `FinAgent` TSLA and ETHUSD test June 1, 2023 to January 1, 2024 (about 30 weeks).
- Post-cutoff status: PRE-CUTOFF or unverified. `CryptoTrade` tested GPT-4o on late-2023 data while only checking GPT-3.5's September 2021 cutoff ([CryptoTrade](https://arxiv.org/html/2407.09546)); `FinAgent` states no model knowledge cutoff for its GPT-4 backbone ([FinAgent](https://arxiv.org/html/2402.18485v3)).
- Size of difference (MEASURED, pre-cutoff single runs): In `CryptoTrade`, `Full` returned `28.47%` (Sharpe `0.23`) versus `w/o News` `19.69%` (Sharpe `0.06`, news minus no-news `+8.78 pp` over 8.71 weeks, `+100.8 bp` a week), `w/o Reflection` `17.14%`, and `Base` `8.40%` ([CryptoTrade](https://arxiv.org/html/2407.09546)). In `FinAgent`, adding low-level reflection `L` to `M` raised TSLA ARR from `39.27%` to `57.16%` and ETHUSD from `25.97%` to `52.33%`; adding high-level reflection `H` raised TSLA to `89.25%` ("the integration of the low-level reflection module leads to an impressive increase in ARR% by 45% to 101% for TSLA, and ETHUSD") ([FinAgent](https://arxiv.org/html/2402.18485v3)).
- Repeated runs and seeds: Neither paper reports multi-seed variance. `FinAgent` Appendix H.2 admits uncontrolled run-to-run variation: "In our experiments, we observed a distinct variation in the trading decisions when modifying the decision prompt and executing the agent across different trials. Owing to the inherent nature of the API service provided by OpenAI, controlling the randomness in the responses is not feasible." ([FinAgent](https://arxiv.org/html/2402.18485v3)).
- Costs assumed: Both mention commission fees in the MDP text without stating a numerical fee rate or slippage.
- News feeding: `CryptoTrade` pulled daily Gnews items summarized by `GPT-3.5-turbo` (item count not stated).
- Replication or live survival: FAILED later replication. As already documented in `docs/research/03_llm_trading_agents_evidence.md`, `FinAgent` failed to beat buy-and-hold in FINSABER's 20-year test (`p > 0.34`) and posted negative Sharpe (`-0.28` to `-0.03`) in FinPanel's 2025 out-of-knowledge test.

## Dedicated Run-to-Run Noise and Memory-Leakage Studies (2026)

### Reproducibility in the TradingAgents Framework (ACM ICAIF 2026)

- Link: [TradingAgents Reproducibility](https://dl.acm.org/doi/10.1145/3800973.3801029)
- Instruments and dates: Single stock (`GOOGL`), 3 months (May to July 2025, about 13 weeks), post-cutoff (`GPT-4o` May 2024 cutoff, `Qwen3-30B` April 2025 cutoff). Post-hoc cost note: `0.05%` round trip (`0.85%` over 17 trades).
- Run-to-run spread (MEASURED): `GPT-4o` (`T=1`, 5 runs) averaged `15.8% ± 4.2%` SEM, **SD `9.4%`**. `Qwen3:30B` (`T=1`, 10 runs) averaged `18.1% ± 2.8%` SEM, **SD `9.0%`**, ranging from `5%` to `28%` (a `23 pp` spread). Setting `T=0` with random seed (10 runs) still left **SD `5.5%`**; setting `T=0` with fixed `seed=42` (10 runs) still left **SD `4.3%`**. Only locking `T=0, seed=42, top_k=1, top_p=0` produced `0.0%` SD. None of the configurations differed statistically from `GOOGL` buy-and-hold (`19.1%`, `p > 0.26`) ([TradingAgents Reproducibility](https://dl.acm.org/doi/10.1145/3800973.3801029)).

### KTD-Fin Memory-Controlled Benchmark (arXiv:2605.28359v1)

- Link: [KTD-Fin](https://arxiv.org/html/2605.28359v1)
- What was tested: Same price-only LLM trader on Chinese CSI300 stocks (10 windows of about 43 trading days, 2024 to 2026, only W10 strictly post-cutoff; buy cost `5 bp`, sell cost `15 bp`, 5 seeds per cell) under four masking modes: real ticker and date (`bright`), anonymized ticker (`stock-blind`), anonymized date (`date-blind`), and both anonymized (`blinded`).
- Key finding (MEASURED): Showing real tickers injects identity priors even when zero news is provided. "Under bright, justifications interleave factor inputs with content the input does not carry—brand identity, sector taxonomy, and, most diagnostically, specific historical trading days (e.g. 'the Oct-18 limit-up move' for SMIC, a date unrecoverable from the price-only channel)." The authors summarize: "the ticker-visible model trades on identity priors and loses; the anonymized model holds cash." ([KTD-Fin](https://arxiv.org/html/2605.28359v1)). Under `memory-only` across 5 seeds, `bright` median return was `-0.16%` while `blinded` held cash at `0.00%`; under `open-research`, `bright` median was `-2.11%` versus `-1.83%` `blinded` (per-cell IQR was not printed in Table 3).

## Evidence on How News Should Be Fed: Freshness, Clustering, and Numbers vs Stories

Two large 2026 empirical studies tested news format, freshness, and story clustering directly (neither is a full LLM-trader ablation, so they inform news-feeding design rather than the bp-per-week table).

### Buy the Rumor, Sell the News: When Is News Priced In? (arXiv:2608.14014)

- Link: [Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014)
- Corpus: "We test them on 4.57 million financial news articles covering roughly 3,000 US stocks (2023–2026)." ([Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014)).
- Freshness and overreaction (MEASURED): "Pooled across all signed events, this running total reaches +0.58% by the close of publication day, then falls back and ends day +20 at +0.20%. The ratio of the two levels is 2.8: by the closing bell of publication day the market had already moved almost three times as far as where it would stand a month later, and the extra ground was given back over the following weeks." ([Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014)).
- Rumor versus confirmation (MEASURED): "The rumor day delivers +0.36% in the rumor's direction. Between rumor and confirmation the stock adds nothing (−0.09%). The confirmation day itself is worth +0.01%, and days +6 to +20 after confirmation give back −0.06%." ([Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014)).
- Quantified numbers versus soft stories (MEASURED): "markets underreact to numbers and overreact to stories: quantified fundamental news (earnings, dividends, guidance, analyst actions) keeps drifting in the direction of the news for weeks, while soft story-driven news (launches, macro commentary, leadership) gives back its move." Over days `+6` to `+20`, capital returns drifted `+0.35%`, earnings `+0.22%`, guidance `+0.13%`, and analyst actions `+0.10%`, while macro read-throughs reversed `-0.34%`, product launches `-0.18%`, leadership stories `-0.18%`, and competition `-0.17%` ([Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014)).
- Follow-up duplication (MEASURED): Clustering title-and-summary embeddings at cosine similarity `0.80` "reveals that 55% of all articles are follow-up coverage of a story already running" ([Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014)).

### LLM-Driven Small-Cap Trading (arXiv:2608.12283v1)

- Link: [LLM-Driven Small-Cap Trading](https://arxiv.org/html/2608.12283v1)
- Corpus: Russell 2000 equities, news scored with `GPT-4o mini` (October 2023 cutoff, held-out 2025 test, 20:00 UTC next-day cutoff, `50` and `100 bp` plus `5 bp` slippage cost scenarios). No price-only ablation is reported.
- Story clustering versus isolated headlines (STATED design finding): "multiple outlets frequently cover the same event, and scoring each report separately lets syndicated coverage dominate a signal simply by being repeated, not by being informative." The authors cluster article summaries over a trailing 30-day window at cosine similarity `0.90` and retain only the centroid article per story ([LLM-Driven Small-Cap Trading](https://arxiv.org/html/2608.12283v1)).
- Residual distraction effect (STATED): Even with a pre-test model cutoff, "the model may still carry general knowledge of a company independent of the specific event being scored" ([LLM-Driven Small-Cap Trading](https://arxiv.org/html/2608.12283v1)).

## 1. Table of Measured News-Minus-No-News Differences

Weekly conversions divide each paper's reported percentage-point difference by the test length in trading weeks (`bp/week = pp * 100 / weeks`). All underlying differences are MEASURED by the cited paper; weekly conversions are arithmetic rescalings of those figures.

| Study | Market and Period | Cutoff Clean? | Costs | Paper's News Minus No-News | Weekly Conversion (bp/week) | Status |
|---|---|---|---|---|---|---|
| [StockBench](https://arxiv.org/html/2510.02209) (`Kimi-K2`) | 20 DJIA stocks, 82 days (16.4 wks, 2025) | STATED yes | 0 bp | `+0.5 pp` (`+1.9%` vs `+1.4%`) | `+3.0 bp/week` | MEASURED |
| [StockBench](https://arxiv.org/html/2510.02209) (`GPT-OSS-120B`) | 20 DJIA stocks, 82 days (16.4 wks, 2025) | STATED yes | 0 bp | `0.0 pp` (`-1.2%` vs `-1.2%`) | `0.0 bp/week` | MEASURED |
| [Inside the Trading Loop](https://arxiv.org/html/2611.11657) (`L1 sentiment`) | 157 US stocks, 118 days (23.6 wks, 2026) | No (Aug 2026 run) | 5 bp/side | `-0.2 pp` (`59.7%` vs `59.9%`) | `-0.8 bp/week` | MEASURED |
| [Inside the Trading Loop](https://arxiv.org/html/2611.11657) (`L1 advisory`) | 157 US stocks, 118 days (23.6 wks, 2026) | No (Aug 2026 run) | 5 bp/side | `-0.9 pp` (`95% CI [-4.7, +3.6]`) | `-3.8 bp/week` (`[-19.9, +15.3]`) | MEASURED |
| [rta-bench-1](https://arxiv.org/html/2611.19530) | 56 US stocks, 3 periods (18 paired runs) | Mixed (2026 clean) | 5 bp + impact | `-0.09 pp` per 5-day decision (`+0.3 pp` total) | `-9.0 bp/week` (`[-24, +8]`) | MEASURED |
| [CLQT](https://arxiv.org/html/2606.29771v3) | ~72 US stocks, 52 wks (2025 to 2026) | STATED yes | 3.5 bp + impact | `-0.12` Sharpe (`2.26` vs `2.38`, in noise band) | UNKNOWN (returns not printed) | MEASURED |
| [Multi-Axis News](https://arxiv.org/html/2605.06730v1) (`semantic tilt`) | 30 NDX stocks, 251.6 wks (2019 to 2023) | No (pre-cutoff) | 10 bp/trade | `+0.234 bp/day` (`p = 0.568`) | `+1.2 bp/week` (`[-6.0, +7.5]`) | MEASURED |
| [Multi-Axis News](https://arxiv.org/html/2605.06730v1) (`+sentiment`) | 30 NDX stocks, 251.6 wks (2019 to 2023) | No (pre-cutoff) | 10 bp/trade | `-4.16 pp` (`122.24%` vs `126.40%`) | `-1.7 bp/week` | MEASURED |
| [Sota](https://arxiv.org/html/2610.10407) | SPY + 9 stock options, 26 wks (2025) | UNKNOWN | `$0.65` + half-spread | `-21.04 pp` (`-2.72%` vs `+18.32%`) | `-80.9 bp/week` (options) | MEASURED |
| [LiveOption](https://arxiv.org/html/2609.33470) (3 models) | 24 US earnings options, 4-day episodes | No | `$0.65` + 1 bp | `+2.46`, `-0.82`, `-0.72 pp` (`p_Holm = 1.0`) | Not weekly equity | MEASURED |
| [CryptoTrade](https://arxiv.org/html/2407.09546) | ETH bull split, 8.71 wks (late 2023) | No (pre-cutoff) | Unspecified | `+8.78 pp` (`28.47%` vs `19.69%`) | `+100.8 bp/week` (crypto, 1 run) | MEASURED |

## 2. Measured Run-to-Run Spread Figures

- [TradingAgents Reproducibility](https://dl.acm.org/doi/10.1145/3800973.3801029) (GOOGL, 13 weeks, post-cutoff): `GPT-4o` (`T=1`, 5 runs) SD `9.4%`; `Qwen3:30B` (`T=1`, 10 runs) SD `9.0%` (range `5%` to `28%`, `23 pp` spread); `Qwen3:30B` (`T=0`, random seed, 10 runs) SD `5.5%`; `Qwen3:30B` (`T=0`, fixed `seed=42`, 10 runs) SD `4.3%` (MEASURED).
- [StockBench](https://arxiv.org/html/2510.02209) (20 DJIA stocks, 16.4 weeks, 3 seeds): Table 5 SD spans `0.27%` (`DeepSeek-V3`), `0.39%` (`Claude-4-Sonnet`), and `0.46%` (`GPT-5`) up to `1.37%` (`Kimi-K2`), `1.80%` (`Openai-O3`), and `3.19%` (`GPT-OSS-120B`) (MEASURED; Appendix B does not explicitly confirm whether Table 5 variance is across the 3 seeds).
- [CLQT](https://arxiv.org/html/2606.29771v3) (~72 US stocks, 52 weeks, 5 seeds): anchor repeated-run noise band `±0.42` Sharpe (`±1 sigma`), which at `11.0%` annual volatility equals `4.62%` a year; across configurations, repeated runs moved Sharpe by up to `2.3` units (MEASURED).
- [rta-bench-1](https://arxiv.org/html/2611.19530) (56 US stocks, multi-month windows): `5.2 pp` mean absolute return gap across 54 different-seed pairs and `5.4 pp` across 24 same-seed reruns (MEASURED, already in doc 18).
- [Multi-Axis News Decomposition](https://arxiv.org/html/2605.06730v1) (30 NDX stocks, 5 years, 21 seeds): `DP-PPO` cross-seed SD was `±44.18 pp` cumulative return (`±0.096` Sharpe) with news and `±42.57 pp` (`±0.094` Sharpe) without news (MEASURED).

## 3. Plain Reading: Is +20 bp a Week on 20 Weeks Detectable? (INFERENCE)

Label: INFERENCE from the measured spreads above and standard `n = 20` paired t-test math.

For a true mean difference of `+20 bp` a week over `n = 20` weeks to clear a one-sided 5% test (`t >= 1.73`, `df = 19`), the standard error of `D_t = N_t - mean(P1_t, P2_t)` must be at most `11.6 bp` a week, which requires the weekly standard deviation `sd(D)` to be at most `52 bp` a week. For 80% statistical power (`mean / SE >= 2.55`), `sd(D)` must be at most `35 bp` a week.

On the outside evidence, `sd(D)` in a 38-stock LLM desk is very unlikely to stay below `35` to `52 bp` a week unless the news notes barely change positions at all (as happened in [Inside the Trading Loop](https://arxiv.org/html/2611.11657), where news moved weights by `0.1 pp` and added `-0.8 bp` a week). Converting the multi-stock run-to-run SDs above to weekly equivalents (dividing multi-week SD by `sqrt(weeks)`) gives `34` to `79 bp` a week for the active `StockBench` models (`Kimi-K2`, `o3`, `GPT-OSS-120B`), `64 bp` a week for `CLQT` (`462 bp / sqrt(52)`), and `119` to `261 bp` a week on a single stock in `TradingAgents`, before adding active portfolio tracking error when `N` picks different stocks from `P1` and `P2`. Even in [Inside the Trading Loop](https://arxiv.org/html/2611.11657), the 23.6-week `95% CI` around the paired advisory difference was `830 bp` wide (`[-4.7, +3.6] pp`), implying a weekly paired SD near `212 bp` a week. Averaging `P1` and `P2` cuts price-only run variance by only half (and leaves `N` unaveraged), while averaging two bosses gives less than a `sqrt(2)` reduction if both models react similarly to the same week's tape.

Plain verdict (INFERENCE): `+20 bp` a week over 20 weeks is very unlikely to be detectable in TM09 unless the desk holds nearly identical portfolios across arms, and every post-cutoff US equity ablation so far puts the true news effect near zero (`-9` to `+3 bp` a week), far below `+20 bp` a week.

## 4. TM09 Design Choices Flagged as Known Mistakes by Outside Evidence

Each item maps a specific line in `timemachine/TM09_REGISTRATION.md` to published 2024 to 2026 evidence.

- Forbidding raw headlines and sending only scout paraphrases to `N` ("It may name the event in its own words, but may not paste a headline in a note... Send only paraphrased notes to N"): `AgentRouter` (ICML 2026, in `docs/research/03_llm_trading_agents_evidence.md` and `docs/playbook/03_role_of_ai.md`) shows that passing a smaller model's paraphrase without primary text degrades frontier-model decisions when step 1 drops details. [Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014) shows that quantified numbers (earnings, guidance, capital returns) drift positively while soft narrative stories reverse; paraphrasing headlines strips exact figures while keeping the promotional story.
- Headline-only input with no article body and no story deduplication ("The news scout gets only headline, source time and symbol. No article or filing body, summary, URL or attachment"): [Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014) measures that `55%` of financial news articles are follow-up coverage of an already-running story and that rumor confirmations add `+0.01%` and reverse. [LLM-Driven Small-Cap Trading](https://arxiv.org/html/2608.12283v1) warns that unclustered headline streams overweight syndicated duplicates simply because they repeat.
- Weekly flat reset at Friday close ("Start every boss arm flat with the cash named by `tm09.execution.starting_cash_key`" and "On Friday, or the week's last recorded stock session, mark positions held after any fills from that session's last wake at that session's close less the configured half-spread"): [Buy the Rumor, Sell the News](https://arxiv.org/pdf/2608.14014) finds that publication-day moves are already overdone (`2.8x` the 20-day level) while the only positive post-news drift on quantified fundamentals plays out over days `+6` to `+20` (`+0.10%` to `+0.35%`). Resetting flat every week cuts off multi-week drift while paying full weekly half-spread friction.
- Asymmetric `1` news run (`N`) versus `2` price-only runs (`P1`, `P2`) per boss-week: Because `Var(N - mean(P1, P2)) = Var(N) + 0.5 * Var(P)`, the single unaveraged `N` run contributes two-thirds of the run-to-run variance. Given `4.3%` to `9.4%` SD in [TradingAgents Reproducibility](https://dl.acm.org/doi/10.1145/3800973.3801029) and `5.2` to `5.4 pp` seed gaps in [rta-bench-1](https://arxiv.org/html/2611.19530), running `N` only once leaves the treatment arm the noisiest piece of the paired difference.
- Real ticker symbols and real dates on historical weeks, plus a post-hoc 38-stock roster ("The list was chosen after the replay period"): [KTD-Fin](https://arxiv.org/html/2605.28359v1) proves that visible tickers cause LLMs to trade on brand priors and remembered events even with price-only inputs ("the ticker-visible model trades on identity priors and loses; the anonymized model holds cash"). If any replay week predates a boss or scout model's training cutoff, real tickers and dates also allow pretraining recall.
- Unverified Alpaca headline revision history ("Its equal creation and update times do not prove that an original headline version survived"): [Inside the Trading Loop](https://arxiv.org/html/2611.11657) flags this exact archive flaw on Benzinga substitutes ("publication-time-filtered Benzinga substitutes do not recover historical revisions"). Silent post-publication headline edits can leak later outcomes into `N`.
