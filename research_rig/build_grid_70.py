"""Write deterministic rule-grid JSON to stdout. No data inputs."""
import itertools
import json

SOURCES = {
    "clock_after_move": (
        "https://academic.oup.com/jfec/article-abstract/22/1/224/6759403",
        "Liquidity changes by session and weekday; a patient counterparty may be paid to absorb recent urgent flow.",
        "At the fixed UTC entry hour and day type, fade a signed lag-hour log close move of at least threshold."),
    "hourly_shock": (
        "https://arxiv.org/html/2102.04591v1",
        "Liquidated traders cannot choose when to trade; a patient buyer or seller may earn a concession after the burst.",
        "Fade a signed one-hour log close move at least threshold, with last bar volume at least ratio times preceding volume_lookback mean; proxy, not verified liquidation."),
    "london_brr_fade": (
        "https://www.cmegroup.com/trading/files/bitcoin-reference-rate-methodology.pdf",
        "Settlement-linked desks have a reason to concentrate turnover during the fixed London benchmark window; the pressure may dissipate when the clock expires.",
        "BTC only; at 16:00 Europe/London, fade the last completed bar's signed open-to-close log return if at least threshold; apply daylight saving."),
    "midnight_stop_run": (
        "https://ar5iv.labs.arxiv.org/html/2306.17095",
        "Trading activity clusters at round clocks. A liquidity taker crossing a visible daily boundary may pay a waiting counterparty after a stop sweep.",
        "At 00:00 UTC, fade a signed one-hour log close move at least threshold, with preceding bar volume at least ratio times the prior volume_lookback mean and a break of the prior lag_range-hour extreme."),
    "btc_overextension_fade": (
        "https://arxiv.org/abs/2109.12142",
        "The documented common BTC and ETH price activity motivates a test that impatient orders in an alt overshoot during a common large move.",
        "Fade the alt excess over multiple times BTC's same-direction lag-hour log close move, requiring BTC's move in that direction to meet threshold."),
    "bitcoin_lead": (
        "https://ar5iv.labs.arxiv.org/html/2108.09750",
        "Fragmented traders face costs moving information across books and can reprice slower books after a leading move.",
        "Follow the signed BTC log close move if at least threshold and the same signed alt move is at most fraction times BTC's signed move."),
    "volume_shock": (
        "https://ar5iv.labs.arxiv.org/html/2108.09750",
        "A large trader demanding immediate execution can pay to move through thin depth; wait for the burst to finish.",
        "Fade last hour's signed log close move at least threshold if its base volume divided by the previous 24-hour mean is at least ratio."),
    "hedged_relative": (
        "https://www.nber.org/papers/w24877",
        "Gradual rebalancing may leave the strongest relative performer still being bought, or the weakest still being sold; hedge the common BTC move.",
        "Among altcoins, choose the greatest signed lag-hour log close move less BTC's same-clock move, requiring threshold; take opposite BTC at equal dollars."),
    "round_rejection": (
        "https://pubsonline.informs.org/servlet/linkout?suffix=B76&dbid=16&doi=10.1287/mnsc.2023.4790&key=10.1016/j.econlet.2017.07.035",
        "Orders bunch at conspicuous prices; an impatient sweep into a queue can pay the counterparty waiting for a rejection.",
        "Anchor on nearest round multiple to the preceding close, with step multiple times 10**floor(log10(previous close)); last bar pierces it and closes back across by threshold log distance."),
    "range_rejection": (
        "https://www.newyorkfed.org/research/staff_reports/sr150.html",
        "Stop and take-profit orders can cluster at visible levels; wait for a failed sweep instead of buying a breakout.",
        "Compare last hourly bar with the prior lag-hour high/low, excluding the last bar; require a pierce and close back inside by threshold log distance."),
}


def grid():
    out = []

    def add(family, side, hold, params):
        url, reason, trigger = SOURCES[family]
        row = {"id": f"70-{len(out) + 1:03}", "family": family, "mechanism": reason,
                    "source": url, "signal": trigger, "parameters": params, "side": side,
                    "universe": "btc_only" if family == "london_brr_fade" else
                    "alts_only" if family in ("btc_overextension_fade", "bitcoin_lead", "hedged_relative") else "all",
                    "entry": "first subsequent hourly spot open, no signal data from entry bar",
                    "exit": "spot open exactly hold_hours after entry, no stop or target",
                    "hold_hours": hold, "btc_hedge": family == "hedged_relative"}
        if family in ("bitcoin_lead", "volume_shock", "hedged_relative"):
            row["prior_replay_note"] = "related to Replay 09 at a different horizon"
        out.append(row)

    for h, day, lag, side, hold in itertools.product((2, 9, 14, 18), ("weekday", "weekend"), (2, 4), (1, -1), (1, 2)):
        add("clock_after_move", side, hold, {"entry_hour": h, "day_type": day, "lag": lag,
                                           "threshold": {2: .004, 4: .006}[lag]})
    for threshold, side, hold in itertools.product((.015, .025, .040), (1, -1), (1, 2)):
        add("hourly_shock", side, hold, {"lag": 1, "threshold": threshold, "volume_lookback": 24, "ratio": 3.})
    for threshold, side, hold in itertools.product((.0075, .0125, .020), (1, -1), (1, 2)):
        add("london_brr_fade", side, hold, {"threshold": threshold})
    for threshold, side, hold in itertools.product((.010, .015, .025), (1, -1), (1, 2)):
        add("midnight_stop_run", side, hold,
            {"lag": 1, "threshold": threshold, "volume_lookback": 24, "ratio": 1.5, "lag_range": 24})
    for threshold, multiple, side, hold in itertools.product((.015, .025), (2., 2.5), (1, -1), (1, 2)):
        add("btc_overextension_fade", side, hold, {"lag": 2, "threshold": threshold, "multiple": multiple})
    for multiple, threshold, side in itertools.product((.1, .2), (.0005, .001), (1, -1)):
        add("round_rejection", side, 1, {"multiple": multiple, "threshold": threshold})
    for lag, threshold, side, hold in itertools.product((8, 36), (.001, .0025), (1, -1), (1, 2)):
        add("range_rejection", side, hold, {"lag": lag, "threshold": threshold})
    for lag, threshold, fraction, side in itertools.product((1, 3), (.0075, .0125), (.25, .50), (1, -1)):
        add("bitcoin_lead", side, 1, {"lag": lag, "threshold": threshold, "fraction": fraction})
    for ratio, threshold, side, hold in itertools.product((2., 3.), (.005, .01), (1, -1), (1, 2)):
        add("volume_shock", side, hold, {"lag": 1, "volume_lookback": 24, "threshold": threshold, "ratio": ratio})
    for lag, threshold, side, hold in itertools.product((2, 4), (.004, .008), (1, -1), (1, 2)):
        add("hedged_relative", side, hold, {"lag": lag, "threshold": threshold})
    return out


if __name__ == "__main__":
    print(json.dumps(grid(), indent=2) + "")
