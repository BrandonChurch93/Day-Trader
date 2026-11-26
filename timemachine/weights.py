"""Weights sessions: the trader answers each wake with target weights, and the desk moves the book there. Pretend money only.

A weights session asks one thing: how much to hold of each allowed symbol. There are no picks, stops or targets, and
nothing happens between wakes. At each wake the trader sends
    {"weights": {"BTC/USD": 0.6}, "why": "..."}        each weight 0 to 1, the sum at most 1, the rest is cash
or  {"no_change": true, "why": "..."}                  keep the current target (no trade)
The desk then moves the book to the target at the open of the first recorded minute at or after the wake (stocks: at
or after the next regular open when the wake is outside regular hours), with the same half spread and crypto fee as
the pick sessions, trading only the difference. A symbol whose weight would move by less than tm_weights_min_change
is not traded; a move to zero weight is always traded. A repeated answer, like no_change, trades nothing, except that a
move left unfilled because no minute was recorded before the next wake is tried again at the next wake.

Leverage (optional): a session made with max_gross above 1 lets the weights add up to max_gross; borrowed dollars pay
financing each whole UTC hour (stored perpetual funding where tm_lev_funding_files has the symbol, else
tm_lev_fixed_rate_per_day), and on every recorded minute between wakes lev_scan() closes the whole book out when the
account value at the minute's low falls below the maintenance share of gross position value. Without max_gross (or at
1.0) none of this runs and every result is as before.

The fast tape (optional): `new --tape fast` makes a crypto session on the second price store tape_fast.sqlite. session.json
then carries tape_readonly and tape_name, and the session, its twins and its scorer open that file read-only. Spot costs
are as on the main tape. Without the flag nothing changes.

Perpetual futures (optional): a session made by timemachine/perp.py carries instrument "perp" and is opened as a
perp.PSession, with its own book (signed weights, funding, stops and targets). Every other session never reaches it.

The book arithmetic is one pure function, step_book(), used by the session, the twins and timemachine/score_weights.py
alike. Prices come only from the tape: fill_row() reads the fill minute after the wake and the as-of price at the wake.

A session folder under $TM_RUNS (the same layout as a pick session):
  session.json        what the session is (kind "weights"; never changed)
  progress.json       the one file that holds the state: wake k, the book, every step. Written in one go after each answer.
  account.json        a copy of the book, for reading
  records/wakes.jsonl one line per answered wake: weights asked, weights held after fills, book value, the why text
  picks/<TRADER>/<wake id>.json   each answer as the trader sent it
  packets/<k>.json    what the trader was shown at wake k (made once, then served again as it is)
  looks.jsonl         every extra lookup
  result.json         written after the last wake
Every session is one line in timemachine/SESSIONS.jsonl with kind "weights". Standard library only.

python3 timemachine/weights.py new --trader W01 --model M --method CARD.md --market crypto --symbols BTC/USD \
    --from 2026-04-01 --to 2026-11-23 [--open cash | --open '{"BTC/USD": 1}'] [--wakes pick-hours|weekly|JSON] [--news] [--session ID]
"""
import argparse, datetime as dt, hashlib, json, math, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from timemachine import session as S
from timemachine.tape import Tape

UTC, NY = S.UTC, S.NY
iso, parse = S.iso, S.parse
W_KEYS = ["tm_weights_min_change", "tm_weights_sum_tolerance", "tm_weights_return_days", "tm_weights_weekly_weekday", "tm_weights_weekly_time_ny",
          "tm_weights_max_headlines_per_symbol", "tm_weights_news_first_wake_hours", "tm_weights_why_max_chars", "tm_weights_twin_draws", "tm_weights_twin_seed", "tm_weights_pass_percentile"]
LIMITS = [S.LIMITS[1], S.LIMITS[2], S.LIMITS[3], S.LIMITS[4], S.LIMITS[5],
          "Fills are assumed: the open of the first recorded minute at or after the wake, a fixed half spread, and the crypto fee. There is no cap on the share of a minute's volume. They are not real fills.",
          "The book is valued at the last recorded price at each wake, with no cost of selling taken off.",
          "Nothing happens between wakes: the book drifts with prices and is not moved back to the target until the trader answers with a new target."]
HARD_LINES = S.HARD_LINES


def w_config(path=ROOT / "config" / "thresholds.yaml"):
    out, key = {}, None
    for line in open(path):
        m = re.match(r"^([a-z0-9_]+):\s*$", line)
        if m:
            key = m.group(1); continue
        m = re.match(r"^  value:\s*(.*)$", line)
        if m and key in W_KEYS:
            v = m.group(1).strip()
            out[key] = [float(x) for x in v.strip("[]").split(",") if x.strip()] if v.startswith("[") else float(v)
    bad = [k for k in W_KEYS if k not in out]
    assert not bad, f"missing in config/thresholds.yaml: {bad}"
    return out


def full_config():
    cfg = S.full_config(); cfg.update(w_config()); return cfg


# ---- wakes
def default_rules(market, kind, cfg):
    if kind == "weekly":
        return [dict(every="week", weekday=int(cfg["tm_weights_weekly_weekday"]), ny_time=cfg["tm_weights_weekly_time_ny"])]
    if market == "crypto":
        return [dict(every="day", utc_hours=list(cfg["tm_crypto_wake_hours_utc"]))]
    return [dict(every="session_day", ny_times=list(cfg["tm_stock_wake_times_ny"]))]


def ny_time(d, x):
    h = int(x); m = int(round((x - h) * 60))
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=NY).astimezone(UTC)


def window_end(tape, market, start_date, end_date):
    d0, d1 = dt.date.fromisoformat(start_date), dt.date.fromisoformat(end_date)
    if market == "crypto":
        return dt.datetime(d0.year, d0.month, d0.day, tzinfo=UTC), dt.datetime(d1.year, d1.month, d1.day, tzinfo=UTC) + dt.timedelta(days=1)
    rows = tape.sessions(start_date, end_date)
    assert rows, f"the tape has no stock sessions from {start_date} to {end_date}"
    return dt.datetime(d0.year, d0.month, d0.day, tzinfo=NY).astimezone(UTC), rows[-1][2]


