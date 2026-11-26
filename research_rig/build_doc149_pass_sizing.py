"""Doc 149: honest $500 sizing of our two US-reachable passes, from repo files only.

Reads every figure from result pages, calibration JSON, practice cards, AGENTS.md
and config/thresholds.yaml already in the repo, then writes
docs/research/149_what_the_passes_are_worth.md. It opens no raw price file, opens
no off-repo result JSON and runs no scorer. Any figure not on the repo is written
as UNKNOWN.

Run: nice -n 10 python3 research_rig/build_doc149_pass_sizing.py
"""

from __future__ import annotations

import json
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "research" / "149_what_the_passes_are_worth.md"

ACCOUNT_USD = 500.0

SRC_R25 = "docs/research/69_replay_25_treasury_month_end.md"
SRC_M34 = "docs/research/82_measurement_34_tmf_ubt_month_end.md"
SRC_R48 = "docs/research/103_replay_48_muni_cef_january.md"
SRC_R53 = "docs/research/122_replay_53_taxable_fund_january_rebound.md"
SRC_136 = "docs/research/136_measured_stock_trading_costs.md"
SRC_140 = "docs/research/140_false_pass_audit.md"
SRC_CAL48 = "research_rig/CALIBRATION_48.json"
SRC_E01 = "practice/traders/E01_tlt_month_end_close.md"
SRC_E04 = "practice/traders/E04_muni_cef_january_watch.md"
SRC_E08 = "practice/traders/E08_taxable_cef_fifth_session_exit.md"
SRC_AGENTS = "AGENTS.md"
SRC_THRESH = "config/thresholds.yaml"


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def find(rel: str, pattern: str, group: int = 1, flags: int = 0) -> str:
    m = re.search(pattern, read_text(rel), flags)
    if not m:
        sys.exit(f"pattern not found in {rel}: {pattern}")
    return m.group(group)


def find_all(rel: str, pattern: str, flags: int = 0) -> list[tuple[str, ...]]:
    matches = re.findall(pattern, read_text(rel), flags)
    if not matches:
        sys.exit(f"no matches found in {rel}: {pattern}")
    return matches


def yaml_scalar(key: str) -> str:
    t = read_text(SRC_THRESH)
    m = re.search(r"^" + re.escape(key) + r":\n  value: ([^\n]+)", t, re.M)
    if not m:
        sys.exit(f"threshold not found: {key}")
    return m.group(1).strip()


def fmt_pct(val: float, decimals: int = 2, signed: bool = True) -> str:
    sign = "+" if signed and val > 0 else ""
    return f"{sign}{val:.{decimals}f}%"


def fmt_usd(val: float, signed: bool = True) -> str:
    if signed:
        if val < 0:
            return f"-${abs(val):.2f}"
        if val > 0:
            return f"+${val:.2f}"
        return "$0.00"
    return f"${val:.2f}"


def parse_replay_25() -> dict:
    mean_2bp = float(find(SRC_R25, r"\| Net mean above zero \| ([+-]\d+\.\d+)% \|"))
    t_2bp = float(find(SRC_R25, r"\| Net window t at least 2\.0 \| (\d+\.\d+) \|"))
    trim_2bp = float(find(SRC_R25, r"\| Net mean above zero after dropping the best three \| ([+-]\d+\.\d+)% \|"))
    post2020_2bp = float(find(SRC_R25, r"\| Net mean above zero from January 2020 \| ([+-]\d+\.\d+)% \|"))
    pos_years_2bp = find(SRC_R25, r"\| At least 60% of years have positive net means \| (\d+ of \d+)")

    m5 = re.search(
        r"^\| TLT last three, 5 bps per side \| \d+ \| ([+-]\d+\.\d+)% \| ([+-]?\d+\.\d+) \|",
        read_text(SRC_R25),
        re.M,
    )
    m10 = re.search(
        r"^\| TLT last three, 10 bps per side \| \d+ \| ([+-]\d+\.\d+)% \| ([+-]?\d+\.\d+) \|",
        read_text(SRC_R25),
        re.M,
    )
    if not m5 or not m10:
        sys.exit(f"5/10 bps rows not found in {SRC_R25}")

    cost_rows = {
        "2 bps (judged)": {
            "mean_pct": mean_2bp,
            "t": t_2bp,
            "trimmed_pct": trim_2bp,
            "post2020_pct": post2020_2bp,
            "pos_years": pos_years_2bp,
        },
        "5 bps": {"mean_pct": float(m5.group(1)), "t": float(m5.group(2))},
        "10 bps": {"mean_pct": float(m10.group(1)), "t": float(m10.group(2))},
    }

    # Yearly breakdown rows: | 2016 | 12 | +0.4424% | 1.64 | 36 | +0.1616% | 215 | -0.0211% | ...
    years = []
    for yr_s, win_s, net_s, wt_s, in_n, in_m, out_n, out_m in find_all(
        SRC_R25,
        r"^\| (\d{4}) \| (\d+) \| ([+-]\d+\.\d+)% \| ([+-]?\d+\.\d+) \| (\d+) \| ([+-]\d+\.\d+)% \| (\d+) \| ([+-]\d+\.\d+)% \|",
        re.M,
    ):
        yr = int(yr_s)
        wins = int(win_s)
        mean_pct = float(net_s)
        years.append(
            {
                "year": yr,
                "windows": wins,
                "mean_pct": mean_pct,
                "window_t": float(wt_s),
                "simple_year_pct": wins * mean_pct,
                "simple_year_usd": ACCOUNT_USD * (wins * mean_pct) / 100.0,
                "outside_daily_pct": float(out_m),
            }
        )

    n_windows = int(find(SRC_R25, r"(\d+) monthly windows"))
    inside_n = int(find(SRC_R25, r"across (\d+) inside intervals"))
    outside_n = int(find(SRC_R25, r"across ([0-9,]+) outside intervals").replace(",", ""))
    marks = find(SRC_R25, r"passed \*\*(\d+ of \d+ marks)\*\*")
    span = find(SRC_R25, r"(January 2016 through October 2026)")
    return {
        "n_windows": n_windows,
        "inside_intervals": inside_n,
        "outside_intervals": outside_n,
        "marks": marks,
        "span": span,
        "costs": cost_rows,
        "years": years,
    }


