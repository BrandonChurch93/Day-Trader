"""Plan 22 checks on invented fixtures only. No real bars are read."""
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_22 as G  # noqa: E402

RAW = {
    "judged_start": "2020-01-01", "judged_end": "2020-07-01", "shown_start": "2020-07-01",
    "shown_end": "2020-09-01", "wake_hour_utc": 14, "range_days": 21, "volume_days": 30,
    "volume_window_hours": 24, "min_volume_ratio": 1.5, "max_above_level_pct": 3.0, "max_names": 5,
    "min_parts": 3, "stall_days": 2, "stall_volume_ratio": 1.0, "top_rank": 30, "max_page_age_days": 45,
    "judged_cost_bps": 12, "shown_cost_bps": [1, 25, 40], "min_sharpe": 1.0, "max_drawdown": 0.4,
    "twins": 20, "twin_percentile": 95.0, "twin_seed": 7, "twin_max_draws": 1000,
    "min_positive_years": 1, "annual_days": 365, "drop_best": 3, "btc_line_days": 7,
    "calibration_seed": 1, "calibration_seeds": 2, "calibration_edges_pct": [0, 4],
    "calibration_coins": 6, "calibration_days": 200, "calibration_sigma_hourly": 0.006,
    "calibration_hl_spread": 0.002, "calibration_drift_hours": 72,
    "calibration_volume_boost": [2.0, 4.0], "calibration_fade_days": 30}
P = G.policy(RAW)
S = G.hour_of("2020-01-01")
N = 220 * 24
FAILS = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        FAILS.append(name)


def flat(price=100., qv=1000., n=N, start=S):
    c = np.full(n, price)
    return dict(start=start, o=c.copy(), h=c * 1.001, l=c * 0.999, c=c.copy(), qv=np.full(n, qv))


def tape(d):
    return G.Tape(d["start"], d["o"], d["h"], d["l"], d["c"], d["qv"])


def plant_break(d, wake, jump=1.01, vol=3.0, hold=None):
    """Price steps up at the hour before wake to jump x the flat high; volume x vol over 24h."""
    i = wake - d["start"]
    base_high = d["h"][i - 30]
    px = base_high * jump
    d["c"][i - 1:] = px
    d["o"][i:] = px
    d["h"][i - 1:] = px * 1.001
    d["l"][i - 1:] = px * 0.999
    d["o"][i - 1] = d["c"][i - 2]
    d["qv"][i - 24:i] *= vol
    if hold is not None:
        hold(d, i)
    return base_high


A = G.Asset(1, "AAAUSDT", -10**9, 10**9)
B = G.Asset(2, "BBBUSDT", -10**9, 10**9)
WAKE = S + 60 * 24 + 14


def sig_tests():
    d = flat()
    level = plant_break(d, WAKE)
    t = tape(d)
    got = G.signal(t, A, WAKE, P)
    check("fresh break on volume signals", isinstance(got, tuple) and abs(got[0] - level) < 1e-9)
    check("volume ratio is last 24h over the 30-day daily mean", isinstance(got, tuple) and abs(got[1] - 3.0) < 1e-9)
    check("one wake later the old break is inside the new level", G.signal(t, A, WAKE + 24, P) == "no_break")
    d = flat(); level = plant_break(d, WAKE)
    i = WAKE - S
    d["c"][i + 10:] = level * 1.025; d["o"][i + 11:] = level * 1.025; d["h"][i + 10:] = level * 1.026
    d["qv"][i:] *= 3
    check("still above at the next wake is not fresh", G.signal(tape(d), A, WAKE + 24, P) == "not_fresh")
    d = flat(); plant_break(d, WAKE, vol=1.4)
    check("volume ratio 1.4 is refused", G.signal(tape(d), A, WAKE, P) == "low_volume")
    d = flat(); plant_break(d, WAKE, jump=1.031)
    check("more than 3% above the level is refused", G.signal(tape(d), A, WAKE, P) == "too_far_above")
    d = flat(); plant_break(d, WAKE, jump=1.029)
    check("2.9% above the level is taken", isinstance(G.signal(tape(d), A, WAKE, P), tuple))
    d = flat(); plant_break(d, WAKE); d["c"][WAKE - S - 300] = np.nan
    check("a missing hour in the 31 days refuses the signal", G.signal(tape(d), A, WAKE, P) == "incomplete")
    d = flat(); plant_break(d, WAKE)
    d0 = G.day_start(WAKE)
    d["h"][d0 - S + 3] = d["h"][0] * 1.5      # today's early high must not count in the level
    check("today's hours are not part of the 21-day level", isinstance(G.signal(tape(d), A, WAKE, P), tuple))
    d = flat(); plant_break(d, WAKE)
    d["h"][d0 - S - 21 * 24 - 1] = d["h"][0] * 1.5   # 22 days ago does not count
    check("day 22 back is outside the level", isinstance(G.signal(tape(d), A, WAKE, P), tuple))
    d = flat(); plant_break(d, WAKE)
    d["h"][d0 - S - 21 * 24] = d["h"][0] * 1.5      # day 21 back counts
    check("day 21 back is inside the level", G.signal(tape(d), A, WAKE, P) == "no_break")
    d = flat(); plant_break(d, WAKE)
    e = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in d.items()}
    for k in ("o", "h", "l", "c", "qv"):
        e[k][WAKE - S:] = e[k][WAKE - S:] * 7
    check("bars from the wake on cannot change the signal", G.signal(tape(e), A, WAKE, P) == G.signal(tape(d), A, WAKE, P))
    a2 = G.Asset(1, "AAAUSDT", WAKE - 700, 10**9)
    check("a segment younger than 31 days gives no signal", G.signal(tape(d), a2, WAKE, P) == "incomplete")


def members_of(*assets):
    return lambda w: list(assets)


def exit_tests():
    d = flat(); level = plant_break(d, WAKE)
    i = WAKE - S
    d["c"][i + 10 - 1:] = level * 0.99    # falls under the level the same day
    d["o"][i + 10:] = level * 0.99
    d["h"][i + 10 - 1:] = level * 0.991
    t = tape(d)
    ws = G.wakes(S, S + N, P)
    tr = G.rule_a({"AAAUSDT": t}, members_of(A), ws, P)
    check("one trade entered at the break wake", len(tr) == 1 and tr[0].entry == WAKE)
    check("exit on the next daily close under the level", tr and tr[0].exit == WAKE + 24 and tr[0].reason == "close_under_level")
    d = flat(); level = plant_break(d, WAKE)      # flat above level, volume back to 1x
    t = tape(d)
    tr = G.rule_a({"AAAUSDT": t}, members_of(A), ws, P)
    check("stall exit: no new high in 2 days and volume ratio under 1.0", tr and tr[0].reason == "stall" and tr[0].exit >= WAKE + 48)
    # The 24h-before-wake volume is still elevated at +48h? only the planted 24h was x3, so the ratio is back under 1.
    d = flat(); level = plant_break(d, WAKE)
    i = WAKE - S
    d["qv"][i:] *= 3        # volume stays high: stall needs both legs
    tr = G.rule_a({"AAAUSDT": tape(d)}, members_of(A), ws, P)
    check("no stall exit while volume stays high", tr and tr[0].reason != "stall" or not tr)
    tr = G.rule_a({"AAAUSDT": tape(d)}, members_of(A), ws, P, stall_needs_volume=False)
    check("shown short exit: no new high in 2 days alone", tr and tr[0].reason == "stall" and tr[0].exit == WAKE + 48)
    d = flat(); level = plant_break(d, WAKE)
    i = WAKE - S
    d["h"][i + 30] = d["h"][i] * 1.05         # a new high inside 2 days
    tr = G.rule_a({"AAAUSDT": tape(d)}, members_of(A), ws, P)
    check("a new high in the first 2 days blocks the stall exit", tr and tr[0].reason == "window_end")
    d = flat(); plant_break(d, WAKE); d["qv"][WAKE - S:] *= 3
    gone = G.Asset(1, "AAAUSDT", -10**9, 10**9)
    seq = lambda w: [gone] if w < WAKE + 24 * 3 else []
    tr = G.rule_a({"AAAUSDT": tape(d)}, seq, ws, P)
    check("leaving the list closes at the next wake", tr and tr[0].reason == "left_list" and tr[0].exit == WAKE + 72)


