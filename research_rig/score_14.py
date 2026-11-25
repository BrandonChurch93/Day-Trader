"""Scorer for plan 14: plain 12-month momentum (skipping the last month) on S&P 500 members by date, re-formed monthly,
two basket sizes, against SPY, every member in equal parts, and random baskets.

Usage, from research_rig/ (no setting is read from the command line; all come from replay_14_plan):
  python3 score_14.py --selftest   runs test_14.py on made-up data; free to run at any time
  python3 score_14.py --coverage   members, bars and rankable counts; reads whether a bar exists, never a price value;
                                   writes coverage_14.json
  python3 score_14.py --pins       prints the members hash, bar manifest hash and code commit the frozen plan must pin
  python3 score_14.py --run        the one real run (the lead runs it once, after the plan is frozen)

--run refuses:
  - if any of REPLAY_14_MEMBERS, REPLAY_14_BARS, RESULTS_14_DIR, REPLAY_14_LOCK_DIR is set (only the tests set them),
  - while the plan file named in replay_14_plan.source, or any PREREG_14_*.md here, has DRAFT in its name, or its
    Status line says DRAFT, or the plan file does not exist,
  - if the plan, config/thresholds.yaml, members list builder or this code differs from the last commit (git HEAD),
  - unless the plan pins members_sha256, bars_manifest_sha256, code_commit and config_sha256 (lines "name: value") and each equals
    the value now, so changed data or a committed code change after the freeze is refused,
  - if a data check (stale flat bars, file identity, one company counted twice; common_14.data_checks) flags a row
    that the plan does not list with a reason,
  - if score_14.lock exists here or in ~/workspace/rig/data/replay_14/, or results_14.json exists here. Both locks are
    taken after the checks and before any price is read.
It writes results_14.json with the command, the time, the git commit and the fingerprints of every input.

Definitions: plan 14, "Definitions fixed before the run" (agreed with the lead 2026-11-25). In short:
  - ranking day: each month-end from the lookback_months-th; gain = close one month-end before / close twelve
    month-ends before - 1, both on those exact days; top N bought in equal parts at the next day's open; ties by ticker.
  - one share class per company (first ticker alphabetically) in the rule and every yardstick.
  - (b) every member with a close on the ranking day and an open on the purchase day; (c) random_draws paths of N
    stocks from those the rule could rank that have an open, seed; turnover-matched (lead's decision on the opus audit,
    2026-11-25): at each re-form a path keeps exactly as many of its holdings as the rule kept, chosen at random, and
    draws the rest from the eligible stocks it did not hold; same costs and stop handling as the rule; above = strictly
    above the random_percentile-th percentile (numpy linear).
  - cost_bps_per_side on what is traded at each re-form, the first purchase, stop sales and the final sale; SPY pays
    one buy and one sell.
  - halves split at the first ranking day after first_half_end; SPY over the same open-to-open spans."""
import sys, os, json, subprocess, glob, datetime as dt
import numpy as np
import common_14 as C

P = C.P
OUT = "results_14.json"
LOCK = "score_14.lock"
CODE = ("research_rig/common_14.py", "research_rig/score_14.py", "research_rig/build_members_14.py", "research_rig/fetch_14.py",
        "research_rig/test_14.py", "research_rig/report_14.py")

class Refused(Exception): pass

# ------------------------------------------------------------------------------------------------------------ scoring
def plan_periods(members, px, days):
    """Ranking days, fill days, rankable lists and counts. Uses closes up to each ranking day and the open of the fill day."""
    R, me = C.ranking_index(days)
    out = []
    for i, k in R:
        ranked, unr = C.rankable(members, px, days, me, k)
        out.append(dict(i=i, k=k, fill=i + 1, ranked=ranked, unrankable=unr))
    return out, me

def run_setup(members, px, days, periods, n, daily=True, cost=None):
    fills = [p["fill"] for p in periods]
    baskets = [C.top_n(p["ranked"], px, p["fill"], n) for p in periods]
    sim = C.simulate(px, fills, baskets, P["cost_bps_per_side"] if cost is None else cost, daily=daily)
    sim["baskets"] = baskets
    return sim

def kept_counts(baskets, flags):
    """How many names the rule kept at each re-form: in this basket and in the last one, not stopped in between."""
    st = {}
    for k, s, _ in flags: st.setdefault(k, set()).add(s)
    return [0] + [len(set(baskets[k]) & (set(baskets[k - 1]) - st.get(k - 1, set()))) for k in range(1, len(baskets))]

