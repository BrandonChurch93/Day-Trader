"""Pure Plan 47 clocks, schema validation, score and invented-data calibration."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from math import fsum, isfinite, sqrt
from random import Random
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
ACC = re.compile(r"[0-9]{10}-[0-9]{2}-[0-9]{6}")
TICKER = re.compile(r"[A-Z][A-Z0-9]{1,14}")
PIN = re.compile(r"[0-9a-f]{64}")
# Exact Coinbase first-opening evidence for the three reviewed fallback rows.
FIRST_OPENING = {
    ("0000744452", "0001104659-25-094465", "BNB", "2025-09-29T20:01:35Z"):
        "https://x.com/CoinbaseMarkets/status/1981013406141551062",
    ("0001566610", "0001493152-25-011558", "TON", "2025-08-04T13:01:05Z"):
        "https://x.com/CoinbaseMarkets/status/1990503887820787844",
    ("0001095435", "0001171843-25-005698", "TON", "2025-09-03T13:22:05Z"):
        "https://x.com/CoinbaseMarkets/status/1990503887820787844",
}
FIRST_OPENING_ROWS = {key[:3] for key in FIRST_OPENING}
KRAKEN_LISTING = {
    "BNB": "https://blog.kraken.com/product/pro/new-assets-and-pairs-available-for-margin-trading-bnb-avnt-and-stbl",
    "TON": "https://blog.kraken.com/product/asset-listings/ton-is-available-for-trading",
}
FIELDS = {"first", "last", "lag_min", "bar_min", "hold_h", "shown_h", "coinbase_fee_bps", "kraken_fee_bps",
          "coinbase_sensitivity_bps", "halfspread_bps",
          "min_events", "min_t", "drop_best", "coin_cap", "excluded_asset", "max_news_hours",
          "cal_seed", "cal_reps", "cal_n", "cal_plant_pct", "cal_idio_pct", "cal_day_pct", "cal_btc_pct",
          "cal_tail_pct", "cal_rare_probability_pct"}


class Incomplete(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise Incomplete(code)


def exact(obj, keys, code):
    need(type(obj) is dict and set(obj) == set(keys), code)


def digest(s):
    return type(s) is str and PIN.fullmatch(s) is not None


def stamp(s):
    need(type(s) is str and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", s), "CLOCK")
    t = datetime.fromisoformat(s)
    need(t.strftime("%Y-%m-%dT%H:%M:%SZ") == s, "CLOCK")
    return t


def regular_day(s):
    need(type(s) is str, "DATE")
    d = date.fromisoformat(s)
    need(str(d) == s, "DATE")
    return d


def vals(p):
    exact(p, FIELDS, "CONFIG")
    nums = FIELDS - {"first", "last", "shown_h", "cal_n", "cal_plant_pct", "excluded_asset"}
    need(all(type(p[k]) is int and p[k] > 0 for k in nums), "CONFIG")
    need(regular_day(p["last"]) >= regular_day(p["first"]) and p["bar_min"] == 1
         and p["excluded_asset"] == "SOL" and all(p[k] + p["halfspread_bps"] < 1000
         for k in ("coinbase_fee_bps", "kraken_fee_bps", "coinbase_sensitivity_bps"))
         and p["cal_rare_probability_pct"] < 100, "CONFIG")
    for k in ("shown_h", "cal_n", "cal_plant_pct"):
        a = p[k]
        need(type(a) is list and a and all(type(x) is int and x >= 0 for x in a) and sorted(set(a)) == a, "CONFIG")
    need(p["hold_h"] not in p["shown_h"] and min(p["shown_h"]) > 0 and min(p["cal_n"]) > p["drop_best"], "CONFIG")
    return p


def u(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def sec_url(txt, cik, accession=None):
    need(type(txt) is str, "SOURCE")
    s = urlsplit(txt)
    m = re.fullmatch(r"/Archives/edgar/data/(\d+)/(\d{18})/[A-Za-z0-9_.()-]+", s.path)
    need(s.scheme == "https" and s.netloc == "www.sec.gov" and not (s.query or s.fragment)
         and m and int(m[1]) == int(cik) and (accession is None or m[2] == accession.replace("-", "")), "SOURCE")


def market_url(txt, venue):
    need(type(txt) is str, "VENUE_SOURCE")
    s = urlsplit(txt)
    suffix = ".coinbase.com" if venue == "coinbase" else ".kraken.com"
    need(s.scheme == "https" and s.hostname and s.hostname.endswith(suffix) and s.netloc == s.hostname
         and not s.fragment, "VENUE_SOURCE")


def earliest(accepted, p):
    lagged = accepted + timedelta(minutes=p["lag_min"])
    return lagged if not lagged.second else lagged.replace(second=0) + timedelta(minutes=p["bar_min"])


def fresh(row, accepted, p):
    """Only an evidenced public clock supersedes an 8-K date; filing-only must be explicit."""
    when, kind = row["public_when"], row["clock_basis"]
    event_date = row["event_date"]
    local = accepted.astimezone(NY).date()
    if event_date is not None:
        need(regular_day(event_date) <= local, "EVENT_DATE")
    if kind == "public_time":
        prior = stamp(when)
        # A separately timed release after the filing cannot backdate the public clock.
        return timedelta() <= accepted - prior <= timedelta(hours=p["max_news_hours"])
    if kind == "public_date":
        return regular_day(when) == local
    if kind == "8k_event_date":
        return row["form"] == "8-K" and when is not None and when == event_date and regular_day(when) == local
    if kind == "filing_only":
        return when is None
    return False


def events(manifest, p):
    exact(manifest, {"schema", "status", "docket_sha256", "review_sha256", "events"}, "DOCKET")
    need(type(manifest["schema"]) is int and manifest["schema"] == 1 and manifest["status"] == "REVIEWED" and all(map(digest,
         (manifest["docket_sha256"], manifest["review_sha256"]))) and type(manifest["events"]) is list
         and manifest["events"], "DOCKET")
    seen, keys, canonical = set(), set(), []
    for row in manifest["events"]:
        exact(row, {"cik", "accession", "coin", "form", "accepted_utc", "event_date", "public_when",
                    "clock_basis", "filing_url", "clock_url", "origin_key", "venue", "market_url",
                    "coinbase_status", "coinbase_status_url"}, "EVENT")
        cik, acc, coin, dt = row["cik"], row["accession"], row["coin"], stamp(row["accepted_utc"])
        need(re.fullmatch(r"\d{10}", cik) and int(cik) > 0 and ACC.fullmatch(acc) and TICKER.fullmatch(coin)
             and coin not in {"BTC", "ETH", "XBT"} and row["form"] in ("8-K", "6-K")
             and (row["form"] != "6-K" or row["event_date"] is None)
             and p["first"] <= str(dt.astimezone(NY).date()) <= p["last"], "EVENT")
        sec_url(row["filing_url"], cik, acc)
        sec_url(row["clock_url"], cik)
        need(fresh(row, dt, p), "STALE")
        first_key, origin = (cik, coin), (row["origin_key"], coin)
        need(type(origin[0]) is str and re.fullmatch(r"[A-Za-z0-9_:\-]{1,100}", origin[0])
             and first_key not in seen and origin not in keys, "DUPLICATE_EVENT")
        seen.add(first_key)
        keys.add(origin)
        v = row["venue"]
        first_opening = FIRST_OPENING.get((cik, acc, coin, u(dt)))
        is_fallback = (cik, acc, coin) in FIRST_OPENING_ROWS
        need(v == ("kraken" if is_fallback else "coinbase")
             and row["coinbase_status"] == ("listed" if v == "coinbase" else "unlisted"), "VENUE")
        market_url(row["market_url"], v)
        if v == "kraken":
            need(first_opening is not None and first_opening == row["coinbase_status_url"]
                 and row["market_url"] == KRAKEN_LISTING[coin], "VENUE_SOURCE")
        else:
            market_url(row["coinbase_status_url"], "coinbase")
        canonical.append((dt, acc, coin, v, cik))
    need(canonical == sorted(canonical), "DOCKET_ORDER")
    return canonical


def bar_keys(rows, p):
    """Minimal exact-open request keys. No forward imputation, cross-venue replacement or price access."""
    want = set()
    for t, _, coin, venue, _ in rows:
        start = earliest(t, p)
        for dt in [start] + [start + timedelta(hours=h) for h in (p["hold_h"], *p["shown_h"])]:
            want |= {(venue, f"{base}-USD", u(dt)) for base in (coin, "BTC")}
    return want


def positive(s):
    need(type(s) in (str, int, Decimal), "BAR_NUMBER")
    try:
        x = Decimal(s)
    except InvalidOperation:
        raise Incomplete("BAR_NUMBER") from None
    need(x.is_finite() and 0 < x <= Decimal("1e18") and x >= Decimal("1e-18"), "BAR_NUMBER")
    return x


def validate(packet, wanted, manifest_pin):
    """Check envelope and exactly the requested positive-volume minute bars, never compute a return."""
    exact(packet, {"schema", "manifest_sha256", "granularity_seconds", "rows"}, "BUNDLE")
    need(type(packet["schema"]) is int and packet["schema"] == 1 and packet["manifest_sha256"] == manifest_pin
         and type(packet["granularity_seconds"]) is int and packet["granularity_seconds"] == 60 and type(packet["rows"]) is list
         and len(packet["rows"]) == len(wanted), "BUNDLE")
    out = {}
    for b in packet["rows"]:
        exact(b, {"venue", "product", "time", "state", "open", "volume", "source_sha256"}, "BAR")
        key = (b["venue"], b["product"], b["time"])
        need(key in wanted and key not in out and digest(b["source_sha256"]), "BAR_KEY")
        if b["state"] == "observed":
            out[key] = positive(b["open"])
            positive(b["volume"])
        else:
            need(b["state"] == "documented_missing" and b["open"] is None and b["volume"] is None, "BAR_STATE")
            out[key] = None
    return out


def average(seq):
    return fsum(seq) / len(seq) if seq else None


def cluster_stat(rows, mean):
    n = len(rows)
    if mean is None:
        return 0, None
    groups = defaultdict(list)
    for r in rows:
        groups[r["cluster_day"]].append(Fraction(r["excess"]))
    g = len(groups)
    if g < 2:
        return g, None
    # Compare the day totals as exact binary rational observations before
    # rounding, including balanced nonconstant days and different group sizes.
    totals = [(len(xs), sum(xs)) for xs in groups.values()]
    total = sum(x for _, x in totals)
    deltas = [n * x - size * total for size, x in totals]
    if not any(deltas):
        return g, None
    ss = fsum(float(d / n)**2 for d in deltas)
    se = sqrt(g / (g - 1) * ss) / n
    return g, mean / se if se > 0 else None


def brief(rows):
    return {"n": len(rows), "raw_mean": average([r["raw_net"] for r in rows]),
            "excess_mean": average([r["excess"] for r in rows])}


def judge(rows, p):
    all_ = brief(rows)
    g, t = cluster_stat(rows, all_["excess_mean"])
    # Inputs already chronological with deterministic accession/coin tie-breaks.
    ridx = sorted(range(len(rows)), key=lambda i: (-rows[i]["excess"], i))
    drop = set(ridx[:p["drop_best"]])
    caps, counts = [], Counter()
    for r in rows:
        if counts[r["coin"]] < p["coin_cap"]:
            caps.append(r)
            counts[r["coin"]] += 1
    trim = brief([r for i, r in enumerate(rows) if i not in drop])
    exsol = brief([r for r in rows if r["coin"] != p["excluded_asset"]])
    cap = brief(caps)
    both = lambda b: b["n"] > 0 and b["raw_mean"] > 0 and b["excess_mean"] > 0
    marks = {"enough_events": all_["n"] >= p["min_events"], "raw_positive": bool(rows) and all_["raw_mean"] > 0,
             "excess_positive_cluster_t": bool(rows) and all_["excess_mean"] > 0 and t is not None and t >= p["min_t"],
             "without_best": both(trim), "without_SOL": both(exsol), "coin_cap": both(cap)}
    return all_ | {"clusters": g, "excess_cluster_t": t, "without_best": trim, "without_SOL": exsol,
                   "coin_cap": cap, "marks": marks, "passes": all(marks.values())}


def payoff(a, b, p, venue="coinbase", sensitivity=False):
    fee_key = "coinbase_sensitivity_bps" if venue == "coinbase" and sensitivity else venue + "_fee_bps"
    fee, spread = (Decimal(p[k]) / 10000 for k in (fee_key, "halfspread_bps"))
    return float((b / a) * (1 - spread) * (1 - fee) / ((1 + spread) * (1 + fee)) - 1)


def evaluate(rows, bars, p):
    out, refused, stress = {}, {}, []
    for h in (p["hold_h"], *p["shown_h"]):
        trades, missed = [], []
        for t, acc, coin, venue, cik in rows:
            start = earliest(t, p)
            end = start + timedelta(hours=h)
            lookup = lambda base, dt: bars[(venue, base + "-USD", u(dt))]
            a, b, x, y = lookup(coin, start), lookup(coin, end), lookup("BTC", start), lookup("BTC", end)
            if None in (a, b, x, y):
                missed.append({"accession": acc, "coin": coin, "venue": venue, "reason": "missing_candle",
                               "missing": [k for k, v in zip(("coin_entry", "coin_exit", "btc_entry", "btc_exit"), (a,b,x,y)) if v is None]})
                continue
            raw = payoff(a, b, p, venue)
            btc = payoff(x, y, p, venue)
            need(isfinite(raw) and isfinite(btc), "RETURN")
            trades.append({"cik": cik, "accession": acc, "coin": coin, "venue": venue, "cluster_day": str(t.date()),
                           "entry": u(start), "exit": u(end), "raw_net": raw, "btc_net": btc, "excess": raw - btc})
            if h == p["hold_h"]:
                ra, rb = payoff(a, b, p, venue, True), payoff(x, y, p, venue, True)
                stress.append({"raw_net": ra, "excess": ra - rb})
        out[str(h)] = {"summary": judge(trades, p) if h == p["hold_h"] else brief(trades), "trades": trades,
                       "missing_candle_refusals": len(missed)}
        refused[str(h)] = missed
    return {"primary_h": p["hold_h"], "windows": out, "refusals_by_hold": refused,
            "descriptive_only_below_count": not out[str(p["hold_h"])]["summary"]["marks"]["enough_events"],
            "fee_bps_per_side": {venue: p[venue + "_fee_bps"] for venue in ("coinbase", "kraken")},
            "halfspread_bps_per_side": p["halfspread_bps"], "coinbase_fee_sensitivity_shown_only":
                brief(stress) | {"coinbase_bps_per_side": p["coinbase_sensitivity_bps"]}}


def calibration(p):
    """Design sensitivity only. Simulated net benchmark drags roughly the modeled fees/spread."""
    random = Random(p["cal_seed"])
    bps0 = payoff(Decimal(1), Decimal(1), p)
    board = ["SOL"] * 4 + ["XRP"] * 2 + ["SUI", "AVAX", "DOGE", "WLD"]
    output = []
    for n in p["cal_n"]:
        trials = []
        for _ in range(p["cal_reps"]):
            groups = max(2, n * 3 // 4)
            btc = [random.gauss(0, p["cal_btc_pct"] / 100) + bps0 for _ in range(groups)]
            common = [random.gauss(0, p["cal_day_pct"] / 100) for _ in range(groups)]
            trial = []
            for i in range(n):
                d = i * groups // n
                coin = board[i % len(board)]
                rare = random.random() < p["cal_rare_probability_pct"] / 100
                e = random.gauss(0, p["cal_idio_pct"] / 100) + common[d] + (
                    random.choice((-1, 1)) * p["cal_tail_pct"] / 100 if rare else 0)
                trial.append((d, coin, btc[d], e))
            trials.append(trial)
        for plant in p["cal_plant_pct"]:
            tally = Counter({"all": 0})
            for trial in trials:
                rows = [dict(cluster_day=d, coin=c, raw_net=b + e + plant / 100, excess=e + plant / 100)
                        for d, c, b, e in trial]
                j = judge(rows, p)
                for k, ok in j["marks"].items():
                    tally[k] += ok
                tally["all"] += j["passes"]
            output.append({"n": n, "planted_net_excess_pct": plant, "simulations": p["cal_reps"],
                           "pass_pct": {k: round(v * 100 / p["cal_reps"], 2) for k, v in tally.items()}})
    return output
