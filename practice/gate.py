"""The criteria gate: plain code between a scout's candidate and a pick. No model call anywhere in this file.

A scout (a cheap model, or a person) files a candidate: a symbol, the time of an event, the kind of event, a source link
and a line of facts. It never writes a price, a size, a target or a stop. The gate takes that candidate and one criteria
card (practice/criteria/*.json), fetches prices itself through a price source, recomputes every entry check from those
prices, and returns either a pick in the form of practice/picks.py or a refusal that names the check that failed. The
pick's size and exits come from the card and the prices, never from the scout. trader.py then places the pick and
enforces its exits like any other pick.

Every decision, accepted or refused, is appended to a decision log (one JSON line) with the card, its settings, the
candidate as filed and the bars the gate used, so "why did it buy" and "what did it turn down" can be answered later.

The same decide() runs live and against a past clock. It takes a `now` and a price source. It uses only bars that were
complete at `now` (bar start plus its length at or before `now`), whatever the source hands back, so a replay of past
candidates cannot see past its own clock. practice/test_gate.py proves this with made-up bars.

Every threshold lives once in config/thresholds.yaml; a card names the key. Standard library only.

  decide(candidate, card, now, prices, settings)          -> Decision (pick or refusal); pure, no writes
  gate(candidate, card, now, prices, settings, log_path)  -> the same, and appends one line to the decision log
  replay(candidates, card, prices, settings, log_path)    -> decide each candidate at its own filed time, oldest first
  simulate_exit(pick, card, prices, settings, until)      -> for replays: which exit a pick would have met, bar by bar
  process_inbox(inbox, cards, picks_dir, log, now, prices) -> the live path: read new candidates, gate them, write picks
"""
import datetime as dt, hashlib, json, math, re
from pathlib import Path

try:
    from . import picks
except ImportError:
    import picks

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = ROOT / "config" / "thresholds.yaml"
CRITERIA = Path(__file__).parent / "criteria"
UTC = dt.timezone.utc
TIMEFRAMES = {"1Min": dt.timedelta(minutes=1), "1Hour": dt.timedelta(hours=1), "1Day": dt.timedelta(days=1)}
CARD_TOP = {"id", "status", "registered", "tradable", "title", "trader", "ledger_row", "market", "candidate", "timeframe",
            "entry", "size", "exit", "costs", "pick_life_minutes"}
CANDIDATE_TOP = {"card", "symbol", "event", "event_utc", "filed_utc", "source", "facts", "scout"}
EVENT = re.compile(r"[a-z][a-z0-9_]{1,40}")
CAND_ID = re.compile(r"[0-9]{8}T[0-9]{6}Z-[a-z0-9-]{1,40}")
KEY = re.compile(r"practice_[a-z0-9_]+")


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(obj):
    raw = obj if isinstance(obj, bytes) else json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


# ------------------------------------------------------------------ settings and cards
def settings(path=THRESHOLDS):
    """Every plain-number value in config/thresholds.yaml, by key. Same line format trader.config() reads."""
    out, key = {}, None
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^([a-z0-9_]+):\s*$", line)
        if m:
            key = m.group(1); continue
        m = re.match(r"^  value:\s*(-?[0-9.]+(?:e-?[0-9]+)?)\s*$", line)
        if m and key:
            out[key] = float(m.group(1))
    return out


# Each entry check: its parameter names, and the number of complete bars it needs given its parameters.
CHECKS = {
    "enough_bars": (("bars",), lambda p: int(p["bars"])),
    "fell_at_least": (("lookback_bars", "min_fall"), lambda p: int(p["lookback_bars"]) + 1),
    "rose_at_least": (("lookback_bars", "min_rise"), lambda p: int(p["lookback_bars"]) + 1),
    "volume_above_mean": (("lookback_bars", "multiple"), lambda p: int(p["lookback_bars"]) + 1),
    "close_above_high": (("lookback_bars",), lambda p: int(p["lookback_bars"]) + 1),
    "close_above_mean": (("lookback_bars",), lambda p: int(p["lookback_bars"])),
}


