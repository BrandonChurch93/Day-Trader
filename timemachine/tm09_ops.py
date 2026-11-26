"""TM09 host operator ceremony: key, rehearsal approval, sudo canary, sudo review and signed boundaries.

Prints names and hashes only, never a key, bearer, price or headline. Commands and the account each runs as:

  keygen                                   tm09desk
  approve-rehearsal BOUNDARY_TEXT          tm09desk
  canary SID PORT                          root (osudo); writes a proof owned by tm09desk
  launch-boundary SID PORT PROOF           tm09desk
  sudo-review SID NONCE OPERATOR_JSONL     root (osudo); writes a review owned by tm09desk
  review-boundary SID PORT NONCE DESK_DIR PROBE SUDO_REVIEW   tm09desk; refuses any unlisted sudo line

Set TM09_RELEASE to the pinned release directory. The engine (tm09_operator) checks every capsule again.
"""
import json
import os
from pathlib import Path
import re
import secrets
from hashlib import sha256
import sys

ROOT = Path('/var/lib/tm09')
OPS = ROOT / 'ops'
KEY = ROOT / 'operator.key'
SUDO_LOG = Path('/var/log/tm07-sudo.log')
WORKER = 'user'
FILES = ('timemachine/tm09_desk.py', 'timemachine/tm09_orders.py', 'timemachine/tm09_fixture.py', 'timemachine/tm09_feed.py',
         'timemachine/tm09_operator.py', 'timemachine/tm09_isolation_probe.py', 'timemachine/score_tm09.py',
         'timemachine/tm09_blind.py', 'timemachine/test_tm09.py', 'timemachine/TM09_WORKER_BRIEFS.md')
REHEARSAL_LIMITS = dict(notes=2, note_chars=280, looks=50, look_rows=120, headline_rows=20, headline_chars=500)
NONCE = re.compile(r'[a-f0-9]{32}')
LINE = re.compile(r'\w+ +\d+ (\d\d:\d\d:\d\d) : (\S+) :.*?COMMAND=(.*)$')
CANARY = re.compile(r'/usr/bin/true tm09-([a-f0-9]{32})')


class Refused(ValueError):
    pass


def h(raw):
    return sha256(raw).hexdigest()


def _seconds(t):
    hh, mm, ss = map(int, t.split(':'))
    return hh * 3600 + mm * 60 + ss


def _norm(s):
    return re.sub(r'\s+', ' ', re.sub(r"[\\'\"]", '', s.replace('#012', ' '))).strip()


def _argv(record):
    a = list(record['argv'])
    while a and a[0] in ('-u', '-n', '-g'):
        a = a[2:] if a[0] in ('-u', '-g') else a[1:]
    return a


def sudo_review(lines, records, nonce, canaries_on_file, slack=2):
    """Match each sudo log line to one operator record (time within slack s, same command) or a TM09 canary.

    A canary line is listed only when it is this launch's nonce or a nonce with an operator proof on file.
    Anything else, including any line not run by the operator account, is unlisted.
    """
    used, listed, unlisted = set(), [], []
    for line in lines:
        m = LINE.match(line.rstrip())
        if not m or m.group(2) != WORKER:
            unlisted.append(line)
            continue
        t, cmd = m.group(1), m.group(3)
        c = CANARY.fullmatch(cmd)
        if c and (c.group(1) == nonce or c.group(1) in canaries_on_file):
            listed.append({'time': t, 'command': cmd, 'canary': 'own' if c.group(1) == nonce else 'other TM09 launch, proof on file'})
            continue
        first, _, rest = cmd.partition(' ')
        hit = None
        for i, r in enumerate(records):
            a = _argv(r)
            if (i not in used and a and abs(_seconds(t) - _seconds(r['time'])) <= slack
                    and os.path.basename(a[0]) == os.path.basename(first) and _norm(' '.join(a[1:])) == _norm(rest)):
                hit = i
                break
        if hit is None:
            unlisted.append(line)
        else:
            used.add(hit)
            listed.append({'time': t, 'command': cmd})
    return {'session': None, 'nonce': nonce, 'entries': len(lines), 'listed': listed, 'unlisted': unlisted}


def review_body(review, sid, port, nonce, control, probe_raw, sudo_raw):
    """Body of the ledger-222-tm09-review capsule. Refuses unless the sudo review is complete and clean."""
    if (review.get('session') != sid or review.get('nonce') != nonce or review.get('unlisted') != []
            or not isinstance(review.get('listed'), list) or review.get('entries') != len(review['listed'])):
        raise Refused('unlisted or unreviewed sudo entries: not signing a review boundary')
    from timemachine.tm09_fixture import fingerprint
    return dict(session=sid, port=port, nonce=nonce, control_sha256=fingerprint(control),
                post_stop_probe_sha256=h(probe_raw), sudo_review_sha256=h(sudo_raw),
                sudo_allowlist_reviewed=True, raw_copies_denied=True, listener_stopped=True)