def rank_tests():
    tapes, assets = {}, []
    for k in range(7):
        d = flat(); plant_break(d, WAKE, vol=2 + k)
        a = G.Asset(10 + k, f"C{k}USDT", -10**9, 10**9)
        tapes[a.pair] = tape(d); assets.append(a)
    ws = G.wakes(S, S + N, P)
    tr = G.rule_a(tapes, lambda w: assets, ws, P, counts=(c := {}))
    picked = sorted(t.asset.coin for t in tr if t.entry == WAKE)
    check("at most 5 names, highest volume ratios first", picked == [12, 13, 14, 15, 16])
    check("signals over the slots are counted", c.get("signals_over_slots") == 2)


def book_tests():
    d = flat(); plant_break(d, WAKE)
    t = tape(d)
    tr = [G.Trade(A, WAKE, None, "window_end")]
    r = G.book(tr, {"AAAUSDT": t}, S, S + 100 * 24, 0, 3, P["wake_hour_utc"])
    px0 = t.open(WAKE); px1 = t.last_close(S + 100 * 24 - 1, -10**9)
    want = 2 / 3 + (1 / 3) * px1 / px0
    check("one name takes one third, the rest is cash", abs(r.equity[-1] - want) < 1e-9)
    r12 = G.book(tr, {"AAAUSDT": t}, S, S + 100 * 24, 12, 3, P["wake_hour_utc"])
    want12 = 2 / 3 + (1 / 3) * (1 - .0012) * px1 / px0 * (1 - .0012)
    check("12 bps charged on the buy and on the closing sale", abs(r12.equity[-1] - want12) < 1e-6)
    tapes = {}
    trs = []
    for k in range(4):
        dk = flat(100 + k)
        a = G.Asset(20 + k, f"D{k}USDT", -10**9, 10**9)
        tapes[a.pair] = tape(dk)
        trs.append(G.Trade(a, WAKE, None, "window_end"))
    r = G.book(trs, tapes, S, S + 100 * 24, 0, 3, P["wake_hour_utc"])
    check("four names take a quarter each, fully invested", abs(r.equity[-1] - 1) < 1e-9)
    check("cash never below zero with costs", min(G.book(trs, tapes, S, S + 100 * 24, 40, 3, P["wake_hour_utc"]).equity) > 0)
    # A coin that stops trading while held: closed at its last bar with volume, never dropped.
    dd = flat()
    cut = WAKE - S + 5 * 24
    dd["c"][cut:] = np.nan; dd["o"][cut:] = np.nan; dd["h"][cut:] = np.nan; dd["l"][cut:] = np.nan
    dd["c"][cut - 1] = 50.
    tt = tape(dd)
    tr = [G.Trade(A, WAKE, WAKE + 10 * 24, "left_list")]
    r = G.book(tr, {"AAAUSDT": tt}, S, S + 100 * 24, 0, 3, P["wake_hour_utc"])
    check("dead coin closed at its last traded close", abs(r.equity[-1] - (2 / 3 + 1 / 3 * 0.5)) < 1e-9
          and r.gaps["closed_at_last_bar"] == 1)
    # Missing fill at the exit wake: sold at the next traded open.
    de = flat()
    x = WAKE + 10 * 24
    de["c"][x - S] = np.nan; de["o"][x - S] = np.nan; de["h"][x - S] = np.nan; de["l"][x - S] = np.nan
    de["o"][x - S + 1] = 120.
    r = G.book([G.Trade(A, WAKE, x, "stall")], {"AAAUSDT": tape(de)}, S, S + 100 * 24, 0, 3, P["wake_hour_utc"])
    check("sale waits for the next bar with volume", abs(r.equity[-1] - (2 / 3 + 1 / 3 * 1.2)) < 1e-9
          and r.gaps["sales_after_wake"] == 1)
    dm = flat(); dm["qv"][WAKE - S] = 0
    r = G.book([G.Trade(A, WAKE, None, "x")], {"AAAUSDT": tape(dm)}, S, S + 100 * 24, 0, 3, P["wake_hour_utc"])
    check("buy skipped without a traded bar at the wake", r.gaps["buys_without_fill"] == 1 and abs(r.equity[-1] - 1) < 1e-12)


def metric_tests():
    res = G.Result(marks=[G.hour_of("2020-12-31"), G.hour_of("2021-01-01"), G.hour_of("2021-01-02")],
                   equity=[1.0, 1.1, 0.99], fills=[], gaps={})
    s = G.summary(res, P)
    check("drawdown from peak", abs(s["max_drawdown"] - 0.1) < 1e-12)
    check("1 January mark closes the old year", abs(s["by_year"][2020] - 0.1) < 1e-12 and abs(s["by_year"][2021] + 0.1) < 1e-12)
    r = np.array([0.01, -0.005, 0.02, 0.0])
    e = np.concatenate(([1.], np.cumprod(1 + r)))
    res = G.Result(marks=list(range(0, 24 * 5, 24)), equity=list(e), fills=[], gaps={})
    want = r.mean() / r.std(ddof=1) * math.sqrt(365)
    check("daily Sharpe, sample sd, 365 days", abs(G.summary(res, P)["sharpe"] - want) < 1e-9)
    j = G.judge({"final": 2., "sharpe": 1.1, "max_drawdown": .3, "positive_years": 5},
                {"final": 1.5}, list(np.linspace(1, 1.9, 100)), {**P, "min_positive_years": 5})
    check("all five tests pass together", j["pass"])
    j = G.judge({"final": 2., "sharpe": 1.1, "max_drawdown": .41, "positive_years": 5},
                {"final": 1.5}, list(np.linspace(1, 1.9, 100)), {**P, "min_positive_years": 5})
    check("drawdown 41% fails", not j["pass"] and not j["tests"]["drawdown"])


