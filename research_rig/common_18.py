"""Funding-carry mechanics. Only the registered policy is loaded here."""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from math import fsum, isfinite, sqrt
from pathlib import Path
from random import Random
from statistics import mean, stdev

import yaml

CONFIG = Path(__file__).resolve().parents[1]/"config/thresholds.yaml"
H = 3600


def policy(raw):
    p = dict(yaml.safe_load(raw)["replay_18_plan"]["value"])
    integers = set("roll_hours lookback_hours funding_interval_hours funding_lag_intervals funding_jitter_seconds fill_lag_hours "
                   "max_snapshot_age_days top_rank legs min_positive_years min_traded_slots "
                   "annualization_days random_draws seed power_seed power_pairs".split())
    others = set("start end judged_cost_bps shown_cost_bps min_sharpe max_drawdown random_quantiles "
                 "power_sharpes power_sigma_daily".split())
    if set(p) != integers|others or any(type(p[k]) is not int or p[k]<=0 for k in integers):
        raise ValueError("invalid Plan 18 policy fields")
    for k in ("start","end"):
        d = datetime.fromisoformat(p[k])
        if d.tzinfo is not None or d.hour or d.minute or d.second or d.microsecond:
            raise ValueError("Plan 18 bounds must be dates in UTC")
        p[k] = int(d.replace(tzinfo=timezone.utc).timestamp()//H)
    fees = (*p["shown_cost_bps"],p["judged_cost_bps"])
    if (p["start"]>=p["end"] or len(fees)!=3 or len(set(fees))!=len(fees)
        or not all(type(x) is int and 0<=x<10_000 for x in fees)
        or not p["shown_cost_bps"][0]<p["judged_cost_bps"]<p["shown_cost_bps"][1]
        or p["roll_hours"]%p["funding_interval_hours"]
        or p["lookback_hours"]%p["funding_interval_hours"] or p["funding_interval_hours"]>=24
        or not 0<p["fill_lag_hours"]<p["roll_hours"] or 2*p["legs"]>p["top_rank"]
        or not isfinite(p["min_sharpe"]) or not 0<p["max_drawdown"]<1
        or sorted(set(p["random_quantiles"]))!=p["random_quantiles"]
        or not all(0<=x<=1 for x in p["random_quantiles"])
        or not 0<p["funding_jitter_seconds"]<H/2
        or sorted(set(p["power_sharpes"]))!=p["power_sharpes"] or not p["power_sharpes"]
        or not 0<p["power_sigma_daily"]<1
        or p["min_positive_years"]>utc_year(p["end"]-1)-utc_year(p["start"])+1):
        raise ValueError("inconsistent Plan 18 policy")
    return p


def utc_year(t):
    return datetime.fromtimestamp(t*H, timezone.utc).year


P = policy(CONFIG.read_bytes())
ROLL,FUND,LEGS,DRAWS,SEED,START,END = (P[k] for k in
    ("roll_hours","funding_interval_hours","legs","random_draws","seed","start","end"))
COSTS = tuple(sorted((*P["shown_cost_bps"],P["judged_cost_bps"])))


class Incomplete(ValueError):
    """An occupied position cannot be accounted for without inventing data."""


@dataclass(frozen=True)
class Contract:
    coin_id: int
    rank: int
    key: str                  # unique dated contract segment, not bare ticker
    begin: int                # all times in UTC hours since the epoch
    end: int                  # exclusive full-bar boundary
    listed_known_at: int = -10**15  # exact UTC seconds
    closed_effective: int | None = None  # UTC hours; independent of accounting end
    closed_known_at: int | None = None   # UTC seconds


@dataclass(frozen=True)
class Snapshot:
    known_at: int              # exact UTC seconds
    contracts: tuple[Contract, ...]
    ranks: tuple[tuple[int,int], ...] = ()  # rank and ID from the raw page


@dataclass(frozen=True)
class Result:
    sharpe: float | None
    max_drawdown: float
    years: dict
    final: float
    traded: int
    too_few: int
    no_open: int
    marks: tuple[bool, bool, bool]
    price_pnl: float
    funding_pnl: float
    fees: float
    funnel: dict
    forced: tuple


@dataclass(frozen=True)
class Draw:
    seed: int
    result: Result | None
    refusal: str | None = None


def latest(snapshots, t, p=P):
    visible = [s for s in snapshots if s.known_at < t*H]
    if not visible:
        raise Incomplete(f"no known monthly snapshot at {t}")
    snap = max(visible, key=lambda s: s.known_at)
    if t*H - snap.known_at > p["max_snapshot_age_days"]*24*H or sum(s.known_at == snap.known_at for s in visible) != 1:
        raise Incomplete(f"stale or ambiguous monthly snapshot at {t}")
    return snap


def eligible(tape, snap, t, roster=None, p=P, funnel=None):
    """Adapter must supply exact completed-bar and settlement coverage, not guessed zeros."""
    lo = t-p["lookback_hours"]-p["funding_interval_hours"]*p["funding_lag_intervals"]
    hi = lo+p["lookback_hours"]
    scope = {i for r,i in snap.ranks if 1<=r<=p["top_rank"]} if snap.ranks else {
        c.coin_id for c in snap.contracts if 1<=c.rank<=p["top_rank"]}
    if roster is not None:
        scope = set(roster)
    chosen = [c for c in snap.contracts if c.coin_id in scope and c.begin<=lo
              and c.listed_known_at<t*H and not (
                  c.closed_known_at is not None and c.closed_known_at<t*H and c.closed_effective<=t)]
    if len({c.coin_id for c in chosen}) != len(chosen) or len({c.key for c in chosen}) != len(chosen):
        raise Incomplete(f"ambiguous dated mapping at {t}")
    pool = []
    funnel = Counter() if funnel is None else funnel
    funnel.update({"scope":len(scope),"dated_listed":len(chosen)})
    if roster is None and snap.ranks:
        funnel["raw_rank_page_rows"] += len(snap.ranks)
        funnel["outside_rank_cutoff"] += len(snap.ranks)-len(scope)
    for c in chosen:
        if not tape.traded(c.key, t-2) or not c.begin<=t-2:
            funnel["missing_prior_traded_bar"] += 1
            continue
        funnel["prior_bar"] += 1
        rates = []
        for h in range(lo, hi):
            covered, rate = tape.rank_funding(c.key, h, t*H)
            if not covered:
                funnel["funding_uncovered_or_unavailable"] += 1
                break
            if rate is None and h % p["funding_interval_hours"] == 0:
                funnel["expected_settlement_missing"] += 1
                break
            if rate is not None and (h % p["funding_interval_hours"] or not isfinite(rate)):
                funnel["off_grid_or_invalid_settlement"] += 1
                break
            if rate is not None:
                rates.append(rate)
        else:
            pool.append((fsum(rates), c))
    funnel["rankable"] += len(pool)
    return sorted(pool, key=lambda q: (q[0], q[1].coin_id, q[1].key))


def selection(pool, rng=None, p=P):
    legs = p["legs"]
    if len(pool) < 2*legs:
        return ()
    if rng is None:
        sides = pool[:legs] + pool[-legs:]
    else:
        universe = sorted(pool, key=lambda q: (q[1].coin_id, q[1].key))
        sides = rng.sample(universe, 2*legs)
    return tuple((c, 1 if i < legs else -1) for i, (_, c) in enumerate(sides))


def valid(price):
    return price is not None and isfinite(price) and price > 0


def marks(p, sharpe, dd, years, traded):
    return (sharpe is not None and sharpe>=p["min_sharpe"],
            dd<=p["max_drawdown"] and traded>=p["min_traded_slots"],
            sum(v>0. for v in years.values())>=p["min_positive_years"])


def run_book(tape, snapshots, start, end, bps=None, *, roster=None, rng=None, p=P,
             pools=None, gross_reopen=False):
    bps = p["judged_cost_bps"] if bps is None else bps
    if start % 24 or end % 24 or end <= start or bps not in (p["judged_cost_bps"],*p["shown_cost_bps"]):
        raise ValueError("use UTC day boundaries and a declared fee")
    fee = bps/10_000
    cash = peak = 1.
    dd = 0.
    daily = {start: cash}
    traded = too_few = no_open = 0
    price_pnl = funding_pnl = fees = 0.
    funnel = Counter()
    forced = []
    positions = {}  # key -> (contract, quantity, basis, last traded hour, last trade close)
    roll,lag = p["roll_hours"],p["fill_lag_hours"]

    def value(h, equity, save_day=True):
        nonlocal peak, dd
        if not isfinite(equity) or equity <= 0:
            raise Incomplete(f"nonpositive or invalid proxy equity at {h}; no marks")
        peak = max(peak, equity)
        dd = max(dd, 1-equity/peak)
        if save_day and h % 24 == 0:
            daily[h] = equity

    def force(key,h,reason):
        nonlocal cash,price_pnl,fees
        c,q,basis,last_h,last_px = positions.pop(key)
        zero = q>0 and tape.terminal(c,h,last_h)
        px = 0. if zero else last_px
        pnl = q*(px-basis)
        charge = abs(q)*last_px*p["judged_cost_bps"]/10_000
        cash += pnl-charge
        price_pnl += pnl
        fees += charge
        forced.append(dict(hour=h,last_trade_hour=last_h,coin_id=c.coin_id,key=key,
                           side="long" if q>0 else "short",reason=reason,price=px,
                           last_close=last_px,fee=charge,zeroed=zero))

    def retarget(h,picks,opens):
        nonlocal cash,price_pnl,fees
        for key,(c,_,_,_,_) in tuple(positions.items()):
            if not c.begin<=h<c.end or not valid(opens.get(key)):
                force(key,h,"no_tradable_exit_open")
        old = dict(positions)
        step_price = fsum(q*(opens[key]-basis) for key,(_,q,basis,_,_) in old.items())
        cash += step_price
        price_pnl += step_price
        positions.clear()
        if gross_reopen:
            exit_fee = fee*fsum(opens[k]*abs(v[1]) for k,v in old.items())
            fees += exit_fee
            cash -= exit_fee
            value(h,cash,save_day=False)
        if picks:
            for c,side in picks:
                px = opens[c.key]
                positions[c.key] = c,side*cash/(2*p["legs"]*px),px,h,px
        notionals = []
        for key in sorted(old.keys()|positions.keys()):
            before = old[key][1] if key in old else 0.
            after = positions[key][1] if key in positions else 0.
            notionals.append(opens[key]*(abs(after) if gross_reopen else abs(after-before)))
        charge = fsum(notionals)*fee
        fees += charge
        cash -= charge
        value(h,cash,save_day=False)

    first = start+lag
    stop = first+max(0,(end-first)//roll)*roll
    for h in range(start+24,min(first,end)+1,24):
        value(h,cash)
    for t in range(first,stop,roll):
        decision,e = t-lag,t+roll
        if pools is None or decision not in pools:
            f = Counter()
            pool = eligible(tape, latest(snapshots, decision,p), decision,roster,p,f)
            if pools is not None:
                pools[decision] = pool,f
        else:
            pool,f = pools[decision]
        funnel.update(f)
        picks = selection(pool,rng,p)
        too_few += not picks
        contracts = {c.key:c for c,_ in picks} | {k:v[0] for k,v in positions.items()}
        opens = {k:tape.open_price(k,t) if c.begin<=t<c.end else None for k,c in contracts.items()}
        if picks and not all(valid(opens[c.key]) for c,_ in picks):
            no_open += 1
            picks = ()
        traded += bool(picks)
        retarget(t,picks,opens)
        for h in range(t+1, e+1):
            unrealized = 0.
            closes = {}
            for key,(c,q,basis,_,_) in tuple(positions.items()):
                tr = tape.trade_close(key,h-1) if h-1<c.end else None
                if not valid(tr):
                    force(key,h,"trade_gap_or_fence")
                    continue
                positions[key] = c,q,basis,h-1,tr
                mark = tape.mark_close(key,h-1)
                if not valid(mark):
                    funnel["occupied_mark_fallback"] += 1
                    mark = tr
                unrealized += q*(mark-basis)
                closes[key] = mark
            value(h, cash+unrealized, save_day=False)
            for key,(c,q,basis,_,_) in tuple(positions.items()):
                mark = closes[key]
                if h >= c.end:
                    unrealized -= q*(mark-basis)
                    force(key,h,"dated_accounting_fence")
                    continue
                covered, rate = tape.funding(key, h)
                if not covered:
                    unrealized -= q*(mark-basis)
                    force(key,h,"occupied_funding_coverage_gap")
                    continue
                if rate is not None and not isfinite(rate):
                    raise Incomplete(f"invalid stored funding for {c.key} at {h}")
                if rate is not None:
                    flow = -q*mark*rate
                    cash += flow
                    funding_pnl += flow
            value(h, cash+unrealized)
    retarget(stop,(),{k:tape.open_price(k,stop) for k in positions})
    value(stop,cash)
    for h in range((stop//24+1)*24,end+1,24):
        value(h,cash)
    if len(daily) != (end-start)//24+1:
        raise Incomplete("missing daily equity")
    changes, years = [], {}
    for h in range(start, end, 24):
        ret = daily[h+24]/daily[h]
        changes.append(ret-1)
        year = utc_year(h)
        years[year] = years.get(year,1.)*ret
    years = {y:v-1 for y,v in years.items()}
    sd = stdev(changes) if len(changes)>1 else 0.
    sharpe = sqrt(p["annualization_days"])*mean(changes)/sd if sd else None
    judged = ((start,end,bps)==(p["start"],p["end"],p["judged_cost_bps"])
              and roster is None and rng is None and not gross_reopen)
    hit = marks(p,sharpe,dd,years,traded) if judged else (False,)*3
    return Result(sharpe,dd,years,cash,traded,too_few,no_open,hit,price_pnl,funding_pnl,fees,
                  dict(funnel),tuple(forced))


def random_books(tape,snapshots,start,end,*,p=P,pools=None,check=lambda:None):
    pools = {} if pools is None else pools
    results = []
    for seed in range(p["seed"],p["seed"]+p["random_draws"]):
        check()
        try:
            result = run_book(tape,snapshots,start,end,rng=Random(seed),p=p,pools=pools)
        except Incomplete as exc:
            results.append(Draw(seed,None,str(exc)))
        else:
            results.append(Draw(seed,result))
    return tuple(results)


def quantiles(values,probs):
    seq = sorted(values)
    if not seq:
        return {str(q):None for q in probs}
    answer = {}
    for q in probs:
        i = q*(len(seq)-1)
        lo,hi = int(i),min(int(i)+1,len(seq)-1)
        answer[str(q)] = seq[lo]+(i-lo)*(seq[hi]-seq[lo])
    return answer


def random_summary(draws,ranked,p=P):
    books = [d.result for d in draws if d.result is not None]
    sharpe = [r.sharpe for r in books if r.sharpe is not None]
    probs = p["random_quantiles"]
    ref = ranked.sharpe if ranked is not None else None
    return dict(requested=len(draws), complete=len(books), defined_sharpe=len(sharpe),
                incomplete=len(draws)-len(books),
                undefined_sharpe=len(books)-len(sharpe),
                refusals=[dict(seed=d.seed,reason=d.refusal) for d in draws if d.refusal],
                fraction_at_or_above_sharpe=(sum(v>=ref for v in sharpe)/len(sharpe)
                                              if sharpe and ref is not None else None),
                quantiles={"sharpe":quantiles(sharpe,probs),**{k:quantiles(
                    (getattr(r,k)-(k=="final") for r in books),probs) for k in
                    ("final","max_drawdown","traded","no_open","too_few","fees")}},
                forced_counts={str(d.seed):len(d.result.forced) for d in draws if d.result is not None},
                forced_cases={str(d.seed):d.result.forced for d in draws if d.result and d.result.forced})
