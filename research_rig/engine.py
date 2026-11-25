"""Research rig engine. Daily or hourly bars, long or flat, one asset per sleeve.
Not the product. Signals use bars up to and including t. Fills happen at the open of t+1."""
import numpy as np, pandas as pd, math
from scipy import stats

def simulate(opens, closes, target, cost_bps, band=0.10, start_cash=1.0):
    """opens, closes: arrays. target[t]: desired weight in [0,1] decided at close of t.
    Returns equity marked at each close, weight held at each close, traded notional per bar."""
    n=len(closes); eq=np.empty(n); wt=np.empty(n); traded=np.zeros(n)
    cash=start_cash; units=0.0; c=cost_bps/1e4
    for t in range(n):
        if t>0:
            tw=target[t-1]
            if not np.isnan(tw):
                o=opens[t]; e=cash+units*o; cur=(units*o)/e if e>0 else 0.0
                full_switch = (tw==0.0 and cur>0) or (tw>0 and cur==0.0)
                if full_switch or abs(tw-cur)>band:
                    # choose new units so that after paying cost the weight equals tw
                    # buy: spend x dollars, get x/o units, pay x*c. sell: sell x dollars, receive x*(1-c)
                    want=tw*e
                    have=units*o
                    if want>have:
                        x=(want-have)/(1+tw*c)      # dollars of coin bought
                        x=min(x, cash/(1+c))
                        units+=x/o; cash-=x*(1+c); traded[t]=x
                    else:
                        x=(have-want)/(1-tw*c) if tw>0 else have
                        x=min(x,have)
                        units-=x/o; cash+=x*(1-c); traded[t]=x
        eq[t]=cash+units*closes[t]; wt[t]=units*closes[t]/eq[t] if eq[t]>0 else 0.0
    return eq, wt, traded

def metrics(eq, ppy=365):
    r=eq[1:]/eq[:-1]-1; n=len(r)
    years=n/ppy
    cagr=(eq[-1]/eq[0])**(1/years)-1 if eq[-1]>0 else -1
    vol=r.std(ddof=1)*math.sqrt(ppy)
    sr=r.mean()/r.std(ddof=1)*math.sqrt(ppy) if r.std(ddof=1)>0 else 0.0
    peak=np.maximum.accumulate(eq); mdd=(eq/peak-1).min()
    return dict(cagr=cagr,vol=vol,sharpe=sr,maxdd=mdd,total=eq[-1]/eq[0]-1,n=n)

def sharpe_per_period(r):
    s=r.std(ddof=1); return r.mean()/s if s>0 else 0.0

def deflated_sharpe(r, n_trials, sr_trials_std):
    """Bailey and Lopez de Prado deflated Sharpe ratio. r: per-period returns of the chosen rule.
    sr_trials_std: standard deviation of per-period Sharpe ratios across all trials."""
    T=len(r); sr=sharpe_per_period(r); g3=stats.skew(r); g4=stats.kurtosis(r,fisher=False)
    em=0.5772156649
    sr0=sr_trials_std*((1-em)*stats.norm.ppf(1-1/n_trials)+em*stats.norm.ppf(1-1/(n_trials*math.e)))
    den=math.sqrt(max(1e-12,1-g3*sr+(g4-1)/4*sr*sr))
    return float(stats.norm.cdf((sr-sr0)*math.sqrt(T-1)/den)), sr0

def pbo_cscv(R, S=16):
    """Probability of backtest overfitting by combinatorially symmetric cross-validation.
    R: T x N matrix of per-period returns of N rules."""
    from itertools import combinations
    T,N=R.shape; blocks=np.array_split(np.arange(T),S); lam=[]
    for comb in combinations(range(S),S//2):
        ins=np.concatenate([blocks[i] for i in comb]); oos=np.concatenate([blocks[i] for i in range(S) if i not in comb])
        a=R[ins]; b=R[oos]
        sa=a.mean(0)/a.std(0,ddof=1); sb=b.mean(0)/b.std(0,ddof=1)
        best=np.argmax(sa); rank=stats.rankdata(sb)[best]; w=rank/(N+1); lam.append(math.log(w/(1-w)))
    lam=np.array(lam); return float((lam<=0).mean())

def block_bootstrap_sharpe_diff(ra, rb, block=30, draws=2000, seed=7, ppy=365):
    rng=np.random.default_rng(seed); n=len(ra); nb=math.ceil(n/block); out=np.empty(draws)
    for d in range(draws):
        st=rng.integers(0,n-block+1,nb); idx=(st[:,None]+np.arange(block)[None,:]).ravel()[:n]
        a=ra[idx]; b=rb[idx]
        out[d]=(sharpe_per_period(a)-sharpe_per_period(b))*math.sqrt(ppy)
    return np.percentile(out,[5,50,95])

def shuffle_spells(target, rng):
    """Keep the rule's own in and out spells, put them in random order."""
    t=np.nan_to_num(target,nan=0.0); spells=[]; s=0
    for i in range(1,len(t)+1):
        if i==len(t) or t[i]!=t[s]:
            spells.append(t[s:i]); s=i
    order=rng.permutation(len(spells)); return np.concatenate([spells[i] for i in order])
