"""All prices here are invented in memory. No custody directory or bars are opened."""

import json
from contextlib import redirect_stdout
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np

import score_75 as scorer
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
            # Existing made-up go fixture, captured on main d454509 before vault edits.
            assert sha(("\n".join(output) + "\n").encode()) == (
                "2f7f39b6077e61cfe67e90148d1890b47903211799c37e4ddb96d9f1214ef771"
            )
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


def vault_marks_and_btc(cfg):
    gross = np.array([1.00, 1.10, 1.10, 0.99])
    strategy = np.array([1.00, 1.05, 1.05, 0.9975])
    fees = .01
    # +10%, -10% gross; +5%, -5% strategy. Scaled entry notional 0.5 NAV,
    # scaled exit notional 0.5 * .99/1.10 of prior NAV.
    fills = [(1, 0, 1.0, 0.), (3, 0, -0.99, 0.)]
    matched, scale = scorer.matched_btc(gross, fills, strategy, fees)
    assert np.isclose(scale, .5)
    assert np.isclose(matched, (1.05 - .005) * (.95 - .0045) - 1)
    assert scorer.matched_btc(np.ones(4), [], strategy, fees) == (None, None)
    matched, scale = scorer.matched_btc(np.array([1., .50]), [], np.array([1., 2.20]), fees)
    assert matched is None and np.isclose(scale, 2.4)  # 1 + 2.4 * (-.50) is below zero.
    assert scorer.vault_marks(.2, .3, matched, -.03, cfg) == {
        "positive_net": True, "above_matched_btc_net": False, "drawdown_under_ceiling": True,
        "after_paper_at_or_above_floor": True,
    }
    # Plant a passing mark input and cross only the relevant boundary in each case.
    base = [0.20, 0.30, -0.10, cfg["after_paper_min_net"]]
    good = scorer.vault_marks(*base, cfg)
    assert all(good.values())
    boundary = (0.0, cfg["vault_max_drawdown"], base[0], base[3] - 0.01)
    for index, (mark, value) in enumerate(zip(
            ("positive_net", "drawdown_under_ceiling", "above_matched_btc_net",
             "after_paper_at_or_above_floor"), boundary, strict=True)):
        planted = base.copy()
        planted[index] = value
        checks = scorer.vault_marks(*planted, cfg)
        assert {k for k, v in checks.items() if not v} == {mark}
    assert not scorer.vault_marks(.2, .3, None, -.03, cfg)["above_matched_btc_net"]


def vault_warmup(cfg, fee):
    days = scorer.vault_axes(cfg)
    path = 100 + np.arange(len(days)) / 7
    opens = np.full((len(days), len(NAMES)), np.nan)
    opens[:, NAMES.index("BTC")] = path
    admitted = np.isfinite(opens)
    tape = Tape(days, NAMES, opens, opens, admitted, admitted)
    inp = indicators(tape, cfg["lookbacks"], cfg, cfg["vault_annual_days"])
    clock = calendar(tape, inp[2])
    book = play(tape, fee, cfg, cfg["cap"], inp, clock)
    assert book.fills and book.fills[0][0] == cfg["vol_days"] + 1
    assert np.all(book.nav[:book.fills[0][0]] == 1)
    benchmark = scorer.btc_comparison(tape, book, fee, cfg, inp, clock, None)
    assert benchmark["status"] == "SCORED" and benchmark["scale"] is not None
    gap = opens.copy()
    gap[-2, NAMES.index("BTC")] = np.nan
    missing = Tape(days, NAMES, gap, opens, admitted, admitted)
    benchmark = scorer.btc_comparison(missing, book, fee, cfg, inp, clock, None)
    assert benchmark["status"] == "UNSCORABLE" and benchmark["matched_net"] is None


