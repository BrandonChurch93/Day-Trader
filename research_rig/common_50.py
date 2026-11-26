"""Plan 50: pure trading clocks, packet validation, sealed arithmetic, invented calibration."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction as F
from math import fsum, sqrt
from random import Random
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

KINDS = {"liquidation", "term", "open_ending"}
TERMINALS = {"completed", "failed", "cancelled", "no_trigger", "unresolved"}
SYMBOL = re.compile(r"[A-Z][A-Z0-9.\-]{0,11}")
TAG = re.compile(r"[A-Za-z0-9_.:-]{1,96}")
UTC = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?Z")
DATE = re.compile(r"\d{4}-\d\d-\d\d")


class Refused(Exception):
    pass


def need(ok, key):
    if not ok:
        raise Refused("P50_" + key)


def exact(obj, keys):
    return type(obj) is dict and set(obj) == set(keys.split())


def match(pattern, val):
    return type(val) is str and pattern.fullmatch(val) is not None


def utc(s):
    need(match(UTC, s), "UTC")
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def release_utc(s):
    t = utc(s)
    fraction = s.partition(".")[2].rstrip("Z")
    return t + timedelta(microseconds=int(any(x != "0" for x in fraction[6:])))


def day(s):
    need(match(DATE, s), "DATE")
    return date.fromisoformat(s)


def ny(t):
    return t.astimezone(ZoneInfo("America/New_York"))


def url(s):
    if type(s) is not str or len(s) > 1200:
        return False
    u = urlsplit(s)
    return u.scheme == "https" and bool(u.hostname) and not u.username and not u.password


def number(x, lower=0, upper=1000000, strictly=False):
    need(type(x) in (int, Decimal), "NUMBER")
    n = F(x)
    need((n > lower if strictly else n >= lower) and n <= upper, "NUMBER")
    return n


def config(p):
    need(exact(p, "capital min_placed t_cut drop_best term_sessions signal_minutes max_sessions first_day last_entry last_data coverage_pct cost benchmarks calibration")
         and all(type(p[k]) is int and p[k] > 0 for k in
                 ("capital", "min_placed", "t_cut", "drop_best", "term_sessions", "signal_minutes", "max_sessions"))
         and p["min_placed"] > p["drop_best"], "CONFIG")
    need(day(p["first_day"]) <= day(p["last_entry"]) < day(p["last_data"])
         and type(p["coverage_pct"]) is int and 0 <= p["coverage_pct"] <= 5, "CONFIG")
    c, b, a = p["cost"], p["benchmarks"], p["calibration"]
    need(exact(c, "extra_bps proxy_half_bps expiry_seconds min_coverage_seconds")
         and all(type(x) is int and x > 0 for x in c.values()) and c["min_coverage_seconds"] <= 300, "CONFIG")
    need(type(b) is dict and b and all(match(TAG, k) and match(SYMBOL, v) for k, v in b.items()), "CONFIG")
    need(exact(a, "trials seed sizes edges_pp monthly_sd_pp excess_sd_pp benchmark_sd_pp null_ceiling")
         and type(a["trials"]) is int and a["trials"] > 0 and type(a["seed"]) is int
         and type(a["sizes"]) is list and a["sizes"] and all(type(x) is int and x >= p["min_placed"] for x in a["sizes"])
         and type(a["edges_pp"]) is list and a["edges_pp"] and a["edges_pp"][0] == 0
         and all(type(x) is int and x >= 0 for x in a["edges_pp"])
         and all(type(a[k]) is int and a[k] > 0 for k in ("monthly_sd_pp", "excess_sd_pp", "benchmark_sd_pp"))
         and 0 < number(a["null_ceiling"]) <= F(1, 10), "CONFIG")
    return p


def calendar(blob):
    need(exact(blob, "calendar sessions version") and blob["calendar"] == "XNYS", "CALENDAR")
    out = {}
    previous = ""
    for row in blob["sessions"]:
        need(type(row) is list and len(row) == 3, "CALENDAR")
        s, op, cl = row
        d, a, b = day(s), utc(op), utc(cl)
        need(s > previous and d.weekday() < 5 and ny(a).date() == ny(b).date() == d
             and ny(a).strftime("%H:%M:%S") == "09:30:00"
             and ny(b).strftime("%H:%M:%S") in {"13:00:00", "14:00:00", "16:00:00"}, "CALENDAR")
        out[s] = (a, b)
        previous = s
    need(bool(out), "CALENDAR")
    return out


def signal_day(s):
    return day(s) if match(DATE, s) else ny(utc(s)).date()


def next_open(s, cal, lag):
    if match(DATE, s):
        return next((d for d in cal if d > s), None)
    bound = release_utc(s) + timedelta(minutes=lag)
    return next((d for d, (a, _) in cal.items() if a >= bound), None)


def events(packet, cal, p):
    need(exact(packet, "schema status events excluded") and type(packet["schema"]) is int and packet["schema"] == 1
         and packet["status"] == "INDEPENDENT_PRICE_BLIND_REVIEW"
         and type(packet["events"]) is list and type(packet["excluded"]) is list, "EVENTS")
    sessions = list(cal)
    need(sessions[-1] == p["last_data"] and len(sessions) > p["max_sessions"]
         and sessions[-1-p["max_sessions"]] == p["last_entry"], "HORIZON")
    rows, used, event_keys = {}, set(), set()
    for x in packet["excluded"]:
        need(exact(x, "id reason source") and match(TAG, x["id"]) and x["id"] not in used
             and x["reason"] in {"clock_unknown", "wrong_instrument", "duplicate", "no_matching_fund",
                                 "out_of_period", "term_not_operative", "not_board_backed",
                                 "exit_notice_unverifiable", "terminated_preentry"} and url(x["source"]), "EVENT_EXCLUSION")
        used.add(x["id"])
    for e in packet["events"]:
        keys = ("id ticker asset kind signal term_date terminal terminal_clock terminal_notice terminal_notice_source "
                "terms_source terminal_source asset_source listing_source")
        need(exact(e, keys) and match(TAG, e["id"]) and e["id"] not in used and match(SYMBOL, e["ticker"])
             and e["asset"] in p["benchmarks"] and e["kind"] in KINDS and e["terminal"] in TERMINALS
             and all(url(e[k]) for k in ("terms_source", "terminal_source", "asset_source", "listing_source")), "EVENT")
        used.add(e["id"])
        ent = (e["ticker"], e["kind"], e["signal"], e["term_date"])
        need(ent not in event_keys, "EVENT_DUPLICATE")
        event_keys.add(ent)
        if e["kind"] == "term":
            stated = e["term_date"]
            day(stated)
            before = [d for d in cal if d < stated]
            need(len(before) >= p["term_sessions"] and stated <= p["last_data"], "TERM_CALENDAR")
            entry = before[-p["term_sessions"]]
            observed = signal_day(e["signal"])
            # It must have been known before the selected entry. No hindsight
            # substitution of the actual payout or an after-entry extension.
            need(observed < day(entry) or (not match(DATE, e["signal"])
                 and release_utc(e["signal"]) + timedelta(minutes=p["signal_minutes"]) <= cal[entry][0]), "TERM_NOT_PUBLIC")
            cluster = entry[:7]
        else:
            need(e["term_date"] is None, "EVENT")
            entry = next_open(e["signal"], cal, p["signal_minutes"])
            cluster = str(signal_day(e["signal"]))[:7]
        need(entry is not None and p["first_day"] <= entry <= p["last_entry"], "ENTRY_CALENDAR")
        t, s = e["terminal"], e["terminal_clock"]
        need(url(e["terminal_notice_source"]) if e["terminal_notice"] is not None
             else e["terminal_notice_source"] is None, "NOTICE_SOURCE")
        stop = sessions[sessions.index(entry) + p["max_sessions"]]
        if t in {"failed", "cancelled"}:
            need(signal_day(s) >= day(entry)
                 and (match(DATE, s) or release_utc(s) > cal[entry][0]), "EXIT_CLOCK")
            end, side = next_open(s, cal, p["signal_minutes"]), 0
        elif t == "completed":
            day(s)
            need(s >= entry and (s > p["last_data"] or s in cal), "LAST_REGULAR_DAY")
            notice = e["terminal_notice"]
            if notice is None:
                # Independently established absence of a public schedule
                # (unverifiable searches instead go in the exclusion ledger).
                end, side = None, 1
            elif match(DATE, notice):
                need(day(notice) < day(s), "LAST_REGULAR_NOTICE")
                end, side = s, 1
            else:
                nd = signal_day(notice)
                close = cal[s][1] if s in cal else None
                need(nd < day(s) or (nd == day(s) and (close is None or utc(notice) < close)),
                     "LAST_REGULAR_NOTICE")
                end, side = s, 1
        else:
            need(s is None, "STOP_CLOCK")
            end, side = None, 1
        need(t == "completed" or e["terminal_notice"] is None, "NOTICE_SCOPE")
        if t == "unresolved":
            need(s is None, "UNRESOLVED_CLOCK")
        elif end is None or end > stop:
            end, side, t = stop, 1, "time_stop"
        need(end is None or end > entry or (end == entry and side == 1), "EXIT_CALENDAR")
        b = p["benchmarks"][e["asset"]]
        need(b != e["ticker"], "SELF_BENCHMARK")
        rows[e["id"]] = dict(e, entry=entry, end=end, side=side, exit_type=t, benchmark=b, cluster=cluster)
    return rows


def bar_keys(rows):
    out = set()
    for e in rows.values():
        for d in (e["entry"], e["end"]):
            if d is not None:
                out |= {(e["ticker"], d), (e["benchmark"], d)}
    return out


def quote_keys(rows):
    out = set()
    for e in rows.values():
        for d, s in ((e["entry"], 0), (e["end"], e["side"])):
            if d is not None:
                out |= {(e["ticker"], d, s), (e["benchmark"], d, s)}
    return out


def bars(blob, identity):
    need(exact(blob, "schema bars") and type(blob["schema"]) is int and blob["schema"] == 1 and type(blob["bars"]) is list, "BARS")
    out = {}
    for r in blob["bars"]:
        need(exact(r, "symbol security_id session state open close volume") and match(SYMBOL, r["symbol"]), "BAR")
        key = r["symbol"], r["session"]
        need(key not in out and key in identity and identity[key] == r["security_id"], "BAR_IDENTITY_OR_DUPLICATE")
        if r["state"] == "documented_missing":
            need(all(r[k] is None for k in ("open", "close", "volume")), "BAR_STATE")
            out[key] = None
        else:
            need(r["state"] == "present" and type(r["volume"]) is int and r["volume"] > 0, "BAR_STATE")
            out[key] = tuple(number(r[k], strictly=True) for k in ("open", "close"))
    need(set(out) == set(identity), "BAR_SCOPE")
    return out


def quote_window(r, key, identity, cal, p):
    need(exact(r, "schema symbol security_id session side updates") and type(r["schema"]) is int
         and r["schema"] == 1 and type(r["side"]) is int and (r["symbol"], r["session"], r["side"]) == key
         and r["security_id"] == identity[key[:2]] and type(r["updates"]) is list, "QUOTES")
    clock = cal[key[1]][key[2]]
    ticks = []
    for q in r["updates"]:
        need(type(q) is list and len(q) == 5 and all(type(x) is int and x >= 0 for x in q[3:]), "QUOTE")
        t = utc(q[0])
        # dt truncates after microseconds; preserve remaining vendor
        # precision in order comparisons and duration weights.
        decimal = q[0].partition(".")[2].rstrip("Z")
        tail = F(int(decimal[6:] or 0), 10 ** len(decimal)) if len(decimal) > 6 else F(0)
        delta = t - clock
        dt = F(delta.days * 86400 + delta.seconds) + F(delta.microseconds, 1000000) + tail
        need(-420 <= dt < -60 and (not ticks or dt >= ticks[-1][0]), "QUOTE_CLOCK")
        bid, ask = number(q[1]), number(q[2])
        ticks.append((dt, bid if q[3] else F(0), ask if q[4] else F(0)))
    return half_spread(ticks, p)


def half_spread(updates, p):
    """All updates end the previous interval; invalid states earn no valid time."""
    c = p["cost"]
    w0, w1 = -360, -60
    spans = []
    for i, (t, bid, ask) in enumerate(updates):
        nex = updates[i + 1][0] if i + 1 < len(updates) else w1
        weight = min(nex, t + c["expiry_seconds"], w1) - max(t, w0)
        if weight > 0 and 0 < bid < ask:
            spans.append(((ask - bid) / (ask + bid), weight))
    total = sum(w for _, w in spans)
    if total < c["min_coverage_seconds"]:
        return None
    for h, w in sorted(spans):
        total -= 2 * w
        if total <= 0:
            return h
    raise AssertionError("median")


def costs(measured, a, b, p):
    c = p["cost"]
    proxy, extra = F(c["proxy_half_bps"], 10000), F(c["extra_bps"], 10000)
    left, right = measured[a], measured[b]
    entry = proxy if left is None else left
    exit_ = max(entry, proxy if right is None else right)
    return entry + extra, exit_ + extra, int(left is None) + int(right is None)


def instruments(blob, rows):
    need(exact(blob, "schema status rows") and type(blob["schema"]) is int and blob["schema"] == 1
         and blob["status"] == "INDEPENDENT_POINT_IN_TIME_INSTRUMENT_REVIEW"
         and type(blob["rows"]) is dict and set(blob["rows"]) == set(rows), "INSTRUMENTS")
    out = {}
    for ident, x in blob["rows"].items():
        e = rows[ident]
        need(exact(x, "cef_id cef_exchange benchmark_id benchmark_exchange benchmark listing asset_source benchmark_source")
             and match(TAG, x["cef_id"]) and match(TAG, x["benchmark_id"]) and x["cef_id"] != x["benchmark_id"]
             and x["cef_exchange"] in {"NYSE", "NYSE American", "Nasdaq", "NYSE Arca"}
             and x["benchmark_exchange"] in {"NYSE", "NYSE American", "Nasdaq", "NYSE Arca", "Cboe BZX"}
             and x["benchmark"] == e["benchmark"] and x["listing"] == e["listing_source"]
             and x["asset_source"] == e["asset_source"] and url(x["benchmark_source"]), "INSTRUMENT")
        for d in (e["entry"], e["end"]):
            if d is not None:
                for sym, stable in ((e["ticker"], x["cef_id"]), (e["benchmark"], x["benchmark_id"])):
                    need(out.setdefault((sym, d), stable) == stable, "INSTRUMENT_COLLISION")
    need(set(out) == bar_keys(rows), "INSTRUMENT_SCOPE")
    return out


def actions(blob, rows):
    need(exact(blob, "schema status rows") and type(blob["schema"]) is int and blob["schema"] == 1
         and blob["status"] == "INDEPENDENT_ISSUER_CASH_AND_ACTION_REVIEW"
         and type(blob["rows"]) is dict and set(blob["rows"]) == set(rows), "ACTIONS")
    out = {}
    for ident, x in blob["rows"].items():
        e = rows[ident]
        need(exact(x, "cef benchmark claims intervening coverage")
             and all(type(x[k]) is list for k in ("cef", "benchmark", "claims", "intervening"))
             and exact(x["coverage"], "cef benchmark") and all(url(s) for s in x["coverage"].values()), "ACTION")
        if e["end"] is None:
            need(not any(x[k] for k in ("cef", "benchmark", "claims", "intervening")), "UNRESOLVED_ACTIONS")
        ids = set()
        undoc = {"cef": 0, "benchmark": 0}
        def cash(leg):
            vals = []
            for d in x[leg]:
                need(exact(d, "id kind ex_date amount source") and match(TAG, d["id"]) and (leg, d["id"]) not in ids
                     and d["kind"] in {"ordinary", "interim"} and url(d["source"]), "CASH")
                ids.add((leg, d["id"]))
                s = day(d["ex_date"])
                # On an opening exit the holder was already entitled at the
                # open on that date. The buyer on the entry ex-date was not.
                need(day(e["entry"]) < s <= day(e["end"]), "CASH_CLOCK")
                if d["amount"] is None:
                    need(d["kind"] == "interim", "CASH")
                    undoc[leg] += 1
                else:
                    vals.append(number(d["amount"], strictly=True))
            return sum(vals, F(0))
        cef, bench = cash("cef"), cash("benchmark")
        claims, final = F(0), False
        for d in x["claims"]:
            need(exact(d, "id kind entitlement_date paid_date amount source") and match(TAG, d["id"])
                 and d["kind"] in {"late_interim", "final"} and ("cef", d["id"]) not in ids and url(d["source"])
                 and e["exit_type"] == "completed" and e["kind"] in {"liquidation", "term"}
                 and day(e["entry"]) < day(d["entitlement_date"]) <= day(d["paid_date"])
                 and (d["kind"] == "final" or day(e["end"]) < day(d["entitlement_date"])), "CLAIM")
            if d["kind"] == "final":
                need(not final, "FINAL_CASH_DUPLICATE")
                final = True
            ids.add(("cef", d["id"]))
            claims += number(d["amount"], strictly=True)
        issues = set()
        for d in x["intervening"]:
            need(exact(d, "id leg kind date source") and match(TAG, d["id"]) and d["id"] not in issues
                 and d["leg"] in {"cef", "benchmark"} and d["kind"] in {"reverse_split", "forward_split", "merger"}
                 and url(d["source"]) and day(e["entry"]) < day(d["date"]) <= day(e["end"]), "INTERVENING")
            issues.add(d["id"])
        out[ident] = dict(cef=cef, benchmark=bench, claims=claims, issues=issues, final_documented=final,
                          undocumented_interims=undoc)
    return out


def avg(xs):
    if not xs:
        return None
    return float(sum(xs) / len(xs)) if all(isinstance(x, F) for x in xs) else fsum(xs) / len(xs)


def clustered_t(rows):
    if not rows:
        return 0, None
    groups = defaultdict(list)
    for r in rows:
        groups[r["cluster"]].append(F(r["excess"]))
    g, n = len(groups), len(rows)
    if g < 2:
        return g, None
    total = sum(sum(x) for x in groups.values())
    residual = [n * sum(x) - len(x) * total for x in groups.values()]
    if not any(residual):
        return g, None
    se = sqrt(g / (g - 1) * fsum(float(d / n) ** 2 for d in residual)) / n
    return g, float(total / n) / se if se else None


def summary(rows):
    return dict(n=len(rows), raw_mean=avg([x["raw"] for x in rows]),
                paired_mean=avg([x["excess"] for x in rows]),
                positive=sum(x["raw"] > 0 for x in rows))


def judge(rows, p):
    main = summary(rows)
    count, t = clustered_t(rows)
    trimmed = summary(sorted(rows, key=lambda r: (-r["excess"], r["id"]))[p["drop_best"]:])
    def pos(x):
        return x is not None and x > 0
    marks = dict(count=main["n"] >= p["min_placed"], raw=pos(main["raw_mean"]),
                 paired=pos(main["paired_mean"]) and t is not None and t >= p["t_cut"],
                 trim=pos(trimmed["raw_mean"]) and pos(trimmed["paired_mean"]),
                 breadth=bool(rows) and 2 * main["positive"] >= main["n"])
    return dict(main=main, trimmed=trimmed, clusters=count, paired_cluster_t=t, marks=marks, passed=all(marks.values()),
                descriptive_only=not marks["count"])


def placement(e, b, q, a, p):
    et, bt = e["ticker"], e["benchmark"]
    d, x, s = e["entry"], e["end"], e["side"]
    if not b[et, d] or not b[bt, d]:
        return "missing_entry", None
    if x is None:
        return "unresolved_exit_clock", None
    if a["issues"]:
        return "intervening_action", None
    if not b[et, x] or not b[bt, x]:
        return "missing_exit", None
    ce, cx, cp = costs(q, (et, d, 0), (et, x, s), p)
    be, bx, bp = costs(q, (bt, d, 0), (bt, x, s), p)
    cap = F(p["capital"])
    en, bn = b[et, d][0] * (1 + ce), b[bt, d][0] * (1 + be)
    n, m = cap // en, cap // bn
    if not n or not m:
        return "unaffordable", None
    return None, (en, bn, n, m, cx, bx, cp + bp)


def coverage(rows, placed, refused, p):
    types = {k: sum(rows[x]["kind"] == k for x in placed) for k in sorted(KINDS)}
    unresolved = sum(x in {"missing_entry", "missing_exit", "unresolved_exit_clock"} for x in refused.values())
    return dict(placed=len(placed), by_type=types, clusters=len({rows[x]["cluster"] for x in placed}),
                refused=dict(sorted(Counter(refused.values()).items())), unresolved=unresolved,
                coverage_ok=100 * unresolved <= p["coverage_pct"] * len(placed))


def prepare(rows, b, q, a, p):
    placed, refused = {}, {}
    for ident, e in sorted(rows.items()):
        fail, fill = placement(e, b, q, a[ident], p)
        if fail:
            refused[ident] = fail
        else:
            placed[ident] = fill
    return placed, refused, coverage(rows, placed, refused, p)


def evaluate(rows, b, a, p, prepared):
    fills, refused, disposition = prepared
    placed = []
    for ident, (entry, base_entry, n, m, cost, base_cost, proxied) in fills.items():
        e, t = rows[ident], a[ident]
        d, s = e["end"], e["side"]
        sell, base_sell = b[e["ticker"], d][s] * (1-cost), b[e["benchmark"], d][s] * (1-base_cost)
        gross = n * (sell + t["cef"] - entry) / p["capital"]
        base = m * (base_sell + t["benchmark"] - base_entry) / p["capital"]
        # No fictitious last-sale fallback and never a zero-imputed final
        # payout. Cash hold is a non-judged separate denominator.
        shown = n * (t["claims"] + t["cef"] - entry) / p["capital"] if t["final_documented"] else None
        placed.append(dict(id=ident, kind=e["kind"], exit_type=e["exit_type"], cluster=e["cluster"], entry=e["entry"], exit=d,
                           raw=gross, benchmark=base, excess=gross-base, shares=n,
                           benchmark_shares=m, proxied_sides=proxied, undocumented_interims=t["undocumented_interims"],
                           shown_documented_cash_raw=float(shown) if shown is not None else None))
    result = judge(placed, p)
    inconclusive = not disposition["coverage_ok"]
    shown = [x["shown_documented_cash_raw"] for x in placed if x["shown_documented_cash_raw"] is not None]
    return result | dict(passed=result["passed"] and not inconclusive, inconclusive=inconclusive,
                         verdict=("INCONCLUSIVE" if inconclusive else "PASS" if result["passed"] else "FAIL"),
                         descriptive_only=result["descriptive_only"] or inconclusive,
                         rows=[x | {k: float(x[k]) for k in ("raw", "benchmark", "excess")} for x in placed],
                         refusals=refused, placement=disposition,
                         by_type={k: summary([x for x in placed if x["kind"] == k]) for k in sorted(KINDS)},
                         proxied_sides=sum(x["proxied_sides"] for x in placed),
                         intervening_actions=sum(bool(x["issues"]) for x in a.values()),
                         undocumented_interims={k: sum(x["undocumented_interims"][k] for x in a.values())
                                                for k in ("cef", "benchmark")},
                         shown_documented_cash=dict(n=len(shown), raw_mean=avg(shown)))


def calibrate(p):
    a = p["calibration"]
    report = []
    for n in a["sizes"]:
        groups = max(4, n // 2)
        for edge in a["edges_pp"]:
            rng = Random(a["seed"] + n)
            counts = Counter()
            for _ in range(a["trials"]):
                shared = [rng.gauss(0, a["monthly_sd_pp"] / 100) for k in range(groups)]
                rows = []
                for j in range(n):
                    g = j % groups
                    bm = rng.gauss(0, a["benchmark_sd_pp"] / 100)
                    ex = edge / 100 + shared[g] + rng.gauss(0, a["excess_sd_pp"] / 100)
                    rows.append(dict(id=str(j), raw=bm + ex, excess=ex, cluster=g))
                result = judge(rows, p)
                counts.update(k for k, v in result["marks"].items() if v)
                counts["all"] += result["passed"]
            report.append(dict(n=n, groups=groups, planted_net_excess_pp=edge, trials=a["trials"],
                               pass_rate={k: v / a["trials"] for k, v in sorted(counts.items())}))
    return dict(schema=1, model="synthetic net control + correlated monthly paired shocks",
                null_ceiling=float(a["null_ceiling"]), cells=report)
