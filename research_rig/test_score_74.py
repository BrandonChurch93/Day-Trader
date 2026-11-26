"""Invented Plan 74 fixtures. Opens no actual market or filing file."""

import json
import math
import os
import subprocess
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

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
    clock = tuple(date(2017, 1, 3) + timedelta(days=i) for i in range(gap + 2))
    hit = [Signal("A", "without_earnings", "SYN-" + str(i), 0, 7, 7, 8)
           for i in range(need["A"])]
    hit += [replace(hit[0], day=i) for i in (1, gap, gap + 1)]
    count = count_signals(hit, clock, cfg)
    assert count["A", "without_earnings"] == (need["A"] + 3, 4, need["A"] + 1, 2)
    lines = list(count_lines(count, cfg))
    assert lines[-2:] == ["BRANCH A without_earnings", "BRANCH B close_on_count"]
    assert all(type(n) is int for row in count.values() for n in row)
    print("MEASURED fixture: raw/lower integer-only counts; branch uses third-version need and the lower bound")


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
    files = {"calendar.csv": ("session\n" + "\n".join(days) + "\n").encode(),
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
        ledger.write_text(f"| 226 | Plan 74 `P74_DESIGN_GO={go}` |\n")
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
            p.load_snapshot(fd, pin, cfg)
            refusal("REFUSE_UNRESOLVED_PLAN", p.guarded_run, fd, committed, cfg)
            assert not (folder / "RUN.lock").exists()

            def decoder(layout, stream, _):
                assert (folder / "RUN.lock").read_text() == go + "\n"
                assert stream.read(len(row)) == row
                stream.seek(0)
                return p.decode_bar(stream)

            bar = p.guarded_run(fd, committed, cfg, authorize=lambda _: None, decoder=decoder)
            assert bar.close == 5
            refusal("REFUSE_LOCK", p.guarded_run, fd, committed, cfg, authorize=lambda _: None,
                    decoder=decoder)
    print("MEASURED fixture: dirty checkout, missing or duplicate approval, wrong hash, and second run refused")
    print("MEASURED fixture: opaque validation and durable-before-decode lock ordering exercised; production activation refused")


def self_test():
    cfg = config()
    test_play(cfg)
    test_marks(cfg)
    test_counts(cfg)
    test_guards(cfg)


if __name__ == "__main__":
    self_test()
