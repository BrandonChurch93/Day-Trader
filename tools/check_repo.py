"""Checks that the repo's map is true. Run from the repo root before every commit: python3 tools/check_repo.py
Fails (exit 1) if:
  1. a tracked file is not listed in docs/INDEX.md. Listed means: the file's full path is in backticks in the first column
     of a file table row (a row whose State cell starts with CURRENT, RECORD, DRAFT or RAW), or a folder with a trailing
     slash that holds it is. The task table does not count. A path or folder named anywhere else on that page
     does not count, so a new file under docs/research/ or research_rig/ needs its own row
  2. a path written in backticks in README.md, AGENTS.md, docs/STATUS.md, docs/INDEX.md, docs/GLOSSARY.md,
     docs/DECISIONS.md, docs/QUEUE.md, research_rig/README.md,
     dashboard/README.md, or any file directly under docs/playbook/ or docs/research/ does not exist
     (a path that git ignores, such as research_rig/data/ or dashboard/data.json, is local only and is not flagged; the few
     names that look like paths and are not, such as a model name, are listed with reasons in NOT_IN_REPO below)
     Not checked for paths: archive/, the raw reports in docs/research/*_raw/, and the plans
     and notes in research_rig/ other than its README
  3. a config key written in backticks anywhere under docs/ or research_rig/*.md is missing from config/thresholds.yaml
     (only names that look like keys of that file are checked: the known prefixes below)
  4. docs/STATUS.md has no line of the form 'Last updated: YYYY-MM-DD HH:MM UTC'
  5. the results table in docs/STATUS.md is not what tools/status_table.py writes from the output files
  6. a stored output in research_rig/, or a raw input file present on this machine, differs from its fingerprint in
     research_rig/provenance.json (this does not fingerprint the code files that record lists)
  7. the coverage tables in docs/research/10_historical_data_and_practice.md are not what tools/bars_coverage.py writes from
     research_rig/platform_bars_coverage.json and research_rig/platform_bars_crosscheck.json, or the page holds more than one
     such block, or the file fingerprints listed in the coverage file do not add up to the two in research_rig/provenance.json.
     This does not show that the counts in those two files are right: only someone with the price files can rerun them
With --builders it also runs every research_rig/build_doc*.py and fails if a file that git tracks changes. A document that
differs from what its builder writes was edited by hand or is stale. This takes a few seconds and runs no rule on any price.
The builders read stored outputs only, except build_doc16.py, which also compares two raw price files when they are present.
It does not check that the status page is fresh. That is a rule for the person or model making the commit."""
import subprocess, re, sys, os, glob
bad = []
# Names in backticks that look like paths and are not files in this repo, each with the reason. Keep this list short and exact:
# a pair is (the file that names it, the name). Anything else that does not resolve is a fault.
NOT_IN_REPO = {
    ("dashboard/README.md", "summary.json"): "generated on the practice-records branch, not stored on this branch",
    ("docs/research/08_backtester_fixtures_draft.md", "kit/data/"): "the owner's build kit, which lives outside this repo",
    ("docs/research/05_perplexity_platform_options.md", "perplexity/sonar"): "a model name, not a path",
    ("docs/research/06_architecture_and_build_process.md", "config/universe.yaml"): "a file the reading proposed; nothing is built",
    ("docs/research/06_architecture_and_build_process.md", "src/risk/"): "a folder the reading proposed; nothing is built",
    ("docs/research/07_tradingview_and_operator_access.md", "CLAUDE.md"): "a file another tool reads; not part of this repo",
}
tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split("\n"); tracked = [t for t in tracked if t]
idx = open("docs/INDEX.md").read()
listed = set()
for line in idx.split("\n"):
    cells = line.split("|")
    # a file row has three cells and its last one starts with a state word; the task table and the state legend do not
    if line.startswith("|") and len(cells) == 5 and cells[3].strip().split(".")[0].split(" ")[0] in ("CURRENT", "RECORD", "DRAFT", "RAW"): listed |= set(re.findall(r"`([^`\s]+)`", cells[1]))
folders = [p for p in listed if p.endswith("/")]
for t in tracked:
    if t in listed or any(t.startswith(f) for f in folders): continue
    bad.append(f"not in docs/INDEX.md: {t}")
