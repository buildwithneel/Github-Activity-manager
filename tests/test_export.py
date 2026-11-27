"""Tests for CSV, JSON, text reports, SVG, and PNG exports."""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from github_activity_generator.analyzer.activity import ActivityAnalyzer
from github_activity_generator.analyzer.empty_days import EmptyDayAnalyzer
from github_activity_generator.analyzer.empty_weeks import EmptyWeekAnalyzer
from github_activity_generator.analyzer.statistics import compute_statistics
from github_activity_generator.export.csv_export import (
    export_daily_csv,
    export_empty_days_csv,
    export_empty_weeks_csv,
    export_existing_work_csv,
)
from github_activity_generator.export.image_export import export_png_graph, export_svg_graph
from github_activity_generator.export.json_export import export_activity_json
from github_activity_generator.export.reports import (
    export_empty_day_report,
    export_empty_week_report,
    export_existing_work_report,
    export_text_report,
)
from github_activity_generator.generator.simulation import SimulationEngine


class TestExports(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.records = ActivityAnalyzer.analyze(
            {"2025-01-06": 3, "2025-01-10": 1},
            date(2025, 1, 6),
            date(2025, 1, 19),
        )
        self.planned = {"2025-01-07": 2, "2025-01-13": 4}
        self.empty_days = EmptyDayAnalyzer.analyze(self.records)
        self.empty_weeks = EmptyWeekAnalyzer.analyze(self.records)
        self.stats = compute_statistics(self.records, self.planned)
        self.sim = SimulationEngine.simulate(self.records, self.planned)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_csv_exports(self) -> None:
        daily = export_daily_csv(self.records, self.out / "daily.csv", self.planned)
        self.assertTrue(daily.exists())
        self.assertIn("simulated_planned_contributions", daily.read_text(encoding="utf-8"))

        ed = export_empty_days_csv(self.empty_days, self.out / "empty_days.csv")
        ew = export_empty_weeks_csv(self.empty_weeks, self.out / "empty_weeks.csv")
        ex = export_existing_work_csv(self.records, self.out / "existing.csv")
        self.assertTrue(ed.exists() and ew.exists() and ex.exists())

    def test_json_and_text_reports(self) -> None:
        j_path = export_activity_json(self.records, self.stats, self.out / "activity.json", self.planned)
        parsed = json.loads(j_path.read_text(encoding="utf-8"))
        self.assertEqual(parsed["statistics"]["existing_total_contributions"], 4)
        self.assertEqual(parsed["statistics"]["simulated_planned_total"], 6)

        txt = export_text_report(self.stats, self.empty_days, self.empty_weeks, self.out / "report.txt")
        self.assertIn("GITHUB ACTIVITY GENERATOR", txt.read_text(encoding="utf-8"))
        self.assertTrue(export_empty_day_report(self.empty_days, self.out / "ed.txt").exists())
        self.assertTrue(export_empty_week_report(self.empty_weeks, self.out / "ew.txt").exists())
        self.assertTrue(export_existing_work_report(self.records, self.out / "ex.txt").exists())

    def test_svg_and_png_graph_exports(self) -> None:
        svg = export_svg_graph(self.sim, self.out / "graph.svg")
        self.assertTrue(svg.exists())
        self.assertIn("<svg", svg.read_text(encoding="utf-8"))

        png = export_png_graph(self.sim, self.out / "graph.png")
        self.assertTrue(png.exists())
        self.assertEqual(png.read_bytes()[:4], b"\x89PNG")


if __name__ == "__main__":
    unittest.main()
