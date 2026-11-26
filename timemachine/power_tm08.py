"""Made-up-data power for the draft TM08 mark (dip card minus breakout card).

No market data is read. The noise sizes come from two repo files of already
scored months (timemachine/results_tm01.json and results_tm02.json): the
monthly gain of the same model on two cards in the same month (TM02 minus
TM01), split into a part shared by every model in that month and the rest.
Writes timemachine/POWER_TM08.json. Run: nice -n 10 python3 timemachine/power_tm08.py
"""
import json, math, os, statistics as st
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
START_USD = 1000.0
SIMS = 20000
SEED = 8008
MODELS = 6
RUNS = (1, 2, 3)
MONTHS = (3, 6, 12)
EDGES = (0.0, 0.5, 1.0, 2.0)          # true dip-minus-breakout gain, % of the account per month
NULL_CAP = 0.025                      # one-sided false-pass cap for the judged mark
CUT_START, CUT_STEP = 1.50, 0.01
WEEKS_PER_MONTH = 52 / 12


def noise_from_repo():
    a = json.load(open(os.path.join(HERE, 'results_tm01.json')))['models']
    b = json.load(open(os.path.join(HERE, 'results_tm02.json')))['models']
    mods = sorted(a)
    months = sorted(a[mods[0]]['months'])
    d = {(m, k): (b[m]['months'][k]['gain_usd'] - a[m]['months'][k]['gain_usd']) / START_USD * 100
         for m in mods for k in months}
    mm = {k: st.mean(d[(m, k)] for m in mods) for k in months}
    res = [d[(m, k)] - mm[k] for m in mods for k in months]
    sd_e = math.sqrt(sum(x * x for x in res) / (len(res) - len(months)))
    var_mm = st.variance(mm.values())
    sd_c = math.sqrt(max(var_mm - sd_e ** 2 / len(mods), 0.0))
    cm = [v - st.mean(mm.values()) for v in mm.values()]
    return {'models': mods, 'months': months, 'cells': len(res), 'sd_cell_pct': sd_e,
            'sd_month_common_pct': sd_c, 'sd_month_means_pct': math.sqrt(var_mm),
            'resid_pct': res, 'month_centred_pct': cm}


def draw(rng, shape, n, sd, pool=None):
    if shape == 'normal':
        return rng.normal(0, sd, n)
    if shape == 't4':
        return rng.standard_t(4, n) * sd / math.sqrt(2.0)
    if shape == 'resampled':
        p = np.asarray(pool, float)
        p = p / p.std() * sd if p.std() > 0 else p
        return rng.choice(p, n)
    raise ValueError(shape)


def month_means(rng, shape, sims, M, R, edge, N):
    """sims x M array: the month mean of dip minus breakout over MODELS x R cells."""
    c = draw(rng, shape, sims * M, N['sd_c'], N['month_centred_pct']).reshape(sims, M)
    e = draw(rng, shape, sims * M * MODELS * R, N['sd_e'], N['resid_pct']).reshape(sims, M, MODELS * R)
    return edge + c + e.mean(axis=2)


def mark(D, cut):
    M = D.shape[1]
    mu = D.mean(axis=1)
    sd = D.std(axis=1, ddof=1)
    t = np.where(sd > 0, mu / (sd / math.sqrt(M)), -np.inf)
    trim = (D.sum(axis=1) - D.max(axis=1)) / (M - 1)
    return (t >= cut) & (trim > 0)


