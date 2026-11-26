"""Queue 110 / ledger 216 screen: dip gate against breakout gate, made-up data only.

No market data is read. No bars, no gate-open counts from held bars.
Run:  nice -n 10 python3 -B research_rig/power_110.py > research_rig/POWER_110.json

Judged comparison (fixed in doc 148): for each calendar week in which both gates
open at least one entry, D_w = mean market-adjusted 7-day net return of the dip
entries minus the same for the breakout entries. Both arms pay the same cost per
entry against a paper benchmark, so the cost cancels in D_w; gross and net D are equal.

Week noise model (assumption, scaled to a published spread):
  D_w = edge + c_w + e_w,
  var(c_w) = 0.5 * S^2                      (shared week part)
  var(e_w) = sig_e^2 * (1/kd + 1/kb), with sig_e^2 chosen so that a week with
  6 entries a side has total variance S^2 (Grobys et al. 2025 quintiles of the
  top 30 hold about 6 coins a side).
  The shared part follows AR(1) with rho 0.3 across calendar weeks (overlapping
  7-day holds entered daily).
S is the weekly sd of the published winner-minus-loser spread (STATED, see doc 148).

Noise shapes for the zero-edge calibration: normal; t3 scaled to the same sd;
common x2 (shared part doubled); jump (normal plus, with probability 1/416 a
week, a 250-point shock of random sign, after the -255.28 week in Grobys Table 1).

Marks (two-sided; the sign of the mean names the winning gate):
  M1 paired weeks >= 100
  M2 |Newey-West t, lag 2| >= cutoff (cutoff calibrated, from 1.96 by 0.01,
     until the zero-edge pass rate is at most 5% under every shape and count case)
  M3 mean keeps its sign after dropping the 1% of weeks (ceil) most favourable to it
  M4 the winning sign holds in at least 4 of the 7 calendar years 2020..2026
"""
import json
import math
import numpy as np

