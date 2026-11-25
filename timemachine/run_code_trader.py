"""Runs a code trader through a time machine session, with no server. Pretend money only. Each run is a new session,
counted in timemachine/SESSIONS.jsonl like any other.

python3 timemachine/run_code_trader.py hold --symbol BTC/USD --market crypto --from 2026-10-01 --to 2026-10-31 [--trader HOLD] [--session ID]
python3 timemachine/run_code_trader.py twin --result $TM_RUNS/<ai session>/result.json --seed 1 [--trader TWIN] [--session ID]
python3 timemachine/run_code_trader.py rule --rule timemachine.code_traders:perp_hold --args '["BTC/USD", -1.0]' --symbols BTC/USD \
    --from 2026-10-01 --to 2026-10-31 --wakes '[{"every": "minutes", "step": 60}]' [--perp --max-gross 2] [--news] [--trader RULE] [--session ID]
Prints the end value, the benchmark hold, the order count and the wall time. Prices are not printed.

rule: a fixed rule (a Python function fn(packet, look) -> answer, which sees only the packet and its lookups) run through a
weights session, or with --perp a perp session, at full speed: the same book, costs and checks an AI trader gets."""
import argparse, datetime as dt, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S, code_traders as C
from timemachine.tape import Tape


def _run_fast(session_id, fn, tape):
    """Run a code trader with deferred per-tick disk writes and lightweight packets when the trader does not read the feed."""
    s = S.Session(session_id, tape=tape)
    s.rec.defer_writes = True
    real_save = s.save
    real_finish = s.finish
    real_packet = s.packet

    def finish_and_flush():
        s.rec.flush()
        s.save = real_save
        return real_finish()

    s.finish = finish_and_flush
    pick_counts = {}
    picks_folder = s.dir / "picks" / s.tid

    def fast_idle():
        if s.sb.holding() or s.sb.has_open():
            return False
        if not s.rec.rows("starts"):
            return False
        done = {(r["pick_id"], r["n"]) for r in s.rec.rows("picks")}
        for pid, n_act in pick_counts.items():
            if any((pid, n) not in done for n in range(n_act)):
                return False
        return True

    s.idle = fast_idle
    needs_feed = getattr(fn, "needs_feed", True)
    needs_book = getattr(fn, "needs_book", True)
    while not s.done():
        if needs_feed:
            pk = real_packet()
        else:
            k = s.prog["k"]; made = s.now; nxt = s.next_time(k)
            exp = min(nxt, made + dt.timedelta(hours=s.cfg["practice_pick_max_life_hours"]))
            pk = dict(
                session=s.meta["session"], trader=s.tid, utc=S.iso(made), step=k + 1, of=s.N,
                next_wake_utc=S.iso(nxt), is_last=k + 1 == s.N, market=s.meta["market"],
                watch=s.meta["watch"], pick_id=s.pick_id(),
                pick_template=dict(trader=s.tid, made_utc=S.iso(made), expires_utc=S.iso(exp), thesis="...", actions=[], exits=[]),
            )
            if needs_book:
                pk["book"] = s.book()
            s.packet = lambda fresh=False, _pk=pk: _pk
        body = fn(pk, s.look)
        if isinstance(body, dict) and "no_pick" not in body:
            pick_counts[s.pick_id()] = len(body.get("actions", []))
        s.save = lambda: None
        try:
            r = s.submit(body)
        finally:
            s.save = real_save
            s.packet = real_packet
        if not s.done():
            real_save()
        if not r.get("ok"):
            raise RuntimeError(f"the code trader's pick was refused: {r}")
    return json.loads((s.dir / "result.json").read_text())


def run_weights_fast(session_id, fn, tape):
    """A code trader through a weights or perp session: every packet is made and saved as for an AI trader, every answer goes
    through submit(). Only the rewrite of progress.json and records/wakes.jsonl after each wake is held back to the end."""
    from timemachine import weights as W
    s = W.open_session(session_id, tape=tape); assert isinstance(s, W.WSession), "not a weights or perp session"
    real_save, real_mirror = s.save, s.mirror; s.save = lambda: None; s.mirror = lambda: None
    try:
        while not s.done():
            pk = s.packet(); r = s.submit(fn(pk, s.look))
            if not r.get("ok"):
                raise RuntimeError(f"the code trader's answer was refused: {r}")
    finally:
        s.save, s.mirror = real_save, real_mirror; s.save(); s.mirror()
    return json.loads((s.dir / "result.json").read_text())


