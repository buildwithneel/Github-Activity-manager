"""Rich terminal preview for simulated GitHub contribution calendars."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from github_activity_generator.calendar.calendar_engine import CalendarEngine
from github_activity_generator.constants import GITHUB_GREEN_PALETTE
from github_activity_generator.generator.simulation import SimulationResult

ROW_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def render_simulation_preview(console: Console, simulation: SimulationResult) -> None:
    """Render a dark-terminal-compatible GitHub-style contribution preview."""
    console.print(
        Panel.fit(
            "[bold yellow]SIMULATED CONTRIBUTION PREVIEW[/bold yellow]\n"
            "[dim]This preview is 100% simulated and independent of real Git operations.[/dim]",
            border_style="yellow",
        )
    )

    grids = CalendarEngine.build_year_grids(simulation.days)
    for grid in grids:
        console.print(f"\n[bold cyan]Year {grid.year}[/bold cyan]")

        # Month header line
        month_header = [" "] * (len(grid.weeks) * 2 + 5)
        for col_idx, label in grid.month_positions:
            pos = 5 + col_idx * 2
            for i, ch in enumerate(label):
                if pos + i < len(month_header):
                    month_header[pos + i] = ch
        console.print("".join(month_header), style="dim")

        for row in range(7):
            line = Text()
            label = f"{ROW_LABELS[row]}  " if row in (1, 3, 5) else "     "
            line.append(label, style="dim")
            for week_col in grid.weeks:
                cell = week_col[row]
                if cell is None:
                    line.append("  ")
                else:
                    color = GITHUB_GREEN_PALETTE[cell.intensity_level]
                    glyph = "■ " if cell.is_protected or cell.combined_simulated_count == 0 else "▪ "
                    line.append(glyph, style=color)
            console.print(line)

    legend = Text("Less ")
    for color in GITHUB_GREEN_PALETTE:
        legend.append("■ ", style=color)
    legend.append("More  (■ = Existing/Empty, ▪ = Simulated Planned)")
    console.print(legend)

    table = Table(title="Before vs Simulated Comparison", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Existing (Real GitHub)", justify="right", style="green")
    table.add_column("Planned (Simulated Only)", justify="right", style="yellow")
    table.add_column("Combined (Simulated)", justify="right", style="bold white")

    table.add_row(
        "Total Contributions",
        str(simulation.existing_total),
        str(simulation.planned_total),
        str(simulation.simulated_combined_total),
    )
    table.add_row(
        "Active Days",
        str(simulation.before_active_days),
        str(simulation.after_simulated_active_days - simulation.before_active_days),
        str(simulation.after_simulated_active_days),
    )
    console.print(table)
