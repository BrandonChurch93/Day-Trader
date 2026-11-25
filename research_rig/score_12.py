"""Scorer for plan 12: following stock purchases disclosed by members of Congress, as a calendar portfolio against SPY.

Usage, from research_rig/ (the lead runs --design and --heldback, once each):
  python3 score_12.py --counts     events and missing prices, counts and dates only; reads bar dates, no price value
  python3 score_12.py --design     scores the nine set-ups on the design half; writes results_12_design.json with the
                                   chosen set-up; refuses a second run
  python3 score_12.py --heldback   scores the chosen set-up once on the held-back half; refuses a second run
  python3 score_12.py --selftest   runs test_12.py on made-up data; free to run at any time

Both real modes refuse:
  - if any of CONGRESS_12_TRADES, CONGRESS_12_DETAILS, CONGRESS_12_BARS, RESULTS_12_DIR is set (only the tests set them),
  - unless the plan is research_rig/PREREG_12_congress_followers.md and is in origin/main byte for byte, and the
    replay_12_plan config value equals origin/main's,
  - --design: if results_12_design.json or score_12_design.lock exists here or in origin/main. The lock is written after
    the checks and before any price is read. Every price file is cut at the last day a design event or a design random
    draw can need, so no held-back event's price is read,
  - --heldback: if results_12_heldback.json or score_12_heldback.lock exists here or in origin/main, unless
    results_12_design.json is in origin/main byte for byte, and unless the trades files and config are the ones the
    design run used. The lock is written before any price is read.

Definitions (agreed with the lead 2026-11-25, written into the plan's "Definitions fixed before the run"):
  - entry versions: main (first trading day after the filing day), late5 (+late_entry_trading_days trading days),
    cal30 (first trading day after filing day + late_entry_calendar_days). Every result is worked out all three ways.
  - an event is in the held-back half for hold N if it is filed from heldback_filed_from and its hold finishes by the
    last price day in all three versions.
  - SPY over the same days: a mirror with the same weights, each stock swapped for SPY. No cost on the mirror.
  - per-year excess: (portfolio growth / mirror growth) ** (252 / days) - 1. The design run chooses the set-up with the
    largest, main entry.
  - proven members: refreshes every proven_refresh_days trading days from the first trading day of the half. At each,
    the proven_top_members members with at least proven_min_events purchases filed in the proven_lookback_days calendar
    days before the refresh day and exited before it, ranked by their mean (stock return - SPY return) per event, entry
    open to exit close, at the set-up's own hold and entry version, no cost. Ties go by name. The list applies to events
    filed from that refresh day to the next; events filed before the first refresh day use the first list. Sales of the
    same members while on the list make the sales side.
  - costs: replay_12_plan.cost_bps_per_side on daily turnover (judged); entries and exits only (not judged).
  - a stock whose bars stop inside the hold is sold at its last close, flagged and counted; an event with no bar on its
    entry day is left out and counted.
  - pass on the held-back half: (1) growth above the SPY mirror's, (2) bootstrap 5th percentile of the mean monthly
    difference above 0, (3) per-year excess above the same group's sales portfolio's, (4) at least min_events traded
    purchase events, (5) with the late5 entry, growth still above the SPY mirror's."""
import sys, os, json, subprocess, hashlib, datetime as dt
import numpy as np
import yaml
import common_12 as C

P = C.P
FROZEN_PLAN = "research_rig/PREREG_12_congress_followers.md"
FROZEN_CODE = ("research_rig/score_12.py", "research_rig/common_12.py", "research_rig/renames_12.csv")
DESIGN_OUT, DESIGN_LOCK = "results_12_design.json", "score_12_design.lock"
HELDBACK_OUT, HELDBACK_LOCK = "results_12_heldback.json", "score_12_heldback.lock"
GROUPS = ("all", "large", "proven")
HOLDS = tuple(P["holds_days"])
SETUPS = [(g, n) for g in GROUPS for n in HOLDS]

class Refused(Exception): pass

# ------------------------------------------------------------------------------------------------------------- guards
def pushed_bytes(rel):
    if subprocess.run(["git", "fetch", "--quiet", "origin", "main"], cwd=C.REPO).returncode: raise Refused("refused: git fetch origin main failed")
    r = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=C.REPO, capture_output=True)
    return r.stdout if r.returncode == 0 else None

