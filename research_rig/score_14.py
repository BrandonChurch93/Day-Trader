"""Scorer for plan 14: plain 12-month momentum (skipping the last month) on S&P 500 members by date, re-formed monthly,
two basket sizes, against SPY, every member in equal parts, and random baskets.

Usage, from research_rig/ (no setting is read from the command line; all come from replay_14_plan):
  python3 score_14.py --selftest   runs test_14.py on made-up data; free to run at any time
  python3 score_14.py --coverage   members, bars and rankable counts; reads whether a bar exists, never a price value;
                                   writes coverage_14.json
  python3 score_14.py --run        the one real run (the lead runs it once, after the plan is frozen)

--run refuses:
  - if any of REPLAY_14_MEMBERS, REPLAY_14_BARS, RESULTS_14_DIR, REPLAY_14_LOCK_DIR is set (only the tests set them),
  - while the plan file named in replay_14_plan.source, or any PREREG_14_*.md here, has DRAFT in its name, or its
    Status line says DRAFT, or the plan file does not exist,
  - if the plan, config/thresholds.yaml, members list builder or this code differs from the last commit (git HEAD),
  - if score_14.lock exists here or in ~/workspace/rig/data/replay_14/, or results_14.json exists here. Both locks are
    taken after the checks and before any price is read.
It writes results_14.json with the command, the time, the git commit and the fingerprints of every input.

Definitions: plan 14, "Definitions fixed before the run" (agreed with the lead 2026-11-25). In short:
  - ranking day: each month-end from the lookback_months-th; gain = close one month-end before / close twelve
    month-ends before - 1, both on those exact days; top N bought in equal parts at the next day's open; ties by ticker.
  - one share class per company (first ticker alphabetically) in the rule and every yardstick.
  - (b) every member with a close on the ranking day and an open on the purchase day; (c) N drawn from the stocks the
    rule could rank, random_draws paths, seed, a fresh draw each month in each path; above = strictly above the
    random_percentile-th percentile (numpy linear).
  - cost_bps_per_side on what is traded at each re-form, the first purchase, stop sales and the final sale; SPY pays
    one buy and one sell.
  - halves split at the first ranking day after first_half_end; SPY over the same open-to-open spans."""
import sys, os, json, subprocess, glob, datetime as dt
import numpy as np
import common_14 as C

P = C.P
OUT = "results_14.json"
LOCK = "score_14.lock"
CODE = ("research_rig/common_14.py", "research_rig/score_14.py", "research_rig/build_members_14.py", "research_rig/fetch_14.py")

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

def run_setup(members, px, days, periods, n, daily=True):
    fills = [p["fill"] for p in periods]
    baskets = [C.top_n(p["ranked"], px, p["fill"], n) for p in periods]
    sim = C.simulate(px, fills, baskets, P["cost_bps_per_side"], daily=daily)
    sim["baskets"] = baskets
    return sim

def score(members, px, days, with_random=True):
    """Every judged and reported figure, from members, prices and the calendar. Used by the real run and the tests."""
    periods, me = plan_periods(members, px, days)
    fills = [p["fill"] for p in periods]; cost = P["cost_bps_per_side"]
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
    tick = {px.si[r["series"]]: r["ticker_then"] for r in members if r["series"] in px.si}
    for name, n in (("small", P["n_small"]), ("wide", P["n_wide"])):
        S = run_setup(members, px, days, periods, n)
        tot = S["value"] - 1.0
        h1 = S["at_fill"][k2] - 1.0 if k2 < len(periods) else tot
        h2 = S["value"] / S["at_fill"][k2] - 1.0 if k2 < len(periods) else float("nan")
        rnd = []
        if with_random:
            rng = np.random.default_rng([P["seed"], n])
            bk = C.random_baskets(periods, px, n, P["random_draws"], rng)
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
            random=dict(draws=len(rnd), percentile=P["random_percentile"], value_at_percentile=pct,
                        median=float(np.median(rnd)) if rnd else float("nan"),
                        share_of_draws_beaten=float(np.mean(np.array(rnd) < tot)) if rnd else float("nan")),
            marks=marks, passes=all(marks.values()),
            reported=dict(by_year=by_year(S["daily"]), max_drop=C.max_drop(S["daily"]),
                          mean_turnover=float(np.mean(S["turnover"][1:])) if len(S["turnover"]) > 1 else 0.0,
                          flagged_holdings=len(S["flags"]), carried_through_gap=len(S["carried"]),
                          flagged=[dict(ticker=tick.get(s, px.keys[s]), period_ranking_day=days[periods[k]["i"]], last_close_day=days[d])
                                   for k, s, d in S["flags"]],
                          total_without_flagged_hindsight=without,
                          short_baskets=sum(len(b) < n for b in S["baskets"]),
                          spmo_overlap="UNKNOWN: no dated public record of SPMO's holdings was found"),
            picks={days[p["i"]]: [tick.get(s, px.keys[s]) for s in b] for p, b in zip(periods, S["baskets"])})
    return res

