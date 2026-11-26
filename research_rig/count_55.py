"""Count 55: US closed-end fund rights offerings, 2016 to 2026. Price-blind.

Reads the per-event table (SEC filing links only, no prices), prints the counts the ledger row
asks for, runs the doc 117 screen on published figures, and writes
research_rig/COUNT_55_cef_rights_offerings.md. Nothing here reads a price.

    python3 research_rig/count_55.py            # print and write the doc
    python3 research_rig/count_55.py --print    # print only
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import math
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "research_rig" / "count_55_events.csv"
DOC_PATH = ROOT / "research_rig" / "COUNT_55_cef_rights_offerings.md"

# Lines fixed in ledger 212 before the count started.
YEAR_FIRST, YEAR_LAST = 2016, 2026
COUNT_LINE = 100            # completed offerings, exact expiration, US listing
POWER_LINE = 0.33           # chance of t at 2 under the doc 117 screen
T_MARK = 2.0
SCREEN_SESSIONS = 10        # the ledger fixes 10-session dispersion

# Published dispersion: Malkiel and Xu (2005), 59 US equity CEFs, 1993 to 2002, page 27.
MX_ANNUAL_SD = 0.196
SESSIONS_PER_YEAR = 252

# Assumed cost, not measured: one round trip on a listed CEF (doc 74 states 10 to 30 bp spreads).
COST_RT_BP = 30

# Clustering for the effective count: same sponsor, expirations this many calendar days apart or less.
CLUSTER_DAYS = 14

# Published rebound figures (STATED, copied from the sources named in the doc).
OAL_MEAN = 0.0021           # Open-Alpha-Lab study 929, mean CAR, post-expiry window
OAL_MEDIAN = 0.0044
OAL_T = 0.25
OAL_N = 39
OAL_SESSIONS = 21           # trading days +29 to +49 after the month anchor
OAL_CI = (-0.0151, 0.0187)
AIC_BOUNCE = 0.05           # AIC article, "a bounce of +5%", window not stated
AIC_N = 127
AIC_DISC_EXPIRY = -0.047
AIC_PREM_90_AFTER = 0.0017
AIC_PREM_90_BEFORE = 0.067
AIC_90D_SESSIONS = 63       # 90 calendar days read as about 63 sessions (assumption)

N01 = NormalDist()
Z_LINE = N01.inv_cdf(POWER_LINE)


def sd_for(sessions):
    return MX_ANNUAL_SD * math.sqrt(sessions / SESSIONS_PER_YEAR)


def power(n, edge, sd):
    if n <= 0:
        return 0.0
    return N01.cdf(math.sqrt(n) * edge / sd - T_MARK)


def needed(n, sd):
    """Edge that gives POWER_LINE at n events: sqrt(n) * e / sd - T_MARK = z(POWER_LINE)."""
    return (T_MARK + Z_LINE) * sd / math.sqrt(n)


def load(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def d(s):
    return dt.date.fromisoformat(s) if s else None


def eligible(r):
    e = d(r["expiration_final"])
    return (r["status"] == "completed" and e is not None and r["us_listed"] == "yes"
            and r["security"] == "common" and YEAR_FIRST <= e.year <= YEAR_LAST)


def clusters(rows):
    """Greedy chains: same sponsor and an expiration within CLUSTER_DAYS of the chain's last one."""
    out = []
    for r in sorted(rows, key=lambda x: (x["sponsor"], x["expiration_final"])):
        e = d(r["expiration_final"])
        if out and out[-1][0] == r["sponsor"] and (e - out[-1][1]).days <= CLUSTER_DAYS:
            out[-1][1] = e
            out[-1][2] += 1
        else:
            out.append([r["sponsor"], e, 1])
    return out


def pct(x, nd=2):
    return f"{100 * x:.{nd}f}%"


