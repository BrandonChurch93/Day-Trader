"""Check the deeper steady-volume USD hourly pulls. Reads prices but runs no rules."""
import json

from run_09 import DATES, ENDPOINT, HERE, HOME, fingerprint, filename, read_bars

REPLAY = HERE / "results_09.json"
OUTPUT = HERE / "alpaca_coverage_09.json"


def main():
    replay = json.loads(REPLAY.read_text())
    symbols = [s for s, x in replay["coverage"].items() if x["1Day"].get("recent_daily_liquidity_screen")]
    filepath = {s: filename(HOME, s, "1Hour") for s in symbols}
    pending = [s for s, path in filepath.items() if not path.exists()]
    if pending:
        raise SystemExit("Deeper hourly histories still pending: " + ", ".join(pending))
    coverage = {}
    for symbol, path in filepath.items():
        full, notes = read_bars(path, DATES["held"][1], "1h")
        if full.empty:
            raise ValueError(f"empty query for a steady-volume pair: {symbol}")
        notes["file"] = str(path.relative_to(HOME))
        replay_file = replay["coverage"][symbol]["1Hour"].get("file")
        if replay_file:
            replay_path = HOME / replay_file
            old, _ = read_bars(replay_path, DATES["held"][1], "1h")
            if fingerprint(replay_path) != replay["coverage"][symbol]["1Hour"]["sha256"]:
                raise ValueError(f"replay input has changed: {symbol}")
            window = full.loc[old.index[0]:old.index[-1]]
            shared = window.index.intersection(old.index)
            notes.update(
                common_replay_hours=len(shared),
                only_in_replay=len(old.index.difference(window.index)),
                only_in_deeper_pull=len(window.index.difference(old.index)),
                changed_shared_bars=int((window.loc[shared, ["o", "h", "l", "c", "v"]]
                                         != old.loc[shared, ["o", "h", "l", "c", "v"]]).any(axis=1).sum()),
            )
        coverage[symbol] = notes
    out = dict(source=ENDPOINT, end=DATES["held"][1], replay_sha256=fingerprint(REPLAY), coverage=coverage)
    OUTPUT.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
