"""TM07 protocol. An operator supplies frozen local inputs; nothing fetches or calls a model."""
from collections import Counter
from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3

from timemachine import perp as P, desk_orders as orders, tm06

UTC = timezone.utc
SCOUTS = ("price_scout", "news_scout")
ARMS = ("A", "B", "C")
BOSSES = ("claude_fable_5_2", "claude_opus_5_5")
SETTINGS = dict(notes_per_scout=2, note_chars=280, looks=3, look_rows=120, max_conditions=2, max_hours=6,
                headline_rows=3, attention_rows=7)
SID = re.compile(r"TM07-[A-Za-z0-9_-]{1,72}\Z")
OID = re.compile(r"[A-Za-z0-9_./:-]{1,180}\Z")


def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(obj):
    return sha256(encode(obj).encode()).hexdigest()


def seal(key, domain, obj):
    if not isinstance(key,str) or len(key) < 32:
        raise ValueError("operator seal key is required")
    return hmac.digest(key.encode(), encode([domain,obj]).encode(), "sha256").hex()


def verify_seal(key, domain, obj, signature):
    if not isinstance(signature,str) or not hmac.compare_digest(seal(key,domain,obj),signature):
        raise ValueError(f"bad {domain} seal")


def issue_role_tokens(arm):
    roles = SCOUTS if arm == "scout" else ("boss",)
    return {r:secrets.token_urlsafe(32) for r in roles}


def claim_tokens(root,sid,tokens):
    """The operator's desk root has one registry; collisions fail closed."""
    path = root/".role_tokens.sqlite"
    with closing(sqlite3.connect(path)) as con, con:
        path.chmod(0o600)
        con.execute("CREATE TABLE IF NOT EXISTS claimed (digest TEXT PRIMARY KEY, session TEXT, role TEXT)")
        try:
            con.executemany("INSERT INTO claimed VALUES(?,?,?)",
                            [(sha256(t.encode()).hexdigest(),sid,r) for r,t in tokens.items()])
        except sqlite3.IntegrityError as exc:
            raise ValueError("a role token is already assigned") from exc


def validate_worker_boundary(key,proof,signature,root,*,launcher_digest=None):
    """Require a sealed, release-bound receipt of the sampled rehearsal."""
    from timemachine import tm07_isolation_probe as probe
    verify_seal(key,"worker-boundary",proof,signature)
    if proof.get("scope") != probe.SCOPE:
        raise ValueError("worker boundary receipt must be scoped to the sampled rehearsal")
    identities = proof.get("sandbox_identities")
    hash_ok = lambda s:isinstance(s,str) and re.fullmatch(r"[0-9a-f]{64}",s)
    if (proof.get("version") != probe.VERSION or proof.get("root") != str(Path(root).resolve())
            or not hash_ok(launcher_digest) or proof.get("launcher_digest") != launcher_digest
            or not hash_ok(proof.get("registration")) or not hash_ok(proof.get("probe_transcript_digest"))
            or not isinstance(identities,dict) or set(identities) != probe.IDENTITIES
            or not all(isinstance(s,str) and s for s in identities.values())
            or len(set(identities.values())) != len(identities)
            or proof.get("passed") != sorted(probe.CHECKS)):
        raise ValueError("worker boundary has missing isolation probes")


def epoch(value):
    if type(value) is int:
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("UTC datetime needs a time zone")
        return int(value.timestamp())
    return int(P.parse(value).timestamp())


def wall(value):
    return datetime.fromtimestamp(value, UTC)


PRICE_FIELDS = {"price","observed_at","change_1h","change_24h","volume","funding"}
TYPED_ROW_FIELDS = {"id","symbol","kind","published","known_at","vintage","licensed","value"}
BAR_LENGTHS = {"1Min":60,"30Min":1800,"1Hour":3600,"1Day":86400}
ISO_CLOCK = re.compile(r"(?P<whole>\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}:\d{2})(?:[.,](?P<fraction>\d+))?(?P<zone>Z|z|[+-]\d{2}:\d{2})\Z")
DATE_PREFIX = re.compile(r"^\d{4}[-/]\d{1,2}(?:[-/]|$)")
CLOCK_KEY = re.compile(r"(?:^|_)(?:timestamp|datetime|date|utc|epoch|time|stamp)(?:_|$)|(?:_at|_on)$")
EXACT_CLOCK_KEYS = {"t","ts","published","known","observed","period_start","period_end","stamped","as_of","asof"}


def clock_not_after(stamp, bound):
    """Compare against a whole-second bound without discarding fraction digits."""
    if type(stamp) is int:
        return stamp <= bound
    if type(stamp) is float:
        return math.isfinite(stamp) and stamp <= bound
    if not isinstance(stamp,str):
        return False
    match = ISO_CLOCK.fullmatch(stamp)
    if match:
        whole, fraction, zone = match.groups()
        try:
            at = datetime.fromisoformat(whole+("Z" if zone == "z" else zone))
            limit = wall(bound)
        except (OSError, OverflowError, ValueError):
            return False
        return at < limit or at == limit and not (fraction or "").strip("0")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}",stamp):
        try:
            return datetime.fromisoformat(stamp).replace(tzinfo=UTC) <= wall(bound)
        except (OSError, OverflowError, ValueError):
            return False
    return False


