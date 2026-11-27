"""The private pass log and the duplicate guard.

One JSON line per event in <private_dir>/log.jsonl (folder 0700, file 0600, fsynced). Only our own data is kept:
post and question ids, the question type, a hash of the question text (not the text: the site's terms bar storing a
significant portion of its content), our forecasts, our comment's hash, model call counts and every outcome. Every
line passes through metaculus.redact_held before it is written, so a held token can never reach the file.

Duplicate guard:
- a post is answered once: a `submitted` row for every question of the task, or our own forecast already on the site,
  means it is skipped and recorded as already answered;
- before each submission a `claim` row is written. A claim without a result (a crash or an unknown HTTP outcome) is
  settled on a later pass by reading our own forecasts on the site, never by sending again blind. `settle` rows record
  submitted_confirmed_later (every id shows a forecast) or claim_not_on_site (every id reported, none with a forecast);
  both close the claim. claim_cannot_check (an id omitted) leaves it open and the post is not sent; after the claim
  is 24 hours old that row is written once per UTC day, not once per pass;
- every open post seen in a pass gets exactly one outcome row in that pass, so nothing is skipped silently.
"""
import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

from .metaculus import redact_held


class Busy(RuntimeError):
    """Another pass holds the bot lock."""


def text_hash(q, ctx=None):
    parts = [q.get(k) or "" for k in ("title", "description", "resolution_criteria", "fine_print")]
    parts += [json.dumps(ctx or {}, sort_keys=True)]
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


class Log:
    def __init__(self, folder):
        self.dir = Path(folder)
        self.path = self.dir / "log.jsonl"

    def ensure(self):
        self.dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.dir, 0o700)
        if not self.path.exists():
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            os.close(fd)

    @contextmanager
    def locked(self):
        self.ensure()
        fd = os.open(self.dir / ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Busy("another pass holds the bot lock") from None
            yield self
        finally:
            os.close(fd)

    def rows(self):
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text().splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out

    def add(self, **row):
        line = redact_held(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False))
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        try:
            os.write(fd, (line + "\n").encode())
            os.fsync(fd)
        finally:
            os.close(fd)
        return row


def index(rows):
    """What the log says: questions submitted, claims not yet settled, and tries per post."""
    submitted, claims, attempts, calls, noted = set(), {}, {}, {}, {}
    for r in rows:
        kind = r.get("kind")
        if kind == "calls":
            calls[r["day"]] = calls.get(r["day"], 0) + r["n"]
        if kind == "settle" and r.get("status") == "claim_cannot_check" and r.get("open_claim_id"):
            noted.setdefault(r["open_claim_id"], set()).add(r.get("day"))
        if kind == "attempt":
            attempts[r["post_id"]] = attempts.get(r["post_id"], 0) + 1
        elif kind == "claim":
            claims[r["claim_id"]] = r
        elif kind in ("outcome", "settle"):
            if r.get("claim_id"):
                claims.pop(r["claim_id"], None)
            if r.get("status") in ("submitted", "submitted_confirmed_later"):
                submitted.update(r.get("question_ids") or [])
    return {"submitted": submitted, "open_claims": claims, "attempts": attempts, "calls_by_day": calls,
            "cannot_check_days": noted}
