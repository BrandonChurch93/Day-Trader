"""Artificial CLI and exact arithmetic witnesses for Plan 60."""
from decimal import Decimal
from fractions import Fraction
import gzip
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import score_60 as s
from test_43 import SyntheticRepo

BOOT="""
import runpy,sys
from pathlib import Path
from hashlib import sha256
root,data=map(Path,sys.argv[1:3])
g=runpy.run_path(str(root/"research_rig/score_60.py"))["main"].__globals__
g.update(ROOT=root,DATA=data,INPUT=data/"plan43_successor_inputs",RUN=data/"replay_60",
         VENDOR=data/"plan60_vendor_actions",PRICE_BASE=sys.argv[3],PRICE_PRIOR=sys.argv[4])
p=g["p"]
changes=dict(ROOT=root,DATA=data,INPUT=g["INPUT"],DOCKET=data/"docket.jsonl",COLLECTOR=data/"collector.py",
             COLLECTOR_SHA256=sha256((data/"collector.py").read_bytes()).hexdigest())
p.__dict__.update(changes)
p.git.__globals__.update(changes)
if sys.argv[5]=="--validate-inputs":
    def forbidden(*a,**k):
        raise AssertionError("validation must not compute returns")
    g.update(fill=forbidden,score=forbidden)
sys.argv=["score_60.py",*sys.argv[5:]]
raise SystemExit(g["main"]())
"""


