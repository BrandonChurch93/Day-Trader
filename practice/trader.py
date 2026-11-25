"""The practice desk. A plain program on a timer, pretend money only, Alpaca practice account only.

It is the hands, not the head. Decisions come from two places:
  - fixed rules (practice/rules.py), worked out here from prices;
  - AI traders, who write their decisions as pick files (practice/picks.py says what a pick looks like).
This program checks each decision against the trader's pretend budget and the limits in config/thresholds.yaml, places
the order, and writes down what happened. It adds no opinion of its own, and no model runs inside it.

One run:
  1. Read the account, every order and every holding from the broker (AGENTS.md, "What the order program always does").
  2. Work out each trader's books again from the broker's order list (practice/books.py). Nothing is carried in memory.
  3. Compare the books with what the account holds. A symbol that does not add up is not traded.
  4. For each trader: check exits, then new decisions. Before any order is sent, the intent is written down and saved
     to the records branch. If it cannot be saved, the order is not sent.
  5. An order whose result is not clear is never sent again (AGENTS.md, "What the order program always does").
     The trader stops until it is cleared by hand.
  6. Write summary.json for the owner's screen.

Usage: python3 practice/trader.py     (records go to $PRACTICE_RECORDS_DIR, picks are read from $PRACTICE_PICKS_DIR)
Every number comes from config/thresholds.yaml (keys starting practice_). Standard library only."""
import datetime as dt, hashlib, json, math, os, re, subprocess, sys, time
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import books, picks, rules
from broker import Broker, Refused, Unclear

ROOT = Path(__file__).resolve().parent.parent
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
KEYS = ["practice_amount_per_trader_usd", "practice_max_order_usd", "practice_min_order_usd", "practice_max_orders_per_trader_per_day", "practice_rebalance_band",
        "practice_crypto_fee_bps_added", "practice_crypto_fee_in_coin", "practice_max_price_age_hours_crypto", "practice_max_price_age_days_stock",
        "practice_max_quote_age_minutes", "practice_fill_wait_seconds", "practice_qty_tolerance", "practice_open_order_max_hours",
        "practice_unread_runs_before_alarm", "practice_pick_max_life_hours", "practice_pick_max_actions"]
HISTORY_DAYS = {"p1": 260, "t1": 400}
RESOLVED = {"rejected", "not_sent", "cleared"}  # journal events after which an intent needs no more attention


def config(path=ROOT / "config" / "thresholds.yaml"):
    out, key = {}, None
    for line in open(path):
        m = re.match(r"^([a-z0-9_]+):\s*$", line)
        if m:
            key = m.group(1); continue
        m = re.match(r"^  value:\s*(.*)$", line)
        if m and key in KEYS:
            out[key] = float(m.group(1).strip())
    bad = [k for k in KEYS if not (k in out and math.isfinite(out[k]) and out[k] >= 0)]
    assert not bad, f"missing or not a plain number in config/thresholds.yaml: {bad}"
    return out


def roster(path=Path(__file__).parent / "traders.json"):
    r = json.loads(Path(path).read_text())
    assert len({t["id"] for t in r}) == len(r) and all(re.fullmatch(r"[A-Z0-9-]{2,12}", t["id"]) and t["kind"] in ("rule", "ai") for t in r), "bad traders.json"
    return r


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def floor_dp(x, dp):
    """x cut down to dp decimals. Never above x. Worked on the number as written, so 0.3 stays 0.3."""
    if not (isinstance(x, (int, float)) and math.isfinite(x) and x > 0):
        return 0.0
    return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-dp), rounding=ROUND_DOWN))


class Records:
    def __init__(self, folder):
        self.dir = Path(folder); self.dir.mkdir(parents=True, exist_ok=True)
        self.defer_writes = False; self._mem = {}; self._last_run = None

    def add(self, name, row):
        line = json.dumps(row, sort_keys=True) + "\n"
        with open(self.dir / (name + ".jsonl"), "a") as f:
            f.write(line)
        kept = self.__dict__.get("_kept")
        if self.defer_writes and kept is not None and name in kept:
            at, rows = kept[name]
            rows.append(json.loads(line))
            kept[name] = (at + len(line.encode()), rows)

    def rows(self, name):
        """Every row of one record file. The files only ever grow, so rows read before are kept and only new lines are parsed."""
        kept = self.__dict__.setdefault("_kept", {})
        if self.defer_writes and name in kept:
            return kept[name][1]
        p = self.dir / (name + ".jsonl")
        if not p.exists():
            if self.defer_writes:
                kept[name] = (0, [])
            return []
        at, rows = kept.get(name, (0, []))
        size = p.stat().st_size
        if size < at:
            at, rows = 0, []
        if size > at:
            with open(p, "rb") as f:
                f.seek(at); chunk = f.read()
            end = chunk.rfind(b"\n") + 1                      # a half-written last line waits for the next read
            rows = rows + [json.loads(x) for x in chunk[:end].decode().split("\n") if x.strip()]
            at += end; kept[name] = (at, rows)
        elif self.defer_writes:
            kept[name] = (at, rows)
        return [dict(r) for r in rows]

    def load(self, name, default):
        if self.defer_writes and name in self._mem:
            return self._mem[name]
        p = self.dir / name
        try:
            return json.loads(p.read_text()) if p.exists() else default
        except ValueError:
            return default

    def save(self, name, obj):
        if self.defer_writes:
            self._mem[name] = obj
            return
        tmp = self.dir / (name + ".tmp"); tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n"); os.replace(tmp, self.dir / name)

    def flush(self):
        if self._last_run is not None:
            r = self._last_run; self._last_run = None
            self._mem["summary.json"] = r.summary(None, None)
        for name, obj in list(self._mem.items()):
            tmp = self.dir / (name + ".tmp"); tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n"); os.replace(tmp, self.dir / name)


