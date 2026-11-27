#!/usr/bin/env python3
"""Plan 76: writes the held-back result page and a small public summary from three aggregate files.

Reads, read-only, the count, design and held-back `result.json` files that the one run of each
stage left in the custody folder named in config/thresholds.yaml (plan_76.custody.root). Each is
pinned by the SHA-256 written on ledger row 229. It never runs `score_76.py`, never opens a bars
file and copies no price or trade row. Every figure in the page is read here or computed here.

Writes:
  docs/research/200_plan_76_heldback_result.md
  research_rig/RESULT_76_summary.json   (aggregate figures only, for the dashboard)

If the three files are not on this computer it leaves the committed outputs untouched and says so.
The blind recompute line and the breakdown by year, by coin and by thin pair come from the
independent auditor's report (RECOMPUTE below, pinned by SHA-256, aggregates only). The stage
results hold no per-trade rows, so those lines cannot be computed here and the scorer is never
rerun to get them; the page cites the report as their source. Each of the auditor's headline
figures is checked against the official result, and each breakdown must add back to the official
15 bp mean. Without the report the page says "Blind recompute: pending" and has no breakdown.

Run: python3 research_rig/report_76.py
"""
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = "docs/research/200_plan_76_heldback_result.md"
SUMMARY = "research_rig/RESULT_76_summary.json"
LEDGER = "research_rig/TRIAL_LEDGER.md"
QUEUE = "docs/QUEUE.md"
SCORECARD = "docs/research/95_where_we_stand_after_32_tests.md"
PLAN = "research_rig/PREREG_76_washout_rebound.md"
BITSTAMP_API = "https://www.bitstamp.net/api/"
STAGES = ("count", "design", "heldback")
MARK_ORDER = ("enough_trades", "positive", "positive_trimmed", "beats_random")


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def cfg():
    return yaml.safe_load(text("config/thresholds.yaml"))["plan_76"]["value"]


def one(pattern, body, what, flags=0):
    found = re.findall(pattern, body, flags)
    if len(found) != 1:
        raise ValueError(f"Plan 76 report: {what} not found once ({len(found)} matches)")
    return found[0]


def ledger_row(n):
    rows = [l for l in text(LEDGER).splitlines() if l.startswith(f"| {n} |")]
    if len(rows) != 1:
        raise ValueError(f"Plan 76 report: ledger row {n} not found once")
    return rows[0]


def queue_cells(n):
    for line in text(QUEUE).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == n:
            return cells
    raise ValueError(f"Plan 76 report: queue row {n} not found")


def pins():
    """Result file SHA-256 per stage, as written on ledger row 229."""
    row = ledger_row(229)
    return {"count": one(r"Count result \([^)]*result file sha256 ([0-9a-f]{64})\)", row, "count result hash"),
            "design": one(r"Design result \([^)]*result file sha256 ([0-9a-f]{64})\)", row, "design result hash"),
            "heldback": one(r"HELD-BACK RESULT \([^)]*result file sha256 ([0-9a-f]{64})", row, "held-back result hash")}


def load_results(root):
    """The three stage results, pinned. None when any file is absent."""
    paths = {s: pathlib.Path(root) / s / "result.json" for s in STAGES}
    if not all(p.is_file() for p in paths.values()):
        return None
    want = pins()
    out = {}
    for stage, path in paths.items():
        blob = path.read_bytes()
        if hashlib.sha256(blob).hexdigest() != want[stage]:
            raise ValueError(f"Plan 76 report: {stage} result.json does not match the hash on ledger row 229")
        out[stage] = json.loads(blob)
        if out[stage].get("stage") != stage:
            raise ValueError(f"Plan 76 report: {stage} result.json names another stage")
    return out


RECOMPUTE = pathlib.Path("/home/user/workspace/out/p76_blind_recompute.md")
RECOMPUTE_SHA = "ce70a457aa66f7890350f4fe2a0470dc9e3e6d68f519e0d52c121148e58fd19e"
THIN = 4  # the auditor's four pairs with the most flat hours


