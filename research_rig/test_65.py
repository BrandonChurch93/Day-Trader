"""Plan 65 tests. Synthetic and hand-built inputs only; no real bar is read.
Run: PYTHONDONTWRITEBYTECODE=1 python3 research_rig/test_65.py"""
import copy
import datetime as dt
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score_65 as S  # noqa: E402

CFG = S.load_config(S.CONFIG.read_bytes())
SESS = S.load_calendar((HERE / "calendar_65.json").read_bytes(), CFG)
DATES = [x[0] for x in SESS]
FAILS = []
COUNT = [0]


def check(name, cond):
    COUNT[0] += 1
    if not cond:
        FAILS.append(name)
        print("FAIL", name)


def refuses(name, fn, code):
    try:
        fn()
    except S.Refused as e:
        check(name, str(e).startswith(code))
        return
    check(name + " (did not refuse)", False)


def run_rule(blobs):
    daily, intra, acts = S.parse(blobs, SESS, CFG)
    last, week4, first = S.session_flags(SESS, CFG)
    cs, rs = S.total_returns(daily["SPY"], acts["SPY"], DATES)
    cb, rb = S.total_returns(daily["IEF"], acts["IEF"], DATES)
    ps = S.partial_returns(intra["SPY"], daily["SPY"], acts["SPY"], SESS, CFG)
    pb = S.partial_returns(intra["IEF"], daily["IEF"], acts["IEF"], SESS, CFG)
    return S.signals(rs, rb, ps, pb, last, week4, first, CFG), (rs, rb, ps, pb, last, week4, first, cs, cb)


def edit_bars(blobs, name, pred, f):
    rows = json.loads(blobs[name])
    for r in rows:
        if pred(r["t"]):
            r["c"] = f(r["c"])
            r["o"] = r["h"] = r["l"] = r["c"]
    out = dict(blobs)
    out[name] = json.dumps(rows).encode()
    return out


def test_formulas():
    w = S.drift(0.6, 0.01, -0.005)
    check("drift hand", abs(w - 0.6 * 1.01 / (0.6 * 1.01 + 0.4 * 0.995)) < 1e-15)
    check("deltas 26", len(S.deltas(CFG)) == 26 and S.deltas(CFG)[0] == 0 and abs(S.deltas(CFG)[-1] - 0.025) < 1e-12)
    c, r = S.total_returns({"a": 100.0, "b": 50.0, "c": 51.0}, {"b": (1.0, 2.0)}, ["a", "b", "c"])
    check("total return split and cash", abs(r[1] - (2 * 51.0 / 100.0 - 1)) < 1e-12 and abs(r[2] - (51 / 50 - 1)) < 1e-12)


def test_flags_and_clock():
    last, week4, first = S.session_flags(SESS, CFG)
    jan = [i for i, d in enumerate(DATES) if d.startswith("2016-01")]
    check("jan 2016 last", DATES[jan[-1]] == "2016-01-29" and last[jan[-1]] and last.sum() == len({d[:7] for d in DATES}) - 1)
    check("jan 2016 week4", [DATES[i] for i in jan if week4[i]] == ["2016-01-25", "2016-01-26", "2016-01-27",
                                                                       "2016-01-28", "2016-01-29"])
    check("first", first[0] and DATES[[i for i in range(len(DATES)) if first[i]][1]] == "2016-02-01")
    k = DATES.index("2016-01-04")
    check("bar winter 15:30 ET", S.signal_bar_start(SESS[k], CFG) == "2016-01-04T20:30:00Z")
    k = DATES.index("2016-07-01")
    check("bar summer 15:30 ET", S.signal_bar_start(SESS[k], CFG) == "2016-07-01T19:30:00Z")
    k = DATES.index("2016-11-25")
    check("bar early close 12:30 ET", S.signal_bar_start(SESS[k], CFG) == "2016-11-25T17:30:00Z")
    check("last session", DATES[-1] == "2026-11-25" and len(DATES) == 2741)


