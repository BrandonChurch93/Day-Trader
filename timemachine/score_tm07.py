"""Scores one saved week at a time. Nothing is opened on import."""
from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from math import comb, prod
import json
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


class Registration:
    """A separately operator-sealed attempt, not inputs asserted by an arm."""
    def __init__(self,document,key):
        self._key = key
        self.body = json.loads(desk.encode(document["body"]))
        desk.verify_seal(key,"registration",self.body,document.get("seal"))
        self.hash = desk.digest(self.body)
        if self.body.get("version") != "TM07-v1" or not self.body.get("runner_id") or not self.body.get("ledger_ref"):
            raise ValueError("register the runner and ledger reference before launch")
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
        arm, scout = manifest["arm"], manifest["scout"]
        model = "gemini_neon" if arm == "scout" else manifest["boss"]
        if manifest.get("model_build") != self.body["builds"][model]["id"]:
            raise ValueError("unregistered model build")
        if arm == "scout" and sid != item["neutral_id"] or arm in ("B","C") and scout["neutral_id"] != item["neutral_id"]:
            raise ValueError("arm did not use designated neutral scout")
        from itertools import groupby
        good = {t//3600*3600 for t,rows in groupby(spec["minutes"],key=lambda r:r[0])
                if set(spec["symbols"]) <= {r[1] for r in rows}}
        if not set(spec["wakes"]) <= good or any(not set(spec["symbols"]) <= r["marks"].keys() for r in spec["rows"]):
            raise ValueError("registered twin coverage lacks marks or a common open")
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
    if book.get("desk_liquidation") and spec["end"] not in unsupported:
        unsupported.append(spec["end"])
    book["last_px"].update(spec["end_marks"])
    final = max(0.0, P.value_at(book, spec["end_marks"]))
    return dict(value=final, book=book, events=events, scans=scans, immediate=count, standing=hits,
                triggered=triggered, unsupported=unsupported)


def buy_and_hold(sess, weights, fee, multiple=1):
    """Fully fund every declared leg together after explicit fee and spread."""
    spec = sess.spec
    pp = P.with_fee(sess.pp,fee)
    book = P.new_book(spec["cfg"]["tm_account_start_usd"])
    weights = {s:w*multiple for s,w in sorted(weights.items())}
    required = set(weights)
    if not required <= set(pp["symbols"]) or not required <= spec["end_marks"].keys():
        raise UnsupportedWeek("benchmark lacks priced symbols or final marks")
    at,end = spec["wakes"][0],spec["end"]
    cutoff = min(at+3600,end)
    gross = sum(abs(w) for w in weights.values())
    cost = sum(abs(w)*(pp["hs"][s]+pp["fee"][s]*(1+pp["hs"][s]*(1 if w > 0 else -1)))
               for s,w in weights.items())
    entered = []

    def enter(tick,opens,protected):
        if entered or tick >= cutoff or not required <= opens.keys():
            return
        budget = book["cash"]/(1+cost)
        need = sum(abs(w)*budget*pp["maint"][s] for s,w in weights.items())
        if budget < need:
            raise UnsupportedWeek("benchmark cannot meet maintenance at its first common open")
        for s,w in weights.items():
            entered.append(P.trade(book,s,w*budget/opens[s],opens[s],pp))
        book["target"] = dict(weights)
        return required

    rows = P.scan_rows(sess.minutes,at,end,required)
    O.Orders().advance(book,pp,rows,at,end,gross,on_open=enter,last=True)
    if len(entered) != len(weights) or book.get("desk_liquidation"):
        raise UnsupportedWeek("benchmark has no executable full-book open")
    book["last_px"].update(spec["end_marks"])
    return dict(value=max(0.0,P.value_at(book,spec["end_marks"])),book=book,entries=entered)


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
    by = {}
    for mult in (1, *cfg["tm06_plan"]["carried_leverage"]):
        for f in sorted(set(cfg["tm_perp_fee_levels_bps"]) | {fee}):
            gain = lambda v: (v/start-1)*100
            run = replay(sess, bundles, f, mult)
            try:
                equal, btc_long, btc_short = (gain(buy_and_hold(sess,w,f,mult)["value"])
                                              for w in (hold,{benchmark:1.0},{benchmark:-1.0}))
            except UnsupportedWeek as exc:
                return emit(dict(ident,invalid=str(exc)))
            entry = dict(value=run["value"], gain=gain(run["value"]), equal=equal,
                         benchmark=btc_long, benchmark_short=btc_short,
                         stats=P.p_stats(run["book"], run["value"], start), immediate=run["immediate"], standing=run["standing"])
            if mult == 1 and f == fee or draw_sensitivities:
                twin, activity = [], []
                for i in range(draws):
                    try:
                        shuffled = shuffle_bundles(bundles, spec["rows"], spec["wakes"], spec["end"],
                                                    random.Random(f'tm06_shuffle:{seed}:{sess.sid}:{i}'))
                    except UnsupportedWeek as exc:
                        return emit(dict(ident, invalid=str(exc), failed_draw=i))
                    trial = replay(sess, shuffled, f, mult)
                    if trial["unsupported"]:
                        return emit(dict(ident, invalid=f"twin has no common open: {trial['unsupported']}", failed_draw=i))
                    twin.append(gain(trial["value"]))
                    activity.append(dict(immediate=trial["immediate"],standing=trial["standing"],triggered=trial["triggered"],
                                         turnover_usd=trial["book"]["traded_usd"]))
                entry.update(twin=twin,twin_activity=activity,twin_trigger_counts=[x["triggered"] for x in activity],
                             twin_standing_fill_counts=[x["standing"] for x in activity],
                             judge=SW.judge(twin, entry["gain"], cfg["tm_weights_pass_percentile"]))
            by[f"{mult}x/{f:g}"] = entry
    neutral = (sess.manifest["scout"] or {}).get("usage", [])
    expected = {"boss":spec["wakes"]}
    if sess.arm != "A":
        expected.update({role:spec["wakes"] for role in desk.SCOUTS})
    return emit(dict(ident, main=by[f"1x/{fee:g}"],
                usage=usage_totals(log,neutral,expected), unique_boss_usage=usage_totals(log,expected={"boss":spec["wakes"]}),
                neutral_scout_used=bool(neutral), by_fee_multiple=by,
                delayed_value=replay(sess, bundles, fee, delay=60)["value"] if sess.arm == "C" else None))


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
    scouts = {}
    for s in scores:
        w = s["week"]
        desk.verify_seal(registration._key,"score",{k:v for k,v in s.items() if k != "attestation"},s.get("attestation"))
        if (s.get("registration") != registration.hash or w not in registration.weeks
                or s["fixture"] != registration.weeks[w]["fixture"]):
            raise ValueError("unregistered score or fixture")
        if s["arm"] in ("B","C"):
            if (not s.get("scout_hash") or s.get("neutral_id") != registration.weeks[w]["neutral_id"]
                    or scouts.setdefault(w,s["scout_hash"]) != s["scout_hash"]):
                raise ValueError("different neutral scout stream for the same week")
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
