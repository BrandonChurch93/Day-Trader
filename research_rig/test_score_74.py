"""Invented Plan 74 fixtures. Opens no actual market or filing file."""

import json
import math
import os
import subprocess
from dataclasses import replace
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import score_74 as p
from count_74 import Bar, Signal, close_signals, config, count_lines, count_signals


def refusal(code, call, *args, **kwargs):
    try:
        call(*args, **kwargs)
    except p.Refusal as e:
        assert str(e) == code, str(e)
    else:
        raise AssertionError(code)


def near(a, b):
    assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12), (a, b)


def bars_fixture(cfg):
    t = cfg["signal_rules"]["A"]["high_sessions"] + 8
    clock = tuple(date(2017, 1, 3) + timedelta(days=i) for i in range(t + 4))
    steady = Bar(10, 10.04, 9.96, 10, 600_000)
    stock = [steady] * t
    stock[-10:-5] = [Bar(10, 10.04, 9.70, 10, 600_000)] * 5
    stock += [Bar(10.13, 10.24, 10.05, 10.24, 1_200_000),
              Bar(10.25, 10.6, 10.20, 10.55, 600_000),
              Bar(11.0, 11.20, 10.85, 11.10, 600_000), None]
    fund = tuple(Bar(25, 25, 25, 25, 1) for _ in clock)
    tape = p.Tape(clock, {"MADE_UP": tuple(stock), "IWM": fund}, {t: frozenset({"MADE_UP"})},
                  {t: {"MADE_UP": 100_000_000}}, {t: frozenset({"MADE_UP"})}, {}, {},
                  {"MADE_UP": t + 2})
    candidates, _ = close_signals(tape.view(t), cfg)
    assert len(candidates) == 1 and candidates[0].arm == "without_market", candidates
    return tape, candidates[0]


def test_play(cfg):
    tape, sig = bars_fixture(cfg)
    t = sig.day
    result = p.simulate(tape, sig, cfg)
    assert len(result.legs) == 1
    assert result.legs[0].reason == "delisted" and result.legs[0].day == t + 2
    near(result.legs[0].value, 11.10)
    cfg_cost = cfg["costs_bp_per_side"]["A"]
    cost = cfg_cost / p.BP_PER_UNIT
    over = cfg["stop_overshoot_share_of_risk"]["A"]
    primary = cfg["delisted_last_close_share"]["primary"]
    near(p.excess(result, cfg_cost, over, primary),
         11.10 * (1 - cost) / (10.25 * (1 + cost)) - 1)
    assert p.simulate(tape, replace(sig, day=t + 1), cfg) is None
    assert p.simulate(tape, replace(sig, day=t - 1), cfg).day != result.day

    def edit(day, bar):
        s = list(tape.bars[sig.id])
        s[day] = bar
        return replace(tape, bars={**tape.bars, sig.id: tuple(s)})

    future = edit(t + 1, Bar(10.25, 10.6, 9.9, 10.55, 600_000))
    assert close_signals(future.view(t), cfg) == close_signals(tape.view(t), cfg)
    stop = p.simulate(future, sig, cfg)
    assert stop.legs[0].reason == "stop_intraday"
    near(p.excess(stop, cfg_cost, over, primary),
         (sig.stop - over * (10.25 - sig.stop)) * (1 - cost) / (10.25 * (1 + cost)) - 1)
    gap = p.simulate(edit(t + 2, Bar(9.5, 9.9, 9.4, 9.6, 600_000)), sig, cfg)
    assert gap.legs[0].reason == "stop_gap"
    near(p.excess(gap, cfg_cost, over, primary), 9.5 * (1 - cost) / (10.25 * (1 + cost)) - 1)
    print("MEASURED fixture: close-only signal; one-session shift changes execution; future-bar edits do not change earlier signals")
    print("MEASURED fixture: delisted last close; overshoot only on intraday stop; one cost per side")


