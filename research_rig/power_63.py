"""Plan 63 power sensitivity on price-blind clocks and approved dispersion only."""
import argparse
from datetime import date
from fractions import Fraction
import json
from math import ceil, erf, isfinite, sqrt
from pathlib import Path

import numpy as np

from count_63 import CUTOFF, EVENTS, EVENTS_SHA, HOLDS, SABA, candidates, schedule, select
from placebo_63 import touches_deny
from hashlib import sha256
from score_63 import FLOOR


EDGES = np.array((*range(0, 301, 5), *range(325, 1001, 25)))
CHANCES = (.50, .80)
COSTS = (40, 70, 120)
PLACEMENT = (.8, .9, 1.)
# Shared variance fractions: filing date, return-window session, same filer.
DEPENDENCE = {"independent": (0., 0., 0.), "moderate": (.10, .10, .02), "high": (.20, .25, .05)}
TAIL = .05
MAD_FACTOR = 1.482602218505602
SCALAR_FIELDS = {"scheduled_fund_windows", "capture_embargo_purge", "pre_sip_start", "target_overlap", "deny_segment", "missing_endpoint_or_identity",
                 "contributing_fund_windows", "placebo_filer_days", "placebo_non_saba_filer_days",
                 "sample_sd_bps", "scaled_mad_bps", "winsor_cap_bps"}


def noise_cases(sd, mad):
    if not (isfinite(sd) and isfinite(mad) and sd > 0 and mad > 0):
        raise ValueError("dispersion must be finite and positive")
    out = {"gaussian_sd": (sd, sd), "gaussian_scaled_mad": (mad, mad)}
    if mad < sd:
        def broad(calm):
            return sqrt((sd**2 - (1 - TAIL) * calm**2) / TAIL)
        absolute_median = mad / MAD_FACTOR
        low, high = 0., sd
        for _ in range(65):
            mid = (low + high) / 2
            cdf = ((1 - TAIL) * erf(absolute_median / (sqrt(2) * mid)) +
                   TAIL * erf(absolute_median / (sqrt(2) * broad(mid))))
            if cdf > .5:
                low = mid
            else:
                high = mid
        calm = (low + high) / 2
        out["two_scale_fit"] = (calm, broad(calm))
    return out


def design(raw, sessions, n, deny):
    _, deduped, days, closes = candidates(raw, sessions)
    members = [r for r in select(deduped, closes, n) if days[r["exit"]] <= CUTOFF and
               not touches_deny(deny, r["fund"], days[r["entry"]], days[r["exit"]])]
    keys = sorted({(r["day"], r["filer"]) for r in members})
    ids = {k: i for i, k in enumerate(keys)}
    members = [(ids[(r["day"], r["filer"])], r["entry"], r["exit"]) for r in members]
    gid, first, last = np.array(members, dtype=int).T
    count = np.bincount(gid)
    _, filing = np.unique([d.toordinal() for d, _ in keys], return_inverse=True)
    _, filer = np.unique([f for _, f in keys], return_inverse=True)
    year = np.array([d.year - 2016 for d, _ in keys])
    non_saba = np.array([f != SABA for _, f in keys])
    # A cluster's session shock is the mean across its constituent fund
    # windows, normalized to unit marginal variance using exact overlaps.
    overlap_norm = np.array([
        sqrt(sum(max(0, min(last[i], last[j]) - max(first[i], first[j]))
                 for i in np.flatnonzero(gid == k) for j in np.flatnonzero(gid == k)))
        for k in range(len(keys))
    ])
    if np.any(count < 1) or np.any(overlap_norm <= 0) or np.any(last - first != n):
        raise ValueError("price-blind window design mismatch")
    return filing, filer, year, non_saba, (gid, first, last, overlap_norm)


