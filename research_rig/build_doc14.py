"""Builds docs/research/14 from results_02.json and pilot/decisions.jsonl. Run after score_02.py."""
import json, datetime, collections, numpy as np
o=json.load(open("results_02.json")); R=o["runs"]
runs=collections.defaultdict(list)
for l in open("pilot/decisions.jsonl"):
    r=json.loads(l); runs[r["run"]].append(r)
NAME={"r_fable_a":"Claude Fable 5.2, run A","r_fable_b":"Claude Fable 5.2, run B","r_fable_c":"Claude Fable 5.2, run C","r_opus":"Claude Opus 5.5","r_sol":"GPT-6.2 Sol","r_neon":"Gemini Neon","P1":"Trend rule P1 (no AI)","hold":"Hold both coins"}
ORDER=["r_fable_a","r_fable_b","r_fable_c","r_opus","r_sol","r_neon"]
pc=lambda x,d=1: f"{x*100:+.{d}f}%"
t1="| Run | Net return | Largest drop | Time invested | Trades | Cost paid | Sharpe |\n|---|---|---|---|---|---|---|\n"
for k in ["P1","hold"]+ORDER:
    s=R[k]; t1+=f"| {NAME[k]} | {pc(s['net_return'])} | {pc(s['max_drop'])} | {s['exposure']*100:.0f}% | {s['trades']} | {s['cost_paid']*100:.2f}% | {s['sharpe']:.2f} |\n"
t2="| Run | Average daily gap to P1 (bps) | 90% range of that gap (bps) | Does the range exclude zero? | Same holding as P1 (share of days) | Correlation of holdings with P1 | Shuffle percentile |\n|---|---|---|---|---|---|---|\n"
for k in ORDER:
    s=R[k]; lo,mid,hi=s["daily_diff_vs_P1_bps_90"]
    t2+=f"| {NAME[k]} | {s['daily_diff_vs_P1_bps_mean']:+.1f} | {lo:+.1f} to {hi:+.1f} | {'yes' if lo>0 or hi<0 else 'no'} | {s['match_P1_share']*100:.0f}% | {s['corr_weight_with_P1']:.2f} | {s['shuffle_pct']:.3f} |\n"
fs=o["fable_spread"]; pa=fs["pair_agreement"]
t3="| Run | First answer (UTC) | Last answer (UTC) | Median seconds between answers | Shortest | Longest | Reasons over 25 words |\n|---|---|---|---|---|---|---|\n"
for k in ORDER:
    v=runs[k]; t=[datetime.datetime.fromisoformat(x["server_time"]) for x in v]; g=np.diff([x.timestamp() for x in t])
    t3+=f"| {NAME[k]} | {t[0].strftime('%H:%M:%S')} | {t[-1].strftime('%H:%M:%S')} | {np.median(g):.1f} | {g.min():.1f} | {g.max():.0f} | {sum(len(x['reason'].split())>25 for x in v)} |\n"
