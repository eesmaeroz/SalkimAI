"""Model training entry point."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import yaml

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"


DROP_COLUMNS = [
    "yield_kg_per_m2",
    "planting_date",
    "harvest_date",
]


def load_params() -> dict:
    """
    config/params.yaml dosyasını okur.
    """

    with open(PARAMS_PATH, "r", encoding="utf-8") as file:
        params = yaml.safe_load(file)

    return params


def load_training_data(path: str | Path) -> pd.DataFrame:
    """
    Eğitimde kullanılacak işlenmiş veriyi okur.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"İşlenmiş veri bulunamadı: {path}. "
            "Önce python -m ml.prediction.features.feature_engineering "
            "komutunu çalıştır."
        )

    df = pd.read_csv(path)

    return df


def split_features_and_target(
    df: pd.DataFrame,
    target_column: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Veri setini X ve y olarak ayırır.

    X:
        Modelin kullanacağı bağımsız değişkenler.

    y:
        Modelin tahmin edeceği hedef değişken.
    """

    if target_column not in df.columns:
        raise ValueError(f"Hedef sütun bulunamadı: {target_column}")

    X = df.drop(columns=DROP_COLUMNS, errors="ignore")
    y = df[target_column]

    return X, y


def build_model(
    params: dict,
    X: pd.DataFrame,
) -> Pipeline:
    """
    Ön işleme + Random Forest model pipeline'ı oluşturur.

    Kategorik değişkenler:
        OneHotEncoder ile sayısallaştırılır.

    Sayısal değişkenler:
        Direkt modele verilir.
    """

    model_params = params["training"]["model"]

    categorical_features = X.select_dtypes(include=["object"]).columns.tolist()
    numeric_features = X.select_dtypes(include=["number"]).columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "numeric",
                "passthrough",
                numeric_features,
            ),
        ]
    )

    regressor = RandomForestRegressor(
        n_estimators=model_params["n_estimators"],
        max_depth=model_params["max_depth"],
        min_samples_split=model_params["min_samples_split"],
        min_samples_leaf=model_params["min_samples_leaf"],
        random_state=params["training"]["random_state"],
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", regressor),
        ]
    )

    return pipeline


def evaluate_model(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """
    Test verisi üzerinde model başarımını hesaplar.

    Hesaplanan metrikler:
        MAE
        RMSE
        R2
    """

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2),
    }

    return metrics


def save_metrics(
    metrics: dict,
    output_path: str | Path,
) -> None:
    """
    Model metriklerini JSON dosyası olarak kaydeder.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2, ensure_ascii=False)


def main() -> None:
    """
    Model eğitim pipeline ana fonksiyonu.
    """

    params = load_params()

    data_path = PROJECT_ROOT / params["paths"]["processed_data"]
    model_output_path = PROJECT_ROOT / params["paths"]["model_output"]
    metrics_output_path = PROJECT_ROOT / params["paths"]["metrics_output"]

    target_column = params["training"]["target_column"]
    test_size = params["training"]["test_size"]
    random_state = params["training"]["random_state"]

    df = load_training_data(data_path)

    X, y = split_features_and_target(
        df=df,
        target_column=target_column,
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    model = build_model(
        params=params,
        X=X,
    )

    mlflow_tracking_uri = PROJECT_ROOT / params["mlflow"]["tracking_uri"]

    mlflow.set_tracking_uri(str(mlflow_tracking_uri))
    mlflow.set_experiment(params["mlflow"]["experiment_name"])

    with mlflow.start_run(run_name=params["mlflow"]["run_name"]):
        model.fit(X_train, y_train)

        metrics = evaluate_model(
            model=model,
            X_test=X_test,
            y_test=y_test,
        )

        model_output_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, model_output_path)

        save_metrics(
            metrics=metrics,
            output_path=metrics_output_path,
        )

        mlflow.log_param("model_type", params["training"]["model"]["type"])
        mlflow.log_param("n_estimators", params["training"]["model"]["n_estimators"])
        mlflow.log_param("max_depth", params["training"]["model"]["max_depth"])
        mlflow.log_param(
            "min_samples_split",
            params["training"]["model"]["min_samples_split"],
        )
        mlflow.log_param(
            "min_samples_leaf",
            params["training"]["model"]["min_samples_leaf"],
        )
        mlflow.log_param("test_size", test_size)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("target_column", target_column)
        mlflow.log_param("feature_count", X.shape[1])
        mlflow.log_param("row_count", X.shape[0])

        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)

        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
        )

        mlflow.log_artifact(str(metrics_output_path))

    print("Model eğitimi tamamlandı.")
    print(f"Model dosyası: {model_output_path}")
    print(f"Metrik dosyası: {metrics_output_path}")
    print(f"MAE: {metrics['MAE']:.4f}")
    print(f"RMSE: {metrics['RMSE']:.4f}")
    print(f"R2: {metrics['R2']:.4f}")


if __name__ == "__main__":
    main()