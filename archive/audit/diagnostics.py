"""Read-only checks of the rig, separate from independently written replay."""
from pathlib import Path
from itertools import combinations
import json
import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import rankdata

RIG = Path(__file__).resolve().parents[2] / 'research_rig'
sys.dont_write_bytecode = True
sys.path.insert(0, str(RIG))
os.chdir(RIG)
import common_01 as d1
import common_03 as h3
import engine as eng


def check_data():
    for a in ['BTCUSD','ETHUSD']:
        for name, freq in [(f'bitstamp_{a}', 'D'), (f'bitstamp_{a}_1h', 'h'),
                           (f'kraken_{a}', 'D'), (f'krakenfull_{a}', 'D')]:
            p = pd.read_csv(f'data/{name}.csv')
            d = (pd.DatetimeIndex(pd.to_datetime(p.ts, unit='s', utc=True)) if 'ts' in p else
                 pd.DatetimeIndex(pd.to_datetime(p.date, utc=True)))
            end = pd.Timestamp('2026-11-24' + (' 23:00' if freq == 'h' else ''), tz='UTC')
            active = d<=end
            p, d = p[active], d[active]
            missing = pd.date_range(d.min(), end, freq=freq).difference(d)
            print('DATA', name, len(d), d[0], d[-1], 'missing', len(missing),
                  'dups', d.duplicated().sum(), 'sorted', d.is_monotonic_increasing,
                  'zero', p.volume.eq(0).sum(), 'NAs', p.isna().to_numpy().sum())
        bars = h3.load_h(a)
        mask = bars.index>=h3.start_date(a)
        T = h3.rules_h(bars,a)
        print('hour missing after start', a, bars.missing[mask].sum())
        for name, tg in {**T, 'BH':np.ones(len(bars))}.items():
            o,c = bars.open[mask].values,bars.close[mask].values
            eq,held=h3.sim_fast(o,c,tg[mask],30)
            fill=np.diff(held,prepend=0)!=0
            k=bars.loc[mask]
            print('FILL', a,name,'first EOD',eq[23], 'last held',held[-1],
                  'zero',np.sum(fill & k.volume.eq(0)), 'missing',np.sum(fill & k.missing))


def check_trade_dust():
    for n in ['P1','S50']:
        eq, _, trade, _ = d1.run('BTCUSD', n, 30)
        small = trade[(trade>0) & ((trade/eq.shift(1))<1e-12)]
        print('DUST',n,small.to_dict(), 'real count', (trade>0).sum()-len(small))


def pbo(m, how):
    rem = len(m) % 16
    if how=='drop first' and rem:
        m = m[rem:]
    if how=='drop last' and rem:
        m = m[:-rem]
    blocks = np.array_split(m,16,axis=0)
    size = np.array([len(i) for i in blocks])
    sums = np.stack([i.sum(0) for i in blocks])
    squares = np.stack([(i**2).sum(0) for i in blocks])
    combos = np.array(list(combinations(np.arange(16),8)))
    def sh(n,s,s2):
        return (s/n) / (((s2-s*s/n)/(n-1))**.5)
    ns=size[combos].sum(1)[:,None]; s=sums[combos].sum(1); s2=squares[combos].sum(1)
    a = sh(ns,s,s2)
    b = sh(len(m)-ns,m.sum(0)-s,(m**2).sum(0)-s2)
    ranks = rankdata(b,axis=1)[np.arange(len(a)),a.argmax(1)]
    return np.mean(ranks/(m.shape[1]+1)<=.5)


def check_pbo():
    d1.load = lambda a: pd.read_csv(f'data/krakenfull_{a}.csv',index_col='date',parse_dates=True)
    d1.START['BTCUSD']='2014-05-01'
    for v,fee in d1.VENUES.items():
        m=np.column_stack([d1.rets(d1.run('BTCUSD',n,fee+5)[0]) for n in d1.RULES])
        print('PBO',v,'n',len(m),*(f'{k}: {pbo(m,k):.10g}' for k in ['unequal','drop first','drop last']))
    # Constant-return columns are plausible in a quiet/short sample.
    m = np.column_stack([np.zeros(320), np.random.default_rng(7).normal(.1,1,320)])
    print('PBO constant column rig (default SciPy NaN handling)', eng.pbo_cscv(m))


def spell_labels(t):
    return int(np.count_nonzero(np.diff(np.r_[0,t]) != 0))


def shuffle_test(t, o, c, sites, price, label):
    base=np.nan_to_num(t,nan=0.)
    active=base[:-1]
    blocks = np.split(active,np.where(np.diff(active))[0]+1)
    order = np.array([x[0] for x in blocks],dtype=int)
    slots0,slots1 = [np.flatnonzero(order==x) for x in (0,1)]
    rnd=np.random.default_rng(7); a_rng=np.random.default_rng(7)
    real_sides=spell_labels(active)
    def sharpe(tg):
        e=h3.sim_fast(o,c,tg,price)[0][sites]
        return eng.sharpe_per_period(e[1:]/e[:-1]-1)
    real=sharpe(t)
    both=[]
    for k in range(1000):
        legacy=h3.shuffle_fast(base,rnd)
        ar = np.arange(len(order)); ar[slots0]=a_rng.permutation(slots0); ar[slots1]=a_rng.permutation(slots1)
        corrected=np.concatenate([*(blocks[i] for i in ar),base[-1:]])
        both.append((spell_labels(legacy[:-1]),np.count_nonzero(legacy[:-1]),
                     sharpe(legacy)<real,sharpe(corrected)<real))
    val=np.array(both)
    print('SHUF',label,'real sides and held',real_sides,np.count_nonzero(active),
          'legacy sides min mean max',np.min(val[:,0]),np.mean(val[:,0]),np.max(val[:,0]),
          'legacy held min/max',np.min(val[:,1]),np.max(val[:,1]),
          'legacy and conditioned percentiles',*np.mean(val[:,2:],0))


def check_shuffle():
    for price in [7,30]:
        d=d1.load('BTCUSD'); t=d1.RULES['S50'](d.close).loc['2013-01-01':].values
        d=d.loc['2013-01-01':]; shuffle_test(t,d.open.values,d.close.values,slice(None),price,f'S50 {price}')
        h=h3.load_h('BTCUSD'); m=h.index>=h3.start_date('BTCUSD'); t=h3.rules_h(h,'BTCUSD')['H1'][m]; d=h[m]
        shuffle_test(t,d.open.values,d.close.values,d.index.hour==23,price,f'H1 {price}')


if __name__=='__main__':
    check_data()
    check_trade_dust()
    check_shuffle()
    check_pbo()
