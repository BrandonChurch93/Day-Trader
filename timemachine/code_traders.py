"""Code traders: plain functions that trade a session through the same path an AI trader uses (packet in, pick out).
No model. Each returns fn(packet, look) -> a pick dict or {"no_pick": true, "why": "..."}.

hold(symbol)                  buys with all its cash at the first wake and never sells.
random_twin(result_json, seed)  replays an AI session's wakes. At each wake where the AI's buy was sent, it buys the same
                              dollars of a symbol drawn at random (seeded) from that day's stock universe (stock sessions)
                              or from the crypto list (crypto sessions). It sells after the AI's holding time for that
                              buy, and sets its stop and target the same distance in percent from its own price.
The twin reads prices only from the tape as of the packet's time. Standard library only."""
import datetime as dt, json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import picks
from timemachine.tape import Tape, NY

UTC = dt.timezone.utc


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def hold(symbol):
    def fn(packet, look):
        if packet["step"] == 1:
            return dict(thesis=f"Code trader hold: buy {symbol} with all the cash at the first wake and never sell.",
                        actions=[dict(symbol=symbol, side="buy", usd=packet["book"]["cash_usd"], reason="hold: buy once")])
        return {"no_pick": True, "why": "hold: never sells"}
    fn.label = f"hold({symbol})"
    return fn


def twin_plan(result, seed, tape):
    """What the twin will do at each wake, worked out in wake order so the same seed always gives the same plan.
    Returns {wake utc: [dict(ai_symbol, usd, stop_pct, target_pct, hold_seconds)]} and the draw function."""
    closed = result["summary"]["closed"]
    plan = {}
    for st in result["steps"]:
        p = st.get("pick") or {}
        sent = {r["n"] for r in st.get("outcome", []) if r.get("outcome") == "sent"}
        buys = []
        for n, a in enumerate(p.get("actions", [])):
            if a["side"] != "buy" or n not in sent:
                continue
            ref = st.get("ref_prices", {}).get(a["symbol"]); x = next((e for e in p.get("exits", []) if e["symbol"] == a["symbol"]), {})
            later = sorted((c for c in closed if c["symbol"] == a["symbol"] and c["opened_utc"] >= st["utc"]), key=lambda c: c["opened_utc"])
            hold_s = None
            if later:
                hold_s = (picks.parse_t(later[0]["closed_utc"]) - picks.parse_t(later[0]["opened_utc"])).total_seconds()
            elif "by_utc" in x:
                hold_s = (picks.parse_t(x["by_utc"]) - picks.parse_t(st["utc"])).total_seconds()
            buys.append(dict(ai_symbol=a["symbol"], usd=a["usd"], stop_pct=(x["stop"] / ref) if ("stop" in x and ref) else None,
                             target_pct=(x["target"] / ref) if ("target" in x and ref) else None, hold_seconds=hold_s))
        if buys:
            plan[st["utc"]] = buys
    return plan


def random_twin(result_json, seed, tape=None):
    result = json.loads(Path(result_json).read_text()) if not isinstance(result_json, dict) else result_json
    tape = tape or Tape(result["session"].get("tape")); market = result["session"]["market"]
    plan = twin_plan(result, seed, tape); rng = random.Random(f"twin:{seed}")

    def pool(t):
        if market == "stocks":
            return sorted(tape.universe(t.astimezone(NY).strftime("%Y-%m-%d")))
        return sorted(tape._crypto_symbols_as_of(int(t.timestamp())))

    def fn(packet, look):
        buys = plan.get(packet["utc"])
        if not buys:
            return {"no_pick": True, "why": "twin: the AI bought nothing at this wake"}
        now = picks.parse_t(packet["utc"]); choices = [s for s in pool(now) if picks.symbol_ok(s)]
        rng.shuffle(choices)  # one shuffle per buying wake, in wake order: the same seed gives the same draws
        snap = tape.snapshot(choices[:200], now); acts, exits = [], []
        for b in buys:
            sym = next((s for s in choices if s in snap and s not in {a["symbol"] for a in acts}), None)
            if sym is None:
                continue
            px = snap[sym]["price"]; acts.append(dict(symbol=sym, side="buy", usd=b["usd"], reason=f"random twin of a buy of {b['ai_symbol']}"))
            x = dict(symbol=sym)
            if b["stop_pct"]:
                x["stop"] = round(px * b["stop_pct"], 6)
            if b["target_pct"]:
                x["target"] = round(px * b["target_pct"], 6)
            if b["hold_seconds"] is not None:
                x["by_utc"] = iso(now + dt.timedelta(seconds=b["hold_seconds"]))
            if len(x) > 1:
                exits.append(x)
        if not acts:
            return {"no_pick": True, "why": "twin: no symbol with a price at this wake"}
        return dict(thesis=f"Random twin (seed {seed}) of session {result['session']['session']}.", actions=acts, exits=exits)
    fn.label = f"random_twin({result['session']['session']}, {seed})"
    return fn
