"""Plan 60, filing schedule and sealed-tape candidate; no networking."""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from hashlib import sha256
import os
from pathlib import Path
import re
import runpy
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent.parent
p=SimpleNamespace(**runpy.run_path(str(ROOT/"research_rig/score_43.py")))
need=p.need
DATA=p.DATA
INPUT=p.INPUT
RUN=DATA/"replay_60"
VENDOR=DATA/"plan60_vendor_actions"
PLAN="research_rig/PREREG_60_special_dividends.md"
PROOF="research_rig/CALIBRATION_60.json"
PINS="research_rig/PINNED_60.json"
ADOPT="research_rig/ADOPTION_60.md"
VALID="research_rig/APPROVAL_60.md"
GO="research_rig/GO_60.md"
LEDGER=199
QUEUE=99
PRICE_BASE="f7f2fbf52f9993bbc8dbb9d8d45c0e09e12d8584"
PRICE_PRIOR=p.PREVIOUS_VALIDATION
VENDOR_ENDPOINT="https://data.alpaca.markets/v1/corporate-actions"
VENDOR_NAME="vendor_actions.json"
VENDOR_INDEX="vendor_action_index.json"
b=SimpleNamespace(**runpy.run_path(str(ROOT/"research_rig/basis_43.py")))
SOURCES={PLAN,PROOF,p.CONFIG,p.ENGINE,p.PROVENANCE,p.BASIS,*p.CALENDARS,
         "research_rig/score_43.py","research_rig/score_60.py","research_rig/test_60.py"}
ADOPT_RE=(rb"Approved by the lead: plan 60 ledger 199, adopt sealed Plan 43 prices from validation commit "
          +p.UUID+rb", prior approval SHA-256 "+p.SHA+rb", freeze commit "+p.UUID+rb", freeze SHA-256 "+p.SHA+
          rb", no price acquisition\.\n")
VALID_RE=(rb"Approved by the lead: plan 60 ledger 199, validation only, adoption commit "+p.UUID+
          rb", adoption approval SHA-256 "+p.SHA+rb", vendor actions SHA-256 "+p.SHA+
          rb", vendor native index SHA-256 "+p.SHA+rb"\.\n")
GO_RE=(rb"Approved by the lead: plan 60 ledger 199, one scored run, validation approval commit "+p.UUID+
       rb", validation receipt SHA-256 "+p.SHA+rb"\.\n")


