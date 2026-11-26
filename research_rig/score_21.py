"""Plan 21: pinned approvals, serial acquisition, silent validation, one-shot scoring."""
import argparse
import csv
from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import urlencode, urlsplit

import yaml

if __package__:
    from . import common_21 as C
else:
    import common_21 as C

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RUN = ROOT.parent / "rig/data/replay_21"
PLAN = "research_rig/PREREG_21_odd_lot_tenders.md"
CONFIG = "config/thresholds.yaml"
LEDGER = "research_rig/TRIAL_LEDGER.md"
QUEUE = "docs/QUEUE.md"
PIN_FILE = "research_rig/PINNED_21.json"
APPROVAL = "research_rig/APPROVAL_21.md"
APPROVAL_RE = (rb"Approved by the lead: plan 21, one custodian acquisition, validation and one scored run, "
               rb"freeze commit ([0-9a-f]{40}), freeze SHA-256 ([0-9a-f]{64}), "
               rb"event manifest SHA-256 ([0-9a-f]{64}), calendar SHA-256 ([0-9a-f]{64}), "
               rb"request scope SHA-256 ([0-9a-f]{64})\.\n")
PINNED = (PLAN, CONFIG, *(f"research_rig/{x}_21.py" for x in ("common", "score", "test")))
RESULT = HERE / "results_21.json"
LOCK = RUN / "score_21.lock"
EVENTS = RUN / "event_manifest_21.json"
SESSIONS = RUN / "calendar_21.csv"
BARS = RUN / "bars_21.json"
SCOPE = RUN / "request_scope_21.json"
ACQUIRE_LOCK = RUN / "acquire_21.lock"
BAR_FIELDS = tuple("tohlcv")
ENDPOINT = "https://data.alpaca.markets/v2/stocks/bars"
ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}")
SHA = re.compile(r"[a-f0-9]{64}")
SYMBOL = re.compile(r"[A-Z][A-Z0-9.\-]{0,14}")
NOTICE_DOMAINS = ("nyse.com","nasdaq.com","theocc.com","cboe.com","miaxglobal.com","iexexchange.io")
MAX_BYTES = 80 * 1024 * 1024


class Refused(Exception):
    """The public error exposes a fixed code and a path, never bar values."""
    def __init__(self, code, path):
        super().__init__(code)
        self.code, self.path = code, path


def digest(b):
    return sha256(b).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def safe_read(path, pin=None):
    if path.resolve() != path or not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise C.Incomplete("missing, linked or oversized input")
    b = path.read_bytes()
    if pin is not None and (not SHA.fullmatch(pin) or digest(b) != pin):
        raise C.Incomplete("incorrect pinned digest")
    return b


