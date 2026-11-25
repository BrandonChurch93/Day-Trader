"""A pretend Alpaca practice account that plays back the tape. Pretend money only. It never talks to a network.

SimBroker(tape, clock, cfg, state_path) has the same public methods and return shapes as practice/broker.py: Broker,
so practice/trader.py: Run uses it unchanged. clock() returns the simulated now (an aware UTC datetime).

Fill model (every number is a tm_ or practice_ key in config/thresholds.yaml):
  - A market order placed at simulated time T fills at the OPEN of the first 1Min bar that starts at or after T. It never
    uses the bar T sits inside. The price is moved against the trader by half the assumed spread.
  - It fills only once the simulated clock has passed the end of that bar. Until then it is open (status accepted).
  - At most tm_max_share_of_minute_volume (stocks) or tm_crypto_max_share_of_minute_volume (crypto; 0 means no cap) of
    that bar's volume fills. The rest is canceled: status canceled with filled_qty above zero, which is how Alpaca shows a part fill.
  - A stock day order with no regular-hours bar before the close expires at the close. Crypto orders are gtc.
  - Crypto fee: practice_crypto_fee_bps_added. With practice_crypto_fee_in_coin = 0 the cash pays it in dollars, else
    the coins bought are cut by it. Either way practice/books.py counts it the same way, so books and account agree.
  - Cash starts at tm_account_start_usd. Buying power is cash less open buys. No margin, no shorting.
The account (cash, holdings, every order) is written to state_path after every change, so a stop loses nothing.
Fills depend only on the tape and the order, never on when the account is read, so reading twice changes nothing.
Standard library only."""
import datetime as dt, json, math, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "practice") not in sys.path:
    sys.path.insert(0, str(ROOT / "practice"))
from broker import Refused  # the same class practice/trader.py catches

UTC = dt.timezone.utc


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def floor9(x):
    return math.floor(x * 1e9 + 1e-6) / 1e9


def num_str(x):
    return repr(float(x))


