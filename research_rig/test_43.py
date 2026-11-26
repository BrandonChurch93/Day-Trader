"""Executable synthetic controls for Plan 43. No vendor inputs are opened."""
import copy
from contextlib import redirect_stdout
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import score_43 as s

AUTH = ["https://issuer.example/filing","https://exchange.example/notice"]


def cfg():
    return s.config((s.ROOT/s.CONFIG).read_bytes())


def condition():
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


class Plan43(unittest.TestCase):
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
