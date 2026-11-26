"""Checks for the Plan 58 quote sampler with pretend answers. Makes no request."""
import json, sys, tempfile
from datetime import datetime, timedelta, timezone, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sampler_p58_quotes as S

UTC = timezone.utc
N = 0


def check(ok, what):
    global N
    assert ok, what
    N += 1


def book(code, bid="100", ask="100.1", bs="1", az="2", t="2026-12-01T21:00:00.123456789Z"):
    return json.dumps(dict(pricebook=dict(product_id=code, bids=[dict(price=bid, size=bs)], asks=[dict(price=ask, size=az)], time=t),
                           last="1", mid_market="1", spread_bps="1")).encode()


def main():
    L = S.lattice(date(2026, 12, 1))
    check(len(L) == 42 and L[0][0].strftime("%H:%M:%S") == "20:55:00" and L[-1][0].strftime("%H:%M:%S") == "23:05:00", "lattice")
    check(all(lab == "sample" for _, lab in L), "a Tuesday has no maintenance")
    jf = S.lattice(date(2027, 7, 2))      # Friday in summer: 21:00 UTC is 17:00 New York
    check(sum(lab == "maintenance" for _, lab in jf) == 11 and jf[10][1] == "maintenance" and jf[9][1] == "sample", "Friday 17:00 to 18:00 New York is labelled")
    check(all(lab == "sample" for _, lab in S.lattice(date(2026, 12, 4))[:21]), "a winter Friday window ends before 17:00 New York")
    recv = datetime(2026, 12, 1, 21, 0, 1, tzinfo=UTC)
    c = S.CONTRACTS[0]
    r = S.judge_book(c, 200, book(c), recv)
    check(r["status"] == "ok" and abs(r["spread_bps"] - 10000 * 0.1 / 100.05) < 1e-3 and abs(r["book_age_s"] - 0.877) < 1e-3, "spread and age")
    check(set(r) == {"status", "book_age_s", "spread_bps"}, "no sizes, levels, mid or last kept")
    check(S.judge_book(c, 200, book(S.CONTRACTS[1]), recv)["reason"] == "product_id_mismatch", "id must match")
    check(S.judge_book(c, 200, book(c, bid="100.1", ask="100"), recv)["reason"] == "crossed_or_locked", "crossed refused")
    check(S.judge_book(c, 200, book(c, bs="0"), recv)["reason"] == "zero_size", "zero size refused")
    check(S.judge_book(c, 200, book(c, bid="0"), recv)["reason"] == "nonpositive_price", "nonpositive refused")
    check(S.judge_book(c, 200, json.dumps(dict(pricebook=dict(product_id=c, bids=[], asks=[], time="2026-12-01T21:00:00Z"))).encode(), recv)["reason"] == "empty_side", "empty refused")
    check(S.judge_book(c, 200, book(c, t="2026-12-01T20:59:50.9Z"), recv)["reason"] == "stale_book", "older than 10 s refused")
    check(S.judge_book(c, 200, book(c, t="2026-12-01T20:59:51.5Z"), recv)["status"] == "ok", "9.5 s old is kept")
    check(S.judge_book(c, 200, book(c, t="2026-12-01T21:00:02.5Z"), recv)["reason"] == "future_time", "future-dated refused")
    check(S.judge_book(c, 429, b"", recv)["reason"] == "http_429", "429 refused, no retry")
    for code in (401, 403, 451):
        try:
            S.judge_book(c, code, b"", recv); check(False, "stop")
        except S.Stop:
            check(True, f"{code} stops")
    good = dict(product_id=c, product_type="FUTURE", product_venue="FCM", future_product_details=dict(venue="cde", contract_root_unit="BTC", contract_expiry_type="EXPIRING", funding_rate="0.1"), price="9")
    p = S.judge_product(c, 200, json.dumps(good).encode())
    check(p["status"] == "ok" and "price" not in p and "funding_rate" not in p, "catalog keeps flags only")
    check(S.judge_product(c, 200, json.dumps(dict(good, product_venue="INTX")).encode())["status"] == "refused", "INTX refused")
    check(S.judge_product(c, 200, json.dumps(dict(good, future_product_details=dict(good["future_product_details"], venue="other"))).encode())["status"] == "refused", "non-CDE refused")
    check(S.judge_product(c, 200, json.dumps(dict(good, future_product_details=dict(good["future_product_details"], contract_root_unit="ETH"))).encode())["status"] == "refused", "wrong root refused")
    check(S.judge_product(c, 200, json.dumps(dict(good, product_id="BIP-27DEC26-CDE")).encode())["status"] == "refused", "other product refused")
    check(S.judge_product(c, 200, json.dumps(dict(good, product_type="SPOT")).encode())["status"] == "refused", "spot refused")
    with tempfile.TemporaryDirectory() as d:
        off = Path(d) / "q"; clock = [datetime(2026, 12, 1, 20, 54, 50, tzinfo=UTC)]; calls = []
        def now(): return clock[0]
        def sleep(s): clock[0] += timedelta(seconds=s)
        def get(url):
            calls.append((clock[0], url)); clock[0] += timedelta(seconds=0.2)
            code = url.split("product_id=")[1].split("&")[0]
            if clock[0] > datetime(2026, 12, 1, 21, 0, tzinfo=UTC) and clock[0] < datetime(2026, 12, 1, 21, 0, 40, tzinfo=UTC):
                clock[0] += timedelta(seconds=40)   # a slow answer makes the next point late
            return 200, book(code, t=S.iso(clock[0]))
        import time as _t
        mono = [0.0]
        S.time.monotonic = lambda: (clock[0] - datetime(2026, 1, 1, tzinfo=UTC)).total_seconds()
        S.run(get=get, off=off, now=now, sleep=sleep, until=date(2026, 12, 1))
        rows = [json.loads(x) for x in (off / "samples.jsonl").read_text().splitlines()]
        check(len(rows) == 84, "one row per point and contract")
        gaps = [(b[0] - a[0]).total_seconds() for a, b in zip(calls, calls[1:])]
        check(min(gaps) >= 1.0 - 1e-9, "at most one request a second")
        check(any(r["status"] == "missed" for r in rows) and len(calls) < 84, "late points are missed, not caught up")
        firsts = [r["contract"] for i, r in enumerate(rows) if i % 2 == 0 and r["status"] != "missed"]
        check(len(set(firsts)) == 2, "the first contract alternates")
        check(all(r["season"] == "standard" for r in rows) and all("receipt_late_s" in r for r in rows if r["status"] == "ok"), "season and receipt time kept")
        check(all("spread_bps" in r for r in rows if r["status"] == "ok"), "ok rows have a spread")
        check(oct((off / "samples.jsonl").stat().st_mode & 0o777) == "0o600" and oct(off.stat().st_mode & 0o777) == "0o700", "private files")
        rl = S.sample_point(datetime(2026, 12, 2, 20, 56, tzinfo=UTC), "sample", lambda u: (429, b""), off, lambda: datetime(2026, 12, 2, 20, 56, tzinfo=UTC), S.Spacer(lambda: 0.0, lambda s: None))
        check([r["reason"] for r in rl] == ["http_429", "rate_limited_tick_skipped"], "a 429 skips the rest of the tick")
        check(S.season(datetime(2027, 7, 2, 21, 0, tzinfo=UTC)) == "daylight", "summer is daylight")
        try:
            S.sample_point(datetime(2026, 12, 2, 21, 0, tzinfo=UTC), "sample", lambda u: (401, b""), off, lambda: datetime(2026, 12, 2, 21, 0, tzinfo=UTC), S.Spacer(lambda: 0.0, lambda s: None))
            check(False, "stop")
        except S.Stop:
            last = json.loads((off / "samples.jsonl").read_text().splitlines()[-1])
            check(last["status"] == "stop" and "owner futures-account" in last["reason"], "401 is logged and stops")
    print(f"{N} checks passed")


if __name__ == "__main__":
    main()
