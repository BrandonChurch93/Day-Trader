"""Plan 58, Measurement 59: forward quote-only sampler for two Coinbase US nano futures.

Prepared only. It makes no request unless it is given --approved with the ledger row, which the
lead gives after the ledger and freeze are confirmed.

Commands:
  catalog --approved 197   one public product check per contract: is it an FCM future on the CDE
                           venue, not spot or INTX? Writes field names and flags only, no prices.
  run --approved 197       polls the public product book on a 30-second UTC lattice from 20:55 to
                           21:05 and from 22:55 to 23:05 every day, until stopped.
  plan                     prints today's lattice and its labels, with no request.

What is kept for each point and contract: the scheduled UTC time, how late the request was, the
book's age (receive time minus pricebook.time), the contract code, ok or a refusal reason, and the
relative spread in basis points, 10000*(ask-bid)/mid. No sizes, levels, mid, last, OHLC, account,
key or order is kept. There is no catch-up: a point more than LATE_MAX_S late is logged as missed.
A 401 or 403 stops the sampler as an owner futures-account dependency, and a 451 stops it as a
geographic block. No other route is tried.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

UTC, NY = timezone.utc, ZoneInfo("America/New_York")
LEDGER = "197"
CONTRACTS = ("BIP-20DEC30-CDE", "ETP-20DEC30-CDE")
ROOTS = {"BIP-20DEC30-CDE": "BTC", "ETP-20DEC30-CDE": "ETH"}
BOOK = "https://api.coinbase.com/api/v3/brokerage/market/product_book?product_id={}&limit=1"
PRODUCT = "https://api.coinbase.com/api/v3/brokerage/market/products/{}"
WINDOWS = (((20, 55), (21, 5)), ((22, 55), (23, 5)))
STEP_S, MIN_GAP_S, LATE_MAX_S, TIMEOUT_S = 30, 1.0, 10.0, 8.0
BOOK_AGE_MAX_S = 10.0      # an older book is refused as stale
FUTURE_SKEW_S = 1.0        # a book stamped more than this after receipt is refused as future-dated
OFF = Path("/home/user/workspace/rig/data/p58_quotes")


class Stop(Exception):
    pass


def lattice(day):
    """All points for one UTC date, each with its label."""
    d = datetime(day.year, day.month, day.day, tzinfo=UTC)
    out = []
    for (h0, m0), (h1, m1) in WINDOWS:
        t, end = d.replace(hour=h0, minute=m0), d.replace(hour=h1, minute=m1)
        while t <= end:
            ny = t.astimezone(NY)
            out.append((t, "maintenance" if ny.weekday() == 4 and 17 <= ny.hour < 18 else "sample"))
            t += timedelta(seconds=STEP_S)
    return out


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_time(s):
    s = s.strip().replace("Z", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        n = 0
        while n < len(rest) and rest[n].isdigit():
            n += 1
        frac = rest[:n]
        tz = rest[len(frac):]
        s = f"{head}.{frac[:6].ljust(6, '0')}{tz}"
    t = datetime.fromisoformat(s)
    if t.tzinfo is None:
        raise ValueError("no zone")
    return t


def http_get(url):
    """Returns (status, body). Status 0 means no answer."""
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "Accept": "application/json",
                                               "User-Agent": "p58-quote-sampler/1"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:
        return 0, b""


def stop_for(status):
    if status in (401, 403):
        raise Stop(f"http_{status}: public endpoint asks for auth; owner futures-account dependency")
    if status == 451:
        raise Stop("http_451: geographic block")


def judge_book(code, status, body, recv):
    """Turns one answer into the kept fields, or a refusal reason."""
    stop_for(status)
    if status != 200:
        return dict(status="refused", reason=f"http_{status}" if status else "no_answer")
    try:
        pb = json.loads(body)["pricebook"]
    except Exception:
        return dict(status="refused", reason="bad_json")
    if pb.get("product_id") != code:
        return dict(status="refused", reason="product_id_mismatch")
    try:
        age = (recv - parse_time(pb["time"])).total_seconds()
    except Exception:
        return dict(status="refused", reason="bad_time")
    if age < -FUTURE_SKEW_S:
        return dict(status="refused", reason="future_time", book_age_s=round(age, 3))
    if age > BOOK_AGE_MAX_S:
        return dict(status="refused", reason="stale_book", book_age_s=round(age, 3))
    try:
        b, a = pb["bids"][0], pb["asks"][0]
        bp, bs, ap, asz = float(b["price"]), float(b["size"]), float(a["price"]), float(a["size"])
    except Exception:
        return dict(status="refused", reason="empty_side", book_age_s=round(age, 3))
    if not (bp > 0 and ap > 0):
        return dict(status="refused", reason="nonpositive_price", book_age_s=round(age, 3))
    if not (bs > 0 and asz > 0):
        return dict(status="refused", reason="zero_size", book_age_s=round(age, 3))
    if bp >= ap:
        return dict(status="refused", reason="crossed_or_locked", book_age_s=round(age, 3))
    return dict(status="ok", book_age_s=round(age, 3), spread_bps=round(10000 * (ap - bp) / ((ap + bp) / 2), 4))


def judge_product(code, status, body):
    """Catalog check: flags only, no prices, funding or open interest."""
    stop_for(status)
    if status != 200:
        return dict(contract=code, status="refused", reason=f"http_{status}" if status else "no_answer")
    try:
        p = json.loads(body)
    except Exception:
        return dict(contract=code, status="refused", reason="bad_json")
    f = p.get("future_product_details") or {}
    perp = f.get("perpetual_details") or {}
    out = dict(contract=code, product_id_match=p.get("product_id") == code, product_type=p.get("product_type"),
               product_venue=p.get("product_venue"), venue=f.get("venue"), contract_code=f.get("contract_code"),
               contract_root_unit=f.get("contract_root_unit"), contract_expiry_type=f.get("contract_expiry_type"),
               contract_expiry=f.get("contract_expiry"), display_name=p.get("display_name"),
               contract_display_name=f.get("contract_display_name"), has_funding_interval=bool(f.get("funding_interval")),
               has_perpetual_details=bool(perp), view_only=p.get("view_only"), trading_disabled=p.get("trading_disabled"))
    out["is_us_fcm_future"] = (out["product_id_match"] and out["product_type"] == "FUTURE" and out["product_venue"] == "FCM"
                               and str(out["venue"] or "").lower() == "cde" and out["contract_root_unit"] == ROOTS[code]
                               and out["contract_expiry_type"] in ("EXPIRING", "PERPETUAL"))
    out["status"] = "ok" if out["is_us_fcm_future"] else "refused"
    if not out["is_us_fcm_future"]:
        out["reason"] = "not_the_cde_fcm_future_for_this_root"
    return out


class Spacer:
    """At most one request per MIN_GAP_S, across all contracts."""
    def __init__(self, clock, sleep):
        self.clock, self.sleep, self.last = clock, sleep, None

    def wait(self):
        if self.last is not None:
            gap = MIN_GAP_S - (self.clock() - self.last)
            if gap > 0:
                self.sleep(gap)
        self.last = self.clock()


def write(off, name, row):
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    if off.stat().st_mode & 0o077:
        raise Stop("log folder must be private")
    fd = os.open(off / name, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a") as f:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def catalog(get=http_get, off=OFF, now=lambda: datetime.now(UTC), sleep=time.sleep):
    sp, rows = Spacer(time.monotonic, sleep), []
    for code in CONTRACTS:
        sp.wait()
        st, body = get(PRODUCT.format(code))
        r = judge_product(code, st, body); r["checked_utc"] = iso(now()); rows.append(r)
        write(off, "catalog.jsonl", r)
    return rows


def sample_point(t, label, get, off, now, sp):
    rows = []
    for code in CONTRACTS:
        base = dict(schedule_utc=iso(t), contract=code)
        if label == "maintenance":
            rows.append(dict(base, status="maintenance", reason="friday_17_18_new_york"))
            continue
        sp.wait()
        late = (now() - t).total_seconds()
        if late > LATE_MAX_S:
            rows.append(dict(base, status="missed", reason="late_no_catch_up", late_s=round(late, 3)))
            continue
        st, body = get(BOOK.format(code))
        recv = now()
        try:
            rows.append(dict(base, late_s=round(late, 3), **judge_book(code, st, body, recv)))
        except Stop as e:
            rows.append(dict(base, late_s=round(late, 3), status="stop", reason=str(e)))
            for r in rows:
                write(off, "samples.jsonl", r)
            raise
    for r in rows:
        write(off, "samples.jsonl", r)
    return rows


def run(get=http_get, off=OFF, now=lambda: datetime.now(UTC), sleep=time.sleep, until=None):
    """Walks the lattice forward from now. Points before the start are skipped; points missed while running
    are logged as missed and never fetched."""
    sp = Spacer(time.monotonic, sleep)
    began = now(); day = began.date()
    while until is None or day <= until:
        for t, label in lattice(day):
            late = (now() - t).total_seconds()
            if late > LATE_MAX_S:
                if t >= began:
                    for code in CONTRACTS:
                        write(off, "samples.jsonl", dict(schedule_utc=iso(t), contract=code, status="missed", reason="late_no_catch_up", late_s=round(late, 3)))
                continue
            if late < 0:
                sleep(-late)
            sample_point(t, label, get, off, now, sp)
        day += timedelta(days=1)


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("command", choices=["plan", "catalog", "run"])
    cli.add_argument("--approved", default=None, help="the ledger row the lead approved")
    a = cli.parse_args()
    if a.command == "plan":
        for t, label in lattice(datetime.now(UTC).date()):
            print(iso(t), label)
        return
    if a.approved != LEDGER:
        sys.exit(f"refused: {a.command} makes live requests; it needs --approved {LEDGER} after the lead confirms the ledger and freeze")
    try:
        if a.command == "catalog":
            for r in catalog():
                print(json.dumps({k: r.get(k) for k in ("contract", "status", "reason", "product_type", "product_venue", "venue", "contract_root_unit", "contract_expiry_type")}))
        else:
            run()
    except Stop as e:
        sys.exit(f"stopped: {e}")


if __name__ == "__main__":
    main()
