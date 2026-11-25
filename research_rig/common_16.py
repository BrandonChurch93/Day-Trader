"""Pure Replay 16 engine. The caller, not this module, opens verified archives."""
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
import random

import numpy as np

try:
    from . import common_13 as C
    from . import fetch_16 as F
except ImportError:
    import common_13 as C
    import fetch_16 as F

H = C.HOUR
MAJORS = (C.Asset(1,"BTCUSDT"),C.Asset(1027,"ETHUSDT"))
LEVELS = ("low","judged","high")


@dataclass(frozen=True)
class FBar:
    o: float
    h: float
    c: float


@dataclass
class Tape:
    trade: C.Series
    mark: C.Series
    funding: dict
    covered: tuple

    def __post_init__(self):
        self.payments = sorted(self.funding)

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


@dataclass(frozen=True)
class Sleeve:
    price: float
    funding: float
    turnover: float
    flagged: bool
    reason: str
    # End-of-hour marked cumulative gross components relative to entry notional.
    path: np.ndarray


def live(asset,tape,t,end,p):
    if tape is None or t not in tape.trade.bars or not asset.begin <= t < asset.end:
        return False,False
    # Initial source presence is distinct from trading liveness. A source
    # is needed only while this identity segment is in force.
    coverage = tape.covers(t,min(end,asset.end-H))
    latest = bisect_left(tape.payments,t)-1
    observed = latest >= 0 and tape.payments[latest] >= max(
        asset.begin,t-p["live_funding_lookback_hours"]*H)
    return coverage and observed,not coverage


def market_pool(snapshot,tapes,t,end,p):
    available = []
    unknown = set()
    taken = set()
    for row in snapshot["kept"] if snapshot else ():
        for asset in F.perp_segments(row):
            if not asset.begin <= t < asset.end or asset.pair in taken:
                continue
            ok,miss = live(asset,tapes.get(asset.pair),t,end,p)
            if miss:
                unknown.add(asset.pair)
            if ok:
                taken.add(asset.pair)
                available.append(asset)
                break
    return available,unknown


def short_week(tape,asset,start,end,p,trace=None):
    entry = tape.trade.bars[start].o
    stop = entry*(1+p["short_stop_pct"]/100)
    lookback = p["live_funding_lookback_hours"]*H
    idx = bisect_left(tape.payments,start)-1
    last_pay = tape.payments[idx] if idx >= 0 else -10**12
    prev_trade = None
    before = bisect_left(tape.trade.times,start)-1
    if before >= 0 and tape.trade.times[before] >= asset.begin:
        prev_trade = tape.trade.bars[tape.trade.times[before]].c
    funding, due = 0.0,None
    gap = tape.trade.missing_hours(start,end-H,before=asset.end) > p["max_missing_hours"]
    path = []
    loop = range(start,end+H,H)
    for t in loop:
        trade = tape.trade.bars.get(t) if t < asset.end else None
        mark = tape.mark.bars.get(t) if t < asset.end else None
        risk = mark or trade
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


