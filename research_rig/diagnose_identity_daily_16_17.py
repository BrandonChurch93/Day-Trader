"""Counts-only comparison of the authorized hourly and UTC-day identity rules."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
from pathlib import Path
import unittest

try:
    from . import check_identity_levels_16_17 as L
except ImportError:
    import check_identity_levels_16_17 as L

F = L.F
DAY = 24 * F.H
OUT = "identity_daily_diagnostic_16_17.json"
CORRECTED = "identity_daily_corrected_16_17.json"
DATED = "identity_months_16_17.json"
SATS = {(28683,"spot","1000SATSUSDT"),(28683,"futures","1000SATSUSDT")}


def utc_day(t):
    return t // DAY * DAY


def daily_matches(cmc, multiplier, low, high):
    scaled = cmc * multiplier * 100
    return low * 95 <= scaled <= high * 105


def bins(rows):
    result = [0] * 10
    for r in rows:
        m, n = r["matched_months"], r["comparable_months"]
        if n >= 3:
            result[min(9, m * 10 // n)] += 1
    return result


def by_day(files, days):
    ranges = {}
    for key, meta in sorted(files.items()):
        relevant = {d for d in days if meta["first"] <= d+DAY-F.H and d <= meta["last"]}
        if not relevant:
            continue
        if meta["where"] not in {"replay_13", "replay_16"}:
            raise ValueError(f"unknown archive location for {key}")
        raw = F.archive_root(key, meta["where"]).read_bytes()
        if F.digest(raw) != meta["sha256"]:
            raise ValueError(f"archive fingerprint changed for {key}")
        for row in F.F.zip_rows(raw):
            t = F.F.open_epoch(row[0])
            d = utc_day(t)
            if d not in relevant:
                continue
            try:
                hi,lo = Decimal(row[2]),Decimal(row[3])
                if not hi.is_finite() or not lo.is_finite() or not 0 < lo <= hi:
                    raise ValueError("invalid daily-range input")
            except (ArithmeticError, IndexError, ValueError):
                raise ValueError(f"unusable high or low in {key} at {t}") from None
            if t % F.H:
                raise ValueError(f"non-hourly row in {key} at {t}")
            hours, low, high = ranges.setdefault(d, (set(),lo,hi))
            if t in hours:
                raise ValueError(f"duplicate hour in {key} at {t}")
            hours.add(t)
            ranges[d] = hours,min(low,lo),max(high,hi)
    return {d:(lo,hi) for d,(hours,lo,hi) in ranges.items() if len(hours)==24}


def main(workers, correct_sats_unit=False, dated=False):
    note_raw = (F.DATA/L.NOTICE).read_bytes()
    hour_raw = (F.DATA/L.OUT).read_bytes()
    snap_raw = (F.DATA/"snapshots_16.json").read_bytes()
    manifest_raw = [(F.DATA/n).read_bytes() for n in L.MANIFESTS]
    hourly = json.loads(hour_raw)
    if (hourly["notice_sha256"] != F.digest(note_raw)
        or hourly["snapshots_sha256"] != F.digest(snap_raw)
        or hourly["archive_manifest_sha256"] != {k:F.digest(v) for k,v in zip(L.MANIFESTS,manifest_raw)}):
        raise ValueError("hourly identity result and daily diagnostic inputs differ")
    inventory = F.json_read(F.DATA/"identity_inventory.json")
    notice = {L.mapping(r):r for r in json.loads(note_raw)["rows"] if r["checked"]}
    a = {L.mapping(r):r for r in hourly["rows"]}
    if set(a) != set(notice):
        raise ValueError("hourly level results have different mappings")
    baseline_raw = (F.DATA/OUT).read_bytes() if correct_sats_unit else None
    baseline = json.loads(baseline_raw) if baseline_raw else None
    selected = SATS if correct_sats_unit else set(notice)
    if baseline and (baseline["hourly_results_sha256"] != F.digest(hour_raw)
                     or {L.mapping(r) for r in baseline["rows"]} != set(notice)):
        raise ValueError("the corrected pass must use the same hourly diagnostic mappings")
    snapshots = json.loads(snap_raw)
    quotes, pages = L.quotes_by_coin(snapshots, {cid for cid,_,_ in selected})
    page_dates = {s["date"][:7]:s["date"] for s in snapshots["viewed"] if not s.get("hole")}
    index = L.archive_index([json.loads(raw) for raw in manifest_raw])
    jobs = defaultdict(lambda: defaultdict(list))
    for k,r in notice.items():
        if k not in selected:
            continue
        cid,market,pair = k
        info = inventory[str(cid)]["markets"].get(market+"/"+pair)
        segs = info["segments"] if info else [(None,None)]
        bounds = [(L.epoch(a) if a else -10**12,L.epoch(b) if b else 10**12) for a,b in segs]
        mult = int(r["multiplier"].removesuffix("x"))
        if k in SATS and (correct_sats_unit or dated):
            if k not in SATS or inventory[str(cid)]["tickers"] != ["1000SATS"] or mult != 1000:
                raise ValueError("unexpected source quote unit for the SATS correction")
            # The quote already represents 1,000 SATS, the same unit as the pair.
            mult = 1
        for month,(t,p) in quotes[cid].items():
            d = utc_day(t)
            if any(lo<=d and d+DAY<=hi for lo,hi in bounds):
                jobs[market,pair][d].append((k,p,mult,page_dates[month],d+DAY))

    def per_pair(key):
        matched,compared = Counter(),Counter()
        monthly = defaultdict(list)
        todo = jobs[key]
        for d,(lo,hi) in by_day(index.get(key,{}),todo).items():
            for k,p,mult,date,quote_day_end in todo[d]:
                hit = daily_matches(p,mult,lo,hi)
                compared[k] += 1
                matched[k] += hit
                if dated:
                    monthly[k].append([date,quote_day_end,hit])
        return matched,compared,monthly

    hits,totals = Counter(),Counter()
    monthly = {}
    with ThreadPoolExecutor(workers) as pool:
        for matched,compared,by_mapping in pool.map(per_pair,sorted(jobs)):
            hits.update(matched)
            totals.update(compared)
            monthly.update(by_mapping)
    b = [dict(id=k[0],market=k[1],pair=k[2],matched_months=hits[k],comparable_months=totals[k])
         for k in sorted(selected)]
    if dated:
        for r in b:
            r["months"] = sorted(monthly.get(L.mapping(r),[]))
        F.F.put_json(F.DATA/DATED,{"snapshots_sha256":F.digest(snap_raw),
                      "notice_sha256":F.digest(note_raw),
                      "archive_manifest_sha256":hourly["archive_manifest_sha256"],"rows":b})
        return
    if baseline:
        previous = {L.mapping(r):r for r in baseline["rows"]}
        if any(r["comparable_months"] != previous[L.mapping(r)]["comparable_months"] for r in b):
            raise ValueError("fixing the SATS quote units must not change comparable months")
        F.F.put_json(F.DATA/CORRECTED, {
            "hourly_results_sha256":F.digest(hour_raw),
            "original_daily_results_sha256":F.digest(baseline_raw),
            "daily_checker_sha256":F.digest(Path(__file__).read_bytes()),
            "corrected_rows":b,
        })
        return
    removals = []
    for r in b:
        k = L.mapping(r)
        if a[k]["status"] == "REMOVED":
            removals.append({**r,"name":notice[k]["name"],
                             "hourly_matched_months":a[k]["matched_months"],
                             "hourly_comparable_months":a[k]["comparable_months"]})
    ab,bb = bins(a.values()),bins(b)
    F.F.put_json(F.DATA/OUT, {
        "hourly_results_sha256":F.digest(hour_raw),
        "daily_checker_sha256":F.digest(Path(__file__).read_bytes()),
        "cmc_pages":pages,"hourly_histogram":ab,"daily_histogram":bb,
        "hourly_removed_with_daily_counts":removals,"rows":b,
    })
    print("rule\t0-10\t10-20\t20-30\t30-40\t40-50\t50-60\t60-70\t70-80\t80-90\t90-100")
    print("a\t"+"\t".join(map(str,ab)))
    print("b\t"+"\t".join(map(str,bb)))
    print("name\tmarket\tpair\ta matched\ta comparable\tb matched\tb comparable")
    for r in removals:
        print("\t".join(str(r[k]) for k in ("name","market","pair","hourly_matched_months",
                                           "hourly_comparable_months","matched_months","comparable_months")))


class DailyTest(unittest.TestCase):
    def test_utc_day(self):
        self.assertEqual(utc_day(L.epoch("2024-01-01T23:59:00Z")),
                         L.epoch("2024-01-01T00:00:00Z"))

    def test_daily_inclusive_band(self):
        lo,hi = Decimal(20),Decimal(30)
        for p in ("0.019", "0.0315"):
            self.assertTrue(daily_matches(Decimal(p),1000,lo,hi))
        for p in ("0.0189", "0.0316"):
            self.assertFalse(daily_matches(Decimal(p),1000,lo,hi))

    def test_bins_exclude_thin_and_cap_perfect(self):
        rows = [dict(matched_months=m,comparable_months=n) for m,n in ((0,3),(1,10),(3,3),(1,2),(9,10))]
        self.assertEqual(bins(rows),[1,1,0,0,0,0,0,0,0,2])


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selftest",action="store_true")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--correct-sats-unit",action="store_true")
    mode.add_argument("--dated-evidence",action="store_true")
    p.add_argument("--workers",type=int,default=2,choices=(1,2))
    opts = p.parse_args()
    if opts.selftest:
        unittest.main(argv=[__file__])
    else:
        main(opts.workers,opts.correct_sats_unit,opts.dated_evidence)
