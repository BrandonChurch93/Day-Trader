"""Scores one saved week at a time. Nothing is opened on import."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from math import comb, prod
import json
from pathlib import Path
import random

from timemachine import desk_orders as O, desk, perp as P, score_weights as SW, tm06

SCREEN = ("2026-07-20", "2026-08-31", "2026-10-05")
DIAGNOSTIC = "2026-05-11"
FIXED = dict(zip((DIAGNOSTIC,*SCREEN),("ENA NEAR ONDO SUI ZEC","LINK LTC ONDO PEPE ZEC","BNB HYPE LINK SOL ZEC","AAVE ADA BNB HBAR XLM")))
WATCH = frozenset(s+"/USD" for s in "AAVE ADA AVAX BCH BNB DOGE DOT ENA HBAR HYPE LINK LTC NEAR ONDO PEPE SOL SUI XLM XRP ZEC".split())
DRAW_COUNT, PERCENTILE, SEED = 1000, 90, 1
ALPHA = 0.05/4
FIRST, LAST = date(2026, 7, 6), date(2026, 11, 16)
WEEKS = tuple((FIRST + timedelta(weeks=i)).isoformat() for i in range((LAST-FIRST).days//7+1))
EXTENSION = tuple(w for w in WEEKS if w not in SCREEN)


class UnsupportedWeek(ValueError):
    """A frozen draw cannot be represented intact on its destination tape."""


def effective_costs(cfg,symbols):
    pp = P.p_params(sorted(symbols),cfg,funding={})
    return {k:pp[k] for k in ("fee","hs","maint","hours","fallback_per_day","penalty","min_change")} | {
        "venue":{s:P.per(cfg["tm_fast_funding_venue"],s) for s in sorted(symbols)}}


def canonical_cost_hash():
    """Pin registration to the independently stored TM06 thresholds."""
    return desk.digest(effective_costs(tm06.full_config(),WATCH|{"BTC/USD"}))


def settlement_map(rows):
    if not isinstance(rows,dict):
        raise ValueError("invalid funding settlement mapping")
    result = {}
    for key,value in rows.items():
        if type(key) is int or isinstance(key,str) and key.isascii() and key.isdecimal() and str(int(key)) == key:
            result[int(key)] = value
        else:
            raise ValueError("invalid funding settlement stamp")
    return result


def funding_profile_hash(params):
    """The operator can rebuild this from exact source rows before sealing."""
    return desk.digest({k:params[k] for k in ("funding","funding_known_at","source")})


class Registration:
    """A separately operator-sealed attempt, not inputs asserted by an arm."""
    def __init__(self,document,key):
        self._key = key
        self.body = json.loads(desk.encode(document["body"]))
        desk.verify_seal(key,"registration",self.body,document.get("seal"))
        self.hash = desk.digest(self.body)
        if self.body.get("version") != "TM07-v1" or not self.body.get("runner_id") or not self.body.get("ledger_ref"):
            raise ValueError("register the runner and ledger reference before launch")
        self.root = Path(self.body.get("study_root",""))
        if not self.root.is_absolute() or self.root != self.root.resolve():
            raise ValueError("register one absolute canonical study root")
        self.cost_cfg = tm06.full_config()
        if self.body.get("cost_hash") != desk.digest(effective_costs(self.cost_cfg,WATCH|{"BTC/USD"})):
            raise ValueError("registration cost profile does not match TM06")
        models = self.body.get("builds",{})
        if set(models) != {*desk.BOSSES,"gemini_neon"} or any(not v.get("id") for v in models.values()):
            raise ValueError("register all exact model builds")
        self.earliest = max("2026-07-01",*(date.fromisoformat(v["first_after_cutoff"]).isoformat() for v in models.values()))
        self.weeks = self.body["weeks"]
        if set(self.weeks) not in (set(WEEKS),set(WEEKS)|{DIAGNOSTIC}):
            raise ValueError("registration is missing the fixed calendar")
        neutral_ids = set()
        for w,item in self.weeks.items():
            neutral_id = item.get("neutral_id","")
            fixture_id = item.get("fixture","")
            if (not desk.SID.fullmatch(neutral_id) or neutral_id in neutral_ids or len(fixture_id) != 64
                    or any(c not in "0123456789abcdef" for c in fixture_id)):
                raise ValueError("register the unique neutral run and fixture hash for each week")
            funding_id = item.get("funding_hash","")
            if (not isinstance(item.get("funding_ref"),str) or not item["funding_ref"].strip()
                    or len(funding_id) != 64 or any(c not in "0123456789abcdef" for c in funding_id)):
                raise ValueError("register the source snapshot and funding settlement hash for each week")
            neutral_ids.add(neutral_id)
            if w in FIXED:
                symbols = sorted(s+"/USD" for s in FIXED[w].split())
            else:
                d = date.fromisoformat(w)
                if item.get("last_known_on") != w or item.get("before_known_on") != (d-timedelta(days=7)).isoformat():
                    raise ValueError("extension selection requires two finished Sunday closes")
                before,last = item["before"],item["last"]
                if (set(before)|set(last))-WATCH:
                    raise ValueError("extension selection is outside the fixed watch list")
                symbols = select_five(before,last)
            if item["symbols"] != symbols:
                raise ValueError("wrong registered tradable list")

    def check_root(self,path):
        path = Path(path)
        if path.parent.resolve() != self.root or path.is_symlink():
            raise ValueError("attempt is outside the registered study root")

    def bind_neutral(self,week,sid,stream_hash):
        if sid != self.weeks[week]["neutral_id"]:
            raise ValueError("wrong registered neutral session")
        record = [self.hash,week,sid,stream_hash]
        with desk.study_ledger(self.root,write=True) as con:
            attempt = con.execute("SELECT session FROM attempts WHERE reg=? AND week=? AND arm='scout'",
                                  (self.hash,week)).fetchone()
            if attempt != (sid,):
                raise ValueError("no designated neutral scout attempt")
            current = con.execute("SELECT session,hash,seal FROM neutral WHERE reg=? AND week=?",(self.hash,week)).fetchone()
            signature = desk.seal(self._key,"neutral-binding",record)
            if current is None:
                con.execute("INSERT INTO neutral VALUES(?,?,?,?,?)",(*record,signature))
            elif current != (sid,stream_hash,signature):
                raise ValueError("registered neutral stream was already finalized")

    def verify_neutral(self,week,sid,stream_hash):
        if sid != self.weeks[week]["neutral_id"] or not stream_hash:
            raise ValueError("wrong registered neutral session")
        with desk.study_ledger(self.root) as con:
            row = con.execute("SELECT session,hash,seal FROM neutral WHERE reg=? AND week=?",(self.hash,week)).fetchone()
        if row is None or row[:2] != (sid,stream_hash):
            raise ValueError("does not match the finalized registered neutral stream")
        desk.verify_seal(self._key,"neutral-binding",[self.hash,week,sid,stream_hash],row[2])

    def validate(self,spec,manifest,sid):
        w = desk.wall(spec["wakes"][0]).date().isoformat()
        if w not in self.weeks or w != DIAGNOSTIC and w < self.earliest:
            raise ValueError("unregistered week or model cutoff")
        item = self.weeks[w]
        start = desk.epoch(w+"T00:00:00Z")
        if (spec["wakes"] != list(range(start,start+7*86400,3600)) or spec["end"] != start+7*86400
                or spec["symbols"] != item["symbols"] or set(spec["watch"]) != WATCH
                or spec.get("runner_id") != self.body["runner_id"] or manifest["fixture"] != item["fixture"]
                or manifest["settings"] != desk.SETTINGS):
            raise ValueError("fixture differs from registered windows, coins or runner")
        cfg = spec["cfg"]
        pp = spec["params"]
        if (spec["gross"] != 1 or spec["opening"] or cfg["tm_account_start_usd"] != 1000
                or cfg["tm06_plan"]["main_fee_bps"] != 12 or cfg["tm06_plan"]["carried_leverage"] != [2,3]
                or sorted(cfg["tm_perp_fee_levels_bps"]) != [1,12,25]
                or cfg["tm_weights_twin_draws"] != DRAW_COUNT or cfg["tm_weights_pass_percentile"] != PERCENTILE
                or cfg["tm_weights_twin_seed"] != SEED or any(f != .0012 for f in pp["fee"].values())):
            raise ValueError("registration requires fixed costs, 1,000 twins and 90th percentile")
        priced = set(item["symbols"])|{"BTC/USD"}
        expected = effective_costs(self.cost_cfg,priced)
        if (effective_costs(cfg,priced) != expected or any(pp.get(k) != v for k,v in expected.items() if k != "venue")
                or pp.get("source") != expected["venue"] or sorted(pp.get("symbols",[])) != sorted(priced)
                or spec.get("benchmark") != "BTC/USD" or set(spec["end_marks"]) != priced
                or not all(O.number(v) and v > 0 for v in spec["end_marks"].values())):
            raise ValueError("fixture cost parameters or priced-symbol coverage differ from registered TM06")
        rates, clock = pp.get("funding",{}),pp.get("funding_known_at",{})
        if set(rates) != priced or set(clock) != priced:
            raise ValueError("funding settlement required symbol coverage")
        for sym in priced:
            values, stamps = settlement_map(rates[sym]),settlement_map(clock[sym])
            if (values.keys() != stamps.keys() or any(type(stamps[t]) is not int or stamps[t] != t
                or not start <= t <= spec["end"] or not O.number(rate) for t,rate in values.items())):
                raise ValueError("funding rate must use its exact source settlement stamp")
        if funding_profile_hash(pp) != item["funding_hash"]:
            raise ValueError("funding settlement digest differs from independently registered source")
        arm, scout = manifest["arm"], manifest["scout"]
        model = "gemini_neon" if arm == "scout" else manifest["boss"]
        if manifest.get("model_build") != self.body["builds"][model]["id"]:
            raise ValueError("unregistered model build")
        if arm == "scout" and sid != item["neutral_id"] or arm in ("B","C") and scout["neutral_id"] != item["neutral_id"]:
            raise ValueError("arm did not use designated neutral scout")
        if arm in ("B","C"):
            self.verify_neutral(w,scout["neutral_id"],manifest["scout_hash"])
        from itertools import groupby
        good = {t//3600*3600 for t,rows in groupby(spec["minutes"],key=lambda r:r[0])
                if set(spec["symbols"]) <= {r[1] for r in rows}}
        if not set(spec["wakes"]) <= good or any(not set(spec["symbols"]) <= r["marks"].keys() for r in spec["rows"]):
            raise ValueError("registered twin coverage lacks marks or a common open")
        if not any(r[1] == "BTC/USD" and start <= r[0] < start+3600 for r in spec["minutes"]):
            raise ValueError("registered benchmark has no opening price")
        legacy = spec.get("legacy_yardsticks",{})
        table = legacy.get("table",{})
        rows = table.get("rows",[])
        if (len(rows) != len(spec["wakes"]) or not priced <= table.get("end_marks",{}).keys()
                or not all(rows[0].get("fills",{}).get(s) for s in priced)
                or not isinstance(legacy.get("funding"),dict)):
            raise ValueError("freeze the legacy benchmark inputs before launch")
        return w

    def verify_gate(self,week,boss,arm,gates,key):
        if week not in EXTENSION:
            return
        for envelope in gates or ():
            item = envelope["body"]
            desk.verify_seal(key,"screen-gate",item,envelope.get("seal"))
            if (item.get("registration") == self.hash and item.get("wins") == 3
                    and item.get("screen_weeks") == list(SCREEN)
                    and (arm == "scout" or item.get("boss") == boss and (arm == "A" or item.get("arm") == arm))):
                return
        raise ValueError("extension launch requires a sealed 3/3 screen gate")

    def attest_score(self,summary):
        return dict(summary,attestation=desk.seal(self._key,"score",summary))


def sign_tail(n, k):
    return sum(comb(n, j) for j in range(k, n+1))/2**n


def sign_mark(n, cap=ALPHA):
    return next((k for k in range(1, n+1) if sign_tail(n, k) <= cap), None)


def select_five(before, last):
    """TM06's reverse sorted (rise, symbol) tie rule. Caller supplies the two prior Sunday closes."""
    ranks = sorted(((last[s]/p - 1, s) for s, p in before.items() if p > 0 and last.get(s, 0) > 0), reverse=True)
    if len(ranks) < 5:
        raise ValueError("fewer than five known prior Sunday pairs")
    return sorted(s for _, s in ranks[:5])