def score(members, px, days, with_random=True, cost_bps=None):
    """Every judged and reported figure, from members, prices and the calendar. Used by the real run and the tests.
    cost_bps replaces the configured cost (only the no-edge check uses it, to measure the effect of cost)."""
    periods, me = plan_periods(members, px, days)
    fills = [p["fill"] for p in periods]; cost = P["cost_bps_per_side"] if cost_bps is None else cost_bps
    half_end = str(P["first_half_end"])
    k2 = next((j for j, p in enumerate(periods) if days[p["i"]] > half_end), len(periods))
    spy = px.si["SPY||"]
    spy_final, spy_units, spy_daily = C.hold_one(px, spy, fills[0], cost)
    c = cost / 1e4
    # SPY over the two halves, open to open, the buy charged in the first half and the sale in the second
    spy_mid = spy_units * px.O[spy, fills[k2]] if k2 < len(periods) else spy_final
    spy_h1, spy_h2 = spy_mid - 1.0, spy_final / spy_mid - 1.0

    def by_year(daily):
        out = {}; prev = 1.0
        for y in sorted({d[:4] for d in days[fills[0]:]}):
            idx = [t for t in range(fills[0], len(days)) if days[t][:4] == y]
            v = daily[idx[-1]]; out[y] = v / prev - 1.0; prev = v
        return out

    b_baskets = [C.everyone(members, px, days, p["i"], p["fill"]) for p in periods]
    B = C.simulate(px, fills, b_baskets, cost, daily=True)
    res = dict(first_ranking_day=days[periods[0]["i"]], last_ranking_day=days[periods[-1]["i"]],
               first_purchase_day=days[fills[0]], last_day=days[-1], ranking_days=len(periods),
               second_half_first_ranking_day=days[periods[k2]["i"]] if k2 < len(periods) else None,
               spy=dict(total=spy_final - 1.0, first_half=spy_h1, second_half=spy_h2, max_drop=C.max_drop(spy_daily),
                        by_year=by_year(spy_daily)),
               everyone=dict(total=B["value"] - 1.0, max_drop=C.max_drop(B["daily"]), by_year=by_year(B["daily"]),
                             mean_turnover=float(np.mean(B["turnover"][1:])) if len(B["turnover"]) > 1 else 0.0,
                             flagged=len(B["flags"]), mean_basket=float(np.mean([len(b) for b in b_baskets]))),
               scale={}, setups={},
               counts=dict(rankable=[len(p["ranked"]) for p in periods], unrankable=[len(p["unrankable"]) for p in periods],
                           ranking_days=[days[p["i"]] for p in periods]))
    for s in ("SPMO", "MTUM"):
        k = f"{s}||"
        if k in px.si and not np.isnan(px.O[px.si[k], fills[0]]):
            f_, _, d_ = C.hold_one(px, px.si[k], fills[0], cost); res["scale"][s] = dict(total=f_ - 1.0, max_drop=C.max_drop(d_))
        else: res["scale"][s] = None
    moves = C.period_moves(px, fills)
    by_s = {}
    for r in members:
        if r["series"] in px.si: by_s.setdefault(px.si[r["series"]], []).append(r)
    def label(s, day):
        """ticker_then of the member row on this series in force on that day (a series can carry several labels)."""
        rs = by_s.get(s, [])
        now = [r for r in rs if r["date_from"] <= day < r["date_to"]]
        return (now or sorted(rs, key=lambda r: r["date_from"])[-1:] or [dict(ticker_then=px.keys[s])])[0]["ticker_then"]
    for name, n in (("small", P["n_small"]), ("wide", P["n_wide"])):
        S = run_setup(members, px, days, periods, n, cost=cost)
        tot = S["value"] - 1.0
        h1 = S["at_fill"][k2] - 1.0 if k2 < len(periods) else tot
        h2 = S["value"] / S["at_fill"][k2] - 1.0 if k2 < len(periods) else float("nan")
        rnd = []
        if with_random:
            rng = np.random.default_rng([P["seed"], n])
            kept = kept_counts(S["baskets"], S["flags"])
            bk = C.random_baskets(periods, px, n, P["random_draws"], rng, kept=kept, stopped=moves[2])
            rnd = list(C.fast_values(moves, bk, cost) - 1.0)
        pct = float(np.percentile(rnd, P["random_percentile"])) if rnd else float("nan")
        marks = {"1_above_spy": bool(tot > res["spy"]["total"]),
                 "2_above_everyone": bool(tot > res["everyone"]["total"]),
                 "3_above_random_percentile": bool(rnd) and bool(tot > pct),
                 "4_above_spy_each_half": bool(h1 > spy_h1 and h2 > spy_h2)}
        flagged = sorted({s for _, s, _ in S["flags"]})
        # reported only: without every stock ever flagged in this set-up (hindsight)
        if flagged:
            drop = set(flagged)
            pr2 = [dict(p, ranked=[x for x in p["ranked"] if x[2] not in drop]) for p in periods]
            S2 = C.simulate(px, fills, [C.top_n(p["ranked"], px, p["fill"], n) for p in pr2], cost)
            without = S2["value"] - 1.0
        else: without = tot
        res["setups"][name] = dict(
            n=n, ledger_row=146 if name == "small" else 147, total=tot, first_half=h1, second_half=h2,
            random=dict(draws=len(rnd), percentile=P["random_percentile"], value_at_percentile=pct, turnover_matched=True,
                        rule_mean_kept=float(np.mean(kept[1:])) if with_random and len(kept) > 1 else float("nan"),
                        median=float(np.median(rnd)) if rnd else float("nan"),
                        share_of_draws_beaten=float(np.mean(np.array(rnd) < tot)) if rnd else float("nan")),
            marks=marks, passes=all(marks.values()),
            reported=dict(by_year=by_year(S["daily"]), max_drop=C.max_drop(S["daily"]),
                          mean_turnover=float(np.mean(S["turnover"][1:])) if len(S["turnover"]) > 1 else 0.0,
                          flagged_holdings=len(S["flags"]), carried_through_gap=len(S["carried"]),
                          flagged=[dict(ticker=label(s, days[periods[k]["i"]]), period_ranking_day=days[periods[k]["i"]], last_close_day=days[d])
                                   for k, s, d in S["flags"]],
                          total_without_flagged_hindsight=without,
                          short_baskets=sum(len(b) < n for b in S["baskets"]),
                          spmo_overlap="UNKNOWN: no dated public record of SPMO's holdings was found"),
            carried=[dict(ticker=label(s, days[periods[k]["i"]]), period_ranking_day=days[periods[k]["i"]]) for k, s in S["carried"]],
            picks={days[p["i"]]: [label(s, days[p["i"]]) for s in b] for p, b in zip(periods, S["baskets"])})
    return res

