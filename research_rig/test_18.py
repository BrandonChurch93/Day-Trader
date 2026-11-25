"""Tests use only generated snapshots, rates and prices."""
import math
from random import Random
import unittest

from . import common_18 as C


def snapshots(start=C.START, end=C.END):
    contracts = tuple(C.Contract(i,i,str(i),start-1000,end+1) for i in range(1,9))
    return tuple(C.Snapshot(h,contracts) for h in range(start-24,end,30*24))


class Fake:
    def __init__(self, seed=1, planted=False, moving=False):
        rng = Random(seed)
        self.phase = [rng.random()*7 for _ in range(9)]
        self.strength = [rng.uniform(.00055,.00085) for _ in range(9)]
        self.planted, self.moving = planted, moving
        self.open_overrides, self.mark_overrides, self.funding_overrides = {}, {}, {}

    def traded(self, key, t):
        return self.open_price(key,t) is not None

    def open_price(self, key, t):
        return self.open_overrides.get((key,t),self.price(key,t))

    def price(self, key, t):
        if not self.moving:
            return 100.
        return 100 + .21*math.sin(t/17+self.phase[int(key)]) + .12*math.sin(t/7+self.phase[int(key)])

    def mark_close(self, key,t):
        return self.mark_overrides.get((key,t),self.price(key,t+1))

    def funding(self, key,t):
        if (key,t) in self.funding_overrides:
            return self.funding_overrides[key,t]
        if t % C.FUND:
            return True,None
        i = int(key)
        if not self.planted:
            return True,0.
        return True, self.strength[i]*(-1 if i<=3 else 1 if i>=6 else 0)


class FundingCarryTests(unittest.TestCase):
    def setUp(self):
        self.t = C.START
        self.e = self.t+C.ROLL
        self.snaps = snapshots(self.t,self.e)
        self.snap = self.snaps[0]

    def test_point_in_time_top30_and_independent_shown_filter(self):
        t = self.t
        c = C.Contract(55,31,"1",t-1000,t+1000)
        s = C.Snapshot(t,(c,))
        self.assertEqual(C.latest((self.snap,s),t-1),self.snap)
        self.assertEqual(C.latest((self.snap,s),t),s)
        self.assertEqual(C.eligible(Fake(),s,t),[])
        self.assertEqual(C.eligible(Fake(),s,t,{55}),[(0.,c)])

    def test_no_stale_snapshot_or_duplicate_identity(self):
        with self.assertRaises(C.Incomplete):
            C.latest((self.snap,),self.t+46*24)
        s = C.Snapshot(self.t,(self.snap.contracts[0],)*2)
        with self.assertRaises(C.Incomplete):
            C.eligible(Fake(),s,self.t)

    def test_known_past_only_and_full_fence(self):
        f = Fake()
        f.funding_overrides["1",self.t] = True,100.
        pool = C.eligible(f,self.snap,self.t)
        self.assertEqual([(c.key,s) for c,s in C.selection(pool)],
                         [("1",1),("2",1),("3",1),("6",-1),("7",-1),("8",-1)])
        f.funding_overrides["1",self.t-C.ROLL] = True,None
        f.funding_overrides["2",self.t-1] = True,.01
        c = C.Contract(3,3,"3",self.t-C.ROLL+1,self.e+1)
        s = C.Snapshot(self.t,(c,*self.snap.contracts[:2],*self.snap.contracts[3:]))
        self.assertEqual([x.key for _,x in C.eligible(f,s,self.t)],list("45678"))

    def test_handoff_and_all_in_fee(self):
        f = Fake()
        for h in range(self.t,self.e+1,8):
            for k in "123678":
                f.funding_overrides[k,h] = True,-.001 if k in "123" else .001
        f.funding_overrides["1",self.t] = True,9.  # not earned by incoming book
        for bps in C.COSTS:
            with self.subTest(bps=bps):
                r = C.run_book(f,self.snaps,self.t,self.e,bps)
                self.assertAlmostEqual(r.final,1-2*bps/10000+9*.001)
                self.assertFalse(any(r.marks))

    def test_mark_not_entry_for_funding_and_intraday_drawdown(self):
        f = Fake()
        f.funding_overrides["8",self.t+8] = True,.01
        f.mark_overrides["8",self.t+7] = 160.
        r = C.run_book(f,self.snaps,self.t,self.e)
        self.assertAlmostEqual(r.final,1-.0024+.01*160/(6*100))
        self.assertGreater(r.max_drawdown,.10)

    def test_missing_entry_all_cash_no_fallback(self):
        f = Fake()
        f.open_overrides["1",self.t] = None
        r = C.run_book(f,self.snaps,self.t,self.e)
        self.assertEqual((r.final,r.traded,r.no_open,r.sharpe),(1.,0,1,None))

    def test_missing_open_basket_inputs_refuse(self):
        for kind,k,h,v in (("mark","8",self.e-1,None),
                           ("funding","8",self.t+10,(False,None)),
                           ("open","8",self.e,None)):
            with self.subTest(kind=kind):
                f = Fake()
                getattr(f,kind+"_overrides")[k,h] = v
                with self.assertRaises(C.Incomplete):
                    C.run_book(f,self.snaps,self.t,self.e)

    def test_no_lookahead_fence_filter(self):
        c = C.Contract(1,1,"1",self.t-1000,self.t+6)
        s = C.Snapshot(self.t,(c,*self.snap.contracts[1:]))
        self.assertIn(c,[v for _,v in C.eligible(Fake(),s,self.t)])
        with self.assertRaisesRegex(C.Incomplete,"dated fence"):
            C.run_book(Fake(),(s,),self.t,self.e)

    def test_random_yardstick_reproducible_and_same_size(self):
        f = Fake(planted=True)
        p = C.eligible(f,self.snap,self.t)
        s = C.selection(p,Random(C.SEED))
        self.assertEqual(len({c.key for c,_ in s}),6)
        self.assertEqual(sum(side for _,side in s),0)
        a = C.random_books(f,self.snaps,self.t,self.e,draws=4)
        b = C.random_books(f,self.snaps,self.t,self.e,draws=4)
        self.assertEqual(a,b)
        self.assertTrue(all(d.result.traded == 1 and not any(d.result.marks) for d in a))
        unavailable = s[0][0].key
        f.open_overrides[unavailable,self.e] = None
        b = C.random_books(f,self.snaps,self.t,self.e,draws=20)
        self.assertEqual(b[0].seed,C.SEED)
        self.assertIsNone(b[0].result)
        self.assertIn("exit",b[0].refusal)
        self.assertTrue(any(d.result is not None for d in b))


def power():
    """Paired full-clock worlds: same prices, add only a persistent rate spread."""
    snaps = snapshots()
    total = 20
    null = planted = 0
    for i in range(total):
        a,b = (C.run_book(Fake(18100+i,edge,moving=True),snaps,C.START,C.END)
               for edge in (False,True))
        null += all(a.marks)
        planted += all(b.marks)
    if null > 2 or planted < 16:
        raise AssertionError(f"power gate missed: {null}/{total} null, {planted}/{total} planted")
    print(f"MEASURED made-up power check: {null}/{total} null, {planted}/{total} planted clear all marks")