def build(rows, sha):
    L = []
    years = list(range(YEAR_FIRST, YEAR_LAST + 1))
    allr = [r for r in rows if r["expiration_final"] and YEAR_FIRST <= d(r["expiration_final"]).year <= YEAR_LAST]
    elig = [r for r in allr if eligible(r)]
    by_year = collections.Counter(d(r["expiration_final"]).year for r in allr)
    by_year_el = collections.Counter(d(r["expiration_final"]).year for r in elig)
    status = collections.Counter(r["status"] for r in allr)
    trans = collections.Counter(r["transferable"] for r in elig)
    spons = collections.Counter(r["sponsor"] for r in elig)
    funds = len({r["cik"] for r in elig})
    ext = sum(1 for r in elig if r["extension_dates"])
    cl = clusters(elig)
    n, n_eff = len(elig), len(cl)
    hhi = sum((v / n) ** 2 for v in spons.values()) if n else 0.0
    top5 = sum(v for _, v in spons.most_common(5))
    with_ann = sum(1 for r in elig if r["announce_accept_et"])
    with_rec = sum(1 for r in elig if r["record_date"])
    with_sh = sum(1 for r in elig if r["shares_issued"])
    wd = [r for r in allr if r["status"] != "completed"]

    s10 = sd_for(SCREEN_SESSIONS)
    cost = COST_RT_BP / 10000
    res = {
        "n": n, "n_eff": n_eff, "s10": s10, "funds": funds, "by_year": by_year_el, "status": status,
        "need_gross_n": needed(n, s10) if n else float("nan"),
        "need_gross_eff": needed(n_eff, s10) if n_eff else float("nan"),
    }
    res["need_with_cost_n"] = res["need_gross_n"] + cost
    res["need_with_cost_eff"] = res["need_gross_eff"] + cost
    s_oal = sd_for(OAL_SESSIONS)
    s_90 = sd_for(AIC_90D_SESSIONS)
    oal_implied_sd = OAL_MEAN * math.sqrt(OAL_N) / OAL_T
    readings = [
        ("Open-Alpha-Lab mean, its own 21-session window, net of cost", OAL_MEAN - cost, s_oal),
        ("Open-Alpha-Lab median, its own 21-session window, net of cost", OAL_MEDIAN - cost, s_oal),
        ("AIC +5% bounce read as 10 sessions (assumption), net of cost", AIC_BOUNCE - cost, s10),
        ("AIC +5% bounce read as 90 calendar days, about 63 sessions (assumption), net of cost", AIC_BOUNCE - cost, s_90),
    ]
    res["readings"] = [(lab, e, s, power(n, e, s), power(n_eff, e, s)) for lab, e, s in readings]
    count_ok = n >= COUNT_LINE
    windowed_ok = res["readings"][0][3] >= POWER_LINE
    res["count_ok"], res["windowed_ok"] = count_ok, windowed_ok

    w = L.append
    w("# Count 55: US closed-end fund rights offerings, 2016 to 2026")
    w("")
    w("Queue row 55, ledger 212. Price-blind count. This file is written by `research_rig/count_55.py` from "
      "`research_rig/count_55_events.csv`. Do not edit it by hand.")
    w("")
    w("## Lines fixed before the count")
    w("")
    w(f"- STATED (ledger 212): at least `COUNT_LINE` = {COUNT_LINE} completed offerings with an exact expiration date, "
      f"on a fund with a US listing, expiring {YEAR_FIRST} to {YEAR_LAST}.")
    w(f"- STATED (ledger 212): a post-expiration rebound size from a published source that gives at least "
      f"`POWER_LINE` = {pct(POWER_LINE, 0)} chance of t at `T_MARK` = {T_MARK:g} at that count under the doc 117 screen, "
      f"with `SCREEN_SESSIONS` = {SCREEN_SESSIONS}-session dispersion from a published figure, never our bars.")
    w("- STATED: below either line the row closes.")
    w("")
    w("## How the table was built")
    w("")
    w("- STATED: SEC sources only. Quarterly form indexes from https://www.sec.gov/Archives/edgar/full-index/ "
      "for 2015 Q3 to 2026 Q4, then the full submission text of each candidate filing.")
    w("- STATED: candidates were every 424B filing, plus 497, 497AD and 8-K filings, by a filer that also files N-CSR, "
      "kept when the text names a rights offering. N-2, N-2/A and POS 8C filings for each event's fund were read in a "
      "second pass to find the first filing that names the event's record or expiration date.")
    w("- STATED: no SEC full-text search, no press wire site, no sponsor site, no price data of any kind. "
      "Descriptive User-Agent, at most 4 requests a second. Raw filings stay in "
      "`/home/user/workspace/rig/data/count_55/`, off the repo.")
    w("- STATED: each event row was checked by hand against the filing text. Dates were read from the filings, "
      "with a link for each. The subscription price is kept as a formula only, never as a dollar figure.")
    w("- STATED: `status` is completed when a result filing, a later prospectus or a shareholder report states the "
      "offering closed or shares were issued; withdrawn when a filing says it was terminated or withdrawn.")
    w("- STATED: `us_listed` is yes when an offering filing names the NYSE, NYSE American or Nasdaq listing of the "
      "fund's shares, with the ticker at the time.")
    w(f"- STATED: `count_55_events.csv` sha256 `{sha}`. It holds no prices.")
    w("")
    w("## Counts")
    w("")
    w(f"- MEASURED: {len(allr)} offerings in the table expire {YEAR_FIRST} to {YEAR_LAST}. "
      + ", ".join(f"{k} {v}" for k, v in sorted(status.items())) + ".")
    w(f"- MEASURED: {n} pass the count rule (completed, exact expiration, US listing), on {funds} funds.")
    w(f"- MEASURED: {sum(1 for r in allr if r['status'] == 'completed' and r['security'] != 'common')} completed "
      "offerings were for preferred shares and are not counted.")
    w(f"- MEASURED: {ext} of the {n} had the expiration extended. The count uses the final expiration date.")
    w(f"- MEASURED: of the {n}, {with_ann} have a dated announcement filing with an SEC acceptance time, "
      f"{with_rec} a record date, {with_sh} a stated share count.")
    w("")
    w("By final expiration year, all offerings and those that pass the count rule:")
    w("")
    w("| Year | In table | Pass the count rule |")
    w("|---|---:|---:|")
    for y in years:
        w(f"| {y} | {by_year.get(y, 0)} | {by_year_el.get(y, 0)} |")
    w(f"| Total | {len(allr)} | {n} |")
    w("")
    w("Transferable or not, among those that pass:")
    w("")
    for k in sorted(trans):
        w(f"- MEASURED: {k}: {trans[k]}.")
    w("")
    w("Sponsor concentration, among those that pass:")
    w("")
    for s, v in spons.most_common(10):
        w(f"- MEASURED: {s}: {v} ({pct(v / n, 1)}).")
    w(f"- MEASURED: the top five sponsors hold {top5} of {n} ({pct(top5 / n, 1) if n else 'n/a'}). "
      f"Herfindahl index over sponsors {hhi:.3f}.")
    w(f"- MEASURED: {n_eff} clusters when offerings by one sponsor that expire within "
      f"`CLUSTER_DAYS` = {CLUSTER_DAYS} calendar days of each other count once.")
    if wd:
        w("")
        w("Offerings in the table not counted as completed:")
        w("")
        for r in sorted(wd, key=lambda x: x["expiration_final"]):
            w(f"- MEASURED: {r['fund']}, expiration {r['expiration_final']}, {r['status']} ([filing]({r['status_link'] or r['announce_link']})).")
    w("")
    w("## Published rebound figures")
    w("")
    w("- STATED: Khorana, Wahal and Zenner (2002, JFQA), 120 US CEF rights offerings 1988 to 1998: the premium turns "
      "into a discount over the offering. Before 2000 and no post-expiration rebound figure. "
      "[Cambridge](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/agency-conflicts-in-closedend-funds-the-case-of-rights-offerings/A9BD552704DEECFB4E2BC7E2627D42EC)")
    w("- STATED: Brigham (LSU dissertation, 2000) reports a very weak price rebound after offers, with no figure usable "
      "here, and the sample is before 2000. [LSU](https://repository.lsu.edu/gradschool_disstheses/7143/)")
    w(f"- STATED: AIC article citing John Cole Scott (CEF Advisors), about 12.5 years of data to 2024, {AIC_N} rights "
      f"offerings: average premium {pct(AIC_PREM_90_BEFORE, 1)} 90 days before expiration, {pct(AIC_DISC_EXPIRY, 1)} on "
      f"expiration day, {pct(AIC_PREM_90_AFTER)} 90 days after; \"-11% relative alpha then a bounce of +5%\". "
      "No window for the bounce, no sample dates, no t and no dispersion. Not peer reviewed. "
      "[AIC](https://aicalliance.org/wp-content/uploads/2024/10/How-Corporate-Actions-in-Closed-End-Funds-Can-Potentially-Boost-Portfolio-Performance.pdf)")
    w(f"- STATED: Open-Alpha-Lab study 929, not peer reviewed, {OAL_N} US offerings by 20 issuers, 2013 to 2023, event "
      f"dates only to the month: trading days +29 to +49 after the anchor (about {OAL_SESSIONS} sessions after a modelled "
      f"expiry) mean {pct(OAL_MEAN)}, median {pct(OAL_MEDIAN)}, t {OAL_T}, 95% interval {pct(OAL_CI[0])} to "
      f"{pct(OAL_CI[1])}. "
      "[results](https://raw.githubusercontent.com/Guillain-RDCDE/Open-Alpha-Lab/main/studies/929-rights-offering-discount/docs/results.md)")
    w(f"- MEASURED from those figures: the implied per-event sd of the Open-Alpha-Lab window is "
      f"{pct(oal_implied_sd)}, close to the published Malkiel and Xu figure scaled to {OAL_SESSIONS} sessions, "
      f"{pct(s_oal)}.")
    w("- UNKNOWN: no published post-2000 measurement gives a rebound size for a fixed 10-session window after the "
      "exact expiration date.")
    w("")
    w("## Doc 117 screen")
    w("")
    w(f"- STATED: dispersion from Malkiel and Xu (2005), 59 US equity CEFs, 1993 to 2002: average annualized volatility "
      f"from weekly returns `MX_ANNUAL_SD` = {pct(MX_ANNUAL_SD, 1)}. "
      "[paper](http://www-stat.wharton.upenn.edu/~steele/Courses/956/Resource/CEF/MalkielXu.pdf)")
    w(f"- MEASURED: scaled by the square root of `SCREEN_SESSIONS` / `SESSIONS_PER_YEAR` = {SCREEN_SESSIONS}/"
      f"{SESSIONS_PER_YEAR}, the 10-session sd is {pct(s10)}. This is the fund's own return sd. The paired noise "
      "against a same-clock alternative is UNKNOWN; it is used as the paired noise here.")
    w(f"- STATED: power is Φ(√N × edge ÷ sd − `T_MARK`). The {pct(POWER_LINE, 0)} line needs √N × edge ÷ sd of at "
      f"least {T_MARK + Z_LINE:.2f}.")
    w(f"- STATED: `COST_RT_BP` = {COST_RT_BP} bp round trip is an assumption, the top of the 10 to 30 bp spread range "
      "in doc 74.")
    w(f"- MEASURED: at N = {n}, the 10-session edge needed is {pct(res['need_gross_n'])} gross, "
      f"{pct(res['need_with_cost_n'])} before the cost is taken off.")
    w(f"- MEASURED: at the clustered count {n_eff}, it is {pct(res['need_gross_eff'])} gross, "
      f"{pct(res['need_with_cost_eff'])} before the cost is taken off.")
    w("")
    w(f"| Published figure, reading | Net edge | sd for its window | Power at N = {n} | Power at clustered {n_eff} |")
    w("|---|---:|---:|---:|---:|")
    for lab, e, s, p1, p2 in res["readings"]:
        w(f"| {lab} | {pct(e)} | {pct(s)} | {pct(p1, 1)} | {pct(p2, 1)} |")
    w("")
    w("## Verdict")
    w("")
    w(f"- MEASURED: count line: {n} against {COUNT_LINE}. " + ("Met." if count_ok else "Not met."))
    w(f"- MEASURED: the one published figure with a stated window (Open-Alpha-Lab, mean) gives "
      f"{pct(res['readings'][0][3], 1)} at N = {n}, against {pct(POWER_LINE, 0)}. "
      + ("Met." if windowed_ok else "Not met."))
    w("- STATED: the AIC +5% passes only if its unstated window is assumed. The line asks for a stated size, so "
      "this reading is shown but not used for the verdict.")
    verdict = "the row stays open for the lead's decision" if (count_ok and windowed_ok) else "the row closes on the fixed lines"
    w(f"- STATED: {verdict}.")
    w("")
    w("## Limits")
    w("")
    w("- UNKNOWN: recall. Offerings named only in filings outside the forms read here (for example a press release "
      "posted only on a sponsor site) are missed. The count is a lower bound.")
    w("- STATED: completion was read by hand from later shareholder reports and prospectuses for the events where "
      "no result filing was found; the CSV `status_basis` column says which.")
    w(f"- STATED: {sum(1 for r in rows if r['expiration_final'][:4] < str(YEAR_FIRST))} rows in the CSV expire before "
      f"{YEAR_FIRST}; they were found by the 2015 index quarters and are kept but not counted.")
    w("- STATED: 20 candidate filings failed to download in the first pass. They were fetched again later; none was a "
      "rights offering prospectus or notice (two named rights only as a possible future offering type).")
    w("- STATED: the shareholder reports read for completion state subscription prices. Those prices were not copied into "
      "the table or the repo.")
    w("- UNKNOWN: the paired noise of a fund against its same-clock alternative; the fund's own sd stands in.")
    w("- UNKNOWN: whether the 1993 to 2002 Malkiel and Xu volatility holds for 2016 to 2026.")
    w("")
    return "\n".join(L), res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(CSV_PATH))
    ap.add_argument("--print", action="store_true", dest="print_only")
    a = ap.parse_args()
    raw = Path(a.csv).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    rows = load(a.csv)
    doc, res = build(rows, sha)
    print(f"csv sha256 {sha}")
    print(f"pass the count rule {res['n']} on {res['funds']} funds, clustered {res['n_eff']}")
    print("by year " + " ".join(f"{y}:{res['by_year'].get(y, 0)}" for y in range(YEAR_FIRST, YEAR_LAST + 1)))
    print("status " + " ".join(f"{k}:{v}" for k, v in sorted(res["status"].items())))
    print(f"10-session sd {pct(res['s10'])}, needed gross {pct(res['need_gross_n'])} at N, "
          f"{pct(res['need_gross_eff'])} clustered")
    for lab, e, s, p1, p2 in res["readings"]:
        print(f"  {lab}: edge {pct(e)} sd {pct(s)} power {pct(p1, 1)} / {pct(p2, 1)}")
    print(f"count line {'met' if res['count_ok'] else 'not met'}; windowed power line "
          f"{'met' if res['windowed_ok'] else 'not met'}")
    if not a.print_only:
        DOC_PATH.write_text(doc)
        print(f"wrote {DOC_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
