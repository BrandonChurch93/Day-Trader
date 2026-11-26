"""Builds the TM07 registration week table from the custodied Coinbase snapshot. Ledger 198.

It reads the snapshot read-only and uses the registered selection code at the TM07 engine commit
(score_tm07.week_selection and select_five), imported from a clean checkout of that commit.

What it reads: minute counts per coin and week, the two prior completed Sunday daily closes for
ranking vacancies and extension weeks, and the funding rows per week. What it writes: names,
counts, reasons and SHA-256 digests only. Prices and the ranking ratios stay in memory and are
never printed or saved. No arm, twin, yardstick or rule arm is replayed, and no return is computed.

    python3 tools/build_tm07_registration.py --engine /path/to/checkout-at-ENGINE --out timemachine/TM07_REGISTRATION_weeks.json
"""
import argparse, hashlib, json, sqlite3, subprocess, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ENGINE = "058a54320c2bc13043761633d828c1b2a78fbb82"
SNAPSHOT = Path("/home/user/workspace/rig/tm07_custody/tm07_coinbase_all21_20261126.sqlite")
SNAPSHOT_SHA256 = "6346be0d4a10976a3531f2f2c70dd99132bfad331c47564366e0e6f4c2e486eb"
UTC = timezone.utc
DAY, WEEK = 86400, 7 * 86400


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def engine_import(path):
    head = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(path), "status", "--porcelain", "--", "timemachine"], capture_output=True, text=True, check=True).stdout
    if head != ENGINE or dirty:
        sys.exit(f"refused: engine checkout must be clean at {ENGINE}")
    sys.path.insert(0, str(path))
    from timemachine import score_tm07 as S, desk
    return S, desk


def ts(day):
    return int(datetime(day.year, day.month, day.day, tzinfo=UTC).timestamp())


def week_item(con, S, week):
    start = ts(date.fromisoformat(week))
    watch = sorted(S.WATCH)
    counts = dict.fromkeys(watch, 0)
    for sym, n in con.execute("SELECT symbol, COUNT(*) FROM bars WHERE tf='1Min' AND t>=? AND t<? GROUP BY symbol", (start, start + WEEK)):
        if sym in counts:
            counts[sym] = n
    btc = con.execute("SELECT COUNT(*) FROM bars WHERE tf='1Min' AND symbol='BTC/USD' AND t>=? AND t<?", (start, start + WEEK)).fetchone()[0]
    # Sunday daily bars: the bar opening Sunday 00:00 UTC closes at Monday 00:00, so both are finished before the week opens.
    def closes(t):
        return {s: c for s, c in con.execute("SELECT symbol, c FROM bars WHERE tf='1Day' AND t=?", (t,)) if s in counts}
    last, before = closes(start - DAY), closes(start - 8 * DAY)
    fund = con.execute("SELECT symbol, venue, t, rate, interval_hours FROM funding WHERE t>=? AND t<=? ORDER BY symbol, venue, t",
                       (start - 8 * 3600, start + WEEK)).fetchall()
    prior = (date.fromisoformat(week) - timedelta(days=7)).isoformat()
    item = dict(minute_counts=counts, last_known_on=week, before_known_on=prior, before=before, last=last)
    return item, btc, fund


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("--engine", required=True)
    cli.add_argument("--out", required=True)
    a = cli.parse_args()
    S, desk = engine_import(Path(a.engine).resolve())
    if sha_file(SNAPSHOT) != SNAPSHOT_SHA256:
        sys.exit("refused: snapshot hash differs from the custody record")
    screen = S.screen_config()
    con = sqlite3.connect(f"file:{SNAPSHOT}?mode=ro", uri=True)
    weeks = {}
    for week in (S.DIAGNOSTIC, *S.WEEKS):
        item, btc, fund = week_item(con, S, week)
        use = "diagnostic" if week == S.DIAGNOSTIC else "screen" if week in S.SCREEN else "extension"
        row = dict(use=use, fixed=sorted(s + "/USD" for s in S.FIXED.get(week, "").split()),
                   minute_counts=item["minute_counts"], minutes_in_week=7 * 24 * 60,
                   covered_count=sum(n * 100 >= 7 * 24 * 60 * screen["min_minute_coverage_pct"] for n in item["minute_counts"].values()),
                   listed_count=len(S.listed_at_open(week, screen)),
                   sunday_pairs_count=len(set(item["before"]) & set(item["last"])),
                   btc_minute_count=btc, funding_rows=len(fund), funding_rows_sha256=digest(fund),
                   selection_inputs_sha256=digest({k: item[k] for k in ("minute_counts", "before", "last", "last_known_on", "before_known_on")}))
        try:
            five, displaced = S.week_selection(week, item, screen)
            row.update(five=five, displaced=displaced, blocked=None,
                       replaced={s: "ranked by the two prior Sunday closes" for s in five if s not in row["fixed"]})
        except ValueError as e:
            row.update(five=None, displaced=None, blocked=str(e))
        weeks[week] = row
    con.close()
    out = dict(ledger="198", engine_commit=ENGINE, snapshot=SNAPSHOT.name, snapshot_sha256=SNAPSHOT_SHA256,
               screen_hash=desk.digest(screen), cost_hash=S.canonical_cost_hash(),
               calendar=dict(screen=list(S.SCREEN), extension=list(S.EXTENSION), diagnostic=S.DIAGNOSTIC),
               marks=dict(per_claim_cap=S.ALPHA, claims=4, weeks=len(S.WEEKS), wins_needed=S.sign_mark(len(S.WEEKS)),
                          tail_at_mark=S.sign_tail(len(S.WEEKS), S.sign_mark(len(S.WEEKS))), screen_gate="3 of 3",
                          twin_draws=S.DRAW_COUNT, twin_percentile=S.PERCENTILE, twin_seed=S.SEED),
               weeks=weeks)
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    for w, r in weeks.items():
        print(w, r["use"], "blocked: " + r["blocked"] if r["blocked"] else " ".join(s.split("/")[0] for s in r["five"]),
              f"covered {r['covered_count']}/20 listed {r['listed_count']}/20 pairs {r['sunday_pairs_count']} funding_rows {r['funding_rows']}",
              "displaced " + ",".join(r["displaced"] or {}) if r.get("displaced") else "")


if __name__ == "__main__":
    main()
