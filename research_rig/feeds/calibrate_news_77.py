"""One seeded UTC day of GDELT counts. Do not write article metadata or archives."""
from collections import Counter
from datetime import datetime, timezone
from html import unescape
import json
import random
import re
import time
from urllib.parse import urlsplit

from research_rig.feeds import news_77 as news

DAY = 86400
PUBLISHERS = ("coindesk.com", "cointelegraph.com", "decrypt.co", "theblock.co", "cryptoslate.com",
              "beincrypto.com", "u.today", "dlnews.com", "blockworks.co", "cryptonews.com")
TERMS = {w: re.compile(rf"\b{w}\b", re.I) for w in ("bitcoin", "solana", "crypto")}
OPEN = re.compile(rb"<PAGE_TITLE>", re.I)
COMPLETE = re.compile(rb"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.I | re.S)
REASONS = ("kept", "non_web_collection", "pilot_title_format", "pilot_title_length",
           "outside_solana_basket", "alias_miss", "excluded_domain", "url_rejected", "duplicate")
METRICS = ("records", "page_title", *TERMS)


def domain(url):
    try:
        return (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def publisher(host):
    return next((p for p in PUBLISHERS if host == p or host.endswith("." + p)), None)


def decoded_title(m):
    return " ".join(unescape(m[1].decode("utf-8", errors="replace")).split())


def classify(fields, url, host, tick, coins, seen_url, seen_title):
    if fields[2] != b"1":
        return "non_web_collection"
    strict = news.TITLE.search(fields[26]) if b"<PAGE_TITLE>" in fields[26] else None
    if strict is None:
        return "pilot_title_format"
    title = decoded_title(strict)
    if not 2 <= len(title) <= 512:
        return "pilot_title_length"
    if "SOL" not in coins:
        return "outside_solana_basket"
    if "SOL" not in news.matched(title, coins):
        return "alias_miss"
    linked = news.link(url)
    if linked is None:
        return "excluded_domain" if set(host.split(".")) & news.BLOCKED else "url_rejected"
    row = {"first_seen_utc": tick, "source_domain": linked[0], "title": title, "url": linked[1],
           "matched_coin": "SOL"}
    return "kept" if news.unique_rows([row], seen_url, seen_title) else "duplicate"


def scan_day():
    weeks, schedule = news.batches()
    jobs = {t: coins for t, _, coins in schedule}
    start = news.utc(weeks[0][0]) + random.Random(news.SEED).randrange(news.WEEK // DAY) * DAY
    ticks = range(start, start + DAY, news.QUARTER)
    news.check_space(news.ROOT)
    prior, original_day = [], 0
    for r in news.read_file(news.ROOT, "rows.jsonl"):
        if r["matched_coin"] != "SOL":
            continue
        t = r["first_seen_utc"]
        if t < start:
            prior.append(r)
        elif t in ticks and TERMS["solana"].search(r["title"]):
            original_day += 1
    seen_url, seen_title = set(), set()
    news.unique_rows(prior, seen_url, seen_title)
    by_domain = {p: dict.fromkeys(METRICS, 0) for p in PUBLISHERS}
    source_reasons, all_reasons = Counter(), Counter()
    total = compressed = 0
    a = news.Archive()
    for i, t in enumerate(ticks):
        news.check_space(news.ROOT)
        if i:
            time.sleep(news.PAUSE)  # actual quiet time after the prior batch
        news.check_space(news.ROOT)
        raw = a.get(t)
        compressed += len(raw)
        for f in news.batch_fields(raw, t):
            total += 1
            url = f[4].decode("utf-8", errors="replace")
            host = domain(url)
            p = publisher(host)
            if p:
                by_domain[p]["records"] += 1
                by_domain[p]["page_title"] += bool(OPEN.search(f[26]))
            m = COMPLETE.search(f[26])
            if not m:
                continue
            title = decoded_title(m)
            found = {w for w, pattern in TERMS.items() if pattern.search(title)}
            if p:
                for w in found:
                    by_domain[p][w] += 1
            if "solana" in found:
                reason = classify(f, url, host, t, jobs[t], seen_url, seen_title)
                all_reasons[reason] += 1
                if p:
                    source_reasons[reason] += 1
            elif "SOL" in jobs[t]:
                # Earlier cashtag/bare-ticker matches can still affect duplicate history.
                classify(f, url, host, t, jobs[t], seen_url, seen_title)
    return {"seed": news.SEED, "date_utc": datetime.fromtimestamp(start, timezone.utc).date().isoformat(),
            "batches": len(ticks), "compressed_bytes": compressed, "gkg_records": total,
            "publishers": by_domain, "publisher_solana": {r: source_reasons[r] for r in REASONS},
            "all_solana": {r: all_reasons[r] for r in REASONS}, "original_pilot_solana_kept": original_day}


if __name__ == "__main__":
    print(json.dumps(scan_day(), sort_keys=True))
