"""All prices here are invented in memory. No custody directory or bars are opened."""

import json
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from score_75 import (
    INDEX_HEADER, NAMES, REPEAT_DAYS, Refusal, Tape, approval_id, calendar, decode_repeat, indicators,
    load_config, open_folder, period_return, play, registered_summary, run_repeat, score_repeat,
    sha, snapshot, twins, validate_bytes,
)


def toy(edge):
    # Each countdown chain breaks out, then retreats through its prior midpoint.
    # In the planted path only, the following opens allow an actual directional gain.
    levels = np.r_[100.8 - .017 * np.arange(34), [105, 108, 110, 112, 114, 116, 117, 118],
                   100.1 - .013 * np.arange(18)]
    n = len(REPEAT_DAYS)
    if edge:
        close = np.resize(levels, n)
        open_ = np.resize(np.r_[np.full(35, 100.), levels[34:-1]], n)
        # The collapse at close 42 can only be sold at open 43.
        open_[np.arange(n) % 60 == 43] = 118
    else:
        # Time-varying signals; every executable open and terminal close are at par.
        # The engine can lose costs but cannot compound directional P&L at these fills.
        close = np.resize(levels, n)
        close[-1] = 100
        open_ = np.full(n, 100.0)
    flag = np.ones((n, 1), dtype=bool)
    return Tape(REPEAT_DAYS, ("TOY",), open_[:, None], close[:, None], flag, flag.copy())


def assert_refusal(code, call, *args):
    try:
        call(*args)
    except Refusal as e:
        assert str(e) == code, str(e)
    else:
        raise AssertionError(code)


def validation():
    index = INDEX_HEADER + b"".join(f"{d},{coin},0,0,0,0\n".encode()
                                   for d in REPEAT_DAYS for coin in NAMES)
    n = len(REPEAT_DAYS) * len(NAMES)
    # Deliberately nonsense bytes (negative/nonfinite IEEE encodings included).
    # The checker authenticates bytes and geometry, not their numeric meaning.
    opaque = b"\xff" * (16 * n)
    base = {
        "schema": 1, "start": "2020-01-01", "stop_exclusive": "2024-01-01",
        "names": list(NAMES), "rows": n, "index_sha256": sha(index),
        "payload_sha256": sha(opaque), "source_receipt_sha256": "a" * 64,
        "eligibility_receipt_sha256": "b" * 64,
    }
    def pack(modified):
        raw = json.dumps(modified).encode()
        return raw, sha(raw)

    raw, pin = pack(base)
    flags = validate_bytes(raw, index, opaque, pin)
    assert flags.shape == (1461, 20, 4)
    assert_refusal("REFUSE_PRICES", decode_repeat, flags, b"\x00" * len(opaque))
    assert np.isnan(decode_repeat(flags, opaque).closes).all()
    assert_refusal("REFUSE_PIN", validate_bytes, raw, index, opaque, "0" * 64)
    assert_refusal("REFUSE_HASH", validate_bytes, raw, index, b"\x00" + opaque[1:], pin)
    bad = index.replace(b"2020-01-01", b"2024-01-01", 1)
    bad_raw, bad_pin = pack(dict(base, index_sha256=sha(bad)))
    assert_refusal("REFUSE_INDEX", validate_bytes, bad_raw, bad, opaque, bad_pin)
    bad_raw, bad_pin = pack(dict(base, payload_sha256=sha(opaque[:-1])))
    assert_refusal("REFUSE_SIZE", validate_bytes, bad_raw, index, opaque[:-1], bad_pin)
    with TemporaryDirectory() as path:
        root = Path(path)
        (root / "copy").write_bytes(raw)
        (root / "redirect").symlink_to(root / "copy")
        assert snapshot(root, "copy", len(raw)) == raw
        try:
            snapshot(root, "redirect", len(raw))
        except OSError:
            pass
        else:
            raise AssertionError("symlink accepted")
    return raw, pin, index, opaque


