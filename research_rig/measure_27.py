"""Measurement 27 (queue row 47, ledger row 164): the Nasdaq closing cross against the SIP daily close on the
130 entry and 130 exit sessions of Replay 25. A fill measurement. No window return is computed.

Plan, frozen before any trade was collected: research_rig/MEASURE_27_tlt_closing_cross.md

  python3 measure_27.py --validate-inputs
      checks the sessions and the Replay 25 input closes. No network. Prints counts only, no prices.
  python3 measure_27.py --run
      once only. Reads SIP trades around each scheduled close through the owner's saved data credential and
      writes the per-session output off repo (trades are vendor data and stay there).
  python3 measure_27.py --report
      writes measure_27_summary.json (aggregates only) and docs/research/70_measure_27_tlt_closing_cross.md
      from the off-repo result file. No network.
Standard library only.
"""
import argparse, json, os, subprocess, sys
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from statistics import fmean, median
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import common_25 as C

HERE = Path(__file__).resolve().parent
INPUTS = Path("/home/user/workspace/rig/data/replay_25/inputs")
OUT = Path("/home/user/workspace/rig/data/measure_27")
MANIFEST_SHA = "43f92b5249c8a2aa8778139f928cf643814e47b778d5892a903227830777aa9a"
HANDLE = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
API = "https://data.alpaca.markets/v2/stocks/TLT/trades"
SUMMARY = HERE / "measure_27_summary.json"
DOC = HERE.parent / "docs" / "research" / "70_measure_27_tlt_closing_cross.md"
PLAN = "research_rig/MEASURE_27_tlt_closing_cross.md"
NY, UTC = ZoneInfo("America/New_York"), timezone.utc
LAST_SESSION = date(2026, 10, 30)
BEFORE_S, AFTER_S = 1, 300
# XNYS early closes (13:00 New York) from 2016-01-04 to 2026-11-24, exchange-calendars 4.13.3, the version pinned in
# calendar_25.json. Made once with that version; listed here so this file needs no third-party package.
EARLY = frozenset(date.fromisoformat(d) for d in (
    "2016-11-25", "2017-07-03", "2017-11-24", "2018-07-03", "2018-11-23", "2018-12-24", "2019-07-03", "2019-11-29",
    "2019-12-24", "2020-11-27", "2020-12-24", "2021-11-26", "2022-11-25", "2023-07-03", "2023-11-24", "2024-07-03",
    "2024-11-29", "2024-12-24", "2025-07-03", "2025-11-28", "2025-12-24"))
MARK_FOUND, MARK_MEAN, MARK_P95 = 0.95, 1.0, 3.0


def need(ok, code):
    if not ok:
        raise C.Refused(code)


def sessions():
    days = C.check_calendar(json.loads((HERE / "calendar_25.json").read_text()))
    out = []
    for buy, sell, _ in C.windows(days, 3):
        for d, side in ((buy, "entry"), (sell, "exit")):
            close_ny = datetime.combine(d, time(13 if d in EARLY else 16), NY)
            out.append(dict(session=d.isoformat(), side=side, early=d in EARLY, close_utc=close_ny.astimezone(UTC)))
    need(len(out) == 260 and sum(r["side"] == "entry" for r in out) == 130, "M27_SESSIONS")
    need(max(date.fromisoformat(r["session"]) for r in out) == LAST_SESSION, "M27_SESSIONS")
    need(len({r["session"] for r in out}) == 260, "M27_SESSIONS")
    return days, out


def closes(days):
    raw = (INPUTS / "manifest.json").read_bytes()
    need(sha256(raw).hexdigest() == MANIFEST_SHA, "M27_MANIFEST")
    files = json.loads(raw)["files"]
    tlt = (INPUTS / "TLT.json").read_bytes()
    need(sha256(tlt).hexdigest() == files["TLT.json"], "M27_TLT_FILE")
    rows = json.loads(tlt)
    C.check_bar_clocks(rows, days)
    return {d.isoformat(): b.c for d, b in C.price_tape(rows, days).items()}


