"""Rich terminal display helpers: banner, main menu, tables, and reports."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from github_activity_generator.analyzer.empty_days import EmptyDayReport
from github_activity_generator.analyzer.empty_weeks import EmptyWeekReport
from github_activity_generator.analyzer.statistics import ActivityStatistics
from github_activity_generator.auth.session import AuthStatus
from github_activity_generator.constants import APP_NAME, APP_VERSION
from github_activity_generator.github.profile import UserProfile

MAIN_MENU_ITEMS = [
    ("1", "Login with GitHub OAuth"),
    ("2", "Login with Personal Access Token"),
    ("3", "View GitHub Profile"),
    ("4", "Retrieve Contribution History"),
    ("5", "Analyze Activity Calendar"),
    ("6", "Find Empty Days and Weeks"),
    ("7", "Configure Activity Generation"),
    ("8", "Generate Activity Plan"),
    ("9", "Preview Contribution Graph"),
    ("10", "Manage Repositories"),
    ("11", "Export Reports"),
    ("12", "Settings"),
    ("13", "Logout"),
    ("0", "Exit"),
]


def render_header(
    console: Console,
    auth_status: AuthStatus,
    selected_repo: str | None,
    current_operation: str = "Ready",
) -> None:
    """Render the application status banner."""
    auth_str = (
        f"[green]Authenticated ({auth_status.auth_method or 'token'})[/green] as "
        f"[bold cyan]{auth_status.username}[/bold cyan]"
        if auth_status.authenticated
        else "[yellow]Not Authenticated[/yellow]"
    )
    repo_str = f"[bold white]{selected_repo}[/bold white]" if selected_repo else "[dim]None[/dim]"

    body = (
        f"[bold white]{APP_NAME}[/bold white] [dim]v{APP_VERSION}[/dim]\n"
        f"Status: {auth_str}  |  Repository: {repo_str}\n"
        f"Operation: [cyan]{current_operation}[/cyan]"
    )
    console.print(Panel(body, border_style="bright_blue"))


def render_main_menu(console: Console) -> None:
    """Render the interactive main menu table."""
    table = Table(title="Main Menu", show_header=False, box=None, padding=(0, 2))
    table.add_column("Option", style="bold cyan", width=4)
    table.add_column("Action", style="white")
    for key, label in MAIN_MENU_ITEMS:
        table.add_row(f"[{key}]", label)
    console.print(table)


def render_profile(console: Console, profile: UserProfile) -> None:
    """Display authenticated GitHub user profile details."""
    table = Table(title=f"GitHub Profile: {profile.login}", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Username", profile.login)
    table.add_row("Name", profile.name or "-")
    table.add_row("Public Repos", str(profile.public_repos))
    table.add_row("Followers / Following", f"{profile.followers} / {profile.following}")
    table.add_row("Scopes", ", ".join(profile.scopes) if profile.scopes else "(fine-grained / default)")
    table.add_row("Profile URL", profile.html_url)
    console.print(table)


def render_statistics(console: Console, stats: ActivityStatistics) -> None:
    """Render existing vs simulated statistics clearly."""
    table = Table(title="Activity & Gap Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="white")

    table.add_row("Total Days in Range", str(stats.total_days))
    table.add_row("Active Days (Protected)", f"[green]{stats.active_days}[/green]")
    table.add_row("Empty Days (0 contributions)", f"[yellow]{stats.empty_days}[/yellow]")
    table.add_row("Excluded Days", str(stats.excluded_days))
    table.add_row("Eligible Days for Planning", f"[bold cyan]{stats.eligible_days}[/bold cyan]")
    table.add_row("Existing GitHub Contributions", str(stats.existing_total_contributions))
    table.add_row("Average Daily (Existing)", str(stats.average_daily_existing))
    table.add_row("Completely Empty Weeks", str(stats.completely_empty_weeks))
    table.add_row("Partially Active Weeks", str(stats.partially_active_weeks))
    table.add_row("Fully Active Weeks", str(stats.fully_active_weeks))
    table.add_row("Longest Existing Active Streak", f"{stats.longest_existing_active_streak} day(s)")
    table.add_row("Longest Inactive Streak", f"{stats.longest_inactive_streak} day(s)")
    if stats.highest_existing_day:
        table.add_row(
            "Highest Existing Day",
            f"{stats.highest_existing_day[0]} ({stats.highest_existing_day[1]})",
        )
    if stats.simulated_planned_total > 0:
        table.add_row(
            "Simulated Planned Total",
            f"[yellow]{stats.simulated_planned_total} (Simulated Only)[/yellow]",
        )
    console.print(table)


def render_gap_summary(
    console: Console, empty_days: EmptyDayReport, empty_weeks: EmptyWeekReport
) -> None:
    """Display summary tables for empty days and empty/partially-active weeks."""
    table = Table(title="Gap Analysis Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="white")
    table.add_row("Total Empty Days", str(len(empty_days.empty_days)))
    table.add_row("Weekday Gaps (Mon-Fri)", str(len(empty_days.weekday_gaps)))
    table.add_row("Weekend Gaps (Sat-Sun)", str(len(empty_days.weekend_gaps)))
    table.add_row("Longest Inactive Streak", f"{empty_days.longest_inactive_streak} day(s)")
    table.add_row("Completely Empty Weeks (7/7 empty)", str(len(empty_weeks.completely_empty_weeks)))
    table.add_row("Partially Active Weeks (eligible preserved)", str(len(empty_weeks.partially_active_weeks)))
    table.add_row("Fully Active Weeks", str(len(empty_weeks.fully_active_weeks)))
    console.print(table)

    if empty_weeks.completely_empty_weeks:
        w_table = Table(title="Completely Empty Weeks (showing up to 15)")
        w_table.add_column("ISO Week", style="cyan")
        w_table.add_column("Start", style="white")
        w_table.add_column("End", style="white")
        w_table.add_column("Eligible Days", justify="right", style="green")
        for w in empty_weeks.completely_empty_weeks[:15]:
            w_table.add_row(
                f"{w.iso_year}-W{w.iso_week:02d}",
                w.week_start.isoformat(),
                w.week_end.isoformat(),
                str(len(w.eligible_dates)),
            )
        console.print(w_table)
