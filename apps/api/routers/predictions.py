"""
Salkım AI — Predictions (Tahminleme) Router'ı

Doküman 2.4 (Faz 2, Gün 15–17) — T2 görevi:
  POST /api/v1/predictions/harvest       → Hasat tarihi tahmini iste
  POST /api/v1/predictions/disease_risk  → Hastalık risk tahmini iste
  GET  /api/v1/predictions/{greenhouse_id}/history  → Geçmiş tahminler

Tüm endpoint'ler JWT ile korunur.
Tahmin sonuçları PostgreSQL'e kalıcı olarak yazılır.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models.greenhouse import Greenhouse
from apps.api.models.prediction import HarvestPrediction
from apps.api.models.user import User
from apps.api.services.auth import get_current_user
from apps.api.services.prediction import predict_harvest, predict_disease_risk
from apps.api.services.metrics import HARVEST_PREDICTIONS_TOTAL

router = APIRouter(tags=["predictions"])


# --- Pydantic Şemaları ---

class HarvestPredictionRequest(BaseModel):
    greenhouse_id: uuid.UUID
    crop_type: str = Field(..., description="Bitki türü, örn: Tomato")
    variety: str = Field(..., description="Çeşit, örn: Beefsteak")
    avg_temperature_C: float = Field(..., description="Ortalama sıcaklık")
    min_temperature_C: float = Field(..., description="Min sıcaklık")
    max_temperature_C: float = Field(..., description="Max sıcaklık")
    humidity_percent: float = Field(..., description="Nem oranı")
    co2_ppm: float = Field(..., description="CO2 yoğunluğu")
    light_intensity_lux: float = Field(..., description="Işık yoğunluğu")
    photoperiod_hours: float = Field(..., description="Fotoperiyot saat")
    irrigation_mm: float = Field(..., description="Sulama miktarı mm")
    fertilizer_N_kg_ha: float = Field(..., description="Gübre N miktarı")
    fertilizer_P_kg_ha: float = Field(..., description="Gübre P miktarı")
    fertilizer_K_kg_ha: float = Field(..., description="Gübre K miktarı")
    pest_severity: float = Field(..., description="Zararlı seviyesi")
    soil_pH: float = Field(..., description="Toprak pH")


class HarvestPredictionResponse(BaseModel):
    prediction_id: uuid.UUID
    greenhouse_id: uuid.UUID
    predicted_harvest_date: Optional[date]
    predicted_days_remaining: Optional[int]
    predicted_yield_kg_m2: Optional[float]
    confidence_score: Optional[float]
    model_version: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DiseaseRiskRequest(BaseModel):
    greenhouse_id: uuid.UUID
    avg_humidity_last_7d: Optional[float] = Field(
        None, ge=0, le=100, description="Son 7 günlük ortalama nem (%)"
    )
    avg_temp_last_7d: Optional[float] = Field(
        None, ge=-10, le=60, description="Son 7 günlük ortalama sıcaklık (°C)"
    )
    disease_prob_from_vision: Optional[float] = Field(
        None, ge=0, le=1,
        description="Görüntü analizinden gelen hastalık olasılığı (Esma+Dilan'ın Vision servisi)"
    )


class DiseaseRiskResponse(BaseModel):
    greenhouse_id: uuid.UUID
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: str = Field(..., description="low | medium | high")
    recommendation: str
    confidence_score: float
    model_version: str


# --- Yardımcı ---

def _verify_greenhouse_owner(greenhouse_id: uuid.UUID, user: User, db: Session) -> Greenhouse:
    gh = db.query(Greenhouse).filter(
        Greenhouse.id == greenhouse_id,
        Greenhouse.user_id == user.id,
    ).first()
    if not gh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sera bulunamadı veya bu seraya erişim yetkiniz yok.",
        )
    return gh


# --- Endpoint'ler ---

@router.post(
    "/harvest",
    response_model=HarvestPredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hasat Tarihi ve Rekolte Tahmini",
)
def create_harvest_prediction(
    request: HarvestPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gh = _verify_greenhouse_owner(request.greenhouse_id, current_user, db)

    prediction_result = predict_harvest(
        crop_type=request.crop_type,
        variety=request.variety,
        avg_temperature_C=request.avg_temperature_C,
        min_temperature_C=request.min_temperature_C,
        max_temperature_C=request.max_temperature_C,
        humidity_percent=request.humidity_percent,
        co2_ppm=request.co2_ppm,
        light_intensity_lux=request.light_intensity_lux,
        photoperiod_hours=request.photoperiod_hours,
        irrigation_mm=request.irrigation_mm,
        fertilizer_N_kg_ha=request.fertilizer_N_kg_ha,
        fertilizer_P_kg_ha=request.fertilizer_P_kg_ha,
        fertilizer_K_kg_ha=request.fertilizer_K_kg_ha,
        pest_severity=request.pest_severity,
        soil_pH=request.soil_pH,
    )

    pred = HarvestPrediction(
        greenhouse_id=gh.id,
        gdd_accumulated=0.0, # Not used in new model but kept for DB compat
        days_since_planting=0,
        predicted_harvest_date=prediction_result["predicted_harvest_date"],
        predicted_days_remaining=prediction_result["predicted_days_remaining"],
        predicted_yield_kg_m2=prediction_result["predicted_yield_kg_m2"],
        confidence_score=prediction_result["confidence_score"],
        model_version=prediction_result["model_version"],
    )
    db.add(pred)
    db.commit()

    # Prometheus metric güncelle
    HARVEST_PREDICTIONS_TOTAL.inc()

    return HarvestPredictionResponse(
        prediction_id=prediction.id,
        greenhouse_id=prediction.greenhouse_id,
        predicted_harvest_date=prediction.predicted_harvest_date,
        predicted_days_remaining=prediction.predicted_days_remaining,
        confidence_score=prediction.confidence_score,
        model_version=prediction.model_version,
        created_at=prediction.created_at,
    )


@router.post(
    "/disease_risk",
    response_model=DiseaseRiskResponse,
    summary="Hastalık Risk Tahmini",
)
def request_disease_risk(
    body: DiseaseRiskRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Görüntü analizi + çevre koşullarını birleştirerek hastalık riski hesaplar.

    Vision servisi (Esma + Dilan) görüntü analizinden `disease_prob_from_vision`
    alanını doldurarak bu endpoint'i çağırır.

    Hastalık riski yüksekse (>0.70) mobil uygulama FCM bildirimi gönderir.
    """
    _verify_greenhouse_owner(body.greenhouse_id, user, db)

    result = predict_disease_risk(
        greenhouse_id=str(body.greenhouse_id),
        avg_humidity_last_7d=body.avg_humidity_last_7d,
        avg_temp_last_7d=body.avg_temp_last_7d,
        disease_prob_from_vision=body.disease_prob_from_vision,
    )

    return DiseaseRiskResponse(
        greenhouse_id=body.greenhouse_id,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        recommendation=result["recommendation"],
        confidence_score=result["confidence_score"],
        model_version=result["model_version"],
    )


@router.get(
    "/{greenhouse_id}/history",
    response_model=List[HarvestPredictionResponse],
    summary="Geçmiş Hasat Tahminleri",
)
def get_prediction_history(
    greenhouse_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Bir seranın geçmiş hasat tahminlerini getirir.
    Faz 3 model kalibrasyonu için kullanılır.
    """
    _verify_greenhouse_owner(greenhouse_id, user, db)

    predictions = (
        db.query(HarvestPrediction)
        .filter(HarvestPrediction.greenhouse_id == greenhouse_id)
        .order_by(HarvestPrediction.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        HarvestPredictionResponse(
            prediction_id=p.id,
            greenhouse_id=p.greenhouse_id,
            predicted_harvest_date=p.predicted_harvest_date,
            predicted_days_remaining=p.predicted_days_remaining,
            confidence_score=p.confidence_score,
            model_version=p.model_version,
            created_at=p.created_at,
        )
        for p in predictions
    ]