nshuf=sum(R[k]["shuffle_pct"]>0.95 for k in ORDER); nex=[NAME[k] for k in ORDER if R[k]["daily_diff_vs_P1_bps_90"][0]>0 or R[k]["daily_diff_vs_P1_bps_90"][2]<0]
doc=f"""# Pilot 02: AI models making the calls, replayed one day at a time

Run on 2026-11-25 (UTC), the evening of 2026-11-24 in Idaho. Uses the research rig in `research_rig/`.

Status: research evidence. Proposed by research. Nothing in this file is an owner decision. No account, key or order was involved. The models traded pretend money against past prices.

Tags: every result number here is MEASURED by our own rig from Bitstamp's public price bars and the models' recorded answers. The models' descriptions of their own conduct are STATED.

## The question

If a model is shown one day of bitcoin and ether prices at a time and asked how much to hold, how does it behave next to a plain trend rule, after costs?

## Bottom line

- The result on skill is inconclusive. This was written down before the run, because 147 days cannot show skill.
- All six runs ended ahead of holding, and all six had much smaller drops than holding. So did the plain trend rule with no AI in it.
- All six runs acted like trend followers. Their holdings moved with the trend rule's holdings (correlation {min(R[k]['corr_weight_with_P1'] for k in ORDER):.2f} to {max(R[k]['corr_weight_with_P1'] for k in ORDER):.2f}).
- The three Fable runs finished at {pc(fs['net_min'])} to {pc(fs['net_max'])}. The trend rule finished at {pc(R['P1']['net_return'])}. They are not distinguishable from the rule.
- No run beat its own shuffled timing often enough to pass the shuffle mark used in replay 01. {nshuf} of 6 were above it.
- One run's 90% range against the trend rule excludes zero: {", ".join(nex) if nex else "none"}. With six runs and one short window, one such result is expected by chance about a quarter to a half of the time. It is not a finding.
- What the pilot did show: the one-day-at-a-time harness works, identical Fable runs agree with each other on about three days in four, and five of the six runs traded less often than the rule did.

## What was fixed before the run

The full text is `research_rig/PREREG_02_ai_calls_pilot.md`, written at 06:43 UTC before any model saw a price.

| Item | Fixed value |
|---|---|
| Decisions | One per day after the UTC close, 2026-06-30 to 2026-11-23. 147 decisions. Fills at the next open |
| Why these dates | They are after the knowledge cutoffs that the makers state for the Claude and GPT models, so those models should not have read these prices in training |
| Assets | Bitcoin and ether, half the account each. Long or cash only |
| Allowed answers | Hold 0, 0.25, 0.5, 0.75 or 1 of each half |
| What the model saw | Prices only: the day's bar, recent changes, the 20, 50, 100 and 200 day averages, 30 day volatility, distance from the yearly high, and its own account. No news, no web |
| Cost | 30 bps of each dollar traded, the Alpaca figure used in replay 01 |
| Time order | A local server showed one day, recorded the answer with a time stamp, then showed the next day |
| Pass mark | None. Declared inconclusive in advance |
| Trials | 6 runs, numbers 21 to 26 in `research_rig/TRIAL_LEDGER.md` |

## Results

Every run is shown. None was dropped or rerun.

{t1}
Against the trend rule P1, same dates and costs:

{t2}
How to read the second table:

- The gap is the run's daily return minus the trend rule's daily return. The range comes from resampling 10-day blocks 2,000 times.
- The shuffle percentile asks whether the timing of the run's ins and outs mattered, by putting its own spells in random order 1,000 times. Replay 01's mark for that is `replay_min_shuffle_percentile` in `config/thresholds.yaml`.

## How alike were three identical runs

The three Fable runs had the same model and the same instructions.

| Pair | Days with the same answer for a coin |
|---|---|
| A and B | {pa['r_fable_a|r_fable_b']*100:.0f}% |
| A and C | {pa['r_fable_a|r_fable_c']*100:.0f}% |
| B and C | {pa['r_fable_c|r_fable_b']*100:.0f}% |

Their final results differed by {abs(fs['net_max']-fs['net_min'])*100:.1f} percentage points. That is the size of difference that means nothing in a test like this. Any future comparison between models has to be larger than the spread between copies of one model.

## What the models said they did

All of this is STATED by the models in their own reports.

- All six described the same approach: follow the trend, use the moving averages, trade rarely because of the cost, go to cash when the trend breaks.
- All three Fable runs named the same bad trade: buying back in on November 4 after a one-day bounce. It failed the next day and cost about 3.5% to 4% of the account. Identical models made the identical mistake on the same day. Gemini Neon described that day as a trap as well.
- Fable run A reported adding bitcoin one day after saying it would wait for a higher close, and it reversed.
- Fable run B reported twice not acting on a trigger it had stated the day before.
- GPT-6.2 Sol reported using an output filter on the server's replies to hide lines. That is outside the instruction to use only the two plain commands. Its run is kept and flagged.
- Gemini Neon reported two reasons one word over the 25-word limit. The log confirms two.
- Fable run A reported one extra, unrelated command after it had finished. It did not affect any answer.

## Timing of the answers

From the server's own clock.

{t3}
Each answer came seconds after the last. That fits a model answering by hand each day. It cannot prove no model used a shortcut. The ban on scripts, web search and reading other files was an instruction, not a lock. This was listed as a weak point before the run.

## What this does not show

- It does not show that a model can trade, or that it cannot. One 147-day window in one market cannot tell skill from luck. The design work in research 11 says a fair test needs several hundred independent days and must run forward on days that have not happened yet.
- The models were handed the moving averages. That pushes them toward trend following. A different information packet could give a different picture.
- The window suited any cautious approach. Both coins rose sharply, then fell back to near where they began. Sitting in cash at the end looked wise. In a steady rise it would have looked foolish.
- Gemini Neon's knowledge cutoff was not checked. If its training data reaches into this window, its result means nothing. UNKNOWN.
- The models ran as agents with their usual setup, not through a bare connection with fixed settings. The runs cannot be pinned to an exact model build.
- The person who built the pilot (this model) saw the price path while building it.

## What research proposes from this

None of this is decided.

1. Keep the harness. It is the right shape for a fair forward test: one day at a time, answers recorded before the next day is shown, a plain rule charged the same costs next to it.
2. Do not read tonight's numbers as support for putting AI in the order path. The models matched a four-line rule. The rule costs nothing to run and never changes its mind.
3. If the owner wants the AI question answered properly, run it forward in the Alpaca practice account next to the trend rule, with the design in research 11. That needs his practice keys.
4. A cheaper and more useful next pilot: give the models something the rule does not have (dated news), and test whether that changes anything. It needs a news source with reliable time stamps, and its own written plan first.

## How to reproduce

From `research_rig/`: `python3 pilot/server.py` starts the server. `python3 score_02.py` scores the recorded answers in `pilot/decisions.jsonl` and writes `results_02.json`. `python3 build_doc14.py` writes this file. Seed 7.
"""
open("../docs/research/14_ai_calls_pilot_02.md","w").write(doc); print(len(doc))
