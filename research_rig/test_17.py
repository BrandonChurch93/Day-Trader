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

    def test_contract_signal_does_not_cross_identity_or_use_mark(self):
        t = fut({-25:(90,90,90),-3:(120,120,120),0:(80,80,80)})
        self.assertTrue(R.prepare(t,X,T,ts(2),settings()).signals[0])
        self.assertFalse(R.prepare(t,C.Asset(10,X.pair,ts(-22),ts(10)),T,ts(2),settings()).signals[0])
        control = fut({-25:(90,90,90),0:(80,500,500)},marks={-3:(120,120,120)})
        self.assertFalse(R.prepare(control,X,T,ts(2),settings()).signals[0])

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
        ac.add([R.Part(a,False),R.Part(b,False)],np.array([[0,1]]),2,False)
        self.assertEqual(ac.value[0],0)
        self.assertEqual(ac.row()["trades"],1)
        self.assertAlmostEqual(ac.row()["price"],-1.2)

    def test_idle_is_not_a_flag_even_for_carried_list(self):
        path = np.zeros((3,7))
        path[-1,[0,1,5]] = [.1,.1,1]
        ac = R.Accounts(1)
        ac.add([R.Part(path,False)],np.array([[0,1,1,1,1]]),5,True)
        r = ac.row()
        self.assertAlmostEqual(r["end"],1.02)
        self.assertEqual((r["idle_parts"],r["flagged_parts"],r["flag_share_pct"]),(4,1,20))

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
        self.assertIn("No costs or funding",P.render(got|{"cutoff_utc":"invented"}))
