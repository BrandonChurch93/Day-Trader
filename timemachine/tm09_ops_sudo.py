"""TM09 host ceremony on the TM07 operator route.

The sudo-log functions below are copied from tm07_isolation_probe.py (release 058a543, lines 45-130), the route
auditor b cleared and TM07 has run for five weeks. Only these change: the log owner and canary prefix are
parameters, the current canary must appear exactly once, and an operator entry must name its run-as account.
The glue after them writes the evidence and capsules the TM09 engine requires. Stated limits, the same as TM07:
the sudo audit catches a careless breach, not a deliberate hidden one, and workers share the host uid, so the
worker probe run here through runuser is host-uid evidence, not proof of the hosted worker's own sandbox.

  init-canaries                                        root, once: tm09desk-owned canary files for tape, notes, results
  approve-rehearsal BOUNDARY_TEXT                      root: invented-data rehearsal approval (ledger 222 scope)
  bearer-copy SLOT_DIR OUT                             root: worker-owned copy of one slot bearer for the probe
  checkpoint SID PORT                                  root: canary, private checkpoint, proof, launch capsule
  probe PHASE SID PORT NONCE SIBLING BEARER            root: isolation probe as the worker uid, four canaries
  new-go-id                                            root, once: id for the lead's one TM09_GO line (lead ruling)
  approve-build|approve-run AUTH_ID FIELDS_JSON        root, once per stage: fixture-build or run capsule, only if the pinned release
                                                       ledger row 222 final cell ends with the lead's approval wording and TM09_GO=AUTH_ID (engine parser), records the ledger
                                                       sha256; A or B also needs the engine's signed Stage 1 check
                                                       naming that branch (no second go line, same release)
  preflight MODE [RUN_CAPSULE EXPORT_DIR]              root: canaries exist; production: signed stage file set matches
  entries SID PORT NONCE                               root: after stop, cut the log lines since the checkpoint
  canaries                                             root: {nonce: session} of every TM09 checkpoint
  review MODE SID PORT NONCE DESK_DIR OPERATOR_SUDO            root: cut lines vs operator list, review capsule
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import stat
import subprocess
import sys

SUDO_LOG = Path("/var/log/tm07-sudo.log")
LOG_UID = 0
CANARY_PREFIX = "tm09-"
ROOT = Path("/var/lib/tm09")
CONTROL = ROOT/"control"      # root-owned checkpoints, as TM07 keeps /var/lib/tm07/control
OPS = ROOT/"ops-v2"           # tm09desk-readable evidence of this tool version; rehearsal-1 evidence stays in ops/
SERVICE = "tm09desk"
WORKER = "user"
CANARIES = [ROOT/"canaries/tape",ROOT/"canaries/notes",ROOT/"operator.key",ROOT/"canaries/results"]  # probe order
PORTS = range(8801,8807)
SID = re.compile(r"TM09-[0-9a-f]{32}")
NONCE = re.compile(r"[0-9a-f]{32}")
FILES = ("timemachine/tm09_desk.py","timemachine/tm09_orders.py","timemachine/tm09_fixture.py","timemachine/tm09_feed.py",
         "timemachine/tm09_operator.py","timemachine/tm09_isolation_probe.py","timemachine/score_tm09.py",
         "timemachine/tm09_blind.py","timemachine/test_tm09.py","timemachine/TM09_WORKER_BRIEFS.md")
LEDGER = "research_rig/TRIAL_LEDGER.md"
STAGE_FILES = {True:{"stock_sessions.jsonl","stock_bars.jsonl"},False:{"stock_sessions.jsonl","stock_bars.jsonl","stock_news.jsonl"}}
REHEARSAL_LIMITS = dict(notes=2,note_chars=280,looks=50,look_rows=120,headline_rows=20,headline_chars=500)


# ---- copied from tm07_isolation_probe.py with the parameter changes named above ----
def sudo_log_state():
    info = SUDO_LOG.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != LOG_UID or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError("expected a root-owned mode-0600 sudo log")
    return [info.st_dev,info.st_ino]


def log_snapshot(*,prefix=None,canary=None):
    """Hash a fixed-size sample of the root-owned sudo log, never a tape file."""
    expected = sudo_log_state()
    fd = os.open(SUDO_LOG,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as log:
        info = os.fstat(fd)
        size = info.st_size
        if (expected != [info.st_dev,info.st_ino] or info.st_uid != LOG_UID
                or not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                or prefix is not None and (prefix["id"] != expected or prefix["size"] > size)):
            raise ValueError("sudo log was replaced or truncated")
        digest = sha256()
        remaining = prefix["size"] if prefix else 0
        while remaining:
            b = log.read(min(remaining,65536))
            if not b:
                raise ValueError("sudo log truncated during the check")
            digest.update(b)
            remaining -= len(b)
        if prefix and digest.hexdigest() != prefix["sha256"]:
            raise ValueError("sudo log prefix changed")
        remaining = size-log.tell()
        matched = 0
        while remaining:
            line = log.readline(min(remaining,65536))
            if not line:
                raise ValueError("sudo log truncated during the check")
            digest.update(line)
            remaining -= len(line)
            if canary and re.search(rb"\buser\s*:\s+.*;\s*USER=root\s*;\s*COMMAND=/usr/bin/true "+CANARY_PREFIX.encode()
                                    +canary.encode()+rb"\s*\n$",line):
                matched += 1
        if canary and (size <= prefix["size"] or matched != 1):
            raise ValueError("sudo log did not grow and record the current canary command")
        return dict(id=expected,size=size,sha256=digest.hexdigest())


def sudo_checkpoint(nonce):
    before = log_snapshot()
    subprocess.run(["/usr/sbin/runuser","-u","user","--","/usr/bin/sudo","-n","/usr/bin/true",CANARY_PREFIX+nonce],
                   stdin=subprocess.DEVNULL,check=True,timeout=15)
    return dict(log_snapshot(prefix=before,canary=nonce),before_size=before["size"],canary=nonce)


def valid_log_checkpoint(value,nonce):
    return (isinstance(value,dict) and isinstance(value.get("sha256"),str)
            and re.fullmatch(r"[0-9a-f]{64}",value["sha256"]) is not None
            and type(value.get("before_size")) is int and type(value.get("size")) is int
            and 0 <= value["before_size"] < value["size"] and value.get("canary") == nonce)


def log_entries_after(checkpoint,limit=1<<20):
    """Lines the root-owned sudo log gained after a checkpoint (the soft, audited boundary)."""
    now = log_snapshot(prefix=checkpoint)
    fd = os.open(SUDO_LOG,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as log:
        log.seek(checkpoint["size"])
        data = log.read(min(now["size"]-checkpoint["size"],limit))
    if now["size"]-checkpoint["size"] > limit:
        raise ValueError("sudo log grew too much during the session to review")
    return now,[line for line in data.decode("utf-8","replace").splitlines() if line.strip()]


def sudo_review(entries,operator):
    """Void unless every sudo entry during the session matches an operator-listed time and command."""
    if not isinstance(operator,list) or any(not isinstance(o,dict) or not isinstance(o.get("time"),str)
                                            or not isinstance(o.get("command"),str) or not o["time"] or not o["command"]
                                            for o in operator):
        raise ValueError("operator sudo list must be [{time, command}] with both fields filled")
    unused = list(operator)
    unlisted = []
    for line in entries:
        hit = next((o for o in unused if o["time"] in line and line.rstrip().endswith("COMMAND="+o["command"])
                    and "; USER="+o.get("user","root")+" ;" in line),None)
        if hit is None:
            unlisted.append(line)
        else:
            unused.remove(hit)
    return dict(entries=len(entries),operator_listed=len(operator),unlisted=unlisted,void=bool(unlisted))



# ---- TM09 glue: evidence and capsules the engine requires ----
def h(raw):
    return sha256(raw).hexdigest()


def put(path,data,owner="service"):
    """New 0600 file, never overwritten (a repeated proof or review refuses)."""
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if owner:
        u = pwd.getpwnam(SERVICE if owner == "service" else owner)
        os.chown(path,u.pw_uid,u.pw_gid)


def check_probe(ev,sid,port,phase,nonce,launch_sha256):
    if (ev.get("phase") != phase or ev.get("session") != sid or ev.get("port") != port or ev.get("nonce") != nonce
            or ev.get("launch_sha256") != launch_sha256 or ev.get("denied_count") != len(CANARIES)
            or ev.get("canaries") != [str(p) for p in CANARIES]):
        raise ValueError(phase+" probe is not this launch's full four-canary probe")


def check_generation(control,launch,sid,port,nonce,fingerprint):
    c,l = control["body"],launch["body"]
    if (c.get("session"),c.get("nonce"),c.get("port")) != (sid,nonce,port) or (l["session"],l["nonce"],l["port"]) != (sid,nonce,port) \
            or c.get("boundary_sha256") != fingerprint(l):
        raise ValueError("control receipt is not this launch's generation")


def export_files(run_body,read,stage1,export_dir):
    export = Path(run_body["export_dir"])
    if (export.parent != ROOT or export != Path(export_dir) or not isinstance(run_body.get("export_sha256"),dict)
            or set(run_body["export_sha256"]) != STAGE_FILES[stage1]):
        raise ValueError("signed export scope must name this directory and exactly the stage's files")
    for name,pin in sorted(run_body["export_sha256"].items()):
        f = export/name
        if not f.is_file() or h(read(f)) != pin or f.stat().st_size == 0:
            raise ValueError("a signed export file is missing, empty or changed")
    return len(run_body["export_sha256"])


def go_line(ledger_raw,auth_id):
    """The engine's own docket check (tm09_operator.go_line), so ops and engine cannot disagree."""
    from timemachine.tm09_operator import go_line as engine_go_line
    engine_go_line(ledger_raw,auth_id)


