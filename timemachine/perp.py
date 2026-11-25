"""Perp sessions: a weights session on perpetual futures. Longs and shorts, funding, stops and targets. Pretend money only.

A perp session is a weights session (kind "weights") with instrument "perp". weights.open_session() opens it as a PSession;
every other session never reaches this file, so their results are as before to the cent.

What is different from a spot weights session:
  weights      signed. 0.5 is long half the account value, -1.0 is short one account's worth. The sum of absolute weights is at
               most the session's max_gross. A linear USD perp is assumed: position value is quantity times price.
  the book     cash plus signed quantities; the account value is cash plus the sum of quantity times price. There is no
               borrowing interest. Funding is charged on the whole position value at each funding time of the symbol
               (tm_perp_funding_hours: whole multiples of 1 or 8 hours in UTC). A long pays a positive rate and receives a
               negative one; a short the reverse. The rate comes from tm_perp_funding_files where the symbol has a stored
               hourly file (an 8 hour charge sums its 8 hourly rates); otherwise tm_perp_fallback_rate_per_day, paid by longs
               and shorts alike. The scan counts the hours charged at the fallback.
  costs        tm_perp_fee_bps_per_side (the session's run) and tm_perp_half_spread_bps (a symbol named there, else its coin's
               measured tm_crypto_half_spread_bps_by_coin, else the default). Not the spot keys. The scorer re-runs the same
               answers at each fee per side in tm_perp_fee_levels_bps.
  min change   tm_perp_min_change. A move to zero and a change of side are always traded; a weight under it from flat is not.
  stops        an answer may carry "exits": {"SOL/USD": {"stop": price, "target": price}}. For a long the stop is below the
               price at the wake and the target above; for a short the reverse. On every recorded minute between wakes, a
               long's stop fills when the minute's low reaches it and a short's when the high does (targets the other way),
               at the level less the half spread and fee. If the minute opens already beyond the level (a gap), the fill is
               at that minute's open. If one minute crosses both, the stop is taken. After a stop or target the symbol's
               target is zero: no_change does not open it again. A weights answer replaces all exits; no_change keeps them.
  close-out    on every recorded minute, each symbol at its worst price of that minute (the low for a long, the high for a
               short; the other symbols at their last close), the account value is checked against the sum of
               tm_perp_maintenance times position value. Below it, the whole book is closed at those prices less the half
               spread, the fee and tm_perp_closeout_penalty, and stays flat until the next wake, where the standing target
               is traded again (as in the spot leverage path). With several symbols the worst prices of a minute are not
               reached at the same moment, so this is stricter than a real venue when symbols move together.
               The account value never goes below zero; any shortfall is recorded.
  packet       small: the latest tm_perp_packet_bars bars per symbol at the wake spacing, the book, the last wake. More bars
               are a lookup (15Min, 1Hour, 4Hour, 1Day and 1Min).
Crypto only.
  fast tape    `new --tape fast` runs on tape_fast.sqlite, read-only. Funding then comes from its funding table (the venue per coin
               in tm_fast_funding_venue; see timemachine/tm06.py), and the packet adds the 24 hour change in open interest.
  long only    `new --long-only` refuses a negative weight; the book itself still allows one.

The book is pure functions (p_step, p_scan, run_perp) used by the session, the twins and the scorer alike.

python3 timemachine/perp.py new --trader F01 --model M --method CARD.md --symbols SOL/USD,DOGE/USD --from 2026-10-01 --to 2026-10-31 \\
    --wakes '[{"every": "minutes", "step": 60}]' --max-gross 2 [--news] [--session ID]
python3 timemachine/perp.py score SESSION [--draws N] [--fee-bps F] [--json]   (prints every fee level in tm_perp_fee_levels_bps)
"""
import argparse, bisect, datetime as dt, hashlib, heapq, json, math, os, random, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from timemachine import session as S, weights as W
from timemachine.tape import Tape

UTC = S.UTC
iso, parse = S.iso, S.parse
P_KEYS = ["tm_perp_fee_bps_per_side", "tm_perp_half_spread_bps", "tm_perp_maintenance", "tm_perp_closeout_penalty", "tm_perp_funding_files",
          "tm_perp_funding_hours", "tm_perp_fallback_rate_per_day", "tm_perp_min_change", "tm_perp_packet_bars", "tm_perp_fee_levels_bps", "tm_crypto_half_spread_bps_by_coin",
          "tm_crypto_half_spread_bps_default"]
LIMITS = W.LIMITS[:5] + [
    "Fills are assumed: the open of the first recorded minute at or after the wake, a fixed half spread and fee per symbol. There is no cap on the share of a minute's volume. They are not real fills.",
    "Perpetual futures are modelled as linear USD contracts priced at the spot minute bars on the tape, not at a venue's own mark or index price.",
    "Funding is the stored hourly Kraken rate where tm_perp_funding_files has the symbol, else a fixed fallback paid by both sides.",
    "Stops, targets and the maintenance rule are checked on minute highs and lows. With several symbols the worst prices of one minute are taken together, which they need not be.",
    "Inside one minute the order of prices is not known: a minute that crosses both a stop and a target is counted as the stop.",
    "Between wakes only the minutes of symbols held are read. Funding falling on a minute where only a symbol not held traded is charged at the next minute of a held one."]


def p_config(path=ROOT / "config" / "thresholds.yaml"):
    c = W.lev_config(path, proposed=ROOT / "timemachine" / "no_such_file", keys=P_KEYS); c.pop("_from"); return c


def full_config():
    cfg = W.full_config(); cfg.update(p_config()); return cfg


def per(m, s):
    return m.get(s, m["default"])


def half_spread_bps(cfg, s):
    """A symbol named in tm_perp_half_spread_bps, else its coin in tm_crypto_half_spread_bps_by_coin (measured), else
    tm_crypto_half_spread_bps_default (a placeholder; absent from sessions made before it existed), else the default."""
    m, coin = cfg["tm_perp_half_spread_bps"], (cfg.get("tm_crypto_half_spread_bps_by_coin") or {})
    d = cfg.get("tm_crypto_half_spread_bps_default")
    return m[s] if s in m else coin[s.split("/")[0]] if s.split("/")[0] in coin else d if d is not None else m["default"]


