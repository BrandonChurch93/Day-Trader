"""Builds the S&P 500 member list by date for draft plan 14 and compares it with a second public source.

Sources (copies kept off-repo in ~/workspace/rig/data/replay_14/src/, fetched 2026-11-25):
  A (main)  Wikipedia "List of S&P 500 companies" (current members) and "Historical components of the S&P 500"
            (dated additions and removals). https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
            https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500
  B (check) fja05680/sp500 on GitHub, "S&P 500 Historical Components & Changes (Updated).csv": the full member list on
            each change day. https://github.com/fja05680/sp500 (its last row is 2026-08-18)

Method: start from source A's current list and undo source A's changes one date at a time, going back to the plan's
start. Within one date: undo additions, then the hand-listed ticker changes below, then removals. Each member is
tracked as one company (an "entity"), so a ticker used by two companies (IR, Q, AA, FOXA) never joins them.

Reads no price. It reads only the date spans of the stored bar files (bar_spans.json) to choose which file a row uses.

Writes, off-repo, to ~/workspace/rig/data/replay_14/:
  members.csv        date_from, date_to (not included), ticker_then, ticker_feed, company, feed_from, feed_to,
                     company_id, entity, note. feed_from / feed_to: the feed file is used only between these days
                     (blank = no limit); they cut out days when the file holds another company.
  members_note.md    sources, member count on each month-end, every disagreement with source B.

Usage, from research_rig/: python3 build_members_14.py"""
import os, io, csv, json, bisect, datetime as dt
from collections import defaultdict, Counter
import pandas as pd
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(os.path.expanduser("~"), "workspace", "rig", "data", "replay_14")
SRC = os.path.join(DATA, "src")
P = yaml.safe_load(open(os.path.join(REPO, "config", "thresholds.yaml")))["replay_14_plan"]["value"]
START, END = str(P["start"]), str(P["end"])
END_EXCL = (dt.date.fromisoformat(END) + dt.timedelta(days=1)).isoformat()
WIKI_CUR = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKI_HIST = "https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500"
FJA = "https://github.com/fja05680/sp500"