def run_stage(body):
    if body.get("mode") not in ("stage1","A","B"):
        raise ValueError("run capsule must sign the data stage")
    return body["mode"] == "stage1"


def check_go(body,ledger_raw):
    """Every production preflight re-reads the pinned release ledger: same bytes as signed, docket line present."""
    if h(ledger_raw) != body.get("ledger_sha256"):
        raise ValueError("pinned release ledger differs from the one the run capsule signed")
    go_line(ledger_raw,body.get("authorization_id",""))


def main(argv):
    rel = Path(os.environ["TM09_RELEASE"])
    sys.path.insert(0,str(rel))
    from timemachine.tm09_desk import seal,verify_seal
    from timemachine.tm09_fixture import fingerprint,read_private,settings
    key = read_private(ROOT/"operator.key").decode().strip()

    def stage2_gate(body,cfg,registration):
        """The engine's own Stage 1 check receipt must name this branch before any Stage 2 input is opened."""
        from timemachine.tm09_blind import verify_stage2
        from timemachine.tm09_fixture import stage1_weeks
        verify_stage2(ROOT,key,body["mode"],body.get("blind_report_sha256"),h(cfg),h(registration),
                      len(stage1_weeks(settings(cfg)["study"])))

    def capsule(domain,body,path):
        put(path,(json.dumps({"body":body,"seal":seal(key,domain,body)},sort_keys=True)+"\n").encode())
        print(path.name,h(path.read_bytes()))

    cmd,a = argv[0],argv[1:]
    if cmd == "init-canaries":
        u = pwd.getpwnam(SERVICE)
        (ROOT/"canaries").mkdir(mode=0o700)
        os.chown(ROOT/"canaries",u.pw_uid,u.pw_gid)
        for p in CANARIES:
            if p.parent.name == "canaries":
                put(p,b"TM09 canary file; a worker must not be able to open it\n")
        print("canaries",len(CANARIES))
    elif cmd == "approve-rehearsal":
        cfg = read_private(rel/"config/thresholds.yaml")
        body = dict(root=str(ROOT),service_uid=pwd.getpwnam(SERVICE).pw_uid,release=str(rel),
                    approved_by="lead agent, ledger 222 (rehearsal and provisioning release)",
                    release_files={n:h(read_private(rel/n)) for n in FILES},config_sha256=h(cfg),
                    registration_sha256=h(read_private(rel/"timemachine/TM09_REGISTRATION.md")),
                    resolved_settings=settings(cfg),limits=dict(REHEARSAL_LIMITS),
                    operator_boundary_sha256=h(read_private(Path(a[0]))),ports=list(PORTS))
        capsule("ledger-222-rehearse-tm09",body,OPS/"rehearsal-approval.json")
    elif cmd == "new-go-id":
        auth = secrets.token_hex(16)
        put(CONTROL/"tm09-go-id",auth.encode(),owner=None)
        print("TM09_GO="+auth)
    elif cmd in ("approve-build","approve-run"):
        auth,fields = a[0],json.loads(read_private(Path(a[1])))
        stage1 = run_stage(fields)
        if read_private(CONTROL/"tm09-go-id").decode() != auth:
            raise ValueError("authorization id was not issued here")
        ledger = read_private(rel/LEDGER)
        go_line(ledger,auth)
        cfg = read_private(rel/"config/thresholds.yaml")
        if not stage1:
            stage2_gate(fields,cfg,read_private(rel/"timemachine/TM09_REGISTRATION.md"))
        export_files(fields,read_private,stage1,fields["export_dir"])
        body = dict(fields,root=str(ROOT),service_uid=pwd.getpwnam(SERVICE).pw_uid,release=str(rel),
                    approved_by="lead agent, ledger 222 line TM09_GO="+auth,authorization_id=auth,ledger_sha256=h(ledger),
                    release_files={n:h(read_private(rel/n)) for n in FILES},config_sha256=h(cfg),
                    registration_sha256=h(read_private(rel/"timemachine/TM09_REGISTRATION.md")),
                    resolved_settings=settings(cfg),ports=list(PORTS))
        scope,stem = ("ledger-222-build-fixtures","build") if cmd == "approve-build" else ("ledger-222-run-tm09","run")
        capsule(scope,body,OPS/f"{stem}-{fields['mode']}-{auth}.json")
    elif cmd == "bearer-copy":
        slot_dir,out = Path(a[0]),Path(a[1])
        w = pwd.getpwnam(WORKER)
        if slot_dir.parent not in (ROOT,ROOT/"invented-rehearsal") or out.parent.stat().st_uid != w.pw_uid \
                or out.parent.stat().st_mode & 0o077:
            raise ValueError("TM09 slot and a private worker-owned directory required")
        b = json.loads(read_private(slot_dir/"bearer.json"))
        put(out,json.dumps({"session":b["session"],"token":b["token"]}).encode(),owner=WORKER)
        print(out.name,b["session"])
    elif cmd == "checkpoint":
        sid,port = a[0],int(a[1])
        if not SID.fullmatch(sid) or port not in PORTS:
            raise ValueError("opaque session and TM09 port required")
        nonce = secrets.token_hex(16)
        cp = sudo_checkpoint(nonce)
        put(CONTROL/f"{sid}-{nonce}.checkpoint.json",json.dumps(dict(cp,session=sid,port=port)).encode(),owner=None)
        proof = json.dumps(dict(session=sid,port=port,nonce=nonce,matched_canary=True,prefix_unchanged=True,
                                size_before=cp["before_size"],size_after=cp["size"]),sort_keys=True).encode()
        put(OPS/f"{sid}-{nonce}-proof.json",proof)
        print(OPS/f"{sid}-{nonce}-proof.json")
        capsule("ledger-222-tm09-launch",dict(session=sid,port=port,nonce=nonce,canary_observed=True,
                sudo_size_before=cp["before_size"],sudo_size_after=cp["size"],sudo_checkpoint_sha256=h(proof)),
                OPS/f"{sid}-{nonce}-launch.json")
    elif cmd == "probe":
        phase,sid,port,nonce,sibling,bearer = a[0],a[1],int(a[2]),a[3],a[4],a[5]
        if phase not in ("live","stopped") or not NONCE.fullmatch(nonce) or not Path(bearer).is_absolute():
            raise ValueError("bad probe arguments")
        launch_sha256 = h(read_private(OPS/f"{sid}-{nonce}-launch.json"))
        run = subprocess.run(["/usr/sbin/runuser","-u",WORKER,"--","env","-i","PATH=/usr/bin:/bin","/usr/bin/python3.14","-B",
                              "-m","timemachine.tm09_isolation_probe","--port",str(port),"--session",sid,"--sibling",sibling,
                              "--bearer-file",bearer,*[x for p in CANARIES for x in ("--canary",str(p))],
                              *(["--stopped"] if phase == "stopped" else [])],cwd=rel,capture_output=True,text=True,timeout=60)
        if run.returncode:
            raise ValueError(phase+" worker probe failed")
        ev = dict(json.loads(run.stdout),nonce=nonce,launch_sha256=launch_sha256,canaries=[str(p) for p in CANARIES])
        check_probe(ev,sid,port,phase,nonce,launch_sha256)
        put(OPS/f"{sid}-{nonce}-{phase}-probe.json",json.dumps(ev,sort_keys=True).encode())
        print(f"{sid}-{nonce}-{phase}-probe.json denied",ev["denied_count"])
    elif cmd == "preflight":
        if a[0] not in ("rehearsal","production") or any(not p.is_file() for p in CANARIES):
            raise ValueError("mode and all four canary files required")
        n = 0
        if a[0] == "production":
            cap = json.loads(read_private(Path(a[1])))
            verify_seal(key,"ledger-222-run-tm09",cap["body"],cap["seal"])
            check_go(cap["body"],read_private(rel/LEDGER))
            stage1 = run_stage(cap["body"])
            if not stage1:
                stage2_gate(cap["body"],read_private(rel/"config/thresholds.yaml"),read_private(rel/"timemachine/TM09_REGISTRATION.md"))
            n = export_files(cap["body"],read_private,stage1,a[2])
        print("preflight canaries",len(CANARIES),"export files",n)
    elif cmd == "entries":
        sid,port,nonce = a[0],int(a[1]),a[2]
        cp = json.loads(read_private(CONTROL/f"{sid}-{nonce}.checkpoint.json"))
        if not valid_log_checkpoint(cp,nonce) or (cp["session"],cp["port"]) != (sid,port):
            raise ValueError("checkpoint is for another launch")
        now,entries = log_entries_after(cp)
        put(CONTROL/f"{sid}-{nonce}.entries.json",json.dumps(dict(now=now,sudo_entries=entries)).encode(),owner=None)
        print("entries",len(entries))
    elif cmd == "canaries":
        out = {}
        for p in sorted(CONTROL.glob("TM09-*.checkpoint.json")):
            cp = json.loads(read_private(p))
            if p.name == f"{cp['session']}-{cp['canary']}.checkpoint.json":
                out[cp["canary"]] = cp["session"]
        print(json.dumps(out,sort_keys=True))
    elif cmd == "review":
        mode,sid,port,nonce,desk_dir,operator = a[0],a[1],int(a[2]),a[3],Path(a[4]),Path(a[5])
        if mode not in ("rehearsal","production"):
            raise ValueError("mode required")
        cp = json.loads(read_private(CONTROL/f"{sid}-{nonce}.checkpoint.json"))
        if not valid_log_checkpoint(cp,nonce) or (cp["session"],cp["port"]) != (sid,port):
            raise ValueError("checkpoint is for another launch")
        launch_raw = read_private(OPS/f"{sid}-{nonce}-launch.json")
        launch = json.loads(launch_raw)
        verify_seal(key,"ledger-222-tm09-launch",launch["body"],launch["seal"])
        for phase in (("live","stopped") if mode == "rehearsal" else ("stopped",)):  # real sessions: post-stop only
            check_probe(json.loads(read_private(OPS/f"{sid}-{nonce}-{phase}-probe.json")),sid,port,phase,nonce,h(launch_raw))
        control = json.loads(read_private(desk_dir/f"{nonce}-control.json"))
        verify_seal(key,"tm09-control",control["body"],control["seal"])
        stop = json.loads(read_private(desk_dir/f"{nonce}-stop.json"))
        verify_seal(key,"tm09-stop",stop["body"],stop["seal"])
        check_generation(control,launch,sid,port,nonce,fingerprint)
        cut = json.loads(read_private(CONTROL/f"{sid}-{nonce}.entries.json"))
        if cut["now"]["size"] < cp["size"]:
            raise ValueError("cut is older than the checkpoint")
        log_snapshot(prefix=cut["now"])  # fails closed if the log shrank, rotated or changed since the cut
        entries = cut["sudo_entries"]
        result = dict(sudo_review(entries,json.loads(read_private(operator))),session=sid,nonce=nonce,
                      checkpoint_sha256=cp["sha256"],reviewed_to=cut["now"],operator_sudo_sha256=h(read_private(operator)))
        raw = json.dumps(result,sort_keys=True).encode()
        put(OPS/f"{sid}-{nonce}-sudo.json",raw)
        print("REVIEW",{k:result[k] for k in ("entries","operator_listed","unlisted","void")})
        if result["void"]:
            raise ValueError("unlisted sudo entries: not signing a review boundary")
        stopped_raw = read_private(OPS/f"{sid}-{nonce}-stopped-probe.json")
        capsule("ledger-222-tm09-review",dict(session=sid,port=port,nonce=nonce,control_sha256=fingerprint(control),
                post_stop_probe_sha256=h(stopped_raw),sudo_review_sha256=h(raw),sudo_allowlist_reviewed=True,
                raw_copies_denied=True,listener_stopped=True,void=False),OPS/f"{sid}-{nonce}-review.json")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (ValueError,KeyError,OSError) as exc:
        raise SystemExit("TM09 ops refused: "+str(exc))
