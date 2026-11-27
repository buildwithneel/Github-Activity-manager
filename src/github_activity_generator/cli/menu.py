"""Main interactive CLI controller for GitHub Activity Generator."""

import os
from datetime import date, timedelta
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from github_activity_generator.analyzer.activity import ActivityAnalyzer, DayRecord
from github_activity_generator.analyzer.empty_days import EmptyDayAnalyzer
from github_activity_generator.analyzer.empty_weeks import EmptyWeekAnalyzer
from github_activity_generator.analyzer.statistics import compute_statistics
from github_activity_generator.auth.oauth import OAuthDeviceFlowAuthenticator
from github_activity_generator.auth.pat import PATAuthenticator, RECOMMENDED_PAT_SCOPES
from github_activity_generator.auth.session import SessionManager
from github_activity_generator.calendar.calendar_engine import CalendarEngine
from github_activity_generator.calendar.preview import render_simulation_preview
from github_activity_generator.config import AppPaths, AppSettings
from github_activity_generator.constants import ACTIVITY_PATTERNS
from github_activity_generator.exceptions import AppError
from github_activity_generator.export import (
    export_activity_json,
    export_daily_csv,
    export_empty_day_report,
    export_empty_days_csv,
    export_empty_week_report,
    export_empty_weeks_csv,
    export_existing_work_csv,
    export_existing_work_report,
    export_png_graph,
    export_svg_graph,
    export_text_report,
)
from github_activity_generator.generator.distribution import DistributionEngine, DistributionPlan
from github_activity_generator.generator.simulation import SimulationEngine, SimulationResult
from github_activity_generator.git.operations import (
    commit_activity_change,
    prepare_activity_entry,
    push_to_remote,
)
from github_activity_generator.git.repository import clone_repository, initialize_local_repository
from github_activity_generator.git.safety import inspect_repo_safety
from github_activity_generator.github.contributions import (
    ContributionHistory,
    ContributionRetriever,
    parse_iso_date,
)
from github_activity_generator.github.profile import fetch_user_profile
from github_activity_generator.github.repositories import RepositoryAPI
from github_activity_generator.logging_setup import setup_logging
from github_activity_generator.storage.config_store import ConfigStore
from github_activity_generator.storage.database import ActivityDatabase
from github_activity_generator.storage.keyring_store import KeyringStore

from github_activity_generator.cli.display import (
    render_gap_summary,
    render_header,
    render_main_menu,
    render_profile,
    render_statistics,
)
from github_activity_generator.cli.progress import status_spinner
from github_activity_generator.cli.prompts import (
    ask_choice,
    ask_confirm,
    ask_int,
    ask_secret,
    ask_text,
)


