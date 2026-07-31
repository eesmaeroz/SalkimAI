"""Shared helpers for maturity / harvest-date models."""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split


# Columns that must never reach harvest/maturity models.
# `irrigation_per_day` historically leaked the target via irrigation_mm / days_to_maturity;
# it is still dropped defensively even after planned_cycle_days was introduced.
HARVEST_DROP_COLUMNS = [
    "yield_kg_per_m2",
    "days_to_maturity",
    "planting_date",
    "harvest_date",
    "calculated_days_to_maturity",
]


def maturity_split_params(params: dict) -> dict:
    """Prefer shared maturity_split; fall back to harvest_training settings."""
    if "maturity_split" in params:
        split = dict(params["maturity_split"])
        split.setdefault("calibration_size", 0.5)
        return split
    harvest = params["harvest_training"]
    return {
        "test_size": harvest["test_size"],
        "random_state": harvest["random_state"],
        "calibration_size": 0.5,
    }


def split_maturity_indices(
    n_samples: int,
    test_size: float,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return train/test row indices with a shared split recipe."""
    indices = np.arange(n_samples)
    train_idx, test_idx = train_test_split(
        indices,
        test_size=test_size,
        random_state=random_state,
    )
    return train_idx, test_idx


def split_calibration_indices(
    test_idx: np.ndarray,
    calibration_size: float,
    random_state: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Split the holdout into calibration-fit vs final evaluation indices."""
    if not 0.0 < float(calibration_size) < 1.0:
        raise ValueError("calibration_size must be between 0 and 1 (exclusive).")
    if len(test_idx) < 4:
        # Tiny holdouts: use everything for both fit and eval (best-effort).
        return test_idx, test_idx
    calib_idx, eval_idx = train_test_split(
        test_idx,
        test_size=1.0 - float(calibration_size),
        random_state=random_state,
    )
    return calib_idx, eval_idx
