"""Calendar, input checks, leg arithmetic, marks and synthetic power for Plan 66 (DRAFT)."""
from datetime import date
from math import floor, isfinite, sqrt
import random
from statistics import fmean, stdev

FIRST = date(2016, 1, 15)
LAST = date(2026, 11, 20)
POST = date(2023, 10, 1)
YEARS = tuple(range(2016, 2027))
N_EXPIRATIONS, N_POST = 131, 38
SHIFTED = {date(2019, 4, 18), date(2022, 4, 14), date(2025, 4, 17), date(2026, 6, 18)}
LEG_USD, SIDE_BPS, CENT = 500, 2, 0.01
MIN_PLACED, MIN_T, DROP_BEST, MIN_YEARS = 120, 2.0, 2, 7
SH_CUSIPS = ("74347B425", "74349Y753")  # SH before / after the 2024-11-07 1:4 reverse split
SPY_CUSIP, SPLG_CUSIP = "78462F103", "78464A854"  # SPLG traded as SPYM from 2025-10-31, same CUSIP
SPLG_SP500_FROM = date(2020, 1, 24)  # SPLG benchmark became the S&P 500 on this date (SEC 497K)
OPEN_RULE = "arca_opening_print"  # PENDING RULING (setting S2)
REFUSALS = ("NO_MARKS", "MISSING_PRICE", "ZERO_SHARES", "FUND_ID", "CASH_UNVERIFIED", "SPLIT_ON_EVENT")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P66_" + code)


def exact_day(x):
    need(type(x) is str, "DATE")
    d = date.fromisoformat(x)
    need(d.isoformat() == x, "DATE")
    return d


def calendar(raw):
    """Return {expiration: entry_session} after checking the pinned calendar."""
    need(type(raw) is dict and raw.get("schema") == 1 and type(raw.get("expirations")) is list, "CALENDAR")
    events = {}
    for row in raw["expirations"]:
        need(type(row) is dict and {"expiration", "entry_session", "third_friday", "source"} <= set(row), "CALENDAR")
        e, entry, tf = (exact_day(row[k]) for k in ("expiration", "entry_session", "third_friday"))
        need(tf.weekday() == 4 and 15 <= tf.day <= 21 and entry < e <= tf and e not in events, "CALENDAR")
        need((e != tf) == (e in SHIFTED), "CALENDAR")
        events[e] = entry
    need(len(events) == N_EXPIRATIONS and min(events) == FIRST and max(events) == LAST
         and sum(e >= POST for e in events) == N_POST
         and {y: sum(e.year == y for e in events) for y in YEARS} == {y: 11 if y == 2026 else 12 for y in YEARS},
         "CALENDAR")
    return events


def leg(entry_px, exit_px, cash_per_share=0.0):
    """Net return of one whole-share $500 leg, or None if no share can be bought."""
    shares = floor(LEG_USD / entry_px)
    if shares < 1:
        return None
    side = lambda px: max(SIDE_BPS / 10_000 * shares * px, CENT * shares)
    pnl = shares * (exit_px - entry_px + cash_per_share) - side(entry_px) - side(exit_px)
    return pnl / (shares * entry_px)


def gross_leg(entry_px, exit_px, cash_per_share=0.0):
    return (exit_px + cash_per_share) / entry_px - 1


def leg1_cusip(e):
    """PENDING RULING (setting S1). Recommended: SPY until SPLG tracks the S&P 500, then SPLG/SPYM."""
    return SPY_CUSIP if e < SPLG_SP500_FROM else SPLG_CUSIP


def price(x):
    return type(x) in (int, float) and isfinite(x) and x > 0


