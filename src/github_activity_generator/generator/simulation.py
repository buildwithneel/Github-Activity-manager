"""Activity simulation engine (strictly independent of real Git operations)."""

from dataclasses import dataclass

from github_activity_generator.analyzer.activity import DayRecord


@dataclass
class SimulationDay:
    """Single day in a simulated contribution graph."""

    date_str: str
    weekday: int
    existing_count: int
    planned_count: int
    combined_simulated_count: int
    intensity_level: int
    is_protected: bool
    is_simulated: bool


@dataclass
class SimulationResult:
    """Before-and-after simulation summary (clearly labeled as simulated)."""

    days: list[SimulationDay]
    existing_total: int
    planned_total: int
    simulated_combined_total: int
    before_active_days: int
    after_simulated_active_days: int


def compute_intensity_level(count: int, max_count: int) -> int:
    """Map a contribution count to GitHub-style intensity level 0..4."""
    if count <= 0:
        return 0
    if max_count <= 1:
        return 4
    ratio = count / max_count
    if ratio <= 0.25:
        return 1
    if ratio <= 0.50:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


class SimulationEngine:
    """Combines existing contributions and planned distribution for preview only."""

    @staticmethod
    def simulate(
        records: list[DayRecord],
        planned_counts: dict[str, int],
    ) -> SimulationResult:
        combined_values = [
            r.existing_count + planned_counts.get(r.date_str, 0) for r in records
        ]
        max_count = max(combined_values, default=0)

        sim_days: list[SimulationDay] = []
        existing_total = 0
        planned_total = 0
        before_active = 0
        after_active = 0

        for rec in records:
            existing = rec.existing_count
            planned = 0 if rec.protected else max(0, planned_counts.get(rec.date_str, 0))
            combined = existing + planned

            existing_total += existing
            planned_total += planned
            if existing > 0:
                before_active += 1
            if combined > 0:
                after_active += 1

            sim_days.append(
                SimulationDay(
                    date_str=rec.date_str,
                    weekday=rec.weekday,
                    existing_count=existing,
                    planned_count=planned,
                    combined_simulated_count=combined,
                    intensity_level=compute_intensity_level(combined, max_count),
                    is_protected=rec.protected,
                    is_simulated=planned > 0,
                )
            )

        return SimulationResult(
            days=sim_days,
            existing_total=existing_total,
            planned_total=planned_total,
            simulated_combined_total=existing_total + planned_total,
            before_active_days=before_active,
            after_simulated_active_days=after_active,
        )
