"""Tests for plan 12's scorer, on made-up trades and prices only. Run from research_rig/:  python3 test_12.py
(or python3 score_12.py --selftest). Everything is written to a temporary folder; no real trade or price is read."""
import os, sys, json, csv, tempfile, shutil, datetime as dt
import numpy as np

TMP = tempfile.mkdtemp(prefix="t12_")
os.environ.update(CONGRESS_12_TRADES=os.path.join(TMP, "trades.csv"), CONGRESS_12_DETAILS=os.path.join(TMP, "details.csv"),
                  CONGRESS_12_BARS=os.path.join(TMP, "bars"), RESULTS_12_DIR=os.path.join(TMP, "out"))
for d in ("bars", "out"): os.makedirs(os.path.join(TMP, d))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_12 as C, score_12 as S

P = C.P
P["random_date_draws"] = 10; P["bootstrap_draws"] = 1000      # smaller for speed; both runs see the same values
fails = []
def ok(cond, name):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)
def refused(fn, *a, **k):
    try: fn(*a, **k); return False
    except (S.Refused, SystemExit): return True

# ---- made-up calendar: weekdays 2018-12-03 to 2024-10-31
days, d = [], dt.date(2018, 12, 3)
while d <= dt.date(2024, 10, 31):
    if d.weekday() < 5: days.append(d.isoformat())
    d += dt.timedelta(days=1)
N = len(days); rng = np.random.default_rng(1)
def write_bars(sym, o, c, lo=0, hi=None):
    with open(os.path.join(C.BARS, sym + ".csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close", "volume"])
        for i in range(lo, hi or N):
            if not np.isnan(c[i]): w.writerow([days[i], f"{o[i]:.6f}", 0, 0, f"{c[i]:.6f}", 1])
spy_r = rng.normal(0.0003, 0.01, N); spy_c = 100 * np.cumprod(1 + spy_r); spy_o = np.r_[100, spy_c[:-1]] * (1 + rng.normal(0, 0.002, N))
write_bars("SPY", spy_o, spy_c)
q = 100 * np.cumprod(1 + spy_r * 1.2); write_bars("QQQ", np.r_[100, q[:-1]], q)
nanc = 30 * np.cumprod(1 + spy_r); n0 = days.index("2023-02-07"); write_bars("NANC", np.r_[30, nanc[:-1]], nanc, lo=n0)

# ---- made-up members and events: each event its own stock, so the planted edge is exact
MEMBERS = ["Alice Green", "Bob Greene", "Daniel Goldman", "Danielle Goldmanson", "Nancy Pelosi", "Eve Busy", "Frank Small", "Gina Mid"]
rows, details = [], []
def add(member, ticker, side, filed, asset="stock", low=1001.0, text=""):
    r = dict(member=member, chamber="house", party="D", ticker=ticker, asset_type=asset, side=side, amount_range_low=str(low),
             amount_range_high="15000.0", transaction_date="2000-01-01", filed_date=filed, owner="", source_url="x")
    rows.append(r); details.append(dict(r, event_id="", asset_description=text, description_note="", owner_original="", asset_classification="", filing_timestamp_ny="", house_index_date=""))
EDGE = 0.002                                                       # extra daily gain of a bought stock from its entry day
n_ev = 0
for i in range(5, N - 30):
    if days[i] < "2019-01-02": continue
    for side in ("buy", "sell"):
        m = MEMBERS[5] if rng.random() < 0.4 else MEMBERS[rng.integers(0, len(MEMBERS))]   # one busy member, as in the record
        t = f"{'B' if side == 'buy' else 'S'}{n_ev:05d}"; n_ev += 1
        filed = days[i]; e0 = i + 1
        r = spy_r + rng.normal(0, 0.01, N)
        if side == "buy": r[e0:] += EDGE
        c = 50 * np.cumprod(1 + r); o = np.r_[50, c[:-1]] * (1 + rng.normal(0, 0.002, N))
        if side == "buy" and e0 < N: o[e0] = c[e0 - 1]            # the edge starts at the entry open
        lo, hi = max(0, i - 100), min(N, i + 280)
        if not (side == "buy" and n_ev % 97 == 0): write_bars(t, o, c, lo, hi)   # a few stocks have no prices at all
        add(m, t, side, filed, low=50001.0 if rng.random() < 0.3 else 1001.0, text="Exercised call options" if (side == "buy" and n_ev % 53 == 0) else "")
