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


def add_blocked(event_rows, ids, bars, acts):
    event=event_rows[0]
    blocked=SimpleNamespace(**(vars(event)|dict(a="0000000002-24-000001",cik="0000000002")))
    event_rows.append(blocked)
    for packet in (ids,acts):
        packet["records"][blocked.a]=copy.deepcopy(packet["records"][event.a])
        packet["records"][blocked.a]["stock"]["identity"]="SECL-BLOCKED"
    ids["records"][blocked.a]["stock"].update(cik=blocked.cik,ticker="BLOCKED")
    stock=acts["records"][blocked.a]["stock"]
    stock.update(status="blocked",reason_code=s.NONCASH_SKIP,reason_sources=AUTH)
    bars["records"][blocked.a]="Any attempt to evaluate this excluded event's tape must fail"
    return blocked.a


class SyntheticRepo:
    """Real Git objects and CLI in a temporary tree; only absolute paths are redirected."""

    BOOT = """
import runpy, sys
from pathlib import Path
root, data = map(Path, sys.argv[1:3])
g = runpy.run_path(str(root / "research_rig/score_43.py"))["main"].__globals__
g.update(ROOT=root, DATA=data, INPUT=data/"plan43_inputs", RUN=data/"replay_43", DOCKET=data/"docket.jsonl")
sys.argv = ["score_43.py", *sys.argv[3:]]
raise SystemExit(g["main"]())
"""

    def __init__(self, base, with_blocked=False):
        self.root=base/"repo"
        self.data=base/"data"
        self.root.mkdir()
        self.data.mkdir(mode=0o700)
        self.inp=self.data/"plan43_inputs"
        self.run=self.data/"replay_43"
        self.inp.mkdir(mode=0o700)
        self.run.mkdir(mode=0o700)
        self.git("init","-q","-b","main")
        self.git("config","user.name","Synthetic Fixture")
        self.git("config","user.email","fixture@example.invalid")
        self.git("config","commit.gpgsign","false")
        ds=s.calendar([(s.ROOT/n).read_bytes() for n in s.CALENDARS])
        events,_,_,c,*self.packets=condition(ds)
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
        config=b"replay_43_plan:\n  value: "+json.dumps(c,default=float).encode()+b"\n"
        proof=s.render(dict(docket_sha256=self.dp,trials=c["calibration"]["trials"],eligible=len(events),
                            edges=c["calibration"]["edges"],shares=[0]))
        custom={s.CONFIG:config,s.CALIBRATION:proof}
        for name in s.SOURCES:
            blob=custom[name] if name in custom else (s.ROOT/name).read_bytes()
            if name==s.PLAN:
                blob=blob.replace(b"Status DRAFT.",b"Status FROZEN.")
            self.put(name,blob)
        for name,num in (("research_rig/TRIAL_LEDGER.md",178),("docs/QUEUE.md",74)):
            self.put(name,f"| {num} | `{s.PLAN}` | synthetic selection |\n".encode())
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

    def repin(self):
        pins={k:sha256((self.root/k).read_bytes()).hexdigest() for k in s.SOURCES}
        blob=s.render(pins)
        self.put(s.PINS,blob)
        self.fp=sha256(blob).hexdigest()

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
        return (f"Approved by the lead: plan 43, one custodian acquisition, freeze commit {freeze}, "
                f"freeze SHA-256 {self.fp}, docket SHA-256 {self.dp}.\n").encode()

    def validation(self,acq,bars_pin=None):
        receipt=self.inp/f"acquisition.{acq}.lock"
        ap=sha256(receipt.read_bytes()).hexdigest()
        ids,bars,actions=(sha256((self.inp/n).read_bytes()).hexdigest() for n in s.PACKETS)
        return (f"Approved by the lead: plan 43, validation only, acquisition commit {acq}, "
                f"acquisition receipt SHA-256 {ap}, identities SHA-256 {ids}, bars SHA-256 {bars_pin or bars}, "
                f"actions SHA-256 {actions}.\n").encode()

    def release(self,val,pin):
        return (f"Approved by the lead: plan 43, one scored run, validation approval commit {val}, "
                f"validation receipt SHA-256 {pin}.\n").encode()

    def process(self,flag,ref=None,*,isolated=True):
        flags=("-I","-B") if isolated else ("-B",)
        args=[] if ref is None else ["--approval-commit",ref]
        return subprocess.run([sys.executable,*flags,"-c",self.BOOT,str(self.root),str(self.data),
                               "--"+flag,*args],capture_output=True,text=True,timeout=120)

    def cli(self,test,flag,ref,expected,*,isolated=True):
        proc=self.process(flag,ref,isolated=isolated)
        ok=expected in ("P43_ACQUISITION_CLAIMED","P43_VALIDATED","P43_SCORED_ONCE")
        test.assertEqual(proc.returncode,0 if ok else 2,proc.stderr)
        test.assertEqual((proc.stdout,proc.stderr),((expected+"\n","") if ok else ("",expected+"\n")))

    def stage_packets(self):
        for name,p in zip(s.PACKETS,self.packets):
            s.write_exclusive(self.inp/name,s.render(p))


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
            f.cli(self,"claim-acquisition",acq,"P43_ACQUISITION_CLAIMED")
            f.cli(self,"claim-acquisition",acq,"P43_REFUSED")
            receipt=f.inp/f"acquisition.{acq}.lock"
            self.assertEqual(s.parse(receipt.read_bytes())["acquisition_commit"],acq)
            f.stage_packets()
            actions_file=f.inp/"actions.json"
            original_actions=actions_file.read_bytes()
            for case in ("missing_code","wrong_code","non_independent","blocked_comparator"):
                with self.subTest(case=case):
                    altered=s.parse(original_actions)
                    legs=altered["records"][f.blocked]
                    if case=="missing_code":
                        del legs["stock"]["reason_code"]
                    elif case=="wrong_code":
                        legs["stock"]["reason_code"]="unsupported"
                    elif case=="non_independent":
                        legs["stock"]["reason_sources"]=[AUTH[0],AUTH[0]]
                    else:
                        legs["IWM"].update(status="blocked",reason_code=s.NONCASH_SKIP,reason_sources=AUTH)
                    actions_file.write_bytes(s.render(altered))
                    bad=f.commit(s.APPROVAL,f.validation(acq))
                    f.cli(self,"validate-inputs",bad,"P43_ACTION_COVERAGE")
                    f.checkout(acq)
            actions_file.write_bytes(original_actions)

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
            self.assertEqual(result["skipped_by_reason"],{s.NONCASH_SKIP:1})
            self.assertEqual(result["judged"]["absolute"]["n"],1)
            self.assertEqual(result["sleeves"]["placed"],1)
            self.assertEqual(result["no_trade_unaffordable"],0)
            self.assertEqual(result["idle_zero_mean"],result["judged"]["absolute"]["mean"])
            f.cli(self,"go",go,"P43_CONSUMED")

    def test_real_cli_acquisition_git_refusals(self):
        flag="claim-acquisition"
        with TemporaryDirectory() as d:
            f=SyntheticRepo(Path(d))
            needle=f.acquisition()
            for mode,ref in (("claim-acquisition",None),("validate-inputs",None),("go",None),("self-test",f.freeze)):
                rejection=f.process(mode,ref)
                self.assertEqual(rejection.returncode,2)
                self.assertIn("real modes require --approval-commit; synthetic modes reject it",rejection.stderr)
            f.cli(self,flag,"invalid","P43_APPROVAL")
            f.cli(self,flag,f.freeze,"P43_APPROVAL")
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
                ("research_rig/TRIAL_LEDGER.md",b"| 178 | changed |\n","P43_LEDGER_QUEUE"),
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
        job=dict(ledger=178,acquisition_commit=commit,freeze_commit="b"*40,
                 freeze_sha256="c"*64,docket_sha256=c["docket_sha256"])
        proof=dict(docket_sha256=c["docket_sha256"],trials=c["calibration"]["trials"],eligible=len(ordered),
                   edges=c["calibration"]["edges"],shares=[0])
        blobs={s.CONFIG:(s.ROOT/s.CONFIG).read_bytes(),s.CALIBRATION:s.render(proof),s.ENGINE:b"dummy"}
        with TemporaryDirectory() as d,redirect_stdout(StringIO()):
            tmp=Path(d)
            inp,run=tmp/"inp",tmp/"run"
            inp.mkdir(mode=0o700)
            run.mkdir(mode=0o700)
            auth=Mock(side_effect=lambda *_:(job.copy(),blobs))
            returns=Mock(side_effect=lambda *_:{"dummy":True})
            with patch.multiple(s,INPUT=inp,RUN=run,authorize=auth,resources=Mock(),
                                local_schedule=Mock(return_value=(ordered,days,c)),engine=Mock(),
                                prepared=Mock(),report=returns):
                s.approved(commit,"acquire")
                with self.assertRaises(FileExistsError):
                    s.approved(commit,"acquire")
                receipt=inp/f"acquisition.{commit}.lock"
                job.update(approval_commit="d"*40,acquisition_receipt_sha256=sha256(receipt.read_bytes()).hexdigest())
                for name in s.PACKETS:
                    s.write_exclusive(inp/name,b"{}")
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
            with self.subTest(change=change), self.assertRaises(s.Refused):
                s.prepared(*p)

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
        for change,code in (("raw_double","RAW_BASIS_CHANGE"),("asof_scale","ASOF_BASIS_CHANGE"),
                            ("padding","PADDED_TAPE")):
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
            else:
                for k in ("raw","all","filing_all"):
                    bar[k]=[r for r in bar[k] if r["t"][:10] in {x.isoformat() for x in (e.early,e.entry,e.exit)}]
            with self.subTest(change=change),self.assertRaisesRegex(s.Refused,code):
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
