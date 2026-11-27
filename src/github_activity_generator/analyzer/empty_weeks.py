"""Empty-week and partially-active-week detection."""

from dataclasses import dataclass
from datetime import date
from enum import Enum

from github_activity_generator.analyzer.activity import DayRecord, DayStatus


class WeekClassification(str, Enum):
    """Classification of a calendar week within the selected range."""

    COMPLETELY_EMPTY = "COMPLETELY_EMPTY"
    PARTIALLY_ACTIVE = "PARTIALLY_ACTIVE"
    FULLY_ACTIVE = "FULLY_ACTIVE"
    HAS_EXCLUDED = "HAS_EXCLUDED"


@dataclass
class WeekRecord:
    """Analysis of a single calendar week (or partial boundary week)."""

    week_start: date
    week_end: date
    iso_year: int
    iso_week: int
    days: list[DayRecord]
    is_full_calendar_week: bool
    classification: WeekClassification
    active_count: int
    empty_count: int
    excluded_count: int
    total_contributions: int
    eligible_dates: list[date]


@dataclass
class EmptyWeekReport:
    """Summary of week-level gap analysis."""

    weeks: list[WeekRecord]
    completely_empty_weeks: list[WeekRecord]
    partially_active_weeks: list[WeekRecord]
    fully_active_weeks: list[WeekRecord]
    weeks_with_excluded: list[WeekRecord]


class EmptyWeekAnalyzer:
    """Groups DayRecords into calendar weeks (Mon-Sun) and classifies each week."""

    @staticmethod
    def analyze(records: list[DayRecord]) -> EmptyWeekReport:
        grouped: dict[tuple[int, int], list[DayRecord]] = {}
        for rec in records:
            grouped.setdefault((rec.iso_year, rec.week_number), []).append(rec)

        weeks: list[WeekRecord] = []
        completely_empty: list[WeekRecord] = []
        partially_active: list[WeekRecord] = []
        fully_active: list[WeekRecord] = []
        with_excluded: list[WeekRecord] = []

        for (iso_year, iso_week), days in sorted(grouped.items()):
            days_sorted = sorted(days, key=lambda d: d.day)
            active_count = sum(1 for d in days_sorted if d.status == DayStatus.ACTIVE)
            empty_count = sum(1 for d in days_sorted if d.status == DayStatus.EMPTY)
            excluded_count = sum(1 for d in days_sorted if d.status == DayStatus.EXCLUDED)
            total_contrib = sum(d.existing_count for d in days_sorted)
            eligible_dates = [d.day for d in days_sorted if d.eligible]
            is_full = len(days_sorted) == 7

            if excluded_count > 0:
                classification = WeekClassification.HAS_EXCLUDED
            elif is_full and active_count == 0:
                classification = WeekClassification.COMPLETELY_EMPTY
            elif active_count == len(days_sorted):
                classification = WeekClassification.FULLY_ACTIVE
            elif active_count == 0:
                # Partial boundary week with 0 contributions
                classification = WeekClassification.COMPLETELY_EMPTY
            else:
                classification = WeekClassification.PARTIALLY_ACTIVE

            week_rec = WeekRecord(
                week_start=days_sorted[0].day,
                week_end=days_sorted[-1].day,
                iso_year=iso_year,
                iso_week=iso_week,
                days=days_sorted,
                is_full_calendar_week=is_full,
                classification=classification,
                active_count=active_count,
                empty_count=empty_count,
                excluded_count=excluded_count,
                total_contributions=total_contrib,
                eligible_dates=eligible_dates,
            )
            weeks.append(week_rec)

            if classification == WeekClassification.COMPLETELY_EMPTY and is_full:
                completely_empty.append(week_rec)
            elif classification == WeekClassification.PARTIALLY_ACTIVE:
                partially_active.append(week_rec)
            elif classification == WeekClassification.FULLY_ACTIVE:
                fully_active.append(week_rec)
            if excluded_count > 0:
                with_excluded.append(week_rec)

        return EmptyWeekReport(
            weeks=weeks,
            completely_empty_weeks=completely_empty,
            partially_active_weeks=partially_active,
            fully_active_weeks=fully_active,
            weeks_with_excluded=with_excluded,
        )