add("Nancy Pelosi", "B00002", "buy", "2019-03-04", asset="option", text="Purchased 20 call options with a strike price of $140")
add("Nancy Pelosi", "B00004", "buy", "2020-03-03", asset="option", text="Purchased 5 put options")
for path, R in ((C.TRADES, rows), (C.DETAILS, details)):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(R[0])); w.writeheader(); w.writerows(R)

# ---- entries: never on the filing day
cal = C.calendar(); ok(cal == days, "the calendar is the SPY file's dates")
px0 = C.Prices.from_arrays(days, {"SPY": (spy_o, spy_c)})
f = np.array([C.ordinal(x) for x in ["2019-03-01", "2019-03-02", "2019-03-03", "2019-03-04"]])
a = C.entries(px0, f, "main")
ok([days[i] for i in a] == ["2019-03-04", "2019-03-04", "2019-03-04", "2019-03-05"], "main entry: the first trading day after the filing day, never the filing day")
ok(list(C.entries(px0, f, "late5") - a) == [5] * 4, "late5 entry: 5 trading days after the main entry")
ok([days[i] for i in C.entries(px0, f, "cal30")] == ["2019-04-01", "2019-04-02", "2019-04-03", "2019-04-04"], "cal30 entry: the first trading day after filing day + 30 calendar days")
fr = rng.integers(C.ordinal("2019-01-01"), C.ordinal("2024-01-01"), 2000)
ok(all((px0.ord[C.entries(px0, fr, v)] > fr).all() for v in C.VARIANTS), "every entry version is after the filing day, for 2,000 random filing days")

# ---- events, trades, no price, stopped, merge
allrows = C.load_rows(); B = C.events(allrows, "buy")
ok(len(B) == sum(1 for r in rows if r["side"] == "buy" and r["asset_type"] == "stock"), "one event per member, stock and filing day; option rows are not events")
add_rows = [dict(r) for r in allrows[:1]]; add_rows += [dict(add_rows[0])]
ok(len(C.events(add_rows, add_rows[0]["side"])) == 1, "two rows of one member, stock and filing day are one event")
syms = {e["sym"] for e in B} | {"SPY", "QQQ", "NANC"}
px = C.Prices(days, syms); ev = C.Ev(B, px)
tr = C.trades(px, ev, 21, "main")
nofile = [j for j, e in enumerate(B) if not os.path.exists(os.path.join(C.BARS, e["sym"] + ".csv"))]
ok(len(nofile) > 0 and all(tr["status"][j] == C.NOPRICE for j in nofile), "an event whose stock has no prices is marked no price")
late = [j for j, e in enumerate(B) if e["filed"] > days[N - 21]]
ok(all(tr["status"][j] == C.UNFINISHED for j in late), "an event whose hold ends after the last price day is unfinished")
cut = {"SPY": (spy_o, spy_c), "X": (np.where(np.arange(N) < 30, 10.0, np.nan), np.where(np.arange(N) < 30, 10.0, np.nan)),
       "LATE": (np.where(np.arange(N) > 20, 10.0, np.nan), np.where(np.arange(N) > 20, 10.0, np.nan))}
pxs = C.Prices.from_arrays(days, cut)
E2 = [dict(member="m", sym="X", filed=days[19], large=False, call_rows=False, ticker="X"), dict(member="m", sym="LATE", filed=days[10], large=False, call_rows=False, ticker="LATE")]
ev2 = C.Ev(E2, pxs); t2 = C.trades(pxs, ev2, 21, "main")
ok(t2["status"][0] == C.TRADED and t2["stopped"][0] and t2["b"][0] == 29, "bars that stop inside the hold: sold at the last close and flagged")
ok(t2["status"][1] == C.NOPRICE, "bars that start after the entry day: no price")
m_, s_, a_, b_ = C.merge(np.array([0, 0, 0, 1]), np.array([5, 5, 5, 5]), np.array([10, 20, 60]), np.array([30, 40, 80]), "member") if False else C.merge(np.array([0, 0, 0, 1]), np.array([5, 5, 5, 5]), np.array([10, 20, 60, 15]), np.array([30, 40, 80, 35]), "member")
ok(sorted(zip(m_, a_, b_)) == [(0, 10, 40), (0, 60, 80), (1, 15, 35)], "holds of one member in one stock that overlap are one position")
ok(len(C.merge(np.array([0, 0, 0, 1]), np.array([5, 5, 5, 5]), np.array([10, 20, 60, 15]), np.array([30, 40, 80, 35]), "stock")[0]) == 2, "by stock, all members' holds of a stock merge")