class ActivityGeneratorCLI:
    """Coordinates user interaction, local state, API calls, analysis, and safe Git operations."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.console = Console()
        self.paths = AppPaths(root=data_dir) if data_dir else AppPaths()
        self.paths.ensure_dirs()
        self.logger = setup_logging(self.paths.logs_dir)
        self.config_store = ConfigStore(self.paths)
        self.settings: AppSettings = self.config_store.load()
        self.keyring = KeyringStore(self.paths.credentials_file)
        self.session = SessionManager(self.keyring)
        self.database = ActivityDatabase(self.paths.db_file)

        self.history: ContributionHistory | None = None
        self.records: list[DayRecord] = []
        self.plan: DistributionPlan | None = None
        self.simulation: SimulationResult | None = None
        self.current_operation = "Ready"

    def run(self) -> None:
        """Main interactive loop with graceful Ctrl+C handling."""
        try:
            while True:
                auth_status = self.session.validate_session()
                render_header(
                    self.console,
                    auth_status,
                    self.settings.selected_repo_full_name,
                    self.current_operation,
                )
                render_main_menu(self.console)

                choice = ask_text(self.console, "\nSelect an option", default="0")
                if choice == "0":
                    self.console.print("[cyan]Goodbye![/cyan]")
                    break

                try:
                    self._dispatch(choice)
                except AppError as exc:
                    self.console.print(f"[bold red]Error:[/bold red] {exc}")
                    self.logger.warning("Handled application error: %s", exc)
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Operation cancelled.[/yellow]")
                self.console.print()
        except KeyboardInterrupt:
            self.console.print("\n[cyan]Exiting cleanly. Goodbye![/cyan]")

    def _dispatch(self, choice: str) -> None:
        handlers = {
            "1": self._handle_oauth_login,
            "2": self._handle_pat_login,
            "3": self._handle_view_profile,
            "4": self._handle_retrieve_contributions,
            "5": self._handle_analyze_calendar,
            "6": self._handle_find_gaps,
            "7": self._handle_configure_generation,
            "8": self._handle_generate_plan,
            "9": self._handle_preview_graph,
            "10": self._handle_manage_repositories,
            "11": self._handle_export_reports,
            "12": self._handle_settings,
            "13": self._handle_logout,
        }
        handler = handlers.get(choice)
        if handler is None:
            self.console.print("[yellow]Invalid menu option. Choose 0-13.[/yellow]")
            return
        handler()

    def _handle_oauth_login(self) -> None:
        self.current_operation = "GitHub OAuth Login"
        client_id = (
            self.settings.oauth_client_id
            or os.environ.get("GITHUB_OAUTH_CLIENT_ID")
            or ask_text(
                self.console,
                "Enter your GitHub OAuth App Client ID (no client secret needed)",
            )
        )
        oauth = OAuthDeviceFlowAuthenticator(self.session, client_id=client_id)
        with status_spinner(self.console, "Requesting GitHub OAuth device code..."):
            challenge = oauth.request_device_code()

        self.settings.oauth_client_id = client_id
        self.config_store.save(self.settings)

        self.console.print(
            Panel(
                f"Open [bold cyan]{challenge.verification_uri}[/bold cyan]\n"
                f"Enter code: [bold green]{challenge.user_code}[/bold green]",
                title="GitHub Device Authorization",
                border_style="green",
            )
        )
        oauth.open_browser(challenge.verification_uri)
        with status_spinner(self.console, "Waiting for browser authorization..."):
            profile = oauth.poll_for_token(challenge)
        self.console.print(f"[green]Logged in via OAuth as {profile.login}![/green]")
        self.database.record_operation("auth_login", f"OAuth login for {profile.login}")

    def _handle_pat_login(self) -> None:
        self.current_operation = "Personal Access Token Login"
        self.console.print("[cyan]Minimum recommended PAT permissions:[/cyan]")
        for scope in RECOMMENDED_PAT_SCOPES:
            self.console.print(f"  - {scope}")
        token = ask_secret(self.console, "Enter your GitHub Personal Access Token (input hidden)")
        auth = PATAuthenticator(self.session)
        with status_spinner(self.console, "Verifying token with GitHub..."):
            profile = auth.authenticate(token)
        self.console.print(f"[green]Authenticated as {profile.login}![/green]")
        self.database.record_operation("auth_login", f"PAT login for {profile.login}")

    def _handle_view_profile(self) -> None:
        self.current_operation = "Viewing Profile"
        client = self.session.get_authenticated_client()
        with status_spinner(self.console, "Fetching GitHub profile..."):
            profile = fetch_user_profile(client)
        render_profile(self.console, profile)

    def _handle_retrieve_contributions(self) -> None:
        self.current_operation = "Retrieving Contribution History"
        client = self.session.get_authenticated_client()
        status = self.session.validate_session()
        username = status.username or ask_text(self.console, "GitHub username")

        mode = ask_choice(
            self.console,
            "Select date range mode",
            ["last_365_days", "full_year", "multi_year", "custom_dates"],
            default="last_365_days",
        )
        today = date.today()
        if mode == "last_365_days":
            end_d = today
            start_d = today - timedelta(days=364)
        elif mode == "full_year":
            yr = ask_int(self.console, "Enter year (e.g. 2025)", default=today.year, min_value=2008, max_value=today.year)
            start_d, end_d = date(yr, 1, 1), date(yr, 12, 31)
        elif mode == "multi_year":
            y1 = ask_int(self.console, "Start year", default=today.year - 1, min_value=2008, max_value=today.year)
            y2 = ask_int(self.console, "End year", default=today.year, min_value=y1, max_value=today.year)
            start_d, end_d = date(y1, 1, 1), date(y2, 12, 31)
        else:
            start_d = parse_iso_date(ask_text(self.console, "Start date (YYYY-MM-DD)"))
            end_d = parse_iso_date(ask_text(self.console, "End date (YYYY-MM-DD)"))

        retriever = ContributionRetriever(client, self.database)
        with status_spinner(self.console, f"Retrieving contributions for {start_d}..{end_d}..."):
            self.history = retriever.fetch_contributions(username, start_d, end_d)

        self.settings.generation.start_date = start_d.isoformat()
        self.settings.generation.end_date = end_d.isoformat()
        self.config_store.save(self.settings)

        self.records = ActivityAnalyzer.analyze(
            self.history.daily_counts,
            self.history.start_date,
            self.history.end_date,
            excluded_dates=set(self.settings.generation.excluded_dates),
        )
        self.console.print(
            f"[green]Retrieved {len(self.records)} days "
            f"(Existing total: {self.history.total_contributions}).[/green]\n"
            "[dim]Note: A count of 0 means no qualifying contribution was returned by GitHub's API.[/dim]"
        )

    def _ensure_records(self) -> list[DayRecord]:
        if not self.records:
            raise AppError(
                "No contribution data loaded yet. Run '4. Retrieve Contribution History' first."
            )
        return self.records

    def _handle_analyze_calendar(self) -> None:
        self.current_operation = "Analyzing Activity Calendar"
        records = self._ensure_records()
        planned = self.plan.planned_counts if self.plan else None
        stats = compute_statistics(records, planned_counts=planned)
        render_statistics(self.console, stats)

    def _handle_find_gaps(self) -> None:
        self.current_operation = "Finding Empty Days and Weeks"
        records = self._ensure_records()
        empty_days = EmptyDayAnalyzer.analyze(records)
        empty_weeks = EmptyWeekAnalyzer.analyze(records)
        render_gap_summary(self.console, empty_days, empty_weeks)

    def _handle_configure_generation(self) -> None:
        self.current_operation = "Configuring Activity Generation"
        cfg = self.settings.generation
        cfg.min_commits_per_day = ask_int(
            self.console, "Minimum commits per eligible day", default=cfg.min_commits_per_day, min_value=0
        )
        cfg.max_commits_per_day = ask_int(
            self.console,
            "Maximum commits per eligible day",
            default=max(cfg.min_commits_per_day, cfg.max_commits_per_day),
            min_value=cfg.min_commits_per_day,
        )
        cfg.exclude_weekends = ask_confirm(
            self.console, "Exclude weekends (Sat/Sun)?", default=cfg.exclude_weekends
        )
        cfg.pattern = ask_choice(
            self.console,
            "Select activity pattern",
            ACTIVITY_PATTERNS,
            default=cfg.pattern,
        )
        target_str = ask_text(
            self.console,
            "Optional total planned target (leave blank for pattern-based)",
            default="" if cfg.total_target is None else str(cfg.total_target),
        )
        cfg.total_target = int(target_str) if target_str.isdigit() else None
        cfg.random_seed = ask_int(
            self.console, "Deterministic random seed", default=cfg.random_seed or 42
        )
        self.config_store.save(self.settings)
        self.console.print("[green]Configuration saved locally.[/green]")

    def _handle_generate_plan(self) -> None:
        self.current_operation = "Generating Activity Plan"
        records = self._ensure_records()
        self.plan = DistributionEngine.distribute(records, self.settings.generation)
        self.simulation = SimulationEngine.simulate(records, self.plan.planned_counts)
        self.database.save_plan(
            f"plan-{date.today().isoformat()}",
            self.settings.generation.to_dict(),
            self.plan.planned_counts,
        )
        self.console.print(
            f"[green]Activity plan generated![/green] "
            f"Eligible dates: {len(self.plan.eligible_dates)} | "
            f"Protected dates: {len(self.plan.protected_dates)} | "
            f"Simulated planned total: {self.plan.total_planned}"
        )
        for warning in self.plan.warnings:
            self.console.print(f"[yellow]Warning: {warning}[/yellow]")

    def _handle_preview_graph(self) -> None:
        self.current_operation = "Previewing Contribution Graph"
        records = self._ensure_records()
        sim = self.simulation or SimulationEngine.simulate(records, {})
        render_simulation_preview(self.console, sim)
        if ask_confirm(self.console, "Inspect a specific date?", default=False):
            target = ask_text(self.console, "Enter date (YYYY-MM-DD)")
            day = CalendarEngine.inspect_date(sim.days, target)
            if day:
                self.console.print(
                    f"[cyan]{day.date_str}[/cyan]: existing={day.existing_count}, "
                    f"simulated_planned={day.planned_count}, protected={day.is_protected}"
                )
            else:
                self.console.print("[yellow]Date not found in current range.[/yellow]")

    def _handle_manage_repositories(self) -> None:
        self.current_operation = "Managing Repositories"
        mode = ask_choice(
            self.console,
            "Repository mode",
            ["create_new", "select_existing", "genuine_activity_commit"],
            default="select_existing",
        )
        if mode == "create_new":
            client = self.session.get_authenticated_client()
            api = RepositoryAPI(client)
            name = ask_text(self.console, "New repository name")
            desc = ask_text(self.console, "Description", default="")
            private = ask_confirm(self.console, "Private repository?", default=False)
            with status_spinner(self.console, f"Creating repository '{name}' on GitHub..."):
                repo = api.create_repository(name, description=desc, private=private)
            local_dir = Path(
                ask_text(self.console, "Local directory path", default=str(Path.cwd() / repo.name))
            )
            initialize_local_repository(local_dir, remote_url=repo.clone_url)
            self.settings.selected_repo_full_name = repo.full_name
            self.settings.selected_repo_local_path = str(local_dir)
            self.config_store.save(self.settings)
            self.console.print(f"[green]Created and initialized {repo.full_name} at {local_dir}.[/green]")

        elif mode == "select_existing":
            client = self.session.get_authenticated_client()
            api = RepositoryAPI(client)
            with status_spinner(self.console, "Fetching your GitHub repositories..."):
                repos = api.list_repositories(per_page=30)
            table = Table(title="Your Repositories")
            table.add_column("#", style="cyan")
            table.add_column("Repository", style="white")
            table.add_column("Visibility", style="yellow")
            for idx, r in enumerate(repos, start=1):
                table.add_row(str(idx), r.full_name, "Private" if r.private else "Public")
            self.console.print(table)
            if not repos:
                return
            sel = ask_int(self.console, "Select repository number", min_value=1, max_value=len(repos))
            chosen = repos[sel - 1]
            local_dir = Path(
                ask_text(self.console, "Local path to clone or use", default=str(Path.cwd() / chosen.name))
            )
            if not (local_dir / ".git").exists():
                if ask_confirm(self.console, f"Clone {chosen.full_name} into {local_dir}?", default=True):
                    clone_repository(chosen.clone_url, local_dir)
            self.settings.selected_repo_full_name = chosen.full_name
            self.settings.selected_repo_local_path = str(local_dir)
            self.config_store.save(self.settings)
            self.console.print(f"[green]Selected repository: {chosen.full_name}[/green]")

        elif mode == "genuine_activity_commit":
            if not self.settings.selected_repo_local_path:
                raise AppError("No local repository selected. Select or create one first.")
            repo_path = Path(self.settings.selected_repo_local_path)
            safety = inspect_repo_safety(repo_path)
            if safety.has_uncommitted_changes:
                self.console.print(
                    "[yellow]Warning: Repository has uncommitted changes. "
                    "Only activity.txt will be staged if you proceed.[/yellow]"
                )
            note = ask_text(self.console, "Enter genuine work note to record in activity.txt")
            dry_run = ask_confirm(self.console, "Run in dry-run mode first?", default=True)
            changed, diff = prepare_activity_entry(repo_path, note)
            if not changed:
                self.console.print("[yellow]No changes detected.[/yellow]")
                return
            self.console.print(Panel(diff, title="Proposed Diff (activity.txt)", border_style="cyan"))
            if ask_confirm(self.console, "Commit this genuine change with current timestamp?", default=False):
                msg = ask_text(self.console, "Commit message", default=f"Log activity: {note[:40]}")
                out = commit_activity_change(repo_path, msg, dry_run=dry_run)
                self.console.print(f"[green]{out or 'Committed.'}[/green]")
                if ask_confirm(self.console, "Push to remote 'origin'?", default=False):
                    push_out = push_to_remote(repo_path, confirmed=True, dry_run=dry_run)
                    self.console.print(f"[green]{push_out or 'Pushed.'}[/green]")

    def _handle_export_reports(self) -> None:
        self.current_operation = "Exporting Reports"
        records = self._ensure_records()
        planned = self.plan.planned_counts if self.plan else {}
        empty_days = EmptyDayAnalyzer.analyze(records)
        empty_weeks = EmptyWeekAnalyzer.analyze(records)
        stats = compute_statistics(records, planned)
        sim = self.simulation or SimulationEngine.simulate(records, planned)

        fmt = ask_choice(
            self.console,
            "Select export format",
            ["csv", "json", "text", "svg", "png", "all"],
            default="all",
        )
        out_dir = self.paths.exports_dir
        exported: list[Path] = []
        if fmt in ("csv", "all"):
            exported.append(export_daily_csv(records, out_dir / "daily_activity.csv", planned))
            exported.append(export_empty_days_csv(empty_days, out_dir / "empty_days.csv"))
            exported.append(export_empty_weeks_csv(empty_weeks, out_dir / "empty_weeks.csv"))
            exported.append(export_existing_work_csv(records, out_dir / "existing_work.csv"))
        if fmt in ("json", "all"):
            exported.append(export_activity_json(records, stats, out_dir / "activity_report.json", planned))
        if fmt in ("text", "all"):
            exported.append(export_text_report(stats, empty_days, empty_weeks, out_dir / "summary_report.txt"))
            exported.append(export_empty_day_report(empty_days, out_dir / "empty_days_report.txt"))
            exported.append(export_empty_week_report(empty_weeks, out_dir / "empty_weeks_report.txt"))
            exported.append(export_existing_work_report(records, out_dir / "existing_work_report.txt"))
        if fmt in ("svg", "all"):
            exported.append(export_svg_graph(sim, out_dir / "contribution_graph.svg"))
        if fmt in ("png", "all"):
            exported.append(export_png_graph(sim, out_dir / "contribution_graph.png"))

        for path in exported:
            self.console.print(f"[green]Exported:[/green] {path}")

    def _handle_settings(self) -> None:
        self.current_operation = "Settings"
        action = ask_choice(
            self.console,
            "Settings action",
            ["view", "export_config", "import_config", "clear_local_data"],
            default="view",
        )
        if action == "view":
            self.console.print(self.settings.to_dict())
        elif action == "export_config":
            dest = self.paths.exports_dir / "generation_config.json"
            self.config_store.export_generation_config(self.settings.generation, dest)
            self.console.print(f"[green]Exported configuration to {dest}[/green]")
        elif action == "import_config":
            src = Path(ask_text(self.console, "Path to configuration JSON"))
            self.settings.generation = self.config_store.import_generation_config(src)
            self.config_store.save(self.settings)
            self.console.print("[green]Imported configuration.[/green]")
        elif action == "clear_local_data":
            if ask_confirm(self.console, "Clear cached contributions, saved plans, and history?", default=False):
                self.database.clear_all_data()
                self.history = None
                self.records = []
                self.plan = None
                self.simulation = None
                self.console.print("[green]Local database cleared.[/green]")

    def _handle_logout(self) -> None:
        self.current_operation = "Logout"
        self.session.logout()
        self.console.print("[green]Logged out and cleared stored credentials.[/green]")


def run_cli() -> None:
    """Entrypoint for the interactive CLI."""
    ActivityGeneratorCLI().run()