# Same company, new ticker, and source A has no row for it. (old, new, first day of the new ticker, where it is
# stated). The day only moves the label ticker_then; it changes neither membership nor which price file is used.
# "B" means the first change day on which source B shows the new ticker (B's rows are change days, so the true day can
# be earlier). The list is what source A's list needed to roll back without a missing ticker, plus the ones source B shows.
RENAMES = [
    ("UA", "UAA", "2016-04-08", "A row 2016-04-08: Under Armour issued a second class; the class A became UAA (B shows UAA)"),
    ("UA.C", "UA", "2016-12-07", "class C label; day UNKNOWN exactly, label only (A uses UA.C on 2016-04-08, B uses UA)"),
    ("TSO", "ANDV", "2017-08-01", "Tesoro renamed Andeavor; the TSO file ends 2017-07-31 and the ANDV file starts 2017-08-01 (A and B use ANDV throughout)"),
    ("DLPH", "APTV", "2017-12-05", "SEC 8-K https://www.sec.gov/Archives/edgar/data/1521332/000119312517363912/d453817d8k.htm: Delphi Automotive renamed Aptiv, trading as APTV from 2017-12-05"),
    ("KORS", "CPRI", "2019-01-02", "B"),
    ("FOXA", "TFCFA", "2019-03-19", "A: 21st Century Fox class A changed ticker FOXA to TFCFA effective March 19"),
    ("FOX", "TFCF", "2019-03-19", "A: 21st Century Fox class B changed ticker FOX to TFCF effective March 19"),
    ("BHGE", "BKR", "2019-10-18", "plan 12 rename list (SEC 10-K); B. A labels it BKR from 2017-07-07"),
    ("HRS", "LHX", "2019-07-01", "B (Harris bought L3 and renamed itself L3Harris)"),
    ("TMK", "GL", "2019-08-08", "B"),
    ("HCP", "PEAK", "2019-11-05", "B"), ("SYMC", "NLOK", "2019-11-05", "B"),
    ("CBS", "VIAC", "2019-12-05", "B (CBS bought Viacom and renamed itself ViacomCBS)"),
    ("BBT", "TFC", "2019-12-09", "B (BB&T bought SunTrust and renamed itself Truist)"),
    ("JEC", "J", "2019-12-10", "B; plan 12 rename list"),
    ("IR", "TT", "2020-03-03", "B (Ingersoll-Rand plc renamed Trane Technologies; the new IR, formerly Gardner Denver, joined the same day per A)"),
    ("UTX", "RTX", "2020-04-03", "B (United Technologies bought Raytheon and renamed itself Raytheon Technologies)"),
    ("CTL", "LUMN", "2020-09-18", "B"),
    ("LB", "BBWI", "2021-08-03", "B"), ("COG", "CTRA", "2021-10-04", "B (Cabot bought Cimarex and renamed itself Coterra)"),
    ("VIAC", "PARA", "2022-02-17", "B"), ("BLL", "BALL", "2022-05-10", "B"),
    ("FB", "META", "2022-06-09", "B"), ("ANTM", "ELV", "2022-06-28", "B"),
    ("NLOK", "GEN", "2022-11-08", "B"), ("PKI", "RVTY", "2023-05-16", "B"),
    ("FISV", "FI", "2023-06-07", "B; plan 12 rename list"), ("RE", "EG", "2023-07-10", "B"),
    ("ABC", "COR", "2023-08-30", "B"), ("CDAY", "DAY", "2024-02-01", "B"),
    ("PEAK", "DOC", "2024-03-04", "B"), ("FLT", "CPAY", "2024-03-25", "B"),
    ("PARA", "PSKY", "2025-08-07", "B shows PSKY on 2025-08-08; the PSKY and SKYD files start 2025-08-07"),
    ("FI", "FISV", "2025-11-11", "plan 12 rename list (nasdaqtrader notice)"),
    ("MMC", "MRSH", "2026-01-14", "plan 12 rename list (Marsh McLennan notice); B"),
    ("BK", "BNY", "2026-05-21", "B"),
    ("SATS", "ECHO", "2026-06-25", "B shows SATS last on 2026-06-24 and A's current list shows ECHO; day UNKNOWN exactly, label only"),
    ("EQR", "VMRK", "2026-08-18", "B still shows EQR on 2026-08-18, its last row; the EQR file ends 2026-08-17; A's current list shows VMRK; day UNKNOWN exactly, label only"),
    ("PSKY", "SKYD", "2026-10-06", "the PSKY file ends 2026-10-05; A's current list shows SKYD; day UNKNOWN exactly, label only"),
]

# Source A keeps one line through these, but the plan counts them as a merger into a new company: the old history
# ends and the new company joins as new (plan 14, "Definitions fixed before the run"). (old, new, day the new one
# starts, note). Days from source B's change rows.
MERGERS = [
    ("PX", "LIN", "2018-10-31", "Praxair|Praxair and Linde AG combined into the new Linde plc; B ends PX on 2018-10-31; the LIN file starts 2018-10-31"),
    ("MYL", "VTRS", "2020-11-17", "Mylan|Mylan combined with Pfizer's Upjohn into the new Viatris; B ends MYL and starts VTRS on 2020-11-17"),
    ("WRK", "SW", "2024-07-08", "WestRock|Smurfit Kappa bought WestRock into the new Smurfit Westrock; B ends WRK and starts SW on 2024-07-08"),
]
# Source A has rows for these, as a removal and an addition. Same company: one history in the plan's sense. The rows
# stay separate; the price file below is what joins them. Listed in the note.
A_ROW_RENAMES = [("AA", "ARNC", "2016-11-01"), ("Q", "IQV", "2017-11-15"), ("DWDP", "DD", "2019-06-03"),
                 ("ARNC", "HWM", "2020-04-01"), ("WLTW", "WTW", "2022-01-10")]
# Source A rows that are a merger into a new company (kept as separate members, nothing to do): BHI to BKR 2017-07-07,
# DOW and DD into DWDP 2017-09-01.

