"""Sampled operator rehearsal checks for the TM07 launch path, without a model call."""
import argparse
import errno
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from timemachine import desk

VERSION = "TM07-worker-probe-v2"
SCOPE = "sampled-rehearsal-only"
IDENTITIES = {*desk.SCOUTS,*(f"{boss}/{arm}" for boss in desk.BOSSES for arm in desk.ARMS)}
CHECKS = {"desk_routes_only","wrong_role_denied","sibling_token_denied","fixture_read_denied",
          "sibling_journal_read_denied","scorer_state_denied","outbound_denied","fresh_context","role_only_handoff"}
PHASES = ("fresh","handoff","reset")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def request(base,route,sid,token,body=None):
    url = base.rstrip("/")+route+"?"+urllib.parse.urlencode({"session":sid})
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    req = urllib.request.Request(url,None if body is None else desk.encode(body).encode(),
                                 {"Authorization":"Bearer "+token,"Content-Type":"application/json"})
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
        if exc.errno in (errno.ENOENT,errno.EACCES,errno.EPERM):
            return True
        raise
    return False


def connect(canary):
    try:
        with socket.create_connection((canary["host"],canary["port"]),timeout=2):
            return True
    except OSError:
        return False


def worker(challenge):
    """Run inside the same namespace and identity as the rehearsal worker."""
    identity = challenge["identity"]
    base,sid,token = challenge["desk_url"],challenge["session"],challenge["token"]
    code, own = request(base,"/desk/next",sid,token)
    role = identity if identity in desk.SCOUTS else "boss"
    if code != 200 or own.get("session") != sid or own.get("role") != role or not own.get("wake_key"):
        raise ValueError("positive control: worker could not read its live rehearsal packet")
    forbidden = "/desk/notes" if role == "boss" else "/desk/pick"
    checks = {
        "desk_routes_only":all(request(base,r,sid,token)[0] == 404 for r in ("/status","/score","/desk/score")),
        "wrong_role_denied":request(base,forbidden,sid,token,{"wake_key":own["wake_key"]})[0] == 403,
        "sibling_token_denied":all(request(base,"/desk/next",s,token)[0] == 403 for s in challenge["siblings"]),
        "fixture_read_denied":all(denied_read(p) for p in challenge["fixtures"]),
        "sibling_journal_read_denied":all(denied_read(p) for p in challenge["journals"]),
        "scorer_state_denied":all(denied_read(p) for p in challenge["scorer"]),
        "outbound_denied":not connect(challenge["egress_canary"]),
    }
    ns = {name:os.readlink("/proc/self/ns/"+name) for name in ("mnt","net","user")}
    return dict(identity=identity,phase=challenge["phase"],challenge=challenge["challenge"],
                checks=checks,context=challenge["context"],sandbox=dict(uid=os.geteuid(),**ns))


def evaluate(transcript):
    """Validate the sampled observations, not the deployed boundary."""
    rows = transcript["observations"]
    identities = transcript["markers"]
    if set(identities) != IDENTITIES or len(set(identities.values())) != len(IDENTITIES):
        raise ValueError("probe requires every distinct TM07 worker identity")
    expected = {(i,p) for i in IDENTITIES for p in PHASES}
    if len(rows) != len(expected) or {(r["identity"],r["phase"]) for r in rows} != expected:
        raise ValueError("isolation probes are missing worker phases")
    if len({r["challenge"] for r in rows}) != len(rows):
        raise ValueError("worker probe observation replayed")
    sandbox = {phase:{} for phase in PHASES}
    for row in rows:
        identity,phase = row["identity"],row["phase"]
        checks,ctx,ns = row["checks"],row["context"],row["sandbox"]
        role = identity if identity in desk.SCOUTS else "boss"
        tools = {"next","status","usage","look","pick"} if role == "boss" else {"next","status","usage","notes"}
        if (set(checks) != CHECKS-{"fresh_context","role_only_handoff"} or any(v is not True for v in checks.values())
                or ctx.get("conversation_id","missing") is not None or ctx.get("memory_enabled") is not False
                or set(ctx.get("tools",[])) != tools
                or ctx.get("markers") != ([identities[identity]] if phase == "handoff" else [])):
            raise ValueError(f"isolation probes failed for {identity} ({phase})")
        if (set(ns) != {"uid","mnt","net","user"} or type(ns["uid"]) is not int
                or not all(isinstance(ns[k],str) and ns[k] for k in ("mnt","net","user"))):
            raise ValueError("isolation probes lack worker identity evidence")
        sandbox[phase][identity] = f'{ns["uid"]}:{ns["user"]}:{ns["mnt"]}'
    if any(len(set(group.values())) != len(IDENTITIES) or transcript["operator"] in group.values()
           for group in sandbox.values()):
        raise ValueError("worker identities share an OS boundary")
    return dict(version=VERSION,scope=SCOPE,root=transcript["root"],registration=transcript["registration"],
                launcher_digest=transcript["launcher_digest"],probe_transcript_digest=desk.digest(transcript),
                sandbox_identities=sandbox["fresh"],passed=sorted(CHECKS))


