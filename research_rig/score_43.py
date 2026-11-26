"""Plan 43: filing-anchored special dividends. No acquisition; fail closed."""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from io import BytesIO
import json
from math import ceil, sqrt
import os
from pathlib import Path
import random
import re
import resource
from shutil import disk_usage
import stat
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, reset_tzpath

ROOT = Path(__file__).resolve().parent.parent
DATA = Path("/home/user/workspace/rig/data")
INPUT = DATA / "plan43_successor_inputs"
RUN = DATA / "replay_43_successor"
PLAN = "research_rig/PREREG_43_special_dividends.md"
AMENDMENT = "research_rig/AMENDMENT_43_TAPE.md"
PINS = "research_rig/PINNED_43.json"
APPROVAL = "research_rig/APPROVAL_43_SUCCESSOR.md"
ENGINE = "research_rig/common_21.py"
PROVENANCE = "research_rig/provenance_43.py"
CALENDARS = ("research_rig/calendar_36.json", "research_rig/calendar_25.json")
CONFIG = "config/thresholds.yaml"
CALIBRATION = "research_rig/CALIBRATION_43.json"
ACQUISITION = "research_rig/ACQUISITION_43_SUCCESSOR.md"
GO = "research_rig/GO_43_SUCCESSOR.md"
SOURCES = {PLAN, AMENDMENT, ENGINE,PROVENANCE,*CALENDARS, CONFIG, CALIBRATION,
           "research_rig/score_43.py", "research_rig/test_43.py"}
COLLECTOR = DATA / "plan43_provenance/fetch_plan43_bars_v2.py"
COLLECTOR_SHA256 = "5c2ce9a3cbd34a7332bd988c15b62c4dc49ff11d874348703f2ee835ee62a447"
LEDGER = 188
SEC = "www.sec.gov"
ENDPOINT = "https://data.alpaca.markets/v2/stocks/bars"
PACKETS = ("identities.json", "bars.json", "actions.json")
VIEWS = ("raw","all","filing_all")
COVERAGE_BPS = 500
COVERAGE_REASONS = ("missing_entry","zero_volume_entry","missing_exit","zero_volume_exit",
                    "missing_hold","zero_volume_hold")
EARLY_REASONS = ("missing_day1","zero_volume_day1")
PADDING_FLAGS = ("missing_pre_padding","zero_volume_pre_padding",
                 "missing_post_padding","zero_volume_post_padding")
NONCASH_SKIP = "unmodeled_noncash_distribution"
NONCASH_ACCESSION = "0001140361-22-046943"
DOCKET = Path("/home/user/workspace/rig/plan43_draft/EVENT_DOCKET_V2.jsonl")
reset_tzpath(("/usr/share/zoneinfo",))
TZ_BYTES=Path("/usr/share/zoneinfo/America/New_York").read_bytes()
if sha256(TZ_BYTES).hexdigest()!="e9ed07d7bee0c76a9d442d091ef1f01668fee7c4f26014c0a868b19fe6c18a95":
    raise SystemExit("P43_TIMEZONE")
ET=ZoneInfo.from_file(BytesIO(TZ_BYTES),key="America/New_York")
ZERO = Decimal(0)
UUID=rb"([0-9a-f]{40})"
SHA=rb"([0-9a-f]{64})"
ACQUISITION_RE = (rb"Approved by the lead: plan 43 successor ledger 188, one custodian acquisition, freeze commit "+UUID
                  +rb", freeze SHA-256 "+SHA+rb", docket SHA-256 "+SHA+rb", collector SHA-256 "+SHA+rb"\.\n")
APPROVAL_RE = (
    rb"Approved by the lead: plan 43 successor ledger 188, validation only, acquisition commit "+UUID
    +rb", acquisition receipt SHA-256 "+SHA+rb", identities SHA-256 "+SHA
    +rb", bars SHA-256 "+SHA+rb", actions SHA-256 "+SHA+rb", fetch-start SHA-256 "+SHA
    +rb", native index SHA-256 "+SHA+rb", transport index SHA-256 "+SHA
    +rb", offline rebuild SHA-256 "+SHA+rb"\.\n"
)
GO_RE = (rb"Approved by the lead: plan 43 successor ledger 188, one scored run, validation approval commit "+UUID
         +rb", validation receipt SHA-256 "+SHA+rb"\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P43_" + code)


def is_pin(x):
    return isinstance(x, str) and re.fullmatch("[0-9a-f]{64}", x) is not None


def unique(pairs):
    obj = dict(pairs)
    need(len(obj) == len(pairs), "DUPLICATE_KEY")
    return obj


def illegal(_):
    raise Refused("P43_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=illegal, parse_float=Decimal)


def render(obj):
    def export(x):
        if isinstance(x,(Fraction,Decimal)):
            return float(x)
        raise TypeError
    return (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False,default=export) + "\n").encode()


def d(s):
    day = date.fromisoformat(s)
    need(day.isoformat() == s, "DATE")
    return day


def money(x):
    need(type(x) in (int, str, Decimal), "NUMBER")
    out = Decimal(x)
    need(out.is_finite() and out.as_tuple().exponent>=-32 and abs(out)<=10**15,"NUMBER")
    return out


def exact(x):
    return Fraction(str(x)) if type(x) is float else Fraction(x)


def source(u):
    if type(u) is not str or not u.isascii() or any(x.isspace() for x in u):
        return ""
    loc = urlsplit(u)
    return loc.hostname if loc.scheme == "https" and loc.hostname and not loc.username and not loc.fragment else ""


def cites(two):
    return type(two) is list and len(two) == 2 and all(map(source, two)) and source(two[0]) != source(two[1])


def config(blob):
    match = re.findall(rb"(?m)^replay_43_plan:\n  value: (\{[^\n]+\})$", blob)
    need(len(match) == 1, "CONFIG")
    c = parse(match[0])
    need(is_pin(c["docket_sha256"]) and c["eligible"]>=c["marks"]["placed"]
         and c["clock"]=="strict_before_scheduled_close","CONFIG")
    need(c["first_year"] == d(c["from"]).year and c["last_year"] == d(c["through"]).year, "CONFIG")
    return c


def engine(blob):
    # Execute only the already hash-verified Plan 21 pure helpers.
    module = ModuleType("p43_verified_common_21")
    exec(compile(blob, ENGINE, "exec"), module.__dict__)
    return module