SIMS = 20000
WEEKS = 326          # 2020-01-01 to 2026-04-01, 2283 days
YEARS = np.minimum(2020 + (np.arange(WEEKS) * 7) // 365.25, 2026).astype(int)
RHO = 0.3
CAP = 0.05
LAG = 2
NULL_SHAPES = ['normal', 't3', 'common_x2', 'jump']

# Assumed entry counts (not counted from bars). p = share of weeks the gate opens
# at least one entry; k = mean entries in an open week (1 + Poisson(k-1)).
COUNTS = {
    'central':  {'p_dip': 0.55, 'k_dip': 4.0, 'p_brk': 0.70, 'k_brk': 6.0},
    'generous': {'p_dip': 0.80, 'k_dip': 10.0, 'p_brk': 0.80, 'k_brk': 10.0},
}
# Weekly sd of the published spread, percent (STATED in doc 148)
NOISE = {'grobys_s3_20.21': 20.21, 'grobys_s2_14.42': 14.42, 'ficura_implied_9.9': 9.9}
# Edges, dip minus breakout, percent per week (STATED in doc 148)
EDGES = {
    'grobys_s3_loser_minus_winner_+0.19': 0.19,
    'grobys_s1_-0.90': -0.90,
    'ficura_1w_-1.36': -1.36,
}


def draw(rng, S, cnt, shape, edge):
    n = SIMS
    od = rng.random((n, WEEKS)) < cnt['p_dip']
    ob = rng.random((n, WEEKS)) < cnt['p_brk']
    kd = 1 + rng.poisson(cnt['k_dip'] - 1, (n, WEEKS))
    kb = 1 + rng.poisson(cnt['k_brk'] - 1, (n, WEEKS))
    m = od & ob
    sc = math.sqrt(0.5) * S * (2.0 if shape == 'common_x2' else 1.0)
    sig_e2 = 0.5 * S * S / (2.0 / 6.0)
    z = rng.standard_normal((n, WEEKS))
    if shape == 't3':
        z = rng.standard_t(3, (n, WEEKS)) / math.sqrt(3.0)
    c = np.empty_like(z)
    c[:, 0] = z[:, 0]
    a = math.sqrt(1 - RHO * RHO)
    for t in range(1, WEEKS):
        c[:, t] = RHO * c[:, t - 1] + a * z[:, t]
    e = rng.standard_normal((n, WEEKS))
    if shape == 't3':
        e = rng.standard_t(3, (n, WEEKS)) / math.sqrt(3.0)
    d = edge + sc * c + np.sqrt(sig_e2 * (1.0 / kd + 1.0 / kb)) * e
    if shape == 'jump':
        j = rng.random((n, WEEKS)) < 1.0 / 416
        d = d + j * 250.0 * np.where(rng.random((n, WEEKS)) < 0.5, -1.0, 1.0)
    return d, m


def stats(d, m):
    mf = m.astype(float)
    nw = mf.sum(1)
    nn = np.maximum(nw, 1)
    mu = (d * mf).sum(1) / nn
    r = (d - mu[:, None]) * mf
    v = (r * r).sum(1)
    for l in range(1, LAG + 1):
        w = 1 - l / (LAG + 1)
        v = v + 2 * w * (r[:, l:] * r[:, :-l]).sum(1)
    v = np.maximum(v, 1e-12)
    t = mu / np.sqrt(v / (nn * nn))
    sgn = np.sign(mu)
    # M3: drop ceil(1%) weeks most favourable to the sign
    k = np.ceil(0.01 * nw).astype(int)
    fav = np.where(m, d * sgn[:, None], -np.inf)
    srt = -np.sort(-fav, axis=1)
    kmax = int(k.max()) if len(k) else 0
    drop = np.zeros(len(mu))
    for i in range(kmax):
        drop += np.where(i < k, srt[:, i], 0.0)
    trimmed = (mu * sgn * nn - drop) / np.maximum(nn - k, 1)
    m3 = trimmed > 0
    # M4: years with the winning sign
    ny = np.zeros(len(mu), int)
    for y in range(2020, 2027):
        sel = (YEARS == y)
        my = (d[:, sel] * mf[:, sel]).sum(1)
        ny += (my * sgn > 0)
    m4 = ny >= 4
    m1 = nw >= 100
    return t, m1, m3, m4, nw


def pass_rate(t, m1, m3, m4, cut, want=None):
    ok = m1 & (np.abs(t) >= cut) & m3 & m4
    if want is not None:
        ok = ok & (np.sign(t) == want)
    return float(ok.mean())


def main():
    out = {'sims': SIMS, 'weeks': WEEKS, 'rho': RHO, 'nw_lag': LAG, 'cap': CAP,
           'counts_assumed': COUNTS, 'noise_pct_per_week': NOISE, 'edges_pct_per_week': EDGES,
           'null': {}, 'power': [], 'paired_weeks_mean': {}}
    seed = 110000
    # 1. calibrate cutoff on zero edge
    null_t = []
    for cname, cnt in COUNTS.items():
        for nname, S in NOISE.items():
            for shape in NULL_SHAPES:
                seed += 1
                d, m = draw(np.random.default_rng(seed), S, cnt, shape, 0.0)
                st = stats(d, m)
                null_t.append((cname, nname, shape, st))
                out['paired_weeks_mean'][cname] = round(float(st[4].mean()), 1)
    cut = 1.96
    while True:
        worst = max(pass_rate(*st[:4], cut) for _, _, _, st in null_t)
        if worst <= CAP:
            break
        cut = round(cut + 0.01, 2)
    out['cutoff'] = cut
    for cname, nname, shape, st in null_t:
        out['null'][f'{cname}|{nname}|{shape}'] = {
            'all_marks': round(pass_rate(*st[:4], cut), 4),
            't_only': round(float((np.abs(st[0]) >= cut).mean()), 4)}
    # 2. power at the stated edges, normal and t3
    for cname, cnt in COUNTS.items():
        for nname, S in NOISE.items():
            for ename, edge in EDGES.items():
                for shape in ('normal', 't3'):
                    seed += 1
                    d, m = draw(np.random.default_rng(seed), S, cnt, shape, edge)
                    st = stats(d, m)
                    out['power'].append({'counts': cname, 'noise': nname, 'edge': ename, 'shape': shape,
                                         'right_sign_all_marks': round(pass_rate(*st[:4], cut, np.sign(edge)), 4),
                                         'wrong_sign_all_marks': round(pass_rate(*st[:4], cut, -np.sign(edge)), 4)})
    # 3. edge needed for 33% and 50% (normal), breakout-favoured direction, grid 0.2
    need = {}
    for cname, cnt in COUNTS.items():
        for nname, S in NOISE.items():
            got = {}
            for g in np.round(np.arange(0.2, 8.01, 0.2), 1):
                seed += 1
                d, m = draw(np.random.default_rng(seed), S, cnt, 'normal', -float(g))
                p = pass_rate(*stats(d, m)[:4], cut, -1.0)
                for lvl in (0.33, 0.5):
                    if lvl not in got and p >= lvl:
                        got[lvl] = float(g)
                if 0.5 in got:
                    break
            need[f'{cname}|{nname}'] = {'edge_for_33pct': got.get(0.33), 'edge_for_50pct': got.get(0.5)}
    out['edge_needed_pct_per_week'] = need
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
