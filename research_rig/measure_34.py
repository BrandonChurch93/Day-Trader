"""One-shot TMF/UBT instrument measurement. No network or real-input preview."""
import argparse
import json
import os
import re
import stat
import sys
import types
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from fractions import Fraction
from hashlib import sha256
from math import isfinite, prod, sqrt
from pathlib import Path
from statistics import fmean, median, stdev
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/user/workspace/rig/data/measure_34")
TLT_ROOT = Path("/home/user/workspace/rig/data/replay_25/inputs")
TLT_MANIFEST = "43f92b5249c8a2aa8778139f928cf643814e47b778d5892a903227830777aa9a"
FROZEN = {"MEASURE_34_tmf_month_end.md", "measure_34.py", "test_34.py", "common_25.py", "calendar_25.json"}
FUNDS = {"TMF": "direxion.com", "UBT": "proshares.com"}
REQUIRED_SPLITS = {
    "TMF": {
        date(2016, 8, 25): (4, 1, "https://www.sec.gov/Archives/edgar/data/1424958/000119312516658234/0001193125-16-658234.txt"),
        date(2023, 12, 4): (1, 10, "https://www.direxion.com/press-release/direxion-announces-reverse-splits-of-tmf-and-labu"),
    },
    "UBT": {
        date(2020, 8, 18): (2, 1, "https://www.proshares.com/press-releases/proshares-announces-etf-share-splits-80420"),
    },
}
INPUT_NAMES = {n for sym in FUNDS for n in (sym + ".json", sym.lower() + "_quotes.json", sym.lower() + "_actions.json")}
NY, UTC = ZoneInfo("America/New_York"), timezone.utc
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
ISO_UTC = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(?:Z|\+00:00)", re.ASCII)
HEX = re.compile(r"[0-9a-f]{64}", re.ASCII)
EARLY = frozenset(map(date.fromisoformat, (
    "2016-11-25", "2017-07-03", "2017-11-24", "2018-07-03", "2018-11-23", "2018-12-24", "2019-07-03", "2019-11-29",
    "2019-12-24", "2020-11-27", "2020-12-24", "2021-11-26", "2022-11-25", "2023-07-03", "2023-11-24", "2024-07-03",
    "2024-11-29", "2024-12-24", "2025-07-03", "2025-11-28", "2025-12-24")))
ARMS = ("fixed_2bps", "measured_half_spread", "fixed_5bps", "fixed_10bps", "fixed_2bps_plus_half_spread")
FIXED = {"fixed_2bps": 2, "fixed_5bps": 5, "fixed_10bps": 10}


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused(code)


def check_pin(digest):
    need(isinstance(digest, str) and HEX.fullmatch(digest), "M34_PIN")


def private_dir(path):
    s = path.lstat()
    need(stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode) == 0o700
         and s.st_uid == os.geteuid(), "M34_CUSTODY")


def pinned(path, wanted, private=False):
    check_pin(wanted)
    # Nonblocking rejects FIFOs safely; O_NOFOLLOW prevents leaf substitution.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        s = os.fstat(stream.fileno())
        need(stat.S_ISREG(s.st_mode) and s.st_size <= 96 * 1024**2, "M34_FILE")
        need(not private or (s.st_uid == os.geteuid() and stat.S_IMODE(s.st_mode) == 0o600
                             and s.st_nlink == 1), "M34_CUSTODY")
        raw = stream.read(96 * 1024**2 + 1)
    need(len(raw) == s.st_size and sha256(raw).hexdigest() == wanted, "M34_DIGEST")
    return raw


def decode(raw):
    def unique(pairs):
        out = dict(pairs)
        need(len(out) == len(pairs), "M34_JSON")
        return out

    def bad(_):
        raise Refused("M34_JSON")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad)


def ns(stamp):
    m = ISO_UTC.fullmatch(stamp) if isinstance(stamp, str) else None
    need(m, "M34_UTC_CLOCK")
    delta = datetime.fromisoformat(m[1]).replace(tzinfo=UTC) - EPOCH
    return (delta.days * 86400 + delta.seconds) * 10**9 + int((m[2] or "").ljust(9, "0"))


