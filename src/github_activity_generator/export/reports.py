"""Human-readable text report generators."""

from pathlib import Path

from github_activity_generator.analyzer.activity import DayRecord, DayStatus
from github_activity_generator.analyzer.empty_days import EmptyDayReport
from github_activity_generator.analyzer.empty_weeks import EmptyWeekReport
from github_activity_generator.analyzer.statistics import ActivityStatistics


def export_text_report(
    stats: ActivityStatistics,
    empty_days: EmptyDayReport,
    empty_weeks: EmptyWeekReport,
    output_path: Path,
) -> Path:
    """Write a comprehensive plain-text summary report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "GITHUB ACTIVITY GENERATOR - SUMMARY REPORT",
        "=" * 48,
        f"Total days analyzed:           {stats.total_days}",
        f"Active days (protected):       {stats.active_days}",
        f"Empty days:                    {stats.empty_days}",
        f"Excluded days:                 {stats.excluded_days}",
        f"Eligible days for planning:    {stats.eligible_days}",
        f"Existing GitHub contributions: {stats.existing_total_contributions}",
        f"Average daily existing:        {stats.average_daily_existing}",
        f"Longest existing active streak:{stats.longest_existing_active_streak} day(s)",
        f"Longest inactive streak:       {stats.longest_inactive_streak} day(s)",
        f"Completely empty weeks:        {len(empty_weeks.completely_empty_weeks)}",
        f"Partially active weeks:        {len(empty_weeks.partially_active_weeks)}",
        f"Fully active weeks:            {len(empty_weeks.fully_active_weeks)}",
        f"Simulated planned total:       {stats.simulated_planned_total} (simulated only)",
        f"Simulated new active days:     {stats.simulated_active_days}",
        "",
        "Yearly Existing Totals:",
    ]
    for year, total in sorted(stats.yearly_existing_totals.items()):
        lines.append(f"  {year}: {total}")

    if stats.empty_months:
        lines.append("")
        lines.append("Empty Months: " + ", ".join(stats.empty_months))

    lines.append("")
    lines.append(f"Total weekday gaps: {len(empty_days.weekday_gaps)}")
    lines.append(f"Total weekend gaps: {len(empty_days.weekend_gaps)}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def export_empty_day_report(report: EmptyDayReport, output_path: Path) -> Path:
    """Write a dedicated empty-day report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EMPTY DAY REPORT",
        "=" * 40,
        f"Total empty days: {len(report.empty_days)}",
        f"Longest inactive streak: {report.longest_inactive_streak} day(s)",
        "",
        "Dates:",
    ]
    for rec in report.empty_days:
        lines.append(f"  {rec.date_str} ({rec.weekday_name})")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def export_empty_week_report(report: EmptyWeekReport, output_path: Path) -> Path:
    """Write a dedicated empty-week and partially-active-week report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EMPTY & PARTIAL WEEK REPORT",
        "=" * 40,
        f"Completely empty weeks: {len(report.completely_empty_weeks)}",
        f"Partially active weeks: {len(report.partially_active_weeks)}",
        f"Fully active weeks:     {len(report.fully_active_weeks)}",
        "",
        "Completely Empty Weeks:",
    ]
    for w in report.completely_empty_weeks:
        lines.append(f"  {w.iso_year}-W{w.iso_week:02d}: {w.week_start} .. {w.week_end}")
    lines.append("")
    lines.append("Partially Active Weeks (eligible dates preserved):")
    for w in report.partially_active_weeks:
        lines.append(
            f"  {w.iso_year}-W{w.iso_week:02d}: {w.week_start} .. {w.week_end} "
            f"(active={w.active_count}, eligible={len(w.eligible_dates)})"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def export_existing_work_report(records: list[DayRecord], output_path: Path) -> Path:
    """Write a report of all protected days with existing contributions."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    active = [r for r in records if r.status == DayStatus.ACTIVE]
    lines = [
        "EXISTING WORK DAY REPORT (PROTECTED DATES)",
        "=" * 48,
        f"Total protected active days: {len(active)}",
        "",
    ]
    for r in active:
        lines.append(f"  {r.date_str} ({r.weekday_name}): {r.existing_count} contribution(s)")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
