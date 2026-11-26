"""Summarize finished TM scores and simulate TM09; never read prices or session packets."""
from collections import Counter, defaultdict
from datetime import date, datetime
from itertools import combinations
import json
from math import log1p, sqrt
from pathlib import Path
import statistics as st

import numpy as np
from scipy.stats import chi2
import yaml

ROOT = Path(__file__).resolve().parents[1]
TM = ROOT / "timemachine"
RIG = ROOT.parent / "rig"
SEED, SIMS = 22209, 120_000
EFFECTS = (20, 50, 100)
POWER_TARGET = .8
BOOT_WEEKS, ADAPT_TARGET = 5, 50


def read_json(p):
    return json.loads(p.read_text())


def read_saved(relative):
    # Only operator-named finished score files are admissible.
    allowed = {"tm_notes/" + x for x in (
        "results_tm06_six_fast.json", "results_tm06_g.json", "results_tm06_g2.json",
        "results_tm06_g3.json", "results_tm06_r_shown.json",
    )} | {"tm06_control_score.json"}
    if relative not in allowed:
        raise ValueError("not an approved finished score")
    p = RIG / relative
    if p.resolve() != p:
        raise ValueError("linked scores are not allowed")
    return read_json(p)


def rms(xs):
    return sqrt(st.mean(x * x for x in xs))


def weeks(window):
    a, b = (date.fromisoformat(window[k]) for k in ("start", "end"))
    return ((b - a).days + 1) / 7


def log_gap(a_pct, b_pct):
    return 10_000 * (log1p(a_pct / 100) - log1p(b_pct / 100))