def utc_stamp(clock):
    return clock.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan_schedule(C, calendar):
    days = C.check_calendar(calendar)
    spans = C.windows(days, 3)
    all_days = tuple(d for buy, _, earned in spans for d in (buy, *earned))
    endpoints = tuple(d for buy, sell, _ in spans for d in (buy, sell))
    need(len(spans) == 130 and len(set(all_days)) == len(all_days) == 520
         and len(set(endpoints)) == len(endpoints) == 260 and sum(d in EARLY for d in endpoints) == 5
         and spans[-1][1] == date(2026, 10, 30), "M34_SCHEDULE")
    return days, spans, all_days, endpoints


def quote_bounds(day):
    close = datetime.combine(day, time(13 if day in EARLY else 16), NY)
    return utc_stamp(close - timedelta(seconds=60)), utc_stamp(close)


def positive(v):
    try:
        return type(v) in (float, int) and isfinite(v) and v > 0
    except OverflowError:
        return False


def valid_quote_state(state):
    return (all(positive(v) for v in state) and type(state[2]) is int and type(state[3]) is int
            and state[1] >= state[0])


def quote_cost_order(state):
    bid, ask = state[:2]
    # Minimizing bid/ask maximizes (ask-bid)/(ask+bid). Compare exactly
    # without computing an actual spread; prices break equal ratios canonically.
    return Fraction(bid) / Fraction(ask), bid, ask


def quote_book(rows, endpoints):
    need(isinstance(rows, list) and len(rows) == len(endpoints), "M34_QUOTE_COVERAGE")
    book, tied_endpoints = {}, 0
    for day, r in zip(endpoints, rows, strict=True):
        start, end = quote_bounds(day)
        need(set(r) == {"session", "request_start", "request_end", "complete", "quotes"}
             and r["session"] == day.isoformat() and r["request_start"] == start and r["request_end"] == end
             and r["complete"] is True and isinstance(r["quotes"], list) and r["quotes"], "M34_QUOTE_COVERAGE")
        lo, hi = ns(start), ns(end)
        latest, group = lo - 1, []
        for q in r["quotes"]:
            stamp = ns(q["t"])
            need(lo <= stamp < hi and stamp >= latest, "M34_QUOTE_CLOCK")
            xp = tuple(q[k] for k in ("bp", "ap", "bs", "as"))
            if stamp != latest:
                latest, group = stamp, []
            group.append(xp)
        need(group and all(valid_quote_state(xp) for xp in group), "M34_QUOTE_FINAL")
        tied_endpoints += len(group) > 1
        state = group[0] if len(group) == 1 else min(group, key=quote_cost_order)
        book[day] = state[:2]
    return book, tied_endpoints


def action_day(raw, days):
    day = date.fromisoformat(raw)
    need(raw == day.isoformat() and day in days, "M34_ACTION_DAY")
    return day


def action_source(url, domain):
    u = urlsplit(url)
    return u.scheme == "https" and u.netloc in {domain, "www." + domain} and bool(u.path.strip("/"))