class Sessions(list):
    def __init__(self,dates,closes):
        super().__init__(dates)
        self.closes=closes


def calendar(blobs):
    first, second = map(parse, blobs)
    for x in (first, second):
        need(x["calendar"] == "XNYS", "CALENDAR")
    a,b,closes=[],[d(x) for x in second["sessions"]],{}
    for day,opened,closed in first["sessions"]:
        day=d(day)
        op,cl=(datetime.fromisoformat(x.replace("Z","+00:00")).astimezone(ET) for x in (opened,closed))
        need(op.date()==cl.date()==day and op.time()==time(9,30) and op<cl and cl.time()<=time(16),"CALENDAR")
        a.append(day)
        closes[day]=cl
    for days in (a,b):
        need(days == sorted(set(days)) and all(x.weekday() < 5 for x in days), "CALENDAR")
    need([x for x in a if b[0] <= x <= b[-1]] == [x for x in b if a[0] <= x <= a[-1]], "CALENDAR")
    return Sessions(sorted(set(a)|set(b)),closes)


def window(dt, days, c):
    need(dt.tzinfo is not None, "EDGAR_CLOCK")
    et = dt.astimezone(ET)
    idx = bisect_left(days, et.date())
    if idx<len(days) and days[idx]==et.date():
        need(et.date() in days.closes,"CALENDAR_CLOSE")
        if et>=days.closes[et.date()]:
            idx+=1
    lag1, lag2, end = (idx+c["shown_entry"], idx+c["entry"], idx+c["exit"])
    pad = c["stale_run"]
    need(lag1 >= pad and end+pad < len(days), "CALENDAR")
    return SimpleNamespace(day0=days[idx], early=days[lag1], entry=days[lag2], exit=days[end],
                           start=days[lag1-pad], end=days[end+pad])


def events(blob, days, c):
    need(sha256(blob).hexdigest() == c["docket_sha256"], "DOCKET_PIN")
    out, seen = [], set()
    for line in blob.splitlines():
        r = parse(line)
        a = r["accession"]
        need(re.fullmatch(r"\d{10}-\d{2}-\d{6}", a) and a not in seen, "DOCKET")
        seen.add(a)
        if r["disposition"] != "eligible":
            need(r["disposition"] in ("excluded", "unresolved"), "DOCKET")
            continue
        dt = datetime.fromisoformat(r["acceptance"])
        need(dt.tzinfo is not None and dt.utcoffset() == dt.astimezone(ET).utcoffset(), "EDGAR_CLOCK")
        need(d(c["from"]) <= dt.date() <= d(c["through"]) and r["venue"] in ("NYSE","Nasdaq")
             and re.fullmatch(r"\d{10}",r["cik"]) and r["share_class"] and r["words_used"]
             and r["first_time"] in ("YES","NO","UNKNOWN") and source(r["url"]) == SEC
             and money(r["per_share_usd"]) > ZERO, "DOCKET")
        w = window(dt, days, c)
        out.append(SimpleNamespace(a=a,cik=r["cik"],cl=r["share_class"],at=dt,first=r["first_time"],
                                   declared=money(r["per_share_usd"]),year=dt.year,
                                   board=d(r["board_date"]) if r.get("board_date") else None,
                                   record=d(r["record_date"]) if r.get("record_date") else None,
                                   pay=d(r["payment_date"]) if r.get("payment_date") else None, **vars(w)))
    need(len(seen) == c["frame_rows"] and len(out) == c["eligible"], "DOCKET_COUNTS")
    return sorted(out,key=lambda e:(e.at,e.a,e.cl))


def tape(rows, days, C):
    out = {}
    for r in rows:
        stamp = datetime.fromisoformat(r["t"].replace("Z","+00:00"))
        need(stamp.tzinfo is not None, "BAR")
        et = stamp.astimezone(ET)
        day = et.date()
        need(et.time() == time() and day in days and day not in out and set(r) == set("tohlcv"), "BAR")
        for key in "ohlcv":
            money(r[key])
        out[day] = C.Bar.parse(r)
    return out


def actions_packet(p, keyed, days, c):
    need(p["version"] == 1 and p["reviewer"] == c["action_checker"] and set(p["records"]) == set(keyed), "ACTIONS")
    checked = {}
    gids,aliases,targets = {},{},set()
    first,last = min(days),max(days)
    for a,(e, ids) in keyed.items():
        legs = p["records"][a]
        need(set(legs) == set(ids), "ACTIONS")
        checked[a] = {}
        for leg,z in legs.items():
            need(z["identity"] == ids[leg]["identity"] and cites(z["coverage_sources"])
                 and z["start"] == e.start.isoformat()
                 and z["end"] == e.end.isoformat(), "ACTION_COVERAGE")
            if leg=="stock" and a==NONCASH_ACCESSION:
                need(z.get("status")=="blocked" and z.get("reason_code")==NONCASH_SKIP
                     and cites(z.get("reason_sources")),"ACTION_COVERAGE")
                continue
            need(z.get("status")=="complete","ACTION_COVERAGE")
            aset = {}
            for row in z["items"]:
                ex = d(row["ex"])
                identifier = row["id"]
                kind = row["kind"]
                need(type(identifier) is str and identifier and identifier not in aset and cites(row["sources"])
                     and kind in ("ordinary","special","split"),
                     "ACTION_ITEM")
                need(ex in days or (leg == "stock" and z["target"] == identifier and kind == "special"
                     and (ex < first or ex > last) and ex.weekday()<5), "ACTION_SESSION")
                need(e.start <= ex <= e.end or (leg == "stock" and z["target"] == identifier
                     and kind == "special"), "ACTION_SCOPE")
                if kind == "split":
                    nums=[row["new_shares"],row["old_shares"]]
                    need(all(type(v) is int and 0<v<=10**9 for v in nums)
                         and row.get("value") is None and row["payment"] is None and row["available"] is None,
                         "ACTION_SPLIT")
                    value=Fraction(*nums)
                    payment = None
                    available = None
                else:
                    payment = d(row["payment"])
                    available = d(row["available"])
                    value=money(row["value"])
                    need(value>ZERO and available>=max(ex,payment),"ACTION_PAY")
                key = (z["identity"],identifier)
                data = (ex,kind,value,payment,available)
                need(key not in gids or gids[key] == data, "ACTION_CONFLICT")
                alias=(z["identity"],ex,kind,value,payment)
                need(alias not in aliases or aliases[alias]==identifier,"ACTION_ID_ALIAS")
                aliases[alias]=identifier
                gids[key] = data
                aset[identifier] = data
            if leg == "stock":
                link=z["target_disclosure"]
                need(link["accession"]==a and source(link["filing"])==SEC
                     and a.replace("-","") in link["filing"].replace("-","")
                     and d(link["declared"])<=d(link["announced"])<=e.at.date()
                     and (e.board is None or d(link["declared"])==e.board),"ACTION_DISCLOSURE")
                if z["target"] is None:
                    need(cites(z["cancellation_sources"]), "ACTION_TARGET")
                else:
                    need(z["cancellation_sources"] == [] and z["target"] in aset, "ACTION_TARGET")
                    ex,kind,value,pay,_ = aset[z["target"]]
                    record=d(link["record"])
                    key=(z["identity"],z["target"])
                    need(kind=="special" and value==e.declared and key not in targets
                         and pay>=record and record>=d(link["declared"])
                         and (e.record is None or record==e.record)
                         and (e.pay is None or pay==e.pay),"ACTION_TARGET")
                    targets.add(key)
            else:
                need(z["target"] is None and z["cancellation_sources"] == []
                     and z["target_disclosure"] is None,"ACTION_TARGET")
            seq = sorted(aset.values())
            dates = Counter((x[0],x[1]) for x in seq)
            need(all(n == 1 for n in dates.values()), "ACTION_AMBIGUOUS")
            need(all(not dates[(x[0],"split")] for x in seq if x[1] != "split"), "ACTION_SPLIT_ORDER")
            checked[a][leg] = (seq, aset[z["target"]][0] if z["target"] is not None else None)
    # Any shared-identity cash action appearing in another coverage window must be present there too.
    known = defaultdict(set)
    for (identity,_), item in gids.items():
        known[identity].add(item)
    for a,(e,ids) in keyed.items():
        for leg,ident in ids.items():
            if leg not in checked[a]:
                continue
            seq,_ = checked[a][leg]
            need({x for x in known[ident["identity"]] if e.start <= x[0] <= e.end}
                 == {x for x in seq if e.start <= x[0] <= e.end}, "ACTION_OVERLAP")
    return checked