def vault_guards(cfg):
    days = scorer.vault_axes(cfg)
    index = scorer.VAULT_HEADER + b"".join(
        f"{d},{coin},NOT_ADMITTED,0,0,0\n".encode() for d in days for coin in NAMES)
    n = len(days) * len(NAMES)
    opaque = b"\xff" * (n * 16)
    counts = {"PROVED": 0, "INFERRED": 0, "NOT_ADMITTED": n}
    manifest = {
        "schema": 1, "start": cfg["vault"][0], "stop_exclusive": cfg["vault"][1],
        "names": list(NAMES), "rows": n, "admission_coin_days": counts, "index_sha256": sha(index),
        "payload_sha256": sha(opaque), "source_receipt_sha256": "a" * 64,
        "eligibility_receipt_sha256": "b" * 64,
    }
    raw = json.dumps(manifest).encode()
    pin = sha(raw)
    go = "p75v-" + pin
    token = "P75_VAULT_GO=" + go
    repeat = "P75_REPEAT_GO=p75r-" + pin
    parse = scorer.vault_approval_id
    assert parse(f"| 225 | `{repeat}` `{token}` |") == go
    assert_refusal("REFUSE_LEDGER_GO", parse, f"| 225 | {repeat} |")
    assert_refusal("REFUSE_LEDGER_GO", parse, f"| 225 | {token} {token} |")
    assert_refusal("REFUSE_LEDGER_GO", parse, f"| 225 | P75_VAULT_GO=p75r-{pin} |")
    assert_refusal("REFUSE_LEDGER_ROW", parse, f"| 226 | {token} |")
    with patch.object(scorer.subprocess, "run") as git:
        git.side_effect = [
            scorer.subprocess.CompletedProcess([], 0, b"a" * 40 + b"\n"),
            scorer.subprocess.CompletedProcess([], 0, b" M research_rig/TRIAL_LEDGER.md\n"),
        ]
        assert_refusal("REFUSE_DIRTY", scorer.committed_approval, parse)
        assert git.call_count == 2
    out = StringIO()
    with redirect_stdout(out):
        assert scorer.main(["--go-vault", "/not-the-vault"]) == 2
    assert out.getvalue() == "REFUSE_DIR\n"
    validate = scorer.validate_vault_bytes
    assert_refusal("REFUSE_PIN", validate, cfg, raw, index, opaque, "0" * 64)
    pre = index.replace(b"2024-01-01", b"2023-12-31", 1)
    revised = json.dumps(dict(manifest, index_sha256=sha(pre))).encode()
    assert_refusal("REFUSE_INDEX", validate, cfg, revised, pre, opaque, sha(revised))
    revised = json.dumps(dict(manifest, admission_coin_days={
        "PROVED": 1, "INFERRED": 0, "NOT_ADMITTED": n - 1})).encode()
    assert_refusal("REFUSE_ADMISSION", validate, cfg, revised, index, opaque, sha(revised))
    flags, actual = validate(cfg, raw, index, opaque, pin)
    assert actual == counts and not flags.any()
    proved, inferred = b",PROVED,0,0,1\n", b",INFERRED,0,0,1\n"
    mixed = index.replace(b",NOT_ADMITTED,0,0,0\n", proved, 1)
    mixed = mixed.replace(b",NOT_ADMITTED,0,0,0\n", inferred, 1)
    mixed_counts = {"PROVED": 1, "INFERRED": 1, "NOT_ADMITTED": n - 2}
    revised = json.dumps(dict(manifest, index_sha256=sha(mixed), admission_coin_days=mixed_counts)).encode()
    _, actual = validate(cfg, revised, mixed, opaque, sha(revised))
    assert actual == mixed_counts

    def write_fixture(folder, payload):
        m = json.dumps(dict(manifest, payload_sha256=sha(payload))).encode()
        approved = "p75v-" + sha(m)
        (folder / "manifest.json").write_bytes(m)
        (folder / "index.csv").write_bytes(index)
        (folder / "prices.f64").write_bytes(payload)
        (folder / "vault_receipt.json").write_text(json.dumps({
            "schema": 1, "go_id": approved, "manifest_sha256": sha(m),
            "scorer_absent_during_extract": True,
        }))
        return approved

    with TemporaryDirectory() as d:
        folder = Path(d)
        approved = write_fixture(folder, opaque)
        out = StringIO()
        with patch.object(scorer, "VAULT_DIR", folder), patch.object(scorer, "decode_vault") as decode, redirect_stdout(out):
            assert scorer.main(["--validate-vault", approved[5:]]) == 0
            decode.assert_not_called()
        assert out.getvalue() == "VALIDATED_VAULT_NO_PRICE_DECODE\n"
        assert not (folder / "RUN.lock").exists()
        prices = folder / "prices.f64"
        redirected = folder / "made_up_redirect"
        prices.rename(redirected)
        prices.symlink_to(redirected)
        with open_folder(folder) as fd:
            assert_refusal("REFUSE_GO_MISMATCH", scorer.run_vault, fd, "p75r-" + pin)
            try:
                scorer.run_vault(fd, approved)
            except OSError:
                pass
            else:
                raise AssertionError("symlink accepted")
            assert not (folder / "RUN.lock").exists()
            prices.unlink()
            redirected.rename(prices)
            prices.write_bytes(b"\x00" + opaque[1:])
            assert_refusal("REFUSE_HASH", scorer.run_vault, fd, approved)
            assert not (folder / "RUN.lock").exists()
            prices.write_bytes(opaque)
            original = scorer.decode_vault

            def decode_after_lock(*args):
                assert (folder / "RUN.lock").read_text() == approved + "\n"
                return original(*args)

            with patch.object(scorer, "decode_vault", side_effect=decode_after_lock):
                report = scorer.run_vault(fd, approved)
            summary = scorer.vault_summary(report).splitlines()
            assert not report["passed"] and summary[-1] == "VAULT_RESULT FAIL"
            assert set(report["marks"]) == {"positive_net", "above_matched_btc_net",
                                           "drawdown_under_ceiling", "after_paper_at_or_above_floor"}
            assert len(summary) == 5 + 2 * (len(cfg["lookbacks"]) + 2)
            assert not any(f'"{name}"' in " ".join(summary) for name in NAMES)
            assert (folder / "fills.csv").stat().st_mode & 0o777 == 0o600
            assert_refusal("REFUSE_LOCK", scorer.run_vault, fd, approved)
    with TemporaryDirectory() as d:
        folder = Path(d)
        approved = write_fixture(folder, b"\x00" * len(opaque))
        with open_folder(folder) as fd:
            assert_refusal("REFUSE_PRICES", scorer.run_vault, fd, approved)
            assert (folder / "RUN.lock").exists()
            assert_refusal("REFUSE_LOCK", scorer.run_vault, fd, approved)
    with TemporaryDirectory() as d:
        folder = Path(d)
        approved = write_fixture(folder, opaque)
        with open_folder(folder) as fd, patch.object(scorer, "play", side_effect=Refusal("REFUSE_NAV")):
            assert_refusal("REFUSE_NAV", scorer.run_vault, fd, approved)
            assert (folder / "RUN.lock").read_text() == approved + "\n"
            assert_refusal("REFUSE_LOCK", scorer.run_vault, fd, approved)


