"""The newest cards on the owner's screen: the coin sweep (Plans 70 and 71), Plan 73, the E09 forward log, and the
"Running now" strip.

Every figure is read at export time. The sweep and Plan 73 cards read the same pinned summary files that
build_doc152_plan70_search.py, build_doc154_plan71_search.py and build_doc157_plan73_diagnosis.py read, with the
same SHA-256 pins. If a pin no longer matches, or the numbers stop fitting together, the export stops with an error.
If the summary files are not on this computer (they are kept off the repo), the card says so and shows no figure.
The E09 card reads practice/forward/E09_log.json and the E09 card page. The strip reads docs/QUEUE.md. Only labels and
plain wording are written here. Reads no prices and runs nothing.
"""
import datetime
import hashlib
import json
import os
import re
from math import isclose
from zoneinfo import ZoneInfo

import yaml

import build_doc152_plan70_search as B152
import build_doc154_plan71_search as B154
import build_doc157_plan73_diagnosis as B157
import build_doc181_plan75_vault as B181

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MT = ZoneInfo("America/Boise")
D152 = "docs/research/152_plan_70_coin_sweep_search.md"
D154 = "docs/research/154_plan_71_second_coin_grid.md"
D157 = "docs/research/157_plan_73_first_minute_diagnosis.md"
D181 = "docs/research/181_plan_75_heldback_result.md"
E09_LOG = "practice/forward/E09_log.json"
E09_CARD = "practice/traders/E09_overextension_dip_buy.md"
QUEUE = "docs/QUEUE.md"
E10_LOG = "practice/forward/E10_log.json"
E10_CARD = "practice/traders/E10_coin_trend_ratchet.md"
MINUS = "\u2212"


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def bp(x):
    """A fraction as signed basis points with one decimal, true minus sign: 0.0076 -> +76.5 bp."""
    return f"{x * 10000:+.1f} bp".replace("-", MINUS)


def pct(x):
    return f"{x:.2%}"


def mt(utc_text):
    """'2026-11-26T14:20:05Z' -> '2026-11-26 07:20 MT'."""
    t = datetime.datetime.fromisoformat(utc_text.replace("Z", "+00:00")).astimezone(MT)
    return t.strftime("%Y-%m-%d %H:%M") + " MT"


def missing(id_, title, what, links, err):
    return dict(id=id_, title=title, date=None, verdict="Figures not on this computer", tone="unknown",
                basis=f"The summary files are kept off the repo and could not be opened here ({type(err).__name__}). No figure is shown.",
                summary=what, numbers=[], links=links)


# ------------------------------------------------------------------ coin sweep, Plans 70 and 71
def sweep_figures(custody):
    s70 = B152.checked(custody, "sweep_70/search_summary.out", B152.SEARCH_SHA)
    c70 = json.loads(B152.checked(custody, "sweep_70/carry_results.json", B152.CARRY_SHA))
    s71 = B152.checked(custody, "sweep_70/search71_summary.out", B154.SUMMARY_SHA)
    c71 = json.loads(B152.checked(custody, "sweep_70/carry71_results.json", B154.CARRY_SHA))
    _, *r70 = map(json.loads, s70.splitlines())
    h71, *r71 = map(json.loads, s71.splitlines())
    g70 = json.loads(read("research_rig/GRID_70.json"))
    g71 = json.loads(read("research_rig/GRID_71.json"))
    if ([r["rule"] for r in r70] != [r["id"] for r in g70] or [r["rule"] for r in r71] != [r["id"] for r in g71]
            or c70["search_summary_sha256"] != B152.SEARCH_SHA or c71["search71_sha256"] != B154.SUMMARY_SHA):
        raise ValueError("sweep card: the summary files do not match the two checked-in grids")
    fin = sorted((r for r in r70 + r71 if r["finalist_rank"] is not None and r["rule"] in h71["sweep_finalists"]),
                 key=lambda r: h71["sweep_finalists"].index(r["rule"]))
    forecasts = {f["rule"]: f for f in c70["forecasts"] + c71["forecasts"]}
    if ([r["rule"] for r in fin] != h71["sweep_finalists"] or set(forecasts) != set(h71["sweep_finalists"])
            or c70["carried_ids"] or c71["carried_ids"] or any(f["carry"] for f in forecasts.values())):
        raise ValueError("sweep card: finalist or carry list does not fit (expected three finalists, none carried)")
    cfg = yaml.safe_load(read("config/thresholds.yaml"))["replay_70_plan"]["value"]["vault_marks"]
    bar = cfg["min_pre_vault_power"]
    if any(f["probability"] >= bar or not isclose(f["passes"] / f["draws"], f["probability"], abs_tol=5e-5)
           for f in forecasts.values()):
        raise ValueError("sweep card: a carry figure does not fit its bar or its own draw count")
    enough = lambda rows: sum(not r["too_thin"] for r in rows)
    return dict(n70=len(r70), n71=len(r71), ok70=enough(r70), ok71=enough(r71), bar=bar,
                finalists=[(r["rule"], forecasts[r["rule"]]) for r in fin])


