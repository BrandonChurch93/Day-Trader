# Decision autopsy of TM01 to TM04

What it is: a script that reads every written reason the AI traders gave in the finished and already scored time machine plans TM01, TM02, TM03 and TM04, sorts each reason into a fixed category, and joins it to what happened next. The findings are in `docs/research/59_why_the_ai_traders_lost.md`.

This is an after-the-fact look at finished tests. It is not a test: it has no pass mark, it changes no result already scored, and anything it suggests is a hypothesis for a new test on months not yet traded.

## How to rerun

From the repo root, one job at a time:

```
nice -n 10 python3 timemachine/autopsy/autopsy.py
```

About 20 seconds and under 100 MB. It writes `timemachine/autopsy/autopsy_results.json` and prints any label id it could not find in the run folders and any quote that fails a check.

The paths are set in one place, `timemachine/autopsy/settings.py`, and can be changed on the command line or in the environment:

| What | Flag | Environment | Default (the off-repo working area used on 2026-11-25) |
|---|---|---|---|
| Run folder holding the session folders | `--runs` | DT_AUTOPSY_RUNS | /home/user/workspace/rig/tm_runs |
| Recorded tape (sqlite) | `--tape` | DT_AUTOPSY_TAPE | /home/user/workspace/rig/tm_store/tape.sqlite |
| Results file written | `--out` | DT_AUTOPSY_OUT | autopsy_results.json in this folder |

Tests, on made-up records only: `python3 timemachine/autopsy/test_autopsy.py`.

## What it reads

- From the run folder, read only: the session folders TM01-B01-*, TM02-B02-*, TM03-D01-*, TM04-D02-* and the random twin folders TWIN-TM01-* and TWIN-TM02-*. In each: progress.json (every answer and its reason), result.json (orders, fills, closed trades, settings) and, for TM02, the packets. Folders whose names start with TM06 or VOID are never opened.
- From the tape, read only: 1-minute closes, kept in memory. Every price change uses the last minute at or before each time.
- From this folder: `timemachine/autopsy/categories.md` (the categories, fixed before any outcome was joined), `timemachine/autopsy/classify.py` (the word rules), `timemachine/autopsy/labels_by_hand.jsonl` (the analyst's labels), `timemachine/autopsy/hand_checks.json` (blind sample ids, the blind relabel, two rule checks, the contradiction check and two hand verdicts) and `timemachine/autopsy/quotes.json` (the 12 quotes).

## No news text in the repo

Vendor news text is never committed. The labels and hand checks carry only ids, labels, who and when; the script joins them to the stored texts by id at run time. The results file holds no answer text except the 12 quotes, and the script checks each quote: it must be found word for word in its session, be under 40 words, contain no quoted title, and share no run of five words with any headline or summary in that session's packets.

## Files

| File | What it does |
|---|---|
| `timemachine/autopsy/autopsy.py` | The main script: counts, labels, round trips, prices before and after, twins, TM03 and TM04 tables, label checks, record faults, quote checks |
| `timemachine/autopsy/core.py` | Pure helpers: table cells and the under-30 rule, spread per fill, round trips from the desk's closed list, the label id check |
| `timemachine/autopsy/load.py` | Reads answers and fills from the session folders |
| `timemachine/autopsy/prices.py` | Reads minute prices from the tape, read only |
| `timemachine/autopsy/classify.py` | The word rules that place a text in a category, and the buy flags |
| `timemachine/autopsy/settings.py` | The run folder, tape and output paths |
| `timemachine/autopsy/test_autopsy.py` | Tests on made-up records |
