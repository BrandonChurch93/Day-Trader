"""Ledger 215. Optional count modes accept public filing or award metadata only."""

import csv
import json
import math
import re
import sys

import numpy as np


CUTOFF = "2026-11-26"
FIRST = "2016-01-01"
WORLDS = 30_000
SEED = 215111213
MIN_N = 300
MIN_YEARS = 7
YEARS = 11
COMPLETED_QUARTERS = 43
QUARTERS = 44
MIN_POWER = 0.33
ROSTER = {
    "AVAV": r"aerovironment\b", "KTOS": r"kratos\b", "CACI": r"caci\b",
    "LDOS": r"leidos\b", "SAIC": r"science applications international\b|saic\b",
    "BAH": r"booz allen\b", "CW": r"curtiss[- ]wright\b",
    "MRCY": r"mercury (systems|defense)\b",
    "BWXT": r"bwxt\b|bw(x|xt) technologies\b",
    "HII": r"huntington ingalls\b",
}


def count_links():
    rows = [r for r in csv.DictReader(sys.stdin)
            if r["side"] == "customer" and r["form"] == "10-K"
            and r["kind"] == "listed" and r["basis"] == "revenue"
            and float(r["share"]) >= .10 and FIRST <= r["filed"] <= CUTOFF]
    return {"rows": len(rows), "unique_pairs": len({(r["reporter"], r["counterparty_ticker"]) for r in rows}),
            "unique_customers": len({r["counterparty_ticker"] for r in rows}),
            "by_filed_year": {str(y): sum(r["filed"].startswith(str(y)) for r in rows)
                              for y in (2025, 2026)}}


