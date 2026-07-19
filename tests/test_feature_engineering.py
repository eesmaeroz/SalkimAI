import pandas as pd

from ml.prediction.features.feature_engineering import (
    clean_and_convert_types,
    create_features,
    validate_columns,
)


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


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "greenhouse_id": "GH_001",
                "crop_type": "tomato",
                "variety": "Black Krim",
                "planting_date": "2025-01-01",
                "harvest_date": "2025-03-22",
                "days_to_maturity": 80,
                "avg_temperature_C": 22,
                "min_temperature_C": 16,
                "max_temperature_C": 28,
                "humidity_percent": 65,
                "co2_ppm": 420,
                "light_intensity_lux": 18000,
                "photoperiod_hours": 12,
                "irrigation_mm": 240,
                "fertilizer_N_kg_ha": 120,
                "fertilizer_P_kg_ha": 60,
                "fertilizer_K_kg_ha": 140,
                "pest_severity": 1,
                "soil_pH": 6.5,
                "yield_kg_per_m2": 12.5,
            }
        ]
    )


def test_validate_columns_rejects_missing_required_column():
    df = _sample_df().drop(columns=["yield_kg_per_m2"])

    try:
        validate_columns(df, REQUIRED_COLUMNS)
    except ValueError as error:
        assert "yield_kg_per_m2" in str(error)
    else:
        raise AssertionError("Expected missing required column validation to fail")


def test_clean_and_convert_types_adds_real_data_source_when_missing():
    df = clean_and_convert_types(
        df=_sample_df(),
        numeric_columns=NUMERIC_COLUMNS,
        weather_provider="none",
        use_mock_weather=False,
    )

    assert df.loc[0, "data_source"] == "real"
    assert pd.api.types.is_datetime64_any_dtype(df["planting_date"])


def test_create_features_adds_expected_columns():
    cleaned = clean_and_convert_types(
        df=_sample_df(),
        numeric_columns=NUMERIC_COLUMNS,
        weather_provider="none",
        use_mock_weather=False,
    )
    featured = create_features(cleaned, base_temp_c=10)

    assert "gdd" in featured.columns
    assert "light_exposure_index" in featured.columns
    assert featured.loc[0, "gdd"] == 12
