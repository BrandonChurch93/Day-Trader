"""Checks for the practice desk, with a pretend broker and no network. Run: python3 practice/test_trader.py
The timer runs this before every real run and does not trade if any check fails."""
import datetime as dt, json, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import books, broker as B, picks, rules, trader as T

UTC = dt.timezone.utc
N = [0]
def ok(cond, what):
    N[0] += 1
    if not cond:
        print("FAIL:", what); sys.exit(1)

class Fake:
    """Stands in for broker.Broker and for the price reads. It keeps an order list the way the broker does.
    mode: fill, reject, unclear_missing, unclear_exists, stay_open, part_cancel, bad_fill."""
    def __init__(self, key=True, mode="fill", is_open=True, held=None, coin_fee=0.0):
        self.key, self.mode, self.is_open, self.coin_fee = key, mode, is_open, coin_fee
        self.held = dict(held or {}); self.list = []; self.submits = 0; self.px = {}; self.crypto = []; self.stock = []; self.now = None
        self.quote_age_min = 0; self.assets = {}; self.sessions = None; self.cash = 100000.0; self.saves = 0; self.save_fails = False; self.saved_before = []
    # broker
    def has_key(self): return self.key
    def account(self): return dict(status="ACTIVE", crypto_status="ACTIVE", trading_blocked=False, account_blocked=False, currency="USD", cash=str(self.cash))
    def positions(self): return {k: dict(qty=q, available=q) for k, q in self.held.items()}
    def orders(self): return [dict(o) for o in self.list]
    def order_by_cid(self, cid): return next((dict(o) for o in self.list if o["client_order_id"] == cid), None)
    def make(self, symbol, side, cid, qty=None, notional=None, status="filled", frac=1.0, price=None):
        p = price or self.px[symbol]; q = round((qty if qty is not None else notional / p) * frac, 9);  # the broker counts to nine decimals
        filled = status in ("filled", "part") or frac < 1
        o = dict(id=f"{len(self.list):08d}-0000-0000-0000-000000000000", client_order_id=cid, symbol=symbol, side=side, asset_class="crypto" if "/" in symbol else "us_equity",
                 status="canceled" if status == "part" else status, qty=None if qty is None else str(qty), notional=None if notional is None else str(notional),
                 filled_qty=str(q if filled else 0), filled_avg_price=str(p) if filled else None, submitted_at=T.iso(self.now), filled_at=T.iso(self.now) if filled else None)
        self.list.append(o)
        if filled:
            k = symbol.replace("/", ""); got = round(q * (1 - self.coin_fee), 9) if (side == "buy" and "/" in symbol) else q
            self.held[k] = round(self.held.get(k, 0) + (got if side == "buy" else -q), 12)
            if self.held[k] <= 1e-12: del self.held[k]
        return dict(o)
    def submit(self, symbol, side, tif, cid, qty=None, notional=None):
        self.submits += 1; self.saved_before.append(self.saves)
        assert not any(o["client_order_id"] == cid for o in self.list), "the pretend broker was sent the same order name twice"
        if self.mode == "reject": raise B.Refused(422, "pretend refusal")
        if self.mode == "unclear_missing": raise B.Unclear("timeout")
        if self.mode == "unclear_exists": self.make(symbol, side, cid, qty, notional); raise B.Unclear("timeout")
        if self.mode == "stay_open": return self.make(symbol, side, cid, qty, notional, status="accepted")
        if self.mode == "part_cancel": return self.make(symbol, side, cid, qty, notional, status="part", frac=0.5)
        if self.mode == "bad_fill":
            o = self.make(symbol, side, cid, qty, notional); self.list[-1]["filled_avg_price"] = None; return o
        return self.make(symbol, side, cid, qty, notional)
    # prices
    def prices(self, symbols): return {s: dict(price=self.px[s], utc=T.iso(self.now - dt.timedelta(minutes=self.quote_age_min))) for s in symbols if s in self.px}
    def daily_bars(self, symbol, start): return self.crypto if "/" in symbol else self.stock
    def asset(self, symbol): return self.assets.get(symbol, dict(symbol=symbol, tradable=True, fractionable=True))
    def clock(self): return dict(is_open=self.is_open)
    def calendar(self, first, last): return self.sessions if self.sessions is not None else [dict(date=b["t"][:10]) for b in self.stock]
    # saving
    def checkpoint(self):
        if self.save_fails: raise RuntimeError("push failed")
        self.saves += 1

