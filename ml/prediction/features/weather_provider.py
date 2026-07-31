"""Weather providers: Open-Meteo geocoding + forecast, and offline mock.

Live flow mirrors the project JS helper:
1) resolve city -> lat/lon via Open-Meteo geocoding
2) fetch current + 7-day daily forecast from the forecast API
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
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
DEFAULT_LATITUDE = 41.0082
DEFAULT_LONGITUDE = 28.9784
DEFAULT_CITY = "İstanbul"
DEFAULT_TIMEZONE = "Europe/Istanbul"
DEFAULT_FORECAST_DAYS = 7

CURRENT_FIELDS = (
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
)
DAILY_FIELDS = (
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
)


def _cached_session(cache_path: str | Path, expire_after: int) -> requests_cache.CachedSession:
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    return requests_cache.CachedSession(str(cache_path), expire_after=expire_after)


def resolve_city_location(
    city: str = DEFAULT_CITY,
    *,
    language: str = "tr",
    count: int = 1,
    geocoding_url: str = OPEN_METEO_GEOCODING_URL,
    cache_path: str | Path = ".cache/openmeteo_geocoding",
    expire_after: int = 3600,
    retries: int = 5,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    """Resolve a city name to coordinates via Open-Meteo geocoding."""
    if not city or not str(city).strip():
        raise ValueError("city must be a non-empty string.")

    session = _cached_session(cache_path, expire_after)
    params = {
        "name": str(city).strip(),
        "count": int(count),
        "language": language,
        "format": "json",
    }

    last_error: Exception | None = None
    payload: dict[str, Any] | None = None
    for _ in range(max(int(retries), 1)):
        try:
            response = session.get(geocoding_url, params=params, timeout=timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            break
        except Exception as error:  # pragma: no cover - network fallback path
            last_error = error
    else:
        raise RuntimeError("Open-Meteo geocoding request failed.") from last_error

    results = (payload or {}).get("results") or []
    if not results:
        raise ValueError(f"City not found: {city}")

    location = results[0]
    return {
        "name": location.get("name"),
        "admin1": location.get("admin1"),
        "country": location.get("country"),
        "latitude": float(location["latitude"]),
        "longitude": float(location["longitude"]),
        "timezone": location.get("timezone"),
    }


def fetch_open_meteo_forecast(
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    cache_path: str | Path = ".cache/openmeteo",
    expire_after: int = 3600,
    retries: int = 5,
    backoff_factor: float = 0.2,
    api_url: str = OPEN_METEO_URL,
    timezone: str = DEFAULT_TIMEZONE,
    forecast_days: int = DEFAULT_FORECAST_DAYS,
    include_hourly: bool = True,
) -> dict[str, Any]:
    """Fetch current and daily weather from Open-Meteo forecast API.

    Default fields match:
    current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,
            weather_code,cloud_cover,wind_speed_10m
    daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max
    """
    _ = backoff_factor  # kept for config compatibility
    session = _cached_session(cache_path, expire_after)

    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(CURRENT_FIELDS),
        "daily": ",".join(DAILY_FIELDS),
        "timezone": timezone,
        "forecast_days": int(forecast_days),
    }
    if include_hourly:
        params["hourly"] = "temperature_2m,relative_humidity_2m,wind_speed_10m"

    last_error: Exception | None = None
    payload: dict[str, Any] | None = None
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

    assert payload is not None
    current_payload = payload.get("current", {})
    current_data = {
        "time": pd.to_datetime(current_payload.get("time")),
        "temperature_2m": current_payload.get("temperature_2m"),
        "relative_humidity_2m": current_payload.get("relative_humidity_2m"),
        "apparent_temperature": current_payload.get("apparent_temperature"),
        "precipitation": current_payload.get("precipitation"),
        "weather_code": current_payload.get("weather_code"),
        "cloud_cover": current_payload.get("cloud_cover"),
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
            "precipitation_probability_max": daily_payload.get(
                "precipitation_probability_max", []
            ),
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
    """Convert Open-Meteo forecast output into project weather fields."""
    daily = forecast["daily"]
    hourly = forecast["hourly"]
    current = forecast.get("current", {})

    if daily.empty and hourly.empty and current.get("temperature_2m") is None:
        raise ValueError("Open-Meteo forecast response is empty.")

    if not hourly.empty:
        avg_temperature = float(hourly["temperature_2m"].mean())
        humidity = float(hourly["relative_humidity_2m"].mean())
    else:
        avg_temperature = float(current["temperature_2m"])
        humidity = float(current.get("relative_humidity_2m") or 0.0)

    if not daily.empty:
        min_temperature = float(daily["temperature_2m_min"].min())
        max_temperature = float(daily["temperature_2m_max"].max())
    else:
        min_temperature = avg_temperature
        max_temperature = avg_temperature

    return {
        "avg_temperature_C": avg_temperature,
        "min_temperature_C": min_temperature,
        "max_temperature_C": max_temperature,
        "humidity_percent": humidity,
    }


def format_weather_report(
    location: dict[str, Any],
    forecast: dict[str, Any],
) -> dict[str, Any]:
    """Shape location + forecast into the JS-style weather report."""
    current = forecast["current"]
    daily = forecast["daily"]

    tahmin: list[dict[str, Any]] = []
    if not daily.empty:
        for index, row in daily.iterrows():
            tarih = row["date"]
            tahmin.append(
                {
                    "tarih": str(pd.Timestamp(tarih).date()),
                    "enYuksek": row.get("temperature_2m_max"),
                    "enDusuk": row.get("temperature_2m_min"),
                    "yagisIhtimali": row.get("precipitation_probability_max"),
                    "durumKodu": row.get("weather_code"),
                }
            )

    return {
        "sehir": location.get("name"),
        "il": location.get("admin1"),
        "ulke": location.get("country"),
        "koordinatlar": {
            "enlem": location.get("latitude"),
            "boylam": location.get("longitude"),
        },
        "guncel": {
            "sicaklik": current.get("temperature_2m"),
            "hissedilen": current.get("apparent_temperature"),
            "nem": current.get("relative_humidity_2m"),
            "ruzgar": current.get("wind_speed_10m"),
            "yagis": current.get("precipitation"),
            "bulutluluk": current.get("cloud_cover"),
            "durumKodu": current.get("weather_code"),
        },
        "tahmin": tahmin,
        "summary": summarize_open_meteo_forecast(forecast),
    }


def get_weather_by_city(
    city: str = DEFAULT_CITY,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """City-based weather: geocode then fetch Open-Meteo forecast."""
    project_root = Path(__file__).resolve().parents[3]
    config = config or {}

    location = resolve_city_location(
        city=city,
        language=config.get("geocoding_language", "tr"),
        geocoding_url=config.get("geocoding_url", OPEN_METEO_GEOCODING_URL),
        cache_path=project_root / ".cache" / "openmeteo_geocoding",
        expire_after=int(config.get("cache_expire_seconds", 3600)),
        retries=int(config.get("retries", 5)),
    )

    forecast = fetch_open_meteo_forecast(
        latitude=location["latitude"],
        longitude=location["longitude"],
        cache_path=project_root / ".cache" / "openmeteo_json",
        expire_after=int(config.get("cache_expire_seconds", 3600)),
        retries=int(config.get("retries", 5)),
        backoff_factor=float(config.get("backoff_factor", 0.2)),
        api_url=config.get("api_url", OPEN_METEO_URL),
        timezone=config.get("timezone") or location.get("timezone") or DEFAULT_TIMEZONE,
        forecast_days=int(config.get("forecast_days", DEFAULT_FORECAST_DAYS)),
        include_hourly=bool(config.get("include_hourly", True)),
    )
    return format_weather_report(location, forecast)


def hava_durumu_getir(
    sehir: str = DEFAULT_CITY,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Turkish alias for ``get_weather_by_city``."""
    return get_weather_by_city(city=sehir, config=config)


