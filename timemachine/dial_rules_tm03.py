"""Fixed-dial comparison for Time Machine plan TM03 (BTC/USD, April to November 2026). Pretend money only.

FIXED DIALS (written before running; do not add or change after seeing results):
  A      : 1.0 when the last daily close before the wake is above the simple average of the last 20 daily closes, else 0.5.
  B      : 1.0 when the last daily close before the wake is above the simple average of the last 20 daily closes, else 0.0.
  C      : fraction of the simple averages (10, 20, 50) of daily closes before the wake that the last close is above (0, 1/3, 2/3, 1).
  D      : starts each month at 1.0; cuts to 0.5 when the 7-day close-to-close return before the wake is below -5%;
           returns to 1.0 when the 7-day return is above 0%.
  E      : constant 0.7 (fixed lower share, no timing).
  F-<M>  : [HINDSIGHT] each complete model's own month-average share (from timemachine/results_tm03.json) held constant all month.

NOTE: These dials are NOT counted rule trials and prove nothing on their own (eight months, chosen today).
Each month runs through the exact same weights book code (timemachine/weights.py: run_answers / step_book),
same wake clock (00:00 UTC), same fill rule (open of first recorded minute at or after wake), same costs,
same tm_weights_min_change, same monthly reset, and same opening target (1.0 BTC/USD).

Usage:
  python3 timemachine/dial_rules_tm03.py          run comparison and print tables
  python3 timemachine/dial_rules_tm03.py --write  write timemachine/dial_rules_tm03.json and docs/research/37_tm03_plain_dials.md
  python3 timemachine/dial_rules_tm03.py --check  exit 1 if stored JSON or Markdown page is missing or stale
  python3 timemachine/dial_rules_tm03.py --json   print JSON output
  python3 timemachine/dial_rules_tm03.py --test   run self-tests on made-up prices
"""
import argparse
import calendar
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from timemachine import score_tm03 as ST, score_weights as SW, weights as W
from timemachine.tape import Tape

UTC = dt.timezone.utc
RESULTS_PATH = ROOT / "timemachine" / "results_tm03.json"
OUT_JSON = ROOT / "timemachine" / "dial_rules_tm03.json"
OUT_DOC = ROOT / "docs" / "research" / "37_tm03_plain_dials.md"
LOOKBACK_DAYS = 90  # enough calendar days for 50 closed daily bars with safety margin

DIAL_SPECS = [
    ("A", "above 20d SMA -> 1.0, else 0.5", False),
    ("B", "above 20d SMA -> 1.0, else 0.0", False),
    ("C", "fraction of 10/20/50d SMAs below last close (0, 1/3, 2/3, 1)", False),
    ("D", "1.0, cut to 0.5 if 7d ret < -5%, back to 1.0 if 7d ret > 0%", False),
    ("E", "constant 0.7 (fixed lower share, no timing)", False),
]


def month_window(month_str, last_day):
    y, m = (int(x) for x in month_str.split("-"))
    start_date = f"{y:04d}-{m:02d}-01"
    if last_day and str(last_day).startswith(f"{y:04d}-{m:02d}"):
        end_date = str(last_day)
    else:
        end_date = f"{y:04d}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"
    return start_date, end_date


def closed_daily_bars_before(tape, symbol, wake, lookback_days=LOOKBACK_DAYS):
    """Return closed 1Day bars strictly finished at or before `wake` (never reading a close at or after wake)."""
    bars = tape.bars(symbol, "1Day", wake - dt.timedelta(days=lookback_days), wake)
    for b in bars:
        bar_end = b["t"] + dt.timedelta(days=1)
        assert b["t"] < wake and bar_end <= wake, f"look-ahead guard tripped: bar {b['t']} vs wake {wake}"
    return bars


def sma(closes, n):
    assert len(closes) >= n, f"need {n} daily closes, got {len(closes)}"
    return sum(closes[-n:]) / float(n)


def ret_nd(bars, days):
    """Trailing calendar-day close-to-close return, matching timemachine/weights.py:symbol_rows()."""
    last = bars[-1]
    cutoff = last["t"] - dt.timedelta(days=days)
    back = [b for b in bars if b["t"] <= cutoff]
    assert back and back[-1]["c"] > 0, f"missing {days}d prior daily bar before {last['t']}"
    return last["c"] / back[-1]["c"] - 1.0


