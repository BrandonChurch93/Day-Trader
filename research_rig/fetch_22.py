"""Plan 22 coverage collection. Reads bar timestamps only, never prices or returns.

Lists the Binance spot 1h archives needed for the point-in-time top 30 (raw ranks
1 to 30 only), reuses the plan 13 and plan 16/17 local copies, collects what is
missing from data.binance.vision with its published checksum, and writes
manifest_22.json (paths, sha256, row counts, first and last hour)."""
import argparse
from datetime import date, timedelta
import hashlib
import json
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths_22 as PA

sys.path.insert(0, str(PA.RIG))
import fetch_13 as F  # noqa: E402

DAY_S = 86400


def needed(snapshots, p, allowed=None):
    """(pair -> set of UTC dates) for every listed coin's identity segment."""
    pages = sorted((s for s in snapshots if not s.get("hole")), key=lambda s: s["known_at"])
    floor = (p["judged_start_h"] - 32 * 24) * 3600
    ceil = p["shown_end_h"] * 3600
    want = {}
    for i, s in enumerate(pages):
        lo = s["known_at"]
        hi = pages[i + 1]["known_at"] if i + 1 < len(pages) else lo + p["max_page_age_days"] * DAY_S
        lo, hi = lo - 32 * DAY_S, hi + 3 * DAY_S
        for row in PA.top_rows(s, p):
            for a, b, pair in F.segments(row):
                if allowed is not None and (row["id"], pair) not in allowed:
                    continue
                x, y = max(lo, a, floor), min(hi, b, ceil)
                d = x - x % DAY_S
                while d < y:
                    want.setdefault(pair, set()).add(d // DAY_S)
                    d += DAY_S
    return want


def month_key(pair, d):
    return f"data/spot/monthly/klines/{pair}/1h/{pair}-1h-{d:%Y-%m}.zip"


def day_key(pair, d):
    return f"data/spot/daily/klines/{pair}/1h/{pair}-1h-{d:%Y-%m-%d}.zip"


def key_days(key):
    if "/monthly/" in key:
        m = date.fromisoformat(key[-11:-4] + "-01")
        n = (m.replace(day=28) + timedelta(days=4)).replace(day=1)
        return {(m + timedelta(days=k)).toordinal() for k in range((n - m).days)}
    return {date.fromisoformat(key[-14:-4]).toordinal()}


def local_index(pairs):
    out = {}
    m13 = json.loads((PA.R13 / "manifest.json").read_bytes())["archives"]
    m16 = json.loads((PA.R16 / "manifest_spot.json").read_bytes())["archives"]
    for key, meta in m13.items():
        if key.split("/")[4] in pairs:
            out[key] = {**meta, "where": "replay_13"}
    for key, meta in m16.items():
        if key.split("/")[4] in pairs and key not in out:
            out[key] = dict(meta)
    return out


def plan(want, local):
    """Choose one archive per needed day: local monthly, local daily, else fetch."""
    epoch = date(1970, 1, 1).toordinal()
    chosen, fetch = {}, {}
    for pair, days in sorted(want.items()):
        ords = {epoch + d for d in days}
        have = {}
        for key in local:
            if key.split("/")[4] == pair:
                for o in key_days(key):
                    if "/monthly/" in key or o not in have:
                        have[o] = key
        for o in sorted(ords):
            if o in have:
                chosen[have[o]] = local[have[o]]
            else:
                fetch.setdefault(pair, set()).add(o)
    return chosen, fetch


def download(key):
    r = F.get(F.BINANCE + key)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    raw = r.content
    c = F.get(F.BINANCE + key + ".CHECKSUM")
    c.raise_for_status()
    if c.text.split()[0] != hashlib.sha256(raw).hexdigest():
        raise ValueError(f"checksum mismatch: {key}")
    return raw


def stamp_rows(raw, key):
    ts = [F.open_epoch(r[0]) for r in F.zip_rows(raw)]
    if not ts or ts != sorted(set(ts)) or any(t % 3600 for t in ts):
        raise ValueError(f"invalid hour grid: {key}")
    days = key_days(key)
    epoch = date(1970, 1, 1).toordinal()
    if any(epoch + t // DAY_S not in days for t in ts):
        raise ValueError(f"hours outside the file's dates: {key}")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "n": len(ts), "bytes": len(raw),
            "first": ts[0], "last": ts[-1]}


def collect(go):
    p = PA.policy(final=False)
    snaps = json.loads((PA.R13 / "snapshots.json").read_bytes())
    info = json.loads((PA.R16 / "identity_policy_16_17.json").read_bytes())
    allowed = {(r["id"], r["pair"]) for r in info["as_of_rows"] if r["market"] == "spot"} | set(PA.DIRECT)
    want = needed(snaps, p, allowed)
    local = local_index(set(want))
    chosen, fetch = plan(want, local)
    listed = json.loads((PA.R13 / "archive_pairs.json").read_bytes())
    on_binance = set(listed["monthly"]) | set(listed["daily"])
    no_pair = sorted(x for x in fetch if x not in on_binance)
    for x in no_pair:
        del fetch[x]
    print("pairs with no Binance spot archive", len(no_pair), no_pair, flush=True)
    epoch = date(1970, 1, 1).toordinal()
    absent = {}
    todo = []
    for pair, ords in sorted(fetch.items()):
        months = sorted({date.fromordinal(o).replace(day=1) for o in ords})
        for m in months:
            todo.append((pair, m, sorted(o for o in ords if date.fromordinal(o).replace(day=1) == m)))
    print("pairs", len(want), "needed pair-days", sum(map(len, want.values())),
          "local files", len(chosen), "months to collect", len(todo), flush=True)
    if not go:
        for pair, m, ords in todo[:400]:
            print(" collect", pair, f"{m:%Y-%m}", len(ords), "days")
        return
    for pair, m, ords in todo:
        key = month_key(pair, m)
        path = PA.DATA / "archives" / key
        raw = path.read_bytes() if path.exists() else download(key)
        if raw is not None:
            meta = stamp_rows(raw, key)
            if not path.exists():
                F.write(path, raw)
            chosen[key] = {**meta, "where": "replay_22"}
            continue
        listed_days = set(F.list_s3(f"data/spot/daily/klines/{pair}/1h/{pair}-1h-{m:%Y-%m}")[0])
        for o in ords:
            key = day_key(pair, date.fromordinal(o))
            if key not in listed_days:
                absent.setdefault(pair, []).append(date.fromordinal(o).isoformat())
                continue
            path = PA.DATA / "archives" / key
            raw = path.read_bytes() if path.exists() else download(key)
            if raw is None:
                absent.setdefault(pair, []).append(date.fromordinal(o).isoformat())
                continue
            meta = stamp_rows(raw, key)
            if not path.exists():
                F.write(path, raw)
            chosen[key] = {**meta, "where": "replay_22"}
    for key, meta in chosen.items():
        if meta["where"] != "replay_22":
            raw = (PA.WS / "rig/data" / meta["where"] / "archives" / key).read_bytes()
            if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
                raise ValueError(f"local archive changed: {key}")
    out = {"archives": dict(sorted(chosen.items())), "absent_days": absent, "no_binance_pair": no_pair,
           "snapshots_sha256": hashlib.sha256((PA.R13 / "snapshots.json").read_bytes()).hexdigest(),
           "needed_pair_days": {k: len(v) for k, v in sorted(want.items())}}
    F.put_json(PA.DATA / "manifest_22.json", out)
    print("files", len(chosen), "absent pair-days", sum(map(len, absent.values())),
          "pairs with absent days", len(absent))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true", help="collect; without it, list only")
    collect(ap.parse_args().go)
