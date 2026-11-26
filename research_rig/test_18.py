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
        self.offsets = {}
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

    def funding_event(self,key,h):
        covered,rate = self.funding(key,h)
        return covered,rate,self.offsets.get((key,h),0)

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


def archive_fixture(root,pair,kind,rows):
    stem = f"{pair}-fundingRate" if kind=="fundingRate" else "1h/"+pair+"-1h"
    name = f"data/futures/um/monthly/{kind}/{pair}/{stem}-2022-01.zip"
    path = root/name
    path.parent.mkdir(parents=True,exist_ok=True)
    data = blob(rows)
    path.write_bytes(data)
    clocks = [A.clock_us(r[0])//10**6 for r in rows]
    return name,dict(where="replay_16",n=len(rows),sha256=A.digest(data),
                     first=min(clocks,default=None),last=max(clocks,default=None))


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

    def test_migration_alias_links_one_lineage_only_at_its_effective_hour(self):
        t = self.t
        original = dict(coin_id=42,symbol="OLDUSDT",begin=t-1000,end=t-200,listed_known_at=(t-1000)*C.H,
                        closed_effective=t-200,closed_known_at=(t-300)*C.H,delisting_notice=False,
                        listing_evidence_sha256="a"*64,closure_evidence_sha256="b"*64)
        successor = original|dict(coin_id=43,symbol="NEWUSDT",begin=t-96,end=t+1000,
                                  listed_known_at=(t-96)*C.H,closed_effective=None,closed_known_at=None,
                                  closure_evidence_sha256=None)
        u = dict(version=1,scope="reconstructed_verified_subset",contracts=[original,successor],
                 migration_links={"43":dict(lineage_id=42,effective_hour=t-96)})
        contracts,_,_ = A.catalogue(u)
        self.assertEqual([c.coin_id for c in contracts],[42,42])
        aliases = tuple((i,*x) for i,x in A.migration_links(u).items())
        page = C.Snapshot((t-1000)*C.H,contracts,((1,43),),aliases)
        self.assertEqual(C.eligible(Fake(),page,t-500),[])
        self.assertEqual([c for _,c in C.eligible(Fake(),replace(page,ranks=((1,42),)),t-500)],[contracts[0]])
        self.assertEqual([c for _,c in C.eligible(Fake(),page,t)],[contracts[1]])
        u["contracts"][0] = original|dict(end=t-80)
        with self.assertRaisesRegex(C.Incomplete,"overlapping segments for canonical lineage"):
            A.catalogue(u)
        u["contracts"][0] = original
        u["migration_links"]["43"]["effective_hour"] += 1
        with self.assertRaisesRegex(C.Incomplete,"predates"):
            A.catalogue(u)

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
        self.assertEqual(C.run_book(f,(s,),self.t,self.end).no_open,1)
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

    def test_exact_handoff_before_at_and_after_fill(self):
        f = Fake()
        h = self.exit
        second = replace(self.snap,known_at=(h-2)*C.H,
                         contracts=tuple(c for c in self.snap.contracts if c.key!="6"))
        snaps = self.snap,second
        fee = C.P["judged_cost_bps"]/10000
        for key,offset,expected in (("5",-10_000_000,0.),("5",0,0.),("5",10_000_000,.001*(1-fee)),
                ("6",-10_000_000,.0012),("6",0,.001),("6",10_000_000,0.),
                ("8",-10_000_000,.0012),("8",0,.001),("8",10_000_000,.001*(1-fee))):
            with self.subTest(key=key,offset=offset):
                f = Fake()
                f.mark_overrides[key,h-2] = 120.
                f.funding_overrides[key,h] = True,.006
                f.offsets[key,h] = offset
                r = C.run_book(f,snaps,self.t,self.end+C.ROLL)
                self.assertAlmostEqual(r.funding_pnl,expected)

    def test_subhour_utc_year_and_exact_midnight_boundary(self):
        h = A.day_hour("2023-01-01")
        start,end = h-48,h+48
        snaps = snapshots(start,end)
        fee = C.P["judged_cost_bps"]/10000
        for offset in (-10_000_000,0,10_000_000):
            with self.subTest(offset=offset):
                f = Fake()
                f.funding_overrides["8",h] = True,.06
                f.offsets["8",h] = offset
                r = C.run_book(f,snaps,start,end)
                self.assertAlmostEqual(r.funding_pnl,.01)
                self.assertAlmostEqual(r.years[2022],(.01 if offset<=0 else 0.)-fee)
                self.assertAlmostEqual(r.years[2023],r.final/(1+r.years[2022])-1)
                self.assertEqual(r.years[2023]>0,offset>0)

    def test_distinct_settlement_timestamps_expose_intervening_drawdown(self):
        f = Fake()
        h = self.t+24
        for key,offset in (("1",1_000_000),("8",20_000_000)):
            f.funding_overrides[key,h] = True,2.
            f.offsets[key,h] = offset
        split = C.run_book(f,self.snaps,self.t,self.end)
        self.assertAlmostEqual(split.funding_pnl,0.)
        self.assertAlmostEqual(split.max_drawdown,1/3+C.P["judged_cost_bps"]/10000)
        f.offsets["8",h] = f.offsets["1",h]
        simultaneous = C.run_book(f,self.snaps,self.t,self.end)
        self.assertAlmostEqual(simultaneous.max_drawdown,simultaneous.fees)

    def test_drawdown_uses_pre_fee_open_equity_before_resizing(self):
        f = Fake()
        h = self.exit
        f.open_overrides["1",h] = f.open_overrides["1",h+C.ROLL] = 400.
        for b in range(h,h+C.ROLL):
            f.mark_overrides["1",b] = 400.
        fee = C.P["judged_cost_bps"]/10000
        pre = 1-fee+.5
        new_qty = pre/600
        traded = 400*abs(new_qty/4-1/600)+500*abs(new_qty-1/600)
        post = pre-fee*traded
        trough = pre*(1-.2501)
        f.mark_overrides["8",h] = 100+(post-trough)/new_qty
        r = C.run_book(f,self.snaps,self.t,self.end+C.ROLL)
        self.assertAlmostEqual(r.max_drawdown,.2501,places=8)
        self.assertLess(1-trough/post,.25)
        self.assertFalse(C.marks(C.P,r.sharpe,r.max_drawdown,r.years,r.traded)[1])

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
            self.assertEqual(tape.funding_event("fake",h),(True,.001,10_000))
            self.assertEqual(tape.rank_funding("fake",h,(h+C.FUND)*C.H),(False,None))
            self.assertEqual(tape.rank_funding("fake",h,(h+C.FUND)*C.H+1),(True,.001))
            (root/f).write_bytes(blob(([(h*C.H)*1000+10,8,.002],)))
            with self.assertRaisesRegex(C.Incomplete,"hash mismatch"):
                A.Tape(root,[meta],{"fake":pair},set(),p)

    def test_adapter_symbol_reuse_never_leaks_successor_observations(self):
        with TemporaryDirectory() as tmp:
            t,pair = self.t+240,"FAKEUSDT"
            lo = t-80
            old = C.Contract(1,1,"old",self.t-240,lo)
            new = C.Contract(2,2,"new",lo,t+24)
            paths = dict([archive_fixture(Path(tmp),pair,"fundingRate",
                          [[h*C.H,8,.001] for h in range(lo,t,8)]),
                          archive_fixture(Path(tmp),pair,"klines",
                          [[(t-2)*C.H,100,100,100,100,42]])])
            tape = A.Tape(Path(tmp),[dict(archives=paths,errors={})],{"old":pair,"new":pair},set(),
                          C.P|{"end":t+24},contracts=(old,new))
            self.assertIsNone(tape.trade_close("old",t-2))
            self.assertEqual(tape.funding("old",lo),(False,None))
            self.assertEqual(tape.funding("new",lo),(True,.001))
            self.assertEqual(C.eligible(tape,C.Snapshot(t*C.H-1,(old,new)),t),[(.009000000000000001,new)])

    def test_adapter_empty_truncated_and_missing_grid_are_unknown(self):
        with TemporaryDirectory() as tmp:
            h,pair = self.t,"FAKEUSDT"
            p = C.P|{"end":h+48}
            for stamps in ([],[0],[0,8],[0,4,12,16]):
                args = [[(h+k)*C.H,8,.001] for k in stamps]
                name,m = archive_fixture(Path(tmp),pair,"fundingRate",args)
                tape = A.Tape(Path(tmp),[dict(archives={name:m},errors={})],{"a":pair},set(),p)
                self.assertEqual(tape.funding("a",h+24),(False,None))
                self.assertEqual(tape.funding("a",h+16),(True,.001) if 16 in stamps else (False,None))
                self.assertEqual(tape.funding("a",h+1),(len(stamps)>1,None))
                self.assertEqual(tape.funding("a",h+8),(8 in stamps,.001 if 8 in stamps else None))

    def test_archive_metadata_only_counts_observed_clocks_in_the_identity(self):
        with TemporaryDirectory() as tmp:
            h,pair = self.t,"FAKEUSDT"
            old = C.Contract(1,1,"old",h-100,h+2)
            new = C.Contract(2,2,"new",h+2,h+240)
            meta = dict([archive_fixture(Path(tmp),pair,"fundingRate",[[(h+8)*C.H,8,.001]])])
            symbols = dict(old=pair,new=pair)
            p = C.P|{"end":h+240}
            o = A.archive_inventory([dict(archives=meta)],{pair},p)
            inventory = A.period_inventory((old,new),symbols,o,p)
            self.assertEqual(inventory["old"]["2022-01"]["fundingRate"],"unknown_missing_manifest_rows")
            self.assertEqual(inventory["new"]["2022-01"]["fundingRate"],"manifest_rows_listed")

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
            p = C.P|{"end":self.t+240}
            top = [dict(cmcRank=i,id=i) for i in range(1,C.P["top_rank"]+1)]
            page = gzip.compress(('"listingHistorical":{"data":'+json.dumps(top)+'}').encode())
            raw,periods,evidence = [],{},set()
            for d in A.expected_rank_dates(p):
                path_date = d.replace("-","")
                uri = "https://coinmarketcap.com/historical/"+path_date+"/"
                (root/f"cmc/{path_date}.html.gz").write_bytes(page)
                raw.append(dict(date=d,known_at=(A.day_hour(d)+24)*C.H,sha256=A.digest(page),top_raw=top))
                periods[d] = dict(uri=uri,captured_at=None,status="observed",revision_history="unknown",
                                  availability="next_utc_day_proxy",sha256=A.digest(page))
            pins,paths = {},{}
            def put(k,v):
                paths[k] = root/f"{k}.json"
                b = json.dumps(v).encode()
                paths[k].write_bytes(b)
                pins[k] = A.digest(b)
            put("ranks",raw)
            put("viewed_manifest",dict(errors={},archives={}))
            put("held_manifest",dict(errors={},archives={}))
            included,sources = {},{}
            for venue,key in zip(A.VENUES,A.ROSTER_KEYS):
                sources[venue] = dict(count=1,contracts=[{key:venue}])
                put(venue,sources[venue])
                included[venue] = {venue:dict(coin_id=None,reason="not mapped in fixture")}
            b = b"made-up listing record"
            pin = A.digest(b)
            (root/"evidence"/pin).write_bytes(b)
            u = dict(version=1,scope="reconstructed_verified_subset",
                rank_source_sha256=pins["ranks"],archive_manifests={k:pins[k] for k in
                    ("viewed_manifest","held_manifest")},contracts=[dict(
                    coin_id=1,symbol="FAKEUSDT",begin=self.t-1000,end=p["end"],
                    listed_known_at=(self.t-500)*C.H,closed_effective=None,closed_known_at=None,
                    listing_evidence_sha256=pin,delisting_notice=False)],us_rosters=included,
                rank_periods=periods,
                unmatched_judged_ids={str(i):"not in catalogue" for i in range(2,p["top_rank"]+1)})
            put("universe",u)
            def load(inv="0"*64):
                return A.load(paths,pins,root,p,evidence_dir=root/"evidence",inventory_pin=inv)
            with self.assertRaisesRegex(C.Incomplete,"structured source record"):
                load()
            def record(claim):
                b = json.dumps(dict(claim=claim,uri="https://example.org/invented-record",
                    support="Fabricated notice for this exact test contract",retrieved_at=self.t*C.H)).encode()
                sha = A.digest(b)
                (root/"evidence"/sha).write_bytes(b)
                evidence.add(sha)
                return sha
            template = u["contracts"][0]
            archives,contracts = {},[]
            for i in range(1,13):
                row = template|dict(coin_id=i,symbol=f"FAKE{i}USDT",listing_basis="dated_notice")
                identity = {k:row[k] for k in ("coin_id","symbol","begin","end","listed_known_at","listing_basis")}
                row["listing_evidence_sha256"] = record(identity|dict(kind="listing"))
                contracts.append(row)
                for kind,data in (("fundingRate",[[self.t*C.H,8,.001]]),
                                  ("klines",[[self.t*C.H,100,100,100,100,42]]),
                                  ("markPriceKlines",[[self.t*C.H,100,100,100,100]])):
                    k,v = archive_fixture(root,row["symbol"],kind,data)
                    archives[k] = v
            for venue in A.VENUES:
                claim = dict(kind="us_roster",venue=venue,product_id=venue,coin_id=1,
                             product_record_sha256=A.json_digest(sources[venue]["contracts"][0]))
                included[venue][venue] = dict(coin_id=1,evidence_sha256=record(claim))
            u["contracts"] = contracts
            u["unmatched_judged_ids"] = {str(i):dict(classification="outside_registered_scope",
                 reason=f"Invented asset {i} has no documented test listing instrument.",
                 searched=["https://example.org/invented-product-list"]) for i in range(13,p["top_rank"]+1)}
            for cid,row in u["unmatched_judged_ids"].items():
                row["evidence_sha256"] = record(dict(kind="scope_exclusion",coin_id=int(cid),
                    classification=row["classification"],reason=row["reason"]))
            u["rank_page_exclusions"] = {r["date"]:u["unmatched_judged_ids"] for r in raw}
            manifest = dict(errors={},archives=archives)
            put("viewed_manifest",manifest)
            u["archive_manifests"]["viewed_manifest"] = pins["viewed_manifest"]
            cs,syms,_ = A.catalogue(u)
            inv = A.json_digest(sorted(evidence))
            u["archive_period_inventory_sha256"] = A.json_digest(A.period_inventory(
                cs,syms,A.archive_inventory([manifest],set(syms.values()),p),p))
            put("universe",u)
            _,snaps,_,coverage = load(inv)
            self.assertEqual(len(snaps[0].ranks),C.P["top_rank"])
            self.assertEqual(coverage["top_ids_with_dated_mapping"],12)
            self.assertIsNone(coverage["full_market_dead_coin_retention"])
            # The January rank page is after a listed segment closed, not an
            # unknown identity and not a missing monthly archive.
            row = u["contracts"][11]
            row.update(end=self.t+24,closed_effective=self.t+24,closed_known_at=self.t*C.H)
            identity = {k:row[k] for k in ("coin_id","symbol","begin","end")}
            row["listing_evidence_sha256"] = record(identity|dict(kind="listing",
                listing_basis=row["listing_basis"],listed_known_at=row["listed_known_at"]))
            row["closure_evidence_sha256"] = record(identity|dict(kind="closure",closed_effective=self.t+24,
                closed_known_at=self.t*C.H,delisting_notice=False))
            cs,syms,_ = A.catalogue(u)
            u["archive_period_inventory_sha256"] = A.json_digest(A.period_inventory(
                cs,syms,A.archive_inventory([manifest],set(syms.values()),p),p))
            after = next(r["date"] for r in raw if r["known_at"]>=(self.t+24)*C.H)
            u["rank_page_exclusions"][after] = dict(u["unmatched_judged_ids"])|{"12":dict(
                classification="after_dated_closure",reason="The fabricated perpetual ended before this saved rank page.",
                searched=["https://example.org/invented-closure-notice"])}
            # verify_evidence binds only referenced records, not old superseded ones.
            inv = A.verify_evidence(u,sources,root/"evidence")
            put("universe",u)
            self.assertIn(12,load(inv)[3]["rank_page_mapping"][after]["unmapped"])
            u["rank_page_exclusions"][after]["12"]["classification"] = "before_dated_listing"
            put("universe",u)
            with self.assertRaisesRegex(C.Incomplete,"contradicts segment clocks"):
                load(inv)
            u["rank_page_exclusions"][after]["12"]["classification"] = "after_dated_closure"
            u["contracts"][0]["listing_evidence_sha256"] = u["contracts"][1]["listing_evidence_sha256"]
            put("universe",u)
            with self.assertRaisesRegex(C.Incomplete,"not bound to the exact listing"):
                load(inv)

    def test_listing_proxy_uses_earliest_pinned_positive_clock_plus_30_utc_days(self):
        from datetime import datetime, timezone
        utc = lambda y,m,d,h: int(datetime(y,m,d,h,tzinfo=timezone.utc).timestamp())
        name = "data/futures/um/monthly/klines/FAKEUSDT/1h/FAKEUSDT-1h-2022-01.zip"
        later = name.replace("2022-01","2022-02")
        invalid = name.replace("2022-01","2021-12")
        clock,proxy = utc(2022,1,7,22),utc(2022,2,6,0)
        mark = name.replace("/klines/","/markPriceKlines/")
        manifests = [dict(archives={later:dict(first=utc(2022,2,1,0),n=1),mark:dict(first=utc(2022,1,1,0),n=1)}),
                     dict(archives={invalid:dict(first=utc(2021,12,3,0),n=0),name:dict(first=clock,n=1)})]
        row = dict(symbol="FAKEUSDT",listing_basis="archive_first_plus_30_days",listed_known_at=proxy,
                   begin=proxy//C.H,archive_first_path=name,archive_first_seconds=clock)
        A.verify_listing_bases(dict(contracts=[row]),manifests,C.P)
        for bad in (dict(archive_first_path=later),dict(archive_first_seconds=clock+1),
                    dict(listed_known_at=proxy-1),dict(begin=proxy//C.H-1)):
            with self.assertRaisesRegex(C.Incomplete,"earliest pinned clock"):
                A.verify_listing_bases(dict(contracts=[row|bad]),manifests,C.P)
        with self.assertRaisesRegex(C.Incomplete,"supersedes the archive proxy"):
            A.verify_listing_bases(dict(contracts=[row|dict(dated_launch_notice="https://example.org/launch")]),
                                   manifests,C.P)
        with self.assertRaisesRegex(C.Incomplete,"invalid first trade clock"):
            A.first_archive_clocks([dict(archives={name:dict(first=utc(2022,2,1,0),n=1)})],{"FAKEUSDT"})

    def test_ftt_supplement_pins_months_and_fences_rows(self):
        t = self.t
        c = C.Contract(4195,0,"ftt",t+1,t+9,closed_effective=t+9,closed_known_at=t*C.H)
        syms = {"ftt":"FTTUSDT"}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {}
            for kind,inside,outside in (
                ("klines",[t*C.H+2*C.H,100,100,100,100,5],[t*C.H+9*C.H,0,0,0,0,0]),
                ("markPriceKlines",[t*C.H+2*C.H,100,100,100,100],[t*C.H+9*C.H,0,0,0,0]),
                ("fundingRate",[(t+8)*C.H,8,.001],[(t+16)*C.H,8,.999])):
                name,meta = archive_fixture(root,"FTTUSDT",kind,[inside,outside])
                files[name] = dict(where="plan18_ftt",sha256=meta["sha256"])
            u = dict(ftt_archive_supplement=dict(archives=files,evidence_sha256="f"*64))
            manifest = A.ftt_manifest(u,(c,),syms)
            p = C.P|dict(end=t+24)
            periods = A.period_inventory((c,),syms,A.archive_inventory([manifest],{"FTTUSDT"},p),p)
            self.assertEqual(set(periods[c.key]["2022-01"].values()),{"archive_file_listed_rows_unverified"})
            tape = A.Tape(root/"not-old-store",[manifest],syms,set(),p,contracts=(c,),supplemental_dir=root)
            self.assertEqual(tape.open_price(c.key,t+2),100.)
            self.assertIsNone(tape.open_price(c.key,t+9))
            self.assertEqual(tape.funding(c.key,t+8),(True,.001))
            self.assertEqual(tape.funding(c.key,t+16),(False,None))
            files.pop(next(iter(files)))
            with self.assertRaisesRegex(C.Incomplete,"each registered monthly ZIP"):
                A.ftt_manifest(u,(c,),syms)

    def test_terminal_checks_same_coin_successor_evidence(self):
        t = self.t
        tape = A.Tape.__new__(A.Tape)
        tape.lo,tape.hi,tape.symbols,tape.notices = t,t+2,{"old":"FAKEUSDT","new":"FAKE2USDT"},{"old"}
        c = C.Contract(1,1,"old",t-24,t+1,closed_effective=t+1,closed_known_at=t*C.H)
        new = C.Contract(1,1,"new",t+1,t+3)
        tape.segments = {"old":c,"new":new}
        tape.store = {"FAKEUSDT":(None,[100.,0.,0.]),"FAKE2USDT":(None,[0.,0.,100.])}
        tape.by_coin = {1:[c,new]}
        self.assertFalse(tape.terminal(c,t+1,t))
        tape.by_coin = {1:[c]}
        self.assertTrue(tape.terminal(c,t+1,t))
        self.assertFalse(tape.terminal(c,t,t))
        tape.store["FAKEUSDT"] = (None,[100.,float("nan"),float("nan")])
        self.assertFalse(tape.terminal(c,t+1,t))
        tape.store["FAKEUSDT"] = (None,[100.,100.,0.])
        self.assertFalse(tape.terminal(c,t+1,t))

    def test_verify_refuses_draft_missing_bad_seal_and_remote_mismatch(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"research_rig").mkdir()
            (root/"run").mkdir()
            with (patch.object(S,"ROOT",root),patch.object(S,"RUN",root/"run"),
                  patch.object(S,"git") as git,patch.object(S.os,"getenv",return_value=None)):
                (root/S.PLAN).write_text("Status FROZEN.\n")
                (root/S.DRAFT).write_text("draft")
                with self.assertRaisesRegex(C.Incomplete,"still a draft"):
                    S.verify("0"*64)
                (root/S.DRAFT).unlink()
                with self.assertRaisesRegex(C.Incomplete,"missing owner freeze seal"):
                    S.verify("0"*64)
                seal = json.dumps(dict(version=1,commit="1"*40)).encode()
                (root/"run/freeze_18.json").write_bytes(seal)
                with self.assertRaisesRegex(C.Incomplete,"input hash mismatch"):
                    S.verify("0"*64)
                git.assert_not_called()
                git.side_effect = [MagicMock(stdout=b"2"*40+b" refs/heads/main\n"),
                                   MagicMock(stdout=b"3"*40+b"\n")]
                with self.assertRaisesRegex(C.Incomplete,"current origin/main"):
                    S.verify(A.digest(seal))

    def test_attestation_requires_two_reviewers_bound_to_code_and_inputs(self):
        seal = dict(repo={k:"1"*64 for k in (*S.CODE,S.CONFIG)},inputs={"universe":"2"*64},
                    evidence_inventory_sha256="3"*64,frozen_at=200)
        rec = dict(version=1,approval="approved_for_freeze",universe_sha256="2"*64,
                   evidence_inventory_sha256="3"*64,reviewer="Fixture One",reviewed_at=100,
                   code={k:"1"*64 for k in S.CODE},config_sha256="1"*64,
                   remaining_limitations=["Archive revision history is unknown"])
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            def put(r):
                b = json.dumps(r).encode()
                sha = A.digest(b)
                (path/sha).write_bytes(b)
                return sha
            first = put(rec)
            second = put(rec|{"reviewer":"Fixture Two"})
            S.verify_review(seal|{"review_attestations":[first,second]},path)
            with self.assertRaisesRegex(C.Incomplete,"distinct reviewers"):
                S.verify_review(seal|{"review_attestations":[first,put(rec|{"reviewed_at":101})]},path)
            with self.assertRaisesRegex(C.Incomplete,"not bound"):
                S.verify_review(seal|{"review_attestations":[first,second],
                                     "evidence_inventory_sha256":"4"*64},path)

    def test_budget_refuses_before_allocation_and_random_keeps_only_gap_counts(self):
        count = C.END-C.START+81
        max_pairs = (A.MEMORY_CAP-A.WORK_RESERVE)//(count*37+4096)
        self.assertLessEqual(A.check_memory_budget(range(max_pairs),count),A.MEMORY_CAP)
        with self.assertRaisesRegex(C.Incomplete,"preflight budget"):
            A.check_memory_budget(range(max_pairs+1),count)
        f = Fake()
        for c in self.snap.contracts:
            f.trade_overrides[c.key,self.fill] = None
        ranked = C.run_book(f,self.snaps,self.t,self.end)
        self.assertEqual(ranked.qualified_slots,1)
        self.assertEqual(len(ranked.forced),6)
        p = C.P|{"random_draws":3}
        draws = C.random_books(f,self.snaps,self.t,self.end,p=p)
        self.assertTrue(all(not d.result.forced for d in draws))
        self.assertEqual(list(C.random_summary(draws,ranked,p)["forced_counts"].values()),[6]*3)

    def test_fifty_symbol_full_clock_tape_stays_within_virtual_budget(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            pairs = {f"key-{i}":f"FAKE{i}USDT" for i in range(50)}
            cs = tuple(C.Contract(i,i,key,self.t-400,C.END+1) for i,key in enumerate(pairs,1))
            rows = [[self.t*C.H,8,.001],[(self.t+8)*C.H,8,.002]]
            archives = dict(archive_fixture(root,pair,"fundingRate",rows) for pair in pairs.values())
            t = A.Tape(root,[dict(archives=archives,errors={})],pairs,set(),C.P,contracts=cs)
            self.assertEqual(len(t.store),50)
            self.assertEqual(t.funding("key-49",self.t+2),(True,None))
            with open("/proc/self/status",encoding="ascii") as f:
                vm = next(int(line.split()[1])*1024 for line in f if line.startswith("VmSize:"))
            self.assertLess(vm,t.budget_bytes)

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

    def funding_event(self,key,h):
        covered,rate = self.funding(key,h)
        return covered,rate,0.

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
