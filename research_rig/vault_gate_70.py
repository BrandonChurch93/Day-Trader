"""Plan 70 fixed vault calendar, shared mark and paired search-day bootstrap."""
import math
from datetime import date, datetime, timezone

import numpy as np

from sweep_70 import DAYS, HOUR, t_cluster

FIRST = date(2024, 1, 1)
LAST = date(2026, 11, 1)
VAULT_DAYS = (LAST - FIRST).days
VAULT_START, VAULT_STOP = (int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
                           for d in (FIRST, LAST))
VAULT_HOURS = np.arange(VAULT_START, VAULT_STOP, HOUR)
HALF_YEAR = np.repeat(np.arange(6), np.diff([(d - FIRST).days for d in (
    FIRST, date(2024, 7, 1), date(2025, 1, 1), date(2025, 7, 1),
    date(2026, 1, 1), date(2026, 7, 1), LAST)]))


def marks(plain, paired, day, config):
    n = len(plain)
    if (plain.ndim != 1 or plain.shape != paired.shape or plain.shape != day.shape
            or np.any(day < 0) or np.any(day >= VAULT_DAYS)
            or not np.all(np.isfinite(plain)) or not np.all(np.isfinite(paired))):
        raise ValueError("invalid vault ticket vectors")
    active = int(np.unique(day).size)
    total = float(plain.sum())
    annual = total * config["annualization_days"] / VAULT_DAYS
    halves = np.bincount(HALF_YEAR[day], weights=plain, minlength=6)
    positives = int(np.count_nonzero(halves > 0))
    t = t_cluster(paired, day)
    keep = n - math.ceil(config["trim_share"] * n)
    trimmed = float(np.sort(plain)[:keep].mean()) if keep else None
    return {"trades": n, "active_days": active, "plain_mean": total / n if n else None,
            "paired_mean": float(paired.mean()) if n else None, "paired_day_t": t,
            "plain_trimmed_mean": trimmed, "half_year_plain_sums": halves.tolist(),
            "positive_half_years": positives, "simple_net_annual": annual,
            "meets_vault_marks": bool(active >= config["min_days"] and total > 0
                                      and t is not None and t >= config["full_t"]
                                      and trimmed is not None and trimmed > 0
                                      and positives >= config["positive_half_years"]
                                      and annual >= config["annual_min"])}


def day_matrix(plain, paired, day, multiplier):
    if (plain.ndim != 1 or not len(plain) or plain.shape != paired.shape or plain.shape != day.shape
            or np.any(np.diff(day) < 0) or day[0] < 0 or day[-1] >= DAYS
            or not np.all(np.isfinite(plain)) or not np.all(np.isfinite(paired))):
        raise ValueError("missing, non-finite or misordered search tickets")
    counts = np.bincount(day, minlength=DAYS)
    j = np.arange(len(day)) - (counts.cumsum() - counts)[day]
    mask = np.zeros((DAYS, counts.max()), dtype=bool)
    pairs = np.zeros((*mask.shape, 2))
    mask[day, j] = True
    for k, series in enumerate((plain, paired)):
        mean = series.mean()
        pairs[day, j, k] = series - mean + multiplier * mean
    return pairs, mask


def sampled_days(starts, width):
    return ((starts[:, None] + np.arange(width)) % DAYS).ravel()[:VAULT_DAYS]


def bootstrap(rule_id, plain, paired, day, settings):
    gate, params = settings["vault_marks"], settings["vault_power"]
    pairs, mask = day_matrix(plain, paired, day, gate["search_mean_haircut_multiplier"])
    width, draws = params["block_days"], params["draws"]
    seed = params["seed_base"] + int(rule_id.split("-")[1])
    rng = np.random.Generator(np.random.PCG64(seed))
    passes = 0
    for starts in rng.integers(0, DAYS, size=(draws, (VAULT_DAYS + width - 1) // width)):
        dates = sampled_days(starts, width)
        valid = mask[dates]
        tickets = pairs[dates][valid]
        dates_with_tickets = np.nonzero(valid)[0]
        passes += marks(tickets[:, 0], tickets[:, 1], dates_with_tickets, gate)["meets_vault_marks"]
    probability = passes / draws
    return {"rule": rule_id, "seed": seed, "draws": draws, "passes": passes,
            "probability": probability, "carry": probability >= gate["min_pre_vault_power"]}
