"""Tests for maturity sequence building, calibration, and ensemble blending."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.isotonic import IsotonicRegression

from ml.prediction.calibration.calibrate_maturity import (
    apply_calibrator,
    fit_calibrator,
)
from ml.prediction.features.timeseries_builder import (
    SEQUENCE_FEATURE_NAMES,
    build_maturity_sequences,
    build_row_sequence,
)
from ml.prediction.inference.predict_harvest_ensemble import (
    predict_harvest_dates_ensemble,
)
from ml.prediction.training.maturity_common import (
    split_calibration_indices,
    split_maturity_indices,
)
from ml.prediction.training.train_ensemble import weighted_average


def _sample_frame(rows: int = 3) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "greenhouse_id": [f"GH_{i:03d}" for i in range(1, rows + 1)],
            "planting_date": ["2025-03-01", "2025-03-10", "2025-04-01"][:rows],
            "days_to_maturity": [80, 90, 100][:rows],
            "avg_temperature_C": [22.0, 23.0, 21.5][:rows],
        }
    )


def test_build_row_sequence_shape_and_trend():
    row = _sample_frame(1).iloc[0]
    sequence = build_row_sequence(row, lookback=48, base_temp_c=10.0)

    assert sequence.shape == (48, len(SEQUENCE_FEATURE_NAMES))
    # cumulative GDD must be non-decreasing across the lookback window
    cumulative_gdd = sequence[:, SEQUENCE_FEATURE_NAMES.index("cumulative_gdd")]
    assert np.all(np.diff(cumulative_gdd) >= -1e-6)
    maturity_progress = sequence[:, SEQUENCE_FEATURE_NAMES.index("maturity_progress")]
    assert maturity_progress[0] == pytest.approx(0.0)
    assert maturity_progress[-1] == pytest.approx(1.0)


def test_build_maturity_sequences_batch():
    df = _sample_frame(3)
    sequences, targets, feature_names = build_maturity_sequences(
        df, lookback=48, base_temp_c=10.0
    )

    assert sequences.shape == (3, 48, len(SEQUENCE_FEATURE_NAMES))
    assert targets is not None
    assert targets.tolist() == [80, 90, 100]
    assert feature_names == SEQUENCE_FEATURE_NAMES


def test_weighted_average_normalizes_weights():
    xgb_pred = np.array([100.0, 80.0])
    lstm_pred = np.array([80.0, 100.0])
    blended = weighted_average(xgb_pred, lstm_pred, xgb_weight=0.6, lstm_weight=0.4)
    assert blended[0] == pytest.approx(92.0)
    assert blended[1] == pytest.approx(88.0)


def test_shared_maturity_split_is_deterministic():
    first_train, first_test = split_maturity_indices(150, test_size=0.2, random_state=42)
    second_train, second_test = split_maturity_indices(150, test_size=0.2, random_state=42)
    assert np.array_equal(first_train, second_train)
    assert np.array_equal(first_test, second_test)

    calib_idx, eval_idx = split_calibration_indices(
        first_test, calibration_size=0.5, random_state=42
    )
    assert len(calib_idx) + len(eval_idx) == len(first_test)
    assert len(set(calib_idx).intersection(eval_idx)) == 0


def test_isotonic_calibration_reduces_bias():
    y_true = np.array([70.0, 80.0, 90.0, 100.0, 110.0])
    y_pred = y_true + 5.0
    calibrator = fit_calibrator(y_pred, y_true, method="isotonic")
    calibrated = apply_calibrator(calibrator, y_pred)

    assert isinstance(calibrator, IsotonicRegression)
    assert mean_abs(calibrated - y_true) < mean_abs(y_pred - y_true)


def mean_abs(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values)))


def test_predict_harvest_ensemble_requires_artifact():
    workdir = Path(__file__).resolve().parents[1] / ".pytest_tmp_ensemble"
    workdir.mkdir(parents=True, exist_ok=True)
    input_path = workdir / "input.csv"
    output_path = workdir / "output.csv"
    pd.DataFrame({"planting_date": ["2025-01-01"]}).to_csv(input_path, index=False)

    with pytest.raises(FileNotFoundError, match="Ensemble artifact not found"):
        predict_harvest_dates_ensemble(
            input_path,
            output_path,
            ensemble_path=workdir / "missing_ensemble.joblib",
        )

    assert not output_path.exists()
