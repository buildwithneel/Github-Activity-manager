"""SVG and PNG contribution graph image exporters."""

from pathlib import Path

from PIL import Image, ImageDraw

from github_activity_generator.calendar.calendar_engine import CalendarEngine
from github_activity_generator.constants import GITHUB_GREEN_PALETTE
from github_activity_generator.exceptions import StorageError
from github_activity_generator.generator.simulation import SimulationResult


def export_svg_graph(simulation: SimulationResult, output_path: Path) -> Path:
    """Export a GitHub-style contribution graph as a scalable SVG file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grids = CalendarEngine.build_year_grids(simulation.days)
    if not grids:
        raise StorageError("No calendar data available to export SVG.")

    cell = 12
    gap = 3
    step = cell + gap
    margin_x = 30
    year_block_h = 7 * step + 40
    max_weeks = max(len(g.weeks) for g in grids)
    width = margin_x * 2 + max_weeks * step
    height = 50 + len(grids) * year_block_h

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0d1117" rx="8"/>',
        '<text x="30" y="26" fill="#e6edf3" font-family="monospace" font-size="14" font-weight="bold">'
        f'GitHub Activity Generator (Existing: {simulation.existing_total}, '
        f'Simulated Planned: {simulation.planned_total})</text>',
    ]

    for idx, grid in enumerate(grids):
        y_offset = 45 + idx * year_block_h
        svg_lines.append(
            f'<text x="{margin_x}" y="{y_offset + 12}" fill="#8b949e" '
            f'font-family="monospace" font-size="12">{grid.year}</text>'
        )
        grid_y = y_offset + 20
        for col, week in enumerate(grid.weeks):
            for row, day in enumerate(week):
                if day is None:
                    continue
                x = margin_x + col * step
                y = grid_y + row * step
                color = GITHUB_GREEN_PALETTE[day.intensity_level]
                svg_lines.append(
                    f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                    f'rx="2" fill="{color}"/>'
                )

    svg_lines.append("</svg>")
    output_path.write_text("\n".join(svg_lines), encoding="utf-8")
    return output_path


def export_png_graph(simulation: SimulationResult, output_path: Path) -> Path:
    """Export a GitHub-style contribution graph as a PNG image using Pillow."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grids = CalendarEngine.build_year_grids(simulation.days)
    if not grids:
        raise StorageError("No calendar data available to export PNG.")

    cell = 14
    gap = 4
    step = cell + gap
    margin_x = 32
    year_block_h = 7 * step + 44
    max_weeks = max(len(g.weeks) for g in grids)
    width = margin_x * 2 + max_weeks * step
    height = 56 + len(grids) * year_block_h

    img = Image.new("RGB", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)

    title = (
        f"GitHub Activity Generator | Existing: {simulation.existing_total} | "
        f"Simulated Planned: {simulation.planned_total}"
    )
    draw.text((margin_x, 16), title, fill="#e6edf3")

    for idx, grid in enumerate(grids):
        y_offset = 48 + idx * year_block_h
        draw.text((margin_x, y_offset), str(grid.year), fill="#8b949e")
        grid_y = y_offset + 20
        for col, week in enumerate(grid.weeks):
            for row, day in enumerate(week):
                if day is None:
                    continue
                x = margin_x + col * step
                y = grid_y + row * step
                color = GITHUB_GREEN_PALETTE[day.intensity_level]
                draw.rounded_rectangle(
                    [x, y, x + cell, y + cell], radius=2, fill=color
                )

    img.save(output_path, format="PNG")
    return output_path