def dated_at_wake(item, wake):
    """Inspect nested snapshot and provenance fields, not just the envelope."""
    pending = [(item,False)]
    while pending:
        value, is_clock = pending.pop()
        if is_clock or isinstance(value,str) and DATE_PREFIX.match(value.strip()):
            if not clock_not_after(value, wake):
                return False
        elif isinstance(value,dict):
            for field, child in value.items():
                if not isinstance(field,str):
                    return False
                key = re.sub(r"(?<=[a-z0-9])(?=[A-Z])","_",field).lower().replace("-","_")
                pending.append((child,key in EXACT_CLOCK_KEYS or bool(CLOCK_KEY.search(key))))
        elif isinstance(value,(list,tuple)):
            pending.extend((child,False) for child in value)
    return True


def typed_price(value, published):
    if (not isinstance(value,dict) or value.keys()-PRICE_FIELDS or not orders.number(value.get("price"))
            or value["price"] <= 0
            or not clock_not_after(value.get("observed_at"),published)):
        return False
    if any(value.get(k) is not None and not orders.number(value[k]) for k in ("change_1h","change_24h")):
        return False
    volume = value.get("volume")
    if volume is not None and (not isinstance(volume,dict) or volume.keys() != {"usd_24h","usual_usd_per_day","ratio"}
                               or any(v is not None and (not orders.number(v) or v < 0) for v in volume.values())):
        return False
    funding = value.get("funding")
    if funding is not None:
        if (not isinstance(funding,dict) or funding.keys() != {"rate","every_hours","stamped_utc"}
                or not orders.number(funding["rate"]) or not orders.number(funding["every_hours"])
                or not 1 <= funding["every_hours"] <= 24 or not isinstance(funding["stamped_utc"],str)):
            return False
        if not clock_not_after(funding["stamped_utc"],published):
            return False
    return True


def available(e, wake, proofs=None):
    if not isinstance(e,dict) or not dated_at_wake(e,wake):
        return False
    published, known = e.get("published"), e.get("known_at")
    if not (type(published) is int and type(known) is int and published <= known <= wake
            and e.get("vintage") == "original" and e.get("licensed") is True):
        return False
    kind = e.get("kind")
    value = e.get("value")
    if kind == "bars":
        if (e.keys()-(TYPED_ROW_FIELDS|{"period_end","packet"}) or not isinstance(value,dict)
                or value.keys() != set("ohlcv")|{"t","timeframe"} or not isinstance(value["timeframe"],str)
                or any(not orders.number(value[k]) or value[k] <= 0 for k in "ohlc")
                or value["v"] is not None and (not orders.number(value["v"]) or value["v"] < 0)):
            return False
        duration = BAR_LENGTHS.get(value["timeframe"])
        return bool(duration and type(value["t"]) is int and value["t"]+duration == e.get("period_end")
                    and e["period_end"] <= published and type(e.get("packet",True)) is bool)
    if kind == "price":
        return not (e.keys()-TYPED_ROW_FIELDS) and typed_price(value,published)
    if kind not in ("news","attention") or not isinstance(value,dict):
        return False
    if e.keys()-(TYPED_ROW_FIELDS|({"period_end"} if kind == "attention" else {"primary","origins"})):
        return False
    if kind == "attention":
        if (value.keys()-{"count","period_start","period_end","published_at","observed_at"}
                or not orders.number(value.get("count")) or value["count"] < 0
                or type(value.get("period_end")) is not int or value["period_end"] != e.get("period_end")
                or value["period_end"] > published
                or "period_start" in value and (type(value["period_start"]) is not int
                                               or value["period_start"] > value["period_end"])):
            return False
    elif (value.keys()-{"headline","published_at","observed_at"} or not isinstance(value.get("headline"),str)
          or not value["headline"].strip()):
        return False
    if ("published_at" in value and (type(value["published_at"]) is not int or value["published_at"] != published)
            or "observed_at" in value and (type(value["observed_at"]) is not int or not published <= value["observed_at"] <= known)):
        return False
    proof = (proofs or {}).get(e.get("id"),{})
    if (not isinstance(proof,dict) or not dated_at_wake(proof,wake)
            or proof.get("row_hash") != digest(e) or proof.get("version_hash") != digest(value)
            or proof.get("licensed") is not True or not proof.get("version_record")
            or proof.get("published") != published or proof.get("known_at") != known):
        return False
    confirmations = proof.get("confirmations",[])
    if not isinstance(confirmations,list):
        return False
    if any(not isinstance(x,dict) or not x.get("group") or not x.get("version_record") or not x.get("version_hash")
           or x.keys()-{"group","primary","known_at","published_at","version_record","version_hash"}
           or type(x.get("known_at")) is not int or x["known_at"] > known
           or "published_at" in x and (type(x["published_at"]) is not int or x["published_at"] > x["known_at"])
           for x in confirmations):
        return False
    if kind == "attention":
        return True
    return any(x.get("primary") is True for x in confirmations) or len({x["group"] for x in confirmations}) >= 2


def completed_mark(tape, symbol, wake):
    """Latest completed crypto close and its completion time."""
    candidates = []
    for tf, seconds in BAR_LENGTHS.items():
        row = tape._conn().execute(
            "SELECT t,c FROM bars WHERE symbol=? AND tf=? AND t<=? ORDER BY t DESC LIMIT 1",
            (symbol, tf, wake-seconds)).fetchone()
        if row and orders.number(row[1]) and row[1] > 0:
            candidates.append((row[0]+seconds, -seconds, row[1]))
    return max(candidates) if candidates else None


