from ml.prediction.features.gdd_calculator import (
    calculate_gdd,
    calculate_cumulative_gdd,
)
from ml.prediction.features.weather_provider import get_mock_weather_data


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


def test_calculate_gdd_rejects_inverted_range():
    try:
        calculate_gdd(min_temp_c=30, max_temp_c=18)
    except ValueError as error:
        assert "Minimum temperature" in str(error)
    else:
        raise AssertionError("Expected an inverted temperature range to fail")


def test_weather_mock_is_deterministic():
    first = get_mock_weather_data("GH_001", days=2)
    second = get_mock_weather_data("GH_001", days=2)
    assert first == second
