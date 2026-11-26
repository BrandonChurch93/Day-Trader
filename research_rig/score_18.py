"""Plan 18 draft. Only the owner may use the sealed run mode after re-audit."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import unittest

from . import archive_18 as A, common_18 as C

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent/"rig/data"
RUN = DATA/"replay_18"
DRAFT = "research_rig/PREREG_18_funding_carry_DRAFT.md"
PLAN = "research_rig/PREREG_18_funding_carry.md"
CONFIG = "config/thresholds.yaml"
CODE = tuple(f"research_rig/{n}_18.py" for n in ("archive","common","score","test"))
OUTPUT = "research_rig/results_18.json"
ENV_OVERRIDES = ("REPLAY_18_DATA","REPLAY_18_LOCK_DIR","RESULTS_18_DIR","REPLAY_18_ARCHIVE",
                 "GIT_DIR","GIT_WORK_TREE","GIT_INDEX_FILE","GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES","GIT_CONFIG_COUNT","GIT_CONFIG_PARAMETERS")
PATHS = {"universe":RUN/"universe_18.json","ranks":DATA/"replay_13/snapshots.json",
         "viewed_manifest":DATA/"replay_16/manifest_futures.json",
         "held_manifest":DATA/"replay_16/manifest_futures_held.json",
         **{v:DATA.parent/"ideas"/f"shortable_{v}_us_perps.json" for v in A.VENUES}}


def git(*args, check=True):
    return subprocess.run(["git",*args],cwd=ROOT,check=check,capture_output=True)


def verify_review(seal,directory):
    inventory = seal.get("evidence_inventory_sha256")
    reviews = seal.get("review_attestations")
    if (not isinstance(inventory,str) or not A.SHA.fullmatch(inventory)
        or not isinstance(reviews,list) or len(reviews)!=2 or len(set(reviews))!=2
        or not all(isinstance(sha,str) and A.SHA.fullmatch(sha) for sha in reviews)):
        raise C.Incomplete("two distinct pinned pre-freeze reviews are required")
    reviewers = set()
    for sha in reviews:
        r = json.loads(A.read_pinned(directory/sha,sha))
        if (r.get("version")!=1 or r.get("approval")!="approved_for_freeze"
            or r.get("universe_sha256")!=seal["inputs"]["universe"]
            or r.get("evidence_inventory_sha256")!=inventory
            or r.get("code")!={k:seal["repo"][k] for k in CODE}
            or r.get("config_sha256")!=seal["repo"][CONFIG]
            or not isinstance(r.get("reviewer"),str) or not r["reviewer"].strip()
            or not isinstance(r.get("remaining_limitations"),list) or not r["remaining_limitations"]
            or not all(isinstance(x,str) and x.strip() for x in r["remaining_limitations"])
            or type(r.get("reviewed_at")) is not int or type(seal.get("frozen_at")) is not int
            or not 0<r["reviewed_at"]<seal["frozen_at"]):
            raise C.Incomplete("review is not bound to the exact pre-freeze inputs and code")
        reviewers.add(r["reviewer"].strip().casefold())
    if len(reviewers)!=2:
        raise C.Incomplete("two distinct reviewers are required")


def verify(expected):
    if any(os.getenv(k) is not None for k in ENV_OVERRIDES):
        raise C.Incomplete("refused while an input or git override is set")
    if os.path.lexists(ROOT/DRAFT) or not (ROOT/PLAN).is_file():
        raise C.Incomplete("Plan 18 is still a draft")
    if os.path.lexists(ROOT/"research_rig/score_18.lock"):
        raise C.Incomplete("a local Plan 18 lock already exists")
    if RUN.is_symlink() or RUN.stat().st_uid!=os.geteuid() or RUN.stat().st_mode&0o022:
        raise C.Incomplete("the owner-controlled run folder must not be group/world writable")
    try:
        seal = json.loads(A.read_pinned(RUN/"freeze_18.json",expected))
    except OSError as exc:
        raise C.Incomplete("missing owner freeze seal") from exc
    upstream = git("ls-remote","--exit-code","origin","refs/heads/main").stdout.split()[0].decode()
    commit = seal["commit"]
    if (seal["version"]!=1 or not re.fullmatch(r"[0-9a-f]{40}",commit)
        or upstream!=git("rev-parse","origin/main").stdout.decode().strip()
        or git("merge-base","--is-ancestor",commit,upstream,check=False).returncode):
        raise C.Incomplete("seal must name a frozen ancestor of current origin/main; fetch first")
    for artifact in (OUTPUT,"research_rig/score_18.lock"):
        if git("cat-file","-e",f"{upstream}:{artifact}",check=False).returncode==0:
            raise C.Incomplete("origin/main already has a Plan 18 lock or result")
    if git("cat-file","-e",f"{commit}:{DRAFT}",check=False).returncode==0:
        raise C.Incomplete("the sealed commit still has the draft")
    if set(seal["repo"])!={PLAN,CONFIG,*CODE} or set(seal["inputs"])!=set(PATHS):
        raise C.Incomplete("incomplete freeze bindings")
    actual = {}
    for path,pin in seal["repo"].items():
        raw = A.read_pinned(ROOT/path,pin)
        if any(git("show",f"{ref}:{path}").stdout != raw for ref in (commit,upstream)):
            raise C.Incomplete(f"sealed file differs from origin/main: {path}")
        actual[path] = raw
    if not re.search(rb"(?m)^Status FROZEN\.$",actual[PLAN]):
        raise C.Incomplete("final plan lacks freeze declaration")
    if any(not A.SHA.fullmatch(x) for x in seal["inputs"].values()):
        raise C.Incomplete("invalid input pins")
    if any(seal["inputs"][v]!=d for v,d in A.ROSTER_HASHES.items()):
        raise C.Incomplete("frozen US rosters must match the documented fingerprints")
    verify_review(seal,RUN/"reviews")
    require_staged_ftt(seal)
    return seal,C.policy(actual[CONFIG])


def require_staged_ftt(seal):
    """Check only filenames and sizes before the lock; verify ZIP digests after it."""
    u = json.loads(A.read_pinned(PATHS["universe"],seal["inputs"]["universe"]))
    contracts,symbols,_ = A.catalogue(u)
    supplement = A.ftt_manifest(u,contracts,symbols)
    if supplement:
        for name in supplement["archives"]:
            path = RUN/"ftt_archives"/name
            if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=A.MAX_ZIP_BYTES:
                raise C.Incomplete(f"stage the pinned FTT ZIP without opening the rows: {name}")


def sync_directory(path):
    fd = os.open(path,os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_json(stream,record):
    json.dump(record,stream,sort_keys=True,allow_nan=False)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())


def one_shot(lock,output,authorize,score):
    """authorize reads seal/repo metadata; score is the first scoring-data callback."""
    if os.path.lexists(lock) or os.path.lexists(output):
        raise C.Incomplete("the Plan 18 one-shot is consumed")
    binding = authorize()
    try:
        fd = os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as exc:
        raise C.Incomplete("another process claimed the one-shot") from exc
    with os.fdopen(fd,"w") as claim:
        write_json(claim,dict(status="consumed",utc=datetime.now(timezone.utc).isoformat(),
                              seal=binding[0]))
        sync_directory(lock.parent)
        try:
            if os.path.lexists(output):
                raise C.Incomplete("output appeared after the claim")
            result = score(binding)
            with output.open("x") as stream:
                write_json(stream,result)
            sync_directory(output.parent)
        except BaseException as exc:
            write_json(claim,dict(status="failed",error=type(exc).__name__,detail=str(exc)))
            raise
        write_json(claim,dict(status="completed",output=output.name))
    return result


def memory_check():
    with open("/proc/meminfo",encoding="ascii") as f:
        field = next(line for line in f if line.startswith("MemAvailable:"))
    if int(field.split()[1]) < 1572864:
        raise C.Incomplete("available system memory is below 1.5 GiB")


def real_resources():
    memory_check()
    soft,hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(v for v in (A.MEMORY_CAP,soft,hard) if v!=resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS,(cap,hard))
    current = os.nice(0)
    if current<10:
        os.nice(10-current)


def score(binding):
    seal,p = binding
    tape,snaps,rosters,coverage = A.load(PATHS,seal["inputs"],DATA/"replay_16/archives",p,
                                        evidence_dir=RUN/"evidence",
                                        supplemental_dir=RUN/"ftt_archives",
                                        inventory_pin=seal["evidence_inventory_sha256"],check=memory_check)
    pool = {}

    def measure(bps=None,roster=None,gross=False):
        memory_check()
        try:
            return C.run_book(tape,snaps,p["start"],p["end"],bps,roster=roster,p=p,
                              pools=pool if roster is None else None,gross_reopen=gross),None
        except C.Incomplete as exc:
            return None,str(exc)

    def pack(pair):
        result,refusal = pair
        result = (asdict(result)|{"forced_count":len(result.forced),
                                  "cash_slots":result.too_few+result.no_open}) if result else None
        return dict(result=result,refusal=refusal)

    ranks = measure()
    draws = C.random_books(tape,snaps,p["start"],p["end"],p=p,pools=pool,check=memory_check)
    costs = (*p["shown_cost_bps"],p["judged_cost_bps"])
    return dict(ledger=153,ledger_shown=154,frozen_commit=seal["commit"],scope=coverage,judged=pack(ranks),
                shown_costs={str(bps):pack(measure(bps)) for bps in p["shown_cost_bps"]},
                shown_gross_reopen=pack(measure(gross=True)),
                shown_rosters={v:{str(bps):pack(measure(bps,ids)) for bps in costs}
                               for v,ids in rosters.items()},
                random=C.random_summary(draws,ranks[0],p))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--selftest",action="store_true")
    actions.add_argument("--run",action="store_true")
    parser.add_argument("--seal-sha256")
    args = parser.parse_args()
    if args.selftest:
        if args.seal_sha256 is not None:
            parser.error("the self-test accepts no seal")
        from . import test_18
        tests = unittest.defaultTestLoader.loadTestsFromModule(test_18)
        if not unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful():
            return 1
        test_18.power()
    else:
        if not args.seal_sha256 or not A.SHA.fullmatch(args.seal_sha256):
            parser.error("the owner must supply the trusted full seal digest")
        try:
            real_resources()
            one_shot(RUN/"score_18.lock",ROOT/OUTPUT,lambda:verify(args.seal_sha256),score)
        except (C.Incomplete,OSError,ValueError,KeyError,subprocess.CalledProcessError) as exc:
            parser.exit(1,f"Plan 18 refused: {exc}\n")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
