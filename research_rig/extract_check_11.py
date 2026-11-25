"""Extraction check for draft plan 11. For the seeded pick of events in events_11_summary.json (extraction_check_pick),
compares each extracted text with the filing's raw exhibit. Reads no price. Writes research_rig/extraction_check_11.json.

Measured for each text:
  - numbers: the share of number tokens in the raw exhibit's visible text that are also in the extracted text, as a multiset
  - images: the number of <img> tags (charts and logos), whose content a reader never sees
  - tables: the number of <table> tags and of " | " rows in the text
  - after the cap: the share of the text past replay_11_readers.text_cap_chars, and the share of that part that is table rows
  - guidance: where the first line headed outlook or guidance starts, and whether it is before the cap
Also writes research_rig/EXTRACTION_CHECK_11.md: the counts from the JSON, plus reading notes typed after reading each text
against its filing on 2026-11-25. The notes hold no figures; every figure in that file comes from the JSON.
Usage, from research_rig/:  python3 extract_check_11.py"""
import os, re, json, html, glob
from collections import Counter
import common_11 as C, prep_11 as P
from fetch_11_edgar import EXTRACTOR as EXTRACTOR_V

NUM = re.compile(r"\d[\d,]*\.?\d*")

def visible(raw):
    raw = re.sub(r"(?is)^.*?<text>", "", raw, count=1) if re.match(r"(?is)\s*<document>", raw) else raw
    raw = re.sub(r"(?is)<(script|style|head|title|ix:header)\b[^>]*>.*?</\1>", " ", raw)
    return html.unescape(re.sub(r"<[^>]+>", " ", raw)).replace("\xa0", " ")   # every tag a space, so cells never join

def nums(t):
    return Counter(n.rstrip(".,").replace(",", "") for n in NUM.findall(t) if any(ch.isdigit() for ch in n))

def main():
    S = json.load(open(C.SUMMARY)); cap = C.th("replay_11_readers")["text_cap_chars"]; U = {k["event_id"]: k for k in C.load_usable()["events"]}
    rows = []
    for p in S["extraction_check_pick"]:
        k = U[p["event_id"]]; rp = glob.glob(os.path.join(C.EDGAR, "raw", k["accession"] + "_*"))
        raw = open(rp[0], "rb").read().decode("utf-8", "replace"); t = open(os.path.join(C.EDGAR, "ex99", k["accession"] + ".txt"), encoding="utf-8").read()
        a, b = nums(visible(raw)), nums(t); kept = sum(min(v, b[n]) for n, v in a.items()); tot = sum(a.values())
        after = t[cap:]; trows = [l for l in t.split("\n") if " | " in l]
        g = P.guidance_pos(t)
        rows.append(dict(event_id=k["event_id"], list=k["list"], symbol=k["symbol"], accession=k["accession"], text_chars=len(t),
                         numbers_in_raw=tot, numbers_kept_share=round(kept / tot, 4) if tot else None,
                         images=len(re.findall(r"(?i)<img\b", raw)), tables=len(re.findall(r"(?i)<table\b", raw)), table_rows_in_text=len(trows),
                         share_after_cap=round(max(0, len(t) - cap) / len(t), 3),
                         table_share_of_part_after_cap=round(sum(len(l) + 1 for l in after.split("\n") if " | " in l) / len(after), 3) if after else None,
                         table_share_of_part_before_cap=round(sum(len(l) + 1 for l in t[:cap].split("\n") if " | " in l) / min(len(t), cap), 3),
                         guidance_heading_pos=g, guidance_before_cap=(g is not None and g < cap)))
    out = dict(made_by="research_rig/extract_check_11.py", cap=cap, texts=rows,
               totals=dict(texts=len(rows), mean_numbers_kept_share=round(sum(r["numbers_kept_share"] for r in rows) / len(rows), 4),
                           lowest_numbers_kept_share=min(r["numbers_kept_share"] for r in rows), with_images=sum(r["images"] > 0 for r in rows),
                           cut=sum(r["share_after_cap"] > 0 for r in rows), guidance_heading_found=sum(r["guidance_heading_pos"] is not None for r in rows),
                           guidance_before_cap=sum(r["guidance_before_cap"] for r in rows)))
    json.dump(out, open(os.path.join(C.HERE, "extraction_check_11.json"), "w"), indent=1); open(os.path.join(C.HERE, "extraction_check_11.json"), "a").write("\n")
    write_notes(out)
    print(json.dumps(out["totals"], indent=1))