def require_pushed(rel):
    p = os.path.join(C.REPO, rel)
    if not os.path.exists(p): raise Refused(f"refused: {rel} does not exist")
    if pushed_bytes(rel) != open(p, "rb").read(): raise Refused(f"refused: {rel} is not in origin/main as it is here. Commit and push it first.")

def require_no_override():
    on = [v for v in C.ENV_OVERRIDES if v in os.environ]
    if on: raise Refused(f"refused: {', '.join(on)} set. A real run reads only the default files.")

def require_frozen():
    if not os.path.exists(os.path.join(C.REPO, FROZEN_PLAN)): raise Refused(f"refused: {FROZEN_PLAN} does not exist. Freeze the plan first.")
    require_pushed(FROZEN_PLAN)
    for rel in FROZEN_CODE: require_pushed(rel)
    pushed = pushed_bytes("config/thresholds.yaml")
    if pushed is None or (yaml.safe_load(pushed).get("replay_12_plan") or {}).get("value") != P:
        raise Refused("refused: replay_12_plan differs from origin/main")

def out_dir(real): return C.HERE if real else C.OUTDIR

def exists_anywhere(name, real):
    return os.path.exists(os.path.join(out_dir(real), name)) or (real and pushed_bytes(f"research_rig/{name}") is not None)

def lock(path, what):
    open(path, "w").write(json.dumps(dict(started_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), mode=what)) + "\n")

def inputs():
    """The trades files, the rename list and the scoring code. --heldback refuses unless these equal the design run's."""
    return dict(trades_sha256=C.sha256_file(C.TRADES), details_sha256=C.sha256_file(C.DETAILS),
                renames_sha256=C.sha256_file(C.RENAMES_FILE), score_12_sha256=C.sha256_file(os.path.join(C.HERE, "score_12.py")),
                common_12_sha256=C.sha256_file(os.path.join(C.HERE, "common_12.py")))

# ------------------------------------------------------------------------------------------------------------- events
def halves(E):
    d = [e for e in E if P["design_filed_from"] <= e["filed"] <= P["design_filed_to"]]
    h = [e for e in E if e["filed"] >= P["heldback_filed_from"]]
    return d, h

def named_members(rows):
    """Each name in replay_12_plan.named_members matched as whole words in the full names of trades.csv. Stops unless
    each matches exactly one member."""
    out = {}
    for n, hit in named_matches(rows).items():
        if len(hit) != 1: raise Refused(f"refused: named member {n!r} matches {len(hit)} members: {list(hit)[:5]}")
        (m, k), = hit.items(); out[n] = dict(member=m, rows=k)
    return out