def authorize(commit, freeze_pin):
    if (HERE.name != "research_rig" or not re.fullmatch(r"[a-f0-9]{40}", commit or "")
            or not SHA.fullmatch(freeze_pin or "")):
        raise Refused("P21_AUTH_REFUSED", HERE)
    if git("rev-parse", "HEAD").decode().strip() != commit or git("status", "--porcelain", "--untracked-files=all"):
        raise Refused("P21_AUTH_REFUSED", ROOT)
    approval = re.fullmatch(APPROVAL_RE, git("show", f"{commit}:{APPROVAL}"))
    if not approval or git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", commit) != (
            f"A\t{APPROVAL}\n".encode()):
        raise Refused("P21_AUTH_REFUSED", ROOT / APPROVAL)
    freeze, expected_freeze_pin, *input_pins = (x.decode("ascii") for x in approval.groups())
    parents = git("rev-list", "--parents", "-n", "1", commit).decode().split()[1:]
    if len(parents) != 1 or expected_freeze_pin != freeze_pin:
        raise Refused("P21_AUTH_REFUSED", ROOT / APPROVAL)
    git("merge-base", "--is-ancestor", freeze, parents[0])
    package = safe_read(ROOT / PIN_FILE, freeze_pin)
    if any(package != git("show", f"{rev}:{PIN_FILE}") for rev in (freeze, commit)):
        raise Refused("P21_AUTH_REFUSED", ROOT / PIN_FILE)
    file_pins = json.loads(package)
    if set(file_pins) != set(PINNED):
        raise Refused("P21_AUTH_REFUSED", ROOT / PIN_FILE)
    approved = {}
    for relative in PINNED:
        try:
            approved[relative] = safe_read(ROOT / relative, file_pins[relative])
            if any(approved[relative] != git("show", f"{rev}:{relative}") for rev in (freeze, commit)):
                raise C.Incomplete("approved source differs")
        except Exception:
            raise Refused("P21_AUTH_REFUSED", ROOT / relative) from None
    plan = approved[PLAN]
    if [x for x in plan.splitlines() if x.startswith(b"Status ")] != [b"Status FROZEN."]:
        raise Refused("P21_AUTH_REFUSED", ROOT / PLAN)
    for name, row in ((LEDGER, 158), (QUEUE, 38)):
        prefix = f"| {row} |".encode()
        a, b = ([line for line in git("show", f"{rev}:{name}").splitlines() if line.startswith(prefix)]
                for rev in (freeze, commit))
        if len(a) != 1 or a != b or (b"`" + PLAN.encode() + b"`") not in a[0]:
            raise Refused("P21_AUTH_REFUSED", ROOT / name)
    if (RUN.resolve() != RUN or not RUN.is_dir() or RUN.stat().st_uid != os.geteuid()
            or RUN.stat().st_mode & 0o077):
        raise Refused("P21_AUTH_REFUSED", RUN)
    pins = {}
    for key, obj, expected in zip(("EVENT_MANIFEST_SHA256", "CALENDAR_SHA256", "REQUEST_SCOPE_SHA256"),
                                  (EVENTS, SESSIONS, SCOPE), input_pins):
        matches = re.findall((rf"(?m)^{key}: ([a-f0-9]{{64}})$").encode(), plan)
        if matches != [expected.encode("ascii")]:
            raise Refused("P21_AUTH_REFUSED", obj)
        pins[obj] = expected
    p = C.policy(yaml.safe_load(approved[CONFIG])["replay_21_plan"]["value"])
    return p, pins, file_pins, freeze


def valid_ref(row):
    if not ACCESSION.fullmatch(row["accession"]) or not C.cited(row["url"]) or "sec.gov/" not in row["url"]:
        raise C.Incomplete("missing filing accession or SEC source")
    return C.stamp(row["acceptance_utc"])


def distribution_source(url):
    if not C.cited(url):
        return False
    u = urlsplit(url)
    host = u.hostname or ""
    if u.username is not None or u.password is not None:
        return False
    if host in ("sec.gov","www.sec.gov"):
        return u.path.lower().startswith("/archives/edgar/data/")
    return any(host == d or host.endswith("." + d) for d in NOTICE_DOMAINS)


def press_release_dividend_dates(row):
    """Validate the pin for any approved third-tier ordinary dividend date evidence."""
    flag, sources = row.get("div_source_ir",0), row.get("div_source_ir_evidence",[])
    if type(flag) is not int or flag not in (0,1) or type(sources) is not list or bool(sources) != bool(flag):
        raise C.Incomplete("inconsistent issuer dividend release provenance")
    dates = set()
    for s in sources:
        url = s["url"]
        if not C.cited(url) or not urlsplit(url).hostname or not SHA.fullmatch(s["sha256"]) or (
                not distribution_source(s["amount_source_url"])):
            raise C.Incomplete("unverifiable issuer dividend release provenance")
        C.stamp(s["fetched_at_utc"])
        record, pay = C.d(s["record_date"]), C.d(s["payment_date"])
        if record > pay:
            raise C.Incomplete("issuer dividend release payment precedes record")
        dates.add((url, record, pay))
    return dates


