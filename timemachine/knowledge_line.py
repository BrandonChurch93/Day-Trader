"""Measures where each model's knowledge of crypto prices stops, so replays can be read with that in mind. No money, no trading.

The question, fixed before any model was asked (2026-11-25): from memory alone, with no lookups, give the month-end price in US dollars of
bitcoin, ether and solana for every month from 2025-01 to 2026-11, or null where the model does not know, and name the latest month it knows
anything about. A model with no memory of a month can only guess.

How it is read:
- A month is a "hit" for a model when at least two of the three coins are within `tm_knowledge_hit_within` of the tape's month-end close.
- For comparison, "carried forward" counts the hits the model would get by repeating its own answer for its stated latest month in every later month.
  Hits after the stated latest month that are no more than that count are what a guess gives.
- The months that matter are the replay months, 2026-07 to 2026-11.

python3 timemachine/knowledge_line.py --question         prints the question sent to each model
python3 timemachine/knowledge_line.py                    reads the answers in $TM_NOTES/knowledge/<MODEL>.json and the tape, writes
                                                         timemachine/knowledge_lines.json and docs/research/31_model_knowledge_lines.md
The stored files hold the models' answers and hit marks only. No tape price is written out."""
import datetime as dt
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
NOTES = Path(os.environ.get("TM_NOTES", "/home/user/workspace/rig/tm_notes")) / "knowledge"
OUT = ROOT / "timemachine" / "knowledge_lines.json"
DOC = ROOT / "docs" / "research" / "31_model_knowledge_lines.md"
MODELS = [("OPUS", "Claude Opus 5.5"), ("SOL", "GPT-6.2 Sol"), ("NEON", "Gemini Neon"), ("SONNET", "Claude Sonnet 5.5"), ("KIMI", "Kimi K3"), ("GROK", "Grok 4.7")]
COINS = ["BTC/USD", "ETH/USD", "SOL/USD"]
MONTHS = [f"{y}-{m:02d}" for y in (2025, 2026) for m in range(1, 13) if (y, m) <= (2026, 11)]
REPLAY = ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]


def question(tag):
    return f"""This is a memory test. It is not a trading task and nothing depends on a good score. An honest "I do not know" is the most useful answer you can give.

Rules:
- Answer from your own memory only. Do not search the web, do not open any page, do not read any file, do not run any program that fetches data, do not ask another agent.
- If you do not know a value, write null. Do not guess from a trend. Do not fill a month in because the months around it are filled in.

Question: what was the price in US dollars of bitcoin (BTC), ether (ETH) and solana (SOL) at the end of each month from 2025-01 to 2026-11?
For 2026-11 use the last day you know of.

Write your answer as one JSON file at {NOTES}/{tag}.json, in exactly this shape, with every month from 2025-01 to 2026-11 present for each coin:
{{"BTC/USD": {{"2025-01": 12345, "2025-02": null}}, "ETH/USD": {{}}, "SOL/USD": {{}}, "latest_month_known": "YYYY-MM", "how_sure": "one or two plain sentences on where your memory gets thin"}}

"latest_month_known" is the latest month about which you remember anything at all in the crypto market.
Writing that one file is the only tool use allowed. Then send me one line: done, and your latest_month_known."""


def month_end_closes():
    from timemachine.tape import Tape
    t = Tape(); out = {}
    now = dt.datetime(2026, 11, 25, tzinfo=dt.timezone.utc)
    for c in COINS:
        bars = t.bars(c, "1Day", dt.datetime(2024, 12, 25, tzinfo=dt.timezone.utc), now)
        last = {}
        for b in bars:
            last[b["t"].strftime("%Y-%m")] = b["c"]          # the last daily bar of each month wins
        out[c] = last
    return out


def config(key):
    import re
    txt = (ROOT / "config" / "thresholds.yaml").read_text()
    m = re.search(rf"^{key}:\n(?:  .*\n)*?  value: ([0-9.]+)", txt, re.M)
    return float(m.group(1))


