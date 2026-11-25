"""Print the markdown tables used in docs/research/12. Every number comes from results_01*.json and passmarks_01.json."""
import json
o=json.load(open("results_01.json")); p=json.load(open("passmarks_01.json")); c=json.load(open("results_01c.json")); d=json.load(open("results_01d.json"))
V=["Binance.US","Alpaca","Kraken $10k tier","Kraken entry","Coinbase entry"]; COST={"Binance.US":7,"Alpaca":30,"Kraken $10k tier":43,"Kraken entry":85,"Coinbase entry":95}
RN=["P1","P2","S50","S100","S200","D20","D55","M30","M90"]
pc=lambda x: f"{x*100:.1f}%"
print("### T1 whole sample at Alpaca cost")
for a in ["BTCUSD","ETHUSD"]:
    A=o["assets"][a]; b=A["bh"]["Alpaca"]["all"]
    print(f"\n{a}\n\n| Rule | Growth a year | Sharpe | Largest drop | Time invested | Trades | Turnover a year | Break-even cost per side vs holding (bps) | Sharpe difference vs holding, 90% range |\n|---|---|---|---|---|---|---|---|---|")
    print(f"| Hold | {pc(b['cagr'])} | {b['sharpe']:.2f} | {pc(b['maxdd'])} | 100% | 1 | | | |")
    for r in RN:
        rr=A["rules"][r]; m=rr["venues"]["Alpaca"]["all"]; bs=rr["boot_sharpe_diff_vs_bh"]
        print(f"| {r} | {pc(m['cagr'])} | {m['sharpe']:.2f} | {pc(m['maxdd'])} | {m['exposure']*100:.0f}% | {m['trades']} | {m['turnover_py']:.1f}x | {rr['be_vs_bh_bps']:.0f} | {bs[0]:+.2f} to {bs[2]:+.2f} |")
