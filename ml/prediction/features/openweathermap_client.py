"""Production-oriented OpenWeatherMap client.

The API key is intentionally read from an environment variable instead of being
stored in config files. This keeps local development and future deployment safe.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests_cache
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"


def load_openweathermap_config() -> dict[str, Any]:
    with PARAMS_PATH.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)["openweathermap"]


def fetch_openweathermap_forecast(
    api_key: str,
    latitude: float,
    longitude: float,
    api_url: str = "https://api.openweathermap.org/data/2.5/forecast",
    units: str = "metric",
    cache_path: str | Path = ".cache/openweathermap",
    expire_after: int = 3600,
    timeout_seconds: int = 20,
) -> pd.DataFrame:
    """Fetch 5-day / 3-hour forecast data from OpenWeatherMap."""
    if not api_key:
        raise ValueError("OpenWeatherMap API key is empty.")

    cache_file = Path(cache_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    session = requests_cache.CachedSession(str(cache_file), expire_after=expire_after)

    response = session.get(
        api_url,
        params={
            "lat": latitude,
            "lon": longitude,
            "appid": api_key,
            "units": units,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()

    rows: list[dict[str, Any]] = []
    for item in payload.get("list", []):
        main = item.get("main", {})
        weather = item.get("weather", [{}])[0]
        rows.append(
            {
                "date": pd.to_datetime(item.get("dt"), unit="s", utc=True),
                "temperature_2m": main.get("temp"),
                "temperature_2m_min": main.get("temp_min"),
                "temperature_2m_max": main.get("temp_max"),
                "relative_humidity_2m": main.get("humidity"),
                "weather_code": weather.get("id"),
                "weather_description": weather.get("description"),
            }
        )

    return pd.DataFrame(rows)


def summarize_openweathermap_forecast(forecast: pd.DataFrame) -> dict[str, Any]:
    """Convert OpenWeatherMap forecast rows into the project's weather fields."""
    if forecast.empty:
        raise ValueError("OpenWeatherMap forecast response is empty.")

    return {
        "avg_temperature_C": float(forecast["temperature_2m"].mean()),
        "min_temperature_C": float(forecast["temperature_2m_min"].min()),
        "max_temperature_C": float(forecast["temperature_2m_max"].max()),
        "humidity_percent": float(forecast["relative_humidity_2m"].mean()),
    }


def get_openweathermap_weather_data(config: dict[str, Any]) -> dict[str, Any]:
    """Fetch and summarize OpenWeatherMap data using config/env settings."""
    api_key = os.getenv(config["api_key_env"], "")
    forecast = fetch_openweathermap_forecast(
        api_key=api_key,
        latitude=config["latitude"],
        longitude=config["longitude"],
        api_url=config["api_url"],
        units=config["units"],
        cache_path=PROJECT_ROOT / ".cache" / "openweathermap",
        expire_after=config["cache_expire_seconds"],
        timeout_seconds=config["timeout_seconds"],
    )
    return summarize_openweathermap_forecast(forecast)


def main() -> None:
    config = load_openweathermap_config()
    api_key = os.getenv(config["api_key_env"], "")

    forecast = fetch_openweathermap_forecast(
        api_key=api_key,
        latitude=config["latitude"],
        longitude=config["longitude"],
        api_url=config["api_url"],
        units=config["units"],
        cache_path=PROJECT_ROOT / ".cache" / "openweathermap",
        expire_after=config["cache_expire_seconds"],
        timeout_seconds=config["timeout_seconds"],
    )
    print(forecast)


if __name__ == "__main__":
    main()