def long_week(series,asset,t,end,fee,p):
    if t not in series.bars:
        return Long(False,C.Outcome(1,end,()),np.ones((end-t)//H+1))
    # The sole Rule A change is the entry gate above. The position cannot
    # buy after Monday, even though its Rule A sale may be delayed.
    outcome = C.hold_week(series,asset,t,end,fee,1,p)
    entry = series.bars[t].o
    price = entry
    marks = []
    for hour in range(t,end+H,H):
        if hour == end and outcome.release == end:
            marks.append(outcome.factor)
            break
        if hour < end and asset.begin <= hour < asset.end and hour in series.bars:
            price = series.bars[hour].c
        marks.append(price/(entry*(1+fee)))
    return Long(True,outcome,np.array(marks,dtype=float))


def snapshot_at(rows,t):
    return next((s for s in reversed(rows) if s["known_at"]<=t and s["kept"]),None)


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
        self.pending = {}
        self.flags = np.zeros(n,dtype=int)
        self.funding = np.zeros(n)
        self.short_price = np.zeros(n)
        self.short_fees = np.zeros(n)
        self.forced = np.zeros(n,dtype=int)
        self.failed = np.zeros(n,dtype=bool)

    def begin(self,t):
        for when in list(self.pending):
            if when is not None and when <= t:
                self.cash += self.pending.pop(when)
        self.cash[self.failed] = 0

    def add_pending(self,release,amount):
        if np.any(amount):
            self.pending[release] = self.pending.get(release,0)+amount

    def finish(self):
        return np.where(self.failed,0,self.cash+sum(self.pending.values(),0))


def portfolio_step(book,t,end,data,weights,hot_n,short_w,short_plans,is_b,
                   spot_fee,perp_fee,major_fee,share,flags):
    """Vectorized independent paths; delayed long proceeds stay unallocated."""
    book.begin(t)
    opening = book.cash.copy()
    if data:
        fills = weights @ np.array([d.filled for d in data],dtype=float)
        long_pnl = weights @ np.array([
            d.outcome.factor-1 if d.outcome.release is not None and d.outcome.release<=end
            else -1 for d in data])
        scaled = share/hot_n
        exposure = scaled*fills/(1+spot_fee)
        gain = scaled*long_pnl
    else:
        exposure = gain = np.zeros(len(opening))
        scaled = share/hot_n
    if short_plans:
        price = short_w @ np.array([r.price for r in short_plans])
        funding = short_w @ np.array([r.funding for r in short_plans])
        turnover = short_w @ np.array([r.turnover for r in short_plans])
        fee = np.where(is_b,major_fee,perp_fee)
        debit = turnover*fee
        book.forced += ((short_w>0) @ np.array([r.reason=="forced" for r in short_plans],
                                              dtype=int))*(exposure>0)*(~book.failed)
        # Only paths whose componentwise conservative floor is <= 0 need a
        # synchronized hourly check. Every long asset mark is nonnegative.
        floor = short_w @ np.array([r.path[:,0].min()+r.path[:,1].min()
                                   -max(perp_fee,major_fee)*r.path[:,2].max()
                                   for r in short_plans])
        risk = np.flatnonzero((opening>0)&(1-share+exposure*floor<=0))
        if len(risk):
            long_path = (weights[risk] @ np.array([d.path-1 for d in data]))*scaled
            p_paths = np.array([r.path[:,0]+r.path[:,1] for r in short_plans])
            c_paths = np.array([r.path[:,2] for r in short_plans])
            path = 1+long_path+exposure[risk,None]*(short_w[risk]@p_paths-
                              fee[risk,None]*(short_w[risk]@c_paths))
            book.failed[risk[np.any(path<=0,axis=1)]] = True
    else:
        price = funding = debit = np.zeros(len(opening))
    book.funding += opening*exposure*funding
    book.short_price += opening*exposure*price
    book.short_fees += opening*exposure*debit
    book.cash = np.where(book.failed,0,opening*(1+gain+exposure*(price+funding-debit)))
    for j,lot in enumerate(data):
        if lot.filled and (lot.outcome.release is None or lot.outcome.release > end):
            blocked = np.where(book.failed,0,opening*scaled*weights[:,j]*lot.outcome.factor)
            book.add_pending(lot.outcome.release,blocked)
    book.flags += flags


def short_weights(groups,market,majors,style,minimum):
    choices = market+majors
    allocations = np.zeros((len(groups),len(choices)))
    fallback = np.zeros(len(groups),dtype=bool)
    no_short = np.zeros(len(groups),dtype=bool)
    live_count = np.zeros(len(groups),dtype=int)
    for i,group in enumerate(groups):
        omit_ids = {a.coin for a in group}
        omit_symbols = {s for a in group for s in F.aliases(a.pair)}
        ix = [j for j,a in enumerate(market) if a.coin not in omit_ids and a.pair not in omit_symbols]
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


def replay(snapshots,spot,tapes,p,p13):
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
            end = min(t+C.WEEK,finish)
            market,missing = market_pool(snapshot_at(snapshots["viewed"],t),tapes,t,end,p)
            majors = []
            for a in MAJORS:
                ok,bad = live(a,tapes.get(a.pair),t,end,p)
                if ok:
                    majors.append(a)
                if bad:
                    missing.add(a.pair)
            plans = [short_week(tapes[a.pair],a,t,end,p) for a in market+majors]
            for name,snaps in snapshots.items():
                _,ranked,carried = C.weekly_universe(snaps,spot,t,p13)
                hot = ranked[:n]
                pool = sorted(ranked)
                groups = [hot]+[rng[name].sample(pool,min(n,len(pool)))
                                for _ in range(p["random_draws"])]
                w = weight_matrix(groups,ranked)
                base_diag = {"t":t,"rankable":len(ranked),"carried":carried,
                             "hot":[a.coin for a in hot],"missing_funding_symbols":sorted(missing)}
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
