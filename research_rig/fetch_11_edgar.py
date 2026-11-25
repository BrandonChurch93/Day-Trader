"""Collects the events for draft plan 11: 8-K filings with item 2.02 from S&P 500, MidCap 400 and SmallCap 600 members, and the
text of each press release. Runs no rule and reads no price. Raw files go to ~/workspace/rig/data/edgar_11/ (not the repo).
Prints counts only.

Stock lists: the constituents table of each Wikipedia list page, last revision before 2026-04-01, saved under data/edgar_11/
before any price was read:
  500  List of S&P 500 companies, revision 1345606266, 2026-03-27 01:30 UTC
  400  List of S&P 400 companies, revision 1346242889, 2026-03-30 19:25 UTC
  600  List of S&P 600 companies, revision 1346175333, 2026-03-30 10:21 UTC
The 500 and 600 tables carry a CIK. Most 400 rows carry only a ticker; those are matched to a CIK with the SEC's
company_tickers.json (saved 2026-11-25), and the 8 tickers that file no longer lists are matched by name with EDGAR's
company search on 2026-11-25 (MANUAL_CIK below). A CIK found in two lists is kept in the first (500, then 400, then 600).

Usage, from research_rig/:  python3 fetch_11_edgar.py      (resumes; finished files are not fetched again)
The event filters and the split are in prep_11.py summary.
SEC asks for a User-Agent with contact and at most 10 requests a second; this stays under 5."""
import sys, os, re, json, time, html, urllib.request, urllib.error, datetime as dt
from zoneinfo import ZoneInfo
OUT = os.environ.get("EDGAR_11_DIR", os.path.join(os.path.expanduser("~"), "workspace", "rig", "data", "edgar_11"))
UA = "Day-Trader research modernsoftworks@gmail.com"
LISTS = [("500", "sp500_rev1345606266.wiki", "List of S&P 500 companies, revision 1345606266, 2026-03-27 01:30 UTC"),
         ("400", "sp400_rev1346242889.wiki", "List of S&P 400 companies, revision 1346242889, 2026-03-30 19:25 UTC"),
         ("600", "sp600_rev1346175333.wiki", "List of S&P 600 companies, revision 1346175333, 2026-03-30 10:21 UTC")]
TICKER_FILE = "sec_company_tickers_20261125.json"
MANUAL_CIK = {"BLD": "0001633931", "GTLS": "0000892553", "JHG": "0001274173", "MASI": "0000937556",   # EDGAR company search by name,
              "NSA": "0001618563", "TCBI": "0001077428", "TMHC": "0001562476", "WBS": "0000801337"}  # 2026-11-25
START, END = "2026-04-01", "2026-11-20"; NY = ZoneInfo("America/New_York")
_last = [0.0]
import threading; _lock = threading.Lock()

def get(url, binary=False):
    """At most 4 requests a second across all threads."""
    for attempt in range(4):
        with _lock:
            wait = 0.25 - (time.time() - _last[0])
            if wait > 0: time.sleep(wait)
            _last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"}), timeout=60) as r:
                b = r.read(); return b if binary else b.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2 + 3 * attempt)
        except Exception:
            time.sleep(2 + 3 * attempt)
    return None

def members(fname):
    """(symbol, cik or None, how) for each row of a saved constituents table."""
    t = open(os.path.join(OUT, fname), encoding="utf-8").read()
    t = t[t.index('id="constituents"'):]; t = t[:t.index("\n|}")]
    rows = []
    for block in t.split("\n|-")[1:]:
        m = re.search(r"\{\{(?!Anchor\|)(?:NyseSymbol|NasdaqSymbol|BZX link|[A-Za-z ]+)\|\s*([A-Z.\-]+)\s*\}\}", block) or \
            re.search(r"\{\{#invoke:Stock tickers/\w+\|GetURL\|([A-Z.\-]+)\|", block)
        if not m: continue
        c = re.search(r"^\|\s*(\d{10})\s*$", block, re.M) or re.search(r"\|\|\s*(\d{10})\s*(?:\|\||\n|$)", block) or \
            re.search(r"CIK=0*(\d{1,10})\b(?!\w)", block)
        rows.append((m.group(1), c.group(1).zfill(10) if c else None, "table" if c else None))
    return rows

