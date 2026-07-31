"""
Salkım AI — Tahminleme Servisi (ML Bridge)

Arif'in T1 modellerini API'ye bağlar:
  - XGBoost hasat (days_to_maturity)
  - LSTM olgunluk trendi (48 timestep)
  - XGBoost + LSTM ağırlıklı ensemble + calibration
  - RandomForest / legacy yield
  - Open-Meteo şehir hava durumu
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)

DISEASE_RISK_HIGH_THRESHOLD = 0.70
_ML_MODEL_VERSION = "v0.1.0-xgboost-statistical-fallback"


def predict_harvest(
    crop_type: str,
    variety: str,
    avg_temperature_C: float,
    min_temperature_C: float,
    max_temperature_C: float,
    humidity_percent: float,
    co2_ppm: float,
    light_intensity_lux: float,
    photoperiod_hours: float,
    irrigation_mm: float,
    fertilizer_N_kg_ha: float,
    fertilizer_P_kg_ha: float,
    fertilizer_K_kg_ha: float,
    pest_severity: float,
    soil_pH: float,
    planting_date: date | str | None = None,
    greenhouse_id: str = "API_GH",
    use_ensemble: bool = True,
) -> dict[str, Any]:
    """Hasat tarihi + rekolte tahmini (ensemble tercih edilir)."""
    try:
        from ml.prediction.serve import predict_harvest_payload

        return predict_harvest_payload(
            crop_type=crop_type,
            variety=variety,
            avg_temperature_C=avg_temperature_C,
            min_temperature_C=min_temperature_C,
            max_temperature_C=max_temperature_C,
            humidity_percent=humidity_percent,
            co2_ppm=co2_ppm,
            light_intensity_lux=light_intensity_lux,
            photoperiod_hours=photoperiod_hours,
            irrigation_mm=irrigation_mm,
            fertilizer_N_kg_ha=fertilizer_N_kg_ha,
            fertilizer_P_kg_ha=fertilizer_P_kg_ha,
            fertilizer_K_kg_ha=fertilizer_K_kg_ha,
            pest_severity=pest_severity,
            soil_pH=soil_pH,
            planting_date=planting_date,
            greenhouse_id=greenhouse_id,
            use_ensemble=use_ensemble,
        )
    except Exception as exc:
        logger.error("Tahmin hatası (fallback): %s", exc)
        from datetime import timedelta

        today = date.today()
        return {
            "predicted_days_remaining": 60,
            "predicted_harvest_date": today + timedelta(days=60),
            "predicted_yield_kg_m2": 15.0,
            "confidence_score": 0.5,
            "model_version": "v0.1.0-statistical-fallback",
            "planting_date": today.isoformat(),
            "details": {},
        }


def predict_weather(city: str = "İstanbul") -> dict[str, Any]:
    """Şehir bazlı Open-Meteo hava durumu."""
    from ml.prediction.serve import get_weather_payload

    return get_weather_payload(city=city)


def predict_disease_risk(
    greenhouse_id: str,
    avg_humidity_last_7d: Optional[float],
    avg_temp_last_7d: Optional[float],
    disease_prob_from_vision: Optional[float],
) -> dict:
    """Hastalık risk tahmini (vision + çevre)."""
    risk_components = []

    if disease_prob_from_vision is not None:
        risk_components.append(("vision", disease_prob_from_vision, 0.60))

    if avg_humidity_last_7d is not None:
        humidity_risk = max(0.0, min(1.0, (avg_humidity_last_7d - 50) / 40))
        risk_components.append(("humidity", humidity_risk, 0.25))

    if avg_temp_last_7d is not None:
        if avg_temp_last_7d < 10 or avg_temp_last_7d > 35:
            temp_risk = 0.6
        elif avg_temp_last_7d < 15 or avg_temp_last_7d > 30:
            temp_risk = 0.3
        else:
            temp_risk = 0.1
        risk_components.append(("temperature", temp_risk, 0.15))

    if not risk_components:
        risk_score = 0.5
        confidence = 0.2
    else:
        total_weight = sum(w for _, _, w in risk_components)
        risk_score = sum(score * weight for _, score, weight in risk_components) / total_weight
        confidence = min(0.9, 0.3 + len(risk_components) * 0.2)

    risk_score = round(min(1.0, max(0.0, risk_score)), 3)

    if risk_score >= DISEASE_RISK_HIGH_THRESHOLD:
        risk_level = "high"
        recommendation = (
            "Yüksek hastalık riski tespit edildi. "
            "Uzman değerlendirmesi ve ilaçlama gerekebilir."
        )
    elif risk_score >= 0.40:
        risk_level = "medium"
        recommendation = (
            "Orta düzey risk. Bitkileri yakından takip edin, "
            "hava koşullarına dikkat edin."
        )
    else:
        risk_level = "low"
        recommendation = "Düşük risk. Rutin takip yeterli."

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "confidence_score": round(confidence, 2),
        "model_version": _ML_MODEL_VERSION,
    }