def place(events, marks, actions):
    """Per expiration: ('PLACED', leg1, leg2, gross1, gross2) or ('REFUSED', code). No output of prices."""
    out = {}
    for e in sorted(events):
        m = marks.get(e)
        if m is None:
            out[e] = ("REFUSED", "NO_MARKS")
            continue
        fund, sh = m["fund_cusip"], m["sh_cusip"]
        if not all(price(m[k]) for k in ("fund_entry_close", "fund_open", "sh_open", "sh_close")):
            out[e] = ("REFUSED", "MISSING_PRICE")
        elif fund != leg1_cusip(e) or sh not in SH_CUSIPS or fund not in actions or sh not in actions:
            out[e] = ("REFUSED", "FUND_ID")
        elif e in actions[fund]["splits"] or e in actions[sh]["splits"]:
            out[e] = ("REFUSED", "SPLIT_ON_EVENT")
        elif e in actions[fund]["unverified_cash"]:
            out[e] = ("REFUSED", "CASH_UNVERIFIED")
        else:
            cash = actions[fund]["cash"].get(e, 0.0)  # held at the entry close, so the ex-date payout is earned
            r1 = leg(m["fund_entry_close"], m["fund_open"], cash)
            r2 = leg(m["sh_open"], m["sh_close"])  # bought at the ex-date open: no SH payout is earned
            if r1 is None or r2 is None:
                out[e] = ("REFUSED", "ZERO_SHARES")
            else:
                out[e] = ("PLACED", r1, r2, gross_leg(m["fund_entry_close"], m["fund_open"], cash),
                          gross_leg(m["sh_open"], m["sh_close"]))
    return out


def sample_t(values):
    se = stdev(values) / sqrt(len(values)) if len(values) >= 2 else 0
    return fmean(values) / se if se else None


def summary(values):
    return {"n": len(values), "mean": fmean(values) if values else None, "t": sample_t(values)}


def marks(dated):
    """dated: {expiration: judged net return}. Returns (gates, detail). All marks required."""
    values = list(dated.values())
    s = summary(values)
    trimmed = fmean(sorted(values)[:-DROP_BEST]) if len(values) > DROP_BEST else None
    post = summary([v for d, v in dated.items() if d >= POST])
    years = {y: summary([v for d, v in dated.items() if d.year == y]) for y in YEARS}
    positive_years = sum(x["mean"] is not None and x["mean"] > 0 for x in years.values())
    gates = {
        "placed_at_least_120": len(values) >= MIN_PLACED,
        "mean_above_zero": s["mean"] is not None and s["mean"] > 0,
        "t_at_least_2": s["t"] is not None and s["t"] >= MIN_T,
        "mean_above_zero_without_best_2": trimmed is not None and trimmed > 0,
        "at_least_7_of_11_years_positive": positive_years >= MIN_YEARS,
        "mean_above_zero_from_october_2023": post["mean"] is not None and post["mean"] > 0,
    }
    return gates, s | {"trimmed_mean": trimmed, "post": post, "years": years, "positive_years": positive_years}


def actions_packet(raw):
    """{cusip: {"cash": {date: amount}, "unverified_cash": set, "splits": set}} from the private packet."""
    need(type(raw) is dict and set(raw) == {"schema", "funds"} and raw["schema"] == 1
         and type(raw["funds"]) is dict, "ACTIONS")
    need(set(raw["funds"]) == {SPY_CUSIP, SPLG_CUSIP, *SH_CUSIPS}, "ACTIONS")
    out = {}
    for cusip, f in raw["funds"].items():
        need(type(f) is dict and set(f) == {"source", "cash", "unverified_cash", "splits"}
             and type(f["source"]) is str and f["source"].startswith("https://"), "ACTIONS")
        cash, ids = {}, set()
        for row in f["cash"]:
            need(type(row) is dict and set(row) == {"id", "ex_date", "amount"} and type(row["id"]) is str
                 and row["id"] and row["id"] not in ids and price(row["amount"]), "ACTION_ROW")
            ids.add(row["id"])
            d = exact_day(row["ex_date"])
            cash[d] = cash.get(d, 0.0) + row["amount"]
        out[cusip] = {"cash": cash, "unverified_cash": {exact_day(x) for x in f["unverified_cash"]},
                      "splits": {exact_day(x) for x in f["splits"]}}
    return out


MARK_KEYS = {"expiration", "fund_cusip", "sh_cusip", "fund_entry_close", "fund_open", "sh_open", "sh_close"}


