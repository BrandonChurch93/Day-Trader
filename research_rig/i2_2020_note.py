"""Reads the twelve industry file and writes each group's 2020 return, to show what sat behind rule I2's 2020 year in replay 05.
A description of one year, not a rule trial. Output: i2_2020_note.json. Run: python3 i2_2020_note.py"""
import csv, json, os
F = os.environ.get("FRENCH_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "french"))
rows = list(csv.reader(open(F + "/12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv"))); h = rows[0][1:]; acc = {c: 1.0 for c in h}; n = 0
for r in rows[1:]:
    if r[0].replace("-", "").startswith("2020"):
        n += 1
        for c, v in zip(h, r[1:]): acc[c] *= 1 + float(v) / 100
out = {"year": 2020, "days": n, "return_by_group": {c: a - 1 for c, a in acc.items()}}; out["top"] = max(acc, key=acc.get); out["second"] = sorted(acc, key=acc.get)[-2]
json.dump(out, open("i2_2020_note.json", "w"), indent=1); print(out)
