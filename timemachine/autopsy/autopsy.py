"""Decision autopsy of the finished time machine plans TM01 to TM04: every written reason, read and joined to what happened.

An after-the-fact look at finished and already scored tests. Not a test: no pass mark, it changes no result.

Reads, read only:
  - session folders TM01-*, TM02-*, TM03-*, TM04-*, TWIN-TM01-*, TWIN-TM02-* under the run folder (never TM06 or VOID);
  - 1-minute prices from the recorded tape (sqlite, opened read only, kept in memory);
  - categories.md (the category list), classify.py (the text rules), labels_by_hand.jsonl (the analyst's labels, by id),
    hand_checks.json (blind sample ids, relabel and rule checks, contradiction check, hand verdicts), quotes.json.
Writes the results file (default autopsy_results.json next to this script). No answer text is written except the quotes.

Run from the repo root:  nice -n 10 python3 timemachine/autopsy/autopsy.py [--runs DIR] [--tape FILE] [--out FILE]
Defaults come from settings.py (environment DT_AUTOPSY_RUNS, DT_AUTOPSY_TAPE, DT_AUTOPSY_OUT).
"""
import argparse, json, os, re, glob, collections, datetime, sys
import settings

_ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
_ap.add_argument("--runs", default=settings.RUNS, help="folder holding the session folders (default %(default)s)")
_ap.add_argument("--tape", default=settings.TAPE, help="recorded tape sqlite file (default %(default)s)")
_ap.add_argument("--out", default=settings.OUT, help="results file to write (default %(default)s)")
_args = _ap.parse_args()
settings.RUNS, settings.TAPE, settings.OUT = _args.runs, _args.tape, _args.out
if not os.path.isdir(settings.RUNS):
    sys.exit(f"run folder not found: {settings.RUNS}")
if not os.path.exists(settings.TAPE):
    sys.exit(f"tape not found: {settings.TAPE}")

from load import sessions, parse_sid, crypto_texts, crypto_sell_orders, dial_texts, basket_texts
from classify import classify_buy, classify_sell, classify_dial, classify_basket, flags_buy
from core import SMALL, H24, H48, H120, D7, mean, med, share, r6, cell, group, cid_pick, fill_spread, round_trips, trip_table, check_label_ids, shared_runs
import prices as P

HERE = settings.HERE

def jl(name):
    p = os.path.join(HERE, name)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []

HC = json.load(open(os.path.join(HERE, "hand_checks.json")))

# ------------------------------------------------------------------ labels
labels = jl("labels_by_hand.jsonl")
hand = {r["id"]: r["label"] for r in labels}

def place(label, how, _id):
    if label is not None:
        return label, how
    if _id in hand:
        return hand[_id], "hand"
    return "UNCLEAR", "unclear"

# ------------------------------------------------------------------ counts and texts
buys_txt = [r for r in crypto_texts() if r["kind"] == "buy"]
sell_actions_txt = [r for r in crypto_texts() if r["kind"] == "sell"]
sell_orders = crypto_sell_orders()
dials = dial_texts()
baskets = basket_texts()

known_ids = [r["id"] for r in buys_txt + sell_actions_txt + sell_orders + dials + baskets]
missing_label_ids = check_label_ids(labels, known_ids)
check_ids = [r["id"] for k in ("hand_relabel_blind", "rulecheck_sample1", "rulecheck_sample2", "contradiction_check") for r in HC[k]] + HC["blind_sample"]["ids"]
missing_check_ids = check_label_ids([dict(id=i) for i in check_ids], known_ids)
for i in missing_label_ids:
    print(f"label id not found in the run folders: {i}")
for i in missing_check_ids:
    print(f"hand-check id not found in the run folders: {i}")
how_counts = collections.Counter()
buy_cat = {}
for r in buys_txt:
    lab, how = place(*classify_buy(r["reason"], r["thesis"]), r["id"])
    if how == "rule_thesis":
        how = "rule"
    r["cat"] = lab; r["how"] = how; buy_cat[r["id"]] = lab
    r.update(flags_buy(r["reason"], r["thesis"]))
    how_counts[("buy", how)] += 1
for r in sell_orders:
    lab, how = place(*classify_sell(r["reason"]), r["id"])
    r["cat"] = lab; r["how"] = how; how_counts[("sell", how)] += 1
    r["written"] = not r["reason"].startswith("Exit set in pick")
    r["exit_before_stop"] = bool(re.search(r"before (the|its|my)?.{0,12}stop|rather than wait|exit first|exiting above the", r["reason"].lower()))
