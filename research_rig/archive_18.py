"""Offline Plan 18 adapter for the existing public Binance bulk ZIP store."""
from array import array
from collections import defaultdict
import csv
from dataclasses import replace
from datetime import date,datetime,timedelta,timezone
import gzip
from hashlib import sha256
import io
import json
import math
import re
import zipfile

from . import common_18 as C

VENUES = ("robinhood","kalshi","coinbase","kraken")
ROSTER_KEYS = ("symbol","ticker","product_id","symbol")
ROSTER_HASHES = dict(zip(VENUES,(
    "da16e79084aa13d52193379872009bdc1c2759fe6234ff08375d501bf20c9edf",
    "927fa60821a3534a7f8b38579028f50f017fcfaafea0c42d3dcb7871b1651005",
    "36f4307cd753211de9b1a7363190fb02ef1ccf0a5dbef41bb0992a9d26bdcade",
    "0971651ed4ace539e88de36a5516c75a00e3ef7f0c4c2f401843af1215938d29")))
BULK = re.compile(r"data/futures/um/(daily|monthly)/(klines|markPriceKlines|fundingRate)/([A-Z0-9]+)/(?:1h/)?([A-Za-z0-9-]+)\.zip")
SHA = re.compile(r"[0-9a-f]{64}")
NAN = float("nan")


def digest(blob):
    return sha256(blob).hexdigest()


def read_pinned(path,expected):
    if not SHA.fullmatch(expected) or path.is_symlink():
        raise C.Incomplete(f"invalid pin or symlink: {path.name}")
    blob = path.read_bytes()
    if digest(blob)!=expected:
        raise C.Incomplete(f"input hash mismatch: {path.name}")
    return blob


def day_hour(d):
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp()//C.H)


def parse_snapshots(rows, contracts, p):
    snaps, seen, holes = [],set(),[]
    for row in rows:
        d = date.fromisoformat(row["date"])
        assumed = (day_hour(d.isoformat())+24)*C.H
        if row["known_at"]!=assumed or d in seen:
            raise C.Incomplete("invalid saved snapshot timing or duplicate")
        seen.add(d)
        if row.get("hole"):
            holes.append(str(d))
            continue
        if not SHA.fullmatch(row["sha256"]):
            raise C.Incomplete("snapshot raw evidence has no pin")
        ranks = tuple(sorted((r["cmcRank"],r["id"]) for r in row["top_raw"]))
        if (len({i for _,i in ranks})!=len(ranks) or len({r for r,_ in ranks})!=len(ranks)
            or any(type(r) is not int or type(i) is not int or min(r,i)<1 for r,i in ranks)
            or tuple(r for r,_ in ranks if r<=p["top_rank"])!=tuple(range(1,p["top_rank"]+1))):
            raise C.Incomplete(f"historical page must contain unique ranks and IDs, including every judged rank: {d}")
        snaps.append(C.Snapshot(assumed,contracts,ranks))
    if not snaps:
        raise C.Incomplete("no usable historical rank pages")
    return tuple(snaps), sorted(holes)


def verify_rank_pages(rows,directory,p):
    for row in rows:
        if row.get("hole"):
            continue
        path = directory/(row["date"].replace("-","")+".html.gz")
        html = gzip.decompress(read_pinned(path,row["sha256"])).decode().replace('\\"','"')
        start = re.search(r'"listingHistorical"\s*:\s*\{\s*"data"\s*:\s*(?=\[)',html)
        if start is None:
            raise C.Incomplete("pinned historical page lacks a listing")
        records,_ = json.JSONDecoder().raw_decode(html[start.end():])
        expected = sorted((r["cmcRank"],r["id"]) for r in row["top_raw"] if r["cmcRank"]<=p["top_rank"])
        actual = sorted((r["cmcRank"],r["id"]) for r in records if r["cmcRank"]<=p["top_rank"])
        if expected!=actual:
            raise C.Incomplete("saved top ranks differ from their pinned raw page")


