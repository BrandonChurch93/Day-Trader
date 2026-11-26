"""Plan 53 tests: synthetic numbers only, no market data. Run: python3 -I -B research_rig/test_53.py"""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_48 as C  # noqa: E402
import score_53 as S  # noqa: E402

CFG = S.read_config((HERE.parent / S.CONFIG).read_bytes())
CAL = json.loads((HERE / "calendar_25.json").read_bytes())
WINDOWS = C.turns(CAL, CFG)
UTC = timezone.utc


def digest(blob):
    return sha256(blob).hexdigest()


def stamp(d):
    return datetime.combine(d, time(0), C.NY).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def quote_stamps(session, step=30):
    start = datetime.combine(session, time(15, 53), C.NY).astimezone(UTC)
    return [datetime.fromtimestamp(start.timestamp() + i * step, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            for i in range(360 // step)]


def bars_for(w, base, drift, stop=None, skip=None, idle=None):
    rows = []
    for i, d in enumerate(w["sessions"]):
        if (stop and d > stop) or d == skip:
            continue
        c = (Decimal(base) + Decimal(drift) * i).quantize(Decimal("0.01"))
        rows.append({"t": stamp(d), "o": c, "h": c + Decimal("0.05"), "l": c - Decimal("0.05"), "c": c,
                     "v": 0 if d == idle else 1000})
    return rows


def quotes_for(w, mid, half="0.02", empty=False):
    out = {}
    for k in C.CLOCKS:
        m = Decimal(mid)
        out[k] = [] if empty else [{"t": t, "bp": m - Decimal(half), "ap": m + Decimal(half)}
                                   for t in quote_stamps(w[k])]
    return out


def synthetic_packet():
    """Eight synthetic funds per turn: a cheap loser set, one too dear for a share, one with a pre-entry gap,
    one with a zero-volume row before entry (ineligible), one that stops trading in January, one with no
    quotes (proxy) and a zero-volume row on the exit session (valued at its last traded close)."""
    names = ["SYNA", "SYNB", "SYNC", "SYND", "SYNE", "SYNF", "SYNG", "SYNH"]
    bars, quotes, cash = {}, {}, {"schema": 1, "turns": {}}
    for w in WINDOWS:
        y = w["turn"]
        mid_jan = [d for d in w["sessions"] if d.year == y + 1][6]
        spec = {"SYNA": ("10", "-0.004", None, None, None), "SYNB": ("12", "-0.003", None, None, None),
                "SYNC": ("14", "-0.002", mid_jan, None, None), "SYND": ("9", "-0.001", None, None, w["exit"]),
                "SYNE": ("11", "0.001", None, None, None), "SYNF": ("150", "0", None, None, None),
                "SYNG": ("8", "-0.005", None, w["sessions"][40], None),
                "SYNH": ("7", "-0.006", None, None, w["sessions"][60])}
        bars[y] = {"turn": y, "symbols": {s: bars_for(w, *spec[s]) for s in names},
                   "benchmark": bars_for(w, "100", "-0.08")}
        quotes[y] = {"turn": y, "sessions": {k: w[k].isoformat() for k in C.CLOCKS},
                     "symbols": {s: quotes_for(w, "10", empty=(s == "SYND")) for s in names},
                     "benchmark": quotes_for(w, "100", "0.01")}
        ex = [d for d in w["sessions"] if d > w["entry"]][3].isoformat()
        cash["turns"][str(y)] = {
            "symbols": {s: {"source": "https://example.test/notice", "cash": [
                {"id": f"{s}-{y}", "ex_date": ex, "amount": Decimal("0.03")}] if s != "SYNE" else [],
                "splits": []} for s in names},
            "benchmark": {"source": "https://example.test/etf", "cash": [], "splits": []}}
    roster = "turn_year,ticker\n" + "".join(f"{w['turn']},{s}\n" for w in WINDOWS for s in names)
    return names, bars, quotes, cash, roster.encode()


def dump(obj):
    """JSON with Decimals written as bare numbers, as a vendor packet would carry them."""
    if isinstance(obj, Decimal):
        return str(obj).encode()
    if isinstance(obj, dict):
        return b"{" + b",".join(json.dumps(k).encode() + b":" + dump(v) for k, v in obj.items()) + b"}"
    if isinstance(obj, list):
        return b"[" + b",".join(dump(v) for v in obj) + b"]"
    return json.dumps(obj).encode()


def evidence_for(names, reported, tail_days=0):
    """Synthetic split evidence in the vendor's native page shape; split arrays omitted when empty."""
    queries = []
    for w in WINDOWS:
        recs = reported.get(w["turn"], [])
        page = {"corporate_actions": ({"forward_splits": recs} if recs else {}), "next_page_token": None}
        queries.append({"turn": w["turn"], "symbols": list(names[w["turn"]]), "start": w["anchor"].isoformat(),
                        "end": (w["exit"] + timedelta(days=tail_days)).isoformat(),
                        "queried_utc": "2026-11-26T00:00:00Z", "pages": [page]})
    return {"schema": 1, "vendor": "synthetic", "queries": queries}


def parsed(blob):
    return S.parse(blob)


def holdings_roster(names, cfg):
    """Synthetic PCEF filings and one excluded municipal line per turn."""
    proof = "https://example.test/proof"
    header = ("turn_year,holding_id,ticker,cik,holding_name,identity_url,series,"
              "report_period,public_date,form,filing_url")
    roster, exclusions = [header], [header + ",reason"]
    for w in WINDOWS:
        y = w["turn"]
        form = cfg["holdings_forms"][(y - cfg["first_turn"]) % len(cfg["holdings_forms"])]
        accession = f"0000000099-{y % 100:02d}-999999"
        url = (f"https://www.sec.gov/Archives/edgar/data/{int(cfg['holdings_trust_cik'])}/"
               f"{accession.replace('-', '')}/{accession}-index.htm")
        snap = f"{cfg['holdings_series']},{y}-08-31,{y}-10-20,{form},{url}"
        roster.extend(f"{y},{i},{s},{i:010d},{s} Fund,{proof},{snap}" for i, s in enumerate(names, 1))
        exclusions.append(f"{y},{len(names) + 1},SYNZ,0000000099,SYNZ Tax-Free Trust,{proof},{snap},municipal_name")
    return tuple(("\n".join(rows) + "\n").encode() for rows in (roster, exclusions))


def bad_holdings_cases(roster, exclusions):
    return (
        ("cutoff", roster.replace(b"2016-10-20", b"2016-12-01"), exclusions, "ROSTER_CLOCK"),
        ("future_period", roster.replace(b"2016-08-31,2016-10-20", b"2016-12-01,2016-12-02"), exclusions,
         "ROSTER_CLOCK"),
        ("impossible_period", roster.replace(b"2016-08-31", b"2016-10-21"), exclusions, "ROSTER_CLOCK"),
        ("cross_file_snapshot", roster, exclusions.replace(b"2016-10-20", b"2016-11-01", 1), "ROSTER_SNAPSHOT"),
        ("wrong_form", roster.replace(b"N-Q,", b"13F-HR,", 1), exclusions, "ROSTER_SNAPSHOT"),
        ("wrong_series", roster.replace(b"S000027370", b"S999999999", 1), exclusions, "ROSTER_SNAPSHOT"),
        ("wrong_host", roster.replace(b"www.sec.gov", b"www.sec.gov.example.test", 1), exclusions, "ROSTER_SNAPSHOT"),
        ("wrong_path", roster.replace(b"/edgar/data/1378872/", b"/edgar/data/1378873/", 1), exclusions,
         "ROSTER_SNAPSHOT"),
        ("accession_mismatch", roster.replace(b"16-999999-index", b"16-999998-index", 1), exclusions,
         "ROSTER_SNAPSHOT"),
        ("municipal_admission", roster.replace(b"SYNA Fund", b"SYNA Tax-Exempt Fund", 1), exclusions,
         "ROSTER_METADATA"),
        ("municipal_mislabel", roster, exclusions.replace(b"municipal_name", b"replay48_overlap", 1),
         "ROSTER_EXCLUSIONS"),
        ("duplicate_admitted_cik", roster.replace(b"2016,2,SYNB,0000000002", b"2016,2,SYNB,0000000001", 1),
         exclusions, "ROSTER_METADATA"),
        ("noncontiguous_id", roster, exclusions.replace(b"2016,", b"2016,999", 1), "ROSTER_HOLDINGS_IDS"),
        ("duplicate_id", roster, re.sub(rb"\n2016,\d+,", b"\n2016,2,", exclusions, count=1), "ROSTER_METADATA"),
        ("unknown_roster_column", roster.replace(b",filing_url\n", b",filing_url,unknown\n", 1), exclusions,
         "ROSTER_METADATA"),
        ("unknown_exclusion_column", roster, exclusions.replace(b",reason\n", b",reason,unknown\n", 1),
         "ROSTER_EXCLUSIONS"),
    )


class Unit(unittest.TestCase):
    def test_jump_pairs_match_original_check_and_can_span_gaps(self):
        a, skipped, b, c = WINDOWS[0]["sessions"][:4]
        limit = C.exact(CFG["split_check_ratio"])
        closes = {a: Fraction(10), b: 10 * limit, c: Fraction(10)}
        self.assertEqual(list(S.jump_flags(closes, (), limit)), [])
        C.check_jumps(closes, (), CFG)
        closes[b] += Fraction(1, 100)
        expected = [(a.isoformat(), b.isoformat()), (b.isoformat(), c.isoformat())]
        self.assertEqual(list(S.jump_flags(closes, (), limit)), expected)
        with self.assertRaisesRegex(C.Refused, "P48_UNRECORDED_SPLIT"):
            C.check_jumps(closes, (), CFG)
        self.assertEqual(list(S.jump_flags(closes, [(skipped, 2), (c, 2)], limit)), expected[:1])
        self.assertEqual(list(S.jump_flags(closes, [(b, 2), (c, 2)], limit)), [])
        C.check_jumps(closes, [(b, 2), (c, 2)], CFG)

    def test_multiple_identity_pairs_exclude_same_fund_turn_only_once(self):
        w, other = WINDOWS[:2]
        a, b, c = (d.isoformat() for d in w["sessions"][:3])
        pairs = {(w["turn"], "SYN", a, b), (w["turn"], "SYN", b, c)}
        excluded, report = S.reconcile_jumps(pairs, dict.fromkeys(pairs, "IDENTITY_BREAK"),
                                            [w, other], CFG["benchmark"])
        self.assertEqual(excluded, {w["turn"]: {"SYN"}, other["turn"]: set()})
        self.assertEqual([r["outcome"] for r in report], ["EXCLUDED_IDENTITY_BREAK"] * 2)

    def test_vendor_gate_exact_boundary_and_none(self):
        w = WINDOWS[0]
        y = w["turn"]
        names = [f"SYN{k}" for k in range(50)]
        statuses = {(y, s): ("none" if i == 49 else "documented") for i, s in enumerate(names)}
        ex = w["exit"]
        pay = Fraction(1, 10)
        primary = {y: ({s: {"cash": [(ex, pay)] * (2 if i == 0 else 1) if i < 49 else [], "splits": []}
                        for i, s in enumerate(names)}, {"cash": [], "splits": []})}
        vendor_row = {"id": "a", "ex_date": ex.isoformat(), "amount": Decimal("0.1001"), "currency": "",
                      "source": "https://example.test/vendor"}
        block = {s: {"complete": True, "events": [vendor_row]} for s in names}
        raw = {"schema": 1, "turns": {str(y): block}}

        def gate():
            effective, stats = S.vendor_cash(raw, primary, statuses, [w], {y: names}, C, CFG)
            self.assertEqual(effective, primary)
            return stats

        self.assertTrue(gate()["passed"])  # 49/50 both ways: one excess in a none window, one missed event
        self.assertEqual(gate()["overlap"], {"fund_years": 50, "primary_events": 50,
                                           "matched_events": 49, "clean_windows": 49})
        block[names[0]]["events"] = [vendor_row | {"amount": Decimal("0.10010001")}]
        self.assertFalse(gate()["passed"])  # just outside tolerance; no rounding or reuse
        for s in names:
            statuses[y, s] = "none"
            primary[y][0][s]["cash"] = []
            block[s]["events"] = []
        self.assertFalse(gate()["passed"])  # complete clean windows, but no positive match denominator

    def test_roster_holdings_metadata_and_strict_cutoff(self):
        roster, exclusions = holdings_roster(["SYNA", "SYNB"], CFG)
        admitted, excluded = S.roster_metadata(roster, exclusions, WINDOWS, C, CFG)
        self.assertEqual(admitted[WINDOWS[0]["turn"]], ("SYNA", "SYNB"))
        self.assertEqual(excluded, len(WINDOWS))
        for label, included, removed, error in bad_holdings_cases(roster, exclusions):
            with self.subTest(case=label), self.assertRaisesRegex(S.Refused, "P53_" + error):
                S.roster_metadata(included, removed, WINDOWS, C, CFG)
        self.assertFalse(S.municipal_name("Municipally Fund", CFG))
        self.assertTrue(S.municipal_name("A muni. fund", CFG))

    def test_calendar(self):
        self.assertEqual(len(WINDOWS), 10)
        first, last = WINDOWS[0], WINDOWS[-1]
        self.assertEqual(first["anchor"], date(2016, 1, 4))
        self.assertEqual((first["formation"], first["entry"], first["exit"]),
                         (date(2016, 12, 29), date(2016, 12, 30), date(2017, 1, 31)))
        self.assertEqual((last["formation"], last["entry"], last["exit"], last["shown_exit"]),
                         (date(2025, 12, 30), date(2025, 12, 31), date(2026, 1, 30), date(2026, 1, 8)))

    def test_spread_median_crossed_and_coverage(self):
        w = WINDOWS[0]
        rows = C.quote_rows(quotes_for(w, "10", "0.05")["entry"], w["entry"], CFG)
        self.assertEqual(C.measured_half_spread(rows, w["entry"], CFG), Fraction(1, 100) / 2)
        crossed = [(t, ap, bp) for t, bp, ap in rows]
        self.assertIsNone(C.measured_half_spread(crossed, w["entry"], CFG))
        self.assertIsNone(C.measured_half_spread(rows[-1:], w["entry"], CFG))

    def test_costs_proxy_and_exit_max(self):
        w = WINDOWS[0]
        q = {k: C.quote_rows(v, w[k], CFG) for k, v in quotes_for(w, "10", "0.05").items()}
        c = C.side_costs(q, w, CFG)
        self.assertEqual(c["entry"], Fraction(1, 200) + Fraction(5, 10_000))
        self.assertEqual(c["missing_exit"], Fraction(50, 10_000) + Fraction(5, 10_000))
        none = C.side_costs({k: [] for k in C.CLOCKS}, w, CFG)
        self.assertTrue(all(none["proxied"].values()))

    def test_sleeve_missing_exit_and_cash(self):
        w = WINDOWS[0]
        closes = {d: Fraction(10) for d in w["sessions"] if d <= w["exit"]}
        last = max(closes)
        del closes[last]
        costs = {"entry": Fraction(0), "exit": Fraction(0), "shown_exit": Fraction(0),
                 "missing_exit": Fraction(1, 100)}
        later = [d for d in w["sessions"] if d > w["entry"]]
        acts = {"cash": [(later[0], Fraction(1, 10)), (last, Fraction(5))], "splits": []}
        dollars, shares, missing = C.sleeve(closes, acts, costs, w, "exit", Fraction(100))
        self.assertTrue(missing)
        self.assertEqual(shares, 10)
        self.assertEqual(dollars, 10 * (Fraction(10) * Fraction(99, 100) + Fraction(1, 10) - 10))

    def test_split_after_entry_and_unrecorded_jump(self):
        w = WINDOWS[0]
        days = [d for d in w["sessions"] if d <= w["exit"]]
        later = [d for d in days if d > w["entry"]]
        split_day = later[2]
        closes = {d: Fraction(20) if d < split_day else Fraction(10) for d in days}
        zero = {"entry": Fraction(0), "exit": Fraction(0), "shown_exit": Fraction(0), "missing_exit": Fraction(0)}
        acts = {"cash": [(later[5], Fraction(1, 10))], "splits": [(split_day, Fraction(2))]}
        dollars, shares, _ = C.sleeve(closes, acts, zero, w, "exit", Fraction(100))
        self.assertEqual((shares, dollars), (5, Fraction(1)))
        C.check_jumps(closes, acts["splits"], CFG)
        with self.assertRaises(C.Refused):
            C.check_jumps(closes, [], CFG)

    def test_zero_volume_row_is_no_bar(self):
        w = WINDOWS[0]
        rows = parsed(dump(bars_for(w, "10", "0", idle=w["entry"])))
        closes = C.bar_rows(rows, w, w["entry"])
        self.assertNotIn(w["entry"], closes)
        self.assertEqual(len(closes), len(w["sessions"]) - 1)
        self.assertFalse(C.complete_through(closes, w, w["entry"]))
        negative = bars_for(w, "10", "0")
        negative[0]["v"] = -1
        with self.assertRaises(C.Refused):
            C.bar_rows(parsed(dump(negative)), w, w["entry"])
        bench = bars_for(w, "100", "0", idle=w["exit"])
        raw = {"turn": w["turn"], "symbols": {}, "benchmark": bench}
        with self.assertRaises(C.Refused):
            C.bars_file(parsed(dump(raw)), w, (), CFG)

    def test_split_evidence_coverage_and_binding(self):
        names = {w["turn"]: ("SYNA", "SYNB") for w in WINDOWS}
        none = {"cash": [], "splits": []}
        w0 = WINDOWS[0]
        split_day = w0["sessions"][100]
        cash = {w["turn"]: ({"SYNA": none, "SYNB": none}, none) for w in WINDOWS}
        cash[w0["turn"]] = ({"SYNA": {"cash": [], "splits": [(split_day, Fraction(2))]}, "SYNB": none}, none)
        good = evidence_for(names, {w0["turn"]: [{"symbol": "SYNA", "ex_date": split_day.isoformat(),
                                                  "new_rate": 2, "old_rate": 1}]})
        C.split_evidence(good, WINDOWS, names, cash)
        unrecorded = {w["turn"]: ({"SYNA": none, "SYNB": none}, none) for w in WINDOWS}
        with self.assertRaises(C.Refused):
            C.split_evidence(good, WINDOWS, names, unrecorded)
        truncated = json.loads(json.dumps(good))
        truncated["queries"][3]["pages"][-1]["next_page_token"] = "more"
        with self.assertRaises(C.Refused):
            C.split_evidence(truncated, WINDOWS, names, cash)
        short = evidence_for({w["turn"]: ("SYNA",) for w in WINDOWS}, {})
        with self.assertRaises(C.Refused):
            C.split_evidence(short, WINDOWS, names, cash)

    def test_split_control(self):
        names, bars, quotes, cash, roster = synthetic_packet()
        w = WINDOWS[0]
        y = w["turn"]
        nm = {x["turn"]: tuple(sorted(names)) for x in WINDOWS}
        acts = C.distributions(parsed(dump(cash)), WINDOWS, nm, CFG)
        block = {s: {"matched": len(bars[y]["symbols"][s]), "one_sided": 0, "steps": 0} for s in names}
        block["PCEF"] = {"matched": len(bars[y]["benchmark"]), "one_sided": 0, "steps": 0}
        raw = {"schema": 1, "vendor": "synthetic", "queried_utc": "2026-11-26T00:00:00Z",
               "turns": {str(x["turn"]): block for x in WINDOWS}}
        ctl = C.split_control(raw, WINDOWS, nm, CFG)
        C.check_control(ctl[y], parsed(dump(bars[y])), acts[y], CFG)
        for key, bad in (("steps", 1), ("one_sided", 1), ("matched", 0)):
            broken = {s: dict(v) for s, v in block.items()}
            broken["SYNA"][key] = bad
            with self.assertRaises(C.Refused):
                C.check_control(broken, parsed(dump(bars[y])), acts[y], CFG)
        broken = {s: dict(v) for s, v in block.items()}
        broken["PCEF"]["steps"] = 1
        with self.assertRaises(C.Refused):
            C.check_control(broken, parsed(dump(bars[y])), acts[y], CFG)

    def test_loser_mark_needs_price_only_leg(self):
        base = {"portfolio": Fraction(1, 10), "benchmark": Fraction(0), "roster_ew": Fraction(0)}
        rows = [dict(base, portfolio_price=Fraction(1, 10), roster_ew_price=Fraction(0)) for _ in range(10)]
        marks, ok = C.assess(rows, CFG)
        self.assertTrue(ok and marks["beats_roster_mean"])
        tilted = [dict(r, portfolio_price=Fraction(0), roster_ew_price=Fraction(1, 100)) for r in rows]
        marks, ok = C.assess(tilted, CFG)
        self.assertFalse(marks["beats_roster_mean"])
        self.assertFalse(ok)

    def test_marks_zero_not_positive(self):
        rows = [{"portfolio": Fraction(0), "benchmark": Fraction(0), "roster_ew": Fraction(0)}] * 10
        marks, ok = C.assess(rows, CFG)
        self.assertFalse(ok)
        self.assertFalse(marks["positive_mean"])
        self.assertFalse(marks["beats_roster_mean"])

    def test_ranking_eligibility_and_ties(self):
        names, bars, quotes, cash, roster = synthetic_packet()
        w = WINDOWS[0]
        funds, bench = C.bars_file(parsed(dump(bars[w["turn"]])), w, tuple(sorted(names)), CFG)
        q = C.quotes_file(parsed(dump(quotes[w["turn"]])), w, tuple(sorted(names)), CFG)
        cl = C.distributions(parsed(dump(cash)), WINDOWS, {x["turn"]: tuple(sorted(names)) for x in WINDOWS}, CFG)
        r = C.turn_result(w, funds, bench, q, cl[w["turn"]], CFG)
        self.assertEqual((r["roster"], r["eligible"], r["picks"]), (8, 5, 5))
        self.assertNotIn("SYNH", r["held"])
        self.assertEqual(r["held_missing_exit"], 2)
        self.assertEqual((r["held_empty_cash"], r["eligible_empty_cash"]), (1, 1))
        self.assertLess(r["portfolio_price"], r["portfolio"])
        self.assertEqual(r["held_proxy_sides"], 2)
        tie = {"SYNB": dict(funds["SYNA"]), "SYNA": dict(funds["SYNA"])}
        q2 = ({"SYNA": q[0]["SYNA"], "SYNB": q[0]["SYNA"]}, q[1])
        none = {"cash": [], "splits": []}
        cash2 = ({"SYNA": none, "SYNB": {"cash": [], "splits": [(w["formation"], Fraction(2))]}}, none)
        cfg1 = CFG | {"picks": 1}
        a = C.turn_result(w, tie, bench, q2, cash2, cfg1)
        self.assertEqual((a["picks"], a["eligible"], a["held"]), (1, 1, ["SYNA"]))
        cash3 = ({"SYNA": none, "SYNB": none}, none)
        b = C.turn_result(w, tie, bench, q2, cash3, cfg1)
        self.assertEqual((b["eligible"], b["held"]), (2, ["SYNA"]))

    def test_calibration_small(self):
        cfg = CFG | {"calibration": CFG["calibration"] | {"trials": 300}}
        a, b = C.calibrate(cfg), C.calibrate(cfg)
        self.assertEqual(a, b)
        self.assertLessEqual(a["pass_rate"]["zero_edge"], 0.1)
        self.assertGreater(a["pass_rate"]["loser_edge_0.03"], a["pass_rate"]["zero_edge"])

    def test_pinned_calibration_matches_config(self):
        S.check_calibration(C, CFG, (HERE / "CALIBRATION_53.json").read_bytes())

    def test_bad_inputs_refused(self):
        w = WINDOWS[0]
        bad = bars_for(w, "10", "0")
        bad[3]["l"] = Decimal("99")
        with self.assertRaises(C.Refused):
            C.bar_rows(parsed(dump(bad)), w, w["entry"])
        with self.assertRaises(C.Refused):
            C.roster(b"turn_year,ticker\n2016,PCEF\n", CFG)
        with self.assertRaises(S.Refused):
            S.parse(b'{"a": NaN}')

    def test_correlation_pairing_and_constant(self):
        years = [{"turn": y, "portfolio": (y - 2015) / 100} for y in range(2016, 2026)]
        same = S.correlation(S.encode(years), years)
        self.assertAlmostEqual(same["pearson_r"], 1.0)
        opposite = [{"turn": r["turn"], "portfolio": -r["portfolio"]} for r in years]
        self.assertAlmostEqual(S.correlation(S.encode(opposite), years)["pearson_r"], -1.0)
        constant = [{"turn": r["turn"], "portfolio": 0} for r in years]
        self.assertIsNone(S.correlation(S.encode(constant), years)["pearson_r"])
        with self.assertRaisesRegex(S.Refused, "P53_CORRELATION"):
            S.correlation(S.encode(years[::-1]), years)


class EndToEnd(unittest.TestCase):
    """Runs every real-mode CLI path (validate, go, refused second go) as a subprocess in a temporary Git repo.
    The scorer, engine, test, calendar and config are copied. The DATA line and calibration trial count
    are rewritten, and the engine gains a tripwire; the plan, ledger and queue are synthetic stubs."""

    def test_cli_validate_go_and_consumed(self):
        self.check_scenario("valid")

    def test_cli_vendor_gate_failure_uses_only_primary(self):
        self.check_scenario("vendor_fail")

    def test_cli_unproven_currency_state_uses_only_primary(self):
        self.check_scenario("currency_fail")

    def test_cli_comparison_is_hidden_until_consuming_go(self):
        self.check_scenario("wrong_digest")

    def test_cli_correctly_pinned_bad_comparison_consumes_go(self):
        self.check_scenario("wrong_year")

    def test_cli_jump_clearances(self):
        self.check_scenario("jumps")

    def test_cli_identity_segments(self):
        self.check_scenario("identity")

    def check_scenario(self, scenario):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            root, data = tmp / "repo", tmp / "data"
            (root / "research_rig").mkdir(parents=True)
            (root / "config").mkdir()
            (root / "docs").mkdir()
            src = (HERE / "score_53.py").read_text()
            line = 'DATA = Path("/home/user/workspace/rig/data")\n'
            self.assertEqual(src.count(line), 1)
            (root / "research_rig/score_53.py").write_text(src.replace(line, f'DATA = Path("{data}")\n'))
            for name in ("common_48.py", "test_53.py", "calendar_25.json"):
                (root / "research_rig" / name).write_bytes((HERE / name).read_bytes())
            # A validate invocation entering the real evaluator would fail even if it produced no outputs.
            # Go may enter it only after proving that the lock already exists.
            with (root / S.ENGINE).open("a") as stream:
                stream.write(f"""
import sys as _test_sys
from pathlib import Path as _TestPath
_real_evaluate = evaluate
def evaluate(*args, **kwargs):
    if "--validate-inputs" in _test_sys.argv:
        raise SystemExit("SYNTHETIC_VALIDATE_ENTERED_EVALUATOR")
    if not _TestPath({str(data / 'replay_53' / 'score_53.lock')!r}).is_file():
        raise SystemExit("SYNTHETIC_EVALUATOR_ENTERED_BEFORE_LOCK")
    return _real_evaluate(*args, **kwargs)
""")
            conf = (HERE.parent / S.CONFIG).read_text()
            block = [b for b in conf.split("\n") if b.startswith("  value: {\"first_turn\":2016")]
            self.assertEqual(len(block), 1)
            small = block[0].replace('"trials":10000', '"trials":200')
            self.assertNotEqual(small, block[0])
            scope = json.loads(conf.split("replay_53_plan:\n  value: ", 1)[1].splitlines()[0])
            names, bars, quotes, cash, _ = synthetic_packet()
            roster, exclusions = holdings_roster(names, CFG)

            def write_config(included, removed, counts=None):
                attested = {"eligible_rows_by_turn": [len(names)] * len(WINDOWS) if counts is None else counts,
                            "roster_sha256": digest(included), "exclusions_sha256": digest(removed)}
                payload = json.dumps(scope | {"roster_attestation": attested})
                (root / S.CONFIG).write_text(f"replay_48_plan:\n{small}\nreplay_53_plan:\n  value: {payload}\n")

            write_config(roster, exclusions)
            cfg = S.read_config((root / S.CONFIG).read_bytes())
            (root / S.CALIBRATION).write_bytes(S.encode(C.calibrate(cfg)))
            (root / S.PLAN).write_text("# Synthetic plan 53\n\nStatus FROZEN.\n")
            (root / S.AMENDMENT).write_text("# Synthetic cash amendment\n\nStatus FROZEN.\n")
            (root / S.JUMP_AMENDMENT).write_text("# Synthetic jump amendment\n\nStatus FROZEN.\n")
            link = f"`{S.PLAN}`"
            (root / "research_rig/TRIAL_LEDGER.md").write_text(f"| {S.LEDGER_ROW} | {link} |\n")
            (root / "docs/QUEUE.md").write_text(f"| {S.QUEUE_ROW} | {link} |\n")
            pins = {n: digest((root / n).read_bytes()) for n in sorted(S.PIN_NAMES)} | {
                S.ROSTER_PIN: digest(roster), S.EXCLUSIONS_PIN: digest(exclusions)}
            (root / S.PINS).write_bytes(S.encode(pins))
            freeze_pin = digest((root / S.PINS).read_bytes())

            inputs, run = data / "plan53_inputs", data / "replay_53"
            inputs.mkdir(parents=True)
            run.mkdir()
            os.chmod(inputs, 0o700)
            os.chmod(run, 0o700)
            initial = WINDOWS[0]
            evidence = evidence_for({w["turn"]: names + [cfg["benchmark"]] for w in WINDOWS}, {
                initial["turn"]: [{"symbol": "OTHER", "ex_date": "2016-06-01", "new_rate": 2},
                                  {"symbol": names[0], "ex_date": (initial["exit"] + timedelta(days=1)).isoformat(),
                                   "new_rate": 2}],
            }, cfg["split_query_tail_days"])
            control = {"schema": 1, "vendor": "synthetic", "queried_utc": "2026-11-26T00:00:00Z",
                       "turns": {str(y): {s: {"matched": len(bars[y]["symbols"][s]), "one_sided": 0, "steps": 0}
                                          for s in names} | {"PCEF": {"matched": len(bars[y]["benchmark"]),
                                                                     "one_sided": 0, "steps": 0}} for y in bars}}
            coverage = ["turn_year,ticker,status,source"]
            first, second = WINDOWS[:2]
            first_turn, second_turn = first["turn"], second["turn"]
            benchmark = cfg["benchmark"]
            benchmark_payout = Decimal("30")
            cash["turns"][str(first_turn)]["benchmark"]["cash"] = [
                {"id": "benchmark-special", "ex_date": cash["turns"][str(first_turn)]["symbols"]["SYNA"]["cash"][0]["ex_date"],
                 "amount": benchmark_payout}]
            for y in bars:
                block = cash["turns"][str(y)]
                for s, b in (block["symbols"] | {cfg["benchmark"]: block["benchmark"]}).items():
                    status = ("partial" if s == "SYNA" else "documented") if b["cash"] else (
                        "none" if s == cfg["benchmark"] else "unresolved")
                    coverage.append(f"{y},{s},{status},{b['source']}")
                    for row in b["cash"]:
                        row.update(source=b["source"], source_kind="issuer_site")
            coverage = ("\n".join(coverage) + "\n").encode()
            vendor = {"schema": 1, "turns": {}}
            for w in WINDOWS:
                year = str(w["turn"])
                rows = cash["turns"][year]["symbols"]
                vendor["turns"][year] = {s: {"complete": True, "events": [
                    {k: v for k, v in row.items() if k != "source_kind"} | {"currency": ""}
                    for row in rows[s]["cash"]]} for s in names}
            v1 = vendor["turns"][str(first_turn)]
            v1["SYNA"]["events"][0]["amount"] = Decimal("100")  # same known date, must not supplement
            v1["SYNA"]["events"].append({"id": "new-partial", "ex_date": first["exit"].isoformat(),
                                        "amount": Decimal("0.01"), "source": "https://example.test/vendor",
                                        "currency": "USD" if scenario == "currency_fail" else ""})
            v1["SYNE"]["events"] = [{"id": "unresolved", "ex_date": first["exit"].isoformat(),
                                     "amount": Decimal("0.01"), "source": "https://example.test/vendor", "currency": ""}]
            v1["SYNB"]["events"][0]["amount"] += Decimal("0.0001")  # inclusive tolerance, keep primary amount
            if scenario == "vendor_fail":
                v1["SYNB"]["complete"] = False
                v1["SYNB"]["events"] = []
                v1["SYNC"]["events"].append({"id": "vendor-extra", "ex_date": first["exit"].isoformat(),
                                             "amount": Decimal("0.01"), "source": "https://example.test/vendor", "currency": ""})
            comparison = [{"turn": y, "portfolio": Decimal(y - 2015) / 100} for y in bars]
            paired_rows = comparison if scenario != "wrong_year" else [
                {"turn": first_turn - 1, "portfolio": comparison[0]["portfolio"]}, *comparison[1:]]

            def clearance_blob(rows):
                return (",".join(S.JUMP_FIELDS) + "\n" + "".join(
                    f"{y},{s},{a},{b},{kind},evidence:synthetic,{digest(b'synthetic evidence')}\n"
                    for y, s, a, b, kind in rows)).encode()

            def segments_blob(rows):
                return (",".join(S.IDENTITY_FIELDS) + "\n" + "".join(
                    ",".join(map(str, row)) + f",evidence:synthetic,{digest(b'identity evidence')}\n" for row in rows)).encode()

            identities = {(int(r["turn_year"]), r["ticker"]): r["cik"] for r in S.csv_rows(roster, {"cik"}, "TEST")}
            segments = []
            for sample in bars.values():
                for s, series in sample["symbols"].items():
                    for row in series:
                        row["symbol"] = s
            if scenario == "identity":
                # First turn held fund changes ticker right after entry and its exit is present only as the alias.
                cutoff = first["sessions"].index(first["entry"])
                a0, a1, ae = (first["sessions"][i].isoformat() for i in (0, cutoff+1, -1))
                first_symbols = bars[first_turn]["symbols"]
                segments = [(first_turn, "SYNA", identities[first_turn, "SYNA"], "SYNA", a0, first["entry"].isoformat()),
                            (first_turn, "SYNA", identities[first_turn, "SYNA"], "ALIAS", a1, ae),
                            (first_turn, "SYNH", identities[first_turn, "SYNH"], "SYNH", a0,
                             first["sessions"][40].isoformat()),
                            (second_turn, "SYNA", identities[second_turn, "SYNA"], "ALIAS",
                             second["anchor"].isoformat(), second["exit"].isoformat())]
                for row in first_symbols["SYNA"][cutoff+1:]:
                    row["symbol"] = "ALIAS"
                first_symbols["SYNA"][-1].update({k: first_symbols["SYNA"][-1][k] * Decimal("1.1") for k in "ohlc"})
                next(row for row in first_symbols["SYNG"] if row["t"] == stamp(first["formation"]))["v"] = 0
                next(row for row in first_symbols["SYNF"] if row["t"] == stamp(first["entry"]))["v"] = 0
                first_symbols["SYNH"] = first_symbols["SYNH"][:41]
                control["turns"][str(first_turn)]["SYNH"]["matched"] = 41
                for row in bars[second_turn]["symbols"]["SYNA"]:
                    row["symbol"] = "ALIAS"
                for q in evidence["queries"]:
                    if q["turn"] in {first_turn, second_turn}:
                        q["symbols"].append("ALIAS")
                    if q["turn"] == first_turn:
                        # Same literal ticker, wrong identity on this date; must not demand a split on SYNA.
                        q["pages"][0]["corporate_actions"]["forward_splits"].append(
                            {"symbol": "ALIAS", "ex_date": first["formation"].isoformat(), "new_rate": 2})
                third = WINDOWS[2]
                split_fund = cash["turns"][str(third["turn"])]["symbols"]["SYNF"]
                split_fund["splits"] = [{"id": "disjoint-reason-test", "ex_date": third["formation"].isoformat(),
                                         "ratio": 2, "source": split_fund["source"], "source_kind": "issuer_site"}]
                control["turns"][str(third["turn"])]["SYNF"]["steps"] = 1

            jump_rows = []
            if scenario == "jumps":
                # One genuine shock and rebound. One permanent identity break exactly on entry.
                for s, start, stop, kind in (
                    ("SYNA", 20, 21, "GENUINE_MOVE"),
                    ("SYNB", first["sessions"].index(first["entry"]), None, "IDENTITY_BREAK"),
                ):
                    series = bars[first_turn]["symbols"][s]
                    for row in series[start:stop]:
                        row.update({k: row[k] * 2 for k in "ohlc"})
                    for i in (start, stop) if stop else (start,):
                        jump_rows.append((first_turn, s, first["sessions"][i-1].isoformat(),
                                          first["sessions"][i].isoformat(), kind))
                # A sixth otherwise eligible fund leaves five even after the identity exclusion.
                bars[first_turn]["symbols"]["SYNH"][60]["v"] = 1000
            files = {"roster.csv": roster, S.EXCLUSIONS: exclusions, S.CASH_COVERAGE: coverage, S.VENDOR_CASH: dump(vendor),
                     S.JUMP_CLEARANCES: clearance_blob(jump_rows),
                     S.IDENTITY_SEGMENTS: segments_blob(segments),
                     S.COMPARISON: dump(paired_rows), "distributions.json": dump(cash), "split_evidence.json": dump(evidence),
                     "split_control.json": dump(control)}
            for y in bars:
                files[f"bars_{y}.json"] = dump(bars[y])
                files[f"quotes_{y}.json"] = dump(quotes[y])
            for n, b in files.items():
                (inputs / n).write_bytes(b)
                os.chmod(inputs / n, 0o600)
            roster_pin, dist_pin = digest(roster), digest(files["distributions.json"])

            def write_manifest(coverage_blob, roster_blob=roster, exclusions_blob=exclusions, extra=None):
                nonlocal jump_pin, identity_pin
                changed = {S.CASH_COVERAGE: coverage_blob, "roster.csv": roster_blob, S.EXCLUSIONS: exclusions_blob,
                           **{n: files[n] for n in (S.VENDOR_CASH, "split_evidence.json", S.JUMP_CLEARANCES, S.IDENTITY_SEGMENTS,
                                                   f"bars_{first_turn}.json")}} | (extra or {})
                for n, b in changed.items():
                    (inputs / n).write_bytes(b)
                manifest = {"schema": 1, "mode": S.INPUT_MODE, "feed": "sip", "adjustment": "raw",
                            "first_turn": 2016, "last_turn": 2025, "collected_utc": "2026-11-26T00:00:00Z",
                            "files": {n: digest(b) for n, b in (files | changed).items()}}
                payload = S.encode(manifest)
                jump_pin = manifest["files"][S.JUMP_CLEARANCES]
                identity_pin = manifest["files"][S.IDENTITY_SEGMENTS]
                (inputs / "manifest.json").write_bytes(payload)
                os.chmod(inputs / "manifest.json", 0o600)
                return digest(payload)

            jump_pin = identity_pin = None
            input_pin = write_manifest(coverage)

            genv = {"PATH": "/usr/bin:/bin", "HOME": str(tmp), "GIT_CONFIG_GLOBAL": "/dev/null",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "Synthetic", "GIT_AUTHOR_EMAIL": "s@example.test",
                    "GIT_COMMITTER_NAME": "Synthetic", "GIT_COMMITTER_EMAIL": "s@example.test"}

            def git(*args):
                return subprocess.run(["/usr/bin/git", "-C", str(root), *args], check=True, capture_output=True,
                                      text=True, env=genv).stdout.strip()

            def cli_at(commit, mode):
                return subprocess.run(
                    [sys.executable, "-I", "-B", str(root / "research_rig/score_53.py"), mode,
                     "--approval-commit", commit, "--freeze-sha256", freeze_pin, "--input-sha256", input_pin,
                     "--roster-sha256", roster_pin, "--distributions-sha256", dist_pin, "--jump-clearances-sha256", jump_pin,
                     "--identity-segments-sha256", identity_pin],
                    capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, timeout=600)

            git("init", "-q")
            git("add", ".")
            git("commit", "-qm", "synthetic freeze")
            freeze = git("rev-parse", "HEAD")
            def approve(*extra, legacy=False):
                (root / S.APPROVAL).write_text(
                    f"Approved by the lead: plan 53, validation and one scored run, freeze commit {freeze}, "
                    f"freeze SHA-256 {freeze_pin}, input SHA-256 {input_pin}, roster SHA-256 {roster_pin}, "
                    f"distributions SHA-256 {dist_pin}" +
                    (".\n" if legacy else f", jump clearances SHA-256 {jump_pin}, identity segments SHA-256 {identity_pin}.\n"))
                git("add", S.APPROVAL, *extra)
                git("commit", "-qm", "synthetic approval")
                return git("rev-parse", "HEAD")

            def both_refuse(head, reason):
                for mode in ("--validate-inputs", "--go"):
                    out = cli_at(head, mode)
                    self.assertEqual((out.returncode, out.stdout, out.stderr.strip()), (2, "", reason))
                    self.assertFalse(any(run.iterdir()))

            if scenario == "identity":
                good_pin = identity_pin
                identity_pin = digest(b"wrong identity pin")
                both_refuse(approve(), "P53_MANIFEST_FILES")
                git("reset", "-q", "--hard", freeze)
                identity_pin = good_pin
                head = approve()
                (inputs / S.IDENTITY_SEGMENTS).write_bytes(segments_blob([]))
                both_refuse(head, "P53_PIN")
                git("reset", "-q", "--hard", freeze)
                alias_action = {"symbol": "ALIAS", "ex_date": a1, "new_rate": 2}
                native = evidence["queries"][0]
                page = {"corporate_actions": {"forward_splits": [alias_action]}, "next_page_token": None}
                unrecorded = evidence | {"queries": [native | {"pages": [page]}, *evidence["queries"][1:]]}
                input_pin = write_manifest(coverage, extra={"split_evidence.json": dump(unrecorded)})
                both_refuse(approve(), "P53_VENDOR_SPLIT_NOT_RECORDED")
                git("reset", "-q", "--hard", freeze)
                absent = evidence | {"queries": [native | {"symbols": [s for s in native["symbols"] if s != "ALIAS"]},
                                                *evidence["queries"][1:]]}
                input_pin = write_manifest(coverage, extra={"split_evidence.json": dump(absent)})
                both_refuse(approve(), "P53_SPLIT_EVIDENCE_COVERAGE")
                git("reset", "-q", "--hard", freeze)
                for amended, reason in (
                    (segments[2:], "P53_IDENTITY_BAR"),  # undeclared alias
                    ([segments[0], (*segments[1][:4], first["sessions"][cutoff+2].isoformat(), segments[1][-1]),
                      *segments[2:]], "P53_IDENTITY_COVERAGE"),  # one trading-session gap
                    ([segments[0], (*segments[1][:4], first["entry"].isoformat(), segments[1][-1]),
                      *segments[2:]], "P53_IDENTITY_COVERAGE"),  # overlap
                    (list(reversed(segments)), "P53_IDENTITY_ORDER"),
                    ([(segments[0][0], segments[0][1], "9999999999", *segments[0][3:]), *segments[1:]],
                     "P53_IDENTITY_SCHEMA"),
                    ([*segments[:2], (first_turn, "SYNG", identities[first_turn, "SYNG"], "ALIAS", a0, ae),
                      *segments[2:]], "P53_IDENTITY_COLLISION"),
                ):
                    input_pin = write_manifest(coverage, extra={S.IDENTITY_SEGMENTS: segments_blob(amended)})
                    both_refuse(approve(), reason)
                    git("reset", "-q", "--hard", freeze)
                original = bars[first_turn]
                missing_tag = original | {"symbols": original["symbols"] | {"SYNA": [
                    {k: v for k, v in original["symbols"]["SYNA"][0].items() if k != "symbol"},
                    *original["symbols"]["SYNA"][1:]]}}
                input_pin = write_manifest(coverage, extra={f"bars_{first_turn}.json": dump(missing_tag)})
                both_refuse(approve(), "P53_IDENTITY_BAR")
                git("reset", "-q", "--hard", freeze)
                wrong = original | {"symbols": original["symbols"] | {"SYNH": [
                    *original["symbols"]["SYNH"],
                    original["symbols"]["SYNH"][-1] | {"t": stamp(first["sessions"][41])}]}}
                altered = {f"bars_{first_turn}.json": dump(wrong)}
                input_pin = write_manifest(coverage, extra=altered)
                both_refuse(approve(), "P53_IDENTITY_BAR")  # successor after certified termination
                git("reset", "-q", "--hard", freeze)
                # The first alias close also participates in the very same cross-join jump guard.
                crossed = original | {"symbols": original["symbols"] | {"SYNA": [
                    row | {k: row[k] * 2 for k in "ohlc"} if i == cutoff+1 else row
                    for i, row in enumerate(original["symbols"]["SYNA"])]}}
                input_pin = write_manifest(coverage, extra={f"bars_{first_turn}.json": dump(crossed)})
                head = approve()
                val = cli_at(head, "--validate-inputs")
                self.assertEqual((val.returncode, val.stderr.strip()), (2, "P53_JUMP_CLEARANCES"))
                self.assertEqual([r["outcome"] for r in json.loads(val.stdout.split(" ", 1)[1])],
                                 ["UNCLEARED", "UNCLEARED"])
                self.assertEqual(json.loads(val.stdout.split(" ", 1)[1])[0]["earlier_date"], first["entry"].isoformat())
                self.assertFalse(any(run.iterdir()))
                git("reset", "-q", "--hard", freeze)
                input_pin = write_manifest(coverage)

            if scenario == "jumps":
                both_refuse(approve(legacy=True), "P53_APPROVAL")
                git("reset", "-q", "--hard", freeze)
                good_pin = jump_pin
                jump_pin = digest(b"wrong jump pin")
                both_refuse(approve(), "P53_MANIFEST_FILES")
                git("reset", "-q", "--hard", freeze)
                jump_pin = good_pin
                head = approve()
                (inputs / S.JUMP_CLEARANCES).write_bytes(clearance_blob([]))
                both_refuse(head, "P53_PIN")
                git("reset", "-q", "--hard", freeze)
                for payload, reason in (
                    (b"wrong header\n", "P53_JUMP_SCHEMA"),
                    (files[S.JUMP_CLEARANCES].replace(b"evidence:synthetic", b"https://user:secret@example.test/actions"),
                     "P53_JUMP_SCHEMA"),
                    (files[S.JUMP_CLEARANCES].replace(digest(b"synthetic evidence").encode(), b"bad"), "P53_JUMP_SCHEMA"),
                    (clearance_blob([jump_rows[0], *jump_rows]), "P53_JUMP_ORDER"),
                    (clearance_blob(list(reversed(jump_rows))), "P53_JUMP_ORDER"),
                ):
                    input_pin = write_manifest(coverage, extra={S.JUMP_CLEARANCES: payload})
                    both_refuse(approve(), reason)
                    git("reset", "-q", "--hard", freeze)

                def jump_refusal(rows, expected, extra=None, code="P53_JUMP_CLEARANCES"):
                    nonlocal input_pin
                    input_pin = write_manifest(coverage, extra={S.JUMP_CLEARANCES: clearance_blob(rows)} | (extra or {}))
                    head = approve()
                    val = cli_at(head, "--validate-inputs")
                    self.assertEqual((val.returncode, val.stderr.strip()), (2, code))
                    prefix, body = val.stdout.strip().split(" ", 1)
                    self.assertEqual(prefix, "P53_JUMP_REPORT")
                    self.assertEqual([r["outcome"] for r in json.loads(body)], expected)
                    go = cli_at(head, "--go")
                    self.assertEqual((go.returncode, go.stdout, go.stderr.strip()), (2, "", code))
                    self.assertFalse(any(run.iterdir()))
                    git("reset", "-q", "--hard", freeze)

                stale = (first_turn, "SYNF", *jump_rows[0][2:4], "GENUINE_MOVE")
                jump_refusal([(*jump_rows[0][:4], "UNKNOWN"), jump_rows[2], stale],
                             ["BAD_CLASS", "UNCLEARED", "EXCLUDED_IDENTITY_BREAK", "STALE_CLEARANCE"])
                cutoff = first["sessions"].index(first["entry"])
                orig = bars[first_turn]
                post_bars = orig | {"symbols": orig["symbols"] | {"SYNB": [
                    row | {k: row[k] / 2 for k in "ohlc"} if i == cutoff else row
                    for i, row in enumerate(orig["symbols"]["SYNB"])]}}
                post = (first_turn, "SYNB", first["entry"].isoformat(), first["sessions"][cutoff+1].isoformat(),
                        "IDENTITY_BREAK")
                jump_refusal([*jump_rows[:2], post],
                             ["CLEARED_GENUINE_MOVE", "CLEARED_GENUINE_MOVE", "IDENTITY_BREAK_AFTER_ENTRY"],
                             {f"bars_{first_turn}.json": dump(post_bars)})
                pcef_bars = orig | {"benchmark": [row | {k: row[k] * 2 for k in "ohlc"} if i == 20 else row
                                                 for i, row in enumerate(orig["benchmark"])]}
                pcef_claim = (first_turn, benchmark, *jump_rows[0][2:4], "GENUINE_MOVE")
                jump_refusal([pcef_claim, *jump_rows],
                             ["BENCHMARK_FLAG", "BENCHMARK_FLAG", "CLEARED_GENUINE_MOVE", "CLEARED_GENUINE_MOVE",
                              "EXCLUDED_IDENTITY_BREAK"], {f"bars_{first_turn}.json": dump(pcef_bars)})
                jump_refusal([pcef_claim, *jump_rows],
                             ["BENCHMARK_CLEARANCE", "CLEARED_GENUINE_MOVE", "CLEARED_GENUINE_MOVE",
                              "EXCLUDED_IDENTITY_BREAK"])
                thin = orig | {"symbols": orig["symbols"] | {"SYNH": [
                    row | {"v": 0} if i == 60 else row for i, row in enumerate(orig["symbols"]["SYNH"])]}}
                jump_refusal(jump_rows, ["CLEARED_GENUINE_MOVE", "CLEARED_GENUINE_MOVE", "EXCLUDED_IDENTITY_BREAK"],
                             {f"bars_{first_turn}.json": dump(thin)}, code="P53_TOO_FEW_ELIGIBLE")
                input_pin = write_manifest(coverage)

            if scenario == "valid":
                original_freeze = freeze
                cases = (*bad_holdings_cases(roster, exclusions), ("wrong_counts", roster, exclusions, "ROSTER_COUNTS"),
                         ("attestation_mismatch", roster, exclusions, "FREEZE_ROSTER"))
                for label, included, removed, reason in cases:
                    with self.subTest(bad_holdings_packet=label):
                        counts = [len(names) + 1] + [len(names)] * (len(WINDOWS) - 1) if label == "wrong_counts" else None
                        cfg_roster = included + b"invalid config digest" if label == "attestation_mismatch" else included
                        write_config(cfg_roster, removed, counts)
                        roster_pin = digest(included)
                        bad_pins = S.encode(pins | {S.ROSTER_PIN: roster_pin, S.EXCLUSIONS_PIN: digest(removed),
                                                    S.CONFIG: digest((root / S.CONFIG).read_bytes())})
                        (root / S.PINS).write_bytes(bad_pins)
                        freeze_pin = digest(bad_pins)
                        git("add", S.PINS, S.CONFIG)
                        git("commit", "--amend", "-qm", "synthetic freeze with malformed holdings attestation")
                        freeze = git("rev-parse", "HEAD")
                        input_pin = write_manifest(coverage, included, removed)
                        both_refuse(approve(), "P53_" + reason)
                        git("reset", "-q", "--hard", original_freeze)
                freeze = original_freeze
                freeze_pin = digest((root / S.PINS).read_bytes())
                roster_pin = digest(roster)
                input_pin = write_manifest(coverage)
                for label, end in (("too_short", initial["exit"]), ("too_long", initial["exit"] + timedelta(
                        days=cfg["split_query_tail_days"] + 1))):
                    with self.subTest(padded_split_query=label):
                        queries = [evidence["queries"][0] | {"end": end.isoformat()}, *evidence["queries"][1:]]
                        input_pin = write_manifest(coverage, extra={"split_evidence.json": dump(evidence | {"queries": queries})})
                        both_refuse(approve(), "P53_SPLIT_EVIDENCE_TAIL")
                        git("reset", "-q", "--hard", freeze)
                unrecorded = {"symbol": names[0], "ex_date": initial["exit"].isoformat(), "new_rate": 2}
                padded_missing_split = evidence_for({w["turn"]: names + [cfg["benchmark"]] for w in WINDOWS},
                                                    {initial["turn"]: [unrecorded]}, cfg["split_query_tail_days"])
                input_pin = write_manifest(coverage, extra={"split_evidence.json": dump(padded_missing_split)})
                both_refuse(approve(), "P53_VENDOR_SPLIT_NOT_RECORDED")
                git("reset", "-q", "--hard", freeze)
                input_pin = write_manifest(coverage)
                (root / "NOTE.md").write_text("extra file in the approval\n")
                both_refuse(approve("NOTE.md"), "P53_APPROVAL")
                git("reset", "-q", "--hard", freeze)
                documented = f"{first_turn},{benchmark},documented,".encode()
                none = f"{second_turn},{benchmark},none,".encode()
                cases = (
                    ("missing", b"\n".join(line for line in coverage.split(b"\n") if not line.startswith(none)),
                     "P53_CASH_COVERAGE"),
                    ("partial", coverage.replace(documented, documented.replace(b",documented,", b",partial,"), 1),
                     "P53_BENCHMARK_CASH"),
                    ("unresolved", coverage.replace(none, none.replace(b",none,", b",unresolved,"), 1),
                     "P53_BENCHMARK_CASH"),
                )
                for label, changed, reason in cases:
                    with self.subTest(bad_benchmark_cash=label):
                        self.assertNotEqual(changed, coverage)
                        input_pin = write_manifest(changed)
                        both_refuse(approve(), reason)
                        git("reset", "-q", "--hard", freeze)
                for bad_block, reason in (
                    ({s: v for s, v in v1.items() if s != "SYNA"}, "VENDOR_CASH_COVERAGE"),
                    (v1 | {benchmark: {"complete": True, "events": []}}, "VENDOR_CASH_COVERAGE"),
                    (v1 | {"SYNB": v1["SYNB"] | {"complete": False}}, "VENDOR_CASH_COVERAGE"),
                    (v1 | {"SYNB": v1["SYNB"] | {"events": v1["SYNB"]["events"] * 2}}, "VENDOR_CASH_EVENT"),
                    (v1 | {"SYNB": {"complete": True, "events": [v1["SYNB"]["events"][0] | {"currency": "CAD"}]}},
                     "VENDOR_CASH_CURRENCY"),
                ):
                    turns = vendor["turns"] | {str(first_turn): bad_block}
                    input_pin = write_manifest(coverage, extra={S.VENDOR_CASH: dump(vendor | {"turns": turns})})
                    both_refuse(approve(), "P53_" + reason)
                    git("reset", "-q", "--hard", freeze)
                bad_events = (
                    {"source": "https://user:password@example.test/actions"},
                    {"source": "https://example.test/actions?token=secret"},
                    {"source": "https://example.test/actions#token=secret"},
                    {"ex_date": first["entry"].isoformat()},
                    {"amount": Decimal("0")},
                )
                for bad in (vendor | {"schema": True}, *(
                    vendor | {"turns": vendor["turns"] | {str(first_turn): v1 | {"SYNB": {
                        "complete": True, "events": [v1["SYNB"]["events"][0] | change]}}}}
                    for change in bad_events
                )):
                    input_pin = write_manifest(coverage, extra={S.VENDOR_CASH: dump(bad)})
                    both_refuse(approve(), "P53_VENDOR_CASH_EVENT" if bad["schema"] is not True else "P53_VENDOR_CASH_SCHEMA")
                    git("reset", "-q", "--hard", freeze)
                input_pin = write_manifest(coverage)

            (root / "NOTE.md").write_text("intervening commit\n")
            git("add", "NOTE.md")
            git("commit", "-qm", "intervening")
            both_refuse(approve(), "P53_APPROVAL")
            git("reset", "-q", "--hard", freeze)
            head = approve()

            def cli(mode):
                return cli_at(head, mode)

            if scenario == "wrong_digest":
                (inputs / S.COMPARISON).write_bytes(b"not the approved bytes")
            v = cli("--validate-inputs")
            self.assertEqual((v.returncode, v.stderr), (0, ""))
            self.assertTrue(v.stdout.startswith("P53_INPUTS_OK turns 10 roster_rows 80"))
            self.assertIn("events_placed 50 clusters 10 symbols 9", v.stdout)
            self.assertIn("excluded_rows 10", v.stdout)
            self.assertIn("cash_gaps 20 eligible_cash_gaps 20", v.stdout)
            passes = scenario not in {"vendor_fail", "currency_fail"}
            self.assertIn(f"vendor_gate_passed {int(passes)}", v.stdout)
            headline, jump_line = v.stdout.splitlines()
            self.assertTrue(all(re.fullmatch(r"[a-z_]+ \d+", " ".join(line)) for line in
                                zip(headline.split()[1::2], headline.split()[2::2])))
            prefix, body = jump_line.split(" ", 1)
            self.assertEqual(prefix, "P53_JUMP_REPORT")
            jump_report = json.loads(body)
            self.assertEqual(len(jump_report), len(jump_rows))
            self.assertFalse(any(run.iterdir()))
            g = cli("--go")
            if scenario in {"wrong_digest", "wrong_year"}:
                reason = "P53_PIN" if scenario == "wrong_digest" else "P53_CORRELATION"
                self.assertEqual((g.returncode, g.stdout, g.stderr.strip()), (2, "", reason))
                self.assertEqual({p.name for p in run.iterdir()}, {"score_53.lock"})
                lock_before = (run / "score_53.lock").read_bytes()
                (inputs / S.COMPARISON).write_bytes(dump(comparison))
                self.assertEqual(cli("--go").stderr.strip(), "P53_CONSUMED_OR_NOT_EMPTY")
                self.assertEqual({p.name: p.read_bytes() for p in run.iterdir()}, {"score_53.lock": lock_before})
                return
            self.assertEqual((g.returncode, g.stdout.strip(), g.stderr), (0, "P53_RESULT_WRITTEN", ""))
            self.assertEqual({p.name for p in run.iterdir()}, {"score_53.lock", "results_53.json"})
            out = json.loads((run / "results_53.json").read_bytes())
            counts = out["input_counts"]
            self.assertEqual(counts["eligible_rows"] + sum(n for k, n in counts.items() if k.startswith("ineligible_")),
                             counts["roster_rows"])
            shown = out["shown_only"]
            self.assertEqual(shown["jump_clearances"], jump_report)
            if scenario == "identity":
                self.assertEqual(out["job"]["identity_segments_sha256"], identity_pin)
                self.assertEqual(out["input_counts"]["identity_scheduled_fund_turns"], 3)
                self.assertEqual(out["input_counts"]["ineligible_terminated_before_entry"], 1)
                self.assertEqual(out["input_counts"]["ineligible_missing_entry"], 1)
                self.assertEqual(out["input_counts"]["ineligible_missing_formation"], 1)
                self.assertEqual(out["input_counts"]["ineligible_preentry_split"], 1)
                self.assertEqual(out["input_counts"]["ineligible_other_preentry_gap"], 18)
                self.assertEqual(out["input_counts"]["ineligible_unaffordable"], 8)
                self.assertEqual(out["input_counts"]["identity_excluded_fund_turns"], 0)
                for row in out["judged"]["years"][:2]:
                    self.assertIn("SYNA", row["held"])
                    self.assertNotIn("SYNH", row["held"])
                    self.assertEqual(row["held_missing_exit"], 2)  # only the pre-existing fixtures
                self.assertGreater(out["judged"]["years"][0]["portfolio"], out["judged"]["years"][1]["portfolio"])
                self.assertEqual(cli("--go").stderr.strip(), "P53_CONSUMED_OR_NOT_EMPTY")
                return
            if scenario == "jumps":
                self.assertEqual([r["outcome"] for r in jump_report],
                                 ["CLEARED_GENUINE_MOVE", "CLEARED_GENUINE_MOVE", "EXCLUDED_IDENTITY_BREAK"])
                self.assertEqual(out["job"]["jump_clearances_sha256"], jump_pin)
                self.assertEqual(out["input_counts"]["identity_excluded_fund_turns"], 1)
                self.assertEqual(out["input_counts"]["ineligible_identity_break"], 1)
                self.assertEqual(out["input_counts"]["jump_flagged_pairs"], 3)
                for table in (out["judged"], shown["primary_only"], shown["cash_zeroed"],
                              shown["zero_cost"], shown["fifth_january_session_exit"]):
                    first_row, second_row = table["years"][:2]
                    self.assertEqual((first_row["roster"], first_row["eligible"]), (8, 5))
                    self.assertIn("SYNA", first_row["held"])
                    self.assertNotIn("SYNB", first_row["held"])
                    self.assertIn("SYNB", second_row["held"])
                self.assertEqual(cli("--go").stderr.strip(), "P53_CONSUMED_OR_NOT_EMPTY")
                return
            gate = shown["vendor_cash_gate"]
            self.assertEqual((gate["passed"], gate["admitted_source_kind"], gate["admitted_events"]),
                             (passes, "vendor_crosschecked", 2 if passes else 0))
            self.assertEqual(gate["overlap"], {"fund_years": 60, "primary_events": 60,
                             "matched_events": 59 if scenario == "vendor_fail" else 60,
                             "clean_windows": 58 if scenario == "vendor_fail" else 60})
            base, zeroed, judged = shown["primary_only"], shown["cash_zeroed"], out["judged"]
            for table in (base, zeroed):
                self.assertFalse({"marks", "passed"} & set(table))
            for p, z, j in zip(base["years"], zeroed["years"], judged["years"]):
                self.assertEqual(p["benchmark"], j["benchmark"])
                self.assertEqual((j["portfolio_price"], j["roster_ew_price"]), (z["portfolio"], z["roster_ew"]))
                self.assertEqual(p["held"], j["held"])
            self.assertEqual(gate["matched_currency_states"], [""])
            self.assertEqual(gate["candidate_currency_states"], ["", "USD"] if scenario == "currency_fail" else [""])
            if not passes:
                self.assertEqual({k: v for k, v in judged.items() if k not in {"marks", "passed"}}, base)
                self.assertEqual(cli("--go").stderr.strip(), "P53_CONSUMED_OR_NOT_EMPTY")
                return
            self.assertGreater(judged["years"][0]["portfolio"], base["years"][0]["portfolio"])
            self.assertGreater(judged["years"][0]["roster_ew"], base["years"][0]["roster_ew"])
            self.assertEqual(gate["by_turn_and_primary_status"][str(first_turn)]["partial"]["admitted_events"], 1)
            self.assertEqual(gate["by_turn_and_primary_status"][str(first_turn)]["partial"]["primary_events"], 1)
            self.assertEqual(gate["by_turn_and_primary_status"][str(first_turn)]["partial"]
                             ["same_date_vendor_events_suppressed"], 1)
            self.assertEqual(gate["by_turn_and_primary_status"][str(first_turn)]["unresolved"]["admitted_events"], 1)
            self.assertEqual(len(out["judged"]["years"]), 10)
            # SYNH's zero-volume pre-entry row makes it ineligible; SYND's zero-volume exit row is a missing exit.
            self.assertTrue(all(y["roster"] == 8 and y["eligible"] == 5 and y["held_missing_exit"] == 2
                                and "SYNH" not in y["held"] for y in out["judged"]["years"]))
            self.assertTrue(all((y["held_empty_cash"], y["eligible_empty_cash"]) == ((0, 0) if i == 0 else (1, 1))
                                and y["portfolio_price"] < y["portfolio"] for i, y in enumerate(out["judged"]["years"])))
            self.assertIn("mean_portfolio_minus_roster_ew_price_only", out["judged"])
            self.assertEqual(set(shown), {"fifth_january_session_exit", "zero_cost", "replay48_correlation",
                                          "primary_only", "cash_zeroed", "vendor_cash_gate", "jump_clearances"})
            self.assertTrue(all(y["held_cash_gaps"] == 2 for y in out["judged"]["years"]))
            self.assertTrue(all(y["held_quote_coverage_proxy_sides"] == 2 for y in out["judged"]["years"]))
            self.assertNotIn("held_proxy_sides", out["judged"]["years"][0])
            no_cash_returns = []
            for w, row in zip(WINDOWS, out["judged"]["years"]):
                y = w["turn"]
                _, closes = S.identity_bars(bars[y], w, names, {}, C, cfg)
                _, benchmark_quotes = C.quotes_file(quotes[y], w, names, cfg)
                dollars, shares, _ = C.sleeve(closes, {"cash": [], "splits": []},
                                             C.side_costs(benchmark_quotes, w, cfg), w, "exit", cfg["capital"])
                no_cash_returns.append(float(dollars / cfg["capital"]))
                self.assertAlmostEqual(zeroed["years"][len(no_cash_returns) - 1]["benchmark"], no_cash_returns[-1])
                expected_cash = shares * Fraction(benchmark_payout) if y == first_turn else 0
                self.assertAlmostEqual(row["benchmark"], float((dollars + expected_cash) / cfg["capital"]))
            self.assertGreater(sum(y["portfolio"] for y in out["judged"]["years"]) - sum(no_cash_returns), 0)
            self.assertFalse(out["judged"]["marks"]["beats_benchmark_mean"])
            corr = out["shown_only"]["replay48_correlation"]
            self.assertEqual((corr["status"], corr["observations"]), ("MEASURED", 10))
            self.assertEqual([x["muni"] for x in corr["pairs"]], [float(x["portfolio"]) for x in comparison])
            self.assertEqual(out["job"]["freeze_commit"], freeze)
            before = {p.name: p.read_bytes() for p in run.iterdir()}
            again = cli("--go")
            self.assertEqual((again.returncode, again.stderr.strip()), (2, "P53_CONSUMED_OR_NOT_EMPTY"))
            self.assertEqual({p.name: p.read_bytes() for p in run.iterdir()}, before)
            (inputs / "roster.csv").write_bytes(roster + b"2016,SYNZ\n")
            os.chmod(inputs / "roster.csv", 0o600)
            bad = cli("--validate-inputs")
            self.assertEqual((bad.returncode, bad.stderr.strip()), (2, "P53_PIN"))
            other = subprocess.run(
                [sys.executable, "-I", "-B", str(root / "research_rig/score_53.py"), "--validate-inputs",
                 "--approval-commit", head, "--freeze-sha256", freeze_pin, "--input-sha256", input_pin,
                 "--roster-sha256", digest(roster + b"2016,SYNZ\n"), "--distributions-sha256", dist_pin,
                 "--jump-clearances-sha256", jump_pin, "--identity-segments-sha256", identity_pin],
                capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, timeout=600)
            self.assertEqual(other.stderr.strip(), "P53_APPROVAL")


if __name__ == "__main__":
    unittest.main()
