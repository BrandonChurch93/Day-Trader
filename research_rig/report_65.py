"""Build Replay 65's report from the pinned saved aggregate; never score or read market inputs.

Run: python3 research_rig/report_65.py [--result PATH] [--output PATH]
Reads only the saved aggregate results_65.json (pinned by SHA-256), the replay_65_plan block of
config/thresholds.yaml, research_rig/APPROVAL_65.md for the freeze commit and inputs digest, and the pre-run
power file research_rig/POWER_65.json (pinned by SHA-256). It never runs score_65.py and never opens the
sealed inputs in rig/data/plan65_inputs.
"""
import argparse
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parent.parent
RESULT = Path("/home/user/workspace/rig/data/replay_65/results_65.json")
TARGET = ROOT / "docs/research/139_replay_65_stock_bond_rebalancing.md"
RESULT_SHA = "5475bf58f123e68dc26069b2fbfe34a8074fe46a1ab6421aa6face52a5fa1d42"
POWER = ROOT / "research_rig/POWER_65.json"
POWER_SHA = "5ad7b0c52fec7504d2acacdcb458adeef1fb9f68a220afbdaf35bc3f6294cbba"
APPROVAL = ROOT / "research_rig/APPROVAL_65.md"
FREEZE = "a6688cb7da016a182d38ceaedd773598047a4133"
# Independent recompute: a second helper's own numbers, saved off the repo. None means pending.
# When it arrives, set RECOMPUTE_SHA (and RECOMPUTE_FIXED) and adapt recompute_lines to its keys.
RECOMPUTE = Path("/home/user/workspace/rig/data/replay_65_notes/recompute_65.json")
RECOMPUTE_SHA = None
RECOMPUTE_FIXED = None
# STATED by the lead agent: the saved aggregate holds no run clock.
RUN_WINDOW = ("2026-11-26 11:36:49 UTC", "2026-11-26 11:36:52 UTC")
PLAN_PATH = "../../research_rig/PREREG_65_stock_bond_rebalance_spread.md"
PAPER = "https://www.nber.org/system/files/working_papers/w33554/w33554.pdf"
PLAN = ROOT / "research_rig/PREREG_65_stock_bond_rebalance_spread.md"


def paper_claims():
    """The paper's own Sharpe figures, as the frozen plan quotes them (Table 6, p.38 to 39; p.39)."""
    text = PLAN.read_text()
    gross = re.search(r"Reported results \(Table 6, p\.38 to 39\): Sharpe (\d\.\d+) gross", text)
    net = re.search(r"Sharpe ratio net of costs, .{0,80}?stays close to (\d)", text, re.S)
    if not (gross and net):
        raise ValueError("Replay 65 plan no longer quotes the paper's Sharpe figures")
    return gross[1], f"about {net[1]}"


def read_pinned(path, pin, name):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != pin:
        raise ValueError(f"Replay 65 {name} does not match its SHA-256")
    return json.loads(raw)


def read_recompute():
    return None if RECOMPUTE_SHA is None else read_pinned(RECOMPUTE, RECOMPUTE_SHA, "recompute")


def recompute_lines(j, rc):
    if rc is None:
        return "Pending."
    # Expected layout: rc["judged"] with the same keys as the scored result's "judged" block.
    r = rc["judged"]
    gap = max([abs(r[k] - j[k]) for k in ("mean", "t_week", "trim_mean")]
              + [abs(r["by_year"][y] - v) for y, v in j["by_year"].items()])
    if gap > 1e-9 or r["n"] != j["n"] or r["marks"] != j["marks"] or r["pass"] != j["pass"]:
        raise ValueError("recompute no longer agrees with the scored result; rewrite this section by hand")
    return "\n".join([
        f"- MEASURED. A second helper rebuilt the judged numbers with its own code, written from the plan text without reading the scorer. "
        f"Its numbers were fixed on disk at {RECOMPUTE_FIXED}, before it opened the scored result (SHA-256 `{RECOMPUTE_SHA}`).",
        f"- MEASURED. All five marks agree, and the verdict agrees: did not pass. Mean, t, trimmed mean and all {len(j['by_year'])} yearly means agree to within {gap:.0e}.",
    ])


