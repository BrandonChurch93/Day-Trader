"""Synthetic-only tests, never consult the canonical Plan 35 inputs."""
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

import score_35 as S

C = S.parse((Path(__file__).resolve().parent / S.CONFIG).read_bytes())


def q(t, ap=52, bp=51, as_=1, bs=1):
    return {'t': t, 'ap': ap, 'bp': bp, 'as': as_, 'bs': bs}


class TestDesign(unittest.TestCase):
    def test_calendar_and_clock(self):
        expiry, controls = S.calendar_design(C)
        self.assertEqual((len(expiry), len(controls), len(set(expiry + controls))), (34, 108, 142))
        self.assertEqual([sum(d.year == y for d in controls) for y in (2024, 2025, 2026)], [39, 38, 31])
        self.assertEqual([str(d) for d in expiry if d.weekday() != 4], ['2024-03-28'])
        self.assertIn(date(2025, 11, 28), expiry)
        self.assertNotIn(date(2026, 7, 3), controls)
        self.assertIn(date(2024, 7, 5), controls)
        for day, prefix in [('2024-01-26', '11'), ('2024-06-28', '10'), ('2025-10-31', '11')]:
            self.assertEqual(S.london_ns(date.fromisoformat(day), 11), S.stamp_ns(f'{day}T{prefix}:00:00Z'))

    def test_select_first_eligible_exact_nano_and_tie_order(self):
        day = date(2024, 1, 26)
        good = '2024-01-26T11:00:00.000000001Z'
        payload = {'schema': 1, 'symbol': 'IBIT', 'feed': 'sip', 'windows': [
            {'date': str(day), 'hour': 11, 'quotes': [q('2024-01-26T11:00:00Z', ap=0),
                                                      q(good, ap=51, bp=51), q(good, ap=53)]},
            {'date': str(day), 'hour': 14, 'quotes': []},
            {'date': str(day), 'hour': 16, 'quotes': [q('2024-01-26T16:00:59.999999999Z')]},
        ]}
        self.assertEqual(S.quote_packet(payload, [day], C)[day, 11], (51, 51))
        payload['windows'][-1]['quotes'] = [q('2024-01-26T16:01:00Z')]
        with self.assertRaisesRegex(S.Refused, 'QUOTE_CLOCK'):
            S.quote_packet(payload, [day], C)
        payload['windows'].pop()
        with self.assertRaisesRegex(S.Refused, 'QUOTES'):
            S.quote_packet(payload, [day], C)

    def test_rejects_out_of_order_nanosecond_quotes(self):
        day = date(2024, 1, 26)
        windows = [{'date': str(day), 'hour': hour, 'quotes': []} for hour in (11, 14, 16)]
        windows[0]['quotes'] = [q('2024-01-26T11:00:00.000000011Z'), q('2024-01-26T11:00:00.000000010Z')]
        with self.assertRaisesRegex(S.Refused, 'QUOTE_CLOCK'):
            S.quote_packet({'schema': 1, 'symbol': 'IBIT', 'feed': 'sip', 'windows': windows}, [day], C)


