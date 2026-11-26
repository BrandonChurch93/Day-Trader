"""TM07 operator steps that come after the registration package and before any worker. Ledger 198.

Run from a root-owned copy of this file, as the service account `tm07desk`, with the interpreter
pinned in the package (`/usr/bin/python3.14 -B`, PYTHONNOUSERSITE=1, no PYTHONPATH). It imports
the engine only from the root-owned release named by --release, which must be the git archive of
ENGINE. Standard library only.

It prints names, counts and SHA-256 digests only. Prices, marks, fills and ranking inputs stay in
memory or in files under the private TM07 directories (mode 0600, owner tm07desk). No arm, twin,
yardstick or rule arm is replayed and no return is computed here.

    build    --release R --snapshot SNAP --weeks-json J --out SUMMARY
             For every scored week: rebuild the registered selection inputs from the snapshot, check
             them against the registered digests in J, build the price-only fixture with
             desk.prepare_week, and record its digest and funding hash. Fixtures are not kept; they
             are rebuilt and checked against the digest when a session is created.
    sign     --release R --summary SUMMARY --key KEY --study-root ROOT --out REGISTRATION
             Write and seal the registration body, then load it with score_tm07.Registration.
    create   --release R --snapshot SNAP --registration REG --key KEY --week W --arm scout|A|B|C
             [--boss B] [--scout-export FILE] --bearers-out FILE
             Rebuild that week's fixture, check its digest, and create one registered session in
             the study root. The role bearers go to FILE (0600) and nowhere else.
    export   --release R --registration REG --key KEY --week W --out FILE
             Export and bind the sealed neutral scout stream for that week.

The fixture config is tm06.full_config() as stored, except that tm_weights_twin_draws and
tm_weights_twin_seed are written as integers (same values). The thresholds file stores them as
1000.0 and 1.0. score_tm07.score_week refuses a non-integer twin count, and every TM06 scorer
casts both to int before use.
"""
import argparse, hashlib, json, os, sqlite3, stat, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ENGINE = "058a54320c2bc13043761633d828c1b2a78fbb82"
SNAPSHOT_SHA256 = "6346be0d4a10976a3531f2f2c70dd99132bfad331c47564366e0e6f4c2e486eb"
RUNNER_ID = "tm07_desk_v1"
LEDGER_REF = "research_rig/TRIAL_LEDGER.md row 198; timemachine/TM07_REGISTRATION.md"
BUILDS = {"claude_fable_5_2": {"id": "claude_fable_5_2", "first_after_cutoff": "2026-07-01"},
          "claude_opus_5_5": {"id": "claude_opus_5_5", "first_after_cutoff": "2026-07-01"},
          "gemini_neon": {"id": "gemini_neon", "first_after_cutoff": "2026-04-01"}}
BUILD_NOTE = "platform model ID as passed by the lead; the serving build behind the ID is UNKNOWN"
SHORT = {"claude_fable_5_2": "fable", "claude_opus_5_5": "opus"}
UTC = timezone.utc
DAY, WEEK = 86400, 7 * 86400


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def plain_digest(x):
    """The digest used by tools/build_tm07_registration.py for its recorded inputs."""
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def engine(release):
    release = Path(release).resolve(strict=True)
    info = release.stat()
    if info.st_uid != 0 or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        sys.exit("refused: release must be root-owned and not group or world writable")
    sys.path.insert(0, str(release))
    from timemachine import desk, score_tm07 as S, tm06
    from timemachine.tape import Tape
    for mod in (desk, S, tm06):
        if not Path(mod.__file__).resolve().is_relative_to(release):
            sys.exit("refused: engine imported from outside the release")
    return desk, S, tm06, Tape


def private_out(path):
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(fd, "w")


def ts(day):
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())


def neutral_id(week):
    return f"TM07-N-{week}"


def session_id(week, arm, boss=None):
    return neutral_id(week) if arm == "scout" else f"TM07-{week}-{SHORT[boss]}-{arm}"


