"""Tests for simulation engine, calendar grid, and terminal preview."""

import io
import sys
import unittest
from datetime import date
from pathlib import Path

from rich.console import Console

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.analyzer.activity import ActivityAnalyzer
from github_activity_generator.calendar.calendar_engine import CalendarEngine
from github_activity_generator.calendar.preview import render_simulation_preview
from github_activity_generator.generator.simulation import SimulationEngine


class TestCalendarAndSimulation(unittest.TestCase):
    def test_simulation_and_calendar_grid(self) -> None:
        records = ActivityAnalyzer.analyze(
            {"2024-02-29": 4, "2025-01-01": 2},
            date(2024, 1, 1),
            date(2025, 1, 5),
        )
        planned = {"2024-02-29": 99, "2024-03-01": 3}  # 2024-02-29 is protected, must stay 0 planned
        sim = SimulationEngine.simulate(records, planned)

        leap_day = CalendarEngine.inspect_date(sim.days, "2024-02-29")
        self.assertIsNotNone(leap_day)
        assert leap_day is not None
        self.assertEqual(leap_day.existing_count, 4)
        self.assertEqual(leap_day.planned_count, 0)
        self.assertTrue(leap_day.is_protected)

        sim_day = CalendarEngine.inspect_date(sim.days, "2024-03-01")
        self.assertIsNotNone(sim_day)
        assert sim_day is not None
        self.assertEqual(sim_day.planned_count, 3)
        self.assertTrue(sim_day.is_simulated)

        grids = CalendarEngine.build_year_grids(sim.days)
        self.assertEqual([g.year for g in grids], [2024, 2025])

        buf = io.StringIO()
        console = Console(file=buf, force_terminal=False, width=120)
        render_simulation_preview(console, sim)
        output = buf.getvalue()
        self.assertIn("SIMULATED CONTRIBUTION PREVIEW", output)
        self.assertIn("Year 2024", output)
        self.assertIn("Year 2025", output)


if __name__ == "__main__":
    unittest.main()