def pass_grid(z, days, year, non_saba, cap):
    count = len(z)
    if count < FLOOR or not np.any(non_saba):
        return np.zeros(len(EDGES), dtype=bool)
    k = count - ceil(count / 100)
    year_n = np.bincount(year, minlength=11)
    occupied = year_n > 0
    if np.count_nonzero(occupied) < 7:
        return np.zeros(len(EDGES), dtype=bool)
    year_mean = np.bincount(year, weights=z, minlength=11)[occupied] / year_n[occupied]
    min_edge_open = max(-np.mean(z), -np.mean(np.partition(z, k - 1)[:k]),
                        -np.mean(z[non_saba]), np.sort(-year_mean)[6])
    offsets = np.r_[0, np.flatnonzero(np.diff(days)) + 1]  # design order is sorted by filing day
    g = len(offsets)
    out = np.zeros(len(EDGES), dtype=bool)
    eligible = EDGES > min_edge_open
    if not np.any(eligible) or g < 2:
        return out
    z_win = np.clip(z[None, :] + EDGES[eligible, None], -cap, cap)
    centers = z_win.mean(axis=1)
    sums = np.add.reduceat(z_win - centers[:, None], offsets, axis=1)
    variances = g * np.sum(sums * sums, axis=1) / ((g - 1) * count * count)
    out[eligible] = (variances > 0) & (centers >= 2 * np.sqrt(variances))
    return out


def power(raw, sessions, dispersion, trials=2_000, seed=63001, deny=None):
    if not 0 < trials <= 100_000 or set(dispersion) != {str(n) for n in HOLDS}:
        raise ValueError("invalid simulation inputs")
    result = {}
    caps = {}
    for n in HOLDS:
        data = dispersion[str(n)]
        if set(data) != SCALAR_FIELDS or any(type(v) not in (int, float) for v in data.values()):
            raise ValueError("only approved aggregate dispersion is accepted")
        cap = data["winsor_cap_bps"]
        if not (isfinite(cap) and cap > 0 and cap == 5 * data["scaled_mad_bps"]):
            raise ValueError("winsor cap does not match the frozen placebo rule")
        caps[str(n)] = cap
        filing, filer, year, non_saba, spans = design(raw, sessions, n, {} if deny is None else deny)
        gid, first, last, norm = spans
        if not (2 <= data["placebo_filer_days"] <= len(filing) and
                data["scheduled_fund_windows"] == len(gid) and
                0 <= data["placebo_non_saba_filer_days"] <= data["placebo_filer_days"] and
                data["capture_embargo_purge"] + data["pre_sip_start"] + data["target_overlap"] +
                data["deny_segment"] + data["missing_endpoint_or_identity"] +
                data["contributing_fund_windows"] == len(gid)):
            raise ValueError("dispersion and price-blind counts disagree")
        result[str(n)] = {}
        for label, (s_date, s_window, s_filer) in DEPENDENCE.items():
            rng = np.random.default_rng(seed + n)
            cases = noise_cases(data["sample_sd_bps"], data["scaled_mad_bps"])
            counts = np.zeros((len(cases), len(PLACEMENT), len(EDGES)), dtype=int)
            placement_hits = np.zeros(len(PLACEMENT), dtype=int)
            for _ in range(trials):
                zeros = rng.standard_normal(len(filing))
                dates = rng.standard_normal(filing.max() + 1)[filing]
                filers = rng.standard_normal(filer.max() + 1)[filer]
                prefix = np.r_[0., np.cumsum(rng.standard_normal(last.max()))]
                window = np.bincount(gid, weights=prefix[last] - prefix[first]) / norm
                z = (sqrt(1 - s_date - s_window - s_filer) * zeros + sqrt(s_date) * dates +
                     sqrt(s_window) * window + sqrt(s_filer) * filers)
                place, tail = rng.random(len(filing)), rng.random(filing.max() + 1)[filing]
                for p, prob in enumerate(PLACEMENT):
                    k = place < prob
                    if np.count_nonzero(k) < FLOOR:
                        continue
                    placement_hits[p] += 1
                    for c, (calm, broad) in enumerate(cases.values()):
                        eps = z[k] * np.where(tail[k] < TAIL, broad, calm)
                        counts[c, p] += pass_grid(eps, filing[k], year[k], non_saba[k], cap)
            result[str(n)][label] = {case: {
                str(p): thresholds(counts[i, j], placement_hits[j], trials)
                for j, p in enumerate(PLACEMENT)} for i, case in enumerate(cases)}
    return {"trials": trials, "seed": seed, "hold_sessions": HOLDS, "net_edge_grid_bps": EDGES.tolist(),
            "paired_round_trip_drag_bps": COSTS, "primary_cost_bps": 70, "gross_even_chance_limit_bps": 150,
            "winsor_cap_bps": caps, "year_span": [date(2016, 1, 1).year, CUTOFF.year],
            "dependence_fractions_date_window_filer": DEPENDENCE,
            "minimum_net_edge_by_scenario": result, "controlling_rule": ruling(result)}