def load_session(path):
    sess = desk.DeskSession(path)
    if sess.arm not in desk.ARMS:
        raise ValueError("expected a boss arm")
    with sess.tx() as (con, st):
        if st["k"] != len(sess.spec["wakes"]):
            raise ValueError("unfinished week")
        log = [(r, k, json.loads(x)) for r, k, x in con.execute("SELECT role,kind,data FROM journal ORDER BY id")]
    return sess, log


def shuffle_bundles(bundles, rows, wakes, end, rng):
    n = len(bundles)
    ids = list(range(n))
    rng.shuffle(ids)
    move_ids = {order["id"]: f'{wakes[k]}:{s}' for k, j in enumerate(ids)
                for s, order in bundles[j].get("conditions", {}).items()}
    out = []
    for k, j in enumerate(ids):
        b = deepcopy(bundles[j])
        source, dest = rows[j]["marks"], rows[k]["marks"]
        if b.get("exits"):
            if any(not source.get(s) or not dest.get(s) for s in b["exits"]):
                raise UnsupportedWeek(f"missing destination mark for exit at {wakes[k]}")
            b["exits"] = {s: {x: v/source[s]*dest[s] for x, v in e.items()}
                          for s, e in b["exits"].items()}
        orders = b.get("conditions") or {}
        if any(not dest.get(s) for s in orders):
            raise UnsupportedWeek(f"missing destination mark for condition at {wakes[k]}")
        b["conditions"] = {s: dict(o, id=move_ids[o["id"]], wake=wakes[k], level=dest[s]*o["ratio"],
                                   expiry=min(end, wakes[k]+o["hours"]*3600)) for s, o in orders.items()}
        b["keep"] = [move_ids[o] for o in b.get("keep", []) if o in move_ids]
        out.append(b)
    return out


