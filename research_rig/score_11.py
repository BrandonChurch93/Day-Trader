"""Scores draft plan 11. Run from research_rig/.

  python3 score_11.py --design      the design sample: 6 set-ups x 2 holds and yardstick (c), agreement between readers,
                                    and the chosen set-up. Writes results_11_design.json.
  python3 score_11.py --heldback    the lead alone runs this, once. The chosen set-up on every held-back event, the pass
                                    mark, and each list alone. Writes results_11_heldback.json and refuses if it exists.

Before it reads any price it refuses unless:
  - research_rig/answers_11_<phase>_hashes.json is in origin/main, byte for byte (it runs git fetch origin main first),
  - every answers file it lists has that SHA-256, and data/edgar_11/usable_11.json has the SHA-256 it lists,
  - the plan has its frozen name (PREREG_11_earnings_release_reader.md) and is in origin/main byte for byte, and the
    replay_11_* config keys equal origin/main's; --heldback also needs them equal to those results_11_design.json used,
  - --design refuses if results_11_design.json exists here or in origin/main; --heldback refuses if
    results_11_heldback.json or score_11_heldback.lock exists here or in origin/main, and writes the lock before it reads
    a held-back price. The real run always uses research_rig/, whatever RESULTS_11_DIR says,
  - for --heldback, results_11_design.json is also in origin/main byte for byte, and its chosen set-up is the one read,
  - the SPY daily file reaches the last exit day needed (prices must be collected again after 2026-11-24).
Every number it uses comes from config/thresholds.yaml (replay_11_*). It prints a short table and stores no price."""
import sys, os, json, glob, math, random, subprocess, statistics, datetime as dt
import yaml
import common_11 as C

RD, DS, ST, CO, GP, OV = (C.th(k) for k in ("replay_11_readers", "replay_11_design", "replay_11_statistics", "replay_11_costs", "replay_11_gap", "replay_11_overnight"))
SMALL, STRONG = RD["small_models"], RD["strong_model"]
REPO = os.path.dirname(C.HERE)
FROZEN_PLAN = "research_rig/PREREG_11_earnings_release_reader.md"   # the name the plan takes at freeze
HELDBACK_OUT, HELDBACK_LOCK, DESIGN_OUT = "results_11_heldback.json", "score_11_heldback.lock", "results_11_design.json"
CONFIG_KEYS = ("replay_11_events", "replay_11_costs", "replay_11_readers", "replay_11_design", "replay_11_gap", "replay_11_statistics", "replay_11_overnight")

class Refused(SystemExit): pass

# ------------------------------------------------------------------------------------------------ guards
def pushed_bytes(rel):
    if subprocess.run(["git", "fetch", "--quiet", "origin", "main"], cwd=REPO).returncode: raise Refused("refused: git fetch origin main failed")
    r = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=REPO, capture_output=True)
    return r.stdout if r.returncode == 0 else None

def require_pushed(rel):
    local = open(os.path.join(REPO, rel), "rb").read() if os.path.exists(os.path.join(REPO, rel)) else None
    if local is None: raise Refused(f"refused: {rel} does not exist")
    if pushed_bytes(rel) != local: raise Refused(f"refused: {rel} is not in origin/main as it is here. Commit and push it first.")

def out_dir(require_push):
    """The real run (require_push) always reads and writes research_rig/, whatever RESULTS_11_DIR says. Only the tests move it."""
    return C.HERE if require_push else C.OUTDIR

def config_now():
    return {k: C.th(k) for k in CONFIG_KEYS}

def require_frozen():
    """The plan has its frozen name and is in origin/main as it is here; the replay_11_* config keys equal origin/main's."""
    if not os.path.exists(os.path.join(REPO, FROZEN_PLAN)): raise Refused(f"refused: {FROZEN_PLAN} does not exist. Freeze the plan first.")
    require_pushed(FROZEN_PLAN)
    pushed = pushed_bytes("config/thresholds.yaml")
    if pushed is None: raise Refused("refused: config/thresholds.yaml is not in origin/main")
    Y = yaml.safe_load(pushed)
    if {k: (Y.get(k) or {}).get("value") for k in CONFIG_KEYS} != config_now(): raise Refused("refused: the replay_11_* keys differ from origin/main")

