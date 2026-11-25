"""Draft plan 11: picks the usable events, splits them by date, draws the design sample, builds every prompt and the
reader folders. Reads no price after any filing. The only prices it reads are March 2026 windows that end by 2026-03-31,
before the first event, to size the test.

Usage, from research_rig/ after fetch_11_edgar.py has run:
  python3 prep_11.py summary          writes data/edgar_11/usable_11.json and research_rig/events_11_summary.json
  python3 prep_11.py design           writes the prompts and one folder per reader per batch for the design sample
  python3 prep_11.py heldback STAGE   STAGE 1: the chosen set-up's first readers on every held-back event.
                                      STAGE 2 (cascade only): the strong reader on the disagreements and the audit share.
                                      Refuses until results_11_design.json names the chosen set-up.
Prints counts only. Folders go to data/edgar_11/reading/<phase>/<reader>/bNNN/."""
import glob, sys, os, re, json, random, statistics, math, shutil
from collections import Counter, defaultdict
import datetime as dt
import common_11 as C

EV, RD, DS, ST = C.th("replay_11_events"), C.th("replay_11_readers"), C.th("replay_11_design"), C.th("replay_11_statistics")
SEED = ST["seed"]

def companies_by_cik():
    sys.path.insert(0, C.HERE); import fetch_11_edgar as F
    mem, _ = F.companies()
    return {cik: (lst, sym) for lst, sym, cik, how in mem}

def usable():
    """The plan's event filters. Reads which dates have a bar, never a price."""
    raw = json.load(open(os.path.join(C.EDGAR, "events_11.json")))
    E = raw["events"]; byc = companies_by_cik(); days = C.trading_days()
    why = Counter(); keep = []; last = {}; have = {}
    for e in sorted(E, key=lambda e: (e["acceptance_utc"], e["accession"])):
        lst, sym = byc[e["cik"]]; e = dict(e, list=lst, symbol=sym)   # the symbol from the fixed table, by CIK
        if e["form"] != "8-K": why["amendment (8-K/A)"] += 1; continue
        if not (EV["start"] <= e["filing_date"] <= EV["end"]): why["outside dates"] += 1; continue
        if e["text_chars"] < EV["min_text_chars"]: why["text short or no exhibit"] += 1; continue
        d = e["acceptance_ny"][:10]
        if e["cik"] in last and (dt.date.fromisoformat(d) - dt.date.fromisoformat(last[e["cik"]])).days < EV["min_days_between"]:
            why["second within min_days_between"] += 1; continue
        ent = C.entry_day(e["acceptance_ny"], days)
        if sym not in have: have[sym] = C.bar_dates(sym)
        if ent is None or ent not in have[sym]: why["no bar on entry day"] += 1; continue
        last[e["cik"]] = d   # the 20-day wait starts from a kept event only
        keep.append(dict(event_id=C.event_id(e["accession"]), list=lst, symbol=sym, price_symbol=C.price_symbol(sym), cik=e["cik"],
                         accession=e["accession"], acceptance_ny=e["acceptance_ny"], session=e["session"], entry_day=ent,
                         exhibit_file=e["exhibit_file"], text_chars=e["text_chars"]))
    # split by date: the boundary between two entry days nearest the middle by count, so no entry day is in both halves
    cuts = [i for i in range(1, len(keep)) if keep[i]["entry_day"] != keep[i - 1]["entry_day"]]
    half = min(cuts, key=lambda i: (abs(i - len(keep) / 2), i)) if cuts else len(keep) // 2
    for i, k in enumerate(keep): k["half"] = "design" if i < half else "heldback"
    return raw, keep, why

def guidance_pos(t):
    m = re.search(r"(?im)^\s*(?:[\w&,\- ]{0,40})?(outlook|guidance)\b[^\n]{0,80}$", t)
    return m.start() if m else None

def pct(xs, p):
    xs = sorted(xs); return xs[int(p * (len(xs) - 1))] if xs else None

def march_sd(symbols):
    """Spread of open-to-5th-close moves for windows inside March 2026 (all before the first event)."""
    days = [d for d in C.trading_days() if d <= "2026-03-31"]; out = []
    for s in symbols:
        P = C.price_rows(s)
        for i in range(len(days) - 4):
            a, b = days[i], days[i + 4]
            if a in P and b in P and P[a][0] > 0: out.append(P[b][1] / P[a][0] - 1)
    return statistics.pstdev(out), len(out)