print("\n### T2 held-back slice Sharpe by venue (P1, P2, hold)")
for a in ["BTCUSD","ETHUSD"]:
    A=o["assets"][a]
    print(f"\n{a}\n\n| Venue | Cost per side (bps) | Hold Sharpe | Hold drop | P1 Sharpe | P1 growth a year | P1 drop | P2 Sharpe | P2 growth a year | P2 drop | Hold growth a year |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for v in V:
        b=A["bh"][v]["held"]; m1=A["rules"]["P1"]["venues"][v]["held"]; m2=A["rules"]["P2"]["venues"][v]["held"]
        print(f"| {v} | {COST[v]} | {b['sharpe']:.2f} | {pc(b['maxdd'])} | {m1['sharpe']:.2f} | {pc(m1['cagr'])} | {pc(m1['maxdd'])} | {m2['sharpe']:.2f} | {pc(m2['cagr'])} | {pc(m2['maxdd'])} | {pc(b['cagr'])} |")
print("\n### T3 pass marks")
vs=[v for v in V if any(k.startswith(v+"|") for k in p)]
for a in ["BTCUSD","ETHUSD"]:
    print(f"\n{a}. Each cell: marks 1 to 5 in order (Y passed, n failed), then the verdict.\n\n| Rule | "+" | ".join(vs)+" |\n|---|"+"---|"*len(vs))
    for r in RN:
        cells=[]
        for v in vs:
            x=p[f"{v}|{a}|{r}"]; cells.append("".join("Y" if x[f"m{i}"] else "n" for i in range(1,6))+(" PASS" if x["passed"] else " fail"))
        print(f"| {r} | "+" | ".join(cells)+" |")
    print("\n| Venue | Rules that pass all five | Overfitting probability |\n|---|---|---|")
    for v in vs:
        ps=[r for r in RN if p[f"{v}|{a}|{r}"]["passed"]]; print(f"| {v} | {', '.join(ps) if ps else 'none'} | {p[f'{v}|{a}|P1']['pbo']:.2f} |")
print("\n### T3b detail P1 P2")
print("| Venue | Coin | Rule | Held-back Sharpe, rule vs hold | Drop ratio | Break-even vs needed (bps) | Deflated Sharpe | Overfitting probability | Shuffle percentile | Verdict |\n|---|---|---|---|---|---|---|---|---|---|")
for v in vs:
    for a in ["BTCUSD","ETHUSD"]:
        for r in ["P1","P2"]:
            x=p[f"{v}|{a}|{r}"]; print(f"| {v} | {a[:3]} | {r} | {x['held_sharpe']:.2f} vs {x['bh_held_sharpe']:.2f} | {x['dd_ratio']:.2f} | {x['be_vs_bh']:.0f} vs {x['need_be']:.0f} | {x['dsr']:.3f} | {x['pbo']:.2f} | {x['shuffle']:.3f} | {'PASS' if x['passed'] else 'fail'} |")
print("\n### T4 portfolio")
print("| Rule | Venue | Slice | Rule growth a year | Rule Sharpe | Rule drop | Hold growth a year | Hold Sharpe | Hold drop |\n|---|---|---|---|---|---|---|---|---|")
for r in ["P1","P2"]:
    for v in ["Binance.US","Alpaca","Coinbase entry"]:
        for sl,nm in [("all","Whole sample"),("held","Held back"),("post","After cutoff")]:
            x=o["port"][r][v][sl]; print(f"| {r} | {v} | {nm} | {pc(x['rule']['cagr'])} | {x['rule']['sharpe']:.2f} | {pc(x['rule']['maxdd'])} | {pc(x['bh']['cagr'])} | {x['bh']['sharpe']:.2f} | {pc(x['bh']['maxdd'])} |")
print("Portfolio deflated Sharpe: P1",round(o["port"]["P1"]["dsr"],3),"P2",round(o["port"]["P2"]["dsr"],3))
print("\n### T5 years")
for a in ["BTCUSD","ETHUSD"]:
    print(f"\n{a}\n\n| Year | Hold | Hold worst drop | P1 | P1 worst drop | P2 | P2 worst drop |\n|---|---|---|---|---|---|---|")
    for y,row in d[a]["years"].items(): print(f"| {y} | {pc(row['hold'])} | {pc(row['hold_dd'])} | {pc(row['P1'])} | {pc(row['P1_dd'])} | {pc(row['P2'])} | {pc(row['P2_dd'])} |")
print("\n### T6 fill delay (Sharpe: base / one hour late / one day late)")
for a in ["BTCUSD","ETHUSD"]:
    S=c["S1"][a]; print(f"\n{a}: median move in the first hour {S['abs_move_first_hour_bps_median']:.0f} bps, 90th percentile {S['abs_move_first_hour_bps_p90']:.0f} bps, days {S['days']}, hour missing {S['hour_missing_days']}\n\n| Rule | Alpaca, whole sample | Alpaca, held back | Binance.US, whole sample | Binance.US, held back |\n|---|---|---|---|---|")
    for r in RN:
        v=S["rules"][r]; f=lambda vn,sl: " / ".join(f"{v[vn+'|'+k][sl]['sharpe']:.2f}" for k in ["base","hour_late","day_late"])
        print(f"| {r} | {f('Alpaca','all')} | {f('Alpaca','held')} | {f('Binance.US','all')} | {f('Binance.US','held')} |")
print("\n### T7 cross-check")
print("| Coin | Days | Median gap between closes (bps) | Largest gap (bps) | Rule | Bitstamp: return, Sharpe, drop, trades | Kraken: return, Sharpe, drop, trades | Days the target differed | Hold return same dates |\n|---|---|---|---|---|---|---|---|---|")
for a in ["BTCUSD","ETHUSD"]:
    X=c["X1"][a]
    for r in ["P1","P2"]:
        b=X["rules"][r]["bitstamp"]; k=X["rules"][r]["kraken"]
        print(f"| {a[:3]} | {X['days']} | {X['close_diff_bps_median']:.1f} | {X['close_diff_bps_max']:.1f} | {r} | {pc(b['total'])}, {b['sharpe']:.2f}, {pc(b['maxdd'])}, {b['trades']} | {pc(k['total'])}, {k['sharpe']:.2f}, {pc(k['maxdd'])}, {k['trades']} | {X['rules'][r]['days_target_differs']} | {pc(d[a]['hold_last720']['total'])} |")
print("\n### post slice")
for a in ["BTCUSD","ETHUSD"]:
    A=o["assets"][a]; print(a,"hold",pc(A["bh"]["Alpaca"]["post"]["total"]),{r:pc(A["rules"][r]["venues"]["Alpaca"]["post"]["total"]) for r in RN})