class SimBroker:
    def __init__(self, tape, clock, cfg, state_path, data=None):
        self.tape, self.clock, self.cfg, self.path = tape, clock, cfg, Path(state_path)
        self.data = data  # a SimData for get(); made on first use if not given
        self.fee = cfg["practice_crypto_fee_bps_added"] / 1e4; self.in_coin = bool(cfg["practice_crypto_fee_in_coin"])
        if self.path.exists():
            self.s = json.loads(self.path.read_text())
        else:
            self.s = dict(cash=float(cfg["tm_account_start_usd"]), pos={}, orders=[], seq=0)
            self.save()

    # ---- saving
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(self.s, indent=1, sort_keys=True) + "\n"); os.replace(tmp, self.path)

    # ---- the clock moves the orders along
    def settle(self):
        now = self.clock(); changed = False
        for o in self.s["orders"]:
            if o["status"] not in ("accepted", "new"):
                continue
            t0 = parse(o["submitted_at"]); crypto = "/" in o["symbol"]; close = None
            if crypto:
                before = now
            else:
                day = self.tape.session(t0.astimezone(NY()).strftime("%Y-%m-%d"))
                close = day[1] if day else t0
                before = min(now, close)
            bar = self.tape.fill_bar(o["symbol"], t0, before)
            if bar is not None:
                self._fill(o, bar); changed = True
            elif close is not None and now >= close:
                o.update(status="expired", expired_at=iso(close), updated_at=iso(close)); changed = True
        if changed:
            self.save()

    def _fill(self, o, bar):
        crypto = "/" in o["symbol"]; side = o["side"]
        hs = self.cfg["tm_crypto_half_spread_bps" if crypto else "tm_stock_half_spread_bps"] / 1e4
        px = bar["o"] * (1 + hs if side == "buy" else 1 - hs)
        want = floor9(float(o["notional"]) / px) if o["notional"] is not None else float(o["qty"])
        share = self.cfg["tm_crypto_max_share_of_minute_volume" if crypto else "tm_max_share_of_minute_volume"]
        cap = floor9(share * bar["v"]) if share > 0 else math.inf  # 0 means no cap
        k = o["symbol"].replace("/", "")
        if side == "sell":
            want = min(want, self.s["pos"].get(k, 0.0))
        q = min(want, cap); t = iso(bar["t"])
        part = q < want
        if q <= 0:
            o.update(status="canceled", canceled_at=t, updated_at=t, sim_note="no volume could be filled in the fill minute"); return
        notional = q * px; fee = notional * self.fee if crypto else 0.0
        if side == "buy":
            if crypto and self.in_coin:
                self.s["cash"] -= notional; got = q * (1 - self.fee)
            else:
                self.s["cash"] -= notional + fee; got = q
            self.s["pos"][k] = self.s["pos"].get(k, 0.0) + got
        else:
            self.s["cash"] += notional - fee; left = self.s["pos"].get(k, 0.0) - q
            if abs(left) < 1e-9:
                self.s["pos"].pop(k, None)
            else:
                self.s["pos"][k] = left
        o.update(filled_qty=num_str(q), filled_avg_price=num_str(px), filled_at=t, updated_at=t,
                 status="canceled" if part else "filled", sim_fill_bar_utc=t, sim_fee_usd=fee)
        if part:
            o.update(canceled_at=t, sim_note="part filled: the rest was over the share of the minute's volume allowed")

    # ---- the Broker methods
    def has_key(self):
        return True

    def get(self, base, path, params=None):
        if self.data is None:
            from timemachine.simdata import SimData
            self.data = SimData(self.tape, self.clock)
        return self.data.get(base, path, params)

    def account(self):
        self.settle(); bp = self.buying_power()
        return dict(id="sim-account", status="ACTIVE", crypto_status="ACTIVE", trading_blocked=False, account_blocked=False, currency="USD",
                    cash=num_str(self.s["cash"]), buying_power=num_str(bp), non_marginable_buying_power=num_str(bp), multiplier="1", shorting_enabled=False)

    def positions(self):
        self.settle()
        return {k: dict(qty=q, available=q - self._open_sell_qty(k)) for k, q in self.s["pos"].items()}

    def orders(self):
        self.settle()
        return [self._public(o) for o in self.s["orders"]]

    def order_by_cid(self, cid):
        self.settle()
        return next((self._public(o) for o in self.s["orders"] if o["client_order_id"] == cid), None)

    def _public(self, o):
        return {k: v for k, v in o.items() if not k.startswith("sim_")} | {"sim": {k[4:]: v for k, v in o.items() if k.startswith("sim_")}}

    def _open_sell_qty(self, k):
        return sum(float(o["qty"]) for o in self.s["orders"] if o["status"] in ("accepted", "new") and o["side"] == "sell" and o["symbol"].replace("/", "") == k)

    def last_price(self, symbol):
        s = self.tape.snapshot([symbol], self.clock()).get(symbol)
        return s["price"] if s else None

    def buying_power(self):
        held = 0.0
        for o in self.s["orders"]:
            if o["status"] in ("accepted", "new") and o["side"] == "buy":
                n = float(o["notional"]) if o["notional"] is not None else float(o["qty"]) * (self.last_price(o["symbol"]) or 0.0)
                held += n * (1 + (self.fee if "/" in o["symbol"] and not self.in_coin else 0.0))
        return self.s["cash"] - held

    def submit(self, symbol, side, tif, cid, qty=None, notional=None):
        """Places one pretend market order. Raises broker.Refused where Alpaca would answer with a clear refusal."""
        assert side in ("buy", "sell") and tif in ("day", "gtc") and (qty is None) != (notional is None)
        self.settle(); now = self.clock(); crypto = "/" in symbol; k = symbol.replace("/", "")
        if any(o["client_order_id"] == cid for o in self.s["orders"]):
            raise Refused(422, "client_order_id must be unique")
        if not self.tape.has_symbol_as_of(symbol, now):
            raise Refused(422, f"asset {symbol} not found")
        if crypto and tif != "gtc":
            raise Refused(422, "crypto orders must be gtc in the time machine")
        if not crypto:
            if tif != "day":
                raise Refused(422, "stock orders must be day orders in the time machine")
            if not self.tape.is_open(now):
                raise Refused(422, "the stock market is closed; the time machine takes stock orders only while it is open")
            d = now.astimezone(NY()).strftime("%Y-%m-%d")
            if not self.tape.has_minutes(symbol, d) and not self.tape.ensure_minutes(symbol, d):
                raise Refused(422, f"the tape has no minute bars for {symbol} on {d}, so no fill can be worked out")
        if side == "sell" and notional is not None:
            raise Refused(422, "the time machine takes sells by quantity only")
        if side == "buy":
            n = notional if notional is not None else qty * (self.last_price(symbol) or math.inf)
            need = n * (1 + (self.fee if crypto and not self.in_coin else 0.0))
            if need > self.buying_power() + 1e-9:
                raise Refused(403, "insufficient buying power")
        else:
            if qty > self.s["pos"].get(k, 0.0) - self._open_sell_qty(k) + 1e-12:
                raise Refused(403, "insufficient qty available for order")
        self.s["seq"] += 1; t = iso(now)
        o = dict(id=f"{self.s['seq']:08d}-0000-4000-8000-000000000000", client_order_id=cid, symbol=symbol, asset_class="crypto" if crypto else "us_equity",
                 side=side, type="market", time_in_force=tif, status="accepted", qty=None if qty is None else f"{qty:.9f}".rstrip("0").rstrip("."),
                 notional=None if notional is None else f"{notional:.2f}", filled_qty="0", filled_avg_price=None, created_at=t, submitted_at=t, updated_at=t,
                 filled_at=None, canceled_at=None, expired_at=None)
        self.s["orders"].append(o); self.save()
        return self._public(o)

    # ---- for the session and the tests
    def cash(self):
        self.settle(); return self.s["cash"]

    def holding(self):
        self.settle(); return dict(self.s["pos"])

    def has_open(self):
        self.settle(); return any(o["status"] in ("accepted", "new") for o in self.s["orders"])


def NY():
    from zoneinfo import ZoneInfo
    return ZoneInfo("America/New_York")
