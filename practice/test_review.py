"""Offline regression checks for order recovery, sleeve budgets and exit safety."""
import contextlib
import datetime as dt
import io
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

_base_output = io.StringIO()
try:
    with contextlib.redirect_stdout(_base_output):
        from test_trader import AI, B, Fake, RULES, T, cfg, crypto_bars, down, go, now, stock_bars, t2, up
except SystemExit:
    print(_base_output.getvalue(), end="")
    raise

import books
import market
import picks

ROOT = Path(__file__).resolve().parent.parent
RESULTS = []


def check(name, func):
    try:
        result = func()
        if not result:
            print(f"FAIL: {name}")
    except Exception as exc:
        result = False
        print(f"FAIL: {name} ({type(exc).__name__}: {exc})")
    RESULTS.append(bool(result))


def fake(mode="fill", opened=True, when=now):
    f = Fake(mode=mode, is_open=opened)
    f.now = when
    f.px = {"AAA": 10, "BBB": 10, "BTC/USD": 101, "VTI": 10}
    f.crypto = crypto_bars(up, when)
    f.stock = stock_bars(list(range(1, 11)), when, 10)
    return f


def run(f, records, when=now, traders=RULES[:1], pick_root=None, clear=None, config=cfg):
    return go(f, records, when, cfg=config, traders=traders, picks_dir=pick_root, clear=clear)


def buy(symbol, dollars=100):
    return dict(symbol=symbol, side="buy", usd=dollars, reason="test")


def sell(symbol):
    return dict(symbol=symbol, side="sell", share=1, reason="test")


def pick(root, pid, actions=(), exits=(), tid="A01", made=now, exp=None):
    folder = root / "picks" / tid
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (pid + ".json")
    path.write_text(json.dumps(dict(trader=tid, made_utc=T.iso(made), expires_utc=T.iso(exp or made + dt.timedelta(hours=1)), thesis="test", actions=list(actions), exits=list(exits))))
    return path


def sleeve(summary, tid):
    return next(row for row in summary["traders"] if row["id"] == tid)


def journal(folder, event="sending"):
    cid = books.cid_for("P1-BTC", "20261124T0000")
    T.Records(folder).add("orders", dict(utc=T.iso(now), event=event, trader="P1-BTC", symbol="BTC/USD", cid=cid, side="buy", qty=None, usd=997.50, assumed_price=101, reason="test"))
    return cid


def missing_intent_and_lost_state():
    f = fake()
    journal(RECORDS)
    code, _, _ = run(f, RECORDS)
    (RECORDS / "state.json").unlink()
    _, s, _ = run(f, RECORDS, t2)
    return code == 1 and f.submits == 0 and sleeve(s, "P1-BTC")["halted"]


def recovered_unfilled_order():
    f = fake("stay_open")
    cid = journal(RECORDS, "sent")
    f.make("BTC/USD", "buy", cid, notional=997.50, status="accepted")
    f.crypto = crypto_bars(up, t2)
    _, s, _ = run(f, RECORDS, t2)
    return f.submits == 0 and s["orders"][0]["status"] == "open"


def broker_books_without_any_state():
    f = fake()
    run(f, RECORDS)
    shutil.rmtree(RECORDS)
    f.crypto = crypto_bars(up, t2)
    _, s, _ = run(f, RECORDS, t2)
    return f.submits == 1 and len(sleeve(s, "P1-BTC")["positions"]) == 1


def recovered_sell_side_and_idempotent_close():
    f = fake()
    journal(RECORDS)
    f.make("BTC/USD", "buy", books.cid_for("P1-BTC", "older"), qty=5)
    f.now = now + dt.timedelta(minutes=1)
    o = f.make("BTC/USD", "sell", books.cid_for("P1-BTC", "20261124T0000"), qty=5)
    f.crypto = crypto_bars(down, t2)
    _, _, r1 = run(f, RECORDS, t2)
    _, s2, r2 = run(f, RECORDS, t2)
    found = next(order for order in s2["orders"] if order["order_id"] == o["id"])
    return f.submits == 0 and found["side"] == "sell" and len(r1.books["P1-BTC"]["closed"]) == len(r2.books["P1-BTC"]["closed"]) == 1


