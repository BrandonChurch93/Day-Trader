"""Only invented inputs, including temporary ZIPs, lock races, and calibration tapes."""
from concurrent.futures import ThreadPoolExecutor
import csv
from dataclasses import replace
import gzip
import io
import json
from math import exp,sqrt
from pathlib import Path
from random import Random
from statistics import median
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest
from unittest.mock import MagicMock,patch
from zipfile import ZipFile

from . import archive_18 as A, common_18 as C, score_18 as S


def snapshots(start=C.START,end=C.END):
    cs = tuple(C.Contract(i,i,str(i),start-1000,end+1) for i in range(1,9))
    return tuple(C.Snapshot(h*C.H,cs) for h in range(start-24,end,30*24))


class Fake:
    def __init__(self):
        self.open_overrides,self.mark_overrides,self.trade_overrides = {},{},{}
        self.funding_overrides,self.rank_overrides = {},{}
        self.terminal_keys = set()

    def trade_close(self,key,h):
        return self.trade_overrides.get((key,h),self.price(key,h+1))

    def traded(self,key,h):
        return C.valid(self.trade_close(key,h))

    def open_price(self,key,h):
        return self.open_overrides.get((key,h),self.price(key,h))

    def price(self,key,h):
        return 100.

    def mark_close(self,key,h):
        return self.mark_overrides.get((key,h),self.price(key,h+1))

    def funding(self,key,h):
        return self.funding_overrides.get((key,h),(True,None if h%C.FUND else 0.))

    def rank_funding(self,key,h,decision_seconds):
        for published,v in sorted(self.rank_overrides.get((key,h),()),reverse=True):
            if published<decision_seconds:
                return True,v
        return self.funding(key,h)

    def terminal(self,c,h,last_h):
        return c.key in self.terminal_keys


def blob(rows):
    buf = io.BytesIO()
    with ZipFile(buf,"w") as z:
        stream = io.StringIO()
        csv.writer(stream).writerows(rows)
        z.writestr("fixture.csv",stream.getvalue())
    return buf.getvalue()