def named_matches(rows):
    """Every member whose full name has the surname as whole words, with row counts. --counts prints these and does
    not stop, so a list with a name that matches zero or two members can be seen and fixed."""
    import re
    names = sorted({r["member"] for r in rows})
    return {n: {m: sum(r["member"] == m for r in rows) for m in names if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", m)}
            for n in P.get("named_members", [])}

def cut_day(days, E):
    """The last trading day a design event can need: the latest filing, plus the widest random draw, the later entry
    version and the longest hold."""
    last = max(e["filed"] for e in E)
    o = C.ordinal(last) + P["random_date_window_days"]
    import numpy as np
    ords = np.array([C.ordinal(d) for d in days])
    a = max(int(np.searchsorted(ords, o, "right")) + P["late_entry_trading_days"], int(np.searchsorted(ords, o + P["late_entry_calendar_days"], "right")))
    return min(a + max(HOLDS), len(days))          # days[:cut] are loaded

# ------------------------------------------------------------------------------------------------------------- groups
def proven_lists(px, ev, n, variant, half_start, last_day=None):
    """The proven-member lists of a half, from the purchases in ev. At each refresh day R (every proven_refresh_days
    trading days from the half's first trading day): members with at least proven_min_events purchases filed in the
    proven_lookback_days calendar days before R and exited before R, ranked by mean (stock - SPY) per event; the top
    proven_top_members. Nothing on or after R is used. last_day: no refresh after it (the design run passes
    design_filed_to, so no list is built from held-back filings)."""
    tr = C.trades(px, ev, n, variant); ok = tr["status"] == C.TRADED; spy = px.si["SPY"]
    exc = np.full(len(ev), np.nan); k = np.where(ok)[0]
    exc[k] = (px.CF[ev.sym[k], tr["b"][k]] / px.O[ev.sym[k], tr["a"][k]]) - (px.CF[spy, tr["b"][k]] / px.O[spy, tr["a"][k]])
    i0 = int(np.searchsorted(px.ord, C.ordinal(half_start), "left")); lists = []
    for R in range(i0, px.n, P["proven_refresh_days"]):
        if last_day is not None and px.ord[R] > C.ordinal(last_day): break
        cand = ok & (ev.filed < px.ord[R]) & (ev.filed >= px.ord[R] - P["proven_lookback_days"]) & (tr["b"] < R)
        st = {}
        for j in np.where(cand)[0]: st.setdefault(ev.members[ev.member[j]], []).append(exc[j])
        good = sorted(((m, float(np.mean(v))) for m, v in st.items() if len(v) >= P["proven_min_events"]), key=lambda x: (-x[1], x[0]))
        lists.append(dict(day=px.days[R], members=[m for m, _ in good[:P["proven_top_members"]]], candidates=len(good)))
    return lists

def on_list(ev, lists, within):
    """Events filed while their member is on the list: the latest refresh on or before the filing day, else the first."""
    if not lists: return np.zeros(len(ev), bool)
    r = np.array([C.ordinal(L["day"]) for L in lists]); pos = np.maximum(np.searchsorted(r, ev.filed, "right") - 1, 0)
    sets = [set(L["members"]) for L in lists]
    return np.array([ev.members[ev.member[j]] in sets[pos[j]] for j in range(len(ev))], bool) & within

def group_mask(px, ev, group, n, variant, half_start, within, lists=None):
    if group == "all": return within.copy()
    if group == "large": return within & ev.large
    return on_list(ev, lists, within)

# ------------------------------------------------------------------------------------------------------------- results
def strip(S):
    S = dict(S); d = S.pop("monthly_diff", None); return S

def run(px, ev, mask, n, variant, by="member", filed_ord=None):
    tr = C.trades(px, ev, n, variant, filed_ord)
    k = mask & (tr["status"] == C.TRADED)
    pos = C.merge(ev.member[k], ev.sym[k], tr["a"][k], tr["b"][k], by)
    pf = C.portfolio(px, *pos, by=by, cost=P["cost_bps_per_side"])
    return tr, k, pf

def judged(px, ev, mask, n, variant, seed_tag):
    tr, k, pf = run(px, ev, mask, n, variant)
    S = C.summarize(px, pf)
    S["bootstrap_block_months"] = C.block_months(n)
    S["bootstrap_p5_monthly_diff"] = C.bootstrap_p5(S["monthly_diff"], P["bootstrap_draws"], P["bootstrap_seed"], S["bootstrap_block_months"])
    S["qqq_for_scale"] = C.scale(pf, "QQQ"); S["nanc_for_scale"] = C.scale(pf, "NANC")
    in_g = mask & (tr["status"] != C.UNFINISHED)
    S["events"] = dict(in_group=int(in_g.sum()), traded=int(k.sum()), no_price=int((mask & (tr["status"] == C.NOPRICE)).sum()),
                       no_price_share=float((mask & (tr["status"] == C.NOPRICE)).sum() / in_g.sum()) if in_g.sum() else None,
                       stopped=int((k & tr["stopped"]).sum()),
                       no_price_by_year={str(y): int((mask & (tr["status"] == C.NOPRICE) & (ev.year == y)).sum()) for y in sorted(set(ev.year[in_g]))})
    return strip(S), S, tr, k

def side(px, ev, mask, n, variant, by="member"):
    _, k, pf = run(px, ev, mask, n, variant, by)
    S = strip(C.summarize(px, pf)); S["traded_events"] = int(k.sum()); return S

def random_days(px, ev, mask, n, variant, tag):
    """Yardstick (c): the same stocks, each filing day moved by a whole number of calendar days drawn from
    -random_date_window_days..+random_date_window_days, random_date_draws times. Not judged."""
    h = int(hashlib.sha256(f"{P['bootstrap_seed']}-c-{tag}".encode()).hexdigest()[:12], 16)
    rng = np.random.default_rng(h); w = P["random_date_window_days"]; out = []
    for _ in range(P["random_date_draws"]):
        f = ev.filed + rng.integers(-w, w + 1, size=len(ev))
        _, k, pf = run(px, ev, mask, n, variant, filed_ord=f)
        S = C.summarize(px, pf); out.append(S["per_year_excess"])
    v = np.array([x for x in out if x is not None])
    return dict(draws=len(out), with_days=len(v), mean_per_year_excess=float(v.mean()) if len(v) else None,
                p5=float(np.percentile(v, 5)) if len(v) else None, p95=float(np.percentile(v, 95)) if len(v) else None, values=v)

def setup(px, B, S_, g, n, variant, half_start, in_b, in_s, with_random=True, last_day=None):
    """Everything for one set-up and entry version: the judged portfolio and every side line."""
    lists = proven_lists(px, B, n, variant, half_start, last_day) if g == "proven" else None
    mb = group_mask(px, B, g, n, variant, half_start, in_b, lists); ms = group_mask(px, S_, g, n, variant, half_start, in_s, lists)
    J, Jfull, tr, k = judged(px, B, mb, n, variant, f"{g}-{n}-{variant}")
    out = dict(judged=J)
    out["sales_b"] = side(px, S_, ms, n, variant)
    out["by_stock_not_judged"] = side(px, B, mb, n, variant, by="stock")
    counts = np.bincount(B.member[mb], minlength=len(B.members)); busy = int(counts.argmax()) if counts.any() else None
    out["without_busiest_member_not_judged"] = dict(member=B.members[busy] if busy is not None else None, **side(px, B, mb & (B.member != busy), n, variant))
    out["without_call_or_exercise_rows_not_judged"] = dict(events_left_out=int((mb & B.call_rows).sum()), **side(px, B, mb & ~B.call_rows, n, variant))
    out["without_stopped_not_judged"] = side(px, B, mb & ~(k & tr["stopped"]), n, variant)
    if with_random:
        rd = random_days(px, B, mb, n, variant, f"{g}-{n}-{variant}")
        real = J["per_year_excess"]
        out["random_days_c_not_judged"] = dict({x: v for x, v in rd.items() if x != "values"},
                                               share_of_draws_at_or_above_real=float((rd["values"] >= real).mean()) if real is not None and len(rd["values"]) else None)
    if lists is not None: out["proven_lists"] = lists
    return out, Jfull, mb, tr

def largest(px, ev, tr, k, m=20):
    """The m largest single-event returns, by size either way, entry open to exit close, with ticker and dates."""
    j = np.where(k)[0]
    r = px.CF[ev.sym[j], tr["b"][j]] / px.O[ev.sym[j], tr["a"][j]] - 1
    o = j[np.argsort(-np.abs(r))[:m]]; rr = dict(zip(j, r))
    return [dict(ticker=ev.E[i]["ticker"], member=ev.E[i]["member"], filed=ev.E[i]["filed"], entry=px.days[tr["a"][i]], exit=px.days[tr["b"][i]],
                 stopped=bool(tr["stopped"][i]), event_return=float(rr[i])) for i in o]

def named_table(px, rows, ev, cev, in_half, in_call, names):
    """Per named member: stock purchases, and separately the underlying stock after call purchases (stock, not option,
    returns). Per event, from the entry open to the exit close, less SPY over the same days. Not judged."""
    spy = px.si["SPY"]; out = {}
    def stats(E, mask, n, v):
        tr = C.trades(px, E, n, v); k = np.where(mask & (tr["status"] == C.TRADED))[0]
        if not len(k): return dict(events=0, no_price=int((mask & (tr["status"] == C.NOPRICE)).sum()))
        x = (px.CF[E.sym[k], tr["b"][k]] / px.O[E.sym[k], tr["a"][k]]) - (px.CF[spy, tr["b"][k]] / px.O[spy, tr["a"][k]])
        return dict(events=len(k), no_price=int((mask & (tr["status"] == C.NOPRICE)).sum()), mean_minus_spy=float(x.mean()),
                    median_minus_spy=float(np.median(x)), share_above_spy=float((x > 0).mean()),
                    note="too few events to judge" if len(k) < P["min_events"] else "reported, not judged")
    for n_, M in names.items():
        mi = ev.members.index(M["member"]) if M["member"] in ev.members else -1
        ci = cev.members.index(M["member"]) if len(cev) and M["member"] in cev.members else -1
        out[n_] = dict(member=M["member"], rows=M["rows"],
                       stock_purchases={f"H{n}": {v: stats(ev, in_half & (ev.member == mi), n, v) for v in C.VARIANTS} for n in HOLDS},
                       call_purchases_as_underlying_stock_not_option_returns={f"H{n}": {v: stats(cev, in_call & (cev.member == ci), n, v) for v in C.VARIANTS} for n in HOLDS} if ci >= 0 else None)
    return out

def dump(R, path):
    def fix(x):
        if isinstance(x, dict): return {str(k): fix(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)): return [fix(v) for v in x]
        if isinstance(x, np.ndarray): return [fix(v) for v in x.tolist()]
        if isinstance(x, (np.integer,)): return int(x)
        if isinstance(x, (np.floating, float)): return None if not np.isfinite(x) else float(x)
        if isinstance(x, np.bool_): return bool(x)
        return x
    json.dump(fix(R), open(path, "w"), indent=1, allow_nan=False); open(path, "a").write("\n")

def load_all(cut=None):
    rows = C.load_rows()
    B = C.events(rows, "buy"); S_ = C.events(rows, "sell"); CB = C.call_buy_events(rows)
    days = C.calendar()
    syms = {e["sym"] for e in B + S_ + CB} | {"SPY", "QQQ", "NANC"}
    return rows, B, S_, CB, days, syms

# ------------------------------------------------------------------------------------------------------------- modes
def design(real=True):
    d = out_dir(real)
    for name in (DESIGN_OUT, DESIGN_LOCK):
        if exists_anywhere(name, real): raise Refused(f"refused: {name} exists here or in origin/main. The design half is scored once.")
    if real: require_no_override(); require_frozen()
    rows, B, S_, CB, days, syms = load_all()
    names = named_members(rows)
    dB, _ = halves(B); cut = cut_day(days, dB)
    lock(os.path.join(d, DESIGN_LOCK), "design")                   # before any price is read
    px = C.Prices(days, syms, cut)
    Bv, Sv, Cv = C.Ev(B, px), C.Ev(S_, px), C.Ev(CB, px)
    lo, hi = C.ordinal(P["design_filed_from"]), C.ordinal(P["design_filed_to"])
    inb = (Bv.filed >= lo) & (Bv.filed <= hi); ins = (Sv.filed >= lo) & (Sv.filed <= hi); inc = (Cv.filed >= lo) & (Cv.filed <= hi) if len(Cv) else np.array([], bool)
    R = dict(made_by="research_rig/score_12.py --design", made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), config=P,
             inputs=inputs(), prices_read=px.digest(), named_members_matched=names, setups={})
    for g, n in SETUPS:
        R["setups"][f"{g}-H{n}"] = {v: setup(px, Bv, Sv, g, n, v, P["design_filed_from"], inb, ins, last_day=P["design_filed_to"])[0] for v in C.VARIANTS}
    main = [(k, R["setups"][k]["main"]["judged"]["per_year_excess"]) for k in R["setups"]]
    ok = [(k, x) for k, x in main if x is not None]
    R["chosen_setup"] = max(ok, key=lambda kx: (round(kx[1], 6), -[k for k, _ in main].index(kx[0])))[0] if ok else None
    tr = C.trades(px, Bv, P["main_hold_days"], "main"); k = inb & (tr["status"] == C.TRADED)
    R["largest_event_returns_main_hold"] = largest(px, Bv, tr, k)
    R["call_or_exercise_rows"] = dict(buy_events_with_such_rows=int((inb & Bv.call_rows).sum()), all_members=True)
    R["named_members_not_judged"] = named_table(px, rows, Bv, Cv, inb, inc, names)
    dump(R, os.path.join(d, DESIGN_OUT))
    report(R, "design"); return R