def check_basis(raw,adjusted,filing,scope,seq):
    eps=Fraction(1,10000)

    def ratio(a,b):
        pair=list(zip(map(exact,a.flat_key),map(exact,b.flat_key)))
        result=pair[0][0]/pair[0][1]
        need(all(abs((x/y)/result-1)<=eps for x,y in pair),"OHLC_BASIS")
        return result

    actions=defaultdict(list)
    for ex,kind,value,_,_ in seq:
        actions[ex].append((kind,exact(value)))
    anchor=expected=None
    prior=None
    unproved=[]
    for k,day in enumerate(scope):
        if positive(adjusted,day) and positive(filing,day):
            base=ratio(adjusted[day],filing[day])
            if anchor is None:
                anchor=base
            need(abs(base/anchor-1)<=eps,"ASOF_BASIS_CHANGE")
        if not (positive(raw,day) and positive(adjusted,day)):
            continue
        level=ratio(raw[day],adjusted[day])
        unknown=False
        for j in range(prior+1 if prior is not None else k+1,k+1):
            transition=scope[j]
            split=next((value for kind,value in actions[transition] if kind=="split"),None)
            cash=sum(value for kind,value in actions[transition] if kind!="split")
            if split is not None:
                expected/=split
            elif cash:
                if not positive(raw,scope[j-1]):
                    unknown=True
                    unproved.append(transition)
                else:
                    previous=exact(raw[scope[j-1]].c)
                    need(previous>cash,"DIVIDEND_BASIS")
                    expected*=1-cash/previous
        if prior is None or unknown:
            expected=level
        else:
            need(abs(level/expected-1)<=eps,"RAW_BASIS_CHANGE")
        prior=k
    return unproved


def positive(view,day):
    return day in view and view[day].v>ZERO


def issue(tapes, dates):
    cells=[v.get(day) for v in tapes for day in dates]
    if any(bar is None for bar in cells):
        return "missing"
    if any(bar.v==ZERO for bar in cells):
        return "zero_volume"
    return None


class Prepared(dict):
    def __init__(self):
        super().__init__()
        self.decisions={}


def coverage_limit(n):
    return n*COVERAGE_BPS//10000


def enforce_coverage(rows):
    applied=[r for r in rows.decisions.values() if not r.get("noncash")]
    need(sum(r["refusal"] is not None for r in applied)<=coverage_limit(len(applied)),"COVERAGE_CAP")


def canonical_class(e):
    label=e.cl.lower()
    keys={"-".join(m) for m in re.findall(r"\b(class|series) ([a-z])\b",label)}
    if e.a=="0001692063-20-000164" and e.cik=="0001692063" and keys=={"class-a","class-b"}:
        # Issuer supplement declares both classes; the original 8-K cover explicitly
        # identifies SNDR's NYSE-traded Class B as the priceable security.
        return "class-b"
    need(len(keys)<=1,"CLASS_AMBIGUOUS")
    if keys:
        return next(iter(keys))
    return "voting-common" if "voting common" in label else "common"


def identity_actions(event_rows, days, c, identity, actions):
    need(identity["version"] == 1 and identity["custodian"] == c["custodian"]
         and set(identity["records"]) == {e.a for e in event_rows}, "IDENTITY")
    keyed,mapping,subject_ids = {},{},{}
    controls = c["controls"]
    for e in event_rows:
        ids = identity["records"][e.a]
        need(set(ids) == {"stock",*controls}, "IDENTITY")
        for leg,r in ids.items():
            key = r["identity"]
            need(re.fullmatch(r"[A-Z0-9_.:-]{3,100}",key) and source(r["source"])
                 and re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]{0,12}",r["ticker"]), "IDENTITY")
            need(type(r["cik"]) is str and re.fullmatch(r"\d{10}",r["cik"]) and r["share_class"],"IDENTITY")
            if leg == "stock":
                need((r["cik"],r["share_class"],r["class_key"])==(e.cik,e.cl,canonical_class(e)),"IDENTITY")
            else:
                need(r["ticker"]==leg and r["class_key"]=="etf","IDENTITY")
            subject=(leg,r["cik"],r["class_key"])
            need(key not in mapping or mapping[key] == subject, "IDENTITY")
            need(subject not in subject_ids or subject_ids[subject]==key,"IDENTITY_SUBJECT")
            mapping[key] = subject
            subject_ids[subject]=key
        keyed[e.a] = e,ids
    need(all(len({ids[s]["identity"] for _,ids in keyed.values()}) == 1 for s in controls), "CONTROL_IDENTITY")
    action = actions_packet(actions,keyed,set(days),c)
    modeled = {a for a in action if "stock" in action[a]}
    need(keyed.keys()-modeled==({NONCASH_ACCESSION} if NONCASH_ACCESSION in keyed else set())
         and (len(keyed)!=443 or len(modeled)==442),"ACTION_UNIVERSE")
    return keyed,action,modeled


