"""Research rig, second version. Written after the code audit of 2026-11-25 (see AMENDMENT_2026-11-25_audit_fixes.md).
Not the product. Signals use bars up to and including t. Orders fill at the open of the next bar that really traded.
Every pass mark number is read from config/thresholds.yaml."""
import numpy as np, pandas as pd, math, os, yaml
from itertools import combinations
from scipy import stats

_HERE = os.path.dirname(os.path.abspath(__file__))
_TH = yaml.safe_load(open(os.path.join(_HERE, "..", "config", "thresholds.yaml")))
def th(key):
    return _TH[key]["value"]
def thresholds_used():
    keys = ["backtest_max_pbo", "backtest_min_breakeven_cost_multiple", "replay_max_drop_ratio_vs_hold",
            "replay_min_deflated_sharpe", "replay_min_shuffle_percentile"]
    return {k: th(k) for k in keys}

VENUES = {"Binance.US": 2, "Alpaca": 25, "Kraken $10k tier": 38, "Kraken entry": 80, "Coinbase entry": 90}
SLIP = 5
SL = {"dev": (None, "2022-12-31"), "held": ("2023-01-01", "2026-06-30"), "post": ("2026-07-01", "2026-11-24"), "all": (None, "2026-11-24")}
DUST = 1e-9

# ---------------------------------------------------------------- input checks (A17)
def check_bars(d, freq):
    """d: frame indexed by naive UTC timestamps with open, high, low, close, volume."""
    assert d.index.tz is None, "index must be naive UTC"
    assert d.index.is_monotonic_increasing and d.index.is_unique, "index must be sorted and unique"
    step = pd.Timedelta(freq)
    assert ((d.index[1:] - d.index[:-1]) == step).all(), "bars must be on a complete grid"
    if freq == "1D": assert (d.index == d.index.normalize()).all(), "daily bars must sit at 00:00 UTC"
    assert (d[["open", "high", "low", "close"]] > 0).all().all(), "prices must be positive"
    assert d[["open", "high", "low", "close", "volume"]].notna().all().all(), "no missing values"

# ---------------------------------------------------------------- engines
def simulate(opens, closes, target, cost_bps, band=0.10, start_cash=1.0, can_fill=None):
    """General engine (fractional weights). target[t] is decided at the close of bar t and acted on at the open of
    bar t+1 if that bar can fill. A trade happens only when the target differs from the current weight by more than
    band (no exception for moves to or from zero, A12). Returns equity at each close, weight at each close, traded
    dollars per bar."""
    n = len(closes); eq = np.empty(n); wt = np.empty(n); traded = np.zeros(n)
    cash = start_cash; units = 0.0; c = cost_bps / 1e4
    for t in range(n):
        if t > 0 and (can_fill is None or can_fill[t]):
            tw = target[t - 1]
            if not np.isnan(tw):
                o = opens[t]; have = units * o; e = cash + have; cur = have / e if e > 0 else 0.0
                if abs(tw - cur) > band:
                    want = tw * e
                    if want > have:
                        x = (want - have) / (1 + tw * c)
                        if x >= cash / (1 + c) or tw >= 1.0:
                            x = cash / (1 + c); cash = 0.0
                        else:
                            cash -= x * (1 + c)
                        units += x / o; traded[t] = x
                    else:
                        if tw <= 0.0:
                            x = have; units = 0.0
                        else:
                            x = min((have - want) / (1 - tw * c), have); units -= x / o
                        cash += x * (1 - c); traded[t] = x
        eq[t] = cash + units * closes[t]; wt[t] = units * closes[t] / eq[t] if eq[t] > 0 else 0.0
    return eq, wt, traded

def held_from_target(target, can_fill=None):
    """Position held during each bar for a 0/1 target. Bar 0 is always flat."""
    assert not np.isnan(target).any(), "binary targets must not contain NaN (A15)"
    n = len(target); want = np.zeros(n); want[1:] = target[:-1]
    if can_fill is None: return want
    idx = np.where(can_fill, np.arange(n), 0); idx[0] = 0
    idx = np.maximum.accumulate(idx); want[0] = 0.0
    return want[idx]

def sim_fast(o, c, target, cost_bps, can_fill=None):
    """Vectorised engine for 0/1 targets. Must equal simulate() on the same input (checked in fixtures2.py)."""
    k = cost_bps / 1e4; held = held_from_target(target, can_fill)
    prev = np.zeros(len(c)); prev[1:] = held[:-1]; pc = np.empty(len(c)); pc[0] = c[0]; pc[1:] = c[:-1]
    f = np.ones(len(c))
    stay = (held == 1) & (prev == 1); f[stay] = c[stay] / pc[stay]
    ent = (held == 1) & (prev == 0); f[ent] = c[ent] / o[ent] / (1 + k)
    ex = (held == 0) & (prev == 1); f[ex] = o[ex] / pc[ex] * (1 - k)
    return np.cumprod(f), held

