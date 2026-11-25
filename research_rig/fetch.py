"""Research rig data fetch. Public keyless endpoints only. Usage: python3 fetch.py crypto | kraken | hourly. Writes CSV files to data/, which is not stored in the repo."""
import urllib.request, json, time, os, csv, datetime, sys
def get(u, tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=30) as r: return r.read()
        except Exception as e:
            err=e; time.sleep(2)
    raise err
os.makedirs("data",exist_ok=True)
def bitstamp(pair, start, step=86400):
    rows={}; t=start; now=int(time.time())
    while t<now:
        d=json.loads(get(f"https://www.bitstamp.net/api/v2/ohlc/{pair}/?step={step}&limit=1000&start={t}"))["data"]["ohlc"]
        for x in d: rows[int(x["timestamp"])]=(x["open"],x["high"],x["low"],x["close"],x["volume"])
        last=max([int(x["timestamp"]) for x in d]) if d else t
        t=max(last+step, t+1000*step) if not d else last+step
        time.sleep(0.15)
    return rows
# Coinbase removed 2026-11-25: its market data terms limit use of its data, and its daily candle endpoint returned a wrong bar for 2026-11-13.
# Yahoo removed 2026-11-25: its terms bar automated collection without permission (docs/research/10_raw/stock_history_data.md).
def save(name, rows, cols):
    with open(f"data/{name}.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["date"]+cols)
        for ts in sorted(rows): w.writerow([datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")]+list(rows[ts]))
    print(name,len(rows),datetime.datetime.utcfromtimestamp(min(rows)).date(),datetime.datetime.utcfromtimestamp(max(rows)).date(),flush=True)
C=["open","high","low","close","volume"]
what=sys.argv[1]
if what=="crypto":
    save("bitstamp_BTCUSD",bitstamp("btcusd",1313625600),C)
    save("bitstamp_ETHUSD",bitstamp("ethusd",1502841600),C)
if what=="kraken":
    for pair,name in [("XBTUSD","BTCUSD"),("ETHUSD","ETHUSD")]:
        d=json.loads(get(f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval=1440"))["result"]; d=[v for k,v in d.items() if k!="last"][0]
        save("kraken_"+name,{int(x[0]):(x[1],x[2],x[3],x[4],x[6]) for x in d},C)
if what=="hourly":
    for pair in ["btcusd","ethusd"]:
        rows=bitstamp(pair,1502841600 if pair=="ethusd" else 1356998400,3600)
        with open(f"data/bitstamp_{pair.upper()}_1h.csv","w",newline="") as f:
            w=csv.writer(f); w.writerow(["ts"]+C)
            for ts in sorted(rows): w.writerow([ts]+list(rows[ts]))
        print(pair,len(rows),flush=True)