def go_refusals(fixture):
    raw, pin, index, opaque = fixture
    go = "p75r-" + pin
    prefix = "| 225 | approved "
    token = f"P75_REPEAT_GO={go}"
    assert approval_id(f"{prefix}`{token}` |\n") == go
    assert_refusal("REFUSE_LEDGER_ROW", approval_id, f"| 224 | {token} |")
    assert_refusal("REFUSE_LEDGER_ROW", approval_id, f"{prefix}{token} |\n{prefix}{token} |")
    assert_refusal("REFUSE_LEDGER_GO", approval_id, f"{prefix}not approved |")
    assert_refusal("REFUSE_LEDGER_GO", approval_id, f"{prefix}{token} {token} |")
    assert_refusal("REFUSE_LEDGER_GO", approval_id, f"{prefix}{token}a |")
    with TemporaryDirectory() as directory:
        folder = Path(directory)
        (folder / "manifest.json").write_bytes(raw)
        (folder / "index.csv").write_bytes(index)
        (folder / "prices.f64").write_bytes(b"\x00" + opaque[1:])
        receipt = folder / "repeat_receipt.json"
        receipt.write_text(json.dumps({"schema": 1, "go_id": go, "manifest_sha256": pin}))
        with open_folder(folder) as fd:
            assert_refusal("REFUSE_GO_MISMATCH", run_repeat, fd, "p75r-" + "0" * 64)
            assert_refusal("REFUSE_HASH", run_repeat, fd, go)
            assert not (folder / "RUN.lock").exists()
            (folder / "prices.f64").write_bytes(opaque)
            output = registered_summary(run_repeat(fd, go)).splitlines()
            assert (folder / "RUN.lock").read_text() == go + "\n"
            assert (folder / "fills.csv").read_text().splitlines() == [
                "cost_line,book,date_utc,coin,signed_notional,cost"
            ]
            assert len(output) == 3 and output[0].startswith("MAIN ") and output[1].startswith("HARSH ")
            assert output[-1] == "IMPLEMENTATION_CHECK FAIL" and not any("BTC" in line for line in output)
            assert_refusal("REFUSE_LOCK", run_repeat, fd, go)
    # A price-only refusal happens after the durable lock, never before it.
    with TemporaryDirectory() as directory:
        folder = Path(directory)
        invalid = b"\x00" * len(opaque)
        m = json.loads(raw)
        m["payload_sha256"] = sha(invalid)
        revised = json.dumps(m).encode()
        pin = sha(revised)
        go = "p75r-" + pin
        for name, value in (("manifest.json", revised), ("index.csv", index), ("prices.f64", invalid),
                            ("repeat_receipt.json", json.dumps(
                                {"schema": 1, "go_id": go, "manifest_sha256": pin}).encode())):
            (folder / name).write_bytes(value)
        with open_folder(folder) as fd:
            assert_refusal("REFUSE_PRICES", run_repeat, fd, go)
            assert (folder / "RUN.lock").read_text() == go + "\n"
            assert not (folder / "fills.csv").exists()
            assert_refusal("REFUSE_LOCK", run_repeat, fd, go)


def monthly_no_band(cfg, fee):
    days = tuple(date(2020, 1, 29) + timedelta(days=i) for i in range(6))
    prices = np.full((len(days), 1), 100.)
    allowed = np.ones_like(prices, dtype=bool)
    tape = Tape(days, ("TOY",), prices, prices, allowed, allowed)
    long = np.ones((len(days), 1, 1), dtype=bool)
    target = np.array([.50, .60, .60, .60, .60, .60])
    spec = (long, (cfg["target_vol"] / target)[:, None], long)
    clock = calendar(tape, spec[2])
    book = play(tape, fee, cfg, 1, spec, clock)
    assert .0 < abs(book.weights[2, 0, 0] - .60) < cfg["resize_weight_delta"]
    assert not any(d == 2 for d, *_ in book.fills)
    assert any(d == 3 and signed > 0 for d, _, signed, _ in book.fills)
    assert book.targets[3, 0, 0] == .60


