"""Read-only replay 04 probes. No runner main or output writer is called."""
from pathlib import Path
import inspect
import sys
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research_rig'))
import run_04 as run
import rig2
import basket


def future_replay(raw, base):
    for cut in ('2023-01-01','2026-04-01'):
        rng=np.random.default_rng(7)
        modified={}
        for p,bars in raw.items():
            b=bars.copy(); rows=b.index>=cut
            shocks=rng.lognormal(0,1,(sum(rows),2))
            b.loc[rows,'open']*=shocks[:,0]
            b.loc[rows,'close']*=shocks[:,0]
            b.loc[rows,'dv']*=shocks[:,1]
            # Remove alternate existing future prints but leave each original last timestamp;
            # the separate synthetic test isolates the effect of changing that final timestamp.
            after=np.flatnonzero(rows & b.traded.to_numpy())[::2]
            after=after[after!=len(b)-1]
            b.iloc[after,b.columns.get_loc('traded')]=False
            b.iloc[after,b.columns.get_loc('open')]=np.nan
            b.iloc[after,b.columns.get_loc('dv')]=0.
            b.iloc[after,b.columns.get_loc('close')]=np.nan
            b.close=b.close.ffill()
            modified[p]=b
        basket.load_raw=lambda:modified
        D=run.setup()
        common=sorted(set(base['cn'])|set(D['cn']))
        assert D['start']==base['start']
        pre=D['dates']<pd.Timestamp(cut)
        upto={k:m for k,m in base['months'].items() if k<=cut}
        expected={k:m for k,m in D['months'].items() if k<=cut}
        print('FUTURE',cut,'months checked including cut',len(upto),'exact',upto==expected)
        for name in run.RULES:
            records=[]
            for data in (base,D):
                run.D=data
                ss=pd.DataFrame(run.target(name)[pre],columns=data['cn']).reindex(columns=common,fill_value=0)
                e=run.run(name,run.costs(2),detail=False)[0]['eq'][pre]
                records.append((ss.to_numpy(),e))
            print('FUTURE',cut,name,'target max diff',np.max(np.abs(records[0][0]-records[1][0])),
                  'equity max diff',np.max(np.abs(records[0][1]-records[1][1])))
    run.D=base


def extend_terminal(raw,base):
    cut=pd.Timestamp('2026-04-01'); modified={}
    for p,b in raw.items():
        if b.index[-1]>=cut:
            modified[p]=b; continue
        x=b.reindex(pd.date_range(b.index[0],cut)); x['close']=x.close.ffill(); x['dv']=x.dv.fillna(0.)
        x['traded']=x.traded.eq(True); x.loc[cut,'open']=x.loc[cut,'close']; x.loc[cut,'dv']=1e5; x.loc[cut,'traded']=True
        modified[p]=x
    basket.load_raw=lambda:modified
    D=run.setup(); pre=D['dates']<cut; names=sorted(set(base['cn'])|set(D['cn']))
    print('EXTEND added future trades',sum(b.index[-1]<cut for b in raw.values()))
    for n in run.RULES:
        results=[]
        for ds in (base,D):
            run.D=ds
            results.append((pd.DataFrame(run.target(n)[pre],columns=ds['cn'],index=D['dates'][pre]).reindex(columns=names,fill_value=0),
                            run.run(n,run.costs(2),detail=False)[0]['eq'][pre]))
        diff=(results[0][0]!=results[1][0]); dates=diff.index[diff.any(axis=1)]; pieces=diff.columns[diff.any(axis=0)]
        print('EXTEND',n,'target differences',int(diff.to_numpy().sum()),'days',dates[:4].tolist(),'pairs',list(pieces),
              'max eq diff',np.max(np.abs(results[0][1]-results[1][1])))
    run.D=base


def counterexamples():
    # In both datasets the prefix has a position and the same missing third-day bar.
    # Only a future fourth-day trade changes whether the second day's close is paid out.
    o=np.array([[100.],[100.],[np.nan],[np.nan]])
    c=o.copy(); w=np.ones_like(o)
    dead=basket.sim_batch(o,c,w,[5],[0.125],last_day=[1],delist_haircut=.5,detail=True)
    o[-1,0]=110.; c[-1,0]=110.
    live=basket.sim_batch(o,c,w,[5],[0.125],last_day=[10**9],delist_haircut=.5,detail=True)
    print('LAST-DAY FUTURE LEAK',dead['eq'],live['eq'],dead['ev'])
    # At monthly reset, new buy cannot be funded until the unavailable old asset sells.
    p=np.array([[100.,100.],[100.,100.],[np.nan,100.],[100.,100.],[100.,100.]])
    w=np.array([[1.,0.],[0.,1.],[0.,1.],[0.,1.],[0.,1.]])
    o=basket.sim_batch(p,p,w,[7,27],[0,0],rebal=[False,True,True,False,False],detail=True)
    print('PENDING BENCHMARK LOSS',o['wt'].tolist(),o['traded'].tolist(),o['waits'])


