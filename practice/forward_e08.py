"""E08 forward log: the taxable closed-end fund January turn of December 2026, fifth-session exit, pretend money.

Card: practice/traders/E08_taxable_cef_fifth_session_exit.md (the card governs). No orders and no broker. Commands:
  plan               print the pinned sessions, command windows, costs and sizing (no network)
  freeze-list        hash and freeze the reviewed 2026 PCEF-derived roster and exclusion log; the first call writes the
                     log header with the card, logger and engine SHA-256 and the card's commit
  record-entry       after the 2026-12-31 close: read raw SIP daily bars, split records and the entry quote window, rank
                     the frozen list on 2026-01-02 to 2026-12-30 price return, size the worst five that fit and PCEF
  record-exit5       after the 2027-01-08 close (fifth January session): value the same five and PCEF; the card's claim
  record-exit-month  after the 2027-01-29 close (last January session): the plan 53 reference exit
  alive              counts only: which records exist. No prices, tickers or returns

Every command refuses outside its window and refuses a second write. A refusal writes nothing. Private records (raw
pages, closes, quotes, share counts, picks, cash amounts) go to /home/user/workspace/rig/data/forward_e08 (0700 folder,
0600 files) as a hash-chained log.jsonl plus gzip packets. The public log practice/forward/E08_log.json holds dates,
counts, private packet SHA-256, the chain hash and, at each exit, the return percentages only.

Costs, quote parsing, bar parsing and the half-spread rule are imported from the frozen shared engine
research_rig/common_48.py (Plan 48 and Plan 53), whose SHA-256 is pinned in the header. Standard library only. Reads only.

  pplx credentials run <data handle> -- python3 practice/forward_e08.py record-entry
"""
import argparse, csv, fcntl, gzip, io, json, os, re, subprocess, sys
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_rig"))
import common_48 as C  # noqa: E402  frozen Plan 48/53 engine: bar_rows, quote_rows, measured_half_spread

CARD = "practice/traders/E08_taxable_cef_fifth_session_exit.md"
ME = "practice/forward_e08.py"
ENGINE = "research_rig/common_48.py"
OFF = Path(os.environ.get("E08_RECORD_DIR", "/home/user/workspace/rig/data/forward_e08"))
PUBLIC = ROOT / "practice" / "forward" / "E08_log.json"
HANDLE = "custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets"
DATA = "https://data.alpaca.markets"
NY, UTC = ZoneInfo("America/New_York"), timezone.utc

# NYSE sessions, pinned from the NYSE Group 2026 and 2027 holiday calendar (read 2026-11-26) and checked against
# research_rig/calendar_25.json for 2026-01-02 to 2026-11-24. No early close falls on a clock this card uses.
CAL_FROM, CAL_TO = date(2026, 1, 1), date(2027, 2, 28)
HOLIDAYS = {date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3), date(2026, 5, 25), date(2026, 6, 19),
            date(2026, 7, 3), date(2026, 9, 7), date(2026, 11, 26), date(2026, 12, 25), date(2027, 1, 1), date(2027, 1, 18),
            date(2027, 2, 15)}
EARLY = {date(2026, 11, 27), date(2026, 12, 24)}
TURN = 2026
ROSTER_CUTOFF = date(2026, 12, 1)  # report period and public date strictly before this (replay_53_plan.roster_cutoff)

# Plan 48/53 numbers, copied from config/thresholds.yaml replay_48_plan and replay_53_plan (checked by the tests).
CFG = {"sleeve_usd": 100, "capital": 500, "picks": 5, "split_check_ratio": "1.4", "benchmark": "PCEF",
       "cost": {"extra_bps": 5, "proxy_half_bps": 50, "window_start": "15:53:00", "measure_start": "15:54:00",
                "measure_end": "15:59:00", "expiry_seconds": 60, "min_coverage_seconds": 180}}
MUNI_TERMS = ["MUNI", "MUNIS", "MUNICIPAL", "MUNICIPALS", "MUNICIPALITY", "MUNICIPALITIES", "TAX FREE", "TAX EXEMPT"]
HOLDINGS_FORMS = {"N-Q", "N-Q/A", "NPORT-P", "NPORT-P/A", "N-CSR", "N-CSR/A", "N-CSRS", "N-CSRS/A"}
ROSTER_FIELDS = ["turn_year", "holding_id", "ticker", "cik", "holding_name", "identity_url", "series", "report_period",
                 "public_date", "form", "filing_url"]