def twin_tests():
    tapes, assets = {}, []
    for k in range(6):
        a = G.Asset(30 + k, f"T{k}USDT", -10**9, 10**9)
        tapes[a.pair] = tape(flat(100 + k)); assets.append(a)
    ws = G.wakes(S, S + N, P)
    real = [G.Trade(assets[0], ws[40], ws[43], "stall"), G.Trade(assets[1], ws[41], ws[50], "stall"),
            G.Trade(assets[2], ws[100], None, "window_end")]
    at = G.fillable_members(tapes, lambda w: assets)
    s1 = G.twin_schedule(real, at, ws, P, random.Random(5))
    s2 = G.twin_schedule(real, at, ws, P, random.Random(5))
    month = lambda w: G.datetime.fromtimestamp(w * 3600, G.timezone.utc).strftime("%Y-%m")
    idx = {w: i for i, w in enumerate(ws)}
    check("twins are fixed by the seed", s1 == s2)
    check("twins keep entries per month", sorted(month(t.entry) for t in s1) == sorted(month(t.entry) for t in real))
    lens = sorted(idx[t.exit] - idx[t.entry] for t in s1 if t.exit is not None)
    check("twins keep the closed holding lengths", lens == [3, 9])
    half = lambda w: assets if w < ws[60] else assets[1:]
    at2 = G.fillable_members(tapes, half)
    f = G.twin_schedule(real, at2, ws, P, random.Random(9))
    outs = {}
    def nxt(a, j):
        q = j + 1
        while q < len(ws) and a in half(ws[q]):
            q += 1
        return q
    g = G.twin_schedule(real, at2, ws, P, random.Random(9), next_out=nxt)
    check("fast and plain twin exits agree when a coin leaves", f == g and any(t.reason == "left_list" for t in f) or f == g)
    finals, _ = G.twins(real, tapes, lambda w: assets, ws, S, S + N - N % 24, 12, P)
    check("twin count from config", len(finals) == P["twins"])


def switch_tests():
    d = flat(10000.)
    w = WAKE
    i = w - S
    d["c"][i - 1] = 9000.; d["l"][i - 1] = 8990.
    d0 = G.day_start(w)
    d["c"][i:] = 9000.; d["l"][i:] = 8990.; d["h"][i:] = 9010.; d["o"][i:] = 9000.
    back = d0 + 5 * 24
    d["c"][back - S - 1] = 10500.
    t = tape(d)
    ws = G.wakes(S, S + N, P)
    sw = G.BtcSwitch(t, A, ws, P)
    check("switch off when BTC breaks the 7-day low", sw.off(w))
    check("stays off until a daily close above that line", sw.off(w + 24 * 4))
    check("back on after the close above", not sw.off(back + 14))
    def gone(dd, j):
        for k in "ohlc":
            dd[k][j] = np.nan
    d2 = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in d.items()}
    gone(d2, i - 1)
    c2 = {}
    sw2 = G.BtcSwitch(tape(d2), A, ws, P, c2)
    check("rule C stays on when the wake's last close is missing (nothing imputed)",
          not sw2.off(w) and c2.get("btc_switch_unreadable", 0) >= 1)
    d3 = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in d.items()}
    gone(d3, back - S - 1)
    c3 = {}
    sw3 = G.BtcSwitch(tape(d3), A, ws, P, c3)
    check("rule C stays off when the recovery close is missing (nothing imputed)",
          sw3.off(w) and sw3.off(back + 14) and c3.get("btc_switch_recovery_unreadable", 0) >= 1)


def order_tests():
    # S1: a delayed sale due at the hour of the next wake fills before that wake's rebalance.
    tapes = {}
    x1, x2 = WAKE + 10 * 24, WAKE + 11 * 24
    dx = flat(100.)
    dx["qv"][x1 - S:x2 - S] = 0.
    dx["o"][x2 - S:] = 110.
    tapes["AAAUSDT"] = tape(dx)
    dy = flat(50.)
    dy["o"][x2 - S:] = 55.
    tapes["BBBUSDT"] = tape(dy)
    late = [G.Trade(A, WAKE, x1, "stall"), G.Trade(B, x2, None, "window_end")]
    direct = [G.Trade(A, WAKE, x2, "stall"), G.Trade(B, x2, None, "window_end")]
    r1 = G.book(late, tapes, S, S + 100 * 24, 12, 3, P["wake_hour_utc"])
    r2 = G.book(direct, tapes, S, S + 100 * 24, 12, 3, P["wake_hour_utc"])
    check("a delayed sale due at the next wake fills before that wake's rebalance",
          r1.gaps["sales_after_wake"] == 1 and max(abs(u - v) for u, v in zip(r1.equity, r2.equity)) < 1e-12)
    # S1, second edge: the delayed sale fills at a later wake with no other trade at that hour; the reset
    # still happens at that wake.
    da = flat(100.); da["qv"][x1 - S:x2 - S] = 0.
    db = flat(100.); db["o"][x2 - S:] = 200.; db["c"][x2 - S:] = 300.; db["o"][x2 - S + 1:] = 300.
    tp2 = {"AAAUSDT": tape(da), "BBBUSDT": tape(db)}
    late2 = [G.Trade(A, WAKE, x1, "stall"), G.Trade(B, WAKE, None, "window_end")]
    direct2 = [G.Trade(A, WAKE, x2, "stall"), G.Trade(B, WAKE, None, "window_end")]
    q1 = G.book(late2, tp2, S, S + 100 * 24, 12, 3, P["wake_hour_utc"])
    q2 = G.book(direct2, tp2, S, S + 100 * 24, 12, 3, P["wake_hour_utc"])
    check("a delayed sale alone at a later wake still resets the weights at that wake",
          q1.gaps["sales_after_wake"] == 1 and max(abs(u - v) for u, v in zip(q1.equity, q2.equity)) < 1e-12)
    # A delayed sale that fills at a 00:00 mark: the reset waits for that day's 14:00 wake (zero fee).
    m0 = G.day_start(x1) + 24                       # the 00:00 after the first exit wake
    da = flat(100.); da["qv"][x1 - S:m0 - S] = 0.
    db = flat(100.); db["o"][:] = 100.; db["c"][:] = 100.
    db["o"][x1 - S + 1:] = 200.; db["c"][x1 - S + 1:] = 200.
    w14 = m0 + P["wake_hour_utc"]
    db["o"][w14 - S:] = 300.; db["c"][w14 - S:] = 450.; db["o"][w14 - S + 1:] = 450.
    for d_ in (da, db):
        d_["h"] = np.maximum(d_["o"], d_["c"]) * 1.002; d_["l"] = np.minimum(d_["o"], d_["c"]) * .998
    tp4 = {"AAAUSDT": tape(da), "BBBUSDT": tape(db)}
    q4 = G.book([G.Trade(A, WAKE, x1, "stall"), G.Trade(B, WAKE, None, "window_end")], tp4, S, S + 100 * 24, 0, 3,
                P["wake_hour_utc"])
    # 1/3 each in A and B, 1/3 cash. A sells at 100 at 00:00: cash 2/3. B is worth 1 at the 14:00 open of 300:
    # equity 5/3, reset to 5/9 in B, then B rises 1.5 times: 5/3 - 5/9 + 5/9 * 1.5 = 35/18. A reset at 00:00
    # would give 17/9 instead.
    check("a delayed sale at 00:00 waits for the 14:00 wake to reset", q4.gaps["sales_after_wake"] == 1
          and abs(q4.equity[-1] - 35 / 18) < 1e-9)
    # Large moves since the last reset: four names gap up 1000 times, then a fifth enters. An exact
    # nonnegative equal-weight solution exists, so the book must not stop.
    tp3, tr3 = {}, []
    for k in range(5):
        dk = flat(100.)
        if k < 4:
            dk["o"][WAKE - S + 1:] = 100000.; dk["c"][WAKE - S:] = 100000.; dk["h"][WAKE - S:] = 100100.
        a = G.Asset(30 + k, f"E{k}USDT", -10**9, 10**9)
        tp3[a.pair] = tape(dk)
        tr3.append(G.Trade(a, WAKE if k < 4 else WAKE + 24, None, "window_end"))
    ok3 = True
    for bps in (1, 12, 25, 40):
        try:
            r3 = G.book(tr3, tp3, S, S + 100 * 24, bps, 3, P["wake_hour_utc"])
            ok3 = ok3 and min(r3.equity) > 0
        except AssertionError:
            ok3 = False
    check("large gains then a new name: the reset finds a nonnegative-cash target at every cost", ok3)
    # S2: rank first, then check fills. The top coin has no 14:00 bar; its slot stays cash.
    p1 = {**P, "max_names": 1}
    da = flat(); plant_break(da, WAKE, vol=4.0); da["qv"][WAKE - S] = 0.
    db = flat(); plant_break(db, WAKE, vol=3.0)
    tp = {"AAAUSDT": tape(da), "BBBUSDT": tape(db)}
    tr = G.rule_a(tp, lambda w: [A, B], [WAKE], p1, counts=(cc := {}))
    check("a zero-volume hour does not hand the slot to a lower-ranked coin",
          tr == [] and cc.get("signal_without_fill") == 1 and cc.get("signals_over_slots") == 1)


