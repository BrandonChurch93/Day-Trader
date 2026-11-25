"""perp_fast.run_perp against perp.run_perp on made-up minute paths: the book, the records and the final value must be equal
to the last digit (compared with ==, and with repr of the whole result). Covers longs and shorts, stops and targets with gaps,
close-outs, funding from a file and from the fallback, no-change answers, a flat start, and the Minutes and plain-list inputs.
Run: python3 timemachine/test_perp_fast.py. Standard library only."""
import datetime as dt, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from timemachine import perp as P, perp_fast as F  # noqa: E402

UTC = dt.timezone.utc; checks = 0


def iso(t):
    return dt.datetime.fromtimestamp(t, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def world(rng, nsym, days, wake_h, gappy):
    syms = [f"C{i}/USD" for i in range(nsym)]; t0 = int(dt.datetime(2026, 3, 2, tzinfo=UTC).timestamp()); t1 = t0 + days * 86400
    px = {s: rng.uniform(0.5, 300) for s in syms}; rows = []; vol = {s: rng.uniform(0.0005, 0.01) for s in syms}
    for t in range(t0, t1, 60):
        for s in syms:
            if gappy and rng.random() < 0.3:
                continue  # a minute with no bar
            o = px[s] * (1 + rng.gauss(0, vol[s]) * (8 if rng.random() < 0.002 else 1)); c = o * (1 + rng.gauss(0, vol[s]))
            h, l = max(o, c) * (1 + abs(rng.gauss(0, vol[s]))), min(o, c) * (1 - abs(rng.gauss(0, vol[s]))); px[s] = c
            rows.append((t, s, o, h, l, c))
    rows.sort()
    wakes = list(range(t0, t1, wake_h * 3600)); last = {}; trows = []; it = 0
    for w in wakes:
        while it < len(rows) and rows[it][0] < w:
            last[rows[it][1]] = rows[it][5]; it += 1
        fills = {}
        for s in syms:
            nxt = next((r for r in rows[it:it + 400] if r[1] == s), None)
            fills[s] = (iso(nxt[0]), nxt[2]) if nxt else None
        trows.append(dict(marks={s: last.get(s, px[s]) for s in syms}, fills=fills))
    end_marks = {s: next(r[5] for r in reversed(rows) if r[1] == s) for s in syms}
    meta = dict(wakes=[iso(w) for w in wakes], end_utc=iso(t1), opening={})
    return syms, rows, dict(rows=trows, end_marks=end_marks), meta


def answers(rng, syms, table, lev, exits_share):
    out = []
    for k, row in enumerate(table["rows"]):
        if k and rng.random() < 0.3:
            out.append((None, None)); continue
        names = rng.sample(syms, rng.randint(0, len(syms)))
        w = {s: rng.choice([-1, 1]) * rng.uniform(0.1, 1) for s in names}; g = sum(abs(v) for v in w.values()) or 1
        w = {s: v / g * lev for s, v in w.items()}; ex = {}
        for s, v in w.items():
            if rng.random() < exits_share:
                m = row["marks"][s]; d = rng.uniform(0.002, 0.04)
                e = {"stop": m * (1 - d if v > 0 else 1 + d), "target": m * (1 + 2 * d if v > 0 else 1 - 2 * d)}
                if rng.random() < 0.3:
                    e.pop(rng.choice(["stop", "target"]))
                ex[s] = e
        out.append((w, ex or None))
    return out


def same(a, b, what):
    global checks
    assert a[2] == b[2], f"{what}: final {a[2]!r} != {b[2]!r}"
    assert a[0] == b[0], f"{what}: books differ"
    assert repr(a) == repr(b), f"{what}: records differ"
    checks += 1


def main():
    rng = random.Random(20261125); closeouts = exits = 0
    for case in range(24):
        nsym = rng.randint(1, 5); syms, rows, table, meta = world(rng, nsym, rng.randint(1, 3), rng.choice([1, 4, 24]), case % 3 == 0)
        funding = {s: {h: rng.gauss(0, 2e-5) for h in range(rows[0][0] // 3600 * 3600, rows[-1][0] + 7200, 3600)} for s in syms[: nsym // 2]}
        cfg = dict(tm_perp_funding_files={}, tm_perp_fee_bps_per_side={"default": rng.choice([0, 2, 5])}, tm_perp_half_spread_bps={"default": rng.choice([1, 5, 20])},
                   tm_perp_maintenance={"default": rng.choice([0.005, 0.05, 0.3])}, tm_perp_funding_hours={"default": rng.choice([1, 8])}, tm_perp_fallback_rate_per_day=0.0003,
                   tm_perp_closeout_penalty=0.01, tm_perp_min_change=rng.choice([0.0, 0.02]), tm_account_start_usd=1000.0)
        pp = P.p_params(syms, cfg, funding=funding)
        lev = rng.choice([0.5, 1.0, 3.0, 10.0]); ans = answers(rng, syms, table, lev, rng.choice([0.0, 0.5, 1.0]))
        for mins in (P.Minutes(rows), rows):
            for opening in ({}, {syms[0]: 1.0}):
                m = dict(meta, opening=opening)
                a = P.run_perp(m, table, ans, pp, mins, cfg); b = F.run_perp(m, table, ans, pp, mins, cfg)
                same(a, b, f"case {case}"); closeouts += len(a[0]["closeouts"]); exits += len(a[0]["exits_hit"])
    assert closeouts and exits, "the made-up paths must reach close-outs and stops or targets"
    print(f"{checks} checks passed (close-outs {closeouts}, exits {exits})")


if __name__ == "__main__":
    main()
