"""Checks for the criteria gate (practice/gate.py), with made-up bars, a pretend broker and no network.
Run: python3 practice/test_gate.py"""
import copy, datetime as dt, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import broker as B, gate as G, picks, trader as T

UTC = dt.timezone.utc
N = [0]
def ok(cond, what):
    N[0] += 1
    if not cond:
        print("FAIL:", what); sys.exit(1)

CFG = G.settings()
CARDS = G.cards(cfg=CFG)
EX01, EX02 = CARDS["EX01"], CARDS["EX02"]
H = dt.timedelta(hours=1)
T0 = dt.datetime(2026, 11, 20, 0, 0, tzinfo=UTC)


def hourly(closes, vols, start=T0):
    """Made-up hourly bars. Open is the previous close, high and low bracket the bar."""
    out, prev = [], closes[0]
    for i, (c, v) in enumerate(zip(closes, vols)):
        out.append(dict(t=G.iso(start + i * H), o=prev, h=max(prev, c) * 1.001, l=min(prev, c) * 0.999, c=c, v=v)); prev = c
    return out


def drop_bars(last=95.0, last_vol=30.0):
    closes = [100.0] * 27 + [99.0, 97.0, last]
    return hourly(closes, [10.0] * 29 + [last_vol])


BARS = drop_bars()
NOW = T0 + 30 * H + dt.timedelta(minutes=5)          # 05 minutes after the 30th bar closed
def cand(**kw):
    c = dict(card="EX01", symbol="ETH/USD", event="sharp_drop", event_utc=G.iso(NOW - dt.timedelta(minutes=20)),
             filed_utc=G.iso(NOW - dt.timedelta(minutes=2)), source="https://example.test/notice/1",
             facts="ETH fell sharply in the last hour on an exchange notice.", scout="test scout")
    c.update(kw); return c
SRC = lambda bars, sym="ETH/USD", tf="1Hour": G.PastPrices({sym: {tf: bars}})

# ---- cards
ok(set(CARDS) == {"EX01", "EX02"} and all(c["status"] == "EXAMPLE" and c["tradable"] is False and c["registered"] is False for c in CARDS.values()),
   "the two cards are EXAMPLE, not registered, not tradable")
bad = copy.deepcopy(EX01); bad["size"]["usd"] = "practice_gate_no_such_key"
ok(any("no_such_key" in e for e in G.check_card(bad, CFG)), "a card naming a setting that is not in config/thresholds.yaml is refused")
bad = copy.deepcopy(EX01); bad["tradable"] = True
ok(G.check_card(bad, CFG), "an EXAMPLE card marked tradable is refused")
bad = copy.deepcopy(EX01); bad["entry"][1]["min_fall"] = 0.04
ok(G.check_card(bad, CFG), "a card cannot carry a number in place of a settings key")
bad = copy.deepcopy(EX01); bad["entry"].append(dict(check="ask_a_model"))
ok(G.check_card(bad, CFG), "a card cannot name a check the gate does not have")
r = G.resolve(EX01, CFG)
ok(r["usd"] == CFG["practice_gate_ex01_size_usd"] == 100 and r["exit"]["stop"] == CFG["practice_gate_ex01_stop"], "every number on a card is read from config/thresholds.yaml")

# ---- candidate form
ok(G.check_candidate(cand(), EX01, "20261121T060300Z-eth-drop") == [], "a well-formed candidate fits")
for extra in ("price", "target", "stop", "size", "usd"):
    ok(G.check_candidate(dict(cand(), **{extra: 1}), EX01), f"a candidate carrying {extra} is refused")
ok(G.check_candidate(cand(source="http://example.test/x"), EX01), "a source that is not https is refused")
ok(G.check_candidate(cand(event_utc="yesterday"), EX01), "a candidate with a bad time is refused")
ok(G.check_candidate(cand(event_utc=G.iso(NOW), filed_utc=G.iso(NOW - H)), EX01), "an event after its filing time is refused")
ok(G.check_candidate(cand(), EX01, "not an id"), "a candidate file name that is not an id is refused")
ok(G.check_candidate({k: v for k, v in cand().items() if k != "source"}, EX01), "a candidate with no source link is refused")

