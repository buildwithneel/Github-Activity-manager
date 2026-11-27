"""GitHub contribution retrieval engine with multi-year support and local caching."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from github_activity_generator.exceptions import GitHubAPIError, ValidationError
from github_activity_generator.github.client import GitHubClient
from github_activity_generator.github.graphql import (
    CONTRIBUTION_CALENDAR_QUERY,
    CONTRIBUTION_YEARS_QUERY,
)
from github_activity_generator.storage.database import ActivityDatabase


@dataclass
class ContributionHistory:
    """Normalized GitHub contribution history for a date range."""

    username: str
    start_date: date
    end_date: date
    daily_counts: dict[str, int]
    total_contributions: int
    yearly_totals: dict[int, int] = field(default_factory=dict)
    monthly_totals: dict[str, int] = field(default_factory=dict)
    restricted_contributions: int = 0
    available_years: list[int] = field(default_factory=list)


def parse_iso_date(value: str) -> date:
    """Parse YYYY-MM-DD into a date object, raising ValidationError on failure."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValidationError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


def iter_date_range(start: date, end: date) -> list[date]:
    """Return every calendar date from start to end inclusive."""
    if start > end:
        raise ValidationError(f"Start date {start} cannot be after end date {end}.")
    days = (end - start).days + 1
    return [start + timedelta(days=offset) for offset in range(days)]


def split_range_by_year(start: date, end: date) -> list[tuple[date, date]]:
    """Split a date range into per-calendar-year chunks for GitHub GraphQL queries."""
    if start > end:
        raise ValidationError(f"Start date {start} cannot be after end date {end}.")
    chunks: list[tuple[date, date]] = []
    for year in range(start.year, end.year + 1):
        chunk_start = max(start, date(year, 1, 1))
        chunk_end = min(end, date(year, 12, 31))
        chunks.append((chunk_start, chunk_end))
    return chunks


class ContributionRetriever:
    """Retrieves and normalizes GitHub contributionCalendar data across years."""

    def __init__(
        self,
        client: GitHubClient,
        database: ActivityDatabase | None = None,
    ) -> None:
        self.client = client
        self.database = database

    def get_available_years(self, username: str) -> list[int]:
        """Return years in which the user has recorded GitHub contributions."""
        data = self.client.graphql(CONTRIBUTION_YEARS_QUERY, {"login": username})
        user = data.get("user")
        if not isinstance(user, dict):
            raise GitHubAPIError(f"GitHub user '{username}' was not found.")
        years = user.get("contributionsCollection", {}).get("contributionYears", [])
        return sorted((int(y) for y in years), reverse=True)

    def fetch_contributions(
        self,
        username: str,
        start_date: date,
        end_date: date,
        *,
        use_cache: bool = False,
    ) -> ContributionHistory:
        """Retrieve contribution counts for [start_date, end_date], querying year-by-year."""
        all_dates = iter_date_range(start_date, end_date)
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        if use_cache and self.database is not None:
            cached = self.database.get_cached_contributions(username, start_iso, end_iso)
            if len(cached) == len(all_dates):
                return self._build_history(username, start_date, end_date, cached, 0, [])

        merged_counts: dict[str, int] = {d.isoformat(): 0 for d in all_dates}
        restricted_total = 0

        for chunk_start, chunk_end in split_range_by_year(start_date, end_date):
            from_dt = f"{chunk_start.isoformat()}T00:00:00Z"
            to_dt = f"{chunk_end.isoformat()}T23:59:59Z"
            data = self.client.graphql(
                CONTRIBUTION_CALENDAR_QUERY,
                {"login": username, "from": from_dt, "to": to_dt},
            )
            user = data.get("user")
            if not isinstance(user, dict):
                raise GitHubAPIError(f"GitHub user '{username}' was not found.")

            collection = user.get("contributionsCollection", {})
            restricted_total += int(collection.get("restrictedContributionsCount", 0))
            weeks = collection.get("contributionCalendar", {}).get("weeks", [])
            for week in weeks:
                for day in week.get("contributionDays", []):
                    day_str = str(day.get("date", ""))
                    if day_str in merged_counts:
                        merged_counts[day_str] = int(day.get("contributionCount", 0))

        if self.database is not None:
            self.database.cache_contributions(username, merged_counts)

        return self._build_history(
            username=username,
            start_date=start_date,
            end_date=end_date,
            daily_counts=merged_counts,
            restricted_contributions=restricted_total,
            available_years=sorted({d.year for d in all_dates}),
        )

    @staticmethod
    def _build_history(
        username: str,
        start_date: date,
        end_date: date,
        daily_counts: dict[str, int],
        restricted_contributions: int,
        available_years: list[int],
    ) -> ContributionHistory:
        yearly_totals: dict[int, int] = {}
        monthly_totals: dict[str, int] = {}
        total = 0
        for date_str, count in sorted(daily_counts.items()):
            total += count
            year = int(date_str[:4])
            month = date_str[:7]
            yearly_totals[year] = yearly_totals.get(year, 0) + count
            monthly_totals[month] = monthly_totals.get(month, 0) + count

        return ContributionHistory(
            username=username,
            start_date=start_date,
            end_date=end_date,
            daily_counts=daily_counts,
            total_contributions=total,
            yearly_totals=yearly_totals,
            monthly_totals=monthly_totals,
            restricted_contributions=restricted_contributions,
            available_years=available_years or sorted(yearly_totals.keys()),
        )
