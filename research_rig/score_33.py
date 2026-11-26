"""Plan 33: validate pinned native SIP windows or claim one scored replay."""
import argparse
from bisect import bisect_right
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, localcontext
from hashlib import sha256
from io import StringIO
import json
import math
import os
from pathlib import Path
import re
import resource
import stat
from statistics import mean, median, stdev
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = Path("/home/user/workspace/rig/data")
INPUTS, RUN = DATA / "plan33_inputs", DATA / "replay_33"
PLAN, PINS, APPROVAL = "PREREG_33_treasury_auctions.md", "PINNED_33.json", "APPROVAL_33.md"
PIN_NAMES = {PLAN, "score_33.py", "test_33.py", "auction_calendar_33.csv",
             "nonbill_auction_days_33.txt", "control_pairs_33.csv", "sessions_33.csv",
             "fomc_dates_33.txt", "fees_33.csv"}
APPROVAL_RE = re.compile(
    rb"Approved by the lead: plan 33, validation and one scored run, freeze commit ([0-9a-f]{40}), "
    rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64})\.\n")
SHA = re.compile(r"[0-9a-f]{64}")
TS = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{1,9}))?Z")
PAGE = re.compile(r"native/[A-Za-z0-9][A-Za-z0-9_.-]{0,179}\.json")
ET = ZoneInfo("America/New_York")
CLOCKS = ("13:10", "15:59")
LANES = {"10-Year": "IEF", "30-Year": "TLT"}
YEARS = tuple(range(2016, 2027))
SAMPLE_END, END = date(2024, 7, 31), date(2026, 10, 31)
SHARES_CHANGE = date(2025, 11, 3)
CASH, BPS = Decimal(250), Decimal(10000)
NS, CENT = 1_000_000_000, Decimal(".01")
CAP = 16 * 1024 * 1024
CAL_HEADER = ("cusip", "auction_date", "announcemt_date", "closing_time_comp", "security_type",
              "security_term", "original_security_term", "reopening", "inflation_index_security",
              "pdf_filenm_announcemt")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P33_" + code)


def is_pin(value):
    return type(value) is str and SHA.fullmatch(value) is not None


def read_file(path, pin=None, size=None, private=False):
    need(path.resolve() == path, "FILE")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as f:
        s = os.fstat(f.fileno())
        need(stat.S_ISREG(s.st_mode) and s.st_size <= CAP, "FILE")
        if private:
            need(s.st_uid == os.geteuid() and not s.st_mode & 0o077, "PRIVATE")
        data = f.read(CAP + 1)
    need(len(data) <= CAP and (size is None or len(data) == s.st_size == size), "SIZE")
    need(pin is None or (is_pin(pin) and sha256(data).hexdigest() == pin), "HASH")
    return data


def private_dir(path):
    s = path.lstat()
    need(path.resolve() == path and stat.S_ISDIR(s.st_mode) and s.st_uid == os.geteuid()
         and not s.st_mode & 0o077, "PRIVATE")


def unique(pairs):
    obj = dict(pairs)
    need(len(obj) == len(pairs), "JSON_DUPLICATE")
    return obj


def reject_number(_):
    raise Refused("P33_JSON_NUMBER")


def decode(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_float=Decimal,
                      parse_constant=reject_number)


def object_fields(obj, fields, code):
    need(type(obj) is dict and set(obj) == set(fields), code)


def csv_rows(blob, header):
    rows = csv.reader(StringIO(blob.decode("ascii"), newline=""), strict=True)
    need(tuple(next(rows)) == header, "CSV_HEADER")
    for row in rows:
        need(len(row) == len(header) and all(row), "CSV_ROW")
        yield row


def day(text):
    d = date.fromisoformat(text)
    need(d.isoformat() == text, "DATE")
    return d


def timestamp(text):
    m = TS.fullmatch(text) if type(text) is str else None
    need(m is not None, "TIMESTAMP")
    dt = datetime.fromisoformat(m[1]).replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * NS + int((m[2] or "").ljust(9, "0"))