def make_wakes(tape, market, start_date, end_date, rules):
    """Every wake time the rules give inside the window, sorted. Rules:
    {"every": "day", "utc_hours": [..]}         every calendar day (stocks: session days only) at these UTC hours
    {"every": "session_day", "ny_times": [..]}  every stock session day at these New York times (hours, 15.5 is 15:30)
    {"every": "week", "weekday": 4, "ny_time": 15.5}  once a week; Monday is 0. Stocks: that day, or the last session day before it that week.
    {"every": "minutes", "step": 15}            every 15 minutes (60 for hourly, 240 for every 4 hours); stocks: inside regular hours only"""
    d0, d1 = dt.date.fromisoformat(start_date), dt.date.fromisoformat(end_date)
    start, end = window_end(tape, market, start_date, end_date)
    days = [d0 + dt.timedelta(days=i) for i in range((d1 - d0).days + 1)]
    sess_days = {dt.date.fromisoformat(r[0]) for r in tape.sessions(start_date, end_date)}
    out = set()
    for r in rules:
        ev = r.get("every")
        if ev == "day":
            for d in days:
                if market == "stocks" and d not in sess_days:
                    continue
                for h in r["utc_hours"]:
                    out.add(dt.datetime(d.year, d.month, d.day, tzinfo=UTC) + dt.timedelta(hours=h))
        elif ev == "session_day":
            assert market == "stocks", "a session_day rule is for stock sessions"
            for d in sorted(sess_days):
                for x in r["ny_times"]:
                    out.add(ny_time(d, x))
        elif ev == "week":
            wd = int(r["weekday"]); weeks = {}
            for d in days:
                weeks.setdefault(d.isocalendar()[:2], []).append(d)
            for wk, ds in sorted(weeks.items()):
                cand = [d for d in ds if d.weekday() <= wd and (market == "crypto" or d in sess_days)]
                if market == "crypto":
                    cand = [d for d in cand if d.weekday() == wd]
                if cand:
                    out.add(ny_time(max(cand), r["ny_time"]))
        elif ev == "minutes":  # every `step` minutes: crypto from the window start; stocks inside each regular session, from its open
            step = dt.timedelta(minutes=int(r["step"])); assert step.total_seconds() >= 60, "a minutes rule needs step of 1 or more"
            spans = [(start, end)] if market == "crypto" else [(op, cl) for _, op, cl in tape.sessions(start_date, end_date)]
            for a, b in spans:
                t = a
                while t < b:
                    out.add(t); t += step
        else:
            raise AssertionError(f"unknown wake rule {r}")
    return sorted(t for t in out if start <= t < end), end


# ---- prices: only from the tape
def fill_window(tape, market, wake, nxt):
    """The time span in which the answer given at `wake` fills: from the wake (stocks: from the next regular open when the
    market is closed) to the next wake (stocks: or the close of that session, whichever is first)."""
    if market == "crypto":
        return wake, nxt
    after = wake if tape.is_open(wake) else tape.next_open(wake)
    if after is None or after >= nxt:
        return None, None
    return after, min(nxt, tape.next_close(after))


def fill_row(tape, market, symbols, wake, nxt):
    """For each symbol: the fill minute (its start time and open) for an answer given at `wake`, and the as-of price at
    the wake (the last finished bar). The fill minute starts at or after the wake, so the trader never saw it."""
    after, before = fill_window(tape, market, wake, nxt)
    fills = {}
    for s in symbols:
        b = None
        if after is not None:
            if "/" not in s:
                d = after.astimezone(NY).date().isoformat()
                if not tape.has_minutes(s, d):
                    tape.ensure_minutes(s, d)
            b = tape.fill_bar(s, after, before)
        fills[s] = [iso(b["t"]), b["o"]] if b else None
    marks = {s: x["price"] for s, x in tape.snapshot(list(symbols), wake).items()}
    return dict(fills=fills, marks=marks)


def priced(meta):
    """The symbols the desk reads prices for: the allowed list, and the benchmark (held by a yardstick only) if it is not on it."""
    return list(dict.fromkeys(list(meta["symbols"]) + ([meta["benchmark"]] if meta.get("benchmark") else [])))


def end_marks(tape, symbols, end):
    return {s: x["price"] for s, x in tape.snapshot(list(symbols), end).items()}


def price_table(tape, meta):
    """Fill rows for every wake and the marks at the end, for twins and the scorer. The same reads the session makes."""
    wakes = [parse(w) for w in meta["wakes"]]; end = parse(meta["end_utc"]); syms = priced(meta)
    rows = [fill_row(tape, meta["market"], syms, w, wakes[i + 1] if i + 1 < len(wakes) else end) for i, w in enumerate(wakes)]
    return dict(rows=rows, end_marks=end_marks(tape, syms, end))


# ---- the book: one pure function
def new_book(start_usd, opening=None):
    return dict(cash=float(start_usd), qty={}, target=dict(opening or {}), spread_usd=0.0, fee_usd=0.0, traded_usd=0.0, last_px={}, pending=False)


def norm(w):
    return {s: float(v) for s, v in sorted((w or {}).items()) if float(v) > 0}


def value_at(book, px):
    return book["cash"] + sum(q * px.get(s, book["last_px"].get(s, 0.0)) for s, q in book["qty"].items())


def weights_at(book, px):
    v = value_at(book, px)
    return {s: (q * px.get(s, book["last_px"].get(s, 0.0)) / v if v > 0 else 0.0) for s, q in sorted(book["qty"].items()) if q > 0}


