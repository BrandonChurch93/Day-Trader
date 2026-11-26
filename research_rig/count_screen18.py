"""Queue 18 holdings-only count. Run with off-repo SEC custody as the argument."""
import csv
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from zipfile import ZipFile
from zoneinfo import ZoneInfo


ROSTER = {
    "Berkshire": (1067983,), "Icahn": (921669,), "Scion": (1649339,),
    "Pershing Square": (1336528,), "Trian": (1345471,),
    "Appaloosa": (1006438, 1656456), "Greenlight": (1079114,), "Himalaya": (1709323,),
    "Baupost": (1061768,), "Ares": (1259313,), "Avenue": (1259927,), "Alden": (1616882,),
    "Pabrai": (1549575,), "Altimeter": (1541617,), "ValueAct": (1418814,),
    "Steel Partners": (1452857,), "Fairholme": (1056831,), "Mudrick": (1655183,),
    "Valiant": (1452689,), "GoldenTree": (1278951,), "Matrix": (1410830,),
    "Palo Alto Investors": (1306923,), "Cantillon": (1279936,), "Dalton": (1388838,),
}
PRIMARY = set(list(ROSTER)[:5])
CIKS = {cik: name for name, ciks in ROSTER.items() for cik in ciks}
EASTERN = ZoneInfo("America/New_York")
START = date(2016, 1, 1)
BULK_END = date(2026, 8, 31)
SUPPLEMENT_END = date(2026, 11, 26)
LIST_OLD = re.compile(r"^\s*([A-Z0-9]{6}) ([A-Z0-9]{2}) ([0-9])\s*\*?\s+(.+?)\s{2,}(\S.*)$")
LIST_NEW = re.compile(r"^([A-Z0-9]{8}[0-9])")
DENY_CLASS = re.compile(r"\b(?:PFD|PREF|DEBT|NOTE|ADR|ADS|GDR|DEPOS|DEP|WTS?|WARRANTS?|RTS?|RIGHTS?|UNITS?|CALL|PUT|ETF|ETN|CVT|CONV|BOND|PARTNERSHIP|LP)\b")
DENY_ISSUER = re.compile(r"\b(?:ETF|ETN|ETFS|FUND|FUNDS|PORTFOLIO|UCITS|ISHARES|PROSHARES|VANGUARD|DIREXION|SPDR|WISDOMTREE|POWERSHARES|INVESCO EXCH|ACQUISITION|ACQUISITIONS|ACQUISITN|ACQUISITIO|ACQUISITON|ACQUISITION[S]? CORP)\b")
COMMON = re.compile(r"^(?:COM(?:MON)?(?:\b|$)|CAP STK\b|CL(?:ASS)? [A-Z0-9]+(?:\b|$)|ORD(?:INARY)?\b|SHS(?:\b|$))")
SUFFIX = re.compile(r"\b(?:CORP|CORPORATION|INC|INCORPORATED|LTD|LIMITED|CO|COMPANY|PLC|NV|SA|HOLDINGS|HLDGS|HLDG|GROUP)\b")


def quarter(day):
    return day.year * 4 + (day.month - 1) // 3


def label(q):
    return f"{q // 4}Q{q % 4 + 1}"


def datestr(s):
    return date.fromisoformat(s) if len(s) == 10 and s[4] == "-" else datetime.strptime(s, "%d-%b-%Y").date()


def issuer(s):
    return " ".join(SUFFIX.sub(" ", re.sub(r"[^A-Z0-9]+", " ", s.upper())).split())


def sec_stamps(root):
    stamps, names, meta = {}, {}, {}
    for cik in CIKS:
        p = root / f"CIK{cik:010}.json"
        data = json.loads(p.read_text())
        names[str(cik)] = data["name"]
        shards = [root / obj["name"] for obj in data["filings"]["files"] if obj["filingTo"] >= "2015-07-01"]
        for raw in [data["filings"]["recent"], *(json.loads(s.read_text()) for s in shards)]:
            for a, t, typ, rpt, filed in zip(*(raw[k] for k in (
                    "accessionNumber", "acceptanceDateTime", "form", "reportDate", "filingDate")), strict=True):
                if typ != "13F-HR" or not rpt or filed < "2015-07-01":
                    continue
                if t:
                    value = datetime.fromisoformat(t.replace("Z", "+00:00"))
                    if not value.tzinfo:
                        raise ValueError("EDGAR acceptance without a time zone")
                    stamps[a] = value.astimezone(EASTERN)
                meta[a] = (cik, datestr(rpt), datestr(filed))
    return stamps, names, meta


