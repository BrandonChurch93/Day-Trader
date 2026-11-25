import json, time, urllib.request, sys, datetime
def get(u):
    req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=10) as r: return json.loads(r.read())
def binus(sym):
    d=get(f"https://api.binance.us/api/v3/depth?symbol={sym}&limit=50"); return [(float(p),float(q)) for p,q in d["bids"]],[(float(p),float(q)) for p,q in d["asks"]]
def kraken(pair):
    d=get(f"https://api.kraken.com/0/public/Depth?pair={pair}&count=50")["result"]; d=list(d.values())[0]
    return [(float(x[0]),float(x[1])) for x in d["bids"]],[(float(x[0]),float(x[1])) for x in d["asks"]]
def coinbase(p):
    d=get(f"https://api.exchange.coinbase.com/products/{p}/book?level=2")
    return [(float(x[0]),float(x[1])) for x in d["bids"][:200]],[(float(x[0]),float(x[1])) for x in d["asks"][:200]]
def gemini(s):
    d=get(f"https://api.gemini.com/v1/book/{s}?limit_bids=50&limit_asks=50")
    return [(float(x["price"]),float(x["amount"])) for x in d["bids"]],[(float(x["price"]),float(x["amount"])) for x in d["asks"]]
V={"binance_us":(binus,{"BTC":"BTCUSD","ETH":"ETHUSD","BTC_USDT":"BTCUSDT"}),"kraken":(kraken,{"BTC":"XBTUSD","ETH":"ETHUSD"}),"coinbase":(coinbase,{"BTC":"BTC-USD","ETH":"ETH-USD"}),"gemini":(gemini,{"BTC":"btcusd","ETH":"ethusd"})}
def cost(levels, usd):
    # average fill price for a market order of `usd` notional
    rem=usd; qty=0
    for p,q in levels:
        take=min(rem,p*q); qty+=take/p; rem-=take
        if rem<=1e-9: break
    return None if rem>1e-6 else usd/qty
out=open("snapshots.jsonl","a")
for i in range(int(sys.argv[1])):
    for v,(fn,syms) in V.items():
        for a,s in syms.items():
            try:
                b,k=fn(s); bb,ba=b[0][0],k[0][0]; mid=(bb+ba)/2
                rec={"t":datetime.datetime.utcnow().isoformat(),"venue":v,"asset":a,"bid":bb,"ask":ba,"spread_bps":(ba-bb)/mid*1e4,
                     "bid_usd_top":b[0][0]*b[0][1],"ask_usd_top":k[0][0]*k[0][1]}
                for n in (100,1000,10000):
                    pb=cost(k,n); ps=cost(b,n)
                    rec[f"rt_bps_{n}"]= None if (pb is None or ps is None) else (pb-ps)/mid*1e4
                out.write(json.dumps(rec)+"\n"); out.flush()
            except Exception as e:
                out.write(json.dumps({"t":datetime.datetime.utcnow().isoformat(),"venue":v,"asset":a,"error":str(e)[:200]})+"\n"); out.flush()
    time.sleep(float(sys.argv[2]))
