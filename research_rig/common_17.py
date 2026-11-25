"""Pure Replay 17 engine. No file/network I/O."""
from bisect import bisect_left
from dataclasses import dataclass
import random

import numpy as np

try:
    from . import common_13 as C, common_16 as M
except ImportError:
    import common_13 as C, common_16 as M

H = M.H


@dataclass(frozen=True)
class Grid:
    # Include the terminal open, exclude bars from successor identities.
    trades: tuple
    risk: tuple
    signals: tuple
    payments: tuple
    preceding_payment: int
    preceding_close: float | None
    gap: bool
    dry: tuple = ()


@dataclass(frozen=True)
class Part:
    # At each phase, cumulative closed-trade net cash factor minus one;
    # also cumulative price, funding, fees, forced adjustment, trades, forced.
    path: np.ndarray
    flagged: bool


def prepare(tape,asset,t,end,p):
    asset = M.hourly_asset(asset)
    tape = tape.within(asset)
    hours = range(t,end+H,H)
    trade = tuple(tape.executable(x) if asset.begin<=x<asset.end else None for x in hours)
    risk = tuple((tape.mark.bars.get(x) or tape.trade.bars.get(x))
                 if asset.begin<=x<asset.end and not tape.no_volume(x) else None for x in hours)
    signals = tuple(x<min(end,asset.end) and not tape.impassable(x-(24*p["rise_days"]+1)*H,x)
                    and C.dip_signal(tape.trade,asset,x,p) for x in hours)
    dry = tuple(asset.begin<=x<asset.end and tape.no_volume(x) for x in hours)
    payments = tuple(tape.funding.get(x) if asset.begin<=x<asset.end and not dead else None
                     for x,dead in zip(hours,dry))
    i = bisect_left(tape.payments,t)-1
    j = bisect_left(tape.trade.times,t)-1
    prev = None
    while j>=0 and tape.trade.times[j]>=asset.begin:
        b = tape.executable(tape.trade.times[j])
        if b is not None:
            prev = b.c
            break
        j-=1
    return Grid(trade,risk,signals,payments,
                tape.payments[i] if i>=0 and tape.payments[i]>=asset.begin else -10**12,prev,
                tape.trade.missing_hours(t,end-H,before=asset.end)>p["max_missing_hours"],dry)


