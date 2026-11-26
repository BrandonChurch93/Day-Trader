"""Plan 23 fetcher. Before the lock it may read bar dates, volume and the flat-run flag, never a return.

  python3 fetch_23.py --events   pick the events from ipos.csv and breakpoints.csv, and check from each kept 424B4's
                                 cover that it offers common shares or ADS (prospectus only, no bar)
  (--fetch and --freeze also need --approval-commit <the lead's approval commit>; see common_23.authorize)
  python3 fetch_23.py --fetch    collect raw SIP daily bars for each event and for SPY into RUN/bars/ (resumes)
  python3 fetch_23.py --freeze   from bar dates, volume and the flat flag: first trading day, leave-outs (including a
                                 first bar that is not a real trade), count once, the exit-window refusal; writes
                                 events_frozen.csv and freeze.json, prints the freeze SHA-256

The credential is used only through `pplx credentials run`; it is never read, printed or stored here. Bars stay in
RUN (off repo). Output is counts, dates and accessions only, never a price. One process, one request at a time.
"""
import argparse, csv, datetime as dt, json, os, subprocess, sys, time

import common_23 as C

HERE = C.HERE
SRC = os.path.expanduser("~/workspace/rig/data/ipo_fasttrack")
RUN = os.environ.get("P23_RUN", os.path.expanduser("~/workspace/rig/data/replay_23"))
CRED = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
PLAN = os.environ.get("P23_PLAN", C.PLAN_NAME)
CODE = ("common_23.py", "fetch_23.py", "score_23.py", "test_23.py", "calibrate_23.py", "report_23.py",
        os.path.relpath(C.CONFIG, HERE), PLAN)


def paths(run=None, src=None):
    RUN_, SRC_ = run or RUN, src or SRC
    return dict(ipos=os.path.join(SRC_, "ipos.csv"), bps=os.path.join(SRC_, "breakpoints.csv"),
                snips=os.path.join(SRC_, "src", "snips.jsonl.gz"),
                selected=os.path.join(RUN_, "events_selected.csv"), shares=os.path.join(RUN_, "shares_check_23.csv"), frozen=os.path.join(RUN_, "events_frozen.csv"),
                freeze=os.path.join(RUN_, "freeze.json"), bars=os.path.join(RUN_, "bars"), run=RUN_)


def by_year(rows, key="pricing_date"):
    out = {}
    for r in rows:
        k = (r[key][:4], r["group"])
        out[k] = out.get(k, 0) + 1
    return out


def print_counts(rows, title, key="pricing_date"):
    groups = ("judged", "band_1_0_to_1_5", "near_0_67_to_1_0")
    c = by_year(rows, key)
    years = sorted({y for y, _ in c})
    print(title)
    print("year " + " ".join(groups))
    for y in years:
        print(y, " ".join(str(c.get((y, g), 0)) for g in groups))
    print("total", " ".join(str(sum(v for (y, g), v in c.items() if g == gg)) for gg in groups))


def cmd_events(p):
    P = paths()
    ipos, bps = C.read_csv(P["ipos"]), C.read_breakpoints(P["bps"])
    sec = C.security_map(P["snips"], {e["accession"] for e in C.select_events(ipos, bps, p)})
    ev = C.select_events(ipos, bps, p, security=sec)
    by_acc = {r["accession"]: r for r in ipos}
    os.makedirs(RUN, exist_ok=True)
    with open(P["shares"], "w", newline="", encoding="utf-8") as fh:     # the share-total check, one row per event
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["accession", "ticker", "company", "pricing_date", "group", "shares_after", "classes", "check", "quote"])
        for e in ev:
            r = by_acc[e["accession"]]
            w.writerow([e["accession"], e["ticker"], e["company"], e["pricing_date"], e["group"], r.get("shares_out_after", ""),
                        r.get("shares_out_after_classes", ""), r.get("shares_check", ""), r.get("shares_quote", "")])
    with open(P["selected"], "wb") as fh:
        fh.write(C.events_csv_bytes(ev))
    print_counts(ev, "selected events by pricing year (prospectus only)")
    for e in ev:
        if e["status"] == "not_common_security":
            print("not common shares or ADS, left out:", e["accession"], e["company"], e["pricing_date"], e["group"])
        elif e["status"] == "shares_unverified":
            print("share total not read with confidence, left out:", e["accession"], e["company"], e["pricing_date"],
                  e["group"], e["shares_check"])
    print("no ticker:", sum(1 for e in ev if not e["ticker"]), " sha256", C.sha256_file(P["selected"]))


def get(url):
    for attempt in range(6):
        r = subprocess.run(["pplx", "credentials", "run", CRED, "--", "curl", "-s", "--max-time", "120", url],
                           capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            if "bars" in d:
                return d
            msg = str(d.get("message", ""))[:120]
        except Exception:
            msg = "unreadable reply"
        print("retry", attempt, msg, flush=True)
        time.sleep(5 * (attempt + 1))
    raise SystemExit("P23_FEED_FAILED")


def bars(symbol, start, end, asof, p):
    out, token = [], None
    while True:
        url = (f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbol}&timeframe=1Day&start={start}&end={end}"
               f"&adjustment={p['bar_adjustment']}&feed={p['bar_feed']}&limit=10000"
               + (f"&asof={asof}" if asof else "") + (f"&page_token={token}" if token else ""))
        d = get(url)
        out.extend((d.get("bars") or {}).get(symbol, []))
        token = d.get("next_page_token")
        time.sleep(0.35)
        if not token:
            return out