def list_rows(root, q):
    options = sorted(root.glob(f"13flist{label(q).lower()}*.txt"))
    if not options:
        raise FileNotFoundError(f"Official List {label(q)}")
    result = {}
    with options[0].open(errors="replace") as handle:
        for raw in handle:
            line = raw.rstrip("\n\r\f").upper()
            if (m := LIST_NEW.match(line)) and len(line) >= 68:
                cusip, nm, cl, status = m[1], line[10:39].strip(), line[39:69].strip(), line[69:].strip()
            elif (m := LIST_OLD.match(line)):
                cusip = m[1] + m[2] + m[3]
                nm, cl, status = m[4].strip(), m[5].strip(), ""
            else:
                continue
            if "DELETED" in cl or "DELETED" in status or status.split() == ["D"]:
                continue
            result[cusip] = (nm, cl)
    if len(result) < 1000:
        raise ValueError(f"Official List parser {label(q)} recognized only {len(result)} rows")
    return result


def member(z, table):
    return next(name for name in z.namelist() if name.rsplit("/", 1)[-1] == table + ".tsv")


def tsv(z, table):
    return csv.DictReader(io.TextIOWrapper(z.open(member(z, table)), encoding="utf-8-sig",
                                         errors="replace", newline=""), delimiter="\t")


def active(cik, rpt):
    # Appaloosa's documented successor began on Jan 1, 2016. Do not double count.
    return (cik != 1006438 or rpt.year < 2016) and (cik != 1656456 or rpt.year >= 2016)


def bulk(root):
    archives = re.findall(r'href="[^"]+/([^"/]+form13f\.zip)"', (root / "sec-archive.html").read_text())
    selected = archives[:archives.index("2015q3_form13f.zip") + 1]
    if len(selected) != len(set(selected)):
        raise ValueError("duplicate archive selections")
    filings, hashes = {}, {}
    for fn in reversed(selected):
        path = root / fn
        with path.open("rb") as handle:
            hashes[fn] = hashlib.file_digest(handle, "sha256").hexdigest()
        with ZipFile(path) as z:
            chosen = {}
            for row in tsv(z, "SUBMISSION"):
                cik = int(row["CIK"] or 0)
                if row["SUBMISSIONTYPE"] != "13F-HR" or cik not in CIKS or not row["PERIODOFREPORT"]:
                    continue
                rpt = datestr(row["PERIODOFREPORT"])
                if not active(cik, rpt):
                    continue
                acc = row["ACCESSION_NUMBER"]
                chosen[acc] = (cik, rpt, datestr(row["FILING_DATE"]))
            summary = {row["ACCESSION_NUMBER"]: row for row in tsv(z, "SUMMARYPAGE")
                       if row["ACCESSION_NUMBER"] in chosen}
            holdings = defaultdict(list)
            picked = {acc.encode(): acc for acc in chosen}
            with z.open(member(z, "INFOTABLE")) as stream:
                header = stream.readline().decode("utf-8-sig").rstrip("\r\n").split("\t")
                cols = [header.index(k) for k in
                        ("CUSIP", "NAMEOFISSUER", "TITLEOFCLASS", "VALUE", "SSHPRNAMTTYPE", "PUTCALL")]
                for wire in stream:
                    acc = picked.get(wire.split(b"\t", 1)[0])
                    if acc is not None:
                        fields = next(csv.reader([wire.decode("utf-8", errors="replace")], delimiter="\t"))
                        c, n, cl, val, amt, opt = (fields[i] for i in cols)
                        holdings[acc].append((c, n, cl, int(val or 0), amt, opt))
            for acc, (cik, rpt, filed) in chosen.items():
                if acc in filings:
                    raise ValueError(f"archive overlap: {acc}")
                filings[acc] = (cik, rpt, filed, holdings[acc], summary.get(acc), "bulk")
    return filings, hashes


