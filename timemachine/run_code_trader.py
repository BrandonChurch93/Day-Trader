"""Runs a code trader through a time machine session, with no server. Pretend money only. Each run is a new session,
counted in timemachine/SESSIONS.jsonl like any other.

python3 timemachine/run_code_trader.py hold --symbol BTC/USD --market crypto --from 2026-10-01 --to 2026-10-31 [--trader HOLD] [--session ID]
python3 timemachine/run_code_trader.py twin --result $TM_RUNS/<ai session>/result.json --seed 1 [--trader TWIN] [--session ID]
Prints the end value, the benchmark hold, the order count and the wall time. Prices are not printed."""
import argparse, datetime as dt, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S, code_traders as C


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = a.add_subparsers(dest="kind", required=True)
    h = sub.add_parser("hold"); h.add_argument("--symbol", required=True); h.add_argument("--market", choices=["crypto", "stocks"], required=True)
    h.add_argument("--from", dest="start", required=True); h.add_argument("--to", dest="end", required=True)
    w = sub.add_parser("twin"); w.add_argument("--result", required=True); w.add_argument("--seed", required=True)
    for p in (h, w):
        p.add_argument("--trader"); p.add_argument("--session")
    x = a.parse_args(argv); stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    if x.kind == "hold":
        tid = x.trader or "HOLD"; sid = x.session or f"{tid}-{x.symbol.replace('/', '')}-{x.start}-{stamp}"; fn = C.hold(x.symbol)
        S.create(sid, tid, "none (code trader)", f"timemachine/code_traders.py#hold({x.symbol})", x.start, x.end, market=x.market, benchmark=x.symbol,
                 watch=[x.symbol])
    else:
        res = json.loads(Path(x.result).read_text()); m = res["session"]; tid = x.trader or "TWIN"
        sid = x.session or f"{tid}-{m['session']}-s{x.seed}-{stamp}"[:80]; fn = C.random_twin(res, x.seed)
        S.create(sid, tid, "none (code trader)", f"timemachine/code_traders.py#random_twin({m['session']},{x.seed})", m["window"]["start"], m["window"]["end"],
                 wakes=m["wakes"], market=m["market"], watch=m["watch"], benchmark=m["benchmark"])
    t = time.time(); r = S.run_code_trader(sid, fn); wall = time.time() - t; tr = r["summary"]["traders"][0]
    print(json.dumps(dict(session=sid, result=str(S.runs_dir() / sid / "result.json"), start_usd=tr["start_usd"], value_usd=tr["value_usd"], gain_pct=tr["gain_pct"],
                          hold_gain_pct=tr["hold_gain_pct"], orders=r["summary"]["totals"]["orders"], status=r["summary"]["status"], wakes=len(m["wakes"]) if x.kind == "twin" else len(r["steps"]),
                          ticks_run=r["run_facts"]["ticks_run"], ticks_skipped=r["run_facts"]["ticks_skipped"], wall_seconds=round(wall, 1)), indent=1))


if __name__ == "__main__":
    main()
