"""Coverage-only collection for replay 13. Does not compute returns."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import csv
from datetime import date, datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
from threading import local
import time
import xml.etree.ElementTree as ET
import zipfile

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "rig/data/replay_13"
CMC = "https://coinmarketcap.com/historical/"
BINANCE = "https://data.binance.vision/"
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
UTC = timezone.utc
HOUR = 3600
# IDs, not display tickers. FRAX stablecoin is 6952, not FXS renamed FRAX (6953).
# Becker's BSC-USD label was not present in any supplied CMC historical array.
EXCLUDE = {
    1:"BTC", 1027:"ETH", 825:"USDT", 3408:"USDC", 4687:"BUSD", 4943:"DAI",
    7129:"UST/USTC", 2563:"TUSD", 3330:"USDP/PAX", 4779:"HUSD", 3306:"GUSD",
    26081:"FDUSD", 29470:"Ethena USDe", 3792:"ARAW/USDe",
    33039:"USDS", 27772:"PYUSD", 19891:"USDD", 6952:"FRAX stablecoin",
    36148:"USD1", 34691:"USDTB", 3717:"WBTC", 2396:"WETH", 8085:"STETH",
    12409:"WSTETH", 28695:"WEETH", 24760:"WBETH", 32994:"CBBTC", 5777:"RENBTC",
    6941:"HBTC", 3957:"LEO", 4023:"BTCB", 5176:"XAUT", 4705:"PAXG",
    11092:"BGB", 21353:"WBT", 3897:"OKB", 3635:"CRO", 2502:"HT", 4195:"FTT",
    34387:"RLUSD", 39120:"U", 33793:"USDG", 5068:"USDN", 4056:"AMPL",
    18579:"WTRX", 2087:"KCS", 4269:"GT", 3351:"ZB",
    2907:"KBC", 4842:"FLG", 2027:"CNX",
}
TLS = local()

# End is exclusive. A transition is never a price splice. The unit of a
# tradable position is (CMC identity, pair, mapping segment).
MANUAL = {
    1567: [(None, "2022-01-24T04", "NANO"), ("2022-01-28T08", None, "XNO")],
    1720: [(None, None, "IOTA")],  # CMC MIOTA is IOTA on Binance.
    1765: [(None, "2025-05-26T03", "EOS"), ("2025-05-28T08", None, "A")],
    2239: [(None, "2020-10-12T03", "LEND"), ("2020-10-15T03", None, "AAVE")],
    2603: [(None, "2021-04-05T05", "NPXS"), ("2021-04-09T04", None, "PUNDIX")],
    3513: [(None, "2025-01-13T03", "FTM"), ("2025-01-16T08", None, "S")],
    3718: [(None, "2022-01-17T04", "BTT")],  # Old BTT only.
    3890: [(None, "2024-09-10T03", "MATIC"), ("2024-09-13T10", None, "POL")],
    4086: [(None, "2020-08-31T03", "ERD"), ("2020-09-03T03", None, "EGLD")],
    4172: [(None, "2022-05-13T01", "LUNA"), ("2022-09-09T08", None, "LUNC")],
    4256: [(None, "2024-10-28T03", "KLAY"), ("2024-10-31T08", None, "KAIA")],
    5690: [(None, "2024-07-22T03", "RNDR"), ("2024-07-26T08", None, "RENDER")],
    6536: [(None, "2026-03-02T03", "OM"), ("2026-03-04T08", None, "MANTRA")],
    6953: [(None, "2026-01-13T03", "FXS"), ("2026-01-15T08", None, "FRAX")],
    11419: [(None, "2026-06-30T03", "TON"), ("2026-07-02T08", None, "GRAM")],
    1518: [(None, "2025-09-15T03", "MKR"), ("2025-09-17T08", None, "SKY")],
    16086: [("2022-01-25T04", None, "BTTC")],  # New BTT, not BTTUSDT.
    20314: [("2022-05-31T06", None, "LUNA")],  # New Terra; not ranked in these snapshots.
    28298: [(None, None, "BEAMX")],  # Gaming token, not the older BEAM privacy coin.
}


def boundary(s, default):
    return int(datetime.fromisoformat(s).replace(tzinfo=UTC).timestamp()) if s else default


def segments(row):
    rules = MANUAL.get(row["id"], [(None, None, row["symbol"].upper())])
    return tuple((boundary(a, -10**12), boundary(b, 10**12), sym + "USDT") for a,b,sym in rules)


def config():
    return yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["replay_13_plan"]["value"]


def months(a, b):
    d = a.replace(day=1)
    while d <= b:
        yield d
        d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)


def sunday(m):
    return m + timedelta(days=(6 - m.weekday()) % 7)


def stamp(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())


def utc(t):
    return datetime.fromtimestamp(t, UTC)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def put_json(path, data):
    write(path, (json.dumps(data, sort_keys=True, indent=2) + "\n").encode())


def get(url, **kwargs):
    if not hasattr(TLS, "session"):
        TLS.session = requests.Session()
    for pause in (.3, 1, 3, 5):
        try:
            r = TLS.session.get(url, timeout=(8, 30), headers={"User-Agent": "Mozilla/5.0"}, **kwargs)
            if r.status_code not in (429, 500, 502, 503, 504):
                return r
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(pause)
    raise RuntimeError(f"request not verified: {url}")


def snapshot(d, n):
    path = DATA / f"cmc/{d:%Y%m%d}.html.gz"
    url = f"{CMC}{d:%Y%m%d}/"
    if not path.exists():
        r = get(url)
        r.raise_for_status()
        if f"/historical/{d:%Y%m%d}" not in r.url:
            raise ValueError(f"CMC redirected from {url} to {r.url}")
        write(path, gzip.compress(r.content, mtime=0))
        time.sleep(.35)
    html = gzip.decompress(path.read_bytes()).decode("utf-8").replace('\\"', '"')
    match = re.search(r'"listingHistorical":\s*\{\s*"data":\s*(?=\[)', html)
    if not match:
        raise ValueError(f"no snapshot array for {d}")
    rows, _ = json.JSONDecoder().raw_decode(html[match.end():])
    ordered, seen = [], set()
    for row in sorted(rows, key=lambda x: x["cmcRank"]):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        ordered.append({k: row[k] for k in ("id", "name", "symbol", "slug", "cmcRank")})
    kept = [r for r in ordered if r["id"] not in EXCLUDE][:n]
    if len(kept) != n or ordered[0]["id"] != 1 or ordered[0]["cmcRank"] != 1:
        raise ValueError(f"CMC rank or pool incomplete for {d}: {len(kept)} kept of {len(ordered)}")
    return {"date": str(d), "known_at": stamp(d + timedelta(days=1)), "url": url,
            "kept": kept, "top_raw": ordered[:max(100, n)], "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def snapshots(workers):
    p = config()
    start, end = map(date.fromisoformat, (p["start"], p["end"]))
    bootstrap = start.replace(day=1) - timedelta(days=1)
    ds = [sunday(m) for m in months(bootstrap, end)]
    def visit(d):
        try:
            return snapshot(d,p["universe_top_n"])
        except (requests.RequestException,ValueError,RuntimeError) as e:
            return {"date":str(d),"known_at":stamp(d+timedelta(days=1)),
                    "url":f"{CMC}{d:%Y%m%d}/","kept":[],"hole":str(e)}
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(visit, ds))
    put_json(DATA / "snapshots.json", rows)
    put_json(DATA / "admitted_coins.json", roster(rows))
    nh = sum("hole" in r for r in rows)
    print(f"{len(rows)-nh} snapshots with {p['universe_top_n']} eligible CMC ranks; {nh} holes", flush=True)


def roster(rows):
    admitted = defaultdict(lambda: {"symbols": set(), "names": set(), "months": []})
    for snap in rows:
        for asset in snap["kept"]:
            rec = admitted[asset["id"]]
            rec["symbols"].add(asset["symbol"])
            rec["names"].add(asset["name"])
            rec["months"].append(snap["date"][:7])
    return [{"id": i, "symbols": sorted(r["symbols"]), "names": sorted(r["names"]),
             "months": r["months"]} for i,r in sorted(admitted.items())]


def list_s3(prefix, *, delimiter=None):
    params = {"list-type": "2", "prefix": prefix}
    if delimiter:
        params["delimiter"] = delimiter
    keys, prefixes = [], []
    ns = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
    while True:
        r = get(S3, params=params)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        keys += [x.text for x in root.findall("s:Contents/s:Key", ns)]
        prefixes += [x.text for x in root.findall("s:CommonPrefixes/s:Prefix", ns)]
        tok = root.findtext("s:NextContinuationToken", namespaces=ns)
        if root.findtext("s:IsTruncated", namespaces=ns) == "true":
            if not tok or tok == params.get("continuation-token"):
                raise ValueError(f"incomplete archive list: {prefix}")
            params["continuation-token"] = tok
        else:
            return keys, prefixes


def pair_index():
    out = {}
    for bucket in ("monthly", "daily"):
        base = f"data/spot/{bucket}/klines/"
        _, folders = list_s3(base, delimiter="/")
        out[bucket] = sorted(p[len(base):-1] for p in folders if p.endswith("USDT/"))
    put_json(DATA / "archive_pairs.json", out)
    print("Binance pair prefixes", {k: len(v) for k, v in out.items()}, flush=True)


def archive_list(prefix):
    p = DATA / "listings" / (hashlib.sha256(prefix.encode()).hexdigest() + ".json")
    if p.exists():
        q = json.loads(p.read_text())
        if q["prefix"] != prefix:
            raise ValueError("archive prefix mismatch")
        return q["keys"]
    keys, _ = list_s3(prefix)
    keys = [k for k in keys if k.endswith(".zip")]
    put_json(p, {"prefix": prefix, "keys": keys})
    return keys


def paths_for(pair, wanted, pairsets):
    monthbase = f"data/spot/monthly/klines/{pair}/1h/"
    daybase = f"data/spot/daily/klines/{pair}/1h/"
    ms = ({k[-11:-4]: k for k in archive_list(monthbase)} if pair in pairsets["monthly"] else {})
    result = set()
    if pair not in pairsets["monthly"] and pair not in pairsets["daily"]:
        return result
    for ym in sorted(wanted):
        if ym in ms:
            result.add(ms[ym])
        elif pair in pairsets["daily"]:
            result.update(archive_list(f"{daybase}{pair}-1h-{ym}"))
    return result


def open_epoch(raw):
    return int(raw) // (1_000_000 if int(raw) >= 10**14 else 1000)


def zip_rows(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = [n for n in z.namelist() if n.endswith(".csv")]
        if len(members) != 1:
            raise ValueError("expected one archive CSV")
        with z.open(members[0]) as f:
            yield from (r for r in csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
                        if r and r[0].isdigit())


def fetch_file(key):
    p = DATA / "archives" / key
    if not p.exists():
        r = get(BINANCE + key)
        r.raise_for_status()
        raw = r.content
    else:
        raw = p.read_bytes()
    ts = [open_epoch(r[0]) for r in zip_rows(raw)]
    dayfile = "/daily/" in key
    label = key[-14:-4] if dayfile else key[-11:-4] + "-01"
    floor = stamp(date.fromisoformat(label))
    ceil = (floor + 24*HOUR if dayfile else
            stamp((date.fromisoformat(label).replace(day=28) + timedelta(days=4)).replace(day=1)))
    if not ts or not all(floor <= t < ceil and t % HOUR == 0 for t in ts) or ts != sorted(set(ts)):
        raise ValueError(f"invalid archive hour grid: {key}")
    if not p.exists():
        write(p, raw)
    return key, {"sha256": hashlib.sha256(raw).hexdigest(), "n": len(ts),
                 "bytes": len(raw), "first": ts[0], "last": ts[-1]}, ts


def tasks_for(snapshots, p):
    start, end = map(date.fromisoformat, (p["start"], p["end"]))
    end += timedelta(days=1)
    warm = timedelta(hours=max(p["rise_days"]*24,p["dip_lookback_hours"])+1)
    wants, coverage_specs = defaultdict(set), []
    kept = []
    for i, snap in enumerate(snapshots):
        d = date.fromisoformat(snap["date"]).replace(day=1)
        next_month = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        next_active = (utc(snapshots[i+1]["known_at"]).date() if i+1 < len(snapshots) else end)
        scope_lo = stamp(min(d, utc(snap["known_at"]).date())) - int(warm.total_seconds())
        scope_hi = stamp(min(end, max(next_active + timedelta(days=7), next_month)))
        # Preserve fingerprints of the exact decision and execution archive sources.
        kept = snap["kept"] or kept
        for row in kept:
            possible = segments(row)
            for a, b, pair in possible:
                lo, hi = max(a, scope_lo), min(b, scope_hi)
                if lo < hi:
                    wants[pair].update(f"{m:%Y-%m}" for m in months(utc(lo).date(), utc(hi-1).date()))
            if d >= start.replace(day=1) and snap["kept"]:
                coverage_specs.append((d, min(next_month, end), row, possible))
    wants["BTCUSDT"].update(f"{m:%Y-%m}" for m in months(start, end-timedelta(days=1)))
    return wants, coverage_specs


def coverage(specs, by_pair, failures, pairsets):
    import bisect
    stats, records = {}, []
    all_pairs = pairsets["monthly"] | pairsets["daily"]
    for d, end, row, segs in specs:
        t0, t1 = stamp(d), stamp(end)
        touched = [(max(a,t0), min(b,t1), pair) for a,b,pair in segs if max(a,t0) < min(b,t1)]
        n, uncertain = 0, False
        for a, b, pair in touched:
            ts = by_pair.get(pair, ())
            n += bisect.bisect_left(ts,b) - bisect.bisect_left(ts,a)
            uncertain |= (pair, f"{d:%Y-%m}") in failures or (pair, "*") in failures
        expected = (t1-t0)//HOUR
        status = ("unverified_archive" if uncertain else "archived_hours" if n else
                  "no_archived_hours" if any(p in all_pairs for _,_,p in touched) else "no_archived_pair")
        records.append({"month": f"{d:%Y-%m}", "id": row["id"], "symbol": row["symbol"],
                        "pairs": [p for _,_,p in touched], "status": status, "hours": n, "expected": expected})
        s = stats.setdefault(d.year, {"listed":set(), "pair_coins":set(), "coin_months":0,
                                     "with_pair":0,"without_pair":0,"unverified":0,
                                     "hours_observed":0,"missing_if_paired":0,"hours_no_pair":0})
        s["listed"].add(row["id"])
        s["coin_months"] += 1
        s["hours_observed"] += n
        if n:
            s["pair_coins"].add(row["id"])
        if uncertain:
            s["unverified"] += 1
        elif n:
            s["with_pair"] += 1
            s["missing_if_paired"] += expected - n
        else:
            s["without_pair"] += 1
            s["hours_no_pair"] += expected
    for v in stats.values():
        for k in ("listed", "pair_coins"):
            v[k] = len(v[k])
    return stats, records


def pull(workers):
    p = config()
    snaps = json.loads((DATA / "snapshots.json").read_text())
    pairsets = {k:set(v) for k,v in json.loads((DATA / "archive_pairs.json").read_text()).items()}
    wants, specs = tasks_for(snaps, p)
    errors, failures, keys = [], set(), set()
    with ThreadPoolExecutor(min(workers,16)) as pool:
        jobs = {pool.submit(paths_for, pair, periods, pairsets):pair for pair,periods in wants.items()}
        for f in as_completed(jobs):
            pair = jobs[f]
            try:
                keys.update(f.result())
            except Exception as e:
                errors.append((pair,str(e)))
                failures.add((pair,"*"))
    print(f"{len(keys)} archived candle files found, {len(errors)} pair list errors", flush=True)
    keys = {k for k in keys if "/daily/" not in k or k[-14:-4] <= p["end"]}
    manifest, by_pair = {}, defaultdict(list)
    with ThreadPoolExecutor(workers) as pool:
        jobs = {pool.submit(fetch_file, k):k for k in keys}
        for i, f in enumerate(as_completed(jobs), 1):
            key = jobs[f]
            pair = key.split("/")[4]
            try:
                _, meta, ts = f.result()
                manifest[key] = meta
                by_pair[pair].extend(ts)
            except Exception as e:
                errors.append((key,str(e)))
                month = key[-14:-7] if "/daily/" in key else key[-11:-4]
                failures.add((pair,month))
            if i % 250 == 0:
                print(f"Archives {i}/{len(keys)}, errors {len(errors)}", flush=True)
    for pair in by_pair:
        by_pair[pair] = sorted(set(by_pair[pair]))
    years, rows = coverage(specs, by_pair, failures, pairsets)
    put_json(DATA / "manifest.json", {"archives": manifest, "errors": sorted(errors),
                                     "excluded_ids": EXCLUDE,
                                     "pair_mappings": MANUAL, "collection_parameters": collection_parameters(p),
                                     "snapshot_sha256":hashlib.sha256((DATA/"snapshots.json").read_bytes()).hexdigest()})
    put_json(DATA / "coverage.json", {"years": years, "coin_months": rows,
                                     "snapshot_holes": [s for s in snaps if s.get("hole")]})
    print(json.dumps(years, indent=2), flush=True)
    if errors:
        raise SystemExit(f"{len(errors)} archive requests unverified; see manifest.json")


def collection_parameters(p):
    return {k:p[k] for k in ("start","end","universe_top_n","rise_days","dip_lookback_hours")}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=["snapshots", "pairs", "bars"])
    p.add_argument("--workers", type=int, default=6)
    args = p.parse_args()
    if args.stage == "snapshots":
        snapshots(args.workers)
    elif args.stage == "pairs":
        pair_index()
    else:
        pull(args.workers)