def test_signal_state():
    n = 40
    rs = np.zeros(n)
    rb = np.zeros(n)
    rs[5] = 0.05                      # stocks jump on day 5
    ps, pb = rs.copy(), rb.copy()
    ps[0] = pb[0] = np.nan
    last = np.zeros(n, bool)
    last[20] = True
    week4 = np.zeros(n, bool)
    week4[16:21] = True
    first = np.zeros(n, bool)
    first[21] = True
    w, wlag, th, ch = S.signals(rs, rb, ps, pb, last, week4, first, CFG)
    up = S.drift(0.6, 0.05, 0.0) - 0.6
    check("threshold day of jump", abs(th[5] - 0.5 * -up / 0.015) < 1e-12)
    # every delta up to 2.5% resets on a 1.8 point drift? only those <= the drift
    ds = S.deltas(CFG)
    kept = (ds > up + 1e-12)
    check("threshold day after", abs(th[6] - 0.5 * -np.mean(np.where(kept, up, 0.0)) / 0.015) < 1e-12)
    check("calendar outside week4 is zero", ch[10] == 0.0)
    check("calendar in week4 sign", ch[16] == 0.5 * np.sign(-up))
    check("calendar first day uses lag 4", ch[21] == 0.5 * np.sign(up))
    check("w is sum of halves", np.allclose(w[1:], th[1:] + ch[1:]))
    wk2 = week4.copy()
    wk2[36:40] = True
    _, _, _, ch_reset = S.signals(rs, rb, ps, pb, last, wk2, first, CFG)
    _, _, _, ch_noreset = S.signals(rs, rb, ps, pb, np.zeros(n, bool), wk2, first, CFG)
    check("calendar reset at month end", ch_reset[37] == 0.0 and ch_noreset[37] == 0.5 * np.sign(-up))
    # two-sided: a fall resets too
    rs3, ps3 = np.zeros(n), np.zeros(n)
    rs3[5] = ps3[5] = -0.05
    ps3[0] = np.nan
    _, _, th3, _ = S.signals(rs3, rb, ps3, pb, last, week4, first, CFG)
    dn = S.drift(0.6, -0.05, 0.0) - 0.6
    kept3 = ds > abs(dn) + 1e-12
    check("two-sided reset", abs(th3[6] - 0.5 * -np.mean(np.where(kept3, dn, 0.0)) / 0.015) < 1e-12)
    check("lag one is full signal of prior day", abs(wlag[6] - 0.5 * (-up / 0.015)) < 1e-12)


def test_no_lookahead():
    blobs = S.synthetic_inputs(SESS, CFG)
    (w, wlag, th, ch), _ = run_rule(blobs)
    k = 900
    d = DATES[k]
    b2 = edit_bars(blobs, "SPY_1d.json", lambda t: t[:10] >= d, lambda c: round(c * 1.07, 2))
    b2 = edit_bars(b2, "IEF_1d.json", lambda t: t[:10] >= d, lambda c: round(c * 0.95, 2))
    (w2, wlag2, _, _), _ = run_rule(b2)
    check("close k does not move w[k]", np.allclose(w[:k + 1], w2[:k + 1], equal_nan=True))
    check("close k does not move wlag[k]", np.allclose(wlag[:k + 1], wlag2[:k + 1], equal_nan=True))
    b3 = edit_bars(blobs, "SPY_15m.json", lambda t: t[:10] == d, lambda c: round(c * 1.07, 2))
    (w3, wlag3, _, _), _ = run_rule(b3)
    check("signal bar k moves w[k] only", np.allclose(w[:k], w3[:k], equal_nan=True) and w[k] != w3[k]
          and np.allclose(w[k + 1:], w3[k + 1:], equal_nan=True))
    check("signal bar does not move lag clock", np.allclose(wlag, wlag3, equal_nan=True))
    b4 = edit_bars(blobs, "SPY_15m.json", lambda t: t[:10] == d, lambda c: c)
    rows = [r for r in json.loads(b4["SPY_15m.json"]) if r["t"][:10] != d]
    b4["SPY_15m.json"] = json.dumps(rows).encode()
    (w4, _, _, _), _ = run_rule(b4)
    check("missing signal bar gives nan for that day only", np.isnan(w4[k]) and np.allclose(w4[k + 1:], w[k + 1:]))


def test_alt_reversal():
    blobs = S.synthetic_inputs(SESS, CFG)
    (w, _, _, ch), z = run_rule(blobs)
    rs, rb, ps, pb, last, week4, first = z[:7]
    _, _, _, cha = S.signals(rs, rb, ps, pb, last, week4, first, CFG, alt_reversal=True)
    cfg5 = dict(CFG, reversal_lag=5)
    _, _, _, ch5 = S.signals(rs, rb, ps, pb, last, week4, first, cfg5)
    fi = [i for i in range(10, len(DATES)) if first[i]]
    check("alt reversal is the window start, five sessions back", np.allclose(cha[fi], ch5[fi]))
    check("alt reversal differs somewhere", not np.allclose(cha[fi], ch[fi]))
    nf = [i for i in range(1, len(DATES)) if not first[i]]
    check("alt reversal same off first days", np.allclose(cha[nf], ch[nf], equal_nan=True))


