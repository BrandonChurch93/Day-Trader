import json,urllib.request,time,datetime
def get(u):
    req=urllib.request.Request(u,headers={"User-Agent":"research-script"})
    return json.load(urllib.request.urlopen(req,timeout=20))
def cost(levels,notional,mid):
    # levels: list of (price,size) best first; returns avg price slippage vs mid in bps for buying notional
    rem=notional;spent=0;qty=0
    for p,s in levels:
        take=min(rem,p*s);spent+=take;qty+=take/p;rem-=take
        if rem<=1e-9:break
    if rem>1e-9:return None
    avg=spent/qty;return abs(avg-mid)/mid*1e4
def books():
    out={}
    for sym,cb,kr,gm,bu,al in [("BTC","BTC-USD","XBTUSD","btcusd","BTCUSD","BTC/USD"),("ETH","ETH-USD","ETHUSD","ethusd","ETHUSD","ETH/USD")]:
        try:
            d=get(f"https://api.exchange.coinbase.com/products/{cb}/book?level=2")
            out[("Coinbase",sym)]=([(float(a[0]),float(a[1])) for a in d["bids"]],[(float(a[0]),float(a[1])) for a in d["asks"]])
        except Exception as e: print("cb",e)
        try:
            d=get(f"https://api.kraken.com/0/public/Depth?pair={kr}&count=200");k=list(d["result"].values())[0]
            out[("Kraken",sym)]=([(float(a[0]),float(a[1])) for a in k["bids"]],[(float(a[0]),float(a[1])) for a in k["asks"]])
        except Exception as e: print("kr",e)
        try:
            d=get(f"https://api.gemini.com/v1/book/{gm}?limit_bids=200&limit_asks=200")
            out[("Gemini",sym)]=([(float(a["price"]),float(a["amount"])) for a in d["bids"]],[(float(a["price"]),float(a["amount"])) for a in d["asks"]])
        except Exception as e: print("gm",e)
        try:
            d=get(f"https://api.binance.us/api/v3/depth?symbol={bu}&limit=500")
            out[("Binance.US",sym)]=([(float(a[0]),float(a[1])) for a in d["bids"]],[(float(a[0]),float(a[1])) for a in d["asks"]])
        except Exception as e: print("bu",e)
        try:
            d=get(f"https://data.alpaca.markets/v1beta3/crypto/us/latest/orderbooks?symbols={al}")["orderbooks"][al]
            out[("Alpaca",sym)]=([(a["p"],a["s"]) for a in d["b"]],[(a["p"],a["s"]) for a in d["a"]])
        except Exception as e: print("al",e)
    return out
import sys
rounds=int(sys.argv[1]) if len(sys.argv)>1 else 1
res={}
for r in range(rounds):
    ts=datetime.datetime.utcnow().isoformat()[:19]
    for k,(b,a) in books().items():
        b=sorted(b,key=lambda x:-x[0]);a=sorted(a,key=lambda x:x[0])
        mid=(b[0][0]+a[0][0])/2;sp=(a[0][0]-b[0][0])/mid*1e4
        row=[sp]+[cost(a,n,mid) for n in (1000,10000,100000)]
        res.setdefault(k,[]).append(row)
    if r<rounds-1: time.sleep(20)
print("UTC end",datetime.datetime.utcnow().isoformat()[:19],"rounds",rounds)
print("venue sym quoted_spread_bps(median,max) buy-side cost vs mid bps for $1k,$10k,$100k (median)")
import statistics as st
for k,v in sorted(res.items()):
    col=lambda i:[x[i] for x in v if x[i] is not None]
    med=lambda i:round(st.median(col(i)),3) if col(i) else None
    print(k[0],k[1],med(0),round(max(col(0)),3),med(1),med(2),med(3))
