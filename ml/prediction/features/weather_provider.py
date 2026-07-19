"""Weather providers: Open-Meteo JSON client and deterministic offline mock.

The mock functions keep feature engineering repeatable in tests. The live
Open-Meteo client uses the public JSON forecast endpoint, matching the curl
format shown in the project notes.
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests_cache
import yaml


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LATITUDE = 40.8991
DEFAULT_LONGITUDE = 31.1888


def fetch_open_meteo_forecast(
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    cache_path: str | Path = ".cache/openmeteo",
    expire_after: int = 3600,
    retries: int = 5,
    backoff_factor: float = 0.2,
    api_url: str = OPEN_METEO_URL,
) -> dict[str, Any]:
    """Fetch current, hourly and daily weather from Open-Meteo JSON API."""
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    session = requests_cache.CachedSession(str(cache_path), expire_after=expire_after)

    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "auto",
    }
    last_error: Exception | None = None
    for _ in range(max(int(retries), 1)):
        try:
            response = session.get(api_url, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as error:  # pragma: no cover - network fallback path
            last_error = error
    else:
        raise RuntimeError("Open-Meteo request failed.") from last_error

    current_payload = payload.get("current", {})
    current_data = {
        "time": pd.to_datetime(current_payload.get("time")),
        "temperature_2m": current_payload.get("temperature_2m"),
        "relative_humidity_2m": current_payload.get("relative_humidity_2m"),
        "wind_speed_10m": current_payload.get("wind_speed_10m"),
    }

    hourly_payload = payload.get("hourly", {})
    hourly_dataframe = pd.DataFrame(
        {
            "date": pd.to_datetime(hourly_payload.get("time", [])),
            "temperature_2m": hourly_payload.get("temperature_2m", []),
            "relative_humidity_2m": hourly_payload.get("relative_humidity_2m", []),
            "wind_speed_10m": hourly_payload.get("wind_speed_10m", []),
        }
    )

    daily_payload = payload.get("daily", {})
    daily_dataframe = pd.DataFrame(
        {
            "date": pd.to_datetime(daily_payload.get("time", [])),
            "temperature_2m_max": daily_payload.get("temperature_2m_max", []),
            "temperature_2m_min": daily_payload.get("temperature_2m_min", []),
            "weather_code": daily_payload.get("weather_code", []),
        }
    )

    return {
        "metadata": {
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "elevation": payload.get("elevation"),
            "timezone": payload.get("timezone"),
        },
        "current": current_data,
        "hourly": hourly_dataframe,
        "daily": daily_dataframe,
    }


def summarize_open_meteo_forecast(forecast: dict[str, Any]) -> dict[str, Any]:
    """Convert Open-Meteo JSON forecast output into project weather fields."""
    daily = forecast["daily"]
    hourly = forecast["hourly"]
    if daily.empty and hourly.empty:
        raise ValueError("Open-Meteo forecast response is empty.")

    return {
        "avg_temperature_C": float(hourly["temperature_2m"].mean()),
        "min_temperature_C": float(daily["temperature_2m_min"].min()),
        "max_temperature_C": float(daily["temperature_2m_max"].max()),
        "humidity_percent": float(hourly["relative_humidity_2m"].mean()),
    }


def get_open_meteo_weather_data(config: dict[str, Any]) -> dict[str, Any]:
    """Fetch and summarize Open-Meteo data using project config."""
    forecast = fetch_open_meteo_forecast(
        latitude=config["latitude"],
        longitude=config["longitude"],
        cache_path=Path(__file__).resolve().parents[3] / ".cache" / "openmeteo_json",
        expire_after=config["cache_expire_seconds"],
        retries=config["retries"],
        backoff_factor=config["backoff_factor"],
        api_url=config["api_url"],
    )
    return summarize_open_meteo_forecast(forecast)


def _stable_seed(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest()[:8], 16)


def get_mock_weather_data(
    greenhouse_id: str, days: int = 1, end_date: date | None = None
) -> dict[str, Any]:
    """Return stable synthetic weather without calling the internet."""
    if days < 1:
        raise ValueError("days must be at least 1")

    greenhouse_id = greenhouse_id or "UNKNOWN_GREENHOUSE"
    rng = random.Random(_stable_seed(str(greenhouse_id)))
    final_day = end_date or date(2025, 6, 30)
    start_day = final_day - timedelta(days=days - 1)
    rows = []

    for offset in range(days):
        minimum = round(rng.uniform(15.0, 22.0), 2)
        maximum = round(rng.uniform(25.0, 34.0), 2)
        rows.append(
            {
                "date": str(start_day + timedelta(days=offset)),
                "avg_temperature_C": round((minimum + maximum) / 2, 2),
                "min_temperature_C": minimum,
                "max_temperature_C": maximum,
                "humidity_percent": round(rng.uniform(55.0, 80.0), 2),
                "co2_ppm": round(rng.uniform(380.0, 650.0), 2),
                "light_intensity_lux": round(rng.uniform(12000.0, 26000.0), 2),
                "photoperiod_hours": round(rng.uniform(10.0, 14.5), 2),
            }
        )

    latest = {**rows[-1], "greenhouse_id": greenhouse_id, "daily": rows}
    return latest


def enrich_missing_weather_values(row: dict[str, Any]) -> dict[str, Any]:
    """Fill missing greenhouse weather fields from the deterministic mock."""
    result = row.copy()
    mock = get_mock_weather_data(str(result.get("greenhouse_id", "UNKNOWN_GREENHOUSE")))
    columns = (
        "avg_temperature_C",
        "min_temperature_C",
        "max_temperature_C",
        "humidity_percent",
        "co2_ppm",
        "light_intensity_lux",
        "photoperiod_hours",
    )
    for column in columns:
        value = result.get(column)
        if value is None or value == "" or pd.isna(value):
            result[column] = mock[column]
    return result


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    with (project_root / "config" / "params.yaml").open(encoding="utf-8") as stream:
        weather = yaml.safe_load(stream)["weather"]

    forecast = fetch_open_meteo_forecast(
        latitude=weather["latitude"],
        longitude=weather["longitude"],
        cache_path=project_root / ".cache" / "openmeteo",
        expire_after=weather["cache_expire_seconds"],
        retries=weather["retries"],
        backoff_factor=weather["backoff_factor"],
        api_url=weather["api_url"],
    )
    print("Metadata:", forecast["metadata"])
    print("Current:", forecast["current"])
    print("\nHourly weather\n", forecast["hourly"])
    print("\nDaily weather\n", forecast["daily"])


if __name__ == "__main__":
    main()
