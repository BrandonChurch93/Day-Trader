import unittest

from research_rig.dashboard_status import parse_status, scoreboard, tm_hold, validate_status_runs


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

    def test_proxy_venue_pass_counts_with_qualified_reachability(self):
        row = ("| 3 | Plan 75 | Coin trend | momentum | Yes | Passed (4 of 4 marks) | "
               "Tested on a US venue proxy (`docs/research/181_plan_75_heldback_result.md`) |\n")
        inventory = INVENTORY.replace("## 2.", row + "## 2.").replace("| Total | 2 | 1 |", "| Total | 3 | 2 |")
        score = scoreboard(inventory, [], GH)
        self.assertEqual((score["tests"], score["passed"]), (3, 2))
        self.assertEqual(score["passes"][-1]["scope"], "US $500 reachable in principle; tested on a proxy feed")
        self.assertEqual(score["passes"][-1]["url"], GH + "docs/research/181_plan_75_heldback_result.md")

    def test_distinct_legs_share_the_run_clock_and_report_without_double_counting(self):
        extra = """- [Replay 46 Leg A](research/101_two_legs.md), run once 2026-11-26 06:51:58 UTC. Did not pass, 3 of 6 marks.
- [Replay 46 Leg B](research/101_two_legs.md), run once 2026-11-26 06:51:58 UTC. Did not pass, 5 of 6 marks.
- [Replay 46 Leg B](research/101_two_legs.md), run once 2026-11-26 06:51:58 UTC. Did not pass, 5 of 6 marks.
"""
        status = STATUS.replace("## Where things stand\n", "## Where things stand\n" + extra)
        findings = parse_status(status, GH)
        validate_status_runs(status, findings)
        score = scoreboard(INVENTORY, findings, GH)
        self.assertEqual((score["tests"], score["passed"], score["did_not_pass"]), (5, 1, 4))
        self.assertEqual([row["label"] for row in score["latest"][:2]], ["Replay 46 Leg A", "Replay 46 Leg B"])
        self.assertEqual([row["verdict"] for row in score["latest"][:2]],
                         ["Did not pass (3 of 6 marks)", "Did not pass (5 of 6 marks)"])


class TmHoldTests(unittest.TestCase):
    BULLET = ("- HOLD by the lead agent, 2026-11-26 4:54 PM MT: the time machine study TM07 stops after week 8 round one (ledger 198). "
              "Its price tape is Coinbase candles (STATED by the operator), and Coinbase's terms bar using its market data to "
              "benchmark an agent without written consent (MEASURED on its page). No round-two session is created.\n")

    def test_hold_note_in_plain_words(self):
        h = tm_hold("# Status\n## Latest results\n\n" + self.BULLET)
        self.assertEqual(h["id"], "TM07")
        self.assertIn("on hold after week 8, round one (since 2026-11-26 4:54 PM MT, ledger 198)", h["text"])
        self.assertIn("terms bar this use", h["text"])
        self.assertNotRegex(h["text"], r"\$|%|bp|gain|loss")

    def test_no_bullet_no_note_and_changed_bullet_refused(self):
        self.assertIsNone(tm_hold("# Status\n- Nothing on hold.\n"))
        with self.assertRaises(ValueError):
            tm_hold(self.BULLET.replace("Coinbase candles", "Kraken candles"))
