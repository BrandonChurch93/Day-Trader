"""Invented-price and metadata-only tests; no production --run or tape."""
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

try:
    from . import common_13 as C, common_16 as M, fetch_16 as F, score_16 as S, report_16 as R
except ImportError:
    import common_13 as C
    import common_16 as M
    import fetch_16 as F
    import score_16 as S
    import report_16 as R

H = M.H
T = F.F.stamp(date(2020,1,6))
X = C.Asset(10,"TESTUSDT")


def params(**changes):
    base = {"start":"2020-01-01","end":"2020-01-14","held_rank_from":3,"held_rank_to":4,
            "long_share":.5,"cost_low":[5,5,2],"cost_judged":[15,10,5],
            "cost_high":[30,20,10],"min_basket_names":1,"live_funding_lookback_hours":24,
            "short_stop_pct":80,"random_draws":3,"seed":16,"random_percentile":75,
            "min_years_above":1,"min_falling_years":1,"max_year_loss_pct":25,
            "max_missing_hours":6,"max_flagged_week_share_pct":5,
            "financing_bps_per_8h":0,"financing_interval_hours":8}
    return base|changes


def ts(i):
    return T+i*H


def fut(changes=None,marks=None,omit=(),payments=None,coverage=None):
    bars = {ts(i):M.FBar(100,100,100) for i in range(-30,169) if i not in omit}
    bars.update({ts(i):M.FBar(*rec) for i,rec in (changes or {}).items()})
    marks = {ts(i):M.FBar(*rec) for i,rec in (marks or {}).items()}
    pays = {ts(i):v for i,v in (({-8:0}|{i:0 for i in range(0,169,8)})
                               if payments is None else payments).items()}
    return M.Tape(C.Series(bars),C.Series(marks),pays,((T-1000*H,T+200*H),)
                  if coverage is None else coverage)