class Run:
    def __init__(self, broker, mkt, rec, cfg, traders, picks_dir=None, now=None, sleep=time.sleep, checkpoint=None, clear=None):
        self.b, self.m, self.rec, self.cfg, self.traders, self.sleep, self.checkpoint, self.clear = broker, mkt, rec, cfg, traders, sleep, checkpoint, clear
        self.picks_dir = Path(picks_dir) if picks_dir else None
        self.now = now or dt.datetime.now(UTC); self.today = self.now.strftime("%Y-%m-%d")
        # state.json is a convenience only. Losing it loses nothing that matters: books come from the broker, stops from the journal.
        self.state = rec.load("state.json", {}); self.state.setdefault("done", {}); self.state.setdefault("alarms", []); self.state.setdefault("said", {})
        self.fee = cfg["practice_crypto_fee_bps_added"] / 1e4; self.start = cfg["practice_amount_per_trader_usd"]
        self.alarms, self.new_alarm = set(), False; self.blocked, self.sym_blocked = {}, {}
        self.books, self.others, self.cids, self.held, self.px, self.sent, self.sent_n = {}, [], set(), {}, {}, [], {}
        self.pick_files, self._clock, self._assets, self.acct = {}, "unread", {}, {}
        self.res_cash, self.res_qty, self.sym_open = {}, {}, set()
        self.inflight, self.acct_cash, self.dead, self.late_picks, self.t0 = {}, 0.0, set(), set(), time.monotonic()
        self.state.setdefault("last_px", {})

    # ---- writing things down
    def problem(self, who, text, once_key=None):
        if once_key:
            if self.state["said"].get(once_key) == self.today:
                return
            self.state["said"][once_key] = self.today
        self.rec.add("problems", dict(utc=iso(self.now), trader=who, text=text))

    def alarm(self, key, who, text):
        """Something the owner should know about. The run ends with an error the first time each one is seen."""
        self.alarms.add(key)
        if key not in self.state["alarms"]:
            self.new_alarm = True; self.problem(who, text)

    def fee_rate(self, symbol):
        return self.fee if "/" in symbol else 0.0

    # ---- what the broker says
    def read_broker(self):
        orders, held = self.b.orders(), self.b.positions()
        self.held = held; ids = [t["id"] for t in self.traders]
        if self.rec.defer_writes:
            sig = (len(orders), tuple((o.get("id"), o.get("status"), o.get("filled_qty"), o.get("filled_avg_price")) for o in orders))
            bc = getattr(self.rec, "_broker_cache", None)
            if bc is not None and bc[0] == sig:
                self.books, self.others, self.cids, self.by_cid = bc[1]
                return
        self.books, self.others = books.derive(orders, ids, self.start, self.fee, bool(self.cfg["practice_crypto_fee_in_coin"]))
        self.cids = {o.get("client_order_id") for o in orders}
        self.by_cid = {o.get("client_order_id"): o for o in orders}
        if self.rec.defer_writes:
            self.rec._broker_cache = (sig, (self.books, self.others, self.cids, self.by_cid))

    def check_books(self):
        self.blocked, self.sym_blocked = {}, {}
        a = self.acct
        if a.get("trading_blocked") or a.get("account_blocked") or a.get("status") != "ACTIVE":
            for t in self.traders:
                self.blocked[t["id"]] = "The practice account says it cannot trade right now."
            self.alarm("account", None, "The practice account says it cannot trade right now. No order is sent.")
        # An intent the broker does not list is unclear, so that trader stops (see "What the order program always does").
        last = {}
        for r in self.rec.rows("orders"):
            last[r["cid"]] = r
        self.dead = {cid for cid, r in last.items() if r["event"] in ("cleared", "rejected") and cid not in self.cids}  # never sent again under the same id
        for cid, r in last.items():
            if r["event"] in RESOLVED or cid in self.cids:
                continue
            if self.clear and self.clear == r["trader"]:
                try:
                    found = self.b.order_by_cid(cid)  # ask the broker for this one order by name before believing it is not there
                except (Unclear, Refused):
                    found = "unread"
                if found is None:
                    self.rec.add("orders", dict(r, utc=iso(self.now), event="cleared")); self.dead.add(cid)
                    self.problem(r["trader"], f"The unclear order {cid} was cleared by hand. The broker does not have it. It is not sent again, and the trader may trade again."); continue
                self.problem(r["trader"], f"The unclear order {cid} was not cleared: " + ("the broker could not be asked about it." if found == "unread" else "the broker does have it. It is counted when it shows in the order list."))
            self.blocked[r["trader"]] = f"An order ({cid}) was written down as about to be sent, and the broker does not list it. It is not clear whether it was sent. It was not sent again."
            self.alarm("unclear:" + cid, r["trader"], "Stopped. " + self.blocked[r["trader"]])
        for tid, b in self.books.items():
            if b["bad"]:
                self.blocked[tid] = b["bad"][0]; self.alarm("bad:" + tid, tid, "Stopped. " + b["bad"][0])
            for o in b["open"]:
                age = (self.now - picks.parse_t(o["utc"])).total_seconds() / 3600 if o.get("utc") else 0
                if age > self.cfg["practice_open_order_max_hours"]:
                    self.alarm("old:" + o["client_order_id"], tid, f"An order for {o['symbol']} has been open for {age:.0f} hours. This program cannot cancel orders. Look at the practice account.")
        # the account must add up to the books, symbol by symbol
        total, open_syms = {}, set()
        for b in self.books.values():
            for k, q in list(b["pos"].items()) + list(b["dust"].items()):
                total[k] = total.get(k, 0.0) + q
            open_syms |= {books.key(o["symbol"]) for o in b["open"]}
        for o in self.others:
            if o.get("status") not in books.FINAL:
                k = books.key(o["symbol"]); self.sym_blocked[k] = f"The account has an open order for {o['symbol']} that this program did not send."
                self.alarm("stray:" + k, None, self.sym_blocked[k] + " Nothing is traded in that symbol.")
        self.ratio = {}; self.sym_open = set(open_syms)
        for k in set(total) | set(self.held):
            have, want = self.held.get(k, {}).get("qty", 0.0), total.get(k, 0.0)
            if k in open_syms:
                continue  # an order is still filling; compare again when it is final
            self.ratio[k] = have / want if want > 0 else 1.0
            if abs(have - want) > max(1e-9, self.cfg["practice_qty_tolerance"] * max(have, want)):
                self.sym_blocked[k] = f"The practice account holds {have:g} of {k} and the books add up to {want:g}."
                self.alarm("recon:" + k, None, self.sym_blocked[k] + " Nothing is traded in that symbol until they agree.")
            elif abs(have - want) > 1e-9:
                self.problem(None, f"The practice account holds {have:g} of {k} and the books add up to {want:g}. The gap is inside the allowed {self.cfg['practice_qty_tolerance']:g} and may be a fee the practice account takes in coin.", once_key="near:" + k)

    # ---- prices
    def load_picks(self):
        """A pick is fixed the first time the desk sees it. The copy written down then is the one that counts: a file that is
        changed or taken away afterwards changes nothing, so a standing stop cannot vanish and one action cannot run twice."""
        self.pick_files = {}; kept = {}
        for r in self.rec.rows("picks"):
            if r["n"] == -2 and "obj" in r:
                kept.setdefault(r["trader"], {})[r["pick_id"]] = r
        for t in self.traders:
            tid, out = t["id"], {}
            for pid, r in kept.get(tid, {}).items():
                out[pid] = (pid, r["obj"], [])
                if r["outcome"] == "late":
                    self.late_picks.add((tid, pid))
            folder = self.picks_dir / "picks" / tid if self.picks_dir else None
            sha_cache = self.rec.__dict__.setdefault("_pick_sha", {})
            for f in sorted(folder.glob("*.json")) if folder and folder.is_dir() else []:
                pid = f.stem
                if pid in out:
                    if self.rec.defer_writes:
                        st = f.stat(); key = (str(f), st.st_mtime_ns, st.st_size)
                        sha = sha_cache.get(key)
                        if sha is None:
                            try:
                                raw = f.read_bytes()
                            except Exception:
                                raw = b""
                            sha = hashlib.sha256(raw).hexdigest()[:16]; sha_cache[key] = sha
                    else:
                        try:
                            raw = f.read_bytes()
                        except Exception:
                            raw = b""
                        sha = hashlib.sha256(raw).hexdigest()[:16]
                    if kept[tid][pid].get("sha") != sha:
                        self.problem(tid, f"Pick {pid} was changed after the desk first saw it. The first copy is the one in force. A change needs a new pick.", once_key=f"chg:{tid}:{pid}:{sha}")
                    continue
                try:
                    raw = f.read_bytes(); obj = json.loads(raw)
                    errs = picks.validate(obj, tid, pid, self.now, self.cfg["practice_pick_max_life_hours"], self.cfg["practice_pick_max_actions"])
                except Exception:  # a file that cannot be read as a pick stops only itself
                    raw, obj, errs = b"", None, ["The file could not be read as a pick."]
                sha = hashlib.sha256(raw).hexdigest()[:16]
                if errs:
                    out[pid] = (pid, obj, errs); continue
                late = self.now > picks.parse_t(obj["expires_utc"])
                self.rec.add("picks", dict(utc=iso(self.now), trader=tid, pick_id=pid, n=-2, outcome="late" if late else "seen", sha=sha, obj=obj))
                out[pid] = (pid, obj, [])
                if late:
                    self.late_picks.add((tid, pid))
            self.pick_files[tid] = [out[k] for k in sorted(out)]

    def read_prices(self):
        want = set()
        for t in self.traders:
            want |= {t.get("symbol"), t.get("benchmark")}
            done = {(r["pick_id"], r["n"]) for r in self.rec.rows("picks") if r["trader"] == t["id"]}
            for pid, obj, errs in self.pick_files.get(t["id"], []):  # only actions that can still be placed need a price
                if not errs and (t["id"], pid) not in self.late_picks and self.now <= picks.parse_t(obj["expires_utc"]):
                    want |= {a["symbol"] for n, a in enumerate(obj["actions"]) if (pid, n) not in done and books.cid_for(t["id"], f"{pid}.{n}") not in self.cids}
        for b in self.books.values():
            want |= {b["sym"][k] for k in b["pos"]}
        want.discard(None)
        try:
            self.px = self.m.prices(sorted(want)) if want else {}
        except (Unclear, Refused) as e:
            self.px = {}; missed = []
            for sym in sorted(want):  # one bad symbol must not take the prices of the others with it
                try:
                    self.px.update(self.m.prices([sym]))
                except (Unclear, Refused):
                    missed.append(sym)
            self.problem(None, f"Could not read prices for {', '.join(missed)[:200]} ({e}). No order is sent in those on this run.", once_key="noprices")
        for sym in want:
            v = (self.px.get(sym) or {}).get("price")
            if isinstance(v, (int, float)) and v > 0 and math.isfinite(v):
                self.state["last_px"][sym] = v

    def price(self, symbol, fresh=True):
        """Newest price, or None. With fresh=True, only a price read within practice_max_quote_age_minutes."""
        p = self.px.get(symbol)
        if not p or not (isinstance(p.get("price"), (int, float)) and p["price"] > 0 and math.isfinite(p["price"])):
            return None if fresh else self.state["last_px"].get(symbol)  # for showing a value, the last price seen is better than nothing
        if fresh:
            try:
                age = (self.now - picks.parse_t(p["utc"])).total_seconds() / 60
            except (ValueError, KeyError, TypeError):
                return None
            if age > self.cfg["practice_max_quote_age_minutes"] or age < -5:
                return None
        return p["price"]

    def market_open(self):
        if self._clock == "unread":
            try:
                self._clock = bool(self.m.clock()["is_open"])
            except Exception:
                self._clock = None; self.problem(None, "Could not tell whether the stock market is open. No stock order is sent on this run.", once_key="noclock")
        return self._clock

    def asset(self, symbol):
        if symbol not in self._assets:
            self._assets[symbol] = self.m.asset(symbol)
        return self._assets[symbol]

    def value(self, tid):
        b = self.books[tid]
        tot = b["cash"]
        for k, q in b["pos"].items():
            px = self.price(b["sym"][k], fresh=False)
            if px is None:  # never seen a price: count the holding at what was paid for it, and say so
                tot += b["trades"][k]["cost_usd"] - b["trades"][k]["back_usd"] if k in b["trades"] else 0.0
                self.problem(tid, f"No price could be read for {b['sym'][k]}. Its value is shown at what was paid.", once_key=f"nopx:{k}")
            else:
                tot += q * px
        return tot

    def spare_cash(self, tid):
        """Pretend cash the trader can still spend: its books, less buys still open at the broker, less buys sent on this run."""
        b = self.books[tid]; held_back = 0.0
        for o in b["open"]:
            if o["side"] == "buy":
                asked = o["asked_usd"] or (o["asked_qty"] or 0.0) * (self.price(o["symbol"], fresh=False) or 0.0)
                held_back += max(0.0, asked - (o["notional_usd"] or 0.0)) * (1 + self.fee_rate(o["symbol"]))
        return b["cash"] - held_back - self.res_cash.get(tid, 0.0)

    def spare_qty(self, tid, k):
        return max(0.0, self.books[tid]["pos"].get(k, 0.0) - self.res_qty.get((tid, k), 0.0))

    # ---- sending one order
    def send(self, tid, symbol, side, px, tag, reason, qty=None, usd=None, deadline=None):
        """Returns 'sent', 'wait: why' or 'refused: why'."""
        cfg, k, cid = self.cfg, books.key(symbol), books.cid_for(tid, tag)
        if cid in self.cids:
            return "sent"  # the broker already has it
        if cid in self.dead:
            return "refused: this same order was refused or cleared before, and it is not sent again"
        if tid in self.blocked:
            return "wait: this trader is stopped"
        if k in self.sym_blocked:
            return "wait: " + self.sym_blocked[k]
        if any(books.key(o["symbol"]) == k for o in self.books[tid]["open"]):
            return "wait: an earlier order in this symbol is still open"
        if k in self.sym_open:
            return "wait: an order in this symbol is still open"  # for every trader: the account cannot be checked against the books until it is done
        if any(t == tid or sd == "sell" or side == "sell" for t, sd in self.inflight.get(k, [])):
            return "wait: another order in this symbol was sent on this run"  # two traders may buy the same symbol at once; nothing may cross a sale
        size = usd if usd is not None else qty * px
        if size < cfg["practice_min_order_usd"]:
            return "refused: the order would be too small to send"
        if size > cfg["practice_max_order_usd"]:
            return "refused: the order would be larger than the largest order allowed"
        if self.books[tid]["by_day"].get(self.today, 0) + self.sent_n.get(tid, 0) >= cfg["practice_max_orders_per_trader_per_day"]:
            return "refused: this trader has already sent its allowed number of orders today"
        fee = self.fee_rate(symbol); b = self.books[tid]
        if side == "buy" and usd > self.acct_cash:
            return "refused: the practice account does not have that much cash"
        if side == "buy" and usd * (1 + fee) > self.spare_cash(tid) + 0.005:
            return "refused: the trader does not have that much pretend cash left"
        if side == "sell" and qty > self.spare_qty(tid, k) * (1 + 1e-9):
            return "refused: the trader does not hold that much"
        base = dict(trader=tid, symbol=symbol, cid=cid, side=side, qty=qty, usd=usd, assumed_price=px, reason=reason)
        self.rec.add("orders", dict(utc=iso(self.now), event="sending", **base))
        try:
            if not self.checkpoint:
                raise RuntimeError("no place to save the records")
            self.rec.save("state.json", self.state); self.checkpoint()
        except Exception as e:
            self.rec.add("orders", dict(utc=iso(self.now), event="not_sent", **base))
            self.problem(tid, f"The records could not be saved before sending an order ({type(e).__name__}), so it was not sent. It is tried again on the next run.", once_key="nosave")
            return "wait: the records could not be saved first"
        took = time.monotonic() - self.t0  # saving can take a while: the price and the pick must still be good when the order goes
        late = self.now + dt.timedelta(seconds=took)
        try:
            old = (late - picks.parse_t(self.px[symbol]["utc"])).total_seconds() > 60 * cfg["practice_max_quote_age_minutes"]
        except (KeyError, ValueError, TypeError):
            old = True
        shut = False
        if "/" not in symbol:  # the stock market may have closed while the records were being saved: ask again
            try:
                shut = not bool(self.m.clock()["is_open"])
            except Exception:
                shut = True
        if old or shut or (deadline and late > deadline):
            self.rec.add("orders", dict(utc=iso(self.now), event="not_sent", why="too late after saving", **base))
            return "wait: saving the records took too long, so the order was not sent on this run"
        self.sent_n[tid] = self.sent_n.get(tid, 0) + 1; self.cids.add(cid); self.inflight.setdefault(k, []).append((tid, side))
        # set the money or the holding aside now, so a second decision on this run cannot spend it again
        # (kept apart from the books, which only ever change when the broker reports a fill)
        if side == "buy":
            self.res_cash[tid] = self.res_cash.get(tid, 0.0) + usd * (1 + fee); self.acct_cash -= usd
        else:
            self.res_qty[(tid, k)] = self.res_qty.get((tid, k), 0.0) + qty
        try:
            o = self.b.submit(symbol, side, "gtc" if "/" in symbol else "day", cid, qty=qty, notional=usd)
        except Refused as e:
            self.rec.add("orders", dict(utc=iso(self.now), event="rejected", why=str(e), **base)); self.problem(tid, f"The broker refused an order for {symbol}: {e}")
            self.dead.add(cid); self.inflight[k].remove((tid, side))  # nothing was placed, so give back what was set aside
            if side == "buy":
                self.res_cash[tid] -= usd * (1 + fee); self.acct_cash += usd
            else:
                self.res_qty[(tid, k)] -= qty
            return "refused: the broker refused it"
        except Unclear as e:
            try:
                o = self.b.order_by_cid(cid)
            except (Unclear, Refused):
                o = None
            if o is None:
                self.rec.add("orders", dict(utc=iso(self.now), event="unclear", why=str(e), **base))
                self.blocked[tid] = f"An order for {symbol} was sent and the broker's answer was not clear. It was not sent again."
                self.alarm("unclear:" + cid, tid, "Stopped. " + self.blocked[tid]); return "sent"
        self.rec.add("orders", dict(utc=iso(self.now), event="sent", order_id=o.get("id"), **base)); self.sent.append(cid)
        return "sent"

    def sell_qty(self, tid, k, share):
        """How much to sell: the trader's share of what the account really has, so a fee taken in coin cannot leave an order too large."""
        q = self.spare_qty(tid, k) * min(1.0, self.ratio.get(k, 1.0)) * share
        if k in self.held:
            q = min(q, self.held[k].get("available", self.held[k]["qty"]))  # never more than the broker says can be sold right now
        return floor_dp(q, 9)

    # ---- a fixed rule
    def rule_prices(self, t):
        """Returns dict(closes, key, fingerprint) or a string saying why there is no usable price history."""
        bars = self.m.daily_bars(t["symbol"], iso(self.now - dt.timedelta(days=HISTORY_DAYS[t["rule"]])))
        if not bars:
            return "The price service returned no prices."
        rows = [(picks.parse_t(x["t"]), float(x["c"])) for x in bars]
        if any(not (c > 0 and math.isfinite(c)) for _, c in rows) or any(a[0] >= b[0] for a, b in zip(rows, rows[1:])) or rows[-1][0] > self.now:
            return "The prices are not in order, or one is missing, not above zero, or dated in the future."
        if t["rule"] == "p1":
            done = [(d, c) for d, c in rows if d + dt.timedelta(days=1) <= self.now]
            if not done:
                return "No finished day in the prices."
            age_h = (self.now - (done[-1][0] + dt.timedelta(days=1))).total_seconds() / 3600
            if age_h > self.cfg["practice_max_price_age_hours_crypto"]:
                return f"The newest finished day ended {age_h:.0f} hours ago, which is too old."
            used = done[-max(rules.P1_WINDOWS):]
            if any(b[0] - a[0] != dt.timedelta(days=1) for a, b in zip(used, used[1:])):
                return "A day is missing from the prices the rule needs."
            closes = [c for _, c in done]; key = done[-1][0].strftime("%Y%m%dT%H%M"); used = [c for _, c in used]
        else:
            daily = [(d.astimezone(NY).strftime("%Y-%m-%d"), c) for d, c in rows]; now_ny = self.now.astimezone(NY)
            age_d = (now_ny.date() - dt.date.fromisoformat(daily[-1][0])).days
            if age_d > self.cfg["practice_max_price_age_days_stock"]:
                return f"The newest daily price is {age_d} days old, which is too old."
            ends = rules.month_ends(daily, now_ny.strftime("%Y-%m")); prev = (now_ny.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
            if not ends or ends[-1][0] != prev:
                return f"The newest finished month in the prices is {ends[-1][0] if ends else 'missing'}, and it should be {prev}."
            use = ends[-rules.T1_MONTHS:]
            sessions = [s["date"] for s in self.m.calendar(use[0][0] + "-01", now_ny.strftime("%Y-%m-%d"))]
            for mth, day, _ in use:  # each month-end price must be from the last trading day of its month
                last = max((s for s in sessions if s[:7] == mth), default=None)
                if last != day:
                    return f"The last price of {mth} is dated {day}, and the last trading day of that month was {last}."
            closes = [c for _, _, c in ends]; key = prev; used = [c for _, _, c in use]
        return dict(closes=closes, key=key, fingerprint=hashlib.sha256(json.dumps(used).encode()).hexdigest()[:16], n=len(closes))

    def decide_rule(self, t):
        tid, sym, cfg = t["id"], t["symbol"], self.cfg; k = books.key(sym)
        try:
            pr = self.rule_prices(t)
        except (Unclear, Refused) as e:
            self.problem(tid, f"Could not read prices ({e}). No order was sent.", once_key="rp:" + tid); return
        if isinstance(pr, str):
            self.problem(tid, pr + " No order was sent.", once_key="rp:" + tid + pr[:40]); return
        if self.state["done"].get(tid) == pr["key"]:
            return
        tw = rules.p1_weight(pr["closes"]) if t["rule"] == "p1" else rules.t1_weight(pr["closes"])
        check = dict(utc=iso(self.now), trader=tid, price_key=pr["key"], prices_fingerprint=pr["fingerprint"], n_prices=pr["n"], last_close=pr["closes"][-1], target_weight=tw)
        def done(action, **more):
            self.rec.add("checks", dict(action=action, **more, **check)); self.state["done"][tid] = pr["key"]
        if tw is None:
            return done("none", reason="not enough price history")
        self.state.setdefault("target", {})[tid] = tw
        if "/" not in sym and self.market_open() is not True:
            return  # wait for the stock market to open; the same decision is made on a later run
        px = self.price(sym)
        if px is None:
            self.problem(tid, f"No fresh price for {sym}. The decision waits for the next run.", once_key="np:" + tid); return
        b = self.books[tid]; qty = b["pos"].get(k, 0.0); fee = self.fee_rate(sym); equity = b["cash"] + qty * px; cur = qty * px / equity if equity > 0 else 0.0
        check.update(newest_price=px, books_qty=qty, cash_usd=round(b["cash"], 2), value_usd=round(equity, 2), weight_now=round(cur, 4))
        if not ((tw == 0 and qty > 0) or (tw > 0 and qty == 0) or abs(tw - cur) > cfg["practice_rebalance_band"]):
            return done("none", reason="already where the rule wants to be")
        want, have = tw * equity, qty * px; tag = pr["key"]
        if want > have:
            usd = floor_dp(min((want - have) / (1 + tw * fee), b["cash"] / (1 + fee)), 2)
            res = self.send(tid, sym, "buy", px, tag, f"The rule wants {tw:.0%} in the market and has {cur:.0%}.", usd=usd); more = dict(side="buy", usd=usd)
        else:
            q = self.sell_qty(tid, k, 1.0) if tw == 0 else floor_dp(min((have - want) / (1 - tw * fee), have) / px * min(1.0, self.ratio.get(k, 1.0)), 9)
            res = self.send(tid, sym, "sell", px, tag, f"The rule wants {tw:.0%} in the market and has {cur:.0%}.", qty=q); more = dict(side="sell", qty=q)
        if res.startswith("wait"):
            return
        if res.startswith("refused"):
            self.problem(tid, f"An order was not placed: {res[9:]}.")
        done("order" if res == "sent" else "refused", result=res, **more)

    # ---- an AI trader
    def exit_for(self, tid, k):
        """The newest exit conditions an AI trader set for a holding, from the pick that opened it or a later one."""
        tr = self.books[tid]["trades"].get(k); out = None
        if not tr:
            return None
        first = (books.parse_cid(tr["first_cid"]) or ("", ""))[1].rsplit(".", 1)[0]
        for pid, obj, errs in self.pick_files.get(tid, []):
            if errs or pid.lower() < first or (tid, pid) in self.late_picks:
                continue
            for x in obj.get("exits", []):
                if books.key(x["symbol"]) == k:
                    out = dict(x, pick_id=pid)
        return out

    def decide_ai(self, t):
        tid, b = t["id"], self.books[t["id"]]
        done = {(r["pick_id"], r["n"]) for r in self.rec.rows("picks") if r["trader"] == tid}
        def note(pid, n, outcome, **more):
            self.rec.add("picks", dict(utc=iso(self.now), trader=tid, pick_id=pid, n=n, outcome=outcome, **more)); done.add((pid, n))
        # (a pick first seen after it ran out is in self.late_picks and changes nothing, exits included)
        # exits first
        for k in list(b["pos"]):
            x = self.exit_for(tid, k); sym = b["sym"][k]; px = self.price(sym)
            if not x or px is None or ("/" not in sym and self.market_open() is not True):
                continue
            why = "the stop price was reached" if "stop" in x and px <= x["stop"] else "the target price was reached" if "target" in x and px >= x["target"] else \
                  "the exit time was reached" if "by_utc" in x and self.now >= picks.parse_t(x["by_utc"]) else None
            # exit orders are named x.<pick>.<symbol>.<how many times this symbol was closed before>.<count>
            hold = (k.lower(), str(sum(c["symbol"] == sym for c in b["closed"])))
            def mine(cid):  # an exit order of this trader for this holding, whichever pick set the exit
                p = books.parse_cid(cid); t = p[1].split(".") if p else []
                return bool(p) and p[0] == tid.lower() and len(t) == 5 and t[0] == "x" and (t[2], t[3]) == hold
            began = sum(1 for o in b["orders"] if mine(o["client_order_id"]))
            if began and not why:
                why = "the exit had already begun and part of the holding was left"  # once an exit starts it is finished, whatever the price or a newer pick says
            if why:
                dead = sum(1 for c in self.dead if mine(c))
                if dead >= 3:
                    self.blocked[tid] = f"An exit for {sym} was refused or cleared {dead} times."; self.alarm(f"exit:{tid}:{k}:{hold[1]}", tid, "Stopped. " + self.blocked[tid]); return
                pre = f"x.{x['pick_id']}.{k}.{hold[1]}."; n = dead + began
                res = self.send(tid, sym, "sell", px, pre + str(n), f"Exit set in pick {x['pick_id']}: {why}.", qty=self.sell_qty(tid, k, 1.0))
                if res.startswith("refused"):
                    self.problem(tid, f"An exit for {sym} was not placed: {res[9:]}.", once_key=f"x:{tid}:{k}")
        # then new decisions, oldest pick first
        for pid, obj, errs in self.pick_files.get(tid, []):
            if errs:
                if (pid, -1) not in done:
                    note(pid, -1, "refused", why=" ".join(errs)[:600]); self.problem(tid, f"Pick {pid} does not fit the form and nothing in it was traded: {' '.join(errs)[:300]}")
                continue
            for n, a in enumerate(obj["actions"]):
                if (pid, n) in done or books.cid_for(tid, f"{pid}.{n}") in self.cids:
                    continue
                if self.now > picks.parse_t(obj["expires_utc"]):
                    note(pid, n, "expired", symbol=a["symbol"], side=a["side"]); continue
                res = self.act(tid, a, f"{pid}.{n}", picks.parse_t(obj["expires_utc"]))
                if not res.startswith("wait"):
                    note(pid, n, res, symbol=a["symbol"], side=a["side"])
                    if res.startswith("refused"):
                        self.problem(tid, f"Pick {pid}: {a['side']} {a['symbol']} was not placed: {res[9:]}.")

    def act(self, tid, a, tag, deadline=None):
        sym, k, b = a["symbol"], books.key(a["symbol"]), self.books[tid]
        try:
            info = self.asset(sym)
        except (Unclear, Refused):
            return "wait: could not read whether the symbol can be traded"
        if not info or not info.get("tradable"):
            return "refused: the practice account cannot trade this symbol"
        if "/" not in sym:
            if not info.get("fractionable"):
                return "refused: this stock cannot be bought in parts of a share, which the desk needs"
            if self.market_open() is not True:
                return "wait: the stock market is closed"
        px = self.price(sym)
        if px is None:
            return "wait: no fresh price"
        fee = self.fee_rate(sym)
        if a["side"] == "buy":
            usd = floor_dp(min(a["usd"], max(0.0, self.spare_cash(tid)) / (1 + fee)), 2)
            return self.send(tid, sym, "buy", px, tag, a["reason"], usd=usd, deadline=deadline)
        if b["pos"].get(k, 0.0) <= 0:
            return "refused: there is nothing to sell"
        return self.send(tid, sym, "sell", px, tag, a["reason"], qty=self.sell_qty(tid, k, a["share"]), deadline=deadline)

    # ---- the whole run
    def run(self):
        s = self.state
        if not self.b.has_key():
            p = self.rec.dir / "summary.json"  # written once, so the timer does not add a new record every run while it waits
            if self.rec.load("summary.json", {}).get("status") != "waiting_for_key":
                self.finish("waiting_for_key", "No practice trades yet. The desk starts when the practice key is in place.")
            return 0
        try:
            self.acct = self.b.account(); self.acct_cash = books.num(self.acct.get("cash")); self.read_broker()
        except Refused as e:
            first = not s.get("key_refused"); s["key_refused"] = True
            if first:
                self.problem(None, f"The broker refused the practice key (HTTP {e.status}).")
            self.finish("halted", "The broker refused the practice key. Check that it is the key of a practice account."); return 1 if first else 0
        except Unclear as e:
            s["unread"] = s.get("unread", 0) + 1; self.problem(None, f"Could not reach the broker ({e}). Nothing was done on this run.", once_key="unread")
            late = s["unread"] == int(self.cfg["practice_unread_runs_before_alarm"])
            self.rec.save("state.json", s); return 1 if late else 0
        s["key_refused"] = False; s["unread"] = 0; s["started_utc"] = s.get("started_utc") or iso(self.now)
        s["account_facts"] = {k: self.acct.get(k) for k in ("status", "crypto_status", "trading_blocked", "account_blocked", "currency")}
        self.load_picks(); self.check_books(); self.read_prices(); self.start_rows()
        for t in self.traders:
            if t["id"] in self.blocked:
                continue
            try:
                self.decide_rule(t) if t["kind"] == "rule" else self.decide_ai(t)
            except Exception as e:  # a fault in this program: stop that trader for this run instead of guessing
                self.blocked[t["id"]] = f"The program hit a fault it did not expect ({type(e).__name__}: {str(e)[:120]})."
                self.alarm("fault:" + t["id"], t["id"], "Stopped. " + self.blocked[t["id"]])
        waited = 0
        while self.sent and waited < self.cfg["practice_fill_wait_seconds"]:
            self.sleep(3); waited += 3
            try:
                self.read_broker()
            except (Unclear, Refused):
                continue
            if all(self.by_cid.get(c, {}).get("status") in books.FINAL for c in self.sent):
                break
        if self.sent:
            alarms, new = set(self.alarms), self.new_alarm; keep = dict(self.blocked)
            self.check_books(); self.blocked.update(keep); self.alarms |= alarms; self.new_alarm = self.new_alarm or new
        s["alarms"] = sorted(self.alarms); self.points(); self.finish(None, None)
        return 1 if self.new_alarm else 0

    def start_rows(self):
        """The first time a trader is seen with a price for its yardstick, write that price down. 'Just holding' is measured from it."""
        have = {r["trader"] for r in self.rec.rows("starts")}
        for t in self.traders:
            p = self.price(t["benchmark"]) if t.get("benchmark") else None
            if t["id"] not in have and p:
                self.rec.add("starts", dict(utc=iso(self.now), trader=t["id"], benchmark=t["benchmark"], price=p))

    def hold_values(self):
        out = {}
        st = {r["trader"]: r for r in self.rec.rows("starts")}
        for t in self.traders:
            r = st.get(t["id"]); p = self.price(r["benchmark"], fresh=False) if r else None
            out[t["id"]] = self.start * p / r["price"] * (1 - self.fee_rate(r["benchmark"])) if p else (None if r else self.start)
        return out, st

    def points(self):
        hour = self.now.strftime("%Y-%m-%dT%H"); rows = self.rec.rows("points")
        if rows and rows[-1]["utc"][:13] == hour:
            return
        hold, _ = self.hold_values(); v = {t["id"]: round(self.value(t["id"]), 2) for t in self.traders}
        self.rec.add("points", dict(utc=iso(self.now), value_usd=round(sum(v.values()), 2), hold_value_usd=round(sum(h or self.start for h in hold.values()), 2),
                                    traders=v, hold={k: (round(h, 2) if h else None) for k, h in hold.items()}))

    def finish(self, status, text):
        self.rec.save("state.json", self.state)
        if self.rec.defer_writes and status is None:
            self.rec._last_run = self
        else:
            self.rec.save("summary.json", self.summary(status, text))
        if self.checkpoint and status is None:
            try:
                self.checkpoint()
            except Exception:
                pass  # the timer's own last step saves the records again and fails loudly if it cannot

    def summary(self, status, text):
        cfg, journal = self.cfg, {}
        for r in self.rec.rows("orders"):
            journal.setdefault(r["cid"], {}).update(r)
        hold, starts = self.hold_values() if self.books else ({t["id"]: self.start for t in self.traders}, {})
        out_t, all_orders, all_closed = [], [], []
        for t in self.traders:
            tid = t["id"]; b = self.books.get(tid) or books.new_book(self.start); value = self.value(tid) if self.books else self.start
            for o in b["orders"]:
                j = journal.get(o["client_order_id"], {}); ap = j.get("assumed_price"); fp = o["fill_price"]
                o["assumed_price"] = ap; o["reason"] = j.get("reason")
                o["gap_bps"] = round((fp - ap) / ap * 1e4 * (1 if o["side"] == "buy" else -1), 2) if (ap and fp) else None
            seen = {o["client_order_id"] for o in b["orders"]}
            for cid, j in journal.items():  # intents the broker does not list: refused, not sent, or unclear
                if j["trader"] == tid and cid not in seen and j["event"] != "not_sent":
                    b["orders"].append(dict(utc=j["utc"], filled_utc=None, trader=tid, symbol=j["symbol"], side=j["side"], client_order_id=cid, order_id=None, broker_status=None, qty=None,
                                            asked_qty=j.get("qty"), asked_usd=j.get("usd"), fill_price=None, notional_usd=None, fee_added_usd=None, assumed_price=j.get("assumed_price"),
                                            reason=j.get("reason"), gap_bps=None, status={"rejected": "rejected", "cleared": "cleared by hand"}.get(j["event"], "unclear")))
            pos = []
            for k, q in sorted(b["pos"].items()):
                sym = b["sym"][k]; p = self.price(sym, fresh=False); tr = b["trades"].get(k, {}); x = self.exit_for(tid, k) if t["kind"] == "ai" else None
                net = tr.get("cost_usd", 0.0) - tr.get("back_usd", 0.0)
                pos.append(dict(symbol=sym, qty=q, price=p, value_usd=round(q * p, 2) if p else None, opened_utc=tr.get("opened_utc"), cost_usd=round(net, 2),
                                gain_usd=round(q * p - net, 2) if p else None, exit={k2: x[k2] for k2 in ("stop", "target", "by_utc") if k2 in x} if x else None))
            good = [(pid, obj) for pid, obj, errs in self.pick_files.get(tid, []) if not errs]
            wins = sum(c["result"] == "win" for c in b["closed"]); losses = sum(c["result"] == "loss" for c in b["closed"]); h = hold.get(tid)
            out_t.append(dict(id=tid, name=t["name"], kind=t["kind"], model=t.get("model"), method=t.get("method"), label="not passed", halted=tid in self.blocked, halt_reason=self.blocked.get(tid),
                              started=tid in starts, start_usd=self.start, value_usd=round(value, 2), gain_usd=round(value - self.start, 2), gain_pct=value / self.start - 1,
                              benchmark=t.get("benchmark"), hold_value_usd=round(h, 2) if h else None, hold_gain_pct=(h / self.start - 1) if h else None, cash_usd=round(b["cash"], 2),
                              positions=pos, target_weight=self.state.get("target", {}).get(tid), orders_count=len(b["orders"]), closed_trades=len(b["closed"]), wins=wins, losses=losses,
                              win_rate=(wins / len(b["closed"]) if b["closed"] else None), realised_usd=round(sum(c["gain_usd"] for c in b["closed"]), 2), fees_added_usd=round(b["fees"], 2),
                              last_pick=dict(pick_id=good[-1][0], made_utc=good[-1][1]["made_utc"], thesis=good[-1][1]["thesis"], sources=good[-1][1].get("sources", [])) if good else None))
            all_orders += b["orders"]; all_closed += b["closed"]
        out_t.sort(key=lambda r: -r["gain_pct"])
        tot_start = self.start * len(self.traders); tot = sum(r["value_usd"] for r in out_t); n = len(all_closed); wins = sum(c["result"] == "win" for c in all_closed)
        losses = sum(c["result"] == "loss" for c in all_closed)
        if status is None:
            stopped = [r["id"] for r in out_t if r["halted"]]; status = "halted" if (stopped or self.sym_blocked) else "running"
            text = ("Something needs a look: " + ", ".join(stopped + sorted(self.sym_blocked)) + ". The reason is written under it.") if status == "halted" else \
                   "Running on a timer with pretend money."
        return dict(made_utc=iso(self.now), status=status, status_text=text, last_check_utc=iso(self.now) if status != "waiting_for_key" else None,
                    account=dict(pretend_start_usd=tot_start, value_usd=round(tot, 2), gain_usd=round(tot - tot_start, 2), gain_pct=(tot / tot_start - 1) if tot_start else 0.0),
                    traders=out_t, symbols_stopped=[dict(symbol=k, reason=v) for k, v in sorted(self.sym_blocked.items())],
                    totals=dict(orders=len(all_orders), closed_trades=n, wins=wins, losses=losses, flat=n - wins - losses, win_rate=(wins / n if n else None),
                                realised_usd=round(sum(c["gain_usd"] for c in all_closed), 2), fees_added_usd=round(sum(r["fees_added_usd"] for r in out_t), 2)),
                    orders=sorted(all_orders, key=lambda o: o["utc"] or "", reverse=True)[:300], closed=sorted(all_closed, key=lambda c: c["closed_utc"], reverse=True)[:300],
                    points=[dict(utc=p["utc"], value_usd=p["value_usd"], hold_value_usd=p["hold_value_usd"], traders=p["traders"]) for p in self.rec.rows("points")][-1000:],
                    problems=list(reversed(self.rec.rows("problems")))[:50],
                    notes=dict(gap="Gap is how far the fill was from the newest price the program had read when it sent the order, in basis points. Plus means the fill was worse for the account.",
                               fee="The fee on crypto fills is added by this program from config/thresholds.yaml (practice_crypto_fee_bps_added).",
                               not_added="Not counted: regulatory fees on stock sells, and dividends. The practice account does not model them. Just holding is shown without dividends too.",
                               win="A trade is counted when a holding goes back to nothing. It is a win if more dollars came back than went in, fees included."))


def git_checkpoint(folder):
    """Save the records folder to its branch now. Raises if it cannot. The key is not passed to git."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("ALPACA")}
    def git(*a):
        return subprocess.run(["git", "-C", str(folder)] + list(a), env=env, capture_output=True, timeout=60)
    def save():
        if git("add", "-A").returncode != 0:
            raise RuntimeError("add failed")
        if git("diff", "--cached", "--quiet").returncode != 0 and git("commit", "-q", "-m", "Practice desk records " + iso(dt.datetime.now(UTC))).returncode != 0:
            raise RuntimeError("commit failed")
        left = git("status", "--porcelain", "--ignored", "--", ".")  # ignored files count too: a record git skips is a record not saved
        if left.returncode != 0 or left.stdout.strip():
            raise RuntimeError("records not all committed")
        for i in range(3):
            if git("push", "-q", "origin", "HEAD:practice-records").returncode == 0:
                return
            time.sleep(2 * (i + 1))
        raise RuntimeError("push failed")
    return save


class Market:
    """The price reads the desk needs, from practice/market.py, through the broker layer's allowed list."""
    def __init__(self, get):
        import market
        self.get, self.mk = get, market
    def prices(self, symbols): return self.mk.prices(self.get, symbols)
    def daily_bars(self, symbol, start): return self.mk.daily_bars(self.get, symbol, start)
    def asset(self, symbol): return self.mk.asset(self.get, symbol)
    def clock(self): return self.mk.market_clock(self.get)
    def calendar(self, first, last): return self.mk.calendar(self.get, first, last)


if __name__ == "__main__":
    import market
    rec_dir = os.environ.get("PRACTICE_RECORDS_DIR", "practice_records"); b = Broker(extra_reads=market.READS)
    cp = git_checkpoint(rec_dir) if os.environ.get("PRACTICE_SAVE") == "git" else None
    sys.exit(Run(b, Market(b.get), Records(rec_dir), config(), roster(), picks_dir=os.environ.get("PRACTICE_PICKS_DIR"), checkpoint=cp, clear=os.environ.get("PRACTICE_CLEAR") or None).run())