def validate():
    days, rows = sessions()
    c = closes(days)
    need(all(r["session"] in c for r in rows), "M27_CLOSE_MISSING")
    early = [r for r in rows if r["early"]]
    print("M27_INPUTS_OK sessions", len(rows), "entry", sum(r["side"] == "entry" for r in rows),
          "exit", sum(r["side"] == "exit" for r in rows), "early_close", len(early),
          "first", rows[0]["session"], "last", rows[-1]["session"], "closes_found", sum(r["session"] in c for r in rows))
    for r in early:
        print("  early close", r["session"], r["side"])
    return days, rows, c


def get(url):
    cmd = ["pplx", "credentials", "run", HANDLE, "--", "curl", "--silent", "--fail", "--proto", "=https",
           "--max-time", "90", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=120)
    need(r.returncode == 0 and len(r.stdout) <= 8 * 1024 * 1024, "M27_ALPACA")
    return json.loads(r.stdout)


def trades(close_utc, transport=get):
    stamp = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    q = dict(start=stamp(close_utc - timedelta(seconds=BEFORE_S)), end=stamp(close_utc + timedelta(seconds=AFTER_S)),
             feed="sip", limit=10000, sort="asc")
    out, seen = [], set()
    for _ in range(20):
        page = transport(API + "?" + urlencode(q))
        out.extend(page.get("trades") or [])
        tok = page.get("next_page_token")
        if not tok:
            return out
        need(tok not in seen, "M27_PAGE"); seen.add(tok); q["page_token"] = tok
    raise C.Refused("M27_PAGE")


def pick(tr, venues=("Q",)):
    cross = [t for t in tr if t.get("x") in venues and "6" in (t.get("c") or [])]
    cross = sorted(cross, key=lambda t: (-t["s"], t["t"]))[0] if cross else None
    offc = next((t for t in tr if t.get("x") == "Q" and "M" in (t.get("c") or [])), None)
    return cross, offc


def measure_row(r, close, tr, venues=("Q",)):
    cross, offc = pick(tr, venues)
    row = dict(session=r["session"], side=r["side"], early=r["early"], close_utc=r["close_utc"].isoformat(),
               sip_close=close, trades_in_window=len(tr), found=cross is not None,
               cross_price=cross["p"] if cross else None, cross_size=cross["s"] if cross else None,
               cross_time=cross["t"] if cross else None, official_close=offc["p"] if offc else None)
    if cross:
        g = cross["p"] / close - 1
        row["signed_bps"] = g * 1e4 if r["side"] == "entry" else -g * 1e4
        row["abs_bps"] = abs(g) * 1e4
    return row


def run():
    days, rows, c = validate()
    OUT.mkdir(mode=0o700, exist_ok=True)
    res = OUT / "results_27.json"
    need(not res.exists() and not (OUT / "run_27.lock").exists(), "M27_ALREADY_RUN")
    (OUT / "run_27.lock").write_text(datetime.now(UTC).isoformat() + "\n")
    (OUT / "trades").mkdir(mode=0o700, exist_ok=True)
    out = []
    for r in rows:
        tr = trades(r["close_utc"])
        (OUT / "trades" / f"{r['session']}.json").write_text(json.dumps(tr, sort_keys=True) + "\n")
        out.append(measure_row(r, c[r["session"]], tr))
    blob = dict(made_utc=datetime.now(UTC).isoformat(), plan=PLAN, manifest_sha256=MANIFEST_SHA,
                window_seconds=[-BEFORE_S, AFTER_S], rows=out)
    res.write_text(json.dumps(blob, indent=1, sort_keys=True) + "\n")
    os.chmod(res, 0o600)
    print("M27_RUN_DONE rows", len(out), "found", sum(x["found"] for x in out))


def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p; lo = int(k); hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def stats(xs):
    return dict(n=len(xs), mean=fmean(xs) if xs else None, median=median(xs) if xs else None, p95=pct(xs, 0.95),
                min=min(xs) if xs else None, max=max(xs) if xs else None)


