"""Generate doc 68 from the saved Replay 24 result and owner run records."""
from argparse import ArgumentParser
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import yaml

REPO = Path(__file__).resolve().parents[1]
RUN = REPO.parent / "rig/data/replay_24"


def pct(value, digits=2):
    return "not computed" if value is None else f"{value:+.{digits}%}"


def render(out, p, commit, start, end, refused_start, validator_refusals, digest):
    m, marks, shown, coverage = (out[key] for key in ("main", "checks", "shown", "coverage"))
    met, n = sum(marks.values()), len(marks)
    verdict = "passed" if out["passed"] else "did not pass"
    twins = len(out["twins"])
    refusals = Counter(out["twin_refusals"].values())
    refused = sum(refusals.values())
    if twins + refused != p["draws"]:
        raise ValueError("saved twin counts do not reconcile")
    years = m["years"]
    final, initial = m["final"], out["account_usd"]
    excluded = coverage["spot_exclusions"]
    no_ether = 1027 not in coverage["linked_majors"]
    only_dd = " Only the drawdown mark was met." if met == 1 and marks["drawdown"] else ""
    twin_status = "not computed and not met" if out["p95"] is None else ("met" if marks["twins"] else "not met")
    dollars = lambda value,digits: "$"+f"{value:,.{digits}f}"
    spot_only = sorted(k.split("/")[1] for k,v in excluded.items() if v.startswith("No same-original"))
    other = sorted(k.split("/")[1] for k in excluded if k.split("/")[1] not in spot_only)
    cost = p["fees"][out["judged_fee"]]
    lines = [
        "# Replay 24: same-coin funding carry", "",
        f"MEASURED. Replay 24 **{verdict}**, meeting **{met} of {n} marks**.{only_dd} "
        f"The {dollars(initial,0)} account ended at {dollars(final,2)}, or {pct(m['annual'],3)} a year after the "
        f"judged Robinhood fee model. Daily Sharpe was {m['sharpe']:.3f}; the largest fall was {m['drawdown']:.2%}. "
        f"Only {twins} of {p['draws']} random twins matched, so the twin mark was {twin_status}.", "",
        f"STATED. The [frozen plan](../../research_rig/PREREG_24_same_coin_carry.md) buys spot and shorts the same coin's "
        f"perpetual in equal dollars at entry. It uses up to {p['slots']} sleeves, sized only once, enters at a lagged "
        f"seven-day funding rate of at least {p['entry']:.0%} annualized, and exits at {p['exit']:.0%} or less or on loss "
        f"of eligibility. Binance supplies the replay prices and funding; US historical funding and actual fills are UNKNOWN. "
        f"All dates, from {p['start']} 00:00 through the {p['end']} 00:00 UTC cutoff, were already viewed in "
        "[Replay 18](65_replay_18_funding_carry.md). There is no held-back period.", "",
        "## Marks and account result", "",
        "| Frozen mark | MEASURED | Verdict |", "|---|---:|---|",
    ]
    values = [
        ("annual",f"Net gain at least {p['min_annual']:.0%} a year",pct(m["annual"],3)),
        ("sharpe",f"Daily Sharpe at least {p['min_sharpe']:.1f}",f"{m['sharpe']:.3f}"),
        ("drawdown",f"Largest fall at most {p['max_drawdown']:.0%}",f"{m['drawdown']:.2%}"),
        ("positive_years",f"Positive in {p['positive_years']} of {len(years)} UTC years",
         f"{sum(v > 0 for v in years.values())} of {len(years)}"),
        ("twins",f"Strictly above the {p['percentile']*100:.0f}th percentile of all {p['draws']} twins",pct(out["p95"])),
    ]
    for key,label,value in values:
        lines.append(f"| {label} | {value} | {'met' if marks[key] else 'not met'} |")
    lines += [
        "",
        f"MEASURED. Funding added {m['funding_points']:+.2f} percentage points of starting money. "
        f"The difference between the spot and perpetual price moves contributed {m['basis_points']:+.2f} points and "
        f"fees {m['fee_points']:+.2f} points, leaving {pct(final/initial-1)} net for the whole window. "
        f"The book was in the market {m['time_in_market']:.2%} of the time, with {m['coin_hours']:,} coin-hours "
        f"and {m['trade_events']} paired trade events, including {m['margin_topups']} margin top-ups and "
        f"{m['forced']} forced close. A paired entry, exit or maintenance order counts once, not once per leg.", "",
        "| UTC year | Net gain | Paired trade events |", "|---|---:|---:|",
    ]
    for y,value in sorted(years.items()):
        label = f"{y}, partial" if y == p["end"][:4] else y
        lines.append(f"| {label} | {pct(value,3)} | {m['trades'].get(y,0)} |")
    lines += [
        "", "## Gaps and the random comparison", "",
        f"MEASURED. The approved scope covered {coverage['top_rank_lineages']} coin identities over time and "
        f"{coverage['mapped_perp_contracts']} dated perpetual listings, of which {coverage['paired_perp_contracts']} had an "
        f"approved spot link. {len(excluded)} dated listings lacked an approved link: "
        f"{', '.join(sorted(k.split('/')[1] for k in excluded))}. "
        + ("That includes ether; the shown bitcoin/ether row is bitcoin only. " if no_ether else "")
        + "This is a limit of the reviewed inputs, not a claim that the products did not exist.", "",
        f"STATED. The approved older spot records did not supply the matching coin identity for "
        f"{', '.join(spot_only)}. For {', '.join(other)}, the approved notes give a separate reason: "
        "the old OM spot window could not be reused across the token redenomination.", "",
        f"MEASURED. There were {m['unrankable_name_days']:,} otherwise eligible fresh name-days without a complete "
        f"as-of funding signal; none used a slot. Among ranked slots already assigned, {m['data_gap_slot_days']} "
        f"were blocked by missing bars or funding and {m['link_end_slot_days']} by a retrospective link end. "
        f"There were {m['unfilled_slot_days']} unfilled assigned entry slots in all and {m['missing_funding']} charged "
        "missing settlements during holds. These counts do not erase the known archive gaps listed in the plan.", "",
        f"MEASURED. {refused} of {p['draws']} random draws were refused. The plan required each draw to match "
        "the ranked book's number of holdings and additions after every daily fill, and its total coin-hours. "
        "A random book can still hold names that fall out of the available list on a day when the ranked book keeps "
        "its names. With too few available positions to keep, or too few fresh names to add, the draw cannot match.",
        "", "| Saved refusal reason | Draws |", "|---|---:|",
    ]
    lines += [f"| {reason} | {count} |" for reason,count in sorted(refusals.items())]
    lines += [
        "", "MEASURED. The saved refusals do not split how many failed for too few continuing names versus "
        "too few fresh names, or identify the affected dates. No draw was rerolled and the valid draws were not "
        "used on their own. There is no measured percentile or claim that the book beat randomness.", "",
        "## Shown only", "",
        f"STATED. The judged Robinhood model charges {cost['spot_bp']:g} bps per spot order, "
        f"{cost['perp_bp']:g} bps perpetual commission with a {dollars(cost['commission_min'],2)} minimum, "
        f"and a {cost['exchange_bp']:g} bps venue fee. The replay applies the frozen rounding rules to "
        "each executed order. These are fee assumptions, not measured execution prices.", "",
        f"MEASURED. At zero fees, the same rule made {pct(shown['flat_grid']['0'].get('annual'),1)} a year. "
        f"The highest tested flat cost with a strictly positive gain was {shown['grid_break_even_bps']} bps "
        "per leg per side. This is a grid point, not an estimate between points or a quote for a real fill.", "",
        "| Shown variant | Net gain per year |", "|---|---:|",
    ]
    for fee,label in (("kraken","Kraken stated fee model"),("flat_5","Flat 5 bps per leg per side"),("coinbase","Coinbase")):
        value = shown["fees"][fee]
        lines.append(f"| {label} | {pct(value['annual'],3) if 'annual' in value else 'UNKNOWN fee, excluded'} |")
    for threshold,value in sorted(shown["entries"].items(),key=lambda row:float(row[0])):
        lines.append(f"| Entry at {float(threshold):.0%}, Robinhood model | {pct(value.get('annual'),3)} |")
    lines.append(f"| {'Bitcoin only; ether unavailable' if no_ether else 'Bitcoin and ether'}, Robinhood model | "
                 f"{pct(shown['majors'].get('annual'),3)} |")
    lines += ["", "| Flat bps per leg per side | Net gain per year |", "|---:|---:|"]
    lines += [f"| {bps} | {pct(shown['flat_grid'][str(bps)].get('annual'),3)} |" for bps in p["grid"]]
    lines += [
        "", "## Run record", "",
        f"MEASURED. The owner validated the inputs first with {validator_refusals} hard refusals, then the one-shot "
        f"claim opened at {start} and the result was written at {end}. The approval commit was "
        f"`{commit}`. The seal SHA-256 was `{out['freeze_sha256']}`.", "",
    ]
    if refused_start:
        lines += [
            "MEASURED. An earlier start refused in authorization before a claim because the owner's shell supplied "
            "`GIT_` variables. It never opened the replay or produced a result; it was not a run.", "",
        ]
    lines += [
        f"The saved off-repo result SHA-256 is `{digest}`. The [report script](../../research_rig/report_24.py) "
        "generates this page from that result, the bound policy and the run records. No market tape, detailed schedule "
        "or saved result JSON is in the repo.",
    ]
    return "\n".join(lines)+"\n"


def main():
    ap = ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir",type=Path,default=RUN)
    run = ap.parse_args().run_dir
    result = run/"results_24.json"
    raw = result.read_bytes()
    claim = json.loads((run/"score_24.lock").read_bytes())
    check = json.loads((run.parent/"replay_24_validate.log").read_bytes())
    first = (run.parent/"replay_24_run.log").read_text()
    policy = subprocess.check_output(["git","show",claim["commit"]+":config/thresholds.yaml"],cwd=REPO)
    p = yaml.safe_load(policy)["replay_24_plan"]["value"]
    stamp = "%Y-%m-%d %H:%M UTC"
    start = datetime.fromisoformat(claim["utc"]).astimezone(timezone.utc).strftime(stamp)
    end = datetime.fromtimestamp(result.stat().st_mtime,timezone.utc).strftime(stamp)
    refused = "in authorize" in first and "unexpected override or scoring path ownership" in first
    print(render(json.loads(raw),p,claim["commit"],start,end,refused,len(check["refusals"]),sha256(raw).hexdigest()),end="")


if __name__ == "__main__":
    main()