def ruling(results):
    controlling = {}
    for n in HOLDS:
        cases = results[str(n)]["moderate"]
        model = "two_scale_fit" if "two_scale_fit" in cases else "gaussian_sd"
        chance = cases[model]["0.9"]["edge_needed_bps"]
        edge = chance["0.5"]["gross_bps_by_cost"]["70"]
        controlling[n] = {"noise_model": model, "gross_bps_for_even_chance": edge,
                          "gross_bps_per_session": edge / n if edge is not None else None,
                          "qualifies": edge is not None and edge <= 150}
    qualifying = [n for n, row in controlling.items() if row["qualifies"]]
    ratio = lambda n: Fraction(controlling[n]["gross_bps_for_even_chance"], n)
    best = min(map(ratio, qualifying), default=None)
    # This is a mechanical recommendation, not authority to unseal targets.
    recommendation = next((n for n in qualifying if 10 * ratio(n) <= 11 * best), None)
    return {"by_hold": controlling, "recommend_hold_sessions": recommendation,
            "none_qualifies_close_without_target_prices": not qualifying}


def thresholds(hits, placed, trials):
    out = {}
    probabilities = hits / trials
    for chance in CHANCES:
        crossings = np.flatnonzero(probabilities >= chance)
        if not len(crossings):
            out[str(chance)] = {"net_bps": None, "gross_bps_by_cost": {str(c): None for c in COSTS}, "reason": (
                "placement_floor_limits_power" if placed / trials < chance else "not_reached_on_grid")}
            continue
        i = crossings[0]
        p = float(probabilities[i])
        out[str(chance)] = {"net_bps": int(EDGES[i]), "prior_grid_bps": int(EDGES[i - 1]) if i else None,
                            "gross_bps_by_cost": {str(c): int(EDGES[i]) + c for c in COSTS},
                            "chance_at_edge": p, "monte_carlo_se": sqrt(p * (1 - p) / trials)}
    return {"placement_probability": float(placed / trials), "zero_net_edge_pass": float(probabilities[0]),
            "edge_needed_bps": out}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("approved_dispersion_json", type=Path)
    cli.add_argument("dispersion_sha256")
    cli.add_argument("approved_design_json", type=Path)
    cli.add_argument("design_sha256")
    args = cli.parse_args()
    blob = EVENTS.read_bytes()
    if sha256(blob).hexdigest() != EVENTS_SHA:
        raise SystemExit("census hash mismatch")
    def checked(path, pin):
        b = path.read_bytes()
        if sha256(b).hexdigest() != pin:
            raise SystemExit("aggregate or price-free design hash mismatch")
        return json.loads(b)
    design_json = checked(args.approved_design_json, args.design_sha256)
    if (set(design_json) != {"schema", "excluded_subjects", "denied_segments"} or
            design_json["schema"] != "plan63-price-free-power-design-v1"):
        raise SystemExit("price-free design shape")
    census = [r for r in json.loads(blob) if r["cef_cik"] not in set(design_json["excluded_subjects"])]
    deny = {}
    for key, a, b in design_json["denied_segments"]:
        deny.setdefault(key, []).append((date.fromisoformat(a), date.fromisoformat(b)))
    print(json.dumps(power(census, schedule(), checked(args.approved_dispersion_json, args.dispersion_sha256),
                           deny=deny), sort_keys=True, indent=2))
