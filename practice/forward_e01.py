"""E01 forward log (queue row 46, card practice/traders/E01_tlt_month_end_close.md): Replay 25's TLT month-end window,
recorded each month from December 2026 from public market data. No broker account and no order.

  python3 practice/forward_e01.py plan
      the pinned entry and exit sessions. No network.
  pplx credentials run <data handle> -- python3 practice/forward_e01.py record 2026-12
      after the exit close (at least 20 minutes) and before the next month starts in New York. Reads the month's
      SIP daily bars, the trades around both closes and TLT's cash distributions from data.alpaca.markets, then
      writes the full record off repo and one line of figures, with no prices, to practice/forward/E01_log.json.

The rule is Replay 25's, unchanged (research_rig/PREREG_25_treasury_month_end.md, ledger 162): buy at the SIP daily
close of the fourth-last session of the month, sell at the SIP daily close of the last, add cash distributions with
an ex-date on the three sessions after entry, charge 2 bps on each side. A month counts as forward evidence only if
its record is written before the next month starts in New York. Standard library only. Reads only; it sends nothing.
"""
import argparse, json, os, re, subprocess, sys
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
LOG = HERE / "forward" / "E01_log.json"
OFF_REPO = Path(os.environ.get("E01_RECORD_DIR", "/home/user/workspace/rig/data/forward_e01"))
HANDLE = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
DATA = "https://data.alpaca.markets"
READS = (r"/v2/stocks/TLT/bars", r"/v2/stocks/TLT/trades", r"/v1/corporate-actions")
NY, UTC = ZoneInfo("America/New_York"), timezone.utc
COST_BPS = 2.0
CROSS_VENUES = ("Q", "T")  # Alpaca labels the Nasdaq cross Q on recent sessions and T on older ones (doc 70)
# Month: (entry, the three held sessions ending at the exit). XNYS, exchange-calendars 4.13.3, the version pinned for
# Replay 25, made 2026-11-26. All 26 sessions close at 16:00 New York. A month whose bars disagree is refused.
SESSIONS = {
    "2026-12": ("2026-12-28", ("2026-12-29", "2026-12-30", "2026-12-31")),
    "2027-01": ("2027-01-26", ("2027-01-27", "2027-01-28", "2027-01-29")),
    "2027-02": ("2027-02-23", ("2027-02-24", "2027-02-25", "2027-02-26")),
    "2027-03": ("2027-03-25", ("2027-03-29", "2027-03-30", "2027-03-31")),
    "2027-04": ("2027-04-27", ("2027-04-28", "2027-04-29", "2027-04-30")),
    "2027-05": ("2027-05-25", ("2027-05-26", "2027-05-27", "2027-05-28")),
    "2027-06": ("2027-06-25", ("2027-06-28", "2027-06-29", "2027-06-30")),
    "2027-07": ("2027-07-27", ("2027-07-28", "2027-07-29", "2027-07-30")),
    "2027-08": ("2027-08-26", ("2027-08-27", "2027-08-30", "2027-08-31")),
    "2027-09": ("2027-09-27", ("2027-09-28", "2027-09-29", "2027-09-30")),
    "2027-10": ("2027-10-26", ("2027-10-27", "2027-10-28", "2027-10-29")),
    "2027-11": ("2027-11-24", ("2027-11-26", "2027-11-29", "2027-11-30")),
    "2027-12": ("2027-12-28", ("2027-12-29", "2027-12-30", "2027-12-31")),
}


