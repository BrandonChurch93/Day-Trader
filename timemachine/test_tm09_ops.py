"""Made-up checks for the TM09 host ceremony helpers, the host shell wiring and the engine review.

Invented log lines, nonces, sessions and files only. No sudo, no host paths are written, no listener is bound."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from timemachine.tm09_ops import (Refused, check_probe, clean, h, launch_body, parse_role, record_target, required_canaries,
                                  resolve, review_body, sealed, slot_dir, sudo_review, unseal, write_owned)

REPO = Path(__file__).resolve().parents[1]
HOST = REPO / 'timemachine' / 'tm09_ops_host.sh'
OWN = 'a' * 32
OTHER = 'b' * 32
STRAY = 'c' * 32
SID = 'TM09-' + 'd' * 32
SIB = 'TM09-' + 'e' * 32
KEY = 'made-up unittest-only signing material for ops'
BINS = {'/usr/bin/kill', '/usr/bin/install', '/usr/bin/true', '/bin/kill'}


def is_file(p):
    return p in BINS


def line(t, cmd, who='user', target='root'):
    return f'Nov 26 {t} : {who} : PWD=/tmp ; USER={target} ; COMMAND={cmd}\n'


RECORDS = [{'time': '17:50:00', 'argv': ['-u', 'tm09desk', 'kill', '-TERM', '4376']},
           {'time': '17:50:01', 'argv': ['install', '-o', 'tm09desk', '-m', '0600', '/tmp/a', '/var/lib/tm09/ops/a']}]


def checkpoint(prefix=b'', canary_lines=None):
    """An invented log up to and including this launch's canary, and the matching proof fields."""
    seg = ''.join(canary_lines if canary_lines is not None else [line('17:49:58', '/usr/bin/true tm09-' + OWN)]).encode()
    log = prefix + seg
    proof = dict(size_before=len(prefix), size_after=len(log), prefix_sha256=h(log), log_id=[1, 2], sha256='f' * 64)
    return log, proof


class SudoReview(unittest.TestCase):
    def review(self, later, on_file=frozenset(), prefix=b'Nov 26 17:00:00 : user : PWD=/ ; USER=root ; COMMAND=/usr/bin/id\n'):
        log, proof = checkpoint(prefix)
        return sudo_review(log + ''.join(later).encode(), (1, 2), proof, RECORDS, OWN, set(on_file), is_file)

    def test_operator_records_and_own_canary_are_listed(self):
        r = self.review([line('17:50:01', '/usr/bin/kill -TERM 4376', target='tm09desk'),
                         line('17:50:02', '/usr/bin/install -o tm09desk -m 0600 /tmp/a /var/lib/tm09/ops/a')])
        self.assertEqual((r['entries'], len(r['listed']), r['unlisted'], r['own_canary']), (3, 3, [], 1))
        self.assertTrue(clean(r))

    def test_lines_before_the_checkpoint_are_not_reviewed(self):
        self.assertEqual(self.review([])['entries'], 1)

    def test_truncated_log_refuses(self):
        log, proof = checkpoint(b'x' * 50)
        with self.assertRaises(Refused):
            sudo_review(log[:40], (1, 2), proof, RECORDS, OWN, set(), is_file)
        with self.assertRaises(Refused):
            sudo_review(b'', (1, 2), proof, RECORDS, OWN, set(), is_file)

    def test_changed_prefix_refuses(self):
        log, proof = checkpoint(b'y' * 50)
        with self.assertRaises(Refused):
            sudo_review(b'z' + log[1:], (1, 2), proof, RECORDS, OWN, set(), is_file)

    def test_rotated_log_refuses(self):
        log, proof = checkpoint(b'y' * 50)
        with self.assertRaises(Refused):
            sudo_review(log, (1, 3), proof, RECORDS, OWN, set(), is_file)

    def test_missing_or_doubled_own_canary_in_checkpoint_refuses(self):
        for seg in ([], [line('17:49:58', '/usr/bin/true tm09-' + STRAY)], [line('17:49:58', '/usr/bin/true tm09-' + OWN)] * 2,
                    [line('17:49:58', '/usr/bin/true tm09-' + OWN, target='tm09desk')]):
            log, proof = checkpoint(b'p' * 10, seg)
            with self.assertRaises(Refused):
                sudo_review(log, (1, 2), proof, RECORDS, OWN, set(), is_file)

    def test_repeated_own_canary_after_checkpoint_is_unlisted(self):
        r = self.review([line('17:50:03', '/usr/bin/true tm09-' + OWN)])
        self.assertEqual((r['own_canary'], len(r['unlisted'])), (2, 1))
        self.assertFalse(clean(r))

    def test_other_canary_needs_a_proof_and_counts_once(self):
        r = self.review([line('17:49:34', '/usr/bin/true tm09-' + OTHER), line('17:49:46', '/usr/bin/true tm09-' + STRAY),
                         line('17:49:47', '/usr/bin/true tm09-' + OTHER)], {OTHER})
        self.assertEqual(len(r['unlisted']), 2)
        self.assertEqual(sum(1 for x in r['listed'] if x.get('canary') == 'other'), 1)

    def test_time_command_invoker_target_and_full_path_must_match(self):
        bad = [line('17:50:05', '/usr/bin/kill -TERM 4376', target='tm09desk'),      # too late
               line('17:50:01', '/usr/bin/kill -KILL 4376', target='tm09desk'),      # other arguments
               line('17:50:00', '/usr/bin/kill -TERM 4376', who='tm09desk', target='tm09desk'),  # other invoker
               line('17:50:00', '/usr/bin/kill -TERM 4376', target='root'),          # other run-as account
               line('17:50:00', '/tmp/kill -TERM 4376', target='tm09desk')]          # other executable, same basename
        for b in bad:
            r = self.review([b])
            self.assertEqual(len(r['unlisted']), 1, b)

    def test_one_record_covers_one_line(self):
        r = self.review([line('17:50:00', '/usr/bin/kill -TERM 4376', target='tm09desk')] * 2)
        self.assertEqual(len(r['unlisted']), 1)

    def test_record_target_and_resolution(self):
        self.assertEqual(record_target(['-u', 'tm09desk', 'kill', 'x']), ('tm09desk', ['kill', 'x']))
        self.assertEqual(record_target(['-n', '/usr/bin/true', 'x']), ('root', ['/usr/bin/true', 'x']))
        self.assertEqual(resolve('kill', is_file), '/usr/bin/kill')
        self.assertIsNone(resolve('./kill', is_file))
        self.assertIsNone(resolve('nothing', is_file))