class FundingCarryTests(unittest.TestCase):
    def setUp(self):
        self.t = C.START
        self.fill = self.t+C.P["fill_lag_hours"]
        self.exit = self.fill+C.ROLL
        self.end = (self.exit//24+1)*24
        self.snaps = snapshots(self.t,self.end+144)
        self.snap = self.snaps[0]

    def test_rank_release_strict_to_the_second_and_top30(self):
        t = self.t
        c = C.Contract(55,C.P["top_rank"]+1,"1",t-1000,t+1000)
        for at in (t*C.H,t*C.H+300):
            self.assertEqual(C.latest((self.snap,C.Snapshot(at,(c,))),t),self.snap)
        s = C.Snapshot(t*C.H-1,(c,))
        self.assertEqual(C.latest((self.snap,s),t),s)
        self.assertEqual(C.eligible(Fake(),s,t),[])
        self.assertEqual(C.eligible(Fake(),s,t,{55}),[(0.,c)])

    def test_no_stale_snapshot_or_duplicate_identity(self):
        with self.assertRaises(C.Incomplete):
            C.latest((self.snap,),self.t+(C.P["max_snapshot_age_days"]+1)*24)
        s = replace(self.snap,contracts=(self.snap.contracts[0],)*2)
        with self.assertRaises(C.Incomplete):
            C.eligible(Fake(),s,self.t)

    def test_future_publication_recent_settlement_and_fence_do_not_change_picks(self):
        f = Fake()
        p = C.P
        t = self.t
        lo = t-p["lookback_hours"]-C.FUND*p["funding_lag_intervals"]
        baseline = C.selection(C.eligible(f,self.snap,t))
        f.funding_overrides["1",t-C.FUND] = True,100.
        f.rank_overrides["1",lo] = [(t*C.H,100.),(t*C.H+1,101.)]
        f.trade_overrides["1",t-1] = None
        f.open_overrides["1",t] = None
        c = replace(self.snap.contracts[0],end=t,closed_effective=t,closed_known_at=t*C.H+1)
        s = replace(self.snap,contracts=(c,*self.snap.contracts[1:]))
        self.assertEqual([(c.key,k) for c,k in C.selection(C.eligible(f,s,t))],
                         [(c.key,k) for c,k in baseline])
        f.rank_overrides["1",lo].append((t*C.H-1,102.))
        self.assertNotEqual(C.selection(C.eligible(f,self.snap,t)),baseline)
        c = replace(c,closed_known_at=t*C.H-1)
        s = replace(s,contracts=(c,*self.snap.contracts[1:]))
        self.assertNotIn(c,[x for _,x in C.eligible(f,s,t)])

    def test_offgrid_missing_rate_and_prior_coverage_counted(self):
        f = Fake()
        p,t = C.P,self.t
        lo = t-p["lookback_hours"]-C.FUND*p["funding_lag_intervals"]
        f.funding_overrides.update({("1",lo):(True,None),("2",lo+1):(True,.01),
                                    ("3",lo):(False,None)})
        from collections import Counter
        count = Counter()
        self.assertEqual(len(C.eligible(f,self.snap,t,funnel=count)),5)
        for k in ("expected_settlement_missing","off_grid_or_invalid_settlement","funding_uncovered_or_unavailable"):
            self.assertEqual(count[k],1)

    def test_next_open_and_funding_marks(self):
        f = Fake()
        f.open_overrides["1",self.t] = None
        f.funding_overrides["8",self.t] = True,99.
        f.funding_overrides["8",self.fill] = True,99.
        f.funding_overrides["8",self.t+C.FUND] = True,.01
        f.mark_overrides["8",self.t+C.FUND-1] = 160.
        r = C.run_book(f,self.snaps,self.t,self.end)
        self.assertEqual(r.traded,1)
        self.assertAlmostEqual(r.final,1-r.fees+.01*160/(6*100))
        self.assertAlmostEqual(r.funding_pnl,.01*160/(6*100))
        self.assertGreater(r.max_drawdown,.10)
        self.assertFalse(any(r.marks))
        f.open_overrides["1",self.fill] = None
        self.assertEqual(C.run_book(f,self.snaps,self.t,self.end).no_open,1)

    def test_net_delta_costs_and_gross_comparator(self):
        f = Fake()
        end = self.end+C.ROLL
        net = C.run_book(f,self.snaps,self.t,end)
        gross = C.run_book(f,self.snaps,self.t,end,gross_reopen=True)
        fee = C.P["judged_cost_bps"]/10_000
        self.assertEqual(net.traded,2)
        self.assertAlmostEqual(gross.final,(1-2*fee)**2)
        self.assertAlmostEqual(net.fees,fee*(1+fee+1-fee))
        self.assertGreater(net.final,gross.final)
        self.assertAlmostEqual(net.final,1+net.price_pnl+net.funding_pnl-net.fees)

    def test_outgoing_only_at_roll_with_intrahour_event(self):
        f = Fake()
        f.funding_overrides["8",self.exit] = True,.006
        r = C.run_book(f,self.snaps,self.t,self.end+C.ROLL)
        self.assertAlmostEqual(r.funding_pnl,.001)

    def test_gap_zeroes_only_evidenced_terminal_long_and_continues(self):
        f = Fake()
        h = self.fill+5
        for k in "126":
            f.trade_overrides[k,h] = None
        f.terminal_keys.update(("1","6"))
        r = C.run_book(f,self.snaps,self.t,self.end)
        a,b,c = r.forced
        self.assertEqual((a["price"],b["price"],c["price"]),(0.,100.,100.))
        self.assertEqual([x["last_trade_hour"] for x in r.forced],[h-1]*3)
        self.assertEqual([x["zeroed"] for x in r.forced],[True,False,False])
        self.assertAlmostEqual(r.price_pnl,-1/6)
        self.assertAlmostEqual(r.final,1+r.price_pnl+r.funding_pnl-r.fees)

    def test_missing_exit_open_and_mark_are_reported(self):
        f = Fake()
        f.open_overrides["8",self.exit] = None
        f.mark_overrides["8",self.exit-1] = None
        r = C.run_book(f,self.snaps,self.t,self.end)
        self.assertEqual(r.forced[0]["reason"],"no_tradable_exit_open")
        self.assertEqual(r.funnel["occupied_mark_fallback"],1)
        f.funding_overrides["8",self.fill+1] = False,None
        r = C.run_book(f,self.snaps,self.t,self.end)
        self.assertEqual(r.forced[0]["reason"],"occupied_funding_coverage_gap")
        self.assertEqual(r.forced[0]["last_trade_hour"],self.fill)

    def test_threshold_boundaries_and_short_loss_shock(self):
        p = C.P
        y = dict.fromkeys(range(p["min_positive_years"]),.001)
        self.assertEqual(C.marks(p,p["min_sharpe"],p["max_drawdown"],y,p["min_traded_slots"]),(True,)*3)
        y[0] = 0.
        self.assertEqual(C.marks(p,p["min_sharpe"]-.00001,p["max_drawdown"]+.00001,y,
                                 p["min_traded_slots"]),(False,)*3)
        f = Fake()
        f.mark_overrides["8",self.fill+3] = 260.
        self.assertGreater(C.run_book(f,self.snaps,self.t,self.end).max_drawdown,p["max_drawdown"])

    def test_random_seed_and_denominators(self):
        p = C.P|{"random_draws":20}
        f = Fake()
        r = C.run_book(f,self.snaps,self.t,self.end)
        f.mark_overrides["1",self.fill+1] = 800.
        a = C.random_books(f,self.snaps,self.t,self.end,p=p)
        self.assertEqual(a,C.random_books(f,self.snaps,self.t,self.end,p=p))
        q = C.random_summary(a,r,p)
        self.assertEqual(a[0].seed,p["seed"])
        self.assertEqual(q["requested"],q["complete"]+len(q["refusals"]))
        self.assertEqual(q["complete"],q["defined_sharpe"]+q["undefined_sharpe"])
        self.assertGreater(len(q["refusals"]),0)
        self.assertGreater(q["complete"],0)
        self.assertEqual(C.quantiles((0,10),[.05,.5,.95]),{"0.05":.5,"0.5":5.,"0.95":9.5})

    def test_adapter_actual_paths_hash_jitter_and_strict_rank_lag(self):
        h = self.t
        pair = "FAKEUSDT"
        prefix = "data/futures/um/monthly/"
        f = f"{prefix}fundingRate/{pair}/{pair}-fundingRate-2022-01.zip"
        k = f"{prefix}klines/{pair}/1h/{pair}-1h-2022-01.zip"
        m = f"{prefix}markPriceKlines/{pair}/1h/{pair}-1h-2022-01.zip"
        data = {f:blob(([(h*C.H)*1000+10,8,.001],)),k:blob(([
            h*C.H*1000,100,101,99,100,42],)),m:blob(([h*C.H*1000,100,101,99,101],))}
        with TemporaryDirectory() as root:
            root = Path(root)
            for name,b in data.items():
                path = root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b)
            meta = {"errors":{},"archives":{name:dict(where="replay_16",n=1,sha256=A.digest(b))
                                             for name,b in data.items()}}
            p = C.P|{"end":h+48}
            tape = A.Tape(root,[meta],{"fake":pair},set(),p)
            self.assertEqual(tape.open_price("fake",h),100.)
            self.assertEqual(tape.mark_close("fake",h),101.)
            self.assertEqual(tape.rank_funding("fake",h,(h+C.FUND)*C.H),(False,None))
            self.assertEqual(tape.rank_funding("fake",h,(h+C.FUND)*C.H+1),(True,.001))
            (root/f).write_bytes(blob(([(h*C.H)*1000+10,8,.002],)))
            with self.assertRaisesRegex(C.Incomplete,"hash mismatch"):
                A.Tape(root,[meta],{"fake":pair},set(),p)

    def test_adapter_raw_ranks_fail_closed(self):
        row = dict(date="2021-12-30",known_at=(self.t-24)*C.H,sha256="0"*64,
                   top_raw=[dict(cmcRank=i,id=i) for i in range(1,C.P["top_rank"]+1)])
        self.assertEqual(len(A.parse_snapshots([row],(),C.P)[0][0].ranks),C.P["top_rank"])
        with TemporaryDirectory() as tmp:
            pp = Path(tmp)/"20211230.html.gz"
            raw = gzip.compress(('"listingHistorical":{"data":'+json.dumps(row["top_raw"])+'}').encode())
            pp.write_bytes(raw)
            row["sha256"] = A.digest(raw)
            A.verify_rank_pages([row],Path(tmp),C.P)
            row["top_raw"][0]["id"] = 5000
            with self.assertRaisesRegex(C.Incomplete,"differ"):
                A.verify_rank_pages([row],Path(tmp),C.P)
        row["top_raw"][1]["cmcRank"] = 1
        with self.assertRaisesRegex(C.Incomplete,"unique ranks"):
            A.parse_snapshots([row],(),C.P)

    def test_exact_us_product_mapping_and_unmatched_evidence(self):
        src = {v:dict(count=1,contracts=[{k:f"product-{v}"}]) for v,k in zip(A.VENUES,A.ROSTER_KEYS)}
        raw = {v:{f"product-{v}":dict(coin_id=42,evidence_sha256="1"*64)} for v in A.VENUES}
        raw["kalshi"]["product-kalshi"] = dict(coin_id=None,reason="scale identity not verified")
        ids,counts = A.roster_map(raw,src)
        self.assertEqual(ids["coinbase"],{42})
        self.assertEqual(ids["kalshi"],set())
        self.assertEqual(counts["kalshi"]["original"],1)
        raw["kalshi"]["not-in-source"] = raw["kalshi"].pop("product-kalshi")
        with self.assertRaisesRegex(C.Incomplete,"every original"):
            A.roster_map(raw,src)

    def test_offline_loader_requires_pinned_underlying_evidence(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"cmc").mkdir()
            (root/"evidence").mkdir()
            top = [dict(cmcRank=i,id=i) for i in range(1,C.P["top_rank"]+1)]
            page = gzip.compress(('"listingHistorical":{"data":'+json.dumps(top)+'}').encode())
            (root/"cmc/20211230.html.gz").write_bytes(page)
            raw = dict(ranks=[dict(date="2021-12-30",known_at=(self.t-24)*C.H,
                                   sha256=A.digest(page),top_raw=top)],
                       viewed_manifest={"errors":{},"archives":{}},
                       held_manifest={"errors":{},"archives":{}})
            pins,paths = {},{}
            def put(k,v):
                paths[k] = root/f"{k}.json"
                b = json.dumps(v).encode()
                paths[k].write_bytes(b)
                pins[k] = A.digest(b)
            for k,v in raw.items():
                put(k,v)
            included = {}
            for venue,key in zip(A.VENUES,A.ROSTER_KEYS):
                put(venue,dict(count=1,contracts=[{key:venue}]))
                included[venue] = {venue:dict(coin_id=None,reason="not mapped in fixture")}
            b = b"made-up listing record"
            pin = A.digest(b)
            (root/"evidence"/pin).write_bytes(b)
            put("universe",dict(version=1,scope="reconstructed_verified_subset",
                rank_source_sha256=pins["ranks"],archive_manifests={k:pins[k] for k in
                    ("viewed_manifest","held_manifest")},contracts=[dict(
                    coin_id=1,symbol="FAKEUSDT",begin=self.t-300,end=self.end,
                    listed_known_at=(self.t-500)*C.H,closed_effective=None,closed_known_at=None,
                    listing_evidence_sha256=pin)],us_rosters=included,
                unmatched_judged_ids={str(i):"not in catalogue" for i in range(2,C.P["top_rank"]+1)}))
            _,snaps,_,coverage = A.load(paths,pins,root,C.P,evidence_dir=root/"evidence")
            self.assertEqual(len(snaps[0].ranks),C.P["top_rank"])
            self.assertEqual(coverage["top_ids_with_dated_mapping"],1)
            self.assertIsNone(coverage["full_market_dead_coin_retention"])
            (root/"evidence"/pin).write_bytes(b"changed notice")
            with self.assertRaisesRegex(C.Incomplete,"input hash mismatch"):
                A.load(paths,pins,root,C.P,evidence_dir=root/"evidence")

    def test_terminal_checks_same_coin_successor_evidence(self):
        t = self.t
        tape = A.Tape.__new__(A.Tape)
        tape.lo,tape.hi,tape.symbols,tape.notices = t,t+2,{"old":"FAKEUSDT","new":"FAKE2USDT"},{"old"}
        c = C.Contract(1,1,"old",t-24,t+1,closed_effective=t+1,closed_known_at=t*C.H)
        new = C.Contract(1,1,"new",t+1,t+3)
        tape.store = {"FAKEUSDT":(None,[100.,0.,0.]),"FAKE2USDT":(None,[0.,0.,100.])}
        tape.by_coin = {1:[c,new]}
        self.assertFalse(tape.terminal(c,t+1,t))
        tape.by_coin = {1:[c]}
        self.assertTrue(tape.terminal(c,t+1,t))

    def test_lock_rejects_second_attempt_even_on_failure(self):
        with TemporaryDirectory() as tmp:
            lock,out = (Path(tmp)/name for name in ("lock","result"))
            def fail(binding):
                self.assertTrue(lock.exists())
                raise RuntimeError("fake read failed")
            with self.assertRaises(RuntimeError):
                S.one_shot(lock,out,lambda:({"test":"yes"},C.P),fail)
            self.assertIn("failed",lock.read_text())
            self.assertFalse(out.exists())
            with self.assertRaises(C.Incomplete):
                S.one_shot(lock,out,lambda:self.fail("authorized twice"),fail)

    def test_lock_race_and_no_scoring_before_authorization(self):
        with TemporaryDirectory() as tmp:
            lock,out = (Path(tmp)/name for name in ("lock","result"))
            def denied():
                raise C.Incomplete("unfrozen")
            with self.assertRaises(C.Incomplete):
                S.one_shot(lock,out,denied,lambda _:self.fail("read before authorization"))
            self.assertFalse(lock.exists())
            gate = Barrier(2)
            def authorize():
                gate.wait(timeout=5)
                return {},C.P
            def execute():
                try:
                    return S.one_shot(lock,out,authorize,lambda _:{"ok":True})
                except C.Incomplete:
                    return None
            with ThreadPoolExecutor(2) as actors:
                self.assertCountEqual(actors.map(lambda _:execute(),range(2)),({"ok":True},None))
            self.assertTrue(out.exists())

    def test_selftest_does_not_call_adapter_or_lock(self):
        with (patch.object(S.A,"load",side_effect=AssertionError("real archive read")),
              patch.object(S,"one_shot",side_effect=AssertionError("real lock touched")),
              patch.object(S.unittest,"TextTestRunner",return_value=MagicMock()),
              patch(__name__+".power") as fake_power,
              patch("sys.argv",["score_18","--selftest"])):
            self.assertEqual(S.main(),0)
            fake_power.assert_called_once()


