"""E07 forward watch: ETF closures, the closing SIP quote on the last trading day and the published cash payout, pretend money.

Card: practice/traders/E07_etf_closure_payout_watch.md (the card governs). No orders and no broker. Commands:
  plan            print the pinned clock, stop rule and decision rule (no network)
  add-fund        admit funds from a watch-list CSV (filing fields only, read before any market data); the first call writes
                  the log header with the card and logger SHA-256 and the card's commit
  amend-dates     a later supplement moves the last trading day or the payout date; both filing links are kept
  withdraw        the closure was rescinded or turned into a merger before the last trading day
  record-quote    on a fund's stated last trading day, after the quote window and before New York midnight: read the
                  window's SIP NBBO quotes from data.alpaca.markets through the saved credential and log the summary
  record-payout   the final cash liquidating distribution per share, its payment date and a dated primary source link
  alive           counts only: funds, quotes, payouts, completed. No prices, payouts or ratios
  score           the lead's one read; refuses until the stop rule is met, then appends aggregate percentages

Private records (raw quote pages, quote summaries, per-share payouts) go to /home/user/workspace/rig/data/forward_e07
(0700 folder, 0600 files) as a hash-chained log.jsonl plus packet files. The public log practice/forward/E07_log.json holds
filing links, dates, flags, statuses, packet SHA-256 and the previous entry's hash, and aggregate percentages only at stop.
Standard library only. Reads only; it sends nothing.

  pplx credentials run <data handle> -- python3 practice/forward_e07.py record-quote
"""
import argparse, csv, fcntl, gzip, json, os, re, subprocess, sys
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from statistics import median
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CARD = "practice/traders/E07_etf_closure_payout_watch.md"
ME = "practice/forward_e07.py"
OFF = Path(os.environ.get("E07_RECORD_DIR", "/home/user/workspace/rig/data/forward_e07"))
PUBLIC = ROOT / "practice" / "forward" / "E07_log.json"
HANDLE = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
DATA = "https://data.alpaca.markets"
NY, UTC = ZoneInfo("America/New_York"), timezone.utc

# NYSE calendar, pinned from the NYSE Group 2026, 2027 and 2028 holiday and early closings calendar
# (https://www.nyse.com/trade/hours-calendars, read 2026-11-26). A date outside CAL_FROM..CAL_TO is refused.
CAL_FROM, CAL_TO = date(2026, 11, 2), date(2027, 12, 31)
HOLIDAYS = {date(2026, 11, 26), date(2026, 12, 25), date(2027, 1, 1), date(2027, 1, 18), date(2027, 2, 15), date(2027, 3, 26),
            date(2027, 5, 31), date(2027, 6, 18), date(2027, 7, 5), date(2027, 9, 6), date(2027, 11, 25), date(2027, 12, 24)}
EARLY = {date(2026, 11, 27), date(2026, 12, 24), date(2027, 11, 26)}  # 1:00 p.m. New York close
# Quote clock: 15:54:00 to 15:59:00 New York (12:54:00 to 12:59:00 on an early close), 60-second expiry, at least 180 seconds
# of valid two-sided uncrossed coverage, and the NBBO in force at 15:55:00 (12:55:00) as a cross-check.
WIN_START, WIN_END, SNAP = time(15, 54), time(15, 59), time(15, 55)
EXPIRY_S, MIN_COVER_S = 60, 180
# Stop rule and decision rule (card): 40 completed primary funds or 2027-05-31; grace for payouts through 2027-06-21;
# a payout is primary_missing after 15 business days past the stated payout date.
STOP_COUNT, LAST_ADMIT, GRACE_END, PAYOUT_SESSIONS = 40, date(2027, 5, 31), date(2027, 6, 21), 15
MIN_BY_DATE = 20
RULE = dict(mean_gt=0.0025, share_positive_ge=0.60, median_gt=0.0, sub_mean_gt=0.0015, disc_min_n=15, pre_min_n=10)
EXCHANGES = {"NYSE Arca", "NASDAQ", "Cboe BZX"}
FORMS = {"497", "497K", "8-K"}
CASH = {"pre_last_trade", "post_last_trade_only", "timing_unspecified", "not_stated"}
SOURCE_KINDS = {"occ_memo", "issuer_notice", "ici_primary_layout", "irs_8937"}
TICK = re.compile(r"[A-Z]{1,5}")
FIELDS = ["ticker", "fund_name", "exchange", "cik", "accession", "form", "edgar_acceptance_utc", "stated_last_trading_day",
          "stated_liquidation_or_payout_date", "target_maturity_etf", "cash_before_last_trade", "cash_disclosure_quote", "filing_url"]