def marks_packet(raw, events):
    need(type(raw) is dict and set(raw) == {"schema", "open_rule", "rows"} and raw["schema"] == 1
         and raw["open_rule"] == OPEN_RULE and type(raw["rows"]) is list, "MARKS")
    out = {}
    for row in raw["rows"]:
        need(type(row) is dict and set(row) == MARK_KEYS, "MARK_ROW")
        e = exact_day(row["expiration"])
        need(e in events and e not in out, "MARK_ROW")
        need(all(row[k] is None or type(row[k]) in (int, float) for k in MARK_KEYS - {"expiration", "fund_cusip",
                                                                                         "sh_cusip"}), "MARK_ROW")
        out[e] = row
    return out


def evaluate(events, marks_in, actions):
    placed = place(events, marks_in, actions)
    net = {e: v[1] + v[2] for e, v in placed.items() if v[0] == "PLACED"}
    gates, detail = marks(net)
    refused = {}
    for v in placed.values():
        if v[0] == "REFUSED":
            refused[v[1]] = refused.get(v[1], 0) + 1
    ok = [e for e, v in placed.items() if v[0] == "PLACED"]
    quarterly = [e for e in ok if e.month in (3, 6, 9, 12)]
    return {
        "judged_net_per_expiration": detail | {"gates": gates, "passes": all(gates.values())},
        "refused_by_code": refused,
        "shown_only": {
            "leg1_net": summary([placed[e][1] for e in ok]),
            "leg2_net": summary([placed[e][2] for e in ok]),
            "leg1_gross": summary([placed[e][3] for e in ok]),
            "leg2_gross": summary([placed[e][4] for e in ok]),
            "quarterly_net": summary([net[e] for e in quarterly]),
            "other_months_net": summary([net[e] for e in ok if e not in quarterly]),
            "holiday_shifted_net": summary([net[e] for e in ok if e in SHIFTED]),
        },
        "limits": ["An ETF opening auction print is not the SOQ the source measures.",
                   "Costs are fixed assumptions, not fills. Conventional t, no serial-dependence correction.",
                   "No cash yield, tax or borrow; SH is bought, not shorted."],
    }


def synthetic_dates(events=None):
    """The 131 expirations as dates; built from the rule if no calendar is passed (synthetic only)."""
    if events is not None:
        return sorted(events)
    from datetime import timedelta
    out = []
    for y in YEARS:
        for m in range(1, 13):
            f = date(y, m, 1)
            f += timedelta((4 - f.weekday()) % 7)
            tf = f + timedelta(14)
            if tf > LAST:
                continue
            shifted = [s for s in SHIFTED if 0 < (tf - s).days < 4]
            out.append(shifted[0] if shifted else tf)
    need(len(out) == N_EXPIRATIONS, "CALENDAR")
    return out


def synthetic_power(edge_gross_bp, sd_bp, cost_bp=8.0, sims=20_000, seed=66, post_edge_gross_bp=None,
                    dates=None, tails=None):
    """Share of simulated histories passing every mark. Normal noise, or Student t with `tails` df
    rescaled to the same SD. post_edge_gross_bp replaces the edge on expirations from October 2023."""
    dates = synthetic_dates(dates)
    rng = random.Random(seed)
    scale = sqrt((tails - 2) / tails) if tails else 1.0
    mu = [((post_edge_gross_bp if (post_edge_gross_bp is not None and d >= POST) else edge_gross_bp)
           - cost_bp) / 10_000 for d in dates]
    sd = sd_bp / 10_000
    passed, per_gate = 0, {}
    for _ in range(sims):
        if tails:
            draw = lambda: rng.gauss(0, 1) / sqrt(rng.gammavariate(tails / 2, 2) / tails) * scale
        else:
            draw = lambda: rng.gauss(0, 1)
        hist = {d: m + sd * draw() for d, m in zip(dates, mu)}
        gates, _ = marks(hist)
        passed += all(gates.values())
        for k, v in gates.items():
            per_gate[k] = per_gate.get(k, 0) + v
    return {"power": passed / sims, "per_gate": {k: v / sims for k, v in per_gate.items()}}