def sweep_card(gh, custody=B152.CUSTODY):
    title = "Coin sweep (plans 70, 71)"
    links = [["Plan 70 search", gh + D152], ["Plan 71 search", gh + D154]]
    try:
        f = sweep_figures(custody)
    except (FileNotFoundError, NotADirectoryError) as e:
        return missing("sweep70", title, "The search of written coin rules on 2020 to 2023 prices.", links, e)
    n = f["n70"] + f["n71"]
    fin = f["finalists"]
    names = ", ".join(r for r, _ in fin)
    rows = [[f"Rules written ({f['n70']} in plan 70, {f['n71']} in plan 71)", str(n)],
            [f"Rules with enough trades to judge ({f['ok70']} and {f['ok71']})", str(f["ok70"] + f["ok71"])],
            [f"Finalists: {names}", str(len(fin))]]
    rows += [[f"Chance {r} would pass the sealed years, bar {f['bar']:.0%}", pct(c["probability"])] for r, c in fin]
    rows.append(["Carried to the sealed years", "none"])
    return dict(id="sweep70", title=title, date=None, verdict="No rule carried", tone="fail",
                basis=f"MEASURED in the plan 70 and 71 searches. Figures read from the pinned summary files that build {os.path.basename(D152)} "
                      f"and {os.path.basename(D154)}. The carry bar is STATED in config/thresholds.yaml. The summary files are kept off the repo.",
                summary=(f"{n} coin rules were written and tested on 2020 to 2023 prices. {f['ok70'] + f['ok71']} had enough trades to judge. "
                         f"{len(fin)} made the final cut ({names}). None was carried, because each one's chance of passing on the "
                         f"sealed later years was under the {f['bar']:.0%} bar. The sealed years stay unread. "
                         "Rule 70-102 is followed forward with pretend money as E09."),
                numbers=rows, links=links)


# ------------------------------------------------------------------ Plan 73
CLOCK_WORDS = ((B157.SEARCH, "Saved search result"), (B157.HOURLY, "Coinbase hourly open"),
               (B157.REACH, "One minute after the hour"), (B157.LATE, "Five minutes late"),
               ("coinbase_entry_15m_late", "Fifteen minutes late"), ("coinbase_worst_minute", "Worst price of the minute"))


def plan73_figures(custody):
    # The same pinned files doc 157's builder reads; render() runs its full set of fit checks first.
    B157.render(custody)
    go = json.loads(B157.pinned(custody, "plan73/go.out", B157.GO_SHA, mode=0o600))
    means = go["net_mean_by_clock"]
    if set(means) != {k for k, _ in CLOCK_WORDS} or go["kind"] != "shown_search_dates_not_a_test":
        raise ValueError("plan 73 card: go.out no longer has the six clocks or is not marked as a diagnosis")
    hourly, reach = means[B157.HOURLY] / means[B157.SEARCH], means[B157.REACH] / means[B157.HOURLY]
    if not (0.95 <= hourly <= 1.05 and 0.4 <= reach <= 0.6):
        raise ValueError("plan 73 card: the plain words (same at the open, about half gone a minute later) no longer fit")
    return dict(total=go["search_tickets"], compared=go["compared_tickets"], coins=go["compared_coin_count"],
                reading=go["reading"], bars=[[label, round(means[k] * 10000, 1)] for k, label in CLOCK_WORDS])


