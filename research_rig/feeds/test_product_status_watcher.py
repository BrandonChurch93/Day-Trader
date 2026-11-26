"""Synthetic tests for product_status_watcher.py (no network calls)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research_rig.feeds import product_status_watcher as psw


def _cb_payload(status: str = "online", limit_only: bool = False, include_extra: bool = False) -> list[dict]:
    items = [
        {
            "id": "SOL-USD",
            "base_currency": "SOL",
            "quote_currency": "USD",
            "status": status,
            "limit_only": limit_only,
            "cancel_only": False,
            "post_only": False,
            "trading_disabled": False,
            "auction_mode": False,
            "status_message": "",
        },
        {
            "id": "SOL-EUR",
            "base_currency": "SOL",
            "quote_currency": "EUR",
            "status": "online",
            "limit_only": False,
            "cancel_only": False,
            "post_only": False,
            "trading_disabled": False,
            "auction_mode": False,
            "status_message": "",
        },
    ]
    if include_extra:
        items.append(
            {
                "id": "NEW-USD",
                "base_currency": "NEW",
                "quote_currency": "USD",
                "status": "online",
                "limit_only": False,
                "cancel_only": False,
                "post_only": False,
                "trading_disabled": False,
                "auction_mode": False,
                "status_message": "",
            }
        )
    return items


def _kr_payload(status: str = "online", drop_pair: bool = False) -> dict:
    result = {
        "SOLEUR": {"altname": "SOLEUR", "wsname": "SOL/EUR", "base": "SOL", "quote": "ZEUR", "status": "online"}
    }
    if not drop_pair:
        result["SOLUSD"] = {
            "altname": "SOLUSD",
            "wsname": "SOL/USD",
            "base": "SOL",
            "quote": "ZUSD",
            "status": status,
        }
    return {"error": [], "result": result}


class TestProductStatusWatcher(unittest.TestCase):
    def test_minimum_interval_enforced(self) -> None:
        with self.assertRaises(SystemExit):
            psw.parse_args(["--interval-sec", "60"])
        args = psw.parse_args(["--interval-sec", "300", "--once"])
        self.assertEqual(args.interval_sec, 300)
        self.assertTrue(args.once)

    def test_transitions_and_daily_snapshot_budget(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)

            # Poll 1: initial baseline writes 1 daily snapshot and 0 transitions
            def fetch1(url: str):
                return _cb_payload() if "coinbase" in url else _kr_payload()

            hb1 = psw.run_single_poll(out_dir, 300, fetcher=fetch1, now_fn=lambda: "2026-11-26T08:00:00Z")
            self.assertTrue(hb1["ok"])
            self.assertEqual(hb1["coinbase_usd_count"], 1)
            self.assertEqual(hb1["kraken_usd_count"], 1)
            self.assertEqual(hb1["transitions_this_poll"], 0)
            self.assertTrue(hb1["snapshot_written"])
            self.assertFalse((out_dir / "transitions.jsonl").exists())
            self.assertEqual(len((out_dir / "daily_snapshots.jsonl").read_text().splitlines()), 1)

            # Poll 2 (same UTC day, unchanged): 0 transitions, 0 new snapshots
            hb2 = psw.run_single_poll(out_dir, 300, fetcher=fetch1, now_fn=lambda: "2026-11-26T08:05:00Z")
            self.assertEqual(hb2["transitions_this_poll"], 0)
            self.assertFalse(hb2["snapshot_written"])
            self.assertEqual(len((out_dir / "daily_snapshots.jsonl").read_text().splitlines()), 1)

            # Poll 3 (same UTC day, changes: CB SOL-USD limit_only, CB NEW-USD added, KR SOLUSD removed)
            def fetch3(url: str):
                if "coinbase" in url:
                    return _cb_payload(limit_only=True, include_extra=True)
                return _kr_payload(drop_pair=True)

            hb3 = psw.run_single_poll(out_dir, 300, fetcher=fetch3, now_fn=lambda: "2026-11-26T08:10:00Z")
            self.assertEqual(hb3["transitions_this_poll"], 3)
            self.assertEqual(hb3["transitions_total"], 3)
            self.assertFalse(hb3["snapshot_written"])
            lines = [json.loads(line) for line in (out_dir / "transitions.jsonl").read_text().splitlines()]
            events = {(r["venue"], r["pair"], r["event_type"]) for r in lines}
            self.assertEqual(
                events,
                {
                    ("coinbase", "SOL-USD", "changed"),
                    ("coinbase", "NEW-USD", "added"),
                    ("kraken", "SOLUSD", "removed"),
                },
            )

            # Poll 4 (next UTC day, unchanged): 0 transitions, 1 new daily snapshot
            hb4 = psw.run_single_poll(out_dir, 300, fetcher=fetch3, now_fn=lambda: "2026-11-27T00:05:00Z")
            self.assertEqual(hb4["transitions_this_poll"], 0)
            self.assertTrue(hb4["snapshot_written"])
            self.assertEqual(len((out_dir / "daily_snapshots.jsonl").read_text().splitlines()), 2)

    def test_error_updates_heartbeat_without_losing_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)

            def fetch_ok(url: str):
                return _cb_payload() if "coinbase" in url else _kr_payload()

            def fetch_fail(_url: str):
                raise OSError("network unreachable")

            psw.run_single_poll(out_dir, 300, fetcher=fetch_ok, now_fn=lambda: "2026-11-26T08:00:00Z")
            hb_err = psw.run_single_poll(out_dir, 300, fetcher=fetch_fail, now_fn=lambda: "2026-11-26T08:05:00Z")
            self.assertFalse(hb_err["ok"])
            self.assertEqual(hb_err["polls_ok"], 1)
            self.assertEqual(hb_err["polls_err"], 1)
            self.assertIn("OSError", hb_err["last_error"])


if __name__ == "__main__":
    unittest.main()