def pass_marks(m, l5):
    """The five marks from the main and late5 results of the chosen set-up. Mark 3 needs both figures."""
    return {"1_ends_above_spy": bool(m["judged"]["ends_above_spy"]),
             "2_bootstrap_p5_above_0": (m["judged"]["bootstrap_p5_monthly_diff"] or 0) > 0,
             "3_above_sales": m["judged"]["per_year_excess"] is not None and m["sales_b"]["per_year_excess"] is not None and m["judged"]["per_year_excess"] > m["sales_b"]["per_year_excess"],
             "4_min_events": m["judged"]["events"]["traded"] >= P["min_events"],
             "5_late5_ends_above_spy": bool(l5["judged"]["ends_above_spy"])}

def heldback(real=True):
    d = out_dir(real)
    for name in (HELDBACK_OUT, HELDBACK_LOCK):
        if exists_anywhere(name, real): raise Refused(f"refused: {name} exists here or in origin/main. The held-back half is scored once.")
    if real: require_no_override(); require_frozen(); require_pushed(f"research_rig/{DESIGN_OUT}")
    dp = os.path.join(d, DESIGN_OUT)
    if not os.path.exists(dp): raise Refused(f"refused: {DESIGN_OUT} does not exist, so no set-up is chosen")
    D = json.load(open(dp)); ch = D.get("chosen_setup")
    if ch is None: raise Refused("refused: the design run chose no set-up")
    if D.get("config") != json.loads(json.dumps(P)): raise Refused("refused: replay_12_plan differs from the one the design run used")
    if D.get("inputs") != inputs(): raise Refused("refused: the trades files differ from the ones the design run used")
    rows, B, S_, CB, days, syms = load_all()
    names = named_members(rows)
    lock(os.path.join(d, HELDBACK_LOCK), "heldback")               # before any price is read
    px = C.Prices(days, syms)
    Bv, Sv, Cv = C.Ev(B, px), C.Ev(S_, px), C.Ev(CB, px)
    g, n = ch.split("-H"); n = int(n); lo = C.ordinal(P["heldback_filed_from"])
    def finished(E):
        m = E.filed >= lo
        for v in C.VARIANTS: m &= C.trades(px, E, n, v)["status"] != C.UNFINISHED
        return m
    inb, ins = finished(Bv), finished(Sv); inc = finished(Cv) if len(Cv) else np.array([], bool)
    R = dict(made_by="research_rig/score_12.py --heldback", made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), config=P,
             inputs=inputs(), prices_read=px.digest(), chosen_setup=ch, named_members_matched=names, results={})
    for v in C.VARIANTS:
        R["results"][v], Jfull, mb, tr = setup(px, Bv, Sv, g, n, v, P["heldback_filed_from"], inb, ins)
        if v == "main": J = Jfull
    marks = pass_marks(R["results"]["main"], R["results"]["late5"])
    R["pass_marks"] = marks; R["passes"] = all(marks.values())
    tr = C.trades(px, Bv, n, "main"); k = inb & (tr["status"] == C.TRADED)
    R["largest_event_returns_chosen_hold"] = largest(px, Bv, tr, k)
    R["call_or_exercise_rows"] = dict(buy_events_with_such_rows=int((inb & Bv.call_rows).sum()), all_members=True)
    R["named_members_not_judged"] = named_table(px, rows, Bv, Cv, inb, inc, names)
    dump(R, os.path.join(d, HELDBACK_OUT))
    report(R, "heldback"); return R