# ---- member weighting, turnover cost, the SPY mirror
D = {"SPY": (np.full(10, 100.0), 100.0 * 1.01 ** np.arange(1, 11))}
for k, g in (("A1", 0.02), ("A2", 0.02), ("A3", 0.02), ("B1", -0.01)): D[k] = (np.full(10, 10.0), np.full(10, 10.0 * (1 + g)))
d10 = days[:10]; pw = C.Prices.from_arrays(d10, D)
mem, sy = np.array([0, 0, 0, 1]), np.array([pw.si[k] for k in ("A1", "A2", "A3", "B1")])
pf = C.portfolio(pw, *C.merge(mem, sy, np.array([2] * 4), np.array([2] * 4), "member"), by="member", cost=0)
ok(abs(pf["gross"][0] - (0.5 * 0.02 + 0.5 * -0.01)) < 1e-12, "by member: each member half, split among its stocks (A 3 stocks, B 1)")
pf = C.portfolio(pw, *C.merge(mem, sy, np.array([2] * 4), np.array([2] * 4), "stock"), by="stock", cost=0)
ok(abs(pf["gross"][0] - (0.75 * 0.02 + 0.25 * -0.01)) < 1e-12, "by stock: every stock an equal share")
one = C.Prices.from_arrays(d10, {"SPY": D["SPY"], "Z": (np.full(10, 10.0), 10.0 * 1.02 ** np.arange(1, 11))})
pz = C.portfolio(one, np.array([0]), np.array([one.si["Z"]]), np.array([1]), np.array([5]), by="member", cost=10)
g_gross = C.growth(pz["gross"]); g_net = C.growth(pz["net"])
ok(abs(pz["turnover"] - 2.0) < 1e-12 and abs(g_net - g_gross * (1 - 0.001 / 1.02 * 1.02 / 1.02) ) < 2e-3 and g_net < g_gross, "one position: turnover is the buy and the sale, cost lowers the growth")
ok(abs(C.growth(pz["bench"]["SPY"]["r"]) - one.C[one.si["SPY"], 5] / one.O[one.si["SPY"], 1]) < 1e-12, "the SPY mirror runs from the same entry open to the same exit close")
ok(abs(C.growth(pz["no_reset_net"]) - C.growth(pz["net"])) < 1e-12, "one position: no daily reset changes nothing")

# ---- bootstrap is seeded
x = rng.normal(0, 0.01, 40)
ok(C.bootstrap_p5(x, 1000, 12) == C.bootstrap_p5(x, 1000, 12) and C.bootstrap_p5(x, 1000, 12) != C.bootstrap_p5(x, 1000, 13), "the bootstrap is seeded")

# ---- proven members use nothing on or after the refresh day
evB = C.Ev(B, px); L1 = S.proven_lists(px, evB, 21, "main", "2019-01-01")
R = 8; Rday = L1[R]["day"]; Ri = days.index(Rday)
ok(L1[R]["members"] != [], "a proven list is built once members have enough finished purchases")
px2 = C.Prices(days, syms); px2.O[:, Ri:] *= rng.uniform(0.2, 5, size=px2.O[:, Ri:].shape); px2.C[:, Ri:] *= rng.uniform(0.2, 5, size=px2.C[:, Ri:].shape)
px2.CF = np.where(px2.LV >= 0, np.take_along_axis(np.nan_to_num(px2.C), np.maximum(px2.LV, 0), axis=1), np.nan)
L2 = S.proven_lists(px2, C.Ev(B, px2), 21, "main", "2019-01-01")
ok(L2[R]["members"] == L1[R]["members"], "the proven list on a refresh day does not change when every later price is changed")
ok(L2[R + 1]["members"] != L1[R + 1]["members"] or L2[R + 2]["members"] != L1[R + 2]["members"], "and the later lists do change, so the test can see a change")
ok(all(L1[i + 1]["day"] == days[days.index(L1[i]["day"]) + P["proven_refresh_days"]] for i in range(5)), "refreshes are every proven_refresh_days trading days")
w = np.zeros(len(evB), bool); w[:] = True
mk = S.on_list(evB, L1, w); j = np.where(mk)[0]
pos = np.maximum(np.searchsorted([C.ordinal(L["day"]) for L in L1], evB.filed[j], "right") - 1, 0)
ok(all(evB.members[evB.member[k]] in L1[p]["members"] and C.ordinal(L1[p]["day"]) <= evB.filed[k] or p == 0 for k, p in zip(j, pos)), "an event follows the list of the latest refresh on or before its filing day")