# Reading notes, by symbol: where the cap falls and what is lost. Typed from reading, no figures.
NOTES = {
    "TSCO": "Cap falls in the notes under the store metrics table. Bullets in the highlights come through as \"l |\" (a Wingdings bullet in a table cell).",
    "BF.B": "Cap falls inside the brand-by-brand sales table. Highlights, quote and outlook are kept.",
    "DVA": "Cap falls at the start of the income statement. Highlights and the outlook are kept; the statements are lost.",
    "VRTX": "Cap falls inside the notes to the guidance (what the guidance excludes). The guidance figures are kept; part of the caveats is lost.",
    "FICO": "Not cut.",
    "GILD": "Cap falls in the forward-looking statements notice. Page footers (date and page number) sit inline in the text.",
    "AEE": "Cap falls in the forward-looking statements notice. A \"Page n of n\" footer sits inline.",
    "GHC": "Cap falls in the segment revenue tables. No outlook section: the company gives no guidance.",
    "WING": "Cap falls in the restaurant count tables. Outlook kept.",
    "UNM": "Cap falls in the non-GAAP definitions. The outlook heading is close to the cap but before it.",
    "EGP": "Cap falls inside the guidance table (investment and disposition lines). The guidance lines before the cap are kept; the rest of the table is lost.",
    "CNX": "A supplemental pack, not a usual release: it opens with a table of contents and hedge tables. The guidance section is after the cap and is lost.",
    "SLGN": "Cap falls in the segment EBIT and EBITDA reconciliation. Highlights and outlook kept.",
    "RYN": "Cap falls in the forward-looking statements notice. Outlook kept.",
    "CRC": "Cap falls in the revenue table. Highlights and guidance kept.",
    "FORM": "Cap falls in the non-GAAP definitions, just after the outlook. Outlook kept.",
    "HCSG": "Not cut. Outlook is stated in the highlights, not under its own heading.",
    "MBIN": "Cap falls in the company description at the end of the text part; the long loan and deposit tables are lost. No guidance, as usual for a bank.",
    "XPEL": "Cap falls in the adjusted net income reconciliation, very near the end. Nothing of note lost.",
    "MARA": "A shareholder letter laid out as pictures and short lines, with many images. Cap falls inside the financial discussion; key figures in charts are never seen. No outlook heading.",
}

def write_notes(out):
    t = out["totals"]; cap = out["cap"]; pc = lambda x: "n/a" if x is None else f"{100 * x:.1f}%"
    cut = [r for r in out["texts"] if r["share_after_cap"] > 0]
    L = ["# Plan 11 extraction check: reading notes on 20 texts", "",
         f"Written by `extract_check_11.py` from `extraction_check_11.json`. Extractor version {EXTRACTOR_V}. Cap: replay_11_readers.text_cap_chars = {cap}. Labels: MEASURED (counts), STATED (reading notes).", "",
         "## Counts (MEASURED)", "",
         f"- Texts: {t['texts']}, a seeded pick across the three lists (events_11_summary.json, extraction_check_pick).",
         f"- Number tokens of the filing kept in the text: {pc(t['mean_numbers_kept_share'])} on average, lowest {pc(t['lowest_numbers_kept_share'])}.",
         f"- Texts with images: {t['with_images']}. A reader never sees an image.",
         f"- Cut by the cap: {t['cut']}. Guidance heading found: {t['guidance_heading_found']}, of which before the cap: {t['guidance_before_cap']}.",
         f"- In the cut texts, table rows are {pc(sum(r['table_share_of_part_after_cap'] for r in cut) / max(1, len(cut)))} of the cut part on average, and {pc(sum(r['table_share_of_part_before_cap'] for r in out['texts']) / len(out['texts']))} of the kept part.", "",
         "## What was lost (STATED, from reading)", "",
         "- Footnote marks. In extractor version 2 a raised footnote mark was glued to the number before it: \"Adjusted Diluted EPS of $0.81\" with footnote 1 read \"$0.811\", and \"decreasing 1%\" read \"1%1\". A reader could take the wrong number. Fixed in versions 3 to 5, before any reader saw a text: a `<sup>` or a short raised inline element becomes \"[1]\" or \"[(1)]\", and an empty raised element is dropped. All texts were re-extracted from the saved raw exhibits.",
         "- Images: logos, and in some releases charts or whole highlight panels. Their content is lost. This matters most for letter-style releases.",
         "- The cut part is not only tables. It is tables (statements, reconciliations, segment detail) and also non-GAAP definitions, the forward-looking statements notice, the company description, and in a few texts part of the guidance.",
         "- Guidance lost to the cap: in texts where guidance sits late, as in a supplemental pack that starts with tables, or where the guidance table straddles the cap.",
         "- Page headers and footers sit inline (page numbers, dates). Harmless but noisy.",
         "- Bullets come through in mixed forms (\"•\", \"●\", \"l |\"). Readable.",
         "- Nothing was found where words were split or numbers dropped.", "",
         "## Each text (MEASURED counts, STATED note)", "",
         "| List | Symbol | Characters | Numbers kept | Images | Share after cap | Table share of cut part | Guidance heading at | Note |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in out["texts"]:
        g = "none" if r["guidance_heading_pos"] is None else f"{r['guidance_heading_pos']:,}" + ("" if r["guidance_before_cap"] else " (after cap)")
        L.append(f"| {r['list']} | {r['symbol']} | {r['text_chars']:,} | {pc(r['numbers_kept_share'])} | {r['images']} | {pc(r['share_after_cap'])} | {pc(r['table_share_of_part_after_cap'])} | {g} | {NOTES.get(r['symbol'], 'not read')} |")
    open(os.path.join(C.HERE, "EXTRACTION_CHECK_11.md"), "w").write("\n".join(L) + "\n")

if __name__ == "__main__": main()
