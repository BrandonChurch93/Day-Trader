"""Writes docs/research/47_replay_12_congress_followers.md from stored files only: prices_12_summary.json,
events_12_summary.json and, once they exist, results_12_design.json and results_12_heldback.json. Reads no price and
no trade, and runs nothing. Every figure in the page comes from those files.
   python3 report_12.py                      writes the page
   python3 report_12.py --from DIR --out F   reads the result files from DIR and writes F (used by the tests)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(ROOT, "docs", "research", "47_replay_12_congress_followers.md")
VARIANTS = ("main", "late5", "cal30")
VNAME = {"main": "main entry", "late5": "entry 5 trading days later", "cal30": "entry 30 calendar days later"}
GNAME = {"all": "every stock purchase", "large": "purchases of at least large_buy_min_usd", "proven": "purchases by the proven list"}


PLAN = "PREREG_12_congress_followers.md" if os.path.exists(os.path.join(HERE, "PREREG_12_congress_followers.md")) else "PREREG_12_congress_followers_DRAFT.md"


def load(d, name):
    p = os.path.join(d, name)
    return json.load(open(p)) if os.path.exists(p) else None


def pc(x, d=2): return "none" if x is None else f"{x * 100:+.{d}f}%"
def sh(x): return "none" if x is None else f"{x * 100:.1f}%"
def gx(x): return "none" if x is None else f"{x:.3f}"
def setup_name(k):
    g, n = k.split("-H"); return f"{GNAME[g]}, hold {n} trading days"


def build(src):
    PS, ES = load(HERE, "prices_12_summary.json"), load(HERE, "events_12_summary.json")
    D, H = load(src, "results_12_design.json"), load(src, "results_12_heldback.json")
    NE = load(HERE, "noedge_12.json")
    ne_line = None
    if NE:
        hs = NE["holds"]
        ne_line = (f"MEASURED {NE['written_utc']} UTC by `research_rig/noedge_12.py` on {NE['sets']:,} made-up data sets with no edge in them, {NE['months']} months long. "
                   "With nothing there, mark 2 passed " + ", ".join(f"{sh(hs[k]['pass_rate_blocks'])} of the time at the {k}-day hold (blocks of {hs[k]['block_months']} month{'s' if hs[k]['block_months'] > 1 else ''})" for k in hs)
                   + ". The intent is 5%. Mark 2 is one of five marks that must all hold.")
    o = []; w = o.append
    w("# 47. Replay 12: following stock purchases disclosed by members of Congress\n")
    made = ["Built by `research_rig/report_12.py` from `research_rig/prices_12_summary.json` and `research_rig/events_12_summary.json`"]
    if D: made.append("`research_rig/results_12_design.json`")
    if H: made.append("`research_rig/results_12_heldback.json`")
    w("Status: research result, pretend trades on past prices. " + ", ".join(made) + ". The plan is `research_rig/" + PLAN + "`; its numbers are in the config key `replay_12_plan`."
      + (f" Design half scored {D['made_utc']} UTC." if D else " The design half is not scored yet.")
      + (f" Held-back half scored {H['made_utc']} UTC." if H else " The held-back half is not scored yet, so there is no verdict yet.") + "\n")
    w("Labels: MEASURED means computed from the stored files. UNKNOWN means not known.\n")

    w("## What is tested\n")
    w("- A member's purchases of one stock on one filing day are one event. The pretend trade buys at the open of the first trading day after the filing day and sells at the close after the hold (`replay_12_plan.holds_days`; main hold `replay_12_plan.main_hold_days`). The filing day, never the trade day, decides the entry.")
    w("- Every result is also worked out with the entry `replay_12_plan.late_entry_trading_days` trading days later and `replay_12_plan.late_entry_calendar_days` calendar days later.")
    w("- Open positions are held in equal weight, reset each day. Cost is `replay_12_plan.cost_bps_per_side` basis points on each day's turnover. The yardstick is SPY held with the same weights on the same days, with no cost.")
    w("- The bootstrap resamples calendar months in circular blocks of consecutive months, the block the hold in trading days divided by `replay_12_plan.bootstrap_days_per_month`, rounded up." + (" " + ne_line if ne_line else ""))
    w("- The design half (filed `replay_12_plan.design_filed_from` to `replay_12_plan.design_filed_to`) only chooses one set-up. The held-back half (filed from `replay_12_plan.heldback_filed_from`) judges it once.\n")

    w("## Data in hand\n")
    if PS:
        w(f"- MEASURED. Daily bars adjusted for splits and dividends ({PS['collection']['start']} to {PS['collection']['end']}, feed {PS['collection']['feed']}) were asked for {PS['collection']['symbols']} symbols. Of {PS['tickers_in_buy_and_sell_rows']} tickers in buy and sell rows, {PS['tickers_with_bars']} have bars and {PS['tickers_without_bars']} have none.")
        w(f"- MEASURED. {PS['tickers_whose_bars_start_after_2019_01_02']} tickers' bars start after 2019-01-02 and {PS['tickers_whose_bars_end_before_2026_11_24']} end before 2026-11-24. NANC has bars from {PS['scale_funds']['NANC']['first']}.")
    if ES:
        w(f"- MEASURED. {ES['rows']} rows give {ES['buy_events']} stock purchase events and {ES['sell_events']} sale events from {ES['buy_members']} members buying {ES['buy_tickers']} tickers. The busiest buyer, {ES['busiest_buyer']['member']}, has {sh(ES['busiest_buyer']['share'])} of purchase events.")
        w("\n| Half | Side | Events | Large | Members | No bar on main entry day | Share | With call or exercise words |\n|---|---|---|---|---|---|---|---|")
        for k in ("buy_design", "buy_heldback", "sell_design", "sell_heldback"):
            r = ES[k]; side, half = k.split("_")
            w(f"| {half} | {side} | {r['events']} | {r['large']} | {r['members']} | {r['no_bar_on_main_entry_day']} | {sh(r['no_bar_share'])} | {r['with_call_or_exercise_rows']} |")
        w("\nNo bar on the main entry day, by filing year (purchases): " + ", ".join(f"{y} {v}" for h in ("buy_design", "buy_heldback") for y, v in ES[h]["no_bar_by_year"].items()) + ".\n")
        if "rename_list" in ES:
            import csv as _csv
            RL = list(_csv.DictReader(open(os.path.join(HERE, "renames_12.csv"), newline="")))
            st = {x: [r["old_ticker"] for r in RL if r["status"] == x] for x in ("mapped", "left_out", "mapped_before", "left_out_before")}
            rec = lambda h: ", ".join(f"{y} {v}" for y, v in ES[h]["recovered_by_rename_list_by_year"].items())
            w(f"- MEASURED. The rename list `research_rig/renames_12.csv`, built from public sources before scoring, maps {len(st['mapped'])} old tickers to the same company's new ticker and leaves out {len(st['left_out'])} (takeovers, share-class changes, delistings, preferred shares and names not confirmed). Events it gives a bar on the main entry day, by filing year: purchases, design {rec('buy_design')}; purchases, held-back {rec('buy_heldback')}; sales, design {rec('sell_design')}; sales, held-back {rec('sell_heldback')}.")
            mv = lambda h: ", ".join(f"{x} {v}" for x, v in ES[h]["events_moved_by_rename_line"].items() if "<" in x) or "none"
            w(f"- MEASURED. Dated lines, for tickers whose price file holds another company's history for earlier rows (found in passing, not hunted for): {len(st['mapped_before'])} send rows filed before a date to the right ticker and {len(st['left_out_before'])} leave such rows out, counted as no price. The filing day chooses the line. Events moved, by line (ticker before date): purchases, design {mv('buy_design')}; purchases, held-back {mv('buy_heldback')}; sales, design {mv('sell_design')}; sales, held-back {mv('sell_heldback')}.\n")
        w("Named members matched in trades.csv (full name and rows):\n")
        for n_, hit in ES["named_members_matched"].items():
            w(f"- {n_}: " + ("; ".join(f"{m} ({k} rows)" for m, k in hit.items()) if hit else "no member") + ("" if len(hit) == 1 else ". The scoring modes refuse until this name matches exactly one member."))
        w("")

    if not D:
        w("## Results\n\nNot scored yet. This page will be rewritten from the result files when they exist.\n")
        return "\n".join(o)

    w("## The design half (used only to choose a set-up, not to judge)\n")
    w("| Set-up | Entry | Events traded | No price | Growth | SPY mirror | Per-year excess | Sales per-year excess | Bootstrap 5th pct, monthly | No daily reset (not judged) |\n|---|---|---|---|---|---|---|---|---|---|")
    for k, V in D["setups"].items():
        for v in VARIANTS:
            J = V[v]["judged"]; s = V[v]["sales_b"]
            w(f"| {setup_name(k)} | {VNAME[v]} | {J['events']['traded']} | {J['events']['no_price']} | {gx(J['growth'])} | {gx(J['spy_growth'])} | {pc(J['per_year_excess'])} | {pc(s['per_year_excess'])} | {pc(J['bootstrap_p5_monthly_diff'], 3)} | {gx(J.get('no_reset_growth_not_judged'))} |")
    w("")
    w(f"Chosen by the fixed rule (highest per-year excess at the main entry): {setup_name(D['chosen_setup']) if D['chosen_setup'] else 'none'}. It alone is scored on the held-back half, once. The best of {len(D['setups'])} looks better than it is; that is why this half does not judge.\n")

    if not H:
        w("## The held-back half\n\nNot scored yet, so there is no verdict yet.\n")
    else:
        w("## The held-back half (the judge)\n")
        w(f"Set-up: {setup_name(H['chosen_setup'])}.\n")
        w("| Entry | Events traded | No price | Stopped | Growth | SPY mirror | Per-year excess | Sales per-year excess | Bootstrap 5th pct, monthly | QQQ, for scale | NANC, for scale |\n|---|---|---|---|---|---|---|---|---|---|---|")
        for v in VARIANTS:
            R = H["results"][v]; J = R["judged"]
            q, nn = J.get("qqq_for_scale"), J.get("nanc_for_scale")
            w(f"| {VNAME[v]} | {J['events']['traded']} | {J['events']['no_price']} | {J['events']['stopped']} | {gx(J['growth'])} | {gx(J['spy_growth'])} | {pc(J['per_year_excess'])} | {pc(R['sales_b']['per_year_excess'])} | {pc(J['bootstrap_p5_monthly_diff'], 3)} | {pc(q['per_year_excess']) if q else 'none'} | {pc(nn['per_year_excess']) if nn else 'none'} |")
        w("\nPass marks, fixed before:\n")
        LAB = {"1_ends_above_spy": "1. ends above the SPY mirror", "2_bootstrap_p5_above_0": "2. bootstrap 5th percentile of the mean monthly difference above zero",
               "3_above_sales": "3. per-year excess above the sales portfolio's", "4_min_events": "4. at least replay_12_plan.min_events events traded",
               "5_late5_ends_above_spy": "5. with the late5 entry, still ends above SPY"}
        for k, ok in H["pass_marks"].items():
            w(f"- {LAB.get(k, k)}: {'yes' if ok else 'no'}" + (f". {ne_line}" if k.startswith("2_") and ne_line else ""))
        w(f"\nMEASURED. Verdict: {'passes all five marks' if H['passes'] else 'does not pass'}.\n")
        m = H["results"]["main"]
        w("### Side lines (reported, not judged)\n")
        def sl(name, S):
            if S is None: return
            w(f"- {name}: per-year excess {pc(S.get('per_year_excess'))}, events traded {S.get('traded_events', 'none')}.")
        sl("one position per stock, not per member", m.get("by_stock_not_judged"))
        sl(f"without the busiest member ({(m.get('without_busiest_member_not_judged') or {}).get('member')})", m.get("without_busiest_member_not_judged"))
        sl("without events whose rows mention a call or an exercise", m.get("without_call_or_exercise_rows_not_judged"))
        sl("without trades whose prices stop inside the hold", m.get("without_stopped_not_judged"))
        rd = m.get("random_days_c_not_judged")
        if rd: w(f"- the same stocks on random filing days (yardstick c, {rd.get('draws')} draws): share of draws at or above the real result {sh(rd.get('share_of_draws_at_or_above_real'))}.")
        w("")
        w("### Each year apart, main entry (reported, not judged)\n")
        w("| Year | Days held | Growth | SPY mirror |\n|---|---|---|---|")
        for y, Y in (m["judged"].get("years") or {}).items(): w(f"| {y} | {Y['days']} | {gx(Y['growth'])} | {gx(Y['spy_growth'])} |")
        w("")
        w("### No price, by filing year\n")
        w(", ".join(f"{y} {k}" for y, k in m["judged"]["events"]["no_price_by_year"].items()) + "\n")
        w("### The 20 largest single-event returns, chosen hold, main entry\n")
        w("| Ticker | Member | Filed | Entry | Exit | Stopped | Return |\n|---|---|---|---|---|---|---|")
        for e in H["largest_event_returns_chosen_hold"]:
            w(f"| {e['ticker']} | {e['member']} | {e['filed']} | {e['entry']} | {e['exit']} | {'yes' if e['stopped'] else 'no'} | {pc(e['event_return'])} |")
        w("")

    R = H or D; half = "held-back" if H else "design"
    nm = R.get("named_members_not_judged") or {}
    if nm:
        w(f"## Named members, {half} half (reported, not judged)\n")
        w("Per event, entry open to exit close, less SPY over the same days. Call purchases are shown as the underlying stock after the purchase: these are stock returns, not option returns.\n")
        w("| Name | Member | What | Hold | Entry | Events | Mean less SPY | Median less SPY | Share above SPY |\n|---|---|---|---|---|---|---|---|---|")
        for n_, M in nm.items():
            for what, key in (("stock purchases", "stock_purchases"), ("stock after call purchases (not option returns)", "call_purchases_as_underlying_stock_not_option_returns")):
                T = M.get(key)
                if not T: continue
                for h, V in T.items():
                    for v in VARIANTS:
                        s = V[v]
                        if not s.get("events"): continue
                        w(f"| {n_} | {M['member']} | {what} | {h[1:]} | {VNAME[v]} | {s['events']} | {pc(s['mean_minus_spy'])} | {pc(s['median_minus_spy'])} | {sh(s['share_above_spy'])} |")
        w("")
    w("## Limits\n")
    w("- Tickers with no bars are left out and counted. Many are foreign shares sold over the counter, mutual funds, preferreds, and old tickers of companies that were renamed. The price source keeps a renamed company's history under its new ticker, so events under the old ticker have no price. UNKNOWN how much this moves the result.")
    w("- Ticker reuse (an old ticker given later to another company) was not checked. UNKNOWN.")
    w("- The filing day is the day the report was received. It is not proof of when the public could read it; the later entries are there for that.\n")
    return "\n".join(o)


if __name__ == "__main__":
    a = sys.argv[1:]
    src = a[a.index("--from") + 1] if "--from" in a else HERE
    out = a[a.index("--out") + 1] if "--out" in a else PAGE
    text = build(src)
    open(out, "w").write(text + "\n")
    print("wrote", os.path.relpath(out, ROOT) if out.startswith(ROOT) else out)
