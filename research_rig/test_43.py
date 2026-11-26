"""Executable synthetic controls for Plan 43. No vendor inputs are opened."""
import copy
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import runpy
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import score_43 as s

AUTH = ["https://issuer.example/filing","https://exchange.example/notice"]


def cfg():
    return s.config((s.ROOT/s.CONFIG).read_bytes())


def condition(trade_days=None):
    if trade_days is None:
        days=[date(2024,5,1)+timedelta(days=i) for i in range(120)
              if (date(2024,5,1)+timedelta(days=i)).weekday()<5]
        trade_days=s.Sessions(days,{day:datetime.combine(day,time(16),s.ET) for day in days})
    c=cfg()
    at=datetime.fromisoformat("2024-06-07T08:55:00-04:00")
    e=SimpleNamespace(a="0000000001-24-000001",cik="0000000001",cl="Class A",at=at,declared=Decimal(1),
                      year=at.year,first="UNKNOWN",board=None,record=None,pay=None,**vars(s.window(at,trade_days,c)))
    C=s.engine((s.ROOT/s.ENGINE).read_bytes())
    base=dict(version=1,custodian=c["custodian"])
    ids=dict(**base,records={e.a:{}})
    bars=dict(**base,records={e.a:{}},endpoint=s.ENDPOINT,feed="sip",timeframe="1Day",adjustments=["raw","all"])
    acts=dict(version=1,reviewer=c["action_checker"],records={e.a:{}})
    for i,leg in enumerate(("stock","IWM","SPY")):
        ident=dict(identity="SECL-"+str(i),ticker="TEST" if not i else leg,cik=e.cik if not i else f"{i+1:010d}",
                   share_class=e.cl if not i else "units",class_key="class-a" if not i else "etf",source=AUTH[0])
        ids["records"][e.a][leg]=ident
        z=[dict(t=day.isoformat()+"T00:00:00-04:00",o=(i+1)*8+v,h=(i+1)*8+v+1,l=(i+1)*8+v-1,
                c=(i+1)*8+v,v=30000+i) for v,day in enumerate(x for x in trade_days if e.start<=x<=e.end)]
        tape=copy.deepcopy(z)
        if not i:
            ix=next(j for j,b in enumerate(z) if b["t"].startswith(e.exit.isoformat()))
            prev=Decimal(z[ix-1]["c"])
            for b in tape[:ix]:
                for k in "ohlc":
                    b[k]=Decimal(b[k])*(prev-1)/prev
        bars["records"][e.a][leg]=dict(ticker=ident["ticker"],identity=ident["identity"],entry_asof=e.entry.isoformat(),
                                       filing_asof=e.at.date().isoformat(),start=e.start.isoformat(),end=e.end.isoformat(),
                                       raw=copy.deepcopy(z),all=copy.deepcopy(tape),filing_all=copy.deepcopy(tape))
        actions=[]
        disclosure=None
        if leg=="stock":
            actions=[dict(id="special",ex=e.exit.isoformat(),kind="special",value="1",
                          payment=e.entry.isoformat(),available=(e.exit+timedelta(days=2)).isoformat(),sources=AUTH)]
            disclosure=dict(accession=e.a,filing=f"https://www.sec.gov/Archives/edgar/data/1/{e.a}.txt",
                            declared=e.at.date().isoformat(),announced=e.at.date().isoformat(),record=e.early.isoformat())
        acts["records"][e.a][leg]=dict(identity=ident["identity"],start=e.start.isoformat(),end=e.end.isoformat(),
                                      coverage_sources=AUTH,status="complete",target="special" if not i else None,
                                      target_disclosure=disclosure,cancellation_sources=[],items=actions)
    return [e],trade_days,C,c,ids,bars,acts


def add_blocked(event_rows, ids, bars, acts, accession=s.NONCASH_ACCESSION):
    event=event_rows[0]
    blocked=SimpleNamespace(**(vars(event)|dict(a=accession,cik="0000000002")))
    event_rows.append(blocked)
    for packet in (ids,acts):
        packet["records"][blocked.a]=copy.deepcopy(packet["records"][event.a])
        packet["records"][blocked.a]["stock"]["identity"]="SECL-BLOCKED"
    ids["records"][blocked.a]["stock"].update(cik=blocked.cik,ticker="BLOCKED")
    stock=acts["records"][blocked.a]["stock"]
    stock.update(status="blocked",reason_code=s.NONCASH_SKIP,reason_sources=AUTH)
    bars["records"][blocked.a]="Any attempt to evaluate this excluded event's tape must fail"
    return blocked.a


def expand_synthetic_scope(event_rows, ids, bars, acts, n):
    """Independent stock identities, identical matched control tape across windows."""
    root=event_rows[0]
    for i in range(1,n):
        cik=f"{i+100:010d}"
        e=SimpleNamespace(**(vars(root)|dict(a=f"{cik}-24-000001",cik=cik)))
        event_rows.append(e)
        symbol,ident=f"X{i:04d}",f"SECL-{i+100}"
        for packet in (ids,bars,acts):
            stock=copy.deepcopy(packet["records"][root.a]["stock"])
            packet["records"][e.a]=(packet["records"][root.a]|{"stock":stock})
            stock["identity"]=ident
        ids["records"][e.a]["stock"].update(cik=cik,ticker=symbol)
        b=bars["records"][e.a]["stock"]
        b["ticker"]=symbol
        for view in s.VIEWS:
            for row in b[view]:
                row["v"]+=i+100
        acts["records"][e.a]["stock"]["target_disclosure"].update(accession=e.a,
            filing=f"https://www.sec.gov/Archives/edgar/data/{i+100}/{e.a}.txt")