def catalogue(raw):
    if raw.get("version")!=1 or raw.get("scope")!="reconstructed_verified_subset":
        raise C.Incomplete("unexpected universe provenance scope")
    contracts, symbols, keys, notices = [],{},set(),set()
    for row in raw["contracts"]:
        cid,pair,beg,end,known,close,close_known=(row[k] for k in (
            "coin_id","symbol","begin","end","listed_known_at","closed_effective","closed_known_at"))
        key = f"{cid}/{pair}/{beg}"
        if (any(type(v) is not int for v in (cid,beg,end,known)) or cid<=0 or beg>=end or key in keys
            or not re.fullmatch("[A-Z0-9]+USDT",pair) or not SHA.fullmatch(row["listing_evidence_sha256"])
            or (close is None)!=(close_known is None)
            or (close is not None and (type(close_known) is not int or type(close) is not int or close<=beg
                or not SHA.fullmatch(row["closure_evidence_sha256"])))):
            raise C.Incomplete("invalid dated listing evidence row")
        if row.get("delisting_notice") is True:
            if close is None:
                raise C.Incomplete("terminal claim has no dated delisting evidence")
            notices.add(key)
        keys.add(key)
        contracts.append(C.Contract(cid,0,key,beg,end,known,close,close_known))
        symbols[key] = pair
    spans = defaultdict(list)
    for c in contracts:
        spans[symbols[c.key]].append((c.begin,c.end))
    for pair,raw_spans in spans.items():
        ordered = sorted(raw_spans)
        if any(a[1]>b[0] for a,b in zip(ordered,ordered[1:])):
            raise C.Incomplete(f"overlapping accounting identity fences for {pair}")
    return tuple(contracts),symbols,notices


def roster_map(raw, sources):
    mapped, counts = {},{}
    if set(raw)!=set(VENUES) or set(sources)!=set(VENUES):
        raise C.Incomplete("the four separate US roster inputs are required")
    for venue,field in zip(VENUES,ROSTER_KEYS):
        expected = [r[field] for r in sources[venue]["contracts"]]
        if len(set(expected))!=len(expected) or sources[venue]["count"]!=len(expected):
            raise C.Incomplete("duplicate or incomplete original US roster")
        if set(raw[venue])!=set(expected):
            raise C.Incomplete("US roster mapping must address every original contract")
        ids = []
        for code,item in raw[venue].items():
            cid = item["coin_id"]
            if cid is not None:
                if type(cid) is not int or cid<=0 or not SHA.fullmatch(item["evidence_sha256"]):
                    raise C.Incomplete("unverified US contract identity")
                ids.append(cid)
            elif not item.get("reason"):
                raise C.Incomplete("unmapped US contract needs a reason")
        if len(set(ids))!=len(ids):
            raise C.Incomplete("ambiguous duplicate US exposure")
        mapped[venue] = set(ids)
        counts[venue] = dict(original=len(expected),mapped=len(ids),
                              unmatched={k:v["reason"] for k,v in raw[venue].items() if v["coin_id"] is None})
    return mapped,counts


def archive_span(match):
    freq,kind,pair,stem = match.groups()
    prefix = pair+"-"+("fundingRate-" if kind=="fundingRate" else "1h-")
    day = stem.removeprefix(prefix)
    pat = r"\d{4}-\d{2}" if freq=="monthly" else r"\d{4}-\d{2}-\d{2}"
    if ((kind!="fundingRate")!=("/1h/" in match[0]) or
        not stem.startswith(prefix) or not re.fullmatch(pat,day)):
        raise C.Incomplete("unsupported archive period or bar size")
    d = date.fromisoformat(day+("-01" if freq=="monthly" else ""))
    e = (d.replace(day=28)+timedelta(days=4)).replace(day=1) if freq=="monthly" else d+timedelta(days=1)
    return day_hour(d.isoformat()),day_hour(e.isoformat())


def clock(raw):
    v = int(raw)
    if v>=10**14:
        return v/10**6
    if v>=10**11:
        return v/1000
    return float(v)