def summarize(blob, raw):
    rows = blob["rows"]; f = [r for r in rows if r["found"]]
    side = {s: [r["signed_bps"] for r in f if r["side"] == s] for s in ("entry", "exit")}
    absg = [r["abs_bps"] for r in f]
    sizes = [r["cross_size"] for r in f]
    years = sorted({r["session"][:4] for r in rows})
    m_rows = [r for r in f if r["official_close"] is not None]
    marks = dict(
        found=dict(value=len(f) / len(rows), count=len(f), of=len(rows), limit=MARK_FOUND, ok=len(f) / len(rows) >= MARK_FOUND),
        mean_entry=dict(value=fmean(side["entry"]) if side["entry"] else None, limit=MARK_MEAN),
        mean_exit=dict(value=fmean(side["exit"]) if side["exit"] else None, limit=MARK_MEAN),
        p95_abs=dict(value=pct(absg, 0.95), limit=MARK_P95))
    for k in ("mean_entry", "mean_exit", "p95_abs"):
        v = marks[k]["value"]; marks[k]["ok"] = v is not None and v <= marks[k]["limit"]
    return dict(
        source_sha256=sha256(raw).hexdigest(), source_made_utc=blob["made_utc"], plan=PLAN, ledger_row=164, queue_row=47,
        window_seconds=blob["window_seconds"], sessions=len(rows), found=len(f),
        not_found=[dict(session=r["session"], side=r["side"], trades_in_window=r["trades_in_window"]) for r in rows if not r["found"]],
        marks=marks, all_marks_ok=all(m["ok"] for m in marks.values()),
        signed_bps=dict(entry=stats(side["entry"]), exit=stats(side["exit"]), pooled=stats(side["entry"] + side["exit"])),
        abs_bps=stats(absg),
        cross_equals_sip_close=sum(r["cross_price"] == r["sip_close"] for r in f),
        official_close_found=len(m_rows), official_equals_cross=sum(r["official_close"] == r["cross_price"] for r in m_rows),
        cross_size_shares=dict(median=median(sizes) if sizes else None, p5=pct(sizes, 0.05), min=min(sizes) if sizes else None),
        by_year={y: dict(signed=stats([r["signed_bps"] for r in f if r["session"][:4] == y]),
                         abs_p95=pct([r["abs_bps"] for r in f if r["session"][:4] == y], 0.95),
                         sessions=sum(r["session"][:4] == y for r in rows)) for y in years},
        early_close=[dict(session=r["session"], side=r["side"], found=r["found"], signed_bps=r.get("signed_bps")) for r in rows if r["early"]],
    )


def n(x, d=2):
    if isinstance(x, float) and x == 0:
        x = 0.0  # no minus sign on a zero
    return "n/a" if x is None else f"{x:,.{d}f}".replace("-", "−") if isinstance(x, float) else f"{x:,}"


