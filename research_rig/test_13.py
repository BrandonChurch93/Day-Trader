"""Invented fixtures for replay 13. Never loads the real archive."""

from datetime import date
import io
import json
from contextlib import redirect_stderr
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

try:
    from . import common_13 as C
    from . import fetch_13 as F
    from . import score_13 as S
except ImportError:
    import common_13 as C
    import fetch_13 as F
    import score_13 as S

H = F.HOUR
T = F.stamp(date(2020,1,6))
A = C.Asset(10,"AAAUSDT")


def settings(**kwargs):
    p = {"start":"2020-01-01","end":"2020-01-14","universe_top_n":50,
         "rise_days":1,"dip_lookback_hours":3,"dip_pct":5,"take_pct":5,
         "stop_pct":5,"max_hold_hours":24,"cost_bps_per_side":15,
         "other_costs_bps":[5,30],"shown_leverage":3,"judged_leverage":1,
         "liquidation_drop_pct":30,"financing_bps_per_8h":3,
         "financing_interval_hours":8,"random_draws":3,"seed":13,
         "min_years_above":2,"hot_n":5,"random_percentile":75,
         "max_flagged_share_pct":5,"min_trades_per_year":10,"new_trials":2,"max_missing_hours":0}
    p.update(kwargs)
    return p


def toy(changes=None, omit=(), last=8):
    x = {T+i*H:C.Bar(90,90,90) for i in range(-30,last+1) if i not in omit}
    for i, prices in (changes or {}).items():
        x[T+i*H] = C.Bar(*prices)
    return C.Series(x)


def signal():
    return {-3:(110,110,110),-1:(100,100,100)}


def row(id, symbol):
    return {"id":id,"symbol":symbol,"name":symbol}


