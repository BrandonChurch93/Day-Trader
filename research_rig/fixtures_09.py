"""Hand-worked fills and timing cases for Replay 09; reads no vendor prices."""
import numpy as np
import pandas as pd

import run_09 as r


def close(x, y):
    assert np.isclose(x, y, atol=1e-12, rtol=1e-12), (x, y)


def test_fills():
    d = pd.date_range("2024-01-01", periods=48, freq="h")
    frame = pd.DataFrame(dict(o=100.0, c=100.0, v=1.0), index=d)
    frame.loc[d[1], "v"] = 0
    frame.loc[d[5], "o"] = 120
    frame.loc[d[-1], "c"] = 110
    frame = frame.drop(d[[4, -2]])
    market = r.Market({r.BTC: frame}, "2024-01-01", "2024-01-02")
    assert market.fill(r.BTC, 1, 1, 4) is None  # quote-only entry
    assert market.fill(r.BTC, 1, 4, 5) is None  # absent entry
    first = market.fill(r.BTC, 0.5, 2, 4)
    assert (first.start, first.end, first.buy, first.sell) == (2, 5, 100, 120)
    # Spend half the cash; fee in credited coin on purchase, in dollars on sale.
    expected = 0.5 + (0.5 / 100.1 * 0.9975) * (120 * 0.999) * 0.9975
    close(r.terminal([first], r.COST), expected)
    close(r.equity([first], market, r.COST)[-1], expected)
    last = market.fill(r.BTC, 1.0, 45, 48)
    assert last.end is None
    close(r.equity([last], market, r.COST)[-1], 110 / 100.1 * 0.9975)
    close(market.marks[r.BTC][46], 100)


def test_calendar():
    d = pd.date_range("2024-01-03", periods=24 * 6, freq="h")
    w = r.cycles("WKND", d)
    assert list(d[list(w[0].entries)]) == list(pd.to_datetime(["2024-01-03 01:00", "2024-01-06 01:00"]))
    assert d[w[0].actual + w[0].duration] == pd.Timestamp("2024-01-08")
    assert d[r.cycles("MOM", d)[-1].actual] == pd.Timestamp("2024-01-08 01:00")
    a = r.cycles("ASIA", d)[0]
    assert a.entries == (1, 9, 17) and a.bound == 25


def signal_fixture():
    d = pd.date_range("2023-11-01", "2024-01-08", freq="D")
    h = pd.date_range("2024-01-07", "2024-01-08 23:00", freq="h")
    daily = {s: pd.DataFrame(dict(c=100.0, v=200.0), index=d) for s in r.SYMBOLS}
    hourly = {s: pd.DataFrame(dict(o=100.0, c=100.0, v=1.0), index=h) for s in r.SYMBOLS}
    btc = daily[r.BTC]
    btc.loc["2024-01-07"] = [90, 500]
    daily["ALT/USD"] = btc.copy()  # not in the frozen candidate list
    daily["SOL/USD"].loc["2024-01-07", "c"] = 110
    daily["ETH/USD"].loc["2024-01-07", "c"] = 90
    daily["AVAX/USD"].loc["2024-01-07", "c"] = 120
    daily["AVAX/USD"]["v"] = 1  # highest return but ineligible
    hourly[r.BTC].loc["2024-01-08 02:00", "c"] = 102
    hourly["ETH/USD"].loc["2024-01-08 02:00", "c"] = 99
    hourly["SOL/USD"].loc["2024-01-08 02:00", "c"] = 98
    hourly["SOL/USD"].loc["2024-01-08 02:00", "v"] = 0
    return dict(zip(("1Day", "1Hour"), (daily, hourly)))


def test_signals():
    bars = signal_fixture()
    t = pd.Timestamp("2024-01-08 01:00")
    sig = r.signals(bars, "2024-01-08")
    assert r.decision("MOM", t, sig) == ("SOL/USD", 1)
    assert r.decision("REV", t, sig) == (r.BTC, 1)
    assert r.decision("CAP", t, sig) == (r.BTC, 1)
    assert r.decision("LEAD", pd.Timestamp("2024-01-08 04:00"), sig) == ("ETH/USD", 1)
    assert r.decision("LEAD", pd.Timestamp("2024-01-08 00:00"), sig) is None
    assert r.decision("VOL", t, sig) == (r.BTC, 1)
    # Changing all not-yet-closed daily candles cannot affect any daily decision.
    for frame in bars["1Day"].values():
        frame.loc["2024-01-08"] = [1e6, 1e6]
    other = r.signals(bars, "2024-01-08")
    for name in ("MOM", "REV", "CAP", "VOL"):
        assert r.decision(name, t, other) == r.decision(name, t, sig)
    bars["1Day"]["SOL/USD"] = bars["1Day"]["SOL/USD"].drop(pd.Timestamp("2024-01-04"))
    assert r.decision("MOM", t, r.signals(bars, "2024-01-08")) != ("SOL/USD", 1)


def test_random():
    d = pd.date_range("2024-01-01", periods=24 * 2, freq="h")
    frame = pd.DataFrame(dict(o=100.0, c=100.0, v=1.0), index=d)
    market = r.Market({r.BTC: frame}, "2024-01-01", "2024-01-02")
    fills, cycles, counts = r.fit_fills("ASIA", market, {})
    assert len(fills) == counts["signal_count"] == 2
    assert [(x.start, x.end) for x in fills] == [(1, 9), (25, 33)]
    ratios = r.shuffled(fills, market, cycles, np.random.default_rng(10))
    assert len(ratios) == r.STATS["draws"] and np.allclose(ratios, r.terminal(fills, r.COST))
    assert r.shuffled([market.fill(r.BTC, 1, 1, 48)], market, cycles, np.random.default_rng(10)) is None


if __name__ == "__main__":
    for test in (test_fills, test_calendar, test_signals, test_random):
        test()
        print("PASS", test.__name__)
