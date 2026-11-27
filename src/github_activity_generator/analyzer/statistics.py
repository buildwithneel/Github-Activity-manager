"""Statistics and analytics engine separating existing vs simulated activity."""

from dataclasses import dataclass

from github_activity_generator.analyzer.activity import DayRecord, DayStatus
from github_activity_generator.analyzer.empty_days import EmptyDayAnalyzer
from github_activity_generator.analyzer.empty_weeks import EmptyWeekAnalyzer


@dataclass
class ActivityStatistics:
    """Comprehensive statistics for existing and (optionally) simulated activity."""

    total_days: int
    active_days: int
    empty_days: int
    excluded_days: int
    eligible_days: int
    existing_total_contributions: int
    average_daily_existing: float
    completely_empty_weeks: int
    partially_active_weeks: int
    fully_active_weeks: int
    longest_existing_active_streak: int
    longest_inactive_streak: int
    highest_existing_day: tuple[str, int] | None
    highest_existing_week: tuple[str, int] | None
    empty_months: list[str]
    yearly_existing_totals: dict[int, int]
    monthly_existing_totals: dict[str, int]
    simulated_planned_total: int = 0
    simulated_active_days: int = 0


def compute_statistics(
    records: list[DayRecord],
    planned_counts: dict[str, int] | None = None,
) -> ActivityStatistics:
    """Compute existing and simulated statistics without conflating the two."""
    empty_day_report = EmptyDayAnalyzer.analyze(records)
    empty_week_report = EmptyWeekAnalyzer.analyze(records)

    total_days = len(records)
    active_days = sum(1 for r in records if r.status == DayStatus.ACTIVE)
    empty_days = sum(1 for r in records if r.existing_count == 0)
    excluded_days = sum(1 for r in records if r.status == DayStatus.EXCLUDED)
    eligible_days = sum(1 for r in records if r.eligible)
    existing_total = sum(r.existing_count for r in records)
    avg_daily = round(existing_total / total_days, 2) if total_days > 0 else 0.0

    # Longest existing active streak
    longest_active = 0
    cur_active = 0
    for r in records:
        if r.existing_count > 0:
            cur_active += 1
            longest_active = max(longest_active, cur_active)
        else:
            cur_active = 0

    highest_day_rec = max(
        (r for r in records if r.existing_count > 0),
        key=lambda r: r.existing_count,
        default=None,
    )
    highest_day = (
        (highest_day_rec.date_str, highest_day_rec.existing_count)
        if highest_day_rec
        else None
    )

    highest_week_rec = max(
        (w for w in empty_week_report.weeks if w.total_contributions > 0),
        key=lambda w: w.total_contributions,
        default=None,
    )
    highest_week = (
        (
            f"{highest_week_rec.week_start.isoformat()}..{highest_week_rec.week_end.isoformat()}",
            highest_week_rec.total_contributions,
        )
        if highest_week_rec
        else None
    )

    yearly_totals: dict[int, int] = {}
    monthly_totals: dict[str, int] = {}
    for r in records:
        yearly_totals[r.year] = yearly_totals.get(r.year, 0) + r.existing_count
        m_key = f"{r.year:04d}-{r.month:02d}"
        monthly_totals[m_key] = monthly_totals.get(m_key, 0) + r.existing_count

    empty_months = sorted(m for m, total in monthly_totals.items() if total == 0)

    planned = planned_counts or {}
    sim_total = sum(v for v in planned.values() if v > 0)
    sim_days = sum(1 for v in planned.values() if v > 0)

    return ActivityStatistics(
        total_days=total_days,
        active_days=active_days,
        empty_days=empty_days,
        excluded_days=excluded_days,
        eligible_days=eligible_days,
        existing_total_contributions=existing_total,
        average_daily_existing=avg_daily,
        completely_empty_weeks=len(empty_week_report.completely_empty_weeks),
        partially_active_weeks=len(empty_week_report.partially_active_weeks),
        fully_active_weeks=len(empty_week_report.fully_active_weeks),
        longest_existing_active_streak=longest_active,
        longest_inactive_streak=empty_day_report.longest_inactive_streak,
        highest_existing_day=highest_day,
        highest_existing_week=highest_week,
        empty_months=empty_months,
        yearly_existing_totals=yearly_totals,
        monthly_existing_totals=monthly_totals,
        simulated_planned_total=sim_total,
        simulated_active_days=sim_days,
    )
