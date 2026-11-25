"""Tests for draft plan 11's prompt builder, answer checker and scorer, on made-up events, texts and prices only.
Run from research_rig/:  python3 test_11.py
Everything is written to a temporary folder. No real price, filing or answer is read."""
import os, sys, json, tempfile, shutil, random, datetime as dt

TMP = tempfile.mkdtemp(prefix="t11_")
os.environ.update(EDGAR_11_DIR=os.path.join(TMP, "edgar"), STOCK_DAILY_11_DIR=os.path.join(TMP, "px"),
                  SPY_DAILY_11_FILE=os.path.join(TMP, "SPY_1day.csv"), RESULTS_11_DIR=os.path.join(TMP, "out"))
for d in ("edgar/ex99", "px", "out"): os.makedirs(os.path.join(TMP, d))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_11 as C, prep_11 as P, check_11_answers as K, score_11 as S

SMALL, STRONG = S.SMALL, S.STRONG
fails = []
def ok(cond, name):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

# ---- made-up calendar and prices: 40 weekdays from 2026-04-01
days, d = [], dt.date(2026, 4, 1)
while len(days) < 40:
    if d.weekday() < 5: days.append(d.isoformat())
    d += dt.timedelta(days=1)
with open(C.SPY_FILE, "w") as f:
    f.write("date,open,high,low,close,volume\n")
    for i, x in enumerate(days): f.write(f"{x},{100 + i},{101 + i},{99 + i},{100.5 + i},1\n")
def write_px(sym, rows):
    with open(os.path.join(C.PRICES, f"{sym}_1day_2026-03-01_2026-11-24.csv"), "w") as f:
        f.write("date,open,close,volume\r\n")
        for x, (o, c) in rows.items(): f.write(f"{x},{o},{c},1\r\n")
# Stock Sxx: open on day i is 10, close on day i is 10 * (1 + up)^(i - entry + 1) for its own rate; easy to check
lists = ["500"] * 8 + ["400"] * 8 + ["600"] * 8
events = []
for n in range(24):
    sym = f"S{n:02d}"; up = (n % 6 - 2) / 100   # -2% .. +3% a day
    ent = days[2 + n % 10]; i0 = days.index(ent)
    rows = {x: (10.0, 10.0) for x in days[:i0]}
    for j, x in enumerate(days[i0:], 1): rows[x] = (10.0 * (1 + up) ** (j - 1), 10.0 * (1 + up) ** j)
    if n == 5: rows = {x: v for x, v in rows.items() if x <= days[i0 + 2]}   # S05 stops on its 3rd day
    write_px(sym, rows)
    acc = f"0000000000-26-{n:06d}"; eid = C.event_id(acc)
    open(os.path.join(C.EDGAR, "ex99", acc + ".txt"), "w").write(f"Company {n} reports results.\n" + "Line of text.\n" * (200 + 50 * n + (3000 if n == 23 else 0)))
    events.append(dict(event_id=eid, list=lists[n], symbol=sym, price_symbol=sym, cik=f"{n % 20:010d}", accession=acc,
                       acceptance_ny=f"{days[days.index(ent) - 1]} 16:05:00", session="after_close", entry_day=ent,
                       exhibit_file="x.htm", text_chars=0, half="design" if n < 12 else "heldback"))
ids_design = sorted(e["event_id"] for e in events if e["half"] == "design")
json.dump(dict(events=events, design_sample=ids_design), open(os.path.join(C.EDGAR, "usable_11.json"), "w"))
byid = {e["event_id"]: e for e in events}

# ---- calendar helpers
ok(C.entry_day("2026-04-01 08:00:00", days) == "2026-04-01", "filed before 09:30 enters that day's open")
ok(C.entry_day("2026-04-01 09:30:00", days) == "2026-04-02", "filed at 09:30 enters the next open")
ok(C.entry_day("2026-04-03 17:00:00", days) == "2026-04-06", "filed Friday after the close enters Monday")
ok(C.last_close_day_before("2026-04-02 08:00:00", days) == "2026-04-01", "last close before a pre-open filing is the day before")
ok(C.last_close_day_before("2026-04-02 16:30:00", days) == "2026-04-02", "last close before an after-close filing is that day")
write_px("CDN", {x: (10.0, 10.0) for x in days[10:]})
def raw_ev(acc, day): return dict(form="8-K", filing_date=day, text_chars=10 ** 6, acceptance_ny=f"{day} 08:00:00", acceptance_utc=f"{day} 12:00:00",
                                  accession=acc, cik="0000009999", session="pre_open", exhibit_file="x.htm")
