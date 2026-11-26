"""Made-up checks for the TM09 ops route (tm09_ops_sudo.py, tm09_opmatch.py, tm09_launch.sh, tm09_review.sh).

Invented log lines, nonces, sessions and files only. No sudo, no host path is written and no listener is bound."""
import json
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from timemachine import tm09_ops_sudo as ops
from timemachine import tm09_opmatch as om

REPO = Path(__file__).resolve().parents[1]
TM = REPO / 'timemachine'
N1, N2, N3 = 'a' * 32, 'b' * 32, 'c' * 32
GO = lambda auth: '; Approved for TM09 stage 1 and the registered stage 2 branch: `TM09_GO=' + auth + '`'
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

    def test_review_capsule_states_void_false_only_after_the_refusal(self):
        src = (TM / 'tm09_ops_sudo.py').read_text()
        refuse = src.index('if result["void"]:\n            raise ValueError("unlisted sudo entries: not signing a review boundary")')
        sign = src.index('capsule("ledger-222-tm09-review"')
        self.assertLess(refuse, sign)
        self.assertEqual(src.count('capsule("ledger-222-tm09-review"'), 1)
        self.assertIn('listener_stopped=True,void=False)', src[sign:sign + 400])

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
        own = line('17:49:56', '/usr/bin/env -i PATH=/usr/bin:/bin TM09_RELEASE=/opt/r /usr/bin/python3.14 -B /opt/r/timemachine/tm09_ops_sudo.py checkpoint ' + SIB + ' 8802')
        self.assertEqual(self.m([own, good], rec, {N2: SIB})[1], [])                         # record shared with its own line
        self.assertEqual(len(self.m([good, good], rec, {N2: SIB})[1]), 1)                   # repeated
        self.assertEqual(len(self.m([good], rec, {})[1]), 1)                                 # no checkpoint on file
        self.assertEqual(len(self.m([good], rec, {N2: SID})[1]), 1)                          # checkpoint names another session
        self.assertEqual(len(self.m([line('17:50:09', '/usr/bin/true tm09-' + N2)], rec, {N2: SIB})[1]), 1)  # too late
        self.assertEqual(len(self.m([line('17:49:58', '/usr/bin/true tm09-' + N2, target='tm09desk')], rec, {N2: SIB})[1]), 1)

    def test_operator_record_file_pinned_owner_and_mode(self):
        import pwd
        with TemporaryDirectory() as d:
            p = Path(d) / 'opsudo.jsonl'
            p.write_text('{"time":"17:50:00","argv":["true"]}\n')
            p.chmod(0o644)
            me = pwd.getpwuid(os.getuid()).pw_name
            with mock.patch.object(om, 'OPLOG', str(p)):
                self.assertEqual(len(om.read_oplog(str(p), me)[1]), 1)
                other = Path(d) / 'other.jsonl'
                other.write_text(p.read_text())
                with self.assertRaises(SystemExit):
                    om.read_oplog(str(other), me)                     # any other path, even same owner
                with self.assertRaises(KeyError):
                    om.read_oplog(str(p), 'no-such-operator-account')
                p.chmod(0o666)
                with self.assertRaises(SystemExit):
                    om.read_oplog(str(p), me)
            q = Path(d) / 'link'
            q.symlink_to(p)
            with mock.patch.object(om, 'OPLOG', str(q)), self.assertRaises(OSError):
                om.read_oplog(str(q), me)
        self.assertEqual(om.OPLOG, '/tmp/tm07x/opsudo.jsonl')


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

    def test_export_scope_names_this_dir_and_exactly_the_stage_files(self):
        with TemporaryDirectory() as d, mock.patch.object(ops, 'ROOT', Path(d)):
            ex = Path(d) / 'export'
            ex.mkdir()
            pins = {}
            for n in ('stock_sessions.jsonl', 'stock_bars.jsonl', 'stock_news.jsonl'):
                (ex / n).write_bytes(b'made-up ' + n.encode())
                pins[n] = ops.h(b'made-up ' + n.encode())
            s1 = dict(export_dir=str(ex), export_sha256={k: pins[k] for k in ('stock_sessions.jsonl', 'stock_bars.jsonl')})
            s2 = dict(export_dir=str(ex), export_sha256=pins)
            self.assertEqual(ops.export_files(s1, Path.read_bytes, True, ex), 2)
            self.assertEqual(ops.export_files(s2, Path.read_bytes, False, ex), 3)
            other = Path(d) / 'export2'
            for body, stage1, where in ((s2, True, ex), (s1, False, ex), (s1, True, other),
                                        (dict(s1, export_sha256={'unrelated.jsonl': pins['stock_bars.jsonl']}), True, ex),
                                        (dict(s1, export_sha256=dict(s1['export_sha256'], **{'stock_bars.jsonl': '0' * 64})), True, ex),
                                        (dict(s1, export_dir='/tmp/elsewhere'), True, '/tmp/elsewhere')):
                with self.assertRaises(ValueError):
                    ops.export_files(body, Path.read_bytes, stage1, where)
            (ex / 'stock_bars.jsonl').write_bytes(b'')
            with self.assertRaises(ValueError):
                ops.export_files(dict(s1, export_sha256=dict(s1['export_sha256'], **{'stock_bars.jsonl': ops.h(b'')})), Path.read_bytes, True, ex)

    def test_run_approval_needs_the_exact_go_line(self):
        """The engine's parser (lead ruling): one raw row starting `| 222 |`, its final cell ending exactly with the
        approval wording and id, and one TM09_GO= marker in the whole file."""
        ok = b'| 222 | x | lead text' + GO(N1).encode() + b' |\n'
        ops.go_line(ok, N1)
        for bad in (b'| 222 | x | lead text TM09_GO=' + N1.encode() + b' |\n',            # bare marker, no wording
                    b'| 222 | x | lead text' + GO(N1).encode() + b'. |\n',
                    b'| 222 | x | lead text' + GO(N2).encode() + b' |\n',
                    b'| 223 | x | lead text' + GO(N1).encode() + b' |\n',
                    b'| 222 | x | lead text' + GO(N1).encode() + b'\n',
                    ok + b'| 222 | other |\n', ok + b'TM09_GO=other\n', ok + ok, b''):
            with self.assertRaises(ValueError, msg=bad):
                ops.go_line(bad, N1)
        with self.assertRaises(ValueError):
            ops.go_line(ok, 'Not An Id')

    def test_repeated_file_refuses(self):
        with TemporaryDirectory() as d:
            p = Path(d) / 'x'
            ops.put(p, b'{}', owner=None)
            with self.assertRaises(FileExistsError):
                ops.put(p, b'{}', owner=None)


