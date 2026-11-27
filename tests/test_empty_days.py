"""Tests for empty-day detection, protection rules, and statistics."""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.analyzer.activity import ActivityAnalyzer, DayStatus
from github_activity_generator.analyzer.empty_days import EmptyDayAnalyzer
from github_activity_generator.analyzer.statistics import compute_statistics


class TestEmptyDays(unittest.TestCase):
    def test_case_1_seven_empty_days(self) -> None:
        start = date(2025, 1, 6)  # Monday
        end = date(2025, 1, 12)  # Sunday
        records = ActivityAnalyzer.analyze({}, start, end)
        self.assertEqual(len(records), 7)
        self.assertEqual(sum(1 for r in records if r.eligible), 7)
        self.assertEqual(sum(1 for r in records if r.protected), 0)

    def test_case_2_one_contribution_six_empty(self) -> None:
        start = date(2025, 1, 6)
        end = date(2025, 1, 12)
        records = ActivityAnalyzer.analyze({"2025-01-08": 1}, start, end)
        protected = [r for r in records if r.protected]
        eligible = [r for r in records if r.eligible]
        self.assertEqual(len(protected), 1)
        self.assertEqual(protected[0].date_str, "2025-01-08")
        self.assertEqual(protected[0].status, DayStatus.ACTIVE)
        self.assertEqual(len(eligible), 6)

    def test_case_3_fifty_contributions_six_empty(self) -> None:
        start = date(2025, 1, 6)
        end = date(2025, 1, 12)
        records = ActivityAnalyzer.analyze({"2025-01-08": 50}, start, end)
        protected = [r for r in records if r.protected]
        eligible = [r for r in records if r.eligible]
        self.assertEqual(len(protected), 1)
        self.assertEqual(len(eligible), 6)

    def test_case_4_all_seven_active(self) -> None:
        start = date(2025, 1, 6)
        end = date(2025, 1, 12)
        counts = {f"2025-01-{day:02d}": day for day in range(6, 13)}
        records = ActivityAnalyzer.analyze(counts, start, end)
        self.assertEqual(sum(1 for r in records if r.protected), 7)
        self.assertEqual(sum(1 for r in records if r.eligible), 0)

    def test_empty_day_grouping_and_streaks(self) -> None:
        start = date(2025, 1, 30)
        end = date(2025, 2, 4)
        records = ActivityAnalyzer.analyze({"2025-02-01": 4}, start, end)
        report = EmptyDayAnalyzer.analyze(records)
        self.assertEqual(len(report.empty_days), 5)
        self.assertIn("2025-01", report.by_month)
        self.assertIn("2025-02", report.by_month)
        self.assertEqual(report.longest_inactive_streak, 3)

        stats = compute_statistics(records, planned_counts={"2025-01-30": 2})
        self.assertEqual(stats.existing_total_contributions, 4)
        self.assertEqual(stats.simulated_planned_total, 2)


if __name__ == "__main__":
    unittest.main()