def supplement(root, meta):
    result = {}
    for a, (cik, rpt, filed) in meta.items():
        if not (BULK_END < filed <= SUPPLEMENT_END and active(cik, rpt)):
            continue
        path = root / f"{a}.submission.txt"
        if not path.exists():
            result[a] = (cik, rpt, filed, [], None, "missing supplement")
            continue
        native = path.read_text(errors="replace")
        holdings, summary = [], None
        for xml in re.findall(r"<XML>\s*(.*?)\s*</XML>", native, flags=re.S | re.I):
            tree = ET.fromstring(xml)
            for el in tree.iter():
                el.tag = el.tag.rsplit("}", 1)[-1]
            if tree.tag == "edgarSubmission":
                s = tree.find(".//summaryPage")
                if s is not None:
                    summary = {"TABLEENTRYTOTAL": s.findtext("tableEntryTotal"),
                               "TABLEVALUETOTAL": s.findtext("tableValueTotal")}
            if tree.tag != "informationTable":
                continue
            for row in tree.findall("infoTable"):
                holdings.append((row.findtext("cusip", ""), row.findtext("nameOfIssuer", ""),
                                 row.findtext("titleOfClass", ""), int(row.findtext("value", "0")),
                                 row.findtext("shrsOrPrnAmt/sshPrnamtType", ""), row.findtext("putCall", "")))
        result[a] = (cik, rpt, filed, holdings, summary, "supplement")
    return result


def liberal_without_prior(rows):
    book = sum(row[3] for row in rows)
    if book <= 0:
        return 0
    shares = Counter()
    for cusip, _, _, value, amt, opt in rows:
        if cusip.strip() and amt.strip().upper() == "SH" and not opt.strip():
            shares[cusip.strip().upper()] += value
    return sum(v > 0 and 200 * v >= book for v in shares.values())


