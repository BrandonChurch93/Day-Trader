"""Offline E03 checks with invented offers and fabricated SEC/index responses."""
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from practice import forward_e03 as e

OFFER = "0000000111-26-000001"
AMEND = "0000000111-26-000002"
FINAL = "0000000111-26-000003"
NOW = e.plan.stamp("2026-11-27T15:00:00Z")


def url(acc):
    return f"{e.SEC}/Archives/edgar/data/111/{acc.replace('-', '')}/test.htm"


def offer(**overrides):
    return {"cik": "111", "issuer": "Synthetic issuer", "symbol": "FAKE", "filing_date": "2026-11-25",
            "acceptance_utc": "2026-11-25T21:56:00Z", "offer_type": "fixed", "floor": "10",
            "initial_expiry": "2026-12-10", "quote": "We buy all qualifying beneficial odd lots before proration.",
            "url": url(OFFER), "review": "eligible", "review_url": url(OFFER)} | overrides


def bar(session, price, **overrides):
    return {"symbol": "FAKE", "feed": "sip", "adjustment": "raw", "open": price, "volume": "10000",
            "session": session, "source": "https://data.alpaca.markets/v2/stocks/bars"} | overrides


def entry(price="9.85", **overrides):
    return {"bar": bar("2026-11-27", price), "filings_checked_through": "2026-11-27T14:50:00Z",
            "tape_review": "Synthetic tape identity, as-of mapping and stale-bar review."} | overrides