for r in dials:
    if r["direction"] == "same":
        r["cat"] = None; continue
    lab, how = place(*classify_dial(r["reason"]), r["id"])
    r["cat"] = lab; r["how"] = how; how_counts[("dial", how)] += 1
for r in baskets:
    lab, how = place(*classify_basket(r["reason"], r["kind"]), r["id"])
    r["cat"] = lab; r["how"] = how; how_counts[("basket", how)] += 1

out = dict(made_by="autopsy.py", made_utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           note="After-the-fact look at finished tests TM01 to TM04. Not a test. No pass mark. Anything here is a hypothesis for a new test on months not yet traded.",
           small_cell_rule=f"cells with fewer than {SMALL} items are flagged small=true and no conclusion is drawn from them")
out["blind_sample"] = dict(texts=len(HC["blind_sample"]["ids"]), note="seed 59, read before categories.md was written; no numeric confidence was seen in it. Ids in hand_checks.json")
out["labels_file"] = dict(rows=len(labels), ids_not_found_in_run_folders=missing_label_ids, check_ids_not_found_in_run_folders=missing_check_ids)
out["classification"] = {f"{t}_{h}": n for (t, h), n in sorted(how_counts.items())}

# answers per plan and model
cnt = collections.defaultdict(lambda: collections.Counter())
for plan in ("TM01", "TM02", "TM03", "TM04"):
    for d in sessions(plan):
        sid = os.path.basename(d); _, model, _ = parse_sid(sid)
        prog = json.load(open(d + "/progress.json"))
        c = cnt[(plan, model)]
        c["sessions"] += 1
        for s in prog["steps"]:
            c["answers"] += 1
            if plan in ("TM01", "TM02"):
                if s.get("pick"):
                    c["picks"] += 1
                    for a in s["pick"].get("actions", []):
                        c["buy_actions" if a.get("side") == "buy" else "sell_actions"] += 1
                else:
                    c["no_pick"] += 1
            else:
                if s.get("changed"):
                    c["changes"] += 1
        if plan in ("TM01", "TM02"):
            res = json.load(open(d + "/result.json"))
            for o in res["summary"]["orders"]:
                if o["status"] == "filled":
                    c["filled_buys" if o["side"] == "buy" else "filled_sells"] += 1
for r in dials:
    if r["direction"] != "same":
        cnt[("TM03", r["model"])][r["direction"] + "s"] += 1
for r in baskets:
    cnt[("TM04", r["model"])][f"reasons_{r['kind']}"] += 1
out["counts"] = {f"{p}|{m}": dict(c) for (p, m), c in sorted(cnt.items())}
tot = collections.defaultdict(collections.Counter)
for (p, m), c in cnt.items():
    tot[p].update(c)
out["counts_by_plan"] = {p: dict(c) for p, c in sorted(tot.items())}

# ------------------------------------------------------------------ crypto: orders, round trips, prices
picks_by = {}       # (sid, pick_id) -> pick obj
for plan in ("TM01", "TM02"):
    for d in sessions(plan):
        sid = os.path.basename(d)
        for s in json.load(open(d + "/progress.json"))["steps"]:
            if s.get("pick"):
                picks_by[(sid, s.get("pick_id"))] = s["pick"]

buy_by_id = {r["id"]: r for r in buys_txt}
sell_by_id = {r["id"]: r for r in sell_orders}
base_cache = {}

def base_rates(sym, start, end):
    key = (sym, start, end)
    if key in base_cache:
        return base_cache[key]
    f24, f120, b24, b7 = [], [], [], []
    t = start
    while t < end:
        f24.append(P.ret(sym, t, t + H24)); f120.append(P.ret(sym, t, t + H120))
        b24.append(P.ret(sym, t - H24, t)); b7.append(P.ret(sym, t - D7, t))
        t += 3600
    base_cache[key] = dict(f24=mean(f24), f120=mean(f120), b24=mean(b24), b7=mean(b7), n_hours=len(f24))
    return base_cache[key]

