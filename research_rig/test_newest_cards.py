"""Checks for the newest screen cards (newest_cards.py): figures read from the pinned summary files, refusals when the
files stop fitting, the E09 "no signal yet" case, and the Running now strip. Run: python3 -m pytest research_rig/test_newest_cards.py"""
import json, os, re, shutil, sys
import pytest
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import newest_cards as NC
import build_doc152_plan70_search as B152

HAVE = os.path.isdir(os.path.join(str(B152.CUSTODY), "sweep_70")) and os.path.isdir(os.path.join(str(B152.CUSTODY), "plan73"))
need_custody = pytest.mark.skipif(not HAVE, reason="the summary files are kept off the repo")


@pytest.fixture
def doc152_config(tmp_path):
    rel = "config/thresholds.yaml"
    cfg = yaml.safe_load((B152.ROOT / rel).read_text())
    target = tmp_path / rel
    target.parent.mkdir()
    return cfg, target


def test_doc152_ignores_unrelated_thresholds(doc152_config):
    cfg, target = doc152_config
    expected = B152.report_settings(B152.ROOT)
    cfg["unrelated_test_plan"] = {"value": 42}
    cfg["replay_70_plan"]["value"]["search_marks"]["finalist_cap"] = 99
    cfg["replay_70_plan"]["note"] = "Edited note"
    target.write_text(yaml.safe_dump(cfg))
    assert B152.report_settings(target.parent.parent) == expected


@pytest.mark.parametrize("keys, value, fault", [
    (("search_marks", "full_t"), 3.6, "differs"),
    (("vault_marks", "min_pre_vault_power"), None, "missing"),
    (("funding_adverse_bp_per_hour",), True, "differs"),
    (("spot_taker_round_trip_bp",), 161, "differs"),
])
def test_doc152_rejects_changes_to_used_thresholds(doc152_config, keys, value, fault):
    cfg, target = doc152_config
    group = cfg["replay_70_plan"]["value"]
    for key in keys[:-1]:
        group = group[key]
    if value is None:
        del group[keys[-1]]
    else:
        group[keys[-1]] = value
    target.write_text(yaml.safe_dump(cfg))
    path = r"\.".join(keys)
    with pytest.raises(ValueError, match=rf"{fault}: .*replay_70_plan\.value\.{path}$"):
        B152.report_settings(target.parent.parent)


@need_custody
def test_sweep_card_figures():
    c = NC.sweep_card("GH/")
    rows = dict(c["numbers"])
    assert (c["verdict"], c["tone"]) == ("No rule carried", "fail")
    assert rows["Rules written (188 in plan 70, 112 in plan 71)"] == "300"
    assert rows["Rules with enough trades to judge (160 and 63)"] == "223"
    assert rows["Finalists: 71-035, 71-013, 70-102"] == "3"
    assert rows["Chance 70-102 would pass the sealed years, bar 33%"] == "20.67%"
    assert rows["Chance 71-013 would pass the sealed years, bar 33%"] == "20.75%"
    assert rows["Chance 71-035 would pass the sealed years, bar 33%"] == "18.11%"
    assert rows["Carried to the sealed years"] == "none"
    assert "None was carried" in c["summary"] and "under the 33% bar" in c["summary"]
    assert c["basis"].startswith("MEASURED")


@need_custody
def test_plan73_card_figures():
    c = NC.plan73_card("GH/")
    assert (c["verdict"], c["tone"]) == ("A diagnosis, not a test", "info")
    assert c["bars"]["rows"] == [["Saved search result", 76.5], ["Coinbase hourly open", 75.6], ["One minute after the hour", 39.4],
                                 ["Five minutes late", 37.0], ["Fifteen minutes late", 28.4], ["Worst price of the minute", -28.1]]
    assert dict(c["numbers"])["Trades with Coinbase prints at every clock, of 382"] == "182"
    assert "182 of 382 trades had Coinbase prints" in c["summary"] and "diagnosis, not a test" in c["summary"]


