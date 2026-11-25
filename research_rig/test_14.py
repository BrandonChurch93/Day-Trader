"""Tests for plan 14 on made-up data only. No real price is read.

  python3 test_14.py            all tests, then the no-edge check (prints how often each mark passes by chance)
  python3 test_14.py --quick    all tests, a short no-edge check

Made-up worlds: business days from replay_14_plan.start to replay_14_plan.end; stocks follow random walks with no
momentum unless asked; members join and leave; one company has two share classes; some stocks stop."""
import sys, os, tempfile, unittest, subprocess, datetime as dt, json
import numpy as np
os.environ.setdefault("RESULTS_14_DIR", tempfile.mkdtemp())
import common_14 as C
import score_14 as S

P = C.P

def bdays(start, end):
    d = dt.date.fromisoformat(str(start)); e = dt.date.fromisoformat(str(end)); out = []
    while d <= e:
        if d.weekday() < 5: out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out

def row(t, a, b, cid=None, feed=None):
    feed = t if feed is None else feed
    return dict(date_from=a, date_to=b, ticker_then=t, ticker_feed=feed, company=t, feed_from="", feed_to="",
                company_id=cid or t, entity=t, note="", series=f"{feed}||" if feed else "")

def world(seed, n=150, mom=0.0, vol=0.02, days=None, churn=True):
    """A made-up world. mom > 0 adds momentum (a stock's drift is its own past-year drift times mom)."""
    rng = np.random.default_rng(seed); days = days or bdays(P["start"], P["end"]); T = len(days)
    data, members = {}, []
    drift = rng.normal(0, 0.001, n) if mom else np.full(n, 0.0002)   # no momentum: every stock has the same drift
    rets = np.zeros((n, T))
    for t in range(T):
        if mom and t % 21 == 0: drift = mom * drift + np.sqrt(1 - mom ** 2) * rng.normal(0, 0.001, n)
        rets[:, t] = drift + rng.normal(0, vol, n)
    closes = 50 * np.exp(np.cumsum(rets, axis=1))
    opens = closes * np.exp(rng.normal(0, vol / 3, (n, T)))
    for j in range(n):
        tk = f"S{j:03d}"; o, c = opens[j].copy(), closes[j].copy()
        a, b = days[0], "9999-12-31"
        if churn and j % 10 == 3:                      # joins later, priced only from a bit before it joins
            k = int(rng.integers(100, T - 300)); a = days[k]; o[:max(k - 300, 0)] = np.nan; c[:max(k - 300, 0)] = np.nan
        if churn and j % 10 == 7:                      # leaves; prices stop a few days before
            k = int(rng.integers(400, T - 50)); b = days[k]; o[k - 3:] = np.nan; c[k - 3:] = np.nan
        data[f"{tk}||"] = (o, c); members.append(row(tk, a, b, cid="PAIR" if j in (0, 1) else None))
    idx = np.mean(np.exp(rets) - 1, axis=0)                        # SPY: every made-up stock in equal parts, daily
    spy_c = 100 * np.cumprod(1 + idx); data["SPY||"] = (spy_c * np.exp(rng.normal(0, 0.002, T)), spy_c)
    for s in ("SPMO", "MTUM"): data[f"{s}||"] = data["SPY||"]
    return days, members, C.Prices.from_arrays(days, data)

