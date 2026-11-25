"""Compare saved CMC quote levels with archived Binance hourly trade closes.

Historical hourly comparator only. The current policy is built by
identity_review.py using complete widened UTC-day ranges and dated evidence.
This pre-freeze identity audit writes only counts/status. It reads neither
returns nor funding/mark fields and never requests a network resource.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
import gzip
import json
from pathlib import Path
import re
import unittest

try:
    from . import fetch_16 as F
except ImportError:
    import fetch_16 as F


NOTICE = "identity_preliminary_16_17.json"
OUT = "identity_levels_16_17.json"
MANIFESTS = ("manifest_spot.json", "manifest_futures.json", "manifest_futures_held.json")
ROWS = re.compile(r'"listingHistorical":\s*\{\s*"data":\s*(?=\[)')
DECODER = json.JSONDecoder(parse_float=Decimal)


def epoch(s):
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.utcoffset() is None:
        raise ValueError("quote clock must specify its timezone")
    return int(t.timestamp())


def hour(t):
    return t // F.H * F.H


def quote(row):
    q = row["quote"]["USD"]
    stamp = epoch(q["lastUpdated"])
    p = Decimal(q["price"])
    if not p.is_finite() or p <= 0:
        raise ValueError("non-positive or non-finite price level")
    return stamp, p


def level_matches(cmc, close, multiplier):
    target = cmc * multiplier
    return target * 95 <= close * 100 <= target * 105


def verdict(n_match, n_comparable):
    if n_comparable and n_match * 10 >= n_comparable * 9:
        return "CONFIRMED"
    if n_comparable and n_match * 2 < n_comparable:
        return "REMOVED"
    return "UNKNOWN"


def mapping(row):
    return row["id"], row["market"], row["pair"]


def quotes_by_coin(snapshots, ids):
    """Use each full page, not just the ranks retained in that month's list."""
    out, months = defaultdict(dict), set()
    for s in snapshots["viewed"]:
        if s.get("hole"):
            continue
        d = s["date"]
        m = d[:7]
        if m in months:
            raise ValueError(f"more than one saved page in {m}")
        months.add(m)
        path = F.F.DATA/"cmc"/(d.replace("-", "")+".html.gz")
        raw = path.read_bytes()
        if F.digest(raw) != s["sha256"]:
            raise ValueError(f"saved CMC page fingerprint changed for {d}")
        html = gzip.decompress(raw).decode().replace('\\"','"')
        hit = ROWS.search(html)
        if not hit:
            raise ValueError(f"no saved CMC row array for {d}")
        rows, _ = DECODER.raw_decode(html[hit.end():])
        seen = set()
        for row in sorted(rows, key=lambda r:r["cmcRank"]):
            cid = row["id"]
            if cid in seen or cid not in ids:
                continue
            seen.add(cid)
            try:
                out[cid][m] = quote(row)
            except (KeyError, TypeError, ValueError, ArithmeticError):
                raise ValueError(f"no usable saved CMC USD quote price and clock for {cid} in {d}") from None
    if not months or any(cid not in out for cid in ids):
        raise ValueError("one or more mapping IDs have no usable saved CMC price and clock")
    return out, len(months)


def archive_index(manifests):
    archives = defaultdict(dict)
    for name, m in zip(MANIFESTS, manifests):
        if m["errors"]:
            raise ValueError(f"archive manifest has errors: {name}")
        spot = name == MANIFESTS[0]
        for key, meta in m["archives"].items():
            if "/klines/" not in key:
                continue
            market = "spot" if spot else "futures"
            pair = key.split("/")[4 if spot else 5]
            group = archives[market, pair]
            if group.setdefault(key, meta) != meta:
                raise ValueError(f"conflicting shared archive fingerprint: {key}")
    return archives


def archive_closes(files, wanted):
    for key, m in sorted(files.items()):
        times = {t for t in wanted if m["first"] <= t <= m["last"]}
        if not times:
            continue
        if m["where"] not in {"replay_13", "replay_16"}:
            raise ValueError(f"unknown archive location for {key}")
        raw = F.archive_root(key, m["where"]).read_bytes()
        if F.digest(raw) != m["sha256"]:
            raise ValueError(f"archive fingerprint changed for {key}")
        for row in F.F.zip_rows(raw):
            t = F.F.open_epoch(row[0])
            if t in times:
                try:
                    p = Decimal(row[4])
                    if not p.is_finite() or p <= 0:
                        raise ValueError("invalid close")
                except (ArithmeticError, IndexError, ValueError):
                    raise ValueError(f"unusable close in {key} at {t}") from None
                yield t, p