# Which price file a row uses, and the days it may use, where the plain choice (the row's own last ticker) is wrong.
# Key: (ticker_then, the row's date_from or None for any). Value: (ticker_feed, feed_from, feed_to, note).
FEED = {
    ("AA", None): ("", "", "", "old Alcoa Inc. (renamed Arconic): the AA file is the new Alcoa from 2016-10-06 and the ARNC file starts 2016-11-01; no file holds this company's 2016 bars"),
    ("ARNC", None): ("ARNC", "", "2020-03-31", "the ARNC file holds the spun-off Arconic Corp from 2020-04-01, so it is cut there"),
    ("HWM", None): ("HWM", "", "", "same company as ARNC before 2020-04-01, but its earlier bars are in another file and files are not joined, so it cannot be ranked until the HWM file has twelve month-ends"),
    ("Q", "2017-08-29"): ("IQV", "", "", "QuintilesIMS, renamed IQVIA; history under IQV"),
    ("WLTW", None): ("WTW", "", "", "Willis Towers Watson; history under WTW"),
    ("DWDP", None): ("DD", "2017-09-01", "", "DowDuPont, renamed DuPont; the DD file before 2017-09-01 is the old DuPont, a different company"),
    ("DD", "2019-06-03"): ("DD", "2017-09-01", "", "the DD file before 2017-09-01 is the old DuPont"),
    ("DD", None): ("DD@2017-06-01", "", "2017-08-31", "old DuPont; the plain DD file before 2017-09-01 holds Dow Chemical's bars (its volumes are in fixed proportion to DOW@2017-06-01's), so the feed's file for the company that had DD on 2017-06-01 is used"),
    ("DOW", None): ("DOW", "", "2017-08-31", "Dow Chemical; last regular-way day 2017-08-31 (SEC https://www.sec.gov/Archives/edgar/data/0001666700/000119312517274834/d426905dex991.htm); the DOW file is flat with zero volume from 2017-09-01 to 2019-04-01 and is Dow Inc. after"),
    ("DOW", "2019-04-02"): ("DOW", "2019-04-02", "", "Dow Inc.; regular-way trading from 2019-04-02 (SEC https://www.sec.gov/Archives/edgar/data/1751788/000119312519095067/d716962dex991.htm); earlier DOW bars are not this company"),
    ("CBS", None): ("CBS", "", "", "the PARA file has zero volume before 2024, so CBS's own file is used"),
    ("VIAC", None): ("VIAC", "", "", "the PARA file has zero volume before 2024, so ViacomCBS's own file is used"),
    ("PARA", None): ("PARA@2023-06-01", "", "", "Paramount Global; the plain PARA file has zero volume before 2024, so the feed's file for the company that had PARA on 2023-06-01 is used"),
    ("TFCFA", None): ("FOXA", "", "2019-03-18", "21st Century Fox class A; the FOXA file from 2019-03-19 is the new Fox Corporation"),
    ("TFCF", None): ("FOX", "", "2019-03-18", "21st Century Fox class B; the FOX file from 2019-03-19 is the new Fox Corporation"),
    ("FOXA", "2019-03-19"): ("FOXA", "2019-03-19", "", "new Fox Corporation; earlier FOXA bars are 21st Century Fox"),
    ("FOX", "2019-03-19"): ("FOX", "2019-03-19", "", "new Fox Corporation; earlier FOX bars are 21st Century Fox"),
    ("FOXA", None): ("FOXA", "", "2019-03-18", "21st Century Fox class A; the FOXA file from 2019-03-19 is the new Fox Corporation"),
    ("FOX", None): ("FOX", "", "2019-03-18", "21st Century Fox class B; the FOX file from 2019-03-19 is the new Fox Corporation"),
    ("JCI", None): ("JCI", "2016-09-06", "", "Tyco bought Johnson Controls Inc. on 2016-09-02 and took its name and ticker; which company the JCI file holds before then is UNKNOWN, so it is cut at the first day after the TYC file's last bar (2016-09-02)"),
    ("LIN", None): ("LIN", "2018-10-31", "", "new Linde plc"),
    ("SW", None): ("SW", "2024-07-08", "", "new Smurfit Westrock; the SW file before 2024-07-08 holds WestRock's bars"),
    ("PX", None): ("PX", "", "2018-10-31", "Praxair; the PX file later holds another company"),
    ("UA.C", None): ("UA", "2016-04-08", "", "Under Armour class C; the UA file before 2016-04-08 is the class A"),
    ("UA", "2016-12-07"): ("UA", "2016-04-08", "", "Under Armour class C; the UA file before 2016-04-08 is the class A"),
    ("UA", None): ("UAA", "", "", "Under Armour class A before 2016-04-08; its bars before then are in the UA file, which is not used (pre-plan days only)"),
    ("DLPH", None): ("DLPH", "", "2017-12-04", "Delphi Automotive (renamed Aptiv); the DLPH file from 2017-12-05 is the spun-off Delphi Technologies (SEC 8-K)"),
    ("GPS", None): ("GAP", "", "", "Gap Inc.; the GPS file is empty, history under GAP"),
    ("CCE", None): ("", "", "", "Coca-Cola Enterprises, merged into the new Coca-Cola European Partners 2016-05-28; the CCEP file holds both; left without a file (it left before the first ranking day)"),
    ("CMCSK", None): ("", "", "", "Comcast class K; left before the plan starts"),
}
SHARE_CLASS = {"GOOG": "Alphabet", "GOOGL": "Alphabet", "NWS": "News Corp", "NWSA": "News Corp",
               "DISCA": "Discovery", "DISCK": "Discovery", "UA": "Under Armour", "UAA": "Under Armour", "UA.C": "Under Armour",
               "CMCSA": "Comcast", "CMCSK": "Comcast"}