def test_economics():
    dates = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07", "2020-01-08"]
    cfg = copy.deepcopy(CFG)
    w = np.array([np.nan, 0.5, -0.5, np.nan, np.nan])
    rs = np.array([np.nan, 0.0, 0.01, -0.02, 0.0])
    rb = np.array([np.nan, 0.0, 0.002, 0.001, 0.0])
    cs = np.array([300.0] * 5)
    cb = np.array([100.0] * 5)
    net, gross, keep = S.economics(w, rs, rb, cs, cb, dates, 0.005, 0.006, cfg, [1, 2, 3])
    c = 2e-4 + 2e-4                     # both legs at 2 bp (cent is smaller at these prices)
    e1 = 0.5 * (0.01 - 0.002) - 0.5 * c - 0.5 * 0.006 * 3 / 365
    e2 = -0.5 * (-0.02 - 0.001) - 1.0 * c - 0.5 * 0.005 * 1 / 365 - 0.5 * c    # flip, then flat day cost lands here
    check("economics keep", keep == [1, 2])
    check("economics hand", np.allclose(net, [e1, e2]) and np.allclose(gross, [0.5 * 0.008, 0.5 * 0.021]))
    cs2 = np.array([4.0] * 5)
    check("cent floor", abs(S.leg_cost(cs2, cfg)[0] - 0.0025) < 1e-15)
    net2, _, _ = S.economics(w, rs, rb, cs, cb, dates, 0.005, 0.006, cfg, [1, 2, 3], round_trip=True)
    check("round trip", abs(net2[0] - (0.5 * 0.008 - 0.5 * 2 * c - 0.5 * 0.006 * 3 / 365)) < 1e-15)


def test_marks():
    x = np.array([1.0, -0.5, 2.0, 0.5])
    g = np.array([1, 1, 2, 2])
    m = x.mean()
    gs = np.array([(1 - m) + (-0.5 - m), (2 - m) + (0.5 - m)])
    se = math.sqrt(2 / 1 * (gs ** 2).sum()) / 4
    check("cluster t hand", abs(S.cluster_t(x, g) - m / se) < 1e-12)
    cfg = copy.deepcopy(CFG)
    rng = np.random.default_rng(1)
    exits = DATES[127:]
    y = 0.001 + 0.01 * rng.standard_normal(len(exits))
    r = S.marks(y, exits, cfg)
    check("marks n", r["n"] == 2614 and r["marks"]["sessions"])
    check("trim drop count", r["trim_dropped"] == math.ceil(0.01 * 2614))
    check("trim value", abs(r["trim_mean"] - np.sort(y)[:-27].mean()) < 1e-15)
    y2 = y.copy()
    years = np.array([int(d[:4]) for d in exits])
    y2[years >= 2020] = -1.0
    r2 = S.marks(y2, exits, cfg)
    check("years counted", r2["years_positive"] == sum(y[years == k].mean() > 0 for k in range(2016, 2020)))
    r3 = S.marks(y[:100], exits[:100], cfg)
    check("empty years not positive", r3["by_year"]["2025"] is None and not r3["marks"]["sessions"])


def test_parse_refusals():
    blobs = S.synthetic_inputs(SESS, CFG)
    bad = dict(blobs)
    rows = json.loads(bad["SPY_1d.json"])
    rows[3]["x"] = 1
    bad["SPY_1d.json"] = json.dumps(rows).encode()
    refuses("extra field", lambda: S.parse(bad, SESS, CFG), "P65_FORMAT")
    bad = dict(blobs)
    rows = json.loads(bad["IEF_1d.json"])
    rows.append(dict(rows[0]))
    bad["IEF_1d.json"] = json.dumps(rows).encode()
    refuses("duplicate", lambda: S.parse(bad, SESS, CFG), "P65_FORMAT")
    bad = dict(blobs)
    rows = json.loads(bad["IEF_1d.json"])
    rows[0]["t"] = rows[0]["t"][:11] + "13:00:00Z"
    bad["IEF_1d.json"] = json.dumps(rows).encode()
    refuses("daily stamp", lambda: S.parse(bad, SESS, CFG), "P65_FORMAT")
    bad = dict(blobs)
    rows = json.loads(bad["SPY_1d.json"])
    rows[5]["c"] = -1
    bad["SPY_1d.json"] = json.dumps(rows).encode()
    refuses("negative close", lambda: S.parse(bad, SESS, CFG), "P65_FORMAT")
    bad = dict(blobs)
    bad["actions.json"] = json.dumps([{"symbol": "SPY", "type": "cash", "ex_date": "2020-01-02"}]).encode()
    refuses("action fields", lambda: S.parse(bad, SESS, CFG), "P65_FORMAT")
    bad = dict(blobs)
    rows = [r for r in json.loads(bad["SPY_1d.json"]) if r["t"][:10] != "2019-05-01"]
    bad["SPY_1d.json"] = json.dumps(rows).encode()
    daily, intra, acts = S.parse(bad, SESS, CFG)
    refuses("missing SPY daily", lambda: S.score(daily, intra, acts, SESS, CFG), "P65_MISSING_DAILY SPY")
    cov = S.coverage(daily, intra, SESS, CFG)
    check("coverage counts a missing daily bar", cov["missing_daily"]["SPY"] == 1)