# ----------------------------------------------------------------------------------------------------------- coverage
def coverage(members, px, days):
    """Counts only: whether bars exist. No price value is used."""
    me = C.month_end_index(days)
    by_ent_start = {(r["entity"], r["date_from"]) for r in members}
    years = sorted({d[:4] for d in days}); idx = {d: i for i, d in enumerate(days)}
    nobars = {y: [] for y in years}; stops = []
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
            if want is not None and last < want and last >= 0:
                stops.append(dict(ticker=r["ticker_then"], feed=r["ticker_feed"], removed=r["date_to"],
                                  last_bar=days[last], trading_days_short=want - last))
            elif last < 0 and r["date_from"] <= days[-1]: pass
    periods, _ = plan_periods(members, px, days)
    return dict(month_end_lines=[dict(day=days[i], lines=len(C.members_on(members, days[i])),
                                      one_class=len(C.one_class(C.members_on(members, days[i]))),
                                      with_series=len(C.universe(members, px, days[i]))) for i in me],
                lines_without_bars_by_year={y: dict(count=len(v), tickers=sorted(set(v))) for y, v in nobars.items()},
                bars_stop_before_removal=sorted(stops, key=lambda x: x["removed"]),
                ranking_days=[dict(day=days[p["i"]], rankable=len(p["ranked"]), unrankable=len(p["unrankable"]), unrankable_tickers=p["unrankable"]) for p in periods],
                lines=len(members), series=len(px.keys))

# ------------------------------------------------------------------------------------------------------------- guards
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

def fingerprints(px):
    return dict(members_csv_sha256=C.sha256_file(C.MEMBERS), bars=px.digest(), plan_sha256=C.sha256_file(os.path.join(C.REPO, C.PLAN_SOURCE)),
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
               inputs=fingerprints(px), coverage=coverage(members, px, days), result=res)
    json.dump(out, open(os.path.join(C.HERE, OUT), "w"), indent=1, default=float)
    print(f"wrote research_rig/{OUT}. Write the page with: python3 report_14.py")

def coverage_mode():
    days = C.calendar(); members = C.load_members()
    px = C.Prices(days, members)
    cov = coverage(members, px, days)
    cov["made_by"] = "research_rig/score_14.py --coverage (counts only, no price value used)"
    json.dump(cov, open(os.path.join(C.OUTDIR, "coverage_14.json"), "w"), indent=1)
    me = cov["month_end_lines"]; R = cov["ranking_days"]
    print(json.dumps(dict(lines=cov["lines"], series=cov["series"],
                          month_end_lines=[min(m["lines"] for m in me), max(m["lines"] for m in me)],
                          one_class_with_series=[min(m["with_series"] for m in me), max(m["with_series"] for m in me)],
                          lines_without_bars_by_year={y: v["count"] for y, v in cov["lines_without_bars_by_year"].items()},
                          bars_stop_before_removal=len(cov["bars_stop_before_removal"]),
                          rankable=[min(r["rankable"] for r in R), max(r["rankable"] for r in R)],
                          unrankable=[min(r["unrankable"] for r in R), max(r["unrankable"] for r in R)]), indent=1))

if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a == ["--selftest"]:
            sys.exit(subprocess.run([sys.executable, os.path.join(C.HERE, "test_14.py")]).returncode)
        elif a == ["--coverage"]: coverage_mode()
        elif a == ["--run"]: real_run()
        else: print(__doc__); sys.exit(2)
    except Refused as e:
        print(e); sys.exit(3)
