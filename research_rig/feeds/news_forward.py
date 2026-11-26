"""Single-process, append-only, capture-clock RSS/Atom collector for queue 120."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path("/home/user/workspace/rig/data/news_forward")
CAP = 300_000_000
INTERVAL, DELAY, TICK, PAUSE = 600, 60, 15, 1
MAX_PAYLOAD = 2_000_000
MIN_FREE = 3_435_973_837
CONTROL_RESERVE = 128 * 1024
FEEDS = {
    "bitcoin_optech": "https://bitcoinops.org/feed.xml",
    "fed_press": "https://www.federalreserve.gov/feeds/press_all.xml",
    "sec_press": "https://www.sec.gov/rss/news/press.xml",
}
BLOCKED = {"binance", "binancezh", "upbit", "bithumb", "prnewswire", "prnews", "businesswire", "nasdaq", "coingecko"}
OPERATOR = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+", re.ASCII)
DAYFILE = re.compile(r"\d{4}-\d{2}-\d{2}\.jsonl")
HTTP_BLOCK = {401, 403, 407, 429, 451}
ATOM = "{http://www.w3.org/2005/Atom}"


class Full(Exception):
    pass


class Block(Exception):
    pass


def clock():
    # Round up, never advertise capture before the final response byte arrived.
    return math.ceil(time.time())


def iso_day(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).date().isoformat()


def dump(data):
    return (json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


def href(value, feed=False):
    try:
        p = urlsplit(value)
        host = p.hostname
        return (len(value) <= 2048 and not any(c.isspace() or ord(c) < 32 for c in value)
                and p.scheme in (("https",) if feed else ("http", "https"))
                and host and p.netloc.lower() == host
                and not set(host.rstrip(".").split(".")) & BLOCKED)
    except ValueError:
        return False


def leaf(node, name):
    child = node.find(name)
    return " ".join("".join(child.itertext()).split()) if child is not None else ""


def items(body):
    xml = body.decode("utf-8-sig")
    if re.search(r"<!doctype\s+html\b|<html(?:\s|>)", xml[:2048], re.I):
        raise Block("HTML page instead of feed")
    if "\0" in xml or re.search(r"<!\s*(DOCTYPE|ENTITY)\b", xml, re.I):
        raise ValueError("unsafe XML")
    root = ET.fromstring(xml)
    if root.tag == "rss" and root.find("channel") is not None:
        children = root.findall("channel/item")
        is_atom = False
    elif root.tag == ATOM + "feed":
        children = root.findall(ATOM + "entry")
        is_atom = True
    elif str(root.tag).lower().endswith("html"):
        raise Block("HTML page instead of feed")
    else:
        raise ValueError("not RSS 2.0 or Atom")
    entries = {}
    for node in children:
        if is_atom:
            title = leaf(node, ATOM + "title")
            link = next((n.get("href", "") for n in node.findall(ATOM + "link")
                         if n.get("rel", "alternate") == "alternate"), "")
            ident = leaf(node, ATOM + "id")
            dt = leaf(node, ATOM + "published") or leaf(node, ATOM + "updated")
        else:
            title, link = leaf(node, "title"), leaf(node, "link")
            ident, dt = leaf(node, "guid"), leaf(node, "pubDate")
        if not title or len(title) > 1024 or not href(link):
            continue
        key = sha256((("id:" + ident) if ident else ("link:" + link)).encode()).hexdigest()
        entries.setdefault(key, (title, link, dt if 0 < len(dt) <= 160 else None))
    return entries


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def retry_until(headers, now):
    val = headers.get("Retry-After", "")
    if re.fullmatch(r"\d{1,9}", val):
        return now + int(val)
    try:
        parsed = parsedate_to_datetime(val)
        return math.ceil(parsed.timestamp()) if parsed.tzinfo else 0
    except (TypeError, ValueError, OverflowError):
        return 0


def transport(user_agent):
    opener = urllib.request.build_opener(NoRedirect())

    def get(url, validators):
        if not href(url, feed=True):
            raise Block("unapproved URL form")
        headers = {"User-Agent": user_agent, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"}
        if validators.get("etag"):
            headers["If-None-Match"] = validators["etag"]
        if validators.get("modified"):
            headers["If-Modified-Since"] = validators["modified"]
        req = urllib.request.Request(url, headers=headers)
        try:
            with opener.open(req, timeout=20) as response:
                if response.geturl() != url:
                    raise Block("redirect")
                if response.headers.get_content_type() in {"text/html", "application/xhtml+xml"}:
                    raise Block("HTML response")
                body = response.read(MAX_PAYLOAD + 1)
                if len(body) > MAX_PAYLOAD:
                    raise ValueError("oversize feed")
                return response.status, response.headers, body
        except urllib.error.HTTPError as e:
            # Do not read or retain error pages, and never follow a redirect.
            try:
                return e.code, e.headers or {}, b""
            finally:
                e.close()
    return get


def open_private(path, flags=os.O_RDONLY):
    fd = os.open(path, flags | os.O_NOFOLLOW, 0o600)
    s = os.fstat(fd)
    if not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o600 or s.st_nlink != 1:
        os.close(fd)
        raise ValueError("non-private or non-regular custody file")
    return fd


class Store:
    def __init__(self, root=ROOT, cap=CAP, min_free=MIN_FREE):
        self.root, self.cap, self.min_free = root, cap, min_free

    def checked(self):
        s = self.root.lstat()
        if not stat.S_ISDIR(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o700:
            raise ValueError("custody directory must be real and mode 0700")

    def mkdir(self):
        self.root.mkdir(mode=0o700, exist_ok=True)
        self.checked()

    def size(self):
        total = self.root.stat().st_blocks * 512
        for path in self.root.iterdir():
            s = path.lstat()
            if not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o600 or s.st_nlink != 1:
                raise ValueError("unexpected custody file")
            total += max(s.st_size, s.st_blocks * 512)
        return total

    def ensure(self, n=0, control=False, final=False):
        space = os.statvfs(self.root)
        # Reserve allocation blocks and space for a final atomic heartbeat on cap hits.
        reserve = n + 8192 + (0 if control else CONTROL_RESERVE)
        if self.size() + reserve > self.cap:
            raise Full("private store cap")
        if not final and space.f_bavail * space.f_frsize - reserve < self.min_free:
            raise Full("workspace reserve")

    def sync_dir(self):
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def load(self, name, default=None):
        try:
            fd = open_private(self.root / name)
        except FileNotFoundError:
            return default
        with os.fdopen(fd, "rb") as f:
            return json.load(f)

    def atom(self, name, value, *, final=False):
        b = dump(value)
        self.ensure(len(b), control=True, final=final)
        tmp = self.root / (name + ".tmp")
        fd = open_private(tmp, os.O_WRONLY | os.O_CREAT)
        with os.fdopen(fd, "wb") as fh:
            fh.truncate(0)
            fh.write(b)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.root / name)
        self.sync_dir()

    def append(self, epoch, rows):
        if not rows:
            return
        records = b"".join(map(dump, rows))
        self.ensure(len(records))
        fd = open_private(self.root / (iso_day(epoch) + ".jsonl"), os.O_WRONLY | os.O_APPEND | os.O_CREAT)
        with os.fdopen(fd, "ab") as fh:
            fh.write(records)
            fh.flush()
            os.fsync(fh.fileno())
        self.sync_dir()

    def rows(self):
        self.checked()
        for path in sorted(self.root.iterdir()):
            if not DAYFILE.fullmatch(path.name):
                continue
            with os.fdopen(open_private(path), "rb") as fh:
                for line in fh:
                    if not line.endswith(b"\n"):
                        raise ValueError("incomplete append; stop for operator inspection")
                    yield json.loads(line)


def available(rows, wake_utc):
    """An item cannot enter replay before private capture plus the fixed delay."""
    if type(wake_utc) is not int:
        raise TypeError("wake must be integer UTC seconds")
    return [r for r in rows if not r["backlog"] and r["capture_utc"] + DELAY <= wake_utc]


def headlines(wake_utc):
    return available(Store().rows(), wake_utc)


class Logger:
    def __init__(self, store, feeds, get, now=clock):
        self.store, self.feeds, self.get, self.now = store, feeds, get, now
        old = store.load("state.json", {})
        self.state = {k: old.get(k, {"next_utc": 0}) for k in feeds}
        self.baseline = set(feeds)
        for k in feeds:
            if k in old:
                # Keep the interval even if the previous process died mid-request.
                self.state[k]["next_utc"] = max(self.state[k]["next_utc"], now() + INTERVAL)
                if self.state[k].pop("pending", False):
                    # We cannot prove the unresolved response was not a block.
                    self.state[k]["dropped"] = True
                    self.state[k]["interrupted"] = True
                    self.state[k]["errors"] = self.state[k].get("errors", 0) + 1
        self.last, self.backlog, self.counts = {}, set(), Counter()
        for r in store.rows():
            self.admit(r)

    def admit(self, r):
        key = r["feed_id"], r["item_hash"]
        self.last[key] = r["title"]
        if r["backlog"]:
            self.backlog.add(key)
        self.counts["rows"] += 1
        self.counts["backlog_rows"] += r["backlog"]

    def save(self):
        self.store.atom("state.json", self.state)

    def heartbeat(self, running=1, cap_stop=0):
        self.store.atom("heartbeat.json", {
            "heartbeat_utc": self.now(), "running": running, "cap_stop": cap_stop,
            "rows": self.counts["rows"], "backlog_rows": self.counts["backlog_rows"],
            "feeds": len(self.feeds), "dropped_feeds": sum(bool(s.get("dropped")) for s in self.state.values()),
            "attempts": sum(s.get("attempts", 0) for s in self.state.values()),
            "errors": sum(s.get("errors", 0) for s in self.state.values()),
            "successes": sum(s.get("successes", 0) for s in self.state.values()),
            "not_modified": sum(s.get("not_modified", 0) for s in self.state.values()),
            "interrupted_feeds": sum(bool(s.get("interrupted")) for s in self.state.values()),
        }, final=not running)

    def poll(self, feed_id):
        s = self.state[feed_id]
        start = self.now()
        if s.get("dropped") or s["next_utc"] > start:
            return False
        self.store.ensure()
        # Persist the attempt before contacting a source, including when restarted.
        s["next_utc"] = start + INTERVAL
        s["attempts"] = s.get("attempts", 0) + 1
        s["pending"] = True
        self.save()
        hints = {}
        try:
            try:
                status, hints, body = self.get(self.feeds[feed_id], s)
            except OSError as e:
                raise ValueError("feed transport failed") from e
            captured = max(start, self.now())
            s["next_utc"] = max(s["next_utc"], captured + INTERVAL)
            if (status in HTTP_BLOCK or (300 <= status < 400 and status != 304)
                    or hints.get("cf-mitigated", "").lower() == "challenge"):
                raise Block("access refused or redirected")
            if status == 304 and (s.get("etag") or s.get("modified")):
                s["not_modified"] = s.get("not_modified", 0) + 1
                s["failures"] = 0
                # A valid 304 says the last admitted snapshot is still current.
                self.baseline.discard(feed_id)
            elif status == 200:
                entries = items(body)
                rows = []
                for key, (title, link, published) in entries.items():
                    compound = feed_id, key
                    previous = self.last.get(compound)
                    if previous == title:
                        continue
                    backlog = compound in self.backlog or feed_id in self.baseline
                    rows.append({"capture_utc": captured, "feed_id": feed_id, "published": published,
                                 "title": title, "link": link, "item_hash": key, "backlog": backlog})
                self.store.append(captured, rows)
                for r in rows:
                    self.admit(r)
                self.baseline.discard(feed_id)
                for target, header in (("etag", "ETag"), ("modified", "Last-Modified")):
                    v = hints.get(header, "")
                    s[target] = v if len(v) <= 512 and all(32 <= ord(ch) < 127 for ch in v) else ""
                s["failures"] = 0
                s["successes"] = s.get("successes", 0) + 1
            else:
                raise ValueError("unexpected HTTP status")
        except Block:
            s["dropped"] = True
            s["errors"] = s.get("errors", 0) + 1
        except Full:
            # A successful 200 reached the append preflight; no bytes were appended.
            s.pop("pending", None)
            self.save()
            raise
        except (ValueError, ET.ParseError):
            s["errors"] = s.get("errors", 0) + 1
            s["failures"] = min(s.get("failures", 0) + 1, 8)
            end = self.now()
            delay = min(INTERVAL * 2 ** s["failures"], 86400)
            s["next_utc"] = max(s["next_utc"], end + delay, retry_until(hints, end))
        s.pop("pending", None)
        self.save()
        return True


def run(store, user_agent):
    store.checked()
    fd = open_private(store.root / "writer.lock", os.O_CREAT | os.O_WRONLY)
    with os.fdopen(fd, "wb") as fd:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 2
        stopped = False

        def stop(*_args):
            nonlocal stopped
            stopped = True

        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        logger = Logger(store, FEEDS, transport(user_agent))
        try:
            logger.save()  # persists holds recovered from a prior interrupted request
            logger.heartbeat()
            while not stopped:
                for feed in FEEDS:
                    if stopped:
                        break
                    if logger.poll(feed):
                        logger.heartbeat()
                        time.sleep(PAUSE)
                if all(s.get("dropped") for s in logger.state.values()):
                    break
                if not stopped:
                    time.sleep(TICK)
                    logger.heartbeat()
        except Full:
            logger.heartbeat(running=0, cap_stop=1)
            return 0
        logger.heartbeat(running=0)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    start = sub.add_parser("run")
    start.add_argument("--contact", required=True, help="Real operator contact for the User-Agent")
    sub.add_parser("status")
    args = parser.parse_args()
    store = Store()
    if args.action == "status":
        if not store.root.exists():
            print('{"heartbeat_present":0}')
            return 1
        store.checked()
        values = store.load("heartbeat.json")
        if values is None:
            print('{"heartbeat_present":0}')
            return 1
        m = {k: values[k] for k in ("heartbeat_utc", "running", "cap_stop", "rows", "backlog_rows",
                                    "feeds", "dropped_feeds", "attempts", "errors", "successes",
                                    "not_modified", "interrupted_feeds")}
        if any(type(v) is not int or v < 0 for v in m.values()):
            raise SystemExit("invalid heartbeat")
        print(json.dumps({"heartbeat_present": 1, "age_seconds": max(0, clock() - m["heartbeat_utc"]), **m},
                         sort_keys=True))
        return 0
    if not OPERATOR.fullmatch(args.contact) or len(args.contact) > 180 or not args.contact.isascii():
        parser.error("use a real operator email contact")
    store.mkdir()
    return run(store, f"NewsForward120/1.0 (private RSS research; contact {args.contact})")


if __name__ == "__main__":
    raise SystemExit(main())