def plan73_card(gh, custody=B152.CUSTODY):
    title = "Plan 73: can the gain be reached"
    links = [["Plan 73 result", gh + D157]]
    try:
        f = plan73_figures(custody)
    except (FileNotFoundError, NotADirectoryError) as e:
        return missing("plan73", title, "Repricing rule 71-013's search trades at Coinbase prices someone could have reached.", links, e)
    b = dict(f["bars"])
    return dict(id="plan73", title=title, date=None, verdict="A diagnosis, not a test", tone="info",
                basis=f"MEASURED on the search's own trades. Figures read from the pinned plan 73 summary files that build {os.path.basename(D157)}. "
                      "The summary files are kept off the repo.",
                summary=(f"Rule 71-013's search trades, priced again on Coinbase. {f['compared']} of {f['total']} trades had Coinbase prints "
                         f"at every clock, in {f['coins']} coins. The average gain a trade was about the same at the hourly open, "
                         f"but about half was gone one minute later. These are trades the search already picked, so this is a diagnosis, "
                         f"not a test, and no money follows."),
                numbers=[[f"Trades with Coinbase prints at every clock, of {f['total']}", str(f["compared"])],
                         ["Coins in those trades", str(f["coins"])]],
                bars=dict(unit="bp", label="Average net gain a trade, in hundredths of a percent (bp)", rows=f["bars"]),
                links=links)


# ------------------------------------------------------------------ Plan 75, the sealed years
P75_RUN, P75_RECOMPUTE = list(B181.PINS)[:2]      # the official run's output and the blind recompute's result, with doc 181's pins


def p75_pinned(path, pin):
    blob = open(path, "rb").read()
    if hashlib.sha256(blob).hexdigest() != pin:
        raise ValueError(f"plan 75 card: pinned file differs: {os.path.basename(path)}")
    return blob.decode("utf-8")


def plan75_figures(run_path=P75_RUN, recompute_path=P75_RECOMPUTE):
    lines = p75_pinned(run_path, B181.PINS[P75_RUN]).splitlines()
    rec = json.loads(p75_pinned(recompute_path, B181.PINS[P75_RECOMPUTE]))
    tag = lambda t: [json.loads(l[len(t) + 1:]) for l in lines if l.startswith(t + " ")]
    main, harsh, marks, adm = tag("VAULT_MAIN"), tag("VAULT_HARSH_SHOWN_ONLY"), tag("VAULT_MARKS"), tag("ADMISSION_COIN_DAYS")
    result = [l.split(" ", 1)[1] for l in lines if l.startswith("VAULT_RESULT ")]
    if not (len(main) == len(harsh) == len(marks) == len(adm) == 1 and result == ["PASS"]):
        raise ValueError("plan 75 card: the run output no longer has one main line, one harsh line, one marks line and a PASS")
    main, harsh, marks, adm = main[0], harsh[0], marks[0], adm[0]
    p, h, r75 = main["primary"], harsh["primary"], rec["75_bp_per_side"]
    doc = read(D181)
    first, last = re.search(r"The sealed stretch (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", doc).groups()
    after_day = re.search(r"From the (\d{4}-\d{2}-\d{2}) close, after the paper's sample", doc)[1]
    days = (datetime.date.fromisoformat(last) - datetime.date.fromisoformat(first)).days + 1
    coins, rest = divmod(sum(adm.values()), days)
    y, legs = p["years"], sorted({b["book"] for b in tag("VAULT_SHOWN_ONLY") if b["book"].isdigit()}, key=int)
    # The plain words on the card must stay true; stop if the figures stop fitting them.
    if not (len(marks) == 4 and all(marks.values()) and rest == 0 and set(y) == {"2024", "2025", "2026"}
            and y["2024"] > 0 > y["2025"] and y["2026"] < 0 and h["net"] < 0 < p["net"] and p["net"] > main["btc"]["matched_net"]
            and rec["75_bp_per_side"]["result"] == "PASS" and all(rec["75_bp_per_side"]["marks"].values())
            and isclose(main["cost_per_side"], 0.0075) and harsh["cost_per_side"] > main["cost_per_side"]):
        raise ValueError("plan 75 card: the figures no longer fit the card's plain words")
    return dict(first=first, last=last, after_day=after_day, coins=coins, legs=legs, n_marks=len(marks),
                cost=main["cost_per_side"], harsh_cost=harsh["cost_per_side"], net=p["net"], btc=main["btc"]["matched_net"],
                drawdown=p["drawdown"], after=main["after_paper_net"], hold=p["hold_days"]["median"], fills=p["fill_count"],
                blind=r75["primary_net"], harsh_net=h["net"], years=y)


WORDS = {3: "three", 4: "four", 5: "five"}