def swing(grid,asset,t,end,p,fee,*,lev=1,bounce=False,charge_funding=True,trace=None):
    asset = M.hourly_asset(asset)
    last = grid.preceding_close
    last_pay = grid.preceding_payment
    fund_window = p["live_funding_lookback_hours"]*H
    max_hold = p["max_hold_hours"]*H
    take,stop = p["take_pct"]/100,p["stop_pct"]/100
    forced_multiple = 1+p["forced_close_rise_pct"]/100
    # side=-1 short, +1 bounce long, 0 flat.
    side,entry,entered,notional,accrued = 0,0.,0,0.,0.
    total = np.zeros(7)
    path = np.zeros((2*len(grid.trades),7))
    pending,retire_at = None,None
    flagged = grid.gap

    def note(hour,event,px):
        if trace is not None:
            trace.append((hour,event,px,float(1+total[0])))

    def open_at(hour,px,direction):
        nonlocal side,entry,entered,notional,accrued
        side,entry,entered = direction,px,hour
        notional = float(1+total[0])*lev
        accrued = 0.
        note(hour,"sell_short" if side<0 else "buy_bounce",px)

    def close_at(hour,px,reason):
        nonlocal side,pending
        pnl = side*notional*(px/entry-1)
        fees = fee*notional*(1+px/entry)
        raw = pnl+accrued-fees
        wiped = reason=="forced"
        adjust = -(1+total[0])-raw if wiped else 0.
        total[:] += (raw+adjust,pnl,accrued,fees,adjust,1,wiped)
        if wiped:
            total[0] = -1
        note(hour,reason,px)
        side,pending = 0,None

    def forced_price(risk,only_open):
        if not side or lev<=1 or risk is None:
            return None
        if side<0:
            bound = entry*forced_multiple
            if risk.o>=bound or (not only_open and risk.h>=bound):
                return max(risk.o,bound)
        else:
            bound = entry*(2-forced_multiple)
            low = risk.l if risk.l is not None else min(risk.o,risk.c)
            if risk.o<=bound or (not only_open and low<=bound):
                return min(risk.o,bound)
        return None

    for i,hour in enumerate(range(t,end+H,H)):
        bar,risk,rate = grid.trades[i],grid.risk[i],grid.payments[i]
        if grid.dry and grid.dry[i]:
            if side:
                close_at(hour,last,"volume_stop")
            # The existing stale-contract convention retires this weekly
            # part. It can be considered again on a later Monday.
            flagged = True
            path[2*i:] = total
            break
        if rate is not None:
            last_pay = hour
            if side and charge_funding:
                if last is None:
                    raise ValueError("funding with no completed trade close")
                accrued -= side*notional*rate*last/entry
                note(hour,"funding",last)
        terminal = hour>=end or hour>=asset.end or hour==retire_at
        force_px = forced_price(risk,True)
        if force_px is not None:
            close_at(hour,force_px,"forced")
        elif terminal and side:
            if bar is None:
                close_at(hour,last,"last_close")
                flagged = True
            else:
                close_at(hour,bar.o,"funding_timeout" if hour==retire_at else "week_end")
        elif side and pending:
            if bar is None:
                flagged = True
            else:
                flip = bounce and side<0 and pending=="target" and retire_at is None
                close_at(hour,bar.o,pending)
                if flip and 1+total[0]>0:
                    open_at(hour,bar.o,1)
        elif not side and not terminal and 1+total[0]>0 and (pending or grid.signals[i]):
            if bar is None:
                pending,flagged = "entry",True
            else:
                pending = None
                open_at(hour,bar.o,-1)
        path[2*i] = total
        if terminal:
            path[2*i+1:] = total
            break
        force_px = forced_price(risk,False)
        if force_px is not None:
            close_at(hour,force_px,"forced")
        if bar is not None:
            last = bar.c
        if side and pending is None:
            if bar is not None and side*(bar.c/entry-1)>=take-1e-12:
                pending = "target"
            elif bar is not None and side*(bar.c/entry-1)<=-stop+1e-12:
                pending = "stop"
            elif hour+H-entered>=max_hold:
                pending = "time"
        if hour-last_pay>=fund_window and retire_at is None:
            # Check after this hour's recorded payment, never search a later hour.
            # Even an idle part stops taking signals once the contract goes stale.
            retire_at = hour+H
        path[2*i+1] = total
    return Part(path,flagged)


def hold_factor(sleeves,denom,fee,charge_funding):
    """The held shorts use the Plan 16 hourly whole-account equity check."""
    if not sleeves:
        return 1.
    path = np.sum([r.path for r in sleeves],axis=0)
    total = 1+(path[:,0]+path[:,1]*charge_funding-path[:,2]*fee)/denom
    return float(total[-1]) if np.all(total>0) else 0.


def group_pnl(parts,ix,group_size):
    """Return each group's weekly realized components, ending at first ruin."""
    if not parts:
        return np.zeros((len(ix),7))
    cube = np.stack([o.path for o in parts]+[np.zeros_like(parts[0].path)])
    final = cube[ix,-1].sum(axis=1)
    bottoms = cube[:,:,0].min(axis=1)
    for i in np.flatnonzero(bottoms[ix].sum(axis=1)<=-group_size):
        combined = cube[ix[i]].sum(axis=0)
        failed = np.flatnonzero(combined[:,0]<=-group_size)
        if len(failed):
            final[i] = combined[failed[0]]
    final[:,:5] /= group_size
    return final


