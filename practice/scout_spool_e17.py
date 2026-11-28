"""Private E17 scout request/reply files. No model client or desk records."""
import fcntl
import json
import math
import os
import re
import stat
import time
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

CUSTODY = Path("/home/user/workspace/rig/data")
DEFAULT = CUSTODY / "desk_e17_scout"
UTC = timezone.utc
POLL_S = 0.1
ID = re.compile(r"[a-f0-9]{32}")
HASH = re.compile(r"[a-f0-9]{64}")
BUILD = re.compile(r"[a-f0-9]{40}")
MODEL = re.compile(r"[A-Za-z_0-9.-]{1,100}")
USAGE_KEYS = ("input_tokens", "output_tokens", "reasoning_tokens")
SERVICE_CODES = frozenset(("CANCELLED", "UNKNOWN", "INVALID_ARGUMENT", "DEADLINE_EXCEEDED", "NOT_FOUND",
                           "ALREADY_EXISTS", "PERMISSION_DENIED", "RESOURCE_EXHAUSTED", "FAILED_PRECONDITION",
                           "ABORTED", "OUT_OF_RANGE", "UNIMPLEMENTED", "INTERNAL", "UNAVAILABLE", "DATA_LOSS",
                           "UNAUTHENTICATED", "OK"))
KINDS = ("request", "taken", "claim", "reply", "withdrawn")
CONTROL = {"heartbeat.json", ".reply.lock"}
FIELDS = {"request_id", "model", "system_text", "user_text", "reply_schema", "max_tokens", "timeout_s",
          "deadline", "claim_by", "build"}


class Refuse(Exception):
    """No path contents or other private data appear in the exception."""


def now_utc():
    return datetime.now(UTC)


