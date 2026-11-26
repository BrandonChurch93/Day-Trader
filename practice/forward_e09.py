"""E09 forward log: rule 70-102 (buy the coin that fell more than twice as far as bitcoin in a sharp bitcoin drop, hold two
hours) on live Coinbase prices, pretend money, with rules 71-013 and 71-035 shown beside it. No account, no login, no orders.

Card: practice/traders/E09_overextension_dip_buy.md (the card governs). Commands:
  plan      print the pinned rules, coins, contracts and costs (no network)
  start     write the private log header once: SHA-256 of the card, this logger and the imported plan 70 and 71 files,
            the freeze commit and the first wake (the first hourly open strictly after the start)
  record    record the current hourly wake if it is inside its window (10 seconds to 15 minutes after the open) and not
            yet recorded; on a signal or an exit it stays for the 1, 5 and 15 minute quotes. Earlier wakes that were never
            recorded are logged as void. Never back-fills
  loop      call record 10 seconds after every hourly open for as long as the process lives (one loop at a time)
  alive     counts only: wakes, void and late wakes, signals, trades, quote clocks and measured half-spreads. No profit
  publish   write the counts-only public log practice/forward/E09_log.json (same fields as alive)
  score     the lead's one read; refuses until 150 judged trades are complete or the last wake (2027-11-30 23:00 UTC) passed

The signals are the audited plan 70 code: research_rig/sweep_70.py score_signal and order_times on a six-hour Tape built
around each wake, with rule 70-102 of research_rig/GRID_70.json and rules 71-013 and 71-035 of research_rig/GRID_71.json
(both have no delay and one coin, so research_rig/sweep_71.py prices them through that same sweep_70 code).
Reads only these public pages, with no key, at most 2.5 requests a second; it backs off on 429 and stops on 401, 403 or 451:
  https://api.exchange.coinbase.com/products/{COIN}-USD/candles          hourly candles (signal and print lines)
  https://api.exchange.coinbase.com/products/{COIN}-USD/book?level=1     best spot bid and ask
  https://api.coinbase.com/api/v3/brokerage/market/product_book          best bid and ask of the US perpetual-style contract
Private records go to /home/user/workspace/rig/data/forward_e09 (0700 folder, 0600 files) as a hash-chained log.jsonl.
"""
import argparse, fcntl, json, math, os, subprocess, sys, time, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from statistics import median

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_rig"))
import sweep_70  # noqa: E402  (the audited plan 70 signal code)

CARD = "practice/traders/E09_overextension_dip_buy.md"
ME = "practice/forward_e09.py"
PINNED = (CARD, ME, "research_rig/sweep_70.py", "research_rig/coverage_70.py", "research_rig/GRID_70.json",
          "research_rig/sweep_71.py", "research_rig/GRID_71.json")
OFF = Path(os.environ.get("E09_RECORD_DIR", "/home/user/workspace/rig/data/forward_e09"))
PUBLIC = ROOT / "practice" / "forward" / "E09_log.json"
UTC = timezone.utc
HOUR = 3600
JUDGED = "70-102"
ARMS = ("70-102", "71-013", "71-035")      # the first is judged; the other two are shown only
# The 20 plan 70 coins. All 20 had an online USD spot pair in the public Coinbase Exchange product list read 2026-11-26.
COINS = sorted("AAVE ADA AVAX BCH BNB BTC DOGE DOT ETH HBAR LINK LTC NEAR PEPE SHIB SOL SUI XLM XRP ZEC".split())
# The matching US perpetual-style contract for each coin, from the public catalog
# https://api.coinbase.com/api/v3/brokerage/market/products?product_type=FUTURE&limit=250 read 2026-11-26 (doc 120, doc 153 c).
FUT = {"AAVE": "AVE", "ADA": "ADP", "AVAX": "AVP", "BCH": "BCP", "BNB": "BNB", "BTC": "BIP", "DOGE": "DOP", "DOT": "POP",
       "ETH": "ETP", "HBAR": "HEP", "LINK": "LNP", "LTC": "LCP", "NEAR": "NER", "PEPE": "PEP", "SHIB": "SHP", "SOL": "SLP",
       "SUI": "SUP", "XLM": "XLP", "XRP": "XPP", "ZEC": "ZEC"}