class Refuse(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refuse(why)


def curl_get(path, params):
    need(any(re.fullmatch(p, path) for p in READS), f"not on the read list: {path}")
    url = DATA + path + "?" + urlencode(params)
    cmd = ["pplx", "credentials", "run", HANDLE, "--", "curl", "--silent", "--fail", "--proto", "=https", "--max-time", "90", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=120)
    need(r.returncode == 0 and len(r.stdout) <= 8 * 1024 * 1024, "the data read failed")
    return json.loads(r.stdout)


def close_utc(day):
    return datetime.combine(date.fromisoformat(day), time(16), NY).astimezone(UTC)


def stamp(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def paged(get, path, params, key):
    out, seen, q = [], set(), dict(params)
    for _ in range(20):
        page = get(path, q) or {}
        part = page.get(key)
        if isinstance(part, dict):  # bars and corporate actions are keyed by symbol or type
            part = [x for v in part.values() for x in v]
        out.extend(part or [])
        tok = page.get("next_page_token")
        if not tok:
            return out
        need(tok not in seen, "a data page repeated"); seen.add(tok); q["page_token"] = tok
    raise Refuse("too many data pages")


def ny_session(bar_t):
    t = datetime.fromisoformat(bar_t.replace("Z", "+00:00")).astimezone(NY)
    need((t.hour, t.minute) == (0, 0), "a daily bar is not stamped at New York midnight")
    return t.date().isoformat()


def cross(trades):
    c = [t for t in trades if t.get("x") in CROSS_VENUES and "6" in (t.get("c") or [])]
    c = sorted(c, key=lambda t: (-t["s"], t["t"]))[0] if c else None
    m = next((t for t in trades if t.get("x") in CROSS_VENUES and "M" in (t.get("c") or [])), None)
    return c, m


def record(month, get=curl_get, now=None):
    need(month in SESSIONS, f"{month} is not in the pinned session table")
    now = now or datetime.now(UTC)
    entry, held = SESSIONS[month]; exit_ = held[-1]
    need(now >= close_utc(exit_) + timedelta(minutes=20), "wait until at least 20 minutes after the exit close")
    y, m = map(int, month.split("-"))
    first = date(y, m, 1); nxt = date(y + (m == 12), m % 12 + 1, 1)
    bars = paged(get, "/v2/stocks/TLT/bars", dict(timeframe="1Day", start=first.isoformat(), end=(nxt - timedelta(days=1)).isoformat(),
                                                   feed="sip", adjustment="raw", limit=1000, sort="asc"), "bars")
    by_day = {ny_session(b["t"]): b for b in bars}
    days = sorted(by_day)
    need(len(days) >= 4 and days[-4] == entry and tuple(days[-3:]) == held,
         f"the month's SIP bars do not match the pinned sessions (bars end {days[-4:] if days else 'none'})")
    closes = {d: float(by_day[d]["c"]) for d in (entry, exit_)}
    need(all(v > 0 for v in closes.values()) and all(by_day[d]["v"] > 0 for d in (entry, exit_)), "a close or volume is not positive")
    legs = {}
    for side, d in (("entry", entry), ("exit", exit_)):
        cu = close_utc(d)
        tr = paged(get, "/v2/stocks/TLT/trades", dict(start=stamp(cu - timedelta(seconds=1)), end=stamp(cu + timedelta(seconds=300)),
                                                      feed="sip", limit=10000, sort="asc"), "trades")
        c, o = cross(tr)
        g = (c["p"] / closes[d] - 1) * 1e4 if c else None
        legs[side] = dict(session=d, sip_close=closes[d], cross_price=c["p"] if c else None, cross_size=c["s"] if c else None,
                          cross_venue=c["x"] if c else None, cross_time=c["t"] if c else None, official_close=o["p"] if o else None,
                          signed_cost_bps=None if g is None else (g if side == "entry" else -g) + 0.0)
    acts = paged(get, "/v1/corporate-actions", dict(symbols="TLT", types="cash_dividend", start=entry, end=exit_, limit=1000),
                 "corporate_actions")
    paid = [dict(ex_date=a["ex_date"], rate=float(a["rate"]), id=a.get("id")) for a in acts
            if a.get("symbol") == "TLT" and a.get("ex_date") in held]
    div = sum(a["rate"] for a in paid)
    f = COST_BPS / 1e4
    net = (closes[exit_] * (1 - f) + div) / (closes[entry] * (1 + f)) - 1
    at_cross = None
    if legs["entry"]["cross_price"] and legs["exit"]["cross_price"]:
        at_cross = (legs["exit"]["cross_price"] * (1 - f) + div) / (legs["entry"]["cross_price"] * (1 + f)) - 1
    on_time = now < datetime.combine(nxt, time(0), NY).astimezone(UTC)
    full = dict(month=month, made_utc=stamp(now), on_time=on_time, entry=legs["entry"], exit=legs["exit"],
                distributions=paid, distribution_per_share=div, cost_bps_per_side=COST_BPS,
                net_return=net, net_return_at_cross=at_cross)
    blob = (json.dumps(full, indent=1, sort_keys=True) + "\n").encode()
    line = dict(month=month, made_utc=full["made_utc"], counted=on_time, entry_session=entry, exit_session=exit_,
                net_return_pct=round(net * 100, 4), net_return_at_cross_pct=None if at_cross is None else round(at_cross * 100, 4),
                distribution_per_share=round(div, 6), distribution_ex_dates=[a["ex_date"] for a in paid],
                entry_cross_cost_bps=None if legs["entry"]["signed_cost_bps"] is None else round(legs["entry"]["signed_cost_bps"], 3),
                exit_cross_cost_bps=None if legs["exit"]["signed_cost_bps"] is None else round(legs["exit"]["signed_cost_bps"], 3),
                entry_cross_shares=legs["entry"]["cross_size"], exit_cross_shares=legs["exit"]["cross_size"],
                record_sha256=sha256(blob).hexdigest())
    return full, blob, line


def save(month, blob, line, log=LOG, off=OFF_REPO):
    cur = json.loads(log.read_text()) if log.exists() else dict(card="practice/traders/E01_tlt_month_end_close.md", months={})
    need(month not in cur["months"], f"{month} is already in the log; one record per month")
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    p = off / f"{month}.json"
    need(not p.exists(), f"{p.name} already exists off repo")
    p.write_bytes(blob); os.chmod(p, 0o600)
    cur["months"][month] = line
    cur["months"] = dict(sorted(cur["months"].items()))
    log.parent.mkdir(exist_ok=True)
    log.write_text(json.dumps(cur, indent=1, sort_keys=True) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["plan", "record"]); ap.add_argument("month", nargs="?")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "plan":
            for k, (e, h) in SESSIONS.items():
                print(k, "buy at the close of", e, "sell at the close of", h[-1])
            return 0
        need(a.month, "say which month, as YYYY-MM")
        full, blob, line = record(a.month)
        save(a.month, blob, line)
        print(json.dumps(line, indent=1, sort_keys=True)); return 0
    except Refuse as e:
        print("Refused, nothing written:", e); return 2


if __name__ == "__main__":
    sys.exit(main())