def count_dod():
    rows = sorted(csv.DictReader(sys.stdin), key=lambda r: r["releaseDate"])
    seen, dates, all_dates = set(), set(), set()
    by_size = {25: set(), 100: set()}
    full_rows = 0
    for r in rows:
        d = r["releaseDate"]
        ids = r["contractNumbers"].split()
        new = set(ids) - seen
        seen.update(ids)
        if not FIRST <= d <= CUTOFF:
            continue
        full_rows += 1
        all_dates.add(d)
        parent = next((k for k, rx in ROSTER.items() if re.match(rx, r["contractor"].lower())), None)
        if parent is None:
            continue
        dates.add((parent, d))
        if len(ids) != 1 or not new:
            continue
        # A recent FY in the PIID plus a first archive sighting is only a new-award proxy.
        match = re.fullmatch(r"[A-Z0-9]{6}[-]?([0-9]{2})[-]?[A-Z][-]?[0-9A-Z]{4,7}", ids[0])
        if not match or int(d[:4]) - (2000 + int(match[1])) not in (-1, 0, 1):
            continue
        for size in by_size:
            if float(r["amount"] or 0) >= size * 1_000_000:
                by_size[size].add((parent, d))
    return {"archive_rows": full_rows, "archive_dates": len(all_dates),
            "first_and_last_dates": [min(all_dates), max(all_dates)],
            "named_roster_parent_days": len(dates),
            "proxy_25m_parent_days_by_quarter": [
                sum(int(d[:4]) == y and (int(d[5:7]) - 1) // 3 == q for _, d in by_size[25])
                for y in range(2016, 2027) for q in range(4)
            ],
            "proxy_25m_parent_days_by_year": [sum(d.startswith(str(y)) for _, d in by_size[25])
                                              for y in range(2016, 2027)],
            "proxy_100m_parent_days_by_year": [sum(d.startswith(str(y)) for _, d in by_size[100])
                                               for y in range(2016, 2027)]}


def season_counts(n):
    return [n // QUARTERS + (i < n % QUARTERS) for i in range(QUARTERS)]


def screen(label, counts, sigma, rho, issuers, profiles, offset):
    n = sum(counts)
    active = np.flatnonzero(counts)
    starts = np.r_[0, np.cumsum(np.asarray(counts)[active])[:-1]]
    q = np.repeat(active, np.asarray(counts)[active])
    year = q // 4
    ys, y_count = np.unique(year, return_counts=True)
    y_starts = np.r_[0, np.cumsum(y_count)[:-1]]
    # Rotate synthetic issuer assignment by quarter; real identities are not simulated.
    g = np.concatenate([(np.arange(counts[t]) + 17 * t) % issuers for t in active])
    g_order = np.argsort(g, kind="stable")
    _, i_count = np.unique(g, return_counts=True)
    i_starts = np.r_[0, np.cumsum(i_count)[:-1]]
    _, qi_count = np.unique(q * issuers + g, return_counts=True)
    qi_starts = np.r_[0, np.cumsum(qi_count)[:-1]]
    qi_order = np.argsort(q * issuers + g, kind="stable")
    q_count = np.asarray(counts)[active]
    distinct_intersections = len(qi_starts) == n
    cq, ci, cqi = len(active), len(i_starts), len(qi_starts)
    issuer_rho = .03
    var_ratio = (n + rho * np.sum(q_count * (q_count - 1))
                 + issuer_rho * np.sum(i_count * (i_count - 1)))
    n_eff = n ** 2 / var_ratio
    trim = math.ceil(.01 * n)
    rng = np.random.default_rng(SEED + offset)
    tallies = np.zeros((len(profiles), 5), dtype=int)
    for _ in range(WORLDS // 300):
        noise = sigma * (math.sqrt(rho) * rng.standard_normal((300, QUARTERS))[:, q]
                         + math.sqrt(issuer_rho) * rng.standard_normal((300, issuers))[:, g]
                         + math.sqrt(1 - rho - issuer_rho) * rng.standard_normal((300, n)))
        for j, (_, gross, cost, common) in enumerate(profiles):
            x = (noise + gross + common) - (cost + common)
            avg = x.mean(axis=1)
            z = x - avg[:, None]
            ss_q = np.sum(np.add.reduceat(z, starts, axis=1) ** 2, axis=1)
            ss_i = np.sum(np.add.reduceat(z[:, g_order], i_starts, axis=1) ** 2, axis=1)
            ss_qi = (np.sum(z ** 2, axis=1) if distinct_intersections
                     else np.sum(np.add.reduceat(z[:, qi_order], qi_starts, axis=1) ** 2, axis=1))
            vq = ss_q * cq / (cq - 1) if cq > 1 else ss_qi
            vi = ss_i * ci / (ci - 1) if ci > 1 else ss_qi
            # Two-way cluster estimate, floored at the two one-way variances.
            se = np.sqrt(np.maximum(np.maximum(vq, vi), vq + vi - ss_qi * cqi / (cqi - 1))) / n
            trim_mean = np.partition(x, n - trim, axis=1)[:, :n - trim].mean(axis=1)
            positive_years = (np.add.reduceat(x, y_starts, axis=1) > 0).sum(axis=1)
            marks = (avg > 0, (cq > 1) & (avg >= 2 * se), trim_mean > 0, positive_years >= MIN_YEARS)
            joint = np.logical_and.reduce(marks) & (n >= MIN_N)
            tallies[j] += [np.count_nonzero(m) for m in (*marks, joint)]
    result = {}
    for (name, gross, cost, common), values in zip(profiles, tallies):
        net = gross - cost
        result[name] = {
            "gross_bp": gross, "friction_bp": cost, "net_bp": net, "common_rally_bp": common,
            "quick_signal_sq": round(float(n_eff * (max(net, 0) / sigma) ** 2), 5),
            **dict(zip(("mean_positive", "t_at_least_2", "trim_positive", "year_breadth", "all_marks"),
                       (int(v) / WORLDS for v in values)))}
    return {"case": label, "n": n, "dates_mark": n >= MIN_N, "covered_years": len(ys),
            "n_eff": round(float(n_eff), 5), "quarter_counts": list(counts), "trim_n": trim,
            "noise_bp": sigma, "quarter_rho": rho, "issuer_rho": issuer_rho, "results": result}


def scenarios(proxy_name, edge):
    return [("flat_after_cost_null", 0, 0, 0), ("zero_gross_after_cost", 0, 10, 0),
            ("shared_rally_after_cost", 0, 10, 50), (proxy_name, edge, 10, 0)]


def power():
    # Frozen metadata summaries from the separate count modes at the pinned inputs.
    customer_pairs = 281
    q_before_after_proxy = 45_319 / (140_022 - 9_947)
    good_news_fraction = .2
    link_projection = round(customer_pairs * COMPLETED_QUARTERS * q_before_after_proxy * good_news_fraction)
    award_quarters = [
        3, 5, 11, 5, 4, 1, 10, 3, 5, 7, 11, 3, 3, 8, 12, 3, 6, 6, 5, 2, 6, 8,
        9, 5, 7, 4, 6, 9, 3, 4, 12, 3, 4, 5, 8, 7, 3, 7, 5, 5, 3, 6, 8, 2,
    ]
    licensed_us_calls = 482

    cases = [
        screen("11_snapshot_extrapolation", season_counts(link_projection), 1405, .20, 281,
               scenarios("monthly_top_decile_proxy", 142), 11),
        screen("11_low_quarter_dependence", season_counts(link_projection), 1405, .05, 281,
               scenarios("monthly_top_decile_proxy", 142), 11),
        screen("12_licensed_US_full_calls_one_quarter", [0] * 39 + [licensed_us_calls] + [0] * 4,
               704, .20, licensed_us_calls, scenarios("32_session_whole_call_proxy", 66), 12),
        screen("12_same_count_spread_over_history", season_counts(licensed_us_calls), 704, .20, 200,
               scenarios("32_session_whole_call_proxy", 66), 12),
        screen("12_same_count_wider_noise", season_counts(licensed_us_calls), 1408, .20, 200,
               scenarios("32_session_whole_call_proxy", 66), 12),
        screen("13_US_contract_archive_roster_proxy", award_quarters, 320, .20, len(ROSTER),
               scenarios("market_cap_top_5_percent_proxy", 30), 13),
        screen("13_generous_vendor_count_proxy", season_counts(1006), 320, .20, 183,
               scenarios("market_cap_top_5_percent_proxy", 30), 13),
    ]
    return {"cutoff_boise": CUTOFF, "seed": SEED, "worlds": WORLDS,
            "min_n": MIN_N, "min_positive_years": MIN_YEARS, "min_power": MIN_POWER,
            "count_inputs": {
                "row_11_latest_filing_pairs": customer_pairs,
                "row_11_older_paper_order_proxy": round(q_before_after_proxy, 6),
                "row_11_good_news_share_assumption": good_news_fraction,
                "row_11_projected_events": link_projection,
                "row_12_licensed_full_US_calls": licensed_us_calls,
                "row_13_archive_rows": 36_557, "row_13_archive_days": 2668,
                "row_13_roster_parent_days": 1070,
                "row_13_roster_25m_proxy": sum(award_quarters),
                "row_13_roster_100m_proxy": 83},
            "cases": cases}


def main():
    if sys.argv[1:] == ["count-links"]:
        return count_links()
    if sys.argv[1:] == ["count-dod"]:
        return count_dod()
    if sys.argv[1:]:
        raise SystemExit("usage: power_rows_11_12_13.py [count-links|count-dod]")
    return power()


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
