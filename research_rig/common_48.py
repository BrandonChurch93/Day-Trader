"""Plan 48 calendar, packet validation, spread measurement, post-lock engine and synthetic calibration."""
import csv
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
import io
import random
import re
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc
CLOCKS = ("entry", "exit", "shown_exit")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P48_" + code)


def day(value):
    need(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None, "DATE")
    return date.fromisoformat(value)


def exact(v):
    return Fraction(v)


def positive_number(value):
    # Representation bound before Fraction conversion, not a data filter.
    if type(value) is int:
        return 0 < value <= 10**30
    return (type(value) is Decimal and value.is_finite() and value > 0
            and len(value.as_tuple().digits) <= 32 and -30 <= value.adjusted() <= 30)


def nonnegative_number(value):
    return (type(value) is int and value == 0) or (type(value) is Decimal and value.is_finite() and value == 0) \
        or positive_number(value)


# ---------- calendar ----------

def turns(raw, cfg):
    """One window per December turn: anchor (first January session), formation, entry, exit, shown exit."""
    need(type(raw) is dict and set(raw) == {"calendar", "version", "sessions"} and raw["calendar"] == "XNYS"
         and raw["version"] == "4.13.3" and type(raw["sessions"]) is list, "CALENDAR")
    sessions = tuple(map(day, raw["sessions"]))
    need(sessions == tuple(sorted(set(sessions))) and all(d.weekday() < 5 for d in sessions), "CALENDAR")
    out = []
    for year in range(cfg["first_turn"], cfg["last_turn"] + 1):
        jan = [d for d in sessions if d.year == year and d.month == 1]
        dec = [d for d in sessions if d.year == year and d.month == 12]
        nxt = [d for d in sessions if d.year == year + 1 and d.month == 1]
        need(jan and len(dec) >= cfg["formation_from_end"] and len(nxt) >= cfg["shown_exit_session"], "CALENDAR")
        need(jan[0] == sessions[0] or sessions[sessions.index(jan[0]) - 1].year < year, "CALENDAR")
        formation, entry = dec[-cfg["formation_from_end"]], dec[-cfg["entry_from_end"]]
        need(cfg["entry_from_end"] == 1 and cfg["formation_from_end"] == 2
             and sessions.index(entry) == sessions.index(formation) + 1, "CALENDAR")
        need(sessions.index(nxt[0]) == sessions.index(entry) + 1, "CALENDAR")
        span = tuple(d for d in sessions if jan[0] <= d <= nxt[-1])
        out.append({"turn": year, "anchor": jan[0], "formation": formation, "entry": entry, "exit": nxt[-1],
                    "shown_exit": nxt[cfg["shown_exit_session"] - 1], "sessions": span})
    need(len(out) == cfg["turns"], "CALENDAR")
    return tuple(out)


# ---------- packet parsing ----------

TICKER = re.compile(r"[A-Z][A-Z0-9.\-]{0,9}")


def roster(blob, cfg):
    need(type(blob) is bytes and len(blob) > 0, "ROSTER")
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("P48_ROSTER") from None
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    need(rows and {"turn_year", "ticker"} <= set(rows[0]), "ROSTER")
    out = {y: [] for y in range(cfg["first_turn"], cfg["last_turn"] + 1)}
    for r in rows:
        need(type(r["turn_year"]) is str and re.fullmatch(r"\d{4}", r["turn_year"]) is not None
             and type(r["ticker"]) is str and TICKER.fullmatch(r["ticker"]) is not None, "ROSTER_ROW")
        y = int(r["turn_year"])
        if y in out:
            need(r["ticker"] not in out[y] and r["ticker"] != cfg["benchmark"], "ROSTER_ROW")
            out[y].append(r["ticker"])
    need(all(out.values()), "ROSTER_EMPTY_TURN")
    return {y: tuple(sorted(v)) for y, v in out.items()}