def load_recompute(path=RECOMPUTE):
    """The auditor's figures, parsed from its pinned report. None when the report is not on this computer."""
    path = pathlib.Path(path)
    if not path.is_file():
        return None
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != RECOMPUTE_SHA:
        raise ValueError("Plan 76 report: the blind recompute report does not match its pin")
    t = blob.decode("utf-8")
    num = lambda x: float(x.replace("%", "")) / 100
    verdict = one(r"^(AGREES|DISAGREES)\b", t, "recompute verdict", re.M)
    line = {}
    for bp in ("75", "15"):
        block = one(rf"At {bp} bp a side:\n\n(.*?)\n\n", t, f"recompute {bp} bp table", re.S)
        row = lambda name: one(rf"^\| {name} \| ([^|]+?) \|", block, f"recompute {bp} bp {name}", re.M)
        line[bp] = dict(mean_net=num(one(r"([+-][\d.]+%)", row("Mean net"), "mean")),
                        share=float(one(r"([\d.]+)", row("Share of books beaten"), "share")),
                        trimmed=num(one(r"([+-][\d.]+%)", row("Mean without each year's best"), "trimmed")),
                        trades=int(one(r"(\d+)", row("Count of at least 64"), "count")),
                        all_marks=row("All four marks").strip() == "yes")
    by_year = {y: (int(n), num(v)) for y, n, v in re.findall(r"^- (\d{4}): (\d+), ([+-][\d.]+%)$", t, re.M)}
    by_coin = {c: (int(n), num(v)) for c, n, v in re.findall(r"^- ([A-Z]+): (\d+), ([+-][\d.]+%)$", t, re.M)}
    flat = re.findall(r"([A-Z]+) ([\d,]+)", one(r"^- MEASURED: Flat hours by coin, [^:]+: (.+)\.$", t, "flat hours", re.M))
    shib = one(r"Without SHIB, the other (\d+) trades average ([+-][\d.]+%) at 15 bp and ([+-][\d.]+%) at 75 bp", t, "without SHIB")
    thin = one(r"(\d+) of the (\d+) signal bars are on them", t, "thin share")
    thin_m = one(r"Those (\d+) trades average ([+-][\d.]+%) at 15 bp \(([+-][\d.]+%) at 75 bp\)\. The other (\d+) average "
                 r"([+-][\d.]+%) at 15 bp \(([+-][\d.]+%) at 75 bp\)", t, "thin means")
    blind_at = one(r"My numbers were written to \S+ at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}):\d{2} UTC", t, "blind stamp")
    return dict(path=str(path), sha256=RECOMPUTE_SHA, verdict=verdict, finished_utc=blind_at + " UTC", line=line,
                by_year=by_year, by_coin=by_coin, thin_coins=[c for c, _ in flat[:THIN]],
                flat_hours={c: int(n.replace(",", "")) for c, n in flat},
                without_shib=dict(trades=int(shib[0]), cheap=num(shib[1]), main=num(shib[2])),
                thin=dict(trades=int(thin_m[0]), cheap=num(thin_m[1]), main=num(thin_m[2]),
                          rest=int(thin_m[3]), rest_cheap=num(thin_m[4]), rest_main=num(thin_m[5])),
                thin_of=(int(thin[0]), int(thin[1])),
                pattern_seen="had already seen the 4b8d9f4 commit subject" in t,
                stream_unknown="UNKNOWN: whether my random stream is call-for-call the same" in t)