def companies():
    """One row per CIK: a company with two share classes (GOOGL and GOOG) files one 8-K. The first symbol in the table is kept.
    Returns rows (list, symbol, cik, how) and the symbols that could not be given a CIK."""
    tick = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in json.load(open(os.path.join(OUT, TICKER_FILE))).values()}
    seen, out, none = set(), [], []
    for lst, fname, _ in LISTS:
        for sym, cik, how in members(fname):
            if cik is None:
                k = sym.replace(".", "-")
                if k in tick: cik, how = tick[k], "sec ticker file"
                elif sym in MANUAL_CIK: cik, how = MANUAL_CIK[sym], "edgar name search"
                else: none.append((lst, sym)); continue
            if cik not in seen: seen.add(cik); out.append((lst, sym, cik, how))
    return out, none

# Extractor version 2, 2026-11-25, before any reader saw a text. Version 1 put a space for every tag, which split words
# styled mid-word ("GA AP") and broke table rows that hold blocks inside cells. Version 2 joins inline tags, keeps each
# table row on one line with " | " between non-empty cells, joins "$" and ")" or "%" to their numbers, and drops EDGAR's
# wrapper, the <head> and the hidden inline-XBRL header. Versions 3 to 5, same day, still before any reader saw a text: a footnote
# mark (a <sup>, or a short inline element raised by its style) becomes "[1]", so "$0.81" with footnote 1 no longer reads "$0.811".
EXTRACTOR = 5
BLOCK = r"p|div|br|tr|li|h[1-6]|table|ul|ol|center|hr|section|article|blockquote|pre|dd|dt"
def to_text(raw):
    raw = re.sub(r"(?is)^.*?<text>", "", raw, count=1) if re.match(r"(?is)\s*<document>", raw) else raw   # EDGAR's SGML wrapper
    raw = re.sub(r"(?is)<(script|style|head|title|ix:header)\b[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<!--.*?-->", "", raw)
    mark = lambda m: ("[" + m.group("t").strip() + "]") if html.unescape(m.group("t")).strip() else m.group("t")
    raw = re.sub(r"(?is)<sup\b[^>]*>(?P<t>[^<]{1,12})</sup>", mark, raw)
    raw = re.sub(r'(?is)<(font|span)\b[^>]*style="[^"]*(?:top:\s*-[\d.]+\s*pt|vertical-align:\s*super)[^"]*"[^>]*>(?P<t>[^<]{1,12})</\1>', mark, raw)
    raw = re.sub(r"(?is)<tr\b.*?</tr\s*>", lambda m: re.sub(rf"(?i)<(?:/?(?:{BLOCK})\b[^>]*)>", " ", m.group(0)) + "\n", raw)   # a row stays one line
    raw = re.sub(rf"(?i)<(?:/?(?:{BLOCK})\b[^>]*)>", "\n", raw)
    raw = re.sub(r"(?i)</t[dh]\s*>", " \x1f ", raw)                       # cell end, a mark for now
    raw = re.sub(r"<[^>]+>", "", raw)                                       # inline tags join their words
    raw = html.unescape(raw).replace("\xa0", " ").replace("\u200b", "")
    out = []
    for line in raw.split("\n"):
        if "\x1f" in line:
            cells = [c.strip() for c in line.split("\x1f")]
            cells = [c for c in cells if c]
            j = []
            for c in cells:
                if j and (c in (")", "%", ")%", "%)", "x", "pts", "bps") or (c.startswith(")") and len(c) <= 3)): j[-1] += c
                elif j and j[-1] in ("$", "(", "$(", "($", "€", "£", "¥", "C$", "US$"): j[-1] += c
                else: j.append(c)
            line = " | ".join(j)
        line = re.sub(r"[ \t]+", " ", line).strip()
        out.append(line)
    t = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", t).strip()

def session(acc_utc):
    t = acc_utc.astimezone(NY); hm = t.hour * 60 + t.minute + t.second / 60
    if t.weekday() >= 5: return "weekend"
    if hm < 9 * 60 + 30: return "before_open"
    if hm < 16 * 60: return "during_hours"
    return "after_close"