def load_rule(spec, args):
    import importlib
    mod, name = spec.split(":"); return getattr(importlib.import_module(mod), name)(*args)


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sub = a.add_subparsers(dest="kind", required=True)
    h = sub.add_parser("hold"); h.add_argument("--symbol", required=True); h.add_argument("--market", choices=["crypto", "stocks"], required=True)
    h.add_argument("--from", dest="start", required=True); h.add_argument("--to", dest="end", required=True)
    w = sub.add_parser("twin"); w.add_argument("--result", required=True); w.add_argument("--seed", required=True)
    ru = sub.add_parser("rule"); ru.add_argument("--rule", required=True, help="module:function that returns fn(packet, look)"); ru.add_argument("--args", default="[]")
    ru.add_argument("--symbols", required=True); ru.add_argument("--from", dest="start", required=True); ru.add_argument("--to", dest="end", required=True)
    ru.add_argument("--wakes", required=True); ru.add_argument("--perp", action="store_true"); ru.add_argument("--max-gross", type=float, default=1.0)
    ru.add_argument("--news", action="store_true"); ru.add_argument("--benchmark")
    for p in (h, w, ru):
        p.add_argument("--trader"); p.add_argument("--session")
    x = a.parse_args(argv); stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    if x.kind == "rule":
        from timemachine import weights as W, perp as P
        tape = Tape(); fn = load_rule(x.rule, json.loads(x.args)); tid = x.trader or "RULE"; syms = [y.strip() for y in x.symbols.split(",") if y.strip()]
        sid = x.session or f"{tid}-{'P' if x.perp else 'W'}-{x.start}-{stamp}"; kind, rules = W.wake_choice(x.wakes, "crypto")
        label = f"{x.rule}({','.join(map(str, json.loads(x.args)))})"
        if x.perp:
            P.create(sid, tid, "none (code trader)", label, x.start, x.end, syms, max_gross=x.max_gross, rules=rules, wake_kind=kind, news=x.news, tape=tape, benchmark=x.benchmark)
        else:
            W.create(sid, tid, "none (code trader)", label, x.start, x.end, syms, market="crypto", rules=rules, wake_kind=kind, news=x.news, tape=tape, benchmark=x.benchmark,
                     max_gross=x.max_gross if x.max_gross > 1 else None)
        t = time.time(); r = run_weights_fast(sid, fn, tape); wall = time.time() - t; f = r["final"]
        print(json.dumps(dict(session=sid, result=str(S.runs_dir() / sid / "result.json"), value_usd=f["value_usd"], gain_pct=f["gain_pct"], costs_paid_usd=f["costs_paid_usd"],
                              funding_usd=f.get("funding_usd"), closeouts=len(f.get("closeouts") or []), exits_hit=len(f.get("exits_hit") or []), wakes=len(r["steps"]),
                              wall_seconds=round(wall, 1)), indent=1))
        return
    if x.kind == "hold":
        tape = Tape()
        tid = x.trader or "HOLD"; sid = x.session or f"{tid}-{x.symbol.replace('/', '')}-{x.start}-{stamp}"; fn = C.hold(x.symbol)
        S.create(sid, tid, "none (code trader)", f"timemachine/code_traders.py#hold({x.symbol})", x.start, x.end, market=x.market, benchmark=x.symbol,
                 watch=[x.symbol], tape=tape)
    else:
        res = json.loads(Path(x.result).read_text()); m = res["session"]; tid = x.trader or "TWIN"
        tape = Tape(m.get("tape"))
        sid = x.session or f"{tid}-{m['session']}-s{x.seed}-{stamp}"[:80]; fn = C.random_twin(res, x.seed, tape=tape)
        S.create(sid, tid, "none (code trader)", f"timemachine/code_traders.py#random_twin({m['session']},{x.seed})", m["window"]["start"], m["window"]["end"],
                 wakes=m["wakes"], market=m["market"], watch=m["watch"], benchmark=m["benchmark"], tape=tape)
    t = time.time(); r = _run_fast(sid, fn, tape); wall = time.time() - t; tr = r["summary"]["traders"][0]
    print(json.dumps(dict(session=sid, result=str(S.runs_dir() / sid / "result.json"), start_usd=tr["start_usd"], value_usd=tr["value_usd"], gain_pct=tr["gain_pct"],
                          hold_gain_pct=tr["hold_gain_pct"], orders=r["summary"]["totals"]["orders"], status=r["summary"]["status"], wakes=len(m["wakes"]) if x.kind == "twin" else len(r["steps"]),
                          ticks_run=r["run_facts"]["ticks_run"], ticks_skipped=r["run_facts"]["ticks_skipped"], wall_seconds=round(wall, 1)), indent=1))


if __name__ == "__main__":
    main()