def with_base(eq, index, start_cash=1.0):
    """Equity series with the starting cash put in front, one bar before the first bar (A02)."""
    step = index[1] - index[0]
    return pd.Series(np.r_[start_cash, eq], index=index.insert(0, index[0] - step))

def cut(eqp, lo, hi):
    """Slice of an equity series that starts from the last value before lo, so the first day's return is in (A03)."""
    hi_ = pd.Timestamp(hi) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    i1 = eqp.index.searchsorted(hi_, side="right")
    i0 = 0 if lo is None else max(0, eqp.index.searchsorted(pd.Timestamp(lo), side="left") - 1)
    return eqp.iloc[i0:i1]

# ---------------------------------------------------------------- measures
def metrics(eqp, ppy=365, rf=None):
    """eqp: equity values whose first entry is the starting value. rf: per-period cash return, same length as returns."""
    eqp = np.asarray(eqp, float); r = eqp[1:] / eqp[:-1] - 1; n = len(r); years = n / ppy
    x = r if rf is None else r - rf
    sd = x.std(ddof=1) if n > 1 else 0.0
    peak = np.maximum.accumulate(eqp)
    return dict(cagr=(eqp[-1] / eqp[0]) ** (1 / years) - 1 if eqp[-1] > 0 else -1.0, vol=float(r.std(ddof=1) * math.sqrt(ppy)) if n > 1 else 0.0,
                sharpe=float(x.mean() / sd * math.sqrt(ppy)) if sd > 0 else float("nan"),
                maxdd=float((eqp / peak - 1).min()), total=float(eqp[-1] / eqp[0] - 1), n=int(n))

def rets(eqp):
    v = np.asarray(eqp, float); return v[1:] / v[:-1] - 1

def sharpe_pp(r):
    s = r.std(ddof=1) if len(r) > 1 else 0.0
    return r.mean() / s if s > 0 else float("nan")

def activity(eq, wt, traded, index, lo, hi, ppy=365):
    """Both exposure measures and trade counts for a slice (A04, A09). Trades are counted on the fill bar."""
    e = pd.Series(eq, index=index); prev = e.shift(1).fillna(1.0)
    m = np.ones(len(index), bool) if lo is None else (index >= pd.Timestamp(lo))
    m &= index < pd.Timestamp(hi) + pd.Timedelta(days=1)
    econ = traded > DUST * prev.values
    yrs = m.sum() / ppy
    return dict(avg_weight=float(wt[m].mean()), share_of_bars_with_position=float((wt[m] > 1e-6).mean()),
                sides=int(econ[m].sum()), turnover_py=float((traded[m] / prev.values[m]).sum() / yrs) if yrs > 0 else 0.0)

# ---------------------------------------------------------------- statistics
def deflated_sharpe(r, n_trials, sr_trials_std):
    """Bailey and Lopez de Prado. Returns nan when it cannot be worked out (A06). nan never counts as a pass."""
    T = len(r); sr = sharpe_pp(r)
    if T < 30 or not np.isfinite(sr) or not np.isfinite(sr_trials_std): return float("nan"), float("nan")
    g3 = stats.skew(r); g4 = stats.kurtosis(r, fisher=False); em = 0.5772156649
    sr0 = sr_trials_std * ((1 - em) * stats.norm.ppf(1 - 1 / n_trials) + em * stats.norm.ppf(1 - 1 / (n_trials * math.e)))
    den = math.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr * sr))
    return float(stats.norm.cdf((sr - sr0) * math.sqrt(T - 1) / den)), float(sr0)

