"""Core activity analysis and mandatory existing-activity protection engine."""

from dataclasses import dataclass
from datetime import date
from enum import Enum

from github_activity_generator.constants import WEEKDAY_NAMES
from github_activity_generator.github.contributions import iter_date_range


class DayStatus(str, Enum):
    """Classification of a calendar day."""

    ACTIVE = "ACTIVE"
    EMPTY = "EMPTY"
    EXCLUDED = "EXCLUDED"


@dataclass
class DayRecord:
    """Detailed analysis record for a single calendar date."""

    day: date
    date_str: str
    weekday: int
    weekday_name: str
    existing_count: int
    status: DayStatus
    protected: bool
    eligible: bool
    iso_year: int
    week_number: int
    month: int
    year: int


class ActivityAnalyzer:
    """Analyzes daily contributions and enforces the existing-activity protection rule."""

    @staticmethod
    def analyze(
        daily_counts: dict[str, int],
        start_date: date,
        end_date: date,
        excluded_dates: set[str] | None = None,
    ) -> list[DayRecord]:
        """Classify every date in [start_date, end_date] and mark protected/eligible dates."""
        excluded = excluded_dates or set()
        records: list[DayRecord] = []

        for current in iter_date_range(start_date, end_date):
            date_str = current.isoformat()
            existing = max(0, int(daily_counts.get(date_str, 0)))
            iso_year, iso_week, _ = current.isocalendar()

            # Mandatory Activity Protection Rule:
            # Any date with existing_contributions > 0 is ACTIVE, protected, and never eligible.
            if existing > 0:
                status = DayStatus.ACTIVE
                protected = True
                eligible = False
            elif date_str in excluded:
                status = DayStatus.EXCLUDED
                protected = False
                eligible = False
            else:
                status = DayStatus.EMPTY
                protected = False
                eligible = True

            records.append(
                DayRecord(
                    day=current,
                    date_str=date_str,
                    weekday=current.weekday(),
                    weekday_name=WEEKDAY_NAMES[current.weekday()],
                    existing_count=existing,
                    status=status,
                    protected=protected,
                    eligible=eligible,
                    iso_year=iso_year,
                    week_number=iso_week,
                    month=current.month,
                    year=current.year,
                )
            )

        return records