def lock_tests():
    sys.path.insert(0, str(HERE))
    import score_22 as SC
    env = {**os.environ, "PLAN22_TEST_ROOT": "/tmp/x"}
    for mode in ("--real", "--validate-inputs"):
        r = subprocess.run([sys.executable, str(HERE / "score_22.py"), mode, "--approval-commit", "0" * 40],
                           capture_output=True, text=True, env=env)
        check(f"{mode} refuses a PLAN22_ variable", r.returncode == 2 and "P22_ENV PLAN22_TEST_ROOT" in r.stdout)
    clean = {k: v for k, v in os.environ.items() if not k.startswith(("PLAN22_", "P22_"))}
    r = subprocess.run([sys.executable, str(HERE / "score_22.py"), "--real"], capture_output=True, text=True, env=clean)
    check("--real refuses without an approval commit", r.returncode == 2 and "P22_NOT_APPROVED" in r.stdout)
    r = subprocess.run([sys.executable, str(HERE / "score_22.py"), "--real", "--approval-commit", "0" * 40],
                       capture_output=True, text=True, env=clean)
    check("--real refuses from the draft folder", r.returncode == 2 and "P22_NOT_APPROVED" in r.stdout)
    with tempfile.TemporaryDirectory() as tmp:
        lk = Path(tmp) / SC.LOCK
        SC.lock_file(lk, {"a": 1})
        check("lock is read-only", (lk.stat().st_mode & 0o777) == 0o444)
        try:
            SC.lock_file(lk, {"a": 2}); ok = False
        except SC.Refused:
            ok = True
        check("second lock refused", ok)
        d2 = Path(tmp) / "b"; d2.mkdir()
        os.symlink(d2 / "nowhere", d2 / SC.RESULT)
        try:
            SC.lock_file(d2 / SC.LOCK, {}); ok = False
        except SC.Refused:
            ok = True
        check("a dangling result link counts as a used run", ok and not os.path.lexists(d2 / SC.LOCK))


def gate_tests():
    sys.path.insert(0, str(HERE))
    import score_22 as SC
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"; rig = root / "research_rig"; data = Path(tmp) / "data"
        rig.mkdir(parents=True); (root / "config").mkdir()
        def git(*a):
            return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True).stdout.strip()
        git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
        for n in SC.PINNED_NAMES:
            (rig / n).write_bytes(b"Status: FROZEN\n" if n == SC.PLAN_NAME else n.encode())
        (rig / "TRIAL_LEDGER.md").write_text("| 159 | plan 22 | PREREG_22_fable_rule_a.md |\n")
        (root / "config/thresholds.yaml").write_text("replay_22_plan:\n  value: {a: 1}\n")
        for n in SC.DATA_PINS:
            (data / n).parent.mkdir(parents=True, exist_ok=True); (data / n).write_bytes(n.encode())
        pins = {n: SC.digest((rig / n).read_bytes()) for n in SC.PINNED_NAMES}
        pins[SC.CONFIG_PIN] = SC.config_block_sha256((root / "config/thresholds.yaml").read_bytes())
        pins.update({n: SC.digest((data / n).read_bytes()) for n in SC.DATA_PINS})
        (rig / "PINNED_22.json").write_text(json.dumps(pins))
        git("add", "-A"); git("commit", "-qm", "freeze"); frozen = git("rev-parse", "HEAD")
        (rig / "APPROVAL_22.md").write_text(f"Approved by the lead: plan 22, one scored run, freeze commit {frozen}.\n")
        git("add", "-A"); git("commit", "-qm", "approve"); ok_c = git("rev-parse", "HEAD")
        P = {"repo": root, "here": rig, "config": root / "config/thresholds.yaml", "run": data, "data": data,
             "r13": data, "r16": data}

        def refused(commit, P=P):
            try:
                SC.authorize(commit, P)
                return None
            except SC.Refused as e:
                return str(e)
        check("gate passes on a clean approval commit", refused(ok_c) is None)
        check("gate refuses the freeze commit itself", refused(frozen) is not None)
        check("gate refuses code run from elsewhere", "not run from the repo" in (refused(ok_c, {**P, "here": HERE}) or ""))
        (rig / "common_22.py").write_text("changed")
        check("gate refuses a changed tracked file", "tracked files changed" in (refused(ok_c) or ""))
        git("checkout", "-q", "--", ".")
        (data / SC.DATA_PINS[0]).write_bytes(b"other")
        check("gate refuses a changed off-repo input", "P22_INPUT_CHANGED" in (refused(ok_c) or ""))
        (data / SC.DATA_PINS[0]).write_bytes(SC.DATA_PINS[0].encode())
        (rig / "APPROVAL_22.md").write_text("Approved by the lead: plan 22, one scored run, freeze commit " + "1" * 40 + ".\n")
        git("commit", "-qam", "bad approval"); bad = git("rev-parse", "HEAD")
        check("gate refuses an approval naming a commit that is not an ancestor", "not an ancestor" in (refused(bad) or ""))
        os.environ["P22_X"] = "1"
        try:
            check("gate refuses a P22_ variable", "P22_ENV" in (refused(ok_c) or ""))
        finally:
            del os.environ["P22_X"]


