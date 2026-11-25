"""Checks one reader folder's answers.jsonl for draft plan 11, and collects a whole phase once every folder passes.
Reads no price.

  python3 check_11_answers.py FOLDER                 refuses (exit 1) on any fault; on a pass writes FOLDER/checked.jsonl
  python3 check_11_answers.py FOLDER --second-try    after one retry: each missing or bad answer becomes score 0 and is flagged
  python3 check_11_answers.py --collect PHASE        PHASE is design or heldback. Needs checked.jsonl in every folder.
                                                     Writes data/edgar_11/answers_11_<phase>_<reader>.jsonl and
                                                     research_rig/answers_11_<phase>_hashes.json, the file to commit and push.

A fault: a line that is not one JSON object with exactly event_id, input_sha256, score and reason; an event_id not in the
manifest, or given twice; an input_sha256 that differs from the manifest or from the SHA-256 of the stored prompt's text;
a score that is not a whole number from -2 to 2; a reason that is empty, longer than 200 characters or more than one line;
an event in the manifest with no answer; an instruction file that differs from research_rig/reader_instruction_11.txt; a
folder copy of a prompt that differs from the stored prompt (the last two are refused even on --second-try).
A reason that says the reader remembers the move: the score is set to 0 and remembered is stored and counted. A reason of
fewer than 4 words: stored as short_reason and counted. --collect refuses unless every expected reader, folder and event
is there."""
import sys, os, json, re, glob, datetime as dt
import common_11 as C

KEYS = {"event_id", "input_sha256", "score", "reason"}
ZERO_REASON = "no valid answer after two tries"

def prompt_hash(eid):
    b = open(os.path.join(C.EDGAR, "prompts", eid + ".txt"), "rb").read()
    head, sep, body = b.partition(b"========\n")
    return C.sha256_bytes(body) if sep else None

# A reason that says the reader remembers the move. A backstop for the instruction, which already tells the reader to give 0.
# "recall" alone is not enough: "product recall" is common in releases. A match with a negation in the three words before
# it ("I do not remember", "no memory of") is skipped.
REMEMBERS = re.compile(r"(?i)\b(remember(s|ed|ing)?|recollect(s|ed|ion)?|memory of|from memory|as I recall|already know(n)?"
                       r"|(I|we)\s+(can\s+|do\s+)?recall(ed)?|^recall|I\s+know\s+(how|what|that)\s+(it|the\s+stock|shares))\b")
NEGATION = re.compile(r"(?i)^(no|not|never|cannot|without|don't|dont|can't|cant|won't|didn't|doesn't|\w+n't)$")

def remembers(reason):
    for m in REMEMBERS.finditer(reason):
        before = re.findall(r"[\w']+", reason[:m.start()])[-3:]
        if not any(NEGATION.match(w.replace("\u2019", "'")) for w in before): return True
    return False

def phase_of(folder):
    """reading/<phase>/<reader>/bNNN: the phase is in the path, not in the manifest the reader can see."""
    return os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(folder))))

def check(folder, second_try=False):
    man = json.load(open(os.path.join(folder, "manifest.json"))); want = {e["event_id"]: e["input_sha256"] for e in man["events"]}
    faults, hard, flags, got, seen = [], [], [], {}, set()
    inst = C.sha256_file(os.path.join(folder, "INSTRUCTION.txt"))
    if not (inst == man["instruction_sha256"] == C.sha256_file(C.INSTRUCTION)): hard.append("instruction file differs from the frozen one")
    for eid, h in want.items():
        if prompt_hash(eid) != h: hard.append(f"{eid}: manifest hash differs from the stored prompt")
        fp = os.path.join(folder, "events", eid + ".txt")
        if not os.path.exists(fp) or open(fp, "rb").read() != open(os.path.join(C.EDGAR, "prompts", eid + ".txt"), "rb").read():
            hard.append(f"{eid}: the folder's copy differs from the stored prompt")
    p = os.path.join(folder, "answers.jsonl")
    lines = open(p, encoding="utf-8", newline="").read().split("\n") if os.path.exists(p) else []
    if not any(l.strip() for l in lines): faults.append("answers.jsonl is missing or empty")
    for n, line in enumerate(lines, 1):
        line = line[:-1] if line.endswith("\r") else line   # a Windows line end is allowed; a \r inside a reason is not
        if not line.strip(): continue
        try: a = json.loads(line)
        except Exception: faults.append(f"line {n}: not JSON"); continue
        if not isinstance(a, dict) or set(a) != KEYS: faults.append(f"line {n}: keys must be exactly {sorted(KEYS)}"); continue
        eid = a["event_id"]
        if eid not in want: faults.append(f"line {n}: event_id {eid!r} is not in the manifest"); continue
        bad = []
        if eid in seen: bad.append("event answered twice")
        seen.add(eid)
        if a["input_sha256"] != want[eid]: bad.append("wrong input_sha256")
        if type(a["score"]) is not int or not -2 <= a["score"] <= 2: bad.append("score must be a whole number from -2 to 2")
        r = a["reason"]
        if not isinstance(r, str) or not r.strip() or len(r) > 200 or "\n" in r or "\r" in r: bad.append("reason must be one line of 1 to 200 characters")
        if bad:
            faults += [f"line {n} ({eid}): {b}" for b in bad]
            if "event answered twice" in bad: got[eid] = None   # a second answer spoils the first, whichever was valid
            continue
        got[eid] = dict(a, remembered=remembers(r), short_reason=len(r.split()) < 4, score_given=a["score"])
        if got[eid]["remembered"]: got[eid]["score"] = 0; flags.append(f"{eid}: says it remembers, score set to 0")
        if got[eid]["short_reason"]: flags.append(f"{eid}: short reason")
    missing = [e for e in want if got.get(e) is None]
    faults += [f"{e}: no valid answer" for e in missing if e not in got]
    if hard: return False, hard + faults, flags
    if faults and not second_try: return False, faults, flags
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    out = []
    for e in man["events"]:
        a = got.get(e["event_id"]); zero = a is None
        if zero:
            a = dict(event_id=e["event_id"], input_sha256=e["input_sha256"], score=0, reason=ZERO_REASON, remembered=False, short_reason=False, score_given=None)
            flags.append(f"{e['event_id']}: set to 0 after two tries")
        out.append(dict(a, phase=phase_of(folder), reader=man["reader"], batch_id=man["batch_id"], second_try_zero=zero, checked_utc=now))
    with open(os.path.join(folder, "checked.jsonl"), "w") as f:
        for a in out: f.write(json.dumps(a, sort_keys=True) + "\n")
    return True, faults, flags