def no_fill_never_retries_after_clear():
    f = fake()
    cid = journal(RECORDS)
    by_cid = f.order_by_cid
    with patch.object(f, "order_by_cid", wraps=by_cid) as lookup:
        _, _, _ = run(f, RECORDS, clear="P1-BTC")
        return f.submits == 0 and lookup.call_args_list and lookup.call_args_list[-1].args == (cid,)


def matching_partial(status):
    f = fake()
    f.make("AAA", "buy", "pt1.a01.sample", qty=10, frac=.5, status=status)
    _, s, r = run(f, RECORDS, traders=AI)
    expected = "open" if status == "partially_filled" else "part filled"
    return r.books["A01"]["cash"] == 950 and r.books["A01"]["pos"]["AAA"] == 5 and s["orders"][0]["status"] == expected


def invalid_fill_halts(status):
    f = fake()
    f.make("AAA", "buy", "pt1.a01.sample", qty=10, frac=.5, status=status)
    f.list[0]["filled_avg_price"] = None
    code, s, _ = run(f, RECORDS, traders=AI)
    return code == 1 and sleeve(s, "A01")["halted"] and s["orders"][0]["status"] == "unclear"


def replacement_successor():
    f = fake()
    old = f.make("AAA", "buy", "pt1.a01.sample", qty=10, status="accepted")
    f.now = now + dt.timedelta(minutes=1)
    new = f.make("AAA", "buy", "broker-assigned", qty=10)
    f.list[0].update(status="replaced", replaced_by=new["id"])
    f.list[1]["replaces"] = old["id"]
    _, _, r = run(f, RECORDS, t2, traders=AI)
    return len(r.books["A01"]["open"]) == 0 and r.books["A01"]["pos"]["AAA"] == 10 and r.books["A01"]["cash"] == 900


def buy_fills_higher_without_negative_cash():
    f = fake()
    submit = f.submit
    def move(*args, **kwargs):
        f.px["BTC/USD"] = 102
        return submit(*args, **kwargs)
    f.submit = move
    _, _, r = run(f, RECORDS)
    return f.submits == 1 and r.books["P1-BTC"]["cash"] >= 0


def broken_bars(kind):
    f = fake()
    if kind == "future":
        f.crypto.append(dict(t=T.iso(now + dt.timedelta(days=1)), c=.1))
    elif kind == "gap":
        del f.crypto[100]
    else:
        f.sessions = [dict(date=x["t"][:10]) for x in f.stock] + [dict(date="2026-10-30")]
    trader = RULES[1:] if kind == "bad month end" else RULES[:1]
    run(f, RECORDS, traders=trader)
    return f.submits == 0


def concurrent_orders_same_sleeve():
    f = fake()
    pick(PICKS, "20261125T1500Z", [buy("AAA", 800), buy("BBB", 800)])
    _, _, r = run(f, RECORDS, traders=AI, pick_root=PICKS)
    return sum(float(o["notional"]) for o in f.list) <= 1000 and r.books["A01"]["cash"] >= 0


def pending_buys_reserve_cash_across_runs():
    f = fake("stay_open")
    pick(PICKS, "20261125T1500Z", [buy("AAA", 800)])
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    pick(PICKS, "20261125T1510Z", [buy("BBB", 800)])
    run(f, RECORDS, now + dt.timedelta(minutes=10), traders=AI, pick_root=PICKS)
    return sum(float(o["notional"]) for o in f.list) <= 1000


def holds(f, both=False):
    f.make("AAA", "buy", "pt1.a01.20261125t1500z.0", qty=10)
    if both:
        f.make("AAA", "buy", "pt1.a02.20261125t1500z.0", qty=10)


def shared_symbol_sales(use_exit):
    f = fake()
    holds(f, both=True)
    if use_exit:
        pick(PICKS, "20261125T1500Z", exits=[dict(symbol="AAA", stop=11)])
    else:
        pick(PICKS, "20261125T1505Z", [sell("AAA")])
    pick(PICKS, "20261125T1510Z", [sell("AAA")])
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 1 and f.held.get("AAA") == 10