# ---- named members
P["named_members"] = ["Greene", "Goldman", "Pelosi"]
nm = S.named_members(allrows)
ok(nm["Greene"]["member"] == "Bob Greene" and nm["Goldman"]["member"] == "Daniel Goldman" and nm["Pelosi"]["rows"] > 0, "named members: Greene is not Green, Goldman is not Goldmanson; rows are counted")
P["named_members"] = ["Green"]; ok(nm and S.named_members(allrows)["Green"]["member"] == "Alice Green", "Green matches only Alice Green")
P["named_members"] = ["Nobody"]; ok(refused(S.named_members, allrows), "a name that matches no member stops the run")
add_extra = allrows + [dict(allrows[0], member="Tom Green")]
P["named_members"] = ["Green"]; ok(refused(S.named_members, add_extra), "a name that matches two members stops the run")
P["named_members"] = ["Greene", "Goldman", "Pelosi"]
CB = C.call_buy_events(allrows); ok(len(CB) == 1 and CB[0]["sym"] == "B00002", "the named table's call purchases: calls only, not puts")

# ---- rename list: mapped lines change the priced ticker on every date; dated lines by the filing day; left-out lines do not
rl = os.path.join(TMP, "renames.csv")
with open(rl, "w", newline="") as f:
    f.write("old_ticker,new_ticker,effective_date,status,source_url,note\nOLDA,NEWA,2020-01-02,mapped,x,same company\n"
            "GONE,TAKER,,left_out,x,a takeover ends the history\nRE,FIRSTCO,2020-06-01,mapped_before,x,reused ticker\n"
            "TWO,,2020-03-02,left_out_before,x,no price\nTWO,MID,2021-01-04,mapped_before,x,middle owner\n")
rmap = C.load_renames(rl)
ok(rmap[0] == {"OLDA": "NEWA"} and rmap[1] == {"RE": [("2020-06-01", "FIRSTCO")], "TWO": [("2020-03-02", None), ("2021-01-04", "MID")]},
   "the rename list keeps mapped and dated lines and drops left_out lines")
rr = [dict(allrows[0], ticker=t, side="buy", asset_type="stock", member="Zed Rename", filed_date="2020-06-01") for t in ("OLDA", "GONE", "NEWA")]
er = C.events(rr, "buy", renames=rmap)
ok(sorted((e["ticker"], e["sym"], e["renamed"]) for e in er) == [("GONE", "GONE", False), ("OLDA", "NEWA", True)] and er[[e["sym"] for e in er].index("NEWA")]["rows"] == 2,
   "an old ticker is priced from the new ticker's file, a left-out takeover is not mapped, and the old and new ticker of one filing day are one event")
ps = lambda t, d: C.priced_symbol(t, d, rmap)[0]
ok(ps("RE", "2020-05-29") == "FIRSTCO" and ps("RE", "2020-06-01") == "RE" and ps("RE", "2021-01-01") == "RE", "a dated line moves rows filed before its date only; on and after the date the ticker is its own")
ok(ps("TWO", "2020-02-28") == "TWO~LEFT_OUT" and ps("TWO", "2020-03-02") == "MID" and ps("TWO", "2021-01-04") == "TWO", "two dated lines for one ticker: the first whose date is after the filing day applies")
rt = [dict(allrows[0], ticker="RE", side="buy", asset_type="stock", member="Zed Rename", filed_date="2020-06-01", transaction_date="2020-01-01")]
ok(C.events(rt, "buy", renames=rmap)[0]["sym"] == "RE", "the filing day chooses the dated line, not transaction_date")
pxl = C.Prices.from_arrays(days, {"SPY": (spy_o, spy_c)}); evl = C.Ev([dict(member="m", sym="TWO~LEFT_OUT", filed=days[50], large=False, call_rows=False, ticker="TWO")], pxl)
ok(C.trades(pxl, evl, 21, "main")["status"][0] == C.NOPRICE, "a row a left_out_before line catches is counted as no price")
ok(C.RENAMES.get("MMC") == "MRSH" and C.RENAMES.get("SNE") == "SONY" and not any(k in C.RENAMES for k in ("HTA", "JIH", "RDSA", "ABB", "BHI")),
   "the frozen list maps MMC and SNE and leaves out HTA, JIH, RDSA, ABB and BHI")