json.dump(dict(events=[raw_ev("cd-1", days[3]), raw_ev("cd-2", days[12]), raw_ev("cd-3", days[14])]), open(os.path.join(C.EDGAR, "events_11.json"), "w"))
keep_cbc = P.companies_by_cik; P.companies_by_cik = lambda: {"0000009999": ("500", "CDN")}
_, kept, why = P.usable(); P.companies_by_cik = keep_cbc
ok([k["accession"] for k in kept] == ["cd-2"] and why["no bar on entry day"] == 1 and why["second within min_days_between"] == 1,
   "audit 12: an event dropped for no bar does not start the 20-day wait; a kept one does")

# ---- prompts and dealing
h, p = P.prompt(events[23]); raw = open(p, "rb").read()
ok(K.prompt_hash(events[23]["event_id"]) == h, "stored prompt hash is the hash of the text after the header")
ok(b"cut here" in raw and len(raw) < C.th("replay_11_readers")["text_cap_chars"] + 400, "a long text is cut at the cap and says so")
h0, p0 = P.prompt(events[0]); ok(b"cut here" not in open(p0, "rb").read(), "a short text is not cut")
ok(b"S00" not in open(p0, "rb").read(), "the prompt carries no ticker")
big = [dict(e, event_id=f"{i:012d}", cik=f"{i % 30:010d}") for i, e in enumerate(events * 3)]
bins = P.deal(big, "t")
ok(all(len(b) <= C.th("replay_11_readers")["batch_max"] for b in bins), "no folder holds more than batch_max")
ok(all(len({x["cik"] for x in b}) == len(b) for b in bins), "no folder holds two releases from one company")
ok(sorted(x["event_id"] for b in bins for x in b) == sorted(x["event_id"] for x in big), "every event is dealt once")
two = [dict(events[0], event_id="pair00000001"), dict(events[1], event_id="pair00000002", cik=events[0]["cik"])]
b2 = P.deal(two, "t2"); ok(len(b2) == 2 and all(len(b) == 1 for b in b2), "audit 6: two events from one company in a small set go to two folders, no crash")

# ---- folders and the checker
dev = [byid[i] for i in ids_design]; dbins = P.deal(dev, "design")
folders = {r: P.write_folders("design", r, dbins) for r in SMALL + [STRONG]}
ok(len(folders[SMALL[0]]) == 1, "12 events fit in one folder")
try: P.write_folders("design", SMALL[0], dbins); ok(False, "folders are written once")
except SystemExit: ok(True, "folders are written once")

def answer(folder, f=lambda e, i: 1, mutate=None):
    man = json.load(open(os.path.join(folder, "manifest.json"))); lines = []
    for i, e in enumerate(man["events"]):
        a = dict(event_id=e["event_id"], input_sha256=e["input_sha256"], score=f(e["event_id"], i), reason="revenue grew and guidance was raised")
        lines.append(a)
    if mutate: lines = mutate(lines)
    open(os.path.join(folder, "answers.jsonl"), "w").write("\n".join(x if isinstance(x, str) else json.dumps(x) for x in lines) + "\n")

f0 = folders[SMALL[0]][0]
def check_with(mut):
    answer(f0, mutate=mut); return K.check(f0)