def copy_custody(tmp_path):
    for sub in ("sweep_70", "plan73"):
        os.makedirs(tmp_path / sub)
    for rel in ("sweep_70/search_summary.out", "sweep_70/carry_results.json", "sweep_70/search71_summary.out",
                "sweep_70/carry71_results.json", "plan73/go.out", "plan73/count.out"):
        shutil.copy2(os.path.join(str(B152.CUSTODY), rel), tmp_path / rel)
    return tmp_path


@need_custody
def test_refuses_a_changed_summary_file(tmp_path):
    root = copy_custody(tmp_path)
    p = root / "sweep_70/carry71_results.json"
    d = json.loads(p.read_text()); d["forecasts"][0]["probability"] = 0.40
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError, match="differs"):
        NC.sweep_card("GH/", custody=root)
    g = root / "plan73/go.out"
    os.chmod(g, 0o600); g.write_text(g.read_text().replace("REACHABLE", "NOT_REACHABLE")); os.chmod(g, 0o600)
    with pytest.raises(ValueError, match="differs"):
        NC.plan73_card("GH/", custody=root)


def test_missing_custody_shows_no_figure(tmp_path):
    for c in (NC.sweep_card("GH/", custody=tmp_path), NC.plan73_card("GH/", custody=tmp_path)):
        assert c["verdict"] == "Figures not on this computer" and c["numbers"] == [] and "bars" not in c


STOP_WORDS = ("Stopped 2026-11-26 4:47 PM MT because the price source's terms bar this use.", "Closed unjudged")


def test_e09_card_is_stopped(monkeypatch, tmp_path):
    c = NC.e09_card("GH/")
    assert c["title"] == "E09: dip-buy rule, stopped on data terms" and c["verdict"] == "Stopped, closed unjudged"
    assert all(w in c["summary"] for w in STOP_WORDS) and "Replaced by E12 on Binance.US data." in c["summary"]
    assert [r[0] for r in c["numbers"]] in ([], ["Wake-ups recorded before the stop"])
    assert [l[0] for l in c["links"]] == ["E09 card", "Log counts"]
    assert not re.search(r"Signal|Judged|bp|spread|\$", json.dumps(c))
    monkeypatch.setattr(NC, "E09_LOG", str(tmp_path / "absent.json"))
    assert NC.e09_card("GH/")["numbers"] == []


def test_e09_wake_count_only(monkeypatch, tmp_path):
    log = json.load(open(os.path.join(NC.ROOT, "practice/forward/E09_log.json")))
    log.update(started=True, recorded=7)
    log["arms"]["70-102"].update(signals=2, trades_closed=1, trades_judged_ok=1)
    p = tmp_path / "E09_log.json"; p.write_text(json.dumps(log))
    monkeypatch.setattr(NC, "E09_LOG", str(p))
    assert NC.e09_card("GH/")["numbers"] == [["Wake-ups recorded before the stop", "7"]]


def queue_with(monkeypatch, row, step):
    text = NC.read(NC.QUEUE)
    lines = [l if not l.startswith(f"| {row} |") else "|".join(l.split("|")[:-2] + [f" {step} ", ""]) for l in text.splitlines()]
    real = NC.read
    monkeypatch.setattr(NC, "read", lambda path: "\n".join(lines) if path == NC.QUEUE else real(path))


def test_practice_pause(monkeypatch):
    assert NC.practice_pause() == {"when": "2026-11-26 5:03 PM MT"}
    queue_with(monkeypatch, "-", "2026-11-25 16:31 UTC")
    assert NC.practice_pause() is None


def test_stopped_cards_refuse_when_the_queue_no_longer_says_stopped(monkeypatch):
    queue_with(monkeypatch, "131", "2026-11-26 2:53 PM MT: live.")
    with pytest.raises(ValueError, match="E10 card: queue row 131"):
        NC.e10_card("GH/")