def prepared(event_rows, days, C, c, identity, bars, actions):
    need(bars["version"] == 1 and bars["custodian"] == c["custodian"] and bars["endpoint"] == ENDPOINT
         and bars["feed"] == "sip" and bars["timeframe"] == "1Day"
         and bars["adjustments"] == ["raw","all"], "BARS")
    keyed,action,modeled=identity_actions(event_rows,days,c,identity,actions)
    controls=c["controls"]
    need(modeled <= bars["records"].keys() <= keyed.keys(),"BARS")
    complete, identities = Prepared(), defaultdict(dict)
    reversed_fingerprints, alias_dates = defaultdict(set), defaultdict(set)
    for a,(e,ids) in keyed.items():
        if a not in modeled:
            complete.decisions[a]=dict(year=e.year,noncash=NONCASH_SKIP)
            continue
        packet = bars["records"][a]
        need(set(packet) == set(ids), "BARS")
        complete[a] = {}
        scope = days[bisect_left(days,e.start):bisect_right(days,e.end)]
        allowed = set(scope)
        per_leg={}
        gaps={}
        insufficient=[]
        for leg,ident in ids.items():
            r = packet[leg]
            need((r["ticker"],r["identity"]) == (ident["ticker"],ident["identity"])
                 and r["entry_asof"] == e.entry.isoformat() and r["filing_asof"] == e.at.date().isoformat()
                 and r["start"] == e.start.isoformat() and r["end"] == e.end.isoformat(), "BAR_SCOPE")
            need(all(k in r and type(r[k]) is list for k in VIEWS),"BAR_SCOPE")
            raw, adj, check = (tape(r[k],allowed,C) for k in VIEWS)
            per_leg[leg]=(raw,adj,check)
            bad = C.stale_dates(scope,{day:b for day,b in adj.items() if b.v>ZERO},c["stale_run"])
            pair_days=[day for day in scope if positive(adj,day) and positive(check,day)]
            if len(pair_days)>=3:
                need(C.same_tape(adj,check,pair_days),"BAR_IDENTITY")
            else:
                insufficient.append(leg)
            for day in (e.early,e.entry,e.exit):
                need(day not in bad,"BAR_MISSING_STALE")
            unproved=check_basis(raw,adj,check,scope,action[a][leg][0])
            if unproved:
                gaps[leg]=[day.isoformat() for day in unproved]
            key = ident["identity"]
            # Repeated same-identity raw bars must agree on all overlapping sessions.
            for day,b in raw.items():
                need(day not in identities[key] or b == identities[key][day], "BAR_CONFLICT")
                identities[key][day] = b
            # Count exact native OHLCV matches on distinct dates across any view or
            # overlapping request, without allowing another view to replace a fingerprint.
            for view in (raw,adj,check):
                for day,b in view.items():
                    if b.v<=ZERO:
                        continue
                    owners=reversed_fingerprints[(day,b)]
                    for other in owners-{key}:
                        dates=alias_dates[tuple(sorted((key,other)))]
                        dates.add(day)
                        need(len(dates)<3,"BAR_ALIAS")
                    owners.add(key)
            complete[a][leg] = (raw,*action[a][leg])
        views=[view for tapes in per_leg.values() for view in tapes]
        refusal=None
        for name,dates in (("entry",[e.entry]),("exit",[e.exit]),
                           ("hold",[day for day in scope if e.entry<day<e.exit])):
            flag=issue(views,dates)
            if flag is not None:
                refusal=f"{flag}_{name}"
                break
        early=issue(views,[e.early]) if refusal is None else None
        flags=[]
        for label,dates in (("pre",[day for day in scope if day<e.early]),
                            ("post",[day for day in scope if day>e.exit])):
            if any(day not in view for view in views for day in dates):
                flags.append(f"missing_{label}_padding")
            if any(day in view and view[day].v==ZERO for view in views for day in dates):
                flags.append(f"zero_volume_{label}_padding")
        complete.decisions[a]=dict(year=e.year,refusal=refusal,early=f"{early}_day1" if early else None,
                                   padding=flags,unproved_cash_bridge=gaps,adjusted_insufficient=insufficient,
                                   unavailable=[(leg,kind,day.isoformat(),"missing" if day not in view else "zero_volume")
                                   for leg,tapes in per_leg.items() for kind,view in zip(VIEWS,tapes)
                                   for day in scope if not positive(view,day)],
                                   split_product=str(split_product(action[a]["stock"][0],e.entry,e.exit)))
        if refusal:
            del complete[a]
            continue
        starts=[(e.entry,c["cost"]["bps"]),(e.entry,c["cost"]["stress_bps"])]
        if early is None:
            starts.insert(0,(e.early,c["cost"]["bps"]))
        for start,bps in starts:
            for leg,(raw,seq,_) in complete[a].items():
                q = quantity(raw[start].o,c["capital"],bps,c)
                if leg == "stock" and start == e.entry and bps == c["cost"]["bps"]:
                    # A shown-only sleeve can hold any smaller feasible lot.
                    counts = {q,*range(1,quantity(raw[start].o,c["sleeve_usd"],bps,c)+1)}
                else:
                    counts = {q}
                for n in counts:
                    split_basis(n,seq,start,e.exit)
                if start == e.entry and leg == controls[0] and bps == c["cost"]["bps"]:
                    sq = quantity(complete[a]["stock"][0][start].o,c["capital"],bps,c)
                    need(q > 0 or sq == 0, "CONTROL_UNAFFORDABLE")
    return complete


def split_product(seq,start,end):
    product=Fraction(1)
    for ex,kind,value,_,_ in seq:
        if start<ex<=end and kind=="split":
            product*=exact(value)
    return product