ok(check_with(None)[0], "a correct answers file passes")
ok(not check_with(lambda L: L[:-1])[0], "a missing event is refused")
ok(not check_with(lambda L: [dict(L[0], input_sha256="0" * 64)] + L[1:])[0], "a wrong hash is refused")
ok(not check_with(lambda L: [dict(L[0], score=3)] + L[1:])[0], "a score of 3 is refused")
ok(not check_with(lambda L: [dict(L[0], score=True)] + L[1:])[0], "a score of true is refused")
ok(not check_with(lambda L: [dict(L[0], score=1.0)] + L[1:])[0], "a score of 1.0 is refused")
ok(not check_with(lambda L: L + [L[0]])[0], "an event answered twice is refused")
ok(not check_with(lambda L: [dict(L[0], extra=1)] + L[1:])[0], "an extra key is refused")
ok(not check_with(lambda L: [dict(L[0], event_id="zzz")] + L[1:])[0], "an unknown event id is refused")
ok(not check_with(lambda L: ["not json"] + L[1:])[0], "a line that is not JSON is refused")
ok(not check_with(lambda L: [dict(L[0], reason="x" * 201)] + L[1:])[0], "a reason over 200 characters is refused")
r = check_with(lambda L: [dict(L[0], reason="I remember the stock fell")] + L[1:]); ok(r[0] and any("remembers" in x for x in r[2]), "a reason that remembers the move is flagged")
r = check_with(lambda L: L[:-2]); ok(not r[0], "before the retry, missing answers are refused")
r = K.check(f0, second_try=True); rows = [json.loads(l) for l in open(os.path.join(f0, "checked.jsonl"))]
ok(r[0] and sum(x["second_try_zero"] for x in rows) == 2 and all(x["score"] == 0 for x in rows if x["second_try_zero"]), "after the retry, missing answers become 0 and are flagged")
shutil.copy(C.INSTRUCTION, os.path.join(TMP, "inst")); open(os.path.join(f0, "INSTRUCTION.txt"), "a").write("x")
ok(not K.check(f0, second_try=True)[0], "a changed instruction file is refused even on the retry")
shutil.copy(C.INSTRUCTION, os.path.join(f0, "INSTRUCTION.txt"))
man0 = json.load(open(os.path.join(f0, "manifest.json")))
ok(os.path.basename(f0) == "b001" and man0["batch_id"] == "b001", "audit 13: batch folders are b001, b002, ...")
ok("phase" not in man0, "audit 13: the manifest a reader sees has no phase")
ok(K.phase_of(f0) == "design", "audit 13: the checker takes the phase from the folder path")
ok(not check_with(lambda L: [dict(L[0], reason="revenue grew\rguidance was raised")] + L[1:])[0], "audit 13: a carriage return inside a reason is refused")
ev0 = os.path.join(f0, "events", man0["events"][0]["event_id"] + ".txt"); keep_ev = open(ev0, "rb").read()
open(ev0, "ab").write(b" the stock rose 9% the next day"); answer(f0)
r = K.check(f0, second_try=True); ok(not r[0] and any("folder's copy" in x for x in r[1]), "audit 8: a changed event file in the folder is refused, even on the retry")
open(ev0, "wb").write(keep_ev)
r = check_with(lambda L: [dict(L[0], score=2, reason="I remember the stock fell after this report")] + L[1:])
rows = {x["event_id"]: x for x in map(json.loads, open(os.path.join(f0, "checked.jsonl")))}; x0 = rows[man0["events"][0]["event_id"]] if False else None
first = json.loads(open(os.path.join(f0, "answers.jsonl")).readline())["event_id"]
ok(r[0] and rows[first]["score"] == 0 and rows[first]["remembered"] and rows[first]["score_given"] == 2, "audit 4: a reader that remembers the move gets 0; the flag and the given score are stored")
r = check_with(lambda L: [dict(L[0], reason="a product recall cut sales this quarter")] + L[1:])
rows = {x["event_id"]: x for x in map(json.loads, open(os.path.join(f0, "checked.jsonl")))}
ok(r[0] and not rows[first]["remembered"] and rows[first]["score"] == 1, "audit 4: a product recall is not a memory of the move")
said = ["I already know this stock surged 20% after earnings", "From memory, shares fell sharply after this release",
        "Recall the stock gapped up 12% next morning", "As I recall, it dropped", "I know how the stock reacted", "I remember the stock fell"]
not_said = ["I do not remember this move; strong revenue beat and raised guidance", "No memory of this stock; EPS beat by 10% and guidance raised",
            "I don't recall; margins widened", "I never remember these; revenue grew", "a product recall cut sales this quarter"]
ok(all(K.remembers(t) for t in said), "second pass C: already know, from memory, recall, as I recall, I know how the stock are caught")
ok(not any(K.remembers(t) for t in not_said), "second pass C: a negation in the three words before is skipped")
r = check_with(lambda L: [dict(L[0], score=2, reason=not_said[0])] + L[1:])
rows = {x["event_id"]: x for x in map(json.loads, open(os.path.join(f0, "checked.jsonl")))}
ok(r[0] and rows[first]["score"] == 2 and not rows[first]["remembered"], "second pass C: 'I do not remember this move' keeps its score")
answer(f0, mutate=lambda L: [dict(L[0], score=9)] + L); r = K.check(f0, second_try=True)
rows = {x["event_id"]: x for x in map(json.loads, open(os.path.join(f0, "checked.jsonl")))}
ok(r[0] and rows[first]["score"] == 0 and rows[first]["second_try_zero"], "audit 5: a bad answer then a good one for the same event is spoiled to 0 on the retry")

