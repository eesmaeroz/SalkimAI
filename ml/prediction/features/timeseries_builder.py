"""Build fixed-lookback maturity trend sequences for the LSTM model.

Each greenhouse cycle becomes a window of shape `(lookback, n_features)`.
Daily weather is taken from the deterministic mock (or row scalars when needed);
cumulative GDD and normalized day progress capture the maturity trend.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ml.prediction.features.gdd_calculator import calculate_gdd
from ml.prediction.features.weather_provider import get_mock_weather_data


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PARAMS_PATH = PROJECT_ROOT / "config" / "params.yaml"

SEQUENCE_FEATURE_NAMES = [
    "avg_temperature_C",
    "min_temperature_C",
    "max_temperature_C",
    "humidity_percent",
    "daily_gdd",
    "cumulative_gdd",
    "maturity_progress",
]


def load_params() -> dict:
    with PARAMS_PATH.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def _parse_end_date(value: object) -> date | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return None
    return timestamp.date()


def build_row_sequence(
    row: pd.Series,
    lookback: int,
    base_temp_c: float,
) -> np.ndarray:
    """Build one `(lookback, n_features)` maturity-trend window."""
    if lookback < 1:
        raise ValueError("lookback must be at least 1")

    greenhouse_id = str(row.get("greenhouse_id", "UNKNOWN_GREENHOUSE"))
    end_date = _parse_end_date(row.get("planting_date"))
    weather = get_mock_weather_data(
        greenhouse_id,
        days=lookback,
        end_date=end_date,
    )
    daily_rows = weather["daily"]

    sequence = np.zeros((lookback, len(SEQUENCE_FEATURE_NAMES)), dtype=np.float32)
    cumulative_gdd = 0.0
    denominator = max(lookback - 1, 1)

    for step, day in enumerate(daily_rows):
        daily_gdd = calculate_gdd(
            min_temp_c=day["min_temperature_C"],
            max_temp_c=day["max_temperature_C"],
            base_temp_c=base_temp_c,
        )
        cumulative_gdd += daily_gdd
        sequence[step] = [
            day["avg_temperature_C"],
            day["min_temperature_C"],
            day["max_temperature_C"],
            day["humidity_percent"],
            daily_gdd,
            cumulative_gdd,
            step / denominator,
        ]

    return sequence


def build_maturity_sequences(
    df: pd.DataFrame,
    lookback: int = 48,
    base_temp_c: float = 10.0,
    target_column: str | None = "days_to_maturity",
) -> tuple[np.ndarray, np.ndarray | None, list[str]]:
    """Build sequence tensor `(N, lookback, F)` and optional target vector."""
    if df.empty:
        raise ValueError("Cannot build sequences from an empty DataFrame.")

    sequences = np.stack(
        [
            build_row_sequence(row, lookback=lookback, base_temp_c=base_temp_c)
            for _, row in df.iterrows()
        ]
    )

    targets: np.ndarray | None = None
    if target_column and target_column in df.columns:
        targets = df[target_column].to_numpy(dtype=np.float32)

    return sequences, targets, list(SEQUENCE_FEATURE_NAMES)


def save_sequences(
    sequences: np.ndarray,
    targets: np.ndarray | None,
    feature_names: list[str],
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "sequences": sequences,
        "feature_names": np.array(feature_names),
    }
    if targets is not None:
        payload["targets"] = targets
    np.savez_compressed(output_path, **payload)


def load_sequences(
    path: str | Path,
) -> tuple[np.ndarray, np.ndarray | None, list[str]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Sequence data not found: {path}. Run make_sequences first."
        )
    with np.load(path, allow_pickle=False) as archive:
        sequences = archive["sequences"]
        feature_names = archive["feature_names"].tolist()
        targets = archive["targets"] if "targets" in archive.files else None
    return sequences, targets, feature_names


def main() -> None:
    params = load_params()
    lookback = int(params["lstm_training"]["lookback"])
    base_temp_c = float(params["feature_engineering"]["tomato_base_temperature_C"])
    target_column = params["lstm_training"]["target_column"]

    processed_path = PROJECT_ROOT / params["paths"]["processed_data"]
    sequence_path = PROJECT_ROOT / params["paths"]["sequence_data"]

    if not processed_path.exists():
        raise FileNotFoundError(
            f"Processed data not found: {processed_path}. Run make_features first."
        )

    df = pd.read_csv(processed_path)
    sequences, targets, feature_names = build_maturity_sequences(
        df,
        lookback=lookback,
        base_temp_c=base_temp_c,
        target_column=target_column,
    )
    save_sequences(sequences, targets, feature_names, sequence_path)

    print("Maturity sequences built.")
    print(f"Sequence file: {sequence_path}")
    print(f"Shape: {sequences.shape}")
    print(f"Features: {feature_names}")


if __name__ == "__main__":
    main()
