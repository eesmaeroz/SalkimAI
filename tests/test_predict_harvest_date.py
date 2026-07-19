from pathlib import Path

import pandas as pd

from ml.prediction.inference.predict_harvest_date import predict_harvest_dates


def test_predict_harvest_dates_requires_model(tmp_path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    pd.DataFrame({"planting_date": ["2025-01-01"]}).to_csv(input_path, index=False)

    try:
        predict_harvest_dates(
            input_path,
            output_path,
            model_path=tmp_path / "missing_model.joblib",
        )
    except FileNotFoundError as error:
        assert "Harvest model not found" in str(error)
    else:
        raise AssertionError("Expected missing harvest model to fail")

    assert not Path(output_path).exists()
