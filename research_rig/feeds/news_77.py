"""TM09 two scored-week sample. Only GDELT metadata goes to private custody."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html import unescape
from io import BytesIO
import json
import os
from pathlib import Path
import random
import re
import stat
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import urllib.request
from zipfile import ZipFile

REPO = Path(__file__).resolve().parents[2]
WORKSPACE = Path("/home/user/workspace")
ROOT = WORKSPACE / "rig/data/news_feed_77"
REG = REPO / "timemachine/TM07_REGISTRATION_weeks.json"
REG_SHA = "4014b1ef73612c8d0996a719e9984dc934459100aa7a26e35ae692350eae3ebf"
BASE = "https://data.gdeltproject.org/gdeltv2/"
QUARTER, BUFFER = 900, 300
KNOWN_LAG = QUARTER + BUFFER
HOUR, WEEK = 3600, 7 * 86400
MIN_FREE = 3435973837  # ceiling of 3.2 GiB
DISK_CAP = 400_000_000
MAX_ZIP, MAX_UNZIP, MAX_LINE = 24_000_000, 240_000_000, 4_000_000
PAUSE = .55
SEED, SAMPLE_N = 77, 200
BLOCKED = frozenset(("binance", "binancezh", "upbit", "bithumb", "prnewswire", "prnews",
                     "businesswire", "nasdaq", "coingecko"))
ALIASES = {
    "BCH": "Bitcoin Cash", "HYPE": "Hyperliquid", "SOL": "Solana", "XLM": "Stellar Lumens",
    "ZEC": "Zcash", "LINK": "Chainlink", "LTC": "Litecoin", "ONDO": "Ondo Finance", "SUI": "Sui Network",
}
CONTEXT_NAMES = {"XLM": "Stellar", "ONDO": "Ondo", "SUI": "Sui"}
CONTEXT = re.compile(r"\b(?:crypto(?:currency|currencies)?|blockchain|token|bitcoin|ethereum|defi|altcoins?|"
                     r"stablecoins?|memecoins?|web3|mainnet|on-chain|solana|chainlink|hyperliquid|litecoin|zcash)\b", re.I)
TITLE = re.compile(rb"<PAGE_TITLE>([^<>]{1,8192})</PAGE_TITLE>", re.I)
NONWORDS = re.compile(r"[\W_]+")


def utc(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def batches(reg=REG):
    raw = reg.read_bytes()
    if hashlib.sha256(raw).hexdigest() != REG_SHA:
        raise ValueError("TM07 registration hash differs")
    weeks = json.loads(raw)["weeks"]
    scored = [(start, tuple(name.removesuffix("/USD") for name in w["five"]))
              for start, w in sorted(weeks.items()) if w["use"] != "diagnostic"]
    if len(scored) != 20 or [w for w, _ in scored[:2]] != ["2026-07-06", "2026-07-13"]:
        raise ValueError("unexpected TM07 sample")
    sample = scored[:2]
    if any(len(coins) != 5 or not set(coins) <= ALIASES.keys() for _, coins in sample):
        raise ValueError("coin aliases do not cover the two baskets")
    schedule = [(tick, start, coins) for start, coins in sample
                for tick in range(utc(start) - QUARTER, utc(start) + WEEK - QUARTER, QUARTER)]
    if any(not utc(week) <= tick + KNOWN_LAG < utc(week) + WEEK for tick, week, _ in schedule):
        raise ValueError("batch does not belong to the week of its known-at time")
    return sample, schedule


def stamp(tick):
    return datetime.fromtimestamp(tick, timezone.utc).strftime("%Y%m%d%H%M%S")


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def title_key(title):
    return NONWORDS.sub(" ", title.casefold()).strip()


def matched(title, coins):
    has_context = bool(CONTEXT.search(title))
    return [coin for coin in coins if (
        re.search(rf"(?<!\w){re.escape(ALIASES[coin])}(?!\w)", title, re.I)
        or re.search(rf"(?<!\w)\${coin}(?!\w)", title, re.I)
        or has_context and (re.search(rf"(?<!\w){coin}(?!\w)", title)
                            or coin in CONTEXT_NAMES and re.search(
                                rf"(?<!\w){CONTEXT_NAMES[coin]}(?!\w)", title, re.I)))]


def link(url):
    try:
        p = urlsplit(url)
        host = p.hostname
        if (p.scheme not in ("http", "https") or not host or p.netloc.lower() != host
                or not re.fullmatch(r"[a-z0-9.-]{3,253}", host) or "." not in host or len(url) > 2048):
            return None
        host = host.removeprefix("www.")
        if set(host.split(".")) & BLOCKED:
            return None
        safe_q = urlencode(sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True, max_num_fields=80)
                                  if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}))
        return host, urlunsplit((p.scheme, host, p.path, safe_q, ""))
    except ValueError:
        return None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


class Archive:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())
        self.last = 0.

    def get(self, tick):
        time.sleep(max(0., PAUSE - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        req = urllib.request.Request(BASE + stamp(tick) + ".gkg.csv.zip",
                                     headers={"User-Agent": "TM09-GDELT-research/1.0 (serial historical sample)"})
        with self.opener.open(req, timeout=40) as res:
            if res.status != 200 or res.geturl() != req.full_url or res.headers.get_content_type() not in (
                    "application/zip", "application/x-zip-compressed", "application/octet-stream"):
                raise ValueError("unexpected GDELT response; stop")
            raw = res.read(MAX_ZIP + 1)
        if len(raw) > MAX_ZIP or not raw.startswith(b"PK\x03\x04"):
            raise ValueError("unexpected GDELT archive size or signature; stop")
        return raw


def scan(raw, tick, coins):
    prefix = stamp(tick)
    rows = []
    scanned = 0
    with ZipFile(BytesIO(raw)) as archive:
        info, = archive.infolist()
        if info.filename != prefix + ".gkg.csv" or info.file_size > MAX_UNZIP:
            raise ValueError("unexpected GKG ZIP member")
        with archive.open(info) as source:
            while packet := source.readline(MAX_LINE + 1):
                if len(packet) > MAX_LINE:
                    raise ValueError("overlong GKG record")
                scanned += 1
                fields = packet.split(b"\t", 26)
                if len(fields) != 27 or not fields[0].startswith(prefix.encode() + b"-"):
                    raise ValueError("GKG row does not match its own archive batch")
                if fields[2] != b"1" or b"<PAGE_TITLE>" not in fields[26]:
                    continue
                m = TITLE.search(fields[26])
                if m is None:
                    continue
                title = " ".join(unescape(m[1].decode("utf-8", errors="replace")).split())
                if not 2 <= len(title) <= 512:
                    continue
                coins_found = matched(title, coins)
                url = link(fields[4].decode("utf-8", errors="replace")) if coins_found else None
                if url is None:
                    continue
                for coin in coins_found:
                    rows.append({"first_seen_utc": tick, "source_domain": url[0], "title": title,
                                 "url": url[1], "matched_coin": coin})
    return scanned, rows


def signature(row):
    p = urlsplit(row["url"])
    return row["matched_coin"], (p.netloc, p.path.rstrip("/"), p.query), title_key(row["title"])


def unique_rows(rows, seen_url, seen_title):
    kept = []
    for row in rows:
        coin, url, title = signature(row)
        u, t = (coin, url), (coin, title)
        if u in seen_url or t in seen_title:
            continue
        kept.append(row)
        seen_url.add(u)
        seen_title.add(t)
    return kept


def check_space(root, reserve=0):
    fs = os.statvfs(WORKSPACE)
    if fs.f_bavail * fs.f_frsize - reserve < MIN_FREE:
        raise ValueError("STOP: workspace free space below 3.2 GiB after reserving write")
    total = 0
    if root.exists():
        if stat.S_IMODE(root.lstat().st_mode) != 0o700 or not root.is_dir() or root.is_symlink():
            raise ValueError("custody directory is not private")
        for child in root.iterdir():
            s = child.lstat()
            if not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o600:
                raise ValueError("custody contains a non-private or non-regular file")
            total += s.st_blocks * 512
    if total + reserve > DISK_CAP:
        raise ValueError("STOP: writing would exceed the 400 MB custody cap")


def create(root, name):
    return os.fdopen(os.open(root / name, os.O_WRONLY | os.O_NOFOLLOW | os.O_CREAT | os.O_EXCL, 0o600), "wb")


def collect(root=ROOT):
    _, schedule = batches()
    check_space(root, 16384)
    root.mkdir(mode=0o700, exist_ok=True)
    with create(root, "rows.jsonl") as data, create(root, "coverage.jsonl") as coverage:
        archive = Archive()
        urls, titles = set(), set()
        for tick, week, coins in schedule:
            check_space(root)
            raw = archive.get(tick)
            scanned, matches = scan(raw, tick, coins)
            kept = unique_rows(matches, urls, titles)
            records = b"".join(map(encoded, kept))
            journal = encoded({"batch_utc": tick, "week": week, "compressed_bytes": len(raw), "source_rows": scanned,
                               "matching_rows": len(matches), "kept_rows": len(kept), "kept_bytes": len(records)})
            check_space(root, len(records) + len(journal) + 8192)
            data.write(records)
            data.flush()
            coverage.write(journal)
            coverage.flush()


def read_file(root, name):
    with os.fdopen(os.open(root / name, os.O_RDONLY | os.O_NOFOLLOW), "rb") as f:
        mode = os.fstat(f.fileno()).st_mode
        if stat.S_IMODE(mode) != 0o600 or not stat.S_ISREG(mode):
            raise ValueError("headline file is not private and regular")
        yield from (json.loads(line) for line in f)


def known_at(row):
    if type(row["first_seen_utc"]) is not int or row["first_seen_utc"] % QUARTER:
        raise ValueError("unexpected first-seen time")
    return row["first_seen_utc"] + KNOWN_LAG


def visible(rows, wake_utc, *, after_utc=None):
    """The only point-in-time reader; eligibility is inclusive at the known-at time."""
    if type(wake_utc) is not int or (after_utc is not None and type(after_utc) is not int):
        raise TypeError("the simulated clock must be integer UTC seconds")
    return [row for row in rows if (after_utc is None or after_utc < known_at(row)) and known_at(row) <= wake_utc]


def week_visible(rows, wake_utc, *, after_utc=None):
    """Preview only: keep the registered week, basket and point-in-time boundary."""
    if type(wake_utc) is not int or wake_utc % HOUR:
        raise ValueError("expected a registered hourly UTC wake")
    if after_utc is not None and type(after_utc) is not int:
        raise TypeError("lower bound must be integer UTC seconds")
    for week, coins in batches()[0]:
        start = utc(week)
        if start <= wake_utc < start + WEEK:
            lower = start - 1 if after_utc is None else max(start - 1, after_utc)
            permitted = (r for r in rows if r["matched_coin"] in coins)
            return visible(permitted, wake_utc, after_utc=lower)
    raise ValueError("wake outside the two sampled weeks")


def headlines(wake_utc, *, after_utc=None):
    return week_visible(read_file(ROOT, "rows.jsonl"), wake_utc, after_utc=after_utc)


def report(root=ROOT):
    sample, schedule = batches()
    coverage = list(read_file(root, "coverage.jsonl"))
    if [(x["batch_utc"], x["week"]) for x in coverage] != [x[:2] for x in schedule[:len(coverage)]]:
        raise ValueError("coverage must be a contiguous prefix of the fixed schedule")
    raw_size = sum(x["kept_bytes"] for x in coverage)
    if raw_size != (root / "rows.jsonl").stat().st_size:
        raise ValueError("incomplete journal/display snapshot; no counts issued")
    clocks = {t: (w, coins) for t, w, coins in schedule[:len(coverage)]}
    counts = {week: dict.fromkeys(coins, 0) for week, coins in sample}
    wake_counts = {week: dict.fromkeys(coins, 0) for week, coins in sample}
    domains = Counter()
    rows = list(read_file(root, "rows.jsonl"))
    batch_rows, batch_bytes = Counter(), Counter()
    for r in rows:
        t = r["first_seen_utc"]
        if t not in clocks:
            raise ValueError("retained row belongs to an unjournaled batch")
        week, coins = clocks[t]
        if r["matched_coin"] not in coins:
            raise ValueError("retained row is outside its registered basket")
        batch_rows[t] += 1
        batch_bytes[t] += len(encoded(r))
        counts[week][r["matched_coin"]] += 1
        if known_at(r) <= utc(week) + WEEK - HOUR:
            wake_counts[week][r["matched_coin"]] += 1
        domains[r["source_domain"]] += 1
    for c in coverage:
        t = c["batch_utc"]
        if (not 0 <= c["kept_rows"] <= c["matching_rows"]
                or c["kept_rows"] != batch_rows[t] or c["kept_bytes"] != batch_bytes[t]):
            raise ValueError("retained rows do not reconcile with per-batch coverage")
    candidates = sum(c["matching_rows"] for c in coverage)
    return rows, {"completed_batches": len(coverage), "planned_batches": len(schedule),
                  "batches_by_week": dict(Counter(x["week"] for x in coverage)),
                  "compressed_bytes": sum(c["compressed_bytes"] for c in coverage),
                  "scanned_source_rows": sum(c["source_rows"] for c in coverage),
                  "raw_coin_matches": candidates, "duplicate_coin_matches": candidates - len(rows),
                  "kept_coin_headlines": len(rows), "counts_by_week": counts,
                  "visible_by_final_wake": wake_counts,
                  "zero_coin_weeks": sum(n == 0 for w in counts.values() for n in w.values())
                  if len(coverage) == len(schedule) else None,
                  "top_domains": sorted(domains.items(), key=lambda p: (-p[1], p[0]))[:15]}


def seeded_titles(rows):
    titles = {}
    for row in rows:
        titles.setdefault(title_key(row["title"]), row["title"])
    ordered = sorted(titles)
    return [titles[k] for k in random.Random(SEED).sample(ordered, min(SAMPLE_N, len(ordered)))]


def review_key(titles):
    return hashlib.sha256(encoded(titles)).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("plan", "collect-sample", "counts", "review-titles"))
    action = p.parse_args().action
    if action == "plan":
        sample, schedule = batches()
        print(json.dumps({"sample": sample, "requests": len(schedule), "known_lag": KNOWN_LAG}, sort_keys=True))
    elif action == "collect-sample":
        collect()
    else:
        rows, counts = report()
        if action == "counts":
            print(json.dumps(counts, sort_keys=True))
        else:
            titles = seeded_titles(rows)
            print("Review snapshot SHA-256:", review_key(titles))
            for i, title in enumerate(titles, 1):
                print(f"{i:03d} {title}")


if __name__ == "__main__":
    main()