def reviewed_events(data, cal, p):
    """All eligibility classifications are from the pinned, reviewer-approved SEC metadata."""
    if data.get("status") != "REVIEWED" or data.get("version") != 1 or not SHA.fullmatch(data["audit_sha256"]):
        raise C.Incomplete("filing manifest is still a draft")
    if not data.get("independent_sample_review") or not data.get("events"):
        raise C.Incomplete("missing manifest audit declaration")
    candidates, missing, seen, same_event = [], {}, set(), set()
    beneficial_silence = discretionary_priority = missing_dividend_dates = missing_action_coverage = 0
    dates_end = C.d(p["bar_end"])
    end = datetime.combine(C.d(p["result_cutoff"]) + timedelta(days=1), time(), C.ET)
    for row in data["events"]:
        a = row["accession"]
        if not ACCESSION.fullmatch(a) or a in seen or row["filing_reviewed"] is not True:
            raise C.Incomplete("duplicate or unreviewed filing")
        seen.add(a)
        state = row["eligibility"]
        if state == "excluded":
            if not row["eligibility_reason"] or not C.cited(row["eligibility_source"]):
                raise C.Incomplete("unsubstantiated exclusion")
            beneficial_silence += row.get("eligibility_reason_code") == "beneficial_priority_silent"
            discretionary_priority += row.get("eligibility_reason_code") == "odd_lot_priority_discretionary"
            missing_dividend_dates += row.get("eligibility_reason_code") == "ordinary_dividend_dates_unresolved"
            missing_action_coverage += row.get("eligibility_reason_code") == "corporate_action_coverage_unverified"
            continue
        if (state != "eligible" or row["priority"] not in {"yes", "no"}
                or row["offer_type"] not in {"fixed", "dutch_auction"}
                or not p["start"] <= row["filing_date"] <= p["result_cutoff"]
                or not C.cited(row["listing_url"]) or not row.get("listing_quote")
                or not SYMBOL.fullmatch(row["ticker"]) or not row["identity"]
                or C.money(row["floor"]) <= 0 or not row["initial_expiry"]):
            raise C.Incomplete("unresolved security, timing or original terms")
        if row["priority"] == "yes" and (not C.cited(row["clause_url"]) or not row["odd_lot_quote"]):
            raise C.Incomplete("no operative priority quote")
        if row["priority"] == "yes" and (type(row.get("form_wording")) is not int or row["form_wording"] not in (0, 1)):
            raise C.Incomplete("invalid form wording flag")
        own_date = row.get("own_date_wording", 0)
        if type(own_date) is not int or own_date not in (0,1):
            raise C.Incomplete("invalid own-date wording flag")
        ir_dates = press_release_dividend_dates(row)
        for action in row["corporate_actions"]:
            if action["kind"] != "cash_distribution":
                continue
            for key in ("source","payment_source"):
                url = action.get(key)
                if not distribution_source(url) and (
                        action.get("distribution_type") != "ordinary" or not ir_dates or
                        (url,C.d(action["record_date"]),C.d(action["payment_date"])) not in ir_dates):
                    raise C.Incomplete("distribution evidence outside approved sources")
        initial = valid_ref(dict(accession=a, url=row["original_url"], acceptance_utc=row["acceptance_utc"]))
        if initial >= end:
            raise C.Incomplete("acceptance outside the filing window")
        uid = (row["identity"], row["filing_date"], row["initial_expiry"], row["floor"])
        if uid in same_event:
            raise C.Incomplete("same security and offer terms counted twice")
        same_event.add(uid)
        prior = initial
        if not row.get("amendment_review_complete"):
            raise C.Incomplete("unreviewed material-amendment chronology")
        linked = set()
        for am in row["amendments"]:
            am_t = valid_ref(am)
            if am_t < prior or am["accession"] in linked or not am.get("reviewed"):
                raise C.Incomplete("invalid or unreviewed amendment chronology")
            if any(am.get(k) for k in ("new_floor", "new_size", "new_expiry")) and (
                    not am.get("material_quote") or not C.cited(am.get("material_url"))):
                raise C.Incomplete("material amendment lacks cited text")
            prior = am_t
            linked.add(am["accession"])
        res = row["result"]
        matched = bool(res and res["status"] in {"completed", "withdrawn"} and valid_ref(res) < end
                       and res["filing_date"] <= p["result_cutoff"])
        if matched != row["known_terminal_by_cutoff"] or (matched and res["accession"] not in linked):
            raise C.Incomplete("inconsistent terminal outcome")
        if matched and res["status"] == "completed":
            if row["priority"] == "no" and res["proration"] is None:
                missing[a] = "no_priority_proration_unstated"
                continue
            if (C.money(res["price"]) <= 0 or not res.get("price_quote") or not res.get("payment_review_complete")
                    or (res.get("payment_date") and (not res.get("payment_quote")
                        or not ACCESSION.fullmatch(res["payment_source_accession"])
                        or not C.cited(res["payment_source_url"]))) or not row["final_expiry"]
                    or row["final_expiry_accession"] not in {a, *linked}
                    or not ACCESSION.fullmatch(res["price_source_accession"]) or not C.cited(res["price_source_url"])
                    or res["price_source_kind"] not in {"result_amendment", "incorporated_result_exhibit",
                                                        "final price from later issuer filing"}):
                raise C.Incomplete("unresolved completed-offer cash or expiry")
            if row["priority"] == "no" and not 0 <= C.money(res["proration"]) <= 1:
                raise C.Incomplete("invalid stated proration")
        if not matched and row["priority"] == "no":
            missing[a] = "no_priority_unresolved"
            continue
        e = C.schedule(row, cal, p)
        coverage_end = C.d(row["actions_reviewed_through"])
        if coverage_end < e.actions_through or not C.cited(row["actions_source"]):
            raise C.Incomplete("corporate action coverage missing")
        if not e.no_trade:
            old = None
            for action in row["corporate_actions"]:
                ad = C.d(action["date"])
                if old is not None and ad < old or not C.cited(action["source"]):
                    raise C.Incomplete("corporate action chronology or source")
                old = ad
                if not e.entry < ad <= e.terminal:
                    continue
                if action["kind"] == "split" and C.money(action["ratio"]) > 0:
                    continue
                if (action["kind"] == "cash_distribution" and C.money(action["cash_per_share"]) >= 0
                        and C.d(action["payment_date"]) >= ad and C.cited(action["payment_source"])):
                    dtype, derived = action.get("distribution_type"), action.get("ex_derived")
                    if dtype not in {"ordinary","special"} or type(derived) is not int or derived not in (0,1):
                        raise C.Incomplete("unclassified distribution or ex-date provenance")
                    if derived and (dtype != "ordinary" or C.ordinary_ex_date(cal,action["record_date"]) != ad):
                        raise C.Incomplete("invalid derived cash distribution ex-date")
                    continue
                raise C.Incomplete("unresolved corporate action")
            if e.market_end > dates_end:
                raise C.Incomplete("required fill is beyond the price cutoff")
        candidates.append(e)
    derived_counts = [sum(act.get("ex_derived") == 1 for act in e.row["corporate_actions"])
                      for e in candidates if e.row["priority"] == "yes"]
    return candidates, dict(data["summary"], shown_only_metadata_gaps=missing,
                            beneficial_priority_silent_exclusions=beneficial_silence,
                            odd_lot_priority_discretionary_exclusions=discretionary_priority,
                            ordinary_dividend_dates_unresolved_exclusions=missing_dividend_dates,
                            corporate_action_coverage_unverified_exclusions=missing_action_coverage,
                            own_date_wording_flagged_events=sum(e.row.get("own_date_wording",0) == 1
                                    for e in candidates if e.row["priority"] == "yes"),
                            issuer_dividend_release_flagged_events=sum(e.row.get("div_source_ir",0) == 1
                                    for e in candidates if e.row["priority"] == "yes"),
                            ordinary_ex_derived_distributions=sum(derived_counts),
                            ordinary_ex_derived_events=sum(n > 0 for n in derived_counts),
                            final_price_from_later_issuer_filing=sum(e.row["priority"] == "yes"
                                    and e.row["known_terminal_by_cutoff"]
                                    and e.row["result"].get("price_source_kind") == "final price from later issuer filing"
                                    for e in candidates),
                            unresolved_events=sum(e.row["priority"] == "yes" and
                                                  not e.row["known_terminal_by_cutoff"] for e in candidates))


