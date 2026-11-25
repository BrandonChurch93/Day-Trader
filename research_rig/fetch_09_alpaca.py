"""Pull the published Alpaca US USD pair list, without an account or key."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import date, timedelta
import gzip
import json
from pathlib import Path
from statistics import median
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rig2 import th

HOME = Path.home() / "workspace/rig/data/alpaca_crypto"
ENDPOINT = "https://data.alpaca.markets/v1beta3/crypto/us/bars"
INVENTORY = "https://alpaca.markets/support/what-cryptocurrencies-does-alpaca-currently-support"
# Every USD column marked X on the provider's published list, including stablecoins.
PAIRS = tuple(x + "/USD" for x in (
    "AAVE ADA ARB AVAX BAT BCH BONK BTC CRV DOGE DOT ETH FIL GRT HYPE LDO LINK LTC "
    "ONDO PAXG PEPE POL RENDER SHIB SKY SOL SUSHI TRUMP UNI USDC USDG USDT WIF XRP XTZ YFI"
).split())
FIELDS = ("t", "o", "h", "l", "c", "v", "n")
LOCK = threading.Lock()
LAST = 0.0


def filename(folder, symbol, frame):
    return folder / f"{symbol.replace('/', '-')}_{frame}.csv.gz"


def fetch(query):
    global LAST
    url = ENDPOINT + "?" + urlencode(query)
    for attempt in range(8):
        with LOCK:
            time.sleep(max(0, 0.36 - (time.monotonic() - LAST)))
            LAST = time.monotonic()
        try:
            with urlopen(Request(url, headers={"Accept-Encoding": "gzip"}), timeout=30) as response:
                raw = response.read()
                return json.loads(gzip.decompress(raw) if response.headers.get("Content-Encoding") == "gzip" else raw)
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504):
                raise
            delay = exc.headers.get("Retry-After", "")
            time.sleep(max(2 ** attempt, float(delay) if delay.isdecimal() else 0))
        except (TimeoutError, URLError):
            time.sleep(2 ** attempt)
    raise RuntimeError(f"too many retries for {query.get('symbols')}")


def pull(folder, pair, frame, start, end):
    path = filename(folder, pair, frame)
    if path.exists():
        return
    part = path.with_suffix(".part")
    params = dict(symbols=pair, timeframe=frame, start=start,
                  end=end + "T23:59:59Z", limit=10000, sort="asc")
    pages, rows, seen = 0, 0, set()
    with gzip.open(part, "wt", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        while True:
            data = fetch(params)
            pages += 1
            bars = (data.get("bars") or {}).get(pair, [])
            writer.writerows(bars)
            rows += len(bars)
            token = data.get("next_page_token")
            if not token:
                break
            if token in seen:
                raise RuntimeError(f"repeated Alpaca cursor for {pair} {frame}")
            seen.add(token)
            params["page_token"] = token
            if pages % 100 == 0:
                print(pair, frame, "in progress:", rows, "rows on", pages, "pages", flush=True)
    part.replace(path)
    print(pair, frame, rows, pages, flush=True)


def recent_steady(folder, pair, end):
    screen = th("replay_09_liquidity")
    horizon = screen["days"]
    cutoff = date.fromisoformat(end)
    dates = [str(cutoff - timedelta(days=i)) for i in reversed(range(horizon))]
    with gzip.open(filename(folder, pair, "1Day"), "rt", newline="") as source:
        recent = list(csv.DictReader(source))[-horizon:]
    return ([r["t"][:10] for r in recent] == dates
            and median(float(r["c"]) * float(r["v"]) for r in recent) >= screen["min_median_usd"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--basket-only", action="store_true")
    parser.add_argument("--prioritize-replay-window", action="store_true")
    parser.add_argument("--steady-only", action="store_true",
                        help="pull every daily history, then full hours for pairs passing the recent liquidity screen")
    args = parser.parse_args()
    mode = "dev" if args.dev else "held"
    dates = th("replay_09_dates")
    end = dates[mode][1]
    folder = HOME / "dev" if args.dev else HOME
    folder.mkdir(parents=True, exist_ok=True)
    basket = th("replay_09_basket")
    symbols = basket if args.basket_only else (*basket, *(p for p in PAIRS if p not in basket))
    with ThreadPoolExecutor(max_workers=8) as pool:
        if args.prioritize_replay_window:
            if args.dev:
                raise ValueError("this shared sealed download includes both date slices")
            replay = folder / "replay_window"
            replay.mkdir(exist_ok=True)
            start = str(date.fromisoformat(dates["dev"][0]) - timedelta(days=th("replay_09_liquidity")["days"] + 1))
            daily = [pool.submit(pull, folder, p, "1Day", dates["pull_start"], end) for p in symbols]
            jobs = daily + [pool.submit(pull, replay, p, "1Hour", start, end) for p in basket]
        elif args.steady_only:
            daily = [pool.submit(pull, folder, p, "1Day", dates["pull_start"], end) for p in symbols]
            for job in daily:
                job.result()
            steady = [p for p in symbols if recent_steady(folder, p, end)]
            print("Recent liquidity screen:", ", ".join(steady), flush=True)
            jobs = [pool.submit(pull, folder, p, "1Hour", dates["pull_start"], end) for p in steady]
        else:
            jobs = [pool.submit(pull, folder, pair, frame, dates["pull_start"], end)
                    for frame in ("1Day", "1Hour") for pair in symbols]
        for job in jobs:
            job.result()


if __name__ == "__main__":
    main()