def equation_and_gap(cfg, marks):
    values = np.array([2, 4, 3, 3, np.nan, 2, 5, 5, 5.])[:, None]
    days = tuple(date(2020, 1, 1) + timedelta(days=i) for i in range(len(values)))
    eligible = np.ones_like(values, dtype=bool)
    tape = Tape(days, ("TOY",), values, values, eligible, eligible)
    sig, _, _ = indicators(tape, (2,), {**cfg, "vol_days": 2}, marks["annual_days"])
    assert sig[:, 0, 0].tolist() == [False, True, False, True, True, False, True, True, True]
    # A sale pending through a missing executable open waits, and is not backfilled.
    px = np.array([100., 100., 100., np.nan, 100., 100.])[:, None]
    closes = np.full_like(px, 100.)
    sell = np.isfinite(px)
    gap = Tape(days[:len(px)], ("TOY",), px, closes, np.ones_like(px, dtype=bool), sell)
    long = np.array([False, True, False, True, False, False])[:, None, None]
    spec = (long, np.full_like(px, .20), np.ones_like(long))
    out = play(gap, .0075, cfg, 1, spec, calendar(gap, spec[2]))
    assert [(d, q > 0) for d, _, q, _ in out.fills] == [(2, True), (4, False)]


def self_test():
    cfg, marks, costs = load_config()
    go_refusals(validation())
    monthly_no_band(cfg, costs["main"])
    equation_and_gap(cfg, marks)
    hit, null = toy(True), toy(False)
    inp = indicators(hit, cfg["lookbacks"], cfg, marks["annual_days"])
    clock = calendar(hit, inp[2])
    fee = costs["main"]
    planted = play(hit, fee, cfg, cfg["cap"], inp, clock)
    zero = play(null, fee, cfg, cfg["cap"], inp, calendar(null, inp[2]))
    leaked = play(hit, fee, cfg, cfg["cap"], inp, clock, shift=1)
    assert len(planted.fills) > 0 and planted.nav[-1] > 1, planted.nav[-1]
    cut = date.fromisoformat(cfg["repeat_cut"])
    assert period_return(planted.nav, hit.days, hit.days[0], cut) > 0
    assert period_return(planted.nav, hit.days, cut, date(2024, 1, 1)) > 0
    assert len(zero.fills) > 0 and zero.nav[-1] < 1
    assert abs(planted.nav[-1] - leaked.nav[-1]) > 1e-6
    assert planted.max_target_weight <= 1 and np.max(planted.weights) <= 1 + 1e-12
    assert all(paid > 0 and np.isclose(paid, abs(notional) * fee, rtol=1e-12)
               for _, _, notional, paid in planted.fills)
    # At par opens and terminal close, no directional P&L: NAV loss must equal all fees.
    assert np.isclose(1 - zero.nav[-1], sum(x[-1] for x in zero.fills), atol=1e-12)
    # Editing a close cannot change a previously booked opening fill.
    c = hit.closes.copy()
    c[111, 0] *= 2
    edited = Tape(hit.days, hit.names, hit.opens, c, hit.eligible, hit.sell)
    revised = indicators(edited, cfg["lookbacks"], cfg, marks["annual_days"])
    revised_book = play(edited, fee, cfg, cfg["cap"], revised, calendar(edited, revised[2]))
    assert [x for x in revised_book.fills if x[0] <= 111] == [x for x in planted.fills if x[0] <= 111]
    # Exercise real spell placement on a short tape, not only all-cash fallbacks.
    n = 240
    short = Tape(hit.days[:n], hit.names, hit.opens[:n], hit.closes[:n], hit.eligible[:n], hit.sell[:n])
    short_input = tuple(a[:n] for a in inp)
    short_clock = calendar(short, short_input[2])
    short_book = play(short, fee, cfg, cfg["cap"], short_input, short_clock)
    args = (short, fee, cfg, {**marks, "twins": 12}, short_input, short_clock, short_book)
    twin_cut, missed, attempted = twins(*args)
    assert twin_cut != 1 and attempted >= missed >= 0 and (twin_cut, missed, attempted) == twins(*args)
    # Exercise the entire report on flat prices (no volatility size, no spells).
    flat_px = np.full_like(hit.opens, 100.)
    flat = Tape(hit.days, hit.names, flat_px, flat_px, hit.eligible, hit.sell)
    report = score_repeat(flat)
    assert not report["implementation_check"] and all(
        r["primary"]["net"] == r["twins_cut_net"] == 0 and r["twins_n"] == 500
        for r in report["lines"].values())
    print("MEASURED SYNTHETIC planted edge found; null edge not found; future shift changed terminal result")
    print("MEASURED SYNTHETIC every fill costed; 100% cap; ratchet priority; pending gap exit; no-decode validation")
    print("MEASURED SYNTHETIC monthly reset bypassed band; committed-go parser; lock before decode; one-shot refusals")