class Refuse(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refuse(why)


# ---- calendar
def d_(s):
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        raise Refuse(f"not a date: {s!r}")


def session(d):
    need(CAL_FROM <= d <= CAL_TO, f"{d} is outside the pinned NYSE calendar")
    return d.weekday() < 5 and d not in HOLIDAYS


def sessions_between(a, b):
    """NYSE sessions after a, up to and including b."""
    n, d = 0, a
    while d < b:
        d += timedelta(days=1); n += session(d)
    return n


def add_sessions(a, k):
    d = a
    while k:
        d += timedelta(days=1); k -= session(d)
    return d


def window(day):
    shift = timedelta(hours=3) if day in EARLY else timedelta(0)
    at = lambda t: (datetime.combine(day, t, NY) - shift).astimezone(UTC)
    return at(WIN_START), at(WIN_END), at(SNAP)


def ny_day(t):
    return t.astimezone(NY).date()


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def ns(s):
    """An RFC 3339 time with up to nine fractional digits, as integer nanoseconds since the epoch."""
    m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)", s)
    need(m, f"bad quote time {s!r}")
    base = datetime.fromisoformat(m.group(1) + (m.group(3).replace("Z", "+00:00")))
    return int(base.timestamp()) * 10**9 + int((m.group(2) or "0").ljust(9, "0"))


# ---- the quote summary
def summarize(quotes, day):
    """Duration-weighted median NBBO bid and ask over the window. A quote holds from its time until the next quote, its 60-second
    expiry or the window end. Valid means bid > 0, ask > 0 and bid <= ask. Fewer than 180 valid seconds is a refusal."""
    a, b, s = (int(x.timestamp()) * 10**9 for x in window(day))
    q = sorted(((ns(x["t"]), i, float(x.get("bp") or 0), float(x.get("ap") or 0)) for i, x in enumerate(quotes)), key=lambda r: (r[0], r[1]))
    seg = []
    for k, (t, _, bp, ap) in enumerate(q):
        end = min(q[k + 1][0] if k + 1 < len(q) else b, t + EXPIRY_S * 10**9, b)
        lo = max(t, a)
        if end > lo and bp > 0 and ap > 0 and bp <= ap:
            seg.append((end - lo, bp, ap))
    cover = sum(w for w, _, _ in seg) / 1e9

    def wmed(vals):
        tot, run = sum(w for w, _ in vals), 0
        for w, v in sorted(vals, key=lambda r: r[1]):
            run += w
            if 2 * run >= tot:
                return v
    snap = None
    for t, _, bp, ap in q:
        if t <= s:
            snap = (t, bp, ap)
    snap_ok = bool(snap and s - snap[0] < EXPIRY_S * 10**9 and snap[1] > 0 and snap[2] > 0 and snap[1] <= snap[2])
    out = dict(window_utc=[iso(x) for x in window(day)[:2]], snapshot_utc=iso(window(day)[2]), early_close=day in EARLY,
               quotes_read=len(q), valid_seconds=round(cover, 3),
               snapshot=dict(valid=snap_ok, bid=snap[1] if snap_ok else None, ask=snap[2] if snap_ok else None))
    if cover < MIN_COVER_S:
        return dict(out, quote_status="missing_or_insufficient", closing_bid=None, closing_ask=None)
    return dict(out, quote_status="ok", closing_bid=wmed([(w, bp) for w, bp, _ in seg]), closing_ask=wmed([(w, ap) for w, _, ap in seg]))


