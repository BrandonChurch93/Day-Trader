"""The private pass log and the duplicate guard.

One JSON line per event in <private_dir>/log.jsonl (folder 0700, file 0600, fsynced). Only our own data is kept:
post and question ids, the question type, a hash of the question text (not the text: the site's terms bar storing a
significant portion of its content), our forecasts, our comment's hash and every outcome.

Duplicate guard:
- a post is answered once: a `submitted` row for every question of the task, or our own forecast already on the site,
  means it is skipped and recorded as already answered;
- before each submission a `claim` row is written; a claim without a result (a crash or an unknown HTTP outcome) is
  settled next pass by reading our own forecasts on the site, never by sending again blind;
- every open post seen in a pass gets exactly one outcome row in that pass, so nothing is skipped silently.
"""
import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path


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
                raise RuntimeError("another pass holds the bot lock") from None
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
        line = json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False)
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        try:
            os.write(fd, (line + "\n").encode())
            os.fsync(fd)
        finally:
            os.close(fd)
        return row


def index(rows):
    """What the log says: questions submitted, claims not yet settled, and tries per post."""
    submitted, claims, attempts = set(), {}, {}
    for r in rows:
        kind = r.get("kind")
        if kind == "attempt":
            attempts[r["post_id"]] = attempts.get(r["post_id"], 0) + 1
        elif kind == "claim":
            claims[r["claim_id"]] = r
        elif kind in ("outcome", "settle"):
            if r.get("claim_id"):
                claims.pop(r["claim_id"], None)
            if r.get("status") in ("submitted", "submitted_confirmed_later"):
                submitted.update(r.get("question_ids") or [])
    return {"submitted": submitted, "open_claims": claims, "attempts": attempts}