class GlueCLI(unittest.TestCase):
    """The real new-go-id, approve-run and preflight branches on a made-up root, release copy and export."""

    def setUp(self):
        import pwd, shutil
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = Path(os.path.realpath(self.tmp.name))
        self.root, self.rel = d / 'tm09', d / 'rel'
        for sub in ('ops-v2', 'control', 'canaries', 'export'):
            (self.root / sub).mkdir(parents=True)
        (self.root / 'operator.key').write_text('k' * 48 + '\n')
        canaries = [self.root / 'canaries/tape', self.root / 'canaries/notes', self.root / 'operator.key', self.root / 'canaries/results']
        for c in canaries[:2] + canaries[3:]:
            c.write_text('canary\n')
        for name in ops.FILES + ('config/thresholds.yaml', 'timemachine/TM09_REGISTRATION.md', ops.LEDGER):
            (self.rel / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO / name, self.rel / name)
        me = pwd.getpwuid(os.getuid()).pw_name
        for name, value in (('ROOT', self.root), ('OPS', self.root / 'ops-v2'), ('CONTROL', self.root / 'control'),
                            ('CANARIES', canaries), ('SERVICE', me)):
            patcher = mock.patch.object(ops, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.dict(os.environ, TM09_RELEASE=str(self.rel))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.ex = self.root / 'export'
        self.pins = {}
        for n in ('stock_sessions.jsonl', 'stock_bars.jsonl', 'stock_news.jsonl'):
            (self.ex / n).write_bytes(b'made-up ' + n.encode())
            self.pins[n] = ops.h(b'made-up ' + n.encode())

    def main(self, *argv):
        from io import StringIO
        with mock.patch('sys.stdout', new=StringIO()) as out:
            ops.main(list(argv))
        return out.getvalue()

    def go(self, row_end):
        ledger = self.rel / ops.LEDGER
        lines = ledger.read_text().split('\n')
        i = next(i for i, l in enumerate(lines) if l.startswith('| 222 | '))
        lines[i] = lines[i][:-2] + row_end + ' |'
        ledger.write_text('\n'.join(lines))

    def fields(self, mode, names):
        f = self.root / ('fields-' + mode + '.json')
        f.write_text(json.dumps(dict(mode=mode, export_dir=str(self.ex), export_sha256={n: self.pins[n] for n in names})))
        return str(f)

    def test_stage1_run_capsule_and_preflight_without_news(self):
        auth = self.main('new-go-id').strip().split('=')[1]
        s1 = ('stock_sessions.jsonl', 'stock_bars.jsonl')
        with self.assertRaises(ValueError):
            self.main('approve-run', auth, self.fields('stage1', s1))           # no docket line yet
        self.go(GO(auth))
        with self.assertRaises(ValueError):
            self.main('approve-run', auth, self.fields('stage1', ops.STAGE_FILES[False]))   # stage 1 with news refuses
        with self.assertRaises(ValueError):
            self.main('approve-run', N3, self.fields('stage1', s1))             # id not issued here
        (self.ex / 'stock_news.jsonl').unlink()                                  # stage 1 needs no headline store
        self.main('approve-run', auth, self.fields('stage1', s1))
        cap = self.root / 'ops-v2' / f'run-stage1-{auth}.json'
        body = json.loads(cap.read_text())['body']
        self.assertEqual((body['mode'], body['authorization_id'], body['ledger_sha256']),
                         ('stage1', auth, ops.h((self.rel / ops.LEDGER).read_bytes())))
        self.assertIn('export files 2', self.main('preflight', 'production', str(cap), str(self.ex)))
        self.main('approve-build', auth, self.fields('stage1', s1))
        from timemachine.tm09_desk import verify_seal
        b = json.loads((self.root / 'ops-v2' / f'build-stage1-{auth}.json').read_text())
        verify_seal('k' * 48, 'ledger-222-build-fixtures', b['body'], b['seal'])
        self.assertEqual(b['body']['authorization_id'], auth)
        with self.assertRaises(ValueError):
            self.main('preflight', 'production', str(cap), str(self.root / 'other'))
        with open(self.rel / ops.LEDGER, 'a') as f:
            f.write('\nlater line\n')
        with self.assertRaises(ValueError):
            self.main('preflight', 'production', str(cap), str(self.ex))         # ledger changed since signing

    def test_stage2_needs_the_engine_stage1_check_news_and_its_own_id(self):
        from timemachine import tm09_blind
        a = self.main('new-go-id').strip().split('=')[1]
        with self.assertRaises(FileExistsError):
            self.main('new-go-id')                                              # one id, never reissued
        self.go(GO(a))
        full = ops.STAGE_FILES[False]
        self.main('approve-run', a, self.fields('stage1', ('stock_sessions.jsonl', 'stock_bars.jsonl')))  # same id, stage 1
        with self.assertRaises(ValueError):
            self.main('approve-run', N3, self.fields('A', full))                 # an id not issued here
        with self.assertRaises(FileNotFoundError):
            self.main('approve-run', a, self.fields('A', full))                  # real gate: no Stage 1 check receipt
        f = self.root / 'nomode.json'
        f.write_text(json.dumps(dict(export_dir=str(self.ex), export_sha256=self.pins)))
        with self.assertRaises(ValueError):
            self.main('approve-run', a, str(f))
        with mock.patch.object(tm09_blind, 'verify_stage2') as gate:
            with self.assertRaises(ValueError):
                self.main('approve-run', a, self.fields('A', ('stock_sessions.jsonl', 'stock_bars.jsonl')))
            fields = json.loads(Path(self.fields('A', full)).read_text())
            fields['blind_report_sha256'] = 'r' * 64
            (self.root / 'fa.json').write_text(json.dumps(fields))
            self.main('approve-run', a, str(self.root / 'fa.json'))
            self.assertEqual(gate.call_args.args[:4], (self.root, 'k' * 48, 'A', 'r' * 64))
            cap = self.root / 'ops-v2' / f'run-A-{a}.json'
            self.assertIn('export files 3', self.main('preflight', 'production', str(cap), str(self.ex)))
            gate.side_effect = ValueError('Stage 2 checker provenance refused')
            with self.assertRaises(ValueError):
                self.main('preflight', 'production', str(cap), str(self.ex))
        with self.assertRaises(FileNotFoundError):
            self.main('preflight', 'production', str(cap), str(self.ex))        # real gate again
        old = self.root / 'ops-v2' / 'old.json'
        from timemachine.tm09_desk import seal
        body = {k: v for k, v in json.loads(cap.read_text())['body'].items() if k not in ('ledger_sha256', 'authorization_id')}
        old.write_text(json.dumps({'body': body, 'seal': seal('k' * 48, 'ledger-222-run-tm09', body)}))
        with self.assertRaises(ValueError):
            self.main('preflight', 'production', str(old), str(self.ex))        # capsule without ledger binding

    def test_docket_line_must_be_exact(self):
        auth = self.main('new-go-id').strip().split('=')[1]
        s1 = ('stock_sessions.jsonl', 'stock_bars.jsonl')
        for end in (' TM09_GO=' + auth, GO(auth) + '.', GO(auth)[:-1], GO(auth) + ' TM09_GO=' + auth, GO(N3)):
            backup = (self.rel / ops.LEDGER).read_bytes()
            self.go(end)
            with self.assertRaises(ValueError, msg=end):
                self.main('approve-run', auth, self.fields('stage1', s1))
            (self.rel / ops.LEDGER).write_bytes(backup)
        ledger = (self.rel / ops.LEDGER).read_text()
        for extra in ('<!-- | 222 | x' + GO(auth) + ' |\n', '```\n| 222 | x' + GO(auth) + ' |\n```\n'):
            (self.rel / ops.LEDGER).write_text(ledger + extra)                   # the real row does not authorize
            with self.assertRaises(ValueError, msg=extra):
                self.main('approve-run', auth, self.fields('stage1', s1))
        (self.rel / ops.LEDGER).write_text(ledger)
        self.go(GO(auth))
        good = (self.rel / ops.LEDGER).read_text()
        (self.rel / ops.LEDGER).write_text(good + '```\n| 222 | example row |\n```\n')   # a second 222 row, even fenced
        with self.assertRaises(ValueError):
            self.main('approve-run', auth, self.fields('stage1', s1))
        (self.rel / ops.LEDGER).write_text(good)
        self.main('approve-run', auth, self.fields('stage1', s1))


# The stub stands in for osudo only: it appends the timed operator record exactly as osudo does and the sudo log
# line sudo would write (resolved path, run-as account), then answers as the root step would.
STUB = r"""#!/bin/bash
t=$(date -u +%T)
python3 -c 'import json,sys; print(json.dumps({"time":sys.argv[1],"argv":sys.argv[2:]}))' "$t" "$@" >> "$STUB_DIR/oplog"
user=root; a=("$@"); [ "${a[0]}" = -u ] && { user=${a[1]}; a=("${a[@]:2}"); }
cmd=${a[0]}; case "$cmd" in /*) ;; *) cmd=/usr/bin/$cmd ;; esac
rest="${a[*]:1}"; [ -n "$rest" ] && cmd="$cmd $rest"
echo "Nov 26 $t : user : PWD=/tmp ; USER=$user ; COMMAND=$cmd" >> "$STUB_DIR/sudo.log"
printf '%s\n' "$*" >> "$STUB_DIR/calls"
case "$*" in
  *" checkpoint "*) echo "Nov 26 $(date -u +%T) : user : PWD=/tmp ; USER=root ; COMMAND=/usr/bin/true tm09-$NONCE" >> "$STUB_DIR/sudo.log"
                   echo "/var/lib/tm09/ops-v2/$SID-$NONCE-proof.json"; echo "$SID-$NONCE-launch.json abc" ;;
  *"tm09_engine.sh launch "*) echo "Registered desk ready; brief only this session's roles."; sleep 1 ;;
  *"kill -TERM"*) touch "$STUB_DIR/killed" ;;
  *" probe "*) [ -e "$STUB_DIR/probe_fails" ] && exit 1; echo probe ok ;;
  *" canaries") echo "{\"$NONCE\": \"$SID\"}" ;;
  "cat "*entries.json) python3 -c 'import json,sys; print(json.dumps({"sudo_entries": open(sys.argv[1]).read().splitlines()}))' "$STUB_DIR/sudo.log" ;;
esac
exit 0
"""
PGREP = '#!/bin/bash\n[ -e "$STUB_DIR/killed" ] && exit 1\nprintf "%s\\n" "$*" >> "$STUB_DIR/pgrep_calls"\necho 4242\n'


class Shell(unittest.TestCase):
    """The committed scripts, copied with only the osudo, pgrep, log-dir, TM07-port and operator-record constants
    pointed at the stubs."""

    def setUp(self):
        import pwd, socket
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = self.d = Path(self.tmp.name)
        for name, body in (('osudo', STUB), ('pgrep', PGREP)):
            (d / name).write_text(body)
            (d / name).chmod(0o700)
        (d / 'oplog').write_text('')
        (d / 'oplog').chmod(0o600)
        (d / 'sudo.log').write_text('')
        self.bearer = str(d / 'b')
        (d / 'b').write_text('{}')
        free = socket.socket()
        free.bind(('127.0.0.1', 0))
        self.free_port = free.getsockname()[1]
        free.close()
        (d / 'tm').mkdir()
        for f in ('tm09_launch.sh', 'tm09_review.sh'):
            (d / 'tm' / f).write_text((TM / f).read_text())
        (d / 'tm' / 'tm09_ops_env.sh').write_text((TM / 'tm09_ops_env.sh').read_text()
            .replace('OSUDO=/opt/tm07-ops-pub/osudo', f'OSUDO={d}/osudo').replace('PGREP=pgrep', f'PGREP={d}/pgrep')
            .replace('LOGS=/tmp/tm09x/logs', f'LOGS={d}/logs')
            .replace('TM07_PORTS="8781 8782 8783 8784 8785 8786 8787"', f'TM07_PORTS="{self.free_port}"'))
        me = pwd.getpwuid(os.getuid()).pw_name
        (d / 'tm' / 'tm09_opmatch.py').write_text((TM / 'tm09_opmatch.py').read_text()
            .replace('OPLOG = "/tmp/tm07x/opsudo.jsonl"', f'OPLOG = "{d}/oplog"').replace('OPERATOR = "user"', f'OPERATOR = "{me}"'))

    def run_sh(self, script, *args, mode='rehearsal', extra=None):
        d = self.d
        env = dict(PATH='/usr/bin:/bin', STUB_DIR=str(d), SID=SID, NONCE=N1, TM09_RELEASE='/opt/tm09-release-x', TM09_WEEK='2026-09-07')
        env.update(extra or {})
        argv = ['bash', str(d / 'tm' / script)] + ([] if mode is None else [mode]) + list(args)
        r = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=60)
        calls = (d / 'calls').read_text().splitlines() if (d / 'calls').exists() else []
        return r, calls

    def test_bearer_must_be_absolute_before_any_side_effect(self):
        for bad in ('b', 'wk/b.json', str(self.d / 'missing')):
            for script, args in (('tm09_launch.sh', ('price_scout', SID, '8801', SIB, bad)),
                                 ('tm09_review.sh', ('price_scout', SID, '8801', N1, SIB, bad))):
                r, calls = self.run_sh(script, *args)
                self.assertEqual((r.returncode, calls), (2, []), (script, bad, r.stderr))
                self.assertIn('BEARER_FILE must be an absolute path', r.stderr)

    def test_mode_must_be_named(self):
        for mode in (None, '', 'study', '--rehearsal'):
            r, calls = self.run_sh('tm09_launch.sh', 'price_scout', SID, '8801', SIB, self.bearer, mode=mode)
            self.assertEqual((r.returncode, calls), (2, []), mode)

    def test_production_needs_approval_and_export_for_every_role(self):
        for role in ('price_scout', 'boss m P1', 'news_scout'):
            r, calls = self.run_sh('tm09_launch.sh', role, SID, '8801', SIB, self.bearer, mode='production',
                                   extra=dict(TM09_APPROVAL='/var/lib/tm09/ops-v2/run.json'))
            self.assertEqual((r.returncode, calls), (2, []), role)

    def test_refuses_while_a_tm07_listener_answers(self):
        import socket
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', self.free_port))
        s.listen()
        self.addCleanup(s.close)
        for script, args in (('tm09_launch.sh', ('price_scout', SID, '8801', SIB, self.bearer)),
                             ('tm09_review.sh', ('price_scout', SID, '8801', N1, SIB, self.bearer))):
            r, calls = self.run_sh(script, *args)
            self.assertEqual((r.returncode, calls), (3, []), script)

    def test_roles_and_arms(self):
        for args in (('--role price_scout', SID, '8801'), ('boss m', SID, '8801'), ('boss m X', SID, '8801'), ('boss m P4', SID, '8801'),
                     ('price_scout', 'TM07-x', '8801'), ('price_scout', SID, '8781')):
            r, calls = self.run_sh('tm09_launch.sh', *args, SIB, self.bearer)
            self.assertEqual((r.returncode, calls), (2, []), args)
        for arm in ('P1', 'P2', 'P3', 'N', 'N1', 'N2', 'N3'):
            (self.d / 'calls').unlink(missing_ok=True)
            shutil.rmtree(self.d / 'logs', ignore_errors=True)   # no ready line left from the previous arm
            r, calls = self.run_sh('tm09_launch.sh', 'boss m ' + arm, SID, '8801', SIB, self.bearer)
            self.assertEqual(r.returncode, 0, arm + r.stderr)
            launches = [c for c in calls if ' launch ' in c]
            self.assertEqual(len(launches), 1, arm)
            self.assertIn('--arm ' + arm + ' ', launches[0])

    def test_launch_wiring(self):
        r, calls = self.run_sh('tm09_launch.sh', 'boss claude_fable_5_2 N', SID, '8803', SIB, self.bearer)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(calls[0].startswith('env -i ') and calls[0].endswith('tm09_ops_sudo.py preflight rehearsal'))
        self.assertTrue(calls[1].endswith(f'tm09_ops_sudo.py checkpoint {SID} 8803'))
        self.assertEqual(calls[2], f'-u tm09desk /opt/tm09-release-x/timemachine/tm09_engine.sh launch --role boss --boss claude_fable_5_2 --arm N '
                         f'--port 8803 --boundary /var/lib/tm09/ops-v2/{SID}-{N1}-launch.json --canary-proof /var/lib/tm09/ops-v2/{SID}-{N1}-proof.json '
                         f'--rehearsal --root /var/lib/tm09 --key-file /var/lib/tm09/operator.key '
                         f'--approval /var/lib/tm09/ops-v2/rehearsal-approval.json --week 2026-09-07')
        self.assertTrue(calls[3].endswith(f'probe live {SID} 8803 {N1} {SIB} {self.bearer}'))
        self.assertIn('ready, live probe passed', r.stdout)

    def test_failed_live_probe_stops_only_this_generation(self):
        (self.d / 'probe_fails').touch()
        r, calls = self.run_sh('tm09_launch.sh', 'price_scout', SID, '8801', SIB, self.bearer)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(calls[-1], 'kill -TERM 4242')
        self.assertIn(f'--boundary /var/lib/tm09/ops-v2/{SID}-{N1}-launch.json', (self.d / 'pgrep_calls').read_text())

    def test_production_wiring_has_no_live_probe(self):
        x = dict(TM09_APPROVAL='/var/lib/tm09/ops-v2/run.json', TM09_EXPORT_DIR='/var/lib/tm09/export')
        r, calls = self.run_sh('tm09_launch.sh', 'news_scout', SID, '8802', SIB, self.bearer, mode='production', extra=x)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(calls[0].endswith('preflight production /var/lib/tm09/ops-v2/run.json /var/lib/tm09/export'))
        self.assertIn('launch --role news_scout --export-dir /var/lib/tm09/export --port 8802', calls[2])
        self.assertNotIn('--rehearsal', calls[2])
        self.assertFalse(any(' probe ' in c for c in calls))
        (self.d / 'calls').unlink()
        r, calls = self.run_sh('tm09_review.sh', 'news_scout', SID, '8802', N1, SIB, self.bearer, mode='production', extra=x)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertTrue(any(c.endswith(f'review production {SID} 8802 {N1} /var/lib/tm09/TM09-2026-09-07-news_scout '
                                       f'/var/lib/tm09/control/{SID}-{N1}-operator-sudo.json') for c in calls))

    def test_review_wiring(self):
        r, calls = self.run_sh('tm09_review.sh', 'boss m P1', SID, '8804', N1, SIB, self.bearer)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(calls[0], 'kill -TERM 4242')
        self.assertIn(f'--port 8804 --boundary /var/lib/tm09/ops-v2/{SID}-{N1}-launch.json', (self.d / 'pgrep_calls').read_text())
        self.assertTrue(calls[1].endswith(f'probe stopped {SID} 8804 {N1} {SIB} {self.bearer}'))
        self.assertTrue(calls[2].endswith(f'entries {SID} 8804 {N1}'))
        self.assertEqual(calls[3], f'cat /var/lib/tm09/control/{SID}-{N1}.entries.json')
        self.assertTrue(calls[4].endswith('canaries'))
        self.assertTrue(calls[5].startswith('install -o root -g root -m 0600 '))
        self.assertTrue(calls[6].endswith(f'review rehearsal {SID} 8804 {N1} /var/lib/tm09/invented-rehearsal/TM09-2026-09-07-m-P1 '
                                          f'/var/lib/tm09/control/{SID}-{N1}-operator-sudo.json'))
        self.assertEqual(calls[7], f'-u tm09desk /opt/tm09-release-x/timemachine/tm09_engine.sh review --role boss --boss m --arm P1 '
                         f'--boundary /var/lib/tm09/ops-v2/{SID}-{N1}-review.json --probe-proof /var/lib/tm09/ops-v2/{SID}-{N1}-stopped-probe.json '
                         f'--rehearsal --root /var/lib/tm09 --key-file /var/lib/tm09/operator.key '
                         f'--approval /var/lib/tm09/ops-v2/rehearsal-approval.json --week 2026-09-07')

    def test_whole_session_sudo_lines_all_listed_by_the_real_matcher(self):
        """launch then review through the real scripts; the sudo log lines they cause, cut from the checkpoint up to the
        entries step, all match the real matcher's records and the real TM07-derived review, so nothing voids."""
        for script, args in (('tm09_launch.sh', ('boss claude_fable_5_2 N2', SID, '8803', SIB, self.bearer)),
                             ('tm09_review.sh', ('boss claude_fable_5_2 N2', SID, '8803', N1, SIB, self.bearer))):
            r, _ = self.run_sh(script, *args)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        listed = json.loads((self.d / 'logs' / f'review-{SID}-{N1}' / 'operator-sudo.json').read_text())
        lines = (self.d / 'sudo.log').read_text().splitlines()
        cp = next(i for i, l in enumerate(lines) if l.endswith(f'checkpoint {SID} 8803'))
        cut = next(i for i, l in enumerate(lines) if l.endswith(f'entries {SID} 8803 {N1}'))
        window = lines[cp + 1:cut + 1]
        self.assertTrue(any('tm09_engine.sh launch ' in l for l in window))
        self.assertTrue(any('/usr/bin/true tm09-' + N1 in l for l in window))
        review = ops.sudo_review(window, listed)
        self.assertEqual((review['unlisted'], review['void']), ([], False))
        recs = [json.loads(l) for l in (self.d / 'oplog').read_text().splitlines()]
        listed2, miss = om.match(window, recs, {N1: SID}, is_file=lambda p: p.startswith('/usr/bin/'))
        self.assertEqual(miss, [])
        tampered = [l.replace('--arm N2 ', '--arm N3 ') for l in window]
        self.assertTrue(ops.sudo_review(tampered, listed)['void'])


if __name__ == '__main__':
    unittest.main()