buys, sells, trips, open_at_end = [], [], [], []
twin_by_ai = collections.defaultdict(list)   # ai buy id -> list of twin (f24, f120, b24, b7)
anomalies = []
for plan in ("TM01", "TM02"):
    for d in sessions(plan):
        sid = os.path.basename(d); _, model, month = parse_sid(sid)
        res = json.load(open(d + "/result.json"))
        sess = res["session"]; cfg = res["config"]
        hs = cfg["tm_crypto_half_spread_bps"] / 1e4
        w0, w1 = P.ts(sess["window"]["start"] + "T00:00:00"), P.ts(sess["end_utc"])
        orders = [o for o in res["summary"]["orders"] if o["status"] == "filled"]
        for o in orders:
            t = P.ts(o["filled_utc"]); sym = o["symbol"]
            br = base_rates(sym, w0, w1)
            spread = fill_spread(o["side"], o["qty"], o["fill_price"], hs)
            row = dict(sid=sid, plan=plan, model=model, month=month, sym=sym, t=t, utc=o["filled_utc"], side=o["side"], fill=o["fill_price"],
                       qty=o["qty"], fee=o.get("fee_added_usd") or 0.0, spread=spread, cid=o["client_order_id"], reason=o.get("reason") or "",
                       f24=P.ret(sym, t, t + H24), f48=P.ret(sym, t, t + H48), f120=P.ret(sym, t, t + H120),
                       b24=P.ret(sym, t - H24, t), b7=P.ret(sym, t - D7, t), base=br)
            if o["side"] == "buy":
                pid, idx = cid_pick(o["client_order_id"])
                aid = f"{sid}|{pid}|{idx}"
                row["aid"] = aid; row["pick_id"] = pid
                tx = buy_by_id.get(aid)
                if tx is None:
                    anomalies.append(f"{sid}: filled buy {o['client_order_id']} has no matching written buy action")
                    row["cat"] = "UNCLEAR"
                else:
                    row["cat"] = tx["cat"]; row["flags"] = {k: tx[k] for k in ("states_target", "states_stop_in_text", "cites_headline", "size_or_confidence")}
                    row["exits"] = tx["exits"]
                buys.append(row)
            else:
                sr = sell_by_id.get(f"{sid}|{o['order_id']}")
                row["cat"] = sr["cat"] if sr else "UNCLEAR"; row["written"] = sr["written"] if sr else None
                row["exit_before_stop"] = sr["exit_before_stop"] if sr else None
                m = re.match(r"Exit set in pick (\S+?):", row["reason"])
                row["exit_pick"] = m.group(1) if m else None
                sells.append(row)
        # round trips from the desk's own closed list
        my_buys = [b for b in buys if b["sid"] == sid]; my_sells = [s for s in sells if s["sid"] == sid]
        closed = [dict(symbol=c["symbol"], opened_ts=P.ts(c["opened_utc"]), closed_ts=P.ts(c["closed_utc"]), gain_usd=c["gain_usd"], gain_pct=c["gain_pct"]) for c in res["summary"]["closed"]]
        for t_ in round_trips(closed, my_buys, my_sells):
            t_.update(sid=sid, plan=plan, model=model, month=month)
            trips.append(t_)
        tr = res["summary"]["traders"][0]
        for p in tr.get("positions") or []:
            open_at_end.append(dict(sid=sid, sym=p.get("symbol")))

# twins: buys mapped to the AI buy they copy (same wake, same action index)
twin_sessions_used = 0
for plan in ("TM01", "TM02"):
    for d in sorted(glob.glob(f"{settings.RUNS}/TWIN-{plan}-*")):
        if not os.path.exists(d + "/result.json"):
            continue
        b = os.path.basename(d)
        ai_sid = re.sub(r"^TWIN-", "", re.sub(r"-s\d+$", "", b))
        res = json.load(open(d + "/result.json"))
        twin_sessions_used += 1
        for o in res["summary"]["orders"]:
            if o["side"] != "buy" or o["status"] != "filled":
                continue
            pid, idx = cid_pick(o["client_order_id"])
            t = P.ts(o["filled_utc"]); sym = o["symbol"]
            twin_by_ai[f"{ai_sid}|{pid}|{idx}"].append((P.ret(sym, t, t + H24), P.ret(sym, t, t + H120), P.ret(sym, t - H24, t), P.ret(sym, t - D7, t)))
out["twins"] = dict(twin_sessions_read=twin_sessions_used, ai_buys_with_twins=sum(1 for b in buys if b.get("aid") in twin_by_ai))

# ------------------------------------------------------------------ round-trip tables
rt = dict(pooled=trip_table(trips), open_at_end=len(open_at_end))
rt["by_plan"] = {k: trip_table(v) for k, v in sorted(group(trips, lambda r: r["plan"]).items())}
rt["by_model"] = {k: trip_table(v) for k, v in sorted(group(trips, lambda r: r["model"]).items())}
rt["by_plan_model"] = {k: trip_table(v) for k, v in sorted(group(trips, lambda r: r["plan"] + "|" + r["model"]).items())}
rt["oct_nov_net_usd"] = r6(sum(t["gain"] for t in trips if t["month"] in ("2026-10", "2026-11")))
rt["by_month"] = {k: trip_table(v) for k, v in sorted(group(trips, lambda r: r["month"]).items())}
rt["by_entry_cat"] = {k: trip_table(v) for k, v in sorted(group(trips, lambda r: r["entry_cat"]).items())}
rt["by_exit_cat"] = {k: trip_table(v) for k, v in sorted(group(trips, lambda r: r["exit_cat"]).items())}
out["round_trips"] = rt

