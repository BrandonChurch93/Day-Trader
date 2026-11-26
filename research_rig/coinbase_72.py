"""Plan 72 fixed public Coinbase GETs and authenticated private response snapshots."""
import json
import math
import os
import re
import stat
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from carry_70 import create_at, digest, pinned
from coverage_70 import exact_parent
from sweep_70 import ALLOWED

DATA = Path("/home/user/workspace/rig/data/plan72")
URL = "https://api.exchange.coinbase.com"
HOUR = 3600
MINUTE = 60
FRESH = (1483228800, 1577836800)
DIAG = (FRESH[1], 1704067200)
MAX_BUCKETS = 290  # below Coinbase's 300 maximum; end is inclusive in the request
ENVELOPE = re.compile(rb"\[\s*(?:\[(?:[^\[\]]*)\](?:\s*,\s*\[(?:[^\[\]]*)\])*)?\s*\]\s*")
ROW = re.compile(rb"\[\s*(\d+)\s*,([^\[\]]*)\]")


def validate(job, stage):
    if not isinstance(job, (list, tuple)) or len(job) != 4:
        raise ValueError("invalid Coinbase request fields")
    coin, gran, lo, hi = job
    if (coin not in ALLOWED or type(gran) is not int or gran not in (MINUTE, HOUR)
            or type(lo) is not int or type(hi) is not int or lo % gran or hi % gran
            or not 0 < hi - lo <= MAX_BUCKETS * gran):
        raise ValueError("invalid Coinbase product, granularity or bucket range")
    fresh = FRESH[0] <= lo < hi <= FRESH[1]
    diagnostic = DIAG[0] <= lo < hi <= DIAG[1]
    if (stage == "hourly" and not (fresh and gran == HOUR)
            or stage == "windows" and not ((fresh and gran == MINUTE) or diagnostic)
            or stage not in ("hourly", "windows")):
        raise ValueError("request outside its fixed date fence")
    return coin, gran, lo, hi


def path_for(job, stage):
    coin, gran, lo, hi = validate(job, stage)
    return f"{stage}_{coin}_{gran}_{lo}_{hi}.json"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Client:
    """No secrets, redirects, retries, alternate host, parallelism or resume."""
    def __init__(self, delay_seconds):
        self.opener = urllib.request.build_opener(NoRedirect())
        self.next_at = 0.
        self.delay_seconds = delay_seconds

    def get(self, job, stage):
        coin, gran, lo, hi = validate(job, stage)
        wait = self.next_at - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.next_at = time.monotonic() + self.delay_seconds
        params = urllib.parse.urlencode({"granularity": gran, "start": iso(lo), "end": iso(hi - 1)})
        req = urllib.request.Request(f"{URL}/products/{coin}-USD/candles?{params}",
                                     headers={"User-Agent": "day-trader-research-plan72/1.0",
                                              "Accept": "application/json"})
        with self.opener.open(req, timeout=25) as wire:
            if wire.status != 200 or wire.headers.get_content_type() != "application/json":
                raise ValueError("non-JSON or unsuccessful Coinbase response; stop collection")
            raw = wire.read(1_000_001)
        if len(raw) > 1_000_000 or not ENVELOPE.fullmatch(raw):
            raise ValueError("unexpected Coinbase response; stop collection")
        return raw


def parse(raw, job, stage):
    """Skip any server-supplied earlier bucket before decoding price fields."""
    _, gran, lo, hi = validate(job, stage)
    if not ENVELOPE.fullmatch(raw):
        raise ValueError("invalid Coinbase JSON candle envelope")
    out = {}
    matches = list(ROW.finditer(raw))
    if raw.strip() != b"[]" and not matches and re.search(rb"\[\s*\[", raw):
        raise ValueError("malformed Coinbase timestamp")
    if len(matches) != raw.count(b"[") - 1:
        raise ValueError("malformed Coinbase timestamp")
    for m in matches:
        tick = int(m[1])
        if not lo <= tick < hi:
            continue
        if tick in out or tick % gran:
            raise ValueError("duplicate or misaligned Coinbase candle")
        fields = json.loads(b"[" + m[2] + b"]")
        if (len(fields) != 5 or any(type(x) not in (int, float) or not math.isfinite(x) for x in fields)):
            raise ValueError("malformed retained Coinbase candle")
        low, high, opening, close, volume = fields
        if not (0 < low <= min(opening, close) <= max(opening, close) <= high and volume >= 0):
            raise ValueError("invalid retained Coinbase candle")
        out[tick] = (opening, high, low, close, volume)
    return out


def lines(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def private_dir(root):
    with exact_parent(root, "entry") as (fd, _):
        if stat.S_IMODE(os.fstat(fd).st_mode) != 0o700:
            raise ValueError("canonical Plan 72 directory must have mode 0700")


def ensure_dir(root):
    try:
        with exact_parent(root.parent, root.name) as (fd, name):
            os.mkdir(name, mode=0o700, dir_fd=fd)
            os.fsync(fd)
    except FileExistsError:
        pass
    private_dir(root)


def collect(root, stage, jobs, binding, delay):
    ensure_dir(root)
    for job in jobs:
        validate(job, stage)
    if len(jobs) != len({tuple(j) for j in jobs}):
        raise ValueError("duplicate Coinbase request")
    with exact_parent(root, stage + ".started") as (fd, name):
        create_at(fd, name, lines({"stage": stage, "binding": binding, "expected_requests": len(jobs)}))
        client = Client(delay)
        records = []
        for job in jobs:
            raw = client.get(job, stage)
            parse(raw, job, stage)
            rel = path_for(job, stage)
            create_at(fd, rel, raw)
            records.append({"job": job, "sha256": digest(raw)})
        data = lines({"stage": stage, "binding": binding, "files": records})
        create_at(fd, stage + "_manifest.json", data)
    return {"stage": stage, "requests": len(records), "manifest_sha256": digest(data)}


def load(root, stage, manifest_pin, jobs, binding):
    if len(jobs) != len({tuple(j) for j in jobs}):
        raise ValueError("duplicate planned Coinbase requests")
    name = stage + "_manifest.json"
    manifest = json.loads(pinned(root, name, manifest_pin, mode=0o600))
    if (set(manifest) != {"stage", "binding", "files"} or manifest["stage"] != stage
            or manifest["binding"] != binding or [tuple(x["job"]) for x in manifest["files"]] != jobs):
        raise ValueError("Coinbase manifest request coverage or binding differs")
    combined = {}
    for record in manifest["files"]:
        job = tuple(record["job"])
        rel = path_for(job, stage)
        raw = pinned(root, rel, record["sha256"], mode=0o600)
        batch = parse(raw, job, stage)
        data = combined.setdefault((job[0], job[1]), {})
        if data.keys() & batch.keys():
            raise ValueError("repeated candle across Coinbase snapshots")
        data.update(batch)
    return combined