def test_marks(cfg):
    t = [(date(2017, 1, 3), .01), (date(2017, 1, 9), .03),
         (date(2017, 2, 1), .06), (date(2017, 3, 1), .10)]
    # Mean .05; centered month totals -.06, .01, .05; G=3.
    near(p.cluster_t(t, "entry_month"), .05 / (math.sqrt(3 / 2 * (.06**2 + .01**2 + .05**2)) / 4))
    assert p.cluster_t(t[:2], "entry_month") is None
    bp = cfg["costs_bp_per_side"]["A"]
    fee = bp / p.BP_PER_UNIT

    def fixture(edge, spike=False):
        rows = []
        for y in range(2017, 2022):
            for mon in range(1, 13):
                for d in (3, 5, 7):
                    enter = date(y, mon, d)
                    noise = ((mon % 3) - 1) * .003
                    raw = 10 * (1 + fee) / (1 - fee) * (1 + (3 if spike and len(rows) == 0 else edge + noise))
                    clock = (enter - timedelta(days=1), enter, enter + timedelta(days=1))
                    stock = (Bar(9.8, 10, 9.8, 9.98, 100),
                             Bar(10, 10, 10, 10, 100),
                             Bar(raw, raw, raw, raw, 100))
                    fund = (Bar(20, 20, 20, 20, 100),) * len(clock)
                    tape = p.Tape(clock, {"TEST": stock, "IWM": fund}, {}, {}, {}, {}, {}, {})
                    s = Signal("A", "earnings", "TEST", 0, 9.8, 9.8, 10.04)
                    rows.append(p.simulate(tape, s, cfg))
        return p.aggregate(rows, "A", cfg, months=60)

    assert fixture(.02)["passed"]
    assert not fixture(0)["passed"]
    trim = fixture(0, True)["main"]
    assert trim["mean"] >= cfg["marks"]["mean_floor"] and trim["trimmed_count"] == 2
    assert trim["trimmed_mean"] < 0 and not trim["passed"]
    print("MEASURED fixture: planted edge advances; zero edge does not; top-1% removal mark applied")
    print("MEASURED fixture: month-clustered t matches hand calculation; undefined error does not pass")


def test_counts(cfg):
    gap = cfg["count_branch"]["lower_bound_gap_sessions"]["A"]
    need = cfg["count_branch"]["need_signals"]
    offset = cfg["design_last_signal_offset"]["A"]
    clock = tuple(date(2017, 1, 3) + timedelta(days=i) for i in range(gap + offset + 2))
    hit = [Signal("A", "without_earnings", "SYN-" + str(i), 0, 7, 7, 8)
           for i in range(need["A"])]
    hit += [replace(hit[0], day=i) for i in (1, gap, gap + 1)]
    hit.append(replace(hit[0], day=gap + 2))
    b = Signal("B", "pooled", "BB", 0, 7, 7, 8)
    gap_b = cfg["count_branch"]["lower_bound_gap_sessions"]["B"]
    hit.extend(replace(b, day=i) for i in (0, gap_b, gap_b + 1))
    count = count_signals(hit, clock, cfg)
    assert count["A", "without_earnings"] == (need["A"] + 3, 4, need["A"] + 1, 2)
    assert count["B", "pooled"] == (3, 3, 2, 2)
    lines = list(count_lines(count, cfg))
    assert lines[-2:] == ["BRANCH A without_earnings", "BRANCH B close_on_count"]
    assert len(lines) == 5
    assert all(type(n) is int for row in count.values() for n in row)
    print("MEASURED fixture: raw/lower integer-only counts; branch uses third-version need and the lower bound")


