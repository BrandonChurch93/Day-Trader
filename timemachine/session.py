"""One time machine session: one trader alone in one pretend account, over a window of recorded days, with a wake schedule.

The live practice desk program (practice/trader.py: Run, with practice/books.py and practice/picks.py) runs unchanged
inside a session. Only two things are swapped: the broker is timemachine/simbroker.py: SimBroker, and `now` is the
simulated time. A session folder under $TM_RUNS holds everything, so a stopped server loses nothing:
  session.json   what the session is (never changed after it is made)
  progress.json  which wake it is at, and how far the desk runs after the last pick got
  account.json   the pretend account: cash, holdings, every order
  records/       the desk's own records, exactly as on the live desk (orders.jsonl, picks.jsonl, summary.json, ...)
  picks/<TRADER>/<pick id>.json   the trader's picks, exactly as the live desk reads them
  packets/<k>.json  what the trader was shown at wake k (made once, then served again as it is)
  looks.jsonl    every extra lookup
  result.json    written when the last wake is done
Every session ever made is one line in timemachine/SESSIONS.jsonl (env TM_SESSIONS_LOG for tests). Standard library only."""
import datetime as dt, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import books, picks, market as M, trader as T  # the live desk's own code, unchanged
from timemachine.tape import Tape
from timemachine.simdata import SimData
from timemachine.simbroker import SimBroker

UTC, NY = dt.timezone.utc, ZoneInfo("America/New_York")
TM_KEYS = ["tm_account_start_usd", "tm_stock_half_spread_bps", "tm_crypto_half_spread_bps", "tm_max_share_of_minute_volume", "tm_crypto_max_share_of_minute_volume",
           "tm_tick_minutes", "tm_stock_wake_times_ny", "tm_crypto_wake_hours_utc", "tm_max_looks_per_wake", "tm_look_max_bars", "tm_look_max_days", "tm_skip_idle_ticks"]
HARD_LINES = ["The date is the date in this packet. You know nothing that happened after it.",
              "No web search, no web fetch, and no reading any file outside your own notes folder.",
              "Never guess from memory what a price did later."]
LIMITS = ["Fills are assumed from recorded minute bars (next minute's open, a fixed half spread, a cap on the share of the minute's volume for stocks, and for crypto only when tm_crypto_max_share_of_minute_volume is set). They are not real fills.",
          "A model may still know this period if it falls before the model's knowledge line. UNKNOWN how much that helps it.",
          "The no-search and no-file rule is given by instruction. It is not enforced by this program.",
          "News headlines and summaries are as first recorded. A story edited after it was first published is marked edited_later, and its text may hold the later edit.",
          "The stock list is today's list. Stocks delisted during the window are missing.",
          "Prices are raw, not adjusted for splits or dividends. A split inside a held position is not handled. Dividends are not paid.",
          "The screener (movers, most active) is rebuilt from bars. It is not Alpaca's own.",
          "Tradable and fractionable are assumed true for any symbol the tape has bars for on that date. The real flags are not on the data address.",
          "The time machine refuses a stock order while the market is closed. The real Alpaca would queue it for the open.",
          "A stock order is refused if the tape has no minute bars for it that day.",
          "Sell orders by dollar amount are refused. Buying power is cash less open buys."]


def runs_dir():
    return Path(os.environ.get("TM_RUNS", "/home/user/workspace/rig/tm_runs"))


def sessions_log():
    return Path(os.environ.get("TM_SESSIONS_LOG", str(ROOT / "timemachine" / "SESSIONS.jsonl")))


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    return picks.parse_t(s)


def tm_config(path=ROOT / "config" / "thresholds.yaml"):
    """The tm_ keys, read the way practice/trader.py: config() reads its keys. A value may be a number or a [list] of numbers."""
    out, key = {}, None
    for line in open(path):
        m = re.match(r"^([a-z0-9_]+):\s*$", line)
        if m:
            key = m.group(1); continue
        m = re.match(r"^  value:\s*(.*)$", line)
        if m and key in TM_KEYS:
            v = m.group(1).strip()
            out[key] = [float(x) for x in v.strip("[]").split(",") if x.strip()] if v.startswith("[") else float(v)
    bad = [k for k in TM_KEYS if k not in out]
    assert not bad, f"missing in config/thresholds.yaml: {bad}"
    assert all(abs(x * 2 - round(x * 2)) < 1e-9 for x in out["tm_stock_wake_times_ny"]), "tm_stock_wake_times_ny must sit on half-hour marks"
    return out


