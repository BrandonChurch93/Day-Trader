"""Render docs/research/110_tm06_why_may.md from the pinned off-repo TM06 May autopsy summary.

The summary was built read-only from the TM06-P-a..f session folders, the six-model results file and the per-coin
attribution by /home/user/workspace/rig/tm_notes/tm06_autopsy_work/summary.py. This script does not open prices or
score anything; every figure on the page is computed here from the summary.
Run from the repo root:
    python3 tools/report_saved_tm06_may.py /home/user/workspace/rig/tm_notes/tm06_autopsy_work/tm06_why_may_summary.json \
        > docs/research/110_tm06_why_may.md
Stops with TM06MAY_REPORT_PIN if the summary differs from its fingerprint below.
"""
import argparse
import json
import statistics
from hashlib import sha256
from pathlib import Path

SUMMARY_SHA = "443ff2230388e0f687f247e1b616bf6a74b31b313b3066293ba891ad659edd9b"
LETTERS = "abcdef"
MAY = "2026-05"
JUMP_PCT = 15.0  # an add counts as "rose sharply next day" above this next-wake rise; the summary lists them at it
# (model letter, May wake, coin or None for the wake summary, exact words quoted)
QUOTES = (
    ("a", 27, "XLM/USD", "+31% on 24h on volume 13x usual, breaking out in the last two hours on the day's heaviest volume"),
    ("d", 5, "NEAR/USD", "Up 13.9% in 24h on 2.2x usual volume, new breakout replacing DOGE."),
    ("b", 26, "XLM/USD", "on 1.29 times turnover while most coins fell"),
    ("f", 27, None, "XLM is up 31 percent on 13x volume but open interest left 45 percent and wiki is flat, the same blow-off as NEAR."),
    ("d", 15, None, "Going to cash until a coin shows real strength."),
)
pc = lambda x: f"{x:+.1f}%"
pp = lambda x: f"{x:+.2f}"
row = lambda *c: "| " + " | ".join(map(str, c)) + " |"
mon_name = lambda m: ("Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov")[int(m[5:]) - 4]
sid = lambda m, mon: f"TM06-P-{m}-{mon}"