class Accounts:
    def __init__(self,n):
        self.value = np.ones(n)
        self.stats = np.zeros((n,6))
        self.flagged_parts = np.zeros(n,dtype=int)
        self.idle_parts = np.zeros(n,dtype=int)
        self.live_parts = np.zeros(n,dtype=int)
        self.scheduled_parts = 0

    def add(self,parts,indices,n,carried):
        pnl = group_pnl(parts,indices,n)
        prior = self.value.copy()
        self.value *= np.maximum(0,1+pnl[:,0])
        self.stats[:,:4] += prior[:,None]*pnl[:,1:5]
        self.stats[:,4:] += (prior[:,None]>0)*pnl[:,5:]
        self.scheduled_parts += n
        missing = indices==len(parts)
        self.idle_parts += missing.sum(axis=1)
        self.live_parts += (~missing).sum(axis=1)
        if carried:
            # Weeks with no live contract are not flagged, even when carried.
            self.flagged_parts += (~missing).sum(axis=1)
        else:
            flagged = np.array([v.flagged for v in parts]+[False])
            self.flagged_parts += flagged[indices].sum(axis=1)

    def row(self):
        price,funding,fees,forced_adjust,trades,forced = self.stats[0]
        return {"end":float(self.value[0]),"price":float(price),"funding":float(funding),
                "fees":float(fees),"forced_adjustment":float(forced_adjust),
                "trades":int(trades),"forced":int(forced),"idle_parts":int(self.idle_parts[0]),
                "flagged_parts":int(self.flagged_parts[0]),
                "live_parts":int(self.live_parts[0]),
                "flag_share_pct":float(self.flagged_parts[0]*100/max(1,self.live_parts[0])),
                "ruined":bool(self.value[0]==0),"random_ends":self.value[1:].tolist()}


def judge(years,p,level):
    valid,positive,both,rising = [],[],[],[]
    for year,row in years.items():
        y = row["held"]
        r = y["swing"][level]
        if r["trades"]<p["min_trades_per_year"] or r["flag_share_pct"]>p["max_flagged_share_pct"]:
            continue
        valid.append(year)
        if r["end"]>1:
            positive.append(year)
            if r["end"]>y["hot_hold"][level]:
                both.append(year)
                if y["spot_all"]>1:
                    rising.append(year)
    marks = [len(positive)>=p["min_years_above"],len(both)>=p["min_years_above"],
             len(rising)>=p["min_rising_years"]]
    return {"eligible":valid,"positive":positive,"above_hold":both,"rising":rising,
            "marks":marks,"finding":"supported" if all(marks) else "not supported"}


def shown_us_short(roster,spot,tapes,p,identity):
    """One descriptive 1x Rule S series at judged costs, identical rank clock."""
    n = p["hot_n"]
    fee = p["cost_bps_per_side"]/10000
    snap = {"kept":roster,"known_at":-10**12}
    years = {}
    for year,start,last in C.year_windows(p):
        account = Accounts(1)
        rankable = hot_slots = live_slots = 0
        for t in range(start,last,C.WEEK):
            end = min(t+C.WEEK,last)
            spot_ids,futures_ids = M.week_allowlist(identity,t)
            _,ranked,_ = M.spot_universe([snap],spot,t,p,spot_ids)
            hot = ranked[:n]
            rankable += len(ranked)
            hot_slots += len(hot)
            hot_ids = {a.coin for a in hot}
            pool,_ = M.market_pool({"kept":[r for r in roster if r["id"] in hot_ids]},
                                   tapes,t,end,p,futures_ids)
            idx = {a.coin:i for i,a in enumerate(pool)}
            slots = [idx.get(a.coin,len(pool)) for a in hot]
            slots += [len(pool)]*(n-len(slots))
            live_slots += len(pool)
            parts = [swing(prepare(tapes[a.pair],a,t,end,p),a,t,end,p,fee) for a in pool]
            account.add(parts,np.array([slots],dtype=int),n,False)
        years[str(year)] = account.row() | {"rankable_coin_weeks":rankable,
                                           "hot_slots":hot_slots,"live_hot_slots":live_slots}
    return years