def crypto_bars(closes, now):
    """Finished daily bars ending at the last midnight before now, plus today's unfinished bar at the last close."""
    last = now.replace(hour=0, minute=0, second=0, microsecond=0)
    out = [dict(t=T.iso(last - dt.timedelta(days=len(closes) - i)), c=c) for i, c in enumerate(closes)]
    return out + [dict(t=T.iso(last), c=closes[-1])]

def stock_bars(month_ends, now, today):
    """One bar late in each earlier month (the pretend calendar says it is that month's last trading day), then one bar for today."""
    y, m = now.year, now.month; out = []
    for c in reversed(month_ends):
        m -= 1
        if m == 0: y, m = y - 1, 12
        out.append(dict(t=f"{y}-{m:02d}-28T05:00:00Z", c=c))
    return list(reversed(out)) + [dict(t=now.strftime("%Y-%m-%dT05:00:00Z"), c=today)]

RULES = T.roster()[:2]
AI = [dict(id="A01", name="Pretend AI trader", kind="ai", model="none", benchmark="VTI"), dict(id="A02", name="Second pretend AI trader", kind="ai", model="none", benchmark="BTC/USD")]

def go(fake, rec_dir, now, cfg=None, traders=RULES, picks_dir=None, save=True, clear=None):
    fake.now = now
    r = T.Run(fake, fake, T.Records(rec_dir), cfg or T.config(), traders, picks_dir=picks_dir, now=now, sleep=lambda s: None, checkpoint=fake.checkpoint if save else None, clear=clear)
    code = r.run(); return code, json.loads((Path(rec_dir) / "summary.json").read_text()), r

def tr(s, tid): return next(t for t in s["traders"] if t["id"] == tid)
def qty(t, sym): return next((p["qty"] for p in t["positions"] if p["symbol"] == sym), 0.0)

def setup(mode="fill", is_open=False, **kw):
    f = Fake(mode=mode, is_open=is_open, **kw); f.crypto = crypto_bars(up, now); f.px = {"BTC/USD": 101.0, "VTI": 10.0}; f.stock = stock_bars(list(range(1, 11)), now, 10.0)
    return tempfile.mkdtemp(), f

# ---- the rules, worked by hand
ok(rules.p1_weight([100] * 199 + [101]) == 1.0, "P1 above all four averages")
ok(rules.p1_weight([100] * 199 + [99]) == 0.0, "P1 below all four averages")
ok(rules.p1_weight([200] * 180 + [100] * 19 + [101]) == 0.25, "P1 above the 20 day average only: 101 > 100.05, and below 160.02, 180.01 and 190.005")
ok(rules.p1_weight([100] * 199) is None, "P1 needs 200 days")
ok(rules.t1_weight(list(range(1, 11))) == 1.0 and rules.t1_weight(list(range(10, 0, -1))) == 0.0, "T1 against the ten-month average: 10 > 5.5, 1 < 5.5")
ok(rules.t1_weight([5] * 10) == 0.0, "T1 equal to its average is out, as in the replay (strictly above)")
ok(rules.t1_weight([1] * 9) is None, "T1 needs ten months")
ok(rules.month_end_closes([("2026-09-29", 1), ("2026-09-30", 2), ("2026-10-30", 3), ("2026-11-02", 4)], "2026-11") == ([2, 3], "2026-10"), "month ends leave out the month in progress")

# ---- the broker layer can only do what is on its list
ok(B.allowed("POST", B.PAPER, "/v2/orders") and B.allowed("GET", B.PAPER, "/v2/positions") and B.allowed("GET", B.PAPER, "/v2/orders"), "send one order, read positions and read orders are allowed")
for m, base, path in [("DELETE", B.PAPER, "/v2/orders"), ("DELETE", B.PAPER, "/v2/positions"), ("DELETE", B.PAPER, "/v2/orders/00000000-0000-0000-0000-000000000000"),
                      ("PATCH", B.PAPER, "/v2/account/configurations"), ("POST", "https://api.alpaca.markets", "/v2/orders"), ("GET", "https://api.alpaca.markets", "/v2/account"),
                      ("POST", B.PAPER, "/v2/orders/x"), ("PATCH", B.PAPER, "/v2/orders/00000000-0000-0000-0000-000000000000"), ("POST", B.DATA, "/v2/stocks/bars"),
                      ("GET", "https://example.com", "/v2/account")]:
    ok(not B.allowed(m, base, path, [(B.DATA, r"/v2/stocks/bars")]), f"not allowed: {m} {base}{path}")