def main():
    nz = noise_from_repo()
    shapes = {
        'normal': {'sd_e': nz['sd_cell_pct'], 'sd_c': nz['sd_month_common_pct']},
        'normal_common_x2': {'sd_e': nz['sd_cell_pct'], 'sd_c': 2 * nz['sd_month_common_pct']},
        't4': {'sd_e': nz['sd_cell_pct'], 'sd_c': nz['sd_month_common_pct']},
        'resampled': {'sd_e': nz['sd_cell_pct'], 'sd_c': nz['sd_month_common_pct']},
    }
    out = {'made_by': 'timemachine/power_tm08.py', 'sims_per_cell': SIMS, 'seed': SEED,
           'models': MODELS, 'null_cap': NULL_CAP, 'edges_pct_per_month': list(EDGES),
           'noise': {k: v for k, v in nz.items() if k not in ('resid_pct', 'month_centred_pct')},
           'cutoffs': {}, 'power': {}, 'weekly_if_independent': {}}
    rng_seed = SEED
    for M in MONTHS:
        for R in RUNS:
            key = f'M{M}_R{R}'
            # cutoff: smallest on the grid with null rate <= cap under every shape
            nulls = {}
            for s, P in shapes.items():
                rng = np.random.default_rng(rng_seed); rng_seed += 1
                N = dict(P, **nz)
                nulls[s] = month_means(rng, s.replace('_common_x2', ''), SIMS, M, R, 0.0, N)
            cut = CUT_START
            while max(mark(D, cut).mean() for D in nulls.values()) > NULL_CAP:
                cut = round(cut + CUT_STEP, 2)
            out['cutoffs'][key] = cut
            cell = {}
            for s, P in shapes.items():
                N = dict(P, **nz)
                row = {}
                for edge in EDGES:
                    if edge == 0.0:
                        row['0.0'] = float(mark(nulls[s], cut).mean())
                        continue
                    rng = np.random.default_rng(rng_seed); rng_seed += 1
                    D = month_means(rng, s.replace('_common_x2', ''), SIMS, M, R, edge, N)
                    row[str(edge)] = float(mark(D, cut).mean())
                cell[s] = row
            out['power'][key] = cell
    # shown only: weekly clusters, as if weeks were independent (optimistic)
    for M in (6,):
        R = 2
        W = int(round(M * WEEKS_PER_MONTH))
        N = {'sd_e': nz['sd_cell_pct'] / math.sqrt(WEEKS_PER_MONTH),
             'sd_c': nz['sd_month_common_pct'] / math.sqrt(WEEKS_PER_MONTH), **nz}
        rng = np.random.default_rng(rng_seed); rng_seed += 1
        D0 = month_means(rng, 'normal', SIMS, W, R, 0.0, N)
        cut = CUT_START
        while mark(D0, cut).mean() > NULL_CAP:
            cut = round(cut + CUT_STEP, 2)
        row = {'weeks': W, 'cutoff': cut, '0.0': float(mark(D0, cut).mean())}
        for edge in EDGES[1:]:
            rng = np.random.default_rng(rng_seed); rng_seed += 1
            D = month_means(rng, 'normal', SIMS, W, R, edge / WEEKS_PER_MONTH, N)
            row[str(edge)] = float(mark(D, cut).mean())
        out['weekly_if_independent'][f'M{M}_R{R}'] = row
    # shown only: the first half of the queue row's proposed mark (dip above breakout in at least
    # 5 of 6 models, each model's months summed). Its twin half is not modelled, so this is an upper bound.
    M, R = 6, 2
    q = {}
    for edge in EDGES:
        rng = np.random.default_rng(rng_seed); rng_seed += 1
        N = {'sd_e': nz['sd_cell_pct'], 'sd_c': nz['sd_month_common_pct'], **nz}
        c = rng.normal(0, N['sd_c'], (SIMS, M, 1))
        e = rng.normal(0, N['sd_e'], (SIMS, M, MODELS, R)).mean(axis=3)
        per_model = (edge + c + e).sum(axis=1)
        q[str(edge)] = float(((per_model > 0).sum(axis=1) >= 5).mean())
    out['queue_row_mark_5_of_6_models_M6_R2_normal'] = q
    path = os.path.join(HERE, 'POWER_TM08.json')
    with open(path, 'w') as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write('\n')
    print(json.dumps({'noise': out['noise'], 'cutoffs': out['cutoffs']}, indent=1))
    for k, v in out['power'].items():
        print(k, {s: {e: round(p * 100, 2) for e, p in r.items()} for s, r in v.items()})
    print('weekly', out['weekly_if_independent'])
    print('queue 5 of 6', q)


if __name__ == '__main__':
    main()