def signed(x, d=2):
    return f"{100 * x:+.{d}f}%".replace("-", MINUS)


def plan75_card(gh, run_path=P75_RUN, recompute_path=P75_RECOMPUTE):
    title = "Plan 75: coin trend rule, the sealed years"
    links = [["Plan 75 result", gh + D181]]
    try:
        f = plan75_figures(run_path, recompute_path)
    except (FileNotFoundError, NotADirectoryError) as e:
        return missing("plan75", title, "A coin trend rule run once on years it had never seen.", links, e)
    hc = lambda c: f"{c * 10000:g} hundredths of a percent a side"
    legs = ", ".join(f["legs"][:-1]) + " or " + f["legs"][-1]
    yr = f["years"]
    return dict(id="plan75", title=title, date=None, verdict="Passed, thinly", tone="mixed",
                basis=(f"MEASURED in the one run on the sealed years. Figures read from the pinned files that build {os.path.basename(D181)}: "
                       f"{os.path.basename(run_path)} and {os.path.basename(recompute_path)}. They are kept off the repo."),
                summary=(f"Buys one of {f['coins']} large coins when its daily close reaches a {legs} day high, and holds until the close drops under "
                         f"a stop that only moves up. The typical hold was {f['hold']:g} days. "
                         f"It was run once on {f['first']} to {f['last']}, years it had never seen, and met all {WORDS[f['n_marks']]} marks set beforehand. "
                         f"All the gain came in 2024, and at a harsher cost of {hc(f['harsh_cost'])} it loses money. "
                         f"It earns a pretend-money forward card (E10), not real money."),
                numbers=[[f"Net after costs ({hc(f['cost'])})", signed(f["net"])],
                         ["Bitcoin held at the same risk, after costs", signed(f["btc"])],
                         ["Largest fall from a high", f"{100 * f['drawdown']:.2f}%"],
                         [f"Since the paper's sample ended ({f['after_day']})", signed(f["after"])],
                         ["Median hold", f"{f['hold']:g} days"],
                         ["Fills (buys and sells)", f"{f['fills']:,}"],
                         ["Second version, built blind from the plan: net", signed(f["blind"])]],
                bars=dict(unit="%", label=f"Net after costs by year, in percent. The last bar is the whole stretch at {hc(f['harsh_cost'])}.",
                          rows=[["2024", round(100 * yr["2024"], 1)], ["2025", round(100 * yr["2025"], 1)],
                                ["2026, to October", round(100 * yr["2026"], 1)],
                                ["Whole stretch, harsher cost", round(100 * f["harsh_net"], 1)]]),
                links=links)


# ------------------------------------------------------------------ E09 forward log
def queue_step(row):
    """The Current step cell of a row in the Running now table of docs/QUEUE.md."""
    for cells in queue_rows():
        if cells[0] == row:
            return cells[-1]
    raise ValueError(f"queue row {row} not found in the Running now table")


STOP_RE = re.compile(r"^STOPPED (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2} [AP]M MT) on data terms \(Coinbase market data\)\. "
                     r"Closed unjudged;.*?Replaced by (E\d+) \(queue (\d+)\)\.")


def stopped_on_terms(row, card_name):
    """A forward card stopped on data terms: read the stop time and the replacement from its queue row, refuse otherwise."""
    m = STOP_RE.search(queue_step(row))
    if not m:
        raise ValueError(f"{card_name} card: queue row {row} no longer starts with STOPPED on data terms and a replacement")
    when, new, new_row = m.groups()
    reg = queue_step(new_row)
    if not reg.startswith("Registered ") or "Binance.US data only" not in dict((c[0], c[1]) for c in queue_rows())[new_row]:
        raise ValueError(f"{card_name} card: replacement {new} (queue {new_row}) is not a registered Binance.US-only row")
    return when, new


def stop_sentence(when, new):
    return (f"Stopped {when} because the price source's terms bar this use. Closed unjudged; nothing is scored. "
            f"Replaced by {new} on Binance.US data.")


E09_ROW = "114"


