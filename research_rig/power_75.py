"""Offline Plan 75 count and synthetic power only; no prices, archive paths, or runtime."""

from datetime import date, timedelta
from math import sqrt
from pathlib import Path

import numpy as np
import yaml


def dates(first, stop):
    start, end = map(date.fromisoformat, (first, stop))
    return [start + timedelta(days=i) for i in range((end - start).days)]


def schedule(days, names, cfg, phase_rng, worlds):
    """Toy episodes; each world independently draws every coin/leg phase."""
    s = cfg["synthetic"]
    n, k = len(days), len(cfg["lookbacks"])
    paper_days = len(dates(*s["paper_dates"]))
    # The first simulated return after a next-open fill needs 91 completed closes.
    warm = cfg["vol_days"] + 1
    t = np.arange(n - warm, dtype=np.float32)[None, :, None]
    gaps = np.asarray(paper_days / np.array(s["paper_counts"]))
    dwell = np.maximum(1, np.rint(gaps * s["sleeve_duty"]))
    phases = phase_rng.random((worlds, 1, names, k), dtype=np.float32)
    coin = np.zeros((worlds, n, names), dtype=np.float32)
    plant = np.zeros((worlds, n), dtype=np.float32)
    for j, (gap, span) in enumerate(zip(gaps, dwell, strict=True)):
        active = (t + phases[..., j] * np.float32(gap)) % np.float32(gap) < span
        coin[:, warm:] += active * np.float32(s["invested_weight"] / (k * names))
        plant[:, warm:] += active.sum(axis=2) * (s["paper_sized_gross_means"][j] / (span * k * names))
    weight = coin.sum(axis=2)
    # Basket residual is already in the equal-weight hold. Use dispersion about equal exposure.
    idio_weight = np.sqrt(np.sum((coin - weight[..., None] / names) ** 2, axis=2))
    turnover = np.abs(np.diff(coin, axis=1, prepend=np.zeros_like(coin[:, :1]))).sum(axis=2)
    turnover[:, -1] += weight[:, -1]
    return weight, idio_weight, plant, turnover, warm


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
    phase_rng = np.random.default_rng(np.random.SeedSequence([s["seed"], 75, key == "vault"]))
    days = dates(*cfg[key])
    n, names = len(days), s["central_names"][key]
    if key == "repeat":
        cut = days.index(date.fromisoformat(cfg["repeat_cut"]))
    else:
        cut = days.index(date.fromisoformat(cfg["after_paper_first"]))
    blocks = np.arange(n) // s["factor_block_days"]
    ny = marks["annual_days"]
    totals = {(cost, edge): 0 for cost in cost_rows for edge in s["edge_multipliers"]}
    for end in range(0, s["worlds"], s["batch"]):
        b = min(s["batch"], s["worlds"] - end)
        w, wi, p, u, warm = schedule(days, names, cfg, phase_rng, b)
        ib = wi * c["idio_vol"] / sqrt(ny)
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
        for cost_name, side_bp in cost_rows.items():
            fee = side_bp / 10000
            debit = u * (1 + c["extra_turnover"]) * fee
            for edge in s["edge_multipliers"]:
                book = base + edge * p - debit
                log, dd = stats(book)
                sigma = book.std(axis=1, ddof=1)
                if key == "repeat":
                    passes = (log[:, -1] > 0) & ((log[:, cut - 1] > 0) |
                                                  (log[:, -1] > log[:, cut - 1]))
                else:
                    scale = sigma / btc.std(axis=1, ddof=1)
                    matched = btc * scale[:, None]
                    matched[:, (warm, n - 1)] -= fee * scale[:, None]
                    matched_log, _ = stats(matched)
                    old_passes = ((log[:, -1] > 0) & (log[:, -1] > matched_log[:, -1]) &
                                  (dd < marks["max_drawdown"]))
                    passes = old_passes & (log[:, -1] - log[:, cut - 1] >=
                                           np.log1p(cfg["after_paper_min_net"]))
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
