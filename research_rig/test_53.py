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

    def test_cli_comparison_is_hidden_until_consuming_go(self):
        self.check_scenario("wrong_digest")

    def test_cli_correctly_pinned_bad_comparison_consumes_go(self):
        self.check_scenario("wrong_year")

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
            comparison = [{"turn": y, "portfolio": Decimal(y - 2015) / 100} for y in bars]
            paired_rows = comparison if scenario != "wrong_year" else [
                {"turn": first_turn - 1, "portfolio": comparison[0]["portfolio"]}, *comparison[1:]]
            files = {"roster.csv": roster, S.EXCLUSIONS: exclusions, S.CASH_COVERAGE: coverage,
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
                changed = {S.CASH_COVERAGE: coverage_blob, "roster.csv": roster_blob,
                           S.EXCLUSIONS: exclusions_blob} | (extra or {"split_evidence.json": files["split_evidence.json"]})
                for n, b in changed.items():
                    (inputs / n).write_bytes(b)
                manifest = {"schema": 1, "mode": "plan53_raw_sip_v1", "feed": "sip", "adjustment": "raw",
                            "first_turn": 2016, "last_turn": 2025, "collected_utc": "2026-11-26T00:00:00Z",
                            "files": {n: digest(b) for n, b in (files | changed).items()}}
                payload = S.encode(manifest)
                (inputs / "manifest.json").write_bytes(payload)
                os.chmod(inputs / "manifest.json", 0o600)
                return digest(payload)

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
                     "--roster-sha256", roster_pin, "--distributions-sha256", dist_pin],
                    capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, timeout=600)

            git("init", "-q")
            git("add", ".")
            git("commit", "-qm", "synthetic freeze")
            freeze = git("rev-parse", "HEAD")
            def approve(*extra):
                (root / S.APPROVAL).write_text(
                    f"Approved by the lead: plan 53, validation and one scored run, freeze commit {freeze}, "
                    f"freeze SHA-256 {freeze_pin}, input SHA-256 {input_pin}, roster SHA-256 {roster_pin}, "
                    f"distributions SHA-256 {dist_pin}.\n")
                git("add", S.APPROVAL, *extra)
                git("commit", "-qm", "synthetic approval")
                return git("rev-parse", "HEAD")

            def both_refuse(head, reason):
                for mode in ("--validate-inputs", "--go"):
                    out = cli_at(head, mode)
                    self.assertEqual((out.returncode, out.stdout, out.stderr.strip()), (2, "", reason))
                    self.assertFalse(any(run.iterdir()))

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
            self.assertTrue(all(re.fullmatch(r"[a-z_]+ \d+", " ".join(line)) for line in
                                zip(v.stdout.split()[1::2], v.stdout.split()[2::2])))
            self.assertFalse(any(run.iterdir()))
            g = cli("--go")
            if scenario != "valid":
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
            self.assertEqual(len(out["judged"]["years"]), 10)
            # SYNH's zero-volume pre-entry row makes it ineligible; SYND's zero-volume exit row is a missing exit.
            self.assertTrue(all(y["roster"] == 8 and y["eligible"] == 5 and y["held_missing_exit"] == 2
                                and "SYNH" not in y["held"] for y in out["judged"]["years"]))
            self.assertTrue(all((y["held_empty_cash"], y["eligible_empty_cash"]) == (1, 1)
                                and y["portfolio_price"] < y["portfolio"] for y in out["judged"]["years"]))
            self.assertIn("mean_portfolio_minus_roster_ew_price_only", out["judged"])
            self.assertEqual(set(out["shown_only"]), {"fifth_january_session_exit", "zero_cost", "replay48_correlation"})
            self.assertTrue(all(y["held_cash_gaps"] == 2 for y in out["judged"]["years"]))
            self.assertTrue(all(y["held_quote_coverage_proxy_sides"] == 2 for y in out["judged"]["years"]))
            self.assertNotIn("held_proxy_sides", out["judged"]["years"][0])
            no_cash_returns = []
            for w, row in zip(WINDOWS, out["judged"]["years"]):
                y = w["turn"]
                _, closes = C.bars_file(bars[y], w, names, cfg)
                _, benchmark_quotes = C.quotes_file(quotes[y], w, names, cfg)
                dollars, shares, _ = C.sleeve(closes, {"cash": [], "splits": []},
                                             C.side_costs(benchmark_quotes, w, cfg), w, "exit", cfg["capital"])
                no_cash_returns.append(float(dollars / cfg["capital"]))
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
                 "--roster-sha256", digest(roster + b"2016,SYNZ\n"), "--distributions-sha256", dist_pin],
                capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, timeout=600)
            self.assertEqual(other.stderr.strip(), "P53_APPROVAL")


if __name__ == "__main__":
    unittest.main()