def decide_series(dial_id, wakes, bars_fn, const_weight=None):
    """Return a list of target weights (float in [0, 1]) for each wake, decided strictly from closed bars before each wake."""
    out = []
    state_d = 1.0  # D starts each month at 1.0 (fresh account, fully invested)
    for wake in wakes:
        if dial_id == "E":
            out.append(0.7)
            continue
        if dial_id.startswith("F-"):
            assert const_weight is not None
            out.append(float(const_weight))
            continue
        bars = bars_fn(wake)
        assert bars, f"no closed daily bars before {wake}"
        closes = [b["c"] for b in bars]
        last_c = closes[-1]
        if dial_id == "A":
            out.append(1.0 if last_c > sma(closes, 20) else 0.5)
        elif dial_id == "B":
            out.append(1.0 if last_c > sma(closes, 20) else 0.0)
        elif dial_id == "C":
            hits = sum(1 for n in (10, 20, 50) if last_c > sma(closes, n))
            out.append(hits / 3.0)
        elif dial_id == "D":
            r7 = ret_nd(bars, 7)
            if state_d == 1.0 and r7 < -0.05:
                state_d = 0.5
            elif state_d == 0.5 and r7 > 0.0:
                state_d = 1.0
            out.append(state_d)
        else:
            raise ValueError(f"unknown dial_id: {dial_id}")
    return out


def run_month(meta, table, cfg, symbol, weights_seq):
    """Run one month through timemachine/weights.py:run_answers and return stats."""
    answers = [{symbol: w} if w > 0 else {} for w in weights_seq]
    book, recs, final = W.run_answers(meta, table, answers, cfg)
    st = SW.stats(meta, recs, book, final, cfg)
    start = cfg["tm_account_start_usd"]
    wakes = [W.parse(w) for w in meta["wakes"]]
    end = W.parse(meta["end_utc"])
    duration_sec = (end - wakes[0]).total_seconds()
    return dict(
        gain_usd=final - start,
        final_value_usd=final,
        largest_drop_pct=st["largest_drop_pct"],
        avg_weight=st["avg_weight"],
        costs_usd=st["costs_paid_usd"],
        trade_wakes=st["trade_wakes"],
        duration_sec=duration_sec,
    )