def authorize(commit,mode):
    p.checkout(commit)
    go=receipt=None
    if mode=="go":
        parent,(validation,receipt)=p.approval_line(commit,GO,GO_RE)
        need(parent==validation,"P60_ANCESTOR")
        go=commit
    else:
        validation=commit
    parent,(adoption,adopt_pin,vendor_pin,index_pin)=p.approval_line(validation,VALID,VALID_RE)
    need(parent==adoption,"P60_ANCESTOR")
    parent,(prior,prior_pin,freeze,freeze_pin)=p.approval_line(adoption,ADOPT,ADOPT_RE)
    need(parent==freeze and prior==PRICE_PRIOR,"P60_ADOPTION")
    p.follows(PRICE_BASE,freeze)
    p.follows(prior,PRICE_BASE)
    parent,(acq,acq_pin,ids,bars,actions,fetch,native,transport,rebuild)=p.approval_line(prior,p.APPROVAL,p.APPROVAL_RE)
    p.follows(acq,parent)
    parent,(old_freeze,old_fp,docket,collector)=p.approval_line(acq,p.ACQUISITION,p.ACQUISITION_RE)
    p.follows(old_freeze,parent)
    need(collector==p.COLLECTOR_SHA256,"P60_COLLECTOR_PIN")
    refs=tuple(x for x in (freeze,adoption,validation,go) if x)
    for name,ref,pin in ((p.ACQUISITION,acq,None),(p.APPROVAL,prior,prior_pin),
                         (ADOPT,adoption,adopt_pin),(VALID,validation,None)):
        body=p.contents(ref,name)
        need((pin is None or sha256(body).hexdigest()==pin) and
             all(p.contents(r,name)==body for r in (refs[refs.index(ref):] if ref in refs else refs)),
             "P60_APPROVAL_PIN")
    for name in (ADOPT,VALID,GO):
        need(p.git("cat-file","-e",f"{freeze}:{name}",allow=True).returncode!=0,"P60_APPROVAL_FROZEN")
    manifest=p.file_bytes(ROOT/PINS,freeze_pin,16384)
    need(all(p.contents(r,PINS)==manifest for r in refs),"P60_FREEZE")
    pins=p.parse(manifest)
    need(set(pins)==SOURCES and all(map(p.is_pin,pins.values())),"P60_FREEZE")
    blobs={n:p.file_bytes(ROOT/n,pin,2**20) for n,pin in pins.items()}
    need(all(body==p.contents(r,n) for n,body in blobs.items() for r in refs),"P60_FREEZE")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")]==[b"Status FROZEN."],"P60_FREEZE")
    need(p.config(blobs[p.CONFIG])==p.config(p.contents(PRICE_BASE,p.CONFIG)) and
         all(blobs[n]==p.contents(PRICE_BASE,n) for n in (p.ENGINE,p.PROVENANCE,p.BASIS,*p.CALENDARS,
                                                          "research_rig/score_43.py")),"P60_INHERITED_TERMS")
    for num,name in ((LEDGER,"research_rig/TRIAL_LEDGER.md"),(QUEUE,"docs/QUEUE.md")):
        prefix=f"| {num} |".encode()
        row,*others=([x for x in p.contents(r,name).splitlines() if x.startswith(prefix)] for r in refs)
        need(len(row)==1 and PLAN.encode() in row[0] and all(x==row for x in others),"P60_LEDGER_QUEUE")
    price=dict(acquisition_commit=acq,freeze_commit=old_freeze,freeze_sha256=old_fp,
               docket_sha256=docket,collector_sha256=collector,acquisition_receipt_sha256=acq_pin,
               fetch_start_sha256=fetch,native_index_sha256=native,transport_index_sha256=transport,
               offline_rebuild_sha256=rebuild,**dict(zip(p.PACKETS,(ids,bars,actions))))
    job=dict(plan=60,ledger=LEDGER,queue=QUEUE,freeze_commit=freeze,freeze_sha256=freeze_pin,
             price_adoption_source=prior,price_source_approval_sha256=prior_pin,
             adoption_commit=adoption,adoption_sha256=adopt_pin,validation_commit=validation,
             vendor_actions_sha256=vendor_pin,vendor_index_sha256=index_pin,adopted_price=price)
    if go:
        job.update(go_commit=go,validation_receipt_sha256=receipt)
    return job,blobs


def vendor_native(index_blob,meta,c):
    z=p.parse(index_blob)
    need(set(z)=={"version","custodian","endpoint","adoption","status","files"} and z["version"]==1 and
         z["custodian"]==c["custodian"] and z["endpoint"]==VENDOR_ENDPOINT and z["adoption"]==meta and
         z["status"]=="complete" and type(z["files"]) is list and bool(z["files"]),"P60_VENDOR_NATIVE")
    root=VENDOR/"native"
    p.private_dir(root)
    names=set()
    for row in z["files"]:
        name=row["file"]
        need(set(row)=={"file","status","sha256","bytes"} and re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.-]{0,150}",name)
             and name not in names and type(row["status"]) is int and 100<=row["status"]<=599,
             "P60_VENDOR_NATIVE")
        names.add(name)
        blob=p.file_bytes(root/name,row["sha256"],8*2**20,private=True)
        need(type(row["bytes"]) is int and len(blob)==row["bytes"],"P60_VENDOR_NATIVE")
    need({n.name for n in root.iterdir()}==names,"P60_VENDOR_NATIVE")


