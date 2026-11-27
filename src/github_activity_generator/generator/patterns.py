"""Predefined and custom activity pattern weight generators."""

import random

from github_activity_generator.analyzer.activity import DayRecord
from github_activity_generator.config import GenerationConfig


def compute_pattern_weights(
    eligible_records: list[DayRecord],
    config: GenerationConfig,
) -> list[float]:
    """Return a non-negative relative weight for each eligible DayRecord."""
    n = len(eligible_records)
    if n == 0:
        return []

    rng = random.Random(config.random_seed)
    pattern = config.pattern

    if pattern == "consistent":
        return [1.0] * n

    if pattern == "random":
        return [rng.uniform(0.2, 1.0) for _ in range(n)]

    if pattern == "weekday_focused":
        return [1.0 if r.weekday < 5 else 0.2 for r in eligible_records]

    if pattern == "weekend_focused":
        return [1.0 if r.weekday >= 5 else 0.25 for r in eligible_records]

    if pattern == "increasing":
        return [0.2 + 0.8 * (i / max(1, n - 1)) for i in range(n)]

    if pattern == "decreasing":
        return [1.0 - 0.8 * (i / max(1, n - 1)) for i in range(n)]

    if pattern == "sprint":
        # 5-day active sprint followed by 2-day cool-down
        return [1.0 if (i % 7) < 5 else 0.15 for i in range(n)]

    if pattern == "break_based":
        # 10-day active block followed by 4-day break
        return [1.0 if (i % 14) < 10 else 0.0 for i in range(n)]

    if pattern == "custom":
        weights: list[float] = []
        for r in eligible_records:
            w = config.custom_weights.get(
                r.date_str,
                config.custom_weights.get(str(r.weekday), 1.0),
            )
            weights.append(max(0.0, float(w)))
        return weights

    return [1.0] * n