def load_a():
    cur = pd.read_html(io.StringIO(open(os.path.join(SRC, "wiki_sp500.html")).read()))[0]
    ch = pd.read_html(io.StringIO(open(os.path.join(SRC, "wiki_hist.html")).read()))[0]
    ch.columns = ["date", "add", "add_name", "rem", "rem_name", "reason", "refs"]
    ch["date"] = pd.to_datetime(ch["date"]).dt.date.astype(str); ch = ch.fillna("")
    return cur, ch

def split(x): return [t.strip().replace("-", ".") for t in str(x).split(",") if t.strip()]

def roll():
    cur, ch = load_a()
    names = dict(zip(cur.Symbol.str.replace("-", "."), cur.Security))
    ents = {}                     # eid -> dict(start, end, labels=[(label, from)], name)
    state = {}                    # label -> eid, members on the day being undone
    for s in cur.Symbol:
        s = s.replace("-", "."); e = len(ents); ents[e] = dict(start=None, end=END_EXCL, labels=[(s, None)], name=names[s]); state[s] = e
    ev = defaultdict(lambda: dict(add=[], rem=[], ren=[], mer=[]))
    for _, r in ch[ch.date > START].iterrows():
        for a in split(r["add"]): ev[r["date"]]["add"].append((a, r["add_name"]))
        for x in split(r["rem"]): ev[r["date"]]["rem"].append((x, r["rem_name"]))
    for o, n, d, _ in RENAMES:
        if d > START: ev[d]["ren"].append((o, n))
    for o, n, d, note in MERGERS: ev[d]["mer"].append((o, n, note.split("|")[0]))
    problems = []
    for d in sorted(ev, reverse=True):
        E = ev[d]
        for a, _ in E["add"]:
            if a not in state:   # renamed later under a label on the list: find the member that had this ticker
                hit = [l for l, e in state.items() if any(x == a for x, _ in ents[e]["labels"])]
                if len(hit) != 1: problems.append(f"{d}: added {a} is not in the list being rolled back"); continue
                e = state.pop(hit[0]); labs = ents[e]["labels"]; k = [x for x, _ in labs].index(a)
                ents[e]["labels"] = [(a, None)] + labs[k + 1:]; ents[e]["start"] = d; continue
            ents[state.pop(a)]["start"] = d
        for o, n in E["ren"]:
            if n not in state: problems.append(f"{d}: renamed {o} to {n}, but {n} is not in the list"); continue
            e = state.pop(n); ents[e]["labels"][0] = (n, d); ents[e]["labels"].insert(0, (o, None)); state[o] = e
        for o, n, nm in E["mer"]:
            if n not in state: problems.append(f"{d}: merger {o} to {n}, but {n} is not in the list"); continue
            ents[state.pop(n)]["start"] = d
            e = len(ents); ents[e] = dict(start=None, end=d, labels=[(o, None)], name=nm); state[o] = e
        for x, nm in E["rem"]:
            if x in state: problems.append(f"{d}: removed {x} is already in the list"); continue
            e = len(ents); ents[e] = dict(start=None, end=d, labels=[(x, None)], name=nm); state[x] = e
    for e in state.values(): ents[e]["start"] = START
    return ents, problems, ch

GAP_DAYS = 5   # a file whose bars skip more than this many SPY trading days is cut at the gap (another company may follow)

def bars_dir():
    return os.path.join(DATA, "bars")