def test_audit_fixes():
    last, week4, first = S.session_flags(SESS, CFG)
    nov = {d: (bool(week4[i]), bool(last[i])) for i, d in enumerate(DATES) if d.startswith("2026-11")}
    check("november 2026 week4", [d for d, v in nov.items() if v[0]] == ["2026-11-23", "2026-11-24", "2026-11-25"])
    check("sample end is not a month end", not nov["2026-11-25"][1])
    blobs = S.synthetic_inputs(SESS, CFG)

    def mutate(name, f):
        b = dict(blobs)
        rows = json.loads(b[name])
        f(rows)
        b[name] = json.dumps(rows).encode()
        return b
    k = DATES.index("2016-01-05")
    refuses("daily 04 and 05 same day", lambda: S.parse(mutate("SPY_1d.json", lambda r: r.append(
        dict(r[k], t=r[k]["t"][:11] + "04:00:00Z"))), SESS, CFG), "P65_FORMAT")
    refuses("wrong DST stamp", lambda: S.parse(mutate("SPY_1d.json", lambda r: r[k].update(
        t=r[k]["t"][:11] + "04:00:00Z")), SESS, CFG), "P65_FORMAT daily stamp")
    refuses("bool close", lambda: S.parse(mutate("IEF_1d.json", lambda r: r[3].update(c=True)), SESS, CFG), "P65_FORMAT")
    refuses("high below close", lambda: S.parse(mutate("IEF_1d.json", lambda r: r[3].update(h=r[3]["c"] / 2)), SESS, CFG),
            "P65_FORMAT")
    refuses("negative volume", lambda: S.parse(mutate("IEF_15m.json", lambda r: r[3].update(v=-1)), SESS, CFG), "P65_FORMAT")
    refuses("off-grid bar", lambda: S.parse(mutate("IEF_15m.json", lambda r: r[3].update(t=r[3]["t"][:14] + "07:00Z")),
                                            SESS, CFG), "P65_FORMAT time")
    refuses("not a real date", lambda: S.parse(mutate("IEF_15m.json", lambda r: r[3].update(t="2019-02-30T20:30:00Z")),
                                               SESS, CFG), "P65_FORMAT time")
    b = dict(blobs)
    b["SPY_1d.json"] = blobs["SPY_1d.json"].replace(b'"v": 1000}', b'"v": 1000, "v": 1}', 1)
    refuses("duplicate JSON key", lambda: S.parse(b, SESS, CFG), "P65_FORMAT")

    def acts(rows):
        b2 = dict(blobs)
        b2["actions.json"] = json.dumps(rows).encode()
        return b2
    refuses("split ratio 1", lambda: S.parse(acts([{"symbol": "SH", "type": "split", "ex_date": "2020-01-02", "ratio": 1}]),
                                             SESS, CFG), "P65_FORMAT actions value")
    two = [{"symbol": "SPY", "type": "cash", "ex_date": "2020-01-02", "amount": 1.0}] * 2
    refuses("duplicate action", lambda: S.parse(acts(two), SESS, CFG), "P65_FORMAT duplicate action")
    refuses("action bad date", lambda: S.parse(acts([{"symbol": "SPY", "type": "cash", "ex_date": "2020-02-30",
                                                      "amount": 1.0}]), SESS, CFG), "P65_FORMAT actions date")
    refuses("action off calendar", lambda: S.parse(acts([{"symbol": "SPY", "type": "cash", "ex_date": "2020-01-04",
                                                          "amount": 1.0}]), SESS, CFG), "P65_FORMAT action date")
    check("constant series t undefined", math.isnan(S.cluster_t(np.full(2400, 0.001), np.arange(2400) // 4)))
    z = S.marks(np.array([]), [], CFG)
    check("empty marks complete", z["marks_met"] == 0 and z["pass"] is False and set(z["marks"]) == {
        "sessions", "money", "evidence", "trim", "years"})
    cal = json.loads((HERE / "calendar_65.json").read_text())
    bad = dict(cal, sessions=cal["sessions"][:5] + [cal["sessions"][3]] + cal["sessions"][5:])
    refuses("calendar order", lambda: S.load_calendar(json.dumps(bad).encode(), CFG), "P65_CALENDAR")
    short = dict(cal, sessions=[x for x in cal["sessions"] if x[0] <= "2026-11-30"])
    refuses("calendar needs next month", lambda: S.load_calendar(json.dumps(short).encode(), CFG), "P65_CALENDAR")
    # SH line pays the exit at the last close
    dates = ["2020-01-02", "2020-01-03", "2020-01-06"]
    daily = {"IEF": {d: 100.0 for d in dates}, "SH": {d: 20.0 for d in dates}}
    a0 = {"IEF": {}, "SH": {}}
    r = S.sh_version(np.array([np.nan, -1.0, -1.0]), daily, a0, dates, [0, 1], CFG)
    entry = max(2e-4 * 5 * 100, 0.01 * 5) + max(2e-4 * 25 * 20, 0.01 * 25)
    check("sh entry and exit", abs(r["mean"] - (-(entry + entry) / 1000) / 2) < 1e-12 and r["sessions_held"] == 1)


def write_inputs(path, blobs):
    path.mkdir(mode=0o700)
    os.chmod(path, 0o700)
    for n, b in blobs.items():
        p = path / n
        p.write_bytes(b)
        os.chmod(p, 0o600)


def test_validate_and_modes(tmp):
    blobs = S.synthetic_inputs(SESS, CFG)
    rows = [r for r in json.loads(blobs["IEF_15m.json"]) if r["t"][:10] not in ("2018-03-05", "2021-06-07")]
    blobs["IEF_15m.json"] = json.dumps(rows).encode()
    d = tmp / "inputs"
    write_inputs(d, blobs)
    cov = S.validate(d)
    check("validate judged sessions", cov["judged_candidates"] == 2614 and cov["judged_sessions"] == 2612)
    check("validate missing bars", cov["missing_signal_bar"] == {"SPY": 0, "IEF": 2})
    check("validate digest", cov["inputs_sha256"] == S.inputs_digest(blobs))
    check("validate prints no return", not any(k in json.dumps(cov) for k in ("mean", "sharpe", "net")))
    os.chmod(d / "SPY_1d.json", 0o644)
    refuses("file mode", lambda: S.validate(d), "P65_INPUTS")
    os.chmod(d / "SPY_1d.json", 0o600)
    (d / "extra.json").write_bytes(b"[]")
    refuses("extra file", lambda: S.validate(d), "P65_INPUTS")
    (d / "extra.json").unlink()
    os.environ["P65_X"] = "1"
    refuses("env", lambda: S.validate(d), "P65_ENV")
    del os.environ["P65_X"]
    cov2, res = S.run_synthetic()
    cov3, res2 = S.run_synthetic()
    check("synthetic deterministic", json.dumps(res, sort_keys=True, default=float) == json.dumps(res2, sort_keys=True, default=float))
    check("synthetic shown lines", set(res["shown_only"]) == {"post_paper", "without_stress_months", "threshold_half",
                                                              "calendar_half", "lag_one_clock", "full_daily_round_trip",
                                                              "tlt_for_ief", "sh_cash_account",
                                                              "calendar_reversal_window_start"})
    check("post paper subset", res["shown_only"]["post_paper"]["n"] == sum(x >= "2023-04-01" for x in DATES[127:]))
    check("stress subset", res["shown_only"]["without_stress_months"]["n"] == sum(x[:7] != "2020-03" for x in DATES[127:]))


def git(root, *a):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    r = subprocess.run(["git", "-C", str(root), *a], capture_output=True, env=env, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def make_repo(tmp, status="Status: FROZEN", score_bytes=None):
    root = tmp / "repo"
    (root / "research_rig").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "config/thresholds.yaml").write_bytes(S.CONFIG.read_bytes())
    files = {S.PLAN_NAME: f"# Plan 65\n\n{status}\n".encode(),
             "score_65.py": score_bytes or (HERE / "score_65.py").read_bytes(),
             "test_65.py": (HERE / "test_65.py").read_bytes(), "calendar_65.json": (HERE / "calendar_65.json").read_bytes(),
             "power_65.py": b"# power\n", "POWER_65.json": b"{}\n"}
    for n, b in files.items():
        (root / "research_rig" / n).write_bytes(b)
    pins = {n: S.digest(b) for n, b in files.items()}
    pins[S.CONFIG_PIN] = S.config_block_sha256(S.CONFIG.read_bytes())
    (root / S.PINNED).write_text(json.dumps(pins, indent=1))
    (root / "research_rig/TRIAL_LEDGER.md").write_text(
        "| 208 | x | `research_rig/PREREG_65_stock_bond_rebalance_spread.md` | row |\n")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "freeze")
    return root, git(root, "rev-parse", "HEAD")


def approve(root, frozen, digest_hex, extra=None):
    (root / S.APPROVAL).write_text(f"Approved by the lead: plan 65 ledger 208, one scored run, freeze commit {frozen}, "
                                   f"inputs SHA-256 {digest_hex}.\n")
    git(root, "add", S.APPROVAL)
    if extra:
        (root / extra).write_text("x\n")
        git(root, "add", extra)
    git(root, "commit", "-q", "-m", "approve")
    return git(root, "rev-parse", "HEAD")


def test_gate(tmp):
    blobs = S.synthetic_inputs(SESS, CFG)
    inp = tmp / "gin"
    write_inputs(inp, blobs)
    dg = S.inputs_digest(blobs)
    root, frozen = make_repo(tmp)
    cfgp = root / "config/thresholds.yaml"
    refuses("gate on freeze commit", lambda: S.authorize(frozen, root, cfgp), "P65_NOT_APPROVED")
    good = approve(root, frozen, dg)
    got = S.authorize(good, root, cfgp)
    check("gate passes", got[0] == dg)
    refuses("gate bad hash", lambda: S.authorize("0" * 40, root, cfgp), "P65_NOT_APPROVED")
    # go: run dir must exist and be empty
    run = tmp / "run"
    run.mkdir(mode=0o700)
    os.chmod(run, 0o755)
    refuses("run dir mode", lambda: S.go(good, inp, run, root, cfgp), "P65_RUN")
    os.chmod(run, 0o700)
    res = S.go(good, inp, run, root, cfgp)
    check("go writes result", (run / S.RESULT).exists() and (run / S.LOCK).exists() and res["judged"]["n"] == 2614)
    refuses("go twice", lambda: S.go(good, inp, run, root, cfgp), "P65_RUN")
    run2 = tmp / "run2"
    run2.mkdir()
    (run2 / S.LOCK).write_text("{}")
    refuses("lock exists", lambda: S.lock_file(run2 / S.LOCK, {}), "P65_ALREADY_USED")
    run3 = tmp / "run3"
    run3.mkdir()
    os.chmod(run3, 0o700)
    bad = approve_wrong_digest(tmp, blobs)
    refuses("go digest", lambda: S.go(bad[1], inp, run3, bad[0], bad[0] / "config/thresholds.yaml"), "P65_INPUTS digest")
    check("digest refusal leaves no lock", not os.listdir(run3))
    # missing SPY daily refuses before the lock
    b5 = dict(blobs)
    b5["SPY_1d.json"] = json.dumps([r for r in json.loads(b5["SPY_1d.json"]) if r["t"][:10] != "2019-05-01"]).encode()
    inp5 = tmp / "gin5"
    write_inputs(inp5, b5)
    root6, frozen6 = make_repo(tmp / "f")
    c6 = approve(root6, frozen6, S.inputs_digest(b5))
    run6 = tmp / "run6"
    run6.mkdir()
    os.chmod(run6, 0o700)
    refuses("missing daily before lock", lambda: S.go(c6, inp5, run6, root6, root6 / "config/thresholds.yaml"),
            "P65_MISSING_DAILY")
    check("missing daily leaves no lock", not os.listdir(run6))
    # approval file with an extra line
    root7, frozen7 = make_repo(tmp / "g")
    (root7 / S.APPROVAL).write_text(f"Approved by the lead: plan 65 ledger 208, one scored run, freeze commit {frozen7}, "
                                    f"inputs SHA-256 {dg}.\nextra\n")
    git(root7, "add", S.APPROVAL)
    git(root7, "commit", "-q", "-m", "approve")
    c7 = git(root7, "rev-parse", "HEAD")
    refuses("approval extra line", lambda: S.authorize(c7, root7, root7 / "config/thresholds.yaml"), "P65_NOT_APPROVED")
    # the same gate through the command line, in the temp repo (cases that refuse before any input is read)
    for name, rt, c in (("cli extra line", root7, c7), ("cli wrong commit", root7, "0" * 40), ("cli other file", None, None)):
        if rt is None:
            rt, fz = make_repo(tmp / "h")
            c = approve(rt, fz, dg, extra="research_rig/other.md")
        r = subprocess.run([sys.executable, str(rt / "research_rig/score_65.py"), "--go", "--approval-commit", c],
                           capture_output=True, text=True, env={k: v for k, v in os.environ.items()
                                                                 if k != "PYTHONDONTWRITEBYTECODE"} | {"PYTHONDONTWRITEBYTECODE": "1"})
        check(name, r.returncode == 2 and r.stdout.startswith("REFUSED P65_NOT_APPROVED"))
    r = subprocess.run([sys.executable, str(root7 / "research_rig/score_65.py"), "--synthetic"], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    check("cli synthetic", r.returncode == 0 and r.stdout.startswith("SYNTHETIC ONLY"))
    # approval adding another file
    root2, frozen2 = make_repo(tmp / "b")
    c2 = approve(root2, frozen2, dg, extra="research_rig/other.md")
    refuses("approval adds other file", lambda: S.authorize(c2, root2, root2 / "config/thresholds.yaml"), "P65_NOT_APPROVED")
    # plan not frozen
    root3, frozen3 = make_repo(tmp / "c", status="Status: DRAFT")
    c3 = approve(root3, frozen3, dg)
    refuses("plan not frozen", lambda: S.authorize(c3, root3, root3 / "config/thresholds.yaml"), "P65_NOT_APPROVED plan")
    # tracked change after approval
    root4, frozen4 = make_repo(tmp / "d")
    c4 = approve(root4, frozen4, dg)
    (root4 / "research_rig/power_65.py").write_text("# changed\n")
    refuses("tracked change", lambda: S.authorize(c4, root4, root4 / "config/thresholds.yaml"), "P65_NOT_APPROVED tracked")
    # approval naming a commit that is not its parent
    root5, frozen5 = make_repo(tmp / "e")
    (root5 / "research_rig/note.md").write_text("n\n")
    git(root5, "add", "-A")
    git(root5, "commit", "-q", "-m", "later")
    c5 = approve(root5, frozen5, dg)
    refuses("parent not freeze", lambda: S.authorize(c5, root5, root5 / "config/thresholds.yaml"), "P65_NOT_APPROVED the approval")


def test_cli_full(tmp):
    """Both real dispatch paths through the command line: a copy of the scorer whose only change is the WS constant,
    pointing at a temporary workspace, pinned in a temporary Git repo. Never touches the real workspace data."""
    src = (HERE / "score_65.py").read_bytes()
    old = b'WS = Path("/home/user/workspace")\n'
    check("one WS constant", src.count(old) == 1)
    ws = tmp / "ws"
    patched = src.replace(old, ('WS = Path("' + str(ws) + '")\n').encode())
    root, frozen = make_repo(tmp / "cli", score_bytes=patched)
    (ws / "rig/data").mkdir(parents=True)
    blobs = S.synthetic_inputs(SESS, CFG)
    write_inputs(ws / "rig/data/plan65_inputs", blobs)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, str(root / "research_rig/score_65.py")]
    r = subprocess.run(cmd + ["--validate-inputs"], capture_output=True, text=True, env=env)
    check("cli validate runs", r.returncode == 0)
    v = json.loads(r.stdout) if r.returncode == 0 else {}
    check("cli validate counts and digest", v.get("judged_sessions") == 2614 and v.get("inputs_sha256") == S.inputs_digest(blobs))
    check("cli validate wrote nothing", not (ws / "rig/data/replay_65").exists())
    c = approve(root, frozen, v.get("inputs_sha256", "0" * 64))
    r = subprocess.run(cmd + ["--go", "--approval-commit", c], capture_output=True, text=True, env=env)
    check("cli go needs the run dir", r.returncode == 2 and "P65_RUN" in r.stdout)
    run = ws / "rig/data/replay_65"
    run.mkdir()
    os.chmod(run, 0o700)
    r = subprocess.run(cmd + ["--go", "--approval-commit", c], capture_output=True, text=True, env=env)
    check("cli go runs", r.returncode == 0 and json.loads(r.stdout or "{}").get("n") == 2614)

    def no_nan(x):
        raise ValueError(x)
    try:
        out = json.loads((run / S.RESULT).read_text(), parse_constant=no_nan)
        check("cli result is standard JSON", out["judged"]["n"] == 2614 and out["approval_commit"] == c)
    except (ValueError, OSError, KeyError):
        check("cli result is standard JSON", False)
    r = subprocess.run(cmd + ["--go", "--approval-commit", c], capture_output=True, text=True, env=env)
    check("cli go is one shot", r.returncode == 2 and "REFUSED" in r.stdout)


def test_marks_exact_witness():
    exits = DATES[127:127 + 2400]
    wk = [S.week_key(d) for d in exits]
    x = np.full(2400, 2.0 ** -9)
    idx = {}
    for i, k in enumerate(wk):
        idx.setdefault(k, []).append(i)
    for members in idx.values():              # +h, -h in successive pairs; an odd last day keeps the base
        for a, b in zip(members[0::2], members[1::2]):
            x[a] += 2.0 ** -10
            x[b] -= 2.0 ** -10
    x[-1] += 2.0 ** -48
    r = S.marks(x, exits, CFG)
    check("evidence witness finite large t", r["t_week"] is not None and abs(r["t_week"] - 1.3178592545209525e15) < 1e3)
    check("evidence witness passes", all(r["marks"].values()))


def test_sub_breach():
    ds = S.deltas(CFG)
    w1 = 0.6 + ds[-1] - 5e-13
    n = 4
    rs = np.zeros(n); rb = np.zeros(n)
    rs[1] = 0.4 * w1 / (0.6 * (1 - w1)) - 1
    ps = np.zeros(n); pb = np.zeros(n)
    ps[1] = rs[1]
    f = np.zeros(n, bool)
    _, _, th, _ = S.signals(rs, rb, ps, pb, f, f, f, CFG)
    d1 = S.drift(0.6, rs[1], 0.0)
    want = -0.5 * (d1 - 0.6) / len(ds) / CFG["threshold_scale"]
    check("sub-breach close below largest delta", abs(d1 - 0.6) < ds[-1])
    check("sub-breach no reset at largest delta", abs(th[2] - want) < 1e-12 and th[2] < -0.032)


def test_cluster_scale():
    rng = np.random.default_rng(3)
    x = 0.001 + 0.01 * rng.standard_normal(2400)
    g = np.arange(2400) // 5
    t1 = S.cluster_t(x, g)
    check("cluster t scale free", abs(S.cluster_t(x * 1e-9, g) - t1) < 1e-9 * abs(t1)
          and abs(S.cluster_t(x * 1e9, g) - t1) < 1e-9 * abs(t1))
    check("cluster t exact tiny variance", S.cluster_t(np.array([2., -1., 2., -1. + 2. ** -45]), np.array([0, 0, 1, 1])) > 1e13)
    w = np.tile([.007, .010, .009, .011], 100)
    gw = np.arange(400) // 3
    tw = S.cluster_t(w, gw)
    check("cluster t extreme scales", all(abs(S.cluster_t(w * f, gw) - tw) < 1e-12 * tw for f in (1e-17, 1e17, 1e-200, 1e200)))
    check("jsonable", S.jsonable({"a": float("nan"), "b": [np.float64(1.5), float("inf")]}) == {"a": None, "b": [1.5, None]})


def approve_wrong_digest(tmp, blobs):
    root, frozen = make_repo(tmp / "w")
    return root, approve(root, frozen, "f" * 64)


def main():
    test_formulas()
    test_flags_and_clock()
    test_signal_state()
    test_no_lookahead()
    test_alt_reversal()
    test_economics()
    test_marks()
    test_parse_refusals()
    test_audit_fixes()
    with tempfile.TemporaryDirectory() as t:
        test_validate_and_modes(Path(t))
    with tempfile.TemporaryDirectory() as t:
        test_gate(Path(t))
    with tempfile.TemporaryDirectory() as t:
        test_cli_full(Path(t))
    test_cluster_scale()
    test_sub_breach()
    test_marks_exact_witness()
    print(f"{COUNT[0] - len(FAILS)} of {COUNT[0]} checks pass")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
