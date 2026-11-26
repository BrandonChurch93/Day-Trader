"""Collect the selected SIP bar mode. Never calculate returns or inspect OHLC."""
import argparse
from datetime import date, datetime, time, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from urllib.parse import urlencode

import common_25 as C

HERE = Path(__file__).resolve().parent
DATA = Path("/home/user/workspace/rig/data/replay_25")
HANDLE = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
API = "https://data.alpaca.markets/v2/stocks/bars"
DRAFT_FILES = ("PREREG_25_treasury_month_end.md", "calendar_25.json", "common_25.py",
               "fetch_25.py", "score_25.py", "test_25.py")
RAW = "raw_dated_distributions"
SHA = re.compile(r"[0-9a-f]{64}")


def digest(payload):
    return sha256(payload).hexdigest()


def encode(row):
    return (json.dumps(row, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def check_pin(pin):
    C.need(isinstance(pin, str) and SHA.fullmatch(pin) is not None, "P25_PIN")


def pinned(path, pin, private=False):
    check_pin(pin)
    st = path.stat()
    C.need(path.is_file() and not path.is_symlink() and st.st_size <= 12 * 1024 * 1024, "P25_FILE")
    if private:
        C.need(st.st_uid == os.geteuid() and not st.st_mode & 0o077, "P25_PRIVATE_FILE")
    payload = path.read_bytes()
    C.need(digest(payload) == pin, "P25_PIN")
    return payload


def draft(pin, require_frozen=True):
    d = json.loads(pinned(HERE / "PINNED.json", pin))
    C.need(set(d) == set(DRAFT_FILES), "P25_DRAFT")
    for name in DRAFT_FILES:
        check_pin(d[name])
    out = {name: pinned(HERE / name, d[name]) for name in DRAFT_FILES}
    if require_frozen:
        status = [line for line in out[DRAFT_FILES[0]].splitlines() if line.startswith(b"Status ")]
        C.need(status == [b"Status FROZEN."], "P25_NOT_FROZEN")
    return C.check_calendar(json.loads(out["calendar_25.json"]))


def private_dir(path):
    st = path.stat()
    C.need(path.is_dir() and not path.is_symlink() and st.st_uid == os.geteuid()
           and not st.st_mode & 0o077, "P25_PRIVATE_DIR")


def get(url):
    # Do not print or retain stderr, URL pagination tokens, headers or raw errors.
    cmd = ["pplx", "credentials", "run", HANDLE, "--", "curl", "--silent",
           "--fail", "--proto", "=https", "--max-time", "90", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                       check=False, timeout=110)
    C.need(r.returncode == 0 and len(r.stdout) <= 8 * 1024 * 1024, "P25_ALPACA")
    return json.loads(r.stdout)


def fetch(symbol, transport=get):
    # End-stamp allows the entire last New York session but never Nov 25.
    query = dict(symbols=symbol, timeframe="1Day", start=C.BAR_FROM.isoformat(),
                 end=f"{C.DATA_END.isoformat()}T23:59:59-05:00", adjustment="raw",
                 limit=10000, feed="sip", sort="asc")
    rows, seen = [], set()
    for _ in range(16):
        page = transport(API + "?" + urlencode(query))
        bars = page["bars"]
        C.need(isinstance(bars, dict) and set(bars) <= {symbol}, "P25_ALPACA_SCHEMA")
        rows.extend(bars.get(symbol, []))
        token = page["next_page_token"]
        if token is None:
            return rows
        C.need(isinstance(token, str) and token and len(token) < 2048 and token not in seen,
               "P25_ALPACA_PAGE")
        seen.add(token)
        query["page_token"] = token
    raise C.Refused("P25_ALPACA_PAGE")


def collect(args):
    check_pin(args.raw_actions_sha256)
    days = draft(args.approved_draft_sha256)
    actions = pinned(args.raw_actions, args.raw_actions_sha256, private=True)
    C.check_actions(json.loads(actions), days)
    DATA.mkdir(mode=0o700, exist_ok=True)
    private_dir(DATA)
    final = DATA / "inputs"
    C.need(not final.exists() and not final.is_symlink()
           and not os.path.lexists(DATA / "score_25.lock") and not os.path.lexists(DATA / "results_25.json"),
           "P25_COLLECTION_EXISTS")
    with TemporaryDirectory(prefix=".collect_", dir=DATA) as temp:
        batch = Path(temp) / "inputs"
        batch.mkdir(mode=0o700)
        payloads = {}
        for symbol in C.SYMBOLS:
            rows = fetch(symbol)
            C.check_bar_clocks(rows, days)
            payloads[symbol + ".json"] = encode(rows)
        payloads["cash_actions.json"] = actions
        index = {
            "schema": 1, "mode": RAW, "feed": "sip", "adjustment": "raw", "start": str(C.BAR_FROM),
            "end": str(C.DATA_END), "collected_utc": datetime.now(timezone.utc).isoformat(),
            "draft_sha256": args.approved_draft_sha256, "files": {k: digest(v) for k, v in payloads.items()},
        }
        manifest = encode(index)
        for name, raw in (payloads | {"manifest.json": manifest}).items():
            with (batch / name).open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        # An existing published input directory is never empty, so rename will not replace it.
        batch.rename(final)
    print("P25_INPUT_MANIFEST_SHA256", digest(manifest), "sessions", len(days), "mode", RAW)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-draft-sha256", required=True)
    parser.add_argument("--raw-actions", type=Path, required=True)
    parser.add_argument("--raw-actions-sha256", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        collect(args)
    except C.Refused as exc:
        parser.exit(2, f"{exc}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, subprocess.SubprocessError):
        parser.exit(2, "P25_COLLECT_REFUSED\n")


if __name__ == "__main__":
    main()