def file_dates():
    """{symbol: sorted list of dates with a real trade}. Dates only, no price. Bars that are not trades (zero volume, or
    a run of five or more identical rows; common_14.not_trades) are left out, so such a run cuts a file like a gap."""
    from common_14 import not_trades
    B = bars_dir(); out = {}
    for f in os.listdir(B):
        with open(os.path.join(B, f)) as fh: rows = list(csv.DictReader(fh))
        bad = not_trades(rows)
        out[f[:-4]] = [r["date"] for r in rows if r["date"] not in bad]
    return out

def gap_cut(d, spy_idx, a, ff, ft):
    """feed_from / feed_to after cutting the file at gaps of more than GAP_DAYS trading days around the row start a."""
    ii = [spy_idx[x] for x in d if x in spy_idx and (not ff or x >= ff) and (not ft or x <= ft)]
    ds = [x for x in d if x in spy_idx and (not ff or x >= ff) and (not ft or x <= ft)]
    if not ds: return ff, ft, ""
    k = bisect.bisect_left(ds, a); notes = []
    for t in range(max(k + 1, 1), len(ds)):          # gaps after the row start
        if ii[t] - ii[t - 1] > GAP_DAYS: ft = ds[t - 1]; notes.append(f"cut after {ds[t - 1]} at a gap in the file"); break
    for t in range(min(k, len(ds) - 1), 0, -1):
        if ii[t] - ii[t - 1] > GAP_DAYS: ff = ds[t]; notes.append(f"cut before {ds[t]} at a gap in the file"); break
    return ff, ft, "; ".join(notes)

def share(d, spy, a, b):
    """Share of SPY trading days in [a, b) on which the file has a bar."""
    want = bisect.bisect_left(spy, b) - bisect.bisect_left(spy, a)
    have = bisect.bisect_left(d, b) - bisect.bisect_left(d, a)
    return have / want if want else 0.0

COVER = 0.9   # a file "covers" a row when it has a bar on at least this share of the row's trading days

def rows_from(ents):
    """One row per company and ticker label. Price file: the company's latest ticker's file for every row it covers
    (plan 12: the feed keeps a renamed company's history under its new ticker); rows it does not cover use the one file,
    among the company's tickers, that covers most of those rows' days. Files are never joined."""
    FD = file_dates(); spy = FD["SPY"]; spy_idx = {x: i for i, x in enumerate(spy)}
    rows = []
    for e, x in sorted(ents.items(), key=lambda kv: (kv[1]["start"], kv[1]["labels"][0][0])):
        a, b = max(x["start"], START), min(x["end"], END_EXCL)
        if a >= b: continue
        labs = x["labels"]; names = [l for l, _ in labs]; latest = names[-1]
        parts = []
        for i, (lab, f) in enumerate(labs):
            fa = max(a, f or a); fb = min(b, labs[i + 1][1]) if i + 1 < len(labs) else b
            if fa < fb: parts.append((lab, fa, fb))
        cov = [share(FD.get(latest) or [], spy, fa, fb) >= COVER for _, fa, fb in parts]
        rest = [p for p, c in zip(parts, cov) if not c]
        alt = ""
        if rest:
            score = {lab: sum(share(FD.get(lab) or [], spy, fa, fb) * (bisect.bisect_left(spy, fb) - bisect.bisect_left(spy, fa)) for _, fa, fb in rest) for lab in names}
            alt = max(reversed(names), key=lambda l: score[l]) if max(score.values()) > 0 else ""
        for (lab, fa, fb), c in zip(parts, cov):
            key = (lab, fa) if (lab, fa) in FEED else (lab, None)
            if key in FEED: feed, ff, ft, note = FEED[key]
            else: feed, ff, ft, note = (latest if c else alt), "", "", ""
            if feed:
                ff, ft, gnote = gap_cut(FD.get(feed) or [], spy_idx, fa, ff, ft)
                note = "; ".join(n for n in (note, gnote) if n)
            cid = SHARE_CLASS.get(lab)
            if lab in ("FOX", "FOXA", "TFCF", "TFCFA"): cid = "21st Century Fox" if x["name"].startswith(("21st", "Twenty")) or lab.startswith("TFCF") else "Fox Corporation"
            rows.append(dict(date_from=fa, date_to=fb, ticker_then=lab, ticker_feed=feed, company=x["name"],
                             feed_from=ff, feed_to=ft, company_id=cid or f"E{e}", entity=f"E{e}", note=note))
        # a company on two files: the later file is used only from its first row, since its earlier bars are not this
        # company's (this company's earlier bars are in the other file)
        mine = [r for r in rows if r["entity"] == f"E{e}"]
        seen = []
        for r in mine:
            if r["ticker_feed"] and seen and r["ticker_feed"] not in seen:
                first = min(q["date_from"] for q in mine if q["ticker_feed"] == r["ticker_feed"])
                for q in mine:
                    if q["ticker_feed"] == r["ticker_feed"] and (not q["feed_from"] or q["feed_from"] < first):
                        q["feed_from"] = first; q["note"] = "; ".join(n for n in (q["note"], f"file used only from {first}: its earlier bars may be another company's; this company's earlier bars are in another file") if n)
            if r["ticker_feed"] and r["ticker_feed"] not in seen: seen.append(r["ticker_feed"])
    return rows