class Fixture:
    def __init__(self,base,scenarios=False,frozen=True,spy_bad=False,wire_fault=None,alias_gap=False):
        self.f=f=SyntheticRepo(base,with_blocked=True,modeled_count=10 if scenarios else 1)
        rec=f.packets[1]["records"]
        acc=[a for a in rec if a!=f.blocked]
        if scenarios:
            def zero(i,leg,j):
                for view in s.p.VIEWS:
                    rec[acc[i]][leg][view][j]["v"]=0
            for view in s.p.VIEWS:
                rec[acc[1]]["stock"][view].pop(1)
            for view in s.p.VIEWS:
                for row in rec[acc[2]]["stock"][view][:5]:
                    row["v"]=1
            zero(3,"stock",6)
            for j in (10,24,25):
                zero(4,"stock",j)
            for j in range(24,30):
                zero(5,"stock",j)
            for i in range(len(acc)):
                zero(i,"IWM",25)
            zero(7,"stock",24)
            for j in range(24,29):
                zero(9,"stock",j)
            for view in ("all","filing_all"):
                for row in rec[acc[8]]["stock"][view]:
                    for k in "ohlc":
                        row[k]=Decimal(row[k])/2
        acq=f.commit(s.p.ACQUISITION,f.acquisition())
        claimed=f.process("claim-acquisition",acq)
        if claimed.returncode:
            raise AssertionError(claimed.stderr)
        f.stage_packets(acq)
        self.prior=f.commit(s.p.APPROVAL,f.validation(acq))
        f.put(s.p.BASIS,(s.ROOT/s.p.BASIS).read_bytes())
        self.price_base=f.commit()
        self.vendor=f.data/"plan60_vendor_actions"
        self.vendor.mkdir(mode=0o700)
        self.run=f.data/"replay_60"
        self.run.mkdir(mode=0o700)
        native=self.vendor/"native"
        native.mkdir(mode=0o700)
        meta=dict(docket_sha256=f.dp,identities_sha256=sha256((f.inp/"identities.json").read_bytes()).hexdigest(),
                  bars_sha256=sha256((f.inp/"bars.json").read_bytes()).hexdigest())
        base_fields=dict(version=2,custodian=s.p.config((f.root/s.p.CONFIG).read_bytes())["custodian"],
                         endpoint=s.VENDOR_ENDPOINT,adoption=meta)
        rows={}
        streams={}
        retries=[]
        stamp="2026-11-26T00:00:00Z"
        for i,a in enumerate(acc):
            base=rec[a]["stock"]
            through=s.p.d(base["end"])+s.timedelta(days=90)
            ex=f.packets[2]["records"][a]["stock"]["items"][0]["ex"]
            rows[a]={}
            for leg,ident in f.packets[0]["records"][a].items():
                items=[]
                if leg=="stock":
                    items=[dict(id=f"cash{i}",type="cash",ex=ex,
                                cash_usd="2" if scenarios and i==6 else "1",factor=None)]
                    if scenarios and i==8:
                        items.append(dict(id="tail",type="split",ex=str(through-s.timedelta(days=80)),new="1.5",old="0.75"))
                    if scenarios and i==9:
                        items.append(dict(id="unsupported",type="unsupported",ex=ex,vendor_type="spin_offs"))
                    if alias_gap:
                        items.append(dict(id="rename",type="nonprice",ex=ex,vendor_type="name_changes"))
                if leg=="SPY" and spy_bad:
                    items.append(dict(id="spy_bad",type="cash",ex=ex,cash_usd="1",factor=None))
                key=ident["identity"]
                ticker=ident["ticker"]
                if ticker not in streams:
                    wire={}
                    for item in items:
                        fields=dict(id=item["id"],symbol=ticker,cusip=key,process_date=item["ex"],ex_date=item["ex"])
                        if item["type"]=="cash":
                            kind="cash_dividends"
                            fields.update(rate=int(item["cash_usd"]),currency="USD",foreign=False,special=True)
                            # Action discovered by process-date lookback, then projected by ex-date.
                            fields["process_date"]=str(s.p.d(item["ex"])-s.timedelta(days=45))
                        elif item["type"]=="split":
                            kind="forward_splits"
                            fields.update(new_rate=Decimal(item["new"]),old_rate=Decimal(item["old"]))
                        elif item["type"]=="nonprice":
                            kind=item["vendor_type"]
                            fields.pop("ex_date")
                            fields.update(old_symbol=ticker,old_cusip=key,new_symbol="AFTER",new_cusip=key)
                        else:
                            kind=item["vendor_type"]
                            fields.update(source_symbol=ticker,source_cusip=key,new_symbol="OTHER")
                        wire.setdefault(kind,[]).append(fields)
                    terminal="broken" if wire_fault=="pagination" and leg=="stock" else None
                    rawbody=s.p.render(dict(corporate_actions={} if wire_fault=="empty" else wire,next_page_token=terminal))
                    body=gzip.compress(rawbody,mtime=0)
                    name=f"{ticker}.json.gz"
                    s.p.write_exclusive(native/name,body)
                    digest=sha256(rawbody).hexdigest()
                    first=s.p.d(base["start"])-s.timedelta(days=90)
                    pages=[dict(file=name,status=200,sha256=sha256(body).hexdigest(),bytes=len(body),page_token=None,
                                body_sha256=digest,body_bytes=len(rawbody),next_page_token=terminal)]
                    if ticker=="IWM":
                        # Exercise a real two-page chain even when its action lists are empty.
                        name2=f"{ticker}_first.json"
                        firstbody=s.p.render(dict(corporate_actions={},next_page_token="fixture-next"))
                        s.p.write_exclusive(native/name2,firstbody)
                        pages[0]["page_token"]="wrong-next" if wire_fault=="wrong_token" else "fixture-next"
                        firsthash=sha256(firstbody).hexdigest()
                        pages.insert(0,dict(file=name2,status=200,sha256=firsthash,bytes=len(firstbody),
                                            body_sha256=firsthash,body_bytes=len(firstbody),page_token=None,
                                            next_page_token="fixture-next"))
                    params=dict(symbols=ticker,start=str(first),end=str(through),limit="1000",sort="asc",
                                data_quality="complete",region="us")
                    for j,paged in enumerate(pages):
                        token=paged["page_token"]
                        outgoing=params if token is None else params|dict(page_token=token)
                        stamp_fields=dict(identity=key,ticker=ticker,page=j,params=outgoing,fetched_utc=stamp)
                        paged.update(stamp_fields,attempt=1)
                        if ticker=="IWM" and j==0:
                            retries.append(stamp_fields|dict(attempt=1,page_token=None,status=429,curl_rc=0,
                                           body_sha256=sha256(b"").hexdigest(),body_bytes=0))
                            paged["attempt"]=2
                    streams[ticker]=(digest,pages)
                digest,_=streams[ticker]
                rows[a][leg]=dict(identity=key,ticker=ticker,views=dict(all=key,filing_all=key),
                                  start=base["start"],through=str(through),complete=not (alias_gap and leg=="stock"),
                                  items=sorted((item|dict(source_sha256=digest) for item in items),
                                               key=lambda x:(x["ex"],x["id"])))
        entries=[page for _,pages in streams.values() for page in pages]
        index=s.p.render(dict(version="plan60_vendor_action_index_v2",ledger=199,endpoint=s.VENDOR_ENDPOINT,
                              capture_utc=stamp,total_pages=len(entries),total_retries_and_errors=len(retries),
                              total_http_requests=len(entries)+len(retries),entries=entries,retries_and_errors=retries))
        s.p.write_exclusive(self.vendor/s.VENDOR_INDEX,index)
        self.index_pin=sha256(index).hexdigest()
        vendor=s.p.render(base_fields|dict(native_index_sha256=self.index_pin,records=rows))
        s.p.write_exclusive(self.vendor/s.VENDOR_NAME,vendor)
        self.vendor_pin=sha256(vendor).hexdigest()
        suffix=(s.ROOT/s.p.CONFIG).read_bytes().split(b"\nreplay_60_plan:\n",1)[1]
        f.put(s.p.CONFIG,(f.root/s.p.CONFIG).read_bytes()+b"\nreplay_60_plan:\n"+suffix)
        cfg=s.config((f.root/s.p.CONFIG).read_bytes())
        proof=dict(docket_sha256=f.dp,trials=cfg["calibration"]["trials"],eligible=len(acc)+1,
                   edges=cfg["calibration"]["edges"],shares=[0]*4)
        f.put(s.PROOF,s.p.render(dict(plan=60,ledger=199,queue=99,placed_floor=cfg["marks"]["placed"],
                                     cases={str(x):proof for x in cfg["placement_cases"]})))
        for n in (s.PLAN,s.ADAPTER,"research_rig/score_60.py","research_rig/test_60.py"):
            blob=(s.ROOT/n).read_bytes()
            f.put(n,blob.replace(b"Status DRAFT.",b"Status FROZEN.") if n==s.PLAN and frozen else blob)
        for n,num in (("research_rig/TRIAL_LEDGER.md",199),("docs/QUEUE.md",99)):
            f.put(n,(f.root/n).read_bytes()+f"| {num} | {s.PLAN} | synthetic |\n".encode())
        pins=s.p.render({n:sha256((f.root/n).read_bytes()).hexdigest() for n in s.SOURCES})
        f.put(s.PINS,pins)
        freeze=f.commit()
        prior=sha256((f.root/s.p.APPROVAL).read_bytes()).hexdigest()
        adoption=(f"Approved by the lead: plan 60 ledger 199, adopt sealed Plan 43 prices from validation commit "
                  f"{self.prior}, prior approval SHA-256 {prior}, freeze commit {freeze}, "
                  f"freeze SHA-256 {sha256(pins).hexdigest()}, no price acquisition.\n").encode()
        self.adopt=f.commit(s.ADOPT,adoption)
        approval=(f"Approved by the lead: plan 60 ledger 199, validation only, adoption commit {self.adopt}, "
                  f"adoption approval SHA-256 {sha256(adoption).hexdigest()}, vendor actions SHA-256 {self.vendor_pin}, "
                  f"vendor native index SHA-256 {self.index_pin}.\n").encode()
        self.val=f.commit(s.VALID,approval)

    def cli(self,flag,commit):
        return subprocess.run([sys.executable,"-I","-B","-c",BOOT,str(self.f.root),str(self.f.data),
                               self.price_base,self.prior,"--"+flag,"--approval-commit",commit],
                               capture_output=True,text=True,timeout=180)

    def go(self,pin=None):
        if pin is None:
            pin=sha256((self.run/f"validation.{self.val}.json").read_bytes()).hexdigest()
        return self.f.commit(s.GO,(f"Approved by the lead: plan 60 ledger 199, one scored run, validation approval "
                                   f"commit {self.val}, validation receipt SHA-256 {pin}.\n").encode())