# ---- design answers with a known winner: grok buys the 3 best-rising stocks, the others differ
up = {e["event_id"]: (int(e["symbol"][1:]) % 6 - 2) for e in events}
plan = {SMALL[0]: lambda i: 2 if up[i] >= 1 else -1,           # buys the rising half
        SMALL[1]: lambda i: 2 if up[i] >= 3 else -2,           # buys only the best
        SMALL[2]: lambda i: 1,                                 # buys everything: outside the buy-share window
        STRONG:   lambda i: 1 if up[i] <= 0 else -1}           # buys the losers
for rd, fn in plan.items():
    for f in folders[rd]: answer(f, lambda e, i, fn=fn: fn(e)); ok(K.check(f)[0], f"{rd} answers pass the checker")
mem_id = next(i for i in ids_design if up[i] == 0)   # the strong reader buys it (score 1), then says it remembers the move
answer(folders[STRONG][0], lambda e, i: plan[STRONG](e), lambda L: [dict(a, reason="I remember shares fell after this") if a["event_id"] == mem_id else a for a in L])
ok(K.check(folders[STRONG][0])[0], "a remembered answer passes the checker, set to 0")
def refused(fn, *a):
    try: fn(*a); return False
    except (SystemExit, S.Refused): return True
gone = os.path.join(C.READING, "design", STRONG); os.rename(gone, gone + ".away"); shutil.move(gone + ".expected.json", gone + ".x")
ok(refused(K.collect, "design"), "audit 7: collect refuses when a reader is missing"); os.rename(gone + ".away", gone); shutil.move(gone + ".x", gone + ".expected.json")
cp = os.path.join(folders[SMALL[1]][0], "checked.jsonl"); keep_cp = open(cp).read(); open(cp, "w").write("".join(keep_cp.splitlines(True)[1:]))
ok(refused(K.collect, "design"), "audit 7: collect refuses when a folder's checked answers miss an event"); open(cp, "w").write(keep_cp)
os.rename(cp, cp + ".x"); ok(refused(K.collect, "design"), "audit 7: collect refuses an unchecked folder"); os.rename(cp + ".x", cp)
K.collect("design")
H = json.load(open(os.path.join(C.OUTDIR, "answers_11_design_hashes.json")))
ok(len(H["files"]) == 4, "collect writes one hashed file per reader")
ok(H["files"][f"answers_11_design_{SMALL[0]}.jsonl"]["remembered_set_to_zero"] == 0 and "short_reason" in H["files"][f"answers_11_design_{SMALL[0]}.jsonl"], "audit 4: the hashes file counts remembered and short reasons")
HP = os.path.join(C.OUTDIR, "answers_11_design_hashes.json"); keep_h = open(HP).read()
json.dump(dict(H, files={}), open(HP, "w"))
try: S.design(require_push=False); ok(False, "second pass A: a hashes file that lists no files is refused")
except S.Refused as e: ok("not exactly" in str(e), "second pass A: a hashes file that lists no files is refused")
json.dump(dict(H, files={k: v for k, v in H["files"].items() if STRONG not in k}), open(HP, "w"))
try: S.design(require_push=False); ok(False, "second pass A: a hashes file missing one reader is refused")
except S.Refused as e: ok("not exactly" in str(e), "second pass A: a hashes file missing one reader is refused")
open(HP, "w").write(keep_h)
cf = os.path.join(C.EDGAR, f"answers_11_design_{SMALL[1]}.jsonl"); os.rename(cf, cf + ".x")
ok(refused(S.load_answers, "design", [SMALL[1]]), "second pass A: no collected file means refused, not a fallback to the unhashed checked folders"); os.rename(cf + ".x", cf)
try: S.require_no_override(); ok(False, "second pass B: a real run refuses while a test folder override is set")
except S.Refused as e: ok(all(v in str(e) for v in S.ENV_OVERRIDES), "second pass B: a real run refuses while a test folder override is set")
ok(refused(S.design, True) and refused(S.heldback, True), "second pass B: both real runs refuse with an override set")
saved = {v: os.environ.pop(v) for v in S.ENV_OVERRIDES}
try: S.require_no_override(); ok(True, "second pass B: no override, no refusal")
except S.Refused: ok(False, "second pass B: no override, no refusal")
os.environ.update(saved)

