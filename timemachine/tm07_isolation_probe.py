"""Sample the TM07 service-account boundary without sudo as a worker or any model call."""
import argparse
import errno
from hashlib import sha256
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from timemachine import desk

VERSION = "TM07-worker-probe-v5"
SCOPE = "same-host-service-account-sample"
WORKER_UID = 2000
SUDO_LOG = Path("/var/log/tm07-sudo.log")
# Ruling 2026-11-26: one scored stage; every one of the 20 weeks needs raw price copies denied to uid 2000.
STAGES = {"scored"}
IDENTITIES = {*desk.SCOUTS,*(f"{boss}/{arm}" for boss in desk.BOSSES for arm in desk.ARMS)}
CHECKS = {"own_route_allowed","bearer_required","desk_routes_only","wrong_role_denied",
          "sibling_token_denied","study_and_rehearsal_unreadable"}
LAUNCH_TTL = 600


def private_root(path,uid):
    path = Path(path)
    info = path.lstat()
    if (uid in (0,WORKER_UID) or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700
            or str(path.resolve()) != str(path)):
        raise ValueError("expected a canonical mode-0700 root owned by the dedicated service uid")
    return [info.st_dev,info.st_ino]


def sudo_log_state():
    info = SUDO_LOG.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError("expected a root-owned mode-0600 sudo log")
    return [info.st_dev,info.st_ino]