def doc(S):
    m = S["marks"]; ok = lambda b: "met" if b else "not met"
    L = [
        "# 70. Measurement 27: closing cross against the consolidated close on TLT month-end sessions", "",
        f"Written by `research_rig/measure_27.py --report` from `research_rig/measure_27_summary.json`, which was made from the off-repo per-session result of {S['source_made_utc'][:16].replace('T', ' ')} UTC (sha256 {S['source_sha256'][:16]}). "
        f"Plan: `{S['plan']}`, ledger row 164, queue row 47. A fill measurement. No window return was computed.", "",
        "## Result", "",
        "- " + ("MEASURED: all three marks are met. The replay's 2 bps a side is fair for a market-on-close order of ordinary size."
                if S["all_marks_ok"] else
                "MEASURED: mark 1 is not met, so by the frozen rule the replay's 2 bps a side is not supported by the closing cross as measured. "
                "Marks 2 and 3 are met on the sessions where the cross was found. The miss is one of labels, not prices: see the section written after the run."
                if not m["found"]["ok"] and all(m[k]["ok"] for k in ("mean_entry", "mean_exit", "p95_abs")) else
                "MEASURED: at least one mark is not met. The replay's 2 bps a side is not supported by the closing cross as measured."),
        f"- Mark 1, cross print found: {S['found']} of {S['sessions']} sessions ({n(100 * m['found']['value'], 1)}%), limit 95%: {ok(m['found']['ok'])}.",
        f"- Mark 2, mean signed cost per side: entry {n(m['mean_entry']['value'], 3)} bps, exit {n(m['mean_exit']['value'], 3)} bps, limit 1.0 bp each: {ok(m['mean_entry']['ok'] and m['mean_exit']['ok'])}.",
        f"- Mark 3, 95th percentile of the absolute gap: {n(m['p95_abs']['value'], 3)} bps, limit 3 bps: {ok(m['p95_abs']['ok'])}.",
        f"- The cross price equalled the SIP daily close on {S['cross_equals_sip_close']} of {S['found']} found sessions. The Nasdaq official close print (condition M) was found on {S['official_close_found']} and equalled the cross price on {S['official_equals_cross']}.",
        f"- Cross size: median {n(S['cross_size_shares']['median'], 0)} shares, 5th percentile {n(S['cross_size_shares']['p5'], 0)}, smallest {n(S['cross_size_shares']['min'], 0)}.", "",
        "## Signed cost by side", "",
        "MEASURED. Basis points against the SIP daily close the replay used. Positive is a cost: a buy at the cross above the close, or a sell below it. Percentiles use linear interpolation.", "",
        "| side | n | mean | median | p95 | min | max |", "|---|---|---|---|---|---|---|",
    ]
    for k in ("entry", "exit", "pooled"):
        s = S["signed_bps"][k]
        L.append(f"| {k} | {s['n']} | {n(s['mean'], 3)} | {n(s['median'], 3)} | {n(s['p95'], 3)} | {n(s['min'], 3)} | {n(s['max'], 3)} |")
    a = S["abs_bps"]
    L += ["", f"Absolute gap, all found sessions: n {a['n']}, mean {n(a['mean'], 3)}, median {n(a['median'], 3)}, p95 {n(a['p95'], 3)}, max {n(a['max'], 3)} bps.", "",
          "## By year", "", "MEASURED. Both sides together.", "",
          "| year | sessions | found | mean signed | median signed | p95 absolute |", "|---|---|---|---|---|---|"]
    for y, v in S["by_year"].items():
        L.append(f"| {y} | {v['sessions']} | {v['signed']['n']} | {n(v['signed']['mean'], 3)} | {n(v['signed']['median'], 3)} | {n(v['abs_p95'], 3)} |")
    L += ["", "## Early-close sessions", "", "MEASURED. Scheduled close 1:00 pm New York.", "", "| session | side | found | signed bps |", "|---|---|---|---|"]
    for r in S["early_close"]:
        L.append(f"| {r['session']} | {r['side']} | {'yes' if r['found'] else 'no'} | {n(r['signed_bps'], 3)} |")
    if S["not_found"]:
        L += ["", "## Sessions with no cross print found", "",
              f"MEASURED: {len(S['not_found'])} sessions, first {S['not_found'][0]['session']}, last {S['not_found'][-1]['session']}. "
              "All are listed in the summary file. The by-year table above shows where they fall."]
    A = S.get("after_run_q_or_t")
    if A:
        am = A["marks"]
        L += ["", "## Written after the run: the cross labelled Q or T", "",
              "Not a mark and not part of the frozen result. Looking at the sessions with no Q cross print showed why: on all sessions before April 2021 and on some in 2021 to 2023, Alpaca's historical tape labels the Nasdaq closing cross as exchange T (NASDAQ Int), not Q (NASDAQ OMX). It is the same print, with conditions 6 and X, a very large size, at 4:00 pm. This view takes the largest condition-6 print on Q or T, with nothing else changed.", "",
              f"- Found: {A['found']} of {A['sessions']} sessions ({n(100 * am['found']['value'], 1)}%).",
              f"- Mean signed cost: entry {n(am['mean_entry']['value'], 3)} bps, exit {n(am['mean_exit']['value'], 3)} bps. 95th percentile of the absolute gap: {n(am['p95_abs']['value'], 3)} bps.",
              f"- The cross price equalled the SIP daily close on {A['cross_equals_sip_close']} of {A['found']} sessions. Largest single gap: {n(A['abs_bps']['max'], 3)} bps.",
              f"- Cross size: median {n(A['cross_size_shares']['median'], 0)} shares, 5th percentile {n(A['cross_size_shares']['p5'], 0)}, smallest {n(A['cross_size_shares']['min'], 0)}.",
              "- Not found: " + (", ".join(f"{r['session']} {r['side']}" for r in A["not_found"]) or "none") + ". On those two sessions the only condition-6 prints are large ones on NYSE Arca (P), which suggests TLT was still listed there in January 2016. The date of the move is not checked here.", "",
              "| side | n | mean | median | p95 | min | max |", "|---|---|---|---|---|---|---|"]
        for k in ("entry", "exit", "pooled"):
            s_ = A["signed_bps"][k]
            L.append(f"| {k} | {s_['n']} | {n(s_['mean'], 3)} | {n(s_['median'], 3)} | {n(s_['p95'], 3)} | {n(s_['min'], 3)} | {n(s_['max'], 3)} |")
        L += ["", "Label of the cross print, by year:", "", "| year and label | sessions |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in A["cross_label_by_year"].items()]
    L += ["", "## Method", "",
          f"- Sessions: the fourth-last and last session of each month January 2016 to October 2026 in `research_rig/calendar_25.json`, by the Replay 25 rule. 260 sessions. The replay's results file was not read.",
          f"- Trades: Alpaca historical trades, SIP feed, TLT, from −{-S['window_seconds'][0]} s to +{S['window_seconds'][1]} s around the scheduled close (4:00 pm, or 1:00 pm on early closes).",
          "- Cross print: the largest trade on exchange Q (Nasdaq) with condition 6 (Closing Prints). Official close: the first Q trade with condition M.",
          "- Consolidated close: the SIP daily bar close in the Replay 25 input file, checked against its manifest.",
          "- Trades and per-session prices stay off repo. This page and the summary carry aggregates only.", "",
          "## Limits", "",
          "- The cross price is what a market-on-close order receives. Commissions and the very small SEC and FINRA sell fees are not counted.",
          "- An order large enough to move the auction would pay more. The cross size above is the guide to what it absorbs.",
          "- This measures the replay's price, not its result. It does not change the Replay 25 verdict.", ""]
    return "\n".join(L)


def after_run_q_or_t(blob):
    """Written after the run, not a mark. Alpaca's historical tape labels the Nasdaq closing cross as exchange T
    (NASDAQ Int) on older sessions and Q (NASDAQ OMX) on later ones. Same sessions, same closes, cross taken from
    Q or T. Shown only; the frozen marks above use Q alone."""
    rows = []
    for r in blob["rows"]:
        tr = json.loads((OUT / "trades" / f"{r['session']}.json").read_text())
        rr = dict(r, close_utc=datetime.fromisoformat(r["close_utc"]))
        rows.append(measure_row(rr, r["sip_close"], tr, venues=("Q", "T")))
    by_label = {}
    for r in blob["rows"]:
        tr = json.loads((OUT / "trades" / f"{r['session']}.json").read_text())
        c, _ = pick(tr, ("Q", "T"))
        k = (r["session"][:4], c["x"] if c else "none"); by_label[k] = by_label.get(k, 0) + 1
    S = summarize(dict(blob, rows=rows), b"")
    S.pop("source_sha256"); S["cross_label_by_year"] = {f"{y} {x}": v for (y, x), v in sorted(by_label.items())}
    return S


def report():
    raw = (OUT / "results_27.json").read_bytes()
    blob = json.loads(raw)
    S = summarize(blob, raw)
    S["after_run_q_or_t"] = after_run_q_or_t(blob)
    SUMMARY.write_text(json.dumps(S, indent=1, sort_keys=True) + "\n")
    DOC.write_text(doc(S))
    print("M27_REPORT", "all_marks_ok", S["all_marks_ok"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--validate-inputs", action="store_true"); g.add_argument("--run", action="store_true")
    g.add_argument("--report", action="store_true")
    a = ap.parse_args()
    os.umask(0o077)
    try:
        validate() if a.validate_inputs else run() if a.run else report()
    except C.Refused as e:
        print("Refused:", e); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