def get_open_meteo_weather_data(config: dict[str, Any]) -> dict[str, Any]:
    """Fetch and summarize Open-Meteo data using project config.

    Prefer ``city`` (geocoding). Fall back to configured lat/lon.
    """
    project_root = Path(__file__).resolve().parents[3]
    city = config.get("city")
    if city:
        report = get_weather_by_city(city=str(city), config=config)
        return report["summary"]

    forecast = fetch_open_meteo_forecast(
        latitude=float(config.get("latitude", DEFAULT_LATITUDE)),
        longitude=float(config.get("longitude", DEFAULT_LONGITUDE)),
        cache_path=project_root / ".cache" / "openmeteo_json",
        expire_after=int(config.get("cache_expire_seconds", 3600)),
        retries=int(config.get("retries", 5)),
        backoff_factor=float(config.get("backoff_factor", 0.2)),
        api_url=config.get("api_url", OPEN_METEO_URL),
        timezone=config.get("timezone", DEFAULT_TIMEZONE),
        forecast_days=int(config.get("forecast_days", DEFAULT_FORECAST_DAYS)),
        include_hourly=bool(config.get("include_hourly", True)),
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

    city = weather.get("city", DEFAULT_CITY)
    report = get_weather_by_city(city=city, config=weather)
    print("Şehir:", report["sehir"], report["il"], report["ulke"])
    print("Koordinatlar:", report["koordinatlar"])
    print("Güncel:", report["guncel"])
    print("\n7 günlük tahmin:")
    for day in report["tahmin"]:
        print(day)
    print("\nFeature summary:", report["summary"])


if __name__ == "__main__":
    main()