def exists_anywhere(name, require_push):
    """True if research_rig/<name> exists here, or (real run) in origin/main."""
    return os.path.exists(os.path.join(out_dir(require_push), name)) or (require_push and pushed_bytes(f"research_rig/{name}") is not None)

ENV_OVERRIDES = ("EDGAR_11_DIR", "STOCK_DAILY_11_DIR", "SPY_DAILY_11_FILE", "RESULTS_11_DIR")   # only the tests set these

def require_no_override():
    on = [v for v in ENV_OVERRIDES if v in os.environ]
    if on: raise Refused(f"refused: {', '.join(on)} set. A real run reads only the default folders.")

def prices_digest(events):
    """One SHA-256 over the sorted names and bytes of every price file the run reads, SPY included."""
    files = sorted({C.price_path(k["symbol"]) for k in events} - {None} | {C.SPY_FILE}, key=os.path.basename)
    h = __import__("hashlib").sha256()
    for f in files: h.update(os.path.basename(f).encode() + b"\0" + open(f, "rb").read() + b"\0")
    return dict(files=len(files), sha256=h.hexdigest())

def check_hashes(phase, readers, require_push=True):
    rel = f"research_rig/answers_11_{phase}_hashes.json"
    if require_push: require_pushed(rel)
    H = json.load(open(os.path.join(out_dir(require_push), os.path.basename(rel))))
    want = {f"answers_11_{phase}_{r}.jsonl" for r in readers}
    if set(H["files"]) != want: raise Refused(f"refused: the hashes file lists {sorted(H['files'])}, not exactly {sorted(want)}")
    for name, v in H["files"].items():
        p = os.path.join(C.EDGAR, name)
        if not os.path.exists(p) or C.sha256_file(p) != v["sha256"]: raise Refused(f"refused: {name} differs from its pushed hash")
    if C.sha256_file(os.path.join(C.EDGAR, "usable_11.json")) != H["usable_file_sha256"]: raise Refused("refused: usable_11.json differs from its pushed hash")
    if C.sha256_file(C.INSTRUCTION) != H["instruction_sha256"]: raise Refused("refused: the instruction differs from the one the readers saw")
    return H

# ------------------------------------------------------------------------------------------------ answers and set-ups
def load_answers(phase, readers, as_given=False):
    """{reader: {event_id: score}} from the collected, hashed files only. as_given: the score before a remembered move was
    set to 0 (the side line, not judged)."""
    out = {}
    for r in readers:
        p = os.path.join(C.EDGAR, f"answers_11_{phase}_{r}.jsonl")
        if not os.path.exists(p): raise Refused(f"refused: {os.path.basename(p)} does not exist. Run check_11_answers.py --collect {phase}.")
        out[r] = {a["event_id"]: (a["score_given"] if as_given and a.get("remembered") else a["score"]) for a in map(json.loads, open(p))}
    return out

def zeroed(phase, readers):
    """The event ids whose score the checker set to 0 because the reason says the reader remembers the move."""
    return {r: sorted(a["event_id"] for a in map(json.loads, open(os.path.join(C.EDGAR, f"answers_11_{phase}_{r}.jsonl"))) if a.get("remembered")) for r in readers}

def buy(s): return s >= 1

def disagree(scores):
    return len({buy(s) for s in scores}) > 1 or max(scores) - min(scores) >= 2

def cascade_strong_set(ids, A):
    """The held-back events the strong reader reads under cascade: every disagreement, and a seeded audit_share of the
    agreed events. prep_11.py heldback 2 writes exactly these; the scorer checks the strong reader answered them all."""
    dis = sorted(i for i in ids if disagree([A[r][i] for r in SMALL]))
    agreed = sorted(i for i in ids if i not in set(dis))
    audit = sorted(random.Random(f"{ST['seed']}-audit").sample(agreed, round(RD["audit_share"] * len(agreed))))
    return dis, audit

