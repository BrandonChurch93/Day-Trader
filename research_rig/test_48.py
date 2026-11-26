"""Plan 48 tests: synthetic numbers only, no market data. Run: python3 -I -B research_rig/test_48.py"""
from datetime import date, datetime, time, timezone
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_48 as C  # noqa: E402
import score_48 as S  # noqa: E402

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


def bars_for(w, base, drift, stop=None, skip=None):
    rows = []
    for i, d in enumerate(w["sessions"]):
        if (stop and d > stop) or d == skip:
            continue
        c = (Decimal(base) + Decimal(drift) * i).quantize(Decimal("0.01"))
        rows.append({"t": stamp(d), "o": c, "h": c + Decimal("0.05"), "l": c - Decimal("0.05"), "c": c, "v": 1000})
    return rows


def quotes_for(w, mid, half="0.02", empty=False):
    out = {}
    for k in C.CLOCKS:
        m = Decimal(mid)
        out[k] = [] if empty else [{"t": t, "bp": m - Decimal(half), "ap": m + Decimal(half)}
                                   for t in quote_stamps(w[k])]
    return out


def synthetic_packet():
    """Seven synthetic funds per turn: a cheap loser set, one too dear for a share, one with a pre-entry gap,
    one that stops trading in January, one with no quotes (proxy)."""
    names = ["SYNA", "SYNB", "SYNC", "SYND", "SYNE", "SYNF", "SYNG"]
    bars, quotes, cash = {}, {}, {"schema": 1, "turns": {}}
    for w in WINDOWS:
        y = w["turn"]
        mid_jan = [d for d in w["sessions"] if d.year == y + 1][6]
        spec = {"SYNA": ("10", "-0.004", None, None), "SYNB": ("12", "-0.003", None, None),
                "SYNC": ("14", "-0.002", mid_jan, None), "SYND": ("9", "-0.001", None, None),
                "SYNE": ("11", "0.001", None, None), "SYNF": ("150", "0", None, None),
                "SYNG": ("8", "-0.005", None, w["sessions"][40])}
        bars[y] = {"turn": y, "symbols": {s: bars_for(w, *spec[s]) for s in names},
                   "benchmark": bars_for(w, "100", "0.001")}
        quotes[y] = {"turn": y, "sessions": {k: w[k].isoformat() for k in C.CLOCKS},
                     "symbols": {s: quotes_for(w, "10", empty=(s == "SYND")) for s in names},
                     "benchmark": quotes_for(w, "100", "0.01")}
        ex = [d for d in w["sessions"] if d > w["entry"]][3].isoformat()
        cash["turns"][str(y)] = {
            "symbols": {s: {"source": "https://example.test/notice", "cash": [
                {"id": f"{s}-{y}", "ex_date": ex, "amount": Decimal("0.03")}], "splits": []} for s in names},
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


def parsed(blob):
    return S.parse(blob)


class Unit(unittest.TestCase):
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
        self.assertEqual((r["roster"], r["eligible"], r["picks"]), (7, 5, 5))
        self.assertEqual(r["held_missing_exit"], 1)
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
        S.check_calibration(C, CFG, (HERE / "CALIBRATION_48.json").read_bytes())

    def test_bad_inputs_refused(self):
        w = WINDOWS[0]
        bad = bars_for(w, "10", "0")
        bad[3]["l"] = Decimal("99")
        with self.assertRaises(C.Refused):
            C.bar_rows(parsed(dump(bad)), w, w["entry"])
        with self.assertRaises(C.Refused):
            C.roster(b"turn_year,ticker\n2016,MUB\n", CFG)
        with self.assertRaises(S.Refused):
            S.parse(b'{"a": NaN}')


class EndToEnd(unittest.TestCase):
    """Runs every real-mode CLI path (validate, go, refused second go) as a subprocess in a temporary Git repo.
    The real scorer, engine, test, calendar and config are copied; only the DATA line and the calibration trial
    count are rewritten; the plan, ledger and queue are synthetic stubs."""

    def test_cli_validate_go_and_consumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            root, data = tmp / "repo", tmp / "data"
            (root / "research_rig").mkdir(parents=True)
            (root / "config").mkdir()
            (root / "docs").mkdir()
            src = (HERE / "score_48.py").read_text()
            line = 'DATA = Path("/home/user/workspace/rig/data")\n'
            self.assertEqual(src.count(line), 1)
            (root / "research_rig/score_48.py").write_text(src.replace(line, f'DATA = Path("{data}")\n'))
            for name in ("common_48.py", "test_48.py", "calendar_25.json"):
                (root / "research_rig" / name).write_bytes((HERE / name).read_bytes())
            conf = (HERE.parent / S.CONFIG).read_text()
            block = [b for b in conf.split("\n") if b.startswith("  value: {\"first_turn\":2016")]
            self.assertEqual(len(block), 1)
            small = block[0].replace('"trials":10000', '"trials":200')
            self.assertNotEqual(small, block[0])
            (root / S.CONFIG).write_text(f"replay_48_plan:\n{small}\n")
            cfg = S.read_config((root / S.CONFIG).read_bytes())
            (root / S.CALIBRATION).write_bytes(S.encode(C.calibrate(cfg)))
            (root / S.PLAN).write_text("# Synthetic plan 48\n\nStatus FROZEN.\n")
            link = f"`{S.PLAN}`"
            (root / "research_rig/TRIAL_LEDGER.md").write_text(f"| {S.LEDGER_ROW} | {link} |\n")
            (root / "docs/QUEUE.md").write_text(f"| {S.QUEUE_ROW} | {link} |\n")
            pins = {n: digest((root / n).read_bytes()) for n in sorted(S.PIN_NAMES)}
            (root / S.PINS).write_bytes(S.encode(pins))
            freeze_pin = digest((root / S.PINS).read_bytes())

            inputs, run = data / "plan48_inputs", data / "replay_48"
            inputs.mkdir(parents=True)
            run.mkdir()
            os.chmod(inputs, 0o700)
            os.chmod(run, 0o700)
            names, bars, quotes, cash, roster = synthetic_packet()
            files = {"roster.csv": roster, "distributions.json": dump(cash)}
            for y in bars:
                files[f"bars_{y}.json"] = dump(bars[y])
                files[f"quotes_{y}.json"] = dump(quotes[y])
            manifest = {"schema": 1, "mode": "plan48_raw_sip_v1", "feed": "sip", "adjustment": "raw",
                        "first_turn": 2016, "last_turn": 2025, "collected_utc": "2026-11-26T00:00:00Z",
                        "files": {n: digest(b) for n, b in files.items()}}
            files["manifest.json"] = S.encode(manifest)
            for n, b in files.items():
                (inputs / n).write_bytes(b)
                os.chmod(inputs / n, 0o600)
            input_pin, roster_pin, dist_pin = (digest(files[n]) for n in
                                               ("manifest.json", "roster.csv", "distributions.json"))

            genv = {"PATH": "/usr/bin:/bin", "HOME": str(tmp), "GIT_CONFIG_GLOBAL": "/dev/null",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "Synthetic", "GIT_AUTHOR_EMAIL": "s@example.test",
                    "GIT_COMMITTER_NAME": "Synthetic", "GIT_COMMITTER_EMAIL": "s@example.test"}

            def git(*args):
                return subprocess.run(["/usr/bin/git", "-C", str(root), *args], check=True, capture_output=True,
                                      text=True, env=genv).stdout.strip()

            def cli_at(commit, mode):
                return subprocess.run(
                    [sys.executable, "-I", "-B", str(root / "research_rig/score_48.py"), mode,
                     "--approval-commit", commit, "--freeze-sha256", freeze_pin, "--input-sha256", input_pin,
                     "--roster-sha256", roster_pin, "--distributions-sha256", dist_pin],
                    capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, timeout=600)

            git("init", "-q")
            git("add", ".")
            git("commit", "-qm", "synthetic freeze")
            freeze = git("rev-parse", "HEAD")
            approval_text = (
                f"Approved by the lead: plan 48, validation and one scored run, freeze commit {freeze}, "
                f"freeze SHA-256 {freeze_pin}, input SHA-256 {input_pin}, roster SHA-256 {roster_pin}, "
                f"distributions SHA-256 {dist_pin}.\n")
            (root / "NOTE.md").write_text("intervening commit\n")
            git("add", "NOTE.md")
            git("commit", "-qm", "intervening")
            (root / S.APPROVAL).write_text(approval_text)
            git("add", S.APPROVAL)
            git("commit", "-qm", "approval not on the freeze")
            head = git("rev-parse", "HEAD")
            self.assertEqual(cli_at(head, "--validate-inputs").stderr.strip(), "P48_APPROVAL")
            git("reset", "-q", "--hard", freeze)
            (root / S.APPROVAL).write_text(approval_text)
            git("add", S.APPROVAL)
            git("commit", "-qm", "synthetic approval")
            head = git("rev-parse", "HEAD")

            def cli(mode):
                return cli_at(head, mode)

            v = cli("--validate-inputs")
            self.assertEqual((v.returncode, v.stderr), (0, ""))
            self.assertTrue(v.stdout.startswith("P48_INPUTS_OK turns 10 roster_rows 70"))
            self.assertFalse(any(run.iterdir()))
            g = cli("--go")
            self.assertEqual((g.returncode, g.stdout.strip(), g.stderr), (0, "P48_RESULT_WRITTEN", ""))
            self.assertEqual({p.name for p in run.iterdir()}, {"score_48.lock", "results_48.json"})
            out = json.loads((run / "results_48.json").read_bytes())
            self.assertEqual(len(out["judged"]["years"]), 10)
            self.assertEqual(set(out["shown_only"]), {"fifth_january_session_exit", "zero_cost"})
            self.assertEqual(out["job"]["freeze_commit"], freeze)
            again = cli("--go")
            self.assertEqual((again.returncode, again.stderr.strip()), (2, "P48_CONSUMED_OR_NOT_EMPTY"))
            (inputs / "roster.csv").write_bytes(roster + b"2016,SYNZ\n")
            os.chmod(inputs / "roster.csv", 0o600)
            bad = cli("--validate-inputs")
            self.assertEqual((bad.returncode, bad.stderr.strip()), (2, "P48_PIN"))


if __name__ == "__main__":
    unittest.main()
