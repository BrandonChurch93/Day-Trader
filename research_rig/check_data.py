"""Says which local raw data files are present, whether each one matches the fingerprint on record in provenance.json, and how to get
the ones that are missing. Runs in a few seconds.
Usage, from research_rig/: python3 check_data.py            (exit code 1 if anything is missing)
Raw price files are never committed. They live in research_rig/data/, which git ignores, unless the variable named below is set."""
import os, glob, sys
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "data")
K = os.environ.get("KRAKEN_DIR", os.path.join(D, "kraken")); KD = os.environ.get("KRAKEN_DAILY_DIR", os.path.join(K, "daily"))
F = os.environ.get("FRENCH_DIR", os.path.join(D, "french"))
SETS = [
    ("Bitstamp daily bars, bitcoin and ether", [f"{D}/bitstamp_BTCUSD.csv", f"{D}/bitstamp_ETHUSD.csv"], "python3 fetch.py crypto", "replay 01, the rerun, pilot 02"),
    ("Bitstamp hourly bars, bitcoin and ether", [f"{D}/bitstamp_BTCUSD_1h.csv", f"{D}/bitstamp_ETHUSD_1h.csv"], "python3 fetch.py hourly", "replay 03, the rerun"),
    ("Kraken recent daily bars from its public endpoint", [f"{D}/kraken_BTCUSD.csv", f"{D}/kraken_ETHUSD.csv"], "python3 fetch.py kraken", "cross-check X1, build_kraken_daily.py"),
    ("Kraken published archive, bitcoin and ether (KRAKEN_DIR)", [f"{K}/full_XBTUSD_1440.csv", f"{K}/full_ETHUSD_1440.csv", f"{K}/full_XBTUSD_60.csv", f"{K}/full_ETHUSD_60.csv"], "python3 fetch_kraken_archive.py full", "the rerun, build_kraken_daily.py"),
    ("Kraken full daily history, built", [f"{D}/krakenfull_BTCUSD.csv", f"{D}/krakenfull_ETHUSD.csv"], "python3 build_kraken_daily.py   (needs Bitstamp daily, Kraken recent daily and the Kraken archive, all above)", "X2, S2, the rerun, document 16"),
    ("Kraken published archive, every US dollar pair, daily (KRAKEN_DAILY_DIR)", [f"{KD}/XBTUSD_1440.csv", f"{KD}/ETHUSD_1440.csv"], "python3 fetch_kraken_archive.py daily", "replay 04"),
    ("Kenneth French library, market and twelve industry groups (FRENCH_DIR)", [f"{F}/F-F_Research_Data_Factors_daily__main.csv", f"{F}/12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv"], "python3 fetch_french.py", "replay 05, i2_2020_note.py"),
    ("Order-book samples", [f"{D}/books/books.csv"], "not fetchable: a one-night sample taken on 2026-11-25. books_summary.json in the repo holds the summary", "books_summary.py only"),
]
miss = 0
for name, files, how, used in SETS:
    gone = [f for f in files if not os.path.exists(f)]; miss += bool(gone)
    print(("MISSING  " if gone else "present  ") + name + "   [used by: " + used + "]")
    for f in gone: print("           no file " + os.path.relpath(f, H))
    if gone: print("           get it with: " + how)
n = len(glob.glob(f"{KD}/*USD_1440.csv"))
if n: print(f"note     {n} daily files in {os.path.relpath(KD, H)}. Replay 04 was run on 760")
import json, provenance as P
rec = json.load(open(os.path.join(H, "provenance.json")))["inputs"]; differ = 0
for name, was in rec.items():
    now = P.fingerprint(name)
    if now is not None and not P.same(now, was):
        differ += 1; print("DIFFERS  " + name + " is not the file on record in provenance.json. A download taken later can hold different bars, so a script run on it need not give the stored numbers")
print("\nAll present." if not miss else f"\n{miss} data set(s) missing. A script that needs one will stop with a file-not-found error.")
if not differ: print("Every present file that has a fingerprint on record matches it.")
sys.exit(1 if miss or differ else 0)