def test_running_now_strip(monkeypatch):
    rows = NC.running_now()
    assert rows and all(len(r) == 3 and r[1].endswith((".", ".)")) for r in rows)
    assert ["9b", "The earnings release reader.", None] in rows
    state = {r[0]: r[2] for r in rows}
    assert all(state[n] == "Stopped 2026-11-26 4:47 PM MT on data terms" for n in ("114", "131", "132", "133"))
    assert all(state[n] == "Running since 2026-11-26 5:39 PM MT" for n in ("135", "136"))
    assert state["137"] == "Stopped 2026-11-26 7:00 PM MT" and state["139"] == NC.row_state(NC.queue_step("139")) and state["139"].startswith(("Registered 2026-11-26 7:09 PM MT", "Running since "))
    assert NC.row_state("Registered 2026-11-26 4:55 PM MT. Builder assigned.") == "Registered 2026-11-26 4:55 PM MT, not started"
    assert state["-"] == "Paused 2026-11-26 5:03 PM MT"
    assert NC.row_state("HOLD since 2026-11-26 4:54 PM MT after week 8") == "On hold since 2026-11-26 4:54 PM MT"
    assert NC.row_state("2026-11-26 08:40 MT: stopped. More.") == "Stopped 2026-11-26 08:40 MT"
    assert all("`" not in r[1] and "](" not in r[1] for r in rows)
    text = ("# Q\n## Running now\n\nNote.\n\n| # | What | Inputs | Step |\n|---|---|---|---|\n"
            "| 7 | Plan 9 (`docs/x.md`). Second sentence. | a | b |\n| - | Et al. style, Smith et al. 2020 found it. More. | a | b |\n## Done\n")
    monkeypatch.setattr(NC, "read", lambda path: text if path == NC.QUEUE else open(os.path.join(NC.ROOT, path)).read())
    assert NC.running_now() == [["7", "Plan 9.", None], ["-", "Et al. style, Smith et al. 2020 found it.", None]]
    monkeypatch.setattr(NC, "read", lambda path: "# Q\n## Done\n")
    with pytest.raises(ValueError, match="no Running now section"):
        NC.running_now()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


# ---- Plan 75, the sealed years: two pinned aggregate files off repo
HAVE75 = os.path.isfile(NC.P75_RUN) and os.path.isfile(NC.P75_RECOMPUTE)
need75 = pytest.mark.skipif(not HAVE75, reason="the Plan 75 aggregate files are kept off the repo")


@need75
def test_plan75_card_figures():
    c = NC.plan75_card("GH/")
    assert c["id"] == "plan75" and c["verdict"] == "Passed, thinly" and c["tone"] == "mixed"
    assert c["title"] == "Plan 75: coin trend rule, the sealed years"
    n = dict(c["numbers"])
    assert n["Net after costs (75 hundredths of a percent a side)"] == "+9.04%"
    assert n["Bitcoin held at the same risk, after costs"] == "+6.40%"
    assert n["Largest fall from a high"] == "19.27%"
    assert n["Since the paper's sample ended (2025-03-19)"] == "\u22124.35%"
    assert n["Median hold"] == "8 days" and n["Fills (buys and sells)"] == "2,283"
    assert n["Second version, built blind from the plan: net"] == "+10.11%"
    assert c["bars"]["unit"] == "%"
    assert c["bars"]["rows"] == [["2024", 18.8], ["2025", -4.6], ["2026, to October", -3.8], ["Whole stretch, harsher cost", -3.9]]
    for words in ("20 large coins", "10, 20 or 30 day high", "only moves up", "8 days", "2024-01-01 to 2026-10-31",
                  "all four marks", "All the gain came in 2024", "145 hundredths", "pretend-money forward card (E10), not real money"):
        assert words in c["summary"]
    assert c["links"] == [["Plan 75 result", "GH/docs/research/181_plan_75_heldback_result.md"]]
    assert "plan_75_vault_run.out" in c["basis"] and "VAULT_RESULT.json" in c["basis"] and "kept off the repo" in c["basis"]
    assert "-" not in "".join(v for _, v in c["numbers"])


