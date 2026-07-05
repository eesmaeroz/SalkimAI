"""Growing Degree Day (GDD) calculations."""

from __future__ import annotations

from collections.abc import Iterable


def calculate_gdd(
    min_temp_c: float,
    max_temp_c: float,
    base_temp_c: float = 10.0,
    upper_temp_c: float | None = None,
) -> float:
    """Calculate daily GDD and clamp negative results to zero."""
    if min_temp_c is None or max_temp_c is None:
        raise ValueError("Minimum and maximum temperatures cannot be empty.")

    minimum = float(min_temp_c)
    maximum = float(max_temp_c)
    if minimum > maximum:
        raise ValueError("Minimum temperature cannot exceed maximum temperature.")

    if upper_temp_c is not None:
        upper = float(upper_temp_c)
        minimum = min(minimum, upper)
        maximum = min(maximum, upper)

    return max(((minimum + maximum) / 2.0) - float(base_temp_c), 0.0)


def calculate_cumulative_gdd(
    daily_min_temps_c: Iterable[float],
    daily_max_temps_c: Iterable[float],
    base_temp_c: float = 10.0,
) -> float:
    """Calculate cumulative GDD for matching minimum/maximum series."""
    minimums = list(daily_min_temps_c)
    maximums = list(daily_max_temps_c)
    if len(minimums) != len(maximums):
        raise ValueError("Minimum and maximum temperature series must have equal length.")

    return sum(
        calculate_gdd(minimum, maximum, base_temp_c)
        for minimum, maximum in zip(minimums, maximums)
    )