def month_ends(days):
    out = []
    for i, d in enumerate(days):
        if i + 1 == len(days) or days[i + 1][:7] != d[:7]: out.append(d)
    return out

def members_on(rows, d): return [r for r in rows if r["date_from"] <= d < r["date_to"]]

def compare_b(rows, ents):
    """Disagreements with source B on each of B's change days, after mapping both through the same tickers. A ticker
    differs only in label when it is the same company under a rename on the list above; those are not counted."""
    F = pd.read_csv(os.path.join(SRC, "fja_SandP_500_Historical_Components_and_Changes_Updated.csv"))
    F = F[(F.date >= START) & (F.date <= END)]
    canon = {}
    for o, n, d, _ in RENAMES: canon[o] = n
    def c(t):
        seen = set()
        while t in canon and t not in seen: seen.add(t); t = canon[t]
        return t
    out = Counter(); first = {}; last = {}
    for d, t in zip(F.date, F.tickers):
        b = {c(x.replace("-", ".")) for x in t.split(",")}
        a = {c(r["ticker_then"]) for r in members_on(rows, d)}
        for x in a - b: k = ("only in A (Wikipedia)", x); out[k] += 1; first.setdefault(k, d); last[k] = d
        for x in b - a: k = ("only in B (fja05680)", x); out[k] += 1; first.setdefault(k, d); last[k] = d
    return out, first, last, len(F), F.date.min(), F.date.max()