# ---- a long entry, accepted
d = G.decide(cand(), EX01, NOW, SRC(BARS), CFG, cand_id="20261121T060300Z-eth-drop")
ok(d.accepted and d["criterion"] is None, "a candidate that meets every check is accepted")
p = d["pick"]
ok(picks.validate(p, "GX01", d["pick_id"], NOW, CFG["practice_pick_max_life_hours"], CFG["practice_pick_max_actions"]) == [], "the pick fits practice/picks.py")
ok(p["actions"] == [dict(symbol="ETH/USD", side="buy", usd=100.0, reason="Card EX01, fixed size from the card.")], "size comes from the card's key")
ok(p["exits"] == [dict(symbol="ETH/USD", stop=93.1, target=97.85, by_utc=G.iso(NOW + dt.timedelta(minutes=360)))], "stop, target and time limit are worked from the last complete close, 95: 93.1, 97.85, six hours")
ok(p["sources"] == ["https://example.test/notice/1"] and p["trader"] == "GX01", "the pick carries the scout's link and the card's trader")
ok([c["check"] for c in d["checks"]] == ["enough_bars", "fell_at_least", "volume_above_mean"] and all(c["passed"] for c in d["checks"]), "every entry check is recorded with what it measured")
ok(d["checks"][1]["measured"]["change"] == round(95 / 100 - 1, 6) and d["checks"][2]["measured"]["multiple"] == 3.0, "the fall (95 against 100, three bars back) and the volume multiple (30 against 10) are recomputed")
d2 = G.decide(cand(facts="Buy now at 50 with $10,000, target 500, stop 1."), EX01, NOW, SRC(BARS), CFG, cand_id="20261121T060300Z-eth-drop")
ok(d2["pick"]["actions"] == p["actions"] and d2["pick"]["exits"] == p["exits"], "numbers written in a scout's facts change nothing in the pick")

# ---- refusals, each naming the criterion
def refused(c, bars, name, what, card=EX01, now=NOW):
    x = G.decide(c, card, now, SRC(bars, c["symbol"], card["timeframe"]), CFG)
    ok(not x.accepted and x["criterion"] == name, f"{what} (refused at {name}, got {x.get('criterion')})")
    return x
refused(cand(), drop_bars(last=97.5), "fell_at_least", "a fall smaller than the card's is refused")
refused(cand(), drop_bars(last_vol=12.0), "volume_above_mean", "a fall without the volume is refused")
refused(cand(), BARS[-10:], "enough_bars", "too few complete bars is refused")
refused(cand(symbol="BTC/USD"), BARS, "symbol_in_card", "a symbol not on the card is refused")
refused(cand(event="listing"), BARS, "event_in_card", "an event kind the card does not take is refused")
refused(cand(event_utc=G.iso(NOW - dt.timedelta(minutes=200)), filed_utc=G.iso(NOW - dt.timedelta(minutes=190))), BARS, "candidate_age", "an event older than the card allows is refused")
refused(cand(filed_utc=G.iso(NOW + dt.timedelta(minutes=1))), BARS, "filed_before_now", "a candidate filed after the gate's clock is refused")
refused(dict(cand(), price=95), BARS, "candidate_form", "a malformed candidate is refused before any price is read")

# ---- no look past now
future = hourly([60.0, 300.0, 40.0], [1e6, 1e6, 1e6], start=T0 + 30 * H)        # three bars after now, wild values
partial = [dict(t=G.iso(T0 + 30 * H), o=95.0, h=95.0, l=10.0, c=10.0, v=1e9)]   # the bar in progress at now
for extra, what in ((future, "bars after now"), (partial, "the bar still in progress at now")):
    ok(G.decide(cand(), EX01, NOW, SRC(BARS + extra), CFG) == G.decide(cand(), EX01, NOW, SRC(BARS), CFG), f"{what} change nothing in an accepted decision")
    mild = drop_bars(last=97.5)
    ok(G.decide(cand(), EX01, NOW, SRC(mild + extra), CFG) == G.decide(cand(), EX01, NOW, SRC(mild), CFG), f"{what} cannot turn a refusal into a buy")