# ---- guards
try: S.design(require_push=True); ok(False, "unpushed hashes are refused")
except S.Refused: ok(True, "unpushed hashes are refused")
except Exception as e: ok(False, f"unpushed hashes are refused ({e})")
ok(S.out_dir(True) == C.HERE and S.out_dir(False) == C.OUTDIR != C.HERE, "audit 1: the real run uses research_rig/, whatever RESULTS_11_DIR says")
real_pb, real_repo = S.pushed_bytes, S.REPO
before_files = set(os.listdir(C.HERE))
S.pushed_bytes = lambda rel: None
ok(refused(S.design, True) and refused(S.heldback, True), "audit 3: with no frozen plan both real runs are refused")
S.pushed_bytes = lambda rel: b"{}" if rel.endswith("results_11_design.json") else None
ok(refused(S.design, True), "audit 3: --design is refused when results_11_design.json is in origin/main")
S.pushed_bytes = lambda rel: b"{}" if rel.endswith(S.HELDBACK_LOCK) else None
ok(refused(S.heldback, True), "audit 2: --heldback is refused when the lock record is in origin/main")
S.pushed_bytes = lambda rel: b"{}" if rel.endswith(S.HELDBACK_OUT) else None
ok(refused(S.heldback, True), "audit 2: --heldback is refused when results_11_heldback.json is in origin/main")
ok(set(os.listdir(C.HERE)) == before_files, "the refused real runs wrote nothing into research_rig/")
import yaml
fake = os.path.join(TMP, "repo"); os.makedirs(os.path.join(fake, "research_rig")); open(os.path.join(fake, S.FROZEN_PLAN), "w").write("plan\n"); S.REPO = fake
good = yaml.safe_dump({k: dict(value=v) for k, v in S.config_now().items()}).encode()
bad = yaml.safe_dump({k: dict(value=(dict(v, seed=12) if k == "replay_11_statistics" else v)) for k, v in S.config_now().items()}).encode()
S.pushed_bytes = lambda rel: b"plan\n" if rel == S.FROZEN_PLAN else good if rel == "config/thresholds.yaml" else None
try: S.require_frozen(); ok(True, "audit 3: the frozen plan and config as in origin/main pass")
except S.Refused as e: ok(False, f"audit 3: the frozen plan and config as in origin/main pass ({e})")
S.pushed_bytes = lambda rel: b"plan, changed\n" if rel == S.FROZEN_PLAN else good if rel == "config/thresholds.yaml" else None
ok(refused(S.require_frozen), "audit 3: a plan that differs from origin/main is refused")
S.pushed_bytes = lambda rel: b"plan\n" if rel == S.FROZEN_PLAN else bad if rel == "config/thresholds.yaml" else None
ok(refused(S.require_frozen), "audit 3: replay_11_* keys that differ from origin/main are refused")
S.pushed_bytes, S.REPO = real_pb, real_repo
af = os.path.join(C.EDGAR, f"answers_11_design_{SMALL[0]}.jsonl"); keep = open(af).read(); open(af, "a").write("\n")
try: S.design(require_push=False); ok(False, "a changed answers file is refused")
except S.Refused: ok(True, "a changed answers file is refused")
open(af, "w").write(keep)

# ---- returns
T = S.trades(events, C.trading_days())
e = events[3]; c = C.th("replay_11_costs")["bps_per_side"]["500"] / 1e4; g = (1 + (3 % 6 - 2) / 100) ** 5 - 1
ok(abs(T[e["event_id"]]["net"]["H5"] - ((1 + g) * (1 - c) / (1 + c) - 1)) < 1e-12, "H5 net return: 5th close over entry open, cost on both sides")
ok(abs(T[e["event_id"]]["gross"]["H1"] - 0.01) < 1e-12, "H1 is the entry day's close")
ok(T[events[5]["event_id"]]["stopped"]["H5"] and not T[events[5]["event_id"]]["stopped"]["H1"], "a stock whose bars stop exits at its last close and is flagged")
i5 = days.index(events[5]["entry_day"]); want = (100.5 + i5 + 2) / (100 + i5) - 1
ok(abs(T[events[5]["event_id"]]["spy"]["H5"] - want) < 1e-12, "audit 11: a stopped trade's SPY return ends on the stock's own last day")
e12 = events[12]; ok(abs(T[e12["event_id"]]["cost"] - C.th("replay_11_costs")["bps_per_side"]["400"] / 1e4) < 1e-15, "the 400's cost is used for a 400 event")
short = [dict(events[0], entry_day=days[-2])]
try: S.trades(short, C.trading_days()); ok(False, "prices that end before an exit are refused")
except S.Refused: ok(True, "prices that end before an exit are refused")

