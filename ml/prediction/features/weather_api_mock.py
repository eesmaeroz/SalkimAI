"""Deterministic mock weather data for local development and tests."""
from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta


def _stable_seed(value: str) -> int:
    """
    Aynı greenhouse_id için her çalıştırmada benzer mock veri üretir.

    Böylece sistem test edilirken sonuçlar tamamen rastgele değişmez.
    """

    digest = hashlib.md5(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def get_mock_weather_data(greenhouse_id: str, days: int = 1) -> dict:
    """
    Gerçek hava API'si yerine sahte hava verisi üretir.

    Geliştirme aşamasında gerçek API anahtarı kullanmadan sistemi test etmek için yazılmıştır.

    Dönen değerler:
        avg_temperature_C
        min_temperature_C
        max_temperature_C
        humidity_percent
        co2_ppm
        light_intensity_lux
        photoperiod_hours
    """

    if not greenhouse_id:
        greenhouse_id = "UNKNOWN_GREENHOUSE"

    rng = random.Random(_stable_seed(str(greenhouse_id)))

    daily_weather = []
    start_day = date.today() - timedelta(days=days - 1)

    for i in range(days):
        min_temp = round(rng.uniform(15.0, 22.0), 2)
        max_temp = round(rng.uniform(25.0, 34.0), 2)
        avg_temp = round((min_temp + max_temp) / 2, 2)

        weather_row = {
            "date": str(start_day + timedelta(days=i)),
            "avg_temperature_C": avg_temp,
            "min_temperature_C": min_temp,
            "max_temperature_C": max_temp,
            "humidity_percent": round(rng.uniform(55.0, 80.0), 2),
            "co2_ppm": round(rng.uniform(380.0, 650.0), 2),
            "light_intensity_lux": round(rng.uniform(12000.0, 26000.0), 2),
            "photoperiod_hours": round(rng.uniform(10.0, 14.5), 2),
        }

        daily_weather.append(weather_row)

    latest_weather = daily_weather[-1].copy()
    latest_weather["greenhouse_id"] = greenhouse_id
    latest_weather["daily"] = daily_weather

    return latest_weather


def enrich_missing_weather_values(row: dict) -> dict:
    """
    Veri setindeki hava bilgileri eksikse mock hava verisiyle doldurur.

    Örneğin:
        avg_temperature_C boşsa
        min_temperature_C boşsa
        max_temperature_C boşsa

    Bu fonksiyon o değerleri sahte API verisiyle tamamlar.
    """

    greenhouse_id = str(row.get("greenhouse_id", "UNKNOWN_GREENHOUSE"))
    mock_weather = get_mock_weather_data(greenhouse_id)

    weather_columns = [
        "avg_temperature_C",
        "min_temperature_C",
        "max_temperature_C",
        "humidity_percent",
        "co2_ppm",
        "light_intensity_lux",
        "photoperiod_hours",
    ]

    for column in weather_columns:
        value = row.get(column)

        if value is None or value == "" or str(value).lower() == "nan":
            row[column] = mock_weather[column]

    return row