def full_config():
    """The practice_ keys and the tm_ keys together. In a session the one trader's budget is the whole pretend account."""
    cfg = dict(T.config()); cfg.update(tm_config())
    cfg["practice_amount_per_trader_usd"] = cfg["tm_account_start_usd"]
    assert cfg["tm_tick_minutes"] * 60 > cfg["practice_fill_wait_seconds"], "a desk run's wait for fills must end before the next tick"
    return cfg


def sha256_file(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except OSError:
        return None


def git_commit():
    def g(*a):
        try:
            return subprocess.run(["git", "-C", str(ROOT)] + list(a), capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception:
            return ""
    return dict(commit=g("rev-parse", "HEAD") or None, dirty=bool(g("status", "--porcelain", "--", "timemachine", "practice", "config")))


def crypto_symbols(tape, now):
    return tape._crypto_symbols_as_of(int(now.timestamp()))


def make_wakes(tape, market, start_date, end_date, cfg):
    d0, d1 = dt.date.fromisoformat(start_date), dt.date.fromisoformat(end_date)
    out = []
    if market == "crypto":
        d = d0
        while d <= d1:
            for h in cfg["tm_crypto_wake_hours_utc"]:
                out.append(dt.datetime(d.year, d.month, d.day, tzinfo=UTC) + dt.timedelta(hours=h))
            d += dt.timedelta(days=1)
        end = dt.datetime(d1.year, d1.month, d1.day, tzinfo=UTC) + dt.timedelta(days=1)
    else:
        rows = tape.sessions(start_date, end_date)
        assert rows, f"the tape has no stock sessions from {start_date} to {end_date}"
        for date, op, cl in rows:
            y, m, dd = (int(x) for x in date.split("-"))
            for x in cfg["tm_stock_wake_times_ny"]:
                t = dt.datetime(y, m, dd, int(x), int(round((x % 1) * 60)), tzinfo=NY).astimezone(UTC)
                if op <= t < cl:
                    out.append(t)
        tick = int(cfg["tm_tick_minutes"] * 60); cl = rows[-1][2]
        end = dt.datetime.fromtimestamp(math.ceil(cl.timestamp() / tick) * tick, UTC)  # the first tick at or after the last close
    return sorted(set(out)), end


def built_bars(tape, symbol, secs, start, now, limit):
    """Half-hour or hour bars for a coin, built from the recorded minutes. Only buckets that have ended by `now` are returned,
    so the newest bar never holds a minute the trader could not have seen. Oldest first, at most `limit`."""
    end_ts = int(now.timestamp()) // secs * secs                      # the start of the bucket that is still open
    start_ts = max(int(start.timestamp()) // secs * secs, end_ts - limit * secs)
    if start_ts >= end_ts:
        return []
    mins = tape.bars(symbol, "1Min", dt.datetime.fromtimestamp(start_ts, UTC), dt.datetime.fromtimestamp(end_ts, UTC))
    out = {}
    for m in mins:
        ts = int(m["t"].timestamp()) // secs * secs
        if ts < start_ts or ts >= end_ts:
            continue
        x = out.get(ts)
        if x is None:
            out[ts] = dict(t=dt.datetime.fromtimestamp(ts, UTC), o=m["o"], h=m["h"], l=m["l"], c=m["c"], v=m.get("v") or 0.0)
        else:
            x["h"] = max(x["h"], m["h"]); x["l"] = min(x["l"], m["l"]); x["c"] = m["c"]; x["v"] += m.get("v") or 0.0
    return [out[k] for k in sorted(out)][-limit:]


def create(session_id, trader_id, model, method_path, start_date, end_date, wakes=None, market="crypto", watch=None, benchmark=None, tape=None, note=None, news=False):
    """Makes the session folder and counts the session in SESSIONS.jsonl. Returns the folder."""
    assert re.fullmatch(r"[A-Z0-9-]{2,12}", trader_id), "trader id: 2 to 12 capital letters, digits or dashes"
    assert re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", session_id) and ".." not in session_id, "session id: 3 to 80 letters, digits, dot, dash or underscore"
    assert market in ("crypto", "stocks")
    tape = tape or Tape(); cfg = full_config(); folder = runs_dir() / session_id
    if folder.exists():
        raise FileExistsError(f"session {session_id} already exists")
    if wakes:
        wl = sorted({parse(w) if isinstance(w, str) else w for w in wakes})
        _, end = make_wakes(tape, market, start_date, end_date, cfg)
    else:
        wl, end = make_wakes(tape, market, start_date, end_date, cfg)
    assert wl and wl[-1] < end, "no wake falls inside the window"
    if watch is None:
        watch = crypto_symbols(tape, wl[0]) if market == "crypto" else []
    benchmark = benchmark or (("BTC/USD" if (not watch or "BTC/USD" in watch) else watch[0]) if market == "crypto" else "SPY")
    mp = Path(method_path.split("#")[0]); mp = mp if mp.is_absolute() else ROOT / mp
    chash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    meta = dict(session=session_id, trader=trader_id, model=model, method=method_path, method_sha256=sha256_file(mp), market=market, window=dict(start=start_date, end=end_date),
                wakes=[iso(w) for w in wl], end_utc=iso(end), watch=list(watch), benchmark=benchmark, config=cfg, config_hash=chash,
                created_utc=iso(dt.datetime.now(UTC)), git=git_commit(), tape=str(tape.path), note=note, news=bool(news))
    folder.mkdir(parents=True)
    (folder / "session.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n")
    line = dict(session=session_id, trader=trader_id, model=model, method=method_path, method_sha256=meta["method_sha256"], market=market, window=meta["window"],
                wakes=dict(count=len(wl), first=meta["wakes"][0], last=meta["wakes"][-1]), config_hash=chash, created_utc=meta["created_utc"], git_commit=meta["git"]["commit"],
                git_dirty=meta["git"]["dirty"], runs_folder=str(folder))
    log = sessions_log(); log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n"); f.flush(); os.fsync(f.fileno())
    save_json(folder / "progress.json", dict(k=0, phase="waiting", tick_i=0, clock=meta["wakes"][0], bad={}, looks={}, steps=[], done=False,
                                             ticks_run=0, ticks_skipped=0, wall_seconds=0.0))
    return folder


def save_json(p, obj):
    p = Path(p); tmp = p.with_suffix(p.suffix + ".tmp"); tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n"); os.replace(tmp, p)


class Done(Exception):
    pass


class Session:
    def __init__(self, session_id, tape=None, resume=True):
        self.dir = runs_dir() / session_id
        if not (self.dir / "session.json").exists():
            raise KeyError(f"no session {session_id}")
        self.meta = json.loads((self.dir / "session.json").read_text()); self.cfg = self.meta["config"]
        self.prog = json.loads((self.dir / "progress.json").read_text())
        self.tape = tape or Tape(self.meta.get("tape"))
        self.wakes = [parse(w) for w in self.meta["wakes"]]; self.end = parse(self.meta["end_utc"]); self.N = len(self.wakes)
        self.now = parse(self.prog["clock"]); self.tid = self.meta["trader"]
        self.sd = SimData(self.tape, lambda: self.now)
        self.sb = SimBroker(self.tape, lambda: self.now, self.cfg, self.dir / "account.json", data=self.sd)
        self.mkt = T.Market(self.sd.get); self.rec = T.Records(self.dir / "records")
        self.trader = dict(id=self.tid, name=f"{self.tid} replay", kind="ai", model=self.meta["model"], method=self.meta["method"], benchmark=self.meta["benchmark"])
        self.crash_after = None  # tests only: stop the run after this many ticks, as if the server died
        if resume and self.prog["phase"] == "ticking":
            self._ticks()

    # ---- small helpers
    def save(self):
        self.prog["clock"] = iso(self.now); save_json(self.dir / "progress.json", self.prog)

    def done(self):
        return bool(self.prog["done"])

    def pick_id(self, k=None):
        return self.wakes[self.prog["k"] if k is None else k].strftime("%Y%m%dT%H%MZ")

    def next_time(self, k):
        return self.wakes[k + 1] if k + 1 < self.N else self.end

    def _run(self, now):
        return T.Run(self.sb, self.mkt, self.rec, self.cfg, [self.trader], picks_dir=self.dir, now=now, sleep=self._sleep, checkpoint=lambda: None)

    def _sleep(self, seconds):
        self.now = self.now + dt.timedelta(seconds=seconds)

    def status(self):
        k = self.prog["k"]
        return dict(session=self.meta["session"], trader=self.tid, done=self.done(), status="DONE" if self.done() else "waiting for a pick", step=min(k + 1, self.N), of=self.N,
                    utc=iso(self.now), looks_left=None if self.done() else self.looks_left(), bad_attempts=self.prog["bad"].get(str(k), 0))

    def looks_left(self):
        return int(self.cfg["tm_max_looks_per_wake"]) - self.prog["looks"].get(str(self.prog["k"]), 0)

    # ---- the tick schedule after one wake
    def schedule(self, k):
        start, stop, last = self.wakes[k], self.next_time(k), k + 1 == self.N
        tick = int(self.cfg["tm_tick_minutes"] * 60)
        t = math.ceil(start.timestamp() / tick) * tick; grid = [start.timestamp()] if t != start.timestamp() else []
        while t < stop.timestamp() or (last and t <= stop.timestamp()):
            grid.append(t); t += tick
        grid = sorted(set(int(x) for x in grid))
        if self.meta["market"] == "crypto":
            out = grid
        else:
            d0 = start.astimezone(NY).date() - dt.timedelta(days=1); d1 = stop.astimezone(NY).date()
            ss = self.tape.sessions(d0.isoformat(), d1.isoformat()); after = {math.ceil(cl.timestamp() / tick) * tick for _, _, cl in ss}
            out = [x for x in grid if x in after or any(op.timestamp() <= x < cl.timestamp() for _, op, cl in ss)]
            if int(start.timestamp()) not in out:
                out.insert(0, int(start.timestamp()))
            if last and int(stop.timestamp()) not in out:
                out.append(int(stop.timestamp()))
        return [dt.datetime.fromtimestamp(x, UTC) for x in out]

    def idle(self):
        """True when a desk run could do nothing: nothing held, no open order, nothing left in any pick, and the yardstick price written down."""
        if self.sb.holding() or self.sb.has_open():
            return False
        if not self.rec.rows("starts"):
            return False
        done = {(r["pick_id"], r["n"]) for r in self.rec.rows("picks")}
        folder = self.dir / "picks" / self.tid
        for f in sorted(folder.glob("*.json")) if folder.is_dir() else []:
            obj = json.loads(f.read_text())
            if any((f.stem, n) not in done for n in range(len(obj.get("actions", [])))):
                return False
        return True

    def _ticks(self):
        k = self.prog["k"]; ticks = self.schedule(k); t_wall = time.time(); skip_ok = bool(self.cfg["tm_skip_idle_ticks"]); ran = 0
        for i in range(self.prog["tick_i"], len(ticks)):
            t = ticks[i]; self.now = t
            must = i == 0 or (k + 1 == self.N and i == len(ticks) - 1) or ticks[i - 1].strftime("%Y%m%d%H") != t.strftime("%Y%m%d%H")
            if skip_ok and not must and self.idle():
                self.prog["ticks_skipped"] += 1
            else:
                self._run(t).run(); self.prog["ticks_run"] += 1
            self.prog["tick_i"] = i + 1; self.save(); ran += 1
            if self.crash_after is not None and ran >= self.crash_after:
                self.prog["wall_seconds"] += time.time() - t_wall; self.save()
                raise RuntimeError("pretend crash (test)")
        step = self.prog["steps"][-1]; pid = step["pick_id"]
        step["outcome"] = [dict((x, r.get(x)) for x in ("utc", "n", "outcome", "symbol", "side", "why")) for r in self.rec.rows("picks") if pid and r["pick_id"] == pid]
        self.prog["k"] = k + 1; self.prog["phase"] = "waiting"; self.prog["tick_i"] = 0
        self.prog["wall_seconds"] += time.time() - t_wall
        if self.prog["k"] >= self.N:
            self.finish()
        else:
            self.now = self.wakes[self.prog["k"]]; self.save()

    # ---- what the trader sees
    def book(self):
        """The trader's book as of now, worked out by the live desk's own code (books.derive and Run.summary), with nothing written."""
        r = self._run(self.now); r.acct = self.sb.account(); r.read_broker(); r.load_picks(); r.read_prices()
        s = r.summary(None, None); row = s["traders"][0]; b = r.books.get(self.tid) or books.new_book(r.start)
        return dict(cash_usd=row["cash_usd"], value_usd=row["value_usd"], start_usd=row["start_usd"], gain_usd=row["gain_usd"], gain_pct=row["gain_pct"],
                    positions=row["positions"], open_orders=b["open"], closed_trades=row["closed_trades"], wins=row["wins"], losses=row["losses"],
                    realised_usd=row["realised_usd"], fees_added_usd=row["fees_added_usd"],
                    benchmark=dict(symbol=row["benchmark"], hold_value_usd=row["hold_value_usd"], hold_gain_pct=row["hold_gain_pct"]), orders=s["orders"][:30])

    def last_pick(self):
        k = self.prog["k"]
        if k == 0:
            return None
        st = self.prog["steps"][k - 1]; since = st["utc"]
        orders = [o for o in json.loads((self.dir / "records" / "summary.json").read_text())["orders"] if (o.get("utc") or "") >= since] \
            if (self.dir / "records" / "summary.json").exists() else []
        probs = [p for p in self.rec.rows("problems") if p["utc"] >= since]
        return dict(pick_id=st["pick_id"], wake_utc=since, no_pick_why=st.get("no_pick_why"), outcome=st.get("outcome", []), orders_since=orders, problems_since=probs)

    def _feed_get(self, base, path, params=None):
        """A crypto session is shown nothing about stocks, whatever the tape holds."""
        if self.meta["market"] == "crypto" and path == "/v1beta1/screener/stocks/movers":
            return {"gainers": [], "losers": [], "last_updated": iso(self.now), "market_type": "stocks"}
        if self.meta["market"] == "crypto" and path == "/v1beta1/screener/stocks/most-actives":
            return {"most_actives": [], "last_updated": iso(self.now)}
        return self.sd.get(base, path, params)

    def packet(self, fresh=False):
        if self.done():
            raise Done()
        k = self.prog["k"]; p = self.dir / "packets" / f"{k}.json"
        if p.exists() and not fresh:
            return json.loads(p.read_text())
        bk = self.book(); held = [x["symbol"] for x in bk["positions"]]
        feed = M.build_feed(self._feed_get, self.meta["watch"], held, self.now)
        if not self.meta.get("news"):
            feed["news"] = []   # a session made without news shows none, whatever the tape holds
        all_syms = list(dict.fromkeys(list(self.meta["watch"]) + held))
        edited = {(iso(a["created"]) if isinstance(a["created"], dt.datetime) else a["created"], a["headline"].strip()) for a in self.tape.news(self.now, symbols=all_syms or None, limit=50) if a.get("edited_later")}
        for a in feed["news"]:
            if (a["utc"], a["headline"]) in edited or (a["utc"], a["headline"].strip()) in edited:
                a["edited_later"] = True
        made, nxt = self.now, self.next_time(k)
        exp = min(nxt, made + dt.timedelta(hours=self.cfg["practice_pick_max_life_hours"]))
        out = dict(session=self.meta["session"], trader=self.tid, utc=iso(self.now), step=k + 1, of=self.N, next_wake_utc=iso(nxt), is_last=k + 1 == self.N,
                   market=self.meta["market"], watch=self.meta["watch"], feed=feed, book=bk, last_pick=self.last_pick(), looks_left=self.looks_left(),
                   pick_id=self.pick_id(), hard_lines=HARD_LINES,
                   pick_template=dict(trader=self.tid, made_utc=iso(made), expires_utc=iso(exp), thesis="...", actions=[], exits=[]),
                   no_pick_form={"no_pick": True, "why": "..."}, pick_format=picks.__doc__,
                   notes=["Fills happen at the open of the next minute after the desk sends the order, with a spread added. The desk runs every "
                          f"{self.cfg['tm_tick_minutes']:g} simulated minutes until the next wake and enforces your exits then.",
                          "If you leave out trader, made_utc or expires_utc, the values in pick_template are used."])
        if fresh:
            return out
        p.parent.mkdir(exist_ok=True); save_json(p, out)
        return json.loads(p.read_text())

    # ---- extra lookups, as of now only
    def look(self, what, symbol=None, symbols=None, timeframe="1Day", days=None):
        if self.done():
            raise Done()
        k = str(self.prog["k"])
        if self.looks_left() <= 0:
            return dict(ok=False, error=f"No lookups left at this wake (the limit is tm_max_looks_per_wake). Make your pick.")
        days = min(float(days if days is not None else 5), self.cfg["tm_look_max_days"]); start = self.now - dt.timedelta(days=days)
        syms = [s.strip() for s in (symbols or "").split(",") if s.strip()]
        if self.meta["market"] == "crypto" and any("/" not in x for x in syms + ([symbol] if symbol else [])):
            return dict(ok=False, error="This is a crypto session. Lookups are for crypto pairs such as BTC/USD only.")
        if what == "bars":
            assert timeframe in ("1Min", "30Min", "1Hour", "1Day") and symbol, "bars needs symbol and timeframe 1Min, 30Min, 1Hour or 1Day"
            if timeframe == "1Min" and "/" not in symbol:
                d = start.astimezone(NY).date()
                while d <= self.now.astimezone(NY).date():
                    if self.tape.session(d.isoformat()) and not self.tape.has_minutes(symbol, d.isoformat()):
                        self.tape.ensure_minutes(symbol, d.isoformat())
                    d += dt.timedelta(days=1)
            if timeframe in ("30Min", "1Hour") and "/" in symbol:
                rows = built_bars(self.tape, symbol, 1800 if timeframe == "30Min" else 3600, start, self.now, int(self.cfg["tm_look_max_bars"]))
            else:
                rows = self.tape.bars(symbol, "30Min" if timeframe == "1Hour" else timeframe, start, self.now, limit=int(self.cfg["tm_look_max_bars"]))
            data = [dict(b, t=iso(b["t"])) for b in rows]
        elif what == "news" and not self.meta.get("news"):
            return dict(ok=False, error="This session has no news. It trades from prices alone.")
        elif what == "news":
            data = [{k2: (iso(v) if isinstance(v, dt.datetime) else v) for k2, v in a.items() if k2 != "updated"}  # the edit time may be after now: never shown
                    for a in self.tape.news(self.now, symbols=syms or None, since_utc=start, limit=50)]
        elif what == "price":
            data = {s: {k2: (iso(v) if isinstance(v, dt.datetime) else v) for k2, v in x.items()} for s, x in self.tape.snapshot(syms, self.now).items()}
        else:
            return dict(ok=False, error="what must be bars, news or price")
        self.prog["looks"][k] = self.prog["looks"].get(k, 0) + 1; self.save()
        self.rec.dir.parent.joinpath("looks.jsonl").open("a").write(json.dumps(dict(k=int(k), utc=iso(self.now), what=what, symbol=symbol, symbols=syms, timeframe=timeframe,
                                                                                    days=days, rows=len(data)), sort_keys=True) + "\n")
        return dict(ok=True, utc=iso(self.now), what=what, data=data, looks_left=self.looks_left())

    # ---- the trader's answer, then the clock moves
    def bad(self, errs):
        k = str(self.prog["k"]); self.prog["bad"][k] = self.prog["bad"].get(k, 0) + 1; self.save()
        return dict(ok=False, errors=errs, bad_attempts=self.prog["bad"][k], note="Nothing was traded and the clock did not move. Fix the pick and send it again.")

    def submit(self, body):
        if self.done():
            raise Done()
        k = self.prog["k"]; pid = self.pick_id(); now = self.now
        if not isinstance(body, dict):
            return self.bad(["The body must be a JSON object."])
        no_pick = "no_pick" in body
        if no_pick:
            if body.get("no_pick") is not True or set(body) - {"no_pick", "why"} or not (isinstance(body.get("why", ""), str) and len(body.get("why", "")) <= 2000):
                return self.bad(['A no-pick is exactly {"no_pick": true, "why": "..."}.'])
            p = None
        else:
            p = dict(body)
            if p.get("trader", self.tid) != self.tid:
                return self.bad([f"This session belongs to trader {self.tid}. A pick for another trader is refused."])
            tpl = self.packet()["pick_template"]
            for f in ("trader", "made_utc", "expires_utc"):
                p.setdefault(f, tpl[f])
            errs = picks.validate(p, self.tid, pid, now, self.cfg["practice_pick_max_life_hours"], self.cfg["practice_pick_max_actions"])
            if errs:
                return self.bad(errs)
        syms = sorted({a["symbol"] for a in (p or {}).get("actions", [])} | {x["symbol"] for x in (p or {}).get("exits", [])})
        hk = self.sb.holding(); held = sorted({o["symbol"] for o in self.sb.s["orders"] if o["symbol"].replace("/", "") in hk})
        if self.meta["market"] == "stocks" or any("/" not in s for s in syms):
            self.ensure_minutes(sorted(set(syms) | set(held)), now, self.next_time(k))
        ref = {s: x["price"] for s, x in self.tape.snapshot(syms, now).items()} if syms else {}
        if p is not None:
            f = self.dir / "picks" / self.tid / f"{pid}.json"; f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(p, indent=1, sort_keys=True) + "\n")
        step = dict(k=k, utc=iso(now), pick_id=None if no_pick else pid, no_pick_why=body.get("why") if no_pick else None, pick=p, ref_prices=ref,
                    looks=self.prog["looks"].get(str(k), 0), bad_attempts=self.prog["bad"].get(str(k), 0))
        self.prog["steps"].append(step); self.prog["phase"] = "ticking"; self.prog["tick_i"] = 0; self.save()
        self._ticks()
        return dict(ok=True, pick_id=step["pick_id"], step=k + 1, of=self.N, outcome=self.prog["steps"][k].get("outcome", []), done=self.done(),
                    next_utc=None if self.done() else iso(self.now))

    def ensure_minutes(self, symbols, t0, t1):
        for s in symbols:
            if "/" in s:
                continue
            d = t0.astimezone(NY).date()
            while d <= t1.astimezone(NY).date():
                if self.tape.session(d.isoformat()) and not self.tape.has_minutes(s, d.isoformat()):
                    self.tape.ensure_minutes(s, d.isoformat())
                d += dt.timedelta(days=1)

    # ---- the end
    def finish(self):
        summ = json.loads((self.dir / "records" / "summary.json").read_text())
        row = summ["traders"][0]; starts = self.rec.rows("starts")
        meta = {k: v for k, v in self.meta.items() if k != "config"}
        res = dict(session=meta, config=self.cfg, summary=summ, steps=self.prog["steps"],
                   benchmark_hold=dict(symbol=row["benchmark"], start=starts[0] if starts else None, hold_value_usd=row["hold_value_usd"], hold_gain_pct=row["hold_gain_pct"],
                                       note="Just holding the benchmark from the first price the desk read, with the crypto fee taken once, as the live desk counts it."),
                   account=dict(cash_usd=self.sb.cash(), holdings=self.sb.holding(), orders=len(self.sb.s["orders"])),
                   limits=LIMITS, edited_later_news_seen=self._edited_seen(),
                   run_facts=dict(ticks_run=self.prog["ticks_run"], ticks_skipped=self.prog["ticks_skipped"], wall_seconds=round(self.prog["wall_seconds"], 1)))
        self.prog["done"] = True; self.now = self.end; save_json(self.dir / "result.json", res); self.save()

    def _edited_seen(self):
        n = 0
        for f in sorted((self.dir / "packets").glob("*.json")):
            n += sum(1 for a in json.loads(f.read_text())["feed"]["news"] if a.get("edited_later"))
        return n


def run_code_trader(session_id, fn, tape=None):
    """Runs a code trader (a plain function fn(packet, look) -> pick or no-pick) through the same path an AI trader uses."""
    s = Session(session_id, tape=tape)
    while not s.done():
        pk = s.packet()
        r = s.submit(fn(pk, s.look))
        if not r.get("ok"):
            raise RuntimeError(f"the code trader's pick was refused: {r}")
    return json.loads((s.dir / "result.json").read_text())
