# 44. Replay 11: an AI reads each earnings release and says buy or skip

Status: research result, pretend trades on past prices. Built by `research_rig/report_11.py` from `research_rig/results_11_design.json`. The plan, fixed before any reader ran, is `research_rig/PREREG_11_earnings_release_reader.md`. Design sample scored 2026-11-25 18:11 UTC. The held-back half is not scored yet, so there is no verdict yet.

## What was tested

- When a company files its quarterly results, a model reads the press release and gives a score from -2 to 2. A score above zero is a buy at the next regular open. The stock is sold at the close one trading day later (H1) or five trading days later (H5). H5 is the main test.
- Costs per side, in basis points: S&P 500 5, S&P MidCap 400 10, S&P SmallCap 600 20.
- Yardstick (a) is buying every release. Yardstick (b) is the same number of buys drawn at random from the same releases, 1000 times. A set-up has to beat (a) and the 95th percentile of (b).
- The readers saw only the release text. They were told not to use the web or prices. That is an instruction and was not enforced; the gap is in the plan.

## The design sample (used only to choose a set-up, not to judge)

MEASURED. 450 releases, 150 from each list, read by four models.

### Hold H1

| Set-up | Buys | Share bought | Mean of buys after costs | Mean of every release (a) | Buys less (a) | 95th percentile of random picks (b) | Random draws beaten | Buys less SPY | Above both marks |
|---|---|---|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 alone | 199 | 44.2% | -0.00% | -0.02% | +0.02% | +0.42% | 50.2% | -0.20% | no |
| Grok 4.7 alone | 257 | 57.1% | +0.11% | -0.02% | +0.13% | +0.36% | 70.0% | -0.06% | no |
| Kimi K3 alone | 283 | 62.9% | +0.21% | -0.02% | +0.23% | +0.29% | 87.4% | +0.04% | no |
| Claude Opus 5.5 alone | 202 | 44.9% | +0.27% | -0.02% | +0.28% | +0.42% | 85.2% | +0.06% | no |
| middle of the three small readers | 247 | 54.9% | +0.17% | -0.02% | +0.19% | +0.35% | 80.4% | +0.01% | no |
| cascade: small readers, Opus where they disagree | 217 | 48.2% | +0.10% | -0.02% | +0.12% | +0.41% | 68.9% | -0.10% | no |
| plain rule: buy when the stock opened up at least 2.0% | 158 | 35.1% | +0.51% | -0.02% | +0.53% | +0.50% | 95.4% | +0.29% | yes |

### Hold H5 (main)

| Set-up | Buys | Share bought | Mean of buys after costs | Mean of every release (a) | Buys less (a) | 95th percentile of random picks (b) | Random draws beaten | Buys less SPY | Above both marks |
|---|---|---|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 alone | 199 | 44.2% | +1.14% | +0.17% | +0.97% | +0.81% | 99.3% | -0.58% | yes |
| Grok 4.7 alone | 257 | 57.1% | +0.91% | +0.17% | +0.73% | +0.69% | 99.1% | -0.74% | yes |
| Kimi K3 alone | 283 | 62.9% | +0.92% | +0.17% | +0.74% | +0.61% | 99.7% | -0.72% | yes |
| Claude Opus 5.5 alone | 202 | 44.9% | +0.99% | +0.17% | +0.81% | +0.80% | 98.3% | -0.77% | yes |
| middle of the three small readers | 247 | 54.9% | +1.06% | +0.17% | +0.88% | +0.68% | 99.8% | -0.58% | yes |
| cascade: small readers, Opus where they disagree | 217 | 48.2% | +1.06% | +0.17% | +0.88% | +0.75% | 99.6% | -0.65% | yes |
| plain rule: buy when the stock opened up at least 2.0% | 158 | 35.1% | +0.96% | +0.17% | +0.79% | +0.97% | 94.2% | -0.88% | no |

### How much the readers agree

- The three small readers gave the same buy-or-skip answer on 75.1% of releases (Fleiss' kappa 0.67).
- Rank correlation of scores between pairs of readers: 0.74 to 0.85. So the six rows above are close to one result seen six times, not six separate confirmations.
- Where the small readers agreed, the strong reader agreed with them on 94.3% of 334 releases.
- Answers set to zero because the reader said it remembered the move: 2 in all (claude_opus_5_5 2, claude_sonnet_5_5 0, grok_4_7 0, kimi_k3 0).

### The choice

- Rule, fixed before: the highest H5 mean less (a) among set-ups that buy between 20.0% and 60.0% of releases. Qualified: claude_sonnet_5_5, grok_4_7, claude_opus_5_5, middle, cascade.
- Chosen: Claude Sonnet 5.5 alone. It alone reads the held-back half, once.

### The chosen set-up at H5, by list (reported, not judged)

| List | Buys | Mean of buys after costs | Mean of every release (a) | Buys less (a) | Random draws beaten | Buys less SPY |
|---|---|---|---|---|---|---|
| S&P 500 | 74 | +1.49% | +0.83% | +0.66% | 91.0% | +0.08% |
| S&P MidCap 400 | 61 | +1.04% | +0.17% | +0.87% | 90.6% | -0.86% |
| S&P SmallCap 600 | 64 | +0.85% | -0.48% | +1.33% | 92.8% | -1.07% |

Buys less (a) at H5 with costs at 0 times: +0.97%, 0.5 times: +0.97%, 2 times: +0.97%. Costs barely move it because (a) pays the same costs.

## What the design sample does and does not show

- At the five-day hold every set-up's buys did better than buying every release and better than 95% of random picks. At the one-day hold none did.
- The buys still did worse than holding SPY over the same days at H5 (-0.58% for the chosen set-up). SPY rose +1.72% on average over those holds while the average release rose +0.17%. The reader picked the better releases among a group that lagged the index. So what is shown here is choosing, not yet a trade that beats holding the index.
- A plain rule with no reading at all, buying when the stock opened up at least 2.0%, did about as well: buys less (a) of +0.53% at H1 and +0.79% at H5, against +0.02% and +0.97% for the chosen reader. The held-back half reports the plain rule beside the reader, so it will show whether reading adds anything to watching the opening price.
- This sample was used to choose among six set-ups. The best of six looks better than it is. The plan says so, and that is why this half is not the judge.
- 450 releases from April to July 2026 are one earnings season and a half. Releases cluster in the same weeks and share the market's move.

## What is still to come

- The chosen set-up reads the held-back half, 2,146 releases, the later part of the window that ends 2026-11-20. Its answers are hashed and pushed before any held-back price is read.
- The last held-back exits fall five trading days after the last release, so some of those prices do not exist yet. The held-back half is scored once, after those days have traded and the prices are collected again.
- Pass mark, fixed in the plan: at H5, the buys beat buying every release and the 95th percentile of random picks, with at least 100 buys. A pass means worth trying on the practice desk with pretend money. It does not mean it makes money.

