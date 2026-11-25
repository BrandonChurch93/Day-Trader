"""Replay logged AI and random-twin crypto BUY entries under five fixed exit templates (plan TMX1).

Reads only finished session folders (result.json present) under $TM_RUNS and 1Min bars from
$TM_STORE/tape.sqlite (read-only). Costs come from config/thresholds.yaml.
Writes timemachine/results_tmx1.json and docs/research/32_exit_replay.md.
"""
import datetime as dt
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent
RUNS = Path(os.environ.get("TM_RUNS", "/home/user/workspace/rig/tm_runs"))
TAPE = Path(os.environ.get("TM_STORE", "/home/user/workspace/rig/tm_store")) / "tape.sqlite"
CFG = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())

MODELS = [
    ("OPUS", "Claude Opus 5.5"),
    ("SOL", "GPT-6.2 Sol"),
    ("NEON", "Gemini Neon"),
    ("SONNET", "Claude Sonnet 5.5"),
    ("KIMI", "Kimi K3"),
    ("GROK", "Grok 4.7"),
]
MONTHS = [
    ("07", "July"),
    ("08", "August"),
    ("09", "September"),
    ("10", "October"),
    ("11", "November 1 to 24"),
]
SEEDS = list(range(1, 21))
TEMPLATES = ("A", "B", "C", "D", "E")
TEMPLATE_DESC = {
    "A": "as traded (from session records)",
    "B": "time only, 48 hours after fill",
    "C": "time only, 120 hours after fill",
    "D": "stop 8% below fill, no target, 120 hours",
    "E": "stop 8%, once up 3% trail 5% below highest close, 120 hours",
}

HS = CFG["tm_crypto_half_spread_bps"]["value"] / 1e4
FEE = CFG["practice_crypto_fee_bps_added"]["value"] / 1e4
IN_COIN = bool(CFG["practice_crypto_fee_in_coin"]["value"])


def parse_utc(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())


def utc_now_str():
    return subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M:%S UTC"], text=True).strip()


def load_tape_minutes(symbols):
    """Load all 1Min bars for the needed symbols from 2026-07-01 through 2026-11-26 (read-only)."""
    t_lo = parse_utc("2026-07-01T00:00:00Z")
    t_hi = parse_utc("2026-11-26T00:00:00Z")
    con = sqlite3.connect(f"file:{TAPE}?mode=ro", uri=True)
    data = {}
    for sym in sorted(set(symbols) | {"BTC/USD"}):
        rows = con.execute(
            "SELECT t, o, c FROM bars WHERE symbol=? AND tf='1Min' AND t>=? AND t<? ORDER BY t",
            (sym, t_lo, t_hi),
        ).fetchall()
        arr = np.asarray(rows, dtype=np.float64)
        if len(arr):
            data[sym] = (arr[:, 0].astype(np.int64), arr[:, 1], arr[:, 2])
        else:
            data[sym] = (np.empty(0, dtype=np.int64), np.empty(0), np.empty(0))
    con.close()
    return data


def trade_gain_usd(qty, buy_px, sell_open):
    sell_px = sell_open * (1.0 - HS)
    if IN_COIN:
        return qty * (1.0 - FEE) * sell_px * (1.0 - FEE) - qty * buy_px
    return qty * sell_px * (1.0 - FEE) - qty * buy_px * (1.0 + FEE)


def btc_window_gain(btc_bars, fill_ts, exit_ts, end_ts, notional):
    t_arr, o_arr, c_arr = btc_bars
    last_idx = int(np.searchsorted(t_arr, end_ts, side="left")) - 1
    if last_idx < 0:
        return 0.0
    i_in = int(np.searchsorted(t_arr, fill_ts, side="left"))
    if i_in > last_idx:
        return 0.0
    btc_buy_px = float(o_arr[i_in]) * (1.0 + HS)
    btc_qty = notional / btc_buy_px
    i_out = int(np.searchsorted(t_arr, exit_ts, side="left"))
    if i_out > last_idx:
        sell_open = float(o_arr[last_idx])
    else:
        sell_open = float(o_arr[i_out])
    return trade_gain_usd(btc_qty, btc_buy_px, sell_open)