def zip_rows(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member, = [name for name in z.namelist() if name.endswith(".csv")]
        with z.open(member) as stream:
            for i,row in enumerate(csv.reader(io.TextIOWrapper(stream,encoding="utf-8-sig"))):
                if row and row[0].isdigit():
                    yield row
                elif i>0:
                    raise C.Incomplete("invalid archive row")


class Tape:
    def __init__(self, archive_dir, manifests, symbols, notices, p, *, contracts=(), check=lambda:None):
        self.lo = p["start"]-p["lookback_hours"]-p["funding_interval_hours"]*p["funding_lag_intervals"]
        self.hi = p["end"]
        self.symbols,self.notices,self.p = symbols,notices,p
        self.by_coin = defaultdict(list)
        for c in contracts:
            self.by_coin[c.coin_id].append(c)
        self.store = {}
        groups = defaultdict(dict)
        wanted = set(symbols.values())
        for manifest in manifests:
            if manifest["errors"]:
                raise C.Incomplete("archive manifest has reported errors")
            for name,m in manifest["archives"].items():
                match = BULK.fullmatch(name)
                if match is None:
                    raise C.Incomplete("archive manifest contains an unsupported path")
                if match[3] not in wanted:
                    continue
                if name in groups[match[3]] and groups[match[3]][name][1]!=m:
                    raise C.Incomplete("conflicting archive manifests")
                groups[match[3]][name] = match,m
        for pair,items in groups.items():
            check()
            count = self.hi-self.lo+1
            opens,closes,marks,rates = (array("d",[NAN])*count for _ in range(4))
            times = array("f",[NAN])*count  # exact subsecond offset from the grid where available
            coverage = bytearray(count)
            for name,(match,m) in sorted(items.items()):
                lo,hi = archive_span(match)
                if hi<=self.lo or lo>self.hi:
                    continue
                if m["where"]!="replay_16":
                    raise C.Incomplete("venue input is not in the pinned Plan 16 bulk store")
                kind = match[2]
                if kind=="fundingRate":
                    a,b = max(lo,self.lo)-self.lo,min(hi,self.hi+1)-self.lo
                    if any(coverage[a:b]):
                        raise C.Incomplete("overlapping funding coverage")
                    coverage[a:b] = b"\x01"*(b-a)
                n = 0
                for row in zip_rows(read_pinned(archive_dir/name,m["sha256"])):
                    n += 1
                    stamp = clock(row[0])
                    h = round(stamp/C.H)
                    err = stamp-h*C.H
                    if abs(err)>(p["funding_jitter_seconds"] if kind=="fundingRate" else 0) or not lo<=h<hi:
                        raise C.Incomplete("archive event timestamp out of its permitted hour or file")
                    if not self.lo<=h<=self.hi:
                        continue
                    i = h-self.lo
                    if kind=="fundingRate":
                        v = float(row[2])
                        if not math.isfinite(v) or not math.isnan(rates[i]):
                            raise C.Incomplete("duplicate or malformed settlement")
                        rates[i],times[i] = v,err
                    else:
                        op,tr = float(row[1]),float(row[4])
                        vol = float(row[5]) if kind=="klines" else 1.
                        if not C.valid(op) or not C.valid(tr) or not math.isfinite(vol) or vol<0:
                            raise C.Incomplete("malformed trade or mark bar")
                        dest = closes if kind=="klines" else marks
                        if not math.isnan(dest[i]):
                            raise C.Incomplete("duplicate hourly bar")
                        dest[i] = tr if vol>0 else -1.
                        if kind=="klines" and vol>0:
                            opens[i] = op
                if n!=m["n"]:
                    raise C.Incomplete("unexpected archive row count")
            last = next((self.lo+i for i in range(len(closes)-1,-1,-1) if closes[i]>0),None)
            self.store[pair] = opens,closes,marks,rates,times,coverage,last

    def get(self,key,h,index):
        row = self.store.get(self.symbols[key])
        if row is None or not self.lo<=h<=self.hi:
            return None
        return row[index][h-self.lo]

    def open_price(self,key,h):
        return self.get(key,h,0)

    def trade_close(self,key,h):
        return self.get(key,h,1)

    def mark_close(self,key,h):
        return self.get(key,h,2)

    def traded(self,key,h):
        return C.valid(self.trade_close(key,h))

    def funding(self,key,h):
        v = self.get(key,h,3)
        if v is None or not self.get(key,h,5):
            return False,None
        return True,None if math.isnan(v) else v

    def rank_funding(self,key,h,decision_seconds):
        covered,v = self.funding(key,h)
        lag = self.p["funding_interval_hours"]*self.p["funding_lag_intervals"]*C.H
        if v is not None and h*C.H+self.get(key,h,4)+lag>=decision_seconds:
            return False,None
        return covered,v

    def terminal(self,c,h,last_h):
        row = self.store.get(self.symbols[c.key])
        if (c.key not in self.notices or c.closed_effective>self.hi
            or c.closed_known_at>self.hi*C.H or row is None):
            return False
        for segment in self.by_coin[c.coin_id]:
            store = self.store.get(self.symbols[segment.key])
            lo,hi = max(last_h+1,self.lo,segment.begin),min(self.hi+1,segment.end)
            if lo<hi and (store is None or any(x>0 for x in store[1][lo-self.lo:hi-self.lo])):
                return False
        return True


def load(paths,pins,archive_dir,p,*,evidence_dir,check=lambda:None):
    rows = {k:json.loads(read_pinned(paths[k],pins[k])) for k in pins}
    u = rows["universe"]
    if u["rank_source_sha256"]!=pins["ranks"] or u["archive_manifests"]!={
            k:pins[k] for k in ("viewed_manifest","held_manifest")}:
        raise C.Incomplete("universe provenance does not match rank or archive pins")
    contracts,symbols,notices = catalogue(u)
    rank_rows = [r for r in rows["ranks"]
                 if (p["start"]-p["max_snapshot_age_days"]*24)*C.H<=r["known_at"]<p["end"]*C.H]
    snaps,holes = parse_snapshots(rank_rows,contracts,p)
    verify_rank_pages(rank_rows,paths["ranks"].parent/"cmc",p)
    mapped,counts = roster_map(u["us_rosters"],{v:rows[v] for v in VENUES})
    wanted = {i for s in snaps for r,i in s.ranks if r<=p["top_rank"]}.union(*mapped.values())
    contracts = tuple(c for c in contracts if c.coin_id in wanted)
    symbols = {c.key:symbols[c.key] for c in contracts}
    snaps = tuple(replace(s,contracts=contracts) for s in snaps)
    represented = {c.coin_id for c in contracts}
    top = {i for s in snaps for r,i in s.ranks if r<=p["top_rank"]}
    gaps = u["unmatched_judged_ids"]
    if set(gaps)!={str(i) for i in top-represented} or not all(gaps.values()):
        raise C.Incomplete("every unmapped historical top-rank ID must have an exclusion reason")
    terminal_ids = {c.coin_id for c in contracts if c.key in notices}
    evidence = {r[k] for r in u["contracts"] for k in ("listing_evidence_sha256","closure_evidence_sha256")
                if r.get(k)}
    evidence.update(x["evidence_sha256"] for roster in u["us_rosters"].values()
                    for x in roster.values() if x["coin_id"] is not None)
    for sha in sorted(evidence):
        if not SHA.fullmatch(sha):
            raise C.Incomplete("malformed catalogue evidence digest")
        read_pinned(evidence_dir/sha,sha)
    coverage = dict(scope=u["scope"],historical_top_ids=len(top),
                    top_ids_with_dated_mapping=len(top&represented),unmatched_judged_ids=gaps,
                    top_ids_with_evidenced_delisting=len(top&terminal_ids),
                    full_market_dead_coin_retention=None,missing_saved_rank_pages=holes,us_rosters=counts,
                    rank_availability="saved historical page, conservatively next UTC day; revision history unknown",
                    funding_availability="finalized archive rate, full-interval lag; publication and revisions unknown",
                    us_roster_membership_looks_ahead=True)
    tape = Tape(archive_dir,[rows[k] for k in ("viewed_manifest","held_manifest")],symbols,notices,p,
                contracts=contracts,check=check)
    archive_ids = {c.coin_id for c in contracts if symbols[c.key] in tape.store}
    coverage["top_ids_with_any_archive"] = len(top&archive_ids)
    for v,ids in mapped.items():
        counts[v]["with_any_archive"] = len(ids&archive_ids)
    return tape,snaps,mapped,coverage