def bar_rows(raw, window, required_through):
    """Validated raw daily bars for one symbol; returns {session: close}. Rows may stop early (delisting),
    but none may be missing between the anchor and `required_through` when the caller requires it."""
    need(type(raw) is list, "BARS")
    allowed = set(window["sessions"])
    closes, previous = {}, None
    for row in raw:
        need(type(row) is dict and set(row) == {"t", "o", "h", "l", "c", "v"}, "BAR_FIELDS")
        t = row["t"]
        need(type(t) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", t) is not None, "BAR_TIME")
        local = datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(NY)
        d = local.date()
        need((local.hour, local.minute, local.second) == (0, 0, 0) and d in allowed
             and (previous is None or d > previous), "BAR_TIME")
        px = tuple(row[k] for k in ("o", "h", "l", "c"))
        need(all(map(positive_number, px)) and type(row["v"]) is int and row["v"] > 0, "BAR_VALUES")
        o, h, low, c = px
        need(low <= min(o, c) <= max(o, c) <= h, "BAR_VALUES")
        closes[d] = exact(c)
        previous = d
    return closes


def complete_through(closes, window, last):
    return all(d in closes for d in window["sessions"] if d <= last)


def bars_file(raw, window, names, cfg):
    need(type(raw) is dict and set(raw) == {"turn", "symbols", "benchmark"} and raw["turn"] == window["turn"]
         and type(raw["symbols"]) is dict and set(raw["symbols"]) == set(names), "BARS_FILE")
    funds = {s: bar_rows(raw["symbols"][s], window, window["entry"]) for s in names}
    bench = bar_rows(raw["benchmark"], window, window["exit"])
    need(complete_through(bench, window, window["exit"]), "BENCHMARK_BARS")
    return funds, bench


QUOTE_TIME = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?Z")


def quote_instant(t):
    m = QUOTE_TIME.fullmatch(t) if type(t) is str else None
    need(m is not None, "QUOTE_TIME")
    whole = datetime.fromisoformat(m.group(1)).replace(tzinfo=UTC)
    frac = Fraction(int(m.group(2)), 10 ** len(m.group(2))) if m.group(2) else Fraction(0)
    return Fraction(int(whole.timestamp())) + frac


def clock(session, hhmmss):
    return Fraction(int(datetime.combine(session, time.fromisoformat(hhmmss), NY).timestamp()))


def quote_rows(raw, session, cfg):
    need(type(raw) is list, "QUOTES")
    lo, hi = clock(session, cfg["cost"]["window_start"]), clock(session, cfg["cost"]["measure_end"])
    rows, previous = [], None
    for q in raw:
        need(type(q) is dict and set(q) == {"t", "bp", "ap"}, "QUOTE_FIELDS")
        t = quote_instant(q["t"])
        need(lo <= t < hi and (previous is None or t >= previous), "QUOTE_TIME")
        need(nonnegative_number(q["bp"]) and nonnegative_number(q["ap"]), "QUOTE_VALUES")
        rows.append((t, exact(q["bp"]), exact(q["ap"])))
        previous = t
    return rows


def quotes_file(raw, window, names, cfg):
    need(type(raw) is dict and set(raw) == {"turn", "sessions", "symbols", "benchmark"}
         and raw["turn"] == window["turn"] and type(raw["sessions"]) is dict and set(raw["sessions"]) == set(CLOCKS)
         and all(day(raw["sessions"][k]) == window[k] for k in CLOCKS)
         and type(raw["symbols"]) is dict and set(raw["symbols"]) == set(names), "QUOTES_FILE")

    def one(block):
        need(type(block) is dict and set(block) == set(CLOCKS), "QUOTES_FILE")
        return {k: quote_rows(block[k], window[k], cfg) for k in CLOCKS}

    return {s: one(raw["symbols"][s]) for s in names}, one(raw["benchmark"])


def distributions(raw, windows, names_by_turn, cfg):
    need(type(raw) is dict and set(raw) == {"schema", "turns"} and raw["schema"] == 1 and type(raw["schema"]) is int
         and type(raw["turns"]) is dict and set(raw["turns"]) == {str(w["turn"]) for w in windows}, "DISTRIBUTIONS")
    out = {}
    for w in windows:
        block = raw["turns"][str(w["turn"])]
        names = names_by_turn[w["turn"]]
        need(type(block) is dict and set(block) == {"symbols", "benchmark"} and type(block["symbols"]) is dict
             and set(block["symbols"]) == set(names), "DISTRIBUTIONS")

        def one(fund):
            need(type(fund) is dict and set(fund) == {"source", "cash", "splits"} and type(fund["source"]) is str
                 and re.fullmatch(r"https://\S+", fund["source"]) is not None and type(fund["cash"]) is list,
                 "DISTRIBUTION_SOURCE")
            seen, rows, prev = set(), [], None
            for r in fund["cash"]:
                need(type(r) is dict and set(r) == {"id", "ex_date", "amount"}, "DISTRIBUTION_FIELDS")
                ident, d = r["id"], day(r["ex_date"])
                need(type(ident) is str and ident and ident == ident.strip() and ident not in seen
                     and w["entry"] < d <= w["exit"] and d in w["sessions"] and positive_number(r["amount"])
                     and (prev is None or (d, ident) > prev), "DISTRIBUTION_ROW")
                seen.add(ident)
                prev = (d, ident)
                rows.append((d, exact(r["amount"])))
            need(type(fund["splits"]) is list, "SPLITS")
            splits, prev = [], None
            for r in fund["splits"]:
                # ratio = new shares per old share; the ex-date close is the first post-split close.
                need(type(r) is dict and set(r) == {"id", "ex_date", "ratio"}, "SPLIT_FIELDS")
                ident, d = r["id"], day(r["ex_date"])
                need(type(ident) is str and ident and ident == ident.strip() and ident not in seen
                     and w["anchor"] < d <= w["exit"] and d in w["sessions"] and positive_number(r["ratio"])
                     and exact(r["ratio"]) != 1 and (prev is None or d > prev), "SPLIT_ROW")
                seen.add(ident)
                prev = d
                splits.append((d, exact(r["ratio"])))
            return {"cash": rows, "splits": splits}

        bench = one(block["benchmark"])
        need(not bench["splits"], "BENCHMARK_SPLIT")
        out[w["turn"]] = ({s: one(block["symbols"][s]) for s in names}, bench)
    return out


def check_jumps(closes, splits, cfg):
    """Refuse a packet whose consecutive raw closes move by more than the configured factor on a session with
    no recorded split: an unrecorded split, not a filter. Prints nothing and returns nothing."""
    limit = exact(cfg["split_check_ratio"])
    split_days = {d for d, _ in splits}
    days = sorted(closes)
    for a, b in zip(days, days[1:]):
        r = closes[b] / closes[a]
        need(b in split_days or 1 / limit <= r <= limit, "UNRECORDED_SPLIT")


# ---------- costs ----------

def measured_half_spread(rows, session, cfg):
    """Plan 36 convention: duration-weighted median relative spread of valid uncrossed quotes over the five
    minutes ending one minute before the close, 60 s expiry, at least 180 s valid coverage. Returns half of it."""
    c = cfg["cost"]
    w0, w1 = clock(session, c["measure_start"]), clock(session, c["measure_end"])
    life = Fraction(c["expiry_seconds"])
    segments = []
    for i, (t, bp, ap) in enumerate(rows):
        end = min(rows[i + 1][0] if i + 1 < len(rows) else w1, t + life, w1)
        a, b = max(t, w0), end
        if b > a and bp > 0 and ap > bp:
            segments.append(((ap - bp) / ((ap + bp) / 2), b - a))
    covered = sum((d for _, d in segments), Fraction(0))
    if covered < c["min_coverage_seconds"]:
        return None
    running = Fraction(0)
    for s, d in sorted(segments):
        running += d
        if 2 * running >= covered:
            return s / 2
    raise AssertionError("unreachable")


def side_costs(quotes, window, cfg):
    """Per-side cost fractions for entry, exit and shown exit; the exit side is max(entry half, exit half)."""
    proxy = Fraction(cfg["cost"]["proxy_half_bps"], 10_000)
    extra = Fraction(cfg["cost"]["extra_bps"], 10_000)
    half = {k: measured_half_spread(quotes[k], window[k], cfg) for k in CLOCKS}
    entry = half["entry"] if half["entry"] is not None else proxy
    out = {"entry": entry + extra}
    for k in ("exit", "shown_exit"):
        h = half[k] if half[k] is not None else proxy
        out[k] = max(entry, h) + extra
    out["missing_exit"] = max(entry, proxy) + extra
    out["proxied"] = {k: half[k] is None for k in CLOCKS}
    return out


# ---------- post-lock engine ----------

def sleeve(closes, actions, costs, window, exit_key, budget, zero_cost=False):
    """Net dollars and shares for one whole-share sleeve bought at the entry close. A split after entry scales
    the share count from its ex-date; cash is paid per share held on the ex-date."""
    cash, splits = actions["cash"], actions["splits"]
    entry, target = window["entry"], window[exit_key]
    shares = budget // (closes[entry] * (1 + costs["entry"]))  # sizing always at judged cost
    fee_in = Fraction(0) if zero_cost else costs["entry"]
    unit = closes[entry] * (1 + fee_in)
    held = [d for d in closes if entry <= d <= target]
    last = max(held)
    missing = last != target
    fee_out = Fraction(0) if zero_cost else (costs["missing_exit"] if missing else costs[exit_key])
    def held_on(d):
        n = Fraction(shares)
        for x, ratio in splits:
            if entry < x <= d:
                n *= ratio
        return n

    payout = sum((a * held_on(d) for d, a in cash if entry < d <= last), Fraction(0))
    return held_on(last) * closes[last] * (1 - fee_out) + payout - shares * unit, shares, missing


def turn_result(window, funds, bench, quotes, cash, cfg, exit_key="exit", zero_cost=False):
    sleeve_usd, capital = exact(cfg["sleeve_usd"]), exact(cfg["capital"])
    fund_cash, bench_cash = cash
    fund_quotes, bench_quotes = quotes
    eligible = []
    for s, closes in sorted(funds.items()):
        if not complete_through(closes, window, window["entry"]):
            continue
        if any(window["anchor"] < d <= window["entry"] for d, _ in fund_cash[s]["splits"]):
            continue  # a split inside the ranking window makes the raw price return meaningless
        costs = side_costs(fund_quotes[s], window, cfg)
        dollars, shares, missing = sleeve(closes, fund_cash[s], costs, window, exit_key, sleeve_usd, zero_cost)
        if shares < 1:
            continue
        rank = closes[window["formation"]] / closes[window["anchor"]]
        eligible.append({"symbol": s, "rank": rank, "dollars": dollars, "missing": missing,
                         "proxied": costs["proxied"]})
    need(len(eligible) >= cfg["picks"], "TOO_FEW_ELIGIBLE")
    picks = sorted(eligible, key=lambda r: (r["rank"], r["symbol"]))[:cfg["picks"]]
    portfolio = sum((r["dollars"] for r in picks), Fraction(0)) / capital
    roster_ew = sum((r["dollars"] for r in eligible), Fraction(0)) / sleeve_usd / len(eligible)
    bcosts = side_costs(bench_quotes, window, cfg)
    bdollars, bshares, bmissing = sleeve(bench, bench_cash, bcosts, window, exit_key, capital, zero_cost)
    need(bshares >= 1 and not bmissing, "BENCHMARK")
    return {"turn": window["turn"], "portfolio": portfolio, "benchmark": bdollars / capital, "roster_ew": roster_ew,
            "held": [r["symbol"] for r in picks], "picks": len(picks), "eligible": len(eligible), "roster": len(funds),
            "held_missing_exit": sum(r["missing"] for r in picks),
            "eligible_missing_exit": sum(r["missing"] for r in eligible),
            "held_proxy_sides": sum(r["proxied"]["entry"] + r["proxied"][exit_key] for r in picks)}


def positive(values):
    return bool(values) and sum(values) > 0


def assess(rows, cfg):
    m = cfg["marks"]
    p = [r["portfolio"] for r in rows]
    vs_b = [r["portfolio"] - r["benchmark"] for r in rows]
    vs_ew = [r["portfolio"] - r["roster_ew"] for r in rows]
    trimmed = sorted(p, reverse=True)[m["drop_best"]:]
    marks = {
        "all_turns": len(rows) == cfg["turns"],
        "positive_mean": positive(p),
        "positive_years": sum(v > 0 for v in p) >= m["min_positive_years"],
        "beats_benchmark_mean": positive(vs_b),
        "beats_benchmark_years": sum(v > 0 for v in vs_b) >= m["min_years_ahead_of_benchmark"],
        "positive_without_best": positive(trimmed),
        "beats_roster_mean": positive(vs_ew),
    }
    return marks, all(marks.values())


def mean(values):
    values = list(values)
    return float(sum(values, Fraction(0)) / len(values)) if values else None


def evaluate(windows, packet, cfg):
    """packet[turn] = (funds, bench, quotes, cash). Runs only after the lock."""
    def run(exit_key, zero_cost=False):
        return [turn_result(w, *packet[w["turn"]], cfg, exit_key, zero_cost) for w in windows]

    judged = run("exit")
    marks, passed = assess(judged, cfg)

    def table(rows):
        return {"mean_portfolio": mean(r["portfolio"] for r in rows),
                "mean_benchmark": mean(r["benchmark"] for r in rows),
                "mean_roster_ew": mean(r["roster_ew"] for r in rows),
                "mean_portfolio_minus_benchmark": mean(r["portfolio"] - r["benchmark"] for r in rows),
                "mean_portfolio_minus_roster_ew": mean(r["portfolio"] - r["roster_ew"] for r in rows),
                "positive_years": sum(r["portfolio"] > 0 for r in rows),
                "years_ahead_of_benchmark": sum(r["portfolio"] > r["benchmark"] for r in rows),
                "mean_without_best": mean(sorted((r["portfolio"] for r in rows), reverse=True)
                                          [cfg["marks"]["drop_best"]:]),
                "years": [{k: (float(v) if isinstance(v, Fraction) else v) for k, v in r.items()} for r in rows]}

    return {"judged": table(judged) | {"marks": marks, "passed": passed},
            "shown_only": {"fifth_january_session_exit": table(run("shown_exit")),
                           "zero_cost": table(run("exit", zero_cost=True))}}


# ---------- synthetic calibration (no market data) ----------

def calibrate(cfg):
    """Pass rates of the judged marks on synthetic yearly turns. Zero edge: no loser excess over the roster and
    no roster excess over the benchmark. Beta-only: a group-wide premium with no loser excess."""
    cal = cfg["calibration"]
    scenarios = [("zero_edge", 0.0, 0.0)] + [("beta_only", float(cal["beta_only_premium"]), 0.0)] + \
        [(f"loser_edge_{e}", float(cal["beta_only_premium"]), float(e)) for e in cal["edges"][1:]]
    out = {}
    for name, premium, edge in scenarios:
        passes = 0
        for trial in range(cal["trials"]):
            rng = random.Random(cal["seed"] + trial)
            rows = []
            for y in range(cfg["turns"]):
                b = rng.gauss(0, float(cal["benchmark_sd"]))
                ew = float(cal["group_beta"]) * b + premium + rng.gauss(0, float(cal["group_residual_sd"]))
                p = ew + edge + rng.gauss(0, float(cal["loser_residual_sd"]))
                rows.append({"portfolio": exact(p), "benchmark": exact(b), "roster_ew": exact(ew)})
            passes += assess(rows, cfg)[1]
        out[name] = passes / cal["trials"]
    need(out["zero_edge"] <= float(cal["null_ceiling"]), "CALIBRATION")
    return {"data": "synthetic only, no market data", "trials": cal["trials"], "seed": cal["seed"],
            "turns": cfg["turns"], "pass_rate": out}
