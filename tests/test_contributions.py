"""Tests for multi-year contribution retrieval, leap years, and caching."""

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.exceptions import ValidationError
from github_activity_generator.github.contributions import (
    ContributionRetriever,
    iter_date_range,
    split_range_by_year,
)
from github_activity_generator.storage.database import ActivityDatabase


class TestContributions(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = ActivityDatabase(Path(self.tmp.name) / "activity.db")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_split_range_by_year_and_leap_year(self) -> None:
        start = date(2023, 12, 20)
        end = date(2024, 3, 5)
        chunks = split_range_by_year(start, end)
        self.assertEqual(
            chunks,
            [
                (date(2023, 12, 20), date(2023, 12, 31)),
                (date(2024, 1, 1), date(2024, 3, 5)),
            ],
        )
        all_days = iter_date_range(start, end)
        # 12 days in Dec 2023 + 31 (Jan) + 29 (Feb leap) + 5 (Mar) = 77 days
        self.assertEqual(len(all_days), 77)
        self.assertIn(date(2024, 2, 29), all_days)

    def test_invalid_date_range_raises(self) -> None:
        with self.assertRaises(ValidationError):
            iter_date_range(date(2025, 5, 10), date(2025, 5, 1))

    def test_multi_year_graphql_retrieval_and_caching(self) -> None:
        mock_client = MagicMock()
        mock_client.graphql.side_effect = [
            {
                "user": {
                    "contributionsCollection": {
                        "restrictedContributionsCount": 2,
                        "contributionCalendar": {
                            "totalContributions": 4,
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {"date": "2023-12-30", "contributionCount": 1},
                                        {"date": "2023-12-31", "contributionCount": 3},
                                    ]
                                }
                            ],
                        },
                    }
                }
            },
            {
                "user": {
                    "contributionsCollection": {
                        "restrictedContributionsCount": 1,
                        "contributionCalendar": {
                            "totalContributions": 5,
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {"date": "2024-02-29", "contributionCount": 5},
                                    ]
                                }
                            ],
                        },
                    }
                }
            },
        ]

        retriever = ContributionRetriever(mock_client, database=self.db)
        history = retriever.fetch_contributions(
            "octocat", date(2023, 12, 30), date(2024, 3, 1)
        )

        self.assertEqual(mock_client.graphql.call_count, 2)
        self.assertEqual(history.daily_counts["2023-12-31"], 3)
        self.assertEqual(history.daily_counts["2024-02-29"], 5)
        self.assertEqual(history.daily_counts["2024-01-01"], 0)
        self.assertEqual(history.total_contributions, 9)
        self.assertEqual(history.yearly_totals, {2023: 4, 2024: 5})
        self.assertEqual(history.restricted_contributions, 3)

        # Verify cache hit avoids another GraphQL call
        cached_history = retriever.fetch_contributions(
            "octocat", date(2023, 12, 30), date(2024, 3, 1), use_cache=True
        )
        self.assertEqual(mock_client.graphql.call_count, 2)
        self.assertEqual(cached_history.total_contributions, 9)


if __name__ == "__main__":
    unittest.main()