def main():
    mem, no_cik = companies(); os.makedirs(os.path.join(OUT, "submissions"), exist_ok=True); os.makedirs(os.path.join(OUT, "ex99"), exist_ok=True)
    events, no_sub = [], []
    for lst, sym, cik, how in mem:
        p = os.path.join(OUT, "submissions", cik + ".json")
        if not os.path.exists(p):
            b = get(f"https://data.sec.gov/submissions/CIK{cik}.json")
            if b is None: no_sub.append(sym); continue
            open(p, "w").write(b)
        s = json.load(open(p))["filings"]["recent"]
        for i, form in enumerate(s["form"]):
            if form not in ("8-K", "8-K/A") or not (START <= s["filingDate"][i] <= END): continue
            if "2.02" not in s["items"][i].split(","): continue
            acc = s["acceptanceDateTime"][i]   # e.g. 2026-04-23T16:05:12.000Z, UTC
            events.append(dict(list=lst, symbol=sym, cik=cik, form=form, accession=s["accessionNumber"][i], filing_date=s["filingDate"][i], acceptance_utc=acc,
                               items=s["items"][i], primary=s["primaryDocument"][i]))
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    def one(e):
        tp = os.path.join(OUT, "ex99", e["accession"] + ".txt"); mp = tp[:-4] + ".json"
        old = json.load(open(mp)) if os.path.exists(mp) else {}
        if old.get("found_by") == "index page type" and old.get("extractor") == EXTRACTOR: e.update(old); return
        base = f"https://www.sec.gov/Archives/edgar/data/{int(e['cik'])}/{e['accession'].replace('-', '')}/"
        if old.get("found_by") == "index page type":
            info = {k: old[k] for k in ("index_found", "exhibit_file", "exhibit_type", "found_by")}
        else:
            page = get(base + e["accession"] + "-index.htm")   # the filing's own index page states each document's type
            typed = []
            for row in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", page or ""):
                h = re.search(r'href="[^"]*/([^"/]+)"', row); cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"(?is)<td[^>]*>(.*?)</td>", row)]
                if h and len(cells) >= 4: typed.append((cells[3].upper(), h.group(1)))
            cand = [n for t, n in typed if t in ("EX-99.1", "EX-99.01", "EX-99") and n.lower().endswith((".htm", ".html", ".txt"))]
            if not cand: cand = [n for t, n in typed if t.startswith("EX-99") and n.lower().endswith((".htm", ".html", ".txt"))]
            info = dict(index_found=bool(page), exhibit_file=cand[0] if cand else None, exhibit_type=dict((n, t) for t, n in typed).get(cand[0]) if cand else None, found_by="index page type")
        info.update(text_chars=0, extractor=EXTRACTOR)
        if info["exhibit_file"]:
            rp = os.path.join(OUT, "raw", e["accession"] + "_" + info["exhibit_file"])
            if not os.path.exists(rp):
                b = get(base + info["exhibit_file"], binary=True)
                if b: open(rp, "wb").write(b)
            if os.path.exists(rp):
                txt = to_text(open(rp, "rb").read().decode("utf-8", "replace")); open(tp, "w", encoding="utf-8").write(txt); info["text_chars"] = len(txt)
        json.dump(info, open(mp, "w")); e.update(info)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as pool: list(pool.map(one, events))
    for e in events:
        a = dt.datetime.strptime(e["acceptance_utc"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
        e["acceptance_ny"] = a.astimezone(NY).strftime("%Y-%m-%d %H:%M:%S"); e["session"] = session(a)
    json.dump(dict(list_sources={l: src for l, _, src in LISTS}, members={l: sum(m[0] == l for m in mem) for l, _, _ in LISTS},
                   no_cik=no_cik, cik_how={h: sum(m[3] == h for m in mem) for h in {m[3] for m in mem}}, no_submissions=no_sub,
                   window=[START, END], events=events), open(os.path.join(OUT, "events_11.json"), "w"), indent=1)
    readable = [e for e in events if e["text_chars"] >= 1500]
    from collections import Counter
    print(json.dumps(dict(symbols_in_table={l: len(members(f)) for l, f, _ in LISTS}, companies={l: sum(m[0] == l for m in mem) for l, _, _ in LISTS}, no_cik=no_cik, members_without_submissions=len(no_sub), events=Counter(e["list"] for e in events), companies_with_events=len({e["symbol"] for e in events}),
                          amendments=sum(e["form"] == "8-K/A" for e in events), with_exhibit_99=sum(bool(e["exhibit_file"]) for e in events),
                          readable_text_1500_chars=len(readable), session=Counter(e["session"] for e in events), session_readable=Counter(e["session"] for e in readable),
                          by_month=Counter(e["filing_date"][:7] for e in events)), indent=1))

if __name__ == "__main__": main()
