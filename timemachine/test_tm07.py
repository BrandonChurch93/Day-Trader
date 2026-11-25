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
SEAL_KEY = "fake-operator-only-seal-key-" * 3


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
    proofs = {}
    for item in [xs[2] for xs in evidence]:
        proofs[item["id"]] = dict(row_hash=D.digest(item),version_hash=D.digest(item["value"]),licensed=True,
                                  version_record="made-up snapshot",published=item["published"],known_at=item["known_at"],
                                  confirmations=[dict(group="primary",primary=True,known_at=item["known_at"],
                                                      version_record="made-up snapshot",version_hash=D.digest(item["value"]))])
    return dict(wakes=[T,T+3600], end=T+7200, symbols=symbols, watch=symbols, benchmark=BTC, opening={},vendor_proofs=proofs,
                rows=rows, minutes=minutes, end_marks={s:100 for s in [A,B,BTC]}, evidence=evidence,
                cfg=cfg, params=P.p_params([A,B,BTC], cfg, funding={A:{T:0.001}, B:{T:0.0}}), gross=1)


def info(s, r="boss"):
    payload = s.handle(r, "next", {})
    return payload, payload["wake_key"]


def condition(wake, symbol=A, **kw):
    item = dict(symbol=symbol, direction="above", price=102, hours=2, weight=0.25, evidence_ids=["p0"])
    item.update(kw)
    return O.normalize_conditions([item], {symbol:100}, [symbol], wake, wake+7200, 6, 1)


def registered_fixture(root,spec=None):
    weeks = {}
    for w in S.WEEKS:
        item = dict(fixture=D.digest(w),neutral_id="TM07-scout-"+w,funding_ref="made-up tape",funding_hash=D.digest(w))
        if w in S.FIXED:
            item["symbols"] = sorted(s+"/USD" for s in S.FIXED[w].split())
        else:
            prior = (S.date.fromisoformat(w)-S.timedelta(days=7)).isoformat()
            preceding = {s:100 for s in S.WATCH}
            item.update(before=preceding,last=preceding,before_known_on=prior,last_known_on=w,
                        symbols=S.select_five(preceding,preceding))
        weeks[w] = item
    if spec is not None:
        w = D.wall(spec["wakes"][0]).date().isoformat()
        weeks[w]["fixture"] = D.digest(D.json.loads(D.encode(spec)))
        weeks[w]["funding_hash"] = S.funding_profile_hash(spec["params"])
    body = dict(version="TM07-v1",runner_id="toy-runner",ledger_ref="toy-no-run",study_root=str(root.resolve()),
                cost_hash=S.canonical_cost_hash(),
                builds={s:{"id":s+"-toy","first_after_cutoff":"2026-07-01"}
                        for s in (*D.BOSSES,"gemini_neon")},weeks=weeks)
    return S.Registration(dict(body=body,seal=D.seal(SEAL_KEY,"registration",body)),SEAL_KEY)


def registered_world():
    spec = world()
    cfg = spec["cfg"]
    cfg.update({k:v for k,v in tm06.full_config().items() if k in P.P_KEYS or k == "tm_fast_funding_venue"})
    cfg["tm_weights_twin_draws"] = 1000
    symbols = sorted(s+"/USD" for s in S.FIXED[S.SCREEN[0]].split())
    priced = symbols+[BTC]
    wakes = list(range(T,T+7*86400,3600))
    rates = {s:({T+3600:.001} if s == BTC else {}) for s in priced}
    pp = P.p_params(priced,cfg,funding=rates)
    pp.update(source={s:P.per(cfg["tm_fast_funding_venue"],s) for s in priced},
              funding_known_at={s:{t:t for t in rates[s]} for s in priced})
    return dict(spec,symbols=symbols,watch=sorted(S.WATCH),wakes=wakes,end=T+7*86400,runner_id="toy-runner",
                evidence=[[] for _ in wakes],vendor_proofs={},params=pp,
                minutes=[(t,s,100,101,99,100) for t in wakes for s in priced],end_marks={s:100 for s in priced},
                rows=[dict(marks={s:100 for s in priced}) for _ in wakes])


