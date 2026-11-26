"""Synthetic-only tests; never open the research store or contact a network."""

import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import hashlib
from pathlib import Path
import random
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from research_rig.feeds import announcements as feed


ZERO = datetime(2023, 1, 1, tzinfo=timezone.utc)
BINANCE_ID = 'ab' * 16


def at(seconds):
    return int(ZERO.timestamp()) + seconds


def packet(offset, html, venue='binance', path=None):
    capture = ZERO + timedelta(seconds=offset)
    host, paths = feed.INDEXES[venue]
    url = 'https://' + host + (path or paths[0])
    timestamp = capture.strftime('%Y%m%d%H%M%S')
    body = html.encode('utf-8')
    return feed.IndexCapture(
        venue, url, timestamp, base64.b32encode(hashlib.sha1(body).digest()).decode(),
        f'https://web.archive.org/web/{timestamp}id_/{url}', 200,
        format_datetime(capture, usegmt=True), 'text/html; charset=utf-8', body,
    )


def anchor(path, headline):
    return f'<main><a href="{path}">{headline}</a></main>'


class AnnouncementsTest(unittest.TestCase):
    def setUp(self):
        root = TemporaryDirectory()
        self.addCleanup(root.cleanup)
        proxy = patch.object(feed, 'STORE', Path(root.name) / 'private')
        proxy.start()
        self.addCleanup(proxy.stop)

    def test_earliest_exact_evidence_and_wake_boundaries(self):
        first = packet(0, anchor(f'/en/support/announcement/{BINANCE_ID}?tracking=do-not-store',
                                 'Binance Will List TEST &amp; DEMO'))
        edit = packet(850, anchor(f'/en/support/announcement/detail/{BINANCE_ID}',
                                  'Binance Will List DEMO Instead'))
        feed.stage_index(edit)
        self.assertEqual(feed.get_announcements(at(1149)), [])
        feed.stage_index(first)
        feed.stage_index(edit)
        feed.stage_index(first)
        self.assertEqual(feed.get_announcements(at(-1)), [])
        self.assertEqual(feed.get_announcements(at(0)), [])
        self.assertEqual(feed.get_announcements(at(299)), [])
        self.assertEqual(feed.get_announcements(at(300), after_utc=at(300)), [])
        expected = feed.get_announcements(at(300), after_utc=at(299))
        self.assertEqual(expected, feed.get_announcements(at(10000)))
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0], dict(exchange='binance', notice_key=BINANCE_ID, kind='listing',
                                          capture_ts=at(0), known_at=at(300), digest=first.digest,
                                          capture_url=first.response_url,
                                          notice_url=f'https://www.binance.com/en/support/announcement/{BINANCE_ID}',
                                          excerpt='Binance Will List TEST & DEMO'))

    def test_exact_replay_and_digest_fail_closed(self):
        capture = packet(0, anchor(f'/en/support/announcement/detail/{BINANCE_ID}', 'Binance Will List TEST'))
        for modified in (
            replace(capture, response_url=capture.original),
            replace(capture, response_url=capture.response_url.replace(capture.timestamp, '20230102000000')),
            replace(capture, http_status=302),
            replace(capture, http_status=429),
            replace(capture, body=capture.body + b' '),
            replace(capture, content_type='application/json'),
            replace(capture, memento_datetime='Sun, 02 Jan 2023 00:00:00 GMT'),
            replace(capture, memento_datetime=''),
            replace(capture, exchange='upbit'),
            replace(capture, original='https://example.org/blog'),
            replace(capture, timestamp='20230132000000'),
            packet(-4 * 366 * 86400, '<html></html>'),
        ):
            with self.subTest(change=modified.response_url), self.assertRaises(ValueError):
                feed.stage_index(modified)
            self.assertFalse(feed.STORE.exists())

    def test_skip_shells_hidden_external_generic_and_ambiguous(self):
        headline = 'Binance Will List TEST'
        path = f'/en/support/announcement/detail/{BINANCE_ID}'
        valid = anchor(path, headline)
        text = ''.join((f'<nav>{valid}</nav>', f'<script>{valid}</script>', f'<template>{valid}</template>',
                        f'<div hidden>{valid}</div>', f'<div aria-hidden="true">{valid}</div>',
                        f'<div style="display:none">{valid}</div>', anchor('https://other.example' + path, headline),
                        anchor('https://www.binance.com.evil.example' + path, headline),
                        anchor('/en/support/announcement', headline), anchor(path, 'How to list an asset'),
                        anchor(path, 'Binance Will List DEMO and add a Monitoring Tag'),
                        '<div id="root"></div>'))
        self.assertEqual(feed.stage_index(packet(2, text)), 0)
        self.assertFalse(feed.STORE.exists())
        with self.assertRaises(sqlite3.OperationalError) as error:
            feed.get_announcements(at(300))
        self.assertIn('unable to open database', str(error.exception))

    def test_all_venues_and_taxonomy(self):
        cases = (
            ('binance', f'/en/support/announcement/detail/{BINANCE_ID}',
             'Binance will add a Monitoring Tag to FOO', 'monitoring_tag'),
            ('coinbase', '/blog/fake-asset-now-live', 'TEST is now available for trading', 'listing'),
            ('kraken', '/product/asset-listings/test', 'FAKE token is now available for trading', 'listing'),
            ('okx', '/help/okx-delist-demo', 'OKX to delist DEMO trading pairs', 'delisting'),
            ('bybit', '/en/article/temporary-notice', 'Bybit to temporarily suspend spot trading for DEMO', 'trading_halt'),
        )
        for venue, path, text, kind in cases:
            self.assertEqual(feed.stage_index(packet(0, anchor(path, text), venue)), 1)
        self.assertEqual({r['exchange']: r['kind'] for r in feed.get_announcements(at(300))},
                         {venue: kind for venue, _, _, kind in cases})

    def test_headline_variants_and_link_bounds(self):
        samples = (
            ('Exchange New Listing: SYNTH', 'listing'),
            ('Removal of Selected Spot Trading Pairs', 'delisting'),
            ('SYNTH Trading is Temporarily Suspended', 'trading_halt'),
            ('Exchange New Listings Process Explained', None),
        )
        html = ''.join(anchor(f'/en/article/test-{i}', title) for i, (title, _) in enumerate(samples))
        html += anchor('/en/article/' + 'x' * feed.MAX_HREF, 'Exchange Will List DEMO')
        self.assertEqual(feed.stage_index(packet(0, html, 'bybit')), 3)
        self.assertEqual({r['excerpt']: r['kind'] for r in feed.get_announcements(at(300))},
                         dict((title, kind) for title, kind in samples if kind))

    def test_same_timestamp_conflict_is_transactional(self):
        path = f'/en/support/announcement/detail/{BINANCE_ID}'
        first = packet(0, anchor(path, 'Binance Will List TEST'))
        conflict = packet(0, anchor(f'/en/support/announcement/detail/{"0" * 32}', 'Binance Will List EXTRA') +
                          anchor(path, 'Binance Will List A Different Token'))
        feed.stage_index(first)
        with self.assertRaisesRegex(ValueError, 'conflicting evidence'):
            feed.stage_index(conflict)
        results = feed.get_announcements(at(300))
        self.assertEqual([r['excerpt'] for r in results], ['Binance Will List TEST'])

    def test_equal_timestamp_aliases_choose_whole_deterministic_provenance(self):
        direct = f'/en/support/announcement/{BINANCE_ID}'
        detail = f'/en/support/announcement/detail/{BINANCE_ID}'
        title = 'Binance Will List TEST'
        with_aliases = packet(0, anchor(detail, title) + anchor(direct, title))
        with_slash = packet(0, anchor(detail, title), path='/en/support/announcement/')
        self.assertEqual(feed.stage_index(with_slash), 1)
        self.assertEqual(feed.stage_index(with_aliases), 1)
        result, = feed.get_announcements(at(300))
        self.assertEqual(result['capture_url'], with_aliases.response_url)
        self.assertEqual(result['digest'], with_aliases.digest)
        self.assertEqual(result['notice_url'], 'https://www.binance.com' + direct)
        with patch.object(feed, 'STORE', feed.STORE.parent / 'other'):
            feed.stage_index(with_aliases)
            feed.stage_index(with_slash)
            self.assertEqual(feed.get_announcements(at(300)), [result])

    def test_200_seeded_random_wakes_no_future_and_complete_eligible_set(self):
        rng = random.Random(81725)
        cases = {}
        for i in range(65):
            key = f'{i:032x}'
            first = rng.randrange(0, 60_000)
            later = first + rng.randrange(1, 5000)
            path = f'/en/support/announcement/detail/{key}'
            feed.stage_index(packet(later, anchor(path, f'Binance Will List LATER{i}')))
            feed.stage_index(packet(first, anchor(path, f'Binance Will List SYNTH{i}')))
            cases[key] = at(first), f'Binance Will List SYNTH{i}'
        for _ in range(200):
            wake = at(rng.randrange(-1000, 65_000))
            got = feed.get_announcements(wake, exchange='binance')
            want = {key: (ts, text) for key, (ts, text) in cases.items() if ts + 300 <= wake}
            self.assertEqual({r['notice_key']: (r['capture_ts'], r['excerpt']) for r in got}, want)
            self.assertEqual(len(got), len(want))
            for row in got:
                self.assertTrue(row['capture_ts'] <= row['known_at'] <= wake)
                self.assertEqual(row['known_at'] - row['capture_ts'], 300)

    def test_insufficient_disk_stops_before_store_creation(self):
        capture = packet(0, anchor(f'/en/support/announcement/detail/{BINANCE_ID}', 'Binance Will List TEST'))
        with patch.object(feed.shutil, 'disk_usage', return_value=SimpleNamespace(free=feed.MIN_FREE)):
            with self.assertRaisesRegex(OSError, 'leave 1 GiB free'):
                feed.stage_index(capture)
        self.assertFalse(feed.STORE.exists())

    def test_store_permissions_and_no_payload_or_query_persistence(self):
        body_marker = 'archived body content that must not be written'
        private_query = 'url parameter that must not be written'.replace(' ', '-')
        path = f'/en/support/announcement/detail/{BINANCE_ID}?tracking={private_query}'
        capture = packet(0, f'<div>{body_marker}</div>' + anchor(path, 'Binance Will List TEST'))
        feed.stage_index(capture)
        db = feed.STORE / feed.DB_NAME
        self.assertEqual(db.stat().st_mode & 0o077, 0)
        self.assertEqual(feed.STORE.stat().st_mode & 0o077, 0)
        file_before = db.read_bytes()
        self.assertNotIn(body_marker.encode(), file_before)
        self.assertNotIn(private_query.encode(), file_before)
        self.assertEqual(len(feed.get_announcements(at(300))), 1)
        self.assertEqual(db.read_bytes(), file_before)
        self.assertEqual(list(feed.STORE.iterdir()), [db])


if __name__ == '__main__':
    unittest.main()