def check_card(card, cfg):
    """Plain sentences; empty means the card fits the format and every key it names is in config/thresholds.yaml."""
    e = []
    if not isinstance(card, dict):
        return ["The card is not a JSON object."]
    if set(card) != CARD_TOP:
        e.append(f"The card must have exactly these fields: {sorted(CARD_TOP)}.")
        return e
    if not re.fullmatch(r"[A-Z0-9]{2,8}", str(card["id"])) or not re.fullmatch(r"[A-Z0-9-]{2,12}", str(card["trader"])):
        e.append("id must be 2 to 8 capitals or digits, trader 2 to 12 capitals, digits or dashes.")
    if card["tradable"] is True and (card["status"] == "EXAMPLE" or not card["registered"] or not card["ledger_row"]):
        e.append("A tradable card must be registered, not an EXAMPLE, and name its ledger row.")
    if card["status"] == "EXAMPLE" and (card["tradable"] is not False or card["registered"] is not False):
        e.append("An EXAMPLE card is never registered or tradable.")
    m = card["market"]
    if not (isinstance(m, dict) and m.get("kind") in ("crypto", "stock") and isinstance(m.get("symbols"), list) and m["symbols"]
            and all(picks.symbol_ok(s) and (("/" in s) == (m["kind"] == "crypto")) for s in m["symbols"])):
        e.append("market needs a kind of crypto or stock and a list of symbols of that kind.")
    c = card["candidate"]
    if not (isinstance(c, dict) and set(c) == {"events", "max_age_minutes"} and c["events"] and all(EVENT.fullmatch(x) for x in c["events"])):
        e.append("candidate needs a list of event kinds (lower case words) and a max_age_minutes key.")
    if card["timeframe"] not in TIMEFRAMES:
        e.append(f"timeframe must be one of {sorted(TIMEFRAMES)}.")
    keys = [c.get("max_age_minutes") if isinstance(c, dict) else None, card["pick_life_minutes"]]
    if not isinstance(card["entry"], list) or not card["entry"]:
        e.append("entry must be a list of named checks.")
    else:
        for i, ch in enumerate(card["entry"]):
            spec = CHECKS.get(ch.get("check")) if isinstance(ch, dict) else None
            if not spec or set(ch) != {"check", *spec[0]}:
                e.append(f"Entry check {i}: unknown check, or not exactly its parameters ({sorted(CHECKS)})."); continue
            keys += [ch[p] for p in spec[0]]
    if not (isinstance(card["size"], dict) and card["size"].get("rule") == "fixed_usd" and set(card["size"]) == {"rule", "usd"}):
        e.append("size must be {rule: fixed_usd, usd: <key>}; it is the only size rule so far.")
    else:
        keys.append(card["size"]["usd"])
    if not (isinstance(card["exit"], dict) and set(card["exit"]) <= {"target", "stop", "hold_minutes"} and card["exit"]):
        e.append("exit needs at least one of target, stop, hold_minutes.")
    else:
        keys += list(card["exit"].values())
    if not (isinstance(card["costs"], dict) and set(card["costs"]) == {"fee_bps_per_side", "slippage_bps_per_side"}):
        e.append("costs needs fee_bps_per_side and slippage_bps_per_side keys.")
    else:
        keys += list(card["costs"].values())
    for k in keys:
        if not (isinstance(k, str) and KEY.fullmatch(k) and k in cfg):
            e.append(f"The setting {k!r} is not a plain-number key in config/thresholds.yaml.")
    return e


def load_card(path, cfg):
    card = json.loads(Path(path).read_text())
    errs = check_card(card, cfg)
    if errs:
        raise ValueError(f"{Path(path).name}: " + " ".join(errs))
    return card


def cards(folder=CRITERIA, cfg=None):
    cfg = settings() if cfg is None else cfg
    return {c["id"]: c for c in (load_card(p, cfg) for p in sorted(Path(folder).glob("*.json")))}