def clock_ns(d, clock):
    return int(datetime.fromisoformat(f"{d}T{clock}:00").replace(tzinfo=ET).timestamp()) * NS


def dates(blob):
    values = [day(x) for x in blob.decode("ascii").splitlines()]
    need(values == sorted(set(values)), "DATE_LIST")
    return set(values)


def regime(d):
    return d > SAMPLE_END


def quarter(d):
    return (d.month - 1) // 3


def plan_dates(blobs):
    exclusions = {
        (date(2019, 6, 21), "10-Year", "11:00 AM"),
        (date(2019, 11, 5), "10-Year", "01:00 PM"),
    }
    seen, omitted, auctions = set(), set(), {}
    for cusip, ds, anns, close, kind, term, orig, reopen, tips, pdf in csv_rows(
            blobs["auction_calendar_33.csv"], CAL_HEADER):
        d, ann = day(ds), day(anns)
        need((d, cusip) not in seen and d.year in YEARS and d <= END and ann <= d
             and re.fullmatch(r"[A-Z0-9]{9}", cusip) is not None and pdf.endswith(".pdf")
             and tips == "No" and reopen in ("Yes", "No")
             and (orig, kind) in {("10-Year", "Note"), ("30-Year", "Bond")}, "CALENDAR")
        seen.add((d, cusip))
        key = (d, orig, close)
        if key in exclusions:
            need(key not in omitted, "CALENDAR_EXCLUSION")
            omitted.add(key)
            continue
        terms = ("9-Year", "10-Year") if orig == "10-Year" else ("29-Year", "30-Year")
        need(d not in auctions and term.startswith(terms) and close == "01:00 PM"
             and 4 <= (d - ann).days <= 8, "CALENDAR")
        auctions[d] = LANES[orig]
    need(omitted == exclusions and len(seen) == 262 and len(auctions) == 260, "CALENDAR_COUNT")
    need(Counter((d.year, s) for d, s in auctions.items()) ==
         {(y, s): (10 if y == 2026 else 12) for y in YEARS for s in LANES.values()}
         and Counter(s for d, s in auctions.items() if regime(d)) == {"IEF": 27, "TLT": 27}, "CALENDAR_COUNT")
    blocked = dates(blobs["nonbill_auction_days_33.txt"])
    need(len(blocked) == 962 and set(auctions) | {x[0] for x in exclusions} <= blocked, "NONBILL")
    # The pinned projection includes every XNYS session (also half days), to rederive pairs
    # and prove a minimum gap even under the longest historical settlement lag.
    session = {}
    for ds, close in csv_rows(blobs["sessions_33.csv"], ("date", "close_et")):
        d = day(ds)
        need((not session or d > next(reversed(session))) and close in ("13:00", "14:00", "16:00"),
             "SESSIONS")
        session[d] = close
    need(next(iter(session)).year == 2016 and next(reversed(session)).year == 2026, "SESSIONS")
    supplied = []
    for ds, cs, s in csv_rows(blobs["control_pairs_33.csv"], ("auction", "control", "symbol")):
        supplied.append((day(ds), day(cs), s))
    eligible = {d for d, close in session.items() if close == "16:00" and d <= END} - blocked
    matches, todo = {}, []
    for d in sorted(auctions):
        need(session.get(d) == "16:00", "NOT_FULL_SESSION")
        pool = [c for c in eligible if (c.year, c.weekday(), quarter(c), regime(c)) ==
                (d.year, d.weekday(), quarter(d), regime(d))]
        if not pool:
            todo.append(d)
            continue
        c = min(pool, key=lambda c: (abs(c - d), c))
        matches[d] = c
        eligible.remove(c)
    need(todo == [date(2024, 7, 11)], "PAIR_FALLBACK")
    for d in todo:
        pool = [c for c in eligible if (c.year, c.weekday(), regime(c)) == (d.year, d.weekday(), regime(d))
                and abs((c - d).days) <= 42]
        need(bool(pool), "PAIR_FALLBACK")
        c = min(pool, key=lambda c: (abs(c - d), c))
        need(c == date(2024, 5, 30), "PAIR_FALLBACK")
        matches[d] = c
        eligible.remove(c)
    need(supplied == [(d, matches[d], auctions[d]) for d in sorted(auctions)], "PAIR_PIN")
    idx = {d: i for i, d in enumerate(session)}
    for position in (0, 1):
        for s in LANES.values():
            ids = sorted(idx[row[position]] for row in supplied if row[2] == s)
            need(all(b - a >= 5 for a, b in zip(ids, ids[1:])), "SETTLEMENT_GAP")
    return supplied


