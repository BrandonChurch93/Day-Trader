"""Plan 23 calibration on planted paths. Invented bars only; no real bar is opened.

For each seed and each planted edge (percent of the entry price, added evenly over sessions 2 to 5), it makes one
invented bar file per judged event, with that event's real pricing date (from events_selected.csv, prospectus data
only) so the years and the 2023-on slice have the real shape, and a made-up SPY. The files go through the same
trade() and judge() the real run uses. It counts how many seeds pass all eight marks, and each mark alone.

  python3 calibrate_23.py            writes calibration_23.json next to this file and prints the table
"""
import datetime as dt, json, math, os, random

import common_23 as C
import fetch_23 as F


def bdays(a, b):
    d, out = dt.date.fromisoformat(a), []
    end = dt.date.fromisoformat(b)
    while d <= end:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def t_noise(rng, df):
    # Student t with df degrees of freedom, scaled to unit variance.
    z = rng.gauss(0, 1)
    chi = sum(rng.gauss(0, 1) ** 2 for _ in range(df))
    return z / math.sqrt(chi / df) / math.sqrt(df / (df - 2))


def world(events, p, seed, edge):
    rng = random.Random(seed)
    days = bdays("2017-03-01", str(p["bar_end"]))
    spy_px, spy = 100.0, {}
    daily_spy = p["calibration_spy_sigma"] / math.sqrt(p["exit_session"] - 1)   # session-1 close to session-5 close: 4 returns
    for d in days:
        o = spy_px
        spy_px *= 1 + rng.gauss(0, daily_spy)
        spy[d] = dict(d=d, o=o, h=max(o, spy_px), l=min(o, spy_px), c=spy_px, v=1)
    year_shock = {y: rng.gauss(0, p["calibration_year_sigma"]) for y in range(2017, 2027)}
    idio = math.sqrt(max(1e-12, p["calibration_trade_sigma"] ** 2 - (p["calibration_beta"] * p["calibration_spy_sigma"]) ** 2))
    trades = []
    for e in events:
        first = next(d for d in days if d > e["pricing_date"])
        i = days.index(first)
        win = days[i:i + p["exit_window_sessions"]]
        px, bars = 20.0, []
        for k, d in enumerate(win):
            o = px
            if k:
                r_spy = spy[d]["c"] / spy[days[days.index(d) - 1]]["c"] - 1
                drift = (edge + year_shock[int(d[:4])]) / (p["exit_session"] - 1) if k < p["exit_session"] else 0.0
                px *= max(0.05, 1 + p["calibration_beta"] * r_spy + drift
                          + idio / math.sqrt(p["exit_session"] - 1) * t_noise(rng, p["calibration_tail_df"]))
            bars.append(dict(d=d, o=o, h=max(o, px) * 1.01, l=min(o, px) * 0.99, c=px, v=1000 + k))
        ev = dict(e, first_trade_date=first, mega=False, offer_price="20")
        trades.append(C.trade(ev, bars, spy, days, p))
    return [t for t in trades if t["status"] == "traded"]


def main():
    p = C.load_config()
    sel = F.paths()["selected"]
    if os.path.exists(sel):
        events, ciks = [], set()
        for e in C.parse_events(open(sel, "rb").read()):
            if e["group"] == "judged" and not e.get("status") and e["cik"] not in ciks:   # count once by CIK
                events.append(e); ciks.add(e["cik"])
        source = "events_selected.csv pricing dates (judged group, no selection status, one per CIK)"
    else:
        events = [dict(accession=f"x{i}", group="judged", pricing_date=f"{2017 + i % 10}-06-1{i % 9}") for i in range(150)]
        source = "invented dates"
    out = {"events": len(events), "dates_from": source, "seeds": p["calibration_seeds"], "edges_pct": {}}
    for edge in p["calibration_edges_pct"]:
        passed, marks = 0, {}
        for s in range(p["calibration_seeds"]):
            j = C.judge(world(events, p, p["calibration_seed"] + 1000 * s + int(edge * 10), edge / 100), p)
            passed += j["passed"]
            for k, v in j["marks"].items():
                marks[k] = marks.get(k, 0) + bool(v)
        out["edges_pct"][str(edge)] = dict(all_eight=passed, each=marks)
        print(f"edge {edge}% a trade: all eight in {passed} of {p['calibration_seeds']}; each:", marks, flush=True)
    with open(os.path.join(F.RUN, "calibration_23.json"), "w") as fh:          # off repo
        json.dump(out, fh, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