# ------------------------------------------------------------------ candidates
def check_candidate(c, card=None, cand_id=None):
    """Plain sentences; empty means the candidate fits the form. The form has no field for a price, size, target or stop."""
    e = []
    if cand_id is not None and not CAND_ID.fullmatch(cand_id):
        e.append("The file name is not a candidate id like 20261126T153000Z-eth-drop.")
    if not isinstance(c, dict):
        return e + ["The candidate is not a JSON object."]
    if set(c) != CANDIDATE_TOP:
        extra, gone = sorted(set(c) - CANDIDATE_TOP), sorted(CANDIDATE_TOP - set(c))
        return e + [f"A candidate has exactly these fields: {sorted(CANDIDATE_TOP)}."
                    + (f" Not allowed: {extra}." if extra else "") + (f" Missing: {gone}." if gone else "")]
    if not picks.symbol_ok(c["symbol"]):
        e.append("symbol must look like NVDA or BTC/USD.")
    if not (isinstance(c["event"], str) and EVENT.fullmatch(c["event"])):
        e.append("event must be one lower-case word naming the kind of event.")
    try:
        ev, filed = picks.parse_t(c["event_utc"]), picks.parse_t(c["filed_utc"])
        if ev > filed:
            e.append("event_utc is after filed_utc.")
    except ValueError as x:
        e.append(f"event_utc or filed_utc: {x}.")
    if not (isinstance(c["source"], str) and re.fullmatch(r"https://[^\s]{4,490}", c["source"])):
        e.append("source must be one https link.")
    if not (isinstance(c["facts"], str) and 0 < len(c["facts"]) <= 1000):
        e.append("facts must be text, 1 to 1000 characters.")
    if not (isinstance(c["scout"], str) and 0 < len(c["scout"]) <= 80):
        e.append("scout must name who filed it, 1 to 80 characters.")
    if card is not None and c["card"] != card["id"]:
        e.append("The candidate names a different card.")
    return e


# ------------------------------------------------------------------ prices
class LivePrices:
    """Bars through the existing read-only market code (practice/market.py) and the broker's allow-listed GET."""
    def __init__(self, get):
        try:
            from . import market
        except ImportError:
            import market
        self.get, self.mk = get, market

    def bars(self, symbol, timeframe, start_utc):
        return self.mk._bars(self.get, symbol, timeframe, iso(start_utc), adjustment=None if "/" in symbol else "all")


class PastPrices:
    """Made-up or stored bars, {symbol: {timeframe: [bar, ...]}}. It hands back every bar it holds, later ones included:
    the gate itself drops anything not complete at its `now`, so the source does not need to be trusted."""
    def __init__(self, bars):
        self.data = bars

    def bars(self, symbol, timeframe, start_utc):
        return [dict(b) for b in self.data.get(symbol, {}).get(timeframe, [])]


def complete_bars(raw, timeframe, now):
    """The bars that had finished at `now`, oldest first, one per start time. Malformed bars are dropped."""
    span, seen = TIMEFRAMES[timeframe], {}
    for b in raw or ():
        try:
            t = picks.parse_t(b["t"])
            o, h, l, c, v = (float(b[k]) for k in "ohlcv")
        except (KeyError, TypeError, ValueError):
            continue
        if t + span <= now and all(math.isfinite(x) for x in (o, h, l, c, v)) and min(o, h, l, c) > 0 and v >= 0 and l <= min(o, c) and h >= max(o, c):
            seen[t] = dict(t=iso(t), o=o, h=h, l=l, c=c, v=v)
    return [seen[t] for t in sorted(seen)]


# ------------------------------------------------------------------ the checks, recomputed from bars
def run_check(name, p, bars):
    """(passed, what was measured). bars: complete bars, oldest first, at least as many as the check needs."""
    c, v = [b["c"] for b in bars], [b["v"] for b in bars]
    if name == "enough_bars":
        return len(bars) >= p["bars"], dict(bars=len(bars), needed=int(p["bars"]))
    if len(bars) < CHECKS[name][1](p):
        return False, dict(bars=len(bars), needed=CHECKS[name][1](p))
    n = int(p.get("lookback_bars", 0))
    if name == "fell_at_least":
        ch = c[-1] / c[-1 - n] - 1
        return ch <= -p["min_fall"], dict(change=round(ch, 6), from_close=c[-1 - n], to_close=c[-1])
    if name == "rose_at_least":
        ch = c[-1] / c[-1 - n] - 1
        return ch >= p["min_rise"], dict(change=round(ch, 6), from_close=c[-1 - n], to_close=c[-1])
    if name == "volume_above_mean":
        mean = sum(v[-1 - n:-1]) / n
        return mean > 0 and v[-1] >= p["multiple"] * mean, dict(volume=v[-1], mean_before=round(mean, 6), multiple=round(v[-1] / mean, 6) if mean > 0 else None)
    if name == "close_above_high":
        high = max(b["h"] for b in bars[-1 - n:-1])
        return c[-1] > high, dict(close=c[-1], high_before=high)
    if name == "close_above_mean":
        mean = sum(c[-n:]) / n
        return c[-1] > mean, dict(close=c[-1], mean=round(mean, 6))
    raise ValueError(f"unknown check {name}")


