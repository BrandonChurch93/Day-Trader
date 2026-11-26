"""Plan 36 schema, scheduled quote measurements and score engine; no network."""
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from itertools import groupby
from math import ceil, floor, isfinite, sqrt
from random import Random
from re import fullmatch
from statistics import mean, median, stdev
from zoneinfo import ZoneInfo

FIRST, LAST, BAR_FIRST, BAR_MAX = "2016-01-01", "2026-09-30", "2016-01-04", "2026-10-30"
HOLD, WARM, COOLDOWN = 20, 20, 21
PRICE, ADV, BUDGET = 5.0, 1_000_000, 500.0
RESIDUAL, EXTRA = .0005, .0025
FUNDS = {"IWM", "IJH", "IVV"}
YEARS = tuple(range(2016, 2027))
MONTHS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13) if (y, m) <= (2026, 10))
NS, EPOCH, NY = 1_000_000_000, datetime(1970, 1, 1, tzinfo=timezone.utc), ZoneInfo("America/New_York")
DISPOSITIONS = {"confirmed", "venue_excluded", "venue_unknown", "plan_excluded", "correction_excluded",
                "clock_unknown", "identity_unknown"}
ROUTINES = {"opportunistic", "routine", "mixed", "unclassified"}
RANK = {"split": 0, "cash": 1, "stock_distribution": 2, "settle_cash": 3, "settle_stock": 3}
HARD_ENTRY = {"entry_bar_missing", "quote_missing", "cap_missing", "identity_unknown", "incomplete",
              "bar_warmup_missing", "benchmark_missing", "stock_exit_unresolved"}


