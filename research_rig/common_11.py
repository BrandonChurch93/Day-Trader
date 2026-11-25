"""Shared pieces for draft plan 11 (an AI reads each earnings release). Paths, config, event ids, the price-file map and
the trading calendar. Reads no price itself; price_rows() is only called by score_11.py, and by prep_11.py for the March
2026 size check, which ends before the first event.

Raw files stay under ~/workspace/rig/data/ and are never committed. EDGAR_11_DIR and STOCK_DAILY_11_DIR override the
folders (the tests use this with made-up files)."""
import os, json, csv, hashlib, yaml, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.expanduser("~"), "workspace", "rig", "data")
EDGAR = os.environ.get("EDGAR_11_DIR", os.path.join(DATA, "edgar_11"))
PRICES = os.environ.get("STOCK_DAILY_11_DIR", os.path.join(DATA, "stock_daily_11"))
SPY_FILE = os.environ.get("SPY_DAILY_11_FILE", os.path.join(DATA, "platform_bars", "1day", "SPY_1day.csv"))
READING = os.path.join(EDGAR, "reading")
OUTDIR = os.environ.get("RESULTS_11_DIR", HERE)   # the tests point this at a temporary folder
SUMMARY = os.path.join(HERE, "events_11_summary.json")
INSTRUCTION = os.path.join(HERE, "reader_instruction_11.txt")
LISTS = ("500", "400", "600")

_TH = yaml.safe_load(open(os.path.join(HERE, "..", "config", "thresholds.yaml")))
def th(key):
    return _TH[key]["value"]

# Price files for a symbol whose bars continue under another ticker. Each pair: the SEC's company_tickers.json (saved
# 2026-11-25) gives the new ticker for the same CIK, and the two files' closes agree within 0.5% on every shared day, or
# the old ticker has no bars at all (ATGE, AXL). SATS is the exception: its file starts 2026-10-16 and does not match
# EchoStar's (CIK 0001415404) bars under ECHO, which cover the whole window, so the SATS file is another security.
# HLX to HOS (a merger, HOS starts 2026-08-04) and TWO to TWOD (closes do not agree) are not aliases.
ALIAS = {"BK": "BNY", "PSTG": "P", "ASGN": "EFOR", "ATGE": "CVSA", "AXL": "DCH", "EXPI": "AGNT", "FDP": "DMC",
         "IAC": "PPLI", "VSCO": "VSXY", "EQR": "VMRK", "PSKY": "SKYD", "SATS": "ECHO"}

def event_id(accession):
    return hashlib.sha256(accession.encode()).hexdigest()[:12]

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256_file(p):
    return sha256_bytes(open(p, "rb").read())

def price_symbol(sym):
    return ALIAS.get(sym, sym.replace(".", "-"))

def price_path(sym):
    s = price_symbol(sym)
    hits = [f for f in os.listdir(PRICES) if f.startswith(s + "_1day")] if os.path.isdir(PRICES) else []
    return os.path.join(PRICES, sorted(hits)[-1]) if hits else None

def bar_dates(sym):
    """Which dates have a bar. Reads the date column only."""
    p = price_path(sym)
    return {r["date"] for r in csv.DictReader(open(p, newline=""))} if p else set()

def price_rows(sym):
    """{date: (open, close)}. Only score_11.py and the March size check call this."""
    p = price_path(sym)
    if not p: return {}
    return {r["date"]: (float(r["open"]), float(r["close"])) for r in csv.DictReader(open(p, newline=""))}

def window(days, entry, n):
    """The trading days of a hold of n days counting the entry day as day 1, or None if prices end first."""
    i = days.index(entry)
    return days[i:i + n] if i + n <= len(days) else None

def overnight_moves(P, win, lo, hi):
    """Close-to-next-open ratios outside [lo, hi] between two days of a window that both have a bar. P: {date: (open, close)}."""
    have = [d for d in win if d in P]
    return [(a, b, P[b][0] / P[a][1]) for a, b in zip(have, have[1:]) if P[a][1] > 0 and not lo <= P[b][0] / P[a][1] <= hi]

def trading_days(start="2026-03-01"):
    return [r["date"] for r in csv.DictReader(open(SPY_FILE, newline="")) if r["date"] >= start]

def entry_day(acceptance_ny, days):
    """First regular-session open after the acceptance time (New York). Before 09:30 on a trading day: that day."""
    d, t = acceptance_ny[:10], acceptance_ny[11:]
    return next((x for x in days if x > d or (x == d and t < "09:30:00")), None)

def last_close_day_before(acceptance_ny, days):
    """The last trading day whose 16:00 close is before the acceptance time."""
    d, t = acceptance_ny[:10], acceptance_ny[11:]
    prev = [x for x in days if x < d or (x == d and t >= "16:00:00")]
    return prev[-1] if prev else None

def load_usable():
    return json.load(open(os.path.join(EDGAR, "usable_11.json")))