def open_symbol_not_reconciled():
    f = fake()
    holds(f)
    f.held["AAA"] = 20
    f.make("AAA", "buy", "pt1.a01.pending", qty=1, status="accepted")
    pick(PICKS, "20261125T1510Z", [buy("AAA")], tid="A02")
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 0


def no_refused_cash_loss():
    f = fake("reject")
    pick(PICKS, "20261125T1510Z", [buy("AAA", 800)])
    _, s, _ = run(f, RECORDS, traders=AI, pick_root=PICKS)
    return not f.list and sleeve(s, "A01")["value_usd"] == 1000 and sleeve(s, "A01")["cash_usd"] == 1000


def pick_expiry_while_saving():
    f = fake()
    pick(PICKS, "20261125T1510Z", [buy("AAA")], exp=now + dt.timedelta(seconds=1))
    elapsed = [0.0]
    f.checkpoint = lambda: elapsed.__setitem__(0, 2.0)
    with patch.object(T.time, "monotonic", side_effect=lambda: elapsed[0]):
        run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 0


def quote_expiry_while_saving():
    f = fake()
    f.quote_age_min = cfg["practice_max_quote_age_minutes"] - 1
    pick(PICKS, "20261125T1510Z", [buy("AAA")])
    elapsed = [0.0]
    f.checkpoint = lambda: elapsed.__setitem__(0, 120.0)
    with patch.object(T.time, "monotonic", side_effect=lambda: elapsed[0]):
        run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 0


def stale_pick_cannot_move_stop():
    f = fake()
    holds(f)
    pick(PICKS, "20261125T1500Z", exits=[dict(symbol="AAA", stop=11)])
    pick(PICKS, "20261125T1510Z", exits=[dict(symbol="AAA", stop=5)], made=now-dt.timedelta(minutes=30), exp=now-dt.timedelta(minutes=1))
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 1 and "AAA" not in f.held


def edit_pick_does_not_duplicate():
    f = fake()
    pick(PICKS, "20261125T1510Z", [buy("AAA")])
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    pick(PICKS, "20261125T1510Z", [buy("BBB"), buy("AAA")])
    run(f, RECORDS, now + dt.timedelta(minutes=10), traders=AI, pick_root=PICKS)
    return sum(o["symbol"] == "AAA" for o in f.list) == 1


def deleting_pick_does_not_remove_protection():
    f = fake()
    p = pick(PICKS, "20261125T1510Z", [buy("AAA")], [dict(symbol="AAA", stop=9)])
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    p.unlink()
    f.px["AAA"] = 8
    run(f, RECORDS, now + dt.timedelta(minutes=10), traders=AI, pick_root=PICKS)
    return f.submits == 2 and "AAA" not in f.held


def partial_exit_stays_triggered():
    f = fake("part_cancel")
    holds(f)
    pick(PICKS, "20261125T1500Z", exits=[dict(symbol="AAA", stop=11)])
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    f.mode, f.px["AAA"] = "fill", 12
    run(f, RECORDS, now + dt.timedelta(minutes=10), traders=AI, pick_root=PICKS)
    return f.submits == 2 and "AAA" not in f.held


def invalid_pick_is_isolated():
    f = fake()
    pick(PICKS, "20261125T1510Z", [buy(["AAA"])])
    pick(PICKS, "20261125T1510Z", [buy("BBB")], tid="A02")
    _, s, _ = run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 1 and f.list[0]["symbol"] == "BBB" and any("does not fit" in row["text"] for row in s["problems"])


def missing_mark_keeps_value():
    f = fake()
    holds(f)
    _, s1, _ = run(f, RECORDS, traders=AI)
    del f.px["AAA"]
    _, s2, _ = run(f, RECORDS, now + dt.timedelta(hours=1), traders=AI)
    return sleeve(s1, "A01")["value_usd"] == sleeve(s2, "A01")["value_usd"] == 1000


