"""Offline clock and stock census checks; no tape required."""
from datetime import datetime
import json
import unittest

from tools import tm09_stock_news_counts as census


def at(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=census.NY).timestamp())


class CensusTest(unittest.TestCase):
    def test_clock_tags_edited_rows_and_early_close(self):
        sessions, lines = [], []
        for day in ("2026-04-01", "2026-07-02", "2026-07-06", "2026-11-24"):
            close = "T13:00" if day == "2026-07-02" else "T16:00"
            sessions.append((day, at(day + "T09:30"), at(day + close)))
        for source, stamp, tags, lag in (
            ("alpaca", "2026-07-06T08:59", ["AAPL", "AAPL", "AMZN"], 0),
            ("sec_edgar", "2026-07-06T09:00", ["AAPL"], 0),
            ("sec_edgar", "2026-07-02T12:00", ["AAPL"], 0),
            ("alpaca", "2026-07-06T09:04", ["AAPL"], 1),
            ("finbold", "2026-07-06T09:04", ["AAPL"], 0),
            ("alpaca", "2026-11-24T15:15", ["AAPL"], 0),
        ):
            t = at(stamp)
            lines.append(json.dumps(dict(source=source, stated_time=t, updated_time=t + lag,
                                         edited_later=bool(lag), symbols=tags, headline="synthetic")))
        news = census.projected(lines, ("source", "stated_time", "updated_time", "edited_later", "symbols"))
        out = census.admitted_weekly(sessions, news)
        self.assertNotIn("synthetic", repr(out))
        aapl, amzn = (out["stock_order"].index(s) for s in ("AAPL", "AMZN"))
        wakes = dict(out["wakes_utc_first_admissions"])
        self.assertEqual(wakes[at("2026-07-06T10:00")], [[aapl, 1, 1], [amzn, 1, 0]])
        self.assertEqual(wakes[at("2026-07-06T12:30")], [[aapl, 0, 1]])
        self.assertNotIn(at("2026-07-02T15:30"), wakes)
        week = next(w for w in out["weeks"] if w["monday_ny"] == "2026-07-06")
        self.assertEqual(week["counts_by_stock"][aapl], [1, 2])
        self.assertEqual(week["distinct_tagged_items"], [1, 2])
        self.assertEqual(week["empty_stock_weeks"], 36)
        self.assertTrue(week["after_maker"])
        self.assertEqual(out["coverage"]["maker_full_stock_weeks"], 38)
        self.assertEqual(out["source_quality"]["alpaca"]["edited_later"], 1)
        self.assertEqual(out["source_quality"]["alpaca"]["after_final_wake"], 1)
        self.assertNotIn("finbold", out["source_quality"])


if __name__ == "__main__":
    unittest.main()
