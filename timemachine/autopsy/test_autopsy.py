"""Offline tests for the decision autopsy (timemachine/autopsy/), on made-up records only. No run folder, tape or news is read.

Covers: round trips built from the desk's closed list with partial sells, stop / target / time exit attribution from
the desk's sell text, the cost sum (fee plus half-spread of every fill), the 24 h and 120 h price windows using only
minutes at or before each time, the under-30 rule, and the report of a label id that is not in the run folders.

Run: python3 timemachine/autopsy/test_autopsy.py
"""
import os
import sys
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core
import prices as P
from classify import classify_sell

PASS = FAIL = 0


def ok(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {msg}")


def close(a, b, tol=1e-9):
    return a is not None and b is not None and abs(a - b) < tol


T0 = 1_780_000_020  # a made-up epoch second, not on a minute boundary on purpose
H = 3600


# ---------------------------------------------------------------- exit attribution from the desk's sell text
ok(classify_sell("Exit set in pick 20260715T1200Z: the stop price was reached.") == ("S_STOP", "rule"), "stop text -> S_STOP")
ok(classify_sell("Exit set in pick 20260715T1200Z: the target price was reached.") == ("S_TARGET", "rule"), "target text -> S_TARGET")
ok(classify_sell("Exit set in pick 20260715T1200Z: the exit time was reached.") == ("S_TIME", "rule"), "time text -> S_TIME")
ok(classify_sell("Exit set in pick 20260715T1200Z: something new")[0] != "S_STOP", "an unknown desk text is not called a stop")

# ---------------------------------------------------------------- cost per fill
ok(close(core.fill_spread("buy", 1.0, 101.0, 0.01), 1.0), "buy at 101 with 1% half-spread paid 1.00 of spread")
ok(close(core.fill_spread("sell", 1.0, 99.0, 0.01), 1.0), "sell at 99 with 1% half-spread paid 1.00 of spread")
ok(close(core.fill_spread("buy", 2.0, 50.5, 0.01), 1.0), "spread scales with quantity")

# ---------------------------------------------------------------- round trips with partial sells
buys = [dict(sym="SOL/USD", t=T0, fee=0.25, spread=0.10, cat="B_BREAKOUT", pick_id="P1", fill=100.0, exits=[dict(stop=95.0)]),
        dict(sym="SOL/USD", t=T0 + 2 * H, fee=0.25, spread=0.10, cat="B_OTHER", pick_id="P2", fill=101.0),   # top-up inside the trip
        dict(sym="SOL/USD", t=T0 + 30 * H, fee=0.25, spread=0.10, cat="B_SUPPORT", pick_id="P3", fill=90.0),  # next trip
        dict(sym="ETH/USD", t=T0 + 1 * H, fee=0.30, spread=0.20, cat="B_REVERSAL", pick_id="P1", fill=2000.0)]
sells = [dict(sym="SOL/USD", t=T0 + 5 * H, fee=0.20, spread=0.05, cat="S_TARGET", exit_pick="P1", written=False),   # partial
         dict(sym="SOL/USD", t=T0 + 10 * H, fee=0.15, spread=0.05, cat="S_STOP", exit_pick="P2", written=False),    # rest
         dict(sym="SOL/USD", t=T0 + 40 * H, fee=0.20, spread=0.05, cat="S_TIME", exit_pick="P3", written=False),
         dict(sym="ETH/USD", t=T0 + 3 * H, fee=0.30, spread=0.20, cat="S_VIEW_PRICE", exit_pick=None, written=True)]
closed = [dict(symbol="SOL/USD", opened_ts=T0, closed_ts=T0 + 10 * H, gain_usd=-3.0, gain_pct=-0.03),
          dict(symbol="SOL/USD", opened_ts=T0 + 30 * H, closed_ts=T0 + 40 * H, gain_usd=2.0, gain_pct=0.02),
          dict(symbol="ETH/USD", opened_ts=T0 + 1 * H, closed_ts=T0 + 3 * H, gain_usd=-1.0, gain_pct=-0.01)]
trips = core.round_trips(closed, buys, sells)
ok(len(trips) == 3, "one round trip per closed row")
a, b, c = trips
ok(a["n_buys"] == 2 and a["n_sells"] == 2, "first SOL trip holds both buys and both partial sells")
ok(a["entry_cat"] == "B_BREAKOUT" and a["entry_pick"] == "P1", "entry reason is the first buy's")
ok(a["exit_cat"] == "S_STOP" and a["exit_pick"] == "P2", "exit reason is the last sell's (the stop), not the partial target sell")
ok(close(a["costs"], 0.35 + 0.35 + 0.25 + 0.20), "costs are fee plus spread of all four fills of the trip")
ok(close(a["hold_h"], 10.0), "hold time from opening to closing")
ok(b["n_buys"] == 1 and b["n_sells"] == 1 and b["exit_cat"] == "S_TIME", "second SOL trip takes only its own fills")
ok(c["exit_cat"] == "S_VIEW_PRICE" and c["exit_written"] is True, "a written sell is kept as written")
ok(sells[0]["trip_gain"] == -3.0 and sells[1]["trip_gain"] == -3.0, "every sell of a trip carries the trip's gain")
ok(close(sum(t["costs"] for t in trips), sum(x["fee"] + x["spread"] for x in buys + sells)), "cost sum over trips equals the sum over all fills")
tt = core.trip_table(trips)
ok(tt["wins"] == 1 and close(tt["net_usd"], -2.0) and close(tt["gross_before_costs_usd"], -2.0 + tt["costs_usd"]), "trip table net, wins and gross")
ok(close(tt["costs_share_of_net_loss"], tt["costs_usd"] / 2.0), "costs as share of the net loss")
trips_none = core.round_trips([dict(symbol="XRP/USD", opened_ts=T0, closed_ts=T0 + H, gain_usd=1.0, gain_pct=0.01)], buys, sells)
ok(trips_none[0]["entry_cat"] == "UNCLEAR" and trips_none[0]["exit_cat"] == "UNCLEAR", "a closed row with no matching fills is UNCLEAR, not guessed")

# ---------------------------------------------------------------- price windows: only minutes at or before the time
m0 = (T0 // 60) * 60
times = [m0 + 60 * i for i in range(0, 6 * 24 * 60 + 1)]                     # six days of minutes
closes = [100.0 + i * 0.001 for i in range(len(times))]
P._cache["TEST/USD"] = (array("q", times), array("d", closes), array("d", closes), array("d", closes))
t = m0 + 30                                                                  # 30 s after a minute closes
ok(P.px("TEST/USD", t) == closes[0], "price at a time is the last minute at or before it, not the next one")
ok(P.px("TEST/USD", m0 + 60) == closes[1], "a minute stamped exactly at the time is used")
r24 = P.ret("TEST/USD", t, t + core.H24)
ok(close(r24, closes[24 * 60] / closes[0] - 1), "24 h change uses the minute at or before t+24h")
r120 = P.ret("TEST/USD", t, t + core.H120)
ok(close(r120, closes[120 * 60] / closes[0] - 1), "120 h change uses the minute at or before t+120h")
ok(P.ret("TEST/USD", t, times[-1] + 60) is None, "a window ending after the last recorded minute gives None, not a later price")
P._cache["GAP/USD"] = (array("q", [m0, m0 + 10 * H]), array("d", [1.0, 2.0]), array("d", [1.0, 2.0]), array("d", [1.0, 2.0]))
ok(P.px("GAP/USD", m0 + 7 * H) is None, "no minute in the 6 hours before: no price")
ok(P.px("GAP/USD", m0 + 10 * H - 1) is None and P.px("GAP/USD", m0 + 10 * H) == 2.0, "a minute after the time is never used")

# ---------------------------------------------------------------- the under-30 rule
ok(core.cell([0.01] * 29)["small"] is True, "29 items: small")
ok(core.cell([0.01] * 30)["small"] is False, "30 items: not small")
ok(core.cell([0.01] * 29 + [None] * 5)["small"] is True and core.cell([0.01] * 29 + [None] * 5)["n"] == 29, "missing values do not count toward 30")
ok(core.trip_table(trips)["small"] is True, "a trip table of 3 is small")
c4 = core.cell([0.02, -0.01, 0.0, 0.03])
ok(c4["n"] == 4 and close(c4["share_pos"], 0.5) and close(c4["share_neg"], 0.25), "share above and below zero")

# ---------------------------------------------------------------- label ids must exist in the run folders
labels = [dict(id="TM01-B01-OPUS-2026-08|20260801T0000Z|0", kind="buy", label="B_BREAKOUT", who="analyst", time="2026-11-25T21:31Z"),
          dict(id="TM01-B01-OPUS-2026-08|20260801T0000Z|9", kind="buy", label="B_SUPPORT", who="analyst", time="2026-11-25T21:31Z")]
known = ["TM01-B01-OPUS-2026-08|20260801T0000Z|0", "TM01-B01-OPUS-2026-08|20260801T0000Z|1"]
ok(core.check_label_ids(labels, known) == ["TM01-B01-OPUS-2026-08|20260801T0000Z|9"], "a label whose id is not in the run folders is reported")
ok(core.check_label_ids(labels[:1], known) == [], "no report when every id is found")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "autopsy.py")).read()
ok("check_label_ids(labels, known_ids)" in src and "label id not found in the run folders" in src, "autopsy.py runs the id check and prints what it finds")

# ---------------------------------------------------------------- news text check for quotes
ok(core.shared_runs("Bitcoin fell after the big bank said rates stay high", ["Big bank said rates stay high for longer"]) != [], "a five-word run shared with a headline is found")
ok(core.shared_runs("Range breakout above 67k that held for eight hours.", ["Bitcoin ETF inflows hit a record"]) == [], "no shared run, nothing reported")

print(f"{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
