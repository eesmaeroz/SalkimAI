"""
Salkım AI — Tahminleme Servisi (ML Bridge)

Bu modül, Arif'in (T1) XGBoost + LSTM ensemble modelini
API katmanına bağlar.

Faz 2 (Gün 15–17): T2 — Prediction Service API

Model Entegrasyon Stratejisi:
  - Arif'in modeli hazır değilse: istatistiksel fallback tahmin
  - Arif'in modeli hazır olduğunda: ml.prediction.serve modülünden import

Doküman 2.7: Model versiyonlama — her tahminle model versiyonu saklanır.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# --- Sabitler ---

# Arif'in modeli entegre edildiğinde buradan çekilecek
_ML_MODEL_VERSION = "v0.1.0-xgboost-statistical-fallback"

# Domates olgunluk takvimi: GDD (Growing Degree Days) tabanlı
# Referans: ortalama domates çeşidi için ekim → hasat = ~1000–1200 GDD
GDD_HARVEST_THRESHOLD = 1100.0

# Hastalık riski eşiği (0–1 ölçeği)
DISEASE_RISK_HIGH_THRESHOLD = 0.70


import joblib
import pandas as pd

# Global loaded models
_maturity_model = None
_yield_model = None

def _load_models():
    global _maturity_model, _yield_model
    if _maturity_model is None or _yield_model is None:
        try:
            _maturity_model = joblib.load("models/maturity_model.pkl")
            _yield_model = joblib.load("models/yield_model.pkl")
        except Exception as e:
            logger.error(f"Failed to load XGBoost models: {e}")

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
) -> dict:
    """
    Hasat tarihi tahmini.

    Faz 2'de Arif'in XGBoost modeli hazır olduğunda bu fonksiyon
    ml.prediction.serve modülündeki inference fonksiyonunu çağıracak.
    Şu an istatistiksel fallback ile çalışır.

    Returns:
        dict: {
            predicted_days_remaining: int,
            predicted_harvest_date: date,
            confidence_score: float,
            model_version: str,
        }
    """
    try:
        _load_models()
        if _maturity_model is None or _yield_model is None:
            raise Exception("Models not loaded.")

        df_input = pd.DataFrame([{
            'crop_type': crop_type,
            'variety': variety,
            'avg_temperature_C': avg_temperature_C,
            'min_temperature_C': min_temperature_C,
            'max_temperature_C': max_temperature_C,
            'humidity_percent': humidity_percent,
            'co2_ppm': co2_ppm,
            'light_intensity_lux': light_intensity_lux,
            'photoperiod_hours': photoperiod_hours,
            'irrigation_mm': irrigation_mm,
            'fertilizer_N_kg_ha': fertilizer_N_kg_ha,
            'fertilizer_P_kg_ha': fertilizer_P_kg_ha,
            'fertilizer_K_kg_ha': fertilizer_K_kg_ha,
            'pest_severity': pest_severity,
            'soil_pH': soil_pH
        }])

        pred_maturity = float(_maturity_model.predict(df_input)[0])
        pred_yield = float(_yield_model.predict(df_input)[0])
        
        harvest_date = date.today() + timedelta(days=int(pred_maturity))

        return {
            "predicted_days_remaining": int(pred_maturity),
            "predicted_harvest_date": harvest_date,
            "predicted_yield_kg_m2": round(pred_yield, 2),
            "confidence_score": 0.85,
            "model_version": "v1.0.0-xgboost",
        }
    except Exception as exc:
        logger.error(f"Tahmin hatası (fallback'e geçiliyor): {exc}")
        return {
            "predicted_days_remaining": 60,
            "predicted_harvest_date": date.today() + timedelta(days=60),
            "predicted_yield_kg_m2": 15.0,
            "confidence_score": 0.5,
            "model_version": "v0.1.0-statistical-fallback",
        }


def predict_disease_risk(
    greenhouse_id: str,
    avg_humidity_last_7d: Optional[float],
    avg_temp_last_7d: Optional[float],
    disease_prob_from_vision: Optional[float],
) -> dict:
    """
    Hastalık risk tahmini.

    Görüntü analizi sonuçları (Esma + Dilan'ın Vision servisi) ile
    çevre koşullarını birleştirerek risk seviyesi hesaplar.

    Returns:
        dict: {
            risk_score: float (0-1),
            risk_level: str ("low" | "medium" | "high"),
            recommendation: str,
            model_version: str,
        }
    """
    # Ağırlıklı risk hesabı
    # Görüntü analizi %60, çevre koşulları %40 ağırlık
    risk_components = []

    # Görüntü bazlı hastalık olasılığı (V1+V2'den)
    if disease_prob_from_vision is not None:
        risk_components.append(("vision", disease_prob_from_vision, 0.60))

    # Nem bazlı risk (yüksek nem → fungal hastalık riski)
    if avg_humidity_last_7d is not None:
        # >80% nem = yüksek risk, <50% = düşük risk
        humidity_risk = max(0.0, min(1.0, (avg_humidity_last_7d - 50) / 40))
        risk_components.append(("humidity", humidity_risk, 0.25))

    # Sıcaklık bazlı risk (15-25°C arası optimum, dışında hastalık artar)
    if avg_temp_last_7d is not None:
        if avg_temp_last_7d < 10 or avg_temp_last_7d > 35:
            temp_risk = 0.6
        elif avg_temp_last_7d < 15 or avg_temp_last_7d > 30:
            temp_risk = 0.3
        else:
            temp_risk = 0.1
        risk_components.append(("temperature", temp_risk, 0.15))

    if not risk_components:
        # Hiç veri yoksa orta risk döndür
        risk_score = 0.5
        confidence = 0.2
    else:
        total_weight = sum(w for _, _, w in risk_components)
        risk_score = sum(score * weight for _, score, weight in risk_components) / total_weight
        confidence = min(0.9, 0.3 + len(risk_components) * 0.2)

    risk_score = round(min(1.0, max(0.0, risk_score)), 3)

    # Risk seviyesi ve tavsiye
    if risk_score >= DISEASE_RISK_HIGH_THRESHOLD:
        risk_level = "high"
        recommendation = (
            "⚠️ Yüksek hastalık riski tespit edildi. "
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


# --- Dahili Yardımcılar ---

def _statistical_fallback(
    gdd_accumulated: Optional[float],
    days_since_planting: Optional[int],
    avg_temp_last_7d: Optional[float],
    avg_humidity_last_7d: Optional[float],
    current_maturity_score: Optional[float],
) -> dict:
    """
    Arif'in XGBoost modeli olmadan istatistiksel tahmin.

    GDD (Growing Degree Days) tabanlı basit model:
    - Birikimli GDD threshold'a ne kadar yakınsa hasata o kadar yakın.
    - Günlük GDD = max(0, ort_sıcaklık - 10) (domates base temp = 10°C)
    """
    today = date.today()

    # GDD tabanlı tahmin
    if gdd_accumulated is not None and avg_temp_last_7d is not None:
        gdd_remaining = max(0, GDD_HARVEST_THRESHOLD - gdd_accumulated)
        daily_gdd = max(0.1, avg_temp_last_7d - 10)  # sıfıra bölme koruması
        days_remaining = int(gdd_remaining / daily_gdd)
        confidence = 0.55
    elif days_since_planting is not None:
        # Sadece gün sayısı varsa: ortalama domates = 70 gün → hasat
        days_remaining = max(0, 70 - days_since_planting)
        confidence = 0.35
    else:
        # Hiç veri yoksa 30 gün default
        days_remaining = 30
        confidence = 0.20

    # Olgunluk skoru varsa tahmin ince ayarı
    if current_maturity_score is not None and current_maturity_score > 0.7:
        days_remaining = max(0, days_remaining - 5)
        confidence = min(0.80, confidence + 0.15)

    # Sınır: 0–120 gün
    days_remaining = max(0, min(120, days_remaining))
    harvest_date = today + timedelta(days=days_remaining)

    return {
        "predicted_days_remaining": days_remaining,
        "predicted_harvest_date": harvest_date,
        "confidence_score": round(confidence, 2),
        "model_version": _ML_MODEL_VERSION,
    }
