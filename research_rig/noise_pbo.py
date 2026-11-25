"""How noisy is the overfitting estimate (mark 4) when no rule has any edge? Made-up data only. Not a test of any rule.
Written after the audit (finding B03). Each sample: daily returns for N rules over 4,592 days, drawn at random with a shared part (the stated correlation) and no edge. Writes noise_pbo.json. Usage: python3 noise_pbo.py"""
import json, numpy as np, rig2 as R
def one(rng, n_rules, T, rho):
    common = rng.normal(0, 0.03, T); X = np.sqrt(rho) * common[:, None] + np.sqrt(1 - rho) * rng.normal(0, 0.03, (T, n_rules))
    return R.pbo_cscv(X, 16, "earliest")
N_SAMPLES = 100
def case(args):
    n_rules, rho = args; rng = np.random.default_rng(7); v = [one(rng, n_rules, 4592, rho) for _ in range(N_SAMPLES)]; o = {}
    for key in ("pbo", "pbo_strict", "pbo_half"):
        a = np.array([z[key] for z in v])
        o[key] = dict(mean=float(a.mean()), p05=float(np.quantile(a, .05)), p50=float(np.median(a)), p95=float(np.quantile(a, .95)), min=float(a.min()), max=float(a.max()), share_below_bar=float((a < R.th("backtest_max_pbo")).mean()))
    print(n_rules, rho, o["pbo"], flush=True); return f"{n_rules} rules, correlation {rho}", o
if __name__ == "__main__":
    import multiprocessing as mp
    with mp.get_context("fork").Pool(4) as pool: res = pool.map(case, [(9, 0.0), (9, 0.8), (5, 0.8), (8, 0.8)])
    json.dump({"samples": N_SAMPLES, "blocks": 16, "seed": 7, "days": 4592, "max_pbo": R.th("backtest_max_pbo"), "cases": dict(res)}, open("noise_pbo.json", "w"), indent=1)