class Evidence(unittest.TestCase):
    def test_host_seal_detects_fake_or_edited_evidence(self):
        raw = json.dumps(sealed(KEY, 'canary', dict(nonce=OWN, size_before=1))).encode()
        self.assertEqual(unseal(KEY, 'canary', raw)['nonce'], OWN)
        for bad in (json.dumps(dict(json.loads(raw), size_before=2)).encode(), json.dumps(dict(nonce=OWN)).encode(),
                    json.dumps(sealed('another made-up key of enough length!!', 'canary', dict(nonce=OWN))).encode()):
            with self.assertRaises(Refused):
                unseal(KEY, 'canary', bad)
        with self.assertRaises(Refused):
            unseal(KEY, 'probe', raw)  # a canary proof is not a probe proof

    def test_repeated_proof_file_is_refused(self):
        with TemporaryDirectory() as d:
            p = Path(d) / 'x-proof.json'
            write_owned(p, b'{}', chown=False)
            self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                write_owned(p, b'{}', chown=False)

    def test_probe_scope(self):
        can = ['/var/lib/tm09/operator.key', '/var/lib/tm09/canaries/tape', '/var/lib/tm09/canaries/notes', '/var/lib/tm09/canaries/results']
        good = dict(phase='stopped', session=SID, port=8801, worker='user', canaries=can, denied_count=4)
        check_probe(good, SID, 8801, 'stopped', can)
        for bad in (dict(good, denied_count=1), dict(good, phase='live'), dict(good, session=SIB), dict(good, port=8802),
                    dict(good, worker='tm09desk'), dict(good, canaries=can[:1], denied_count=1)):
            with self.assertRaises(Refused):
                check_probe(bad, SID, 8801, 'stopped', can)

    def test_required_canaries(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(Refused):
                required_canaries('rehearsal', root=root)
            (root / 'canaries').mkdir()
            for n in ('operator.key', 'canaries/tape', 'canaries/notes', 'canaries/results'):
                (root / n).write_text('x')
            self.assertEqual(len(required_canaries('rehearsal', root=root)), 4)
            with self.assertRaises(Refused):
                required_canaries('production', root=root)
            (root / 'export').mkdir()
            (root / 'export' / 'stock_bars.jsonl').write_text('x')
            self.assertEqual(len(required_canaries('production', root / 'export', root=root)), 5)

    def test_launch_body(self):
        proof = dict(session=SID, port=8801, nonce=OWN, matched_canary=True, prefix_unchanged=True, size_before=10, size_after=20)
        self.assertTrue(launch_body(SID, 8801, proof, b'{}')['canary_observed'])
        for kw in (dict(matched_canary=False), dict(prefix_unchanged=False), dict(size_after=10), dict(port=8802), dict(nonce='x')):
            with self.assertRaises(Refused):
                launch_body(SID, 8801, dict(proof, **kw), b'{}')


class ReviewSigner(unittest.TestCase):
    CONTROL = {'body': {'session': SID, 'nonce': OWN, 'port': 8801}, 'seal': 'e' * 64}

    def review(self, later, on_file=frozenset()):
        log, proof = checkpoint()
        r = sudo_review(log + ''.join(later).encode(), (1, 2), proof, RECORDS, OWN, set(on_file), is_file)
        r['session'] = SID
        return r, json.dumps(r).encode()

    def test_unlisted_line_refuses_to_sign(self):
        # The rehearsal failure: a sibling launch canary with no proof on file, and the old signer signed anyway.
        r, raw = self.review([line('17:49:34', '/usr/bin/true tm09-' + OTHER)])
        self.assertEqual(len(r['unlisted']), 1)
        with self.assertRaises(Refused):
            review_body(r, SID, 8801, OWN, self.CONTROL, b'{}', raw)

    def test_foreign_or_edited_review_refuses(self):
        r, raw = self.review([])
        for bad in (dict(r, entries=2), dict(r, session=SIB), dict(r, nonce=OTHER), dict(r, own_canary=0), dict(r, unlisted=['x'])):
            with self.assertRaises(Refused):
                review_body(bad, SID, 8801, OWN, self.CONTROL, b'{}', raw)
        with self.assertRaises(Refused):
            review_body(r, SID, 8802, OWN, self.CONTROL, b'{}', raw)

    def test_clean_review_signs_all_flags(self):
        r, raw = self.review([line('17:49:34', '/usr/bin/true tm09-' + OTHER)], {OTHER})
        body = review_body(r, SID, 8801, OWN, self.CONTROL, b'{"phase":"stopped"}', raw)
        self.assertTrue(body['sudo_allowlist_reviewed'] and body['listener_stopped'] and body['raw_copies_denied'])
        self.assertEqual((body['session'], body['nonce'], body['port'], body['sudo_review_sha256']), (SID, OWN, 8801, h(raw)))


class Roles(unittest.TestCase):
    def test_role_args_and_desk_paths(self):
        self.assertEqual(parse_role('boss claude_fable_5_2 N'), ('boss', 'claude_fable_5_2', 'N'))
        self.assertEqual(str(slot_dir('rehearsal', '2026-09-07', 'price_scout')), '/var/lib/tm09/invented-rehearsal/TM09-2026-09-07-price_scout')
        self.assertEqual(str(slot_dir('production', '2026-09-07', 'boss m P1')), '/var/lib/tm09/TM09-2026-09-07-m-P1')
        for bad in ('--role price_scout', 'boss m', 'boss m X', 'scout'):
            with self.assertRaises(Refused):
                parse_role(bad)
        with self.assertRaises(Refused):
            slot_dir('', '2026-09-07', 'price_scout')


STUB = r'''#!/bin/bash
# made-up osudo: record argv, emulate outputs, never escalate
printf '%s\n' "$*" >> "$STUB_DIR/calls"
case "$*" in
  *canary-launch*) echo "/var/lib/tm09/ops/$SID-$NONCE-proof.json"; echo "$SID-$NONCE-launch.json abc" ;;
  *"timemachine.tm09_operator"*" launch "*) echo "Registered desk ready; brief only this session's roles."; sleep 1 ;;
  *"kill -TERM"*) touch "$STUB_DIR/killed" ;;
  *" probe "*) [ -e "$STUB_DIR/probe_fails" ] && exit 1; echo probe ok ;;
esac
exit 0
'''
PGREP = '#!/bin/bash\n[ -e "$STUB_DIR/killed" ] && exit 1\necho 4242\n'


class HostShell(unittest.TestCase):
    def run_host(self, *args, mode='rehearsal', extra=None):
        d = Path(self.tmp.name)
        env = dict(PATH='/usr/bin:/bin', STUB_DIR=str(d), SID=SID, NONCE=OWN, OSUDO=str(d / 'osudo'), PGREP=str(d / 'pgrep'),
                   TM09_RELEASE=str(REPO), TM09_OPS_PY=str(REPO / 'timemachine/tm09_ops.py'), TM09_LOGS=str(d / 'logs'),
                   TM09_WEEK='2026-09-07', OPLOG='/dev/null')
        if mode is not None:
            env['TM09_MODE'] = mode
        env.update(extra or {})
        r = subprocess.run(['bash', str(HOST)] + list(args), env=env, capture_output=True, text=True, timeout=60)
        calls = (d / 'calls').read_text().splitlines() if (d / 'calls').exists() else []
        return r, calls

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = Path(self.tmp.name)
        for name, body in (('osudo', STUB), ('pgrep', PGREP)):
            (d / name).write_text(body)
            (d / name).chmod(0o700)

    def test_unset_or_empty_or_unknown_mode_refuses(self):
        for mode in (None, '', 'study', '--rehearsal'):
            r, calls = self.run_host('launch', 'price_scout', SID, '8801', SIB, '/tmp/b.json', mode=mode)
            self.assertEqual((r.returncode, calls), (2, []), mode)

    def test_production_needs_approval_and_news_export(self):
        r, calls = self.run_host('launch', 'price_scout', SID, '8801', SIB, '/tmp/b.json', mode='production')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(calls, [])
        r, calls = self.run_host('launch', 'news_scout', SID, '8802', SIB, '/tmp/b.json', mode='production',
                                 extra=dict(TM09_APPROVAL='/var/lib/tm09/ops/run.json'))
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(calls, [])

    def test_bad_role_args_refuse(self):
        for role in ('--role price_scout', 'boss m', 'scout'):
            r, calls = self.run_host('launch', role, SID, '8801', SIB, '/tmp/b.json')
            self.assertEqual((r.returncode, calls), (2, []), role)

    def test_launch_wiring(self):
        r, calls = self.run_host('launch', 'boss claude_fable_5_2 N', SID, '8803', SIB, '/tmp/b.json')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('ready, live probe passed', r.stdout)
        self.assertIn(f'canary-launch {SID} 8803', calls[0])
        self.assertNotIn('-u', calls[0].split()[:1])                     # canary runs as root
        serve = next(c for c in calls if 'tm09_operator' in c)
        self.assertTrue(serve.startswith('-u tm09desk sh -c '))             # engine runs as the service account
        self.assertIn(f'launch --role boss --boss claude_fable_5_2 --arm N --port 8803 --boundary /var/lib/tm09/ops/{SID}-{OWN}-launch.json '
                      f'--canary-proof /var/lib/tm09/ops/{SID}-{OWN}-proof.json --rehearsal --root /var/lib/tm09', serve)
        self.assertIn('--week 2026-09-07', serve)
        self.assertIn(f'probe rehearsal live {SID} 8803 {OWN} {SIB} /tmp/b.json', calls[-1])

    def test_failed_live_probe_stops_the_listener(self):
        (Path(self.tmp.name) / 'probe_fails').touch()
        r, calls = self.run_host('launch', 'price_scout', SID, '8801', SIB, '/tmp/b.json')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('kill -TERM 4242', calls[-1])

    def test_production_news_launch_passes_export_dir(self):
        r, calls = self.run_host('launch', 'news_scout', SID, '8802', SIB, '/tmp/b.json', mode='production',
                                 extra=dict(TM09_APPROVAL='/var/lib/tm09/ops/run.json', TM09_EXPORT_DIR='/var/lib/tm09/export'))
        self.assertEqual(r.returncode, 0, r.stderr)
        serve = next(c for c in calls if 'tm09_operator' in c)
        self.assertIn('launch --role news_scout --export-dir /var/lib/tm09/export --port 8802', serve)
        self.assertNotIn('--rehearsal', serve)
        self.assertIn('--approval /var/lib/tm09/ops/run.json', serve)
        self.assertTrue(calls[-1].endswith('/var/lib/tm09/export'))

    def test_stop_review_wiring(self):
        r, calls = self.run_host('stop-review', 'boss m P1', SID, '8804', OWN, SIB, '/tmp/b.json')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(calls[0], 'kill -TERM 4242')
        self.assertIn(f'probe rehearsal stopped {SID} 8804 {OWN} {SIB} /tmp/b.json', calls[1])
        self.assertIn(f'review-boundary rehearsal {SID} 8804 {OWN} /var/lib/tm09/invented-rehearsal/TM09-2026-09-07-m-P1 /dev/null', calls[2])
        self.assertIn(f'review --role boss --boss m --arm P1 --boundary /var/lib/tm09/ops/{SID}-{OWN}-review.json '
                      f'--probe-proof /var/lib/tm09/ops/{SID}-{OWN}-stopped-probe.json --rehearsal', calls[3])


class EngineReview(unittest.TestCase):
    """Each refusal branch of tm09_operator.review, on an invented desk."""

    def setUp(self):
        from timemachine.test_tm09 import KEY as EKEY, inputs
        from timemachine.tm09_desk import initialize, seal, store_new
        from timemachine.tm09_fixture import compile_weeks
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        opts, sessions, bars, news = inputs()
        f = compile_weeks(opts, sessions, bars, news)['2026-09-07']
        self.desk, _ = initialize(self.root, f, opts, 'price_scout', EKEY)
        self.key, self.seal, self.store = EKEY, seal, store_new
        self.control = dict(session=self.desk.public_id, nonce=OWN, port=8801, boundary_sha256='1' * 64,
                            sudo_checkpoint_sha256='2' * 64, journal_start_row=self.desk.access_checkpoint())
        self.n = 0

    def attempt(self, control=None, stop=None, boundary=None, probe=None, stop_seal_domain='tm09-stop'):
        from timemachine.tm09_fixture import fingerprint
        from timemachine.tm09_operator import review
        self.n += 1
        nonce = ('%032x' % self.n)
        c = dict(control or self.control, nonce=nonce)
        cap = {'body': c, 'seal': self.seal(self.key, 'tm09-control', c)}
        self.store(self.desk.path / f'{nonce}-control.json', cap)
        s = dict(stop or dict(c, journal_stop_row=self.desk.access_checkpoint()), nonce=nonce)
        self.store(self.desk.path / f'{nonce}-stop.json', {'body': s, 'seal': self.seal(self.key, stop_seal_domain, s)})
        pr = json.dumps(dict(dict(phase='stopped', session=self.desk.public_id, port=8801, denied_count=4), **(probe or {}))).encode()
        pp = self.root / f'probe-{nonce}.json'
        pp.write_bytes(pr)
        pp.chmod(0o600)
        b = dict(dict(session=self.desk.public_id, port=8801, nonce=nonce, control_sha256=fingerprint(cap),
                      post_stop_probe_sha256=h(pr), sudo_review_sha256='3' * 64, sudo_allowlist_reviewed=True,
                      raw_copies_denied=True, listener_stopped=True), **(boundary or {}))
        bp = self.root / f'boundary-{nonce}.json'
        self.store(bp, {'body': b, 'seal': self.seal(self.key, 'ledger-222-tm09-review', b)})
        review(self.desk, self.key, bp, pp)

    def test_clean_review_passes(self):
        self.attempt()

    def test_each_refusal_branch(self):
        cases = [dict(boundary=dict(control_sha256='0' * 64)), dict(boundary=dict(port=8802)),
                 dict(boundary=dict(sudo_allowlist_reviewed=False)), dict(boundary=dict(raw_copies_denied=False)),
                 dict(boundary=dict(listener_stopped=False)), dict(boundary=dict(post_stop_probe_sha256='0' * 64)),
                 dict(boundary=dict(sudo_review_sha256='x')), dict(boundary=dict(session='TM09-' + '9' * 32)),
                 dict(probe=dict(phase='live')), dict(probe=dict(session=SIB)), dict(probe=dict(port=8802)),
                 dict(probe=dict(denied_count='4')), dict(probe=dict(denied_count=0)),
                 dict(stop=dict(self.control, port=8805, journal_stop_row=0)), dict(stop_seal_domain='tm09-control')]
        for kw in cases:
            with self.assertRaises((ValueError, KeyError), msg=str(kw)):
                self.attempt(**kw)

    def test_engine_accepts_a_one_canary_probe(self):
        # Witness for the auditor: the engine only requires denied_count >= 1. The host signer requires the full
        # scope (Evidence.test_probe_scope); tightening the engine is the engine owner's change.
        self.attempt(probe=dict(denied_count=1))


if __name__ == '__main__':
    unittest.main()
