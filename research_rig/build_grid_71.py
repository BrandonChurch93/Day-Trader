"""Fixed second overextension grid. No prices or result files are inputs."""
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "btc_overextension_fade"
THRESHOLDS = (0.01, 0.015, 0.025, 0.04)


def key(rule):
    p = rule["parameters"]
    return (p["threshold"], p["multiple"], p["lag"], rule["hold_hours"], rule["side"],
            rule.get("delay_hours", 0), rule["btc_hedge"], rule.get("top_coins", 1))


def build(old_grid):
    old = {key(r) for r in old_grid if r["family"] == FAMILY}
    picked = []

    def add(thresholds, multiples, lags, holds, sides, delay=0, hedge=False, top=1):
        for spec in itertools.product(thresholds, multiples, lags, holds, sides, (delay,), (hedge,), (top,)):
            if spec not in old:
                picked.append(spec)

    add(THRESHOLDS, (1.5, 2., 3.), (1, 2, 4), (2,), (1,))
    add((.015, .025), (2.,), (1, 2, 4), (1, 4, 6), (1,))
    add(THRESHOLDS, (2.,), (1, 2, 4), (2,), (-1,))
    add((.015, .025), (2.,), (2,), (1, 4, 6), (-1,))
    for change in ({"delay": 1}, {"hedge": True}, {"top": 2}):
        add(THRESHOLDS, (2.,), (2,), (2, 4), (1, -1), **change)
    if len(picked) != 112 or len(set(picked)) != 112:
        raise ValueError("expected 112 unique new rule specifications")
    base = next(r for r in old_grid if r["id"] == "70-102")
    return [{**base, "id": f"71-{i:03}", "side": side,
             "parameters": {"threshold": cut, "multiple": multiple, "lag": lag},
             "hold_hours": hold, "btc_hedge": hedge, "delay_hours": delay, "top_coins": top,
             "entry": "hourly open, one hour past ordinary entry" if delay else base["entry"]}
            for i, (cut, multiple, lag, hold, side, delay, hedge, top) in enumerate(picked, 1)]


def grid_bytes(grid):
    return (json.dumps(grid, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


if __name__ == "__main__":
    (HERE / "GRID_71.json").write_bytes(grid_bytes(build(json.loads((HERE / "GRID_70.json").read_bytes()))))
