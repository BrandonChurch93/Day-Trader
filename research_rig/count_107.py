"""Price-blind, serial count of lagged SPY holdings and cash actions.

Run roster, then vendor under the credential runner, then count unwrapped.
The roster stage seals the sampling frame and draw before vendor can run.
All files under the supplied data directory are private and off-repo.
"""

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import requests


SEED = "count-107-ledger-209-v1-66afb7af"
START, END = "2016-01", "2026-10"
MIN_TURNS, MIN_NAMES, SAMPLE = 120, 20, 60
REQUEST_CAP, BYTE_CAP = 1500, 150_000_000
DATA_DIR = "/home/user/workspace/rig/data/count_107"
SEC_SUB = "https://data.sec.gov/submissions/"
SEC_DOC = "https://www.sec.gov/Archives/edgar/data/884394/"
ALPACA = "https://data.alpaca.markets/v1/corporate-actions"


def write_json(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n")


def load(path):
    return json.loads(path.read_bytes())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def shift(month, n):
    y, m = map(int, month.split("-"))
    yi, mi = divmod(y * 12 + m - 1 + n, 12)
    return f"{yi:04}-{mi + 1:02}"


def months():
    result = []
    m = START
    while m <= END:
        result.append(m)
        m = shift(m, 1)
    return result


class Collector:
    def __init__(self, directory):
        self.directory = directory
        self.log = directory / "network.json"
        self.stats = load(self.log) if self.log.exists() else {"requests": 0, "bytes": 0}
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Brandon Church Research modernsoftworks@gmail.com"})

    def get(self, filename, url, params=None):
        if not (url.startswith(SEC_SUB) or url.startswith(SEC_DOC) or url == ALPACA):
            raise ValueError("URL outside the declared roster/action endpoints")
        path = self.directory / filename
        if path.exists():
            return path.read_bytes()
        if self.stats["requests"] >= REQUEST_CAP:
            raise ValueError("request cap")
        self.stats["requests"] += 1
        write_json(self.log, self.stats)
        try:
            with self.session.get(url, params=params, timeout=25, stream=True, allow_redirects=False) as reply:
                if reply.status_code != 200:
                    raise ValueError(f"{filename}: HTTP {reply.status_code}")
                body = bytearray()
                for chunk in reply.iter_content(32768):
                    self.stats["bytes"] += len(chunk)
                    if self.stats["bytes"] > BYTE_CAP:
                        raise ValueError("byte cap")
                    body.extend(chunk)
            path.write_bytes(body)
            return body
        finally:
            write_json(self.log, self.stats)
            time.sleep(0.14)


def filing_rows(submission):
    fields = ("form", "reportDate", "acceptanceDateTime", "accessionNumber", "primaryDocument")
    return list(zip(*(submission[k] for k in fields), strict=True))


def field(node, name):
    return (node.findtext(f"{{*}}{name}") or "").strip()


def equity_ids(blob):
    root = ET.fromstring(blob)
    positions = root.findall(".//{*}invstOrSec")
    if not positions:
        raise ValueError("missing N-PORT positions")
    output = {}
    for row in positions:
        if field(row, "assetCat") != "EC" or field(row, "invCountry") != "US":
            continue
        name, title = field(row, "name"), field(row, "title")
        cusip = field(row, "cusip")
        if not re.fullmatch(r"[0-9A-Z]{9}", cusip) or cusip == "000000000":
            raise ValueError("common equity has no usable CUSIP")
        if cusip in output:
            raise ValueError("duplicate common-equity CUSIP")
        output[cusip] = {"name": name, "title": title}
    if not (300 <= len(output) <= 550):
        raise ValueError(f"unexpected US common-equity membership count: {len(output)}")
    return output


def draw_sample(frame):
    pairs = {(month, ident) for month, filing in frame.items() for ident in filing["ids"]}
    return sorted(pairs, key=lambda p: (sha(f"{SEED}|{p[0]}|{p[1]}".encode()), p))[:SAMPLE]


def roster(c):
    metadata = json.loads(c.get("submissions.json", SEC_SUB + "CIK0000884394.json"))
    filings = filing_rows(metadata["filings"]["recent"])
    for old in metadata["filings"]["files"]:
        if old["filingTo"] >= "2015":
            filename = old["name"]
            if not re.fullmatch(r"CIK0000884394-submissions-\d+\.json", filename):
                raise ValueError("unexpected SEC older submissions filename")
            filings += filing_rows(json.loads(c.get(filename, SEC_SUB + filename)))
    eligible = [f for f in filings if f[0] == "NPORT-P" and f[1]]
    if not eligible:
        raise ValueError("no public N-PORT filings")
    selected, parsed = {}, {}
    for month in months():
        cutoff = month + "-01"
        prior = [f for f in eligible if f[1] < cutoff and f[2] and f[2][:10] < cutoff]
        if not prior:
            continue
        form, period, accepted, accession, document = max(prior, key=lambda f: (f[1], f[2], f[3]))
        if accession not in parsed:
            doc = document.rsplit("/", 1)[-1]
            if doc != "primary_doc.xml" or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
                raise ValueError("unexpected SEC primary XML path")
            raw = c.get(f"{accession}.xml", SEC_DOC + accession.replace("-", "") + "/" + doc)
            parsed[accession] = {"period": period, "accepted": accepted, "accession": accession,
                                 "sha256": sha(raw), "ids": equity_ids(raw)}
        selected[month] = parsed[accession]
    frame = {
        "months": months(), "roster": {m: selected[m]["accession"] for m in selected},
        "filings": parsed, "line": {"turns": MIN_TURNS, "names_per_leg": MIN_NAMES, "sample": SAMPLE,
                                    "min_coverage_percent": 95},
        "first_public_nport": min(eligible, key=lambda f: f[2]),
        "nq_count": sum(f[0] in {"N-Q", "N-Q/A"} for f in filings),
        "legacy_n30d": [f for f in filings if f[0] in {"N-30D", "N-30D/A"}
                        and "2015" <= f[1] < "2020"],
    }
    draw = draw_sample(selected)
    if len(draw) != SAMPLE:
        raise ValueError("partial draw")
    write_json(c.directory / "frame.json", frame)
    write_json(c.directory / "sample.json", {"seed": SEED, "frame_sha256": sha((c.directory / "frame.json").read_bytes()),
                                             "scope": "N-PORT frame only", "pairs": draw})


def frame_and_sample(c):
    path = c.directory / "frame.json"
    sample = load(c.directory / "sample.json")
    if sample["seed"] != SEED or sample["frame_sha256"] != sha(path.read_bytes()):
        raise ValueError("frame or seed does not match pre-vendor draw")
    frame = load(path)
    if draw_sample({m: frame["filings"][a] for m, a in frame["roster"].items()}) != [tuple(x) for x in sample["pairs"]]:
        raise ValueError("draw differs from seed")
    return frame, sample


def vendor(c):
    frame, _ = frame_and_sample(c)
    ids = sorted(set().union(*(f["ids"] for f in frame["filings"].values())))
    pages = []
    for first in range(0, len(ids), 50):
        query = {"cusips": ",".join(ids[first:first + 50]), "types": "cash_dividend",
                 "start": shift(START, -12) + "-01", "end": "2026-11-26",
                 "data_quality": "all", "limit": 1000}
        tokens = set()
        for page in range(REQUEST_CAP):
            filename = f"alpaca_{first:04}_{page:04}.json"
            data = json.loads(c.get(filename, ALPACA, query))
            if "corporate_actions" not in data or "next_page_token" not in data:
                raise ValueError(f"unexpected response schema in {filename}")
            pages.append(filename)
            token = data["next_page_token"]
            if not token:
                break
            if token in tokens:
                raise ValueError("repeated page token")
            tokens.add(token)
            query["page_token"] = token
    write_json(c.directory / "vendor_pages.json", pages)


def actions(c, keys):
    exdates, missing, unclear = collections.defaultdict(set), 0, 0
    for file in load(c.directory / "vendor_pages.json"):
        for row in (load(c.directory / file)["corporate_actions"] or {}).get("cash_dividends", []):
            if row.get("cusip") not in keys:
                continue
            if row.get("special") is True:
                continue
            if row.get("special") is not False:
                unclear += 1
                continue
            try:
                ex = dt.date.fromisoformat(row.get("ex_date") or "").isoformat()
            except (ValueError, TypeError):
                missing += 1
                continue
            exdates[row["cusip"]].add(ex)
    return exdates, missing, unclear


def summary(c):
    frame, sample = frame_and_sample(c)
    ids = set().union(*(f["ids"] for f in frame["filings"].values()))
    result = {k: frame[k] for k in ("first_public_nport", "line", "nq_count", "legacy_n30d")}
    result.update({"window_months": len(frame["months"]), "rostered_months": len(frame["roster"]),
                   "first_rostered_month": min(frame["roster"]), "last_rostered_month": max(frame["roster"]),
                   "missing_roster_months": len(frame["months"]) - len(frame["roster"]),
                   "roster_filings": len(frame["filings"]), "security_ids": len(ids), "drawn": len(sample["pairs"]),
                   "sample_sha256": sha((c.directory / "sample.json").read_bytes()), "network": c.stats})
    if (c.directory / "vendor_pages.json").exists():
        dates, missing, unclear = actions(c, ids)
        per_m = {s: {d[:7] for d in es} for s, es in dates.items()}
        turns = {}
        for m, accession in frame["roster"].items():
            predicted = peers = 0
            recent = {shift(m, -n) for n in range(1, 13)}
            lags = {shift(m, -n) for n in (3, 6, 9, 12)}
            for s in frame["filings"][accession]["ids"]:
                history = per_m.get(s, set()) & recent
                if history & lags:
                    predicted += 1
                elif history:
                    peers += 1
            turns[m] = [predicted, peers]
        passed = [m for m, counts in turns.items() if min(counts) >= MIN_NAMES]
        # Row 107's stated edge and noise assumptions, not new measurements.
        edge_bps, noise_bps = 30.3, 140
        result.update({"turn_counts": turns, "qualifying_turns": len(passed),
                       "first_qualifying_turn": min(passed, default=None),
                       "last_qualifying_turn": max(passed, default=None),
                       "missed_leg_counts": {m: v for m, v in turns.items() if m not in passed},
                       "planned_turn_shortfall": max(0, MIN_TURNS - len(passed)),
                       "same_assumption_power_screen": round(len(passed) * (edge_bps / noise_bps) ** 2, 2),
                       "earliest_vendor_month": min((min(v) for v in per_m.values()), default=None),
                       "regular_exdates": sum(map(len, dates.values())),
                       "unusable_missing_exdate": missing, "unusable_unknown_special_flag": unclear,
                       "sample_vendor_positive": sum(m in per_m.get(s, set()) for m, s in sample["pairs"])})
    write_json(c.directory / "summary.json", result)
    print(json.dumps(result, sort_keys=True, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["roster", "vendor", "count"])
    parser.add_argument("--data-dir", type=Path, default=Path(DATA_DIR))
    args = parser.parse_args()
    os.umask(0o077)
    args.data_dir.mkdir(mode=0o700, exist_ok=True)
    c = Collector(args.data_dir)
    {"roster": roster, "vendor": vendor, "count": summary}[args.stage](c)


if __name__ == "__main__":
    main()
