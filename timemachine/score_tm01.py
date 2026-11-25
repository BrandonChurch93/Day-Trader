"""Scores plan TM01 (timemachine/PLAN_TM01_crypto_price_only.md) from the finished session folders. Pretend money only.

python3 timemachine/score_tm01.py            writes timemachine/results_tm01.json and docs/research/29_time_machine_tm01_crypto_price_only.md
python3 timemachine/score_tm01.py --check    exits 1 if the stored files differ from what the session folders give now

Reads only result.json and looks.jsonl of each session under $TM_RUNS. It runs no trader and reads no prices.
A month counts for a model when its AI session, the bitcoin hold of that month and all 20 twins are finished.
The verdict of the plan is written only when all five months count for a model."""
import datetime as dt
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = Path(os.environ.get("TM_RUNS", "/home/user/workspace/rig/tm_runs"))
OUT = ROOT / "timemachine" / "results_tm01.json"
DOC = ROOT / "docs" / "research" / "29_time_machine_tm01_crypto_price_only.md"
MODELS = [("OPUS", "Claude Opus 5.5"), ("SOL", "GPT-6.2 Sol"), ("NEON", "Gemini Neon"), ("SONNET", "Claude Sonnet 5.5"), ("KIMI", "Kimi K3"), ("GROK", "Grok 4.7")]
MONTHS = [("07", "July"), ("08", "August"), ("09", "September"), ("10", "October"), ("11", "November 1 to 24")]
SEEDS = list(range(1, 21))
HOLD_ID = {"10": "HOLD-BTCUSD-2026-10-real1"}


def load(session):
    p = RUNS / session / "result.json"
    return json.loads(p.read_text()) if p.exists() else None


def pct80(xs):
    """80th percentile with straight-line interpolation between ranks (the usual method)."""
    s = sorted(xs); pos = 0.8 * (len(s) - 1); lo = int(pos); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def max_drop(points):
    peak, worst = None, 0.0
    for p in points:
        v = p["value_usd"]; peak = v if peak is None or v > peak else peak
        worst = min(worst, v / peak - 1.0)
    return worst


