#!/usr/bin/env python3
"""Forward product-status watcher for Coinbase Exchange and Kraken USD spot pairs.

Polls documented public REST endpoints at >= 300 second intervals, writes compact
append-only status transitions plus one daily UTC snapshot off-repo, and updates
an atomic heartbeat file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

COINBASE_PRODUCTS_URL = "https://api.exchange.coinbase.com/products"
KRAKEN_ASSET_PAIRS_URL = "https://api.kraken.com/0/public/AssetPairs"
DEFAULT_OUT_DIR = Path("/home/user/workspace/rig/data/status_forward")
MIN_INTERVAL_SEC = 300
USER_AGENT = "dt-product-status-watcher/0.1"


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_json(url: str, timeout_sec: int = 20) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_coinbase_products(raw: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in raw:
        if item.get("quote_currency") != "USD":
            continue
        pair_id = str(item.get("id", "")).strip()
        if not pair_id:
            continue
        out[pair_id] = {
            "base": str(item.get("base_currency", "")).strip(),
            "status": str(item.get("status", "")),
            "limit_only": bool(item.get("limit_only", False)),
            "cancel_only": bool(item.get("cancel_only", False)),
            "post_only": bool(item.get("post_only", False)),
            "trading_disabled": bool(item.get("trading_disabled", False)),
            "auction_mode": bool(item.get("auction_mode", False)),
            "status_message": str(item.get("status_message", "") or ""),
        }
    return out


def normalize_kraken_asset_pairs(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    errors = raw.get("error") or []
    if errors:
        raise RuntimeError(f"Kraken API returned error: {errors}")
    result = raw.get("result") or {}
    out: dict[str, dict[str, Any]] = {}
    for pair_key, item in result.items():
        if not isinstance(item, dict):
            continue
        if item.get("quote") not in ("ZUSD", "USD"):
            continue
        out[str(pair_key)] = {
            "base": str(item.get("base", "")),
            "altname": str(item.get("altname", "")),
            "wsname": str(item.get("wsname", "")),
            "status": str(item.get("status", "")),
        }
    return out


def diff_venue_state(
    venue: str,
    prev: dict[str, dict[str, Any]],
    curr: dict[str, dict[str, Any]],
    ts_utc: str,
) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    all_pairs = sorted(set(prev.keys()) | set(curr.keys()))
    for pair in all_pairs:
        old_val = prev.get(pair)
        new_val = curr.get(pair)
        if old_val is None and new_val is not None:
            transitions.append(
                {
                    "ts_utc": ts_utc,
                    "venue": venue,
                    "pair": pair,
                    "base": new_val.get("base", ""),
                    "event_type": "added",
                    "prev": None,
                    "curr": new_val,
                }
            )
        elif old_val is not None and new_val is None:
            transitions.append(
                {
                    "ts_utc": ts_utc,
                    "venue": venue,
                    "pair": pair,
                    "base": old_val.get("base", ""),
                    "event_type": "removed",
                    "prev": old_val,
                    "curr": None,
                }
            )
        elif old_val != new_val:
            transitions.append(
                {
                    "ts_utc": ts_utc,
                    "venue": venue,
                    "pair": pair,
                    "base": (new_val or {}).get("base", ""),
                    "event_type": "changed",
                    "prev": old_val,
                    "curr": new_val,
                }
            )
    return transitions


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp_path, path)


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")
        fh.flush()


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {
            "last_snapshot_date": None,
            "polls_ok": 0,
            "polls_err": 0,
            "transitions_total": 0,
            "venues": {},
        }
    return json.loads(state_path.read_text(encoding="utf-8"))


def run_single_poll(
    out_dir: Path,
    interval_sec: int,
    fetcher: Callable[[str], Any] = fetch_json,
    now_fn: Callable[[], str] = utc_now_iso,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / "state.json"
    transitions_path = out_dir / "transitions.jsonl"
    snapshots_path = out_dir / "daily_snapshots.jsonl"
    heartbeat_path = out_dir / "heartbeat.json"

    state = load_state(state_path)
    ts_utc = now_fn()
    utc_date = ts_utc[:10]

    last_error = None
    cb_norm: dict[str, dict[str, Any]] | None = None
    kr_norm: dict[str, dict[str, Any]] | None = None

    try:
        cb_raw = fetcher(COINBASE_PRODUCTS_URL)
        cb_norm = normalize_coinbase_products(cb_raw)
        kr_raw = fetcher(KRAKEN_ASSET_PAIRS_URL)
        kr_norm = normalize_kraken_asset_pairs(kr_raw)
    except Exception as exc:
        last_error = f"{type(exc).__name__}: {exc}"
        state["polls_err"] = int(state.get("polls_err", 0)) + 1
        atomic_write_json(state_path, state)
        hb = {
            "ts_utc": ts_utc,
            "pid": os.getpid(),
            "interval_sec": interval_sec,
            "ok": False,
            "polls_ok": state["polls_ok"],
            "polls_err": state["polls_err"],
            "transitions_total": state.get("transitions_total", 0),
            "coinbase_usd_count": len(state.get("venues", {}).get("coinbase", {})),
            "kraken_usd_count": len(state.get("venues", {}).get("kraken", {})),
            "last_snapshot_date": state.get("last_snapshot_date"),
            "last_error": last_error,
        }
        atomic_write_json(heartbeat_path, hb)
        return hb

    venues = state.setdefault("venues", {})
    new_transitions: list[dict[str, Any]] = []
    if "coinbase" in venues:
        new_transitions.extend(diff_venue_state("coinbase", venues["coinbase"], cb_norm, ts_utc))
    if "kraken" in venues:
        new_transitions.extend(diff_venue_state("kraken", venues["kraken"], kr_norm, ts_utc))

    append_jsonl(transitions_path, new_transitions)

    snapshot_written = False
    if state.get("last_snapshot_date") != utc_date:
        append_jsonl(
            snapshots_path,
            [
                {
                    "ts_utc": ts_utc,
                    "utc_date": utc_date,
                    "coinbase": cb_norm,
                    "kraken": kr_norm,
                }
            ],
        )
        state["last_snapshot_date"] = utc_date
        snapshot_written = True

    venues["coinbase"] = cb_norm
    venues["kraken"] = kr_norm
    state["polls_ok"] = int(state.get("polls_ok", 0)) + 1
    state["transitions_total"] = int(state.get("transitions_total", 0)) + len(new_transitions)
    atomic_write_json(state_path, state)

    hb = {
        "ts_utc": ts_utc,
        "pid": os.getpid(),
        "interval_sec": interval_sec,
        "ok": True,
        "polls_ok": state["polls_ok"],
        "polls_err": state.get("polls_err", 0),
        "transitions_this_poll": len(new_transitions),
        "transitions_total": state["transitions_total"],
        "snapshot_written": snapshot_written,
        "last_snapshot_date": state["last_snapshot_date"],
        "coinbase_usd_count": len(cb_norm),
        "kraken_usd_count": len(kr_norm),
        "last_error": None,
    }
    atomic_write_json(heartbeat_path, hb)
    return hb


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forward product-status watcher for Coinbase and Kraken USD pairs.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Off-repo output directory.")
    parser.add_argument(
        "--interval-sec",
        type=int,
        default=MIN_INTERVAL_SEC,
        help=f"Polling interval in seconds (minimum {MIN_INTERVAL_SEC}).",
    )
    parser.add_argument("--once", action="store_true", help="Run a single poll and exit.")
    args = parser.parse_args(argv)
    if args.interval_sec < MIN_INTERVAL_SEC:
        parser.error(f"--interval-sec must be >= {MIN_INTERVAL_SEC} (got {args.interval_sec})")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stop = False

    def _handle_signal(_signum: int, _frame: Any) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    while True:
        hb = run_single_poll(args.out_dir, args.interval_sec)
        print(json.dumps(hb, sort_keys=True), flush=True)
        if args.once or stop:
            break
        slept = 0
        while slept < args.interval_sec and not stop:
            step = min(5, args.interval_sec - slept)
            time.sleep(step)
            slept += step
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
