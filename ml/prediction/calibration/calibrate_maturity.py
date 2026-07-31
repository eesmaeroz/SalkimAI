"""Calibrate blended maturity predictions.

Fits an isotonic or linear mapping from ensemble scores to true
`days_to_maturity` values so harvest-date rounding stays better calibrated.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LinearRegression


SUPPORTED_METHODS = ("isotonic", "linear")


def build_calibrator(method: str = "isotonic"):
    method = method.lower()
    if method not in SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported calibration method: {method}. "
            f"Choose one of {SUPPORTED_METHODS}."
        )
    if method == "isotonic":
        return IsotonicRegression(out_of_bounds="clip")
    return LinearRegression()


def fit_calibrator(
    y_pred: np.ndarray,
    y_true: np.ndarray,
    method: str = "isotonic",
):
    """Fit a calibrator that maps raw predictions to observed targets."""
    calibrator = build_calibrator(method)
    predictions = np.asarray(y_pred, dtype=float).reshape(-1)
    targets = np.asarray(y_true, dtype=float).reshape(-1)
    if method.lower() == "linear":
        calibrator.fit(predictions.reshape(-1, 1), targets)
    else:
        calibrator.fit(predictions, targets)
    return calibrator


def apply_calibrator(calibrator: Any, y_pred: np.ndarray) -> np.ndarray:
    """Apply a fitted calibrator to raw predictions."""
    predictions = np.asarray(y_pred, dtype=float).reshape(-1)
    if isinstance(calibrator, LinearRegression):
        return calibrator.predict(predictions.reshape(-1, 1))
    return np.asarray(calibrator.predict(predictions), dtype=float)