def same_pick_id_in_two_sleeves():
    f = fake()
    f.make("AAA", "buy", "pt1.a02.20261125t1500z.0", qty=10)
    pick(PICKS, "20261125T1500Z", tid="A01", made=now-dt.timedelta(hours=1), exp=now-dt.timedelta(minutes=1))
    pick(PICKS, "20261125T1500Z", exits=[dict(symbol="AAA", stop=11)], tid="A02")
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 1 and "AAA" not in f.held


def refusals_only_stop_their_own_sleeve():
    f = fake()
    f.make("AAA", "buy", "pt1.a02.20261125t1500z.0", qty=10)
    pick(PICKS, "20261125T1500Z", exits=[dict(symbol="AAA", stop=11)], tid="A02")
    for i in range(3):
        T.Records(RECORDS).add("orders", dict(utc=T.iso(now), event="rejected", trader="A01", symbol="AAA", cid=f"pt1.a01.x.20261125t1500z.aaa.0.{i}", side="sell", qty=10, usd=None, assumed_price=10, reason="test"))
    _, s, _ = run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 1 and not sleeve(s, "A02")["halted"]


def later_pick_cannot_reset_started_exit():
    f = fake("part_cancel")
    holds(f)
    pick(PICKS, "20261125T1500Z", exits=[dict(symbol="AAA", stop=11)])
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    f.mode, f.px["AAA"] = "fill", 12
    pick(PICKS, "20261125T1520Z", exits=[dict(symbol="AAA", stop=8)])
    run(f, RECORDS, now + dt.timedelta(minutes=10), traders=AI, pick_root=PICKS)
    return f.submits == 2 and "AAA" not in f.held


def fills_are_sorted_by_utc_instant():
    f = fake()
    f.make("AAA", "buy", "pt1.a01.first", qty=10)
    f.make("AAA", "sell", "pt1.a01.last", qty=10)
    f.list[0]["filled_at"] = "2026-11-25T14:59:00Z"
    f.list[1]["filled_at"] = "2026-11-25T10:00:00-05:00"
    b, _ = books.derive(f.list, ["A01"], 1000, 0)
    return len(b["A01"]["closed"]) == 1 and not b["A01"]["bad"] and not b["A01"]["pos"]


def tiny_partial_stays_in_the_ledger():
    f = fake()
    holds(f)
    f.make("AAA", "sell", "pt1.a01.part", qty=10, frac=.99995, status="canceled")
    code, s, r = run(f, RECORDS, traders=AI)
    b = r.books["A01"]
    if not (code == 0 and len(b["closed"]) == 1 and "AAA" not in b["pos"] and not s["symbols_stopped"]
            and math.isclose(b["dust"].get("AAA", 0), f.held["AAA"], abs_tol=1e-9)):
        return False
    later = now + dt.timedelta(minutes=1)
    f.now = later
    f.make("AAA", "buy", "pt1.a01.next", qty=1)
    code, s, r = run(f, RECORDS, later, traders=AI)
    b = r.books["A01"]
    return (code == 0 and len(b["closed"]) == 1 and "AAA" not in b["dust"] and not s["symbols_stopped"]
            and math.isclose(b["pos"].get("AAA", 0), f.held["AAA"], abs_tol=1e-9))


def position_availability_caps_sale():
    f = fake()
    holds(f)
    f.positions = lambda: {k: dict(qty=q, available=0) for k, q in f.held.items()}
    pick(PICKS, "20261125T1510Z", [sell("AAA")])
    run(f, RECORDS, traders=AI, pick_root=PICKS)
    return f.submits == 0


def stock_market_closes_during_checkpoint():
    f = fake()
    pick(PICKS, "20261125T1510Z", [buy("AAA")])
    def checkpoint():
        f.is_open = False
    T.Run(f, f, T.Records(RECORDS), cfg, AI, picks_dir=PICKS, now=now, sleep=lambda _: None, checkpoint=checkpoint).run()
    return f.submits == 0


