"""Invented prices and temporary guard fixtures only."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

try:
    from . import common_13 as C, common_16 as M, common_17 as R, score_17 as S, report_17 as P
    from .test_16 import X,T,ts,fut,params
except ImportError:
    import common_13 as C
    import common_16 as M
    import common_17 as R
    import score_17 as S
    import report_17 as P
    from test_16 import X,T,ts,fut,params


def settings(**overrides):
    return params(**(dict(rise_days=1,dip_lookback_hours=4,dip_pct=5,take_pct=5,stop_pct=5,
                          max_hold_hours=24,forced_close_rise_pct=30)|overrides))


def grid(trades,signals=(0,),risk=None,pays=None,preceding=-8):
    seq = tuple(M.FBar(*b) if b else None for b in trades)
    marks = tuple(M.FBar(*risk[i]) if risk and i in risk else b for i,b in enumerate(seq))
    return R.Grid(seq,marks,tuple(i in signals for i in range(len(seq))),
                  tuple((pays or {}).get(i) for i in range(len(seq))),ts(preceding),100,False)


def run(g,**opts):
    trace = []
    out = R.swing(g,X,T,ts(len(g.trades)-1),opts.pop("p",settings()),opts.pop("fee",0),
                  trace=trace,**opts)
    return out,[(t,k,px,v) for t,k,px,v in trace if k!="funding"]


class Replay17Test(unittest.TestCase):
    def test_config(self):
        p13,p16 = S.F.config()
        p = S.F.F.yaml.safe_load((S.F.F.ROOT/"config/thresholds.yaml").read_bytes())["replay_17_plan"]["value"]
        S.validate(p,p13,p16)
        self.assertEqual(p["cost_bps_per_side"],10)
        self.assertEqual(p["us_costs_bps"],[38,80])
        for bad in (None,(38,80),[38],["38",80],[True,80],[10,80],[38,float("inf")]):
            with self.subTest(fees=bad),self.assertRaisesRegex(S.S.Refused,"US fees"):
                S.validate(p|{"us_costs_bps":bad},p13,p16)

    def test_contract_signal_does_not_cross_identity_or_use_mark(self):
        t = fut({-25:(90,90,90),-3:(120,120,120),0:(80,80,80)})
        self.assertTrue(R.prepare(t,X,T,ts(2),settings()).signals[0])
        self.assertFalse(R.prepare(t,C.Asset(10,X.pair,ts(-22),ts(10)),T,ts(2),settings()).signals[0])
        control = fut({-25:(90,90,90),0:(80,500,500)},marks={-3:(120,120,120)})
        self.assertFalse(R.prepare(control,X,T,ts(2),settings()).signals[0])

    def test_half_hour_fence_is_not_a_mark_or_trade_and_successor_waits(self):
        tape = fut({-25:(90,90,90),-3:(120,120,120),0:(100,100,98),
                    1:(98,99,96),2:(900,1000,900)},marks={2:(900,1000,900)})
        old = C.Asset(10,X.pair,ts(-30),ts(2)+M.H//2)
        successor = C.Asset(11,X.pair,old.end,ts(40))
        g = R.prepare(tape,old,T,ts(5),settings())
        self.assertTrue(g.signals[0])
        self.assertIsNone(g.trades[2])
        self.assertIsNone(g.risk[2])
        trace = []
        out = R.swing(g,old,T,ts(5),settings(),0.,lev=3,trace=trace)
        self.assertTrue(out.flagged)
        self.assertEqual(trace[-1][:3],(ts(2),"last_close",96))
        g2 = R.prepare(tape,successor,ts(2),ts(5),settings())
        self.assertIsNone(g2.trades[0])
        self.assertIsNone(g2.risk[0])
        self.assertIsNotNone(g2.trades[1])
        self.assertFalse(any(g2.signals))

    def test_exit_clocks_funding_and_fees(self):
        g = grid([(100,100,95),(90,100,90),(100,100,100)],pays={0:.4,1:.1})
        a,tr = run(g,fee=.01)
        self.assertEqual(tr[-1][:3],(ts(1),"target",90))
        self.assertAlmostEqual(a.path[-1,0],.1+.095-.019)
        self.assertAlmostEqual(a.path[-1,2],.095)
        b,_ = run(g,charge_funding=False)
        self.assertAlmostEqual(b.path[-1,0],.10)
        self.assertEqual(b.path[-1,2],0)

    def test_delayed_entry_and_exit(self):
        g = grid([None,(103,105,100),(100,100,94),None,(96,99,96),(101,101,101)])
        a,tr = run(g)
        self.assertTrue(a.flagged)
        self.assertEqual([(t,kind) for t,kind,_,_ in tr],[(ts(1),"sell_short"),(ts(4),"target")])

    def test_one_x_uncapped_and_no_high_stop(self):
        a,tr = run(grid([(100,650,106),(350,750,350),(390,1000,390)]))
        self.assertEqual(tr[-1][1],"stop")
        self.assertAlmostEqual(a.path[-1,0],-2.5)
        self.assertEqual(a.path[-1,-1],0)

    def test_three_x_entry_high_uses_mark_caps_part(self):
        a,tr = run(grid([(100,100,100)]*3,risk={0:(100,131,100)}),lev=3,fee=.02)
        self.assertEqual(tr[-1][:3],(T,"forced",130))
        self.assertEqual(a.path[-1,0],-1)
        self.assertAlmostEqual(a.path[-1,1]+a.path[-1,2]-a.path[-1,3]+a.path[-1,4],-1)

    def test_three_x_queued_exit_only_checks_open(self):
        for px,mode,net in ((95,"target",.15),(180,"forced",-1)):
            a,tr = run(grid([(100,100,94),(px,500,px),(100,100,100)]),lev=3)
            self.assertEqual(tr[-1][1],mode)
            self.assertAlmostEqual(a.path[-1,0],net)

    def test_bounce_only_after_target_reverses_funding(self):
        g = grid([(100,100,94),(90,100,100),(99,100,99),(99,100,99)],pays={1:.1,2:.02})
        a,tr = run(g,bounce=True)
        self.assertEqual([k for _,k,_,_ in tr],["sell_short","target","buy_bounce","target"])
        self.assertEqual(tr[1][0],tr[2][0])
        self.assertAlmostEqual(a.path[-1,2],.094-.02*1.194*100/90)
        _,tr = run(grid([(100,110,108),(90,100,100),(99,100,99)]),bounce=True)
        self.assertEqual([k for _,k,_,_ in tr],["sell_short","stop"])

    def test_timeout_never_backdates_against_future_payment_or_allows_reentry(self):
        g = grid([(100,100,94)]+[(100,100,100)]*4,signals=(0,2,3),pays={2:0},preceding=-24)
        a,tr = run(g,bounce=True)
        self.assertEqual([k for _,k,_,_ in tr],["sell_short","funding_timeout"])
        self.assertFalse(a.flagged)

    def test_missing_terminal_open_last_trade_close_and_flag(self):
        a,tr = run(grid([(100,100,100),(100,108,101),None]))
        self.assertTrue(a.flagged)
        self.assertEqual(tr[-1][:3],(ts(2),"last_close",101))
        self.assertAlmostEqual(a.path[-1,0],-.01)

    def test_target_before_time_on_same_close(self):
        _,tr = run(grid([(100,100,94),(93,100,93),(100,100,100)]),p=settings(max_hold_hours=1))
        self.assertEqual(tr[-1][1],"target")

    def test_each_trade_compounds_local_part(self):
        g = grid([(100,100,94),(90,90,90),(100,100,93),(90,90,90),(90,90,90)],signals=(0,2))
        a,_ = run(g)
        self.assertAlmostEqual(a.path[-1,0],1.1**2-1)
        self.assertEqual(a.path[-1,5],2)

    def test_portfolio_stops_at_first_realized_zero(self):
        a,b = np.zeros((4,7)),np.zeros((4,7))
        a[1:,[0,1]] = -2.4
        a[1:,5] = 1
        b[3,[0,1,5]] = [1,1,1]
        ac = R.Accounts(1)
        ac.add([R.Part(a,False,1),R.Part(b,False,3)],np.array([[0,1]]),2,False)
        self.assertEqual(ac.value[0],0)
        self.assertEqual(ac.row()["trades"],1)
        self.assertEqual(ac.row()["dead_spell_closes"]["rule"],1)
        self.assertAlmostEqual(ac.row()["price"],-1.2)

    def test_idle_is_not_a_flag_even_for_carried_list(self):
        path = np.zeros((3,7))
        path[-1,[0,1,5]] = [.1,.1,1]
        ac = R.Accounts(1)
        ac.add([R.Part(path,False)],np.array([[0,1,1,1,1]]),5,True)
        r = ac.row()
        self.assertAlmostEqual(r["end"],1.02)
        self.assertEqual((r["idle_parts"],r["live_parts"],r["flagged_parts"],r["flag_share_pct"]),(4,1,1,100))

    def test_live_part_flags_include_no_trigger(self):
        path = np.zeros((4,7))
        ac = R.Accounts(1)
        ac.add([R.Part(path,True),R.Part(path,False)],np.array([[0,1,2,2,2]]),5,False)
        r = ac.row()
        self.assertEqual((r["trades"],r["live_parts"],r["flagged_parts"],r["flag_share_pct"]),(0,2,1,50))

    def test_stale_run_closes_before_funding_and_skips_no_trade_hours(self):
        tape = fut({-25:(90,90,90),-3:(120,120,120),0:(100,100,98)}
                   |{i:(98,150,98,1,0) for i in range(1,25)},
                   payments={-8:0,1:.8,8:.9})
        tr = []
        gp = R.prepare(tape,X,T,ts(8),settings())
        part = R.swing(gp,X,T,ts(8),settings(),.01,trace=tr)
        self.assertEqual(tr[-1][:3],(ts(1),"volume_stop",98))
        self.assertEqual(part.path[-1,2],0)
        self.assertAlmostEqual(part.path[-1,3],.0198)
        self.assertTrue(part.flagged)
        self.assertEqual(part.dead_close_phase,2)
        flat = R.swing(R.Grid(gp.trades,gp.risk,(False,)*len(gp.signals),gp.payments,
                              gp.preceding_payment,gp.preceding_close,gp.gap,gp.dry),
                       X,T,ts(8),settings(),.01)
        self.assertTrue(flat.flagged)
        self.assertIsNone(flat.dead_close_phase)

    def test_hold_dead_spell_close_counts_stop_at_ruin(self):
        early = M.Sleeve(-4,0,6,False,"forced",np.array([[0,0,1],[-4,0,6],[-4,0,6]]))
        dry = M.Sleeve(0,0,2,True,"volume_stop",np.array([[0,0,1],[0,0,1],[0,0,2]]),2)
        diag = []
        self.assertEqual(R.hold_factor([early,dry],2,0,True,diag),0)
        self.assertEqual(diag,[0])
        self.assertEqual(R.hold_factor([dry],1,0,True,diag),1)
        self.assertEqual(diag,[0,1])

    def test_trade_low_is_forced_proxy_for_levered_bounce(self):
        tape = fut({-25:(80,80,80),-3:(120,120,120),0:(100,100,94),
                    1:(94,96,94,60,1)})
        tr = []
        R.swing(R.prepare(tape,X,T,ts(4),settings()),X,T,ts(4),settings(),
                0,lev=3,bounce=True,trace=tr)
        self.assertIn((ts(1),"forced",94*.7),[x[:3] for x in tr])

    def test_judgment_counts_same_years_ignores_quality_failures(self):
        def row(end,hold,spot,n=12,flags=0):
            return {"held":{"swing":{"judged":{"end":end,"trades":n,"flag_share_pct":flags}},
                            "hot_hold":{"judged":hold},"spot_all":spot}}
        y = {"2020":row(1.2,1.1,1.1),"2021":row(1.2,1.3,1.1),
             "2022":row(1.2,1.1,1.2,n=3),"2023":row(1.1,1,1.2,flags=5.001)}
        x = R.judge(y,dict(min_trades_per_year=10,max_flagged_share_pct=5,
                           min_years_above=2,min_rising_years=1),"judged")
        self.assertEqual(x["eligible"],["2020","2021"])
        self.assertEqual(x["marks"],[True,False,True])

    def test_guard_blocks_when_either_plan_is_draft(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            f16,f17,d16,d17 = (d/k for k in ("16","17","draft16","draft17"))
            for p in (f16,f17):
                p.write_text("Status: frozen fixture")
            with patch.multiple(S.A,PLAN=f16,DRAFT=d16,PEER_PLAN=f17,PEER_DRAFT=d17), \
                 patch.object(S.S,"unused_paths") as lock:
                for draft in (d17,d16):
                    draft.touch()
                    for scorer in (S,S.A):
                        with self.assertRaises(S.S.Refused):
                            scorer.run()
                    draft.unlink()
                lock.assert_not_called()

    def test_toy_replay_and_result_only_report(self):
        cfg = dict(hot_n=2,cost_bps_per_side=10,other_costs_bps=[5,20],shown_leverage=3,
                   random_draws=3,seed=17,min_rising_years=1,min_trades_per_year=1,
                   max_flagged_share_pct=100,min_years_above=1)
        p = settings()
        snap = {"known_at":T,"kept":[{"id":10,"symbol":"TEST"},{"id":20,"symbol":"ALT"}]}
        s = C.Series({ts(i):C.Bar(100,100,100) for i in range(-30,169)})
        tape = fut({-25:(90,90,90),-3:(120,120,120),0:(100,100,94),1:(90,100,100)},
                   payments={-8:0,0:0,1:.01})
        got = R.replay({"held":[snap],"viewed":[snap]},dict(TESTUSDT=s,ALTUSDT=s),
                       {X.pair:tape},cfg,p,p|cfg)
        y = got["years"]["2020"]["held"]
        self.assertEqual(y["swing"]["judged"]["idle_parts"],1)
        self.assertEqual(len(y["swing"]["judged"]["random_ends"]),3)
        self.assertGreater(y["swing"]["judged"]["end"],1)
        report = P.render(got|{"cutoff_utc":"2019-01-14T00:00:00+00:00",
                               "last_complete_funding_week_monday_utc":"2019-01-07"})
        self.assertIn("No costs or funding",report)
        self.assertIn("Rule S | Random Rule S median (range) | Hot hold | All live short",report)
        self.assertIn("began Monday 2019-01-07 UTC",report)
        with_roster = R.replay({"held":[snap],"viewed":[snap]},dict(TESTUSDT=s,ALTUSDT=s),
                               {X.pair:tape},cfg,p,p|cfg,us_roster=snap["kept"])
        report = P.render(with_roster|{"cutoff_utc":"2019-01-14T00:00:00+00:00",
                                      "last_complete_funding_week_monday_utc":"2019-01-07"})
        self.assertIn("US-shortable roster, shown only",report)
        self.assertGreater(with_roster.pop("shown_us_shortable")["2020"]["end"],1)
        self.assertEqual(with_roster,got)

    def test_shown_roster_uses_spot_tie_id_and_never_replaces_ineligible_pick(self):
        cfg = settings(hot_n=2,cost_bps_per_side=10)
        roster = [{"id":30,"symbol":"THIRD","cmcRank":12},
                  {"id":20,"symbol":"ALT","cmcRank":6},
                  {"id":10,"symbol":"TEST","cmcRank":500}]
        series = C.Series({ts(i):C.Bar(100,100,100) for i in range(-30,169)})
        spot = {r["symbol"]+"USDT":series for r in roster}
        tape = fut({-25:(90,90,90),-3:(120,120,120),0:(100,100,94),1:(90,100,100)},
                   payments={-8:0,0:0,1:.01})
        tapes = {s:tape for s in spot}
        identity = {"spot":{(r["id"],r["symbol"]+"USDT") for r in roster},
                    "futures":{(10,"TESTUSDT"),(30,"THIRDUSDT")}}
        with patch.object(C,"year_windows",return_value=[(2020,T,ts(8))]):
            got = R.shown_us_short(roster,spot,tapes,cfg,identity)["2020"]
            self.assertEqual(got["rankable_coin_weeks"],3)
            self.assertEqual(got["hot_slots"],2)
            self.assertEqual(got["live_hot_slots"],1)
            self.assertEqual(got["idle_parts"],1)
            self.assertEqual(got["trades"],1)
            self.assertAlmostEqual(got["end"],1+(0.1+0.0094-0.0019)/2)
            tape.covered = ()
            observed = R.shown_us_short(roster,spot,tapes,cfg,identity)["2020"]
            self.assertEqual(observed,got)

    def test_shown_us_fees_lower_each_net_on_same_single_trade_gross(self):
        cfg = settings(hot_n=1,cost_bps_per_side=10,other_costs_bps=[5,20],us_costs_bps=[38,80],
                       shown_leverage=3,random_draws=3,seed=17,min_rising_years=1,
                       min_trades_per_year=1,max_flagged_share_pct=100,min_years_above=1)
        roster = [{"id":X.coin,"symbol":"TEST"}]
        snapshots = {label:[{"known_at":T,"kept":roster}] for label in ("held","viewed")}
        spot = {X.pair:C.Series({ts(i):C.Bar(100,100,100) for i in range(-30,169)})}
        tapes = {X.pair:fut({-25:(90,90,90),-3:(120,120,120),0:(100,100,94),1:(90,100,100)},
                           payments={-8:0,0:0,1:.01})}
        with patch.object(C,"year_windows",return_value=[(2020,T,ts(8))]):
            result = R.replay(snapshots,spot,tapes,cfg,cfg,cfg,us_roster=roster)
            old = R.replay(snapshots,spot,tapes,{k:v for k,v in cfg.items() if k!="us_costs_bps"},
                           cfg,cfg,us_roster=roster)
        fees = result["shown_us_entry_tier_fees"]
        self.assertEqual({k:v for k,v in result.items() if k!="shown_us_entry_tier_fees"},old)
        self.assertEqual(set(fees),{"held","viewed","us_roster"})
        for label,years in fees.items():
            t3,t1 = (years["2020"][k] for k in ("tier_3_taker","tier_1_taker"))
            judged = (old["shown_us_shortable"]["2020"] if label=="us_roster"
                      else old["years"]["2020"][label]["swing"]["judged"])
            self.assertEqual([judged["trades"],t3["trades"],t1["trades"]],[1,1,1])
            self.assertLess(t1["end"],t3["end"])
            self.assertLess(t3["end"],judged["end"])
            self.assertGreater(t1["fees"],t3["fees"])
            for key in ("price","funding","forced_adjustment"):
                self.assertEqual(t1[key],t3[key])
                self.assertEqual(t3[key],judged[key])
            self.assertNotEqual(t1["price"],0)
            self.assertNotEqual(t1["funding"],0)
        report = P.render(result|{"cutoff_utc":"2019-01-14T00:00:00+00:00",
                                  "last_complete_funding_week_monday_utc":"2019-01-07"})
        self.assertIn("shown only, US entry-tier fees",report)
        for name in ("Held-back","Viewed","US-shortable roster"):
            self.assertIn(f"| 2020 | {name} | 38 bps |",report)

    def test_roster_pin_uses_measured_only_and_drops_four(self):
        import json
        from hashlib import sha256
        u = S.A.U
        roster = {"measured_count":5,"measured_coins":[{"coin":x} for x in ("TEST","USDC","PAXG","BTC","ETH")],
                  "stated_only":[{"coin":"NOTMEASURED"}]}
        raw = json.dumps(roster).encode()
        with patch.multiple(u,SHA256=sha256(raw).hexdigest(),IDS={"TEST":10}):
            self.assertEqual(u.rows(raw),[{"id":10,"symbol":"TEST"}])
            with self.assertRaises(ValueError):
                u.rows(raw+b" ")