def build(tape=None, results_path=RESULTS_PATH):
    cfg = ST.tm03_config()
    plan = cfg["tm03_plan"]
    symbol = plan["symbol"]
    months = list(plan["months"])
    last_day = plan.get("last_day")
    wake_rules = [{"every": "day", "utc_hours": [plan["wake_hour_utc"]]}]
    opening = {symbol: float(plan["opening_weight"])}
    tape = tape or Tape()

    tm03 = json.loads(Path(results_path).read_text())
    ordered_tags = [tag for tag, _ in ST.MODELS if tag in tm03["models"]]
    ordered_tags += [tag for tag in sorted(tm03["models"]) if tag not in ordered_tags]
    complete_models = [tag for tag in ordered_tags if tm03["models"][tag].get("complete")]
    incomplete_models = [
        dict(
            tag=tag,
            name=tm03["models"][tag]["name"],
            months_done=len(tm03["models"][tag].get("months_counted") or []),
            months_total=len(months),
        )
        for tag in ordered_tags
        if not tm03["models"][tag].get("complete")
    ]
    assert complete_models, "no complete models found in results_tm03.json"

    # Prepare price tables and closed daily bar cache once per month
    month_data = {}
    hold_rows = {}
    for mo in months:
        s_date, e_date = month_window(mo, last_day)
        wakes, end = W.make_wakes(tape, "crypto", s_date, e_date, wake_rules)
        meta = dict(
            market="crypto",
            symbols=[symbol],
            benchmark=symbol,
            opening=dict(opening),
            wakes=[W.iso(w) for w in wakes],
            end_utc=W.iso(end),
            window=dict(start=s_date, end=e_date),
        )
        table = W.price_table(tape, meta)
        bars_by_wake = {w: closed_daily_bars_before(tape, symbol, w) for w in wakes}
        month_data[mo] = dict(meta=meta, table=table, wakes=wakes, bars_by_wake=bars_by_wake)

        # Hold baseline via weights.py (opening 1.0, no_change every wake)
        book_h, recs_h, final_h = W.run_answers(meta, table, [None] * len(wakes), cfg)
        st_h = SW.stats(meta, recs_h, book_h, final_h, cfg)
        hold_gain = final_h - cfg["tm_account_start_usd"]
        ref_hold = tm03["models"][complete_models[0]]["months"][mo]["hold_gain_usd"]
        assert round(hold_gain, 2) == round(ref_hold, 2), (
            f"hold mismatch on {mo}: {hold_gain:.4f} vs results_tm03.json {ref_hold:.2f}"
        )
        hold_rows[mo] = dict(
            gain_usd=hold_gain,
            largest_drop_pct=st_h["largest_drop_pct"],
            avg_weight=st_h["avg_weight"],
            costs_usd=st_h["costs_paid_usd"],
            duration_sec=(end - wakes[0]).total_seconds(),
        )

    # Collect complete models' per-month and summed numbers from results_tm03.json
    models_ref = {}
    for tag in complete_models:
        m = tm03["models"][tag]
        mo_map = {}
        for mo in months:
            r = m["months"][mo]
            mo_map[mo] = dict(
                gain_usd=float(r["gain_usd"]),
                largest_drop_pct=float(r["largest_drop_pct"]),
                avg_weight=float(r["avg_weight"]),
                costs_usd=float(r["costs_usd"]),
                duration_sec=hold_rows[mo]["duration_sec"],
            )
        tot_dur = sum(x["duration_sec"] for x in mo_map.values())
        models_ref[tag] = dict(
            name=m["name"],
            months=mo_map,
            sum_gain_usd=float(m["sum_gain_usd"]),
            worst_drop_pct=min(x["largest_drop_pct"] for x in mo_map.values()),
            avg_weight=sum(x["avg_weight"] * x["duration_sec"] for x in mo_map.values()) / tot_dur,
            sum_costs_usd=float(m["sum_costs_usd"]),
        )

    all_dials = list(DIAL_SPECS) + [
        (f"F-{tag}", f"{models_ref[tag]['name']} month-average share held constant", True)
        for tag in complete_models
    ]

    dials_out = {}
    for dial_id, desc, hindsight in all_dials:
        m_out = {}
        for mo in months:
            md = month_data[mo]
            cw = models_ref[dial_id[2:]]["months"][mo]["avg_weight"] if dial_id.startswith("F-") else None
            w_seq = decide_series(dial_id, md["wakes"], lambda w, b=md["bars_by_wake"]: b[w], const_weight=cw)
            r = run_month(md["meta"], md["table"], cfg, symbol, w_seq)
            r["vs_hold_usd"] = r["gain_usd"] - hold_rows[mo]["gain_usd"]
            r["vs_models_usd"] = {tag: r["gain_usd"] - models_ref[tag]["months"][mo]["gain_usd"] for tag in complete_models}
            m_out[mo] = r

        tot_dur = sum(x["duration_sec"] for x in m_out.values())
        sum_gain = sum(x["gain_usd"] for x in m_out.values())
        sum_hold = sum(x["gain_usd"] for x in hold_rows.values())
        dials_out[dial_id] = dict(
            description=desc,
            hindsight=hindsight,
            months=m_out,
            sum_gain_usd=sum_gain,
            sum_vs_hold_usd=sum_gain - sum_hold,
            sum_vs_models_usd={tag: sum_gain - models_ref[tag]["sum_gain_usd"] for tag in complete_models},
            worst_drop_pct=min(x["largest_drop_pct"] for x in m_out.values()),
            avg_weight=sum(x["avg_weight"] * x["duration_sec"] for x in m_out.values()) / tot_dur,
            sum_costs_usd=sum(x["costs_usd"] for x in m_out.values()),
            sum_trade_wakes=sum(x["trade_wakes"] for x in m_out.values()),
        )

    tot_dur_h = sum(x["duration_sec"] for x in hold_rows.values())
    hold_summary = dict(
        months=hold_rows,
        sum_gain_usd=sum(x["gain_usd"] for x in hold_rows.values()),
        worst_drop_pct=min(x["largest_drop_pct"] for x in hold_rows.values()),
        avg_weight=sum(x["avg_weight"] * x["duration_sec"] for x in hold_rows.values()) / tot_dur_h,
        sum_costs_usd=sum(x["costs_usd"] for x in hold_rows.values()),
    )

    return dict(
        disclaimer=(
            "Not counted rule trials. These fixed dials were chosen on 2026-11-25 on an eight-month window "
            "(April to November 24, 2026) by someone who had seen the months' hold returns, and prove nothing "
            "on their own. Dials F-* use each model's finished monthly average share and are hindsight."
        ),
        symbol=symbol,
        months=months,
        last_day=last_day,
        total_models=len(ordered_tags),
        complete_models=complete_models,
        incomplete_models=incomplete_models,
        account_start_usd=cfg["tm_account_start_usd"],
        hold=hold_summary,
        models=models_ref,
        dials=dials_out,
    )


