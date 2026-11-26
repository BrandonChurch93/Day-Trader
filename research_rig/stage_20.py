"""Plan 20 input staging: official public bulk ZIP paths and checksums only."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from shutil import disk_usage
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import build_opener, HTTPRedirectHandler

import yaml

from . import common_20 as C, score_20 as S

BULK_URL = "https://data.binance.vision/"
CLOCK = ("klines", "markPriceKlines", "fundingRate")
CHECKSUM = re.compile(rb"([a-fA-F0-9]{64})[ \t]+\*?([^\r\n]+)\r?\n?")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = build_opener(NoRedirect())


def month(hour):
    return datetime.fromtimestamp(hour * 3600, timezone.utc).strftime("%Y-%m")


def day(hour):
    return datetime.fromtimestamp(hour * 3600, timezone.utc).strftime("%Y-%m-%d")


def key(symbol, kind, period):
    frequency = "monthly" if len(period) == 7 else "daily"
    interval = "" if kind == "fundingRate" else "/1h"
    stem = "fundingRate" if kind == "fundingRate" else "1h"
    return f"data/futures/um/{frequency}/{kind}/{symbol}{interval}/{symbol}-{stem}-{period}.zip"


def atomic(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".stage")
    with tmp.open("xb") as output:
        output.write(raw)
    os.replace(tmp, path)


def read_bulk(object_path, maximum):
    for attempt in range(3):
        try:
            with OPENER.open(BULK_URL + quote(object_path, safe="/"), timeout=30) as response:
                raw = response.read(maximum + 1)
            if len(raw) > maximum:
                raise ValueError("bulk object larger than allowed")
            return raw
        except HTTPError as error:
            if error.code == 404:
                return None
            if attempt == 2 or error.code not in (429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise


def stage(object_path):
    if disk_usage(S.DATA).free < 2 * 1024**3 + S.A.MAX_ZIP_BYTES:
        raise ValueError("leave at least 2 GiB free on the data volume")
    sidecar = S.STAGING / "checksums" / (object_path + ".CHECKSUM")
    raw = sidecar.read_bytes() if sidecar.is_file() else read_bulk(object_path + ".CHECKSUM", 512)
    if raw is None:
        return None
    matched = CHECKSUM.fullmatch(raw)
    if not matched or matched[2].decode() != Path(object_path).name:
        raise ValueError("invalid named published checksum")
    expected = matched[1].decode().lower()
    path = S.STORES["replay_20"] / object_path
    data = path.read_bytes() if path.is_file() else read_bulk(object_path, S.A.MAX_ZIP_BYTES)
    if not data or sha256(data).hexdigest() != expected:
        raise ValueError("bulk archive checksum mismatch")
    if not path.is_file():
        atomic(path, data)
    if not sidecar.is_file():
        atomic(sidecar, raw)
    return expected


def base_inventory():
    existing = {}
    for path, pin in S.MANIFESTS.items():
        manifest = json.loads(S.A.read_pinned(path, pin))
        for name, spec in manifest["archives"].items():
            if existing.setdefault(name, spec) != spec:
                raise ValueError("unresolved existing archive conflict")
    return existing


def required(first, p):
    wanted = defaultdict(set)
    for event, contract in first.values():
        if contract is None:
            continue
        notice_day = event.minute // 1440 * 24
        entry_latest = notice_day + p["red_days"] * 24 + p["entry_hour_utc"]
        start = max(contract.launch_minute // 60, notice_day - 24)
        end = min(p["end"], entry_latest + p["hold_hours"] + 24)
        if contract.end_minute is not None:
            # The cover may settle funding at the exact delisting boundary.
            end = min(end, contract.end_minute // 60 + 1)
        for h in range((start // 24) * 24, end, 24):
            for kind in CLOCK:
                wanted[event.symbol, kind, month(h)].add(day(h))
    return wanted


def make(wanted, existing):
    selected, missing = {}, []
    for (symbol, kind, ym), days in sorted(wanted.items()):
        S.memory()
        monthly = key(symbol, kind, ym)
        if monthly in existing:
            # Respect the Plan 16 record of partial months. Known disjoint
            # daily repairs already in that inventory are kept rather than
            # replacing or decoding the monthly archive at this stage.
            spec = existing[monthly]
            first = day(spec["first"] // 3600)
            last = day(spec["last"] // 3600)
            holes = sorted(d for d in days if not first <= d <= last)
            if kind == "fundingRate":
                continue
        else:
            all_daily = all(key(symbol, kind, d) in existing for d in days)
            if all_daily:
                continue
            if not any(name.startswith(monthly.rsplit("/", 1)[0].replace("/monthly/", "/daily/") + "/")
                       and Path(name).name.startswith(Path(monthly).stem + "-") for name in existing):
                pin = stage(monthly)
                if pin:
                    selected[monthly] = pin
                    continue
            holes = sorted(days)
        for d in holes:
            daily = key(symbol, kind, d)
            if daily in existing:
                continue
            pin = stage(daily)
            if pin is None:
                missing.append(daily)
            else:
                selected[daily] = pin
    return selected, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster-sha256", required=True)
    parser.add_argument("--notice-map-sha256", required=True)
    parser.add_argument("--identity-sha256")
    parser.add_argument("--lifetimes-sha256")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--candidate-notices", action="store_true",
                        help="stage a superset from mapped eligible notices without publishing a manifest")
    args = parser.parse_args()
    S.configure_resources()
    p = C.policy(yaml.safe_load(S.CONFIG.read_bytes())["replay_20_plan"]["value"])
    if args.candidate_notices:
        S.A.read_pinned(S.DATED_ROSTER, args.roster_sha256)
        raw = S.A.read_pinned(S.NOTICE_MAP, args.notice_map_sha256)
        first = {}
        for row in csv.DictReader(raw.decode("utf-8-sig").splitlines()):
            if row["mapping_category"] != "trading_at_notice":
                continue
            pair = row["matched_symbol"]
            minute = S.parse_minute(row["published_at_utc"])
            launch = S.parse_minute(row["matched_launch_time_utc"])
            end = (S.parse_minute(row["matched_last_trading_time_utc"])
                   if row["matched_last_trading_source"] == "binance_delisting_announcement" else None)
            if not re.fullmatch(r"[^\W_]+", pair) or launch > minute or (end is not None and minute >= end):
                raise ValueError("inconsistent mapped eligibility")
            if minute <= p["last_event_minute"]:
                first[row["notice_id"], row["coin_ticker"], minute] = (
                    C.Notice(row["coin_ticker"], pair, minute), C.Contract(pair, pair, launch, end))
    else:
        if not args.identity_sha256 or not args.lifetimes_sha256:
            parser.error("both sidecar SHA-256 options are required for exact staging")
        identity_data = S.identities(args.identity_sha256, args.lifetimes_sha256)
        roster = S.dated_roster(args.roster_sha256, identity_data)
        first, _, _ = S.notices(p, roster, args.notice_map_sha256, identity_data)
    wanted = required(first, p)
    print(json.dumps({"required_coin_month_kinds": len(wanted),
                      "required_symbols": len({symbol for symbol, _, _ in wanted})}), flush=True)
    if args.plan_only:
        return 0
    archives, missing = make(wanted, base_inventory())
    if args.candidate_notices:
        print(json.dumps({"candidate_archives": len(archives), "missing_bulk_paths": missing}))
        return int(bool(missing))
    if missing:
        print(json.dumps({"missing_bulk_paths": missing, "unsealed_archives": len(archives)}))
        return 1
    manifest = {"version": 2, "replace": [], "archives": archives}
    manifest["control_domains"] = S.manifest_domains(S.inventory(p, candidate=manifest))
    blob = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    atomic(S.SUPPLEMENT, blob)
    print(json.dumps({"new_archives": len(archives), "manifest_sha256": S.digest(blob)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
