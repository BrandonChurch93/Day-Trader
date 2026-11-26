"""Checks for the newest screen cards (newest_cards.py): figures read from the pinned summary files, refusals when the
files stop fitting, the E09 "no signal yet" case, and the Running now strip. Run: python3 -m pytest research_rig/test_newest_cards.py"""
import json, os, shutil, sys
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


def test_e09_card_and_no_log(monkeypatch, tmp_path):
    c = NC.e09_card("GH/")
    assert "No profit figure before 150 judged trades or 2027-11-30." in c["summary"]
    assert "Live since 2026-11-26 07:20 MT" in c["summary"]
    monkeypatch.setattr(NC, "E09_LOG", str(tmp_path / "absent.json"))
    c = NC.e09_card("GH/")
    assert c["verdict"] == "No signal yet" and c["numbers"] == [] and "No signal yet." in c["summary"]


def test_e09_counts_from_log(monkeypatch, tmp_path):
    log = json.load(open(os.path.join(NC.ROOT, "practice/forward/E09_log.json")))
    log.update(started=True, recorded=7, written_utc="2026-12-01T20:05:00Z")
    log["arms"]["70-102"].update(signals=2, trades_closed=1, trades_judged_ok=1)
    log["arms"]["71-013"]["signals"] = 3
    p = tmp_path / "E09_log.json"; p.write_text(json.dumps(log))
    monkeypatch.setattr(NC, "E09_LOG", str(p))
    c = NC.e09_card("GH/"); rows = dict(c["numbers"])
    assert c["verdict"] == "Running"
    assert rows["Wake-ups recorded"] == "7" and rows["Signals, rule 70-102"] == "2"
    assert rows["Signals, the two shown rules (71-013, 71-035)"] == "3"
    assert rows["Judged trades, rule 70-102 (of 150 needed)"] == "1"
    assert rows["Counts written"] == "2026-12-01 13:05 MT"


def test_running_now_strip(monkeypatch):
    rows = NC.running_now()
    assert rows and all(len(r) == 2 and r[1].endswith((".", ".)")) for r in rows)
    assert ["9b", "The earnings release reader."] in rows
    assert all("`" not in r[1] and "](" not in r[1] for r in rows)
    text = ("# Q\n## Running now\n\nNote.\n\n| # | What | Inputs | Step |\n|---|---|---|---|\n"
            "| 7 | Plan 9 (`docs/x.md`). Second sentence. | a | b |\n| - | Et al. style, Smith et al. 2020 found it. More. | a | b |\n## Done\n")
    monkeypatch.setattr(NC, "read", lambda path: text if path == NC.QUEUE else open(os.path.join(NC.ROOT, path)).read())
    assert NC.running_now() == [["7", "Plan 9."], ["-", "Et al. style, Smith et al. 2020 found it."]]
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
    assert NC.cards("GH/")[0]["id"] == "plan75"
