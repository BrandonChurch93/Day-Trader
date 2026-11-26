# practice/: the practice desk

Traders use pretend money at live prices in one Alpaca practice account. Each trader has its own pretend budget and its own books. The owner's screen shows every trade and each trader's wins and losses. This is the judge: a method counts when it does well here, not when a replay says so.

Two kinds of trader work here:

- Fixed rules. Plain functions in `rules.py`, worked out from prices by the program.
- AI traders. Each follows a method card in `traders/` and decides by writing a pick (`picks.py` has the form). 

The program in `trader.py` is the hands, not the head. It reads decisions, keeps each trader inside its budget, places the order, enforces exits and writes down what happened. No model runs inside it. The plan in force is `PLAN_02_ai_desk.md`.

## Files

| File | What it is |
|---|---|
| `PLAN_02_ai_desk.md` | The plan in force: how a decision becomes an order, what is written down, when a trader stops, what the desk cannot do yet |
| `trader.py` | The program. One run reads the broker, rebuilds every trader's books, checks exits, places new decisions, writes the records and the summary for the owner's screen |
| `picks.py` | The form a pick must take, and the check that it does |
| `books.py` | Works out each trader's cash, holdings, closed trades, wins and losses from the broker's own order list |
| `broker.py` | The only code that talks to the broker. A short fixed list of things it can do, practice address only |
| `market.py` | Prices: daily history for the rules, live quotes with their own time stamps for orders |
| `rules.py` | The two fixed rules, P1 on bitcoin and the ten-month rule T1 on a total market fund |
| `traders.json` | The traders on the desk now |
| `traders/` | `ROSTER.md` and one method card for each AI trader |
| `gate.py` | The criteria gate: turns a scout's candidate into a pick, or a named refusal, by fixed criteria on a card. See below |
| `criteria/` | One criteria card per method (JSON), the scout brief `SCOUT_BRIEF.md`, and two EXAMPLE cards for the tests |
| `test_gate.py` | Checks for the gate with made-up bars, a pretend broker and no network |
| `test_trader.py`, `test_review.py`, `test_market.py` | Checks with a pretend broker and no network. The timer runs them before every real run. `test_review.py` was written by an outside reviewer to break the order code |

The timer is `.github/workflows/practice-trader.yml`. GitHub's own schedule in that file did not fire in its first two hours, so each run also starts the next one itself after the interval, unless a newer run has already begun. Every setting is in `config/thresholds.yaml`, in the keys that start with `practice_`.

## Working here

- After any change run all three test files. Each must print that every check passed.
- A new trader, or a changed card, model or setting, is a new attempt: write its ledger row (`research_rig/TRIAL_LEDGER.md`) before it trades.
- The broker key lives only in the repo's secrets. Do not put a key anywhere a model can read it, and do not run `trader.py` with a real key by hand.
- The program has no code to cancel all orders, close all holdings or change the account, and it only knows the practice address. The tests fail if that changes.
- Do not edit the record lines on the `practice-records` branch. They are the evidence.

## Running it

```
python3 practice/test_trader.py && python3 practice/test_review.py && python3 practice/test_market.py && python3 practice/test_gate.py
```

With no key in the environment, `python3 practice/trader.py` sends nothing and writes "waiting for key". That is safe to run anywhere.

## The criteria gate

The loop: scouts look widely and file candidates; plain code checks each candidate against a fixed card; `trader.py` places the pretend trade and sells on the card's exits. No model decides size, entry or exit.

A card, `criteria/<name>.json`, has these fields. Every number on it is the name of a key in `config/thresholds.yaml`, never the number itself.

| Field | What it says |
|---|---|
| `id`, `title`, `trader` | The card's id (the inbox folder), plain words, and the desk trader its picks go to |
| `status`, `registered`, `tradable`, `ledger_row` | `EXAMPLE` cards are never registered or tradable. A tradable card must be registered and name its ledger row. The lead agent registers real cards |
| `market` | `kind` (crypto or stock) and the symbols the card takes |
| `candidate` | The kinds of event it takes, and the key for how old an event may be |
| `timeframe` | The bars the checks use: `1Min`, `1Hour` or `1Day` |
| `entry` | Named checks with their parameter keys: `enough_bars`, `fell_at_least`, `rose_at_least`, `volume_above_mean`, `close_above_high`, `close_above_mean` |
| `size` | `fixed_usd` and its key, the only size rule so far |
| `exit` | Keys for `target` and `stop` (shares of the reference close) and `hold_minutes` |
| `costs` | Keys for fee and slippage per side, in basis points, written with every decision and charged in replays |
| `pick_life_minutes` | Key for how long the pick stays valid |

`gate.decide(candidate, card, now, prices, settings)` checks the candidate's form, the symbol, the event kind and its age, then asks the price source for bars and keeps only those complete at `now`. It works out each entry check from those bars. The reference price is the last complete close; stop, target and time limit come from it and the card. It returns a pick in the `picks.py` form, or a refusal naming the check that failed. `gate.gate()` does the same and appends the decision, with the card's fingerprint, the settings read, the candidate as filed and the bars used, to a decision log; `gate.why(log)` lists what it bought and what it turned down, with the reason.

The price source is any object with `bars(symbol, timeframe, start)`. `LivePrices(get)` reads through `market.py`; `PastPrices(bars)` serves stored or made-up bars, so `gate.replay()` can run a month of candidates at their own times. Bars after `now` never count, whatever the source returns. `gate.simulate_exit()` walks a replayed pick to its stop, target or time limit; live, `trader.py` checks exits about every ten minutes instead, so live fills differ.

Candidates go in an inbox, `inbox/<card id>/<candidate id>.json`, in the form in `criteria/SCOUT_BRIEF.md`. `python3 practice/gate.py check-inbox <folder>` checks every file. `gate.process_inbox()` gates each new file once and writes accepted picks to `<picks folder>/picks/<trader>/`, where `trader.py` reads them. A card that is not tradable never yields a pick there.

Not built yet: nothing runs `process_inbox` on a timer, and no inbox branch exists. Before a card trades, its trader needs a line in `traders.json` and a ledger row.

## Where things are kept

| Branch | What is on it |
|---|---|
| `main` | The code |
| `practice-picks` | Pick files, `picks/<trader id>/<pick id>.json`. AI traders write here |
| `practice-records` | What the program wrote down, under `records/`. The summary file there is what the owner's screen shows |

```
git fetch origin practice-records
git show FETCH_HEAD:records/summary.json
```

## What the owner does

1. Makes an API key for an Alpaca practice account.
2. Adds two repository secrets: `ALPACA_PAPER_KEY_ID` and `ALPACA_PAPER_SECRET_KEY`.

The next run of the timer starts the pretend trading. To stop it, remove the two secrets or disable the workflow.
