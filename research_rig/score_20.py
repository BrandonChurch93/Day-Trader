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
from urllib.parse import urlsplit
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
DATED_ROSTER = NOTICE.with_name("binance_um_roster.csv")
NOTICE_MAP = NOTICE.with_name("notice_perp_map.csv")
IDENTITIES = NOTICE.with_name("notice_identity_sidecar.csv")
LIFETIMES = NOTICE.with_name("symbol_lifetimes_sidecar.csv")
STAGING = DATA / "replay_20_inputs"
SUPPLEMENT = STAGING / "archives.json"
US_ROSTER = DATA.parent / "ideas" / US.NAME
LOCK = RUN / "score_20.lock"
RESULT = ROOT / "research_rig/results_20.json"
NOTICE_PIN = "6d7e4a67f7964d394a9412551369df27c2317b21a156d2cb5cd73f34040baec7"
DATED_ROSTER_PIN = ""
NOTICE_MAP_PIN = ""
IDENTITY_PIN = ""
LIFETIMES_PIN = ""
SUPPLEMENT_PIN = ""
MANIFESTS = {
    DATA / "replay_16/manifest_futures.json": "07a28ae776606bb1430aa91ab94ae69b5cfeec37e0f48c9f2d342ab745e8b94d",
    DATA / "replay_16/manifest_futures_held.json": "d2949c130e4d98d13ed4bf376abee0700e4122fbf76af80a7d8fcf695a1e9afd",
}
STORES = {key: DATA / key / "archives" for key in ("replay_13", "replay_16")}
STORES["replay_20"] = STAGING / "archives"
HOUR_US = 3_600_000_000
NUMBER = re.compile(rb"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]{1,3})?")
HEADERS = {b"open_time", b"openTime", b"calc_time", b"fundingTime"}
BULK = re.compile(r"data/futures/um/(daily|monthly)/(klines|markPriceKlines|fundingRate)/([^\W_]+)/(?:1h/)?([^/]+)\.zip")


def digest(raw):
    return sha256(raw).hexdigest()


def inventory(p, *, base_only=False, candidate=None):
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
    if not base_only:
        try:
            supplement = json.loads(A.read_pinned(SUPPLEMENT, SUPPLEMENT_PIN)) if candidate is None else candidate
            if supplement["version"] != 2:
                raise C.Invalid("bad supplement version")
            for key in supplement["replace"]:
                del index[key]
            for key, pin in supplement["archives"].items():
                match = BULK.fullmatch(key)
                a, b = A.archive_span(match)
                if key in index or not A.SHA.fullmatch(pin):
                    raise C.Invalid("unsupported supplemental entry")
                index[key] = (match[3], match[2], a * 3600, b * 3600 - 1, a, b, "replay_20", pin)
        except (Exception, KeyboardInterrupt):
            raise Refused("P20_SUPPLEMENT_REFUSED", SUPPLEMENT) from None
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
    if not base_only and candidate is None and supplement.get("control_domains") != manifest_domains(groups):
        raise Refused("P20_SUPPLEMENT_REFUSED", SUPPLEMENT)
    return dict(groups)