def setup_scores(setup, A, ids):
    if setup in A and setup in SMALL + [STRONG]: return {i: A[setup][i] for i in ids}
    if setup == "middle": return {i: sorted(A[r][i] for r in SMALL)[1] for i in ids}
    if setup == "cascade":
        return {i: (A[STRONG][i] if disagree([A[r][i] for r in SMALL]) else sorted(A[r][i] for r in SMALL)[1]) for i in ids}
    raise ValueError(setup)

# ------------------------------------------------------------------------------------------------ trades
def trades(events, days):
    """Per event and hold: return after the list's cost (fraction), and the same window's SPY move. Flags a stock whose bars
    stop inside the hold (sold at its last close) and a large overnight move inside the hold (replay_11_overnight)."""
    import csv
    spy = {r["date"]: (float(r["open"]), float(r["close"])) for r in csv.DictReader(open(C.SPY_FILE, newline=""))}
    prices_reach(events, days); out = {}; cache = {}
    for k in events:
        s = k["symbol"]; P = cache.setdefault(s, C.price_rows(s)); c = CO["bps_per_side"][k["list"]] / 1e4
        i0 = days.index(k["entry_day"]); o = P[k["entry_day"]][0]; row = dict(list=k["list"], gross={}, net={}, spy={}, stopped={}, overnight={})
        for h, n in ST["holds"].items():
            ex = days[i0 + n - 1]; stopped = ex not in P
            exd = ex if not stopped else max(d for d in P if d <= ex)
            cl = P[exd][1]; row["gross"][h] = cl / o - 1; row["net"][h] = cl * (1 - c) / (o * (1 + c)) - 1
            row["spy"][h] = spy[exd][1] / spy[k["entry_day"]][0] - 1; row["stopped"][h] = stopped   # SPY over the stock's own hold
            row["overnight"][h] = [f"{a} to {b} {q:.3f}" for a, b, q in C.overnight_moves(P, days[i0:i0 + n], OV["ratio_min"], OV["ratio_max"])]
        lc = C.last_close_day_before(k["acceptance_ny"], days)
        row["gap_buy"] = bool(lc in P and P[lc][1] > 0 and o / P[lc][1] - 1 > GP["min_up_pct"] / 100)
        row["cost"] = c; out[k["event_id"]] = row
    return out

def prices_reach(events, days):
    need = max((days.index(k["entry_day"]) + max(ST["holds"].values()) - 1 for k in events), default=0)
    if need >= len(days): raise Refused(f"refused: prices end {days[-1]}; collect them again to the last exit day first")

def as_given_line(T, ids, picks, h, tag):
    """The same set-up with the scores as the readers gave them, before a remembered move was set to 0. Not judged."""
    j = judge(T, ids, picks, h, tag, side=False)
    return dict(buys=j["buys"], mean=j["mean"], minus_a=j["minus_a"])

def net_at(T, i, h, mult):
    c = T[i]["cost"] * mult; g = T[i]["gross"][h]
    return (1 + g) * (1 - c) / (1 + c) - 1