@dataclass(frozen=True)
class Quote:
    stamp: str
    ns: int
    bid: Decimal
    ask: Decimal
    bs: int
    az: int
    condition: tuple
    ordinal: int

    def regular(self, *, r_only=False):
        allowed = self.condition == ("R",) or (not r_only and self.condition == ("?",))
        return allowed and 0 < self.bid <= self.ask and self.bs > 0 and self.az > 0


def number(value):
    need(type(value) in (int, Decimal), "NATIVE_NUMBER")
    value = Decimal(value)
    # Guard representational magnitude, not observed prices or spreads.
    need(value.is_finite() and (not value or abs(value.adjusted()) <= 12)
         and len(value.as_tuple().digits) <= 32, "NATIVE_NUMBER")
    return value


def quote(row, d, ns, ordinal):
    object_fields(row, ("t", "bp", "ap", "bs", "as", "bx", "ax", "c", "z"), "QUOTE_ROW")
    need(all(type(row[x]) is int and 0 <= row[x] <= 2**31 - 1 for x in ("bs", "as"))
         and all(type(row[x]) is str and len(row[x]) <= 1 for x in ("bx", "ax"))
         and type(row["z"]) is str and row["z"] in ("A", "B", "C")
         and type(row["c"]) is list
         and all(type(x) is str and len(x) == 1 for x in row["c"]), "QUOTE_ROW")
    scale = 100 if d < SHARES_CHANGE else 1
    return Quote(row["t"], ns, number(row["bp"]), number(row["ap"]),
                 row["bs"] * scale, row["as"] * scale, tuple(row["c"]), ordinal)


def bar(row):
    object_fields(row, ("t", "o", "h", "l", "c", "v", "n", "vw"), "BAR_ROW")
    o, h, low, c, vw = (number(row[x]) for x in ("o", "h", "l", "c", "vw"))
    need(0 < low <= min(o, c) <= max(o, c) <= h and vw > 0
         and all(type(row[x]) is int and row[x] > 0 for x in ("v", "n")), "BAR_ROW")


def series(src, pages, kind, d, s, lo, used):
    need(type(pages) is list and 0 < len(pages) <= 64, "PAGES")
    hi = lo + 15 * NS if kind == "quotes" else lo
    token, tokens, previous, quotes, count = None, set(), lo, [], 0
    for i, p in enumerate(pages):
        object_fields(p, ("path", "sha256", "bytes", "page_token"), "PAGE")
        name = p["path"]
        need(type(name) is str and PAGE.fullmatch(name) and name not in used and is_pin(p["sha256"])
             and type(p["bytes"]) is int and 0 < p["bytes"] <= CAP
             and p["page_token"] == token, "PAGE")
        used.add(name)
        native = decode(read_file(src / name, p["sha256"], p["bytes"], private=True))
        object_fields(native, (kind, "next_page_token"), "NATIVE")
        token = native["next_page_token"]
        last = i == len(pages) - 1
        need((last and token is None) or
             (not last and type(token) is str and 0 < len(token) <= 4096 and token not in tokens),
             "PAGINATION")
        if token is not None:
            tokens.add(token)
        obj = native[kind]
        # Alpaca emits a null or empty symbol map for an empty multi-symbol response.
        need(obj is None or (type(obj) is dict and set(obj) <= {s}), "SYMBOL")
        rows = (obj or {}).get(s, [])
        need(type(rows) is list and len(rows) <= 10000 and (last or bool(rows)), "NATIVE_ROWS")
        for row in rows:
            need(type(row) is dict and "t" in row, "NATIVE_ROW")
            ns = timestamp(row["t"])
            need(lo <= ns <= hi and previous <= ns, "NATIVE_CLOCK_OR_ORDER")
            previous = ns
            count += 1
            if kind == "quotes":
                quotes.append(quote(row, d, ns, count))
            else:
                bar(row)
                need(count == 1, "BAR_DUPLICATE")
    return quotes if kind == "quotes" else bool(count)


