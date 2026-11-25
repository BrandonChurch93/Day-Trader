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
ALPHA = 0.05/4
FIRST, LAST = date(2026, 7, 6), date(2026, 11, 16)
WEEKS = tuple((FIRST + timedelta(weeks=i)).isoformat() for i in range((LAST-FIRST).days//7+1))
EXTENSION = tuple(w for w in WEEKS if w not in SCREEN)


class UnsupportedWeek(ValueError):
    """A frozen draw cannot be represented intact on its destination tape."""


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
    count = hits = 0
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
        if any(x["why"] == "no_common_open" for x in rec["skipped"]):
            unsupported.append(at)
        if journal:
            events.extend(changes)
            scans.append(rec["scan"])
    book["last_px"].update(spec["end_marks"])
    final = max(0.0, P.value_at(book, spec["end_marks"]))
    return dict(value=final, book=book, events=events, scans=scans, immediate=count, standing=hits, unsupported=unsupported)


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


def score_week(path, draws=None, draw_sensitivities=False):
    sess, log = load_session(path)
    spec = sess.spec
    cfg = spec["cfg"]
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
                 fixture=sess.manifest["fixture"], scout_hash=sess.manifest["scout_hash"], settings=desk.digest(sess.opts))
    if (cents(check["value"]) != cents(stored["value"]) or check["book"] != stored["book"]
            or check["events"] != [d for _, k, d in log if k == "condition"]
            or check["scans"] != [d for _, k, d in log if k == "scan"]):
        raise ValueError("journal does not match replay")
    if check["unsupported"]:
        return dict(ident, invalid=f"original has no common open: {check['unsupported']}")
    n = len(bundles)
    hold = [{ "weights": {s: spec["gross"]/len(spec["symbols"]) for s in spec["symbols"]}}] + [{} for _ in range(n-1)]
    benchmark = spec["benchmark"]
    btc = [{"weights": {benchmark: 1.0}}] + [{} for _ in range(n-1)]
    by = {}
    for mult in (1, *cfg["tm06_plan"]["carried_leverage"]):
        for f in sorted(set(cfg["tm_perp_fee_levels_bps"]) | {fee}):
            gain = lambda v: (v/start-1)*100
            run = replay(sess, bundles, f, mult)
            entry = dict(value=run["value"], gain=gain(run["value"]), equal=gain(replay(sess, hold, f, mult)["value"]),
                         benchmark=gain(replay(sess, btc, f, mult)["value"]),
                         benchmark_short=gain(replay(sess, [{"weights": {benchmark: -1.0}}]+[{} for _ in range(n-1)], f, mult)["value"]),
                         stats=P.p_stats(run["book"], run["value"], start), immediate=run["immediate"], standing=run["standing"])
            if mult == 1 and f == fee or draw_sensitivities:
                twin, activity = [], []
                for i in range(draws):
                    try:
                        shuffled = shuffle_bundles(bundles, spec["rows"], spec["wakes"], spec["end"],
                                                    random.Random(f'tm06_shuffle:{seed}:{sess.sid}:{i}'))
                    except UnsupportedWeek as exc:
                        return dict(ident, invalid=str(exc), failed_draw=i)
                    trial = replay(sess, shuffled, f, mult)
                    if trial["unsupported"]:
                        return dict(ident, invalid=f"twin has no common open: {trial['unsupported']}", failed_draw=i)
                    twin.append(gain(trial["value"]))
                    activity.append(dict(immediate=trial["immediate"],standing=trial["standing"],turnover_usd=trial["book"]["traded_usd"]))
                entry.update(twin=twin,twin_activity=activity,twin_trigger_counts=[x["standing"] for x in activity],
                             judge=SW.judge(twin, entry["gain"], cfg["tm_weights_pass_percentile"]))
            by[f"{mult}x/{f:g}"] = entry
    neutral = (sess.manifest["scout"] or {}).get("usage", [])
    expected = {"boss":spec["wakes"]}
    if sess.arm != "A":
        expected.update({role:spec["wakes"] for role in desk.SCOUTS})
    return dict(ident, main=by[f"1x/{fee:g}"],
                usage=usage_totals(log,neutral,expected), unique_boss_usage=usage_totals(log,expected={"boss":spec["wakes"]}),
                neutral_scout_used=bool(neutral), by_fee_multiple=by,
                delayed_value=replay(sess, bundles, fee, delay=60)["value"] if sess.arm == "C" else None)


def cents(value):
    return Decimal(str(value)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def cent_lift(baseline, candidate):
    return float(cents(candidate)-cents(baseline))


def paired(scores, boss, arm, percentile=90):
    """Four registered contrasts only. Missing weeks do not reduce the denominator."""
    if boss not in desk.BOSSES or arm not in ("B", "C"):
        raise ValueError("not a registered comparison")
    grouped = {}
    for s in scores:
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
        mark = SW.judge(twin, gain, percentile)
        result.update(gain=gain, equal=equal, timing=mark, sign_p=sign_tail(len(weeks), wins),
                      lifts=[cent_lift(a["value"],b["value"]) for a, b in vals],
                      passes=gate and gain > equal and mark["model_above_pass_percentile"] and wins >= result["pass_mark"])
    return result
