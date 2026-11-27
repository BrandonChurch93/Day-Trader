"""Ledger 240, queue 150: one census of the public Apify Store listing.

A count, not a test of a method and not an income figure. It reads the
documented public endpoint GET https://api.apify.com/v2/store with no key,
keeps a few fields per Actor in a private folder, and prints counts.
Marks and limits come from config/thresholds.yaml key count_150_apify_store.

  python3 research_rig/count_150_apify_store.py run      once only
  python3 research_rig/count_150_apify_store.py report   any time, reads the private file
"""
import json, statistics, sys, time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load(open(ROOT / "config/thresholds.yaml"))["count_150_apify_store"]["value"]
OFF = Path(CFG["private_dir"])
ROWS = OFF / "actors.jsonl"
DONE = OFF / "run_done.json"


def run():
    OFF.mkdir(parents=True, exist_ok=True)
    if ROWS.exists() or DONE.exists():
        sys.exit("refused: this census already ran; use report")
    seen, total, offset, pages = set(), None, 0, 0
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(ROWS, "w") as out:
        while pages < CFG["max_pages"]:
            url = f'{CFG["endpoint"]}?limit={CFG["page_size"]}&offset={offset}'
            with urlopen(Request(url, headers={"User-Agent": CFG["user_agent"]}), timeout=60) as r:
                if r.status != 200:
                    sys.exit(f"stopped: status {r.status} at offset {offset}; no retry")
                data = json.load(r)["data"]
            total = data["total"]
            for it in data["items"]:
                if it["id"] in seen:
                    continue
                seen.add(it["id"])
                s = it.get("stats") or {}
                p = it.get("currentPricingInfo") or {}
                out.write(json.dumps({
                    "id": it["id"], "user": it.get("username"), "cats": it.get("categories") or [],
                    "model": p.get("pricingModel"), "u30": s.get("totalUsers30Days") or 0,
                    "u90": s.get("totalUsers90Days") or 0, "uall": s.get("totalUsers") or 0,
                    "runs": s.get("totalRuns") or 0, "reviews": s.get("actorReviewCount") or 0,
                    "verified": bool(it.get("isVerified")),
                }) + "\n")
            pages += 1
            offset += data["count"]
            if data["count"] == 0 or offset >= total:
                break
            time.sleep(CFG["seconds_between_requests"])
    DONE.write_text(json.dumps({"started": started, "ended": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "pages": pages, "listed_total": total, "kept": len(seen)}))
    report()


def report():
    meta = json.loads(DONE.read_text())
    rows = [json.loads(x) for x in open(ROWS)]
    paid = [r for r in rows if r["model"] and r["model"] != "FREE"]
    n = len(paid)
    by_pub = defaultdict(int)
    for r in paid:
        by_pub[r["user"]] += r["u30"]
    pubs = sorted(by_pub.values(), reverse=True)
    all30 = sum(pubs)
    top = set(sorted(by_pub, key=by_pub.get, reverse=True)[:CFG["top_publishers"]])
    share = lambda k: sum(r["u30"] >= k for r in paid) / n
    a = share(CFG["users_floor"])
    b = statistics.median(pubs)
    c = sum(pubs[:CFG["top_publishers"]]) / all30
    rest = [r for r in paid if r["user"] not in top]
    out = {
        "run": meta, "actors_kept": len(rows), "pricing_models": dict(Counter(r["model"] or "none" for r in rows)),
        "paid_actors": n, "paid_publishers": len(pubs),
        "paid_share_with_30d_users_at_least": {str(k): round(share(k), 4) for k in (1, 2, 10, 100, 1000)},
        "paid_actor_30d_users_median": statistics.median(r["u30"] for r in paid),
        "publisher_30d_users_median": b,
        "publisher_30d_users_quartiles": [round(x, 1) for x in statistics.quantiles(pubs, n=4)],
        "publishers_with_30d_users_at_least": {str(k): sum(x >= k for x in pubs) for k in (10, 100, 1000)},
        "share_of_30d_users_top_publishers": round(c, 4),
        "outside_top_publishers": {
            "paid_actors": len(rest), "with_floor_users": sum(r["u30"] >= CFG["users_floor"] for r in rest),
            "categories_of_those": Counter(k for r in rest if r["u30"] >= CFG["users_floor"] for k in r["cats"]).most_common(15),
        },
        "marks": {
            "A_share_paid_with_floor_users": [round(a, 4), CFG["mark_share_min"], a >= CFG["mark_share_min"]],
            "B_publisher_median_30d_users": [b, CFG["mark_publisher_median_min"], b >= CFG["mark_publisher_median_min"]],
            "C_top_publisher_share": [round(c, 4), CFG["mark_top_share_max"], c <= CFG["mark_top_share_max"]],
        },
    }
    out["all_marks_met"] = all(v[2] for v in out["marks"].values())
    # Added after the run, description only, no mark attached.
    per_pub = Counter(r["user"] for r in paid)
    big = [v for v in per_pub.values() if v >= 100]
    out["added_after_run"] = {
        "paid_actors_per_publisher_median": statistics.median(per_pub.values()),
        "paid_actors_per_publisher_max": max(per_pub.values()),
        "publishers_with_100_or_more_paid_actors": len(big), "paid_actors_they_hold": sum(big),
        "paid_share_with_at_most_1_user_30d": round(sum(r["u30"] <= 1 for r in paid) / n, 4),
        "paid_share_with_no_review": round(sum(r["reviews"] == 0 for r in paid) / n, 4),
    }
    fl = CFG["users_floor"]
    for cat in ("GOVERNMENT_AND_PUBLIC_DATA", "SOCIAL_MEDIA", "FINANCIAL_DATA"):
        sub = [r for r in paid if cat in r["cats"]]
        out["added_after_run"]["category_" + cat] = {
            "paid_actors": len(sub), "share_with_floor_users": round(sum(r["u30"] >= fl for r in sub) / len(sub), 4)}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"run": run, "report": report}[sys.argv[1]]()
