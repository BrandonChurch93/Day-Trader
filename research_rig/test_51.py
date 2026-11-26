"""Plan 51 synthetic units and isolated CLI fixture; no real packet is resolved."""
from collections import defaultdict
from datetime import timedelta
from fractions import Fraction
from itertools import combinations
import io
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import yaml

try:
    from . import common_51 as C, score_51 as S
except ImportError:
    import common_51 as C
    import score_51 as S

P = {"hot_n": 2, "max_missing_hours": 6, "cost_bps_per_side": 15}
HOUR = C.prior.HOUR


class Engine(unittest.TestCase):
    def test_uniform_gap_compositions(self):
        class Fixed:
            def __init__(self, picks):
                self.picks = picks

            def sample(self, population, k):
                assert list(population) == list(range(4)) and k == 2
                return self.picks

        found = {tuple(S.K.uniform_gaps([2, 3], 3, Fixed(picks)))
                 for picks in combinations(range(4), 2)}
        expected = {(a, b, 3 - a - b) for a in range(3) for b in range(1, 4 - a)}
        self.assertEqual(found, expected)
        self.assertEqual(S.K.uniform_gaps([2, 3], 1, Fixed(None)), [0, 1, 0])
        self.assertEqual(S.K.uniform_gaps([], 7, Fixed(None)), [7])

    def test_calibration_release_uses_counts(self):
        p = {"calibration_trials": 100, "calibration_target_bps": 20,
             "calibration_target_days": 40, "calibration_power_floor": .5}
        rows = {key: {"passes": 0, "trials": 100, "rate": 0.0, "upper95": S.K.upper95(0, 100)}
                for key in ("iid_0bp", "volatility_blocks_0bp", "persistent_20bp_40d")}
        self.assertFalse(S.K.release(rows, p, verify_counts=True)["unlocked"])
        rows["persistent_20bp_40d"]["rate"] = 1.0
        with self.assertRaises(ValueError):
            S.K.release(rows, p, verify_counts=True)

    def test_packed_close_keeps_native_precision(self):
        bars = S.PackedSeries([0, HOUR], [1.0, 1.0],
                              [1000000000000000001, 1000000000000000002], [-18, -18])
        self.assertEqual(bars[0].c, bars[HOUR].c)
        self.assertEqual(bars.exact_close(HOUR) - bars.exact_close(0), Fraction(1, 10**18))

    def test_spells_and_gaps_are_matched(self):
        for mask in ([0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0],
                     [1, 1, 0, 1, 0, 0], [0, 0, 1, 0, 1, 1],
                     [1, 1, 1], [0, 0, 0]):
            spells, gaps = C.schedule(mask)
            rng = random.Random(51)
            samples = {tuple(C.shuffled_mask(spells, gaps, rng)) for _ in range(100)}
            for x in samples:
                s, g = C.schedule(x)
                self.assertEqual(sum(x), sum(mask))
                self.assertEqual(sorted(s), sorted(spells))
                self.assertEqual(sorted(g), sorted(gaps))
                self.assertEqual(bool(g[0]), bool(gaps[0]))
                self.assertEqual(bool(g[-1]), bool(gaps[-1]))
            if len(set(spells)) > 1:
                self.assertGreater(len(samples), 1)

    def test_lag_endpoints_and_missing(self):
        a, b = C.prior.Asset(1, "A"), C.prior.Asset(2, "B")
        s, t = 24 * HOUR, 48 * HOUR
        series = C.prior.Series
        bar = C.prior.Bar
        data = {"A": series({s-HOUR: bar(9, 9, 10), t-HOUR: bar(11, 11, 12),
                             t: bar(1, 1, 500)}),
                "B": series({s-HOUR: bar(9, 9, 10), t-HOUR: bar(9, 9, 10),
                             t: bar(500, 500, 1)})}
        self.assertAlmostEqual(C.signal_return(data, [a, b], s, t, 1), .1)
        self.assertIsNone(C.signal_return(data, [a, b], s, t + HOUR * 2, 1))
        gate = C.Gate(2)
        self.assertFalse(gate.add(.1))
        self.assertFalse(gate.add(None))
        self.assertFalse(gate.add(.1))
        self.assertTrue(gate.add(.1))
        self.assertFalse(gate.add(-.1))
        exact_zero = C.Gate(3)
        self.assertFalse(exact_zero.add(.1))
        self.assertFalse(exact_zero.add(.2))
        self.assertFalse(exact_zero.add(-.3))
        self.assertTrue(exact_zero.add(.1000000000000001))

    def test_retained_sleeve_trades_only_once(self):
        a, b, c = [C.prior.Asset(i, x) for i, x in enumerate("ABC", 1)]
        step = C.prior.DAY
        end = 2 * step
        make = lambda xs: C.prior.Series({i * step: C.prior.Bar(v, v, v) for i, v in enumerate(xs)})
        data = {"A": make((100, 150, 200)), "B": make((100, 100, 100)), "C": make((100, 100, 100))}
        f = C.Fills(data, P)
        result = C.portfolio(f, [(0, (a, b), 2), (step, (a, c), 2)], end)
        fee = f.fee
        one_round_trip = (1 - fee) / (1 + fee)
        self.assertAlmostEqual(result, one_round_trip + .5 * one_round_trip**2)
        self.assertNotIn((a, step), f.buys)
        self.assertNotIn((a, step, end), f.sells)

    def test_missing_sale_proceeds_not_reused(self):
        a, b = C.prior.Asset(1, "A"), C.prior.Asset(2, "B")
        step = C.prior.DAY
        bar = C.prior.Bar(100, 100, 100)
        f = C.Fills({"A": C.prior.Series({0: bar, step + HOUR: bar}),
                     "B": C.prior.Series({step: bar, 2 * step: bar})}, P)
        self.assertAlmostEqual(C.portfolio(f, [(0, (a,), 1), (step, (b,), 1)], 2 * step),
                               (1 - f.fee) / (1 + f.fee))
        self.assertNotIn((b, step), f.buys)
        self.assertEqual(f.sell(a, step, step)[0], None)

    def test_ties_count_against_the_rule(self):
        p = {"twin_p_max": .1 / 9, "min_positive_years": 4}
        result = C.metrics(.25, [1.25] * 11 + [1] * 989, .1, 4, p)
        self.assertTrue(result["marks"]["above_twin_p90"])
        self.assertFalse(result["marks"]["family_tail_guard"])
        self.assertEqual(result["twin_p_rank"], 12 / 1001)


