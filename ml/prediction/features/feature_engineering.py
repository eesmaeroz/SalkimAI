"""Feature engineering entry points."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ml.prediction.features.gdd_calculator import calculate_gdd
from ml.prediction.features.weather_api_mock import enrich_missing_weather_values


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"


REQUIRED_COLUMNS = [
    "greenhouse_id",
    "crop_type",
    "variety",
    "planting_date",
    "harvest_date",
    "days_to_maturity",
    "avg_temperature_C",
    "min_temperature_C",
    "max_temperature_C",
    "humidity_percent",
    "co2_ppm",
    "light_intensity_lux",
    "photoperiod_hours",
    "irrigation_mm",
    "fertilizer_N_kg_ha",
    "fertilizer_P_kg_ha",
    "fertilizer_K_kg_ha",
    "pest_severity",
    "soil_pH",
    "yield_kg_per_m2",
]


NUMERIC_COLUMNS = [
    "days_to_maturity",
    "avg_temperature_C",
    "min_temperature_C",
    "max_temperature_C",
    "humidity_percent",
    "co2_ppm",
    "light_intensity_lux",
    "photoperiod_hours",
    "irrigation_mm",
    "fertilizer_N_kg_ha",
    "fertilizer_P_kg_ha",
    "fertilizer_K_kg_ha",
    "pest_severity",
    "soil_pH",
    "yield_kg_per_m2",
]


def load_params() -> dict:
    """
    config/params.yaml dosyasını okur.
    """

    with open(PARAMS_PATH, "r", encoding="utf-8") as file:
        params = yaml.safe_load(file)

    return params


def validate_columns(df: pd.DataFrame) -> None:
    """
    Veri setinde beklenen sütunlar var mı kontrol eder.
    Eksik sütun varsa hata verir.
    """

    missing_columns = []

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(
            "Veri setinde eksik sütunlar var: "
            + ", ".join(missing_columns)
            + "\nBeklenen sütunlar: "
            + ", ".join(REQUIRED_COLUMNS)
        )


def read_dataset(path: str | Path) -> pd.DataFrame:
    """
    CSV veri setini okur.
    Türkçe karakter veya encoding sorunu olursa utf-8-sig ile tekrar dener.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Veri dosyası bulunamadı: {path}. "
            "Önce data/raw/greenhouse_data.csv dosyasını ekle "
            "veya python scripts/create_sample_data.py komutunu çalıştır."
        )

    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8-sig")

    return df


def clean_and_convert_types(
    df: pd.DataFrame,
    use_mock_weather: bool,
) -> pd.DataFrame:
    """
    Veri temizleme ve tip dönüştürme işlemlerini yapar.

    Yapılan işlemler:
        - Eksik hava değerlerini mock API ile doldurur.
        - Sayısal sütunları numeric tipe çevirir.
        - Tarih sütunlarını datetime tipine çevirir.
    """

    df = df.copy()

    if use_mock_weather:
        enriched_rows = []

        for _, row in df.iterrows():
            enriched_row = enrich_missing_weather_values(row.to_dict())
            enriched_rows.append(enriched_row)

        df = pd.DataFrame(enriched_rows)

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["planting_date"] = pd.to_datetime(df["planting_date"], errors="coerce")
    df["harvest_date"] = pd.to_datetime(df["harvest_date"], errors="coerce")

    if df["planting_date"].isna().any():
        raise ValueError(
            "planting_date sütununda dönüştürülemeyen tarih var. "
            "Örnek doğru format: 2025-03-15"
        )

    if df["harvest_date"].isna().any():
        raise ValueError(
            "harvest_date sütununda dönüştürülemeyen tarih var. "
            "Örnek doğru format: 2025-07-01"
        )

    return df