def expected_readers(phase):
    """Who must have answered what: design, all four readers on the design sample; held-back, the chosen set-up's readers
    on every held-back event, and for cascade the strong reader on exactly the disagreements and the audit."""
    RD = C.th("replay_11_readers"); U = C.load_usable()
    if phase == "design": return {r: set(U["design_sample"]) for r in RD["small_models"] + [RD["strong_model"]]}
    dp = os.path.join(C.OUTDIR, "results_11_design.json")
    if not os.path.exists(dp): sys.exit("refused: results_11_design.json does not exist")
    chosen = json.load(open(dp))["chosen_setup"]
    if chosen is None: sys.exit("refused: no set-up was chosen, so the held-back half is not read")
    hb = {k["event_id"] for k in U["events"] if k["half"] == "heldback"}
    want = {r: hb for r in (RD["small_models"] if chosen in ("middle", "cascade") else [chosen])}
    if chosen == "cascade":
        sp = os.path.join(C.READING, "heldback", "strong_reads.json")
        if not os.path.exists(sp): sys.exit("refused: strong_reads.json does not exist. Run prep_11.py heldback 2 first.")
        sr = json.load(open(sp)); want[RD["strong_model"]] = set(sr["disagreements"]) | set(sr["audit"])
    return want

def collect(phase):
    if phase not in ("design", "heldback"): sys.exit("refused: phase is design or heldback")
    root = os.path.join(C.READING, phase); want = expected_readers(phase)
    readers = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))) if os.path.isdir(root) else []
    if set(readers) != set(want): sys.exit(f"refused: readers on disk {readers} are not the expected {sorted(want)}")
    per = {}
    for r in readers:
        ep = os.path.join(root, r + ".expected.json")
        if not os.path.exists(ep): sys.exit(f"refused: {ep} is missing; folders must come from prep_11.py")
        X = json.load(open(ep)); on_disk = sorted(os.path.basename(f) for f in glob.glob(os.path.join(root, r, "b*")))
        if on_disk != sorted(X["batches"]): sys.exit(f"refused: {r} folders on disk {on_disk[:3]}... differ from the {len(X['batches'])} written")
        rows = []
        for b, ids in sorted(X["batches"].items()):
            cp = os.path.join(root, r, b, "checked.jsonl")
            if not os.path.exists(cp): sys.exit(f"refused: {r}/{b} not checked yet")
            got = [json.loads(l) for l in open(cp)]
            if sorted(a["event_id"] for a in got) != sorted(ids): sys.exit(f"refused: {r}/{b} checked answers do not match the events written")
            rows += got
        ids = [a["event_id"] for a in rows]
        if len(ids) != len(set(ids)): sys.exit(f"refused: {r} answers an event in two folders")
        if set(ids) != want[r]: sys.exit(f"refused: {r} answered {len(set(ids))} events, expected {len(want[r])}")
        per[r] = rows
    H = dict(phase=phase, made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
             instruction_sha256=C.sha256_file(C.INSTRUCTION), usable_file_sha256=C.sha256_file(os.path.join(C.EDGAR, "usable_11.json")), files={})
    for r, rows in sorted(per.items()):
        p = os.path.join(C.EDGAR, f"answers_11_{phase}_{r}.jsonl")
        with open(p, "w") as f:
            for a in sorted(rows, key=lambda a: a["event_id"]): f.write(json.dumps(a, sort_keys=True) + "\n")
        H["files"][os.path.basename(p)] = dict(sha256=C.sha256_file(p), answers=len(rows), set_to_zero=sum(a["second_try_zero"] for a in rows),
                                               remembered_set_to_zero=sum(a["remembered"] for a in rows), short_reason=sum(a["short_reason"] for a in rows))
    out = os.path.join(C.OUTDIR, f"answers_11_{phase}_hashes.json")
    json.dump(H, open(out, "w"), indent=1); open(out, "a").write("\n")
    print(json.dumps(H, indent=1)); print(f"commit and push {os.path.relpath(out, os.path.dirname(C.HERE))} before score_11.py will run")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--collect"] and len(a) == 2: collect(a[1]); sys.exit(0)
    if not a: print(__doc__); sys.exit(2)
    ok, faults, flags = check(a[0], "--second-try" in a)
    print(json.dumps(dict(folder=a[0], ok=ok, faults=faults[:40], fault_count=len(faults), flags=flags), indent=1))
    sys.exit(0 if ok else 1)