class Watch(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log, self.off = (Path(self.tmp.name) / k for k in ("tracked/log.json", "private"))

    def record(self, mode, packet, filing=OFFER, now=NOW):
        return e.record(mode, OFFER, filing, packet, now, self.log, self.off)

    def confirm(self, **overrides):
        return self.record("confirm", offer(**overrides), now=e.plan.stamp("2026-11-25T22:00:00Z"))

    def test_index_with_live_dedup_and_exact_forms(self):
        index = f"""Description: Master Index
CIK|Company Name|Form Type|Date Filed|Filename
--------------
111|Synthetic issuer|SC TO-I|2026-11-25|edgar/data/111/{OFFER}.txt
111|Synthetic issuer|SC TO-I/A|2026-11-26|edgar/data/111/{AMEND}.txt
111|Ignore options other form|SC TO-T|2026-11-26|edgar/data/111/{FINAL}.txt
""".encode()
        link = url(OFFER).replace("test.htm", OFFER + "-index.htm")
        live = f"""<feed xmlns="http://www.w3.org/2005/Atom"><updated>2026-11-26T00:00:00-05:00</updated>
<entry><title>SC TO-I - Synthetic issuer (0000000111) (Subject)</title><link rel="alternate" href="{link}"/>
<summary>&lt;b&gt;Filed:&lt;/b&gt; 2026-11-25</summary><updated>2026-11-25T16:56:00-05:00</updated>
<category term="SC TO-I"/></entry></feed>""".encode()
        r = e.scan(date(2026, 11, 25), date(2026, 11, 26), lambda path: live if path == e.ATOM else index)
        self.assertEqual([(x[0], x[5]) for x in r], [(OFFER, "2026-11-25T21:56:00Z"), (AMEND, None)])

    def test_holiday_equality_friction_and_no_price_in_log(self):
        self.confirm()
        r = self.record("entry", entry())
        self.assertEqual(r["summary"], dict(entry_session="2026-11-27", same_day=True, issuer="Synthetic issuer",
                                            symbol="FAKE", action="pretend_entry", reason=None, shares=50, discount_bps=150))
        self.assertIn("150.00 bps | 50 shares | pretend money only", e.alert(OFFER, r["summary"]))
        self.assertNotIn('"open"', self.log.read_text())
        self.assertNotIn('"floor"', self.log.read_text())
        self.assertEqual(e.verify(self.log, self.off)["records"][1]["previous_sha256"],
                         e.verify(self.log, self.off)["records"][0]["sha256"])
        with self.assertRaisesRegex(ValueError, "already recorded"):
            self.record("entry", entry())

    def test_election_deadline_and_inclusive_amendment_clock(self):
        self.confirm(initial_expiry="2026-12-01")
        am = {"acceptance_utc": "2026-11-27T14:00:00Z", "url": url(AMEND), "new_expiry": "2026-12-02", "new_floor": "20"}
        self.record("amend", am, AMEND)
        r = self.record("entry", entry("19.70"))
        self.assertEqual((r["summary"]["action"], r["summary"]["shares"]), ("pretend_entry", 25))

    def test_too_late_amendment_does_not_rescue_entry(self):
        self.confirm(initial_expiry="2026-12-01")
        self.record("amend", {"acceptance_utc": "2026-11-27T14:00:01Z", "url": url(AMEND),
                              "new_expiry": "2026-12-02"}, AMEND)
        p = entry()
        del p["bar"]
        self.assertEqual(self.record("entry", p)["summary"]["reason"], "election_cutoff")

    def test_terminal_known_before_open(self):
        self.confirm()
        self.record("amend", {"acceptance_utc": "2026-11-27T14:00:00Z", "url": url(AMEND),
                              "terminal_notice": "withdrawn"}, AMEND)
        p = entry()
        del p["bar"]
        self.assertEqual(self.record("entry", p)["summary"]["reason"], "outcome_already_known")

    def test_below_threshold_and_missing_volume(self):
        self.confirm()
        with self.assertRaises(ValueError):
            self.record("entry", entry(bar=bar("2026-11-27", "9.80", volume=0)))
        r = self.record("entry", entry("9.8501"))["summary"]
        self.assertEqual(r["reason"], "entry_discount")
        self.assertIsNone(e.alert(OFFER, r))

    def test_discount_alert_without_affordable_share(self):
        self.confirm(floor="600")
        r = self.record("entry", entry("550"))["summary"]
        self.assertEqual(r["reason"], "zero_affordable_shares")
        self.assertIn("no affordable whole share", e.alert(OFFER, r))

    def test_late_entry_and_provenance(self):
        self.confirm()
        r = self.record("entry", entry(), now=e.plan.stamp("2026-11-30T15:00:00Z"))
        self.assertFalse(r["summary"]["same_day"])
        self.assertIsNone(e.alert(OFFER, r["summary"]))
        raw = self.off / (r["sha256"] + ".json")
        raw.write_text('{"changed":true}')
        with self.assertRaisesRegex(ValueError, "payload hash"):
            e.verify(self.log, self.off)

    def test_completed_net_and_default_pay_date(self):
        self.confirm()
        self.record("entry", entry())
        p = {"accession": FINAL, "acceptance_utc": "2026-12-11T20:00:00Z", "url": url(FINAL), "status": "completed",
             "final_expiry": "2026-12-10", "price": "10.20", "corporate_actions": [], "coverage_through": "2026-12-17",
             "coverage_note": "Synthetic corporate-action review through assumed payment.", "exit_bars": []}
        r = self.record("outcome", p, FINAL, e.plan.stamp("2026-12-11T20:30:00Z"))["summary"]
        self.assertEqual((r["exit_session"], r["outcome"], r["net_return_pct"]), ("2026-12-17", "completed", 3.0303))
        public = json.loads(self.log.read_text())
        self.assertNotIn("price", public["records"][-1]["summary"])

    def test_price_cut_and_distribution_use_plan_exit(self):
        self.confirm()
        self.record("entry", entry())
        self.record("amend", {"acceptance_utc": "2026-12-01T15:00:00Z", "url": url(AMEND), "new_floor": "9"},
                    AMEND, e.plan.stamp("2026-12-01T16:00:00Z"))
        p = {"accession": FINAL, "acceptance_utc": "2026-12-11T20:00:00Z", "url": url(FINAL), "status": "completed",
             "final_expiry": "2026-12-10", "price": "9.10", "coverage_through": "2026-12-17",
             "corporate_actions": [{"kind": "cash_distribution", "date": "2026-12-01", "payment_date": "2026-12-10",
                                    "url": url(AMEND), "cash_per_share": "0.10"}],
             "coverage_note": "Synthetic corporate-action review through assumed payment.",
             "exit_bars": [bar("2026-12-02", "9.50")]}
        r = self.record("outcome", p, FINAL, e.plan.stamp("2026-12-11T20:30:00Z"))["summary"]
        self.assertEqual((r["exit_session"], r["outcome"], r["net_return_pct"]), ("2026-12-02", "price_cut", -3.5354))

    def test_public_tamper_refuses_even_for_next_record(self):
        self.confirm()
        public = json.loads(self.log.read_text())
        public["records"][0]["summary"]["issuer"] = "changed"
        self.log.write_bytes(e.enc(public))
        with self.assertRaisesRegex(ValueError, "chain mismatch"):
            self.record("entry", entry())


if __name__ == "__main__":
    unittest.main()