# ---- large overnight moves inside the hold (replay_11_overnight), and the side results without flagged or stopped trades
OVc = C.th("replay_11_overnight")
ent = days[5]; i0 = days.index(ent)
rows = {x: (10.0, 10.0) for x in days}
rows[days[i0 - 1]] = (10.0, 5.0)                      # a halving before entry: an earnings gap, not inside the hold
rows[days[i0 + 2]] = (5.0, 5.0)                       # close 10 on day 2 of the hold, next open 5: inside H5, after H1
for x in days[i0 + 3:]: rows[x] = (5.0, 5.0)
write_px("JMP", rows); write_px("EDG", {x: (10.0 * (0.70 if x == days[i0 + 1] else 1.0), 10.0) for x in days})
ev_j = dict(events[0], event_id="jump00000000", symbol="JMP", entry_day=ent); ev_e = dict(events[0], event_id="edge00000000", symbol="EDG", entry_day=ent)
TJ = S.trades([ev_j, ev_e], C.trading_days())
ok(TJ["jump00000000"]["overnight"]["H5"] and not TJ["jump00000000"]["overnight"]["H1"], "a large overnight move inside the hold is flagged, and only for the hold that holds it")
ok(len(TJ["jump00000000"]["overnight"]["H5"]) == 1, "a gap before the entry open is not inside the hold")
ok(not TJ["edge00000000"]["overnight"]["H5"], "a ratio exactly at ratio_min is not flagged")
ok(C.overnight_moves({"a": (1, 10.0), "b": (14.6, 1)}, ["a", "b"], OVc["ratio_min"], OVc["ratio_max"]), "a ratio above ratio_max is flagged")
TF = {f"e{i}": dict(list="500", cost=0.0, gross={"H5": g}, net={"H5": g}, spy={"H5": 0.0}, stopped={"H5": i == 3}, overnight={"H5": ["d to d 0.5"] if i == 0 else []})
      for i, g in enumerate([-0.5, 0.02, 0.01, 0.04, 0.0, 0.0])}
jf = S.judge(TF, list(TF), ["e0", "e1", "e3"], "H5", "t")
w = jf["without_overnight_flagged_not_judged"]; ws = jf["without_stopped_not_judged"]
ok(jf["buys"] == 3 and abs(jf["mean"] - (-0.5 + 0.02 + 0.04) / 3) < 1e-12, "the judged result keeps flagged and stopped trades")
ok(w["buys"] == 2 and abs(w["mean"] - 0.03) < 1e-12 and abs(w["mean_all_a"] - 0.07 / 5) < 1e-12, "without overnight-flagged: left out of the buys and of yardstick (a)")
ok(ws["buys"] == 2 and abs(ws["mean"] - (-0.24)) < 1e-12, "without stopped: left out the same way")
ok(jf["overnight_flagged"] == 1 and list(jf["overnight_flagged_trades"]) == ["e0"], "flagged trades are listed")

# ---- split check on made-up bars
import split_check_11 as SC
fake = {"UP": {"2026-06-10": (100.0, 100.0), "2026-06-11": (100.5, 101.0)}, "RAW": {"2026-06-10": (400.0, 400.0), "2026-06-11": (100.5, 101.0)}}
r = SC.check(lambda s: fake.get(s, {}), [("UP", 4, "2026-06-11", 400.0, []), ("RAW", 4, "2026-06-11", 400.0, []), ("NONE", 2, "2026-06-11", None, [])])
ok(r[0]["adjusted"] and not r[1]["adjusted"] and r[2]["found"] is False, "split check: an adjusted file passes, an unadjusted jump fails, a missing file is reported")

