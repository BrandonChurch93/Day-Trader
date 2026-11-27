"""Tests for report_76.py: the Plan 76 page and summary. Read-only on the custody files; never runs the scorer."""
import json
import os
import pathlib
import re
import shutil

import pytest

import report_76 as R

CUSTODY = pathlib.Path(R.cfg()["custody"]["root"])
HAVE = all((CUSTODY / s / "result.json").is_file() for s in R.STAGES)
HAVE_REC = R.RECOMPUTE.is_file()
need = pytest.mark.skipif(not HAVE, reason="Plan 76 stage results are not on this computer")
need_rec = pytest.mark.skipif(not (HAVE and HAVE_REC), reason="Plan 76 recompute report is not on this computer")


def tmp_root(tmp_path):
    for d in ("docs/research", "research_rig"):
        (tmp_path / d).mkdir(parents=True)
    return tmp_path


def copy_custody(tmp_path):
    dst = tmp_path / "custody"
    for s in R.STAGES:
        (dst / s).mkdir(parents=True)
        shutil.copyfile(CUSTODY / s / "result.json", dst / s / "result.json")
    return dst


def test_break_even_arithmetic():
    for bp in (0, 15, 75, 92.9, 150):
        assert abs(R.break_even_bp(R.gross_from(0.0, bp)) - bp) < 1e-9
    assert abs((1 + R.gross_from(0.01, 75)) * R.keep(75) - 1 - 0.01) < 1e-15


def test_absent_files_leave_outputs_untouched(tmp_path, capsys):
    root = tmp_root(tmp_path)
    (root / R.PAGE).write_text("kept")
    (root / R.SUMMARY).write_text("kept")
    assert R.main(custody=tmp_path / "empty", root=root) == 0
    assert (root / R.PAGE).read_text() == "kept" and (root / R.SUMMARY).read_text() == "kept"
    assert "left as they are" in capsys.readouterr().out


@need_rec
def test_committed_outputs_match_a_fresh_build(tmp_path):
    root = tmp_root(tmp_path)
    R.main(custody=CUSTODY, root=root)
    for rel in (R.PAGE, R.SUMMARY):
        assert (root / rel).read_text() == (R.ROOT / rel).read_text(), rel


@need_rec
def test_page_order_and_figures():
    page = R.text(R.PAGE)
    lines = page.splitlines()
    assert lines[2].startswith("- MEASURED: did not pass.") and "closest miss" in lines[3]
    heads = [l for l in lines if l.startswith("## ")]
    assert heads == ["## Where the result comes from", "## The rule in plain words", "## The held-back figures",
                     "## What cost the rule can stand", "## Shown only, these decide nothing", "## The two earlier stages",
                     "## Limits", "## What happens next"]
    assert "2024 +3.71% (42 trades); 2025 -0.44% (25 trades); 2026 -0.91% (16 trades)" in page
    assert "(AAVE, SHIB, HBAR, LINK) carry 54 of the 83 signals and average +2.90%" in page
    assert "reaches zero at 92.9 bp a side" in page and "XRP position, entered 2020-12-28 23:00 UTC and sold 2023-07-14 00:00 UTC" in page
    assert "Blind recompute: done" in page and R.BITSTAMP_API in page
    assert "\u2014" not in page and "*" not in page.replace("**", "")
    s = json.loads(R.text(R.SUMMARY))
    assert not re.search(r"price|open|close|bars_file", json.dumps(list(s)), re.I)
    assert s["tests_scored"] == 46 and s["passes_counted"] == 4


@need
def test_without_recompute_the_line_is_pending(tmp_path):
    root = tmp_root(tmp_path)
    f = R.figures(R.load_results(CUSTODY), R.load_recompute(tmp_path / "none.md"))
    page = R.page(f)
    assert "- Blind recompute: pending." in page and "## Where the result comes from" not in page


@need
def test_a_changed_result_file_is_refused(tmp_path):
    dst = copy_custody(tmp_path)
    p = dst / "heldback" / "result.json"
    p.write_text(p.read_text().replace('"trades": 83', '"trades": 84', 1))
    with pytest.raises(ValueError, match="does not match the hash"):
        R.load_results(dst)


@need_rec
def test_a_changed_recompute_report_is_refused(tmp_path):
    p = tmp_path / "rec.md"
    p.write_text(R.RECOMPUTE.read_text().replace("SHIB: 11, +8.19%", "SHIB: 11, +9.19%"))
    with pytest.raises(ValueError, match="does not match its pin"):
        R.load_recompute(p)


@need_rec
@pytest.mark.parametrize("change", ["year", "coin", "thin", "headline"])
def test_recompute_breakdowns_must_add_back(change):
    res = R.load_results(CUSTODY)
    rec = R.load_recompute()
    if change == "year":
        rec["by_year"]["2024"] = (42, 0.0471)
    elif change == "coin":
        rec["by_coin"]["ADA"] = (10, -0.0350)
    elif change == "thin":
        rec["thin"]["rest_cheap"] = -0.0189
    else:
        rec["line"]["75"]["trimmed"] = 0.001
    with pytest.raises(ValueError, match="Plan 76 report"):
        R.figures(res, rec)


@need_rec
def test_scorecard_row_46_matches_the_summary():
    s = json.loads(R.text(R.SUMMARY))
    row = [l for l in R.text(R.SCORECARD).splitlines() if l.startswith("| 46 | Plan 76 |")]
    assert len(row) == 1
    m, ch = s["lines"]["main"], s["lines"]["cheap"]
    assert f"Did not pass ({m['met']} of 4 marks)" in row[0]
    assert f"At {m['bp']} bp a side {R.pct(m['mean_net'])} net a trade over {m['trades']} trades, {R.pct(m['trimmed'])} without each year's best" in row[0]
    assert f"at {ch['bp']} bp a side ({R.pct(ch['mean_net'])})" in row[0]
