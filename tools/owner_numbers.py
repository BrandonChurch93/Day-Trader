"""Writes the two number tables in docs/decisions/morning_list_2026-11-25.md from config/thresholds.yaml, so that no
threshold or suggested value on the owner's list is typed by hand.
Run from the repo root:  python3 tools/owner_numbers.py --write     (tools/check_repo.py fails if the tables are out of date)
The words in WHAT and MARKS are descriptions. Every number comes from the config file."""
import re, sys
PAGE = "docs/decisions/morning_list_2026-11-25.md"
START, END = "<!-- numbers:start (written by tools/owner_numbers.py from config/thresholds.yaml, do not edit by hand) -->", "<!-- numbers:end -->"
MARKS = [("1", "replay_max_drop_ratio_vs_hold", "In the held-back years the rule must have a better Sharpe ratio than holding, and its largest drop may be at most this share of holding's largest drop. Since the audits the crypto rules must also hold with the order filled one hour late"),
         ("2", "backtest_min_breakeven_cost_multiple", "The rule must stay ahead of holding up to a cost that is this many times the modeled cost"),
         ("3", "replay_min_deflated_sharpe", "The deflated Sharpe ratio, which marks a result down for every rule that was tried, must be at least this"),
         ("4", "backtest_max_pbo", "The overfitting estimate must be below this"),
         ("5", "replay_min_shuffle_percentile", "The rule must beat this share of copies of itself with its in and out spells put in random order")]
WHAT = [("live_starting_capital_usd", "Money in the live account at the start, in dollars"),
        ("live_max_position_usd", "The most held in one position, in dollars"),
        ("live_max_daily_loss_usd", "The most the account may lose in one day before it stops for the day, in dollars"),
        ("live_max_total_loss_usd", "The most the account may lose in total before it stops and waits for you, in dollars"),
        ("moonshot_sleeve_share", "Share of the account set aside for high-risk ideas"),
        ("moonshot_max_position_share", "The most of the account in any one high-risk idea"),
        ("api_model_spend_cap_usd_month", "The most the running service may spend on AI model calls in a month, in dollars")]
def config():
    out, key = {}, None
    for line in open("config/thresholds.yaml"):
        m = re.match(r"^([a-z0-9_]+):\s*$", line)
        if m: key = m.group(1); out[key] = {}; continue
        m = re.match(r"^  ([a-z_]+):\s*(.*)$", line)
        if m and key: out[key][m.group(1)] = m.group(2).strip()
    return out
def block():
    c = config()
    t = START + "\n| Pass mark | What it asks | Value now | Key | Status in the config file |\n|---|---|---|---|---|\n"
    for n, k, w in MARKS: t += f"| {n} | {w} | {c[k]['value']} | `{k}` | {c[k]['status']} |\n"
    t += "\n| What the number is | Research's suggestion, not a value in use | Key |\n|---|---|---|\n"
    for k, w in WHAT:
        assert c[k]["status"] == "open" and c[k]["value"] == "null", k
        t += f"| {w} | {c[k]['recommended']} | `{k}` |\n"
    return t + END
def in_sync():
    s = open(PAGE).read(); m = re.search(re.escape(START) + r".*?" + re.escape(END), s, re.S); return bool(m) and m.group(0) == block()
if __name__ == "__main__":
    if "--write" in sys.argv:
        s = open(PAGE).read(); m = re.search(re.escape(START) + r".*?" + re.escape(END), s, re.S)
        assert m, PAGE + " has no numbers markers"; open(PAGE, "w").write(s[:m.start()] + block() + s[m.end():]); print(PAGE + " number tables written")
    else: print(block())
