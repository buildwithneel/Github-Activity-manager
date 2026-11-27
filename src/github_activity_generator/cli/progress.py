"""Progress indicators for API calls and exports."""

from contextlib import contextmanager
from typing import Iterator

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


@contextmanager
def status_spinner(console: Console, description: str) -> Iterator[None]:
    """Display a clean Rich spinner while an operation is running."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description=description, total=None)
        yield