def counts(rows):
    summary=dict(filing_eligible=len(rows),noncash_skipped=0,coverage_refused=0,coverage_kept=0,
                 refused_by_reason=dict.fromkeys(COVERAGE_REASONS,0),
                 padding_flags=dict.fromkeys(PADDING_FLAGS,0),early_omissions=dict.fromkeys(EARLY_REASONS,0),
                 unproved_cash_bridge_events=0,adjusted_insufficient_events=0)
    for r in rows:
        if r.get("noncash"):
            summary["noncash_skipped"]+=1
            continue
        if r["refusal"]:
            summary["coverage_refused"]+=1
            summary["refused_by_reason"][r["refusal"]]+=1
        else:
            summary["coverage_kept"]+=1
            if r["early"]:
                summary["early_omissions"][r["early"]]+=1
        for flag in r["padding"]:
            summary["padding_flags"][flag]+=1
        summary["unproved_cash_bridge_events"]+=bool(r["unproved_cash_bridge"])
        summary["adjusted_insufficient_events"]+=bool(r["adjusted_insufficient"])
    return summary


def coverage_summary(complete,c):
    rows=list(complete.decisions.values())
    years=range(c["first_year"],c["last_year"]+1)
    return counts(rows)|dict(by_acceptance_year={str(y):counts([r for r in rows if r["year"]==y]) for y in years},
                             cap=coverage_limit(sum(not r.get("noncash") for r in rows)))