def fetch(handle, symbol, asof, start, end, adjusted):
    """Only used in approved post-freeze acquisition. Never print HTTP response or handle."""
    q = dict(symbols=symbol, asof=asof.isoformat(), start=start.isoformat() + "T00:00:00Z",
             end=end.isoformat() + "T23:59:59Z",
             timeframe="1Day", feed="sip", adjustment=adjusted, limit=10000)
    rows, tokens = [], set()
    for _ in range(12):
        proc = subprocess.run(["pplx", "credentials", "run", handle, "--", "curl", "--fail",
                               "--silent", "--max-time", "120", ENDPOINT + "?" + urlencode(q)],
                              capture_output=True, check=True)
        data = json.loads(proc.stdout)
        packed = data["bars"] or {}
        if set(packed) - {symbol}:
            raise C.Incomplete("response symbol mismatch")
        rows.extend({field: row[field] for field in BAR_FIELDS} for row in (packed.get(symbol) or []))
        token = data.get("next_page_token")
        if not token:
            return rows
        if token in tokens:
            raise C.Incomplete("cyclic bar pagination")
        tokens.add(token)
        q["page_token"] = token
    raise C.Incomplete("too many bar pages")


def window(e, cal, p):
    # Use the five surrounding regular sessions needed for a five-run check, where bounded.
    start = cal.before_day(e.entry, p["stale_run"])
    end = min(C.d(p["bar_end"]), cal.after_day(e.market_end, p["stale_run"]))
    return start, end