EXCL_REASONS = {"municipal_name", "replay48_overlap", "not_listed_cef_common", "unresolved_identity", "duplicate_common"}
MUNI_ROSTER = Path(os.environ.get("E08_MUNI_ROSTER", "/home/user/workspace/rig/inventories/row86_muni_cef_roster.csv"))
CASH_KINDS = {"issuer_site", "issuer_wire", "sec", "exchange"}
CASH_STATUS = {"documented", "none", "partial", "unresolved"}
TICK = re.compile(r"[A-Z]{1,5}")
SETTLE = timedelta(minutes=20)  # bars and quotes are read at least 20 minutes after the 16:00 close


class Refuse(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refuse(why)


# ---- calendar and windows
def d_(s):
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        raise Refuse(f"not a date: {s!r}")


def session(d):
    need(CAL_FROM <= d <= CAL_TO, f"{d} is outside the pinned NYSE calendar")
    return d.weekday() < 5 and d not in HOLIDAYS


def sessions(a, b):
    out, d = [], a
    while d <= b:
        if session(d):
            out.append(d)
        d += timedelta(days=1)
    return out


DEC = [d for d in sessions(date(2026, 12, 1), date(2026, 12, 31))]
JAN = [d for d in sessions(date(2027, 1, 1), date(2027, 1, 31))]
ANCHOR = sessions(date(2026, 1, 1), date(2026, 1, 31))[0]
FORMATION, ENTRY = DEC[-2], DEC[-1]
EXIT5, EXITM = JAN[4], JAN[-1]
RANK_DAYS = sessions(ANCHOR, ENTRY)


def ny(d, hh, mm=0):
    return datetime.combine(d, time(hh, mm), NY).astimezone(UTC)


def midnight(d):
    return datetime.combine(d, time(0), NY).astimezone(UTC)


# Each command's window [open, close) in UTC. Freeze closes at the formation session's open, so the list is fixed before
# the ranking close exists; entry closes at the first January open, so the picks are fixed before any January price.
WINDOWS = {
    "freeze-list": (midnight(ROSTER_CUTOFF), ny(FORMATION, 9, 30)),
    "record-entry": (ny(ENTRY, 16) + SETTLE, ny(JAN[0], 9, 30)),
    "record-exit5": (ny(EXIT5, 16) + SETTLE, midnight(EXIT5 + timedelta(days=8))),
    "record-exit-month": (ny(EXITM, 16) + SETTLE, midnight(EXITM + timedelta(days=15))),
}
KIND = {"freeze-list": "freeze", "record-entry": "entry", "record-exit5": "exit5", "record-exit-month": "exit_month"}
EXIT_DAY = {"exit5": EXIT5, "exit_month": EXITM}


def in_window(cmd, now):
    a, b = WINDOWS[cmd]
    need(a <= now < b, f"{cmd} is open from {iso(a)} to {iso(b)} (UTC); now is {iso(now)}")


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- data route (the same saved credential and host as E07)
READS = (r"/v2/stocks/[A-Z]{1,5}/quotes", r"/v2/stocks/[A-Z]{1,5}/bars", r"/v1/corporate-actions")


def curl_get(path, params):
    need(any(re.fullmatch(p, path) for p in READS), f"not on the read list: {path}")
    url = DATA + path + "?" + urlencode(params)
    cmd = ["pplx", "credentials", "run", HANDLE, "--", "curl", "--silent", "--fail", "--proto", "=https", "--max-time", "90", url]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=120)
    need(r.returncode == 0 and len(r.stdout) <= 16 * 1024 * 1024, "the data read failed")
    return json.loads(r.stdout, parse_float=Decimal)


def paged(get, path, q, key):
    q, pages, seen = dict(q), [], set()
    for _ in range(200):
        p = get(path, q) or {}
        pages.append(p)
        tok = p.get("next_page_token")
        if not tok:
            return pages
        need(tok not in seen, "a data page repeated"); seen.add(tok); q["page_token"] = tok
    raise Refuse("too many data pages")


def read_bars(get, t, a, b, adjustment):
    pages = paged(get, f"/v2/stocks/{t}/bars", dict(timeframe="1Day", start=a.isoformat(), end=b.isoformat(), feed="sip",
                                                    adjustment=adjustment, limit=10000, sort="asc"), "bars")
    rows = [dict(t=x["t"], o=x["o"], h=x["h"], l=x["l"], c=x["c"], v=x["v"]) for p in pages for x in (p.get("bars") or [])]
    return rows, pages


