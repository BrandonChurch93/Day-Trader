"""Offline Plan 60 native corporate-action page verifier and exact window projector."""
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import gzip
import re


TYPES={
    "capital_gains_distributions","cash_dividends","cash_mergers","forward_splits","name_changes",
    "partial_calls","redemptions","reorganizations","reverse_splits","rights_distributions","spin_offs",
    "stock_and_cash_mergers","stock_dividends","stock_mergers","unit_splits","worthless_removals",
}
MAX_BODY=8*2**20


def decimal(api,raw):
    api.need(type(raw) in (int,Decimal),"P60_VENDOR_WIRE")
    value=format(api.money(raw),"f")
    return value.rstrip("0").rstrip(".") if "." in value else value


def unpack(api,kind,a,symbol,start,end,digest):
    need=api.need
    need(type(a) is dict and type(a.get("id")) is str and 0<len(a["id"])<=120,"P60_VENDOR_WIRE")
    process=api.d(a["process_date"])
    need(start<=process<=end,"P60_VENDOR_REQUEST_SCOPE")
    if kind=="name_changes":
        primary=("old_symbol","old_cusip")
    elif kind=="unit_splits":
        primary=("old_symbol","old_cusip")
    elif kind in {"cash_mergers","stock_mergers","stock_and_cash_mergers"}:
        primary=("acquiree_symbol","acquiree_cusip")
    elif kind in {"rights_distributions","spin_offs"}:
        primary=("source_symbol","source_cusip")
    else:
        primary=("symbol","old_cusip" if kind=="reverse_splits" else "cusip")
    original=a[primary[0]]
    need(valid_symbol(original),"P60_VENDOR_WIRE")
    target=a.get("new_symbol") if kind in {"name_changes","reverse_splits"} else None
    need(target in (None,"") or valid_symbol(target),"P60_VENDOR_WIRE")
    related={original}
    if target:
        related.add(target)
    # These records can also be returned on a counterparty or distributed leg query.
    for key in ("acquirer_symbol","new_symbol","alternate_symbol"):
        value=a.get(key)
        if value:
            need(valid_symbol(value),"P60_VENDOR_WIRE")
            related.add(value)
    need(symbol in related,"P60_VENDOR_REQUEST_SCOPE")
    actual=a.get("ex_date") or a.get("effective_date")
    ex=api.d(actual) if actual else process
    uncertain=actual is None and kind!="name_changes"
    row=dict(id=a["id"],ex=str(ex),source_sha256=digest)
    if kind=="cash_dividends" and a.get("currency") in ("USD",None,"") and (
            a.get("currency")=="USD" or a.get("foreign") is False):
        rate=decimal(api,a["rate"])
        if api.money(rate)>0:
            row.update(type="cash",cash_usd=rate,factor=None)
    elif kind in {"forward_splits","reverse_splits"}:
        new,old=(decimal(api,a[x]) for x in ("new_rate","old_rate"))
        if api.money(new)>0 and api.money(old)>0:
            row.update(type="split",new=new,old=old)
    elif kind=="name_changes":
        row.update(type="nonprice",vendor_type=kind)
    if "type" not in row:
        row.update(type="unsupported",vendor_type=kind)
    cusips={v for v in (a.get(primary[1]),a.get("new_cusip") if
                         kind in {"name_changes","reverse_splits"} else None) if v}
    need(all(type(v) is str and len(v)<=20 for v in cusips),"P60_VENDOR_WIRE")
    return original,target or None,tuple(sorted(related)),tuple(sorted(cusips)),uncertain,row


def valid_symbol(s):
    return type(s) is str and re.fullmatch(r"[A-Z0-9][A-Z0-9./-]{0,19}",s) is not None