# ----------------------------------------------------------------------------------------------------------- coverage
def coverage(members, px, days):
    """Counts only: whether bars exist. No price value is used."""
    me = C.month_end_index(days)
    by_ent_start = {(r["entity"], r["date_from"]) for r in members}
    years = sorted({d[:4] for d in days}); idx = {d: i for i, d in enumerate(days)}
    nobars = {y: [] for y in years}; stops = []; stops_nobar = []
    for r in members:
        s = px.si.get(r["series"]) if r["series"] else None
        for y in years:
            a = max(r["date_from"], f"{y}-01-01"); b = min(r["date_to"], f"{int(y) + 1}-01-01")
            span = [i for d, i in idx.items() if a <= d < b]
            if not span: continue
            if s is None or np.isnan(px.C[s, span]).all(): nobars[y].append(r["ticker_then"])
        removed = r["date_to"] <= days[-1] and (r["entity"], r["date_to"]) not in by_ent_start
        if removed and s is not None:
            prior = [i for d, i in idx.items() if d < r["date_to"]]
            want = max(prior) if prior else None
            last = int(px.last[s])
            inside = [i for d, i in idx.items() if r["date_from"] <= d < r["date_to"]]
            priced = bool(inside) and not np.isnan(px.C[s, inside]).all()
            if want is not None and last < want and last >= 0:
                (stops if priced else stops_nobar).append(dict(ticker=r["ticker_then"], feed=r["ticker_feed"], removed=r["date_to"],
                                  last_bar=days[last], trading_days_short=want - last))
            elif last < 0 and r["date_from"] <= days[-1]: pass
    periods, _ = plan_periods(members, px, days)
    return dict(month_end_lines=[dict(day=days[i], lines=len(C.members_on(members, days[i])),
                                      one_class=len(C.one_class(C.members_on(members, days[i]))),
                                      with_series=len(C.universe(members, px, days[i]))) for i in me],
                lines_without_bars_by_year={y: dict(count=len(v), tickers=sorted(set(v))) for y, v in nobars.items()},
                bars_stop_before_removal=sorted(stops, key=lambda x: x["removed"]),
                bars_stop_before_removal_by_days_short={str(k): sum(x["trading_days_short"] == k for x in stops) for k in sorted({x["trading_days_short"] for x in stops})},
                stop_lines_with_no_bar_in_membership=sorted(stops_nobar, key=lambda x: x["removed"]),
                companies_on_two_files=two_files(members),
                ranking_days=[dict(day=days[p["i"]], rankable=len(p["ranked"]), unrankable=len(p["unrankable"]), unrankable_tickers=p["unrankable"]) for p in periods],
                lines=len(members), series=len(px.keys))

