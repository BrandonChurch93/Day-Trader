"""Plan 22 paths, policy loading and the point-in-time list rules. No prices."""
import json
import os
from pathlib import Path

import yaml

import common_22 as G

HERE = Path(__file__).resolve().parent
if HERE.name == "research_rig":
    REPO = HERE.parent
else:                                   # off-repo draft: rig/plan22_draft
    REPO = HERE.parents[1] / "dt-work"
WS = REPO.parent
RIG = REPO / "research_rig"
R13 = WS / "rig/data/replay_13"
R16 = WS / "rig/data/replay_16"
DATA = WS / "rig/data/replay_22"
# Fixed paths. No environment variable can move them (audit B1); tests pass paths explicitly.
PLAN = REPO / "research_rig/PREREG_22_fable_rule_a.md"
DRAFT = REPO / "research_rig/PREREG_22_fable_rule_a_DRAFT.md"
CONFIG = REPO / "config/thresholds.yaml"
DRAFT_CONFIG = HERE / "config_22.yaml"
KEY = "replay_22_plan"

# CMC IDs taken out: stablecoins and other pegged tokens, wrapped or staked
# copies, and gold tokens. Each ID is from the plan 13 exclusion map. BTC, ETH,
# exchange tokens and every other ranked coin stay in.
EXCLUDE_22 = frozenset({
    825, 3408, 4687, 4943, 7129, 2563, 3330, 4779, 3306, 26081, 29470, 3792, 33039, 27772,
    19891, 6952, 36148, 34691, 34387, 39120, 33793, 5068,          # stablecoins
    3717, 2396, 8085, 12409, 28695, 24760, 32994, 5777, 6941, 4023, 18579,  # wrapped or staked
    5176, 4705,                                                     # gold tokens
})
# Coins with no plan 16/17 spot identity row because plan 13 left them out.
# One unambiguous Binance spot pair each.
DIRECT = frozenset({(1027, "ETHUSDT"), (4195, "FTTUSDT")})


def read_input(path):
    """Bytes of an input file. If only a gzip copy (path + ".gz") exists, its decompressed bytes; the pins are
    always on the uncompressed bytes, so compressing a file to save disk does not change its pin."""
    path = Path(path)
    if path.is_file():
        return path.read_bytes()
    gz = path.with_name(path.name + ".gz")
    if gz.is_file():
        import gzip
        return gzip.decompress(gz.read_bytes())
    raise FileNotFoundError(str(path))


def policy(final=True):
    raw = yaml.safe_load(CONFIG.read_bytes()) if CONFIG.exists() else {}
    if KEY in raw:
        return G.policy(raw[KEY]["value"])
    if final:
        raise RuntimeError(f"{KEY} is not in config/thresholds.yaml")
    return G.policy(yaml.safe_load(DRAFT_CONFIG.read_bytes())[KEY]["value"])


def top_rows(page, p):
    """Raw ranks 1 to top_rank only; nothing below is kept or returned."""
    rows = [r for r in page["top_raw"] if 1 <= r["cmcRank"] <= p["top_rank"]]
    ranks = sorted(r["cmcRank"] for r in rows)
    if ranks != list(range(1, p["top_rank"] + 1)) or len({r["id"] for r in rows}) != len(rows):
        raise ValueError(f"page {page.get('date')} lacks a full unique top {p['top_rank']}")
    return [r for r in sorted(rows, key=lambda r: r["cmcRank"]) if r["id"] not in EXCLUDE_22]


def page_at(pages, w, p):
    """Latest page known strictly before wake hour w and no older than the age limit."""
    best = None
    for s in pages:
        if s["known_at"] < w * 3600 and (best is None or s["known_at"] > best["known_at"]):
            best = s
    if best is None or w * 3600 - best["known_at"] > p["max_page_age_days"] * 86400:
        return None
    return best