ok(C.priced_symbol("BBT", "2019-04-25")[0] == "TFC" and C.priced_symbol("BBT", "2025-10-22")[0] == "BBT" and C.priced_symbol("AM", "2019-02-04")[0] == "AM~LEFT_OUT"
   and C.priced_symbol("AM", "2019-05-01")[0] == "AM" and C.priced_symbol("WTW", "2020-08-13")[0] == "WW" and C.priced_symbol("WTW", "2022-02-01")[0] == "WTW",
   "the frozen dated lines: BB&T rows to TFC, AM before 2019-03-13 left out, WTW between 2019-04-22 and 2022-01-10 to WW")
with open(rl, "a") as f: f.write("OLDA,OTHER,,mapped,x,repeat\n")
ok(refused(C.load_renames, rl), "a ticker mapped twice in the rename list stops the run")

# ---- prices that start after the filing day, and shifted filing days before the calendar
st_ = 40; LS = {"SPY": (spy_o, spy_c), "NEWCO": (np.where(np.arange(N) >= st_, 10.0, np.nan), np.where(np.arange(N) >= st_, 10.0, np.nan))}
pls = C.Prices.from_arrays(days, LS)
E3 = [dict(member="m", sym="NEWCO", filed=days[st_ - 2], large=False, call_rows=False, ticker="NEWCO"),
      dict(member="m", sym="NEWCO", filed=days[st_], large=False, call_rows=False, ticker="NEWCO")]
ev3 = C.Ev(E3, pls)
ok(all(C.trades(pls, ev3, 21, v)["status"][0] == C.NOPRICE for v in C.VARIANTS) and all(C.trades(pls, ev3, 21, v)["status"][1] == C.TRADED for v in C.VARIANTS),
   "an event whose stock's prices start after its filing day is no price in every entry version, even when the later entry has a bar")
ok(C.trades(pls, ev3, 21, "main", filed_ord=np.array([pls.ord[0] - 3, pls.ord[0]]))["status"][0] == C.NOPRICE, "a shifted filing day before the first calendar day is no price, not piled onto the first day")

# ---- proven list: a hold that exits on the refresh day itself is not finished
dq = {"SPY": (np.full(N, 100.0), np.full(N, 100.0)), "Q": (np.full(N, 10.0), np.full(N, 11.0))}
pq = C.Prices.from_arrays(days, dq); Rq = 2 * P["proven_refresh_days"]
fq = [days[10 + t] for t in range(P["proven_min_events"] - 1)] + [days[Rq - 21]]            # the last exits on day Rq exactly
Eq = [dict(member="Xq Solo", sym="Q", filed=x, large=False, call_rows=False, ticker="Q") for x in fq]
evq = C.Ev(Eq, pq); Lq = S.proven_lists(pq, evq, 21, "main", days[0])
ok(C.trades(pq, evq, 21, "main")["b"][-1] == Rq and Lq[2]["members"] == [] and Lq[3]["members"] == ["Xq Solo"],
   "a purchase whose exit is the refresh day itself does not count for that refresh, only for the next")
ok(len(S.proven_lists(pq, evq, 21, "main", days[0], last_day=days[Rq])) == 3, "proven lists stop at last_day (the design run passes design_filed_to)")

# ---- mark 3 needs a sales figure
mk3 = lambda pj, ps: S.pass_marks(dict(judged=dict(ends_above_spy=True, bootstrap_p5_monthly_diff=0.01, per_year_excess=pj, events=dict(traded=999)), sales_b=dict(per_year_excess=ps)),
                                   dict(judged=dict(ends_above_spy=True)))["3_above_sales"]
