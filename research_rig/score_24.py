"""Owner-only one-shot and synthetic calibration, with no live mode in the draft."""
import argparse
from array import array
from bisect import bisect_right
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite, nan
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile
from types import SimpleNamespace

try:
    from . import common_24 as C
except ImportError:
    import common_24 as C

HERE = Path(__file__).resolve().parent
REPO = HERE.parent if HERE.name == "research_rig" else HERE.parents[1]/"dt-work"
DATA = REPO.parent/"rig/data"
RUN = DATA/"replay_24"
FINAL = "PREREG_24_same_coin_carry.md"
DRAFT = "PREREG_24_same_coin_carry_DRAFT.md"
INPUTS = {"universe":"universe_top30.json","ranks":"ranks_top30.json","perp":"perp_top30_manifest.json",
          "spot":"spot_top30_manifest.json","links":"spot_links_top30.json","ftt":"ftt_top30_manifest.json"}
CODE = ("common_24.py","score_24.py","test_24.py")
DEPS = ("archive_18","common_18","fetch_16","fetch_13")
SHA = re.compile(r"[0-9a-f]{64}\Z")
SPOT = re.compile(r"data/spot/(?:monthly|daily)/klines/([A-Z0-9]+USDT)/1h/\1-1h-\d{4}-\d{2}(?:-\d{2})?\.zip\Z")


def policy(raw):
    import yaml
    p = dict(yaml.safe_load(raw)["replay_24_plan"]["value"])
    integer = {"fill_hours","lookback_hours","annual_days","slots","positive_years","draws","seed","initial_usd","entry_min_usd"}
    ratios = {"entry","exit","maintenance","missing_floor","min_annual","min_sharpe","max_drawdown","percentile"}
    if set(p)!=integer|ratios|{"start","end","judged","fees","shown_entry","grid"}:
        raise C.Incomplete("unexpected config keys")
    if any(type(p[k]) is not int or p[k]<=0 for k in integer):
        raise C.Incomplete("expected positive integer config")
    if any(type(p[k]) not in (int,float) or not isfinite(p[k]) or p[k]<=0 for k in ratios):
        raise C.Incomplete("expected positive rate config")
    p["start"],p["end"] = C.hour(p["start"]),C.hour(p["end"])
    if (p["start"]>=p["end"] or p["start"]%24 or p["end"]%24 or p["exit"]>=p["entry"]
            or p["fill_hours"]>=24 or p["maintenance"]>=1 or p["percentile"]>=1
            or p["max_drawdown"]>=1 or sorted(set(p["grid"]))!=p["grid"]
            or not all(type(x) is int and 0<=x<10000 for x in p["grid"])
            or p["judged"] not in p["fees"] or p["fees"][p["judged"]] is None):
        raise C.Incomplete("unsupported config or missing judged fees")
    for name,row in p["fees"].items():
        if row is None:
            continue
        fee = C.Fee(**row)
        for k,v in asdict(fee).items():
            if k=="robinhood_rounding" and type(v) is bool:
                continue
            if type(v) not in (int,float) or not isfinite(v) or v<0 or (k.endswith("_bp") and v>=10000):
                raise C.Incomplete("invalid fee table")
        p["fees"][name] = fee
    return p


def pinned(path,expected):
    if not isinstance(expected,str) or not SHA.fullmatch(expected) or path.is_symlink():
        raise C.Incomplete(f"invalid pin or redirected path: {path}")
    b = path.read_bytes()
    if sha256(b).hexdigest()!=expected:
        raise C.Incomplete(f"changed input: {path}")
    return b


def is_pin(value):
    return isinstance(value,str) and bool(SHA.fullmatch(value))


class InputChecks:
    """Collect one hard refusal per code/path, never echo input values or exceptions."""
    # Decoder libraries may throw multiple exception families for corrupt
    # pinned inputs. Fail closed without exposing a traceback or skipping
    # independently addressable files. Do not swallow interrupts or exits.
    errors = Exception

    def __init__(self):
        self.refused = Counter()
        self.gaps = Counter()
        self.counts = Counter()

    @contextmanager
    def scan(self,code,path):
        self.counts[code+"_checked"] += 1
        try:
            yield
        except self.errors as exc:
            self.refused[code,str(getattr(exc,"path",path))] += 1

    def report(self):
        rows = lambda counter:[dict(code=code,path=path,count=n) for (code,path),n in sorted(counter.items()) if n]
        return dict(counts=dict(self.counts),refusals=rows(self.refused),policy_gaps=rows(self.gaps))


@contextmanager
def scan(checks,code,path):
    if checks is None:
        yield
    else:
        with checks.scan(code,path):
            yield


def terminal_price(row):
    try:
        v = float(row[1])
    except (IndexError,TypeError,ValueError):
        return None
    return v if C.good(v) else None


def parent_note(note,projection):
    if (set(note)!={"projection_sha256","reviewer","review_state","parents"}
            or note["projection_sha256"]!=projection or note["review_state"]!="independently-approved"
            or not isinstance(note["reviewer"],str) or not note["reviewer"].strip()
            or not isinstance(note["parents"],dict) or not note["parents"]
            or not all(isinstance(k,str) and k.strip() and is_pin(v) for k,v in note["parents"].items())):
        raise C.Incomplete("missing bound independent parent provenance")