def approved(commit,mode):
    job,blobs=authorize(commit,mode)
    c=config(blobs[p.CONFIG])
    p.resources(c)
    for path in (INPUT,RUN,VENDOR):
        p.private_dir(path)
    p.unused(RUN)
    price=job["adopted_price"]
    p.file_bytes(p.COLLECTOR,p.COLLECTOR_SHA256,2**20)
    days=p.calendar([blobs[n] for n in p.CALENDARS])
    docket=p.file_bytes(p.DOCKET,price["docket_sha256"],12*2**20,private=True)
    q=p.events(docket,days,c)
    proof=p.parse(blobs[PROOF])
    need(proof["plan"]==60 and proof["ledger"]==LEDGER and proof["queue"]==QUEUE and
         proof["placed_floor"]==c["marks"]["placed"] and
         set(proof["cases"])=={str(v) for v in c["placement_cases"]},"P60_CALIBRATION")
    for case in proof["cases"].values():
        need(case["docket_sha256"]==price["docket_sha256"] and case["eligible"]==len(q) and
             case["edges"]==c["calibration"]["edges"] and case["trials"]==c["calibration"]["trials"] and
             case["shares"][0]<=c["calibration"]["null_ceiling"],"P60_CALIBRATION")
    acq=price["acquisition_commit"]
    receipt=p.render(p.acquired(price,c,price["identities.json"],price["actions.json"]))
    need(p.file_bytes(INPUT/f"acquisition.{acq}.lock",price["acquisition_receipt_sha256"],16384,private=True)
         ==receipt,"P60_PRICE_RECEIPT")
    raw={name:p.file_bytes(INPUT/name,price[name],cap,private=True)
         for name,cap in zip(p.PACKETS,(8*2**20,96*2**20,32*2**20))}
    ids,bars,actions=[p.parse(raw[name]) for name in p.PACKETS]
    verified=p.identity_actions(q,days,c,ids,actions)
    nscope=p.Prepared()
    nscope.decisions={e.a:dict(noncash=e.a not in verified[2]) for e in q}
    p.check_native(blobs[p.PROVENANCE],price,c,q,days,ids,nscope,raw["bars.json"])
    meta=dict(docket_sha256=price["docket_sha256"],identities_sha256=price["identities.json"],
              bars_sha256=price["bars.json"])
    index=p.file_bytes(VENDOR/VENDOR_INDEX,job["vendor_index_sha256"],32*2**20,private=True)
    vendor_native(index,meta,c)
    actions_blob=p.file_bytes(VENDOR/VENDOR_NAME,job["vendor_actions_sha256"],64*2**20,private=True)
    external=p.parse(actions_blob)
    need(external["native_index_sha256"]==job["vendor_index_sha256"],"P60_VENDOR_BINDING")
    vendor=schema_vendor(external,meta,q,verified[0],c)
    C=p.engine(blobs[p.ENGINE])
    tapes=market_tapes(q,days,C,c,ids,bars,verified)
    decisions,staged=prepare(q,tapes,vendor,c)
    print_summary=rollup(decisions,c)
    v=job["validation_commit"]
    decisions_blob=p.render(dict(summary=print_summary,decisions=decisions))
    path=RUN/f"decisions.{v}.json"
    validated=RUN/f"validation.{v}.json"
    expected=p.render(dict(status="validated_no_returns",decisions_sha256=sha256(decisions_blob).hexdigest(),
                           **{k:v for k,v in job.items() if k not in ("go_commit","validation_receipt_sha256")}))
    if mode=="validate":
        p.put_or_check(path,decisions_blob,16*2**20)
        p.put_or_check(validated,expected,16384)
        print(p.render(print_summary).decode(),end="")
        print("P60_VALIDATED")
        return
    pin=sha256(expected).hexdigest()
    need(job["validation_receipt_sha256"]==pin and p.file_bytes(validated,pin,16384,private=True)==expected
         and p.file_bytes(path,sha256(decisions_blob).hexdigest(),16*2**20,private=True)==decisions_blob,
         "P60_VALIDATION_RECEIPT")
    need(authorize(commit,"go")== (job,blobs),"P60_APPROVAL_CHANGED")
    job.update(started_utc=datetime.now(timezone.utc).isoformat())
    p.once(RUN,job,lambda:score(q,decisions,staged,days,c))
    print("P60_SCORED_ONCE")


def yes(view,day):
    return day in view and view[day].v>0