def validate_tests():
    sys.path.insert(0, str(HERE))
    import io
    import zipfile
    import score_22 as SC
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        rows = [[str((S + i) * 3600 * 1000), "1", "1.1", "0.9", "1", "5", "0", "5"] for i in range(3)]

        def arc(name, rs):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                z.writestr(name + ".csv", "\n".join(",".join(r) for r in rs) + "\n")
            raw = buf.getvalue()
            key = f"data/spot/monthly/klines/ETHUSDT/1h/{name}.zip"
            (data / "replay_22/archives" / key).parent.mkdir(parents=True, exist_ok=True)
            (data / "replay_22/archives" / key).write_bytes(raw)
            return key, {"where": "replay_22", "sha256": SC.digest(raw), "n": len(rs),
                         "first": int(rs[0][0]) // 1000, "last": int(rs[-1][0]) // 1000}
        PD = {"data": data}

        def why(man):
            try:
                SC.load_tapes(man, P=PD)
                return None
            except SC.Refused as e:
                return str(e)
        k, m = arc("good", rows)
        check("validation reads a clean archive", why({"archives": {k: m}}) is None)
        check("validation refuses a changed archive", "P22_ARCHIVE_CHANGED" in why({"archives": {k: {**m, "sha256": "0" * 64}}}))
        check("validation refuses a row count that differs", "P22_ROWS_DIFFER" in why({"archives": {k: {**m, "n": 4}}}))
        k2, m2 = arc("dup", rows + [rows[-1]])
        check("validation refuses a duplicate hour", "P22_BAD_OR_DUPLICATE_BAR" in why({"archives": {k2: m2}}))
        off = [list(r) for r in rows]; off[1][0] = str(int(off[1][0]) + 60000)
        k3, m3 = arc("off", off)
        check("validation refuses an hour off the grid", "P22_OFF_GRID" in why({"archives": {k3: m3}}))
        bad = [list(r) for r in rows]; bad[1][2] = "0.5"
        k4, m4 = arc("bad", bad)
        check("validation refuses a bar with high under open or close", "P22_BAD_OR_DUPLICATE_BAR" in why({"archives": {k4: m4}}))
        mal = [list(r) for r in rows]; mal[1][4] = "SECRETVALUE"
        k5, m5 = arc("mal", mal)
        msg5 = why({"archives": {k5: m5}}) or ""
        check("a malformed number is refused without echoing it", msg5.startswith("P22_BAD_ROW") and "SECRET" not in msg5)
        try:
            SC.validate_inputs(P, PD, {"archives": {k: m}})
            msg = None
        except SC.Refused as e:
            msg = str(e)
        except Exception as e:
            msg = repr(e)
        check("validation refuses inputs without BTCUSDT", msg == "P22_NO_BTCUSDT")
        import gzip
        import paths_22 as PA
        (data / "x.json.gz").write_bytes(gzip.compress(b"abc"))
        check("a gzip-only input reads as its uncompressed bytes", PA.read_input(data / "x.json") == b"abc")


def universe_tests():
    sys.path.insert(0, str(HERE))
    import score_22 as SC
    page = {"date": "2020-01-05", "known_at": (S + 100) * 3600,
            "top_raw": [{"cmcRank": r, "id": 1000 + r, "symbol": f"S{r}"} for r in range(1, 101)]}
    page["top_raw"][1]["id"] = 825
    rows = SC.top_rows(page, P)
    check("only ranks 1 to 30 are read", max(r["cmcRank"] for r in rows) == 30)
    check("stablecoins and wrapped coins are out", all(r["id"] not in SC.EXCLUDE_22 for r in rows) and len(rows) == 29)
    check("BTC, ETH and FTT are kept", not ({1, 1027, 4195} & SC.EXCLUDE_22))
    pages = [page]
    check("page usable only strictly after known_at", SC.page_at(pages, S + 100, P) is None and SC.page_at(pages, S + 101, P) is page)
    check("page older than 45 days is refused", SC.page_at(pages, S + 101 + 46 * 24, P) is None)


def lookahead_tests():
    import calibrate_22 as K
    p = {**P, "calibration_days": 400, "calibration_coins": 6, "judged_start_h": S}
    tapes, assets = K.market(3, p, 4)
    start, end = S, S + 400 * 24
    ws = G.wakes(start, end, p)
    cut = S + 200 * 24 + 14
    base = G.rule_a(tapes, lambda w: assets, ws, p)
    rng = np.random.default_rng(1)
    bent = {}
    for k, tp in tapes.items():
        i = cut - tp.start
        cols = [x.copy() for x in (tp.o, tp.h, tp.l, tp.c, tp.qv)]
        f = np.exp(np.cumsum(rng.normal(0, .01, len(cols[0]) - i)))
        for x in cols[:4]:
            x[i:] *= f
        cols[1][i:] = np.maximum(cols[1][i:], np.maximum(cols[0][i:], cols[3][i:]))
        cols[4][i:] *= 5
        bent[k] = G.Tape(tp.start, *cols)
    other = G.rule_a(bent, lambda w: assets, ws, p)
    before = lambda s: [(t.asset, t.entry, t.exit if t.exit is not None and t.exit < cut else None) for t in s if t.entry < cut]
    check("changing bars from a wake on leaves earlier entries and exits alone", before(base) == before(other) and len(base) > 0)
    r1 = G.book(base, tapes, start, end, 12, 3, P["wake_hour_utc"])
    r2 = G.book(other, bent, start, end, 12, 3, P["wake_hour_utc"])
    n = sum(1 for h in r1.marks if h <= cut - 14)
    check("marks before the change are identical", r1.equity[:n] == r2.equity[:n] and n > 100)


RIG_SRC = HERE.parents[1] / "dt-work/research_rig" if HERE.name != "research_rig" else HERE
OURS = ("common_22.py", "paths_22.py", "score_22.py", "fetch_22.py", "test_22.py", "calibrate_22.py")
THEIRS = ("fetch_13.py", "fetch_16.py", "common_13.py", "identity_asof_16_17.py")


def fixture_bar(pair, h):
    """Planted fixture paths, so the scored run has real trades in both windows.
    Base: flat at 100, highs and lows 0.2% out, quote volume 1e6 an hour.
    AAA: break at the 2020-01-20 wake (13:00 close 1.5% over the 21-day high, last 24 hours of volume x3), new
    highs for three days, then a close under the level (exit close_under_level).
    BBB: break at the 2020-03-10 wake, then flat at the new price with ordinary volume (exit stall).
    BTC: falls 5% at 10:00 on 2020-02-10 for four days, which trips rule C once in the judged window."""
    o = c = 100.
    qv = 1e6
    w_a, w_b = G.hour_of("2020-01-20") + 14, G.hour_of("2020-03-10") + 14
    if pair == "AAAUSDT" and h >= w_a - 10:
        k = h - w_a
        c = 101.5 if k < 0 else (102. + min(k, 72) / 72 if k < 4 * 24 else 99.)
        o = c
        if w_a - 24 <= h < w_a:
            qv = 3e6
    if pair == "BBBUSDT" and h >= w_b - 10:
        o = c = 101.5
        if w_b - 24 <= h < w_b:
            qv = 3e6
    if pair == "BTCUSDT":
        d = G.hour_of("2020-02-10") + 10
        if d <= h < d + 4 * 24:
            o = c = 95.
    return o, max(o, c) * 1.002, min(o, c) * .998, c, qv


def e2e_fixture(tmp, mutate=None):
    """A whole temporary workspace: repo with the real plan 22 code, a fixture config, ledger and plan,
    and fixture data in the fixed layout the code expects (rig/data next to the repo). mutate(stage, ctx) can
    change the rows, pages, identity rows and manifest before anything is pinned, so a refusal case is
    correctly pinned and reaches the input checks."""
    import io
    import zipfile
    import yaml
    sys.path.insert(0, str(HERE))
    import score_22 as SC
    mutate = mutate or (lambda stage, ctx: None)
    ws = Path(tmp) / "ws"; repo = ws / "dt-work"; rig = repo / "research_rig"; data = ws / "rig/data"
    rig.mkdir(parents=True); (repo / "config").mkdir()
    for n in OURS:
        (rig / n).write_bytes((HERE / n).read_bytes())
    for n in THEIRS:
        (rig / n).write_bytes((RIG_SRC / n).read_bytes())
    (rig / SC.PLAN_NAME).write_text("# Plan 22 fixture\n\nStatus: FROZEN\n")
    (rig / "TRIAL_LEDGER.md").write_text("| 159 | t | `research_rig/PREREG_22_fable_rule_a.md` | fixture |\n")
    raw = {**RAW, "judged_start": "2020-01-01", "judged_end": "2020-03-01", "shown_start": "2020-03-01",
           "shown_end": "2020-04-01", "twins": 10, "min_positive_years": 1}
    (repo / "config/thresholds.yaml").write_text(yaml.safe_dump({"replay_22_plan": {"value": raw}}))
    coins = [(1, "BTC"), (900001, "AAA"), (900002, "BBB")]
    rows = [{"cmcRank": k + 1, "id": i, "name": s, "slug": s.lower(), "symbol": s} for k, (i, s) in enumerate(coins)]
    rows += [{"cmcRank": r, "id": 910000 + r, "name": f"F{r}", "slug": f"f{r}", "symbol": f"FX{r}"} for r in range(4, 31)]
    pages = [{"date": d, "known_at": (G.hour_of(d) + 24) * 3600, "top_raw": rows}
             for d in ("2019-12-01", "2020-01-01", "2020-02-01", "2020-03-01")]
    ident = {"as_of_cutoff_utc": "2020-04-01", "as_of_rows": [
        {"market": "spot", "id": i, "pair": s + "USDT", "months": [], "notice_status": "CONFIRMED",
         "notice_at": "2019-01-01", "all_month_status": "CONFIRMED"} for i, s in coins]}
    arch = {}
    for _, s in coins:
        pair = s + "USDT"
        for month in ("2019-11", "2019-12", "2020-01", "2020-02", "2020-03"):
            a = G.hour_of(month + "-01")
            y, m = int(month[:4]), int(month[5:])
            b = G.hour_of(f"{y + (m == 12)}-{m % 12 + 1:02d}-01")
            unit = 3600 * (10**6 if (pair, month) == ("BBBUSDT", "2020-03") else 1000)   # one file in microseconds
            lines = []
            for h in range(a, b):
                o, hh, ll, cl, qv = fixture_bar(pair, h)
                lines.append([str(h * unit), repr(o), repr(hh), repr(ll), repr(cl), "1", str(h * unit + unit - 1), repr(qv)])
            arch[f"data/spot/monthly/klines/{pair}/1h/{pair}-1h-{month}.zip"] = {"rows": lines, "a": a, "b": b}
    ctx = {"arch": arch, "pages": pages, "ident": ident, "skip": set()}
    mutate("rows", ctx)
    man = {"archives": {}, "absent_days": {}, "no_binance_pair": []}
    for key, x in arch.items():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(key.rsplit("/", 1)[1].replace(".zip", ".csv"), "\n".join(",".join(r) for r in x["rows"]) + "\n")
        path = data / "replay_22/archives" / key
        path.parent.mkdir(parents=True, exist_ok=True)
        if key not in ctx["skip"]:
            path.write_bytes(buf.getvalue())
        man["archives"][key] = {"where": "replay_22", "sha256": SC.digest(buf.getvalue()), "n": len(x["rows"]),
                                "first": x["a"] * 3600, "last": (x["b"] - 1) * 3600, "bytes": len(buf.getvalue())}
    ctx["man"] = man
    mutate("man", ctx)
    (data / "replay_13").mkdir(parents=True); (data / "replay_16").mkdir(parents=True)
    (data / "replay_13/snapshots.json").write_text(json.dumps(ctx["pages"]))
    (data / "replay_16/identity_policy_16_17.json").write_text(json.dumps(ctx["ident"]))
    (data / "replay_22/manifest_22.json").write_text(json.dumps(man, sort_keys=True))
    pins = {n: SC.digest((rig / n).read_bytes()) for n in SC.PINNED_NAMES}
    pins[SC.CONFIG_PIN] = SC.config_block_sha256((repo / "config/thresholds.yaml").read_bytes())
    pins.update({n: SC.digest((data / n).read_bytes()) for n in SC.DATA_PINS})
    (rig / "PINNED_22.json").write_text(json.dumps(pins, indent=1, sort_keys=True))
    return SC, repo, rig, data


def e2e_tests():
    """Every real-mode path through the command line, in a temporary Git repo with fixture data."""
    with tempfile.TemporaryDirectory() as tmp:
        SC, repo, rig, data = e2e_fixture(tmp)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PLAN22_", "P22_"))}
        env.update(PYTHONDONTWRITEBYTECODE="1", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")

        def git(*a):
            return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True, env=env).stdout.strip()

        def cli(*a, extra=None):
            r = subprocess.run([sys.executable, str(rig / "score_22.py"), *a], capture_output=True, text=True,
                               env={**env, **(extra or {})}, cwd=tmp)
            return r.returncode, r.stdout + r.stderr
        run = data / "replay_22"
        used = lambda: os.path.lexists(run / SC.LOCK) or os.path.lexists(run / SC.RESULT)
        git("init", "-q"); git("add", "-A"); git("commit", "-qm", "freeze"); frozen = git("rev-parse", "HEAD")
        line = f"Approved by the lead: plan 22, one scored run, freeze commit {frozen}.\n"
        (rig / "APPROVAL_22.md").write_text(line)
        git("add", "-A"); git("commit", "-qm", "approve"); ok_c = git("rev-parse", "HEAD")
        rc, out = cli("--validate-inputs", "--approval-commit", ok_c)
        check("e2e: --validate-inputs passes on the approval commit and takes no lock",
              rc == 0 and '"validated": true' in out and '"gate_checked": true' in out and not used())
        rc, out = cli("--real", "--approval-commit", ok_c, extra={"P22_SEED": "1"})
        check("e2e: --real refuses a P22_ variable", rc == 2 and "P22_ENV" in out and not used())
        rc, out = cli("--real")
        check("e2e: --real refuses without an approval commit", rc == 2 and "P22_NOT_APPROVED" in out and not used())
        rc, out = cli("--real", "--approval-commit", frozen)
        check("e2e: --real refuses the freeze commit as approval", rc == 2 and "P22_NOT_APPROVED" in out and not used())
        (rig / "common_22.py").write_text((rig / "common_22.py").read_text() + "# x\n")
        rc, out = cli("--real", "--approval-commit", ok_c)
        check("e2e: --real refuses a changed tracked file", rc == 2 and "tracked files changed" in out and not used())
        git("checkout", "-q", "--", ".")
        cfg = repo / "config/thresholds.yaml"
        keep = cfg.read_bytes()
        git("checkout", "-q", "--detach", frozen)
        (rig / "APPROVAL_22.md").write_text(line); (rig / "extra.md").write_text("x\n")
        git("add", "-A"); git("commit", "-qm", "approve plus"); plus = git("rev-parse", "HEAD")
        rc, out = cli("--real", "--approval-commit", plus)
        check("e2e: --real refuses an approval commit that adds more than the approval file",
              rc == 2 and "must add only" in out and not used())
        git("checkout", "-q", "--detach", frozen)
        (rig / "notes.md").write_text("x\n"); git("add", "-A"); git("commit", "-qm", "between")
        (rig / "APPROVAL_22.md").write_text(line); git("add", "-A"); git("commit", "-qm", "approve late")
        late = git("rev-parse", "HEAD")
        rc, out = cli("--real", "--approval-commit", late)
        check("e2e: --real refuses an approval commit whose parent is not the freeze commit",
              rc == 2 and "single parent" in out and not used())
        git("checkout", "-q", "--detach", ok_c)
        check("e2e: back on the approval commit", cfg.read_bytes() == keep)
        snaps = data / "replay_13/snapshots.json"
        keep_snaps = snaps.read_bytes()
        snaps.write_text("[]")
        rc, out = cli("--real", "--approval-commit", ok_c)
        check("e2e: --real refuses a changed off-repo input", rc == 2 and "P22_INPUT_CHANGED" in out and not used())
        arc = sorted((data / "replay_22/archives").rglob("*.zip"))[3]
        good = arc.read_bytes()
        arc.write_bytes(good[:-1] + bytes([good[-1] ^ 1]))
        snaps.write_bytes(keep_snaps)
        rc, out = cli("--real", "--approval-commit", ok_c)
        check("e2e: --real refuses a changed archive before the lock", rc == 2 and "P22_ARCHIVE_CHANGED" in out and not used())
        arc.write_bytes(good)
        r = subprocess.run([sys.executable, str(rig / "score_22.py"), "--real", "--approval-commit", ok_c],
                           capture_output=True, text=True, env=env, cwd=tmp)
        res = json.loads((run / SC.RESULT).read_text()) if (run / SC.RESULT).exists() else {}
        check("e2e: --real scores once on the approval commit", r.returncode == 0 and "judge" in res.get("judged", {})
              and res.get("approval_commit") == ok_c and (run / SC.LOCK).stat().st_mode & 0o777 == 0o444)
        check("e2e: --real prints only the result path, no mark or figure",
              r.stdout == f"written {run / SC.RESULT}\n" and r.stderr == "")
        jd, sh = res.get("judged", {}), res.get("source_months_shown_only", {})
        check("e2e: the judged window has planted trades, a fill and a close-under-level exit",
              jd.get("trades", 0) >= 1 and jd.get("exit_reasons", {}).get("close_under_level", 0) >= 1
              and jd.get("rule_a", {}).get("12", {}).get("final", 1.) != 1.)
        check("e2e: the shown months have a planted trade with a stall exit",
              sh.get("trades", 0) >= 1 and sh.get("exit_reasons", {}).get("stall", 0) >= 1)
        tw = jd.get("twins", {})
        check("e2e: twins are drawn and placed", tw.get("n") == 10 and tw.get("median") != 1.
              and tw.get("counts", {}).get("twin_entries_not_placed", 0) < 10)
        check("e2e: rule C trips once in the judged window and the shown lines are present",
              jd.get("btc_switch_off_wakes", 0) >= 1 and all(
                  k in jd and k in sh for k in ("rule_a_with_c", "rule_a_short_exit", "btc_held", "without_best")))
        # Hand oracle from the final auditor, worked without book(): exact figures for the planted fixture.
        r12, h12 = jd.get("rule_a", {}).get("12", {}), jd.get("hold", {}).get("12", {})
        near = lambda a, b: a is not None and abs(a - b) < 1e-9
        check("e2e: the planted judged figures match the hand oracle",
              near(r12.get("final"), 0.9894120783059326) and near(r12.get("sharpe"), -1.9752176985822807)
              and near(r12.get("max_drawdown"), 0.013416286644950981) and near(h12.get("final"), 0.9942775336263151)
              and near(tw.get("cut"), 0.9992003198720512)
              and jd.get("judge", {}).get("tests") == {k: k == "drawdown" for k in ("beats_hold", "sharpe", "drawdown", "twins", "years")}
              and "judge" not in sh and "twins" not in sh)
        sealed = ((run / SC.LOCK).read_bytes(), (run / SC.RESULT).read_bytes())
        rc, out = cli("--real", "--approval-commit", ok_c)
        check("e2e: a second --real is refused and both sealed files keep their bytes", rc == 2 and "P22_ALREADY_USED" in out
              and ((run / SC.LOCK).read_bytes(), (run / SC.RESULT).read_bytes()) == sealed)
        rc, out = cli("--validate-inputs", "--approval-commit", ok_c)
        check("e2e: --validate-inputs still runs after the run, with no new file", rc == 0 and sorted(
            x.name for x in run.iterdir()) == sorted(["archives", "manifest_22.json", SC.LOCK, SC.RESULT]))


def refusal_cli_tests():
    """Each input check through --real with every pin correct: a fresh fixture is changed before it is pinned
    and committed, and --real must refuse with the named code before it takes the lock."""
    K = "data/spot/monthly/klines/AAAUSDT/1h/AAAUSDT-1h-2020-01.zip"
    KU = "data/spot/monthly/klines/BBBUSDT/1h/BBBUSDT-1h-2020-03.zip"

    def rows(f):
        return lambda stage, ctx: f(ctx) if stage == "rows" else None

    def man(f):
        return lambda stage, ctx: f(ctx) if stage == "man" else None

    def setr(key, i, j, v):
        def f(ctx):
            ctx["arch"][key]["rows"][i][j] = v(ctx["arch"][key]["rows"][i][j])
        return f

    def drop_pair(pair, month=None):
        def f(ctx):
            for k in [k for k in ctx["arch"] if f"/{pair}/" in k and (month is None or month in k)]:
                del ctx["arch"][k]
        return f

    def dup(ctx):
        r = ctx["arch"][K]["rows"]
        r.insert(6, list(r[5]))
    cases = [
        ("a malformed number", rows(setr(K, 5, 4, lambda v: "x")), "P22_BAD_ROW"),
        ("an open time 1 ms off the hour", rows(setr(K, 5, 0, lambda v: str(int(v) + 1))), "P22_OFF_GRID"),
        ("an open time 1 us off the hour", rows(setr(KU, 5, 0, lambda v: str(int(v) + 1))), "P22_OFF_GRID"),
        ("a duplicate hour", rows(dup), "P22_BAD_OR_DUPLICATE_BAR"),
        ("a high under the close", rows(setr(K, 5, 2, lambda v: "50.0")), "P22_BAD_OR_DUPLICATE_BAR"),
        ("a negative volume", rows(setr(K, 5, 7, lambda v: "-1.0")), "P22_BAD_OR_DUPLICATE_BAR"),
        ("a row count that differs", man(lambda ctx: ctx["man"]["archives"][K].update(n=ctx["man"]["archives"][K]["n"] + 1)),
         "P22_ROWS_DIFFER"),
        ("a row before the manifest's first hour",
         man(lambda ctx: ctx["man"]["archives"][K].update(first=ctx["man"]["archives"][K]["first"] + 3600)), "P22_OUT_OF_BOUNDS"),
        ("a last hour that differs",
         man(lambda ctx: ctx["man"]["archives"][K].update(last=ctx["man"]["archives"][K]["last"] + 3600)), "P22_ROWS_DIFFER"),
        ("a missing archive", rows(lambda ctx: ctx["skip"].add(K)), "P22_ARCHIVE_MISSING"),
        ("a listed coin with no Binance pair", man(lambda ctx: ctx["man"].update(no_binance_pair=["ZZZ"])), "P22_NO_BINANCE_PAIR"),
        ("no BTCUSDT", rows(drop_pair("BTCUSDT")), "P22_NO_BTCUSDT"),
        ("BTCUSDT too short", rows(drop_pair("BTCUSDT", "2019-11")), "P22_BTCUSDT_SHORT"),
        ("an identity cutoff before the shown end", rows(lambda ctx: ctx["ident"].update(as_of_cutoff_utc="2020-03-15")),
         "P22_IDENTITY_CUTOFF"),
        ("wakes without a rank page", rows(lambda ctx: ctx.update(pages=[x for x in ctx["pages"] if x["date"] != "2020-02-01"])),
         "P22_LIST_HOLE"),
        ("a confirmed pair without a tape", rows(drop_pair("AAAUSDT")), "P22_LISTED_PAIR_WITHOUT_BARS"),
    ]
    for name, mut, code in cases:
        with tempfile.TemporaryDirectory() as tmp:
            SC, rig, data, ok_c, cli = e2e_setup(tmp, mut)
            run = data / "replay_22"
            rc, out = cli("--real", "--approval-commit", ok_c)
            check(f"e2e refusal before the lock: {name}", rc == 2 and code in out and not os.path.lexists(run / SC.LOCK)
                  and not os.path.lexists(run / SC.RESULT))


def sharpe_tests():
    marks = [S + 24 * k for k in range(4)]
    s = G.summary(G.Result(marks, [1., 1.8, 3.24, 5.832000000000001], [], {}), P)
    check("constant nonzero daily returns give Sharpe 0, so the Sharpe mark fails",
          s["sharpe"] == 0. and not G.judge(s, s, [0.], P)["tests"]["sharpe"])
    s2 = G.summary(G.Result(marks[:2], [1., 1.1], [], {}), P)
    check("a single return gives Sharpe 0", s2["sharpe"] == 0.)


TRAP = """import sys
sys.path.insert(0, sys.argv[1])
import common_22 as G
def trap(*a, **k):
    raise SystemExit("RETURN_TRAP_HIT")
for name in ("book", "summary", "rule_a", "membership", "twins", "judge", "without_best", "BtcSwitch"):
    setattr(G, name, trap)
import score_22
sys.argv = ["score_22.py"] + sys.argv[2:]
score_22.main()
"""
FAIL_AFTER_LOCK = """import sys
sys.path.insert(0, sys.argv[1])
import score_22
def boom(*a, **k):
    raise RuntimeError("SECRET_FIELD_VALUE")
score_22.run_window = boom
sys.argv = ["score_22.py"] + sys.argv[2:]
score_22.main()
"""


def e2e_setup(tmp, mutate=None):
    SC, repo, rig, data = e2e_fixture(tmp, mutate)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PLAN22_", "P22_"))}
    env.update(PYTHONDONTWRITEBYTECODE="1", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")

    def git(*a):
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True, env=env).stdout.strip()
    git("init", "-q"); git("add", "-A"); git("commit", "-qm", "freeze"); frozen = git("rev-parse", "HEAD")
    (rig / "APPROVAL_22.md").write_text(f"Approved by the lead: plan 22, one scored run, freeze commit {frozen}.\n")
    git("add", "-A"); git("commit", "-qm", "approve"); ok_c = git("rev-parse", "HEAD")

    def cli(*a, script=None):
        cmd = [sys.executable, "-c", script, str(rig), *a] if script else [sys.executable, str(rig / "score_22.py"), *a]
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=tmp)
        return r.returncode, r.stdout + r.stderr
    return SC, rig, data, ok_c, cli


