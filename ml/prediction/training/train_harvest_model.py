"""Train an XGBoost model for harvest timing.

The target is `days_to_maturity`; at inference time this can be added to a
planting date to estimate harvest date.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import yaml
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"

DROP_COLUMNS = [
    "yield_kg_per_m2",
    "days_to_maturity",
    "planting_date",
    "harvest_date",
    "calculated_days_to_maturity",
]


def load_params() -> dict:
    with PARAMS_PATH.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def load_training_data(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Processed data not found: {path}. Run dvc repro or feature engineering first."
        )
    return pd.read_csv(path)


def split_features_and_target(
    df: pd.DataFrame,
    target_column: str,
) -> tuple[pd.DataFrame, pd.Series]:
    if target_column not in df.columns:
        raise ValueError(f"Target column not found: {target_column}")

    X = df.drop(columns=DROP_COLUMNS, errors="ignore")
    y = df[target_column]
    return X, y


def build_model(params: dict, X: pd.DataFrame) -> Pipeline:
    try:
        from xgboost import XGBRegressor
    except ImportError as error:
        raise ImportError(
            "XGBoost is not installed. Install it with: python -m pip install xgboost"
        ) from error

    model_params = params["harvest_training"]["model"]
    categorical_features = X.select_dtypes(include=["object"]).columns.tolist()
    numeric_features = X.select_dtypes(include=["number"]).columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("numeric", "passthrough", numeric_features),
        ]
    )

    regressor = XGBRegressor(
        n_estimators=model_params["n_estimators"],
        max_depth=model_params["max_depth"],
        learning_rate=model_params["learning_rate"],
        subsample=model_params["subsample"],
        colsample_bytree=model_params["colsample_bytree"],
        objective=model_params["objective"],
        random_state=params["harvest_training"]["random_state"],
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", regressor),
        ]
    )


def evaluate_model(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[dict, np.ndarray]:
    y_pred = model.predict(X_test)
    metrics = {
        "MAE_days": float(mean_absolute_error(y_test, y_pred)),
        "RMSE_days": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "R2": float(r2_score(y_test, y_pred)),
    }
    return metrics, y_pred


def save_metrics(metrics: dict, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(metrics, stream, indent=2, ensure_ascii=False)


def main() -> None:
    params = load_params()
    harvest_params = params["harvest_training"]

    data_path = PROJECT_ROOT / params["paths"]["processed_data"]
    model_output_path = PROJECT_ROOT / params["paths"]["harvest_model_output"]
    metrics_output_path = PROJECT_ROOT / params["paths"]["harvest_metrics_output"]

    df = load_training_data(data_path)
    X, y = split_features_and_target(df, harvest_params["target_column"])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=harvest_params["test_size"],
        random_state=harvest_params["random_state"],
    )

    model = build_model(params, X)

    mlflow.set_tracking_uri(params["mlflow"]["tracking_uri"])
    experiment_name = params["mlflow"]["experiment_name"]
    if mlflow.get_experiment_by_name(experiment_name) is None:
        mlflow.create_experiment(
            name=experiment_name,
            artifact_location=params["mlflow"].get("artifact_location"),
        )
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="xgboost_harvest_date_baseline"):
        model.fit(X_train, y_train)
        metrics, y_pred = evaluate_model(model, X_test, y_test)

        model_output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_output_path)
        save_metrics(metrics, metrics_output_path)

        mlflow.log_params(
            {
                "model_type": harvest_params["model"]["type"],
                "target_column": harvest_params["target_column"],
                "test_size": harvest_params["test_size"],
                "random_state": harvest_params["random_state"],
                "feature_count": X.shape[1],
                "row_count": X.shape[0],
            }
        )
        mlflow.log_params(harvest_params["model"])
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)
        signature = infer_signature(X_test, y_pred)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="harvest_model",
            signature=signature,
            input_example=X_test.head(3),
        )
        mlflow.log_artifact(str(metrics_output_path))

    print("XGBoost harvest model training completed.")
    print(f"Model file: {model_output_path}")
    print(f"Metrics file: {metrics_output_path}")
    print(f"MAE days: {metrics['MAE_days']:.4f}")
    print(f"RMSE days: {metrics['RMSE_days']:.4f}")
    print(f"R2: {metrics['R2']:.4f}")


if __name__ == "__main__":
    main()