def selection_item(con, S, week):
    """Same reads as tools/build_tm07_registration.py week_item; kept in memory only."""
    start = ts(date.fromisoformat(week))
    watch = sorted(S.WATCH)
    counts = dict.fromkeys(watch, 0)
    for sym, n in con.execute("SELECT symbol, COUNT(*) FROM bars WHERE tf='1Min' AND t>=? AND t<? GROUP BY symbol",
                              (start, start + WEEK)):
        if sym in counts:
            counts[sym] = n
    closes = lambda t: {s: c for s, c in con.execute("SELECT symbol, c FROM bars WHERE tf='1Day' AND t=?", (t,)) if s in counts}
    last, before = closes(start - DAY), closes(start - 8 * DAY)
    fund = con.execute("SELECT symbol, venue, t, rate, interval_hours FROM funding WHERE t>=? AND t<=? ORDER BY symbol, venue, t",
                       (start - 8 * 3600, start + WEEK)).fetchall()
    prior = (date.fromisoformat(week) - timedelta(days=7)).isoformat()
    item = dict(minute_counts=counts, last_known_on=week, before_known_on=prior, before=before, last=last)
    return item, fund


def fixture_cfg(tm06):
    cfg = tm06.full_config()
    for k in ("tm_weights_twin_draws", "tm_weights_twin_seed"):
        v = cfg[k]
        if int(v) != v:
            raise ValueError(f"{k} is not a whole number")
        cfg[k] = int(v)
    return cfg


def build_fixture(desk, tm06, Tape, snapshot, week, symbols):
    tape = Tape(snapshot, readonly=True)
    try:
        end = (date.fromisoformat(week) + timedelta(days=7)).isoformat()
        spec = desk.prepare_week(tape, fixture_cfg(tm06), week + "T00:00:00Z", end + "T00:00:00Z", list(symbols), {},
                                 runner_id=RUNNER_ID)
    finally:
        tape.close()
    return json.loads(desk.encode(spec))


def check_snapshot(snapshot):
    if sha_file(snapshot) != SNAPSHOT_SHA256:
        sys.exit("refused: snapshot hash differs from the custody record")


def cmd_build(a):
    desk, S, tm06, Tape = engine(a.release)
    check_snapshot(a.snapshot)
    registered = json.loads(Path(a.weeks_json).read_text())
    if registered["engine_commit"] != ENGINE or registered["snapshot_sha256"] != SNAPSHOT_SHA256:
        sys.exit("refused: weeks file is for another engine or snapshot")
    screen = S.screen_config()
    if registered["screen_hash"] != desk.digest(screen) or registered["cost_hash"] != S.canonical_cost_hash():
        sys.exit("refused: screen or cost hash differs from the weeks file")
    con = sqlite3.connect(f"file:{a.snapshot}?mode=ro", uri=True)
    out = dict(engine=ENGINE, snapshot_sha256=SNAPSHOT_SHA256, weeks_json_sha256=sha_file(a.weeks_json),
               runner_id=RUNNER_ID, weeks={})
    for week in S.WEEKS:
        reg = registered["weeks"][week]
        item, fund = selection_item(con, S, week)
        if plain_digest({k: item[k] for k in ("minute_counts", "before", "last", "last_known_on", "before_known_on")}) != reg["selection_inputs_sha256"]:
            sys.exit(f"refused: {week} selection inputs differ from the registered digest")
        if plain_digest(fund) != reg["funding_rows_sha256"]:
            sys.exit(f"refused: {week} funding rows differ from the registered digest")
        symbols, displaced = S.week_selection(week, item, screen)
        if symbols != reg["five"] or displaced != reg["displaced"]:
            sys.exit(f"refused: {week} selection differs from the registered weeks file")
        spec = build_fixture(desk, tm06, Tape, a.snapshot, week, symbols)
        if spec["symbols"] != symbols or len(spec["wakes"]) != 168:
            sys.exit(f"refused: {week} fixture shape")
        out["weeks"][week] = dict(item, symbols=symbols, displaced=displaced, neutral_id=neutral_id(week),
                                  fixture=desk.digest(spec), funding_hash=S.funding_profile_hash(spec["params"]),
                                  funding_ref=f"snapshot sha256 {SNAPSHOT_SHA256}, funding table, venue per tm_fast_funding_venue")
        print(week, " ".join(s.split("/")[0] for s in symbols), "fixture", out["weeks"][week]["fixture"][:12],
              "funding", out["weeks"][week]["funding_hash"][:12], flush=True)
    con.close()
    with private_out(a.out) as f:
        f.write(json.dumps(out, sort_keys=True))
    print("summary written; weeks", len(out["weeks"]))


