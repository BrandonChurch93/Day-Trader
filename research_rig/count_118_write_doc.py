"""Count 118: writes research_rig/COUNT_118_pre_earnings_reversal.md from count_118_summary.json,
count_118_events.csv and count_118_notice_sample.csv. Every figure in the doc comes from those files or from
the named keys in CFG below (paper figures are STATED, typed once here with their page)."""
import json, os, csv, math, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = dict(
    sw2014_expected_low_high_bp=65.2,    # So and Wang 2014, Table 7 p. 37, expected-date sample, Low-High RET(-1,+1)
    sw2014_expected_q1_bp=40.8,          # same table, Q1 (long side)
    sw2014_actual_low_high_bp=144.8,     # Table 2, actual-date sample
    sw2014_actual_q1_bp=81.3,            # Table 2, Q1
    sw2014_early_low_high_bp=-14.7,      # Table 7, reports that came early
    sw2014_ontime_low_high_bp=166.6,     # Table 7, on-time
    sw2014_late_low_high_bp=68.9,        # Table 7, late
    sw2014_sd_ret_bp=877.4,              # Table 1 p. 31, SD of RET(-1,+1) over all events, 8.774%
    haircut=0.5,                        # lead rule: halve the paper effect
    cost_half_spread_last30_bp=1.074,   # doc 136, single-stock median half-spread, last 30 min
    cost_judged_per_side_bp=5.0,        # time machine judged cost per side
    quintile_share=0.2,                 # bottom fifth
    z_needed=2.0,
    handcheck_read=20, handcheck_text_wrong=1, handcheck_fallback_read=3, handcheck_fallback_wrong=2,  # hand reading of kept group filings, random.Random(118)
    cik_by_hand=18, grid69_single_stocks=33,
)
PAPER = "https://dspace.mit.edu/bitstream/handle/1721.1/119665/So_News-driven%20return.pdf"
NQ = "https://www.sec.gov/Archives/edgar/data/1100663/000119312516480933/d146052dnq.htm"
def pct(a, b): return f"{100*a/b:.1f}%"
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