shuffled = list(reversed(BARS + future)) + BARS[:5]
ok(G.decide(cand(), EX01, NOW, SRC(shuffled), CFG) == G.decide(cand(), EX01, NOW, SRC(BARS), CFG), "bars out of order or repeated give the same decision")
early = NOW - H                                                                  # one hour earlier, the last bar is not yet complete
de = G.decide(cand(event_utc=G.iso(early - dt.timedelta(minutes=10)), filed_utc=G.iso(early - dt.timedelta(minutes=5))), EX01, early, SRC(BARS), CFG)
ok(de["bars"]["last"] == BARS[-2]["t"] and de["criterion"] == "fell_at_least", "an hour earlier the gate sees only the bars complete then (last close 97, a 3% fall) and refuses")

# ---- the decision log and replay
tmp = Path(tempfile.mkdtemp()); logp = tmp / "decisions.jsonl"
cands = [("20261121T060300Z-eth-drop", cand()),
         ("20261121T050300Z-eth-early", cand(event_utc=G.iso(early - dt.timedelta(minutes=10)), filed_utc=G.iso(early - dt.timedelta(minutes=5)))),
         ("20261121T060400Z-sol", cand(symbol="SOL/USD"))]
out = G.replay(cands, EX01, G.PastPrices({"ETH/USD": {"1Hour": BARS + future}}), CFG, logp)
rows = G.read_log(logp)
ok([x["outcome"] for x in out] == ["refused", "accepted", "refused"] and len(rows) == 3 and all(r["mode"] == "replay" for r in rows), "a replay decides each candidate at its own filed time, oldest first, and logs every decision")
ok(rows[1]["bars"]["rows"] == BARS[-24:] and rows[1]["settings"]["practice_gate_ex01_min_fall"] == 0.04 and rows[1]["card_sha256"] == G.sha(EX01),
   "a logged decision holds the bars it used, the settings it read and the card's fingerprint")
ok(rows[2]["criterion"] == "enough_bars" and rows[2]["bars"]["n"] == 0, "a coin with no bars is refused and the log says so")
w = G.why(logp, outcome="refused")
ok(len(w) == 2 and "fell_at_least" in w[0] and len(G.why(logp, outcome="accepted")) == 1, "the log answers what it turned down and why it bought")

# ---- exits in a replay
def after(closes):
    return hourly(closes, [10.0] * len(closes), start=T0 + 31 * H)   # bars from the first full hour after the decision
pk = d["pick"]
future_src = lambda closes: G.PastPrices({"ETH/USD": {"1Hour": BARS + [dict(t=G.iso(T0 + 30 * H), o=95.0, h=95.2, l=94.9, c=95.0, v=10)] + after(closes)}})
s = G.simulate_exit(pk, EX01, future_src([96.0, 98.0, 99.0]), CFG, NOW + dt.timedelta(hours=12))
ok(s["outcome"] == "target" and s["exit_price"] == 97.85 and s["entry_utc"] == G.iso(T0 + 31 * H), "a rise past the target exits at the target")
cost = (25 + 5) / 10000
ok(abs(s["net_return"] - ((97.85 * (1 - cost)) / (s["entry_price"] * (1 + cost)) - 1)) < 1e-8, "the card's fee and slippage are charged on both sides")
s = G.simulate_exit(pk, EX01, future_src([94.0, 92.0]), CFG, NOW + dt.timedelta(hours=12))
ok(s["outcome"] == "stop" and s["exit_price"] == 93.1 and s["net_usd"] < 0, "a fall past the stop exits at the stop, a loss")
s = G.simulate_exit(pk, EX01, future_src([95.5, 90.0]), CFG, NOW + dt.timedelta(hours=12))
ok(s["outcome"] == "stop" and s["exit_price"] == 93.1, "a bar from 95.5 to 90 passes through the stop and exits at it")
gap = BARS + [dict(t=G.iso(T0 + 31 * H), o=95.0, h=95.1, l=94.9, c=95.0, v=10), dict(t=G.iso(T0 + 32 * H), o=90.0, h=99.0, l=89.0, c=91.0, v=10)]
s = G.simulate_exit(pk, EX01, G.PastPrices({"ETH/USD": {"1Hour": gap}}), CFG, NOW + dt.timedelta(hours=12))
ok(s["outcome"] == "stop" and s["exit_price"] == 90.0, "a gap below the stop fills at the open, and a bar that touched both counts as the stop")
s = G.simulate_exit(pk, EX01, future_src([95.5, 96.0, 95.0, 96.5, 95.8, 96.2, 95.9]), CFG, NOW + dt.timedelta(hours=12))
ok(s["outcome"] == "time" and s["exit_utc"] == G.iso(T0 + 37 * H) and s["exit_price"] == 96.2, "with neither level hit, it exits at the close of the bar that ends at or after the time limit")
ok(G.simulate_exit(pk, EX01, future_src([95.5, 96.0]), CFG, NOW + dt.timedelta(hours=3))["outcome"] == "open", "bars after the replay's end are not used")