# ------------------------------------------------------------------ buys: after and before, against base and twins
def buy_table(rows):
    ex = lambda k: [None if (b[k] is None or b["base"][k] is None) else b[k] - b["base"][k] for b in rows]
    tw24 = [mean([x[0] for x in twin_by_ai[b["aid"]]]) for b in rows if b.get("aid") in twin_by_ai]
    tw120 = [mean([x[1] for x in twin_by_ai[b["aid"]]]) for b in rows if b.get("aid") in twin_by_ai]
    ai24 = [b["f24"] for b in rows if b.get("aid") in twin_by_ai]
    ai120 = [b["f120"] for b in rows if b.get("aid") in twin_by_ai]
    return dict(n=len(rows), small=len(rows) < SMALL,
                after_24h=cell([b["f24"] for b in rows]), after_120h=cell([b["f120"] for b in rows]),
                after_24h_minus_base=cell(ex("f24")), after_120h_minus_base=cell(ex("f120")),
                base_24h_mean=r6(mean([b["base"]["f24"] for b in rows])), base_120h_mean=r6(mean([b["base"]["f120"] for b in rows])),
                before_24h=cell([b["b24"] for b in rows]), before_7d=cell([b["b7"] for b in rows]),
                before_24h_minus_base=cell(ex("b24")), before_7d_minus_base=cell(ex("b7")),
                twins=dict(n_ai_buys_with_twins=len(ai24), ai_after_24h_mean=r6(mean(ai24)), twin_after_24h_mean=r6(mean(tw24)),
                           ai_after_120h_mean=r6(mean(ai120)), twin_after_120h_mean=r6(mean(tw120)), small=len(ai24) < SMALL))

bt = dict(pooled=buy_table(buys))
bt["by_plan"] = {k: buy_table(v) for k, v in sorted(group(buys, lambda r: r["plan"]).items())}
bt["by_model"] = {k: buy_table(v) for k, v in sorted(group(buys, lambda r: r["model"]).items())}
bt["by_cat"] = {k: buy_table(v) for k, v in sorted(group(buys, lambda r: r["cat"]).items())}
bt["by_plan_cat"] = {k: buy_table(v) for k, v in sorted(group(buys, lambda r: r["plan"] + "|" + r["cat"]).items())}
# broad groups: after a rise vs after a fall vs headline/other
broad = {"B_BREAKOUT": "after_rise", "B_PULLBACK": "after_rise", "B_RELSTRENGTH": "after_rise", "B_SUPPORT": "after_fall",
         "B_REVERSAL": "after_fall", "B_HEADLINE": "headline", "B_INDICATOR": "other", "B_OTHER": "other", "UNCLEAR": "other"}
bt["by_broad"] = {k: buy_table(v) for k, v in sorted(group(buys, lambda r: broad.get(r["cat"], "other")).items())}
fl = {}
for f in ("states_target", "states_stop_in_text", "cites_headline", "size_or_confidence"):
    fl[f] = {str(v): buy_table(rows) for v, rows in group([b for b in buys if b.get("flags")], lambda r: r["flags"][f]).items()}
    fl[f]["share_yes"] = r6(share([b["flags"][f] for b in buys if b.get("flags")]))
bt["by_flag"] = fl
tm02 = [b for b in buys if b["plan"] == "TM02" and b.get("flags")]
bt["tm02_by_cites_headline"] = {str(v): buy_table(rows) for v, rows in group(tm02, lambda r: r["flags"]["cites_headline"]).items()}
bt["tm02_by_cites_headline"]["share_yes"] = r6(share([b["flags"]["cites_headline"] for b in tm02]))
tm02_trips = [t for t in trips if t["plan"] == "TM02" and t.get("entry_flags")]
bt["tm02_trips_by_cites_headline"] = {str(v): trip_table(rows) for v, rows in group(tm02_trips, lambda r: r["entry_flags"]["cites_headline"]).items()}
# stated exit plan as numbers in the pick
ex_set = [b for b in buys if b.get("exits") is not None]
bt["exit_fields_at_entry"] = dict(n=len(ex_set), with_stop=sum(1 for b in ex_set if any(e.get("stop") for e in b["exits"])),
                                  with_target=sum(1 for b in ex_set if any(e.get("target") for e in b["exits"])),
                                  with_time=sum(1 for b in ex_set if any(e.get("by_utc") for e in b["exits"])))