def main():
    S = json.load(open(os.path.join(HERE, "count_118_summary.json")))
    ev = list(csv.DictReader(open(os.path.join(HERE, "count_118_events.csv"))))
    ns = list(csv.DictReader(open(os.path.join(HERE, "count_118_notice_sample.csv"))))
    F = S["forecast_2a"]; U = S["usable_2a"]; n = S["reports"]
    early = F["early_1"] + F["early_more"]
    tim = collections.Counter(e["timing"] for e in ev)
    # power
    q1 = U["events"] * CFG["quintile_share"]
    gross = CFG["sw2014_expected_q1_bp"] * CFG["haircut"]
    nets = [("doc 136 measured, last 30 min (`cost_half_spread_last30_bp` x 2)", gross - 2 * CFG["cost_half_spread_last30_bp"]),
            ("judged (`cost_judged_per_side_bp` x 2)", gross - 2 * CFG["cost_judged_per_side_bp"])]
    sd = CFG["sw2014_sd_ret_bp"]
    lines = []
    W = lines.append
    W("# Count 118: pre-earnings reversal, can the report date be known beforehand")
    W("")
    W("Queue 118, doc 155 candidate 1. Count only, no price of any kind was read. Window 2016-01-01 to 2021-12-31. Nothing dated 2022 or later was used. "
      "All figures below are written by `research_rig/count_118_write_doc.py` from `research_rig/count_118_summary.json`, `research_rig/count_118_events.csv` and `research_rig/count_118_notice_sample.csv`.")
    W("")
    W("## Verdict")
    W("")
    W("Close before prices. MEASURED: the date is easy to know for about half the reports and the rule fires often enough, "
      f"but at {U['events']} usable events the bottom fifth is about {q1:.0f} trades in six years. "
      f"With the halved paper effect and the paper's own noise, the sum gives z about {nets[0][1]/sd*math.sqrt(q1):.2f}, far from {CFG['z_needed']:.0f}. "
      "No plausible change of universe size inside a $500 account fixes that.")
    W("")
    W("## Universe")
    W("")
    W(f"- STATED: the 100 companies in the S&P 100 on 2015-12-31, from the iShares S&P 100 ETF (OEF) schedule of investments in the [iShares Trust N-Q filed 2016-02-26]({NQ}). Two share classes of one firm count once.")
    W(f"- Why: a dated list fixed before the window, so firms that later merged away are kept until they stop reporting (no survivor filter). Plan 69's roster (research_rig/GRID_69.json) has only {CFG['grid69_single_stocks']} single stocks.")
    W(f"- Disney has two CIKs (old and the 2019 holding company); both are used. {CFG['cik_by_hand']} CIKs were set by hand and checked against EDGAR names.")
    W(f"- MEASURED: {S['companies']} companies produced at least one report in the window.")
    W("")
    W("## Step 1: actual report times")
    W("")
    W("Source: data.sec.gov submissions JSON per company, declared user agent, about 4 requests a second. No full-text search. The bulk files also hold rows after 2021; those were dropped unread beyond the date field.")
    W("")
    W("Rule: an original 8-K listing Item 2.02. Acceptance time is UTC, converted to New York time. Before 09:30 is before the open, 09:30 to the close is in session, after the close (16:00, or 13:00 on early-close days) is after the close. "
      "Report day t is the acceptance day for before the open and in session, the next session for after the close or a closed day.")
    W("")
    W(f"Dedupe: Item 2.02 filings by one company within 60 calendar days of the first in a group form one group. MEASURED: {S['clusters']['clusters']} groups, {S['extra_202_dropped']} extra filings dropped. "
      f"In {S['clusters']['picked_by_text']} groups the kept filing is the first whose Item 2.02 text names results of a quarter or year and none of a fixed list of non-report words (preliminary, transcript, recast, historical, fact sheet, charge and so on). "
      f"In {S['clusters']['fallback_first']} groups no filing passed and the first was kept; those are marked `fallback` in the events file and left out of the usable count.")
    W("")
    W("| Year | Reports | Separate report days | Before open | In session | After close |")
    W("|---|---|---|---|---|---|")
    for y, r in S["by_year"].items():
        W(f"| {y} | {r['reports']} | {r['days']} | {r['before_open']} | {r['in_session']} | {r['after_close']} |")
    W(f"| All | {n} | {S['days']} | {tim['before_open']} ({pct(tim['before_open'],n)}) | {tim['in_session']} ({pct(tim['in_session'],n)}) | {tim['after_close']} ({pct(tim['after_close'],n)}) |")
    W("")
    W(f"MEASURED, dedupe quality: a hand reading of {CFG['handcheck_read']} random kept filings from groups (before the last text-test fix) found {CFG['handcheck_text_wrong']} wrong pick by text (a January healthcare-conference guidance update, since added to the word list) and {CFG['handcheck_fallback_wrong']} of {CFG['handcheck_fallback_read']} fallbacks wrong. Single filings were not read; a gap check found the off-cycle ones (guidance, recasts) and the 60-day window was set to catch them.")
    W("")
    W("## Step 2a: mechanical forecast")
    W("")
    W("Rule, fixed before scoring: take the company's kept report 300 to 430 days earlier closest to 364 days; forecast the same month, same weekday, same ordinal week a year later (last such weekday if it does not exist), moved to the next session if closed. "
      "Forecast day f is that day for a base report before the open or in session, the next session if the base was after the close.")
    W("")
    W(f"MEASURED on {F['with_base']} reports with a base ({F['no_base']} had none):")
    W("")
    W(f"- Exact: {F['exact']} ({pct(F['exact'],F['with_base'])}).")
    W(f"- Off by one session: {F['late_1']+F['early_1']} ({pct(F['late_1']+F['early_1'],F['with_base'])}); {F['late_1']} late, {F['early_1']} early.")
    W(f"- Off by more: {F['late_more']+F['early_more']} ({pct(F['late_more']+F['early_more'],F['with_base'])}); {F['late_more']} late, {F['early_more']} early.")
    W(f"- Came early (before f): {early} ({pct(early,F['with_base'])}). Of these, {F['skip_known']} were public before the entry close, so no trade.")
    W("")
    W("Entry under 2a: buy at the close of the session before f if no Item 2.02 has been accepted by then. Sell at the close of the session after t once the 8-K appears. If the report is late by more than one session, the trade is a wasted entry.")
    W("")
    W("## Step 2b: company's own advance notice on EDGAR")
    W("")
    nf = [r for r in ns if r["notice_found"] == "True"]
    lagok = sum(1 for r in ns if r["release_date_in_8k"] and r["release_date_in_8k"] == r["accepted_et"][:10])
    lagn = sum(1 for r in ns if r["release_date_in_8k"])
    W(f"Sample: {len(ns)} kept reports, random.Random(118) over the events file sorted by accession. For each, every 8-K with Item 7.01 or 8.01 accepted in the 45 days before, and the previous quarter's Item 2.02 release, were read (all .htm exhibits). A date near a call, webcast, results or earnings word was then read by hand.")
    W("")
    W(f"- MEASURED: notice found on EDGAR for {len(nf)} of {len(ns)} ({pct(len(nf),len(ns))}). All {len(nf)} named the exact release date. None came early or late against the named date.")
    W(f"- MEASURED: days ahead: {', '.join(r['calendar_days_ahead'] for r in nf)} calendar days ({', '.join(r['tk']+' '+r['notice_kind'] for r in nf)}).")
    W(f"- MEASURED: {sum(int(r['docs_701_801'])>0 for r in ns)} of {len(ns)} reports had any 7.01 or 8.01 filing in the 45 days before.")
    W("- UNKNOWN: how many firms gave notice by newswire or their own site. Those channels are outside this count; the queue 101 protocol (`research_rig/COUNT_101_earnings_date_advancers.md`) already excludes newswire syndications.")
    W("")
    W("Entry under 2b: buy at the close of the session before the named date (the session before the next session if the named time is after the close). Only about one report in twenty gets a 2b entry, so 2b is not a working source here.")
    W("")
    W(f"MEASURED, 8-K lag check on the same sample: the date in the 8-K's own Item 2.02 text equals its acceptance date in {lagok} of {lagn}. So at day level the 8-K does not lag the release. A within-day lag (press release before the open, 8-K after the close) cannot be seen from EDGAR and is UNKNOWN.")
    W("")
    W("## Step 3: usable events and power")
    W("")
    W(f"MEASURED under 2a: usable means t is f or f+1, the report was not out before the entry close, and the group was not a fallback. {U['events']} usable events on {U['entry_days']} separate entry days. {U['wasted_entries']} entries would be placed with no report by f+1. {U['fallback_dedupe_excluded']} fallback events left out.")
    W("")
    W("| Year | " + " | ".join(str(y) for y in U["by_year"]) + " |")
    W("|---|" + "---|" * len(U["by_year"]))
    W("| Usable | " + " | ".join(str(v) for v in U["by_year"].values()) + " |")
    W("")
    W(f"STATED from [So and Wang 2014]({PAPER}):")
    W("")
    W(f"- Table 2, actual date: Low-High {CFG['sw2014_actual_low_high_bp']} bp (`sw2014_actual_low_high_bp`), long side {CFG['sw2014_actual_q1_bp']} bp (`sw2014_actual_q1_bp`).")
    W(f"- Table 7, p. 37, expected date: Low-High {CFG['sw2014_expected_low_high_bp']} bp (`sw2014_expected_low_high_bp`), long side {CFG['sw2014_expected_q1_bp']} bp (`sw2014_expected_q1_bp`), so the long side is {pct(CFG['sw2014_expected_q1_bp'],CFG['sw2014_expected_low_high_bp'])} of the spread.")
    W(f"- Table 7 by timing: on time {CFG['sw2014_ontime_low_high_bp']} bp, late {CFG['sw2014_late_low_high_bp']} bp, early {CFG['sw2014_early_low_high_bp']} bp.")
    W(f"- Table 1, p. 31: SD of the three-day return over all events {CFG['sw2014_sd_ret_bp']} bp (`sw2014_sd_ret_bp`). A per-event SD of the long leg or the spread is not printed: UNKNOWN. The all-event SD is used as the noise.")
    W("")
    W(f"Sum (doc 117 form, z = net / SD x sqrt(n)): gross = `sw2014_expected_q1_bp` x `haircut` = {gross:.1f} bp. Long trades n = usable x `quintile_share` = {q1:.0f}.")
    W("")
    W("| Cost case | Net bp | z at n | n needed for z = 2 |")
    W("|---|---|---|---|")
    for name, net in nets:
        W(f"| {name} | {net:.1f} | {net/sd*math.sqrt(q1):.2f} | {math.ceil((CFG['z_needed']*sd/net)**2)} |")
    W("")
    W(f"Days cluster: the {U['events']} usable events share {U['entry_days']} entry days, so the effective n is lower than the table uses. The exact-close cost is UNKNOWN (doc 136 measures the last 30 minutes only). The rule enters at the close before t and holds days t and t+1; the paper's three-day return also holds day t-1, so the paper figure may overstate this rule: UNKNOWN by how much.")
    W("")
    W("## Ways this fools us")
    W("")
    W("- Look-ahead from the actual date. Check: the usable count uses only the forecast day and the filings accepted before the entry close.")
    W("- 8-K lags the press release. Check: release date in the 8-K text vs acceptance date (done for the sample, day level). Within-day lag needs a dated newswire source.")
    W("- Non-earnings Item 2.02 filings (guidance, preliminaries, recasts). Check: the text test, the 60-day groups and the hand reading above; a price test would also need it.")
    W(f"- Early reports do not reverse (paper: early {CFG['sw2014_early_low_high_bp']} bp). Check: 2a skips any report out before the entry close; the count shows how many.")
    W("- Effect gone after the paper's sample (1996 to 2011) and among the largest firms. Check: split any later test by year and firm size; the paper says the effect was larger in its first half, no number printed.")
    W("- Window mismatch (rule holds t, t+1; paper holds t-1, t, t+1). Check: price both windows; the paper's figure is for the longer one.")
    W("- Market adjustment and beta: high-beta names sit in the bottom fifth after a market drop. Check: adjust by beta and by sector, not only by the market.")
    W("- Survivorship and mergers: firms leaving mid-window. Check: fixed 2015 list, stop events at the last report; MEASURED company count above.")
    W("- Cost at the exact close is UNKNOWN. Check: measure the closing auction cost before any plan.")
    W("- COVID 2020 date shifts lower the 2a hit rate. Check: the by-year usable row (2020 is the lowest).")
    W("")
    W("## Files")
    W("")
    W(f"- `research_rig/count_118_events.csv`: one row per kept report, no price field, SHA-256 {sha(os.path.join(HERE,'count_118_events.csv'))}.")
    W(f"- `research_rig/count_118_notice_sample.csv`: the 60-report notice sample, no price field, SHA-256 {sha(os.path.join(HERE,'count_118_notice_sample.csv'))}.")
    W(f"- `research_rig/count_118_summary.json`: counts. The text-test flags file kept off repo has SHA-256 {S['clus_flags_sha256']}.")
    W("- `research_rig/count_118_pre_earnings.py`, `research_rig/count_118_fetch_notice.py`, `research_rig/count_118_write_doc.py`: the scripts. Raw EDGAR downloads stay off repo, packed with xz.")
    open(os.path.join(HERE, "COUNT_118_pre_earnings_reversal.md"), "w").write("\n".join(lines) + "\n")

if __name__ == "__main__": main()
