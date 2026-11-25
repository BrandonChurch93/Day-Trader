"""TM07 fixtures only. No real tape, session registry, provider or HTTP listener."""
import copy
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from timemachine import desk as D, desk_orders as O, perp as P, perp_fast as F, score_tm07 as S, server, tm06, weights as W

A, B, BTC = "AAA/USD", "BBB/USD", "BTC/USD"
T = 1784505600  # hourly anchor; prices and headlines below are invented
TOKEN = "fake-boss-bearer-" * 4


def world(minutes=None):
    cfg = dict(tm_perp_funding_files={}, tm_perp_fee_bps_per_side={"default": 12},
               tm_perp_half_spread_bps={"default": 4}, tm_perp_maintenance={"default": 0.05},
               tm_perp_funding_hours={"default": 1}, tm_perp_fallback_rate_per_day=0.0003,
               tm_perp_closeout_penalty=0.01, tm_perp_min_change=0.02, tm_account_start_usd=1000.0,
               tm_weights_why_max_chars=1000, tm_weights_sum_tolerance=0.000001,
               tm_weights_twin_draws=4, tm_weights_twin_seed=1, tm_weights_pass_percentile=90,
               tm06_plan={"main_fee_bps": 12, "carried_leverage": [2, 3]}, tm_perp_fee_levels_bps=[1, 12, 25])
    symbols = [A, B]
    if minutes is None:
        minutes = [(t, s, 100, 104 if (s, t) == (A, T+60) else 101, 97 if (s,t) == (B,T+120) else 99, 100)
                   for t in range(T, T+2*3600, 60) for s in [A, B, BTC]]
    rows, evidence = [], []
    for i in range(2):
        t = T+i*3600
        rows.append(dict(marks={s:100 for s in [A,B,BTC]},
                         fills={s:next(([P.iso(D.wall(r[0])), r[2]] for r in minutes if r[0] >= t and r[0] < t+3600 and r[1] == s), None)
                                for s in [A,B,BTC]}))
        common = dict(symbol=A, published=t-60, known_at=t-60, vintage="original", licensed=True)
        evidence.append([dict(common, kind="price", id=f"p{i}", value={"price":100}),
                         dict(common, symbol=B, kind="price", id=f"bp{i}", value={"price":100}),
                         dict(common, kind="news", id=f"n{i}", value={"headline":"A made-up notice"}, primary=True),
                         dict(common, kind="news", id=f"future{i}", known_at=t+1, primary=True),
                         dict(common, kind="news", id=f"mirror{i}", origins=["wire","wire"]),
                         dict(common, kind="attention", id=f"estimated{i}", period_end=t-60, vintage="assumed_lag"),
                         dict(common, kind="bars", id=f"unfinished{i}", period_end=t+60),
                         dict(common, kind="news", id=f"unlicensed{i}", primary=True, licensed=False)])
    return dict(wakes=[T,T+3600], end=T+7200, symbols=symbols, watch=symbols, benchmark=BTC, opening={},
                rows=rows, minutes=minutes, end_marks={s:100 for s in [A,B,BTC]}, evidence=evidence,
                cfg=cfg, params=P.p_params([A,B,BTC], cfg, funding={A:{T:0.001}, B:{T:0.0}}), gross=1)


def info(s, r="boss"):
    payload = s.handle(r, "next", {})
    return payload, payload["wake_key"]


def condition(wake, symbol=A, **kw):
    item = dict(symbol=symbol, direction="above", price=102, hours=2, weight=0.25, evidence_ids=["p0"])
    item.update(kw)
    return O.normalize_conditions([item], {symbol:100}, [symbol], wake, wake+7200, 6, 1)


class DeskTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tm07-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def create(self, arm, scout=None, spec=None, sid=None):
        spec = spec or world()
        path = self.root / (sid or f"TM07-test-{arm}")
        tokens = {r: "fake-" + r*7 for r in D.SCOUTS} if arm == "scout" else {"boss":TOKEN}
        D.create_desk(path, spec, arm, D.BOSSES[0], tokens, scout)
        return D.DeskSession(path)

    def test_b01_later_bar_cannot_change_quote_or_condition(self):
        class Tape:
            def _conn(self):
                return conn
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        conn.execute("CREATE TABLE bars(symbol,tf,t,c)")
        conn.executemany("INSERT INTO bars VALUES(?,?,?,?)", [(A,"1Min",T-86400,50),(A,"30Min",T-1800,100)])
        def quote():
            mark = D.mark_as_of(Tape(), A, T)
            return mark, condition_at(mark)
        def condition_at(mark):
            return O.normalize_conditions([dict(symbol=A,direction="above",pct=2,hours=1,weight=.2)],
                                          {A:mark},[A],T,T+3600,6,1)[A]["level"]
        self.assertEqual(quote(),(100,102))
        conn.execute("INSERT INTO bars VALUES(?,?,?,?)",(A,"1Min",T+60,200))
        self.assertEqual(quote(),(100,102))

    def test_b03_off_hour_funding_never_rounded_back(self):
        class Tape:
            def _conn(self):
                return conn
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        conn.execute("CREATE TABLE funding(symbol,venue,t,rate,interval_hours)")
        conn.execute("INSERT INTO funding VALUES(?,?,?,?,?)",(A,"toy",T+1,.05,1))
        cfg = dict(world()["cfg"], tm_fast_funding_venue={"default":"toy"})
        read = getattr(D,"desk_funding",tm06.fast_funding)
        result = read(Tape(),[A],cfg,D.wall(T),D.wall(T+7200))
        self.assertEqual(result[0][A],{T+3600:.05})
        self.assertEqual(result[2][A][T+3600],T+1)

    def test_s01_gap_keeps_exposure_and_funding(self):
        minutes = [x for x in world()["minutes"] if x[0] != T+3600]
        spec = world(minutes)
        s = self.create("A", spec=spec)
        bundles = [{"weights":{A:.2},"exits":None},{"weights":None,"exits":None}]
        meta = dict(wakes=[P.iso(D.wall(t)) for t in spec["wakes"]],end_utc=P.iso(D.wall(spec["end"])),opening={})
        table = dict(rows=spec["rows"],end_marks=spec["end_marks"])
        legacy = P.run_perp(meta,table,[(x["weights"],x["exits"]) for x in bundles],s.pp,s.minutes,spec["cfg"])
        got = S.replay(s,bundles)
        self.assertEqual(got["book"],legacy[0])
        self.assertEqual(got["book"]["held_seconds"],7200)

    def test_b02_immediate_cannot_size_from_a_later_open(self):
        def execute(later):
            spec = world()
            book = P.new_book(1000)
            book.update(cash=500, qty={B:5}, target={B:.5}, last_px={A:100,B:100})
            fills = {A:[P.iso(D.wall(T)),100],B:[P.iso(D.wall(T+60)),later]}
            bars = P.Minutes([(T,A,100,100,100,100),(T+60,A,105,105,105,105),
                               (T+60,B,later,later,later,later)])
            rec,_,_ = O.step(book,dict(weights={A:.4,B:.4}),dict(marks={A:100,B:100},fills=fills),
                            spec["params"],bars,T,T+120,True,{},1)
            return rec
        for px in (100,200):
            with self.subTest(later_open=px):
                rec = execute(px)
                self.assertTrue(rec["trades"])
                self.assertFalse(any(t["fill_utc"] == P.iso(D.wall(T)) for t in rec["trades"]))
                self.assertTrue(all(t["fill_utc"] == P.iso(D.wall(T+60)) for t in rec["trades"]))

    def test_b06_actual_rebalance_blocks_same_open_condition(self):
        spec = world()
        book = P.new_book(1000)
        book.update(cash=900, qty={A:1}, target={A:.2}, last_px={A:100,B:100})
        active = condition(T-3600, weight=.4)
        active[A]["observed"] = T
        bundle = dict(weights={A:.2,B:.2},keep=[active[A]["id"]])
        rec,_,ev = O.step(book,bundle,spec["rows"][0],spec["params"],P.Minutes(spec["minutes"]),T,T+3600,False,active,1)
        self.assertIn(A,[x["symbol"] for x in rec["trades"]])
        self.assertEqual([(x["kind"],x.get("reason")) for x in ev],[("cancelled","immediate_fill")])

    def test_b07_risk_uses_all_simultaneous_opens_before_filling(self):
        spec = world()
        for opening, expected in ((160,"gross_limit"),(300,"maintenance")):
            book = P.new_book(1000)
            book.update(cash=1600,qty={B:-6},target={B:-.6},last_px={A:100,B:100})
            active = condition(T-3600,weight=.35)
            active[A]["observed"] = T
            engine = O.Orders(active)
            engine.advance(book,spec["params"],[(T,A,100,100,100,100),(T,B,opening,opening,opening,opening)],T,T+60,1)
            self.assertEqual(engine.events[-1].get("reason"),expected)
            self.assertNotIn(A,book["qty"])
            self.assertEqual(bool(book["closeouts"]),opening == 300)
        book = P.new_book(1000)
        rec,_,_ = O.step(book,{"weights":{A:1}},spec["rows"][0],spec["params"],
                        P.Minutes(spec["minutes"]),T,T+60,True,{},1,first=True)
        self.assertEqual(rec["skipped"][0]["why"],"gross_limit")
        self.assertLessEqual(P.gross_at(book,{A:100}),P.value_at(book,{A:100}))

    def test_b08_twin_cannot_drop_a_condition_or_ignore_unfillable_wake(self):
        spec = world()
        bundles = [{"weights":{A:.2},"conditions":condition(T,B)},{"weights":None}]
        class Swap:
            def shuffle(self, xs):
                xs.reverse()
        rows = copy.deepcopy(spec["rows"])
        rows[1]["marks"].pop(B)
        with self.assertRaisesRegex(ValueError,"destination mark"):
            S.shuffle_bundles(bundles,rows,spec["wakes"],spec["end"],Swap())
        moved = S.shuffle_bundles(bundles,spec["rows"],spec["wakes"],spec["end"],Swap())
        gap = world([r for r in spec["minutes"] if r[0] < T+3600 or r[1] != A])
        s = self.create("A",spec=gap)
        self.assertEqual(S.replay(s,moved).get("unsupported"),[T+3600])

    def test_s03_hidden_quote_cannot_validate_a_condition(self):
        d = self.create("C",self.scout_export())
        _,key = info(d)
        pick = dict(wake_key=key,no_change=True,why="Wait",conditions=[
            dict(symbol=B,direction="below",price=98,hours=1,weight=.2,evidence_ids=[f"book:{T}"])])
        with self.assertRaisesRegex(ValueError,"visible quote"):
            d.handle("boss","pick",pick)
        found = d.handle("boss","look",dict(wake_key=key,symbol=B,kind="bars",request_id="price-b"))
        self.assertEqual(found["quote"]["price"],100)
        self.assertTrue(d.handle("boss","pick",pick)["accepted"])

    def scout_export(self, spec=None):
        s = self.create("scout", spec=spec)
        for k in range(2):
            for r in D.SCOUTS:
                _, key = info(s,r)
                s.handle(r, "usage", dict(wake_key=key, request_id=f"call{k}",
                                          usage={"in":10,"out":2}, counts={"input":10,"output":2}))
                s.handle(r, "notes", dict(wake_key=key, notes=[dict(symbol=A,text="Found a fact",evidence_ids=[f"n{k}"])]))
        return s.export_scout()

    def test_no_condition_parity(self):
        spec = world()
        p = self.create("A", spec=spec)
        _, k = info(p)
        p.handle("boss","pick", dict(wake_key=k, weights={A:.3,B:-.2}, exits={B:{"stop":102,"target":98}}, why="Test",
                                    citations={s:{"evidence_ids":[f"book:{T}"]} for s in (A,B)}))
        _, k = info(p)
        p.handle("boss","pick", dict(wake_key=k,no_change=True,why="Test"))
        args = dict(wakes=[P.iso(D.wall(t)) for t in spec["wakes"]], end_utc=P.iso(D.wall(spec["end"])),opening={})
        table = dict(rows=spec["rows"],end_marks=spec["end_marks"])
        _, log = S.load_session(p.path)
        protective, = [d for _,kind,d in log if kind == "protective_exit"]
        self.assertEqual(protective["execution"]["symbol"], B)
        self.assertEqual(protective["parent"]["evidence_ids"], [f"book:{T}"])
        bundles = [b for _,k,b in log if k == "decision"]
        ans = [(b["weights"],b["exits"]) for b in bundles]
        slow = P.run_perp(args, table, ans, p.pp, p.minutes, spec["cfg"])
        fast = F.run_perp(args, table, ans, p.pp, p.minutes, spec["cfg"])
        with self.assertRaisesRegex(ValueError, "conditional desk answers"):
            F.run_perp(dict(args, tm07_arm="C"), table, ans, p.pp, p.minutes, spec["cfg"])
        dsk = S.replay(p,bundles,journal=True)
        self.assertEqual(slow,fast)
        self.assertEqual(slow[0],dsk["book"])
        self.assertEqual(slow[2],dsk["value"])
        # The desk records boundary funding at the opening wake, not in the
        # last wake's receipt. The complete book and exit history still match.
        self.assertEqual([e for r in slow[1] for e in r["scan"]["exits"]],[e for r in dsk["scans"] for e in r["exits"]])
        self.assertAlmostEqual(sum(r["scan"]["funding_usd"] for r in slow[1]),sum(r["funding_usd"] for r in dsk["scans"]))
        for seed in range(4):
            twin = tm06.shuffle_answers(ans, spec["rows"], random.Random(seed))
            got = S.shuffle_bundles(bundles, spec["rows"],spec["wakes"],spec["end"],random.Random(seed))
            self.assertEqual(twin,[(x["weights"],x["exits"]) for x in got])
        self.assertEqual(S.score_week(p.path)["main"]["value"],slow[2])

    def test_no_lookahead_and_bad_note(self):
        s = self.create("scout")
        p,k = info(s,D.SCOUTS[0])
        self.assertEqual({r["id"] for r in p["evidence"]},{"p0","bp0","n0"})
        for value in ("future0","mirror0","estimated0","unlicensed0","unfinished0"):
            with self.assertRaisesRegex(ValueError,"not visible"):
                s.handle(D.SCOUTS[0],"notes",dict(wake_key=k,notes=[dict(symbol=A,text="bad",evidence_ids=[value])]))

    def test_neutral_merge_and_hidden_arm(self):
        neutral = self.scout_export()
        self.assertEqual(len(neutral["wakes"][0]["notes"]),1)
        a,b = self.create("A"), self.create("B", neutral)
        p,ak = info(a)
        q,bk = info(b)
        self.assertNotIn("notes",p)
        self.assertNotIn("evidence",q)
        self.assertEqual(q["notes"],neutral["wakes"][0]["notes"])
        self.assertNotEqual(ak,bk)
        with self.assertRaises(PermissionError):
            b.handle("boss","look",dict(wake_key=ak,symbol=A,kind="news"))
        self.assertEqual(b.authenticate(TOKEN),"boss")
        self.assertIsNone(b.authenticate("wrong"))

    def test_three_lookups_and_no_other_role(self):
        a = self.create("A")
        _,key = info(a)
        for i in range(3):
            rows = a.handle("boss","look",dict(wake_key=key,symbol=A,kind="news"))
            self.assertEqual([r["id"] for r in rows["rows"]],["n0"])
            self.assertEqual(rows["looks_left"],2-i)
        with self.assertRaisesRegex(ValueError,"no lookups left"):
            a.handle("boss","look",dict(wake_key=key,symbol=A,kind="news"))
        with self.assertRaises(PermissionError):
            a.handle("news_scout","next",{})

    def test_flat_trigger_uses_next_open(self):
        neutral = self.scout_export()
        s = self.create("C",neutral)
        p,k = info(s)
        s.handle("boss","pick",dict(wake_key=k,no_change=True,why="Wait.",conditions=[
                 dict(symbol=A,direction="above",pct=2,hours=1,weight=.2,note_ids=[p["notes"][0]["id"]])]))
        p,k = info(s)
        self.assertGreater(p["book"]["weights"][A],.2)
        s.handle("boss","pick",dict(wake_key=k,no_change=True,why="Hold."))
        _,log = S.load_session(s.path)
        events = [d for _,kind,d in log if kind=="condition"]
        self.assertEqual([x["kind"] for x in events],["armed","triggered","filled"])
        self.assertEqual(events[1]["utc"],T+120)
        self.assertEqual(events[2]["utc"],T+120)
        self.assertEqual(events[2]["open"],100)
        self.assertEqual(events[2]["note_ids"],[neutral["wakes"][0]["notes"][0]["id"]])
        self.assertGreater(events[2]["trade"]["fee_usd"],0)
        self.assertEqual(S.score_week(s.path)["main"]["standing"],1)

    def test_gaps_and_expiry(self):
        spec = world()
        engine, book = O.Orders(), P.new_book(1000)
        new = condition(T,hours=1)
        engine.submit({"conditions":new},book,T)
        engine.advance(book,spec["params"],[(T+60,A,100,103,99,100),(T+3600,A,200,210,199,205)],T,T+3660,1)
        self.assertFalse(book["qty"])
        self.assertEqual([(e["kind"],e["utc"]) for e in engine.events],
                         [("armed",T),("triggered",T+120),("expired",T+3600)])

    def test_immediate_cancel_and_protection(self):
        spec = world()
        engine, book = O.Orders(), P.new_book(1000)
        book.update(qty={A:1}, target={A:.1}, exits={A:{"stop":98}}, last_px={A:100},cash=900)
        engine.submit({"conditions":condition(T)},book,T)
        engine.advance(book,spec["params"],[(T,A,100,104,97,100),(T+60,A,100,104,99,100)],T,T+120,1)
        self.assertEqual([e["kind"] for e in engine.events],["armed","cancelled"])
        self.assertEqual(book["exits_hit"][0]["kind"],"stop")
        engine.submit({"conditions":condition(T)},book,T)
        engine.observe_close((T,A,100,104,99,100))
        engine.submit({"weights":{A:.2},"keep":[engine.active[A]["id"]]},book,T+3600)
        self.assertEqual(engine.events[-1]["reason"],"immediate_target")

    def test_restart_exactly_once(self):
        s = self.create("A")
        _,k = info(s)
        b = dict(wake_key=k,no_change=True,why="Test")
        reply = s.handle("boss","pick",b)
        r = D.DeskSession(s.path)
        self.assertEqual(r.handle("boss","pick",b),reply)
        self.assertEqual(r.handle("boss","status",{})["step"],1)
        with self.assertRaises(PermissionError):
            r.handle("boss","pick",dict(b,why="Changed retry"))

    def test_weights_dispatch_requires_role(self):
        s = self.create("A")
        with patch.dict("os.environ", TM07_RUNS_DIR=str(self.root)):
            with self.assertRaises(PermissionError):
                W.open_session(s.sid)
            with self.assertRaises(FileNotFoundError):
                W.open_session("TM07-../../other", desk_token=TOKEN)
            self.assertEqual(W.open_session(s.sid, desk_token=TOKEN).sid, s.sid)

    def test_guarded_routes_and_no_sibling_access(self):
        s = self.create("A")
        scout = self.create("scout")
        target = {"session": [s.sid]}
        auth = "Bearer " + TOKEN
        with patch.dict("os.environ", TM07_RUNS_DIR=str(self.root)):
            self.assertEqual(server.handle("GET","/next",target,None,auth)[0],404)
            self.assertEqual(server.handle("GET","/desk/next",target,None)[0],403)
            self.assertEqual(server.handle("GET","/desk/next",{"session":[scout.sid]},None,auth)[0],403)
            status,packet = server.handle("GET","/desk/next",target,None,auth)
            self.assertEqual(status,200)
            self.assertEqual(packet["role"],"boss")
            obj = D.encode({"wake_key":packet["wake_key"],"notes":[]})
            self.assertEqual(server.handle("POST","/desk/notes",target,obj,auth)[0],403)

    def test_sign_mark_gate_and_fixed_weeks(self):
        self.assertEqual(len(S.EXTENSION),17)
        self.assertEqual(S.WEEKS[-1],"2026-11-16")
        self.assertEqual(S.sign_mark(20),16)
        self.assertAlmostEqual(S.sign_tail(20,16),.005908966064453125)
        boss=D.BOSSES[1]
        specs=[dict(week=w, arm=a, boss=boss, fixture=w, main=dict(value=1000+5*(a=="B"), gain=.5,
                     equal=0,twin=[0,.1,.2])) for w in S.WEEKS for a in ("A","B")]
        got=S.paired(specs,boss,"B")
        self.assertEqual(got["wins"],20)
        self.assertTrue(got["passes"])
        specs[2*S.WEEKS.index(S.SCREEN[0])+1]["main"]["value"]=1000
        with self.assertRaisesRegex(ValueError,"screen gate"):
            S.paired(specs,boss,"B")
        self.assertEqual(S.select_five({str(i):100 for i in range(6)},{str(i):100 for i in range(6)}),list("12345"))

    def test_token_usage_missing_fields(self):
        s = self.create("B",self.scout_export())
        _,key=info(s)
        x=dict(wake_key=key,request_id="boss1",counts={"input":1},usage={"input_tokens":1})
        self.assertEqual(s.handle("boss","usage",x),s.handle("boss","usage",x))
        with self.assertRaises(ValueError):
            s.handle("boss","usage",dict(x,usage={"input_tokens":99}))
        for i in range(2):
            _,key=info(s)
            s.handle("boss","pick",dict(wake_key=key,no_change=True,why="Test"))
        scored=S.score_week(s.path)
        self.assertEqual(scored["usage"]["boss"]["calls"],1)
        self.assertNotIn("output",scored["usage"]["boss"]["tokens"])
        self.assertEqual(scored["usage"]["news_scout"]["tokens"]["output"],4)


if __name__ == "__main__":
    unittest.main()
