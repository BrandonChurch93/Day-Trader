"""Plan 74 power-model calibration of the common month share, from published Kenneth French library data only.

Reads two zips already held off-repo under /home/user/workspace/rig/data/french's parent folder
(10_Portfolios_Prior_12_2_Daily_CSV.zip and F-F_Research_Data_Factors_daily_CSV.zip). Uses only rows dated
before 2017-01-01; later rows are skipped before any arithmetic. No Alpaca bar, no vendor price file, no network.

Series: top prior-return decile ("Hi PRIOR", the nearest held series to a long momentum book) minus the market
(Mkt-RF + RF), daily returns compounded to calendar months. Monthly common SD = SD of that monthly difference.
Share per noise row = monthly variance x average fraction of a month a hold spans / per-signal variance,
where the average fraction = mean of a hold uniform from 1 to the card's limit, over 21 sessions.
Writes research_rig/CALIB_74.json (a few summary numbers, no rows) and prints a markdown table.
Run: python3 research_rig/calib_74.py"""
import io, json, math, pathlib, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FR = pathlib.Path("/home/user/workspace/rig/data/french").resolve().parent
MOM = "10_Portfolios_Prior_12_2_Daily_CSV.zip"; FAC = "F-F_Research_Data_Factors_daily_CSV.zip"
CUTOFF = 20170101

def _plan():
    lines = (ROOT / "config" / "thresholds.yaml").read_text().splitlines()
    i = lines.index("replay_74_plan:")
    return json.loads(lines[i + 1].split("value:", 1)[1])

def sections(zname):
    with zipfile.ZipFile(FR / zname) as z:
        text = z.read(z.namelist()[0]).decode("latin-1")
    out, title, rows = {}, None, None
    for line in io.StringIO(text):
        s = line.strip()
        if not s:
            continue
        if s.startswith(","):
            rows = out.setdefault(title or "main", {"cols": [c.strip() for c in s.split(",")[1:]], "rows": {}})["rows"]; continue
        head = s.split(",")[0].strip()
        if head.isdigit() and len(head) == 8 and rows is not None:
            d = int(head)
            if d >= CUTOFF:
                continue                      # 2017 and later never enter the arithmetic
            rows[d] = [float(v) for v in s.split(",")[1:]]
        else:
            title, rows = s, None
    return out

def monthly(daily, first, last):
    acc = {}
    for d, r in daily.items():
        m = d // 100
        if first <= m <= last:
            acc[m] = acc.get(m, 1.0) * (1 + r / 100.0)
    return {m: v - 1 for m, v in acc.items()}

def main():
    C = _plan()["power"]["calibration"]
    mom = sections(MOM); fac = list(sections(FAC).values())[0]
    ci = fac["cols"].index("Mkt-RF"); ri = fac["cols"].index("RF")
    mkt_d = {d: r[ci] + r[ri] for d, r in fac["rows"].items()}
    res = {"files": [MOM, FAC], "series": {}, "rows": []}
    print("| Series | Months used | Months | Monthly SD of top decile minus market |")
    print("|---|---|---:|---:|")
    for key, title in (("equal", "Average Equal Weighted Returns -- Daily"), ("value", "Average Value Weighted Returns -- Daily")):
        sec = mom[title]; hi = sec["cols"].index("Hi PRIOR")
        top_d = {d: r[hi] for d, r in sec["rows"].items() if r[hi] > -99}
        for span in C["spans"]:
            a, b = span
            tm = monthly(top_d, a, b); mm = monthly({d: v for d, v in mkt_d.items() if d in top_d}, a, b)
            diff = [tm[m] - mm[m] for m in sorted(tm) if m in mm]
            mu = sum(diff) / len(diff)
            sd = math.sqrt(sum((x - mu) ** 2 for x in diff) / (len(diff) - 1))
            res["series"][f"{key}_{a}_{b}"] = {"months": len(diff), "first": min(tm), "last": max(tm), "monthly_sd": round(sd, 6)}
            print(f"| Hi PRIOR {key}-weighted minus market | {a // 100}-{a % 100:02d} to {b // 100}-{b % 100:02d} | {len(diff)} | {sd:.2%} |")
    main_sd = res["series"][C["main"]]["monthly_sd"]
    P = _plan()["power"]; res["main"] = C["main"]; res["shares"] = {}
    print(f"\nMain series {C['main']}, monthly common SD {main_sd:.2%}, variance {main_sd ** 2:.6f}.\n")
    print("| Card | Hold limit | Average fraction of a month a hold spans | Noise SD per signal | Common month share |")
    print("|---|---:|---:|---:|---:|")
    for card in ("A", "B"):
        lim = P["hold_limit"][card]; frac = (lim + 1) / 2 / P["sessions_per_month"]
        res["shares"][card] = {}
        for sd in P["noise_sd"][card]:
            share = min(main_sd ** 2 * frac / sd ** 2, 0.99)
            res["shares"][card][f"{sd:.2f}"] = round(share, 4)
            print(f"| {card} | {lim} | {frac:.4f} | {sd:.0%} | {share:.2%} |")
    (ROOT / "research_rig" / "CALIB_74.json").write_text(json.dumps(res, indent=1) + "\n")

if __name__ == "__main__":
    main()