dist = []
tdist = []
for b in ex_set:
    for e in b["exits"]:
        if e.get("stop"):
            dist.append((b["fill"] - e["stop"]) / b["fill"])
        if e.get("target"):
            tdist.append((e["target"] - b["fill"]) / b["fill"])
bt["exit_fields_at_entry"].update(stop_distance=cell(dist), target_distance=cell(tdist))
out["buys"] = bt

# ------------------------------------------------------------------ sells
def sell_table(rows):
    ex = lambda k: [None if (s[k] is None or s["base"]["f24"] is None) else s[k] - (s["base"]["f24"] if k == "f24" else 2 * s["base"]["f24"]) for s in rows]
    return dict(n=len(rows), small=len(rows) < SMALL,
                closed_trip_at_loss=sum(1 for s in rows if s.get("trip_gain") is not None and s["trip_gain"] <= 0),
                closed_trip_known=sum(1 for s in rows if s.get("trip_gain") is not None),
                after_24h=cell([s["f24"] for s in rows]), after_48h=cell([s["f48"] for s in rows]),
                after_24h_minus_base=cell(ex("f24")), after_48h_minus_base=cell(ex("f48")),
                before_24h=cell([s["b24"] for s in rows]))
st = dict(pooled=sell_table(sells))
st["by_cat"] = {k: sell_table(v) for k, v in sorted(group(sells, lambda r: r["cat"]).items())}
st["by_plan_cat"] = {k: sell_table(v) for k, v in sorted(group(sells, lambda r: r["plan"] + "|" + r["cat"]).items())}
st["stop_at_loss"] = sell_table([s for s in sells if s["cat"] == "S_STOP" and s.get("trip_gain") is not None and s["trip_gain"] <= 0])
st["stop_at_gain"] = sell_table([s for s in sells if s["cat"] == "S_STOP" and s.get("trip_gain") is not None and s["trip_gain"] > 0])
st["written_sells"] = dict(n=sum(1 for s in sells if s["written"]), exit_before_stop=sum(1 for s in sells if s["written"] and s["exit_before_stop"]))
out["sells"] = st

# ------------------------------------------------------------------ exit plan followed
def plan_class(t):
    if t["exit_written"]:
        return "sold_by_hand"
    if t["exit_pick"] is None:
        return "unknown"
    if t["exit_pick"] == t["entry_pick"]:
        return "entry_plan_as_set"
    return "revised_in_later_pick"

pf = collections.defaultdict(list)
moves = collections.Counter()
for t in trips:
    c = plan_class(t); pf[c].append(t)
    if c == "revised_in_later_pick" and t["entry_exits"]:
        later = picks_by.get((t["sid"], t["exit_pick"]))
        e0 = next((e for e in t["entry_exits"] if e.get("stop")), None)
        e1 = next((e for e in (later or {}).get("exits", []) if e.get("symbol") == t["sym"] and e.get("stop")), None)
        if e0 and e1:
            moves["stop_raised" if e1["stop"] > e0["stop"] else ("stop_lowered" if e1["stop"] < e0["stop"] else "stop_same")] += 1
        else:
            moves["stop_unknown"] += 1
out["exit_plan"] = dict({k: trip_table(v) for k, v in sorted(pf.items())}, stop_moves_in_revised=dict(moves),
                        note="entry_plan_as_set: the desk sold on the stop, target or time written in the buying pick; revised: on numbers from a later pick; sold_by_hand: the model wrote a sell")

# ------------------------------------------------------------------ TM03 dial
btc = "BTC/USD"
d_rows = []
for d in sessions("TM03"):
    sid = os.path.basename(d); _, model, month = parse_sid(sid)
    prog = json.load(open(d + "/progress.json"))
    by_k = {s["k"]: s for s in prog["steps"]}
    for r in [x for x in dials if x["sid"] == sid and x["direction"] != "same"]:
        s = by_k[int(r["id"].split("|")[1])]
        t = P.ts(s.get("fill_utc") or s["utc"])
        d_rows.append(dict(sid=sid, model=model, month=month, t=t, dir=r["direction"], cat=r["cat"], dw=r["new"] - r["prev"],
                           f24=P.ret(btc, t, t + H24), f120=P.ret(btc, t, t + H120), b24=P.ret(btc, t - H24, t), b7=P.ret(btc, t - D7, t)))
# base: every daily wake of the TM03 months
m_start = {}
for d in sessions("TM03"):
    sess = json.load(open(d + "/session.json"))
    m_start[parse_sid(os.path.basename(d))[2]] = (P.ts(sess["window"]["start"] + "T00:00:00"), P.ts(sess["end_utc"]))