class Small(unittest.TestCase):
    """Hand-checked cases on a tiny calendar."""
    def setUp(self):
        self.days = bdays("2020-01-01", "2020-04-30")
    def px(self, data): return C.Prices.from_arrays(self.days, {k: (np.array(v[0], float), np.array(v[1], float)) for k, v in data.items()})

    def test_month_ends(self):
        me = C.month_end_index(self.days)
        self.assertEqual([self.days[i] for i in me], ["2020-01-31", "2020-02-28", "2020-03-31", "2020-04-30"])
        d2 = self.days[:-3]                            # April not complete
        self.assertEqual([d2[i] for i in C.month_end_index(d2)], ["2020-01-31", "2020-02-28", "2020-03-31"])

    def test_one_period_cost(self):
        T = len(self.days); f = 5
        o = np.full(T, 10.0); c = np.full(T, 10.0); c[f:] = 12.0
        px = self.px({"A||": (o, c)})
        r = C.simulate(px, [f], [[0]], 5)
        self.assertAlmostEqual(r["value"], (1 - 5e-4) * 1.2 * (1 - 5e-4), places=12)

    def test_rebalance_turnover(self):
        T = len(self.days); f1, f2 = 3, 30
        oa = np.full(T, 10.0); ca = np.full(T, 10.0); ob = np.full(T, 10.0); cb = np.full(T, 10.0)
        oa[f2:] = 20.0; ca[f2 - 1:] = 20.0               # A doubles before the second re-form
        px = self.px({"A||": (oa, ca), "B||": (ob, cb)})
        r = C.simulate(px, [f1, f2], [[0, 1], [0, 1]], 10)
        V0 = 1 - 1e-3
        Vopen = V0 * 0.5 * 2 + V0 * 0.5                  # 1.5 * V0
        dA, dB = 2 / 3, 1 / 3; T2 = abs(0.5 - dA) + abs(0.5 - dB)
        self.assertAlmostEqual(r["turnover"][1], T2, places=12)
        self.assertAlmostEqual(r["value"], Vopen * (1 - 1e-3 * T2) * (1 - 1e-3), places=12)

    def test_stop_goes_to_cash_and_is_flagged(self):
        T = len(self.days); f1, f2 = 3, 30
        oa = np.full(T, 10.0); ca = np.full(T, 10.0); oa[20:] = np.nan; ca[20:] = np.nan; ca[19] = 15.0
        ob = np.full(T, 10.0); cb = np.full(T, 10.0)
        px = self.px({"A||": (oa, ca), "B||": (ob, cb)})
        r = C.simulate(px, [f1, f2], [[0, 1], [1]], 0)
        self.assertEqual(r["flags"], [(0, 0, 19)])
        self.assertAlmostEqual(r["value"], 0.5 * 1.5 + 0.5, places=12)

    def test_gap_is_carried_not_traded(self):
        # A has no bar from day 25 to 34, so no open at the re-form on day 30, and prices again from day 35.
        # The rule wants B at day 30, but A cannot be sold then: it is carried through the gap on its own prices.
        T = len(self.days); f1, f2 = 3, 30
        oa = np.full(T, 10.0); ca = np.full(T, 10.0); oa[25:35] = np.nan; ca[25:35] = np.nan; ca[24] = 11.0
        oa[35:] = 12.0; ca[35:] = 12.0
        ob = np.full(T, 10.0); cb = np.full(T, 10.0); cb[40:] = 20.0
        px = self.px({"A||": (oa, ca), "B||": (ob, cb)})
        r = C.simulate(px, [f1, f2], [[0], [1]], 10, daily=True)
        c = 1e-3
        self.assertEqual(r["flags"], []); self.assertEqual(r["carried"], [(1, 0)])
        self.assertAlmostEqual(r["at_fill"][1], (1 - c) * 1.1, places=12)          # valued at its last close
        self.assertAlmostEqual(r["turnover"][1], 0.0, places=12)                    # nothing could be traded
        self.assertAlmostEqual(r["value"], (1 - c) * 1.2 * (1 - c), places=12)      # A's own prices, B never bought
        self.assertAlmostEqual(r["daily"][30], (1 - c) * 1.1, places=12)

    def test_gap_part_carried_rest_reformed(self):
        # A and B held; A gaps over the re-form; B is sold and C bought with B's money only.
        T = len(self.days); f1, f2 = 3, 30
        oa = np.full(T, 10.0); ca = np.full(T, 10.0); oa[28:32] = np.nan; ca[28:32] = np.nan
        ob = np.full(T, 10.0); cb = np.full(T, 10.0)
        oc = np.full(T, 10.0); cc = np.full(T, 10.0); cc[50:] = 15.0
        px = self.px({"A||": (oa, ca), "B||": (ob, cb), "C||": (oc, cc)})
        r = C.simulate(px, [f1, f2], [[0, 1], [2]], 10)
        c = 1e-3; V0 = 1 - c
        self.assertAlmostEqual(r["turnover"][1], 1.0, places=12)                    # sell B's half, buy C's half
        Vb = V0 * 0.5 - c * 1.0 * V0
        self.assertAlmostEqual(r["value"], (V0 * 0.5 + Vb * 1.5) * (1 - c), places=12)

    def test_stop_sale_cost_on_the_stop_day(self):
        T = len(self.days); f1, f2 = 3, 30
        oa = np.full(T, 10.0); ca = np.full(T, 10.0); oa[20:] = np.nan; ca[20:] = np.nan
        ob = np.full(T, 10.0); cb = np.full(T, 10.0)
        px = self.px({"A||": (oa, ca), "B||": (ob, cb)})
        r = C.simulate(px, [f1, f2], [[0, 1], [1]], 10, daily=True)
        c = 1e-3; V0 = 1 - c
        self.assertAlmostEqual(r["daily"][18], V0, places=12)
        self.assertAlmostEqual(r["daily"][19], V0 * 0.5 * (1 - c) + V0 * 0.5, places=12)   # sold at that close

    def test_fast_equals_simulate(self):
        days, members, px = world(5, n=40, days=bdays("2016-01-04", "2019-12-31"))
        periods, me = S.plan_periods(members, px, days)
        fills = [p["fill"] for p in periods]
        # put gaps across some re-form days so carried stocks are tested too
        O, Cc = px.O.copy(), px.C.copy()
        rg = np.random.default_rng(9)
        for s in rg.choice(len(px.keys) - 1, 15, replace=False):
            for f in rg.choice(fills[1:], 3, replace=False):
                O[s, f - 2:f + 3] = np.nan; Cc[s, f - 2:f + 3] = np.nan
        px = C.Prices.from_arrays(days, {k: (O[i], Cc[i]) for i, k in enumerate(px.keys)})
        rng = np.random.default_rng(1)
        bk = C.random_baskets(periods, px, 10, 40, rng)
        fast = C.fast_values(C.period_moves(px, fills), bk, 5)
        ncar = 0
        for j in range(40):
            sim = C.simulate(px, fills, [[s for s in bk[j, k] if s >= 0] for k in range(len(fills))], 5)
            ncar += len(sim["carried"])
            self.assertAlmostEqual(fast[j], sim["value"], places=10)
        self.assertGreater(ncar, 0)

    def test_random_paths_keep_as_many_as_the_rule(self):
        days, members, px = world(6, n=60, days=bdays("2016-01-04", "2019-12-31"))
        periods, me = S.plan_periods(members, px, days)
        fills = [p["fill"] for p in periods]; n = 10
        rule = S.run_setup(members, px, days, periods, n, daily=False)
        kept = S.kept_counts(rule["baskets"], rule["flags"])
        mv = C.period_moves(px, fills)
        bk = C.random_baskets(periods, px, n, 50, np.random.default_rng(2), kept=kept, stopped=mv[2])
        self.assertGreater(sum(kept), 0)
        for j in range(50):
            for k in range(1, len(periods)):
                cur = {s for s in bk[j, k] if s >= 0}; prev = {s for s in bk[j, k - 1] if s >= 0 and not mv[2][k - 1][s]}
                elig = {s for _, _, s in periods[k]["ranked"] if not np.isnan(px.O[s, fills[k]])}
                self.assertEqual(len(cur & prev), min(kept[k], len(prev & elig)))
                self.assertTrue(cur <= elig); self.assertEqual(len(cur), min(n, len(elig)))
        fast = C.fast_values(mv, bk, 5)
        for j in range(5):
            self.assertAlmostEqual(fast[j], C.simulate(px, fills, [[s for s in bk[j, k] if s >= 0] for k in range(len(fills))], 5)["value"], places=10)