def judge(T, ids, picks, h, seed_tag, mult=1.0, side=True):
    """picks: the event ids bought. Yardsticks (a) and (b) are drawn from ids. With side=True it adds, not judged, the same
    figures with flagged trades left out of both picks and ids: without large overnight moves, and without stops."""
    r_all = [net_at(T, i, h, mult) for i in ids]; r = [net_at(T, i, h, mult) for i in picks]
    a = statistics.fmean(r_all); m = statistics.fmean(r) if r else None
    rng = random.Random(f"{ST['seed']}-{seed_tag}-{h}"); draws = []
    if r:
        for _ in range(ST["draws"]): draws.append(statistics.fmean(rng.sample(r_all, len(r))))
    draws.sort()
    p95 = draws[int(0.95 * (len(draws) - 1))] if draws else None
    return dict(buys=len(r), events=len(ids), buy_share=round(len(r) / len(ids), 4), mean=m, mean_all_a=a,
                minus_a=(m - a) if r else None, random_p95_b=p95, share_of_draws_beaten=(sum(d < m for d in draws) / len(draws)) if r else None,
                minus_spy=statistics.fmean(net_at(T, i, h, mult) - T[i]["spy"][h] for i in picks) if r else None,
                stopped=sum(T[i]["stopped"][h] for i in picks), overnight_flagged=sum(bool(T[i]["overnight"][h]) for i in picks),
                **(side_results(T, ids, picks, h, seed_tag, mult) if side else {}))

def side_results(T, ids, picks, h, seed_tag, mult):
    out = {}
    for name, bad in (("without_overnight_flagged_not_judged", lambda i: bool(T[i]["overnight"][h])), ("without_stopped_not_judged", lambda i: T[i]["stopped"][h])):
        ids2 = [i for i in ids if not bad(i)]; picks2 = [i for i in picks if not bad(i)]
        j = judge(T, ids2, picks2, h, seed_tag, mult, side=False) if ids2 else {}
        out[name] = {k: j.get(k) for k in ("buys", "events", "mean", "mean_all_a", "minus_a", "random_p95_b")}
    out["overnight_flagged_trades"] = {i: T[i]["overnight"][h] for i in picks if T[i]["overnight"][h]}
    return out

def by_list(T, ids, picks, h, tag):
    U = {i: T[i]["list"] for i in ids}
    return {l: judge(T, [i for i in ids if U[i] == l], [i for i in picks if U[i] == l], h, f"{tag}-{l}") for l in C.LISTS if any(U[i] == l for i in ids)}

def agreement(A, ids):
    from scipy.stats import spearmanr
    yes = [[buy(A[r][i]) for r in SMALL] for i in ids]; n = len(SMALL); N = len(ids)
    p = sum(sum(y) for y in yes) / (N * n)
    Pi = [(sum(y) * (sum(y) - 1) + (n - sum(y)) * (n - sum(y) - 1)) / (n * (n - 1)) for y in yes]
    Pe = p * p + (1 - p) * (1 - p); Pbar = statistics.fmean(Pi)
    out = dict(unanimous_buy_or_skip=sum(len(set(y)) == 1 for y in yes) / N, fleiss_kappa_buy_skip=(Pbar - Pe) / (1 - Pe) if Pe < 1 else None,
               sent_to_strong=sum(disagree([A[r][i] for r in SMALL]) for i in ids) / N,
               buy_share={r: (sum(buy(A[r][i]) for i in ids if i in A[r]) / sum(i in A[r] for i in ids)) if any(i in A[r] for i in ids) else None for r in A},
               spearman={})
    rs = list(A)
    for x in range(len(rs)):
        for y in range(x + 1, len(rs)):
            both = [i for i in ids if i in A[rs[x]] and i in A[rs[y]]]   # the strong reader answers only part of the held-back half
            v = spearmanr([A[rs[x]][i] for i in both], [A[rs[y]][i] for i in both]).statistic if len(both) > 2 else None
            out["spearman"][f"{rs[x]}~{rs[y]}"] = None if v is None or math.isnan(v) else float(v)   # a constant reader has no rank correlation
    if STRONG in A:
        agreed = [i for i in ids if not disagree([A[r][i] for r in SMALL]) and i in A[STRONG]]   # held-back: the audited agreed events
        out["strong_agrees_with_agreed_small"] = sum(buy(A[STRONG][i]) == buy(sorted(A[r][i] for r in SMALL)[1]) for i in agreed) / len(agreed) if agreed else None
        out["strong_agreed_events_compared"] = len(agreed)
    return out

def remembered(H):
    return {name: v.get("remembered_set_to_zero") for name, v in H["files"].items()}

