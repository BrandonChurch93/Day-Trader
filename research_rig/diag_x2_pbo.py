"""Diagnostic written AFTER seeing cross-check X2 (not pre-registered). Question: did mark 4 change because of
Kraken's prices, or because Kraken's bitcoin history starts 16 months later? Writes diag_x2_pbo.json."""
import numpy as np, pandas as pd, json
import common_01 as c1
from engine import *
from rules import RULES
bit=c1.load
def kload(a):
    d=pd.read_csv(f"data/krakenfull_{a}.csv",parse_dates=["date"]).set_index("date"); return d[d.index<="2026-11-24"]
out={}
for src,ld in [("Bitstamp",bit),("Kraken",kload)]:
    for start in ["2013-01-01","2014-05-01"]:
        if src=="Kraken" and start=="2013-01-01": continue
        c1.load=ld; c1.START={"BTCUSD":start,"ETHUSD":"2018-03-05"}
        for v,fee in c1.VENUES.items():
            c=fee+c1.SLIP; M=np.column_stack([c1.rets(c1.run("BTCUSD",r,c)[0]) for r in RULES])
            sh={r:float(metrics(c1.run("BTCUSD",r,c)[0].values)["sharpe"]) for r in RULES}
            out[f"{src}|{start}|{v}"]={"pbo":float(pbo_cscv(M,16)),"sharpe_all":sh,"bh_sharpe":float(metrics(c1.bh("BTCUSD",c).values)["sharpe"])}
json.dump(out,open("diag_x2_pbo.json","w"),indent=1)
for k,v in out.items(): print(k, round(v["pbo"],3), "bh",round(v["bh_sharpe"],2), {r:round(s,2) for r,s in v["sharpe_all"].items()})