def resolve(card, cfg):
    """Every number the card points at, read from the settings once."""
    val = lambda k: cfg[k]
    return dict(
        max_age_minutes=val(card["candidate"]["max_age_minutes"]), pick_life_minutes=val(card["pick_life_minutes"]),
        entry=[dict(check=ch["check"], **{k: val(ch[k]) for k in CHECKS[ch["check"]][0]}) for ch in card["entry"]],
        usd=val(card["size"]["usd"]), exit={k: val(x) for k, x in card["exit"].items()},
        costs={k: val(x) for k, x in card["costs"].items()},
        keys=sorted({ch[k] for ch in card["entry"] for k in CHECKS[ch["check"]][0]} | set(card["exit"].values()) | set(card["costs"].values())
                    | {card["candidate"]["max_age_minutes"], card["pick_life_minutes"], card["size"]["usd"]}))


def needed_bars(r):
    return max(CHECKS[ch["check"]][1](ch) for ch in r["entry"])


def fetch_start(now, timeframe, n):
    span = TIMEFRAMES[timeframe]
    return now - span * (n * (2 if timeframe == "1Day" else 1) + 10)   # a hint to the source only; the gate never filters on it


# ------------------------------------------------------------------ the decision
class Decision(dict):
    @property
    def accepted(self): return self["outcome"] == "accepted"


def price_round(x):
    return float(f"{x:.6g}") if x < 1 else round(x, 4 if x < 100 else 2)


def decide(candidate, card, now, prices, cfg, cand_id=None, max_life_hours=None, max_actions=None):
    """One decision at `now`. Pure: reads prices through `prices`, writes nothing. Returns a Decision with outcome
    "accepted" (and the pick and its pick id) or "refused" (and the named criterion that failed)."""
    now = now.astimezone(UTC)
    r = resolve(card, cfg)
    base = dict(now_utc=iso(now), card=card["id"], card_sha256=sha(card), settings={k: cfg[k] for k in r["keys"]},
                candidate=candidate, candidate_id=cand_id, candidate_sha256=sha(candidate), checks=[], bars=None)

    def refuse(criterion, why, **more):
        return Decision(base, outcome="refused", criterion=criterion, why=why, **more)

    errs = check_candidate(candidate, card, cand_id)
    if errs:
        return refuse("candidate_form", " ".join(errs))
    if candidate["symbol"] not in card["market"]["symbols"]:
        return refuse("symbol_in_card", f"{candidate['symbol']} is not on card {card['id']}'s list.")
    if candidate["event"] not in card["candidate"]["events"]:
        return refuse("event_in_card", f"Card {card['id']} does not take {candidate['event']} events.")
    ev, filed = picks.parse_t(candidate["event_utc"]), picks.parse_t(candidate["filed_utc"])
    if filed > now:
        return refuse("filed_before_now", "The candidate was filed after the gate's clock.")
    age = (now - ev).total_seconds() / 60
    if age > r["max_age_minutes"]:
        return refuse("candidate_age", f"The event is {age:.0f} minutes old, over the card's {r['max_age_minutes']:g}.")
    tf, n = card["timeframe"], needed_bars(r)
    bars = complete_bars(prices.bars(candidate["symbol"], tf, fetch_start(now, tf, n)), tf, now)[-max(n, 1):]
    base["bars"] = dict(symbol=candidate["symbol"], timeframe=tf, n=len(bars), first=bars[0]["t"] if bars else None,
                        last=bars[-1]["t"] if bars else None, sha256=sha(bars), rows=bars)
    for ch in r["entry"]:
        p = {k: x for k, x in ch.items() if k != "check"}
        ok, measured = run_check(ch["check"], p, bars)
        base["checks"].append(dict(check=ch["check"], params=p, passed=ok, measured=measured))
        if not ok:
            return refuse(ch["check"], f"Entry check {ch['check']} failed: {json.dumps(measured, sort_keys=True)}.")
    ref = bars[-1]["c"]
    ex = r["exit"]
    exits = dict(symbol=candidate["symbol"])
    if "stop" in ex: exits["stop"] = price_round(ref * (1 - ex["stop"]))
    if "target" in ex: exits["target"] = price_round(ref * (1 + ex["target"]))
    if "hold_minutes" in ex: exits["by_utc"] = iso(now + dt.timedelta(minutes=ex["hold_minutes"]))
    made = now.replace(second=0, microsecond=0)
    pick_id = made.strftime("%Y%m%dT%H%MZ") + "-" + sha(candidate)[:8]
    pick = dict(trader=card["trader"], made_utc=iso(made), expires_utc=iso(made + dt.timedelta(minutes=r["pick_life_minutes"])),
                thesis=(f"Criteria gate, card {card['id']}. Candidate from {candidate['scout']}: {candidate['event']} on {candidate['symbol']} "
                        f"at {candidate['event_utc']}. Every entry check was recomputed from {len(bars)} complete {tf} bars and passed: "
                        + ", ".join(c["check"] for c in base["checks"]) + f". Reference close {ref:g} at {bars[-1]['t']}. "
                        f"Costs assumed {r['costs']['fee_bps_per_side']:g} bp fee and {r['costs']['slippage_bps_per_side']:g} bp slippage a side."),
                sources=[candidate["source"]],
                actions=[dict(symbol=candidate["symbol"], side="buy", usd=r["usd"], reason=f"Card {card['id']}, fixed size from the card.")],
                exits=[exits])
    life = max_life_hours if max_life_hours is not None else cfg.get("practice_pick_max_life_hours", 24)
    acts = max_actions if max_actions is not None else cfg.get("practice_pick_max_actions", 10)
    errs = picks.validate(pick, card["trader"], pick_id, now, life, acts)
    if errs:
        return refuse("pick_form", " ".join(errs))
    return Decision(base, outcome="accepted", criterion=None, why="Every entry check passed.", pick_id=pick_id, pick=pick, reference_close=ref)


