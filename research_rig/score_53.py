"""Plan 53: synthetic calibration, silent validation, or one locked score from an approved, pinned packet."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import io
import json
import math
import os
from pathlib import Path
import re
import resource
import stat
import statistics
import subprocess
import sys
from types import ModuleType
from zoneinfo import reset_tzpath

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = Path("/home/user/workspace/rig/data")
INPUTS, RUN = DATA / "plan53_inputs", DATA / "replay_53"
PLAN = "research_rig/PREREG_53_taxable_cef_tax_loss.md"
PINS = "research_rig/PINNED_53.json"
APPROVAL = "research_rig/APPROVAL_53.md"
CALENDAR = "research_rig/calendar_25.json"
ENGINE = "research_rig/common_48.py"
CALIBRATION = "research_rig/CALIBRATION_53.json"
CONFIG = "config/thresholds.yaml"
PIN_NAMES = {PLAN, CALENDAR, ENGINE, CALIBRATION, CONFIG, "research_rig/score_53.py", "research_rig/test_53.py"}
ROSTER_PIN = "packet:roster.csv"  # off-repo point-in-time roster, pinned at freeze
EXCLUSIONS = "roster_exclusions.csv"
EXCLUSIONS_PIN = "packet:" + EXCLUSIONS
CASH_COVERAGE = "cash_coverage.csv"
COMPARISON = "replay48_portfolio_turns.json"
LEDGER_ROW, QUEUE_ROW = 187, 90
CAP = 64 * 1024 * 1024
CONFIG_KEYS = {"first_turn", "last_turn", "turns", "capital", "sleeve_usd", "picks", "formation_from_end",
               "entry_from_end", "shown_exit_session", "benchmark", "split_check_ratio", "cost", "marks", "calibration", "resources"}
APPROVAL_RE = (rb"Approved by the lead: plan 53, validation and one scored run, freeze commit ([0-9a-f]{40}), "
               rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64}), "
               rb"roster SHA-256 ([0-9a-f]{64}), distributions SHA-256 ([0-9a-f]{64})\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P53_" + code)


def is_pin(v):
    return type(v) is str and re.fullmatch(r"[0-9a-f]{64}", v) is not None


def pinned(path, pin, private=False):
    need(is_pin(pin), "PIN")
    need(path.resolve() == path, "FILE")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_size <= CAP, "FILE")
        if private:
            need(st.st_uid == os.geteuid() and stat.S_IMODE(st.st_mode) == 0o600, "PRIVATE")
        blob = f.read(CAP + 1)
    need(len(blob) <= CAP and sha256(blob).hexdigest() == pin, "PIN")
    return blob


def unique(pairs):
    obj = dict(pairs)
    need(len(obj) == len(pairs), "JSON_DUPLICATE")
    return obj


def reject_number(_):
    raise Refused("P53_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number, parse_float=Decimal)


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def private_dir(path):
    st = path.lstat()
    need(path.resolve() == path and stat.S_ISDIR(st.st_mode) and st.st_uid == os.geteuid()
         and stat.S_IMODE(st.st_mode) == 0o700, "PRIVATE")


def resources(cfg):
    r = cfg["resources"]
    with open("/proc/meminfo") as stream:
        available = next(int(s.split()[1]) for s in stream if s.startswith("MemAvailable:"))
    need(available >= r["minimum_free_mib"] * 1024, "LOW_MEMORY")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(x for x in (r["process_cap_mib"] * 1024 * 1024, soft, hard) if x != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    priority = os.nice(0)
    if priority < r["nice"]:
        os.nice(r["nice"] - priority)


def git(*args, allow=False):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                           "-c", "safe.directory=*", "-C", str(REPO), *args], capture_output=True, env=env,
                          timeout=15)
    need(allow or proc.returncode == 0, "APPROVAL")
    return proc


def authorize(approval, freeze_pin, input_pin, roster_pin, dist_pin):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(all(map(is_pin, (freeze_pin, input_pin, roster_pin, dist_pin))), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:{name}").stdout

    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, *named = (x.decode("ascii") for x in body.groups())
    parent = git("rev-list", "--parents", "-n", "1", approval).stdout.split()[1:]
    need(tuple(named) == (freeze_pin, input_pin, roster_pin, dist_pin) and len(parent) == 1, "APPROVAL")
    # The approval sits directly on the freeze, so every pinned file (including the whole config) is the frozen one.
    need(parent[0].decode() == freeze, "APPROVAL")
    need(git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", approval).stdout
         == f"A\t{APPROVAL}\n".encode(), "APPROVAL")
    need(git("cat-file", "-e", f"{freeze}:{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = pinned(REPO / PINS, freeze_pin)
    need(manifest == contents(freeze, PINS) == contents(approval, PINS), "FREEZE")
    pins = parse(manifest)
    need(type(pins) is dict and set(pins) == PIN_NAMES | {ROSTER_PIN, EXCLUSIONS_PIN} and all(map(is_pin, pins.values()))
         and pins[ROSTER_PIN] == roster_pin, "FREEZE")
    blobs = {name: pinned(REPO / name, pins[name]) for name in PIN_NAMES}
    need(all(b == contents(freeze, name) == contents(approval, name) for name, b in blobs.items()), "FREEZE")
    attested = read_config(blobs[CONFIG])["roster_attestation"]
    need((pins[ROSTER_PIN], pins[EXCLUSIONS_PIN]) == (attested["roster_sha256"], attested["exclusions_sha256"]),
         "FREEZE_ROSTER")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."], "FREEZE")
    link = b"`" + PLAN.encode() + b"`"
    for name, row, code in (("research_rig/TRIAL_LEDGER.md", LEDGER_ROW, "LEDGER"),
                            ("docs/QUEUE.md", QUEUE_ROW, "QUEUE")):
        prefix = f"| {row} |".encode()
        a, b = ([line for line in contents(commit, name).splitlines() if line.startswith(prefix)]
                for commit in (freeze, approval))
        need(len(a) == 1 and a == b and link in a[0], code)
    return freeze, blobs, pins[EXCLUSIONS_PIN]


def load_engine(blob):
    reset_tzpath(("/usr/share/zoneinfo",))
    C = ModuleType("common_48_verified")
    exec(compile(blob, ENGINE, "exec"), C.__dict__)
    return C


def read_config(blob):
    # One JSON-flow YAML value, read without a third-party parser.
    def block(key):
        blocks = re.findall(rb"(?m)^" + key + rb":\n  value: (\{[^\n]+\})\n", blob)
        need(len(blocks) == 1, "CONFIG")
        return parse(blocks[0])

    scope = block(b"replay_53_plan")
    need(type(scope) is dict and set(scope) == {"base", "benchmark", "roster_cutoff", "holdings_trust_cik", "holdings_series",
                                               "holdings_forms", "municipal_name_terms", "split_query_tail_days",
                                               "roster_attestation"}
         and scope["base"] == "replay_48_plan" and type(scope["benchmark"]) is str
         and re.fullmatch(r"\d{2}-\d{2}", scope["roster_cutoff"]) is not None
         and re.fullmatch(r"\d{10}", scope["holdings_trust_cik"]) is not None
         and re.fullmatch(r"S\d{9}", scope["holdings_series"]) is not None
         and type(scope["split_query_tail_days"]) is int and scope["split_query_tail_days"] > 0
         and all(type(scope[k]) is list and scope[k]
                 and all(type(v) is str and v for v in scope[k])
                 and len(set(scope[k])) == len(scope[k]) for k in ("holdings_forms", "municipal_name_terms")), "CONFIG")
    cfg = block(b"replay_48_plan")
    need(type(cfg) is dict and set(cfg) == CONFIG_KEYS, "CONFIG")
    need(set(cfg["cost"]) == {"extra_bps", "proxy_half_bps", "window_start", "measure_start", "measure_end",
                              "expiry_seconds", "min_coverage_seconds"}
         and set(cfg["marks"]) == {"min_positive_years", "min_years_ahead_of_benchmark", "drop_best"}
         and set(cfg["calibration"]) == {"trials", "seed", "edges", "benchmark_sd", "group_beta",
                                         "group_residual_sd", "beta_only_premium", "loser_residual_sd",
                                         "null_ceiling"}
         and set(cfg["resources"]) == {"minimum_free_mib", "process_cap_mib", "nice"}, "CONFIG")
    attested = scope["roster_attestation"]
    need(type(attested) is dict and set(attested) == {"eligible_rows_by_turn", "roster_sha256", "exclusions_sha256"}
         and all(is_pin(attested[k]) for k in ("roster_sha256", "exclusions_sha256"))
         and type(attested["eligible_rows_by_turn"]) is list and len(attested["eligible_rows_by_turn"]) == cfg["turns"]
         and all(type(n) is int and n >= cfg["picks"] for n in attested["eligible_rows_by_turn"]), "CONFIG")
    return cfg | {k: v for k, v in scope.items() if k != "base"}


def check_calibration(C, cfg, blob):
    need(blob == encode(C.calibrate(cfg)), "CALIBRATION")


def input_names(cfg):
    years = range(cfg["first_turn"], cfg["last_turn"] + 1)
    return ({"roster.csv", EXCLUSIONS, "distributions.json", CASH_COVERAGE, COMPARISON, "split_evidence.json",
             "split_control.json"} | {f"bars_{y}.json" for y in years}
            | {f"quotes_{y}.json" for y in years})


def https(value):
    return type(value) is str and re.fullmatch(r"https://[^/\s]+/\S*", value) is not None


def csv_rows(blob, required, code, exact=False):
    rows = csv.DictReader(io.StringIO(blob.decode("utf-8"), newline=""), strict=True)
    fields = rows.fieldnames
    need(fields and len(fields) == len(set(fields)) and (required == set(fields) if exact else required <= set(fields)), code)
    out = list(rows)
    need(all(None not in row and all(v is not None for v in row.values()) for row in out), code)
    return out


def municipal_name(value, cfg):
    normalized = " " + " ".join(re.findall(r"[A-Z0-9]+", value.upper())) + " "
    return any(f" {term} " in normalized for term in cfg["municipal_name_terms"])


def roster_metadata(roster_blob, exclusions_blob, windows, C, cfg):
    base = C.roster(roster_blob, cfg)
    by_year = {str(w["turn"]): w for w in windows}
    snapshot_keys = ("series", "report_period", "public_date", "form", "filing_url")
    common = {"turn_year", "holding_id", "ticker", "cik", "holding_name", "identity_url"} | set(snapshot_keys)
    rows = csv_rows(roster_blob, common, "ROSTER_METADATA", exact=True)
    excluded = csv_rows(exclusions_blob, common | {"reason"}, "ROSTER_EXCLUSIONS", exact=True)
    ids = {y: set() for y in by_year}
    snapshots = {}
    admitted = set()
    trust = str(int(cfg["holdings_trust_cik"]))
    index_url = re.compile(rf"https://www\.sec\.gov/Archives/edgar/data/0*{trust}/"
                           r"([0-9]{10})([0-9]{2})([0-9]{6})/\1-\2-\3-index\.html?")
    for included, batch in ((True, rows), (False, excluded)):
        for r in batch:
            y = r["turn_year"]
            need(y in by_year and re.fullmatch(r"[1-9][0-9]*", r["holding_id"]) is not None
                 and r["holding_id"] not in ids[y] and bool(r["holding_name"].strip()), "ROSTER_METADATA")
            ids[y].add(r["holding_id"])
            snap = tuple(r[key] for key in snapshot_keys)
            need(snapshots.setdefault(y, snap) == snap and r["series"] == cfg["holdings_series"]
                 and r["form"] in cfg["holdings_forms"] and index_url.fullmatch(r["filing_url"]) is not None,
                 "ROSTER_SNAPSHOT")
            cutoff = C.day(f"{y}-{cfg['roster_cutoff']}")
            need(C.day(r["report_period"]) <= C.day(r["public_date"]) < cutoff, "ROSTER_CLOCK")
            named_muni = municipal_name(r["holding_name"], cfg)
            if included:
                need(not named_muni and re.fullmatch(r"\d{10}", r["cik"]) is not None
                     and https(r["identity_url"]) and (y, r["cik"]) not in admitted, "ROSTER_METADATA")
                admitted.add((y, r["cik"]))
            else:
                need(r["reason"] in {"municipal_name", "replay48_overlap", "not_listed_cef_common",
                                     "unresolved_identity", "duplicate_common"}
                     and (r["reason"] == "municipal_name") == named_muni
                     and (not r["cik"] or re.fullmatch(r"\d{10}", r["cik"]) is not None)
                     and (not r["ticker"] or C.TICKER.fullmatch(r["ticker"]) is not None)
                     and (not r["identity_url"] or https(r["identity_url"])), "ROSTER_EXCLUSIONS")
    need(all(positions == {str(i) for i in range(1, len(positions) + 1)} for positions in ids.values()),
         "ROSTER_HOLDINGS_IDS")
    return base, len(excluded)


def actions_and_coverage(raw, coverage_blob, windows, roster, C, cfg):
    # Strip provenance only after checking it; the immutable shared engine checks every date/amount/ratio.
    names = {w["turn"]: set(roster[w["turn"]]) | {cfg["benchmark"]} for w in windows}
    fields = {"turn_year", "ticker", "status", "source"}
    coverage = {}
    for r in csv_rows(coverage_blob, fields, "CASH_COVERAGE"):
        need(re.fullmatch(r"\d{4}", r["turn_year"]) is not None, "CASH_COVERAGE")
        y, s = int(r["turn_year"]), r["ticker"]
        need(y in names and s in names[y] and (y, s) not in coverage
             and r["status"] in {"documented", "none", "unresolved", "partial"} and https(r["source"]),
             "CASH_COVERAGE")
        coverage[y, s] = r["status"], r["source"]
    need(set(coverage) == {(y, s) for y, symbols in names.items() for s in symbols}, "CASH_COVERAGE")
    need(type(raw) is dict and set(raw) == {"schema", "turns"} and type(raw["turns"]) is dict
         and set(raw["turns"]) == {str(y) for y in names}, "CASH_COVERAGE")
    documented_events = 0
    gaps = {y: set() for y in names}
    for y, symbols in names.items():
        b = raw["turns"][str(y)]
        need(type(b) is dict and set(b) == {"symbols", "benchmark"} and type(b["symbols"]) is dict
             and set(b["symbols"]) == set(roster[y]), "CASH_COVERAGE")
        for s in symbols:
            is_benchmark = s == cfg["benchmark"]
            f = b["benchmark"] if is_benchmark else b["symbols"][s]
            status, source = coverage[y, s]
            need(type(f) is dict and set(f) == {"source", "cash", "splits"} and f["source"] == source
                 and all(type(f[k]) is list for k in ("cash", "splits")), "CASH_COVERAGE")
            need(bool(f["cash"]) == (status in {"documented", "partial"}), "CASH_COVERAGE")
            need(not is_benchmark or status in {"documented", "none"}, "BENCHMARK_CASH")
            if status in {"unresolved", "partial"}:
                gaps[y].add(s)
            documented_events += len(f["cash"])
            for kind in ("cash", "splits"):
                for event in f[kind]:
                    need(type(event) is dict and https(event.get("source"))
                         and type(event.get("source_kind")) is str
                         and event["source_kind"] in {"issuer_site", "issuer_wire", "sec", "exchange"},
                         "ACTION_SOURCE")
                    del event["source"], event["source_kind"]
    return C.distributions(raw, windows, roster, cfg), gaps, documented_events


def split_evidence(raw, windows, names, cash, C, cfg):
    # Preserve native pages. Only the projected query end is adapted to the shared engine's window check.
    need(type(raw) is dict and type(raw.get("queries")) is list, "SPLIT_EVIDENCE")
    exits = {w["turn"]: w["exit"] for w in windows}
    projected = []
    for q in raw["queries"]:
        need(type(q) is dict and type(q.get("turn")) is int and q["turn"] in exits, "SPLIT_EVIDENCE")
        exit_date = exits[q["turn"]]
        padded = exit_date + timedelta(days=cfg["split_query_tail_days"])
        need(q.get("end") == padded.isoformat(), "SPLIT_EVIDENCE_TAIL")
        projected.append(q | {"end": exit_date.isoformat()})
    C.split_evidence(raw | {"queries": projected}, windows, names, cash)


def load_inputs(input_dir, input_pin, roster_pin, dist_pin, exclusions_pin, C, calendar_blob, cfg):
    private_dir(input_dir)
    windows = C.turns(parse(calendar_blob), cfg)
    m = parse(pinned(input_dir / "manifest.json", input_pin, private=True))
    need(type(m) is dict and set(m) == {"schema", "mode", "feed", "adjustment", "first_turn", "last_turn",
                                       "collected_utc", "files"}
         and type(m["schema"]) is int and m["schema"] == 1 and m["mode"] == "plan53_raw_sip_v1"
         and m["feed"] == "sip" and m["adjustment"] == "raw" and m["first_turn"] == cfg["first_turn"]
         and m["last_turn"] == cfg["last_turn"], "MANIFEST")
    ts = m["collected_utc"]
    need(type(ts) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts) is not None
         and datetime.fromisoformat(ts.replace("Z", "+00:00")).date() > windows[-1]["exit"], "MANIFEST_CLOCK")
    names = input_names(cfg)
    need(type(m["files"]) is dict and set(m["files"]) == names and all(map(is_pin, m["files"].values()))
         and {p.name for p in input_dir.iterdir()} == names | {"manifest.json"}
         and m["files"]["roster.csv"] == roster_pin and m["files"]["distributions.json"] == dist_pin
         and m["files"][EXCLUSIONS] == exclusions_pin,
         "MANIFEST_FILES")
    roster, exclusions_count = roster_metadata(pinned(input_dir / "roster.csv", roster_pin, private=True),
                                                pinned(input_dir / EXCLUSIONS, exclusions_pin, private=True),
                                                windows, C, cfg)
    need([len(roster[w["turn"]]) for w in windows] == cfg["roster_attestation"]["eligible_rows_by_turn"],
         "ROSTER_COUNTS")
    cash, gaps, cash_events = actions_and_coverage(parse(pinned(input_dir / "distributions.json", dist_pin, private=True)),
                                                 pinned(input_dir / CASH_COVERAGE, m["files"][CASH_COVERAGE], private=True),
                                                 windows, roster, C, cfg)
    split_names = {y: (*members, cfg["benchmark"]) for y, members in roster.items()}
    split_cash = {y: (funds | {cfg["benchmark"]: bench}, bench) for y, (funds, bench) in cash.items()}
    split_evidence(parse(pinned(input_dir / "split_evidence.json", m["files"]["split_evidence.json"],
                                private=True)), windows, split_names, split_cash, C, cfg)
    control = C.split_control(parse(pinned(input_dir / "split_control.json", m["files"]["split_control.json"],
                                           private=True)), windows, roster, cfg)
    window_by_year = {w["turn"]: w for w in windows}

    def turn_packet(y):
        w = window_by_year[y]
        raw_bars = parse(pinned(input_dir / f"bars_{y}.json", m["files"][f"bars_{y}.json"], private=True))
        funds, bench = C.bars_file(raw_bars, w, roster[y], cfg)
        C.check_control(control[y], raw_bars, cash[y], cfg)
        del raw_bars
        quotes = C.quotes_file(parse(pinned(input_dir / f"quotes_{y}.json", m["files"][f"quotes_{y}.json"],
                                            private=True)), w, roster[y], cfg)
        for s, closes in funds.items():
            C.check_jumps(closes, cash[y][0][s]["splits"], cfg)
        C.check_jumps(bench, [], cfg)
        return funds, bench, quotes, cash[y]

    class StreamedPacket:
        def __getitem__(self, turn):
            return turn_packet(turn)

    eligible = {}
    for w in windows:
        y = w["turn"]
        funds, bench, quotes, actions = turn_packet(y)
        eligible[y] = {
            s for s, closes in funds.items()
            if C.complete_through(closes, w, w["entry"])
            and not any(w["anchor"] < d <= w["entry"] for d, _ in actions[0][s]["splits"])
            and closes[w["entry"]] * (1 + C.side_costs(quotes[0][s], w, cfg)["entry"]) <= cfg["sleeve_usd"]
        }
        need(len(eligible[y]) >= cfg["picks"], "TOO_FEW_ELIGIBLE")
        need(bench[w["entry"]] * (1 + C.side_costs(quotes[1], w, cfg)["entry"]) <= cfg["capital"], "BENCHMARK")
        # Drop prior turn payloads before opening the next, including when estimates are very large.
        del funds, bench, quotes, actions
    stat_counts = {
        "turns": len(windows), "roster_rows": sum(map(len, roster.values())),
        "events_placed": cfg["picks"] * len(windows), "clusters": len(windows),
        "symbols": len(set().union(*map(set, roster.values())) | {cfg["benchmark"]}),
        "eligible_rows": sum(map(len, eligible.values())), "excluded_rows": exclusions_count,
        "cash_events": cash_events, "cash_gaps": sum(map(len, gaps.values())),
        "eligible_cash_gaps": sum(len(gaps[y] & eligible[y]) for y in roster),
    }
    return windows, StreamedPacket(), eligible, gaps, stat_counts, m["files"][COMPARISON]


def correlation(blob, years):
    raw = parse(blob)
    need(type(raw) is list and len(raw) == len(years), "CORRELATION")
    pairs = []
    for previous, current in zip(raw, years):
        need(type(previous) is dict and set(previous) == {"turn", "portfolio"}
             and type(previous["turn"]) is int and previous["turn"] == current["turn"]
             and type(previous["portfolio"]) in (int, Decimal), "CORRELATION")
        p = float(previous["portfolio"])
        need(math.isfinite(p), "CORRELATION")
        pairs.append({"turn": current["turn"], "taxable": current["portfolio"], "muni": p})
    x, y = [r["taxable"] for r in pairs], [r["muni"] for r in pairs]
    r = statistics.correlation(x, y) if len(set(x)) > 1 and len(set(y)) > 1 else None
    need(r is None or math.isfinite(r), "CORRELATION")
    return {"pearson_r": r, "observations": len(pairs), "pairs": pairs,
            "status": "MEASURED" if r is not None else "UNKNOWN"}


def unused(run):
    private_dir(run)
    need(not any(run.iterdir()), "CONSUMED_OR_NOT_EMPTY")


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_new(path, payload):
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def once(run, metadata, inputs, evaluate):
    unused(run)
    job = metadata | {"claimed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        write_new(run / "score_53.lock", encode(job))
    except FileExistsError:
        raise Refused("P53_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    result = encode({"job": job} | evaluate(*inputs))
    tmp = run / ".results_53.tmp"
    write_new(tmp, result)
    os.link(tmp, run / "results_53.json", follow_symlinks=False)
    sync_dir(run)
    tmp.unlink()
    sync_dir(run)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "P53_ARGUMENTS\n")


def check_environment():
    need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
         and not any(k.startswith(("P53_", "PLAN53_", "GIT_", "PYTHON", "LD_")) or k in {"TZ", "TZDIR"}
                     for k in os.environ), "ENVIRONMENT")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--calibrate", action="store_true")
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    for flag in ("--approval-commit", "--freeze-sha256", "--input-sha256", "--roster-sha256",
                 "--distributions-sha256"):
        p.add_argument(flag)
    a = p.parse_args()
    os.umask(0o077)
    try:
        if a.calibrate:
            # Synthetic only: reads the working-tree engine and config, never the input or run directories.
            need(not any((a.approval_commit, a.freeze_sha256, a.input_sha256, a.roster_sha256,
                          a.distributions_sha256)), "ARGUMENTS")
            C = load_engine((REPO / ENGINE).read_bytes())
            sys.stdout.buffer.write(encode(C.calibrate(read_config((REPO / CONFIG).read_bytes()))))
            return
        pins = (a.approval_commit, a.freeze_sha256, a.input_sha256, a.roster_sha256, a.distributions_sha256)
        need(all(v is not None for v in pins), "ARGUMENTS")
        check_environment()
        freeze, blobs, exclusions_pin = authorize(*pins)
        C = load_engine(blobs[ENGINE])
        cfg = read_config(blobs[CONFIG])
        resources(cfg)
        if a.go:
            unused(RUN)
        try:
            check_calibration(C, cfg, blobs[CALIBRATION])
            inputs = load_inputs(INPUTS, a.input_sha256, a.roster_sha256, a.distributions_sha256, exclusions_pin, C,
                                 blobs[CALENDAR], cfg)
        except C.Refused as exc:
            raise Refused(str(exc).replace("P48_", "P53_", 1)) from None
        windows, packet, eligible, gaps, counts, comparison_pin = inputs
        if a.validate_inputs:
            print("P53_INPUTS_OK", " ".join(f"{k} {v}" for k, v in counts.items()))
            return
        meta = {"schema": 1, "ledger": LEDGER_ROW, "queue": QUEUE_ROW, "freeze_commit": freeze,
                "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
                "input_sha256": a.input_sha256, "roster_sha256": a.roster_sha256,
                "distributions_sha256": a.distributions_sha256, "roster_exclusions_sha256": exclusions_pin,
                "comparison_sha256": comparison_pin}
        need((freeze, blobs, exclusions_pin) == authorize(*pins), "APPROVAL")

        def evaluate():
            # This callback runs only after the lock is durable. Validation never opens the comparison payload.
            comp = pinned(INPUTS / COMPARISON, comparison_pin, private=True)
            result = C.evaluate(windows, packet, cfg)
            for table in (result["judged"], *result["shown_only"].values()):
                for row in table["years"]:
                    y = row["turn"]
                    row["held_quote_coverage_proxy_sides"] = row.pop("held_proxy_sides")
                    row["roster_cash_gaps"] = len(gaps[y])
                    row["eligible_cash_gaps"] = len(gaps[y] & eligible[y])
                    row["held_cash_gaps"] = len(gaps[y] & set(row["held"]))
            result["shown_only"]["replay48_correlation"] = correlation(comp, result["judged"]["years"])
            result["input_counts"] = counts
            return result

        try:
            once(RUN, meta, (), evaluate)
        except C.Refused as exc:
            raise Refused(str(exc).replace("P48_", "P53_", 1)) from None
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P53_REFUSED\n")
    print("P53_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