class Invalid(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Invalid("P36_" + code)


def fields(row, keys, code):
    need(type(row) is dict and set(row) == set(keys.split()), code)


def number(n, minimum=0, inclusive=False):
    return type(n) in (float, int) and isfinite(n) and (n >= minimum if inclusive else n > minimum)


def text(s, pattern):
    return type(s) is str and fullmatch(pattern, s) is not None


def pin(s):
    return text(s, r"[0-9a-f]{64}")


def source(s):
    return text(s, r"https://[^\s]{1,1500}")


def iso(s):
    need(text(s, r"\d{4}-\d{2}-\d{2}"), "DATE")
    return date.fromisoformat(s)


def stamp(s):
    need(text(s, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z"), "TIMESTAMP")
    dt = datetime.fromisoformat(s[:19] + "+00:00")
    nanos = int(s[20:-1].ljust(9, "0")) if s[19] == "." else 0
    return ((dt - EPOCH).days * 86400 + (dt - EPOCH).seconds) * NS + nanos, dt.astimezone(NY).date().isoformat()


def calendar(obj):
    fields(obj, "calendar version sessions", "CALENDAR")
    need(obj["calendar"] == "XNYS" and obj["version"] == "4.13.3" and type(obj["sessions"]) is list, "CALENDAR")
    days, closes = [], {}
    for row in obj["sessions"]:
        need(type(row) is list and len(row) == 3, "CALENDAR")
        d, a, b = row
        iso(d)
        o, od = stamp(a)
        c, cd = stamp(b)
        need((not days or days[-1] < d) and od == cd == d and o < c, "CALENDAR")
        days.append(d)
        closes[d] = c
    need(len(days) > 20 and days[0] == "2015-12-15" and days[-1] == BAR_MAX, "CALENDAR")
    return days, dict(zip(days, range(len(days)))), closes


def parse_roster(records, days, indexes):
    prior, ids, blocked, rows = None, set(), {}, []
    for row in records:
        fields(row, "id cik class_key ticker batch_date buys disposition security cap routine provenance", "ROSTER")
        r = dict(row)
        d, c, k = r["batch_date"], r["cik"], r["class_key"]
        iso(d)
        need(days[0] <= d <= LAST and text(c, r"[1-9]\d{0,9}") and text(k, r"[_a-z0-9]{1,30}"), "ROSTER")
        need(r["id"] == f"{d}:{c}:{k}" and r["id"] not in ids and (prior is None or prior < (d,c,k)), "ROSTER")
        need(r["ticker"] is None or text(r["ticker"], r"[A-Z0-9./^_-]{1,25}"), "ROSTER")
        need(r["security"] is None or (text(r["security"], r"[A-Za-z0-9._:-]{1,100}") and r["security"] not in FUNDS), "ROSTER")
        need(r["disposition"] in DISPOSITIONS and r["routine"] in ROUTINES and pin(r["provenance"]), "ROSTER")
        status = r["disposition"]
        need(status != "confirmed" or (r["security"] is not None and r["ticker"] is not None), "ROSTER")
        need(status != "identity_unknown" or r["security"] is None, "ROSTER")
        need(type(r["buys"]) is list and 1 <= len(r["buys"]) <= 200, "ROSTER")
        j, buyers, valid, order_total = bisect_right(days, d) - 1, set(), [], 0.0
        for b in r["buys"]:
            fields(b, "accession owner_cik officer director trade_date accepted_utc public_utc shares reported_price venue plan", "BUY")
            a, owner = b["accession"], b["owner_cik"]
            need(text(a, r"\d{10}-\d{2}-\d{6}") and text(owner, r"[1-9]\d{0,9}"), "BUY")
            need(type(b["officer"]) is bool and type(b["director"]) is bool and (b["officer"] or b["director"]), "BUY")
            need((a,owner) not in buyers and b["trade_date"] in indexes, "BUY")
            need(number(b["shares"]) and number(b["reported_price"]) and isfinite(b["shares"]*b["reported_price"]), "BUY")
            need(b["venue"] in {"open_market","private","unknown"} and b["plan"] in
                 {"no_indication","affirmative","historical_unknown","unknown"}, "BUY")
            trade_i = indexes[b["trade_date"]]
            need(0 <= j - trade_i <= 5, "BUY")
            acc, pub = b["accepted_utc"], b["public_utc"]
            if acc is not None and pub is None:
                stamp(acc)
            if pub is not None:
                accepted, accepted_day = stamp(acc)
                public, day = stamp(pub)
                need(accepted <= public and b["trade_date"] <= accepted_day <= day <= d, "BUY_CLOCK")
                if (b["venue"] == "open_market" and b["plan"] in {"no_indication","historical_unknown"}):
                    need(b["plan"] != "historical_unknown" or day < "2023-04-01", "BUY")
                    valid.append((owner, trade_i, day, a, b))
            buyers.add((a,owner))
        keep = [x for x in valid if any(x[0] != y[0] and abs(x[1]-y[1]) <= 2
                                        and max(x[2],y[2]) == d for y in valid)]
        if status in {"confirmed","identity_unknown"}:
            need(keep, "PAIR")
            need(j+1 >= blocked.get((c,k), -1), "COOLDOWN")
            blocked[c,k] = j+1+COOLDOWN
        order_total = sum(x[4]["shares"]*x[4]["reported_price"] for x in keep)
        need(isfinite(order_total), "BUY")
        cap = r["cap"]
        if cap is not None:
            fields(cap, "shares asof accepted_utc source", "CAP")
            _, accepted_day = stamp(cap["accepted_utc"])
            asof = iso(cap["asof"])
            need(number(cap["shares"]) and source(cap["source"]) and asof <= iso(accepted_day) <= iso(days[j+1]), "CAP")
        r.update(start=j+1, amount=order_total, plan_unknown=any(x[4]["plan"]=="historical_unknown" for x in keep),
                 role=("officer_and_director" if any(x[4]["officer"] for x in keep) and any(x[4]["director"] for x in keep)
                       else "officer_only" if any(x[4]["officer"] for x in keep)
                       else "director_only" if keep else "unclassified"))
        prior = d,c,k
        ids.add(r["id"])
        if FIRST <= d:
            rows.append(r)
    need(bool(rows), "ROSTER")
    return rows


def identities(records, indexes):
    by_security, by_symbol = defaultdict(list), defaultdict(list)
    for r in records:
        fields(r, "security symbol from through source", "IDENTITY")
        s,b = r["security"],r["symbol"]
        need(text(s,r"[A-Za-z0-9._:-]{1,100}") and text(b,r"[A-Z0-9./^_-]{1,25}") and source(r["source"]), "IDENTITY")
        iso(r["from"]); iso(r["through"])
        need(r["from"] <= r["through"] and (s not in FUNDS or s == b), "IDENTITY")
        by_security[s].append((r["from"],r["through"],b))
        by_symbol[b].append((r["from"],r["through"],s))
    for group in (by_security,by_symbol):
        for parts in group.values():
            parts.sort()
            need(all(a[1] < b[0] for a,b in zip(parts,parts[1:])), "IDENTITY_OVERLAP")
    return dict(by_security)


def symbol(symbols, s, d):
    return next((b for a,z,b in symbols.get(s,()) if a <= d <= z), None)


def actions(obj, indexes, symbols, marked):
    fields(obj,"coverage actions","ACTIONS")
    coverage, acts, action_ids = defaultdict(list), defaultdict(list), set()
    need(type(obj["coverage"]) is list and type(obj["actions"]) is list, "ACTIONS")
    for r in obj["coverage"]:
        fields(r,"security from through status source","ACTIONS")
        s,a,b = r["security"],r["from"],r["through"]
        need(s in symbols and a in indexes and b in indexes and BAR_FIRST <= a <= b <= marked
             and r["status"] in {"complete","unresolved"} and source(r["source"]), "ACTION_COVERAGE")
        coverage[s].append((a,b,r["status"]))
    for periods in coverage.values():
        periods.sort()
        need(all(a[1] < b[0] for a,b in zip(periods,periods[1:])), "ACTION_COVERAGE")
    for r in obj["actions"]:
        fields(r,"id security date kind amount target source","ACTIONS")
        s,d,k,t = r["security"],r["date"],r["kind"],r["target"]
        need(text(r["id"],r"[A-Za-z0-9._:-]{1,120}") and r["id"] not in action_ids and
             s in symbols and d in indexes and BAR_FIRST <= d <= marked and k in RANK and source(r["source"]), "ACTIONS")
        need(number(r["amount"], inclusive=k in {"cash","settle_cash"}), "ACTION_AMOUNT")
        need((t in symbols and (k != "settle_stock" or t != s)) if k in {"settle_stock","stock_distribution"} else t is None,
             "ACTION_TARGET")
        need(not any(x["kind"] == k for x in acts[s,d]) if k == "split" else True, "ACTION_DUPLICATE")
        need(not any(RANK[x["kind"]] == 3 for x in acts[s,d]) if RANK[k] == 3 else True, "ACTION_DUPLICATE")
        acts[s,d].append(r)
        action_ids.add(r["id"])
    for day in acts.values():
        day.sort(key=lambda r:(RANK[r["kind"]],r["id"]))
    return dict(coverage),dict(acts)


def covered(coverage,s,d):
    return any(a <= d <= z and state=="complete" for a,z,state in coverage.get(s,()))


def planned(rows, days, indexes, marked, acts):
    """Bound market payloads to deduped stock lookbacks and holding/diagnostic dates."""
    needed, qt = defaultdict(set), set()
    top = indexes[marked]
    start = indexes[BAR_FIRST]
    for r in rows:
        if r["disposition"] != "confirmed":
            continue
        i,s = r["start"],r["security"]
        end = min(i+HOLD+1,top)
        needed[s].update(range(max(i-WARM,start),end+1))
        qt.update((s,days[j]) for j in (i,i+1,i+HOLD,i+HOLD+1) if j <= top)
        primary_exits = {j for j in range(i+1,end+1)
                         if any(x["kind"].startswith("settle_") for x in acts.get((s,days[j]),()))}
        visited, pending = {}, [(s,i,end)]
        while pending:
            security, a, b = pending.pop()
            if a>b or visited.get((security,a),-1)>=b:
                continue
            visited[security,a] = b
            for j in range(a+1,b+1):
                for act in acts.get((security,days[j]),()):
                    target = act["target"]
                    if act["kind"].startswith("settle_"):
                        qt.add((security,days[j]))
                    if target and target != security:
                        z = b if act["kind"]=="stock_distribution" else j
                        needed[target].update(range(j,z+1))
                        qt.update((target,days[k]) for k in range(j,z+1)
                                  if k in primary_exits or k in {i+HOLD,i+HOLD+1,j})
                        if z>j:
                            pending.append((target,j,z))
    return needed,qt


def build_bars(records, symbols, days, indexes, marked, requested):
    bars, fund_rows = defaultdict(dict), defaultdict(dict)
    for r in records:
        fields(r,"security symbol date t o h l c v","BAR")
        s,d = r["security"],r["date"]
        need(d in indexes and BAR_FIRST <= d <= marked and symbol(symbols,s,d)==r["symbol"] and r["symbol"] is not None,
             "BAR_IDENTITY")
        target = fund_rows if s in FUNDS else bars
        need((s in FUNDS or indexes[d] in requested.get(s,())) and d not in target[s], "BAR_SCOPE")
        _, r_date = stamp(r["t"])
        need(r_date==d and all(number(r[k]) for k in ("o","h","l","c","v")) and
             r["l"] <= min(r["o"],r["c"]) <= max(r["o"],r["c"]) <= r["h"], "BAR_VALUES")
        target[s][days[indexes[d]]] = (None,None,None,r["c"],r["v"])
    return dict(bars),dict(fund_rows)


def good(q):
    return q is not None and 0 < q[0] < q[1] and q[2]>0 and q[3]>0


def relative(q):
    return (q[1]-q[0])/((q[0]+q[1])/2)


def measure(updates, cutoff):
    """Quote-only calculations: return half-spread, cutoff snapshot and valid nanoseconds."""
    left = cutoff-300*NS
    prev, points, spans = None,[],[]
    for t,q in updates:
        if prev is not None and prev[0] == t:
            points[-1] = t,q
        else:
            points.append((t,q))
        prev = t,q
    for i,(t,q) in enumerate(points):
        until = points[i+1][0] if i+1<len(points) else cutoff
        duration = min(until,t+60*NS,cutoff)-max(t,left)
        if duration>0 and good(q):
            spans.append((relative(q),duration))
    total = sum(d for _,d in spans)
    if not points or total < 180*NS or cutoff-points[-1][0] >= 60*NS or not good(points[-1][1]):
        return None
    sofar = 0
    for spread,duration in sorted(spans):
        sofar += duration
        if 2*sofar >= total:
            return spread/2,points[-1][1],total
    raise AssertionError("unreachable quote median")


def quotes(records, allowed, closes):
    def raw():
        previous = None
        for r in records:
            fields(r,"security date t bid ask bid_size ask_size","QUOTE")
            k = r["security"],r["date"]
            need(k in allowed and k[1] in closes, "QUOTE_SCOPE")
            t,d = stamp(r["t"])
            cutoff = closes[d]-60*NS
            need(d==k[1] and cutoff-360*NS<=t<=cutoff, "QUOTE_CLOCK")
            need(previous is None or previous <= (k,t), "QUOTE_ORDER")
            q = tuple(r[f] for f in ("bid","ask","bid_size","ask_size"))
            need(all(number(x,inclusive=True) for x in q), "QUOTE_VALUES")
            previous = k,t
            yield k,t,q
    return {k:measure(((t,q) for _,t,q in rs),closes[k[1]]-60*NS) for k,rs in groupby(raw(), key=lambda x:x[0])}


def benchmark(r,i,days,closes,bars):
    cap = r["cap"]
    if cap is None:
        return None
    accepted,_ = stamp(cap["accepted_utc"])
    cutoff = closes[days[i]]-60*NS
    old = (iso(days[i])-iso(cap["asof"])).days
    if not (accepted<=cutoff and 0<=old<=180) or days[i-1] not in bars.get(r["security"],{}):
        return None
    value = cap["shares"]*bars[r["security"]][days[i-1]][3]
    need(isfinite(value), "CAP")
    return "IWM" if value<2_000_000_000 else "IJH" if value<10_000_000_000 else "IVV"


def load(manifest, clock, roster_data, identity_data, bar_data, quote_data, action_data):
    """Contracts, price sanity and quote spread measurement only. No return calculations."""
    days,indexes,closes = calendar(clock)
    mark = manifest["bar_through"]
    need(mark in indexes and BAR_FIRST <= mark <= BAR_MAX, "MANIFEST")
    rows = parse_roster(roster_data,days,indexes)
    symbols = identities(identity_data,indexes)
    for r in rows:
        if r["disposition"] == "confirmed":
            need(r["security"] in symbols and symbol(symbols,r["security"],r["batch_date"])==r["ticker"], "ROSTER_IDENTITY")
    coverage,acts = actions(action_data,indexes,symbols,mark)
    requested,quote_scope = planned(rows,days,indexes,mark,acts)
    bars,funds = build_bars(bar_data,symbols,days,indexes,mark,requested)
    fund_scope = defaultdict(set)
    for r in rows:
        if r["disposition"]!="confirmed":
            continue
        i = r["start"]
        f = benchmark(r,i,days,closes,bars)
        if f:
            fund_scope[f].update(days[i:min(i+HOLD+1,indexes[mark])+1])
    need(all(set(tape)<=fund_scope[f] for f,tape in funds.items()), "FUND_SCOPE")
    quote_scope.update((f,days[j]) for r in rows if r["disposition"]=="confirmed"
                       for i in (r["start"],) for f in (benchmark(r,i,days,closes,bars),) if f
                       for j in (i,i+1,i+HOLD,i+HOLD+1) if j<=indexes[mark])
    spreads = quotes(quote_data,quote_scope,closes)
    return rows,days,indexes,closes,mark,bars|funds,spreads,coverage,acts


def entry(i,s,days,mark,bars,spreads,budget=BUDGET):
    d = days[i]
    if d>mark:
        return "incomplete",None
    if i-WARM<bisect_right(days,BAR_FIRST)-1:
        return "left_edge",None
    tape = bars.get(s,{})
    lookback = days[i-WARM:i]
    if any(x not in tape for x in lookback):
        return "bar_warmup_missing",None
    adv = [tape[x][3]*tape[x][4] for x in lookback]
    need(all(isfinite(v) for v in adv), "BAR_VALUES")
    if tape[days[i-1]][3]<PRICE or median(adv)<ADV:
        return "liquidity",None
    q = spreads.get((s,d))
    if q is None:
        return "quote_missing",None
    half,(bid,ask,bids,asks),_ = q
    if (bid+ask)/2<PRICE:
        return "liquidity",None
    n = floor(budget/(ask*(1+RESIDUAL)))
    if not n or min(bids,asks)<n:
        return "liquidity",None
    if d not in tape:
        return "entry_bar_missing",None
    c = tape[d][3]
    if n*c*(1+half+RESIDUAL)>budget:
        return "unfilled_limit",None
    return "filled",(n,c,half)


def payoff(s,i,j,days,bars,spreads,coverage,acts,half,gross=False):
    """One opening share; returns cash, uncosted listed value, spread charges, end index."""
    units,cash,traded,cost = {s:1.0},0.0,0.0,0.0
    def sale(security,d,x):
        if d not in bars.get(security,{}):
            return None
        size = bars[security][d][3]*x
        q = spreads.get((security,d))
        fee = 0 if gross else size*(max(half,q[0] if q else 0)+RESIDUAL)
        return size,fee
    for k in range(i+1,j+1):
        d = days[k]
        addons = defaultdict(float)
        primary = False
        for security in tuple(units):
            if not covered(coverage,security,d):
                return None
            for a in acts.get((security,d),()):
                amount,kind,target = a["amount"],a["kind"],a["target"]
                if kind=="split":
                    units[security] *= amount
                elif kind=="cash":
                    cash += units[security]*amount
                elif kind=="stock_distribution":
                    if target==security:
                        units[security] *= 1+amount
                    else:
                        addons[target] += units[security]*amount
                else:
                    x = units.pop(security)*amount
                    if kind=="settle_cash":
                        cash += x
                    else:
                        p = sale(target,d,x)
                        if p is None:
                            return None
                        traded += p[0]; cost += p[1]
                    if security==s:
                        primary = True
        for target,x in addons.items():
            units[target] = units.get(target,0)+x
        if primary or k==j:
            for security,x in units.items():
                p = sale(security,d,x)
                if p is None:
                    return None
                traded += p[0]; cost += p[1]
            need(all(isfinite(v) for v in (cash,traded,cost)), "ACTION_RANGE")
            return cash,traded,cost,k
    raise AssertionError("nonpositive holding span")


def fund_payoff(f,i,j,days,bars,spreads,coverage,acts):
    if f is None or any(d not in bars.get(f,{}) for d in days[i:j+1]):
        return None
    p = payoff(f,i,j,days,bars,spreads,coverage,acts,0,gross=True)
    if p is None or p[3]!=j:
        return None
    return (p[0]+p[1])/bars[f][days[i]][3]-1


def observation(r,data,delay=0,budget=BUDGET):
    _,days,indexes,closes,mark,bars,spreads,coverage,acts = data
    label = r["disposition"]
    if label!="confirmed":
        return {"status":label}
    i,s = r["start"]+delay,r["security"]
    state,fill = entry(i,s,days,mark,bars,spreads,budget)
    if fill is None:
        return {"status":state}
    n,c,half = fill
    f = benchmark(r,r["start"],days,closes,bars)
    j = i+HOLD
    end = j<=indexes[mark]
    p = payoff(s,i,j,days,bars,spreads,coverage,acts,half) if end else None
    item = {"status":"incomplete" if not end else "stock_exit_unresolved", "filled":True,
            "start":i,"quote_half":half,"basis":c,"per_share":p,"shares":n}
    if p is None:
        item["stress_fund"] = fund_payoff(f,i,j,days,bars,spreads,coverage,acts) if end else None
        return item
    cash,traded,fee,z = p
    net = (cash+traded-fee)/(c*(1+half+RESIDUAL))-1
    item.update(net=net, zero=(cash+traded)/c-1, cost=(fee+c*(half+RESIDUAL))/c,
                harsh=(cash+traded-fee-traded*EXTRA)/(c*(1+half+RESIDUAL+EXTRA))-1)
    f_return = fund_payoff(f,i,z,days,bars,spreads,coverage,acts)
    if f_return is None:
        item["status"] = "cap_missing" if f is None else "benchmark_missing"
        return item
    need(all(isfinite(item[x]) for x in ("net","zero","cost","harsh")) and isfinite(f_return), "RETURN_RANGE")
    item.update(status="paired", fund=f_return, excess=net-f_return)
    return item


def avg(values):
    values = list(values)
    return mean(values) if values else None


def positive(x):
    return x is not None and x>0


def quants(values):
    values = sorted(values)
    return {str(p):values[max(0,ceil(p*len(values))-1)] if values else None for p in (.05,.5,.95)}


def blocks(rows,days):
    weights = {m:[0.0,0] for m in MONTHS}
    for _,x in rows:
        z = weights[days[x["start"]][:7]]
        z[0] += x["excess"]; z[1] += 1
    months = list(weights.values())
    n,rng,sim = len(months),Random(36),[]
    if not rows:
        return None,None
    for _ in range(10_000):
        num,den = 0.0,0
        for j in range(0,n,3):
            p = rng.randrange(n)
            for k in range(min(3,n-j)):
                a,b = months[(p+k)%n]
                num += a; den += b
        if den==0:
            return None,None
        sim.append(num/den)
    return sorted(sim)[499],stdev(sim)


def sequential(rows,data):
    _,days,_,_,mark,_,_,_,_ = data
    cash,last,skips,trades,unknown,active = BUDGET,-1,0,0,0,0
    choices = sorted((r for r in rows if r["disposition"]=="confirmed"),
                     key=lambda r:(r["start"],-r["amount"],int(r["cik"]),r["class_key"]))
    for r in choices:
        i = r["start"]
        if i<=last:
            skips += 1
            continue
        x = observation(r,data,budget=cash)
        if not x.get("filled"):
            continue
        n,c,half = x["shares"],x["basis"],x["quote_half"]
        p = x["per_share"]
        trades += 1
        if p is None:
            unknown += 1
            break
        dist,listed,fee,last = p
        cash += n*(dist+listed-fee-c*(1+half+RESIDUAL))
        active += last-i
    span = bisect_right(days,mark)-bisect_right(days,BAR_FIRST)+1
    return {"net":None if unknown else cash/BUDGET-1,"trades":trades,"overlap_skipped":skips,
            "unvalued_position":unknown,"idle_session_intervals":None if unknown else max(0,span-1-active)}


def reachable(s,i,j,days,bars,coverage,acts):
    """Check action sources and terminal bar presence without valuing any leg."""
    held = {s}
    for k in range(i+1,j+1):
        d = days[k]
        acquired,primary = set(),False
        for security in tuple(held):
            if not covered(coverage,security,d):
                return None
            for a in acts.get((security,d),()):
                kind,target = a["kind"],a["target"]
                if kind=="stock_distribution":
                    if target!=security:
                        acquired.add(target)
                elif kind.startswith("settle_"):
                    held.remove(security)
                    primary |= security==s
                    if kind=="settle_stock" and d not in bars.get(target,{}):
                        return None
        held.update(acquired)
        if primary or k==j:
            return k if all(d in bars.get(x,{}) for x in held) else None
    return None


def assess(data):
    """Readiness only: stage and entry constraints, no payoffs/returns."""
    rows,days,indexes,closes,mark,bars,spreads,coverage,acts = data
    stages = Counter()
    for r in rows:
        stage = r["disposition"]
        if stage=="confirmed":
            i,s = r["start"],r["security"]
            stage,_ = entry(i,s,days,mark,bars,spreads)
            if stage=="filled":
                f = benchmark(r,i,days,closes,bars)
                if i+HOLD>indexes[mark]:
                    stage = "incomplete"
                elif f is None:
                    stage = "cap_missing"
                else:
                    k = reachable(s,i,i+HOLD,days,bars,coverage,acts)
                    if k is None:
                        stage = "stock_exit_unresolved"
                    elif (any(d not in bars.get(f,{}) for d in days[i:k+1]) or
                          reachable(f,i,k,days,bars,coverage,acts)!=k):
                        stage = "benchmark_missing"
                    else:
                        stage = "paired_ready"
        stages[stage] += 1
    return dict(stages)


def evaluate(*data):
    rows,days,_,_,_,_,_,_,_ = data
    records = [(r,observation(r,data)) for r in rows]
    paired = [(r,x) for r,x in records if x["status"]=="paired"]
    unresolved = [(r,x) for r,x in records if x["status"] in HARD_ENTRY]
    attempts = [(r,x) for r,x in records if r["disposition"] in {"confirmed","identity_unknown"} and x["status"]!="left_edge"]
    staged,by_role,by_year,year_n,year_bad,issuer = Counter(),defaultdict(Counter),defaultdict(Counter),Counter(),Counter(),Counter()
    cohort,breadth = defaultdict(list),{}
    for r,x in records:
        y = int(r["batch_date"][:4])
        staged[x["status"]] += 1
        by_year[y][x["status"]] += 1
        by_role[r["role"]][x["status"]] += 1
    for r,_ in attempts:
        year_n[int(r["batch_date"][:4])] += 1
    for r,_ in unresolved:
        year_bad[int(r["batch_date"][:4])] += 1
    yy = defaultdict(list)
    for r,x in paired:
        yy[int(r["batch_date"][:4])].append(x["excess"])
        cohort[r["routine"]].append(x["excess"])
        issuer[r["cik"]] += x["excess"]
    xs = [x["excess"] for _,x in paired]
    mu,stock = avg(xs),avg(x["net"] for _,x in paired)
    low,se = blocks(paired,days)
    worst,count = [],0
    for _,x in records:
        if x["status"]=="stock_exit_unresolved":
            count += 1
            if x["stress_fund"] is not None:
                worst.append(-1-x["stress_fund"])
    stress = avg(xs+worst) if count==len(worst) else None
    ycover = {y:year_bad[y]/year_n[y] if year_n[y] else None for y in YEARS}
    cover = len(unresolved)/len(attempts) if attempts else None
    t1 = avg(sorted(xs)[:-3])
    leader = max(issuer,key=lambda k:(issuer[k],k)) if issuer else None
    t2 = avg(x["excess"] for r,x in paired if r["cik"]!=leader)
    breadth = {y:avg(yy[y]) for y in YEARS}
    loo = {y:avg(x for k in YEARS if k!=y for x in yy[k]) for y in YEARS}
    recent = avg(x for y in YEARS if y>=2020 for x in yy[y])
    marks = {"coverage":cover is not None and cover<=.05 and all(v is None or v<=.10 for v in ycover.values()),
             "count":len(paired)>=500 and len(issuer)>=100,"net_stock":positive(stock),
             "paired_excess":mu is not None and mu>=.0025 and positive(low),"tail":positive(t1) and positive(t2),
             "year_breadth":sum(positive(v) for v in breadth.values())>=7,"recency":positive(recent),
             "leave_one_year_out":all(positive(v) for v in loo.values()),"missing_exits":positive(stress)}
    g,n = len(issuer),len(xs)
    residuals = Counter()
    if n:
        for r,x in paired:
            residuals[r["cik"]] += x["excess"]-mu
    issuer_se = sqrt(g/(g-1)*sum(v*v for v in residuals.values()))/n if g>1 else None
    delayed = [observation(r,data,delay=1) for r in rows]
    delayed_x = [x["excess"] for x in delayed if x["status"]=="paired"]
    break_even = []
    for _,x in paired:
        cash,traded,_,_ = x["per_share"]
        base, target = x["basis"], 1+x["fund"]
        den = traded+base*target
        if den>0:
            break_even.append(2*((cash+traded-base*target)/den-RESIDUAL))
    return {"verdict":"INCONCLUSIVE" if not marks["coverage"] else "PASS" if all(marks.values()) else "NOT_SUPPORTED",
            "marks":marks,"stages":dict(staged),"stage_by_year":dict(by_year),"stage_by_role":dict(by_role),
            "coverage":{"attempts":len(attempts),"unresolved_share":cover,"unresolved_by_year":ycover},
            "paired":{"count":n,"issuers":g,"net":stock,"excess":mu,"block_lower":low,"block_se":se,
                      "block_t":mu/se if se else None,"issuer_se":issuer_se,"issuer_t":mu/issuer_se if issuer_se else None,
                      "trimmed":t1,"without_top_issuer":t2,"by_year":breadth,"loo":loo,"recent":recent,
                      "stress":stress,"unresolved_filled_exits":count},
            "shown":{"routine":{k:{"n":len(cohort[k]),"excess":avg(cohort[k])} for k in sorted(ROUTINES)},
                     "historical_plan_unknown":{"n":sum(r["plan_unknown"] for r,_ in paired),
                                                "excess":avg(x["excess"] for r,x in paired if r["plan_unknown"])},
                     "zero_friction_excess":avg(x["zero"]-x["fund"] for _,x in paired),
                     "extra_cost_excess":avg(x["harsh"]-x["fund"] for _,x in paired),
                     "one_day_delay":{"n":len(delayed_x),"excess":avg(delayed_x)},
                     "entry_full_spread":quants(2*x["quote_half"] for _,x in records if x.get("filled")),
                     "modeled_cost":quants(x["cost"] for _,x in paired),
                     "break_even_constant_full_spread":quants(break_even),
                     "sequential":sequential(rows,data)}}