def two_files(members):
    """Companies whose rows use more than one price file: files are never joined, so the history restarts."""
    from build_members_14 import A_ROW_RENAMES          # same company where source A has a removal and an addition
    ent = {r["entity"]: r["entity"] for r in members}
    def root(e):
        while ent[e] != e: e = ent[e]
        return e
    for o, n_, d in A_ROW_RENAMES:
        a = [r["entity"] for r in members if r["ticker_then"] == o and r["date_to"] == d]
        b = [r["entity"] for r in members if r["ticker_then"] == n_ and r["date_from"] == d]
        if a and b: ent[root(b[0])] = root(a[0])
    by = {}
    for r in members:
        if r["ticker_feed"]: by.setdefault(root(r["entity"]), []).append(r)
    out = []
    for e, rs in by.items():
        rs.sort(key=lambda r: r["date_from"]); files = list(dict.fromkeys(r["ticker_feed"] for r in rs))
        if len(files) > 1:
            out.append(dict(company=rs[-1]["company"], files=files,
                            restarts=[min(r["date_from"] for r in rs if r["ticker_feed"] == f) for f in files[1:]]))
    return sorted(out, key=lambda x: x["restarts"][0])

# ------------------------------------------------------------------------------------------------------------- guards
PINS = ("members_sha256", "bars_manifest_sha256", "code_commit", "config_sha256")

def pins_now(members):
    """What the frozen plan must pin: the member list hash, a manifest hash over every bar file the run can read
    (name and sha256 of each), and the last commit that touched the code or the config."""
    files = sorted({r["ticker_feed"] for r in members if r["ticker_feed"]} | set(C.SCALE))
    h = __import__("hashlib").sha256()
    names = [os.path.join(C.BARS, f + ".csv") for f in files]
    names += [os.path.join(C.ASOF, f) for f in sorted(os.listdir(C.ASOF))] if os.path.isdir(C.ASOF) else []
    for p in names:
        f = os.path.relpath(p, os.path.dirname(C.BARS))
        h.update(f.encode() + b"\0" + (C.sha256_file(p) if os.path.exists(p) else "missing").encode() + b"\n")
    commit = git("log", "-1", "--format=%H", "--", "config/thresholds.yaml", *CODE).stdout.strip()
    return dict(members_sha256=C.sha256_file(C.MEMBERS), bars_manifest_sha256=h.hexdigest(), code_commit=commit,
                config_sha256=C.sha256_json(P))

def git(*a): return subprocess.run(["git", *a], cwd=C.REPO, capture_output=True, text=True)

def plan_file():
    p = os.path.join(C.REPO, C.PLAN_SOURCE)
    others = glob.glob(os.path.join(C.HERE, "PREREG_14_*.md"))
    return p, others

def guard_run():
    on = [v for v in C.ENV_OVERRIDES if v in os.environ]
    if on: raise Refused(f"refused: {', '.join(on)} set. A real run reads only the default files.")
    p, others = plan_file()
    for q in [p] + others:
        if "DRAFT" in os.path.basename(q).upper(): raise Refused(f"refused: the plan file {os.path.relpath(q, C.REPO)} is still a draft (DRAFT in its name). Freeze it first.")
    if not os.path.exists(p): raise Refused(f"refused: the plan file {C.PLAN_SOURCE} named in replay_14_plan.source does not exist")
    status = next((l for l in open(p) if l.lower().startswith("status:")), "")
    if not status or "DRAFT" in status.upper() or "frozen" not in status.lower():
        raise Refused("refused: the plan's Status line does not say frozen (or still says DRAFT)")
    rels = [C.PLAN_SOURCE, "config/thresholds.yaml", *CODE]
    dirty = git("status", "--porcelain", "--", *rels).stdout.strip()
    if dirty: raise Refused("refused: these differ from the last commit; commit them first:\n" + dirty)
    with open(p) as fh: text = fh.read()
    members = C.load_members(); now = pins_now(members)
    for k in PINS:
        line = next((l for l in text.splitlines() if l.strip().lstrip("-* ").startswith(k + ":")), None)
        if line is None: raise Refused(f"refused: the plan does not pin {k}. Print the values with: python3 score_14.py --pins")
        if line.split(":", 1)[1].strip().strip("`") != now[k]:
            raise Refused(f"refused: {k} differs from the value pinned in the plan (data or code changed after the freeze)")
    unlisted = C.flags_listed(C.data_checks(members, C.calendar()), text)
    if unlisted: raise Refused("refused: data check flags not listed in the plan with a reason (a line with the key and 'because'): " + ", ".join(unlisted))
    for d in (C.HERE, C.OFF_REPO_LOCK_DIR):
        if os.path.exists(os.path.join(d, LOCK)): raise Refused(f"refused: {os.path.join(d, LOCK)} exists; the one run has been taken")
    if os.path.exists(os.path.join(C.HERE, OUT)): raise Refused(f"refused: {OUT} exists; the one run has been taken")