def mark_as_of(tape, symbol, wake):
    mark = completed_mark(tape,symbol,wake)
    return mark[-1] if mark else None


def desk_marks(tape, symbols, wake):
    return {s:m for s in symbols if (m := mark_as_of(tape, s, wake)) is not None}


def desk_funding(tape, symbols, cfg, start, end):
    """Do not round or distribute an observed settlement."""
    a, b = epoch(start), epoch(end)
    funding, sources, stamps = {}, {}, {}
    for s in symbols:
        venue = P.per(cfg["tm_fast_funding_venue"], s)
        rates = tm06.rows(tape, "SELECT t,rate,interval_hours FROM funding WHERE symbol=? AND venue=? AND t BETWEEN ? AND ? ORDER BY t",
                          (s, venue, a, b))
        by_hour, known = {}, {}
        for t, rate, interval in rates:
            if (type(t) is not int or not orders.number(rate) or not orders.number(interval)
                    or int(interval) != interval or not 1 <= interval <= 24):
                raise ValueError("unusable funding publication or interval")
            if t in by_hour:
                raise ValueError("duplicate funding settlement")
            by_hour[t] = rate
            known[t] = t
        funding[s], stamps[s] = by_hour, known
        sources[s] = venue
    return funding, sources, stamps


def prepare_week(tape, cfg, start, end, symbols, evidence_by_wake, *, vendor_proofs=None,runner_id=None):
    """Builder helper only. Reads a caller-supplied tape and separately vetted existing rows."""
    a, b = epoch(start), epoch(end)
    wakes = list(range(a, b, 3600))
    watch = [c if "/" in c else c + "/USD" for c in cfg["tm06_plan"]["coins"]]
    priced = list(dict.fromkeys(symbols + ["BTC/USD"]))
    funding, source, stamps = desk_funding(tape, priced, cfg, a, b)
    pp = P.p_params(priced, cfg, funding=funding)
    pp.update(source=source,funding_known_at=stamps)
    mins = P.perp_minutes(tape, priced, wall(a), wall(b))
    rows = []
    for t in wakes:
        fills = {}
        for s in priced:
            bar = tape.fill_bar(s, wall(t), wall(t + 3600))
            fills[s] = [P.iso(bar["t"]), bar["o"]] if bar else None
        rows.append(dict(marks=desk_marks(tape, priced, t), fills=fills))
    evidence, dropped = [], []
    for t in wakes:
        w = wall(t)
        packet = []
        for s in watch:
            quote = completed_mark(tape,s,t)
            if quote:
                observed,_,mark = quote
                h1, h24 = (mark_as_of(tape, s, t-3600*n) for n in (1, 24))
                packet.append(dict(id=f"price:{t}:{s}", symbol=s, kind="price", published=t, known_at=t,
                                   vintage="original", licensed=True, value=dict(price=mark,observed_at=observed,
                                       change_1h=(mark/h1-1)*100 if h1 else None, change_24h=(mark/h24-1)*100 if h24 else None,
                                       volume=tm06.volume_row(tape, s, w, cfg), funding=tm06.last_funding(tape, s, w, cfg))))
            for size, count, tf in ((3600, 24, "1Hour"), (60, 30, "1Min")):
                bs = (P.S.built_bars(tape, s, size, w-timedelta(seconds=size*(count+1)), w, count)
                      if size == 3600 else tape.bars(s, tf, w-timedelta(minutes=count+1), w, limit=count))
                for bar in bs:
                    stamp = epoch(bar["t"])
                    packet.append(dict(id=f"bar:{size}:{stamp}:{s}", symbol=s, kind="bars", published=stamp+size,
                                       known_at=stamp+size, period_end=stamp+size, vintage="original", licensed=True,
                                       packet=True, value=dict(t=stamp, timeframe=tf, **{k: bar.get(k) for k in "ohlcv"})))
        rejected = Counter()
        for e in evidence_by_wake.get(str(t),[]):
            kind = e.get("kind")
            if kind in ("news","attention") and available(e,t,vendor_proofs):
                packet.append(e)
            else:
                rejected[kind if kind in ("news","attention") else "other"] += 1
        dropped.append(dict(rejected))
        evidence.append(packet)
    legacy_meta = dict(market="crypto",symbols=symbols,benchmark="BTC/USD",
                       wakes=[P.iso(wall(t)) for t in wakes],end_utc=P.iso(wall(b)))
    legacy = dict(table=P.W.price_table(tape,legacy_meta),
                  funding=tm06.fast_funding(tape,priced,cfg,wall(a),wall(b))[0])
    return dict(wakes=wakes, end=b, symbols=symbols, watch=watch, benchmark="BTC/USD", opening={},
                rows=rows, minutes=list(mins), end_marks=desk_marks(tape, priced, b),
                evidence=evidence, evidence_drops=dropped, cfg=cfg, params=pp, vendor_proofs=vendor_proofs or {},
                gross=float(cfg["tm06_plan"]["swing_max_gross"]),runner_id=runner_id,legacy_yardsticks=legacy)


