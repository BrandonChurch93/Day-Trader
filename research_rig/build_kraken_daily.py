"""Builds data/krakenfull_{BTCUSD,ETHUSD}.csv from Kraken's published archive files (written by fetch_kraken_archive.py into data/kraken, or KRAKEN_DIR) plus the public daily bars already in data/kraken_*.csv."""
import pandas as pd, os, json
K=os.environ.get("KRAKEN_DIR",os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kraken")); out={}
for pair,a in [("XBTUSD","BTCUSD"),("ETHUSD","ETHUSD")]:
    d=pd.read_csv(f"{K}/full_{pair}_1440.csv",header=None,names=["ts","open","high","low","close","volume","trades"])
    d.index=pd.to_datetime(d.ts,unit="s"); d=d.drop(columns=["ts","trades"]); d=d[d.index<="2026-09-30"]
    api=pd.read_csv(f"data/kraken_{a}.csv",parse_dates=["date"]).set_index("date"); api=api[(api.index>="2026-10-01")&(api.index<="2026-11-24")]
    ov=pd.read_csv(f"data/kraken_{a}.csv",parse_dates=["date"]).set_index("date"); j=d.join(ov,rsuffix="_api",how="inner")
    out[a+"_archive_vs_api_close_max_bps"]=float(((j.close/j.close_api-1).abs().max())*1e4); out[a+"_overlap_days"]=int(len(j))
    d=pd.concat([d,api[["open","high","low","close","volume"]]])
    full=pd.date_range(d.index[0],"2026-11-24",freq="D"); miss=~full.isin(d.index); d=d.reindex(full)
    d["close"]=d.close.ffill()
    for c in ["open","high","low"]: d[c]=d[c].fillna(d.close)
    d["volume"]=d.volume.fillna(0.0); d.index.name="date"; d.to_csv(f"data/krakenfull_{a}.csv")
    out[a+"_first"]=str(d.index[0].date()); out[a+"_days"]=int(len(d)); out[a+"_missing_days_filled"]=int(miss.sum()); out[a+"_missing_after_test_start"]=int(miss[full>=("2014-05-01" if a=="BTCUSD" else "2016-03-01")].sum())
    b=pd.read_csv(f"data/bitstamp_{a}.csv",parse_dates=["date"]).set_index("date"); j=d.join(b,rsuffix="_b",how="inner"); j=j[j.index>=("2014-05-01" if a=="BTCUSD" else "2018-03-05")]
    g=(j.close/j.close_b-1).abs()*1e4; out[a+"_close_gap_vs_bitstamp_bps"]=dict(median=float(g.median()),p99=float(g.quantile(0.99)),max=float(g.max()),max_date=str(g.idxmax().date()),days=int(len(g)))
json.dump(out,open("kraken_daily_build.json","w"),indent=1); print(json.dumps(out,indent=1))
