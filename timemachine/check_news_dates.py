"""Check the three keyless news sites for stories given a date earlier than when they were made.
Post numbers on these sites rise as posts are made. A story dated early but numbered far above
stories dated days later was made later and given an old date. Writes timemachine/news_date_check.json: counts and post numbers only, no story text.

python3 timemachine/check_news_dates.py"""
import json, time, urllib.request, urllib.parse, bisect, datetime as dt
from pathlib import Path
UA = "Day-Trader research modernsoftworks@gmail.com"
SITES = {"newsbtc": "www.newsbtc.com", "cryptopotato": "cryptopotato.com", "cryptoslate": "cryptoslate.com"}
out = {}
for name, host in SITES.items():
    posts, page = [], 1
    while True:
        q = urllib.parse.urlencode({"per_page": 100, "page": page, "after": "2026-05-31T23:59:59", "before": "2026-11-25T00:00:00",
                                    "orderby": "date", "order": "asc", "_fields": "id,date_gmt,modified_gmt,link"})
        req = urllib.request.Request(f"https://{host}/wp-json/wp/v2/posts?{q}", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.load(r)
        except Exception as e:
            if "400" in str(e): break
            time.sleep(5); continue
        if not d: break
        posts += d; page += 1; time.sleep(1.2)
        if len(d) < 100: break
    ts = lambda s: dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()
    posts.sort(key=lambda x: x["date_gmt"])
    t = [ts(p["date_gmt"]) for p in posts]; ids = [p["id"] for p in posts]
    flagged = []
    for i, p in enumerate(posts):
        j = bisect.bisect_left(t, t[i] + 2 * 86400)          # posts dated two days or more later
        later = sorted(ids[j:j + 200])
        if len(later) < 20: continue
        med = later[len(later) // 2]
        if ids[i] > med:                                     # numbered above the middle of posts dated 2+ days later
            flagged.append({"id": ids[i], "date_gmt": p["date_gmt"], "modified_gmt": p["modified_gmt"], "link": p["link"], "later_median_id": med})
    out[name] = {"posts": len(posts), "first": posts[0]["date_gmt"] if posts else None, "last": posts[-1]["date_gmt"] if posts else None,
                 "modified_before_date": sum(1 for p in posts if p["modified_gmt"] < p["date_gmt"]),
                 "max_hours_modified_before_date": round(max([0] + [(ts(p["date_gmt"]) - ts(p["modified_gmt"])) / 3600 for p in posts]), 1),
                 "flagged_dated_early": len(flagged),
                 "flagged": [{k: f[k] for k in ("id", "date_gmt", "later_median_id", "link")} for f in flagged[:40]]}
    print(name, {k: v for k, v in out[name].items() if k != "flagged"}, flush=True)
out["checked_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
(Path(__file__).resolve().parent / "news_date_check.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
