"""Read time-stamped attention counts without using a later publication or revision."""

from contextlib import closing
from datetime import datetime
from math import floor, isfinite
import os
from pathlib import Path
import re
import sqlite3


SECONDS_PER_DAY = 86_400
DEFAULT_STORE = Path("/home/user/workspace/rig/tm_store")
SCHEMA = """
CREATE TABLE attention (
    source TEXT NOT NULL,
    coin TEXT NOT NULL,
    ts_utc INTEGER NOT NULL,
    value REAL NOT NULL CHECK (value >= 0),
    known_at_utc INTEGER NOT NULL CHECK (known_at_utc >= ts_utc),
    vintage TEXT NOT NULL CHECK (vintage IN ('original', 'assumed_lag', 'capture_only')),
    PRIMARY KEY (coin, ts_utc, source, known_at_utc, vintage)
) STRICT, WITHOUT ROWID;
"""
VINTAGES = {"capture_only": 0, "assumed_lag": 1, "original": 2}


def _epoch(as_of):
    if isinstance(as_of, str):
        as_of = datetime.fromisoformat(as_of)
    if isinstance(as_of, datetime) and as_of.utcoffset() is not None:
        return floor(as_of.timestamp())
    if type(as_of) in (int, float) and isfinite(as_of):
        return floor(as_of)
    raise ValueError("as_of_utc must be a timezone-aware time or Unix seconds")


def get_attention(coin, as_of_utc, lookback_days, *, min_vintage="assumed_lag", db_path=None):
    """Latest value known per source and period, for period ends in (as_of-lookback, as_of].

    Returns a list of dicts. Times are integer UTC Unix seconds. Missing rows
    mean no known value, not zero. A missing store is an error, not an empty feed.
    Use min_vintage="original" for verified vintages only. Capture-only data
    is excluded unless explicitly opted into.
    """
    coin = coin.strip().upper()
    if coin.endswith(("-USD", "/USD")):
        coin = coin[:-4]
    if not re.fullmatch(r"[A-Z0-9]{1,24}", coin):
        raise ValueError("coin must be a base symbol or a USD pair")
    if type(lookback_days) is not int or lookback_days < 0:
        raise ValueError("lookback_days must be a nonnegative integer")
    if min_vintage not in VINTAGES:
        raise ValueError("unknown minimum vintage")
    hi = _epoch(as_of_utc)
    lo = hi - lookback_days * SECONDS_PER_DAY
    path = Path(db_path) if db_path is not None else Path(os.environ.get("TM_STORE", DEFAULT_STORE)) / "attention.sqlite"
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT source, coin, ts_utc, value, known_at_utc, vintage
            FROM (
                SELECT *, row_number() OVER (
                    PARTITION BY source, coin, ts_utc
                    ORDER BY known_at_utc DESC,
                        CASE vintage WHEN 'original' THEN 2 WHEN 'assumed_lag' THEN 1 ELSE 0 END DESC
                ) AS version_rank
                FROM attention
                WHERE coin = ? AND ts_utc > ? AND ts_utc <= ? AND known_at_utc <= ?
                AND CASE vintage WHEN 'original' THEN 2 WHEN 'assumed_lag' THEN 1 ELSE 0 END >= ?
            )
            WHERE version_rank = 1
            ORDER BY ts_utc, source
            """,
            (coin, lo, hi, hi, VINTAGES[min_vintage]),
        )
        return [dict(row) for row in rows]
