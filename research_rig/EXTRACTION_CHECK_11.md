# Plan 11 extraction check: reading notes on 20 texts

Written by `extract_check_11.py` from `extraction_check_11.json`. Extractor version 5. Cap: replay_11_readers.text_cap_chars = 20000. Labels: MEASURED (counts), STATED (reading notes).

## Counts (MEASURED)

- Texts: 20, a seeded pick across the three lists (events_11_summary.json, extraction_check_pick).
- Number tokens of the filing kept in the text: 100.0% on average, lowest 100.0%.
- Texts with images: 14. A reader never sees an image.
- Cut by the cap: 18. Guidance heading found: 16, of which before the cap: 15.
- In the cut texts, table rows are 45.2% of the cut part on average, and 23.3% of the kept part.

## What was lost (STATED, from reading)

- Footnote marks. In extractor version 2 a raised footnote mark was glued to the number before it: "Adjusted Diluted EPS of $0.81" with footnote 1 read "$0.811", and "decreasing 1%" read "1%1". A reader could take the wrong number. Fixed in versions 3 to 5, before any reader saw a text: a `<sup>` or a short raised inline element becomes "[1]" or "[(1)]", and an empty raised element is dropped. All texts were re-extracted from the saved raw exhibits.
- Images: logos, and in some releases charts or whole highlight panels. Their content is lost. This matters most for letter-style releases.
- The cut part is not only tables. It is tables (statements, reconciliations, segment detail) and also non-GAAP definitions, the forward-looking statements notice, the company description, and in a few texts part of the guidance.
- Guidance lost to the cap: in texts where guidance sits late, as in a supplemental pack that starts with tables, or where the guidance table straddles the cap.
- Page headers and footers sit inline (page numbers, dates). Harmless but noisy.
- Bullets come through in mixed forms ("•", "●", "l |"). Readable.
- Nothing was found where words were split or numbers dropped.

## Each text (MEASURED counts, STATED note)

| List | Symbol | Characters | Numbers kept | Images | Share after cap | Table share of cut part | Guidance heading at | Note |
|---|---|---|---|---|---|---|---|---|
| 500 | TSCO | 24,492 | 100.0% | 1 | 18.3% | 49.1% | 6,104 | Cap falls in the notes under the store metrics table. Bullets in the highlights come through as "l |" (a Wingdings bullet in a table cell). |
| 500 | BF.B | 40,143 | 100.0% | 1 | 50.2% | 48.5% | 5,982 | Cap falls inside the brand-by-brand sales table. Highlights, quote and outlook are kept. |
| 500 | DVA | 48,600 | 100.0% | 0 | 58.8% | 49.8% | 5,880 | Cap falls at the start of the income statement. Highlights and the outlook are kept; the statements are lost. |
| 500 | VRTX | 35,468 | 100.0% | 0 | 43.6% | 36.2% | 3,099 | Cap falls inside the notes to the guidance (what the guidance excludes). The guidance figures are kept; part of the caveats is lost. |
| 500 | FICO | 16,206 | 100.0% | 0 | 0.0% | n/a | 2,750 | Not cut. |
| 500 | GILD | 42,793 | 100.0% | 1 | 53.3% | 69.7% | 6,974 | Cap falls in the forward-looking statements notice. Page footers (date and page number) sit inline in the text. |
| 500 | AEE | 33,788 | 100.0% | 1 | 40.8% | 48.2% | 4,455 | Cap falls in the forward-looking statements notice. A "Page n of n" footer sits inline. |
| 400 | GHC | 29,629 | 100.0% | 0 | 32.5% | 62.1% | none | Cap falls in the segment revenue tables. No outlook section: the company gives no guidance. |
| 400 | WING | 23,028 | 100.0% | 1 | 13.1% | 34.5% | 4,917 | Cap falls in the restaurant count tables. Outlook kept. |
| 400 | UNM | 37,703 | 100.0% | 13 | 47.0% | 27.8% | 17,279 | Cap falls in the non-GAAP definitions. The outlook heading is close to the cap but before it. |
| 400 | EGP | 43,520 | 100.0% | 1 | 54.0% | 25.1% | 16,754 | Cap falls inside the guidance table (investment and disposition lines). The guidance lines before the cap are kept; the rest of the table is lost. |
| 400 | CNX | 42,643 | 100.0% | 1 | 53.1% | 43.6% | 21,389 (after cap) | A supplemental pack, not a usual release: it opens with a table of contents and hedge tables. The guidance section is after the cap and is lost. |
| 400 | SLGN | 28,270 | 100.0% | 3 | 29.3% | 17.6% | 8,450 | Cap falls in the segment EBIT and EBITDA reconciliation. Highlights and outlook kept. |
| 400 | RYN | 53,202 | 100.0% | 1 | 62.4% | 58.4% | 12,546 | Cap falls in the forward-looking statements notice. Outlook kept. |
| 600 | CRC | 45,894 | 100.0% | 1 | 56.4% | 61.6% | 6,699 | Cap falls in the revenue table. Highlights and guidance kept. |
| 600 | FORM | 21,191 | 100.0% | 1 | 5.6% | 0.0% | 3,115 | Cap falls in the non-GAAP definitions, just after the outlook. Outlook kept. |
| 600 | HCSG | 14,665 | 100.0% | 0 | 0.0% | n/a | none | Not cut. Outlook is stated in the highlights, not under its own heading. |
| 600 | MBIN | 47,803 | 100.0% | 2 | 58.2% | 75.1% | none | Cap falls in the company description at the end of the text part; the long loan and deposit tables are lost. No guidance, as usual for a bank. |
| 600 | XPEL | 20,429 | 100.0% | 0 | 2.1% | 89.5% | 5,694 | Cap falls in the adjusted net income reconciliation, very near the end. Nothing of note lost. |
| 600 | MARA | 44,569 | 100.0% | 35 | 55.1% | 17.6% | none | A shareholder letter laid out as pictures and short lines, with many images. Cap falls inside the financial discussion; key figures in charts are never seen. No outlook heading. |