def check_recompute(rec, lines, by_year_counts, draws):
    """Every auditor figure that the official result also holds must agree; each breakdown must add back."""
    off = {"75": lines["main"], "15": lines["cheap"]}
    for bp, mine in rec["line"].items():
        o = off[bp]
        if (mine["trades"] != o["trades"] or abs(mine["mean_net"] - o["mean_net"]) > 5e-7 or abs(mine["trimmed"] - o["trimmed"]) > 5e-7
                or round(mine["share"] * draws) != o["beaten"] or mine["all_marks"] != all(o["marks"].values())):
            raise ValueError(f"Plan 76 report: the blind recompute does not match the official result at {bp} bp")
    if rec["verdict"] != "AGREES":
        raise ValueError("Plan 76 report: the blind recompute does not say AGREES")
    total, cheap = lines["cheap"]["trades"], lines["cheap"]["mean_net"]
    if {y: n for y, (n, _) in rec["by_year"].items()} != {y: n for y, n in by_year_counts.items()}:
        raise ValueError("Plan 76 report: the recompute's trades by year differ from the official result")
    # Each breakdown is printed to two decimals, so it may miss the official mean by rounding only.
    tol = lambda n: 0.00005 * n / total + 1e-9
    for name, parts in (("by year", list(rec["by_year"].values())), ("by coin", list(rec["by_coin"].values())),
                        ("SHIB split", [rec["by_coin"]["SHIB"], (rec["without_shib"]["trades"], rec["without_shib"]["cheap"])]),
                        ("thin split", [(rec["thin"]["trades"], rec["thin"]["cheap"]), (rec["thin"]["rest"], rec["thin"]["rest_cheap"])])):
        n = sum(k for k, _ in parts)
        if n != total or abs(sum(k * v for k, v in parts) / total - cheap) > sum(tol(k) for k, _ in parts):
            raise ValueError(f"Plan 76 report: the recompute's {name} breakdown does not add back to the official result")
    if sum(rec["by_coin"][c][0] for c in rec["thin_coins"]) != rec["thin"]["trades"] or rec["thin_of"] != (rec["thin"]["trades"], total):
        raise ValueError("Plan 76 report: the thin-pair count does not match the coin counts")
    for t75, t15 in ((rec["without_shib"]["main"], rec["without_shib"]["cheap"]), (rec["thin"]["main"], rec["thin"]["cheap"]),
                     (rec["thin"]["rest_main"], rec["thin"]["rest_cheap"])):
        # The same trades at two flat costs share one gross mean.
        if abs(gross_from(t75, 75) - gross_from(t15, 15)) > 0.0002:
            raise ValueError("Plan 76 report: a recompute split does not hold one gross mean at both costs")


# ------------------------------------------------------------------ arithmetic
def keep(bp):
    """What a round trip keeps of the sale proceeds: ((1 - f) / (1 + f)), the plan's net formula."""
    f = bp / 10_000
    return (1 - f) / (1 + f)


def gross_from(net, bp):
    """The mean gross return per trade behind a mean net at a flat cost (the formula is affine in gross)."""
    return (1 + net) / keep(bp) - 1


def break_even_bp(gross):
    """The flat cost per side at which (1 + gross) * keep(bp) - 1 is zero."""
    return 10_000 * gross / (2 + gross)


def mt_from_utc(stamp):
    """'2026-11-27 01:00 UTC' -> '2026-11-26 6:00 PM MT'."""
    from zoneinfo import ZoneInfo
    t = dt.datetime.strptime(stamp, "%Y-%m-%d %H:%M UTC").replace(tzinfo=dt.timezone.utc).astimezone(ZoneInfo("America/Boise"))
    return f"{t:%Y-%m-%d} {t.hour % 12 or 12}:{t:%M} {'AM' if t.hour < 12 else 'PM'} MT"


def pct(x, d=2):
    return f"{100 * x:+.{d}f}%".replace("+-", "-")


def yes(b):
    return "yes" if b else "no"


