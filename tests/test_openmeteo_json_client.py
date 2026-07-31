import pandas as pd
import pytest

from ml.prediction.features.weather_provider import (
    format_weather_report,
    summarize_open_meteo_forecast,
)


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
                "precipitation_probability_max": [40],
            }
        ),
    }

    summary = summarize_open_meteo_forecast(forecast)

    assert summary["avg_temperature_C"] == 21.0
    assert summary["min_temperature_C"] == 18.0
    assert summary["max_temperature_C"] == 30.0
    assert summary["humidity_percent"] == 75.0


def test_summarize_falls_back_to_current_when_hourly_empty():
    forecast = {
        "current": {
            "temperature_2m": 24.5,
            "relative_humidity_2m": 55,
        },
        "hourly": pd.DataFrame(
            columns=["date", "temperature_2m", "relative_humidity_2m", "wind_speed_10m"]
        ),
        "daily": pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-07-19"]),
                "temperature_2m_max": [29.0],
                "temperature_2m_min": [17.0],
                "weather_code": [2],
                "precipitation_probability_max": [10],
            }
        ),
    }

    summary = summarize_open_meteo_forecast(forecast)
    assert summary["avg_temperature_C"] == 24.5
    assert summary["humidity_percent"] == 55.0
    assert summary["min_temperature_C"] == 17.0
    assert summary["max_temperature_C"] == 29.0


def test_format_weather_report_matches_js_shape():
    location = {
        "name": "İstanbul",
        "admin1": "İstanbul",
        "country": "Türkiye",
        "latitude": 41.0082,
        "longitude": 28.9784,
    }
    forecast = {
        "current": {
            "temperature_2m": 22.0,
            "apparent_temperature": 21.0,
            "relative_humidity_2m": 60,
            "wind_speed_10m": 8.0,
            "precipitation": 0.0,
            "cloud_cover": 40,
            "weather_code": 1,
        },
        "hourly": pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-07-19T00:00"]),
                "temperature_2m": [22.0],
                "relative_humidity_2m": [60.0],
                "wind_speed_10m": [8.0],
            }
        ),
        "daily": pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-07-19", "2026-07-20"]),
                "temperature_2m_max": [28.0, 29.0],
                "temperature_2m_min": [18.0, 19.0],
                "weather_code": [1, 2],
                "precipitation_probability_max": [20, 35],
            }
        ),
    }

    report = format_weather_report(location, forecast)

    assert report["sehir"] == "İstanbul"
    assert report["koordinatlar"]["enlem"] == pytest.approx(41.0082)
    assert report["guncel"]["sicaklik"] == 22.0
    assert len(report["tahmin"]) == 2
    assert report["tahmin"][0]["tarih"] == "2026-07-19"
    assert report["tahmin"][1]["yagisIhtimali"] == 35
    assert "avg_temperature_C" in report["summary"]