def take_locks(cmd):
    stamp = dict(command=cmd, utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), commit=git("rev-parse", "HEAD").stdout.strip())
    made = []
    for d in (C.HERE, C.OFF_REPO_LOCK_DIR):
        fd = os.open(os.path.join(d, LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, (json.dumps(stamp) + "\n").encode()); os.close(fd); made.append(os.path.join(d, LOCK))
    return stamp

def fingerprints(px, members):
    return dict(pins=pins_now(members), members_csv_sha256=C.sha256_file(C.MEMBERS), bars=px.digest(), plan_sha256=C.sha256_file(os.path.join(C.REPO, C.PLAN_SOURCE)),
                config_replay_14_plan_sha256=C.sha256_json(P), config_replay_14_plan=P,
                code_sha256={rel: C.sha256_file(os.path.join(C.REPO, rel)) for rel in CODE})

def real_run():
    guard_run()
    cmd = " ".join(["python3"] + sys.argv)
    stamp = take_locks(cmd)                                    # before any price is read
    days = C.calendar(); members = C.load_members()
    px = C.Prices(days, members)
    res = score(members, px, days)
    out = dict(made_by="research_rig/score_14.py --run", plan=C.PLAN_SOURCE, run=stamp,
               finished_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
               inputs=fingerprints(px, members), coverage=coverage(members, px, days), data_checks=C.data_checks(members, days), result=res)
    json.dump(out, open(os.path.join(C.HERE, OUT), "w"), indent=1, default=float)
    print(f"wrote research_rig/{OUT}. Write the page with: python3 report_14.py")

def coverage_mode():
    days = C.calendar(); members = C.load_members()
    px = C.Prices(days, members)
    cov = coverage(members, px, days)
    cov["made_by"] = "research_rig/score_14.py --coverage (counts only, no price value used)"
    cov["data_checks"] = C.data_checks(members, days)
    json.dump(cov, open(os.path.join(C.OUTDIR, "coverage_14.json"), "w"), indent=1)
    me = cov["month_end_lines"]; R = cov["ranking_days"]
    print(json.dumps(dict(lines=cov["lines"], series=cov["series"],
                          month_end_lines=[min(m["lines"] for m in me), max(m["lines"] for m in me)],
                          one_class_with_series=[min(m["with_series"] for m in me), max(m["with_series"] for m in me)],
                          lines_without_bars_by_year={y: v["count"] for y, v in cov["lines_without_bars_by_year"].items()},
                          bars_stop_before_removal=len(cov["bars_stop_before_removal"]),
                          by_days_short=cov["bars_stop_before_removal_by_days_short"],
                          stop_lines_with_no_bar_in_membership=[x["ticker"] for x in cov["stop_lines_with_no_bar_in_membership"]],
                          companies_on_two_files=len(cov["companies_on_two_files"]),
                          data_checks={k: len(v) for k, v in cov["data_checks"].items()},
                          rankable=[min(r["rankable"] for r in R), max(r["rankable"] for r in R)],
                          unrankable=[min(r["unrankable"] for r in R), max(r["unrankable"] for r in R)]), indent=1))

if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a == ["--selftest"]:
            sys.exit(subprocess.run([sys.executable, os.path.join(C.HERE, "test_14.py")]).returncode)
        elif a == ["--coverage"]: coverage_mode()
        elif a == ["--pins"]: print(json.dumps(pins_now(C.load_members()), indent=1))
        elif a == ["--run"]: real_run()
        else: print(__doc__); sys.exit(2)
    except Refused as e:
        print(e); sys.exit(3)