def count(root):
    stamps, names, meta = sec_stamps(root)
    filings, archive_hashes = bulk(root)
    filings.update(supplement(root, meta))
    issue = {"primary": Counter(), "wider": Counter()}
    unresolved_liberal_observed = Counter()
    books, lists, qrows, audit = {}, {}, defaultdict(lambda: defaultdict(Counter)), []
    manager_diagnostics = defaultdict(Counter)
    for a, (cik, rpt, filed, rows, summary, method) in sorted(
            filings.items(), key=lambda kv: (stamps.get(kv[0], datetime.max.replace(tzinfo=EASTERN)), kv[0])):
        name = CIKS[cik]
        groups = ["wider", "primary"] if name in PRIMARY else ["wider"]
        rq = quarter(rpt)
        flags = []
        if a not in stamps:
            flags.append("exact acceptance missing")
        elif (cik, rpt, filed) != meta[a]:
            flags.append("bulk metadata disagrees with EDGAR metadata")
        elif abs((stamps[a].date() - filed).days) > 3:
            flags.append("acceptance and filing dates more than three days apart")
        if not rows:
            flags.append("table missing or empty")
        if not summary or not summary["TABLEENTRYTOTAL"] or int(summary["TABLEENTRYTOTAL"]) != len(rows):
            flags.append("summary row count absent or disagrees")
        book = sum(row[3] for row in rows)
        if not summary or not summary["TABLEVALUETOTAL"] or int(summary["TABLEVALUETOTAL"]) != book:
            flags.append("summary value absent or disagrees")
        key = (name, rq)
        if key in books:
            flags.append("later original")
        if flags:
            if key not in books and a in stamps:
                books[key] = (None, None)
            if filed >= START:
                manager_diagnostics[name].update(flags)
                for group in groups:
                    issue[group].update(flags)
                    if "later original" not in flags:
                        unresolved_liberal_observed[group] += liberal_without_prior(rows)
            continue
        current = defaultdict(lambda: [0, set(), set()])
        for cusip, nm, cl, value, amt, opt in rows:
            if opt.strip() or amt.strip().upper() != "SH" or not cusip:
                continue
            v = current[cusip.strip().upper()]
            v[0] += value
            v[1].add(nm.upper())
            v[2].add(cl.upper())
        t = stamps[a]
        fq = quarter(t.date())
        prior, prior_t = books.get((name, rq - 1), (None, None))
        books[key] = current, t
        if not START <= t.date() <= SUPPLEMENT_END:
            continue
        if prior is None or not prior_t < t:
            manager_diagnostics[name]["no valid earlier original for immediately prior quarter"] += 1
            for group in groups:
                issue[group]["no valid earlier original for immediately prior quarter"] += 1
                unresolved_liberal_observed[group] += liberal_without_prior(rows)
            continue
        qrows[fq][name]["valid_filing_pairs"] += 1
        if rq not in lists:
            lists[rq] = list_rows(root, rq)
        listing = lists[rq]
        prior_names = {issuer(nm) for _, nms, _ in prior.values() for nm in nms}
        # Six-character issuer stem is additional protection against a class change.
        prior_stems = {cusip[:6] for cusip in prior}
        for cusip, (value, nms, cls) in current.items():
            if value <= 0 or 200 * value < book or cusip in prior:
                continue
            qrows[fq][name]["liberal_new_share_cusips"] += 1
            if cusip[:6] in prior_stems or ({issuer(nm) for nm in nms} - {""}) & prior_names:
                qrows[fq][name]["prior_issuer_exclusion"] += 1
                continue
            official = listing.get(cusip)
            if not official:
                qrows[fq][name]["official_list_missing"] += 1
                continue
            nm, cl = official
            if (any(DENY_ISSUER.search(n) for n in {*nms, nm}) or
                    any(DENY_CLASS.search(c) for c in {*cls, cl}) or not COMMON.search(cl)):
                qrows[fq][name]["class_or_issuer_exclusion"] += 1
                continue
            qrows[fq][name]["official_list_common_proxy"] += 1
            audit.append((label(fq), name, a, t.isoformat(), label(rq), cusip, nm, cl, method))
    quarterly = []
    for fq in range(quarter(START), quarter(SUPPLEMENT_END) + 1):
        managers = qrows[fq]
        primary = sum((managers[n] for n in PRIMARY), Counter())
        wider = sum(managers.values(), Counter())
        quarterly.append({"filing_quarter": label(fq), "primary": dict(primary), "wider_shown_only": dict(wider)})
    totals = {}
    for group in ("primary", "wider_shown_only"):
        totals[group] = dict(sum((Counter(r[group]) for r in quarterly), Counter()))
    managers = {name: dict(sum((m.get(name, Counter()) for m in qrows.values()), Counter()))
                for name in ROSTER}
    # Reconcile any original in the timestamp catalogue that does not appear in the bulk tables.
    omitted = {kind: sum(1 for a, (cik, rpt, filed) in meta.items() if a not in filings and active(cik, rpt)
                           and START <= filed <= BULK_END and (kind == "wider" or CIKS[cik] in PRIMARY))
               for kind in ("primary", "wider")}
    supplement_totals = {
        "primary": sum(name in PRIMARY and src == "supplement" for _, name, *_, src in audit),
        "wider_shown_only": sum(src == "supplement" for *_, src in audit),
    }
    primary_audit = [r for r in audit if r[1] in PRIMARY]
    concentration = {
        "primary_distinct_cusips": len({r[5] for r in primary_audit}),
        "primary_distinct_quarter_cusips": len({(r[0], r[5]) for r in primary_audit}),
    }
    return {"kind": "price_blind_sec_13f_aggregate", "bulk_archive_count": len(archive_hashes),
            "bulk_archive_sha256": archive_hashes, "bulk_end": str(BULK_END),
            "filing_start": str(START), "observed_through": str(SUPPLEMENT_END),
            "catalogue_originals_missing_from_bulk": omitted, "roster": ROSTER, "sec_filer_names": names,
            "filing_diagnostics": issue, "manager_diagnostics": manager_diagnostics,
            "manager_totals": managers, "quarterly": quarterly, "totals": totals,
            "supplement_common_by_group": supplement_totals, "concentration": concentration,
            "unresolved_current_observed_share_rows_at_floor_assuming_all_new": unresolved_liberal_observed}, sorted(audit)


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    result, private = count(root)
    if len(sys.argv) > 2 and sys.argv[2] == "--save-private-audit":
        with (root / "queue18.private.tsv").open("w") as stream:
            w = csv.writer(stream, delimiter="\t")
            w.writerow(("filing_q", "manager", "accession", "accepted_et", "report_q", "cusip", "issuer", "class", "source"))
            w.writerows(private)
    print(json.dumps(result, indent=2, sort_keys=True))
