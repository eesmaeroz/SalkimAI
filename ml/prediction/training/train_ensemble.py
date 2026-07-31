"""Train an XGBoost + LSTM ensemble for days-to-maturity.

Blends the two base models with a weighted average, then fits a calibrator on
a held-out calibration slice and reports metrics on a disjoint evaluation slice.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.prediction.calibration.calibrate_maturity import (
    apply_calibrator,
    fit_calibrator,
)
from ml.prediction.features.timeseries_builder import build_maturity_sequences
from ml.prediction.training.maturity_common import (
    HARVEST_DROP_COLUMNS,
    maturity_split_params,
    split_calibration_indices,
    split_maturity_indices,
)
from ml.prediction.training.train_harvest_model import split_features_and_target
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


def weighted_average(
    xgb_pred: np.ndarray,
    lstm_pred: np.ndarray,
    xgb_weight: float,
    lstm_weight: float,
) -> np.ndarray:
    total = float(xgb_weight) + float(lstm_weight)
    if total <= 0:
        raise ValueError("Ensemble weights must sum to a positive value.")
    w_xgb = float(xgb_weight) / total
    w_lstm = float(lstm_weight) / total
    return w_xgb * np.asarray(xgb_pred, dtype=float) + w_lstm * np.asarray(
        lstm_pred, dtype=float
    )


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "MAE_days": float(mean_absolute_error(y_true, y_pred)),
        "RMSE_days": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
    }


def save_metrics(metrics: dict, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(metrics, stream, indent=2, ensure_ascii=False)


def _predict_xgb(model, df: pd.DataFrame) -> np.ndarray:
    X = df.drop(columns=DROP_COLUMNS, errors="ignore")
    return np.asarray(model.predict(X), dtype=float)


def _predict_lstm(
    keras_model,
    scaler_bundle: dict,
    df: pd.DataFrame,
    lookback: int,
    base_temp_c: float,
) -> np.ndarray:
    sequences, _, _ = build_maturity_sequences(
        df,
        lookback=lookback,
        base_temp_c=base_temp_c,
        target_column=None,
    )
    scaled, _ = scale_sequences(sequences, scaler=scaler_bundle["scaler"], fit=False)
    return keras_model.predict(scaled, verbose=0).reshape(-1)


def main() -> None:
    params = load_params()
    ensemble_params = params["ensemble"]
    harvest_params = params["harvest_training"]
    lstm_params = params["lstm_training"]
    split_params = maturity_split_params(params)
    keras = _import_keras()

    processed_path = PROJECT_ROOT / params["paths"]["processed_data"]
    xgb_path = PROJECT_ROOT / params["paths"]["harvest_model_output"]
    lstm_path = PROJECT_ROOT / params["paths"]["lstm_model_output"]
    scaler_path = PROJECT_ROOT / params["paths"]["lstm_scaler_output"]
    ensemble_path = PROJECT_ROOT / params["paths"]["ensemble_output"]
    metrics_path = PROJECT_ROOT / params["paths"]["ensemble_metrics_output"]

    for path, label in (
        (processed_path, "Processed data"),
        (xgb_path, "XGBoost harvest model"),
        (lstm_path, "LSTM maturity model"),
        (scaler_path, "LSTM scaler"),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{label} not found: {path}")

    df = pd.read_csv(processed_path)
    _, y = split_features_and_target(df, harvest_params["target_column"])

    _, test_idx = split_maturity_indices(
        n_samples=len(df),
        test_size=split_params["test_size"],
        random_state=split_params["random_state"],
    )
    calib_idx, eval_idx = split_calibration_indices(
        test_idx,
        calibration_size=split_params["calibration_size"],
        random_state=split_params["random_state"],
    )

    df_calib = df.iloc[calib_idx].reset_index(drop=True)
    df_eval = df.iloc[eval_idx].reset_index(drop=True)
    y_calib = y.iloc[calib_idx].to_numpy(dtype=float)
    y_eval = y.iloc[eval_idx].to_numpy(dtype=float)

    xgb_model = joblib.load(xgb_path)
    lstm_model = keras.models.load_model(lstm_path)
    scaler_bundle = joblib.load(scaler_path)

    lookback = int(scaler_bundle.get("lookback", lstm_params["lookback"]))
    base_temp_c = float(params["feature_engineering"]["tomato_base_temperature_C"])

    xgb_calib = _predict_xgb(xgb_model, df_calib)
    lstm_calib = _predict_lstm(
        lstm_model,
        scaler_bundle,
        df_calib,
        lookback=lookback,
        base_temp_c=base_temp_c,
    )
    xgb_eval = _predict_xgb(xgb_model, df_eval)
    lstm_eval = _predict_lstm(
        lstm_model,
        scaler_bundle,
        df_eval,
        lookback=lookback,
        base_temp_c=base_temp_c,
    )

    xgb_weight = float(ensemble_params["xgb_weight"])
    lstm_weight = float(ensemble_params["lstm_weight"])
    blended_calib = weighted_average(xgb_calib, lstm_calib, xgb_weight, lstm_weight)
    blended_eval = weighted_average(xgb_eval, lstm_eval, xgb_weight, lstm_weight)

    calibration_method = ensemble_params["calibration"]["method"]
    calibrator = fit_calibrator(blended_calib, y_calib, method=calibration_method)
    calibrated_eval = apply_calibrator(calibrator, blended_eval)

    metrics = {
        "xgb": evaluate_predictions(y_eval, xgb_eval),
        "lstm": evaluate_predictions(y_eval, lstm_eval),
        "ensemble_raw": evaluate_predictions(y_eval, blended_eval),
        "ensemble_calibrated": evaluate_predictions(y_eval, calibrated_eval),
        "xgb_weight": xgb_weight,
        "lstm_weight": lstm_weight,
        "calibration_method": calibration_method,
        "calibration_rows": int(len(calib_idx)),
        "evaluation_rows": int(len(eval_idx)),
    }

    bundle = {
        "xgb_weight": xgb_weight,
        "lstm_weight": lstm_weight,
        "calibration_method": calibration_method,
        "calibrator": calibrator,
        "xgb_model_path": str(xgb_path.relative_to(PROJECT_ROOT)),
        "lstm_model_path": str(lstm_path.relative_to(PROJECT_ROOT)),
        "lstm_scaler_path": str(scaler_path.relative_to(PROJECT_ROOT)),
        "lookback": lookback,
        "base_temp_c": base_temp_c,
        "target_column": harvest_params["target_column"],
    }

    ensemble_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, ensemble_path)
    save_metrics(metrics, metrics_path)

    mlflow.set_tracking_uri(params["mlflow"]["tracking_uri"])
    experiment_name = params["mlflow"]["experiment_name"]
    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(
            name=experiment_name,
            artifact_location=params["mlflow"].get("artifact_location"),
        )
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="maturity_ensemble_calibrated"):
        mlflow.log_params(
            {
                "ensemble_type": "weighted_average",
                "xgb_weight": xgb_weight,
                "lstm_weight": lstm_weight,
                "calibration_method": calibration_method,
                "lookback": lookback,
                "calibration_rows": len(calib_idx),
                "evaluation_rows": len(eval_idx),
            }
        )
        for prefix in ("xgb", "lstm", "ensemble_raw", "ensemble_calibrated"):
            for metric_name, metric_value in metrics[prefix].items():
                mlflow.log_metric(f"{prefix}_{metric_name}", metric_value)
        mlflow.log_artifact(str(metrics_path))
        mlflow.log_artifact(str(ensemble_path))

    print("Maturity ensemble training completed.")
    print(f"Ensemble file: {ensemble_path}")
    print(f"Metrics file: {metrics_path}")
    print(
        "Calibrated MAE days (held-out eval): "
        f"{metrics['ensemble_calibrated']['MAE_days']:.4f}"
    )


if __name__ == "__main__":
    main()
