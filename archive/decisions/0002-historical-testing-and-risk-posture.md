# 0002 - Historical testing and risk posture

Date: 2026-11-24
Status: the first section is what the owner said. Everything after it is proposed by the research team and is not an owner decision.

## What the owner said, 2026-11-24

- "He doesn't need to collect modern evidence. We have the entire past of the Internet that we can scour through."
- "I don't necessarily want to play it safe. Either goal is to find a nice median."
- "I'm not against putting a small amount in my portfolio into moonshots if the moonshot actually makes sense and has a reason behind it."

## Proposed: how historical data is used

| Use | Historical data valid? | Condition |
|---|---|---|
| Rule-based strategies (trend, volatility sizing, scanners) | Yes, all available history | Final slice held back and tested once; every variant tried is counted; realistic costs. [STATED] our recommendation |
| Comparing models (Fable 5.2 against others) | Yes, but only dates after each model's training cutoff | Search and browsing off; the model sees only documents published before each decision time. [STATED] our recommendation |
| Model backtests on dates before the cutoff | No | The model has already read what happened next. Agent results fell 51% to 62% past the cutoff ([Profit Mirage](https://arxiv.org/html/2510.07920)). [MEASURED] |

Fable 5.2, Opus 5.5, Sonnet 5.5 and Haiku 5.5 all have a June 2026 training cutoff ([Anthropic models overview](https://docs.anthropic.com/en/docs/about-claude/models/overview)). [MEASURED] That leaves July 2026 onward as history none of them has seen, so the model comparison can start as a replay and does not need to wait for new market days. Cutoffs for non-Anthropic models must be checked individually before they join the comparison. [UNKNOWN]

Note added 2026-11-25 09:10 UTC. The two rows above about comparing models, and the words "the model comparison can start as a replay", conflict with `AGENTS.md` hard rule 7, which ends: "Only forward paper or shadow results count." `AGENTS.md` wins. Until the owner says otherwise, a replay of a model on past dates, even dates after its training cutoff, is not counted as evidence. Pilot 02 was such a replay; it was reported as inconclusive and is not used as evidence for or against any model. The conflict is question 19 in `archive/decisions/morning_list_2026-11-25.md`.

A pattern found in history is a hypothesis. Published predictors earned 58% less after publication ([McLean and Pontiff](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12365)). [MEASURED] The held-back slice is how we tell a real pattern from a fitted one. It is a test of truth, not a safety measure.

## Proposed: core plus a moonshot sleeve

- Core: the rule-based strategies from playbook 01 and 02, run by the service.
- Moonshot sleeve: a capped share of the portfolio for high-risk, high-payoff positions. [STATED] our recommendation
- Every moonshot needs a written thesis before entry: the reason, the catalyst and its date, what would prove it wrong, position size, and the assumption that the whole position can go to zero.
- Models research and write the thesis and the case against it. The owner makes the buy decision. This keeps a person in the loop for each personalised buy call, which the provider policies in playbook 05 call for.
- Sleeve losses never get refilled from the core automatically.
- AGENTS.md rule 10 still applies: no options, leveraged ETFs, perpetual futures, margin or shorting inside the sleeve unless a later decision record changes it.

## Open owner decisions

Each is put to the owner one at a time. Values named by key live in `config/thresholds.yaml`, where `recommended` is a suggestion and never a value to use.

| # | Decision | Recommended pick | Reason | What it costs him |
|---|---|---|---|---|
| H | Sleeve size | The `recommended` value of `moonshot_sleeve_share` | Large enough to matter if one works, small enough that losing all of it leaves the core intact | That share of the account is expected to be volatile and can go to zero |
| I | Largest single moonshot | The `recommended` value of `moonshot_max_position_share` | Leaves room for several ideas, so one wrong thesis does not end the sleeve | A single strong idea is held smaller than he may want |
| J | What the sleeve may hold | Plain stocks and spot crypto only | The loss is capped at what was put in | No options, so no cheap leveraged bets on a catalyst |