def session_params(meta, cfg, tape):
    """The book settings for a session: from the stored funding files, or on the fast tape from its funding table."""
    if meta.get("tape_name") == "fast":
        from timemachine import tm06
        return tm06.fast_params(W.priced(meta), cfg, tape, parse(meta["wakes"][0]), parse(meta["end_utc"]))
    return p_params(W.priced(meta), cfg)


def with_fee(pp, fee_bps):
    """The same settings with one fee per side for every symbol (the scorer's fee levels)."""
    return dict(pp, fee={s: float(fee_bps) / 1e4 for s in pp["fee"]})


def p_params(symbols, cfg, funding=None, fee_bps=None):
    """Everything the book needs, per symbol. funding: {symbol: {hour epoch: rate}}; by default read from tm_perp_funding_files.
    fee_bps, if given, is the fee per side for every symbol (the scorer's fee levels); otherwise tm_perp_fee_bps_per_side."""
    files = cfg["tm_perp_funding_files"] or {}
    if funding is None:
        funding = {s: W.load_funding(files[s]) for s in symbols if s in files}
    return dict(fee={s: (per(cfg["tm_perp_fee_bps_per_side"], s) if fee_bps is None else float(fee_bps)) / 1e4 for s in symbols},
                hs={s: half_spread_bps(cfg, s) / 1e4 for s in symbols},
                maint={s: float(per(cfg["tm_perp_maintenance"], s)) for s in symbols}, hours={s: int(per(cfg["tm_perp_funding_hours"], s)) for s in symbols},
                fallback_per_day=float(cfg["tm_perp_fallback_rate_per_day"]), penalty=float(cfg["tm_perp_closeout_penalty"]), min_change=float(cfg["tm_perp_min_change"]),
                funding=funding, symbols=list(symbols),
                source={s: ("funding file " + str(files[s]) if s in funding and s in files else "funding given" if s in funding else "tm_perp_fallback_rate_per_day") for s in symbols})


# ---- the book
def new_book(start_usd, opening=None):
    return dict(cash=float(start_usd), qty={}, target=dict(opening or {}), exits={}, spread_usd=0.0, fee_usd=0.0, traded_usd=0.0, funding_usd=0.0, fallback_hours=0,
                penalty_usd=0.0, shortfall_usd=0.0, closeouts=[], exits_hit=[], peak=float(start_usd), largest_drop=0.0, last_px={}, pending=False)


def norm(w):
    return {s: float(v) for s, v in sorted((w or {}).items()) if float(v) != 0}


def value_at(book, px):
    return book["cash"] + sum(q * px.get(s, book["last_px"].get(s, 0.0)) for s, q in book["qty"].items())


def gross_at(book, px):
    return sum(abs(q) * px.get(s, book["last_px"].get(s, 0.0)) for s, q in book["qty"].items())


def weights_at(book, px):
    v = value_at(book, px)
    return {s: (q * px.get(s, book["last_px"].get(s, 0.0)) / v if v > 0 else 0.0) for s, q in sorted(book["qty"].items()) if q != 0}


def trade(book, s, dq, p, pp, penalty=0.0):
    """Buys (dq > 0) or sells (dq < 0) dq of s at price p, with the half spread, the fee and an optional penalty share."""
    hs, fee = pp["hs"][s], pp["fee"][s]; px = p * (1 + hs) if dq > 0 else p * (1 - hs)
    f = abs(dq) * px * fee; pen = abs(dq) * px * penalty
    book["cash"] -= dq * px + f + pen; q = book["qty"].get(s, 0.0) + dq
    if abs(q * p) < 1e-9:
        book["qty"].pop(s, None)
    else:
        book["qty"][s] = q
    book["spread_usd"] += abs(dq) * p * hs; book["fee_usd"] += f; book["penalty_usd"] += pen; book["traded_usd"] += abs(dq) * p
    return dict(symbol=s, side="buy" if dq > 0 else "sell", qty=abs(dq), open=p, price=px, fee_usd=f, penalty_usd=pen)


def p_step(book, answer, exits, row, pp, first):
    """Moves `book` (changed in place) for one wake. answer: signed weights, or None for no change. exits: the answer's stops and
    targets (a weights answer replaces all exits; None keeps the standing ones). Returns a record of what was done."""
    marks, fills = row["marks"], row["fills"]
    for s, p in marks.items():
        book["last_px"][s] = p
    value_before = value_at(book, marks)
    target = norm(book["target"]) if answer is None else norm(answer)
    if answer is not None:
        book["exits"] = {s: dict(e) for s, e in sorted((exits or {}).items()) if s in target}
    retry = bool(book.get("pending")); changed = first or retry or target != norm(book["target"]); book["target"] = target
    rec = dict(target=target, exits=dict(book["exits"]), changed=changed, retry=retry, value_before=value_before, trades=[], skipped=[])
    if not changed:
        rec.update(value_after=value_before, weights_after=weights_at(book, marks), fill_utc=None); return rec
    fp = {s: f[1] for s, f in fills.items() if f}
    px = {s: fp.get(s, marks.get(s, book["last_px"].get(s, 0.0))) for s in set(book["qty"]) | set(target)}
    V = value_at(book, px)
    for s in sorted(px):
        w, q = target.get(s, 0.0), book["qty"].get(s, 0.0); c = q * px[s] / V if V > 0 else 0.0
        if w == c or (q == 0 and w == 0):
            continue
        if V <= 0:
            rec["skipped"].append(dict(symbol=s, why="the account value is zero", want=w, held=c)); continue
        if s not in fp:
            rec["skipped"].append(dict(symbol=s, why="no recorded minute to fill in before the next wake", want=w, held=c)); continue
        if abs(w - c) < pp["min_change"] and not (w == 0 or q * w < 0):
            rec["skipped"].append(dict(symbol=s, why="change smaller than tm_perp_min_change", want=w, held=c)); continue
        t = trade(book, s, w * V / fp[s] - q, fp[s], pp); t["fill_utc"] = fills[s][0]; rec["trades"].append(t)
    for s, p in fp.items():
        book["last_px"][s] = p  # the fill minute's open is now the latest price; the scan's maintenance check starts from it
    book["pending"] = any(x["why"].startswith("no recorded minute") for x in rec["skipped"])
    rec.update(value_after=value_at(book, px), weights_after=weights_at(book, px), fill_utc=min([t["fill_utc"] for t in rec["trades"]], default=None))
    return rec


