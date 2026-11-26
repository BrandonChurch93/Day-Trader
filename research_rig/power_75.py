"""Offline Plan 75 count and synthetic power only; no prices, archive paths, or runtime."""

from datetime import date, timedelta
from math import sqrt
from pathlib import Path

import numpy as np
import yaml


def dates(first, stop):
    start, end = map(date.fromisoformat, (first, stop))
    return [start + timedelta(days=i) for i in range((end - start).days)]


def schedule(days, names, cfg, rng):
    """Toy periodic episodes, not a Donchian signal, with staggered coin/leg phases."""
    s = cfg["synthetic"]
    n, k = len(days), len(cfg["lookbacks"])
    paper_days = len(dates(*s["paper_dates"]))
    # The first simulated return after a next-open fill needs 91 completed closes.
    warm = cfg["vol_days"] + 1
    t = np.arange(n - warm)[:, None, None]
    gaps = np.asarray(paper_days / np.array(s["paper_counts"]))
    dwell = np.maximum(1, np.rint(gaps * s["sleeve_duty"]))
    phase = rng.uniform(size=(1, names, k)) * gaps
    active = (t + phase) % gaps < dwell
    leg = s["invested_weight"] * active.astype(np.float32) / k
    coin = np.pad(leg.sum(axis=2) / names, ((warm, 0), (0, 0)))
    weight = coin.sum(axis=1)
    # Basket residual is already in the equal-weight hold. Use dispersion about equal exposure.
    idio_weight = np.sqrt(np.sum((coin - weight[:, None] / names) ** 2, axis=1))
    plant = np.pad((active.mean(axis=1) @ (np.asarray(s["paper_sized_gross_means"]) / dwell)) / k,
                   (warm, 0))
    delta = np.empty_like(coin)
    delta[0], delta[1:] = coin[0], np.diff(coin, axis=0)
    turnover = np.abs(delta).sum(axis=1)
    turnover[-1] += weight[-1]
    # Preserve realized cost base while shifting exposure in calendar months.
    return weight, idio_weight, plant, turnover, warm


def month_slices(days, first=0):
    starts = [first] + [i for i in range(first + 1, len(days)) if days[i].day == 1]
    return list(zip(starts, starts[1:] + [len(days)]))


def twin_weights(weight, periods, draws, rng):
    """Roll aggregate exposures within month. Approximation to matched ticket placements."""
    out = np.zeros((len(weight), draws), dtype=np.float32)
    for lo, hi in periods:
        length = hi - lo
        shifts = rng.integers(length, size=draws)
        out[lo:hi] = weight[lo + (np.arange(length)[:, None] + shifts) % length]
    return out, out**2


def stats(simple):
    if not np.all(simple > -1):
        raise ValueError("toy daily loss exceeds capital")
    log = np.cumsum(np.log1p(simple), axis=1)
    peak = np.maximum(np.maximum.accumulate(log, axis=1), 0)
    return log, np.max(-np.expm1(log - peak), axis=1)


def typical_turns(cfg, key, days, skip=0):
    s = cfg["synthetic"]
    span = len(dates(*s["paper_dates"]))
    return [[round((days - skip) / span * m * x, 1) for x in s["paper_counts"]]
            for m in (1, s["central_names"][key], s["inventory_ceiling_names"])]


