"""Made-up checks for the TM09 ops route (tm09_ops_sudo.py, tm09_opmatch.py, tm09_launch.sh, tm09_review.sh).

Invented log lines, nonces, sessions and files only. No sudo, no host path is written and no listener is bound."""
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from timemachine import tm09_ops_sudo as ops
from timemachine import tm09_opmatch as om

REPO = Path(__file__).resolve().parents[1]
TM = REPO / 'timemachine'
N1, N2, N3 = 'a' * 32, 'b' * 32, 'c' * 32
SID, SIB = 'TM09-' + 'd' * 32, 'TM09-' + 'e' * 32
BINS = {'/usr/bin/kill', '/usr/bin/install', '/usr/bin/true', '/usr/bin/env', '/usr/bin/cat'}


def is_file(p):
    return p in BINS


def line(t, cmd, who='user', target='root'):
    return f'Nov 26 {t} : {who} : PWD=/tmp ; USER={target} ; COMMAND={cmd}\n'


class Log(unittest.TestCase):
    """The TM07 log functions, with the log owner as a parameter so a made-up log can stand in."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / 'sudo.log'
        self.log.write_text(line('17:00:00', '/usr/bin/id'))
        self.log.chmod(0o600)
        for name, value in (('SUDO_LOG', self.log), ('LOG_UID', os.getuid())):
            p = mock.patch.object(ops, name, value)
            p.start()
            self.addCleanup(p.stop)

    def add(self, text):
        with open(self.log, 'a') as f:
            f.write(text)

    def checkpoint(self, *canaries):
        before = ops.log_snapshot()
        self.add(''.join(canaries))
        return dict(ops.log_snapshot(prefix=before, canary=N1), before_size=before['size'], canary=N1)

    def test_one_own_canary_checkpoints(self):
        cp = self.checkpoint(line('17:49:58', '/usr/bin/true tm09-' + N1))
        self.assertTrue(ops.valid_log_checkpoint(cp, N1))

    def test_missing_doubled_or_other_canary_refuses(self):
        for seg in ([], [line('17:49:58', '/usr/bin/true tm09-' + N1)] * 2, [line('17:49:58', '/usr/bin/true tm09-' + N2)],
                    [line('17:49:58', '/usr/bin/true tm07-' + N1)], [line('17:49:58', '/usr/bin/true tm09-' + N1, target='tm09desk')]):
            self.log.write_text(line('17:00:00', '/usr/bin/id'))
            with self.assertRaises(ValueError, msg=seg):
                self.checkpoint(*seg)

    def test_shrunk_changed_or_rotated_log_refuses(self):
        cp = self.checkpoint(line('17:49:58', '/usr/bin/true tm09-' + N1))
        self.add(line('17:50:00', '/usr/bin/kill -TERM 1', target='tm09desk'))
        now, entries = ops.log_entries_after(cp)
        self.assertEqual(len(entries), 1)
        raw = self.log.read_bytes()
        for bad in (raw[:cp['size'] - 5], b'', b'X' + raw[1:]):
            self.log.write_bytes(bad)
            with self.assertRaises(ValueError):
                ops.log_entries_after(cp)
        rotated = Path(self.tmp.name) / 'new.log'
        rotated.write_bytes(raw)
        rotated.chmod(0o600)
        os.replace(rotated, self.log)
        with self.assertRaises(ValueError):
            ops.log_snapshot(prefix=now)

    def test_review_needs_time_command_and_run_as_account(self):
        entries = [line('17:50:00', '/usr/bin/kill -TERM 1', target='tm09desk')]
        self.assertFalse(ops.sudo_review(entries, [{'time': '17:50:00', 'command': '/usr/bin/kill -TERM 1', 'user': 'tm09desk'}])['void'])
        self.assertTrue(ops.sudo_review(entries, [{'time': '17:50:00', 'command': '/usr/bin/kill -TERM 1'}])['void'])
        self.assertTrue(ops.sudo_review(entries, [{'time': '17:50:01', 'command': '/usr/bin/kill -TERM 1', 'user': 'tm09desk'}])['void'])


class OperatorMatch(unittest.TestCase):
    CHECK = ['env', '-i', 'PATH=/usr/bin:/bin', 'TM09_RELEASE=/opt/r', '/usr/bin/python3.14', '-B', '/opt/r/timemachine/tm09_ops_sudo.py']

    def m(self, lines, recs, canaries=None):
        return om.match(lines, recs, canaries or {}, is_file=is_file)

    def test_exact_argv_full_path_and_run_as(self):
        rec = [{'time': '17:50:00', 'argv': ['-u', 'tm09desk', 'kill', '-TERM', '4376']}]
        self.assertEqual(len(self.m([line('17:50:01', '/usr/bin/kill -TERM 4376', target='tm09desk')], rec)[0]), 1)
        for bad in (line('17:50:01', '/usr/bin/kill -TERM 4376'),                       # other run-as account
                    line('17:50:01', '/tmp/kill -TERM 4376', target='tm09desk'),        # same basename, other path
                    line('17:50:01', '/usr/bin/kill -TERM  4376', target='tm09desk'),   # whitespace differs
                    line('17:50:01', '/usr/bin/kill -KILL 4376', target='tm09desk'),
                    line('17:50:04', '/usr/bin/kill -TERM 4376', target='tm09desk'),
                    line('17:50:01', '/usr/bin/kill -TERM 4376', who='tm09desk', target='tm09desk')):
            self.assertEqual(len(self.m([bad], rec)[1]), 1, bad)

    def test_quoted_or_escaped_arguments_never_match(self):
        rec = [{'time': '17:50:00', 'argv': ['cat', "/tmp/a b"]}, {'time': '17:50:00', 'argv': ['cat', '/tmp/"ab"']}]
        for cmd in ('/usr/bin/cat /tmp/a b', '/usr/bin/cat /tmp/ab', '/usr/bin/cat /tmp/"ab"'):
            self.assertEqual(len(self.m([line('17:50:00', cmd)], rec)[1]), 1, cmd)

    def test_one_record_one_line(self):
        rec = [{'time': '17:50:00', 'argv': ['cat', '/tmp/a']}]
        self.assertEqual(len(self.m([line('17:50:00', '/usr/bin/cat /tmp/a')] * 2, rec)[1]), 1)

    def test_canary_bound_to_its_checkpoint_record_once(self):
        rec = [{'time': '17:49:56', 'argv': self.CHECK + ['checkpoint', SIB, '8802']}]
        good = line('17:49:58', '/usr/bin/true tm09-' + N2)
        self.assertEqual(len(self.m([good], rec, {N2: SIB})[0]), 1)
        self.assertEqual(len(self.m([good, good], rec, {N2: SIB})[1]), 1)                   # repeated
        self.assertEqual(len(self.m([good], rec, {})[1]), 1)                                 # no checkpoint on file
        self.assertEqual(len(self.m([good], rec, {N2: SID})[1]), 1)                          # checkpoint names another session
        self.assertEqual(len(self.m([line('17:50:09', '/usr/bin/true tm09-' + N2)], rec, {N2: SIB})[1]), 1)  # too late
        self.assertEqual(len(self.m([line('17:49:58', '/usr/bin/true tm09-' + N2, target='tm09desk')], rec, {N2: SIB})[1]), 1)

    def test_operator_record_file_owner_and_mode(self):
        with TemporaryDirectory() as d:
            p = Path(d) / 'opsudo.jsonl'
            p.write_text('{"time":"17:50:00","argv":["true"]}\n')
            p.chmod(0o644)
            self.assertEqual(len(om.read_oplog(p)[1]), 1)
            p.chmod(0o666)
            with self.assertRaises(SystemExit):
                om.read_oplog(p)
            q = Path(d) / 'link'
            q.symlink_to(p)
            with self.assertRaises(OSError):
                om.read_oplog(q)


class Glue(unittest.TestCase):
    def ev(self, **kw):
        return dict(dict(phase='stopped', session=SID, port=8801, nonce=N1, launch_sha256='f' * 64, denied_count=4,
                         canaries=[str(p) for p in ops.CANARIES]), **kw)

    def test_canary_targets_are_the_engine_four_in_order(self):
        self.assertEqual([p.name for p in ops.CANARIES], ['tape', 'notes', 'operator.key', 'results'])

    def test_probe_must_be_this_launch_and_full_scope(self):
        ops.check_probe(self.ev(), SID, 8801, 'stopped', N1, 'f' * 64)
        for bad in (dict(nonce=N2), dict(launch_sha256='0' * 64), dict(denied_count=1), dict(phase='live'),
                    dict(session=SIB), dict(port=8802), dict(canaries=[str(p) for p in ops.CANARIES][::-1])):
            with self.assertRaises(ValueError, msg=bad):
                ops.check_probe(self.ev(**bad), SID, 8801, 'stopped', N1, 'f' * 64)

    def test_control_must_be_this_generation(self):
        fp = lambda b: 'h-' + json.dumps(b, sort_keys=True)
        launch = {'body': dict(session=SID, port=8801, nonce=N1)}
        control = {'body': dict(session=SID, port=8801, nonce=N1, boundary_sha256=fp(launch['body']))}
        ops.check_generation(control, launch, SID, 8801, N1, fp)
        older = {'body': dict(session=SID, port=8801, nonce=N2)}
        for c, l in ((control, older), ({'body': dict(control['body'], nonce=N2)}, launch),
                     ({'body': dict(control['body'], boundary_sha256='x')}, launch)):
            with self.assertRaises(ValueError):
                ops.check_generation(c, l, SID, 8801, N1, fp)

    def test_export_files_must_exist_non_empty_and_match(self):
        with TemporaryDirectory() as d, mock.patch.object(ops, 'ROOT', Path(d)):
            ex = Path(d) / 'export'
            ex.mkdir()
            (ex / 'stock_bars.jsonl').write_bytes(b'made-up\n')
            body = dict(export_dir=str(ex), export_sha256={'stock_bars.jsonl': ops.h(b'made-up\n')})
            self.assertEqual(ops.export_files(body, Path.read_bytes), 1)
            for bad in (dict(body, export_sha256={}), dict(body, export_dir='/tmp/elsewhere'),
                        dict(body, export_sha256={'stock_bars.jsonl': '0' * 64}),
                        dict(body, export_sha256={'missing.jsonl': ops.h(b'')})):
                with self.assertRaises(ValueError):
                    ops.export_files(bad, Path.read_bytes)

    def test_repeated_file_refuses(self):
        with TemporaryDirectory() as d:
            p = Path(d) / 'x'
            ops.put(p, b'{}', owner=None)
            with self.assertRaises(FileExistsError):
                ops.put(p, b'{}', owner=None)


STUB = r'''#!/bin/bash
printf '%s\n' "$*" >> "$STUB_DIR/calls"
case "$*" in
  *" checkpoint "*) echo "/var/lib/tm09/ops-v2/$SID-$NONCE-proof.json"; echo "$SID-$NONCE-launch.json abc" ;;
  *"timemachine.tm09_operator"*" launch "*) echo "Registered desk ready; brief only this session's roles."; sleep 1 ;;
  *"kill -TERM"*) touch "$STUB_DIR/killed" ;;
  *" probe "*) [ -e "$STUB_DIR/probe_fails" ] && exit 1; echo probe ok ;;
  *" canaries") echo '{}' ;;
  "cat "*entries.json) echo '{"sudo_entries": []}' ;;
esac
exit 0
'''
PGREP = '#!/bin/bash\n[ -e "$STUB_DIR/killed" ] && exit 1\necho 4242\n'


class Shell(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = Path(self.tmp.name)
        for name, body in (('osudo', STUB), ('pgrep', PGREP)):
            (d / name).write_text(body)
            (d / name).chmod(0o700)
        (d / 'oplog').write_text('')
        (d / 'oplog').chmod(0o600)

    def run_sh(self, script, *args, mode='rehearsal', extra=None):
        d = Path(self.tmp.name)
        env = dict(PATH='/usr/bin:/bin', STUB_DIR=str(d), SID=SID, NONCE=N1, OSUDO=str(d / 'osudo'), PGREP=str(d / 'pgrep'),
                   TM09_RELEASE='/opt/tm09-release-x', TM09_LOGS=str(d / 'logs'), TM09_WEEK='2026-09-07', OPLOG=str(d / 'oplog'))
        env.update(extra or {})
        argv = ['bash', str(TM / script)] + ([] if mode is None else [mode]) + list(args)
        r = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60)
        calls = (d / 'calls').read_text().splitlines() if (d / 'calls').exists() else []
        return r, calls

    def test_mode_must_be_named(self):
        for mode in (None, '', 'study', '--rehearsal'):
            r, calls = self.run_sh('tm09_launch.sh', 'price_scout', SID, '8801', SIB, '/tmp/b', mode=mode)
            self.assertEqual((r.returncode, calls), (2, []), mode)

    def test_production_needs_approval_and_export_for_every_role(self):
        for role in ('price_scout', 'boss m P1', 'news_scout'):
            r, calls = self.run_sh('tm09_launch.sh', role, SID, '8801', SIB, '/tmp/b', mode='production',
                                   extra=dict(TM09_APPROVAL='/var/lib/tm09/ops-v2/run.json'))
            self.assertEqual((r.returncode, calls), (2, []), role)

    def test_bad_role_session_or_port_refuses(self):
        for args in (('--role price_scout', SID, '8801'), ('boss m', SID, '8801'), ('boss m X', SID, '8801'),
                     ('price_scout', 'TM07-x', '8801'), ('price_scout', SID, '8781')):
            r, calls = self.run_sh('tm09_launch.sh', *args, SIB, '/tmp/b')
            self.assertEqual((r.returncode, calls), (2, []), args)

    def test_launch_wiring(self):
        r, calls = self.run_sh('tm09_launch.sh', 'boss claude_fable_5_2 N', SID, '8803', SIB, '/tmp/b')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(calls[0].startswith('env -i ') and calls[0].endswith('tm09_ops_sudo.py preflight rehearsal'))
        self.assertTrue(calls[1].endswith(f'tm09_ops_sudo.py checkpoint {SID} 8803'))
        serve = calls[2]
        self.assertTrue(serve.startswith('-u tm09desk sh -c '))
        self.assertIn(f'launch --role boss --boss claude_fable_5_2 --arm N --port 8803 --boundary /var/lib/tm09/ops-v2/{SID}-{N1}-launch.json '
                      f'--canary-proof /var/lib/tm09/ops-v2/{SID}-{N1}-proof.json --rehearsal --root /var/lib/tm09 '
                      f'--key-file /var/lib/tm09/operator.key --approval /var/lib/tm09/ops-v2/rehearsal-approval.json --week 2026-09-07', serve)
        self.assertTrue(calls[3].endswith(f'probe live {SID} 8803 {N1} {SIB} /tmp/b'))
        self.assertIn('ready, live probe passed', r.stdout)

    def test_failed_live_probe_stops_the_listener(self):
        (Path(self.tmp.name) / 'probe_fails').touch()
        r, calls = self.run_sh('tm09_launch.sh', 'price_scout', SID, '8801', SIB, '/tmp/b')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(calls[-1], 'kill -TERM 4242')

    def test_production_wiring(self):
        x = dict(TM09_APPROVAL='/var/lib/tm09/ops-v2/run.json', TM09_EXPORT_DIR='/var/lib/tm09/export')
        r, calls = self.run_sh('tm09_launch.sh', 'news_scout', SID, '8802', SIB, '/tmp/b', mode='production', extra=x)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(calls[0].endswith('preflight production /var/lib/tm09/ops-v2/run.json'))
        self.assertIn('launch --role news_scout --export-dir /var/lib/tm09/export --port 8802', calls[2])
        self.assertNotIn('--rehearsal', calls[2])
        r, calls = self.run_sh('tm09_launch.sh', 'price_scout', SID, '8801', SIB, '/tmp/b', mode='production', extra=x)
        self.assertNotIn('--export-dir', [c for c in calls if 'tm09_operator' in c][-1])

    def test_review_wiring(self):
        r, calls = self.run_sh('tm09_review.sh', 'boss m P1', SID, '8804', N1, SIB, '/tmp/b')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(calls[0], 'kill -TERM 4242')
        self.assertTrue(calls[1].endswith(f'probe stopped {SID} 8804 {N1} {SIB} /tmp/b'))
        self.assertTrue(calls[2].endswith(f'entries {SID} 8804 {N1}'))
        self.assertEqual(calls[3], f'cat /var/lib/tm09/control/{SID}-{N1}.entries.json')
        self.assertTrue(calls[4].endswith('canaries'))
        self.assertTrue(calls[5].startswith('install -o root -g root -m 0600 '))
        self.assertTrue(calls[6].endswith(f'review {SID} 8804 {N1} /var/lib/tm09/invented-rehearsal/TM09-2026-09-07-m-P1 '
                                          f'/var/lib/tm09/control/{SID}-{N1}-operator-sudo.json'))
        self.assertIn(f'review --role boss --boss m --arm P1 --boundary /var/lib/tm09/ops-v2/{SID}-{N1}-review.json '
                      f'--probe-proof /var/lib/tm09/ops-v2/{SID}-{N1}-stopped-probe.json --rehearsal', calls[7])
        self.assertIn('-u tm09desk sh -c', calls[7])


if __name__ == '__main__':
    unittest.main()