def synthetic_scores(reg,boss,draws=1000):
    for w in S.WEEKS:
        sid = reg.weeks[w]["neutral_id"]
        D.record_attempt(reg.root/sid,reg.hash,w,None,"scout",[])
        reg.bind_neutral(w,sid,D.digest([w,"scout"]))
    return [dict(week=w,arm=a,boss=boss,fixture=reg.weeks[w]["fixture"],registration=reg.hash,
                 neutral_id=reg.weeks[w]["neutral_id"] if a=="B" else None,scout_hash=D.digest([w,"scout"]) if a=="B" else None,
                 main=dict(value=1000+5*(a=="B"),gain=.5,equal=0,twin=[0]*draws))
            for w in S.WEEKS for a in ("A","B")]


class DeskTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="tm07-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def create(self, arm, scout=None, spec=None, sid=None):
        spec = spec or world()
        path = self.root / (sid or f"TM07-test-{arm}")
        tokens = {r: "fake-" + r*7 for r in D.SCOUTS} if arm == "scout" else {"boss":TOKEN if arm == "A" else TOKEN+path.name}
        D.create_desk(path,spec,arm,D.BOSSES[0],tokens,scout,approval_key=SEAL_KEY,
                      vendor_signature=D.seal(SEAL_KEY,"vendor",spec.get("vendor_proofs",{})))
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
        self.assertEqual(result[0][A],{T+1:.05})
        self.assertEqual(result[2][A][T+1],T+1)

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

    def test_reaudit_r6_flat_idle_wake_needs_no_open(self):
        spec = world([(T+3600,A,100,100,100,100)])
        session = self.create("A",spec=spec)
        idle = S.replay(session,[{},{}])
        self.assertEqual(idle["unsupported"],[])
        self.assertEqual(idle["value"],1000)
        move = S.replay(session,[{"weights":{A:.3}},{}])
        self.assertEqual(move["unsupported"],[T])

    def test_reaudit_sol_r07_detection_is_not_a_fill(self):
        spec = world()
        session = self.create("A",spec=spec)
        orders = condition(T,weight=1)
        trial = S.replay(session,[{"conditions":orders},{}],journal=True)
        self.assertIn("refused",[e["kind"] for e in trial["events"]])
        self.assertEqual(trial["triggered"],1)
        self.assertEqual(trial["standing"],0)

    def test_reaudit_r2_new_stop_activates_after_its_fill_open(self):
        for held,first in ((False,T),(True,T+60)):
            with self.subTest(held=held):
                spec = world([(T,A,100,101,99,100)]*held +
                             [(first,s,90,92,85,89) for s in ([A,B] if held else [A])] +
                             [(first+60,A,88,90,84,89)])
                book = P.new_book(1000)
                if held:
                    book.update(qty={A:2,B:1},target={A:.2,B:.1},cash=700,last_px={A:100,B:100})
                weight = {A:.5,**({B:.1} if held else {})}
                rec,_,_ = O.step(book,dict(weights=weight,exits={A:{"stop":95}}),
                                  spec["rows"][0],spec["params"],P.Minutes(spec["minutes"]),T,T+180,True,{},1,first=not held)
                self.assertEqual(next(x for x in rec["trades"] if x["symbol"] == A)["fill_utc"],O.stamp(first))
                exit, = rec["scan"]["exits"]
                self.assertEqual((exit["utc"],exit["filled_at"],exit["gap"]),(O.stamp(first+60),88,True))
        spec = world([(T,A,100,101,99,100),(T+60,A,90,92,85,89),
                      (T+60,B,100,100,100,100),(T+120,A,88,90,84,89)])
        book = P.new_book(1000)
        book.update(qty={A:2,B:1},target={A:.2,B:.1},cash=700,last_px={A:100,B:100},exits={A:{"stop":80}})
        rec,_,_ = O.step(book,dict(weights=book["target"],exits={A:{"stop":95}}),spec["rows"][0],
                         spec["params"],P.Minutes(spec["minutes"]),T,T+180,True,{},1)
        self.assertFalse(rec["trades"])
        self.assertEqual([x["utc"] for x in rec["scan"]["exits"]],[O.stamp(T+120)])

    def test_reaudit_sol_r02_later_high_cannot_liquidate_at_earlier_open(self):
        def trial(high):
            spec = world([(T,A,100,high,99,100),(T,B,100,100,99,100),
                          (T+60,A,170,171,169,170),(T+60,B,120,121,119,120)])
            book = P.new_book(1000)
            book.update(cash=1900,qty={A:-6,B:-3},target={A:-.6,B:-.3},last_px={A:100,B:100})
            return O.step(book,dict(weights={A:-.6,B:-.35}),spec["rows"][0],spec["params"],
                          P.Minutes(spec["minutes"]),T,T+120,True,{},1)[0]
        calm, jump = trial(101),trial(350)
        self.assertEqual(calm["trades"],jump["trades"])
        self.assertEqual(jump["trades"][0]["fill_utc"],O.stamp(T))
        self.assertIsNone(calm["scan"]["closeout"])
        closeout = jump["scan"]["closeout"]
        self.assertEqual(closeout["utc"],O.stamp(T+60))
        self.assertEqual({r["symbol"]:r["open"] for r in closeout["trades"]},{A:170,B:120})

    def test_reaudit_r1_full_costed_benchmarks_hold_every_leg(self):
        for px in (90,110):
            spec = world([(t,s,p,p,p,p) for t,p in ((T,100),(T+3600,px)) for s in (A,B,BTC)])
            spec["end_marks"] = {s:px for s in (A,B,BTC)}
            spec["params"]["funding"][A] = {T+3600:.001,T+7200:.002}
            spec["params"]["funding"][B] = {T+3600:.002,T+7200:.001}
            spec["params"]["funding"][BTC] = {T+3600:.0015,T+7200:.0015}
            path = self.root/f"TM07-bench-{px}"
            D.create_desk(path,spec,"A",D.BOSSES[0],D.issue_role_tokens("A"),approval_key=SEAL_KEY,
                          vendor_signature=D.seal(SEAL_KEY,"vendor",spec["vendor_proofs"]))
            session = D.DeskSession(path)
            for weights,sign in (({A:.5,B:.5},1),({B:.5,A:.5},1),({BTC:1},1),({BTC:-1},-1)):
                got = S.buy_and_hold(session,weights,12)
                notional = 1000/(1+.0004+.0012*(1+sign*.0004))
                expected = notional+sign*notional*(px/100-1)-sign*notional*px/100*.003
                self.assertAlmostEqual(got["value"],expected,places=8)
                self.assertEqual(set(got["book"]["qty"]),set(weights))
                self.assertAlmostEqual(got["book"]["traded_usd"],notional)
            for _ in range(2):
                _,key = info(session)
                session.handle("boss","pick",dict(wake_key=key,no_change=True,why="Baseline."))
            main = S.score_week(path)["main"]
            baseline = (1000/(1+.0004+.0012*1.0004))*(px/100)*(1-.003)
            self.assertAlmostEqual(main["equal"],100*(baseline/1000-1))
            self.assertAlmostEqual(main["benchmark"],main["equal"])
            with self.assertRaisesRegex(S.UnsupportedWeek,"benchmark"):
                S.buy_and_hold(session,{A:.5,"MISSING/USD":.5},12)

    def test_reaudit_opr_r5_price_packet_rejects_unscreened_fields(self):
        spec = world()
        price, other = spec["evidence"][0][:2]
        price["value"]["observed_at"] = T+3600
        other["value"]["funding"] = {"rate":.002,"every_hours":1,"stamped_utc":O.stamp(T+1)}
        session = self.create("scout",spec=spec)
        raw,_ = info(session,D.SCOUTS[0])
        self.assertFalse({"p0","bp0"} & session.evidence(0).keys())
        self.assertNotIn("observed_at",D.encode(raw))
        clean = dict(price,value={"price":100,"observed_at":T-60})
        self.assertTrue(D.available(clean,T))
        self.assertFalse(D.available(dict(clean,future_hint=109),T))

    def test_reaudit_sol_r04_signed_attention_must_match_its_own_clock(self):
        spec = world()
        for name,end in (("late",T+3600),("ok",T)):
            e = dict(id=name,symbol=A,kind="attention",published=T,known_at=T,period_end=T,licensed=True,
                     vintage="original",value={"count":7,"period_end":end})
            spec["evidence"][0].append(e)
            spec["vendor_proofs"][name] = dict(row_hash=D.digest(e),version_hash=D.digest(e["value"]),
                                               version_record="toy snapshot",licensed=True,published=T,known_at=T)
        session = self.create("scout",spec=spec)
        for role in D.SCOUTS:
            packet,key = info(session,role)
            self.assertNotIn("late",{e["id"] for e in packet["evidence"]})
            self.assertIn("ok",{e["id"] for e in packet["evidence"]})
            with self.assertRaises(ValueError):
                session.handle(role,"notes",dict(wake_key=key,notes=[dict(symbol=A,text="Future.",evidence_ids=["late"])]))
        with session.tx() as (con,_):
            drops, = con.execute("SELECT data FROM journal WHERE kind='evidence_drops'").fetchall()
        self.assertEqual(D.json.loads(drops[0])["attention"],2)

    def test_reaudit_opr_r3_standalone_boss_gates_cannot_split_neutral(self):
        reg = registered_fixture(self.root)
        good = [s for s in synthetic_scores(reg,D.BOSSES[0]) if s["week"] in S.SCREEN]
        other = [dict(s,boss=D.BOSSES[1]) for s in good]
        for s in other:
            if s["arm"] == "B":
                s["scout_hash"] = D.digest(["alternate",s["week"]])
        S.seal_screen_gate([reg.attest_score(s) for s in good],D.BOSSES[0],"B",reg,SEAL_KEY)
        with self.assertRaisesRegex(ValueError,"neutral"):
            S.seal_screen_gate([reg.attest_score(s) for s in other],D.BOSSES[1],"B",reg,SEAL_KEY)
        week = S.SCREEN[0]
        with self.assertRaisesRegex(ValueError,"already finalized"):
            reg.bind_neutral(week,reg.weeks[week]["neutral_id"],D.digest("other"))

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

    def test_s04_lookup_retry_is_not_a_second_paid_lookup(self):
        a = self.create("A")
        _,key = info(a)
        request = dict(wake_key=key,symbol=A,kind="news",request_id="first")
        first = a.handle("boss","look",request)
        again = D.DeskSession(a.path).handle("boss","look",request)
        self.assertEqual(first,again)
        with self.assertRaisesRegex(ValueError,"request id"):
            a.handle("boss","look",dict(request,kind="bars"))
        more = a.handle("boss","look",dict(request,request_id="second"))
        self.assertEqual(more["looks_left"],1)

    def test_s05_diagnostics_keep_twin_trades_and_cent_agreement(self):
        a = self.create("A")
        for at in world()["wakes"]:
            _,key = info(a)
            a.handle("boss","pick",dict(wake_key=key,no_change=True,why="No move"))
        summary = S.score_week(a.path)
        self.assertEqual(summary["main"]["twin_activity"],[
            {"immediate":0,"standing":0,"triggered":0,"turnover_usd":0.0} for _ in range(4)])
        self.assertEqual(summary["usage"]["boss"]["status"],"UNKNOWN")
        self.assertEqual(S.cent_lift(1000.0049,1000.005),.01)

    def test_s02_legacy_tm07_prefix_is_not_reserved(self):
        with patch.object(W,"is_weights",return_value=False), patch.object(W.S,"Session",return_value="legacy"):
            self.assertEqual(W.open_session("TM07-legacy"),"legacy")
        p = self.root / "TM07-legacy"
        p.mkdir()
        (p/"session.json").write_text("{}")
        with patch.object(server.S,"runs_dir",return_value=self.root), patch.object(server,"tape",return_value=None), \
             patch.object(server.W,"open_session") as opening:
            opening.return_value.status.return_value = {"legacy":True}
            self.assertEqual(server.handle("GET","/status",{"session":[p.name]},None),(200,{"legacy":True}))

    def test_b04_self_declared_confirmation_and_future_bar_are_not_proof(self):
        base = dict(id="id",symbol=A,published=T,known_at=T,licensed=True,vintage="original")
        future = dict(base,kind="bars",period_end=T,value={"t":T+60,"timeframe":"1Min"})
        pretext = dict(base,kind="news",origins=["wire","mirror"],confirmation_known_at=T+3600,
                       value={"headline":"made up"})
        self.assertFalse(D.available(future,T))
        self.assertFalse(D.available(pretext,T))
        evidence = {pretext["id"]:dict(row_hash=D.digest(pretext),version_hash=D.digest(pretext["value"]),licensed=True,
                    version_record="fake dated copy",published=T,known_at=T,
                    confirmations=[dict(group=g,known_at=at,version_record=g,version_hash="toy")
                                   for g,at in (("wire",T),("owner",T+3600))])}
        self.assertFalse(D.available(pretext,T,evidence))
        s = self.scout_export()
        bad = copy.deepcopy(s)
        bad["wakes"][0]["notes"][0]["evidence"][0]["known_at"] = T+60
        with self.assertRaisesRegex(ValueError,"seal"):
            self.create("B",bad)

    def test_b05_desk_service_never_dispatches_legacy_and_tokens_are_unique(self):
        a = self.create("A")
        with patch.object(server,"handle",side_effect=AssertionError("legacy route dispatched")):
            self.assertEqual(server.handle_desk_only("GET","/next",{"session":[a.sid]},None,None)[0],404)
        spec = world()
        with self.assertRaisesRegex(ValueError,"already assigned"):
            D.create_desk(self.root/"TM07-other",spec,"A",D.BOSSES[0],{"boss":TOKEN},
                          approval_key=SEAL_KEY,vendor_signature=D.seal(SEAL_KEY,"vendor",spec["vendor_proofs"]))
        incomplete = dict(root=str(self.root),launcher_digest="toy",probe_transcript_digest="toy",
                          sandbox_identities=["toy"],passed=["desk_routes_only"])
        with self.assertRaisesRegex(ValueError,"missing isolation"):
            D.validate_worker_boundary(SEAL_KEY,incomplete,D.seal(SEAL_KEY,"worker-boundary",incomplete),self.root)

    def test_b09_one_draw_cannot_pass_the_registered_gate(self):
        boss = D.BOSSES[0]
        fake = [dict(week=w,arm=a,boss=boss,fixture=w,main=dict(value=1000+5*(a=="B"),gain=.5,equal=0,twin=[0]))
                for w in S.WEEKS for a in ("A","B")]
        with self.assertRaisesRegex(ValueError,"register|1,000"):
            S.paired(fake,boss,"B")
        reg = registered_fixture(self.root)
        with self.assertRaisesRegex(ValueError,"1,000"):
            S.paired([reg.attest_score(x) for x in synthetic_scores(reg,boss,draws=1)],boss,"B",registration=reg)
        with self.assertRaisesRegex(ValueError,"sealed"):
            reg.verify_gate(S.EXTENSION[0],boss,"B",[],SEAL_KEY)

    def test_registered_create_checks_full_week_and_records_attempt_once(self):
        spec = registered_world()
        reg = registered_fixture(self.root,spec)
        envelope = dict(body=reg.body,seal=D.seal(SEAL_KEY,"registration",reg.body))
        boss = D.BOSSES[0]
        settings = dict(approval_key=SEAL_KEY,registration=envelope,model_build=boss+"-toy")
        D.create_desk(self.root/"TM07-registered",spec,"A",boss,D.issue_role_tokens("A"),**settings)
        other_root = self.root/"other"
        other_root.mkdir()
        with self.assertRaisesRegex(ValueError,"study root"):
            D.create_desk(other_root/"TM07-copied",spec,"A",boss,D.issue_role_tokens("A"),**settings)
        with self.assertRaisesRegex(ValueError,"already recorded"):
            D.create_desk(self.root/"TM07-repeat",spec,"A",boss,D.issue_role_tokens("A"),**settings)
        spec["end"] -= 60
        with self.assertRaisesRegex(ValueError,"registered windows"):
            D.create_desk(self.root/"TM07-wrong-window",spec,"A",boss,D.issue_role_tokens("A"),**settings)

    def test_reaudit_sol_r05_cannot_attest_wrong_costs_or_future_funding(self):
        spec = registered_world()
        for change,why in ((lambda pp:pp["hs"].update({BTC:.08}),"cost"),
                           (lambda pp:pp["maint"].update({BTC:.55}),"cost"),
                           (lambda pp:pp["funding_known_at"][BTC].update({T+3600:T+3601}),"settlement")):
            faulty = copy.deepcopy(spec)
            change(faulty["params"])
            reg = registered_fixture(self.root,faulty)
            envelope = dict(body=reg.body,seal=D.seal(SEAL_KEY,"registration",reg.body))
            with self.assertRaisesRegex(ValueError,why):
                D.create_desk(self.root/"TM07-wrong-cost",faulty,"A",D.BOSSES[0],D.issue_role_tokens("A"),
                              approval_key=SEAL_KEY,registration=envelope,model_build=D.BOSSES[0]+"-toy")
        original = registered_fixture(self.root,spec)
        spec["params"]["funding"][BTC][T+3600] = .05
        changed = registered_fixture(self.root,spec).body
        changed["weeks"][S.SCREEN[0]]["funding_hash"] = original.weeks[S.SCREEN[0]]["funding_hash"]
        envelope = dict(body=changed,seal=D.seal(SEAL_KEY,"registration",changed))
        with self.assertRaisesRegex(ValueError,"settlement digest"):
            D.create_desk(self.root/"TM07-wrong-funding",spec,"A",D.BOSSES[0],D.issue_role_tokens("A"),
                          approval_key=SEAL_KEY,registration=envelope,model_build=D.BOSSES[0]+"-toy")

    def test_reaudit_sol_r05_settlement_uses_quantity_at_exact_stamp(self):
        spec = world([(T,A,100,100,100,100),(T+60,A,110,110,110,110),
                      (T+120,A,120,900,120,800),(T+180,A,120,120,120,120)])
        pp = spec["params"]
        pp["funding"][A] = {T+1:.01,T+61:.02}
        book = P.new_book(1000)
        rec,_,_ = O.step(book,dict(weights={A:.5}),spec["rows"][0],pp,P.Minutes(spec["minutes"]),
                         T,T+60,False,{},1,first=True)
        self.assertAlmostEqual(rec["scan"]["funding_usd"],5)
        rec,_,_ = O.step(book,dict(weights={A:.25}),spec["rows"][0],pp,P.Minutes(spec["minutes"]),
                         T+60,T+180,True,{},1)
        self.assertAlmostEqual(rec["scan"]["funding_usd"],book["qty"][A]*110*.02)
        self.assertEqual([r["utc"] for r in rec["scan"]["settlements"]],[O.stamp(T+61)])

    def test_opus_r2_drift_does_not_allow_an_over_cap_saved_target(self):
        spec = world()
        book = P.new_book(1000)
        P.p_step(book,{A:.9},None,spec["rows"][0],spec["params"],True)
        engine = O.Orders(condition(T,B,weight=.15))
        engine.observe_close((T,B,100,106,99,105))
        engine.execute_open(book,spec["params"],T+60,{A:60.,B:105.},1)
        self.assertEqual(engine.events[-1].get("reason"),"target_gross_limit")
        self.assertLessEqual(sum(abs(w) for w in book["target"].values()),1)

    def test_opus_r1_open_coverage_is_not_in_the_pick_reply(self):
        def arm(gappy):
            spec = world()
            if gappy:
                spec = world([r for r in spec["minutes"] if r[0] != T or r[1] != A])
            # Keep the temp worker roots distinct, as in separate fixtures.
            original = self.root
            self.root = original / str(gappy)
            self.root.mkdir()
            try:
                s = self.create("C",self.scout_export(spec),spec)
                p,key = info(s)
                cited = {"note_ids":[p["notes"][0]["id"]]}
                response = s.handle("boss","pick",dict(wake_key=key,why="Test",weights={A:.3},citations={A:cited},
                                    conditions=[dict(symbol=A,direction="above",price=110,hours=2,weight=.2,**cited)]))
                with s.tx() as (con,_):
                    fill = D.json.loads(con.execute("SELECT data FROM journal WHERE kind='immediate'").fetchone()[0])
                return response,fill["trade"]["fill_utc"]
            finally:
                self.root = original
        plain,gap = arm(False),arm(True)
        self.assertEqual(plain[0],gap[0])
        self.assertEqual(plain[1],P.iso(D.wall(T)))
        self.assertEqual(gap[1],P.iso(D.wall(T+60)))

    def scout_export(self, spec=None):
        s = self.create("scout", spec=spec)
        for k in range(2):
            for r in D.SCOUTS:
                _, key = info(s,r)
                s.handle(r, "usage", dict(wake_key=key, request_id=f"call{k}",
                                          usage={"in":10,"out":2}, counts={"input":10,"output":2}))
                s.handle(r, "notes", dict(wake_key=key, notes=[dict(symbol=A,text="Found a fact",evidence_ids=[f"n{k}"])]))
        return s.export_scout(SEAL_KEY)

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
        self.assertEqual({k:v for k,v in slow[0].items() if k != "exits_hit"},
                         {k:v for k,v in dsk["book"].items() if k != "exits_hit"})
        self.assertEqual(slow[2],dsk["value"])
        # The desk records boundary funding at the opening wake, not in the
        # last wake's receipt. The complete book and exit history still match.
        before, = [e for r in slow[1] for e in r["scan"]["exits"]]
        after, = [e for r in dsk["scans"] for e in r["exits"]]
        self.assertEqual(after,dict(before,utc=O.stamp(D.epoch(before["utc"])+60),phase="intrabar"))
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
        self.assertIsNone(b.authenticate(TOKEN))
        self.assertEqual(b.authenticate(TOKEN+b.sid),"boss")
        self.assertIsNone(b.authenticate("wrong"))

    def test_three_lookups_and_no_other_role(self):
        a = self.create("A")
        _,key = info(a)
        for i in range(3):
            rows = a.handle("boss","look",dict(wake_key=key,symbol=A,kind="news",request_id=f"look-{i}"))
            self.assertEqual([r["id"] for r in rows["rows"]],["n0"])
            self.assertEqual(rows["looks_left"],2-i)
        with self.assertRaisesRegex(ValueError,"no lookups left"):
            a.handle("boss","look",dict(wake_key=key,symbol=A,kind="news",request_id="overflow"))
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
                W.open_session(s.sid, desk_token="wrong")
            with self.assertRaises(FileNotFoundError):
                W.open_session("TM07-../../other", desk_token=TOKEN)
            self.assertEqual(W.open_session(s.sid, desk_token=TOKEN).sid, s.sid)

    def test_guarded_routes_and_no_sibling_access(self):
        s = self.create("A")
        scout = self.create("scout")
        target = {"session": [s.sid]}
        auth = "Bearer " + TOKEN
        with patch.dict("os.environ", TM07_RUNS_DIR=str(self.root)), patch.object(server.S,"runs_dir",return_value=self.root):
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
        reg = registered_fixture(self.root)
        specs = synthetic_scores(reg,boss)
        signed = [reg.attest_score(x) for x in specs]
        got=S.paired(signed,boss,"B",registration=reg)
        self.assertEqual(got["wins"],20)
        self.assertTrue(got["passes"])
        gate = S.seal_screen_gate(signed,boss,"B",reg,SEAL_KEY)
        reg.verify_gate(S.EXTENSION[0],boss,"B",[gate],SEAL_KEY)
        with self.assertRaisesRegex(ValueError,"screen gate"):
            reg.verify_gate(S.EXTENSION[0],boss,"C",[gate],SEAL_KEY)
        specs[2*S.WEEKS.index(S.SCREEN[0])+1]["main"]["value"]=1000
        with self.assertRaisesRegex(ValueError,"screen gate"):
            S.paired([reg.attest_score(x) for x in specs],boss,"B",registration=reg)
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