IDENTITY = {"GIT_AUTHOR_NAME": "Brandon Church", "GIT_AUTHOR_EMAIL": "modernsoftworks@gmail.com",
            "GIT_COMMITTER_NAME": "Brandon Church", "GIT_COMMITTER_EMAIL": "modernsoftworks@gmail.com"}
TRAILER = "Co-authored-by: Perplexity <noreply@perplexity.ai>"


def fixture(repo, inputs):
    for rel in S.BOUND:
        out = repo / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(S.ROOT / rel, out)
    (repo / ".synthetic-only").write_text("SYNTHETIC ONLY\n")
    plan = repo / S.PLAN
    lines = ["Status: FROZEN" if line.startswith("Status: ") else line
             for line in plan.read_text().splitlines()]
    plan.write_text("\n".join(lines) + "\n")
    config = repo / S.CONFIG
    full = yaml.safe_load(config.read_text())
    p, p13 = (full[k]["value"] for k in ("replay_51_plan", "replay_13_plan"))
    p.update(years=[2020], judged_stop="2020-01-16", shown_stop="2020-01-21")
    config.write_text(yaml.safe_dump({"replay_51_plan": {"value": p}, "replay_13_plan": {"value": p13}}))
    rows = {key: {"passes": passes, "trials": 100, "rate": passes / 100,
                  "upper95": S.K.upper95(passes, 100)}
            for key, passes in (("iid_0bp", 0), ("volatility_blocks_0bp", 0),
                                ("persistent_20bp_40d", 100))}
    (repo / S.CALIBRATION).write_text(json.dumps({"cli_fixture": True, "rows": rows, **S.K.release(rows, p)}))
    day = C.prior.utc(C.stamp("2019-12-01")).date()
    roster = [{"id": 100001 + i, "symbol": f"FIX{i}", "cmcRank": i + 2} for i in range(50)]
    raw = b"synthetic snapshot fixture only"
    (inputs / "cmc").mkdir()
    (inputs / "cmc/20191201.html.gz").write_bytes(raw)
    snaps = [{"date": str(day), "known_at": C.prior.stamp(day + timedelta(days=1)),
              "sha256": S.sha(raw), "top_raw": [{"id": 1, "cmcRank": 1}] + roster, "kept": roster}]
    payload = json.dumps(snaps).encode()
    (inputs / "snapshots.json").write_bytes(payload)
    mf = {"archives": {}, "errors": [], "snapshot_sha256": S.sha(payload),
          "collection_parameters": S.F.collection_parameters(p13),
          "excluded_ids": S.F.EXCLUDE, "pair_mappings": S.F.MANUAL}
    start, end = C.stamp("2019-12-01"), C.stamp("2020-01-22")
    for i, pair in enumerate(["BTCUSDT"] + [f"FIX{x}USDT" for x in range(6)]):
        by_month = defaultdict(list)
        for t in range(start, end, HOUR):
            month = C.prior.utc(t).strftime("%Y-%m")
            px = 100 * (1 + i / 100_000) ** ((t - start) // HOUR)
            by_month[month].append(f"{t * 1000},{px},{px},{px},{px}\n")
        for month, rows in by_month.items():
            key = f"data/spot/monthly/klines/{pair}/1h/{pair}-1h-{month}.zip"
            path = inputs / "archives" / key
            path.parent.mkdir(parents=True, exist_ok=True)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("fixture.csv", "".join(rows))
            blob = buf.getvalue()
            path.write_bytes(blob)
            mf["archives"][key] = {"n": len(rows), "sha256": S.sha(blob)}
    payload = json.dumps(mf).encode()
    (inputs / "manifest.json").write_bytes(payload)
    return S.sha(payload)


class CLI(unittest.TestCase):
    def test_disposable_synthetic_fixture(self):
        with tempfile.TemporaryDirectory(dir="/tmp", prefix="plan51-fixture-") as tmp:
            scratch = Path(tmp)
            repo, inputs, run = [scratch / n for n in ("repo", "input", "run")]
            for path in (repo, inputs, run):
                path.mkdir()
            manifest = fixture(repo, inputs)
            env = {**os.environ, **IDENTITY, "PYTHONDONTWRITEBYTECODE": "1"}

            def git(*args):
                return subprocess.check_output(["git", *args], cwd=repo, env=env,
                                               stderr=subprocess.DEVNULL, text=True).strip()

            def cli(*args):
                out = subprocess.run([sys.executable, str(repo / "research_rig/score_51.py"),
                                      *args], cwd=repo, env=env, capture_output=True, text=True)
                self.assertEqual(out.stderr, "")
                return out.returncode, out.stdout.strip()

            git("init", "-q")
            git("add", ".")
            git("commit", "-qm", "Synthetic freeze\n\n" + TRAILER)
            freeze = git("rev-parse", "HEAD")
            self.assertEqual(cli("--validate"), (2, "REFUSED P51_FIXTURE_MODE"))
            self.assertEqual(cli("--validate", "--synthetic-fixture"), (2, "REFUSED P51_APPROVAL_PARENT"))
            approval = repo / S.APPROVAL
            approval.write_text(f"Approved by the lead agent for Plan 51 historical counts and one lead-only score "
                                f"from freeze {freeze} with Replay 13 manifest {manifest}.\n")
            git("add", S.APPROVAL)
            git("commit", "-qm", "Synthetic approval\n\n" + TRAILER)
            raw = (inputs / "manifest.json").read_bytes()
            (inputs / "manifest.json").write_bytes(raw + b" ")
            self.assertEqual(cli("--validate", "--synthetic-fixture"), (2, "REFUSED P51_MANIFEST_HASH"))
            (inputs / "manifest.json").write_bytes(raw)
            rc, out = cli("--validate", "--synthetic-fixture")
            self.assertEqual(rc, 0, out)
            self.assertEqual(json.loads(out), {"days": 10, "in_market_days": 8,
                                               "spells_per_year": {"2020": 1},
                                               "coins_on_list_per_year": {"2020": 6}})
            self.assertEqual(list(run.iterdir()), [])
            self.assertEqual(cli("--go", "--synthetic-fixture"), (0, ""))
            scored_path, lock_path = run / "results_51.json", run / "score_51.lock"
            original, claim = scored_path.read_bytes(), lock_path.read_bytes()
            self.assertEqual(json.loads(original)["shown_only"]["days"], 5)
            self.assertEqual(json.loads(claim)["freeze"], freeze)
            self.assertEqual(cli("--go", "--synthetic-fixture"), (2, "REFUSED P51_SPENT"))
            self.assertEqual((scored_path.read_bytes(), lock_path.read_bytes()), (original, claim))


if __name__ == "__main__":
    unittest.main()
