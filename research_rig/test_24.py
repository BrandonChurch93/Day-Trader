"""Invented fixtures and planted calibration. No imported tape/catalogue."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from random import Random
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

try:
    from . import common_24 as C, score_24 as S
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    import common_24 as C
    import score_24 as S

candidate = Path(__file__).with_name("config_24_candidate.yaml")
P = S.policy((candidate if candidate.is_file() else S.REPO/"config/thresholds.yaml").read_bytes())


class Toy:
    def __init__(self,p,n=8):
        self.p = p
        self.pairs = tuple(C.Pair(i+1,f"p{i}",f"s{i}",p["start"]-300,p["end"]+1) for i in range(n))
        self.rates,self.bars,self.pay,self.peaks = {},{},{},{}
        self.terminal_opens = {}
        self.clock_block = set()

    def pool(self,t,only=None):
        return tuple(a for a in self.pairs if only is None or a.coin in only)

    def signal(self,a,t):
        return self.rates.get((a,t),.24 if a.coin<=self.p["slots"] else 0.)

    def entry_covered(self,a,t):
        return (a,t) not in self.clock_block

    def decision_traded(self,a,t):
        return self.bar(a,t-2) is not None

    def bar(self,a,t):
        return self.bars.get((a,t),C.Bar(100,100,100,100,100,100))

    def payment(self,a,t):
        return self.pay.get((a,t),(None,0))

    def closing_open(self,a,t):
        if a in self.terminal_opens:
            return self.terminal_opens[a]
        b = self.bar(a,t)
        return (b.spot_open,b.perp_open) if b else None

    def payment_missing(self,a,t):
        return (a,t) in self.pay and self.pay[a,t]==(None,0)

    def peak(self,a):
        return self.peaks.get(a,0.)


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.p = dict(P,end=P["start"]+72,slots=1,draws=10)
        self.tape = Toy(self.p)
        self.a = self.tape.pairs[0]
        self.t = self.p["start"]

    def test_thresholds_hysteresis_fill_lag_no_replacement(self):
        a,b,*_ = self.tape.pairs
        self.tape.rates.update({(a,self.t):.20,(a,self.t+24):.0501,(b,self.t+24):.35,
                                (a,self.t+48):.05,(b,self.t+48):.35})
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertEqual(list(r["schedule"][1].values()),[1,0,1])
        self.assertEqual(r["coin_hours"],71)
        self.tape.bars[a,self.t+1] = None
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertEqual(r["schedule"][0][self.t],0)

    def test_matched_price_move_cancels_and_costs_reconcile(self):
        a,t = self.a,self.t
        for h in range(t+2,t+73):
            self.tape.bars[a,h] = C.Bar(130,130,130,130,130,130)
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertAlmostEqual(r["final"],500)
        self.assertAlmostEqual(r["basis_points"],0)
        self.tape.pay[a,t+5] = (.01,0)
        credited = C.run(self.tape,self.p,C.Fee(5,5))
        self.assertGreater(credited["funding_points"],0)
        self.assertLess(credited["fee_points"],0)
        self.assertAlmostEqual((credited["final"]/500-1)*100,
                               credited["funding_points"]+credited["fee_points"]+credited["basis_points"])

    def test_slot_budget_idles_four_sleeves(self):
        p = dict(self.p,slots=5)
        for a in self.tape.pairs[1:]:
            for h in range(self.t,self.t+72,24):
                self.tape.rates[a,h] = 0.
        self.tape.pay[self.a,self.t+2] = (.02,0)
        r = C.run(self.tape,p,C.Fee(0,0))
        self.assertAlmostEqual(r["final"],501)

    def test_gap_closes_at_last_common_worse_side_no_later_funding(self):
        self.tape.bars[self.a,self.t+2] = C.Bar(100,93,100,100,101,100)
        self.tape.bars[self.a,self.t+3] = None
        self.tape.pay[self.a,self.t+3] = (.9,0)
        for h in (self.t+24,self.t+48):
            self.tape.rates[self.a,h] = 0
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertEqual(r["forced"],1)
        self.assertAlmostEqual(r["final"],480)
        self.assertEqual(r["funding_points"],0)

    def test_missing_settlement_uses_larger_debit_and_only_carried_quantity(self):
        self.tape.pay[self.a,self.t+1] = (None,0)  # not carried yet
        self.tape.pay[self.a,self.t+2] = (None,0)
        self.tape.peaks[self.a] = .03
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertEqual(r["missing_funding"],1)
        self.assertAlmostEqual(r["funding_points"],-1.5)
        self.tape.peaks[self.a] = .01
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertAlmostEqual(r["funding_points"],-1.)

    def test_margin_top_up_trims_both_legs_and_charges(self):
        self.tape.bars[self.a,self.t+3] = C.Bar(180,179,180,195,195,196)
        for t in range(self.t+4,self.t+73):
            self.tape.bars[self.a,t] = C.Bar(180,180,180,195,195,195)
        r = C.run(self.tape,self.p,C.Fee(5,5))
        self.assertGreaterEqual(r["margin_topups"],1)
        self.assertLess(r["fee_points"],-.1)
        self.assertEqual(r["forced"],0)

    def test_robinhood_cash_order_rounding(self):
        f = P["fees"]["robinhood"]
        self.assertAlmostEqual(f.charge(50,50),.4875)
        self.assertAlmostEqual(f.charge(1000,1000),9.6)
        self.assertAlmostEqual(f.charge(0,200.01),.03)  # commission rounds up to 2 cents
        self.assertAlmostEqual(f.charge(50,0),.475)
        self.assertAlmostEqual(P["fees"]["kraken"].charge(50,50),.525)
        self.assertEqual(f.charge(0,200.00000000000003),.02)
        self.assertEqual(f.charge(0,200.005),.03)
        self.assertAlmostEqual(f.charge(50.005,0),.475095)

    def test_fill_hour_checks_carry_before_resize_exit_or_force(self):
        p = dict(self.p,slots=5,end=self.t+48)
        t = self.t
        for mode in ("retain","exit","force","funding"):
            with self.subTest(mode=mode):
                tape = Toy(p,n=1)
                x = tape.pairs[0]
                if mode=="exit":
                    tape.rates[x,t+24] = 0.
                pp = 310 if mode=="force" else 110 if mode=="funding" else 200
                if mode=="funding":
                    tape.pay[x,t+25] = (-.8,0)
                for h in range(t+25,t+49):
                    tape.bars[x,h] = C.Bar(100,100,100,pp,pp,pp)
                r = C.run(tape,p,C.Fee(5,5))
                if mode=="force":
                    self.assertEqual(r["forced"],1)
                    self.assertEqual(r["schedule"][0][t+24],0)
                else:
                    self.assertGreaterEqual(r["margin_topups"],1)
                    self.assertEqual(r["schedule"][0][t+24],int(mode!="exit"))
                self.assertLess(r["fee_points"],0)

    def test_forced_execution_drawdown_precedes_other_sleeves_close(self):
        p = dict(self.p,slots=5,end=self.t+24)
        for injured in (0,1):
            tape = Toy(p,n=2)
            a,b = tape.pairs[injured],tape.pairs[1-injured]
            h = self.t+23
            tape.bars[a,h] = C.Bar(100,100,100,100,100,100,302)
            tape.bars[b,h] = C.Bar(100,100,210,100,100,100)
            tape.terminal_opens[b] = (210,100)
            r = C.run(tape,p,C.Fee(0,0))
            self.assertEqual(r["forced"],1)
            self.assertAlmostEqual(r["drawdown"],.202)
            self.assertAlmostEqual(r["final"],454.)

    def test_peak_attribution_uses_exact_offset_and_cutoff(self):
        from types import SimpleNamespace
        t = self.t
        old = SimpleNamespace(begin=t,end=t+1)
        new = SimpleNamespace(begin=t+1,end=t+4)
        values = {t:(.001,0),t+1:(.04,-1_000_000),t+2:(.001,0),t+3:(.10,0)}
        def event(k,h):
            rate,offset = values[h]
            c = {"old":old,"new":new}[k]
            stamp = h*C.HOUR*10**6+offset
            if c.begin*C.HOUR*10**6<=stamp<c.end*C.HOUR*10**6:
                return True,rate,offset
            return False,None,0
        perp = SimpleNamespace(lo=t,hi=t+3,segments={"old":old,"new":new},symbols={"old":"P","new":"P"},
                               store={"P":(None,None,None,[v for v,_ in values.values()])},funding_event=event)
        archive = S.Archive(perp,{},(),{},None,dict(self.p,end=t+3))
        self.assertEqual(archive.peaks,{"old":.04,"new":.001})

    def test_cutoff_only_pre_stamp_payment_and_open_or_adverse_gap(self):
        a,t,end = self.a,self.t,self.p["end"]
        for offset,amount in ((-1_000_000,.5),(0,0),(1_000_000,0),(None,0)):
            with self.subTest(offset=offset):
                self.tape.pay[a,end] = (.01,offset) if offset is not None else (None,0)
                self.tape.bars[a,end] = None
                self.tape.terminal_opens[a] = (101,100)  # independently present, no completed bar
                r = C.run(self.tape,self.p,C.Fee(0,0))
                self.assertAlmostEqual(r["funding_points"],amount)
                self.assertEqual(r["missing_funding"],0)
                self.assertEqual(r["forced"],0)
                self.assertAlmostEqual(r["final"],502.5+5*amount)
        self.tape.bars[a,end-1] = C.Bar(100,93,100,100,100,100,101)
        self.tape.terminal_opens[a] = None
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertEqual(r["forced"],1)
        self.assertAlmostEqual(r["final"],480)

    def test_perp_cutoff_adapter_ignores_later_bar_fields_and_settlement(self):
        from types import SimpleNamespace
        t = self.t
        key = self.a.perp
        c = SimpleNamespace(key=key,begin=t-1,end=t+1)
        perp = SimpleNamespace(symbols={key:"P"},lo=t-1,hi=t-1,p={},segments={key:c},store={})
        groups = {"P":{"funding":((None,None,"fundingRate"),{}),"trade":((None,None,"klines"),{})}}
        rows = {"funding":[(t,-1_000_000,False,["time","unused","0.04"]),
                           (t,0,False,["time","unused","0.20"]),
                           (t,1_000_000,False,["time","unused","0.30"])],
                "trade":[(t,0,False,["time","103"])]}
        adapter = SimpleNamespace(archive_groups=lambda *_:groups,archive_span=lambda _:(t-1,t+1),
                                  archive_input=lambda _,__,name,*args:(name,False),
                                  archive_rows=lambda name,*_ :iter(rows[name]))
        payload = S.risk_and_cutoff(adapter,perp,(),(c,),None,None,t)
        a = C.Pair(1,key,"S",t-1,t+1)
        tape = S.Archive(perp,{"S":([100.,102.],[],[])},(),{},None,dict(self.p,end=t),*payload)
        self.assertEqual(tape.closing_open(a,t),(102.,103.))
        self.assertEqual(tape.payment(a,t),(.04,-1_000_000))
        self.assertEqual(tape.peak(a),.04)

    def test_held_sleeve_neither_changes_quantity_nor_trades(self):
        a,t,end = self.a,self.t,self.p["end"]
        for h in range(t+25,end):
            self.tape.bars[a,h] = C.Bar(100.2,100.2,100.2,100,100,100)
        self.tape.terminal_opens[a] = (200,100)
        r = C.run(self.tape,self.p,C.Fee(0,0))
        self.assertEqual(r["trade_events"],2)  # entry and terminal exit only
        self.assertAlmostEqual(r["final"],750.)  # all 2.5 spot units still held

    def test_auditor_five_sleeve_witness_has_no_resizes(self):
        t = self.t
        p = dict(P,end=t+48)
        tape = Toy(p,n=5)
        m = 49.757394939661026
        ss = [47.232166919488364,47.85504564462611,50.42706638399432,47.26956288130227,48.08188834999949]
        qs = [46.2937197152708,47.52449749618887,53.36942309718803,52.8999674622894,49.29828305376202]
        rs = [52.42569011602107,52.10404016893151,46.82611722963482,46.39969835350787,50.174738774372294]
        for a,s,q,r in zip(tape.pairs,ss,qs,rs):
            tape.pay[a,t+23] = ((r-(2*m-q))/m,0)
            for h in range(t+24,t+49):
                sp,pp = 100*s/m,100*q/m
                tape.bars[a,h] = C.Bar(sp,sp,sp,pp,pp,pp)
        result = C.run(tape,p,P["fees"]["robinhood"])
        self.assertEqual(result["trade_events"],10)
        self.assertEqual(result["margin_topups"],0)
        self.assertEqual(result["forced"],0)
        self.assertEqual(list(result["schedule"][1].values()),[5,0])

    def test_entry_uses_decision_nav_and_cash_never_skips_to_resize_or_subdollar(self):
        t = self.t
        p = dict(P,end=t+48)
        tape = Toy(p,n=2)
        a,b = tape.pairs
        tape.rates[b,t] = 0
        tape.pay[a,t+24] = (.20,0)  # cash event is after decision's strictly prior NAV
        tape.terminal_opens[b] = (200.,100.)
        result = C.run(tape,p,C.Fee(0,0))
        self.assertAlmostEqual(result["final"],560)  # $10 funding and $50 B at decision NAV
        p = dict(p,initial_usd=10)
        result = C.run(Toy(p,n=5),p,P["fees"]["robinhood"])
        self.assertEqual(result["schedule"][1][t],4)
        self.assertEqual(result["trade_events"],8)

    def test_utc_cash_event_before_or_at_year_cut_and_gap(self):
        t = C.hour("2025-12-31")
        p = dict(P,start=t,end=t+48)
        for offset,first in ((-1_000_000,.01),(0,0),(1_000_000,0)):
            with self.subTest(offset=offset):
                tape = Toy(p,n=1)
                a = tape.pairs[0]
                tape.pay[a,t+24] = (.10,offset)
                tape.pay[a,t+31] = (.02,0)
                result = C.run(tape,p,C.Fee(0,0))
                self.assertAlmostEqual(result["final"],506)
                self.assertAlmostEqual(result["years"]["2025"],first)
                self.assertAlmostEqual(result["years"]["2026"],506/(500*(1+first))-1)
        tape = Toy(p,n=1)
        a = tape.pairs[0]
        tape.pay[a,t+24] = (.10,-1_000_000)
        tape.bars[a,t+24] = None
        tape.rates[a,t+24] = 0
        result = C.run(tape,p,C.Fee(0,0))
        self.assertEqual(result["forced"],1)
        self.assertAlmostEqual(result["years"]["2025"],.01)

    def test_metadata_clock_gates_fresh_entries_but_not_held_exposure(self):
        from types import SimpleNamespace
        import re
        t,p = self.t,self.p
        names = dict(spot="data/spot/monthly/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01.zip",
                     trade="data/futures/um/monthly/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01.zip",
                     funds="data/futures/um/monthly/fundingRate/AAAUSDT/AAAUSDT-fundingRate-2022-01.zip")
        m = lambda first,last:dict(first=first*C.HOUR,last=last*C.HOUR)
        legacy = dict(funding_interval_hours=8,funding_lag_intervals=1)
        api = SimpleNamespace(BULK=re.compile(r"data/futures/um/(monthly)/(klines|fundingRate)/([A-Z]+USDT)/.*"),
                              scheduled_funding=lambda _,h,__ :h%8==0)
        a = C.Pair(1,"A","AAAUSDT",t-500,t+100)
        spot = {"archives":{names["spot"]:m(t-176,t+1)}}
        perp = {"archives":{names["trade"]:m(t-176,t+1),names["funds"]:m(t-176,t-16)}}
        self.assertTrue(S.ClockGate(api,spot,perp,{"A":"AAAUSDT"},legacy,p).allows(a,t))
        perp["archives"][names["trade"]] = m(t-175,t+1)  # missing first bar of either leg is a veto
        self.assertFalse(S.ClockGate(api,spot,perp,{"A":"AAAUSDT"},legacy,p).allows(a,t))
        perp["archives"][names["trade"]] = m(t-176,t+1)
        spot["archives"][names["spot"]] = m(t-176,t)  # missing next fill
        self.assertFalse(S.ClockGate(api,spot,perp,{"A":"AAAUSDT"},legacy,p).allows(a,t))
        spot["archives"][names["spot"]] = m(t-176,t+1)
        perp["archives"][names["funds"]] = m(t-168,t-16)  # missing first funding clock
        self.assertFalse(S.ClockGate(api,spot,perp,{"A":"AAAUSDT"},legacy,p).allows(a,t))
        tape = Toy(p,n=1)
        a = tape.pairs[0]
        tape.clock_block.update({(a,t),(a,t+48)})
        result = C.run(tape,p,C.Fee(0,0))
        self.assertEqual(list(result["schedule"][1].values()),[0,1,0])
        self.assertEqual(list(result["schedule"][0].values()),[0,1,1])
        self.assertEqual(result["blocked_slot_days"],1)

    def test_rank_first_blocks_winner_without_promoting_lower_signal(self):
        from types import SimpleNamespace
        t = self.t
        p = dict(self.p,end=t+24)
        tape = Toy(p,n=3)
        a,b,c = tape.pairs
        snapshot = SimpleNamespace(migrations=(),ranks=((1,a.coin),),
                                   contracts=(SimpleNamespace(coin_id=a.coin,listed_known_at=0,begin=a.begin,
                                                              closed_known_at=None,key=a.perp),))
        archive = S.Archive(SimpleNamespace(p={},segments={}),{},(),
                            {a.perp:((a,0),)},SimpleNamespace(latest=Mock(return_value=snapshot)),p)
        archive.bar = Mock(return_value=None)
        self.assertEqual(archive.pool(t),(a,))
        archive.bar.assert_not_called()
        self.assertFalse(archive.decision_traded(a,t))
        tape.rates.update({(a,t):.90,(b,t):.30,(c,t):None})
        tape.clock_block.add((a,t))
        tape.bars[a,t-2] = None  # do not discard the winner from the as-of queue
        out = S.evaluate(tape,p)
        self.assertEqual(out["main"]["schedule"][0],{t:0})
        self.assertEqual(out["main"]["trade_events"],0)
        self.assertEqual(out["main"]["blocked_slot_days"],1)
        self.assertEqual(out["main"]["data_gap_slot_days"],1)
        self.assertEqual(out["main"]["unfilled_slot_days"],1)
        self.assertEqual(out["main"]["unrankable_name_days"],1)
        self.assertIn("Gap: data-gap entry slot-days: 1. Metadata-blocked entry slot-days: 1.",S.render(out))
        self.assertIn("no slot assigned): 1.",S.render(out))
        tape.clock_block.clear()
        for missing_hour in (t-2,t+1):
            tape.bars = {(a,missing_hour):None}
            result = C.run(tape,p,C.Fee(0,0))
            self.assertEqual(result["trade_events"],0)
            self.assertEqual(result["blocked_slot_days"],0)
            self.assertEqual(result["data_gap_slot_days"],1)
            self.assertEqual(result["unfilled_slot_days"],1)
        tape.bars.clear()
        result = C.run(tape,dict(p,initial_usd=1),C.Fee(0,0))
        self.assertEqual(result["unfilled_slot_days"],1)
        self.assertEqual(result["data_gap_slot_days"],0)
        self.assertEqual(C.run(tape,p,C.Fee(0,0))["trade_events"],2)
        tape.clock_block.add((a,t))
        with self.assertRaisesRegex(C.Incomplete,"missed a matched open"):
            rng = Mock()
            rng.sample.side_effect = [[],[a]]
            C.run(tape,p,C.Fee(0,0),twin=({t:1},{t:1},23),rng=rng)
        tape.rates[a,t] = None
        result = C.run(tape,p,C.Fee(0,0))
        self.assertEqual(result["schedule"][1],{t:1})  # B gets the slot only if A has no rank
        self.assertEqual(result["blocked_slot_days"],0)
        self.assertEqual(result["unrankable_name_days"],2)

    def test_retrospective_link_end_keeps_slot_but_asof_closure_releases_it(self):
        from dataclasses import replace
        from types import SimpleNamespace
        t = self.t
        p = dict(self.p,end=t+24)
        for end in (t,t+1):
            for closed in (None,t*C.HOUR-1,t*C.HOUR,t*C.HOUR+1):
                with self.subTest(end=end,closed=closed):
                    tape = Toy(p,n=2)
                    a,b = tape.pairs
                    a = replace(a,end=end,closed_known_at=closed)
                    links = {x.perp:((x,0),) for x in (a,b)}
                    snap = SimpleNamespace(migrations=(),ranks=((1,a.coin),(2,b.coin)),
                                           contracts=tuple(SimpleNamespace(coin_id=x.coin,listed_known_at=0,
                                               begin=x.begin,closed_known_at=None,key=x.perp) for x in (a,b)))
                    archive = S.Archive(SimpleNamespace(p={},segments={}),{},(),links,
                                        SimpleNamespace(latest=Mock(return_value=snap)),p)
                    tape.pool = archive.pool
                    tape.rates.update({(a,t):.90,(b,t):.30})
                    tape.clock_block.add((a,t))
                    out = S.evaluate(tape,p)
                    known = closed==t*C.HOUR-1
                    self.assertEqual(out["main"]["schedule"][1],{t:int(known)})
                    self.assertEqual(out["main"]["link_end_slot_days"],int(not known))
                    self.assertEqual(out["main"]["data_gap_slot_days"],0)  # don't count it twice
                    self.assertIn(f"Gap: retrospective link-end entry slot-days: {int(not known)}.",S.render(out))
                    if not known:
                        rng = Mock()
                        rng.sample.side_effect = [[],[a]]
                        with self.assertRaisesRegex(C.Incomplete,"missed a matched open"):
                            C.run(tape,p,C.Fee(0,0),twin=({t:1},{t:1},23),rng=rng)
                        self.assertIn(a,rng.sample.call_args.args[0])

    def test_schema_refuses_ambiguous_same_spot_and_pending_review(self):
        from types import SimpleNamespace
        mk = lambda k,lo,hi:dict(contract=k,spot="AAAUSDT",begin=lo,end=hi,known_at=1,evidence_sha256="a"*64)
        contracts = {"a":SimpleNamespace(begin=10,end=20,coin_id=1),"b":SimpleNamespace(begin=10,end=30,coin_id=2)}
        with self.assertRaisesRegex(C.Incomplete,"distinct canonical"):
            S.validate_links([mk("a",10,20),mk("b",19,30)],contracts)
        with self.assertRaisesRegex(C.Incomplete,"unexpected fields"):
            S.validate_links([mk("a",10,20)|{"extra":[51]},mk("b",20,30)],contracts)
        S.validate_links([mk("a",10,20),mk("b",20,30)],contracts)
        valid,_ = S.validate_links([mk("a",10,20)|{"closed_known_at":21*C.HOUR},mk("b",20,30)],contracts)
        self.assertEqual(valid["a"][0][0].closed_known_at,21*C.HOUR)
        with self.assertRaisesRegex(C.Incomplete,"invalid top-30"):
            S.validate_links([mk("a",10,20)|{"closed_known_at":True},mk("b",20,30)],contracts)
        n = dict(reviewer="Invented independent reviewer",projection_sha256="a"*64,parents={"parent":"b"*64})
        with self.assertRaisesRegex(C.Incomplete,"independent parent"):
            S.parent_note(n,"a"*64)
        S.parent_note(n|{"review_state":"independently-approved"},"a"*64)

    def test_rank_snapshot_refusal_is_structured(self):
        from types import SimpleNamespace
        class OtherIncomplete(ValueError):
            pass
        legacy = SimpleNamespace(Incomplete=OtherIncomplete,latest=Mock(side_effect=OtherIncomplete("no visible")))
        perp = SimpleNamespace(p={},segments={})
        tape = S.Archive(perp,{},(),{},legacy,self.p)
        result = S.evaluate(tape,self.p)
        self.assertFalse(result["passed"])
        self.assertIn("rank snapshot",result["judged_refused"])

    def test_matched_twins_reproducible_and_refuse_bad_fill(self):
        p = dict(self.p,draws=8)
        out = C.assess(self.tape,p,C.Fee(0,0))
        self.assertEqual(len(out["twins"]),8)
        self.assertEqual(out,C.assess(self.tape,p,C.Fee(0,0)))
        self.assertFalse(out["checks"]["twins"])  # ties are not a win
        for a in self.tape.pairs[1:]:
            self.tape.bars[a,self.t+1] = None
        out = C.assess(self.tape,p,C.Fee(0,0))
        self.assertTrue(out["twin_refusals"])
        self.assertIsNone(out["p95"])

    def test_signal_uses_only_lagged_range_and_refuses_missing(self):
        a,t = self.a,self.t
        perp = Mock(segments={},store={},symbols={},p=dict(funding_interval_hours=8,funding_lag_intervals=1))
        perp.expects_settlement.side_effect = lambda k,h:h%8==0
        perp.rank_funding.side_effect = lambda k,h,now:(True,.001 if h%8==0 else None)
        tape = S.Archive(perp,{},(),{},None,self.p)
        self.assertAlmostEqual(tape.signal(a,t),1.095)
        self.assertEqual([c.args[1] for c in perp.rank_funding.call_args_list],list(range(t-176,t-8)))
        perp.rank_funding.side_effect = lambda *args:(False,None)
        self.assertIsNone(tape.signal(a,t+24))

    def test_spot_archive_uses_positive_volume_and_rejects_other_names_before_io(self):
        from hashlib import sha256
        from types import SimpleNamespace
        t = self.t
        rows = [[str(t*3600000),"100","102","98","101","0"],
                [str((t+1)*3600000),"100","102","99","101","1"]]
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/"zip"
            source.write_bytes(b"invented")
            fetch = SimpleNamespace(F=SimpleNamespace(zip_rows=lambda _:rows,open_epoch=lambda x:int(x)//1000),
                                    archive_root=Mock(return_value=source))
            name = "data/spot/monthly/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01.zip"
            manifest = {"errors":{},"archives":{name:{"where":"replay_16","n":2,"sha256":sha256(b"invented").hexdigest()}}}
            with self.assertRaisesRegex(C.Incomplete,"non-top-30"):
                S.load_spot(fetch,manifest,{"BBBUSDT"},t,t+1)
            fetch.archive_root.assert_not_called()
            loaded = S.load_spot(fetch,manifest,{"AAAUSDT"},t,t+1)["AAAUSDT"]
            self.assertEqual([list(col) for col in loaded],[[-1,100],[-1,99],[-1,101]])
            rows[1] = [str((t+1)*3600000),"102"]  # terminal open, no other bar fields
            terminal = S.load_spot(fetch,manifest,{"AAAUSDT"},t,t+1,terminal=t+1)
            perp = SimpleNamespace(segments={},lo=t,symbols={self.a.perp:"P"})
            tape = S.Archive(perp,{self.a.spot:terminal["AAAUSDT"]},(),{},None,dict(self.p,end=t+1),closing={"P":98})
            self.assertEqual(tape.closing_open(self.a,t+1),(102,98))

    def test_one_shot_refusal_and_consume_before_load(self):
        with tempfile.TemporaryDirectory() as d:
            lock,out = (Path(d)/x for x in ("lock","out"))
            good = lambda:({"commit":"toy"},None)
            def failed(_):
                self.assertTrue(lock.exists())
                raise OSError("invented load failure")
            with self.assertRaises(OSError):
                S.one_shot(lock,out,good,failed)
            self.assertFalse(out.exists())
            with self.assertRaisesRegex(C.Incomplete,"consumed"):
                S.one_shot(lock,out,good,lambda _:self.fail("second run"))
        with patch.object(S,"HERE",S.REPO/"off_repo_draft"), self.assertRaisesRegex(C.Incomplete,"draft"):
            S.authorize("x"*64)

    def test_concurrent_lock_only_one_score(self):
        from threading import Barrier
        with tempfile.TemporaryDirectory() as d:
            lock,out = (Path(d)/x for x in ("lock","out"))
            b = Barrier(2)
            def auth():
                b.wait(timeout=2)
                return {"commit":"toy"},None
            def runner():
                try:
                    return S.one_shot(lock,out,auth,lambda _:{"won":True})
                except C.Incomplete:
                    return None
            with ThreadPoolExecutor(2) as pool:
                result = list(pool.map(lambda _:runner(),range(2)))
            self.assertEqual(result.count({"won":True}),1)
            self.assertEqual(json.loads(out.read_text()),{"won":True})

    def test_validate_inputs_collects_projection_and_provenance_refusals_without_archive_scope(self):
        with tempfile.TemporaryDirectory() as d, patch.object(S,"RUN",Path(d)):
            seal = {k:{name:"a"*64 for name in S.INPUTS} for k in ("inputs","parent_evidence")}
            with patch.object(S,"scope_projections") as scope, patch.object(S,"load_perp") as perp:
                report = S.validate_inputs((seal,self.p))
                scope.assert_not_called()
                perp.assert_not_called()
            for code in ("projection","provenance"):
                self.assertEqual(sum(r["code"]==code for r in report["refusals"]),6)
            self.assertEqual(report["counts"]["archive_scope_blocked"],1)
            self.assertEqual(list(Path(d).iterdir()),[])

    def test_validate_inputs_collects_multiple_perp_decoder_refusals_for_one_symbol(self):
        from research_rig import archive_18 as A, common_18 as L
        t = self.t
        p = dict(L.P,start=t,end=t+48,lookback_hours=168)
        a = self.a
        symbol = "AAAUSDT"
        names = [
            "data/futures/um/monthly/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01.zip",
            "data/futures/um/monthly/markPriceKlines/AAAUSDT/1h/AAAUSDT-1h-2022-01.zip",
        ]
        manifests = (dict(archives={n:dict(where="replay_16",sha256="a"*64,n=1) for n in names},errors={}),)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            checks = S.InputChecks()
            with self.assertRaises(A.ArchivePathError):
                S.load_perp(A,path,manifests,{a.perp:symbol},{},p,(),path,None)
            self.assertIsNone(S.load_perp(A,path,manifests,{a.perp:symbol},{},p,(),path,checks))
            self.assertEqual(checks.refused,{("perp_decode",str(path/n)):1 for n in names})
            self.assertEqual(checks.counts["perp_files"],2)

    def test_validation_uses_numeric_risk_decoder_and_keeps_checking_later_files(self):
        from hashlib import sha256
        from types import SimpleNamespace
        from zipfile import ZipFile
        from research_rig import archive_18 as A, common_18 as L
        t = self.t
        names = ["data/futures/um/daily/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01-01.zip",
                 "data/futures/um/daily/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01-02.zip"]
        p = dict(L.P,start=t,end=t+47,lookback_hours=168)
        contract = SimpleNamespace(key="a",begin=t-300,end=t+100,coin_id=1)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            files = {}
            for i,name in enumerate(names):
                f = path/name
                f.parent.mkdir(parents=True,exist_ok=True)
                with ZipFile(f,"w") as z:
                    z.writestr("rows.csv",f"{(t+24*i)*C.HOUR*1000},100,99,95,101,2\n")
                files[name] = dict(where="replay_16",sha256=sha256(f.read_bytes()).hexdigest(),n=1)
            m = (dict(archives=files,errors={}),)
            symbols = {"a":"AAAUSDT"}
            tape = A.Tape(path,m,symbols,{},p,contracts=(contract,),supplemental_dir=path)
            with self.assertRaisesRegex(C.Incomplete,"perpetual high"):
                S.risk_and_cutoff(A,tape,m,(contract,),path,path,t+48)
            checks = S.InputChecks()
            S.risk_and_cutoff(A,tape,m,(contract,),path,path,t+48,checks=checks)
            self.assertEqual(checks.refused,{("perp_risk_archive",n):1 for n in names})
            self.assertEqual(checks.counts["perp_risk_rows_decoded"],2)

    def test_validation_sanitizes_spot_decoder_exception_and_continues(self):
        from hashlib import sha256
        from types import SimpleNamespace
        t = self.t
        bad = "data/spot/daily/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01-01.zip"
        good = "data/spot/daily/klines/AAAUSDT/1h/AAAUSDT-1h-2022-01-02.zip"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            files = {}
            for i,name in enumerate((bad,good)):
                f = path/name
                f.parent.mkdir(parents=True,exist_ok=True)
                raw = str(i).encode()
                f.write_bytes(raw)
                files[name] = dict(where="replay_16",sha256=sha256(raw).hexdigest(),n=1)
            def rows(raw):
                if raw==b"0":
                    raise RuntimeError("private decoder details 123.45")
                return [[str((t+24)*C.HOUR),"100","101","99","100","1"]]
            fetch = SimpleNamespace(archive_root=lambda name,_:path/name,F=SimpleNamespace(zip_rows=rows,open_epoch=int))
            checks = S.InputChecks()
            S.load_spot(fetch,dict(archives=files,errors={}),{"AAAUSDT"},t,t+48,checks=checks)
            self.assertEqual(checks.refused,{("spot_decode",str(path/bad)):1})
            self.assertEqual(checks.counts["spot_rows_decoded"],1)
            self.assertNotIn("123.45",json.dumps(checks.report()))

    def test_validate_cli_checks_uses_and_never_claims_ranks_or_computes_returns(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from types import SimpleNamespace
        t = self.t
        p = dict(self.p,end=t+24)
        a = self.a
        tape = SimpleNamespace(pool=Mock(return_value=(a,)),funding_inputs=Mock(return_value=([],1)),
            entry_covered=Mock(return_value=True),decision_traded=Mock(return_value=True),
            bar=Mock(return_value=None),payment_missing=Mock(return_value=True),
            payment=Mock(),peak=Mock(),closure=Mock(),closing_open=Mock(return_value=None),
            perp=SimpleNamespace(mark_close=Mock(return_value=None)),links={a.perp:((a,0),)})
        cases = [(tape,0),(C.Incomplete("private return literal 123.45"),1)]
        for response,rc in cases:
            out = StringIO()
            kwargs = dict(side_effect=response) if isinstance(response,Exception) else dict(return_value=(None,p))
            with (patch.object(S.sys,"argv",["score_24","--validate-inputs","a"*64]),
                  patch.object(S,"authorize",**kwargs),patch.object(S,"resources"),
                  patch.object(S,"load",return_value=tape) as load,patch.object(S,"one_shot") as one,
                  patch.object(S,"evaluate") as score,redirect_stdout(out)):
                self.assertEqual(S.main(),rc)
                one.assert_not_called()
                score.assert_not_called()
                self.assertEqual(load.call_count,1-rc)
            raw = out.getvalue()
            report = json.loads(raw)
            self.assertNotIn("123.45",raw)
            self.assertNotIn("annual",raw)
            self.assertEqual(len(report["refusals"]),rc)
        tape.funding_inputs.assert_called_once_with(a,t,full=True)
        tape.closing_open.assert_called_once_with(a,p["end"])
        # A hard hole during a possible hold does not hide later hours,
        # the contemporaneous funding access, or the terminal checks.
        tape.bar.reset_mock(side_effect=True,return_value=True)
        def bar(_,h):
            if h==t:
                raise C.Incomplete("invented accessor error")
            return C.Bar(100,95,100,100,100,100)
        tape.bar.side_effect = bar
        tape.closing_open.reset_mock()
        tape.payment.reset_mock()
        checks = S.InputChecks()
        S.check_uses(tape,p,checks)
        self.assertEqual(checks.refused,{("held_bar_access",f"{a.perp}/{a.spot}"):1})
        self.assertEqual(checks.counts["possible_held_hours"],24)
        tape.payment.assert_any_call(a,t)
        tape.payment.assert_any_call(a,t+24)
        tape.closing_open.assert_called_once_with(a,t+24)


class Planted(Toy):
    def __init__(self,p,kind,seed):
        super().__init__(p,n=10)
        self.kind, self.seed = kind,seed
        rng = Random(seed)
        self.noise = [rng.random() for _ in range((p["end"]-p["start"])//24+1)]

    def signal(self,a,t):
        return .40 if a.coin<=5 else .02

    def payment(self,a,t):
        if t%8:
            return None,0
        y = (t-self.p["start"])//24
        jitter = .0003*self.noise[y]
        if self.kind=="null":
            return jitter,0
        if a.coin<=5:
            return ((.00065+jitter) if self.kind=="edge" else (-.00065+jitter)),0
        return .0001+jitter,0


def calibration():
    # Two-day pieces of five UTC years would not test compounding. Use a
    # contiguous path touching five UTC years, with 8 twins per planted path for QA.
    p = dict(P,end=C.hour("2026-01-04"),draws=8)
    rows = {}
    for kind in ("edge","null","reversed"):
        out = C.assess(Planted(p,kind,24001),p,p["fees"][p["judged"]])
        r = out["main"]
        rows[kind] = {k:r[k] for k in ("annual","sharpe","drawdown","years","funding_points","basis_points","fee_points")}
        rows[kind].update(p95=out["p95"],checks=out["checks"],passed=out["passed"],twins=len(out["twins"]))
    assert rows["edge"]["passed"] and not rows["null"]["passed"] and not rows["reversed"]["passed"]
    return dict(scope="invented planted paths only, not a power estimate",draws_per_path=p["draws"],rows=rows)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration",action="store_true")
    args = parser.parse_args()
    if args.calibration:
        print(json.dumps(calibration(),sort_keys=True,indent=2,allow_nan=False))
    else:
        unittest.main(argv=[__file__])
