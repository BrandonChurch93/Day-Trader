"""Print the Replay 48 result page from its pinned saved result, without opening market data or scoring.

Usage, from the repository root:
    python3 research_rig/report_48.py /home/user/workspace/rig/data/replay_48/results_48.json \
        [/home/user/workspace/rig/plan48_review/recompute_48.md]

Every figure on the page comes from the saved result, the frozen plan settings in config/thresholds.yaml
(replay_48_plan), research_rig/CALIBRATION_48.json, or the pinned independent recompute note. The few facts that
exist in none of those files are in STATED below with who reported them; they are printed as STATED, not MEASURED.
"""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parent.parent
RESULT_SHA = "d303cc1b980c4bbedf92a53379e45150d3424aed44fbd97dfbbacbd4c314d1ba"
RECOMPUTE_SHA = "6a699f08fb83fcefb978c5b344cc38a80a47294c8c4e0073c1cab019a0ef7492"
CONFIG = ROOT / "config" / "thresholds.yaml"
CALIBRATION = ROOT / "research_rig" / "CALIBRATION_48.json"
MARK_ORDER = ("all_turns", "positive_mean", "positive_years", "beats_benchmark_mean", "beats_benchmark_years",
              "positive_without_best", "beats_roster_mean")
# Facts held in no file this script reads. Each is printed once, labelled STATED, with its source.
STATED = {
    "zero_credited_fund_turns": 470,       # custodian's off-packet coverage table, as reported by the lead agent
    "merger_turn": 2025,                   # lead agent: the NXC/NXN merger falls in this turn
    "glimpsed_pages": 2,                   # lead agent: closing-price pages the distribution reviewer glimpsed
}


def pct(x, d=2):
    return f"{x * 100:+.{d}f}%"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def plan_settings():
    return yaml.safe_load(CONFIG.read_text())["replay_48_plan"]["value"]


def recompute_facts(text):
    """Counts read from the pinned independent recompute note."""
    picks = re.search(r"(\d+)/(\d+) ordered picks matched", text)
    marks = re.search(r"(\d+)/(\d+) marks matched", text)
    turns = [line for line in text.splitlines() if re.match(r"^\| 20\d\d \| \d/\d \|", line)]
    triples = [[c.strip() for c in line.strip("|").split("|")] for line in turns]

    def matched(col):
        return sum(abs(float(cells[col].split("/")[2])) < 1e-9 for cells in triples)

    diffs = {}
    for level, field, value in re.findall(r"^\| (2017|summary) \| (\w+) \| ([+-][0-9.]+E-?\d+) \|$", text, re.M):
        diffs[(level, field)] = float(value)
    seconds = re.search(r"from (\d+\.\d+) to (\d+\.\d+) seconds", text)
    floor = re.search(r"above the (\d+)-second requirement", text)
    found = dict(picks=(int(picks[1]), int(picks[2])), marks=(int(marks[1]), int(marks[2])), turns=len(triples),
                 portfolio=matched(2), benchmark=matched(3), diffs=diffs,
                 seconds=(seconds[1], seconds[2]), floor=int(floor[1]))
    need = {("2017", "roster_ew"), ("summary", "mean_roster_ew"), ("summary", "mean_portfolio_minus_roster_ew"),
            ("summary", "mean_portfolio_minus_roster_ew_price_only")}
    if not need <= set(diffs) or found["turns"] == 0:
        raise ValueError("recompute note does not carry the expected tables")
    return found


