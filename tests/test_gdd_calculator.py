from ml.prediction.features.gdd_calculator import (
    calculate_gdd,
    calculate_cumulative_gdd,
)


def test_calculate_gdd_positive():
    result = calculate_gdd(
        min_temp_c=18,
        max_temp_c=30,
        base_temp_c=10,
    )

    assert result == 14


def test_calculate_gdd_never_negative():
    result = calculate_gdd(
        min_temp_c=2,
        max_temp_c=8,
        base_temp_c=10,
    )

    assert result == 0


def test_calculate_cumulative_gdd():
    result = calculate_cumulative_gdd(
        daily_min_temps_c=[18, 20],
        daily_max_temps_c=[30, 32],
        base_temp_c=10,
    )

    assert result == 30