# ------------------------------------------------------------------ the figures
def figures(res, rec=None):
    c = cfg()
    bp = c["costs_bp"]
    hb, de, co = res["heldback"], res["design"], res["count"]
    row = ledger_row(229)
    sel = hb["selected"]
    if not (sel == de["selected"] == co["selected"] == "primary"):
        raise ValueError("Plan 76 report: the judged arm is not the 5% arm in every stage")
    lines = {}
    for name in ("main", "cheap"):
        ln = hb["lines"][name]
        marks = ln["marks"]
        if set(marks) != set(MARK_ORDER):
            raise ValueError("Plan 76 report: the held-back marks have another shape")
        k = round(ln["control_share_strictly_beaten"] * c["control"]["draws"])
        # The marks in the file must agree with the figures in the file and the frozen thresholds.
        check = {"enough_trades": ln["trades"] >= c["min_heldback_trades"], "positive": ln["mean_net"] > c["mean_floor"],
                 "positive_trimmed": ln["mean_without_each_year_best"] > c["mean_floor"],
                 "beats_random": ln["control_share_strictly_beaten"] > c["control"]["beat_share"]}
        if check != marks:
            raise ValueError(f"Plan 76 report: the {name} line's marks do not follow from its figures")
        lines[name] = dict(bp=bp[name], trades=ln["trades"], mean_net=ln["mean_net"],
                           trimmed=ln["mean_without_each_year_best"], beaten=k, books=c["control"]["draws"],
                           marks=marks, met=sum(marks.values()))
    gross = gross_from(lines["main"]["mean_net"], bp["main"])
    gross_t = gross_from(lines["main"]["trimmed"], bp["main"])
    for name in ("cheap",):
        if abs((1 + gross) * keep(bp[name]) - 1 - lines[name]["mean_net"]) > 1e-12 or \
           abs((1 + gross_t) * keep(bp[name]) - 1 - lines[name]["trimmed"]) > 1e-12:
            raise ValueError("Plan 76 report: the two cost lines do not share one gross mean; break-even refused")
    passed = all(lines["main"]["marks"].values())
    outcome = hb["outcome"]
    if passed or outcome != "forward card on Binance.US books, not a counted pass" or not all(lines["cheap"]["marks"].values()):
        raise ValueError("Plan 76 report: the outcome is not the one this page is written for")
    shown = hb["shown_only"]
    sh = lambda key: dict(trades=shown[key]["trades"], main=shown[key]["mean_net"]["main"], cheap=shown[key]["mean_net"]["cheap"])
    window = one(r"HELD-BACK RESULT .*?MEASURED on Bitstamp hourly bars, (\d+) coins, (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", row, "held-back window")
    coins = one(r"(\d+) of the 20 coins meet the coverage rule \(([A-Z, ]+):", row, "covered coins")
    if int(window[0]) != int(coins[0]) or len(coins[1].split(", ")) != int(coins[0]):
        raise ValueError("Plan 76 report: the coin count and the coin list disagree")
    run_at = one(r"HELD-BACK RESULT \([^)]*run once at ([0-9a-f]{7,40})", row, "held-back run commit")
    xrp = one(r"the delayed sale in the design stage is ([A-Z]+), entered (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC and sold (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC", row, "design delayed sale")
    held_days = (dt.datetime.fromisoformat(xrp[2]) - dt.datetime.fromisoformat(xrp[1])).total_seconds() / 86400
    dsel = de["shown_only"]["selected_arm_marks"]
    total = one(r"^\| Total \| (\d+) \| (\d+) \|", text(SCORECARD), "scorecard Total row", re.M)
    q138 = queue_cells("138")
    e14 = one(r"judged at (\d+) trades or (\d{4}-\d{2}-\d{2})", q138[1], "E14 judging rule")
    q137 = queue_cells("137")
    m133 = one(r"(\d+) hourly wakes to (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2} [AP]M MT)", q137[-1], "Measurement 133 end")
    f = dict(
        plan=76, ledger_row=229, page=PAGE, outcome=outcome, passed=False,
        source="Bitstamp US dollar hourly bars", source_url=BITSTAMP_API,
        coins=int(coins[0]), coin_list=coins[1].split(", "), window=[window[1], window[2]], run_at=run_at,
        drop=c["drops"]["primary"], drop_shown=c["drops"]["alternate"], hold_hours=c["hold_hours"]["primary"],
        hold_shown=c["hold_hours"]["shown"], min_trades=c["min_heldback_trades"], beat_share=c["control"]["beat_share"],
        trades_by_year=hb["trades_by_utc_entry_year"], coverage=hb["coverage"], lines=lines,
        gross_mean=gross, gross_trimmed=gross_t,
        break_even_bp=break_even_bp(gross), break_even_all_marks_bp=break_even_bp(gross_t),
        shown_only={"drop_3_5": sh("alternate"), "hold_12h": sh("primary_short"), "entry_1h_late": sh("primary_late")},
        count=dict(primary=co["counts_by_utc_entry_year"]["primary"], alternate=co["counts_by_utc_entry_year"]["alternate"],
                   refused=co["refused_at_fence"], need=c["count_each_year"], years=c["count_years"]),
        design=dict(trades=dsel["main"]["trades"], by_year=de["trades_by_utc_entry_year"], main=dsel["main"]["mean_net"],
                    cheap=dsel["cheap"]["mean_net"], trimmed_main=dsel["main"]["mean_without_each_year_best"],
                    trimmed_cheap=dsel["cheap"]["mean_without_each_year_best"],
                    beaten=round(dsel["main"]["control_share_strictly_beaten"] * c["control"]["draws"]),
                    delayed=de["coverage"]["delayed_sales"], span=[c["design"][0], str(dt.date.fromisoformat(c["design"][1]) - dt.timedelta(days=1))],
                    delayed_coin=xrp[0], delayed_in=xrp[1] + " UTC", delayed_out=xrp[2] + " UTC", delayed_days=held_days),
        tests_scored=int(total[0]), passes_counted=int(total[1]),
        e14=dict(queue="138", ledger="233", trades=int(e14[0]), last=e14[1], state=q138[-1].split(".")[0]),
        m133=dict(queue="137", wakes=int(m133[0]), last=m133[1], state=q137[-1].split(" (")[0]),
        sha256=pins(), recompute=None)
    if rec:
        check_recompute(rec, lines, hb["trades_by_utc_entry_year"], c["control"]["draws"])
        f["recompute"] = dict(rec, finished_mt=mt_from_utc(rec["finished_utc"]))
    return f