def report(R, mode):
    def pc(x): return "none" if x is None else f"{100 * x:+.2f}%"
    print("named members:", {k: (v["member"], v["rows"]) for k, v in R["named_members_matched"].items()})
    sets = R["setups"] if mode == "design" else {R["chosen_setup"]: R["results"]}
    for k, V in sets.items():
        for v, x in V.items():
            j = x["judged"]
            print(f"{k:12s} {v:5s} per-year excess {pc(j['per_year_excess'])} | events {j['events']['traded']} no price {j['events']['no_price']} "
                  f"| sales {pc(x['sales_b']['per_year_excess'])} | no reset {j.get('no_reset_growth_not_judged')} | without call rows {pc(x['without_call_or_exercise_rows_not_judged']['per_year_excess'])}")
            print("   no price by year:", j["events"]["no_price_by_year"])
    if mode == "design": print("chosen:", R["chosen_setup"])
    else: print("pass marks:", R["pass_marks"], "passes:", R["passes"])
    for x in R.get("largest_event_returns_main_hold", R.get("largest_event_returns_chosen_hold", [])): print("  largest:", x)

def counts(real=True):
    """Events and missing prices, counts and dates only: reads which dates have a bar, no price value."""
    import csv
    rows, B, S_, CB, days, syms = load_all()
    have = {}
    for s in syms:
        p = os.path.join(C.BARS, s + ".csv")
        have[s] = {r["date"] for r in csv.DictReader(open(p))} if os.path.exists(p) else set()
    names = named_matches(rows)
    ords = np.array([C.ordinal(d) for d in days])
    def entry_has_bar(e):
        i = int(np.searchsorted(ords, C.ordinal(e["filed"]), "right"))
        return i < len(days) and days[i] in have[e["sym"]]
    first = {s: min(v) for s, v in have.items() if v}
    def starts_late(e): return e["sym"] in first and first[e["sym"]] > e["filed"]
    out = dict(made_by="research_rig/score_12.py --counts", made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
               rows=len(rows), buy_events=len(B), sell_events=len(S_), call_buy_events_named_table_only=len(CB),
               buy_members=len({e["member"] for e in B}), buy_tickers=len({e["sym"] for e in B}), last_price_day=days[-1])
    for lab, E in (("buy", B), ("sell", S_)):
        d, h = halves(E)
        for half, L in (("design", d), ("heldback", h)):
            miss = [e for e in L if not entry_has_bar(e)]
            yrs = sorted({e["filed"][:4] for e in L})
            out[f"{lab}_{half}"] = dict(events=len(L), large=sum(e["large"] for e in L), members=len({e["member"] for e in L}),
                                        no_bar_on_main_entry_day=len(miss), no_bar_share=round(len(miss) / len(L), 4) if L else None,
                                        no_bar_by_year={y: sum(e["filed"][:4] == y for e in miss) for y in yrs},
                                        tickers_without_any_bar=len({e["sym"] for e in L if not have[e["sym"]]}),
                                        with_call_or_exercise_rows=sum(e["call_rows"] for e in L),
                                        bar_on_entry_day_but_prices_start_after_filing=sum(entry_has_bar(e) and starts_late(e) for e in L),
                                        renamed_events=sum(e["renamed"] for e in L),
                                        events_moved_by_rename_line={x: sum(e["rename_line"] == x for e in L) for x in sorted({e["rename_line"] for e in L if e["rename_line"]})},
                                        recovered_by_rename_list_by_year={y: sum(e["renamed"] and entry_has_bar(e) and not starts_late(e) and e["filed"][:4] == y for e in L) for y in yrs})
    from collections import Counter
    cm = Counter(e["member"] for e in B); top = cm.most_common(1)[0]
    out["busiest_buyer"] = dict(member=top[0], buy_events=top[1], share=round(top[1] / len(B), 4))
    out["named_members_matched"] = names
    out["rename_list"] = dict(file="research_rig/renames_12.csv", sha256=C.sha256_file(C.RENAMES_FILE), mapped=len(C.RENAMES),
                              dated_lines=sum(len(v) for v in C.RENAMES_ALL[1].values()), decided_by="filed_date")
    p = os.path.join(C.HERE, "events_12_summary.json") if real else os.path.join(C.OUTDIR, "events_12_summary.json")
    json.dump(out, open(p, "w"), indent=1); open(p, "a").write("\n")
    print(json.dumps(out, indent=1)); return out

if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a == ["--counts"]: counts()
        elif a == ["--design"]: design(True)
        elif a == ["--heldback"]: heldback(True)
        elif a == ["--selftest"]: sys.exit(subprocess.run([sys.executable, os.path.join(C.HERE, "test_12.py")]).returncode)
        else: print(__doc__)
    except Refused as e: sys.exit(str(e))
