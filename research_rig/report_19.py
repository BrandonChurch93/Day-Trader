"""Print the Replay 19 result page from its saved JSON. Never open market data."""
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

RESULT = Path(__file__).with_name("results_19.json")
# Measured on invented bars before freeze and recorded in the frozen plan, not in the real result.
CALIBRATION_PASSES = {0: 0, 10: 0, 20: 3, 40: 19}


def pct(value):
    return f"{value:+.2%}"


def stamp(value):
    return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M UTC")


def cells(book):
    if "refusal" in book:
        return f"{book['refusal']} | not scored | not scored"
    return f"{pct(book['whole']['net'])} | {book['whole']['sharpe']:+.3f} | {pct(book['after_cme']['net'])}"


def render(r, digest):
    p, o, job = r["policy"], r["outcome"], r["job"]
    pair, marks, placebo = o["main"]["pair"], o["marks"], o["placebo"]
    sharpe = pair["whole"]["sharpe"]
    above = sum(s is not None and s > sharpe for s in placebo["sharpes"].values())
    ties = sum(s is not None and s == sharpe for s in placebo["sharpes"].values())
    n_start = len(placebo["sharpes"]) + 1
    positive = [y for y in pair["full_years"] if pair["years"][y] > 0]
    all_weeks = f"{pair['traded_weeks']} of {pair['scheduled_weeks']}"
    post_weeks = f"{pair['post_cme_traded_weeks']} of {pair['post_cme_weeks']}"
    roles = placebo["zero_volume_touched_by_role"]
    rule = f"{p['hold_hours']}-hour momentum"
    cost = p["judged_bps"]
    verdict = "passed" if o["passes"] else "did not pass"
    plan = "[frozen plan](../../research_rig/PREREG_19_monday_asia.md)"

    print(f"""# Replay 19: the Monday Asia window

MEASURED. The equal-weight bitcoin and ether rule **{verdict}**. It met **{sum(marks.values())} of {len(marks)} marks** at {cost} bps per side. The account returned {pct(pair['whole']['net'])} net, with a Sharpe of {sharpe:+.3f}.

STATED. [Concretum Group](https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/) describes an approximate window for its private trend benchmark but gives no entry, exit or directional signal. This replay uses our stand-in and does not test their models. All dates were already viewed, {p['first_date']} through the {p['last_date']} UTC close. There is no held-back period.

STATED. The local {plan} commit and [ledger row {job['ledger']}](../../research_rig/TRIAL_LEDGER.md) were in place before the run at {stamp(job['started_utc'])}. GitHub pushes were refused before the run, so the public GitHub timestamp is necessarily after the run, not evidence of a public freeze beforehand.

MEASURED. The first invocation stopped before the lock on a zero-volume trade candle. It never scored a book or consumed the run. The dated amendment in the {plan} let zero-volume candles mark the value of an open position, but kept them out of the judged signal, entry and exit. Opens and closes still had to be finite and positive, and trade volume finite and nonnegative.

## Preregistered marks

STATED. At Sunday {p['sunday_hour_ny']:02d}:00 New York time, compare the last fully closed candle with the close {p['hold_hours']} hours earlier. Go long if it rose, short if it fell, and stay flat on a tie. Fill at the next hourly open and exit {p['hold_hours']} hours later. The pair starts each window in equal parts, with no leverage at entry.

| Mark | Measured | Verdict |
|---|---:|---|
| Net Sharpe of at least {p['min_sharpe']:.1f} | {sharpe:+.3f} | {'met' if marks['sharpe'] else 'not met'} |
| Positive in at least {p['min_positive_years']} full years | {len(positive)} of {len(pair['full_years'])}, {', '.join(positive) or 'none'} | {'met' if marks['full_years'] else 'not met'} |
| Positive after the CME cutoff | {pct(pair['after_cme']['net'])} | {'met' if marks['post_cme'] else 'not met'} |
| Above the {p['placebo_percentile']}th percentile of shifted windows | {sharpe:+.3f} vs. {placebo['percentile']:+.3f} | {'met' if marks['placebo'] else 'not met'} |
| Trade at least {p['min_trade_pct']}% of windows overall and after the cut | {all_weeks} overall; {post_weeks} after | {'met' if marks['breadth'] else 'not met'} |

MEASURED. The rule ranked **{above + 1}th of {n_start} start hours**, best to worst. Of the {placebo['defined']} defined shifted Sharpes, {above} were higher and {ties} tied. No shifted book failed or had an undefined Sharpe. The shifted windows overlap, so the rank is not a significance test.

## Year by year

MEASURED. The pair's net returns below use {cost} bps per side and include funding. The last year is partial.

| Year | Net return |
|---|---:|""")
    for y, value in pair["years"].items():
        label = y if y in pair["full_years"] else f"{y}, partial"
        print(f"| {label} | {pct(value)} |")
    print(f"""
MEASURED. The pair's largest fall was {pair['largest_fall']:.2%}. In percentage points of starting equity, price changes contributed {100 * pair['price_pnl']:+.2f}, funding {100 * pair['funding_pnl']:+.2f} and fees {100 * -pair['fees']:+.2f}. The loss was not just fees.

MEASURED. The pair returned {pct(pair['before_cme']['net'])} before the split (Sharpe {pair['before_cme']['sharpe']:+.3f}) and {pct(pair['after_cme']['net'])} after it (Sharpe {pair['after_cme']['sharpe']:+.3f}). The split is {stamp(p['cme_cut'])}, as scheduled in the [CME Globex notice](https://www.cmegroup.com/notices/electronic-trading/2026/05/20260511.html). The later period covers only {pair['post_cme_weeks']} scheduled windows and does not show that the CME change caused the loss.

## Shown only

MEASURED. The comparisons below are not extra marks. The [cheaper fee](60_us_venue_costs_checked.md) is a sensitivity, not evidence of a real fill at that price.

| Variant | Net return | Sharpe | Net after the CME cut |
|---|---:|---:|---:|""")
    for key, label in (("BTCUSDT", "Bitcoin alone"), ("ETHUSDT", "Ether alone")):
        print(f"| {label}, {cost} bps per side | {cells(o['main'][key])} |")
    for fee in p["shown_bps"]:
        unit = "bp" if fee == 1 else "bps"
        print(f"| Pair {rule}, {fee} {unit} per side | {cells(o['shown_costs'][str(fee)]['pair'])} |")
    for key, label in (("one_candle", "One-candle direction"), ("long", "Always long in the window")):
        print(f"| {label}, {cost} bps per side | {cells(o['shown_signals'][key]['pair'])} |")
    print(f"""
MEASURED. Price changes added to both coins' always-long books. The plain reading is that always-long gained because bitcoin and ether rose during its holds over this period, not that Monday has an edge. The replay did not test whether always-long in this window beat holding continuously or taking the same long exposure at other hours.

## Zero-volume candles
""")
    for symbol, book in o["zero_volume_trade_candles"].items():
        print(f"- {symbol}: {book['count']} at {', '.join(stamp(x) for x in book['utc_open_stamps'])}.")
    print(f"""
MEASURED. None supplied a judged signal or fill. The shifted windows touched one in {placebo['zero_volume_touched_windows']} cases: {roles['signal']} as a signal, {roles['entry']} at entry and {roles['exit']} at exit.

## Made-up arithmetic check

MEASURED on invented bars before the run. The {plan} records these joint passes out of {p['calibration_seeds']} seeds at each planted gross edge:

| Gross plant per trade | Seeds clearing all marks |
|---|---:|""")
    for bps in p["calibration_edges_bps"]:
        print(f"| {bps} bps | {CALIBRATION_PASSES[bps]} of {p['calibration_seeds']} |")
    print(f"""
STATED. Under this invented noise, the marks usually caught the {p['calibration_edges_bps'][-1]} bps edge and seldom caught the {p['calibration_edges_bps'][-2]} bps edge. This is an arithmetic guide, not a power estimate or a minimum detectable edge for real prices.

UNKNOWN. This all-viewed replay does not establish a live fill or a repeatable window edge. The [saved result](../../research_rig/results_19.json) is bound to local commit `{job['commit']}`, the ledger and the archive manifest. Its SHA-256 is `{digest}`. The [report script](../../research_rig/report_19.py) reads only the saved result.
""", end="")


if __name__ == "__main__":
    raw = RESULT.read_bytes()
    render(json.loads(raw), sha256(raw).hexdigest())
