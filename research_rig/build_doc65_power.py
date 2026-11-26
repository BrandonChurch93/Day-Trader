"""Write the Plan 65 power block into its plan from research_rig/POWER_65.json. Reads no prices and runs no rule.
Run: python3 research_rig/build_doc65_power.py"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = HERE / "PREREG_65_stock_bond_rebalance_spread.md"
START, END = "<!-- power_65 start -->", "<!-- power_65 end -->"
NAMES = {"normal": "Normal", "t4": "Student t, 4 df", "skew_iid": "Skew mix 5.23, jumps spread out",
         "skew_burst": "Skew mix 5.23, jumps in 5-session runs", "skew_half": "Soft mix, jumps carry 30% of the mean"}


def block(j):
    sh = [0.9, 0.6, 0.45, 0.3]
    t = ["MEASURED from `POWER_65.json` (synthetic, no market data). "
         f"{j['N_judged']} judged sessions, {j['n_week_clusters']} week clusters, {j['seeds']} seeds a cell, "
         f"jump share of days {j['p_jump']}. Each cell is the share of runs that meet all five marks. "
         "The even-chance column is the lowest net Sharpe on a 0.05 grid from 0.30 at which at least half the runs pass.", "",
         "| Noise shape | Net Sharpe 0.9 | 0.6 | 0.45 | 0.3 | Even chance needs net Sharpe |",
         "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for k, name in NAMES.items():
        cells = [next(r for r in j["table"] if r["kind"] == k and r["sharpe"] == s)["pass_all"] for s in sh]
        e = j["even_chance_sharpe"][k]
        t.append(f"| {name} | " + " | ".join(f"{c:.1%}" for c in cells) + f" | {'above 2.0' if e is None else f'{e:.2f}'} |")
    m = j["mix"]
    t += ["", "In the skew mix the jump days carry this share of the true mean: "
          + ", ".join(f"{m[str(s)]['skew_iid_jump_share_of_mean']:.0%} at Sharpe {s}" for s in sh)
          + ". Above 100% means the other days lose on average. The soft mix has skew "
          + ", ".join(f"{m[str(s)]['skew_half_skew']:.2f}" for s in sh) + " at the same four Sharpe levels."]
    worst = max(v for v in j["even_chance_sharpe"].values() if v is not None) if all(
        v is not None for v in j["even_chance_sharpe"].values()) else None
    t += ["", "Close rule, fixed before bars: if an even chance needs a net Sharpe above 0.9, the row closes. "
          + ("Worst shape here needs " + f"{worst:.2f}" + (", so the row stays open." if worst <= 0.9 else ", so the row closes.")
             if worst is not None else "One shape never reaches an even chance below 2.0, so the row closes.")]
    return "\n".join(t)


def main():
    j = json.loads((HERE / "POWER_65.json").read_text())
    s = PLAN.read_text()
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: START + "\n" + block(j) + "\n" + END, s, flags=re.S)
    if new != s:
        PLAN.write_text(new)


if __name__ == "__main__":
    main()