def check(data, cfg, calib):
    j, job = data["judged"], data["job"]
    years, m = j["years"], cfg["marks"]
    p = [y["portfolio"] for y in years]
    vs_b = [y["portfolio"] - y["benchmark"] for y in years]
    vs_ew = [y["portfolio"] - y["roster_ew"] for y in years]
    vs_ew_price = [y["portfolio_price"] - y["roster_ew_price"] for y in years]
    trimmed = sorted(p, reverse=True)[m["drop_best"]:]
    mean = lambda xs: sum(xs) / len(xs)
    marks = {
        "all_turns": len(years) == cfg["turns"],
        "positive_mean": mean(p) > 0,
        "positive_years": sum(v > 0 for v in p) >= m["min_positive_years"],
        "beats_benchmark_mean": mean(vs_b) > 0,
        "beats_benchmark_years": sum(v > 0 for v in vs_b) >= m["min_years_ahead_of_benchmark"],
        "positive_without_best": mean(trimmed) > 0,
        "beats_roster_mean": mean(vs_ew) > 0 and mean(vs_ew_price) > 0,
    }
    close = lambda a, b: abs(a - b) < 1e-12
    if (
        (job["schema"], job["ledger"], job["queue"]) != (1, 182, 86)
        or set(j["marks"]) != set(MARK_ORDER) or marks != j["marks"] or all(marks.values()) != j["passed"]
        or [y["turn"] for y in years] != list(range(cfg["first_turn"], cfg["last_turn"] + 1))
        or any(y["picks"] != cfg["picks"] or len(y["held"]) != cfg["picks"] for y in years)
        or not close(mean(p), j["mean_portfolio"]) or not close(mean(vs_b), j["mean_portfolio_minus_benchmark"])
        or not close(mean(vs_ew), j["mean_portfolio_minus_roster_ew"])
        or not close(mean(vs_ew_price), j["mean_portfolio_minus_roster_ew_price_only"])
        or not close(mean(trimmed), j["mean_without_best"])
        or sum(v > 0 for v in p) != j["positive_years"] or sum(v > 0 for v in vs_b) != j["years_ahead_of_benchmark"]
        or calib["trials"] != cfg["calibration"]["trials"] or calib["seed"] != cfg["calibration"]["seed"]
    ):
        raise ValueError("saved results do not reconcile")
    return dict(vs_b=vs_b, vs_ew=vs_ew, vs_ew_price=vs_ew_price)