def cat(shares):
    amt = Decimal(".000003") * shares
    return Decimal(0) if amt < CENT else amt.quantize(CENT, rounding=ROUND_HALF_UP)


def entry_size(ask):
    # Use exact affordability and monotonic CAT fees, including the rounding threshold.
    n, den = ask.as_integer_ratio()
    low, high = 0, int(CASH) * den // n + 1
    with localcontext() as ctx:
        ctx.prec = 80
        while high - low > 1:
            q = (high + low) // 2
            if q * ask + cat(q) <= CASH:
                low = q
            else:
                high = q
    return low


def select(entry, exit_, *, r_only=False):
    for x in entry:
        if x.regular(r_only=r_only):
            q = entry_size(x.ask)
            # No downsizing to displayed size or looking ahead at the exit.
            if 0 < q <= x.az:
                return x, next((y for y in exit_ if y.regular(r_only=r_only) and y.bs >= q), None), q
    return None, None, 0


@dataclass(frozen=True)
class Observation:
    day: date
    symbol: str
    entry: Quote | None
    exit: Quote | None
    size: int
    bars: tuple
    quote_rows: tuple
    exit_has_regular_quote: bool

    @property
    def placed(self):
        return self.entry is not None and self.exit is not None

    @property
    def missing(self):
        if self.entry is None:
            return ["entry"] if self.exit_has_regular_quote else ["entry", "exit"]
        return [] if self.exit is not None else ["exit"]


def observe(d, s, qs, bs, *, r_only=False):
    e, x, q = select(*qs, r_only=r_only)
    return Observation(d, s, e, x, q, tuple(bs), tuple(map(len, qs)),
                       any(y.regular(r_only=r_only) for y in qs[1]))


def load_inputs(src, pin, pairs, *, r_only_out=None):
    private_dir(src)
    private_dir(src / "native")
    manifest = decode(read_file(src / "manifest.json", pin, private=True))
    object_fields(manifest, ("schema", "feed", "windows"), "MANIFEST")
    need(manifest["schema"] == "plan33-alpaca-native-v1" and manifest["feed"] == "sip", "MANIFEST")
    expected = {(d, s, c) for a, b, s in pairs for d in (a, b) for c in CLOCKS}
    windows = manifest["windows"]
    need(type(windows) is list and len(windows) == len(expected), "WINDOW_COUNT")
    index = {}
    for w in windows:
        object_fields(w, ("date", "symbol", "clock", "quotes", "bars"), "WINDOW")
        k = (day(w["date"]), w["symbol"], w["clock"])
        need(k in expected and k not in index, "WINDOW_KEY")
        index[k] = w
    used, observations, errors = set(), {}, []
    for d, s in sorted({(d, s) for d, s, _ in expected}):
        qs, bs = [], []
        for c in CLOCKS:
            w = index[d, s, c]
            for kind, output in (("quotes", qs), ("bars", bs)):
                try:
                    output.append(series(src, w[kind], kind, d, s, clock_ns(d, c), used))
                except (Refused, KeyError, ValueError, TypeError, OSError, ArithmeticError) as exc:
                    errors.append(f"{d} {s} {c} {kind} " + (str(exc) if isinstance(exc, Refused) else "P33_BAD_NATIVE"))
        if len(qs) == len(bs) == 2:
            observations[d, s] = observe(d, s, qs, bs)
            if r_only_out is not None:
                r_only_out[d, s] = observe(d, s, qs, bs, r_only=True)
    if not errors:
        need({f"native/{p.name}" for p in (src / "native").iterdir()} == used, "EXTRA_NATIVE")
    return observations, errors


