"""Checks for the newest screen cards (newest_cards.py): figures read from the pinned summary files, refusals when the
files stop fitting, the E09 "no signal yet" case, and the Running now strip. Run: python3 -m pytest research_rig/test_newest_cards.py"""
import json, os, shutil, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import newest_cards as NC
import build_doc152_plan70_search as B152

HAVE = os.path.isdir(os.path.join(str(B152.CUSTODY), "sweep_70")) and os.path.isdir(os.path.join(str(B152.CUSTODY), "plan73"))
need_custody = pytest.mark.skipif(not HAVE, reason="the summary files are kept off the repo")


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
