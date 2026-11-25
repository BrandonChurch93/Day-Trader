# 49. Governance votes: a first look

Status: measured 2026-11-25 18:38 UTC by a helper on the research machine. A description, not a counted test: no ledger row, no pass mark. The helper wrote down what it would measure before it read any price. Scripts, the vote list and the full yearly table are on the research machine, not in the repo.

Why: queue row 9j, kept from `docs/research/43_crypto_events_evidence_checked.md` as the one cheap look among dated crypto events.

## In plain words

- Parked. There is nothing here to build a test on.
- Of the 23 coins in the second price store, only 3 have a verified vote space on Snapshot, and one coin, AAVE, has 933 of the 945 votes. This is a look at one coin, not at a method.
- After costs, buying when a vote opened or closed lost against bitcoin at most holding times, and the sign changes from year to year.

## What was measured

- MEASURED: 945 closed votes from 2022 on, from the free [Snapshot API](https://docs.snapshot.box/tools/api): AAVE 933, ENA 8, BNB 4. BNB's votes all fall before its prices start. The spaces were matched to coins from each project's own pages ([Aave](https://aave.com/docs/ecosystem/governance), [BNB Chain](https://docs.bnbchain.org/bnb-smart-chain/governance/temp-check/), [Ethena](https://docs.ethena.fi/protocol-overview/governance)).
- Entry at the next daily open after the vote opened or closed. Return is the coin's less bitcoin's. Cost shown is 30 bps a round trip. The yardstick is the same coin on 1,000 random days in the same quarter.
- "Most ballots" means the top fifth for that coin among votes already closed at the time, so nothing later is used. All 191 such votes are AAVE in 2022 and 2023.

Each cell is before costs / after costs / the same coin on random days before costs, in hundredths of a percent.

| Group | Votes | 1 day | 3 days | 7 days |
|---|---|---|---|---|
| After a vote opens | 937 | +10.3 / -19.7 / -10.4 | +33.9 / +3.9 / -4.6 | -13.4 / -43.4 / +24.7 |
| After a vote closes | 938 | -11.4 / -41.4 / -10.5 | -26.3 / -56.3 / -5.4 | -32.5 / -62.5 / +24.0 |
| Closes with the most ballots | 191 | -27.0 / -57.0 / -15.7 | -97.9 / -127.9 / -11.6 | -135.0 / -165.0 / -0.5 |

After costs, by year, at 1 / 3 / 7 days:

| Year | After opens | After closes | Most ballots |
|---|---|---|---|
| 2022 | -28 / -64 / -154 | -62 / -73 / -115 | -42 / -79 / -39 |
| 2023 | +22 / +36 / -74 | -47 / -81 / -129 | -65 / -155 / -235 |
| 2024 | -13 / +15 / +69 | -29 / +28 / +76 | none |
| 2025 | -109 / -102 / -179 | -34 / -130 / -123 | none |
| 2026 | -3 / +163 / +143 | -40 / -61 / -58 | none |

The one cell above zero after costs in the first table (three days after a vote opens, +3.9) is -13.0 without 2026.

## Gaps

- 20 of 23 coins had no verified vote space on Snapshot. Votes held on other systems, and votes removed since, are UNKNOWN.
- The votes bunch: about six in ten of the one-day rows share a coin and day with another vote, and nearly all seven-day windows overlap another. The random-day yardstick is a description, not a test of chance.
- Daily bars only. What a coin did in the hours after a vote ended is not answered here.
- The number of ballots is not how close a vote was. A close-vote question would be a different, separately planned look with more vote systems. It is not in the queue.
