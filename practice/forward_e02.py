"""E02 forward watch: plan the pinned dates or manually record one completed IWM event."""
import argparse
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
LOG = HERE / "forward" / "E02_log.json"
OFF_REPO = Path("/home/user/workspace/rig/data/forward_e02")
CARD = "practice/traders/E02_iwm_pre_holiday.md"
NY, UTC = ZoneInfo("America/New_York"), timezone.utc
COST_BPS = 2.0
# Official NYSE closure: (entry session, exit session, exit hour ET, next open session).
SESSIONS = {
    "2026-12-25": ("2026-12-23", "2026-12-24", 13, "2026-12-28"),
    "2027-01-01": ("2026-12-30", "2026-12-31", 16, "2027-01-04"),
    "2027-01-18": ("2027-01-14", "2027-01-15", 16, "2027-01-19"),
    "2027-02-15": ("2027-02-11", "2027-02-12", 16, "2027-02-16"),
    "2027-03-26": ("2027-03-24", "2027-03-25", 16, "2027-03-29"),
    "2027-05-31": ("2027-05-27", "2027-05-28", 16, "2027-06-01"),
    "2027-06-18": ("2027-06-16", "2027-06-17", 16, "2027-06-21"),
    "2027-07-05": ("2027-07-01", "2027-07-02", 16, "2027-07-06"),
    "2027-09-06": ("2027-09-02", "2027-09-03", 16, "2027-09-07"),
    "2027-11-25": ("2027-11-23", "2027-11-24", 16, "2027-11-26"),
    "2027-12-24": ("2027-12-22", "2027-12-23", 16, "2027-12-27"),
}


class Refuse(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refuse(why)


def clock(day, hour):
    return datetime.combine(date.fromisoformat(day), time(hour), NY)


def encode(obj):
    return (json.dumps(obj, indent=1, sort_keys=True, allow_nan=False) + "\n").encode()


def record(holiday, packet, now=None):
    need(holiday in SESSIONS, "holiday not in the pinned table")
    entry, exit_, hour, next_session = SESSIONS[holiday]
    now = now or datetime.now(UTC)
    need(now >= clock(exit_, hour) + timedelta(minutes=20), "wait at least 20 minutes after the exit close")
    need(type(packet) is dict and set(packet) == {"symbol", "feed", "adjustment", "entry_session",
                                                  "exit_session", "entry_close", "exit_close",
                                                  "exit_ex_date_cash_per_share"}, "invalid packet fields")
    need((packet["symbol"], packet["feed"], packet["adjustment"], packet["entry_session"],
          packet["exit_session"]) == ("IWM", "sip", "raw", entry, exit_), "packet does not match pinned IWM sessions")
    buy, sell, cash = (packet[k] for k in ("entry_close", "exit_close", "exit_ex_date_cash_per_share"))
    need(all(type(x) in (float, int) and isfinite(x) for x in (buy, sell, cash))
         and min(buy, sell) > 0 and cash >= 0, "invalid close or payout")
    f = COST_BPS / 10_000
    net = (sell * (1 - f) + cash) / (buy * (1 + f)) - 1
    made = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    counted = now < clock(next_session, 0)
    blob = encode(packet | {"holiday": holiday, "made_utc": made, "counted": counted,
                            "cost_bps_per_side": COST_BPS, "net_return": net})
    line = {"holiday": holiday, "made_utc": made, "counted": counted, "entry_session": entry,
            "exit_session": exit_, "net_return_pct": round(net * 100, 4),
            "distribution_per_share": round(cash, 6), "distribution_ex_dates": [exit_] if cash else [],
            "record_sha256": sha256(blob).hexdigest()}
    return blob, line


def save(holiday, blob, line, log=LOG, off=OFF_REPO):
    cur = json.loads(log.read_text()) if log.exists() else {"card": CARD, "events": {}}
    need(cur["card"] == CARD and holiday not in cur["events"], "event already in the log or wrong card")
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    need(off.resolve() == off and off.stat().st_mode & 0o077 == 0, "record directory must be private")
    with os.fdopen(os.open(off / f"{holiday}.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as out:
        out.write(blob)
    cur["events"][holiday] = line
    log.parent.mkdir(exist_ok=True)
    log.write_bytes(encode(cur))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    modes = cli.add_subparsers(dest="command", required=True)
    modes.add_parser("plan")
    run = modes.add_parser("record")
    run.add_argument("holiday")
    run.add_argument("packet", type=Path)
    args = cli.parse_args()
    if args.command == "plan":
        for h, (entry, exit_, hour, _) in SESSIONS.items():
            print(f"{h}: buy at {entry} close; sell at {exit_} {hour:02d}:00 ET")
        return 0
    try:
        path = args.packet.resolve(strict=True)
        need(path.is_file() and not path.is_relative_to(HERE.parent) and path.stat().st_mode & 0o077 == 0
             and path.stat().st_size <= 16_384, "input packet must be a small private file outside the repo")
        blob, line = record(args.holiday, json.loads(path.read_bytes()))
        save(args.holiday, blob, line)
    except Refuse as e:
        cli.exit(2, f"Refused: {e}\n")
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError):
        cli.exit(2, "Refused: unreadable packet, existing private record, or record write failed\n")
    print(encode(line).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