def e09_card(gh):
    card = read(E09_CARD)
    what = re.search(r"^# E09: Forward log of rule 70-102, (.+)$", card, re.M)[1]
    when, new = stopped_on_terms(E09_ROW, "E09")
    links = [["E09 card", gh + E09_CARD], ["Log counts", gh + E09_LOG]]
    path = os.path.join(ROOT, E09_LOG)
    log = json.load(open(path)) if os.path.exists(path) else None
    nums = []
    if log and log.get("started"):
        if not (isinstance(log.get("recorded"), int) and log["recorded"] >= 0):
            raise ValueError("E09 card: the log counts do not fit")
        nums = [["Wake-ups recorded before the stop", f"{log['recorded']:,}"]]
    return dict(id="e09", title="E09: dip-buy rule, stopped on data terms", date=None, links=links,
                verdict="Stopped, closed unjudged", tone="unknown", numbers=nums,
                basis=(f"STATED in the queue page, row {E09_ROW}. " + (f"The wake-up count is read from {os.path.basename(E09_LOG)}. " if nums else "")
                       + "Pretend money, no real account."),
                summary=f"Followed rule 70-102, {what}, forward on live prices with pretend money. " + stop_sentence(when, new))

# ------------------------------------------------------------------ E10 forward log
E10_VENUES = (("coinbase", "Coinbase"), ("binance_us", "Binance.US"))
E10_PLACE = {"delayed_sells", "fills", "minimum_unknown", "orders", "pair_unavailable", "queued_sells", "quote_missing",
             "under", "venue_unavailable", "void_buys"}
E10_VENUE_KEYS = {"all_in_cost_by_side", "block_reason", "coin_candle_page_failures", "coin_quote_page_failures",
                  "flat_reference_bp", "follow_observations", "half_spread_by_coin", "label", "late_wakes", "missed_wakes",
                  "placeability", "status", "unavailable_observations", "void_wakes", "wakes"}
E10_STATES = {"NOT_STARTED", "STARTED", "BLOCKED", "NO_DECISION_FEED"}


def e10_checked(log):
    """Refuse a log whose shape is not the one forward_e10.py publish writes. Returns it unchanged."""
    def need(ok, what):
        if not ok:
            raise ValueError(f"E10 card: the log does not fit: {what}")
    count = lambda x: isinstance(x, int) and not isinstance(x, bool) and x >= 0
    need(isinstance(log, dict) and set(log) == {"card", "coinbase", "binance_us", "coinbase_vs_second_feed"}, "top-level keys")
    need(log["card"] == "E10" and log["coinbase_vs_second_feed"] == "NOT_MEASURED", "card name or feed comparison")
    for key, _ in E10_VENUES:
        v = log[key]
        need(isinstance(v, dict) and set(v) == E10_VENUE_KEYS, f"{key} keys")
        need(v["status"] in E10_STATES and (v["status"] == "BLOCKED") == isinstance(v["block_reason"], str), f"{key} status")
        need(all(count(v[k]) for k in ("wakes", "void_wakes", "missed_wakes", "late_wakes", "follow_observations",
                                       "unavailable_observations", "coin_quote_page_failures", "coin_candle_page_failures")), f"{key} counts")
        need(v["void_wakes"] == v["missed_wakes"] + v["late_wakes"], f"{key} void wakes")
        need(isinstance(v["flat_reference_bp"], (int, float)) and isclose(v["flat_reference_bp"], 75.0), f"{key} cost line")
        need(set(v["placeability"]) == {"main", "shown"}, f"{key} books")
        for book in v["placeability"].values():
            need(set(book) == E10_PLACE and all(count(x) for x in book.values()) and book["fills"] <= book["orders"], f"{key} order counts")
        cost = v["all_in_cost_by_side"]
        need(set(cost) == {"buy", "sell"}, f"{key} cost sides")
        for c in cost.values():
            need(set(c) == {"n", "median_bp", "p90_bp", "median_minus_flat_bp", "p90_minus_flat_bp"} and count(c["n"]), f"{key} cost keys")
            need(all((c[k] is None) == (c["n"] == 0) for k in ("median_bp", "p90_bp", "median_minus_flat_bp", "p90_minus_flat_bp")), f"{key} cost values")
        need(cost["buy"]["n"] + cost["sell"]["n"] == v["placeability"]["main"]["fills"], f"{key} costs against fills")
        if v["status"] == "NOT_STARTED":
            need(v["wakes"] == v["void_wakes"] == v["placeability"]["main"]["orders"] == 0, f"{key} counts before start")
    states = {log[k]["status"] for k, _ in E10_VENUES}
    need((log["coinbase"]["status"] == "NOT_STARTED") == (log["binance_us"]["status"] == "NOT_STARTED"), "one venue not started")
    need(log["coinbase"]["status"] != "NO_DECISION_FEED" and (log["binance_us"]["status"] != "NO_DECISION_FEED"
         or log["coinbase"]["status"] == "BLOCKED"), "decision feed state")
    return log