def downside_floor(split,c):
    capital,floor=exact(c["capital"]),exact(c["cost"]["floor"])
    need(capital>0 and floor>0 and 0<=c["cost"]["bps"]<=10000,"BOUND_CONFIG")
    return -1-floor*(capital//floor)*exact(split)/capital


def fee(px,bps,c):
    return max(exact(px)*exact(bps)/10000,exact(c["cost"]["floor"]))


def quantity(px,capital,bps,c):
    return int(exact(capital)//(exact(px)+fee(px,bps,c)))


def split_basis(n,seq,start,end):
    for ex,kind,value,pay,available in seq:
        if start < ex <= end and kind == "split":
            n *= exact(value)
            need(n == int(n), "FRACTIONAL_SPLIT")
    return n


def trade(event, leg, start, capital, bps, c):
    raw,seq,target = leg
    op,cl = exact(raw[start].o),exact(raw[event.exit].c)
    q = quantity(op,capital,bps,c)
    if not q:
        return None
    deployed = q*(op+fee(op,bps,c))
    n, cash = q, []
    for ex, kind, value, pay, available in seq:
        if start < ex <= event.exit:
            if kind=="split":
                n *= exact(value)
            else:
                cash.append((available,n*exact(value)))
    proceeds = n*(cl-fee(cl,bps,c))
    pnl = proceeds+sum(v for _,v in cash)-deployed
    return SimpleNamespace(pnl=pnl, used=deployed, proceeds=proceeds, cash=cash,
                           economic=pnl/exact(capital), deployed=pnl/deployed,
                           yield_at_open=exact(event.declared)/op,
                           inside=target is not None and start < target <= event.exit)


def avg(x):
    return sum(map(exact,x))/len(x) if len(x) else None


def cluster(rows):
    if not rows:
        return {"n":0,"groups":0,"mean":None,"t":None,"variance":None}
    mu = avg([x for _,x in rows])
    buckets = defaultdict(list)
    for month,value in rows:
        buckets[month].append(exact(value)-mu)
    g,n = len(buckets),len(rows)
    var = Fraction(g,(g-1)*n*n)*sum(sum(vals)**2 for vals in buckets.values()) if g>1 else None
    t = None if not var else (1 if mu>=0 else -1)*sqrt(float(mu*mu/var))
    return {"n":n,"groups":g,"mean":mu,"t":t,"variance":var}


def marks(rows,c):
    m=c["marks"]
    def positive(v):
        return v is not None and v>0
    def enough_t(stat):
        mu,var=stat["mean"],stat["variance"]
        return positive(mu) and var is not None and var>0 and mu**2>=exact(m["t"])**2*var
    raw=cluster([(r.month,r.stock) for r in rows])
    paired=cluster([(r.month,exact(r.stock)-exact(r.control)) for r in rows])
    n=len(rows)
    drop=ceil(n*exact(m["trim"]))
    trimmed=avg([r.stock for r in sorted(rows,key=lambda z:(z.stock,z.a))[:n-drop]])
    per_year={str(y):avg([r.stock for r in rows if r.year==y]) for y in range(c["first_year"],c["last_year"]+1)}
    recent=avg([r.stock for r in rows if r.year>=m["recent"]])
    tests=dict(placed=n>=m["placed"],net=positive(raw["mean"]),clustered_t=enough_t(raw),
               trimmed=positive(trimmed),positive_years=sum(positive(v) for v in per_year.values())>=m["years"],
               recent=positive(recent),paired=enough_t(paired))
    return dict(marks=tests, passed=all(tests.values()), absolute=raw, paired=paired, trim_removed=drop,
                trimmed_mean=trimmed, by_acceptance_year=per_year, recent_mean=recent)


def sleeve_path(event_rows, complete, days, c):
    cash=[exact(c["sleeve_usd"])]*c["sleeves"]
    active={}
    due=[]
    total, placed, skips=Fraction(0),0,Counter()
    grouped=defaultdict(list)
    for e in event_rows:
        grouped[e.entry].append(e)
    for day in sorted(grouped):
        for k,(ex,issuer) in list(active.items()):
            if ex<day:
                del active[k]
        for pay,k,value,at_open in due:
            if pay<day or (pay==day and at_open):
                cash[k]+=value
        due=[item for item in due if item[0]>day or (item[0]==day and not item[3])]
        reserved=set()
        pending=set()
        for e in grouped[day]:
            if e.cik in pending or e.cik in {v[1] for v in active.values()}:
                skips["issuer_open"]+=1
                continue
            free=next((k for k in range(len(cash)) if k not in active and k not in reserved),None)
            if free is None:
                skips["no_free_sleeve"]+=1
                continue
            reserved.add(free)
            pending.add(e.cik)
            budget=min(cash[free],exact(c["sleeve_usd"]))
            t=trade(e,complete[e.a]["stock"],day,budget,c["cost"]["bps"],c)
            if t is None:
                skips["cannot_buy_share_or_unsettled"]+=1
                continue
            active[free]=(e.exit,e.cik)
            cash[free]-=t.used
            lag=next(n for start,n in reversed(c["settlement"]) if e.exit>=d(start))
            due.append((days[bisect_right(days,e.exit)+lag-1],free,t.proceeds,True))
            due.extend((pay,free,value,False) for pay,value in t.cash)
            total+=t.pnl
            placed+=1
    return dict(placed=placed, skips=dict(skips), pnl_usd=total,
                on_starting_cash=total/(exact(c["sleeve_usd"])*c["sleeves"]))


def report(event_rows, complete, days, c):
    out, shown = [], defaultdict(list)
    no=Counter()
    iwm,spy=c["controls"]
    cap=c["capital"]
    base,stress=c["cost"]["bps"],c["cost"]["stress_bps"]
    spy_cash=0
    modeled=[e for e in event_rows if e.a in complete]
    for e in modeled:
        bars=complete[e.a]
        stock=trade(e,bars["stock"],e.entry,cap,base,c)
        for key,entry,bps in (("entry_plus_one",e.early,base),("stress_cost",e.entry,stress)):
            if key=="entry_plus_one" and complete.decisions[e.a]["early"]:
                continue
            obj=trade(e,bars["stock"],entry,cap,bps,c)
            if obj:
                shown[key].append(obj.economic)
        if not stock:
            no[str(e.year)]+=1
            continue
        control=trade(e,bars[iwm],e.entry,cap,base,c)
        need(control is not None,"CONTROL_UNAFFORDABLE")
        out.append(SimpleNamespace(a=e.a,month=e.entry.strftime("%Y-%m"),year=e.year,stock=stock.economic,
                                   control=control.economic))
        shown["deployed"].append(stock.deployed)
        comp=trade(e,bars[spy],e.entry,cap,base,c)
        spy_cash+=comp is None
        shown["paired_spy"].append(stock.economic-(comp.economic if comp else 0))
        shown["declared_ex_inside" if stock.inside else "declared_ex_outside_or_canceled"].append(stock.economic)
        shown["first_time_"+e.first].append(stock.economic)
        ratio=c["size_breaks"]
        band=sum(stock.yield_at_open>=exact(x) for x in ratio)
        shown[f"size_bucket_{band}"].append(stock.economic)
    coverage=coverage_summary(complete,c)
    placed=Counter(str(r.year) for r in out)
    for y,s in coverage["by_acceptance_year"].items():
        s.update(judged_placed=placed[y],unaffordable=no[y])
    coverage.update(judged_placed=len(out),unaffordable=sum(no.values()))
    lost=[downside_floor(Fraction(r["split_product"]),c) for r in complete.decisions.values() if r.get("refusal")]
    full_denominator=len(modeled)+len(lost)
    bound=(sum(r.stock for r in out)+sum(lost))/full_denominator if full_denominator else None
    return dict(judged=marks(out,c), no_trade_unaffordable=sum(no.values()), no_trade_by_year=dict(no),
                eligible=len(event_rows),modeled=len(modeled),coverage=coverage,
                skipped_by_reason={NONCASH_SKIP:coverage["noncash_skipped"]}|coverage["refused_by_reason"],
                conservative_full_docket_stock_floor=bound,full_docket_floor_denominator=full_denominator,
                limitation=("This result speaks only for events with complete positive-volume SIP views on every judged "
                            "session that passed the tape checks and, for the judged marks, supported a placed stock and "
                            "IWM pair. It does not establish a return for every eligible filing."),
                idle_zero_mean=avg([r.stock for r in out]+[0]*sum(no.values())),
                shown={k:dict(n=len(vals),mean=avg(vals)) for k,vals in sorted(shown.items())},
                spy_unaffordable_cash=spy_cash,sleeves=sleeve_path(modeled,complete,days,c))


def calibrate(event_rows,c):
    """Planted edge on net allocation returns; never accepts a price or action packet."""
    cal=c["calibration"]
    schedule=[(e.a,e.entry.strftime("%Y-%m"),e.year) for e in event_rows]
    counts=[0 for _ in cal["edges"]]
    for trial in range(cal["trials"]):
        rng=random.Random(cal["seed"]+trial)
        months={}
        synthetic=[]
        for a,month,y in schedule:
            if month not in months:
                months[month]=(rng.gauss(0,float(cal["market_month"])),rng.gauss(0,float(cal["residual_month"])))
            market,residual=months[month]
            if rng.random()>=float(cal["placement"]):
                continue
            iwm=market+rng.gauss(0,float(cal["market_event"]))
            eps=rng.gauss(0,float(cal["residual_event"]))
            if rng.random()<float(cal["tail_chance"]):
                eps*=float(cal["tail_scale"])
            synthetic.append((a,month,y,exact(iwm),exact(residual)+exact(iwm)+exact(eps)))
        for k,edge in enumerate(cal["edges"]):
            rows=[SimpleNamespace(a=a,month=m,year=y,stock=stock+exact(edge),control=iwm)
                  for a,m,y,iwm,stock in synthetic]
            counts[k]+=marks(rows,c)["passed"]
    share=[n/cal["trials"] for n in counts]
    need(share[0]<=float(cal["null_ceiling"]),"CALIBRATION")
    return dict(data="synthetic only, real filing schedule", trials=cal["trials"],eligible=len(schedule),
                docket_sha256=c["docket_sha256"], all_mark_passes=counts, shares=share,
                edges=[float(x) for x in cal["edges"]])


def read_bytes(path,cap,private=False):
    need(path.resolve()==path,"FILE")
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),"rb") as f:
        s=os.fstat(f.fileno())
        need(stat.S_ISREG(s.st_mode) and s.st_size<=cap,"FILE")
        if private:
            need(s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o600,"PRIVATE")
        b=f.read(cap+1)
    need(len(b)<=cap,"FILE")
    return b


def file_bytes(path, pin, cap, private=False):
    need(is_pin(pin),"FILE")
    b=read_bytes(path,cap,private=private)
    need(sha256(b).hexdigest()==pin,"PIN")
    return b


def private_dir(path):
    s=path.lstat()
    need(path.resolve()==path and stat.S_ISDIR(s.st_mode) and s.st_uid==os.geteuid()
         and stat.S_IMODE(s.st_mode)==0o700,"PRIVATE")