def parse_minute(value):
    stamp = datetime.fromisoformat(value)
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() or stamp.second or stamp.microsecond:
        raise C.Invalid("UTC timestamp required")
    return int(stamp.timestamp() // 60)


def official_notice(url):
    parts = urlsplit(url)
    return (parts.scheme == "https" and parts.netloc == "www.binance.com" and
            bool(re.fullmatch(r"/en/support/announcement/(?:detail/)?[0-9a-z-]*[0-9a-f]{32}/?", parts.path)))


def dated_end(value, precision, source, url):
    if not value:
        if precision or source or url:
            raise C.Invalid("end provenance without a date")
        return None, None
    if source in {"binance_delisting_announcement", "binance_migration_announcement"} and precision == "hour" and official_notice(url):
        return parse_minute(value), None
    if source == "data_binance_vision_last_daily" and precision == "day_precision" and not url:
        # This date records the last daily archive, not a trade or an end stamp.
        return None, (parse_minute(value) // 1440 + 1) * 1440
    raise C.Invalid("end provenance unsupported")


def identities(pin=None, lifetimes_pin=None):
    try:
        raw = A.read_pinned(IDENTITIES, IDENTITY_PIN if pin is None else pin)
        notes = {}
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
            key = "|".join(row[k] for k in ("notice_id", "coin_ticker", "published_at_utc"))
            if key in notes or not row["notice_asset_id"]:
                raise C.Invalid("duplicate or empty notice identity")
            notes[key] = row
    except (Exception, KeyboardInterrupt):
        raise Refused("P20_IDENTITIES_REFUSED", IDENTITIES) from None
    try:
        raw = A.read_pinned(LIFETIMES, LIFETIMES_PIN if lifetimes_pin is None else lifetimes_pin)
        symbols = defaultdict(dict)
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
            ids = symbols[row["symbol"]]
            seq = int(row["lifetime_seq"])
            if seq < 1 or seq in ids:
                raise C.Invalid("bad lifetime sequence")
            ids[seq] = row
        if any(set(seq) != set(range(1, len(seq) + 1)) for seq in symbols.values()):
            raise C.Invalid("incomplete lifetime sequence")
    except (Exception, KeyboardInterrupt):
        raise Refused("P20_LIFETIMES_REFUSED", LIFETIMES) from None
    return {"contracts": {s: [ids[i] for i in sorted(ids)] for s, ids in symbols.items()}, "notices": notes}


def dated_roster(pin=None, identity_data=None):
    contracts = defaultdict(list)
    patches = {} if identity_data is None else identity_data["contracts"]
    try:
        raw = A.read_pinned(DATED_ROSTER, DATED_ROSTER_PIN if pin is None else pin)
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
            symbol, asset = row["symbol"], row["underlying_asset"]
            if (not re.fullmatch(r"[^\W_]+", symbol) or not asset or symbol in contracts or
                    row["contract_type"] not in {"PERPETUAL", "SETTLED_ARCHIVE"} or int(row["multiplier"]) < 1):
                raise C.Invalid("bad roster contract")
            launch_source = row["launch_time_source"]
            precision = row["launch_time_precision"]
            launch_url = row["launch_source_url"]
            if not ((launch_source == "binance_launch_announcement" and precision == "hour" and official_notice(launch_url)) or
                    (launch_source == "data_binance_vision_first_daily" and precision == "day_precision" and
                     not launch_url and row["launch_time_utc"] == f"{row['first_daily_file']}T00:00Z")):
                raise C.Invalid("unsupported launch provenance")
            launch = parse_minute(row["launch_time_utc"])
            end, tail = dated_end(row["last_trading_time_utc"], row["last_trading_precision"],
                                  row["last_trading_source"], row["last_trading_source_url"])
            lifetimes = patches.get(symbol)
            if lifetimes is None:
                contracts[symbol].append(C.Contract(symbol, asset, launch, end, tail))
            else:
                for dated in lifetimes:
                    if (dated["quote_asset"], dated["multiplier"]) != (row["quote_asset"], row["multiplier"]):
                        raise C.Invalid("lifetime contract fields differ")
                    corrected_launch = parse_minute(dated["launch_time_utc"])
                    dated_launch = (dated["launch_time_precision"], dated["launch_time_source"], dated["launch_source_url"])
                    if dated_launch != (precision, launch_source, launch_url) or corrected_launch != launch:
                        if not (dated_launch[:2] == ("hour", "binance_launch_announcement") and official_notice(dated_launch[2])):
                            raise C.Invalid("unproved launch override")
                    corrected_end, corrected_tail = dated_end(dated["end_time_utc"], dated["end_time_precision"],
                                                              dated["end_time_source"], dated["end_source_url"])
                    if (corrected_end, corrected_tail) != (end, tail) and corrected_end is None and len(lifetimes) == 1:
                        raise C.Invalid("unproved end override")
                    contracts[symbol].append(C.Contract(symbol, dated["asset_id"], corrected_launch,
                                                        corrected_end, corrected_tail))
        if identity_data is not None and patches.keys() != contracts.keys():
            raise C.Invalid("lifetime coverage differs from roster")
        for symbol, lifetimes in contracts.items():
            if not lifetimes or any(not c.asset or (c.end_minute is not None and c.end_minute <= c.launch_minute)
                                    or (c.archive_tail_minute is not None and c.archive_tail_minute <= c.launch_minute)
                                    for c in lifetimes):
                raise C.Invalid("invalid or absent dated lifetimes")
            lifetimes.sort(key=lambda c: c.launch_minute)
            for old, new in zip(lifetimes, lifetimes[1:]):
                if old.end_minute is None or old.end_minute > new.launch_minute:
                    raise C.Invalid("overlapping lifetimes")
        if not contracts:
            raise C.Invalid("empty dated roster")
    except (Exception, KeyboardInterrupt):
        raise Refused("P20_DATED_ROSTER_REFUSED", DATED_ROSTER) from None
    return dict(contracts)


def notices(p, roster, map_pin=None, identity_data=None):
    first, notice_index, counts = {}, defaultdict(list), Counter()
    try:
        raw = A.read_pinned(NOTICE, NOTICE_PIN)
        source = {}
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
            if row["market"] != "KRW":
                continue
            key = row["notice_id"], row["coin_ticker"], parse_minute(row["published_at_utc"])
            if key in source:
                raise C.Invalid("duplicate KRW row")
            source[key] = row["binance_um_perp_at_notice"] == "yes"
    except (Exception, KeyboardInterrupt):
        raise Refused("P20_NOTICE_REFUSED", NOTICE) from None
    try:
        raw = A.read_pinned(NOTICE_MAP, NOTICE_MAP_PIN if map_pin is None else map_pin)
        used, identity_keys = set(), set()
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
            ticker, pair = row["coin_ticker"], row["matched_symbol"]
            minute = parse_minute(row["published_at_utc"])
            key = row["notice_id"], ticker, minute
            if key not in source or key in used or row["old_store_flag"] != ("yes" if source[key] else "no"):
                raise C.Invalid("map does not match source")
            used.add(key)
            counts["krw"] += 1
            counts["legacy_path_flags"] += source[key]
            flag, category = row["binance_um_perp_at_notice"], row["mapping_category"]
            if (category not in {"trading_at_notice", "launched_later", "ended_before", "never_listed"} or
                    flag != ("yes" if category == "trading_at_notice" else "no") or
                    row["differs_from_old_flag"] != ("yes" if (flag == "yes") != source[key] else "no")):
                raise C.Invalid("ambiguous or inconsistent notice map")
            counts[category] += 1
            counts["changed_from_legacy"] += (flag == "yes") != source[key]
            key_text = "|".join((row["notice_id"], ticker, row["published_at_utc"]))
            identity_keys.add(key_text)
            if identity_data is not None:
                identity = identity_data["notices"][key_text]
                asset = identity["notice_asset_id"]
                if (identity["mapping_category"], identity["matched_symbol"]) != (category, pair):
                    raise C.Invalid("identity sidecar disagrees with notice map")
                if pair:
                    seq = int(identity["matched_lifetime_seq"])
                    lifetimes = identity_data["contracts"][pair]
                    if not 1 <= seq <= len(lifetimes):
                        raise C.Invalid("unknown mapped lifetime")
                    c = lifetimes[seq - 1]
                    if (asset, identity["matched_asset_id"], identity["matched_launch_time_utc"],
                            identity["matched_end_time_utc"], identity["matched_end_time_source"]) != (
                            c["asset_id"], c["asset_id"], c["launch_time_utc"], c["end_time_utc"], c["end_time_source"]):
                        raise C.Invalid("mapped identity is inconsistent")
            elif pair:
                asset = roster[pair][0].asset
            else:
                asset = ticker
            matched = [c for c in roster.get(pair, ()) if c.asset == asset]
            if category == "trading_at_notice":
                matched = [c for c in matched if c.active(minute) and
                           (c.archive_tail_minute is None or minute < c.archive_tail_minute)]
            if category == "launched_later":
                matched = [c for c in matched if minute < c.launch_minute]
            if category == "ended_before":
                matched = [c for c in matched if c.end_minute is not None and c.end_minute <= minute]
            if category == "never_listed":
                if pair:
                    raise C.Invalid("never-listed notice has a contract")
                if any(c.asset == asset for contracts in roster.values() for c in contracts):
                    raise C.Invalid("never-listed asset collides with roster identity")
            elif len(matched) != 1:
                raise C.Invalid("map and dated contract disagree")
            else:
                mapped_launch = parse_minute(row["matched_launch_time_utc"])
                if (row["matched_launch_precision"] == "hour" and matched[0].launch_minute != mapped_launch or
                        row["matched_launch_precision"] == "day_precision" and
                        matched[0].launch_minute // 1440 != mapped_launch // 1440 or
                        row["matched_launch_precision"] not in {"hour", "day_precision"}):
                    raise C.Invalid("notice map launch provenance mismatch")
            contract = matched[0] if flag == "yes" else None
            notice_index[asset].append(minute)
            if minute > p["last_event_minute"]:
                counts["after_event_cutoff"] += 1
                counts["legacy_path_flags_after_cutoff"] += source[key]
                continue
            found = C.Notice(ticker, pair if contract else "", minute, source[key])
            previous = first.get(asset)
            if previous is None or minute < previous[0].minute:
                first[asset] = found, contract
            elif minute == previous[0].minute and (found, contract) != previous:
                raise C.Invalid("ambiguous first notice")
        if used != source.keys():
            raise C.Invalid("notice map is incomplete")
        if identity_data is not None and identity_keys != identity_data["notices"].keys():
            raise C.Invalid("identity notice coverage differs")
    except (Exception, KeyboardInterrupt):
        raise Refused("P20_NOTICE_MAP_REFUSED", NOTICE_MAP) from None
    return first, {asset: sorted(set(minutes)) for asset, minutes in notice_index.items()}, counts


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
                        observe(h, no_volume, interval if funding else None)
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
        marks, funding = set(), {}
        for kind, a, b, path, pin in files:
            checked += 1
            def observe(h, _, interval):
                if p["start"] <= h < p["end"]:
                    if kind == "markPriceKlines":
                        marks.add(h)
                    elif kind == "fundingRate":
                        if h in funding:
                            stats["duplicate_funding_clocks"] += 1
                        funding[h] = interval
            try:
                decode_archive(kind, a, b, path, pin, p, stats,
                               observe=observe if kind != "klines" else None)
            except Refused as error:
                refusals[error.code] += 1
                if len(examples) < 12:
                    examples.append([error.code, str(error.path)])
        clocks = sorted(funding)
        stats["settlements_without_mark_open"] += len(funding.keys() - marks)
        stats["settlement_clock_gaps_or_transitions"] += sum(
            right - left != funding[right] for left, right in zip(clocks, clocks[1:]))
    return dict(symbols=len(groups), files=checked, rows=dict(stats), refusals=dict(refusals), examples=examples)


def scan_notice_clocks(groups, events, p):
    """Possible red-day roles only; no price-based signal or stop selected."""
    counts, stats, repairs, signals, boundaries = Counter(), Counter(), set(), set(), set()
    for event, contract in events.values():
        if contract is None:
            continue
        memory()
        day = (event.minute // 1440) * 24
        entries = [day + (d + 1) * 24 + p["entry_hour_utc"] for d in range(p["red_days"])]
        start = max(day - 1, contract.launch_minute // 60)
        end = min(entries[-1] + p["hold_hours"] + 24, p["end"])
        if contract.end_minute is not None:
            end = min(end, max(start + 1, (contract.end_minute + 59) // 60))
        if contract.archive_tail_minute is not None and contract.archive_tail_minute <= end * 60:
            end = min(end, (contract.archive_tail_minute + 59) // 60)
            counts["potential_unverified_terminal_windows"] += 1
            boundaries.add(event.symbol)
        seen, zero, marks, rates = set(), set(), set(), {}

        def observe(h, empty, interval):
            if start <= h < end:
                if kind == "klines":
                    if h in seen:
                        raise C.Invalid("duplicate notice-window trade timestamp")
                    seen.add(h)
                    if empty:
                        zero.add(h)
                elif kind == "markPriceKlines":
                    marks.add(h)
                else:
                    rates[h] = interval

        for kind, a, b, path, pin in groups.get(event.symbol, ()):
            if a < end and start < b:
                decode_archive(kind, a, b, path, pin, p, stats, observe=observe)
        possible_signals = {h for h in (day + d * 24 - 1 for d in range(p["red_days"] + 1))
                            if start <= h < end}
        possible_signals.update(range(event.minute // 60, min(entries[-1], end)))
        entry_missing = {h for h in entries if start <= h < end and h not in seen}
        signal_missing = possible_signals - seen
        counts["first_flagged_notices"] += 1
        counts["missing_notice_hour"] += event.minute // 60 not in seen
        counts["missing_inside_candidate_envelope"] += len(seen) != end - start
        counts["potential_missing_signal"] += bool(signal_missing)
        counts["potential_missing_entry"] += bool(entry_missing)
        for h in signal_missing | entry_missing:
            signals.add((event.symbol, datetime.fromtimestamp(h * 3600, timezone.utc).date().isoformat()))
        counts["potential_zero_signal"] += bool(possible_signals & zero)
        counts["potential_zero_entry"] += bool(set(entries) & zero)
        counts["potential_zero_timed_exit"] += bool({h + p["hold_hours"] for h in entries} & zero)
        counts["potential_zero_stop_hour"] += any(entries[0] <= h < end for h in zero)
        needed = sorted(h for h in rates if entries[0] < h < end)
        no_mark = [h for h in needed if h not in marks]
        counts["potential_settlements_without_mark"] += len(no_mark)
        counts["potential_notice_windows_with_missing_marks"] += bool(no_mark)
        clock = sorted(rates)
        counts["potential_funding_clock_gaps_or_transitions"] += sum(
            right - left != rates[right] for left, right in zip(clock, clock[1:]))
        for h in no_mark:
            repairs.add((event.symbol, datetime.fromtimestamp(h * 3600, timezone.utc).date().isoformat()))
    return {"counts": dict(counts), "mark_repair_symbol_days": sorted(repairs),
            "potential_signal_or_entry_symbol_days": sorted(signals), "unverified_boundary_symbols": sorted(boundaries)}


def load(files, p):
    tape = C.Tape(p["start"] - 24, p["end"])
    quiet = Counter()
    for kind, a, b, path, pin in files:
        decode_archive(kind, a, b, path, pin, p, quiet, tape)
    tape.finish()
    return tape


def affected(symbol, files, error):
    if error.kind == "unverified_end":
        return DATED_ROSTER
    for kind, a, b, path, _ in files:
        if kind == error.kind and a <= error.hour < b:
            return path
    month = datetime.fromtimestamp(error.hour * 3600, timezone.utc).strftime("%Y-%m")
    kind = error.kind
    interval = "" if kind == "fundingRate" else "/1h"
    stem = "fundingRate" if kind == "fundingRate" else "1h"
    key = f"data/futures/um/monthly/{kind}/{symbol}{interval}/{symbol}-{stem}-{month}.zip"
    return STORES["replay_20"] / key


def control_components(groups, roster):
    """Symbols linked by a dated asset share a single seven-day trigger clock."""
    by_asset = defaultdict(set)
    for symbol in groups:
        if symbol not in roster:
            raise Refused("P20_CONTROL_ROSTER_REFUSED", DATED_ROSTER)
        for contract in roster[symbol]:
            by_asset[contract.asset].add(symbol)
    done = set()
    for symbol in sorted(groups):
        if symbol in done:
            continue
        component, todo = set(), [symbol]
        while todo:
            item = todo.pop()
            if item in component:
                continue
            component.add(item)
            for contract in roster[item]:
                todo.extend(by_asset[contract.asset] - component)
        done.update(component)
        yield sorted(component)


def control_domains(groups):
    """Clock domains for supplement-only symbols, from listed spans, not rows."""
    def ranges(slices):
        result = []
        for a, b in sorted(slices):
            if result and a <= result[-1][1]:
                result[-1] = result[-1][0], max(b, result[-1][1])
            else:
                result.append((a, b))
        return result

    domains = {}
    for symbol, files in groups.items():
        if not files or not all(isinstance(path, Path) and path.is_relative_to(STAGING) for _, _, _, path, _ in files):
            continue
        by_kind = {}
        for kind in ("klines", "markPriceKlines", "fundingRate"):
            by_kind[kind] = ranges((a, b) for k, a, b, _, _ in files if k == kind)
        a, b, c = by_kind.values()
        domains[symbol] = ranges((max(lo, mid, x), min(hi, end, y))
                                 for lo, hi in a for mid, end in b for x, y in c
                                 if max(lo, mid, x) < min(hi, end, y))
    return domains


def manifest_domains(groups):
    return {symbol: [list(span) for span in spans] for symbol, spans in control_domains(groups).items()}


def evaluate_book(groups, notice_data, roster, us, p, *, validate_only=False):
    first, notice_index, source_counts = notice_data
    events = defaultdict(list)
    absent_notices = []
    legacy = Counter()
    for event, contract in first.values():
        if contract:
            events[event.symbol].append((event, contract))
        else:
            absent_notices.append(event.ticker)
            legacy["not_trading_at_notice"] += event.legacy_path_flag
    trades, shown_us, hourly, earlier, unscreened, after_notice = [], [], [], [], [], []
    pools, clean_pools = defaultdict(list), defaultdict(list)
    disposition = dict.fromkeys(("traded", "no_red_day", "not_trading_at_notice", "no_fill", "other"), 0)
    disposition["not_trading_at_notice"] = len(absent_notices)
    absent_controls, ordinary_counts, judged_diagnostics = Counter(), Counter(), Counter()
    control_counts = {"store_symbols": 0, "supplement_only_symbols": 0}
    if set(events) - groups.keys():
        symbol = sorted(set(events) - groups.keys())[0]
        start = events[symbol][0][0].minute // 60
        raise Refused("P20_REQUIRED_KLINES", affected(symbol, (), C.InputFault("klines", start)))
    domains = control_domains(groups)
    for component in control_components(groups, roster):
        memory()
        tapes = {}
        for symbol in component:
            memory()
            tape = tapes[symbol] = load(groups[symbol], p)
            for event, contract in events[symbol]:
                try:
                    signal = C.setup(tape, event.minute, p, contract, counts=judged_diagnostics)
                    if signal is None:
                        disposition["no_red_day"] += 1
                        legacy["no_red_day"] += event.legacy_path_flag
                    else:
                        trade = C.evaluate(tape, signal, p, contract, validate_only=validate_only)
                        disposition["traded"] += 1
                        legacy["traded"] += event.legacy_path_flag
                        if not validate_only:
                            trades.append(trade)
                            if event.ticker in us and symbol == event.ticker + "USDT":
                                shown_us.append(trade)
                except C.NoFill:
                    disposition["no_fill"] += 1
                    legacy["no_fill"] += event.legacy_path_flag
                except C.InputFault as e:
                    raise Refused("P20_REQUIRED_" + e.kind.upper(), affected(symbol, groups[symbol], e)) from None
                if not validate_only:
                    variants = ((False, True, False, hourly), (True, True, False, earlier),
                                (False, False, False, unscreened), (None, False, True, after_notice))
                    for pre, screen, post, output in variants:
                        try:
                            signal = C.setup(tape, event.minute, p, contract, earlier=pre, screen=screen,
                                             post_notice_only=post)
                            if signal:
                                output.append(C.evaluate(tape, signal, p, contract))
                        except (C.NoFill, C.InputFault):
                            continue
        try:
            for trade, clean in C.ordinary(tapes, roster, notice_index, p, ordinary_counts,
                                           validate_only=validate_only, absent=absent_controls, domains=domains,
                                           source_counts=control_counts):
                pools[trade.year].append(trade.net(p["judged_bps"]))
                if clean:
                    clean_pools[trade.year].append(trade.net(p["judged_bps"]))
        except C.InputFault as e:
            raise Refused("P20_REQUIRED_" + e.kind.upper(), affected(e.symbol, groups[e.symbol], e)) from None
    if sum(disposition.values()) != len(first) or disposition["other"] or ordinary_counts["other"]:
        raise Refused("P20_NOTICE_RECONCILIATION", NOTICE_MAP)
    if validate_only:
        return
    legacy["after_event_cutoff"] = source_counts.get("legacy_path_flags_after_cutoff", 0)
    legacy["not_first_for_asset"] = source_counts.get("legacy_path_flags", 0) - sum(legacy.values())
    bps = p["judged_bps"]
    judged_values = [(t.year, t.net(bps)) for t in trades]
    return {"notice_counts": dict(source_counts), "first_notices": len(first),
            "trading_at_notice": len(first) - len(absent_notices), "notice_disposition": disposition,
            "legacy_nonjudging_path_flag_disposition": dict(legacy),
            "not_trading_at_notice_coins": sorted(absent_notices), "judged_diagnostics": dict(judged_diagnostics),
            "ordinary_disposition": dict(ordinary_counts), "not_trading_at_trigger_by_symbol": dict(absent_controls),
            "ordinary_trade_counts_by_source": control_counts,
            "judgment": C.judgment(p, judged_values, pools, memory), "judged": C.summary(trades, bps),
            "shown_clean_ordinary": C.judgment(p, judged_values, clean_pools, memory),
            "shown_last_close": C.summary([C.last_close_version(t) for t in trades], bps),
            "shown_post_notice_high": C.summary(after_notice, bps),
            "higher_fee": C.summary(trades, p["shown_bps"]), "us_today": C.summary(shown_us, bps),
            "hourly_25pct": C.summary(hourly, bps), "hourly_earlier_25pct": C.summary(earlier, bps),
            "hourly_all_jumps": C.summary(unscreened, bps)}


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
               notices_sha256=NOTICE_PIN, notice_map_sha256=NOTICE_MAP_PIN, dated_roster_sha256=DATED_ROSTER_PIN,
               supplement_sha256=SUPPLEMENT_PIN, identity_sha256=IDENTITY_PIN, lifetimes_sha256=LIFETIMES_PIN,
               us_roster_sha256=US.SHA256, repo_sha256=bound,
               started_utc=datetime.now(timezone.utc).isoformat())

    def prepare():
        groups = inventory(p)
        identity_data = identities()
        roster = dated_roster(identity_data=identity_data)
        mapped = notices(p, roster, identity_data=identity_data)
        try:
            us = {row["symbol"] for row in US.rows(A.read_pinned(US_ROSTER, US.SHA256))}
        except Exception:
            raise Refused("P20_ROSTER_REFUSED", US_ROSTER) from None
        evaluate_book(groups, mapped, roster, us, p, validate_only=True)
        memory()
        return groups, mapped, roster, us

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
            identity_data = identities()
            events, _, counts = notices(p, dated_roster(identity_data=identity_data), identity_data=identity_data)
            if args.inventory:
                print(json.dumps(dict(notices=dict(counts), first_notices=len(events),
                                      trading_at_notice=sum(c is not None for _, c in events.values()),
                                      symbols=len(groups), files=sum(map(len, groups.values())))))
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