E10_ROW = "131"


def e10_card(gh, log_path=None):
    card = read(E10_CARD)
    coins = re.search(r"Read the (\d+) Plan 70 coins", card)[1]
    legs = re.search(r"Use the Plan 75 primary book for decisions: (\d+)-, (\d+)- and (\d+)-day legs", card).groups()
    when, new = stopped_on_terms(E10_ROW, "E10")
    log = e10_checked(json.load(open(log_path or os.path.join(ROOT, E10_LOG))))
    wakes = log["coinbase"]["wakes"]
    links = [["E10 card", gh + E10_CARD], ["Log counts", gh + E10_LOG]]
    return dict(id="e10", title="E10: coin trend rule, stopped on data terms", date=None, links=links,
                verdict="Stopped, closed unjudged", tone="unknown",
                numbers=[["Wakes recorded before the stop", f"{wakes:,}"]],
                basis=(f"STATED in the queue page, row {E10_ROW}. The wake count is read from {os.path.basename(E10_LOG)}. "
                       "Pretend money, no account at any venue."),
                summary=(f"Followed the Plan 75 rule forward with pretend money: buy one of {coins} large coins when its daily close "
                         f"reaches a {legs[0]}, {legs[1]} or {legs[2]} day high, sell when the close drops under a stop that only moves up. "
                         + stop_sentence(when, new)))

# ------------------------------------------------------------------ Running now strip
def first_sentence(text):
    text = re.sub(r"\s*\((?:[^()]*`[^()]*)\)", "", text)                       # parentheses that only point at files
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text).replace("`", "").replace("**", "").strip()
    m = re.search(r"(?<!\bal)(?<!\be\.g)(?<!\bi\.e)\.(?=\s+[A-Z(]|$)", text)
    return (text[:m.start() + 1] if m else text.rstrip(".") + ".").strip()


def queue_rows():
    """Cells of each row of the "Running now" table in docs/QUEUE.md."""
    body = re.search(r"^## Running now[ \t]*\n(.*?)(?=^## |\Z)", read(QUEUE), re.M | re.S)
    if not body:
        raise ValueError("running strip: docs/QUEUE.md has no Running now section")
    lines = [l for l in body[1].splitlines() if l.startswith("|")]
    if len(lines) < 3 or [c.strip() for c in lines[0].strip("|").split("|")][:2] != ["#", "What"]:
        raise ValueError("running strip: the Running now table no longer starts with # and What")
    return [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[2:]]


def row_state(step):
    """A short plain state for a row whose step says it is stopped or only registered; None otherwise."""
    m = re.match(r"STOPPED (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(?: [AP]M)? MT)( on data terms)?", step)
    if m:
        return f"Stopped {m[1]}" + (" on data terms" if m[2] else "")
    m = re.match(r"PAUSED (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(?: [AP]M)? MT)", step)
    if m:
        return f"Paused {m[1]}"
    m = re.match(r"(?:ON HOLD|HOLD) (?:since )?(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(?: [AP]M)? MT)", step)
    if m:
        return f"On hold since {m[1]}"
    m = re.match(r"(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(?: [AP]M)? MT): stopped\b", step)
    if m:
        return f"Stopped {m[1]}"
    m = re.match(r"Registered (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}(?: [AP]M)? MT)\.", step)
    if m:
        return f"Registered {m[1]}, not started"
    return None


def practice_pause():
    """The practice desk's pause, from its row in the Running now table: {"when": ...} or None when the row does not say PAUSED."""
    rows = [c for c in queue_rows() if c[0] == "-" and "practice desk" in c[1]]
    if len(rows) != 1:
        raise ValueError("practice pause: the practice desk row is not in the Running now table once")
    m = re.match(r"PAUSED (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2} [AP]M MT) by the lead agent", rows[0][-1])
    return dict(when=m[1]) if m else None


def running_now():
    """Rows of the "Running now" table in docs/QUEUE.md: [row number, first sentence of What, state or None]."""
    return [[c[0], first_sentence(c[1]), row_state(c[-1]) if len(c) >= 3 else None] for c in queue_rows()]

def cards(gh):
    return [plan75_card(gh), sweep_card(gh), plan73_card(gh), e09_card(gh), e10_card(gh)]
