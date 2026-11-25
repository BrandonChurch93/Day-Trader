"""Rebuild Replay 04 K1 and K4 from raw Kraken days without importing the rig."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = Path('/home/user/workspace/rig/kraken/daily')
END = '2026-09-30'
BIG = ('XBTUSD', 'ETHUSD')
REAL_OTHER_QUOTES = ('ETHPYUSD','XBTPYUSD','XRPRLUSD')


def bars_for(p):
    bars = pd.read_csv(p, header=None, usecols=[0,1,4,5], names=['day','o','c','volume'])
    bars.index = pd.to_datetime(bars.pop('day'), unit='s')
    return bars.loc[:END]


def rebuild_membership(include_merl=False, strict_more=False, drop_gold=False):
    by_pair = {}
    for p in sorted(DATA.glob('*USD_1440.csv')):
        pair = p.name.removesuffix('_1440.csv')
        if pair.endswith(('PYUSD','RLUSD')) and not (pair == 'MERLUSD' and include_merl):
            continue
        if drop_gold and pair in ('PAXGUSD','XAUTUSD'):
            continue
        x = bars_for(p)
        if len(x) > 1:
            by_pair[pair] = x
    quoted = pd.DataFrame({p: x.c for p,x in by_pair.items()}).asfreq('D').loc[:END]
    v = pd.DataFrame({p: x.c*x.volume for p,x in by_pair.items()}).reindex(quoted.index).fillna(0)
    r = quoted.ffill().pct_change(fill_method=None)
    first = np.array([x.index[0] for x in by_pair.values()], dtype='datetime64[D]')
    book = {}
    for day in quoted.index[quoted.index.day==1]:
        before = slice(day-pd.Timedelta(days=90),day-pd.Timedelta(days=1))
        hist = r.loc[before]
        if len(hist)<90:
            continue
        ok = ((np.datetime64(day,'D')-first).astype(int)>=200) & (quoted.loc[before].count()>=80)
        good = hist.loc[:, ok]
        good = good.loc[:, good.std()*365**.5>=.2]
        dv = v.loc[before,good.columns].median().sort_values(ascending=False,kind='stable')
        z = good[dv.index].to_numpy(copy=True); z -= z.mean(0); z /= np.sqrt((z*z).sum(0))
        corr = z.T @ z
        ahead = np.tril(np.ones(corr.shape,bool),-1)
        if strict_more:
            vals = dv.to_numpy(); ahead &= vals[None,:] > vals[:,None]
        keep = dv.index[~((corr>.98)&ahead).any(1)].tolist()
        if book or len(keep)>=10:
            book[day] = keep
    return by_pair,book


def independent_trade(name, price, book, fee, exact=False):
    use = sorted({p for pairs in book.values() for p in pairs[:10]}) if name in ('K1','HOLD_BASKET') else list(BIG[:1] if name=='HOLD_BTC' else BIG)
    first = min(book)
    days = pd.date_range(first-pd.Timedelta(days=1), END)
    closes,opens,trend = {},{},{}
    for p in use:
        s = price[p].asfreq('D'); c = s.c.ffill(); opens[p]=s.o.reindex(days); closes[p]=c.reindex(days).ffill()
        w = sum((c>c.rolling(n).mean()).astype(float) for n in (20,50,100,200))/4
        trend[p] = w.where(c.rolling(200).count().eq(200), 0).reindex(days).fillna(0)
    cash, holding, equity = 1., dict.fromkeys(use,0.),[1.]
    slot = .1 if name in ('K1','HOLD_BASKET') else .5 if name=='K4' else 1.
    k = {p:(fee+(5 if p in BIG else 25))/10000 for p in use}
    prev = days[0]; waits=set(); weighted_error=[]; worst_cash=1.; cutoff='2026-07-01'
    for day in days[1:]:
        m = book[day.replace(day=1)][:10] if name in ('K1','HOLD_BASKET') else use
        if name=='HOLD_BASKET' and day.day==1: waits=set(use)
        if name=='HOLD_BTC' and day==first: waits=set(use)
        mark = {p:opens[p][day] if pd.notna(opens[p][day]) else closes[p][prev] for p in use}
        pos = {p:holding[p]*mark[p] if holding[p] else 0. for p in use}
        value = cash+sum(pos.values())
        target = {p:(slot*(1 if name.startswith('HOLD') else trend[p][prev]) if p in m else 0.) for p in use}
        unlocked = [p for p in use if pd.notna(opens[p][day])]
        todo = [p for p in unlocked if (p in waits and target[p] != pos[p]/value if name.startswith('HOLD') else
                abs(target[p]-pos[p]/value)>slot/8 or (p not in m and holding[p]>0))]
        if name.startswith('HOLD'): waits.difference_update(unlocked)
        budget = value
        if exact and todo:
            # Solve net equity after paying fees on target deltas, holding the chosen band decisions fixed.
            low,high=0.,value
            for _ in range(48):
                x=(low+high)/2
                if x+sum(k[p]*abs(target[p]*x-pos[p]) for p in todo)>value: high=x
                else: low=x
            budget=(low+high)/2
        for p in todo:
            sale = pos[p]-target[p]*budget
            if sale>0:
                cash += sale*(1-k[p]); holding[p] = target[p]*budget/mark[p]
        buys = {p:max(0.,target[p]*budget-pos[p]) for p in todo}
        spend = sum(x*(1+k[p]) for p,x in buys.items())
        scale = min(1.,cash/spend) if spend else 1.
        for p,x in buys.items():
            holding[p] += x*scale/mark[p]
        cash = max(0.,cash-spend*scale)
        if name=='HOLD_BASKET' and day.day==1 and all(p in unlocked for p in m):
            opval=cash+sum(holding[p]*mark[p] for p in use if holding[p])
            err=max(abs(holding[p]*mark[p]/opval-.1) for p in m)
            weighted_error.append((day,err,cash/opval))
        equity.append(cash+sum(holding[p]*closes[p][day] for p in use if holding[p]))
        worst_cash=min(worst_cash,cash)
        prev=day
    if weighted_error:
        print(name, 'largest complete-month open weight error', max(weighted_error, key=lambda q:q[1]))
    return pd.Series(equity,index=days)


def measures(e):
    ret = e.pct_change().iloc[1:]
    return np.array([(e.iloc[-1]/e.iloc[0])**(365/len(ret))-1,
                     ret.mean()/ret.std()*365**.5, (e/e.cummax()-1).min()])


def main():
    stored = json.loads((ROOT/'research_rig/results_04.json').read_text())
    raw, book = rebuild_membership()
    print('start',min(book),'months',len(book),'top10 membership differences',sum(v[:10]!=stored['membership'][str(d.date())]['top10'] for d,v in book.items()))
    print('top20 membership differences',sum(v[:20]!=stored['membership'][str(d.date())]['top20'] for d,v in book.items()))
    for name in ('K1','K4','HOLD_BTC','HOLD_BASKET'):
        eq = independent_trade(name,raw,book,2)
        got=measures(eq.loc['2022-12-31':'2026-06-30'])
        row = stored['venues']['Binance.US']['bench' if name.startswith('HOLD') else 'rules'][name]['slices']['held']
        expected=np.array([row[k] for k in ['cagr','sharpe','maxdd']])
        print(name, 'independent', got, 'saved', expected, 'delta',got-expected)
        eq2=independent_trade(name,raw,book,2,exact=True)
        print(name, 'after-fee target sensitivity, held',measures(eq2.loc['2022-12-31':'2026-06-30']), 'whole',measures(eq2))
    _, more = rebuild_membership(include_merl=True, strict_more=True)
    print('After restoring MERLUSD and requiring strictly more median dollar volume:',
          'top10 differences',sum(v[:10]!=book[d][:10] for d,v in more.items()),
          'top20 differences',sum(v[:20]!=book[d][:20] for d,v in more.items()),
          'MERL in top 20',sum('MERLUSD' in v[:20] for v in more.values()))


if __name__=='__main__': main()