ok(mk3(0.05, 0.01) and not mk3(0.05, None) and not mk3(None, 0.01) and not mk3(0.01, 0.05), "mark 3 passes only when both figures exist and purchases are higher")

# ---- real-run guards (origin/main faked; nothing is written into research_rig/)
before = set(os.listdir(C.HERE))
ok(refused(S.design, True) and refused(S.heldback, True), "real runs refuse while a test folder override is set")
real_pb, real_repo = S.pushed_bytes, C.REPO
saved = {v: os.environ.pop(v) for v in C.ENV_OVERRIDES}
S.pushed_bytes = lambda rel: None
ok(refused(S.require_frozen), "no frozen plan: refused")
fake = os.path.join(TMP, "repo"); os.makedirs(os.path.join(fake, "research_rig")); open(os.path.join(fake, S.FROZEN_PLAN), "w").write("plan\n"); C.REPO = fake
import yaml
good = yaml.safe_dump({"replay_12_plan": {"value": P}}).encode(); bad = yaml.safe_dump({"replay_12_plan": {"value": dict(P, cost_bps_per_side=5)}}).encode()
code = {rel: open(os.path.join(real_repo, rel), "rb").read() for rel in S.FROZEN_CODE}
for rel, b in code.items(): open(os.path.join(fake, rel), "wb").write(b)
S.pushed_bytes = lambda rel: b"plan\n" if rel == S.FROZEN_PLAN else good if rel == "config/thresholds.yaml" else code.get(rel)
ok(not refused(S.require_frozen), "frozen plan, config, scorer and rename list as in origin/main: allowed")
for rel in S.FROZEN_CODE:
    S.pushed_bytes = lambda r, rel=rel: b"plan\n" if r == S.FROZEN_PLAN else good if r == "config/thresholds.yaml" else (b"x" if r == rel else code.get(r))
    ok(refused(S.require_frozen), f"{rel} that differs from origin/main: refused")
S.pushed_bytes = lambda rel: b"plan\n" if rel == S.FROZEN_PLAN else bad if rel == "config/thresholds.yaml" else None
ok(refused(S.require_frozen), "config that differs from origin/main: refused")
S.pushed_bytes = lambda rel: b"other\n" if rel == S.FROZEN_PLAN else good if rel == "config/thresholds.yaml" else None
ok(refused(S.require_frozen), "a plan that differs from origin/main: refused")
for name in (S.DESIGN_OUT, S.DESIGN_LOCK):
    S.pushed_bytes = lambda rel, name=name: b"{}" if rel.endswith(name) else None
    ok(refused(S.design, True), f"--design refused when {name} is in origin/main")
for name in (S.HELDBACK_OUT, S.HELDBACK_LOCK):
    S.pushed_bytes = lambda rel, name=name: b"{}" if rel.endswith(name) else None
    ok(refused(S.heldback, True), f"--heldback refused when {name} is in origin/main")
S.pushed_bytes, C.REPO = real_pb, real_repo; os.environ.update(saved)
ok(set(os.listdir(C.HERE)) == before, "the refused real runs wrote nothing into research_rig/")

# ---- held-back before design, design lock before prices
ok(refused(S.heldback, False), "--heldback refuses without the design result")
real_prices = C.Prices
def boom(*a, **k): raise RuntimeError("prices")
C.Prices = boom
try: S.design(False)
except RuntimeError: pass
C.Prices = real_prices
ok(os.path.exists(os.path.join(C.OUTDIR, S.DESIGN_LOCK)), "--design writes its lock before it reads a price")
ok(refused(S.design, False), "--design refuses while its lock exists, even with no result")
os.remove(os.path.join(C.OUTDIR, S.DESIGN_LOCK))

# ---- the design run on the planted edge
RD = S.design(False)
ok(refused(S.design, False), "--design refuses a second run")
dB, _ = S.halves(B); cutn = S.cut_day(days, dB)
ok(RD["prices_read"]["last_day_loaded"] == days[cutn - 1] and days[cutn - 1] < "2024-01-01", "the design run loads no day after the last one a design event or draw needs")
ok(RD["chosen_setup"] is not None and RD["setups"][RD["chosen_setup"]]["main"]["judged"]["per_year_excess"] > 0, "planted edge: the design run finds buys that beat SPY")
for k, V in RD["setups"].items():
    if not all(V[v]["judged"]["ends_above_spy"] for v in C.VARIANTS if V[v]["judged"]["days"]): ok(False, f"planted edge: {k} beats SPY in every entry version")