def replay(sess, bundles, fee=None, multiple=1, delay=0, journal=False):
    spec = sess.spec
    if len(spec["wakes"]) != len(bundles):
        raise ValueError("one answer per wake required")
    pp = sess.pp if fee is None else P.with_fee(sess.pp, fee)
    book = P.new_book(spec["cfg"]["tm_account_start_usd"], spec.get("opening"))
    active, events, scans, unsupported = {}, [], [], []
    count = hits = triggered = 0
    for i, (at, bundle, row) in enumerate(zip(spec["wakes"], bundles, spec["rows"])):
        end = spec["wakes"][i+1] if i+1 < len(bundles) else spec["end"]
        if multiple != 1:
            weights = bundle.get("weights")
            bundle = dict(bundle, weights=None if weights is None else {s: v*multiple for s, v in weights.items()},
                          conditions={s: dict(o, weight=o["weight"]*multiple) for s, o in bundle.get("conditions", {}).items()})
        rec, active, changes = O.step(book, bundle, row, pp, sess.minutes, at, end, end == spec["end"], active,
                                      spec["gross"]*multiple, first=i == 0, delay=delay)
        count += len(rec["trades"])
        hits += sum(e["kind"] == "filled" for e in changes)
        triggered += sum(e["kind"] == "triggered" for e in changes)
        if any(x["why"] == "no_common_open" for x in rec["skipped"]):
            unsupported.append(at)
        if journal:
            events.extend(changes)
            scans.append(rec["scan"])
    book["last_px"].update(spec["end_marks"])
    final = max(0.0, P.value_at(book, spec["end_marks"]))
    return dict(value=final, book=book, events=events, scans=scans, immediate=count, standing=hits,
                triggered=triggered, unsupported=unsupported)