def create_desk(path, spec, arm, boss, tokens, scout=None, settings=None, *, approval_key=None, vendor_signature=None,
                registration=None,model_build=None,gates=None):
    """Write one isolated off-repo session folder. Scout mode has no trading book access."""
    if arm not in (*ARMS, "scout") or (arm != "scout" and boss not in BOSSES):
        raise ValueError("unknown arm or boss")
    roles = SCOUTS if arm == "scout" else ("boss",)
    if (set(tokens) != set(roles) or any(not isinstance(t, str) or len(t) < 32 for t in tokens.values())
            or len(set(tokens.values())) != len(roles)):
        raise ValueError("use separate random role tokens")
    if (arm in ("B", "C")) != (scout is not None):
        raise ValueError("desk arms require a sealed neutral scout export")
    spec = json.loads(encode(spec))
    fixture = digest(spec)
    proof = spec.get("vendor_proofs",{})
    if proof:
        verify_seal(approval_key,"vendor",proof,vendor_signature)
    # A shared frozen packet is evidence, not another boss's output.
    if scout:
        verify_seal(approval_key,"scout",{k:v for k,v in scout.items() if k != "seal"},scout.get("seal"))
        if (scout["fixture"] != fixture or len(scout["wakes"]) != len(spec["wakes"])
                or not SID.fullmatch(scout["neutral_id"])):
            raise ValueError("scout seal belongs to another tape or neutral session")
        opts = dict(SETTINGS,**(settings or {}))
        for at, rows, block in zip(spec["wakes"],spec["evidence"],scout["wakes"]):
            pool = {e["id"]:e for e in rows if available(e,at,proof)}
            out = block["notes"]
            if block.get("wake") != at or not isinstance(out,list) or len(out) > 2*opts["notes_per_scout"]:
                raise ValueError("wrong wake in scout seal")
            allowed = {f"note:{at}:{role}:{i}" for role in SCOUTS for i in range(opts["notes_per_scout"])}
            for note in out:
                if (note.get("id") not in allowed or note.get("wake") != at or note.get("symbol") not in spec["watch"]
                        or not isinstance(note.get("text"),str) or not 1 <= len(note["text"]) <= opts["note_chars"]
                        or not isinstance(note.get("evidence"),list) or not note["evidence"]
                        or any(pool.get(e.get("id")) != e or e.get("symbol") != note["symbol"] for e in note["evidence"])):
                    raise ValueError("invalid note in scout seal")
                allowed.remove(note["id"])
    path = Path(path)
    if not SID.fullmatch(path.name):
        raise ValueError("invalid TM07 session id")
    meta = dict(arm=arm,boss=boss,fixture=fixture,scout_hash=digest(scout) if scout else None,scout=scout,
                settings=dict(SETTINGS,**(settings or {})),approval_scope=seal(approval_key,"scope",fixture) if approval_key else None,
                tokens={role:sha256(t.encode()).hexdigest() for role,t in tokens.items()})
    if registration is not None:
        from timemachine.score_tm07 import Registration
        reg = Registration(registration,approval_key)
        reg.check_root(path)
        meta.update(registration=registration,model_build=model_build,gates=gates or [])
        week = reg.validate(spec,meta,path.name)
        reg.verify_gate(week,boss,arm,gates,approval_key)
        record_attempt(path,reg.hash,week,boss,arm,gates)
    claim_tokens(path.parent,path.name,tokens)
    path.mkdir(mode=0o700, parents=False)
    for name, obj in (("fixture.json",spec),("manifest.json",meta)):
        fd = os.open(path / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(encode(obj))
    with closing(sqlite3.connect(path / "desk.sqlite")) as con, con:
        con.executescript("CREATE TABLE state (id INTEGER PRIMARY KEY CHECK(id=0), data TEXT NOT NULL);"
                          "CREATE TABLE journal (id INTEGER PRIMARY KEY, wake INTEGER, role TEXT, kind TEXT, data TEXT);"
                          "CREATE TRIGGER no_change BEFORE UPDATE ON journal BEGIN SELECT RAISE(ABORT,'append only'); END;"
                          "CREATE TRIGGER no_delete BEFORE DELETE ON journal BEGIN SELECT RAISE(ABORT,'append only'); END;")
        con.execute("INSERT INTO state VALUES (0, ?)", (encode(dict(k=0, issued={}, scout={}, active={}, looks=[],
                    book=P.new_book(spec["cfg"]["tm_account_start_usd"], spec.get("opening")))),))


@contextmanager
def study_ledger(root,write=False):
    target = Path(root)/".registered_attempts.sqlite"
    if target.is_symlink() or not write and not target.is_file():
        raise ValueError("canonical TM07 attempt ledger is missing or redirected")
    with closing(sqlite3.connect(target)) as con,con:
        if write:
            target.chmod(0o600)
            con.executescript(
                "CREATE TABLE IF NOT EXISTS attempts (reg TEXT, week TEXT, boss TEXT, arm TEXT, session TEXT UNIQUE, gate_hash TEXT,"
                "PRIMARY KEY(reg,week,boss,arm));"
                "CREATE TABLE IF NOT EXISTS neutral (reg TEXT, week TEXT, session TEXT UNIQUE, hash TEXT, seal TEXT,"
                "PRIMARY KEY(reg,week));"
                "CREATE TRIGGER IF NOT EXISTS neutral_no_update BEFORE UPDATE ON neutral BEGIN SELECT RAISE(ABORT,'append only'); END;"
                "CREATE TRIGGER IF NOT EXISTS neutral_no_delete BEFORE DELETE ON neutral BEGIN SELECT RAISE(ABORT,'append only'); END;")
            con.execute("BEGIN IMMEDIATE")
        yield con


def record_attempt(path,reg,week,boss,arm,gates):
    with study_ledger(path.parent,write=True) as con:
        try:
            con.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?)",(reg,week,boss or "scout",arm,path.name,digest(gates or [])))
        except sqlite3.IntegrityError as exc:
            raise ValueError("registered attempt already recorded; do not replace it") from exc