def fees_table(blob):
    result = {"SEC": [], "TAF": []}
    for label, ds, amount, cap, url in csv_rows(blob, ("fee", "effective_trade_date", "rate", "cap", "source")):
        need(label in result and url.startswith(("https://www.sec.gov/", "https://www.finra.org/")), "FEES")
        d, val, ceiling = day(ds), Decimal(amount), None if cap == "-" else Decimal(cap)
        rec = result[label]
        need(0 <= val and (not rec or d > rec[-1][0]) and
             ((label == "SEC" and ceiling is None) or (label == "TAF" and ceiling is not None and ceiling >= 0)),
             "FEES")
        rec.append((d, val, ceiling))
    need(all(rec and rec[0][0] <= date(2016, 1, 1) for rec in result.values()), "FEES")
    return result


def statutory(table, d, gross, shares):
    def rate(label):
        seq = table[label]
        ix = bisect_right([row[0] for row in seq], d) - 1
        need(ix >= 0, "FEE_DATE")
        return seq[ix][1:]
    sec, _ = rate("SEC")
    taf, cap = rate("TAF")
    return gross * sec / 1_000_000, min(shares * taf, cap)


def retail(table, d, gross, shares):
    sec, taf = statutory(table, d, gross, shares)
    return ((Decimal(0) if gross <= 500 else sec.quantize(CENT, rounding=ROUND_CEILING)),
            (Decimal(0) if shares <= 50 else taf.quantize(CENT, rounding=ROUND_HALF_UP)),
            cat(shares))


def trade(o, table, slip=0, unwaived=False):
    if not o.placed:
        return None
    a, b, q = o.entry, o.exit, o.size
    f = Decimal(slip) / BPS
    paid, gross = a.ask * (1 + f) * q + cat(q), b.bid * (1 - f) * q
    sec, taf, sell_cat = retail(table, o.day, gross, q)
    if unwaived:
        sec, taf = statutory(table, o.day, gross, q)
    payout = gross - sec - taf - sell_cat
    return {"net_bps": float(BPS * (payout - paid) / paid),
            "net_usd": float(payout - paid),
            "idle_usd": float(CASH - paid),
            "sec_usd": float(sec), "taf_usd": float(taf), "cat_usd": float(sell_cat + cat(q)),
            "entry_half_spread_bps": float(BPS * (a.ask - a.bid) / (a.ask + a.bid)),
            "exit_half_spread_bps": float(BPS * (b.ask - b.bid) / (b.ask + b.bid)),
            "entry_locked": a.ask == a.bid, "exit_locked": b.ask == b.bid}


def stats(values):
    n = len(values)
    if not n:
        return dict(n=0, mean=None, median=None, sd=None, t=None)
    m, sd = mean(values), stdev(values) if n > 1 else None
    return dict(n=n, mean=m, median=median(values), sd=sd,
                t=m * math.sqrt(n) / sd if sd else None)


def clustered(items):
    # Intercept-only CR1 SE on observation-weighted mean; weeks indexed by auction date for pairs.
    n, sums, week_values = len(items), defaultdict(float), defaultdict(list)
    m = mean(x for d, x in items) if n else None
    for d, x in items:
        week = d.isocalendar()[:2]
        sums[week] += x - m
        week_values[week].append(x)
    g = len(sums)
    se = math.sqrt(g / (g - 1) * math.fsum(x*x for x in sums.values())) / n if g > 1 else None
    return {"weeks": g, "trade_weighted_mean_bps": m, "cluster_se_bps": se,
            "cluster_t": m/se if se else None,
            "equal_week_weighted_bps": stats([mean(v) for v in week_values.values()])}


