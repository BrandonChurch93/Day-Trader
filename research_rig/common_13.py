"""Replay 13 calendar, availability, execution and portfolio rules."""

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import date, timedelta
import heapq
import math
import random
from statistics import mean

try:
    from .fetch_13 import HOUR, stamp, utc, segments
except ImportError:
    from fetch_13 import HOUR, stamp, utc, segments

DAY = 24 * HOUR
WEEK = 7 * DAY


@dataclass(frozen=True, order=True)
class Asset:
    coin: int
    pair: str
    begin: int = -10**12
    end: int = 10**12


@dataclass(frozen=True)
class Bar:
    o: float
    l: float
    c: float
    h: float | None = None


@dataclass
class Series:
    bars: dict

    def __post_init__(self):
        self.times = sorted(self.bars)

    def open_at_or_after(self, t, end):
        i = bisect_left(self.times, t)
        if i < len(self.times) and self.times[i] < end:
            return self.times[i], self.bars[self.times[i]].o
        return None

    def missing_hours(self, a, b, *, before=None):
        """Count missing hourly opens in [a,b]; don't borrow from a new identity segment."""
        if a > b:
            return 0
        observed_through = min(b,before-HOUR) if before is not None else b
        observed = max(0,bisect_right(self.times,observed_through)-bisect_left(self.times,a))
        return (b-a)//HOUR+1-observed

    def usable_lookback(self, a, b, max_missing):
        return a in self.bars and b in self.bars and self.missing_hours(a,b) <= max_missing


@dataclass(frozen=True)
class Outcome:
    factor: float
    release: int | None
    reasons: tuple
    flagged: bool = False


def year_windows(p):
    lo, hi = map(date.fromisoformat, (p["start"], p["end"]))
    final = hi - timedelta(days=hi.weekday())
    for yr in range(lo.year, hi.year+1):
        start = max(lo,date(yr,1,1))
        first = start + timedelta(days=(-start.weekday()) % 7)
        end = min(date(yr+1,1,1), final) if yr == hi.year else date(yr+1,1,1)
        if first < end:
            yield yr, stamp(first), stamp(end)


def weekly_universe(snapshots, data, t, p, diagnostics=None):
    eligible = [s for s in snapshots if s["known_at"] <= t]
    current = next((s for s in reversed(eligible) if s["kept"]), None)
    flagged = current is None or current is not eligible[-1]
    listed, ranked, allocated = [], [], {}
    duplicate_pairs, duplicates = set(), set()
    rows = sorted(current["kept"],key=lambda row: row.get("cmcRank",float("inf"))) if current else ()
    for row in rows:
        for lo, hi, pair in segments(row):
            if not lo <= t < hi:
                continue
            if pair in allocated:
                if allocated[pair] != row["id"]:
                    duplicate_pairs.add(pair)
                    duplicates.add(row["id"])
                continue
            allocated[pair] = row["id"]
            if pair not in data:
                continue
            # A listing/open is not inferred from a future bar.
            series = data[pair]
            if t-HOUR < lo or t-HOUR not in series.bars:
                continue
            asset = Asset(row["id"], pair, lo, hi)
            listed.append(asset)
            cutoff = t-(24*p["rise_days"]+1)*HOUR
            if cutoff >= lo and series.usable_lookback(cutoff,t-HOUR,p["max_missing_hours"]):
                ranked.append((series.bars[t-HOUR].c/series.bars[cutoff].c-1, asset))
    ranked.sort(key=lambda item: (-item[0], item[1].coin))
    if diagnostics is not None:
        diagnostics.update(no_prior_hour=len(rows)-len(listed)-len(duplicates),
                           incomplete_history=len(listed)-len(ranked),
                           not_rankable=len(rows)-len(ranked),
                           duplicate_pair_count=len(duplicate_pairs),
                           duplicate_pair_exclusions=len(duplicates))
    return listed, [a for _,a in ranked], flagged