def git(*args,allow=False):
    env={"PATH":"/usr/bin:/bin","LC_ALL":"C","GIT_CONFIG_NOSYSTEM":"1",
         "GIT_CONFIG_GLOBAL":"/dev/null","GIT_OPTIONAL_LOCKS":"0"}
    proc=subprocess.run(["/usr/bin/git","--no-replace-objects","-c","core.fsmonitor=false",
                         "-C",str(ROOT),*args],capture_output=True,env=env,timeout=20)
    need(allow or proc.returncode==0,"APPROVAL")
    return proc


def checkout(commit):
    need(type(commit) is str and re.fullmatch(r"[0-9a-f]{40}",commit),"APPROVAL")
    need(git("rev-parse","HEAD").stdout.strip()==commit.encode()
         and not git("status","--porcelain","--untracked-files=all").stdout,"DIRTY")


def contents(rev,name):
    return git("show",f"{rev}:{name}").stdout


def approval_line(commit,name,pattern):
    body=re.fullmatch(pattern,contents(commit,name))
    need(body is not None,"APPROVAL")
    parent=git("rev-list","--parents","-n","1",commit).stdout.split()[1:]
    need(len(parent)==1,"APPROVAL")
    need(git("diff-tree","--no-commit-id","--no-renames","--name-status","-r",commit).stdout
         == f"A\t{name}\n".encode(),"APPROVAL_SCOPE")
    return parent[0].decode(),list(map(bytes.decode,body.groups()))


def follows(ancestor,parent):
    need(git("merge-base","--is-ancestor",ancestor,parent,allow=True).returncode==0,"ANCESTOR")


def authorize(commit,mode):
    checkout(commit)
    go, validated, approval= None,None,None
    if mode=="go":
        parent,(approval,validated)=approval_line(commit,GO,GO_RE)
        follows(approval,parent)
        go=commit
    elif mode=="validate":
        approval=commit
    if approval:
        parent,(acq,acq_pin,ids,bars,actions,fetch_pin,native_pin,transport_pin,rebuild_pin)=approval_line(
            approval,APPROVAL,APPROVAL_RE)
        follows(acq,parent)
    else:
        acq=commit
    parent,(freeze,freeze_pin,docket_pin,collector_pin)=approval_line(acq,ACQUISITION,ACQUISITION_RE)
    follows(freeze,parent)
    need(collector_pin==COLLECTOR_SHA256,"COLLECTOR_PIN")
    for n in (ACQUISITION,APPROVAL,GO):
        need(git("cat-file","-e",f"{freeze}:{n}",allow=True).returncode!=0,"APPROVAL_FROZEN")
    refs=list(dict.fromkeys(r for r in (freeze,acq,approval,go) if r))
    manifest=file_bytes(ROOT/PINS,freeze_pin,16384)
    need(all(manifest==contents(rev,PINS) for rev in refs),"FREEZE")
    need(all(contents(acq,ACQUISITION)==contents(rev,ACQUISITION) for rev in refs[1:]),"ACQUISITION_PIN")
    if go:
        need(contents(approval,APPROVAL)==contents(go,APPROVAL),"VALIDATION_PIN")
    pins=parse(manifest)
    need(set(pins)==SOURCES and all(map(is_pin,pins.values())),"FREEZE")
    blobs={n:file_bytes(ROOT/n,pins[n],2**20) for n in SOURCES}
    need(all(b==contents(rev,n) for n,b in blobs.items() for rev in refs),"FREEZE")
    need(all([line for line in blobs[n].splitlines() if line.startswith(b"Status ")]==[b"Status FROZEN."]
             for n in (PLAN,AMENDMENT)),"FREEZE")
    for name,num,doc in (("research_rig/TRIAL_LEDGER.md",LEDGER,AMENDMENT),("docs/QUEUE.md",74,PLAN)):
        prefix=f"| {num} |".encode()
        a,*checks=([line for line in contents(r,name).splitlines() if line.startswith(prefix)] for r in refs)
        need(len(a)==1 and all(x==a for x in checks) and doc.encode() in a[0],"LEDGER_QUEUE")
    job=dict(ledger=LEDGER,acquisition_commit=acq,freeze_commit=freeze,freeze_sha256=freeze_pin,
             docket_sha256=docket_pin,collector_sha256=collector_pin)
    if approval:
        job|=dict(approval_commit=approval,acquisition_receipt_sha256=acq_pin,fetch_start_sha256=fetch_pin,
                  native_index_sha256=native_pin,transport_index_sha256=transport_pin,offline_rebuild_sha256=rebuild_pin,
                  **dict(zip(PACKETS,(ids,bars,actions))))
    if go:
        job|=dict(go_commit=go,validation_receipt_sha256=validated)
    return job,blobs


def unused(run):
    need(not any(os.path.lexists(run/n) for n in ("score.lock","result.json")),"CONSUMED")


def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_exclusive(path,b):
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),"wb") as f:
        f.write(b)
        f.flush()
        os.fsync(f.fileno())
    sync_dir(path.parent)


def once(run,job,calculate):
    unused(run)
    write_exclusive(run/"score.lock",render(dict(job,status="consumed")))
    payload=calculate()
    write_exclusive(run/"result.json",render(dict(job=job,outcome=payload)))


def local_schedule(blobs):
    c=config(blobs[CONFIG])
    ds=calendar([blobs[x] for x in CALENDARS])
    q=events(file_bytes(DOCKET,c["docket_sha256"],12*2**20,private=True),ds,c)
    return q,ds,c


def resources(c):
    need(sys.flags.isolated and sys.flags.dont_write_bytecode,"ISOLATION")
    p=c["resources"]
    with open("/proc/meminfo",encoding="ascii") as f:
        available=next(int(x.split()[1])*1024 for x in f if x.startswith("MemAvailable:"))
    need(available>=p["minimum_free_mib"]*2**20 and disk_usage(DATA).free>=p["disk_floor_mib"]*2**20,"RESOURCES")
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    cap=min(x for x in (soft,hard,p["process_cap_mib"]*2**20) if x!=resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS,(cap,hard))
    nice=os.nice(0)
    if nice<p["nice"]:
        os.nice(p["nice"]-nice)


def acquired(job,c,ids_pin,actions_pin):
    return dict(acquisition_commit=job["acquisition_commit"],freeze_commit=job["freeze_commit"],
                freeze_sha256=job["freeze_sha256"],docket_sha256=job["docket_sha256"],custodian=c["custodian"],
                ledger=LEDGER,input_dir=str(INPUT),collector_sha256=COLLECTOR_SHA256,
                identities_sha256=ids_pin,actions_sha256=actions_pin)