def simulate_exit(bars, fill_ts, buy_px, end_ts, template):
    """Return (sell_open, exit_ts, exit_reason) for templates B..E."""
    t_arr, o_arr, c_arr = bars
    last_idx = int(np.searchsorted(t_arr, end_ts, side="left")) - 1
    assert last_idx >= 0, "no 1Min bars inside session"

    def time_exit(hours):
        target_ts = fill_ts + hours * 3600
        if target_ts < end_ts:
            j = int(np.searchsorted(t_arr, target_ts, side="left"))
            if j <= last_idx:
                return float(o_arr[j]), int(t_arr[j]), "time"
        return float(o_arr[last_idx]), int(t_arr[last_idx]), "session_end"

    if template == "B":
        return time_exit(48)
    if template == "C":
        return time_exit(120)

    # Templates D and E: check 1Min closes strictly after fill_ts and before min(fill_ts + 120h, end_ts)
    limit_ts = min(fill_ts + 120 * 3600, end_ts)
    k0 = int(np.searchsorted(t_arr, fill_ts, side="right"))
    k1 = int(np.searchsorted(t_arr, limit_ts, side="left"))
    k1 = min(k1, last_idx + 1)

    stop_px = 0.92 * buy_px
    if template == "D":
        if k0 < k1:
            sub_c = c_arr[k0:k1]
            hits = np.flatnonzero(sub_c <= stop_px)
            if len(hits):
                k = k0 + int(hits[0])
                if k + 1 <= last_idx:
                    return float(o_arr[k + 1]), int(t_arr[k + 1]), "stop"
                return float(c_arr[k]), int(t_arr[k]), "stop_end"
        return time_exit(120)

    if template == "E":
        if k0 < k1:
            sub_c = c_arr[k0:k1]
            # Vectorized highest close since entry (starting from buy_px)
            highs = np.maximum.accumulate(np.maximum(sub_c, buy_px))
            activated = np.maximum.accumulate(sub_c >= 1.03 * buy_px)
            active_stop = np.where(activated, np.maximum(stop_px, 0.95 * highs), stop_px)
            hits = np.flatnonzero(sub_c <= active_stop)
            if len(hits):
                k = k0 + int(hits[0])
                if k + 1 <= last_idx:
                    return float(o_arr[k + 1]), int(t_arr[k + 1]), "trail_or_stop"
                return float(c_arr[k]), int(t_arr[k]), "trail_or_stop_end"
        return time_exit(120)

    raise ValueError(template)


def replay_session(res, tape, anomalies, sid, is_twin=False):
    end_ts = parse_utc(res["session"]["end_utc"])
    orders = res["summary"]["orders"]
    closed = res["summary"]["closed"]
    acct_gain = float(res["summary"]["account"]["gain_usd"])
    buys = [o for o in orders if o["side"] == "buy" and o["status"] == "filled"]

    # Check trade-record oddities (for AI sessions)
    if not is_twin:
        non_filled_buys = [o for o in orders if o["side"] == "buy" and o["status"] != "filled"]
        if non_filled_buys:
            anomalies.append(f"{sid}: {len(non_filled_buys)} non-filled buy order(s) (statuses: {sorted({o['status'] for o in non_filled_buys})})")
        tr = res["summary"]["traders"][0]
        if tr.get("halted"):
            anomalies.append(f"{sid}: trader halted ({tr.get('halt_reason')})")
        if res["summary"].get("problems"):
            anomalies.append(f"{sid}: problems={res['summary']['problems']}")
        open_pos = tr.get("positions") or []
        closed_sum = sum(float(c["gain_usd"]) for c in closed)
        if open_pos:
            anomalies.append(f"{sid}: {len(open_pos)} open position(s) at session end (acct={acct_gain:.2f}, closed_sum={closed_sum:.2f})")
        elif abs(acct_gain - closed_sum) > 0.15:
            anomalies.append(f"{sid}: acct gain ({acct_gain:.2f}) differs from sum(closed) ({closed_sum:.2f}) by {acct_gain - closed_sum:+.2f}")
        if not buys:
            anomalies.append(f"{sid}: 0 filled buys")

    gains = {t: 0.0 for t in TEMPLATES}
    btc_gains = {t: 0.0 for t in TEMPLATES}
    gains["A"] = acct_gain

    # Match each buy to its closed trade (for BTC window under A)
    left_closed = sorted(closed, key=lambda c: c["opened_utc"])
    btc_bars = tape["BTC/USD"]

    for o in buys:
        sym = o["symbol"]
        fill_ts = parse_utc(o["filled_utc"])
        buy_px = float(o["fill_price"])
        qty = float(o["qty"])
        notional = qty * buy_px

        # Sanity-check fill_price vs tape open * (1 + HS)
        if not is_twin:
            t_arr, o_arr, _ = tape[sym]
            idx = int(np.searchsorted(t_arr, fill_ts, side="left"))
            if idx >= len(t_arr) or int(t_arr[idx]) != fill_ts:
                anomalies.append(f"{sid}: buy fill_utc {o['filled_utc']} for {sym} not exact in 1Min tape")
            else:
                expected_px = float(o_arr[idx]) * (1.0 + HS)
                if abs(buy_px - expected_px) / expected_px > 1e-4:
                    anomalies.append(f"{sid}: buy fill_price {buy_px:.6f} != tape open*(1+hs) {expected_px:.6f} for {sym} at {o['filled_utc']}")

        # Matched exit timestamp for A's BTC window
        c_match = None
        for c in left_closed:
            if c["symbol"] == sym and c["opened_utc"] == o["filled_utc"]:
                c_match = c
                left_closed.remove(c)
                break
        if c_match is None:
            # Fallback: first closed for same symbol opened >= filled_utc
            for c in left_closed:
                if c["symbol"] == sym and c["opened_utc"] >= o["filled_utc"]:
                    c_match = c
                    left_closed.remove(c)
                    break
        a_exit_ts = parse_utc(c_match["closed_utc"]) if c_match is not None else end_ts
        btc_gains["A"] += btc_window_gain(btc_bars, fill_ts, a_exit_ts, end_ts, notional)

        for tmpl in ("B", "C", "D", "E"):
            sell_open, exit_ts, _ = simulate_exit(tape[sym], fill_ts, buy_px, end_ts, tmpl)
            gains[tmpl] += trade_gain_usd(qty, buy_px, sell_open)
            btc_gains[tmpl] += btc_window_gain(btc_bars, fill_ts, exit_ts, end_ts, notional)

    return dict(
        buys=len(buys),
        gains={k: round(v, 4) for k, v in gains.items()},
        btc_gains={k: round(v, 4) for k, v in btc_gains.items()},
    )