def fund_actions(d, symbol, days):
    need(set(d) == {"schema", "symbol", "currency", "coverage_start", "coverage_end", "share_basis",
                   "reviewer", "cash", "splits"}
         and type(d["schema"]) is int and d["schema"] == 1 and d["symbol"] == symbol and d["currency"] == "USD"
         and d["coverage_start"] == "2016-01-04" and d["coverage_end"] == "2026-10-30"
         and d["share_basis"] == "contemporaneous_ex_date_post_split"
         and isinstance(d["reviewer"], str) and d["reviewer"].strip() and isinstance(d["cash"], list) and d["cash"]
         and isinstance(d["splits"], list), "M34_ACTION_COVERAGE")
    cash, splits, known = defaultdict(list), {}, set()
    days = {x for x in days if x <= date(2026, 10, 30)}
    for kind, fields, clock in (
        ("cash", {"id", "ex_date", "amount", "source"}, "ex_date"),
        ("splits", {"id", "effective_date", "new", "old", "source"}, "effective_date"),
    ):
        for row in d[kind]:
            need(set(row) == fields and isinstance(row["id"], str) and row["id"].strip()
                 and row["id"] not in known, "M34_ACTION_ROW")
            known.add(row["id"])
            day = action_day(row[clock], days)
            if kind == "cash":
                need(action_source(row["source"], FUNDS[symbol]), "M34_ACTION_ROW")
                need(positive(row["amount"]), "M34_ACTION_AMOUNT")
                cash[day].append(row["amount"])
            else:
                a, b = row["new"], row["old"]
                need(type(a) is int and type(b) is int and 0 < a <= 1_000_000 and 0 < b <= 1_000_000
                     and a != b and day not in splits, "M34_SPLIT")
                need((a, b, row["source"]) == REQUIRED_SPLITS[symbol].get(day), "M34_KNOWN_SPLIT")
                splits[day] = (a, b)
    need(splits.keys() == REQUIRED_SPLITS[symbol].keys(), "M34_KNOWN_SPLIT")
    return dict(cash), splits


def manifest_check(m):
    expected = dict(schema=1, symbols=list(FUNDS), feed="sip", adjustment="raw", currency="USD",
                    bars_route="/v2/stocks/{symbol}/bars", quotes_route="/v2/stocks/{symbol}/quotes",
                    quote_scope="close_minus_60s_inclusive_to_close_exclusive")
    need(set(m) == set(expected) | {"collected_utc", "files"} and type(m["schema"]) is int
         and all(m[k] == v for k, v in expected.items()) and set(m["files"]) == INPUT_NAMES, "M34_MANIFEST")
    ns(m["collected_utc"])
    for h in m["files"].values():
        check_pin(h)


def check_tape(C, rows, clocks, width=None):
    C.check_bar_clocks(rows, clocks)
    if width is None:
        return {d: b.c for d, b in C.price_tape(rows, clocks).items()}
    # Sparse windows have an unobserved gap, not one continuous stale-run clock.
    out = {}
    for i in range(0, len(clocks), width):
        out.update((d, b.c) for d, b in C.price_tape(rows[i:i + width], clocks[i:i + width]).items())
    return out


def prepare(freeze_pin, input_pin):
    check_pin(freeze_pin)
    check_pin(input_pin)
    f = decode(pinned(HERE / "FREEZE.json", freeze_pin))
    need(set(f) == {"schema", "files"} and type(f["schema"]) is int and f["schema"] == 1
         and set(f["files"]) == FROZEN, "M34_FREEZE")
    for h in f["files"].values():
        check_pin(h)
    frozen = {name: pinned(HERE / name, h) for name, h in f["files"].items()}
    # Load only the verified bytes; do not import from PYTHONPATH or write caches.
    C = types.ModuleType("_m34_verified_common")
    sys.modules[C.__name__] = C
    exec(compile(frozen["common_25.py"], "common_25.py", "exec"), C.__dict__)
    C.Refused = Refused
    days, spans, wanted, endpoints = plan_schedule(C, decode(frozen["calendar_25.json"]))
    for d in (ROOT, ROOT / "inputs", TLT_ROOT.parent, TLT_ROOT):
        private_dir(d)
    root = ROOT / "inputs"
    need({p.name for p in root.iterdir()} == INPUT_NAMES | {"manifest.json"}, "M34_FILE_SET")
    m = decode(pinned(root / "manifest.json", input_pin, private=True))
    manifest_check(m)
    tlt_m = decode(pinned(TLT_ROOT / "manifest.json", TLT_MANIFEST, private=True))
    for name in ("TLT.json", "cash_actions.json"):
        check_pin(tlt_m["files"][name])

    tlt_bars = check_tape(C, decode(pinned(TLT_ROOT / "TLT.json", tlt_m["files"]["TLT.json"], private=True)), days)
    tlt_a = decode(pinned(TLT_ROOT / "cash_actions.json", tlt_m["files"]["cash_actions.json"], private=True))
    C.check_actions(tlt_a, days)
    tlt_cash = defaultdict(list)
    for r in tlt_a["funds"]["TLT"]["cash"]:
        need(positive(r["amount"]), "M34_ACTION_AMOUNT")
        tlt_cash[date.fromisoformat(r["ex_date"])].append(r["amount"])
    funds = {}
    for sym in FUNDS:
        def get(name):
            return decode(pinned(root / name, m["files"][name], private=True))
        bars = check_tape(C, get(sym + ".json"), wanted, width=4)
        quotes = quote_book(get(sym.lower() + "_quotes.json"), endpoints)
        cash, splits = fund_actions(get(sym.lower() + "_actions.json"), sym, days)
        funds[sym] = (bars, cash, splits, quotes)
    return spans, (tlt_bars, dict(tlt_cash), {}), funds


