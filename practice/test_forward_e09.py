"""Checks for the E09 forward logger on made-up candles with a pretend venue. Makes no requests.

The main check: on the same made-up hourly bars, the trades the logger opens wake by wake are exactly the tickets that
research_rig/sweep_70.py (score_signal and order_times, rule 70-102 of GRID_70.json) picks on the whole tape at once."""
import json, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forward_e09 as E
import sweep_71  # noqa: E402  (on the path through forward_e09)

UTC = timezone.utc
HOUR = 3600
N = 0


def check(ok, what):
    global N
    assert ok, what
    N += 1


def made_up_panel(seed, hours):
    """Bitcoin with sharp falls; the other coins follow it with a larger beta and their own noise; a few bars missing."""
    rng = np.random.default_rng(seed)
    k, n = len(E.COINS), len(hours)
    btc = rng.normal(0, 0.009, n)
    btc[rng.choice(n, n // 15, replace=False)] -= 0.02
    logp = np.zeros((k, n))
    for j, c in enumerate(E.COINS):
        beta = 1.0 if c == "BTC" else rng.uniform(1.2, 3.0)
        r = beta * btc + (0 if c == "BTC" else rng.normal(0, 0.006, n))
        logp[j] = np.log(rng.uniform(0.5, 500)) + np.cumsum(r)
    close = np.exp(logp)
    o = np.c_[close[:, :1], close[:, :-1]] * np.exp(rng.normal(0, 0.001, (k, n)))
    hi, lo = np.maximum(o, close) * 1.002, np.minimum(o, close) * 0.998
    panel = np.stack([o, hi, lo, close, rng.uniform(10, 100, (k, n))], axis=-1)
    gone = rng.random((k, n)) < 0.01
    panel[gone] = np.nan
    return panel


class Venue:
    """Serves the made-up candles as the public pages would at the wake: only hours that have begun, newest first."""
    def __init__(self, hours, panel, futures_refused=()):
        self.hours, self.panel, self.now, self.futures_refused = hours, panel, None, set(futures_refused)

    def candles(self, coin, start, end):
        j = E.COINS.index(coin); out = []
        for i, t in enumerate(self.hours):
            if start.timestamp() <= t <= min(end.timestamp(), self.now) and np.isfinite(self.panel[j, i, 0]):
                out.append((int(t), *map(float, self.panel[j, i])))
        return list(reversed(out))

    def _px(self, coin):
        j = E.COINS.index(coin); i = int(np.searchsorted(self.hours, self.now, side="right") - 1)
        p = self.panel[j, i, 0]
        return float(p if np.isfinite(p) else np.nanmean(self.panel[j, :, 3]))

    def spot_book(self, coin):
        p = self._px(coin); return dict(bid=p * 0.9995, ask=p * 1.0005, venue_time=None)

    def futures_book(self, code):
        coin = next(c for c, f in E.FUT.items() if f == code)
        if coin in self.futures_refused:
            raise E.Refuse("venue refused with HTTP 403")
        p = self._px(coin); return dict(bid=p * 0.999, ask=p * 1.001, venue_time=None)


def sweep_tickets(hours, panel, rule):
    tape = E.sweep_70.Tape(list(E.COINS), panel, hours=hours, split=None)
    j, i = E.sweep_70.order_times(tape, rule, E.sweep_70.score_signal(tape, rule))
    return [(E.COINS[a], E.iso(datetime.fromtimestamp(int(hours[b]), UTC))) for a, b in zip(j, i)]


def run_logger(hours, panel, off, skip=(), late=(), futures_refused=()):
    E.LAST_WAKE = datetime.fromtimestamp(int(hours[-1]), UTC)
    v = Venue(hours, panel, futures_refused)
    clock = lambda: datetime.fromtimestamp(v.now, UTC)
    def sleep(s):
        v.now += s
    E.start(datetime.fromtimestamp(int(hours[3]) - 1800, UTC), off, commit="abc")
    for t in hours[3:]:
        if int(t) in skip:
            continue
        v.now = int(t) + (200 if int(t) in late else 20)
        E.record(clock(), v, off, clock, sleep)
    v.now = int(hours[-1]) + 3 * HOUR
    E.record(clock(), v, off, clock, sleep)   # logs any trailing missed wakes
    return E.read_log(off)


def main():
    st = E.settings()
    check(len(st["coins"]) == 20 and st["rules"]["70-102"]["parameters"] == {"lag": 2, "threshold": 0.015, "multiple": 2.0}, "pinned rule and coins")
    check(st["rules"]["71-013"]["hold_hours"] == 2 and st["rules"]["71-035"]["hold_hours"] == 1 and st["rules"]["71-035"]["parameters"]["lag"] == 1, "shown rules 71-013 and 71-035")
    check(st["futures_route_round_trip_bp"]["SUI"] == 21.89 and st["funding_bp_per_hour"] == 1 and st["spot_taker_round_trip_bp"] == 160, "plan 70 costs")
    check(set(E.FUT) == set(E.COINS) and E.FUT["BTC"] == "BIP-20DEC30-CDE", "a US contract for every coin")
    keep = E.LAST_WAKE
    t0 = int(datetime(2027, 1, 7, tzinfo=UTC).timestamp())
    hours = np.arange(t0, t0 + 300 * HOUR, HOUR, dtype=np.int64)
    total = 0
    for seed in (1, 2):
        panel = made_up_panel(seed, hours)
        with tempfile.TemporaryDirectory() as d:
            log = run_logger(hours, panel, Path(d) / "e09")
        for arm in E.ARMS:
            want = sweep_tickets(hours, panel, st["rules"][arm])
            got = [(e["coin"], e["wake"]) for x in log[1:] for e in x.get("entries", []) if e["arm"] == arm]
            check(len(want) > 5 and got == want, f"seed {seed} {arm}: logger trades match sweep_70 on the same bars ({len(got)} vs {len(want)})")
            total += len(want)
        tape = sweep_71.old.Tape(list(E.COINS), panel, hours=hours, split=None)
        for arm in ("71-013", "71-035"):
            r = st["rules"][arm]
            cj, ci, *_ = sweep_71.ticket_legs(tape, r, np.zeros(len(E.COINS)), 1)
            res = [(E.COINS[a], E.iso(datetime.fromtimestamp(int(hours[b]), UTC))) for a, b in zip(cj[0], ci)]
            check(set(res) <= set(sweep_tickets(hours, panel, r)), f"{arm}: sweep_71 tickets are the same sweep_70 tickets")
        rows = E.trades(log)
        check(all(r["exit_wake"] == E.iso(E.parse(r["entry_wake"]) + timedelta(hours=st["rules"][r["arm"]]["hold_hours"])) for r in rows), "exit after the hold")
        for r in rows:
            if E.sweep_70.maintenance(E.parse(r["entry_wake"]).timestamp()) or E.sweep_70.maintenance(E.parse(r["exit_wake"]).timestamp()):
                check(False, "a trade touches the Friday maintenance hour")
        snaps = [x for x in log[1:] if x["kind"] == "quotes"]
        sig = [x for x in log[1:] if x["kind"] != "quotes" and x.get("quotes")]
        check(len(snaps) == 3 * len(sig) and {q["quotes"]["offset_s"] for q in snaps} == {60, 300, 900}, "1, 5 and 15 minute quotes after every signal or exit")
        check(all("BTC" in x["quotes"][0]["coins"] and x["quotes"][0]["taken_s"] == 20 for x in sig), "bitcoin is quoted too, with seconds after the hour")
        r = next(r for r in rows if r["arm"] == "70-102" and r["judged_ok"])
        m = E.money(r, st)
        a, b = r["entry_quotes"][0]["coins"][r["coin"]]["spot"]["ask"], r["exit_quotes"][0]["coins"][r["coin"]]["spot"]["bid"]
        fee = (st["futures_route_round_trip_bp"][r["coin"]] + 2) / 1e4
        check(abs(m["a_spot_quotes_at_wake"] - (b / a - 1 - fee)) < 1e-12, "judged line buys the wake ask, sells the exit bid, pays fee and funding")
        check(abs(m["shown_spot_taker_fee"] - (b / a - 1 - 0.016)) < 1e-12 and {"shown_spot_quotes_plus_1m", "shown_spot_quotes_plus_5m",
              "shown_spot_quotes_plus_15m", "shown_futures_quotes_at_wake"} <= set(m), "shown lines")
    # One signal-level check: the made-up drop the card describes
    R = st["rules"]["70-102"]
    w = datetime(2027, 1, 7, 12, tzinfo=UTC); n = int(w.timestamp())
    bars = {c: {n - 3 * HOUR: (1, 1, 1, 1.0, 1), n - 2 * HOUR: (1, 1, 1, 1.0, 1), n - HOUR: (1, 1, 1, 1.0, 1)} for c in E.COINS}
    bars["BTC"][n - HOUR] = (1, 1, 1, float(np.exp(-0.015)), 1)
    bars["SOL"][n - HOUR] = (1, 1, 1, float(np.exp(-0.0301)), 1)
    bars["ADA"][n - HOUR] = (1, 1, 1, float(np.exp(-0.0301)), 1)
    bars["XRP"][n - HOUR] = (1, 1, 1, float(np.exp(-0.0300)), 1)
    check(E.decide(w, bars, R)[0] == "ADA", "a 0.015 bitcoin fall picks the largest excess drop, alphabetical tie")
    bars["BTC"][n - HOUR] = (1, 1, 1, float(np.exp(-0.0149)), 1)
    check(E.decide(w, bars, R) is None, "a bitcoin fall under 0.015 gives no trade")
    bars["BTC"][n - HOUR] = (1, 1, 1, float(np.exp(-0.02)), 1)
    check(E.decide(w, bars, R) is None, "no coin falling more than twice bitcoin gives no trade")
    fri = datetime(2027, 1, 8, 20, tzinfo=UTC)   # 15:00 New York; exit at 17:00 New York is in the maintenance hour
    fb = {c: {int(fri.timestamp()) - k * HOUR: v for k, v in zip((3, 2, 1), (bars[c][n - 3 * HOUR], bars[c][n - 2 * HOUR], bars[c][n - HOUR]))} for c in E.COINS}
    fb["SOL"][int(fri.timestamp()) - HOUR] = (1, 1, 1, float(np.exp(-0.05)), 1)
    check(E.decide(fri, fb, R) is None and E.decide(fri - timedelta(hours=1), {c: {t - HOUR: v for t, v in b.items()} for c, b in fb.items()}, R)[0] == "SOL",
          "an exit in the Friday maintenance hour is skipped, an hour earlier is not")
    # Missed and late wakes, unresolved exits, unknown futures quotes, counts-only outputs and the score lock
    panel = made_up_panel(4, hours)
    want = sweep_tickets(hours, panel, st["rules"]["70-102"])
    exit_t = int(E.parse(want[0][1]).timestamp()) + 2 * HOUR
    skip = {exit_t, exit_t + 5 * HOUR}
    late_w = next(w for _, w in want[1:] if not {int(E.parse(w).timestamp()), int(E.parse(w).timestamp()) + 2 * HOUR} & skip)
    late_t = int(E.parse(late_w).timestamp())
    with tempfile.TemporaryDirectory() as d:
        off = Path(d) / "e09"
        log = run_logger(hours, panel, off, skip=skip, late={late_t}, futures_refused={want[0][0]})
        x = next(y for y in log[1:] if y["wake"] == E.iso(datetime.fromtimestamp(exit_t, UTC)) and y["kind"] != "quotes")
        ex = [e for e in x["exits"] if e["arm"] == "70-102"]
        check(x["kind"] == "void" and ex and ex[0]["status"] == "unresolved", "a missed exit wake is void and the trade unresolved, never back-filled")
        first = next(y for y in log[1:] if y["kind"] != "quotes" and y.get("quotes") and y["wake"] == want[0][1])
        check(first["quotes"][0]["coins"][want[0][0]]["futures"] == "UNKNOWN", "a refused futures quote is UNKNOWN")
        rows = E.trades(log)
        lr = next(r for r in rows if r["arm"] == "70-102" and r["entry_wake"] == late_w)
        check(lr["status"] == "complete" and not lr["judged_ok"] and "a_spot_quotes_at_wake" not in E.money(lr, st)
              and "shown_spot_quotes_plus_1m" in E.money(lr, st), "a wake more than 120 seconds late is void for the judged line only")
        wakes = [y["wake"] for y in log[1:] if y["kind"] != "quotes"]
        check(len(wakes) == len(set(wakes)) == len(hours) - 3, "every wake has exactly one line")
        a = E.counts(datetime.fromtimestamp(int(hours[-1]) + 3 * HOUR, UTC), off)
        check(a["void_logged"] >= 2 and a["void_not_yet_logged"] == 0 and a["wakes_closed"] == len(hours) - 3, "counts of void wakes")
        check(a["first_quote_seconds_after_hour"]["over_120"] >= 1 and a["arms"]["70-102"]["trades_unresolved"] >= 1, "counts of late quotes and unresolved trades")
        blob = json.dumps(a)
        check(not any(k in blob for k in ("money", "usd", "gross", "ask", "bid", "price", "shown_", "a_spot")), "counts show no prices or profit")
        p = Path(d) / "E09_log.json"; E.publish(datetime.fromtimestamp(int(hours[-1]) + 3 * HOUR, UTC), off, p)
        check(json.loads(p.read_text())["arms"] == a["arms"], "the public log holds the counts")
        E.LAST_WAKE = keep
        try:
            E.score(datetime.fromtimestamp(int(hours[-1]) + 3 * HOUR, UTC), off); check(False, "early score")
        except E.Refuse:
            check(True, "score refuses before 150 trades or the stop date")
        E.LAST_WAKE = datetime.fromtimestamp(int(hours[-1]), UTC)
        s = E.score(datetime.fromtimestamp(int(hours[-1]) + 3 * HOUR, UTC), off)
        check(s["judged"]["verdict"] in ("too few to judge", "pass", "did not pass") and set(E.ARMS) <= set(s), "score after the stop date")
        lines = (off / "log.jsonl").read_text().splitlines()
        (off / "log.jsonl").write_text("\n".join(lines[:1] + [lines[2], lines[1]] + lines[3:]) + "\n")
        try:
            E.read_log(off); check(False, "chain")
        except E.Refuse:
            check(True, "a reordered log is refused")
    E.LAST_WAKE = keep
    # The marks on made-up trade rows
    def rows(vals, days):
        return [dict(entry_wake=E.iso(datetime(2027, 1, 1, tzinfo=UTC) + timedelta(days=dd, hours=k % 20)), money=dict(a_spot_quotes_at_wake=v))
                for k, (v, dd) in enumerate(zip(vals, days))]
    rng = np.random.default_rng(7)
    good = rows(list(0.004 + rng.normal(0, 0.01, 150)), [k // 2 for k in range(150)])
    j = E.judge(good, st, False)
    check(j["verdict"] == "pass" and j["marks_met"] == 3 and j["trades"] == 150, "a clear edge passes all three marks")
    lucky = rows([-0.001] * 148 + [0.2, 0.2], range(150))
    j = E.judge(lucky, st, False)
    check(j["marks"]["mean_a_above_zero"] and not j["marks"]["positive_without_best_2"] and j["verdict"] == "did not pass", "two lucky trades do not pass")
    check(E.judge(rows([0.01] * 59, range(59)), st, True)["verdict"] == "too few to judge", "under 60 trades by the date is too few")
    check(E.judge(rows(list(0.004 + rng.normal(0, 0.01, 170)), range(170)), st, False)["trades"] == 150, "judged on the first 150 trades")
    # Freeze: a changed pinned file stops recording
    with tempfile.TemporaryDirectory() as d:
        off = Path(d) / "e09"
        h = E.start(datetime(2027, 1, 7, 10, 30, tzinfo=UTC), off, commit="abc")
        check(h["first_wake"] == "2027-01-07T11:00:00Z" and set(h["sha256"]) == set(E.PINNED), "header pins card, logger and plan 70 files")
        lines = (off / "log.jsonl").read_text().splitlines(); hd = json.loads(lines[0]); hd["sha256"][E.ME] = "0" * 64
        (off / "log.jsonl").write_text(E.enc(hd) + "\n")
        try:
            E.record(datetime(2027, 1, 7, 11, 2, tzinfo=UTC), Venue(hours, panel), off); check(False, "freeze")
        except E.Refuse:
            check(True, "a changed logger is refused")
        check(not (Path(d) / "e09" / "log.jsonl").stat().st_mode & 0o077, "private log file mode")
    print(f"{N} checks passed ({total} made-up trades matched sweep_70 across the three rules)")


if __name__ == "__main__":
    main()