def buy_and_hold(sess, weights, fee, multiple=1):
    """Run the unchanged TM06 opening-cash hold on its separately frozen inputs."""
    spec = sess.spec
    frozen = spec.get("legacy_yardsticks")
    table = frozen["table"] if frozen else {k:spec[k] for k in ("rows","end_marks")}
    pp = P.with_fee(sess.pp,fee)
    if frozen:
        pp.update(funding={s:settlement_map(v) for s,v in frozen["funding"].items()},hours=dict.fromkeys(pp["symbols"],1))
    required = set(weights)
    if (not required <= set(pp["symbols"]) or not required <= table["end_marks"].keys()
            or not all(table["rows"][0].get("fills",{}).get(s) for s in required)):
        raise UnsupportedWeek("benchmark lacks priced symbols, opening fills or final marks")
    meta = dict(opening={},wakes=[P.iso(desk.wall(t)) for t in spec["wakes"]],end_utc=P.iso(desk.wall(spec["end"])))
    answers = tm06.times(tm06.hold(len(spec["wakes"]),weights),multiple)
    book, records, value = P.run_perp(meta,table,answers,pp,sess.minutes,spec["cfg"])
    entered = records[0]["trades"]
    if {t["symbol"] for t in entered} != required:
        raise UnsupportedWeek("benchmark did not enter every declared leg")
    return dict(value=value,book=book,entries=entered)


