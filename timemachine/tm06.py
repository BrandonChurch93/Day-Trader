"""Plan TM06: the owner's own method. Pick the hot coins once a day (part P), trade swings on a few coins hourly (part S),
replay a finished swing session at 2x and 3x (item 6), and a negative control with no model (item 7). Pretend money only.

Everything here runs on the futures book of timemachine/perp.py and on the fast tape (tape_fast.sqlite), read-only.

The fast tape
  prices       its 1Min and 1Day bars. Fills at the open of the first recorded minute at or after the wake, as in every session.
  half spread  per coin: tm_perp_half_spread_bps by symbol, else tm_crypto_half_spread_bps_by_coin, else the placeholder
               tm_crypto_half_spread_bps_default (perp.half_spread_bps).
  funding      from its funding table, venue per coin from tm_fast_funding_venue (default kraken_futures_pf, hourly, all 23
               coins from 2025-11-19). An hourly rate stamped t is charged at t. An 8 hour rate (any 8 hourly venue) stamped t is
               known at t and charged as one eighth at each of the 8 whole hours after t. A charge time with no stored rate
               (before the venue's first rate, or in a gap) pays tm_perp_fallback_rate_per_day, long or short, and is counted.
               No rate stamped after the simulated time is ever charged or shown.
  open interest  the 24 hour change, in the packet only, from tm_fast_oi_venue, each row known tm_fast_oi_known_after_hours
               after its stamp.
  attention    timemachine/attention.py get_attention(coin, wake, days): only values known at the wake.

Part P, the picker (PickerSession): one wake a day at tm06_plan.picker_wake_hour_utc. The answer is
    {"coins": ["SOL/USD", "ZEC/USD"], "reasons": {"SOL/USD": "one plain line", "ZEC/USD": "one plain line"}, "why": "..."}
with 0 to tm06_plan.picker_max_names coins from the list as of the wake (a coin with a recorded minute in the tm06_pick_listed_hours
before it). The desk holds the named coins in equal parts adding up to 1x, long only, on the futures book. Naming the same
coins again trades nothing; a changed list moves every coin to its equal part, trading only the difference (perp.p_step,
with tm_perp_min_change). No coins means cash.

Part S, swing sessions: a perp session waking every tm06_plan.swing_wake_minutes on a fixed set of coins, long or flat
(long_only), gross at most tm06_plan.swing_max_gross, stops and targets as the book has them.

Negative control: code_traders.reversal on tm06_reversal's symbol, every tm06_reversal minutes, after a move of more than
tm06_plan.control_move_bps, through a perp session.

Every number the plan fixes is read from tm06_plan (plan(cfg)); the tm06_ keys hold only what the plan leaves to the tool.

Scoring (score_picker, score_swing, score_control) replays the session to the cent, then runs the same answers and every
yardstick through the same book at each fee in tm_perp_fee_levels_bps. timemachine/score_tm06.py collects them.

python3 timemachine/tm06.py picker --trader P01 --model M --method CARD.md --month 2026-04 [--session ID]     (coins: tm06_plan.coins)
python3 timemachine/tm06.py swing --trader S01 --model M --method CARD.md --week 1 [--session ID]     (tm06_plan.swing_weeks; 168 wakes)
  (or --from/--to, and for swing --symbols, instead of --month or --week. Both refuse to start while a coin would be priced at
   the placeholder half spread tm_crypto_half_spread_bps_default.)
python3 timemachine/tm06.py control --from 2026-03-01 --to 2026-03-31 [--session ID]     (runs the rule at once)
python3 timemachine/tm06.py score SESSION [--draws N]
"""
import argparse, datetime as dt, hashlib, json, math, os, random, secrets, shutil, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from timemachine import session as S, weights as W, perp as P
from timemachine.attention import get_attention

UTC = S.UTC
iso, parse = S.iso, S.parse
T_KEYS = ["tm_fast_funding_venue", "tm_fast_oi_venue", "tm_fast_oi_known_after_hours", "tm06_pick_change_hours", "tm06_pick_volume_usual_days",
          "tm06_pick_listed_hours", "tm06_pick_attention_days", "tm06_attention_rule", "tm06_reversal", "tm06_plan",
          "tm06_swing_packet_hour_bars", "tm06_swing_packet_minute_bars", "tm06_handoff_swing_wakes", "tm06_handoff_picker_split_day"]
LIMITS = P.LIMITS + [
    "The fast tape's funding is from Kraken's non-US perps by default; a US venue's rates may differ. Before a coin's first stored rate the fixed fallback is charged.",
    "Open interest and attention counts are shown as they were known at the wake; the store does not always say when a value was first published, so attention uses the reader's assumed lag."]
DAY = 86400


def t_config(path=ROOT / "config" / "thresholds.yaml"):
    c = W.lev_config(path, proposed=ROOT / "timemachine" / "no_such_file", keys=T_KEYS); c.pop("_from"); return c


def full_config():
    cfg = P.full_config(); cfg.update(t_config()); return cfg


def plan(cfg):
    """The plan's own numbers, each read from tm06_plan (timemachine/PLAN_TM06_hot_coin_swing.md governs). A session made
    before the tool read tm06_plan (the control TM06-0-control) carries its rule in tm06_reversal and is scored from that."""
    p = cfg.get("tm06_plan"); r = cfg["tm06_reversal"]
    if not p:
        return dict(move_pct=float(r["move_pct"]), control_leverage=list(r["multiples"]), main_fee_bps=None)
    return dict(coins=[f"{c}/USD" for c in p["coins"]], wake_hour=int(p["picker_wake_hour_utc"]), max_names=int(p["picker_max_names"]),
                rise_hours=24 * float(p["picker_rise_days"]), swing_weeks=p["swing_weeks"], swing_minutes=int(p["swing_wake_minutes"]),
                swing_max_gross=float(p["swing_max_gross"]), main_fee_bps=float(p["main_fee_bps"]), carried=list(p["carried_leverage"]),
                move_pct=float(p["control_move_bps"]) / 100, control_leverage=list(p["control_leverage"]))


