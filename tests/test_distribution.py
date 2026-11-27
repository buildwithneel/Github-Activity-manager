"""Tests for smart distribution engine, patterns, and impossible target detection."""

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.analyzer.activity import ActivityAnalyzer
from github_activity_generator.config import GenerationConfig
from github_activity_generator.exceptions import ImpossibleTargetError, ValidationError
from github_activity_generator.generator.distribution import DistributionEngine


class TestDistribution(unittest.TestCase):
    def test_distribution_respects_protected_and_exact_total(self) -> None:
        start = date(2025, 1, 1)
        end = date(2025, 1, 10)
        # 3 active days (protected), 7 empty days (eligible)
        existing = {"2025-01-02": 1, "2025-01-05": 25, "2025-01-09": 3}
        records = ActivityAnalyzer.analyze(existing, start, end)

        cfg = GenerationConfig(
            min_commits_per_day=1,
            max_commits_per_day=5,
            total_target=20,
            pattern="random",
            random_seed=123,
        )
        plan = DistributionEngine.distribute(records, cfg)

        self.assertEqual(len(plan.eligible_dates), 7)
        self.assertEqual(len(plan.protected_dates), 3)
        self.assertEqual(plan.total_planned, 20)
        for p_date in plan.protected_dates:
            self.assertEqual(plan.planned_counts[p_date], 0)

    def test_deterministic_random_seed(self) -> None:
        records = ActivityAnalyzer.analyze({}, date(2025, 2, 1), date(2025, 2, 14))
        cfg1 = GenerationConfig(min_commits_per_day=1, max_commits_per_day=8, pattern="random", random_seed=99)
        cfg2 = GenerationConfig(min_commits_per_day=1, max_commits_per_day=8, pattern="random", random_seed=99)
        plan1 = DistributionEngine.distribute(records, cfg1)
        plan2 = DistributionEngine.distribute(records, cfg2)
        self.assertEqual(plan1.planned_counts, plan2.planned_counts)

    def test_exact_daily_target_and_weekend_exclusion(self) -> None:
        # 2025-01-06 (Mon) .. 2025-01-12 (Sun) -> 5 weekdays
        records = ActivityAnalyzer.analyze({}, date(2025, 1, 6), date(2025, 1, 12))
        cfg = GenerationConfig(exact_daily_target=3, exclude_weekends=True)
        plan = DistributionEngine.distribute(records, cfg)
        self.assertEqual(len(plan.eligible_dates), 5)
        self.assertEqual(plan.total_planned, 15)
        self.assertEqual(plan.planned_counts["2025-01-11"], 0)
        self.assertEqual(plan.planned_counts["2025-01-12"], 0)

    def test_weekly_and_monthly_caps(self) -> None:
        records = ActivityAnalyzer.analyze({}, date(2025, 1, 6), date(2025, 1, 12))
        cfg = GenerationConfig(exact_daily_target=4, weekly_target=10)
        plan = DistributionEngine.distribute(records, cfg)
        self.assertEqual(plan.total_planned, 10)
        self.assertTrue(any("Weekly target cap" in w for w in plan.warnings))

    def test_impossible_targets_raise(self) -> None:
        records = ActivityAnalyzer.analyze({}, date(2025, 1, 1), date(2025, 1, 5))
        # Target exceeds max possible (5 * 2 = 10 < 50)
        with self.assertRaises(ImpossibleTargetError):
            DistributionEngine.distribute(
                records,
                GenerationConfig(min_commits_per_day=1, max_commits_per_day=2, total_target=50),
            )
        # All days protected -> 0 eligible dates
        all_active = ActivityAnalyzer.analyze(
            {f"2025-01-0{d}": 1 for d in range(1, 6)},
            date(2025, 1, 1),
            date(2025, 1, 5),
        )
        with self.assertRaises(ImpossibleTargetError):
            DistributionEngine.distribute(all_active, GenerationConfig(total_target=5))

        # Invalid min > max
        with self.assertRaises(ValidationError):
            DistributionEngine.distribute(
                records, GenerationConfig(min_commits_per_day=5, max_commits_per_day=2)
            )


if __name__ == "__main__":
    unittest.main()