def not_computed(action):
    """Contain failures only at the reporting boundary, never in judged replay."""
    try:
        return action()
    except Exception as exc:
        return dict(status="not computed",reason=f"{type(exc).__name__}: {exc}")


def usage_totals(rows, neutral=(), expected=None):
    """None means an unobserved field, not an observed zero. Cached/reasoning may be subsets."""
    out, seen = {}, {}
    for role, call in [(r, d) for r, k, d in rows if k.startswith("usage:")] + [tuple(x) for x in neutral]:
        entry = out.setdefault(role, {"calls": 0, "tokens": {}, "calls_with_field": {}})
        entry["calls"] += 1
        seen.setdefault(role,set()).add(call.get("wake"))
        for field, n in call["counts"].items():
            entry["tokens"][field] = entry["tokens"].get(field, 0) + n
            entry["calls_with_field"][field] = entry["calls_with_field"].get(field, 0) + 1
    for role, wakes in (expected or {}).items():
        entry = out.setdefault(role,{"calls":0,"tokens":{},"calls_with_field":{}})
        entry["wakes_without_receipt"] = sorted(set(wakes) - seen.get(role,set()))
        entry["fields_unknown_or_partial"] = [field for field in ("input","output","reasoning","cache_read","cache_write")
                                             if not entry["calls"] or entry["calls_with_field"].get(field,0) < entry["calls"]]
        entry["status"] = ("UNKNOWN" if not entry["calls"] else "PARTIAL"
                           if entry["wakes_without_receipt"] or any(f in entry["fields_unknown_or_partial"] for f in ("input","output"))
                           else "MEASURED")
    return out


