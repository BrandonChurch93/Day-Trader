"""Allowlisted Binance global spot ZIP timestamp census. Never parse a price."""
import calendar
import hashlib
import json
import os
import stat
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

COINS = "AAVE ADA AVAX BCH BNB BTC DOGE DOT ENA ETH HBAR HYPE LINK LTC NEAR ONDO PAXG PEPE SHIB SOL SUI XLM XRP ZEC".split()
ROOTS = ("replay_13", "replay_22", "replay_16")
MONTHS = [(y, m) for y in range(2020, 2024) for m in range(1, 13)]


def read_snapshot(root, rel):
    """Open an exact regular file without following redirects, then read it once."""
    root, rel = Path(root), Path(rel)
    if root.anchor != "/" or rel.is_absolute() or not rel.parts or ".." in (*root.parts, *rel.parts):
        raise ValueError("invalid custody path")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent = os.open("/", flags)
    try:
        for part in (*root.parts[1:], *rel.parts[:-1]):
            child = os.open(part, flags, dir_fd=parent)
            os.close(parent)
            parent = child
        fd = os.open(rel.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as wire:
            if not stat.S_ISREG(os.fstat(wire.fileno()).st_mode):
                raise ValueError("custody input is not a regular file")
            return wire.read()
    finally:
        os.close(parent)


def census(root):
    out = {}
    for coin in COINS:
        months = []
        for y, m in MONTHS:
            tag = f"{y}-{m:02}"
            filename = f"{coin}USDT-1h-{tag}"
            rel = f"archives/data/spot/monthly/klines/{coin}USDT/1h/{filename}.zip"
            candidate = None
            for r in ROOTS:
                try:
                    snapshot = read_snapshot(root, Path(r) / rel)
                except FileNotFoundError:
                    continue
                candidate = f"{r}/{rel}"
                break
            if candidate is None:
                months.append({"month": tag, "missing_archive": True})
                continue
            digest = hashlib.sha256(snapshot).hexdigest()
            first = int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp())
            expected = calendar.monthrange(y, m)[1] * 24
            stamps = []
            with ZipFile(BytesIO(snapshot)) as archive, archive.open(filename + ".csv") as stream:
                for line in stream:
                    # First field only. Do not parse, store or display OHLC or volume.
                    t = int(line.split(b",", 1)[0])
                    if t % 3_600_000:
                        raise ValueError("misaligned hour")
                    stamps.append(t // 1000)
            unique = set(stamps)
            if len(unique) != len(stamps) or any(not first <= t < first + expected * 3600 for t in unique):
                raise ValueError("duplicate or spill outside named month")
            months.append({"month": tag, "path": candidate, "sha256": digest,
                           "rows": len(unique), "expected": expected, "first_utc_seconds": min(unique),
                           "last_utc_seconds": max(unique), "complete": len(unique) == expected})
        start = next((i for i, row in enumerate(months) if row.get("complete")), None)
        after = [] if start is None else months[start:]
        kept = bool(after and after[-1].get("complete") and
                    not any(row.get("missing_archive") for row in after))
        out[coin] = {"admit": kept, "first_full_month": None if start is None else months[start]["month"],
                     "archive_gaps_after_start": [r["month"] for r in after if r.get("missing_archive")],
                     "missing_hours_inside_available_months": sum(r.get("expected", 0) - r.get("rows", 0) for r in after),
                     "files": [r for r in after if not r.get("missing_archive")] if kept else []}
    return out


if __name__ == "__main__":
    print(json.dumps(census(Path(sys.argv[1]).absolute()), sort_keys=True, separators=(",", ":")))