def launch_fingerprint(files):
    digests = {}
    for name in files:
        path = Path(name).resolve(strict=True)
        with path.open("rb") as f:
            hashing = sha256()
            for block in iter(lambda:f.read(65536),b""):
                hashing.update(block)
            digests[str(path)] = hashing.hexdigest()
    if not digests:
        raise ValueError("name all launcher and wrapper release files")
    return desk.digest(digests)


def collect(profile):
    entries = profile["workers"]
    root = str(Path(profile["root"]).resolve(strict=True))
    rehearsal = Path(profile["rehearsal_root"]).resolve(strict=True)
    if Path(root) == rehearsal or Path(root).is_relative_to(rehearsal) or rehearsal.is_relative_to(Path(root)):
        raise ValueError("rehearsal and registered roots must be separate")
    launch = profile["launcher"]
    release = profile["release_files"]
    if not Path(launch[0]).is_absolute() or launch[0] not in release or set(entries) != IDENTITIES:
        raise ValueError("name the absolute real launcher and all eight workers")
    if not connect(profile["egress_canary"]):
        raise ValueError("egress canary must be reachable from the operator namespace")
    declared = [e["session"] for e in entries.values()]
    if len(set(declared)) != 7:
        raise ValueError("probe expects two scout roles, sharing one scout session, and six boss sessions")
    if entries[desk.SCOUTS[0]]["session"] != entries[desk.SCOUTS[1]]["session"]:
        raise ValueError("probe scout roles must share the rehearsal scout session ID")
    for p in [v[k] for v in entries.values() for k in ("fixture","journal","token_file")] + profile["scorer_only"]:
        if not Path(p).resolve(strict=True).is_relative_to(rehearsal) or denied_read(p):
            raise ValueError("a probe file is unreadable even to the operator")
    if not profile["scorer_only"]:
        raise ValueError("name at least one readable scorer-only rehearsal canary")
    markers = {i:"tm07-probe-"+secrets.token_hex(20) for i in sorted(entries)}
    operator = ":".join([str(os.geteuid()),os.readlink("/proc/self/ns/user"),os.readlink("/proc/self/ns/mnt")])
    transcript = dict(root=root,registration=profile["registration"],launcher_digest=launch_fingerprint(release),operator=operator,
                      markers=markers,observations=[])
    for phase in PHASES:
        for i,e in sorted(entries.items()):
            foreign = [v for v in entries.values() if v["session"] != e["session"]]
            challenge = dict(identity=i,phase=phase,challenge=secrets.token_hex(16),marker=markers[i],
                             desk_url=profile["desk_url"],session=e["session"],token=json.loads(Path(e["token_file"]).read_text()),
                             siblings=sorted({v["session"] for v in foreign}),
                             fixtures=sorted({v["fixture"] for v in entries.values()}),
                             journals=sorted({v["journal"] for v in entries.values()}),
                             scorer=profile["scorer_only"]+[v["token_file"] for v in entries.values()],
                             egress_canary=profile["egress_canary"])
            proc = subprocess.run([*launch,i,phase],input=desk.encode(challenge),text=True,
                                  capture_output=True,timeout=35,check=False)
            if proc.returncode:
                raise ValueError(f"launcher probe failed for {i} ({phase})")
            row = json.loads(proc.stdout)
            if (set(row) != {"identity","phase","challenge","checks","context","sandbox"}
                    or any(row[k] != challenge[k] for k in ("identity","phase","challenge"))
                    or set(row["context"]) != {"conversation_id","memory_enabled","tools","markers"}
                    or any(v not in markers.values() for v in row["context"]["markers"])):
                raise ValueError("launcher did not return the matching challenge")
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
        put(ready,dict(workers=entries,scorer_only=[str(scorer)],rehearsal_root=str(root),
                       desk_url=f"http://127.0.0.1:{srv.server_address[1]}"))
        srv.serve_forever()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    action = p.add_subparsers(dest="action",required=True)
    action.add_parser("worker")
    c = action.add_parser("collect")
    for key in ("profile","transcript"):
        c.add_argument("--"+key,type=Path,required=True)
    r = action.add_parser("rehearse")
    r.add_argument("--rehearsal-root",type=Path,required=True)
    r.add_argument("--ready",type=Path,required=True)
    r.add_argument("--port",type=int,required=True)
    s = action.add_parser("seal")
    for key in ("transcript","key-file","receipt"):
        s.add_argument("--"+key,type=Path,required=True)
    args = p.parse_args()
    if args.action == "worker":
        print(desk.encode(worker(json.load(sys.stdin))))
    elif args.action == "rehearse":
        rehearse(args.rehearsal_root,args.ready,args.port)
    elif args.action == "collect":
        transcript = collect(json.loads(args.profile.read_text()))
        put(args.transcript,transcript)
        evaluate(transcript)
    else:
        proof = evaluate(json.loads(args.transcript.read_text()))
        key = args.key_file.read_text().strip()
        signature = desk.seal(key,"worker-boundary",proof)
        desk.validate_worker_boundary(key,proof,signature,proof["root"],launcher_digest=proof["launcher_digest"])
        put(args.receipt,dict(body=proof,seal=signature))


if __name__ == "__main__":
    main()