def curl_get(path, params):
    need(re.fullmatch(r"/v2/stocks/[A-Z]{1,5}/quotes", path), f"not on the read list: {path}")
    url = DATA + path + "?" + urlencode(params)
    cmd = ["pplx", "credentials", "run", HANDLE, "--", "curl", "--silent", "--fail", "--proto", "=https", "--max-time", "90", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=120)
    need(r.returncode == 0 and len(r.stdout) <= 16 * 1024 * 1024, "the data read failed")
    return json.loads(r.stdout)


def read_quotes(get, ticker, day):
    a, b, _ = window(day)
    q = dict(start=iso(a - timedelta(seconds=EXPIRY_S)), end=iso(b), feed="sip", limit=10000, sort="asc")
    pages, out, seen = [], [], set()
    for _ in range(50):
        p = get(f"/v2/stocks/{ticker}/quotes", q) or {}
        pages.append(p); out += p.get("quotes") or []
        tok = p.get("next_page_token")
        if not tok:
            return out, pages
        need(tok not in seen, "a data page repeated"); seen.add(tok); q["page_token"] = tok
    raise Refuse("too many data pages")


# ---- logs
def enc(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)


def private(off):
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    need(off.stat().st_mode & 0o077 == 0, "the record folder must be private (0700)")


def read_log(off=OFF):
    f = off / "log.jsonl"
    if not f.exists():
        return []
    out, prev = [], None
    for line in f.read_text().splitlines():
        x = json.loads(line)
        need(x["prev"] == prev, "log chain broken")
        prev = sha256(line.encode()).hexdigest(); out.append(x)
    return out


def read_public(pub):
    if not pub.exists():
        return []
    ent, prev = json.loads(pub.read_text())["entries"], None
    for x in ent:
        need(x["prev"] == prev, "public log chain broken")
        prev = sha256(enc(x).encode()).hexdigest()
    return ent


def write_packet(off, name, obj):
    blob = gzip.compress((json.dumps(obj, sort_keys=True, indent=1) + "\n").encode(), mtime=0)
    p = off / "packets" / name
    p.parent.mkdir(exist_ok=True, mode=0o700)
    need(not p.exists(), f"packet {name} already exists")
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(blob)
    return sha256(blob).hexdigest()


