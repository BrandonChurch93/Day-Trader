"""The record of how each stored output was made: script, command, the commit that stored it, and the fingerprint of every input file.

Written after the fact on 2026-11-25. At run time the outputs were not stored with their command, commit and input
fingerprints, which archive/quality/01_the_bar.md asks for. This file rebuilds what can still be shown:
  - the output file as it is in the repo (sha256) and the commits that first stored it and last changed it (from git history)
  - the script and command (from the code and the run logs)
  - the raw input files as they were on the research machine when this record was taken (sha256, bytes, last-modified time)
It cannot show that an output was made from exactly these input bytes. Where an input file was last modified after the
output was first stored, the record says so in "inputs_modified_after_output_first_stored".

Usage, from research_rig/:
  python3 provenance.py             check only. Writes nothing. Exit 1 if an output or a present input differs from the record
  python3 provenance.py --record    rewrite provenance.json. An input fingerprint already on record is kept, even if the
                                    file is missing or different now. A new input gets its fingerprint added
  python3 provenance.py --record --replace NAME   also replace the recorded fingerprint of the input called NAME
Running a run_*.py script is a separate matter with its own rule. See README.md, "How each stored output was made"."""
import os, sys, json, glob, hashlib, subprocess, datetime
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "data")
K = os.environ.get("KRAKEN_DIR", os.path.join(D, "kraken")); KD = os.environ.get("KRAKEN_DAILY_DIR", os.path.join(D, "kraken", "daily"))   # as basket.py: not moved by KRAKEN_DIR
F = os.environ.get("FRENCH_DIR", os.path.join(D, "french"))

# name -> (how it is shown, real path). Names are what README.md and check_data.py call the files.
INPUTS = {
    "data/bitstamp_BTCUSD.csv": f"{D}/bitstamp_BTCUSD.csv", "data/bitstamp_ETHUSD.csv": f"{D}/bitstamp_ETHUSD.csv",
    "data/bitstamp_BTCUSD_1h.csv": f"{D}/bitstamp_BTCUSD_1h.csv", "data/bitstamp_ETHUSD_1h.csv": f"{D}/bitstamp_ETHUSD_1h.csv",
    "data/kraken_BTCUSD.csv": f"{D}/kraken_BTCUSD.csv", "data/kraken_ETHUSD.csv": f"{D}/kraken_ETHUSD.csv",
    "data/krakenfull_BTCUSD.csv": f"{D}/krakenfull_BTCUSD.csv", "data/krakenfull_ETHUSD.csv": f"{D}/krakenfull_ETHUSD.csv",
    "KRAKEN_DIR/full_XBTUSD_1440.csv": f"{K}/full_XBTUSD_1440.csv", "KRAKEN_DIR/full_ETHUSD_1440.csv": f"{K}/full_ETHUSD_1440.csv",
    "KRAKEN_DIR/full_XBTUSD_60.csv": f"{K}/full_XBTUSD_60.csv", "KRAKEN_DIR/full_ETHUSD_60.csv": f"{K}/full_ETHUSD_60.csv",
    "KRAKEN_DAILY_DIR/*USD_1440.csv": f"{KD}/*USD_1440.csv",
    "FRENCH_DIR/F-F_Research_Data_Factors_daily__main.csv": f"{F}/F-F_Research_Data_Factors_daily__main.csv",
    "FRENCH_DIR/12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv": f"{F}/12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv",
    "data/books/books.csv": f"{D}/books/books.csv",
    "data/platform_bars/1min/*.csv": os.path.join(os.environ.get("PLATFORM_BARS_DIR", f"{D}/platform_bars"), "1min", "*.csv"),
    "data/platform_bars/1day/*.csv": os.path.join(os.environ.get("PLATFORM_BARS_DIR", f"{D}/platform_bars"), "1day", "*.csv"),
}
BD, BH = ["data/bitstamp_BTCUSD.csv", "data/bitstamp_ETHUSD.csv"], ["data/bitstamp_BTCUSD_1h.csv", "data/bitstamp_ETHUSD_1h.csv"]
KA, KF = ["data/kraken_BTCUSD.csv", "data/kraken_ETHUSD.csv"], ["data/krakenfull_BTCUSD.csv", "data/krakenfull_ETHUSD.csv"]
K1440, K60 = ["KRAKEN_DIR/full_XBTUSD_1440.csv", "KRAKEN_DIR/full_ETHUSD_1440.csv"], ["KRAKEN_DIR/full_XBTUSD_60.csv", "KRAKEN_DIR/full_ETHUSD_60.csv"]
FR = ["FRENCH_DIR/F-F_Research_Data_Factors_daily__main.csv", "FRENCH_DIR/12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv"]
ALPACA_09 = os.path.join(os.path.expanduser("~"), "workspace", "rig", "data", "alpaca_crypto")
RUN_09 = os.path.join(H, "results_09.json")
RAW_09 = []
if os.path.exists(RUN_09):
    with open(RUN_09) as r09:
        replay_09 = json.load(r09)
    for frames in replay_09["coverage"].values():
        for meta in frames.values():
            if "file" in meta:
                name = "ALPACA_09/" + meta["file"]
                INPUTS[name] = os.path.join(ALPACA_09, meta["file"])
                RAW_09.append(name)

