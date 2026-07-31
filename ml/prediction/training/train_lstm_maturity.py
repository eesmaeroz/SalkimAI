"""Train an LSTM model on maturity-trend sequences.

Predicts `days_to_maturity` from a fixed lookback window (default 48 timesteps)
that encodes daily weather plus cumulative GDD / maturity progress.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import numpy as np
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ml.prediction.features.timeseries_builder import (
    build_maturity_sequences,
    load_sequences,
    save_sequences,
)
from ml.prediction.training.maturity_common import (
    maturity_split_params,
    split_maturity_indices,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"


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


def scale_sequences(
    sequences: np.ndarray,
    scaler: StandardScaler | None = None,
    fit: bool = False,
) -> tuple[np.ndarray, StandardScaler]:
    """Scale sequence features with a scaler fit on flattened timesteps."""
    n_samples, lookback, n_features = sequences.shape
    flat = sequences.reshape(-1, n_features)
    if scaler is None:
        scaler = StandardScaler()
    if fit:
        flat_scaled = scaler.fit_transform(flat)
    else:
        flat_scaled = scaler.transform(flat)
    return flat_scaled.reshape(n_samples, lookback, n_features).astype(np.float32), scaler


def build_lstm_model(
    lookback: int,
    n_features: int,
    lstm_units: list[int],
    dropout: float,
    learning_rate: float,
):
    keras = _import_keras()
    inputs = keras.Input(shape=(lookback, n_features))
    x = inputs
    for index, units in enumerate(lstm_units):
        return_sequences = index < len(lstm_units) - 1
        x = keras.layers.LSTM(units, return_sequences=return_sequences)(x)
        if dropout > 0:
            x = keras.layers.Dropout(dropout)(x)
    outputs = keras.layers.Dense(1)(x)
    model = keras.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mse",
        metrics=["mae"],
    )
    return model


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


def ensure_sequence_data(params: dict) -> tuple[np.ndarray, np.ndarray, list[str]]:
    sequence_path = PROJECT_ROOT / params["paths"]["sequence_data"]
    if sequence_path.exists():
        sequences, targets, feature_names = load_sequences(sequence_path)
        if targets is None:
            raise ValueError(f"Sequence file has no targets: {sequence_path}")
        return sequences, targets, feature_names

    processed_path = PROJECT_ROOT / params["paths"]["processed_data"]
    if not processed_path.exists():
        raise FileNotFoundError(
            f"Processed data not found: {processed_path}. Run make_features first."
        )

    import pandas as pd

    df = pd.read_csv(processed_path)
    lookback = int(params["lstm_training"]["lookback"])
    base_temp_c = float(params["feature_engineering"]["tomato_base_temperature_C"])
    target_column = params["lstm_training"]["target_column"]
    sequences, targets, feature_names = build_maturity_sequences(
        df,
        lookback=lookback,
        base_temp_c=base_temp_c,
        target_column=target_column,
    )
    if targets is None:
        raise ValueError(f"Target column missing: {target_column}")
    save_sequences(sequences, targets, feature_names, sequence_path)
    return sequences, targets, feature_names


def main() -> None:
    params = load_params()
    lstm_params = params["lstm_training"]
    keras = _import_keras()

    sequences, targets, feature_names = ensure_sequence_data(params)
    lookback = sequences.shape[1]
    n_features = sequences.shape[2]

    split_params = maturity_split_params(params)
    train_idx, test_idx = split_maturity_indices(
        n_samples=len(sequences),
        test_size=split_params["test_size"],
        random_state=split_params["random_state"],
    )
    # Keep a validation slice inside train for monitoring; hold test for metrics only.
    train_idx, val_idx = train_test_split(
        train_idx,
        test_size=0.2,
        random_state=split_params["random_state"],
    )

    X_train_raw, X_val_raw, X_test_raw = (
        sequences[train_idx],
        sequences[val_idx],
        sequences[test_idx],
    )
    y_train, y_val, y_test = (
        targets[train_idx],
        targets[val_idx],
        targets[test_idx],
    )

    X_train, scaler = scale_sequences(X_train_raw, fit=True)
    X_val, _ = scale_sequences(X_val_raw, scaler=scaler, fit=False)
    X_test, _ = scale_sequences(X_test_raw, scaler=scaler, fit=False)

    model = build_lstm_model(
        lookback=lookback,
        n_features=n_features,
        lstm_units=list(lstm_params["lstm_units"]),
        dropout=float(lstm_params["dropout"]),
        learning_rate=float(lstm_params["learning_rate"]),
    )

    model_output_path = PROJECT_ROOT / params["paths"]["lstm_model_output"]
    scaler_output_path = PROJECT_ROOT / params["paths"]["lstm_scaler_output"]
    metrics_output_path = PROJECT_ROOT / params["paths"]["lstm_metrics_output"]
    model_output_path.parent.mkdir(parents=True, exist_ok=True)

    mlflow.set_tracking_uri(params["mlflow"]["tracking_uri"])
    experiment_name = params["mlflow"]["experiment_name"]
    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(
            name=experiment_name,
            artifact_location=params["mlflow"].get("artifact_location"),
        )
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="lstm_maturity_trend"):
        history = model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=int(lstm_params["epochs"]),
            batch_size=int(lstm_params["batch_size"]),
            verbose=0,
        )
        y_pred = model.predict(X_test, verbose=0).reshape(-1)
        metrics = evaluate_predictions(y_test, y_pred)

        model.save(model_output_path)
        joblib.dump(
            {
                "scaler": scaler,
                "feature_names": feature_names,
                "lookback": lookback,
            },
            scaler_output_path,
        )
        save_metrics(metrics, metrics_output_path)

        mlflow.log_params(
            {
                "model_type": "LSTM",
                "target_column": lstm_params["target_column"],
                "lookback": lookback,
                "n_features": n_features,
                "epochs": lstm_params["epochs"],
                "batch_size": lstm_params["batch_size"],
                "dropout": lstm_params["dropout"],
                "learning_rate": lstm_params["learning_rate"],
                "lstm_units": str(lstm_params["lstm_units"]),
                "row_count": len(sequences),
            }
        )
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)
        final_val_loss = float(history.history["val_loss"][-1])
        mlflow.log_metric("val_loss", final_val_loss)
        mlflow.log_artifact(str(metrics_output_path))
        mlflow.log_artifact(str(scaler_output_path))

    print("LSTM maturity model training completed.")
    print(f"Model file: {model_output_path}")
    print(f"Scaler file: {scaler_output_path}")
    print(f"Metrics file: {metrics_output_path}")
    print(f"MAE days: {metrics['MAE_days']:.4f}")
    print(f"RMSE days: {metrics['RMSE_days']:.4f}")
    print(f"R2: {metrics['R2']:.4f}")


if __name__ == "__main__":
    main()