def append(x, pub_line, off, pub):
    """One private line and, if given, one public entry, both chained to the line before."""
    private(off)
    f = off / "log.jsonl"
    with open(off / ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        cur = read_log(off)
        x["prev"] = sha256(f.read_text().splitlines()[-1].encode()).hexdigest() if cur else None
        fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a") as out:
            out.write(enc(x) + "\n")
        if pub_line is not None:
            ent = read_public(pub)
            pub_line = dict(pub_line, prev=sha256(enc(ent[-1]).encode()).hexdigest() if ent else None,
                            private_line_sha256=sha256(enc(x).encode()).hexdigest())
            pub.parent.mkdir(exist_ok=True)
            tmp = pub.with_suffix(".tmp")
            tmp.write_text(json.dumps(dict(card=CARD, entries=ent + [pub_line]), indent=1, sort_keys=True) + "\n")
            os.replace(tmp, pub)
    return x


def file_sha(p):
    return sha256((ROOT / p).read_bytes()).hexdigest()


def pinned(log):
    need(log and log[0]["kind"] == "header", "log not started")
    h = log[0]
    need(file_sha(CARD) == h["card_sha256"] and file_sha(ME) == h["logger_sha256"], "card or logger changed since the header")
    return h


# ---- state
def state(log):
    funds, order = {}, []
    for x in log[1:]:
        k, t = x["kind"], x.get("ticker")
        if k == "fund":
            funds[t] = dict(fund=x["fund"], amended=[], withdrawn=None, quote=None, payout=None, secondary=[]); order.append(t)
        elif k == "amend":
            funds[t]["amended"].append(x); funds[t]["fund"] = dict(funds[t]["fund"], **x["new"])
        elif k == "withdraw":
            funds[t]["withdrawn"] = x
        elif k == "quote":
            funds[t]["quote"] = x
        elif k == "payout":
            funds[t]["secondary" if x["secondary"] else "payout"] = (funds[t]["secondary"] + [x]) if x["secondary"] else x
    first_pay = {}
    for i, x in enumerate(log):
        if x["kind"] == "payout" and not x["secondary"]:
            first_pay.setdefault(x["ticker"], i)
    completed = sorted((t for t in funds if done(funds[t])), key=lambda t: first_pay[t])
    return funds, order, completed


def done(f):
    return bool(f["payout"] and f["quote"] and f["quote"]["summary"]["quote_status"] == "ok" and not f["withdrawn"])


def stopped(log, now):
    _, _, comp = state(log)
    return len(comp) >= STOP_COUNT or ny_day(now) > LAST_ADMIT


# ---- commands
def check_row(r, now):
    need(set(FIELDS) <= set(r), "the watch-list row lacks a card field")
    t = r["ticker"].strip()
    need(TICK.fullmatch(t), f"bad ticker {t!r}")
    need(r["exchange"] in EXCHANGES, f"{t}: exchange {r['exchange']!r} is not NYSE Arca, NASDAQ or Cboe BZX")
    need(re.fullmatch(r"\d{1,10}", r["cik"]) and re.fullmatch(r"\d{10}-\d\d-\d{6}", r["accession"]), f"{t}: bad CIK or accession")
    need(r["form"] in FORMS, f"{t}: form {r['form']!r} is not 497, 497K or 8-K")
    need(re.fullmatch(r"https://www\.sec\.gov/\S+", r["filing_url"]), f"{t}: the filing link must be an https sec.gov link")
    acc = datetime.strptime(r["edgar_acceptance_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    ltd, pay = d_(r["stated_last_trading_day"]), d_(r["stated_liquidation_or_payout_date"])
    need(session(ltd), f"{t}: the stated last trading day {ltd} is not an NYSE session")
    need(ltd > ny_day(acc), f"{t}: the last trading day must be after the filing's acceptance day")
    need(pay >= ltd, f"{t}: the payout date is before the last trading day")
    need(ltd <= LAST_ADMIT, f"{t}: last trading day after {LAST_ADMIT}, outside the watch")
    need(now < window(ltd)[0], f"{t}: its quote window has started or passed; no back-filling")
    need(r["target_maturity_etf"] in ("true", "false"), f"{t}: target_maturity_etf must be true or false")
    need(r["cash_before_last_trade"] in CASH, f"{t}: bad cash_before_last_trade")
    need(r["cash_disclosure_quote"].strip() or r["cash_before_last_trade"] == "not_stated", f"{t}: the controlling sentence is missing")
    out = {k: r[k].strip() for k in FIELDS}
    out["target_maturity_etf"] = r["target_maturity_etf"] == "true"
    return out


def public_fund(f):
    return {k: f[k] for k in ("ticker", "fund_name", "exchange", "cik", "accession", "form", "edgar_acceptance_utc", "stated_last_trading_day",
                              "stated_liquidation_or_payout_date", "target_maturity_etf", "cash_before_last_trade", "filing_url")}


def add_funds(csv_path, tickers, now, off=OFF, pub=PUBLIC, commit=None):
    raw = Path(csv_path).read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    log = read_log(off)
    if not log:
        if commit is None:
            need(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", CARD, ME], capture_output=True, text=True).stdout == "",
                 "card or logger differs from the commit")
            commit = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", ME], capture_output=True, text=True, check=True).stdout.strip()
        h = dict(kind="header", card=CARD, card_sha256=file_sha(CARD), logger_sha256=file_sha(ME), commit=commit, made_utc=iso(now),
                 rules=dict(stop_count=STOP_COUNT, last_admit=str(LAST_ADMIT), grace_end=str(GRACE_END), payout_sessions=PAYOUT_SESSIONS,
                            min_by_date=MIN_BY_DATE, decision=RULE, expiry_s=EXPIRY_S, min_cover_s=MIN_COVER_S))
        append(h, dict(kind="header", card_sha256=h["card_sha256"], logger_sha256=h["logger_sha256"], commit=commit, made_utc=h["made_utc"]), off, pub)
        log = read_log(off)
    pinned(log)
    need(not stopped(log, now), "the stop rule is met; no new funds")
    funds, _, _ = state(log)
    pick = [r for r in rows if not tickers or r["ticker"].strip() in tickers]
    need(pick, "no matching rows")
    ok = [check_row(r, now) for r in pick]
    seen = set(funds)
    for f in ok:
        need(f["ticker"] not in seen, f"{f['ticker']} is already admitted"); seen.add(f["ticker"])
    src = dict(csv_sha256=sha256(raw).hexdigest(), csv_name=Path(csv_path).name)
    for f in ok:
        append(dict(kind="fund", ticker=f["ticker"], fund=f, source=src, made_utc=iso(now)),
               dict(kind="fund", **public_fund(f), csv_sha256=src["csv_sha256"], made_utc=iso(now)), off, pub)
    return [f["ticker"] for f in ok]


def amend(ticker, ltd, pay, url, now, off=OFF, pub=PUBLIC):
    log = read_log(off); pinned(log); funds, _, _ = state(log)
    need(ticker in funds and not funds[ticker]["withdrawn"], f"{ticker} is not an open fund")
    f = funds[ticker]["fund"]
    need(now < window(d_(f["stated_last_trading_day"]))[0], "the original quote window has started; no amendment")
    need(re.fullmatch(r"https://www\.sec\.gov/\S+", url), "the supplement link must be an https sec.gov link")
    new = {}
    if ltd:
        L = d_(ltd); need(session(L) and L <= LAST_ADMIT and now < window(L)[0], "the new last trading day is not a future session in the watch"); new["stated_last_trading_day"] = ltd
    if pay:
        need(d_(pay) >= d_(ltd or f["stated_last_trading_day"]), "the new payout date is before the last trading day"); new["stated_liquidation_or_payout_date"] = pay
    need(new, "nothing to amend")
    old = {k: f[k] for k in new}
    return append(dict(kind="amend", ticker=ticker, old=old, new=new, filing_url=url, original_filing_url=f["filing_url"], made_utc=iso(now)),
                  dict(kind="amend", ticker=ticker, old=old, new=new, filing_url=url, made_utc=iso(now)), off, pub)


def withdraw(ticker, url, reason, now, off=OFF, pub=PUBLIC):
    log = read_log(off); pinned(log); funds, _, _ = state(log)
    need(ticker in funds and not funds[ticker]["withdrawn"] and not funds[ticker]["payout"], f"{ticker} is not an open fund")
    need(re.fullmatch(r"https://\S+", url) and reason.strip(), "give the superseding filing link and a reason")
    return append(dict(kind="withdraw", ticker=ticker, filing_url=url, reason=reason, made_utc=iso(now)),
                  dict(kind="withdraw", ticker=ticker, filing_url=url, reason=reason, made_utc=iso(now)), off, pub)


def record_quote(now, get=None, tickers=None, off=OFF, pub=PUBLIC):
    """Record every open fund whose stated last trading day is today in New York and whose window has closed."""
    log = read_log(off); pinned(log); funds, _, comp = state(log)
    need(len(comp) < STOP_COUNT, "40 completed funds are in; no new observations")
    today, out = ny_day(now), []
    for t, F in funds.items():
        f = F["fund"]
        if tickers and t not in tickers:
            continue
        if F["withdrawn"] or F["quote"] or d_(f["stated_last_trading_day"]) != today:
            continue
        if now < window(today)[1] + timedelta(seconds=30):
            continue
        try:
            q, pages = read_quotes(get or curl_get, t, today)
            s = summarize(q, today)
        except Refuse as e:
            s, pages = dict(quote_status="missing_or_insufficient", reason=str(e), closing_bid=None, closing_ask=None), []
        sha = write_packet(off, f"{t}_{today}_quote.json.gz", dict(ticker=t, day=str(today), pages=pages, summary=s))
        x = append(dict(kind="quote", ticker=t, day=str(today), summary=s, packet_sha256=sha, made_utc=iso(now)),
                   dict(kind="quote", ticker=t, day=str(today), quote_status=s["quote_status"], valid_seconds=s.get("valid_seconds"),
                        early_close=today in EARLY, packet_sha256=sha, made_utc=iso(now)), off, pub)
        out.append((t, s["quote_status"]))
    return out


def payout_deadline(f):
    return add_sessions(d_(f["stated_liquidation_or_payout_date"]), PAYOUT_SESSIONS)


def record_payout(ticker, per_share, payment_date, url, kind, source_date, now, extras=(), secondary=False, off=OFF, pub=PUBLIC):
    log = read_log(off); pinned(log); funds, _, _ = state(log)
    need(ticker in funds and not funds[ticker]["withdrawn"], f"{ticker} is not an open fund")
    F = funds[ticker]; f = F["fund"]; ltd = d_(f["stated_last_trading_day"])
    need(secondary or not F["payout"], f"{ticker} already has a primary payout")
    need(isinstance(per_share, float) and per_share > 0, "the payout per share must be a positive number")
    pay, sd = d_(payment_date), d_(source_date)
    need(pay >= ltd and sd <= ny_day(now), "the payment date is before the last trading day, or the source date is in the future")
    need(re.fullmatch(r"https://\S+", url), "the source must be an https link")
    if not secondary:
        need(kind in SOURCE_KINDS, f"a primary source is one of {sorted(SOURCE_KINDS)}")
        need(ny_day(now) <= min(payout_deadline(f), GRACE_END), f"{ticker}: past the payout deadline; it stays primary_missing")
    ex = []
    for e in extras:
        need(e["amount"] > 0 and d_(e["ex_date"]) > ltd and re.fullmatch(r"https://\S+", e["url"]),
             "an extra distribution needs a positive amount, an ex-date after the last trading day and an https link")
        ex.append(dict(amount=e["amount"], ex_date=e["ex_date"], url=e["url"]))
    rec = dict(payout_per_share=per_share, extra_distributions=ex, payout_total=per_share + sum(e["amount"] for e in ex),
               payment_date=payment_date, source_url=url, source_kind=kind, source_date=source_date)
    sha = write_packet(off, f"{ticker}_payout{'_secondary_' + str(len(F['secondary'])) if secondary else ''}.json.gz", dict(ticker=ticker, **rec))
    return append(dict(kind="payout", ticker=ticker, secondary=secondary, payout=rec, packet_sha256=sha, made_utc=iso(now)),
                  dict(kind="payout", ticker=ticker, secondary=secondary, payment_date=payment_date, source_url=url, source_kind=kind,
                       source_date=source_date, extra_ex_dates=[e["ex_date"] for e in ex], packet_sha256=sha,
                       calendar_days=(pay - ltd).days, sessions=sessions_between(ltd, pay), made_utc=iso(now)), off, pub)


def alive(now, off=OFF):
    log = read_log(off)
    if not log:
        return dict(started=False)
    funds, _, comp = state(log); today = ny_day(now)
    c = dict(started=True, funds=len(funds), withdrawn=0, quote_ok=0, quote_refused=0, quote_missed=0, quote_pending=0,
             payout_primary=0, payout_pending=0, primary_missing=0, secondary_only=0, completed=len(comp),
             stop_met=stopped(log, now), last_made_utc=log[-1].get("made_utc"))
    for F in funds.values():
        f = F["fund"]
        if F["withdrawn"]:
            c["withdrawn"] += 1; continue
        ltd = d_(f["stated_last_trading_day"])
        if F["quote"]:
            c["quote_ok" if F["quote"]["summary"]["quote_status"] == "ok" else "quote_refused"] += 1
        elif ltd < today:
            c["quote_missed"] += 1
        else:
            c["quote_pending"] += 1
        if F["payout"]:
            c["payout_primary"] += 1
        elif today > min(payout_deadline(f), GRACE_END):
            c["primary_missing"] += 1; c["secondary_only"] += bool(F["secondary"])
        else:
            c["payout_pending"] += 1
    return c


def measures(F):
    q, p = F["quote"]["summary"], F["payout"]["payout"]
    ltd, pay = d_(F["fund"]["stated_last_trading_day"]), d_(p["payment_date"])
    a, b = q["closing_ask"], q["closing_bid"]
    return dict(over_ask=p["payout_total"] / a - 1, over_bid=p["payout_total"] / b - 1, spread_bps=(a - b) / ((a + b) / 2) * 1e4,
                calendar_days=(pay - ltd).days, sessions=sessions_between(ltd, pay))


def agg(ms):
    if not ms:
        return dict(n=0)
    oa = [m["over_ask"] for m in ms]
    return dict(n=len(ms), mean_over_ask_pct=round(100 * sum(oa) / len(oa), 4), median_over_ask_pct=round(100 * median(oa), 4),
                share_over_ask_positive_pct=round(100 * sum(x > 0 for x in oa) / len(oa), 2),
                mean_over_bid_pct=round(100 * sum(m["over_bid"] for m in ms) / len(ms), 4),
                median_spread_bps=round(median(m["spread_bps"] for m in ms), 2),
                median_calendar_days=median(m["calendar_days"] for m in ms), median_sessions=median(m["sessions"] for m in ms))


def score(now, off=OFF, pub=PUBLIC):
    log = read_log(off); pinned(log); funds, _, comp = state(log)
    need(not any(x["kind"] == "final" for x in log), "already scored")
    by_count = len(comp) >= STOP_COUNT
    need(by_count or ny_day(now) > GRACE_END, f"the stop rule is not met: {len(comp)} completed of {STOP_COUNT}, and the grace ends {GRACE_END}")
    use = comp[:STOP_COUNT]
    m = {t: measures(funds[t]) for t in use}
    tm = lambda v: [m[t] for t in use if funds[t]["fund"]["target_maturity_etf"] is v]
    cash = lambda k: [m[t] for t in use if funds[t]["fund"]["cash_before_last_trade"] == k]
    sl = dict(all=agg(list(m.values())), discretionary=agg(tm(False)), target_maturity=agg(tm(True)),
              pre_last_trade=agg(cash("pre_last_trade")), post_last_trade_only=agg(cash("post_last_trade_only")))
    n = len(use)
    if not by_count and n < MIN_BY_DATE:
        verdict = "inconclusive_on_data_availability"; conds = None
    else:
        oa = [m[t]["over_ask"] for t in use]
        d, p = [x["over_ask"] for x in tm(False)], [x["over_ask"] for x in cash("pre_last_trade")]
        conds = dict(mean=sum(oa) / n > RULE["mean_gt"], share_positive=sum(x > 0 for x in oa) / n >= RULE["share_positive_ge"],
                     median=median(oa) > RULE["median_gt"],
                     discretionary=(sum(d) / len(d) > RULE["sub_mean_gt"]) if len(d) >= RULE["disc_min_n"] else None,
                     pre_last_trade=(sum(p) / len(p) > RULE["sub_mean_gt"]) if len(p) >= RULE["pre_min_n"] else None)
        verdict = "write_follow_on" if all(v is not False for v in conds.values()) else "close_on_forward_evidence"
    a = alive(now, off)
    res = dict(stopped_by="count" if by_count else "date", completed_used=n, slices=sl, conditions=conds, verdict=verdict,
               counts={k: a[k] for k in ("funds", "withdrawn", "quote_ok", "quote_refused", "quote_missed", "primary_missing", "secondary_only")})
    append(dict(kind="final", result=res, made_utc=iso(now)), dict(kind="final", **res, made_utc=iso(now)), off, pub)
    return res


def plan():
    return dict(card=CARD, window_ny=[str(WIN_START), str(WIN_END)], snapshot_ny=str(SNAP), early_closes=sorted(map(str, EARLY)),
                expiry_s=EXPIRY_S, min_cover_s=MIN_COVER_S, stop_count=STOP_COUNT, last_admit=str(LAST_ADMIT), grace_end=str(GRACE_END),
                payout_sessions=PAYOUT_SESSIONS, min_by_date=MIN_BY_DATE, decision=RULE, primary_sources=sorted(SOURCE_KINDS))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    s = sub.add_parser("add-fund"); s.add_argument("--csv", required=True); s.add_argument("tickers", nargs="*")
    s = sub.add_parser("amend-dates"); s.add_argument("ticker"); s.add_argument("--last-trading-day"); s.add_argument("--payout-date"); s.add_argument("--filing-url", required=True)
    s = sub.add_parser("withdraw"); s.add_argument("ticker"); s.add_argument("--filing-url", required=True); s.add_argument("--reason", required=True)
    s = sub.add_parser("record-quote"); s.add_argument("tickers", nargs="*")
    s = sub.add_parser("record-payout"); s.add_argument("ticker"); s.add_argument("--per-share", type=float, required=True)
    s.add_argument("--payment-date", required=True); s.add_argument("--source-url", required=True); s.add_argument("--source-kind", required=True)
    s.add_argument("--source-date", required=True); s.add_argument("--extra", action="append", default=[], help="AMOUNT,EX_DATE,URL")
    s.add_argument("--secondary", action="store_true")
    sub.add_parser("alive"); sub.add_parser("score")
    a = ap.parse_args(argv); now = datetime.now(UTC)
    try:
        if a.cmd == "plan":
            print(json.dumps(plan(), indent=1))
        elif a.cmd == "add-fund":
            print("admitted", " ".join(add_funds(a.csv, a.tickers, now)))
        elif a.cmd == "amend-dates":
            amend(a.ticker, a.last_trading_day, a.payout_date, a.filing_url, now); print("amended", a.ticker)
        elif a.cmd == "withdraw":
            withdraw(a.ticker, a.filing_url, a.reason, now); print("withdrawn", a.ticker)
        elif a.cmd == "record-quote":
            r = record_quote(now, tickers=a.tickers); print("nothing due" if not r else " ".join(f"{t}:{s}" for t, s in r))
        elif a.cmd == "record-payout":
            ex = []
            for e in a.extra:
                amt, d, u = e.split(",", 2); ex.append(dict(amount=float(amt), ex_date=d, url=u))
            record_payout(a.ticker, a.per_share, a.payment_date, a.source_url, a.source_kind, a.source_date, now, ex, a.secondary)
            print("payout recorded", a.ticker, "(secondary, not counted)" if a.secondary else "")
        elif a.cmd == "alive":
            print(json.dumps(alive(now), indent=1))
        else:
            print(json.dumps(score(now), indent=1))
    except Refuse as e:
        print("Refused, nothing written:", e); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