j = RD["setups"]["all-H63"]["main"]
ok(j["sales_b"]["per_year_excess"] is not None and j["sales_b"]["per_year_excess"] < j["judged"]["per_year_excess"] and abs(j["sales_b"]["per_year_excess"]) < 0.05,
   "the sales yardstick: sales with no edge end near SPY and below the buys")
ok(j["judged"]["events"]["no_price"] > 0 and j["judged"]["events"]["no_price"] == sum(1 for e in dB if not os.path.exists(os.path.join(C.BARS, e["sym"] + ".csv"))),
   "events with no price are counted and left out")
ok(sum(j["judged"]["events"]["no_price_by_year"].values()) == j["judged"]["events"]["no_price"], "no-price events are counted by year")
ok(j["without_busiest_member_not_judged"]["member"] == "Eve Busy", "the busiest member is the one left out")
ok(j["without_call_or_exercise_rows_not_judged"]["events_left_out"] > 0, "events with call or exercise words are counted and a side line without them is printed")
ok(j["random_days_c_not_judged"]["draws"] == P["random_date_draws"], "yardstick (c) is drawn random_date_draws times")
ok(j["judged"]["qqq_for_scale"] is not None and (j["judged"]["nanc_for_scale"] is None or j["judged"]["nanc_for_scale"]["days"] < j["judged"]["qqq_for_scale"]["days"]), "QQQ is shown; NANC only on its own days (from 2023-02-07)")
ok(len(RD["largest_event_returns_main_hold"]) == 20, "the 20 largest single-event returns are listed")
ok(set(RD["named_members_not_judged"]) == {"Greene", "Goldman", "Pelosi"} and RD["named_members_not_judged"]["Pelosi"]["call_purchases_as_underlying_stock_not_option_returns"]["H21"]["main"]["events"] == 1,
   "the named table has stock purchases and, apart, the stock after call purchases")
ok(RD["setups"]["proven-H63"]["main"]["proven_lists"][0]["members"] == [], "the first proven list of the design half is empty: no finished purchases yet")
ok(all(L["day"] <= P["design_filed_to"] for k in RD["setups"] if k.startswith("proven") for v in C.VARIANTS for L in RD["setups"][k][v]["proven_lists"]),
   "the design run builds and writes no proven list after design_filed_to")
# the same design run with every price after the cut changed gives the same result
os.rename(os.path.join(C.OUTDIR, S.DESIGN_OUT), os.path.join(TMP, "d1.json")); os.remove(os.path.join(C.OUTDIR, S.DESIGN_LOCK))
for fn in os.listdir(C.BARS)[:400]:
    p = os.path.join(C.BARS, fn); L = list(csv.reader(open(p)))
    L = [L[0]] + [r if r[0] < days[cutn] else [r[0], str(float(r[1]) * 3), 0, 0, str(float(r[4]) * 0.3), 1] for r in L[1:]]
    csv.writer(open(p, "w", newline="")).writerows(L)
S.design(False); d2 = json.load(open(os.path.join(C.OUTDIR, S.DESIGN_OUT))); d1 = json.load(open(os.path.join(TMP, "d1.json")))
ok({k: v for k, v in d1.items() if k not in ("made_utc", "prices_read")} == {k: v for k, v in d2.items() if k not in ("made_utc", "prices_read")}, "changing prices after the cut does not change the design result")

# ---- held-back
DP = os.path.join(C.OUTDIR, S.DESIGN_OUT); D0 = json.load(open(DP))
json.dump(dict(D0, inputs=dict(D0["inputs"], trades_sha256="0" * 64)), open(DP, "w"))
ok(refused(S.heldback, False), "--heldback refuses when the trades file differs from the design run's")
for key in ("renames_sha256", "score_12_sha256", "common_12_sha256"):
    json.dump(dict(D0, inputs=dict(D0["inputs"], **{key: "0" * 64})), open(DP, "w"))
    ok(refused(S.heldback, False), f"--heldback refuses when {key} differs from the design run's")