def score_week(path, draws=None, draw_sensitivities=False, *, approval_key=None):
    sess, log = load_session(path)
    spec = sess.spec
    cfg = spec["cfg"]
    registered = sess.manifest.get("registration")
    if registered is not None:
        if draws is not None:
            raise ValueError("cannot override registered twin draws")
        reg = Registration(registered,approval_key)
        reg.check_root(sess.path)
        week = reg.validate(spec,sess.manifest,sess.sid)
        reg.verify_gate(week,sess.manifest["boss"],sess.arm,sess.manifest.get("gates"),approval_key)
    else:
        reg = None
    fee = cfg["tm06_plan"]["main_fee_bps"]
    start = cfg["tm_account_start_usd"]
    draws = cfg["tm_weights_twin_draws"] if draws is None else draws
    seed = cfg["tm_weights_twin_seed"]
    if type(draws) is not int or draws < 1:
        raise ValueError("positive twin count required")
    bundles = [d for _, k, d in log if k == "decision"]
    stored = [d for _, k, d in log if k == "finish"][0]
    check = replay(sess, bundles, journal=True)
    ident = dict(week=desk.wall(spec["wakes"][0]).date().isoformat(), arm=sess.arm, boss=sess.manifest["boss"],
                 fixture=sess.manifest["fixture"], scout_hash=sess.manifest["scout_hash"], settings=desk.digest(sess.opts),
                 neutral_id=(sess.manifest["scout"] or {}).get("neutral_id"),registration=reg.hash if reg else None)
    emit = reg.attest_score if reg else lambda x:x
    if (cents(check["value"]) != cents(stored["value"]) or check["book"] != stored["book"]
            or check["events"] != [d for _, k, d in log if k == "condition"]
            or check["scans"] != [d for _, k, d in log if k == "scan"]):
        raise ValueError("journal does not match replay")
    if check["unsupported"]:
        return emit(dict(ident, invalid=f"original has no common open: {check['unsupported']}"))
    hold = {s: spec["gross"]/len(spec["symbols"]) for s in spec["symbols"]}
    benchmark = spec["benchmark"]
    def supported(trial):
        if trial["unsupported"]:
            raise UnsupportedWeek(f"no common open: {trial['unsupported']}")
        return trial

    def cell(f,mult,with_twins):
        gain = lambda v:(v/start-1)*100
        run = supported(replay(sess,bundles,f,mult))
        equal,btc_long = (gain(buy_and_hold(sess,w,f,mult)["value"]) for w in (hold,{benchmark:1.0}))
        entry = dict(value=run["value"],gain=gain(run["value"]),equal=equal,benchmark=btc_long,
                     benchmark_short=not_computed(lambda:gain(buy_and_hold(sess,{benchmark:-1.0},f,mult)["value"])),
                     stats=P.p_stats(run["book"],run["value"],start),immediate=run["immediate"],standing=run["standing"])
        if with_twins:
            twin,activity = [],[]
            for i in range(draws):
                try:
                    shuffled = shuffle_bundles(bundles,spec["rows"],spec["wakes"],spec["end"],
                                               random.Random(f'tm06_shuffle:{seed}:{sess.sid}:{i}'))
                    trial = supported(replay(sess,shuffled,f,mult))
                except UnsupportedWeek as exc:
                    error = UnsupportedWeek(f"twin {i}: {exc}")
                    error.draw = i
                    raise error from exc
                twin.append(gain(trial["value"]))
                activity.append(dict(immediate=trial["immediate"],standing=trial["standing"],triggered=trial["triggered"],
                                     turnover_usd=trial["book"]["traded_usd"]))
            entry.update(twin=twin,twin_activity=activity,twin_trigger_counts=[x["triggered"] for x in activity],
                         twin_standing_fill_counts=[x["standing"] for x in activity],
                         judge=SW.judge(twin,entry["gain"],cfg["tm_weights_pass_percentile"]))
        return entry

    main_key = f"1x/{fee:g}"
    try:
        main = cell(fee,1,True)
    except UnsupportedWeek as exc:
        fields = {"failed_draw":exc.draw} if hasattr(exc,"draw") else {}
        return emit(dict(ident,invalid=str(exc),**fields))
    by = {main_key:main}
    for mult in (1,*cfg["tm06_plan"]["carried_leverage"]):
        for f in sorted(set(cfg["tm_perp_fee_levels_bps"])|{fee}):
            key = f"{mult}x/{f:g}"
            if key != main_key:
                by[key] = not_computed(lambda:cell(f,mult,draw_sensitivities))
    neutral = (sess.manifest["scout"] or {}).get("usage", [])
    expected = {"boss":spec["wakes"]}
    if sess.arm != "A":
        expected.update({role:spec["wakes"] for role in desk.SCOUTS})
    return emit(dict(ident, main=main,
                usage=usage_totals(log,neutral,expected), unique_boss_usage=usage_totals(log,expected={"boss":spec["wakes"]}),
                neutral_scout_used=bool(neutral), by_fee_multiple=by,
                delayed_value=not_computed(lambda:supported(replay(sess,bundles,fee,delay=60))["value"])
                if sess.arm == "C" else None))