def cmd_sign(a):
    desk, S, tm06, Tape = engine(a.release)
    summary = json.loads(Path(a.summary).read_text())
    key = Path(a.key).read_text().strip()
    root = Path(a.study_root)
    if root.resolve() != root or not root.is_absolute():
        sys.exit("refused: study root must be absolute and canonical")
    body = dict(version="TM07-CFM-v1", runner_id=RUNNER_ID, ledger_ref=LEDGER_REF, study_root=str(root),
                cost_hash=S.canonical_cost_hash(), screen_hash=desk.digest(S.screen_config()),
                builds={k: dict(v, note=BUILD_NOTE) for k, v in BUILDS.items()},
                engine=ENGINE, snapshot_sha256=SNAPSHOT_SHA256, weeks_json_sha256=summary["weeks_json_sha256"],
                weeks=summary["weeks"])
    body = json.loads(desk.encode(body))
    doc = dict(body=body, seal=desk.seal(key, "registration", body))
    reg = S.Registration(doc, key)
    with private_out(a.out) as f:
        f.write(desk.encode(doc))
    print("registration body sha256", reg.hash)


def load_reg(S, a):
    key = Path(a.key).read_text().strip()
    doc = json.loads(Path(a.registration).read_text())
    return key, doc, S.Registration(doc, key)


def cmd_create(a):
    desk, S, tm06, Tape = engine(a.release)
    check_snapshot(a.snapshot)
    key, doc, reg = load_reg(S, a)
    item = reg.weeks[a.week]
    if a.week not in S.WEEKS:
        sys.exit("refused: not a scored week")
    if (a.arm == "scout") != (a.boss is None) or (a.arm in ("B", "C")) != (a.scout_export is not None):
        sys.exit("refused: scout takes no boss; B and C need the sealed scout export")
    spec = build_fixture(desk, tm06, Tape, a.snapshot, a.week, item["symbols"])
    if desk.digest(spec) != item["fixture"] or S.funding_profile_hash(spec["params"]) != item["funding_hash"]:
        sys.exit("refused: rebuilt fixture differs from the registered digest")
    scout = None
    if a.scout_export:
        scout = json.loads(Path(a.scout_export).read_text())
        reg.verify_neutral(a.week, scout["neutral_id"], desk.digest(scout))
    sid = session_id(a.week, a.arm, a.boss)
    tokens = desk.issue_role_tokens(a.arm)
    build = doc["body"]["builds"]["gemini_neon" if a.arm == "scout" else a.boss]
    with private_out(a.bearers_out) as f:
        f.write(json.dumps(dict(session=sid, arm=a.arm, boss=a.boss, model=build["id"], bearers=tokens), sort_keys=True))
    desk.create_desk(reg.root / sid, spec, a.arm, a.boss, tokens, scout, approval_key=key, registration=doc, model_build=build["id"])
    print("created", sid, "arm", a.arm, "model", build["id"], "roles", " ".join(sorted(tokens)))


def cmd_export(a):
    desk, S, tm06, Tape = engine(a.release)
    key, doc, reg = load_reg(S, a)
    sess = desk.DeskSession(reg.root / neutral_id(a.week))
    result = sess.export_scout(key)
    with private_out(a.out) as f:
        f.write(desk.encode(result))
    print("exported", result["neutral_id"], "wakes", len(result["wakes"]), "sha256", desk.digest(result))


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = cli.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--release", required=True); b.add_argument("--snapshot", required=True)
    b.add_argument("--weeks-json", required=True); b.add_argument("--out", required=True)
    s = sub.add_parser("sign"); s.add_argument("--release", required=True); s.add_argument("--summary", required=True)
    s.add_argument("--key", required=True); s.add_argument("--study-root", required=True); s.add_argument("--out", required=True)
    c = sub.add_parser("create")
    for k in ("--release", "--snapshot", "--registration", "--key", "--week", "--bearers-out"):
        c.add_argument(k, required=True)
    c.add_argument("--arm", required=True, choices=("scout", "A", "B", "C"))
    c.add_argument("--boss", choices=tuple(SHORT)); c.add_argument("--scout-export")
    e = sub.add_parser("export")
    for k in ("--release", "--registration", "--key", "--week", "--out"):
        e.add_argument(k, required=True)
    a = cli.parse_args()
    if os.environ.get("PYTHONPATH") or os.environ.get("PYTHONHOME"):
        sys.exit("refused: unset PYTHONPATH and PYTHONHOME")
    dict(build=cmd_build, sign=cmd_sign, create=cmd_create, export=cmd_export)[a.cmd](a)


if __name__ == "__main__":
    main()
