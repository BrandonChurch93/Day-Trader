"""Synthetic only. No production runner mode, fixed input directory, or market device."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name,HERE/(name+".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


S = module("score_36")
C = module("common_36")
CLOCK = (HERE/"calendar_36.json").read_bytes()
DAY, INDEX, CLOSE = C.calendar(S.parse(CLOCK))
SOURCE = "https://example.invalid/synthetic"


def fake_roster(d="2024-06-28"):
    return dict(id=d+":100:a",cik="100",class_key="a",ticker="FAKE",batch_date=d,
                buys=[dict(accession=f"000000000{i}-24-000001",owner_cik=str(i),
                           officer=i==1,director=i==2,trade_date=d,accepted_utc=d+"T20:20:00Z",
                           public_utc=d+"T20:20:01Z",shares=10,reported_price=50,
                           venue="open_market",plan="no_indication") for i in (1,2)],
                disposition="confirmed",security="synthetic:100",
                cap=dict(shares=1000000,asof=d,accepted_utc=d+"T20:20:00Z",source=SOURCE),
                routine="unclassified",provenance="a"*64)


def fixture(d="2024-06-28"):
    r = fake_roster(d)
    rows = C.parse_roster([r],DAY,INDEX)
    i,s = rows[0]["start"],r["security"]
    tape = {day:(50,51,49,50,100000) for day in DAY[i-20:i+22]}
    tape[DAY[i+20]] = (56,56,54,55,100001)
    fund = {day:(100,101,99,100,100000) for day in DAY[i:i+22]}
    coverage = {x:[(DAY[i],DAY[i+21],"complete")] for x in (s,"IWM")}
    q = {(s,DAY[i]):(.001,(49.95,50.05,5000,5000),240*C.NS)}
    return rows,DAY,INDEX,CLOSE,DAY[i+21],{s:tape,"IWM":fund},q,coverage,{}


class EngineTests(unittest.TestCase):
    def test_canonical_packet(self):
        roster = fake_roster()
        s = roster["security"]
        i = INDEX["2024-07-01"]
        ids = [dict(security=a,symbol=b,**{"from":DAY[i-20],"through":DAY[i+21]},source=SOURCE)
               for a,b in ((s,"FAKE"),("IWM","IWM"))]
        coverage = [dict(security=a,**{"from":DAY[i],"through":DAY[i+21]},status="complete",source=SOURCE)
                    for a in (s,"IWM")]
        b = [dict(security=a,symbol=t,date=d,t=d+"T05:00:00Z",o=50,h=55,l=45,c=55 if a==s and d==DAY[i+20] else 50,v=100000)
             for a,t,lookback in ((s,"FAKE",20),("IWM","IWM",0)) for d in DAY[i-lookback:i+22]]
        q = [dict(security=s,date=DAY[i],t=DAY[i]+f"T{h}:{m}:30Z",bid=49.95,ask=50.05,bid_size=1000,ask_size=1000)
             for h,m in (("19","54"),("19","55"),("19","56"),("19","57"),("19","58"))]
        args = ({"bar_through":DAY[i+21]},S.parse(CLOCK),[roster],ids,b,q,{"coverage":coverage,"actions":[]})
        data = C.load(*args)
        self.assertEqual(C.assess(data),{"paired_ready":1})
        self.assertAlmostEqual(C.observation(data[0][0],data)["excess"],55*.9985/(50*1.0015)-1)
        with self.assertRaisesRegex(C.Invalid,"FUND_SCOPE"):
            C.load(*args[:4],b+[dict(b[-1],date=DAY[i-1],t=DAY[i-1]+"T05:00:00Z")],*args[5:])
        with self.assertRaisesRegex(C.Invalid,"QUOTE_CLOCK"):
            C.load(*args[:5],q+[dict(q[-1],t=DAY[i]+"T20:00:00Z")],args[-1])

    def test_clock_and_early_close(self):
        self.assertEqual(CLOSE["2024-11-29"],C.stamp("2024-11-29T18:00:00Z")[0])
        r = fake_roster("2024-11-29")
        rows = C.parse_roster([r],DAY,INDEX)
        self.assertEqual(DAY[rows[0]["start"]],"2024-12-02")
        r["buys"][1]["public_utc"]="2024-12-02T19:30:00Z"
        with self.assertRaisesRegex(C.Invalid,"BUY_CLOCK"):
            C.parse_roster([r],DAY,INDEX)

    def test_distinct_owner_and_cooldown(self):
        r = fake_roster()
        r["buys"][1]["owner_cik"]="1"
        with self.assertRaisesRegex(C.Invalid,"PAIR"):
            C.parse_roster([r],DAY,INDEX)
        r = fake_roster()
        r["buys"][1]["accession"]=r["buys"][0]["accession"]
        self.assertEqual(len(C.parse_roster([r],DAY,INDEX)),1)
        with self.assertRaisesRegex(C.Invalid,"COOLDOWN"):
            C.parse_roster([r,fake_roster("2024-07-03")],DAY,INDEX)

    def test_quote_ties_expiry_and_duration(self):
        n = C.NS
        q = (49.95,50.05,1000,1000)
        bad = (50,50,1000,1000)
        updates = [(t*n,q) for t in (0,50,100,150,200,250)]
        self.assertAlmostEqual(C.measure(updates,300*n)[0],.001)
        self.assertIsNone(C.measure(updates+[(250*n,bad)],300*n))
        self.assertIsNotNone(C.measure(updates+[(250*n,bad),(250*n,q)],300*n))
        self.assertIsNone(C.measure(updates,310*n))
        self.assertIsNone(C.measure(updates[3:],300*n))

    def test_fills_missingness_and_stress(self):
        d = fixture()
        r,s,i = d[0][0],d[0][0]["security"],d[0][0]["start"]
        o = C.observation(r,d)
        self.assertEqual(o["status"],"paired")
        self.assertAlmostEqual(o["excess"],55*.9985/(50*1.0015)-1)
        with patch.object(C,"payoff",side_effect=AssertionError):
            self.assertEqual(C.assess(d),{"paired_ready":1})
        self.assertEqual(C.observation(r,d[:4]+(DAY[i+10],)+d[5:])["status"],"incomplete")
        z = C.evaluate(*(d[:4]+(DAY[i+10],)+d[5:]))
        self.assertEqual(len(z["marks"]),9)
        self.assertEqual(z["verdict"],"INCONCLUSIVE")
        self.assertFalse(z["marks"]["missing_exits"])
        del d[5][s][DAY[i+20]]
        self.assertEqual(C.assess(d),{"stock_exit_unresolved":1})
        self.assertEqual(C.observation(r,d)["stress_fund"],0)
        self.assertEqual(C.evaluate(*d)["paired"]["stress"],-1)
        del d[5]["IWM"][DAY[i+20]]
        self.assertIsNone(C.evaluate(*d)["paired"]["stress"])
        d[6].clear()
        self.assertEqual(C.observation(r,d)["status"],"quote_missing")

    def test_dividend_split_and_terminal_settlement(self):
        d = fixture()
        r,s,i = d[0][0],d[0][0]["security"],d[0][0]["start"]
        def action(k,amount,target=None):
            return {"kind":k,"amount":amount,"target":target}
        d[8][s,DAY[i]] = [action("cash",100)]
        d[8][s,DAY[i+1]] = [action("split",2),action("cash",1)]
        d[8][s,DAY[i+2]] = [action("settle_cash",28)]
        self.assertEqual(C.observation(r,d)["per_share"],(58,0,0,i+2))
        d[8][s,DAY[i+2]] = [action("cash",2),action("settle_stock",.5,"SYNTH")]
        d[5]["SYNTH"] = {DAY[i+2]:(50,51,49,50,100000)}
        p = C.observation(r,d)["per_share"]
        self.assertEqual(p,(6,50,.075,i+2))
        d[8][s,DAY[i+2]] = [action("stock_distribution",.1,s),action("settle_cash",25)]
        self.assertAlmostEqual(C.observation(r,d)["per_share"][0],57)
        d[8][s,DAY[i+1]].append(action("stock_distribution",.5,"SYNTH"))
        b,q = C.planned([r],DAY,INDEX,d[4],d[8])
        self.assertIn(("SYNTH",DAY[i+2]),q)
        self.assertIn(i+2,b["SYNTH"])
        d[7].clear()
        self.assertEqual(C.observation(r,d)["status"],"stock_exit_unresolved")

    def test_bootstrap(self):
        rows = [(None,{"start":i,"excess":.004}) for i,d in enumerate(DAY) if d[:7] in C.MONTHS]
        lower,se = C.blocks(rows,DAY)
        self.assertAlmostEqual(lower,.004)
        self.assertLess(se,1e-15)


class GateTests(unittest.TestCase):
    def test_bad_approval_or_dirty_repo(self):
        x = "a"*40
        pins = ["b"*64]*3
        with patch.object(S,"git",side_effect=[SimpleNamespace(stdout=x.encode()),SimpleNamespace(stdout=b"dirty")]):
            with self.assertRaisesRegex(S.Refused,"APPROVAL"):
                S.authorize(x,*pins)
        with patch.object(S,"git",side_effect=[SimpleNamespace(stdout=x.encode()),SimpleNamespace(stdout=b"")]), \
             patch.object(S,"tree",return_value=b"not approval"):
            with self.assertRaisesRegex(S.Refused,"APPROVAL"):
                S.authorize(x,*pins)

    def test_no_score_validate_and_private_pins(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t)
            src,out = path/"inputs",path/"output"
            src.mkdir(mode=0o700); out.mkdir(mode=0o700)
            r = fake_roster()
            r["disposition"] = "identity_unknown"
            r["security"] = None
            payloads = {"roster.jsonl":S.encode(r).replace(b"\n",b"")+b"\n","identities.jsonl":b"",
                        "bars.jsonl":b"","quotes.jsonl":b"","actions.json":b'{"coverage":[],"actions":[]}'}
            pins = {name:S.sha256(b).hexdigest() for name,b in payloads.items()}
            manifest = dict(schema=1,plan=36,vendor="Alpaca",feed="sip",adjustment="raw",frequency="1Day",
                            filed_from=C.FIRST,filed_through=C.LAST,bar_from=C.BAR_FIRST,bar_through=C.BAR_MAX,
                            collected_utc="2026-11-25T17:30:00Z",files=pins)
            payloads["manifest.json"] = S.encode(manifest)
            for name,b in payloads.items():
                p = src/name
                p.write_bytes(b); p.chmod(0o600)
            args = (src,S.sha256(payloads["manifest.json"]).hexdigest(),pins["actions.json"],C,CLOCK)
            with patch.object(C,"payoff",side_effect=AssertionError),patch.object(C,"evaluate",side_effect=AssertionError):
                self.assertEqual(C.assess(S.load_inputs(*args)),{"identity_unknown":1})
            self.assertFalse(list(out.iterdir()))
            (src/"bars.jsonl").write_bytes(b"oops")
            with self.assertRaisesRegex(S.Refused,"PIN"):
                S.load_inputs(*args)
            with self.assertRaisesRegex(S.Refused,"JSON_DUPLICATE"):
                S.parse(b'{"x":1,"x":2}')

    def test_fsync_order_and_no_retry_after_claim(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            seen = []
            sync = S.os.fsync
            def hooked(fd):
                seen.append("fsync")
                sync(fd)
            def score():
                self.assertEqual(seen,["fsync","fsync"])
                self.assertTrue((out/S.LOCK).is_file())
                seen.append("score")
                return {"ok":True}
            with patch.object(S.os,"fsync",side_effect=hooked):
                S.once(out,{},(),score)
            self.assertEqual(seen,["fsync","fsync","score","fsync","fsync"])
            with self.assertRaisesRegex(S.Refused,"CONSUMED"):
                S.once(out,{},(),score)
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            def fail():
                raise ArithmeticError
            with self.assertRaises(ArithmeticError):
                S.once(out,{},(),fail)
            self.assertTrue((out/S.LOCK).exists())
            self.assertFalse((out/S.RESULT).exists())
            with self.assertRaisesRegex(S.Refused,"CONSUMED"):
                S.once(out,{},(),fail)


if __name__=="__main__":
    unittest.main()
