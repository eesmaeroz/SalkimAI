"""Feature engineering pipeline for greenhouse prediction datasets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ml.prediction.features.gdd_calculator import calculate_gdd
from ml.prediction.features.openweathermap_client import get_openweathermap_weather_data
from ml.prediction.features.weather_provider import (
    enrich_missing_weather_values,
    get_open_meteo_weather_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"


def load_params() -> dict:
    """Load project parameters from config/params.yaml."""
    with PARAMS_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_schema(params: dict) -> dict:
    """Load dataset schema from config/schema.yaml."""
    schema_path = PROJECT_ROOT / params["paths"]["schema"]
    with schema_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_required_columns(schema: dict) -> list[str]:
    """Return required input columns from the dataset schema."""
    return list(schema["dataset"]["required_columns"].keys())


def get_numeric_columns(schema: dict) -> list[str]:
    """Return numeric input columns from the dataset schema."""
    return [
        column
        for column, column_type in schema["dataset"]["required_columns"].items()
        if column_type == "numeric"
    ]


def validate_columns(df: pd.DataFrame, required_columns: list[str]) -> None:
    """Validate that the raw dataset contains all required columns."""
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(missing_columns)
            + "\nExpected columns: "
            + ", ".join(required_columns)
        )


def read_dataset(path: str | Path) -> pd.DataFrame:
    """Read a CSV dataset with a utf-8 fallback."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Raw data file not found: {path}. "
            "Add data/raw/greenhouse_data.csv or run python scripts/create_sample_data.py."
        )

    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="utf-8-sig")


def _fill_missing_from_openweathermap(
    df: pd.DataFrame,
    openweathermap_config: dict,
) -> pd.DataFrame:
    """Fill missing weather columns from OpenWeatherMap forecast summary."""
    weather_summary = get_openweathermap_weather_data(openweathermap_config)
    fillable_columns = (
        "avg_temperature_C",
        "min_temperature_C",
        "max_temperature_C",
        "humidity_percent",
    )

    df = df.copy()
    for column in fillable_columns:
        df[column] = df[column].fillna(weather_summary[column])
    return df


def _fill_missing_from_weather_summary(
    df: pd.DataFrame,
    weather_summary: dict,
) -> pd.DataFrame:
    """Fill standard project weather columns from a provider summary."""
    fillable_columns = (
        "avg_temperature_C",
        "min_temperature_C",
        "max_temperature_C",
        "humidity_percent",
    )

    df = df.copy()
    for column in fillable_columns:
        df[column] = df[column].fillna(weather_summary[column])
    return df


def clean_and_convert_types(
    df: pd.DataFrame,
    numeric_columns: list[str],
    weather_provider: str,
    use_mock_weather: bool,
    openweathermap_config: dict | None = None,
) -> pd.DataFrame:
    """Clean raw data, fill missing weather values and convert column types."""
    df = df.copy()

    if "data_source" not in df.columns:
        df["data_source"] = "real"

    if weather_provider == "mock" and use_mock_weather:
        df = pd.DataFrame(
            [enrich_missing_weather_values(row.to_dict()) for _, row in df.iterrows()]
        )
    elif weather_provider == "openweathermap":
        if openweathermap_config is None:
            raise ValueError("OpenWeatherMap config is required for openweathermap provider.")
        df = _fill_missing_from_openweathermap(df, openweathermap_config)
    elif weather_provider == "openmeteo":
        df = _fill_missing_from_weather_summary(
            df=df,
            weather_summary=get_open_meteo_weather_data(load_params()["weather"]),
        )
    elif weather_provider != "none":
        raise ValueError(
            "Unsupported weather_provider. Use one of: mock, openmeteo, openweathermap, none."
        )

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["planting_date"] = pd.to_datetime(df["planting_date"], errors="coerce")
    df["harvest_date"] = pd.to_datetime(df["harvest_date"], errors="coerce")

    if df["planting_date"].isna().any():
        raise ValueError("planting_date contains invalid dates. Example: 2025-03-15")

    if df["harvest_date"].isna().any():
        raise ValueError("harvest_date contains invalid dates. Example: 2025-07-01")

    return df