def dip_signal(series, asset, t, p):
    prev = t-HOUR
    old = prev-24*p["rise_days"]*HOUR
    high_from = prev-p["dip_lookback_hours"]*HOUR
    if min(old,high_from) < asset.begin or not series.usable_lookback(old,prev,p["max_missing_hours"]):
        return False
    close = series.bars[prev].c
    high = max((series.bars[x].c for x in range(high_from,prev,HOUR) if x in series.bars),default=None)
    return high is not None and close <= high*(1-p["dip_pct"]/100) and close > series.bars[old].c


def sale_factor(entry, sale, held, fee, leverage, p):
    # Size from cash including the entry fee. Funding is prorated to elapsed hours.
    notional = leverage / (1+leverage*fee)
    exit_notional = notional * sale / entry
    borrowed = notional*(1-1/leverage)
    funding = (borrowed*p["financing_bps_per_8h"]/10_000
               * held / (p["financing_interval_hours"]*HOUR))
    return max(0, notional/leverage + exit_notional-notional - exit_notional*fee-funding)


def hold_week(s, asset, start, end, fee, leverage, p, trace=None):
    limit = p["max_missing_hours"]
    week_gap = s.missing_hours(start,end-HOUR,before=asset.end) > limit
    deadline = min(end-HOUR, start+limit*HOUR)
    first = s.open_at_or_after(max(start,asset.begin), min(deadline+HOUR,asset.end))
    if trace is not None and start not in s.bars and deadline > start:
        trace.append((start,"queue_entry",None,1))
    if first is None:
        if trace is not None:
            trace.append((deadline,"skip_entry",None,1))
        return Outcome(1,end,(),True)
    entry_at, entry = first
    if trace is not None:
        trace.append((entry_at,"buy",entry,1))
    sell = s.open_at_or_after(end, asset.end)
    if sell is not None:
        t, px = sell
        factor = sale_factor(entry,px,t-entry_at,fee,leverage,p)
        if trace is not None:
            if t > end:
                trace.append((end,"queue_exit",None,1))
            trace.append((t,"sell",px,factor))
        return Outcome(factor,t,("week_end",),t != end or week_gap)
    i = bisect_left(s.times,min(end,asset.end))-1
    t = s.times[i]
    factor = sale_factor(entry,s.bars[t].c,t+HOUR-entry_at,fee,leverage,p)
    if trace is not None:
        trace.append((end,"queue_exit",None,1))
    return Outcome(factor,None,("last_close",),True)


def swing_week(s, asset, start, end, fee, leverage, p, trace=None):
    wealth, entry, entry_at = 1, None, None
    pending, reasons = None, []
    flagged = s.missing_hours(start,end-HOUR,before=asset.end) > p["max_missing_hours"]
    last = None
    lev = leverage > 1
    floor = 1 - p["liquidation_drop_pct"]/100
    for t in range(start,end+HOUR,HOUR):
        bar = s.bars.get(t) if t < asset.end else None
        if entry is not None:
            prev = s.bars.get(t-HOUR) if t-HOUR < asset.end else None
            if lev and ((prev and prev.l <= entry*floor) or (bar and bar.o <= entry*floor)):
                if trace is not None:
                    trace.append((t,"liquidation",None,0))
                return Outcome(0,t,tuple(reasons+["liquidation"]),flagged)
            reason = pending
            if t == end:
                reason = "week_end"
            elif reason is None and prev is not None:
                if prev.c <= entry*(1-p["stop_pct"]/100):
                    reason = "stop"
                elif prev.c >= entry*(1+p["take_pct"]/100):
                    reason = "take"
            if reason is None and t-entry_at >= p["max_hold_hours"]*HOUR:
                reason = "timeout"
            if reason is not None:
                if not bar:
                    flagged = True
                    pending = reason
                    if trace is not None:
                        trace.append((t,"queue_exit",None,wealth))
                else:
                    wealth *= sale_factor(entry,bar.o,t-entry_at,fee,leverage,p)
                    reasons.append(reason)
                    if trace is not None:
                        trace.append((t,reason,bar.o,wealth))
                    entry, pending = None,None
        elif t < end and bar and wealth > 0 and dip_signal(s,asset,t,p):
            entry, entry_at = bar.o,t
            if trace is not None:
                trace.append((t,"buy",entry,wealth))
        if bar is not None and t < end:
            last = (t,bar)
    if entry is None:
        return Outcome(wealth,end,tuple(reasons),flagged)
    next_print = s.open_at_or_after(end+HOUR, asset.end)
    if next_print is not None:
        t, px = next_print
        if lev and px <= entry*floor:
            if trace is not None:
                trace.append((t,"liquidation",None,0))
            return Outcome(0,t,tuple(reasons+["liquidation"]),True)
        wealth *= sale_factor(entry,px,t-entry_at,fee,leverage,p)
        if trace is not None:
            trace.append((t,"week_end",px,wealth))
        return Outcome(wealth,t,tuple(reasons+["week_end"]),True)
    t, bar = last
    wealth *= sale_factor(entry,bar.c,t+HOUR-entry_at,fee,leverage,p)
    return Outcome(wealth,None,tuple(reasons+["last_close"]),True)