def plan():
    return yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["replay_65_plan"]["value"]


def sr(x):
    return f"{x:.2f}".replace("-0.00", "0.00")


def month_name(key):
    y, m = key.split("-")
    return ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][int(m) - 1] + " " + y


def bp(x, d=2):
    return f"{x * 1e4:+,.{d}f} bp"


def pct(x, d=2):
    return f"{x * 100:.{d}f}%"


def table(head, rows):
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in (head, ("---",) * len(head), *rows))


def power_line(pw):
    cells = {(r["kind"], r["sharpe"]): r["pass_all"] for r in pw["table"]}
    skew = [k for k in ("skew_iid", "skew_burst")]
    rng = lambda s: sorted(cells[(k, s)] for k in skew)
    lo9, hi9 = rng(0.9)
    lo6, hi6 = rng(0.6)
    return (lo9, hi9, lo6, hi6, pw["skew_target"], pw["seeds"])


def render(data, cfg, pw, freeze, inputs):
    j, plain, gross, cov, sh = data["judged"], data["judged_plain"], data["gross_plain"], data["coverage"], data["shown_only"]
    mk = cfg["marks"]
    years = [str(y) for y in mk["years"]]
    pos = sum(j["by_year"].get(y, 0) > 0 for y in years)
    drop = ceil(j["n"] * mk["trim_share"])
    marks = {
        "sessions": ("Judged sessions", f"At least {mk['min_sessions']:,}", f"{j['n']:,}", j["n"] >= mk["min_sessions"]),
        "money": ("Money", "Mean net return a session above zero", bp(j["mean"]), j["mean"] > 0),
        "evidence": ("Evidence", f"t at least {mk['t_min']:g}, clustered by calendar week of the exit session", f"{j['t_week']:.2f}",
                     j["t_week"] is not None and j["t_week"] >= mk["t_min"]),
        "trim": ("Trim", f"Mean above zero after dropping the best {mk['trim_share']:.0%} of sessions, rounded up",
                 f"{bp(j['trim_mean'])}; dropped {j['trim_dropped']}", j["trim_mean"] > 0),
        "years": ("Year breadth", f"At least {mk['years_positive_min']} of the {len(years)} years {years[0]} to {years[-1]} with a positive mean",
                  f"{j['years_positive']} of {len(years)}", j["years_positive"] >= mk["years_positive_min"]),
    }
    met = sum(v[-1] for v in marks.values())
    if (set(j["marks"]) != set(marks) or any(j["marks"][k] != v[-1] for k, v in marks.items()) or met != j["marks_met"]
            or j["pass"] is not all(j["marks"].values()) or j["pass"] or pos != j["years_positive"] or drop != j["trim_dropped"]
            or plain["mean"] != j["mean"] or plain["n"] != j["n"] or cov["judged_sessions"] != j["n"]
            or set(j["by_year"]) != set(years) or data["approval_commit"] is None or data["inputs_sha256"] != inputs or freeze != FREEZE):
        raise ValueError("Replay 65 saved aggregates and frozen marks do not reconcile")
    nosm, post, cash = sh["without_stress_months"], sh["post_paper"], sh["sh_cash_account"]
    # The fixed reading and the plain sentences below must stay true of the numbers they describe.
    if not (j["mean"] > 0 and 1 <= j["t_week"] < mk["t_min"] and round(plain["sharpe_yearly"], 2) == 0.35
            and nosm["mean"] <= 0 and abs(post["mean"]) < 0.5e-4 and abs(post["t_week"]) < 0.5 and cash["mean"] < 0):
        raise ValueError("Replay 65 plain reading no longer fits the saved aggregates; rewrite What it means by hand")
    lo9, hi9, lo6, hi6, skew, seeds = power_line(pw)
    stress = " and ".join(map(month_name, cfg["stress_exclude_months"]))
    PAPER_GROSS_SHARPE, PAPER_NET_SHARPE = paper_claims()
    b = cfg["borrow_annual"]
    cut = "Cannot count toward a mark."
    shown = [
        ("tlt_for_ief", "TLT in place of IEF, same weights, TLT returns, prices and borrow"),
        ("threshold_half", "Threshold half only, its own costs"),
        ("calendar_half", "Calendar half only, its own costs"),
        ("post_paper", f"From {cfg['post_paper_from']} on, outside the paper's printed sample"),
        ("without_stress_months", f"Without {stress}"),
        ("calendar_reversal_window_start", "Other reading of the Calendar first-day signal (start of the previous month's last-five window)"),
        ("lag_one_clock", "Lag-one clock: day t-1's full-close signal, held from close t to close t+1"),
        ("full_daily_round_trip", "Full daily round trip: entry and exit cost on every judged session"),
    ]
    if set(sh) != {k for k, _ in shown} | {"sh_cash_account"}:
        raise ValueError("Replay 65 shown-only lines differ from the nine the plan names")
    line = lambda r: f"{bp(r['mean'])} a session over {r['n']:,} sessions, yearly Sharpe {sr(r['sharpe_yearly'])}" + (f", t {r['t_week']:.2f}" if "t_week" in r else "")
    return "\n\n".join([
        "# Replay 65. Stock-bond rebalancing",
        "## The rule",
        "\n".join([
            f"- STATED, from the [frozen plan]({PLAN_PATH}). The source is Harvey, Mazzoleni and Melone, [NBER working paper w33554]({PAPER}). "
            f"The paper claims that portfolios rebalancing back to {cfg['target']:.0%} stocks push prices around, and that a rule trading against that flow had a "
            f"yearly Sharpe of {PAPER_GROSS_SHARPE} before costs and stayed {PAPER_NET_SHARPE} after costs, on stock and 10-year note futures.",
            f"- STATED. What we traded: long or short SPY against IEF, one weight a day. The weight is set at the close from a signal read on the 15-minute bar "
            f"that starts {cfg['signal_bar_start_before_close_min']} minutes before the close, and held to the next close. It averages a Threshold signal "
            f"(26 bands from {pct(cfg['delta_min'], 1)} to {pct(cfg['delta_max'], 1)}, scaled by {pct(cfg['threshold_scale'], 1)}) and a Calendar signal "
            f"active in the last {cfg['week4_sessions']} sessions of each month and its first session. Nothing was fitted on our data.",
            f"- STATED. Costs: on each change in weight, per leg, the greater of {cfg['cost_bps']} bp or ${cfg['cost_cent']:.2f} a share. "
            f"Borrow on the short leg: SPY {pct(b['SPY'])} a year, IEF {pct(b['IEF'])} a year. Scored {cfg['first_session']} to {cfg['last_session']}, "
            f"judged after a burn-in of {cfg['burn_in_sessions']} sessions.",
            f"- MEASURED. The average size of the weight was {pct(data['mean_abs_weight'], 1)} of capital.",
        ]),
        "## Did it pass?",
        f"MEASURED. Did not pass, **{met} of {len(marks)} frozen marks**, in the one scored run, started {RUN_WINDOW[0]}. "
        f"The mean net return was {bp(j['mean'])} a session over {j['n']:,} sessions, with a week-clustered t of {j['t_week']:.2f} against a bar of {mk['t_min']:g}. "
        f"After dropping the best {j['trim_dropped']} sessions the mean was {bp(j['trim_mean'])}. "
        f"The net yearly Sharpe was {plain['sharpe_yearly']:.2f}. Sessions, money and year breadth were met; evidence and trim were not.",
        "## Frozen marks",
        f"MEASURED. All five were required. Returns are net of costs and borrow, per unit of capital, in basis points a session. "
        f"Before costs and borrow the mean was {bp(gross['mean'])} (yearly Sharpe {gross['sharpe_yearly']:.2f}).",
        table(("Mark", "Frozen bar", "Measured", "Verdict"),
              [(label, bar, value, "met" if ok else "not met") for label, bar, value, ok in marks.values()]),
        "## By year",
        f"MEASURED. Mean net return a session by calendar year of the exit session. {years[-1]} runs to {cfg['last_session']}. Positive in {pos} of {len(years)}.",
        table(("Year", "Mean net a session"), [(y + (f" (to {cfg['last_session'][5:]})" if y == years[-1] else ""), bp(j["by_year"][y])) for y in years]),
        "## Shown only",
        "MEASURED. Each line below was named in the plan as shown only. None of them can count toward a mark.",
        "\n".join([f"- {label}: {line(sh[k])}. {cut}" for k, label in shown]
                  + [f"- Cash account with SH (whole shares of IEF and SH, up to ${cfg['sh_leg_usd']:,} each, only on sessions with a negative weight): "
                     f"{bp(cash['mean'])} a session over {cash['n']:,} sessions, held on {cash['sessions_held']:,}, yearly Sharpe {sr(cash['sharpe_yearly'])}. {cut}"]),
        "## Gaps",
        "\n".join([
            "- STATED before any return. Most of the window is inside the paper's own sample, which runs 1997-09-10 to 2023-03-17, and the authors say they extended it through 2025 and found the results stronger. So only about 2026 has not been looked at by anyone, and only the months from April 2023 on lie outside the printed sample.",
            "- STATED before any return. IEF stands in for the 10-year note future the paper uses. The future settles at 3:00 PM New York time and the ETFs close at 4:00 PM; IEF's duration differs.",
            "- STATED before any return. The costs and borrow rates are ours. The paper gives no per-trade cost.",
            "- UNKNOWN. Closing-auction fills, order cutoffs and the fill price. No realized spread is claimed.",
            f"- MEASURED. Coverage: {cov['judged_sessions']:,} of {cov['judged_candidates']:,} candidate sessions judged; {sum(cov['missing_daily'].values())} missing daily bars and {cov['sessions_without_signal_bar']} sessions without a signal bar.",
            f"- MEASURED on synthetic series before the run ([POWER_65.json](../../research_rig/POWER_65.json), {seeds:,} seeds a cell). Under the paper's skew of {skew}, the chance to pass all five marks was {pct(lo9, 1)} to {pct(hi9, 1)} at a true net Sharpe of 0.9 and {pct(lo6, 1)} to {pct(hi6, 1)} at 0.6.",
        ]),
        "## What it means",
        "\n".join([
            f"- STATED before the run. For a positive mean with t at least 1 but below {mk['t_min']:g}, the fixed reading is **not shown, not refuted**. That is this result.",
            f"- MEASURED. The net yearly Sharpe was {plain['sharpe_yearly']:.2f}, against {PAPER_NET_SHARPE} stated in the paper.",
            f"- MEASURED. Without {stress} the mean was {bp(nosm['mean'])}, at or below zero. From {cfg['post_paper_from']} on, the only months outside the paper's sample, it was {bp(post['mean'])}, about zero.",
            f"- MEASURED. The cash-account version a $500 account could hold lost money: {bp(cash['mean'])} a session.",
            "- STATED, ruling by the lead agent. No forward log is started, and the row closes.",
        ]),
        "## Independent recompute",
        recompute_lines(j, read_recompute()),
        "## Run record",
        "\n".join([
            f"- STATED by the lead agent. Scored exactly once, from {RUN_WINDOW[0]} to {RUN_WINDOW[1]}, exit 0. Ledger 208, queue 106.",
            f"- MEASURED. Freeze: `{freeze}`.",
            f"- MEASURED. Scoring approval: `{data['approval_commit']}`.",
            f"- MEASURED. Inputs digest: `{data['inputs_sha256']}`.",
            f"- MEASURED. Saved aggregate result SHA-256: `{RESULT_SHA}`.",
        ]),
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--output", type=Path, default=TARGET)
    args = parser.parse_args()
    m = re.fullmatch(r"Approved by the lead: plan 65 ledger 208, one scored run, freeze commit ([0-9a-f]{40}), inputs SHA-256 ([0-9a-f]{64})\.\n",
                     APPROVAL.read_text())
    if not m:
        raise ValueError("APPROVAL_65.md is not the one approval line")
    out = render(read_pinned(args.result, RESULT_SHA, "saved result"), plan(), read_pinned(POWER, POWER_SHA, "power file"), *m.groups())
    args.output.write_text(out, encoding="utf-8")


if __name__ == "__main__":
    main()
