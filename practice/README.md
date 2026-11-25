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
python3 practice/test_trader.py && python3 practice/test_review.py && python3 practice/test_market.py
```

With no key in the environment, `python3 practice/trader.py` sends nothing and writes "waiting for key". That is safe to run anywhere.

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