class Rules(unittest.TestCase):
    def test_gain_uses_exact_month_ends(self):
        days = bdays("2016-01-04", "2017-03-31")
        T = len(days); me = C.month_end_index(days)
        c = np.full(T, 10.0); c[me[11]] = 30.0; c[me[0]] = 15.0     # ranking at me[12]: me[11] / me[0]
        o = np.full(T, 10.0)
        c2 = c.copy(); c2[me[0]] = np.nan                           # missing close on the exact day
        px = C.Prices.from_arrays(days, {"A||": (o, c), "B||": (o, c2), "SPY||": (o, c)})
        members = [row("A", "2000-01-01", "9999"), row("B", "2000-01-01", "9999")]
        ranked, unr = C.rankable(members, px, days, me, 12)
        self.assertEqual(len(ranked), 1); self.assertEqual(unr, ["B"])
        self.assertAlmostEqual(ranked[0][0], 30 / 15 - 1)

    def test_top_n_skips_no_open_and_ties_by_ticker(self):
        days = bdays("2020-01-01", "2020-02-28"); T = len(days)
        o = np.full(T, 1.0); on = o.copy(); on[10] = np.nan
        px = C.Prices.from_arrays(days, {"A||": (o, o), "B||": (on, o), "C||": (o, o)})
        ranked = [(0.5, "B", 1), (0.2, "C", 2), (0.2, "A", 0)]
        self.assertEqual(C.top_n(ranked, px, 10, 2), [0, 2])           # B has no open; A before C on the tie

    def test_one_share_class(self):
        r = [row("GOOGL", "2000", "9999", cid="X"), row("GOOG", "2000", "9999", cid="X"), row("AAPL", "2000", "9999")]
        self.assertEqual([x["ticker_then"] for x in C.one_class(r)], ["AAPL", "GOOG"])

    def test_member_days_exclude_removal_day(self):
        r = [row("A", "2020-01-02", "2020-02-03")]
        self.assertEqual(len(C.members_on(r, "2020-02-03")), 0); self.assertEqual(len(C.members_on(r, "2020-01-02")), 1)