# output -> (kind, command, code files, raw inputs, stored outputs it reads)
# kind "held-back": the script runs a trading rule, or scores or collects trading calls, on prices that include held-back dates.
# kind "prices-no-rule": it reads raw prices that include held-back dates and runs no trading rule. It builds a data file or
#                        compares two price histories.
# kind "no-rule": it reads no raw price that a rule was tested on. It compares stored outputs, draws random numbers, or sums up order-book samples.
OUTPUTS = {
    "results_01.json": ("held-back", "python3 run_01.py", ["run_01.py", "engine.py", "rules.py"], BD, []),
    "passmarks_01.json": ("held-back", "python3 run_01b.py", ["run_01b.py", "engine.py", "rules.py", "common_01.py"], BD, ["results_01.json"]),
    "results_01c.json": ("held-back", "python3 run_01c.py", ["run_01c.py", "engine.py", "rules.py", "common_01.py"], BD + KA + BH, []),
    "results_01d.json": ("held-back", "python3 report_01d.py", ["report_01d.py", "engine.py", "rules.py", "common_01.py"], BD, []),
    "results_01x2.json": ("held-back", "python3 run_01x2.py", ["run_01x2.py", "engine.py", "rules.py", "common_01.py", "common_03.py"], KF, ["kraken_daily_build.json"]),
    "diag_x2_pbo.json": ("held-back", "python3 diag_x2_pbo.py", ["diag_x2_pbo.py", "engine.py", "rules.py", "common_01.py"], KF + BD, []),
    "results_02.json": ("held-back", "python3 score_02.py", ["score_02.py", "engine.py", "rules.py"], BD, ["pilot/decisions.jsonl"]),
    "results_03.json": ("held-back", "python3 run_03.py", ["run_03.py", "common_03.py", "common_01.py", "rules.py", "engine.py"], BH + BD, []),
    "results_v2.json": ("held-back", "python3 run_v2.py R01 X2 S2 DIAG R03", ["run_v2.py", "rig2.py", "rules.py", "common_03.py", "fixtures2.py", "../config/thresholds.yaml"], BD + KF + BH + K60, []),
    "results_04.json": ("held-back", "python3 run_04.py", ["run_04.py", "rig2.py", "basket.py", "rules.py", "fixtures2.py", "fixtures_basket.py", "../config/thresholds.yaml"], ["KRAKEN_DAILY_DIR/*USD_1440.csv"], []),
    "results_05.json": ("held-back", "python3 run_05.py", ["run_05.py", "rig2.py", "fixtures2.py", "../config/thresholds.yaml"], FR, []),
    "results_05b.json": ("held-back", "R05_POOL=1 python3 run_05.py", ["run_05.py", "rig2.py", "fixtures2.py", "../config/thresholds.yaml"], FR, []),
    "i2_2020_note.json": ("prices-no-rule", "python3 i2_2020_note.py", ["i2_2020_note.py"], FR[1:], []),
    "pilot/decisions.jsonl": ("held-back", "python3 pilot/server.py, with six AI model runs calling it over HTTP", ["pilot/server.py", "engine.py"], BD, []),
    "kraken_daily_build.json": ("prices-no-rule", "python3 build_kraken_daily.py", ["build_kraken_daily.py"], K1440 + KA + BD, []),
    "venue_price_gap.json": ("prices-no-rule", "python3 build_doc16.py", ["build_doc16.py"], BD[:1] + KF[:1], []),
    "compare_v1_v2.json": ("no-rule", "python3 compare_v1_v2.py", ["compare_v1_v2.py"], [], ["results_v2.json", "passmarks_01.json", "results_01x2.json", "results_03.json", "diag_x2_pbo.json"]),
    "noise_pbo.json": ("no-rule", "python3 noise_pbo.py", ["noise_pbo.py", "rig2.py"], [], []),
    "ledger_count_check.json": ("no-rule", "python3 ledger_count_check.py", ["ledger_count_check.py", "rig2.py"], [], ["results_v2.json", "results_04.json", "results_05.json", "results_05b.json"]),
    "books_summary.json": ("no-rule", "python3 books_summary.py", ["books_summary.py"], ["data/books/books.csv"], []),
    "platform_bars_crosscheck.json": ("prices-no-rule", "python3 platform_bars_crosscheck.py", ["platform_bars_crosscheck.py"], ["data/platform_bars/1min/*.csv", "data/platform_bars/1day/*.csv"], []),
    "platform_bars_coverage.json": ("prices-no-rule", "python3 platform_bars_integrity.py, then from the repo root python3 tools/bars_coverage.py --summarise", ["platform_bars_integrity.py", "platform_bars_consolidate.py", "../tools/bars_coverage.py"], ["data/platform_bars/1min/*.csv", "data/platform_bars/1day/*.csv"], []),
}
NOTES = {
    "results_v2.json": "The hourly part (R03) stopped twice on program errors and was started again (docs/research/16_rig_audit.md). Its returns cache data/v2_r01_returns.json is local and not fingerprinted.",
    "results_05.json": "First run. Rule I2 was coded differently from its pushed plan (AMENDMENT_05_I2_equal_thirds.md).",
    "results_05b.json": "Corrected run, ledger row R2. The fault was in the rule code, not in the engine.",
    "i2_2020_note.json": "Multiplies up each industry group's daily returns for 2020, a held-back year. No rule, no pass mark, not a trial. Run once more after its data path line changed in commit c7956c4, so the second run was not of unchanged code; output identical; not counted. Research keeps it on the do-not-run list all the same (README.md, \"Held-back scripts\").",
    "venue_price_gap.json": "Written by build_doc16.py only when both price files are present. Otherwise the stored file is read.",
    "platform_bars_crosscheck.json": "For SPY and QQQ, how far the day's open, high, low and close rebuilt from the one-minute files sit from the daily file, in basis points, with counts and dates. No price is in it, no rule was run and no return over time was worked out. Both sets of files come from the same lookup, so this cannot show that either is right.",
    "platform_bars_coverage.json": "The check's full output (integrity.json) and the original pulls are on the research machine and are not fingerprinted here; only the joined price files are. Dates, counts and file fingerprints of the stock prices collected through the workspace's own price lookup on 2026-11-25. No price is in it, no rule was run and no return was worked out. The price files are on the research machine only and cannot be fetched by a script; whether they may be kept is item 6 of the morning list.",
    "books_summary.json": "As of 2026-11-25 09:55 UTC the sampler was still writing data/books/books.csv, and stops by itself at about 16:30 UTC. The summary stored here covers its first 34 minutes. The input fingerprint is added with --with-books once sampling ends, or as an interim one that says so.",
    "results_01.json": "v1 engine. Kept as the record. Superseded by results_v2.json.",
    "pilot/decisions.jsonl": "Pilot 02. The server gave each model one day of prices at a time, 2026-06-30 to 2026-11-23, and logged its call. Run once. The models' replies cannot be made again from this record.",
    "kraken_daily_build.json": "Compares Kraken and Bitstamp daily closes while building the Kraken daily files. No rule.",
}
if RAW_09:
    OUTPUTS["results_09.json"] = (
        "held-back", "python3 run_09.py --held --prereg-commit " + replay_09["provenance"]["prereg_commit"][:7],
        ["run_09.py", "fetch_09_alpaca.py", "rig2.py", "fixtures_09.py", "../config/thresholds.yaml"], RAW_09, [],
    )
    NOTES["results_09.json"] = "Alpaca bars and replay code carry run-time fingerprints in the output. Minute tape is coverage only."

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def mtime(p): return datetime.datetime.fromtimestamp(os.path.getmtime(p), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def fingerprint(name):
    p = INPUTS[name]
    if "*" in p:
        fs = sorted(glob.glob(p))
        if not fs: return None
        lines = "".join(f"{os.path.basename(f)} {sha(f)}\n" for f in fs)
        return dict(files=len(fs), bytes=sum(os.path.getsize(f) for f in fs), sha256_of_name_and_sha256_lines=hashlib.sha256(lines.encode()).hexdigest(),
                    modified_first=min(mtime(f) for f in fs), modified_last=max(mtime(f) for f in fs))
    if not os.path.exists(p): return None
    return dict(bytes=os.path.getsize(p), sha256=sha(p), modified=mtime(p))
def same(a, b): return a is not None and b is not None and all(a.get(k) == b.get(k) for k in ("sha256", "sha256_of_name_and_sha256_lines", "bytes", "files"))
def git(*a): return subprocess.run(["git", *a], cwd=H, capture_output=True, text=True).stdout.strip()
def commits(f):
    log = git("log", "--format=%h %cI", "--", f).split("\n"); log = [x for x in log if x]
    if not log: return None, None
    dirty = bool(git("status", "--porcelain", "--", f))
    return log[-1], ("not committed yet" if dirty else log[0])

def main():
    record = "--record" in sys.argv; replace = [sys.argv[i + 1] for i, a in enumerate(sys.argv[:-1]) if a == "--replace"]
    path = os.path.join(H, "provenance.json"); old = json.load(open(path)) if os.path.exists(path) else {"inputs": {}, "outputs": {}}
    inputs, diffs, absent = {}, [], []
    for name in INPUTS:
        if name == "data/books/books.csv" and name not in old["inputs"] and "--with-books" not in sys.argv: continue   # still being written
        now = fingerprint(name); was = old["inputs"].get(name)
        if now is None: absent.append(name)
        elif was is not None and not same(now, was): diffs.append(f"input differs from the record: {name}")
        inputs[name] = now if (was is None or name in replace) and now is not None else was
        if inputs[name] is None: del inputs[name]
    outputs = {}
    for out, (kind, cmd, code, ins, reads) in OUTPUTS.items():
        first, last = commits(out); s = sha(os.path.join(H, out)); was = old["outputs"].get(out, {})
        if was and was.get("sha256") != s: diffs.append(f"output differs from the record: {out}")
        stored = first.split(" ")[1] if first else None
        late = sorted(n for n in ins if n in inputs and stored and max(inputs[n].get("modified", ""), inputs[n].get("modified_last", "")) > stored.replace("+00:00", "Z"))
        outputs[out] = dict(kind=kind, command=cmd, run_from="research_rig/", code=code, raw_inputs=ins, reads_stored_outputs=reads, sha256=s,
                            first_stored_in_commit=first, last_changed_in_commit=last, inputs_modified_after_output_first_stored=late)
        if out in NOTES: outputs[out]["note"] = NOTES[out]
    doc = dict(
        what_this_is="Record of how each stored output in research_rig/ was made. Built after the fact by provenance.py; see its first lines for what this can and cannot show.",
        python_when_recorded=(old.get("python_when_recorded") if not record and old.get("python_when_recorded") else sys.version.split()[0]),
        packages="research_rig/requirements.txt",
        commit_fields="short hash and commit time. 'first_stored_in_commit' is the commit that added the file. The code a run used is taken to be the code at that commit; that is STATED by research, and nothing in this record can show it.",
        not_in_this_record="dashboard/data.json and dashboard/curves_cache.json, which are not committed. export_dashboard.py --resimulate replays five stored runs, of three rules, on raw prices that include held-back dates to draw their curves. See README.md, 'How each stored output was made'.",
        inputs=inputs, outputs=outputs)
    text = json.dumps(doc, indent=1) + "\n"
    if record:
        open(path, "w").write(text); print(f"provenance.json written: {len(outputs)} outputs, {len(inputs)} inputs on record")
    for d in diffs: print(d)
    for a in absent: print("input not on this machine (record kept): " + a)
    stale = (not record) and os.path.exists(path) and open(path).read() != text and not diffs
    if stale: print("provenance.json is not what this script would write (a commit field or the map changed): run python3 provenance.py --record")
    here = len(inputs) - len([a for a in absent if a in inputs])
    if not diffs and not stale and not record:
        print(f"{len(outputs)} stored outputs match the record. " + (f"{here} of {len(inputs)} recorded input files are on this machine and match."
              if here else f"None of the {len(inputs)} recorded input files is on this machine, so no input was checked."))
    sys.exit(1 if (diffs or stale) and not record else 0)
if __name__ == "__main__": main()
