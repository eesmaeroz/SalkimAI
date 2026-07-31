"""Predict harvest dates with the calibrated XGBoost + LSTM ensemble."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml

from ml.prediction.calibration.calibrate_maturity import apply_calibrator
from ml.prediction.features.feature_engineering import prepare_inference_features
from ml.prediction.features.timeseries_builder import build_maturity_sequences
from ml.prediction.training.maturity_common import HARVEST_DROP_COLUMNS
from ml.prediction.training.train_ensemble import weighted_average
from ml.prediction.training.train_lstm_maturity import scale_sequences


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"

DROP_COLUMNS = HARVEST_DROP_COLUMNS


def load_params() -> dict:
    with PARAMS_PATH.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def _import_keras():
    try:
        from tensorflow import keras
    except ImportError as error:
        raise ImportError(
            "TensorFlow is not installed. Install it with: "
            "python -m pip install 'tensorflow>=2.15.0,<3.0'"
        ) from error
    return keras


def _load_feature_frame(input_csv_path: Path, params: dict) -> pd.DataFrame:
    df = pd.read_csv(input_csv_path)
    if {"gdd", "light_exposure_index", "irrigation_per_day"}.issubset(df.columns):
        return df
    return prepare_inference_features(df, params=params)


def predict_harvest_dates_ensemble(
    input_csv_path: str | Path,
    output_csv_path: str | Path,
    ensemble_path: str | Path | None = None,
) -> None:
    """Blend XGBoost + LSTM, calibrate, then convert days to harvest dates."""
    params = load_params()
    ensemble_path = (
        Path(ensemble_path)
        if ensemble_path is not None
        else PROJECT_ROOT / params["paths"]["ensemble_output"]
    )

    if not ensemble_path.exists():
        raise FileNotFoundError(
            f"Ensemble artifact not found: {ensemble_path}. "
            "Run dvc repro train_ensemble after train_harvest and train_lstm."
        )

    bundle = joblib.load(ensemble_path)
    xgb_path = PROJECT_ROOT / bundle["xgb_model_path"]
    lstm_path = PROJECT_ROOT / bundle["lstm_model_path"]
    scaler_path = PROJECT_ROOT / bundle["lstm_scaler_path"]

    for path, label in (
        (xgb_path, "XGBoost harvest model"),
        (lstm_path, "LSTM maturity model"),
        (scaler_path, "LSTM scaler"),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{label} not found: {path}")

    df = _load_feature_frame(Path(input_csv_path), params)
    if "planting_date" not in df.columns:
        raise ValueError("Input data must contain planting_date.")

    planting_dates = pd.to_datetime(df["planting_date"], errors="coerce")
    if planting_dates.isna().any():
        raise ValueError("planting_date contains invalid dates.")

    keras = _import_keras()
    xgb_model = joblib.load(xgb_path)
    lstm_model = keras.models.load_model(lstm_path)
    scaler_bundle = joblib.load(scaler_path)

    X_tab = df.drop(columns=DROP_COLUMNS, errors="ignore")
    xgb_pred = np.asarray(xgb_model.predict(X_tab), dtype=float)

    lookback = int(bundle.get("lookback", params["lstm_training"]["lookback"]))
    base_temp_c = float(
        bundle.get(
            "base_temp_c",
            params["feature_engineering"]["tomato_base_temperature_C"],
        )
    )
    sequences, _, _ = build_maturity_sequences(
        df,
        lookback=lookback,
        base_temp_c=base_temp_c,
        target_column=None,
    )
    scaled, _ = scale_sequences(sequences, scaler=scaler_bundle["scaler"], fit=False)
    lstm_pred = lstm_model.predict(scaled, verbose=0).reshape(-1)

    blended = weighted_average(
        xgb_pred,
        lstm_pred,
        bundle["xgb_weight"],
        bundle["lstm_weight"],
    )
    calibrated = apply_calibrator(bundle["calibrator"], blended)
    predicted_days = np.rint(calibrated).astype(int)

    result = df.copy()
    result["predicted_days_xgb"] = np.rint(xgb_pred).astype(int)
    result["predicted_days_lstm"] = np.rint(lstm_pred).astype(int)
    result["predicted_days_ensemble_raw"] = np.rint(blended).astype(int)
    result["predicted_days_to_maturity"] = predicted_days
    result["predicted_harvest_date"] = (
        planting_dates + pd.to_timedelta(predicted_days, unit="D")
    ).dt.date.astype(str)

    output_csv_path = Path(output_csv_path)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv_path, index=False)

    print(f"Ensemble harvest date predictions saved: {output_csv_path}")


def main() -> None:
    params = load_params()
    input_csv_path = PROJECT_ROOT / params["paths"]["processed_data"]
    output_csv_path = PROJECT_ROOT / params["paths"]["ensemble_predictions_output"]
    predict_harvest_dates_ensemble(input_csv_path, output_csv_path)


if __name__ == "__main__":
    main()
