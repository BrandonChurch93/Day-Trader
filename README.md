# Day-Trader

An AI-assisted trading system for US stocks and crypto. Status: research complete, nothing built, no accounts or keys connected. Last updated 2026-11-24.

## Read in this order

1. `AGENTS.md` - rules every agent and contributor follows. One page.
2. `docs/playbook/00_START_HERE.md` - the whole picture in about two pages.
3. `docs/playbook/01..06` - condensed decisions per topic. This is the layer agents load by default.
4. `docs/research/01..06` - full reports with every source. Open only when a playbook line points there.
5. `docs/decisions/` - dated record of choices and the audits of the playbook.

## What the evidence says, in five lines

- Most retail day traders lose money after costs, and most LLM agents given real or simulated money have lost too.
- The ideas with the best evidence are slower than day trading: multi-day trend following with volatility-based sizing, held overnight.
- Language models are useful for reading news, filings and transcripts, for writing and reviewing strategy code, and for reviewing trades. They are poor at predicting prices from numbers.
- So the product is a small always-on rules-based trading service. The AI sits beside it as a researcher and reviewer and never touches the order path.
- Cheap-model screening with rare escalation to a top model is the right cost design. Illustrative list-price arithmetic puts it near 15 dollars a month against near 89 for running the top model on every scan.

## Layout

```text
Day-Trader/
├── AGENTS.md              rules for agents
├── README.md
└── docs/
    ├── playbook/          condensed, decision-only (default reading)
    ├── research/          full cited reports (audit trail)
    └── decisions/         decision log and playbook audits
```

Code directories (`src/`, `config/`, `tests/`, `infra/`) are specified in `docs/playbook/06_architecture_and_build.md` and get created in Phase 1.

## Evidence labels

- MEASURED: independent empirical data, official rule text, or a published price page.
- STATED: claimed by a vendor, author or promoter and not independently verified.
- UNKNOWN: could not be verified. Treat as a thing to test, not a fact.

This repository is research and engineering documentation, not financial advice.