def pbo_cscv(R, S=16, drop="earliest"):
    """Probability of backtest overfitting, combinatorially symmetric cross-validation with equal blocks (A05).
    Rows that do not fill a block are dropped from the start (drop='earliest') or the end (drop='latest').
    A rule with no variation inside a half gets Sharpe 0 there, and the count of such cases is returned (A06)."""
    T, N = R.shape; B = T // S; used = B * S
    R = R[T - used:] if drop == "earliest" else R[:used]
    X = R.reshape(S, B, N); bs = X.sum(1); bq = (X ** 2).sum(1); n = (S // 2) * B
    tot_s = bs.sum(0); tot_q = bq.sum(0); lam = []; zero = 0
    def sh(s, q):
        nonlocal zero
        mean = s / n; var = (q - n * mean ** 2) / (n - 1); ok = var > 1e-18
        zero += int((~ok).sum())
        return np.where(ok, mean / np.sqrt(np.where(ok, var, 1.0)), 0.0)
    for comb in combinations(range(S), S // 2):
        ix = list(comb); s_in = bs[ix].sum(0); q_in = bq[ix].sum(0)
        sa = sh(s_in, q_in); sb = sh(tot_s - s_in, tot_q - q_in)
        best = int(np.argmax(sa)); w = stats.rankdata(sb)[best] / (N + 1); lam.append(math.log(w / (1 - w)))
    lam = np.array(lam)
    return dict(pbo=float((lam <= 0).mean()), rows_used=int(used), rows_dropped=int(T - used), zero_variance_cases=int(zero))

def block_bootstrap_sharpe_diff(ra, rb, block=30, draws=2000, seed=7, ppy=365):
    rng = np.random.default_rng(seed); n = len(ra); nb = math.ceil(n / block); out = np.empty(draws)
    for d in range(draws):
        st = rng.integers(0, n - block + 1, nb); idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:n]
        out[d] = (sharpe_pp(ra[idx]) - sharpe_pp(rb[idx])) * math.sqrt(ppy)
    return [float(x) for x in np.nanpercentile(out, [5, 50, 95])]

# ---------------------------------------------------------------- shuffled timing (A01)
def null_binary(target, rng):
    """Same in spells and same out spells, in a random order, still alternating. Keeps the number of trades,
    the time held and the state at both ends."""
    t = np.asarray(target, float); cutp = np.flatnonzero(np.diff(t) != 0) + 1
    starts = np.r_[0, cutp]; lens = np.diff(np.r_[starts, len(t)]); vals = t[starts]
    new = lens.copy()
    for v in (0.0, 1.0):
        m = vals == v
        if m.sum() > 1: new[m] = rng.permutation(lens[m])
    return np.repeat(vals, new)

def null_circular(target, rng, min_shift=30):
    """The rule's whole sequence of target weights, started at a random point and wrapped around. Used for
    fractional rules, where spells are not well defined."""
    n = len(target); k = int(rng.integers(min_shift, n - min_shift)); return np.roll(np.nan_to_num(target, nan=0.0), k)

# ---------------------------------------------------------------- break-even cost (A08)
GRID = (0, 5, 10, 20, 40, 80, 160, 320, 640, 1280, 2560)
def breakeven(f):
    """f(cost_bps) > 0 while the rule is still ahead. Returns the first cost where it stops being ahead.
    status: 'below_at_zero' (never ahead), 'bracketed', or 'above_cap' (still ahead at the largest cost tried)."""
    vals = [f(c) for c in GRID]
    if not vals[0] > 0: return dict(bps=0.0, status="below_at_zero", crossings=0)
    signs = [v > 0 for v in vals]; crossings = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])
    if all(signs): return dict(bps=float(GRID[-1]), status="above_cap", crossings=0)
    i = signs.index(False); lo, hi = float(GRID[i - 1]), float(GRID[i])
    for _ in range(30):
        mid = (lo + hi) / 2
        if f(mid) > 0: lo = mid
        else: hi = mid
    return dict(bps=(lo + hi) / 2, status="bracketed", crossings=crossings)

# ---------------------------------------------------------------- pass marks
def five_marks(held_rule, held_hold, be, cost, dsr, pbo, shuffle_pct, extra_m1=None):
    """Returns the five marks. A value that could not be worked out (nan) fails its mark."""
    ok = lambda x: x is not None and np.isfinite(x)
    m1 = ok(held_rule["sharpe"]) and ok(held_hold["sharpe"]) and held_rule["sharpe"] > held_hold["sharpe"] and abs(held_rule["maxdd"]) <= th("replay_max_drop_ratio_vs_hold") * abs(held_hold["maxdd"])
    if extra_m1 is not None: m1 = m1 and bool(extra_m1)
    m2 = be["status"] == "above_cap" or be["bps"] >= th("backtest_min_breakeven_cost_multiple") * cost
    m3 = ok(dsr) and dsr > th("replay_min_deflated_sharpe")
    m4 = ok(pbo) and pbo < th("backtest_max_pbo")
    m5 = ok(shuffle_pct) and shuffle_pct > th("replay_min_shuffle_percentile")
    return dict(m1=bool(m1), m2=bool(m2), m3=bool(m3), m4=bool(m4), m5=bool(m5), passed=bool(m1 and m2 and m3 and m4 and m5))