# ------------------------------------------------------------------ the page
def page(f):
    m, ch = f["lines"]["main"], f["lines"]["cheap"]
    d, co, s = f["design"], f["count"], f["shown_only"]
    years = ", ".join(f"{n} in {y}" for y, n in sorted(f["trades_by_year"].items()))
    o = []
    a = o.append
    a(f"# 200. Plan 76, the held-back run: buy a coin after a one-hour fall, hold a day")
    a("")
    a(f"- MEASURED: did not pass. After {m['bp']} bp a side the rule made {pct(m['mean_net'])} a trade on years it had never seen, "
      f"but {pct(m['trimmed'])} with each year's best trade taken out, so {('one', 'two', 'three', 'four')[3 - m['met']]} of the four marks failed.")
    a(f"- INFERENCE: the closest miss so far on a rule that trades in days. At {ch['bp']} bp a side all four marks were met, "
      f"which earns practice card E14 on Binance.US books, not a counted pass.")
    a("")
    r = f["recompute"]
    if r is not None:
        yb = "; ".join(f"{y} {pct(v)} ({n} trades)" for y, (n, v) in sorted(r["by_year"].items()))
        shib, ws, th = r["by_coin"]["SHIB"], r["without_shib"], r["thin"]
        a("## Where the result comes from")
        a("")
        a(f"Source of this section: the independent auditor's blind recompute report, `{r['path']}` (SHA-256 `{r['sha256'][:12]}`, kept off the repo, "
          f"aggregates only). The stage results hold no per-trade rows, so these lines are not computed here and the scorer was not run again. "
          f"This script checks that each breakdown adds back to the official {ch['bp']} bp mean.")
        a("")
        a(f"- MEASURED by the auditor, by entry year at {ch['bp']} bp a side: {yb}.")
        a(f"- MEASURED by the auditor: SHIB made {pct(shib[1])} a trade over {shib[0]} trades. Without SHIB the other {ws['trades']} trades average "
          f"{pct(ws['cheap'])} at {ch['bp']} bp a side and {pct(ws['main'])} at {m['bp']} bp.")
        a(f"- MEASURED by the auditor: the {len(r['thin_coins'])} pairs with the most hours of no price change ({', '.join(r['thin_coins'])}) carry "
          f"{th['trades']} of the {m['trades']} signals and average {pct(th['cheap'])} at {ch['bp']} bp a side. The other {th['rest']} average {pct(th['rest_cheap'])} at {ch['bp']} bp.")
        a(f"- INFERENCE: the result rests on 2024 and on thinly traded pairs, whose hourly opens are the least likely to be real fills. "
          f"Both later years lose even at {ch['bp']} bp a side. It earns a forward card only.")
        a("")
    a(f"Built by `research_rig/report_76.py` from the three stage results, each pinned by the SHA-256 on ledger row {f['ledger_row']}. "
      f"No price, bar or trade row is in the repo. Plan: [`{PLAN}`](../../{PLAN}). bp means a hundredth of a percent. "
      f"Labels: MEASURED is from the runs, STATED is from the plan or the ledger, INFERENCE is a reading, UNKNOWN is not measured.")
    a("")
    a("## The rule in plain words")
    a("")
    a(f"- STATED: {f['coins']} coins on {f['source']}: {', '.join(f['coin_list'])}. Source page: [Bitstamp API]({f['source_url']}).")
    a(f"- STATED: when a coin's hourly close is {100 * f['drop']:g}% or more below the close an hour before, buy it at the next hour's open. "
      f"If several fell, buy the one that fell most.")
    a(f"- STATED: sell {f['hold_hours']} hours later. One position at a time, so trades never overlap.")
    a(f"- STATED: the judged cost is {m['bp']} bp a side. A cheaper {ch['bp']} bp a side line is shown; it can only earn a forward card.")
    a(f"- STATED: four marks, all at {m['bp']} bp a side: at least {f['min_trades']} trades; mean net per trade above zero; "
      f"still above zero with each year's best trade taken out; better than more than {100 * f['beat_share']:g}% of {m['books']} random books "
      f"that buy the same coins at the same hours of the week.")
    a("")
    a("## The held-back figures")
    a("")
    a(f"- MEASURED: {f['window'][0]} to {f['window'][1]}, run once at commit `{f['run_at']}`. {m['trades']} completed trades: {years}. "
      f"Void trades: {f['coverage']['void_missing_entry_bar'] + f['coverage']['void_missing_exit_bar']}. Delayed sales: {f['coverage']['delayed_sales']}.")
    a("")
    a(f"| Mark | At {m['bp']} bp a side | Met | At {ch['bp']} bp a side | Met |")
    a("|---|---|---|---|---|")
    a(f"| At least {f['min_trades']} trades | {m['trades']} | {yes(m['marks']['enough_trades'])} | {ch['trades']} | {yes(ch['marks']['enough_trades'])} |")
    a(f"| Mean net per trade above zero | {pct(m['mean_net'])} | {yes(m['marks']['positive'])} | {pct(ch['mean_net'])} | {yes(ch['marks']['positive'])} |")
    a(f"| Above zero without each year's best trade | {pct(m['trimmed'])} | {yes(m['marks']['positive_trimmed'])} | {pct(ch['trimmed'])} | {yes(ch['marks']['positive_trimmed'])} |")
    a(f"| Better than more than {100 * f['beat_share']:g}% of random books | {m['beaten']} of {m['books']} | {yes(m['marks']['beats_random'])} | "
      f"{ch['beaten']} of {ch['books']} | {yes(ch['marks']['beats_random'])} |")
    a(f"| Marks met | {m['met']} of 4 | | {ch['met']} of 4 | |")
    a("")
    a("## What cost the rule can stand")
    a("")
    a(f"- MEASURED, worked out here from the two lines with the plan's net formula: before costs the rule made {pct(f['gross_mean'])} a trade.")
    a(f"- MEASURED, worked out here: the mean net reaches zero at {f['break_even_bp']:.1f} bp a side.")
    a(f"- MEASURED, worked out here: the failed mark, without each year's best trade, reaches zero at {f['break_even_all_marks_bp']:.1f} bp a side. "
      f"A flat cost does not change which trade is best or how the rule ranks against the random books, so all four marks hold at any flat cost "
      f"under that figure.")
    a("- UNKNOWN: what a $250 order really costs in the hour after a 5% fall on a venue we can use. That is what E14 measures.")
    a("")
    a("## Shown only, these decide nothing")
    a("")
    a(f"- MEASURED: the {100 * f['drop_shown']:g}% fall: {s['drop_3_5']['trades']} trades, {pct(s['drop_3_5']['main'])} a trade at {m['bp']} bp a side, "
      f"{pct(s['drop_3_5']['cheap'])} at {ch['bp']} bp.")
    a(f"- MEASURED: a {f['hold_shown']}-hour hold: {s['hold_12h']['trades']} trades, {pct(s['hold_12h']['main'])} and {pct(s['hold_12h']['cheap'])}.")
    a(f"- MEASURED: buying one hour late: {s['entry_1h_late']['trades']} trades, {pct(s['entry_1h_late']['main'])} and {pct(s['entry_1h_late']['cheap'])}.")
    a("")
    a("## The two earlier stages")
    a("")
    cy = lambda arm: ", ".join(f"{n} in {y}" for y, n in sorted(co[arm].items()))
    a(f"- MEASURED, count stage, no return read: signals that did not overlap, by entry year, {100 * f['drop']:g}% fall: {cy('primary')}; "
      f"{100 * f['drop_shown']:g}% fall: {cy('alternate')}. One signal in each arm fell past the end date and was refused.")
    a(f"- STATED: the {100 * f['drop']:g}% arm needed at least {co['need']} in each of {co['years'][0]} and {co['years'][1]}, had them, and so became the judged arm.")
    dy = ", ".join(f"{n} in {y}" for y, n in sorted(d["by_year"].items()))
    a(f"- MEASURED, design stage, {d['span'][0]} to {d['span'][1]}: {d['trades']} trades ({dy}), {pct(d['main'])} a trade at {m['bp']} bp a side and "
      f"{pct(d['cheap'])} at {ch['bp']} bp, better than {d['beaten']} of {m['books']} random books. Without each year's best trade: "
      f"{pct(d['trimmed_main'])} and {pct(d['trimmed_cheap'])}. It went on to the held-back stage because the mean was above zero, as the plan says.")
    a(f"- STATED by the data custodian on ledger row {f['ledger_row']}: the design figure rests on one {d['delayed_coin']} position, entered "
      f"{d['delayed_in']} and sold {d['delayed_out']} under the registered wait rule, when the coin could be bought again. It held the only slot "
      f"for {d['delayed_days']:.0f} days and is the largest trade in that book. The design figure is not evidence for the rule.")
    a("")
    a("## Limits")
    a("")
    a(f"- STATED: this is one test of {f['tests_scored']} scored so far, with {f['passes_counted']} counted passes.")
    a(f"- STATED: the prices are Bitstamp hourly bars, not Binance.US order books. Source: [Bitstamp API]({f['source_url']}).")
    a("- STATED: a 5% hourly move on a thin pair can be one stale print. A bar test cannot tell that from a real fall.")
    a("- UNKNOWN: the cost on a venue we can use in the hour after a fall.")
    a("")
    a("## What happens next")
    a("")
    a(f"- STATED: practice card E14 (queue {f['e14']['queue']}, ledger {f['e14']['ledger']}) is to run this rule forward on Binance.US books with pretend money, "
      f"judged at {f['e14']['trades']} trades or {f['e14']['last']}. Now: {f['e14']['state']}.")
    a(f"- STATED: Measurement 133 (queue {f['m133']['queue']}) records the cost of a small trade on Binance.US every hour, "
      f"{f['m133']['wakes']} wakes to {f['m133']['last']}. Now: {f['m133']['state']}.")
    if r is None:
        a("- Blind recompute: pending. A helper who has not read the scorer will compute the marks again from the plan text alone.")
    else:
        rm, rc = r["line"]["75"], r["line"]["15"]
        a(f"- Blind recompute: done, stamped {r['finished_mt']} before the official result was opened, and it agrees on every mark. "
          f"MEASURED, official then recompute: {m['trades']} and {rm['trades']} trades; at {m['bp']} bp a side mean net {pct(m['mean_net'])} and "
          f"{pct(rm['mean_net'])}, without each year's best {pct(m['trimmed'])} and {pct(rm['trimmed'])}; at {ch['bp']} bp {pct(ch['mean_net'])} and "
          f"{pct(rc['mean_net'])}.")
        if r["pattern_seen"]:
            a("- STATED by the auditor: it had seen the pass and fail pattern in a commit subject before it started; its figures were blind.")
        if r["stream_unknown"]:
            a("- UNKNOWN: whether the auditor's random draws match the scorer's call for call. The shares agree.")
    a("")
    return "\n".join(o)


