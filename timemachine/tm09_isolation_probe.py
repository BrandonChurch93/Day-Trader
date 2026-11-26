"""Redacted TM09 boundary check. Run as the actual sandboxed rehearsal worker."""
import argparse
import json
import os
from pathlib import Path
import stat
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from timemachine.tm09_desk import PORTS, PUBLIC_SID, ROLES, TOKEN
from timemachine.tm09_fixture import read_private

# Workers of every role are denied direct reads of these same four targets.
CANARY_TARGETS = ('private tape', 'notes', 'key', 'results')


def required_canary_targets(role):
    if role not in ROLES:
        raise ValueError('invalid worker role for isolation review')
    return CANARY_TARGETS


def request(opener, port, sid, route, token, data=None):
    header = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    uri = f'http://127.0.0.1:{port}/desk/{route}?session={sid}'
    try:
        with opener.open(Request(uri, data=data, headers=header), timeout=3) as reply:
            return reply.status, json.load(reply)
    except HTTPError as exc:
        return exc.code, None


def cannot_open(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        return isinstance(exc, PermissionError)
    os.close(fd)
    return False


def probe(port, sid, sibling, token, canaries, stopped=False):
    if (port not in PORTS or not PUBLIC_SID.fullmatch(sid) or not PUBLIC_SID.fullmatch(sibling)
            or not TOKEN.fullmatch(token) or sid == sibling or not os.geteuid()):
        raise ValueError('invalid rehearsal boundary parameters')
    if (len(canaries) != len(CANARY_TARGETS) or len(set(canaries)) != len(canaries)
            or not all(cannot_open(p) for p in canaries)):
        raise ValueError('raw-copy boundary not proven')
    opener = build_opener(ProxyHandler({}))
    if stopped:
        # After stop, repeat the file check; confirm the port no longer answers.
        from urllib.error import URLError
        try:
            request(opener, port, sid, 'status', token)
        except URLError as exc:
            if not isinstance(exc.reason, ConnectionRefusedError):
                raise
            return
        raise ValueError('rehearsal listener still reachable')
    status, body = request(opener, port, sid, 'status', token)
    if status != 200 or set(body) != {'done', 'step', 'total'}:
        raise ValueError('own session did not provide scoped status')
    tests = [request(opener, port, sibling, 'status', token),
             request(opener, port, sid, 'status', 'x' * 48),
             request(opener, port, sid, 'export', token),
             request(opener, port, sid, 'look', token, b'{"wake_key":"wrong","symbol":"SYN","rows":1}')]
    if any(status != 403 for status, _ in tests):
        raise ValueError('worker scope or wake-key guard not proven')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--session', required=True)
    p.add_argument('--sibling', required=True)
    p.add_argument('--bearer-file', type=Path, required=True)
    p.add_argument('--canary', type=Path, action='append', required=True,
                   help='one distinct, operator-verified path per target, in order: ' + ', '.join(CANARY_TARGETS))
    p.add_argument('--stopped', action='store_true')
    a = p.parse_args()
    try:
        if (a.bearer_file.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO)
                or any(not f.is_relative_to('/var/lib/tm09') or '..' in f.parts or 'tm07' in str(f).lower() for f in a.canary)):
            raise ValueError('use private bearer and direct TM09-only canaries')
        token = json.loads(read_private(a.bearer_file))['token']
        probe(a.port, a.session, a.sibling, token, a.canary, stopped=a.stopped)
    except (ValueError, KeyError, OSError):
        p.exit(1, 'TM09 isolation check failed; no input or token logged.\n')
    print(json.dumps({'session': a.session, 'port': a.port, 'denied_count': len(a.canary),
                      'phase': 'stopped' if a.stopped else 'live'}, sort_keys=True))
