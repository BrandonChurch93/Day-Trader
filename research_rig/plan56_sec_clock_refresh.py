"""Fill missing trigger-day clocks using only official SEC submissions JSON."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
from threading import Event, Lock
import time
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, HTTPRedirectHandler, Request


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    contact = os.environ["SEC_FAIR_ACCESS_USER_AGENT"]
    with (args.source / "candidate_clocks.json").open() as f:
        known = json.load(f)
    with (args.source / "primary_clock_and_calendar.json").open() as f:
        calendar = json.load(f)
    dest = args.source / "sec_clock_supplement.json"
    saved = json.loads(dest.read_text()) if dest.exists() else {}
    known.update(saved)
    need = defaultdict(dict)
    for day, issuer, _, candidates, _ in calendar:
        for acc in candidates:
            if acc not in known:
                need[issuer][acc] = day
    pace, stopped = Lock(), Event()
    last = 0.0
    statuses = Counter()
    limit = 1_572_864

    def get(name):
        nonlocal last
        if stopped.is_set():
            return None
        if not re.fullmatch(r"CIK\d{10}(?:-submissions-\d+)?\.json", name):
            raise ValueError("Unexpected submissions filename")
        with pace:
            time.sleep(max(0, last + 0.27 - time.monotonic()))
            if stopped.is_set():
                return None
            last = time.monotonic()
        url = "https://data.sec.gov/submissions/" + name
        t = datetime.now(timezone.utc).isoformat()
        req = Request(url, headers={"User-Agent": contact, "Accept-Encoding": "gzip"})
        data, code = b"", 0
        try:
            with build_opener(NoRedirect).open(req, timeout=20) as res:
                code = res.status
                data = res.read(10_000_001)
                if res.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
            if len(data) > 10_000_000:
                raise ValueError("Unexpected submissions payload size")
        except HTTPError as ex:
            code = ex.code
            if code in {401, 403, 429, 451}:
                stopped.set()
        except (URLError, TimeoutError):
            pass
        with pace:
            statuses[code] += 1
            log.write(json.dumps({"name": name, "utc": t, "status": code, "sha256": hashlib.sha256(data).hexdigest()}) + "\n")
        return json.loads(data) if code == 200 else None

    def issuer_lookup(item):
        issuer, want = item
        with open("/proc/meminfo") as f:
            free = next(int(s.split()[1]) for s in f if s.startswith("MemAvailable:"))
        if free < limit:
            stopped.set()
            return {}
        found = {}

        def take(block):
            for acc, form, stamp in zip(block["accessionNumber"], block["form"], block["acceptanceDateTime"], strict=True):
                if acc in want and form == "4" and stamp and stamp.endswith("Z"):
                    found[acc] = stamp

        data = get(f"CIK{issuer:010d}.json")
        if data is None:
            return found
        take(data["filings"]["recent"])
        for row in data["filings"].get("files", []):
            if not any(row["filingFrom"] <= day <= row["filingTo"] for a, day in want.items() if a not in found):
                continue
            older = get(row["name"])
            if older is not None:
                take(older)
        return found

    print("SEC refresh issuer count", len(need), "missing same-day accessions", sum(map(len, need.values())), flush=True)
    with (args.source / "sec_clock_refresh_log.jsonl").open("a", buffering=1) as log, ThreadPoolExecutor(max_workers=3) as pool:
        for new in pool.map(issuer_lookup, sorted(need.items())):
            saved.update(new)
    with dest.open("w") as f:
        json.dump(saved, f)
    print("SEC refresh statuses", dict(statuses), "saved clocks", len(saved), "stopped", stopped.is_set())


if __name__ == "__main__":
    main()