def percentile(values, percentage):
    a = sorted(values)
    k = (len(a)-1)*percentage/100
    lo, hi = math.floor(k),math.ceil(k)
    return a[lo] + (a[hi]-a[lo])*(k-lo)


class Account:
    def __init__(self):
        self.cash = 1.0
        self.queue = []
        self.terminal_marks = []
        self.flags = 0
        self.parts = 0
        self.reasons = {}
        self.weeks = 0

    def advance(self, start, slots, flows, entire_week_flagged):
        self.weeks += 1
        self.parts += slots
        while self.queue and self.queue[0][0] <= start:
            self.cash += heapq.heappop(self.queue)[1]
        if len(flows) > slots:
            raise ValueError("more sleeve outcomes than account parts")
        allocation = self.cash / slots
        self.cash = allocation*(slots-len(flows))
        # A cash placeholder without a selected coin is not a flagged part.
        self.flags += len(flows) if entire_week_flagged else sum(x.flagged for x in flows)
        for r in flows:
            if allocation <= 0:
                continue
            for why in r.reasons:
                self.reasons[why] = self.reasons.get(why,0)+1
            if r.release is None:
                # A full-file inference sets the terminal mark, not tradable cash.
                self.terminal_marks.append(allocation*r.factor)
            else:
                heapq.heappush(self.queue,(r.release,allocation*r.factor))

    def finish(self):
        trades = sum(self.reasons.values())
        return {
            "gain": self.cash + sum(v for _,v in self.queue) + sum(self.terminal_marks) - 1,
            "trades": trades, "reasons": self.reasons,
            "stop_share": self.reasons.get("stop",0)/trades if trades else None,
            "weeks": self.weeks, "flagged_part_weeks": self.flags, "part_weeks":self.parts,
            "flagged_share_pct": 100*self.flags/self.parts if self.parts else 0,
        }


def bitcoin(data, start, end, fee, p):
    series = data.get("BTCUSDT")
    if not series or not all(t in series.bars for t in (start,end)):
        return None
    a,b = series.bars[start].o,series.bars[end].o
    return {"gross":b/a-1,"net":sale_factor(a,b,end-start,fee,1,p)-1}