def inventory():
    log = defaultdict(list)
    with (TM / "SESSIONS.jsonl").open() as f:
        for line in f:
            rec = json.loads(line)
            sid = rec.get("session", "")
            if sid[:5] in ("TM01-", "TM02-", "TM03-", "TM04-", "TM05-", "TM06-"):
                log[sid].append(rec)
    older = {i: read_json(TM / f"results_tm0{i}.json") for i in (1, 2, 3, 4, 6)}
    names = {m: x["name"] for m, x in older[4]["models"].items()}
    scored = defaultdict(list)
    matched = defaultdict(set)

    def add(group, sid, model, window=None):
        meta = log[sid][-1]
        w = window or meta["window"]
        scored[group].append(sid)
        matched[(model, w["start"], w["end"])].add(group)

    for i in (1, 2, 3):
        for m, x in older[i]["models"].items():
            for key in x["months_counted"]:
                row = x["months"][key]
                if row["finished"]:
                    add(f"TM0{i}", row["session"], names[m])

    stock, estimate = {}, []
    for m, x in older[4]["models"].items():
        a, b = (x["runs"][k] for k in ("r1", "r2"))
        ma, mb = (log[r["session"]][-1] for r in (a, b))
        assert a["finished"] and b["finished"]
        assert all(ma[k] == mb[k] for k in ("window", "wakes", "method", "method_sha256", "symbols", "model", "news"))
        first, last = (datetime.fromisoformat(ma["wakes"][k]).date() for k in ("first", "last"))
        length = (last - first).days / 7
        d = log_gap(a["gain_pct"], b["gain_pct"])
        amplitude = abs(d) / sqrt(length)
        stock[names[m]] = dict(session_ids=[a["session"], b["session"]], scored_pairs=1,
                               observed_week_pairs=0, wakes=a["wakes"], weeks_assumed=length,
                               final_gap_usd=x["run_spread"]["gain_gap_usd"],
                               terminal_log_gap_bp=d, implied_weekly_bp_one_draw=amplitude)
        estimate.append(amplitude)
        for r in (a, b):
            add("TM04", r["session"], names[m])

    notes = "tm_notes/results_tm06_"
    six = read_saved(notes + "six_fast.json")
    gfiles = [read_saved(notes + k + ".json") for k in ("g", "g2", "g3")]
    control = read_saved("tm06_control_score.json")
    tracked_control = older[6]["scores"][control["session"]]
    assert tracked_control == control == six["scores"][control["session"]]
    repeats, swing = defaultdict(dict), defaultdict(dict)
    for idx, f in enumerate([six, *gfiles]):
        for sid, x in f["scores"].items():
            part = x["part"]
            if part == "C":
                scored["TM06-control"].append(sid)
                continue
            add("TM06-R" if idx >= 2 else "TM06-" + part, sid, x["model"], x["window"])
            k = x["window"]["start"]
            fee = f"{x['main_fee_bps']:g}"
            if part == "S":
                assert weeks(x["window"]) == 1
                swing[x["model"]][k] = x["by_multiple"]["1x"][fee]["model"]["final_gain_pct"] * 100
            elif idx:
                repeats[k][idx] = (weeks(x["window"]), x["by_fee"][fee]["model"]["final_gain_pct"])
    shown = read_saved(notes + "r_shown.json")
    assert len(repeats) == len(shown["per_month_median"])
    fable_est, fable_blocks = defaultdict(list), []
    for _, group in sorted(repeats.items()):
        assert set(group) == {1, 2, 3}
        length = group[1][0]
        assert all(w == length for w, _ in group.values())
        fable_blocks.append(length)
        for a, b in combinations(sorted(group), 2):
            fable_est[f"g{a}_vs_g{b}"].append(log_gap(group[a][1], group[b][1]) / sqrt(length))
    coin_near = {}
    near_values = []
    start_usd = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["tm_account_start_usd"]["value"]
    for model, x in older[1]["models"].items():
        y = older[2]["models"][model]
        diffs = []
        for k in set(x["months_counted"]) & set(y["months_counted"]):
            a, b = x["months"][k], y["months"][k]
            w = log[a["session"]][-1]["window"]
            assert w == log[b["session"]][-1]["window"]
            ap, bp = (100 * z["gain_usd"] / start_usd for z in (a, b))
            diffs.append(log_gap(bp, ap) / sqrt(weeks(w)))
        coin_near[names[model]] = dict(matched_months=len(diffs), implied_weekly_rms_gap_bp=rms(diffs))
        near_values.extend(diffs)

    # This is weekly, but a different-model contrast is not a repeat-noise observation.
    across = []
    for a, b in combinations(swing.values(), 2):
        ds = [a[k] - b[k] for k in sorted(set(a) & set(b))]
        assert len(ds) == 4
        across.append(st.stdev(ds))
    overlaps = Counter()
    for groups in matched.values():
        overlaps.update(" vs ".join(p) for p in combinations(sorted(groups), 2))
    return dict(
        inventory={
            "scored_sessions_by_family": {k: sorted(v) for k, v in sorted(scored.items())},
            "matched_model_exact_windows_across_families": dict(sorted(overlaps.items())),
            "duplicate_index_ids_by_plan": dict(Counter(k[:4] for k, v in log.items() if len(v) > 1)),
            "tm05_indexed": sum(k.startswith("TM05-") for k in log),
            "tm06_fees_leverage_and_twins": "same saved decisions / controls, not fresh matching model sessions",
        },
        stocks={
            "within_model": stock,
            "observed_week_pairs": 0,
            "pooled_whole_run_pairs": len(estimate),
            "weekly_repeat_sd_inference": {
                "low": min(estimate), "central": rms(estimate), "high": max(estimate),
            },
        },
        coins={
            "tm06r_fable": dict(model="Claude Fable 5.2", sessions=sum(map(len, repeats.values())),
                              matched_months=len(repeats), full_run_pairings=len(fable_est),
                              pair_months=sum(map(len, fable_est.values())),
                              observed_week_pairs=0, elapsed_weeks_by_month=fable_blocks,
                              by_run_pair_implied_weekly_bp={k: rms(v) for k, v in fable_est.items()},
                              implied_weekly_rms_bp=rms([x for v in fable_est.values() for x in v])),
            "tm01_vs_tm02_near_comparison": dict(by_model=coin_near, pair_months=len(near_values),
                                              implied_weekly_rms_bp=rms(near_values), observed_week_pairs=0),
            "tm06_swing_across_models_not_repeats": dict(models=len(swing), unique_weeks=len(next(iter(swing.values()))),
                                                      different_model_pairs=len(across),
                                                      pair_weeks=sum(map(len, swing.values())) * (len(swing) - 1) // 2,
                                                      centered_pooled_weekly_sd_bp=rms(across)),
        },
    )


def contrast_sd(repeat_gap, n_p, n_n, boss_corr=0, within=.5, cross=.5):
    # v is the marginal single-session variance; common covariances cancel when equal.
    v = repeat_gap**2 / (2 * (1 - within))
    per_boss = v * ((1 - within) * (1 / n_p + 1 / n_n) + 2 * (within - cross))
    return sqrt(per_boss * (1 + boss_corr) / 2)