def create_features(
    df: pd.DataFrame,
    base_temp_c: float,
) -> pd.DataFrame:
    """
    Ham sera verisinden yeni özellikler üretir.

    Üretilen feature'lar:
        - calculated_days_to_maturity
        - gdd
        - temperature_range_C
        - total_fertilizer_kg_ha
        - N_ratio
        - P_ratio
        - K_ratio
        - light_exposure_index
        - irrigation_per_day
        - co2_light_interaction
        - pest_health_score
    """

    df = df.copy()

    df["calculated_days_to_maturity"] = (
        df["harvest_date"] - df["planting_date"]
    ).dt.days

    df["days_to_maturity"] = df["days_to_maturity"].fillna(
        df["calculated_days_to_maturity"]
    )

    df["gdd"] = df.apply(
        lambda row: calculate_gdd(
            min_temp_c=row["min_temperature_C"],
            max_temp_c=row["max_temperature_C"],
            base_temp_c=base_temp_c,
        ),
        axis=1,
    )

    df["temperature_range_C"] = (
        df["max_temperature_C"] - df["min_temperature_C"]
    )

    df["total_fertilizer_kg_ha"] = (
        df["fertilizer_N_kg_ha"]
        + df["fertilizer_P_kg_ha"]
        + df["fertilizer_K_kg_ha"]
    )

    safe_total_fertilizer = df["total_fertilizer_kg_ha"].replace(0, np.nan)

    df["N_ratio"] = df["fertilizer_N_kg_ha"] / safe_total_fertilizer
    df["P_ratio"] = df["fertilizer_P_kg_ha"] / safe_total_fertilizer
    df["K_ratio"] = df["fertilizer_K_kg_ha"] / safe_total_fertilizer

    df["light_exposure_index"] = (
        df["light_intensity_lux"] * df["photoperiod_hours"]
    )

    df["irrigation_per_day"] = (
        df["irrigation_mm"] / df["days_to_maturity"].replace(0, np.nan)
    )

    df["co2_light_interaction"] = (
        df["co2_ppm"] * df["light_intensity_lux"]
    )

    df["pest_health_score"] = 1 / (1 + df["pest_severity"])

    df = df.replace([np.inf, -np.inf], np.nan)

    numeric_columns = df.select_dtypes(include=["number"]).columns

    for column in numeric_columns:
        df[column] = df[column].fillna(df[column].median())

    text_columns = df.select_dtypes(include=["object"]).columns

    for column in text_columns:
        df[column] = df[column].fillna("unknown")

    return df


def save_feature_report(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """
    Feature engineering sonucunda oluşan raporu JSON olarak kaydeder.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    added_features = []

    for column in df_after.columns:
        if column not in df_before.columns:
            added_features.append(column)

    report = {
        "raw_shape": list(df_before.shape),
        "processed_shape": list(df_after.shape),
        "added_feature_count": len(added_features),
        "added_features": added_features,
        "missing_values_after_processing": int(df_after.isna().sum().sum()),
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)


def main() -> None:
    """
    Feature engineering pipeline ana fonksiyonu.
    """

    params = load_params()

    raw_data_path = PROJECT_ROOT / params["paths"]["raw_data"]
    processed_data_path = PROJECT_ROOT / params["paths"]["processed_data"]
    feature_report_path = PROJECT_ROOT / params["paths"]["feature_report_output"]

    base_temp_c = params["feature_engineering"]["tomato_base_temperature_C"]
    use_mock_weather = params["feature_engineering"]["use_mock_weather_when_missing"]

    df_raw = read_dataset(raw_data_path)

    validate_columns(df_raw)

    df_clean = clean_and_convert_types(
        df=df_raw,
        use_mock_weather=use_mock_weather,
    )

    df_features = create_features(
        df=df_clean,
        base_temp_c=base_temp_c,
    )

    processed_data_path.parent.mkdir(parents=True, exist_ok=True)

    df_features.to_csv(processed_data_path, index=False)

    save_feature_report(
        df_before=df_raw,
        df_after=df_features,
        output_path=feature_report_path,
    )

    print("Feature engineering tamamlandı.")
    print(f"Ham veri: {raw_data_path}")
    print(f"İşlenmiş veri: {processed_data_path}")
    print(f"Feature raporu: {feature_report_path}")
    print(f"Üretilen satır/sütun: {df_features.shape}")


if __name__ == "__main__":
    main()