@need75
@pytest.mark.parametrize("which", ["run", "recompute"])
def test_plan75_refuses_a_changed_pinned_copy(tmp_path, which):
    run, rec = tmp_path / "plan_75_vault_run.out", tmp_path / "VAULT_RESULT.json"
    shutil.copy(NC.P75_RUN, run)
    shutil.copy(NC.P75_RECOMPUTE, rec)
    assert NC.plan75_card("GH/", run, rec)["numbers"]
    target = run if which == "run" else rec
    target.write_text(target.read_text().replace("PASS", "FAIL", 1))
    with pytest.raises(ValueError, match="pinned file differs"):
        NC.plan75_card("GH/", run, rec)


def test_plan75_missing_files_fall_back_quietly(tmp_path):
    c = NC.plan75_card("GH/", tmp_path / "nope.out", tmp_path / "nope.json")
    assert c["id"] == "plan75" and c["verdict"] == "Figures not on this computer" and c["numbers"] == [] and "bars" not in c
    assert [c["id"] for c in NC.cards("GH/")][:2] == ["plan76", "plan75"]


# ---- E10 forward log: shape from forward_e10.py publish, made-up logs only through its test helpers in a temp folder
def e10_log(tmp_path, days=4, block_at=None):
    from datetime import timedelta
    sys.path.insert(0, os.path.join(NC.ROOT, "practice"))
    import forward_e10 as fe
    import test_forward_e10 as helpers
    folder, out = tmp_path / "invented", tmp_path / "E10_log.json"
    fe.start(helpers.T - timedelta(days=1), folder, "invented")
    second = helpers.SecondVenue(block_at=block_at)
    for d in range(days):
        c = helpers.Clock(helpers.T + timedelta(days=d), 10)
        fe.record(c(), helpers.Venue(), folder, c, c.sleep, second_venue=second)
    fe.publish(folder, out)
    return out


def test_e10_card_is_stopped_and_shows_wakes_only(tmp_path):
    sys.path.insert(0, os.path.join(NC.ROOT, "practice"))
    import forward_e10 as fe
    empty = tmp_path / "E10_empty.json"
    fe.publish(tmp_path / "empty", empty)
    (tmp_path / "b").mkdir()
    for path, wakes in ((empty, "0"), (e10_log(tmp_path), "4"), (e10_log(tmp_path / "b", block_at=3), "4")):
        c = NC.e10_card("GH/", path)
        assert c["title"] == "E10: coin trend rule, stopped on data terms" and c["verdict"] == "Stopped, closed unjudged"
        assert all(w in c["summary"] for w in STOP_WORDS) and "Replaced by E13 on Binance.US data." in c["summary"]
        assert c["numbers"] == [["Wakes recorded before the stop", wakes]] and "columns" not in c
        assert not re.search(r"bp|cost|spread|fill|order|\$", json.dumps(c), re.I)
        assert [l[0] for l in c["links"]] == ["E10 card", "Log counts"]
    assert [x["id"] for x in NC.cards("GH/")][-7:] == ["e09", "e10", "e12", "e13", "m133", "m134", "e14"]
    assert "Standing chore" not in open(NC.__file__).read()


@pytest.mark.parametrize("change", ["drop", "extra", "text", "status", "costs"])
def test_e10_refuses_a_log_of_another_shape(tmp_path, change):
    path = e10_log(tmp_path)
    log = json.load(open(path))
    v = log["coinbase"]
    if change == "drop":
        del v["placeability"]["main"]["void_buys"]
    elif change == "extra":
        log["profit"] = 0.1
    elif change == "text":
        v["wakes"] = "4"
    elif change == "status":
        v["status"] = "RUNNING"
    else:
        v["all_in_cost_by_side"]["buy"]["n"] = 2
    path.write_text(json.dumps(log))
    with pytest.raises(ValueError, match="E10 card"):
        NC.e10_card("GH/", path)


RUNNING = {"e12": ("135", "230", "Judged at 150 trades or 2027-11-30."),
           "e13": ("136", "231", "Read once, a year after the first wake.")}