def replay(snapshots,spot,tapes,p,p16,p13,identity=None,us_roster=None):
    n = p["hot_n"]
    params = p13|p16|p
    levels = dict(zip(("low","judged","high"),sorted([p["cost_bps_per_side"],*p["other_costs_bps"]])))
    levels["no_cost_no_funding"] = 0
    rng = {s:random.Random(p["seed"]) for s in snapshots}
    years = {}
    for year,start,last in C.year_windows(params):
        year_result = {}
        for sample,snaps in snapshots.items():
            normal = {k:Accounts(1+p["random_draws"] if k=="judged" else 1) for k in levels}
            extras = {k:Accounts(1) for k in ("levered","bounce")}
            holds = {k:1. for k in levels}
            all_short = 1.
            spot_book = C.Account()
            diagnostics = []
            for t in range(start,last,C.WEEK):
                spot_ids,futures_ids = M.week_allowlist(identity,t)
                end = min(t+C.WEEK,last)
                _,ranked,carried = M.spot_universe(snaps,spot,t,params,spot_ids)
                hot = ranked[:n]
                selected = [hot]+[rng[sample].sample(sorted(ranked),min(n,len(ranked)))
                                  for _ in range(p["random_draws"])]
                screens = {"monday_live":set(),"file_gate_excluded":set()}
                pool,missing = M.market_pool(M.snapshot_at(snaps,t),tapes,t,end,params,futures_ids,screens)
                indices = {a.coin:i for i,a in enumerate(pool)}
                groups = np.full((len(selected),n),len(pool),dtype=int)
                for j,s in enumerate(selected):
                    for i,a in enumerate(s):
                        groups[j,i] = indices.get(a.coin,len(pool))
                grids = [prepare(tapes[a.pair],a,t,end,params) for a in pool]
                diagnostics.append({"t":t,"rankable":len(ranked),"live":len(pool),
                                    "hot_live":int(np.sum(groups[0]!=len(pool))),
                                    "missing_funding_files":len(missing),"carried":carried,
                                    **{k:len(v) for k,v in screens.items()}})
                longs = [M.spot_outcome(spot[a.pair],a,t,end,p13["cost_bps_per_side"]/10000,params)
                         for a in ranked]
                spot_book.advance(t,max(1,len(longs)),longs,carried)
                weekly = [M.short_week(tapes[a.pair],a,t,end,params) for a in pool]
                for level,bps in levels.items():
                    fee = bps/10000
                    pay = level!="no_cost_no_funding"
                    parts = [swing(g,a,t,end,params,fee,charge_funding=pay)
                             for g,a in zip(grids,pool)]
                    normal[level].add(parts,groups if level=="judged" else groups[:1],n,carried)
                    holds[level] *= hold_factor([weekly[i] for i in groups[0] if i<len(pool)],n,fee,pay)
                    if level=="judged" and weekly:
                        all_short *= hold_factor(weekly,len(weekly),fee,pay)
                fee = p["cost_bps_per_side"]/10000
                for key,kw in (("levered",{"lev":p["shown_leverage"]}),("bounce",{"bounce":True})):
                    parts = [swing(g,a,t,end,params,fee,**kw) for g,a in zip(grids,pool)]
                    extras[key].add(parts,groups[:1],n,carried)
            year_result[sample] = {"swing":{k:a.row() for k,a in normal.items()},
                                   "shown":{k:a.row() for k,a in extras.items()},
                                   "hot_hold":holds,"all_short":all_short,
                                   "spot_all":1+spot_book.finish()["gain"],"weeks":diagnostics}
        years[str(year)] = year_result
    judgments = {k:judge(years,p,k) for k in ("judged","low","no_cost_no_funding")}
    judged = judgments["judged"]["marks"]
    result = {"years":years,"judgment":judgments,
            "failed_on_timing":judged[0] and not judged[1],
            "failed_on_rising":judged[1] and not judged[2],
            "failed_on_costs":all(judgments["no_cost_no_funding"]["marks"]) and
            not all(judgments["judged"]["marks"])}
    if us_roster is not None:
        result["shown_us_shortable"] = shown_us_short(us_roster,spot,tapes,params,identity)
    return result