# ---- set-ups (heldback stage 2 needs no prices)
A = {SMALL[0]: {"x": 1}, SMALL[1]: {"x": 2}, SMALL[2]: {"x": 0}, STRONG: {"x": -2}}
ok(S.setup_scores("middle", A, ["x"])["x"] == 1, "middle is the median of the three")
ok(S.setup_scores("cascade", A, ["x"])["x"] == -2, "cascade uses the strong reader when the small readers disagree")
A2 = {SMALL[0]: {"x": 1}, SMALL[1]: {"x": 2}, SMALL[2]: {"x": 1}, STRONG: {"x": -2}}
ok(S.setup_scores("cascade", A2, ["x"])["x"] == 1, "cascade keeps the median when they agree")
ok(S.disagree([1, 1, 2]) is False and S.disagree([0, 0, 2]) is True and S.disagree([-1, 1, 1]) is True, "disagreement: buy and skip split, or a spread of 2")

# ---- design scoring and the choosing rule
R = S.design(require_push=False)
ok(SMALL[1] not in R["qualified_setups"] and R["setups"][SMALL[1]]["H5"]["buy_share"] < 0.2, "a set-up that buys under 20% does not qualify, however good")
ok(R["setups"]["middle"]["H5"]["minus_a"] == R["setups"][SMALL[0]]["H5"]["minus_a"], "made-up tie: middle equals the first small reader")
ok(R["chosen_setup"] == SMALL[0], "the choosing rule picks the best qualified H5 edge over (a), and a tie goes to the cheaper set-up")
ok(SMALL[2] not in R["qualified_setups"], "a set-up that buys everything is outside the buy-share window")
ok(R["setups"][SMALL[2]]["H5"]["minus_a"] == 0, "buying everything equals yardstick (a)")
ok(0 <= R["agreement"]["unanimous_buy_or_skip"] <= 1 and "fleiss_kappa_buy_skip" in R["agreement"], "agreement is measured")
ok(refused(S.design, False), "audit 3: a second design run is refused")
ok(R["remembered_zeroed_events"][STRONG] == [mem_id] and R["remembered_zeroed_events"][SMALL[0]] == [], "second pass C: the zeroed event ids are listed per reader")
g = R["setups"][STRONG]["H5"]["scores_as_given_not_judged"]
ok(g["buys"] == R["setups"][STRONG]["H5"]["buys"] + 1, "second pass C: the side line uses the scores as given (one more buy)")
dsym = {e["symbol"] for e in events if e["event_id"] in set(ids_design)}
ok(R["prices_read"]["files"] == len(dsym) + 1 and len(R["prices_read"]["sha256"]) == 64, "second pass B: the result holds one digest over the price files read, SPY included")
d0 = S.prices_digest([byid[i] for i in ids_design]); pf = C.price_path(byid[ids_design[0]]["symbol"]); kp = open(pf).read(); open(pf, "a").write("\n")
ok(S.prices_digest([byid[i] for i in ids_design])["sha256"] != d0["sha256"], "second pass B: a changed price file changes the digest"); open(pf, "w").write(kp)
ok(R["config"] == S.config_now() and "replay_11_overnight" in R["config"], "the design result stores every replay_11_* key")
Ac = {SMALL[0]: {"a": 1, "b": 1, "c": 1}, SMALL[1]: {"a": -1, "b": 0, "c": 2}, SMALL[2]: {"a": 0, "b": 1, "c": 2}, STRONG: {"b": 2}}
ag = S.agreement(Ac, ["a", "b", "c"])
ok(ag["spearman"][f"{SMALL[0]}~{SMALL[1]}"] is None and ag["spearman"][f"{SMALL[1]}~{STRONG}"] is None and ag["buy_share"][STRONG] == 1.0, "audit 9, 10: a constant reader or too few shared events gives None, not NaN; a partial strong reader is handled")
try: json.dumps(ag, allow_nan=False); ok(True, "audit 10: agreement writes as strict JSON")
except ValueError: ok(False, "audit 10: agreement writes as strict JSON")

# ---- held-back guards
try: S.heldback(require_push=False); ok(False, "held-back without its answers is refused")
except (S.Refused, FileNotFoundError): ok(True, "held-back without its answers is refused")
open(os.path.join(C.OUTDIR, "results_11_heldback.json"), "w").write("{}")
try: S.heldback(require_push=False); ok(False, "a second held-back run is refused")
except S.Refused: ok(True, "a second held-back run is refused")
os.remove(os.path.join(C.OUTDIR, "results_11_heldback.json"))
open(os.path.join(C.OUTDIR, S.HELDBACK_LOCK), "w").write("{}")
ok(refused(S.heldback, False), "audit 2: with the output deleted, the lock record alone refuses a held-back run")
os.remove(os.path.join(C.OUTDIR, S.HELDBACK_LOCK))

