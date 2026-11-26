"""Count-only Form 4 feasibility; output private dates only to the work folder."""
import argparse
import collections as c
import datetime as dt
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

START = dt.date(2016, 1, 1)
END = dt.date(2025, 12, 31)
WINDOW = dt.timedelta(days=30)
ET = ZoneInfo("America/New_York")
ROLE = re.compile(r"\b(officer|director)\b", re.I)
COMMON = re.compile(r"\b(common stock|common shares?|ordinary shares?)\b", re.I)
SHARE_CLASS = re.compile(r"\bclass\s+([a-z0-9]+)\b", re.I)
OTHER = re.compile(r"\b(preferred|convertible|depositary|adr|ads|unit[s]?|rsu|restricted|option|warrant|tracker|tracking|right[s]?)\b", re.I)
FUND = re.compile(r"\b(funds?|etfs?|exchange.traded|closed.end|investment trust|business development company)\b", re.I)
PRIVATE = re.compile(r"\b(private(?:ly)?|off.market|negotiated|subscription|direct offering|registered direct|underwrit\w*|public offering|initial public|ipo|rights offering|purchase agreement|employee stock purchase|espp|dividend reinvestment|drip|stock purchase plan|directly from (?:the )?(?:issuer|company)|(?:upon|through|pursuant to|result(?:ed|ing) from)\s+(?:the )?(?:exercise|conversion))\b", re.I)
OFFER_PRICE = re.compile(r"\b(?:offering|subscription) price\b[^.;\n$]{0,45}\$\s*([0-9,]+(?:\.[0-9]+)?)", re.I)
MARKET = re.compile(r"\b(open[- ]market|(?:purchased|executed|transactions?) on (?:the )?(?:nasdaq|nyse|new york stock exchange))\b", re.I)
PLAN = re.compile(r"\b(?:rule\s*)?10b\s*[- ]?5\s*[-–‑ ]?\(?1\)?|\b(?:prearranged|pre-arranged|preset) trading plan", re.I)
NEG_PLAN = re.compile(r"(?:not|no)\b[^.!?;]{0,45}(?:10b\s*[- ]?5\s*[-–‑ ]?\(?1\)?|trading plan)", re.I)


def date(raw):
    return dt.datetime.strptime(raw, "%d-%b-%Y").date()


def num(raw):
    try:
        v = Decimal(raw)
        return v if v.is_finite() and v > 0 else None
    except (InvalidOperation, TypeError):
        return None


def clusters(rows, clocks=None):
    """One cluster per class per 30 days; when clocking, retain all same-day inputs."""
    by = c.defaultdict(lambda: c.defaultdict(list))
    for day, issuer, klass, owner, accession in rows:
        by[issuer, klass][day].append((owner, accession))
    for (issuer, klass), days in by.items():
        history = c.deque()
        last = None
        for day, items in sorted(days.items()):
            while history and day - history[0][0] >= WINDOW:
                history.popleft()
            before = {owner for _, owner in history}
            history.extend((day, owner) for owner, _ in items)
            if day < START or day > END or (last and day - last < WINDOW):
                continue
            if len(before) >= 3 or len(before | {owner for owner, _ in items}) < 3:
                continue
            eligible = sorted({acc for owner, acc in items if owner not in before})
            if not eligible:
                continue
            last = day
            trigger = None
            if clocks is not None and all(acc in clocks and clocks[acc].astimezone(ET).date() == day for acc in eligible):
                for owner, acc in sorted(((o, a) for o, a in items if a in eligible), key=lambda item: (clocks[item[1]], item[1])):
                    before.add(owner)
                    if len(before) >= 3:
                        trigger = acc
                        break
            yield (day, issuer, klass, eligible, trigger)