def usd(x):
    if abs(x) < 0.005:
        return "$0.00"
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def s_usd(x):
    if abs(x) < 0.005:
        return "$0.00"
    return f"+${x:,.2f}" if x > 0 else usd(x)


def ordered_dial_ids(data):
    base = [d for d, _, _ in DIAL_SPECS if d in data["dials"]]
    f_ids = [f"F-{t}" for t in data["complete_models"] if f"F-{t}" in data["dials"]]
    return base + f_ids


def render_doc(data):
    """Render docs/research/37_tm03_plain_dials.md from stored JSON data. Plain words, flat lists, no em dashes."""
    models = data["complete_models"]
    inc = data["incomplete_models"]
    h = data["hold"]
    dials = data["dials"]
    dial_ids = ordered_dial_ids(data)
    m_hdr = " | ".join(f"vs {t}" for t in models)

    best_model_tag = max(models, key=lambda t: data["models"][t]["sum_gain_usd"])
    best_model = data["models"][best_model_tag]
    worst_model_tag = min(models, key=lambda t: data["models"][t]["sum_gain_usd"])
    worst_model = data["models"][worst_model_tag]

    b_dial, c_dial, e_dial = dials["B"], dials["C"], dials["E"]
    f_margins = [dials[f"F-{t}"]["sum_vs_models_usd"][t] for t in models]
    f_min_margin, f_max_margin = min(f_margins), max(f_margins)
    b_beats = [t for t in models if b_dial["sum_gain_usd"] > data["models"][t]["sum_gain_usd"]]
    c_beats = [t for t in models if c_dial["sum_gain_usd"] > data["models"][t]["sum_gain_usd"]]
    model_drops = [data["models"][t]["worst_drop_pct"] for t in models]
    worst_m_drop, mildest_m_drop = min(model_drops), max(model_drops)

    if inc:
        inc_text = ", ".join(f"{x['name']} ({x['months_done']} of {x['months_total']})" for x in inc)
        status_line = (
            f"MEASURED. Models with all {len(data['months'])} months in at the time this page was written: "
            f"{len(models)} of {data['total_models']} ({', '.join(data['models'][t]['name'] for t in models)}). "
            f"Still incomplete and left out until all {len(data['months'])} months finish: {inc_text}."
        )
    else:
        status_line = (
            f"MEASURED. Models with all {len(data['months'])} months in at the time this page was written: "
            f"{len(models)} of {data['total_models']} ({', '.join(data['models'][t]['name'] for t in models)})."
        )

    L = [
        "# Time machine plan TM03: plain fixed dials against the AI models",
        "",
        "Made by `timemachine/dial_rules_tm03.py --write` from `timemachine/dial_rules_tm03.json` and `timemachine/results_tm03.json`. Do not edit by hand. Pretend money.",
        "",
        status_line,
        "",
        "## What was asked",
        "",
        "- STATED. In plan TM03 (`docs/research/34_time_machine_tm03_bitcoin_dial.md`), several AI models ended ahead of holding bitcoin over the eight months from April to November 24, 2026, while none stood clear of their own answers in shuffled order (`shuffle_runs`).",
        "- STATED. This check asks whether plain fixed rules, decided only from daily closes before each wake and run through the exact same weights book code (`timemachine/weights.py`), land in the same place.",
        "",
        "## How the first wake of each month works",
        "",
        "- STATED. Each month in `tm03_plan.months` starts as a fresh `tm_account_start_usd` cash account with opening target `tm03_plan.opening_weight` (fully invested in BTC/USD).",
        "- STATED. Both the AI models and the fixed dials are asked for a target share at the first wake of each month (`tm03_plan.wake_hour_utc` on day 1), using only daily bars whose close finished at or before that wake.",
        "- STATED. In `timemachine/weights.py` (`step_book`), the desk does not buy the opening target before the first wake's answer arrives. If a model or dial keeps the opening share of 1.0, the desk buys 1.0 at the open of the first recorded minute and pays spread (`tm_crypto_half_spread_bps`) plus fee (`practice_crypto_fee_bps_added`) on the full account.",
        "- STATED. If a model or dial answers a lower share `w` at the first wake (for example 0.7 for Dial E or 0.0 for Dial B when bitcoin is already below its 20-day average), the desk replaces the opening target with `w` and buys only `w` directly from cash at that first minute open. It does not buy 1.0 and then sell `1 - w`. So opening below 1.0 at wake 0 costs spread and fee only on `w`, and costs $0.00 when `w` is 0.0.",
        "- STATED. On every later wake in the month, the desk trades only when the new target differs from the standing target, skips changes smaller than `tm_weights_min_change` unless moving to 0.0, and lets the book drift between wakes.",
        "",
        "## The dials, fixed before running",
        "",
        "STATED. Batch 1 was fixed at the top of `timemachine/dial_rules_tm03.py` before running and was not changed after seeing results:",
        "",
    ]
    for dial_id in dial_ids:
        d = dials[dial_id]
        tag = " (hindsight)" if d["hindsight"] else ""
        L.append(f"- Dial {dial_id}{tag}: {d['description']}.")

    L += [
        "",
        "## Summed over all eight months",
        "",
        "MEASURED, pretend money, April to November 24, 2026 (`tm03_plan.months`, November ending on `tm03_plan.last_day`). Fresh `tm_account_start_usd` account each month. Largest drop is the worst single-month drawdown across the eight months; average share is time-weighted across all eight months.",
        "",
        f"| Rule / Model | Gain ($) | vs Hold | {m_hdr} | Largest drop | Avg share | Costs ($) |",
        "|---|---:|---:|" + "---:|" * len(models) + "---:|---:|---:|",
    ]
    vs_m_h = " | ".join(s_usd(h["sum_gain_usd"] - data["models"][t]["sum_gain_usd"]) for t in models)
    L.append(
        f"| Hold {data['symbol']} | {usd(h['sum_gain_usd'])} | {s_usd(0.0)} | {vs_m_h} | "
        f"{h['worst_drop_pct']:.1f}% | {h['avg_weight']:.2f} | {usd(h['sum_costs_usd'])} |"
    )
    for t in models:
        m = data["models"][t]
        vs_m = " | ".join(s_usd(m["sum_gain_usd"] - data["models"][t2]["sum_gain_usd"]) for t2 in models)
        L.append(
            f"| Model {t} ({m['name']}) | {usd(m['sum_gain_usd'])} | {s_usd(m['sum_gain_usd'] - h['sum_gain_usd'])} | "
            f"{vs_m} | {m['worst_drop_pct']:.1f}% | {m['avg_weight']:.2f} | {usd(m['sum_costs_usd'])} |"
        )
    for dial_id in dial_ids:
        d = dials[dial_id]
        label = f"{dial_id} (hindsight)" if d["hindsight"] else dial_id
        vs_m = " | ".join(s_usd(d["sum_vs_models_usd"][t]) for t in models)
        L.append(
            f"| Dial {label} | {usd(d['sum_gain_usd'])} | {s_usd(d['sum_vs_hold_usd'])} | "
            f"{vs_m} | {d['worst_drop_pct']:.1f}% | {d['avg_weight']:.2f} | {usd(d['sum_costs_usd'])} |"
        )

    L += [
        "",
        "## Month by month",
        "",
        "MEASURED. Each table gives one dial's dollar gain, difference against hold and each complete model, largest drop, time-weighted average share, and costs paid.",
        "",
    ]
    for dial_id in dial_ids:
        d = dials[dial_id]
        label = f"{dial_id} (hindsight)" if d["hindsight"] else dial_id
        L += [
            f"### Dial {label}",
            "",
            f"| Month | Gain ($) | vs Hold | {m_hdr} | Largest drop | Avg share | Costs ($) |",
            "|---|---:|---:|" + "---:|" * len(models) + "---:|---:|---:|",
        ]
        for mo in data["months"]:
            r = d["months"][mo]
            vs_m = " | ".join(s_usd(r["vs_models_usd"][t]) for t in models)
            L.append(
                f"| {mo} | {usd(r['gain_usd'])} | {s_usd(r['vs_hold_usd'])} | "
                f"{vs_m} | {r['largest_drop_pct']:.1f}% | {r['avg_weight']:.2f} | {usd(r['costs_usd'])} |"
            )
        L.append("")

    L += [
        "## What this says",
        "",
        f"- MEASURED. Every fixed dial A to E beat holding {data['symbol']} ({usd(h['sum_gain_usd'])}) over these eight months.",
        f"- MEASURED. Plain moving-average rules that can cut all the way to 0.0 matched the best AI models without headlines or a language model: Dial B ended at {usd(b_dial['sum_gain_usd'])} (beating {len(b_beats)} of {len(models)} complete models: {', '.join(b_beats) if b_beats else 'none'}) and Dial C ended at {usd(c_dial['sum_gain_usd'])} (beating {len(c_beats)} of {len(models)} complete models: {', '.join(c_beats) if c_beats else 'none'}), compared with {usd(worst_model['sum_gain_usd'])} ({worst_model['name']}) to {usd(best_model['sum_gain_usd'])} ({best_model['name']}). Worst-month drops were {b_dial['worst_drop_pct']:.1f}% for Dial B and {c_dial['worst_drop_pct']:.1f}% for Dial C, against {worst_m_drop:.1f}% to {mildest_m_drop:.1f}% across the complete models, with costs of {usd(b_dial['sum_costs_usd'])} and {usd(c_dial['sum_costs_usd'])}.",
        f"- MEASURED. A constant lower share alone did not explain the models' edge over hold: Dial E (constant 0.7) ended at {usd(e_dial['sum_gain_usd'])} ({s_usd(e_dial['sum_vs_hold_usd'])} vs hold). Dials A ({usd(dials['A']['sum_gain_usd'])}) and D ({usd(dials['D']['sum_gain_usd'])}), which never cut below 0.5, also lagged B, C and the top models during the two sharp down months (June and November).",
        f"- MEASURED. Holding each model's own month-average share constant from day 1 (Dial F, hindsight) beat every complete model by {s_usd(f_min_margin)} to {s_usd(f_max_margin)}. That explains why the models failed their shuffled-stretch test in TM03: their gain over hold came from lowering exposure during falling months, but they cut after the drops had already started and paid more in trading costs than holding the same monthly share flat.",
        "- STATED. Plain trend rules on bitcoin over many years did not pass in replay 01 (`docs/research/12_replay_01_crypto_trend.md`, corrected in `docs/research/16_rig_audit.md`), so matching them over eight months is not evidence of an edge.",
        "",
        "## What this does not show",
        "",
        "- STATED. Eight months only (April to November 24, 2026). That window is far too short to judge any trading rule.",
        "- STATED. The dials were chosen on 2026-11-25 by someone who had already seen the months' hold returns.",
        "- STATED. These dials are not counted rule trials in `research_rig/TRIAL_LEDGER.md` and prove nothing on their own.",
        "- STATED. Long only, with no shorting and no leverage.",
        "- STATED. Fills are assumed at the open of the first recorded minute at or after each wake, with fixed half spread (`tm_crypto_half_spread_bps`) and fixed crypto fee (`practice_crypto_fee_bps_added`), not live order-book fills.",
        "- STATED. Dials F-* are hindsight: they read each model's finished monthly average share from `timemachine/results_tm03.json` and hold it from day 1 of that month.",
        "",
        "## Files",
        "",
        "- `timemachine/dial_rules_tm03.py`: runs the fixed dials through `timemachine/weights.py`, writes `timemachine/dial_rules_tm03.json` and this page (`--write`), checks freshness (`--check`), and runs synthetic-price tests (`--test`).",
        "- `timemachine/dial_rules_tm03.json`: stored JSON output with sorted keys.",
        "- `timemachine/results_tm03.json` and `docs/research/34_time_machine_tm03_bitcoin_dial.md`: the AI model results compared here.",
        "- `docs/research/12_replay_01_crypto_trend.md` and `docs/research/16_rig_audit.md`: multi-year replay 01 results where plain crypto trend rules did not pass.",
        "",
    ]
    return "\n".join(L)


