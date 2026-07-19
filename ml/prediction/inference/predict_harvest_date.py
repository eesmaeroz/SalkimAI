"""Predict harvest dates from an XGBoost days-to-maturity model."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import yaml


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
    with PARAMS_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def predict_harvest_dates(
    input_csv_path: str | Path,
    output_csv_path: str | Path,
    model_path: str | Path | None = None,
) -> None:
    """Predict days to maturity and convert them into harvest dates."""
    params = load_params()
    model_path = (
        Path(model_path)
        if model_path is not None
        else PROJECT_ROOT / params["paths"]["harvest_model_output"]
    )

    if not model_path.exists():
        raise FileNotFoundError(
            f"Harvest model not found: {model_path}. "
            "Run dvc repro train_harvest after installing xgboost."
        )

    df = pd.read_csv(input_csv_path)
    if "planting_date" not in df.columns:
        raise ValueError("Input data must contain planting_date.")

    planting_dates = pd.to_datetime(df["planting_date"], errors="coerce")
    if planting_dates.isna().any():
        raise ValueError("planting_date contains invalid dates.")

    model = joblib.load(model_path)
    X = df.drop(columns=DROP_COLUMNS, errors="ignore")
    predicted_days = model.predict(X).round().astype(int)

    result = df.copy()
    result["predicted_days_to_maturity"] = predicted_days
    result["predicted_harvest_date"] = (
        planting_dates + pd.to_timedelta(predicted_days, unit="D")
    ).dt.date.astype(str)

    output_csv_path = Path(output_csv_path)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv_path, index=False)

    print(f"Harvest date predictions saved: {output_csv_path}")


def main() -> None:
    params = load_params()
    input_csv_path = PROJECT_ROOT / params["paths"]["processed_data"]
    output_csv_path = PROJECT_ROOT / params["paths"]["harvest_predictions_output"]
    predict_harvest_dates(input_csv_path, output_csv_path)


if __name__ == "__main__":
    main()