def parse_measurement_34() -> dict:
    t = read_text(SRC_M34)
    tlt_gross = float(find(SRC_M34, r"unlevered TLT gross mean was ([+-]\d+\.\d+)%"))
    tmf_ratio = float(find(SRC_M34, r"TMF gross tracking (\d+\.\d+)x"))
    tmf_band = find(SRC_M34, r"vs (2\.7x to 3\.1x)")
    tmf_marked_mean = float(find(SRC_M34, r"marked net mean ([+-]\d+\.\d+)%"))
    tmf_gross_mean = float(find(SRC_M34, r"^\| TMF \| ([+-]\d+\.\d+)% \|", 1, re.M))

    def parse_spreads(fund: str) -> dict:
        spreads = {}
        for side, n_s, mean_s, med_s, p95_s, max_s in re.findall(
            r"^\| " + re.escape(fund) + r" \| (Entry|Exit) \| (\d+) \| (\d+\.\d+) \| (\d+\.\d+) \| (\d+\.\d+) \| (\d+\.\d+) \|",
            t,
            re.M,
        ):
            spreads[side.lower()] = {
                "n": int(n_s),
                "mean_bp": float(mean_s),
                "median_bp": float(med_s),
                "p95_bp": float(p95_s),
                "max_bp": float(max_s),
            }
        if len(spreads) != 2:
            sys.exit(f"spreads not found for {fund} in {SRC_M34}")
        return spreads

    def parse_fund_section(fund: str) -> dict:
        header = f"### {fund}"
        start = t.index(header)
        end = t.find("\n### ", start + len(header))
        end2 = t.find("\n## ", start + len(header))
        stops = [p for p in (end, end2) if p != -1]
        block = t[start:] if not stops else t[start : min(stops)]

        m_marked = re.search(
            r"^\| Fixed 2 bp \+ half-spread \| ([+-]\d+\.\d+)% \| ([+-]?\d+\.\d+) \| ([+-]\d+\.\d+)% \| ([+-]\d+\.\d+)% \((\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\) \| (\d{4}) \(([+-]\d+\.\d+)%\) \| (\d{4}) \(([+-]\d+\.\d+)%\) \| (\d+ of \d+) \| (\d+\.\d+)x \| (\d+\.\d+)% \((\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\) \|",
            block,
            re.M,
        )
        if not m_marked:
            sys.exit(f"marked row not found in {SRC_M34} under {header}")

        m_2bp = re.search(
            r"^\| Fixed 2 bp \| ([+-]\d+\.\d+)% \| ([+-]?\d+\.\d+) \| ([+-]\d+\.\d+)% \| ([+-]\d+\.\d+)% \((\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\) \|",
            block,
            re.M,
        )
        if not m_2bp:
            sys.exit(f"2 bp row not found in {SRC_M34} under {header}")

        years = []
        # | 2016 | 12 | +1.23% / +15.24% | +1.19% / +14.72% | +1.15% / +14.17% | ...
        for yr_s, win_s, mean_s, comp_s in re.findall(
            r"^\| (\d{4}) \| (\d+) \| [^|]+ \| [^|]+ \| ([+-]\d+\.\d+)% / ([+-]\d+\.\d+)% \|",
            block,
            re.M,
        ):
            years.append(
                {
                    "year": int(yr_s),
                    "windows": int(win_s),
                    "mean_pct": float(mean_s),
                    "compounded_pct": float(comp_s),
                    "compounded_usd": ACCOUNT_USD * float(comp_s) / 100.0,
                }
            )
        if not years:
            sys.exit(f"annual rows not found in {SRC_M34} under {header}")

        return {
            "marked": {
                "mean_pct": float(m_marked.group(1)),
                "t": float(m_marked.group(2)),
                "trimmed_pct": float(m_marked.group(3)),
                "worst_window_pct": float(m_marked.group(4)),
                "worst_window_dates": f"{m_marked.group(5)} to {m_marked.group(6)}",
                "worst_comp_year": int(m_marked.group(7)),
                "worst_comp_year_pct": float(m_marked.group(8)),
                "worst_mean_year": int(m_marked.group(9)),
                "worst_mean_year_pct": float(m_marked.group(10)),
                "pos_years": m_marked.group(11),
                "net_ratio_vs_tlt": float(m_marked.group(12)),
                "max_dd_pct": float(m_marked.group(13)),
                "max_dd_dates": f"{m_marked.group(14)} to {m_marked.group(15)}",
            },
            "fixed_2bp": {
                "mean_pct": float(m_2bp.group(1)),
                "t": float(m_2bp.group(2)),
                "trimmed_pct": float(m_2bp.group(3)),
                "worst_window_pct": float(m_2bp.group(4)),
                "worst_window_dates": f"{m_2bp.group(5)} to {m_2bp.group(6)}",
            },
            "spreads": parse_spreads(fund),
            "years": years,
        }

    return {
        "tlt_gross_pct": tlt_gross,
        "tmf_gross_pct": tmf_gross_mean,
        "tmf_gross_ratio": tmf_ratio,
        "tmf_band": tmf_band,
        "tmf_marked_mean_pct": tmf_marked_mean,
        "tmf": parse_fund_section("TMF"),
        "ubt": parse_fund_section("UBT"),
    }


def parse_replay_48() -> dict:
    marks = find(SRC_R48, r"Passed, \*\*(\d+ of \d+) frozen marks\*\*")
    mean_pct = float(find(SRC_R48, r"averaged ([+-]\d+\.\d+)% net from the last December close"))
    mub_pct = float(find(SRC_R48, r"MUB averaged ([+-]\d+\.\d+)%"))
    roster_pct = float(find(SRC_R48, r"equal-weight roster of all eligible funds ([+-]\d+\.\d+)%"))
    pos_years = find(SRC_R48, r"above zero in (\d+ of \d+) years")
    ahead_mub = find(SRC_R48, r"ahead of MUB in (\d+ of \d+)")
    loser_cash = float(find(SRC_R48, r"\| Loser effect \| [^|]+ \| ([+-]\d+\.\d+)% with cash, ([+-]\d+\.\d+)% price only \|", 1))
    loser_price = float(find(SRC_R48, r"\| Loser effect \| [^|]+ \| ([+-]\d+\.\d+)% with cash, ([+-]\d+\.\d+)% price only \|", 2))
    ex_best_pct = float(find(SRC_R48, r"\| Without best year \| [^|]+ \| ([+-]\d+\.\d+)% \|"))
    zero_cost_pct = float(find(SRC_R48, r"\| Shown only: zero cost \| ([+-]\d+\.\d+)% \|"))
    cost_drag_pp = float(find(SRC_R48, r"Costs took (\d+\.\d+) percentage points a year"))
    proxy_sides_n = int(find(SRC_R48, r"MEASURED\. (\d+) held entry or exit sides used the 50 bp proxy"))
    mean_usd = float(find(SRC_R48, r"mean net result was \+\$(\d+\.\d+) a year"))
    vs_mub_usd = float(find(SRC_R48, r"\$(\d+\.\d+) more than MUB"))
    vs_roster_usd = float(find(SRC_R48, r"\$(\d+\.\d+) more than the equal-weight roster"))
    worst_usd = float(find(SRC_R48, r"worst turn was -\$(\d+\.\d+)"))
    best_usd = float(find(SRC_R48, r"best \+\$(\d+\.\d+)"))
    undoc_cash = find(SRC_R48, r"(\d+ of \d+) held fund-turns")

    turns = []
    # | 2016 | +0.62% | +0.21% | +2.26% | 132 | 5 of 5 | 0 |
    for yr_s, port_s, mub_s, ros_s, elig_s, cash_s, prox_s in find_all(
        SRC_R48,
        r"^\| (\d{4}) \| ([+-]\d+\.\d+)% \| ([+-]\d+\.\d+)% \| ([+-]\d+\.\d+)% \| (\d+) \| (\d+ of \d+) \| (\d+) \|",
        re.M,
    ):
        turns.append(
            {
                "turn_year": int(yr_s),
                "exit_year": int(yr_s) + 1,
                "eligible": int(elig_s),
                "port_pct": float(port_s),
                "port_usd": ACCOUNT_USD * float(port_s) / 100.0,
                "mub_pct": float(mub_s),
                "roster_pct": float(ros_s),
                "proxy_sides": int(prox_s),
            }
        )

    cal = json.loads(read_text(SRC_CAL48))
    return {
        "marks": marks,
        "mean_pct": mean_pct,
        "mub_pct": mub_pct,
        "roster_pct": roster_pct,
        "pos_years": pos_years,
        "ahead_mub": ahead_mub,
        "loser_cash_pct": loser_cash,
        "loser_price_pct": loser_price,
        "ex_best_pct": ex_best_pct,
        "zero_cost_pct": zero_cost_pct,
        "cost_drag_pp": cost_drag_pp,
        "proxy_sides": f"{proxy_sides_n} of {len(turns) * 10} held sides",
        "mean_usd": mean_usd,
        "vs_mub_usd": vs_mub_usd,
        "vs_roster_usd": vs_roster_usd,
        "worst_usd": -worst_usd,
        "best_usd": best_usd,
        "undoc_cash": f"{undoc_cash} held fund-turns",
        "turns": turns,
        "cal_no_edge_pct": 100.0 * cal["pass_rate"]["zero_edge"],
        "cal_muni_rally_pct": 100.0 * cal["pass_rate"]["beta_only"],
    }