def coverage(obs):
    return {
        "registered": len(obs), "placed": sum(o.placed for o in obs),
        "missing_entry": sum("entry" in o.missing for o in obs),
        "missing_exit": sum("exit" in o.missing for o in obs),
        "missing_exit_after_entry": sum(o.entry is not None and o.exit is None for o in obs),
        "missing_trade_bars": sum(2 - sum(o.bars) for o in obs),
        "empty_quote_windows": sum(sum(n == 0 for n in o.quote_rows) for o in obs),
        "not_placed": [{"date": str(o.day), "symbol": o.symbol, "missing_endpoints": o.missing,
                        "exit_size_unassessed": o.entry is None and o.exit_has_regular_quote}
                       for o in obs if not o.placed],
    }


def summary(pairs, observations, trades):
    a_keys = [(a, s) for a, c, s in pairs]
    c_keys = [(c, s) for a, c, s in pairs]
    a_book = [(a, trades[a, s]) for a, s in a_keys if trades[a, s] is not None]
    c_book = [(c, trades[c, s]) for c, s in c_keys if trades[c, s] is not None]
    complete = [(a, trades[a, s]["net_bps"] - trades[c, s]["net_bps"])
                for a, c, s in pairs if trades[a, s] is not None and trades[c, s] is not None]

    def describe(book, keys):
        metrics = {}
        for k in ("net_bps", "net_usd", "idle_usd", "sec_usd", "taf_usd", "cat_usd",
                  "entry_half_spread_bps", "exit_half_spread_bps"):
            metrics[k] = stats([tr[k] for _, tr in book])
        metrics["sum_half_spreads_bps"] = stats(
            [tr["entry_half_spread_bps"] + tr["exit_half_spread_bps"] for _, tr in book])
        return {"coverage": coverage([observations[k] for k in keys]), **metrics,
                "net_usd_sum_noncompounded": math.fsum(tr["net_usd"] for _, tr in book),
                "entry_locked": sum(tr["entry_locked"] for _, tr in book),
                "exit_locked": sum(tr["exit_locked"] for _, tr in book),
                "iso_week": clustered([(d, tr["net_bps"]) for d, tr in book])}

    return {"auctions": describe(a_book, a_keys), "controls": describe(c_book, c_keys),
            "paired_diff_bps": stats([x for d, x in complete]),
            "paired_iso_week_by_auction_date": clustered(complete),
            "pairs_incomplete": [{"auction": str(a), "control": str(c), "symbol": s,
                                  "missing_auction": observations[a, s].missing,
                                  "missing_control": observations[c, s].missing}
                                 for a, c, s in pairs if not (observations[a, s].placed and observations[c, s].placed)]}


