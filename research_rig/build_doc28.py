"""Write the Replay 09 report from stored results. Reads no prices and runs no rule."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs/research/28_replay_09_crypto_methods.md"


def pct(x):
    return "UNKNOWN" if x is None else f"{x:+.2%}"


def val(x):
    return "UNKNOWN" if x is None else f"{x:.3f}"


def bps(x):
    return "UNKNOWN" if x is None else f"{x:.2f}"


def coverage(j):
    t = ["| Symbol | Hourly query | First hourly bar UTC | Last hourly bar UTC | Hourly bars | Hours missing inside range | Longest gap, hours | Zero-volume hours | First daily bar UTC | Daily bars | Days missing inside range | Zero-volume days | Recent liquidity screen |",
         "|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|"]
    for sym, frames in j["coverage"].items():
        hour, day = frames["1Hour"], frames["1Day"]
        ok = day.get("recent_daily_liquidity_screen")
        def fmt(frame, k):
            return str(frame.get(k, "n/a"))
        row = [sym, fmt(hour, "status"), *(fmt(hour, k) for k in ("first", "last", "rows", "internal_missing", "longest_internal_gap", "zero_volume")),
               *(fmt(day, k) for k in ("first", "rows", "internal_missing", "zero_volume")),
               "yes" if ok is True else ("no" if ok is False else "UNKNOWN")]
        t += ["| " + " | ".join(row) + " |"]
    return t


def report(j, deeper=None):
    r = j["rules"]
    h = j["hold"]["held"]
    held, dev = j["dates"]["held"], j["dates"]["dev"]
    winners = [n for n, x in r.items() if x["marks"]["passed"]]
    losers = [n for n, x in r.items() if not x["marks"]["passed"]]
    growth = max(r, key=lambda n: r[n]["held"]["total"])
    positive = sum(x["held"]["total"] > 0 for x in r.values())
    ahead = sum(x["held"]["total"] > h["total"] for x in r.values())
    closed = r[growth]["held"]["closed"]
    fee = j["fee"]
    t = [
        "# Replay 09: new crypto methods on Alpaca", "",
        f"MEASURED. {len(winners)} of {len(r)} rules passed all marks. Pass: {', '.join(winners) or 'none'}. "
        f"Fail: {', '.join(losers) or 'none'}. In the held-back slice, {positive} {'rule' if positive == 1 else 'rules'} made money and "
        f"{ahead} beat holding bitcoin. The best net growth was {pct(r[growth]['held']['total'])} "
        f"({growth}), versus {pct(h['total'])} for bitcoin. That rule closed {closed} {'trade' if closed == 1 else 'trades'}. "
        "These are replay figures, not returns from a real account.", "",
        "## What ran", "",
        f"- STATED. The [frozen plan](../../{j['provenance'].get('plan_path', 'research_rig/PREREG_09_crypto_methods.md')}) "
        f"was pushed in commit `{j['provenance']['prereg_commit'][:7]}`. Development ran {dev[0]} through "
        f"{dev[1]}. Held back ran {held[0]} through {held[1]} (`replay_09_dates`, inclusive UTC days). "
        "Each slice restarted with cash. Prior market episodes were already visible in earlier research; the replay "
        "was held back for these rule versions, not a blind forward test.",
        f"- STATED. The modeled cost was {fee['practice_crypto_fee_bps_added']} bps [Alpaca entry-tier taker fee](https://docs.alpaca.markets/us/docs/crypto-fees) "
        f"(`practice_crypto_fee_bps_added`) plus {fee['tm_crypto_half_spread_bps']} bps assumed adverse fill "
        f"(`tm_crypto_half_spread_bps`) per side, {fee['total_bps']} bps nominal on each buy or sell. "
        "The fee is taken from the received asset. Bitcoin buy-and-hold paid to buy and was marked without a closing sale. "
        "There were no maker, price impact, minimum-order, queue, partial-fill or tax assumptions.",
        f"- MEASURED. Rules used hourly and daily bars from the [Alpaca US market data API]({j['source']}). "
        f"The fixed candidate set was {', '.join(s.replace('/USD', '') for s in j['symbols'])} "
        "(`replay_09_basket`). The test did not include other pairs, dead coins, or more venues.",
        "", "## Held-back results at modeled Alpaca cost", "",
        "Net growth is for the slice, not annualized. Largest drop and Sharpe use daily closing equity, not intraday lows. "
        "The random twin uses the same symbols, weights, durations and number of filled sides, with the timing moved. "
        "UNKNOWN means the exact match could not be constructed.", "",
        "| Rule | Net growth | Largest drop | Sharpe | Filled sides | Missed entries | Delayed sales | Still open | Random twin net growth |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| HOLD BTC | {pct(h['total'])} | {pct(h['maxdd'])} | {val(h['sharpe'])} | {h['sides']} | n/a | n/a | {h['open']} | n/a |",
    ]
    for n, x in r.items():
        m = x["held"]
        twin = x["twin"].get("held", {}).get("total")
        t.append(f"| {n} | {pct(m['total'])} | {pct(m['maxdd'])} | {val(m['sharpe'])} | {m['sides']} | "
                 f"{m['entry_missed']} | {m['delayed_exit']} | {m['open']} | {pct(twin)} |")
    t += ["", "## Pass marks", "",
          f"MEASURED. Mark 3 counted {j['stats']['trial_count']} ledger rule trials "
          "(`replay_09_statistics.trial_count`). Mark 4 used the worst overfitting estimate across the frozen "
          "starts (`replay_09_dates.pbo_starts`): " + ", ".join(f"{k}: {val(v['pbo'])}" for k, v in j["pbo"].items())
          + f". The cap is {val(j['thresholds']['backtest_max_pbo'])} (`backtest_max_pbo`). "
          "Mark 2 is against holding bitcoin; zero denotes never ahead at zero friction. A whole-sample shuffle is "
          "UNKNOWN if either slice cannot be matched exactly; the held-only twin can still be reported. "
          "See the plan for the five keys, the daily-return spread proxy and exact rule definitions.", "",
          "| Rule | Mark 1 held | Mark 2 cost | Mark 3 deflated Sharpe | Mark 4 overfit | Mark 5 shuffle | Result | Break-even bps | Deflated Sharpe | Matched draws beaten |",
          "|---|---|---|---|---|---|---|---:|---:|---:|"]
    for n, x in r.items():
        yesno = ["pass" if x["marks"][f"m{i}"] else "fail" for i in range(1, 6)]
        share = x["shuffle_percentile"]
        t.append("| " + " | ".join([n, *yesno, "pass" if x["marks"]["passed"] else "fail",
                                       bps(x["break_even"]["bps"]), val(x["dsr"]),
                                       "UNKNOWN" if share is None else f"{share:.2%}"]) + " |")
    t += ["", "## Data coverage", "",
          f"MEASURED. The coverage check lists every USD pair named on [Alpaca's published pair list]({j['inventory']}), "
          f"{len(j['coverage'])} pairs in total. Internal gaps exclude time outside each file's first and last timestamps. "
          "The [historical bars API](https://docs.alpaca.markets/us/reference/cryptobars-1) can paginate before the requested row limit. Where the full hourly pull was not ready, the table "
          "shows replay-window coverage or marks the download as not yet available. Neither means prices did not exist. "
          f"A recent pass means that each of the last {j['liquidity']['days']} days was present and median daily dollar volume "
          f"was at least {j['liquidity']['min_median_usd']:,} USD (`replay_09_liquidity`). It does not prove the market was liquid "
          "enough to fill any order. No other venue's feed was added. These are the public API's bars, not a complete "
          "historical catalog of every pair ever listed.", "",
          *coverage(j), "",
          "MEASURED. The recorded tape was checked separately and not used for fills. Missing counts below are inside "
          "each recorded minute span, so they do not count time outside its endpoints.", "",
          "| Symbol | First minute UTC | Last minute UTC | Recorded minutes | Internal missing minutes | Zero-volume minutes |",
          "|---|---|---|---:|---:|---:|"]
    for x in j["tape"]:
        if x["frame"] == "1Min":
            t.append("| " + " | ".join(str(x[k]) for k in ("symbol", "first", "last", "rows", "internal_missing", "zero_volume")) + " |")
    if deeper:
        t += [
            "", "## Deeper hourly coverage, checked after the run", "",
            f"MEASURED. The full hourly query completed for all {len(deeper['coverage'])} USD pairs that passed the "
            "recent liquidity screen. This later audit ran no rule. The replay used the original inputs and was not rerun.", "",
            "| USD pair | First UTC hour | Last UTC hour | Hourly bars | Internal missing hours | Longest gap, hours | Zero-volume hours | Replay/long pull mismatches in shared window |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
        for sym, row in deeper["coverage"].items():
            diff = (row["only_in_replay"] + row["only_in_deeper_pull"] + row["changed_shared_bars"]
                    if "changed_shared_bars" in row else "n/a")
            fields = [row[k] for k in ("first", "last", "rows", "internal_missing", "longest_internal_gap", "zero_volume")]
            t.append("| " + " | ".join(str(item) for item in (sym, *fields, diff)) + " |")
    t += [
        "", "## What is still unknown", "",
        "- UNKNOWN. Live fills, actual spreads, depth, latency, adverse selection and venue size limits. A zero-volume bar "
        "may show quote marks ([Alpaca crypto bar notes](https://docs.alpaca.markets/us/docs/real-time-crypto-pricing-data)) "
        "but cannot fill an order here. Even on a bar with volume, the opening mark is only a proxy "
        "for a contemporaneous executable quote.",
        "- UNKNOWN. Whether any calendar effect or ranking signal persists in a truly unseen market. The pair shortlist is "
        "based on markets known now, and the held-back span is short. A smaller loss than BTC is not positive net growth.",
        "- Next test: preregister one resting-limit rule, using timestamped Alpaca trades and quotes rather than highs and lows. "
        "Require an actual trade beyond the resting limit, then compare it with small paper orders for a fill-rate check.",
        "",
        "Built by `research_rig/build_doc28.py` from `research_rig/results_09.json`. The result stores the command, "
        "code fingerprints and fingerprints of each input bar file. Raw prices stay off the repo.", "",
    ]
    return "\n".join(t)


if __name__ == "__main__":
    replay = (HERE / "results_09.json").read_bytes()
    deep = HERE / "alpaca_coverage_09.json"
    extra = json.loads(deep.read_text()) if deep.exists() else None
    if extra:
        import hashlib
        if hashlib.sha256(replay).hexdigest() != extra["replay_sha256"]:
            raise ValueError("deeper coverage was checked against a different replay output")
    OUT.write_text(report(json.loads(replay), extra))
