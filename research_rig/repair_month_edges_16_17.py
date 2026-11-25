"""Audit and repair stored public-archive month edge clocks; never calculate returns."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from hashlib import sha256
from pathlib import Path
import re
import shutil
import threading

import requests

from . import fetch_16 as F

NAMES = ("manifest_spot.json","manifest_futures.json","manifest_futures_held.json")
D,H = 86400,3600
BASE = "https://data.binance.vision"


def month_after(d):
    return date(d.year+int(d.month==12),d.month%12+1,1)


def category(key):
    if "/spot/" in key:
        return "spot"
    if "/fundingRate/" in key:
        return "funding"
    if "/markPriceKlines/" in key:
        return "mark"
    return "futures_trade"


def key_group(key):
    return re.sub(r"/(?:monthly|daily)/","/",key.rsplit("/",1)[0])


def active(data):
    manifests = {name:F.json_read(data/name) for name in NAMES}
    merged = {}
    for m in manifests.values():
        for k,v in m["archives"].items():
            if k in merged and merged[k]!=v:
                raise ValueError("conflicting metadata for shared archive")
            merged[k] = v
    return manifests,merged


def scan(data,*,include_unmanifested=False,manifest_directory=None):
    _,merged = active(data if manifest_directory is None else manifest_directory)
    extras = []
    if include_unmanifested:
        for where,archive in (("replay_16",data/"archives"),
                              ("replay_13",data.parent/"replay_13"/"archives")):
            for path in archive.rglob("*.zip"):
                key = path.relative_to(archive).as_posix()
                if "/monthly/" not in key or key in merged:
                    continue
                ts = list(F.csv_times(path.read_bytes()))
                if not len(ts):
                    raise ValueError(f"unmanifested archive has no timestamps {key}")
                extra = dict(first=min(ts),last=max(ts),n=len(ts),where=where)
                merged[key] = extra
                extras.append(dict(key=key,**extra))
    by_group = defaultdict(dict)
    daily = defaultdict(set)
    for key,m in merged.items():
        group = key_group(key)
        monthly = "/monthly/" in key
        if monthly:
            by_group[group][date.fromisoformat(key[-11:-4]+"-01")] = (key,m)
        elif "/daily/" in key and m["n"]==24 and m["last"]-m["first"]==23*H:
            daily[group].add(m["first"])
    totals, edges, repairs = defaultdict(Counter),[],{}
    for group,monthlies in by_group.items():
        for month,(key,m) in sorted(monthlies.items()):
            k = category(key)
            ym = month.isoformat()[:7]
            lo,hi = F.F.stamp(month),F.F.stamp(month_after(month))
            prev = date(month.year-int(month.month==1),(month.month-2)%12+1,1)
            first,last = m["first"],m["last"]
            counts = totals[(k,ym)]
            counts["files"] += 1
            if k=="funding":
                first,last = (first+30)//60*60,(last+30)//60*60
            leading = first-lo if prev in monthlies else 0
            trailing = hi-H-last if month_after(month) in monthlies else 0
            if leading>0 or trailing>0:
                counts["affected"] += 1
                counts["leading"] += int(leading>0)
                counts["trailing"] += int(trailing>0)
                edges.append(dict(key=key,category=k,month=ym,leading_hours=leading//H,
                                  trailing_hours=trailing//H))
            if k=="funding":
                # Binance funding normally occurs on a sub-daily schedule,
                # not each bar hour. Keep its literal hour-edge count separate
                # from holes of a full calendar day that need investigation.
                counts["at_least_one_full_day"] += int(leading>=D or trailing>=D)
                continue
            if not (leading>0 or trailing>0):
                continue
            missing = [t for t in range(lo,hi,D)
                       if ((leading>0 and t+23*H<first) or (trailing>0 and t>last))
                       and t not in daily[group]]
            counts["uncovered_days"] += len(missing)
            for t in missing:
                day = F.F.utc(t).date().isoformat()
                dkey = key.replace("/monthly/","/daily/")[:-11]+day+".zip"
                if dkey in merged:
                    raise ValueError("a partial daily file already exists for an uncovered day")
                repairs[dkey] = {"parent":key,"day":day}
    result = {"by_kind_month":{f"{k}/{m}":dict(v) for (k,m),v in sorted(totals.items())},
              "edges":edges,"repair_candidates":repairs}
    if include_unmanifested:
        result["unmanifested"] = sorted(extras,key=lambda x:x["key"])
    return result


def print_counts(result):
    for key,v in result["by_kind_month"].items():
        if v.get("affected"):
            print(key,v)
    print("uncovered whole daily files",len(result["repair_candidates"]))


def download(data,report):
    manifests,merged = active(data)
    todo = scan(data)["repair_candidates"]
    stop = threading.Event()
    tls = threading.local()

    def get(key):
        if stop.is_set():
            raise ValueError("archive refusal stopped the job")
        if not hasattr(tls,"session"):
            tls.session = requests.Session()
        r = tls.session.get(BASE+"/"+key,stream=True,timeout=(10,25),allow_redirects=False)
        if r.status_code==451:
            stop.set()
            r.close()
            raise PermissionError("451 from bulk archive, no alternate route used")
        return r

    def transfer(item):
        key,info = item
        with get(key+".CHECKSUM") as r:
            if r.status_code==404:
                return key,{"status":"CHECKSUM_404"}
            if r.status_code!=200:
                raise ValueError(f"checksum HTTP {r.status_code} for {key}")
            first = next(r.iter_content(chunk_size=4096),b"")
            match = re.fullmatch(rb"([0-9a-fA-F]{64})[ \t]+\*?([^ \r\n]+)\s*",first)
            if not match or match[2].decode()!=key.rsplit("/",1)[1]:
                raise ValueError(f"malformed checksum {key}")
            expected = match[1].decode().lower()
        target = data/"archives"/key
        tmp = target.with_name(target.name+".repair.tmp")
        if shutil.disk_usage(data).free<1.5*1024**3:
            stop.set()
            raise ValueError("disk space below hard floor")
        with get(key) as r:
            if r.status_code==404:
                return key,{"status":"ZIP_404"}
            if r.status_code!=200:
                raise ValueError(f"ZIP HTTP {r.status_code} for {key}")
            target.parent.mkdir(parents=True,exist_ok=True)
            h = sha256()
            n = 0
            try:
                with tmp.open("wb") as out:
                    for chunk in r.iter_content(chunk_size=16384):
                        n += len(chunk)
                        if n>2*1024**2:
                            raise ValueError("daily archive exceeded expected size")
                        h.update(chunk)
                        out.write(chunk)
                first = F.F.stamp(date.fromisoformat(info["day"]))
                ts = list(F.csv_times(tmp.read_bytes()))
                if h.hexdigest()!=expected or ts!=list(range(first,first+D,H)):
                    raise ValueError(f"daily archive checksum or clock mismatch {key}")
                if target.exists():
                    if F.digest(target.read_bytes())!=expected:
                        raise ValueError("existing repair file differs from official checksum")
                    tmp.unlink()
                else:
                    tmp.replace(target)
            finally:
                tmp.unlink(missing_ok=True)
        return key,{"status":"VERIFIED","meta":{"sha256":expected,"n":24,"first":first,
                                                "last":first+23*H,"where":"replay_16","bytes":n}}

    results = {}
    with ThreadPoolExecutor(2) as pool:
        for key,result in pool.map(transfer,sorted(todo.items())):
            results[key] = result
    for name,manifest in manifests.items():
        archives = manifest["archives"]
        for key,res in results.items():
            if res["status"]=="VERIFIED" and todo[key]["parent"] in archives:
                if key in merged:
                    raise ValueError("repair would duplicate an active archive")
                archives[key] = res["meta"]
        F.F.put_json(data/name,manifest)
    F.F.put_json(report,{"outcomes":results,
                        "counts":dict(Counter(v["status"] for v in results.values())),
                        "source":BASE})
    print(dict(Counter(v["status"] for v in results.values())),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("data",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--download",action="store_true")
    p.add_argument("--include-unmanifested",action="store_true",
                   help="include physically stored monthly files in a scan only")
    p.add_argument("--manifest-directory",type=Path,
                   help="use saved historical manifests for a scan only")
    x=p.parse_args()
    if x.download:
        if x.include_unmanifested or x.manifest_directory is not None:
            p.error("automatic repair requires only the active manifests")
        download(x.data,x.out)
    else:
        result=scan(x.data,include_unmanifested=x.include_unmanifested,
                    manifest_directory=x.manifest_directory)
        F.F.put_json(x.out,result)
        print_counts(result)