def old_pick_does_not_request_unrelated_prices():
    f = fake()
    prior = now - dt.timedelta(hours=2)
    pick(PICKS, "20261125T1300Z", [buy("BBB")], made=prior, exp=prior+dt.timedelta(hours=1))
    prices = f.prices
    def read(symbols):
        if "BBB" in symbols:
            raise B.Refused(422, "pretend outdated symbol data failure")
        return prices(symbols)
    f.prices = read
    r = T.Run(f, f, T.Records(RECORDS), cfg, RULES[:1] + AI, picks_dir=PICKS, now=now, sleep=lambda _: None, checkpoint=f.checkpoint)
    r.run()
    return f.submits == 1 and f.list[-1]["symbol"] == "BTC/USD"


def git(cwd, *args, must=True):
    return subprocess.run(["git", "-C", str(cwd), *args], check=must, capture_output=True, text=True)


def real_checkpoint(failure=None):
    bare = PATH / "bare"
    bare.mkdir()
    git(bare, "init", "--bare")
    work = PATH / "work"
    work.mkdir()
    git(work, "init")
    git(work, "config", "user.name", "Review test")
    git(work, "config", "user.email", "review@example.invalid")
    rec = work / "records"
    rec.mkdir()
    (rec / "placeholder").write_text("test\n")
    if failure == "ignored":
        (work / ".gitignore").write_text("records/orders.jsonl\n")
    git(work, "add", "-A")
    git(work, "commit", "-m", "Initialize")
    git(work, "remote", "add", "origin", str(bare))
    git(work, "push", "origin", "HEAD:practice-records")
    if failure == "lock":
        (work / ".git" / "index.lock").write_text("Cannot stage the order\n")
    f = fake()
    before_submit = []
    submit = f.submit
    def verify(*args, **kwargs):
        remote = git(bare, "show", "practice-records:records/orders.jsonl", must=False)
        before_submit.append(remote.returncode == 0 and json.loads(remote.stdout.splitlines()[-1])["event"] == "sending")
        return submit(*args, **kwargs)
    f.submit = verify
    r = T.Run(f, f, T.Records(rec), cfg, RULES[:1], now=now, sleep=lambda _: None, checkpoint=T.git_checkpoint(rec))
    r.run()
    return f.submits == 0 if failure else before_submit == [True]


def order_cursor_completes_or_fails_closed():
    rows = [dict(id=str(i), submitted_at="2026-11-25T15:17:00.123Z") for i in range(500)]
    later = dict(id="500", submitted_at="2026-11-25T15:17:01.000Z")
    b = B.Broker(key_id="dummy", secret="dummy")
    b._call = lambda method, base, path, params, **kw: [later] if params.get("after_order_id") == "499" else rows
    try:
        return len(b.orders()) == 501
    except B.Unclear:
        return True


def quote_cannot_borrow_trade_time():
    raw = dict(latestQuote=dict(bp=9, ap=9.01), latestTrade=dict(p=10, t=T.iso(now)))
    row = market._parse_snapshot(raw, "test", .02)
    return row is None or row["price"] == 10


def in_tmp(func):
    def wrapper():
        global PATH, RECORDS, PICKS
        with tempfile.TemporaryDirectory() as directory:
            PATH = Path(directory)
            RECORDS, PICKS = PATH / "records", PATH / "picks_branch"
            return func()
    return wrapper


check("A missing broker order remains stopped after the state cache is lost", in_tmp(missing_intent_and_lost_state))
check("A previously sent open order cannot be sent again under a new price day", in_tmp(recovered_unfilled_order))
check("A complete broker order restores the holding without re-sending it", in_tmp(broker_books_without_any_state))
check("An earlier sell is booked as a sell and one closure is counted on repeated runs", in_tmp(recovered_sell_side_and_idempotent_close))
check("Manual clear performs the lookup and does not recycle the old order id", in_tmp(no_fill_never_retries_after_clear))
for status in ("partially_filled", "canceled", "expired"):
    check(f"An order marked {status} counts only its filled quantity", in_tmp(lambda: matching_partial(status)))
for status in ("filled", "canceled", "expired"):
    check(f"An order marked {status} with fill size but no price stops its trader", in_tmp(lambda: invalid_fill_halts(status)))