def put(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(rows, fh, separators=(",", ":"))
    os.replace(tmp, path)


def cmd_fetch(p):
    P = paths()
    os.makedirs(P["bars"], exist_ok=True)
    ev = C.parse_events(open(P["selected"], "rb").read())
    end_cap = str(p["bar_end"])
    spy = os.path.join(P["bars"], "SPY.json")
    if not os.path.exists(spy):
        put(spy, bars("SPY", str(p["spy_start"]), end_cap, None, p))
    n = 0
    for e in ev:
        f = os.path.join(P["bars"], e["accession"] + ".json")
        if os.path.exists(f) or not e["ticker"] or e["status"]:
            continue
        d0 = dt.date.fromisoformat(e["filing_date"])       # one rule for every event: windows key on the filing date
        start = (d0 - dt.timedelta(days=p["prior_listing_days"])).isoformat()
        end = min((d0 + dt.timedelta(days=p["fetch_after_days"])).isoformat(), end_cap)
        asof = (d0 + dt.timedelta(days=p["asof_days"])).isoformat()   # inside the first-bar window, so the listing's own ticker
        put(f, bars(e["ticker"], start, end, asof, p))
        n += 1
        if n % 50 == 0:
            print("fetched", n, flush=True)
    print("fetched", n, "files; dates, volume and the flat flag only from here")


def repo_ready():
    """The freeze is for the repo copy only: the config must be the repo's thresholds.yaml and the plan must not be
    the draft (audit pass 1, S3). P23_ALLOW_DRAFT=1 lets the tests freeze inside a temporary folder."""
    if os.environ.get("P23_ALLOW_DRAFT") == "1":
        return
    plan = [f for f in CODE if os.path.basename(f).startswith("PREREG_23")]
    if os.path.basename(C.CONFIG) != "thresholds.yaml" or not plan or any("DRAFT" in os.path.basename(f) for f in plan):
        raise SystemExit("P23_FREEZE_ON_DRAFT config=" + C.CONFIG + " plan=" + ",".join(plan))


def cmd_freeze(p):
    repo_ready()
    P = paths()
    ev = C.parse_events(open(P["selected"], "rb").read())
    sessions = C.dates_from_json(open(os.path.join(P["bars"], "SPY.json"), "rb").read())
    dates = {}
    for e in ev:
        f = os.path.join(P["bars"], e["accession"] + ".json")
        if os.path.exists(f):
            dates[e["accession"]] = C.real_dates_from_json(open(f, "rb").read(), p["flat_run"], p["bar_end"])
    out = C.resolve_dates(ev, dates, sessions, p)
    raw = C.events_csv_bytes(out)
    with open(P["frozen"], "wb") as fh:
        fh.write(raw)
    st = {}
    for e in out:
        st[(e["group"], e["status"])] = st.get((e["group"], e["status"]), 0) + 1
    for k in sorted(st):
        print(*k, st[k])
    for e in out:
        if e["status"] in ("entry_not_real_bar", "not_common_security", "shares_unverified", "late_first_bar",
                           "prior_bars", "bars_before_window", "no_bar"):
            print("left out:", e["status"], e["accession"], e["company"], e["group"])
    refused = [e["accession"] for e in out if e["status"] == "refused_no_exit_bar"]
    if refused:
        raise SystemExit("P23_REFUSED_NO_EXIT_BAR " + " ".join(refused))
    ok = [e for e in out if e["status"] == "ok"]
    print_counts(ok, "events kept after the date checks, by first trading year", key="first_trade_date")
    bar_files = {e["accession"]: C.sha256_file(os.path.join(P["bars"], e["accession"] + ".json")) for e in ok}
    bar_files["SPY"] = C.sha256_file(os.path.join(P["bars"], "SPY.json"))
    rec = dict(made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               events_frozen_sha256=C.sha256_bytes(raw), events_selected_sha256=C.sha256_file(P["selected"]),
               ipos_sha256=C.sha256_file(P["ipos"]), breakpoints_sha256=C.sha256_file(P["bps"]),
               snips_sha256=C.sha256_file(P["snips"]),
               code_sha256={f: C.sha256_file(os.path.join(HERE, f)) for f in CODE}, bars_sha256=bar_files)
    body = json.dumps(rec, sort_keys=True, indent=1).encode()
    if os.path.exists(P["freeze"]):
        raise SystemExit("P23_FREEZE_EXISTS")
    with open(P["freeze"], "wb") as fh:
        fh.write(body)
    print("freeze sha256", C.sha256_bytes(body))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--events", action="store_true")
    g.add_argument("--fetch", action="store_true")
    g.add_argument("--freeze", action="store_true")
    ap.add_argument("--approval-commit", help="the lead's approval commit; needed for --fetch and --freeze")
    a = ap.parse_args()
    p = C.load_config()
    try:
        if not a.events:
            C.authorize(a.approval_commit)
        (cmd_events if a.events else cmd_fetch if a.fetch else cmd_freeze)(p)
    except C.Refused as exc:
        raise SystemExit(str(exc))
