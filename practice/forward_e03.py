"""E03: scan EDGAR, then manually record an odd-lot offer, its entry and outcome."""
import argparse
import fcntl
import json
import os
import re
import sys
import tempfile
import time
from datetime import date, datetime, time as clock, timedelta
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research_rig import common_21 as plan

CARD = "practice/traders/E03_odd_lot_tender_watch.md"
LOG = ROOT / "practice/forward/E03_log.json"
PRIVATE = Path("/home/user/workspace/rig/data/forward_e03")
SEC = "https://www.sec.gov"
ATOM = "/cgi-bin/browse-edgar?" + urlencode(
    dict(action="getcurrent", type="SC TO-I", owner="include", count=100, output="atom"))
NS = {"a": "http://www.w3.org/2005/Atom"}
FORMS = {"SC TO-I", "SC TO-I/A"}
ACC = r"[0-9]{10}-[0-9]{2}-[0-9]{6}"
IDX = re.compile(rf"edgar/data/(?P<cik>[0-9]+)/(?P<acc>{ACC})\.txt")
DETAIL = re.compile(rf"/Archives/edgar/data/(?P<cik>[0-9]+)/(?P<compact>[0-9]{{18}})/(?P<acc>{ACC})-index\.html?")
HOLIDAYS = frozenset("""
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19
2026-07-03 2026-09-07 2026-11-26 2026-12-25
2027-01-01 2027-01-18 2027-02-15 2027-03-26 2027-05-31 2027-06-18
2027-07-05 2027-09-06 2027-11-25 2027-12-24
""".split())
FIRST, LAST = date(2026, 1, 1), date(2027, 12, 31)


def need(ok, why):
    if not ok:
        raise ValueError(why)


def fields(obj, required, optional=()):
    need(isinstance(obj, dict) and set(required) <= obj.keys() <= set(required) | set(optional),
         "packet fields do not match the card")


