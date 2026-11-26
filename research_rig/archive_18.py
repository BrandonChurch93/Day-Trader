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
MEMORY_CAP = 300_000_000
WORK_RESERVE = 130_000_000
MAX_ZIP_BYTES = 8_000_000


def digest(blob):
    return sha256(blob).hexdigest()


def json_digest(value):
    return digest(json.dumps(value,sort_keys=True,separators=(",",":")).encode())


def read_pinned(path,expected):
    if not SHA.fullmatch(expected) or path.is_symlink():
        raise C.Incomplete(f"invalid pin or symlink: {path.name}")
    blob = path.read_bytes()
    if digest(blob)!=expected:
        raise C.Incomplete(f"input hash mismatch: {path.name}")
    return blob


def day_hour(d):
    return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp()//C.H)


def expected_rank_dates(p):
    """First Sundays, independent of what is present in the rank cache."""
    dt = lambda h: datetime.fromtimestamp(h*C.H,timezone.utc).date()
    d = dt(p["start"]-p["max_snapshot_age_days"]*24).replace(day=1)
    end = dt(p["end"])
    while d<end:
        sunday = d+timedelta(days=(6-d.weekday())%7)
        known = day_hour(str(sunday))+24
        if p["start"]-p["max_snapshot_age_days"]*24<=known<p["end"]:
            yield str(sunday)
        d = (d.replace(day=28)+timedelta(days=4)).replace(day=1)


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


def migration_links(raw):
    result = {}
    for id_string,row in raw.get("migration_links",{}).items():
        if not re.fullmatch(r"[1-9][0-9]*",id_string):
            raise C.Incomplete("invalid migration alias")
        cid = int(id_string)
        lineage,effective = row.get("lineage_id"),row.get("effective_hour")
        if (type(lineage) is not int or type(effective) is not int or min(lineage,effective)<=0
            or lineage==cid or str(lineage) in raw["migration_links"]):
            raise C.Incomplete("invalid or chained migration")
        result[cid] = lineage,effective
    return result


def catalogue(raw):
    if raw.get("version")!=1 or raw.get("scope")!="reconstructed_verified_subset":
        raise C.Incomplete("unexpected universe provenance scope")
    contracts, symbols, keys, notices = [],{},set(),set()
    links = migration_links(raw)
    for row in raw["contracts"]:
        cid,pair,beg,end,known,close,close_known=(row[k] for k in (
            "coin_id","symbol","begin","end","listed_known_at","closed_effective","closed_known_at"))
        key = f"{cid}/{pair}/{beg}/{end}"
        if (any(type(v) is not int for v in (cid,beg,end,known)) or min(cid,beg,known)<=0 or beg>=end or key in keys
            or not re.fullmatch("[A-Z0-9]+USDT",pair) or not SHA.fullmatch(row["listing_evidence_sha256"])
            or type(row.get("delisting_notice")) is not bool or (close is None)!=(close_known is None)
            or (close is not None and (type(close_known) is not int or type(close) is not int or close<=beg
                or not SHA.fullmatch(row["closure_evidence_sha256"])))
            or (close is None and row.get("closure_evidence_sha256") is not None)):
            raise C.Incomplete("invalid dated listing evidence row")
        if row.get("delisting_notice") is True:
            if close is None or close>end:
                raise C.Incomplete("terminal claim has no dated delisting evidence")
            notices.add(key)
        keys.add(key)
        lineage,effective = links.get(cid,(cid,beg))
        if beg<effective:
            raise C.Incomplete("successor segment predates its documented migration")
        contracts.append(C.Contract(lineage,0,key,beg,end,known,close,close_known))
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
                              original_products=sorted(expected),
                              mapped_products={k:v["coin_id"] for k,v in raw[venue].items()
                                               if v["coin_id"] is not None},
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


def clock_us(raw):
    v = int(raw)
    if v>=10**14:
        return v
    if v>=10**11:
        return v*1000
    return v*10**6