def test_running_cards_from_the_real_queue_and_ledger():
    got = {c["id"]: c for c in NC.cards("GH/")}
    for id_, (qrow, lrow, read_rule) in RUNNING.items():
        c = got[id_]
        assert c["verdict"] == "Running, no result yet" and c["tone"] == "info"
        assert c["numbers"] == [] and "columns" not in c and "bars" not in c
        assert "Running since 2026-11-26 5:39 PM MT" in c["summary"] and read_rule in c["summary"]
        assert c["summary"].endswith("No result exists yet, so no figure is shown.")
        assert f"row {qrow}" in c["basis"] and f"row {lrow}" in c["basis"]
        assert "Binance.US data only" in c["summary"] or "on Binance.US" in c["summary"]
        assert not re.search(r"\bbp\b|%|profit of|net ", c["summary"])
        assert c["links"][1] == ["Queue row", "GH/docs/QUEUE.md#running-now"]
        assert os.path.exists(os.path.join(NC.ROOT, c["links"][0][1][3:]))
    assert "at a pretend $250 a trade" in got["e12"]["summary"]
    assert "first daily wake 2026-11-27 5:00 PM MT" in got["e13"]["summary"]


def ledger_with(monkeypatch, row, old, new):
    text = NC.read(NC.LEDGER)
    assert old in text
    lines = [l.replace(old, new) if l.startswith(f"| {row} |") else l for l in text.splitlines()]
    real = NC.read
    monkeypatch.setattr(NC, "read", lambda path: "\n".join(lines) if path == NC.LEDGER else real(path))


@pytest.mark.parametrize("id_", list(RUNNING))
def test_running_cards_refuse_when_the_queue_row_changes(monkeypatch, id_):
    qrow = RUNNING[id_][0]
    step = NC.queue_step(qrow)
    queue_with(monkeypatch, qrow, step.replace("Running since", "Registered"))
    with pytest.raises(ValueError):
        getattr(NC, id_ + "_card")("GH/")


@pytest.mark.parametrize("id_", list(RUNNING))
def test_running_cards_refuse_without_a_start_go(monkeypatch, id_):
    lrow = RUNNING[id_][1]
    ledger_with(monkeypatch, lrow, "START GO (lead agent", "START HELD (lead agent")
    with pytest.raises(ValueError, match="no longer says running"):
        getattr(NC, id_ + "_card")("GH/")


@pytest.mark.parametrize("id_", list(RUNNING))
def test_running_cards_refuse_when_the_read_rule_changes(monkeypatch, id_):
    qrow, _, read_rule = RUNNING[id_]
    queue_with(monkeypatch, qrow, NC.queue_step(qrow).replace(read_rule, "Read whenever."))
    with pytest.raises(ValueError):
        getattr(NC, id_ + "_card")("GH/")


# ---- Plan 76 result card and E14, from the public summary and the queue and ledger rows
def test_plan76_card_reads_the_summary():
    f = json.loads(NC.read(NC.P76_SUMMARY))
    c = NC.plan76_card("GH/")
    assert c["verdict"] == "Did not pass" and c["tone"] == "fail"
    assert "All marks met at 15 bp a side, practice card E14 follows" in c["summary"] and "not a counted pass" in c["summary"]
    assert dict(c["numbers"])["Mean net a trade at 75 bp a side"] == NC.signed(f["lines"]["main"]["mean_net"])
    assert dict(c["numbers"])["Cost a side where the mean reaches zero"] == f"{f['break_even_bp']:.1f} bp"
    assert [r[1] for r in c["bars"]["rows"]] == [round(100 * v["cheap"], 2) for _, v in sorted(f["recompute"]["by_year"].items())]
    assert "INFERENCE" in c["summary"] and "SHIB" in c["summary"] and "blind recompute" in c["basis"]
    assert c["links"][0] == ["Plan 76 result", "GH/" + NC.D200]