class SyntheticRepo:
    """Real Git objects and CLI in a temporary tree; only absolute paths are redirected."""

    BOOT = """
import runpy, sys
from hashlib import sha256
from pathlib import Path
root, data = map(Path, sys.argv[1:3])
g = runpy.run_path(str(root / "research_rig/score_43.py"))["main"].__globals__
collector = data/"collector.py"
g.update(ROOT=root, DATA=data, INPUT=data/"plan43_successor_inputs", RUN=data/"replay_43_successor",
         RUN3=data/"replay_43_attempt3",
         DOCKET=data/"docket.jsonl",COLLECTOR=collector,COLLECTOR_SHA256=sha256(collector.read_bytes()).hexdigest())
sys.argv = ["score_43.py", *sys.argv[3:]]
raise SystemExit(g["main"]())
"""

    def __init__(self, base, with_blocked=False, modeled_count=1):
        self.root=base/"repo"
        self.data=base/"data"
        self.root.mkdir()
        self.data.mkdir(mode=0o700)
        self.inp=self.data/"plan43_successor_inputs"
        self.run=self.data/"replay_43_successor"
        self.inp.mkdir(mode=0o700)
        self.run.mkdir(mode=0o700)
        collector=b"# synthetic fixture; no collector is executed\n"
        s.write_exclusive(self.data/"collector.py",collector)
        self.collector=sha256(collector).hexdigest()
        self.git("init","-q","-b","main")
        self.git("config","user.name","Synthetic Fixture")
        self.git("config","user.email","fixture@example.invalid")
        self.git("config","commit.gpgsign","false")
        ds=s.calendar([(s.ROOT/n).read_bytes() for n in s.CALENDARS])
        events,_,_,c,*self.packets=condition(ds)
        expand_synthetic_scope(events,*self.packets,modeled_count)
        self.blocked=add_blocked(events,*self.packets) if with_blocked else None
        docket=b"".join((json.dumps(dict(accession=event.a,cik=event.cik,share_class=event.cl,
                                disposition="eligible", acceptance=event.at.isoformat(), venue="NYSE",
                                words_used="synthetic",first_time="UNKNOWN",per_share_usd="1",
                                url=f"https://{s.SEC}/Archives/fixture"))+"\n").encode() for event in events)
        self.dp=sha256(docket).hexdigest()
        s.write_exclusive(self.data/"docket.jsonl",docket)
        c.update(docket_sha256=self.dp,frame_rows=len(events),eligible=len(events))
        c["marks"]["placed"]=1
        # Keep OS guards and their real implementation in the test with small fixture floors.
        c["resources"].update(minimum_free_mib=1,disk_floor_mib=1)
        s.write_exclusive(self.inp/"identities.json",s.render(self.packets[0]))
        s.write_exclusive(self.inp/"actions.json",s.render(self.packets[2]))
        config=b"replay_43_plan:\n  value: "+json.dumps(c,default=float).encode()+b"\n"
        proof=s.render(dict(docket_sha256=self.dp,trials=c["calibration"]["trials"],eligible=len(events),
                            edges=c["calibration"]["edges"],shares=[0]))
        custom={s.CONFIG:config,s.CALIBRATION:proof}
        for name in s.SOURCES:
            blob=custom[name] if name in custom else (s.ROOT/name).read_bytes()
            if name in (s.PLAN,s.AMENDMENT):
                blob=blob.replace(b"Status DRAFT.",b"Status FROZEN.")
            self.put(name,blob)
        for name,num,doc in (("research_rig/TRIAL_LEDGER.md",s.LEDGER,s.AMENDMENT),("docs/QUEUE.md",74,s.PLAN)):
            self.put(name,f"| {num} | `{doc}` | synthetic selection |\n".encode())
        self.repin()
        self.freeze=self.commit()

    def git(self,*args):
        env={"PATH":"/usr/bin:/bin","LC_ALL":"C","GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"/dev/null"}
        return subprocess.run(["/usr/bin/git","-C",str(self.root),*args],env=env,capture_output=True,check=True,
                              text=True,timeout=30).stdout.strip()

    def put(self,name,content):
        where=self.root/name
        where.parent.mkdir(parents=True,exist_ok=True)
        where.write_bytes(content)

    def repin(self,third=False):
        names=s.SOURCES|({s.BASIS,s.BASIS_AMENDMENT} if third else set())
        pins={k:sha256((self.root/k).read_bytes()).hexdigest() for k in names}
        blob=s.render(pins)
        self.put(s.PINS,blob)
        self.fp=sha256(blob).hexdigest()

    def basis_attempt(self,previous):
        self.run3=self.data/"replay_43_attempt3"
        self.run3.mkdir(mode=0o700)
        prev_pin=sha256((self.root/s.APPROVAL).read_bytes()).hexdigest()
        for n in (s.BASIS,s.BASIS_AMENDMENT):
            self.put(n,(s.ROOT/n).read_bytes().replace(b"Status DRAFT.",b"Status FROZEN."))
        scorer="research_rig/score_43.py"
        self.put(scorer,(self.root/scorer).read_bytes().replace(s.PREVIOUS_VALIDATION.encode(),previous.encode()))
        log="research_rig/TRIAL_LEDGER.md"
        self.put(log,(self.root/log).read_bytes()+f"| {s.ATTEMPT3} | `{s.BASIS_AMENDMENT}` | synthetic |\n".encode())
        self.repin(third=True)
        freeze3=self.commit()
        adopt=(f"Approved by the lead: plan 43 attempt 3 ledger 195, adopt sealed packet from refused validation commit "
               f"{previous}, prior approval SHA-256 {prev_pin}, freeze commit {freeze3}, freeze SHA-256 {self.fp}, "
               f"no new vendor calls.\n").encode()
        adoption=self.commit(s.ADOPTION,adopt)
        approval=(f"Approved by the lead: plan 43 attempt 3 ledger 195, validation only, adoption commit {adoption}, "
                  f"adoption approval SHA-256 {sha256(adopt).hexdigest()}.\n").encode()
        return adoption,self.commit(s.VALIDATION3,approval)

    def commit(self,name=None,content=None):
        if name is not None:
            self.put(name,content)
        self.git("add","-A")
        self.git("commit","-qm","Synthetic fixture")
        return self.git("rev-parse","HEAD")

    def checkout(self,ref):
        self.git("checkout","-q","--detach",ref)

    def acquisition(self,freeze=None):
        freeze=freeze or self.freeze
        return (f"Approved by the lead: plan 43 successor ledger 188, one custodian acquisition, freeze commit {freeze}, "
                f"freeze SHA-256 {self.fp}, docket SHA-256 {self.dp}, collector SHA-256 {self.collector}.\n").encode()

    def validation(self,acq,bars_pin=None):
        receipt=self.inp/f"acquisition.{acq}.lock"
        ap=sha256(receipt.read_bytes()).hexdigest()
        ids,bars,actions=(sha256((self.inp/n).read_bytes()).hexdigest() for n in s.PACKETS)
        fetch,native,transport,rebuild=[sha256((self.inp/n).read_bytes()).hexdigest() for n in
                                       (f"fetch_start.{acq}.lock","native/native_index.json",
                                        "native/transport_index.json","offline_rebuild.json")]
        return (f"Approved by the lead: plan 43 successor ledger 188, validation only, acquisition commit {acq}, "
                f"acquisition receipt SHA-256 {ap}, identities SHA-256 {ids}, bars SHA-256 {bars_pin or bars}, "
                f"actions SHA-256 {actions}, fetch-start SHA-256 {fetch}, native index SHA-256 {native}, "
                f"transport index SHA-256 {transport}, offline rebuild SHA-256 {rebuild}.\n").encode()

    def release(self,val,pin):
        return (f"Approved by the lead: plan 43 successor ledger 188, one scored run, validation approval commit {val}, "
                f"validation receipt SHA-256 {pin}.\n").encode()

    def process(self,flag,ref=None,*,isolated=True):
        flags=("-I","-B") if isolated else ("-B",)
        args=[] if ref is None else ["--approval-commit",ref]
        return subprocess.run([sys.executable,*flags,"-c",self.BOOT,str(self.root),str(self.data),
                               "--"+flag,*args],capture_output=True,text=True,timeout=300)

    def cli(self,test,flag,ref,expected,*,isolated=True):
        proc=self.process(flag,ref,isolated=isolated)
        ok=expected in ("P43_ACQUISITION_CLAIMED","P43_CUSTODY_READY","P43_VALIDATED","P43_SCORED_ONCE")
        test.assertEqual(proc.returncode,0 if ok else 2,proc.stderr)
        test.assertEqual((proc.stdout,proc.stderr),((expected+"\n","") if ok else ("",expected+"\n")))

    def stage_packets(self,acq,core_missing=0):
        _,bars,_=self.packets
        bars=copy.deepcopy(bars)
        bars["records"].pop(self.blocked,None)
        first=next(iter(bars["records"].values()))
        # Keep one diagnostic gap and one earlier-entry omission; no core refusal
        # fits the 5% cap in this two-accession fixture.
        first["stock"]["filing_all"].pop(0)
        early_index=cfg()["stale_run"]
        first["stock"]["filing_all"][early_index-1]["v"]=0
        for legs in list(bars["records"].values())[:core_missing]:
            legs["stock"]["raw"].pop(early_index+1)
        for legs in bars["records"].values():
            for leg in legs.values():
                for view in s.VIEWS:
                    for r in leg[view]:
                        for k in "ohlc":
                            r[k]=str(r[k])
        body=lambda p:(json.dumps(p,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
        s.write_exclusive(self.inp/"bars.json",body(bars))
        native=self.inp/"native"
        native.mkdir(mode=0o700,exist_ok=True)
        (native/"errors").mkdir(mode=0o700,exist_ok=True)
        receipt=self.inp/f"acquisition.{acq}.lock"
        fetch=dict(version=1,custodian=cfg()["custodian"],acquisition_commit=acq,
                   acquisition_receipt_sha256=sha256(receipt.read_bytes()).hexdigest())
        lock_path=self.inp/f"fetch_start.{acq}.lock"
        if lock_path.exists():
            lock=lock_path.read_bytes()
            timestamp=s.parse(lock)["started_utc"]
        else:
            timestamp="2026-11-26T00:00:00Z"
            lock=s.render(fetch|dict(ledger=s.LEDGER,input_dir=str(self.inp),acquisition_receipt_path=str(receipt),
                                     native_dir=str(native),out_bars=str(self.inp/"bars.json"),started_utc=timestamp))
            s.write_exclusive(lock_path,lock)
        header=fetch|dict(endpoint=s.ENDPOINT,feed="sip",timeframe="1Day",fetch_start_lock_sha256=sha256(lock).hexdigest())
        good,all_attempts=[],[]
        for a,legs in bars["records"].items():
            x=legs["stock"]
            syms=[legs[k]["ticker"] for k in ("stock","IWM","SPY")]
            for view in s.VIEWS:
                params=dict(symbols=",".join(syms),timeframe="1Day",start=x["start"],end=x["end"],feed="sip",
                            adjustment="raw" if view=="raw" else "all",
                            asof=x["filing_asof"] if view=="filing_all" else x["entry_asof"],limit="1000")
                rows={leg["ticker"]:leg[view] for leg in legs.values()}
                npages=2 if view=="raw" else 1
                for j in range(npages):
                    page_params=params|({"page_token":"fixture-token"} if j else {})
                    if view=="raw" and j==0:
                        seq=len(all_attempts)+1
                        name=f"errors/{seq:06d}__{a}__{view}__p{j}__att1__http429.raw"
                        blob=b"synthetic throttle"
                        s.write_exclusive(native/name,blob)
                        all_attempts.append(dict(seq=seq,file=name,accession=a,view=view,page=j,status=429,
                                                 params=page_params,fetched_utc=timestamp,bytes=len(blob),
                                                 sha256=sha256(blob).hexdigest(),attempt=1,curl_rc=0,outcome="retry"))
                    seq=len(all_attempts)+1
                    name=f"{a}__{view}__p{j}.json"
                    if npages==2:
                        rowdata={k:v[:10] if j==0 else v[10:] for k,v in rows.items()}
                    else:
                        rowdata=rows
                    blob=body(dict(bars=rowdata,next_page_token="fixture-token" if npages==2 and j==0 else None))
                    s.write_exclusive(native/name,blob)
                    proto=dict(seq=seq,file=name,accession=a,view=view,page=j,status=200,params=page_params,
                               fetched_utc=timestamp,bytes=len(blob),sha256=sha256(blob).hexdigest())
                    good.append(proto)
                    all_attempts.append(proto|dict(attempt=2 if view=="raw" and j==0 else 1,curl_rc=0,outcome="ok"))
        tb=s.render(header|dict(status="complete",attempts_count=len(all_attempts),attempts=all_attempts))
        s.write_exclusive(native/"transport_index.json",tb)
        nb=s.render(header|dict(transport_index_sha256=sha256(tb).hexdigest(),files_count=len(good),files=good))
        s.write_exclusive(native/"native_index.json",nb)
        att=dict(reviewer="/root/rig_code_auditor_a",acquisition_commit=acq,collector_sha256=self.collector,
                 native_index_sha256=sha256(nb).hexdigest(),transport_index_sha256=sha256(tb).hexdigest(),
                 rebuilt_bars_sha256=sha256(body(bars)).hexdigest())
        s.write_exclusive(self.inp/"offline_rebuild.json",s.render(att))


class Plan43(unittest.TestCase):
    def test_real_cli_transport_history_and_three_release_stages(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d),with_blocked=True)
            first=f.commit(s.ACQUISITION,f.acquisition())
            (f.root/s.ACQUISITION).unlink()
            removed=f.commit()
            f.checkout(f.freeze)
            f.put("transport-note","synthetic byte grammar refreeze".encode())
            f.freeze=f.commit()
            f.checkout(removed)
            f.git("merge","-q","--no-ff",f.freeze,"-m","Merge synthetic refreeze")
            acq=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",first,"P43_DIRTY")
            f.cli(self,"claim-acquisition",acq,"P43_ISOLATION",isolated=False)
            staged=f.inp/"bars.json"
            s.write_exclusive(staged,b"{}")
            f.cli(self,"claim-acquisition",acq,"P43_BARS_ALREADY_STAGED")
            staged.unlink()
            f.cli(self,"check-custody",acq,"P43_REFUSED")
            actions_file=f.inp/"actions.json"
            original_actions=actions_file.read_bytes()
            for case in ("missing_code","wrong_code","non_independent","blocked_comparator","cbio_complete","other_blocked"):
                with self.subTest(case=case):
                    altered=s.parse(original_actions)
                    legs=altered["records"][f.blocked]
                    if case=="missing_code":
                        del legs["stock"]["reason_code"]
                    elif case=="wrong_code":
                        legs["stock"]["reason_code"]="unsupported"
                    elif case=="non_independent":
                        legs["stock"]["reason_sources"]=[AUTH[0],AUTH[0]]
                    elif case=="blocked_comparator":
                        legs["IWM"].update(status="blocked",reason_code=s.NONCASH_SKIP,reason_sources=AUTH)
                    elif case=="cbio_complete":
                        legs["stock"]["status"]="complete"
                    else:
                        other=next(v for a,v in altered["records"].items() if a!=f.blocked)
                        other["stock"].update(status="blocked",reason_code=s.NONCASH_SKIP,reason_sources=AUTH)
                    actions_file.write_bytes(s.render(altered))
                    f.cli(self,"claim-acquisition",acq,"P43_ACTION_COVERAGE")
            actions_file.write_bytes(original_actions)
            f.cli(self,"claim-acquisition",acq,"P43_ACQUISITION_CLAIMED")
            f.cli(self,"claim-acquisition",acq,"P43_REFUSED")
            receipt=f.inp/f"acquisition.{acq}.lock"
            self.assertEqual(s.parse(receipt.read_bytes())["acquisition_commit"],acq)
            f.cli(self,"check-custody",acq,"P43_CUSTODY_READY")
            actions_file.write_bytes(s.render(s.parse(original_actions)|{"fixture":"different bytes"}))
            f.cli(self,"check-custody",acq,"P43_PIN")
            actions_file.write_bytes(original_actions)
            f.stage_packets(acq)
            staged=f.inp/"bars.json"
            staged_hold=f.inp/"bars.off"
            staged.rename(staged_hold)
            f.cli(self,"check-custody",acq,"P43_CUSTODY_CONSUMED")
            staged_hold.rename(staged)

            (f.root/s.ACQUISITION).write_bytes(f.acquisition()+b"changed")
            f.commit()
            amended=f.commit(s.APPROVAL,f.validation(acq))
            f.cli(self,"validate-inputs",amended,"P43_ACQUISITION_PIN")
            f.checkout(acq)
            bad=f.commit(s.APPROVAL,b"not a validation approval\n")
            f.cli(self,"validate-inputs",bad,"P43_APPROVAL")
            f.checkout(acq)
            bad=f.commit(s.APPROVAL,f.validation(acq,"1"*64))
            f.cli(self,"validate-inputs",bad,"P43_PIN")
            f.checkout(acq)
            packet=f.inp/"bars.json"
            original=packet.read_bytes()
            packet.write_bytes(b'{"version":0}\n')
            bad=f.commit(s.APPROVAL,f.validation(acq))
            f.cli(self,"validate-inputs",bad,"P43_BARS")
            packet.write_bytes(original)
            f.checkout(acq)
            val=f.commit(s.APPROVAL,f.validation(acq))
            buf=receipt.read_bytes()
            receipt.unlink()
            f.cli(self,"validate-inputs",val,"P43_REFUSED")
            s.write_exclusive(receipt,b"wrong")
            f.cli(self,"validate-inputs",val,"P43_PIN")
            receipt.unlink()
            s.write_exclusive(receipt,b"wrong-but-pinned")
            f.checkout(acq)
            wrong_receipt=f.commit(s.APPROVAL,f.validation(acq))
            f.cli(self,"validate-inputs",wrong_receipt,"P43_ACQUISITION_RECEIPT")
            receipt.unlink()
            s.write_exclusive(receipt,buf)
            f.checkout(val)
            nb=f.inp/"native/native_index.json"
            saved=nb.read_bytes()
            nb.write_bytes(b"tampered")
            f.cli(self,"validate-inputs",val,"P43_PIN")
            nb.write_bytes(saved)
            saved=staged.read_bytes()
            mismatch=s.parse(saved)
            next(iter(mismatch["records"].values()))["stock"]["raw"][0]["v"]+=1
            staged.write_bytes(s.render(mismatch))
            attest=f.inp/"offline_rebuild.json"
            orig_att=attest.read_bytes()
            attest.write_bytes(s.render(s.parse(orig_att)|{"rebuilt_bars_sha256":sha256(staged.read_bytes()).hexdigest()}))
            f.checkout(acq)
            no_rebuild=f.commit(s.APPROVAL,f.validation(acq))
            f.cli(self,"validate-inputs",no_rebuild,"P43_NATIVE_REBUILD")
            staged.write_bytes(saved)
            attest.write_bytes(orig_att)
            f.checkout(val)
            f.cli(self,"validate-inputs",val,"P43_VALIDATED")
            f.cli(self,"validate-inputs",val,"P43_VALIDATED")
            self.assertFalse((f.run/"score.lock").exists())
            self.assertFalse((f.run/"result.json").exists())
            proof=f.run/f"validation.{val}.json"
            good=proof.read_bytes()
            pin=sha256(good).hexdigest()
            proof.write_bytes(b"wrong")
            f.cli(self,"validate-inputs",val,"P43_PIN")
            proof.write_bytes(good)

            (f.root/s.APPROVAL).write_bytes(b"rewritten validation approval")
            f.commit()
            rewritten=f.commit(s.GO,f.release(val,pin))
            f.cli(self,"go",rewritten,"P43_VALIDATION_PIN")
            f.checkout(val)
            malformed=f.commit(s.GO,f.release(val,pin).rstrip())
            f.cli(self,"go",malformed,"P43_APPROVAL")
            f.checkout(val)
            wrong=f.commit(s.GO,f.release(val,"b"*64))
            f.cli(self,"go",wrong,"P43_VALIDATION_RECEIPT")
            f.checkout(val)
            go=f.commit(s.GO,f.release(val,pin))
            cover=f.run/f"coverage.{val}.json"
            cv=cover.read_bytes()
            cover.write_bytes(b"tampered")
            f.cli(self,"go",go,"P43_PIN")
            cover.write_bytes(cv)
            proof.unlink()
            f.cli(self,"go",go,"P43_REFUSED")
            self.assertFalse((f.run/"score.lock").exists())
            s.write_exclusive(proof,good)
            f.cli(self,"go",go,"P43_SCORED_ONCE")
            out=s.parse((f.run/"result.json").read_bytes())
            self.assertEqual(out["job"]["go_commit"],go)
            result=out["outcome"]
            self.assertEqual(result["eligible"],2)
            self.assertEqual(result["modeled"],1)
            self.assertEqual(result["skipped_by_reason"][s.NONCASH_SKIP],1)
            self.assertEqual(result["judged"]["absolute"]["n"],1)
            self.assertEqual(result["sleeves"]["placed"],1)
            self.assertEqual(result["no_trade_unaffordable"],0)
            self.assertEqual(result["idle_zero_mean"],result["judged"]["absolute"]["mean"])
            self.assertEqual(result["coverage"]["early_omissions"]["zero_volume_day1"],1)
            self.assertNotIn("entry_plus_one",result["shown"])
            f.cli(self,"go",go,"P43_CONSUMED")

    def test_real_cli_coverage_cap_and_partial_transport_holds(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            acq=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",acq,"P43_ACQUISITION_CLAIMED")
            f.stage_packets(acq,core_missing=True)
            index=f.inp/"native/transport_index.json"
            body=index.read_bytes()
            index.write_bytes(s.render(s.parse(body)|{"status":"failed_or_partial"}))
            partial=f.commit(s.APPROVAL,f.validation(acq))
            f.cli(self,"validate-inputs",partial,"P43_NATIVE_TRANSPORT")
            index.write_bytes(body)
            f.checkout(acq)
            val=f.commit(s.APPROVAL,f.validation(acq))
            f.cli(self,"validate-inputs",val,"P43_COVERAGE_CAP")
            summary=s.parse((f.run/f"coverage.{val}.json").read_bytes())["summary"]
            self.assertEqual(summary["refused_by_reason"]["missing_entry"],1)
            self.assertFalse((f.run/f"validation.{val}.json").exists())
            self.assertFalse((f.run/"score.lock").exists())

    def test_real_cli_exact_22_of_442_boundary(self):
        for omitted,expected in ((22,"P43_VALIDATED"),(23,"P43_COVERAGE_CAP")):
            with self.subTest(omitted=omitted), TemporaryDirectory() as d:
                f=SyntheticRepo(Path(d),with_blocked=True,modeled_count=442)
                acq=f.commit(s.ACQUISITION,f.acquisition())
                f.cli(self,"claim-acquisition",acq,"P43_ACQUISITION_CLAIMED")
                f.cli(self,"check-custody",acq,"P43_CUSTODY_READY")
                f.stage_packets(acq,core_missing=omitted)
                val=f.commit(s.APPROVAL,f.validation(acq))
                f.cli(self,"validate-inputs",val,expected)
                summary=s.parse((f.run/f"coverage.{val}.json").read_bytes())["summary"]
                self.assertEqual(summary["refused_by_reason"]["missing_entry"],omitted)
                self.assertEqual((f.run/f"validation.{val}.json").exists(),omitted==22)
                self.assertFalse((f.run/"score.lock").exists())

    def test_pinned_external_collector_real_scorer_and_offline_rebuild(self):
        if not s.COLLECTOR.exists():
            self.skipTest("External source only: provision the exact pinned v2 collector to run this witness.")
        collector=s.file_bytes(s.COLLECTOR,s.COLLECTOR_SHA256,2**20)
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d),with_blocked=True,modeled_count=442)
            collector_path=f.data/"collector.py"
            collector_path.write_bytes(collector)
            f.collector=sha256(collector).hexdigest()
            scorer=f.root/"research_rig/score_43.py"
            src=scorer.read_bytes()
            for var,value in (("DATA",f.data),("DOCKET",f.data/"docket.jsonl"),("COLLECTOR",collector_path)):
                old=next(line for line in src.splitlines() if line.startswith(f"{var} = ".encode()))
                src=src.replace(old,f"{var} = Path({str(value)!r})".encode(),1)
            scorer.write_bytes(src)
            f.repin()
            f.freeze=f.commit()
            acq=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",acq,"P43_ACQUISITION_CLAIMED")
            collector_api=runpy.run_path(str(collector_path))["preflight_and_lock"].__globals__
            receipt=f.inp/f"acquisition.{acq}.lock"
            native=f.inp/"native"
            bars=f.inp/"bars.json"
            args=(f.root,acq,receipt,f.inp,native,bars)
            network=Mock(side_effect=AssertionError("no live transport in a synthetic witness"))
            with patch.dict(collector_api,dict(CANONICAL_INPUT_DIR=f.inp,DOCKET=f.data/"docket.jsonl",
                                               raw_http_attempt=network)):
                cal=f.root/s.CALENDARS[0]
                clean_cal=cal.read_bytes()
                cal.write_bytes(b"synthetic mutable calendar")
                with patch.dict(collector_api,{"run_scorer_check_custody":Mock(side_effect=AssertionError)}):
                    with self.assertRaisesRegex(RuntimeError,"WORKTREE_DIRTY|PINNED_FILE_MISMATCH"):
                        collector_api["preflight_and_lock"](*args)
                self.assertFalse(native.exists())
                cal.write_bytes(clean_cal)
                custody=collector_api["preflight_and_lock"](*args)
                with self.assertRaisesRegex(RuntimeError,"FETCH_ALREADY_STARTED"):
                    collector_api["preflight_and_lock"](*args)
                f.stage_packets(acq,core_missing=22)
                rebuilt=f.data/"offline.bars.json"
                with redirect_stdout(StringIO()):
                    collector_api["build_from_native"](f.root,f.inp,native,rebuilt,*custody[1:])
                self.assertEqual(sha256(rebuilt.read_bytes()).digest(),sha256(bars.read_bytes()).digest())
                self.assertTrue(rebuilt.read_bytes()==bars.read_bytes())
            network.assert_not_called()
            val=f.commit(s.APPROVAL,f.validation(acq))
            f.cli(self,"validate-inputs",val,"P43_VALIDATED")
            self.assertFalse((f.run/"score.lock").exists())

    def third_fixture(self,f,mutate=None,omitted=0):
        if mutate is not None:
            mutate(f.packets[1]["records"])
        acq=f.commit(s.ACQUISITION,f.acquisition())
        f.cli(self,"claim-acquisition",acq,"P43_ACQUISITION_CLAIMED")
        f.stage_packets(acq,core_missing=omitted)
        previous=f.commit(s.APPROVAL,f.validation(acq))
        return f.basis_attempt(previous)

    def third_validate(self,f,val,expected=None):
        p=f.process("validate-inputs",val)
        output=p.stdout.splitlines()
        self.assertTrue(output,p.stderr)
        diag=json.loads(output[0])
        self.assertEqual((diag["plan"],diag["attempt"],diag["ledger"]),(43,3,195))
        if expected is None:
            self.assertEqual((p.returncode,output[1:],p.stderr),(0,["P43_VALIDATED"],""))
        else:
            self.assertEqual((p.returncode,output[1:],p.stderr),(2,[],expected+"\n"))
        return diag

    def test_attempt3_cli_quantized_low_price_and_one_go(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            def rounded(records):
                legs=next(iter(records.values()))
                for view in s.VIEWS:
                    for row in legs["SPY"][view]:
                        for key in "ohlc":
                            px=Decimal(row[key])*Decimal(".0173")
                            row[key]=px if view=="raw" else px.quantize(Decimal(".01"))
                for view in ("all","filing_all"):
                    for i,row in enumerate(legs["stock"][view]):
                        for key in "ohlc":
                            row[key]=Decimal(row[key]).quantize(Decimal(1).scaleb(-(2+i%3)))
            adoption,val=self.third_fixture(f,rounded)
            diag=self.third_validate(f,val)
            self.assertEqual(diag["gates"]["ohlc_shape"]["status"],"PARTIAL")
            self.assertEqual(diag["gates"]["ohlc_shape"]["failed"],0)
            self.assertEqual(diag["gates"]["raw_factor"]["status"],"PASS")
            self.assertEqual(diag["gates"]["native_provenance"]["status"],"PASS")
            self.assertEqual(diag["coverage"]["coverage_refused"],0)
            self.assertEqual(diag["gates"]["validation_receipt"]["status"],"PASS")
            f.cli(self,"claim-acquisition",val,"P43_ATTEMPT3_NO_VENDOR")
            receipt=f.run3/f"validation.{val}.json"
            diagfile=f.run3/f"diagnostics.{val}.json"
            original=diagfile.read_bytes()
            diagfile.write_bytes(b'{"malformed":"diagnostic"}')
            sealed=self.third_validate(f,val,"P43_PIN")
            self.assertEqual(sealed["gates"]["coverage_sidecar"]["status"],"PASS")
            self.assertEqual(sealed["gates"]["diagnostic_sidecar"]["status"],"HOLD")
            self.assertEqual(sealed["gates"]["validation_receipt"]["status"],"NOT_EVALUATED")
            diagfile.write_bytes(original)
            line=lambda pin:(f"Approved by the lead: plan 43 attempt 3 ledger 195, one scored run, "
                             f"validation approval commit {val}, validation receipt SHA-256 {pin}.\n").encode()
            bad=f.commit(s.GO3,line("a"*64))
            f.cli(self,"go",bad,"P43_VALIDATION_RECEIPT")
            self.assertFalse((f.run3/"score.lock").exists())
            f.checkout(val)
            pin=sha256(receipt.read_bytes()).hexdigest()
            go=f.commit(s.GO3,line(pin))
            f.cli(self,"go",go,"P43_SCORED_ONCE")
            f.cli(self,"go",go,"P43_CONSUMED")
            result=s.parse((f.run3/"result.json").read_bytes())["outcome"]
            self.assertEqual((result["attempt"],result["ledger"],set(result["prior_stops"])),(3,195,{"178","188"}))

    def test_attempt3_cli_wrong_factor_and_shape_are_reported_together(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d),modeled_count=2)
            def faults(records):
                first,second=list(records.values())
                for view in ("all","filing_all"):
                    for key in "ohlc":
                        second["stock"][view][9][key]*=Decimal("1.05")
                    first["stock"][view][8]["h"]+=1
            _,val=self.third_fixture(f,faults)
            diag=self.third_validate(f,val,"P43_RAW_BASIS_CHANGE")
            self.assertEqual(diag["gates"]["raw_factor"]["status"],"HOLD")
            self.assertEqual(diag["gates"]["ohlc_shape"]["status"],"REFUSAL")
            self.assertEqual(diag["gates"]["mixed_cap"]["status"],"HOLD")
            self.assertEqual(diag["gates"]["native_provenance"]["status"],"PASS")
            self.assertFalse((f.run3/f"validation.{val}.json").exists())
            self.assertFalse((f.run3/"score.lock").exists())

    def test_attempt3_exact_cent_envelope_boundary(self):
        b=runpy.run_path(str(s.ROOT/s.BASIS))
        interval,err=b["interval"],b["ERROR"]
        mk=lambda xs:SimpleNamespace(flat_key=xs)
        raw=mk([1,1,1,1])
        within=mk([1,1+err,1-err,1])
        outside=mk([1,1+err+Fraction(1,10**10),1-err,1])
        self.assertEqual(interval(raw,within),(1,1))
        self.assertIsNone(interval(raw,outside))
        low=mk([Fraction(1,1000)]*4)
        self.assertEqual(interval(low,low,err),(0,None))

    def test_attempt3_cli_same_row_fault_before_first_factor_anchor(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            def fault(records):
                stock=next(iter(records.values()))["stock"]
                for view in ("all","filing_all"):
                    row=stock[view][0]
                    for key in "ohlc":
                        row[key]*=2
                    row["h"]+=1
            _,val=self.third_fixture(f,fault)
            diag=self.third_validate(f,val,"P43_RAW_BASIS_CHANGE")
            self.assertEqual(diag["gates"]["raw_factor"]["status"],"HOLD")
            self.assertEqual(diag["gates"]["ohlc_shape"]["status"],"REFUSAL")
            self.assertFalse((f.run3/f"validation.{val}.json").exists())

    def test_attempt3_cli_digest_bound_bad_header_and_prior_receipt(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            f.packets[1]["endpoint"]="synthetic malformed metadata"
            _,val=self.third_fixture(f)
            diag=self.third_validate(f,val,"P43_NATIVE_REBUILD")
            self.assertEqual(diag["gates"]["packet_shape"]["status"],"HOLD")
            self.assertEqual(diag["gates"]["native_provenance"]["status"],"HOLD")
            self.assertEqual(diag["gates"]["core_tape"]["status"],"PASS")
            self.assertFalse((f.run3/f"validation.{val}.json").exists())
            s.write_exclusive(f.run/f'validation.{"a"*40}.json',b"{}")
            blocked=self.third_validate(f,val,"P43_PREVIOUS_RECEIPT")
            self.assertEqual(blocked["gates"]["previous_stop"]["status"],"HOLD")
            self.assertEqual(blocked["gates"]["bars_hash"]["status"],"NOT_EVALUATED")

    def test_attempt3_cli_mixed_cap_exact_boundary(self):
        for union,expected in ((22,None),(23,"P43_COVERAGE_CAP")):
            with self.subTest(union=union), TemporaryDirectory() as d:
                f=SyntheticRepo(Path(d),with_blocked=True,modeled_count=442)
                def faults(records):
                    for i,legs in enumerate(records.values()):
                        if i==0 or 11<=i<union:
                            for view in ("all","filing_all"):
                                legs["stock"][view][8]["h"]+=1
                _,val=self.third_fixture(f,faults,omitted=11)
                summary=self.third_validate(f,val,expected)["coverage"]
                self.assertEqual((summary["tape_refused"],summary["ohlc_shape_events"],
                                  summary["tape_and_shape"],summary["coverage_refused"]),(11,union-10,1,union))
                self.assertEqual(summary["refused_by_reason"]["ohlc_tick_shape"],union-11)
                self.assertEqual((f.run3/f"validation.{val}.json").exists(),union==22)
                self.assertFalse((f.run3/"score.lock").exists())

    def test_real_cli_native_lock_journal_and_attestation_refusals(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            acq=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",acq,"P43_ACQUISITION_CLAIMED")
            f.cli(self,"check-custody",acq,"P43_CUSTODY_READY")
            f.stage_packets(acq)
            lock=f.inp/f"fetch_start.{acq}.lock"
            native=f.inp/"native/native_index.json"
            transport=f.inp/"native/transport_index.json"
            att=f.inp/"offline_rebuild.json"
            page=f.inp/f"native/{next(iter(f.packets[0]['records']))}__raw__p0.json"
            original={p:p.read_bytes() for p in (lock,native,transport,att,page)}
            for case,code in (("wrong_lock","P43_NATIVE_LOCK"),("wrong_reviewer","P43_NATIVE_ATTESTATION"),
                              ("page_token","P43_NATIVE_REQUEST"),("body_inventory","P43_NATIVE_INVENTORY"),
                              ("duplicate_key","P43_DUPLICATE_KEY"),("nonfinite","P43_NUMBER"),
                              ("tab_token","P43_NATIVE_PAGINATION"),("long_token","P43_NATIVE_PAGINATION"),
                              ("padded_token","P43_NATIVE_PAGINATION")):
                with self.subTest(case=case):
                    stray=f.inp/"native/unindexed.json"
                    if case=="wrong_lock":
                        lock.write_bytes(s.render(s.parse(original[lock])|{"ledger":178}))
                    elif case=="wrong_reviewer":
                        att.write_bytes(s.render(s.parse(original[att])|{"reviewer":"unapproved"}))
                    elif case!="body_inventory":
                        doc=s.parse(original[transport])
                        native_doc=s.parse(original[native])
                        if case=="page_token":
                            paged=next(x for x in doc["attempts"] if x["page"]==1)
                            paged["params"]["page_token"]="substituted"
                        else:
                            if case=="duplicate_key":
                                payload=b'{"next_page_token":null,'+original[page][1:]
                            elif case=="nonfinite":
                                payload=b'{"metadata":NaN,'+original[page][1:]
                            else:
                                bad={"tab_token":"a\tb","long_token":"a"*8193,"padded_token":" a"}[case]
                                payload=s.render(s.parse(original[page])|{"next_page_token":bad})
                            page.write_bytes(payload)
                            for rows in (doc["attempts"],native_doc["files"]):
                                next(r for r in rows if r["file"]==page.name).update(
                                    bytes=len(payload),sha256=sha256(payload).hexdigest())
                        new_t=s.render(doc)
                        transport.write_bytes(new_t)
                        tp=sha256(new_t).hexdigest()
                        new_n=s.render(native_doc|{"transport_index_sha256":tp})
                        native.write_bytes(new_n)
                        att.write_bytes(s.render(s.parse(original[att])|{"transport_index_sha256":tp,
                                                                        "native_index_sha256":sha256(new_n).hexdigest()}))
                    else:
                        s.write_exclusive(stray,b"unindexed")
                    val=f.commit(s.APPROVAL,f.validation(acq))
                    f.cli(self,"validate-inputs",val,code)
                    self.assertFalse((f.run/f"validation.{val}.json").exists())
                    f.checkout(acq)
                    for p,blob in original.items():
                        p.write_bytes(blob)
                    if stray.exists():
                        stray.unlink()

    def test_real_cli_acquisition_git_refusals(self):
        flag="claim-acquisition"
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            needle=f.acquisition()
            for mode,ref in (("claim-acquisition",None),("check-custody",None),("validate-inputs",None),
                             ("go",None),("self-test",f.freeze)):
                rejection=f.process(mode,ref)
                self.assertEqual(rejection.returncode,2)
                self.assertIn("real modes require --approval-commit; synthetic modes reject it",rejection.stderr)
            f.cli(self,flag,"invalid","P43_APPROVAL")
            f.cli(self,flag,f.freeze,"P43_APPROVAL")
            bad=f.commit(s.ACQUISITION,needle.replace(f.collector.encode(),b"1"*64))
            f.cli(self,flag,bad,"P43_COLLECTOR_PIN")
            f.checkout(f.freeze)
            bad=f.commit(s.ACQUISITION,needle+b"\n")
            f.cli(self,flag,bad,"P43_APPROVAL")
            f.checkout(f.freeze)
            f.put("extra",b"not a sole-file add")
            bad=f.commit(s.ACQUISITION,needle)
            f.cli(self,flag,bad,"P43_APPROVAL_SCOPE")
            f.checkout(f.freeze)
            side=f.commit("side",b"synthetic second parent")
            f.checkout(f.freeze)
            f.git("merge","-q","--no-ff","--no-commit",side)
            bad=f.commit(s.ACQUISITION,needle)
            f.cli(self,flag,bad,"P43_APPROVAL")
            f.checkout(f.freeze)
            bad=f.commit(s.ACQUISITION,f.acquisition(freeze=side))
            f.cli(self,flag,bad,"P43_ANCESTOR")
            f.checkout(f.freeze)
            for path,content,expected in (
                (s.CALIBRATION,b"{}", "P43_PIN"),
                ("docs/QUEUE.md",b"| 74 | changed |\n","P43_LEDGER_QUEUE"),
                ("research_rig/TRIAL_LEDGER.md",b"| 188 | changed |\n","P43_LEDGER_QUEUE"),
            ):
                with self.subTest(path=path):
                    f.commit(path,content)
                    bad=f.commit(s.ACQUISITION,needle)
                    f.cli(self,flag,bad,expected)
                    f.checkout(f.freeze)
            f.commit(s.APPROVAL,b"stale approval at freeze")
            historical=f.git("rev-parse","HEAD")
            bad=f.commit(s.ACQUISITION,f.acquisition(freeze=historical))
            f.cli(self,flag,bad,"P43_APPROVAL_FROZEN")
            f.checkout(f.freeze)
            start=f.freeze
            f.put(s.PLAN,(f.root/s.PLAN).read_bytes().replace(b"Status FROZEN.",b"Status DRAFT."))
            f.repin()
            f.freeze=f.commit()
            draft=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,flag,draft,"P43_FREEZE")
            f.checkout(start)
            f.freeze=start
            f.repin()
            valid=f.commit(s.ACQUISITION,needle)
            f.put("untracked",b"dirty tree")
            f.cli(self,flag,valid,"P43_DIRTY")
            (f.root/"untracked").unlink()
            f.run.chmod(0o755)
            f.cli(self,flag,valid,"P43_PRIVATE")
            f.run.chmod(0o700)
            docket=f.data/"docket.jsonl"
            docket.write_bytes(b"not pinned")
            f.cli(self,flag,valid,"P43_PIN")
            self.assertFalse((f.inp/f"acquisition.{valid}.lock").exists())

    def test_real_cli_proof_mismatch_and_pinned_malformed_docket(self):
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            start=f.freeze
            proof=f.root/s.CALIBRATION
            altered=s.parse(proof.read_bytes())|{"shares":[1]}
            f.put(s.CALIBRATION,s.render(altered))
            f.repin()
            f.commit()
            bad=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",bad,"P43_FREEZE")
            f.checkout(start)
            f.put(s.CALIBRATION,s.render(altered))
            f.repin()
            f.freeze=f.commit()
            bad=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",bad,"P43_CALIBRATION")
            f.checkout(start)
            cfg_path=f.root/s.CONFIG
            c=s.config(cfg_path.read_bytes())
            c["resources"]["disk_floor_mib"]=10**12
            f.put(s.CONFIG,b"replay_43_plan:\n  value: "+json.dumps(c,default=float).encode()+b"\n")
            f.repin()
            f.freeze=f.commit()
            bad=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",bad,"P43_RESOURCES")
            f.checkout(start)
            docket=f.data/"docket.jsonl"
            stub=b'{"accession":"not-a-filing"}\n'
            docket.write_bytes(stub)
            old=f.dp
            f.dp=sha256(stub).hexdigest()
            f.put(s.CONFIG,(f.root/s.CONFIG).read_bytes().replace(old.encode(),f.dp.encode()))
            f.repin()
            f.freeze=f.commit()
            bad=f.commit(s.ACQUISITION,f.acquisition())
            f.cli(self,"claim-acquisition",bad,"P43_DOCKET")

    def test_packet_file_size_mode_and_symlink_guards(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            packet=root/"synthetic"
            pin=sha256(b"synthetic").hexdigest()
            s.write_exclusive(packet,b"synthetic")
            with self.assertRaisesRegex(s.Refused,"FILE"):
                s.file_bytes(packet,pin,8,private=True)
            packet.chmod(0o644)
            with self.assertRaisesRegex(s.Refused,"PRIVATE"):
                s.file_bytes(packet,pin,32,private=True)
            link=root/"link"
            link.symlink_to(packet)
            with self.assertRaisesRegex(s.Refused,"FILE"):
                s.file_bytes(link,pin,32,private=True)

    def test_concurrent_exclusive_gate_file(self):
        with TemporaryDirectory() as d, ThreadPoolExecutor(max_workers=2) as pool:
            lock=Path(d)/"lock"
            def claimant(n):
                try:
                    s.write_exclusive(lock,str(n).encode())
                except FileExistsError:
                    return None
                return n
            outcomes=list(pool.map(claimant,(1,2)))
            winners=[n for n in outcomes if n is not None]
            self.assertEqual(len(winners),1)
            self.assertEqual(lock.read_text(),str(winners[0]))

    def test_cutoff_preopen_and_weekend(self):
        q,days,_,c,*_=condition()
        w=lambda x:s.window(datetime.fromisoformat(x),days,c)
        self.assertEqual(w("2024-06-07T03:00:00-04:00").entry,date(2024,6,11))
        self.assertEqual(w("2024-06-07T15:59:59-04:00").entry,date(2024,6,11))
        self.assertEqual(w("2024-06-07T16:00:00-04:00").entry,date(2024,6,12))
        self.assertEqual(w("2024-06-08T12:00:00-04:00").entry,date(2024,6,12))
        self.assertEqual(w("2024-06-07T15:59:59-04:00").early,date(2024,6,10))
        self.assertEqual(days.index(q[0].exit)-days.index(q[0].day0),20)
        days.closes[date(2024,6,7)]=datetime(2024,6,7,13,tzinfo=s.ET)
        self.assertEqual(w("2024-06-07T12:59:59-04:00").entry,date(2024,6,11))
        self.assertEqual(w("2024-06-07T13:00:00-04:00").entry,date(2024,6,12))

    def test_calendars_agree(self):
        blobs=[(s.ROOT/n).read_bytes() for n in s.CALENDARS]
        days=s.calendar(blobs)
        self.assertEqual(days[0],date(2015,12,15))
        self.assertEqual(days[-1],date(2026,11,24))

    def test_docket_pin_and_duplicate(self):
        q,days,_,c,*_=condition()
        with self.assertRaisesRegex(s.Refused,"DOCKET_PIN"):
            s.events(b"not the docket",days,c)
        with self.assertRaisesRegex(s.Refused,"DUPLICATE_KEY"):
            s.parse(b'{"a":1,"a":2}')

    def test_silent_validation_never_trade_or_returns(self):
        with patch.object(s,"trade",side_effect=AssertionError), patch.object(s,"marks",side_effect=AssertionError):
            a=condition()
            ready=s.prepared(*a)
        self.assertEqual(set(ready[a[0][0].a]),{"stock","IWM","SPY"})

    def test_blocked_stock_never_needs_bars_but_other_coverage_remains_required(self):
        p=condition()
        blocked=add_blocked(p[0],*p[4:])
        del p[5]["records"][blocked]
        self.assertEqual(set(s.prepared(*p)),{p[0][0].a})
        p[6]["records"][blocked]["SPY"]["status"]="incomplete"
        with self.assertRaisesRegex(s.Refused,"ACTION_COVERAGE"):
            s.prepared(*p)

    def test_approval_receipts_and_recheck(self):
        ordered,days,_,c,*_=condition()
        commit="a"*40
        job=dict(ledger=s.LEDGER,acquisition_commit=commit,freeze_commit="b"*40,
                 freeze_sha256="c"*64,docket_sha256=c["docket_sha256"])
        proof=dict(docket_sha256=c["docket_sha256"],trials=c["calibration"]["trials"],eligible=len(ordered),
                   edges=c["calibration"]["edges"],shares=[0])
        blobs={s.CONFIG:(s.ROOT/s.CONFIG).read_bytes(),s.CALIBRATION:s.render(proof),s.ENGINE:b"dummy",
               s.PROVENANCE:b"dummy"}
        with TemporaryDirectory() as d,redirect_stdout(StringIO()):
            tmp=Path(d)
            inp,run=tmp/"inp",tmp/"run"
            inp.mkdir(mode=0o700)
            run.mkdir(mode=0o700)
            auth=Mock(side_effect=lambda *_:(job.copy(),blobs))
            returns=Mock(side_effect=lambda *_:{"dummy":True})
            collector=tmp/"collector.py"
            collector.write_bytes(b"synthetic")
            with patch.multiple(s,INPUT=inp,RUN=run,COLLECTOR=collector,COLLECTOR_SHA256=sha256(b"synthetic").hexdigest(),
                                authorize=auth,resources=Mock(),check_native=Mock(),identity_actions=Mock(),
                                local_schedule=Mock(return_value=(ordered,days,c)),engine=Mock(),
                                prepared=Mock(return_value=s.Prepared()),report=returns):
                for name in ("identities.json","actions.json"):
                    s.write_exclusive(inp/name,b"{}")
                s.approved(commit,"acquire")
                with self.assertRaises(FileExistsError):
                    s.approved(commit,"acquire")
                receipt=inp/f"acquisition.{commit}.lock"
                job.update(approval_commit="d"*40,acquisition_receipt_sha256=sha256(receipt.read_bytes()).hexdigest())
                s.write_exclusive(inp/"bars.json",b"{}")
                for name in s.PACKETS:
                    job[name]=sha256(b"{}").hexdigest()
                for _ in range(2):
                    s.approved(job["approval_commit"],"validate")
                returns.assert_not_called()
                self.assertFalse((run/"score.lock").exists())
                validated=run/f'validation.{job["approval_commit"]}.json'
                job.update(go_commit="e"*40,validation_receipt_sha256="f"*64)
                with self.assertRaisesRegex(s.Refused,"VALIDATION_RECEIPT"):
                    s.approved(job["go_commit"],"go")
                job["validation_receipt_sha256"]=sha256(validated.read_bytes()).hexdigest()
                auth.side_effect=[(job.copy(),blobs),(job.copy()|{"freeze_commit":"1"*40},blobs)]
                with self.assertRaisesRegex(s.Refused,"APPROVAL_CHANGED"):
                    s.approved(job["go_commit"],"go")
                returns.assert_not_called()
                self.assertFalse((run/"score.lock").exists())
                auth.side_effect=lambda *_:(job.copy(),blobs)
                s.approved(job["go_commit"],"go")
                self.assertTrue((run/"score.lock").exists())
                with self.assertRaisesRegex(s.Refused,"CONSUMED"):
                    s.approved(job["go_commit"],"go")
                returns.assert_called_once()

    def test_missing_zero_and_stale_bar(self):
        q,_,_,_,_,_,_=condition()
        a=q[0].a
        for change in ("missing","zero","stale"):
            p=condition()
            r=p[5]["records"][a]["stock"]
            entry=q[0].entry.isoformat()
            if change=="missing":
                r["raw"]=[b for b in r["raw"] if not b["t"].startswith(entry)]
            elif change=="zero":
                next(b for b in r["raw"] if b["t"].startswith(entry))["v"]=0
            else:
                dates=[b["t"] for b in r["all"]]
                i=next(i for i,t in enumerate(dates) if t.startswith(entry))
                for k in ("all","filing_all"):
                    for j in range(i-2,i+3):
                        r[k][j].update(o=20,h=21,l=19,c=20)
            with self.subTest(change=change):
                if change=="stale":
                    with self.assertRaisesRegex(s.Refused,"BAR_MISSING_STALE"):
                        s.prepared(*p)
                else:
                    ready=s.prepared(*p)
                    self.assertEqual(ready.decisions[a]["refusal"],
                                     ("missing" if change=="missing" else "zero_volume")+"_entry")

    def test_asof_shape_and_identity(self):
        p=condition(); a=p[0][0].a
        p[5]["records"][a]["stock"]["entry_asof"]="2024-07-01"
        with self.assertRaisesRegex(s.Refused,"BAR_SCOPE"):
            s.prepared(*p)
        p=condition()
        p[4]["records"][a]["stock"]["share_class"]="wrong"
        with self.assertRaisesRegex(s.Refused,"IDENTITY"):
            s.prepared(*p)
        p=condition()
        r=p[5]["records"][a]["stock"]
        next(b for b in r["filing_all"] if b["t"].startswith(p[0][0].entry.isoformat()))["h"]+=2
        with self.assertRaisesRegex(s.Refused,"BAR_IDENTITY"):
            s.prepared(*p)
        p=condition()
        legs=p[5]["records"][a]
        for k in ("raw","all","filing_all"):
            legs["SPY"][k]=copy.deepcopy(legs["IWM"][k])
        with self.assertRaisesRegex(s.Refused,"BAR_ALIAS"):
            s.prepared(*p)

    def test_padded_cross_day_basis_witnesses(self):
        for change,code in (("raw_double","RAW_BASIS_CHANGE"),("asof_scale","ASOF_BASIS_CHANGE")):
            p=condition()
            e=p[0][0]
            bar=p[5]["records"][e.a]["IWM"]
            if change=="raw_double":
                row=next(r for r in bar["raw"] if r["t"].startswith(e.entry.isoformat()))
                for k in "ohlc":
                    row[k]*=2
            elif change=="asof_scale":
                for n,row in enumerate(bar["filing_all"]):
                    for k in "ohlc":
                        row[k]*=2+n%2
            with self.subTest(change=change),self.assertRaisesRegex(s.Refused,code):
                s.prepared(*p)

    def test_successor_core_priority_and_exact_cap(self):
        for day_key,cell,code in (("entry","zero","zero_volume_entry"),("exit","missing","missing_exit"),
                                  ("core","zero","zero_volume_hold"),("core","missing","missing_hold")):
            p=condition()
            e=p[0][0]
            day=next(x for x in p[1] if e.entry<x<e.exit) if day_key=="core" else getattr(e,day_key)
            v=p[5]["records"][e.a]["SPY"]["filing_all"]
            i=next(j for j,r in enumerate(v) if r["t"].startswith(day.isoformat()))
            if cell=="zero":
                v[i]["v"]=0
            else:
                del v[i]
            ready=s.prepared(*p)
            self.assertEqual(ready.decisions[e.a]["refusal"],code)
            self.assertNotIn(e.a,ready)
        self.assertEqual(s.coverage_limit(442),22)
        decisions=s.Prepared()
        decisions.decisions={str(i):dict(refusal="missing_entry" if i<22 else None) for i in range(442)}
        decisions.decisions["noncash"]=dict(noncash=s.NONCASH_SKIP)
        s.enforce_coverage(decisions)
        decisions.decisions["22"]["refusal"]="zero_volume_exit"
        with self.assertRaisesRegex(s.Refused,"COVERAGE_CAP"):
            s.enforce_coverage(decisions)
        self.assertEqual(s.downside_floor(Fraction(3,2),cfg()),Fraction(-5,2))

    def test_unrelated_gap_never_hides_basis_or_stale_evidence(self):
        for defect,code in (("basis","RAW_BASIS_CHANGE"),("stale","BAR_MISSING_STALE")):
            p=condition()
            e=p[0][0]
            view=p[5]["records"][e.a]["IWM"]
            i=next(j for j,r in enumerate(view["raw"]) if r["t"].startswith(str(e.entry)))
            if defect=="basis":
                del view["filing_all"][i]
                for k in "ohlc":
                    view["raw"][i][k]*=2
            else:
                # The five positive adjusted rows straddle the shown-only fill
                # while filing-view padding beside it is unavailable.
                for mode in ("all","filing_all"):
                    for j in range(i-5,i):
                        view[mode][j].update(o=16,h=17,l=15,c=16)
                del view["filing_all"][i-3]
            with self.subTest(defect=defect),self.assertRaisesRegex(s.Refused,code):
                s.prepared(*p)

    def test_cash_factor_invalid_vs_missing_and_exact_split_gap(self):
        p=condition()
        e=p[0][0]
        v=p[5]["records"][e.a]["IWM"]
        j=next(i for i,r in enumerate(v["raw"]) if r["t"].startswith(str(e.entry)))
        v_cash=str(v["raw"][j-1]["c"])
        p[6]["records"][e.a]["IWM"]["items"].append(dict(id="cash",ex=str(e.entry),kind="ordinary",
                    value=v_cash,payment=str(e.entry),available=str(e.entry),sources=AUTH))
        with self.assertRaisesRegex(s.Refused,"DIVIDEND_BASIS"):
            s.prepared(*p)
        del v["raw"][j-1]
        ready=s.prepared(*p)
        self.assertEqual(ready.decisions[e.a]["unproved_cash_bridge"],{"IWM":[str(e.entry)]})
        self.assertEqual(ready.decisions[e.a]["early"],"missing_day1")
        self.assertIn(e.a,ready)
        # Force both cash transitions into one bridge: the first is unproved,
        # but the second still has a present and invalid preceding raw close.
        later=v["raw"][j]["t"][:10]
        del v["all"][j]
        p[6]["records"][e.a]["IWM"]["items"].append(dict(id="cash2",ex=later,kind="ordinary",
                    value=str(v["raw"][j-1]["c"]),payment=later,available=later,sources=AUTH))
        with self.assertRaisesRegex(s.Refused,"DIVIDEND_BASIS"):
            s.prepared(*p)
        p=condition()
        e=p[0][0]
        v=p[5]["records"][e.a]["SPY"]
        ex=p[1][p[1].index(e.early)-2]
        for view in ("all","filing_all"):
            for row in v[view]:
                if row["t"][:10]<str(ex):
                    for k in "ohlc":
                        row[k]=Decimal(row[k])/2
            v[view]=[row for row in v[view] if row["t"][:10]!=str(ex)]
        a=p[6]["records"][e.a]["SPY"]["items"]
        a.append(dict(id="split",ex=str(ex),kind="split",new_shares=2,old_shares=1,
                      payment=None,available=None,sources=AUTH))
        self.assertIn(e.a,s.prepared(*p))
        a.clear()
        with self.assertRaisesRegex(s.Refused,"RAW_BASIS_CHANGE"):
            s.prepared(*p)

    def test_insufficient_adjusted_pair_and_three_distinct_native_alias_dates(self):
        p=condition()
        e=p[0][0]
        v=p[5]["records"][e.a]["SPY"]
        v["filing_all"]=v["filing_all"][:2]
        ready=s.prepared(*p)
        self.assertEqual(ready.decisions[e.a]["adjusted_insufficient"],["SPY"])
        v["filing_all"][0]["h"]+=1
        with self.assertRaisesRegex(s.Refused,"OHLC_BASIS"):
            s.prepared(*p)
        for equivalent in (2,3):
            p=condition()
            e=p[0][0]
            legs=p[5]["records"][e.a]
            for mode in s.VIEWS:
                legs["SPY"][mode]=copy.deepcopy(legs["IWM"][mode])
                for row in legs["SPY"][mode][equivalent:]:
                    row["v"]+=7
            # A separate core omission should not hide raw matching rows in the pad.
            legs["SPY"]["filing_all"].pop(8)
            if equivalent==3:
                with self.assertRaisesRegex(s.Refused,"BAR_ALIAS"):
                    s.prepared(*p)
            else:
                self.assertEqual(s.prepared(*p).decisions[e.a]["refusal"],"missing_hold")

    def test_refused_event_still_checks_all_present_raw_overlap(self):
        p=condition()
        e=p[0][0]
        extra=add_blocked(p[0],*p[4:],accession="0000000002-24-000001")
        legs=p[6]["records"][extra]
        legs["stock"]["status"]="complete"
        legs["stock"]["target_disclosure"].update(accession=extra,
            filing=f"https://www.sec.gov/Archives/edgar/data/2/{extra}.txt")
        p[5]["records"][extra]=copy.deepcopy(p[5]["records"][e.a])
        bar=p[5]["records"][extra]
        bar["stock"].update(identity="SECL-BLOCKED",ticker="BLOCKED")
        for mode in s.VIEWS:
            for row in bar["stock"][mode]:
                row["v"]+=111
        bar["stock"]["filing_all"].pop(8)
        prior=bar["IWM"]["raw"][0]
        prior["v"]=0
        with self.assertRaisesRegex(s.Refused,"BAR_CONFLICT"):
            s.prepared(*p)

    def test_alias_with_single_mismatched_session_and_small_cumulative_drift(self):
        for change,code in (("alias","BAR_ALIAS"),("drift","RAW_BASIS_CHANGE")):
            p=condition()
            e=p[0][0]
            bars=p[5]["records"][e.a]
            actions=p[6]["records"][e.a]["stock"]
            ex=(e.end+timedelta(days=1))
            while ex not in p[1]:
                ex+=timedelta(days=1)
            actions["items"][0].update(ex=ex.isoformat(),available=ex.isoformat())
            for mode in ("all","filing_all"):
                bars["stock"][mode]=copy.deepcopy(bars["stock"]["raw"])
            if change=="alias":
                for mode in ("raw","all","filing_all"):
                    bars["IWM"][mode]=copy.deepcopy(bars["stock"][mode])
                    bars["IWM"][mode][0]["v"]+=1
            else:
                for i,row in enumerate(bars["stock"]["raw"]):
                    for field in "ohlc":
                        row[field]*=1+Decimal("0.00009")*i
            with self.subTest(change=change),self.assertRaisesRegex(s.Refused,code):
                s.prepared(*p)

    def test_duplicate_target_and_two_distinct_classes(self):
        for change,code in (("target","ACTION_TARGET"),("class","IDENTITY"),("inverse","IDENTITY_SUBJECT")):
            p=condition()
            at=p[0][0]
            e=SimpleNamespace(**(vars(at)|dict(a="0000000001-24-000002")))
            p[0].append(e)
            for i in (4,5,6):
                p[i]["records"][e.a]=copy.deepcopy(p[i]["records"][at.a])
            ar=p[6]["records"][e.a]["stock"]["target_disclosure"]
            ar.update(accession=e.a,filing=f"https://www.sec.gov/Archives/edgar/data/1/{e.a}.txt")
            if change=="class":
                e.cl="Class B"
                p[4]["records"][e.a]["stock"].update(share_class=e.cl,class_key="class-b")
            if change=="inverse":
                p[4]["records"][e.a]["stock"]["identity"]="OTHER-STOCK"
            with self.subTest(change=change),self.assertRaisesRegex(s.Refused,code):
                s.prepared(*p)

    def test_class_alias_and_action_alias(self):
        first=SimpleNamespace(a="a",cik="0000000001",cl="Issuer Class A non-voting common")
        second=SimpleNamespace(a="b",cik="0000000001",cl="OLDTICKER Class A common")
        self.assertEqual(s.canonical_class(first),s.canonical_class(second))
        p=condition()
        at=p[0][0]
        e=SimpleNamespace(**(vars(at)|dict(a="0000000001-24-000002")))
        p[0].append(e)
        for i in (4,5,6):
            p[i]["records"][e.a]=copy.deepcopy(p[i]["records"][at.a])
        z=p[6]["records"][e.a]["stock"]
        z["items"][0]["id"]="renamed"
        z["target"]="renamed"
        z["target_disclosure"].update(accession=e.a,filing=f"https://www.sec.gov/Archives/edgar/data/1/{e.a}.txt")
        with self.assertRaisesRegex(s.Refused,"ACTION_ID_ALIAS"):
            s.prepared(*p)

    def test_action_amount_source_and_due_bill(self):
        p=condition(); a=p[0][0].a
        self.assertEqual(s.prepared(*p)[a]["stock"][-1],p[0][0].exit)
        for k,value in (("value","1.20"),("available",p[0][0].entry.isoformat()),("sources",[AUTH[0],AUTH[0]])):
            p=condition()
            p[6]["records"][a]["stock"]["items"][0][k]=value
            with self.subTest(k=k),self.assertRaises(s.Refused):
                s.prepared(*p)

    def test_entitlement_interval_and_return_denominators(self):
        q,_,C,c,*_=condition()
        e=q[0]; D=Decimal
        op,cl=D("99"),D("101")
        raw={e.entry:C.Bar(op,op,op,op,D(500)),e.exit:C.Bar(cl,cl,cl,cl,D(500))}
        available=e.exit+timedelta(days=4)
        outside=e.exit+timedelta(days=1)
        seq=[(e.entry,"ordinary",D(77),available,available),(e.exit,"special",D(2),e.entry,available),
             (outside,"ordinary",D(80),available,available)]
        trade=s.trade(e,(raw,seq,e.exit),e.entry,500,5,c)
        self.assertEqual(trade.used, D("495.2475"))
        self.assertEqual(trade.cash,[(available,D(10))])
        self.assertEqual(trade.pnl,D("19.5000"))
        self.assertAlmostEqual(trade.economic,.039)
        self.assertGreater(trade.deployed,trade.economic)
        self.assertTrue(trade.inside)
        self.assertEqual(s.fee(D(3),5,c),D(".01"))
        self.assertEqual(s.quantity(D(500),500,5,c),0)

    def test_split_checks(self):
        q,_,_,c,*_=condition()
        e=q[0]
        seq=[(e.exit,"split",Decimal(".5"),None,None)]
        self.assertEqual(s.split_basis(4,seq,e.entry,e.exit),2)
        with self.assertRaisesRegex(s.Refused,"FRACTIONAL_SPLIT"):
            s.split_basis(3,seq,e.entry,e.exit)
        exact=[(e.exit,"split",Fraction(1,3),None,None)]
        self.assertEqual(s.split_basis(3,exact,e.entry,e.exit),1)
        with self.assertRaisesRegex(s.Refused,"FRACTIONAL_SPLIT"):
            s.split_basis(3,[(e.exit,"split",Decimal("0.333333333333333333333333333333333"),None,None)],e.entry,e.exit)

    def test_cluster_and_trim(self):
        x=s.cluster([("a",.03),("a",.03),("b",.01),("b",.01)])
        self.assertAlmostEqual(x["mean"],.02)
        self.assertAlmostEqual(x["t"],2)
        self.assertIsNone(s.cluster([("a",1),("a",2)])["t"])
        c=cfg()
        rs=[SimpleNamespace(a=str(i),stock=.01+i*.000001,control=.001,year=2016+i%11,month=str(i%100))
            for i in range(300)]
        marks=s.marks(rs,c)
        self.assertTrue(marks["passed"])
        self.assertEqual(marks["trim_removed"],3)
        self.assertFalse(s.marks(rs[:-1],c)["marks"]["placed"])
        zero=[SimpleNamespace(a=str(i),stock=v,control=0,year=2020,month=str(i))
              for i,v in enumerate((Decimal(".1"),Decimal(".2"),Decimal("-.3")))]
        self.assertEqual(s.marks(zero,c)["absolute"]["mean"],0)
        self.assertFalse(s.marks(zero,c)["marks"]["net"])
        self.assertFalse(s.marks(zero,c)["marks"]["recent"])

    def test_sleeve_same_open_miss_reserves_and_one_issuer(self):
        p=condition(); e=p[0][0]; day=e.entry
        cal=p[1]
        c=dict(p[3],sleeves=2)
        def copy_e(a,cik):
            return SimpleNamespace(**(vars(e)|dict(a=a,cik=cik)))
        rows=[copy_e("a","1"),copy_e("aa","1"),copy_e("b","2"),copy_e("c","2"),copy_e("d","3")]
        C=p[2]
        def tape(n):
            v=Decimal(n)
            b=C.Bar(v,v,v,v,v)
            return ({day:b,e.exit:b},[],None)
        packet={x.a:{"stock":tape(500 if x.a=="a" else 40)} for x in rows}
        result=s.sleeve_path(rows,packet,cal,c)
        self.assertEqual(result["placed"],1)
        self.assertEqual(result["skips"],dict(cannot_buy_share_or_unsettled=1,issuer_open=2,no_free_sleeve=1))

    def test_lock_one_shot_and_failure_consumes(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)
            with self.assertRaises(RuntimeError):
                s.once(p,dict(case="synthetic"),lambda:(_ for _ in ()).throw(RuntimeError()))
            self.assertTrue((p/"score.lock").exists())
            self.assertFalse((p/"result.json").exists())
            with self.assertRaisesRegex(s.Refused,"CONSUMED"):
                s.once(p,{},lambda:1)
        with TemporaryDirectory() as folder:
            p=Path(folder)
            s.once(p,{},lambda:{"done":True})
            self.assertEqual(s.parse((p/"result.json").read_bytes())["outcome"],{"done":True})

    def test_unapproved_never_reads_packets(self):
        with patch.object(s,"file_bytes",side_effect=AssertionError):
            with self.assertRaisesRegex(s.Refused,"APPROVAL"):
                s.approved("bad","validate")


if __name__=="__main__":
    unittest.main()