def summary(f):
    """The public summary: aggregate figures only."""
    keys = ("plan", "ledger_row", "page", "outcome", "passed", "source", "source_url", "coins", "window", "trades_by_year",
            "lines", "gross_mean", "break_even_bp", "break_even_all_marks_bp", "shown_only", "tests_scored", "passes_counted",
            "e14")
    out = {k: f[k] for k in keys}
    r = f["recompute"]
    out["recompute"] = None if r is None else {
        "verdict": r["verdict"], "finished_utc": r["finished_utc"], "sha256": r["sha256"],
        "by_year": {y: {"trades": n, "cheap": v} for y, (n, v) in sorted(r["by_year"].items())},
        "shib": {"trades": r["by_coin"]["SHIB"][0], "cheap": r["by_coin"]["SHIB"][1]},
        "without_shib": r["without_shib"], "thin_coins": r["thin_coins"], "thin": r["thin"]}
    out["design"] = {k: f["design"][k] for k in ("trades", "main", "trimmed_main", "delayed_coin", "delayed_in", "delayed_out")}
    return out


def main(custody=None, root=ROOT, recompute=RECOMPUTE):
    custody = custody or cfg()["custody"]["root"]
    res = load_results(custody)
    if res is None:
        print(f"Plan 76 result files are not on this computer ({custody}); {PAGE} and {SUMMARY} are left as they are.")
        return 0
    f = figures(res, load_recompute(recompute))
    (root / PAGE).write_text(page(f), encoding="utf-8")
    (root / SUMMARY).write_text(json.dumps(summary(f), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {PAGE} and {SUMMARY}; blind recompute {'pending' if f['recompute'] is None else 'filled'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