def dump(R, path):
    json.dump(R, open(path, "w"), indent=1, allow_nan=False)

# ------------------------------------------------------------------------------------------------ runs
def design(require_push=True):
    if exists_anywhere(DESIGN_OUT, require_push): raise Refused(f"refused: {DESIGN_OUT} exists here or in origin/main. The design sample is scored once.")
    if require_push: require_no_override(); require_frozen()
    H = check_hashes("design", SMALL + [STRONG], require_push)
    U = C.load_usable(); ids = sorted(U["design_sample"]); ev = [k for k in U["events"] if k["event_id"] in set(ids)]
    A = load_answers("design", SMALL + [STRONG])
    for r in A:
        if set(A[r]) != set(ids): raise Refused(f"refused: {r} did not answer exactly the design sample")
    T = trades(ev, C.trading_days())
    R = dict(made_by="research_rig/score_11.py --design", made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
             answers_hashes=H, config=config_now(),
             agreement=agreement(A, ids), remembered_set_to_zero=remembered(H), remembered_zeroed_events=zeroed("design", SMALL + [STRONG]),
             prices_read=prices_digest(ev), setups={}, gap_yardstick_c={})
    G = load_answers("design", SMALL + [STRONG], as_given=True)
    for s in DS["setups"]:
        sc = setup_scores(s, A, ids); picks = [i for i in ids if buy(sc[i])]
        gs = setup_scores(s, G, ids); gpk = [i for i in ids if buy(gs[i])]
        R["setups"][s] = {h: dict(judge(T, ids, picks, h, f"design-{s}"), by_list=by_list(T, ids, picks, h, f"design-{s}"),
                                  cost_sensitivity={str(m): judge(T, ids, picks, h, f"design-{s}", m, side=False)["minus_a"] for m in CO["sensitivity_multiples"]},
                                  scores_as_given_not_judged=as_given_line(T, ids, gpk, h, f"design-{s}"))
                          for h in ST["holds"]}
    gp = [i for i in ids if T[i]["gap_buy"]]
    R["gap_yardstick_c"] = {h: dict(judge(T, ids, gp, h, "design-gap"), by_list=by_list(T, ids, gp, h, "design-gap")) for h in ST["holds"]}
    main = ST["main_hold"]; ok = [s for s in DS["setups"] if DS["buy_share_min"] <= R["setups"][s][main]["buy_share"] <= DS["buy_share_max"]]
    R["qualified_setups"] = ok
    R["chosen_setup"] = max(ok, key=lambda s: (round(R["setups"][s][main]["minus_a"], 4), -DS["setups"].index(s))) if ok else None
    dump(R, os.path.join(out_dir(require_push), DESIGN_OUT))
    for s in DS["setups"]:
        x = R["setups"][s][main]; f = lambda v: None if v is None else round(100 * v, 2)
        print(f"{s:20s} buys {x['buys']:4d} share {x['buy_share']:.2f} minus_a {f(x['minus_a'])} | not judged: without overnight-flagged {f(x['without_overnight_flagged_not_judged']['minus_a'])}, without stopped {f(x['without_stopped_not_judged']['minus_a'])}, scores as given {f(x['scores_as_given_not_judged']['minus_a'])}")
    print("set to 0, remembers the move:", {r: len(v) for r, v in R["remembered_zeroed_events"].items()}); print("chosen:", R["chosen_setup"]); return R