def cents(value):
    return Decimal(str(value)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def cent_lift(baseline, candidate):
    return float(cents(candidate)-cents(baseline))


def paired(scores, boss, arm, *, registration=None):
    """Four registered contrasts only. Missing weeks do not reduce the denominator."""
    if boss not in desk.BOSSES or arm not in ("B", "C"):
        raise ValueError("not a registered comparison")
    if not isinstance(registration,Registration):
        raise ValueError("provide the registered TM07 manifest, not preview scores")
    grouped = {}
    for s in scores:
        w = s["week"]
        desk.verify_seal(registration._key,"score",{k:v for k,v in s.items() if k != "attestation"},s.get("attestation"))
        if (s.get("registration") != registration.hash or w not in registration.weeks
                or s["fixture"] != registration.weeks[w]["fixture"]):
            raise ValueError("unregistered score or fixture")
        if s["arm"] in ("B","C"):
            registration.verify_neutral(w,s.get("neutral_id"),s.get("scout_hash"))
        if not s.get("invalid") and len(s["main"]["twin"]) != DRAW_COUNT:
            raise ValueError("registered comparison needs 1,000 timing draws")
        if s["boss"] != boss or s["arm"] not in ("A", arm):
            continue
        k = (s["week"], s["arm"])
        if k in grouped:
            raise ValueError("duplicate arm and week")
        grouped[k] = s
    pairs = {}
    for week in WEEKS:
        baseline, candidate = (grouped.get((week, a)) for a in ("A", arm))
        if baseline and candidate and not (baseline.get("invalid") or candidate.get("invalid")):
            if baseline["fixture"] != candidate["fixture"] or baseline.get("settings") != candidate.get("settings"):
                raise ValueError("unmatched input")
            pairs[week] = (baseline["main"], candidate["main"])
    win = lambda p: cents(p[1]["value"]) > cents(p[0]["value"])
    screen_wins = sum(w in pairs and win(pairs[w]) for w in SCREEN)
    gate = screen_wins == len(SCREEN)
    if not gate and any((w, arm) in grouped for w in EXTENSION):
        raise ValueError("extension was scored without its screen gate")
    weeks = WEEKS if gate else SCREEN
    vals = [pairs[w] for w in weeks if w in pairs]
    complete = len(vals) == len(weeks)
    wins = sum(win(p) for p in vals)
    result = dict(boss=boss, arm=arm, screen_wins=screen_wins, extension_eligible=gate,
                  weeks=len(weeks), wins=wins, missing=[w for w in weeks if w not in pairs], pass_mark=sign_mark(len(WEEKS)))
    if complete:
        blocks = [p[1] for p in vals]
        count = {len(b["twin"]) for b in blocks}
        if len(count) != 1:
            raise ValueError("inconsistent twins")
        def join(gs):
            return (prod(1+g/100 for g in gs)-1)*100
        gain = join(b["gain"] for b in blocks)
        equal = join(b["equal"] for b in blocks)
        twin = [join(xs) for xs in zip(*(b["twin"] for b in blocks))]
        mark = SW.judge(twin, gain, PERCENTILE)
        result.update(gain=gain, equal=equal, timing=mark, sign_p=sign_tail(len(weeks), wins),
                      lifts=[cent_lift(a["value"],b["value"]) for a, b in vals],
                      passes=gate and gain > equal and mark["model_above_pass_percentile"] and wins >= result["pass_mark"])
    return result


def seal_screen_gate(scores,boss,arm,registration,key):
    screened = [s for s in scores if s["week"] in SCREEN]
    result = paired(screened,boss,arm,registration=registration)
    if not result["extension_eligible"]:
        raise ValueError("did not win all three screen weeks")
    body = dict(registration=registration.hash,boss=boss,arm=arm,wins=3,screen_weeks=list(SCREEN),
                screens=desk.digest(screened))
    return dict(body=body,seal=desk.seal(key,"screen-gate",body))
