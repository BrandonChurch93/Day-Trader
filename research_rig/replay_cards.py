"""Test cards for Replays 48, 52, 53 and 60, read from their published result pages.

The saved results for these replays are kept outside the repo. Each card therefore reads its figures, at export
time, from the result page in docs/research/ (and, for Replay 48, from research_rig/REVIEW_48_identity.md). Only
labels and plain wording are written here. If a page no longer has the line or table a card needs, the export
stops with an error instead of showing a guess. Reads no prices and runs nothing.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P48 = "docs/research/103_replay_48_muni_cef_january.md"
P52 = "docs/research/113_replay_52_quarter_end_corporate_bond_funds.md"
P53 = "docs/research/122_replay_53_taxable_fund_january_rebound.md"
P60 = "docs/research/126_replay_60_special_dividends.md"
R48 = "research_rig/REVIEW_48_identity.md"


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def need(pattern, text, path, flags=0):
    m = re.search(pattern, text, flags)
    if not m:
        raise ValueError(f"replay card: {path} no longer has the line the card reads ({pattern!r})")
    return m


def section(text, title, path):
    return need(rf"^## {re.escape(title)}[ \t]*\n(.*?)(?=^## |\Z)", text, path, re.M | re.S)[1]


def table(text, path):
    """The first Markdown table in text, as a list of dicts keyed by header."""
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("|")]
    if len(lines) < 3:
        raise ValueError(f"replay card: {path} has no table where the card reads one")
    cells = lambda l: [c.strip() for c in l.strip("|").split("|")]
    head = cells(lines[0])
    return [dict(zip(head, cells(l))) for l in lines[2:]]


def minus(s):
    """Signed figures as printed on the page, with a true minus sign for losses."""
    return s.replace("-", "\u2212")


def money(s):
    """'+$13.68' or '-$15.86' from a page, shown as $13.68 or \u2212$15.86."""
    sign, amount = need(r"^([+-]?)\$([\d,]+\.\d{2})$", s, "money").groups()
    return ("\u2212" if sign == "-" else "") + "$" + amount


def head(text, path):
    """Verdict, marks met, marks in all, and run date from the page's opening MEASURED line."""
    m = need(r"^MEASURED\.[^\n]*?(Passed|did not pass|Did not pass)[^\n]*?\*\*(\d+) of (\d+) frozen marks\*\*", text, path, re.M)
    date = need(r"\b(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} UTC", text, path)[1]
    return m[1].lower() == "passed", int(m[2]), int(m[3]), date


def mark_rows(text, path):
    rows, met, missed = [], 0, []
    for r in table(section(text, "Frozen marks", path), path):
        label = r["Mark"] + (f": {r.get('Bar') or r.get('Frozen bar')}" if (r.get("Bar") or r.get("Frozen bar")) else "")
        rows.append([label, f"{minus(r['Measured'])}, {r['Verdict']}"])
        met += r["Verdict"] == "met"
        if r["Verdict"] != "met": missed.append(r["Mark"])
    return rows, met, missed


def card(id_, title, path, what, extra_lines, extra_rows, links):
    text = read(path)
    passed, n_met, n_all, date = head(text, path)
    rows, met, missed = mark_rows(text, path)
    if met != n_met or len(rows) != n_all:
        raise ValueError(f"replay card: {path} opening line says {n_met} of {n_all} marks, its table shows {met} of {len(rows)}")
    verdict = ("Passed" if passed else "Did not pass") + f", {n_met} of {n_all} marks"
    summary = " ".join([what, f"It {'met all' if n_met == n_all else 'met'} {n_met} of {n_all} frozen marks"
                        + ("" if passed or n_met == n_all else ", and all had to be met") + "."]
                       + ([f"Missed: {'; '.join(missed)}."] if missed and len(missed) < n_all else []) + extra_lines)
    return dict(id=id_, title=title, date=date, verdict=verdict,
                tone="mixed" if passed else "fail",     # the rule the other cards use: mixed when something passes, fail when nothing does
                basis=f"MEASURED in one scored run. Figures read from {os.path.basename(path)}"
                      + (f" and {os.path.basename(R48)}" if id_ == "replay48" else "") + ". The saved result is kept off the repo.",
                summary=summary, numbers=rows + extra_rows, links=links)


def card_48(gh):
    text = read(P48)
    turns = need(r"Over (\d+) yearly turns", text, P48)[1]
    dollars = need(r"mean net result was ([+-]?\$[\d,]+\.\d{2}) a year", section(text, "In dollars", P48), P48)[1]
    rev = read(R48)
    need(r"\*\*Outcome: the Replay 48 pass stands; the picks are unchanged\.\*\*", rev, R48)
    sym, wrong = need(r"traded on the NYSE as (\w+) through \d{4} but is listed in `roster\.csv` under the symbol (\w+)", rev, R48).groups()
    need(rf"{sym} was eligible in all nine turns and outside the worst five in all nine", rev, R48)
    review = (f"Identity review: one fund, {sym}, was listed under a wrong symbol ({wrong}). "
              f"It was checked and would not have been picked in any turn, so the pass stands.")
    return card("replay48", "Muni closed-end funds in January", P48,
                f"Buys the five muni closed-end funds that fell most in the year, at the last December close, and sells at the last January close. {turns} yearly turns.",
                [review, "A pass means worth watching with pretend money, not that it makes money."],
                [["Mean net result on $500, once a year, before taxes", money(dollars)]],
                [["Replay 48", gh + P48], ["Identity review", gh + R48], ["Plan", gh + "research_rig/PREREG_48_muni_cef_tax_loss.md"]])


