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
KINDS = ("request", "taken", "reply", "withdrawn")
CONTROL = {"heartbeat.json"}
FIELDS = {"request_id", "model", "system_text", "user_text", "reply_schema", "max_tokens", "timeout_s",
          "deadline", "take_until", "build"}


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


def request(fields, cutoff, timeout, take_until, build):
    body = dict(fields, request_id=uuid4().hex, deadline=cutoff.isoformat(), timeout_s=timeout,
                take_until=take_until.isoformat(), build=build)
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
                and now < utc(body["take_until"]) <= utc(body["deadline"]))
    except (ValueError, TypeError, KeyError, OverflowError):
        return False


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
    if status == "reply_late" and set(result) == {"status"}:
        return {"status": "call_timeout"} | duration
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

    def read(self, name):
        with self.file(name, os.O_RDONLY) as fd, os.fdopen(os.dup(fd), "rb") as inp:
            return json.load(inp)

    def write(self, name, data, *, swept_ok=False):
        tmp = "." + uuid4().hex
        try:
            with self.file(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY) as fd, os.fdopen(os.dup(fd), "wb") as out:
                out.write(encode(data) + b"\n")
                out.flush()
                os.fsync(out.fileno())
            try:
                self.rename(tmp, name)
            except FileNotFoundError:
                # A wake sweep may have removed a runner's unpublished file.
                if not swept_ok:
                    raise
        finally:
            self.drop(tmp)

    def rename(self, src, dst):
        os.rename(src, dst, src_dir_fd=self.fd, dst_dir_fd=self.fd)
        os.fsync(self.fd)

    def drop(self, name):
        try:
            os.unlink(name, dir_fd=self.fd)
            return True
        except FileNotFoundError:
            return False

    def exists(self, name):
        try:
            os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False

    def names(self):
        return os.listdir(self.fd)

    def transfer(self, rid, dest):
        try:
            self.rename(filename("request", rid), filename(dest, rid))
            return True
        except FileNotFoundError:
            return False

    def take(self, req, build, clock, until):
        rid = req["request_id"]
        if not valid_request(req, rid, clock()) or req["build"] != build:
            return False
        return clock() < min(until, utc(req["take_until"])) and self.transfer(rid, "taken")

    def pop_reply(self, rid):
        # Move this publication out of the way before reading it. A replacement
        # can then arrive without being unlinked in place of the one we read.
        readback = ".read-" + uuid4().hex
        try:
            self.rename(filename("reply", rid), readback)
        except FileNotFoundError:
            return None, False
        try:
            body, _ = peek(self, readback)
            return body, True
        finally:
            self.drop(readback)

    def sweep(self, keep):
        expected = CONTROL | {filename(kind, rid) for rid in keep for kind in KINDS}
        ignored = sum(self.drop(name) for name in set(self.names()) - expected)
        os.fsync(self.fd)
        return ignored

    def cleanup(self, ids):
        ignored = 0
        for rid in ids:
            for kind in KINDS:
                removed = self.drop(filename(kind, rid))
                ignored += int(kind == "reply" and removed)
        os.fsync(self.fd)
        return ignored


@contextmanager
def directory(path, *, create=False):
    if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(CUSTODY):
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
        yield fd
    finally:
        os.close(fd)


@contextmanager
def private(path=None, *, create=False):
    path = Path(DEFAULT if path is None else path)
    if path == CUSTODY:
        raise Refuse("scout directory is outside custody")
    with directory(path, create=create) as fd:
        if stat.S_IMODE(os.fstat(fd).st_mode) != 0o700:
            raise Refuse("scout directory must be private")
        yield Folder(fd)


@contextmanager
def desk_owner():
    """One desk owner across start and wake, without opening the spool."""
    with directory(CUSTODY) as fd:
        with Folder(fd).file(".desk_e17_scout.owner.lock", os.O_CREAT | os.O_RDWR) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield


def cleanup(ids, path=None):
    if ids:
        with private(path) as folder:
            return folder.cleanup(ids)
    return 0


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


def exchange(jobs, timeout, claim_s, clock, sleep=time.sleep, monotonic=time.monotonic, *,
             deadline, build, before_call=None, before_request=None, path=None):
    """Send the batch together, bound the wait, and leave disposal to the desk after its journal write."""
    start, began = clock(), monotonic()
    wall_budget = min(timeout, (deadline - start).total_seconds())
    if wall_budget <= 0:
        return {key: {"status": "no_time"} for key in jobs}, [], 0
    claim_wait = min(claim_s, wall_budget)
    take_until = min(deadline, start + timedelta(seconds=claim_wait))
    requests = {key: request(fields, deadline, timeout, take_until, build) for key, fields in jobs.items()}
    ids, taken, results = [], set(), {}
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
                rid = req["request_id"]
                if key not in results and key not in taken:
                    if elapsed >= claim_wait:
                        if folder.transfer(rid, "withdrawn"):
                            results[key] = {"status": "scout_no_runner"}
                        else:
                            # The only other consumer of the request name is take.
                            taken.add(key)
                    elif folder.exists(filename("taken", rid)):
                        taken.add(key)
                reply, exists = folder.pop_reply(rid)
                if exists:
                    if key not in results and key not in taken and folder.exists(filename("taken", rid)):
                        taken.add(key)  # Take may have won since our first check.
                    accepted = reply_result(reply, req) if key not in results and key in taken else None
                    if accepted is not None and clock() < deadline and monotonic() - began < wall_budget:
                        results[key] = accepted
                    else:
                        ignored += 1
                if key not in results and elapsed >= wall_budget:
                    results[key] = {"status": "call_timeout"}
            for name in folder.names():
                if name.startswith("reply-") and name.endswith(".json"):
                    other = name[len("reply-"):-len(".json")]
                    if other not in ids:
                        ignored += int(folder.drop(name))
            if len(results) != len(requests):
                edge = claim_wait if elapsed < claim_wait else wall_budget
                sleep(min(POLL_S, max(0.0, edge - elapsed)))
    if before_call:
        for key in requests:
            if key in taken:
                before_call(key)
    return results, ids, ignored
