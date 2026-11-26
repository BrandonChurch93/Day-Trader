import unittest

from research_rig.dashboard_status import parse_status, scoreboard, validate_status_runs


GH = "https://example.test/blob/main/"
STATUS = """# Status
## Where things stand

- Plan 45 closed 2026-11-26, dropped at feasibility.
- [Replay 21](research/97_latest.md), run once 2026-11-26 05:52:52 UTC.
  MEASURED. Did not pass, 4 of 6 marks.
- [Replay 41](research/92_previous.md), run once 2026-11-26 05:33:58 UTC. Did not pass.
- [Replay 01](research/old.md), run once 2026-11-25 02:00 UTC. Did not pass.
- An outside study ([paper](https://example.org/paper.pdf)).

## Every test so far
| This table is not a STATUS bullet | run once |

## What is believed now

- Treasury funds at month-end: MEASURED 2026-11-26 04:51:41 UTC (""" + chr(96) + """docs/research/82_check.md""" + chr(96) + """).
- No real trades.
"""

INVENTORY = """## 1. Test inventory
| 1 | Replay 25 | TLT month-end | flow | Yes | PASSED (9/9) | \x60docs/research/pass.md\x60 |
| 2 | Replay 41 | Switch | flow | Yes | Failed (4/8) | \x60docs/research/92_previous.md\x60 |
## 2. Count by Family
| Total | 2 | 1 | Counted passes only |
"""


class DashboardStatusTests(unittest.TestCase):
    def test_both_sections_links_and_newest_first(self):
        findings = parse_status(STATUS, GH)
        validate_status_runs(STATUS, findings)
        self.assertEqual(findings[0]["lead"], "Replay 21")
        self.assertEqual(findings[0]["utc"], "2026-11-26 05:52:52")
        self.assertIn("Did not pass", findings[0]["body"])
        self.assertEqual(findings[0]["links"], [["Replay 21", GH + "docs/research/97_latest.md"]])
        self.assertEqual(findings[2]["lead"], "Treasury funds at month-end")
        self.assertEqual(findings[2]["links"], [["82_check.md", GH + "docs/research/82_check.md"]])
        self.assertEqual(findings[3]["lead"], "Plan 45 closed 2026-11-26, dropped at feasibility")
        self.assertEqual(findings[3]["links"][0][1], GH + "docs/STATUS.md#where-things-stand")
        self.assertIn([["paper", "https://example.org/paper.pdf"]], [item["links"] for item in findings])
        self.assertEqual(len(findings), 7)

    def test_run_once_missing_from_export_fails(self):
        findings = parse_status(STATUS, GH)
        with self.assertRaisesRegex(ValueError, "Replay 21"):
            validate_status_runs(STATUS, findings[1:])
        malformed = STATUS.replace("- [Replay 21]", "1. [Replay 21]")
        with self.assertRaisesRegex(ValueError, "run once.*was not exported"):
            validate_status_runs(malformed, parse_status(malformed, GH))

    def test_scoreboard_extends_inventory_without_double_counting(self):
        score = scoreboard(INVENTORY, parse_status(STATUS, GH), GH)
        self.assertEqual((score["tests"], score["passed"], score["did_not_pass"]), (3, 1, 2))
        self.assertEqual([row["label"] for row in score["latest"]], ["Replay 21", "Replay 41", "Replay 25"])
        self.assertEqual(score["latest"][0]["verdict"], "Did not pass (4 of 6 marks)")
        self.assertEqual(score["passes"][0]["url"], GH + "docs/research/pass.md")

    def test_inconsistent_inventory_fails(self):
        with self.assertRaisesRegex(ValueError, "family totals disagree"):
            scoreboard(INVENTORY.replace("| Total | 2", "| Total | 9"), [], GH)