def request_scope(events, cal, p):
    cases = {}
    for e in events:
        if e.required:
            start, end = window(e, cal, p)
            cases[e.accession] = dict(ticker=e.row["ticker"], start=start.isoformat(), end=end.isoformat(),
                                      filing_asof=e.row["filing_date"], entry_asof=e.entry.isoformat())
    return dict(version=1, endpoint=ENDPOINT, feed="sip", timeframe="1Day", fields=list(BAR_FIELDS),
                adjustments={"raw": "entry_asof/raw", "all": "entry_asof/all", "filing_all": "filing_asof/all"},
                through=p["bar_end"], cases=cases)


def acquire(events, cal, p, handle):
    if not re.fullmatch(r"custom-cred:[A-Za-z0-9-]+@data\.alpaca\.markets", handle or ""):
        raise Refused("P21_ACQUIRE_REFUSED", BARS)
    bundle = dict(version=1, feed="sip", endpoint=ENDPOINT, adjustments=["raw", "all"],
                  through=p["bar_end"], data={})
    for e in events:
        if not e.required:
            continue
        start, end = window(e, cal, p)
        symbol, filed = e.row["ticker"], C.d(e.row["filing_date"])
        bundle["data"][e.accession] = {
            "ticker": symbol, "identity": e.row["identity"], "start": start.isoformat(), "end": end.isoformat(),
            "entry_asof": e.entry.isoformat(), "filing_asof": filed.isoformat(),
            "raw": fetch(handle, symbol, e.entry, start, end, "raw"),
            "all": fetch(handle, symbol, e.entry, start, end, "all"),
            "filing_all": fetch(handle, symbol, filed, start, end, "all"),
        }
    return bundle


