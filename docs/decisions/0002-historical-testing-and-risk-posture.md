# 0002 - Historical testing and risk posture

Date: 2026-11-24
Status: owner direction recorded; items marked OWNER still need a number.

## Owner direction

- Use historical data rather than waiting to collect new evidence wherever that is valid.
- Do not optimise for safety alone. Aim for a middle risk level.
- A small part of the portfolio may go to moonshots, but only when the moonshot has a stated reason behind it.

## How historical data is used

| Use | Historical data valid? | Condition |
|---|---|---|
| Rule-based strategies (trend, volatility sizing, scanners) | Yes, all available history | Final slice held back and tested once; every variant tried is counted; realistic costs. [STATED] our recommendation |
| Comparing models (Fable 5.2 against others) | Yes, but only dates after each model's training cutoff | Search and browsing off; the model sees only documents published before each decision time. [STATED] our recommendation |
| Model backtests on dates before the cutoff | No | The model has already read what happened next. Agent results fell 51% to 62% past the cutoff ([Profit Mirage](https://arxiv.org/html/2510.07920)). [MEASURED] |

Fable 5.2, Opus 5.5, Sonnet 5.5 and Haiku 5.5 all have a June 2026 training cutoff ([Anthropic models overview](https://docs.anthropic.com/en/docs/about-claude/models/overview)). [MEASURED] That leaves July 2026 onward as history none of them has seen, so the model comparison can start as a replay now and does not need weeks of waiting. Cutoffs for non-Anthropic models must be checked individually before they join the comparison. [UNKNOWN]

A pattern found in history is a hypothesis. Published predictors earned 58% less after publication ([McLean and Pontiff](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12365)). [MEASURED] The held-back slice is how we tell a real pattern from a fitted one; it is a test of truth, not a safety measure.

## Risk posture: core plus a moonshot sleeve

- Core: the rule-based strategies from playbook 01 and 02, run by the service.
- Moonshot sleeve: a capped share of the portfolio for high-risk, high-payoff positions. [STATED] our recommendation
- Every moonshot needs a written thesis before entry: the reason, the catalyst and its date, what would prove it wrong, position size, and the assumption that the whole position can go to zero.
- Models research and write the thesis and the case against it. The owner makes the buy decision. This keeps a person in the loop for each personalised buy call, which the provider policies in playbook 05 call for.
- Sleeve losses never get refilled from the core automatically.
- AGENTS.md rule 10 still applies: no options, leveraged ETFs, perpetual futures, margin or shorting inside the sleeve unless a later decision record changes it.

## OWNER numbers still open

- Sleeve size as a share of the trading account.
- Largest single moonshot position.
- Whether the sleeve may use anything beyond plain stocks and spot crypto.
