"""Tests for empty-week detection, partially active weeks, and mid-week ranges."""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.analyzer.activity import ActivityAnalyzer
from github_activity_generator.analyzer.empty_weeks import EmptyWeekAnalyzer, WeekClassification


class TestEmptyWeeks(unittest.TestCase):
    def test_completely_empty_and_partially_active_weeks(self) -> None:
        # Week 1: Jan 6 - Jan 12 (completely empty)
        # Week 2: Jan 13 - Jan 19 (Wed Jan 15 has 2 contributions -> partially active, 6 eligible)
        # Week 3: Jan 20 - Jan 26 (all 7 days active -> fully active)
        start = date(2025, 1, 6)
        end = date(2025, 1, 26)
        counts = {"2025-01-15": 2}
        for d in range(20, 27):
            counts[f"2025-01-{d:02d}"] = 1

        records = ActivityAnalyzer.analyze(counts, start, end)
        report = EmptyWeekAnalyzer.analyze(records)

        self.assertEqual(len(report.completely_empty_weeks), 1)
        self.assertEqual(len(report.completely_empty_weeks[0].eligible_dates), 7)

        self.assertEqual(len(report.partially_active_weeks), 1)
        partial = report.partially_active_weeks[0]
        self.assertEqual(partial.classification, WeekClassification.PARTIALLY_ACTIVE)
        self.assertEqual(len(partial.eligible_dates), 6)
        self.assertNotIn(date(2025, 1, 15), partial.eligible_dates)

        self.assertEqual(len(report.fully_active_weeks), 1)

    def test_case_5_mid_week_start_and_end(self) -> None:
        # 2025-01-08 is Wednesday; 2025-01-10 is Friday (3 days only)
        start = date(2025, 1, 8)
        end = date(2025, 1, 10)
        records = ActivityAnalyzer.analyze({}, start, end)
        report = EmptyWeekAnalyzer.analyze(records)

        self.assertEqual(len(records), 3)
        self.assertEqual(len(report.weeks), 1)
        self.assertFalse(report.weeks[0].is_full_calendar_week)
        self.assertEqual(len(report.weeks[0].days), 3)
        self.assertEqual(len(report.completely_empty_weeks), 0)  # not a full 7-day calendar week


if __name__ == "__main__":
    unittest.main()