def run_plan(plan_name, prefix, tape, anomalies):
    finished = []
    unfinished = []
    sessions = {}
    twin_sessions = {}
    twin_unfinished = 0

    for tag, mname in MODELS:
        for mo, moname in MONTHS:
            sid = f"{prefix}-{tag}-2026-{mo}"
            rp = RUNS / sid / "result.json"
            if not rp.exists():
                unfinished.append(sid)
                continue
            finished.append(sid)
            res = json.loads(rp.read_text())
            sessions[(tag, mo)] = replay_session(res, tape, anomalies, sid, is_twin=False)

            # Finished twins for this session
            t_list = []
            for seed in SEEDS:
                tsid = f"TWIN-{sid}-s{seed}"
                trp = RUNS / tsid / "result.json"
                if trp.exists():
                    tres = json.loads(trp.read_text())
                    t_list.append(replay_session(tres, tape, anomalies, tsid, is_twin=True))
                elif (RUNS / tsid).exists():
                    twin_unfinished += 1
            if t_list:
                twin_sessions[(tag, mo)] = dict(
                    count=len(t_list),
                    mean_gains={t: round(float(np.mean([x["gains"][t] for x in t_list])), 4) for t in TEMPLATES},
                    mean_btc_gains={t: round(float(np.mean([x["btc_gains"][t] for x in t_list])), 4) for t in TEMPLATES},
                )

    by_model = {}
    for tag, mname in MODELS:
        mos = [mo for mo, _ in MONTHS if (tag, mo) in sessions]
        by_model[tag] = dict(
            name=mname,
            months_finished=mos,
            buys=sum(sessions[(tag, mo)]["buys"] for mo in mos),
            gains={t: round(sum(sessions[(tag, mo)]["gains"][t] for mo in mos), 2) for t in TEMPLATES},
            btc_gains={t: round(sum(sessions[(tag, mo)]["btc_gains"][t] for mo in mos), 2) for t in TEMPLATES},
        )

    by_month = {}
    for mo, moname in MONTHS:
        tags = [tag for tag, _ in MODELS if (tag, mo) in sessions]
        by_month[mo] = dict(
            name=moname,
            models_finished=tags,
            buys=sum(sessions[(tag, mo)]["buys"] for tag in tags),
            gains={t: round(sum(sessions[(tag, mo)]["gains"][t] for tag in tags), 2) for t in TEMPLATES},
            btc_gains={t: round(sum(sessions[(tag, mo)]["btc_gains"][t] for tag in tags), 2) for t in TEMPLATES},
        )

    totals = dict(
        sessions_finished=len(finished),
        sessions_unfinished=len(unfinished),
        buys=sum(s["buys"] for s in sessions.values()),
        gains={t: round(sum(s["gains"][t] for s in sessions.values()), 2) for t in TEMPLATES},
        btc_gains={t: round(sum(s["btc_gains"][t] for s in sessions.values()), 2) for t in TEMPLATES},
    )

    # AI minus twins (only across sessions that have >= 1 finished twin)
    paired_keys = sorted(twin_sessions.keys())
    ai_minus_twins = dict(
        paired_sessions=len(paired_keys),
        twin_runs_used=sum(twin_sessions[k]["count"] for k in paired_keys),
        twin_unfinished_folders=twin_unfinished,
        ai_gains={t: round(sum(sessions[k]["gains"][t] for k in paired_keys), 2) for t in TEMPLATES},
        twin_mean_gains={t: round(sum(twin_sessions[k]["mean_gains"][t] for k in paired_keys), 2) for t in TEMPLATES},
        diff={t: round(sum(sessions[k]["gains"][t] - twin_sessions[k]["mean_gains"][t] for k in paired_keys), 2) for t in TEMPLATES},
        by_model={},
        by_month={},
    )
    for tag, mname in MODELS:
        ks = [k for k in paired_keys if k[0] == tag]
        if ks:
            ai_minus_twins["by_model"][tag] = dict(
                name=mname,
                paired_months=len(ks),
                diff={t: round(sum(sessions[k]["gains"][t] - twin_sessions[k]["mean_gains"][t] for k in ks), 2) for t in TEMPLATES},
            )
    for mo, moname in MONTHS:
        ks = [k for k in paired_keys if k[1] == mo]
        if ks:
            ai_minus_twins["by_month"][mo] = dict(
                name=moname,
                paired_models=len(ks),
                diff={t: round(sum(sessions[k]["gains"][t] - twin_sessions[k]["mean_gains"][t] for k in ks), 2) for t in TEMPLATES},
            )

    # Verdict against fixed marks (TM01 is the primary mark; also compute for TM02 as informational)
    verdict = {}
    for tmpl in ("B", "C", "D", "E"):
        m_beat = [mo for mo, _ in MONTHS if by_month[mo]["models_finished"] and by_month[mo]["gains"][tmpl] > by_month[mo]["gains"]["A"]]
        mod_beat = [tag for tag, _ in MODELS if by_model[tag]["months_finished"] and by_model[tag]["gains"][tmpl] > by_model[tag]["gains"]["A"]]
        verdict[tmpl] = dict(
            months_beating_A=len(m_beat),
            months_list=m_beat,
            models_beating_A=len(mod_beat),
            models_list=mod_beat,
            helps=bool(len(m_beat) >= 4 and len(mod_beat) >= 5),
        )

    return dict(
        plan=plan_name,
        finished=finished,
        unfinished=unfinished,
        totals=totals,
        by_model=by_model,
        by_month=by_month,
        ai_minus_twins=ai_minus_twins,
        verdict=verdict,
    )