def launch_body(sid, port, proof_raw):
    ev = json.loads(proof_raw)
    if (ev.get('session') != sid or ev.get('port') != port or not NONCE.fullmatch(ev.get('nonce', ''))
            or ev.get('matched_canary') is not True or ev.get('prefix_unchanged') is not True
            or not 0 <= ev['size_before'] < ev['size_after']):
        raise Refused('canary proof does not support a launch')
    return dict(session=sid, port=port, nonce=ev['nonce'], canary_observed=True,
                sudo_size_before=ev['size_before'], sudo_size_after=ev['size_after'], sudo_checkpoint_sha256=h(proof_raw))


def _write_owned(path, data):
    """Root helper: create a 0600 file owned by tm09desk."""
    import pwd
    u = pwd.getpwnam('tm09desk')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.write(fd, data)
    os.fsync(fd)
    os.close(fd)
    os.chown(path, u.pw_uid, u.pw_gid)


def main(argv):
    rel = Path(os.environ['TM09_RELEASE'])
    sys.path.insert(0, str(rel))
    from timemachine.tm09_desk import seal, store_new
    from timemachine.tm09_fixture import read_private, settings

    def key():
        return read_private(KEY).decode().strip()

    def capsule(domain, body, out):
        store_new(out, {'body': body, 'seal': seal(key(), domain, body)})
        print(out.name, h(read_private(out)))

    cmd, args = argv[0], argv[1:]
    if cmd == 'keygen':
        fd = os.open(KEY, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.write(fd, (secrets.token_urlsafe(48) + '\n').encode())
        os.close(fd)
        print('key written')
    elif cmd == 'approve-rehearsal':
        cfg = read_private(rel / 'config/thresholds.yaml')
        files = {n: h(read_private(rel / n)) for n in FILES}
        body = dict(root=str(ROOT), service_uid=os.geteuid(), release=str(rel),
                    approved_by='lead agent, ledger 222 (rehearsal and provisioning release)',
                    release_files=files, config_sha256=h(cfg),
                    registration_sha256=h(read_private(rel / 'timemachine/TM09_REGISTRATION.md')),
                    resolved_settings=settings(cfg), limits=dict(REHEARSAL_LIMITS),
                    operator_boundary_sha256=h(read_private(Path(args[0]))), ports=list(range(8801, 8807)))
        capsule('ledger-222-rehearse-tm09', body, OPS / 'rehearsal-approval.json')
    elif cmd == 'canary':
        import subprocess
        sid, port = args[0], int(args[1])
        nonce = secrets.token_hex(16)
        before = SUDO_LOG.read_bytes()
        subprocess.run(['/usr/sbin/runuser', '-u', WORKER, '--', '/usr/bin/sudo', '-n', '/usr/bin/true', 'tm09-' + nonce], check=True)
        after = SUDO_LOG.read_bytes()
        tail = after[len(before):]
        matched = re.search(rb'\b' + WORKER.encode() + rb'\s*:.*;\s*USER=root\s*;\s*COMMAND=/usr/bin/true tm09-'
                            + nonce.encode() + rb'\s*\n', tail) is not None
        proof = dict(session=sid, port=port, nonce=nonce, matched_canary=matched,
                     prefix_unchanged=after[:len(before)] == before, size_before=len(before), size_after=len(after))
        out = OPS / f'{sid}-{nonce}-proof.json'
        _write_owned(out, json.dumps(proof, sort_keys=True).encode())
        print(out, 'matched', matched, 'prefix', proof['prefix_unchanged'])
    elif cmd == 'launch-boundary':
        sid, port, proof = args[0], int(args[1]), Path(args[2])
        body = launch_body(sid, port, read_private(proof))
        capsule('ledger-222-tm09-launch', body, OPS / f'{sid}-{body["nonce"]}-launch.json')
    elif cmd == 'sudo-review':
        sid, nonce, oplog = args[0], args[1], Path(args[2])
        proof = json.loads(read_private(OPS / f'{sid}-{nonce}-proof.json'))
        lines = [l for l in SUDO_LOG.read_bytes()[proof['size_before']:].decode('utf-8', 'replace').splitlines() if l.strip()]
        records = [json.loads(l) for l in oplog.read_text().splitlines() if l.strip()]
        on_file = {m.group(1) for p in OPS.iterdir() if (m := re.fullmatch(r'TM09-[0-9a-f]{32}-([0-9a-f]{32})-proof\.json', p.name))}
        review = sudo_review(lines, records, nonce, on_file)
        review['session'] = sid
        out = OPS / f'{sid}-{nonce}-sudo.json'
        _write_owned(out, json.dumps(review, indent=1, sort_keys=True).encode())
        print('sudo entries', review['entries'], 'listed', len(review['listed']), 'unlisted', len(review['unlisted']))
        for line in review['unlisted']:
            print('UNLISTED', line[:200])
    elif cmd == 'review-boundary':
        sid, port, nonce, desk_dir, probe, sudo = args[0], int(args[1]), args[2], Path(args[3]), Path(args[4]), Path(args[5])
        sudo_raw = read_private(sudo)
        control = json.loads(read_private(desk_dir / f'{nonce}-control.json'))
        body = review_body(json.loads(sudo_raw), sid, port, nonce, control, read_private(probe), sudo_raw)
        capsule('ledger-222-tm09-review', body, OPS / f'{sid}-{nonce}-review.json')
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Refused as exc:
        raise SystemExit('TM09 ops refused: ' + str(exc))