def utc(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() != timedelta(0):
        raise ValueError("UTC time required")
    return result


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(fields):
    return sha256(encode(fields)).hexdigest()


def request(fields, cutoff, timeout, claim_by, build):
    body = dict(fields, request_id=uuid4().hex, deadline=cutoff.isoformat(), timeout_s=timeout,
                claim_by=claim_by.isoformat(), build=build)
    return dict(body, sha256=digest(body))


def valid_request(body, rid, now):
    try:
        return (type(body) is dict and set(body) == FIELDS | {"sha256"} and body["request_id"] == rid
                and ID.fullmatch(rid) is not None and HASH.fullmatch(body["sha256"]) is not None
                and digest({key: body[key] for key in FIELDS}) == body["sha256"]
                and MODEL.fullmatch(body["model"]) is not None and type(body["system_text"]) is str
                and type(body["user_text"]) is str and type(body["reply_schema"]) is dict
                and type(body["max_tokens"]) is int and body["max_tokens"] > 0
                and type(body["timeout_s"]) in (int, float) and math.isfinite(body["timeout_s"])
                and BUILD.fullmatch(body["build"]) is not None and body["timeout_s"] > 0
                and now < utc(body["claim_by"]) <= utc(body["deadline"]))
    except (ValueError, TypeError, KeyError, OverflowError):
        return False


def claim_record(req, build, now):
    return {"request_id": req["request_id"], "request_sha256": req["sha256"],
            "build": build, "claimed_utc": now.isoformat()}


def reply_envelope(req, build, result):
    return {"request_id": req["request_id"], "request_sha256": req["sha256"], "build": build, "result": result}


def reply_result(reply, req):
    if (type(reply) is not dict or reply.get("request_id") != req["request_id"]
            or reply.get("request_sha256") != req["sha256"] or reply.get("build") != req["build"]
            or type(reply.get("result")) is not dict):
        return None
    result = reply["result"]
    secs = reply.get("secs")
    if secs is not None:
        if type(secs) not in (float, int) or not math.isfinite(secs) or secs < 0:
            return None
    duration = {} if secs is None else {"secs": secs}
    status = result.get("status")
    if status == "call_timeout" and set(result) == {"status"}:
        return result | duration
    if status == "call_error":
        error, code = result.get("error"), result.get("service_status")
        if (set(result) == {"status", "error", "service_status"} and type(error) is str
                and MODEL.fullmatch(error) and type(code) is str and code in SERVICE_CODES):
            return result | duration
    if (set(result) == {"finish", "end_turn", "text", "usage", "model_reported"}
            and all(type(result[k]) is str for k in ("finish", "text", "model_reported"))
            and type(result["end_turn"]) is bool and type(result["usage"]) is dict
            and all(k in USAGE_KEYS and type(v) is int for k, v in result["usage"].items())):
        return result | duration
    return None


def filename(kind, rid):
    if kind not in KINDS or not isinstance(rid, str) or not ID.fullmatch(rid):
        raise Refuse("invalid scout file name")
    return f"{kind}-{rid}.json"


class Folder:
    """Only open descriptors to the checked directory and regular private files."""
    def __init__(self, fd):
        self.fd = fd

    @contextmanager
    def file(self, name, flags):
        fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=self.fd)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o600):
                raise Refuse("scout files must be private regular files")
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def fence(self, *, blocking=True):
        # Serialize claim metadata, reply publication and disposal. The rename
        # from the one request source is the durable claim or withdrawal.
        with self.file(".reply.lock", os.O_CREAT | os.O_RDWR) as fd:
            fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            yield

    def read(self, name):
        with self.file(name, os.O_RDONLY) as fd, os.fdopen(os.dup(fd), "rb") as inp:
            return json.load(inp)

    def write(self, name, data):
        tmp = "." + uuid4().hex
        try:
            with self.file(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY) as fd, os.fdopen(os.dup(fd), "wb") as out:
                out.write(encode(data) + b"\n")
                out.flush()
                os.fsync(out.fileno())
            self.rename(tmp, name)
        finally:
            self.drop(tmp)

    def rename(self, src, dst):
        os.rename(src, dst, src_dir_fd=self.fd, dst_dir_fd=self.fd)
        os.fsync(self.fd)

    def drop(self, name):
        with suppress(FileNotFoundError):
            os.unlink(name, dir_fd=self.fd)

    def names(self):
        return os.listdir(self.fd)

    def transfer(self, rid, dest):
        try:
            self.rename(filename("request", rid), filename(dest, rid))
            return True
        except FileNotFoundError:
            return False

    def claim(self, req, build, clock, until):
        rid = req["request_id"]
        with self.fence():
            stamp = clock()
            if (stamp >= until or req["build"] != build or not valid_request(req, rid, stamp)
                    or peek(self, filename("request", rid))[0] != req):
                return None
            meta = claim_record(req, build, stamp)
            name = filename("claim", rid)
            self.write(name, meta)
            if clock() >= min(until, utc(req["claim_by"])) or not self.transfer(rid, "taken"):
                self.drop(name)
                return None
            return meta

    def sweep(self, keep):
        expected = CONTROL | {filename(kind, rid) for rid in keep for kind in KINDS}
        with self.fence():
            stale = set(self.names()) - expected
            for name in stale:
                self.drop(name)
            os.fsync(self.fd)
            return len(stale)

    def cleanup(self, ids):
        with self.fence():
            for rid in ids:
                for kind in KINDS:
                    self.drop(filename(kind, rid))
            os.fsync(self.fd)