# ---- a daily stock card
def daily(closes, highs=None, start=dt.datetime(2026, 10, 1, 5, tzinfo=UTC)):
    return [dict(t=G.iso(start + dt.timedelta(days=i)), o=c, h=(highs or closes)[i], l=c * 0.99, c=c, v=1000.0) for i, c in enumerate(closes)]
sn = dt.datetime(2026, 10, 23, 6, tzinfo=UTC)                         # 22 daily bars are complete
sc = dict(cand(card="EX02", symbol="ABC", event="earnings_beat"), event_utc=G.iso(sn - H), filed_utc=G.iso(sn - dt.timedelta(minutes=30)))
up = [50.0] * 21 + [55.0]
x = G.decide(sc, EX02, sn, SRC(daily(up), "ABC", "1Day"), CFG)
ok(x.accepted and x["pick"]["actions"][0]["usd"] == 200.0 and x["pick"]["exits"][0]["stop"] == 53.35 and x["pick"]["exits"][0]["target"] == 57.75, "a stock close above its 20-day high and its mean is accepted, with the card's size and exits")
refused(sc, daily([50.0] * 21 + [49.0]), "close_above_high", "a close that does not clear the 20-day high is refused", card=EX02, now=sn)

# ---- the pick goes through the existing hands: trader.py buys it and enforces its exits
class Fake:
    def __init__(self):
        self.list, self.held, self.px, self.now, self.submits = [], {}, {}, None, 0
    def has_key(self): return True
    def account(self): return dict(status="ACTIVE", crypto_status="ACTIVE", trading_blocked=False, account_blocked=False, currency="USD", cash="100000")
    def positions(self): return {k: dict(qty=q, available=q) for k, q in self.held.items()}
    def orders(self): return [dict(o) for o in self.list]
    def order_by_cid(self, cid): return next((dict(o) for o in self.list if o["client_order_id"] == cid), None)
    def submit(self, symbol, side, tif, cid, qty=None, notional=None):
        self.submits += 1; p = self.px[symbol]; q = round(qty if qty is not None else notional / p, 9)
        o = dict(id=f"{len(self.list):08d}-0000-0000-0000-000000000000", client_order_id=cid, symbol=symbol, side=side, asset_class="crypto",
                 status="filled", qty=None if qty is None else str(qty), notional=None if notional is None else str(notional),
                 filled_qty=str(q), filled_avg_price=str(p), submitted_at=T.iso(self.now), filled_at=T.iso(self.now))
        self.list.append(o); k = symbol.replace("/", ""); self.held[k] = round(self.held.get(k, 0) + (q if side == "buy" else -q), 12)
        if self.held[k] <= 1e-12: del self.held[k]
        return dict(o)
    def prices(self, symbols): return {s: dict(price=self.px[s], utc=T.iso(self.now)) for s in symbols if s in self.px}
    def daily_bars(self, symbol, start): return []
    def asset(self, symbol): return dict(symbol=symbol, tradable=True, fractionable=True)
    def clock(self): return dict(is_open=True)
    def calendar(self, first, last): return []
    def checkpoint(self): pass

def run(f, rec, pd, now):
    f.now = now
    r = T.Run(f, f, T.Records(rec), T.config(), [dict(id="GX01", name="Gate example", kind="ai", model="none", benchmark="ETH/USD")],
              picks_dir=pd, now=now, sleep=lambda s: None, checkpoint=f.checkpoint)
    r.run(); return json.loads((Path(rec) / "summary.json").read_text())

