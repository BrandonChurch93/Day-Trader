"""Invented Plan 21 fixtures and planted-mean calibration; no real input paths."""
from collections import Counter
from copy import deepcopy
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
from random import Random
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

if __package__:
    from . import common_21 as C, score_21 as S
else:
    import common_21 as C
    import score_21 as S


def calendar():
    start = date(2024, 3, 1)
    return C.Calendar.from_rows([
        dict(date=day.isoformat(), open_utc=datetime.combine(day, time(9, 30), C.ET)
             .astimezone(C.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
        for i in range(125) if (day := start + timedelta(days=i)).weekday() < 5
        and day not in {date(2024, 3, 29), date(2024, 5, 27)}  # invented holiday calendar
    ])


def invented(**changes):
    return dict(accession="0000000001-24-000001", cik="1", ticker="ZTEST", identity="one",
                filing_date="2024-03-08", acceptance_utc="2024-03-08T20:55:00Z",
                known_terminal_by_cutoff=True, offer_type="fixed", floor="100",
                initial_expiry="2024-03-22", final_expiry="2024-03-22", priority="yes", form_wording=0,
                amendments=[], corporate_actions=[],
                result=dict(status="completed", accession="0000000001-24-000002",
                            acceptance_utc="2024-03-25T23:00:00Z", price="100",
                            payment_date=None, proration=None)) | changes


def bar(o):
    x = Decimal(str(o))
    return C.Bar(x, x + 1, x - 1, x, Decimal(100))


def packet(e, cal, p=C.POLICY):
    start, end = S.window(e, cal, p)
    def bars(base):
        return [dict(t=datetime.combine(d, time(), C.ET).isoformat(), o=base+i, h=base+i+1, l=base+i-1,
                     c=base+i, v=100+3*i) for i, d in enumerate(cal.between(start, end))]
    return dict(version=1, feed="sip", endpoint=S.ENDPOINT, through=p["bar_end"], adjustments=["raw", "all"],
                data={e.accession: dict(ticker=e.row["ticker"], identity=e.row["identity"],
                    start=start.isoformat(), end=end.isoformat(), entry_asof=e.entry.isoformat(),
                    filing_asof=e.row["filing_date"], raw=bars(60), **{"all": bars(66), "filing_all": bars(66)})})


class Test21(unittest.TestCase):
    def test_exact_30_and_dst(self):
        c = calendar()
        self.assertEqual(c.after_stamp("2024-03-08T14:00:00Z", 30), C.d("2024-03-08"))
        self.assertEqual(c.after_stamp("2024-03-08T14:00:01Z", 30), C.d("2024-03-11"))
        self.assertEqual(c.after_stamp("2024-03-11T13:00:00Z", 30), C.d("2024-03-11"))

    def test_ordinary_ex_date_uses_three_historical_regimes(self):
        ds = ["2017-08-30","2017-08-31","2017-09-01","2017-09-05",
              "2024-05-23","2024-05-24","2024-05-28"]
        c = C.Calendar.from_rows(dict(date=x,open_utc=x+"T13:30:00Z") for x in ds)
        self.assertEqual(C.ordinary_ex_date(c,"2017-09-01"),C.d("2017-08-30"))
        self.assertEqual(C.ordinary_ex_date(c,"2017-09-05"),C.d("2017-09-01"))
        self.assertEqual(C.ordinary_ex_date(c,"2024-05-24"),C.d("2024-05-23"))
        self.assertEqual(C.ordinary_ex_date(c,"2024-05-28"),C.d("2024-05-28"))

    def test_silence_and_discretion_exclusions_count_separately(self):
        rows = [dict(accession=f"0000000001-24-00000{i}", filing_reviewed=True,
                     eligibility="excluded", eligibility_reason="invented clause",
                     eligibility_source="https://www.sec.gov/Archives/example", eligibility_reason_code=code)
                for i,code in enumerate(("beneficial_priority_silent","odd_lot_priority_discretionary",
                                         "corporate_action_coverage_unverified","ordinary_dividend_dates_unresolved","other"),1)]
        m = dict(status="REVIEWED", version=1, audit_sha256="0"*64,
                 independent_sample_review="invented", events=rows, summary={})
        e, counts = S.reviewed_events(m,calendar(),C.POLICY)
        self.assertEqual(e,[])
        self.assertEqual(counts["beneficial_priority_silent_exclusions"],1)
        self.assertEqual(counts["odd_lot_priority_discretionary_exclusions"],1)
        self.assertEqual(counts["corporate_action_coverage_unverified_exclusions"],1)
        self.assertEqual(counts["ordinary_dividend_dates_unresolved_exclusions"],1)

    def test_raw_boundary_cost_and_fallback_payment(self):
        e = C.schedule(invented(), calendar())
        self.assertEqual(e.entry, C.d("2024-03-11"))
        self.assertEqual(e.terminal, C.d("2024-04-01"))
        t, reason = C.simulate(e, {e.entry: bar("98.50")})
        self.assertIsNone(reason)
        self.assertEqual(t["shares"], 5)
        self.assertAlmostEqual(t["net_return"], (500-5*98.50*1.001)/(5*98.50*1.001))
        self.assertEqual(C.simulate(e, {e.entry: bar("98.51")}), (None, "entry_discount"))
        t, _ = C.simulate(e, {e.entry: bar(5)})
        self.assertEqual(t["shares"], 99)
        t, _ = C.simulate(e, {e.entry: bar(50)}, 50)
        self.assertEqual(t["shares"], 9)  # 10 shares plus entry cost exceeds $500
        self.assertEqual(t["fee"], 50)
        self.assertAlmostEqual(t["annualized_linear"], t["net_return"]*365/t["days"])

    def test_election_deadline_uses_only_known_extensions(self):
        c = calendar()
        row = invented(acceptance_utc="2024-03-20T13:00:00Z")
        self.assertEqual(C.schedule(row,c).no_trade, "election_cutoff")
        row["amendments"] = [dict(accession="am", acceptance_utc="2024-03-20T13:00:01Z",new_expiry="2024-03-25")]
        self.assertEqual(C.schedule(row,c).no_trade, "election_cutoff")
        row["amendments"][0]["acceptance_utc"] = "2024-03-20T13:00:00Z"
        row["acceptance_utc"] = "2024-03-20T12:59:59Z"
        row["final_expiry"] = row["amendments"][0]["new_expiry"] = "2024-03-26"
        self.assertIsNone(C.schedule(row,c).no_trade)

    def test_auditor_pre_entry_floor_repros(self):
        c = calendar()
        for revised, opened, skip in [("98", "97.50", "entry_discount"), ("110", "105", None)]:
            with self.subTest(revised=revised):
                row = invented(amendments=[dict(accession="am", acceptance_utc="2024-03-11T12:30:00Z",
                                                new_floor=revised)])
                e = C.schedule(row, c)
                self.assertEqual(e.entry_floor, C.money(revised))
                self.assertEqual(C.simulate(e, {e.entry:bar(opened)})[1], skip)
        row = invented(amendments=[dict(accession="am", acceptance_utc="2024-03-11T13:00:01Z",new_floor="110")])
        e = C.schedule(row,c)
        self.assertEqual(e.entry_floor, Decimal(100))
        self.assertEqual(C.simulate(e,{e.entry:bar(105)})[1],"entry_discount")

    def test_t_plus_transition_and_minimum_per_share_cost(self):
        c = calendar()
        a = invented(acceptance_utc="2024-05-24T12:45:00Z", initial_expiry="2024-05-30", final_expiry="2024-05-30",
                     known_terminal_by_cutoff=False, result=None)
        self.assertEqual(C.schedule(a,c).no_trade, "election_cutoff")
        b = a | dict(acceptance_utc="2024-05-28T12:45:00Z", initial_expiry="2024-05-31", final_expiry="2024-05-31")
        self.assertIsNone(C.schedule(b,c).no_trade)
        self.assertEqual(C.market_cost(Decimal("4")), Decimal(".05"))
        self.assertEqual(C.market_cost(Decimal("60")), Decimal(".06"))
        b = C.schedule(b,c)
        trade, skip = C.simulate(b,{b.entry:bar(4),b.terminal:bar(3)})
        self.assertIsNone(skip)
        self.assertEqual(trade["investment"], 99 * 4.05)
        self.assertAlmostEqual(trade["cash_payout"], 99 * 2.95)

    def test_open_holdings_and_single_cash_path(self):
        c = calendar()
        a = C.schedule(invented(accession="A"), c)
        b = C.schedule(invented(accession="B",acceptance_utc="2024-03-11T15:00:00Z"),c)
        later = invented(accession="C",acceptance_utc="2024-04-01T15:00:00Z",
                         initial_expiry="2024-04-19",final_expiry="2024-04-19")
        later["result"].update(acceptance_utc="2024-04-22T12:00:00Z")
        later = C.schedule(later,c)
        a.row["result"]["price"]="80"
        tapes = {a.accession:{a.entry:bar(95)},b.accession:{b.entry:bar(95)},later.accession:{later.entry:bar(90)}}
        r = C.report([later,b,a],tapes,{})
        self.assertEqual(r["peak_holdings_open_shown_only"],2)
        single = r["single_500_account_shown_only"]
        self.assertEqual([(t["accession"], t["shares"]) for t in single["trades"]],[("A",5),("C",4)])
        self.assertEqual(single["no_trade"],{"cash_tied_up":1})

    def test_distribution_counts_on_ex_date_but_cannot_finance_entry_before_payment(self):
        c = calendar()
        first = invented(accession="A", corporate_actions=[
            dict(kind="cash_distribution",date="2024-03-13",payment_date="2024-04-08",cash_per_share="20")])
        first["result"]["price"] = "80"
        a = C.schedule(first,c)
        next_row = invented(accession="B",acceptance_utc="2024-04-01T15:00:00Z",
                            initial_expiry="2024-04-19",final_expiry="2024-04-19")
        next_row["result"]["acceptance_utc"] = "2024-04-22T12:00:00Z"
        b = C.schedule(next_row,c)
        tapes = {"A":{a.entry:bar(95)},"B":{b.entry:bar(90)}}
        result = C.single_account([b,a], tapes)
        self.assertEqual([t["shares"] for t in result["trades"]], [5,4])
        self.assertEqual(result["trades"][0]["distribution_credits"], {"2024-04-08":"100"})
        self.assertGreater(result["trades"][0]["net_return"],0)
        self.assertAlmostEqual(result["final_cash"],500 - 475.475 + 400 + 100 - 360.36 + 400)

    def test_form_wording_rows_stay_judged_and_drop_only_in_sensitivity(self):
        c = calendar()
        a = C.schedule(invented(accession="A",form_wording=1),c)
        b = C.schedule(invented(accession="B",form_wording=0),c)
        tapes = {"A":{a.entry:bar(95)},"B":{b.entry:bar(95)}}
        report = C.report([a,b],tapes,{})
        self.assertEqual(report["form_wording_flagged_filings"],1)
        self.assertEqual([t["accession"] for t in report["arms"]["judged"]["trades"]],["A","B"])
        sensitivity = report["arms"]["without_form_wording_shown_only"]
        self.assertEqual([t["accession"] for t in sensitivity["trades"]],["B"])
        self.assertNotIn("judgment",sensitivity)

    def test_issuer_dividend_release_flag_requires_pins_and_drops_only_in_sensitivity(self):
        c = calendar()
        a = C.schedule(invented(accession="A",div_source_ir=1),c)
        b = C.schedule(invented(accession="B",div_source_ir=0),c)
        tapes = {"A":{a.entry:bar(95)},"B":{b.entry:bar(95)}}
        report = C.report([a,b],tapes,{})
        self.assertEqual(report["div_source_ir_flagged_filings"],1)
        self.assertEqual([t["accession"] for t in report["arms"]["judged"]["trades"]],["A","B"])
        filtered = report["arms"]["without_div_source_ir_shown_only"]
        self.assertEqual([t["accession"] for t in filtered["trades"]],["B"])
        self.assertNotIn("judgment",filtered)
        with self.assertRaises(C.Incomplete):
            S.press_release_dividend_dates(a.row)
        pin = dict(url="https://issuer.example/dividend-announcement",
                   amount_source_url="https://www.sec.gov/Archives/edgar/data/example",
                   fetched_at_utc="2024-03-30T15:30:00Z",sha256="f"*64,
                   record_date="2024-03-20",payment_date="2024-04-01")
        self.assertEqual(len(S.press_release_dividend_dates(dict(a.row,div_source_ir_evidence=[pin]))),1)

    def test_withdrawal_and_cut_and_unknown(self):
        c = calendar()
        r = invented()
        r["result"].update(status="withdrawn", acceptance_utc="2024-03-19T13:00:01Z")
        e = C.schedule(r, c)
        self.assertEqual(e.required, {e.entry, C.d("2024-03-20")})
        t, _ = C.simulate(e, {e.entry:bar(95), e.terminal:bar(92)}, 50)
        self.assertEqual((t["outcome"], t["fee"]), ("withdrawn",0))
        r = invented(amendments=[dict(accession="AM", acceptance_utc="2024-03-14T13:00:00Z", new_floor="90")])
        e = C.schedule(r,c)
        t, _ = C.simulate(e,{e.entry:bar(95), C.d("2024-03-14"):bar(91)},50)
        self.assertEqual((t["outcome"],t["exit_accession"],t["fee"]), ("price_cut","AM",0))
        t, _ = C.simulate(e,{e.entry:bar(89), C.d("2024-03-14"):bar(91)},50)
        self.assertEqual((t["outcome"], t["fee"]), ("completed",50))
        fallback = C.schedule(invented(result=None,known_terminal_by_cutoff=False),c)
        out = C.report([fallback], {fallback.accession:{fallback.entry:bar(90),fallback.terminal:bar(88)}}, {})
        self.assertEqual(out["arms"]["judged"]["judgment"]["n"],0)
        self.assertEqual(len(out["arms"]["unresolved_fallback_shown_only"]["trades"]),1)

    def test_no_priority_remainder_and_stated_payment(self):
        r = invented(priority="no")
        r["result"].update(proration=".4",payment_date="2024-03-26")
        e = C.schedule(r, calendar())
        self.assertEqual(e.terminal, C.d("2024-03-26"))
        t, _ = C.simulate(e,{e.entry:bar(95),e.terminal:bar(93)})
        self.assertEqual(t["shares"],5)
        self.assertAlmostEqual(t["net_return"],(200+3*93*.999-5*95*1.001)/(5*95*1.001))

    def test_split_and_cash_when_supported(self):
        r = invented(corporate_actions=[dict(date="2024-03-12",kind="split",ratio="2"),
                                       dict(date="2024-03-13",payment_date="2024-03-18",
                                            kind="cash_distribution",cash_per_share="1")])
        r["result"]["price"]="50"
        e = C.schedule(r,calendar())
        t, _ = C.simulate(e,{e.entry:bar(95)})
        self.assertAlmostEqual(t["net_return"],(500+10-5*95*1.001)/(5*95*1.001))

    def test_validate_uses_paired_raw_and_adjusted(self):
        c = calendar()
        e = C.schedule(invented(), c)
        b = packet(e,c)
        self.assertEqual(S.validate_bundle(b,[e],c,C.POLICY)[e.accession][e.entry].o, Decimal(65))
        z = deepcopy(b)
        z["data"][e.accession]["raw"].pop(5)
        with self.assertRaises(C.Incomplete):
            S.validate_bundle(z,[e],c,C.POLICY)
        z = deepcopy(b)
        for r in z["data"][e.accession]["all"][1:6]:
            r.update(o=99,h=99,l=99,c=99)
        with self.assertRaises(C.Incomplete):
            S.validate_bundle(z,[e],c,C.POLICY)
        z = deepcopy(b)
        z["data"][e.accession]["filing_all"][4]["v"] *= 4
        with self.assertRaises(C.Incomplete):
            S.validate_bundle(z,[e],c,C.POLICY)

    def test_count_once_cross_identity(self):
        c = calendar()
        e1 = C.schedule(invented(), c)
        e2 = C.schedule(invented(accession="0000000002-24-000001",identity="two",ticker="ZZTEST"),c)
        b = packet(e1,c)
        b["data"].update(packet(e2,c)["data"])
        with self.assertRaises(C.Incomplete):
            S.validate_bundle(b,[e1,e2],c,C.POLICY)

    def test_no_lock_on_preflight_and_one_shot(self):
        with TemporaryDirectory() as temp:
            lock, result = (Path(temp)/s for s in ("lock","result"))
            def fail():
                raise C.Incomplete("incomplete invented tape")
            with self.assertRaises(C.Incomplete):
                S.claim(lock,result,{},fail,lambda x:x)
            self.assertFalse(lock.exists() or result.exists())
            def calc(x):
                self.assertTrue(lock.exists())
                return x
            S.claim(lock,result,{"ledger":158},lambda:{"fixture":1},calc)
            self.assertTrue(Path(result).exists())
            with self.assertRaises(S.Refused):
                S.claim(lock,result,{},fail,calc)

    def test_draft_refused_before_price_reader(self):
        with patch.object(S, "fetch", side_effect=AssertionError("draft network ever attempted")):
            with self.assertRaises(S.Refused):
                S.run("f"*40, "f"*64, acquire_bars=True)
        with self.assertRaises(C.Incomplete):
            S.reviewed_events({"status":"DRAFT_NOT_REVIEWED"},calendar(),C.POLICY)

    def test_approval_only_file_and_frozen_input_pins(self):
        freeze, approval = "a" * 40, "b" * 40
        inp = ["1" * 64, "2" * 64, "3" * 64]
        plan = ("Status FROZEN.\n" + "".join(f"{k}: {v}\n" for k,v in zip(
            ("EVENT_MANIFEST_SHA256","CALENDAR_SHA256","REQUEST_SCOPE_SHA256"),inp))).encode()
        blobs = {k:b"invented" for k in S.PINNED}
        blobs[S.PLAN] = plan
        blobs[S.CONFIG] = json.dumps({"replay_21_plan":{"value":C.POLICY}}).encode()
        package = json.dumps({k:S.digest(v) for k,v in blobs.items()}).encode()
        blobs[S.PIN_FILE] = package
        freeze_pin = S.digest(package)
        line = (f"Approved by the lead: plan 21, one custodian acquisition, validation and one scored run, "
                f"freeze commit {freeze}, freeze SHA-256 {freeze_pin}, event manifest SHA-256 {inp[0]}, "
                f"calendar SHA-256 {inp[1]}, request scope SHA-256 {inp[2]}.\n").encode()
        blobs[S.APPROVAL] = line
        blobs[S.LEDGER] = f"| 158 | `{S.PLAN}` |\n".encode()
        blobs[S.QUEUE] = f"| 38 | `{S.PLAN}` |\n".encode()
        delta = [f"A\t{S.APPROVAL}\n".encode()]
        def mock_git(*args):
            if args[0] == "show": return blobs[args[1].split(":",1)[1]]
            if args[0] == "status": return b""
            if args[0] == "rev-parse": return approval.encode()
            if args[0] == "rev-list": return f"{approval} {freeze}\n".encode()
            if args[0] == "merge-base": return b""
            if args[0] == "diff-tree": return delta[0]
            raise AssertionError(args)
        def mock_read(path, pin):
            b = blobs[str(path.relative_to(S.ROOT))]
            self.assertEqual(pin,S.digest(b))
            return b
        with TemporaryDirectory() as temp, patch.object(S,"git", side_effect=mock_git), patch.object(
                S,"safe_read", side_effect=mock_read), patch.object(S,"RUN",Path(temp)):
            p, pins, _, approved_freeze = S.authorize(approval,freeze_pin)
            self.assertEqual((p,pins[S.SCOPE],approved_freeze),(C.POLICY,inp[2],freeze))
            blobs[S.APPROVAL] = line.replace(b"\n",b"\r\n")
            with self.assertRaises(S.Refused):
                S.authorize(approval,freeze_pin)
            blobs[S.APPROVAL] = line
            delta[0] += b"M\tdocs/INDEX.md\n"
            with self.assertRaises(S.Refused):
                S.authorize(approval,freeze_pin)
            delta[0] = f"A\t{S.APPROVAL}\n".encode()
            blobs[S.APPROVAL] = line.replace(inp[2].encode(), ("4"*64).encode())
            with self.assertRaises(S.Refused):
                S.authorize(approval,freeze_pin)

    def test_price_blind_request_scope(self):
        c = calendar()
        e = C.schedule(invented(), c)
        r = S.request_scope([e],c,C.POLICY)
        start,end = S.window(e,c,C.POLICY)
        self.assertEqual(r["cases"], {e.accession: dict(ticker="ZTEST",
            start=start.isoformat(),end=end.isoformat(),filing_asof="2024-03-08",entry_asof="2024-03-11")})
        self.assertEqual(r["fields"],list("tohlcv"))

    def exercise_transport(self, outcomes, expected, refusal=False):
        d = C.d("2024-03-11")
        transport = dict(requests=0,retries=0)
        with patch.object(S.subprocess,"run",side_effect=outcomes) as run, patch.object(S,"sleep") as sleep:
            def fetch():
                return S.fetch("invented-handle","ZTEST",d,d,d,"raw",transport)
            if refusal:
                with self.assertRaisesRegex(C.Incomplete,"acquisition transport refused"):
                    fetch()
            else:
                self.assertEqual(fetch(),[])
            self.assertEqual(transport,dict(requests=len(outcomes),retries=len(outcomes)-1))
            urls = [call.args[0][-1] for call in run.call_args_list]
            self.assertEqual(urls,[urls[0]]*len(outcomes))
            self.assertIn("symbols=ZTEST",urls[0])
            self.assertIn("adjustment=raw",urls[0])
            self.assertEqual([call.args[0] for call in sleep.call_args_list],expected)

    def test_fetch_retries_rate_limit_then_success(self):
        limited = subprocess.CompletedProcess([],0,b"not-json\n429")
        okay = subprocess.CompletedProcess([],0,b'{"bars":{}}\n200')
        self.exercise_transport([limited,okay],[5,0.5])

    def test_fetch_repeated_rate_limit_refuses_at_fifth_attempt(self):
        limited = subprocess.CompletedProcess([],0,b"not-json\n429")
        self.exercise_transport([limited]*5,[5,0.5,10,0.5,20,0.5,40,0.5],refusal=True)

    def test_fetch_non_rate_limit_status_refuses_without_retry(self):
        for status in (b"401",b"403",b"404",b"500"):
            with self.subTest(status=status):
                denied = subprocess.CompletedProcess([],0,b"not-json\n"+status)
                self.exercise_transport([denied],[],refusal=True)

    def test_fetch_retries_timeouts_only(self):
        curl_timeout = subprocess.CompletedProcess([],28,b"partial\n200")
        wrapper_timeout = subprocess.TimeoutExpired("invented command",135,output=b"partial")
        okay = subprocess.CompletedProcess([],0,b'{"bars":{}}\n200')
        self.exercise_transport([curl_timeout,wrapper_timeout,okay],[5,0.5,10,0.5])
        self.exercise_transport([subprocess.CompletedProcess([],28,b"partial\n503")],[],refusal=True)

    def test_acquire_paces_across_series_and_records_transport_totals(self):
        c = calendar()
        e = C.schedule(invented(),c)
        limited = subprocess.CompletedProcess([],0,b"not-json\n429")
        okay = subprocess.CompletedProcess([],0,b'{"bars":{}}\n200')
        with patch.object(S.subprocess,"run",side_effect=[okay,limited,okay,okay]) as run, (
                patch.object(S,"sleep")) as sleep:
            bundle = S.acquire([e],c,C.POLICY,"custom-cred:invented@data.alpaca.markets")
        self.assertEqual(bundle["transport"],dict(requests=4,retries=1))
        urls = [call.args[0][-1] for call in run.call_args_list]
        self.assertEqual(urls[1],urls[2])
        self.assertNotEqual(urls[0],urls[1])
        self.assertNotEqual(urls[1],urls[3])
        self.assertEqual([call.args[0] for call in sleep.call_args_list],[0.5,5,0.5,0.5])

    def test_separate_exclusive_custody_and_no_return_validation(self):
        c = calendar()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            bars, custody, lock, result, scope = (root/k for k in ("bars","custody","lock","result","scope"))
            pins = {S.SESSIONS: "1"*64, S.EVENTS: "2"*64, scope: "3"*64}
            with (
                    patch.multiple(S,RUN=root,BARS=bars,SCOPE=scope,ACQUIRE_LOCK=custody,LOCK=lock,RESULT=result),
                    patch.dict(os.environ,PLAN21_ALPACA_HANDLE="custom-cred:invented@data.alpaca.markets"),
                    patch.object(S,"authorize",return_value=(C.POLICY,pins,{},"a"*40)),
                    patch.object(C.Calendar,"from_rows",return_value=type("Cal",(),{
                        "days":[C.d("2015-12-15"),C.d("2026-12-15")]})()),
                    patch.object(S,"reviewed_events",return_value=([],{})),
                    patch.object(S,"request_scope",return_value={}),
                    patch.object(S,"acquire",return_value={"invented":True}) as acquire,
                    patch.object(S,"validate_bundle",return_value={}) as validate,
                    patch.object(C,"report",side_effect=AssertionError("validation computed a return")),
                    patch("builtins.print"),
            ):
                read = S.safe_read
                def mock_read(path,pin=None):
                    return b"{}" if path in {S.SESSIONS,S.EVENTS,scope} else read(path,pin)
                with patch.object(S,"safe_read",side_effect=mock_read):
                    S.run("b"*40,"4"*64,acquire_bars=True)
                    self.assertTrue(custody.exists())
                    self.assertEqual(custody.stat().st_mode & 0o777,0o600)
                    with self.assertRaises(S.Refused):
                        S.run("b"*40,"4"*64,acquire_bars=True)
                    acquire.assert_called_once()
                    S.run("b"*40,"4"*64,S.digest(read(bars)),validate_only=True)
                    validate.assert_called_once()
                    self.assertFalse(lock.exists() or result.exists())

    def test_reviewed_manifest_accepts_later_issuer_price_without_using_its_clock(self):
        url = "https://www.sec.gov/Archives/mock"
        r = invented(filing_reviewed=True, eligibility="eligible", amendment_review_complete=True,
                     listing_url=url,listing_quote="Listed Class A", original_url=url,
                     odd_lot_quote="Odd-lot priority sentence",clause_url=url,
                     actions_reviewed_through="2024-04-30",actions_source=url,
                     final_expiry_accession="0000000001-24-000001")
        r["result"].update(filing_date="2024-03-25",url=url,price_quote="Paid $100 per share",
                           price_source_accession="0000000001-24-000010",price_source_url=url,
                           payment_review_complete=True,price_source_kind="final price from later issuer filing")
        r["amendments"] = [dict(accession=r["result"]["accession"],
                                acceptance_utc=r["result"]["acceptance_utc"],url=url,reviewed=True)]
        manifest = dict(status="REVIEWED",version=1,audit_sha256="f"*64,independent_sample_review="fixture",
                        events=[r],summary={})
        events, meta = S.reviewed_events(manifest,calendar(),C.POLICY)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0].terminal,C.d("2024-04-01"))
        self.assertEqual(meta["final_price_from_later_issuer_filing"],1)
        self.assertEqual(meta["own_date_wording_flagged_events"],0)
        r["own_date_wording"] = 1
        self.assertEqual(S.reviewed_events(manifest,calendar(),C.POLICY)[1]["own_date_wording_flagged_events"],1)
        r["own_date_wording"] = True
        with self.assertRaisesRegex(C.Incomplete,"own-date wording"):
            S.reviewed_events(manifest,calendar(),C.POLICY)

    def test_action_horizon_includes_prorated_remainder(self):
        r = invented(priority="no")
        r["result"].update(proration=".4",payment_date="2024-03-25",acceptance_utc="2024-04-05T23:00:00Z")
        e = C.schedule(r,calendar())
        self.assertEqual(e.actions_through,C.d("2024-04-08"))

    def test_all_marks_and_degenerate_variance(self):
        balanced = [(2019+i//6,.04 + (i%6-2)*.007) for i in range(36)]
        self.assertTrue(C.judgment(balanced)["passes"])
        self.assertFalse(C.judgment([(2020,.1)]*40)["marks"]["t_at_least_2"])
        out = C.judgment([(2020,-.001)]*33 + [(2020,.2)]*3)
        self.assertFalse(out["marks"]["positive_without_best_three"])
        self.assertFalse(out["marks"]["positive_median"])


def calibrate(p):
    """Stylized after-cost independent trade noise plus common yearly shocks.

    Same random draws for each plant; the intercept is the population mean,
    not a forced sample mean. No historical stock or offer outcome inputs.
    """
    counts = Counter()
    years = 6
    for i in range(p["calibration_seeds"]):
        rng = Random(p["calibration_seed"] + i)
        base = []
        for y in range(2020,2020+years):
            drift = rng.gauss(0,p["calibration_year_sigma"])
            for _ in range(p["calibration_trades"]//years):
                shock = rng.gauss(0,p["calibration_trade_sigma"])
                if rng.random() < p["calibration_tail_chance"]:
                    shock *= p["calibration_tail_scale"]
                base.append((y,drift+shock))
        for edge in p["calibration_edges_pct"]:
            counts[edge] += C.judgment([(y, x+edge/100) for y,x in base],p)["passes"]
    for edge in p["calibration_edges_pct"]:
        print(f"synthetic net plant {edge}%: {counts[edge]}/{p['calibration_seeds']} pass all six marks")
    return counts


if __name__ == "__main__":
    unittest.main()
