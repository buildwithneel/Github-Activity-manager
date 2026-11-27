"""Empty-day detection and gap analysis."""

from dataclasses import dataclass

from github_activity_generator.analyzer.activity import DayRecord, DayStatus


@dataclass
class EmptyDayReport:
    """Structured report of all zero-contribution days in a range."""

    empty_days: list[DayRecord]
    by_month: dict[str, list[DayRecord]]
    by_year: dict[int, list[DayRecord]]
    weekday_gaps: list[DayRecord]
    weekend_gaps: list[DayRecord]
    consecutive_streaks: list[list[DayRecord]]
    longest_inactive_streak: int


class EmptyDayAnalyzer:
    """Detects and groups empty (zero-contribution) days."""

    @staticmethod
    def analyze(records: list[DayRecord]) -> EmptyDayReport:
        empty_days = [r for r in records if r.existing_count == 0 and r.status != DayStatus.ACTIVE]
        by_month: dict[str, list[DayRecord]] = {}
        by_year: dict[int, list[DayRecord]] = {}
        weekday_gaps: list[DayRecord] = []
        weekend_gaps: list[DayRecord] = []

        for rec in empty_days:
            month_key = f"{rec.year:04d}-{rec.month:02d}"
            by_month.setdefault(month_key, []).append(rec)
            by_year.setdefault(rec.year, []).append(rec)
            if rec.weekday < 5:
                weekday_gaps.append(rec)
            else:
                weekend_gaps.append(rec)

        streaks: list[list[DayRecord]] = []
        current_streak: list[DayRecord] = []
        for rec in records:
            if rec.existing_count == 0:
                current_streak.append(rec)
            elif current_streak:
                streaks.append(current_streak)
                current_streak = []
        if current_streak:
            streaks.append(current_streak)

        longest = max((len(s) for s in streaks), default=0)

        return EmptyDayReport(
            empty_days=empty_days,
            by_month=by_month,
            by_year=by_year,
            weekday_gaps=weekday_gaps,
            weekend_gaps=weekend_gaps,
            consecutive_streaks=streaks,
            longest_inactive_streak=longest,
        )
