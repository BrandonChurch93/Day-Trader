"""Plan 65 scorer: stock-bond rebalancing spread (Harvey, Mazzoleni and Melone, NBER w33554, section 4).

Modes
  --synthetic          build seeded synthetic bars in memory, run the full rule, check invariants. No real file is read.
  --validate-inputs    open and check the real inputs. Prints judged-session and missing-bar counts and the
                       inputs digest. Computes no return and no signal. Writes nothing.
  --go --approval-commit <c>
                       the single judged run. Runs the approval gate, checks the inputs digest named in the
                       approval line, takes the one-shot lock, scores, writes results_65.json.
No PLAN65_ or P65_ environment variable is allowed. Settings come only from config/thresholds.yaml#replay_65_plan.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = REPO / "config/thresholds.yaml"
KEY = "replay_65_plan"
WS = Path("/home/user/workspace")
INPUTS = WS / "rig/data/plan65_inputs"
RUN = WS / "rig/data/replay_65"
RESULT, LOCK = "results_65.json", "score_65.lock"
PLAN_NAME = "PREREG_65_stock_bond_rebalance_spread.md"
PINNED_NAMES = (PLAN_NAME, "score_65.py", "test_65.py", "calendar_65.json", "power_65.py", "POWER_65.json")
CONFIG_PIN = "thresholds.yaml#replay_65_plan"
APPROVAL = "research_rig/APPROVAL_65.md"
PINNED = "research_rig/PINNED_65.json"
APPROVAL_LINE = re.compile(r"Approved by the lead: plan 65 ledger 208, one scored run, freeze commit ([0-9a-f]{40}), "
                           r"inputs SHA-256 ([0-9a-f]{64})\.\n")    # the whole file, exactly this one line
LEDGER_ROW = re.compile(rb"(?m)^\| 208 \|[^\n]+PREREG_65_stock_bond_rebalance_spread")
GIT = shutil.which("git") or "/usr/bin/git"
INPUT_NAMES = ("SPY_15m.json", "IEF_15m.json", "SPY_1d.json", "IEF_1d.json", "TLT_1d.json", "SH_1d.json", "actions.json")
DAILY = ("SPY", "IEF", "TLT", "SH")
INTRA = ("SPY", "IEF")


class Refused(Exception):
    """A fixed-code refusal. The message names a check and a path, key or count, never a price."""


def digest(b):
    return hashlib.sha256(b).hexdigest()


def no_env():
    bad = sorted(k for k in os.environ if k.startswith(("PLAN65_", "P65_")))
    if bad:
        raise Refused("P65_ENV " + ",".join(bad))


# ---------- config and calendar ----------

def load_config(raw):
    v = yaml.safe_load(raw)[KEY]["value"]
    need = {"target", "delta_min", "delta_max", "delta_step", "threshold_scale", "week4_sessions", "reversal_lag",
            "burn_in_sessions", "first_session", "last_session", "cost_bps", "cost_cent", "borrow_annual",
            "signal_bar_start_before_close_min", "marks", "sh_leg_usd", "stress_exclude_months", "post_paper_from"}
    if set(v) != need:
        raise Refused("P65_CONFIG keys")
    return v


def config_block_sha256(raw):
    return digest(json.dumps(yaml.safe_load(raw)[KEY]["value"], sort_keys=True, default=str).encode())


def deltas(cfg):
    n = int(round((cfg["delta_max"] - cfg["delta_min"]) / cfg["delta_step"])) + 1
    return np.array([round(cfg["delta_min"] + i * cfg["delta_step"], 10) for i in range(n)])


class Sessions(list):
    """The scored sessions, first_session to last_session. .tail holds the calendar sessions after last_session,
    used only to place month ends (the sample end is not a month end)."""
    tail = ()


def load_calendar(raw, cfg):
    allx = json.loads(raw)["sessions"]
    prev = ""
    for x in allx:
        if not (isinstance(x, list) and len(x) == 3 and all(isinstance(v, str) for v in x)):
            raise Refused("P65_CALENDAR row")
        try:
            d0, o, c = dt.date.fromisoformat(x[0]), utc(x[1]), utc(x[2])
        except ValueError as e:
            raise Refused("P65_CALENDAR row") from e
        if x[0] <= prev or o >= c or d0.weekday() > 4 or o.date() != d0 or o.strftime("%H:%M") not in ("13:30", "14:30"):
            raise Refused("P65_CALENDAR row " + x[0])
        prev = x[0]
    s = Sessions(x for x in allx if cfg["first_session"] <= x[0] <= cfg["last_session"])
    if not s or s[0][0] != cfg["first_session"] or s[-1][0] != cfg["last_session"]:
        raise Refused("P65_CALENDAR span")
    s.tail = [x for x in allx if x[0] > cfg["last_session"]]
    if not any(x[0][:7] > cfg["last_session"][:7] for x in s.tail):
        raise Refused("P65_CALENDAR no session after the last month end")
    return s


def utc(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def session_flags(sessions, cfg):
    """last-of-month, in-week4 (last k sessions of the month) and first-of-month flags, from the calendar only.
    Sessions in sessions.tail (after the sample end) are counted so that the sample end is not taken as a month end;
    the flags returned cover only the scored sessions."""
    n0 = len(sessions)
    dates = [x[0] for x in sessions] + [x[0] for x in getattr(sessions, "tail", ())]
    ym = [d[:7] for d in dates]
    n = len(dates)
    last = np.array([i == n - 1 or ym[i + 1] != ym[i] for i in range(n)])
    first = np.array([i == 0 or ym[i - 1] != ym[i] for i in range(n)])
    week4 = np.zeros(n, bool)
    k = cfg["week4_sessions"]
    for i in range(n):
        j = i
        left = 0
        while j < n - 1 and ym[j + 1] == ym[i]:
            j += 1
            left += 1
        week4[i] = left < k            # this session is among the last k of its month
    return last[:n0], week4[:n0], first[:n0]


def signal_bar_start(session, cfg):
    close = utc(session[2])
    return (close - dt.timedelta(minutes=cfg["signal_bar_start_before_close_min"])).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- inputs ----------

def check_dir(path):
    st = os.lstat(path)
    if not stat.S_ISDIR(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o700 or st.st_uid != os.getuid():
        raise Refused("P65_INPUTS directory mode " + str(path))
    names = sorted(os.listdir(path))
    if names != sorted(INPUT_NAMES):
        raise Refused("P65_INPUTS names")
    for n in names:
        st = os.lstat(path / n)
        if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o600 or st.st_uid != os.getuid():
            raise Refused("P65_INPUTS file mode " + n)


def read_inputs(path):
    check_dir(path)
    return {n: (path / n).read_bytes() for n in INPUT_NAMES}


def inputs_digest(blobs):
    return digest(json.dumps({n: digest(blobs[n]) for n in sorted(blobs)}, sort_keys=True).encode())


def _no_dupes(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise Refused("P65_FORMAT duplicate JSON key")
    return dict(pairs)


def jload(raw, name):
    try:
        return json.loads(raw, object_pairs_hook=_no_dupes)
    except ValueError as e:
        raise Refused("P65_FORMAT " + name) from e


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _bars(raw, name):
    rows = jload(raw, name)
    if not isinstance(rows, list):
        raise Refused("P65_FORMAT " + name)
    out = {}
    for r in rows:
        if not isinstance(r, dict) or set(r) != {"t", "o", "h", "l", "c", "v"}:
            raise Refused("P65_FORMAT fields " + name)
        if not isinstance(r["t"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:(00|15|30|45):00Z", r["t"]):
            raise Refused("P65_FORMAT time " + name)
        try:
            utc(r["t"])
        except ValueError as e:
            raise Refused("P65_FORMAT time " + name) from e
        if not all(_num(r[k]) and r[k] > 0 for k in "ohlc") or not (_num(r["v"]) and r["v"] >= 0):
            raise Refused("P65_FORMAT value " + name)
        if not r["l"] <= min(r["o"], r["c"]) <= max(r["o"], r["c"]) <= r["h"]:
            raise Refused("P65_FORMAT range " + name)
        if r["t"] in out:
            raise Refused("P65_FORMAT duplicate " + name)
        out[r["t"]] = float(r["c"])
    return out


def parse_daily(raw, name, sessions):
    """Daily stamp must be midnight New York for a calendar session: 05:00Z when the session opens at 14:30Z
    (standard time), 04:00Z when it opens at 13:30Z (daylight time). One bar per session; no bar off the calendar."""
    want = {}
    for x in list(sessions) + list(getattr(sessions, "tail", ())):
        want[x[0]] = x[0] + ("T05:00:00Z" if x[1][11:16] == "14:30" else "T04:00:00Z")
    out = {}
    for t, c in _bars(raw, name).items():
        d = t[:10]
        if d not in want:
            if sessions[0][0] <= d <= sessions[-1][0]:
                raise Refused("P65_FORMAT daily bar off the calendar " + name)
            continue
        if t != want[d]:
            raise Refused("P65_FORMAT daily stamp " + name)
        if d in out:
            raise Refused("P65_FORMAT duplicate " + name)
        out[d] = c
    return out


def parse_actions(raw, sessions):
    """One row per symbol, type and ex-date (custody merges same-day cash). An ex-date inside the span must be a
    calendar session."""
    rows = jload(raw, "actions.json")
    on_cal = {x[0] for x in sessions}
    if not isinstance(rows, list):
        raise Refused("P65_FORMAT actions.json")
    acts = {s: {} for s in DAILY}
    seen = set()
    for r in rows:
        if not isinstance(r, dict) or r.get("symbol") not in DAILY or r.get("type") not in ("cash", "split"):
            raise Refused("P65_FORMAT actions row")
        key = "amount" if r["type"] == "cash" else "ratio"
        if set(r) != {"symbol", "type", "ex_date", key} or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r["ex_date"])):
            raise Refused("P65_FORMAT actions row")
        try:
            dt.date.fromisoformat(r["ex_date"])
        except ValueError as e:
            raise Refused("P65_FORMAT actions date") from e
        x = r[key]
        if not _num(x) or x <= 0 or (r["type"] == "split" and x == 1):
            raise Refused("P65_FORMAT actions value")
        if sessions[0][0] <= r["ex_date"] <= sessions[-1][0] and r["ex_date"] not in on_cal:
            raise Refused("P65_FORMAT action date off the calendar")
        k3 = (r["symbol"], r["type"], r["ex_date"])
        if k3 in seen:
            raise Refused("P65_FORMAT duplicate action")
        seen.add(k3)
        cash, ratio = acts[r["symbol"]].get(r["ex_date"], (0.0, 1.0))
        if r["type"] == "cash":
            cash += float(x)
        else:
            if ratio != 1.0:
                raise Refused("P65_FORMAT two splits one day")
            ratio = float(x)
        acts[r["symbol"]][r["ex_date"]] = (cash, ratio)
    return acts


def parse(blobs, sessions, cfg):
    daily = {s: parse_daily(blobs[s + "_1d.json"], s + "_1d.json", sessions) for s in DAILY}
    intra = {s: _bars(blobs[s + "_15m.json"], s + "_15m.json") for s in INTRA}
    acts = parse_actions(blobs["actions.json"], sessions)
    return daily, intra, acts


def coverage(daily, intra, sessions, cfg):
    """Counts only. No price is compared with another."""
    dates = [x[0] for x in sessions]
    miss_daily = {s: sum(d not in daily[s] for d in dates) for s in DAILY}
    starts = [signal_bar_start(x, cfg) for x in sessions]
    b = cfg["burn_in_sessions"]
    judged_idx = range(b, len(sessions) - 1)
    miss_intra = {s: sum(starts[i] not in intra[s] for i in judged_idx) for s in INTRA}
    no_bar = sum(any(starts[i] not in intra[s] for s in INTRA) for i in judged_idx)
    return {"sessions": len(sessions), "judged_candidates": len(judged_idx), "judged_sessions": len(judged_idx) - no_bar,
            "missing_daily": miss_daily, "missing_signal_bar": miss_intra, "sessions_without_signal_bar": no_bar}


# ---------- rule ----------

def total_returns(closes, acts, dates):
    """R[i] = ratio_i * (C_i + D_i) / C_{i-1} - 1. Cash is per post-split share. R[0] is nan."""
    c = np.array([closes[d] for d in dates])
    r = np.full(len(dates), np.nan)
    for i in range(1, len(dates)):
        cash, ratio = acts.get(dates[i], (0.0, 1.0))
        r[i] = ratio * (c[i] + cash) / c[i - 1] - 1.0
    return c, r


def partial_returns(intra, closes, acts, sessions, cfg):
    """Return from close i-1 to the close of the signal bar on day i; nan where the bar is missing."""
    dates = [x[0] for x in sessions]
    r = np.full(len(dates), np.nan)
    for i in range(1, len(dates)):
        p = intra.get(signal_bar_start(sessions[i], cfg))
        if p is None:
            continue
        cash, ratio = acts.get(dates[i], (0.0, 1.0))
        r[i] = ratio * (p + cash) / closes[dates[i - 1]] - 1.0
    return r


def drift(w, rs, rb):
    a = w * (1 + rs)
    return a / (a + (1 - w) * (1 + rb))


def signals(rs, rb, ps, pb, last, week4, first, cfg, alt_reversal=False):
    """Paper section 4 weight. History uses full closes; the day-i signal uses close i-1 state plus the
    signal-bar return on day i. Returns w (judged clock), wlag (shown, signal through close i-1 held
    from close i), thr_half and cal_half (the two halves of w), all indexed by session of the close
    at which the position is set."""
    n = len(rs)
    tgt = cfg["target"]
    ds = deltas(cfg)
    post_t = np.full(len(ds), tgt)            # each Threshold portfolio, after its reset decision, at close 0
    post_c = tgt
    thr_full = np.full(n, np.nan)
    cal_full = np.full(n, np.nan)
    thr_part = np.full(n, np.nan)
    cal_part = np.full(n, np.nan)
    for i in range(1, n):
        if not np.isnan(ps[i]) and not np.isnan(pb[i]):
            thr_part[i] = np.mean(drift(post_t, ps[i], pb[i]) - tgt)
            cal_part[i] = drift(post_c, ps[i], pb[i]) - tgt
        dt_ = drift(post_t, rs[i], rb[i])
        thr_full[i] = np.mean(dt_ - tgt)
        post_t = np.where(np.abs(dt_ - tgt) >= ds - 1e-12, tgt, dt_)   # two-sided, reset at the breach close
        dc = drift(post_c, rs[i], rb[i])
        cal_full[i] = dc - tgt
        post_c = tgt if last[i] else dc

    lag = cfg["reversal_lag"]
    scale = cfg["threshold_scale"]

    def mod_cal(i, cal_now):
        if week4[i]:
            return float(np.sign(-cal_now))
        if first[i] and alt_reversal:
            j = i - 1
            while j - 1 >= 1 and week4[j - 1] and not last[j - 1]:
                j -= 1
            return float(np.sign(cal_full[j])) if j >= 1 and week4[j] else 0.0
        if first[i] and i - lag >= 1:
            return float(np.sign(cal_full[i - lag]))
        return 0.0

    w = np.full(n, np.nan)
    thr_half = np.full(n, np.nan)
    cal_half = np.full(n, np.nan)
    wfull = np.full(n, np.nan)
    for i in range(1, n):
        wfull[i] = 0.5 * (-thr_full[i] / scale + mod_cal(i, cal_full[i]))
        if not np.isnan(thr_part[i]):
            thr_half[i] = 0.5 * (-thr_part[i] / scale)
            cal_half[i] = 0.5 * mod_cal(i, cal_part[i])
            w[i] = thr_half[i] + cal_half[i]
    wlag = np.full(n, np.nan)
    wlag[2:] = wfull[1:-1]
    return w, wlag, thr_half, cal_half


def leg_cost(price, cfg):
    return np.maximum(cfg["cost_bps"] * 1e-4, cfg["cost_cent"] / price)


def economics(w, rs, rb, cs, cb, dates, b_short_s, b_short_b, cfg, idx, round_trip=False):
    """Net return per unit capital of holding w on the stock leg and -w on the bond leg from close i to close i+1,
    for each i in idx. A nan weight means no signal bar that day: the position is flat for that session and the
    session is not judged; the cost of going flat and of re-entering is charged to the next judged session (or to
    the last judged one if none follows). Cost is on the change in weight at close i, both legs, and the final
    position is closed at the last close. Borrow on the short leg by calendar days. With round_trip, each judged
    session instead pays a full entry and exit at close i and close i+1."""
    net, gross, keep = [], [], []
    prev, pending = 0.0, 0.0
    cost_s, cost_b = leg_cost(cs, cfg), leg_cost(cb, cfg)
    for k, i in enumerate(idx):
        flat = bool(np.isnan(w[i]))
        wi = 0.0 if flat else float(w[i])
        if round_trip:
            c = 0.0 if flat else abs(wi) * (cost_s[i] + cost_b[i] + cost_s[i + 1] + cost_b[i + 1])
        else:
            c = abs(wi - prev) * (cost_s[i] + cost_b[i])
            if k == len(idx) - 1:
                c += abs(wi) * (cost_s[i + 1] + cost_b[i + 1])
        prev = wi
        if flat:
            pending += c
            continue
        days = (dt.date.fromisoformat(dates[i + 1]) - dt.date.fromisoformat(dates[i])).days
        borrow = (wi * b_short_b if wi > 0 else -wi * b_short_s) * days / 365.0
        g = wi * (rs[i + 1] - rb[i + 1])
        gross.append(g)
        net.append(g - c - borrow - pending)
        pending = 0.0
        keep.append(i)
    if pending and net:
        net[-1] -= pending
    return np.array(net), np.array(gross), keep


def cluster_t(x, groups):
    n = len(x)
    if n < 2:
        return float("nan")
    m = x.mean()
    u, inv = np.unique(groups, return_inverse=True)
    G = len(u)
    if G < 2:
        return float("nan")
    g = np.bincount(inv, weights=x - m)
    se = math.sqrt(G / (G - 1) * float(np.sum(g ** 2))) / n
    if not math.isfinite(se) or se <= 1e-15 * max(1.0, abs(m)) or np.ptp(x) == 0:
        return float("nan")                    # constant or zero-variance series: t is undefined
    return float(m / se)


def week_key(d):
    y, w, _ = dt.date.fromisoformat(d).isocalendar()
    return y * 100 + w


def marks(x, exit_dates, cfg):
    M = cfg["marks"]
    n = len(x)
    if n == 0:
        ok = dict.fromkeys(("sessions", "money", "evidence", "trim", "years"), False)
        return {"n": 0, "mean": None, "t_week": None, "trim_mean": None, "trim_dropped": 0, "years_positive": 0,
                "by_year": {str(y): None for y in M["years"]}, "marks": ok, "marks_met": 0, "pass": False}
    m = float(x.mean())
    t = cluster_t(x, np.array([week_key(d) for d in exit_dates]))
    k = int(math.ceil(M["trim_share"] * n))
    trim = float(np.sort(x)[:-k].mean()) if n > k else float("nan")
    years = np.array([int(d[:4]) for d in exit_dates])
    by_year = {y: (float(x[years == y].mean()) if (years == y).any() else None) for y in M["years"]}
    ypos = sum(v is not None and v > 0 for v in by_year.values())
    ok = {"sessions": n >= M["min_sessions"], "money": m > 0, "evidence": (not math.isnan(t)) and t >= M["t_min"],
          "trim": (not math.isnan(trim)) and trim > 0, "years": ypos >= M["years_positive_min"]}
    return {"n": n, "mean": m, "t_week": t, "trim_mean": trim, "trim_dropped": k, "years_positive": ypos,
            "by_year": {str(y): v for y, v in by_year.items()}, "marks": ok, "marks_met": sum(ok.values()),
            "pass": all(ok.values())}


def plain_stats(x):
    if len(x) == 0:
        return {"n": 0}
    sd = float(x.std(ddof=1)) if len(x) > 1 else float("nan")
    return {"n": int(len(x)), "mean": float(x.mean()), "sd": sd,
            "sharpe_yearly": float(x.mean() / sd * math.sqrt(252)) if sd and sd > 0 else None}


def sh_version(w, daily, acts, dates, idx, cfg):
    """Shown only, cash account. At each close i in idx, hold whole shares of IEF and SH, each worth at most the leg
    budget, when w[i] < 0, else nothing. Cost per side on the change in shares, the greater of the bp rate on value
    and the cent per share. A split or a missing bar on either side of a session sets the count to zero for that
    session at no cost. Mean P&L per session over all sessions in idx, per USD 1,000."""
    out, prev, held = [], {"IEF": 0, "SH": 0}, 0
    for i in idx:
        ok = all(dates[j] in daily[s] for s in ("IEF", "SH") for j in (i, i + 1)) and \
            all(acts[s].get(dates[i + 1], (0.0, 1.0))[1] == 1.0 for s in ("IEF", "SH"))
        pnl, any_held = 0.0, False
        for s in ("IEF", "SH"):
            if not ok:
                prev[s] = 0
                continue
            c0, c1 = daily[s][dates[i]], daily[s][dates[i + 1]]
            n = int(cfg["sh_leg_usd"] // c0) if (not np.isnan(w[i]) and w[i] < 0) else 0
            ch = abs(n - prev[s])
            if ch:
                pnl -= max(cfg["cost_bps"] * 1e-4 * ch * c0, cfg["cost_cent"] * ch)
            pnl += n * (c1 + acts[s].get(dates[i + 1], (0.0, 1.0))[0] - c0)
            prev[s] = n
            any_held |= n > 0
        if i == idx[-1] and ok:                 # liquidate whatever is held at the last close
            for s in ("IEF", "SH"):
                if prev[s]:
                    c1 = daily[s][dates[i + 1]]
                    pnl -= max(cfg["cost_bps"] * 1e-4 * prev[s] * c1, cfg["cost_cent"] * prev[s])
        held += any_held
        out.append(pnl / (2 * cfg["sh_leg_usd"]))
    return plain_stats(np.array(out)) | {"sessions_held": int(held)}


def preflight(daily, sessions):
    """Every refusal the score can raise on the data, run before the one-shot lock."""
    dates = [x[0] for x in sessions]
    for s in ("SPY", "IEF"):
        if any(d not in daily[s] for d in dates):
            raise Refused("P65_MISSING_DAILY " + s)


def score(daily, intra, acts, sessions, cfg):
    dates = [x[0] for x in sessions]
    preflight(daily, sessions)
    last, week4, first = session_flags(sessions, cfg)
    cs, rs = total_returns(daily["SPY"], acts["SPY"], dates)
    cb, rb = total_returns(daily["IEF"], acts["IEF"], dates)
    ps = partial_returns(intra["SPY"], daily["SPY"], acts["SPY"], sessions, cfg)
    pb = partial_returns(intra["IEF"], daily["IEF"], acts["IEF"], sessions, cfg)
    w, wlag, th, ch = signals(rs, rb, ps, pb, last, week4, first, cfg)
    B = cfg["borrow_annual"]
    idx = list(range(cfg["burn_in_sessions"], len(dates) - 1))
    net, gross, keep = economics(w, rs, rb, cs, cb, dates, B["SPY"], B["IEF"], cfg, idx)
    exits = [dates[i + 1] for i in keep]
    res = {"judged": marks(net, exits, cfg), "judged_plain": plain_stats(net), "gross_plain": plain_stats(gross),
           "mean_abs_weight": float(np.nanmean(np.abs(w[idx]))), "shown_only": {}}
    sh = res["shown_only"]

    def subset(pred):
        sel = np.array([pred(d) for d in exits], bool)
        return plain_stats(net[sel]) | {"t_week": cluster_t(net[sel], np.array([week_key(d) for d, k in zip(exits, sel) if k]))}
    sh["post_paper"] = subset(lambda d: d >= cfg["post_paper_from"])
    sh["without_stress_months"] = subset(lambda d: d[:7] not in cfg["stress_exclude_months"])
    for name, ww in (("threshold_half", th), ("calendar_half", ch)):
        n2, _, k2 = economics(ww, rs, rb, cs, cb, dates, B["SPY"], B["IEF"], cfg, idx)
        sh[name] = plain_stats(n2) | {"t_week": cluster_t(n2, np.array([week_key(dates[i + 1]) for i in k2]))}
    w_alt = signals(rs, rb, ps, pb, last, week4, first, cfg, alt_reversal=True)[0]
    n6, _, k6 = economics(w_alt, rs, rb, cs, cb, dates, B["SPY"], B["IEF"], cfg, idx)
    sh["calendar_reversal_window_start"] = plain_stats(n6) | {
        "t_week": cluster_t(n6, np.array([week_key(dates[i + 1]) for i in k6]))}
    n3, _, k3 = economics(wlag, rs, rb, cs, cb, dates, B["SPY"], B["IEF"], cfg, idx)
    sh["lag_one_clock"] = plain_stats(n3) | {"t_week": cluster_t(n3, np.array([week_key(dates[i + 1]) for i in k3]))}
    n4, _, k4 = economics(w, rs, rb, cs, cb, dates, B["SPY"], B["IEF"], cfg, idx, round_trip=True)
    sh["full_daily_round_trip"] = plain_stats(n4) | {"t_week": cluster_t(n4, np.array([week_key(dates[i + 1]) for i in k4]))}
    if all(d in daily["TLT"] for d in dates):
        ct, rt = total_returns(daily["TLT"], acts["TLT"], dates)
        n5, _, k5 = economics(w, rs, rt, cs, ct, dates, B["SPY"], B["TLT"], cfg, idx)
        sh["tlt_for_ief"] = plain_stats(n5) | {"t_week": cluster_t(n5, np.array([week_key(dates[i + 1]) for i in k5]))}
    else:
        sh["tlt_for_ief"] = {"n": 0, "missing_daily": sum(d not in daily["TLT"] for d in dates)}
    sh["sh_cash_account"] = sh_version(w, daily, acts, dates, idx, cfg)
    return res


# ---------- approval gate ----------

def authorize(commit, repo=REPO, config=CONFIG):
    root = str(repo)

    def git(*a, ok=False):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        r = subprocess.run([GIT, "--no-replace-objects", "-c", "core.fsmonitor=false", "-C", root, *a],
                           capture_output=True, env=env)
        if r.returncode and not ok:
            raise Refused("P65_NOT_APPROVED git " + a[0])
        return r

    def show(c, path):
        return git("show", f"{c}:{path}").stdout
    no_env()
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        raise Refused("P65_NOT_APPROVED no approval commit given")
    rig = Path(root) / "research_rig"
    if HERE.resolve() != rig.resolve() and repo == REPO:
        raise Refused("P65_NOT_APPROVED code is not run from the repo")
    if git("rev-parse", "HEAD").stdout.decode().strip() != commit:
        raise Refused("P65_NOT_APPROVED HEAD is not the approval commit")
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise Refused("P65_NOT_APPROVED tracked files changed")
    r = git("show", f"{commit}:{APPROVAL}", ok=True)
    m = APPROVAL_LINE.fullmatch(r.stdout.decode("utf-8", "replace")) if not r.returncode else None
    if not m:
        raise Refused("P65_NOT_APPROVED " + APPROVAL)
    frozen, in_digest = m.group(1), m.group(2)
    if git("rev-list", "--parents", "-n", "1", commit).stdout.decode().split() != [commit, frozen]:
        raise Refused("P65_NOT_APPROVED the approval commit's single parent is not the freeze commit")
    if git("diff", "--name-status", "--no-renames", frozen, commit).stdout.decode().splitlines() != ["A\t" + APPROVAL]:
        raise Refused("P65_NOT_APPROVED the approval commit must add only " + APPROVAL)
    pins = json.loads(show(commit, PINNED))
    if set(pins) != {*PINNED_NAMES, CONFIG_PIN}:
        raise Refused("P65_NOT_APPROVED pin names")
    checked = {}
    for name in PINNED_NAMES:
        path = "research_rig/" + name
        disk = (rig / name).read_bytes()             # read once; the calendar bytes checked here are the ones scored
        h = digest(show(commit, path))
        if h != pins[name] or h != digest(disk):
            raise Refused("P65_NOT_APPROVED pin " + name)
        checked[name] = disk
    disk_cfg = Path(config).read_bytes()
    h = config_block_sha256(show(commit, "config/thresholds.yaml"))
    if h != pins[CONFIG_PIN] or h != config_block_sha256(disk_cfg):
        raise Refused("P65_NOT_APPROVED pin " + CONFIG_PIN)
    plan = show(commit, "research_rig/" + PLAN_NAME)
    status = re.findall(rb"(?m)^Status:[^\n]*", plan)
    if len(status) != 1 or not status[0].startswith(b"Status: FROZEN"):
        raise Refused("P65_NOT_APPROVED plan not frozen")
    if not LEDGER_ROW.search(show(commit, "research_rig/TRIAL_LEDGER.md")):
        raise Refused("P65_NOT_APPROVED ledger row 208")
    return in_digest, disk_cfg, checked["calendar_65.json"]


def lock_file(path, job):
    path = Path(path)
    for x in (path, path.with_name(RESULT)):
        if os.path.lexists(x):
            raise Refused(f"P65_ALREADY_USED {x}")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as e:
        raise Refused(f"P65_ALREADY_USED {path}") from e
    with os.fdopen(fd, "w") as f:
        json.dump(job, f, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    dfd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def write_result(path, res):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(fd, "w") as f:
        json.dump(res, f, sort_keys=True, indent=1, default=float)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


# ---------- modes ----------

def validate(inputs=INPUTS, config=CONFIG, calendar=HERE / "calendar_65.json"):
    no_env()
    cfg = load_config(Path(config).read_bytes())
    sessions = load_calendar(Path(calendar).read_bytes(), cfg)
    blobs = read_inputs(Path(inputs))
    daily, intra, _ = parse(blobs, sessions, cfg)
    cov = coverage(daily, intra, sessions, cfg)
    cov["inputs_sha256"] = inputs_digest(blobs)
    cov["min_sessions_mark"] = cfg["marks"]["min_sessions"]
    return cov


def go(commit, inputs=INPUTS, run=RUN, repo=REPO, config=CONFIG):
    in_digest, raw_cfg, raw_cal = authorize(commit, repo, config)
    cfg = load_config(raw_cfg)
    sessions = load_calendar(raw_cal, cfg)
    blobs = read_inputs(Path(inputs))
    if inputs_digest(blobs) != in_digest:
        raise Refused("P65_INPUTS digest differs from the approval line")
    run = Path(run)
    try:
        st = os.lstat(run)
    except FileNotFoundError as e:
        raise Refused("P65_RUN directory must exist and be empty") from e
    if (not stat.S_ISDIR(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o700 or st.st_uid != os.getuid()
            or os.listdir(run)):
        raise Refused("P65_RUN directory must exist, be empty, mode 0700 and owned by this user")
    daily, intra, acts = parse(blobs, sessions, cfg)
    preflight(daily, sessions)
    lock_file(run / LOCK, {"approval_commit": commit, "inputs_sha256": in_digest,
                           "taken_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")})
    res = score(daily, intra, acts, sessions, cfg)
    res["coverage"] = coverage(daily, intra, sessions, cfg)
    res["approval_commit"], res["inputs_sha256"] = commit, in_digest
    write_result(run / RESULT, res)
    return res


def synthetic_inputs(sessions, cfg, seed=65):
    """Seeded fake bars for every session: random walks, a signal-bar price inside each day, and regular cash
    actions. For checking the machinery only; it carries no edge and says nothing about power."""
    rng = np.random.default_rng(seed)
    n = len(sessions)
    out = {}
    px = {"SPY": 200.0, "IEF": 105.0, "TLT": 120.0, "SH": 40.0}
    vol = {"SPY": 0.011, "IEF": 0.004, "TLT": 0.009, "SH": 0.011}
    closes = {s: np.zeros(n) for s in DAILY}
    mids = {s: np.zeros(n) for s in DAILY}
    for s in DAILY:
        p = px[s]
        for i in range(n):
            mid = p * math.exp(vol[s] * 0.97 * rng.standard_normal())
            p = mid * math.exp(vol[s] * 0.25 * rng.standard_normal())
            mids[s][i], closes[s][i] = mid, p
    for s in DAILY:
        rows = []
        for i, x in enumerate(sessions):
            stamp = x[0] + "T" + ("05" if x[1][11:13] == "14" else "04") + ":00:00Z"   # midnight New York
            c = round(float(closes[s][i]), 2)
            rows.append({"t": stamp, "o": c, "h": c, "l": c, "c": c, "v": 1000})
        out[s + "_1d.json"] = json.dumps(rows).encode()
    for s in INTRA:
        rows = []
        for i, x in enumerate(sessions):
            c = round(float(mids[s][i]), 2)
            rows.append({"t": signal_bar_start(x, cfg), "o": c, "h": c, "l": c, "c": c, "v": 100})
        out[s + "_15m.json"] = json.dumps(rows).encode()
    acts = []
    for i, x in enumerate(sessions):
        if x[0][5:7] in ("03", "06", "09", "12") and x[0][8:10] == "18":
            acts.append({"symbol": "SPY", "type": "cash", "ex_date": x[0], "amount": 1.25})
        if x[0][8:10] == "02":
            acts.append({"symbol": "IEF", "type": "cash", "ex_date": x[0], "amount": 0.2})
    out["actions.json"] = json.dumps(acts).encode()
    return out


def run_synthetic(config=CONFIG, calendar=HERE / "calendar_65.json"):
    cfg = load_config(Path(config).read_bytes())
    sessions = load_calendar(Path(calendar).read_bytes(), cfg)
    blobs = synthetic_inputs(sessions, cfg)
    daily, intra, acts = parse(blobs, sessions, cfg)
    cov = coverage(daily, intra, sessions, cfg)
    res = score(daily, intra, acts, sessions, cfg)
    return cov, res


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--synthetic", action="store_true")
    g.add_argument("--validate-inputs", action="store_true")
    g.add_argument("--go", action="store_true")
    ap.add_argument("--approval-commit")
    a = ap.parse_args()
    try:
        if a.synthetic:
            cov, res = run_synthetic()
            print("SYNTHETIC ONLY, no real bar read")
            print(json.dumps({"coverage": cov, "judged_marks_met": res["judged"]["marks_met"], "n": res["judged"]["n"]}))
        elif a.validate_inputs:
            print(json.dumps(validate(), sort_keys=True, indent=1))
        else:
            res = go(a.approval_commit)
            j = res["judged"]
            print(json.dumps({"pass": j.get("pass"), "marks_met": j.get("marks_met"), "n": j.get("n")}))
    except Refused as e:
        print("REFUSED", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
