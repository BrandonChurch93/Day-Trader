"""The Plan 70 vault inventory: interpret only opening and closing clocks."""
import calendar
import hashlib
import json
from datetime import datetime, timezone
from io import BytesIO
from zipfile import ZipFile

from coverage_70 import HOUR_MS, ROOTS, has_hour_close, read_snapshot
from sweep_70 import ALLOWED, CUSTODY

MONTHS = tuple(f"{y}-{m:02}" for y in range(2024, 2027) for m in range(1, 13)
               if (y, m) <= (2026, 10))
MANIFEST = "sweep_70/vault_coverage.json"


def month_info(tag):
    if tag not in MONTHS:
        raise ValueError("not a vault month")
    y, m = map(int, tag.split("-"))
    start = int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp())
    return start, calendar.monthrange(y, m)[1] * 24, 1 if y == 2024 else 1000


def archive_info(coin, tag):
    if coin not in ALLOWED or tag not in MONTHS:
        raise ValueError("not in vault roster or calendar")
    name = f"{coin}USDT-1h-{tag}"
    rel = f"archives/data/spot/monthly/klines/{coin}USDT/1h/{name}.zip"
    return name, tuple(f"{r}/{rel}" for r in ROOTS)


def month_record(root, coin, tag):
    name, paths = archive_info(coin, tag)
    for path in paths:
        try:
            raw = read_snapshot(root, path)
        except FileNotFoundError:
            continue
        break
    else:
        return {"month": tag, "missing_archive": True}
    first, expected, ticks = month_info(tag)
    quantum = 1000 * ticks
    opens = set()
    bad = 0
    with ZipFile(BytesIO(raw)) as zipfile, zipfile.open(name + ".csv") as stream:
        for line in stream:
            fields = line.split(b",", 7)
            t = int(fields[0])
            if (t % (HOUR_MS * ticks) or t in opens
                    or not first * quantum <= t < (first + expected * 3600) * quantum):
                raise ValueError(f"invalid opening clock in {path}")
            opens.add(t)
            bad += not has_hour_close(fields, t, ticks)
    if not opens:
        raise ValueError(f"no opening clocks in {path}")
    return {"month": tag, "path": path, "sha256": hashlib.sha256(raw).hexdigest(),
            "rows": len(opens), "expected": expected, "wrong_close_clock": bad,
            "first_utc_seconds": min(opens) // quantum, "last_utc_seconds": max(opens) // quantum}


def census(root):
    return {c: [month_record(root, c, m) for m in MONTHS] for c in ALLOWED}


if __name__ == "__main__":
    print(json.dumps(census(CUSTODY), sort_keys=True, separators=(",", ":")))