bf24, bf120 = [], []
for a, z in m_start.values():
    t = a
    while t < z:
        bf24.append(P.ret(btc, t, t + H24)); bf120.append(P.ret(btc, t, t + H120)); t += 86400

mbase = {}
for mo, (a, z) in m_start.items():
    v24, v120 = [], []
    t = a
    while t < z:
        v24.append(P.ret(btc, t, t + H24)); v120.append(P.ret(btc, t, t + H120)); t += 86400
    mbase[mo] = (mean(v24), mean(v120))

def dial_table(rows):
    x24 = [None if r["f24"] is None or mbase[r["month"]][0] is None else r["f24"] - mbase[r["month"]][0] for r in rows]
    x120 = [None if r["f120"] is None or mbase[r["month"]][1] is None else r["f120"] - mbase[r["month"]][1] for r in rows]
    return dict(n=len(rows), small=len(rows) < SMALL, after_24h=cell([r["f24"] for r in rows]), after_120h=cell([r["f120"] for r in rows]),
                after_24h_minus_month_base=cell(x24), after_120h_minus_month_base=cell(x120),
                before_24h=cell([r["b24"] for r in rows]), before_7d=cell([r["b7"] for r in rows]),
                share_weighted_120h=r6(sum(r["dw"] * r["f120"] for r in rows if r["f120"] is not None)))
dt = dict(base_daily=dict(after_24h=cell(bf24), after_120h=cell(bf120)), month_base={m: dict(after_24h=r6(v[0]), after_120h=r6(v[1])) for m, v in sorted(mbase.items())})
dt["by_month_dir"] = {k: dial_table(v) for k, v in sorted(group(d_rows, lambda r: r["month"] + "|" + r["dir"]).items())}
dt["by_dir"] = {k: dial_table(v) for k, v in sorted(group(d_rows, lambda r: r["dir"]).items())}
dt["by_dir_cat"] = {k: dial_table(v) for k, v in sorted(group(d_rows, lambda r: r["dir"] + "|" + r["cat"]).items())}
dt["by_dir_model"] = {k: dial_table(v) for k, v in sorted(group(d_rows, lambda r: r["dir"] + "|" + r["model"]).items())}
dt["changes_classified"] = len(d_rows)
dt["note"] = "after_* is the bitcoin price change from the fill of the change. A cut helps when the price then falls (negative), a raise when it rises. share_weighted_120h sums (new share minus old share) times the 120-hour change: positive means the changes, taken alone over five days, added value before costs."
out["tm03"] = dt

# ------------------------------------------------------------------ TM04 basket
k_rows = []
for d in sessions("TM04"):
    sid = os.path.basename(d); _, model, _ = parse_sid(sid)
    prog = json.load(open(d + "/progress.json"))
    steps = prog["steps"]
    px_at = [{sym: v[1] for sym, v in (s.get("row") or {}).get("fills", {}).items()} for s in steps]
    for r in [x for x in baskets if x["sid"] == sid]:
        k = r["k"]
        def fwd(n):
            if k + n >= len(steps):
                return None, None
            a, b = px_at[k], px_at[k + n]
            if r["symbol"] not in a or r["symbol"] not in b:
                return None, None
            own = b[r["symbol"]] / a[r["symbol"]] - 1
            allr = [b[s] / a[s] - 1 for s in a if s in b]
            return own, own - mean(allr)
        o1, e1 = fwd(1); o4, e4 = fwd(4)
        k_rows.append(dict(sid=sid, model=model, kind=r["kind"], cat=r["cat"], initial=(k == 0), f1w=o1, x1w=e1, f4w=o4, x4w=e4))

def basket_table(rows):
    return dict(n=len(rows), small=len(rows) < SMALL, next_week=cell([r["f1w"] for r in rows]), next_week_minus_all38=cell([r["x1w"] for r in rows]),
                next_4_weeks=cell([r["f4w"] for r in rows]), next_4_weeks_minus_all38=cell([r["x4w"] for r in rows]))
kt = dict(by_kind={k: basket_table(v) for k, v in sorted(group(k_rows, lambda r: r["kind"] or "none").items())})
kt["by_kind_cat"] = {k: basket_table(v) for k, v in sorted(group(k_rows, lambda r: (r["kind"] or "none") + "|" + r["cat"]).items())}
kt["by_kind_model"] = {k: basket_table(v) for k, v in sorted(group(k_rows, lambda r: (r["kind"] or "none") + "|" + r["model"]).items())}
kt["after_first_week_by_kind"] = {k: basket_table(v) for k, v in sorted(group([r for r in k_rows if not r["initial"]], lambda r: r["kind"] or "none").items())}
kt["note"] = "Prices are the desk's own fill marks at each weekly wake. minus_all38 subtracts the equal average of all 38 symbols over the same weeks."
out["tm04"] = kt

