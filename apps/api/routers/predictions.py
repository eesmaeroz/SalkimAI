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
    gdd_accumulated: Optional[float] = Field(
        None, ge=0, description="Birikimli GDD (T1 modülünden veya hesaplanmış)"
    )
    days_since_planting: Optional[int] = Field(
        None, ge=0, le=365, description="Ekim tarihinden bu yana geçen gün"
    )
    avg_temp_last_7d: Optional[float] = Field(
        None, ge=-10, le=60, description="Son 7 günlük ortalama sıcaklık (°C)"
    )
    avg_humidity_last_7d: Optional[float] = Field(
        None, ge=0, le=100, description="Son 7 günlük ortalama nem (%)"
    )
    current_maturity_score: Optional[float] = Field(
        None, ge=0, le=1, description="Görüntü analizinden gelen olgunluk skoru"
    )


class HarvestPredictionResponse(BaseModel):
    prediction_id: uuid.UUID
    greenhouse_id: uuid.UUID
    predicted_harvest_date: Optional[date]
    predicted_days_remaining: Optional[int]
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
    summary="Hasat Tarihi Tahmini",
)
def request_harvest_prediction(
    body: HarvestPredictionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    XGBoost + LSTM ensemble modelini kullanarak hasat tarihi tahmini yapar.

    Feature'lar:
    - GDD (Growing Degree Days) birikimi
    - Ekim tarihinden bu yana geçen gün sayısı
    - Son 7 günlük hava koşulları (sıcaklık, nem)
    - Görüntü analizinden gelen olgunluk skoru

    Sonuç hem döndürülür hem de DB'ye yazılır (kalibrasyon için).
    """
    _verify_greenhouse_owner(body.greenhouse_id, user, db)

    # ML servisi çağır
    result = predict_harvest(
        greenhouse_id=str(body.greenhouse_id),
        gdd_accumulated=body.gdd_accumulated,
        days_since_planting=body.days_since_planting,
        avg_temp_last_7d=body.avg_temp_last_7d,
        avg_humidity_last_7d=body.avg_humidity_last_7d,
        current_maturity_score=body.current_maturity_score,
    )

    # DB'ye kaydet
    prediction = HarvestPrediction(
        greenhouse_id=body.greenhouse_id,
        gdd_accumulated=body.gdd_accumulated,
        days_since_planting=body.days_since_planting,
        avg_temp_last_7d=body.avg_temp_last_7d,
        avg_humidity_last_7d=body.avg_humidity_last_7d,
        current_maturity_score=body.current_maturity_score,
        predicted_harvest_date=result["predicted_harvest_date"],
        predicted_days_remaining=result["predicted_days_remaining"],
        confidence_score=result["confidence_score"],
        model_version=result["model_version"],
        raw_features=body.model_dump(exclude={"greenhouse_id"}),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

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
