"""Makes a new time machine session and counts it in timemachine/SESSIONS.jsonl. Pretend money only.

python3 timemachine/new_session.py --trader A07 --model <model build> --method practice/traders/A07_crypto_trend.md \
    --market crypto --from 2026-10-01 --to 2026-10-31 [--session ID] [--watch BTC/USD,ETH/USD] [--benchmark BTC/USD] [--wakes T1,T2,...]
Prints the session id and the curl lines a trader agent uses."""
import argparse, datetime as dt, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--trader", required=True); a.add_argument("--model", required=True); a.add_argument("--method", required=True)
    a.add_argument("--market", choices=["crypto", "stocks"], required=True)
    a.add_argument("--from", dest="start", required=True); a.add_argument("--to", dest="end", required=True)
    a.add_argument("--session"); a.add_argument("--watch"); a.add_argument("--benchmark"); a.add_argument("--wakes"); a.add_argument("--note")
    x = a.parse_args(argv)
    sid = x.session or f"{x.trader}-{x.start}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    folder = S.create(sid, x.trader, x.model, x.method, x.start, x.end, wakes=x.wakes.split(",") if x.wakes else None, market=x.market,
                      watch=[s for s in x.watch.split(",") if s] if x.watch is not None else None, benchmark=x.benchmark, note=x.note)
    meta = json.loads((folder / "session.json").read_text()); port = os.environ.get("TM_PORT", "8765"); base = f"http://127.0.0.1:{port}"
    print(json.dumps(dict(session=sid, folder=str(folder), wakes=len(meta["wakes"]), first_wake=meta["wakes"][0], end_utc=meta["end_utc"]), indent=1))
    print(f"curl -s '{base}/next?session={sid}'")
    print(f"curl -s -X POST '{base}/pick?session={sid}' -H 'Content-Type: application/json' -d @pick.json")
    print(f"curl -s '{base}/status?session={sid}'")


if __name__ == "__main__":
    main()
