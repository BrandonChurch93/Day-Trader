"""Point-in-time admission from dated, counts-only identity evidence."""
from collections import Counter
from dataclasses import replace
from datetime import date

try:
    from . import common_13 as C, fetch_16 as F
except ImportError:
    import common_13 as C
    import fetch_16 as F


def status_at(row,t):
    if row["notice_status"] == "REMOVED":
        return "REMOVED"
    m = n = 0
    monday = F.F.utc(t).date().isoformat()
    if row.get("start_from_utc","")>monday:
        return "UNKNOWN"
    if "notice_end_utc" in row and t>=F.F.boundary(row["notice_end_utc"],10**12):
        return "REMOVED"
    for page,day_end,matched in row["months"]:
        if page <= monday and day_end <= t:
            n += 1
            m += matched
    if n and 5*m >= 4*n:
        return "CONFIRMED"
    if n>=3 and 2*m<n:
        return "REMOVED"
    if row["notice_status"] == "CONFIRMED" and row["notice_at"] and row["notice_at"] <= monday:
        return "CONFIRMED"
    return "UNKNOWN"


class DatedPairs(set):
    def __init__(self,floors):
        super().__init__()
        self.floors = floors


def asset_floor(pairs,i,s):
    return getattr(pairs,"floors",{}).get((i,s),-10**12)


def bound_asset(a,pairs):
    start = asset_floor(pairs,a.coin,a.pair)
    return replace(a,begin=start) if start>a.begin else a


class Timeline:
    def __init__(self,info,cutoff):
        self.cutoff = cutoff
        rows = info["as_of_rows"]
        self.baseline = {(r["market"],r["id"],r["pair"]):r for r in rows}
        if len(self.baseline)!=len(rows):
            raise ValueError("duplicate dated identity mapping")
        cutoff_date = F.F.utc(cutoff).date().isoformat()
        for r in rows:
            days = set()
            start = F.F.boundary(r.get("start_from_utc"),-10**12)
            for page,day_end,hit in r["months"]:
                date.fromisoformat(page)
                if (page>cutoff_date or not start+86400<=day_end<=cutoff or type(hit) is not bool
                    or day_end%86400 or page[:7] in days):
                    raise ValueError("invalid or post-cutoff dated identity evidence")
                days.add(page[:7])
            if r["notice_at"] is not None:
                date.fromisoformat(r["notice_at"])
        self.cache = {}
        self.floors = {m:{(r["id"],r["pair"]):F.F.boundary(r["start_from_utc"],0)
                         for r in rows if r["market"]==m and "start_from_utc" in r}
                       for m in ("spot","futures")}

    def states(self,t):
        if t>self.cutoff:
            raise ValueError("identity requested after scoring cutoff")
        if t not in self.cache:
            self.cache[t] = {k:status_at(r,t) for k,r in self.baseline.items()}
        return self.cache[t]

    def at(self,t):
        answer = {m:DatedPairs(floors) for m,floors in self.floors.items()}
        for (market,i,symbol),status in self.states(t).items():
            if status=="CONFIRMED":
                answer[market].add((i,symbol))
        return answer

    def admitted(self,params):
        admitted = {"spot":set(),"futures":set()}
        for _,start,end in C.year_windows(params):
            for t in range(start,end,C.WEEK):
                for market,pairs in self.at(t).items():
                    admitted[market].update(pairs)
        return admitted


def week_allowlist(identity,t):
    if identity is None:
        return None,None
    policy = identity.at(t) if isinstance(identity,Timeline) else identity
    return policy["spot"],policy["futures"]


def compare_counts(timeline,snapshots,params):
    """Compare active ID-market coin-weeks with the old all-month baseline."""
    def roll(states):
        return next((s for s in ("CONFIRMED","REMOVED","UNKNOWN") if s in states),"NO_ARCHIVE")
    result = {}
    for sample,rows in snapshots.items():
        result[sample] = {}
        for year,start,end in C.year_windows(params):
            stats = {m:Counter({"changed":0}) for m in ("spot","futures")}
            for t in range(start,end,C.WEEK):
                snap = next((s for s in reversed(rows) if s["kept"] and s["known_at"]<=t),None)
                if snap is None:
                    continue
                current = timeline.states(t)
                for r in snap["kept"]:
                    cid = r["id"]
                    markets = {"spot":[(lo,hi,s) for lo,hi,s in F.spot_segments(r)],
                               "futures":[(a.begin,a.end,a.pair) for a in F.perp_segments(r)]}
                    for market,segs in markets.items():
                        keys = [(market,cid,s) for lo,hi,s in segs if lo<=t<hi
                                and (market,cid,s) in timeline.baseline]
                        old = roll({timeline.baseline[k]["all_month_status"] for k in keys})
                        new = roll({current[k] for k in keys})
                        if old != new:
                            stats[market]["changed"] += 1
                            stats[market][old+"_to_"+new] += 1
            result[sample][str(year)] = {m:dict(c) for m,c in stats.items()}
    return result