def usd(x):
    if x is None:
        return "n/a"
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def build_doc(out):
    L = [
        "# Time machine exit replay (TMX1): fixed exit templates on logged AI buys",
        "",
        f"Made by `timemachine/exit_replay.py` from `timemachine/results_tmx1.json` at {out['run_utc']}. Do not edit by hand. Pretend money only. Plan fixed before running: `timemachine/PLAN_TMX1_exit_replay.md`.",
        "",
        "## What was tested",
        "",
        "- Every logged filled BUY from finished `TM01` (prices only) and `TM02` (with news) sessions, plus finished random twin sessions, replayed one trade at a time on its own without re-simulating the cash book.",
        "- Costs from `config/thresholds.yaml`: half-spread `tm_crypto_half_spread_bps` and fee `practice_crypto_fee_bps_added` (`practice_crypto_fee_in_coin` = " + str(out["costs"]["fee_in_coin"]) + "), filled on 1Min bars from the recorded tape.",
        "- Templates: A = as traded; B = 48h time only; C = 120h time only; D = 8% stop, no target, 120h; E = 8% stop, +3% trigger / 5% trail, 120h. Stops check each 1Min close and fill at the next minute's open. Trades still open at session end close at the session's last minute.",
        "- Fixed mark: on `TM01` AI buys, a template helps only if its summed dollar gain beats A in at least 4 of the 5 months AND for at least 5 of the 6 models.",
        "",
        "## Session coverage at run time",
        "",
        f"Run timestamp: {out['run_utc']}.",
        "",
    ]
    for pname in ("TM01", "TM02"):
        p = out["plans"][pname]
        unfin = ", ".join(p["unfinished"]) if p["unfinished"] else "none"
        L.append(f"- {pname}: {p['totals']['sessions_finished']} finished, {p['totals']['sessions_unfinished']} unfinished ({unfin}). Paired with twins: {p['ai_minus_twins']['paired_sessions']} sessions ({p['ai_minus_twins']['twin_runs_used']} finished twin runs).")

    for pname in ("TM01", "TM02"):
        p = out["plans"][pname]
        L += [
            "",
            f"## {pname}: summed dollar gain by model",
            "",
            "| Model | Months | Buys | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for tag, _ in MODELS:
            m = p["by_model"][tag]
            g = m["gains"]
            L.append(f"| {m['name']} | {len(m['months_finished'])} of 5 | {m['buys']} | {usd(g['A'])} | {usd(g['B'])} | {usd(g['C'])} | {usd(g['D'])} | {usd(g['E'])} |")
        tg = p["totals"]["gains"]
        bg = p["totals"]["btc_gains"]
        L.append(f"| **Total (AI buys)** | {p['totals']['sessions_finished']} sess | {p['totals']['buys']} | {usd(tg['A'])} | {usd(tg['B'])} | {usd(tg['C'])} | {usd(tg['D'])} | {usd(tg['E'])} |")
        L.append(f"| **BTC same windows** | same | same | {usd(bg['A'])} | {usd(bg['B'])} | {usd(bg['C'])} | {usd(bg['D'])} | {usd(bg['E'])} |")

        L += [
            "",
            f"## {pname}: summed dollar gain by month",
            "",
            "| Month | Models | Buys | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) | BTC same windows (A / B / C / D / E) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
        for mo, _ in MONTHS:
            m = p["by_month"][mo]
            g = m["gains"]
            b = m["btc_gains"]
            b_str = " / ".join(usd(b[t]) for t in TEMPLATES)
            L.append(f"| {m['name']} | {len(m['models_finished'])} of 6 | {m['buys']} | {usd(g['A'])} | {usd(g['B'])} | {usd(g['C'])} | {usd(g['D'])} | {usd(g['E'])} | {b_str} |")

    # AI minus twins section
    L += ["", "## AI buys minus random twin buys", ""]
    for pname in ("TM01", "TM02"):
        tw = out["plans"][pname]["ai_minus_twins"]
        if not tw["paired_sessions"]:
            L.append(f"- {pname}: 0 finished twin sessions at run time; AI minus twins is not available yet.")
            continue
        L += [
            f"Paired across {tw['paired_sessions']} finished {pname} sessions ({tw['twin_runs_used']} finished twin runs; each session's twins averaged to match 1 AI session scale).",
            "",
            "| Group | Paired | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) |",
            "|---|---:|---:|---:|---:|---:|---:|",
            f"| AI buys (paired) | {tw['paired_sessions']} | " + " | ".join(usd(tw["ai_gains"][t]) for t in TEMPLATES) + " |",
            f"| Twin mean (paired) | {tw['paired_sessions']} | " + " | ".join(usd(tw["twin_mean_gains"][t]) for t in TEMPLATES) + " |",
            f"| **AI minus twins** | {tw['paired_sessions']} | " + " | ".join(usd(tw["diff"][t]) for t in TEMPLATES) + " |",
            "",
            f"By model ({pname}, AI minus twins):",
            "",
            "| Model | Paired months | A | B | C | D | E |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for tag, _ in MODELS:
            if tag in tw["by_model"]:
                row = tw["by_model"][tag]
                L.append(f"| {row['name']} | {row['paired_months']} | " + " | ".join(usd(row["diff"][t]) for t in TEMPLATES) + " |")
        L += [
            "",
            f"By month ({pname}, AI minus twins):",
            "",
            "| Month | Paired models | A | B | C | D | E |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for mo, _ in MONTHS:
            if mo in tw["by_month"]:
                row = tw["by_month"][mo]
                L.append(f"| {row['name']} | {row['paired_models']} | " + " | ".join(usd(row["diff"][t]) for t in TEMPLATES) + " |")

    # Verdict table
    L += [
        "",
        "## Verdict against the fixed marks",
        "",
        "Primary mark is `TM01` AI buys: a template helps only if it beats A in at least 4 of 5 months AND for at least 5 of 6 models. `TM02` is shown beside it for reference.",
        "",
        "| Template | Description | TM01 total vs A | TM01 months > A | TM01 models > A | TM01 verdict | TM02 months > A | TM02 models > A |",
        "|---|---|---:|---:|---:|---|---:|---:|",
    ]
    p1, p2 = out["plans"]["TM01"], out["plans"]["TM02"]
    for tmpl in ("B", "C", "D", "E"):
        v1, v2 = p1["verdict"][tmpl], p2["verdict"][tmpl]
        diff1 = p1["totals"]["gains"][tmpl] - p1["totals"]["gains"]["A"]
        verdict_txt = "HELPS (earns fresh test on new months)" if v1["helps"] else "does not help"
        L.append(
            f"| {tmpl} | {TEMPLATE_DESC[tmpl]} | {usd(diff1)} | {v1['months_beating_A']} of 5 | {v1['models_beating_A']} of 6 | {verdict_txt} | {v2['months_beating_A']} of 5 | {v2['models_beating_A']} of 6 |"
        )

    # Anomalies
    L += ["", "## Trade-record checks", ""]
    if out["anomalies"]:
        for a in out["anomalies"]:
            L.append(f"- {a}")
    else:
        L.append("- No anomalies found in finished AI session trade records.")

    L += [
        "",
        "## What this does not show",
        "",
        "- This is a second look at months already traded. A \"helps\" verdict does not prove a rule is profitable and is not a result to trade on; it only earns a fresh test on new months.",
        "- Each buy is replayed on its own without re-simulating the cash book. Longer holds (48h or 120h) would tie up cash and block some later buys in a live cash account, so summed per-trade dollars overstate what a single cash book could deploy when buys overlap.",
        "- A longer hold in a rising market gains from market drift alone. Compare AI buys against both BTC over the same windows and AI minus random twins before attributing any gain to entry skill.",
        "- Fills are assumed from recorded 1Min bars with fixed spread and fee assumptions; real fills on thin crypto minutes could be worse.",
        "- Unfinished sessions at run time are omitted; rerunning after all 30 sessions per plan and all 20 twins per session finish may change totals.",
        "",
    ]
    return "\n".join(L)


def main():
    run_utc = utc_now_str()
    # Discover all symbols used in finished sessions
    syms = {"BTC/USD"}
    for prefix in ("TM01-B01", "TM02-B02", "TWIN-TM01-B01", "TWIN-TM02-B02"):
        for rp in RUNS.glob(f"{prefix}-*/result.json"):
            res = json.loads(rp.read_text())
            for o in res["summary"]["orders"]:
                if o["side"] == "buy" and o["status"] == "filled":
                    syms.add(o["symbol"])
    tape = load_tape_minutes(syms)
    anomalies = []
    out = dict(
        plan="timemachine/PLAN_TMX1_exit_replay.md",
        run_utc=run_utc,
        costs=dict(
            half_spread_bps=CFG["tm_crypto_half_spread_bps"]["value"],
            fee_bps=CFG["practice_crypto_fee_bps_added"]["value"],
            fee_in_coin=CFG["practice_crypto_fee_in_coin"]["value"],
        ),
        plans=dict(
            TM01=run_plan("TM01", "TM01-B01", tape, anomalies),
            TM02=run_plan("TM02", "TM02-B02", tape, anomalies),
        ),
        anomalies=anomalies,
    )
    out_path = ROOT / "timemachine/results_tmx1.json"
    doc_path = ROOT / "docs/research/32_exit_replay.md"
    out_path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    doc_path.write_text(build_doc(out))
    print(f"Wrote {out_path} and {doc_path} at {run_utc}")
    for pname in ("TM01", "TM02"):
        p = out["plans"][pname]
        print(f"\n=== {pname} ({p['totals']['sessions_finished']} finished, {p['totals']['buys']} buys) ===")
        print("Totals AI :", p["totals"]["gains"])
        print("Totals BTC:", p["totals"]["btc_gains"])
        print("AI-Twins  :", p["ai_minus_twins"]["diff"], f"(paired={p['ai_minus_twins']['paired_sessions']})")
        for t in ("B", "C", "D", "E"):
            v = p["verdict"][t]
            print(f"  {t}: months={v['months_beating_A']}/5, models={v['models_beating_A']}/6, helps={v['helps']}")
    print(f"\nAnomalies ({len(anomalies)}):")
    for a in anomalies[:25]:
        print(" ", a)


if __name__ == "__main__":
    main()