class LookAhead(unittest.TestCase):
    """Changing every made-up bar after a ranking day leaves the picks and fills up to that day unchanged."""
    def test_future_bars_do_not_move_the_past(self):
        days, members, px = world(11, n=80)
        periods, me = S.plan_periods(members, px, days)
        fills = [p["fill"] for p in periods]
        for kcut in (0, 20, len(periods) // 2, len(periods) - 2):
            i = periods[kcut]["i"]
            O2, C2 = px.O.copy(), px.C.copy()
            rng = np.random.default_rng(kcut)
            C2[:, i + 1:] *= np.exp(rng.normal(0, 0.3, C2[:, i + 1:].shape)); O2[:, i + 1:] *= np.exp(rng.normal(0, 0.3, O2[:, i + 1:].shape))
            O2[:, i + 1:][rng.random(O2[:, i + 1:].shape) < 0.01] = np.nan
            px2 = C.Prices.from_arrays(days, {k: (O2[px.si[k]], C2[px.si[k]]) for k in px.keys})
            per2, _ = S.plan_periods(members, px2, days)
            for k in range(kcut + 1):
                self.assertEqual(periods[k]["ranked"], per2[k]["ranked"], f"ranking on {days[periods[k]['i']]} moved")
            for n in (P["n_small"], P["n_wide"]):
                for k in range(kcut):                  # baskets bought at opens up to the ranking day
                    self.assertEqual(C.top_n(periods[k]["ranked"], px, fills[k], n), C.top_n(per2[k]["ranked"], px2, fills[k], n))
                a = C.simulate(px, fills[:kcut + 1], [C.top_n(p["ranked"], px, p["fill"], n) for p in periods[:kcut + 1]], 5, daily=True)
                b = C.simulate(px2, fills[:kcut + 1], [C.top_n(p["ranked"], px2, p["fill"], n) for p in per2[:kcut + 1]], 5, daily=True)
                self.assertEqual(a["at_fill"][:kcut], b["at_fill"][:kcut])           # fills on days up to the ranking day
                np.testing.assert_array_equal(a["daily"][:i + 1], b["daily"][:i + 1])
            # the ranking itself on the cut day also cannot see the purchase-day open
            self.assertEqual(periods[kcut]["ranked"], per2[kcut]["ranked"])

class Guards(unittest.TestCase):
    def test_draft_plan_refused(self):
        d = tempfile.mkdtemp(); plan = os.path.join(d, "PREREG_14_x_DRAFT.md")
        with open(plan, "w") as fh: fh.write("Status: DRAFT\n")
        h, src = C.HERE, C.PLAN_SOURCE
        saved = dict(os.environ); [os.environ.pop(v, None) for v in C.ENV_OVERRIDES]
        C.HERE, C.PLAN_SOURCE = d, plan
        try:
            with self.assertRaisesRegex(S.Refused, "draft"): S.guard_run()
            p2 = os.path.join(d, "PREREG_14_x.md"); os.rename(plan, p2); C.PLAN_SOURCE = p2
            with self.assertRaisesRegex(S.Refused, "Status"): S.guard_run()
        finally:
            C.HERE, C.PLAN_SOURCE = h, src; os.environ.clear(); os.environ.update(saved)

    def test_override_refused(self):
        os.environ["REPLAY_14_BARS"] = "/tmp/x"
        try:
            with self.assertRaises(S.Refused): S.guard_run()
        finally: os.environ.pop("REPLAY_14_BARS")

    def test_second_lock_refused(self):
        d1, d2 = tempfile.mkdtemp(), tempfile.mkdtemp()
        h, o = C.HERE, C.OFF_REPO_LOCK_DIR
        C.HERE, C.OFF_REPO_LOCK_DIR = d1, d2
        try:
            S.take_locks("test")
            with self.assertRaises(FileExistsError): S.take_locks("test again")
            os.remove(os.path.join(d1, S.LOCK))         # either lock alone also blocks
            with self.assertRaises(FileExistsError): S.take_locks("test again")
        finally: C.HERE, C.OFF_REPO_LOCK_DIR = h, o

    def test_pins_required_and_checked(self):
        d = tempfile.mkdtemp(); plan = os.path.join(d, "PREREG_14_frozen.md")
        h, src = C.HERE, C.PLAN_SOURCE
        saved = dict(os.environ); [os.environ.pop(v, None) for v in C.ENV_OVERRIDES]
        C.HERE, C.PLAN_SOURCE = d, plan
        try:
            with open(plan, "w") as fh: fh.write("# plan\nStatus: frozen\n")
            with self.assertRaisesRegex(S.Refused, "does not pin"): S.guard_run()
            with open(plan, "w") as fh: fh.write("Status: frozen\n" + "".join(f"- {k}: 0\n" for k in S.PINS))
            with self.assertRaisesRegex(S.Refused, "differs from the value pinned"): S.guard_run()
        finally:
            C.HERE, C.PLAN_SOURCE = h, src; os.environ.clear(); os.environ.update(saved)

class DataChecks(unittest.TestCase):
    def setUp(self):
        self.days = bdays("2020-01-01", "2021-06-30"); self.b = tempfile.mkdtemp(); self.a = tempfile.mkdtemp()
    def put(self, d, name, vols, close=None):
        with open(os.path.join(d, name + ".csv"), "w") as fh:
            fh.write("date,open,high,low,close,volume\n")
            for i, (day, v) in enumerate(zip(self.days, vols)):
                c = 10 + 0.01 * i if close is None else close[i]
                fh.write(f"{day},{c},{c},{c},{c},{v}\n" if v == 0 else f"{day},{c},{c + 1},{c - 1},{c},{v}\n")

    def test_zero_volume_is_no_bar_except_funds(self):
        T = len(self.days); v = [100 + i for i in range(T)]; v[50:60] = [0] * 10
        cl = [10 + 0.01 * i for i in range(T)]; cl[70:76] = [9.0] * 6           # six identical rows with volume
        self.put(self.b, "X", v, cl); self.put(self.b, "SPY", v, cl)
        px = C.Prices(self.days, [row("X", "2020-01-01", "2022-01-01")], bars=self.b, extra=("SPY",))
        x, spy = px.si["X||"], px.si["SPY||"]
        self.assertTrue(np.isnan(px.C[x, 50:60]).all()); self.assertFalse(np.isnan(px.C[x, 49]))
        self.assertTrue(np.isnan(px.C[x, 70:76]).all()); self.assertFalse(np.isnan(px.C[x, 76]))
        self.assertFalse(np.isnan(px.C[spy, 50:60]).any())

    def test_flags(self):
        T = len(self.days); rg = np.random.default_rng(3); cl = [10 + 0.01 * i for i in range(T)]
        nv = lambda: [int(x) for x in rg.integers(1000, 9000, T)]
        base = nv()
        st = nv(); st[100:106] = [0] * 6                               # six flat zero-volume sessions
        sc = list(cl); sc[100:106] = [sc[99]] * 6
        self.put(self.b, "S", st, sc); self.put(self.a, "S@2021-01-04", [2 * x for x in st], sc)
        iv = nv(); self.put(self.b, "I", iv); self.put(self.a, "I@2021-01-04", nv())   # another stock
        ov = nv(); self.put(self.b, "OK", ov); self.put(self.a, "OK@2021-01-04", [3 * x for x in ov])          # same stock, scaled
        self.put(self.b, "D1", base); self.put(self.b, "D2", base)
        self.put(self.a, "D1@2021-01-04", base); self.put(self.a, "D2@2021-01-04", base)
        m = [row(t, "2021-01-04", "2021-06-30") for t in ("S", "I", "OK", "D1", "D2")]
        r = C.data_checks(m, self.days, bars=self.b, asof=self.a)
        self.assertEqual([f["key"] for f in r["stale"]], ["S@2021-01-04"])
        self.assertEqual([f["key"] for f in r["identity"]], ["I@2021-01-04"])
        self.assertEqual([f["keys"] for f in r["duplicate"]], [["D1@2021-01-04", "D2@2021-01-04"]])
        plan = "- S@2021-01-04 is stale because the feed pads it\n- I@2021-01-04 because checked by hand\n"
        self.assertEqual(C.flags_listed(r, plan), ["D1@2021-01-04+D2@2021-01-04"])

class RealShape(unittest.TestCase):
    """The real member list and the real bar dates (which days have a bar), with made-up prices put in their place.
    No real price value is used: every real open and close is overwritten before scoring."""
    @unittest.skipUnless(os.path.exists(os.path.join(C.DATA_DEFAULT, "members.csv")), "no member list on this machine")
    def test_scorer_runs_on_the_real_shape(self):
        bars = os.path.join(C.DATA_DEFAULT, "bars")
        days = C.calendar(bars); members = C.load_members(os.path.join(C.DATA_DEFAULT, "members.csv"))
        px = C.Prices(days, members, bars)
        rng = np.random.default_rng(0)
        fake = 50 * np.exp(np.cumsum(rng.normal(0.0002, 0.02, px.C.shape), axis=1))
        mask = np.isnan(px.C)
        px2 = C.Prices.from_arrays(days, {k: (np.where(mask[i], np.nan, fake[i] * 1.001), np.where(mask[i], np.nan, fake[i])) for i, k in enumerate(px.keys)})
        del px
        r = S.score(members, px2, days)
        self.assertEqual(r["first_ranking_day"], "2017-01-31"); self.assertEqual(r["last_ranking_day"], "2026-10-30")
        self.assertEqual(r["second_half_first_ranking_day"], "2022-01-31")
        for k, n in (("small", P["n_small"]), ("wide", P["n_wide"])):
            self.assertEqual(r["setups"][k]["reported"]["short_baskets"], 0)
            self.assertTrue(all(len(v) == n for v in r["setups"][k]["picks"].values()))
            for v in r["setups"][k]["picks"].values():      # never two share classes of one company
                self.assertFalse({"GOOG", "GOOGL"} <= set(v) or {"FOX", "FOXA"} <= set(v) or {"NWS", "NWSA"} <= set(v))

class Funds(unittest.TestCase):
    def test_last_mark_includes_the_sale(self):
        days = bdays("2020-01-01", "2020-03-31"); T = len(days)
        px = C.Prices.from_arrays(days, {"SPY||": (np.full(T, 10.0), np.linspace(10, 12, T))})
        final, units, daily = C.hold_one(px, 0, 1, 5)
        self.assertAlmostEqual(daily[-1], final, places=14)
        self.assertAlmostEqual(final, (1 - 5e-4) / 10 * 12 * (1 - 5e-4), places=12)

class Report(unittest.TestCase):
    def test_refuses_before_opening_the_page(self):
        d = tempfile.mkdtemp(); out = os.path.join(d, "page.md")
        r = subprocess.run([sys.executable, os.path.join(C.HERE, "report_14.py"), "--from", d, "--out", out], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0); self.assertFalse(os.path.exists(out))

    def test_page_from_result_file_only(self):
        import report_14
        d = tempfile.mkdtemp()
        with self.assertRaises(SystemExit): report_14.build(d)            # no result file: refused
        days, members, px = world(3, n=80)
        res = S.score(members, px, days)
        out = dict(made_by="test", plan="made-up", run=dict(utc="made-up", commit="0" * 40, command="test"),
                   inputs=dict(members_csv_sha256="0" * 64, bars=dict(files=0, sha256="0" * 64), config_replay_14_plan_sha256="0" * 64,
                               config_replay_14_plan=P), coverage=S.coverage(members, px, days), result=res)
        with open(os.path.join(d, "results_14.json"), "w") as fh: json.dump(out, fh, default=float)
        page = report_14.build(d)
        for k in ("small", "wide"):
            self.assertIn(f"{res['setups'][k]['total'] * 100:+.1f}%", page)
        self.assertIn(f"{res['spy']['total'] * 100:+.1f}%", page)
        self.assertNotIn("nan", page.lower().replace("nanc", ""))

def score_world(seed, mom=0.0, cost_bps=None):
    days, members, px = world(seed, mom=mom)
    return S.score(members, px, days, cost_bps=cost_bps)

def noedge(worlds, costs=(None, 0)):
    """How often each mark passes by chance, in made-up worlds with no momentum, at the configured cost and at 0. Also
    the share of random paths each set-up beat, by tenths: with no edge it should be spread evenly (uniform)."""
    keys = ("1_above_spy", "2_above_everyone", "3_above_random_percentile", "4_above_spy_each_half")
    out = {}
    for cb in costs:
        tally = {n: {k: 0 for k in keys + ("all_four",)} for n in ("small", "wide")}
        share = {n: [] for n in tally}
        for w in range(worlds):
            r = score_world(1000 + w, cost_bps=cb)
            for n in tally:
                m = r["setups"][n]["marks"]
                for k in keys: tally[n][k] += m[k]
                tally[n]["all_four"] += r["setups"][n]["passes"]
                share[n].append(r["setups"][n]["random"]["share_of_draws_beaten"])
        name = f"cost_{P['cost_bps_per_side'] if cb is None else cb}_bps"
        out[name] = {n: dict(passes={k: f"{v}/{worlds}" for k, v in tally[n].items()},
                             share_beaten_mean=round(float(np.mean(share[n])), 3), share_beaten_var=round(float(np.var(share[n])), 3),
                             share_beaten_by_tenths=[int(x) for x in np.histogram(share[n], bins=10, range=(0, 1))[0]])
                     for n in tally}
    return out

if __name__ == "__main__":
    quick = "--quick" in sys.argv
    argv = [a for a in sys.argv if a != "--quick"]
    res = unittest.main(argv=argv, exit=False, verbosity=1).result
    if not res.wasSuccessful(): sys.exit(1)
    r = score_world(7)
    print("made-up world, one full score: ranking days", r["ranking_days"], "first", r["first_ranking_day"], "last", r["last_ranking_day"],
          "second half from", r["second_half_first_ranking_day"], "rankable", min(r["counts"]["rankable"]), "-", max(r["counts"]["rankable"]))
    rm = score_world(7, mom=0.9)
    print("made-up world with momentum built in, marks:", {n: rm["setups"][n]["marks"] for n in rm["setups"]})
    worlds = 10 if quick else 400
    ne = noedge(worlds)
    print("no-edge check (made-up worlds, no momentum), passes:", json.dumps(ne))
    if not quick:
        json.dump(dict(made_by="research_rig/test_14.py (made-up data only)", worlds=worlds, seeds=f"1000 to {999 + worlds}", by_cost=ne,
                       uniform_reference=dict(mean=0.5, var=round(1 / 12, 3)),
                       utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")), open(os.path.join(C.HERE, "noedge_14.json"), "w"), indent=1)
