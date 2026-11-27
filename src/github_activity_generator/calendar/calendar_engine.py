"""Calendar grid construction for GitHub-style Sunday-to-Saturday visualization."""

from dataclasses import dataclass
from datetime import date, timedelta

from github_activity_generator.generator.simulation import SimulationDay


@dataclass
class YearCalendarGrid:
    """7-row (Sun..Sat) x N-week grid for a single calendar year."""

    year: int
    weeks: list[list[SimulationDay | None]]  # weeks[col][row 0..6] (0=Sun..6=Sat)
    month_positions: list[tuple[int, str]]


class CalendarEngine:
    """Builds GitHub-style contribution calendar matrices and date lookup."""

    @staticmethod
    def build_year_grids(days: list[SimulationDay]) -> list[YearCalendarGrid]:
        by_year: dict[int, dict[str, SimulationDay]] = {}
        for d in days:
            year = int(d.date_str[:4])
            by_year.setdefault(year, {})[d.date_str] = d

        grids: list[YearCalendarGrid] = []
        for year in sorted(by_year.keys()):
            day_map = by_year[year]
            jan1 = date(year, 1, 1)
            dec31 = date(year, 12, 31)

            # GitHub calendar rows: 0=Sunday .. 6=Saturday
            # Python weekday(): 0=Monday .. 6=Sunday => (weekday + 1) % 7 gives Sun=0..Sat=6
            start_offset = (jan1.weekday() + 1) % 7
            grid_start = jan1 - timedelta(days=start_offset)

            weeks: list[list[SimulationDay | None]] = []
            month_positions: list[tuple[int, str]] = []
            seen_months: set[int] = set()

            cursor = grid_start
            col = 0
            while cursor <= dec31:
                week_col: list[SimulationDay | None] = []
                for _row in range(7):
                    if jan1 <= cursor <= dec31:
                        if cursor.month not in seen_months and cursor.day <= 7:
                            seen_months.add(cursor.month)
                            month_positions.append((col, cursor.strftime("%b")))
                        week_col.append(day_map.get(cursor.isoformat()))
                    else:
                        week_col.append(None)
                    cursor += timedelta(days=1)
                weeks.append(week_col)
                col += 1

            grids.append(
                YearCalendarGrid(
                    year=year,
                    weeks=weeks,
                    month_positions=month_positions,
                )
            )
        return grids

    @staticmethod
    def inspect_date(days: list[SimulationDay], target_date: str) -> SimulationDay | None:
        """Return the SimulationDay record for a specific YYYY-MM-DD date."""
        for d in days:
            if d.date_str == target_date:
                return d
        return None