def calendar(base):
    run.D=base
    for venue in ('Binance.US','Kraken $10k tier'):
        z,c=run.run('K5',run.costs(rig2.VENUES[venue])); d=base['dates']; m=(z['traded']>rig2.DUST*np.r_[1.,z['eq'][:-1]][:,None]).any(1)
        print('K5 SIDES',venue,int(m.sum()),'outside Thu',int((m & (d.weekday!=3) & (d!=base['start'])).sum()),
              'by weekday',pd.Series(d[m].day_name()).value_counts().to_dict())
        b=run.cols_of('K5'); e=basket.sim_batch(base['O'][:,b],base['C'][:,b],run.target('K5')[:,b],run.costs(rig2.VENUES[venue])[b],
                          [0],rebal=np.asarray((d.weekday==3)|(d==base['start'])),detail=True)
        print('K5 THU EXACT',venue,run.slice_metrics(e['eq'])['held'],run.slice_metrics(e['eq'])['all'],'sides',e['sides'])
    for n in run.RULES:
        z,c=run.run(n,run.costs(2)); print('WAITS',n,z['waits'],'forced',z['ev'])
    for j,m in enumerate(base['months'].values()):
        date=pd.Timestamp(list(base['months'])[j])
        stale=[p for p in m['top20'] if pd.Timestamp(base['last_date'][p])<date]
        if stale: print('SELECTED AFTER LAST PRINT',date,stale)


def exact_target_sensitivity(base):
    # Diagnostic only: same target and pre-fee band decisions, but target weights
    # apply to after-cost equity on all names that are ordered on that day.
    scope={"np":np}; src=inspect.getsource(basket.sim_batch)
    src=src.replace('            s = need & (tw < cur)', '''            budget = e.copy()
            if need.any():
                lo = np.zeros(B); hi = e.copy()
                for _ in range(42):
                    mid=(lo+hi)/2
                    cc=(np.where(need,np.abs(tw*mid[:,None]-val),0)*k).sum(1)
                    too_big=mid+cc>e
                    hi=np.where(too_big,mid,hi); lo=np.where(too_big,lo,mid)
                budget=(lo+hi)/2
            s = need & (tw * budget[:,None] < val)''')
    src=src.replace('val - tw * e[:, None]', 'val - tw * budget[:, None]')
    src=src.replace('bm = need & (tw > cur)','bm = need & (tw * budget[:,None] > val)')
    src=src.replace('tw * e[:, None] - val', 'tw * budget[:, None] - val')
    exec(src,scope)
    run.D=base; orig=run.sim
    for v in ('Binance.US', 'Kraken $10k tier'):
        k=run.costs(rig2.VENUES[v]); out=[]
        for sim in (orig,scope['sim_batch']):
            run.sim=sim; dat={n:run.run(n,k,detail=False)[0]['eq'] for n in run.RULES}
            rets={n:rig2.rets(e) for n,e in dat.items()}
            sd=np.std([rig2.sharpe_pp(r) for r in rets.values()],ddof=1)
            print('SIZING',v,sim is orig,'held/DSR',[(n,run.slice_metrics(dat[n])['held']['sharpe'],rig2.deflated_sharpe(rets[n],49,sd)[0]) for n in run.RULES])
    run.sim=orig


def weekly_preserving_k5(base):
    run.D=base; cv=run.costs(2); name='K5'; t=run.target(name); source=t[:,base['btc']]; n=len(source)
    assert n%7==0
    r=rig2.sharpe_pp(rig2.rets(run.run(name,cv,detail=False)[0]['eq']))
    rng=np.random.default_rng(7); wins=0
    for _ in range(20):
        shifts=rng.integers(5,n//7-4,50)*7
        w=np.tile(t,(50,1,1)); w[:,:,base['btc']]=np.array([np.roll(source,k) for k in shifts]); rr=run.run(name,cv,detail=False,W=w)[0]['eq']
        wins+=sum(rig2.sharpe_pp(rig2.rets(x))<r for x in rr)
    print('K5 same-weekday shuffled percentile, Binance.US:',wins/1000)


if __name__=='__main__':
    raw=basket.load_raw(); basket.load_raw=lambda:raw
    base=run.setup(); run.D=base
    counterexamples(); calendar(base); future_replay(raw,base); exact_target_sensitivity(base)
    extend_terminal(raw,base); weekly_preserving_k5(base)