def create_features(df: pd.DataFrame, base_temp_c: float) -> pd.DataFrame:
    """Create model-ready features from cleaned greenhouse data."""
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

    df["temperature_range_C"] = df["max_temperature_C"] - df["min_temperature_C"]

    df["total_fertilizer_kg_ha"] = (
        df["fertilizer_N_kg_ha"]
        + df["fertilizer_P_kg_ha"]
        + df["fertilizer_K_kg_ha"]
    )

    safe_total_fertilizer = df["total_fertilizer_kg_ha"].replace(0, np.nan)
    df["N_ratio"] = df["fertilizer_N_kg_ha"] / safe_total_fertilizer
    df["P_ratio"] = df["fertilizer_P_kg_ha"] / safe_total_fertilizer
    df["K_ratio"] = df["fertilizer_K_kg_ha"] / safe_total_fertilizer

    df["light_exposure_index"] = df["light_intensity_lux"] * df["photoperiod_hours"]
    df["irrigation_per_day"] = df["irrigation_mm"] / df["days_to_maturity"].replace(
        0, np.nan
    )
    df["co2_light_interaction"] = df["co2_ppm"] * df["light_intensity_lux"]
    df["pest_health_score"] = 1 / (1 + df["pest_severity"])

    df = df.replace([np.inf, -np.inf], np.nan)

    for column in df.select_dtypes(include=["number"]).columns:
        df[column] = df[column].fillna(df[column].median())

    for column in df.select_dtypes(include=["object"]).columns:
        df[column] = df[column].fillna("unknown")

    return df


def save_feature_report(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    output_path: str | Path,
    weather_provider: str,
) -> None:
    """Save a JSON report describing generated features."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    added_features = [
        column for column in df_after.columns if column not in df_before.columns
    ]

    report = {
        "raw_shape": list(df_before.shape),
        "processed_shape": list(df_after.shape),
        "weather_provider": weather_provider,
        "data_sources": sorted(df_after["data_source"].dropna().unique().tolist()),
        "added_feature_count": len(added_features),
        "added_features": added_features,
        "missing_values_after_processing": int(df_after.isna().sum().sum()),
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)


def main() -> None:
    """Run the feature engineering stage."""
    params = load_params()
    schema = load_schema(params)

    raw_data_path = PROJECT_ROOT / params["paths"]["raw_data"]
    processed_data_path = PROJECT_ROOT / params["paths"]["processed_data"]
    feature_report_path = PROJECT_ROOT / params["paths"]["feature_report_output"]

    feature_params = params["feature_engineering"]
    base_temp_c = feature_params["tomato_base_temperature_C"]
    weather_provider = feature_params.get("weather_provider", "mock")
    use_mock_weather = feature_params["use_mock_weather_when_missing"]

    required_columns = get_required_columns(schema)
    numeric_columns = get_numeric_columns(schema)

    df_raw = read_dataset(raw_data_path)
    validate_columns(df_raw, required_columns)

    df_clean = clean_and_convert_types(
        df=df_raw,
        numeric_columns=numeric_columns,
        weather_provider=weather_provider,
        use_mock_weather=use_mock_weather,
        openweathermap_config=params.get("openweathermap"),
    )

    df_features = create_features(df=df_clean, base_temp_c=base_temp_c)

    processed_data_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(processed_data_path, index=False)

    save_feature_report(
        df_before=df_raw,
        df_after=df_features,
        output_path=feature_report_path,
        weather_provider=weather_provider,
    )

    print("Feature engineering completed.")
    print(f"Raw data: {raw_data_path}")
    print(f"Processed data: {processed_data_path}")
    print(f"Feature report: {feature_report_path}")
    print(f"Generated rows/columns: {df_features.shape}")


if __name__ == "__main__":
    main()
