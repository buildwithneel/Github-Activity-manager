"""Smart distribution engine respecting existing activity protection and targets."""

import random
from dataclasses import dataclass, field

from github_activity_generator.analyzer.activity import DayRecord, DayStatus
from github_activity_generator.config import GenerationConfig
from github_activity_generator.exceptions import ImpossibleTargetError
from github_activity_generator.generator.patterns import compute_pattern_weights
from github_activity_generator.generator.validation import (
    validate_generation_config,
    validate_target_feasibility,
)


@dataclass
class DistributionPlan:
    """Result of distributing planned commits across eligible dates."""

    planned_counts: dict[str, int]
    eligible_dates: list[str]
    protected_dates: list[str]
    excluded_dates: list[str]
    total_planned: int
    requested_target: int | None
    remaining_target: int
    warnings: list[str] = field(default_factory=list)


class DistributionEngine:
    """Distributes planned activity strictly onto eligible, unprotected dates."""

    @staticmethod
    def distribute(
        records: list[DayRecord],
        config: GenerationConfig,
    ) -> DistributionPlan:
        validate_generation_config(config)

        protected_dates = [r.date_str for r in records if r.protected]
        excluded_dates: list[str] = []
        eligible_records: list[DayRecord] = []

        for rec in records:
            if rec.protected or rec.existing_count > 0:
                continue
            if rec.status == DayStatus.EXCLUDED:
                excluded_dates.append(rec.date_str)
                continue
            if config.exclude_weekends and rec.weekday >= 5:
                excluded_dates.append(rec.date_str)
                continue
            if rec.weekday not in config.enabled_weekdays:
                excluded_dates.append(rec.date_str)
                continue
            eligible_records.append(rec)

        eligible_dates = [r.date_str for r in eligible_records]
        effective_target = DistributionEngine._resolve_effective_target(
            eligible_records, config
        )
        validate_target_feasibility(len(eligible_records), config, effective_target)

        planned_counts: dict[str, int] = {r.date_str: 0 for r in records}
        warnings: list[str] = []

        if config.exact_daily_target is not None:
            for rec in eligible_records:
                planned_counts[rec.date_str] = config.exact_daily_target
        elif effective_target is not None:
            DistributionEngine._distribute_exact_total(
                eligible_records, config, effective_target, planned_counts
            )
        else:
            DistributionEngine._distribute_by_pattern(
                eligible_records, config, planned_counts
            )

        # Apply weekly / monthly caps if specified
        if config.weekly_target is not None:
            DistributionEngine._enforce_weekly_cap(
                eligible_records, config.weekly_target, planned_counts, warnings
            )
        if config.monthly_target is not None:
            DistributionEngine._enforce_monthly_cap(
                eligible_records, config.monthly_target, planned_counts, warnings
            )

        # Final safety assertion: never assign planned commits to protected dates
        for p_date in protected_dates:
            planned_counts[p_date] = 0

        total_planned = sum(planned_counts.values())
        remaining = max(0, (effective_target or total_planned) - total_planned)

        return DistributionPlan(
            planned_counts=planned_counts,
            eligible_dates=eligible_dates,
            protected_dates=protected_dates,
            excluded_dates=excluded_dates,
            total_planned=total_planned,
            requested_target=effective_target,
            remaining_target=remaining,
            warnings=warnings,
        )

    @staticmethod
    def _resolve_effective_target(
        eligible_records: list[DayRecord],
        config: GenerationConfig,
    ) -> int | None:
        if config.total_target is not None:
            return config.total_target
        if config.exact_daily_target is not None:
            return config.exact_daily_target * len(eligible_records)
        if config.average_daily_target is not None:
            return round(config.average_daily_target * len(eligible_records))
        return None

    @staticmethod
    def _distribute_exact_total(
        eligible_records: list[DayRecord],
        config: GenerationConfig,
        target: int,
        planned_counts: dict[str, int],
    ) -> None:
        n = len(eligible_records)
        min_c = config.min_commits_per_day
        max_c = config.max_commits_per_day

        # Initialize each eligible day at min_c
        assigned = [min_c] * n
        remaining = target - (min_c * n)

        weights = compute_pattern_weights(eligible_records, config)
        if sum(weights) <= 0:
            weights = [1.0] * n

        rng = random.Random(config.random_seed)
        indices = list(range(n))

        while remaining > 0:
            candidates = [i for i in indices if assigned[i] < max_c]
            if not candidates:
                raise ImpossibleTargetError(
                    f"Cannot distribute remaining {remaining} commits without exceeding "
                    f"max_commits_per_day={max_c}."
                )
            candidate_weights = [max(0.01, weights[i]) for i in candidates]
            chosen = rng.choices(candidates, weights=candidate_weights, k=1)[0]
            assigned[chosen] += 1
            remaining -= 1

        for rec, count in zip(eligible_records, assigned):
            planned_counts[rec.date_str] = count

    @staticmethod
    def _distribute_by_pattern(
        eligible_records: list[DayRecord],
        config: GenerationConfig,
        planned_counts: dict[str, int],
    ) -> None:
        weights = compute_pattern_weights(eligible_records, config)
        min_c = config.min_commits_per_day
        max_c = config.max_commits_per_day
        rng = random.Random(config.random_seed)

        for rec, w in zip(eligible_records, weights):
            if config.pattern == "random":
                planned_counts[rec.date_str] = rng.randint(min_c, max_c)
            elif w <= 0.0:
                planned_counts[rec.date_str] = min_c
            else:
                scaled = min_c + round(w * (max_c - min_c))
                planned_counts[rec.date_str] = max(min_c, min(max_c, scaled))

    @staticmethod
    def _enforce_weekly_cap(
        eligible_records: list[DayRecord],
        weekly_cap: int,
        planned_counts: dict[str, int],
        warnings: list[str],
    ) -> None:
        by_week: dict[tuple[int, int], list[DayRecord]] = {}
        for rec in eligible_records:
            by_week.setdefault((rec.iso_year, rec.week_number), []).append(rec)

        capped_weeks = 0
        for recs in by_week.values():
            week_sum = sum(planned_counts[r.date_str] for r in recs)
            if week_sum > weekly_cap:
                capped_weeks += 1
                excess = week_sum - weekly_cap
                for r in reversed(recs):
                    if excess <= 0:
                        break
                    reducible = min(planned_counts[r.date_str], excess)
                    planned_counts[r.date_str] -= reducible
                    excess -= reducible
        if capped_weeks:
            warnings.append(
                f"Weekly target cap ({weekly_cap}/week) reduced planned commits in {capped_weeks} week(s)."
            )

    @staticmethod
    def _enforce_monthly_cap(
        eligible_records: list[DayRecord],
        monthly_cap: int,
        planned_counts: dict[str, int],
        warnings: list[str],
    ) -> None:
        by_month: dict[str, list[DayRecord]] = {}
        for rec in eligible_records:
            by_month.setdefault(f"{rec.year:04d}-{rec.month:02d}", []).append(rec)

        capped_months = 0
        for recs in by_month.values():
            month_sum = sum(planned_counts[r.date_str] for r in recs)
            if month_sum > monthly_cap:
                capped_months += 1
                excess = month_sum - monthly_cap
                for r in reversed(recs):
                    if excess <= 0:
                        break
                    reducible = min(planned_counts[r.date_str], excess)
                    planned_counts[r.date_str] -= reducible
                    excess -= reducible
        if capped_months:
            warnings.append(
                f"Monthly target cap ({monthly_cap}/month) reduced planned commits in {capped_months} month(s)."
            )