for call in [("DELETE", B.PAPER, "/v2/positions"), ("POST", B.DATA, "/v2/stocks/bars")]:
    try:
        B.Broker("k", "s")._call(*call); ok(False, "a call that is not on the list must be refused before any network use")
    except PermissionError:
        ok(True, "")
ok(B._NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://example.com/") is None, "a redirect is never followed, so the key cannot be sent to another address")
ok("SECRETKEY123" not in B.clean('{"message": "bad key SECRETKEY123 <script>"}', ("SECRETKEY123",)) and "<" not in B.clean('{"message": "a <b>"}'), "broker text is cleaned and the key is removed before it is written down")
ok(B.clean("not json SECRET") == "", "broker text that is not the expected form is dropped whole")
src = "".join((Path(__file__).parent / n).read_text() for n in ("broker.py", "trader.py", "books.py", "picks.py", "rules.py"))
ok("api.alpaca.markets" not in src.replace("paper-api.alpaca.markets", ""), "the real-money address is nowhere in the program")
ok(all(w not in src.lower() for w in ("openai", "anthropic", "perplexity.ai", "requests.post", "delete")), "no model or chat service is called, and no request that removes anything exists")

cfg = T.config(); START = cfg["practice_amount_per_trader_usd"]; FEE = cfg["practice_crypto_fee_bps_added"] / 1e4
ok(START == 1000 and FEE == 0.0025 and cfg["practice_crypto_fee_in_coin"] == 0, "set-up: the hand-worked numbers below assume 1,000 pretend dollars per trader and a 25 basis point fee added in dollars")
now = dt.datetime(2026, 11, 25, 15, 17, tzinfo=UTC); t2 = now + dt.timedelta(days=1)
up, down = [100] * 199 + [101], [100] * 199 + [99]

# ---- times in every form the broker may write them
ok(picks.parse_t("2026-11-24T05:00:00Z") == picks.parse_t("2026-11-24T00:00:00.123456789-05:00").replace(microsecond=0) == dt.datetime(2026, 11, 24, 5, tzinfo=UTC), "Z, an offset and nanoseconds all read as the same moment")

# ---- no key: nothing is sent, and the screen says so
d = tempfile.mkdtemp(); f = Fake(key=False); code, s, _ = go(f, d, now)
ok(code == 0 and s["status"] == "waiting_for_key" and f.submits == 0 and s["orders"] == [] and s["account"]["value_usd"] == 2 * START, "no key means no orders")

# ---- first run: both rules want in, each sends one order, and the records are saved before each one goes
d, f = setup(is_open=True); code, s, _ = go(f, d, now)
ok(code == 0 and f.submits == 2 and s["status"] == "running" and s["totals"]["orders"] == 2, "first run sends one order per rule")
ok(f.saved_before == [1, 2], "the records were saved to the branch before each order was sent")
btc, vti = tr(s, "P1-BTC"), tr(s, "T1-VTI")
# by hand: 1000 / 1.0025 = 997.506..., cut to cents 997.50. Bought 997.50 / 101 = 9.876237623... bitcoin. Fee 997.50 * 0.0025 = 2.49375. Cash left 1000 - 997.50 - 2.49375 = 0.00625.
ok(abs(qty(btc, "BTC/USD") - 9.8762376238) < 1e-9 and abs(btc["cash_usd"] - 0.01) < 0.006 and abs(btc["fees_added_usd"] - 2.49) < 0.006, "bitcoin order size, fee and cash left, worked by hand")
ok(abs(btc["value_usd"] - 997.51) < 0.006 and abs(btc["gain_usd"] + 2.49) < 0.006, "the bitcoin rule is down by the fee it paid, and nothing else")
ok(abs(qty(vti, "VTI") - 100.0) < 1e-9 and abs(vti["cash_usd"]) < 0.006 and all(o["gap_bps"] == 0.0 for o in s["orders"]), "fund order size, and a zero gap when the fill is at the price read")
code, s2, _ = go(f, d, now + dt.timedelta(hours=1))
ok(f.submits == 2 and s2["totals"]["orders"] == 2, "the same price day never sends a second order")

# ---- every record lost: the books are the same, because they come from the broker, and nothing is sent again
shutil.rmtree(d); d = tempfile.mkdtemp(); code, s3, _ = go(f, d, now + dt.timedelta(hours=2))
ok(f.submits == 2 and abs(qty(tr(s3, "P1-BTC"), "BTC/USD") - 9.8762376238) < 1e-9 and tr(s3, "T1-VTI")["cash_usd"] == vti["cash_usd"] and code == 0, "losing every record changes no holding and sends no order")

# ---- next day the bitcoin rule wants out at a higher price: one sell, one closed trade, a win, counted once
f.crypto = crypto_bars(up[1:] + [50.0], t2); f.px["BTC/USD"] = 110.0
ok(rules.p1_weight(up[1:] + [50.0]) == 0.0, "set-up: the rule wants out")
code, s, _ = go(f, d, t2); btc = tr(s, "P1-BTC")
# by hand: sold 9.876237623 at 110 = 1086.386139. Fee 2.715965. Back 1083.670173. Cost was 997.50 + 2.49375 = 999.99375. Gain 83.676423.
ok(f.submits == 3 and btc["positions"] == [] and s["totals"]["closed_trades"] == 1 and s["totals"]["wins"] == 1 and s["totals"]["losses"] == 0, "a sell to nothing closes one trade and counts a win")
ok(abs(s["closed"][0]["gain_usd"] - 83.68) < 0.006 and abs(btc["gain_usd"] - 83.68) < 0.006 and s["totals"]["win_rate"] == 1.0, "the win is the right size, fees on both sides included, worked by hand")
ok("BTCUSD" not in f.held, "the pretend broker holds no bitcoin after the sell")
for i in range(3):
    code, s, _ = go(f, d, t2 + dt.timedelta(hours=1 + i))
ok(s["totals"]["closed_trades"] == 1 and s["totals"]["wins"] == 1 and abs(s["totals"]["realised_usd"] - 83.68) < 0.006 and f.submits == 3, "running again and again never counts the same win twice")
ok(len(s["points"]) >= 2, "the value over time is written down")

# ---- a loss is counted as a loss
d, f = setup(); go(f, d, now)
f.crypto = crypto_bars(up[1:] + [50.0], t2); f.px["BTC/USD"] = 50.0; code, s, _ = go(f, d, t2)
ok(s["totals"]["losses"] == 1 and s["totals"]["wins"] == 0 and s["closed"][0]["result"] == "loss" and s["closed"][0]["gain_usd"] < 0, "a sell lower than the buy counts a loss")
ok(f.submits == 2 and tr(s, "T1-VTI")["positions"] == [], "no fund order while the stock market is closed")
f.is_open = True; code, s, _ = go(f, d, t2 + dt.timedelta(hours=1))
ok(f.submits == 3 and qty(tr(s, "T1-VTI"), "VTI") == 100.0, "the fund order goes once the market is open")

# ---- an unclear answer and no order at the broker: the trader stops, the run ends with an error, nothing is sent again
d, f = setup("unclear_missing"); code, s, _ = go(f, d, now); btc = tr(s, "P1-BTC")
ok(code == 1 and btc["halted"] and s["status"] == "halted" and f.submits == 1 and s["orders"][0]["status"] == "unclear", "an unclear order result stops the trader (AGENTS.md, What the order program always does)")
f.mode = "fill"; f.crypto = crypto_bars(up[1:] + [102], t2); code, s, _ = go(f, d, t2)
ok(f.submits == 1 and code == 0 and tr(s, "P1-BTC")["halted"], "a stopped trader sends nothing on later runs, and the error is raised once")
(Path(d) / "state.json").unlink(); code, s, _ = go(f, d, t2 + dt.timedelta(hours=1))
ok(f.submits == 1 and tr(s, "P1-BTC")["halted"], "the stop survives losing the state file, because it is read from the journal")
code, s, _ = go(f, d, t2 + dt.timedelta(hours=2), clear="P1-BTC")
ok(f.submits == 2 and not tr(s, "P1-BTC")["halted"] and qty(tr(s, "P1-BTC"), "BTC/USD") > 0, "after it is cleared by hand the trader trades again")

# ---- an unclear answer but the order is at the broker: it is found by its fixed name and counted, not sent again
d, f = setup("unclear_exists"); code, s, _ = go(f, d, now); btc = tr(s, "P1-BTC")
ok(code == 0 and f.submits == 1 and not btc["halted"] and abs(qty(btc, "BTC/USD") - 9.8762376238) < 1e-9, "an order that did arrive is found and counted once")

# ---- the run died right after writing down that it was about to send. Case one: the order never left
d, f = setup(); rec = T.Records(d); cid = books.cid_for("P1-BTC", "20261124T0000")
rec.add("orders", dict(utc=T.iso(now), event="sending", trader="P1-BTC", symbol="BTC/USD", cid=cid, side="buy", qty=None, usd=997.5, assumed_price=101.0, reason="x"))
code, s, _ = go(f, d, now + dt.timedelta(hours=1))
ok(code == 1 and f.submits == 0 and tr(s, "P1-BTC")["halted"], "an intent with no order at the broker is unclear: the trader stops and nothing is sent")
# Case two: the order did leave
f.now = now; f.make("BTC/USD", "buy", cid, notional=997.5); code, s, _ = go(f, d, now + dt.timedelta(hours=2))
ok(f.submits == 0 and not tr(s, "P1-BTC")["halted"] and abs(qty(tr(s, "P1-BTC"), "BTC/USD") - 9.8762376238) < 1e-9, "when the broker does list it, it is counted and the trader goes on, without sending again")

# ---- the run died after sending and every record of it was lost: the next day does not buy a second time
d, f = setup(); go(f, d, now); shutil.rmtree(d); d = tempfile.mkdtemp()
f.crypto = crypto_bars(up[1:] + [102], t2); f.px["BTC/USD"] = 102.0; code, s, _ = go(f, d, t2)
ok(f.submits == 1 and abs(qty(tr(s, "P1-BTC"), "BTC/USD") - 9.8762376238) < 1e-9, "a lost record cannot lead to a second buy on the next price day")

# ---- the records cannot be saved: the order is not sent, and is tried again later
d, f = setup(); f.save_fails = True; code, s, _ = go(f, d, now)
ok(f.submits == 0 and not tr(s, "P1-BTC")["halted"] and s["orders"] == [], "no order leaves when its record cannot be saved first")
f.save_fails = False; code, s, _ = go(f, d, now + dt.timedelta(hours=1)); ok(f.submits == 1, "it goes on the next run, once the records can be saved")
d, f = setup(); code, s, _ = go(f, d, now, save=False); ok(f.submits == 0, "with no place to save records, nothing is ever sent")

# ---- a clear refusal: written down, trader not stopped, the same price day is not tried again, the next day is
d, f = setup("reject"); code, s, _ = go(f, d, now); go(f, d, now + dt.timedelta(hours=1))
ok(f.submits == 1 and s["orders"][0]["status"] == "rejected" and not tr(s, "P1-BTC")["halted"], "a refused order is recorded and not repeated for the same price day")
f.mode = "fill"; f.crypto = crypto_bars(up[1:] + [102], t2); f.px["BTC/USD"] = 102.0; code, s, _ = go(f, d, t2)
ok(f.submits == 2 and qty(tr(s, "P1-BTC"), "BTC/USD") > 0, "the next price day is a new decision")

# ---- an order that is not final blocks new orders in its symbol, whatever the broker calls its state
for state in ("accepted", "partially_filled", "done_for_day", "stopped", "suspended", "replaced", "pending_new"):
    d, f = setup("stay_open"); code, s, _ = go(f, d, now); f.list[0]["status"] = state
    f.mode = "fill"; f.crypto = crypto_bars(up[1:] + [102], t2); code, s, _ = go(f, d, t2)
    ok(f.submits == 1 and s["orders"][0]["status"] == "open", f"an order in the state '{state}' is still open: no second order is sent the next day")
ok(code == 1 and any("open for" in p["text"] for p in s["problems"]), "an order open for too long raises the alarm, because this program cannot cancel it")
o = f.list[0]; o.update(status="filled", filled_qty="9.8762376238", filled_avg_price="101.5", filled_at=T.iso(t2)); f.held["BTCUSD"] = 9.8762376238
code, s, _ = go(f, d, t2 + dt.timedelta(hours=1))
ok(f.submits == 1 and s["orders"][0]["status"] == "filled" and abs(s["orders"][0]["gap_bps"] - 49.5) < 0.1, "the open order is counted when it fills, with the gap from the price read (0.5 on 101)")

# ---- a fill the broker reports badly, and an order cancelled part way
d, f = setup("bad_fill"); code, s, _ = go(f, d, now)
ok(code == 1 and tr(s, "P1-BTC")["halted"] and s["orders"][0]["status"] == "unclear", "an order marked filled with no price stops the trader instead of being dropped quietly")
d, f = setup("part_cancel"); code, s, _ = go(f, d, now); btc = tr(s, "P1-BTC")
ok(s["orders"][0]["status"] == "part filled" and abs(qty(btc, "BTC/USD") - 9.8762376238 / 2) < 1e-9 and abs(btc["cash_usd"] - (1000 - 498.75 * 1.0025)) < 0.006, "an order cancelled half way is shown as part filled, and only the filled half is counted")

# ---- the account must add up to the books
d, f = setup(held={"BTCUSD": 0.5}); code, s, _ = go(f, d, now)
ok(code == 1 and f.submits == 0 and s["status"] == "halted" and s["symbols_stopped"][0]["symbol"] == "BTCUSD", "a holding the books do not explain stops trading in that symbol")
d, f = setup(); f.now = now; f.make("BTC/USD", "buy", "someone-else", qty=1, status="accepted"); code, s, _ = go(f, d, now)
ok(code == 1 and f.submits == 0 and "did not send" in s["symbols_stopped"][0]["reason"], "an open order this program did not send stops trading in that symbol")
d, f = setup(coin_fee=0.0025); code, s, r = go(f, d, now); f.crypto = crypto_bars(up[1:] + [50.0], t2); f.px["BTC/USD"] = 110.0
ok(code == 0 and any("fee the practice account takes in coin" in p["text"] for p in s["problems"]), "if the practice account takes its fee in coin, the small gap is written down on the first fill")
code, s, _ = go(f, d, t2)
ok("BTCUSD" not in f.held and f.submits == 2 and code == 1 and s["symbols_stopped"], "the sale is cut to what the account really has, and the books then show the gap and stop the symbol until the fee setting is put right")
code, s, _ = go(f, d, t2 + dt.timedelta(hours=1), dict(cfg, practice_crypto_fee_in_coin=1.0)); b = tr(s, "P1-BTC")
# by hand with the fee in coin: paid 997.50, got 9.876237624 x 0.9975 = 9.851547030. Sold at 110 = 1083.670173, fee 2.709175, back 1080.960998. Gain 83.46.
ok(s["status"] == "running" and b["positions"] == [] and abs(b["gain_usd"] - 83.46) < 0.006 and s["totals"]["wins"] == 1, "with the fee setting put right the same orders are counted again from the start and everything adds up")

# ---- prices that cannot be trusted send nothing
d, f = setup(); f.crypto = crypto_bars(up, now - dt.timedelta(days=3))[:-1]; code, s, _ = go(f, d, now)
ok(f.submits == 0 and any("too old" in p["text"] for p in s["problems"]), "old prices send no order")
d, f = setup(); del f.crypto[100]; code, s, _ = go(f, d, now); ok(f.submits == 0 and any("day is missing" in p["text"] for p in s["problems"]), "a missing day in the bitcoin prices sends no order")
d, f = setup(); f.crypto.append(dict(t=T.iso(now + dt.timedelta(days=2)), c=0.1)); code, s, _ = go(f, d, now); ok(f.submits == 0, "a price dated in the future sends no order")
d, f = setup(); f.quote_age_min = 600; code, s, _ = go(f, d, now); ok(f.submits == 0 and any("No fresh price" in p["text"] for p in s["problems"]), "a stale quote sends no order")
d, f = setup(is_open=True); f.stock = f.stock[:-3] + f.stock[-1:]; code, s, _ = go(f, d, now)
ok(f.submits == 1 and any("finished month" in p["text"] for p in s["problems"]), "a missing month end sends no fund order")
d, f = setup(is_open=True); f.sessions = [dict(date=b["t"][:10]) for b in f.stock] + [dict(date="2026-10-30")]; code, s, _ = go(f, d, now)
ok(f.submits == 1 and any("last trading day of that month was 2026-10-30" in p["text"] for p in s["problems"]), "a month-end price that is not from the month's last trading day sends no fund order")

# ---- the program's own limits
d, f = setup(); code, s, _ = go(f, d, now, dict(cfg, practice_max_order_usd=500.0)); ok(f.submits == 0 and any("largest order" in p["text"] for p in s["problems"]), "an order over the largest size is refused by the program")
d, f = setup(); code, s, _ = go(f, d, now, dict(cfg, practice_max_orders_per_trader_per_day=0.0)); ok(f.submits == 0 and any("allowed number" in p["text"] for p in s["problems"]), "the daily order count is enforced")

# ---- the band: a small change in what the rule wants sends nothing, a larger one sends a part sale
d, f = setup(); go(f, d, now)
three = [200] * 150 + [100] * 49 + [100.9]  # above the 20 and 50 day averages (about 100.05 and 100.02) and below the 100 and 200 day ones: the rule wants half
ok(rules.p1_weight(three) == 0.5, "set-up: the rule wants half")
f.crypto = crypto_bars(three, t2); f.px["BTC/USD"] = 100.9; code, s, _ = go(f, d, t2); b = tr(s, "P1-BTC")
ok(f.submits == 2 and s["orders"][0]["side"] == "sell" and abs(b["positions"][0]["value_usd"] / b["value_usd"] - 0.5) < 0.01 and s["totals"]["closed_trades"] == 0, "a move from all in to half sells about half and closes no trade")
f.crypto = crypto_bars(three[1:] + [100.95], t2 + dt.timedelta(days=1)); code, s, _ = go(f, d, t2 + dt.timedelta(days=1))
ok(f.submits == 2, "no order while the holding is within the band of what the rule wants")

# ---- the form of an AI trader's pick
good = dict(trader="A01", made_utc="2026-11-25T15:00:00Z", expires_utc="2026-11-25T17:00:00Z", thesis="A reason.", actions=[dict(symbol="NVDA", side="buy", usd=250, reason="r")],
            exits=[dict(symbol="NVDA", stop=90.0, target=120.0)])
V = lambda p, pid="20261125T1500Z": picks.validate(p, "A01", pid, now, cfg["practice_pick_max_life_hours"], cfg["practice_pick_max_actions"])
ok(V(good) == [], "a pick in the right form is accepted")
for what, bad in [("an unknown field", dict(good, extra=1)), ("the wrong trader", dict(good, trader="A02")), ("a made time in the future", dict(good, made_utc="2026-11-26T15:00:00Z", expires_utc="2026-11-26T16:00:00Z")),
                  ("too long a life", dict(good, expires_utc="2026-11-29T15:00:00Z")), ("no thesis", dict(good, thesis="")), ("a buy with a share", dict(good, actions=[dict(symbol="NVDA", side="buy", share=1, reason="r")])),
                  ("a negative amount", dict(good, actions=[dict(symbol="NVDA", side="buy", usd=-5, reason="r")])), ("a sell of more than all", dict(good, actions=[dict(symbol="NVDA", side="sell", share=1.5, reason="r")])),
                  ("an odd symbol", dict(good, actions=[dict(symbol="nvda; rm", side="buy", usd=5, reason="r")])), ("a short sale word", dict(good, actions=[dict(symbol="NVDA", side="short", usd=5, reason="r")])),
                  ("a stop above its target", dict(good, exits=[dict(symbol="NVDA", stop=130.0, target=120.0)])), ("not an object", [1, 2]), ("a number that is not finite", dict(good, actions=[dict(symbol="NVDA", side="buy", usd=float("inf"), reason="r")])),
                  ("the same symbol twice", dict(good, actions=good["actions"] * 2))]:
    ok(V(bad) != [], f"a pick with {what} is refused")
ok(V(good, "../../x") != [], "a pick with an odd file name is refused")

# ---- an AI trader: buy, a refused form, a stop that sells, and everything counted once
def put(pd, tid, pid, obj):
    p = Path(pd) / "picks" / tid; p.mkdir(parents=True, exist_ok=True); (p / (pid + ".json")).write_text(obj if isinstance(obj, str) else json.dumps(obj))
d, f = setup(is_open=True); pd = tempfile.mkdtemp(); f.px.update({"NVDA": 100.0, "ABC": 5.0}); f.assets["ABC"] = dict(symbol="ABC", tradable=True, fractionable=False)
put(pd, "A01", "20261125T1500Z", good); put(pd, "A01", "20261125T1501Z", "{not json"); put(pd, "A01", "20261125T1502Z", dict(good, actions=[dict(symbol="ABC", side="buy", usd=50, reason="r")], exits=[]))
code, s, _ = go(f, d, now, traders=AI, picks_dir=pd); a = tr(s, "A01")
ok(f.submits == 1 and abs(qty(a, "NVDA") - 2.5) < 1e-9 and abs(a["cash_usd"] - 750.0) < 0.006 and a["positions"][0]["exit"] == dict(stop=90.0, target=120.0), "an AI pick buys the dollars it asked for, and its exit is on record")
ok(sum("does not fit the form" in p["text"] for p in s["problems"]) == 1 and sum("parts of a share" in p["text"] for p in s["problems"]) == 1, "a broken pick file and a stock that cannot be bought in parts are refused and said so")
ok(a["last_pick"]["thesis"] == "A reason." and s["orders"][0]["reason"] == "r", "the trader's reason is shown with the order")
code, s, _ = go(f, d, now + dt.timedelta(minutes=10), traders=AI, picks_dir=pd); ok(f.submits == 1 and len(s["problems"]) == 2, "a pick is acted on once, and its refusals are written once")
(Path(d) / "picks.jsonl").unlink(); (Path(d) / "state.json").unlink(); code, s, _ = go(f, d, now + dt.timedelta(minutes=20), traders=AI, picks_dir=pd)
ok(f.submits == 1 and abs(qty(tr(s, "A01"), "NVDA") - 2.5) < 1e-9, "losing the record of picks cannot buy the same pick twice")
f.px["NVDA"] = 89.0; code, s, _ = go(f, d, now + dt.timedelta(minutes=30), traders=AI, picks_dir=pd); a = tr(s, "A01")
ok(f.submits == 2 and a["positions"] == [] and a["losses"] == 1 and abs(a["realised_usd"] + 27.5) < 0.006 and "stop price" in s["orders"][0]["reason"], "a stop set by the AI is acted on by the plain program: sold all, a loss of 2.5 x 11 = 27.50")
code, s, _ = go(f, d, now + dt.timedelta(minutes=40), traders=AI, picks_dir=pd); ok(f.submits == 2, "an exit is sent once")

# ---- an AI trader: asks for more than it has, sells a share, lets a pick expire, sells what it does not hold; two traders in one symbol
d, f = setup(is_open=True); pd = tempfile.mkdtemp(); f.px.update({"NVDA": 100.0})
put(pd, "A01", "20261125T1500Z", dict(good, actions=[dict(symbol="NVDA", side="buy", usd=5000, reason="r")], exits=[dict(symbol="NVDA", by_utc="2026-11-25T20:45:00Z")]))
put(pd, "A02", "20261125T1500Z", dict(good, trader="A02", actions=[dict(symbol="NVDA", side="buy", usd=100, reason="r"), dict(symbol="BTC/USD", side="sell", share=1.0, reason="r")], exits=[]))
code, s, _ = go(f, d, now, traders=AI, picks_dir=pd)
ok(f.submits == 2 and abs(qty(tr(s, "A01"), "NVDA") - 10.0) < 1e-9 and tr(s, "A01")["cash_usd"] == 0 and abs(qty(tr(s, "A02"), "NVDA") - 1.0) < 1e-9, "a buy larger than the trader's cash is cut to its cash, and two traders can hold the same stock")
ok(abs(f.held["NVDA"] - 11.0) < 1e-9 and s["status"] == "running" and any("nothing to sell" in p["text"] for p in s["problems"]), "the account adds up across traders, and a sale of nothing is refused")
put(pd, "A01", "20261125T1530Z", dict(good, made_utc="2026-11-25T15:10:00Z", actions=[dict(symbol="NVDA", side="sell", share=0.4, reason="r")], exits=[]))
put(pd, "A02", "20261125T1400Z", dict(good, trader="A02", made_utc="2026-11-25T14:00:00Z", expires_utc="2026-11-25T15:00:00Z", actions=[dict(symbol="NVDA", side="buy", usd=100, reason="r")], exits=[]))
code, s, _ = go(f, d, now + dt.timedelta(minutes=10), traders=AI, picks_dir=pd)
ok(f.submits == 3 and abs(qty(tr(s, "A01"), "NVDA") - 6.0) < 1e-9 and abs(qty(tr(s, "A02"), "NVDA") - 1.0) < 1e-9 and tr(s, "A01")["closed_trades"] == 0, "a sale of a share sells that share, and a pick past its time is dropped")
f.is_open = False; late = dt.datetime(2026, 11, 25, 20, 50, tzinfo=UTC); code, s, _ = go(f, d, late, traders=AI, picks_dir=pd); ok(f.submits == 3, "a timed exit for a stock waits while the market is closed")
f.is_open = True; code, s, _ = go(f, d, late + dt.timedelta(minutes=5), traders=AI, picks_dir=pd)
ok(f.submits == 4 and tr(s, "A01")["positions"] == [] and tr(s, "A01")["closed_trades"] == 1 and abs(qty(tr(s, "A02"), "NVDA") - 1.0) < 1e-9, "a timed exit sells all of that trader's holding and leaves the other trader's alone")
ok(tr(s, "A01")["result"] if False else s["closed"][0]["result"] == "flat", "a trade that gets back exactly what it cost is counted as flat, not as a loss")

print(f"{N[0]} checks passed")