def read_splits(get, t, a, b):
    pages = paged(get, "/v1/corporate-actions", dict(symbols=t, types="forward_split,reverse_split", start=a.isoformat(),
                                                     end=b.isoformat(), limit=1000), "corporate_actions")
    out = []
    for p in pages:
        ca = p.get("corporate_actions") or {}
        for kind in ("forward_splits", "reverse_splits"):
            for r in ca.get(kind) or []:
                if r.get("symbol") == t:
                    out.append(dict(kind=kind, ex_date=r.get("ex_date"), new_rate=str(r.get("new_rate")), old_rate=str(r.get("old_rate"))))
    return out, pages


def read_quotes(get, t, d):
    a, b = ny(d, 15, 53), ny(d, 15, 59)
    pages = paged(get, f"/v2/stocks/{t}/quotes", dict(start=iso(a), end=iso(b), feed="sip", limit=10000, sort="asc"), "quotes")
    lo, hi = C.clock(d, CFG["cost"]["window_start"]), C.clock(d, CFG["cost"]["measure_end"])
    rows = []
    for p in pages:
        for x in p.get("quotes") or []:
            r = dict(t=x.get("t"), bp=x.get("bp", 0), ap=x.get("ap", 0))
            try:
                if lo <= C.quote_instant(r["t"]) < hi:
                    rows.append(r)
            except C.Refused:
                rows.append(r)  # a malformed time makes the side a proxy below
    return rows, pages


def half_spread(get, t, d):
    """Plan 48/53 half-spread for one side, or None (the 50 bp proxy) when coverage is short or the page is malformed."""
    rows, pages = read_quotes(get, t, d)
    try:
        h = C.measured_half_spread(C.quote_rows(rows, d, CFG), d, CFG)
        why = None if h is not None else "coverage under 180 seconds"
    except C.Refused as e:
        h, why = None, f"quote page refused by the engine ({e})"
    return h, why, pages


def split_steps(c, ca):
    """Sessions where the raw over split-adjusted close ratio changes from the previous common session: a split step."""
    days = sorted(d for d in c if d in ca)
    return [b for a, b in zip(days, days[1:]) if c[b] / ca[b] != c[a] / ca[a]] + [d for d in c if d not in ca]


def closes_of(rows, days):
    """The engine's raw bar check; zero-volume rows are kept in transport but give no close."""
    return C.bar_rows(rows, {"sessions": days}, days[-1])


# ---- money (exact fractions; floats only for printed percentages)
EXTRA = Fraction(CFG["cost"]["extra_bps"], 10_000)
PROXY = Fraction(CFG["cost"]["proxy_half_bps"], 10_000)


def F(x):
    return Fraction(str(x)) if not isinstance(x, Fraction) else x


def fs(x):
    return f"{x.numerator}/{x.denominator}"


def pct(x):
    return round(float(x) * 100, 4)


# ---- logs (the E07 chain)
def enc(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str)


def private(off):
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    need(off.stat().st_mode & 0o077 == 0, "the record folder must be private (0700)")


def read_log(off):
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
    blob = gzip.compress((json.dumps(obj, sort_keys=True, indent=1, default=str) + "\n").encode(), mtime=0)
    p = off / "packets" / name
    p.parent.mkdir(exist_ok=True, mode=0o700)
    need(not p.exists(), f"packet {name} already exists")
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(blob)
    return sha256(blob).hexdigest()