def universe_schema(u):
    required = {"version","scope","contracts","rank_periods","unmatched_judged_ids"}
    if not required<=set(u)<=required|{"migration_links","ftt_archive_supplement"}:
        raise C.Incomplete("unexpected fields in the top-30 universe projection")
    contract = {"begin","closed_effective","closed_known_at","closure_evidence_sha256","coin_id","delisting_notice",
                "end","listed_known_at","listing_basis","listing_evidence_sha256","symbol"}
    if (any(set(c) not in (contract,contract|{"archive_first_path","archive_first_seconds"}) for c in u["contracts"])
            or any(set(r)!={"availability","captured_at","revision_history","sha256","status","uri"}
                   for r in u["rank_periods"].values())
            or any(set(r)!={"classification","evidence_sha256","reason","searched"} or not is_pin(r["evidence_sha256"])
                   or not isinstance(r["searched"],list) or not all(isinstance(v,str) for v in r["searched"])
                   for r in u["unmatched_judged_ids"].values())
            or any(set(r)!={"effective_hour","evidence_sha256","lineage_id"} or not is_pin(r["evidence_sha256"])
                   for r in u.get("migration_links",{}).values())):
        raise C.Incomplete("unexpected nested fields or unpinned identity evidence in top-30 universe")
    if "ftt_archive_supplement" in u and not is_pin(u["ftt_archive_supplement"].get("evidence_sha256")):
        raise C.Incomplete("unbound FTT universe supplement")


def manifest_schema(m,where):
    if set(m)!={"archives","errors"} or m["errors"] or not isinstance(m["archives"],dict):
        raise C.Incomplete("unexpected archive manifest fields or errors")
    if where=="plan18_ftt":
        base = {"where","sha256"}
    else:
        base = {"where","sha256","n","first","last"}
    locations = {where} if where!="spot" else {"replay_13","replay_16"}
    for row in m["archives"].values():
        if (set(row) not in (base,base|{"bytes"}) or not is_pin(row["sha256"])
                or row["where"] not in locations
                or ("first" in row and (any(type(row[k]) is not int for k in ("first","last","n"))
                                        or row["n"]<=0 or not 0<row["first"]<=row["last"]))
                or ("bytes" in row and (type(row["bytes"]) is not int or row["bytes"]<=0))):
            raise C.Incomplete("unexpected nested archive metadata")