def card_52(gh):
    text = read(P52)
    q = need(r"across (\d+) quarters", text, P52)[1]
    dollars = need(r"mean net result was ([+-]?\$[\d,]+\.\d{2}) per quarter-end basket", section(text, "In dollars", P52), P52)[1]
    return card("replay52", "Corporate bond funds after quarter-end", P52,
                f"Buys four corporate bond funds at the last close of each quarter and sells three sessions later. {q} quarters.",
                ["The rule does not advance."],
                [["Mean net result on $500, per quarter-end, before taxes", money(dollars)]],
                [["Replay 52", gh + P52], ["Plan", gh + "research_rig/PREREG_52_quarter_end_dealer_rebound.md"]])


def card_53(gh):
    text = read(P53)
    shown = section(text, "Shown only", P53)
    fifth = next((r for r in table(shown, P53) if "fifth January session" in r["Line"]), None)
    if fifth is None:
        raise ValueError(f"replay card: {P53} has no fifth January session line")
    need(r"cannot be counted as a pass", shown, P53)
    corr = need(r"Pearson correlation with the \[Replay 48 yearly portfolio results\]\([^)]*\) was ([+-]\d\.\d+)", shown, P53)[1]
    turns = len([r for r in table(section(text, "The ten turns", P53), P53) if r["Turn"].isdigit()])
    mean = next(r for r in table(section(text, "The ten turns", P53), P53) if r["Turn"] == "Mean")
    dollars = section(text, "In dollars", P53)
    d = need(r"mean net result was ([+-]?\$[\d,]+\.\d{2}), versus ([+-]?\$[\d,]+\.\d{2}) for PCEF and ([+-]?\$[\d,]+\.\d{2}) for the roster\. "
             r"The worst turn was ([+-]?\$[\d,]+\.\d{2}) and the best was ([+-]?\$[\d,]+\.\d{2})", dollars, P53).groups()
    return card("replay53", "Taxable closed-end funds in January", P53,
                f"Buys the five taxable closed-end funds that fell most in the year, at the last December close, and sells at the last January close. {turns} yearly turns.",
                ["The exit on the fifth January session is shown only. It was looked at after the fact, so it cannot count as a pass.",
                 f"Its yearly results move with the muni version, Replay 48 (correlation {minus(corr)}, shown only), so it is not a second independent result.",
                 "The rule does not advance."],
                [["Mean net per turn: portfolio, PCEF, all eligible funds", f"{minus(mean['Portfolio net'])}, {minus(mean['PCEF'])}, {minus(mean['Roster equal weight'])}"],
                 ["Mean net result on $500, once a year, before taxes", money(d[0])],
                 ["Same for PCEF, and for all eligible funds", f"{money(d[1])}, {money(d[2])}"],
                 ["Worst and best turn on $500", f"{money(d[3])}, {money(d[4])}"],
                 ["Fifth January session exit, shown only, cannot count", f"{minus(fifth['Portfolio mean'])} mean, {fifth['Positive turns']} positive"],
                 ["Correlation with Replay 48 yearly results, shown only", minus(corr)]],
                [["Replay 53", gh + P53], ["Plan", gh + "research_rig/PREREG_53_taxable_cef_tax_loss.md"], ["Replay 48", gh + P48]])


def card_60(gh):
    text = read(P60)
    judged = {r["Line"]: r for r in table(section(text, "Judged block", P60), P60)}
    stock, iwm, paired = (judged[k] for k in ("Stock", "Matched IWM", "Stock minus IWM"))
    events = need(r"^MEASURED\. The (\d+) filing events", section(text, "Decisions and refusal reasons", P60), P60, re.M)[1]
    basis = need(r"^\| Refused: stock or IWM vendor basis \| (\d+) \|", text, P60, re.M)[1]
    shown = section(text, "Shown only", P60)
    need(r"None of these figures can count toward a mark", shown, P60)
    spy = need(r"^\| Stock minus SPY \| (\d+) \| ([+-][\d.]+%) \|", shown, P60, re.M).groups()
    capital, pnl, gain = need(r"Starting with (\$[\d,]+) in .*? made ([+-]\$[\d,]+\.\d{2}) total net, "
                              r"or ([+-][\d.]+%) of starting cash",
                              section(text, "Settled sleeves on starting cash", P60), P60).groups()
    return card("replay60", "Special-dividend declarations", P60,
                f"Buys whole shares after special-dividend declarations and compares with IWM on the same clocks. "
                f"{stock['Pairs']} matched pairs from {events} filing events.",
                [f"The stock mean was positive, but the lead over IWM was too small relative to its variation. "
                 f"Vendor basis checks refused {basis} events.",
                 "The SPY check and the settled sleeves are shown only and cannot count toward a mark.",
                 "The rule does not advance."],
                [["Mean net: stock, matched IWM, stock minus IWM",
                  ", ".join(minus(r["Mean net"]) for r in (stock, iwm, paired))],
                 ["Stock minus SPY, shown only", f"{minus(spy[1])} on {spy[0]} pairs"],
                 [f"Settled sleeves on {capital}, shown only", f"{money(pnl)} net, {minus(gain)} of starting cash"]],
                [["Replay 60", gh + P60], ["Plan", gh + "research_rig/PREREG_60_special_dividends.md"]])


def cards(gh):
    return [card_48(gh), card_52(gh), card_53(gh), card_60(gh)]
