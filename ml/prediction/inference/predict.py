"""Prediction entry point."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"


def load_params() -> dict:
    """
    config/params.yaml dosyasını okur.
    """

    with open(PARAMS_PATH, "r", encoding="utf-8") as file:
        params = yaml.safe_load(file)

    return params


def predict_from_csv(
    input_csv_path: str | Path,
    output_csv_path: str | Path,
) -> None:
    """
    Eğitilmiş modeli kullanarak CSV dosyası üzerinden tahmin üretir.
    """

    params = load_params()

    model_path = PROJECT_ROOT / params["paths"]["model_output"]

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model bulunamadı: {model_path}. "
            "Önce python -m ml.prediction.training.train_model komutunu çalıştır."
        )

    model = joblib.load(model_path)

    df = pd.read_csv(input_csv_path)

    drop_columns = [
        "yield_kg_per_m2",
        "planting_date",
        "harvest_date",
    ]

    X = df.drop(columns=drop_columns, errors="ignore")

    predictions = model.predict(X)

    result = df.copy()
    result["predicted_yield_kg_per_m2"] = predictions

    output_csv_path = Path(output_csv_path)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    result.to_csv(output_csv_path, index=False)

    print(f"Tahminler kaydedildi: {output_csv_path}")


def main() -> None:
    """
    Varsayılan olarak işlenmiş veri üzerinden tahmin üretir.
    """

    params = load_params()

    input_csv_path = PROJECT_ROOT / params["paths"]["processed_data"]
    output_csv_path = PROJECT_ROOT / params["paths"]["predictions_output"]

    predict_from_csv(
        input_csv_path=input_csv_path,
        output_csv_path=output_csv_path,
    )


if __name__ == "__main__":
    main()