def utc(t):
    return t.astimezone(plan.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def calendar():
    days = (FIRST + timedelta(days=i) for i in range((LAST - FIRST).days + 1))
    return plan.Calendar.from_rows(
        {"date": str(d), "open_utc": utc(datetime.combine(d, clock(9, 30), plan.ET))}
        for d in days if d.weekday() < 5 and str(d) not in HOLIDAYS)


def enc(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value):
    return sha256(enc(value)).hexdigest()


def dated(stamp, now):
    dt = plan.stamp(stamp)
    need(dt <= now and FIRST <= dt.astimezone(plan.ET).date() <= LAST, "filing time is future or outside the watch calendar")
    return dt


def expiry(s):
    day = date.fromisoformat(s)
    need(str(day) == s and FIRST < day <= LAST, "expiry is outside the watch calendar")
    return day


def accession(s):
    need(isinstance(s, str) and re.fullmatch(ACC, s), "invalid accession")
    return s


def sec_doc(url, cik, acc=None):
    u = urlsplit(url)
    m = re.fullmatch(r"/Archives/edgar/data/([0-9]+)/([0-9]{18})/[A-Za-z0-9_.()-]+", u.path)
    need(u.scheme == "https" and u.netloc == "www.sec.gov" and not (u.query or u.fragment)
         and m and int(m[1]) == int(cik) and (acc is None or m[2] == acc.replace("-", "")),
         "use the matching SEC Archives filing or exhibit URL")
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Edgar:
    def __init__(self, agent):
        need(agent and re.search(r"\S+@\S+\.\S+", agent) and "\n" not in agent and "\r" not in agent,
             "set E03_SEC_USER_AGENT to an organization and real contact email")
        self.agent, self.last = agent, 0
        self.opener = build_opener(NoRedirect)

    def __call__(self, path):
        time.sleep(max(0, self.last + .4 - time.monotonic()))
        self.last = time.monotonic()
        with self.opener.open(Request(SEC + path, headers={"User-Agent": self.agent}), timeout=45) as r:
            body = r.read(32 * 1024 * 1024 + 1)
        need(len(body) <= 32 * 1024 * 1024, "SEC response exceeds size limit")
        return body


def index_rows(body):
    header = "CIK|Company Name|Form Type|Date Filed|Filename"
    lines = body.decode("latin-1").splitlines()
    need(header in lines, "unexpected SEC master index")
    for line in lines[lines.index(header) + 2:]:
        if not line:
            continue
        cik, name, form, day, path = line.split("|")
        if form not in FORMS:
            continue
        match = IDX.fullmatch(path)
        need(match and int(cik) == int(match["cik"]), "bad index accession path")
        acc = match["acc"]
        url = f"{SEC}/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{acc}-index.htm"
        yield acc, form, date.fromisoformat(day), name, url, None


def atom_rows(body):
    root = ElementTree.fromstring(body)
    need(root.tag == f"{{{NS['a']}}}feed" and root.find("a:updated", NS) is not None, "unexpected SEC live feed")
    for item in root.findall("a:entry", NS):
        form = item.find("a:category", NS).attrib["term"]
        if form not in FORMS:
            continue
        url = item.find("a:link[@rel='alternate']", NS).attrib["href"]
        match = DETAIL.fullmatch(urlsplit(url).path)
        need(match and match["compact"] == match["acc"].replace("-", ""), "bad live feed accession path")
        sec_doc(url, match["cik"], match["acc"])
        t = datetime.fromisoformat(item.findtext("a:updated", namespaces=NS))
        day = re.search(r"Filed:</b>\s*([0-9-]{10})", item.findtext("a:summary", namespaces=NS))
        need(t.tzinfo and day, "missing filing date or acceptance time")
        name = item.findtext("a:title", namespaces=NS).split(" - ", 1)[1]
        name = re.sub(r"\s+\([0-9]+\)(?: \([^)]*\))?$", "", name)
        yield match["acc"], form, date.fromisoformat(day[1]), name, url, utc(t)


def scan(since, today, get):
    need(FIRST <= since <= today and (today - since).days <= 93, "scan range must be at most 93 days")
    days = (since + timedelta(days=i) for i in range((today - since).days + 1))
    starts = sorted({(day.year, (day.month - 1) // 3 + 1) for day in days})
    indexed = {}
    for y, q in starts:
        for row in index_rows(get(f"/Archives/edgar/full-index/{y}/QTR{q}/master.idx")):
            indexed[row[0]] = row
    live = list(atom_rows(get(ATOM)))
    need(len(live) < 100 or min(row[2] for row in live) < today,
         "today filled the live window; wait for the index or check the additional filing pages")
    for row in live:
        if row[0] in indexed:
            need(row[1:3] == indexed[row[0]][1:3], "live feed and index disagree on a filing")
        indexed[row[0]] = row
    return sorted((row for row in indexed.values() if since <= row[2] <= today), key=lambda r: (r[2], r[0]))


def positive(v):
    n = plan.money(v)
    need(n > 0, "expected a positive amount")
    return n


def checked_confirm(acc, p, now):
    fields(p, {"cik", "issuer", "symbol", "filing_date", "acceptance_utc", "offer_type",
               "floor", "initial_expiry", "quote", "url", "review", "review_url"})
    accepted = dated(p["acceptance_utc"], now)
    start = expiry(p["filing_date"])
    need(accepted.astimezone(plan.ET).date() <= start <= accepted.astimezone(plan.ET).date() + timedelta(days=7),
         "original filing date does not match acceptance")
    need(re.fullmatch(r"[0-9]{1,10}", p["cik"]) and re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", p["symbol"])
         and isinstance(p["issuer"], str) and 1 <= len(p["issuer"].strip()) <= 160, "bad issuer, CIK or ticker")
    sec_doc(p["url"], p["cik"], acc)
    sec_doc(p["review_url"], p["cik"])
    need(isinstance(p["quote"], str) and 20 <= len(p["quote"].strip()) <= 3500, "record the operative odd-lot quote")
    need(p["review"] in ("eligible", "eligible_form_wording", "eligible_signature_date", "eligible_both_flags"),
         "require confirmed all-cash listed common shares and affirmative beneficial priority")
    need(p["offer_type"] in ("fixed", "dutch_auction") and expiry(p["initial_expiry"]) >= start, "invalid offer terms")
    positive(p["floor"])
    return {"issuer": p["issuer"], "cik": p["cik"], "symbol": p["symbol"], "filing_date": p["filing_date"],
            "accepted_utc": p["acceptance_utc"], "initial_expiry": p["initial_expiry"], "offer_type": p["offer_type"],
            "priority_quote": p["quote"], "offer_url": p["url"], "review_url": p["review_url"], "review": p["review"]}


def checked_amend(acc, p, original, now):
    fields(p, {"acceptance_utc", "url"}, {"new_expiry", "new_floor", "terminal_notice", "note"})
    need(dated(p["acceptance_utc"], now) > plan.stamp(original["acceptance_utc"]), "amendment is not after original")
    sec_doc(p["url"], original["cik"], acc)
    if "new_expiry" in p:
        need(expiry(p["new_expiry"]) >= plan.stamp(p["acceptance_utc"]).astimezone(plan.ET).date(), "amendment expiry precedes acceptance")
    if "new_floor" in p:
        positive(p["new_floor"])
    if "terminal_notice" in p:
        need(p["terminal_notice"] in ("completed", "withdrawn"), "not a terminal notice")
    if "note" in p:
        need(isinstance(p["note"], str) and len(p["note"]) <= 2000, "invalid filing note")
    return {"accepted_utc": p["acceptance_utc"], "filing_url": p["url"], "new_expiry": p.get("new_expiry"),
            "terminal_notice": p.get("terminal_notice")}


def modeled(acc, original, amendments, cal, result=None, actions=()):
    for am in amendments:
        if "new_expiry" in am:
            expiry(am["new_expiry"])
    p = plan.POLICY | {"result_cutoff": str(LAST)}
    row = original | {"accession": acc, "priority": "yes", "amendments": sorted(amendments, key=lambda a: a["acceptance_utc"]),
                      "corporate_actions": actions, "known_terminal_by_cutoff": result is not None, "result": result}
    if result is not None:
        row["final_expiry"] = result["final_expiry"]
    return plan.schedule(row, cal, p)


def pending(acc, original, ams, cal):
    event = modeled(acc, original, ams, cal)
    lag = timedelta(minutes=plan.POLICY["lag_minutes"])
    if not event.no_trade and any(a.get("terminal_notice") and
            plan.stamp(a["acceptance_utc"]) + lag <= cal.open_of(event.entry) for a in ams):
        return replace(event, no_trade="outcome_already_known")
    return event


def open_bar(p, symbol, session):
    fields(p, {"symbol", "feed", "adjustment", "session", "open", "volume", "source"})
    need((p["symbol"], p["feed"], p["adjustment"], p["session"]) == (symbol, "sip", "raw", str(session))
         and isinstance(p["source"], str) and p["source"].startswith("https://data.alpaca.markets/")
         and positive(p["volume"]), "use the verified nonzero-volume raw SIP opening print for the modeled session")
    o = positive(p["open"])
    return plan.Bar(o, o, o, o, plan.money(p["volume"]))


def checked_entry(event, p, cal, now, confirmed):
    fields(p, {"filings_checked_through", "tape_review"}, {"bar"})
    opening = cal.open_of(event.entry)
    need(opening <= dated(p["filings_checked_through"], now), "check amendments and any early terminal result through the entry open")
    need(isinstance(p["tape_review"], str) and 20 <= len(p["tape_review"]) <= 3000,
         "document the as-of tape identity, opening print and stale-bar check (or why no bar was needed)")
    same_day = now.astimezone(plan.ET).date() == event.entry
    timely = same_day and confirmed.astimezone(plan.ET).date() <= event.entry
    line = {"entry_session": str(event.entry), "same_day": timely, "action": "no_trade", "reason": event.no_trade}
    if event.no_trade:
        need("bar" not in p, "do not read a bar when the filing clock rules out entry")
        return line
    price = open_bar(p["bar"], event.row["symbol"], event.entry).o
    discount = (1 - price / event.entry_floor) * 10_000
    shares = plan.shares_at(price)
    threshold = 1 - plan.money(plan.POLICY["min_discount_bps"]) / 10_000
    reason = ("entry_discount" if price > event.entry_floor * threshold
              else "zero_affordable_shares" if not shares else None)
    return line | {"discount_bps": float(round(discount, 4)), "action": "pretend_entry" if not reason else "no_trade",
                   "shares": shares if not reason else 0, "reason": reason}


def checked_outcome(offer, original, amendments, entry, entry_summary, p, cal, now):
    fields(p, {"accession", "acceptance_utc", "url", "status", "final_expiry"}, {"price", "price_url", "payment_date",
           "corporate_actions", "coverage_through", "coverage_note", "exit_bars", "note"})
    acc = accession(p["accession"])
    need(acc != offer and dated(p["acceptance_utc"], now) > plan.stamp(original["acceptance_utc"]), "bad terminal filing time")
    sec_doc(p["url"], original["cik"], acc)
    end = expiry(p["final_expiry"])
    latest = sorted(amendments, key=lambda am: am["acceptance_utc"])
    need(str(end) == next((am["new_expiry"] for am in reversed(latest) if "new_expiry" in am), original["initial_expiry"]),
         "final expiry does not match the recorded filing history")
    need(p["status"] in ("completed", "withdrawn"), "use the filed terminal status")
    result = {"status": p["status"], "acceptance_utc": p["acceptance_utc"], "accession": acc, "final_expiry": str(end)}
    if p["status"] == "completed":
        need(end <= plan.stamp(p["acceptance_utc"]).astimezone(plan.ET).date(), "completion filing precedes expiry")
        result["price"] = str(positive(p["price"]))
        if p.get("price_url"):
            sec_doc(p["price_url"], original["cik"])
        if p.get("payment_date"):
            result["payment_date"] = str(expiry(p["payment_date"]))
    else:
        need(not ({"price", "price_url", "payment_date"} & p.keys()), "withdrawal is a market exit")
    line = {"status": p["status"], "terminal_accession": acc, "filing_url": p["url"], "final_expiry": str(end)}
    if not entry_summary or entry_summary["action"] != "pretend_entry":
        return line | {"pretend_trade": False}
    need(isinstance(p.get("coverage_note"), str) and len(p["coverage_note"]) >= 20,
         "record corporate-action evidence through the modeled window")
    acts = p["corporate_actions"]
    for a in acts:
        fields(a, {"kind", "date", "url"}, {"ratio", "payment_date", "cash_per_share"})
        need(plan.cited(a["url"]), "record action evidence URL")
        day = expiry(a["date"])
        if a["kind"] == "cash_distribution":
            need(expiry(a["payment_date"]) >= day, "distribution pay date precedes ex-date")
            positive(a["cash_per_share"])
        else:
            need(a["kind"] == "split", "unresolved noncash action")
            positive(a["ratio"])
    need([a["date"] for a in acts] == sorted(a["date"] for a in acts), "sort corporate actions by effective date")
    event = modeled(offer, original, amendments, cal, result, acts)
    need(not event.no_trade and str(event.entry) == entry_summary["entry_session"], "terminal evidence invalidates entry; do not rewrite it")
    need(expiry(p["coverage_through"]) >= event.actions_through, "action review does not cover the required window")
    price = open_bar(entry["bar"], original["symbol"], event.entry).o
    need(float(round((1 - price / event.entry_floor) * 10_000, 4)) == entry_summary["discount_bps"],
         "late filing evidence changes the recorded entry floor; do not rewrite it")
    bars = {event.entry: open_bar(entry["bar"], original["symbol"], event.entry)}
    for bar in p["exit_bars"]:
        day = expiry(bar["session"])
        need(day in event.exit_candidates and day not in bars and cal.open_of(day) <= now, "wrong or unobserved exit open")
        bars[day] = open_bar(bar, original["symbol"], day)
    trade, reason = plan.simulate(event, bars, plan.POLICY["judged_fee_usd"])
    need(trade and not reason and trade["shares"] == entry_summary["shares"], "recorded entry does not reproduce")
    return line | {"pretend_trade": True, "exit_session": trade["exit"], "outcome": trade["outcome"],
                   "net_return_pct": round(trade["net_return"] * 100, 4), "same_day_entry": entry_summary["same_day"]}


def read_private(path):
    path = path.resolve(strict=True)
    need(path.is_file() and not path.is_relative_to(ROOT) and not any((p / ".git").exists() for p in path.parents)
         and not path.stat().st_mode & 0o077
         and path.stat().st_size <= 2_000_000, "use a small mode-0600 JSON packet outside the repo")
    return json.loads(path.read_bytes())


def verify(log, off):
    cur = json.loads(log.read_bytes()) if log.exists() else {"card": CARD, "records": []}
    need(cur["card"] == CARD, "wrong history card")
    seen, payloads, prev = set(), set(), None
    for r in cur["records"]:
        base = {k: v for k, v in r.items() if k != "sha256"}
        acc, phase, filing = accession(r["offer"]), r["phase"], accession(r["filing"])
        need(phase in {"confirm", "amend", "entry", "outcome"}, "invalid record phase")
        key = (acc, phase, filing if phase == "amend" else acc)
        need(key not in seen and r["previous_sha256"] == prev and digest(base) == r["sha256"], "E03 history chain mismatch")
        prev = r["sha256"]
        seen.add(key)
        payloads.add(prev + ".json")
        private = read_private(off / (prev + ".json"))
        need(digest(private) == r["private_sha256"], "private payload hash mismatch")
    need({p.name for p in off.glob("*.json") if re.fullmatch(r"[0-9a-f]{64}\.json", p.name)} == payloads,
         "unpaired private receipt; recover the log before writing")
    return cur


def write_once(log, off, acc, phase, filing, p, summary, ledger, now):
    records = ledger["records"]
    need(not any(r["offer"] == acc and r["phase"] == phase and (phase != "amend" or r["filing"] == filing)
                 for r in records), "this filing or stage is already recorded")
    base = {"offer": acc, "phase": phase, "filing": filing, "made_utc": utc(now), "summary": summary,
            "private_sha256": digest(p), "previous_sha256": records[-1]["sha256"] if records else None}
    r = base | {"sha256": digest(base)}
    with os.fdopen(os.open(off / (r["sha256"] + ".json"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as out:
        out.write(enc(p))
        out.flush()
        os.fsync(out.fileno())
    records.append(r)
    with tempfile.NamedTemporaryFile(dir=log.parent, delete=False) as tmp:
        try:
            tmp.write(enc(ledger))
            tmp.flush()
            os.fsync(tmp.fileno())
            os.replace(tmp.name, log)
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
    return r


def evidence(records, acc, off):
    history = [r for r in records if r["offer"] == acc]
    existing = {r["phase"]: r for r in history}
    payload = lambda r: read_private(off / (r["sha256"] + ".json"))
    ams = [payload(r) | {"accession": r["filing"]} for r in history if r["phase"] == "amend"]
    return existing, payload, ams


def show_plan(acc, log=LOG, off=PRIVATE):
    entries, payload, ams = evidence(verify(log, off)["records"], acc, off)
    need("confirm" in entries and "outcome" not in entries, "no confirmed open record for this offer")
    cal = calendar()
    event = pending(acc, payload(entries["confirm"]), ams, cal)
    info = entries["confirm"]["summary"]
    return f"E03 PLAN | {info['issuer']} ({info['symbol']}) | {acc} | first qualifying clock: {utc(cal.open_of(event.entry))} | {event.no_trade or 'check the entry discount after the open'}"


def record(phase, acc, filing, p, now, log=LOG, off=PRIVATE):
    accession(acc)
    accession(filing)
    off.mkdir(parents=True, mode=0o700, exist_ok=True)
    need(off.resolve() == off and not off.is_relative_to(ROOT) and not off.stat().st_mode & 0o077,
         "record directory must be private and off repo")
    log.parent.mkdir(parents=True, exist_ok=True)
    with (off / "history.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = verify(log, off)
        existing, payload, ams = evidence(ledger["records"], acc, off)
        cal = calendar()
        if phase == "confirm":
            summary = checked_confirm(acc, p, now)
        else:
            need("confirm" in existing and "outcome" not in existing, "confirm the original first; a terminal record closes the offer")
            original = payload(existing["confirm"])
            if phase == "amend":
                need(filing != acc and p.get("acceptance_utc") not in {a["acceptance_utc"] for a in ams},
                     "amendment accession and timestamp must be distinct")
                summary = checked_amend(filing, p, original, now)
            elif phase == "entry":
                event = pending(acc, original, ams, cal)
                summary = checked_entry(event, p, cal, now, plan.stamp(existing["confirm"]["made_utc"])) | {
                    "issuer": original["issuer"], "symbol": original["symbol"]}
                if any(a.get("terminal_notice") for a in ams):
                    summary["same_day"] = False
            else:
                e = existing.get("entry")
                summary = checked_outcome(acc, original, ams, payload(e) if e else None,
                                          e["summary"] if e else None, p, cal, now)
        return write_once(log, off, acc, phase, filing, p, summary, ledger, now)


def alert(offer, summary):
    if not summary["same_day"] or summary["reason"] not in (None, "zero_affordable_shares"):
        return None
    size = f"{summary['shares']} shares" if summary["shares"] else "no affordable whole share"
    return (f"E03 ALERT | {summary['issuer']} ({summary['symbol']}) {offer} | "
            f"{summary['entry_session']} opening discount {summary['discount_bps']:.2f} bps | "
            f"{size} | pretend money only; no order")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    recent = sub.add_parser("scan", help="read-only SEC filing inbox")
    recent.add_argument("--since", type=date.fromisoformat, help="inclusive filing date")
    sub.add_parser("plan", help="print the next modeled entry clock without any prices").add_argument("offer")
    for mode in ("confirm", "amend", "entry", "outcome"):
        step = sub.add_parser(mode)
        step.add_argument("offer", help="original SC TO-I accession")
        if mode == "amend":
            step.add_argument("filing", help="SC TO-I/A accession")
        step.add_argument("packet", type=Path)
    args = parser.parse_args()
    now = datetime.now(plan.UTC)
    today = now.astimezone(plan.ET).date()
    try:
        if args.mode == "scan":
            rows = scan(args.since or (today - timedelta(days=4)), today, Edgar(os.getenv("E03_SEC_USER_AGENT")))
            for acc, form, day, name, url, accepted in rows:
                kind = "CANDIDATE (confirm all-cash and odd-lot priority)" if form == "SC TO-I" else "AMENDMENT (link to original; check expiry, price terms or results)"
                print(f"{kind} | {day} | {name} | {form} {acc} | {accepted or 'acceptance on filing page'} | {url}")
            print(f"E03 EDGAR: {len(rows)} initial filings and amendments since {args.since or today - timedelta(days=4)}; screening required.")
            return 0
        if args.mode == "plan":
            print(show_plan(accession(args.offer)))
            return 0
        packet = read_private(args.packet)
        filing = args.filing if args.mode == "amend" else packet["accession"] if args.mode == "outcome" else args.offer
        r = record(args.mode, args.offer, filing, packet, now)
        print(enc(r).decode(), end="")
        if args.mode == "entry" and (line := alert(args.offer, r["summary"])):
            print(line)
    except (ValueError, OSError, ArithmeticError, KeyError, AttributeError, TypeError, ElementTree.ParseError):
        # Do not echo exception arguments or the private packet: they may contain raw prices.
        parser.exit(2, "E03 refused: check SEC availability, date and packet schema, verified filings, private history and duplicate records.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