def render(data, cfg, calib, recompute):
    j, job, shown = data["judged"], data["job"], data["shown_only"]
    derived = check(data, cfg, calib)
    years, m, cost = j["years"], cfg["marks"], cfg["cost"]
    n, picks, sleeve, capital = cfg["turns"], cfg["picks"], cfg["sleeve_usd"], cfg["capital"]
    claim = datetime.fromisoformat(job["claimed_utc"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S UTC")
    gates = j["marks"]
    outcome = "Passed" if j["passed"] else "Did not pass"
    total = lambda key: sum(y[key] for y in years)
    held_total, elig_total = n * picks, total("eligible")
    best = max(years, key=lambda y: y["portfolio"])
    rate = calib["pass_rate"]
    zero, fifth = shown["zero_cost"], shown["fifth_january_session_exit"]
    lose_ew = sum(v > 0 for v in derived["vs_ew"])
    lose_ew_price = sum(v > 0 for v in derived["vs_ew_price"])
    dollars = lambda x: f"{'+' if x >= 0 else '-'}${abs(x) * capital:.2f}"
    more = lambda x: f"${abs(x) * capital:.2f} {'more' if x >= 0 else 'less'}"
    labels = {
        "all_turns": ("Turns", f"all {n} turns scored", f"{len(years)} of {n}"),
        "positive_mean": ("Net mean", "yearly portfolio mean above zero", pct(j["mean_portfolio"])),
        "positive_years": ("Positive years", f"at least {m['min_positive_years']} of {n} above zero",
                           f"{j['positive_years']} of {n}"),
        "beats_benchmark_mean": ("Against MUB, mean", "mean of portfolio minus MUB above zero",
                                 pct(j["mean_portfolio_minus_benchmark"])),
        "beats_benchmark_years": ("Against MUB, years", f"at least {m['min_years_ahead_of_benchmark']} of {n} "
                                  "years ahead of MUB", f"{j['years_ahead_of_benchmark']} of {n}"),
        "positive_without_best": ("Without best year", f"mean above zero after removing the best {m['drop_best']}",
                                  pct(j["mean_without_best"])),
        "beats_roster_mean": ("Loser effect", "portfolio minus roster equal weight above zero, with documented "
                              "cash and price only", f"{pct(j['mean_portfolio_minus_roster_ew'])} with cash, "
                              f"{pct(j['mean_portfolio_minus_roster_ew_price_only'])} price only"),
    }
    rc = recompute
    d17 = rc["diffs"][("2017", "roster_ew")]
    dmean = rc["diffs"][("summary", "mean_portfolio_minus_roster_ew_price_only")]
    lines = [
        "# Replay 48. Muni closed-end funds after year-end tax-loss selling", "",
        f"MEASURED. {outcome}, **{sum(gates.values())} of {len(gates)} frozen marks**, in one scored run claimed "
        f"{claim}. Over {n} yearly turns (December 2016 to January 2026) the worst {picks} municipal closed-end "
        f"funds by price return up to late December averaged {pct(j['mean_portfolio'])} net from the last "
        f"December close to the last January close. MUB averaged {pct(j['mean_benchmark'])} on the same clock and "
        f"the equal-weight roster of all eligible funds {pct(j['mean_roster_ew'])}. The portfolio was above zero in "
        f"{j['positive_years']} of {n} years and ahead of MUB in {j['years_ahead_of_benchmark']} of {n}.", "",
        f"STATED. A pass here is one test of a published effect on ten data points. It is a reason to watch the "
        f"December 2026 turn with pretend money (`practice/traders/E04_muni_cef_january_watch.md`), not "
        f"clearance to trade. The pre-run synthetic world with a muni-wide year-end rally and no loser effect "
        f"passed {rate['beta_only']:.2%} of the time, so this pass cannot by itself separate the two.", "",
        "## The rule", "",
        "STATED, from the [frozen plan](../../research_rig/PREREG_48_muni_cef_tax_loss.md). Each turn uses the "
        "muni closed-end funds on the SEC closed-end fund roster for that year. A fund is eligible if it has a raw "
        "SIP daily bar with nonzero volume on every session from the first January close through entry, no split "
        f"in that span, and one whole share fits in a ${sleeve} sleeve after the entry cost. At the second-to-last "
        "December close, rank eligible funds by price return since the first January close, lowest first. Buy the "
        f"worst {picks}, ${sleeve} each in whole shares, at the last December close. Sell at the last January close. "
        "Dated distributions are credited in cash, not reinvested. Leftover cash earns nothing.", "",
        f"STATED. Cost per side is half the measured closing spread plus {cost['extra_bps']} bp, from SIP quotes "
        f"between {cost['measure_start']} and {cost['measure_end']} New York time, each quote valid "
        f"{cost['expiry_seconds']} seconds and at least {cost['min_coverage_seconds']} seconds of cover. If cover is "
        f"short, a {cost['proxy_half_bps']} bp half-spread proxy is used for that side. MUB is one ${capital} "
        "whole-share sleeve on the same clock and rules. The roster equal weight is the mean of "
        f"${sleeve} sleeves over every eligible fund that turn.", "",
        "## Frozen marks", "",
        "MEASURED. All seven had to pass at the judged cost. Zero is not positive.", "",
        row("Mark", "Bar", "Measured", "Verdict"), row("---", "---", "---:", "---"),
    ]
    lines.extend(row(*labels[k], "met" if gates[k] else "not met") for k in MARK_ORDER)
    lines.extend([
        "", "## The ten turns", "",
        "MEASURED. Net returns at the judged cost; the turn is the December year. Cash not documented counts "
        "held funds whose in-window distribution could not be documented and was credited zero. Proxy sides counts "
        f"entry or exit sides of held funds priced at the {cost['proxy_half_bps']} bp proxy. Fund names are kept "
        "off this page.", "",
        row("Turn", "Portfolio", "MUB", "Roster equal weight", "Eligible", "Held, cash not documented",
            "Held proxy sides"),
        row("---", "---:", "---:", "---:", "---:", "---:", "---:"),
    ])
    lines.extend(row(y["turn"], pct(y["portfolio"]), pct(y["benchmark"]), pct(y["roster_ew"]), y["eligible"],
                     f"{y['held_empty_cash']} of {picks}", y["held_proxy_sides"]) for y in years)
    lines.extend([
        row("Mean", pct(j["mean_portfolio"]), pct(j["mean_benchmark"]), pct(j["mean_roster_ew"]), "",
            f"{total('held_empty_cash')} of {held_total}", total("held_proxy_sides")),
        "", f"MEASURED. The best turn was {best['turn']} at {pct(best['portfolio'])}; without it the mean is "
        f"{pct(j['mean_without_best'])}. Held funds had no exit bar in {total('held_missing_exit')} fund-turns; "
        f"eligible funds in {total('eligible_missing_exit')}.", "",
        "## Against the roster, price only", "",
        "MEASURED. The loser mark compares the five losers with every eligible fund in the same turn, so a "
        "muni-wide January move cancels out. It is shown twice: with documented cash, and with cash set to zero "
        "for every fund on both sides.", "",
        row("Turn", "Portfolio minus roster, with cash", "Portfolio minus roster, price only"),
        row("---", "---:", "---:"),
    ])
    lines.extend(row(y["turn"], pct(a), pct(b)) for y, a, b in zip(years, derived["vs_ew"], derived["vs_ew_price"]))
    lines.extend([
        row("Mean", pct(j["mean_portfolio_minus_roster_ew"]), pct(j["mean_portfolio_minus_roster_ew_price_only"])),
        row("Years above zero", f"{lose_ew} of {n}", f"{lose_ew_price} of {n}"),
        "", "## Shown only", "",
        "MEASURED, shown only. These cannot replace or rescue a mark. The fifth-session exit sells at the close of "
        "the fifth January session instead of the last (the five-day window in Starks, Yong and Zheng). The "
        "zero-cost line uses the same share counts with no spread or fee.", "",
        row("Line", "Portfolio mean", "MUB mean", "Minus MUB", "Minus roster, with cash", "Minus roster, price only",
            "Positive years", "Years ahead of MUB"),
        row("---", "---:", "---:", "---:", "---:", "---:", "---:", "---:"),
    ])
    for name, b in (("Judged: last January close", j), ("Shown only: fifth January session", fifth),
                    ("Shown only: zero cost", zero)):
        lines.append(row(name, pct(b["mean_portfolio"]), pct(b["mean_benchmark"]),
                         pct(b["mean_portfolio_minus_benchmark"]), pct(b["mean_portfolio_minus_roster_ew"]),
                         pct(b["mean_portfolio_minus_roster_ew_price_only"]), f"{b['positive_years']} of {n}",
                         f"{b['years_ahead_of_benchmark']} of {n}"))
    lines.extend([
        "", f"MEASURED. Costs took {(zero['mean_portfolio'] - j['mean_portfolio']) * 100:.2f} percentage points a year "
        "off the portfolio mean, the gap between the zero-cost and judged lines.", "",
        "## What ten turns could show", "",
        f"MEASURED on synthetic data before the run (`research_rig/CALIBRATION_48.json`, {calib['trials']:,} trials, "
        f"seed {calib['seed']}). With no edge at all the seven marks pass {rate['zero_edge']:.2%} of the time, under "
        f"the {cfg['calibration']['null_ceiling']:.0%} ceiling. With a muni-wide year-end premium and no loser excess "
        f"they pass {rate['beta_only']:.2%} of the time. A true loser excess of 1%, 2% or 3% a year passes "
        f"{rate['loser_edge_0.01']:.2%}, {rate['loser_edge_0.02']:.2%} or {rate['loser_edge_0.03']:.2%} of the time. "
        "The synthetic spreads are stated assumptions, not estimates.", "",
        "## In dollars", "",
        f"MEASURED. On a ${capital} sleeve, once a year, the mean net result was {dollars(j['mean_portfolio'])} a "
        f"year, {more(j['mean_portfolio_minus_benchmark'])} than MUB and "
        f"{more(j['mean_portfolio_minus_roster_ew'])} than the equal-weight roster. The worst turn was "
        f"{dollars(min(y['portfolio'] for y in years))} and the best {dollars(best['portfolio'])}. Before taxes. "
        "STATED. This is one trade a year; it is not a way to grow a small account quickly.", "",
        "## Gaps", "",
        f"- STATED, from the custodian's off-packet coverage table as reported by the lead agent: "
        f"{STATED['zero_credited_fund_turns']} roster fund-turns had a distribution that could not be documented "
        f"and were credited zero cash. MEASURED: {total('eligible_empty_cash'):,} of {elig_total:,} eligible fund-turns "
        f"and {total('held_empty_cash')} of {held_total} held fund-turns carried an empty cash list. Zero credit "
        "can only lower a fund's return, so it pushes the portfolio's mean and its lead over MUB down, not up. "
        "Against the roster it can push either way, which is why the loser mark also had to pass price only.",
        "- STATED. Split evidence is vendor-derived: the vendor's corporate-action pages, raw against split-adjusted "
        f"closes from the same vendor, and a {cfg['split_check_ratio']}x jump backstop, with any nonzero case resolved by the reviewer. "
        "None was found. A split the vendor missed in both series would not be caught unless it broke the backstop.",
        f"- STATED, from the lead agent: the NXC/NXN merger falls in turn {STATED['merger_turn']}. MEASURED: in that "
        f"turn {years[-1]['eligible_missing_exit']} eligible funds had no bar at the exit and were valued at their "
        f"last close under the plan's rule; " + ("none was held." if years[-1]["held_missing_exit"] == 0 else
                                         f"{years[-1]['held_missing_exit']} of them were held."),
        f"- MEASURED. {total('held_proxy_sides')} held entry or exit sides used the {cost['proxy_half_bps']} bp proxy "
        "because quotes did not cover the window, so their cost is assumed, not measured.",
        f"- STATED, from the lead agent: before the run the distribution reviewer glimpsed "
        f"{STATED['glimpsed_pages']} pages showing closing prices. The ranking and fills come only from the sealed "
        "packet.",
        "- STATED. MUB is the yardstick. It holds investment-grade muni bonds without leverage, while the funds "
        "are leveraged and trade at moving discounts, so beating MUB is partly the funds' extra risk. The roster "
        "comparison is the cleaner test of the loser effect.",
        f"- STATED. One trade a year, so {n} data points. Years are not independent draws, and the same funds may "
        "be picked in several years.",
        f"- STATED. The funds are thin. A ${sleeve} order may not get the close, and the size this could carry is "
        "small. UNKNOWN: how much money it would take to move the price.",
        "- STATED. This is a single test of a published effect: [Starks, Yong and Zheng, Journal of Finance 61(6), "
        "2006](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2006.01011.x), with recent evidence from "
        "[Carrion and Zhang, Journal of Financial Research 47(4), 2024]"
        "(https://onlinelibrary.wiley.com/doi/10.1111/jfir.12384). It is not a replication of their regressions.",
        "", "## Independent recompute", "",
        f"MEASURED, from the recompute note (`/home/user/workspace/rig/plan48_review/recompute_48.md`, off repo, "
        f"SHA-256 `{RECOMPUTE_SHA}`). A helper who did not read the scoring code matched "
        f"{rc['picks'][0]} of {rc['picks'][1]} picks in order, {rc['portfolio']} of {rc['turns']} portfolio returns, "
        f"{rc['benchmark']} of {rc['turns']} MUB returns and {rc['marks'][0]} of {rc['marks'][1]} marks. One "
        f"difference: in turn 2017 the roster equal weight differs by {abs(d17) * 1e4:.2f} bp "
        f"({abs(dmean) * 1e4:.3f} bp in the ten-year mean of each roster comparison), from one eligible fund that was "
        "not picked, on its entry cost. The engine treats a locked quote (bid equal to ask) as ending the valid "
        f"quote before it and adding no valid time, under the plan 36 convention the plan cites. That left "
        f"{float(rc['seconds'][1]):.0f} valid seconds, under the {rc['floor']}-second floor, so the proxy applied; "
        f"the recompute counted locked time and got {float(rc['seconds'][0]):.0f}. STATED: the plan text alone is "
        "ambiguous there; the code auditor confirmed the engine follows the cited convention. It changes no pick, "
        "return of the portfolio or MUB, or mark.", "",
        "## Run record", "",
        f"MEASURED. The saved result records the claim at {claim} for queue {job['queue']} and ledger {job['ledger']}. "
        "STATED. The lead agent reports one validation and one scored run. This page reads the saved result only; "
        "there was no rerun and the lock stays.", "",
        f"- Approval commit `{job['approval_commit']}`",
        f"- Strategy freeze commit `{job['freeze_commit']}`",
        f"- Saved result SHA-256 `{RESULT_SHA}`",
        f"- Freeze manifest SHA-256 `{job['freeze_sha256']}`",
        f"- Input manifest SHA-256 `{job['input_sha256']}`",
        f"- Roster SHA-256 `{job['roster_sha256']}`",
        f"- Distributions SHA-256 `{job['distributions_sha256']}`", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("result", type=Path)
    parser.add_argument("recompute", type=Path, nargs="?",
                        default=Path("/home/user/workspace/rig/plan48_review/recompute_48.md"))
    args = parser.parse_args()
    try:
        blob = args.result.read_bytes()
        if sha256(blob).hexdigest() != RESULT_SHA:
            parser.exit(2, "P48_REPORT_RESULT_PIN\n")
        note = args.recompute.read_bytes()
        if sha256(note).hexdigest() != RECOMPUTE_SHA:
            parser.exit(2, "P48_REPORT_RECOMPUTE_PIN\n")
        output = render(json.loads(blob), plan_settings(), json.loads(CALIBRATION.read_text()),
                        recompute_facts(note.decode()))
    except (OSError, KeyError, TypeError, ValueError, IndexError):
        parser.exit(2, "P48_REPORT_REFUSED\n")
    print(output, end="")


if __name__ == "__main__":
    main()