class TestJudgment(unittest.TestCase):
    def test_paid_whole_shares_historical_fees_and_cash_denominator(self):
        day = date(2024, 5, 31)
        quotes = {(day, 11): (Decimal('61'), Decimal('60')), (day, 16): (Decimal('64'), Decimal('63'))}
        placed, missing = S.outcomes([day], quotes, C, 11)
        self.assertEqual(missing, {})
        self.assertEqual(placed[day], Decimal('15.97') / 500)
        self.assertEqual(S.outcomes([day], quotes, C, 11, 5)[0][day], Decimal('15.726') / 500)
        for when, expected in [('2024-05-21', '.02'), ('2024-05-22', '.03'), ('2025-05-14', '.01'),
                               ('2026-04-04', '.03'), ('2026-10-01', '.02')]:
            self.assertEqual(S.fee_on_sale(date.fromisoformat(when), 8, Decimal(504), C), Decimal(expected))
        quotes[day, 16] = None
        self.assertEqual(S.outcomes([day], quotes, C, 11)[1], {str(day): 'no_exit'})
        quotes[day, 11] = (Decimal(501), Decimal(500))
        self.assertEqual(S.outcomes([day], quotes, C, 11)[1], {str(day): 'unaffordable'})

    def test_synthetic_edge_and_no_edge(self):
        expiry, controls = S.calendar_design(C)
        quotes = {}
        for i, day in enumerate(sorted(expiry + controls)):
            quotes[day, 11] = (Decimal(50), Decimal(49))
            quotes[day, 14] = (Decimal(99), Decimal(98))
            bid = Decimal(51 if day in expiry else 49) + Decimal(i % 3) / 10
            quotes[day, 16] = (bid + 1, bid)
        result = S.evaluate(expiry, controls, quotes, {}, C)
        self.assertTrue(result['pass'])
        self.assertEqual(set(result['marks'].values()), {True})
        self.assertEqual(result['expiry_fridays']['placed'], 33)
        self.assertEqual(result['controls']['placed'], 108)
        self.assertLess(result['shown_only']['shorter_window']['expiry']['mean'], 0)
        for day in expiry[:5]:
            quotes[day, 11] = None
        result = S.evaluate(expiry, controls, quotes, {}, C)
        self.assertEqual(result['expiry']['placed'], 29)
        self.assertFalse(result['marks']['placed'])
        self.assertFalse(result['pass'])
        self.assertIsNone(S.t_stat([.02, .02, .02]))
        self.assertAlmostEqual(S.t_stat([1, 3], [0, 1, 1, 2]), 1 / ((2 / 2 + (2 / 3) / 4) ** .5))


