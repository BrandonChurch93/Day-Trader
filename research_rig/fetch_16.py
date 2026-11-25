"""Replay 16 archive collection. Reads identifiers/timestamps, never prices or returns."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import gzip
import hashlib
import io
import json
import re
import zipfile

try:
    from . import fetch_13 as F
except ImportError:
    import fetch_13 as F

DATA = F.DATA.parent/"replay_16"
UM = "data/futures/um/"
H = F.HOUR
BUNDLES = {
    "SHIBUSDT":"1000SHIBUSDT","PEPEUSDT":"1000PEPEUSDT","BONKUSDT":"1000BONKUSDT",
    "FLOKIUSDT":"1000FLOKIUSDT","XECUSDT":"1000XECUSDT","LUNCUSDT":"1000LUNCUSDT",
    "BTTCUSDT":"1000BTTCUSDT",
}


def config():
    all_p = F.yaml.safe_load((F.ROOT/"config/thresholds.yaml").read_bytes())
    return all_p["replay_13_plan"]["value"],all_p["replay_16_plan"]["value"]


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def json_read(path):
    return json.loads(path.read_bytes())


def snapshot_sets():
    p13,p = config()
    viewed = json_read(F.DATA/"snapshots.json")
    lo,hi = p["held_rank_from"]-1,p["held_rank_to"]
    if lo != p13["universe_top_n"]:
        raise ValueError("held slice does not follow the viewed slice")
    out = {"viewed":viewed,"held":[]}
    for s in viewed:
        if s.get("hole"):
            out["held"].append(s)
            continue
        blob = (F.DATA/"cmc"/(s["date"].replace("-","")+".html.gz")).read_bytes()
        if digest(blob) != s["sha256"]:
            raise ValueError(f"source fingerprint mismatch {s['date']}")
        html = gzip.decompress(blob).decode("utf-8").replace('\\"','"')
        match = re.search(r'"listingHistorical":\s*\{\s*"data":\s*(?=\[)',html)
        if not match:
            raise ValueError(f"no listing at {s['date']}")
        ranked,_ = json.JSONDecoder().raw_decode(html[match.end():])
        rows,seen = [],set()
        for x in sorted(ranked,key=lambda r:r["cmcRank"]):
            if x["id"] not in seen and x["id"] not in F.EXCLUDE:
                rows.append({k:x[k] for k in ("id","name","symbol","slug","cmcRank")})
            seen.add(x["id"])
        if rows[:lo] != s["kept"] or len(rows) < hi:
            raise ValueError(f"viewed slice differs or held slice incomplete {s['date']}")
        assert not ({r["id"] for r in rows[:lo]} & {r["id"] for r in rows[lo:hi]})
        out["held"].append({k:v for k,v in s.items() if k not in ("top_raw","kept")} |
                           {"kept":rows[lo:hi]})
    F.put_json(DATA/"snapshots_16.json",out)
    record_snapshot_fingerprints(out)
    print("snapshots",len(viewed),"with held slice",sum(bool(s["kept"]) for s in out["held"]),flush=True)


def record_snapshot_fingerprints(out):
    canonical = lambda obj: json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    F.put_json(DATA/"snapshot_fingerprints.json",{
        "viewed_sha256":digest(canonical(out["viewed"])),
        "held_sha256":digest(canonical(out["held"])),
        "combined_sha256":digest((DATA/"snapshots_16.json").read_bytes()),
        "source_sha256":digest((F.DATA/"snapshots.json").read_bytes()),
    })


def csv_times(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member, = [n for n in z.namelist() if n.endswith(".csv")]
        with z.open(member) as fp:
            for line in fp:
                first = line.split(b",",1)[0]
                if first.isdigit():
                    yield F.open_epoch(first)


def archive_root(key,where):
    return (F.DATA if where == "replay_13" else DATA)/"archives"/key


def inspect_archive(key, prior):
    wanted = archive_root(key,"replay_16")
    prev = archive_root(key,"replay_13")
    if prior is not None and prev.is_file():
        raw = prev.read_bytes()
        if digest(raw) != prior["sha256"]:
            raise ValueError("reused archive changed")
        where = "replay_13"
    else:
        where = "replay_16"
        raw = wanted.read_bytes() if wanted.is_file() else F.get(F.S3+"/"+key).content
    ts = list(csv_times(raw))
    if not ts or ts != sorted(set(ts)) or ("fundingRate" not in key and any(t%H for t in ts)):
        raise ValueError("invalid archive timestamps")
    if where == "replay_16" and not wanted.is_file():
        F.write(wanted,raw)
    return {"sha256":digest(raw),"bytes":len(raw),"n":len(ts),
            "first":ts[0],"last":ts[-1],"where":where}


def spot_keys(pair,months,indices):
    m = f"data/spot/monthly/klines/{pair}/1h/"
    d = f"data/spot/daily/klines/{pair}/1h/{pair}-1h-"
    monthly = {k[-11:-4]:k for k in zipkeys(m,reuse=True)} if pair in indices["monthly"] else {}
    keys = set()
    for ym in months:
        if ym in monthly:
            keys.add(monthly[ym])
        elif pair in indices["daily"]:
            keys.update(zipkeys(d+ym,reuse=True))
    return keys


def zipkeys(prefix, reuse=False):
    root = DATA/"listings"/(digest(prefix.encode())+".json")
    old = F.DATA/"listings"/root.name
    for path in (root,old) if reuse else (root,):
        if path.is_file():
            q = json_read(path)
            if q["prefix"] != prefix:
                raise ValueError("archive prefix mismatch")
            return q["keys"]
    keys = [s for s in F.list_s3(prefix)[0] if s.endswith(".zip")]
    F.put_json(root,{"prefix":prefix,"keys":keys})
    return keys


def parallel(workers, todo, job):
    with ThreadPoolExecutor(workers) as pool:
        pending = {pool.submit(job,x):x for x in todo}
        for i,fut in enumerate(as_completed(pending),1):
            item = pending[fut]
            try:
                yield item,fut.result(),None
            except Exception as exc:
                yield item,None,str(exc)
            if i%500==0:
                print("inventory",i,"/",len(pending),flush=True)


def store_archives(name,keys,prior,errors,workers):
    result = {}
    for key,meta,err in parallel(workers,sorted(keys),lambda k:inspect_archive(k,prior.get(k))):
        if err is None:
            result[key] = meta
        else:
            errors[key] = err
    F.put_json(DATA/f"manifest_{name}.json",{"archives":result,"errors":errors,
               "snapshots_sha256":digest((DATA/"snapshots_16.json").read_bytes())})
    print(name,"clock-checked archives",len(result),"errors",len(errors),flush=True)
    if errors:
        raise SystemExit(f"{name} incomplete; see manifest")


def spot(workers):
    snaps = json_read(DATA/"snapshots_16.json")
    p13,p = config()
    p13 = p13|{k:p[k] for k in ("start","end")}
    indices = {k:set(v) for k,v in json_read(F.DATA/"archive_pairs.json").items()}
    wanted = defaultdict(set)
    for sm in snaps.values():
        group,_ = F.tasks_for(sm,p13)
        for s,months in group.items():
            wanted[s].update(months)
    prior = json_read(F.DATA/"manifest.json")["archives"]
    keys,errors = set(),{}
    for s,group,err in parallel(min(workers,24),wanted,lambda s:spot_keys(s,wanted[s],indices)):
        if err is not None:
            errors[s] = err
        else:
            keys.update(group)
    keys = {k for k in keys if "/daily/" not in k or k[-14:-4] <= p["end"]}
    store_archives("spot",keys,prior,errors,workers)


def aliases(pair):
    return tuple(dict.fromkeys((pair,BUNDLES.get(pair,pair))))


# Separate USD-M contract identity, not spot price-series joins.
# The old LUNA contract terminated at an explicit intrahour settlement.
PERP_MANUAL = {
    1765: [(None,"2025-05-21T09","EOSUSDT")],
    1982: [(None,"2021-05-21T08","KNCUSDT")],
    2239: [(None,"2020-10-10T00","LENDUSDT")],
    3513: [(None,"2025-01-06T09","FTMUSDT")],
    3890: [(None,"2024-09-04T09","MATICUSDT")],
    4086: [(None,"2020-08-31T03","ERDUSDT")],
    4113: [],  # Unicoin, not Uniswap, despite the UNI symbol in this snapshot.
    4172: [(None,"2022-05-12T15:30","LUNAUSDT"),
           ("2022-09-09T13",None,"1000LUNCUSDT")],
    4256: [(None,"2024-10-22T09","KLAYUSDT")],
    5690: [(None,"2024-07-16T09","RNDRUSDT"),("2024-07-16T09",None,"RENDERUSDT")],
    6536: [(None,"2026-02-23T09","OMUSDT"),("2026-02-23T09",None,"MANTRAUSDT")],
    6953: [(None,"2026-01-06T09","FXSUSDT"),("2026-01-06T09",None,"FRAXUSDT")],
    7278: [("2020-10-16T07",None,"AAVEUSDT")],
    9444: [("2021-05-21T08",None,"KNCUSDT")],
    9891: [(None,"2023-02-11T04","BNXUSDT")],
    11156: [(None,"2024-05-07T00","DYDXUSDT")],
    11419: [(None,"2026-06-23T09","TONUSDT"),("2026-06-23T09",None,"GRAMUSDT")],
    1518: [(None,"2025-09-08T09","MKRUSDT")],
    20314: [("2022-05-31T06",None,"LUNAUSDT")],
    23635: [("2023-02-22T14:45","2025-03-17T09","BNXUSDT"),
            ("2025-03-17T09",None,"FORMUSDT")],
    28324: [("2024-05-07T00",None,"DYDXUSDT")],
}
PERP_EVIDENCE = {
    1518: ["https://www.binance.com/en/support/announcement/detail/bf29506a33a94c17a5d5a01e74e646d2"],
    1765: ["https://www.binance.com/en/support/announcement/detail/1e89a9ca957c4b0ca7502e60b993e201"],
    1982: ["https://x.com/KyberNetwork/status/1395592099005751297"],
    2239: ["https://www.binance.com/en/support/announcement/detail/17595222999545348c8acdd5dc41c00a"],
    3513: ["https://www.binance.com/en/support/announcement/detail/aec6fcbc84b749eeab6690e6bcac2f3d"],
    3890: ["https://www.binance.com/en/support/announcement/detail/6a6de383727f4659a3050f7982e1620f"],
    4086: ["https://www.binance.com/en/support/announcement/detail/2dc59886f2a14a9280a56d1ddd272f3c"],
    4172: ["https://www.binance.com/en/support/announcement/detail/ef3ce76d5c2d45ee9b6dc3f281cde744",
           "https://www.binance.com/en/support/announcement/detail/5b9bc7ef56834de895cf829af859207e"],
    4256: ["https://www.binance.com/en/support/announcement/detail/f75f933759ee49d0af1dfbce7e32144c",
           "https://www.binance.com/en/support/announcement/detail/beac1e0a0edf4fe69d5e5c45f9d60343"],
    5690: ["https://www.binance.com/en/support/announcement/detail/d1f2ae8d99b24439a7a900caa9bb6b3b"],
    6536: ["https://www.binance.com/en/support/announcement/detail/4d13052b4be943f5b155cb9150ca902c"],
    6953: ["https://www.binance.com/en/support/announcement/detail/a17352ba70414c96882cd881591dd36d"],
    9891: ["https://www.binance.com/en/support/announcement/detail/4d23ada51a2e4fa182835c77d51ba1a9"],
    11156: ["https://www.binance.com/en/support/announcement/detail/5e2f6ff0dc0548669e51abcef524f5ad",
            "https://www.binance.com/en/support/announcement/detail/ac8e0258d2e74ccfb57478e5a46d7200"],
    11419: ["https://www.binance.com/en/support/announcement/detail/fe307fba935b44698fde4db01e84a7eb"],
    23635: ["https://www.binance.com/en/support/announcement/detail/940d0e48493e4627889c3f46371df70b",
            "https://www.binance.com/en/support/announcement/detail/2f963977c7274e0583f16f2e26987b61"],
}
# These are clock proxies where notice did not identify the perpetual's index
# switch hour. Neither identity is allowed to read across its boundary.
PERP_UNCERTAIN = {
    "KNCUSDT":"2021-05-21 08:00 UTC is an approximate migration hour from the completion announcement",
    "DYDXUSDT":"2024-05-07 is the documented Binance mainnet integration date, not a verified futures index switchover hour",
}


def perp_segments(row):
    try:
        from .common_13 import Asset
    except ImportError:
        from common_13 import Asset
    cid = row["id"]
    if cid in PERP_MANUAL:
        return [Asset(cid,s,F.boundary(begin,-10**12),F.boundary(end,10**12))
                for begin,end,s in PERP_MANUAL[cid]]
    # Other ticker changes create distinct contract symbols. Their own
    # funding and trade clocks determine active hours, never the spot clock.
    # When a CMC identity is reissued the explicit map above wins.
    return [Asset(cid,s) for s in dict.fromkeys(
        sym for _,_,pair in F.segments(row) for sym in aliases(pair))]


def mark_keys(sym,p):
    start = p["start"][:7]
    stop = p["end"][:7]
    monthly = zipkeys(UM+f"monthly/markPriceKlines/{sym}/1h/")
    by_month = {k[-11:-4]:k for k in monthly}
    names = {k for ym,k in by_month.items() if start<=ym<=stop}
    for m in F.months(date.fromisoformat(p["start"]),date.fromisoformat(p["end"])):
        ym = str(m)[:7]
        if ym not in by_month and (ym==stop or (by_month and min(by_month)<ym<max(by_month))):
            picks = zipkeys(UM+f"daily/markPriceKlines/{sym}/1h/{sym}-1h-"+ym)
            names.update(k for k in picks if k[-14:-4]<=p["end"])
    return names


def futures(workers):
    _,p = config()
    candidates = {"BTCUSDT","ETHUSDT"}
    for s in json_read(DATA/"snapshots_16.json")["viewed"]:
        for row in s["kept"]:
            candidates.update(a.pair for a in perp_segments(row))
    # The sizing inventory is timestamp-only metadata from a fully paged S3
    # listing. Never select contracts from a current exchangeInfo response.
    sizing = json_read(DATA/"object_inventory.json")
    keys = {k for k in sizing if k.split("/")[5] in candidates and
            ("/daily/" not in k or k[-14:-4]<=p["end"])}
    funded = {k.split("/")[5] for k in keys if "/fundingRate/" in k}
    keys = {k for k in keys if k.split("/")[5] in funded}
    errors = {}
    for s,group,err in parallel(min(workers,24),funded,lambda s:mark_keys(s,p)):
        if err is not None:
            errors[s] = err
        else:
            keys.update(group)
    store_archives("futures",keys,{},errors,workers)


def held_futures(workers):
    """Collect a separate manifest for the Replay 17 extension."""
    _,p = config()
    held = {a.pair for s in json_read(DATA/"snapshots_16.json")["held"]
            for row in s["kept"] for a in perp_segments(row)}
    current = json_read(DATA/"manifest_futures.json")
    if current["errors"]:
        raise SystemExit("finish viewed archives first")
    existing = {k for k in current["archives"] if k.split("/")[5] in held}
    start,stop = "2019-12",p["end"][:7]
    roots = {k:UM+suffix for k,suffix in (("f","monthly/fundingRate/"),
             ("m","monthly/klines/"),("d","daily/klines/"))}
    indices = {k:{x.removeprefix(root).rstrip("/") for x in F.list_s3(root,delimiter="/")[1]}
               for k,root in roots.items()}
    active = (held & indices["f"] & (indices["m"] | indices["d"])) - {
        k.split("/")[5] for k in existing if "/fundingRate/" in k}

    def per_symbol(s):
        funding = {k for k in zipkeys(roots["f"]+s+"/") if start<=k[-11:-4]<=stop}
        if not funding:
            return set()
        monthly = {k[-11:-4]:k for k in zipkeys(roots["m"]+s+"/1h/")} if s in indices["m"] else {}
        traded = {k for ym,k in monthly.items() if start<=ym<=stop}
        if s in indices["d"]:
            for ym in {k[-11:-4] for k in funding}-monthly.keys():
                traded.update(k for k in zipkeys(roots["d"]+s+"/1h/"+s+"-1h-"+ym)
                              if k[-14:-4]<=p["end"])
        return funding | traded | mark_keys(s,p)

    keys,errors = set(existing),{}
    for s,group,err in parallel(min(workers,24),sorted(active),per_symbol):
        if err is None:
            keys.update(group)
        else:
            errors[s] = err
    store_archives("futures_held",keys,{},errors,workers)


def coverage(workers):
    """Build clock-only coverage and check disjointness across monthly/daily files."""
    try:
        from . import common_16 as M, common_13 as C, score_16 as S
    except ImportError:
        import common_16 as M
        import common_13 as C
        import score_16 as S
    p13,p = config()
    m = {name:json_read(DATA/f"manifest_{name}.json") for name in ("spot","futures","futures_held")}
    if any(a["errors"] for a in m.values()):
        raise ValueError("incomplete archive manifests")
    totals = {}
    groups = defaultdict(list)
    for name,manifest in m.items():
        totals[name] = {}
        for key,rec in manifest["archives"].items():
            category = ("funding" if "/fundingRate/" in key else
                        "mark" if "/markPriceKlines/" in key else "trade")
            cat = totals[name].setdefault(category,dict(files=0,rows=0,bytes=0))
            cat["files"] += 1
            cat["rows"] += rec["n"]
            cat["bytes"] += rec["bytes"]
            if name=="futures_held" and key in m["futures"]["archives"]:
                if rec!=m["futures"]["archives"][key]:
                    raise ValueError("conflicting shared archive metadata")
                continue
            symbol = key.split("/")[4 if name=="spot" else 5]
            groups["spot" if name=="spot" else "futures",symbol].append((category,key,rec))
    cutoff = S.funding_cutoff(p,p13,S.source_ranges(m["futures"]))
    years = list(C.year_windows(p13|{"end":F.utc(cutoff).date().isoformat()}))
    mondays = {t for _,a,b in years for t in range(a,b,C.WEEK)}

    def scan(item):
        kind,symbol = item
        seen = defaultdict(set)
        for c,k,meta in groups[item]:
            raw = archive_root(k,meta["where"]).read_bytes()
            if digest(raw)!=meta["sha256"]:
                raise ValueError(f"archive fingerprint changed {k}")
            ts = list(csv_times(raw))
            if (len(ts),ts[0],ts[-1])!=(meta["n"],meta["first"],meta["last"]):
                raise ValueError(f"archive clock metadata changed {k}")
            if c=="funding":
                ts = [(t+30)//60*60 for t in ts]
            if len(ts)!=len(set(ts)) or not seen[c].isdisjoint(ts) or any(t%H for t in ts):
                raise ValueError(f"overlapping or non-hour timestamps {k}")
            seen[c].update(ts)
        trade = seen["trade"]
        if kind=="spot":
            return trade & {t-H for t in mondays}
        return trade & mondays,seen["funding"]

    spot_open,clock_tapes = {},{}
    ranges = S.source_ranges({"archives":m["futures"]["archives"]|m["futures_held"]["archives"]})
    for (kind,sym),data,error in parallel(workers,groups,scan):
        if error:
            raise ValueError(error)
        if kind=="spot":
            spot_open[sym] = data
        else:
            t,f = data
            clock_tapes[sym] = M.Tape(C.Series(dict.fromkeys(t)),C.Series({}),
                                      dict.fromkeys(f),ranges.get(sym,()))
    counts = {}
    for name,snaps in json_read(DATA/"snapshots_16.json").items():
        counts[name] = {}
        for year,start,end in years:
            v = dict(weeks=0,listed_coin_weeks=0,spot_prior_open_coin_weeks=0,
                     live_contract_coin_weeks=0,missing_funding_file_candidates=0)
            for t in range(start,end,C.WEEK):
                v["weeks"] += 1
                snap = M.snapshot_at(snaps,t)
                if not snap:
                    continue
                v["listed_coin_weeks"] += len(snap["kept"])
                v["spot_prior_open_coin_weeks"] += sum(any(
                    lo<=t-H and t<hi and t-H in spot_open.get(pair,())
                    for lo,hi,pair in F.segments(row)) for row in snap["kept"])
                live,missing = M.market_pool(snap,clock_tapes,t,min(t+C.WEEK,end),p)
                v["live_contract_coin_weeks"] += len(live)
                v["missing_funding_file_candidates"] += len(missing)
            counts[name][str(year)] = v
    out = {"cutoff_utc":F.utc(cutoff).isoformat(),"manifest_totals":totals,
           "clock_groups_checked":len(groups),"coverage":counts}
    F.put_json(DATA/"coverage_16_17.json",out)
    print(json.dumps(out,indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage",choices=("snapshots","spot","futures","held_futures","coverage"))
    ap.add_argument("--workers",type=int,default=32)
    arg = ap.parse_args()
    if arg.stage == "snapshots":
        snapshot_sets()
    else:
        globals()[arg.stage](arg.workers)