def test_asof(cfg):
    tape, sig = bars_fixture(cfg)
    t = sig.day
    days = tape.days
    close = tuple(p.exchange_close("13:00" if i == t else "16:00", d) for i, d in enumerate(days))

    def admit(when):
        return {"quarter": days[t - 6].isoformat(), "accepted_et": close[t].replace(hour=when).isoformat(),
                "accession": "SYN"}

    def count(day, when, report, shares):
        return {"filed_date": days[day].isoformat(), "accepted_et": close[day].replace(hour=when).isoformat(),
                "report_date": days[report].isoformat(), "basis_date": days[report].isoformat(),
                "shares": shares, "accession": "SYN"}

    stock = {"kind": "stock", "eligibility_intervals": [{"first": days[0].isoformat(), "last": days[-1].isoformat()}],
             "quarter_first_202": [admit(14)], "splits": [],
             "share_counts": [count(t, 9, t - 7, 90), count(t - 1, 9, t - 6, 40),
                              count(t - 1, 10, t - 7, 30), count(t - 1, 10, t - 6, 10),
                              count(t - 1, 10, t - 6, 20)]}
    asof = p.AsOf(days, close, {sig.id: stock}, cfg)
    assert asof.at(t)[1:] == ({sig.id: 20}, frozenset(), frozenset())
    assert sig.id in asof.at(t + 1)[2]
    early = p.AsOf(days, close, {sig.id: dict(stock, quarter_first_202=[admit(13)])}, cfg)
    assert sig.id in early.at(t)[2]
    assert p.simulate(replace(tape, splits={sig.id: {t + 1: 2}}), sig, cfg) is None
    diag = {"missing_share_name_days": 0}
    assert not close_signals(replace(tape.view(t), shares={}), cfg, diagnostics=diag)[0]
    assert diag["missing_share_name_days"] == 1
    exclusions = {"A": set(), "B": set()}
    assert not close_signals(replace(tape.view(t), earnings=frozenset()), cfg, branches_only=True,
                             exclusions=exclusions)[0]
    assert exclusions["A"] == {sig.id}

    broken = list(tape.bars[sig.id])
    broken[t - cfg["signal_rules"]["A"]["rank_sessions"] - 1] = None
    no_rank = replace(tape, bars={**tape.bars, sig.id: tuple(broken)})
    assert not close_signals(no_rank.view(t), cfg)[0]
    high = list(tape.bars[sig.id])
    high[t - cfg["signal_rules"]["A"]["rank_sessions"] - 1] = Bar(8, 8, 8, 8, 600_000)
    high[t - 100] = Bar(10, 20, 10, 10, 600_000)
    view = tape.view(t)
    ranked = replace(view, bars={**view.bars, "HIGHER": tuple(high[:t + 1])},
                     eligible=view.eligible | {"HIGHER"}, shares={**view.shares, "HIGHER": 100_000_000})
    assert not close_signals(ranked, cfg)[0]  # top rank misses the high gate, second rank cannot replace it
    broken[t - 1] = None
    assert p.trailing_ema(replace(tape, bars={**tape.bars, sig.id: tuple(broken)}).view(t),
                          sig.id, cfg["signal_rules"]["A"]["exit_ema_sessions"]) is None
    broken[-1] = broken[0]
    short = replace(tape, bars={**tape.bars, sig.id: tuple(broken)})
    near(p.trailing_ema(short.view(t + 1), sig.id, 2), (broken[t].close + broken[t + 1].close) / 2)
    print("MEASURED fixture: 64-close completeness, fresh EMA seed, early-close earnings, filing tie-break, missing shares and split-entry refusal")


