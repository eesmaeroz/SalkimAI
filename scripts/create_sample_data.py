"""Create a small sample weather dataset."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "greenhouse_data.csv"


def create_sample_data(row_count: int = 150) -> pd.DataFrame:
    """
    Gerçek veri gelmeden önce sistemi test etmek için örnek sera verisi üretir.

    Bu dosya şunları sağlar:
        - Feature engineering test edilebilir.
        - Model eğitimi test edilebilir.
        - MLflow kaydı test edilebilir.
        - DVC pipeline test edilebilir.
    """

    rng = np.random.default_rng(42)

    varieties = [
        "Italian Heart Shaped",
        "Black Krim",
        "German Pink",
        "Italian Red Beefsteak",
        "Kellogg's Breakfast",
    ]

    rows = []

    for i in range(row_count):
        planting_date = pd.Timestamp("2025-01-01") + pd.Timedelta(
            days=int(rng.integers(0, 120))
        )

        days_to_maturity = int(rng.integers(70, 110))

        harvest_date = planting_date + pd.Timedelta(days=days_to_maturity)

        min_temp = round(float(rng.uniform(15, 22)), 2)
        max_temp = round(float(rng.uniform(25, 35)), 2)
        avg_temp = round((min_temp + max_temp) / 2, 2)

        humidity = round(float(rng.uniform(55, 80)), 2)
        co2 = round(float(rng.uniform(380, 650)), 2)
        light = round(float(rng.uniform(12000, 28000)), 2)
        photoperiod = round(float(rng.uniform(10, 14.5)), 2)
        irrigation = round(float(rng.uniform(180, 420)), 2)

        fertilizer_n = round(float(rng.uniform(80, 180)), 2)
        fertilizer_p = round(float(rng.uniform(40, 100)), 2)
        fertilizer_k = round(float(rng.uniform(100, 240)), 2)

        pest = round(float(rng.uniform(0, 5)), 2)
        soil_ph = round(float(rng.uniform(5.7, 7.2)), 2)

        yield_value = (
            7
            + (avg_temp - 18) * 0.25
            + (light / 10000) * 0.6
            + (co2 - 380) * 0.005
            + irrigation * 0.01
            + fertilizer_n * 0.01
            + fertilizer_p * 0.008
            + fertilizer_k * 0.006
            - pest * 0.7
            - abs(soil_ph - 6.4) * 0.8
            + rng.normal(0, 1.2)
        )

        row = {
            "greenhouse_id": f"GH_{int(rng.integers(1, 11)):03d}",
            "data_source": "synthetic",
            "crop_type": "tomato",
            "variety": rng.choice(varieties),
            "planting_date": planting_date.date().isoformat(),
            "harvest_date": harvest_date.date().isoformat(),
            "days_to_maturity": days_to_maturity,
            "avg_temperature_C": avg_temp,
            "min_temperature_C": min_temp,
            "max_temperature_C": max_temp,
            "humidity_percent": humidity,
            "co2_ppm": co2,
            "light_intensity_lux": light,
            "photoperiod_hours": photoperiod,
            "irrigation_mm": irrigation,
            "fertilizer_N_kg_ha": fertilizer_n,
            "fertilizer_P_kg_ha": fertilizer_p,
            "fertilizer_K_kg_ha": fertilizer_k,
            "pest_severity": pest,
            "soil_pH": soil_ph,
            "yield_kg_per_m2": round(max(yield_value, 1), 2),
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    return df


def main() -> None:
    """
    Örnek veri dosyasını data/raw/greenhouse_data.csv konumuna kaydeder.
    """

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = create_sample_data(row_count=150)

    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Örnek veri oluşturuldu: {OUTPUT_PATH}")
    print(df.head())


if __name__ == "__main__":
    main()