class Replay13Test(unittest.TestCase):
    def test_plan_config_keys(self):
        config = F.config()  # Definition text only, no tape.
        S.verify_parameters(config)
        self.assertEqual(config["max_missing_hours"],6)
        S.verify_parameters(settings())
        for bad in (settings(hot_n=0),settings(max_missing_hours=-1),settings(max_missing_hours=True)):
            with self.assertRaises(S.Refused):
                S.verify_parameters(bad)

    def test_mixed_archive_timestamp_units(self):
        self.assertEqual(F.open_epoch(T*1000),T)
        self.assertEqual(F.open_epoch(T*1_000_000),T)
        z = io.BytesIO()
        with zipfile.ZipFile(z,"w") as out:
            out.writestr("toy.csv",f"open_time,open\n{T*1000},9\n")
        self.assertEqual(list(F.zip_rows(z.getvalue())),[[str(T*1000),"9"]])

    def test_ticker_reuse_has_disjoint_identity(self):
        old = F.segments(row(4172,"LUNA"))
        new, = F.segments(row(20314,"LUNA"))
        self.assertEqual((old[0][2],old[1][2],new[2]),("LUNAUSDT","LUNCUSDT","LUNAUSDT"))
        self.assertLess(old[0][1],new[0])
        self.assertEqual(F.segments(row(16086,"BTT"))[0][2],"BTTCUSDT")
        self.assertEqual(F.segments(row(28298,"BEAM"))[0][2],"BEAMXUSDT")
        self.assertEqual(F.segments(row(1720,"MIOTA"))[0][2],"IOTAUSDT")

    def test_snapshots_known_at_monday_and_missing_flag(self):
        a = {"known_at":T-H,"kept":[row(10,"AAA")]}
        b = {"known_at":T+H,"kept":[row(20,"BBB")]}
        missing = {"known_at":T+2*H,"kept":[]}
        market = {"AAAUSDT":toy(), "BBBUSDT":toy()}
        self.assertEqual(C.weekly_universe([a,b,missing],market,T,settings())[1],[A])
        got, ranked, flag = C.weekly_universe([a,b,missing],market,T+2*H,settings())
        self.assertEqual([v.coin for v in got],[20])
        self.assertTrue(flag)

    def test_rank_ties_negative_and_gap(self):
        a,b,c = [row(i,t) for i,t in ((20,"CCC"),(10,"AAA"),(30,"DDD"))]
        s = toy({-1:(80,80,80)})
        no_history = toy(omit=(-12,))
        market = {"CCCUSDT":s,"AAAUSDT":s,"DDDUSDT":no_history}
        snap = {"known_at":T,"kept":[a,b,c]}
        diagnostics = {}
        listed, ranked, flag = C.weekly_universe([snap],market,T,settings(),diagnostics)
        self.assertEqual([x.coin for x in listed],[20,10,30])
        self.assertEqual([x.coin for x in ranked],[10,20])
        self.assertFalse(flag)
        self.assertEqual(diagnostics,{"no_prior_hour":0,"incomplete_history":1,"not_rankable":1,
                                      "duplicate_pair_count":0,"duplicate_pair_exclusions":0})

    def test_coin_exclusions_use_ids(self):
        self.assertTrue({34387,39120,33793,5068,7129,4056,18579,2087,4269,3351,
                         2907,4842,2027} <= F.EXCLUDE.keys())
        self.assertFalse({1839,6953,2694,2700,1817} & F.EXCLUDE.keys())

    def test_current_bar_not_used_to_enter(self):
        s = toy({**signal(),0:(101,75,80),1:(95,95,95)})
        self.assertTrue(C.dip_signal(s,A,T,settings()))
        missing = toy(signal(),omit=(-11,))
        self.assertFalse(C.dip_signal(missing,A,T,settings()))
        # Exact first fill price, not the known previous close or the current low.
        got = C.swing_week(s,A,T,T+H,0,1,settings())
        self.assertAlmostEqual(got.factor,95/101)
        self.assertEqual(got.reasons,("week_end",))

    def test_seven_day_rank_and_dip_require_ends_and_allow_up_to_six_gaps(self):
        p = settings(rise_days=7,max_missing_hours=6)
        snap = {"known_at":T,"kept":[row(10,"AAA")]}
        def rank_and_trace(omit):
            bars = {T+i*H:C.Bar(90,90,90) for i in range(-169,4) if i not in omit}
            bars.update({T+i*H:C.Bar(*px) for i,px in signal().items() if i not in omit})
            series = C.Series(bars)
            _, ranked, _ = C.weekly_universe([snap],{"AAAUSDT":series},T,p)
            trace = []
            C.swing_week(series,A,T,T+2*H,0,1,p,trace)
            return ranked, [(t, action) for t,action,_,_ in trace if t == T]
        valid = ([A],[(T,"buy")])
        self.assertEqual(rank_and_trace((-20,)),valid)
        six = (-20,-21,-22,-23,-24,-25)
        self.assertEqual(rank_and_trace(six),valid)
        for bad in ((*six,-26),(-169,),(-1,)):
            with self.subTest(omit=bad):
                self.assertEqual(rank_and_trace(bad),([],[]))

    def test_dip_high_uses_only_existing_prior_closes_in_24_hour_window(self):
        p = settings(dip_lookback_hours=24,max_missing_hours=6)
        prices = {-26:(180,180,180),-20:(106,106,106),-1:(100,100,100),
                  0:(100,90,160,165)}
        self.assertTrue(C.dip_signal(toy(prices,omit=(-2,)),A,T,p))
        # With the only qualifying in-window high missing, neither an earlier
        # high nor the signal/current bar substitutes for it.
        without_high = {t:px for t,px in prices.items() if t != -20}
        self.assertFalse(C.dip_signal(toy(without_high,omit=(-2,-20)),A,T,p))

    def test_missing_bars_flags_tolerance_but_delays_independently(self):
        p = settings(max_missing_hours=1)
        prices = {**signal(),0:(100,100,100),1:(100,100,100),
                  2:(100,100,100),3:(100,100,100),4:(100,100,100),5:(100,100,100)}
        for algo in (C.hold_week,C.swing_week):
            for omitted,flagged in (((1,),False),((1,2),True),((4,),True)):
                bars = toy({i:px for i,px in prices.items() if i not in omitted},omit=omitted)
                self.assertEqual(algo(bars,A,T,T+4*H,0,1,p).flagged,flagged)
        missing_exit = toy({**signal(),0:(100,100,100)},last=0)
        self.assertTrue(C.swing_week(missing_exit,A,T,T+H,0,1,p).flagged)

    def test_monday_hold_waits_through_six_hours_but_not_into_next_week(self):
        p = settings(max_missing_hours=6)
        entry, exit_at = T+6*H,T+8*H
        before = tuple(range(6))
        s = toy({6:(100,100,100),8:(110,110,110)},omit=before)
        events = []
        got = C.hold_week(s,A,T,exit_at,.0015,1,p,events)
        self.assertEqual(events[:2],[(T,"queue_entry",None,1),(entry,"buy",100,1)])
        self.assertAlmostEqual(got.factor,1.1*(1-.0015)/(1+.0015))
        self.assertFalse(got.flagged)
        late = toy({7:(100,100,100),8:(110,110,110)},omit=(*before,6))
        for tape, end in ((late,exit_at),(s,entry)):
            trace = []
            skipped = C.hold_week(tape,A,T,end,0,1,p,trace)
            self.assertEqual((skipped.factor,skipped.reasons,skipped.flagged),(1,(),True))
            self.assertEqual(trace[0],(T,"queue_entry",None,1))
            self.assertFalse(any(e[1]=="buy" for e in trace))

    def test_ranked_pool_drives_all_and_random_and_delayed_hold_entry(self):
        p = settings(hot_n=1,max_missing_hours=6)
        snap = {"known_at":T,"kept":[row(10,"AAA"),row(20,"BBB"),row(30,"CCC")]}
        a = toy({-1:(110,110,110),6:(100,100,100),168:(120,120,120)},omit=range(6),last=168)
        b = toy({168:(900,900,900)},omit=(-25,),last=168)
        c = toy({-1:(95,95,95),0:(100,100,100),168:(90,90,90)},last=168)
        y = C.replay([snap],{"AAAUSDT":a,"BBBUSDT":b,"CCCUSDT":c},p)["years"]["2020"]
        cost = (1-.0015)/(1+.0015)
        self.assertEqual((y["weeks"][0]["listed"],y["weeks"][0]["rankable"]),(3,2))
        self.assertAlmostEqual(y["fixed"]["A"]["gain"],1.2*cost-1)
        self.assertAlmostEqual(y["fixed"]["all"]["gain"],1.05*cost-1)
        self.assertEqual(y["fixed"]["all"]["trades"],2)
        for gain in y["random"]["A"]["gains"]:
            self.assertTrue(any(abs(gain-(factor*cost-1)) < 1e-12 for factor in (1.2,.9)))

    def test_same_pair_uses_higher_cmc_rank_and_counts_duplicate_weeks(self):
        p = settings(start="2024-09-23",end="2024-10-01",rise_days=7,max_missing_hours=6)
        t = F.stamp(date(2024,9,23))
        old = {**row(3890,"MATIC"),"cmcRank":30}
        new = {**row(28321,"POL"),"cmcRank":29}
        tape = C.Series({t+i*H:C.Bar(100,100,100) for i in range(-169,169)})
        data = {"POLUSDT":tape}
        result = C.replay([{"known_at":t,"kept":[old,new]}],data,p)
        week, = result["years"]["2024"]["weeks"]
        self.assertEqual(week["selected"],[{"id":28321,"pair":"POLUSDT"}])
        self.assertEqual((week["listed"],week["rankable"],week["duplicate_pair_count"]),(1,1,1))
        self.assertEqual(result["years"]["2024"]["duplicate_pair_weeks"],1)
        self.assertEqual(result["diagnostics"]["duplicate_pair_weeks"],1)

    def test_stop_take_timeout_and_precedence(self):
        p = settings(max_hold_hours=1)
        for close, reason in ((105,"take"),(95,"stop"),(100,"timeout")):
            with self.subTest(reason=reason):
                s = toy({**signal(),0:(100,min(100,close),close),1:(97,90,99)})
                got = C.swing_week(s,A,T,T+2*H,0,1,p)
                self.assertEqual(got.reasons[0],reason)
        got = C.swing_week(s,A,T,T+H,0,1,p)
        self.assertEqual(got.reasons,("week_end",))
        self.assertAlmostEqual(got.factor,.97)

    def test_no_reentry_at_sale_open(self):
        s = toy({**signal(),0:(100,95,95),1:(90,90,90),2:(90,90,90)})
        got = C.swing_week(s,A,T,T+2*H,0,1,settings())
        self.assertEqual(got.reasons,("stop",))
        self.assertAlmostEqual(got.factor,.9)

    def test_b_monday_resplit_can_sell_then_buy_same_coin_and_pays_both(self):
        p = settings()
        fee = .0015
        s = toy({**signal(),0:(100,100,100),1:(100,100,100),2:(104,104,104),
                 3:(98,98,98),4:(101,101,101),5:(102,102,102)})
        s = C.Series({k-4*H:v for k,v in s.bars.items()})
        prev, next_ = [], []
        t = T
        first = C.swing_week(s,A,t-4*H,t,fee,1,p,prev)
        second = C.swing_week(s,A,t,t+H,fee,1,p,next_)
        self.assertEqual(prev[-1][:3],(t,"week_end",101))
        self.assertEqual(next_[0][:3],(t,"buy",101))
        account = C.Account()
        account.advance(t-4*H,1,[first],False)
        account.advance(t,1,[second],False)
        self.assertAlmostEqual(account.finish()["gain"]+1,1.02*((1-fee)/(1+fee))**2)

    def test_dual_touch_uses_close_and_takes_next_open(self):
        bar = (100,90,106,110)
        s = toy({**signal(),0:bar,1:(103,102,103)})
        self.assertLessEqual(s.bars[T].l,95)
        self.assertGreaterEqual(s.bars[T].h,105)
        t = []
        result = C.swing_week(s,A,T,T+2*H,0,1,settings(),t)
        self.assertEqual(t[1][:3],(T+H,"take",103))
        self.assertEqual(result.reasons,("take",))

    def test_future_bar_changes_do_not_change_monday_rank_entry_or_prefix(self):
        p = settings(rise_days=7,hot_n=2)
        snap = {"known_at":T,"kept":[row(10,"AAA"),row(20,"BBB"),row(30,"CCC")]}
        def prefix(is_changed):
            market = {}
            for i, pair in enumerate(("AAAUSDT","BBBUSDT","CCCUSDT")):
                bars = {T+k*H:C.Bar(90,90,90) for k in range(-169,10)}
                bars[T-3*H] = C.Bar(120,120,120)
                bars[T-H] = C.Bar(100+i,100+i,100+i)
                bars[T] = C.Bar(101,69,140,150) if is_changed else C.Bar(101,95,101,102)
                if is_changed:
                    bars.update({T+k*H:C.Bar(200+i*k,100,210,220) for k in range(1,10)})
                market[pair] = C.Series(bars)
            _, ranked, _ = C.weekly_universe([snap],market,T,p)
            events = []
            outcomes = []
            for a in ranked[:2]:
                trace = []
                outcomes.append(C.swing_week(market[a.pair],a,T,T+4*H,.0015,1,p,trace))
                events += [(a.coin,*event) for event in trace if event[0] <= T]
            account = C.Account()
            account.advance(T,2,outcomes,False)
            return [a.coin for a in ranked],events,account.cash
        before, after = prefix(False),prefix(True)
        self.assertEqual(before,after)
        self.assertEqual(before,([30,20,10],[(30,T,"buy",101,1),(20,T,"buy",101,1)],0))

    def test_future_delayed_fill_or_terminal_mark_cannot_change_resplit(self):
        p, end = settings(), T+2*H
        def prefix(series, algo):
            events = []
            outcome = algo(series,A,T,end,0,1,p,events)
            acct = C.Account()
            acct.advance(T,2,[outcome],False)
            acct.advance(end,2,[C.Outcome(1,end+H,("take",))],False)
            return ([e for e in events if e[0] <= end],acct.cash), outcome
        base = {**signal(),0:(100,100,100),1:(100,100,100)}
        temporary = toy({**base,3:(120,120,120)},omit=(2,),last=3)
        later = toy({**base,4:(130,130,130)},omit=(2,3),last=4)
        permanent = toy(base,last=1)
        for algo in (C.hold_week,C.swing_week):
            a, fill = prefix(temporary,algo)
            b, late = prefix(later,algo)
            c, mark = prefix(permanent,algo)
            self.assertEqual(a,b)
            self.assertEqual(b,c)
            self.assertEqual(a[1],.25)
            self.assertEqual((fill.release,late.release,mark.release),(end+H,end+2*H,None))

    def test_entry_bar_leverage_liquidation_first(self):
        s = toy({**signal(),0:(100,70,105),1:(110,110,110)})
        a = C.swing_week(s,A,T,T+H,0,3,settings())
        b = C.swing_week(s,A,T,T+H,0,1,settings())
        self.assertEqual((a.factor,a.reasons),(0,("liquidation",)))
        self.assertAlmostEqual(b.factor,1.1)

    def test_delayed_fill_not_reinvested_before_release(self):
        s = toy({0:(100,100,100),3:(120,120,120)},omit=(2,))
        r = C.hold_week(s,A,T,T+2*H,0,1,settings())
        self.assertEqual(r.release,T+3*H)
        self.assertTrue(r.flagged)
        a = C.Account()
        a.advance(T,1,[r],False)
        a.advance(T+2*H,1,[C.Outcome(5,T+3*H,("week_end",))],False)
        self.assertEqual(a.finish()["trades"],1)
        self.assertAlmostEqual(a.finish()["gain"],.2)

    def test_terminal_gap_cannot_use_reused_ticker(self):
        asset = C.Asset(10,"AAAUSDT",-10**12,T+2*H)
        s = toy({0:(100,100,100),1:(100,90,90),3:(900,900,900)},omit=(2,))
        r = C.hold_week(s,asset,T,T+2*H,0,1,settings())
        self.assertEqual((r.reasons,r.flagged),(("last_close",), True))
        self.assertAlmostEqual(r.factor,.9)

    def test_costs_funding_and_idle_parts(self):
        p = settings()
        self.assertAlmostEqual(C.sale_factor(100,100,8*H,.0015,1,p),.9985/1.0015)
        self.assertAlmostEqual(C.sale_factor(100,100,8*H,0,3,p),1-2*.0003)
        a = C.Account()
        a.advance(T,5,[C.Outcome(1.5,T+H,("take",))],False)
        self.assertAlmostEqual(a.finish()["gain"],.1)

    def test_4h_funding_prorates_borrowed_two_thirds(self):
        s = toy({**signal(),0:(100,100,100),1:(100,100,100),
                 2:(100,100,100),3:(100,100,100),4:(100,100,100)})
        got = C.swing_week(s,A,T,T+4*H,0,3,settings())
        self.assertEqual(got.reasons,("week_end",))
        self.assertAlmostEqual(got.factor,1-2*.0003*4/8)

    def test_carried_list_flags_coin_parts_but_not_unfilled_hot_slots(self):
        account = C.Account()
        account.advance(T,5,[C.Outcome(1,T+H,())],True)
        self.assertEqual(account.finish()["part_weeks"],5)
        self.assertEqual(account.finish()["flagged_part_weeks"],1)

    def test_b_flags_later_week_gap_even_after_liquidation(self):
        s = toy({**signal(),0:(100,65,103)},omit=(3,))
        r = C.swing_week(s,A,T,T+4*H,0,3,settings())
        self.assertEqual(r.reasons,("liquidation",))
        self.assertTrue(r.flagged)

    def test_missing_boundary_bar_does_not_flag_earlier_flat_part(self):
        s = toy(omit=(3,))
        result = C.swing_week(s,A,T,T+3*H,0,1,settings())
        self.assertFalse(result.flagged)

    def test_calendar_starts_first_monday_and_partial_year(self):
        ys = dict((y,(a,b)) for y,a,b in C.year_windows(settings(end="2026-11-24")))
        self.assertEqual(ys[2020],(T,F.stamp(date(2021,1,1))))
        self.assertEqual(ys[2026][1],F.stamp(date(2026,11,23)))
        self.assertEqual(len(ys),7)

    def test_benchmark_and_random_path_determinism(self):
        s = toy({0:(100,100,100),168:(108,108,108)},last=168)
        snap = {"known_at":T,"kept":[row(10,"AAA")]}
        data = {"AAAUSDT":s,"BTCUSDT":s}
        p = settings()
        one = C.replay([snap],data,p)
        self.assertEqual(one,C.replay([snap],data,p))
        rs = one["years"]["2020"]
        self.assertEqual(rs["random"]["A"]["gains"],[rs["fixed"]["A"]["gain"]]*3)
        self.assertNotEqual(rs["random"]["A"]["gains"],rs["random"]["B"]["gains"])
        for c in (5,15,30):
            tag = "" if c == 15 else f"_cost_{c}"
            self.assertIn("all"+tag,rs["fixed"])
            self.assertAlmostEqual(rs["BTC_costs"][str(c)]["net"],
                                   C.sale_factor(100,108,168*H,c/10_000,1,p)-1)
            for kind in ("A","B"):
                self.assertEqual(rs["random_costs"][str(c)][kind]["gains"],
                                 [rs["fixed"][kind+tag]["gain"]]*3)
        self.assertEqual([k for k in rs["fixed"] if "leveraged" in k],["B_leveraged"])

    def test_judgment_shared_years_strict_and_quality_gates(self):
        def yr(a,b,cut,flags=0,trades=10):
            return {"fixed":{"A":{"gain":a,"trades":trades,"flagged_share_pct":flags},"all":{"gain":b}},
                    "random":{"A":{"percentile":cut}}}
        p = settings()
        rows = {"1":yr(.3,.2,.25),"2":yr(.1,-.2,.05),"3":yr(.3,.2,.3),
                "4":yr(.5,-.2,.1,6),"5":yr(.5,-.2,.1,trades=9)}
        self.assertEqual(C.judge(rows,"A",p)["finding"],"supported")
        self.assertEqual(C.judge(rows,"A",p)["above_both"],["1","2"])
        del rows["2"]
        self.assertEqual(C.judge(rows,"A",p)["finding"],"paid only when coins rose")
        self.assertEqual(C.judge({"1":yr(0,.1,.2)},"A",p)["finding"],"not paid")

    def test_lock_draft_duplicate_and_durable_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, local, durable = (Path(tmp)/v for v in ("result","local","durable"))
            with self.assertRaises(S.Refused):
                S.guard("Status: DRAFT, later frozen",result,local,durable,{})
            self.assertFalse(durable.exists())
            S.guard("Status: frozen 2026-11-25",result,local,durable,{"toy":True})
            local.unlink()
            with self.assertRaises(S.Refused):
                S.guard("Status: frozen",result,local,durable,{})

    def test_scorer_requires_draft_gate_before_any_archive_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, draft = (Path(tmp)/v for v in ("plan.md","draft.md"))
            with patch.multiple(S,PLAN=plan,DRAFT=draft), patch.object(S,"load_verified_data") as lp:
                for status in ("Status: DRAFT","Status: FROZEN","Status: frozenish"):
                    plan.write_text(status)
                    with self.assertRaises(S.Refused):
                        S.run()
                plan.write_text("Status: frozen")
                draft.symlink_to("missing")
                with self.assertRaises(S.Refused):
                    S.run()
                draft.unlink()
                draft.write_text("Status: frozen")
                with self.assertRaises(S.Refused):
                    S.run()
                plan.unlink()
                with self.assertRaises(S.Refused):
                    S.run()
                lp.assert_not_called()

    def test_one_shot_end_to_end_using_only_invented_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            p = settings(universe_top_n=1, hot_n=1)
            plan, config = base/"plan.md", base/"cfg.yaml"
            plan.write_text("Status: frozen fixture\n")
            config.write_text(F.yaml.safe_dump({"replay_13_plan":{"value":p}}))
            snapshot_blob = b"invented historic snapshot, never fetched"
            F.write(base/"cmc/20200105.html.gz",snapshot_blob)
            F.put_json(base/"snapshots.json",[{"date":"2020-01-05","known_at":T,
                       "kept":[row(10,"AAA")],"top_raw":[row(10,"AAA")],
                       "sha256":S.digest(snapshot_blob)}])
            records = {}
            for pair in ("AAAUSDT","BTCUSDT"):
                key = f"data/spot/monthly/klines/{pair}/1h/{pair}-1h-2020-01.zip"
                buf = io.BytesIO()
                with zipfile.ZipFile(buf,"w") as z:
                    z.writestr("invented.csv","".join(
                        f"{(T+i*H)*1000},100,100,100,100\n" for i in range(-30,169)))
                F.write(base/"archives"/key,buf.getvalue())
                records[key] = {"sha256":S.digest(buf.getvalue()),"n":199}
            F.put_json(base/"manifest.json",{"errors":[],"archives":records,"excluded_ids":F.EXCLUDE,
                       "collection_parameters":F.collection_parameters(p),"pair_mappings":F.MANUAL,
                       "snapshot_sha256":S.digest((base/"snapshots.json").read_bytes())})
            result = base/"results.json"
            with patch.multiple(S,PLAN=plan,DRAFT=base/"draft.md",CONFIG=config,RESULT=result,LOCAL_LOCK=base/"local.lock",
                                DURABLE_LOCK=base/"durable.lock"), patch.object(F,"DATA",base), patch("builtins.print"):
                S.run()
                written = json.loads(result.read_text())
                self.assertEqual(written["inputs"]["archives"],2)
                self.assertEqual(written["admitted_coins"][0]["months"],["2020-01"])
                self.assertEqual(written["years"]["2020"]["fixed"]["A"]["trades"],1)
                self.assertLess(written["years"]["2020"]["fixed"]["A"]["gain"],0)
                with self.assertRaises(S.Refused):
                    S.run()

    def test_failed_run_keeps_input_fingerprints_in_both_locks(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            plan, cfg, result, local, durable = (
                base/name for name in ("plan","cfg","result","local","durable"))
            plan.write_text("Status: frozen fixture\n")
            cfg.write_text(F.yaml.safe_dump({"replay_13_plan":{"value":settings()}}))
            F.put_json(base/"manifest.json",{"invented":True})
            F.put_json(base/"snapshots.json",[])
            hashes = {f"{key}_sha256":S.digest((base/f"{key}.json").read_bytes())
                      for key in ("manifest","snapshots")}
            original_guard = S.guard
            def changed_after_lock(*args):
                original_guard(*args)
                F.put_json(base/"manifest.json",{"invented":"changed"})
            with patch.multiple(S,PLAN=plan,DRAFT=base/"draft",CONFIG=cfg,RESULT=result,
                                LOCAL_LOCK=local,DURABLE_LOCK=durable,guard=changed_after_lock), \
                 patch.object(F,"DATA",base), redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(S.Refused,"metadata changed"):
                    S.run()
                with self.assertRaisesRegex(S.Refused,"previous attempt"):
                    S.run()
            self.assertFalse(result.exists())
            for lock in (local,durable):
                self.assertEqual(json.loads(lock.read_text())["inputs"],hashes)