def vault_shown_only_isolation(cfg, costs):
    days = scorer.vault_axes(cfg)
    shape = len(days), len(NAMES)
    values = np.full(shape, np.nan)
    flags = np.zeros(shape, dtype=bool)
    tape = Tape(days, NAMES, values, values, flags, flags)

    def planted_book(_, fee, _cfg, cap, inputs, __):
        if cap == cfg["printed_cap"] or fee == costs["harsh"]:
            raise Refusal("REFUSE_NAV")
        weights = np.zeros_like(inputs[0], dtype=float)
        return scorer.Book(np.linspace(1., 1.20, len(days)), weights, weights, [], 0, 0.)

    counts = {"NOT_ADMITTED": len(days) * len(NAMES), "PROVED": 0, "INFERRED": 0}
    with patch.object(scorer, "play", side_effect=planted_book), patch.object(
            scorer, "btc_comparison", return_value={"matched_net": .10}):
        result = scorer.score_vault(tape, cfg, costs, counts)
    assert result["passed"] and all(result["marks"].values())
    output = scorer.vault_summary(result).splitlines()
    assert output[-1] == "VAULT_RESULT PASS"
    assert any(line.startswith("VAULT_SHOWN_ONLY ") and "three_legs_200_cap" in line
               and "UNSCORABLE" in line for line in output)
    assert any(line.startswith("VAULT_HARSH_SHOWN_ONLY ") and "UNSCORABLE" in line for line in output)


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
    vault_marks_and_btc(cfg)
    vault_warmup(cfg, costs["main"])
    vault_guards(cfg)
    vault_shown_only_isolation(cfg, costs)
    print("MEASURED SYNTHETIC vault boundaries, hand-matched BTC with fees, missing BTC fails, in-vault warm-up only")
    print("MEASURED SYNTHETIC vault fence, admission, wrong directory, dirty checkout, ledger, hash, symlink and lock refusals")
    print("MEASURED SYNTHETIC nonpositive scaled BTC fails its mark; shown-only refusal cannot gate; primary refusal locks")
    print("MEASURED SYNTHETIC repeat summary byte-identical to d454509")