FUT = {c: f"{k}-20DEC30-CDE" for c, k in FUT.items()}
RECORD_AFTER_S = 10          # a wake is recorded no earlier than 10 seconds after the hourly open
WINDOW_S = 15 * 60           # and no later than 15 minutes after it; otherwise it is void
LATE_S = 120                 # a wake whose first quote is more than 120 seconds after the open is void for the judged line
FOLLOW_S = (60, 300, 900)    # the later quotes, seconds after the first quote
LAST_WAKE = datetime(2027, 11, 30, 23, 0, tzinfo=UTC)  # the stop date; no trade may exit after this wake
STOP_TRADES, MIN_TRADES = 150, 60
MARK_T, DROP_BEST = 2.0, 2
NOTIONAL_USD = 1000.0        # pretend dollars per trade, not compounded
CB = "https://api.exchange.coinbase.com/products/{}-USD"
CBF = "https://api.coinbase.com/api/v3/brokerage/market/product_book?product_id={}&limit=1"
MIN_GAP = 0.4


class Refuse(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refuse(why)


def rules():
    g70 = {r["id"]: r for r in json.loads((ROOT / "research_rig/GRID_70.json").read_bytes())}
    g71 = {r["id"]: r for r in json.loads((ROOT / "research_rig/GRID_71.json").read_bytes())}
    out = {"70-102": g70["70-102"], "71-013": g71["71-013"], "71-035": g71["71-035"]}
    want = {"70-102": (2, 2), "71-013": (1, 2), "71-035": (1, 1)}
    for k, r in out.items():
        need(r["family"] == "btc_overextension_fade" and r["side"] == 1 and not r["btc_hedge"]
             and r.get("delay_hours", 0) == 0 and r.get("top_coins", 1) == 1
             and r["parameters"] == {"lag": want[k][0], "threshold": 0.015, "multiple": 2.0} and r["hold_hours"] == want[k][1],
             f"rule {k} is not the frozen rule")
    return out


def settings():
    plan = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["replay_70_plan"]["value"]
    need(sorted(plan["futures_round_trip_bp"]) == COINS, "plan 70 cost table does not match the coin list")
    return dict(rules=rules(), arms=list(ARMS), judged=JUDGED, coins=COINS, futures=FUT,
                futures_route_round_trip_bp=plan["futures_round_trip_bp"], funding_bp_per_hour=plan["funding_adverse_bp_per_hour"],
                spot_taker_round_trip_bp=plan["spot_taker_round_trip_bp"], record_after_s=RECORD_AFTER_S, window_s=WINDOW_S,
                late_s=LATE_S, follow_s=list(FOLLOW_S), last_wake=iso(LAST_WAKE), stop_trades=STOP_TRADES,
                min_trades=MIN_TRADES, mark_t=MARK_T, drop_best=DROP_BEST, notional_usd=NOTIONAL_USD)


# ---- clocks
def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def floor_hour(t):
    return datetime.fromtimestamp(int(t.timestamp()) // HOUR * HOUR, UTC)


# ---- the public venue
class Coinbase:
    def __init__(self):
        self.last = 0.0

    def _get(self, url):
        for attempt in range(4):
            time.sleep(max(0.0, self.last + MIN_GAP - time.monotonic())); self.last = time.monotonic()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "e09-forward-log/1.0", "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    return json.loads(r.read(4 * 1024 * 1024))
            except urllib.error.HTTPError as e:
                need(e.code not in (401, 403, 451), f"venue refused with HTTP {e.code}")
                time.sleep(2 ** attempt * (5 if e.code == 429 else 1))
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                time.sleep(2 ** attempt)
        raise Refuse("venue did not answer")

    def candles(self, coin, start, end):
        rows = self._get(CB.format(coin) + f"/candles?granularity={HOUR}&start={iso(start)}&end={iso(end)}")
        return [(int(c[0]), float(c[3]), float(c[2]), float(c[1]), float(c[4]), float(c[5])) for c in rows]  # t, o, h, l, c, v

    def spot_book(self, coin):
        b = self._get(CB.format(coin) + "/book?level=1")
        return dict(bid=float(b["bids"][0][0]), ask=float(b["asks"][0][0]), venue_time=b.get("time"))

    def futures_book(self, code):
        b = self._get(CBF.format(code))["pricebook"]
        return dict(bid=float(b["bids"][0]["price"]), ask=float(b["asks"][0]["price"]), venue_time=b.get("time"))


def quote(fn, *a):
    """A best bid and ask, or None if the page refused, failed or showed a crossed or empty book."""
    try:
        q = fn(*a)
    except (Refuse, KeyError, IndexError, TypeError, ValueError):
        return None
    if not (q["bid"] > 0 and q["ask"] > q["bid"] and math.isfinite(q["ask"])):
        return None
    q["half_spread"] = (q["ask"] - q["bid"]) / (q["ask"] + q["bid"])
    return q


def snapshot(venue, coins, wake, clock, offset):
    """Spot and futures best bid and ask for each coin, with the seconds after the hourly open each was taken."""
    out = {}
    for c in sorted(coins):
        s = quote(venue.spot_book, c); s_at = (clock() - wake).total_seconds()
        f = quote(venue.futures_book, FUT[c]); f_at = (clock() - wake).total_seconds()
        if s:
            s["taken_s"] = round(s_at, 3)
        if f:
            f["taken_s"] = round(f_at, 3)
        out[c] = dict(spot=s, futures=f if f else "UNKNOWN")
    return dict(offset_s=offset, taken_s=round(min([q["spot"]["taken_s"] for q in out.values() if q["spot"]] or [math.inf]), 3)
                if any(q["spot"] for q in out.values()) else None, coins=out)


# ---- the signals (plan 70 code)
def decide(wake, bars, rule):
    """bars[coin] maps hourly open time to (o, h, l, c, v) for hours before the wake. Returns (coin, strength) or None.
    A six-hour Tape (three hours before the wake, the wake, and two hours after it) goes through sweep_70's own
    score_signal and order_times, so missing history, ranking, ties and the maintenance hour are the audited code's."""
    n = int(wake.timestamp())
    hours = np.arange(n - 3 * HOUR, n + 3 * HOUR, HOUR, dtype=np.int64)
    panel = np.full((len(COINS), len(hours), 5), np.nan)
    for j, c in enumerate(COINS):
        for k, t in enumerate(hours[:3]):
            if int(t) in bars.get(c, {}):
                panel[j, k] = bars[c][int(t)]
    tape = sweep_70.Tape(list(COINS), panel, hours=hours, split=None)
    signal = sweep_70.score_signal(tape, rule)
    signal[:, :3] = np.nan                    # earlier hours of the short tape were decided at their own wakes
    j, i = sweep_70.order_times(tape, rule, signal)
    if not len(i):
        return None
    need(int(i[0]) == 3, "signal outside the wake hour")
    return COINS[int(j[0])], float(signal[int(j[0]), 3])


# ---- the off-repo log
def enc(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)


def read_log(off=None):
    f = (off or OFF) / "log.jsonl"
    if not f.exists():
        return []
    out, prev = [], None
    for line in f.read_text().splitlines():
        x = json.loads(line)
        need(x["prev"] == prev, "log chain broken")
        prev = sha256(line.encode()).hexdigest(); out.append(x)
    return out


def append(x, off=None):
    off = off or OFF
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    need(off.stat().st_mode & 0o077 == 0, "log directory must be private")
    f = off / "log.jsonl"
    with open(off / ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        lines = f.read_text().splitlines() if f.exists() else []
        x["prev"] = sha256(lines[-1].encode()).hexdigest() if lines else None
        fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a") as out:
            out.write(enc(x) + "\n")
    return x


def file_sha(p):
    return sha256((ROOT / p).read_bytes()).hexdigest()


def start(now, off=None, commit=None):
    need(not read_log(off), "log already started")
    if commit is None:
        need(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", *PINNED, "config/thresholds.yaml"],
                            capture_output=True, text=True).stdout == "", "card, logger or plan files differ from the freeze commit")
        commit = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", CARD], capture_output=True, text=True,
                                check=True).stdout.strip()
    first = floor_hour(now) + timedelta(hours=1)
    need(first <= LAST_WAKE, "the stop date has passed")
    return append(dict(kind="header", card=CARD, sha256={p: file_sha(p) for p in PINNED}, freeze_commit=commit,
                       first_wake=iso(first), settings=settings(), made_utc=iso(now)), off)


def schedule(h, upto):
    """Hourly wakes from the first wake through min(upto, last wake), inclusive."""
    t, out = parse(h["first_wake"]), []
    while t <= min(upto, LAST_WAKE):
        out.append(t); t += timedelta(hours=1)
    return out


def state(log):
    """Each arm's open ticket, the set of logged wakes and the judged arm's count of judged-valid completed trades."""
    opens, done = {a: None for a in ARMS}, set()
    for x in log[1:]:
        if x["kind"] in ("wake", "void"):
            done.add(x["wake"])
        for e in x.get("exits", []):          # a line closes old tickets before it opens new ones
            opens[e["arm"]] = None
        for e in x.get("entries", []):
            opens[e["arm"]] = e
    return opens, done, len([t for t in trades(log) if t["arm"] == JUDGED and t["judged_ok"]])


def record(now, venue=None, off=None, clock=None, sleep=None):
    clock = clock or (lambda: datetime.now(UTC)); sleep = sleep or time.sleep
    log = read_log(off); need(log and log[0]["kind"] == "header", "log not started")
    h = log[0]
    need(all(file_sha(p) == h["sha256"][p] for p in PINNED), "card, logger or plan files changed since the start")
    st = h["settings"]
    need(settings() == st, "plan settings changed since the start")
    opens, done, judged_done = state(log)
    wake = floor_hour(now)
    live = wake + timedelta(seconds=RECORD_AFTER_S) <= now < wake + timedelta(seconds=WINDOW_S)
    # Every earlier wake with no line is void; an open ticket whose exit wake is among them is unresolved.
    for w in schedule(h, wake if live else now):
        if iso(w) in done or (live and w == wake) or now < w + timedelta(seconds=WINDOW_S):
            continue
        x = dict(kind="void", wake=iso(w), reason="missed wake, not recorded inside its window", made_utc=iso(now), exits=[])
        for a, e in opens.items():
            if e and e["exit_due"] == iso(w):
                x["exits"].append(dict(arm=a, coin=e["coin"], entry_wake=e["wake"], exit_wake=iso(w), status="unresolved",
                                       reason="exit wake missed"))
                opens[a] = None
        append(x, off); done.add(iso(w))
    if not live or iso(wake) in done or wake < parse(h["first_wake"]) or wake > LAST_WAKE:
        return None
    venue = venue or Coinbase()
    n = int(wake.timestamp())
    x = dict(kind="wake", wake=iso(wake), made_utc=iso(now), exits=[], entries=[], signals={}, busy=[])
    for a, e in opens.items():
        if e and e["exit_due"] == iso(wake):
            x["exits"].append(dict(arm=a, coin=e["coin"], entry_wake=e["wake"], exit_wake=iso(wake), status="complete"))
            opens[a] = None
    free = [a for a in ARMS if opens[a] is None]
    x["busy"] = [a for a in ARMS if opens[a] is not None]   # one position per arm; no signal is read while one is open
    closed = judged_done >= STOP_TRADES
    bars = {}
    if free and not closed:
        try:
            for c in COINS:
                rows = venue.candles(c, wake - timedelta(hours=3), wake)
                bars[c] = {r[0]: r[1:] for r in rows if n - 3 * HOUR <= r[0] <= n}
        except Refuse as e:
            x.update(kind="void", reason=f"candles: {e}"); bars = {}
    if bars:
        x["bars"] = {c: {str(t): list(v) for t, v in sorted(b.items())} for c, b in bars.items()}
        before = {c: {t: v for t, v in b.items() if t < n} for c, b in bars.items()}  # the signal sees closed bars only
        for a in free:
            rule = st["rules"][a]
            if wake + timedelta(hours=rule["hold_hours"]) > LAST_WAKE:
                continue
            pick = decide(wake, before, rule)
            x["signals"][a] = None if pick is None else dict(coin=pick[0], strength=pick[1])
            if pick:
                o = bars[pick[0]].get(n)
                x["entries"].append(dict(arm=a, coin=pick[0], wake=iso(wake), exit_due=iso(wake + timedelta(hours=rule["hold_hours"])),
                                         entry_open=o[0] if o else None))
    x["closed_to_entries"] = closed
    for e in x["exits"]:                       # the open print and hold bars, for the shown print line only
        try:
            rows = {r[0]: r for r in venue.candles(e["coin"], parse(e["entry_wake"]), wake)}
            e["exit_open"] = rows[n][1] if n in rows else None
            e["hold_bars_ok"] = all(t in rows for t in range(int(parse(e["entry_wake"]).timestamp()), n + 1, HOUR))
        except Refuse as r:
            e.update(exit_open=None, hold_bars_ok=False, reason=f"exit candles: {r}")
    coins = {e["coin"] for e in x["exits"] + x["entries"]}
    if coins:
        coins.add("BTC")
        x["quotes"] = [snapshot(venue, coins, wake, clock, 0)]
    x = append(x, off)
    if coins:                                  # the later quotes, each its own line, never back-filled
        t0 = wake + timedelta(seconds=x["quotes"][0]["taken_s"] or (clock() - wake).total_seconds())
        for k in FOLLOW_S:
            sleep(max(0.0, (t0 + timedelta(seconds=k) - clock()).total_seconds()))
            append(dict(kind="quotes", wake=iso(wake), made_utc=iso(clock()), quotes=snapshot(venue, coins, wake, clock, k)), off)
    return x


def trades(log):
    """One row per closed ticket with every quote recorded for it. A line is computed only where its quotes exist."""
    entries, quotes, rows = {}, {}, []
    for x in log[1:]:
        for q in ([x["quotes"]] if x["kind"] == "quotes" else x.get("quotes", [])):
            quotes.setdefault(x["wake"], {})[q["offset_s"]] = q
    for x in log[1:]:
        for e in x.get("entries", []):
            entries[(e["arm"], e["wake"])] = e
        for e in x.get("exits", []):
            en = entries.get((e["arm"], e["entry_wake"]), {})
            rows.append(dict(arm=e["arm"], coin=e["coin"], entry_wake=e["entry_wake"], exit_wake=e["exit_wake"], status=e["status"],
                             entry_open=en.get("entry_open"), exit_open=e.get("exit_open"), hold_bars_ok=e.get("hold_bars_ok", False),
                             entry_quotes=quotes.get(e["entry_wake"], {}), exit_quotes=quotes.get(e["exit_wake"], {})))
    for r in rows:
        q0, q1 = r["entry_quotes"].get(0), r["exit_quotes"].get(0)
        s0 = q0 and q0["coins"].get(r["coin"], {}).get("spot"); s1 = q1 and q1["coins"].get(r["coin"], {}).get("spot")
        r["judged_ok"] = bool(r["status"] == "complete" and s0 and s1 and s0["taken_s"] <= LATE_S and s1["taken_s"] <= LATE_S)
    return rows


def money(r, st):
    """Pretend net returns for one closed ticket. Line (a), judged for 70-102: buy at the spot ask quoted at the entry wake,
    sell at the spot bid quoted at the exit wake, less the plan 70 futures-route round trip and 1 bp an hour of the hold.
    Shown: the same at the 1, 5 and 15 minute quotes; the futures contract's own ask and bid at the wakes; the spot quotes
    with the US spot taker fee of doc 98; and the hourly open prints less the futures-route charge (the search's own line)."""
    hold = st["rules"][r["arm"]]["hold_hours"]
    fee = (st["futures_route_round_trip_bp"][r["coin"]] + hold * st["funding_bp_per_hour"]) / 1e4
    out = {}

    def leg(k, kind):
        a, b = r["entry_quotes"].get(k), r["exit_quotes"].get(k)
        qa = a and a["coins"].get(r["coin"], {}).get(kind); qb = b and b["coins"].get(r["coin"], {}).get(kind)
        return (qa["ask"], qb["bid"]) if isinstance(qa, dict) and isinstance(qb, dict) else None

    if r["status"] != "complete":
        return out
    p = leg(0, "spot")
    if p and r["judged_ok"]:
        out["a_spot_quotes_at_wake"] = p[1] / p[0] - 1 - fee
    if p:
        out["shown_spot_taker_fee"] = p[1] / p[0] - 1 - st["spot_taker_round_trip_bp"] / 1e4
    for k in FOLLOW_S:
        q = leg(k, "spot")
        if q:
            out[f"shown_spot_quotes_plus_{k // 60}m"] = q[1] / q[0] - 1 - fee
    f = leg(0, "futures")
    if f:
        out["shown_futures_quotes_at_wake"] = f[1] / f[0] - 1 - fee
    if r["entry_open"] and r["exit_open"] and r["hold_bars_ok"]:
        out["shown_open_prints"] = r["exit_open"] / r["entry_open"] - 1 - fee
    return out


def counts(now, off=None):
    """Counts, quote clocks and measured spreads only. No prices, no returns, no profit."""
    log = read_log(off)
    if not log:
        return dict(started=False)
    h = log[0]; lines = log[1:]
    closed = [w for w in schedule(h, now) if w + timedelta(seconds=WINDOW_S) <= now]
    by = {x["wake"]: x for x in lines if x["kind"] in ("wake", "void")}
    rows = trades(log)
    arm = {}
    for a in ARMS:
        mine = [r for r in rows if r["arm"] == a]
        arm[a] = dict(signals=sum(bool(x.get("signals", {}).get(a)) for x in lines),
                      trades_closed=len(mine), trades_complete=sum(r["status"] == "complete" for r in mine),
                      trades_unresolved=sum(r["status"] != "complete" for r in mine),
                      trades_judged_ok=sum(r["judged_ok"] for r in mine))
    snaps = [q for x in lines for q in ([x["quotes"]] if x["kind"] == "quotes" else x.get("quotes", []))]
    first = [q["taken_s"] for q in snaps if q["offset_s"] == 0 and q["taken_s"] is not None]
    spot_hs, fut_hs, fut_unknown = {}, {}, 0
    for q in snaps:
        if q["offset_s"]:
            continue
        for c, v in q["coins"].items():
            if v["spot"]:
                spot_hs.setdefault(c, []).append(v["spot"]["half_spread"] * 1e4)
            if isinstance(v["futures"], dict):
                fut_hs.setdefault(c, []).append(v["futures"]["half_spread"] * 1e4)
            else:
                fut_unknown += 1
    med = lambda d: {c: dict(quotes=len(v), median_half_spread_bp=round(median(v), 2)) for c, v in sorted(d.items())}
    return dict(started=True, first_wake=h["first_wake"], last_wake=iso(LAST_WAKE), wakes_closed=len(closed),
                recorded=sum(by.get(iso(w), {}).get("kind") == "wake" for w in closed),
                void_logged=sum(by.get(iso(w), {}).get("kind") == "void" for w in closed),
                void_not_yet_logged=sum(iso(w) not in by for w in closed),
                quote_snapshots={str(k): sum(q["offset_s"] == k for q in snaps) for k in (0, *FOLLOW_S)},
                first_quote_seconds_after_hour=dict(n=len(first), median=round(median(first), 1) if first else None,
                                                    max=round(max(first), 1) if first else None,
                                                    over_120=sum(s > LATE_S for s in first)),
                arms=arm, futures_quotes_unknown=fut_unknown,
                spot_half_spread_bp=med(spot_hs), futures_half_spread_bp=med(fut_hs),
                last_made_utc=lines[-1]["made_utc"] if lines else None)


def publish(now, off=None, path=PUBLIC):
    c = counts(now, off)
    log = read_log(off)
    c.update(card=CARD, header_line_sha256=sha256(enc(log[0]).encode()).hexdigest() if log else None, written_utc=iso(now))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(c, indent=1, sort_keys=True) + "\n")
    return c