def test_plan76_card_missing_and_refusal(tmp_path):
    c = NC.plan76_card("GH/", str(tmp_path / "nope.json"))
    assert c["verdict"] == "Figures not on this computer" and c["numbers"] == []
    f = json.loads(NC.read(NC.P76_SUMMARY))
    f["lines"]["main"]["met"] = 4
    bad = tmp_path / "s.json"
    bad.write_text(json.dumps(f))
    with pytest.raises(ValueError, match="Plan 76 card"):
        NC.plan76_card("GH/", str(bad))
    f = json.loads(NC.read(NC.P76_SUMMARY))
    f["recompute"] = None
    bad.write_text(json.dumps(f))
    c = NC.plan76_card("GH/", str(bad))
    assert c["summary"].endswith("Blind recompute: pending.") and "bars" not in c


def test_e14_card_running_with_no_figure(monkeypatch):
    c = NC.e14_card("GH/")
    assert c["verdict"] == "Running, no result yet" and c["tone"] == "info" and c["numbers"] == []
    assert "Running since 2026-11-26 6:20 PM MT" in c["summary"] and "60 trades or 2028-11-30" in c["summary"]
    assert "pretend $250" in c["summary"] and "11 coins" in c["summary"]
    assert c["summary"].endswith("No result exists yet, so no figure is shown.")
    queue_with(monkeypatch, "138", "Paused for a rebuild.")
    with pytest.raises(ValueError, match="E14 card"):
        NC.e14_card("GH/")


# ---- Measurement 133 stopped on a build fault; Measurement 134 registered, then running
def test_m133_stopped_card_reads_queue_and_ledger():
    c = NC.m133_card("GH/")
    assert c["verdict"] == "Stopped, closed unread" and c["tone"] == "unknown" and c["numbers"] == []
    assert "second wake, 2026-11-26 7:00 PM MT" in c["summary"] and "E12, held the shared request gate" in c["summary"]
    assert "One wake (6:00 PM MT) was recorded and nothing was read" in c["summary"] and "Measurement 134 (queue 139)" in c["summary"]
    assert not re.search(r"\$|%|\bbp\b|\d+ of \d+", c["summary"])
    assert NC.row_state(NC.queue_step("137")) == "Stopped 2026-11-26 7:00 PM MT"


@pytest.mark.parametrize("where", ["queue", "ledger", "time"])
def test_m133_card_refuses_when_rows_disagree(monkeypatch, where):
    if where == "queue":
        queue_with(monkeypatch, "137", "Running since 2026-11-26 5:39 PM MT (first hourly wake 6:00 PM MT). Read once at the end.")
    elif where == "ledger":
        ledger_with(monkeypatch, "232", "CLOSED UNREAD on a build fault", "RESTARTED after a build fault")
    else:
        queue_with(monkeypatch, "137", NC.queue_step("137").replace("7:00 PM MT", "8:00 PM MT"))
    with pytest.raises(ValueError, match="Measurement 133 card"):
        NC.m133_card("GH/")


def ledger_status(monkeypatch, row, status):
    """Replace the status cell of one ledger row, whatever it says now."""
    text = NC.read(NC.LEDGER)
    lines = [("|".join(l.split("|")[:-2] + [f" {status} ", ""]) if l.startswith(f"| {row} |") else l) for l in text.splitlines()]
    real = NC.read
    monkeypatch.setattr(NC, "read", lambda path: "\n".join(lines) if path == NC.LEDGER else real(path))


M134_REGISTERED = ("Registered 2026-11-26 7:09 PM MT, before any quote. Builder is repairing the Measurement 133 code; then tests, independent audit, start.",
                   "REGISTERED 2026-11-26 7:09 PM MT by the lead agent, before any quote and before any code change. Still to come: build, tests, audit, start.")
M134_RUNNING = ("Running since 2026-11-27 9:08 AM MT (first hourly wake 10:08 AM MT) from a frozen build. Read once at the end.",
                "REGISTERED 2026-11-26 7:09 PM MT by the lead agent. Audit CLEAR. START GO (lead agent, 2026-11-27 9:00 AM MT): `M134_START=abc1234`.")


