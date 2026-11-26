"""Offline-only Plan 43 successor provenance verifier; no network imports."""
from bisect import bisect_left, bisect_right
from datetime import datetime, time
from hashlib import sha256
import json
import re


PAGE_KEYS=("seq","file","accession","view","page","status","params","fetched_utc","bytes","sha256")
INDEX_CAP=32*2**20
BODY_CAP=2**20
REVIEWER="/root/rig_code_auditor_a"


def utc_stamp(s):
    if type(s) is not str or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z",s):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00"))
    except ValueError:
        return None


def verify(api,root,job,c,events,days,ids,prepared,bars_blob):
    need,read,parse=api.need,api.file_bytes,api.parse
    native=root/"native"
    errors=native/"errors"
    api.private_dir(native)
    api.private_dir(errors)
    acq=job["acquisition_commit"]
    lockpin=job["fetch_start_sha256"]
    lock=parse(read(root/f"fetch_start.{acq}.lock",lockpin,16384,private=True))
    binding=dict(version=1,custodian=c["custodian"],acquisition_commit=acq,
                 acquisition_receipt_sha256=job["acquisition_receipt_sha256"])
    expected_lock=binding|dict(ledger=api.LEDGER,input_dir=str(root),
                               acquisition_receipt_path=str(root/f"acquisition.{acq}.lock"),
                               native_dir=str(native),out_bars=str(root/"bars.json"))
    need(type(lock) is dict and set(lock)==set(expected_lock)|{"started_utc"}
         and all(lock[k]==v for k,v in expected_lock.items()) and utc_stamp(lock["started_utc"]),"NATIVE_LOCK")
    expected=binding|dict(endpoint=api.ENDPOINT,feed="sip",timeframe="1Day",fetch_start_lock_sha256=lockpin)
    index=parse(read(native/"native_index.json",job["native_index_sha256"],INDEX_CAP,private=True))
    transport=parse(read(native/"transport_index.json",job["transport_index_sha256"],INDEX_CAP,private=True))
    need(set(transport)==set(expected)|{"status","attempts_count","attempts"}
         and all(transport[k]==v for k,v in expected.items()) and transport["status"]=="complete"
         and type(transport["attempts"]) is list
         and transport["attempts_count"]==len(transport["attempts"]),"NATIVE_TRANSPORT")
    need(set(index)==set(expected)|{"transport_index_sha256","files_count","files"}
         and all(index[k]==v for k,v in expected.items())
         and index["transport_index_sha256"]==job["transport_index_sha256"]
         and type(index["files"]) is list and index["files_count"]==len(index["files"]),"NATIVE_INDEX")
    attestation=parse(read(root/"offline_rebuild.json",job["offline_rebuild_sha256"],16384,private=True))
    need(attestation==dict(reviewer=REVIEWER,acquisition_commit=acq,
                           collector_sha256=api.COLLECTOR_SHA256,
                           native_index_sha256=job["native_index_sha256"],
                           transport_index_sha256=job["transport_index_sha256"],
                           rebuilt_bars_sha256=job["bars.json"]),"NATIVE_ATTESTATION")

    attempts=iter(transport["attempts"])
    files=iter(index["files"])
    expected_files={"errors","native_index.json","transport_index.json"}
    expected_errors=set()
    records={}
    seq=0
    previous_utc=utc_stamp(lock["started_utc"])
    for e in events:
        if prepared.decisions[e.a].get("noncash"):
            continue
        legs=ids["records"][e.a]
        syms=[legs[x]["ticker"] for x in ("stock","IWM","SPY")]
        need(len(set(syms))==3,"NATIVE_SYMBOLS")
        window=days[bisect_left(days,e.start):bisect_right(days,e.end)]
        allowed=set(window)
        collected={}
        for view in api.VIEWS:
            merged={sym:{} for sym in syms}
            token=None
            seen_tokens=set()
            page=0
            while True:
                params=dict(symbols=",".join(syms),timeframe="1Day",start=e.start.isoformat(),
                            end=e.end.isoformat(),feed="sip",adjustment="raw" if view=="raw" else "all",
                            asof=(e.at.date() if view=="filing_all" else e.entry).isoformat(),limit="1000")
                if token:
                    params["page_token"]=token
                payload=None
                for attempt in range(1,9):
                    row=next(attempts,None)
                    seq+=1
                    need(type(row) is dict and set(row)==set(PAGE_KEYS)|{"attempt","curl_rc","outcome"}
                         and (row["seq"],row["accession"],row["view"],row["page"],row["attempt"],row["params"])
                         ==(seq,e.a,view,page,attempt,params)
                         and type(row["status"]) is int and 0<=row["status"]<=599
                         and type(row["curl_rc"]) is int and row["curl_rc"]>=0,"NATIVE_REQUEST")
                    fetched=utc_stamp(row["fetched_utc"])
                    need(fetched is not None and fetched>=previous_utc,"NATIVE_REQUEST")
                    previous_utc=fetched
                    ok=row["status"]==200 and row["curl_rc"]==0
                    if ok:
                        fname=f"{e.a}__{view}__p{page}.json"
                        path=native/fname
                        expected_files.add(fname)
                        need(row["outcome"]=="ok" and row["file"]==fname
                             and next(files,None)=={k:row[k] for k in PAGE_KEYS},"NATIVE_INDEX")
                    else:
                        fname=f"{seq:06d}__{e.a}__{view}__p{page}__att{attempt}__http{row['status']}.raw"
                        path=errors/fname
                        expected_errors.add(fname)
                        need(row["outcome"]=="retry" and row["file"]=="errors/"+fname
                             and (row["curl_rc"]!=0 or row["status"] in (429,500,502,503,504)),"NATIVE_TRANSPORT")
                    body=read(path,row["sha256"],BODY_CAP,private=True)
                    need(type(row["bytes"]) is int and row["bytes"]==len(body),"NATIVE_LENGTH")
                    if ok:
                        payload=parse(body)
                        break
                need(type(payload) is dict and {"bars","next_page_token"}<=payload.keys(),"NATIVE_PAGE")
                mapping=payload["bars"]
                need(type(mapping) is dict and mapping.keys()<=merged.keys(),"NATIVE_SYMBOLS")
                for sym,rows in mapping.items():
                    need(type(rows) is list,"NATIVE_PAGE")
                    for r in rows:
                        normalized,day=normalize(api,r,allowed)
                        need(day not in merged[sym],"NATIVE_DUPLICATE")
                        merged[sym][day]=normalized
                token=payload["next_page_token"]
                if token is None:
                    break
                need(type(token) is str and 0<len(token)<=8192 and token.isprintable()
                     and token==token.strip() and token not in seen_tokens,"NATIVE_PAGINATION")
                seen_tokens.add(token)
                page+=1
            collected[view]=merged
        records[e.a]={leg:dict(ticker=ident["ticker"],identity=ident["identity"],entry_asof=e.entry.isoformat(),
                               filing_asof=e.at.date().isoformat(),start=e.start.isoformat(),end=e.end.isoformat(),
                               **{v:[collected[v][ident["ticker"]][day]
                                     for day in sorted(collected[v][ident["ticker"]])] for v in api.VIEWS})
                      for leg,ident in legs.items()}
    need(next(attempts,None) is None and next(files,None) is None
         and {p.name for p in native.iterdir()}==expected_files
         and {p.name for p in errors.iterdir()}==expected_errors,"NATIVE_INVENTORY")
    payload=dict(version=1,custodian=c["custodian"],endpoint=api.ENDPOINT,feed="sip",timeframe="1Day",
                 adjustments=["raw","all"],records=records)
    rebuilt=(json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
    need(rebuilt==bars_blob and sha256(rebuilt).hexdigest()==attestation["rebuilt_bars_sha256"],"NATIVE_REBUILD")


def normalize(api,r,allowed):
    api.need(type(r) is dict and set("tohlcv")<=r.keys(),"NATIVE_ROW")
    stamp=datetime.fromisoformat(r["t"].replace("Z","+00:00"))
    api.need(stamp.tzinfo is not None,"NATIVE_ROW")
    when=stamp.astimezone(api.ET)
    api.need(when.time()==time(0,0) and when.date() in allowed,"NATIVE_DATE")
    vol=api.money(r["v"])
    api.need(vol==int(vol) and vol>=0,"NATIVE_ROW")
    for k in "ohlc":
        api.money(r[k])
    return dict(t=r["t"],o=str(r["o"]),h=str(r["h"]),l=str(r["l"]),c=str(r["c"]),v=int(vol)),when.date()