def log(decision, path, mode):
    row = dict(decision, mode=mode, written_utc=iso(dt.datetime.now(UTC)))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def gate(candidate, card, now, prices, cfg, log_path, cand_id=None, mode="live"):
    d = decide(candidate, card, now, prices, cfg, cand_id=cand_id)
    log(d, log_path, mode)
    return d


def replay(candidates, card, prices, cfg, log_path, clock=None):
    """Decide each candidate at its own filed time (or clock(candidate)), oldest first, against a past price source.
    candidates: [(candidate id, candidate)]. Every decision goes to the log with mode "replay"."""
    when = clock or (lambda c: picks.parse_t(c["filed_utc"]))
    out = []
    for cid, c in sorted(candidates, key=lambda x: (when(x[1]), x[0])):
        out.append(gate(c, card, when(c), prices, cfg, log_path, cand_id=cid, mode="replay"))
    return out


def read_log(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def why(path, outcome=None, symbol=None):
    """Answers "why did it buy" and "what did it turn down": one plain line per logged decision."""
    out = []
    for r in read_log(path):
        if (outcome and r["outcome"] != outcome) or (symbol and (r["candidate"] or {}).get("symbol") != symbol):
            continue
        c = r["candidate"] if isinstance(r["candidate"], dict) else {}
        out.append(f"{r['now_utc']} {r['card']} {c.get('symbol', '?')} {c.get('event', '?')}: {r['outcome']}"
                   + (f", {r['criterion']}: {r['why']}" if r["outcome"] == "refused" else f", pick {r['pick_id']}"))
    return out


# ------------------------------------------------------------------ replay exits
def simulate_exit(pick, card, prices, cfg, until):
    """For a replay only. Walks the card's bars that finished after the pick was made and at or before `until`.
    Entry at the open of the first bar that starts at or after made_utc. In each later bar a stop is checked before a
    target (a bar that touched both counts as the stop), then the time limit at the bar's end. Costs from the card are
    charged on both sides. trader.py checks a live price about every ten minutes instead, so live fills will differ."""
    r = resolve(card, cfg)
    x, a = pick["exits"][0], pick["actions"][0]
    made, until = picks.parse_t(pick["made_utc"]), until.astimezone(UTC)
    tf, span = card["timeframe"], TIMEFRAMES[card["timeframe"]]
    bars = [b for b in complete_bars(prices.bars(a["symbol"], tf, made), tf, until) if picks.parse_t(b["t"]) >= made]
    if not bars:
        return dict(outcome="not_entered", why="No complete bar after the pick.")
    entry, t0 = bars[0]["o"], bars[0]["t"]
    cost = (r["costs"]["fee_bps_per_side"] + r["costs"]["slippage_bps_per_side"]) / 10000
    by = picks.parse_t(x["by_utc"]) if "by_utc" in x else None
    for b in bars:
        end = picks.parse_t(b["t"]) + span
        hit = ("stop", x["stop"]) if "stop" in x and b["l"] <= x["stop"] else ("target", x["target"]) if "target" in x and b["h"] >= x["target"] else \
              ("time", b["c"]) if by is not None and end >= by else None
        if hit:
            px = min(hit[1], b["o"]) if hit[0] == "stop" else max(hit[1], b["o"]) if hit[0] == "target" else hit[1]   # a gap through the level fills at the open
            net = (px * (1 - cost)) / (entry * (1 + cost)) - 1
            return dict(outcome=hit[0], entry_utc=t0, entry_price=entry, exit_utc=iso(end), exit_price=px, net_return=round(net, 8),
                        usd=a["usd"], net_usd=round(a["usd"] * net, 2))
    return dict(outcome="open", entry_utc=t0, entry_price=entry, why="No exit met by the end of the bars given.")


# ------------------------------------------------------------------ the inbox (live path)
def process_inbox(inbox, cards_by_id, picks_dir, log_path, now, prices, cfg):
    """Reads every candidate file inbox/<card id>/<candidate id>.json not yet in the decision log, validates it, gates it,
    and writes an accepted pick to picks_dir/picks/<trader>/<pick id>.json (the folder trader.py reads). A card that is not
    tradable never yields a pick here: its candidates are logged as refused. Returns the decisions made in this call."""
    seen = {(r["card"], r.get("candidate_id")) for r in read_log(log_path)}
    out = []
    for f in sorted(Path(inbox).glob("*/*.json")):
        card_id, cid = f.parent.name, f.stem
        if (card_id, cid) in seen:
            continue
        card = cards_by_id.get(card_id)
        try:
            cand = json.loads(f.read_text())
        except (OSError, ValueError):
            cand = None
        if card is None:
            d = Decision(now_utc=iso(now), card=card_id, candidate=cand, candidate_id=cid, candidate_sha256=sha(cand), checks=[], bars=None,
                         outcome="refused", criterion="card_known", why=f"No card {card_id} in practice/criteria.")
        elif cand is None:
            d = Decision(now_utc=iso(now), card=card_id, candidate=None, candidate_id=cid, candidate_sha256=None, checks=[], bars=None,
                         outcome="refused", criterion="candidate_form", why="The file is not JSON.")
        elif card["tradable"] is not True:
            d = Decision(now_utc=iso(now), card=card_id, card_sha256=sha(card), candidate=cand, candidate_id=cid, candidate_sha256=sha(cand),
                         checks=[], bars=None, outcome="refused", criterion="card_tradable", why=f"Card {card_id} is not tradable ({card['status']}).")
        else:
            d = decide(cand, card, now, prices, cfg, cand_id=cid)
        log(d, log_path, "live")
        if d.accepted:
            p = Path(picks_dir) / "picks" / card["trader"] / f"{d['pick_id']}.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                p.write_text(json.dumps(d["pick"], indent=1))
        out.append(d)
    return out


def validate_inbox(inbox, cards_by_id):
    """[(path, [problems])] for every candidate file in the inbox; an empty list of problems means it fits the form.
    Reads no prices and gates nothing."""
    out = []
    for f in sorted(Path(inbox).glob("*/*.json")):
        try:
            cand = json.loads(f.read_text())
        except (OSError, ValueError):
            out.append((str(f), ["The file is not JSON."])); continue
        card = cards_by_id.get(f.parent.name)
        errs = ([] if card else [f"No card {f.parent.name} in practice/criteria."]) + check_candidate(cand, card, f.stem)
        out.append((str(f), errs))
    return out


def main(argv):
    """python3 practice/gate.py check-inbox <folder>   lists each candidate file and whether it fits the form. No network."""
    if len(argv) != 3 or argv[1] != "check-inbox":
        print(main.__doc__); return 2
    bad = 0
    for path, errs in validate_inbox(argv[2], cards()):
        print(("ok      " if not errs else "refused ") + path + ("" if not errs else ": " + " ".join(errs)))
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