def e2e_more_tests():
    import gzip
    with tempfile.TemporaryDirectory() as tmp:
        SC, rig, data, ok_c, cli = e2e_setup(tmp)
        run = data / "replay_22"
        used = lambda: os.path.lexists(run / SC.LOCK) or os.path.lexists(run / SC.RESULT)
        plain = {n: (data / n).read_bytes() for n in SC.DATA_PINS}
        for n, b in plain.items():
            (data / (n + ".gz")).write_bytes(gzip.compress(b, 9)); (data / n).unlink()
        rc, out = cli("--validate-inputs", "--approval-commit", ok_c)
        check("e2e: all three inputs as gzip only pass on their uncompressed pins", rc == 0 and '"validated": true' in out)
        for n, b in plain.items():
            (data / (n + ".gz")).write_bytes(gzip.compress(b, 1, mtime=12345))
        rc, out = cli("--validate-inputs", "--approval-commit", ok_c)
        check("e2e: a different compression of the same bytes still passes", rc == 0 and not used())
        n0 = SC.DATA_PINS[1]
        (data / (n0 + ".gz")).write_bytes(gzip.compress(plain[n0] + b" "))
        rc, out = cli("--validate-inputs", "--approval-commit", ok_c)
        check("e2e: a gzip copy whose uncompressed bytes differ is refused", rc == 2 and "P22_INPUT_CHANGED" in out)
        (data / (n0 + ".gz")).write_bytes(gzip.compress(plain[n0]))
        (data / (n0 + ".gz")).rename(data / (n0 + ".away"))
        rc1, out1 = cli("--validate-inputs")
        rc2, out2 = cli("--real", "--approval-commit", ok_c)
        check("e2e: a pinned input missing in both forms is refused in both modes before the lock",
              rc1 == 2 and rc2 == 2 and "P22_INPUT_MISSING" in out1 and "P22_INPUT_MISSING" in out2 and not used())
        (data / (n0 + ".away")).rename(data / (n0 + ".gz"))
        rc, out = cli("--validate-inputs", script=TRAP)
        check("e2e: validation without approval computes no return (trap not hit)",
              rc == 0 and '"gate_checked": false' in out and "RETURN_TRAP_HIT" not in out and not used())
        rc, out = cli("--validate-inputs", "--approval-commit", ok_c, script=TRAP)
        check("e2e: validation with approval computes no return (trap not hit)",
              rc == 0 and '"gate_checked": true' in out and "RETURN_TRAP_HIT" not in out and not used())
        rc, out = cli("--real", "--approval-commit", ok_c, script=FAIL_AFTER_LOCK)
        lock = run / SC.LOCK
        first = lock.read_bytes() if lock.exists() else b""
        check("e2e: a failure after the lock leaves the lock, no result, and no echoed value",
              rc != 0 and first and not os.path.lexists(run / SC.RESULT) and "SECRET" not in out and "RuntimeError" in out)
        rc, out = cli("--real", "--approval-commit", ok_c)
        check("e2e: after a failed run a repeat is refused and the lock bytes do not change",
              rc == 2 and "P22_ALREADY_USED" in out and lock.read_bytes() == first and not os.path.lexists(run / SC.RESULT))


