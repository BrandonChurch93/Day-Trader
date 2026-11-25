import json
o=json.load(open("results_01.json"))
V=["Binance.US","Alpaca","Kraken $10k tier","Kraken entry","Coinbase entry"]; COST={"Binance.US":7,"Alpaca":30,"Kraken $10k tier":43,"Kraken entry":85,"Coinbase entry":95}
for a,A in o["assets"].items():
    print("\n=====",a,"PBO",round(A["pbo"],3))
    for sl in ["all","dev","held","post"]:
        b=A["bh"]["Alpaca"][sl]; print(f"  [{sl}] BH@Alpaca cagr {b['cagr']*100:7.1f}% vol {b['vol']*100:5.1f}% SR {b['sharpe']:.2f} mdd {b['maxdd']*100:6.1f}% total {b['total']*100:8.1f}%")
        for r,rr in A["rules"].items():
            m=rr["venues"]["Alpaca"][sl]; mb=rr["venues"]["Binance.US"][sl]; mc=rr["venues"]["Coinbase entry"][sl]
            print(f"     {r:5s} cagr {m['cagr']*100:7.1f}% SR {m['sharpe']:.2f} mdd {m['maxdd']*100:6.1f}% tot {m['total']*100:8.1f}% exp {m['exposure']:.2f} trades {m['trades']:4d} turn/y {m['turnover_py']:5.1f} | SR bin {mb['sharpe']:.2f} cb {mc['sharpe']:.2f}")
    print("  rule  BEvsBH  BEzero  DSR   shuffle%  shufMed  bootSRdiff[5,50,95]")
    for r,rr in A["rules"].items():
        print(f"  {r:5s} {rr['be_vs_bh_bps']:6.0f} {rr['be_zero_bps']:6.0f}  {rr['dsr']:.3f}  {rr['shuffle_pct']:.3f}   {rr['shuffle_median_sharpe']:.2f}   {[round(x,2) for x in rr['boot_sharpe_diff_vs_bh']]}")
print("\n===== PORT")
for r in ["P1","P2"]:
    print(r,"DSR",round(o["port"][r]["dsr"],3))
    for v in ["Binance.US","Alpaca","Coinbase entry"]:
        for sl in ["all","dev","held","post"]:
            x=o["port"][r][v][sl]; print(f"   {v:15s} [{sl:4s}] rule cagr {x['rule']['cagr']*100:6.1f}% SR {x['rule']['sharpe']:.2f} mdd {x['rule']['maxdd']*100:6.1f}% | BH cagr {x['bh']['cagr']*100:6.1f}% SR {x['bh']['sharpe']:.2f} mdd {x['bh']['maxdd']*100:6.1f}%")
print("trial SR std per period",o["trial_sharpe_std_per_period"])