def study(cfg, marks, cost_rows, key, case_name):
    s = cfg["synthetic"]
    c = s["cases"][case_name]
    rng = np.random.default_rng(s["seed"] + (key == "vault"))
    days = dates(*cfg[key])
    n, names = len(days), s["central_names"][key]
    w, wi, p, u, warm = schedule(days, names, cfg, rng)
    periods = month_slices(days, first=warm)
    if key == "repeat":
        a, a2 = twin_weights(w, periods, marks["twins"], np.random.default_rng(marks["twin_seed"]))
        year_stops = [i for i in range(1, n) if days[i].month == days[i].day == 1] + [n]
        cut = days.index(date.fromisoformat(cfg["repeat_cut"]))
    blocks = np.arange(n) // s["factor_block_days"]
    ny = marks["annual_days"]
    ib = wi * c["idio_vol"] / sqrt(ny)
    totals = {(cost, edge): 0 for cost in cost_rows for edge in s["edge_multipliers"]}
    for end in range(0, s["worlds"], s["batch"]):
        b = min(s["batch"], s["worlds"] - end)
        def normal(width):
            return rng.standard_normal((b, width), dtype=np.float32)

        shared = (sqrt(c["block_share"]) * normal(int(blocks[-1]) + 1)[:, blocks]
                  + sqrt(1 - c["block_share"]) * normal(n))
        basket = (c["market_drift"] / ny + c["market_vol"] / sqrt(ny) * shared
                  + c["idio_vol"] / sqrt(ny * names) * normal(n))
        btc = (c["market_drift"] / ny + c["btc_vol"] / sqrt(ny)
               * (c["btc_corr"] * shared + sqrt(1 - c["btc_corr"] ** 2) * normal(n)))
        basket[:, :warm] = btc[:, :warm] = 0
        base = basket * w + normal(n) * ib
        if key == "repeat":
            # Second-order log compounding and independent residual draws: a deliberately
            # approximate twin statistic, not the future exact twin placement algorithm.
            twin_log_base = (basket @ a - 0.5 * (basket**2 @ a2)
                             - 0.5 * (ib**2).sum()
                             + sqrt((ib**2).sum()) * normal(marks["twins"]))
            twin_no_cost = np.quantile(twin_log_base, marks["twin_percentile"] / 100, axis=1)
        for cost_name, side_bp in cost_rows.items():
            fee = side_bp / 10000
            debit = u * (1 + c["extra_turnover"]) * fee
            if key == "repeat":
                twin_cut = twin_no_cost - debit.sum()
                hold = basket.copy()
                hold[:, (warm, n - 1)] -= fee
                hold_log, _ = stats(hold)
            for edge in s["edge_multipliers"]:
                book = base + edge * p - debit
                log, dd = stats(book)
                sigma = book.std(axis=1, ddof=1)
                if key == "repeat":
                    year_end = log[:, np.asarray(year_stops) - 1]
                    yoy = np.diff(year_end, axis=1, prepend=0)
                    passes = ((log[:, -1] > hold_log[:, -1]) &
                              (book.mean(axis=1) * sqrt(ny) >= marks["min_sharpe"] * sigma) &
                              (sigma > 0) & (dd <= marks["max_drawdown"]) &
                              (log[:, -1] > twin_cut) &
                              (np.count_nonzero(yoy > 0, axis=1) >= cfg["repeat_years_positive"]) &
                              (log[:, cut - 1] > 0) & (log[:, -1] > log[:, cut - 1]))
                else:
                    scale = sigma / btc.std(axis=1, ddof=1)
                    matched = btc * scale[:, None]
                    matched[:, (warm, n - 1)] -= fee * scale[:, None]
                    matched_log, _ = stats(matched)
                    passes = ((log[:, -1] > 0) & (log[:, -1] > matched_log[:, -1]) &
                              (dd < marks["max_drawdown"]))
                totals[cost_name, edge] += int(np.count_nonzero(passes))
    return totals


def main():
    # Fixed settings only; the program offers no data, path or mode arguments.
    root = Path(__file__).resolve().parent.parent
    raw = yaml.safe_load((root / "config/thresholds.yaml").read_text())
    cfg = raw["replay_75_plan"]["value"]
    marks = raw[cfg["inherited_marks_key"]]["value"]
    costs = {line: sum(raw[key]["value"][field] for field in fields)
             for line, (key, *fields) in cfg["costs"].items()}
    s = cfg["synthetic"]
    print("Counts (10/20/30 sleeves, one BTC / central roster / 20-name ceiling)")
    for key in ("repeat", "vault"):
        days = len(dates(*cfg[key]))
        print(f"{key}: {days} d; full {typical_turns(cfg, key, days)}; "
              f"after warm-up {typical_turns(cfg, key, days, cfg['vol_days'] + 1)}")
    post = len(dates(cfg["after_paper_first"], cfg["vault"][1]))
    print(f"after_paper: {post} d; full {typical_turns(cfg, 'vault', post)}; no second warm-up")
    start = date.fromisoformat(cfg["repeat"][0])
    print("Earliest repeat signal closes (if complete):",
          [(n, str(start + timedelta(days=max(n - 1, cfg["vol_days"]))))
           for n in cfg["printed_lookbacks"]])
    print(f"{s['worlds']} worlds per line; pass counts in parentheses")
    print("| Stretch | Scenario | Cost per side | Zero | Half paper | Full paper |")
    print("|---|---|---:|---:|---:|---:|")
    for key in ("repeat", "vault"):
        for case in s["cases"]:
            res = study(cfg, marks, costs, key, case)
            for line, bp in costs.items():
                cells = [f"{res[line, e] / s['worlds']:.2%} ({res[line, e]})"
                         for e in s["edge_multipliers"]]
                print(f"| {key} | {case} | {line} {bp} bp | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