def parse_replay_53() -> dict:
    marks = find(SRC_R53, r"Did not pass, \*\*(\d+ of \d+) frozen marks\*\*")
    mean_pct = float(find(SRC_R53, r"\| Net mean \| [^|]+ \| ([+-]\d+\.\d+)% \|"))
    pos_years = find(SRC_R53, r"\| Positive turns \| [^|]+ \| (\d+ of \d+) \|")
    ahead_pcef = find(SRC_R53, r"\| Against PCEF, turns \| [^|]+ \| (\d+ of \d+) \|")
    mean_usd = float(find(SRC_R53, r"mean net result was \+\$(\d+\.\d+)"))
    worst_usd = float(find(SRC_R53, r"worst turn was -\$(\d+\.\d+)"))
    best_usd = float(find(SRC_R53, r"best was \+\$(\d+\.\d+)"))
    corr_48 = float(find(SRC_R53, r"Pearson correlation[^+]+([+-]\d+\.\d+) across 10 paired turns"))
    turns = []
    # | 2016 | BME, BGY, ETJ, EXD, INB | +4.71% | ...
    for yr_s, port_s in find_all(
        SRC_R53,
        r"^\| (\d{4}) \| [^|]+ \| ([+-]\d+\.\d+)% \|",
        re.M,
    ):
        turns.append((int(yr_s), float(port_s)))
    return {
        "marks": marks,
        "mean_pct": mean_pct,
        "pos_years": pos_years,
        "ahead_pcef": ahead_pcef,
        "mean_usd": mean_usd,
        "worst_usd": -worst_usd,
        "best_usd": best_usd,
        "worst_pct": min(p for _, p in turns),
        "best_pct": max(p for _, p in turns),
        "corr_48": corr_48,
    }


def parse_doc_136() -> dict:
    # | Bond ETF (TLT only) | 0.609 / $0.030 | 0.610 / $0.030 | 0.610 / $0.030 | 0.610 / $0.030 | UNKNOWN |
    m = re.search(
        r"^\| Bond ETF \(TLT only\) \| (\d+\.\d+) / \$(\d+\.\d+) \| (\d+\.\d+) / \$(\d+\.\d+) \| (\d+\.\d+) / \$(\d+\.\d+) \| (\d+\.\d+) / \$(\d+\.\d+) \| (UNKNOWN) \|",
        read_text(SRC_136),
        re.M,
    )
    if not m:
        sys.exit(f"TLT row not found in {SRC_136}")
    return {
        "tlt_first30_bp": float(m.group(1)),
        "tlt_midday_bp": float(m.group(3)),
        "tlt_last30_med_bp": float(m.group(5)),
        "tlt_last30_usd_500": float(m.group(6)),
        "tlt_reg_med_bp": float(m.group(7)),
        "tlt_reg_usd_500": float(m.group(8)),
        "tlt_exact_close": m.group(9),
    }


def parse_doc_140() -> dict:
    m_luck = re.search(
        r"Expected luck passes in the (\d+) trading tests that could give a counted pass: low (\d+\.\d+), high (\d+\.\d+)\.",
        read_text(SRC_140),
    )
    if not m_luck:
        sys.exit(f"34-test luck line not found in {SRC_140}")
    n_tests = int(m_luck.group(1))
    luck_low = float(m_luck.group(2))
    luck_high = float(m_luck.group(3))
    p_ge3_low = float(find(SRC_140, r"Chance of 3 or more passes by luck alone in those 34: (\d+\.\d+)% on the low figures, (\d+\.\d+)% on the high figures", 1))
    p_ge3_high = float(find(SRC_140, r"Chance of 3 or more passes by luck alone in those 34: (\d+\.\d+)% on the low figures, (\d+\.\d+)% on the high figures", 2))
    r25_low = find(SRC_140, r"\| Replay 25 \| [^|]+ \| [^|]+ \| NOMINAL \| (\d+\.\d+%) \| (\d+\.\d+%) \|", 1)
    r25_high = find(SRC_140, r"\| Replay 25 \| [^|]+ \| [^|]+ \| NOMINAL \| (\d+\.\d+%) \| (\d+\.\d+%) \|", 2)
    r48_low = find(SRC_140, r"\| Replay 48 \| [^|]+ \| [^|]+ \| MEASURED \| (\d+\.\d+%) \| (\d+\.\d+%) \|", 1)
    r48_high = find(SRC_140, r"\| Replay 48 \| [^|]+ \| [^|]+ \| MEASURED \| (\d+\.\d+%) \| (\d+\.\d+%) \|", 2)
    return {
        "n_tests": n_tests,
        "luck_low": luck_low,
        "luck_high": luck_high,
        "p_ge3_low": p_ge3_low,
        "p_ge3_high": p_ge3_high,
        "r25_nom": f"{r25_low} to {r25_high} (NOMINAL)",
        "r48_meas": f"{r48_low} point, {r48_high} upper 95% (MEASURED)",
    }


def parse_practice_cards() -> dict:
    e01_first_win = find(SRC_E01, r"^\| (2026-12) \| [A-Za-z]+ 2026-12-\d{2} \|", 1, re.M)
    e01_first_entry = find(SRC_E01, r"^\| 2026-12 \| ([A-Za-z]+ 2026-12-\d{2}) \| ([A-Za-z]+ 2026-12-\d{2}) \|", 1, re.M)
    e01_first_exit = find(SRC_E01, r"^\| 2026-12 \| ([A-Za-z]+ 2026-12-\d{2}) \| ([A-Za-z]+ 2026-12-\d{2}) \|", 2, re.M)
    e01_twelfth_exit = find(SRC_E01, r"^\| 2027-11 \| [A-Za-z]+ 2027-11-\d{2} \| ([A-Za-z]+ 2027-11-\d{2}) \|", 1, re.M)
    e01_last_exit = find(SRC_E01, r"^\| 2027-12 \| [A-Za-z]+ 2027-12-\d{2} \| ([A-Za-z]+ 2027-12-\d{2}) \|", 1, re.M)
    e01_min_months = int(find(SRC_E01, r"Not before (\d+) months"))

    e04_freeze = find(SRC_E04, r"ready before (December 10, 2026)")
    e04_form = find(SRC_E04, r"Formation \| (Wed \d{4}-\d{2}-\d{2})")
    e04_entry = find(SRC_E04, r"Pretend entry \| (Thu \d{4}-\d{2}-\d{2})")
    e04_exit5 = find(SRC_E04, r"Shown-only exit \| (Fri \d{4}-\d{2}-\d{2})")
    e04_exit = find(SRC_E04, r"Judged exit \| (Fri \d{4}-\d{2}-\d{2})")

    e08_p50_pcef = int(find(SRC_E08, r"Portfolio above PCEF, at the shown spread: (\d+) forward years for 50% power"))
    e08_p80_pcef = int(find(SRC_E08, r"Portfolio above PCEF, at the shown spread: \d+ forward years for 50% power, (\d+) for 80%"))
    e08_p50_half = int(find(SRC_E08, r"(\d+) and (\d+) years above PCEF", 1))
    e08_p80_half = int(find(SRC_E08, r"(\d+) and (\d+) years above PCEF", 2))
    e08_entry = find(SRC_E08, r"Pretend entry \| (Thu \d{4}-\d{2}-\d{2})")
    e08_exit5 = find(SRC_E08, r"Claim exit: fifth January session \| (Fri \d{4}-\d{2}-\d{2})")
    e08_exit_m = find(SRC_E08, r"Reference exit: last January session \| (Fri \d{4}-\d{2}-\d{2})")

    return {
        "e01": {
            "first_window": e01_first_win,
            "first_entry": e01_first_entry,
            "first_exit": e01_first_exit,
            "twelfth_exit": e01_twelfth_exit,
            "last_exit": e01_last_exit,
            "min_months": e01_min_months,
        },
        "e04": {
            "freeze": e04_freeze,
            "formation": e04_form,
            "entry": e04_entry,
            "exit5": e04_exit5,
            "exit": e04_exit,
        },
        "e08": {
            "entry": e08_entry,
            "exit5": e08_exit5,
            "exit_month": e08_exit_m,
            "p50_pcef": e08_p50_pcef,
            "p80_pcef": e08_p80_pcef,
            "p50_half": e08_p50_half,
            "p80_half": e08_p80_half,
        },
        "thresholds": {
            "paper_min_trading_days": yaml_scalar("paper_min_trading_days"),
            "paper_min_closed_trades": yaml_scalar("paper_min_closed_trades"),
            "live_tracks_paper_months": yaml_scalar("live_tracks_paper_months"),
            "scale_live_evidence_months": yaml_scalar("scale_live_evidence_months"),
            "live_starting_capital_usd": yaml_scalar("live_starting_capital_usd"),
        },
    }