def check_native(blob,job,c,q,days,identity,ready,bars_blob):
    proof=ModuleType("p43_verified_provenance")
    exec(compile(blob,PROVENANCE,"exec"),proof.__dict__)
    api=SimpleNamespace(need=need,file_bytes=file_bytes,private_dir=private_dir,parse=parse,ET=ET,
                        money=money,VIEWS=VIEWS,ENDPOINT=ENDPOINT,COLLECTOR_SHA256=COLLECTOR_SHA256,LEDGER=LEDGER)
    proof.verify(api,INPUT,job,c,q,days,identity,ready,bars_blob)


def put_or_check(path,expected,cap):
    try:
        write_exclusive(path,expected)
    except FileExistsError:
        need(file_bytes(path,sha256(expected).hexdigest(),cap,private=True)==expected,"RECEIPT")


def approved(commit,mode):
    job,blobs=authorize(commit,mode)
    resources(config(blobs[CONFIG]))
    file_bytes(COLLECTOR,COLLECTOR_SHA256,2**20)
    q,days,c=local_schedule(blobs)
    proof=parse(blobs[CALIBRATION])
    need(job["docket_sha256"]==c["docket_sha256"]==proof["docket_sha256"]
         and proof["trials"]==c["calibration"]["trials"] and proof["eligible"]==len(q)
         and proof["edges"]==c["calibration"]["edges"]
         and proof["shares"][0]<=c["calibration"]["null_ceiling"],"CALIBRATION")
    private_dir(INPUT)
    private_dir(RUN)
    unused(RUN)
    receipt=INPUT/f'acquisition.{job["acquisition_commit"]}.lock'
    if mode in ("acquire","custody"):
        need(not os.path.lexists(INPUT/"bars.json"),"BARS_ALREADY_STAGED")
        native=INPUT/"native"
        need(not any(INPUT.glob("fetch_start.*.lock")) and
             (not os.path.lexists(native) or (native.is_dir() and not native.is_symlink() and
              next(native.iterdir(),None) is None)),"CUSTODY_CONSUMED")
        ids=read_bytes(INPUT/"identities.json",8*2**20,private=True)
        acts=read_bytes(INPUT/"actions.json",32*2**20,private=True)
        identity_actions(q,days,c,parse(ids),parse(acts))
        expected=render(acquired(job,c,sha256(ids).hexdigest(),sha256(acts).hexdigest()))
        if mode=="acquire":
            write_exclusive(receipt,expected)
            print("P43_ACQUISITION_CLAIMED")
        else:
            need(file_bytes(receipt,sha256(expected).hexdigest(),16384,private=True)==expected,"ACQUISITION_RECEIPT")
            print("P43_CUSTODY_READY")
        return
    expected=render(acquired(job,c,job["identities.json"],job["actions.json"]))
    need(file_bytes(receipt,job["acquisition_receipt_sha256"],16384,private=True)==expected,"ACQUISITION_RECEIPT")
    C=engine(blobs[ENGINE])
    cap=(8*2**20,96*2**20,32*2**20)
    packet_blobs=[file_bytes(INPUT/name,job[name],n,private=True) for name,n in zip(PACKETS,cap)]
    packets=list(map(parse,packet_blobs))
    ready=prepared(q,days,C,c,*packets)
    check_native(blobs[PROVENANCE],job,c,q,days,packets[0],ready,packet_blobs[1])
    del packets,packet_blobs
    unused(RUN)
    validated=RUN/f'validation.{job["approval_commit"]}.json'
    coverage=RUN/f'coverage.{job["approval_commit"]}.json'
    coverage_bytes=render(dict(summary=coverage_summary(ready,c),decisions=ready.decisions))
    coverage_pin=sha256(coverage_bytes).hexdigest()
    if mode=="validate":
        put_or_check(coverage,coverage_bytes,16*2**20)
    else:
        need(file_bytes(coverage,coverage_pin,16*2**20,private=True)==coverage_bytes,"COVERAGE_RECEIPT")
    enforce_coverage(ready)
    expected=render(dict(status="validated_no_returns",coverage_sha256=coverage_pin,
                         rebuilt_bars_sha256=job["bars.json"],**{k:v for k,v in job.items() if k not in
                         ("go_commit","validation_receipt_sha256")}))
    validation_pin=sha256(expected).hexdigest()
    if mode=="validate":
        put_or_check(validated,expected,16384)
        print("P43_VALIDATED")
        return
    need(job["validation_receipt_sha256"]==validation_pin and
         file_bytes(validated,validation_pin,16384,private=True)==expected,"VALIDATION_RECEIPT")
    # Confirm all approval and freeze bytes again immediately before claiming the one score.
    again,rechecked=authorize(commit,"go")
    need(again==job and rechecked==blobs,"APPROVAL_CHANGED")
    job.update(started_utc=datetime.now(timezone.utc).isoformat())
    once(RUN,job,lambda:report(q,ready,days,c))
    print("P43_SCORED_ONCE")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    for flag in ("claim-acquisition","check-custody","validate-inputs","go","calibrate","self-test"):
        mode.add_argument("--"+flag,action="store_true")
    parser.add_argument("--approval-commit")
    a=parser.parse_args()
    if bool(a.approval_commit)!=bool(a.go or a.validate_inputs or a.claim_acquisition or a.check_custody):
        parser.error("real modes require --approval-commit; synthetic modes reject it")
    try:
        if a.self_test:
            # Isolated tests operate on temporary synthetic packet paths only.
            test=subprocess.run([sys.executable,"-B",str(ROOT/"research_rig/test_43.py")])
            return test.returncode
        if a.calibrate:
            blobs={n:(ROOT/n).read_bytes() for n in (CONFIG,*CALENDARS)}
            rows,_,c=local_schedule(blobs)
            sys.stdout.buffer.write(render(calibrate(rows,c)))
            return 0
        approved(a.approval_commit,"go" if a.go else "validate" if a.validate_inputs else
                 "custody" if a.check_custody else "acquire")
    except Refused as exc:
        print(str(exc),file=sys.stderr)
        return 2
    except (Exception,KeyboardInterrupt):
        # Don't expose native vendor data, keys, or row values in parsing errors.
        print("P43_REFUSED",file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