def summary():
    raw, keep, why = usable()
    texts = {k["event_id"]: open(os.path.join(C.EDGAR, "ex99", k["accession"] + ".txt"), encoding="utf-8").read() for k in keep}
    cap = RD["text_cap_chars"]; nd = sum(k["half"] == "design" for k in keep); split = keep[nd]
    S = dict(made_by="research_rig/prep_11.py summary", made_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
             list_sources=raw["list_sources"], members=raw["members"], cik_how=raw["cik_how"], members_without_cik=raw["no_cik"],
             window=raw["window"], price_aliases=C.ALIAS)
    allE = raw["events"]; byc = companies_by_cik()
    for e in allE: e["list"] = byc[e["cik"]][0]
    S["filings"] = {l: dict(item_202_filings=sum(e["list"] == l for e in allE),
                            companies_with_filings=len({e["cik"] for e in allE if e["list"] == l}),
                            amendments=sum(e["list"] == l and e["form"] == "8-K/A" for e in allE),
                            with_exhibit_99=sum(e["list"] == l and bool(e["exhibit_file"]) for e in allE),
                            text_at_least_min=sum(e["list"] == l and e["text_chars"] >= EV["min_text_chars"] for e in allE),
                            session=dict(Counter(e["session"] for e in allE if e["list"] == l)))
                    for l in C.LISTS}
    S["dropped"] = dict(why)
    S["used"] = {l: dict(events=sum(k["list"] == l for k in keep), companies=len({k["cik"] for k in keep if k["list"] == l}),
                         design=sum(k["list"] == l and k["half"] == "design" for k in keep),
                         heldback=sum(k["list"] == l and k["half"] == "heldback" for k in keep)) for l in C.LISTS}
    S["used_total"] = dict(events=len(keep), design=sum(k["half"] == "design" for k in keep), heldback=sum(k["half"] == "heldback" for k in keep),
                           split_last_design=keep[nd - 1]["acceptance_ny"], split_first_heldback=split["acceptance_ny"],
                           last_design_entry_day=keep[nd - 1]["entry_day"], first_heldback_entry_day=split["entry_day"],
                           by_month=dict(sorted(Counter(k["acceptance_ny"][:7] for k in keep).items())))
    L = [len(t) for t in texts.values()]; G = [g for g in (guidance_pos(t) for t in texts.values()) if g is not None]
    S["text_chars"] = dict(events=len(L), p10=pct(L, .1), p25=pct(L, .25), median=pct(L, .5), p75=pct(L, .75), p90=pct(L, .9), max=max(L),
                           by_list={l: pct([len(texts[k["event_id"]]) for k in keep if k["list"] == l], .5) for l in C.LISTS},
                           guidance_heading_found=len(G), guidance_heading_median_pos=pct(G, .5), guidance_heading_p90_pos=pct(G, .9),
                           cap=cap, share_cut=round(sum(x > cap for x in L) / len(L), 3),
                           share_guidance_heading_after_cap=round(sum(g > cap for g in G) / len(G), 3),
                           share_cut_by_candidate_cap={str(c): round(sum(x > c for x in L) / len(L), 3) for c in (10000, 15000, 20000, 25000, 30000)},
                           share_guidance_after_by_candidate_cap={str(c): round(sum(g > c for g in G) / len(G), 3) for c in (10000, 15000, 20000, 25000, 30000)})
    # price coverage, dates only
    days = C.trading_days(); cov = {}
    for l in C.LISTS:
        syms = sorted({s for s in (m[1] for m in byc.values() if m[0] == l)}); short = {}
        for s in syms:
            ds = sorted(C.bar_dates(s) & set(days))
            if len(ds) != len(days): short[s] = dict(price_symbol=C.price_symbol(s), days=len(ds), first=ds[0] if ds else None, last=ds[-1] if ds else None)
        cov[l] = dict(companies=len(syms), every_day=len(syms) - len(short), short=short)
    OV0 = C.th("replay_11_overnight"); rows_cache = {}; flagged_syms = set(); all_moves = 0
    for s_ in sorted({k["symbol"] for k in keep}):
        P_ = C.price_rows(s_); f_ = C.overnight_moves(P_, days, OV0["ratio_min"], OV0["ratio_max"])
        if f_: flagged_syms.add(s_); rows_cache[s_] = P_; all_moves += len(f_)
    # the prompt header carries no ticker, but the release text usually does: share of used texts whose shown part (to the
    # cap) holds the ticker as a whole word, any of its spellings (BF.B, BF-B, BFB)
    def has_ticker(k):
        t = open(os.path.join(C.EDGAR, "ex99", k["accession"] + ".txt"), encoding="utf-8").read()[:RD["text_cap_chars"]]
        forms = {k["symbol"], k["symbol"].replace(".", "-"), k["symbol"].replace(".", ""), k["symbol"].replace(".", " ")}
        return any(re.search(r"(?<![A-Za-z0-9])" + re.escape(f) + r"(?![A-Za-z0-9])", t) for f in forms)
    S["text_chars"]["share_with_ticker_in_shown_text"] = round(sum(map(has_ticker, keep)) / len(keep), 3)
    S["prices"] = dict(trading_days=len(days), first=days[0], last=days[-1], by_list=cov,
                       used_events_whose_bars_stop_before_last_day=sum(1 for k in keep if k["symbol"] in cov[k["list"]]["short"]))
    # windows: whose bars stop inside the hold (dates only), and large overnight moves inside the hold (replay_11_overnight).
    # The overnight check reads the open and close of the window's days only to compare a close with the next open; it
    # works out no event return and stores no price, only counts and the dates of each flagged move.
    OV = C.th("replay_11_overnight"); win_counts = {}; moves = set()
    for h, n in C.th("replay_11_statistics")["holds"].items():
        c = dict(stops_inside={}, overnight_flagged={}, prices_end_first=0)
        for k in keep:
            w = C.window(days, k["entry_day"], n)
            if w is None: c["prices_end_first"] += 1; continue
            key = f"{k['list']}_{k['half']}"
            if w[-1] not in C.bar_dates(k["symbol"]) if k["symbol"] in cov[k["list"]]["short"] else False:
                c["stops_inside"][key] = c["stops_inside"].get(key, 0) + 1
            if k["symbol"] in flagged_syms:
                f = C.overnight_moves(rows_cache[k["symbol"]], w, OV["ratio_min"], OV["ratio_max"])
                if f:
                    c["overnight_flagged"][key] = c["overnight_flagged"].get(key, 0) + 1
                    moves.update((k["symbol"], a, b) for a, b, _ in f)
        c["stops_inside_total"] = sum(c["stops_inside"].values()); c["overnight_flagged_total"] = sum(c["overnight_flagged"].values())
        win_counts[h] = c
    S["windows"] = dict(by_hold=win_counts, all_large_overnight_moves_in_used_symbols=all_moves,
                        moves_inside_a_used_window=sorted(f"{s} {a} to {b}" for s, a, b in moves))
    # design sample: seeded, sample_per_list from each list's design half
    rng = random.Random(SEED); sample = []
    for l in C.LISTS:
        pool = sorted(k["event_id"] for k in keep if k["list"] == l and k["half"] == "design")
        sample += rng.sample(pool, DS["sample_per_list"])
    for k in keep: k["design_sample"] = k["event_id"] in set(sample)
    # extraction check pick: seeded, across the lists
    rng = random.Random(f"{SEED}-extraction"); n = ST["extraction_check"]; per = [n // 3 + (i < n % 3) for i in range(3)]
    pick = []
    for l, m in zip(C.LISTS, per): pick += rng.sample(sorted(k["event_id"] for k in keep if k["list"] == l), m)
    byid = {k["event_id"]: k for k in keep}
    S["extraction_check_pick"] = [dict(event_id=i, list=byid[i]["list"], symbol=byid[i]["symbol"], accession=byid[i]["accession"]) for i in pick]
    batches = math.ceil(DS["sample_per_list"] * len(C.LISTS) / RD["batch_max"])
    S["design_sample"] = dict(events=len(sample), per_list=DS["sample_per_list"], folders_per_reader=batches,
                              readers=RD["small_models"] + [RD["strong_model"]], folders_total=batches * (len(RD["small_models"]) + 1))
    # size: March 2026 spread by list, before the first event
    sd = {}
    for l in C.LISTS:
        s, n_ = march_sd(sorted({k["symbol"] for k in keep if k["list"] == l})); sd[l] = dict(sd=round(s, 4), windows=n_)
    H = {l: S["used"][l]["heldback"] for l in C.LISTS}; N = sum(H.values())
    pooled = math.sqrt(sum(H[l] * sd[l]["sd"] ** 2 for l in C.LISTS) / N)
    z = 1.645 + 0.842
    def edge80(sdv, b): return z * sdv * math.sqrt(1 / b - 1 / N)
    S["size"] = dict(march_open_to_5th_close_sd=sd, pooled_sd_heldback_weights=round(pooled, 4), heldback_events=N,
                     note="sd from windows that start and end inside March 2026. After earnings the spread is wider by an amount UNKNOWN; x1.5 is an assumption.",
                     edge_80pct_at_buy_share={f"{bs}": dict(buys=round(bs * N), sd_march=round(edge80(pooled, bs * N), 4), sd_march_x1_5=round(edge80(1.5 * pooled, bs * N), 4))
                                              for bs in (0.2, 0.4, 0.6)},
                     events_for_80pct_at_0_5pct_edge_half_bought=dict(sd_march=round((z * pooled / 0.005) ** 2), sd_march_x1_5=round((z * 1.5 * pooled / 0.005) ** 2)))
    os.makedirs(C.EDGAR, exist_ok=True)
    json.dump(dict(events=keep, design_sample=sorted(sample)), open(os.path.join(C.EDGAR, "usable_11.json"), "w"), indent=1)
    S["usable_file_sha256"] = C.sha256_file(os.path.join(C.EDGAR, "usable_11.json"))
    json.dump(S, open(C.SUMMARY, "w"), indent=1); open(C.SUMMARY, "a").write("\n")
    print(json.dumps(dict(used=S["used"], total=S["used_total"], cap=cap, share_cut=S["text_chars"]["share_cut"], design=S["design_sample"]), indent=1))

# ------------------------------------------------------------------------------------------------ prompts and folders
def body(k):
    t = open(os.path.join(C.EDGAR, "ex99", k["accession"] + ".txt"), encoding="utf-8").read()
    cap = RD["text_cap_chars"]; cut = len(t) > cap
    if cut:
        t = t[:cap]; t = t[:t.rfind("\n")] if "\n" in t[cap // 2:] else t
        t += f"\n\n[The text is cut here at about {cap} characters. The rest of the release is not shown.]"
    return f"Filed with the SEC (accepted): {k['acceptance_ny']} New York time\n\n{t}\n"

def prompt(k):
    """The exact bytes a reader is shown for one event, and their SHA-256. Written once per event."""
    b = body(k).encode("utf-8"); h = C.sha256_bytes(b)
    head = f"event_id: {k['event_id']}\ninput_sha256: {h}\n========\n".encode("utf-8")
    os.makedirs(os.path.join(C.EDGAR, "prompts"), exist_ok=True)
    p = os.path.join(C.EDGAR, "prompts", k["event_id"] + ".txt"); open(p, "wb").write(head + b)
    return h, p

def deal(events, tag):
    """Shuffle with the seed and deal into folders of at most batch_max, no two from one company in a folder."""
    ev = sorted(events, key=lambda k: k["event_id"]); random.Random(f"{SEED}-{tag}").shuffle(ev)
    most = max(Counter(k["cik"] for k in ev).values(), default=1)
    n = max(1, math.ceil(len(ev) / RD["batch_max"]), most); bins = [[] for _ in range(n)]   # most: one company's events need that many folders
    for k in ev:
        free = [b for b in bins if len(b) < math.ceil(len(ev) / n) and all(x["cik"] != k["cik"] for x in b)]
        if not free: free = [b for b in bins if len(b) < RD["batch_max"] and all(x["cik"] != k["cik"] for x in b)]
        min(free, key=len).append(k)
    return bins

def write_folders(phase, reader, bins):
    inst = open(C.INSTRUCTION, "rb").read(); ih = C.sha256_bytes(inst); out = []
    root = os.path.join(C.READING, phase, reader)
    if os.path.exists(root): sys.exit(f"refused: {root} exists. Folders are written once.")
    for i, b in enumerate(bins, 1):
        f = os.path.join(root, f"b{i:03d}"); os.makedirs(os.path.join(f, "events"))
        order = list(b); random.Random(f"{SEED}-{phase}-{reader}-{i}").shuffle(order); man = []
        for k in order:
            h, p = prompt(k); shutil.copy(p, os.path.join(f, "events", k["event_id"] + ".txt"))
            man.append(dict(event_id=k["event_id"], input_sha256=h, file=f"events/{k['event_id']}.txt"))
        open(os.path.join(f, "INSTRUCTION.txt"), "wb").write(inst)
        json.dump(dict(reader=reader, batch_id=f"b{i:03d}", instruction_sha256=ih, events=man), open(os.path.join(f, "manifest.json"), "w"), indent=1)
        out.append(f)
    # what check_11_answers.py --collect must find, kept outside the reader's folder
    json.dump(dict(phase=phase, reader=reader, batches={f"b{i:03d}": sorted(k["event_id"] for k in b) for i, b in enumerate(bins, 1)}),
              open(os.path.join(C.READING, phase, reader + ".expected.json"), "w"), indent=1)
    return out

def design():
    U = C.load_usable(); s = set(U["design_sample"]); ev = [k for k in U["events"] if k["event_id"] in s]
    bins = deal(ev, "design"); n = 0
    for r in RD["small_models"] + [RD["strong_model"]]: n += len(write_folders("design", r, bins))
    print(json.dumps(dict(events=len(ev), folders_per_reader=len(bins), folders=n, largest=max(map(len, bins)), smallest=min(map(len, bins))), indent=1))

def heldback(stage):
    p = os.path.join(C.HERE, "results_11_design.json")   # the real file, whatever RESULTS_11_DIR says
    if not os.path.exists(p): sys.exit("refused: results_11_design.json does not exist, so no set-up is chosen")
    chosen = json.load(open(p))["chosen_setup"]
    if chosen is None: sys.exit("refused: no set-up qualified on the design sample, so the held-back half is not read")
    U = C.load_usable(); ev = [k for k in U["events"] if k["half"] == "heldback"]
    if stage == "1":
        readers = RD["small_models"] if chosen in ("middle", "cascade") else [chosen]
        bins = deal(ev, "heldback"); n = sum(len(write_folders("heldback", r, bins)) for r in readers)
        print(json.dumps(dict(chosen=chosen, events=len(ev), readers=readers, folders=n), indent=1)); return
    if chosen != "cascade": sys.exit("refused: stage 2 is for the cascade set-up only")
    import score_11 as S
    # the small readers' checked folders; the scorer later reads only the collected, hashed files
    A = {r: {x["event_id"]: x["score"] for f in sorted(glob.glob(os.path.join(C.READING, "heldback", r, "b*", "checked.jsonl"))) for x in map(json.loads, open(f))}
         for r in RD["small_models"]}
    if any(set(A[r]) != {k["event_id"] for k in ev} for r in A): sys.exit("refused: a small reader has not answered every held-back event")
    dis_ids, audit = S.cascade_strong_set(sorted(k["event_id"] for k in ev), A)
    dis = [k for k in ev if k["event_id"] in set(dis_ids)]; audit = set(audit)
    todo = dis + [k for k in ev if k["event_id"] in audit]
    bins = deal(todo, "heldback-strong"); n = len(write_folders("heldback", RD["strong_model"], bins))
    json.dump(dict(disagreements=sorted(k["event_id"] for k in dis), audit=sorted(audit)), open(os.path.join(C.READING, "heldback", "strong_reads.json"), "w"), indent=1)
    print(json.dumps(dict(disagreements=len(dis), audit=len(audit), folders=n), indent=1))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["summary"]: summary()
    elif a[:1] == ["design"]: design()
    elif a[:1] == ["heldback"] and len(a) == 2: heldback(a[1])
    else: print(__doc__)