def streams(api,index,endpoint,known):
    """Verify the direct v2 custodian HTTP index, including outgoing retry metadata."""
    need=api.need
    need(type(index) is dict and set(index)=={"version","ledger","endpoint","capture_utc","total_pages",
        "total_retries_and_errors","total_http_requests","entries","retries_and_errors"} and
        index["version"]=="plan60_vendor_action_index_v2" and index["ledger"]==199 and index["endpoint"]==endpoint,
        "P60_VENDOR_NATIVE")
    need(type(index["entries"]) is list and bool(index["entries"]) and type(index["retries_and_errors"]) is list and
         type(index["total_pages"]) is type(index["total_retries_and_errors"]) is type(index["total_http_requests"]) is int and
         len(index["entries"])==index["total_pages"] and len(index["retries_and_errors"])==index["total_retries_and_errors"]
         and index["total_http_requests"]==index["total_pages"]+index["total_retries_and_errors"],"P60_VENDOR_NATIVE")

    def timestamp(s):
        t=datetime.fromisoformat(s)
        need(t.utcoffset()==timedelta(0),"P60_VENDOR_TIMESTAMP")
        return t

    capture=timestamp(index["capture_utc"])
    grouped={}
    common={"identity","ticker","page","attempt","params","page_token","status","body_bytes","body_sha256","fetched_utc"}
    success={"file","sha256","bytes","next_page_token"}
    for good,rows in ((True,index["entries"]),(False,index["retries_and_errors"])):
        for row in rows:
            need(type(row) is dict and set(row)==common|(success if good else {"curl_rc"}),"P60_VENDOR_TRANSPORT")
            identity,symbol,page,attempt,params,token=(row[k] for k in
                ("identity","ticker","page","attempt","params","page_token"))
            need(identity in known and valid_symbol(symbol) and type(page) is int and page>=0 and
                 type(attempt) is int and attempt>=1 and type(params) is dict and params.get("symbols")==symbol and
                 (("page_token" not in params and token is None) or
                  (type(token) is str and bool(token) and params.get("page_token")==token)) and
                 timestamp(row["fetched_utc"])>=capture and type(row["status"]) is int and
                 type(row["body_bytes"]) is int and row["body_bytes"]>=0 and api.is_pin(row["body_sha256"]),
                 "P60_VENDOR_TRANSPORT")
            if good:
                need(row["status"]==200,"P60_VENDOR_PAGE")
            else:
                need(type(row["curl_rc"]) is int and (row["curl_rc"]!=0 or row["status"]!=200),
                     "P60_VENDOR_TRANSPORT")
            base={k:v for k,v in params.items() if k!="page_token"}
            key=(identity,symbol,base.get("start"),base.get("end"))
            previous,numbered=grouped.setdefault(key,(base,{}))
            need(base==previous,"P60_VENDOR_REQUEST")
            history=numbered.setdefault(page,{})
            need(attempt not in history,"P60_VENDOR_TRANSPORT")
            history[attempt]=(good,row)
    for (identity,symbol,_,_),(params,numbered) in grouped.items():
        need(sorted(numbered)==list(range(len(numbered))),"P60_VENDOR_PAGINATION")
        pages=[]
        interrupted=None
        for num,history in sorted(numbered.items()):
            need(sorted(history)==list(range(1,len(history)+1)),"P60_VENDOR_TRANSPORT")
            attempts=[row for _,row in sorted(history.items())]
            good=[i for i,(ok,_) in enumerate(attempts) if ok]
            need(all(row["page_token"]==attempts[0][1]["page_token"] for _,row in attempts) and
                 (good==[len(attempts)-1] or (not good and num==len(numbered)-1)),"P60_VENDOR_TRANSPORT")
            if good:
                pages.append(attempts[-1][1])
            else:
                interrupted=attempts[-1][1]
        yield identity,params,pages,interrupted