def why_rows(session, r):
    """One row per buy: what the trader looked up at that wake, what it said, and how the trade ended."""
    looks = {}
    lp = RUNS / session / "looks.jsonl"
    if lp.exists():
        for line in lp.read_text().splitlines():
            d = json.loads(line); looks.setdefault(d["k"], []).append(d)
    orders = r["summary"]["orders"]; sells = [o for o in orders if o["side"] == "sell" and o["status"] == "filled"]
    left = sorted(r["summary"]["closed"], key=lambda c: c["opened_utc"])

    def closed_for(symbol, wake_utc):
        # The buy fills at the first recorded minute at or after the wake, which can be some minutes later on a thin coin.
        # Take the first closed trade in that coin opened at or after the wake and within twelve hours, and use it once.
        hi = (dt.datetime.fromisoformat(wake_utc.replace("Z", "+00:00")) + dt.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for c in left:
            if c["symbol"] == symbol and wake_utc <= c["opened_utc"] < hi:
                left.remove(c); return c
        return None
    rows = []
    for st in r["steps"]:
        pick = st.get("pick") or {}
        for a in pick.get("actions", []):
            if a.get("side") != "buy":
                continue
            lk = looks.get(st["k"], [])
            seen = {}
            for d in lk:
                key = d["timeframe"] if d["what"] == "bars" else d["what"]; seen[key] = seen.get(key, 0) + 1
            c = closed_for(a["symbol"], st["utc"])
            ex = next((o for o in sells if c and o["symbol"] == a["symbol"] and o["filled_utc"] == c["closed_utc"]), None)
            rows.append(dict(wake_utc=st["utc"], symbol=a["symbol"], usd=a.get("usd"), looked=seen, news_looked=seen.get("news", 0),
                             thesis=pick.get("thesis"), reason=a.get("reason"),
                             closed_utc=c["closed_utc"] if c else None, result=c["result"] if c else "still held at the end or not filled",
                             gain_usd=c["gain_usd"] if c else None, gain_pct=round(c["gain_pct"], 4) if c else None,
                             exit_reason=ex["reason"] if ex else None))
    return rows


def session_row(tag, mo):
    sid = f"TM01-B01-{tag}-2026-{mo}"; r = load(sid)
    if r is None:
        return dict(session=sid, finished=False)
    s = r["summary"]; t = s["totals"]; steps = r["steps"]
    twins = {}
    for seed in SEEDS:
        tr = load(f"TWIN-{sid}-s{seed}")
        if tr is not None:
            twins[seed] = tr["summary"]["account"]["gain_usd"]
    hold = load(HOLD_ID.get(mo, f"HOLD-BTCUSD-2026-{mo}"))
    row = dict(session=sid, finished=True, model=r["session"]["model"], wakes=len(steps), gain_usd=s["account"]["gain_usd"],
               buys=sum(1 for o in s["orders"] if o["side"] == "buy" and o["status"] == "filled"),
               closed=t["closed_trades"], wins=t["wins"], losses=t["losses"], fees_usd=t["fees_added_usd"], max_drop=round(max_drop(s["points"]), 4),
               wakes_no_pick=sum(1 for x in steps if x.get("pick") is None), refused_attempts=sum(x.get("bad_attempts", 0) for x in steps),
               lookups=sum(x.get("looks", 0) for x in steps), git_dirty=r["session"]["git"]["dirty"], config_hash=r["session"]["config_hash"],
               benchmark_shown=r["session"]["benchmark"], hold_gain_usd=hold["summary"]["account"]["gain_usd"] if hold else None,
               twins_done=len(twins), twin_gains={str(k): v for k, v in sorted(twins.items())}, why=why_rows(sid, r))
    row["counts"] = hold is not None and len(twins) == len(SEEDS)
    if len(twins) == len(SEEDS):
        g = list(twins.values()); row["twin_p80_usd"] = round(pct80(g), 2); row["twin_median_usd"] = round(sorted(g)[len(g) // 2 - 1] / 2 + sorted(g)[len(g) // 2] / 2, 2)
        row["twins_beaten"] = sum(1 for x in g if row["gain_usd"] > x)
    return row


def build():
    out = dict(plan="timemachine/PLAN_TM01_crypto_price_only.md", start_usd=None, models={})
    for tag, name in MODELS:
        rows = {mo: session_row(tag, mo) for mo, _ in MONTHS}
        done = [mo for mo, _ in MONTHS if rows[mo].get("counts")]
        m = dict(name=name, months=rows, months_counted=done)
        if done:
            m["sum_gain_usd"] = round(sum(rows[mo]["gain_usd"] for mo in done), 2)
            m["sum_hold_usd"] = round(sum(rows[mo]["hold_gain_usd"] for mo in done), 2)
            sums = [sum(rows[mo]["twin_gains"][str(seed)] for mo in done) for seed in SEEDS]
            m["sum_twin_p80_usd"] = round(pct80(sums), 2); m["sum_twins_beaten"] = sum(1 for x in sums if m["sum_gain_usd"] > x)
            m["beats_hold"] = m["sum_gain_usd"] > m["sum_hold_usd"]; m["beats_twins"] = m["sum_gain_usd"] > m["sum_twin_p80_usd"]
        m["verdict"] = ("counts: beat both yardsticks" if m.get("beats_hold") and m.get("beats_twins") else "has shown nothing") if len(done) == len(MONTHS) else "not finished"
        out["models"][tag] = m
    return out


def usd(x):
    return "n/a" if x is None else (f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}")


def doc(o):
    L = ["# Time machine plan TM01: six AI models trade crypto from prices alone", "",
         "Made by `timemachine/score_tm01.py` from `timemachine/results_tm01.json`. Do not edit by hand. Pretend money. The plan, with its pass mark fixed before any session ran, is `timemachine/PLAN_TM01_crypto_price_only.md`.", "",
         "## What was run", "",
         "- Each model follows the card `practice/traders/B01_crypto_swing_price_only.md` alone in a pretend account of `tm_account_start_usd`, one session per month, a fresh agent per session.",
         "- It wakes at the hours in `tm_crypto_wake_hours_utc`, sees prices up to that minute and nothing later, and may buy any of eight coins. It cannot sell short.",
         "- Costs: the fee `practice_crypto_fee_bps_added` and the spread `tm_crypto_half_spread_bps` on each side. Fills are assumed at the next recorded minute's open.",
         "- Yardsticks: holding bitcoin for the month, and 20 random twins per session that buy at the same wakes and sizes with the same exits, a coin drawn at random.",
         "- What counts, from the plan: over the five months added up, a model's gain is above holding bitcoin and above the 80th percentile of its twins. One month alone decides nothing.", "",
         "## Where each model stands", "",
         "MEASURED, pretend money, months finished so far. A month is in the sum when the AI session, the hold and all 20 twins are done.", "",
         "| Model | Months counted | Gain summed | Holding bitcoin, same months | 80th percentile of twins | Twins beaten | Verdict |", "|---|---|---|---|---|---|---|"]
    for tag, _ in MODELS:
        m = o["models"][tag]; n = len(m["months_counted"])
        L.append(f"| {m['name']} | {n} of {len(MONTHS)} | {usd(m.get('sum_gain_usd'))} | {usd(m.get('sum_hold_usd'))} | {usd(m.get('sum_twin_p80_usd'))} | {m.get('sum_twins_beaten', 'n/a')}{' of 20' if n else ''} | {m['verdict']} |")
    L += ["", "## Each session", "",
          "| Month | Model | Gain | Hold | Twin 80th pct | Twins beaten | Buys | Wins | Losses | Fees | Largest drop | Wakes with no pick | Lookups |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for mo, mname in MONTHS:
        for tag, _ in MODELS:
            r = o["models"][tag]["months"][mo]
            if not r["finished"]:
                L.append(f"| {mname} | {o['models'][tag]['name']} | not finished | | | | | | | | | | |"); continue
            L.append(f"| {mname} | {o['models'][tag]['name']} | {usd(r['gain_usd'])} | {usd(r['hold_gain_usd'])} | {usd(r.get('twin_p80_usd'))} | "
                     f"{r.get('twins_beaten', 'n/a')} of {r['twins_done']} | {r['buys']} | {r['wins']} | {r['losses']} | {usd(r['fees_usd'])} | {r['max_drop'] * 100:.1f}% | {r['wakes_no_pick']} of {r['wakes']} | {r['lookups']} |")
    L += ["", "## Why each trade was made, and how it ended", "",
          "One row per buy. \"Looked at\" is what the trader asked the desk for at that wake, beyond the packet it is always given. No trader in this plan had news, so none looked at news.", ""]
    for mo, mname in MONTHS:
        for tag, _ in MODELS:
            r = o["models"][tag]["months"][mo]
            if not r["finished"] or not r["why"]:
                continue
            L += [f"### {mname}, {o['models'][tag]['name']}", "", "| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |", "|---|---|---|---|---|---|"]
            for w in r["why"]:
                looked = ", ".join(f"{k} bars x{v}" if k not in ("news", "price") else f"{k} x{v}" for k, v in sorted(w["looked"].items())) or "packet only"
                why = (w["reason"] or "").replace("|", "/").replace("\n", " ")
                end = ("stop reached" if "stop" in (w["exit_reason"] or "") else "target reached" if "target" in (w["exit_reason"] or "") else "time limit" if "by_utc" in (w["exit_reason"] or "") or "time" in (w["exit_reason"] or "") else "sold by the trader") if w["closed_utc"] else "open at the end"
                res = f"{w['result']} {usd(w['gain_usd'])} ({w['gain_pct'] * 100:+.1f}%)" if w["gain_usd"] is not None else w["result"]
                L.append(f"| {w['wake_utc'][:16].replace('T', ' ')} | {w['symbol']} | {looked} | {why} | {end}{' ' + w['closed_utc'][:16].replace('T', ' ') if w['closed_utc'] else ''} | {res} |")
            L.append("")
    L += ["## What this does not show", "",
          "- Fills are assumed, not real. Many crypto minutes on the tape are thin, so real fills could be worse.",
          "- The rule against outside knowledge is given by instruction. Each trader's lookups are logged; its memory is not.",
          "- Whether these months fall after each model's knowledge line is UNKNOWN. It has not been measured.",
          "- October was the shakedown month. Its three known differences are listed at the end of the plan.",
          "- With six models, one looking good by luck is likely. That is why the bar is per model and was fixed before the run.", ""]
    return "\n".join(L)


def main():
    o = build(); js = json.dumps(o, indent=1, sort_keys=True) + "\n"; md = doc(o)
    if "--check" in sys.argv:
        bad = [str(p.relative_to(ROOT)) for p, t in ((OUT, js), (DOC, md)) if not p.exists() or p.read_text() != t]
        print("stale: " + ", ".join(bad) if bad else "ok"); sys.exit(1 if bad else 0)
    OUT.write_text(js); DOC.write_text(md)
    for tag, _ in MODELS:
        m = o["models"][tag]; print(tag, m["months_counted"], m.get("sum_gain_usd"), m.get("sum_hold_usd"), m.get("sum_twin_p80_usd"), m["verdict"])


if __name__ == "__main__":
    main()