class ClockGate:
    """Known gaps from pinned archive bounds, without opening payloads."""
    def __init__(self, archive_api, spot, perp, symbols, legacy, policy):
        raw = defaultdict(list)
        hour = C.HOUR
        for name,row in spot["archives"].items():
            raw["spot",SPOT.fullmatch(name)[1]].append((-(-row["first"]//hour),row["last"]//hour+1))
        for name,row in perp["archives"].items():
            m = archive_api.BULK.fullmatch(name)
            if m[2]=="klines":
                raw["trade",m[3]].append((-(-row["first"]//hour),row["last"]//hour+1))
            elif m[2]=="fundingRate":
                # Same rounded center hour as Plan 18's settlement adapter.
                raw["funding",m[3]].append(((row["first"]+hour//2)//hour,(row["last"]+hour//2)//hour+1))
        self.bounds = {}
        for key,spans in raw.items():
            merged = []
            for lo,hi in sorted(spans):
                if lo>=hi:
                    continue
                if merged and lo<=merged[-1][1]:
                    merged[-1] = (merged[-1][0],max(hi,merged[-1][1]))
                else:
                    merged.append((lo,hi))
            self.bounds[key] = ([lo for lo,_ in merged],[hi for _,hi in merged])
        self.api,self.symbols,self.legacy,self.policy = archive_api,symbols,legacy,policy

    def covers(self,kind,symbol,lo,hi):
        starts,ends = self.bounds.get((kind,symbol),((),()))
        i = bisect_right(starts,lo)-1
        return i>=0 and ends[i]>=hi

    def allows(self,pair,decision):
        p,l = self.policy,self.legacy
        fill = decision+p["fill_hours"]
        hi = decision-l["funding_interval_hours"]*l["funding_lag_intervals"]
        lo = hi-p["lookback_hours"]
        if not pair.begin<=lo<fill<pair.end:
            return False
        symbol = self.symbols[pair.perp]
        for kind,key in (("spot",pair.spot),("trade",symbol)):
            if not all(self.covers(kind,key,a,b) for a,b in ((lo,hi),(decision-2,decision-1),(fill,fill+1))):
                return False
        needed = list(range(lo,hi))+[fill]
        return all(self.covers("funding",symbol,h,h+1) for h in needed if self.api.scheduled_funding(symbol,h,l))


def validate_links(rows,by_key):
    links, families, exclusions = defaultdict(list),defaultdict(list),{}
    for link in rows:
        k = link.get("contract")
        if set(link)=={"contract","excluded_reason","evidence_sha256"}:
            if (k not in by_key or k in exclusions or not isinstance(link["excluded_reason"],str)
                    or not link["excluded_reason"].strip() or not is_pin(link["evidence_sha256"])):
                raise C.Incomplete("invalid spot identity exclusion")
            exclusions[k] = link["excluded_reason"]
            continue
        required = {"contract","spot","begin","end","known_at","evidence_sha256"}
        if set(link) not in (required,required|{"closed_known_at"}):
            raise C.Incomplete("unexpected fields in spot identity link")
        s,lo,hi,known = (link[key] for key in ("spot","begin","end","known_at"))
        closed = link.get("closed_known_at")
        c = by_key.get(k)
        if (c is None or not isinstance(s,str) or not re.fullmatch(r"[A-Z0-9]+USDT",s)
                or not all(type(v) is int for v in (lo,hi,known))
                or not c.begin<=lo<hi<=c.end or not 0<known<hi*C.HOUR
                or ("closed_known_at" in link and (type(closed) is not int or closed<=known))
                or not is_pin(link["evidence_sha256"])):
            raise C.Incomplete("invalid top-30 dated spot identity link")
        links[k].append((C.Pair(c.coin_id,k,s,lo,hi,closed),known))
        families[s].append((lo,hi,c.coin_id))
    if set(links)&set(exclusions) or set(links)|set(exclusions)!=set(by_key):
        raise C.Incomplete("every top-30 dated contract needs a spot match or explicit exclusion")
    for k,items in links.items():
        dates = sorted((a.begin,a.end) for a,_ in items)
        if any(a[1]>b[0] for a,b in zip(dates,dates[1:])):
            raise C.Incomplete(f"overlapping spot identity windows: {k}")
    for spans in families.values():
        spans.sort()
        for i,(lo,hi,coin) in enumerate(spans):
            for other_lo,_,other_coin in spans[i+1:]:
                if other_lo>=hi:
                    break
                if coin!=other_coin:
                    raise C.Incomplete("overlapping spot product assigned to distinct canonical coins")
    return links,exclusions


def git(*args):
    try:
        return subprocess.check_output(("git",*args),cwd=REPO,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        raise C.Incomplete("approval commit or frozen Git blob unavailable") from exc


def authorize(expected):
    """Check owner freeze and code only. Do not open even metadata inputs yet."""
    if HERE != REPO/"research_rig" or os.path.lexists(HERE/DRAFT):
        raise C.Incomplete("draft/off-repo scoring is disabled")
    if (any(k.startswith(("GIT_","REPLAY_24_")) for k in os.environ) or RUN.is_symlink()
            or RUN.stat().st_uid!=os.geteuid() or RUN.stat().st_mode&0o022):
        raise C.Incomplete("unexpected override or scoring path ownership")
    seal = json.loads(pinned(RUN/"freeze_24.json",expected))
    files = {f"research_rig/{f}" for f in (FINAL,*CODE,*(d+".py" for d in DEPS))}|{"config/thresholds.yaml"}
    if (seal.get("version")!=1 or seal.get("approval")!="owner-approved-once"
            or set(seal["files"])!=files or set(seal["inputs"])!=set(INPUTS)
            or not all(isinstance(v,str) and SHA.fullmatch(v) for v in seal["inputs"].values())
            or set(seal.get("parent_evidence",{}))!=set(INPUTS)
            or not all(isinstance(v,str) and SHA.fullmatch(v) for v in seal["parent_evidence"].values())
            or not re.fullmatch(r"[0-9a-f]{40}",seal["commit"])):
        raise C.Incomplete("freeze bindings are incomplete")
    upstream = git("rev-parse","origin/main").decode().strip()
    git("merge-base","--is-ancestor",seal["commit"],upstream)
    bound = {}
    for name,pin in seal["files"].items():
        bound[name] = pinned(REPO/name,pin)
        if any(git("show",f"{ref}:{name}")!=bound[name] for ref in (seal["commit"],upstream)):
            raise C.Incomplete(f"frozen code/config not on origin/main: {name}")
    if not re.search(rb"(?m)^Status FROZEN\.$",bound["research_rig/"+FINAL]):
        raise C.Incomplete("plan is not frozen")
    return seal,policy(bound["config/thresholds.yaml"])


def syncdir(path):
    fd = os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def one_shot(lock,result,authorize_run,score):
    """Burn the claim before the first real input file is opened. No retry, even on error."""
    if os.path.lexists(lock) or os.path.lexists(result):
        raise C.Incomplete("one-shot already consumed")
    binding = authorize_run()
    try:
        fd = os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as exc:
        raise C.Incomplete("another process consumed the one-shot") from exc
    with os.fdopen(fd,"w") as f:
        f.write(json.dumps({"state":"consumed","utc":datetime.now(timezone.utc).isoformat(),
                            "commit":binding[0]["commit"]})+"\n")
        f.flush()
        os.fsync(f.fileno())
    syncdir(lock.parent)
    if os.path.lexists(result):
        raise C.Incomplete("result appeared after the claim")
    report = score(binding)
    with tempfile.NamedTemporaryFile(mode="w",dir=result.parent,prefix=".result24-",delete=False) as f:
        tmp = Path(f.name)
        try:
            json.dump(report,f,sort_keys=True,allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
            os.link(tmp,result)
            syncdir(result.parent)
        finally:
            tmp.unlink()
    return report


class Archive:
    def __init__(self,perp,spot,snapshots,links,legacy,p,highs=None,closing=None,terminal_rates=None,*,clock=None):
        self.perp,self.spot,self.snapshots,self.links,self.legacy,self.p = perp,spot,snapshots,links,legacy,p
        self.highs = highs or {}
        self.closing,self.terminal_rates = closing or {},terminal_rates or {}
        self.clock = clock
        self.entry_clock = {}
        self.peaks,self.pools,self.signals = {},{},{}
        boundary = p["end"]*C.HOUR*10**6
        for k,c in perp.segments.items():
            lo,hi = max(c.begin,perp.lo),min(c.end+1,perp.hi+1)
            row = perp.store.get(perp.symbols[k])
            peak = 0.
            if row is not None:
                for h in range(lo,hi):
                    if not isfinite(row[3][h-perp.lo]):
                        continue
                    ok,v,offset = perp.funding_event(k,h)
                    if ok and v is not None and h*C.HOUR*10**6+offset<boundary:
                        peak = max(peak,abs(v))
            v,_ = self.terminal_payment(k)
            self.peaks[k] = max(peak,abs(v) if v is not None else 0.)

    def terminal_payment(self,key):
        c = self.perp.segments.get(key)
        v,offset = self.terminal_rates.get(self.perp.symbols[key],(None,0))
        if c is not None and v is not None and offset<0:
            hour_us = C.HOUR*10**6
            stamp = self.p["end"]*hour_us+offset
            if c.begin*hour_us<=stamp<c.end*hour_us:
                return v,offset
        return None,0

    def pool(self,t,only=None):
        if t not in self.pools:
            try:
                snap = self.legacy.latest(self.snapshots,t,self.perp.p)
            except self.legacy.Incomplete as exc:
                raise C.Incomplete("Plan 18 rank snapshot is missing, stale or ambiguous") from exc
            aliases = {a:b for a,b,e in snap.migrations if e<=t}
            top = {aliases.get(i,i) for _,i in snap.ranks}
            choices = defaultdict(list)
            fill,stamp = t+self.p["fill_hours"],t*C.HOUR
            for c in snap.contracts:
                if (c.coin_id not in top or c.listed_known_at>=stamp or c.begin>t-2
                        or c.closed_known_at is not None and c.closed_known_at<stamp and c.closed_effective<=fill):
                    continue
                for a,known in self.links.get(c.key,()):
                    if (known>=stamp or a.begin>t
                            or a.closed_known_at is not None and a.closed_known_at<stamp and a.end<=fill):
                        continue
                    choices[c.coin_id].append(a)
            selected = []
            for rows in choices.values():
                # A newer admitted link supersedes its predecessor; a stale,
                # retrospectively fenced link cannot hide that successor.
                ordered = sorted(rows,key=lambda a:a.begin,reverse=True)
                if len(ordered)>1 and any(a.begin==ordered[0].begin or a.end>ordered[0].begin for a in ordered[1:]):
                    raise C.Incomplete(f"ambiguous same-coin spot link at {t}")
                selected.append(ordered[0])
            self.pools[t] = tuple(selected)
        return tuple(a for a in self.pools[t] if only is None or a.coin in only)

    def bar(self,a,t):
        if not a.begin<=t<a.end:
            return None
        cols = self.spot.get(a.spot)
        if cols is None or not self.perp.lo<=t<=self.perp.hi:
            return None
        o,low,cl = (col[t-self.perp.lo] for col in cols)
        po,pc = self.perp.open_price(a.perp,t),self.perp.trade_close(a.perp,t)
        if not all(C.good(v) for v in (o,low,cl,po,pc)):
            return None
        m = self.perp.mark_close(a.perp,t)
        highs = self.highs.get(self.perp.symbols[a.perp])
        high = highs[t-self.perp.lo] if highs is not None else 0.
        return C.Bar(o,low,cl,po,pc,m if C.good(m) else pc,high)

    def closing_open(self,a,t):
        if t!=self.p["end"] or not a.begin<=t<a.end:
            return None
        cols = self.spot.get(a.spot)
        s = cols[0][t-self.perp.lo] if cols is not None and 0<=t-self.perp.lo<len(cols[0]) else None
        f = self.closing.get(self.perp.symbols[a.perp])
        return (s,f) if C.good(s) and C.good(f) else None

    def funding_inputs(self,a,t,*,full=False):
        lag = self.perp.p["funding_interval_hours"]*self.perp.p["funding_lag_intervals"]
        hi = t-lag
        lo = hi-self.p["lookback_hours"]
        rates,missing = [],0
        for h in range(lo,hi):
            covered,rate = self.perp.rank_funding(a.perp,h,t*C.HOUR)
            if not covered or (rate is not None)!=self.perp.expects_settlement(a.perp,h):
                missing += 1
                if not full:
                    break
            elif rate is not None:
                rates.append(rate)
        return rates,missing

    def signal(self,a,t):
        key = a.perp,t
        if key not in self.signals:
            rates,missing = self.funding_inputs(a,t)
            self.signals[key] = None if missing else sum(rates)*self.p["annual_days"]*C.DAY/self.p["lookback_hours"]
        return self.signals[key]

    def entry_covered(self,a,t):
        key = a,t
        if key not in self.entry_clock:
            self.entry_clock[key] = self.clock is not None and self.clock.allows(a,t)
        return self.entry_clock[key]

    def decision_traded(self,a,t):
        return self.bar(a,t-2) is not None

    def payment(self,a,t):
        if t==self.p["end"]:
            return self.terminal_payment(a.perp)
        ok,rate,offset = self.perp.funding_event(a.perp,t)
        return (rate if ok else None),offset

    def payment_missing(self,a,t):
        return self.perp.expects_settlement(a.perp,t) and self.payment(a,t)[0] is None

    def peak(self,a):
        return self.peaks[a.perp]


def load_spot(fetch,manifest,wanted,lo,hi,*,terminal=None,checks=None):
    if manifest["errors"]:
        raise C.Incomplete("spot archive manifest has errors")
    store = {}
    for name,meta in sorted(manifest["archives"].items()):
        match = SPOT.fullmatch(name)
        path = None
        with scan(checks,"spot_archive",name):
            if match is None or match[1] not in wanted or meta["where"] not in {"replay_13","replay_16"}:
                raise C.Incomplete(f"non-top-30 or unsupported spot archive path: {name}")
            path = fetch.archive_root(name,meta["where"])
        if path is None:
            continue
        with scan(checks,"spot_decode",path):
            if not 0<path.stat().st_size<=8_000_000:
                raise C.Incomplete("spot ZIP exceeds the registered per-file bound")
            s = match[1]
            if s not in store:
                store[s] = tuple(array("d",[nan])*(hi-lo+1) for _ in range(3))
            cols = store[s]
            count = 0
            for row in fetch.F.zip_rows(pinned(path,meta["sha256"])):
                count += 1
                t,rem = divmod(fetch.F.open_epoch(row[0]),C.HOUR)
                if rem:
                    raise C.Incomplete("spot clock is not hourly")
                if not lo<=t<=hi:
                    continue
                if t==terminal:
                    o = terminal_price(row)
                    if isfinite(cols[0][t-lo]):
                        raise C.Incomplete("overlapping terminal spot clock")
                    cols[0][t-lo] = o if o is not None else -1.
                    continue
                o,low,cl,v = (float(row[i]) for i in (1,3,4,5))
                if not all(C.good(v) for v in (o,low,cl)) or low>min(o,cl) or not isfinite(v) or v<0:
                    raise C.Incomplete("invalid spot OHLC or volume")
                off = t-lo
                if isfinite(cols[0][off]):
                    raise C.Incomplete("overlapping spot clock")
                for col,value in zip(cols,(o,low,cl)):
                    col[off] = value if v>0 else -1.
            if count!=meta["n"]:
                raise C.Incomplete("spot row count changed")
            if checks is not None:
                checks.counts["spot_rows_decoded"] += count
    return store


def risk_and_cutoff(A,tape,manifests,contracts,path,supplement,cutoff,*,checks=None):
    """Reuse checked clocks; terminal trades need an open, not a completed OHLCV bar."""
    result,closing,terminal_rates = {},{},{}
    by_pair = defaultdict(list)
    for c in contracts:
        by_pair[tape.symbols[c.key]].append(c)
    for pair,files in A.archive_groups(manifests,set(by_pair)).items():
        col = array("d",[0.])*(tape.hi-tape.lo+1)
        for name,(match,meta) in sorted(files.items()):
            with scan(checks,"perp_risk_archive",name):
                lo,hi = A.archive_span(match)
                kind = match[2]
                if kind=="fundingRate" and not lo<=cutoff<=hi or hi<=tape.lo or lo>cutoff:
                    continue
                source,_ = A.archive_input(path,supplement,name,match,meta)
                for h,offset,jitter,row in A.archive_rows(source,match,meta,by_pair[pair],tape.p):
                    if checks is not None:
                        checks.counts["perp_risk_rows_decoded"] += 1
                    if kind=="fundingRate":
                        if h!=cutoff or offset>=0:
                            continue
                        try:
                            v = float(row[2])
                        except (IndexError,TypeError,ValueError):
                            v = nan
                        if pair in terminal_rates or jitter or not isfinite(v):
                            if pair!="FTTUSDT":
                                raise C.Incomplete("duplicate or malformed pre-cutoff settlement")
                            terminal_rates[pair] = (None,0)
                        else:
                            terminal_rates[pair] = v,offset
                        continue
                    if h==cutoff:
                        if kind=="klines":
                            if pair in closing:
                                raise C.Incomplete("duplicate terminal perpetual open")
                            closing[pair] = terminal_price(row)
                        continue
                    if not tape.lo<=h<=tape.hi or match[2]=="klines" and float(row[5])<=0:
                        continue
                    high = float(row[2])
                    if not C.good(high) or high<max(float(row[1]),float(row[4])):
                        raise C.Incomplete("invalid archived perpetual high")
                    i = h-tape.lo
                    col[i] = max(col[i],high)
        result[pair] = col
    return result,closing,terminal_rates


def read_projections(seal,checks):
    for k,pin in seal["parent_evidence"].items():
        path = RUN/f"{k}_provenance.json"
        with scan(checks,"provenance",path):
            note = json.loads(pinned(path,pin))
            parent_note(note,seal["inputs"][k])
    data = {}
    for k,n in INPUTS.items():
        path = RUN/n
        with scan(checks,"projection",path):
            data[k] = json.loads(pinned(path,seal["inputs"][k]))
    validators = dict(universe=universe_schema,perp=lambda m:manifest_schema(m,"replay_16"),
                      spot=lambda m:manifest_schema(m,"spot"),ftt=lambda m:manifest_schema(m,"plan18_ftt"))
    for k,validate in validators.items():
        if k in data:
            with scan(checks,"projection_schema",RUN/INPUTS[k]):
                validate(data[k])
    return data


def parse_ranks(A,data,p,legacy):
    if any(set(r)-{"date","known_at","hole","sha256","top_raw"}
           or any(set(q)!={"cmcRank","id"} or not 1<=q["cmcRank"]<=legacy["top_rank"] for q in r.get("top_raw",[]))
           or r.get("hole") and r.get("top_raw") for r in data["ranks"]):
        raise C.Incomplete("rank input must be a top-30 projection")
    rank_rows = [r for r in data["ranks"] if (p["start"]-legacy["max_snapshot_age_days"]*24)*C.HOUR<=r["known_at"]<p["end"]*C.HOUR]
    if len(rank_rows)!=len(data["ranks"]):
        raise C.Incomplete("rank projection includes rows outside the authorized date scope")
    snaps,_ = A.parse_snapshots(rank_rows,(),legacy)
    A.verify_rank_schedule(data["universe"],rank_rows,legacy)
    return snaps


def scope_projections(A,L,data,p,checks):
    universe = data["universe"]
    legacy = dict(L.P,start=p["start"],end=p["end"],lookback_hours=p["lookback_hours"])
    catalogue = snaps = scope = links = None
    with scan(checks,"universe_catalogue",RUN/INPUTS["universe"]):
        catalogue = (*A.catalogue(universe),A.migration_links(universe))
    with scan(checks,"rank_schedule",RUN/INPUTS["ranks"]):
        snaps = parse_ranks(A,data,p,legacy)
    if catalogue is None:
        return None
    contracts,symbols,notices,aliases = catalogue
    if snaps is not None:
        with scan(checks,"rank_universe_scope",RUN/INPUTS["universe"]):
            scope = {aliases.get(i,(i,0))[0] for snap in snaps for _,i in snap.ranks}
            if any(c.coin_id not in scope for c in contracts) or any(lineage not in scope for lineage,_ in aliases.values()):
                raise C.Incomplete("universe contains a lineage outside the top-30 projection")
            if scope-{c.coin_id for c in contracts} != {aliases.get(int(i),(int(i),0))[0] for i in universe["unmatched_judged_ids"]}:
                raise C.Incomplete("top-30 mapping exclusions do not reconcile")
            snaps = tuple(L.Snapshot(s.known_at,contracts,s.ranks,tuple((i,*v) for i,v in aliases.items())) for s in snaps)
    with scan(checks,"spot_links",RUN/INPUTS["links"]):
        links,exclusions = validate_links(data["links"],{c.key:c for c in contracts})
    with scan(checks,"ftt_supplement",RUN/INPUTS["ftt"]):
        expected_ftt = A.ftt_manifest(universe,contracts,symbols) or {"archives":{},"errors":{}}
        if data["ftt"]!=expected_ftt:
            raise C.Incomplete("FTT projected supplement does not match Plan 18")
    kept_symbols = set(symbols.values())
    manifests = tuple(data[k] for k in ("perp","ftt"))
    for key,manifest in zip(("perp","ftt"),manifests):
        for name in manifest["archives"]:
            if not (m := A.BULK.fullmatch(name)) or m[3] not in kept_symbols:
                with scan(checks,"perp_path_scope",RUN/INPUTS[key]):
                    raise C.Incomplete("perpetual archive is not a top-30-only projection")
    if links is not None:
        allowed_spot = {a.spot for rows in links.values() for a,_ in rows}
        for name in data["spot"]["archives"]:
            if not (m := SPOT.fullmatch(name)) or m[1] not in allowed_spot:
                with scan(checks,"spot_path_scope",RUN/INPUTS["spot"]):
                    raise C.Incomplete("spot archive is not a top-30-only projection")
    if checks is not None and checks.refused:
        return None
    return contracts,symbols,notices,legacy,scope,snaps,links,exclusions,manifests,allowed_spot


def load_perp(A,path,manifests,symbols,notices,p,contracts,supplement,checks):
    def tape(m,sy,cs):
        return A.Tape(path,m,sy,notices,p,contracts=cs,supplemental_dir=supplement)

    if checks is None:
        return tape(manifests,symbols,contracts)
    groups = A.archive_groups(manifests,set(symbols.values()))
    lo = p["start"]-p["lookback_hours"]-p["funding_interval_hours"]*p["funding_lag_intervals"]
    # The clean path calls the same full loader once. Decoder refusal is
    # retraced below to collect every independently addressable archive failure.
    scoped_groups = {}
    for pair,items in groups.items():
        scoped = {}
        for name,(match,m) in items.items():
            with checks.scan("perp_archive_clock",name):
                a,b = A.archive_span(match)
                if b>lo and a<=p["end"]:
                    scoped[name] = m
        checks.counts["perp_files"] += len(scoped)
        scoped_groups[pair] = scoped
    first = None
    if not checks.refused:
        try:
            return tape(manifests,symbols,contracts)
        except A.ArchivePathError as exc:
            first = str(exc.path)  # Confirm it is reported by the isolated reproduction.
        except checks.errors:
            checks.refused["perp_full_tape",str(path)] += 1
    for pair,scoped in scoped_groups.items():
        sy = {k:v for k,v in symbols.items() if v==pair}
        cs = tuple(c for c in contracts if c.key in sy)
        # Tape is the scorer's exact decoder. If it fails one file, report
        # that file and retry the remaining ones for this symbol only.
        while scoped:
            try:
                tape(({"archives":scoped,"errors":{}},),sy,cs)
                break
            except A.ArchivePathError as exc:
                checks.refused["perp_decode",str(exc.path)] += 1
                bad = next((name for name in scoped if str(exc.path).endswith(name)),None)
                if bad is None:
                    break
                del scoped[bad]
            except checks.errors:
                checks.refused["perp_decode",pair] += 1
                break
    if first is not None and ("perp_decode",first) not in checks.refused:
        checks.refused["perp_decode",first] += 1
    return None


def load(binding,checks=None):
    """Shared authorized input loader; opens no full or held rank/manifest."""
    from research_rig import archive_18 as A, common_18 as L, fetch_16 as F
    seal,p = binding
    data = read_projections(seal,checks)
    scoped = None
    if checks is None or not checks.refused:
        with scan(checks,"projection_scope",RUN):
            scoped = scope_projections(A,L,data,p,checks)
    if scoped is None:  # Never touch archive paths whose top-30 scope was not established.
        checks.counts["archive_scope_blocked"] += 1
        return None
    contracts,symbols,notices,legacy,scope,snaps,links,exclusions,manifests,allowed_spot = scoped
    path,supplement = DATA/"replay_16/archives",DATA/"replay_18/ftt_archives"
    cutoff = p["end"]
    prep = legacy|{"end":cutoff-1}
    clock = perp = spot = risk = None
    with scan(checks,"archive_clock_gate",RUN):
        clock = ClockGate(A,data["spot"],data["perp"],symbols,legacy,p)
    with scan(checks,"perp_group",path):
        perp = load_perp(A,path,manifests,symbols,notices,prep,contracts,supplement,checks)
    warmup = p["start"]-p["lookback_hours"]-legacy["funding_interval_hours"]*legacy["funding_lag_intervals"]
    clock_tape = perp if perp is not None else SimpleNamespace(lo=warmup,hi=cutoff-1,p=prep,symbols=symbols)
    with scan(checks,"spot_manifest",RUN/INPUTS["spot"]):
        spot = load_spot(F,data["spot"],allowed_spot,clock_tape.lo,cutoff,terminal=cutoff,checks=checks)
    with scan(checks,"perp_risk_group",path):
        risk = risk_and_cutoff(A,clock_tape,manifests,contracts,path,supplement,cutoff,checks=checks)
    if checks is not None and checks.refused:
        checks.counts["input_access_sweep_blocked"] += 1
        return None
    tape = None
    with scan(checks,"tape_assembly",RUN):
        tape = Archive(perp,spot,snaps,links,L,p,*risk,clock=clock)
    if tape is None:
        return None
    tape.coverage = dict(spot_exclusions=exclusions,top_rank_lineages=len(scope),mapped_perp_contracts=len(contracts),
                         paired_perp_contracts=len(links),spot_archive_symbols=len(spot),
                         linked_majors=sorted({a.coin for pairs in links.values() for a,_ in pairs if a.coin in {1,1027}}))
    return tape


def check_uses(tape,p,checks):
    """Walk a superset of every reachable data access, without building a book."""
    start,end,fill = p["start"],p["end"],p["fill_hours"]
    counts,gaps = checks.counts,checks.gaps
    for t in range(start,end-fill,C.DAY):
        pool = ()
        with checks.scan("decision_pool",RUN/INPUTS["ranks"]):
            pool = tape.pool(t)
        counts["decision_pool_names"] += len(pool)
        for a in pool:
            stamp = f"{a.perp}/{a.spot}"
            with checks.scan("decision_funding_access",stamp):
                # Read the exact lagged funding inputs, but do not annualize,
                # rank, select, or compute a strategy return.
                _,missing = tape.funding_inputs(a,t,full=True)
                if missing:
                    gaps["asof_signal_unavailable",stamp] += 1
            if t+fill>=a.end:
                gaps["possible_retrospective_link_end",stamp] += 1
                continue
            with checks.scan("decision_clock_access",stamp):
                if not tape.entry_covered(a,t):
                    gaps["entry_archive_clock_gap",stamp] += 1
            with checks.scan("decision_bar_access",stamp):
                if not tape.decision_traded(a,t):
                    gaps["entry_completed_bar_gap",stamp] += 1
            with checks.scan("fill_bar_access",stamp):
                if tape.bar(a,t+fill) is None:
                    gaps["entry_fill_bar_gap",stamp] += 1
    for rows in tape.links.values():
        for a,_ in rows:
            stamp = f"{a.perp}/{a.spot}"
            for h in range(max(start,a.begin),min(end,a.end+1)):
                counts["possible_held_hours"] += 1
                with checks.scan("held_bar_access",stamp):
                    if tape.bar(a,h) is None:
                        gaps["held_common_bar_gap",stamp] += 1
                    if not C.good(tape.perp.mark_close(a.perp,h)):
                        gaps["mark_close_fallback",stamp] += 1
                with checks.scan("held_funding_access",stamp):
                    if tape.payment_missing(a,h):
                        gaps["held_scheduled_funding_gap",stamp] += 1
                    tape.payment(a,h)
                    tape.peak(a)
            if a.begin<end<=a.end:
                counts["cutoff_pairs"] += 1
                with checks.scan("cutoff_open_access",stamp):
                    if tape.closing_open(a,end) is None:
                        gaps["cutoff_open_fallback",stamp] += 1
                with checks.scan("cutoff_funding_access",stamp):
                    tape.payment(a,end)


def validate_inputs(binding):
    checks = InputChecks()
    tape = None
    with checks.scan("input_load",RUN):
        tape = load(binding,checks)
    if tape is not None:
        check_uses(tape,binding[1],checks)
    return checks.report()


def evaluate(tape,p):
    judged = p["fees"][p["judged"]]
    try:
        out = C.assess(tape,p,judged)
    except C.Incomplete as exc:
        out = dict(passed=False,judged_refused=str(exc))
    def shown(fee,**kw):
        if fee is None:
            return {"unavailable":"UNKNOWN stated fee"}
        try:
            r = C.run(tape,p,fee,**kw)
            del r["schedule"]
            return r
        except C.Incomplete as exc:
            return {"unavailable":str(exc)}
    costs = {k:shown(f) for k,f in p["fees"].items()}
    grid = {str(k):shown(C.Fee(k,k)) for k in p["grid"]}
    positive = [int(k) for k,v in grid.items() if v.get("annual",0)>0]
    out.update(account_usd=p["initial_usd"],judged_fee=p["judged"],coverage=getattr(tape,"coverage",{}),
               shown=dict(fees=costs,flat_grid=grid,grid_break_even_bps=max(positive,default=None),
                         majors=shown(judged,universe={1,1027}),
                         entries={str(k):shown(judged,threshold=k) for k in p["shown_entry"]}))
    return out


def render(out):
    def pct(x):
        return "not computed" if x is None else f"{x:.2%}"
    main = out.get("main",{})
    lines = ["# Replay 24: same-coin funding carry","","MEASURED only if the owner ran the frozen scorer.",
             f"Judged account: ${out['account_usd']}. Judged fees: {out['judged_fee']}, charged in dollars per actual order.",
             "Viewed dates only. Binance stands in for historical US funding; actual US funding is UNKNOWN.","",
             "| Mark | Value | Met |","|---|---:|---|"]
    values = dict(annual=pct(main.get("annual")),sharpe=main.get("sharpe"),drawdown=pct(main.get("drawdown")),
                  positive_years=sum(v>0 for v in main.get("years",{}).values()) if main else None,twins=pct(out.get("p95")))
    for k,v in values.items():
        lines.append(f"| {k} | {v if v is not None else 'not computed'} | {out.get('checks',{}).get(k,'not computed')} |")
    lines += ["",f"All marks passed: {out.get('passed',False)}.",
              ("Highest positive flat grid cost: "
               + ("none on the grid" if out["shown"]["grid_break_even_bps"] is None
                  else f"{out['shown']['grid_break_even_bps']} bp per leg per side")
               + " (shown only).")]
    if out.get("judged_refused"):
        lines.append(f"Judged line not computed: {out['judged_refused']}.")
    if main:
        lines.append(f"Completed twins: {len(out['twins'])}; refused: {len(out['twin_refusals'])}.")
    blocked = main.get("blocked_slot_days","not computed")
    data_gaps = main.get("data_gap_slot_days","not computed")
    links = main.get("link_end_slot_days","not computed")
    unfilled = main.get("unfilled_slot_days","not computed")
    unrankable = main.get("unrankable_name_days","not computed")
    lines.append(f"Gap: data-gap entry slot-days: {data_gaps}. Metadata-blocked entry slot-days: {blocked}. All unfilled entry slot-days: {unfilled}.")
    lines.append(f"Gap: retrospective link-end entry slot-days: {links}.")
    lines.append(f"Gap: fresh name-days without an as-of funding signal (no slot assigned): {unrankable}.")
    if out.get("coverage"):
        c = out["coverage"]
        lines.append(f"Top-rank lineages: {c['top_rank_lineages']}; dated perpetual segments: {c['mapped_perp_contracts']}; paired: {c['paired_perp_contracts']}.")
        if 1027 not in c["linked_majors"]:
            lines.append("BTC/ETH sensitivity has no eligible ETH pair in the approved spot identity scope.")
    if main:
        lines += ["",f"Funding {main['funding_points']:.2f} points; basis {main['basis_points']:.2f} points; fees {main['fee_points']:.2f} points.",
                  f"Time in market {main['time_in_market']:.2%}; realized coin-hours {main['coin_hours']}.",
                  "","| UTC year | Net gain | Pair trade events |","|---|---:|---:|"]
        for y,v in main["years"].items():
            lines.append(f"| {y} | {v:.2%} | {main['trades'].get(y,0)} |")
    lines += ["","| Shown only | Annual net |","|---|---:|"]
    for key in ("fees","entries","flat_grid"):
        for label,row in out["shown"][key].items():
            value = "UNKNOWN, excluded" if row.get("unavailable")=="UNKNOWN stated fee" else pct(row.get("annual"))
            lines.append(f"| {key}: {label} | {value} |")
    lines.append(f"| BTC/ETH | {pct(out['shown']['majors'].get('annual'))} |")
    return "\n".join(lines)+"\n"


def resources():
    if os.nice(0)<10:
        raise C.Incomplete("start the owner one-shot with nice -n 10")
    soft,hard = resource.getrlimit(resource.RLIMIT_AS)
    bound = min(x for x in (288000*1024,soft,hard) if x!=resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS,(bound,hard))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--run",metavar="OWNER_FREEZE_SHA256")
    group.add_argument("--validate-inputs",metavar="OWNER_FREEZE_SHA256")
    group.add_argument("--render",type=Path)
    args = ap.parse_args()
    if args.render:
        print(render(json.loads(args.render.read_text())),end="")
        return
    if args.validate_inputs is not None:
        checks = InputChecks()
        binding = None
        with checks.scan("resource_policy",REPO):
            resources()
        with checks.scan("authorization",RUN/"freeze_24.json"):
            if not checks.refused:
                binding = authorize(args.validate_inputs)
        report = validate_inputs(binding) if binding is not None else checks.report()
        print(json.dumps(report,sort_keys=True))
        return 1 if report["refusals"] else 0
    resources()
    def score(binding):
        out = evaluate(load(binding),binding[1])
        out["freeze_sha256"] = args.run
        out["input_pins"] = binding[0]["inputs"]
        out["parent_evidence_pins"] = binding[0]["parent_evidence"]
        return out
    one_shot(RUN/"score_24.lock",RUN/"results_24.json",lambda:authorize(args.run),score)


if __name__=="__main__":
    sys.exit(main())