def log_snapshot(*,prefix=None,canary=None):
    """Hash a fixed-size sample of the root-owned sudo log, never a tape file."""
    expected = sudo_log_state()
    fd = os.open(SUDO_LOG,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as log:
        info = os.fstat(fd)
        size = info.st_size
        if (expected != [info.st_dev,info.st_ino] or info.st_uid != 0
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
        matched = False
        while remaining:
            line = log.readline(min(remaining,65536))
            if not line:
                raise ValueError("sudo log truncated during the check")
            digest.update(line)
            remaining -= len(line)
            if canary and re.search(rb"\buser\s*:\s+.*;\s*USER=root\s*;\s*COMMAND=/usr/bin/true tm07-"
                                    +canary.encode()+rb"\s*\n$",line):
                matched = True
        if canary and (size <= prefix["size"] or not matched):
            raise ValueError("sudo log did not grow and record the current canary command")
        return dict(id=expected,size=size,sha256=digest.hexdigest())


def sudo_checkpoint(nonce):
    before = log_snapshot()
    subprocess.run(["/usr/sbin/runuser","-u","user","--","/usr/bin/sudo","-n","/usr/bin/true","tm07-"+nonce],
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
        hit = next((o for o in unused if o["time"] in line and line.rstrip().endswith("COMMAND="+o["command"])),None)
        if hit is None:
            unlisted.append(line)
        else:
            unused.remove(hit)
    return dict(entries=len(entries),operator_listed=len(operator),unlisted=unlisted,void=bool(unlisted))


def consume_receipt(root,proof):
    """Pin the directory instance and race concurrent starts on one exclusive create."""
    fd = os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if ([info.st_dev,info.st_ino] != proof["root_id"] or info.st_uid != proof["service_uid"]
                or stat.S_IMODE(info.st_mode) != 0o700 or time.time() >= proof["expires_at"]):
            raise ValueError("worker boundary study root changed or receipt expired")
        try:
            claim = os.open(".launch-used-"+proof["nonce"],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600,dir_fd=fd)
        except FileExistsError as exc:
            raise ValueError("launch receipt already consumed") from exc
        os.close(claim)
    finally:
        os.close(fd)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def request(base,route,sid,token,body=None):
    url = base.rstrip("/")+route+"?"+urllib.parse.urlencode({"session":sid})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    headers = {"Content-Type":"application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer "+token
    req = urllib.request.Request(url,None if body is None else desk.encode(body).encode(),headers)
    try:
        with op.open(req,timeout=3) as resp:
            return resp.status,json.loads(resp.read(200000))
    except urllib.error.HTTPError as exc:
        with exc:
            return exc.code,{}


def denied_read(path):
    try:
        with open(path,"rb",opener=lambda p,flags:os.open(p,flags|os.O_NOFOLLOW|os.O_NONBLOCK)):
            pass  # permission test only; even a readable raw tape yields no bytes
    except OSError as exc:
        if exc.errno in (errno.EACCES,errno.EPERM):
            return True
        raise
    return False


def denied_directory(path):
    if os.access(path,os.X_OK):
        return False
    try:
        with os.scandir(path) as entries:
            next(entries,None)
    except OSError as exc:
        if exc.errno in (errno.EACCES,errno.EPERM):
            return True
        raise
    return False


def worker(challenge):
    """Run on the same host as a sibling worker, without sudo."""
    if os.getuid() != WORKER_UID or os.geteuid() != WORKER_UID:
        raise ValueError("probe must run as uid 2000")
    identity = challenge["identity"]
    base,sid,token = challenge["desk_url"],challenge["session"],challenge["token"]
    code, own = request(base,"/desk/next",sid,token)
    role = identity if identity in desk.SCOUTS else "boss"
    if code != 200 or own.get("session") != sid or own.get("role") != role or not own.get("wake_key"):
        raise ValueError("positive control: worker could not read its live rehearsal packet")
    forbidden = "/desk/notes" if role == "boss" else "/desk/pick"
    checks = {
        "own_route_allowed":True,
        "bearer_required":all(request(base,r,sid,None,body)[0] == 403 for r,body in
                              [(r,None) for r in ("/desk/next","/desk/status")]+
                              [(r,{}) for r in ("/desk/look","/desk/pick","/desk/usage","/desk/notes")]),
        "desk_routes_only":all(request(base,r,sid,token,body)[0] == 404 for r,body in
                               (("/next",None),("/status",None),("/look",None),("/pick",{}),("/score",None),("/desk/score",None))),
        "wrong_role_denied":request(base,forbidden,sid,token,{"wake_key":own["wake_key"]})[0] == 403,
        "sibling_token_denied":all(request(base,"/desk/next",s,token)[0] == 403 for s in challenge["siblings"]),
        "study_and_rehearsal_unreadable":(all(denied_directory(p) for p in challenge["roots"])
                                         and all(denied_read(p) for p in challenge["canaries"])),
    }
    return dict(identity=identity,challenge=challenge["challenge"],checks=checks,uid=os.geteuid())


def readable_raw_path(paths):
    return next((p for p,kind in paths.items()
                 if not (denied_directory if kind == "dir" else denied_read)(p)),None)


def check_raw(paths):
    if not paths or inventory(paths) != paths:
        raise ValueError("raw bar inventory is missing or changed")
    readable = as_worker("worker-raw",paths)
    if readable is not None:
        raise ValueError(f"raw bar source is readable: {readable}")


def evaluate(transcript):
    """Validate the sampled observations, not the deployed boundary."""
    rows = transcript["observations"]
    stage = transcript["stage"]
    paths = transcript["raw_paths"]
    if (stage not in STAGES or not paths
            or any(not Path(p).is_absolute() or kind not in {"dir","file"} for p,kind in paths.items())):
        raise ValueError("invalid scored-stage raw bar inventory")
    if len(rows) != len(IDENTITIES) or {r["identity"] for r in rows} != IDENTITIES:
        raise ValueError("isolation probes are missing roles")
    if len({r["challenge"] for r in rows}) != len(rows):
        raise ValueError("worker probe observation replayed")
    for row in rows:
        checks = row["checks"]
        if row["uid"] != WORKER_UID or set(checks) != CHECKS or any(v is not True for v in checks.values()):
            raise ValueError(f'isolation probes failed for {row["identity"]}')
    return dict(version=VERSION,scope=SCOPE,root=transcript["root"],registration=transcript["registration"],
                release_digest=transcript["release_digest"],probe_transcript_digest=desk.digest(transcript),
                service_uid=transcript["service_uid"],worker_uid=WORKER_UID,
                stage=stage,raw_paths=paths,passed=sorted(CHECKS))


def release_fingerprint():
    digests = {}
    package = Path(__file__).resolve().parent
    for path in sorted(package.rglob("*.py")):
        info = path.stat()
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError("release code must be root-owned and not group/world writable")
        with path.open("rb") as f:
            hashing = sha256()
            for block in iter(lambda:f.read(65536),b""):
                hashing.update(block)
            digests[str(path.relative_to(package))] = hashing.hexdigest()
    return desk.digest([sys.version,digests])


def as_worker(action,payload):
    if os.geteuid() != 0:
        raise ValueError("operator command must run as root")
    return json.loads(subprocess.run(
        ["/usr/sbin/runuser","-u","user","--",sys.executable,"-B","-m","timemachine.tm07_isolation_probe",action],
        input=desk.encode(payload),text=True,
        capture_output=True,timeout=90,check=True).stdout)


def inventory(files):
    paths = {}
    for name in files:
        path = Path(name).resolve(strict=True)
        mode = path.stat().st_mode
        if stat.S_ISDIR(mode):
            paths[str(path)] = "dir"
        elif stat.S_ISREG(mode):
            paths[str(path)] = "file"
        else:
            raise ValueError("raw bar inventory must contain regular files or directories")
    return paths


def collect(profile):
    entries = profile["workers"]
    root = str(Path(profile["root"]).resolve(strict=True))
    rehearsal = Path(profile["rehearsal_root"]).resolve(strict=True)
    if Path(root) == rehearsal or Path(root).is_relative_to(rehearsal) or rehearsal.is_relative_to(Path(root)):
        raise ValueError("rehearsal and registered roots must be separate")
    uid = profile["service_uid"]
    private_root(root,uid)
    private_root(rehearsal,uid)
    if set(entries) != IDENTITIES:
        raise ValueError("name all eight roles")
    declared = [e["session"] for e in entries.values()]
    if len(set(declared)) != 7:
        raise ValueError("probe expects two scout roles, sharing one scout session, and six boss sessions")
    if entries[desk.SCOUTS[0]]["session"] != entries[desk.SCOUTS[1]]["session"]:
        raise ValueError("probe scout roles must share the rehearsal scout session ID")
    canaries = [Path(v[k]).resolve(strict=True) for v in entries.values() for k in ("fixture","journal","token_file")]
    canaries += [rehearsal/"operator"/"scorer-canary.json"]
    if any(not p.is_relative_to(rehearsal) or not p.is_file() or denied_read(p) for p in canaries):
        raise ValueError("missing or unreadable rehearsal control file")
    # A real private directory and every named rehearsal file are positive-tested
    # by the operator before accepting any permission denial as evidence.
    raw_paths = inventory(profile["raw_bars"])
    transcript = dict(root=root,registration=profile["registration"],release_digest=release_fingerprint(),
                      service_uid=uid,stage=profile["stage"],raw_paths=raw_paths,observations=[])
    for i,e in sorted(entries.items()):
        challenge = dict(identity=i,challenge=secrets.token_hex(16),desk_url=profile["desk_url"],
                         session=e["session"],token=json.loads(Path(e["token_file"]).read_text()),
                         siblings=sorted(set(declared)-{e["session"]}),roots=[root,str(rehearsal)],
                         canaries=sorted(set(map(str,canaries))))
        row = as_worker("worker",challenge)
        if (set(row) != {"identity","challenge","checks","uid"}
                or any(row[k] != challenge[k] for k in ("identity","challenge"))):
            raise ValueError("worker did not return the matching challenge")
        transcript["observations"].append(row)
    return transcript


def put(path,value):
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w") as f:
        f.write(desk.encode(value)+"\n")


def rehearse(root,ready,port):
    """Stand up only self-created made-up sessions, with the same DeskH."""
    from http.server import ThreadingHTTPServer
    from timemachine import server
    from timemachine.test_tm07 import world

    root = root.resolve()
    if os.geteuid() in (0,WORKER_UID):
        raise ValueError("start rehearsal under the dedicated service account")
    root.mkdir(mode=0o700)
    secrets_dir = root/"operator"
    secrets_dir.mkdir(mode=0o700)
    scorer = secrets_dir/"scorer-canary.json"
    put(scorer,{"toy":True})
    os.environ["TM07_RUNS_DIR"] = str(root)
    entries = {}
    spec = dict(world(),vendor_proofs={})
    for i,identity in enumerate(sorted(IDENTITIES)):
        if identity in desk.SCOUTS:
            sid,arm,boss = "TM07-probe-scout","scout",desk.BOSSES[0]
            if identity != sorted(desk.SCOUTS)[0]:
                continue
        else:
            boss,arm = identity.split("/")
            sid = f"TM07-probe-{i}-{arm}"
        path = root/sid
        tokens = desk.issue_role_tokens(arm)
        scout = None
        if arm != "A" and arm != "scout":
            # The static rehearsal packet contains no real evidence or work.
            scout = dict(fixture=desk.digest(spec),neutral_id="TM07-probe-scout",usage=[],
                         wakes=[dict(wake=t,notes=[]) for t in spec["wakes"]])
            key = "rehearsal-only-"+secrets.token_hex(24)
            scout["seal"] = desk.seal(key,"scout",scout)
        else:
            key = None
        desk.create_desk(path,spec,arm,boss,tokens,scout,approval_key=key)
        for role,token in tokens.items():
            who = role if arm == "scout" else identity
            target = secrets_dir/f"token-{who.replace('/','-')}"
            put(target,token)
            entries[who] = dict(session=sid,token_file=str(target),fixture=str(path/"fixture.json"),
                                journal=str(path/"desk.sqlite"))
    with ThreadingHTTPServer(("127.0.0.1",port),server.DeskH) as srv:
        # This listener has only the generated rehearsal root, never a registered study.
        srv.desk_registration = None
        srv.desk_stage = None
        srv.desk_session = None
        pending = ready.with_name(ready.name+".pending")
        put(pending,dict(workers=entries,service_uid=os.geteuid(),rehearsal_root=str(root),
                         desk_url=f"http://127.0.0.1:{srv.server_address[1]}"))
        pending.rename(ready)
        srv.serve_forever()


def service_command(account,*args):
    return ["/usr/bin/setpriv","--reuid",str(account.pw_uid),"--regid",str(account.pw_gid),"--init-groups",
            sys.executable,"-B","-m","timemachine.tm07_isolation_probe",*args]


def stop(child):
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def launch_session(args):
    if os.geteuid() != 0 or pwd.getpwnam("user").pw_uid != WORKER_UID:
        raise ValueError("launch from the operator root shell with worker user at uid 2000")
    if not desk.SID.fullmatch(args.session) or not 1 <= args.port <= 65535:
        raise ValueError("name one registered session and a fixed listener port")
    account = pwd.getpwnam("tm07desk")
    root = str(args.root.resolve(strict=True))
    root_id = private_root(root,account.pw_uid)
    launch = dict(nonce=secrets.token_hex(32),port=args.port,stage=args.stage,session=args.session)
    issued = int(time.time())
    key = args.key_file.read_text().strip()
    registration = json.loads(args.registration.read_text())
    desk.verify_seal(key,"registration",registration["body"],registration.get("seal"))
    if registration["body"].get("study_root") != root:
        raise ValueError("registration names a different study root")
    # Start a new toy listener on the intended live port during this launch.
    with tempfile.TemporaryDirectory(prefix="tm07-launch-") as tmp:
        os.chown(tmp,account.pw_uid,account.pw_gid)
        rehearsal,ready = Path(tmp)/"rehearsal",Path(tmp)/"ready.json"
        toy = subprocess.Popen(service_command(account,"rehearse","--rehearsal-root",str(rehearsal),
                                               "--ready",str(ready),"--port",str(args.port)),
                               stdin=subprocess.DEVNULL,start_new_session=True)
        try:
            while not ready.exists():
                if toy.poll() is not None or time.time() >= issued+LAUNCH_TTL:
                    raise ValueError("fresh rehearsal did not become ready")
                time.sleep(.05)
            profile = json.loads(ready.read_text())
            if profile["desk_url"] != f"http://127.0.0.1:{args.port}" or profile["service_uid"] != account.pw_uid:
                raise ValueError("fresh rehearsal port or service uid changed")
            profile.update(root=root,registration=desk.digest(registration["body"]),stage=args.stage,raw_bars=args.raw_bar)
            transcript = collect(profile)
            proof = evaluate(transcript)
        finally:
            stop(toy)
    check_raw(proof["raw_paths"])
    checkpoint = sudo_checkpoint(launch["nonce"])
    # Ruling 2026-11-26: passwordless worker sudo stays. It is a recorded fact, not a refusal;
    # the canary just succeeded with sudo -n, so it is true for this launch.
    proof.update(launch,root_id=root_id,issued_at=issued,expires_at=issued+LAUNCH_TTL,
                 raw_checked=True,worker_passwordless_sudo=True,sudo_log=checkpoint)
    signature = desk.seal(key,"worker-boundary",proof)
    desk.validate_worker_boundary(key,proof,signature,root,service_uid=account.pw_uid,launch=launch)
    # The receipt travels on a private inherited pipe, not as a reusable file.
    put(args.audit,dict(launch=launch,sudo_before=checkpoint,probe_transcript=transcript))
    child = None
    outcome = "incomplete"
    try:
        env = dict(os.environ,TM07_RUNS_DIR=root,PYTHONNOUSERSITE="1")
        child = subprocess.Popen(service_command(account,"serve","--key-file",str(args.key_file)),
                                 env=env,stdin=subprocess.PIPE,text=True,start_new_session=True)
        with child.stdin:
            child.stdin.write(desk.encode(dict(launch=launch,body=proof,seal=signature)))
        code = child.wait()
        if code:
            raise ValueError(f"registered listener exited with status {code}")
        outcome = "stopped"
    except KeyboardInterrupt:
        outcome = "operator-stop"
    finally:
        if child is not None:
            stop(child)
        after = {"outcome":outcome}
        try:
            after["sudo_after"],after["sudo_entries"] = log_entries_after(checkpoint)
            check_raw(proof["raw_paths"])
            after["raw_denied_after"] = True
        except (ValueError,OSError,subprocess.SubprocessError) as exc:
            after.update(outcome="invalid",error=str(exc))
            raise
        finally:
            put(args.audit.with_name(args.audit.name+".after.json"),after)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    action = p.add_subparsers(dest="action",required=True)
    action.add_parser("worker")
    action.add_parser("worker-raw")
    start = action.add_parser("launch")
    for key in ("registration","root","key-file","audit"):
        start.add_argument("--"+key,type=Path,required=True)
    start.add_argument("--stage",choices=sorted(STAGES),required=True)
    start.add_argument("--session",required=True)
    start.add_argument("--port",type=int,required=True)
    start.add_argument("--raw-bar",action="append",default=[])
    r = action.add_parser("rehearse")
    r.add_argument("--rehearsal-root",type=Path,required=True)
    r.add_argument("--ready",type=Path,required=True)
    r.add_argument("--port",type=int,required=True)
    rv = action.add_parser("review")
    for key in ("after","operator-sudo","out"):
        rv.add_argument("--"+key,type=Path,required=True)
    run = action.add_parser("serve")
    run.add_argument("--key-file",type=Path,required=True)
    args = p.parse_args()
    if args.action == "worker":
        print(desk.encode(worker(json.load(sys.stdin))))
    elif args.action == "worker-raw":
        if os.getuid() != WORKER_UID or os.geteuid() != WORKER_UID:
            raise ValueError("probe must run as uid 2000")
        print(desk.encode(readable_raw_path(json.load(sys.stdin))))
    elif args.action == "rehearse":
        rehearse(args.rehearsal_root,args.ready,args.port)
    elif args.action == "launch":
        def interrupt(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGTERM,interrupt)
        launch_session(args)
    elif args.action == "review":
        after = json.loads(args.after.read_text())
        if "sudo_entries" not in after:
            raise ValueError("after-audit has no sudo entries; the session cannot be reviewed")
        result = sudo_review(after["sudo_entries"],json.loads(args.operator_sudo.read_text()))
        if after.get("outcome") not in ("stopped","operator-stop") or after.get("raw_denied_after") is not True:
            result.update(void=True,after_problem=dict(outcome=after.get("outcome"),raw_denied_after=after.get("raw_denied_after")))
        put(args.out,dict(result,after=str(args.after),manual_checks_pending=[
            "server log: no route other than the session's own desk routes",
            "worker command and address list: no direct read of a listed price copy, no outside price lookup"]))
        print("VOID" if result["void"] else "no unlisted sudo entry")
    elif args.action == "serve":
        from timemachine import server
        receipt = json.load(sys.stdin)
        with server.serve_desk(**receipt["launch"],approval_key=args.key_file.read_text().strip(),
                               proof=receipt["body"],signature=receipt["seal"]) as listener:
            print("Registered desk ready; brief only this session's roles.",flush=True)
            listener.serve_forever()


if __name__ == "__main__":
    main()
