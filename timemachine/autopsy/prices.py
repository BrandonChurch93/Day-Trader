"""Minute prices from the recorded tape, read only, one symbol at a time, kept in memory only (no price file is written)."""
import sqlite3, bisect
from array import array
from datetime import datetime, timezone
import settings

START = int(datetime(2026, 3, 20, tzinfo=timezone.utc).timestamp())   # TM03 starts 2026-04-01; 7 days of look-back
END = int(datetime(2026, 12, 1, tzinfo=timezone.utc).timestamp())
_cache = {}

def ts(s):
    return int(datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())

def load(sym):
    if sym in _cache:
        return _cache[sym]
    con = sqlite3.connect(settings.tape_uri(), uri=True)
    t = array("q"); c = array("d"); h = array("d"); l = array("d")
    for row in con.execute("SELECT t, h, l, c FROM bars WHERE symbol=? AND tf='1Min' AND t>=? AND t<? ORDER BY t", (sym, START, END)):
        t.append(row[0]); h.append(row[1]); l.append(row[2]); c.append(row[3])
    con.close()
    _cache[sym] = (t, c, h, l)
    return _cache[sym]

def px(sym, when):
    """Close of the last minute at or before `when` (epoch seconds). None if no bar in the 6 hours before."""
    t, c, _, _ = load(sym)
    i = bisect.bisect_right(t, when) - 1
    if i < 0 or when - t[i] > 6 * 3600:
        return None
    return c[i]

def last_time(sym):
    t, _, _, _ = load(sym)
    return t[-1] if len(t) else None

def ret(sym, a, b):
    pa, pb = px(sym, a), px(sym, b)
    if pa is None or pb is None:
        return None
    if b > last_time(sym):
        return None
    return pb / pa - 1.0

def hi_lo(sym, a, b):
    t, _, h, l = load(sym)
    i, j = bisect.bisect_left(t, a), bisect.bisect_right(t, b)
    if j <= i:
        return None, None
    return max(h[i:j]), min(l[i:j])
