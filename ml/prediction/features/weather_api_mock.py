"""Open-Meteo client and deterministic offline weather mock.

The mock functions keep feature engineering repeatable in tests. The live client
uses the Open-Meteo FlatBuffers SDK with an on-disk, one-hour response cache and
automatic retries.
"""

from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LATITUDE = 40.8991
DEFAULT_LONGITUDE = 31.1888


def _date_range(section: Any) -> pd.DatetimeIndex:
    return pd.date_range(
        start=pd.to_datetime(section.Time(), unit="s", utc=True),
        end=pd.to_datetime(section.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=section.Interval()),
        inclusive="left",
    )


def fetch_open_meteo_forecast(
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    cache_path: str | Path = ".cache/openmeteo",
    expire_after: int = 3600,
    retries: int = 5,
    backoff_factor: float = 0.2,
) -> dict[str, Any]:
    """Fetch current, hourly and daily weather for the configured location."""
    # Imports stay local so offline mock usage does not require network packages.
    import openmeteo_requests
    import requests_cache
    from retry_requests import retry

    cache_file = Path(cache_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_session = requests_cache.CachedSession(
        str(cache_file), expire_after=expire_after
    )
    retry_session = retry(
        cache_session, retries=retries, backoff_factor=backoff_factor
    )
    client = openmeteo_requests.Client(session=retry_session)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
        "hourly": "temperature_2m",
        "current": ["temperature_2m", "relative_humidity_2m"],
        "timezone": "auto",
    }
    response = client.weather_api(OPEN_METEO_URL, params=params)[0]

    current = response.Current()
    current_data = {
        "time": pd.to_datetime(current.Time(), unit="s", utc=True),
        "temperature_2m": float(current.Variables(0).Value()),
        "relative_humidity_2m": float(current.Variables(1).Value()),
    }

    hourly = response.Hourly()
    hourly_dataframe = pd.DataFrame(
        {
            "date": _date_range(hourly),
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        }
    )

    daily = response.Daily()
    daily_dataframe = pd.DataFrame(
        {
            "date": _date_range(daily),
            "temperature_2m_max": daily.Variables(0).ValuesAsNumpy(),
            "temperature_2m_min": daily.Variables(1).ValuesAsNumpy(),
            "weather_code": daily.Variables(2).ValuesAsNumpy(),
        }
    )

    return {
        "metadata": {
            "latitude": response.Latitude(),
            "longitude": response.Longitude(),
            "elevation": response.Elevation(),
            "utc_offset_seconds": response.UtcOffsetSeconds(),
        },
        "current": current_data,
        "hourly": hourly_dataframe,
        "daily": daily_dataframe,
    }


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
    forecast = fetch_open_meteo_forecast()
    print("Metadata:", forecast["metadata"])
    print("Current:", forecast["current"])
    print("\nHourly weather\n", forecast["hourly"])
    print("\nDaily weather\n", forecast["daily"])


if __name__ == "__main__":
    main()