def tape(rows, allowed):
    b = {}
    for row in rows:
        timestamp = datetime.fromisoformat(row["t"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise C.Incomplete("daily bar timestamp has no offset")
        local = timestamp.astimezone(C.ET)
        day = local.date()
        if local.time() != time() or day in b or day not in allowed:
            raise C.Incomplete("daily bar not on expected session")
        b[day] = C.Bar.parse(row)
    return b


def validate_bundle(bundle, events, cal, p):
    """No returns or printed prices. All potential fill paths have to validate before lock."""
    if (bundle["version"] != 1 or bundle["feed"] != "sip" or bundle["endpoint"] != ENDPOINT
            or bundle["through"] != p["bar_end"] or bundle["adjustments"] != ["raw", "all"]):
        raise C.Incomplete("unexpected bar provenance")
    has_prices = [e for e in events if e.required]
    if set(bundle["data"]) != {e.accession for e in has_prices}:
        raise C.Incomplete("missing or extra bar files")
    verified, identities = {}, {}
    for e in has_prices:
        rec = bundle["data"][e.accession]
        start, end = window(e, cal, p)
        if (rec["ticker"] != e.row["ticker"] or rec["identity"] != e.row["identity"]
                or rec["entry_asof"] != e.entry.isoformat() or rec["filing_asof"] != e.row["filing_date"]
                or rec["start"] != start.isoformat() or rec["end"] != end.isoformat()):
            raise C.Incomplete("bar identity or request span mismatch")
        days = cal.between(start, end)
        raw, adj, corroborating = (tape(rec[k], set(days)) for k in ("raw", "all", "filing_all"))
        bad = C.stale_dates(days, adj, p["stale_run"])
        if any(k not in raw or k not in adj or k not in corroborating or k in bad
               or min(raw[k].v, adj[k].v, corroborating[k].v) <= 0 for k in e.required):
            raise C.Incomplete("required fill bar missing or stale")
        if not C.same_tape(adj, corroborating, days):
            raise C.Incomplete("as-of stock identity unconfirmed")
        # Quantity is inspected silently only for corporate-action feasibility. This
        # never evaluates the spread, computes a return, or selects a smaller sample.
        if e.row["corporate_actions"]:
            maximum = C.shares_at(raw[e.entry].o, p)
            # The shown-only single account may have less available cash. Verify every
            # smaller feasible lot, without projecting that account or computing returns.
            quantities = range(1, maximum + 1) if e.row["priority"] == "yes" else (maximum,)
            for exit_day in e.required - {e.entry}:
                ratio = C.unit_basis(e, exit_day)[0]
                if any(q * ratio != int(q * ratio) for q in quantities):
                    raise C.Incomplete("split can leave a fractional position with unresolved disposition")
            if e.mode == "completed":
                expiry = C.d(e.row["final_expiry"])
                ratio = C.unit_basis(e, expiry)[0]
                q = maximum * ratio
                if (any(n * ratio != int(n * ratio) for n in quantities)
                        or (e.row["priority"] == "yes" and q >= 100)):
                    raise C.Incomplete("split invalidates modeled tender eligibility")
                if e.row["priority"] == "no":
                    factor = C.money(e.row["result"]["proration"])
                    for day, reasons in e.exit_candidates.items():
                        if any(x[0] == "remainder" for x in reasons):
                            extra = (q - int(q * factor)) * C.unit_basis(e, day)[0] / C.unit_basis(e, expiry)[0]
                            if extra != int(extra):
                                raise C.Incomplete("split may leave a fractional prorated balance")
        # One security identity cannot be counted under separate issuer IDs; repeating offers by
        # the same identity are legitimate. Overlapping identical adjusted series under different
        # IDs are not counted twice; a reviewer must resolve the inferred alias before scoring.
        for other_id, other in identities.items():
            if other_id == rec["identity"]:
                continue
            common = sorted(set(adj).intersection(other))
            if len(common) >= 3 and all(adj[k].v == other[k].v > 0 and adj[k].flat_key == other[k].flat_key for k in common):
                raise C.Incomplete("overlapping tape counted under two security identities")
        identities.setdefault(rec["identity"], {}).update(adj)
        verified[e.accession] = raw
    return verified


def dump(stream, payload):
    json.dump(payload, stream, allow_nan=False, sort_keys=True, separators=(",", ":"))
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())


def sync(folder):
    fd = os.open(folder, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def claim(lock, result, job, prepare, calculate):
    if os.path.lexists(lock) or os.path.lexists(result):
        raise Refused("P21_CONSUMED", lock if os.path.lexists(lock) else result)
    validated = prepare()
    if os.path.lexists(result):
        raise Refused("P21_CONSUMED", result)
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise Refused("P21_CONSUMED", lock) from None
    with os.fdopen(fd, "w") as f:
        dump(f, dict(job, status="consumed"))
        sync(lock.parent)
        try:
            payload = calculate(validated)
            fd = os.open(result, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as output:
                dump(output, payload)
            sync(result.parent)
        except BaseException:
            dump(f, {"status": "failed"})
            raise
        dump(f, {"status": "completed", "output": result.name})


def run(commit, freeze_pin, bundle_pin=None, acquire_bars=False, validate_only=False):
    try:
        p, pins, source, freeze = authorize(commit, freeze_pin)
    except Refused:
        raise
    except Exception:
        raise Refused("P21_AUTH_REFUSED", ROOT / PLAN) from None
    if os.path.lexists(LOCK) or os.path.lexists(RESULT) or os.path.lexists(HERE / LOCK.name):
        raise Refused("P21_CONSUMED", LOCK)
    try:
        cal = C.Calendar.from_rows(csv.DictReader(safe_read(SESSIONS, pins[SESSIONS]).decode().splitlines()))
        if cal.days[0] > C.d("2015-12-15") or cal.days[-1] < C.d("2026-12-15"):
            raise C.Incomplete("calendar span is incomplete")
        events, meta = reviewed_events(json.loads(safe_read(EVENTS, pins[EVENTS])), cal, p)
        if json.loads(safe_read(SCOPE, pins[SCOPE])) != request_scope(events, cal, p):
            raise C.Incomplete("custodian request scope differs from frozen schedule")
    except (Exception, KeyboardInterrupt):
        raise Refused("P21_METADATA_REFUSED", EVENTS) from None
    if acquire_bars:
        try:
            if os.path.lexists(BARS):
                raise C.Incomplete("bar bundle already exists")
            handle = os.environ.get("PLAN21_ALPACA_HANDLE")
            if not re.fullmatch(r"custom-cred:[A-Za-z0-9-]+@data\.alpaca\.markets", handle or ""):
                raise C.Incomplete("named custodian handle missing")
            with os.fdopen(os.open(ACQUIRE_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as fh:
                dump(fh, dict(approval_commit=commit, freeze_commit=freeze, scope_sha256=pins[SCOPE]))
            sync(RUN)
            packet = acquire(events, cal, p, handle)
            fd = os.open(BARS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as fh:
                dump(fh, packet)
            sync(BARS.parent)
        except (Exception, KeyboardInterrupt):
            raise Refused("P21_ACQUIRE_REFUSED", BARS) from None
        print("bar bundle SHA-256:", digest(safe_read(BARS)))
        return
    if not SHA.fullmatch(bundle_pin or ""):
        raise Refused("P21_INVENTORY_REFUSED", BARS)
    job = dict(ledger=158, commit=commit, freeze_commit=freeze, freeze_sha256=freeze_pin, source_sha256=source,
               event_manifest_sha256=pins[EVENTS], calendar_sha256=pins[SESSIONS],
               request_scope_sha256=pins[SCOPE],
               bar_bundle_sha256=bundle_pin, started_utc=datetime.now(timezone.utc).isoformat())

    def prepare():
        try:
            st = BARS.stat()
            if not ACQUIRE_LOCK.is_file() or st.st_uid != os.geteuid() or st.st_mode & 0o777 != 0o600:
                raise C.Incomplete("missing custody or private bar bundle")
            if json.loads(safe_read(ACQUIRE_LOCK)) != dict(approval_commit=commit, freeze_commit=freeze,
                                                          scope_sha256=pins[SCOPE]):
                raise C.Incomplete("custody does not match approved scope")
            return validate_bundle(json.loads(safe_read(BARS, bundle_pin)), events, cal, p)
        except (Exception, KeyboardInterrupt):
            raise Refused("P21_TAPE_REFUSED", BARS) from None

    try:
        if validate_only:
            prepare()
            print("P21_VALIDATED")
            return
        claim(LOCK, RESULT, job, prepare, lambda t: dict(job=job, outcome=C.report(events, t, meta, p)))
    except Refused:
        raise
    except (Exception, KeyboardInterrupt):
        raise Refused("P21_SCORE_FAILED", LOCK) from None
    print("Plan 21 wrote its one-shot result.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    for flag in ("--self-test", "--calibration", "--acquire", "--validate-inputs", "--go"):
        mode.add_argument(flag, action="store_true")
    ap.add_argument("--approval-commit")
    ap.add_argument("--freeze-sha256")
    ap.add_argument("--bar-bundle-sha256")
    args = ap.parse_args()
    if args.self_test or args.calibration:
        if __package__:
            from . import test_21 as T
        else:
            import test_21 as T
        if args.calibration:
            T.calibrate(C.POLICY)
            return 0
        return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(T)).wasSuccessful() else 1
    try:
        os.nice(max(0, 10 - os.nice(0)))
        run(args.approval_commit, args.freeze_sha256, args.bar_bundle_sha256, args.acquire, args.validate_inputs)
    except Refused as e:
        print(e.code, e.path, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
