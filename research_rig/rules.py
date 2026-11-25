import numpy as np, pandas as pd
def sma_above(c,L): return (c>c.rolling(L).mean()).astype(float).where(c.rolling(L).mean().notna())
def p1(c): return sum(sma_above(c,L) for L in (20,50,100,200))/4
def p2(c, tv=0.40, ppy=365):
    rv=c.pct_change().rolling(30).std(ddof=1)*np.sqrt(ppy)
    return p1(c)*np.minimum(1.0, tv/rv)
def donchian(c, n_in, n_out):
    hi=c.rolling(n_in).max(); lo=c.rolling(n_out).min(); pos=np.full(len(c),np.nan); cur=0.0
    cv=c.values; hv=hi.values; lv=lo.values
    for i in range(len(c)):
        if np.isnan(hv[i]): continue
        if cur==0.0 and cv[i]>=hv[i]: cur=1.0
        elif cur==1.0 and cv[i]<=lv[i]: cur=0.0
        pos[i]=cur
    return pd.Series(pos,index=c.index)
def mom(c,L): return (c>c.shift(L)).astype(float).where(c.shift(L).notna())
RULES={"P1":p1,"P2":p2,"S50":lambda c:sma_above(c,50),"S100":lambda c:sma_above(c,100),"S200":lambda c:sma_above(c,200),
       "D20":lambda c:donchian(c,20,10),"D55":lambda c:donchian(c,55,20),"M30":lambda c:mom(c,30),"M90":lambda c:mom(c,90)}