check("A completed replacement is credited to the original trader and no longer blocks the symbol", in_tmp(replacement_successor))
check("A higher buy fill price does not create negative cash", in_tmp(buy_fills_higher_without_negative_cash))
for kind in ("future", "gap", "bad month end"):
    check(f"The fixed rules refuse price history with {kind}", in_tmp(lambda: broken_bars(kind)))
check("Offsets and nanoseconds retain the correct UTC instant", lambda: picks.parse_t("2026-11-24T00:00:00.123456789-05:00") == dt.datetime(2026, 11, 24, 5, 0, 0, 123456, tzinfo=dt.timezone.utc))
check("Quantity rounding never returns more than the available quantity", lambda: T.floor_dp(math.nextafter(1e-9, 0), 9) <= math.nextafter(1e-9, 0))
check("Two buys on the same run never spend more than the sleeve has", in_tmp(concurrent_orders_same_sleeve))
check("A pending buy on an earlier run still reserves sleeve cash", in_tmp(pending_buys_reserve_cash_across_runs))
check("An exit and a pick sale cannot both sell another sleeve's shares", in_tmp(lambda: shared_symbol_sales(True)))
check("Two pick sales cannot both sell another sleeve's shares", in_tmp(lambda: shared_symbol_sales(False)))
check("An open order cannot let another sleeve trade an unreconciled holding", in_tmp(open_symbol_not_reconciled))
check("A refused buy has no effect on booked cash or account value", in_tmp(no_refused_cash_loss))
check("A pick that expires during the checkpoint is not sent", in_tmp(pick_expiry_while_saving))
check("A quote that gets too old during the checkpoint is not used", in_tmp(quote_expiry_while_saving))
check("A pick first seen after expiry cannot override an active stop", in_tmp(stale_pick_cannot_move_stop))
check("Editing a previously acted-on pick cannot send the same action twice", in_tmp(edit_pick_does_not_duplicate))
check("Removing the source pick cannot remove standing protection", in_tmp(deleting_pick_does_not_remove_protection))
check("A partially filled exit stays triggered after price recovers", in_tmp(partial_exit_stays_triggered))
check("A new pick cannot reset an exit that already partly filled", in_tmp(later_pick_cannot_reset_started_exit))
check("An expired pick cannot affect a different sleeve with the same pick id", in_tmp(same_pick_id_in_two_sleeves))
check("One sleeve's exit refusals cannot stop another sleeve's exit", in_tmp(refusals_only_stop_their_own_sleeve))
check("One malformed pick is rejected without disabling another trader", in_tmp(invalid_pick_is_isolated))
check("A missing quote cannot make a known holding suddenly worthless", in_tmp(missing_mark_keeps_value))
check("The ledger sorts fills by elapsed time even when timestamp offsets differ", fills_are_sorted_by_utc_instant)
check("A subcent remainder stays on record after closing and is folded into the next buy", in_tmp(tiny_partial_stays_in_the_ledger))
check("An unavailable broker position is not submitted for sale", in_tmp(position_availability_caps_sale))
check("A stock order is not sent if the market closes during the checkpoint", in_tmp(stock_market_closes_during_checkpoint))
check("An expired pick cannot block another trader with a needless quote request", in_tmp(old_pick_does_not_request_unrelated_prices))
check("A successful real Git push contains the intent before POST", in_tmp(real_checkpoint))
check("A failed Git add does not allow a POST", in_tmp(lambda: real_checkpoint("lock")))
check("An ignored order journal cannot let Git report a false durable checkpoint", in_tmp(lambda: real_checkpoint("ignored")))
check("A full order page with the same timestamps cannot silently truncate history", order_cursor_completes_or_fails_closed)
check("A price computed from a quote cannot borrow a trade's timestamp", quote_cannot_borrow_trade_time)
check("The broker declines to follow redirects", lambda: B._NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://example.invalid/") is None)
check("A JSON-escaped dummy credential is scrubbed from broker errors", lambda: "DUMMYKEY" not in B.clean(r'{"message":"echo \u0044UMMYKEY"}', ("DUMMYKEY",)))

print(f"{sum(RESULTS)} checks passed")
raise SystemExit(0 if all(RESULTS) else 1)