def window_path(span, bars, cash, splits, entry_cost, exit_cost):
    entry, exit_day, earned_days = span
    cost_basis = bars[entry] * (1 + entry_cost)
    qty, payouts = 1.0, 0.0
    out = [(entry, bars[entry] / cost_basis)]
    for d in earned_days:
        if d in splits:
            n, old = splits[d]
            qty *= n / old
        payouts += qty * sum(cash.get(d, ()))
        value = qty * bars[d]
        if d == exit_day:
            value *= 1 - exit_cost
        factor = (value + payouts) / cost_basis
        need(positive(factor), "M34_NUMERIC")
        out.append((d, factor))
    return out


def simulate(spans, instrument, costs):
    windows = []
    equity, peak, peak_day = 1.0, 1.0, "START"
    dd = dict(fraction=0.0, peak="START", trough="START")
    for span in spans:
        path = window_path(span, *instrument, costs.get(span[0], 0.0), costs.get(span[1], 0.0))
        for day, factor in path:
            marked = equity * factor
            need(positive(marked), "M34_NUMERIC")
            if marked > peak:
                peak, peak_day = marked, day.isoformat()
            draw = 1 - marked / peak
            if draw > dd["fraction"]:
                dd = dict(fraction=draw, peak=peak_day, trough=day.isoformat())
        equity *= path[-1][1]
        windows.append((span[0], span[1], path[-1][1] - 1))
    return windows, dd, equity


def ratio(a, b):
    return a / b if b else None


def summarize(calc):
    rows, dd, equity = calc
    v = [r[-1] for r in rows]
    mean, spread = fmean(v), stdev(v)
    dates = defaultdict(list)
    for _, d, value in rows:
        dates[str(d.year)].append(value)
    years = {y: dict(n=len(x), mean_net=fmean(x), compounded_net=prod(1 + z for z in x) - 1)
             for y, x in dates.items()}
    entry, day, worst = min(rows, key=lambda r: r[-1])
    return dict(n=len(v), mean_net=mean, t=mean * sqrt(len(v)) / spread if spread else None,
                trimmed_mean=fmean(sorted(v)[:-3]), worst_window=dict(entry=entry.isoformat(), exit=day.isoformat(), net=worst),
                by_year=years, worst_year_compounded=min(years, key=lambda y: years[y]["compounded_net"]),
                worst_year_mean=min(years, key=lambda y: years[y]["mean_net"]),
                positive_year_share=sum(y["mean_net"] > 0 for y in years.values()) / len(years),
                max_drawdown=dd, end_equity=equity)


def report_spread(xs):
    values = sorted(x * 1e4 for x in xs)
    i = 0.95 * (len(values) - 1)
    p = values[int(i)] + (i - int(i)) * (values[min(int(i) + 1, len(values) - 1)] - values[int(i)])
    return dict(n=len(values), mean=fmean(values), median=median(values), p95=p, max=values[-1])


