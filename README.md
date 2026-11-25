# Day-Trader

An AI-assisted trading system for US stocks and crypto. Status: research complete, nothing built, no accounts or keys connected. Last updated 2026-11-24.

## Read in this order

1. `AGENTS.md` - rules every agent and contributor follows. One page.
2. `docs/playbook/00_START_HERE.md` - the whole picture in about two pages.
3. `docs/quality/00_READ_FIRST.md` - the owner's quality bar and build method.
4. `docs/playbook/01..06` - condensed decisions per topic. This is the layer agents load by default.
5. `docs/research/01..13` - full reports with every source. Open only when a playbook line points there. 09 is brokers and venues, 10 is historical data and practice accounts, 11 is the AI trader test design, 12 is the first replay results, 13 is the high-risk sleeve evidence.
6. `docs/decisions/` - dated record of choices, the audits of the playbook and the source checks.

## What the evidence says, in five lines

- Most retail day traders lose money after costs, and most LLM agents given real or simulated money have lost too.
- The ideas with the best evidence are slower than day trading: multi-day trend following with volatility-based sizing, held overnight.
- Language models are useful for reading news, filings and transcripts, for writing and reviewing strategy code, and for reviewing trades. They are poor at predicting prices from numbers.
- So the product is a small always-on rules-based trading service. The AI sits beside it as a researcher and reviewer and never touches the order path.
- Cheap-model screening with rare escalation to a top model is the right cost design. The list-price comparison lives in `docs/playbook/05_perplexity_and_costs.md`.

## Layout

```text
Day-Trader/
├── AGENTS.md              rules for agents
├── README.md
├── config/                every threshold and owner number, once
└── docs/
    ├── playbook/          condensed, decision-only (default reading)
    ├── quality/           the owner's quality bar and build method
    ├── research/          full cited reports (audit trail)
    └── decisions/         decision log and playbook audits
```

Code directories (`src/`, `config/`, `tests/`, `infra/`) are specified in `docs/playbook/06_architecture_and_build.md` and get created in Phase 1.

## Evidence labels

- MEASURED: independent empirical data, official rule text, or a published price page.
- STATED: claimed by a vendor, author or promoter and not independently verified.
- UNKNOWN: could not be verified. Treat as a thing to test, not a fact.

This repository is research and engineering documentation, not financial advice.