def judge(rows, st, at_date):
    """rows: the judged arm's judged-valid trades in entry order, each with entry_wake and money. The card's marks on line (a)."""
    rows = rows[:STOP_TRADES]
    a = np.array([r["money"]["a_spot_quotes_at_wake"] for r in rows], dtype=float)
    day = np.array([int(parse(r["entry_wake"]).timestamp()) // 86400 for r in rows], dtype=np.int64)
    out = dict(trades=len(rows))
    if at_date and len(rows) < MIN_TRADES:
        out["verdict"] = "too few to judge"; return out
    day = day - day.min() if len(day) else day
    t = sweep_70.t_cluster(a, day) if len(a) else None
    kept = np.sort(a)[:-DROP_BEST] if len(a) > DROP_BEST else np.array([])
    marks = dict(mean_a_above_zero=bool(len(a) and a.mean() > 0), day_t_at_least_2=bool(t is not None and t >= MARK_T),
                 positive_without_best_2=bool(len(kept) and kept.mean() > 0))
    out.update(mean_a=float(a.mean()) if len(a) else None, day_t_a=t, mean_a_without_best_2=float(kept.mean()) if len(kept) else None,
               marks=marks, marks_met=sum(marks.values()), verdict="pass" if all(marks.values()) else "did not pass",
               pretend_usd_a=float(a.sum() * st["notional_usd"]), entry_days=int(np.unique(day).size))
    return out


def shown(rows, st):
    out = {}
    for r in rows:
        for k, v in r["money"].items():
            out.setdefault(k, []).append(v)
    return {k: dict(trades=len(v), mean=float(np.mean(v)), pretend_usd=float(np.sum(v) * st["notional_usd"])) for k, v in out.items()}


def score(now, off=None):
    log = read_log(off); need(log and log[0]["kind"] == "header", "log not started")
    st = log[0]["settings"]
    rows = trades(log)
    for r in rows:
        r["money"] = money(r, st)
    ok = [r for r in rows if r["arm"] == JUDGED and r["judged_ok"]]
    at_date = now >= LAST_WAKE + timedelta(seconds=WINDOW_S)
    need(len(ok) >= STOP_TRADES or at_date, "not yet: fewer than 150 judged trades and the stop date has not passed")
    out = dict(judged=judge(ok, st, at_date and len(ok) < STOP_TRADES))
    cut = parse(ok[STOP_TRADES - 1]["entry_wake"]) if len(ok) >= STOP_TRADES else LAST_WAKE
    for a in ARMS:
        mine = [r for r in rows if r["arm"] == a and parse(r["entry_wake"]) <= cut]
        out[a] = dict(closed=len(mine), unresolved=sum(r["status"] != "complete" for r in mine),
                      late_or_unquoted=sum(r["status"] == "complete" and not r["judged_ok"] for r in mine),
                      shown=shown([r for r in mine if r["status"] == "complete"], st))
    return out


def loop(off=None):
    off = off or OFF
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    lk = open(off / ".loop.lock", "w")
    try:
        fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise Refuse("another loop is running")
    while True:
        now = datetime.now(UTC)
        try:
            x = record(now)
            if x is not None:
                print(iso(now), x["kind"], x["wake"], flush=True)
        except Refuse as e:
            print(iso(now), "refused:", e, flush=True)
        if now > LAST_WAKE + timedelta(seconds=WINDOW_S):
            return
        nxt = floor_hour(datetime.now(UTC)) + timedelta(hours=1, seconds=RECORD_AFTER_S)
        time.sleep(max(1.0, (nxt - datetime.now(UTC)).total_seconds()))


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("command", choices=["plan", "start", "record", "loop", "alive", "publish", "score"])
    a = cli.parse_args(); now = lambda: datetime.now(UTC)
    try:
        if a.command == "plan":
            print(json.dumps(settings(), indent=1))
        elif a.command == "start":
            x = start(now()); print("started; first wake", x["first_wake"], "freeze", x["freeze_commit"])
        elif a.command == "record":
            x = record(now()); print("nothing due" if x is None else f"{x['kind']} {x['wake']}")
        elif a.command == "loop":
            loop()
        elif a.command == "alive":
            print(json.dumps(counts(now()), indent=1))
        elif a.command == "publish":
            publish(now()); print("wrote", PUBLIC.relative_to(ROOT))
        else:
            print(json.dumps(score(now()), indent=1))
    except Refuse as e:
        cli.exit(2, f"Refused: {e}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
