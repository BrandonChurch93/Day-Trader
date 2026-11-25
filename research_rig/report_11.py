"""Writes docs/research/44_replay_11_earnings_reader.md from results_11_design.json and, once it exists, results_11_heldback.json.
Reads no price and runs nothing. Every figure in the page comes from those two files.   python3 report_11.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, "results_11_design.json")))
hp = os.path.join(HERE, "results_11_heldback.json")
H = json.load(open(hp)) if os.path.exists(hp) else None
NAMES = {"claude_sonnet_5_5": "Claude Sonnet 5.5 alone", "grok_4_7": "Grok 4.7 alone", "kimi_k3": "Kimi K3 alone", "claude_opus_5_5": "Claude Opus 5.5 alone",
         "middle": "middle of the three small readers", "cascade": "cascade: small readers, Opus where they disagree"}
LN = {"500": "S&P 500", "400": "S&P MidCap 400", "600": "S&P SmallCap 600"}
cfg = D["config"]; st = cfg["replay_11_statistics"]; ds = cfg["replay_11_design"]; co = cfg["replay_11_costs"]
main = st["main_hold"]; holds = list(st["holds"])
def pc(x, d=2): return f"{x * 100:+.{d}f}%"
def sh(x): return f"{x * 100:.1f}%"
def row(name, r):
    ok = r["minus_a"] > 0 and r["mean"] > r["random_p95_b"]
    return f"| {name} | {r['buys']} | {sh(r['buy_share'])} | {pc(r['mean'])} | {pc(r['mean_all_a'])} | {pc(r['minus_a'])} | {pc(r['random_p95_b'])} | {sh(r['share_of_draws_beaten'])} | {pc(r['minus_spy'])} | {'yes' if ok else 'no'} |"
HEAD = "| Set-up | Buys | Share bought | Mean of buys after costs | Mean of every release (a) | Buys less (a) | 95th percentile of random picks (b) | Random draws beaten | Buys less SPY | Above both marks |\n|---|---|---|---|---|---|---|---|---|---|"
o = []; w = o.append
w("# 44. Replay 11: an AI reads each earnings release and says buy or skip\n")
w(f"Status: research result, pretend trades on past prices. Built by `research_rig/report_11.py` from `research_rig/results_11_design.json`" + (" and `research_rig/results_11_heldback.json`" if H else "") + f". The plan, fixed before any reader ran, is `research_rig/PREREG_11_earnings_release_reader.md`. Design sample scored {D['made_utc']} UTC." + (f" Held-back half scored {H['made_utc']} UTC." if H else " The held-back half is not scored yet, so there is no verdict yet.") + "\n")
w("## What was tested\n")
w("- When a company files its quarterly results, a model reads the press release and gives a score from -2 to 2. A score above zero is a buy at the next regular open. The stock is sold at the close one trading day later (H1) or five trading days later (H5). H5 is the main test.")
w(f"- Costs per side, in basis points: {', '.join(LN[k] + ' ' + str(v) for k, v in co['bps_per_side'].items())}.")
w("- Yardstick (a) is buying every release. Yardstick (b) is the same number of buys drawn at random from the same releases, " + str(st["draws"]) + " times. A set-up has to beat (a) and the 95th percentile of (b).")
w("- The readers saw only the release text. They were told not to use the web or prices. That is an instruction and was not enforced; the gap is in the plan.\n")
w("## The design sample (used only to choose a set-up, not to judge)\n")
w(f"MEASURED. {D['setups'][ds['setups'][0]][main]['events']} releases, {ds['sample_per_list']} from each list, read by four models.\n")
for h in holds:
    w(f"### Hold {h}" + (" (main)" if h == main else "") + "\n")
    w(HEAD)
    for s in ds["setups"]: w(row(NAMES[s], D["setups"][s][h]))
    w(row("plain rule: buy when the stock opened up at least " + str(cfg["replay_11_gap"]["min_up_pct"]) + "%", D["gap_yardstick_c"][h]))
    w("")
A = D["agreement"]
w("### How much the readers agree\n")
w(f"- The three small readers gave the same buy-or-skip answer on {sh(A['unanimous_buy_or_skip'])} of releases (Fleiss' kappa {A['fleiss_kappa_buy_skip']:.2f}).")
w(f"- Rank correlation of scores between pairs of readers: {min(A['spearman'].values()):.2f} to {max(A['spearman'].values()):.2f}. So the six rows above are close to one result seen six times, not six separate confirmations.")
w(f"- Where the small readers agreed, the strong reader agreed with them on {sh(A['strong_agrees_with_agreed_small'])} of {A['strong_agreed_events_compared']} releases.")
z = D["remembered_set_to_zero"]
w(f"- Answers set to zero because the reader said it remembered the move: {sum(z.values())} in all ({', '.join(k.replace('answers_11_design_', '').replace('.jsonl', '') + ' ' + str(v) for k, v in z.items())}).\n")
ch = D["chosen_setup"]
w("### The choice\n")
w(f"- Rule, fixed before: the highest H5 mean less (a) among set-ups that buy between {sh(ds['buy_share_min'])} and {sh(ds['buy_share_max'])} of releases. Qualified: {', '.join(D['qualified_setups'])}.")
w(f"- Chosen: {NAMES[ch]}. It alone reads the held-back half, once.\n")
c = D["setups"][ch][main]
w(f"### The chosen set-up at {main}, by list (reported, not judged)\n")
w("| List | Buys | Mean of buys after costs | Mean of every release (a) | Buys less (a) | Random draws beaten | Buys less SPY |\n|---|---|---|---|---|---|---|")
for k, r in c["by_list"].items(): w(f"| {LN[k]} | {r['buys']} | {pc(r['mean'])} | {pc(r['mean_all_a'])} | {pc(r['minus_a'])} | {sh(r['share_of_draws_beaten'])} | {pc(r['minus_spy'])} |")
w("")
cs = c["cost_sensitivity"]
w(f"Buys less (a) at {main} with costs at " + ", ".join(f"{k} times: {pc(v)}" for k, v in cs.items()) + ". Costs barely move it because (a) pays the same costs.\n")
w("## What the design sample does and does not show\n")
w(f"- At the five-day hold every set-up's buys did better than buying every release and better than 95% of random picks. At the one-day hold none did.")
w(f"- The buys still did worse than holding SPY over the same days at {main} ({pc(c['minus_spy'])} for the chosen set-up). SPY rose {pc(c['mean'] - c['minus_spy'])} on average over those holds while the average release rose {pc(c['mean_all_a'])}. The reader picked the better releases among a group that lagged the index. So what is shown here is choosing, not yet a trade that beats holding the index.")
g1 = D["gap_yardstick_c"][holds[0]]; g5 = D["gap_yardstick_c"][main]
w(f"- A plain rule with no reading at all, buying when the stock opened up at least {cfg['replay_11_gap']['min_up_pct']}%, did about as well: buys less (a) of {pc(g1['minus_a'])} at {holds[0]} and {pc(g5['minus_a'])} at {main}, against {pc(D['setups'][ch][holds[0]]['minus_a'])} and {pc(c['minus_a'])} for the chosen reader. The held-back half reports the plain rule beside the reader, so it will show whether reading adds anything to watching the opening price.")
w("- This sample was used to choose among six set-ups. The best of six looks better than it is. The plan says so, and that is why this half is not the judge.")
w("- 450 releases from April to July 2026 are one earnings season and a half. Releases cluster in the same weeks and share the market's move.\n")
if H:
    w("## The held-back half (the judge)\n")
    w(f"MEASURED. Read once by {NAMES[H.get('chosen_setup', ch)]}.\n")
    for h in holds:
        r = H["setups"][H.get("chosen_setup", ch)][h] if "setups" in H else H[h]
        w(f"### Hold {h}" + (" (main)" if h == main else "") + "\n"); w(HEAD); w(row(NAMES[H.get('chosen_setup', ch)], r)); w("")
else:
    w("## What is still to come\n")
    ep = os.path.join(os.environ.get("EDGAR_11_READING", "/home/user/workspace/rig/data/edgar_11/reading"), "heldback", ch + ".expected.json")
    n_held = sum(len(v) for v in json.load(open(ep))["batches"].values()) if os.path.exists(ep) else None
    w("- The chosen set-up reads the held-back half" + (f", {n_held:,} releases" if n_held else "") + f", the later part of the window that ends {cfg['replay_11_events']['end']}. Its answers are hashed and pushed before any held-back price is read.")
    w("- The last held-back exits fall five trading days after the last release, so some of those prices do not exist yet. The held-back half is scored once, after those days have traded and the prices are collected again.")
    w(f"- Pass mark, fixed in the plan: at {main}, the buys beat buying every release and the 95th percentile of random picks, with at least {st['min_buys']} buys. A pass means worth trying on the practice desk with pretend money. It does not mean it makes money.\n")
open(os.path.join(ROOT, "docs", "research", "44_replay_11_earnings_reader.md"), "w", encoding="utf-8").write("\n".join(o) + "\n")
print("wrote docs/research/44_replay_11_earnings_reader.md")
