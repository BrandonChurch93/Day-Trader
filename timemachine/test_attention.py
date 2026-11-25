"""Invented rows only. No vendor files or replay returns are read."""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest

try:
    from .attention import SCHEMA, get_attention
except ImportError:
    from attention import SCHEMA, get_attention


class AttentionTest(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="tm attention ")
        self.addCleanup(scratch.cleanup)
        self.path = Path(scratch.name) / "fixture.sqlite"
        self.now = int(datetime(2025, 8, 5, tzinfo=timezone.utc).timestamp())
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.executescript(SCHEMA)
            conn.executemany("INSERT INTO attention VALUES (?, ?, ?, ?, ?, ?)", [
                ("one", "DOGE", self.now - 25, 1, self.now - 5, "original"),
                ("one", "DOGE", self.now - 25, 2, self.now, "assumed_lag"),
                ("one", "DOGE", self.now - 25, 3, self.now + 1, "original"),
                ("one", "DOGE", self.now, 4, self.now + 1, "assumed_lag"),
                ("one", "SHIB", self.now, 5, self.now, "original"),
                ("one", "DOGE", self.now - 86400, 6, self.now, "original"),
                ("two", "DOGE", self.now - 1, 0, self.now - 1, "assumed_lag"),
                ("three", "DOGE", self.now, 7, self.now, "capture_only"),
            ])

    def read(self, as_of, coin="DOGE", window=1):
        return get_attention(coin, as_of, window, db_path=self.path)

    def test_exclude_one_second_after_cutoff(self):
        rows = self.read("2025-08-04T20:00:00-04:00", "doge-usd")
        self.assertEqual([r["value"] for r in rows], [2, 0])
        self.assertTrue(all(r["known_at_utc"] <= self.now for r in rows))

    def test_revision_does_not_replace_earlier_vintage(self):
        self.assertEqual([r["value"] for r in self.read(self.now - 1)], [1, 0])
        self.assertEqual([r["value"] for r in self.read(self.now + 1)], [3, 0, 4])

    def test_missing_store_is_not_created(self):
        missing = self.path.with_name("missing.sqlite")
        with self.assertRaises(sqlite3.OperationalError):
            get_attention("DOGE", self.now, 1, db_path=missing)
        self.assertFalse(missing.exists())

    def test_minimum_vintage(self):
        def values(min_vintage):
            return [r["value"] for r in get_attention(
                "DOGE", self.now, 1, db_path=self.path, min_vintage=min_vintage)]

        self.assertEqual(values("original"), [1])
        self.assertEqual(values("assumed_lag"), [2, 0])
        self.assertEqual(values("capture_only"), [2, 0, 7])
        with self.assertRaises(ValueError):
            values("unknown")

    def test_half_open_lookback_and_bad_times(self):
        self.assertEqual(self.read(self.now, window=0), [])
        self.assertEqual([r["value"] for r in self.read(self.now, window=2)], [6, 2, 0])
        with self.assertRaises(ValueError):
            self.read("2025-08-05T00:00:00")
        with self.assertRaises(ValueError):
            self.read(self.now, window=-1)


if __name__ == "__main__":
    unittest.main()