def plan_figures_tests():
    """The plan's power paragraph must be exactly what calibrate_22.py writes from the two output files."""
    import calibrate_22 as K
    plan = next((x for x in (HERE / "PREREG_22_fable_rule_a.md", HERE / "PREREG_22_fable_rule_a_DRAFT.md") if x.exists()), None)
    if plan is None or not (HERE / "calibration_22.json").exists() or not (HERE / "calibration_timing_22.json").exists():
        check("plan figures: plan and calibration files present", False)
        return
    text = plan.read_text()
    a, b = text.index(K.BEGIN) + len(K.BEGIN), text.index(K.END)
    want = "\n" + K.limits_text(json.loads((HERE / "calibration_22.json").read_text()),
                                json.loads((HERE / "calibration_timing_22.json").read_text())) + "\n"
    check("plan figures match the calibration files", text[a:b] == want)


for f in (lookahead_tests, sig_tests, exit_tests, rank_tests, book_tests, metric_tests, twin_tests, switch_tests, universe_tests, lock_tests,
          order_tests, gate_tests, validate_tests, e2e_tests, e2e_more_tests, refusal_cli_tests, sharpe_tests, plan_figures_tests):
    f()
print(f"{'FAILED ' + str(len(FAILS)) if FAILS else 'all passed'}")
sys.exit(1 if FAILS else 0)
