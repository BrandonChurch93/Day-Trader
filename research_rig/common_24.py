"""Pure Plan 24 paired carry. UTC hours since epoch; no file or network access."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_EVEN, ROUND_HALF_UP
from math import ceil, fsum, isfinite, sqrt
from random import Random
from statistics import mean, stdev

DAY, HOUR = 24, 3600


class Incomplete(ValueError):
    pass


def hour(day):
    return int(datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())//HOUR


def year(t):
    return str(datetime.fromtimestamp(t*HOUR,timezone.utc).year)


def good(x):
    return x is not None and isfinite(x) and x>0


def cents(x):
    return Decimal(str(x)).quantize(Decimal(".01"),rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Pair:
    coin: int
    perp: str
    spot: str
    begin: int
    end: int
    closed_known_at: int | None = None


@dataclass(frozen=True)
class Bar:
    spot_open: float
    spot_low: float
    spot_close: float
    perp_open: float
    perp_close: float
    mark_close: float
    perp_high: float = 0.

    @property
    def worst(self):
        return self.spot_low,max(self.perp_open,self.perp_close,self.mark_close,self.perp_high)


@dataclass(frozen=True)
class Fee:
    spot_bp: float
    perp_bp: float
    commission_min: float = 0.
    exchange_bp: float = 0.
    perpetual_contract_fee: float = 0.
    min_perp_order: float = 0.
    robinhood_rounding: bool = False

    def charge(self,s,p,units=None):
        if p and self.min_perp_order and p+1e-9<self.min_perp_order:
            raise Incomplete("order below stated perpetual minimum")
        if p and self.perpetual_contract_fee and not good(units):
            raise Incomplete("no approved US contract conversion")
        if self.robinhood_rounding:
            spot, notional = cents(s),cents(p)
            spot_cost = spot*Decimal(str(self.spot_bp))/10000
            if not p:
                return float(spot_cost)
            commission = max(Decimal(str(self.commission_min)),
                             (notional*Decimal(str(self.perp_bp))/10000).quantize(Decimal(".01"),rounding=ROUND_CEILING))
            exchange = (notional*Decimal(str(self.exchange_bp))/10000).quantize(Decimal(".00001"),rounding=ROUND_HALF_EVEN)
            return float(spot_cost+commission+exchange)
        return (s*self.spot_bp/10000 + (max(self.commission_min,p*self.perp_bp/10000)
                +p*self.exchange_bp/10000+self.perpetual_contract_fee*(units or 0) if p else 0))


@dataclass
class Lot:
    s: float
    q: float
    margin: float
    spot: float
    perp: float
    worst: tuple


def run(tape, p, fee, *, threshold=None, universe=None, twin=None, rng=None):
    """A twin matches the ranked post-fill daily counts and realized occupied hours."""
    if twin is not None and rng is None:
        raise ValueError("a twin requires a fixed random stream")
    start,end = p["start"],p["end"]
    threshold = p["entry"] if threshold is None else threshold
    cash = p["initial_usd"]
    book, years, counts, entries = {}, {}, {}, {}
    by_year = {}
    curve, daily = [],[(start,cash)]
    spot_pnl = perp_pnl = funding = fees = 0.
    held_hours = occupied = missing_funding = forced = tops = trades = 0
    blocked_slot_days = bar_gap_slot_days = link_end_slot_days = unfilled_slot_days = unrankable_name_days = 0
    planned,entry_notional = (),0.
    selected_fresh = set()

    def equity():
        return cash + fsum(l.s*l.spot+l.margin for l in book.values())

    def charge(pair,t,spot_notional,short_notional,base):
        nonlocal fees
        converter = getattr(tape,"contract_units",None)
        units = converter(pair,t,base) if converter and fee.perpetual_contract_fee and base else None
        amount = fee.charge(spot_notional,short_notional,units=units)
        fees += amount
        return amount

    def mark(l,s,f):
        nonlocal spot_pnl,perp_pnl
        spot_pnl += l.s*(s-l.spot)
        delta = l.q*(l.perp-f)
        perp_pnl += delta
        l.margin += delta
        l.spot,l.perp = s,f

    def record(t):
        nonlocal trades
        trades += 1
        y = year(min(t,end-1))
        by_year[y] = by_year.get(y,0)+1

    def close(pair,t,s,f):
        nonlocal cash
        l = book.pop(pair)
        mark(l,s,f)
        cash += l.s*s+l.margin-charge(pair,t,l.s*s,l.q*f,l.q)
        record(t)

    def note_equity():
        e = equity()
        if not good(e):
            raise Incomplete("account equity is nonpositive")
        curve.append(e)
        return e

    def maintain(a,t,s,f):
        nonlocal forced,tops
        l = book[a]
        if l.margin+l.q*(l.perp-f)>=p["maintenance"]*l.q*f:
            return
        mark(l,s,f)
        value,short = l.s*s,l.q*f
        converter = getattr(tape,"contract_units",None)
        def fee_at(x):
            units = converter(a,t,l.q*x) if converter and fee.perpetual_contract_fee else None
            return fee.charge(value*x,short*x,units=units)
        if l.margin+value-fee_at(1)<0:
            close(a,t,s,f)
            forced += 1
            note_equity()
            return
        lo,hi = 0.,1.
        for _ in range(42):
            x = (lo+hi)/2
            if l.margin+x*value-fee_at(x)>=p["maintenance"]*(1-x)*short:
                hi = x
            else:
                lo = x
        if hi>=1-1e-10:
            close(a,t,s,f)
            forced += 1
        else:
            cost = charge(a,t,value*hi,short*hi,l.q*hi)
            l.margin += hi*value-cost
            l.s *= 1-hi
            l.q *= 1-hi
            tops += 1
            record(t)
        note_equity()

    for t in range(start,end+1):
        if t==end:
            opens = {a:tape.closing_open(a,t) for a in book}
            for a,l in book.items():
                op = opens[a]
                rate,offset = tape.payment(a,t)
                if rate is not None and offset<0:
                    f = op[1] if op is not None else l.perp
                    fp = max(l.perp,f) if rate<0 else min(l.perp,f)
                    l.margin += l.q*fp*rate
                    funding += l.q*fp*rate
                if op is not None:
                    mark(l,*op)
            if book:
                note_equity()
            for a in tuple(book):
                op = opens[a]
                if op is None:
                    close(a,t,*book[a].worst)
                    forced += 1
                else:
                    close(a,t,*op)
                note_equity()
            daily.append((t,note_equity()))
            break
        # Negative-offset events belong to the prior UTC period even when the
        # archive rounds them into a midnight hour or a gap starts at that hour.
        held_bars = {a:tape.bar(a,t) for a in book}
        carried_event = {a:tape.payment(a,t) for a in book}
        for a,l in book.items():
            rate,offset = carried_event[a]
            if rate is not None and offset<0:
                b = held_bars[a]
                f = b.perp_open if b is not None else l.perp
                fp = max(l.perp,f) if rate<0 else min(l.perp,f)
                delta = l.q*fp*rate
                l.margin += delta
                funding += delta
        if t%DAY==0 and t>start:
            daily.append((t,note_equity()))
        if t%DAY==0 and t+p["fill_hours"]<end:
            entry_notional = equity()/(2*p["slots"])
            pool = tape.pool(t,universe)
            incumbents = {a for a in book if a in pool and tape.decision_traded(a,t)}
            fresh = set(pool)-book.keys()
            if twin is None:
                rates = {a:tape.signal(a,t) for a in incumbents|fresh}
                unrankable_name_days += sum(rates[a] is None for a in fresh)
                # Missing signal or rank exit releases an incumbent; no replacement on a failed fill.
                keep = {a for a in incumbents if rates[a] is not None and rates[a]>p["exit"]}
                queue = sorted((a for a in fresh if rates[a] is not None and rates[a]>=threshold),
                               key=lambda a:(-rates[a],a.coin,a.perp,a.spot))
                planned = tuple(sorted(keep,key=lambda a:(a.coin,a.perp,a.spot)))+tuple(queue[:p["slots"]-len(keep)])
            else:
                order = lambda a:(a.coin,a.perp,a.spot)
                n,new = twin[0][t],twin[1][t]
                stay, fresh = sorted(incumbents,key=order),sorted(fresh,key=order)
                if n-new>len(stay) or new>len(fresh):
                    raise Incomplete("twin cannot match the ranked count and turnover as of decision")
                planned = tuple(rng.sample(stay,n-new)+rng.sample(fresh,new))
            # Allocate slots before checking entry coverage, without backfilling.
            selected_fresh = set(planned)-book.keys()
            admitted = []
            for a in planned:
                if a in book:
                    admitted.append(a)
                elif t+p["fill_hours"]>=a.end:
                    link_end_slot_days += 1
                elif not tape.entry_covered(a,t):
                    blocked_slot_days += 1
                elif tape.decision_traded(a,t):
                    admitted.append(a)
                else:
                    bar_gap_slot_days += 1
            planned = tuple(admitted)
        is_fill = t%DAY==p["fill_hours"] and t<end
        bars = held_bars | ({a:tape.bar(a,t) for a in planned if a not in held_bars} if is_fill else {})
        # Mark all carried lots consistently before execution checkpoints.
        gaps = []
        carried = set(book)
        for a in tuple(book):
            l,b = book[a],bars[a]
            if b is None:
                gaps.append(a)
                continue
            rate,offset = carried_event[a]
            if rate is not None and offset==0:
                fp = max(l.perp,b.perp_open) if rate<0 else min(l.perp,b.perp_open)
                l.margin += l.q*fp*rate
                funding += l.q*fp*rate
            if tape.payment_missing(a,t):
                fp = max(l.perp,b.perp_open)
                debit = l.q*fp*max(p["missing_floor"],tape.peak(a))
                l.margin -= debit
                funding -= debit
                missing_funding += 1
            mark(l,b.spot_open,b.perp_open)
        if book:
            note_equity()
        for a in gaps:
            close(a,t,*book[a].worst)
            forced += 1
            note_equity()
        for a in tuple(book):
            b = bars[a]
            maintain(a,t,b.spot_open,b.perp_open)
        if is_fill:
            old = set(book)
            # Do not use the incoming bar's low or close to select or price a normal fill.
            for a in tuple(book):
                if a not in planned:
                    b = bars[a]
                    close(a,t,b.spot_open,b.perp_open)
                    note_equity()
            for a in planned:
                b = bars[a]
                if a not in selected_fresh or a in carried:  # no resize or reopening planned stayers
                    continue
                if b is None:
                    bar_gap_slot_days += 1
                    continue
                cap = min(entry_notional,cash/2)
                if cap<p["entry_min_usd"]:
                    continue
                converter = getattr(tape,"contract_units",None)
                def order_cost(n):
                    units = converter(a,t,n/b.perp_open) if converter and fee.perpetual_contract_fee else None
                    return fee.charge(n,n,units=units)
                # Reserve the fee quoted at the upper bound. Actual fees can
                # only be lower on the registered schedules. No solver.
                n = min(cap,(cash-order_cost(cap))/2)
                if n<p["entry_min_usd"]:
                    continue
                cost = order_cost(n)
                if 2*n+cost>cash+1e-10:
                    raise Incomplete("entry fee exceeds reserved free cash")
                cash -= 2*n+cost
                fees += cost
                book[a] = Lot(n/b.spot_open,n/b.perp_open,n,b.spot_open,b.perp_open,(b.spot_open,b.perp_open))
                record(t)
                note_equity()
            counts[t-p["fill_hours"]] = len(book)
            entries[t-p["fill_hours"]] = len(set(book)-old)
            unfilled_slot_days += len(selected_fresh)-entries[t-p["fill_hours"]]
            if twin is not None and (len(book),entries[t-p["fill_hours"]])!=(twin[0][t-p["fill_hours"]],twin[1][t-p["fill_hours"]]):
                raise Incomplete("twin missed a matched open")
        held_hours += len(book)
        occupied += bool(book)
        for a in tuple(book):
            l,b = book[a],bars[a]
            rate,offset = tape.payment(a,t)
            if rate is not None and offset>0:
                fp = max(b.perp_open,b.mark_close) if rate<0 else min(b.perp_open,b.mark_close)
                l.margin += l.q*fp*rate
                funding += l.q*fp*rate
        for a in tuple(book):
            maintain(a,t,*bars[a].worst)
        for a,l in book.items():
            b = bars[a]
            mark(l,b.spot_close,b.mark_close)
            l.worst = b.worst
        note_equity()
    if twin is not None and held_hours!=twin[2]:
        raise Incomplete("twin has different realized coin-hours")
    final = daily[-1][1]
    returns = [b/a-1 for (_,a),(_,b) in zip(daily,daily[1:])]
    sigma = stdev(returns) if len(returns)>1 else 0
    high,dd = p["initial_usd"],0.
    for v in curve:
        high = max(high,v)
        dd = max(dd,1-v/high)
    for (t,a),(_,b) in zip(daily,daily[1:]):
        y = year(t)
        base,_ = years.get(y,(a,a))
        years[y] = (base,b)
    initial = p["initial_usd"]
    if abs(final-initial-(spot_pnl+perp_pnl+funding-fees))>max(initial,final)*1e-8:
        raise AssertionError("pair P&L does not reconcile")
    return dict(final=final,annual=(final/initial)**(p["annual_days"]*DAY/(end-start))-1,
                sharpe=mean(returns)/sigma*sqrt(p["annual_days"]) if sigma else None,drawdown=dd,
                years={y:b/a-1 for y,(a,b) in years.items()},trades=by_year,trade_events=trades,
                funding_points=100*funding/initial,basis_points=100*(spot_pnl+perp_pnl)/initial,
                fee_points=-100*fees/initial,coin_hours=held_hours,time_in_market=occupied/(end-start),
                forced=forced,margin_topups=tops,missing_funding=missing_funding,
                blocked_slot_days=blocked_slot_days,bar_gap_slot_days=bar_gap_slot_days,
                data_gap_slot_days=blocked_slot_days+bar_gap_slot_days,unfilled_slot_days=unfilled_slot_days,
                link_end_slot_days=link_end_slot_days,
                unrankable_name_days=unrankable_name_days,schedule=(counts,entries,held_hours))


def assess(tape,p,fee):
    main = run(tape,p,fee)
    twins,refused = [],{}
    for i in range(p["draws"]):
        try:
            twins.append(run(tape,p,fee,twin=main["schedule"],rng=Random(p["seed"]+i))["annual"])
        except Incomplete as exc:
            refused[str(i)] = str(exc)
    q = sorted(twins)[ceil(len(twins)*p["percentile"])-1] if len(twins)==p["draws"] else None
    checks = dict(annual=main["annual"]>=p["min_annual"],sharpe=main["sharpe"] is not None and main["sharpe"]>=p["min_sharpe"],
                  drawdown=main["drawdown"]<=p["max_drawdown"],
                  positive_years=sum(v>0 for v in main["years"].values())>=p["positive_years"],
                  twins=q is not None and main["annual"]>q)
    return dict(main=main,twins=twins,twin_refusals=refused,p95=q,checks=checks,passed=all(checks.values()))