def replay(snapshots, data, p):
    years = {}
    base = p["cost_bps_per_side"]
    alt = p["other_costs_bps"]
    leverage = p["judged_leverage"]
    n = p["hot_n"]
    rng = random.Random(p["seed"])
    for yr, start, finish in year_windows(p):
        models = [("A",base,leverage),("B",base,leverage),("all",base,leverage),
                  ("B_leveraged",base,p["shown_leverage"])]
        models += [(kind,c,leverage) for c in alt for kind in ("A","B","all")]
        fixed = {key:Account() for key in models}
        costs = [base,*alt]
        random_at = {c: {kind:[Account() for _ in range(p["random_draws"])]
                         for kind in ("A","B")} for c in costs}
        weekly = []
        for t in range(start,finish,WEEK):
            end = min(t+WEEK,finish)
            diagnostics = {}
            listed, ranked, flag = weekly_universe(snapshots,data,t,p,diagnostics)
            hot = ranked[:n]
            weekly.append({"start":utc(t).isoformat(),"end":utc(end).isoformat(),
                           "listed":len(listed),"rankable":len(ranked),"snapshot_flagged":flag,
                           "selected":[{"id":a.coin,"pair":a.pair} for a in hot], **diagnostics})
            week_cache = {}

            def find(kind, asset, c, l):
                mode = "A" if kind in ("A","all") else "B"
                key = mode,asset,c,l
                if key not in week_cache:
                    algo = hold_week if mode == "A" else swing_week
                    week_cache[key] = algo(data[asset.pair],asset,t,end,c/10_000,l,p)
                return week_cache[key]

            for (kind,c,l), account in fixed.items():
                active = ranked if kind == "all" else hot
                slots = max(1,len(active)) if kind == "all" else n
                account.advance(t,slots,[find(kind,a,c,l) for a in active],flag)
            sample_pool = sorted(ranked)
            for i in range(p["random_draws"]):
                picks = rng.sample(sample_pool,min(n,len(sample_pool)))
                for c, accounts in random_at.items():
                    for kind in ("A","B"):
                        accounts[kind][i].advance(t,n,[find(kind,x,c,leverage) for x in picks],flag)

        def random_summary(accounts):
            rows = [a.finish() for a in accounts]
            gains = [r["gain"] for r in rows]
            return {"mean":mean(gains),"percentile":percentile(gains,p["random_percentile"]),
                    "gains":gains,"mean_flagged_share_pct":mean(r["flagged_share_pct"] for r in rows)}

        random_costs = {str(c):{kind:random_summary(accounts) for kind,accounts in pair.items()}
                        for c,pair in random_at.items()}
        btc_costs = {str(c):bitcoin(data,start,finish,c/10_000,p) for c in costs}
        years[str(yr)] = {
            "start":utc(start).isoformat(),"end":utc(finish).isoformat(),
            "weeks":weekly,
            "duplicate_pair_weeks":sum(w["duplicate_pair_count"] > 0 for w in weekly),
            "fixed":{kind if c == base else f"{kind}_cost_{c}":a.finish()
                     for (kind,c,l),a in fixed.items()},
            "random":random_costs[str(base)],"random_costs":random_costs,
            "BTC":btc_costs[str(base)],"BTC_costs":btc_costs,
        }
    return {"years":years,"judgment":{kind:judge(years,kind,p) for kind in ("A","B")},
            "diagnostics":{"duplicate_pair_weeks":sum(y["duplicate_pair_weeks"] for y in years.values())}}


def judge(years, kind, p):
    eligible, above, qualifiers, falling = [], [], [], []
    for year,row in years.items():
        strat, bench = row["fixed"][kind],row["fixed"]["all"]["gain"]
        if (strat["trades"] < p["min_trades_per_year"] or
            strat["flagged_share_pct"] > p["max_flagged_share_pct"]):
            continue
        eligible.append(year)
        if strat["gain"] > bench:
            above.append(year)
            if strat["gain"] > row["random"][kind]["percentile"]:
                qualifiers.append(year)
                if bench < 0:
                    falling.append(year)
    supported = len(qualifiers) >= p["min_years_above"] and bool(falling)
    paid_when_up = bool(above) and all(years[y]["fixed"]["all"]["gain"] > 0 for y in above)
    return {"finding":"supported" if supported else "paid only when coins rose" if paid_when_up else "not paid",
            "eligible":eligible,"above_all":above,"above_both":qualifiers,"above_both_falling":falling}