def outcome(job, pairs, observations, table, fomc, r_only_observations):
    base = {k: trade(o, table) for k, o in observations.items()}
    overall = summary(pairs, observations, base)
    by_year = {y: summary([p for p in pairs if p[0].year == y], observations, base) for y in YEARS}
    by_lane = {lane: summary([p for p in pairs if p[2] == lane], observations, base)
               for lane in sorted(LANES.values())}
    by_year_and_lane = {y: {lane: summary([p for p in pairs if p[0].year == y and p[2] == lane],
                                         observations, base) for lane in sorted(LANES.values())} for y in YEARS}
    post = summary([p for p in pairs if regime(p[0])], observations, base)
    recent = summary([p for p in pairs if p[0] >= date(2026, 4, 1)], observations, base)
    loo = {y: stats([base[a, s]["net_bps"] for a, c, s in pairs if a.year != y and base[a, s] is not None])
           for y in YEARS}
    arb = sorted(base[a, s]["net_bps"] for a, c, s in pairs if base[a, s] is not None)
    trimmed = stats(arb[:-3])

    def pos(s):
        return s["mean"] is not None and s["mean"] > 0

    def t_ok(s):
        return s["t"] is not None and s["t"] >= 2

    a, p = overall["auctions"], overall["paired_diff_bps"]
    n = a["coverage"]["placed"]
    flags = {
        "placed_count_overall_and_per_lane": n >= 200 and
            all(l["auctions"]["coverage"]["placed"] >= 100 for l in by_lane.values()),
        "placed_95_percent": n * 100 >= len(pairs) * 95,
        "positive_net_mean": pos(a["net_bps"]),
        "net_trade_t_at_least_2": t_ok(a["net_bps"]),
        "positive_without_best_three": pos(trimmed),
        "post_sample_at_least_40_registered_and_positive": post["auctions"]["coverage"]["registered"] >= 40
            and pos(post["auctions"]["net_bps"]),
        "seven_positive_years": sum(pos(l["auctions"]["net_bps"]) for l in by_year.values()) >= 7,
        "paired_positive_and_t_at_least_2": pos(p) and t_ok(p),
        "pairs_95_percent": p["n"] * 100 >= len(pairs) * 95,
        "both_lanes_positive": all(pos(l["auctions"]["net_bps"]) for l in by_lane.values()),
        "all_leave_one_year_out_positive": all(pos(s) for s in loo.values()),
    }
    sensitivities = {"exclude_either_fomc_statement_date": summary(
        [(a, c, s) for a, c, s in pairs if a not in fomc and c not in fomc], observations, base)}
    for slip in (1, 2):
        shown = {k: trade(o, table, slip=slip) for k, o in observations.items()}
        sensitivities[f"adverse_{slip}bp_per_side_fixed_size"] = summary(pairs, observations, shown)
    shown = {k: trade(o, table, unwaived=True) for k, o in observations.items()}
    sensitivities["unwaived_actual_rate_SEC_and_TAF_unrounded"] = summary(pairs, observations, shown)
    shown = {k: trade(o, table) for k, o in r_only_observations.items()}
    sensitivities["regular_condition_R_only"] = summary(pairs, r_only_observations, shown)
    return {"job": job, "pass": all(flags.values()), "marks": flags, "overall": overall,
            "by_year": by_year, "by_maturity_etf": by_lane, "by_year_and_maturity_etf": by_year_and_lane,
            "trimmed_bps": trimmed, "after_2024_07_31_paper_sample": post,
            "april_to_october_2026_descriptive_not_post_revision": recent, "leave_one_year_out_bps": loo,
            "shown_only": sensitivities,
            "limitations": [
                "Clock proxy for the paper's after-release window; no verified post-revision subset.",
                "Shown liquidity is not an order execution or an odd-lot protection guarantee.",
                "The vendor's ? condition is unknown, not verified regular; R-only is shown separately.",
                "No exit quote is retrospective coverage, not something known at entry.",
                "Dates are separate fixed-notional trades, not a compounded account path.",
                "Current Robinhood customer exemptions/rounding applied historically, not broker receipts.",
                "No causal inference from descriptive trade, paired, or ISO-week t statistics.",
            ]}


def git(*args, allow=False):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                           "-C", str(REPO), *args], capture_output=True, env=env, timeout=20)
    need(allow or proc.returncode == 0, "GIT")
    return proc