def eligible_hour(t, ranges):
    h = hour(t)
    return any(lo <= h and h + F.H <= hi for lo, hi in ranges)


def run(workers):
    notes = (F.DATA/NOTICE).read_bytes()
    inventory = F.json_read(F.DATA/"identity_inventory.json")
    snap = (F.DATA/"snapshots_16.json").read_bytes()
    manifests = [(F.DATA/n).read_bytes() for n in MANIFESTS]
    index = archive_index([json.loads(raw) for raw in manifests])
    review = json.loads(notes)
    if review["snapshots_sha256"] != F.digest(snap) or review["pending"]:
        raise ValueError("notice audit is incomplete or built from different snapshots")
    candidates = [row for row in review["rows"] if row["status"] != "NO_ARCHIVE"]
    if len(candidates) != review["checked"] or len({mapping(r) for r in candidates}) != len(candidates):
        raise ValueError("notice mapping count or uniqueness changed")
    prices, pages = quotes_by_coin(json.loads(snap), {r["id"] for r in candidates})
    checks = defaultdict(lambda: defaultdict(list))
    for row in candidates:
        cid, market, pair = mapping(row)
        record = inventory[str(cid)]["markets"].get(market+"/"+pair)
        # Known pre-archive removals remain included in the level audit, where
        # there is a bar in an active manifest; neither can enter the scorer.
        segs = record["segments"] if record else [(None, None)]
        bounds = [(epoch(a) if a else -10**12, epoch(b) if b else 10**12) for a,b in segs]
        mult = int(row["multiplier"].removesuffix("x"))
        for t, p in prices[cid].values():
            if eligible_hour(t, bounds):
                checks[market, pair][hour(t)].append(((cid, market, pair), p, mult))

    def per_pair(key):
        targets = checks[key]
        matched, compared, seen = Counter(), Counter(), set()
        for t, p in archive_closes(index.get(key, {}), targets):
            if t in seen:
                raise ValueError(f"multiple archive closes at {t} for {key}")
            seen.add(t)
            for mk, cmc, mult in targets[t]:
                compared[mk] += 1
                matched[mk] += level_matches(cmc, p, mult)
        return matched, compared

    matched, compared = Counter(), Counter()
    with ThreadPoolExecutor(workers) as pool:
        for m, n in pool.map(per_pair, sorted(checks)):
            matched.update(m)
            compared.update(n)
    rows = []
    for cid, market, pair in sorted(mapping(r) for r in candidates):
        key = cid, market, pair
        m, n = matched[key], compared[key]
        rows.append(dict(id=cid, market=market, pair=pair, matched_months=m,
                         comparable_months=n, thin=(n == 1), status=verdict(m, n)))
    F.F.put_json(F.DATA/OUT, {
        "snapshots_sha256": F.digest(snap), "notice_sha256": F.digest(notes),
        "checker_sha256": F.digest(Path(__file__).read_bytes()),
        "archive_manifest_sha256": {k:F.digest(v) for k,v in zip(MANIFESTS, manifests)},
        "cmc_pages": pages, "rows": rows,
    })


class LevelTest(unittest.TestCase):
    def test_quote_clock_comes_from_usd_quote(self):
        t, p = quote({"lastUpdated": "2020-01-01T23:59:00Z", "quote": {"USD": {
            "lastUpdated": "2020-01-01T00:15:00Z", "price": Decimal("0.02")}}})
        self.assertEqual(datetime.fromtimestamp(hour(t), F.F.UTC).hour, 0)
        self.assertEqual(p, Decimal("0.02"))

    def test_inclusive_band_with_multiplier(self):
        p = Decimal("0.02")
        for x in ("19", "20", "21"):
            self.assertTrue(level_matches(p, Decimal(x), 1000))
        for x in ("0.02", "18.9999", "21.0001"):
            self.assertFalse(level_matches(p, Decimal(x), 1000))

    def test_status_boundaries(self):
        for m,n,w in ((0,0,"UNKNOWN"),(0,1,"REMOVED"),(1,1,"CONFIRMED"),
                      (8,10,"UNKNOWN"),(9,10,"CONFIRMED"),(1,2,"UNKNOWN"),(1,3,"REMOVED")):
            self.assertEqual(verdict(m,n),w)

    def test_hour_must_be_within_segment(self):
        self.assertTrue(eligible_hour(5400, [(3600,7200)]))
        self.assertFalse(eligible_hour(5400, [(3900,7200)]))
        self.assertFalse(eligible_hour(5400, [(3600,7000)]))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--workers", type=int, default=2, choices=(1,2))
    args = p.parse_args()
    if args.selftest:
        unittest.main(argv=[__file__])
    else:
        run(args.workers)