def step_book(book, answer, row, cfg, first, max_gross=1.0):
    """Moves `book` (changed in place) for one wake. `answer` is a weights dict, or None for no change.
    Returns a record of what was done. A trade happens at the first wake (to reach the opening or answered weights)
    and at any wake whose target differs from the standing one; otherwise nothing is traded."""
    marks = row["marks"]; fills = row["fills"]
    for s, p in marks.items():
        book["last_px"][s] = p
    value_before = value_at(book, marks)
    target = norm(book["target"]) if answer is None else norm(answer)
    retry = bool(book.get("pending"))  # the last move left a symbol unfilled for want of a recorded minute: try again now
    # the opening book (kept at the first wake, or retried after a missing minute) is bought whole: tm_weights_min_change
    # is for changes the trader asks for, and an opening share below it (an equal share of a long list) must still be bought
    opening_buy = (first and answer is None) or (retry and answer is None and bool(book.get("opening_retry")))
    changed = first or retry or target != norm(book["target"])
    book["target"] = target
    rec = dict(target=target, changed=changed, retry=retry, value_before=value_before, trades=[], skipped=[])
    if not changed:
        rec.update(value_after=value_before, weights_after=weights_at(book, marks), fill_utc=None)
        return rec
    fp = {s: f[1] for s, f in fills.items() if f}
    px = {s: fp.get(s, marks.get(s, book["last_px"].get(s, 0.0))) for s in set(book["qty"]) | set(target)}
    V = value_at(book, px); cur = {s: (book["qty"].get(s, 0.0) * px[s] / V if V > 0 else 0.0) for s in px}
    mc, hs_c, hs_s = cfg["tm_weights_min_change"], cfg["tm_crypto_half_spread_bps"] / 1e4, cfg["tm_stock_half_spread_bps"] / 1e4
    fee_c, in_coin = cfg["practice_crypto_fee_bps_added"] / 1e4, bool(cfg["practice_crypto_fee_in_coin"])
    sells, buys = [], []
    for s in sorted(px):
        w, c, q = target.get(s, 0.0), cur[s], book["qty"].get(s, 0.0)
        if w == c or (q <= 0 and w <= 0):
            continue
        if s not in fp:
            rec["skipped"].append(dict(symbol=s, why="no recorded minute to fill in before the next wake", want=w, held=c)); continue
        if abs(w - c) < mc and not (w <= 0 < q) and not opening_buy:
            rec["skipped"].append(dict(symbol=s, why="change smaller than tm_weights_min_change", want=w, held=c)); continue
        (sells if w < c else buys).append((s, w, c))
    for s, w, c in sells:
        p = fp[s]; hs = hs_c if "/" in s else hs_s; fee = fee_c if "/" in s else 0.0; q = book["qty"].get(s, 0.0)
        qs = q if w <= 0 else min(q, (c - w) * V / p)
        gross = qs * p * (1 - hs); f = gross * fee; book["cash"] += gross - f
        book["qty"][s] = q - qs
        if w <= 0 or book["qty"][s] <= 0:
            book["qty"].pop(s, None)
        book["spread_usd"] += qs * p * hs; book["fee_usd"] += f; book["traded_usd"] += qs * p
        rec["trades"].append(dict(symbol=s, side="sell", qty=qs, open=p, price=p * (1 - hs), fee_usd=f, fill_utc=fills[s][0]))
    need = []
    for s, w, c in buys:
        p = fp[s]; hs = hs_c if "/" in s else hs_s; fee = fee_c if "/" in s else 0.0; dv = (w - c) * V
        need.append((s, p, hs, fee, dv, dv * (1 + hs) * (1 + (0.0 if in_coin else fee))))
    tot = sum(x[5] for x in need)
    if max_gross > 1.0:  # leverage: buys may borrow, up to gross positions of max_gross times the account value
        room = book["cash"] + (max_gross - 1.0) * max(V, 0.0); scale = max(0.0, min(1.0, room / tot)) if tot > 0 else 1.0
    else:
        scale = min(1.0, book["cash"] / tot) if tot > 0 else 1.0
    for s, p, hs, fee, dv, cash_need in need:
        pay = cash_need * scale; notional = pay / (1 + (0.0 if in_coin else fee)); f = notional * fee
        qb = notional / (p * (1 + hs)) * ((1 - fee) if in_coin else 1.0)
        book["cash"] = (book["cash"] - pay) if max_gross > 1.0 else max(0.0, book["cash"] - pay); book["qty"][s] = book["qty"].get(s, 0.0) + qb
        book["spread_usd"] += notional - notional / (1 + hs); book["fee_usd"] += f; book["traded_usd"] += notional / (1 + hs)
        rec["trades"].append(dict(symbol=s, side="buy", qty=qb, open=p, price=p * (1 + hs), fee_usd=f, fill_utc=fills[s][0], scaled=scale))
    book["pending"] = any(x["why"].startswith("no recorded minute") for x in rec["skipped"])
    book["opening_retry"] = opening_buy and book["pending"]
    rec.update(value_after=value_at(book, px), weights_after=weights_at(book, px), fill_utc=min([t["fill_utc"] for t in rec["trades"]], default=None))
    return rec


def run_answers(meta, table, answers, cfg, lev=None, minutes=None):
    """The whole session from a list of answers (weights dict or None per wake), with the stored price table.
    Returns (book, records, final value). Used by the twins and the scorer.
    With lev (from lev_params) and minutes (from lev_minutes), the book may borrow up to lev["max_gross"] and between
    wakes every recorded minute is checked by lev_scan for financing and the maintenance rule."""
    book = new_book(cfg["tm_account_start_usd"], meta.get("opening"))
    if lev is not None:
        lev_book(book, cfg); wakes = [parse(w) for w in meta["wakes"]]; end = parse(meta["end_utc"]); recs = []
        for k, a in enumerate(answers):
            r = step_book(book, a, table["rows"][k], cfg, k == 0, lev["max_gross"])
            t0 = parse(r["fill_utc"]) if r["fill_utc"] else wakes[k]
            r["lev"] = lev_scan(book, minutes, max(t0, wakes[k]), wakes[k + 1] if k + 1 < len(wakes) else end, lev, cfg); recs.append(r)
        for s, p in table["end_marks"].items():
            book["last_px"][s] = p
        return book, recs, max(0.0, value_at(book, table["end_marks"]))
    recs = [step_book(book, a, table["rows"][k], cfg, k == 0) for k, a in enumerate(answers)]
    for s, p in table["end_marks"].items():
        book["last_px"][s] = p
    return book, recs, value_at(book, table["end_marks"])


# ---- leverage (optional; a session without max_gross, or with 1.0, never reaches this code)
LEV_KEYS = ["tm_lev_fixed_rate_per_day", "tm_lev_maintenance_crypto", "tm_lev_maintenance_stocks", "tm_lev_closeout_penalty", "tm_lev_funding_files"]
LEV_PROPOSED = ROOT / "timemachine" / "leverage_keys_PROPOSED.yaml"


def lev_config(path=ROOT / "config" / "thresholds.yaml", proposed=LEV_PROPOSED, keys=None):
    """The leverage keys, from config/thresholds.yaml; any key not there yet is read from the proposal file, and the
    result says which keys came from where."""
    from timemachine.score_tm03 import flow
    def read(fp):
        out, key = {}, None
        if not Path(fp).exists():
            return out
        for line in open(fp):
            m = re.match(r"^([a-z0-9_]+):\s*$", line)
            if m:
                key = m.group(1); continue
            m = re.match(r"^  value:\s*(.*)$", line)
            if m and key in want:
                v = m.group(1).strip(); out[key] = flow(v) if v.startswith(("{", "[")) else float(v)
        return out
    want = list(keys or LEV_KEYS); main, prop = read(path), read(proposed)
    out = {k: main.get(k, prop.get(k)) for k in want}
    bad = [k for k, v in out.items() if v is None]
    assert not bad, f"leverage keys missing from config/thresholds.yaml and {proposed}: {bad}"
    out["_from"] = {k: ("config/thresholds.yaml" if k in main else str(Path(proposed).relative_to(ROOT))) for k in want}
    return out


