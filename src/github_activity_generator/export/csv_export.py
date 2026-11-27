"""CSV export functions for daily activity, empty days, empty weeks, and existing work."""

import csv
from pathlib import Path

from github_activity_generator.analyzer.activity import DayRecord, DayStatus
from github_activity_generator.analyzer.empty_days import EmptyDayReport
from github_activity_generator.analyzer.empty_weeks import EmptyWeekReport


def export_daily_csv(
    records: list[DayRecord],
    output_path: Path,
    planned_counts: dict[str, int] | None = None,
) -> Path:
    """Export daily activity records with separate existing and simulated columns."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    planned = planned_counts or {}
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "date",
                "weekday",
                "existing_contributions",
                "status",
                "protected",
                "eligible",
                "simulated_planned_contributions",
            ]
        )
        for rec in records:
            sim_val = 0 if rec.protected else planned.get(rec.date_str, 0)
            writer.writerow(
                [
                    rec.date_str,
                    rec.weekday_name,
                    rec.existing_count,
                    rec.status.value,
                    rec.protected,
                    rec.eligible,
                    sim_val,
                ]
            )
    return output_path


def export_empty_days_csv(report: EmptyDayReport, output_path: Path) -> Path:
    """Export all zero-contribution days."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "weekday", "year", "month", "is_weekend", "status"])
        for rec in report.empty_days:
            writer.writerow(
                [
                    rec.date_str,
                    rec.weekday_name,
                    rec.year,
                    f"{rec.year:04d}-{rec.month:02d}",
                    rec.weekday >= 5,
                    rec.status.value,
                ]
            )
    return output_path


def export_empty_weeks_csv(report: EmptyWeekReport, output_path: Path) -> Path:
    """Export week-level gap analysis."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "iso_year",
                "iso_week",
                "week_start",
                "week_end",
                "is_full_calendar_week",
                "classification",
                "active_days",
                "empty_days",
                "eligible_days",
                "existing_contributions",
            ]
        )
        for w in report.weeks:
            writer.writerow(
                [
                    w.iso_year,
                    w.iso_week,
                    w.week_start.isoformat(),
                    w.week_end.isoformat(),
                    w.is_full_calendar_week,
                    w.classification.value,
                    w.active_count,
                    w.empty_count,
                    len(w.eligible_dates),
                    w.total_contributions,
                ]
            )
    return output_path


def export_existing_work_csv(records: list[DayRecord], output_path: Path) -> Path:
    """Export only protected days with existing GitHub contributions."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "weekday", "existing_contributions", "protected"])
        for rec in records:
            if rec.status == DayStatus.ACTIVE:
                writer.writerow([rec.date_str, rec.weekday_name, rec.existing_count, rec.protected])
    return output_path
