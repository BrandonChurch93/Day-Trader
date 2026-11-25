"""Checks that the repo's map is true. Run from the repo root before every commit: python3 tools/check_repo.py
Fails (exit 1) if:
  1. a tracked file is not listed in docs/INDEX.md (a folder listed with a trailing slash covers everything under it)
  2. a path written in backticks in README.md, AGENTS.md, docs/STATUS.md, docs/INDEX.md or research_rig/README.md does not exist
     (a path that git ignores, such as research_rig/data/ or dashboard/data.json, is local only and is not flagged)
  3. a config key written in backticks anywhere under docs/ or research_rig/*.md is missing from config/thresholds.yaml
     (only names that look like keys of that file are checked: the known prefixes below)
  4. docs/STATUS.md has no line of the form 'Last updated: YYYY-MM-DD HH:MM UTC'
  5. the results table in docs/STATUS.md is not what tools/status_table.py writes from the output files
  6. a stored output in research_rig/, or a raw input file present on this machine, differs from its fingerprint in
     research_rig/provenance.json
With --builders it also runs every research_rig/build_doc*.py and fails if a file that git tracks changes. A document that
differs from what its builder writes was edited by hand or is stale. This takes a few seconds and reads no held-back slice anew:
the builders read stored outputs only.
It does not check that the status page is fresh. That is a rule for the person or model making the commit."""
import subprocess, re, sys, os, glob
bad = []
tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split("\n"); tracked = [t for t in tracked if t]
idx = open("docs/INDEX.md").read()
listed = set(re.findall(r"`([^`\s]+)`", idx)); folders = [p for p in listed if p.endswith("/")]
for t in tracked:
    if t in listed or any(t.startswith(f) for f in folders): continue
    bad.append(f"not in docs/INDEX.md: {t}")
for f in ["README.md", "AGENTS.md", "docs/STATUS.md", "docs/INDEX.md", "research_rig/README.md"]:
    for p in set(re.findall(r"`([A-Za-z0-9_./\-]+)`", open(f).read())):
        if "/" not in p and not re.search(r"\.(md|py|json|yaml|csv|html|js|css)$", p): continue
        if "*" in p or ".." in p or p.startswith("/") or "NN" in p: continue  # NN marks a pattern, not a file
        cands = [p, os.path.join(os.path.dirname(f), p), os.path.join("research_rig", p), os.path.join("docs", p)]
        if any(os.path.exists(c) for c in cands): continue
        if any(subprocess.run(["git", "check-ignore", "-q", c.rstrip("/")]).returncode == 0 for c in cands): continue  # a local-only path that git ignores, such as research_rig/data/
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
pv = subprocess.run([sys.executable, "provenance.py"], cwd="research_rig", capture_output=True, text=True).stdout
bad += [l for l in pv.split("\n") if l.startswith(("output differs", "input differs"))]
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