def test_b_and_pool(cfg):
    days = tuple(date(2019, 1, 2) + timedelta(days=i) for i in range(22))
    raw = [Bar(1.02, 1.04, 1.0, 1.03, 100), Bar(1.04, 2.1, 1.02, 2.08, 100),
           Bar(1.05, 1.10, 1.0, 1.05, 100), Bar(.90, .92, .47, .5, 100)]
    normal = Bar(1.04, 1.05, 1.01, 1.04, 100)
    tape = p.Tape(days, {"S": tuple(raw + [normal] * (len(days)-len(raw))),
                         "IWM": tuple(Bar(10 + i, 10 + i, 10 + i, 10 + i, 100) for i in range(len(days)))},
                  {}, {}, {}, {"S": {2: 2}}, {}, {})
    sig = Signal("B", "pooled", "S", 0, 1, .98, 1.06, "Gold")
    trade = p.simulate(tape, sig, cfg)
    assert [(x.day, x.reason, x.shares) for x in trade.legs] == [
        (2, "partial", .5), (3, "stop_intraday", .5)]
    near(trade.legs[-1].value, .98)
    near(p.benchmark_return(trade), .5 * (12 / 11 - 1) + .5 * (13 / 11 - 1))
    with patch.object(p, "simulate", side_effect=[trade, None]):
        assert p.play_arm(tape, [sig, replace(sig, day=13), replace(sig, day=14)], cfg) == ([trade], 1, 1)
    with patch.object(p, "simulate", side_effect=[trade, None]):
        a = replace(sig, card="A")
        assert p.play_arm(tape, [a, replace(a, day=2), replace(a, day=3)], cfg) == ([trade], 1, 1)

    counts = cfg["compare_shown"]["min_pool"]
    controls = [f"SYN-{i}" for i in range(counts)]
    rows = {**tape.bars, **{n: tape.bars["IWM"] for n in controls}}
    full = p.pool_comparison(replace(tape, bars=rows), [(sig, trade)], {("B", 0): (*controls, "S")}, "B", cfg)
    near(full["mean_pool"], p.benchmark_return(trade))
    missing = list(rows[controls[0]])
    missing[3] = None
    rows[controls[0]] = tuple(missing)
    assert p.pool_comparison(replace(tape, bars=rows), [(sig, trade)], {("B", 0): controls}, "B", cfg)["blank"] == 1
    assert p.aggregate([trade], "B", cfg)["main"]["t"] is None
    print("MEASURED fixture: split-converted stop, weighted Card B exits, overlap and final-exit cooldown, and comparison minimum")


def test_gap_add_book(cfg):
    tape, base = bars_fixture(cfg)
    t = base.day
    unresolved = replace(tape, delisted={})
    u = p.simulate(unresolved, base, cfg)
    assert u.legs[-1].reason == "bars_ended"

    day = tape.days[0]
    clock = tuple(day + timedelta(days=i) for i in range(16))
    m = Bar(20, 20, 20, 20, 100)
    b = Bar(1.04, 1.05, 1.01, 1.04, 100)
    late = p.Tape(clock, {"S": (b, b) + (None,) * 13 + (b,), "IWM": (m,) * 16},
                  {}, {}, {}, {}, {}, {})
    s = Signal("B", "pooled", "S", 0, 1, .98, 1.06, "Revival")
    ended = p.simulate(late, s, cfg)
    assert ended.legs[-1].reason == "design_fence" and ended.legs[-1].day == 15
    assert p.aggregate([ended], "B", cfg)["coverage_warning"]
    assert p.simulate(late, replace(s, day=1), cfg) is None
    recovered = list(late.bars["S"])
    recovered[1] = Bar(1.04, 1.18, 1.01, 1.18, 100)
    recovered[6] = b
    trade = p.simulate(replace(late, bars={**late.bars, "S": tuple(recovered)}), s, cfg)
    assert trade.legs[0].reason == "partial" and trade.legs[0].day == 6

    fund = tuple(Bar(25 + i / 10, 25 + i / 10, 25 + i / 10, 25 + i / 10, 100)
                 for i in range(len(tape.days)))
    rows = list(tape.bars[base.id])
    rows[t + 2] = Bar(10.5, 10.6, 10.4, 10.55, 100)
    rows[t + 3] = Bar(10.53, 10.6, 10.36, 10.53, 100)
    on = replace(tape, bars={base.id: tuple(rows), "IWM": fund, "QQQ": fund}, delisted={})
    add = p.simulate(on, replace(base, arm="one_add"), cfg)
    half = cfg["add_rules"]["max_initial_share"]
    assert add.add_day == t + 3 and add.added == half
    assert add.legs[0].reason == "stop_intraday" and add.legs[0].risk == 0
    fee = cfg["costs_bp_per_side"]["A"] / p.BP_PER_UNIT
    spent = add.price + half * add.add_price
    near(p.benchmark_return(add), add.price / spent * (fund[t + 3].close / fund[t + 1].open - 1))
    expected = (1 + half) * 10.4 * (1 - fee) / (spent * (1 + fee)) - 1 - p.benchmark_return(add)
    near(p.excess(add, cfg["costs_bp_per_side"]["A"], cfg["stop_overshoot_share_of_risk"]["A"], 1), expected)

    book = p.cash_book(tape, [base], "A", cfg)
    assert book["funded"] == 1 and book["delisted_documented"] == 1 and book["ending_equity"] > 500
    split_bars = list(tape.bars[base.id])
    r = split_bars[t + 2]
    split_bars[t + 2] = Bar(r.open * 100, r.high * 100, r.low * 100, r.close * 100, r.volume / 100)
    split_tape = replace(tape, bars={**tape.bars, base.id: tuple(split_bars)},
                         splits={base.id: {t + 2: Fraction(1, 100)}})
    rounded = p.cash_book(split_tape, [base], "A", cfg)
    assert rounded["split_fractions_rounded"] == 1 and rounded["ending_equity"] < 500
    assert p.settlement_lag(date(2017, 9, 4), cfg["book_rules"]) == 3
    assert p.settlement_lag(date(2017, 9, 5), cfg["book_rules"]) == 2
    print("MEASURED fixture: resumed-bar exit, undocumented last close, fence warning, half add and weighted benchmark, and settled whole-share book with split rounding")