def authorize(approval):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and git("cat-file", "-t", approval).stdout == b"commit\n"
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:research_rig/{name}").stdout

    authority = contents(approval, APPROVAL)
    body = APPROVAL_RE.fullmatch(authority)
    need(body is not None and authority == read_file(HERE / APPROVAL), "APPROVAL")
    freeze, freeze_pin, input_pin = (x.decode("ascii") for x in body.groups())
    need(freeze != approval and git("merge-base", "--is-ancestor", freeze, approval, allow=True).returncode == 0
         and git("cat-file", "-t", freeze).stdout == b"commit\n"
         and git("cat-file", "-e", f"{freeze}:research_rig/{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = read_file(HERE / PINS, freeze_pin)
    need(manifest == contents(freeze, PINS) == contents(approval, PINS), "FREEZE")
    pins = decode(manifest)
    object_fields(pins, PIN_NAMES, "PIN_NAMES")
    need(all(map(is_pin, pins.values())), "PINS")
    blobs = {n: read_file(HERE / n, pins[n]) for n in pins}
    need(all(blob == contents(freeze, n) == contents(approval, n) for n, blob in blobs.items()), "FREEZE")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."],
         "PLAN_STATUS")
    need(re.search(rb"(?m)^\| 168 \|[^\n]+research_rig/" + re.escape(PLAN.encode()) + rb"` \|",
                   contents(freeze, "TRIAL_LEDGER.md")), "LEDGER")
    queue = git("show", f"{freeze}:docs/QUEUE.md").stdout
    need(re.search(rb"(?m)^\| 52 \|[^\n]+Plan 33[^\n]+168", queue), "QUEUE")
    return freeze, freeze_pin, input_pin, blobs


def encode(obj):
    return (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_exclusive(root, name, data):
    with (root / name).open("xb") as out:
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def unused(root):
    need(not any(os.path.lexists(root / x) for x in ("score_33.lock", "results_33.json")), "CONSUMED")


def claim(root, job, evaluate):
    unused(root)
    try:
        write_exclusive(root, "score_33.lock", encode(job))
    except FileExistsError:
        raise Refused("P33_CONSUMED") from None
    write_exclusive(root, "results_33.json", encode(evaluate()))


def resources():
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    lim = min(x for x in (292_968 * 1024, soft, hard) if x != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (lim, hard))
    priority = os.nice(0)
    if priority < 10:
        os.nice(10 - priority)


def refusal_environment():
    need(sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.optimize == 0
         and not any(k.startswith(("P33_", "PLAN33_", "GIT_", "PYTHON", "LD_"))
                     for k in os.environ), "ENVIRONMENT")


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-inputs", action="store_true")
    modes.add_argument("--go", action="store_true")
    parser.add_argument("--approval-commit", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        refusal_environment()
        resources()
        freeze, fpin, ipin, blobs = authorize(args.approval_commit)
        if args.go:
            private_dir(RUN)
            unused(RUN)
        pairs = plan_dates(blobs)
        table, fomc = fees_table(blobs["fees_33.csv"]), dates(blobs["fomc_dates_33.txt"])
        r_only = {} if args.go else None
        obs, errors = load_inputs(INPUTS, ipin, pairs, r_only_out=r_only)
        if errors:
            for msg in errors:
                print(msg, file=sys.stderr)
            raise Refused(f"P33_REFUSALS {len(errors)}")
        if args.validate_inputs:
            # Coverage only: no return, spread, fee, P&L, scoring, result file or claim.
            print(encode({"status": "P33_INPUTS_VALIDATED", "refusals": 0, "pairs": len(pairs),
                          "auction_inputs": coverage([obs[a, s] for a, c, s in pairs]),
                          "control_inputs": coverage([obs[c, s] for a, c, s in pairs]),
                          "complete_pairs": sum(obs[a, s].placed and obs[c, s].placed for a, c, s in pairs)})
                  .decode(), end="")
            return
        job = {"schema": 1, "ledger": 168, "approval_commit": args.approval_commit, "freeze_commit": freeze,
               "freeze_sha256": fpin, "input_sha256": ipin, "claimed_utc": datetime.now(timezone.utc).isoformat()}
        claim(RUN, job, lambda: outcome(job, pairs, obs, table, fomc, r_only))
    except Refused as exc:
        parser.exit(2, f"{exc}\n")
    except (OSError, ValueError, TypeError, KeyError, IndexError, StopIteration, ArithmeticError,
            subprocess.SubprocessError, MemoryError, RecursionError, csv.Error):
        parser.exit(2, "P33_REFUSED\n")
    print("P33_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