class Plan60(unittest.TestCase):
    def test_cli_tape_vendor_and_one_go(self):
        with TemporaryDirectory() as d:
            f=Fixture(Path(d),scenarios=True)
            proc=f.cli("validate-inputs",f.val)
            self.assertEqual((proc.returncode,proc.stderr),(0,""))
            payload,signal=proc.stdout.rsplit("\n",2)[:2]
            self.assertEqual(signal,"P60_VALIDATED")
            summary=json.loads(payload)
            reasons=dict(noncash_skip=1,outside_padding_volume=1,outside_dollar_volume=1,unfilled_entry=1,
                         refused_no_exit=1,refused_vendor_basis=2,unfilled_capital=0,unfilled_iwm_clock=1,
                         unfilled_iwm_capital=0,eligible_pair=3)
            self.assertEqual(summary["reason_counts"],reasons)
            self.assertEqual(summary["by_year"]["2024"]["reason_counts"],reasons)
            self.assertGreater(summary["inside_unavailable_sessions"],0)
            self.assertEqual(summary["post_window_action_explains_legs"],1)
            self.assertEqual(summary["vendor_only_in_window_actions"],2)
            self.assertEqual(summary["filing_only_in_window_actions"],1)
            self.assertFalse((f.run/"score.lock").exists())
            bad=f.cli("go",f.go("0"*64))
            self.assertEqual((bad.returncode,bad.stderr),(2,"P43_P60_VALIDATION_RECEIPT\n"))
            f.f.checkout(f.val)
            go=f.go()
            ok=f.cli("go",go)
            self.assertEqual((ok.returncode,ok.stdout,ok.stderr),(0,"P60_SCORED_ONCE\n",""))
            twice=f.cli("go",go)
            self.assertEqual((twice.returncode,twice.stderr),(2,"P43_CONSUMED\n"))
            result=json.loads((f.run/"result.json").read_bytes())["outcome"]
            self.assertEqual(result["shown"]["including_vendor_basis_refusals"]["n"],6)
            self.assertEqual(result["shown"]["paired_iwm_including_vendor_basis_refusals"]["n"],5)
            self.assertEqual(result["shown"]["paired_spy"]["n"],4)  # IWM-only clock loss does not suppress SPY.

    def test_cli_draft_and_vendor_tamper_refused(self):
        for frozen,reason in ((False,"P43_P60_FREEZE"),(True,"P43_PIN")):
            with TemporaryDirectory() as d:
                f=Fixture(Path(d),frozen=frozen)
                if frozen:
                    (f.vendor/"native/TEST.json.gz").write_bytes(b"tampered")
                check=f.cli("validate-inputs",f.val)
                self.assertEqual((check.returncode,check.stderr),(2,reason+"\n"))
                self.assertFalse((f.run/f"validation.{f.val}.json").exists())

    def test_cli_native_projection_and_pagination_fail_closed(self):
        for fault,reason in (("empty","P60_VENDOR_PROJECTION"),("pagination","P60_VENDOR_PAGINATION"),
                             ("wrong_token","P60_VENDOR_PAGE")):
            with TemporaryDirectory() as d:
                f=Fixture(Path(d),wire_fault=fault)
                got=f.cli("validate-inputs",f.val)
                self.assertEqual((got.returncode,got.stderr),(2,"P43_"+reason+"\n"))
                self.assertFalse((f.run/f"validation.{f.val}.json").exists())

    def test_cli_incomplete_alias_coverage_refuses_only_affected_event(self):
        with TemporaryDirectory() as d:
            f=Fixture(Path(d),alias_gap=True)
            got=f.cli("validate-inputs",f.val)
            self.assertEqual((got.returncode,got.stderr),(0,""))
            summary=json.loads(got.stdout.rsplit("\n",2)[0])
            self.assertEqual(summary["reason_counts"]["refused_vendor_basis"],1)
            self.assertEqual(summary["vendor_basis_refusal_reasons"],{"vendor_mapping_or_coverage":1})

    def test_cli_spy_only_basis_failure_keeps_judged_pair(self):
        with TemporaryDirectory() as d:
            f=Fixture(Path(d),spy_bad=True)
            got=f.cli("validate-inputs",f.val)
            self.assertEqual((got.returncode,got.stderr),(0,""))
            summary=json.loads(got.stdout.rsplit("\n",2)[0])
            self.assertEqual(summary["reason_counts"]["eligible_pair"],1)
            self.assertEqual(summary["reason_counts"]["refused_vendor_basis"],0)
            self.assertEqual(summary["shown_spy_basis_omissions"],1)
            out=f.cli("go",f.go())
            self.assertEqual((out.returncode,out.stdout,out.stderr),(0,"P60_SCORED_ONCE\n",""))
            outcome=json.loads((f.run/"result.json").read_bytes())["outcome"]
            self.assertNotIn("paired_spy",outcome["shown"])

    def test_missing_vendor_cash_factor_cannot_reset_fit(self):
        days=[s.p.d("2024-06-01")+s.timedelta(days=i) for i in range(5)]
        b=lambda n,v:SimpleNamespace(v=v,c=n,flat_key=(n,n,n,n))
        raw={d:b(10,1) for d in days}
        raw[days[1]]=b(10,0)
        adj={d:b(10 if d>=days[2] else 9,1) for d in days}
        items=[(days[2],"cash",Fraction(1),None)]
        compare=lambda x:s.vendor_compare(raw,adj,adj,days,x,Fraction(1,200))[0]
        self.assertEqual(compare(items),"vendor_cash_reference_missing_or_invalid")
        self.assertIsNone(compare([(days[2],"cash",Fraction(1),Fraction(9,10))]))

    def test_first_padded_session_supported_action_needs_no_backward_factor(self):
        days=[s.p.d("2024-06-03")+s.timedelta(days=i) for i in range(5)]
        bar=SimpleNamespace(v=1,c=10,flat_key=(10,10,10,10))
        view={day:bar for day in days}
        for kind,value,factor in (("cash",Fraction(1),None),("split",Fraction(2),Fraction(1,2))):
            with self.subTest(kind=kind):
                self.assertEqual(s.vendor_compare(view,view,view,days,[(days[0],kind,value,factor)],
                                                  Fraction(1,200)),(None,False,False))

    def test_first_padded_session_unsupported_action_fails_leg(self):
        days=[s.p.d("2024-06-03")+s.timedelta(days=i) for i in range(5)]
        bar=SimpleNamespace(v=1,c=10,flat_key=(10,10,10,10))
        view={day:bar for day in days}
        result=s.vendor_compare(view,view,view,days,[(days[0],"unsupported","spin_offs",None)],Fraction(1,200))
        self.assertEqual(result,("unsupported_vendor_action",False,False))

    def test_joint_multiplier_and_no_refit_after_gap(self):
        days=[s.p.d("2024-06-01")+s.timedelta(days=i) for i in range(8)]
        b=lambda x:SimpleNamespace(v=1,c=x,flat_key=(x,x,x,x))
        raw={d:b(20) for d in days if d!=days[4]}
        all_view={d:b(10) for d in raw}
        filing={d:b(10 if d<days[4] else Fraction(1002,100)) for d in raw}
        self.assertEqual(s.vendor_compare(raw,all_view,filing,days,[],Fraction(500001,10**8))[0],
                         "vendor_basis_mismatch")
        self.assertIsNone(s.vendor_compare(raw,all_view,all_view,days,[],Fraction(500001,10**8))[0])

    def test_exact_liquidity_cutoff_and_delayed_open(self):
        ds=[s.p.d("2024-06-01")+s.timedelta(days=i) for i in range(15)]
        e=SimpleNamespace(early=ds[5],entry=ds[6],exit=ds[9],declared=1)
        b=lambda n,v:SimpleNamespace(v=v,o=n,c=n+1)
        raw={d:b(9,10000) for d in ds}
        raw[ds[9]],raw[ds[10]],raw[ds[11]]=b(9,0),b(12,0),b(18,1)
        cfg=s.config((s.ROOT/s.p.CONFIG).read_bytes())
        self.assertEqual(s.event_execution(e,raw,ds,cfg),(None,ds[11]))
        verified=[(ds[11],"special",2,ds[12],ds[12])]
        t=s.fill(e,(raw,verified,ds[11]),ds[6],ds[11],500,5,cfg)
        self.assertEqual(t.proceeds,55*(18-s.p.fee(18,5,cfg)))
        self.assertEqual(t.cash,[(ds[12],110)])
        del raw[ds[6]]
        self.assertEqual(s.event_execution(e,raw,ds,cfg),("unfilled_entry",None))


if __name__=="__main__":
    unittest.main()