def append(x, pub_line, off, pub):
    private(off)
    f = off / "log.jsonl"
    with open(off / ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        cur = read_log(off)
        need(not any(y["kind"] == x["kind"] for y in cur), f"a {x['kind']} record already exists; one write only")
        x["prev"] = sha256(f.read_text().splitlines()[-1].encode()).hexdigest() if cur else None
        fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a") as out:
            out.write(enc(x) + "\n")
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
    need(log and log[0]["kind"] == "header", "log not started: run freeze-list first")
    h = log[0]
    need(file_sha(CARD) == h["card_sha256"] and file_sha(ME) == h["logger_sha256"] and file_sha(ENGINE) == h["engine_sha256"],
         "card, logger or engine changed since the header")
    return h


def get_kind(log, k):
    return next((x for x in log if x["kind"] == k), None)


def first_write(kind, log):
    need(get_kind(log, kind) is None, f"a {kind} record already exists; one write only")


# ---- freeze-list
def muni_hit(name):
    toks = [t for t in re.split(r"[^A-Z0-9]+", name.upper()) if t]
    text = " " + " ".join(toks) + " "
    return any(f" {m} " in text for m in MUNI_TERMS)


def read_csv(path, fields):
    raw = Path(path).read_bytes()
    need(raw.endswith(b"\n"), f"{Path(path).name}: the file must end with a newline")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"), newline="")))
    need(rows == [] or list(rows[0].keys()) == fields, f"{Path(path).name}: header must be {','.join(fields)}")
    return raw, rows


def check_roster(roster_path, excl_path, muni_path=MUNI_ROSTER):
    raw_r, rows = read_csv(roster_path, ROSTER_FIELDS)
    raw_x, xs = read_csv(excl_path, ROSTER_FIELDS + ["reason"])
    need(len(rows) >= CFG["picks"], "the roster has fewer than five funds")
    seen_t, seen_c, ids, filing = set(), set(), [], set()
    for r in rows + xs:
        need(r["turn_year"] == str(TURN), f"row turn_year must be {TURN}")
        need(re.fullmatch(r"[1-9]\d*", r["holding_id"]), "holding_id must be a positive integer")
        ids.append(int(r["holding_id"])); filing.add((r["filing_url"], r["report_period"], r["public_date"], r["form"]))
    need(sorted(ids) == list(range(1, len(ids) + 1)), "holding_id must run 1..N without gaps across both files")
    need([int(r["holding_id"]) for r in rows] == sorted(int(r["holding_id"]) for r in rows), "roster.csv not sorted by holding_id")
    need([int(r["holding_id"]) for r in xs] == sorted(int(r["holding_id"]) for r in xs), "exclusions not sorted by holding_id")
    need(len(filing) == 1, "both files must come from one PCEF holdings filing")
    url, rp, pd, form = filing.pop()
    need(form in HOLDINGS_FORMS, f"form {form} is not a permitted holdings form")
    need(d_(rp) < ROSTER_CUTOFF and d_(pd) < ROSTER_CUTOFF, "report period and public date must both be before 2026-12-01")
    need(re.fullmatch(r"https://www\.sec\.gov/Archives/edgar/data/1378872/\S+", url), "the filing must be a PCEF trust filing on sec.gov")
    muni_t, muni_c = set(), set()
    for r in csv.DictReader(io.StringIO(Path(muni_path).read_text(encoding="utf-8-sig"))):
        if r["turn_year"].strip() == str(TURN):
            muni_t.add(r["ticker"].strip()); muni_c.add(r["cik"].strip())
    need(muni_t, "the Replay 48 muni roster has no 2026 rows")
    for r in rows:
        t = r["ticker"]
        need(TICK.fullmatch(t) and t != CFG["benchmark"], f"bad roster ticker {t!r}")
        need(re.fullmatch(r"\d{10}", r["cik"]), f"{t}: CIK must have ten digits")
        need(r["series"] == "S000027370", f"{t}: series must be the PCEF series S000027370")
        need(re.fullmatch(r"https://\S+", r["identity_url"]), f"{t}: identity_url must be an https link")
        need(t not in seen_t and r["cik"] not in seen_c, f"{t}: duplicate common fund"); seen_t.add(t); seen_c.add(r["cik"])
        need(not muni_hit(r["holding_name"]), f"{t}: municipal name hit; it belongs in the exclusion log")
        need(t not in muni_t and r["cik"] not in muni_c, f"{t}: matches the Replay 48 muni roster for 2026")
    for r in xs:
        need(r["reason"] in EXCL_REASONS, f"exclusion reason {r['reason']!r} is not one of plan 53's five")
    return dict(roster_sha256=sha256(raw_r).hexdigest(), exclusions_sha256=sha256(raw_x).hexdigest(),
                roster=[r["ticker"] for r in rows], excluded=len(xs), filing_url=url, report_period=rp, public_date=pd, form=form)


def freeze_list(roster_path, excl_path, now, off=OFF, pub=PUBLIC, commit=None, muni_path=MUNI_ROSTER):
    in_window("freeze-list", now)
    log = read_log(off)
    need(not log, "the list is already frozen; one write only")
    fz = check_roster(roster_path, excl_path, muni_path)
    if commit is None:
        need(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", CARD, ME, ENGINE], capture_output=True,
                            text=True).stdout == "", "card, logger or engine differs from the commit")
        commit = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", ME], capture_output=True, text=True,
                                check=True).stdout.strip()
    h = dict(kind="header", card=CARD, card_sha256=file_sha(CARD), logger_sha256=file_sha(ME), engine_sha256=file_sha(ENGINE),
             commit=commit, made_utc=iso(now), rules=plan())
    append(h, dict(kind="header", card_sha256=h["card_sha256"], logger_sha256=h["logger_sha256"], engine_sha256=h["engine_sha256"],
                   commit=commit, made_utc=h["made_utc"]), off, pub)
    priv = dict(kind="freeze", made_utc=iso(now), **fz)
    pubx = {k: fz[k] for k in ("roster_sha256", "exclusions_sha256", "excluded", "filing_url", "report_period", "public_date", "form")}
    append(priv, dict(kind="freeze", roster_count=len(fz["roster"]), made_utc=iso(now), **pubx), off, pub)
    return fz


