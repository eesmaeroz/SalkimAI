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


def predict_harvest(
    greenhouse_id: str,
    gdd_accumulated: Optional[float],
    days_since_planting: Optional[int],
    avg_temp_last_7d: Optional[float],
    avg_humidity_last_7d: Optional[float],
    current_maturity_score: Optional[float],
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
        # Arif'in modeli hazır olduğunda bu blok aktif edilecek
        # from ml.prediction.serve.harvest_predictor import predict as ml_predict
        # return ml_predict(gdd_accumulated, days_since_planting, ...)
        return _statistical_fallback(
            gdd_accumulated=gdd_accumulated,
            days_since_planting=days_since_planting,
            avg_temp_last_7d=avg_temp_last_7d,
            avg_humidity_last_7d=avg_humidity_last_7d,
            current_maturity_score=current_maturity_score,
        )
    except Exception as exc:
        logger.error(f"Tahmin hatası (fallback'e geçiliyor): {exc}")
        return _statistical_fallback(
            gdd_accumulated=gdd_accumulated,
            days_since_planting=days_since_planting,
            avg_temp_last_7d=avg_temp_last_7d,
            avg_humidity_last_7d=avg_humidity_last_7d,
            current_maturity_score=current_maturity_score,
        )


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