class TestProtocol(unittest.TestCase):
    def test_stream_checks_digest_layout_and_window_coverage(self):
        day = date(2024, 1, 26)
        payload = S.QUOTE_HEADER + b',\n'.join(
            json.dumps({'date': str(day), 'hour': h,
                        'quotes': [q(f'{day}T{h}:00:00.000000001Z')]}).encode()
            for h in (11, 14, 16)) + b'\n]}\n'
        with TemporaryDirectory() as name:
            p = Path(name).resolve() / 'quotes.json'
            p.write_bytes(payload)
            p.chmod(0o600)
            digest = sha256(payload).hexdigest()
            self.assertEqual(S.quote_stream(p, digest, [day], C)[day, 11], (52, 51))
            with self.assertRaisesRegex(S.Refused, 'PIN'):
                S.quote_stream(p, '0' * 64, [day], C)
            corrupt = payload[:-3] + b']}\n\n'
            p.write_bytes(corrupt)
            with self.assertRaisesRegex(S.Refused, 'QUOTE_LAYOUT'):
                S.quote_stream(p, sha256(corrupt).hexdigest(), [day], C)
            with patch.object(S, 'WINDOW_CAP', 75), self.assertRaisesRegex(S.Refused, 'QUOTE_LAYOUT'):
                S.quote_stream(p, sha256(corrupt).hexdigest(), [day], C)

    def test_approval_commit_gate_in_invented_git_repo(self):
        with TemporaryDirectory() as name:
            repo = Path(name).resolve()
            folder = repo / 'research_rig'
            folder.mkdir()
            docs = repo / 'docs'
            docs.mkdir()
            def g(*args):
                return subprocess.check_output(['/usr/bin/git', '-C', str(repo), *args], stderr=subprocess.DEVNULL,
                                               env={'PATH': '/usr/bin:/bin', 'GIT_CONFIG_GLOBAL': '/dev/null',
                                                    'GIT_CONFIG_NOSYSTEM': '1', 'LC_ALL': 'C'}).decode().strip()
            def commit(message):
                g('add', '.')
                g('-c', 'user.name=Synthetic Owner', '-c', 'user.email=synthetic@example.invalid',
                  '-c', 'commit.gpgsign=false', 'commit', '-qm', message)
                return g('rev-parse', 'HEAD')
            g('init', '-q')
            for filename in S.PIN_NAMES:
                if filename == S.PLAN:
                    raw = b'Status FROZEN.\n'
                elif filename == S.CONFIG:
                    raw = S.encode(C)
                else:
                    raw = b'# invented fixture\n'
                (folder / filename).write_bytes(raw)
            (folder / 'TRIAL_LEDGER.md').write_text(f'| 170 | {S.PLAN} |\n')
            (docs / 'QUEUE.md').write_text(f'| 57 | {S.PLAN} |\n')
            pins = S.encode({f: sha256((folder / f).read_bytes()).hexdigest() for f in S.PIN_NAMES})
            (folder / S.PINS).write_bytes(pins)
            freeze, freeze_pin, input_pin = commit('freeze'), sha256(pins).hexdigest(), '7' * 64
            with patch.object(S, 'HERE', folder), patch.object(S, 'REPO', repo):
                with self.assertRaisesRegex(S.Refused, 'APPROVAL'):
                    S.authorize(freeze, freeze_pin, input_pin)
                (folder / S.APPROVAL).write_text(
                    f'Approved by the lead: plan 35, validation and one scored run, freeze commit {freeze}, '
                    f'freeze SHA-256 {freeze_pin}, input SHA-256 {input_pin}.\n')
                approval = commit('approval')
                self.assertEqual(S.authorize(approval, freeze_pin, input_pin), (freeze, C))
                with self.assertRaisesRegex(S.Refused, 'APPROVAL'):
                    S.authorize(approval, freeze_pin, '8' * 64)
                (folder / S.CONFIG).write_bytes(b'{}')
                with self.assertRaisesRegex(S.Refused, 'CLEAN'):
                    S.authorize(approval, freeze_pin, input_pin)

    def test_private_digest_and_link_denial(self):
        with TemporaryDirectory() as name:
            p = Path(name).resolve() / 'x'
            p.write_bytes(b'invented')
            p.chmod(0o600)
            pin = sha256(b'invented').hexdigest()
            self.assertEqual(S.pinned(p, pin, 100, True), b'invented')
            with self.assertRaisesRegex(S.Refused, 'PIN'):
                S.pinned(p, '0' * 64, 100, True)
            symlink = p.parent / 'y'
            symlink.symlink_to(p)
            with self.assertRaisesRegex(S.Refused, 'PIN'):
                S.pinned(symlink, pin, 100, True)

    def test_validate_main_never_evaluates_or_claims(self):
        cli = ['score_35.py', '--validate-inputs', '--approval-commit', '1' * 40,
               '--freeze-sha256', '2' * 64, '--input-sha256', '3' * 64]
        out = StringIO()
        with (patch.object(S.sys, 'argv', cli), patch.object(S, 'check_environment'),
              patch.object(S, 'set_limits'), patch.object(S.os, 'umask'), patch.object(S, 'reset_tzpath'),
              patch.object(S, 'authorize', return_value=('4' * 40, C)), patch.object(S, 'private_dir'),
              patch.object(S, 'unused'), patch.object(S, 'load_inputs', return_value=([], [], {}, {}, C)),
              patch.object(S, 'evaluate') as eval_, patch.object(S, 'once') as once_, redirect_stdout(out)):
            S.main()
        self.assertIn('P35_INPUTS_OK', out.getvalue())
        eval_.assert_not_called()
        once_.assert_not_called()

    def test_lock_consumed_even_after_evaluation_error(self):
        with TemporaryDirectory() as name:
            folder = Path(name)
            with patch.object(S, 'evaluate', side_effect=ValueError('invented failure')):
                with self.assertRaises(ValueError):
                    S.once(folder, {}, ())
            self.assertTrue((folder / 'score_35.lock').is_file())
            self.assertFalse((folder / 'results_35.json').exists())
            with self.assertRaisesRegex(S.Refused, 'CONSUMED'):
                S.once(folder, {}, ())


if __name__ == '__main__':
    unittest.main()