def main_fee(cx):
    """The judged fee: tm06_plan.main_fee_bps, which must be one of tm_perp_fee_levels_bps (the middle level for an older session)."""
    f = plan(cx["cfg"])["main_fee_bps"]; lv = cx["levels"]
    assert f is None or f in lv, "tm06_plan.main_fee_bps is not one of tm_perp_fee_levels_bps"
    return lv[len(lv) // 2] if f is None else f


def ep(t):
    return int(t.timestamp()) if isinstance(t, dt.datetime) else int(t)


def rows(tape, sql, args):
    """A read from the fast tape's own tables; a tape without them (the main tape) gives nothing."""
    try:
        return tape._conn().execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        return []


# ---- funding and open interest from the fast tape
def fast_funding(tape, symbols, cfg, t0, t1):
    """{symbol: {hour epoch: rate per hour}} for charges from t0 to t1, and a plain line per symbol saying where it came from.
    Positive: longs pay. Only rates stamped at or before the hour they are charged."""
    a, b = ep(t0), ep(t1); out, src = {}, {}
    for s in symbols:
        venue = P.per(cfg["tm_fast_funding_venue"], s)
        rs = rows(tape, "SELECT t, rate, interval_hours FROM funding WHERE symbol = ? AND venue = ? AND t >= ? AND t <= ? ORDER BY t", (s, venue, a - 8 * 3600, b))
        if not rs:
            src[s] = f"no {venue} rate on the fast tape for this window: tm_perp_fallback_rate_per_day"; continue
        f = {}
        for t, r, H in rs:
            H = int(round(H))
            if H <= 1:
                f[t // 3600 * 3600] = float(r)
            else:  # known at t; charged in equal parts at each whole hour after it, never before
                for j in range(1, H + 1):
                    f[t // 3600 * 3600 + 3600 * j] = float(r) / H
        out[s] = f
        src[s] = (f"fast tape funding, {venue}, every {int(round(rs[0][2]))} h, first rate read {iso(dt.datetime.fromtimestamp(rs[0][0], UTC))}; "
                  "before it and in any gap tm_perp_fallback_rate_per_day")
    return out, src


def fast_params(symbols, cfg, tape, t0, t1):
    funding, src = fast_funding(tape, symbols, cfg, t0, t1)
    pp = P.p_params(symbols, cfg, funding=funding); pp["hours"] = {s: 1 for s in symbols}; pp["source"] = src
    return pp


def last_funding(tape, s, now, cfg):
    """The latest stored rate stamped at or before now, per its own interval (not per hour), or None."""
    r = rows(tape, "SELECT t, rate, interval_hours FROM funding WHERE symbol = ? AND venue = ? AND t <= ? ORDER BY t DESC LIMIT 1",
             (s, P.per(cfg["tm_fast_funding_venue"], s), ep(now)))
    return dict(rate=r[0][1], every_hours=r[0][2], stamped_utc=iso(dt.datetime.fromtimestamp(r[0][0], UTC))) if r else None


def oi_change_pct(tape, s, now, cfg):
    """Percent change in open interest over the 24 hours before the latest row known at now, or None."""
    venue = P.per(cfg["tm_fast_oi_venue"], s); n = ep(now) - int(float(cfg["tm_fast_oi_known_after_hours"]) * 3600)
    r1 = rows(tape, "SELECT t, oi_contracts FROM open_interest WHERE symbol = ? AND venue = ? AND t <= ? ORDER BY t DESC LIMIT 1", (s, venue, n))
    if not r1:
        return None
    r0 = rows(tape, "SELECT t, oi_contracts FROM open_interest WHERE symbol = ? AND venue = ? AND t <= ? AND t >= ? ORDER BY t DESC LIMIT 1",
              (s, venue, r1[0][0] - DAY, r1[0][0] - 2 * DAY))
    return (r1[0][1] / r0[0][1] - 1) * 100 if r0 and r0[0][1] > 0 else None


# ---- what a coin looks like at a wake
def price_at(tape, s, t):
    """The last finished minute's close at or before t (within a day), else the last finished daily close."""
    b = rows(tape, "SELECT c FROM bars WHERE symbol = ? AND tf = '1Min' AND t <= ? AND t >= ? ORDER BY t DESC LIMIT 1", (s, ep(t) - 60, ep(t) - DAY))
    if b:
        return b[0][0]
    b = rows(tape, "SELECT c FROM bars WHERE symbol = ? AND tf = '1Day' AND t <= ? ORDER BY t DESC LIMIT 1", (s, ep(t) - DAY))
    return b[0][0] if b else None


def listed(tape, symbols, t, cfg):
    """The coins the desk can fill at t: a recorded minute in the tm06_pick_listed_hours before t."""
    lo = ep(t) - int(float(cfg["tm06_pick_listed_hours"]) * 3600)
    return [s for s in symbols if rows(tape, "SELECT 1 FROM bars WHERE symbol = ? AND tf = '1Min' AND t >= ? AND t <= ? LIMIT 1", (s, lo, ep(t) - 60))]


def change_pct(tape, s, t, hours):
    a, b = price_at(tape, s, ep(t) - int(hours * 3600)), price_at(tape, s, t)
    return (b / a - 1) * 100 if a and b else None


def volume_row(tape, s, t, cfg):
    """Dollar volume over the last 24 hours (minutes) against the mean daily dollar volume of the usual-days days before."""
    n = ep(t); v24 = rows(tape, "SELECT SUM(v * c) FROM bars WHERE symbol = ? AND tf = '1Min' AND t >= ? AND t <= ?", (s, n - DAY, n - 60))[0][0]
    days = int(cfg["tm06_pick_volume_usual_days"])
    d = rows(tape, "SELECT v * c FROM bars WHERE symbol = ? AND tf = '1Day' AND t <= ? AND t > ? ORDER BY t", (s, n - 2 * DAY, n - (days + 2) * DAY))
    usual = sum(x[0] for x in d) / len(d) if len(d) == days else None
    return dict(usd_24h=v24, usual_usd_per_day=usual, ratio=(v24 / usual if v24 is not None and usual else None))


def attention_rows(coin, t, days, db):
    """Daily attention counts known at t, per source: {source: [[day, value], ...]}. Hourly and capture-only sources left out."""
    out = {}
    for r in get_attention(coin, ep(t), int(days), db_path=db):
        if r["source"].endswith("_daily"):
            out.setdefault(r["source"], []).append([iso(dt.datetime.fromtimestamp(r["ts_utc"], UTC))[:10], r["value"]])
    return out


def attention_rise(coin, t, cfg, db):
    """Yardstick (c): the latest daily count of the rule's source known at t against the mean of the before_days days before it.
    None when any of those counts is missing or their mean is zero."""
    rule = cfg["tm06_attention_rule"]; n = int(rule["before_days"])
    vals = {r["ts_utc"]: r["value"] for r in get_attention(coin, ep(t), int(rule["lookback_days"]), db_path=db) if r["source"] == rule["source"]}
    if not vals:
        return None
    last = max(vals); before = [vals.get(last - DAY * j) for j in range(1, n + 1)]
    if any(v is None for v in before) or sum(before) <= 0:
        return None
    return vals[last] / (sum(before) / n) - 1


def coin_row(tape, s, t, cfg, db):
    hrs = cfg["tm06_pick_change_hours"]
    news = tape.news(t, symbols=[s], since_utc=t - dt.timedelta(days=1), limit=int(cfg["tm_weights_max_headlines_per_symbol"]))
    return dict(price=price_at(tape, s, t), change_pct={f"{int(h)}h": change_pct(tape, s, t, h) for h in hrs}, volume=volume_row(tape, s, t, cfg),
                funding_latest=last_funding(tape, s, t, cfg), open_interest_change_24h_pct=oi_change_pct(tape, s, t, cfg),
                attention=attention_rows(s.split("/")[0], t, cfg["tm06_pick_attention_days"], db),
                headlines=[dict(utc=iso(n["created"]), headline=n["headline"], source=n["source"]) for n in news])


# ---- making sessions
def default_attention_db():
    from timemachine.tape import DEFAULT_STORE
    return str(Path(os.environ.get("TM_STORE", str(DEFAULT_STORE))) / "attention.sqlite")


def tape_coins(tape):
    return json.loads(tape.get_meta("coins_json") or "[]") if hasattr(tape, "get_meta") else []


def measured_spread(symbols, cfg):
    """A picker or swing session starts only when every coin it prices has its own half spread (tm_perp_half_spread_bps by
    symbol, or tm_crypto_half_spread_bps_by_coin), never the placeholder tm_crypto_half_spread_bps_default."""
    m, coin = cfg["tm_perp_half_spread_bps"], (cfg.get("tm_crypto_half_spread_bps_by_coin") or {})
    bad = [s for s in symbols if s not in m and s.split("/")[0] not in coin]
    assert not bad, f"no measured half spread for {', '.join(bad)}: set it in tm_perp_half_spread_bps before a session (the placeholder is not used)"


def create_picker(session_id, trader_id, model, method_path, start_date, end_date, tape=None, coins=None, attention_db=None, note=None):
    """coins: tm06_plan.coins unless given (tests)."""
    tape = tape or W.fast_tape(); cfg = full_config(); pl = plan(cfg); coins = list(coins or pl["coins"]); assert coins, "no coin list"
    measured_spread(coins + ["BTC/USD"], cfg); db = str(attention_db or default_attention_db())
    return P.create(session_id, trader_id, model, method_path, start_date, end_date, coins, max_gross=1.0,
                    rules=[dict(every="day", utc_hours=[pl["wake_hour"]])], tape=tape, note=note, benchmark="BTC/USD", long_only=True,
                    extra=dict(tm06=dict(part="P", max_names=pl["max_names"], attention_db=db, config={k: cfg[k] for k in T_KEYS})))


def create_swing(session_id, trader_id, model, method_path, start_date, end_date, symbols, tape=None, note=None, news=False):
    tape = tape or W.fast_tape(); cfg = full_config(); pl = plan(cfg); measured_spread(list(symbols) + ["BTC/USD"], cfg)
    return P.create(session_id, trader_id, model, method_path, start_date, end_date, symbols, max_gross=pl["swing_max_gross"],
                    rules=[dict(every="minutes", step=pl["swing_minutes"])], tape=tape, note=note, news=news, benchmark="BTC/USD", long_only=True,
                    extra=dict(tm06=dict(part="S", config={k: cfg[k] for k in T_KEYS})))


def plan_week(n, cfg=None):
    """Swing week n (1 to 4) of tm06_plan.swing_weeks: its first day, its last day (the Sunday; the plan's end is the next
    Monday, not included) and its coins as pairs."""
    pl = plan(cfg or full_config()); w = pl["swing_weeks"][int(n) - 1]
    last = (dt.date.fromisoformat(w["end"]) - dt.timedelta(days=1)).isoformat()
    return w["start"], last, [f"{c}/USD" for c in w["coins"]]


def plan_month(month, cfg=None):
    """The picker's dates for one calendar month YYYY-MM, clipped to tm06_plan.picker_start and picker_end."""
    p = (cfg or full_config())["tm06_plan"]; y, m = (int(x) for x in month.split("-"))
    first = dt.date(y, m, 1); last = (dt.date(y + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1))
    a, b = max(first, dt.date.fromisoformat(p["picker_start"])), min(last, dt.date.fromisoformat(p["picker_end"]))
    assert a <= b, f"{month} is outside the plan's picker dates"
    return a.isoformat(), b.isoformat()


def create_control(session_id, start_date, end_date, tape=None, note=None):
    tape = tape or W.fast_tape(); cfg = full_config(); r = cfg["tm06_reversal"]; mv = plan(cfg)["move_pct"]
    return P.create(session_id, "RULE", "none (code trader)", f"timemachine/code_traders.py#reversal({r['symbol']}, {mv:g})", start_date, end_date,
                    [r["symbol"]], max_gross=1.0, rules=[dict(every="minutes", step=int(r["minutes"]))], tape=tape, note=note, benchmark=r["symbol"],
                    extra=dict(tm06=dict(part="C", config={k: cfg[k] for k in T_KEYS})))


def run_control(session_id, tape=None):
    from timemachine import code_traders as C, run_code_trader as RC
    meta = json.loads((S.runs_dir() / session_id / "session.json").read_text()); c = meta["tm06"]["config"]; r = c["tm06_reversal"]
    return RC.run_weights_fast(session_id, C.reversal(r["symbol"], plan(c)["move_pct"], int(r["minutes"])), tape or W.session_tape(meta))


def check_pick(body, listed_now, max_names, cfg):
    mx = int(cfg["tm_weights_why_max_chars"])
    if not isinstance(body, dict):
        return ["The body must be a JSON object."]
    if set(body) - {"driver"} != {"coins", "reasons", "why"}:
        return ['An answer is {"coins": [...], "reasons": {"COIN/USD": "one plain line", ...}, "why": "..."}. An empty list means cash.']
    why, coins, rs = body["why"], body["coins"], body["reasons"]; errs = []
    if not isinstance(why, str) or not why.strip() or len(why) > mx:
        errs.append("why: one short plain paragraph (at most tm_weights_why_max_chars characters).")
    if not isinstance(coins, list) or not all(isinstance(c, str) for c in coins) or len(set(coins)) != len(coins):
        return errs + ["coins is a list of different coin names such as \"SOL/USD\"."]
    if len(coins) > max_names:
        errs.append(f"At most {max_names} coins (tm06_plan.picker_max_names).")
    bad = [c for c in coins if c not in listed_now]
    if bad:
        errs.append(f"Not on the list at this wake: {', '.join(bad)}. The list is: {', '.join(listed_now)}.")
    if not isinstance(rs, dict) or set(rs) != set(coins) or not all(isinstance(v, str) and v.strip() and "\n" not in v and len(v) <= mx for v in rs.values()):
        errs.append("reasons gives exactly one plain line (no line break) for each coin named, and nothing else.")
    if "driver" in body and body["driver"] not in W.DRIVERS:
        errs.append(f"driver, if given, is one of: {', '.join(W.DRIVERS)}.")
    return errs


# ---- the answer key: traders share one machine, so an answer built from another session's (or an older) packet is refused
KEY_RULE = ("Every answer carries \"session\" and \"answer_key\" copied from this packet. An answer whose session or answer_key is not "
            "this session's current packet is refused: it was built from another session's packet or an older step.")


def keyed(sess, out):
    """Adds a fresh random answer_key (nothing in it depends on the date or the session) and puts it in the answer forms."""
    out["answer_key"] = secrets.token_hex(8)
    for f in out["answer_forms"]:
        f["session"] = out["session"]; f["answer_key"] = out["answer_key"]
    out["rules"].append(KEY_RULE)
    return out


def key_check(sess, body):
    """None if the body is for this session's current packet, else the refusal. Logs each refusal to key_refusals.jsonl."""
    if not isinstance(body, dict):
        return None  # the usual checks answer this
    sid = sess.meta["session"]; k = sess.prog["k"]; pk = sess.dir / "packets" / f"{k}.json"
    want = json.loads(pk.read_text()).get("answer_key") if pk.exists() else None
    if body.get("session") != sid:
        why = (f"This answer names session {body.get('session')!r}, but it was sent to session {sid}. The packet it was built from belongs to "
               f"another session. Call /next?session={sid} and build the answer from that packet only.")
    elif want is None or body.get("answer_key") != want:
        why = (f"The answer_key does not match the current packet of session {sid} (step {k + 1}). The packet it was built from belongs to "
               "another session or an older step. Call /next for this session and build the answer from that packet only.")
    else:
        return None
    with open(sess.dir / "key_refusals.jsonl", "a") as f:
        f.write(json.dumps(dict(k=k, sent_session=body.get("session"), key_given=body.get("answer_key") is not None)) + "\n")
    return sess.bad([why])


def unkeyed(body):
    return {x: v for x, v in body.items() if x not in ("session", "answer_key")}


class PickerSession(P.PSession):
    """Part P: a daily perp session over the whole coin list, answered with coin names."""

    def __init__(self, session_id, tape=None):
        super().__init__(session_id, tape=tape)
        t = self.meta["tm06"]; self.max_names = int(t["max_names"]); self.att_db = t["attention_db"]; self.tcfg = dict(self.cfg, **t["config"])

    def listed_now(self):
        return listed(self.tape, self.allowed, self.now, self.tcfg)

    def packet(self, fresh=False):
        if self.done():
            raise S.Done()
        k = self.prog["k"]; p = self.dir / "packets" / f"{k}.json"
        if p.exists() and not fresh:
            return json.loads(p.read_text())
        last = self.prog["steps"][-1] if self.prog["steps"] else None; since = view = None
        if last is not None:  # what happened since the last wake, on a copy; the real scan runs at submit
            b2 = json.loads(json.dumps(self.prog["book"])); t0 = parse(last["scan_from"])
            sc = P.p_scan(b2, P.perp_minutes(self.tape, self.pp["symbols"], t0, self.now), t0, self.now, self.pp); view = b2
            since = dict(closeout=sc["closeout"], funding_usd=sc["funding_usd"])
        ls = self.listed_now(); n = self.max_names
        out = dict(session=self.meta["session"], kind="weights", instrument="perp", part="P", trader=self.tid, utc=iso(self.now), step=k + 1, of=self.N,
                   next_wake_utc=iso(self.next_time(k)), is_last=k + 1 == self.N, market="crypto", max_names=n, list=ls,
                   coins={s: coin_row(self.tape, s, self.now, self.tcfg, self.att_db) for s in ls}, book=self.book_view(view),
                   last_wake=None if last is None else dict(utc=last["utc"], named=sorted(last["asked"] or {}), reasons=last["reasons"], trades=last["trades"],
                                                            skipped=last["skipped"], since=since),
                   looks_left=self.looks_left(), hard_lines=W.HARD_LINES,
                   answer_forms=[{"coins": ls[:2], "reasons": {c: "one plain line" for c in ls[:2]}, "why": "..."}, {"coins": [], "reasons": {}, "why": "..."}],
                   rules=[f"Name 0 to {n} coins from the list. The desk holds them in equal parts adding up to the account value, long only, on perpetual futures.",
                          "Naming the same coins as yesterday trades nothing. A changed list moves every coin to its equal part, trading only the difference.",
                          "No coins means cash. Give one plain line of reason for each coin named.",
                          "Funding is paid or received on the whole position value each hour: a long pays a positive rate.",
                          "change_pct is the price change over 1 hour, 24 hours, 7 days and 30 days. volume.ratio is the last 24 hours' dollar volume against "
                          "the coin's own mean day of the 30 days before. attention is daily counts known at this time; a missing count is unknown, not zero.",
                          "More bars: /look what=bars timeframe=1Min, 15Min, 1Hour, 4Hour or 1Day."])
        if fresh:
            return out
        keyed(self, out); p.parent.mkdir(exist_ok=True); S.save_json(p, out)
        return json.loads(p.read_text())

    def submit(self, body):
        if self.done():
            raise S.Done()
        refused = key_check(self, body)
        if refused:
            return refused
        body = unkeyed(body) if isinstance(body, dict) else body
        errs = check_pick(body, self.listed_now(), self.max_names, self.cfg)
        if errs:
            return self.bad(errs)
        c = body["coins"]; b2 = dict(weights={x: 1.0 / len(c) for x in c}, why=body["why"], reasons=body["reasons"])
        if "driver" in body:
            b2["driver"] = body["driver"]
        return super().submit(b2)


class SwingSession(P.PSession):
    """Part S: a perp session whose packet also shows, per coin, the last tm06_swing_packet_hour_bars hourly bars (as bars),
    the last tm06_swing_packet_minute_bars finished one-minute bars (bars_1min) and the picker's volume row."""

    def symbol_rows(self):
        out = super().symbol_rows(); c = dict(self.cfg, **self.meta["tm06"]["config"])
        nh, nm = int(c["tm06_swing_packet_hour_bars"]), int(c["tm06_swing_packet_minute_bars"])
        for s in self.allowed:
            hb = S.built_bars(self.tape, s, 3600, self.now - dt.timedelta(hours=nh + 1), self.now, nh)
            mb = self.tape.bars(s, "1Min", self.now - dt.timedelta(minutes=nm + 1), self.now, limit=nm)  # finished minutes only
            out[s]["bars"] = [[S.iso(b["t"]), b["o"], b["h"], b["l"], b["c"], b["v"]] for b in hb]
            out[s]["bars_1min"] = [[S.iso(b["t"]), b["o"], b["h"], b["l"], b["c"], b.get("v")] for b in mb]
            out[s]["volume"] = volume_row(self.tape, s, self.now, c)
        return out

    def packet(self, fresh=False):
        """The perp packet with the swing's own wording: long or flat (the perp text offers shorts), and what the bars are."""
        if self.done():
            raise S.Done()
        p = self.dir / "packets" / f"{self.prog['k']}.json"
        if p.exists() and not fresh:
            return json.loads(p.read_text())
        out = super().packet(fresh=True); mg = self.pmg; s0 = self.allowed[0]; c = dict(self.cfg, **self.meta["tm06"]["config"])
        out["answer_forms"][0] = {"weights": {s0: min(0.5, mg)}, "exits": {s0: {"stop": "price", "target": "price"}}, "why": "..."}
        out["rules"][0] = f"Perpetual futures, long or flat. Each weight is from 0 to {mg:g}. The weights add up to at most {mg:g}. The rest is margin."
        out["rules"].insert(1, f"bars: the last {int(c['tm06_swing_packet_hour_bars'])} finished hourly bars. bars_1min: the last {int(c['tm06_swing_packet_minute_bars'])} "
                               "finished one-minute bars. volume.ratio is the last 24 hours' dollar volume against the coin's own mean day of the 30 days before.")
        if fresh:
            return out
        keyed(self, out); p.parent.mkdir(exist_ok=True); S.save_json(p, out)
        return json.loads(p.read_text())

    def submit(self, body):
        if self.done():
            raise S.Done()
        refused = key_check(self, body)
        if refused:
            return refused
        return super().submit(unkeyed(body) if isinstance(body, dict) else body)


# ---- scoring: one replay setting, then the same book for the model and every yardstick
def load(session_id, tape=None):
    d = S.runs_dir() / session_id; meta = json.loads((d / "session.json").read_text()); assert meta.get("instrument") == "perp" and meta.get("tm06"), "not a TM06 session"
    res = json.loads((d / "result.json").read_text()); cfg = dict(res["config"], **meta["tm06"]["config"])
    tape = tape or W.session_tape(meta); table = W.price_table(tape, meta)
    assert [st["row"] for st in res["steps"]] == table["rows"], "the tape gives other prices than the session recorded: it was changed after the run"
    syms = W.priced(meta); pp = P.session_params(meta, cfg, tape); mins = P.perp_minutes(tape, pp["symbols"], parse(meta["wakes"][0]), parse(meta["end_utc"]))
    answers = [(st["asked"], st["exits"]) for st in res["steps"]]
    _, _, final = P.run_perp(meta, table, answers, pp, mins, cfg)
    assert round(final, 2) == round(res["final"]["value_usd"], 2), "the replay of the session's answers does not match the recorded final value"
    levels = list(cfg.get("tm_perp_fee_levels_bps") or P.p_config()["tm_perp_fee_levels_bps"])
    return dict(meta=meta, res=res, cfg=cfg, tape=tape, table=table, pp=pp, mins=mins, answers=answers, levels=levels, syms=syms)


def stats(cx, book, recs, final):
    st = P.p_stats(book, final, cx["cfg"]["tm_account_start_usd"]); span = ep(parse(cx["meta"]["end_utc"])) - ep(parse(cx["meta"]["wakes"][0]))
    st.update(trades=sum(len(r["trades"]) for r in recs) + st["exits_hit"], wakes_trading=sum(1 for r in recs if r["trades"]),
              time_in_market_share=book.get("held_seconds", 0) / span if span > 0 else 0.0, shortfall_usd=book["shortfall_usd"])
    return st


def run(cx, answers, pp, opening_cash=False):
    meta = dict(cx["meta"], opening={}) if opening_cash else cx["meta"]
    b, r, f = P.run_perp(meta, cx["table"], answers, pp, cx["mins"], cx["cfg"]); return stats(cx, b, r, f), b, f


def times(answers, m):
    return [(None if w is None else {s: v * m for s, v in w.items()}, ex) for w, ex in answers]


def hold(n, w):
    return [(dict(w), None)] + [(None, None)] * (n - 1)


def twin_block(name, runs, model_final, cfg):
    from timemachine import score_weights as SW
    return SW.twin_set(name, runs, model_final, cfg)  # keeps _draw_gains_pct for joining months and weeks; public() drops it


def public(x):
    """The score without its private draw lists (keys starting with _)."""
    if isinstance(x, dict):
        return {k: public(v) for k, v in x.items() if not k.startswith("_")}
    return [public(v) for v in x] if isinstance(x, list) else x


def swap_twin(swaps, lists, rng):
    """Yardstick (d), one draw: each day drop as many held names as the model dropped and add as many as it added, at random
    from that day's list. Gives the names held at each wake."""
    cur, out = [], []
    for k, sw in enumerate(swaps):
        gone = rng.sample(sorted(cur), min(sw["removed"], len(cur))); cur = [c for c in cur if c not in gone]
        pool = sorted(set(lists[k]) - set(cur) - set(gone)); cur = sorted(cur + rng.sample(pool, min(sw["added"], len(pool)))); out.append(list(cur))
    return out


def score_picker(session_id, tape=None, draws=None, seed=None):
    """Part P: the model and yardsticks (a) to (e) at each fee level."""
    cx = load(session_id, tape); cfg = cx["cfg"]; meta = cx["meta"]; tp = cx["tape"]; db = meta["tm06"]["attention_db"]; N = int(meta["tm06"]["max_names"])
    draws = int(draws if draws is not None else cfg["tm_weights_twin_draws"]); seed = int(seed if seed is not None else cfg["tm_weights_twin_seed"])
    wakes = [parse(w) for w in meta["wakes"]]; n = len(wakes); lists = [listed(tp, meta["symbols"], w, cfg) for w in wakes]
    eq = lambda names: {c: 1.0 / len(names) for c in names}
    named = [sorted(a[0]) if a[0] is not None else None for a in cx["answers"]]
    for k in range(n):
        if named[k] is None:
            named[k] = named[k - 1] if k else []
    mom, att = [], []
    for k, w in enumerate(wakes):
        r7 = {s: change_pct(tp, s, w, plan(cfg)["rise_hours"]) for s in lists[k]}; top = sorted((s for s in r7 if r7[s] is not None), key=lambda s: (-r7[s], s))[:N]
        mom.append((eq(top), None))
        ra = {s: attention_rise(s.split("/")[0], w, cfg, db) for s in lists[k]}; top = sorted((s for s in ra if ra[s] is not None), key=lambda s: (-ra[s], s))[:N]
        att.append((eq(top), None))
    swaps = [dict(added=len(set(named[k]) - set(named[k - 1] if k else [])), removed=len(set(named[k - 1] if k else []) - set(named[k]))) for k in range(n)]
    twins = [[(eq(c), None) for c in swap_twin(swaps, lists, random.Random(f"tm06_picker_twin:{seed}:{session_id}:{i}"))] for i in range(draws)]
    ys = dict(equal_all_held=hold(n, eq(lists[0])), top_7d_rise=mom, top_attention_rise=att, btc_held=hold(n, {"BTC/USD": 1.0}))
    out = dict(session=session_id, part="P", model=meta["model"], trader=meta["trader"], window=meta["window"], wakes=n, funding_source=cx["pp"]["source"],
               half_spread_bps={s: cx["pp"]["hs"][s] * 1e4 for s in cx["syms"]}, session_value_usd=cx["res"]["final"]["value_usd"], fee_levels_bps=cx["levels"],
               main_fee_bps=main_fee(cx), names_per_wake=[len(x) for x in named], swaps=swaps, list_size_per_wake=[len(x) for x in lists],
               attention_rule_left_out_per_wake=[len(lists[k]) - sum(1 for s in lists[k] if attention_rise(s.split("/")[0], wakes[k], cfg, db) is not None) for k in range(n)],
               twin_draws=draws, by_fee={})
    for f in cx["levels"]:
        pp = P.with_fee(cx["pp"], f); m, _, mf = run(cx, cx["answers"], pp); blk = dict(model=m, yardsticks={})
        for name, a in ys.items():
            y, _, yf = run(cx, a, pp, opening_cash=True); blk["yardsticks"][name] = dict(stats=y, model_above=mf > yf)
        tw = []
        for a in twins:
            _, b, tf = run(cx, a, pp, opening_cash=True); tw.append((b, tf))
        blk["random_swap_twins"] = twin_block("random_swap_twins", tw, mf, cfg)
        out["by_fee"][f"{f:g}"] = blk
    return out


def shuffle_answers(answers, trows, rng):
    """The session's own wake answers in a random order. Stops and targets keep their percent distance from the price at the
    wake they were given, applied from the price at the wake they land on."""
    order = list(range(len(answers))); rng.shuffle(order); out = []
    for k, j in enumerate(order):
        w, ex = answers[j]
        if ex:
            mj, mk = trows[j]["marks"], trows[k]["marks"]
            ex = {s: {x: v / mj[s] * mk[s] for x, v in e.items()} for s, e in ex.items() if mj.get(s) and mk.get(s)}
        out.append((w, ex))
    return out


def swing_runs(cx, answers, pp, mult, twins):
    meta = cx["meta"]; n = len(answers); g = plan(cx["cfg"])["swing_max_gross"]; syms = meta["symbols"]
    m, _, mf = run(cx, times(answers, mult), pp)
    blk = dict(model=m, yardsticks={})
    for name, a in ((f"equal_hold_{len(syms)}", hold(n, {s: g / len(syms) for s in syms})), (f"hold_long_{meta['benchmark']}", hold(n, {meta["benchmark"]: 1.0}))):
        y, _, yf = run(cx, times(a, mult), pp, opening_cash=True); blk["yardsticks"][name] = dict(stats=y, model_above=mf > yf)
    tw = []
    for a in twins:
        _, b, tf = run(cx, times(a, mult), pp); tw.append((b, tf))
    blk["shuffled_order_twins"] = twin_block("shuffled_order_twins", tw, mf, cx["cfg"])
    return blk


def score_swing(session_id, tape=None, draws=None, seed=None):
    """Part S: the model, equal hold of its coins, its own answers in shuffled order, hold long; at 1x and at each
    tm06_plan.carried_leverage (a replay and not a session), at each fee level."""
    cx = load(session_id, tape); cfg = cx["cfg"]; meta = cx["meta"]
    draws = int(draws if draws is not None else cfg["tm_weights_twin_draws"]); seed = int(seed if seed is not None else cfg["tm_weights_twin_seed"])
    twins = [shuffle_answers(cx["answers"], cx["table"]["rows"], random.Random(f"tm06_shuffle:{seed}:{session_id}:{i}")) for i in range(draws)]
    mults = [1] + [m for m in plan(cfg)["carried"] if m != 1]
    out = dict(session=session_id, part="S", model=meta["model"], trader=meta["trader"], window=meta["window"], wakes=len(cx["answers"]), symbols=meta["symbols"],
               funding_source=cx["pp"]["source"], half_spread_bps={s: cx["pp"]["hs"][s] * 1e4 for s in cx["syms"]}, session_value_usd=cx["res"]["final"]["value_usd"],
               fee_levels_bps=cx["levels"], main_fee_bps=main_fee(cx), multiples=mults, twin_draws=draws, by_multiple={})
    for m in mults:
        out["by_multiple"][f"{m:g}x"] = {f"{f:g}": swing_runs(cx, cx["answers"], P.with_fee(cx["pp"], f), m, twins) for f in cx["levels"]}
    return out


def score_control(session_id, tape=None):
    """The negative control: the rule's own answers at each leverage in tm06_plan.control_leverage and each fee level."""
    cx = load(session_id, tape); r = cx["cfg"]["tm06_reversal"]
    out = dict(session=session_id, part="C", rule=cx["meta"]["method"], window=cx["meta"]["window"], wakes=len(cx["answers"]), funding_source=cx["pp"]["source"],
               half_spread_bps={s: cx["pp"]["hs"][s] * 1e4 for s in cx["syms"]}, fee_levels_bps=cx["levels"], main_fee_bps=main_fee(cx),
               by_multiple={})
    for m in plan(cx["cfg"])["control_leverage"]:
        out["by_multiple"][f"{m:g}x"] = {f"{f:g}": run(cx, times(cx["answers"], m), P.with_fee(cx["pp"], f))[0] for f in cx["levels"]}
    hb = hold(len(cx["answers"]), {r["symbol"]: 1.0})
    out["hold_long"] = {f"{f:g}": run(cx, hb, P.with_fee(cx["pp"], f), opening_cash=True)[0] for f in cx["levels"]}
    return out


def score(session_id, tape=None, draws=None):
    part = json.loads((S.runs_dir() / session_id / "session.json").read_text())["tm06"]["part"]
    return score_picker(session_id, tape, draws) if part == "P" else score_swing(session_id, tape, draws) if part == "S" else score_control(session_id, tape)


# ---- hand-offs: one session answered by several agents in turn (plan line on splitting)
BRIEFS = ROOT / "timemachine" / "TM06_LAUNCH_BRIEFS.md"


def handoff_points(meta, cfg):
    """The 0-based wakes where a new agent takes over. Swing: every tm06_handoff_swing_wakes wakes, at the same UTC clock
    times every day (00:00 and 12:00 for 12 hourly wakes), the same for every model. Picker: the first wake on or after day tm06_handoff_picker_split_day of the month, when that splits the session
    (null: no split). Control and other sessions: none. The session's own snapshot of the keys wins over today's config."""
    c = dict(cfg, **(meta.get("tm06") or {}).get("config", {})); part = (meta.get("tm06") or {}).get("part"); wakes = [parse(w) for w in meta["wakes"]]
    if part == "S":
        n = int(c["tm06_handoff_swing_wakes"]); pts = list(range(n, len(wakes), n))
        assert (wakes[0].hour, wakes[0].minute) == (0, 0) and 1440 % (n * int(plan(c)["swing_minutes"])) == 0, "swing hand-offs would not fall at the same clock times every day"
        return pts
    if part == "P" and c.get("tm06_handoff_picker_split_day") is not None:
        d = int(c["tm06_handoff_picker_split_day"]); k = next((i for i, w in enumerate(wakes) if w.day >= d), None)
        return [k] if k else []
    return []


def handoffs_done(sid):
    f = S.runs_dir() / sid / "handoffs.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def next_wake(sid, cfg=None):
    """For a session: the next wake, whether it is a hand-off point, which agent answers it and that agent's steps."""
    d = S.runs_dir() / sid; meta = json.loads((d / "session.json").read_text()); prog = json.loads((d / "progress.json").read_text())
    pts = handoff_points(meta, cfg or full_config()); n = len(meta["wakes"]); k = int(prog["k"]); done = bool(prog.get("done")) or k >= n
    starts = [0] + pts; agent = sum(1 for p in starts if p <= min(k, n - 1)); first = starts[agent - 1]; last = (starts[agent] if agent < len(starts) else n) - 1
    rec = {h["k"]: h for h in handoffs_done(sid)}
    out = dict(session=sid, part=(meta.get("tm06") or {}).get("part"), model=meta.get("model"), method=meta.get("method"), wakes=n, done=done, handoff_steps=[p + 1 for p in pts],
               agents=len(starts), recorded=[rec[k_]["agent"] for k_ in sorted(rec)])
    if done:
        return out
    hand = k in pts
    out.update(next_step=k + 1, next_utc=meta["wakes"][k], agent=agent, first_step=first + 1, last_step=last + 1, is_handoff=hand,
               handoff_recorded=k in rec, notes_for_agent=rec[k]["frozen"] if k in rec else None,
               ran_past=[p + 1 for p in pts if p < k and p not in rec])
    return out


def handoff(sid, notes, cfg=None):
    """Records a hand-off at the session's next wake: freezes a copy of the earlier agent's notes in the session folder
    (handoffs/notes_for_agent_N.md, read-only) and adds one line to handoffs.jsonl. Only at a hand-off point, once."""
    nx = next_wake(sid, cfg); assert not nx["done"], f"{sid} is finished"
    assert nx["is_handoff"], f"step {nx['next_step']} is not a hand-off point (they are {nx['handoff_steps']})"
    assert not nx["handoff_recorded"], f"the hand-off at step {nx['next_step']} is already recorded"
    src = Path(notes); assert src.is_file(), f"no notes file at {src}"
    d = S.runs_dir() / sid / "handoffs"; d.mkdir(exist_ok=True); dst = d / f"notes_for_agent_{nx['agent']}.md"
    shutil.copyfile(src, dst); os.chmod(dst, 0o444)
    rec = dict(k=nx["next_step"] - 1, step=nx["next_step"], utc=nx["next_utc"], agent=nx["agent"], notes_from=str(src.resolve()), frozen=str(dst),
               sha256=hashlib.sha256(dst.read_bytes()).hexdigest(), made_utc=dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
    with open(S.runs_dir() / sid / "handoffs.jsonl", "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def brief_text(nx, port, notes_path):
    """The launcher brief for the next agent, its placeholders filled (TM06_LAUNCH_BRIEFS.md, the part's section)."""
    t = BRIEFS.read_text(); part = {"S": "swing", "P": "picker"}[nx["part"]]
    body = t.split(f"<!-- BRIEF {part} -->")[1].split("<!-- END -->")[0].strip()
    vals = dict(MODEL=nx["model"], METHOD_CARD=nx["method"], SESSION_ID=nx["session"], PORT=str(port), AGENT=str(nx["agent"]), AGENTS=str(nx["agents"]), FIRST_STEP=str(nx["first_step"]),
                LAST_STEP=str(nx["last_step"]), WAKES=str(nx["wakes"]), NOTES_PATH=notes_path, HANDOFF_NOTES_PATH=nx["notes_for_agent"] or "none (you are the first agent)",
                SCRATCH_DIR=str(Path(notes_path).parent / f"scratch_agent{nx['agent']}"), TAG=f"{nx['session']}_a{nx['agent']}")
    for k, v in vals.items():
        body = body.replace("{" + k + "}", v)
    return body


def main(argv=None):
    a = argparse.ArgumentParser(description="Plan TM06 sessions and scoring, on the fast tape. Pretend money only."); sub = a.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("picker"); sw = sub.add_parser("swing"); co = sub.add_parser("control"); sc = sub.add_parser("score")
    nx_ = sub.add_parser("next", help="the next wake of a session, whether it is a hand-off point, and which agent answers it")
    nx_.add_argument("session"); nx_.add_argument("--port", type=int, help="also print the filled launcher brief"); nx_.add_argument("--notes", help="with --port: the new agent's own notes file")
    ho = sub.add_parser("handoff", help="at a hand-off point: freeze the earlier agent's notes into the session and record the hand-off")
    ho.add_argument("session"); ho.add_argument("--notes", required=True, help="the earlier agent's notes file")
    for p in (pk, sw):
        p.add_argument("--trader", required=True); p.add_argument("--model", required=True); p.add_argument("--method", required=True)
    sw.add_argument("--symbols"); sw.add_argument("--week", type=int, help="1 to 4: dates and coins from tm06_plan.swing_weeks (168 hourly wakes)")
    pk.add_argument("--month", help="YYYY-MM: that month's dates, clipped to tm06_plan.picker_start and picker_end")
    for p in (pk, sw, co):
        p.add_argument("--from", dest="start"); p.add_argument("--to", dest="end"); p.add_argument("--session"); p.add_argument("--note")
    sc.add_argument("session"); sc.add_argument("--draws", type=int)
    x = a.parse_args(argv); stamp = dt.datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    if x.cmd == "next":
        nx = next_wake(x.session); print(json.dumps(nx, indent=1))
        if x.port and not nx["done"]:
            assert x.notes, "give --notes: the new agent's own notes file"
            assert not nx["is_handoff"] or nx["handoff_recorded"], "record the hand-off first: tm06.py handoff SESSION --notes EARLIER_NOTES"
            print("\n" + brief_text(nx, x.port, x.notes))
        return
    if x.cmd == "handoff":
        print(json.dumps(handoff(x.session, x.notes), indent=1)); return
    if x.cmd == "score":
        print(json.dumps(public(score(x.session, draws=x.draws)), indent=1, sort_keys=True)); return
    if x.cmd == "picker":
        if x.month:
            x.start, x.end = plan_month(x.month)
        assert x.start and x.end, "give --month or --from and --to"
        sid = x.session or f"TM06-P-{x.trader}-{x.month or x.start}"; create_picker(sid, x.trader, x.model, x.method, x.start, x.end, note=x.note)
    elif x.cmd == "swing":
        if x.week:
            x.start, x.end, syms = plan_week(x.week); pl = plan(full_config())
            want = (dt.date.fromisoformat(x.end) - dt.date.fromisoformat(x.start)).days * 1440 // pl["swing_minutes"] + 1440 // pl["swing_minutes"]
            got = len(W.make_wakes(W.fast_tape(), "crypto", x.start, x.end, [dict(every="minutes", step=pl["swing_minutes"])])[0])
            assert got == want, f"week {x.week} gives {got} wakes, not {want}"
        else:
            assert x.symbols and x.start and x.end, "give --week or --symbols, --from and --to"
            syms = [s.strip() for s in x.symbols.split(",") if s.strip()]
        sid = x.session or (f"TM06-S-{x.trader}-w{x.week}" if x.week else f"TM06-S-{x.trader}-{x.start}-{stamp}")
        create_swing(sid, x.trader, x.model, x.method, x.start, x.end, syms, note=x.note)
    else:
        assert x.start and x.end, "give --from and --to"
        sid = x.session or f"TM06-C-{x.start}-{stamp}"; create_control(sid, x.start, x.end, note=x.note); r = run_control(sid)
        print(json.dumps(dict(session=sid, wakes=len(r["steps"]), done=True), indent=1)); return
    meta = json.loads((S.runs_dir() / sid / "session.json").read_text())
    print(json.dumps(dict(session=sid, wakes=len(meta["wakes"]), first_wake=meta["wakes"][0], end_utc=meta["end_utc"]), indent=1))


if __name__ == "__main__":
    main()