for f in ["README.md", "AGENTS.md", "docs/STATUS.md", "docs/INDEX.md", "docs/GLOSSARY.md", "docs/DECISIONS.md", "docs/QUEUE.md", "research_rig/README.md", "dashboard/README.md"] + sorted(glob.glob("docs/playbook/*.md")) + sorted(glob.glob("docs/research/*.md")):
    for p in set(re.findall(r"`([A-Za-z0-9_./\-]+)`", open(f).read())):
        if "/" not in p and not re.search(r"\.(md|py|json|yaml|csv|html|js|css)$", p): continue
        if "*" in p or ".." in p or p.startswith("/") or "NN" in p: continue  # NN marks a pattern, not a file
        if (f, p) in NOT_IN_REPO: continue
        cands = [p, os.path.join(os.path.dirname(f), p), os.path.join("research_rig", p), os.path.join("docs", p)] + [os.path.join("docs", d, p) for d in ("research", "playbook")]
        if any(os.path.exists(c) for c in cands): continue
        if any(subprocess.run(["git", "check-ignore", "-q", x]).returncode == 0 for c in cands for x in {c, c.rstrip("/")}): continue  # a local-only path that git ignores, such as research_rig/data/
        bad.append(f"{f} names a path that does not exist: {p}")
keys = set(re.findall(r"^([a-z0-9_]+):", open("config/thresholds.yaml").read(), re.M))
pref = ("backtest_", "replay_", "paper_", "live_", "moonshot_", "api_model_", "cost_model_", "shadow_", "intraday_trend_", "research_run_", "scale_live_", "max_kelly", "drawdown_derisk")
for f in glob.glob("docs/**/*.md", recursive=True) + glob.glob("research_rig/*.md"):
    if "_raw/" in f or "checklogs" in f: continue
    for k in set(re.findall(r"`([a-z0-9_]+)`", open(f).read())):
        if k.startswith(pref) and k not in keys and k not in pref: bad.append(f"{f} names a config key that does not exist: {k}")
m = re.search(r"Last updated: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC", open("docs/STATUS.md").read())
if not m: bad.append("docs/STATUS.md has no 'Last updated: YYYY-MM-DD HH:MM UTC' line")
sys.path.insert(0, "tools"); import status_table
if not status_table.in_sync(): bad.append("docs/STATUS.md results table is out of date: run python3 tools/status_table.py --write")
import bars_coverage
if not bars_coverage.in_sync(): bad.append("docs/research/10_historical_data_and_practice.md coverage tables are out of date, or there is more than one block: run python3 tools/bars_coverage.py --write")
if not bars_coverage.fingerprints_agree(): bad.append("research_rig/platform_bars_coverage.json lists file fingerprints that do not add up to the ones in research_rig/provenance.json")
pv = subprocess.run([sys.executable, "provenance.py"], cwd="research_rig", capture_output=True, text=True)
pl = [l for l in pv.stdout.split("\n") if l.startswith(("output differs", "input differs", "provenance.json is not"))]
bad += pl
if pv.returncode and not pl:   # provenance.py failed for a reason the lines above did not name
    bad.append("research_rig/provenance.py exited with an error: " + ((pv.stderr.strip().splitlines() or pv.stdout.strip().splitlines() or ["no message"])[-1]))
if "--builders" in sys.argv:
    def state(): return subprocess.run("git status --porcelain; git diff | sha256sum", shell=True, capture_output=True, text=True).stdout
    before = state()
    for b in sorted(glob.glob("research_rig/build_doc*.py")):
        r = subprocess.run([sys.executable, os.path.basename(b)], cwd="research_rig", capture_output=True, text=True)
        if r.returncode: bad.append(f"{b} stopped with an error: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}")
        after = state()
        if after != before: bad.append(f"{b} changed a tracked file: the document was edited by hand or is stale"); before = after
        print("ran " + b)
if bad:
    print("\n".join(sorted(bad))); print(f"\n{len(bad)} problem(s)"); sys.exit(1)
print(f"repo map ok: {len(tracked)} tracked files, all listed; paths and config keys resolve")
