"""Synthetic-only test suite: no private packet or filesystem price access."""
from base64 import b64encode
from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from fractions import Fraction as F
from hashlib import sha256
from gzip import compress
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from count_63 import CUTOFF, HOLDS, NY, SABA, measure as counts, schedule, self_check
from placebo_63 import Leg, admissible, leg_return, measure
from placebo_native_63 import approved_bar_leaves
from placebo_project_63 import project
from placebo_run_63 import Proofs, approved_scope, decode, exclusive, read_projection
from power_63 import power
from score_63 import (
    BLIND_FLAGS, BlindFacts, Facts, Stop, filer_days, fund_rates, load_blind_facts,
    marks, measure_half, print_price_free_validation, validate_inputs,
)


class Plan63(unittest.TestCase):
    def test_calendar_and_overlap(self):
        self_check(schedule())

    def test_duration_median_and_floor(self):
        m = 60_000_000_000
        quotes = [(-6*m, F(99), F(101)), (-5*m, F(99), F(101)),
                  (-4*m, F(999), F(1001)), (-3*m, F(999), F(1001)),
                  (-2*m, F(999), F(1001))]
        self.assertEqual(measure_half(quotes), F(1, 1000))
        self.assertIsNone(measure_half(quotes[:2]))
        self.assertEqual(fund_rates(F(1, 10000), None), (F(15, 10000), F(55, 10000)))
        self.assertEqual(fund_rates(None, F(1, 10000)), (F(55, 10000), F(55, 10000)))
        with self.assertRaises(Stop):
            measure_half(quotes + [quotes[-1]])

    def test_validation_without_exit_price(self):
        ok = Facts(date(2024, 5, 1), SABA, True, True, True, True,
                   "printed_positive_volume", True, True, True, F(100), F(20), None)
        no_lot = replace(ok, fund_entry_close=F(499))
        self.assertEqual(validate_inputs([ok, ok, no_lot]), {
            "placed_filer_days": 1, "meets_floor": False,
            "gate_counts_fund_days": {"fund_no_whole_share": 1, "placed": 2}})
        for bad in (replace(ok, action_sources_agree=False), replace(ok, exit_state="successor")):
            with self.assertRaises(Stop):
                validate_inputs([bad])
        blind = BlindFacts(ok.day, ok.filer, *([True] * 9))
        aggregate = StringIO()
        print_price_free_validation([blind, blind], aggregate)
        self.assertEqual(json.loads(aggregate.getvalue())["placed_filer_days_upper_bound"], 1)
        with self.assertRaises(Stop):
            print_price_free_validation([ok], StringIO())
        planned = {"fictitious accession": (ok.day, ok.filer)}
        clean = {"accession": "fictitious accession", **dict.fromkeys(BLIND_FLAGS, True)}
        manifest = {"schema": "plan63-price-free-target-gates-v1", "gates": [clean]}
        self.assertEqual(load_blind_facts(manifest, planned), [blind])
        with self.assertRaises(Stop):
            load_blind_facts({**manifest, "gates": [{**clean, "fund_entry_close": 20}]}, planned)

    def test_leg_cash_and_split(self):
        a, b = date(2024, 1, 5), date(2024, 1, 12)
        leg = Leg("fund", a, b, F(100), F(49), True, True, ((b, "split", F(2)), (b, "cash_usd", F(2))))
        self.assertEqual(leg_return(leg, "fund", a, b), F(2, 100))
        with self.assertRaises(Stop):
            leg_return(leg, "fund", a, b + timedelta(days=1))
        with self.assertRaises(Stop):
            leg_return(leg, "different fund", a, b)
        for actions in (leg.actions + (leg.actions[-1],), tuple(reversed(leg.actions))):
            with self.assertRaises(Stop):
                leg_return(replace(leg, actions=actions), "fund", a, b)

    def test_cluster_marks(self):
        rows = filer_days([(date(2020, 1, 1), SABA, F(200)), (date(2020, 1, 1), SABA, F(100)),
                          (date(2020, 1, 1), "non-Saba", F(-50)), (date(2020, 1, 2), "non-Saba", F(40))])
        m = marks(rows, SABA, 600)
        self.assertEqual(m["placed_filer_days"], 3)
        self.assertEqual(m["raw_mean_bps"], F(140, 3))
        self.assertFalse(m["marks"]["filer_breadth"])
        self.assertFalse(m["marks"]["placement"])

    def test_placebo_and_power_synthetic_only(self):
        sessions = schedule()
        ss = [d for d, c in sessions.items() if c is not None and 2017 <= d.year <= 2025]
        raw, by_fund = [], {}
        # Two independently listed funds on spread-out filing dates, clearing the
        # placement floor so the power simulation exercises all dependence cases.
        for i, day in enumerate([x for x in ss if x.day in (5, 10, 15)]):
            for j in range(2):
                key = f"artificial {i}-{j}"
                at = sessions[day].astimezone(NY) - timedelta(hours=2)
                raw.append({"acceptanceDateTime": at.isoformat(), "et_date": str(day),
                            "is_cef_subject": True, "is_preferred": False, "cef_cik": key,
                            "filer_group": SABA if j else "fictitious other", "accession": key})
                by_fund[key] = (i, at)

        def read_leg(key, a, b):
            if key != "PCEF":
                i, at = by_fund[key]
                # No observer is ever given a quote or target-close row.
                self.assertLess(sessions[b], at)
                delta = (i % 13) - 5 if i % 19 else 43
            else:
                delta = 0
            return Leg(key, a, b, F(100), F(100) + F(delta, 10), True, True, ())

        aggregate = measure(raw, sessions, read_leg)
        counted = counts(raw, sessions)
        for n in HOLDS:
            row = aggregate[str(n)]
            self.assertEqual(row["placebo_filer_days"], counted["holds"][str(n)]["mature_as_of"]["filer_days"])
            self.assertNotIn("mean", row)
            self.assertNotIn("median", row)
        out = power(raw, sessions, aggregate, trials=3)
        self.assertEqual(out["hold_sessions"], HOLDS)
        self.assertEqual(out["year_span"][-1], CUTOFF.year)
        self.assertEqual(out["minimum_net_edge_by_scenario"]["20"]["high"]["gaussian_sd"]["1.0"]
                         ["placement_probability"], 1.)

        first, later = ss[10], ss[75]
        prior_target_exit = ss[70]
        for d in (first, later):
            at = sessions[d].astimezone(NY) - timedelta(hours=2)
            raw.append({"acceptanceDateTime": at.isoformat(), "et_date": str(d),
                        "is_cef_subject": True, "is_preferred": False, "cef_cik": "repeat",
                        "filer_group": SABA, "accession": str(d)})
        for d in (later,):
            at = sessions[d].astimezone(NY) - timedelta(hours=2)
            raw.append({"acceptanceDateTime": at.isoformat(), "et_date": str(d),
                        "is_cef_subject": True, "is_preferred": False, "cef_cik": "another",
                        "filer_group": SABA, "accession": f"{d}-another"})
        permitted_benchmark = []

        def overlapping_case(key, a, b):
            if key == "repeat":
                self.assertLess(b, first)
                return Leg(key, a, b, F(5), F(4), True, True, ())
            if key == "another":
                self.assertEqual(b, prior_target_exit)
                return None   # missing is counted, never replaced
            if key == "PCEF" and b == prior_target_exit:
                permitted_benchmark.append((a, b))
            return read_leg(key, a, b)

        blocked = measure(raw, sessions, overlapping_case)
        for n in HOLDS:
            self.assertEqual(blocked[str(n)]["target_overlap"], 1)
            self.assertEqual(blocked[str(n)]["missing_endpoint_or_identity"], 1)
        self.assertEqual(len(permitted_benchmark), 3)

    def test_projection_canonical_aliases_authentic_bytes_and_exact_fields(self):
        sessions = schedule()
        raw = []
        for i, day in enumerate((date(2022, 7, 15), date(2022, 7, 18))):
            at = sessions[day].astimezone(NY) - timedelta(hours=2)
            raw.append({"acceptanceDateTime": at.isoformat(), "et_date": str(day),
                        "is_cef_subject": True, "is_preferred": False, "cef_cik": f"test{i}",
                        "filer_group": SABA if i else "fictitious other", "accession": str(i)})
        evidence = []

        def seal(role, *binding):
            b = tuple(map(str, binding))
            details = {"action_sha256s": []} if role == "action_coverage" else {}
            support = []
            for source in ("issuer_primary", "vendor_native", "independent_reconciliation"):
                excerpt = json.dumps([source, role, list(b)]).encode("ascii")
                fragment = json.dumps({"schema": "plan63-bound-source-excerpt-v1", "source_kind": source,
                    "role": role, "binding": list(b), "excerpt_sha256": sha256(excerpt).hexdigest(),
                    "excerpt_b64": b64encode(excerpt).decode("ascii"), "claim": details}).encode("ascii")
                support.append({"source_kind": source, "sha256": sha256(fragment).hexdigest(),
                                "bytes_b64": b64encode(fragment).decode("ascii")})
            src = json.dumps({"schema": "plan63-reviewed-proof-v1", "role": role, "binding": list(b),
                              "support": support, "details": details}).encode("ascii")
            pin = sha256(src).hexdigest()
            evidence.append({"sha256": pin, "role": role, "binding": list(b),
                             "bytes_b64": b64encode(src).decode("ascii")})
            return pin

        identity = {}
        for i, key in enumerate(("test0", "test1", "PCEF")):
            issue, alias = "issue-" + key, "alias-" + key
            cusip = f"QA{i:07d}"
            identity[key] = {"subject_key": key, "stable_security_id": issue,
                             "identity_sha256": seal("identity", key, issue),
                             "dated_aliases": [{"alias": alias, "from_session": "2016-01-01",
                                                "through_session": "2026-11-25", "cusips": [cusip], "evidence_sha256":
                                                seal("alias", key, issue, alias, "2016-01-01", "2026-11-25", cusip)}]}
        scope = sorted({(key, *span) for rows in admissible(raw, sessions).values()
                        for r, g, span in rows if g == "eligible" for key in (r["fund"], "PCEF")})
        manifest = {"schema": "plan63-placebo-projection-v1",
                    "identity_map": list(identity.values()), "scopes": [], "successor_marks": []}
        preflight = {"schema": "plan63-approved-scope-preflight-v1", "excluded": [], "deny": [], "successor_marks": []}
        indices = {"schema": "plan63-placebo-leaf-index-v1", "legs": []}
        native = {"schema": "plan63-placebo-bar-transport-v1", "streams": []}
        tokens, archives, denied_offsets = {}, {}, {}
        for key, a, b in scope:
            issue, alias = identity[key]["stable_security_id"], identity[key]["dated_aliases"][0]["alias"]
            attrs = {"subject_key": key, "start": str(a), "end": str(b), "stable_security_id": issue}
            manifest["scopes"].append({**attrs, "status": "present", "entry_alias": alias, "exit_alias": alias,
                                       "identity_sha256": identity[key]["identity_sha256"],
                                       "split_basis_sha256": seal("basis", issue, a, b),
                                       "action_coverage_sha256": seal("action_coverage", issue, a, b),
                                       "missing_endpoint_sha256": None})
            ix = {**attrs, "actions": []}
            for side, d in (("entry", a), ("exit", b)):
                field = (key, d)
                if field not in tokens:
                    t = datetime.combine(d, time(), NY).isoformat()
                    body = json.dumps({"bars": {alias: [{"t": t, "o": 10, "h": 999999, "l": 10,
                                                         "c": 10, "v": 1}]}, "next_page_token": None}).encode("ascii")
                    tokens[field] = approved_bar_leaves(body, {(alias, d)})[alias, d]
                    packed = compress(body, mtime=0)
                    digest = sha256(body).hexdigest()
                    denied_offsets[digest] = body.index(b"999999")
                    partition = "benchmark" if key == "PCEF" else "placebo"
                    path = f"{partition}/native/bars_raw/{digest}.json.gz"
                    archives[path] = packed
                    native["streams"].append({"partition": partition, "subject_key": key,
                        "stable_security_id": issue, "alias": alias, "first": str(d), "last": str(d),
                        "feed": "sip", "view": "raw", "pages": [{"file": path,
                        "file_sha256": sha256(packed).hexdigest(), "body_sha256": digest,
                        "page_token": None, "next_page_token": None}]})
                ix[side] = tokens[field]
            indices["legs"].append(ix)

        def build(ix, v):
            return project(manifest, raw, sessions, Proofs(evidence), ix, v, preflight, load_archive=archives.__getitem__)

        blob = build(indices, native)
        with patch("placebo_project_63.single_token", side_effect=AssertionError("premature price read")) as spy:
            spy.reset_mock()
            extra_scope = deepcopy(indices)
            extra_scope["legs"].append({**extra_scope["legs"][0], "subject_key": "forbidden"})
            late_bad = deepcopy(indices)
            late_bad["legs"][-1]["entry"]["volume"] = 9
            redirected = deepcopy(indices)
            ref = redirected["legs"][0]["entry"]["close_ref"]
            ref.update(offset=denied_offsets[ref["body_sha256"]], length=6)
            for ix in (extra_scope, late_bad, redirected):
                with self.assertRaises(Stop):
                    build(ix, native)
            bad_native = deepcopy(native)
            bad_native["streams"][0]["pages"][0]["body_sha256"] = "a" * 64
            with self.assertRaises(Stop):
                build(indices, bad_native)
            chain = deepcopy(native)
            chain["streams"][0]["pages"][0]["next_page_token"] = "missing-tail"
            with self.assertRaises(Stop):
                build(indices, chain)
            spy.assert_not_called()
        malformed = deepcopy(blob)
        malformed["legs"][0]["entry"]["volume"] = 0
        p = Proofs(evidence)
        allowed, _, _, _ = approved_scope(manifest, raw, sessions, p, preflight)
        with self.assertRaises(Stop):
            read_projection(malformed, allowed, p)
        alias_collision = deepcopy(manifest)
        alias_collision["identity_map"][1]["stable_security_id"] = identity["test0"]["stable_security_id"]
        with self.assertRaises(Stop):
            approved_scope(alias_collision, raw, sessions, Proofs(evidence), preflight)
        successor_missing = {**preflight, "successor_marks": [{}]}
        with self.assertRaises(Stop):
            approved_scope(manifest, raw, sessions, Proofs(evidence), successor_missing)
        with self.assertRaises(Stop):
            Proofs([{**evidence[0], "bytes_b64": b64encode(b"unapproved").decode("ascii")}])

    def test_once_lock_and_duplicate_json(self):
        with self.assertRaises(Stop):
            decode(b'{"a":1,"a":2}')
        with TemporaryDirectory() as p:
            folder = os.open(p, os.O_RDONLY | os.O_DIRECTORY)
            try:
                exclusive(folder, "attempt.once", b"pinned approval")
                with self.assertRaises(FileExistsError):
                    exclusive(folder, "attempt.once", b"second attempt")
                self.assertEqual((Path(p) / "attempt.once").read_bytes(), b"pinned approval")
            finally:
                os.close(folder)

    def test_native_bar_offset_scan_never_decodes_price(self):
        t = b'"2022-07-18T04:00:00Z"'
        native = (
            b'{"bars":{"DO-NOT-READ":[{"t":' + t + b',"c":123456789,"h":4,"o":4,"l":4,"v":1}],'
            b'"ALLOW":[{"o":2,"h":3,"l":1,"c":2.5,"t":' + t + b',"v":7}]},"next_page_token":null}'
        )
        d = date(2022, 7, 18)
        seen = []
        original = json.loads

        def only_metadata(b, *args, **kwargs):
            seen.append(b)
            self.assertNotIn(b"123456789", b)
            self.assertNotIn(b"2.5", b)
            return original(b, *args, **kwargs)

        with patch("placebo_native_63.json.loads", side_effect=only_metadata):
            got = approved_bar_leaves(native, {("ALLOW", d)})
        self.assertEqual(set(got), {("ALLOW", d)})
        off = got["ALLOW", d]["close_ref"]
        self.assertEqual(native[off["offset"]:off["offset"] + off["length"]], b"2.5")
        self.assertEqual(got["ALLOW", d]["volume"], 7)
        self.assertTrue(seen)


if __name__ == "__main__":
    unittest.main()