def verify(api,root,index,c,q,keyed,endpoint,noncash):
    """Check indexed requests and pages, then independently reproduce every leg."""
    need=api.need
    api.private_dir(root)
    known={x["identity"] for _,legs in keyed.values() for x in legs.values()}
    names=set()
    scopes=defaultdict(list)
    facts=defaultdict(dict)
    by_id={}
    links=defaultdict(set)
    cusips=defaultdict(set)
    cusip_links=defaultdict(set)
    for identity,params,pages,interrupted in streams(api,index,endpoint,known):
        need(type(params) is dict and set(params)-{"region"}=={"symbols","start","end","limit","sort","data_quality"}
             and params["limit"]=="1000" and params["sort"]=="asc" and params["data_quality"]=="complete"
             and params.get("region","us")=="us" and valid_symbol(params["symbols"]),
             "P60_VENDOR_REQUEST")
        symbol=params["symbols"]
        start,end=(api.d(params[k]) for k in ("start","end"))
        need(start<=end,"P60_VENDOR_REQUEST_SCOPE")
        expected=None
        seen=set()
        for i,page in enumerate(pages):
            need(page["page_token"]==expected,"P60_VENDOR_PAGE")
            name=page["file"]
            need(type(name) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,150}",name)
                 and name not in names,"P60_VENDOR_NATIVE")
            names.add(name)
            blob=api.file_bytes(root/name,page["sha256"],MAX_BODY,private=True)
            need(type(page["bytes"]) is int and page["bytes"]==len(blob),"P60_VENDOR_NATIVE")
            if name.endswith(".gz"):
                with gzip.GzipFile(fileobj=BytesIO(blob)) as gz:
                    blob=gz.read(MAX_BODY+1)
                need(len(blob)<=MAX_BODY,"P60_VENDOR_NATIVE")
            digest=sha256(blob).hexdigest()
            need(page["body_sha256"]==digest and type(page["body_bytes"]) is int and page["body_bytes"]==len(blob),
                 "P60_VENDOR_BODY")
            payload=api.parse(blob)
            need(type(payload) is dict and set(payload)=={"corporate_actions","next_page_token"} and
                 type(payload["corporate_actions"]) is dict and set(payload["corporate_actions"])<=TYPES,
                 "P60_VENDOR_WIRE")
            expected=payload["next_page_token"]
            need(expected==page["next_page_token"],"P60_VENDOR_PAGINATION")
            terminal=i==len(pages)-1 and interrupted is None
            need((terminal and expected is None) or
                 (not terminal and type(expected) is str and 0<len(expected)<=8192 and
                  expected.isprintable() and expected==expected.strip() and expected not in seen),
                 "P60_VENDOR_PAGINATION")
            seen.add(expected)
            for kind,rows in payload["corporate_actions"].items():
                need(type(rows) is list,"P60_VENDOR_WIRE")
                for a in rows:
                    original,target,related,keys,uncertain,row=unpack(api,kind,a,symbol,start,end,digest)
                    item=row["id"]
                    fingerprint=(kind,original,target,related,keys,uncertain,
                                 {k:v for k,v in row.items() if k!="source_sha256"})
                    need(item not in by_id or by_id[item]==fingerprint,"P60_VENDOR_CONFLICT")
                    by_id[item]=fingerprint
                    if target and target!=original:
                        links[original].add(target)
                        links[target].add(original)
                    cusips[original].update(keys)
                    if len(keys)==2 and kind in {"name_changes","reverse_splits"}:
                        a,b=keys
                        cusip_links[a].add(b)
                        cusip_links[b].add(a)
                    for participant in related if row["type"]=="unsupported" else (original,):
                        if item in facts[participant]:
                            old,old_uncertain=facts[participant][item]
                            need((old|{"source_sha256":digest},old_uncertain)==(row,uncertain),
                                 "P60_VENDOR_CONFLICT")
                            if old["source_sha256"]<digest:
                                continue
                        facts[participant][item]=(row,uncertain)
        if interrupted is not None:
            need(interrupted["page_token"]==expected,"P60_VENDOR_PAGE")
        else:
            need(bool(pages) and expected is None,"P60_VENDOR_PAGINATION")
            scopes[(identity,symbol)].append((start,end))
    need({f.name for f in root.iterdir()}==names,"P60_VENDOR_NATIVE")

    tickers=defaultdict(set)
    adopted_aliases=defaultdict(set)
    for e in q:
        if e.a!=noncash:
            for leg in keyed[e.a][1].values():
                tickers[leg["ticker"]].add(leg["identity"])
                adopted_aliases[leg["identity"]].add(leg["ticker"])

    def covered(identity,symbol,first,last):
        for start,end in sorted(scopes[identity,symbol]):
            if start>first:
                return False
            if end>=last:
                return True
            first=max(first,end+timedelta(days=1))
        return False

    expected={}
    for e in q:
        if e.a==noncash:
            continue
        expected[e.a]={}
        for leg,x in keyed[e.a][1].items():
            ticker,identity=x["ticker"],x["identity"]
            aliases=set(adopted_aliases[identity])
            pending=list(aliases)
            while pending:
                for a in links[pending.pop()]-aliases:
                    aliases.add(a)
                    pending.append(a)
            through=e.end+timedelta(days=c["vendor_tail_days"])
            first=e.start-timedelta(days=c["vendor_process_lookback_days"])
            last=through
            distinct=set().union(*(cusips[a] for a in aliases))
            if distinct:
                pending=[min(distinct)]
                linked=set(pending)
                while pending:
                    for key in cusip_links[pending.pop()]-linked:
                        linked.add(key)
                        pending.append(key)
            else:
                linked=set()
            unique=all(tickers[a]<={identity} for a in aliases) and distinct<=linked
            complete=unique and all(covered(identity,a,first,last) for a in aliases)
            items={}
            for a in aliases:
                for item,(row,uncertain) in facts[a].items():
                    ex=api.d(row["ex"])
                    if uncertain and first<=ex<=through:
                        complete=False
                    if e.start<=ex<=through and (item not in items or row["source_sha256"]<items[item]["source_sha256"]):
                        items[item]=row
            expected[e.a][leg]=dict(identity=identity,ticker=ticker,start=str(e.start),through=str(through),
                                    views=dict(all=identity if unique else "unresolved",
                                               filing_all=identity if unique else "unresolved"),
                                    complete=complete,items=sorted(items.values(),key=lambda row:(row["ex"],row["id"])))
    return expected


def project_packet(api,root,index_blob,adoption,c,q,keyed,endpoint,noncash):
    """Produce the exact normalized packet for an offline custodian or verifier."""
    records=verify(api,root,api.parse(index_blob),c,q,keyed,endpoint,noncash)
    return dict(version=2,custodian=c["custodian"],endpoint=endpoint,adoption=adoption,
                native_index_sha256=sha256(index_blob).hexdigest(),records=records)
