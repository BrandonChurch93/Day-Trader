"""Plan 65 synthetic power, redesigned rule (every session judged).

No market data is read. Only the session calendar is used, for week and year labels.
True net yearly Sharpe S is set; daily sd is 1 (scale free, marks are scale free).
Noise shapes:
  normal    : iid normal.
  t4        : iid Student t, 4 df, scaled to sd 1. No skew.
  skew_iid  : stress mix matched to the paper's skew 5.23 (Table 6, printed p.38).
              On 1% of days (iid) the return is s*Exp(1) (always positive);
              on the other 99% it is normal(a, sig). a, sig, s solved so that the
              mixture has mean S/sqrt(252), sd 1 and skew 5.23.
  skew_burst: same marginal as skew_iid, but jump days arrive in runs of 5
              consecutive sessions (crisis weeks), so they share week clusters.
  skew_half : jump days carry only 30% of the mean (base keeps 70%); skew is
              whatever that gives (reported). Softer stress.
"""
import json, sys
import numpy as np
from scipy.optimize import brentq

from pathlib import Path
HERE = Path(__file__).resolve().parent
CAL = HERE / 'calendar_65.json'
SEEDS = 2000
P_JUMP = 0.01
SKEW = 5.23
BURN = 126

sess = [x[0] for x in json.load(open(CAL))['sessions'] if x[0] <= '2026-11-25']   # scored span only (last_session)
# position set at close of session index i (i >= BURN), return to close i+1
exit_dates = sess[BURN + 1:]
N = len(exit_dates)
import datetime as dt
d = [dt.date.fromisoformat(x) for x in exit_dates]
weeks = np.unique([x.isocalendar()[:2] for x in d], axis=0, return_inverse=True)[1].ravel()
years = np.array([x.year for x in d])


def mix_params(mu, share=None):
    p = P_JUMP
    def solve_sig(a, s):
        sig2 = (1 + mu ** 2 - p * 2 * s ** 2) / (1 - p) - a ** 2
        return np.sqrt(sig2)
    def skew_of(s):
        a = (mu - p * s) / (1 - p)
        sig = solve_sig(a, s)
        m = mu
        e2 = 1 + mu ** 2
        e3 = (1 - p) * (a ** 3 + 3 * a * sig ** 2) + p * 6 * s ** 3
        return (e3 - 3 * m * e2 + 2 * m ** 3)
    if share is None:
        s = brentq(lambda s: skew_of(s) - SKEW, 1e-3, 6.9)
    else:
        s = share * mu / p
    a = (mu - p * s) / (1 - p)
    return a, solve_sig(a, s), s, skew_of(s)


def draw(kind, S, rng, n_seeds):
    mu = S / np.sqrt(252)
    if kind == 'normal':
        return mu + rng.standard_normal((n_seeds, N))
    if kind == 't4':
        return mu + rng.standard_t(4, (n_seeds, N)) / np.sqrt(2.0)
    share = 0.30 if kind == 'skew_half' else None
    a, sig, s, _ = mix_params(mu, share)
    base = a + sig * rng.standard_normal((n_seeds, N))
    jumps = s * rng.exponential(1.0, (n_seeds, N))
    if kind == 'skew_burst':
        starts = rng.random((n_seeds, N)) < P_JUMP / 5
        mask = np.zeros_like(starts)
        for k in range(5):
            mask[:, k:] |= starts[:, :N - k]
    else:
        mask = rng.random((n_seeds, N)) < P_JUMP
    return np.where(mask, jumps, base)


G = weeks.max() + 1
YEARS = np.unique(years)
K_DROP = int(np.ceil(0.01 * N))


def marks(R):
    m = R.mean(1)
    dev = R - m[:, None]
    g = np.zeros((R.shape[0], G))
    for j in range(R.shape[0]):
        g[j] = np.bincount(weeks, weights=dev[j], minlength=G)
    se = np.sqrt(G / (G - 1) * (g ** 2).sum(1)) / N
    t = m / se
    srt = np.sort(R, 1)
    trim = srt[:, :-K_DROP].mean(1)
    yp = np.zeros(R.shape[0], int)
    for y in YEARS:
        yp += R[:, years == y].mean(1) > 0
    ok = np.stack([np.full(R.shape[0], N >= 2400), m > 0, t >= 2, trim > 0, yp >= 7])
    return ok


def power(kind, S):
    rng = np.random.default_rng(65)
    ok = np.zeros(5)
    allp = 0
    for b in range(SEEDS // 250):
        okb = marks(draw(kind, S, rng, 250))
        ok += okb.sum(1)
        allp += okb.all(0).sum()
    return allp / SEEDS, (ok / SEEDS).round(3).tolist()


if __name__ == '__main__':
    kinds = ['normal', 't4', 'skew_iid', 'skew_burst', 'skew_half']
    out = {'N_judged': int(N), 'n_week_clusters': int(G), 'years': YEARS.tolist(), 'seeds': SEEDS,
           'p_jump': P_JUMP, 'skew_target': SKEW, 'table': [], 'even_chance_sharpe': {}, 'mix': {}}
    for S in (0.9, 0.6, 0.45, 0.3):
        mu = S / np.sqrt(252)
        a, sig, s, _ = mix_params(mu)
        a2, sig2, s2, m3 = mix_params(mu, 0.30)
        out['mix'][str(S)] = {'skew_iid_jump_share_of_mean': round(P_JUMP * s / mu, 3), 'jump_scale_sd': round(s, 3),
                              'skew_half_skew': round(float(m3), 2)}
    for kind in kinds:
        for S in (0.9, 0.6, 0.45, 0.3):
            p, each = power(kind, S)
            out['table'].append({'kind': kind, 'sharpe': S, 'pass_all': p, 'each': each})
            print(kind, S, p, each); sys.stdout.flush()
        grid = np.round(np.arange(0.30, 2.01, 0.05), 2)
        lo = None
        for S in grid:
            p, _ = power(kind, S)
            if p >= 0.5:
                lo = float(S); break
        out['even_chance_sharpe'][kind] = lo
        print(kind, 'even chance at', lo); sys.stdout.flush()
    json.dump(out, open(HERE / 'POWER_65.json', 'w'), indent=1)