class DeskSession:
    def __init__(self, path):
        self.path = Path(path)
        self.sid = self.path.name
        self.manifest = json.loads((self.path / "manifest.json").read_text())
        self.spec = json.loads((self.path / "fixture.json").read_text())
        if digest(self.spec) != self.manifest["fixture"]:
            raise ValueError("frozen fixture changed")
        scout = self.manifest["scout"]
        if scout is not None and (digest(scout) != self.manifest["scout_hash"] or scout["fixture"] != self.manifest["fixture"]):
            raise ValueError("sealed scout stream changed")
        self.arm = self.manifest["arm"]
        self.opts = self.manifest["settings"]
        self.pp = self.spec["params"]
        self.pp["funding"] = {s: {int(k): v for k, v in rows.items()} for s, rows in self.pp["funding"].items()}
        self.minutes = P.Minutes(self.spec["minutes"])

    def authenticate(self, token):
        hashed = sha256(token.encode()).hexdigest()
        return next((r for r, v in self.manifest["tokens"].items() if hmac.compare_digest(hashed, v)), None)

    @contextmanager
    def tx(self):
        with closing(sqlite3.connect(self.path / "desk.sqlite")) as con, con:
            con.execute("BEGIN IMMEDIATE")
            st = json.loads(con.execute("SELECT data FROM state WHERE id=0").fetchone()[0])
            yield con, st
            con.execute("UPDATE state SET data=? WHERE id=0", (encode(st),))

    @staticmethod
    def log(con, at, role, kind, data):
        con.execute("INSERT INTO journal(wake, role, kind, data) VALUES(?,?,?,?)", (at, role, kind, encode(data)))

    def evidence(self, k):
        at = self.spec["wakes"][k]
        out = {}
        for e in self.spec["evidence"][k]:
            if (available(e,at,self.spec.get("vendor_proofs")) and e.get("symbol") in self.spec["watch"] and isinstance(e.get("id"), str)
                    and OID.fullmatch(e["id"]) and e["kind"] in ("price", "bars", "news", "attention")):
                if e["id"] in out and out[e["id"]] != e:
                    raise ValueError("conflicting evidence id")
                out[e["id"]] = e
        return out

    def raw(self, pool, at):
        result = []
        for s in self.spec["watch"]:
            for kind, limit in (("price", 1), ("bars", 54), ("news", self.opts["headline_rows"]), ("attention", self.opts["attention_rows"])):
                es = [e for e in pool.values() if e["symbol"] == s and e["kind"] == kind
                      and (kind != "news" or e["known_at"] >= at-86400)
                      and (kind != "bars" or e.get("packet", True))]
                result.extend(sorted(es, key=lambda e: (e["known_at"], e["id"]), reverse=True)[:limit])
        return result

    def merge_notes(self, by_role, k):
        pool = self.evidence(k)
        at = self.spec["wakes"][k]
        raw = self.raw(pool, at)
        exposed = {e["id"]: e for e in raw}
        out, seen = [], set()
        for rank in range(self.opts["notes_per_scout"]):
            for role in SCOUTS:
                ns = by_role[role]
                if rank >= len(ns):
                    continue
                n = ns[rank]
                ev = [exposed[i] for i in n["evidence_ids"]]
                news = next((e for e in ev if e["kind"] == "news"), None)
                key = (n["symbol"], news.get("event_id", news["id"]) if news else "price")
                if key in seen:
                    continue
                seen.add(key)
                price = next((e for e in raw if e["symbol"] == n["symbol"] and e["kind"] == "price"), None)
                if price and price not in ev:
                    ev.append(price)
                out.append(dict(id=f"note:{at}:{role}:{rank}", wake=at, symbol=n["symbol"], text=n["text"], evidence=ev))
        return out

    def packet(self, con, st, role):
        k = st["k"]
        at = self.spec["wakes"][k]
        issued = st["issued"]
        if role not in issued:
            issued[role] = secrets.token_hex(24)
        pool = self.evidence(k)
        if not con.execute("SELECT 1 FROM journal WHERE wake=? AND kind='evidence_drops'",(at,)).fetchone():
            prior = self.spec.get("evidence_drops")
            dropped = Counter(prior[k] if prior else {})
            for e in self.spec["evidence"][k]:
                if not isinstance(e,dict) or pool.get(e.get("id")) != e:
                    kind = e.get("kind") if isinstance(e,dict) else None
                    dropped[kind if kind in ("price","bars","news","attention") else "other"] += 1
            self.log(con,at,"operator","evidence_drops",dict(dropped))
        result = dict(session=self.sid, role=role, utc=at, step=k+1, total=len(self.spec["wakes"]), wake_key=issued[role],
                      tradable=self.spec["symbols"])
        if role in SCOUTS or self.arm == "A":
            result["evidence"] = self.raw(pool, at)
            result["watch"] = self.spec["watch"]
        if role == "boss":
            marks = self.spec["rows"][k]["marks"]
            b = st["book"]
            result.update(arm=self.arm, book=dict(cash=b["cash"], equity=P.value_at(b, marks),
                          weights=P.weights_at(b, marks), current_target=b["target"], exits=b["exits"],
                          marks={s:marks[s] for s in b["qty"] if s in marks}),
                          active=self.resting(st), looks_left=self.opts["looks"]-len(st["looks"]),
                          book_evidence=f"book:{at}")
            if self.arm != "A":
                result["notes"] = self.manifest["scout"]["wakes"][k]["notes"]
        if not con.execute("SELECT 1 FROM journal WHERE wake=? AND role=? AND kind='packet'", (at, role)).fetchone():
            self.log(con, at, role, "packet", dict(hash=digest(result)))
        return result

    @staticmethod
    def resting(st):
        waiting = st["book"].get("desk_order_updates",{})
        return list(st["active"].values())+[dict(c["order"],pending_install=True)
                                            for _,c in sorted(waiting.items()) if c["order"] is not None]

    def lookup(self, con, st, body):
        if len(st["looks"]) >= self.opts["looks"]:
            raise ValueError("no lookups left")
        k = st["k"]
        at = self.spec["wakes"][k]
        sym, kind = body.get("symbol"), body.get("kind")
        if sym not in self.spec["symbols"] or kind not in ("bars", "news", "attention"):
            raise ValueError("lookup needs one tradable symbol and an approved view")
        rows = [e for e in self.evidence(k).values() if e["symbol"] == sym and e["kind"] == kind and e["known_at"] >= at-86400]
        rows = sorted(rows, key=lambda e: (e["known_at"], e["id"]), reverse=True)[:self.opts["look_rows"]]
        ids = [e["id"] for e in rows]
        quote = self.quote(k,sym) if kind == "bars" else None
        if quote:
            ids.append(quote["id"])
        st["looks"].append(ids)
        result = dict(rows=rows, quote=quote, looks_left=self.opts["looks"]-len(st["looks"]))
        self.log(con, at, "boss", "look", dict(symbol=sym, kind=kind, ids=ids, hash=digest(result)))
        return result

    def quote(self,k,symbol):
        mark = self.spec["rows"][k]["marks"].get(symbol)
        quotes = [e for e in self.evidence(k).values() if e["kind"] == "price" and e["symbol"] == symbol
                  and e["value"]["price"] == mark]
        if quotes:
            row = max(quotes,key=lambda e:(e["known_at"],e["id"]))
            t = self.spec["wakes"][k]
            return dict(id=f"quote:{t}:{symbol}",symbol=symbol,utc=t,price=mark,observed_at=row["value"]["observed_at"])

    def visible_marks(self,k,st,notes):
        marks = self.spec["rows"][k]["marks"]
        ids = {i for look in st["looks"] for i in look}
        rows = self.raw(self.evidence(k),self.spec["wakes"][k]) if self.arm == "A" else [
            e for n in notes for e in n["evidence"]]
        quoted = {e["symbol"] for e in rows if e["kind"] == "price" and isinstance(e.get("value"),dict)
                  and e["value"].get("price") == marks.get(e["symbol"])}
        return {s:m for s,m in marks.items() if s in quoted or s in st["book"]["qty"]
                or f"quote:{self.spec['wakes'][k]}:{s}" in ids}

    def scout_submit(self, con, st, role, items):
        if role in st["scout"]:
            raise ValueError("scout already filed for this wake")
        if not isinstance(items, list) or len(items) > self.opts["notes_per_scout"]:
            raise ValueError("too many scout notes")
        k = st["k"]
        at = self.spec["wakes"][k]
        pool = {e["id"]: e for e in self.raw(self.evidence(k), at)}
        for n in items:
            if (not isinstance(n, dict) or set(n) != {"symbol", "text", "evidence_ids"}
                    or n["symbol"] not in self.spec["watch"] or not isinstance(n["text"], str)
                    or not n["text"].strip() or len(n["text"]) > self.opts["note_chars"]):
                raise ValueError("bad scout note")
            ids = n["evidence_ids"]
            if (not isinstance(ids, list) or not 1 <= len(ids) <= 4
                    or any(not isinstance(i, str) or i not in pool or pool[i]["symbol"] != n["symbol"] for i in ids)):
                raise ValueError("scout evidence not visible for this coin")
        st["scout"][role] = items
        self.log(con, at, role, "scout", dict(notes=items))
        if all(r in st["scout"] for r in SCOUTS):
            notes = self.merge_notes(st["scout"], k)
            self.log(con, at, "neutral", "seal", dict(wake=at,notes=notes,count_before=sum(map(len,st["scout"].values()))))
            self.next(st)
        return dict(accepted=True)

    def decision(self, con, st, body):
        k = st["k"]
        at = self.spec["wakes"][k]
        end = self.spec["end"]
        row = self.spec["rows"][k]
        bare = {x: v for x, v in body.items() if x not in ("conditions", "keep", "citations")}
        notes = self.manifest["scout"]["wakes"][k]["notes"] if self.arm != "A" else []
        marks = self.visible_marks(k,st,notes)
        mentioned = set(bare["exits"]) if isinstance(bare.get("exits"),dict) else set()
        conditions = body.get("conditions",[])
        if isinstance(conditions,list):
            mentioned.update(x["symbol"] for x in conditions
                             if isinstance(x,dict) and isinstance(x.get("symbol"),str))
        if (mentioned & set(self.spec["symbols"])) - marks.keys():
            raise ValueError("protective exits and conditions need a visible quote; request bars")
        errs = P.check_answer(bare, self.spec["symbols"], self.spec["cfg"], self.spec["gross"], marks)
        if errs:
            raise ValueError(errs[0])
        if self.arm != "C" and body.keys() & {"conditions", "keep"}:
            raise ValueError("standing orders are for arm C only")
        cites = body.get("citations", {})
        if not isinstance(cites, dict) or cites.keys() - set(self.spec["symbols"]):
            raise ValueError("citations must be by tradable symbol")
        note_ids = {n["id"] for n in notes}
        ids = {f"book:{at}"} | {i for look in st["looks"] for i in look}
        ids.update(e["id"] for n in notes for e in n["evidence"])
        if self.arm == "A":
            ids.update(e["id"] for e in self.raw(self.evidence(k), at))

        def cite(obj):
            if not isinstance(obj, dict):
                raise ValueError("bad citation")
            n, e = obj.get("note_ids", []), obj.get("evidence_ids", [])
            if (not isinstance(n, list) or not isinstance(e, list) or not (n or e)
                    or any(not isinstance(x, str) or x not in note_ids for x in n)
                    or any(not isinstance(x, str) or x not in ids for x in e)):
                raise ValueError("cite a visible note, tape row or book id")

        weights = bare.get("weights")
        if weights is not None:
            old = st["book"]["target"]
            for s in set(old) | set(weights):
                if weights.get(s, 0) != old.get(s, 0):
                    cite(cites.get(s))
        for c in cites.values():
            cite(c)
        new = orders.normalize_conditions(conditions, marks, self.spec["symbols"], at,
                                          end, self.opts["max_hours"], self.spec["gross"])
        decision_id = f"{self.sid}:{at}"
        for c in new.values():
            c["decision_id"] = decision_id
            cite(c)
        keep = body.get("keep", [])
        resting = {o["id"]:o["symbol"] for o in self.resting(st)}
        if (not isinstance(keep, list) or len(keep) > self.opts["max_conditions"]
                or any(not isinstance(i, str) or i not in resting for i in keep)):
            raise ValueError("keep must name active order ids")
        kept = {resting[i] for i in keep}
        if len(kept | new.keys()) > self.opts["max_conditions"]:
            raise ValueError("too many live conditions")
        bundle = dict(weights=weights, exits=bare.get("exits"), conditions=new, keep=keep,
                      decision_id=decision_id, citations=cites, why=bare["why"])
        nxt = self.spec["wakes"][k+1] if k+1 < len(self.spec["wakes"]) else end
        rec, active, events = orders.step(st["book"], bundle, row, self.pp, self.minutes, at, nxt, nxt == end,
                                          st["active"], self.spec["gross"], first=k == 0)
        self.log(con, at, "boss", "decision", bundle)
        for trade in rec["trades"]:
            s = trade["symbol"]
            self.log(con, at, "executor", "immediate", dict(decision_id=decision_id, order_id=None,
                     citation=cites.get(s, {}), trade=trade, spread_usd=trade["qty"]*trade["open"]*self.pp["hs"][s],
                     target=rec["target"].get(s, 0)))
        for event in events:
            self.log(con, at, "executor", "condition", event)
        # Reconstruct lineage in bar order. An ordinary protective exit has no
        # new note; it inherits the last decision that moved that position.
        parents = st.setdefault("position_origin", {})
        timeline = []
        for tr in rec["trades"]:
            s = tr["symbol"]
            timeline.append((epoch(tr["fill_utc"]), 0, s, dict(decision_id=decision_id, order_id=None,
                             note_ids=cites.get(s, {}).get("note_ids", []),
                             evidence_ids=cites.get(s, {}).get("evidence_ids", [])) if rec["target"].get(s, 0) else None))
        for e in events:
            if e["kind"] == "filled":
                timeline.append((e["utc"], 1, e["symbol"], {k:e[k] for k in ("decision_id","order_id","note_ids","evidence_ids")}
                                 if e["target"] else None))
        for e in rec["scan"]["exits"]:
            timeline.append((epoch(e["utc"]), 2, e["symbol"], e))
        if rec["scan"]["closeout"]:
            e = rec["scan"]["closeout"]
            timeline.append((epoch(e["utc"]), 3, "", e))
        # A completed bar may be observed at the same instant as the
        # following open. Close the old lineage before attaching a new one.
        phase_rank = {2:0, 3:1, 0:2, 1:3}
        for tick, kind, s, data in sorted(timeline, key=lambda item:(item[0],phase_rank[item[1]],item[2])):
            if kind < 2:
                if data:
                    # A retried immediate move can have no new citation. Keep
                    # the previously established decision lineage in that case.
                    if data["note_ids"] or data["evidence_ids"] or s not in parents:
                        parents[s] = data
                else:
                    parents.pop(s, None)
            elif kind == 2:
                self.log(con, at, "executor", "protective_exit", dict(utc=tick, execution=data,
                         parent=parents.pop(s, None), order_id=None))
            else:
                self.log(con, at, "executor", "maintenance", dict(utc=tick, execution=data,
                         parents=dict(parents), order_id=None))
                parents.clear()
        self.log(con, at, "executor", "scan", rec["scan"])
        st["active"] = active
        if nxt == end:
            st["book"]["last_px"].update(self.spec["end_marks"])
            self.log(con, at, "executor", "finish", dict(value=max(0.0, P.value_at(st["book"], self.spec["end_marks"])),
                                                        book=st["book"]))
        self.next(st)
        # Only acknowledge. The next packet is the first place at which earlier fills may be observed.
        return dict(accepted=True, done=nxt == end)

    @staticmethod
    def next(st):
        st.update(k=st["k"]+1, issued={}, scout={}, looks=[])

    def handle(self, role, action, body):
        if role not in self.manifest["tokens"]:
            raise PermissionError("bad role")
        with self.tx() as (con, st):
            k = st["k"]
            done = k >= len(self.spec["wakes"])
            if action == "status":
                return dict(done=done, step=k, total=len(self.spec["wakes"]))
            key = body.get("wake_key")
            if action in ("look", "notes", "pick", "usage") and isinstance(key, str):
                rid = digest([role, action, key, body])
                prev = con.execute("SELECT data FROM journal WHERE kind=? LIMIT 1", ("receipt:"+rid,)).fetchone()
                if prev:
                    return json.loads(prev[0])
            if done:
                return dict(done=True)
            if action == "next":
                return self.packet(con, st, role)
            if not isinstance(key, str) or not hmac.compare_digest(st["issued"].get(role, "-"), key):
                raise PermissionError("wrong wake key")
            at = self.spec["wakes"][k]
            if action == "look" and role == "boss":
                request = body.get("request_id")
                if not isinstance(request,str) or not OID.fullmatch(request):
                    raise ValueError("lookup needs a wake-scoped request id")
                req = "lookup:" + request
                if con.execute("SELECT 1 FROM journal WHERE wake=? AND role=? AND kind=?", (at,role,req)).fetchone():
                    raise ValueError("lookup request id cannot be reused with changed fields")
                result = self.lookup(con, st, body)
                self.log(con,at,role,req,dict(receipt=rid))
            elif action == "notes" and role in SCOUTS:
                result = self.scout_submit(con, st, role, body.get("notes"))
            elif action == "pick" and role == "boss":
                result = self.decision(con, st, {x: v for x, v in body.items() if x != "wake_key"})
            elif action == "usage":
                request, usage = body.get("request_id"), body.get("usage")
                if not isinstance(request, str) or not OID.fullmatch(request) or not isinstance(usage, dict):
                    raise ValueError("bad usage receipt")
                kind = "usage:"+role+":"+request
                if con.execute("SELECT 1 FROM journal WHERE kind=?", (kind,)).fetchone():
                    raise ValueError("usage request already logged")
                counts = body.get("counts")
                if (not isinstance(counts, dict) or set(counts)-{"input", "output", "reasoning", "cache_read", "cache_write"}
                        or any(type(x) is not int or x < 0 for x in counts.values())):
                    raise ValueError("bad normalized token counts")
                self.log(con, at, role, kind, dict(request_id=request, usage=usage, counts=counts, wake=at))
                result = dict(accepted=True)
            else:
                raise PermissionError("operation outside role")
            self.log(con, at, role, "receipt:"+rid, result)
            return result

    def export_scout(self,approval_key):
        if self.arm != "scout":
            raise ValueError("only the neutral scout can export notes")
        verify_seal(approval_key,"scope",self.manifest["fixture"],self.manifest.get("approval_scope"))
        with self.tx() as (con, st):
            if st["k"] != len(self.spec["wakes"]):
                raise ValueError("scout stream is not sealed")
            items = [json.loads(x[0]) for x in con.execute("SELECT data FROM journal WHERE kind='seal' ORDER BY wake")]
            usage = [(r, json.loads(x)) for r, x in con.execute("SELECT role, data FROM journal WHERE kind LIKE 'usage:%' ORDER BY id")]
            result = dict(fixture=self.manifest["fixture"],neutral_id=self.sid,wakes=items,usage=usage)
            result["seal"] = seal(approval_key,"scout",result)
        if self.manifest.get("registration") is not None:
            from timemachine.score_tm07 import Registration
            reg = Registration(self.manifest["registration"],approval_key)
            reg.check_root(self.path)
            week = reg.validate(self.spec,self.manifest,self.sid)
            reg.bind_neutral(week,self.sid,digest(result))
        return result


def open_desk(sid, root=None, token=None):
    base = root or os.environ.get("TM07_RUNS_DIR")
    if not base or not SID.fullmatch(sid):
        raise FileNotFoundError("TM07 not enabled")
    base = Path(base).resolve()
    path = (base / sid).resolve()
    if path.parent != base or path.name != sid or not path.is_dir():
        raise FileNotFoundError("unknown TM07 session")
    if not isinstance(token, str) or len(token) > 512:
        raise PermissionError("bad role token")
    wanted = sha256(token.encode()).hexdigest()
    manifest = json.loads((path / "manifest.json").read_text())
    if not any(hmac.compare_digest(wanted, v) for v in manifest["tokens"].values()):
        raise PermissionError("bad role token")
    return DeskSession(path)
