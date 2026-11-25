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
        self.assertEqual(M.live(X,fut(payments={-1:0},coverage=()),T,ts(8),p),(True,True))
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

    def test_negative_cash_opens_no_risk_in_second_week_with_pending_lot(self):
        w = np.ones((1,1))
        no = np.zeros((1,0))
        f = np.zeros(1,dtype=bool)
        gain = M.Long(True,C.Outcome(2,ts(4),()),np.array([1,1,2.]))
        gap = M.Sleeve(-1.2,0,3.2,False,"forced",np.array([[0,0,1],[-1.2,0,3.2],[-1.2,0,3.2]]))
        for release,goal in ((ts(5),.4),(ts(3),.3)):
            book = M.Book(1)
            factor = 1 if release==ts(5) else .8
            old = M.Long(True,C.Outcome(factor,release,()),np.ones(3))
            M.portfolio_step(book,T,ts(2),[old],w,1,w,[gap],f,0,0,0,.5,f)
            self.assertAlmostEqual(book.cash[0],-.1)
            self.assertAlmostEqual(book.equity(ts(2))[0],.4)
            M.portfolio_step(book,ts(2),ts(4),[gain],w,1,no,[],f,0,0,0,.5,f)
            self.assertFalse(book.failed[0])
            self.assertAlmostEqual(book.finish()[0],goal)
            if release==ts(3):
                self.assertEqual(book.pending,[])
                self.assertAlmostEqual(book.cash[0],.3)

    def test_marked_equity_sizing_capped_by_free_cash(self):
        w = np.ones((1,1))
        f = np.zeros(1,dtype=bool)
        b = M.Book(1)
        b.cash[0] = .1
        old = M.Long(True,C.Outcome(1,ts(5),()),np.ones(3))
        b.add_pending(old,np.array([.5]))
        new = M.Long(True,C.Outcome(2,ts(4),()),np.array([1,1,2.]))
        M.portfolio_step(b,ts(2),ts(4),[new],w,1,np.zeros((1,0)),[],f,0,0,0,.5,f)
        self.assertAlmostEqual(b.cash[0],.15)
        self.assertAlmostEqual(b.finish()[0],.65)

    def test_large_waiting_lot_does_not_back_new_short(self):
        w = np.ones((1,1))
        f = np.zeros(1,dtype=bool)
        book = M.Book(1)
        book.cash[0] = .2
        book.add_pending(M.Long(True,C.Outcome(1,ts(8),()),np.ones(3)),np.array([4.]))
        new = M.Long(True,C.Outcome(1,ts(7),()),np.ones(3))
        sleeve = M.Sleeve(0,.2,2,False,"weekly",np.array([[0,0,1],[0,.2,2],[0,.2,2.]]))
        M.portfolio_step(book,ts(2),ts(4),[new],w,1,w,[sleeve],f,.01,0,0,.5,f)
        self.assertAlmostEqual(book.pending[-1][1][0],.1)
        self.assertAlmostEqual(book.funding[0],.1/1.01*.2)
        self.assertAlmostEqual(book.cash[0]-book.funding[0],.1)

    def test_fence_at_half_hour_settles_at_prior_complete_close(self):
        boundary = C.Asset(10,X.pair,T-H,ts(2)+H//2)
        class RejectCross(dict):
            def __getitem__(self,t):
                if t==ts(2):
                    raise AssertionError("bar crosses identity boundary")
                return super().__getitem__(t)
            def get(self,t,default=None):
                return self[t] if t in self else default
        tape = fut({1:(100,100,96),2:(900,1000,900)},marks={2:(900,1000,900)},
                   payments={-1:0,2:.5})
        tape.trade.bars = RejectCross(tape.trade.bars)
        tape.mark.bars = RejectCross(tape.mark.bars)
        out = M.short_week(tape,boundary,T,ts(4),params())
        self.assertEqual((out.reason,out.funding,out.flagged),("last_close",0,True))
        self.assertAlmostEqual(out.price,.04)
        prices = C.Series(RejectCross({T:C.Bar(100,100,100),ts(1):C.Bar(100,95,96),
                                       ts(2):C.Bar(900,900,900)}))
        lot = M.long_week(prices,boundary,T,ts(4),0,params())
        self.assertEqual((lot.outcome.release,lot.outcome.flagged),(ts(2),True))
        self.assertAlmostEqual(lot.outcome.factor,.96)

    def test_successor_starts_at_first_complete_bar_and_cannot_borrow_volume(self):
        boundary = C.Asset(10,X.pair,T-H//2,ts(30))
        tape = fut({i:(100,100,100,100,0) for i in range(-24,0)},payments={-1:0,0:0})
        self.assertFalse(M.live(boundary,tape,ts(-1),ts(5),params())[0])
        self.assertFalse(M.live(boundary,tape,T,ts(5),params())[0])
        self.assertTrue(M.live(boundary,tape,ts(1),ts(5),params())[0])
        self.assertEqual(tape.within(M.hourly_asset(boundary)).dead,[])
        series = C.Series({ts(i):C.Bar(100,100,100) for i in range(-1,31)})
        self.assertFalse(M.long_week(series,boundary,ts(-1),ts(5),0,params()).filled)
        self.assertTrue(M.long_week(series,boundary,T,ts(5),0,params()).filled)

    def test_year_end_pending_open_settles_to_opening_year(self):
        series = C.Series({ts(0):C.Bar(100,100,100),ts(3):C.Bar(150,150,150)})
        lot = M.long_week(series,X,T,ts(2),0,params())
        b = M.Book(1)
        f = np.zeros(1,dtype=bool)
        M.portfolio_step(b,T,ts(2),[lot],np.ones((1,1)),1,np.zeros((1,0)),[],f,0,0,0,1,f)
        self.assertEqual(lot.outcome.release,ts(3))
        self.assertEqual(b.cash[0],0)
        self.assertAlmostEqual(b.finish()[0],1.5)

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
            plan = f"Shared identity policy SHA-256 {S.F.digest(good)}.".encode()
            with patch.object(S.F,"DATA",d):
                with self.assertRaises(S.S.Refused):
                    S.identity_bytes(plan,b"missing")
                bogus = f"Shared identity policy SHA-256 {'f'*64}.\nUnrelated note {S.F.digest(good)}.".encode()
                with self.assertRaises(S.S.Refused):
                    S.identity_bytes(bogus,bogus)
                self.assertEqual(S.identity_bytes(plan,plan),good)

    def test_trusted_freeze_refuses_mutated_manifest_code_config_or_record(self):
        import json
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            rec = {"version":1,"inputs":{"archive":"a"},"config_sha256":"b","code_sha256":{"c":"d"}}
            raw = json.dumps(rec).encode()
            record = d/S.FREEZE
            record.write_bytes(raw)
            trusted = S.F.digest(raw)
            with patch.object(S.F,"DATA",d), patch.object(S,"collect_freeze",return_value=(rec,)):
                self.assertEqual(S.verified_freeze(trusted),(rec,))
                for change in ({"config_sha256":"new"},{"code_sha256":{"c":"new"}},
                               {"inputs":{"archive":"new"}}):
                    with patch.object(S,"collect_freeze",return_value=(rec|change,)):
                        with self.assertRaises(S.S.Refused):
                            S.verified_freeze(trusted)
                record.write_bytes(raw+b" ")
                with self.assertRaises(S.S.Refused):
                    S.verified_freeze(trusted)

    def test_both_run_entries_refuse_changed_source_before_any_lock(self):
        try:
            from . import score_17 as peer
        except ImportError:
            import score_17 as peer
        import json
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d/"config").mkdir()
            (d/"config/thresholds.yaml").write_text("dummy")
            (d/"snapshots.json").write_text("source")
            for name in S.FREEZE_META:
                (d/name).write_text("metadata")
            code = d/"code.py"
            code.write_text("before")
            declared = f"Shared identity policy SHA-256 {F.digest(b'metadata')}.".encode()
            with patch.object(S,"HERE",d), patch.object(S,"SHARED_CODE",("code.py",)), \
                 patch.object(F,"DATA",d), patch.object(F.F,"ROOT",d), patch.object(F.F,"DATA",d), \
                 patch.object(S,"plan_bytes",return_value=declared), \
                 patch.object(S,"peer_plan_bytes",return_value=declared), \
                 patch.object(S,"us_roster_bytes",return_value=b"roster"), \
                 patch.object(S.S,"guard") as lock, patch.object(S,"load_groups") as bars:
                rec,*_ = S.collect_freeze()
                raw = json.dumps(rec).encode()
                (d/S.FREEZE).write_bytes(raw)
                code.write_text("after")
                for runner in (S.run,peer.run):
                    with self.assertRaises(S.S.Refused):
                        runner(F.digest(raw))
                lock.assert_not_called()
                bars.assert_not_called()

    def test_asof_timeline_does_not_read_future_months_and_notices(self):
        d = lambda s:F.F.boundary(s,0)
        rows = [dict(id=10,market="spot",pair="TESTUSDT",notice_status="CONFIRMED",
                     notice_at="2020-03-02",months=[
                         ("2020-01-05",d("2020-01-06"),True),
                         ("2020-02-02",d("2020-02-03"),False),
                         ("2020-03-01",d("2020-03-02"),False)])]
        timeline = S.I.Timeline({"as_of_rows":rows},d("2020-03-02"))
        k = ("spot",10,"TESTUSDT")
        self.assertEqual(timeline.states(d("2020-01-05"))[k],"UNKNOWN")
        self.assertEqual(timeline.states(d("2020-01-06"))[k],"CONFIRMED")
        self.assertEqual(timeline.states(d("2020-02-03"))[k],"UNKNOWN")
        self.assertEqual(timeline.states(d("2020-03-02"))[k],"REMOVED")
        with self.assertRaises(ValueError):
            S.I.Timeline({"as_of_rows":rows},d("2020-02-03"))
        wrong = rows[0]|{"notice_status":"REMOVED"}
        self.assertEqual(S.I.status_at(wrong,d("2020-01-06")),"REMOVED")

    def test_date_only_monday_notice_confirms_next_monday_not_current(self):
        d = lambda day:F.F.boundary(day,0)
        row = dict(id=10,market="spot",pair="TESTUSDT",notice_status="CONFIRMED",
                   notice_at="2020-03-02",months=[])
        timeline = S.I.Timeline({"as_of_rows":[row]},d("2020-03-09"))
        key = ("spot",10,"TESTUSDT")
        self.assertEqual(timeline.states(d("2020-03-02"))[key],"UNKNOWN")
        self.assertEqual(timeline.states(d("2020-03-09"))[key],"CONFIRMED")

    def test_chronology_lifts_only_proven_date_only_gaps_through_60_days(self):
        try:
            from . import identity_chronology_16_17 as q
        except ImportError:
            import identity_chronology_16_17 as q
        self.assertEqual(q.gap_bounds(["2020-03-02"],"2021-04-01","2020-02"),(2,30))
        self.assertEqual(q.bucket((2,30)),"unresolved_bucket")
        chron = {"notice_status":"REMOVED","reason":"excluded under the chronology rule"}
        self.assertTrue(q.soft_removal(chron,(60,60)))
        self.assertTrue(q.soft_removal(chron,(-5,60)))
        self.assertFalse(q.soft_removal(chron,(61,61)))
        self.assertFalse(q.soft_removal(chron,(1,61)))
        self.assertFalse(q.soft_removal(chron|{"reason":"different underlying asset"},(1,1)))

    def test_chronology_never_reads_pre_date_bars_for_the_coin(self):
        try:
            from . import common_17 as inverse
        except ImportError:
            import common_17 as inverse
        d = lambda s:F.F.boundary(s,0)
        r = dict(id=999,market="spot",pair="TESTUSDT",notice_status="CONFIRMED",
                 notice_at="2020-01-02",months=[],start_from_utc="2020-01-03")
        floor = d("2020-01-03")
        timeline = S.I.Timeline({"as_of_rows":[r,r|{"market":"futures"}]},d("2020-02-01"))
        early,late = d("2020-01-06"),d("2020-01-13")
        self.assertNotIn((999,"TESTUSDT"),timeline.at(d("2020-01-02"))["spot"])
        class RejectEarly(dict):
            def __getitem__(self,t):
                if t<floor:
                    raise AssertionError("attempt to read pre-date price")
                return super().__getitem__(t)
            def get(self,t,default=None):
                return self[t] if t in self else default
        prices = C.Series({t:C.Bar(100,100,100) for t in range(floor-12*H,late+48*H,H)})
        prices.bars = RejectEarly(prices.bars)
        snap = {"known_at":early,"kept":[{"id":999,"symbol":"TEST"}]}
        cfg = params(rise_days=7)
        self.assertFalse(M.spot_universe([snap],{"TESTUSDT":prices},early,cfg,timeline.at(early)["spot"])[1])
        asset = M.spot_universe([snap],{"TESTUSDT":prices},late,cfg,timeline.at(late)["spot"])[1][0]
        self.assertEqual(asset.begin,floor)
        self.assertTrue(M.long_week(prices,asset,late,late+H,0,cfg).filled)
        futures_prices = C.Series({t:M.FBar(100,100,100) for t in prices.times})
        future = M.Tape(futures_prices,futures_prices,{floor-H:0,floor+H:0},((floor-12*H,late+48*H),))
        futures_prices.bars = RejectEarly(futures_prices.bars)
        ap = S.I.bound_asset(C.Asset(999,"TESTUSDT"),timeline.at(early)["futures"])
        self.assertEqual(ap.begin,floor)
        self.assertFalse(M.live(ap,future,floor,floor+2*H,cfg)[0])
        inv = inverse.prepare(future,ap,floor,floor+2*H,cfg|{"dip_lookback_hours":4})
        self.assertIsNone(inv.preceding_close)
        self.assertEqual(inv.preceding_payment,-10**12)
        M.short_week(future,ap,floor,floor+2*H,cfg)

    def test_zero_volume_run_retires_at_last_executable_close_without_funding(self):
        flat = {i:(98,400,98,1,0) for i in range(1,25)}
        tape = fut({0:(100,100,97,96,3)}|flat,payments={-8:0,1:.7,8:.9,24:1,25:0})
        self.assertEqual(tape.dead,[(ts(1),ts(25))])
        self.assertEqual(tape.payments,[ts(-8),ts(25)])
        self.assertTrue(M.live(X,tape,T,ts(30),params())[0])
        self.assertFalse(M.live(X,tape,ts(1),ts(30),params())[0])
        self.assertTrue(M.live(X,tape,ts(26),ts(30),params())[0])
        out = M.short_week(tape,X,T,ts(8),params())
        self.assertEqual((out.reason,out.funding,out.flagged),("volume_stop",0,True))
        self.assertEqual(out.dead_close_phase,1)
        self.assertAlmostEqual(out.price,.03)
        self.assertAlmostEqual(out.turnover,1.97)
        self.assertFalse(fut(dict(list(flat.items())[:-1])).dead)

    def test_dead_spell_close_requires_a_sized_open_short(self):
        book = M.Book(2)
        lot = M.Long(True,C.Outcome(1,ts(1),()),np.ones(2))
        dry = M.Sleeve(0.,0.,2.,True,"volume_stop",np.array([[0,0,1],[0,0,2]]),1)
        M.portfolio_step(book,T,ts(1),[lot],np.array([[1.],[0.]]),1,np.ones((2,1)),
                         [dry],np.zeros(2,dtype=bool),0.,0.,0.,.5,np.zeros(2,dtype=bool))
        self.assertEqual(M.dead_counts(book),{"rule":1,"random":[0]})

    def test_spot_and_futures_use_same_swap_bounds_and_date_fence(self):
        for cid in F.SPOT_SWAP_IDS:
            by_spot = F.spot_segments({"id":cid})
            self.assertEqual(by_spot,tuple((a.begin,a.end,a.pair) for a in F.perp_segments({"id":cid})))
        r = dict(id=1042,market="futures",pair="SCUSDT",notice_status="UNKNOWN",
                 notice_at=None,months=[("2022-06-05",F.F.boundary("2022-06-06",0),True)],
                 notice_end_utc="2022-06-17T09")
        self.assertEqual(S.I.status_at(r,F.F.boundary("2022-06-13",0)),"CONFIRMED")
        self.assertEqual(S.I.status_at(r,F.F.boundary("2022-06-20",0)),"REMOVED")

    def test_same_ticker_different_resolved_coin_does_not_omit_short(self):
        other = C.Asset(55,X.pair,begin=T,end=ts(8))
        holdings = [[X]]
        w,fall,_,n = M.short_weights(holdings,[other],[],"M",1)
        self.assertEqual(w[0,0],1)
        self.assertFalse(fall[0])
        self.assertEqual(n[0],1)

    def test_funding_timestamp_rounded_before_cutoff_filter(self):
        key = "data/futures/um/monthly/fundingRate/TESTUSDT/dummy.zip"
        with tempfile.TemporaryDirectory() as temp:
            archive=Path(temp)/"tiny"
            archive.write_bytes(b"dummy")
            m=dict(where="replay_16",sha256=F.digest(b"dummy"),n=2)
            rows=[(str((T+1)*1000),"8","0.01"),(str((ts(1)+1)*1000),"8","0.02")]
            with patch.object(F,"archive_root",return_value=archive), patch.object(F.F,"zip_rows",return_value=rows):
                actual=S.load_groups({"archives":{key:m}},False,T)
            self.assertEqual(actual["TESTUSDT"].funding,{T:.01})

    def test_file_gate_reports_observed_liveness_separately(self):
        p=params()
        tape=fut(payments={-1:0},coverage=())
        self.assertEqual(M.live_screens(X,tape,T,ts(4),p),(True,False))
        stale=fut(payments={-25:0},coverage=())
        self.assertEqual(M.live_screens(X,stale,T,ts(4),p),(False,False))

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
        report = R.render(got|{"cutoff_utc":"2019-01-14T00:00:00+00:00",
                               "last_complete_funding_week_monday_utc":"2019-01-07"})
        self.assertIn("Short forced closes",report)
        self.assertIn("Monday-observed basket name-weeks | Monday-observed major name-weeks",report)
        self.assertIn("dead-spell closes, judged costs",report)
        self.assertIn("began Monday 2019-01-07 UTC",report)

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