def check_memory_budget(groups,count):
    # Four double arrays, one signed int32 (microseconds), and one coverage byte.
    # Reserve separately for Python, manifests, one compressed ZIP and results.
    size = len(groups)*(count*37+4096)+WORK_RESERVE
    if size>MEMORY_CAP:
        raise C.Incomplete("Plan 18 archive allocation exceeds the preflight budget")
    return size


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
        self.segments = {c.key:c for c in contracts}
        by_pair = defaultdict(list)
        for c in contracts:
            by_pair[symbols[c.key]].append(c)
        for pair in set(symbols.values()):
            by_pair[pair].sort(key=lambda c:c.begin)
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
        count = self.hi-self.lo+1
        self.budget_bytes = check_memory_budget(groups,count)
        for pair,items in groups.items():
            check()
            opens,closes,marks,rates = (array("d",[NAN])*count for _ in range(4))
            times = array("i",[0])*count
            coverage = bytearray(count)
            for name,(match,m) in sorted(items.items()):
                lo,hi = archive_span(match)
                if hi<=self.lo or lo>self.hi:
                    continue
                if m["where"]!="replay_16":
                    raise C.Incomplete("venue input is not in the pinned Plan 16 bulk store")
                kind = match[2]
                n = 0
                if (archive_dir/name).stat().st_size>MAX_ZIP_BYTES:
                    raise C.Incomplete("archive ZIP exceeds the preflight per-file limit")
                for row in zip_rows(read_pinned(archive_dir/name,m["sha256"])):
                    n += 1
                    stamp = clock_us(row[0])
                    hour_us = C.H*10**6
                    h = (stamp+hour_us//2)//hour_us
                    err = stamp-h*hour_us
                    in_period = lo<=h<hi
                    if kind=="fundingRate":
                        in_period = in_period or lo*hour_us<=stamp<hi*hour_us
                    if abs(err)>(p["funding_jitter_seconds"]*10**6 if kind=="fundingRate" else 0) or not in_period:
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
            previous = None
            last_owner = None
            for i,v in enumerate(rates):
                if math.isnan(v):
                    continue
                stamps = (self.lo+i)*C.H*10**6+times[i]
                owner = next((c for c in by_pair[pair]
                              if c.begin*C.H*10**6<=stamps<c.end*C.H*10**6),None)
                if owner is None and by_pair[pair]:
                    previous = last_owner = None
                    continue
                coverage[i] = 1
                if previous is not None and owner==last_owner and i-previous<=p["funding_interval_hours"]:
                    for j in range(previous+1,i):
                        coverage[j] = 1 if (self.lo+j)%p["funding_interval_hours"] else 2
                previous,last_owner = i,owner
            last = next((self.lo+i for i in range(len(closes)-1,-1,-1) if closes[i]>0),None)
            self.store[pair] = opens,closes,marks,rates,times,coverage,last

    def get(self,key,h,index):
        c = self.segments.get(key)
        if c is not None and not c.begin<=h<c.end:
            return None
        return self.raw_at(key,h,index)

    def raw_at(self,key,h,index):
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
        return self.funding_event(key,h)[:2]

    def funding_event(self,key,h):
        value = self.raw_at(key,h,3)
        if value is None or self.raw_at(key,h,5)!=1:
            return False,None,0.
        rate = None if math.isnan(value) else value
        offset_us = self.raw_at(key,h,4) if rate is not None else 0
        c = self.segments.get(key)
        if c is not None and not c.begin*C.H*10**6<=h*C.H*10**6+offset_us<c.end*C.H*10**6:
            return False,None,0.
        return True,rate,offset_us

    def funding_gap_reason(self,key,h):
        return ("expected_settlement_missing" if self.get(key,h,5)==2 else
                "funding_uncovered_or_unavailable")

    def rank_funding(self,key,h,decision_seconds):
        covered,v,offset = self.funding_event(key,h)
        lag = self.p["funding_interval_hours"]*self.p["funding_lag_intervals"]*C.H
        if v is not None and (h*C.H+lag)*10**6+offset>=decision_seconds*10**6:
            return False,None
        return covered,v

    def terminal(self,c,h,last_h):
        row = self.store.get(self.symbols[c.key])
        if (c.key not in self.notices or c.closed_effective!=h
            or c.closed_known_at>h*C.H or row is None):
            return False
        # Require observed post-trade clocks, not an array tail of NaNs, before
        # calling an earlier gap terminal. Absence of a proof keeps the last close.
        a,b = max(last_h+1,self.lo),min(h,self.hi)
        if a>b or not all(math.isfinite(x) and x<=0 for x in row[1][a-self.lo:b-self.lo+1]):
            return False
        # Positive rows with no verified later owner are conflicting evidence,
        # not permission to presume all post-announcement data are synthetic.
        pair = self.symbols[c.key]
        other_segments = [s for s in self.segments.values() if s.key!=c.key
                          and self.symbols[s.key]==pair and s.begin>=c.end]
        if any(v>0 and not any(s.begin<=i<s.end for s in other_segments)
               for i,v in enumerate(row[1][b-self.lo+1:],b+1)):
            return False
        for segment in self.by_coin[c.coin_id]:
            store = self.store.get(self.symbols[segment.key])
            lo,hi = max(last_h+1,self.lo,segment.begin),min(self.hi+1,segment.end)
            if lo<hi:
                if store is None:
                    return False
                seen = store[1][lo-self.lo:hi-self.lo]
                if any(not math.isfinite(x) or x>0 for x in seen):
                    return False
        return True

    def observed_coverage(self):
        """Count only loaded rows inside each identity and clipped calendar window."""
        result = {}
        for c in self.segments.values():
            pair = self.symbols[c.key]
            arrays = self.store.get(pair)
            lo,hi = max(self.lo,c.begin),min(self.hi+1,c.end)
            months = {}
            if lo>=hi:
                result[c.key] = months
                continue
            d = datetime.fromtimestamp(lo*C.H,timezone.utc).date().replace(day=1)
            while day_hour(str(d))<hi:
                nxt = (d.replace(day=28)+timedelta(days=4)).replace(day=1)
                first,last = max(lo,day_hour(str(d))),min(hi,day_hour(str(nxt)))
                row = dict(clock_hours=last-first,trade_rows=0,positive_trade_rows=0,
                           mark_rows=0,observed_settlements=0,bracketed_non_events=0,
                           unknown_funding_hours=0)
                if arrays is None:
                    row["unknown_funding_hours"] = last-first
                else:
                    for h in range(first,last):
                        i = h-self.lo
                        row["trade_rows"] += math.isfinite(arrays[1][i])
                        row["positive_trade_rows"] += arrays[1][i]>0
                        row["mark_rows"] += math.isfinite(arrays[2][i])
                        known,rate,_ = self.funding_event(c.key,h)
                        row["observed_settlements"] += known and rate is not None
                        row["bracketed_non_events"] += known and rate is None
                        row["unknown_funding_hours"] += not known
                months[str(d)[:7]] = row
                d = nxt
            result[c.key] = months
        return result


def require_exclusion(row, context):
    if (not isinstance(row,dict) or row.get("classification") not in
        {"identity_unresolved","product_scale_unresolved","non_perpetual_asset",
         "no_dated_listing_evidence","outside_registered_scope","before_dated_listing",
         "archive_proxy_not_mature","between_migration_segments","archive_coverage_unavailable"}
        or not isinstance(row.get("reason"),str) or len(row["reason"].strip())<24
        or not isinstance(row.get("searched"),list) or not row["searched"]
        or not all(isinstance(s,str) and s.startswith("https://") for s in row["searched"])):
        raise C.Incomplete(f"missing specific exclusion evidence: {context}")


def bind_evidence(directory,pin,claim,inventory):
    if not isinstance(pin,str) or not SHA.fullmatch(pin):
        raise C.Incomplete("malformed catalogue evidence digest")
    try:
        record = json.loads(read_pinned(directory/pin,pin))
    except (ValueError,UnicodeError) as exc:
        raise C.Incomplete("catalogue evidence is not a structured source record") from exc
    if (not isinstance(record,dict) or record.get("claim")!=claim
        or not isinstance(record.get("uri"),str) or not record["uri"].startswith("https://")
        or not isinstance(record.get("support"),str) or len(record["support"].strip())<20
        or type(record.get("retrieved_at")) is not int or record["retrieved_at"]<=0):
        raise C.Incomplete(f"source record is not bound to the exact {claim['kind']} claim")
    inventory.add(pin)


def verify_evidence(u, sources, directory):
    inventory = set()
    for cid,(lineage,effective) in migration_links(u).items():
        row = u["migration_links"][str(cid)]
        bind_evidence(directory,row.get("evidence_sha256"),dict(
            kind="migration",coin_id=cid,lineage_id=lineage,effective_hour=effective),inventory)
    for row in u["contracts"]:
        identity = {k:row[k] for k in ("coin_id","symbol","begin","end")}
        if "listing_basis" in row:
            identity["listing_basis"] = row["listing_basis"]
        bind_evidence(directory,row["listing_evidence_sha256"],identity|dict(
            kind="listing",listed_known_at=row["listed_known_at"]),inventory)
        if row["closed_effective"] is not None:
            bind_evidence(directory,row["closure_evidence_sha256"],{k:v for k,v in identity.items() if k!="listing_basis"}|dict(
                kind="closure",**{k:row[k] for k in ("closed_effective","closed_known_at","delisting_notice")}),
                inventory)
    for venue,field in zip(VENUES,ROSTER_KEYS):
        for product in sources[venue]["contracts"]:
            code = product[field]
            row = u["us_rosters"][venue][code]
            if row["coin_id"] is None:
                require_exclusion(row,code)
                continue
            bind_evidence(directory,row["evidence_sha256"],dict(
                kind="us_roster",venue=venue,product_id=code,coin_id=row["coin_id"],
                product_record_sha256=json_digest(product)),inventory)
    for cid,row in u["unmatched_judged_ids"].items():
        require_exclusion(row,cid)
        if "rank_page_exclusions" in u:
            bind_evidence(directory,row.get("evidence_sha256"),dict(
                kind="scope_exclusion",coin_id=int(cid),classification=row["classification"],
                reason=row["reason"]),inventory)
    return json_digest(sorted(inventory))


def first_archive_clocks(manifests, wanted):
    first = {}
    for manifest in manifests:
        for name,meta in manifest["archives"].items():
            match = BULK.fullmatch(name)
            if match is None or match[3] not in wanted:
                continue
            seconds = meta.get("first")
            if type(seconds) is not int or seconds<=0 or meta.get("n",0)<=0:
                continue
            value = seconds,name
            if match[3] not in first or value<first[match[3]]:
                first[match[3]] = value
    return first


def verify_listing_bases(u,manifests,p):
    proxy = [r for r in u["contracts"] if r.get("listing_basis")=="archive_first_plus_30_days"]
    first = first_archive_clocks(manifests,{r["symbol"] for r in proxy})
    for row in u["contracts"]:
        basis = row.get("listing_basis")
        if "rank_page_exclusions" in u and basis not in {"dated_notice","archive_first_plus_30_days"}:
            raise C.Incomplete("listing requires a dated notice or the registered archive proxy")
        if basis!="archive_first_plus_30_days":
            continue
        clock,path = first.get(row["symbol"],(0,""))
        assumed = (clock//86400+p["archive_listing_lag_days"])*86400
        if (not path or row.get("archive_first_seconds")!=clock or row.get("archive_first_path")!=path
            or row["listed_known_at"]!=assumed or row["begin"]*C.H!=assumed):
            raise C.Incomplete("archive listing proxy disagrees with the earliest pinned clock and delay")


def verify_rank_schedule(u,rank_rows,p):
    expected = set(expected_rank_dates(p))
    by_date = {row["date"]:row for row in rank_rows}
    evidence = u.get("rank_periods",{})
    if not expected or set(evidence)!=expected or not set(by_date)<=expected:
        raise C.Incomplete("rank evidence must address the independent first-Sunday schedule")
    holes = []
    for day in sorted(expected):
        raw = by_date.get(day)
        row = evidence[day]
        uri = "https://coinmarketcap.com/historical/"+day.replace("-","")+"/"
        if (not isinstance(row,dict) or row.get("uri")!=uri or "captured_at" not in row
            or (row["captured_at"] is not None and (type(row["captured_at"]) is not int
                or row["captured_at"]<day_hour(day)*C.H))
            or row.get("revision_history")!="unknown"
            or row.get("availability")!="next_utc_day_proxy"):
            raise C.Incomplete(f"missing rank capture provenance: {day}")
        if not raw or raw.get("hole"):
            if row.get("status")!="missing":
                raise C.Incomplete(f"rank hole was not declared: {day}")
            holes.append(day)
        elif row.get("status")!="observed" or row.get("sha256")!=raw["sha256"]:
            raise C.Incomplete(f"rank period is not bound to raw bytes: {day}")
    if len(holes)>p["max_missing_rank_pages"]:
        raise C.Incomplete("missing rank periods exceed the configured limit")
    return holes


def archive_inventory(manifests, wanted, p):
    observed = defaultdict(dict)
    for manifest in manifests:
        for name,m in manifest["archives"].items():
            match = BULK.fullmatch(name)
            if match is None or match[3] not in wanted or m.get("n",0)<=0:
                continue
            lo,hi = archive_span(match)
            if hi<=p["start"]-p["lookback_hours"]-p["funding_interval_hours"]*p["funding_lag_intervals"] or lo>=p["end"]:
                continue
            if (type(m.get("first")) is not int or type(m.get("last")) is not int
                or not (lo*C.H-p["funding_jitter_seconds"]<=m["first"]<=m["last"]<hi*C.H)):
                raise C.Incomplete(f"invalid archive observation clock: {name}")
            clock = m["first"],m["last"],m["n"]
            group = observed[match[3],match[2]]
            if name in group and group[name]!=clock:
                raise C.Incomplete("conflicting archive observation metadata")
            group[name] = clock
    return observed


def period_inventory(contracts,symbols,observed,p):
    """Metadata only: distinguish a calendar label from proof of rows at runtime."""
    indexed = defaultdict(list)
    for (pair,kind), clocks in observed.items():
        for name,clock in clocks.items():
            lo,_ = archive_span(BULK.fullmatch(name))
            month = datetime.fromtimestamp(lo*C.H,timezone.utc).strftime("%Y-%m")
            indexed[pair,kind,month].append(clock)
    result = {}
    for c in contracts:
        months = {}
        start = max(c.begin,p["start"]-p["lookback_hours"]-
                    p["funding_interval_hours"]*p["funding_lag_intervals"])
        end = min(c.end,p["end"])
        d = datetime.fromtimestamp(start*C.H,timezone.utc).date().replace(day=1)
        while day_hour(str(d))<end and start<end:
            key = str(d)[:7]
            nxt = (d.replace(day=28)+timedelta(days=4)).replace(day=1)
            left,right = max(start,day_hour(str(d)))*C.H,min(end,day_hour(str(nxt)))*C.H
            months[key] = {
                kind:("manifest_rows_listed" if any(
                    left<=first<right or left<=last<right
                    for first,last,_ in indexed[symbols[c.key],kind,key])
                    else "unknown_missing_manifest_rows")
                for kind in ("klines","markPriceKlines","fundingRate")}
            d = nxt
        result[c.key] = months
    return result


def inspect_universe(paths,pins,p,*,evidence_dir,inventory_pin):
    """Validate rank/listing/product provenance and inventory metadata only."""
    rows = {k:json.loads(read_pinned(paths[k],pins[k])) for k in pins}
    u = rows["universe"]
    if u["rank_source_sha256"]!=pins["ranks"] or u["archive_manifests"]!={
            k:pins[k] for k in ("viewed_manifest","held_manifest")}:
        raise C.Incomplete("universe provenance does not match rank or archive pins")
    contracts,symbols,notices = catalogue(u)
    rank_rows = [r for r in rows["ranks"]
                 if (p["start"]-p["max_snapshot_age_days"]*24)*C.H<=r["known_at"]<p["end"]*C.H]
    holes = verify_rank_schedule(u,rank_rows,p)
    snaps,_ = parse_snapshots(rank_rows,contracts,p)
    verify_rank_pages(rank_rows,paths["ranks"].parent/"cmc",p)
    mapped,counts = roster_map(u["us_rosters"],{v:rows[v] for v in VENUES})
    links = migration_links(u)
    lineage = lambda i: links.get(i,(i,0))[0]
    mapped = {v:{lineage(i) for i in ids} for v,ids in mapped.items()}
    wanted = {lineage(i) for s in snaps for r,i in s.ranks if r<=p["top_rank"]}.union(*mapped.values())
    contracts = tuple(c for c in contracts if c.coin_id in wanted)
    symbols = {c.key:symbols[c.key] for c in contracts}
    snaps = tuple(replace(s,contracts=contracts,migrations=tuple((i,*x) for i,x in links.items())) for s in snaps)
    represented = {c.coin_id for c in contracts}
    top = {i for s in snaps for r,i in s.ranks if r<=p["top_rank"]}
    gaps = u["unmatched_judged_ids"]
    if set(gaps)!={str(i) for i in top if lineage(i) not in represented}:
        raise C.Incomplete("every unmapped historical top-rank ID must have an exclusion reason")
    if any(c.coin_id not in wanted for c in catalogue(u)[0]):
        raise C.Incomplete("unreferenced contract in the universe")
    if verify_evidence(u,{v:rows[v] for v in VENUES},evidence_dir)!=inventory_pin:
        raise C.Incomplete("catalogue evidence inventory differs from approved inventory")
    manifests = [rows[k] for k in ("viewed_manifest","held_manifest")]
    if "rank_page_exclusions" not in u:
        raise C.Incomplete("missing dated decisions for unrepresented rank positions")
    verify_listing_bases(u,manifests,p)
    observed = archive_inventory(manifests,set(symbols.values()),p)
    periods = period_inventory(contracts,symbols,observed,p)
    if u.get("archive_period_inventory_sha256")!=json_digest(periods):
        raise C.Incomplete("archive period coverage inventory is not pinned")
    def metadata_backed(c, month):
        return all(v=="manifest_rows_listed" for v in periods[c.key].get(month,{}).values()) and month in periods[c.key]
    complete_keys = {c.key for c in contracts if any(metadata_backed(c,m) for m in periods[c.key])}
    page_funnel = {}
    if set(u["rank_page_exclusions"])!={r["date"] for r in rank_rows if not r.get("hole")}:
        raise C.Incomplete("dated decisions must cover exactly the observed rank pages")
    listing_bases = {f"{r['coin_id']}/{r['symbol']}/{r['begin']}/{r['end']}":r["listing_basis"]
                     for r in u["contracts"]}
    for snap in snaps:
        page = {i for r,i in snap.ranks if r<=p["top_rank"]}
        page_hour = snap.known_at//C.H
        # The preliminary page standing in for the start uses observations in
        # the start month; the warmup itself is still independently checked.
        month = datetime.fromtimestamp(max(page_hour,p["start"])*C.H,timezone.utc).strftime("%Y-%m")
        active = {c.coin_id for c in contracts if c.begin<=page_hour<c.end and metadata_backed(c,month)}
        mapped_for_page = {i for i in page if (lineage(i) if page_hour>=links.get(i,(i,0))[1] else i) in active}
        day = datetime.fromtimestamp(snap.known_at-C.H*24,timezone.utc).date().isoformat()
        page_funnel[day] = dict(mapped=len(mapped_for_page),total=len(page),unmapped=sorted(page-mapped_for_page))
        exclusions = u["rank_page_exclusions"][day]
        if set(exclusions)!={str(i) for i in page-mapped_for_page}:
            raise C.Incomplete(f"each unmapped rank appearance needs a dated decision: {day}")
        for cid,row in exclusions.items():
            require_exclusion(row,f"{day}/{cid}")
            if cid in gaps:
                if row!=gaps[cid] or row["classification"] not in {
                        "non_perpetual_asset","outside_registered_scope","archive_coverage_unavailable"}:
                    raise C.Incomplete(f"unresolved or unpinned ranked contract exclusion: {day}/{cid}")
                continue
            alias = int(cid)
            family = [c for c in contracts if c.coin_id==lineage(alias)]
            live = any(c.begin<=page_hour<c.end for c in family)
            earliest = min(family,key=lambda c:c.begin)
            if live and page_hour>=links.get(alias,(alias,0))[1]:
                expected = "archive_coverage_unavailable"
            elif page_hour<earliest.begin:
                expected = ("archive_proxy_not_mature" if listing_bases[earliest.key]=="archive_first_plus_30_days"
                            else "before_dated_listing")
            elif page_hour>=max(c.end for c in family):
                expected = "after_dated_closure"
            else:
                expected = "between_migration_segments"
            if row["classification"]!=expected:
                raise C.Incomplete(f"rank exclusion contradicts segment clocks or inventory: {day}/{cid}")
        if (len(mapped_for_page)/len(page)<p["min_judged_mapped_share"]
            or len(mapped_for_page)<2*p["legs"]):
            raise C.Incomplete("rank period lacks the configured breadth of dated archive mappings")
    if any(not ids or not any(c.coin_id in ids and c.key in complete_keys for c in contracts)
           for ids in mapped.values()):
        raise C.Incomplete("US roster illustration lacks any dated archive mapping")
    terminal_ids = {c.coin_id for c in contracts if c.key in notices}
    coverage = dict(scope=u["scope"],historical_top_ids=len(top),
                    top_ids_with_dated_mapping=sum(lineage(i) in represented for i in top),unmatched_judged_ids=gaps,
                    top_ids_with_evidenced_delisting=len(top&terminal_ids),
                    full_market_dead_coin_retention=None,missing_saved_rank_pages=holes,us_rosters=counts,
                    rank_availability="saved historical page, conservatively next UTC day; revision history unknown",
                    funding_availability="finalized archive rate, full-interval lag; publication and revisions unknown",
                    us_roster_membership_looks_ahead=True)
    coverage["archive_month_labels"] = periods
    coverage["rank_page_mapping"] = page_funnel
    for venue in VENUES:
        products = u["us_rosters"][venue]
        coverage["us_rosters"][venue]["with_dated_segment"] = sum(
            lineage(row["coin_id"]) in represented for row in products.values())
        coverage["us_rosters"][venue]["mapped_but_no_dated_segment"] = sorted(
            code for code,row in products.items() if row["coin_id"] is not None
            and lineage(row["coin_id"]) not in represented)
    coverage["archive_first_plus_30_days_ids"] = sorted({r["coin_id"] for r in u["contracts"]
        if r.get("listing_basis")=="archive_first_plus_30_days"})
    return contracts,symbols,notices,snaps,mapped,coverage,manifests,top


def load(paths,pins,archive_dir,p,*,evidence_dir,inventory_pin,check=lambda:None):
    contracts,symbols,notices,snaps,mapped,coverage,manifests,top = inspect_universe(
        paths,pins,p,evidence_dir=evidence_dir,inventory_pin=inventory_pin)
    tape = Tape(archive_dir,manifests,symbols,notices,p,
                contracts=contracts,check=check)
    coverage["archive_memory_budget_bytes"] = tape.budget_bytes
    coverage["observed_archive_coverage_by_month"] = tape.observed_coverage()
    archive_ids = {c.coin_id for c in contracts if symbols[c.key] in tape.store}
    links = {i:lineage for s in snaps for i,lineage,_ in s.migrations}
    coverage["top_ids_with_any_archive"] = sum(links.get(i,i) in archive_ids for i in top)
    for v,ids in mapped.items():
        coverage["us_rosters"][v]["with_any_archive"] = len(ids&archive_ids)
    return tape,snaps,mapped,coverage