def schema_vendor(packet,meta,q,keyed,c):
    need(type(packet) is dict and set(packet)=={"version","custodian","endpoint","adoption","native_index_sha256","records"}
         and packet["version"]==1 and packet["custodian"]==c["custodian"] and packet["endpoint"]==VENDOR_ENDPOINT
         and packet["adoption"]==meta,"P60_VENDOR_SHAPE")
    expected={e.a for e in q}-{p.NONCASH_ACCESSION}
    need(set(packet["records"])==expected,"P60_VENDOR_SHAPE")
    out={}
    seen={}
    for e in q:
        if e.a not in expected:
            continue
        legs=packet["records"][e.a]
        ids=keyed[e.a][1]
        need(set(legs)==set(ids),"P60_VENDOR_SHAPE")
        out[e.a]={}
        through=e.end+timedelta(days=c["vendor_tail_days"])
        for leg,r in legs.items():
            ident=ids[leg]
            need(set(r)=={"identity","ticker","views","start","through","complete","items"} and
                 (r["identity"],r["ticker"])==(ident["identity"],ident["ticker"]) and
                 r["start"]==str(e.start) and r["through"]==str(through) and type(r["complete"]) is bool and
                 set(r["views"])=={"all","filing_all"} and
                 all(type(x) is str and 0<len(x)<=100 for x in r["views"].values()) and type(r["items"]) is list,
                 "P60_VENDOR_SCOPE")
            items={}
            for a in r["items"]:
                kind=a["type"]
                identifier=a["id"]
                ex=p.d(a["ex"])
                fields={"id","type","ex"}|(
                    {"cash_usd","factor"} if kind=="cash" else {"new","old"} if kind=="split" else {"vendor_type"})
                need(kind in {"cash","split","nonprice","unsupported"} and
                     set(a)==fields and type(identifier) is str and 0<len(identifier)<=120 and
                     identifier not in items and e.start<=ex<=through,"P60_VENDOR_ACTION")
                factor=None
                if kind=="cash":
                    need(type(a["cash_usd"]) is str and
                         (a["factor"] is None or type(a["factor"]) is str),"P60_VENDOR_ACTION")
                    amount=p.exact(p.money(a["cash_usd"]))
                    factor=None if a["factor"] is None else p.exact(p.money(a["factor"]))
                    need(amount>0 and (factor is None or 0<factor<1),"P60_VENDOR_ACTION")
                elif kind=="split":
                    need(type(a["new"]) is str and type(a["old"]) is str,"P60_VENDOR_ACTION")
                    new,old=(p.exact(p.money(a[x])) for x in ("new","old"))
                    need(new>0 and old>0,"P60_VENDOR_ACTION")
                    amount=new/old
                    factor=1/amount
                else:
                    need(type(a["vendor_type"]) is str and 0<len(a["vendor_type"])<=100,"P60_VENDOR_ACTION")
                    amount=a["vendor_type"]
                item=(ex,kind,amount,factor)
                key=(r["identity"],identifier)
                need(key not in seen or seen[key]==item,"P60_VENDOR_CONFLICT")
                seen[key]=items[identifier]=item
            out[e.a][leg]=(r["complete"] and all(v==ident["identity"] for v in r["views"].values()),
                           sorted(items.values(),key=lambda x:(x[0],x[1],str(x[2]),str(x[3]))))
    return out


