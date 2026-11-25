"""Downloads the two Kenneth French Data Library files that replay 05 reads and writes one tidy CSV per section.
Usage, from research_rig/: python3 fetch_french.py
Writes to data/french unless FRENCH_DIR is set. git ignores data/. Raw files are never committed.
Tidy files: first row is the header, first column is `date` as YYYYMMDD, values are copied as they are (percent per day).
The library rebuilds its full history at each update, so a later download can differ slightly from the one used on 2026-11-25
(data_notes_french.md). A rerun on a later download is a new run, not a reproduction."""
import urllib.request, zipfile, io, os, re, datetime
F = os.environ.get("FRENCH_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "french"))
BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FILES = ["F-F_Research_Data_Factors_daily_CSV.zip", "12_Industry_Portfolios_daily_CSV.zip"]

def tidy(name, text):
    """Splits one library CSV into its sections. Same logic as the parser used for the 2026-11-25 download."""
    secs = []; cur = None; title = "main"; hdr = None
    for l in text.splitlines():
        s = l.strip()
        if re.match(r"^\d{8},", s):
            if cur is None: cur = {"title": title, "header": hdr, "rows": []}
            cur["rows"].append(s.split(","))
        else:
            if cur: secs.append(cur); cur = None
            if s.startswith(","): hdr = [c.strip() for c in s.split(",")]; hdr[0] = "date"
            elif s and not s.startswith("Copyright"): title = s
    if cur: secs.append(cur)
    for k, sct in enumerate(secs):
        out = f"{name}__main.csv" if len(secs) == 1 else f"{name}__{k}_{re.sub(r'[^A-Za-z]+', '_', sct['title']).strip('_')[:40]}.csv"
        with open(os.path.join(F, out), "w") as o:
            o.write(",".join(sct["header"]) + "\n")
            for r in sct["rows"]: o.write(",".join(v.strip() for v in r) + "\n")
        print("  wrote", out, len(sct["rows"]), "rows", sct["rows"][0][0], "to", sct["rows"][-1][0], flush=True)

if __name__ == "__main__":
    os.makedirs(F, exist_ok=True)
    for z in FILES:
        raw = urllib.request.urlopen(urllib.request.Request(BASE + z, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read()
        print(z, len(raw), "bytes", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), flush=True)
        zf = zipfile.ZipFile(io.BytesIO(raw))
        for n in zf.namelist(): tidy(n.rsplit(".", 1)[0], zf.read(n).decode("latin-1"))
