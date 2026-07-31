"""HTTP-facing prediction helpers for the Salkım API.

Tries artifacts in this order:
1) calibrated XGBoost + LSTM ensemble
2) XGBoost harvest + RandomForest yield (joblib pipelines)
3) legacy ``models/maturity_model.pkl`` + ``models/yield_model.pkl``
4) statistical fallback
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"
MODELS_DIR = PROJECT_ROOT / "models"

ENSEMBLE_VERSION = "v1.1.0-xgb-lstm-ensemble"
XGB_VERSION = "v1.0.0-xgboost-harvest"
LEGACY_VERSION = "v1.0.0-xgboost"
FALLBACK_VERSION = "v0.1.0-statistical-fallback"

_CACHE: dict[str, Any] = {}


def _load_params() -> dict:
    if PARAMS_PATH.exists():
        with PARAMS_PATH.open(encoding="utf-8") as stream:
            return yaml.safe_load(stream) or {}
    return {}


def _resolve_path(key: str, default_relative: str) -> Path:
    params = _load_params()
    relative = params.get("paths", {}).get(key, default_relative)
    return PROJECT_ROOT / relative


def _get_cached(name: str, loader):
    if name not in _CACHE:
        _CACHE[name] = loader()
    return _CACHE[name]


def build_feature_row(
    *,
    crop_type: str,
    variety: str,
    avg_temperature_C: float,
    min_temperature_C: float,
    max_temperature_C: float,
    humidity_percent: float,
    co2_ppm: float,
    light_intensity_lux: float,
    photoperiod_hours: float,
    irrigation_mm: float,
    fertilizer_N_kg_ha: float,
    fertilizer_P_kg_ha: float,
    fertilizer_K_kg_ha: float,
    pest_severity: float,
    soil_pH: float,
    planting_date: date | str | None = None,
    greenhouse_id: str = "API_GH",
) -> pd.DataFrame:
    """Build one inference row with engineered features when possible."""
    if planting_date is None:
        planting_date = date.today()
    if isinstance(planting_date, str):
        planting_date = date.fromisoformat(planting_date)

    raw = pd.DataFrame(
        [
            {
                "greenhouse_id": greenhouse_id,
                "crop_type": crop_type,
                "variety": variety,
                "planting_date": planting_date.isoformat(),
                "avg_temperature_C": avg_temperature_C,
                "min_temperature_C": min_temperature_C,
                "max_temperature_C": max_temperature_C,
                "humidity_percent": humidity_percent,
                "co2_ppm": co2_ppm,
                "light_intensity_lux": light_intensity_lux,
                "photoperiod_hours": photoperiod_hours,
                "irrigation_mm": irrigation_mm,
                "fertilizer_N_kg_ha": fertilizer_N_kg_ha,
                "fertilizer_P_kg_ha": fertilizer_P_kg_ha,
                "fertilizer_K_kg_ha": fertilizer_K_kg_ha,
                "pest_severity": pest_severity,
                "soil_pH": soil_pH,
            }
        ]
    )

    try:
        from ml.prediction.features.feature_engineering import prepare_inference_features

        return prepare_inference_features(raw, params=_load_params())
    except Exception as exc:
        logger.warning("Feature engineering fallback to raw row: %s", exc)
        return raw


def _predict_yield(df: pd.DataFrame) -> float | None:
    yield_joblib = _resolve_path("model_output", "models/random_forest_yield_model.joblib")
    legacy_yield = MODELS_DIR / "yield_model.pkl"

    drop_columns = [
        "yield_kg_per_m2",
        "planting_date",
        "harvest_date",
        "days_to_maturity",
        "calculated_days_to_maturity",
    ]

    for path in (yield_joblib, legacy_yield):
        if not path.exists():
            continue
        try:
            model = _get_cached(f"yield:{path}", lambda p=path: joblib.load(p))
            X = df.drop(columns=drop_columns, errors="ignore")
            return float(model.predict(X)[0])
        except Exception as exc:
            logger.warning("Yield model failed (%s): %s", path, exc)
    return None


def _predict_days_xgb(df: pd.DataFrame) -> float | None:
    from ml.prediction.training.maturity_common import HARVEST_DROP_COLUMNS

    harvest_joblib = _resolve_path(
        "harvest_model_output", "models/xgboost_harvest_date_model.joblib"
    )
    legacy_maturity = MODELS_DIR / "maturity_model.pkl"

    for path in (harvest_joblib, legacy_maturity):
        if not path.exists():
            continue
        try:
            model = _get_cached(f"harvest:{path}", lambda p=path: joblib.load(p))
            X = df.drop(columns=HARVEST_DROP_COLUMNS, errors="ignore")
            # legacy model was trained without engineered columns; drop unknowns softly
            return float(model.predict(X)[0])
        except Exception as exc:
            logger.warning("Harvest XGB failed (%s): %s", path, exc)
    return None


def _predict_days_ensemble(df: pd.DataFrame) -> dict[str, Any] | None:
    ensemble_path = _resolve_path("ensemble_output", "models/maturity_ensemble.joblib")
    if not ensemble_path.exists():
        return None

    try:
        from ml.prediction.calibration.calibrate_maturity import apply_calibrator
        from ml.prediction.features.timeseries_builder import build_maturity_sequences
        from ml.prediction.training.maturity_common import HARVEST_DROP_COLUMNS
        from ml.prediction.training.train_ensemble import weighted_average
        from ml.prediction.training.train_lstm_maturity import scale_sequences
        from tensorflow import keras
    except Exception as exc:
        logger.warning("Ensemble imports unavailable: %s", exc)
        return None

    try:
        bundle = _get_cached("ensemble_bundle", lambda: joblib.load(ensemble_path))
        xgb_path = PROJECT_ROOT / bundle["xgb_model_path"]
        lstm_path = PROJECT_ROOT / bundle["lstm_model_path"]
        scaler_path = PROJECT_ROOT / bundle["lstm_scaler_path"]
        if not (xgb_path.exists() and lstm_path.exists() and scaler_path.exists()):
            return None

        xgb_model = _get_cached(f"xgb:{xgb_path}", lambda: joblib.load(xgb_path))
        lstm_model = _get_cached(
            f"lstm:{lstm_path}", lambda: keras.models.load_model(lstm_path)
        )
        scaler_bundle = _get_cached(
            f"scaler:{scaler_path}", lambda: joblib.load(scaler_path)
        )

        X_tab = df.drop(columns=HARVEST_DROP_COLUMNS, errors="ignore")
        xgb_pred = float(xgb_model.predict(X_tab)[0])

        lookback = int(bundle.get("lookback", 48))
        base_temp_c = float(bundle.get("base_temp_c", 10.0))
        sequences, _, _ = build_maturity_sequences(
            df,
            lookback=lookback,
            base_temp_c=base_temp_c,
            target_column=None,
        )
        scaled, _ = scale_sequences(
            sequences, scaler=scaler_bundle["scaler"], fit=False
        )
        lstm_pred = float(lstm_model.predict(scaled, verbose=0).reshape(-1)[0])
        blended = float(
            weighted_average(
                np.array([xgb_pred]),
                np.array([lstm_pred]),
                bundle["xgb_weight"],
                bundle["lstm_weight"],
            )[0]
        )
        calibrated = float(apply_calibrator(bundle["calibrator"], np.array([blended]))[0])

        return {
            "predicted_days_xgb": int(round(xgb_pred)),
            "predicted_days_lstm": int(round(lstm_pred)),
            "predicted_days_ensemble_raw": int(round(blended)),
            "predicted_days_remaining": int(round(calibrated)),
            "model_version": ENSEMBLE_VERSION,
        }
    except Exception as exc:
        logger.warning("Ensemble prediction failed: %s", exc)
        return None


def predict_harvest_payload(
    *,
    crop_type: str,
    variety: str,
    avg_temperature_C: float,
    min_temperature_C: float,
    max_temperature_C: float,
    humidity_percent: float,
    co2_ppm: float,
    light_intensity_lux: float,
    photoperiod_hours: float,
    irrigation_mm: float,
    fertilizer_N_kg_ha: float,
    fertilizer_P_kg_ha: float,
    fertilizer_K_kg_ha: float,
    pest_severity: float,
    soil_pH: float,
    planting_date: date | str | None = None,
    greenhouse_id: str = "API_GH",
    use_ensemble: bool = True,
) -> dict[str, Any]:
    """Return harvest + yield prediction for API responses."""
    if isinstance(planting_date, str):
        planting_date_obj = date.fromisoformat(planting_date)
    else:
        planting_date_obj = planting_date or date.today()

    df = build_feature_row(
        crop_type=crop_type,
        variety=variety,
        avg_temperature_C=avg_temperature_C,
        min_temperature_C=min_temperature_C,
        max_temperature_C=max_temperature_C,
        humidity_percent=humidity_percent,
        co2_ppm=co2_ppm,
        light_intensity_lux=light_intensity_lux,
        photoperiod_hours=photoperiod_hours,
        irrigation_mm=irrigation_mm,
        fertilizer_N_kg_ha=fertilizer_N_kg_ha,
        fertilizer_P_kg_ha=fertilizer_P_kg_ha,
        fertilizer_K_kg_ha=fertilizer_K_kg_ha,
        pest_severity=pest_severity,
        soil_pH=soil_pH,
        planting_date=planting_date_obj,
        greenhouse_id=greenhouse_id,
    )

    details: dict[str, Any] = {}
    days: float | None = None
    model_version = FALLBACK_VERSION
    confidence = 0.5

    if use_ensemble:
        ensemble = _predict_days_ensemble(df)
        if ensemble is not None:
            days = float(ensemble["predicted_days_remaining"])
            model_version = ensemble["model_version"]
            confidence = 0.88
            details = {
                "predicted_days_xgb": ensemble["predicted_days_xgb"],
                "predicted_days_lstm": ensemble["predicted_days_lstm"],
                "predicted_days_ensemble_raw": ensemble["predicted_days_ensemble_raw"],
            }

    if days is None:
        xgb_days = _predict_days_xgb(df)
        if xgb_days is not None:
            days = xgb_days
            model_version = XGB_VERSION if "xgboost_harvest" in str(
                _resolve_path("harvest_model_output", "models/xgboost_harvest_date_model.joblib")
            ) else LEGACY_VERSION
            # distinguish joblib vs legacy by path existence
            if _resolve_path(
                "harvest_model_output", "models/xgboost_harvest_date_model.joblib"
            ).exists():
                model_version = XGB_VERSION
            else:
                model_version = LEGACY_VERSION
            confidence = 0.82

    if days is None:
        days = 60.0
        model_version = FALLBACK_VERSION
        confidence = 0.5

    days_int = int(round(max(0, days)))
    harvest_date = planting_date_obj + timedelta(days=days_int)
    yield_value = _predict_yield(df)
    if yield_value is None:
        yield_value = 15.0
        confidence = min(confidence, 0.55)

    return {
        "predicted_days_remaining": days_int,
        "predicted_harvest_date": harvest_date,
        "predicted_yield_kg_m2": round(float(yield_value), 2),
        "confidence_score": round(float(confidence), 2),
        "model_version": model_version,
        "planting_date": planting_date_obj.isoformat(),
        "details": details,
        "forecasted_at": datetime.utcnow().isoformat() + "Z",
    }


def get_weather_payload(city: str = "İstanbul") -> dict[str, Any]:
    """City weather via Open-Meteo geocoding + 7-day forecast."""
    from ml.prediction.features.weather_provider import get_weather_by_city

    params = _load_params()
    weather_cfg = params.get("weather", {})
    return get_weather_by_city(city=city, config=weather_cfg)
