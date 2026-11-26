"""TM09 copy of the TM07 operator sudo matcher (opmatch.py), which lists each sudo log line of a session window
against the timed operator records that osudo writes. Changes from the TM07 matcher: arguments must match
exactly (no quote, backslash or whitespace flattening; any argument outside plain characters cannot match), the
full executable path and the run-as account must match, a TM09 canary is listed only once, only for a nonce with a
root-owned checkpoint naming its session, and only 0-10 s after the operator record that ran that session's
checkpoint. The operator record file must be a regular file owned by the operator account. Its sha256 goes into
the output.

usage: tm09_opmatch.py ENTRIES_JSON OUT_JSON CANARIES_JSON OPLOG
  ENTRIES_JSON   {"sudo_entries": [...]} from `tm09_ops_sudo.py entries`
  CANARIES_JSON  {nonce: session} from the root-owned TM09 checkpoints
"""
import json
import os
import re
import stat
import sys
from hashlib import sha256

SECURE_PATH = ("/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin")
SAFE = re.compile(r"[A-Za-z0-9_./=:,+@%-]+")
LINE = re.compile(r"\w+ +\d+ (\d\d:\d\d:\d\d) : (\S+) : (.*?)COMMAND=(.*)$")
CANARY = re.compile(r"/usr/bin/true tm09-([0-9a-f]{32})")


def secs(t):
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def resolve(name, is_file=os.path.isfile):
    if name.startswith("/"):
        return os.path.normpath(name)
    if "/" in name:
        return None
    return next((d + "/" + name for d in SECURE_PATH if is_file(d + "/" + name)), None)


def split(argv):
    """Run-as account and command words of one osudo record."""
    a, user = list(argv), "root"
    while a and a[0] in ("-u", "-n", "-g"):
        if a[0] == "-u":
            user = a[1]
        a = a[2:] if a[0] in ("-u", "-g") else a[1:]
    return user, a


def is_checkpoint(words, sid):
    return any(w.endswith("tm09_ops_sudo.py") for w in words) and words[-3:-1] == ["checkpoint", sid]


def match(entries, recs, canaries, invoker="user", is_file=os.path.isfile):
    used, listed, miss, seen = set(), [], [], set()
    for line in entries:
        m = LINE.match(line.rstrip())
        if not m or m.group(2) != invoker:
            miss.append(line)
            continue
        t, cmd = m.group(1), m.group(4)
        fields = dict(f.strip().split("=", 1) for f in m.group(3).split(";") if "=" in f)
        target = fields.get("USER", "")
        c = CANARY.fullmatch(cmd)
        hit = None
        for i, r in enumerate(recs):
            dt = secs(t) - secs(r["time"])
            if i in used or abs(dt) > 10:
                continue
            user, a = split(r["argv"])
            if not a:
                continue
            if c:
                n = c.group(1)
                if (n not in seen and n in canaries and target == "root" and 0 <= dt <= 10
                        and is_checkpoint(a, canaries[n])):
                    hit = i
                    break
                continue
            if (abs(dt) <= 2 and user == target and all(SAFE.fullmatch(w) for w in a)
                    and resolve(a[0], is_file) is not None and cmd == resolve(a[0], is_file) + "".join(" " + w for w in a[1:])):
                hit = i
                break
        if hit is None:
            miss.append(line)
        else:
            if c:
                seen.add(c.group(1))
            else:
                used.add(hit)
            listed.append({"time": t, "command": cmd, "user": target})
    return listed, miss


def read_oplog(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise SystemExit("operator record file must be a regular file owned by the operator, not group or other writable")
        raw = f.read()
    return raw, [json.loads(l) for l in raw.decode().splitlines() if l.strip()]


if __name__ == "__main__":
    entries_path, out, canaries_path, oplog = sys.argv[1:5]
    entries = json.load(open(entries_path))["sudo_entries"]
    raw, recs = read_oplog(oplog)
    listed, miss = match(entries, recs, json.load(open(canaries_path)))
    json.dump(listed, open(out, "w"), indent=1)
    print("entries", len(entries), "matched", len(listed), "unmatched", len(miss), "oplog sha256", sha256(raw).hexdigest())
    for l in miss:
        print("UNMATCHED:", l[:300])