@contextmanager
def private(path=None, *, create=False):
    path = Path(DEFAULT if path is None else path)
    if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(CUSTODY) or path == CUSTODY:
        raise Refuse("scout directory is outside custody")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open("/", flags)
    try:
        current = Path("/")
        for part in path.parts[1:]:
            current /= part
            if create and current == path:
                with suppress(FileExistsError):
                    os.mkdir(part, mode=0o700, dir_fd=fd)
            next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
            if current.is_relative_to(CUSTODY) and os.fstat(fd).st_uid != os.geteuid():
                raise Refuse("scout directory owner differs")
            try:
                os.stat(".git", dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise Refuse("scout directory is inside a git work tree")
        if stat.S_IMODE(os.fstat(fd).st_mode) != 0o700:
            raise Refuse("scout directory must be private")
        yield Folder(fd)
    finally:
        os.close(fd)


def cleanup(ids, path=None):
    if ids:
        with private(path) as folder:
            folder.cleanup(ids)


def sweep(keep=(), path=None):
    with private(path, create=True) as folder:
        return folder.sweep(keep)


def peek(folder, name):
    """Return the contents and whether an unreadable/malformed file was present."""
    try:
        return folder.read(name), True
    except FileNotFoundError:
        return None, False
    except (OSError, Refuse, ValueError, TypeError):
        return None, True


def inspect_claim(folder, rid, request_sha256, claim_by, build):
    """Check the durable rename plus its matching metadata, under the fence."""
    taken, present = peek(folder, filename("taken", rid))
    if not present:
        return None, False
    meta, _ = peek(folder, filename("claim", rid))
    try:
        stamp = utc(meta["claimed_utc"])
        if (stamp < utc(claim_by) and meta == claim_record(taken, build, stamp)
                and taken["build"] == build and taken["request_id"] == rid and taken["sha256"] == request_sha256
                and taken["claim_by"] == claim_by and valid_request(taken, rid, stamp)):
            return meta, True
    except (ValueError, TypeError, KeyError, OverflowError):
        pass
    return None, True


def exchange(jobs, timeout, claim_s, clock, sleep=time.sleep, monotonic=time.monotonic, *,
             deadline, build, before_call=None, before_request=None, path=None):
    """Send the batch together, bound the wait, and leave disposal to the desk after its journal write."""
    start, began = clock(), monotonic()
    wall_budget = min(timeout, (deadline - start).total_seconds())
    if wall_budget <= 0:
        return {key: {"status": "no_time"} for key in jobs}, [], 0
    claim_by = min(deadline, start + timedelta(seconds=claim_s))
    requests = {key: request(fields, deadline, timeout, claim_by, build) for key, fields in jobs.items()}
    ids, claimed, results = [], set(), {}
    ignored = 0
    if not requests:
        return results, ids, ignored
    with private(path, create=True) as folder:
        for key, req in requests.items():
            rid = req["request_id"]
            ids.append(rid)
            if before_request:
                before_request(key, req)
            folder.write(filename("request", rid), req)
        while len(results) < len(requests):
            now = clock()
            elapsed = max(monotonic() - began, (now - start).total_seconds())
            for key, req in requests.items():
                if key in results:
                    continue
                rid = req["request_id"]
                claim_closed = now >= claim_by or elapsed >= min(claim_s, wall_budget)
                with suppress(BlockingIOError):
                    with folder.fence(blocking=False):
                        if key not in claimed:
                            if claim_closed:
                                folder.transfer(rid, "withdrawn")
                            claim, taken = inspect_claim(folder, rid, req["sha256"], req["claim_by"], build)
                            if claim is not None:
                                claimed.add(key)
                            elif taken or claim_closed:
                                results[key] = {"status": "scout_no_runner"}
                                ignored += int(taken)
                        name = filename("reply", rid)
                        reply, exists = peek(folder, name)
                        if exists:
                            accepted = reply_result(reply, req) if key in claimed else None
                            if accepted is None:
                                ignored += 1
                                folder.drop(name)
                            elif clock() < deadline and monotonic() - began < wall_budget:
                                results[key] = accepted
                        for name in folder.names():
                            if not name.startswith("reply-") or not name.endswith(".json"):
                                continue
                            other = name[len("reply-"):-len(".json")]
                            if other in ids:
                                continue
                            if not ID.fullmatch(other) or not any(
                                    peek(folder, filename(kind, other))[1] for kind in ("request", "taken")):
                                ignored += 1
                                folder.drop(name)
                if key not in results and elapsed >= wall_budget:
                    if key not in claimed:
                        # The reply lock might be busy at the deadline. The taken
                        # file is renamed only after its metadata is durable.
                        claim, taken = inspect_claim(folder, rid, req["sha256"], req["claim_by"], build)
                        if claim is not None:
                            claimed.add(key)
                        else:
                            ignored += int(taken)
                    results[key] = {"status": "call_timeout" if key in claimed else "scout_no_runner"}
            if len(results) != len(requests):
                sleep(min(POLL_S, max(0.0, wall_budget - elapsed)))
    if before_call:
        for key in requests:
            if key in claimed:
                before_call(key)
    return results, ids, ignored
