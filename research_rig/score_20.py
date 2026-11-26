"""Replay 20 offline adapter. Draft cannot execute real scoring."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from math import isfinite
import os
from pathlib import Path
import re
import resource
import subprocess
import unittest
import zipfile

import yaml

from . import archive_18 as A, common_20 as C, us_roster_17 as US
from .score_19 import Refused, claim, memory

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "rig" / "data"
RUN = DATA / "replay_20"
DRAFT = ROOT / "research_rig/PREREG_20_upbit_listing_short_DRAFT.md"
FROZEN = ROOT / "research_rig/PREREG_20_upbit_listing_short.md"
CONFIG = ROOT / "config/thresholds.yaml"
LEDGER = ROOT / "research_rig/TRIAL_LEDGER.md"
NOTICE = DATA / "upbit_listings/notices.csv"
ROSTER = DATA.parent / "ideas" / US.NAME
LOCK = RUN / "score_20.lock"
RESULT = ROOT / "research_rig/results_20.json"
NOTICE_PIN = "6d7e4a67f7964d394a9412551369df27c2317b21a156d2cb5cd73f34040baec7"
MANIFESTS = {
    DATA / "replay_16/manifest_futures.json": "07a28ae776606bb1430aa91ab94ae69b5cfeec37e0f48c9f2d342ab745e8b94d",
    DATA / "replay_16/manifest_futures_held.json": "d2949c130e4d98d13ed4bf376abee0700e4122fbf76af80a7d8fcf695a1e9afd",
}
STORES = {key: DATA / key / "archives" for key in ("replay_13", "replay_16", "replay_20")}
HOUR_US = 3_600_000_000
NUMBER = re.compile(rb"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]{1,3})?")
HEADERS = {b"open_time", b"openTime", b"calc_time", b"fundingTime"}
BULK = re.compile(r"data/futures/um/(daily|monthly)/(klines|markPriceKlines|fundingRate)/([^\W_]+)/(?:1h/)?([^/]+)\.zip")


def digest(raw):
    return sha256(raw).hexdigest()


def inventory(p):
    index = {}
    for manifest, pin in MANIFESTS.items():
        try:
            parsed = json.loads(A.read_pinned(manifest, pin))
            if parsed["errors"]:
                raise C.Invalid("manifest errors")
            for key, spec in parsed["archives"].items():
                match = BULK.fullmatch(key)
                a, b = A.archive_span(match)
                # Previous UTC close and an adjacent settlement can be outside
                # the sample. No trade, outcome or seasoning after the cutoff.
                if b <= p["start"] - 24 or a >= p["end"]:
                    continue
                where, fingerprint = spec["where"], spec["sha256"]
                if where not in STORES or not A.SHA.fullmatch(fingerprint):
                    raise C.Invalid("bad archive specification")
                first, last = spec["first"], spec["last"]
                if type(first) is not int or type(last) is not int or first > last:
                    raise C.Invalid("invalid recorded archive bounds")
                item = (match[3], match[2], first, last, a, b, where, fingerprint)
                if index.setdefault(key, item) != item:
                    raise C.Invalid("conflicting archive specifications")
            del parsed
        except (Exception, KeyboardInterrupt):
            raise Refused("P20_MANIFEST_REFUSED", manifest) from None
    groups = defaultdict(list)
    ends = {}
    for key, (symbol, kind, first, last, a, b, where, pin) in sorted(index.items(), key=lambda item: item[1][:4]):
        path = STORES[where] / key
        # Daily repair files may fill a truncated monthly archive. The
        # original manifests recorded disjoint real timestamp ranges.
        if ends.get((symbol, kind), -1) >= first:
            raise Refused("P20_ARCHIVE_OVERLAP", path)
        ends[symbol, kind] = last
        groups[symbol].append((kind, a, b, path, pin))
    return dict(groups)


def notices(p):
    judged, by_ticker, by_symbol = {}, defaultdict(list), defaultdict(list)
    rows = Counter()
    try:
        raw = A.read_pinned(NOTICE, NOTICE_PIN)
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
            if row["market"] != "KRW":
                continue
            ticker, published, pair = row["coin_ticker"], row["published_at_utc"], row["binance_um_symbol"]
            if not re.fullmatch(r"[A-Z0-9]+", ticker) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\dZ", published):
                raise C.Invalid("bad KRW row")
            minute = int(datetime.fromisoformat(published).timestamp()) // 60
            if not p["start"] * 60 <= minute < p["end"] * 60:
                raise C.Invalid("notice outside sample")
            flag = row["binance_um_perp_at_notice"]
            allowed = {ticker+"USDT", "1000"+ticker+"USDT"}
            if ticker == "BEAM":
                allowed.add("BEAMXUSDT")
            if flag not in {"yes", "no"} or (flag == "yes" and pair not in allowed):
                raise C.Invalid("bad pair flag")
            rows["krw"] += 1
            rows["path_flag_yes"] += flag == "yes"
            found = C.Notice(ticker, pair if flag == "yes" else "", minute)
            by_ticker[ticker].append(minute)
            if pair and flag == "yes":
                by_symbol[pair].append(minute)
            previous = judged.get(ticker)
            if previous is None or found.minute < previous.minute:
                judged[ticker] = found
            elif found.minute == previous.minute and found != previous:
                raise C.Invalid("ambiguous first notice")
    except (Exception, KeyboardInterrupt):
        raise Refused("P20_NOTICE_REFUSED", NOTICE) from None
    return judged, by_ticker, by_symbol, rows


def decode_archive(kind, a, b, path, pin, p, stats, tape=None, observe=None):
    """In scan mode, inspect byte categories only, never convert prices or rates."""
    last = None
    try:
        if path.stat().st_size > A.MAX_ZIP_BYTES:
            raise C.Invalid("archive too large")
        raw = A.read_pinned(path, pin)
    except Exception:
        raise Refused("P20_ARCHIVE_PIN", path) from None
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            member, = (name for name in z.namelist() if name.endswith(".csv"))
            with z.open(member) as stream:
                for n, line in enumerate(stream):
                    row = line.rstrip(b"\r\n").split(b",")
                    if n == 0:
                        row[0] = row[0].removeprefix(b"\xef\xbb\xbf")
                        if row[0] in HEADERS:
                            continue
                    if not row[0].isdigit():
                        raise C.Invalid("bad open stamp")
                    stamp = A.clock_us(row[0])
                    h = (stamp + HOUR_US // 2) // HOUR_US
                    funding = kind == "fundingRate"
                    if funding:
                        interval = int(row[1])
                        if (interval not in {1, 2, 4, 8} or h % interval or
                                not (a <= h < b or a * HOUR_US <= stamp < b * HOUR_US) or
                                abs(stamp - h * HOUR_US) > p["funding_jitter_seconds"] * 10**6):
                            raise C.Invalid("bad funding stamp")
                        fields = (("rate", row[2]),)
                    else:
                        if (not a <= h < b or stamp != h * HOUR_US or not row[6].isdigit() or
                                A.clock_us(row[6]) // 1000 != (stamp + HOUR_US) // 1000 - 1):
                            raise C.Invalid("bad bar stamp")
                        fields = ((("mark", row[1]),) if kind == "markPriceKlines" else
                                  tuple((key, row[i]) for key, i in (("open", 1), ("high", 2), ("low", 3), ("close", 4), ("volume", 5))))
                    if last is not None and h <= last:
                        raise C.Invalid("archive clocks not increasing")
                    last = h
                    stats[kind] += 1
                    values = {}
                    no_volume = False
                    for key, token in fields:
                        if not NUMBER.fullmatch(token):
                            raise C.Invalid("invalid numeric category")
                        if key != "rate":
                            base = token.lower().split(b"e", 1)[0].lstrip(b"+-").replace(b".", b"")
                            zero = not base.strip(b"0")
                            if (token.startswith(b"-") and not zero) or (zero and key != "volume"):
                                raise C.Invalid("invalid sign or zero category")
                            if key == "volume" and zero:
                                stats["zero_volume"] += 1
                                no_volume = True
                        if tape is not None:
                            v = float(token)
                            if not isfinite(v) or (key not in {"rate", "volume"} and v <= 0):
                                raise C.Invalid("unrepresentable number")
                            values[key] = v
                    if observe is not None:
                        observe(h, no_volume)
                    if tape is not None and tape.start <= h < tape.end:
                        if funding:
                            if h in tape.funding:
                                raise C.Invalid("duplicate settlement")
                            tape.funding[h] = interval, values["rate"]
                        else:
                            if kind == "klines" and not values["low"] <= min(values["open"], values["close"]) <= max(values["open"], values["close"]) <= values["high"]:
                                raise C.Invalid("inconsistent OHLC")
                            for key, value in values.items():
                                if key != "low":
                                    tape.set(key, h, value)
        if last is None:
            raise C.Invalid("empty archive")
    except (IndexError, ValueError, OSError, zipfile.BadZipFile, RuntimeError):
        raise Refused("P20_CLOCK_OR_FIELD", path) from None


def scan(groups, p):
    stats, refusals, checked = Counter(), Counter(), 0
    examples = []
    for files in groups.values():
        memory()
        for kind, a, b, path, pin in files:
            checked += 1
            try:
                decode_archive(kind, a, b, path, pin, p, stats)
            except Refused as error:
                refusals[error.code] += 1
                if len(examples) < 12:
                    examples.append([error.code, str(error.path)])
    return dict(symbols=len(groups), files=checked, rows=dict(stats), refusals=dict(refusals), examples=examples)


def scan_notice_clocks(groups, events, p):
    """Possible red-day roles only; no price-based signal or stop selected."""
    counts, stats = Counter(), Counter()
    for event in events.values():
        if not event.symbol:
            continue
        memory()
        day = (event.minute // 1440) * 24
        entries = [day + (d + 1) * 24 + p["entry_hour_utc"] for d in range(p["red_days"])]
        start = day - 1
        end = min(entries[-1] + p["hold_hours"] + 1, p["end"])
        seen, zero = set(), set()

        def observe(h, empty):
            if start <= h < end:
                if h in seen:
                    raise C.Invalid("duplicate notice-window trade timestamp")
                seen.add(h)
                if empty:
                    zero.add(h)

        for kind, a, b, path, pin in groups.get(event.symbol, ()):
            if kind == "klines" and a < end and start < b:
                decode_archive(kind, a, b, path, pin, p, stats, observe=observe)
        possible_signals = {day + d * 24 - 1 for d in range(p["red_days"] + 1)}
        possible_signals.update(range(event.minute // 60, entries[-1]))
        counts["first_flagged_notices"] += 1
        counts["missing_notice_hour"] += event.minute // 60 not in seen
        counts["missing_inside_candidate_envelope"] += len(seen) != end - start
        counts["potential_zero_signal"] += bool(possible_signals & zero)
        counts["potential_zero_entry"] += bool(set(entries) & zero)
        counts["potential_zero_timed_exit"] += bool({h + p["hold_hours"] for h in entries} & zero)
        counts["potential_zero_stop_hour"] += any(entries[0] <= h < end for h in zero)
    return dict(counts)


def load(files, p):
    tape = C.Tape(p["start"] - 24, p["end"])
    quiet = Counter()
    for kind, a, b, path, pin in files:
        decode_archive(kind, a, b, path, pin, p, quiet, tape)
    tape.finish()
    return tape


def evaluate_book(groups, notice_data, us, p, *, validate_only=False):
    judged, by_ticker, by_symbol, rows = notice_data
    rows = rows.copy()
    events = defaultdict(list)
    for notice in judged.values():
        if notice.symbol:
            events[notice.symbol].append(notice)
    trades, shown_us, hourly, earlier, unscreened, pools = [], [], [], [], [], defaultdict(list)
    disposition = dict.fromkeys(("traded", "no_red_day", "not_trading_at_notice", "no_fill", "other"), 0)
    absent_notices, absent_controls = [], {}
    ordinary_counts = Counter()
    if set(events) - groups.keys():
        raise Refused("P20_NOTICE_PAIR_UNAVAILABLE", NOTICE)
    for symbol, files in groups.items():
        memory()
        tape = load(files, p)
        for event in events[symbol]:
            if not tape.bar(event.minute // 60):
                disposition["not_trading_at_notice"] += 1
                absent_notices.append(event.ticker)
                continue
            try:
                s = C.setup(tape, event.minute, p)
                if s is None:
                    disposition["no_red_day"] += 1
                else:
                    t = C.evaluate(tape, s, p, validate_only=validate_only)
                    disposition["traded"] += 1
                    if not validate_only:
                        trades.append(t)
                        if event.ticker in us and symbol == event.ticker + "USDT":
                            shown_us.append(t)
            except C.NoFill:
                disposition["no_fill"] += 1
            except LookupError:
                disposition["other"] += 1
            if not validate_only:
                for pre, screen, output in ((False, True, hourly), (True, True, earlier), (False, False, unscreened)):
                    try:
                        s = C.setup(tape, event.minute, p, earlier=pre, screen=screen)
                        if s:
                            output.append(C.evaluate(tape, s, p))
                    except LookupError:
                        continue
        if not validate_only:
            stem = symbol.removesuffix("USDT")
            candidates = set(by_ticker.get(stem, ())) | set(by_symbol.get(symbol, ()))
            if stem.startswith("1000"):
                candidates.update(by_ticker.get(stem[4:], ()))
            control_counts = Counter()
            for t in C.ordinary(tape, sorted(candidates), p, control_counts):
                pools[t.year].append(t.net(p["judged_bps"]))
            ordinary_counts.update(control_counts)
            if control_counts["not_trading_at_trigger"]:
                absent_controls[symbol] = control_counts["not_trading_at_trigger"]
    first_flagged = sum(map(len, events.values()))
    if sum(disposition.values()) != first_flagged:
        raise Refused("P20_NOTICE_RECONCILIATION", NOTICE)
    if not validate_only:
        judged_values = [(t.year, t.net(p["judged_bps"])) for t in trades]
        return {"notice_counts": dict(rows), "first_flagged_notices": first_flagged,
                "notice_disposition": disposition, "not_trading_at_notice_coins": sorted(absent_notices),
                "ordinary_disposition": dict(ordinary_counts), "not_trading_at_trigger_by_symbol": absent_controls,
                "judgment": C.judgment(p, judged_values, pools, memory),
                "judged": C.summary(trades, p["judged_bps"]), "higher_fee": C.summary(trades, p["shown_bps"]),
                "us_today": C.summary(shown_us, p["judged_bps"]), "hourly_25pct": C.summary(hourly, p["judged_bps"]),
                "hourly_earlier_25pct": C.summary(earlier, p["judged_bps"]),
                "hourly_all_jumps": C.summary(unscreened, p["judged_bps"])}


def configure_resources():
    memory()
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(v for v in (A.MEMORY_CAP, soft, hard) if v != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    os.nice(max(0, 10 - os.nice(0)))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def authorize(commit):
    if not re.fullmatch(r"[0-9a-f]{40}", commit or "") or git("rev-parse", "HEAD").decode().strip() != commit:
        raise Refused("P20_AUTH_REFUSED", FROZEN)
    if DRAFT.exists() or not FROZEN.is_file() or git("status", "--porcelain"):
        raise Refused("P20_AUTH_REFUSED", FROZEN)
    paths = [FROZEN, CONFIG, LEDGER, *(ROOT / f"research_rig/{name}_20.py" for name in ("common", "score", "test")),
             *(ROOT / f"research_rig/{name}.py" for name in ("archive_18", "common_18", "score_19", "common_19", "us_roster_17"))]
    bound = {}
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        if path.is_symlink() or raw != git("show", f"{commit}:{relative}"):
            raise Refused("P20_AUTH_REFUSED", path)
        bound[relative] = digest(raw)
    if not re.search(rb"(?m)^Status FROZEN\.$", FROZEN.read_bytes()):
        raise Refused("P20_AUTH_REFUSED", FROZEN)
    if not re.search(rb"(?m)^\| 157 \|[^\n]*PREREG_20_upbit_listing_short\.md", LEDGER.read_bytes()):
        raise Refused("P20_AUTH_REFUSED", LEDGER)
    if RUN.is_symlink() or RUN.stat().st_uid != os.geteuid() or RUN.stat().st_mode & 0o022:
        raise Refused("P20_AUTH_REFUSED", RUN)
    return bound


def go(commit):
    bound = authorize(commit)
    p = C.policy(yaml.safe_load(CONFIG.read_bytes())["replay_20_plan"]["value"])
    job = dict(ledger=157, commit=commit, source_manifests={path.name: pin for path, pin in MANIFESTS.items()},
               notices_sha256=NOTICE_PIN, us_roster_sha256=US.SHA256, repo_sha256=bound,
               started_utc=datetime.now(timezone.utc).isoformat())

    def prepare():
        groups = inventory(p)
        mapped = notices(p)
        try:
            us = {row["symbol"] for row in US.rows(A.read_pinned(ROSTER, US.SHA256))}
        except Exception:
            raise Refused("P20_ROSTER_REFUSED", ROSTER) from None
        evaluate_book(groups, mapped, us, p, validate_only=True)
        memory()
        return groups, mapped, us

    def calculate(prepared):
        return {"job": job, "policy": p, "outcome": evaluate_book(*prepared, p)}

    try:
        claim(LOCK, RESULT, job, prepare, calculate)
    except Refused as error:
        if error.code == "P19_CONSUMED":
            raise Refused("P20_CONSUMED", error.path) from None
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("inventory", "clock-scan", "notice-clock-scan", "selftest", "calibration", "go"):
        mode.add_argument("--" + name, action="store_true")
    parser.add_argument("--approval-commit")
    args = parser.parse_args()
    try:
        configure_resources()
        if args.go:
            go(args.approval_commit)
            return 0
        p = C.policy(yaml.safe_load(CONFIG.read_bytes())["replay_20_plan"]["value"])
        if args.selftest or args.calibration:
            from . import test_20
            return test_20.run(p, calibration=args.calibration)
        groups = inventory(p)
        if args.inventory or args.notice_clock_scan:
            events, _, _, counts = notices(p)
            if args.inventory:
                print(json.dumps(dict(notices=dict(counts), symbols=len(groups), files=sum(map(len, groups.values())))))
            else:
                print(json.dumps(scan_notice_clocks(groups, events, p), sort_keys=True))
            return 0
        result = scan(groups, p)
        print(json.dumps(result, sort_keys=True))
        return int(bool(result["refusals"]))
    except Refused as error:
        path = str(error.path).encode("unicode_escape").decode("ascii")
        parser.exit(1, f"{error.code} {path}\n")
    except (Exception, KeyboardInterrupt):
        parser.exit(1, f"P20_REFUSED {ROOT / 'research_rig/score_20.py'}\n")


if __name__ == "__main__":
    raise SystemExit(main())
