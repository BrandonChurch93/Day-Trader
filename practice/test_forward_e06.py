"""Checks for the E06 forward logger with a pretend candle source. Makes no requests."""
import json, math, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forward_e06 as E

UTC = timezone.utc
N = 0


def fake(drop=None):
    """Smooth made-up prices: each coin drifts at its own rate, so the 7-day ranking is fixed and known."""
    def get(coin, gran, start, end):
        if drop and coin == drop and gran == 60 and end.timestamp() > fake.wake:
            return []
        out, t = [], int(start.timestamp()) // gran * gran
        k = sum(map(ord, coin)) % 17 - 8
        while t <= end.timestamp():
            p = 10 * math.exp(k * 1e-6 * (t / 60 % 1e6) / 10)
            out.append([t, p * 0.999, p * 1.001, p, p, 100.0 + k + 10])
            t += gran
        return list(reversed(out))
    return get


def check(ok, what):
    global N
    assert ok, what
    N += 1


def main():
    st, _ = E.settings()
    check(len(st["coins"]) == 20 and st["fee_bps"] == 12.0 and st["change_hours"] == 24, "pinned settings")
    with tempfile.TemporaryDirectory() as d:
        off = Path(d) / "e06"
        frz = datetime(2026, 12, 1, 9, 0, tzinfo=UTC)
        h = E.start(frz, off, commit="abc", commit_utc=frz)
        check(h["first_wake"] == "2026-12-01T14:00:00Z" and h["wakes"] == 141, "first wake is the first after the freeze")
        try:
            E.start(frz, off, commit="abc", commit_utc=frz); check(False, "second start")
        except E.Refuse:
            check(True, "start refuses twice")
        w0 = E.parse(h["first_wake"]); fake.wake = w0.timestamp()
        check(E.record(w0 + timedelta(minutes=5), fake(), off) is None, "too early does nothing")
        x = E.record(w0 + timedelta(minutes=30), fake(), off)
        check(x["kind"] == "wake" and len(x["picks"]["R1"]) == 5 and x["picks"]["R3"] == st["coins"], "a wake is recorded with five R1 picks")
        check(set(x["picks"]["R2"]) <= set(x["picks"]["R1"]), "R2 is R1 less drops")
        check(all(abs(v - 1000.0) < 1e-9 for v in x["value_before_trade"].values()), "each arm starts at 1000")
        check(E.record(w0 + timedelta(minutes=40), fake(), off) is None, "a recorded wake is not recorded again")
        w1 = w0 + timedelta(days=1); fake.wake = w1.timestamp()
        check(E.record(w1 + timedelta(minutes=200), fake(), off) is None, "after the window nothing is back-filled")
        w2 = w0 + timedelta(days=2); fake.wake = w2.timestamp()
        v = E.record(w2 + timedelta(minutes=25), fake(drop="SOL"), off)
        check(v["kind"] == "void" and v["coins"] == ["SOL/USD"], "a coin without a fill minute voids the wake")
        w3 = w0 + timedelta(days=3); fake.wake = w3.timestamp()
        y = E.record(w3 + timedelta(minutes=25), fake(), off)
        check(y["kind"] == "wake" and y["costs_usd"]["R3"] if "R3" in y["costs_usd"] else True, "R3 does not trade again")
        check("R3" not in y["costs_usd"], "R3 holds")
        a = E.alive(w3 + timedelta(hours=4), off)
        check((a["wakes_closed"], a["recorded"], a["void_logged"], a["void_missed"]) == (4, 2, 1, 1), "alive counts")
        check(set(a) == {"started", "first_wake", "wakes_total", "wakes_closed", "recorded", "void_logged", "void_missed", "last_made_utc"}, "alive shows counts only")
        try:
            E.score(w3 + timedelta(hours=4), off); check(False, "early score")
        except E.Refuse:
            check(True, "score refuses before the end")
        lines = (off / "log.jsonl").read_text().splitlines()
        (off / "log.jsonl").write_text("\n".join(lines[:1] + [lines[2], lines[1]] + lines[3:]) + "\n")
        try:
            E.read_log(off); check(False, "chain")
        except E.Refuse:
            check(True, "a reordered log is refused")
    with tempfile.TemporaryDirectory() as d:
        off = Path(d) / "e06"; E.WEEKS = 1
        frz = datetime(2026, 12, 1, 15, 0, tzinfo=UTC)
        h = E.start(frz, off, commit="abc", commit_utc=frz)
        check(h["first_wake"] == "2026-12-02T14:00:00Z" and h["wakes"] == 8, "a freeze after the wake starts the next day")
        for w in E.schedule(E.read_log(off)):
            fake.wake = w.timestamp(); E.record(w + timedelta(minutes=30), fake(), off)
        s = E.score(E.schedule(E.read_log(off))[-1] + timedelta(hours=4), off)
        check(s["void_weeks"] == 0 and len(s["weeks"]) == 1 and s["need"] == 16, "score after the end")
    print(f"{N} checks passed")


if __name__ == "__main__":
    main()