# ------------------------------------------------------------------ label checks and contradiction check
def agree(name, key):
    rows = HC[name]
    if not rows:
        return None
    ref = dict(hand)
    rule = {}
    for r in buys_txt: rule[r["id"]] = r["cat"]
    for r in sell_orders: rule[r["id"]] = r["cat"]
    for r in dials:
        if r.get("cat"): rule[r["id"]] = r["cat"]
    for r in baskets: rule[r["id"]] = r["cat"]
    src = ref if key == "second_label" else rule
    a = sum(1 for r in rows if src.get(r["id"]) == r[key])
    return dict(n=len(rows), agree=a, rate=r6(a / len(rows)))
out["label_checks"] = dict(
    hand_relabel_blind=agree("hand_relabel_blind", "second_label"),
    rule_vs_analyst_after_fix_sample1=agree("rulecheck_sample1", "analyst_label"),
    rule_vs_analyst_sample2=agree("rulecheck_sample2", "analyst_label"),
    rule_vs_analyst_sample1_before_fix=dict(n=60, agree=46, rate=round(46 / 60, 6), note="recorded at the time; the basket rule was then fixed (dropped stocks named only by trailing returns were labelled momentum) and the indicator rule (it matched the word small)"),
    note="hand_relabel_blind is the same analyst labelling again minutes later without seeing the first label: a check of consistency, not of correctness.")
cb = HC["contradiction_check"]
chk = [r for r in cb if r["verdict"] != "not_checkable"]
out["contradiction_check"] = dict(sampled=len(cb), checkable=len(chk), contradicted=sum(1 for r in chk if r["verdict"] == "contradicted"),
                                  rate=r6(sum(1 for r in chk if r["verdict"] == "contradicted") / len(chk)) if chk else None,
                                  borderline=sum(1 for r in cb if r.get("borderline")),
                                  notes=[r["note"] for r in cb if r["verdict"] == "contradicted"],
                                  method="Seeded sample of 60 buys. Stated price facts checked by hand against tape minute prices up to the decision time (the same data the model could request) and against the headlines in the packet.")