def heldback(require_push=True):
    d = out_dir(require_push); out = os.path.join(d, HELDBACK_OUT)
    for name in (HELDBACK_OUT, HELDBACK_LOCK):
        if exists_anywhere(name, require_push): raise Refused(f"refused: {name} exists here or in origin/main. The held-back half is scored once.")
    if require_push: require_no_override(); require_frozen(); require_pushed(f"research_rig/{DESIGN_OUT}")
    D = json.load(open(os.path.join(d, DESIGN_OUT))); s = D["chosen_setup"]
    if s is None: raise Refused("refused: no set-up qualified on the design sample")
    if D.get("config") != config_now():
        raise Refused("refused: the replay_11_* keys differ from those the design run used")
    U = C.load_usable(); ev = [k for k in U["events"] if k["half"] == "heldback"]; ids = sorted(k["event_id"] for k in ev)
    need = SMALL if s == "middle" else SMALL + [STRONG] if s == "cascade" else [s]
    H = check_hashes("heldback", need, require_push)
    A = load_answers("heldback", need)
    for r in need:
        if r == STRONG and s == "cascade":
            dis, audit = cascade_strong_set(ids, A)
            if set(A[r]) != set(dis) | set(audit): raise Refused("refused: the strong reader did not answer exactly the disagreements and the audit")
        elif set(A[r]) != set(ids): raise Refused(f"refused: {r} did not answer every held-back event")
    days = C.trading_days(); prices_reach(ev, days)
    # the lock record is written before any held-back price is read, and is committed with the result
    open(os.path.join(d, HELDBACK_LOCK), "w").write(json.dumps(dict(started_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), chosen_setup=s)) + "\n")
    T = trades(ev, days); sc = setup_scores(s, A, ids); picks = [i for i in ids if buy(sc[i])]; gp = [i for i in ids if T[i]["gap_buy"]]
    R = dict(made_by="research_rig/score_11.py --heldback", made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
             chosen_setup=s, answers_hashes=H, remembered_set_to_zero=remembered(H), remembered_zeroed_events=zeroed("heldback", need),
             prices_read=prices_digest(ev), results={}, gap_yardstick_c={})
    G = load_answers("heldback", need, as_given=True); gs = setup_scores(s, G, ids); gpk = [i for i in ids if buy(gs[i])]
    for h in ST["holds"]:
        j = judge(T, ids, picks, h, f"heldback-{s}")
        j["pass"] = (j["buys"] >= ST["min_buys"] and j["mean"] > j["mean_all_a"] and j["mean"] > j["random_p95_b"]) if j["buys"] else False
        j["too_few_to_judge"] = j["buys"] < ST["min_buys"]
        j["by_list_not_judged"] = by_list(T, ids, picks, h, f"heldback-{s}")
        j["scores_as_given_not_judged"] = as_given_line(T, ids, gpk, h, f"heldback-{s}")
        j["cost_sensitivity"] = {str(m): judge(T, ids, picks, h, f"heldback-{s}", m, side=False)["minus_a"] for m in CO["sensitivity_multiples"]}
        R["results"][h] = j
        R["gap_yardstick_c"][h] = dict(judge(T, ids, gp, h, "heldback-gap"), by_list=by_list(T, ids, gp, h, "heldback-gap"))
    if len(need) > 1:
        R["agreement"] = agreement({r: {i: A[r][i] for i in ids if i in A[r]} for r in need}, ids)
        if s == "cascade": R["audit"] = dict(disagreements=len(dis), audit=len(audit), note="strong_agrees_with_agreed_small is over the audit, reported, not judged")
    R["main_hold"] = ST["main_hold"]; R["passes_main_hold"] = R["results"][ST["main_hold"]]["pass"]
    dump(R, out)
    for h, j in R["results"].items():
        print(h, "buys", j["buys"], "pass", j["pass"], "| not judged: without overnight-flagged", j["without_overnight_flagged_not_judged"]["minus_a"],
              "without stopped", j["without_stopped_not_judged"]["minus_a"], "scores as given", j["scores_as_given_not_judged"]["minus_a"], "| flagged", j["overnight_flagged"], "stopped", j["stopped"])
        for i, f in j["overnight_flagged_trades"].items(): print("  large overnight move inside the hold:", i, "; ".join(f))
    return R

if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a == ["--design"]: design()
        elif a == ["--heldback"]: heldback()
        else: print(__doc__); sys.exit(2)
    except Refused as e:
        print(e.code); sys.exit(1)
