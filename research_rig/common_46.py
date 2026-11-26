"""Plan 46 calendar, strict candle validation, and the two frozen estimators."""
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
import math
import re
from statistics import fmean

LEGS = ("A", "B")
BTC = "BTC"
URL = r"https://www\.cftc\.gov/"
DETAIL = URL + r"IndustryOversight/IndustryFilings/TradingOrganizationProducts/[0-9]+"
PDF = URL + r"(?:sites/default/files/)?filings/(?:ptc|orgrules)/[A-Za-z0-9_/.-]+\.pdf"


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P46_" + code)


def day(token):
    need(type(token) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", token), "DATE")
    try:
        return date.fromisoformat(token)
    except ValueError:
        raise Refused("P46_DATE") from None


def config(cfg):
    ints = ("entry_lag_days", "a_min_hold_days", "b_start_days", "b_hold_days", "min_events", "trim_dates",
            "a_fee_bps", "a_half_spread_bps", "b_fee_bps", "b_half_spread_bps", "b_funding_bps_per_day",
            "a_sensitivity_fee_bps",
            "spot_btc_half_spread_bps", "perp_btc_half_spread_bps")
    other = {"min_dates", "min_t", "asof", "first_post", "rows", "source", "queue", "ledger"}
    need(type(cfg) is dict and set(cfg) == set(ints) | other
         and all(type(cfg[k]) is int and 0 <= cfg[k] < 10000 for k in ints)
         and min(cfg[k] for k in ints[:6]) > 0
         and type(cfg["min_dates"]) is dict and set(cfg["min_dates"]) == set(LEGS)
         and all(type(n) is int and n > cfg["trim_dates"] for n in cfg["min_dates"].values())
         and type(cfg["min_t"]) in (int, Decimal) and cfg["min_t"] > 0
         and type(cfg["rows"]) is int and cfg["rows"] > 0
         and cfg["source"] == "coinbase_exchange_utc_daily"
         and type(cfg["queue"]) is int and cfg["queue"] == 83
         and cfg["ledger"] == {"A": 179, "B": 181}
         and day(cfg["first_post"]) <= day(cfg["asof"]), "CONFIG")
    return cfg


def docket(blob, cfg):
    need(type(blob) is list and len(blob) == cfg["rows"], "DOCKET")
    rows, seen = [], set()
    for r in blob:
        need(type(r) is dict and set(r) == {"post", "launch", "coin", "venue", "detail", "filing"}, "DOCKET")
        post = day(r["post"])
        launch = day(r["launch"]) if r["launch"] is not None else None
        coin, venue = r["coin"], r["venue"]
        need(day(cfg["first_post"]) <= post <= day(cfg["asof"])
             and type(coin) is str and re.fullmatch(r"[A-Z0-9]{2,12}", coin) and coin not in {"BTC", "ETH"}
             and venue in {"BTNL", "CDNA", "CME", "COIN", "KEX"}
             and type(r["detail"]) is str and re.fullmatch(DETAIL, r["detail"])
             and type(r["filing"]) is str and re.fullmatch(PDF, r["filing"]), "DOCKET")
        key = (post, venue, coin)
        need(key not in seen, "DOCKET_DUPLICATE")
        seen.add(key)
        rows.append((post, launch, coin, venue, r["detail"]))
    need(rows == sorted(rows, key=lambda r: (r[0], r[3], r[2], r[4])), "DOCKET_ORDER")
    return rows


def planned(rows, cfg):
    first = {}
    for row in rows:
        post, launch, coin, venue, detail = row
        first[coin] = min(first.get(coin, (post, venue, detail)), (post, venue, detail))
    holds, skips = {}, {}
    for leg in LEGS:
        picks, excluded = [], Counter()
        for post, launch, coin, venue, detail in rows:
            if launch is None:
                excluded["unknown_trade_date"] += 1
                continue
            aware = post + timedelta(days=cfg["entry_lag_days"])
            if leg == "A":
                start, stop = aware, launch
                if (stop - start).days < cfg["a_min_hold_days"]:
                    excluded["short_notice"] += 1
                    continue
            else:
                start = max(launch + timedelta(days=cfg["b_start_days"]), aware)
                stop = start + timedelta(days=cfg["b_hold_days"])
            if stop > day(cfg["asof"]):
                excluded["right_censored"] += 1
                continue
            picks.append((start, post, venue, detail, stop, coin, (post, venue, detail) == first[coin], launch))
        last, holds[leg] = {}, []
        for start, post, venue, detail, stop, coin, first_, launch in sorted(picks):
            if coin in last and start < last[coin]:
                excluded["same_coin_overlap"] += 1
                continue
            last[coin] = stop
            holds[leg].append((start, post, venue, detail, stop, coin, first_, launch))
        skips[leg] = dict(excluded)
    return holds, skips


def endpoints(leg, start, stop):
    # A enters the bucket's first trade, then exits on the final trade before launch.
    # B uses the first trade of each boundary bucket exactly seven calendar days apart.
    return (start, stop - timedelta(days=1), "close") if leg == "A" else (start, stop, "open")


def required(holds):
    wanted = defaultdict(set)
    for leg in LEGS:
        for start, _, _, _, stop, coin, _, _ in holds[leg]:
            e, x, _ = endpoints(leg, start, stop)
            for asset in (coin, BTC):
                for offset in range((x - e).days + 1):
                    wanted[asset].add(e + timedelta(days=offset))
    return dict(wanted)


def candle_tape(blob, days):
    # Private custodian records confirmed absent buckets as null; never replace with a price.
    need(type(blob) is dict and set(blob) == {d.isoformat() for d in days}, "CANDLE_GRID")
    parsed = {}
    for token, v in blob.items():
        if v is None:
            continue
        need(type(v) is list and len(v) == 5
             and all(type(x) in (int, Decimal) and Decimal(x).is_finite() and 0 < x <= 10**15 for x in v),
             "CANDLE_FIELD")
        lo, hi, o, c, volume = map(Decimal, v)
        need(lo <= min(o, c) <= max(o, c) <= hi and volume > 0, "CANDLE_RANGE")
        o_, c_ = float(o), float(c)
        need(min(o_, c_) >= 1e-100, "CANDLE_RANGE")
        parsed[day(token)] = (o_, c_)
    return parsed


def execution(leg, holds, tapes):
    placed, missing = [], Counter()
    for trade in holds:
        start, _, _, _, stop, coin, _, _ = trade
        e, x, _ = endpoints(leg, start, stop)
        dates = [e + timedelta(days=i) for i in range((x - e).days + 1)]
        absent = [all(d in tapes[s] for d in dates) for s in (coin, BTC)]
        if not all(absent):
            missing["coin_gap" if absent[1] else "btc_gap" if absent[0] else "coin_and_btc_gap"] += 1
        else:
            placed.append(trade)
    return placed, dict(missing)


def return_net(leg, entry, exit_, days, cfg, btc=False):
    # Linear unlevered P&L on entry notional. Fee charged on each adverse fill.
    sign = 1 if leg == "A" else -1
    fee = cfg["a_fee_bps" if leg == "A" else "b_fee_bps"] / 10000
    spread_key = (("spot_btc_half_spread_bps" if leg == "A" else "perp_btc_half_spread_bps")
                  if btc else ("a_half_spread_bps" if leg == "A" else "b_half_spread_bps"))
    half = cfg[spread_key] / 10000
    buy_sell_entry = entry * (1 + sign * half)
    buy_sell_exit = exit_ * (1 - sign * half)
    funding = cfg["b_funding_bps_per_day"] * days / 10000 if leg == "B" else 0.0
    return (sign * (buy_sell_exit - buy_sell_entry) - fee * (buy_sell_entry + buy_sell_exit)) / entry - funding


def clustered(pairs):
    n = len(pairs)
    totals = defaultdict(float)
    mean = fmean(x for _, x in pairs) if n else None
    for group, value in pairs:
        totals[group] += value - mean
    g = len(totals)
    constant = bool(pairs) and all(value == pairs[0][1] for _, value in pairs)
    se = math.sqrt(g / (g - 1) * math.fsum(v * v for v in totals.values())) / n if g > 1 else None
    if g > 1 and constant:
        se = 0.0
    # Degenerate variance is uninformative, not an automatic pass.
    t = mean / se if se else None
    return {"n": n, "posting_dates": g, "mean": mean, "clustered_se": se, "t": t}


def assess(rows, cfg, leg):
    groups = defaultdict(list)
    for r in rows:
        groups[r["post"]].append(r["paired"])
    top = sorted(groups, key=lambda d: (-fmean(groups[d]), d))[:cfg["trim_dates"]]
    paired = clustered([(r["post"], r["paired"]) for r in rows])
    net = clustered([(r["post"], r["net"]) for r in rows])
    trimmed = clustered([(r["post"], r["paired"]) for r in rows if r["post"] not in top])
    first = [r for r in rows if r["first_in_docket"]]
    shown = {k: clustered([(r["post"], r[k]) for r in first]) for k in ("paired", "net")}
    marks = {
        "minimum_events": paired["n"] >= cfg["min_events"],
        "minimum_posting_dates": paired["posting_dates"] >= cfg["min_dates"][leg],
        "positive_raw_net": net["mean"] is not None and net["mean"] > 0,
        "positive_paired_net": paired["mean"] is not None and paired["mean"] > 0,
        "minimum_paired_t": paired["t"] is not None and paired["t"] >= float(cfg["min_t"]),
        "positive_paired_without_best_dates": trimmed["mean"] is not None and trimmed["mean"] > 0,
    }
    return {"marks": marks, "passed": all(marks.values()), "net": net, "paired": paired, "trimmed": trimmed,
            "removed_posting_dates": top, "shown_only_first_in_docket": shown}


def evaluate(holds, skips, tapes, cfg):
    result = {}
    for leg in LEGS:
        selected, gaps = execution(leg, holds[leg], tapes)
        rows, fee_sensitivity = [], []
        for start, post, venue, detail, stop, coin, first_, launch in selected:
            e, x, exit_field = endpoints(leg, start, stop)
            index = int(exit_field == "close")
            returns = [return_net(leg, tapes[s][e][0], tapes[s][x][index], (stop - start).days, cfg, s == BTC)
                       for s in (coin, BTC)]
            rows.append({"post": post.isoformat(), "launch": launch.isoformat(), "entry_bucket": e.isoformat(),
                         "exit_bucket": x.isoformat(), "launch_before_post": launch < post,
                         "coin": coin, "venue": venue, "detail": detail, "first_in_docket": first_,
                         "net": returns[0], "btc_net": returns[1], "paired": returns[0] - returns[1]})
            if leg == "A":
                alt_fee = cfg | {"a_fee_bps": cfg["a_sensitivity_fee_bps"]}
                alt = [return_net(leg, tapes[s][e][0], tapes[s][x][index], (stop - start).days, alt_fee, s == BTC)
                       for s in (coin, BTC)]
                fee_sensitivity.append((post.isoformat(), alt[0], alt[0] - alt[1]))
        result[leg] = assess(rows, cfg, leg) | {"ledger": cfg["ledger"][leg], "rows": rows,
                                                    "calendar_skips": skips[leg], "data_skips": gaps}
        if leg == "B":
            result[leg]["shown_only_without_negative_notice"] = {
                k: clustered([(r["post"], r[k]) for r in rows if not r["launch_before_post"]])
                for k in ("net", "paired")
            }
        else:
            result[leg]["shown_only_fee_sensitivity"] = {
                "fee_bps_per_side": cfg["a_sensitivity_fee_bps"],
                "net": clustered([(p, n) for p, n, _ in fee_sensitivity]),
                "paired": clustered([(p, x) for p, _, x in fee_sensitivity]),
            }
    return {"legs": result}