# ------------------------------------------------------------------ faults in the stored records
faults = {}
MON = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
def later_dates(text, when):
    hits = []
    for m in re.finditer(r"(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d)", text or ""):
        try:
            tt = P.ts(f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}:00")
        except ValueError:
            continue
        if tt > when:
            hits.append(m.group(0))
    for m in re.finditer(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? (\d{1,2})\b", text or ""):
        mo, dd = MON[m.group(1).lower()], int(m.group(2))
        dw = datetime.datetime.fromtimestamp(when, datetime.timezone.utc)
        try:
            cand = datetime.datetime(dw.year, mo, dd, tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
        if cand.date() > dw.date() and (cand - dw).days < 200:
            hits.append(m.group(0))
    return hits
later = []
all_texts = []
for plan in ("TM01", "TM02", "TM03", "TM04"):
    for d in sessions(plan):
        sid = os.path.basename(d)
        for s in json.load(open(d + "/progress.json"))["steps"]:
            when = P.ts(s["utc"])
            texts = []
            if s.get("pick"):
                texts += [s["pick"].get("thesis", "")] + [a.get("reason", "") for a in s["pick"].get("actions", [])]
            texts += [s.get("no_pick_why") or "", s.get("why") or ""] + list((s.get("reasons") or {}).values())
            for tx in texts:
                if tx:
                    all_texts.append((sid, s["utc"], tx))
                for h in later_dates(tx, when):
                    later.append(dict(sid=sid, utc=s["utc"], date_named=h))
faults["texts_scanned"] = len(all_texts)
iso_later = [x for x in later if re.match(r"\d{4}-", x["date_named"])]
hv = HC["later_dates_by_hand"]
faults["answers_naming_a_later_date"] = dict(n=len(later), timestamped_items_after_the_clock=len(iso_later), month_day_mentions=len(later) - len(iso_later),
                                             hand_read=hv, items=later[:60])
faults["missing_reasons"] = dict(
    buy_actions_without_reason=sum(1 for r in buys_txt if not r["reason"].strip()),
    picks_without_thesis=sum(1 for r in buys_txt if not r["thesis"].strip()),
    dial_changes_without_why=sum(1 for r in dials if r["direction"] != "same" and not r["reason"].strip()),
    tm03_answers_without_why=sum(1 for d in sessions("TM03") for s in json.load(open(d + "/progress.json"))["steps"] if not (s.get("why") or "").strip()),
    tm04_answers_without_why=sum(1 for d in sessions("TM04") for s in json.load(open(d + "/progress.json"))["steps"] if not (s.get("why") or "").strip()),
    tm04_changes_without_stock_reasons=sum(1 for d in sessions("TM04") for s in json.load(open(d + "/progress.json"))["steps"] if s.get("changed") and not s.get("reasons")),
    filled_buys_without_written_action=sum(1 for b in buys if b["cat"] == "UNCLEAR"))
dup = collections.defaultdict(set)
for sid, utc, tx in all_texts:
    if len(tx) >= 40:
        dup[tx.strip()].add(sid)
cross = {t: sorted(s) for t, s in dup.items() if len(s) > 1}
dup_where = collections.defaultdict(list)
for sid, utc, tx in all_texts:
    if tx.strip() in cross:
        dup_where[tx.strip()].append(f"{sid} at {utc}")
within = collections.Counter((sid, tx.strip()) for sid, utc, tx in all_texts if len(tx) >= 40)
faults["duplicated_texts"] = dict(same_text_in_more_than_one_session=len(cross), examples=[dict(where=sorted(set(dup_where[t]))[:6]) for t in list(cross)[:10]],
                                  same_text_repeated_within_a_session=sum(1 for v in within.values() if v > 1))
# quoted headlines that are not in the packet the model was given at that wake (TM02 buys)
q_tot = q_found = 0; q_after = 0
for r in buys_txt:
    if r["plan"] != "TM02":
        continue
    qs = [a or b for a, b in re.findall(r"'([^']{20,})'|\"([^\"]{20,})\"", r["reason"])]
    if not qs:
        continue
    heads = []
    for pf_ in glob.glob(f"{settings.RUNS}/{r['sid']}/packets/*.json"):
        p = json.load(open(pf_))
        if p.get("utc") == r["utc"]:
            heads = [n["headline"].lower() for n in p["feed"].get("news", [])]; break
    for q in qs:
        q_tot += 1
        if any(q[:40].lower() in h for h in heads):
            q_found += 1
faults["tm02_quoted_headlines"] = dict(quoted=q_tot, found_in_that_wakes_packet=q_found,
                                       note="A quoted headline not in the wake's packet may have come from a news look the model made; looks are logged without their content, so this is not counted as a fault on its own.")
faults["other"] = anomalies[:30]
cx = HC["cross_session_by_hand"]
faults["duplicated_texts"]["hand_read"] = cx
out["faults"] = faults

# ------------------------------------------------------------------ quotes (checked against stored texts)
qs = json.load(open(os.path.join(HERE, "quotes.json"))) if os.path.exists(os.path.join(HERE, "quotes.json")) else []
blob = {}
for sid, utc, tx in all_texts:
    blob.setdefault(sid, []).append(tx)
for r in sell_orders:
    blob.setdefault(r["sid"], []).append(r["reason"])
from classify import _quoted_title
def session_news(sid):
    """Every headline and summary in the packets of one session (none for TM01, which has no news)."""
    out_ = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("headline", "title", "summary", "text") and isinstance(v, str):
                    out_.append(v)
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    for f in sorted(glob.glob(f"{settings.RUNS}/{sid}/packets/*.json")):
        walk(json.load(open(f)))
    return out_
for q in qs:
    q["found_in_records"] = any(q["quote"] in t for t in blob.get(q["session"], []))
    q["words"] = len(q["quote"].split())
    q["five_word_runs_shared_with_news"] = len(shared_runs(q["quote"], session_news(q["session"])))
    q["has_quoted_title"] = _quoted_title(q["quote"])
    if not q["found_in_records"] or q["five_word_runs_shared_with_news"] or q["has_quoted_title"] or q["words"] >= 40:
        print(f"quote {q['n']} fails a check: {q}")
out["quotes"] = qs

# ------------------------------------------------------------------ costs and settings used
out["settings"] = dict(crypto_fee_bps_per_side="practice_crypto_fee_bps_added = 25 (from each session's config)",
                       crypto_half_spread_bps="tm_crypto_half_spread_bps = 10 (from each session's config)",
                       price_source="recorded tape, 1-minute closes; 24h, 48h, 120h, 7d changes from the minute at or before each time",
                       base_rate="every hour of the session month for the same coin (crypto); every daily wake of the TM03 months (bitcoin); all 38 symbols the same week (TM04)")
json.dump(out, open(settings.OUT, "w"), indent=1, default=str)
print("written", settings.OUT, out["made_utc"])