def vendor_compare(raw,adjusted,filing,scope,items,error):
    """Apply vendor changes backwards from last session and fit one joint tail factor."""
    factors=defaultdict(list)
    tail=[(kind,mult) for ex,kind,_,mult in items if kind!="nonprice" and ex>scope[-1]]
    for ex,kind,value,mult in items:
        if kind=="nonprice" or ex>scope[-1]:
            continue
        if kind=="unsupported":
            return "unsupported_vendor_action",False,bool(tail)
        if ex==scope[0]:
            continue  # No pre-ex observation inside this window.
        if ex not in scope:
            return "vendor_action_not_session",False,bool(tail)
        factors[ex].append((kind,value,mult))
    common=(Fraction(0),None)
    scale=Fraction(1)
    checked=[0,0]
    for i in range(len(scope)-1,-1,-1):
        day=scope[i]
        for k,view in enumerate((adjusted,filing)):
            if not (yes(raw,day) and yes(view,day)):
                continue
            checked[k]+=1
            for x,y in zip(raw[day].flat_key,view[day].flat_key):
                x=p.exact(x)*scale
                y=p.exact(y)
                common=b.intersect(common,(max(0,y-error)/x,(y+error)/x))
                if common is None:
                    return "vendor_basis_mismatch",False,bool(tail)
        today=factors[day]
        splits=[row for row in today if row[0]=="split"]
        cash=[row for row in today if row[0]=="cash"]
        if len(splits)>1 or (splits and cash) or (len(cash)>1 and any(r[2] is not None for r in cash)):
            return "unsupported_vendor_action_combination",False,bool(tail)
        if splits:
            scale*=splits[0][2]
        elif cash:
            amount=sum(r[1] for r in cash)
            explicit=cash[0][2] if len(cash)==1 else None
            if explicit is not None:
                scale*=explicit
            elif not yes(raw,scope[i-1]) or p.exact(raw[scope[i-1]].c)<=amount:
                return "vendor_cash_reference_missing_or_invalid",False,bool(tail)
            else:
                scale*=1-amount/p.exact(raw[scope[i-1]].c)
    if min(checked)<3:
        return "vendor_basis_insufficient",False,bool(tail)
    known=bool(tail) and all(mult is not None for _,mult in tail)
    product=Fraction(1)
    if known:
        for _,mult in tail:
            product*=mult
    explains=known and b.intersect(common,(product,product)) is not None
    return None,explains,bool(tail)


def terms_delta(items,verified,scope):
    a=Counter((ex,kind,value) for ex,kind,value,_ in items
              if scope[0]<=ex<=scope[-1] and kind in ("cash","split","unsupported"))
    z=Counter((ex,"split" if kind=="split" else "cash",p.exact(value)) for ex,kind,value,*_ in verified
              if scope[0]<=ex<=scope[-1])
    return sum((a-z).values()),sum((z-a).values())


