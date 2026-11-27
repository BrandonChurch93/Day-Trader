"""Doc 140: false-pass audit of the scoreboard, from repo files only.

Reads the plans, calibration and power files, thresholds, and results records
for the rate at which a rule with no edge would pass all its marks,
then writes docs/research/140_false_pass_audit.md. It runs no scorer, opens no
price or result file off the repo and computes no return. Every number in the
page is read here from a repo file or computed here from such a number.

Run: nice -n 10 python3 research_rig/build_doc140_false_pass_audit.py
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RR = ROOT / "research_rig"
OUT = ROOT / "docs" / "research" / "140_false_pass_audit.md"
SCORECARD = "docs/research/95_where_we_stand_after_32_tests.md"
PLAN75_RESULT = "docs/research/181_plan_75_heldback_result.md"

# Stated assumptions, used only where the repo has no measured figure.
LOW_ASSUME = 0.005   # low bracket: other marks cut a nominal tail well below itself
HIGH_UNKNOWN = 0.10  # high bracket for a test with neither a measured rate nor a nominal mark


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def find(rel, pattern, group=1, flags=0):
    m = re.search(pattern, text(rel), flags)
    if not m:
        sys.exit(f"pattern not found in {rel}: {pattern}")
    return m.group(group)


def jload(rel):
    return json.loads(text(rel))


def yaml_scalar(key):
    """value of a top-level `key:` block in config/thresholds.yaml (scalar)."""
    t = text("config/thresholds.yaml")
    m = re.search(r"^" + re.escape(key) + r":\n  value: ([^\n]+)", t, re.M)
    if not m:
        sys.exit(f"threshold not found: {key}")
    return m.group(1)


def yaml_inner(block, key):
    t = text("config/thresholds.yaml")
    m = re.search(r"^" + re.escape(block) + r":\n  value: \{([^\n]+)\}", t, re.M)
    if not m:
        sys.exit(f"threshold block not found: {block}")
    m2 = re.search(r"\b" + re.escape(key) + r": ([0-9.]+)", m.group(1))
    if not m2:
        sys.exit(f"key {key} not in {block}")
    return float(m2.group(1))


def norm_tail(t):
    return 0.5 * math.erfc(t / math.sqrt(2))


def binom_cdf(k, n, p):
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    lp, lq = math.log(p), math.log1p(-p)
    return sum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
               for i in range(0, k + 1))


def cp_upper(k, n, alpha=0.05):
    """one-sided exact (Clopper-Pearson) upper limit for k passes in n runs."""
    if k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if binom_cdf(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def binom_ge(k, n, p):
    return 1 - binom_cdf(k - 1, n, p)


def tm_method(n, p_top, need_top, need_median):
    """chance that at least need_top of n independent no-skill models land above
    the (1 - p_top) percentile and at least need_median land above the median."""
    tot = 0.0
    for a in range(n + 1):            # above the top percentile
        for b in range(n - a + 1):    # above median, below the top percentile
            c = n - a - b
            if a >= need_top and a + b >= need_median:
                tot += (math.factorial(n) / (math.factorial(a) * math.factorial(b) * math.factorial(c))
                        * p_top ** a * (0.5 - p_top) ** b * 0.5 ** c)
    return tot


# ---------------------------------------------------------------- scored tests
def doc95_rows():
    scorecard = text(SCORECARD)
    totals = re.findall(r"^\| Total \| (\d+) \| (\d+) \|", scorecard, re.M)
    if len(totals) != 1:
        sys.exit(f"{SCORECARD}: expected one scored-test Total row, found {len(totals)}")
    expected, expected_passes = map(int, totals[0])
    rows = []
    for line in scorecard.splitlines():
        m = re.match(r"\| (\d+) \| ([^|]+) \| [^|]+ \| ([^|]+) \| [^|]+ \| ([^|]+) \| (.+) \|$", line)
        if m:
            paths = re.findall(r"`(docs/[^`]+)`", m.group(5))
            rows.append({"n": int(m.group(1)), "test": m.group(2).strip(), "family": m.group(3).strip(),
                         "result": m.group(4).strip(), "page": paths[0] if paths else ""})
    numbers = [row["n"] for row in rows]
    if numbers != list(range(1, expected + 1)):
        sys.exit(f"{SCORECARD}: Total says {expected} scored tests, but parsed {len(rows)} rows with IDs {numbers}")
    actual_passes = counted_passes(rows)
    if actual_passes != expected_passes:
        sys.exit(f"{SCORECARD}: Total says {expected_passes} counted passes, but found {actual_passes}")
    return rows


def counted_passes(rows):
    return sum(r["result"].casefold().startswith("passed") for r in rows)


def spec(n):
    """returns dict(label, low, high, src, note) for test n."""
    T_MARK = 2.0
    tail = norm_tail(T_MARK)

    def nominal_t(rel, pattern, arms=1, what="t mark"):
        val = float(find(rel, pattern))
        assert abs(val - T_MARK) < 1e-9, (rel, val)
        hi = min(1.0, arms * norm_tail(val))
        return dict(label="NOMINAL", low=LOW_ASSUME, high=hi,
                    src=f"`{rel}`: {what} {val:g}" + (f", {arms} legs" if arms > 1 else ""),
                    note="one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it")

    def measured_k(rel, k, nn, key, note=""):
        return dict(label="MEASURED", low=k / nn, high=cp_upper(k, nn),
                    src=f"`{rel}`: {key} ({k} of {nn})", note=note or "high is the one-sided 95% upper limit for that count")

    # DSR-family replays (01, 03, 04, 05, 06, 07, 09): deflated Sharpe mark, measured
    # by auditor B on made-up data with related rules and no edge (doc 16).
    dsr_bar = float(yaml_scalar("replay_min_deflated_sharpe"))
    dsr_rate = float(find("docs/research/16_rig_audit.md", r"with strongly related rules and no edge it passed ([0-9.]+)% of the time")) / 100
    pbo_rate = float(find("docs/research/16_rig_audit.md", r"On made-up data with no edge at all, (\d+)% of samples still came in under the bar")) / 100

    def dsr(rel):
        return dict(label="MEASURED, one mark", low=LOW_ASSUME, high=dsr_rate,
                    src=f"`docs/research/16_rig_audit.md`: deflated Sharpe mark ({dsr_bar:g}) passed {dsr_rate:.1%} of no-edge samples; overfitting mark let {pbo_rate:.0%} through; plan `{rel}`",
                    note="measured for one mark of five; all marks together is lower and was not measured")

    if n == 1:
        return dsr("research_rig/PREREG_01_daily_crypto_trend.md")
    if n == 2:
        return dict(label="STATED", low=0.0, high=0.0, src="`docs/research/14_ai_calls_pilot_02.md`: inconclusive by design",
                    note="no pass mark, so no pass by luck was possible")
    if n == 3:
        return dsr("research_rig/PREREG_03_intraday_crypto.md")
    if n == 4:
        return dsr("research_rig/PREREG_04_coin_basket_trend.md")
    if n == 5:
        return dsr("research_rig/PREREG_05_stock_trend_free_data.md")
    if n == 6:
        return dsr("research_rig/PREREG_06_fund_trend_paid_data.md")
    if n == 7:
        return dsr("research_rig/PREREG_07_intraday_spy_qqq.md")
    if n == 8:
        return dsr("research_rig/PREREG_09_crypto_methods.md")
    if n == 9:
        return dict(label="STATED", low=0.0, high=0.0, src="`docs/research/44_replay_11_earnings_reader.md`: design half only",
                    note="held-back half not run, so no verdict and no pass by luck was possible")
    if n == 10:
        ne = jload("research_rig/noedge_12.json")
        hold = find("docs/research/47_replay_12_congress_followers.md", r"Chosen by the fixed rule[^.]*?hold (\d+) trading days")
        r = ne["holds"][hold]["pass_rate_blocks"]
        k = round(r * ne["sets"])
        return dict(label="MEASURED, one mark", low=LOW_ASSUME, high=cp_upper(k, ne["sets"]),
                    src=f"`research_rig/noedge_12.json`: holds.{hold}.pass_rate_blocks = {r} ({k} of {ne['sets']}), the chosen {hold}-day hold",
                    note="measured for the bootstrap mark only; all five marks together is lower")
    if n in (11, 12):
        pct = yaml_inner("replay_13_plan", "random_percentile")
        yrs = int(yaml_inner("replay_13_plan", "min_years_above"))
        hi = binom_ge(yrs, 7, 1 - pct / 100)
        return dict(label="NOMINAL", low=min(LOW_ASSUME, hi), high=hi,
                    src=f"`config/thresholds.yaml` replay_13_plan: above the {pct:g}th percentile of random in at least {yrs} of 7 years",
                    note="binomial tail of the random-percentile mark alone with independent years; not measured")
    if n == 13:
        o = jload("research_rig/noedge_14.json")["by_cost"]["cost_5_bps"]
        ks = {arm: int(o[arm]["passes"]["all_four"].split("/")[0]) for arm in ("small", "wide")}
        nn = int(o["small"]["passes"]["all_four"].split("/")[1])
        return dict(label="MEASURED", low=max(ks.values()) / nn, high=min(1.0, sum(cp_upper(k, nn) for k in ks.values())),
                    src=f"`research_rig/noedge_14.json`: by_cost.cost_5_bps.{{small,wide}}.passes.all_four = {ks['small']}/{nn} and {ks['wide']}/{nn}",
                    note="two judged lists; low is the larger list alone, high adds both upper limits")
    if n == 14:
        k = int(find("research_rig/PREREG_16_hot_five_hedged.md", r"With no edge built in, all four marks passed in (\d+) of 20 worlds"))
        return measured_k("research_rig/PREREG_16_hot_five_hedged.md", k, 20, "no edge, all four marks")
    if n == 15:
        k = int(find("research_rig/PREREG_17_short_the_peak.md", r"With no edge built in, all three marks passed in (\d+) of 20 worlds"))
        return measured_k("research_rig/PREREG_17_short_the_peak.md", k, 20, "no edge, all three marks")
    if n == 16:
        k = int(find("research_rig/PREREG_18_funding_carry.md", r"Zero edge cleared all marks in (\d+) of 20 worlds"))
        return measured_k("research_rig/PREREG_18_funding_carry.md", k, 20, "zero edge, all marks")
    if n == 17:
        k = int(find("research_rig/PREREG_19_monday_asia.md", r"Of 20 seeds at each gross plant, (\d+) cleared all five marks at 0 bps"))
        return measured_k("research_rig/PREREG_19_monday_asia.md", k, 20, "0 bps plant, all five marks")
    if n == 18:
        k = int(find("research_rig/PREREG_20_upbit_listing_short.md", r"the tightened five marks cleared (\d+), \d+, \d+ and \d+ of 20 seeds at planted net means of 0%"))
        return measured_k("research_rig/PREREG_20_upbit_listing_short.md", k, 20, "0% plant, all five marks")
    if n == 19:
        k = int(find("research_rig/PREREG_23_ipo_fast_track.md", r"With no edge, (\d+) world in 20 passed all eight marks"))
        return measured_k("research_rig/PREREG_23_ipo_fast_track.md", k, 20, "no edge, all eight marks")
    if n == 20:
        pct = float(find("research_rig/PREREG_24_same_coin_carry.md", r"nearest-rank (\d+)th percentile of 500 twins"))
        return dict(label="NOMINAL", low=LOW_ASSUME, high=1 - pct / 100,
                    src=f"`research_rig/PREREG_24_same_coin_carry.md`: above the {pct:g}th percentile of 500 twins",
                    note="tail of the twin mark alone; not measured")
    if n == 21:
        return nominal_t("research_rig/PREREG_25_treasury_month_end.md", r"Welch t at least (\d\.\d)", what="t marks (window t and Welch t) at")
    if n == 22:
        return nominal_t("research_rig/PREREG_31_bond_etf_month_end.md", r"One-sample residual t-statistic at least (\d\.\d)", what="t marks at")
    if n == 23:
        return nominal_t("research_rig/PREREG_33_treasury_auctions.md", r"One-sample t at least (\d\.\d)", what="t marks at")
    if n == 24:
        return nominal_t("research_rig/PREREG_35_ibit_cme_expiry.md", r"One-sample t at least (\d\.\d)", what="t marks at")
    if n == 25:
        return nominal_t("research_rig/PREREG_39_iwm_preholiday.md", r"Welch t at least (\d\.\d)", what="t marks at")
    if n == 26:
        return nominal_t("research_rig/PREREG_41_pension_month_end.md", r"conventional one-sample t at least (\d\.\d)", what="t mark at")
    if n in (27, 28):
        rel = "timemachine/PLAN_TM01_crypto_price_only.md" if n == 27 else "timemachine/PLAN_TM02_crypto_with_news.md"
        pct = float(find(rel, r"above the (\d+)th percentile of its own 20 twins"))
        p = 1 - pct / 100
        return dict(label="NOMINAL", low=p * 0.5, high=1 - (1 - p) ** 6,
                    src=f"`{rel}`: any of 6 models above BTC and above the {pct:g}th percentile of 20 twins",
                    note=f"low: one model, models moving together, beating BTC a coin flip; high: twin mark alone, six independent models")
    pct_w = float(yaml_scalar("tm_weights_pass_percentile"))
    if n in (29, 30, 33, 34):
        rel = {29: "timemachine/PLAN_TM03_bitcoin_dial.md", 30: "timemachine/PLAN_TM04_stock_basket.md",
               33: "timemachine/PLAN_TM06_hot_coin_swing.md", 34: "timemachine/PLAN_TM06_hot_coin_swing.md"}[n]
        mins = [int(x) for x in re.findall(r"method_min_models_[a-z_]+: (\d+)", text("config/thresholds.yaml"))]
        need_med, need_top = 5, 2
        assert need_med in mins and need_top in mins
        p = 1 - pct_w / 100
        return dict(label="NOMINAL", low=tm_method(6, p, need_top, need_med), high=binom_ge(need_top, 6, p),
                    src=f"`{rel}` and `config/thresholds.yaml`: method needs {need_top} of 6 models above the {pct_w:g}th percentile and {need_med} of 6 above the middle",
                    note="six independent no-skill models; low counts both method lines, high the percentile line alone")
    if n == 31:
        p = 1 - pct_w / 100
        return dict(label="NOMINAL", low=p ** 3, high=p,
                    src=f"`timemachine/TM06R_addendum.md`: one model, three runs, each judged above the {pct_w:g}th percentile of its twins",
                    note="low: all three runs clear by luck; high: one run clears")
    if n == 32:
        return dict(label="STATED", low=0.0, high=0.0, src="`docs/research/66_measure_15_breakout_fills.md`: fill-cost gate, not a return mark",
                    note="a cost measurement cannot produce a counted pass")
    if n == 35:
        return nominal_t("research_rig/PREREG_21_odd_lot_tenders.md", r"ordinary one-sample \(t\) at least (\d\.\d)",
                         what="t mark at (its planted-0% calibration count is not on the repo)")
    if n in (36, 37):
        return nominal_t("research_rig/PREREG_46_cftc_altcoin_futures.md", r"paired date-clustered t at least (\d\.\d)", what="paired clustered t mark at")
    if n in (38, 40):
        rel = "research_rig/CALIBRATION_48.json" if n == 38 else "research_rig/CALIBRATION_53.json"
        o = jload(rel)
        k = round(o["pass_rate"]["zero_edge"] * o["trials"])
        d = measured_k(rel, k, o["trials"], f"pass_rate.zero_edge = {o['pass_rate']['zero_edge']}")
        if n == 40:
            same = jload("research_rig/CALIBRATION_48.json") == o
            d["note"] = ("file is identical to CALIBRATION_48.json (same seed and marks); " if same else "") + d["note"]
        return d
    if n == 39:
        o = jload("research_rig/CALIBRATION_52.json")
        sel = o["selected"]
        v = [x for x in o["variants"] if x["breadth"] == sel["breadth"] and x["raw_t_required"] == sel["raw_t_required"]][0]
        z = v["scenarios"]["quarter_only"]["0"]
        return dict(label="MEASURED", low=z["rate"], high=v["null_upper_wilson"],
                    src=f"`research_rig/CALIBRATION_52.json`: selected variant (breadth {sel['breadth']}, raw t {sel['raw_t_required']}), scenarios.quarter_only.0.rate = {z['rate']} ({z['count']} of {o['assumptions']['worlds']}); high is its null_upper_wilson",
                    note="")
    if n == 41:
        o = jload("research_rig/CALIBRATION_60.json")
        lo_k = o["cases"]["0.65"]["all_mark_passes"][o["cases"]["0.65"]["edges"].index(0.0)]
        hi_k = o["cases"]["0.75"]["all_mark_passes"][o["cases"]["0.75"]["edges"].index(0.0)]
        nn = o["cases"]["0.75"]["trials"]
        return dict(label="MEASURED", low=lo_k / nn, high=cp_upper(hi_k, nn),
                    src=f"`research_rig/CALIBRATION_60.json`: cases.0.65 and cases.0.75 all_mark_passes at edge 0 = {lo_k} and {hi_k} of {nn}",
                    note="two placement assumptions; high is the upper limit of the 0.75 case")
    if n == 42:
        o = jload("research_rig/POWER_61.json")
        k = o["full"]["by_placement"]["0.8"]["counts"]["1.5"]["winsor_t"][o["edge_bps"].index(0)]
        d = measured_k("research_rig/POWER_61.json", k, o["trials"], "full.by_placement.0.8.counts.1.5.winsor_t at 0 bp")
        d["label"] = "MEASURED for plan 61, STATED for 62"
        d["note"] = "plan 62 reuses plan 61's power run (`research_rig/PREREG_62_special_dividend_ex_day_v2.md`); " + d["note"]
        return d
    if n == 43:
        o = jload("research_rig/calibration_22.json")
        e0 = o["edges_pct"]["0"]
        k = round(e0["pass_share"] * e0["seeds"])
        return measured_k("research_rig/calibration_22.json", k, e0["seeds"], f"edges_pct.0.pass_share = {e0['pass_share']}")
    if n == 44:
        p = jload("research_rig/POWER_65.json")
        lowest = min(r["sharpe"] for r in p["table"])
        d = nominal_t("research_rig/PREREG_65_stock_bond_rebalance_spread.md", r"\| Evidence \| t at least (\d)", what="clustered t mark at")
        d["note"] = f"`research_rig/POWER_65.json` has no zero-edge row (lowest Sharpe {lowest}), so no measured rate; " + d["note"]
        return d
    if n == 45:
        pattern = (r"^## How much a pass like this proves\n\n"
                   r"- MEASURED by the independent auditor on made-up price worlds with no edge, same code and same four marks: "
                   r"(\d+) of (\d+) worlds passed \([0-9.]+%\); with a (\d+%) yearly upward drift in coin prices, (\d+) of (\d+)")
        lo_k, lo_n, hi_k, hi_n = (int(find(PLAN75_RESULT, pattern, group, re.M)) for group in (1, 2, 4, 5))
        drift = find(PLAN75_RESULT, pattern, 3, re.M)
        return dict(label="MEASURED", low=lo_k / lo_n, high=cp_upper(hi_k, hi_n),
                    src=f"`{PLAN75_RESULT}`: {lo_k} of {lo_n} with no drift, {hi_k} of {hi_n} with {drift} yearly drift",
                    note="high is the one-sided 95% upper limit on the drift count; the edge model and coverage in those worlds are the auditor's assumptions")
    if n == 46:
        rel = "research_rig/PREREG_76_washout_rebound.md"
        worlds = int(find(rel, r"Each scenario uses ([\d,]+) worlds").replace(",", ""))
        rows = {int(c): float(r) / 100 for c, r in re.findall(r"^\| (\d+) \| 5% \| ([0-9.]+)% / [0-9.]+% \|", text(rel), re.M)}
        if sorted(rows) != [64, 96, 144]:
            sys.exit(f"{rel}: expected the 64, 96 and 144 trade rows of the 5% arm")
        k_hi = round(rows[64] * worlds)
        return dict(label="MEASURED", low=min(rows.values()), high=cp_upper(k_hi, worlds),
                    src=(f"`{rel}`: invented-data power table, 5% arm, no edge, main cost: "
                         + ", ".join(f"{100 * v:.2f}% at {c} trades" for c, v in sorted(rows.items())) + f", {worlds:,} worlds each"),
                    note="made-up returns; low is the 144-trade row, high the one-sided 95% upper limit on the 64-trade row; the run had 83 trades")
    sys.exit(f"no spec for test {n}")


# ---------------------------------------------------------- closed before prices
def closed_before_prices():
    """ideas closed before any return: ledger rows plus queue Done rows not already in the ledger."""
    q = text("docs/QUEUE.md")
    qrows = []
    for line in q.splitlines():
        if line.startswith("| "):
            c = [x.strip() for x in line.split("|")]
            if len(c) >= 4 and c[1] != "#":
                qrows.append(c)
    pat = re.compile(r"CLOSED|STOPPED AT VALIDATION|NOT SCORED|Blocked at input validation")
    found = {}
    for line in text("research_rig/TRIAL_LEDGER.md").splitlines():
        if not line.startswith("| "):
            continue
        c = [x.strip() for x in line.split("|")]
        if len(c) < 5 or not re.match(r"\d+$", c[1]):
            continue
        st, plan = c[-2], c[3]
        if "REVIEW_48" in plan or not pat.search(st[:80]):
            continue
        qtext = " ".join(r[3] for r in qrows if re.search(r"ledger[s]? (\d+ and )?" + c[1] + r"\b", r[2]))
        name = re.sub(r"`|\s*\(to be drafted\)", "", plan)
        found["ledger " + c[1]] = (name, st[:60] + " || " + st + " " + plan + " " + qtext)
    done = q[q.index("## Done"):]
    qpat = re.compile(r"^(CLOSED|Closed|Done [^.]*\. Closed on count)|dropped at feasibility|Closed without a run")
    extra = {}
    for line in done.splitlines():
        if not line.startswith("| "):
            continue
        c = [x.strip() for x in line.split("|")]
        if len(c) < 4 or c[1] == "#" or "identity review" in c[2] or not qpat.search(c[3]):
            continue
        refs = set(re.findall(r"ledger (\d+)", c[2] + " " + c[3]))
        if any("ledger " + r in found for r in refs):
            continue
        key = "queue " + (c[1] if c[1] != "-" else "(no number)")
        extra[key] = (re.sub(r"\s*\(.*", "", c[2])[:70], c[3][:60] + " || " + c[3])
    def kind(s):
        head = s.split(" || ")[0].lower()
        for k, keys in (("power", ("power",)), ("count", ("count",)), ("cost", ("cost",)), ("coverage", ("coverage",)),
                        ("feasibility", ("feasibility",)), ("validation", ("validation",))):
            if any(x in head for x in keys):
                return k
        low = s.lower()
        if "placed pairs under" in low:
            return "count"
        if "power" in low or "made-up data" in low or "chance of passing" in low:
            return "power"
        if "count" in low or "placed pairs under" in low or "signal fired" in low:
            return "count"
        for k in ("cost", "coverage", "feasibility", "validation"):
            if k in low:
                return k
        return "other, before prices"
    return [(k, v[0], kind(v[1])) for k, v in list(found.items()) + list(extra.items())]


# --------------------------------------------------------------- counted passes
def pass_marks(rel):
    out = []
    for line in text(rel).splitlines():
        c = [x.strip() for x in line.split("|")]
        if len(c) >= 5 and c[-2] in ("met", "not met"):
            out.append(" | ".join(c[1:-1]))
        if len(out) and not line.startswith("|"):
            break
    return out


def main():
    rows = doc95_rows()
    for r in rows:
        r.update(spec(r["n"]))
    ai = [r for r in rows if r["family"].startswith("AI")]
    nopass = [r for r in rows if r["high"] == 0.0]
    counted_pool = [r for r in rows if r not in ai and r not in nopass]
    n_pass = counted_passes(rows)
    lo_all, hi_all = sum(r["low"] for r in rows), sum(r["high"] for r in rows)
    lo_c, hi_c = sum(r["low"] for r in counted_pool), sum(r["high"] for r in counted_pool)
    lo_ai, hi_ai = sum(r["low"] for r in ai), sum(r["high"] for r in ai)
    n_meas = sum(1 for r in rows if r["label"].startswith("MEASURED") and "one mark" not in r["label"])
    n_one = sum(1 for r in rows if "one mark" in r["label"])
    n_nom = sum(1 for r in rows if r["label"] == "NOMINAL")
    n_stated0 = len(nopass)

    # Chance of at least the recorded count by luck in the counted pool, Poisson-binomial.
    def p_at_least(ps, k):
        dist = [1.0]
        for p in ps:
            dist = [a * (1 - p) + (dist[i - 1] * p if i else 0) for i, a in enumerate(dist)] + [dist[-1] * p]
        return sum(dist[k:])
    tail_lo = p_at_least([r["low"] for r in counted_pool], n_pass)
    tail_hi = p_at_least([r["high"] for r in counted_pool], n_pass)

    closed = closed_before_prices()
    kinds = {}
    for c in closed:
        kinds[c[2]] = kinds.get(c[2], 0) + 1

    by = {r["n"]: r for r in rows}
    clock = subprocess.run(["date", "-u", "+%Y-%m-%d %H:%M UTC"], capture_output=True, text=True).stdout.strip()

    # pass details read from results pages and plans
    m25 = pass_marks("docs/research/69_replay_25_treasury_month_end.md")
    m48 = pass_marks("docs/research/103_replay_48_muni_cef_january.md")
    m20 = pass_marks("docs/research/71_replay_20_upbit_listing_short.md")
    t25 = float(find("docs/research/69_replay_25_treasury_month_end.md", r"Net window t at least 2\.0 \| ([0-9.]+)"))
    w25 = float(find("docs/research/69_replay_25_treasury_month_end.md", r"Welch t ([0-9.]+) \| met"))
    yrs48_bar = find("docs/research/103_replay_48_muni_cef_january.md", r"Positive years \| at least (\d+ of \d+) above zero \| (\d+ of \d+)", 1)
    yrs48_got = find("docs/research/103_replay_48_muni_cef_january.md", r"Positive years \| at least (\d+ of \d+) above zero \| (\d+ of \d+)", 2)
    t20 = float(find("docs/research/71_replay_20_upbit_listing_short.md", r"Per-trade t at least 2\.0 \| ([0-9.]+)"))
    share26 = find("docs/research/71_replay_20_upbit_listing_short.md", r"2026 averaged [^.]*\.\d% and supplied (\d+)% of the summed net returns")
    yrs75 = find(PLAN75_RESULT, r"MEASURED: ([Oo]ne of three) calendar years was positive").lower()
    harsh75 = find(PLAN75_RESULT, r"At 145 bp a side: (-[0-9.]+%) and -[0-9.]+%")
    spread75 = find(PLAN75_RESULT, r"the two differ by ([0-9.]+) percentage points on the net return", flags=re.I)
    corr53 = find("docs/research/122_replay_53_taxable_fund_january_rebound.md", r"Pearson correlation with the \[Replay 48[^)]*\)\s*was ([+0-9.]+)")
    hs = find("docs/research/74_round_10_forced_flow_ideas.md", r"Hartley and Schwarz cover (\d{4} to \d{4}) Treasuries")
    ov48 = find("research_rig/PREREG_48_muni_cef_tax_loss.md", r"(Turns 2016 to 2019 overlap[^.]*\.)")
    viewed20 = find("research_rig/PREREG_20_upbit_listing_short.md", r"(All dates have already been viewed\.)")
    sel20 = find("research_rig/PREREG_20_upbit_listing_short.md", r"(The author selected the hold after viewing results and tried other variants\.)")
    e01_first = find("practice/traders/E01_tlt_month_end_close.md", r"First month (\w+ \d{4})")
    e04_entry = find("practice/traders/E04_muni_cef_january_watch.md", r"\| Pretend entry \| (\w+ \d{4}-\d{2}-\d{2})")
    e04_exit = find("practice/traders/E04_muni_cef_january_watch.md", r"(\w+ \d{4}-\d{2}-\d{2}) close: judged result")
    q49 = find("docs/QUEUE.md", r"^\| 49 \| (Upbit KRW listing forward watcher[^|]*?) \(", 1, re.M)
    noshort = find("practice/traders/ROSTER.md", r"(It does not place short sales)")
    logs = sorted(p.name for p in (ROOT / "practice" / "forward").glob("*.json")) if (ROOT / "practice" / "forward").exists() else []

    rel25 = [22, 23, 26, 39, 44]

    def fam(nums):
        return "; ".join(f"{by[k]['test']}: {by[k]['result']}" for k in nums)

    def pct(x):
        return f"{100 * x:.2f}%"

    L = []
    w = L.append
    w(f"# 140. False-pass audit: how many of our {n_pass} passes could be luck")
    w("")
    w(f"Written {clock} by `research_rig/build_doc140_false_pass_audit.py`, which reads every figure below from repo files. No scorer was run, no price or result file off the repo was opened, and no return was computed.")
    w("")
    w("Labels: MEASURED means a no-edge pass rate counted on made-up data and recorded in a plan file or audit record. MEASURED, one mark means only one of the marks was counted that way, so the all-mark rate is lower. NOMINAL means no rate was measured; the figure is the textbook tail of the plan's mark (a one-sided normal tail for a t of 2, or a percentile tail), worked out here, not measured. STATED means taken from a plan or results page as written. INFERENCE means a reading of the evidence. UNKNOWN means not on the repo.")
    w("")
    w("## Headline")
    w("")
    w(f"- Expected passes by luck across all {len(rows)} scored tests: low {lo_all:.2f}, high {hi_all:.2f}. Counted passes: {n_pass}.")
    w(f"- About half of the high figure comes from the {len(ai)} AI time-machine tests ({lo_ai:.2f} to {hi_ai:.2f}). Their marks were loose (a model above the 80th or 90th percentile of its own twins), but a clearing there is reported as shown, never as a counted pass, so they cannot explain the {n_pass} counted passes.")
    w(f"- Expected luck passes in the {len(counted_pool)} trading tests that could give a counted pass: low {lo_c:.2f}, high {hi_c:.2f}. The {n_pass} seen is {n_pass / hi_c:.1f} to {n_pass / lo_c:.1f} times what luck alone gives.")
    w(f"- Chance of {n_pass} or more passes by luck alone in those {len(counted_pool)}: {pct(tail_lo)} on the low figures, {pct(tail_hi)} on the high figures (independent tests assumed; the month-end tests share windows).")
    w(f"- Rates: {n_meas} tests have a measured all-mark no-edge rate, {n_one} have one measured mark only, {n_nom} have no measured rate (UNKNOWN) and are bracketed by the nominal tail of their own t or percentile mark as the high and a stated low of {LOW_ASSUME} per test, and {n_stated0} could not pass at all (design only, inconclusive by design, a cost gate).")
    w(f"- Ideas closed before any return on count, power, cost, coverage, validation or feasibility: {len(closed)} ({kinds.get('count', 0)} on count, {kinds.get('power', 0)} on power). They had no chance to pass by luck, so they add nothing to the luck figure.")
    w("")
    w("## Assumptions, stated")
    w("")
    w(f"- Low bracket where only a nominal t tail exists: {LOW_ASSUME} per test. The other marks (count floors, trims, year breadth) can only cut the tail, and the passes that did happen cleared the t mark by a small margin, so this is a floor, not an estimate.")
    w("- High bracket for a nominal t mark: the one-sided normal tail at t of 2, "
      f"{pct(norm_tail(2.0))}, times the number of separately judged legs. It ignores the other marks, so it is a ceiling under normal errors. Fat tails, overlapping windows or few clusters can push a real no-edge rate above it; that is UNKNOWN for each such test.")
    w("- High bracket for a measured count: the one-sided 95% upper limit for that count. A 0 of 20 calibration still allows up to "
      f"{pct(cp_upper(0, 20))} by this rule, which is why those tests have wide highs.")
    w("- Tests are summed as if independent. Several are not (Replays 25, 31, 41 and 65 share month-end windows; Replays 48 and 53 share dates). Dependence does not change the expected count; it makes clusters of luck passes or misses more likely.")
    w("")
    w(f"## The {len(rows)} tests")
    w("")
    w("| # | Test | Family | Result (doc 95) | Label | Low | High | Where the figure comes from | Note |")
    w("|---:|---|---|---|---|---:|---:|---|---|")
    for r in rows:
        w(f"| {r['n']} | {r['test']} | {r['family']} | {r['result']} | {r['label']} | {pct(r['low'])} | {pct(r['high'])} | {r['src']} | {r['note']} |")
    w(f"| | Total, all {len(rows)} | | | | {lo_all:.2f} | {hi_all:.2f} | | |")
    w(f"| | Total, {len(counted_pool)} trading tests that could give a counted pass | | | | {lo_c:.2f} | {hi_c:.2f} | | |")
    w("")
    w(f"Results are copied from `{SCORECARD}`. Results pages are those cited there.")
    w("")
    w(f"## How that compares with {n_pass}")
    w("")
    w(f"- MEASURED and NOMINAL together: luck alone would give about {lo_c:.2f} to {hi_c:.2f} counted passes, compared with {n_pass} observed.")
    w(f"- INFERENCE: on the high figures {n_pass} or more by luck happens {pct(tail_hi)} of the time if tests are independent. That is not the probability any specific pass was luck.")
    met_marks = [by[k] for k in (11, 33, 31)]
    w(f"- {len(met_marks)} other results met their own marks and were not counted: " + "; ".join(f"{r['test']} ({r['result']})" for r in met_marks)
      + f". Counting those too, {n_pass + len(met_marks)} of {len(rows)} cleared, against {lo_all:.2f} to {hi_all:.2f} expected by luck.")
    w("")
    w(f"## The {n_pass} counted passes")
    w("")
    w("### Replay 25, TLT over the last three sessions of the month")
    w("")
    w(f"- No-edge pass rate: {by[21]['label']}, {pct(by[21]['low'])} to {pct(by[21]['high'])}. No calibration was run for this plan; only the t marks give a figure.")
    w(f"- How far past its marks (MEASURED, `docs/research/69_replay_25_treasury_month_end.md`): window t {t25} against 2.0, Welch t {w25} against 2.0. The marks it cleared:")
    w("")
    for m in m25:
        w(f"- {m}")
    w("")
    w(f"- Relatives that did not pass (MEASURED): {fam(rel25)}. Measurement 34 (TMF, UBT) used the same windows and is not new evidence; Replay 26 (2002 to 2015) was blocked at input validation and never scored. So 1 of {len(rel25) + 1} scored month-end and bond-flow tests passed.")
    w(f"- Overlap with the source sample (STATED, `docs/research/74_round_10_forced_flow_ideas.md`): Hartley and Schwarz cover {hs} Treasuries, so 2016 to 2018 of the 2016 to 2026 window overlap; the rest does not.")
    w(f"- Forward log (STATED, `practice/traders/E01_tlt_month_end_close.md`): E01 records the same window each month from {e01_first}. MEASURED: no E01 record yet (forward logs on the repo: {', '.join(logs) if logs else 'none'}).")
    w(f"- Trust today: a modest pass with no measured null, sitting among {len(rel25)} failed relatives, so treat it as a lead that E01 must confirm, not as a found edge.")
    w("")
    w("### Replay 48, muni closed-end fund losers into January")
    w("")
    w(f"- No-edge pass rate: {by[38]['label']}, {pct(by[38]['low'])} (upper {pct(by[38]['high'])}) from `research_rig/CALIBRATION_48.json`, set before the run.")
    w("- How far past its marks (MEASURED, `docs/research/103_replay_48_muni_cef_january.md`):")
    w("")
    for m in m48:
        w(f"- {m}")
    w("")
    w(f"- Closest mark: positive years, {yrs48_got} against a bar of at least {yrs48_bar}; one losing year more and it would not have passed. Ten turns is a small sample.")
    w(f"- Relatives (MEASURED): {fam([40])}. Its yearly results had a correlation of {corr53} with Replay 48 (`docs/research/122_replay_53_taxable_fund_january_rebound.md`), so it is a near copy that failed on breadth. Three more tax-loss relatives (preferreds, BDCs, Plan 54) were closed on power before prices.")
    w(f"- Overlap with the source sample (STATED, `research_rig/PREREG_48_muni_cef_tax_loss.md`): {ov48}")
    w(f"- Forward log (STATED, `practice/traders/E04_muni_cef_january_watch.md`): E04, pretend entry {e04_entry}, judged {e04_exit}. MEASURED: no E04 record yet.")
    w("- Trust today: well founded on a measured null near 4% and six of ten turns outside the paper, but ten turns at the edge of its breadth mark and a near copy that failed; one more January is the next real evidence.")
    w("")
    w("### Replay 20, short after an Upbit listing red day")
    w("")
    w(f"- No-edge pass rate: {by[18]['label']}, {pct(by[18]['low'])} measured (upper {pct(by[18]['high'])}) in `research_rig/PREREG_20_upbit_listing_short.md`.")
    w(f"- How far past its marks (MEASURED, `docs/research/71_replay_20_upbit_listing_short.md`): per-trade t {t20} against 2.0. 2026 supplied {share26}% of the summed net returns.")
    w("")
    for m in m20:
        w(f"- {m}")
    w("")
    w(f"- Relatives that did not pass (MEASURED): {fam([35, 36, 37, 41, 42])}. Crypto short rules: {fam([15])}.")
    w(f"- Overlap with the source (STATED, plan): \"{viewed20}\" \"{sel20}\" The source's own sample period is UNKNOWN on the repo. The window is wholly inside what the source author looked at.")
    w(f"- Forward log (STATED): no pretend-money log; the desk roster says \"{noshort}\" (`practice/traders/ROSTER.md`). Queue row 49: {q49}; it logs listings, not returns.")
    w("- Trust today: low for a new market; the null was low but the dates were already seen, the rule was picked by its author after viewing results, most of the gain is from one partial year, and there is no US-reachable forward check.")
    w("")
    w("### Plan 75, coin trends with a rising stop")
    w("")
    w(f"- No-edge pass rate: {by[45]['label']}, {pct(by[45]['low'])} (upper {pct(by[45]['high'])}) in the independent audit's made-up worlds (`{PLAN75_RESULT}`).")
    w(f"- MEASURED (`{PLAN75_RESULT}`): all four frozen marks passed, but the rule made money in only {yrs75} calendar years. At 145 bp a side, shown only, net was {harsh75}.")
    w(f"- MEASURED: the independent recompute also passed every mark. An ambiguity about when to start tracking the signal explains about one percentage point of the difference; the two net figures were {spread75} points apart.")
    w(f"- STATED (`{PLAN75_RESULT}`): Binance USDT bars stood in for a US venue, and the coins were picked with hindsight. E10 is being built to log live US venue quotes with pretend money; no forward check yet.")
    w("- INFERENCE, trust today: the thinnest pass by size. The sign changes at higher costs, so measure live costs and order sizes before taking the gain at face value.")
    w("")
    w("## Ideas closed before a return")
    w("")
    w(f"MEASURED from `research_rig/TRIAL_LEDGER.md` and the Done section of `docs/QUEUE.md`, one count per idea (queue rows already in the ledger are not counted twice): {len(closed)} ideas closed before any return was computed.")
    w("")
    for k in sorted(kinds):
        w(f"- {k}: {kinds[k]}")
    w("")
    for c in closed:
        w(f"- {c[0]}: {c[1]}, closed on {c[2]}")
    w("")
    w("What that does to the reading:")
    w("")
    w("- These ideas never had a chance to pass by luck, so they do not raise the luck figure. The denominator for luck is the scored tests, not every idea looked at.")
    w("- They were closed on count, power, cost or data checks, read without returns, so the closing did not pick winners by their results.")
    w("- Closing weak-power ideas early also means the scored tests were, on paper, ones that could detect a real edge. That raises the share of real effects among the passes a little, but no figure for it is measured.")
    w("- It does not remove the earlier choices that shaped each idea (which source, which window, which fund). Those are not counted anywhere and are UNKNOWN.")
    w("")
    w("## What stays UNKNOWN")
    w("")
    w("- The all-mark no-edge rate for every NOMINAL row; only the t or percentile mark was used.")
    w("- How correlated the month-end tests are with each other.")
    w("- Any forward result for E01, E04 or E10; none is on record yet.")
    w("")
    OUT.write_text("\n".join(L).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: all{len(rows)} {lo_all:.3f}-{hi_all:.3f}, pool{len(counted_pool)} {lo_c:.3f}-{hi_c:.3f}, "
          f"p(at least {n_pass}) {tail_lo:.4f}-{tail_hi:.4f}, measured {n_meas}, one-mark {n_one}, nominal {n_nom}, nopass {n_stated0}, closed {len(closed)} {kinds}")


if __name__ == "__main__":
    main()
