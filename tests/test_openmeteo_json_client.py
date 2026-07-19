import pandas as pd

from ml.prediction.features.weather_provider import summarize_open_meteo_forecast


def test_summarize_open_meteo_forecast_matches_json_shape():
    forecast = {
        "current": {
            "time": pd.Timestamp("2026-07-19T12:00:00"),
            "temperature_2m": 25.0,
            "relative_humidity_2m": 60,
            "wind_speed_10m": 10,
        },
        "hourly": pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-07-19T00:00", "2026-07-19T01:00"]),
                "temperature_2m": [20.0, 22.0],
                "relative_humidity_2m": [70.0, 80.0],
                "wind_speed_10m": [5.0, 6.0],
            }
        ),
        "daily": pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-07-19"]),
                "temperature_2m_max": [30.0],
                "temperature_2m_min": [18.0],
                "weather_code": [1],
            }
        ),
    }

    summary = summarize_open_meteo_forecast(forecast)

    assert summary["avg_temperature_C"] == 21.0
    assert summary["min_temperature_C"] == 18.0
    assert summary["max_temperature_C"] == 30.0
    assert summary["humidity_percent"] == 75.0