def event_execution(e,raw,scope,c):
    padding=[day for day in scope if day<e.early]
    need(len(padding)==c["pre_padding_sessions"],"P60_PADDING")
    if not all(yes(raw,day) for day in padding):
        return "outside_padding_volume",None
    dollars=sorted(p.exact(raw[day].c)*p.exact(raw[day].v) for day in padding)
    if dollars[len(dollars)//2]<c["min_median_dollar_volume"]:
        return "outside_dollar_volume",None
    if not yes(raw,e.entry):
        return "unfilled_entry",None
    for day in scope[scope.index(e.exit):scope.index(e.exit)+1+c["exit_wait_sessions"]]:
        if yes(raw,day):
            return None,day
    return "refused_no_exit",None


def market_tapes(q,days,C,c,ids,bars,verified):
    keyed,actions,modeled=verified
    need(bars["version"]==1 and bars["custodian"]==c["custodian"] and bars["endpoint"]==p.ENDPOINT and
         bars["feed"]=="sip" and bars["timeframe"]=="1Day" and bars["adjustments"]==["raw","all"] and
         set(bars["records"])==set(modeled),"P60_BARS")
    available={}
    seen=defaultdict(dict)
    reverse=defaultdict(set)
    hits=defaultdict(set)
    for e in q:
        if e.a not in modeled:
            continue
        z=bars["records"][e.a]
        leg_ids=keyed[e.a][1]
        need(set(z)==set(leg_ids),"P60_BARS")
        scope=days[bisect_left(days,e.start):bisect_right(days,e.end)]
        active={}
        for leg,r in z.items():
            ident=leg_ids[leg]
            need((r["ticker"],r["identity"],r["entry_asof"],r["filing_asof"],r["start"],r["end"])
                 ==(ident["ticker"],ident["identity"],str(e.entry),str(e.at.date()),str(e.start),str(e.end))
                 and all(type(r[x]) is list for x in p.VIEWS),"P60_BAR_SCOPE")
            parsed=tuple(p.tape(r[v],set(scope),C) for v in p.VIEWS)
            key=r["identity"]
            for day,bar in parsed[0].items():
                need(day not in seen[key] or seen[key][day]==bar,"P60_BAR_CONFLICT")
                seen[key][day]=bar
            for view in parsed:
                for day,bar in view.items():
                    if bar.v<=0:
                        continue
                    owners=reverse[(day,bar)]
                    for other in owners-{key}:
                        matches=hits[tuple(sorted((key,other)))]
                        matches.add(day)
                        need(len(matches)<3,"P60_BAR_ALIAS")
                    owners.add(key)
            active[leg]=parsed
        available[e.a]=(scope,active,actions[e.a])
    return available


def lot_ok(record,start,end,bps,capital,c):
    raw,seq,_=record
    if not yes(raw,start) or not yes(raw,end):
        return False
    n=p.quantity(raw[start].o,capital,bps,c)
    p.split_basis(n,seq,start,end)
    return n>0


def prepare(q,available,vendor,c):
    decisions={}
    staged={}
    error=p.exact(p.money(c["ohlc_tick"]))/2+p.exact(p.money(c["ohlc_slack"]))
    for e in q:
        if e.a not in available:
            decisions[e.a]=dict(year=e.year,reason="noncash_skip")
            continue
        scope,tapes,acts=available[e.a]
        status,exit_day=event_execution(e,tapes["stock"][0],scope,c)
        failures={}
        tails={}
        diffs={}
        for leg,(raw,entry,filing) in tapes.items():
            complete,items=vendor[e.a][leg]
            why,explain,post=(vendor_compare(raw,entry,filing,scope,items,error) if complete else
                             ("vendor_mapping_or_coverage",False,False))
            if why:
                failures[leg]=why
            tails[leg]=dict(post_action=post,post_action_explains=explain)
            diffs[leg]=terms_delta(items,acts[leg][0],scope)
        info=dict(year=e.year,reason=status,vendor_basis=failures,tail=tails,action_delta=diffs,
                  effective_exit=exit_day.isoformat() if exit_day else None)
        decisions[e.a]=info
        if exit_day is None:
            continue
        records={leg:(tapes[leg][0],*acts[leg]) for leg in tapes}
        stock=records["stock"]
        iwm,spy=c["controls"]
        base=c["cost"]["bps"]
        cap=c["capital"]
        supports_iwm=yes(records[iwm][0],e.entry) and yes(records[iwm][0],exit_day)
        for arm,start,cost,legs in (("base",e.entry,base,records),("stress",e.entry,c["cost"]["stress_bps"],{"stock":stock}),
                                       ("early",e.early,base,{"stock":stock})):
            for rec in legs.values():
                lot_ok(rec,start,exit_day,cost,cap,c)
        for n in range(1,p.quantity(stock[0][e.entry].o,c["sleeve_usd"],base,c)+1):
            p.split_basis(n,stock[1],e.entry,exit_day)
        stock_lot=lot_ok(stock,e.entry,exit_day,base,cap,c)
        control_lot=supports_iwm and lot_ok(records[iwm],e.entry,exit_day,base,cap,c)
        if failures:
            info["reason"]="refused_vendor_basis"
        elif not stock_lot:
            info["reason"]="unfilled_capital"
        elif not supports_iwm:
            info["reason"]="unfilled_iwm_clock"
        elif not control_lot:
            info["reason"]="unfilled_iwm_capital"
        else:
            info["reason"]="eligible_pair"
        info.update(delayed=exit_day!=e.exit,inside_no_bar=sum(not yes(stock[0],day)
                    for day in scope if e.entry<day<exit_day),show_basis_excluded=bool(failures and stock_lot))
        staged[e.a]=(records,exit_day,stock_lot,control_lot)
    return decisions,staged


COUNTS=("noncash_skip","outside_padding_volume","outside_dollar_volume","unfilled_entry","refused_no_exit",
        "refused_vendor_basis","unfilled_capital","unfilled_iwm_clock","unfilled_iwm_capital","eligible_pair")


def rollup(decisions,c):
    def one(rows):
        k=Counter(r["reason"] for r in rows)
        tails=[v for r in rows for v in r.get("tail",{}).values()]
        diffs=[v for r in rows for v in r.get("action_delta",{}).values()]
        return dict(events=len(rows),reason_counts={name:k[name] for name in COUNTS},
                    post_window_action_legs=sum(x["post_action"] for x in tails),
                    post_window_action_explains_legs=sum(x["post_action_explains"] for x in tails),
                    vendor_only_in_window_actions=sum(x[0] for x in diffs),
                    filing_only_in_window_actions=sum(x[1] for x in diffs),
                    vendor_basis_refusal_reasons=dict(Counter(why for r in rows for why in r.get("vendor_basis",{}).values())),
                    delayed_exits=sum(bool(r.get("delayed")) for r in rows),
                    inside_unavailable_sessions=sum(r.get("inside_no_bar",0) for r in rows))
    rows=list(decisions.values())
    return one(rows)|dict(by_year={str(y):one([r for r in rows if r["year"]==y])
                                   for y in range(c["first_year"],c["last_year"]+1)})


def fill(e,rec,start,end,capital,bps,c):
    """Arms all use the stock clock; only verified actions affect cash and share count."""
    raw,seq,target=rec
    if not yes(raw,start) or not yes(raw,end):
        return None
    op=p.exact(raw[start].o)
    cl=p.exact(raw[end].c if end==e.exit else raw[end].o)
    n=p.quantity(op,capital,bps,c)
    if not n:
        return None
    used=n*(op+p.fee(op,bps,c))
    cash=[]
    for ex,kind,value,_,available in seq:
        if start<ex<=end:
            if kind=="split":
                n*=p.exact(value)
                need(n==int(n),"P60_FRACTIONAL_SPLIT")
            else:
                cash.append((available,n*p.exact(value)))
    proceeds=n*(cl-p.fee(cl,bps,c))
    pnl=proceeds+sum(v for _,v in cash)-used
    return SimpleNamespace(pnl=pnl,economic=pnl/p.exact(capital),deployed=pnl/used,used=used,
                           cash=cash,proceeds=proceeds,inside=target is not None and start<target<=end,
                           yield_at_open=p.exact(e.declared)/op)


def sleeves(q,decisions,staged,days,c):
    cap=c["sleeve_usd"]
    slots=[p.exact(cap) for _ in range(c["sleeves"])]
    due=[]
    active={}
    skips=Counter()
    pnl=Fraction(0)
    placed=0
    grouped=defaultdict(list)
    for e in q:
        if e.a in staged and not decisions[e.a]["vendor_basis"]:
            grouped[e.entry].append(e)
    for day in sorted(grouped):
        active={slot:(end,cik) for slot,(end,cik) in active.items() if end>=day}
        for release,k,amount,at_open in due:
            if release<day or (release==day and at_open):
                slots[k]+=amount
        due=[(r,k,a,o) for r,k,a,o in due if r>day or (r==day and not o)]
        reserved=set()
        pending=set()
        for e in grouped[day]:
            if e.cik in pending or e.cik in {v[1] for v in active.values()}:
                skips["issuer_open"]+=1
                continue
            free=next((k for k in range(len(slots)) if k not in active and k not in reserved),None)
            if free is None:
                skips["no_free_sleeve"]+=1
                continue
            reserved.add(free)
            pending.add(e.cik)
            records,end,*_=staged[e.a]
            t=fill(e,records["stock"],day,end,min(slots[free],p.exact(cap)),c["cost"]["bps"],c)
            if t is None:
                skips["cannot_buy_share_or_unsettled"]+=1
                continue
            lag=next(n for start,n in reversed(c["settlement"]) if end>=p.d(start))
            index=bisect_right(days,end)+lag-1
            need(index<len(days),"P60_SETTLEMENT")
            slots[free]-=t.used
            active[free]=(end,e.cik)
            due.append((days[index],free,t.proceeds,True))
            due.extend((pay,free,value,False) for pay,value in t.cash)
            placed+=1
            pnl+=t.pnl
    return dict(placed=placed,skips=dict(skips),pnl_usd=pnl,on_starting_cash=pnl/(c["sleeves"]*cap))


def score(q,decisions,staged,days,c):
    rows=[]
    broad=[]
    broad_pair=[]
    shown=defaultdict(list)
    iwm,spy=c["controls"]
    for e in q:
        if e.a not in staged:
            continue
        rec,end,stock_lot,control_lot=staged[e.a]
        base=c["cost"]["bps"]
        cap=c["capital"]
        t=fill(e,rec["stock"],e.entry,end,cap,base,c)
        control=fill(e,rec[iwm],e.entry,end,cap,base,c)
        if t:
            broad.append(t.economic)
            if control:
                broad_pair.append(t.economic-control.economic)
        if decisions[e.a]["reason"]=="eligible_pair":
            need(t is not None and control is not None,"P60_PAIR")
            rows.append(SimpleNamespace(a=e.a,month=e.entry.strftime("%Y-%m"),year=e.year,
                                        stock=t.economic,control=control.economic))
        if decisions[e.a]["vendor_basis"]:
            continue
        for key,start,cost in (("entry_plus_one",e.early,base),("stress_cost",e.entry,c["cost"]["stress_bps"])):
            out=fill(e,rec["stock"],start,end,cap,cost,c)
            if out:
                shown[key].append(out.economic)
        if not t:
            continue
        cmp=fill(e,rec[spy],e.entry,end,cap,base,c)
        if cmp:
            shown["paired_spy"].append(t.economic-cmp.economic)
        shown["deployed"].append(t.deployed)
        shown["declared_ex_inside" if t.inside else "declared_ex_outside_or_canceled"].append(t.economic)
        shown["first_time_"+e.first].append(t.economic)
        band=sum(t.yield_at_open>=p.exact(x) for x in c["size_breaks"])
        shown[f"size_bucket_{band}"].append(t.economic)
    shown.update(including_vendor_basis_refusals=broad,paired_iwm_including_vendor_basis_refusals=broad_pair)
    return dict(plan=60,ledger=LEDGER,queue=QUEUE,judged=p.marks(rows,c),decisions=rollup(decisions,c),
                shown={k:dict(n=len(vals),mean=p.avg(vals)) for k,vals in sorted(shown.items())},
                vendor_tail_absolute_scale="not established",
                sleeves=sleeves(q,decisions,staged,days,c))


def config(blob):
    base=p.config(blob)
    matches=re.findall(rb"(?m)^replay_60_plan:\n  value: (\{[^\n]+\})$",blob)
    need(len(matches)==1,"P60_CONFIG")
    extra=p.parse(matches[0])
    need(set(extra)=={"inherit","pre_padding_sessions","min_median_dollar_volume","exit_wait_sessions",
                      "vendor_tail_days","placement_cases","ohlc_tick","ohlc_slack"} and
         extra["inherit"]=="replay_43_plan" and extra["pre_padding_sessions"]==base["stale_run"]==5 and
         extra["exit_wait_sessions"]==base["stale_run"] and extra["min_median_dollar_volume"]==100000 and
         extra["vendor_tail_days"]==90,
         "P60_CONFIG")
    need(extra["placement_cases"]==[p.money(".75"),p.money(".65")] and
         p.money(extra["ohlc_tick"])==p.money(".01") and p.money(extra["ohlc_slack"])==p.money(".00000001"),
         "P60_CONFIG")
    return base|extra


def calibration(q,c):
    cases={}
    for share in c["placement_cases"]:
        scenario=c|{"calibration":c["calibration"]|{"placement":share}}
        cases[str(share)]=p.calibrate(q,scenario)
    return dict(plan=60,ledger=LEDGER,queue=QUEUE,
                memo="synthetic only, fixed placement assumptions, not estimates of the actual universe",
                placed_floor=c["marks"]["placed"],cases=cases)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--calibrate",action="store_true")
    modes.add_argument("--validate-inputs",action="store_true")
    modes.add_argument("--go",action="store_true")
    parser.add_argument("--approval-commit")
    args=parser.parse_args()
    if bool(args.approval_commit)!=(args.validate_inputs or args.go):
        parser.error("only real modes require --approval-commit")
    try:
        if args.calibrate:
            cfg=config((ROOT/p.CONFIG).read_bytes())
            days=p.calendar([(ROOT/n).read_bytes() for n in p.CALENDARS])
            docket=p.file_bytes(p.DOCKET,cfg["docket_sha256"],12*2**20,private=True)
            sys.stdout.buffer.write(p.render(calibration(p.events(docket,days,cfg),cfg)))
        else:
            approved(args.approval_commit,"go" if args.go else "validate")
    except p.Refused as exc:
        print(str(exc),file=sys.stderr)
        return 2
    except (Exception,KeyboardInterrupt):
        print("P60_REFUSED",file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
