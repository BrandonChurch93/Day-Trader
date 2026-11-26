"""Sample the TM07 service-account boundary without sudo as a worker or any model call."""
import argparse
import errno
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from timemachine import desk

VERSION = "TM07-worker-probe-v3"
SCOPE = "same-host-service-account-sample"
WORKER_UID = 2000
SUDO_LOG = Path("/var/log/tm07-sudo.log")
STAGES = {"screen","extension"}
IDENTITIES = {*desk.SCOUTS,*(f"{boss}/{arm}" for boss in desk.BOSSES for arm in desk.ARMS)}
CHECKS = {"own_route_allowed","bearer_required","desk_routes_only","wrong_role_denied",
          "sibling_token_denied","study_and_rehearsal_unreadable"}
EXTENSION_CHECK = "extension_raw_bars_unreadable"


def private_root(path,uid):
    path = Path(path)
    info = path.lstat()
    if (uid in (0,WORKER_UID) or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700
            or str(path.resolve()) != str(path)):
        raise ValueError("expected a canonical mode-0700 root owned by the dedicated service uid")


def sudo_log_state():
    info = SUDO_LOG.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError("expected a root-owned mode-0600 sudo log")
    return [info.st_dev,info.st_ino]


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
        with open(path,"rb") as f:
            f.read(1)
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
    if challenge["raw_paths"]:
        checks[EXTENSION_CHECK] = raw_denied(challenge["raw_paths"])
    return dict(identity=identity,challenge=challenge["challenge"],checks=checks,uid=os.geteuid())


def raw_denied(paths):
    return all((denied_directory if kind == "dir" else denied_read)(p) for p,kind in paths.items())


def evaluate(transcript):
    """Validate the sampled observations, not the deployed boundary."""
    rows = transcript["observations"]
    stage = transcript["stage"]
    paths = transcript["raw_paths"]
    if (stage not in STAGES or bool(paths) != (stage == "extension")
            or any(not Path(p).is_absolute() or kind not in {"dir","file"} for p,kind in paths.items())):
        raise ValueError("invalid screen or extension raw bar inventory")
    expected = CHECKS | ({EXTENSION_CHECK} if paths else set())
    if len(rows) != len(IDENTITIES) or {r["identity"] for r in rows} != IDENTITIES:
        raise ValueError("isolation probes are missing roles")
    if len({r["challenge"] for r in rows}) != len(rows):
        raise ValueError("worker probe observation replayed")
    for row in rows:
        checks = row["checks"]
        if row["uid"] != WORKER_UID or set(checks) != expected or any(v is not True for v in checks.values()):
            raise ValueError(f'isolation probes failed for {row["identity"]}')
    return dict(version=VERSION,scope=SCOPE,root=transcript["root"],registration=transcript["registration"],
                release_digest=transcript["release_digest"],probe_transcript_digest=desk.digest(transcript),
                service_uid=transcript["service_uid"],worker_uid=WORKER_UID,sudo_log=transcript["sudo_log"],
                stage=stage,raw_paths=paths,passed=sorted(expected))


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
                      service_uid=uid,stage=profile["stage"],raw_paths=raw_paths,sudo_log=sudo_log_state(),observations=[])
    for i,e in sorted(entries.items()):
        challenge = dict(identity=i,challenge=secrets.token_hex(16),desk_url=profile["desk_url"],
                         session=e["session"],token=json.loads(Path(e["token_file"]).read_text()),
                         siblings=sorted(set(declared)-{e["session"]}),roots=[root,str(rehearsal)],
                         canaries=sorted(set(map(str,canaries))),raw_paths=raw_paths)
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
        put(ready,dict(workers=entries,service_uid=os.geteuid(),rehearsal_root=str(root),
                       desk_url=f"http://127.0.0.1:{srv.server_address[1]}"))
        srv.serve_forever()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    action = p.add_subparsers(dest="action",required=True)
    action.add_parser("worker")
    action.add_parser("worker-raw")
    a = action.add_parser("check-raw")
    a.add_argument("--receipt",type=Path,required=True)
    a.add_argument("--key-file",type=Path,required=True)
    c = action.add_parser("collect")
    for key in ("ready","registration","root","transcript"):
        c.add_argument("--"+key,type=Path,required=True)
    c.add_argument("--stage",choices=sorted(STAGES),required=True)
    c.add_argument("--raw-bar",action="append",default=[])
    r = action.add_parser("rehearse")
    r.add_argument("--rehearsal-root",type=Path,required=True)
    r.add_argument("--ready",type=Path,required=True)
    r.add_argument("--port",type=int,required=True)
    s = action.add_parser("seal")
    for key in ("transcript","key-file","receipt"):
        s.add_argument("--"+key,type=Path,required=True)
    s.add_argument("--sudo-log-reviewed",action="store_true",required=True)
    run = action.add_parser("serve")
    for key in ("receipt","key-file"):
        run.add_argument("--"+key,type=Path,required=True)
    run.add_argument("--port",type=int,required=True)
    args = p.parse_args()
    if args.action == "worker":
        print(desk.encode(worker(json.load(sys.stdin))))
    elif args.action == "worker-raw":
        if os.getuid() != WORKER_UID or os.geteuid() != WORKER_UID:
            raise ValueError("probe must run as uid 2000")
        print(desk.encode(raw_denied(json.load(sys.stdin))))
    elif args.action == "check-raw":
        receipt = json.loads(args.receipt.read_text())
        proof = receipt["body"]
        desk.validate_worker_boundary(args.key_file.read_text().strip(),proof,receipt["seal"],
                                      proof["root"],service_uid=proof["service_uid"])
        if (proof["stage"] != "extension" or inventory(proof["raw_paths"]) != proof["raw_paths"]
                or not as_worker("worker-raw",proof["raw_paths"])):
            raise ValueError("extension raw bar access check failed")
    elif args.action == "rehearse":
        rehearse(args.rehearsal_root,args.ready,args.port)
    elif args.action == "collect":
        profile = json.loads(args.ready.read_text())
        profile.update(root=str(args.root),registration=desk.digest(json.loads(args.registration.read_text())["body"]),
                       stage=args.stage,raw_bars=args.raw_bar)
        transcript = collect(profile)
        evaluate(transcript)
        put(args.transcript,transcript)
    elif args.action == "serve":
        from timemachine import server
        receipt = json.loads(args.receipt.read_text())
        with server.serve_desk(args.port,approval_key=args.key_file.read_text().strip(),
                               proof=receipt["body"],signature=receipt["seal"]) as listener:
            listener.serve_forever()
    else:
        if os.geteuid() != 0:
            raise ValueError("seal as the operator from a root shell")
        proof = dict(evaluate(json.loads(args.transcript.read_text())),sudo_log_reviewed=args.sudo_log_reviewed)
        if sudo_log_state() != proof["sudo_log"]:
            raise ValueError("sudo log changed since collection")
        key = args.key_file.read_text().strip()
        signature = desk.seal(key,"worker-boundary",proof)
        desk.validate_worker_boundary(key,proof,signature,proof["root"],service_uid=proof["service_uid"])
        put(args.receipt,dict(body=proof,seal=signature))


if __name__ == "__main__":
    main()