def placed(exit_px, minutes_later):
    f, rec, pd = Fake(), tempfile.mkdtemp(), Path(tempfile.mkdtemp())
    (pd / "picks" / "GX01").mkdir(parents=True); (pd / "picks" / "GX01" / f"{d['pick_id']}.json").write_text(json.dumps(p))
    f.px = {"ETH/USD": 95.0}; s = run(f, rec, pd, NOW)
    bought = f.submits == 1 and f.list[0]["side"] == "buy" and abs(float(f.list[0]["filled_qty"]) * 95.0 - 100.0) < 1e-6
    f.px = {"ETH/USD": exit_px}; s = run(f, rec, pd, NOW + dt.timedelta(minutes=minutes_later))
    return bought, f, s
b, f, s = placed(92.0, 20)
ok(b and f.submits == 2 and f.list[1]["side"] == "sell" and s["closed"][0]["result"] == "loss", "trader.py buys the gate's pick for the card's $100 and sells it at the card's stop")
b, f, s = placed(98.0, 20)
ok(b and f.submits == 2 and s["closed"][0]["result"] == "win", "trader.py sells it at the card's target")
b, f, s = placed(96.5, 361)
ok(b and f.submits == 2 and s["closed"][0]["result"] == "win", "trader.py sells it at the card's time limit")
b, f, s = placed(95.5, 20)
ok(b and f.submits == 1, "between the levels and before the time limit it holds")

# ---- the inbox
inbox, pd2, log2 = tmp / "inbox", tmp / "picks2", tmp / "inbox_decisions.jsonl"
(inbox / "EX01").mkdir(parents=True)
(inbox / "EX01" / "20261121T060300Z-eth-drop.json").write_text(json.dumps(cand()))
(inbox / "EX01" / "20261121T060301Z-eth-priced.json").write_text(json.dumps(dict(cand(), target=150)))
(inbox / "EX01" / "20261121T060302Z-broken.json").write_text("{not json")
(inbox / "ZZ99").mkdir(); (inbox / "ZZ99" / "20261121T060303Z-x.json").write_text(json.dumps(cand(card="ZZ99")))
v = dict((Path(a).name, e) for a, e in G.validate_inbox(inbox, CARDS))
ok(v["20261121T060300Z-eth-drop.json"] == [] and all(v[k] for k in v if k != "20261121T060300Z-eth-drop.json"), "the inbox check passes the good file and names the faults in the other three")
res = G.process_inbox(inbox, CARDS, pd2, log2, NOW, SRC(BARS), CFG)
ok(len(res) == 4 and all(not r.accepted for r in res) and not (pd2 / "picks").exists(), "an EXAMPLE card never yields a pick from the inbox")
ok(sorted(r["criterion"] for r in res) == ["candidate_form", "card_known", "card_tradable", "card_tradable"], "each inbox refusal is named: not tradable, unknown card, not JSON")
live = copy.deepcopy(CARDS); live["EX01"].update(status="TEST", registered=True, tradable=True, ledger_row="test only")
ok(G.check_card(live["EX01"], CFG) == [], "a registered card with a ledger row may be tradable")
log3 = tmp / "inbox3.jsonl"
res = G.process_inbox(inbox, live, pd2, log3, NOW, SRC(BARS), CFG)
wrote = list((pd2 / "picks" / "GX01").glob("*.json"))
ok([r["outcome"] for r in res].count("accepted") == 1 and len(wrote) == 1 and json.loads(wrote[0].read_text()) == p, "a tradable card's good candidate becomes one pick file where trader.py reads picks")
ok(next(r for r in res if r["candidate_id"] == "20261121T060301Z-eth-priced")["criterion"] == "candidate_form", "a candidate carrying a target is refused at the form")
ok(G.process_inbox(inbox, live, pd2, log3, NOW + dt.timedelta(minutes=10), SRC(BARS), CFG) == [] and len(G.read_log(log3)) == 4, "a candidate already decided is not decided again")

# ---- plain code only
src = Path(G.__file__).read_text()
ok(not any(w in src for w in ("urllib", "requests", "http.client", "socket", "anthropic", "openai", "subprocess")), "the gate opens no connection of its own and calls no model")
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()): code = G.main(["gate.py"])
ok(code == 2, "the command line prints its use when called wrongly")

print(f"{N[0]} checks passed")