def build():
    tol = config("tm_knowledge_hit_within"); true = month_end_closes(); out = dict(hit_within=tol, months=MONTHS, replay_months=REPLAY, models={})
    for tag, name in MODELS:
        p = NOTES / f"{tag}.json"
        if not p.exists():
            out["models"][tag] = dict(name=name, answered=False); continue
        a = json.loads(p.read_text()); rows = {}

        def near(c, mo, v):
            return v is not None and mo in true[c] and abs(float(v) / true[c][mo] - 1) <= tol

        for mo in MONTHS:
            vals = {c: (a.get(c) or {}).get(mo) for c in COINS}
            rows[mo] = dict(answers=vals, given=sum(v is not None for v in vals.values()), near=sum(near(c, mo, v) for c, v in vals.items()))
            rows[mo]["hit"] = rows[mo]["near"] >= 2
        stated = a.get("latest_month_known")
        carried = None
        if stated in rows:
            base = rows[stated]["answers"]
            carried = [mo for mo in MONTHS if mo > stated and sum(near(c, mo, base[c]) for c in COINS) >= 2]
        hits = [mo for mo in MONTHS if rows[mo]["hit"]]
        out["models"][tag] = dict(name=name, answered=True, stated_latest_month=stated, how_sure=a.get("how_sure"), months=rows,
                                  last_hit=hits[-1] if hits else None, hits_after_stated=[mo for mo in hits if stated and mo > stated],
                                  carried_forward_hits=carried, replay_hits=[mo for mo in REPLAY if rows[mo]["hit"]],
                                  replay_given=[mo for mo in REPLAY if rows[mo]["given"]])
    return out


def doc(o):
    L = ["# Where each model's memory of crypto prices stops", "",
         "Made by `timemachine/knowledge_line.py` from `timemachine/knowledge_lines.json`. Do not edit by hand. No money and no trading.", "",
         "## Why this was measured", "",
         "- The time machine replays July to November 2026. A model that remembers those months would look skilled and would not be.",
         "- Each model was asked once, from memory and with no lookups, for the month-end price of bitcoin, ether and solana from 2025-01 to 2026-11, with null where it does not know.",
         f"- A month is a hit when at least two of the three coins are within {o['hit_within']:.0%} of the tape's month-end price (`tm_knowledge_hit_within`).",
         "- \"Carried forward\" is how many later months would be hits if the model just repeated its answer for its stated latest month. Hits no more than that are what a guess gives.", "",
         "## Result", "",
         "| Model | Latest month it says it knows | Last month it got right | Replay months it answered | Replay months it got right | Later hits by carrying its last answer forward |", "|---|---|---|---|---|---|"]
    for tag, _ in MODELS:
        m = o["models"][tag]
        if not m["answered"]:
            L.append(f"| {m['name']} | not asked yet | | | | |"); continue
        cf = m["carried_forward_hits"]
        L.append(f"| {m['name']} | {m['stated_latest_month'] or 'not given'} | {m['last_hit'] or 'none'} | {len(m['replay_given'])} of {len(o['replay_months'])} | "
                 f"{len(m['replay_hits'])} of {len(o['replay_months'])}{' (' + ', '.join(m['replay_hits']) + ')' if m['replay_hits'] else ''} | {'n/a' if cf is None else len(cf)} |")
    L += ["", "## Month by month", "", "Each cell: coins answered, then coins within the band. A dash means it answered null for all three.", "",
          "| Month | " + " | ".join(n for _, n in MODELS) + " |", "|---|" + "---|" * len(MODELS)]
    for mo in o["months"]:
        cells = []
        for tag, _ in MODELS:
            m = o["models"][tag]
            if not m["answered"]:
                cells.append(""); continue
            r = m["months"][mo]; cells.append("-" if not r["given"] else f"{r['given']} / {r['near']}{' hit' if r['hit'] else ''}")
        L.append(f"| {mo}{' (replay)' if mo in o['replay_months'] else ''} | " + " | ".join(cells) + " |")
    L += ["", "## What each model said about its own memory", ""]
    for tag, _ in MODELS:
        m = o["models"][tag]
        if m["answered"]:
            L.append(f"- {m['name']}: {(m['how_sure'] or 'nothing given').replace(chr(10), ' ')}")
    L += ["", "## What this does not show", "",
          "- One question, asked once. A model can know events without knowing prices, or the other way round.",
          "- The no-lookup rule was given by instruction. The agent that answered had tools it was told not to use.",
          "- The agent could see today's date. It could not see prices unless it broke the rule.",
          "- A hit by luck is possible when prices move little. The carried-forward column is there to show how much luck gives.", ""]
    return "\n".join(L)


def main():
    if "--question" in sys.argv:
        print(question("MODEL")); return
    o = build(); OUT.write_text(json.dumps(o, indent=1, sort_keys=True) + "\n"); DOC.write_text(doc(o))
    for tag, _ in MODELS:
        m = o["models"][tag]
        print(tag, "not asked" if not m["answered"] else (m["stated_latest_month"], m["last_hit"], m["replay_hits"], m["carried_forward_hits"]))


if __name__ == "__main__":
    main()
