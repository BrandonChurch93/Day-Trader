"""Plan 36: approval-pinned, private, no-return validation or one scored replay."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = Path("/home/user/workspace/rig/data")
INPUTS, OUTPUT = DATA / "plan36_inputs", DATA / "replay_36"
PLAN, PINS, APPROVAL = "PREREG_36_form4_cluster_buys.md", "PINNED_36.json", "APPROVAL_36.md"
NAMES = {PLAN,"INPUT_CONTRACT_36.md","calendar_36.json","common_36.py","score_36.py","test_36.py"}
FILES = {"roster.jsonl","identities.jsonl","bars.jsonl","quotes.jsonl","actions.json"}
LOCK, RESULT = "score_36.lock", "results_36.json"
COMMIT = r"[0-9a-f]{40}"
PIN = r"[0-9a-f]{64}"
MAX_DOC, MAX_LINE = 32*1024*1024, 1024*1024
APPROVAL_RE = (rf"Approved by the lead: plan 36, validation and one scored run, freeze commit ({COMMIT}), "
               rf"freeze SHA-256 ({PIN}), input SHA-256 ({PIN}), actions SHA-256 ({PIN})\.\n")


class Refused(Exception):
    pass


def need(condition, code):
    if not condition:
        raise Refused("P36_"+code)


def is_pin(p):
    return type(p) is str and re.fullmatch(PIN,p) is not None


def unique(pairs):
    obj = dict(pairs)
    need(len(obj)==len(pairs),"JSON_DUPLICATE")
    return obj


def reject_number(_):
    raise Refused("P36_JSON_NUMBER")


def parse(blob):
    return json.loads(blob.decode("utf-8"),object_pairs_hook=unique,parse_constant=reject_number)


def encode(obj):
    return (json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()


def private_dir(p):
    s = p.lstat()
    need(p.resolve()==p and stat.S_ISDIR(s.st_mode) and s.st_uid==os.geteuid()
         and stat.S_IMODE(s.st_mode)==0o700,"PRIVATE")


def secure_open(p, private):
    need(p.resolve()==p,"FILE")
    f = os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),"rb")
    try:
        s = os.fstat(f.fileno())
        need(stat.S_ISREG(s.st_mode) and (not private or (s.st_uid==os.geteuid() and s.st_nlink==1
             and s.st_mode&0o077==0)),"FILE")
        return f
    except BaseException:
        f.close()
        raise


def document(p, expected, private=False):
    with secure_open(p,private) as f:
        b = f.read(MAX_DOC+1)
    need(len(b)<=MAX_DOC and sha256(b).hexdigest()==expected,"PIN")
    return b


def stream(f, pin):
    """Second digest on the exact bytes parsed; no whole-file quote materialization."""
    h = sha256()
    while b := f.readline(MAX_LINE+1):
        need(len(b)<=MAX_LINE and b.strip(),"JSONL")
        h.update(b)
        yield parse(b)
    need(h.hexdigest()==pin,"PIN")


def verify_open(f, pin):
    h = sha256()
    while b := f.read(1024*1024):
        h.update(b)
    need(h.hexdigest()==pin,"PIN")
    f.seek(0)


def git(*args, optional=False):
    env = {"PATH":"/usr/bin:/bin","LC_ALL":"C","GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"/dev/null",
           "GIT_OPTIONAL_LOCKS":"0"}
    proc = subprocess.run(["/usr/bin/git","--no-replace-objects","-c","core.fsmonitor=false","-C",str(REPO),*args],
                          capture_output=True,env=env,timeout=20)
    need(optional or proc.returncode==0,"APPROVAL")
    return proc


def tree(commit,name):
    return git("show",f"{commit}:{name}").stdout


def authorize(approval, freeze_pin, input_pin, actions_pin):
    need(re.fullmatch(COMMIT,approval) is not None and all(map(is_pin,(freeze_pin,input_pin,actions_pin))),"APPROVAL")
    need(git("rev-parse","HEAD").stdout.strip()==approval.encode() and
         not git("status","--porcelain","--untracked-files=all").stdout,"APPROVAL")
    def src(commit,f):
        return tree(commit,"research_rig/"+f)
    match = re.fullmatch(APPROVAL_RE,src(approval,APPROVAL).decode("ascii"))
    need(match is not None,"APPROVAL")
    freeze,a,b,c = match.groups()
    need((a,b,c)==(freeze_pin,input_pin,actions_pin) and freeze!=approval and
         git("merge-base","--is-ancestor",freeze,approval,optional=True).returncode==0 and
         git("cat-file","-e",f"{freeze}:research_rig/{APPROVAL}",optional=True).returncode!=0,"APPROVAL")
    manifest = document(HERE/PINS,freeze_pin)
    need(manifest==src(freeze,PINS)==src(approval,PINS),"FREEZE")
    pins = parse(manifest)
    need(type(pins) is dict and set(pins)==NAMES and all(map(is_pin,pins.values())),"FREEZE")
    blobs = {f:document(HERE/f,pins[f]) for f in sorted(NAMES)}
    need(all(b==src(freeze,f)==src(approval,f) for f,b in blobs.items()),"FREEZE")
    need([x for x in blobs[PLAN].splitlines() if x.startswith(b"Status ")]==[b"Status FROZEN."],"FREEZE")
    for commit in (freeze,approval):
        ledger,queue = src(commit,"TRIAL_LEDGER.md"),tree(commit,"docs/QUEUE.md")
        need(re.search(rb"(?m)^\| 171 \|[^\n]+research_rig/"+re.escape(PLAN.encode())+rb"` \|",ledger),"LEDGER")
        need(re.search(rb"(?m)^\| 60 \|[^\n]+Plan 36[^\n]+171",queue),"QUEUE")
    return freeze,blobs


def engine(blobs):
    m = ModuleType("common_36")
    exec(compile(blobs["common_36.py"],str(HERE/"common_36.py"),"exec"),m.__dict__)
    return m


def unused(path):
    need(not any(os.path.lexists(path/name) for name in (LOCK,RESULT)),"CONSUMED")


def load_inputs(src,input_pin,actions_pin,C,clock):
    private_dir(src)
    need({f.name for f in src.iterdir()}==FILES|{"manifest.json"},"MANIFEST")
    m = parse(document(src/"manifest.json",input_pin,private=True))
    static = {"schema":1,"plan":36,"vendor":"Alpaca","feed":"sip","adjustment":"raw","frequency":"1Day",
              "filed_from":C.FIRST,"filed_through":C.LAST,"bar_from":C.BAR_FIRST}
    need(type(m) is dict and set(m)==set(static)|{"bar_through","collected_utc","files"} and
         all(type(m[k]) is type(v) and m[k]==v for k,v in static.items()),"MANIFEST")
    when, _ = C.stamp(m["collected_utc"])
    need(C.iso(m["bar_through"]).isoformat()==m["bar_through"] and
         when>=C.stamp(m["bar_through"]+"T23:59:59Z")[0],"MANIFEST")
    files = m["files"]
    need(type(files) is dict and set(files)==FILES and all(map(is_pin,files.values())),"MANIFEST")
    need(files["actions.json"]==actions_pin,"ACTION_PIN")
    with ExitStack() as stack:
        f = {name:stack.enter_context(secure_open(src/name,True)) for name in sorted(FILES)}
        for name,h in files.items():
            verify_open(f[name],h)
        a = f["actions.json"].read(MAX_DOC+1)
        need(len(a)<=MAX_DOC and sha256(a).hexdigest()==actions_pin,"ACTION_PIN")
        return C.load(m,parse(clock),*(stream(f[name],files[name]) for name in
                      ("roster.jsonl","identities.jsonl","bars.jsonl","quotes.jsonl")),parse(a))


def exclusive(path, data):
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def directory_sync(path):
    fd = os.open(path,os.O_DIRECTORY|os.O_RDONLY|os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def once(out, meta, data, evaluate):
    unused(out)
    job = meta|{"claimed_utc":datetime.now(timezone.utc).isoformat()}
    try:
        exclusive(out/LOCK,encode(job))
    except FileExistsError:
        raise Refused("P36_CONSUMED") from None
    directory_sync(out)
    result = evaluate(*data)
    exclusive(out/RESULT,encode({"job":job}|result))
    directory_sync(out)


def resources():
    with open("/proc/meminfo") as f:
        available = next(int(x.split()[1]) for x in f if x.startswith("MemAvailable:"))
    need(available>=1_572_864,"LOW_MEMORY")
    soft,hard = resource.getrlimit(resource.RLIMIT_AS)
    space = min(x for x in (292_968*1024,soft,hard) if x!=resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS,(space,hard))
    n = os.nice(0)
    if n<10:
        os.nice(10-n)


class Parser(argparse.ArgumentParser):
    def error(self,_):
        self.exit(2,"P36_ARGUMENTS\n")


def main():
    p = Parser(description=__doc__,allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs",action="store_true")
    mode.add_argument("--go",action="store_true")
    for a in ("approval-commit","freeze-sha256","input-sha256","actions-sha256"):
        p.add_argument("--"+a,required=True)
    args = p.parse_args()
    os.umask(0o077)
    C = None
    try:
        need(sys.flags.isolated and sys.flags.no_site and sys.flags.optimize==0 and sys.dont_write_bytecode and not
             any(k in {"TZ","PYTHONTZPATH"} or k.startswith(
                 ("P36_","PLAN36_","RIG_","GIT_","PYTHON","LD_")) for k in os.environ),"ENVIRONMENT")
        resources()
        freeze,pins = authorize(args.approval_commit,args.freeze_sha256,args.input_sha256,args.actions_sha256)
        C = engine(pins)
        if args.go:
            private_dir(OUTPUT)
            unused(OUTPUT)
        data = load_inputs(INPUTS,args.input_sha256,args.actions_sha256,C,pins["calendar_36.json"])
        if args.validate_inputs:
            print("P36_INPUTS_OK",json.dumps(C.assess(data),sort_keys=True))
            return
        once(OUTPUT,{"schema":1,"ledger":171,"queue":60,"freeze_commit":freeze,"approval_commit":args.approval_commit,
                     "freeze_sha256":args.freeze_sha256,"input_sha256":args.input_sha256,
                     "actions_sha256":args.actions_sha256},data,C.evaluate)
        print("P36_RESULT_WRITTEN")
    except Exception as exc:
        if isinstance(exc,Refused) or C is not None and isinstance(exc,C.Invalid):
            p.exit(2,f"{exc}\n")
        p.exit(2,"P36_REFUSED\n")


if __name__=="__main__":
    main()