def count(base):
    manifest = {}
    with (base / "sec_zips.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            manifest[row["quarter"]] = row["extract_sha256"]
    exact_quarters = {"2015q4", "2026q1"} | {f"{y}q{q}" for y in range(2016, 2026) for q in range(1, 5)}
    total = c.Counter()
    status = c.Counter()
    venue = c.Counter()
    by_year = c.Counter()
    bands = c.defaultdict(list)
    accessions = set()
    economic = set()
    for quarter in sorted(exact_quarters):
        path = base / "sec_extract" / (quarter + ".json.gz")
        with path.open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != manifest[quarter]:
                raise ValueError("Quarter digest mismatch")
        with gzip.open(path, "rt") as handle:
            data = json.load(handle)
        subs = {r["ACCESSION_NUMBER"]: r for r in data["submission"]}
        owners = c.defaultdict(dict)
        notes = c.defaultdict(dict)
        grouped = c.defaultdict(list)
        for r in data["owner"]:
            owners[r["ACCESSION_NUMBER"]][r["RPTOWNERCIK"]] = r["RPTOWNER_RELATIONSHIP"]
        for r in data["footnotes"]:
            notes[r["ACCESSION_NUMBER"]][r["FOOTNOTE_ID"]] = r["FOOTNOTE_TXT"]
        for r in data["nonderiv_p"]:
            grouped[r["ACCESSION_NUMBER"]].append(r)
        for acc, items in sorted(grouped.items()):
            s = subs[acc]
            if s["DOCUMENT_TYPE"] != "4" or acc in accessions:
                continue
            accessions.add(acc)
            day = date(s["FILING_DATE"])
            if not START - WINDOW <= day <= END:
                continue
            in_sample = day >= START
            n = total if in_sample else c.Counter()
            own = owners[acc]
            n["original_P_non_derivative_rows"] += len(items)
            if len(own) != 1 or not ROLE.search(next(iter(own.values()))):
                continue
            n["single_officer_or_director_P_rows"] += len(items)
            issuer = int(s["ISSUERCIK"])
            owner = int(next(iter(own)))
            if FUND.search(s["ISSUERNAME"]) or not s["ISSUERTRADINGSYMBOL"].strip():
                continue
            buckets = c.defaultdict(Decimal)
            seen = set()
            for r in items:
                sk = r["NONDERIV_TRANS_SK"]
                if sk in seen:
                    continue
                seen.add(sk)
                title = r["SECURITY_TITLE"]
                klass = SHARE_CLASS.search(title)
                klass = klass[1].upper() if klass else "UNSPECIFIED"
                shares, px = num(r["TRANS_SHARES"]), num(r["TRANS_PRICEPERSHARE"])
                if (not COMMON.search(title) or OTHER.search(title) or
                    r["TRANS_ACQUIRED_DISP_CD"] != "A" or r["DIRECT_INDIRECT_OWNERSHIP"] != "D" or
                    not shares or not px or not r["TRANS_DATE"] or date(r["TRANS_DATE"]) > day or
                    r["EQUITY_SWAP_INVOLVED"].upper() in {"Y", "1", "TRUE"}):
                    continue
                ids = {i.strip() for k, v in r.items() if k.endswith("_FN") and v for i in v.split(",")}
                txt = " ".join([s.get("REMARKS") or ""] + [notes[acc].get(i, "") for i in sorted(ids)])
                check = (s.get("AFF10B5ONE") or "").upper().strip()
                if in_sample:
                    status[check or "blank_or_absent"] += 1
                if check in {"Y", "1", "TRUE"} or PLAN.search(NEG_PLAN.sub("", txt)):
                    n["flagged_plan_rows"] += 1
                    continue
                if PRIVATE.search(txt) or any(num(v.replace(",", "")) == px for v in OFFER_PRICE.findall(txt)):
                    n["explicit_nonmarket_rows"] += 1
                    continue
                market = bool(MARKET.search(txt))
                nonplan = bool(NEG_PLAN.search(txt)) or check in {"N", "0", "FALSE"}
                if in_sample:
                    venue["market" if market else "ambiguous"] += 1
                key = (issuer, klass, owner, r["TRANS_DATE"], shares, px)
                if key in economic:
                    n["matched_economic_duplicate_rows"] += 1
                    continue
                economic.add(key)
                for band, admitted in (("primary", True), ("market_language", market), ("strict", market and nonplan)):
                    if admitted:
                        buckets[band, klass] += shares * px
            for (band, klass), dollars in buckets.items():
                if dollars >= 25000:
                    bands[band].append((day, issuer, klass, owner, acc))
                    if in_sample:
                        n[f"{band}_filing_classes"] += 1
                        by_year[band, day.year] += 1
    return bands, total, status, venue, by_year


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Private source folder")
    args = parser.parse_args()
    base = args.source / "plan36_provenance"
    bands, total, status, venue, by_year = count(base)
    target = {acc for band in ("primary", "market_language", "strict") for row in clusters(bands[band]) for acc in row[3]}
    clocks = {}
    conflicts = set()
    with (base / "accept_times.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            acc, stamp = row["accession"], row["accepted"]
            if acc not in target or row["form"] != "4" or not stamp or not stamp.endswith("Z"):
                continue
            stamp = dt.datetime.fromisoformat(stamp)
            if acc in clocks and clocks[acc] != stamp:
                conflicts.add(acc)
            clocks[acc] = stamp
    for acc in conflicts:
        clocks.pop(acc)
    supplemental = args.source / "sec_clock_supplement.json"
    if supplemental.exists():
        with supplemental.open() as handle:
            for acc, stamp in json.load(handle).items():
                if acc in target and acc not in clocks:
                    clocks[acc] = dt.datetime.fromisoformat(stamp)
    print("row and filing counts", dict(total))
    print("checkbox observations", dict(status), "venue observations after exclusions", dict(venue))
    for band, rows in bands.items():
        records = sorted(clusters(rows, clocks))
        print(band, "filing classes by year", {y: by_year[band, y] for y in range(2016, 2026)})
        want = {acc for r in records for acc in r[3]}
        print(band, "provisional clusters", len(records), "issuers", len({r[1] for r in records}), "by year", dict(sorted(c.Counter(r[0].year for r in records).items())))
        print(band, "clock accessions", len(want), "locally matched", len(want & clocks.keys()),
              "conflicts", len(want & conflicts), "clusters clocked", sum(bool(r[4]) for r in records))
        with (args.source / f"{band}_clock_and_calendar.json").open("w") as handle:
            json.dump([[str(day), issuer, klass, accs, trigger] for day, issuer, klass, accs, trigger in records], handle)
    with (args.source / "candidate_clocks.json").open("w") as handle:
        json.dump({acc: stamp.isoformat() for acc, stamp in clocks.items()}, handle)


if __name__ == "__main__":
    main()