# ---- full held-back run with the chosen single reader
hb = [e for e in events if e["half"] == "heldback"]; hbins = P.deal(hb, "heldback")
for f in P.write_folders("heldback", SMALL[0], hbins): answer(f, lambda e, i: plan[SMALL[0]](e)); K.check(f)
K.collect("heldback")
R2 = S.heldback(require_push=False)
ok(R2["chosen_setup"] == SMALL[0] and R2["results"]["H5"]["too_few_to_judge"] and R2["results"]["H5"]["pass"] is False, "fewer than min_buys buys is too few to judge, not a pass")
ok(set(R2["results"]["H5"]["by_list_not_judged"]) <= {"400", "600"}, "each list is reported alone")
ok(os.path.exists(os.path.join(C.OUTDIR, S.HELDBACK_LOCK)), "audit 2: the held-back run writes its lock record")
os.remove(os.path.join(C.OUTDIR, S.HELDBACK_OUT)); ok(refused(S.heldback, False), "audit 2: deleting the output does not let the held-back run go again")
DP = os.path.join(C.OUTDIR, S.DESIGN_OUT); D0 = json.load(open(DP))
real_cfg = S.config_now; S.config_now = lambda: dict(real_cfg(), replay_11_costs={"changed": 1}); os.remove(os.path.join(C.OUTDIR, S.HELDBACK_LOCK))
ok(refused(S.heldback, False), "audit 3: config that differs from the design run's is refused"); S.config_now = real_cfg

# ---- audit 9: the cascade's strong reader must answer the disagreements and the audit
json.dump(dict(D0, chosen_setup="cascade"), open(DP, "w"), allow_nan=False)
sc = {SMALL[0]: plan[SMALL[0]], SMALL[1]: plan[SMALL[0]], SMALL[2]: lambda i: 2}
for rd in SMALL[1:]:
    for f in P.write_folders("heldback", rd, hbins): answer(f, lambda e, i, rd=rd: sc[rd](e)); K.check(f)
hids = sorted(e["event_id"] for e in hb); dis, audit = S.cascade_strong_set(hids, {r: {i: sc[r](i) for i in hids} for r in SMALL})
ok(len(audit) == 1 and len(dis) == 6, "audit 9: the made-up cascade has 6 disagreements and 1 audited agreed event")
def strong_reads(todo):
    root = os.path.join(C.READING, "heldback", STRONG); shutil.rmtree(root, ignore_errors=True)
    if os.path.exists(root + ".expected.json"): os.remove(root + ".expected.json")
    for f in P.write_folders("heldback", STRONG, P.deal([byid[i] for i in todo], "heldback-strong")): answer(f, lambda e, i: 2); K.check(f)
    json.dump(dict(disagreements=dis, audit=sorted(set(todo) - set(dis))), open(os.path.join(C.READING, "heldback", "strong_reads.json"), "w"))
    os.remove(os.path.join(C.OUTDIR, "answers_11_heldback_hashes.json")); K.collect("heldback")
strong_reads(dis)
for n in (S.HELDBACK_OUT, S.HELDBACK_LOCK):
    if os.path.exists(os.path.join(C.OUTDIR, n)): os.remove(os.path.join(C.OUTDIR, n))
ok(refused(S.heldback, False) and not os.path.exists(os.path.join(C.OUTDIR, S.HELDBACK_LOCK)), "audit 9: a strong reader that skipped the audit is refused, before the lock and before any price")
strong_reads(dis + audit); R3 = S.heldback(require_push=False)
ok(R3["audit"] == dict(disagreements=6, audit=1, note=R3["audit"]["note"]) and R3["agreement"]["strong_agreed_events_compared"] == 1, "audit 9: with the audit answered, the cascade runs and the audit is compared")
ok(R3["remembered_set_to_zero"] and all(v == 0 for v in R3["remembered_set_to_zero"].values()), "audit 4: the result counts remembered answers per reader")
ok("scores_as_given_not_judged" in R3["results"]["H5"] and "prices_read" in R3 and R3["remembered_zeroed_events"][STRONG] == [], "second pass B, C: the held-back result has the as-given side line, the zeroed ids and the price digest")

shutil.rmtree(TMP)
print(f"\n{len(fails)} failed" if fails else "\nall passed"); sys.exit(1 if fails else 0)