# ---- jumps (Plan 53 v4 rule, forward form)
def jumps(closes, split_days=()):
    lim = Fraction(CFG["split_check_ratio"])
    days = sorted(closes)
    return [(a, b) for a, b in zip(days, days[1:]) if b not in split_days and not (1 / lim <= closes[b] / closes[a] <= lim)]


def parse_clear(items, allowed):
    out = {}
    for s in items:
        p = s.split(",", 4)
        need(len(p) == 5, "a clearance is TICKER,EARLIER,LATER,CLASS,EVIDENCE_URL")
        t, a, b, k, u = p
        need(k in allowed and re.fullmatch(r"https://[^\s,?#@]+", u), f"bad clearance class or link for {t}")
        key = (t, d_(a), d_(b))
        need(key not in out, f"duplicate clearance {s}"); out[key] = dict(classification=k, evidence_url=u)
    return out


# ---- record-entry
def record_entry(now, get=None, clear=(), off=OFF, pub=PUBLIC):
    in_window("record-entry", now)
    get = get or curl_get
    log = read_log(off); pinned(log); first_write("entry", log)
    fz = get_kind(log, "freeze"); need(fz, "no frozen list")
    clears = parse_clear(clear, {"GENUINE_MOVE", "IDENTITY_BREAK"})
    raw, why, closes, flagged = {}, {}, {}, []
    for t in fz["roster"] + [CFG["benchmark"]]:
        rows, p1 = read_bars(get, t, ANCHOR, ENTRY, "raw")
        adj, p2 = read_bars(get, t, ANCHOR, ENTRY, "split")
        spl, p3 = read_splits(get, t, ANCHOR, ENTRY)
        raw[t] = dict(bars_raw=p1, bars_split=p2, splits=p3)
        try:
            c = closes_of(rows, RANK_DAYS); ca = closes_of(adj, RANK_DAYS)
        except C.Refused as e:
            why[t] = f"bars refused by the engine ({e})"; continue
        if not all(d in c for d in RANK_DAYS):
            why[t] = "missing or zero-volume session from anchor through entry"; continue
        if any(ANCHOR < d_(s["ex_date"]) <= ENTRY for s in spl) or split_steps(c, ca):
            why[t] = "split from anchor through entry (vendor record or raw versus split-adjusted step)"; continue
        for a, b in jumps(c):
            flagged.append((t, a, b))
        closes[t] = c
    B = CFG["benchmark"]
    need(B in closes, f"{B}: {why.get(B, 'not usable')}; the benchmark must have every session and no split")
    need(not [k for k in flagged if k[0] == B], f"{B} has an unexplained close jump; no clearance route for the benchmark")
    need(set(clears) == set(flagged), "flagged jumps and clearances differ: flagged " +
         ", ".join(f"{t} {a}..{b}" for t, a, b in sorted(flagged)) + "; give exactly one clearance per flagged pair")
    for (t, a, b), cl in clears.items():
        if cl["classification"] == "IDENTITY_BREAK" and t in closes:
            del closes[t]; why[t] = "identity break on or before entry"
    eligible = sorted(t for t in closes if t != B)
    rank = sorted(eligible, key=lambda t: (closes[t][FORMATION] / closes[t][ANCHOR], t))
    picks, tried, qraw = [], [], {}
    for t in rank:
        if len(picks) == CFG["picks"]:
            break
        h, hw, pages = half_spread(get, t, ENTRY); qraw[t] = pages
        cost = (h if h is not None else PROXY) + EXTRA
        shares = int(CFG["sleeve_usd"] // (closes[t][ENTRY] * (1 + cost)))
        tried.append(dict(ticker=t, shares=shares, proxy=h is None))
        if shares >= 1:
            picks.append(dict(ticker=t, rank=rank.index(t) + 1, shares=shares, entry_close=fs(closes[t][ENTRY]),
                              entry_half=fs(h if h is not None else PROXY), entry_proxied=h is None, proxy_reason=hw))
    need(len(picks) == CFG["picks"], "fewer than five eligible funds fit a $100 sleeve; the turn refuses")
    h, hw, pages = half_spread(get, B, ENTRY); qraw[B] = pages
    bcost = (h if h is not None else PROXY) + EXTRA
    bsh = int(CFG["capital"] // (closes[B][ENTRY] * (1 + bcost)))
    need(bsh >= 1, f"one {B} share does not fit $500")
    bench = dict(ticker=B, shares=bsh, entry_close=fs(closes[B][ENTRY]), entry_half=fs(h if h is not None else PROXY),
                 entry_proxied=h is None, proxy_reason=hw)
    rec = dict(sessions=dict(anchor=str(ANCHOR), formation=str(FORMATION), entry=str(ENTRY)), eligible=eligible,
               ineligible=why, ranked=[t for t in rank], picks=picks, skipped_unaffordable=[x["ticker"] for x in tried if x["shares"] < 1],
               benchmark=bench, clearances={f"{t},{a},{b}": v for (t, a, b), v in clears.items()},
               formation_returns={t: fs(closes[t][FORMATION] / closes[t][ANCHOR] - 1) for t in eligible})
    sha = write_packet(off, "entry_2026-12-31.json.gz", dict(record=rec, raw=raw, quotes=qraw))
    reasons = {}
    for v in why.values():
        reasons[v.split(" (")[0]] = reasons.get(v.split(" (")[0], 0) + 1
    append(dict(kind="entry", record=rec, packet_sha256=sha, made_utc=iso(now)),
           dict(kind="entry", entry_session=str(ENTRY), roster=len(fz["roster"]), eligible=len(eligible), ineligible_by_reason=reasons,
                held=len(picks), skipped_unaffordable=len(rec["skipped_unaffordable"]), jump_clearances=len(clears),
                entry_proxy_sides=sum(p["entry_proxied"] for p in picks) + bench["entry_proxied"], packet_sha256=sha,
                made_utc=iso(now)), off, pub)
    return dict(eligible=len(eligible), held=len(picks))


# ---- exits
def parse_cash(items):
    out = []
    for s in items:
        p = s.split(",", 4)
        need(len(p) == 5, "a cash event is TICKER,EX_DATE,AMOUNT,SOURCE_URL,SOURCE_KIND")
        t, ex, amt, u, k = p
        need(re.fullmatch(r"\d+(\.\d+)?", amt) and Fraction(amt) > 0, f"{t}: the amount must be a positive decimal")
        need(k in CASH_KINDS and re.fullmatch(r"https://\S+", u), f"{t}: source must be an https issuer, wire, SEC or exchange record")
        out.append(dict(ticker=t, ex_date=str(d_(ex)), amount=amt, source=u, source_kind=k))
    return out


def parse_status(items):
    out = {}
    for s in items:
        p = s.split(",", 2)
        need(len(p) == 3 and p[1] in CASH_STATUS and re.fullmatch(r"https://\S+", p[2]), "a status is TICKER,STATUS,CHECKED_URL")
        need(p[0] not in out, f"{p[0]}: two statuses"); out[p[0]] = dict(status=p[1], source=p[2])
    return out


def parse_splits(items):
    out = []
    for s in items:
        p = s.split(",", 3)
        need(len(p) == 4 and re.fullmatch(r"\d+/\d+", p[2]) and re.fullmatch(r"https://\S+", p[3]), "a split is TICKER,EX_DATE,NEW/OLD,URL")
        need(Fraction(p[2]) > 0, "the split ratio must be positive")
        out.append(dict(ticker=p[0], ex_date=str(d_(p[1])), ratio=p[2], source=p[3]))
    return out


def record_exit(kind, now, get=None, cash=(), status=(), splits=(), clear=(), off=OFF, pub=PUBLIC):
    cmd = {"exit5": "record-exit5", "exit_month": "record-exit-month"}[kind]
    in_window(cmd, now)
    get = get or curl_get
    log = read_log(off); pinned(log); first_write(kind, log)
    ent = get_kind(log, "entry"); need(ent, "no entry record; nothing is held")
    X = EXIT_DAY[kind]
    days = sessions(ENTRY, X)
    rec_e = ent["record"]; B = CFG["benchmark"]
    held = [p["ticker"] for p in rec_e["picks"]]
    names = held + [B]
    ev, st, sp = parse_cash(cash), parse_status(status), parse_splits(splits)
    clears = parse_clear(clear, {"GENUINE_MOVE"})
    need(set(st) == set(names), "give exactly one cash status for each held fund and the benchmark: " + " ".join(names))
    need(st[B]["status"] in ("documented", "none"), f"{B} cash must be documented or none")
    need(all(e["ticker"] in names for e in ev) and all(s["ticker"] in names for s in sp), "cash or split for a fund that is not held")
    need(not [s for s in sp if s["ticker"] == B], f"a {B} split refuses the turn")
    keys = [(e["ticker"], e["ex_date"], e["amount"]) for e in ev]
    need(len(keys) == len(set(keys)), "a cash event is repeated")
    if kind == "exit_month":
        e5 = get_kind(log, "exit5")
        if e5:
            early = {(e["ticker"], e["ex_date"], e["amount"]) for e in e5["record"]["cash"]}
            need(early <= set(keys), "the month exit must repeat every cash event credited at the fifth-session exit")
    raw, out, flagged, proxies, missing = {}, {}, [], 0, 0
    for t in names:
        rows, p1 = read_bars(get, t, ENTRY, X, "raw")
        adj, p2 = read_bars(get, t, ENTRY, X, "split")
        vs, p3 = read_splits(get, t, ENTRY + timedelta(days=1), X)
        try:
            c = closes_of(rows, days); ca = closes_of(adj, days)
        except C.Refused as e:
            raise Refuse(f"{t}: bars refused by the engine ({e})")
        pk = rec_e["benchmark"] if t == B else next(p for p in rec_e["picks"] if p["ticker"] == t)
        need(c.get(ENTRY) == Fraction(pk["entry_close"]), f"{t}: the entry close read now differs from the entry record")
        mine = sorted((s["ex_date"], s["ratio"]) for s in sp if s["ticker"] == t)
        vend = sorted(s["ex_date"] for s in vs)
        steps = sorted(str(d) for d in split_steps(c, ca))
        need(t != B or (not vend and not steps), f"{B} shows a split; the turn refuses")
        need(sorted(d for d, _ in mine) == vend, f"{t}: vendor split dates {vend} differ from the documented splits {[d for d, _ in mine]}")
        need(set(steps) <= set(vend), f"{t}: raw versus split-adjusted step on {steps} with no recorded split")
        for a, b in jumps(c, {d_(d) for d in vend}):
            flagged.append((t, a, b))
        last = max(c)
        miss = last != X
        eh = Fraction(pk["entry_half"])
        if miss:
            h, hw, qp, fee = None, "no usable exit bar", [], max(eh, PROXY) + EXTRA
        else:
            h, hw, qp = half_spread(get, t, X)
            fee = max(eh, h if h is not None else PROXY) + EXTRA
        raw[t] = dict(bars_raw=p1, bars_split=p2, splits=p3, quotes=qp)
        shares = Fraction(pk["shares"])
        def held_on(d, shares=shares, mine=mine):
            n = shares
            for x, r in mine:
                if ENTRY < d_(x) <= d:
                    n *= Fraction(r)
            return n
        mycash = [e for e in ev if e["ticker"] == t]
        for e in mycash:
            need(ENTRY < d_(e["ex_date"]) <= last, f"{t}: cash ex-date {e['ex_date']} is outside {ENTRY} < ex-date <= {last}")
        s_ = st[t]["status"]
        need((s_ in ("documented", "partial")) == bool(mycash), f"{t}: status {s_} does not match {len(mycash)} cash events")
        pay = sum((Fraction(e["amount"]) * held_on(d_(e["ex_date"])) for e in mycash), Fraction(0))
        cost_in = shares * Fraction(pk["entry_close"]) * (1 + Fraction(pk["entry_half"]) + EXTRA)
        value = held_on(last) * c[last] * (1 - fee)
        out[t] = dict(last_close_session=str(last), last_close=fs(c[last]), missing_exit=miss, exit_half=None if h is None else fs(h),
                      exit_proxied=(h is None) and not miss, proxy_reason=hw, exit_fee=fs(fee), cash=fs(pay), cash_status=s_,
                      net=fs(value + pay - cost_in), net_price_only=fs(value - cost_in), cash_events=len(mycash))
        proxies += (h is None) and not miss; missing += miss
    need(not [k for k in flagged if k[0] == B], f"{B} has an unexplained close jump; the turn refuses")
    need(set(clears) == set(flagged), "flagged jumps after entry and clearances differ: flagged " +
         ", ".join(f"{t} {a}..{b}" for t, a, b in sorted(flagged)) + "; only GENUINE_MOVE clears a held fund")
    cap = Fraction(CFG["capital"])
    port = sum(Fraction(out[t]["net"]) for t in held) / cap
    port_p = sum(Fraction(out[t]["net_price_only"]) for t in held) / cap
    bench = Fraction(out[B]["net"]) / cap
    bench_p = Fraction(out[B]["net_price_only"]) / cap
    res = dict(portfolio_pct=pct(port), pcef_pct=pct(bench), portfolio_minus_pcef_pct=pct(port - bench),
               portfolio_price_only_pct=pct(port_p), pcef_price_only_pct=pct(bench_p),
               portfolio_minus_pcef_price_only_pct=pct(port_p - bench_p))
    record = dict(exit_session=str(X), funds=out, cash=ev, statuses=st, splits=sp,
                  clearances={f"{t},{a},{b}": v for (t, a, b), v in clears.items()}, result=res)
    sha = write_packet(off, f"{kind}_{X}.json.gz", dict(record=record, raw=raw))
    gaps = sum(st[t]["status"] in ("partial", "unresolved") for t in held)
    append(dict(kind=kind, record=record, packet_sha256=sha, made_utc=iso(now)),
           dict(kind=kind, exit_session=str(X), held=len(held), missing_exits=missing, exit_proxy_sides=proxies,
                held_cash_gaps=gaps, held_cash_events=sum(out[t]["cash_events"] for t in held), held_splits=len(sp),
                jump_clearances=len(clears), packet_sha256=sha, made_utc=iso(now), **res), off, pub)
    return res


def alive(now, off=OFF):
    log = read_log(off)
    return dict(started=bool(log), records=[x["kind"] for x in log], now_utc=iso(now),
                open_now=[c for c, (a, b) in WINDOWS.items() if a <= now < b])


def plan():
    return dict(card=CARD, turn=TURN, roster_cutoff=str(ROSTER_CUTOFF), anchor=str(ANCHOR), formation=str(FORMATION), entry=str(ENTRY),
                exit5=str(EXIT5), exit_month=str(EXITM), windows_utc={k: [iso(a), iso(b)] for k, (a, b) in WINDOWS.items()},
                sizing=dict(sleeve_usd=CFG["sleeve_usd"], picks=CFG["picks"], benchmark=CFG["benchmark"], benchmark_usd=CFG["capital"]),
                cost=CFG["cost"], split_check_ratio=CFG["split_check_ratio"], cash_kinds=sorted(CASH_KINDS))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan"); sub.add_parser("alive")
    s = sub.add_parser("freeze-list"); s.add_argument("--roster", required=True); s.add_argument("--exclusions", required=True)
    s = sub.add_parser("record-entry"); s.add_argument("--clear", action="append", default=[], help="TICKER,EARLIER,LATER,CLASS,URL")
    for name in ("record-exit5", "record-exit-month"):
        s = sub.add_parser(name)
        s.add_argument("--cash", action="append", default=[], help="TICKER,EX_DATE,AMOUNT,SOURCE_URL,SOURCE_KIND")
        s.add_argument("--status", action="append", default=[], help="TICKER,STATUS,CHECKED_URL (every held fund and PCEF)")
        s.add_argument("--split", action="append", default=[], help="TICKER,EX_DATE,NEW/OLD,URL")
        s.add_argument("--clear", action="append", default=[], help="TICKER,EARLIER,LATER,GENUINE_MOVE,URL")
    a = ap.parse_args(argv); now = datetime.now(UTC)
    try:
        if a.cmd == "plan":
            print(json.dumps(plan(), indent=1))
        elif a.cmd == "alive":
            print(json.dumps(alive(now), indent=1))
        elif a.cmd == "freeze-list":
            fz = freeze_list(a.roster, a.exclusions, now)
            print("frozen", len(fz["roster"]), "funds, roster SHA-256", fz["roster_sha256"])
        elif a.cmd == "record-entry":
            r = record_entry(now, clear=a.clear); print("entry recorded:", r["eligible"], "eligible,", r["held"], "held")
        else:
            k = "exit5" if a.cmd == "record-exit5" else "exit_month"
            record_exit(k, now, cash=a.cash, status=a.status, splits=a.split, clear=a.clear)
            print(k, "recorded; see the public log")
    except (Refuse, C.Refused) as e:
        print("Refused, nothing written:", e); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