def hurdle(noise, t_min, wins):
    n = noise.shape[1]
    means = noise.mean(axis=1)
    test = t_min * noise.std(axis=1, ddof=1) / sqrt(n) - means
    signs = -np.partition(noise, n - wins, axis=1)[:, n - wins]
    return np.maximum(test, signs)


def power_summary(required, keep=None):
    keep = np.ones(len(required), dtype=bool) if keep is None else keep
    need = np.sort(required[keep])
    ix = int(np.ceil(POWER_TARGET * len(required))) - 1
    return dict(
        **{f"power_at_{x}_bp": float(np.mean(keep & (required < x))) for x in EFFECTS},
        power_at_zero=float(np.mean(keep & (required < 0))),
        bp_for_80pct=float(max(0., need[ix])) if ix < len(need) else None,
    )


def plan_power(stock):
    cfg = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["tm09"]["value"]
    n = cfg["window"]["weeks"]
    t_min, wins = (cfg["marks"][x] for x in ("primary_t_min", "positive_weeks_min"))
    assert len(cfg["boss_models"]) == 2
    rng = np.random.default_rng(SEED)
    normal = rng.standard_normal((SIMS, n))
    tails = rng.standard_t(5, (SIMS, n)) * sqrt(3 / 5)
    blind = rng.standard_normal((SIMS, BOOT_WEEKS)).std(axis=1, ddof=1)
    h_norm, h_tail = (hurdle(z, t_min, wins) for z in (normal, tails))
    unit_mde = np.quantile(h_norm, POWER_TARGET)
    cases = {}
    for name, s in stock["weekly_repeat_sd_inference"].items():
        base, more = (contrast_sd(s, p, q) for p, q in ((2, 1), (3, 3)))
        estimated_repeat = s * blind
        as_base = unit_mde * estimated_repeat * contrast_sd(1, 2, 1) <= ADAPT_TARGET
        as_more = ~as_base & (unit_mde * estimated_repeat * contrast_sd(1, 3, 3) <= ADAPT_TARGET)
        keep = as_base | as_more
        cases[name] = dict(
            inferred_repeat_gap_sd_bp=s,
            estimate_primary_sd_bp=base,
            base_normal=power_summary(base * h_norm),
            base_fat_tail_t5=power_summary(base * h_tail),
            base_shared_news_and_boss_noise=power_summary(contrast_sd(s, 2, 1, .5, .5, .25) * h_norm),
            three_each_normal=power_summary(more * h_norm),
            three_each_fat_tail_t5=power_summary(more * h_tail),
            three_each_shared_news_and_boss_noise=power_summary(contrast_sd(s, 3, 3, .5, .5, .25) * h_norm),
            scoring_or_news_subset_assumed_sd_scaling={
                str(scale): power_summary(scale * base * h_norm) for scale in (.5, .75, 1, 1.25)
            },
            blinded_adaptive_normal=dict(
                proceed_baseline=float(np.mean(as_base)), expand=float(np.mean(as_more)),
                stop=float(np.mean(~keep)), **power_summary(np.where(as_base, base, more) * h_norm, keep),
            ),
        )
    rehearsal = {}
    for confidence in (.9, .95):
        def interval(count):
            df = count - 1
            a = (1 - confidence) / 2
            return [sqrt(df / chi2.ppf(1 - a, df)), sqrt(df / chi2.ppf(a, df))]
        rehearsal[str(confidence)] = dict(
            multipliers_at_five_weeks=interval(5),
            min_weeks_by_factor={
                str(factor): next(
                    {"weeks": i, "interval_in_units_of_sample_sd": interval(i), "boss_sessions": 4 * i}
                    for i in range(2, 200)
                    if interval(i)[0] >= 1/factor and interval(i)[1] <= factor
                )
                for factor in (2, 1.5)
            },
        )
    return dict(seed=SEED, simulations=SIMS, weeks=n, primary_t_min=t_min, positive_weeks_min=wins,
                effects_bp=EFFECTS, blind_weeks=BOOT_WEEKS, blind_projected_target_bp=ADAPT_TARGET,
                max_primary_sd_for_80pct_at_20_bp=float(EFFECTS[0] / unit_mde),
                boss_sessions_baseline=n * len(cfg["boss_models"]) * 3,
                boss_sessions_three_each=n * len(cfg["boss_models"]) * 6,
                rehearsals=rehearsal, cases=cases)


def main():
    report = inventory()
    report["power"] = plan_power(report["stocks"])
    report["made_by"] = "research_rig/power_tm09.py"
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
