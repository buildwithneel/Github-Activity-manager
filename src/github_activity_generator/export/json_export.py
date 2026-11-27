"""JSON export functions without secrets."""

import json
from dataclasses import asdict
from pathlib import Path

from github_activity_generator.analyzer.activity import DayRecord
from github_activity_generator.analyzer.statistics import ActivityStatistics


def export_activity_json(
    records: list[DayRecord],
    stats: ActivityStatistics,
    output_path: Path,
    planned_counts: dict[str, int] | None = None,
) -> Path:
    """Export full activity analysis, statistics, and optional simulated plan as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    planned = planned_counts or {}

    payload = {
        "disclaimer": (
            "Existing GitHub contributions and simulated planned values are stored separately. "
            "A zero existing count means no qualifying contribution was returned by GitHub's API."
        ),
        "statistics": asdict(stats),
        "days": [
            {
                "date": r.date_str,
                "weekday": r.weekday_name,
                "existing_contributions": r.existing_count,
                "status": r.status.value,
                "protected": r.protected,
                "eligible": r.eligible,
                "simulated_planned_contributions": 0 if r.protected else planned.get(r.date_str, 0),
            }
            for r in records
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