def to_json(data):
    return json.dumps(data, sort_keys=True).encode()


def write_private(folder, basename, bytes_):
    path = folder / basename
    path.write_bytes(bytes_)
    path.chmod(0o600)


def custody_fixture(folder, cfg):
    a = cfg["signal_rules"]["A"]
    names = sorted(set(cfg["benchmark"].values()) | {cfg["arm_52w"]["market_fund"], a["ema_fund"],
                                                      a["sma_fund"]})
    identity = [dict(id=n, kind="fund", ticker_intervals=[], cusips=[], registration_date=None,
                     delisted=False, delist_effective=None, eligibility_intervals=[], splits=[],
                     quarter_first_202=[], share_counts=[], halts=[]) for n in names]
    days = [cfg[k] for k in ("warmup_first", "design_first", "design_last")]
    row = p.BAR.pack(5, 6, 4, 5, 3_000_000)
    files = {"calendar.csv": ("session,close_et\n" + "".join(f"{d},16:00\n" for d in days)).encode(),
             "identity.json": to_json({"schema": 1, "securities": identity}),
             "bars_index.csv": ("id,first_session_index,rows\n" +
                                "".join(f"{n},0,{len(days)}\n" for n in names)).encode(),
             "bars.f64": row * (len(names) * len(days)),
             "source_receipt.json": to_json({"schema": 1, "source_pins": {"fake": "f" * 64},
                                            "review_id": "fixture"})}
    manifest = {"schema": 1, "rows": len(names) * len(days),
                **{k: cfg[k] for k in ("warmup_first", "design_first", "design_last")},
                "sha256": {k: p.sha(v) for k, v in files.items()}}
    files["manifest.json"] = to_json(manifest)
    pin = p.sha(files["manifest.json"])
    files["design_receipt.json"] = to_json({"schema": 1, "go_id": "p74d-" + pin, "manifest_sha256": pin})
    for name, data in files.items():
        write_private(folder, name, data)
    return pin, row, files


