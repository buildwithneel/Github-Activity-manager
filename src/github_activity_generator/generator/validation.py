"""Validation for activity generation configuration and target feasibility."""

from github_activity_generator.config import GenerationConfig
from github_activity_generator.constants import ACTIVITY_PATTERNS
from github_activity_generator.exceptions import ImpossibleTargetError, ValidationError


def validate_generation_config(config: GenerationConfig) -> None:
    """Validate GenerationConfig fields and raise ValidationError on invalid values."""
    if config.min_commits_per_day < 0:
        raise ValidationError("Minimum commits per day cannot be negative.")
    if config.max_commits_per_day < config.min_commits_per_day:
        raise ValidationError(
            "Maximum commits per day must be greater than or equal to minimum commits per day."
        )
    if config.pattern not in ACTIVITY_PATTERNS:
        raise ValidationError(
            f"Unknown activity pattern '{config.pattern}'. "
            f"Valid options: {', '.join(ACTIVITY_PATTERNS)}."
        )
    if config.exact_daily_target is not None and config.exact_daily_target < 0:
        raise ValidationError("Exact daily target cannot be negative.")
    if config.average_daily_target is not None and config.average_daily_target < 0:
        raise ValidationError("Average daily target cannot be negative.")
    if config.weekly_target is not None and config.weekly_target < 0:
        raise ValidationError("Weekly target cannot be negative.")
    if config.monthly_target is not None and config.monthly_target < 0:
        raise ValidationError("Monthly target cannot be negative.")
    if config.total_target is not None and config.total_target < 0:
        raise ValidationError("Total planned target cannot be negative.")
    if any(wd < 0 or wd > 6 for wd in config.enabled_weekdays):
        raise ValidationError("Enabled weekdays must be integers between 0 (Monday) and 6 (Sunday).")


def validate_target_feasibility(
    eligible_count: int,
    config: GenerationConfig,
    effective_target: int | None,
) -> None:
    """Check whether the requested target can be achieved with the eligible dates."""
    if eligible_count == 0:
        raise ImpossibleTargetError(
            "No eligible dates are available in the selected range. "
            "All dates are either protected (existing contributions > 0) or excluded by weekday/date rules. "
            "Adjust your date range, weekday filters, or exclusions."
        )

    if effective_target is None:
        return

    if config.exact_daily_target is not None:
        expected_total = config.exact_daily_target * eligible_count
        if config.total_target is not None and config.total_target != expected_total:
            raise ImpossibleTargetError(
                f"Conflicting targets: exact daily target ({config.exact_daily_target}) across "
                f"{eligible_count} eligible days equals {expected_total}, which does not match "
                f"total_target={config.total_target}."
            )
        return

    min_possible = config.min_commits_per_day * eligible_count
    max_possible = config.max_commits_per_day * eligible_count
    if effective_target < min_possible:
        suggested_min = effective_target // eligible_count
        raise ImpossibleTargetError(
            f"Requested target ({effective_target}) is below the minimum possible ({min_possible}) "
            f"for {eligible_count} eligible days with min_commits_per_day={config.min_commits_per_day}. "
            f"Suggestion: lower min_commits_per_day to {suggested_min} or increase total_target to >= {min_possible}."
        )
    if effective_target > max_possible:
        suggested_max = (effective_target + eligible_count - 1) // eligible_count
        raise ImpossibleTargetError(
            f"Requested target ({effective_target}) exceeds the maximum possible ({max_possible}) "
            f"for {eligible_count} eligible days with max_commits_per_day={config.max_commits_per_day}. "
            f"Suggestion: raise max_commits_per_day to {suggested_max} or lower total_target to <= {max_possible}."
        )
