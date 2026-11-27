"""Interactive prompt helpers using Rich (with optional Questionary support)."""

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt


def ask_text(console: Console, message: str, default: str = "") -> str:
    """Prompt for text input."""
    return Prompt.ask(message, default=default, console=console).strip()


def ask_secret(console: Console, message: str) -> str:
    """Prompt for sensitive input without echoing characters to the terminal."""
    return Prompt.ask(message, password=True, console=console).strip()


def ask_int(
    console: Console,
    message: str,
    *,
    default: int | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Prompt for an integer with optional bounds validation."""
    while True:
        val = (
            IntPrompt.ask(message, default=default, console=console)
            if default is not None
            else IntPrompt.ask(message, console=console)
        )
        if min_value is not None and val < min_value:
            console.print(f"[red]Value must be at least {min_value}.[/red]")
            continue
        if max_value is not None and val > max_value:
            console.print(f"[red]Value must be at most {max_value}.[/red]")
            continue
        return val


def ask_confirm(console: Console, message: str, default: bool = False) -> bool:
    """Prompt for a yes/no confirmation."""
    return Confirm.ask(message, default=default, console=console)


def ask_choice(
    console: Console,
    message: str,
    choices: list[str],
    default: str | None = None,
) -> str:
    """Prompt the user to pick one option from a list."""
    return Prompt.ask(
        message,
        choices=choices,
        default=default or choices[0],
        console=console,
    )