def evaluate(job, prepared):
    spans, tlt, funds = prepared
    tlt_gross = fmean(w[-1] for w in simulate(spans, tlt, {})[0])
    sides = [d for buy, sell, _ in spans for d in (buy, sell)]
    tlt_fixed = {arm: fmean(w[-1] for w in simulate(spans, tlt, dict.fromkeys(sides, bps / 1e4))[0])
                 for arm, bps in FIXED.items()}
    out = {}
    for sym, (*instrument, (quotes, tied_endpoints)) in funds.items():
        spread = {d: (1 - bid / ask) / (1 + bid / ask) for d, (bid, ask) in quotes.items()}
        mean_gross = fmean(w[-1] for w in simulate(spans, instrument, {})[0])
        band = (2.7, 3.1) if sym == "TMF" else (1.8, 2.1)
        gross_ratio = ratio(mean_gross, tlt_gross)
        data = {"gross_mean": mean_gross, "gross_tracking_ratio": gross_ratio, "reference_band": band,
                "tied_quote_endpoints": tied_endpoints,
                "tied_quote_policy": "conservative tied-endpoint estimate: maximum half spread at the final timestamp",
                "entry_half_spread_bps": report_spread(spread[d] for d in sides[::2]),
                "exit_half_spread_bps": report_spread(spread[d] for d in sides[1::2]), "arms": {}}
        for arm in ARMS:
            costs = dict.fromkeys(sides, FIXED[arm] / 1e4) if arm in FIXED else (
                spread if arm == "measured_half_spread" else {d: z + 0.0002 for d, z in spread.items()})
            r = summarize(simulate(spans, instrument, costs))
            ref = arm if arm in FIXED else "fixed_2bps"
            r["net_tracking_ratio"] = ratio(r["mean_net"], tlt_fixed[ref])
            r["net_tracking_reference"] = "TLT_" + ref
            data["arms"][arm] = r
        if sym == "TMF":
            data["marks"] = dict(gross_tracking_band=gross_ratio is not None and band[0] <= gross_ratio <= band[1],
                                 positive_net_at_fixed_2bps_plus_half_spread=(
                                     data["arms"]["fixed_2bps_plus_half_spread"]["mean_net"] > 0))
        out[sym] = data
    return dict(job=job, tlt_gross_mean=tlt_gross, tlt_fixed_means=tlt_fixed, funds=out)


def claim(root, job, evaluator):
    lock, result = root / "run_34.lock", root / "results_34.json"
    need(not os.path.lexists(lock) and not os.path.lexists(result), "M34_ALREADY_RUN")
    dir_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        def create(name, blob):
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)
            with os.fdopen(fd, "wb") as f:
                f.write(blob)
                f.flush()
                os.fsync(f.fileno())
            os.fsync(dir_fd)

        try:
            create(lock.name, (json.dumps(job, sort_keys=True) + "\n").encode())
        except FileExistsError:
            raise Refused("M34_ALREADY_RUN") from None
        blob = (json.dumps(evaluator(), indent=2, allow_nan=False) + "\n").encode()
        create(result.name, blob)
    finally:
        os.close(dir_fd)


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    task = p.add_mutually_exclusive_group(required=True)
    task.add_argument("--validate-inputs", action="store_true")
    task.add_argument("--run", action="store_true")
    p.add_argument("--approved-freeze-sha256", required=True)
    p.add_argument("--approved-input-sha256", required=True)
    args = p.parse_args()
    os.umask(0o077)
    try:
        data = prepare(args.approved_freeze_sha256, args.approved_input_sha256)
        if args.validate_inputs:
            print("M34_INPUTS_OK 130 windows; 260 quote endpoints and 520 bar rows per fund")
            return
        job = dict(schema=1, ledger=169, queue=56, freeze_sha256=args.approved_freeze_sha256,
                   input_sha256=args.approved_input_sha256, tlt_manifest_sha256=TLT_MANIFEST,
                   claimed_utc=datetime.now(UTC).isoformat())
        claim(ROOT, job, lambda: evaluate(job, data))
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError, UnicodeError, AttributeError):
        p.exit(2, "M34_INVALID_INPUT\n")
    print("M34_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