def test_guards(cfg):
    with TemporaryDirectory(prefix="p74-invented-") as d:
        root = Path(d)
        folder, repo = root / "private", root / "repo"
        folder.mkdir(mode=0o700)
        repo.mkdir()
        pin, row, files = custody_fixture(folder, cfg)
        go = "p74d-" + pin
        ledger = repo / p.LEDGER
        ledger.parent.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = os.devnull

        def git(*args):
            subprocess.run(("git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                            *args), cwd=repo, env=env, check=True, capture_output=True)

        def committed():
            return p.committed_approval(repo)

        git("init", "-q")
        ledger.write_text("| 226 | Plan 74 price-free |\n")
        git("add", ".")
        git("commit", "-qm", "fixture")
        refusal("REFUSE_LEDGER_GO", committed)
        count_go = "p74c-" + pin
        ledger.write_text(f"| 226 | Plan 74 `P74_DESIGN_GO={go}` `P74_COUNT_GO={count_go}` |\n")
        refusal("REFUSE_DIRTY", committed)
        git("add", ".")
        refusal("REFUSE_DIRTY", committed)
        git("commit", "-qm", "fixture approval")
        assert committed()[1] == go
        git("update-index", "--assume-unchanged", p.LEDGER)
        refusal("REFUSE_DIRTY", committed)
        git("update-index", "--no-assume-unchanged", p.LEDGER)
        refusal("REFUSE_LEDGER_GO", p.approved_id, f"| 226 | P74_DESIGN_GO={go} P74_DESIGN_GO={go} |")
        with p.private_folder(folder) as fd:
            refusal("REFUSE_PIN", p.load_snapshot, fd, "0" * 64, cfg)
            write_private(folder, "bars.f64", b"\xff" + files["bars.f64"][1:])
            refusal("REFUSE_HASH", p.load_snapshot, fd, pin, cfg)
            write_private(folder, "bars.f64", files["bars.f64"])
            layout = p.load_snapshot(fd, pin, cfg)
            p.required_benchmark_prints(layout, cfg)
            refusal("REFUSE_COUNT_NOT_COMPLETE", p.guarded_run, fd, committed, cfg)
            assert not (folder / "RUN.lock").exists()
            days, clocks, names, segments = layout
            reduced = [s for s in segments if s[0] != "IWM"]
            refusal("REFUSE_BENCHMARK_MISSING " + cfg["design_last"], p.required_benchmark_prints,
                    (days, clocks, names, reduced), cfg)

            def count_token():
                return p.committed_approval(repo, stage="COUNT")

            refusal("REFUSE_GO_MISMATCH", p.guarded_count, fd, count_token, "0" * 64, cfg)
            assert p.guarded_count(fd, count_token, pin, cfg)[-2:] == [
                "BRANCH A close_on_count", "BRANCH B close_on_count"]
            assert (folder / "COUNT.lock").read_text() == count_go + "\n"
            refusal("REFUSE_LOCK", p.guarded_count, fd, count_token, pin, cfg)
            assert not (folder / "RUN.lock").exists()

            def decoder(layout, stream, _):
                assert (folder / "RUN.lock").read_text() == go + "\n"
                assert stream.read(len(row)) == row
                stream.seek(0)
                bar = p.decode_bar(stream)
                assert bar.close == 5
                return p.decode_design(layout, stream, cfg, p.completed_count(fd, pin))

            report = p.guarded_run(fd, committed, cfg, decoder=decoder)
            assert list(p.summary(report, cfg))[-1] == "closed"
            refusal("REFUSE_LOCK", p.guarded_run, fd, committed, cfg, decoder=decoder)
    print("MEASURED fixture: dirty checkout, missing or duplicate approval, wrong hash, and second run refused")
    print("MEASURED fixture: independent count and design locks; pinned opaque adapter; missing IWM dates refused before design lock")


def self_test():
    cfg = config()
    test_play(cfg)
    test_marks(cfg)
    test_counts(cfg)
    test_asof(cfg)
    test_b_and_pool(cfg)
    test_gap_add_book(cfg)
    test_guards(cfg)


if __name__ == "__main__":
    self_test()
