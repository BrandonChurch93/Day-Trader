"""Made-up checks for the TM09 host ceremony helpers. Invented log lines and nonces only."""
import json
import unittest

from timemachine.tm09_ops import Refused, launch_body, review_body, sudo_review

OWN = 'a' * 32
OTHER = 'b' * 32
STRAY = 'c' * 32
SID = 'TM09-' + 'd' * 32


def line(t, cmd, who='user'):
    return f'Nov 26 {t} : {who} : PWD=/tmp ; USER=root ; COMMAND={cmd}'


RECORDS = [{'time': '17:50:00', 'argv': ['-u', 'tm09desk', 'kill', '-TERM', '4376']},
           {'time': '17:50:01', 'argv': ['install', '-o', 'tm09desk', '-m', '0600', '/tmp/a', '/var/lib/tm09/ops/a']}]
CONTROL = {'body': {'session': SID, 'nonce': OWN, 'port': 8801}, 'seal': 'e' * 64}


class SudoReview(unittest.TestCase):
    def test_operator_records_and_own_canary_are_listed(self):
        r = sudo_review([line('17:49:58', '/usr/bin/true tm09-' + OWN), line('17:50:01', '/usr/bin/kill -TERM 4376'),
                         line('17:50:02', '/usr/bin/install -o tm09desk -m 0600 /tmp/a /var/lib/tm09/ops/a')], RECORDS, OWN, set())
        self.assertEqual((r['entries'], len(r['listed']), r['unlisted']), (3, 3, []))

    def test_other_canary_is_listed_only_with_a_proof_on_file(self):
        lines = [line('17:49:34', '/usr/bin/true tm09-' + OTHER), line('17:49:46', '/usr/bin/true tm09-' + STRAY)]
        r = sudo_review(lines, [], OWN, {OTHER})
        self.assertEqual(len(r['listed']), 1)
        self.assertEqual(r['unlisted'], [lines[1]])

    def test_time_slack_command_and_account_must_match(self):
        lines = [line('17:50:05', '/usr/bin/kill -TERM 4376'), line('17:50:01', '/usr/bin/kill -KILL 4376'),
                 line('17:50:00', '/usr/bin/kill -TERM 4376', who='tm09desk')]
        self.assertEqual(len(sudo_review(lines, RECORDS, OWN, set())['unlisted']), 3)

    def test_one_record_covers_one_line(self):
        lines = [line('17:50:00', '/usr/bin/kill -TERM 4376')] * 2
        self.assertEqual(len(sudo_review(lines, RECORDS, OWN, set())['unlisted']), 1)


class ReviewBoundary(unittest.TestCase):
    def review(self, lines, on_file=frozenset()):
        r = sudo_review(lines, RECORDS, OWN, set(on_file))
        r['session'] = SID
        return r, json.dumps(r).encode()

    def test_unlisted_line_refuses_to_sign(self):
        # The rehearsal failure: a sibling launch canary with no matching record, and the signer signed anyway.
        r, raw = self.review([line('17:49:58', '/usr/bin/true tm09-' + OWN), line('17:49:34', '/usr/bin/true tm09-' + OTHER)])
        self.assertEqual(len(r['unlisted']), 1)
        with self.assertRaises(Refused):
            review_body(r, SID, 8801, OWN, CONTROL, b'{}', raw)

    def test_tampered_or_foreign_review_refuses(self):
        r, raw = self.review([line('17:49:58', '/usr/bin/true tm09-' + OWN)])
        for bad in (dict(r, entries=2), dict(r, session='TM09-' + 'f' * 32), dict(r, nonce=OTHER), {k: v for k, v in r.items() if k != 'unlisted'}):
            with self.assertRaises(Refused):
                review_body(bad, SID, 8801, OWN, CONTROL, b'{}', raw)

    def test_clean_review_signs_all_flags(self):
        r, raw = self.review([line('17:49:58', '/usr/bin/true tm09-' + OWN), line('17:49:34', '/usr/bin/true tm09-' + OTHER)], {OTHER})
        body = review_body(r, SID, 8801, OWN, CONTROL, b'{"phase":"stopped"}', raw)
        self.assertTrue(body['sudo_allowlist_reviewed'] and body['listener_stopped'] and body['raw_copies_denied'])
        self.assertEqual((body['session'], body['nonce'], body['port']), (SID, OWN, 8801))


class LaunchBoundary(unittest.TestCase):
    def proof(self, **kw):
        return json.dumps(dict(dict(session=SID, port=8801, nonce=OWN, matched_canary=True, prefix_unchanged=True,
                                    size_before=10, size_after=20), **kw)).encode()

    def test_good_proof(self):
        self.assertTrue(launch_body(SID, 8801, self.proof())['canary_observed'])

    def test_bad_proofs_refuse(self):
        for kw in (dict(matched_canary=False), dict(prefix_unchanged=False), dict(size_after=10), dict(port=8802), dict(nonce='x')):
            with self.assertRaises(Refused):
                launch_body(SID, 8801, self.proof(**kw))


if __name__ == '__main__':
    unittest.main()