class Noise:
    """Daily Gaussian shocks distributed as one daily bar jump on opposing price legs."""
    def __init__(self,seed,target,p):
        rng = Random(seed)
        self.lo = p["start"]-p["lookback_hours"]-p["funding_lag_intervals"]*p["funding_interval_hours"]
        count = p["end"]-self.lo+2
        a,b = [100.]*count,[100.]*count
        level = 0.
        for i in range(count):
            if i and (self.lo+i)%24==0:
                level += rng.gauss(0,p["power_sigma_daily"])
            a[i],b[i] = 100*exp(level),100*exp(-level)
        self.a,self.b = a,b
        self.cadence = p["funding_interval_hours"]
        self.rate = target*p["power_sigma_daily"]/(sqrt(p["annualization_days"])*(24/self.cadence))

    def open_price(self,key,h):
        return (self.a if key in "12345" else self.b)[h-self.lo]

    def trade_close(self,key,h):
        return self.open_price(key,h+1)

    mark_close = trade_close

    def traded(self,key,h):
        return True

    def funding(self,key,h):
        return True,(None if h%self.cadence else -self.rate if key in "123" else self.rate if key in "678" else 0.)

    def rank_funding(self,key,h,decision_seconds):
        return self.funding(key,h)


def power():
    p = C.P
    snaps = snapshots()
    for target in p["power_sharpes"]:
        count, sharpe = [0,0,0,0],[]
        for i in range(p["power_pairs"]):
            r = C.run_book(Noise(p["power_seed"]+i,target,p),snaps,p["start"],p["end"],p=p)
            sharpe.append(r.sharpe)
            for j,hit in enumerate((*r.marks,all(r.marks))):
                count[j] += hit
        print(f"MEASURED synthetic target Sharpe {target:.1f}: median {median(sharpe):.3f}, "
              f"marks Sharpe/DD/years/all {count} of {p['power_pairs']}",flush=True)