json.dump(dict(D0, config=dict(D0["config"], cost_bps_per_side=1)), open(DP, "w"))
ok(refused(S.heldback, False), "--heldback refuses when the config differs from the design run's")
json.dump(dict(D0, chosen_setup="all-H63"), open(DP, "w"))
RH = S.heldback(False)
ok(os.path.exists(os.path.join(C.OUTDIR, S.HELDBACK_LOCK)), "--heldback writes its lock")
ok(RH["passes"] and all(RH["pass_marks"].values()), "planted edge: the held-back run passes all five marks")
ok(RH["results"]["main"]["judged"]["nanc_for_scale"] is not None, "NANC is shown on the held-back half")
hb_last = max(e["filed"] for e in B if e["filed"] >= P["heldback_filed_from"])
ok(RH["results"]["main"]["judged"]["events"]["in_group"] < sum(1 for e in B if e["filed"] >= P["heldback_filed_from"]), "held-back events whose hold does not finish are left out")
import report_12
txt = report_12.build(C.OUTDIR)
ok("### Each year apart" in txt and "| 2024 |" in txt, "report_12 shows each year apart on the held-back half")
ok("Verdict: passes all five marks" in txt and "| Ticker | Member |" in txt and "not option returns" in txt, "report_12 writes the page from the stored results only")
ok("by `research_rig/noedge_12.py`" in txt and txt.count("The intent is 5%") == 2, "report_12 quotes the no-edge pass rates from noedge_12.json in the method and beside mark 2")
ok("Not scored yet" in report_12.build(TMP), "report_12 says not scored yet when no result file exists")
ok(refused(S.heldback, False), "--heldback refuses a second run")
os.remove(os.path.join(C.OUTDIR, S.HELDBACK_OUT)); ok(refused(S.heldback, False), "deleting the held-back output does not let it run again (lock)")

# ---- block bootstrap: a block is consecutive months and wraps from the last month to the first
xb = np.arange(10.0); Lb = 3; kb = -(-10 // Lb); stb = np.random.default_rng(5).integers(0, 10, size=(4, kb))
pkb = ((stb[:, :, None] + np.arange(Lb)[None, None, :]) % 10).reshape(4, kb * Lb)[:, :10]
ok(all(((b[1:] - b[:-1]) % 10 == 1).all() for row in pkb for b in [row[t:t + Lb] for t in range(0, 9, Lb)]) and (pkb == 0).any(), "block picks are runs of consecutive months that wrap around")
ok(abs(C.bootstrap_p5(np.full(12, 0.01), 500, 1, 3) - 0.01) < 1e-12 and abs(C.bootstrap_p5(xb, 500, 1, 10) - float(xb.mean())) < 1e-12, "a block as long as the series gives the series mean")
ok([C.block_months(h) for h in P["holds_days"]] == [1, 3, 6], "block length is hold days / bootstrap_days_per_month rounded up")

# ---- no edge: random data over about four years, each hold, the bootstrap mark passes near its nominal 5%
def trial(seed, hold):
    r = np.random.default_rng(seed); n = 1008; dd = days[:n]
    sr = r.normal(0.0003, 0.01, n); sc = 100 * np.cumprod(1 + sr); data = {"SPY": (np.r_[100, sc[:-1]], sc)}
    for k in range(60):
        x = sr + r.normal(0, 0.015, n); c = 20 * np.cumprod(1 + x); data[f"K{k}"] = (np.r_[20, c[:-1]], c)
    q = C.Prices.from_arrays(dd, data); m = 400
    a = r.integers(1, n - hold - 1, m); s = np.array([q.si[f"K{k}"] for k in r.integers(0, 60, m)]); mem = r.integers(0, 8, m)
    pf = C.portfolio(q, *C.merge(mem, s, a, a + hold - 1, "member"), by="member", cost=0)
    sm = C.summarize(q, pf); return C.bootstrap_p5(sm["monthly_diff"], 1000, seed, C.block_months(hold)) > 0
for hold in P["holds_days"]:
    rate = np.mean([trial(s, hold) for s in range(200)])
    ok(rate <= 0.10, f"no edge, hold {hold}, blocks of {C.block_months(hold)} months: the bootstrap mark passes in {rate:.1%} of 200 random data sets (nominal 5%)")

shutil.rmtree(TMP)
print(f"\n{len(fails)} failed" if fails else "\nall passed"); sys.exit(1 if fails else 0)