def m134_rows(monkeypatch, state):
    step, status = state
    queue_with(monkeypatch, "139", step)
    ledger_status(monkeypatch, "234", status)


def test_m134_card_registered(monkeypatch):
    m134_rows(monkeypatch, M134_REGISTERED)
    c = NC.m134_card("GH/")
    assert c["verdict"] == "Registered, not started" and c["tone"] == "info" and c["numbers"] == []
    assert "Registered 2026-11-26 7:09 PM MT" in c["summary"] and "8 minutes after the hour" in c["summary"]
    assert "$25 and $250 on each of 20 coins" in c["summary"] and "720 hourly wakes" in c["summary"]
    assert c["summary"].endswith("No result exists yet, so no figure is shown.")


def test_m134_card_running(monkeypatch):
    m134_rows(monkeypatch, M134_RUNNING)
    c = NC.m134_card("GH/")
    assert c["verdict"] == "Running, no result yet" and c["tone"] == "info" and c["numbers"] == []
    assert "Running since 2026-11-27 9:08 AM MT; first hourly wake 10:08 AM MT" in c["summary"] and "Read once at the end." in c["summary"]
    assert not re.search(r"\bbp\b|%|profit of", c["summary"])


@pytest.mark.parametrize("step, status", [
    (M134_RUNNING[0], M134_REGISTERED[1]),                                   # queue says running, ledger has no start go
    (M134_RUNNING[0], M134_RUNNING[1].replace("M134_START", "M133_START")),  # start go for another measurement
    (M134_RUNNING[0], M134_RUNNING[1].replace("CLEAR", "NOT YET")),          # no audit CLEAR
    (M134_REGISTERED[0], M134_RUNNING[1]),                                   # ledger has started, queue still registered
    ("Paused for a rebuild.", M134_REGISTERED[1]),
])
def test_m134_card_refuses_rows_that_disagree(monkeypatch, step, status):
    m134_rows(monkeypatch, (step, status))
    with pytest.raises(ValueError, match="Measurement 134 card"):
        NC.m134_card("GH/")


def test_m134_card_from_the_live_rows():
    step = NC.queue_step("139")
    c = NC.m134_card("GH/")
    assert c["numbers"] == [] and c["tone"] == "info"
    if step.startswith("Running since "):
        assert c["verdict"] == "Running, no result yet" and NC.row_state(step) in c["summary"]
    else:
        assert c["verdict"] == "Registered, not started"


def research_listing(monkeypatch, keep_202, extra=()):
    real = NC.os.listdir
    def listing(d):
        names = real(d)
        if d.endswith("docs/research"):
            names = [n for n in names if keep_202 or not n.startswith("202_")] + list(extra)
        return names
    monkeypatch.setattr(NC.os, "listdir", listing)


def test_m134_links_the_ledger_until_a_202_plan_exists(monkeypatch):
    research_listing(monkeypatch, keep_202=False)
    assert NC.m134_card("GH/")["links"][0] == ["Trial ledger", "GH/" + NC.LEDGER]


def test_m134_links_the_one_202_plan(monkeypatch):
    research_listing(monkeypatch, keep_202=False, extra=["202_measurement_134_plan.md"])
    assert NC.m134_card("GH/")["links"][0] == ["Measurement 134 plan", "GH/docs/research/202_measurement_134_plan.md"]
    research_listing(monkeypatch, keep_202=False, extra=["202_a.md", "202_b.md"])
    with pytest.raises(ValueError, match="more than one"):
        NC.m134_card("GH/")


def test_m134_links_the_real_plan_when_it_is_there():
    plans = [n for n in os.listdir(os.path.join(NC.ROOT, "docs/research")) if n.startswith("202_") and n.endswith(".md")]
    link = NC.m134_card("GH/")["links"][0]
    assert link == (["Measurement 134 plan", "GH/docs/research/" + plans[0]] if plans else ["Trial ledger", "GH/" + NC.LEDGER])