class Replay16Test(unittest.TestCase):
    def test_config_definition_only(self):
        p13,p = F.config()
        S.validate(p,p13)
        self.assertEqual(p["cost_judged"],[15,10,5])

    def test_majors_archive_cutoff(self):
        p13,p = F.config()
        lo = F.F.stamp(date(2020,1,1))
        hi = F.F.stamp(date(2026,11,1))
        cutoff = S.funding_cutoff(p,p13,{a.pair:((lo,hi),) for a in M.MAJORS})
        self.assertEqual(F.F.utc(cutoff).date(),date(2026,10,26))

    def test_live_uses_entry_past_payment_and_fixed_metadata_not_future(self):
        p = params()
        covered = ((ts(0),ts(100)),)
        for pays in ({-24:.02},{-24:.02,3:-.1}):
            tape = fut(payments=pays,coverage=covered)
            self.assertEqual(M.live(X,tape,T,ts(8),p),(True,False))
        self.assertEqual(M.live(X,fut(payments={-25:0,0:0}),T,ts(8),p),(False,False))
        self.assertEqual(M.live(X,fut(payments={-1:0},coverage=()),T,ts(8),p),(False,True))
        self.assertEqual(M.live(X,fut(omit=(0,)),T,ts(8),p),(False,False))

    def test_funding_uses_last_completed_trade_close_not_mark_open_or_entry_rate(self):
        tape = fut({0:(100,120,120),1:(101,150,135),2:(90,95,92)},
                   marks={1:(145,145,145)},payments={-8:.9,0:.7,1:.01,2:-.02})
        r = M.short_week(tape,X,T,ts(2),params())
        self.assertAlmostEqual(r.funding,.01*1.2-.02*1.35)
        self.assertAlmostEqual(r.price,.10)
        self.assertAlmostEqual(r.turnover,1.9)

    def test_stop_uses_marks_per_hour_and_entry_high_but_not_exit_high(self):
        entry = fut({0:(100,101,100)},marks={0:(101,181,105)})
        r = M.short_week(entry,X,T,ts(2),params())
        self.assertEqual(r.reason,"forced")
        self.assertAlmostEqual(r.price,-.8)
        trade = fut({1:(100,195,100)},marks={0:(100,105,100)})
        self.assertEqual(M.short_week(trade,X,T,ts(2),params()).reason,"forced")
        late = fut({2:(103,900,105)})
        r = M.short_week(late,X,T,ts(2),params())
        self.assertEqual(r.reason,"weekly")
        self.assertAlmostEqual(r.price,-.03)

    def test_gap_through_stop_has_no_loss_cap_and_funding_first(self):
        tape = fut({1:(315,320,319)},payments={-1:0,1:.05})
        trace = []
        r = M.short_week(tape,X,T,ts(3),params(),trace)
        self.assertAlmostEqual(r.price,-2.15)
        self.assertAlmostEqual(r.funding,.05)
        self.assertEqual([e[1] for e in trace],["funding","forced"])

    def test_timeout_follows_24_hours_since_last_payment_not_future_silence(self):
        p = params()
        a = fut({17:(110,111,110)},payments={-8:.1})
        b = fut({17:(110,111,110)},payments={-8:.1,18:.3})
        timelines = []
        for tape in (a,b):
            trace = []
            r = M.short_week(tape,X,T,ts(30),p,trace)
            self.assertEqual(r.reason,"timeout")
            self.assertAlmostEqual(r.price,-.10)
            timelines.append(trace)
        self.assertEqual(timelines[0],timelines[1])
        self.assertEqual(timelines[0][0][:2],(ts(16),"queue_timeout"))
        self.assertEqual(timelines[0][1][:2],(ts(17),"timeout"))

    def test_no_exit_bar_only_earlier_same_segment_close_no_carry(self):
        tape = fut({1:(101,110,107),3:(125,145,137)},omit=(2,))
        r = M.short_week(tape,X,T,ts(2),params())
        self.assertEqual((r.reason,r.flagged),("last_close",True))
        self.assertAlmostEqual(r.price,-.07)

    def test_short_week_gap_tolerance(self):
        for n,flg in ((6,False),(7,True)):
            tape = fut(omit=tuple(range(2,2+n)))
            self.assertEqual(M.short_week(tape,X,T,ts(16),params()).flagged,flg)

    def test_long_immediate_gate_and_fee_included_real_notional(self):
        price = C.Series({ts(1):C.Bar(100,100,100),ts(2):C.Bar(105,105,105)})
        empty = M.long_week(price,X,T,ts(2),.01,params())
        self.assertFalse(empty.filled)
        self.assertEqual(empty.outcome.factor,1)
        price = C.Series({ts(i):C.Bar(100,100,100) for i in range(3)})
        long = M.long_week(price,X,T,ts(2),.01,params())
        short = M.short_week(fut({2:(90,100,90)}),X,T,ts(2),params())
        book = M.Book(1)
        M.portfolio_step(book,T,ts(2),[long],np.ones((1,1)),1,np.ones((1,1)),
                         [short],np.array([False]),.01,.02,.03,.5,np.zeros(1,dtype=bool))
        self.assertAlmostEqual(book.finish()[0],.5+.5*.99/1.01+.5/1.01*(.1-.02*1.9))

    def test_random_excludes_own_names_even_if_unfilled_and_major_fallback(self):
        alt = C.Asset(20,"ALTUSDT")
        major = M.MAJORS[0]
        alloc,fallback,no_short,counts = M.short_weights([[X],[alt],[X,alt]],[X,alt],[major],"M",1)
        self.assertEqual(alloc.tolist(),[[0,1,0],[1,0,0],[0,0,1]])
        self.assertEqual(fallback.tolist(),[False,False,True])
        self.assertEqual(counts.tolist(),[1,1,0])
        self.assertFalse(no_short.any())
        _,_,no,_ = M.short_weights([[X]],[X],[],"M",1)
        self.assertTrue(no[0])

    def test_short_gap_can_ruin_the_account_and_it_never_restarts(self):
        long = M.Long(True,C.Outcome(1,ts(2),()),np.ones(3))
        short = M.short_week(fut({1:(340,345,340)}),X,T,ts(2),params())
        book = M.Book(1)
        w = np.ones((1,1))
        def apply():
            M.portfolio_step(book,T,ts(2),[long],w,1,w,[short],np.array([False]),
                             0,0,0,.5,np.zeros(1,dtype=bool))
        apply()
        self.assertTrue(book.failed[0])
        self.assertEqual(book.finish()[0],0)
        apply()
        self.assertEqual(book.finish()[0],0)

    def test_ruin_excludes_later_short_funding_and_forced_closes(self):
        long = M.Long(True,C.Outcome(1,ts(3),()),np.ones(4))
        a = M.short_week(fut({1:(550,550,550)}),X,T,ts(3),params())
        b = M.short_week(fut({2:(200,200,200)},payments={-8:0,2:.5}),X,T,ts(3),params())
        book = M.Book(1)
        M.portfolio_step(book,T,ts(3),[long],np.ones((1,1)),1,np.array([[.5,.5]]),
                         [a,b],np.array([False]),0,.01,0,.5,np.zeros(1,dtype=bool))
        self.assertTrue(book.failed[0])
        self.assertEqual(book.funding[0],0)
        self.assertEqual(book.forced[0],1)
        self.assertAlmostEqual(book.short_fees[0],.25*.01*(6.5+1))

    def test_delayed_long_future_value_does_not_fund_earlier_monday(self):
        def ending(future_factor,release):
            b = M.Book(1)
            h = M.Long(True,C.Outcome(future_factor,release,("last_close",),True),np.ones(3))
            M.portfolio_step(b,T,ts(2),[h],np.ones((1,1)),1,np.zeros((1,0)),[],
                             np.array([False]),0,0,0,.5,np.zeros(1,dtype=bool))
            b.begin(ts(2))
            return b.cash[0],b.finish()[0]
        self.assertEqual(ending(2,ts(3))[0],ending(3,None)[0])
        self.assertEqual(ending(2,ts(3))[0],.5)
        self.assertNotEqual(ending(2,ts(3))[1],ending(3,None)[1])

    def test_reissued_contract_ids_are_disjoint(self):
        old = F.perp_segments({"id":4172,"symbol":"LUNA"})
        new, = F.perp_segments({"id":20314,"symbol":"LUNA"})
        self.assertEqual(old[0].pair,new.pair)
        self.assertLess(old[0].end,new.begin)
        self.assertEqual(old[1].pair,"1000LUNCUSDT")

    def test_identity_filter_does_not_carry_if_present_list_loses_all_candidates(self):
        a = {"id":10,"symbol":"TEST"}
        b = {"id":20,"symbol":"ALT"}
        sn = [{"known_at":ts(-1),"kept":[b]},{"known_at":T,"kept":[a]}]
        s = C.Series({ts(i):C.Bar(100,100,100) for i in range(-60,0)})
        listed,ranked,carried = M.spot_universe(sn,{"TESTUSDT":s,"ALTUSDT":s},T,
                                               params(rise_days=1),{(20,"ALTUSDT")})
        self.assertEqual((listed,ranked,carried),([],[],False))
        live,missing = M.market_pool(sn[-1],{X.pair:fut()},T,ts(8),params(),{(20,X.pair)})
        self.assertEqual((live,missing),([],set()))

    def test_identity_policy_must_match_snapshot_and_be_named_in_each_plan(self):
        import json
        good = json.dumps({"snapshots_sha256":"abc","confirmed":{"spot":[[1,"BTCUSDT"]],
                           "futures":[[1,"BTCUSDT"]]},
                           "archive_manifest_sha256":{"manifest_spot.json":"xyz"}}).encode()
        self.assertEqual(S.identity_policy(good,"abc")["futures"],{(1,"BTCUSDT")})
        self.assertEqual(S.identity_policy(good,"abc",{"manifest_spot.json":"xyz"})["spot"],{(1,"BTCUSDT")})
        with self.assertRaises(S.S.Refused):
            S.identity_policy(good,"abc",{"manifest_spot.json":"changed"})
        with self.assertRaises(S.S.Refused):
            S.identity_policy(good,"other-snapshot")
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d/S.IDENTITY).write_bytes(good)
            plan = S.F.digest(good)[:12].encode()
            with patch.object(S.F,"DATA",d):
                with self.assertRaises(S.S.Refused):
                    S.identity_bytes(plan,b"missing")
                self.assertEqual(S.identity_bytes(plan,plan),good)

    def test_marks_1_to_3_ignore_quality_but_loss_mark_does_not(self):
        def year(end,reference,random,flags):
            return {"held":{"all_spot_end":reference,"shorts":{"M":{"judged":{
                "end":end,"random_percentile":random,"flagged_week_share_pct":flags}}}}}
        y = {"a":year(1.2,.95,1.1,5),"b":year(.7,.9,.6,6)}
        r = M.judge(y,params())
        self.assertEqual(r["marks"],[True,True,True,False])
        self.assertEqual(r["eligible"],["a"])
        self.assertEqual(r["over_max_loss"],["b"])

    def test_toy_replay_all_costs_and_report(self):
        p13 = {"start":"2020-01-01","end":"2020-01-14","universe_top_n":2,"hot_n":1,
               "rise_days":1,"max_missing_hours":6,"financing_bps_per_8h":0,
               "financing_interval_hours":8}
        a,b = {"id":10,"symbol":"TEST"},{"id":20,"symbol":"ALT"}
        spot = {"TESTUSDT":C.Series({ts(i):C.Bar(100,100,100) for i in range(-30,169)}),
                "ALTUSDT":C.Series({ts(i):C.Bar(100,100,100) for i in range(-30,169)})}
        snap = {"known_at":T,"kept":[a,b]}
        got = M.replay({"viewed":[snap],"held":[snap]},spot,
                       {s:fut() for s in ("TESTUSDT","ALTUSDT","BTCUSDT")},params(),p13)
        r = got["years"]["2020"]["held"]["shorts"]
        self.assertEqual(set(r["M"]),{"low","judged","high"})
        self.assertTrue(r["M"]["low"]["end"]>r["M"]["judged"]["end"]>r["M"]["high"]["end"])
        self.assertEqual(len(r["M"]["judged"]["random_ends"]),3)
        self.assertIn("Short forced closes",R.render(got|{"cutoff_utc":"invented"}))

    def test_guard_before_metadata_or_result_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            final,draft = d/"final",d/"draft"
            with patch.multiple(S,PLAN=final,DRAFT=draft),patch.object(S,"metadata") as meta:
                for f in ("Status: DRAFT","Status: FROZEN"):
                    final.write_text(f)
                    with self.assertRaises(S.S.Refused):
                        S.run()
                final.write_text("Status: frozen fixture")
                draft.write_text("Status: DRAFT")
                with self.assertRaises(S.S.Refused):
                    S.run()
                meta.assert_not_called()

    def test_one_shot_durable_lock_and_no_symlink_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            result,local,durable = d/"result",d/"local",d/"durable"
            S.S.guard("Status: frozen fixture",result,local,durable,{"fixture":True})
            self.assertTrue(durable.is_file())
            local.unlink()
            with self.assertRaises(S.S.Refused):
                S.S.guard("Status: frozen fixture",result,local,durable,{})
            durable.unlink()
            durable.symlink_to(d/"absent")
            with self.assertRaises(S.S.Refused):
                S.S.unused_paths(result,local,durable)