def build_doc() -> str:
    r25 = parse_replay_25()
    m34 = parse_measurement_34()
    r48 = parse_replay_48()
    r53 = parse_replay_53()
    d136 = parse_doc_136()
    d140 = parse_doc_140()
    pc = parse_practice_cards()

    # Derived figures from repo-printed tables only
    r25_2bp = r25["costs"]["2 bps (judged)"]
    r25_5bp = r25["costs"]["5 bps"]
    r25_10bp = r25["costs"]["10 bps"]

    r25_full_years = [y for y in r25["years"] if y["windows"] == 12]
    r25_2026 = [y for y in r25["years"] if y["year"] == 2026][0]
    r25_full_min = min(r25_full_years, key=lambda y: y["simple_year_pct"])
    r25_full_max = max(r25_full_years, key=lambda y: y["simple_year_pct"])
    r25_all_min = min(r25["years"], key=lambda y: y["simple_year_pct"])
    r25_all_max = max(r25["years"], key=lambda y: y["simple_year_pct"])
    r25_12win_pct = 12.0 * r25_2bp["mean_pct"]
    r25_12win_usd = ACCOUNT_USD * r25_12win_pct / 100.0
    r25_full_avg_pct = statistics.mean(y["simple_year_pct"] for y in r25_full_years)
    r25_full_avg_usd = ACCOUNT_USD * r25_full_avg_pct / 100.0

    # Replay 25 invested / idle share from doc 69's printed interval counts
    r25_total_intervals = r25["inside_intervals"] + r25["outside_intervals"]
    r25_invested_pct = 100.0 * r25["inside_intervals"] / r25_total_intervals
    r25_idle_pct = 100.0 * r25["outside_intervals"] / r25_total_intervals

    # Replay 48 spread of outcomes from the 10 printed turns
    r48_vals = [t["port_pct"] for t in r48["turns"]]
    r48_sd = statistics.stdev(r48_vals)
    r48_med = statistics.median(r48_vals)
    r48_worst = min(r48["turns"], key=lambda t: t["port_pct"])
    r48_best = max(r48["turns"], key=lambda t: t["port_pct"])
    r48_second_worst = sorted(r48["turns"], key=lambda t: t["port_pct"])[1]
    r48_elig_max = max(r48["turns"], key=lambda t: t["eligible"])
    r48_elig_last = r48["turns"][-1]

    # TMF & UBT derived figures from doc 82's printed tables
    tmf = m34["tmf"]
    ubt = m34["ubt"]
    tmf_full_years = [y for y in tmf["years"] if y["windows"] == 12]
    tmf_2026 = [y for y in tmf["years"] if y["year"] == 2026][0]
    tmf_full_min = min(tmf_full_years, key=lambda y: y["compounded_pct"])
    tmf_full_max = max(tmf_full_years, key=lambda y: y["compounded_pct"])
    tmf_full_avg_pct = statistics.mean(y["compounded_pct"] for y in tmf_full_years)
    tmf_full_avg_usd = ACCOUNT_USD * tmf_full_avg_pct / 100.0
    tmf_all_avg_pct = statistics.mean(y["compounded_pct"] for y in tmf["years"])
    tmf_all_avg_usd = ACCOUNT_USD * tmf_all_avg_pct / 100.0
    tmf_12win_simple_pct = 12.0 * tmf["marked"]["mean_pct"]
    tmf_12win_simple_usd = ACCOUNT_USD * tmf_12win_simple_pct / 100.0
    tmf_rt_spread_bp = tmf["spreads"]["entry"]["mean_bp"] + tmf["spreads"]["exit"]["mean_bp"]
    tmf_total_drag_bp = (m34["tmf_gross_pct"] - tmf["marked"]["mean_pct"]) * 100.0
    tlt_drag_bp = (m34["tlt_gross_pct"] - r25_2bp["mean_pct"]) * 100.0
    tmf_extra_drag_bp = tmf_total_drag_bp - tlt_drag_bp
    tmf_extra_drag_usd = ACCOUNT_USD * tmf_extra_drag_bp / 10000.0
    tmf_worst_usd = ACCOUNT_USD * tmf["marked"]["worst_window_pct"] / 100.0
    tmf_dd_usd = ACCOUNT_USD * tmf["marked"]["max_dd_pct"] / 100.0
    ubt_rt_spread_bp = ubt["spreads"]["entry"]["mean_bp"] + ubt["spreads"]["exit"]["mean_bp"]
    ubt_worst_usd = ACCOUNT_USD * ubt["marked"]["worst_window_pct"] / 100.0

    # Side-by-side table rows for 2016..2025 (matching exit calendar year vs turn year)
    r25_by_year = {y["year"]: y for y in r25["years"]}
    tmf_by_year = {y["year"]: y for y in tmf["years"]}
    r48_by_turn = {t["turn_year"]: t for t in r48["turns"]}
    r48_by_exit = {t["exit_year"]: t for t in r48["turns"]}

    side_rows = []
    for yr in range(2016, 2027):
        y25 = r25_by_year[yr]
        ytmf = tmf_by_year[yr]
        t48_exit = r48_by_exit.get(yr)
        r48_cell = (
            f"{fmt_pct(t48_exit['port_pct'])} ({fmt_usd(t48_exit['port_usd'])}, turn {t48_exit['turn_year']})"
            if t48_exit
            else "none (first turn entered Dec 2016)"
        )
        side_rows.append(
            f"| {yr} | {y25['windows']} | {fmt_pct(y25['simple_year_pct'])} ({fmt_usd(y25['simple_year_usd'])}) | "
            f"{fmt_pct(ytmf['compounded_pct'])} ({fmt_usd(ytmf['compounded_usd'])}) | {r48_cell} | UNKNOWN |"
        )

    lines = [
        "# 149: What the two US-reachable passes are worth on $500",
        "",
        "Written 2026-11-26 by `research_rig/build_doc149_pass_sizing.py` from repo result pages, calibration files, practice cards, `AGENTS.md` and `config/thresholds.yaml` only. No raw price file was opened, no off-repo result file was read and no scorer was run. Every figure below is historical as measured on past dates or stated in a repo rule; nothing here is a forecast or advice to trade.",
        "",
        "## Headline",
        "",
        f"- MEASURED, Replay 25 (TLT month-end, 1x, `docs/research/69_replay_25_treasury_month_end.md`): on $500 before taxes, the judged 2 bps/side mean of {fmt_pct(r25_2bp['mean_pct'], 4)} across {r25['n_windows']} windows equals {fmt_pct(r25_12win_pct)} ({fmt_usd(r25_12win_usd)}) per 12-window year. Across the 10 full years (2016 to 2025) the simple annual sum ranged from {fmt_pct(r25_full_min['simple_year_pct'])} ({fmt_usd(r25_full_min['simple_year_usd'])}, {r25_full_min['year']}) to {fmt_pct(r25_full_max['simple_year_pct'])} ({fmt_usd(r25_full_max['simple_year_usd'])}, {r25_full_max['year']}), and partial 2026 ({r25_2026['windows']} windows) was {fmt_pct(r25_2026['simple_year_pct'])} ({fmt_usd(r25_2026['simple_year_usd'])}).",
        f"- MEASURED, Measurement 34 (TMF 3x on the same month-end windows, `docs/research/82_measurement_34_tmf_ubt_month_end.md`): failed its frozen gross tracking mark ({m34['tmf_gross_ratio']:.4f}x vs {m34['tmf_band']}). At marked cost (fixed 2 bp + closing half-spread), the net mean was {fmt_pct(tmf['marked']['mean_pct'], 4)} per window ({fmt_pct(tmf_12win_simple_pct)} or {fmt_usd(tmf_12win_simple_usd)} per 12-window year simple), with compounded full-year returns from {fmt_pct(tmf_full_min['compounded_pct'])} ({fmt_usd(tmf_full_min['compounded_usd'])}, {tmf_full_min['year']}) to {fmt_pct(tmf_full_max['compounded_pct'])} ({fmt_usd(tmf_full_max['compounded_usd'])}, {tmf_full_max['year']}), partial 2026 at {fmt_pct(tmf_2026['compounded_pct'])} ({fmt_usd(tmf_2026['compounded_usd'])}), worst window {fmt_pct(tmf['marked']['worst_window_pct'])} ({fmt_usd(tmf_worst_usd)}) and max drawdown {tmf['marked']['max_dd_pct']:.2f}% ({fmt_usd(-tmf_dd_usd)}).",
        f"- MEASURED, Replay 48 (worst 5 muni CEFs in January, 1x, `docs/research/103_replay_48_muni_cef_january.md`): on a $500 sleeve once a year, before taxes, the mean net return across 10 turns (2016 to 2025) was {fmt_pct(r48['mean_pct'])} ({fmt_usd(r48['mean_usd'])}/year), ranging from {fmt_pct(r48_worst['port_pct'])} ({fmt_usd(r48['worst_usd'])}, turn {r48_worst['turn_year']}) to {fmt_pct(r48_best['port_pct'])} ({fmt_usd(r48['best_usd'])}, turn {r48_best['turn_year']}).",
        "- MEASURED, idle cash and overlap: Replay 25 sits idle about 86% of trading sessions and Replay 48 sits idle about 92% of trading sessions. Both want the same $500 during the last 3 sessions of January. The exact combined annual return on one $500 account is UNKNOWN on the repo because neither Replay 25 nor Measurement 34 prints individual monthly window returns.",
        f"- STATED, forward proof before real money: neither pass has any completed forward practice records yet. Practice card E01 (`practice/traders/E01_tlt_month_end_close.md`) requires at least {pc['e01']['min_months']} forward months (earliest after {pc['e01']['twelfth_exit']}). Practice card E04 (`practice/traders/E04_muni_cef_january_watch.md`) sets no numeric turn count and says one turn proves nothing on its own (first forward exit {pc['e04']['exit']}).",
        "",
        "## 1. Per trade: mean net, spread of outcomes, worst case seen, trades per year",
        "",
        "Replay 25 (TLT, 1x, last 3 sessions of each month; source `docs/research/69_replay_25_treasury_month_end.md` and `docs/research/82_measurement_34_tmf_ubt_month_end.md`):",
        "",
        f"- MEASURED: passed {r25['marks']} over {r25['n_windows']} monthly windows ({r25['span']}).",
        f"- MEASURED: mean net per trade at the judged 2 bps/side cost was {fmt_pct(r25_2bp['mean_pct'], 4)} (t = {r25_2bp['t']:.2f}; trimmed without best 3 windows {fmt_pct(r25_2bp['trimmed_pct'], 4)}; post-2020 {fmt_pct(r25_2bp['post2020_pct'], 4)}; gross mean {fmt_pct(m34['tlt_gross_pct'], 4)}). On $500 that is {fmt_usd(ACCOUNT_USD * r25_2bp['mean_pct'] / 100.0)} per trade before taxes.",
        f"- MEASURED: at higher shown costs, the per-trade mean fell to {fmt_pct(r25_5bp['mean_pct'], 4)} (t = {r25_5bp['t']:.2f}) at 5 bps/side and {fmt_pct(r25_10bp['mean_pct'], 4)} (t = {r25_10bp['t']:.2f}) at 10 bps/side.",
        f"- MEASURED (`docs/research/136_measured_stock_trading_costs.md`): TLT regular-hours median half-spread was {d136['tlt_reg_med_bp']:.3f} bp (${d136['tlt_reg_usd_500']:.3f} per $500 side) and last-30-minute median half-spread was {d136['tlt_last30_med_bp']:.3f} bp (${d136['tlt_last30_usd_500']:.3f} per $500 side). Exact closing-auction fill cost for TLT is {d136['tlt_exact_close']} on doc 136.",
        f"- MEASURED: spread of annual per-window means across the 11 scored years ran from {fmt_pct(r25_2026['mean_pct'], 4)} (2026, {r25_2026['windows']} windows) to {fmt_pct(r25_full_max['mean_pct'], 4)} ({r25_full_max['year']}, 12 windows), with {r25_2bp['pos_years']} positive.",
        "- UNKNOWN: single-window standard deviation, single-window median, interquartile range and single worst TLT window are not printed on `docs/research/69_replay_25_treasury_month_end.md`, and Replay 25's saved results file is kept off the repo.",
        "- STATED: 12 round-trip trades per full year (1 window per month, 3 held sessions per window).",
        "",
        "Replay 48 (worst 5 muni closed-end funds, 1x, last December close to last January close; source `docs/research/103_replay_48_muni_cef_january.md`):",
        "",
        f"- MEASURED: passed {r48['marks']} across 10 yearly turns (turns 2016 to 2025, exiting January 2017 to January 2026).",
        f"- MEASURED: mean net per trade (yearly turn) was {fmt_pct(r48['mean_pct'])} ({fmt_usd(r48['mean_usd'])} on $500 before taxes), versus {fmt_pct(r48['mub_pct'])} for MUB ({fmt_usd(r48['vs_mub_usd'])} ahead) and {fmt_pct(r48['roster_pct'])} for the equal-weight roster ({fmt_usd(r48['vs_roster_usd'])} ahead; loser effect {fmt_pct(r48['loser_cash_pct'])} with cash, {fmt_pct(r48['loser_price_pct'])} price only).",
        f"- MEASURED: spread of outcomes across the 10 printed yearly turns had sample standard deviation {r48_sd:.2f}%, median {fmt_pct(r48_med)}, positive in {r48['pos_years']} and ahead of MUB in {r48['ahead_mub']}. Without the best year (turn {r48_best['turn_year']}, {fmt_pct(r48_best['port_pct'])}), the mean fell to {fmt_pct(r48['ex_best_pct'])}.",
        f"- MEASURED: worst case seen was {fmt_pct(r48_worst['port_pct'])} ({fmt_usd(r48['worst_usd'])} on $500, turn {r48_worst['turn_year']}); second worst was {fmt_pct(r48_second_worst['port_pct'])} (turn {r48_second_worst['turn_year']}); best was {fmt_pct(r48_best['port_pct'])} ({fmt_usd(r48['best_usd'])}, turn {r48_best['turn_year']}).",
        f"- MEASURED: trading costs (closing half-spread + 5 bp/side, with a 50 bp proxy on {r48['proxy_sides']}) cut {r48['cost_drag_pp']:.2f} percentage points a year (zero-cost mean {fmt_pct(r48['zero_cost_pct'])} vs judged {fmt_pct(r48['mean_pct'])}). Closed-end funds were not sampled in `docs/research/136_measured_stock_trading_costs.md`, so live CEF fill cost outside Replay 48's quote sample is UNKNOWN.",
        "- STATED: 1 yearly turn per year (5 funds in $100 whole-share sleeves, 10 order sides per year).",
        f"- MEASURED, failed near copy (`docs/research/122_replay_53_taxable_fund_january_rebound.md`): Replay 53 (taxable CEFs on the same 10 turns, Pearson correlation {r53['corr_48']:+.3f} with Replay 48) did not pass ({r53['marks']}). Its mean was {fmt_pct(r53['mean_pct'])} ({fmt_usd(r53['mean_usd'])} on $500, worst {fmt_pct(r53['worst_pct'])} or {fmt_usd(r53['worst_usd'])}, best {fmt_pct(r53['best_pct'])} or {fmt_usd(r53['best_usd'])}), but it was positive in only {r53['pos_years']} and ahead of PCEF in only {r53['ahead_pcef']}.",
        "",
        "| Pass | Cost basis | Mean net per trade | Spread of outcomes | Worst case seen | Trades per year |",
        "|---|---|---|---|---|---|",
        f"| Replay 25 (TLT, 1x) | 2 bps/side (judged) | {fmt_pct(r25_2bp['mean_pct'], 4)} ({fmt_usd(ACCOUNT_USD * r25_2bp['mean_pct'] / 100.0)} on $500) | Single-window SD UNKNOWN; yearly means {fmt_pct(r25_2026['mean_pct'], 4)} to {fmt_pct(r25_full_max['mean_pct'], 4)} | UNKNOWN on repo | 12 |",
        f"| Replay 48 (Muni CEFs, 1x) | Half-spread + 5 bps/side (judged) | {fmt_pct(r48['mean_pct'])} ({fmt_usd(r48['mean_usd'])} on $500) | 10-turn SD {r48_sd:.2f}%, median {fmt_pct(r48_med)}, {r48['pos_years']} positive | {fmt_pct(r48_worst['port_pct'])} ({fmt_usd(r48['worst_usd'])}, turn {r48_worst['turn_year']}) | 1 |",
        f"| Replay 53 (Taxable CEFs, failed copy) | Half-spread + 5 bps/side (judged) | {fmt_pct(r53['mean_pct'])} ({fmt_usd(r53['mean_usd'])} on $500) | {r53['pos_years']} positive, {r53['ahead_pcef']} ahead of PCEF | {fmt_pct(r53['worst_pct'])} ({fmt_usd(r53['worst_usd'])}, turn 2021) | 1 |",
        "",
        "## 2. Per year on $500 at 1x (measured historical range, not a forecast)",
        "",
        "Replay 25 (TLT, 1x, $500 deployed fresh each month, before taxes, 0% on idle cash; source `docs/research/69_replay_25_treasury_month_end.md`):",
        "",
        f"- MEASURED: across all {r25['n_windows']} windows, 12 times the judged window mean is {fmt_pct(r25_12win_pct)} ({fmt_usd(r25_12win_usd)} per 12-window year). Across the 10 full years (2016 to 2025), the average of the simple 12-window annual sums was {fmt_pct(r25_full_avg_pct)} ({fmt_usd(r25_full_avg_usd)}/year).",
        f"- MEASURED: across the 10 full scored years (2016 to 2025), the simple 12-window annual sum ranged from {fmt_pct(r25_full_min['simple_year_pct'])} ({fmt_usd(r25_full_min['simple_year_usd'])}, {r25_full_min['year']}) to {fmt_pct(r25_full_max['simple_year_pct'])} ({fmt_usd(r25_full_max['simple_year_usd'])}, {r25_full_max['year']}).",
        f"- MEASURED: including partial 2026 ({r25_2026['windows']} windows, Jan to Oct), the lowest year row was {fmt_pct(r25_all_min['simple_year_pct'])} ({fmt_usd(r25_all_min['simple_year_usd'])}, {r25_all_min['year']}) and the highest was {fmt_pct(r25_all_max['simple_year_pct'])} ({fmt_usd(r25_all_max['simple_year_usd'])}, {r25_all_max['year']}).",
        "- UNKNOWN: exact compounded annual TLT returns and whole-share rounding drag on $500 are not printed on `docs/research/69_replay_25_treasury_month_end.md`.",
        "",
        "Replay 48 (worst 5 muni CEFs, 1x, $500 sleeve in $100 whole-share slots, before taxes; source `docs/research/103_replay_48_muni_cef_january.md`):",
        "",
        f"- MEASURED: mean net annual return was {fmt_pct(r48['mean_pct'])} ({fmt_usd(r48['mean_usd'])}/year on $500).",
        f"- MEASURED: across all 10 scored turns (2016 to 2025), annual returns ranged from {fmt_pct(r48_worst['port_pct'])} ({fmt_usd(r48['worst_usd'])}, turn {r48_worst['turn_year']}) to {fmt_pct(r48_best['port_pct'])} ({fmt_usd(r48['best_usd'])}, turn {r48_best['turn_year']}).",
        "",
        "| Pass (1x on $500) | Mean per year | Lowest full year | Highest full year | Worst scored year row (incl. 2026) | Basis |",
        "|---|---|---|---|---|---|",
        f"| Replay 25 (TLT, 1x) | {fmt_pct(r25_12win_pct)} ({fmt_usd(r25_12win_usd)}) | {fmt_pct(r25_full_min['simple_year_pct'])} ({fmt_usd(r25_full_min['simple_year_usd'])}, {r25_full_min['year']}) | {fmt_pct(r25_full_max['simple_year_pct'])} ({fmt_usd(r25_full_max['simple_year_usd'])}, {r25_full_max['year']}) | {fmt_pct(r25_all_min['simple_year_pct'])} ({fmt_usd(r25_all_min['simple_year_usd'])}, {r25_all_min['year']}, 10 win) | Simple sum of printed yearly window means; compounded UNKNOWN |",
        f"| Replay 48 (Muni CEFs, 1x) | {fmt_pct(r48['mean_pct'])} ({fmt_usd(r48['mean_usd'])}) | {fmt_pct(r48_worst['port_pct'])} ({fmt_usd(r48['worst_usd'])}, turn {r48_worst['turn_year']}) | {fmt_pct(r48_best['port_pct'])} ({fmt_usd(r48['best_usd'])}, turn {r48_best['turn_year']}) | {fmt_pct(r48_worst['port_pct'])} ({fmt_usd(r48['worst_usd'])}, turn {r48_worst['turn_year']}) | Direct $500 whole-share sleeve, before taxes |",
        "",
        "## 3. With reachable leverage measured (TMF and UBT on the month-end window)",
        "",
        "Measurement 34 (`docs/research/82_measurement_34_tmf_ubt_month_end.md`) ran on the exact same 130 windows as Replay 25. It measures vehicle tracking and quote cost on the same effect, not a second independent test.",
        "",
        "TMF (3x long Treasury ETF):",
        "",
        f"- MEASURED: TMF failed its frozen gross tracking mark ({m34['tmf_gross_ratio']:.4f}x vs {m34['tmf_band']}; gross mean {fmt_pct(m34['tmf_gross_pct'], 4)} vs TLT gross {fmt_pct(m34['tlt_gross_pct'], 4)}). It passed its positive-net-mean mark at fixed 2 bp + closing half-spread ({fmt_pct(tmf['marked']['mean_pct'], 4)}, t = {tmf['marked']['t']:.3f}, trimmed {fmt_pct(tmf['marked']['trimmed_pct'], 4)}).",
        f"- MEASURED extra cost: TMF's closing-minute SIP half-spread averaged {tmf['spreads']['entry']['mean_bp']:.3f} bp at entry (median {tmf['spreads']['entry']['median_bp']:.3f}, p95 {tmf['spreads']['entry']['p95_bp']:.3f}, max {tmf['spreads']['entry']['max_bp']:.3f}) and {tmf['spreads']['exit']['mean_bp']:.3f} bp at exit (median {tmf['spreads']['exit']['median_bp']:.3f}, p95 {tmf['spreads']['exit']['p95_bp']:.3f}, max {tmf['spreads']['exit']['max_bp']:.3f}), or {tmf_rt_spread_bp:.2f} bp round-trip in quote half-spread alone. Combined with 2 bp/side fixed cost, total drag was {tmf_total_drag_bp:.2f} bp/window versus {tlt_drag_bp:.2f} bp/window on TLT at 2 bp/side — an extra {tmf_extra_drag_bp:.2f} bp/window ({fmt_usd(tmf_extra_drag_usd, False)} per $500 round-trip).",
        f"- MEASURED on $500 per year (marked cost, before taxes): 12 times the window mean is {fmt_pct(tmf_12win_simple_pct)} ({fmt_usd(tmf_12win_simple_usd)}/year simple). Across the 10 full years (2016 to 2025), compounded annual returns averaged {fmt_pct(tmf_full_avg_pct)} ({fmt_usd(tmf_full_avg_usd)}) and ranged from {fmt_pct(tmf_full_min['compounded_pct'])} ({fmt_usd(tmf_full_min['compounded_usd'])}, {tmf_full_min['year']}) to {fmt_pct(tmf_full_max['compounded_pct'])} ({fmt_usd(tmf_full_max['compounded_usd'])}, {tmf_full_max['year']}). Across all 11 year rows including partial 2026 ({tmf_2026['windows']} windows, {fmt_pct(tmf_2026['compounded_pct'])} or {fmt_usd(tmf_2026['compounded_usd'])}), the mean compounded row was {fmt_pct(tmf_all_avg_pct)} ({fmt_usd(tmf_all_avg_usd)}). Positive mean years: {tmf['marked']['pos_years']}.",
        f"- MEASURED worst window and drawdown: TMF's worst single window at marked cost was {fmt_pct(tmf['marked']['worst_window_pct'])} ({fmt_usd(tmf_worst_usd)} on $500, {tmf['marked']['worst_window_dates']}; {fmt_pct(tmf['fixed_2bp']['worst_window_pct'])} at fixed 2 bp). Peak-to-trough max drawdown on daily closes was {tmf['marked']['max_dd_pct']:.2f}% ({fmt_usd(-tmf_dd_usd)} on $500, {tmf['marked']['max_dd_dates']}).",
        "",
        "UBT (2x long Treasury ETF, shown only, no pass/fail marks):",
        "",
        f"- MEASURED: UBT's closing-minute SIP half-spread averaged {ubt['spreads']['entry']['mean_bp']:.3f} bp at entry (p95 {ubt['spreads']['entry']['p95_bp']:.3f}, max {ubt['spreads']['entry']['max_bp']:.3f}) and {ubt['spreads']['exit']['mean_bp']:.3f} bp at exit (p95 {ubt['spreads']['exit']['p95_bp']:.3f}, max {ubt['spreads']['exit']['max_bp']:.3f}), or {ubt_rt_spread_bp:.2f} bp round-trip in quote half-spread alone.",
        f"- MEASURED: at fixed 2 bp + half-spread, UBT's net mean fell to {fmt_pct(ubt['marked']['mean_pct'], 4)} (t = {ubt['marked']['t']:.3f}, net ratio {ubt['marked']['net_ratio_vs_tlt']:.2f}x TLT, {ubt['marked']['pos_years']} positive), with worst window {fmt_pct(ubt['marked']['worst_window_pct'])} ({fmt_usd(ubt_worst_usd)}, {ubt['marked']['worst_window_dates']}), worst compounded year {fmt_pct(ubt['marked']['worst_comp_year_pct'])} ({ubt['marked']['worst_comp_year']}) and max drawdown {ubt['marked']['max_dd_pct']:.2f}%.",
        "",
        "Leverage for Replay 48 (muni CEFs):",
        "",
        "- UNKNOWN / not tested: no external leverage or margin test was run for Replay 48 (the desk cash account does not use margin, and the underlying muni CEFs already carry internal fund leverage).",
        "",
        "| Vehicle (month-end) | Marked net mean / trade | Round-trip half-spread (mean) | Worst single window | Worst compounded year | Max drawdown |",
        "|---|---|---|---|---|---|",
        f"| TLT (1x, Replay 25) | {fmt_pct(r25_2bp['mean_pct'], 4)} (2 bp/side) | {2.0 * d136['tlt_last30_med_bp']:.2f} bp (doc 136 last-30m med x2; close UNKNOWN) | UNKNOWN on repo | UNKNOWN on repo (2026 simple {fmt_pct(r25_2026['simple_year_pct'])}) | UNKNOWN on repo |",
        f"| TMF (3x, Meas. 34) | {fmt_pct(tmf['marked']['mean_pct'], 4)} (2 bp + spread) | {tmf_rt_spread_bp:.2f} bp (closing-min SIP) | {fmt_pct(tmf['marked']['worst_window_pct'])} ({fmt_usd(tmf_worst_usd)}) | {fmt_pct(tmf['marked']['worst_comp_year_pct'])} ({tmf['marked']['worst_comp_year']}) | {tmf['marked']['max_dd_pct']:.2f}% ({fmt_usd(-tmf_dd_usd)}) |",
        f"| UBT (2x, Meas. 34, shown) | {fmt_pct(ubt['marked']['mean_pct'], 4)} (2 bp + spread) | {ubt_rt_spread_bp:.2f} bp (closing-min SIP) | {fmt_pct(ubt['marked']['worst_window_pct'])} ({fmt_usd(ubt_worst_usd)}) | {fmt_pct(ubt['marked']['worst_comp_year_pct'])} ({ubt['marked']['worst_comp_year']}) | {ubt['marked']['max_dd_pct']:.2f}% |",
        "",
        "## 4. Idle time and both passes together by scored year",
        "",
        "How much of the year the money sits idle:",
        "",
        f"- MEASURED, Replay 25 (TLT or TMF): held 3 sessions per month (36 sessions in a full year). Across 2016 to 2026 in `docs/research/69_replay_25_treasury_month_end.md`, {r25['inside_intervals']} daily return intervals fell inside the window and {r25['outside_intervals']} fell outside — {r25_invested_pct:.1f}% invested and {r25_idle_pct:.1f}% idle.",
        "- STATED, Replay 48 (muni CEFs): held from the last December close to the last January close (about 20 to 21 trading sessions out of ~252 per year, roughly 8% invested and 92% idle).",
        "- STATED, overlap on one $500 account: Replay 48 holds across the last 3 sessions of January, which is also Replay 25's January month-end window. A single $500 cash account cannot put $500 into both during those 3 sessions without splitting capital or skipping January's Treasury window. Running Replay 48 in January and Replay 25 in the other 11 months (about 53 to 54 trading sessions per year) still leaves the cash idle about 79% of trading sessions.",
        "- UNKNOWN: any cash-sweep interest earned during idle sessions (both replays assume 0% on idle cash).",
        "",
        "What both passes together would have given in each scored year:",
        "",
        "- UNKNOWN on the repo: the exact combined per-year return on one $500 account cannot be computed from repo files without opening raw data. Neither `docs/research/69_replay_25_treasury_month_end.md` nor `docs/research/82_measurement_34_tmf_ubt_month_end.md` prints individual monthly returns (so the overlapping January Treasury window cannot be removed), and `docs/research/69_replay_25_treasury_month_end.md` does not print compounded annual TLT returns. Per the repo-only rule, no combined year total is computed below.",
        "- MEASURED, side-by-side per-year figures that are printed on the repo (aligned by exit calendar year: Replay 48 turn Y enters at the end of December Y and exits at the end of January Y+1):",
        "",
        "| Exit year | Month-end windows | Replay 25 TLT 1x simple sum (2 bp/side) | Meas. 34 TMF 3x compounded (marked) | Replay 48 Muni CEFs 1x (exiting Jan) | Combined on $500 |",
        "|---|---|---|---|---|---|",
        *side_rows,
        "",
        "## 5. Forward months needed before real money, and the dates",
        "",
        "Project rules (`AGENTS.md` and `config/thresholds.yaml`):",
        "",
        "- STATED (`AGENTS.md`): what survives past tests trades pretend money on the practice desk, and the practice desk is the judge. Real money moves in stages set by the owner: now pretend accounts only; next a first small test amount ($300 or $500, keys such as `live_starting_capital_usd` are marked `open` in `config/thresholds.yaml`); later stricter sizing once matured. `AGENTS.md` does not set a fixed numeric forward-month count before the owner's first $300 to $500 test money.",
        "- STATED (`config/thresholds.yaml`, builder thresholds for general practice-desk rules): see `paper_min_trading_days`, `paper_min_closed_trades`, `live_tracks_paper_months` and `scale_live_evidence_months` (per `config/thresholds.yaml`, documents name the keys rather than repeating their values).",
        "",
        "Each card's current count and dates (as of 2026-11-26):",
        "",
        f"- MEASURED, E01 (`practice/traders/E01_tlt_month_end_close.md`, Replay 25 forward log): 0 forward months completed (`docs/research/140_false_pass_audit.md` notes no E01 forward log exists yet). E01 states judgment is not before {pc['e01']['min_months']} forward months. First window is {pc['e01']['first_window']} (entry {pc['e01']['first_entry']}, exit {pc['e01']['first_exit']}); the 12th forward month finishes at the exit of 2027-11 ({pc['e01']['twelfth_exit']}), and the pinned 13-month schedule ends {pc['e01']['last_exit']}. Remaining forward months by E01's rule: {pc['e01']['min_months']}. (Applying `paper_min_closed_trades` literally at 12 trades/year would take over 8 years.)",
        f"- MEASURED, E04 (`practice/traders/E04_muni_cef_january_watch.md`, Replay 48 forward watch): 0 forward turns completed. Next turn dates: roster freeze {pc['e04']['freeze']}, formation {pc['e04']['formation']}, pretend entry {pc['e04']['entry']}, shown-only fifth-session exit {pc['e04']['exit5']}, judged exit {pc['e04']['exit']}. E04 states one turn proves nothing on its own and sets no numeric turn count before real money (remaining months before real money is UNKNOWN / owner decision; at 1 turn per year, even 3 to 5 forward turns would run to January 2029 to January 2031).",
        f"- MEASURED, E08 (`practice/traders/E08_taxable_cef_fifth_session_exit.md`, Replay 53 shown-only lead, not a pass): 0 forward turns completed. Next turn dates: pretend entry {pc['e08']['entry']}, claim exit {pc['e08']['exit5']}, reference exit {pc['e08']['exit_month']}. E08's own power math states beating PCEF at the shown spread needs {pc['e08']['p50_pcef']} forward years for 50% power and {pc['e08']['p80_pcef']} forward years for 80% power ({pc['e08']['p50_half']} and {pc['e08']['p80_half']} years if the true edge is half the shown mean), so E08 cannot clear the screen on its own.",
        "",
        "## 6. What could make each stop working",
        "",
        "Shared risks across both passes:",
        "",
        f"- MEASURED (`docs/research/140_false_pass_audit.md`): across {d140['n_tests']} trading tests that could give a counted pass, a no-edge world predicts {d140['luck_low']:.2f} to {d140['luck_high']:.2f} passes by luck alone, giving a {d140['p_ge3_low']:.2f}% to {d140['p_ge3_high']:.2f}% chance of seeing 3 or more passes by luck. One or both passes could be chance.",
        "- STATED (`docs/research/136_measured_stock_trading_costs.md`): exact closing-auction fills are UNKNOWN in our spread measurement. Live slippage or wider spreads can erase thin edges.",
        "- STATED: both rules rest on published academic calendar effects (Hartley and Schwarz for Treasury month-end; Starks, Yong and Zheng plus Carrion and Zhang for closed-end fund tax-loss selling). Crowding or broker/fund flow shifts can shrink them.",
        "- STATED: every return above is before taxes. Short-term gains and taxable distributions on a US taxable account cut realized dollars (exact tax drag is UNKNOWN here).",
        "",
        "Specific risks for Replay 25 (TLT / TMF month-end):",
        "",
        f"- MEASURED: it already lost money in partial 2026 ({r25_2026['windows']} windows): {fmt_pct(r25_2026['mean_pct'], 4)} per window in TLT ({fmt_pct(r25_2026['simple_year_pct'])} simple) and {fmt_pct(tmf_2026['compounded_pct'])} compounded in TMF at marked cost, with a {tmf['marked']['max_dd_pct']:.2f}% peak-to-trough TMF drawdown.",
        f"- MEASURED: cost sensitivity is tight. TLT's t-statistic drops to {r25_5bp['t']:.2f} (below 2.0) at 5 bps/side, and TMF's marked t-statistic ({tmf['marked']['t']:.3f}) already sits right on 2.0 while failing its {m34['tmf_band']} gross tracking mark ({m34['tmf_gross_ratio']:.4f}x).",
        f"- MEASURED (`docs/research/140_false_pass_audit.md`): Replay 25's nominal no-edge rate was {d140['r25_nom']}; 5 of 6 scored month-end and bond-flow tests in the same family failed; 2016 to 2018 overlapped Hartley and Schwarz's published sample; and the 2002 to 2015 check (Replay 26) was blocked before scoring.",
        "- STATED: changes in Treasury auction schedules, bond-index rebalancing, dealer balance-sheet capacity, or sustained high rate volatility (which increases daily-reset drag in TMF) could weaken or invert the window.",
        "",
        "Specific risks for Replay 48 (muni CEFs in January):",
        "",
        f"- MEASURED (`research_rig/CALIBRATION_48.json` and `docs/research/140_false_pass_audit.md`): only 10 yearly turns exist, the pass sits right on the {r48['pos_years']} positive-year bar (one more losing January would have failed), the no-edge pass rate was {d140['r48_meas']}, and a synthetic muni-wide rally with zero loser effect passed {r48['cal_muni_rally_pct']:.2f}% of the time.",
        f"- MEASURED (`docs/research/122_replay_53_taxable_fund_january_rebound.md`): the closest sibling test (Replay 53, taxable CEFs, correlation {r53['corr_48']:+.3f}) failed ({r53['marks']}, positive in only {r53['pos_years']}).",
        f"- MEASURED (`docs/research/103_replay_48_muni_cef_january.md`): thinly traded muni CEFs have real execution and data gaps — {r48['proxy_sides']} lacked full closing-quote cover (50 bp proxy), {r48['undoc_cash']} had undocumented cash, and the eligible muni CEF pool shrank over the decade (from {r48_elig_max['eligible']} eligible in turn {r48_elig_max['turn_year']} to {r48_elig_last['eligible']} in turn {r48_elig_last['turn_year']}).",
        f"- STATED: January municipal bond selloffs (like turns {r48_second_worst['turn_year']} at {fmt_pct(r48_second_worst['port_pct'])} and {r48_worst['turn_year']} at {fmt_pct(r48_worst['port_pct'])}), fund mergers, tender offers or shifts in retail tax-loss selling timing could wipe out multiple years of average gains in one month.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    content = build_doc()
    OUT.write_text(content, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(content.splitlines())} lines)")


if __name__ == "__main__":
    main()
