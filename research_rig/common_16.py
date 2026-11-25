"""Pure Replay 16 engine. The caller, not this module, opens verified archives."""
from bisect import bisect_left, bisect_right
from collections import defaultdict
from copy import copy
from dataclasses import dataclass, replace
import random

import numpy as np

try:
    from . import common_13 as C
    from . import fetch_16 as F
    from .identity_asof_16_17 import week_allowlist, asset_floor, bound_asset
except ImportError:
    import common_13 as C
    import fetch_16 as F
    from identity_asof_16_17 import week_allowlist, asset_floor, bound_asset

H = C.HOUR
MAJORS = (C.Asset(1,"BTCUSDT"),C.Asset(1027,"ETHUSDT"))
LEVELS = ("low","judged","high")
UNBOUNDED = 10**12


def hour_bounds(begin,end):
    """Keep only complete UTC bars wholly inside the identity segment."""
    return ((begin+H-1)//H*H if begin>-UNBOUNDED else begin,
            end//H*H if end<UNBOUNDED else end)


def hourly_asset(asset):
    begin,end = hour_bounds(asset.begin,asset.end)
    return asset if (begin,end)==(asset.begin,asset.end) else replace(asset,begin=begin,end=end)


@dataclass(frozen=True)
class FBar:
    o: float
    h: float
    c: float
    l: float | None = None
    v: float = 1.0


@dataclass
class Tape:
    trade: C.Series
    mark: C.Series
    funding: dict
    covered: tuple

    def __post_init__(self):
        self.dead = zero_runs(self.trade)
        self.dead_starts = [a for a,_ in self.dead]
        self.payments = sorted(t for t in self.funding if not self.no_volume(t))
        self.scoped = {}

    def within(self,asset):
        span = (asset.begin,asset.end)
        if span==(-UNBOUNDED,UNBOUNDED):
            return self
        if span not in self.scoped:
            scoped = copy(self)
            scoped.dead = zero_runs(self.trade,*span)
            scoped.dead_starts = [a for a,_ in scoped.dead]
            scoped.payments = sorted(t for t in self.funding
                                      if span[0]<=t<span[1] and not scoped.no_volume(t))
            self.scoped[span] = scoped
        return self.scoped[span]

    def no_volume(self,t):
        i = bisect_left(self.dead_starts,t+1)-1
        return i>=0 and self.dead[i][0]<=t<self.dead[i][1]

    def impassable(self,lo,hi):
        i = bisect_left(self.dead_starts,hi)-1
        return i>=0 and self.dead[i][1]>lo

    def executable(self,t):
        if self.no_volume(t):
            return None
        b = self.trade.bars.get(t)
        return b if b is not None and getattr(b,"v",1)>0 else None

    def covers(self,a,b):
        # Coverage is fixed archive/API provenance, not inferred from later
        # funding events in a path. Ranges are half-open.
        edge = a
        for lo,hi in self.covered:
            if lo <= edge < hi:
                edge = hi
            if edge > b:
                return True
        return False


def zero_runs(trade,begin=-UNBOUNDED,end=UNBOUNDED):
    timestamps = trade.times
    if not len(timestamps):
        return []
    lo,hi = bisect_left(timestamps,begin),bisect_left(timestamps,end)
    if not isinstance(trade.bars,dict):
        volumes = trade.bars.values[:,4]
        zero = lo+np.flatnonzero(volumes[lo:hi]==0)
        volume_at = volumes.__getitem__
    else:
        volume_at = lambda i:getattr(trade.bars[timestamps[i]],"v",1)
        zero = [i for i in range(lo,hi) if volume_at(i)==0]
    out = []
    j = 0
    while j<len(zero):
        i = j
        j += 1
        while j<len(zero) and timestamps[zero[j]]==timestamps[zero[j-1]]+H:
            j += 1
        if j-i>=24:
            start = int(timestamps[zero[i]])
            if out and start<out[-1][1]:
                continue
            k = zero[j-1]+1
            while k<hi and volume_at(k)==0:
                k += 1
            resume = int(timestamps[k]) if k<hi else end
            out.append((start,resume))
    return out


@dataclass(frozen=True)
class Sleeve:
    price: float
    funding: float
    turnover: float
    flagged: bool
    reason: str
    # End-of-hour marked cumulative gross components relative to entry notional.
    path: np.ndarray


def live_screens(asset,tape,t,end,p):
    asset = hourly_asset(asset)
    if tape is None or not asset.begin <= t < asset.end or t not in tape.trade.bars:
        return None
    tape = tape.within(asset)
    # Initial source presence is distinct from trading liveness. A source
    # is needed only while this identity segment is in force.
    coverage = tape.covers(t,min(end,asset.end-H))
    latest = bisect_left(tape.payments,t)-1
    observed = (not tape.no_volume(t) and getattr(tape.trade.bars[t],"v",1)>0
        and latest >= 0 and tape.payments[latest] >= max(
            asset.begin,t-p["live_funding_lookback_hours"]*H))
    return observed,coverage


def live(asset,tape,t,end,p):
    result = live_screens(asset,tape,t,end,p)
    return ((result[0],not result[1]) if result is not None
            else (False,False))


def market_pool(snapshot,tapes,t,end,p,confirmed=None,screens=None,*,legacy_file_gate=False):
    available = []
    unknown = set()
    taken = set()
    for row in snapshot["kept"] if snapshot else ():
        for asset in F.perp_segments(row):
            asset = hourly_asset(bound_asset(asset,confirmed))
            if not asset.begin <= t < asset.end or asset.pair in taken:
                continue
            if confirmed is not None and (asset.coin,asset.pair) not in confirmed:
                continue
            if screens is not None:
                measured = live_screens(asset,tapes.get(asset.pair),t,end,p)
                if measured is not None:
                    observed,covered = measured
                    if observed:
                        screens["monday_live"].add(asset.pair)
                        if not covered:
                            screens["file_gate_excluded"].add(asset.pair)
            ok,miss = live(asset,tapes.get(asset.pair),t,end,p)
            if miss:
                unknown.add(asset.pair)
            if ok and not (legacy_file_gate and miss):
                taken.add(asset.pair)
                available.append(asset)
                break
    return available,unknown


def short_week(tape,asset,start,end,p,trace=None):
    asset = hourly_asset(asset)
    if not asset.begin<=start<asset.end:
        raise ValueError("short entry outside the identity segment")
    tape = tape.within(asset)
    opening = tape.executable(start)
    if opening is None:
        raise ValueError("short entry without a positive-volume open")
    entry = opening.o
    stop = entry*(1+p["short_stop_pct"]/100)
    lookback = p["live_funding_lookback_hours"]*H
    idx = bisect_left(tape.payments,start)-1
    last_pay = tape.payments[idx] if idx >= 0 and tape.payments[idx]>=asset.begin else -10**12
    prev_trade = None
    before = bisect_left(tape.trade.times,start)-1
    while before >= 0 and tape.trade.times[before] >= asset.begin:
        prior = tape.executable(tape.trade.times[before])
        if prior is not None:
            prev_trade = prior.c
            break
        before -= 1
    funding, due = 0.0,None
    gap = tape.trade.missing_hours(start,end-H,before=asset.end) > p["max_missing_hours"]
    path = []
    loop = range(start,end+H,H)
    for t in loop:
        if tape.no_volume(t) and t<asset.end:
            price,reason,gap = prev_trade,"volume_stop",True
            break
        trade = tape.executable(t) if t < asset.end else None
        mark = tape.mark.bars.get(t) if t < asset.end else None
        risk = mark or (tape.trade.bars.get(t) if t<asset.end else None)
        # Exactly-on-entry payments are not earned. Both timed exits and
        # forced closes include the payment stamped on their exit hour.
        if start <= t < asset.end and t in tape.funding:
            last_pay = t
            if t > start:
                if prev_trade is None:
                    raise ValueError("funding event without completed trade close")
                funding += tape.funding[t]*prev_trade/entry
                if trace is not None:
                    trace.append((t,"funding",prev_trade/entry,funding))
        if t >= asset.end or t == due or t == end:
            if trade is not None:
                if risk.o >= stop:
                    price,reason = risk.o,"forced"
                else:
                    price,reason = trade.o,"timeout" if t == due else "weekly"
            else:
                price,reason,gap = prev_trade,"last_close",True
            break
        if risk is not None and (risk.o >= stop or risk.h >= stop):
            price,reason = max(risk.o,stop),"forced"
            break
        if t-last_pay >= lookback and due is None:
            due = t+H
            if trace is not None:
                trace.append((t,"queue_timeout",None,funding))
        if trade is not None:
            prev_trade = trade.c
        valuation = (risk.c if risk is not None else prev_trade) or entry
        path.append((1-valuation/entry,funding,1))
    gain = 1-price/entry
    turnover = 1+price/entry
    if trace is not None:
        trace.append((t,reason,price,funding))
    path.extend([(gain,funding,turnover)]*(len(loop)-len(path)))
    return Sleeve(gain,funding,turnover,gap,reason,np.array(path,dtype=float))


@dataclass(frozen=True)
class Long:
    filled: bool
    outcome: C.Outcome
    path: np.ndarray
    series: object = None
    asset: object = None
    entry_basis: float = 1.0

    def mark(self,t,completed_before=False):
        if self.outcome.release is not None and self.outcome.release<=t:
            return self.outcome.factor
        if self.series is None:
            return float(self.path[-1])
        before = min(t+(0 if completed_before else H),self.asset.end)
        i = bisect_left(self.series.times,before)-1
        return self.series.bars[self.series.times[i]].c/self.entry_basis


def long_week(series,asset,t,end,fee,p):
    asset = hourly_asset(asset)
    if not asset.begin<=t<asset.end or t not in series.bars:
        return Long(False,C.Outcome(1,end,()),np.ones((end-t)//H+1))
    # The sole Rule A change is the entry gate above. The position cannot
    # buy after Monday, even though its Rule A sale may be delayed.
    outcome = spot_outcome(series,asset,t,end,fee,p)
    entry = series.bars[t].o
    price = entry
    marks = []
    for hour in range(t,end+H,H):
        if outcome.release is not None and hour >= outcome.release:
            marks.append(outcome.factor)
            continue
        if hour < end and asset.begin <= hour < asset.end and hour in series.bars:
            price = series.bars[hour].c
        marks.append(price/(entry*(1+fee)))
    return Long(True,outcome,np.array(marks,dtype=float),series,asset,entry*(1+fee))


def spot_outcome(series,asset,t,end,fee,p):
    asset = hourly_asset(asset)
    outcome = C.hold_week(series,asset,t,end,fee,1,p)
    if outcome.release is None and asset.end<UNBOUNDED:
        # A known identity end retires the lot, rather than leaving an
        # unfillable pending order alive in the original account.
        i = bisect_left(series.times,asset.end)-1
        outcome = replace(outcome,release=series.times[i]+H)
    return outcome


def snapshot_at(rows,t):
    return next((s for s in reversed(rows) if s["known_at"]<=t and s["kept"]),None)


def spot_universe(rows,spot,t,p,confirmed=None):
    if confirmed is None:
        return C.weekly_universe(rows,spot,t,p)
    snap = snapshot_at(rows,t)
    last = next((s for s in reversed(rows) if s["known_at"]<=t),None)
    if not snap:
        return [],[],True
    # A confirmed-ID filter cannot change when a saved list applies, carry
    # a different list, or move the boundary of either ranked slice.
    first_rank_close = t-(24*p["rise_days"]+1)*H
    listed,ranked,allocated = [],[],set()
    for r in sorted(snap["kept"],key=lambda r:r.get("cmcRank",float("inf"))):
        for lo,hi,pair in F.spot_segments(r):
            key = (r["id"],pair)
            if key not in confirmed or not lo<=t<hi or pair in allocated:
                continue
            lo,hi = hour_bounds(max(lo,asset_floor(confirmed,*key)),hi)
            if not lo<=t<hi:
                continue
            if t-H<lo:
                continue
            allocated.add(pair)
            s = spot.get(pair)
            if s is None or t-H not in s.bars:
                continue
            a = C.Asset(r["id"],pair,lo,hi)
            listed.append(a)
            if first_rank_close>=lo and s.usable_lookback(first_rank_close,t-H,p["max_missing_hours"]):
                ranked.append((s.bars[t-H].c/s.bars[first_rank_close].c-1,a))
    ranked.sort(key=lambda x:(-x[0],x[1].coin))
    return listed,[a for _,a in ranked],snap is not last


def weight_matrix(picks,universe):
    columns = {a.coin:i for i,a in enumerate(universe)}
    w = np.zeros((len(picks),len(columns)),dtype=float)
    for i,group in enumerate(picks):
        for a in group:
            w[i,columns[a.coin]] = 1
    return w


class Book:
    def __init__(self,n):
        self.cash = np.ones(n)
        self.pending = []
        self.flags = np.zeros(n,dtype=int)
        self.funding = np.zeros(n)
        self.short_price = np.zeros(n)
        self.short_fees = np.zeros(n)
        self.forced = np.zeros(n,dtype=int)
        self.failed = np.zeros(n,dtype=bool)

    def begin(self,t):
        still = []
        for lot,basis in self.pending:
            when = lot.outcome.release
            if when is not None and when<=t:
                self.cash += basis*lot.outcome.factor
            else:
                still.append((lot,basis))
        self.pending = still
        self.cash[self.failed] = 0

    def add_pending(self,lot,basis):
        if np.any(basis):
            self.pending.append((lot,basis))

    def equity(self,t):
        pending = sum((basis*lot.mark(t,completed_before=True) for lot,basis in self.pending),0)
        return np.where(self.failed,0,self.cash+pending)

    def finish(self):
        # A delayed year-end sale belongs to its opening year even when the
        # first available same-identity open is in the following calendar year.
        released = sum((basis*lot.outcome.factor for lot,basis in self.pending),0)
        return np.where(self.failed,0,self.cash+released)


def portfolio_step(book,t,end,data,weights,hot_n,short_w,short_plans,is_b,
                   spot_fee,perp_fee,major_fee,share,flags):
    """Vectorized independent paths; delayed long proceeds stay unallocated."""
    book.begin(t)
    opening = book.cash.copy()
    equity = book.equity(t)
    active = ~book.failed
    if data:
        fills = weights @ np.array([d.filled for d in data],dtype=float)
        long_pnl = weights @ np.array([
            d.outcome.factor-1 if d.outcome.release is not None and d.outcome.release<=end
            else -1 for d in data])
        unit = np.where(active & (opening>0) & (equity>0),
                        np.minimum(equity*share/hot_n,opening*share/np.maximum(fills,1)),0)
        exposure = unit*fills/(1+spot_fee)
        gain = unit*long_pnl
    else:
        exposure = gain = unit = np.zeros(len(opening))
    forced = np.zeros(len(opening),dtype=int)
    if short_plans:
        price = short_w @ np.array([r.price for r in short_plans])
        funding = short_w @ np.array([r.funding for r in short_plans])
        turnover = short_w @ np.array([r.turnover for r in short_plans])
        fee = np.where(is_b,major_fee,perp_fee)
        debit = turnover*fee
        is_forced = np.array([r.reason=="forced" for r in short_plans],dtype=bool)
        forced = (short_w>0) @ is_forced.astype(int)
        # Only paths whose componentwise conservative floor is <= 0 need a
        # synchronized hourly check. Every long asset mark is nonnegative.
        floor = short_w @ np.array([r.path[:,0].min()+r.path[:,1].min()
                                   -max(perp_fee,major_fee)*r.path[:,2].max()
                                   for r in short_plans])
    else:
        price = funding = debit = floor = np.zeros(len(opening))
    # New equity includes the marked long notional (or sale proceeds when
    # released) and any older pending lots, including during a cash deficit.
    risk = np.flatnonzero(active & ((equity<=0) | (opening-unit*fills+exposure*floor<=0))) if data else np.flatnonzero(active & ((equity<=0) | (opening<=0)))
    if len(risk):
        hours = list(range(t,end+H,H))
        path = np.broadcast_to(opening[risk,None],(len(risk),len(hours))).copy()
        for lot,basis in book.pending:
            path += basis[risk,None]*np.array([lot.mark(x,completed_before=x==end) for x in hours])
        if data:
            path += unit[risk,None]*(weights[risk] @ np.array([d.path-1 for d in data]))
        if short_plans:
            sleeve_paths = np.array([r.path for r in short_plans])
            p_paths = sleeve_paths[:,:,0]+sleeve_paths[:,:,1]
            c_paths = sleeve_paths[:,:,2]
            path += exposure[risk,None]*(short_w[risk]@p_paths-
                              fee[risk,None]*(short_w[risk]@c_paths))
        for j,i in enumerate(risk):
            hit = np.flatnonzero(path[j]<=0)
            if equity[i]<=0 or len(hit):
                first = int(hit[0]) if len(hit) and equity[i]>0 else 0
                if short_plans and exposure[i]>0:
                    w = short_w[i]
                    price[i],funding[i],turn = w@sleeve_paths[:,first,:]
                    debit[i] = turn*fee[i]
                    forced[i] = np.sum((w>0)&is_forced&(c_paths[:,first]>1))
                book.failed[i] = True
    book.forced += forced*(exposure>0)
    book.funding += exposure*funding
    book.short_price += exposure*price
    book.short_fees += exposure*debit
    book.cash = np.where(book.failed,0,opening+gain+exposure*(price+funding-debit))
    for j,lot in enumerate(data):
        if lot.filled and (lot.outcome.release is None or lot.outcome.release > end):
            blocked = np.where(book.failed,0,unit*weights[:,j])
            book.add_pending(lot,blocked)
    book.begin(end)
    book.flags += flags


def short_weights(groups,market,majors,style,minimum):
    choices = market+majors
    allocations = np.zeros((len(groups),len(choices)))
    fallback = np.zeros(len(groups),dtype=bool)
    no_short = np.zeros(len(groups),dtype=bool)
    live_count = np.zeros(len(groups),dtype=int)
    for i,group in enumerate(groups):
        omit_ids = {a.coin for a in group}
        ix = [j for j,a in enumerate(market) if a.coin not in omit_ids]
        live_count[i] = len(ix)
        if style == "B" or len(ix) < minimum:
            fallback[i] = style == "M"
            ix = list(range(len(market),len(choices)))
        if ix:
            allocations[i,ix] = 1/len(ix)
        else:
            no_short[i] = True
    return allocations,fallback,no_short,live_count


def detail(book,p,weeks):
    end = book.finish()
    return {"end":float(end[0]),"funding":float(book.funding[0]),
            "short_price":float(book.short_price[0]),"short_fees":float(book.short_fees[0]),
            "forced_closes":int(book.forced[0]),"flagged_weeks":int(book.flags[0]),
            "flagged_week_share_pct":100*book.flags[0].item()/weeks,"ruined":bool(book.failed[0]),
            "random_percentile":C.percentile(end[1:].tolist(),p["random_percentile"]),
            "random_ends":end[1:].tolist()}


def replay(snapshots,spot,tapes,p,p13,identity=None):
    n = p13["hot_n"]
    p13 = p13|{k:p[k] for k in ("start","end","max_missing_hours")}
    rng = {name:random.Random(p["seed"]) for name in snapshots}
    answer = {}
    for year,start,finish in C.year_windows(p13):
        accounts = {name:{style:{c:Book(1+p["random_draws"]) for c in LEVELS}
                          for style in ("M","B")} for name in snapshots}
        all_spot = {name:Book(1) for name in snapshots}
        long_only = {name:{c:Book(1) for c in LEVELS} for name in snapshots}
        short_alone = {name:{style:{c:Book(1) for c in LEVELS} for style in ("M","B")}
                       for name in snapshots}
        paper = {name:1.0 for name in snapshots}
        rows = {name:[] for name in snapshots}
        for t in range(start,finish,C.WEEK):
            spot_ids,futures_ids = week_allowlist(identity,t)
            end = min(t+C.WEEK,finish)
            screens = defaultdict(set)
            market,missing = market_pool(snapshot_at(snapshots["viewed"],t),tapes,t,end,p,futures_ids,screens)
            majors = []
            for a in MAJORS:
                ok,bad = live(a,tapes.get(a.pair),t,end,p) if (
                    futures_ids is None or (a.coin,a.pair) in futures_ids) else (False,False)
                if ok:
                    majors.append(a)
                if bad:
                    missing.add(a.pair)
                if futures_ids is None or (a.coin,a.pair) in futures_ids:
                    actual = live_screens(a,tapes.get(a.pair),t,end,p)
                    if actual is not None and actual[0]:
                        screens["monday_live_majors"].add(a.pair)
                        if not actual[1]:
                            screens["file_gate_excluded_majors"].add(a.pair)
            plans = [short_week(tapes[a.pair],a,t,end,p) for a in market+majors]
            for name,snaps in snapshots.items():
                _,ranked,carried = spot_universe(snaps,spot,t,p13,spot_ids)
                hot = ranked[:n]
                pool = sorted(ranked)
                groups = [hot]+[rng[name].sample(pool,min(n,len(pool)))
                                for _ in range(p["random_draws"])]
                w = weight_matrix(groups,ranked)
                base_diag = {"t":t,"rankable":len(ranked),"carried":carried,
                             "hot":[a.coin for a in hot],"missing_funding_symbols":sorted(missing),
                             **{k:len(screens[k]) for k in ("monday_live","file_gate_excluded",
                                                           "monday_live_majors","file_gate_excluded_majors")}}
                sw = {s:short_weights(groups,market,majors,s,p["min_basket_names"])
                      for s in ("M","B")}
                base_diag.update(live_market=int(sw["M"][3][0]),live_majors=len(majors),
                                 fallback=bool(sw["M"][1][0]),no_short=bool(sw["M"][2][0]))
                rows[name].append(base_diag)
                for level in (*LEVELS,"paper"):
                    a,b,c = (0,0,0) if level=="paper" else [x/10000 for x in p[f"cost_{level}"]]
                    longs = [long_week(spot[x.pair],x,t,end,a,p13) for x in ranked]
                    all_w = np.ones((1,len(ranked)))
                    none = np.zeros((1,0))
                    false = np.zeros(1,dtype=bool)
                    if level in ("paper","judged"):
                        denom = max(1,len(ranked))
                        if level == "judged":
                            portfolio_step(all_spot[name],t,end,longs,all_w,denom,none,[],false,
                                           a,b,c,1,false)
                        else:
                            gains = np.array([r.outcome.factor-1 for r in longs])
                            paper[name] *= 1+(float(w[0]@gains)/n-float(all_w[0]@gains)/denom)
                            continue
                    portfolio_step(long_only[name][level],t,end,longs,w[:1],n,none,[],false,a,b,c,1,false)
                    long_flag = (w @ np.array([r.outcome.flagged for r in longs],dtype=int))>0
                    for style in ("M","B"):
                        alloc,fallback,no_short,_ = sw[style]
                        is_b = np.ones(len(w),dtype=bool) if style=="B" else fallback
                        short_flag = (alloc @ np.array([s.flagged for s in plans],dtype=int))>0
                        used_short = (w @ np.array([r.filled for r in longs],dtype=int))>0
                        flags = carried|fallback|no_short|long_flag|(short_flag&used_short)
                        portfolio_step(accounts[name][style][level],t,end,longs,w,n,alloc,plans,is_b,
                                       a,b,c,p["long_share"],flags)
                        # Matched size, but no long price change or equity tied
                        # up in coins for the scale-only short book.
                        neutral = [Long(r.filled,C.Outcome(1,end,()),np.ones_like(r.path)) for r in longs]
                        portfolio_step(short_alone[name][style][level],t,end,neutral,w[:1],n,alloc[:1],
                                       plans,is_b[:1],a,b,c,p["long_share"],flags[:1])
        answer[str(year)] = {
            name:{"weeks":rows[name],"all_spot_end":float(all_spot[name].finish()[0]),
                  "paper_lean_end":paper[name],
                  "long_only":{c:float(r.finish()[0]) for c,r in long_only[name].items()},
                  "short_alone":{s:{c:float(r.finish()[0]) for c,r in v.items()}
                                 for s,v in short_alone[name].items()},
                  "shorts":{s:{c:detail(r,p,len(rows[name])) for c,r in v.items()}
                            for s,v in accounts[name].items()}}
            for name in snapshots}
    return {"years":answer,"judgment":judge(answer,p)}


def judge(years,p):
    eligible,positive,both,falling,deep = [],[],[],[],[]
    for year, row in years.items():
        test = row["held"]["shorts"]["M"]["judged"]
        if test["end"] < 1-p["max_year_loss_pct"]/100:
            deep.append(year)
        if test["flagged_week_share_pct"] > p["max_flagged_week_share_pct"]:
            continue
        eligible.append(year)
        if test["end"] > 1:
            positive.append(year)
            if test["end"] > test["random_percentile"]:
                both.append(year)
                if row["held"]["all_spot_end"] < 1:
                    falling.append(year)
    marks = [len(positive)>=p["min_years_above"],len(both)>=p["min_years_above"],
             len(falling)>=p["min_falling_years"],not deep]
    return {"finding":"supported" if all(marks) else "not supported","marks":marks,
            "eligible":eligible,"positive":positive,"above_both":both,"falling":falling,
            "over_max_loss":deep}