def main():
    ents, problems, ch = roll()
    rows = rows_from(ents)
    cols = ["date_from", "date_to", "ticker_then", "ticker_feed", "company", "feed_from", "feed_to", "company_id", "entity", "note"]
    with open(os.path.join(DATA, "members.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); [w.writerow(r) for r in rows]
    days = [r["date"] for r in csv.DictReader(open(os.path.join(bars_dir(), "SPY.csv")))]
    me = month_ends(days)
    counts = [(d, len(members_on(rows, d)), len({r["company_id"] for r in members_on(rows, d)})) for d in me]
    dis, first, last, nb, b0, b1 = compare_b(rows, ents)
    L = ["# Plan 14 member list: sources, counts, disagreements", "",
         f"Made by research_rig/build_members_14.py on {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC. Counts and dates only.", "",
         "## Sources", "",
         f"- A, main: Wikipedia current list ({WIKI_CUR}) and dated changes ({WIKI_HIST}), copies taken 2026-11-25. The list was rolled back from today's {sum(1 for e in ents.values() if e['end'] == END_EXCL)} lines one change date at a time.",
         f"- B, check: fja05680/sp500 ({FJA}), file 'S&P 500 Historical Components & Changes (Updated).csv', {nb} change days from {b0} to {b1}. After {b1} only source A is used.",
         "- Ticker changes with no row in A: the RENAMES list in build_members_14.py, each with where it is stated.",
         "- Price files: which file each row uses, and cut days, are in members.csv (ticker_feed, feed_from, feed_to, note).", "",
         "## Problems while rolling back source A", ""]
    L += [f"- {p}" for p in problems] or ["- none"]
    L += ["", "## Treated as one company (same company, new ticker; source A has a removal and an addition)", ""]
    L += [f"- {o} to {n} on {d}" for o, n, d in A_ROW_RENAMES]
    L += ["", "## Treated as a merger into a new company (source A keeps one line; history ends, new company joins as new)", ""]
    L += [f"- {o} to {n} on {d}: {note.split('|')[1]}" for o, n, d, note in MERGERS]
    L += ["- Also from rows in source A: BHI to BKR 2017-07-07; DOW and DD into DWDP 2017-09-01.",
          "- FMC Technologies into the new TechnipFMC (FTI), 2017-01: source A keeps one line; the FTI file starts 2017-01-17, so the old company's 2016 days have no bars and TechnipFMC cannot be ranked until it has twelve month-ends.",
          "- Johnson Controls and Tyco, 2016-09-02: the JCI file is used only from 2016-09-06, because which company it holds before then is UNKNOWN.",
          "- Paramount Skydance (PSKY, now SKYD), 2025-08-07: source A keeps one line and the PARA file runs on, but the PSKY and SKYD files start 2025-08-07; rows from then use the SKYD file, so its history restarts there.", "",
          "## Two share classes of one company (only the first by ticker may be ranked or drawn)", ""]
    pairs = defaultdict(set)
    for r in rows:
        if not r["company_id"].startswith("E"): pairs[r["company_id"]].add(r["ticker_then"])
    L += [f"- {k}: {', '.join(sorted(v))}" for k, v in sorted(pairs.items())]
    L += ["", "## One company whose rows use more than one price file (files are not joined; the later file starts its own history)", ""]
    byent = defaultdict(list)
    for r in rows: byent[r["entity"]].append(r)
    for e, rs in byent.items():
        feeds = [r["ticker_feed"] for r in rs]
        if len(set(feeds)) > 1 or len({(r["feed_from"], r["feed_to"]) for r in rs}) > 1:
            L.append("- " + rs[0]["company"] + ": " + "; ".join(f"{r['ticker_then']} {r['date_from']} to {r['date_to']} uses {r['ticker_feed'] or 'no file'}" for r in rs))
    L += ["", "## Members on each month-end (lines; companies after joining share classes)", "", "| month-end | lines | companies |", "|---|---|---|"]
    L += [f"| {d} | {n} | {k} |" for d, n, k in counts]
    L += ["", f"Lines on a month-end: lowest {min(c[1] for c in counts)}, highest {max(c[1] for c in counts)}.", "",
          f"## Disagreements with source B ({nb} change days compared, {b0} to {b1})", "",
          "Counted in change days of B on which the ticker is in one source and not the other, with first and last such day.", "",
          "| side | ticker | days | first | last |", "|---|---|---|---|---|"]
    for (side, t), n in sorted(dis.items(), key=lambda kv: (first[kv[0]], kv[0][1])):
        L.append(f"| {side} | {t} | {n} | {first[(side, t)]} | {last[(side, t)]} |")
    # the same comparison on ranking-day month-ends only, B's list in force on that day
    F = pd.read_csv(os.path.join(SRC, "fja_SandP_500_Historical_Components_and_Changes_Updated.csv"))
    F = F[F.date <= END]; bd = list(F.date); bs = [set(t.split(",")) for t in F.tickers]
    canon = {o: n for o, n, d, _ in RENAMES}
    def cn(t):
        seen = set()
        while t in canon and t not in seen: seen.add(t); t = canon[t]
        return t
    L += ["", f"## Month-ends from 2017-01-31 to {b1} where the two lists differ (B's list in force that day)", "",
          "Label-only differences are a ticker the company had at another time (B often uses a later ticker for earlier days).", ""]
    nd = 0
    for d in me:
        if d < "2017-01-31" or d > b1: continue
        j = bisect.bisect_right(bd, d) - 1
        bb = {cn(x.replace("-", ".")) for x in bs[j]}; aa = {cn(r["ticker_then"]) for r in members_on(rows, d)}
        if aa != bb: nd += 1; L.append(f"- {d}: only in A {', '.join(sorted(aa - bb)) or 'none'}; only in B {', '.join(sorted(bb - aa)) or 'none'}")
    if not nd: L.append("- none")
    open(os.path.join(DATA, "members_note.md"), "w").write("\n".join(L) + "\n")
    print(f"rows {len(rows)}, problems {len(problems)}, month-end lines {min(c[1] for c in counts)}-{max(c[1] for c in counts)}, disagreements {len(dis)}")
    for p in problems: print(" ", p)

if __name__ == "__main__":
    main()