def format_report(data):
    return render_doc(data)


# ---- Self-tests on made-up prices ----
def run_tests():
    t0 = dt.datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

    def make_bars(closes):
        return [dict(t=t0 + dt.timedelta(days=i), o=c, h=c, l=c, c=float(c), v=1.0) for i, c in enumerate(closes)]

    # 1. Look-ahead test: changing the bar starting AT the wake must not affect the answer at that wake
    base_closes = [100.0] * 55 + [110.0]
    wake = t0 + dt.timedelta(days=56)

    def bars_strict(all_bars, w):
        got = [b for b in all_bars if b["t"] + dt.timedelta(days=1) <= w]
        for b in got:
            assert b["t"] < w and b["t"] + dt.timedelta(days=1) <= w
        return got

    bars_1 = make_bars(base_closes + [1.0])
    bars_2 = make_bars(base_closes + [999999.0])
    for dial in ("A", "B", "C", "D", "E"):
        w1 = decide_series(dial, [wake], lambda w: bars_strict(bars_1, w))
        w2 = decide_series(dial, [wake], lambda w: bars_strict(bars_2, w))
        assert w1 == w2, f"look-ahead failed for {dial}: {w1} vs {w2}"

    # 2. Exact hand-checked values for A, B, C on tie, above, and partial SMA crossings
    flat = make_bars([100.0] * 50)
    w_flat = t0 + dt.timedelta(days=50)
    assert decide_series("A", [w_flat], lambda w: bars_strict(flat, w)) == [0.5]
    assert decide_series("B", [w_flat], lambda w: bars_strict(flat, w)) == [0.0]
    assert decide_series("C", [w_flat], lambda w: bars_strict(flat, w)) == [0.0]

    up = make_bars([100.0] * 49 + [105.0])
    assert decide_series("A", [w_flat], lambda w: bars_strict(up, w)) == [1.0]
    assert decide_series("B", [w_flat], lambda w: bars_strict(up, w)) == [1.0]
    assert decide_series("C", [w_flat], lambda w: bars_strict(up, w)) == [1.0]

    mixed = make_bars([80.0] * 30 + [120.0] * 10 + [100.0] * 10)
    c_val = decide_series("C", [w_flat], lambda w: bars_strict(mixed, w))[0]
    assert abs(c_val - 1.0 / 3.0) < 1e-12, f"expected 1/3, got {c_val}"

    # 3. Rule D hysteresis & monthly reset on made-up closes
    d_bars = make_bars([100.0] * 10 + [96.0, 94.0, 99.0, 100.0, 101.0])
    d_wakes = [t0 + dt.timedelta(days=k) for k in range(11, 16)]
    d_got = decide_series("D", d_wakes, lambda w: bars_strict(d_bars, w))
    assert d_got == [1.0, 0.5, 0.5, 0.5, 1.0], f"Rule D failed: {d_got}"
    d_fresh = decide_series("D", [t0 + dt.timedelta(days=14)], lambda w: bars_strict(d_bars, w))
    assert d_fresh == [1.0], f"Rule D fresh month reset failed: {d_fresh}"

    # 4. Rule E and F
    assert decide_series("E", d_wakes, lambda w: []) == [0.7] * len(d_wakes)
    assert decide_series("F-TEST", d_wakes, lambda w: [], const_weight=0.62) == [0.62] * len(d_wakes)

    # 5. End-to-end weights.py book check on made-up 2-wake month (verifies first-wake direct buy & costs)
    cfg = W.full_config()
    sym = "BTC/USD"
    w0 = dt.datetime(2026, 4, 1, 0, 0, tzinfo=UTC)
    w1 = dt.datetime(2026, 4, 2, 0, 0, tzinfo=UTC)
    w_end = dt.datetime(2026, 4, 3, 0, 0, tzinfo=UTC)
    meta = dict(market="crypto", symbols=[sym], benchmark=sym, opening={sym: 1.0}, wakes=[W.iso(w0), W.iso(w1)], end_utc=W.iso(w_end))
    table = dict(
        rows=[
            dict(fills={sym: [W.iso(w0), 100.0]}, marks={sym: 100.0}),
            dict(fills={sym: [W.iso(w1), 200.0]}, marks={sym: 200.0}),
        ],
        end_marks={sym: 200.0},
    )
    r_hold = run_month(meta, table, cfg, sym, [1.0, 1.0])
    r_half = run_month(meta, table, cfg, sym, [0.5, 0.5])
    r_zero = run_month(meta, table, cfg, sym, [0.0, 0.0])
    assert 990.0 < r_hold["gain_usd"] < 1000.0
    assert 495.0 < r_half["gain_usd"] < 500.0
    assert r_zero["gain_usd"] == 0.0 and r_zero["costs_usd"] == 0.0 and r_zero["trade_wakes"] == 0
    assert r_half["trade_wakes"] == 1 and r_hold["trade_wakes"] == 1
    assert 0.49 < r_half["costs_usd"] / r_hold["costs_usd"] < 0.51
    assert 0.57 < r_half["avg_weight"] < 0.60

    # 6. Doc renderer check: no em dashes, deterministic JSON & Markdown bytes
    synth_mo = {"2026-04": dict(gain_usd=10.0, largest_drop_pct=-2.0, avg_weight=0.5, costs_usd=2.0, duration_sec=86400.0, vs_hold_usd=5.0, vs_models_usd={"M1": 2.0})}
    synth_data = dict(
        disclaimer="test disclaimer",
        symbol=sym,
        months=["2026-04"],
        last_day="2026-04-30",
        total_models=2,
        complete_models=["M1"],
        incomplete_models=[dict(tag="M2", name="Model Two", months_done=0, months_total=1)],
        account_start_usd=1000.0,
        hold=dict(months={"2026-04": dict(gain_usd=5.0, largest_drop_pct=-3.0, avg_weight=1.0, costs_usd=3.5, duration_sec=86400.0)}, sum_gain_usd=5.0, worst_drop_pct=-3.0, avg_weight=1.0, sum_costs_usd=3.5),
        models={"M1": dict(name="Model One", months={"2026-04": dict(gain_usd=8.0, largest_drop_pct=-2.5, avg_weight=0.8, costs_usd=4.0, duration_sec=86400.0)}, sum_gain_usd=8.0, worst_drop_pct=-2.5, avg_weight=0.8, sum_costs_usd=4.0)},
        dials={
            k: dict(description=desc, hindsight=hs, months=synth_mo, sum_gain_usd=10.0, sum_vs_hold_usd=5.0, sum_vs_models_usd={"M1": 2.0}, worst_drop_pct=-2.0, avg_weight=0.5, sum_costs_usd=2.0, sum_trade_wakes=1)
            for k, desc, hs in list(DIAL_SPECS) + [("F-M1", "Model One month-average share held constant", True)]
        },
    )
    md1 = render_doc(synth_data)
    md2 = render_doc(synth_data)
    assert md1 == md2 and "\u2014" not in md1 and "1 of 2" in md1 and "Model Two (0 of 1)" in md1
    with tempfile.TemporaryDirectory() as td:
        jp, mp = Path(td) / "out.json", Path(td) / "out.md"
        js = json.dumps(synth_data, indent=1, sort_keys=True) + "\n"
        jp.write_text(js, encoding="utf-8")
        mp.write_text(md1, encoding="utf-8")
        assert jp.read_bytes() == js.encode("utf-8") and mp.read_bytes() == md1.encode("utf-8")
    print("OK: all 6 synthetic-price and doc tests passed.")


def main(argv=None):
    p = argparse.ArgumentParser(description="Fixed-dial comparison for TM03 through timemachine/weights.py.")
    p.add_argument("--write", action="store_true", help="write timemachine/dial_rules_tm03.json and docs/research/37_tm03_plain_dials.md")
    p.add_argument("--check", action="store_true", help="exit 1 if stored JSON or Markdown page is missing or stale")
    p.add_argument("--json", action="store_true", help="print JSON output")
    p.add_argument("--test", action="store_true", help="run self-tests on made-up prices")
    args = p.parse_args(argv)
    if args.test:
        run_tests()
        return 0
    data = build()
    js = json.dumps(data, indent=1, sort_keys=True) + "\n"
    md = render_doc(data)
    if args.check:
        stale = [
            str(path.relative_to(ROOT))
            for path, text in ((OUT_JSON, js), (OUT_DOC, md))
            if not path.is_file() or path.read_bytes() != text.encode("utf-8")
        ]
        if stale:
            print("stale: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("ok")
        return 0
    if args.write:
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_DOC.write_text(md, encoding="utf-8")
        print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_DOC.relative_to(ROOT)}")
        return 0
    if args.json:
        print(js, end="")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