def and_list(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def joined(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def short(model):
    return model.split(" ", 1)[1] if model.startswith("Claude ") else model


def render(S):
    months, models, sess = S["months"], S["models"], S["sessions"]
    assert set(models) == set(LETTERS) and len(months) == 8 and len(sess) == 48
    lead = S["yardstick_lead"]
    may_lead = lead[MAY]
    other_leads = [lead[m] for m in months if m != MAY]
    assert may_lead > max(other_leads)
    top7 = {mon: sess[sid("a", mon)]["top7"] for mon in months}
    equal = {mon: sess[sid("a", mon)]["equal"] for mon in months}
    btc_may = sess[sid("a", MAY)]["btc"]
    pos7 = [m for m in months if top7[m] > 0]
    ahead7 = [m for m in months if top7[m] > equal[m]]
    assert all(abs(sess[sid(m, mon)]["top7"] - top7[mon]) < 1e-9 for m in LETTERS for mon in months)
    chk = S["may_check"]
    nums = sum(c["numbers"] for c in chk.values())
    own = sum(c.get("own", 0) for c in chk.values())
    other = sum(c.get("other", 0) for c in chk.values())
    off = sum(c.get("off", 0) for c in chk.values())
    events = sum(c["event_words"] for c in chk.values())
    assert own + other + off == nums
    attr = {}
    for m in LETTERS:
        pnl = S["may_attr"][m]["pnl"]
        ranked = sorted(pnl.items(), key=lambda kv: -kv[1])
        gross = sum(pnl.values())
        attr[m] = dict(top=ranked[:4], gross=gross, share=sum(v for _, v in ranked[:4]) / gross,
                       held=S["may_attr"][m]["held"])
    y7 = sorted(S["may_attr"]["top7"]["pnl"].items(), key=lambda kv: -kv[1])[:4]
    pres = S["prescient"]
    pres_may = [p for p in pres if p["sid"].endswith(MAY)]
    pres_top3 = sum(p["rank24"] <= 3 for p in pres)
    by_month = {mon: sum(p["sid"].endswith(mon) for p in pres) for mon in months}
    busiest = max(by_month, key=by_month.get)
    quotes = []
    for m, k, coin, words in QUOTES:
        step = S["steps_may_" + m][k]
        source = step["why"] if coin is None else step["reasons"][coin]
        assert words in source, (m, k)
        quotes.append((m, k, coin, words, step["utc"][:10]))
    b_xlm = next(p for p in pres_may if p["sid"] == sid("b", MAY) and p["coin"] == "XLM")
    # Grok's cash run in May
    f_steps = S["steps_may_f"]
    last_held = max(s["k"] for s in f_steps if s["target"])
    f_cash_run = [s for s in f_steps if s["k"] > last_held]
    assert all(not s["target"] for s in f_cash_run)
    f_cash_from = f_cash_run[0]["utc"][:10]
    f_may = sess[sid("f", MAY)]
    # Sonnet's cash wakes
    dcash = {mon: S["cash"][sid("d", mon)] for mon in months}
    cash_mean = lambda xs, key: statistics.mean(x[key] for x in xs) if xs else None
    better = [m for m in LETTERS if sess[sid(m, MAY)]["gain"] > top7[MAY]]
    late = months[3:]
    lost_all = [mon for mon in late if all(sess[sid(m, mon)]["gain"] < 0 for m in LETTERS)]
    gained_all = [mon for mon in late if all(sess[sid(m, mon)]["gain"] > 0 for m in LETTERS)]
    trail_top7 = [mon for mon in gained_all if all(sess[sid(m, mon)]["gain"] < top7[mon] for m in LETTERS)]

    L = [
        "# TM06: why May happened", "",
        "MEASURED. The six picker models (TM06-P, [page 102](102_time_machine_tm06_six_models.md)) bought coins that were "
        "already at the top of the screen they were shown. May 2026 was the month in which that paid by far the most: the plain "
        f"top_7d_rise yardstick, which holds the five coins with the biggest 7-day rise at each daily wake, made "
        f"{pc(top7[MAY])} in May on the same coins the models held, against {pc(equal[MAY])} for holding all 20 coins "
        f"and {pc(btc_may)} for bitcoin. The yardstick's next-day lead over the 20-coin average was {pp(may_lead)} "
        f"percentage points a day in May and between {pp(min(other_leads))} and {pp(max(other_leads))} in the other "
        f"seven months. The yardstick also made money in {joined([mon_name(m) for m in pos7 if m != MAY])}, but it beat "
        f"holding all 20 coins only in {joined([mon_name(m) for m in ahead7])}: by {top7[MAY] - equal[MAY]:.1f} percentage "
        f"points in May against at most {max(top7[m] - equal[m] for m in ahead7 if m != MAY):.1f} in the others.", "",
        f"MEASURED. Of {nums:,} numbers the models wrote in their May reasons, {own:,} match that coin's screen at that "
        f"wake and {other} match another coin on the same screen. The other {off} are ratios worked out from screen "
        f"counts, one portfolio weight and one daily-bar look. The screens for April to June carried "
        f"{S['headlines_apr_jun']} headlines, and no May reason names an outside event ({events} event words found).", "",
        "Verdict: screen-based for all six. Memory is not ruled out. A model that remembered May could still pick "
        "the right coins and justify them with screen numbers, and each model's knowledge line for these months is "
        f"UNKNOWN. One pick is thin: GPT-6.2 Sol bought XLM on {quotes[2][4]}, when it was the number "
        f"{b_xlm['rank24']} 24-hour riser on a red day, \"{quotes[2][3]}\". It rose {b_xlm['next_pct']:.0f}% the next day. "
        "That single pick cannot be told apart from foresight.", "",
        "## Each model against the yardstick, by month", "",
        "MEASURED. Net gain at the 12 bp main fee on a $1,000 book. Next-day lead is the yardstick's average next-wake "
        "return minus the 20-coin average, in percentage points a day, gross.", "",
        row("Model", *[mon_name(m) for m in months]), row("---", *["---:"] * len(months)),
    ]
    for m in LETTERS:
        L.append(row(models[m], *[pc(sess[sid(m, mon)]["gain"]) for mon in months]))
    L += [
        row("top_7d_rise", *[pc(top7[mon]) for mon in months]),
        row("Hold all 20", *[pc(equal[mon]) for mon in months]),
        row("Yardstick next-day lead", *[pp(lead[mon]) for mon in months]), "",
        f"MEASURED. In May {len(better)} of 6 models beat the yardstick ({', '.join(short(models[m]) for m in better)}). "
        f"From July on, all six lost money in {and_list([mon_name(m) for m in lost_all])}. In "
        f"{' and '.join(mon_name(m) for m in gained_all)} all six made money, and in "
        f"{' and '.join(mon_name(m) for m in trail_top7)} every one trailed top_7d_rise.", "",
        "## What each model held in May", "",
        "MEASURED. Gross dollars by coin on the $1,000 book, before costs, from the session fills. The top four can "
        "exceed 100% of the gross gain when the other coins lost.", "",
        row("Model", "Net gain", "Twin median", "Top four coins, gross $", "Gross gain", "Top four share"),
        row("---", "---:", "---:", "---", "---:", "---:"),
    ]
    for m in LETTERS:
        a, s = attr[m], sess[sid(m, MAY)]
        coins = ", ".join(f"{c.split('/')[0]} {v:.0f}" for c, v in a["top"])
        L.append(row(models[m], pc(s["gain"]), pc(s["twin_median"]), coins, f"${a['gross']:.0f}", f"{a['share']:.0%}"))
    L += [
        "", f"MEASURED. The yardstick's own top coins in May: {', '.join(f'{c.split(chr(47))[0]} {v:.0f}' for c, v in y7)} "
        "(gross $).", "",
        f"MEASURED. Grok 4.7 made its May gain before {f_cash_from}, then held cash on all {len(f_cash_run)} wakes from "
        f"{f_cash_from} to the end of the month ({f_may['cash_wakes']} cash wakes in all). It still finished at the "
        f"{f_may['pct']:.0f}th percentile of its random twins, which swap on the same days.", "",
        "## Were the reasons on the screen", "",
        "MEASURED. Every number followed by % or x in a May coin reason, compared with the packet the model was shown at "
        "that wake (within 0.6 points or 6%).", "",
        row("Model", "Numbers", "On that coin's screen", "On another coin's screen", "Not on the screen"),
        row("---", "---:", "---:", "---:", "---:"),
    ]
    for m in LETTERS:
        c = chk[m]
        L.append(row(models[m], c["numbers"], c.get("own", 0), c.get("other", 0), c.get("off", 0)))
    L += [row("All", f"{nums:,}", f"{own:,}", other, off), "", "Quoted word for word from the May notes:", ""]
    for m, k, coin, words, day in quotes:
        where = f"{coin.split('/')[0]} reason" if coin else "wake summary"
        L.append(f"- {models[m]}, {day}, {where}: \"{words}\"")
    L += [
        "", "## Bought before or after the move", "",
        "MEASURED. For every coin a model added in May: its rank by 24-hour change on the screen (1 is the biggest "
        "riser of 20) and its next-day return minus the 20-coin average.", "",
        row("Model", "Adds", "Median 24-hour rank", "Share in the top 3", "Next-day lead, points"),
        row("---", "---:", "---:", "---:", "---:"),
    ]
    for m in LETTERS:
        s = sess[sid(m, MAY)]
        L.append(row(models[m], s["adds"], f"{s['median_rank24']:g}", f"{s['share_top3']:.0%}", pp(s["add_lead"])))
    L += [
        row("top_7d_rise picks", "", "", "", pp(may_lead)), "",
        f"MEASURED. Across all 48 sessions, {len(pres)} adds rose more than {JUMP_PCT:.0f}% the next day; {pres_top3} of "
        f"them were already a top-3 24-hour riser. {len(pres_may)} were in May; {mon_name(busiest)} had the most "
        f"({by_month[busiest]}) and was not a month in which the models beat the yardstick.", "",
        "## Sonnet 5.5 in April and June", "",
    ]
    d = {mon: sess[sid("d", mon)] for mon in months}
    L += [
        f"MEASURED. Claude Sonnet 5.5 also sat above the 95th percentile of its twins in April ({pc(d['2026-04']['gain'])}, "
        f"percentile {d['2026-04']['pct']:.1f}, yardstick {pc(top7['2026-04'])}) and June ({pc(d['2026-06']['gain'])}, "
        f"percentile {d['2026-06']['pct']:.1f}, yardstick {pc(top7['2026-06'])}). Its April gain came mostly from holding "
        f"ZEC ({S['sonnet_april_zec_days']} days). Its June gain came from cash: it went to cash when the screen was "
        "red, and in June the red days kept going. In October and November the same habit dodged only small next-day "
        f"losses ({pc(cash_mean(dcash['2026-10'], 'next_mean'))} and {pc(cash_mean(dcash['2026-11'], 'next_mean'))} for the "
        "20 coins) and both months lost.", "",
        row("Month", "Cash wakes", "20-coin 24-hour change before going to cash", "20-coin next-day return on those wakes",
            "Month net"),
        row("---", "---:", "---:", "---:", "---:"),
    ]
    for mon in months:
        xs = [x for x in dcash[mon]]
        if not xs:
            L.append(row(mon_name(mon), d[mon]["cash_wakes"], "", "", pc(d[mon]["gain"])))
            continue
        L.append(row(mon_name(mon), d[mon]["cash_wakes"], pc(cash_mean(xs, "prior24")), pc(cash_mean(xs, "next_mean")),
                     pc(d[mon]["gain"])))
    L += [
        "", "MEASURED. Cash wakes counts every wake with an empty pick; the two averages use the cash wakes that had a "
        "next wake.", "",
        "## July to November", "",
        "MEASURED. The models kept the same habit: most adds were coins already near the top of the 24-hour list "
        f"(median 24-hour rank by model and month between "
        f"{min(sess[sid(m, mon)]['median_rank24'] for m in LETTERS for mon in late):g} and "
        f"{max(sess[sid(m, mon)]['median_rank24'] for m in LETTERS for mon in late):g}). What changed was the market: "
        "the yardstick's next-day lead fell to "
        + ", ".join(f"{pp(lead[mon])} ({mon_name(mon)})" for mon in late) + ", so buying what had just risen stopped paying.", "",
        "## Verdict and limits", "",
        "- Screen-based for all six models. The reasons cite screen values, the buys follow visible moves, and the "
        "mechanical screen rule made most of the same money in May.",
        "- Memory not ruled out. STATED by the maker: a June 2026 knowledge line for Claude Opus 5.5 and GPT-6.2 Sol "
        "(page 102); UNKNOWN for the other four, and UNKNOWN how much any of them knows of these months. A strong spring and a "
        "weak summer to autumn is also what a spring knowledge line would produce. TM07 runs on weeks after the stated "
        "knowledge lines and is the test that can separate the two.",
        f"- One thin pick named: GPT-6.2 Sol's XLM buy on {quotes[2][4]}.",
        "- Next-day leads are gross and one wake ahead; they say which way the picks leaned, not what a trader would net.",
        "- The number check is a tolerance match. A number that is on the screen could still have been chosen for "
        "another reason.", "",
        "## Run record", "",
        "STATED. Built read-only from the TM06-P-a to f session folders for April to November under "
        "/home/user/workspace/rig/tm_runs and from /home/user/workspace/rig/tm_notes/results_tm06_six_fast.json. Scripts "
        "and the full note are off repo in /home/user/workspace/rig/tm_notes/tm06_autopsy_work and "
        "/home/user/workspace/rig/tm_notes/tm06_six_may_autopsy.md.", "",
        f"- Summary SHA-256 `{SUMMARY_SHA}`", "",
    ]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("summary", type=Path)
    a = ap.parse_args()
    blob = a.summary.read_bytes()
    if sha256(blob).hexdigest() != SUMMARY_SHA:
        ap.exit(2, "TM06MAY_REPORT_PIN\n")
    print(render(json.loads(blob)), end="")


if __name__ == "__main__":
    main()