def load_funding(path):
    """Hourly perpetual funding from a stored Kraken file: {hour epoch: relative rate per hour}. Positive: longs pay."""
    p = Path(path); p = p if p.is_absolute() else ROOT.parent / p
    rates = json.loads(p.read_text()).get("rates") or []
    return {int(to_dt(r["timestamp"]).timestamp()) // 3600 * 3600: float(r["relativeFundingRate"]) for r in rates}


def to_dt(x):
    return dt.datetime.fromisoformat(x.replace("Z", "+00:00"))


def lev_params(market, symbols, max_gross, lc=None, funding=None):
    """Everything the leverage path needs. funding: {symbol: {hour epoch: rate}}; by default read from tm_lev_funding_files
    for the symbols that have a file; the others pay tm_lev_fixed_rate_per_day."""
    lc = lc or lev_config(); files = lc["tm_lev_funding_files"] or {}
    if funding is None:
        funding = {s: load_funding(files[s]) for s in symbols if s in files}
    return dict(max_gross=float(max_gross), maint=float(lc["tm_lev_maintenance_crypto" if market == "crypto" else "tm_lev_maintenance_stocks"]),
                penalty=float(lc["tm_lev_closeout_penalty"]), fixed_per_hour=float(lc["tm_lev_fixed_rate_per_day"]) / 24.0, funding=funding,
                source={s: ("funding file " + str(files[s]) if s in funding and s in files else "funding given" if s in funding else "tm_lev_fixed_rate_per_day") for s in symbols})


def lev_minutes(tape, symbols, t0, t1):
    """Every recorded 1Min bar of the symbols from t0 to t1, sorted: (start epoch, symbol, low, close)."""
    out = []
    for s in symbols:
        out += [(int(b["t"].timestamp()), s, b["l"], b["c"]) for b in tape.bars(s, "1Min", t0, t1) if b["t"] < t1]
    return sorted(out)


def lev_book(book, cfg):
    book.update(financing_usd=0.0, penalty_usd=0.0, shortfall_usd=0.0, closeouts=[], lev_peak=float(cfg["tm_account_start_usd"]), lev_largest_drop=0.0)


def lev_scan(book, minutes, t0, t1, lev, cfg):
    """From t0 to t1 (a wake to the next): financing on borrowed dollars at each whole UTC hour, and the maintenance rule
    on every recorded minute. A minute whose low puts the account value below lev["maint"] of gross position value closes
    the whole book at that low, less the half spread, the crypto fee and lev["penalty"]; the book then stays in cash until
    the next wake, where its standing target is bought again. The account value is never below zero: a shortfall is
    recorded and set to zero. Also keeps the largest drop of the account value on minute lows."""
    import bisect
    a, b = int(t0.timestamp()), int(t1.timestamp()); keys = [m[0] for m in minutes]
    i0, i1 = bisect.bisect_left(keys, a), bisect.bisect_left(keys, b)
    hours = list(range((a // 3600 + 1) * 3600, b + 1, 3600))
    hs_c, hs_s, fee_c = cfg["tm_crypto_half_spread_bps"] / 1e4, cfg["tm_stock_half_spread_bps"] / 1e4, cfg["practice_crypto_fee_bps_added"] / 1e4
    px = dict(book["last_px"]); rec = dict(financing_usd=0.0, closeout=None, fixed_hours=0); hi = 0
    def finance(h):
        q = book["qty"]; borrowed = max(0.0, -book["cash"])
        if borrowed <= 0 or not q:
            return
        vals = {s: x * px.get(s, 0.0) for s, x in q.items()}; tot = sum(vals.values()) or 1.0; cost = 0.0
        for s, v in vals.items():
            r = lev["funding"].get(s, {}).get(h)
            if r is None:
                r = lev["fixed_per_hour"]; rec["fixed_hours"] += 1
            cost += borrowed * v / tot * r
        book["cash"] -= cost; book["financing_usd"] += cost; rec["financing_usd"] += cost
    for j in range(i0, i1):
        t, s, lo, cl = minutes[j]
        while hi < len(hours) and hours[hi] <= t:
            finance(hours[hi]); hi += 1
        if not book["qty"]:
            px[s] = cl; continue
        low_px = dict(px); low_px[s] = lo
        gross = sum(q * low_px.get(x, 0.0) for x, q in book["qty"].items()); eq = book["cash"] + gross
        book["lev_largest_drop"] = min(book["lev_largest_drop"], max(eq, 0.0) / book["lev_peak"] - 1 if book["lev_peak"] > 0 else 0.0)
        if gross > 0 and eq < lev["maint"] * gross:
            got = 0.0
            for x, q in book["qty"].items():
                hs = hs_c if "/" in x else hs_s; fee = fee_c if "/" in x else 0.0; g = q * low_px[x] * (1 - hs)
                pen = g * lev["penalty"]; f = g * fee; got += g - pen - f
                book["spread_usd"] += q * low_px[x] * hs; book["fee_usd"] += f; book["penalty_usd"] += pen; book["traded_usd"] += q * low_px[x]
            book["cash"] += got; book["qty"] = {}; short = max(0.0, -book["cash"])
            if short:
                book["shortfall_usd"] += short; book["cash"] = 0.0
            rec["closeout"] = dict(utc=iso(dt.datetime.fromtimestamp(t, UTC)), symbol=s, value_before=eq, value_after=book["cash"], shortfall_usd=short)
            book["closeouts"].append(rec["closeout"]); book["pending"] = True; book["opening_retry"] = False
            book["lev_largest_drop"] = min(book["lev_largest_drop"], book["cash"] / book["lev_peak"] - 1 if book["lev_peak"] > 0 else 0.0)
        px[s] = cl
        if book["qty"]:
            book["lev_peak"] = max(book["lev_peak"], book["cash"] + sum(q * px.get(x, 0.0) for x, q in book["qty"].items()))
    while hi < len(hours):
        finance(hours[hi]); hi += 1
    for s, p in px.items():
        book["last_px"][s] = p
    return rec


# ---- answers
def check_weights(w, allowed, cfg, what="weights", max_gross=1.0):
    errs = []
    if not isinstance(w, dict):
        return [f"{what} must be a JSON object of symbol to weight, for example {{\"{allowed[0]}\": 0.5}}."]
    for s, v in w.items():
        if s not in allowed:
            errs.append(f"{s} is not one of the allowed symbols: {', '.join(allowed)}.")
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
            errs.append(f"The weight for {s} is not a number.")
        elif v < 0 or v > max_gross:
            errs.append(f"The weight for {s} is {v}. Each weight must be from 0 to 1 (long only, no borrowing)." if max_gross <= 1 else
                        f"The weight for {s} is {v}. Each weight must be from 0 to {max_gross:g} (long only).")
    if not errs and sum(w.values()) > max_gross + cfg["tm_weights_sum_tolerance"]:
        errs.append(f"The weights add up to {sum(w.values())}. They must add up to at most 1. The rest is cash." if max_gross <= 1 else
                    f"The weights add up to {sum(w.values())}. They must add up to at most {max_gross:g}. Above 1 is borrowed.")
    return errs


DRIVERS = ["price", "news", "filing", "headline", "both", "more than one", "nothing new"]
OPTIONAL = {"driver", "reasons"}


def check_answer(body, allowed, cfg, basket_size=None, max_gross=1.0):
    mx = int(cfg["tm_weights_why_max_chars"])
    if not isinstance(body, dict):
        return ["The body must be a JSON object."]
    why = body.get("why")
    if not isinstance(why, str) or not why.strip() or len(why) > mx:
        return [f"Every answer needs \"why\": one short plain paragraph (at most tm_weights_why_max_chars characters)."]
    errs = []
    if "driver" in body and body["driver"] not in DRIVERS:
        errs.append(f"driver, if given, is one of: {', '.join(DRIVERS)}.")
    if "reasons" in body and not (isinstance(body["reasons"], dict) and all(k in allowed and isinstance(v, str) and len(v) <= mx for k, v in body["reasons"].items())):
        errs.append("reasons, if given, is an object of allowed symbol to one plain line.")
    if "no_change" in body:
        if body.get("no_change") is not True or set(body) - OPTIONAL != {"no_change", "why"}:
            return errs + ['A no-change answer is {"no_change": true, "why": "..."} (driver and reasons may be added).']
        return errs
    if set(body) - OPTIONAL != {"weights", "why"}:
        return errs + ['An answer is {"weights": {...}, "why": "..."} or {"no_change": true, "why": "..."} (driver and reasons may be added).']
    errs += check_weights(body["weights"], allowed, cfg, max_gross=max_gross)
    if not errs and basket_size:
        w = body["weights"]; names = [k for k, v in w.items() if v > 0]; tol = cfg["tm_weights_sum_tolerance"]
        if len(names) != basket_size or any(abs(w[k] - 1.0 / basket_size) > tol for k in names):
            errs.append(f"This session holds exactly {basket_size} names in equal shares: give each of {basket_size} symbols the weight 1/{basket_size}.")
    return errs


# ---- making a session
def create(session_id, trader_id, model, method_path, start_date, end_date, symbols, market="crypto", opening=None, rules=None, wake_kind="daily",
           news=False, tape=None, note=None, benchmark=None, basket_size=None, max_gross=None, tape_name=None):
    assert re.fullmatch(r"[A-Z0-9-]{2,12}", trader_id), "trader id: 2 to 12 capital letters, digits or dashes"
    assert re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", session_id) and ".." not in session_id, "session id: 3 to 80 letters, digits, dot, dash or underscore"
    assert market in ("crypto", "stocks")
    symbols = list(dict.fromkeys(symbols)); assert symbols, "a weights session needs at least one allowed symbol"
    assert all(("/" in s) == (market == "crypto") for s in symbols), "crypto sessions take pairs like BTC/USD; stock sessions take tickers"
    tape = tape or Tape(); cfg = full_config(); folder = S.runs_dir() / session_id
    if folder.exists():
        raise FileExistsError(f"session {session_id} already exists")
    mg = float(max_gross) if max_gross is not None else 1.0; assert mg >= 1.0, "max_gross is 1 or more"
    opening = dict(opening or {}); errs = check_weights(opening, symbols, cfg, "the opening weights", max_gross=mg)
    assert not errs, " ".join(errs)
    assert basket_size is None or 0 < int(basket_size) <= len(symbols), "basket size: from 1 to the number of allowed symbols"
    rules = rules or default_rules(market, wake_kind, cfg)
    wl, end = make_wakes(tape, market, start_date, end_date, rules)
    assert wl, "no wake falls inside the window"
    benchmark = benchmark or ("BTC/USD" if market == "crypto" else "SPY")
    mp = Path(method_path.split("#")[0]); mp = mp if mp.is_absolute() else ROOT / mp
    chash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    meta = dict(session=session_id, kind="weights", trader=trader_id, model=model, method=method_path, method_sha256=S.sha256_file(mp), market=market,
                window=dict(start=start_date, end=end_date), symbols=symbols, watch=symbols, opening=dict(opening), wake_rules=rules,
                wakes=[iso(w) for w in wl], end_utc=iso(end), benchmark=benchmark, config=cfg, config_hash=chash, created_utc=iso(dt.datetime.now(UTC)),
                git=S.git_commit(), tape=str(tape.path), note=note, news=bool(news), basket_size=int(basket_size) if basket_size else None)
    if mg > 1.0:  # only a leveraged session carries these, so every other session.json is as before
        lc = lev_config(); meta.update(max_gross=mg, leverage={k: v for k, v in lc.items()})
    if getattr(tape, "readonly", False):  # a session on the fast tape opens it read-only again (session_tape)
        meta.update(tape_readonly=True, tape_name=tape_name or "fast")
    folder.mkdir(parents=True)
    (folder / "session.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n")
    line = dict(session=session_id, kind="weights", trader=trader_id, model=model, method=method_path, method_sha256=meta["method_sha256"], market=market,
                window=meta["window"], symbols=symbols, opening=opening, wake_rules=rules, news=bool(news), basket_size=meta["basket_size"], benchmark=benchmark,
                wakes=dict(count=len(wl), first=meta["wakes"][0], last=meta["wakes"][-1]), config_hash=chash, created_utc=meta["created_utc"],
                git_commit=meta["git"]["commit"], git_dirty=meta["git"]["dirty"], runs_folder=str(folder))
    log = S.sessions_log(); log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n"); f.flush(); os.fsync(f.fileno())
    book = new_book(cfg["tm_account_start_usd"], opening)
    if mg > 1.0:
        lev_book(book, cfg)
    S.save_json(folder / "progress.json", dict(k=0, done=False, bad={}, looks={}, steps=[], book=book, clock=meta["wakes"][0]))
    return folder


def is_weights(session_id):
    p = S.runs_dir() / session_id / "session.json"
    return p.exists() and json.loads(p.read_text()).get("kind") == "weights"


def session_tape(meta):
    """The session's own tape. A session made on the fast tape (tape_readonly in session.json) opens it read-only."""
    return Tape(meta.get("tape"), readonly=bool(meta.get("tape_readonly")))


def fast_tape():
    """The second price store, read-only: $TM_STORE/tape_fast.sqlite (another job fills it; nothing here writes to it)."""
    from timemachine.tape import DEFAULT_STORE
    return Tape(Path(os.environ.get("TM_STORE", str(DEFAULT_STORE))) / "tape_fast.sqlite", readonly=True)


def open_session(session_id, tape=None, *, desk_token=None):
    """Open a regular session or an authenticated, separately stored TM07 desk."""
    if desk_token is not None:
        from timemachine.desk import open_desk
        return open_desk(session_id, token=desk_token)
    if is_weights(session_id):
        meta = json.loads((S.runs_dir() / session_id / "session.json").read_text())
        if meta.get("tape_readonly") and (tape is None or str(tape.path) != meta.get("tape")):
            tape = session_tape(meta)  # a fast tape session never runs on the main tape the server passes in
    if is_weights(session_id) and json.loads((S.runs_dir() / session_id / "session.json").read_text()).get("instrument") == "perp":
        if (json.loads((S.runs_dir() / session_id / "session.json").read_text()).get("tm06") or {}).get("part") == "P":
            from timemachine.tm06 import PickerSession  # plan TM06's daily coin picker: a perp session with its own packet and answer
            return PickerSession(session_id, tape=tape)
        if (json.loads((S.runs_dir() / session_id / "session.json").read_text()).get("tm06") or {}).get("part") == "S":
            from timemachine.tm06 import SwingSession  # plan TM06's hourly swing session: more bars and a volume row in the packet
            return SwingSession(session_id, tape=tape)
        from timemachine.perp import PSession
        return PSession(session_id, tape=tape)
    return WSession(session_id, tape=tape) if is_weights(session_id) else S.Session(session_id, tape=tape)


class _Rec:
    def __init__(self, d):
        self.dir = d


class WSession(S.Session):
    """A weights session. Lookups (look, looks_left, bad) are the pick session's own."""

    def __init__(self, session_id, tape=None):
        self.dir = S.runs_dir() / session_id
        if not (self.dir / "session.json").exists():
            raise KeyError(f"no session {session_id}")
        self.meta = json.loads((self.dir / "session.json").read_text()); self.cfg = self.meta["config"]
        assert self.meta.get("kind") == "weights"
        self.prog = json.loads((self.dir / "progress.json").read_text())
        self.tape = tape or session_tape(self.meta)
        self.wakes = [parse(w) for w in self.meta["wakes"]]; self.end = parse(self.meta["end_utc"]); self.N = len(self.wakes)
        self.now = parse(self.prog["clock"]); self.tid = self.meta["trader"]; self.rec = _Rec(self.dir / "records")
        self.allowed = self.meta["symbols"]; self.mg = float(self.meta.get("max_gross") or 1.0)
        self.lev = lev_params(self.meta["market"], priced(self.meta), self.mg, lc=self.meta["leverage"]) if self.mg > 1.0 else None
        if self.prog["k"] >= self.N and not self.prog["done"]:
            self.finish()  # a stop between the last answer and the result file: finish now

    def save(self):
        self.prog["clock"] = iso(self.now); S.save_json(self.dir / "progress.json", self.prog)

    def status(self):
        k = self.prog["k"]
        return dict(session=self.meta["session"], kind="weights", trader=self.tid, done=self.done(), status="DONE" if self.done() else "waiting for an answer",
                    step=min(k + 1, self.N), of=self.N, utc=iso(self.now), looks_left=None if self.done() else self.looks_left(),
                    bad_attempts=self.prog["bad"].get(str(k), 0))

    # ---- what the trader sees
    def symbol_rows(self):
        days = self.cfg["tm_weights_return_days"]; out = {}
        assert max(days) < self.cfg["tm_look_max_days"], "tm_weights_return_days must be shorter than tm_look_max_days"
        snap = self.tape.snapshot(self.allowed, self.now)
        for s in self.allowed:
            bars = self.tape.bars(s, "1Day", self.now - dt.timedelta(days=self.cfg["tm_look_max_days"]), self.now)  # closed bars only
            row = dict(price=snap[s]["price"] if s in snap else None, price_utc=iso(snap[s]["t"]) if s in snap else None)
            if bars:
                last = bars[-1]; row["last_daily_close"] = last["c"]; row["last_daily_bar"] = iso(last["t"])
                for d in days:
                    back = [b for b in bars if b["t"] <= last["t"] - dt.timedelta(days=d)]
                    row[f"return_{d:g}d"] = (last["c"] / back[-1]["c"] - 1) if back and back[-1]["c"] else None
            out[s] = row
        return out

    def book_view(self):
        b = self.prog["book"]; marks = {s: x["price"] for s, x in self.tape.snapshot(list(b["qty"]), self.now).items()}
        v = value_at(b, marks); start = self.cfg["tm_account_start_usd"]
        hold = {s: dict(qty=q, value_usd=q * marks.get(s, b["last_px"].get(s, 0.0)), weight=(q * marks.get(s, b["last_px"].get(s, 0.0)) / v if v > 0 else 0.0))
                for s, q in sorted(b["qty"].items())}
        return dict(cash_usd=b["cash"], value_usd=v, start_usd=start, gain_pct=(v / start - 1) * 100, holdings=hold, cash_weight=(b["cash"] / v if v > 0 else 1.0),
                    target_now=norm(b["target"]), costs_paid_usd=b["spread_usd"] + b["fee_usd"], traded_usd=b["traded_usd"])

    def news_rows(self):
        """Headlines and filings since the last wake, for the allowed symbols only. All SEC filings; at most
        tm_weights_max_headlines_per_symbol other headlines per symbol, newest first. Returns (items, left_out)."""
        if not self.meta.get("news"):
            return None, None
        k = self.prog["k"]; cap = int(self.cfg["tm_weights_max_headlines_per_symbol"])
        since = self.wakes[k - 1] if k > 0 else self.now - dt.timedelta(hours=self.cfg["tm_weights_news_first_wake_hours"])
        lim = max(1, cap * len(self.allowed))
        while True:  # read every story in the window (the cap is applied below, per symbol), so filings are never crowded out
            got = self.tape.news(self.now, symbols=self.allowed, since_utc=since, limit=lim)
            if len(got) < lim:
                break
            lim *= 2
        items = [a for a in got if a["created"] > since or k == 0]
        tags = {s: {s, s.replace("/", "")} for s in self.allowed}; used = {s: 0 for s in self.allowed}; left = {}; out = []
        for a in items:  # newest first
            mine = [s for s in self.allowed if tags[s] & set(a["symbols"])]
            if a["source"] != "sec_edgar":
                room = [s for s in mine if used[s] < cap]
                if not room:
                    for s in mine:
                        left[s] = left.get(s, 0) + 1
                    continue
                for s in mine:
                    used[s] += 1
            out.append(dict(utc=iso(a["created"]), headline=a["headline"], source=a["source"], symbols=a["symbols"], edited_later=bool(a.get("edited_later"))))
        return out, left

    def packet(self, fresh=False):
        if self.done():
            raise S.Done()
        k = self.prog["k"]; p = self.dir / "packets" / f"{k}.json"
        if p.exists() and not fresh:
            return json.loads(p.read_text())
        last = self.prog["steps"][-1] if self.prog["steps"] else None; nw, nleft = self.news_rows()
        out = dict(session=self.meta["session"], kind="weights", trader=self.tid, utc=iso(self.now), step=k + 1, of=self.N,
                   next_wake_utc=iso(self.next_time(k)), is_last=k + 1 == self.N, market=self.meta["market"], allowed=self.allowed,
                   symbols=self.symbol_rows(), book=self.book_view(), news=nw, news_left_out=nleft,
                   last_wake=None if last is None else dict(utc=last["utc"], asked=last["asked"], why=last["why"], trades=last["trades"], skipped=last["skipped"],
                                                            weights_after=last["weights_after"]),
                   looks_left=self.looks_left(), hard_lines=HARD_LINES,
                   answer_forms=[{"weights": {self.allowed[0]: 0.5}, "why": "..."}, {"no_change": True, "why": "..."}],
                   rules=["Each weight is from 0 to 1. The weights add up to at most 1. The rest is cash. Long only.",
                          f"The desk moves the book to your weights at the open of the next recorded minute, with a spread and (crypto) a fee. Stock answers given while the market is closed fill at the next regular open.",
                          f"A change of less than tm_weights_min_change ({self.cfg['tm_weights_min_change']:g}) in one symbol's weight is not traded. A move to zero is always traded.",
                          "no_change, or the same weights as now, trades nothing. Prices drift between wakes and the desk does not move the book back on its own.",
                          "Nothing happens between wakes: no stops, no targets.",
                          f"You may add \"driver\" (one of: {', '.join(DRIVERS)}) and \"reasons\" (symbol to one plain line) to an answer."])
        if self.lev:
            out["rules"][0] = f"Each weight is from 0 to {self.mg:g}. The weights add up to at most {self.mg:g}; above 1 is borrowed and pays financing each hour. Long only."
            out["rules"].append(f"If the account value falls below {self.lev['maint']:g} of the value of what it holds on any recorded minute, the desk sells everything at that minute's low, less a penalty, and holds cash until the next wake.")
        if self.meta.get("basket_size"):
            out["rules"].append(f"This session holds exactly {self.meta['basket_size']} names in equal shares: each named symbol gets the weight 1/{self.meta['basket_size']}.")
        if self.prog["k"] == 0 and self.meta.get("opening"):
            out["rules"].append("Your opening target is the weights in book.target_now. The desk buys them at the first minute unless you answer with other weights.")
        if fresh:
            return out
        p.parent.mkdir(exist_ok=True); S.save_json(p, out)
        return json.loads(p.read_text())

    # ---- the answer, then the clock moves to the next wake
    def submit(self, body):
        if self.done():
            raise S.Done()
        errs = check_answer(body, self.allowed, self.cfg, self.meta.get("basket_size"), max_gross=self.mg)
        if errs:
            return self.bad(errs)
        k = self.prog["k"]; wake = self.wakes[k]; nxt = self.next_time(k)
        answer = None if "no_change" in body else body["weights"]
        row = fill_row(self.tape, self.meta["market"], priced(self.meta), wake, nxt)
        book = json.loads(json.dumps(self.prog["book"])); lev_before = None
        if self.lev and k > 0:
            lev_before = self.lev_between(book, k - 1, wake)
        r = step_book(book, answer, row, self.cfg, k == 0, self.mg)
        step = dict(k=k, utc=iso(wake), asked=answer, why=body["why"], driver=body.get("driver"), reasons=body.get("reasons"), target=r["target"], changed=r["changed"], retry=r["retry"], trades=r["trades"], skipped=r["skipped"],
                    value_before=r["value_before"], value_after_fill=r["value_after"], weights_after=r["weights_after"], fill_utc=r["fill_utc"],
                    cash_after=book["cash"], row=row, looks=self.prog["looks"].get(str(k), 0), bad_attempts=self.prog["bad"].get(str(k), 0))
        if self.lev:
            step["lev_before"] = lev_before
        f = self.dir / "picks" / self.tid / f"{wake.strftime('%Y%m%dT%H%MZ')}.json"; f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        self.prog["book"] = book; self.prog["steps"].append(step); self.prog["k"] = k + 1
        self.now = nxt
        if self.prog["k"] >= self.N:
            self.finish()
        else:
            self.save()
        self.mirror()
        return dict(ok=True, step=k + 1, of=self.N, changed=r["changed"], trades=r["trades"], skipped=r["skipped"], done=self.done(),
                    next_utc=None if self.done() else iso(self.now))

    def mirror(self):
        """Copies of the state for reading. progress.json stays the one true record, so these can always be made again."""
        b = self.prog["book"]
        S.save_json(self.dir / "account.json", dict(cash_usd=b["cash"], holdings=b["qty"], target=b["target"], spread_usd=b["spread_usd"], fee_usd=b["fee_usd"],
                                                    traded_usd=b["traded_usd"]))
        (self.dir / "records").mkdir(exist_ok=True); tmp = self.dir / "records" / "wakes.jsonl.tmp"
        tmp.write_text("".join(json.dumps(dict((x, st[x]) for x in ("k", "utc", "asked", "why", "driver", "reasons", "target", "changed", "retry", "weights_after", "value_before",
                                                                     "value_after_fill", "fill_utc", "trades", "skipped")), sort_keys=True) + "\n"
                               for st in self.prog["steps"]))
        os.replace(tmp, self.dir / "records" / "wakes.jsonl")

    def lev_between(self, book, j, until):
        """Leverage only: financing and the maintenance rule from the fill of step j to `until`."""
        st = self.prog["steps"][j]; t0 = max(parse(st["fill_utc"]) if st.get("fill_utc") else self.wakes[j], self.wakes[j])
        return lev_scan(book, lev_minutes(self.tape, priced(self.meta), t0, until), t0, until, self.lev, self.cfg)

    def finish(self):
        b = self.prog["book"]
        if self.lev and self.prog["steps"] and not self.prog.get("lev_last"):
            self.prog["lev_last"] = self.lev_between(b, len(self.prog["steps"]) - 1, self.end)
        em = end_marks(self.tape, priced(self.meta), self.end)
        for s, p in em.items():
            b["last_px"][s] = p
        v = value_at(b, em); start = self.cfg["tm_account_start_usd"]
        if self.lev:
            v = max(0.0, v)
        meta = {k: v2 for k, v2 in self.meta.items() if k != "config"}
        res = dict(session=meta, config=self.cfg, steps=self.prog["steps"], end_marks=em, end_utc=self.meta["end_utc"],
                   final=dict(value_usd=v, gain_pct=(v / start - 1) * 100, cash_usd=b["cash"], holdings=b["qty"], spread_usd=b["spread_usd"], fee_usd=b["fee_usd"],
                              costs_paid_usd=b["spread_usd"] + b["fee_usd"], traded_usd=b["traded_usd"],
                              **({} if not self.lev else dict(max_gross=self.mg, financing_usd=b["financing_usd"], penalty_usd=b["penalty_usd"],
                                                               shortfall_usd=b["shortfall_usd"], closeouts=b["closeouts"], largest_drop_on_minutes=b["lev_largest_drop"]))),
                   costs=dict(tm_crypto_half_spread_bps=self.cfg["tm_crypto_half_spread_bps"], tm_stock_half_spread_bps=self.cfg["tm_stock_half_spread_bps"],
                              practice_crypto_fee_bps_added=self.cfg["practice_crypto_fee_bps_added"], tm_weights_min_change=self.cfg["tm_weights_min_change"]),
                   limits=LIMITS)
        self.prog["done"] = True; self.now = self.end; S.save_json(self.dir / "result.json", res); self.save()


def run_scripted(session_id, answers, tape=None):
    """Feeds a list of answers (bodies) straight to a session, the way the server would. For tests and code traders."""
    s = WSession(session_id, tape=tape)
    for body in answers:
        if s.done():
            break
        s.packet(); r = s.submit(body)
        if not r.get("ok"):
            raise RuntimeError(f"answer refused: {r}")
    return s


WAKE_WORDS = ("pick-hours", "weekly")


def wake_choice(word, market):
    """The --wakes word of the command line, as (kind, rules). "daily" is refused: for crypto it once meant the two pick-session
    hours, which is easy to take for one wake a day. Give a JSON list for one wake a day, or "pick-hours" for the pick-session hours."""
    if word is None:
        if market == "stocks":
            return "weekly", None
        raise SystemExit('--wakes is needed for a crypto weights session: "pick-hours" (the hours in tm_crypto_wake_hours_utc), "weekly", '
                         'or a JSON list such as \'[{"every": "day", "utc_hours": [0]}]\' for one wake a day at 00:00 UTC.')
    if word == "daily":
        raise SystemExit('--wakes daily is refused because it is unclear how many wakes a day it means. Use "pick-hours" for the pick-session '
                         'hours (tm_crypto_wake_hours_utc for crypto, tm_stock_wake_times_ny for stocks), or a JSON list such as '
                         '\'[{"every": "day", "utc_hours": [0]}]\' for one wake a day at 00:00 UTC.')
    if word == "pick-hours":
        return "daily", None
    if word == "weekly":
        return "weekly", None
    try:
        rules = json.loads(word)
    except ValueError:
        raise SystemExit(f'--wakes {word!r} is not one of {", ".join(WAKE_WORDS)} and not a JSON list of wake rules.')
    if not isinstance(rules, list) or not rules:
        raise SystemExit("--wakes as JSON must be a list of wake rules.")
    return "rules", rules


def main(argv=None):
    a = argparse.ArgumentParser(description="Makes a weights session and counts it in timemachine/SESSIONS.jsonl. Pretend money only.")
    sub = a.add_subparsers(dest="cmd", required=True); n = sub.add_parser("new")
    n.add_argument("--trader", required=True); n.add_argument("--model", required=True); n.add_argument("--method", required=True)
    n.add_argument("--market", choices=["crypto", "stocks"], required=True); n.add_argument("--symbols", required=True, help="allowed symbols, comma separated")
    n.add_argument("--from", dest="start", required=True); n.add_argument("--to", dest="end", required=True)
    n.add_argument("--open", default="cash", help='"cash" or a JSON object of opening weights, for example \'{"BTC/USD": 1}\'')
    n.add_argument("--wakes", default=None, help='"pick-hours", "weekly", or a JSON list of wake rules (see make_wakes); "daily" is refused')
    n.add_argument("--news", action="store_true"); n.add_argument("--session"); n.add_argument("--note"); n.add_argument("--benchmark")
    n.add_argument("--basket-size", type=int, help="answers must name exactly this many symbols in equal shares")
    n.add_argument("--tape", choices=["main", "fast"], default="main", help="fast: the second price store tape_fast.sqlite, read-only (crypto only)")
    x = a.parse_args(argv)
    assert x.tape == "main" or x.market == "crypto", "the fast tape holds crypto only"
    opening = None if x.open == "cash" else json.loads(x.open)
    kind, rules = wake_choice(x.wakes, x.market)
    sid = x.session or f"W-{x.trader}-{x.start}-{dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
    folder = create(sid, x.trader, x.model, x.method, x.start, x.end, [s.strip() for s in x.symbols.split(",") if s.strip()], market=x.market,
                    opening=opening, rules=rules, wake_kind=kind, news=x.news, note=x.note, benchmark=x.benchmark, basket_size=x.basket_size,
                    tape=fast_tape() if x.tape == "fast" else None)
    meta = json.loads((folder / "session.json").read_text()); base = f"http://127.0.0.1:{os.environ.get('TM_PORT', '8765')}"
    print(json.dumps(dict(session=sid, folder=str(folder), wakes=len(meta["wakes"]), first_wake=meta["wakes"][0], end_utc=meta["end_utc"], wake_rules=meta["wake_rules"]), indent=1))
    print(f"curl -s '{base}/next?session={sid}'")
    print(f"curl -s -X POST '{base}/pick?session={sid}' -H 'Content-Type: application/json' -d '{{\"weights\": {{...}}, \"why\": \"...\"}}'")
    print(f"curl -s '{base}/status?session={sid}'")


if __name__ == "__main__":
    main()