def exit_hit(q, ex, o, h, l):
    """(level filled at, "stop" or "target", gapped) for one minute, or None. A gap fills at the open; a stop is taken before a target."""
    st, tg = ex.get("stop"), ex.get("target")
    if q > 0:
        if st is not None and o <= st:
            return o, "stop", True
        if tg is not None and o >= tg:
            return o, "target", True
        if st is not None and l <= st:
            return st, "stop", False
        if tg is not None and h >= tg:
            return tg, "target", False
    else:
        if st is not None and o >= st:
            return o, "stop", True
        if tg is not None and o <= tg:
            return o, "target", True
        if st is not None and h >= st:
            return st, "stop", False
        if tg is not None and l <= tg:
            return tg, "target", False
    return None


def funding_times(pp, a, b):
    """(time, symbol) for every funding charge with a < time <= b, sorted."""
    out = []
    for s in pp["symbols"]:
        step = 3600 * pp["hours"][s]
        out += [(e, s) for e in range((a // step + 1) * step, b + 1, step)]
    return sorted(out)


def fund(book, e, s, px, pp, rec):
    q = book["qty"].get(s)
    if not q:
        return
    H = pp["hours"][s]; f = pp["funding"].get(s) or {}; rs = [f.get(e - 3600 * j) for j in range(H)]; v = q * px.get(s, 0.0)
    if all(r is not None for r in rs):
        cost = v * sum(rs)
    else:
        cost = abs(v) * pp["fallback_per_day"] * H / 24.0; book["fallback_hours"] += H; rec["fallback_hours"] += H
    book["cash"] -= cost; book["funding_usd"] += cost; rec["funding_usd"] += cost


def p_scan(book, minutes, t0, t1, pp):
    """From t0 to t1: funding at each charge time, and on every recorded minute the stops and targets, then the maintenance rule.
    minutes: sorted (start epoch, symbol, open, high, low, close)."""
    a, b = int(t0.timestamp()), int(t1.timestamp()); ev = funding_times(pp, a, b); ei = 0
    px = dict(book["last_px"]); rec = dict(funding_usd=0.0, fallback_hours=0, closeout=None, exits=[])
    held0, flat_t = bool(book["qty"]), None
    for t, s, o, h, l, c in scan_rows(minutes, a, b, book["qty"]):
        while ei < len(ev) and ev[ei][0] <= t:
            fund(book, ev[ei][0], ev[ei][1], px, pp, rec); ei += 1
        q = book["qty"].get(s, 0.0); ex = book["exits"].get(s)
        if q and ex:
            hit = exit_hit(q, ex, o, h, l)
            if hit:
                lv, kind, gap = hit; tr = trade(book, s, -q, lv, pp); book["target"].pop(s, None); book["exits"].pop(s, None)
                x = dict(utc=iso(dt.datetime.fromtimestamp(t, UTC)), symbol=s, kind=kind, level=ex.get(kind), filled_at=lv, gap=gap, price=tr["price"], side=tr["side"], qty=tr["qty"])
                rec["exits"].append(x); book["exits_hit"].append(x)
                if not book["qty"] and flat_t is None:
                    flat_t = t
        if book["qty"]:
            adv = dict(px); q = book["qty"].get(s, 0.0)
            if q:
                adv[s] = l if q > 0 else h
            eq = book["cash"] + sum(x * adv.get(y, 0.0) for y, x in book["qty"].items())
            need = sum(pp["maint"][y] * abs(x) * adv.get(y, 0.0) for y, x in book["qty"].items())
            book["largest_drop"] = min(book["largest_drop"], max(eq, 0.0) / book["peak"] - 1 if book["peak"] > 0 else 0.0)
            if eq < need:
                for y, x in sorted(book["qty"].items()):
                    trade(book, y, -x, adv[y], pp, penalty=pp["penalty"])
                book["qty"] = {}; short = max(0.0, -book["cash"])
                if short:
                    book["shortfall_usd"] += short; book["cash"] = 0.0
                rec["closeout"] = dict(utc=iso(dt.datetime.fromtimestamp(t, UTC)), symbol=s, value_before=eq, value_after=book["cash"], shortfall_usd=short)
                book["closeouts"].append(rec["closeout"]); book["pending"] = True; flat_t = t if flat_t is None else flat_t
                book["largest_drop"] = min(book["largest_drop"], book["cash"] / book["peak"] - 1 if book["peak"] > 0 else 0.0)
        px[s] = c
        if book["qty"]:
            book["peak"] = max(book["peak"], value_at(dict(book, last_px=px), px))
    while ei < len(ev):
        fund(book, ev[ei][0], ev[ei][1], px, pp, rec); ei += 1
    for s, p in px.items():
        book["last_px"][s] = p
    rec["held_seconds"] = ((flat_t if flat_t is not None else b) - a) if held0 else 0  # time in market: held from t0 until flat or t1
    book["held_seconds"] = book.get("held_seconds", 0) + rec["held_seconds"]
    return rec


class Minutes(list):
    """perp_minutes' result: the sorted rows, and each symbol's own rows, so that a scan reads only the symbols held."""

    def __init__(self, rows):
        super().__init__(rows); self.by = {}
        for r in self:
            self.by.setdefault(r[1], []).append(r)
        self.keys = {s: [r[0] for r in rs] for s, rs in self.by.items()}


def scan_rows(minutes, a, b, held):
    """The minutes from a to b in time order. From a Minutes, only the symbols held at the start (a scan never opens a
    position, so no other symbol can matter, except as noted in perp.LIMITS); from a plain list, every row as before."""
    if isinstance(minutes, Minutes):
        parts = [minutes.by[s][bisect.bisect_left(minutes.keys[s], a):bisect.bisect_left(minutes.keys[s], b)] for s in sorted(held) if s in minutes.by]
        return heapq.merge(*parts)
    keys = [m[0] for m in minutes]
    return minutes[bisect.bisect_left(keys, a):bisect.bisect_left(keys, b)]


def perp_minutes(tape, symbols, t0, t1):
    """Every recorded 1Min bar of the symbols that has finished by t1, from t0, sorted: (start epoch, symbol, open, high, low, close).
    The same rows as tape.bars(s, "1Min", t0, t1), read in one query per symbol."""
    a, b = int(t0.timestamp()), int(t1.timestamp()); out = []
    for s in symbols:
        out += [(r[0], s, r[1], r[2], r[3], r[4]) for r in
                tape._conn().execute("SELECT t, o, h, l, c FROM bars WHERE symbol = ? AND tf = '1Min' AND t >= ? AND t <= ? ORDER BY t", (s, a, b - 60))]
    return Minutes(sorted(out))


def scan_from(row, wake):
    """Where the scan after a wake starts: the earliest fill minute of the row (the wake itself when nothing fills)."""
    ts = [parse(f[0]) for f in row["fills"].values() if f]
    return max(wake, min(ts)) if ts else wake


def run_perp(meta, table, answers, pp, minutes, cfg):
    """The whole session from answers [(signed weights or None, exits or None) per wake], the stored price table and the minutes.
    Returns (book, records, final value). Used by the scorer, the twins and the tests."""
    book = new_book(cfg["tm_account_start_usd"], meta.get("opening")); wakes = [parse(w) for w in meta["wakes"]]; end = parse(meta["end_utc"])
    tf = [scan_from(table["rows"][k], wakes[k]) for k in range(len(answers))]; recs = []
    for k, (w, ex) in enumerate(answers):
        if k > 0:
            recs[-1]["scan"] = p_scan(book, minutes, tf[k - 1], tf[k], pp)
        recs.append(p_step(book, w, ex, table["rows"][k], pp, k == 0))
    if recs:
        recs[-1]["scan"] = p_scan(book, minutes, tf[-1], end, pp)
    for s, p in table["end_marks"].items():
        book["last_px"][s] = p
    return book, recs, max(0.0, value_at(book, table["end_marks"]))


# ---- answers
def check_weights(w, allowed, cfg, max_gross, what="weights"):
    if not isinstance(w, dict):
        return [f"{what} must be a JSON object of symbol to signed weight, for example {{\"{allowed[0]}\": -0.5}}."]
    errs = []
    for s, v in w.items():
        if s not in allowed:
            errs.append(f"{s} is not one of the allowed symbols: {', '.join(allowed)}.")
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
            errs.append(f"The weight for {s} is not a number.")
        elif abs(v) > max_gross:
            errs.append(f"The weight for {s} is {v}. Each weight must be from -{max_gross:g} to {max_gross:g}.")
    if not errs and sum(abs(v) for v in w.values()) > max_gross + cfg["tm_weights_sum_tolerance"]:
        errs.append(f"The absolute weights add up to {sum(abs(v) for v in w.values())}. They must add up to at most {max_gross:g}.")
    return errs


def check_exits(ex, w, marks):
    if not isinstance(ex, dict):
        return ["exits must be a JSON object of symbol to {\"stop\": price, \"target\": price}."]
    errs = []
    for s, e in ex.items():
        v = (w or {}).get(s, 0)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or v == 0:
            errs.append(f"exits for {s}: it has no position in this answer's weights."); continue
        if not isinstance(e, dict) or not e or set(e) - {"stop", "target"}:
            errs.append(f"exits for {s} must be {{\"stop\": price}}, {{\"target\": price}} or both."); continue
        m = marks.get(s)
        for k, x in e.items():
            if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x <= 0:
                errs.append(f"The {k} for {s} must be a price above zero.")
            elif m is None:
                errs.append(f"{s} has no price at this wake, so a {k} cannot be checked.")
            elif (k == "stop") == (v > 0) and x >= m:
                errs.append(f"The {k} for {s} must be below the price now ({'long stop' if v > 0 else 'short target'}).")
            elif (k == "stop") != (v > 0) and x <= m:
                errs.append(f"The {k} for {s} must be above the price now ({'long target' if v > 0 else 'short stop'}).")
    return errs


def check_answer(body, allowed, cfg, max_gross, marks, long_only=False):
    mx = int(cfg["tm_weights_why_max_chars"])
    if not isinstance(body, dict):
        return ["The body must be a JSON object."]
    why = body.get("why")
    if not isinstance(why, str) or not why.strip() or len(why) > mx:
        return ["Every answer needs \"why\": one short plain paragraph (at most tm_weights_why_max_chars characters)."]
    errs = []
    if "driver" in body and body["driver"] not in W.DRIVERS:
        errs.append(f"driver, if given, is one of: {', '.join(W.DRIVERS)}.")
    if "reasons" in body and not (isinstance(body["reasons"], dict) and all(k in allowed and isinstance(v, str) and len(v) <= mx for k, v in body["reasons"].items())):
        errs.append("reasons, if given, is an object of allowed symbol to one plain line.")
    if "no_change" in body:
        if body.get("no_change") is not True or set(body) - W.OPTIONAL != {"no_change", "why"}:
            return errs + ['A no-change answer is {"no_change": true, "why": "..."} (driver and reasons may be added). It keeps the standing stops and targets.']
        return errs
    if set(body) - W.OPTIONAL - {"exits"} != {"weights", "why"}:
        return errs + ['An answer is {"weights": {...}, "exits": {...}, "why": "..."} (exits optional) or {"no_change": true, "why": "..."}.']
    errs += check_weights(body["weights"], allowed, cfg, max_gross)
    if not errs and long_only and any(v < 0 for v in body["weights"].values()):
        errs.append("This session is long or flat only: every weight is from 0 up. A negative weight (a short) is refused.")
    if not errs and "exits" in body:
        errs += check_exits(body["exits"], body["weights"], marks)
    return errs


# ---- making a session
def bar_seconds(wakes):
    """The packet's bar size: the wake spacing (15 minutes, 1 hour, 4 hours), or a day for daily or slower wakes."""
    gaps = [int((b - a).total_seconds()) for a, b in zip(wakes, wakes[1:])]
    g = min(gaps) if gaps else 86400
    return 86400 if g >= 86400 else max(60, g)


def create(session_id, trader_id, model, method_path, start_date, end_date, symbols, max_gross=1.0, opening=None, rules=None, wake_kind="daily",
           news=False, tape=None, note=None, benchmark=None, long_only=False, extra=None):
    """long_only: the session refuses a negative weight. extra: more fields for session.json (a plan's own, such as tm06).
    A tape opened read-only (the fast tape) is recorded so that the session opens it read-only again."""
    assert re.fullmatch(r"[A-Z0-9-]{2,12}", trader_id), "trader id: 2 to 12 capital letters, digits or dashes"
    assert re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", session_id) and ".." not in session_id, "session id: 3 to 80 letters, digits, dot, dash or underscore"
    symbols = list(dict.fromkeys(symbols)); assert symbols and all("/" in s for s in symbols), "a perp session takes crypto pairs like SOL/USD"
    mg = float(max_gross); assert mg > 0, "max_gross is above zero"
    tape = tape or Tape(); cfg = full_config(); folder = S.runs_dir() / session_id
    if getattr(tape, "readonly", False):  # the fast tape: its funding venue and open interest keys go in the session's config too
        from timemachine import tm06
        cfg.update(tm06.t_config())
    if folder.exists():
        raise FileExistsError(f"session {session_id} already exists")
    opening = dict(opening or {}); errs = check_weights(opening, symbols, cfg, mg, "the opening weights"); assert not errs, " ".join(errs)
    rules = rules or W.default_rules("crypto", wake_kind, cfg)
    wl, end = W.make_wakes(tape, "crypto", start_date, end_date, rules); assert wl, "no wake falls inside the window"
    benchmark = benchmark or "BTC/USD"
    mp = Path(method_path.split("#")[0]); mp = mp if mp.is_absolute() else ROOT / mp
    chash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    meta = dict(session=session_id, kind="weights", instrument="perp", trader=trader_id, model=model, method=method_path, method_sha256=S.sha256_file(mp), market="crypto",
                window=dict(start=start_date, end=end_date), symbols=symbols, watch=symbols, opening=opening, wake_rules=rules, wakes=[iso(w) for w in wl], end_utc=iso(end),
                benchmark=benchmark, config=cfg, config_hash=chash, created_utc=iso(dt.datetime.now(UTC)), git=S.git_commit(), tape=str(tape.path), note=note,
                news=bool(news), basket_size=None, perp=dict(max_gross=mg, bar_seconds=bar_seconds(wl)))
    if getattr(tape, "readonly", False):
        meta.update(tape_readonly=True, tape_name="fast")
    if long_only:
        meta["long_only"] = True
    meta.update(extra or {})
    folder.mkdir(parents=True)
    (folder / "session.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n")
    line = dict(session=session_id, kind="weights", instrument="perp", max_gross=mg, trader=trader_id, model=model, method=method_path, method_sha256=meta["method_sha256"],
                market="crypto", window=meta["window"], symbols=symbols, opening=opening, wake_rules=rules, news=bool(news), benchmark=benchmark,
                wakes=dict(count=len(wl), first=meta["wakes"][0], last=meta["wakes"][-1]), config_hash=chash, created_utc=meta["created_utc"],
                git_commit=meta["git"]["commit"], git_dirty=meta["git"]["dirty"], runs_folder=str(folder))
    log = S.sessions_log(); log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n"); f.flush(); os.fsync(f.fileno())
    S.save_json(folder / "progress.json", dict(k=0, done=False, bad={}, looks={}, steps=[], book=new_book(cfg["tm_account_start_usd"], opening), clock=meta["wakes"][0]))
    return folder


class PSession(W.WSession):
    """A perp session. Lookups and refusals are the pick session's own; 15Min and 4Hour bars are added for lookups."""

    def __init__(self, session_id, tape=None):
        meta = json.loads((S.runs_dir() / session_id / "session.json").read_text()); assert meta.get("instrument") == "perp"
        tape = tape or W.session_tape(meta)
        self.pp = session_params(meta, meta["config"], tape); self.pmg = float(meta["perp"]["max_gross"]); self.long_only = bool(meta.get("long_only"))
        super().__init__(session_id, tape=tape)

    def last_rate(self, s):
        f = self.pp["funding"].get(s)
        if not f:
            return None
        h = int(self.now.timestamp()) // 3600 * 3600 - 3600  # the last hour that has ended
        return f.get(h)

    def symbol_rows(self):
        secs = int(self.meta["perp"]["bar_seconds"]); n = int(self.cfg["tm_perp_packet_bars"]); out = {}
        snap = self.tape.snapshot(self.allowed, self.now)
        for s in self.allowed:
            if secs >= 86400:
                bars = self.tape.bars(s, "1Day", self.now - dt.timedelta(days=n + 2), self.now, limit=n)
            else:
                bars = S.built_bars(self.tape, s, secs, self.now - dt.timedelta(seconds=secs * (n + 1)), self.now, n)
            out[s] = dict(price=snap[s]["price"] if s in snap else None, price_utc=iso(snap[s]["t"]) if s in snap else None,
                          bars=[[iso(b["t"]), b["o"], b["h"], b["l"], b["c"], b["v"]] for b in bars],
                          funding_rate_last_hour=self.last_rate(s), funding_every_hours=self.pp["hours"][s])
        if self.meta.get("tape_name") == "fast":  # the fast tape adds open interest, as a packet figure only
            from timemachine import tm06
            for s in self.allowed:
                out[s]["open_interest_change_24h_pct"] = tm06.oi_change_pct(self.tape, s, self.now, self.cfg)
        return out

    def book_view(self, b=None):
        b = b or self.prog["book"]; marks = {s: x["price"] for s, x in self.tape.snapshot(list(b["qty"]), self.now).items()}
        v = value_at(b, marks); start = self.cfg["tm_account_start_usd"]
        pos = {s: dict(qty=q, side="long" if q > 0 else "short", value_usd=q * marks.get(s, b["last_px"].get(s, 0.0)),
                       weight=(q * marks.get(s, b["last_px"].get(s, 0.0)) / v if v > 0 else 0.0), exits=b["exits"].get(s)) for s, q in sorted(b["qty"].items())}
        return dict(cash_usd=b["cash"], value_usd=v, start_usd=start, gain_pct=(v / start - 1) * 100, positions=pos, gross=(gross_at(b, marks) / v if v > 0 else 0.0),
                    target_now=norm(b["target"]), exits_now=b["exits"], costs_paid_usd=b["spread_usd"] + b["fee_usd"] + b["penalty_usd"], funding_paid_usd=b["funding_usd"],
                    closeouts=len(b["closeouts"]), exits_hit=len(b["exits_hit"]))

    def packet(self, fresh=False):
        if self.done():
            raise S.Done()
        k = self.prog["k"]; p = self.dir / "packets" / f"{k}.json"
        if p.exists() and not fresh:
            return json.loads(p.read_text())
        last = self.prog["steps"][-1] if self.prog["steps"] else None; nw, nleft = self.news_rows(); mg = self.pmg
        since = None; view = None
        if last is not None:  # what happened since the last wake (exits, a close-out, funding), worked out on a copy; the real scan runs at submit
            b2 = json.loads(json.dumps(self.prog["book"])); t0 = parse(last["scan_from"])
            sc = p_scan(b2, perp_minutes(self.tape, self.pp["symbols"], t0, self.now), t0, self.now, self.pp); view = b2
            since = dict(exits_hit=sc["exits"], closeout=sc["closeout"], funding_usd=sc["funding_usd"])
        out = dict(session=self.meta["session"], kind="weights", instrument="perp", trader=self.tid, utc=iso(self.now), step=k + 1, of=self.N,
                   next_wake_utc=iso(self.next_time(k)), is_last=k + 1 == self.N, market="crypto", allowed=self.allowed, max_gross=mg,
                   bar_seconds=self.meta["perp"]["bar_seconds"], bar_fields=["t", "o", "h", "l", "c", "v"], symbols=self.symbol_rows(), book=self.book_view(view),
                   news=nw, news_left_out=nleft,
                   last_wake=None if last is None else dict(utc=last["utc"], asked=last["asked"], exits=last["exits"], why=last["why"], trades=last["trades"],
                                                            skipped=last["skipped"], weights_after=last["weights_after"], since=since),
                   looks_left=self.looks_left(), hard_lines=W.HARD_LINES,
                   answer_forms=[{"weights": {self.allowed[0]: -0.5}, "exits": {self.allowed[0]: {"stop": "price", "target": "price"}}, "why": "..."},
                                 {"no_change": True, "why": "..."}],
                   rules=[f"Perpetual futures. Each weight is from -{mg:g} to {mg:g}; negative is short. The absolute weights add up to at most {mg:g}. The rest is margin.",
                          "Funding is paid or received on the whole position value at each funding time: a long pays a positive rate, a short receives it.",
                          "The desk trades to your weights at the open of the next recorded minute, with a spread and a fee per symbol.",
                          f"A change of less than tm_perp_min_change ({self.pp['min_change']:g}) in one weight is not traded. A move to zero or a change of side is always traded.",
                          "exits (optional): a stop and a target price per position. Checked on every minute's high and low until filled; a gap fills at the minute's open. "
                          "After a stop or target that symbol stays flat until you ask for it again. A weights answer replaces all exits; no_change keeps them.",
                          "If the account value falls below the maintenance share of position value on any minute, the desk closes everything at that minute's worst prices, "
                          "less a penalty, and stays flat until the next wake.",
                          "More bars: /look what=bars timeframe=1Min, 15Min, 1Hour, 4Hour or 1Day.",
                          f"You may add \"driver\" (one of: {', '.join(W.DRIVERS)}) and \"reasons\" (symbol to one plain line) to an answer."])
        if fresh:
            return out
        p.parent.mkdir(exist_ok=True); S.save_json(p, out)
        return json.loads(p.read_text())

    def look(self, what, symbol=None, symbols=None, timeframe="1Day", days=None):
        if what != "bars" or timeframe not in ("15Min", "4Hour"):
            return super().look(what, symbol=symbol, symbols=symbols, timeframe=timeframe, days=days)
        if self.done():
            raise S.Done()
        k = str(self.prog["k"])
        if self.looks_left() <= 0:
            return dict(ok=False, error="No lookups left at this wake (the limit is tm_max_looks_per_wake). Make your answer.")
        if not symbol or "/" not in symbol:
            return dict(ok=False, error="bars needs a crypto symbol such as SOL/USD")
        days = min(float(days if days is not None else 5), self.cfg["tm_look_max_days"])
        rows = S.built_bars(self.tape, symbol, 900 if timeframe == "15Min" else 14400, self.now - dt.timedelta(days=days), self.now, int(self.cfg["tm_look_max_bars"]))
        data = [dict(b, t=iso(b["t"])) for b in rows]
        self.prog["looks"][k] = self.prog["looks"].get(k, 0) + 1; self.save()
        with self.dir.joinpath("looks.jsonl").open("a") as f:
            f.write(json.dumps(dict(k=int(k), utc=iso(self.now), what=what, symbol=symbol, symbols=[], timeframe=timeframe, days=days, rows=len(data)), sort_keys=True) + "\n")
        return dict(ok=True, utc=iso(self.now), what=what, data=data, looks_left=self.looks_left())

    def submit(self, body):
        if self.done():
            raise S.Done()
        k = self.prog["k"]; wake = self.wakes[k]; nxt = self.next_time(k)
        row = W.fill_row(self.tape, "crypto", W.priced(self.meta), wake, nxt)
        errs = check_answer(body, self.allowed, self.cfg, self.pmg, row["marks"], long_only=self.long_only)
        if errs:
            return self.bad(errs)
        answer = None if "no_change" in body else body["weights"]; exits = None if answer is None else body.get("exits") or {}
        book = json.loads(json.dumps(self.prog["book"])); tf = scan_from(row, wake); before = None
        if k > 0:
            t0 = parse(self.prog["steps"][-1]["scan_from"]); before = p_scan(book, perp_minutes(self.tape, self.pp["symbols"], t0, tf), t0, tf, self.pp)
        r = p_step(book, answer, exits, row, self.pp, k == 0)
        step = dict(k=k, utc=iso(wake), asked=answer, exits=exits, why=body["why"], driver=body.get("driver"), reasons=body.get("reasons"), target=r["target"],
                    exits_standing=r["exits"], changed=r["changed"], retry=r["retry"], trades=r["trades"], skipped=r["skipped"], value_before=r["value_before"],
                    value_after_fill=r["value_after"], weights_after=r["weights_after"], fill_utc=r["fill_utc"], scan_from=iso(tf), scan_before=before,
                    cash_after=book["cash"], row=row, looks=self.prog["looks"].get(str(k), 0), bad_attempts=self.prog["bad"].get(str(k), 0))
        f = self.dir / "picks" / self.tid / f"{wake.strftime('%Y%m%dT%H%MZ')}.json"; f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
        self.prog["book"] = book; self.prog["steps"].append(step); self.prog["k"] = k + 1; self.now = nxt
        if self.prog["k"] >= self.N:
            self.finish()
        else:
            self.save()
        self.mirror()
        return dict(ok=True, step=k + 1, of=self.N, changed=r["changed"], trades=r["trades"], skipped=r["skipped"], done=self.done(), next_utc=None if self.done() else iso(self.now))

    def finish(self):
        b = self.prog["book"]
        if self.prog["steps"] and not self.prog.get("scan_last"):
            t0 = parse(self.prog["steps"][-1]["scan_from"])
            self.prog["scan_last"] = p_scan(b, perp_minutes(self.tape, self.pp["symbols"], t0, self.end), t0, self.end, self.pp)
        em = W.end_marks(self.tape, W.priced(self.meta), self.end)
        for s, p in em.items():
            b["last_px"][s] = p
        v = max(0.0, value_at(b, em)); start = self.cfg["tm_account_start_usd"]
        meta = {k: v2 for k, v2 in self.meta.items() if k != "config"}
        res = dict(session=meta, config=self.cfg, steps=self.prog["steps"], scan_last=self.prog.get("scan_last"), end_marks=em, end_utc=self.meta["end_utc"],
                   final=dict(value_usd=v, gain_pct=(v / start - 1) * 100, cash_usd=b["cash"], positions=b["qty"], spread_usd=b["spread_usd"], fee_usd=b["fee_usd"],
                              penalty_usd=b["penalty_usd"], costs_paid_usd=b["spread_usd"] + b["fee_usd"] + b["penalty_usd"], traded_usd=b["traded_usd"],
                              funding_usd=b["funding_usd"], fallback_hours=b["fallback_hours"], shortfall_usd=b["shortfall_usd"], closeouts=b["closeouts"],
                              exits_hit=b["exits_hit"], largest_drop_on_minutes=b["largest_drop"], max_gross=self.pmg),
                   costs={k: self.cfg[k] for k in P_KEYS}, funding_source=self.pp["source"], limits=LIMITS)
        self.prog["done"] = True; self.now = self.end; S.save_json(self.dir / "result.json", res); self.save()


def run_scripted(session_id, answers, tape=None):
    s = PSession(session_id, tape=tape)
    for body in answers:
        if s.done():
            break
        s.packet(); r = s.submit(body)
        if not r.get("ok"):
            raise RuntimeError(f"answer refused: {r}")
    return s


# ---- the yardsticks
def flip(w, ex, marks):
    """The answer with every sign flipped; stops and targets mirrored about the price at the wake (same distance, other side)."""
    if w is None:
        return None, None
    fx = {}
    for s, e in (ex or {}).items():
        m = marks.get(s)
        if m is None:
            continue
        y = {k: 2 * m - x for k, x in e.items() if 2 * m - x > 0}
        if y:
            fx[s] = y
    return {s: -v for s, v in w.items()}, fx


def twin_answers(answers, steps, rows, allowed, rng):
    """One draw of the perp twin (accepted by the lead 2026-11-25): the model's decisions (the first wake and each wake where it set
    a new target) placed at as many random wakes (the first wake always one), in time order. At its i-th wake the twin takes the
    model's i-th target: the same gross and number of symbols, the symbols drawn at random from the allowed list, each with a random
    sign and one of the model's absolute weights in random order. Stops and targets keep their percent distance from the model's
    price, applied from the twin's own price on the side its sign needs. A flat target stays flat. Every other wake is no_change."""
    n = len(answers); dec = [k for k in range(n) if k == 0 or (answers[k][0] is not None and steps[k]["changed"])]
    when = [0] + sorted(rng.sample(range(1, n), len(dec) - 1)) if n > 1 else [0]
    out = [(None, None)] * n
    for k_twin, k_model in zip(when, dec):
        w = steps[k_model]["target"] if answers[k_model][0] is None else norm(answers[k_model][0]); ex = answers[k_model][1] or {}
        items = sorted(w.items()); rng.shuffle(items); names = rng.sample(allowed, len(items)); tw, tx = {}, {}
        mk_m, mk_t = rows[k_model]["marks"], rows[k_twin]["marks"]
        for (ms, mv), ts in zip(items, names):
            sign = rng.choice([-1, 1]); tw[ts] = sign * abs(mv); e = ex.get(ms) or {}; m0, m1 = mk_m.get(ms), mk_t.get(ts)
            if e and m0 and m1:
                y = {}
                for kind, lv in e.items():
                    d = abs(lv / m0 - 1); adverse = kind == "stop"
                    y[kind] = m1 * (1 - d) if (sign > 0) == adverse else m1 * (1 + d)
                tx[ts] = {k2: v for k2, v in y.items() if v > 0}
        out[k_twin] = (tw, tx)
    return out


def p_stats(b, f, start):
    return dict(final_value_usd=f, final_gain_pct=(f / start - 1) * 100, largest_drop_pct=b["largest_drop"] * 100, funding_usd=b["funding_usd"],
                fallback_hours=b["fallback_hours"], spread_usd=b["spread_usd"], fee_usd=b["fee_usd"], penalty_usd=b["penalty_usd"],
                costs_paid_usd=b["spread_usd"] + b["fee_usd"] + b["penalty_usd"], closeouts=len(b["closeouts"]), exits_hit=len(b["exits_hit"]), traded_usd=b["traded_usd"])


def score_at(meta, table, answers, steps, pp, mins, cfg, draws, seed):
    """The model's answers, its twins and its yardsticks, all through one book setting pp (one fee level)."""
    from timemachine import score_weights as SW
    sid = meta["session"]; start = cfg["tm_account_start_usd"]
    book, _, final = run_perp(meta, table, answers, pp, mins, cfg)
    out = dict(model_stats=p_stats(book, final, start), twins={}, yardsticks={})
    tw = []
    for i in range(draws):
        rng = random.Random(f"perp_twin:{seed}:{sid}:{i}")  # the same draws at every fee level
        b2, _, f2 = run_perp(meta, table, twin_answers(answers, steps, table["rows"], meta["symbols"], rng), pp, mins, cfg); tw.append((b2, f2))
    out["twins"]["random_sign_twin"] = SW.twin_set("random_sign_twin", tw, final, cfg)
    fl = [flip(w, ex, table["rows"][k]["marks"]) for k, (w, ex) in enumerate(answers)]
    if fl and fl[0][0] is None:
        fl[0] = flip(steps[0]["target"], {}, table["rows"][0]["marks"])
    bf, _, ff = run_perp(meta, table, fl, pp, mins, cfg); out["yardsticks"]["signs_flipped"] = dict(stats=p_stats(bf, ff, start), model_above=final > ff)
    bm = meta["benchmark"]
    for name, w in ((f"hold_long_{bm}", 1.0), (f"hold_short_{bm}", -1.0)):
        bh, _, fh = run_perp(dict(meta, opening={}), table, [({bm: w}, None)] + [(None, None)] * (len(answers) - 1), pp, mins, cfg)
        out["yardsticks"][name] = dict(stats=p_stats(bh, fh, start), model_above=final > fh)
    return out


def score(session_id, tape=None, draws=None, seed=None, fee_bps=None):
    """Checks that the session's own run replays to the cent, then scores the same answers at each fee per side in
    tm_perp_fee_levels_bps (or at fee_bps alone), with the session's spreads, funding and minutes. Prices are not printed."""
    d = S.runs_dir() / session_id; meta = json.loads((d / "session.json").read_text()); assert meta.get("instrument") == "perp", "not a perp session"
    res = json.loads((d / "result.json").read_text()); cfg = res["config"]
    draws = int(draws if draws is not None else cfg["tm_weights_twin_draws"]); seed = int(seed if seed is not None else cfg["tm_weights_twin_seed"])
    tape = tape or W.session_tape(meta); table = W.price_table(tape, meta)
    assert [st["row"] for st in res["steps"]] == table["rows"], "the tape gives other prices than the session recorded: it was changed after the run"
    syms = W.priced(meta); pp = session_params(meta, cfg, tape); mins = perp_minutes(tape, pp["symbols"], parse(meta["wakes"][0]), parse(meta["end_utc"]))
    answers = [(st["asked"], st["exits"]) for st in res["steps"]]
    _, _, final = run_perp(meta, table, answers, pp, mins, cfg)
    assert round(final, 2) == round(res["final"]["value_usd"], 2), "the replay of the model's answers does not match the recorded final value"
    levels = [fee_bps] if fee_bps is not None else list(cfg.get("tm_perp_fee_levels_bps") or p_config()["tm_perp_fee_levels_bps"])
    out = dict(session=session_id, model=meta["model"], trader=meta["trader"], wakes=len(answers), window=meta["window"], max_gross=meta["perp"]["max_gross"],
               funding_source=pp["source"], half_spread_bps={s: pp["hs"][s] * 1e4 for s in syms}, session_fee_bps={s: pp["fee"][s] * 1e4 for s in syms},
               session_value_usd=res["final"]["value_usd"], fee_levels_bps=levels, main_fee_bps=levels[len(levels) // 2], by_fee={})
    for f in levels:
        out["by_fee"][f"{f:g}"] = score_at(meta, table, answers, res["steps"], with_fee(pp, f), mins, cfg, draws, seed)
    return out


def public(r):
    return dict(r, by_fee={f: dict(v, twins={k: {a: b for a, b in t.items() if not a.startswith("_")} for k, t in v["twins"].items()}) for f, v in r["by_fee"].items()})


def main(argv=None):
    a = argparse.ArgumentParser(description="Makes or scores a perp session. Pretend money only."); sub = a.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--trader", required=True); n.add_argument("--model", required=True); n.add_argument("--method", required=True)
    n.add_argument("--symbols", required=True); n.add_argument("--from", dest="start", required=True); n.add_argument("--to", dest="end", required=True)
    n.add_argument("--max-gross", type=float, default=1.0); n.add_argument("--open", default="cash"); n.add_argument("--wakes", default=None)
    n.add_argument("--news", action="store_true"); n.add_argument("--session"); n.add_argument("--note"); n.add_argument("--benchmark")
    n.add_argument("--tape", choices=["main", "fast"], default="main", help="fast: the second price store tape_fast.sqlite, read-only, with its funding table")
    n.add_argument("--long-only", action="store_true", help="refuse a negative weight")
    sc = sub.add_parser("score"); sc.add_argument("session"); sc.add_argument("--draws", type=int); sc.add_argument("--seed", type=int); sc.add_argument("--json", action="store_true")
    sc.add_argument("--fee-bps", type=float, help="one fee per side instead of every level in tm_perp_fee_levels_bps")
    x = a.parse_args(argv)
    if x.cmd == "score":
        r = public(score(x.session, draws=x.draws, seed=x.seed, fee_bps=x.fee_bps))
        if x.json:
            print(json.dumps(r, indent=1, sort_keys=True)); return
        print(f"session {r['session']}  model {r['model']}  wakes {r['wakes']}  max gross {r['max_gross']:g}  half spread bps {json.dumps(r['half_spread_bps'], sort_keys=True)}")
        print(f"funding: {json.dumps(r['funding_source'], sort_keys=True)}")
        for f, v in r["by_fee"].items():
            m = v["model_stats"]; t = v["twins"]["random_sign_twin"]; main = "  (main line)" if float(f) == r["main_fee_bps"] else ""
            print(f"fee {f} bps per side{main}: model gain {m['final_gain_pct']:.2f}%  largest drop {m['largest_drop_pct']:.2f}%  costs {m['costs_paid_usd']:.2f} USD  "
                  f"funding {m['funding_usd']:.2f} USD  close-outs {m['closeouts']}  exits {m['exits_hit']}")
            print(f"  random_sign_twin ({t['final_gain_pct']['n']} draws): median gain {t['final_gain_pct']['median']:.2f}%  model percentile {t['model_percentile']:.1f}  "
                  f"above median {t['model_above_median']}  above pass percentile {t['model_above_pass_percentile']}")
            for n2, y in v["yardsticks"].items():
                print(f"  {n2}: gain {y['stats']['final_gain_pct']:.2f}%  model above: {y['model_above']}")
        return
    kind, rules = W.wake_choice(x.wakes, "crypto")
    sid = x.session or f"P-{x.trader}-{x.start}-{dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
    folder = create(sid, x.trader, x.model, x.method, x.start, x.end, [s.strip() for s in x.symbols.split(",") if s.strip()], max_gross=x.max_gross,
                    opening=None if x.open == "cash" else json.loads(x.open), rules=rules, wake_kind=kind, news=x.news, note=x.note, benchmark=x.benchmark,
                    tape=W.fast_tape() if x.tape == "fast" else None, long_only=x.long_only)
    meta = json.loads((folder / "session.json").read_text())
    print(json.dumps(dict(session=sid, folder=str(folder), wakes=len(meta["wakes"]), first_wake=meta["wakes"][0], end_utc=meta["end_utc"], max_gross=x.max_gross), indent=1))


if __name__ == "__main__":
    main()
