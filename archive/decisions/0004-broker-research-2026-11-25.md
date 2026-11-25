# 0004 - Broker and venue research, and what it changes

Date: 2026-11-25 (UTC). Evening of 2026-11-24 in Idaho.
Status: proposed by the research team. Nothing here is an owner decision. The owner asked for this research on 2026-11-24: "Do research on the brokers for both stock and crypto the comprehensive research."

## What was done

- Six researchers each wrote a report from primary pages. They are in `docs/research/09_raw/`.
- Four fresh checkers on three different models re-opened the primary pages for 55 load-bearing figures. Their tables are in `docs/research/09_raw/check/`. This is hand-over 11 in `archive/quality/04_research_to_build.md`.
- We measured four venues' public order books for 30 minutes. Method and table are in `docs/research/09_brokers_and_venues.md`.
- The corrected summary is `docs/research/09_brokers_and_venues.md`.

## What the check found

| Outcome | Count |
|---|---|
| Held with both checkers | 38 |
| Wrong | 1 |
| Overstated or missing a material detail | 12 |
| Not found in any source | 3 |
| Could not be opened | 1 |
| Total | 55 |

The one wrong figure was the Coinbase Advanced entry fee. The reports used 0.40% and 0.60%, which belong to a different Coinbase product. The true entry rates are 0.50% maker and 0.90% taker. An earlier message to the owner said 48 of 55 held. That count was wrong and was corrected to 38 in the thread the same day.

## Changes made to existing files

| File | Change | Why |
|---|---|---|
| `docs/playbook/04_brokers_data_rules.md` | Coinbase row now 0.50% and 0.90%, MEASURED. Binance.US fee row added. Alpaca duplicate-order row added: HTTP 422, not 409. Alpaca key facts added. Kraken sub-account note. The "do not trade crypto often on" line now lists the venues by measured fee | Check results |
| `docs/playbook/02_crypto_what_works.md` | Coinbase Advanced row changed from UNKNOWN to 180 bps taker round trip, MEASURED | Check result |
| `docs/playbook/00_START_HERE.md`, `docs/playbook/05_perplexity_and_costs.md` | Perplexity policy dating fixed. The version in force today is July 8, 2025 and has no human-oversight exception. The January 1, 2027 version adds those words | Check result |
| `archive/decisions/0001-starting-decisions.md` | Rows B and C carry the new recommended picks. Both are still open owner decisions | Research 09 |
| `README.md` | Research index line now covers 01 to 13 | New files |

## Recommended picks, for the owner to confirm, change or decline

| # | Decision | Recommended pick | Reason | What it costs him |
|---|---|---|---|---|
| B | Stock broker | Alpaca, individual account | Free practice account on the same connection as live, keys that run unattended, no minimum, the old $25,000 rule switched off | Free data covers one exchange; full data is a paid monthly plan; keys cannot be locked to one address |
| C1 | Practice venue for stocks and crypto | Alpaca practice account | One connection, needs only an email | Practice fills differ from real fills in known ways (research 10) |
| C2 | Live crypto venue | Not chosen yet. Decide at the live gate. Front-runner on cost is Binance.US with conditions. Fallback is spot bitcoin and ether funds in the Alpaca account | Fees separate the venues. Our replay shows the result depends on them (research 12) | Waiting costs nothing while trading is practice only |

## What the owner is not being asked to approve here

Opening any account, creating any key, moving any money, or any live trading.
