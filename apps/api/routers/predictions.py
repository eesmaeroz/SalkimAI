"""
Salkım AI — Predictions (Tahminleme) Router'ı

  POST /api/v1/predictions/harvest          → Hasat + rekolte (ensemble tercih)
  POST /api/v1/predictions/harvest/ensemble → XGBoost+LSTM ensemble detaylı
  GET  /api/v1/predictions/weather          → Open-Meteo şehir hava durumu
  POST /api/v1/predictions/disease_risk     → Hastalık riski
  GET  /api/v1/predictions/{greenhouse_id}/history
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models.greenhouse import Greenhouse
from apps.api.models.prediction import HarvestPrediction
from apps.api.models.user import User
from apps.api.services.auth import get_current_user
from apps.api.services.metrics import HARVEST_PREDICTIONS_TOTAL
from apps.api.services.prediction import (
    predict_disease_risk,
    predict_harvest,
    predict_weather,
)

router = APIRouter(tags=["predictions"])


class HarvestPredictionRequest(BaseModel):
    greenhouse_id: uuid.UUID
    crop_type: str = Field(..., description="Bitki türü, örn: Tomato")
    variety: str = Field(..., description="Çeşit, örn: Beefsteak")
    planting_date: Optional[date] = Field(
        None, description="Ekim tarihi (yoksa bugün). Hasat tarihi buna göre hesaplanır."
    )
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
    use_ensemble: bool = Field(
        True,
        description="True: XGBoost+LSTM ensemble (varsa). False: sadece XGBoost/legacy.",
    )


class HarvestPredictionResponse(BaseModel):
    prediction_id: uuid.UUID
    greenhouse_id: uuid.UUID
    predicted_harvest_date: Optional[date]
    predicted_days_remaining: Optional[int]
    predicted_yield_kg_m2: Optional[float]
    confidence_score: Optional[float]
    model_version: Optional[str]
    created_at: datetime
    details: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class EnsembleHarvestResponse(BaseModel):
    prediction_id: uuid.UUID
    greenhouse_id: uuid.UUID
    planting_date: Optional[date]
    predicted_harvest_date: Optional[date]
    predicted_days_remaining: Optional[int]
    predicted_days_xgb: Optional[int] = None
    predicted_days_lstm: Optional[int] = None
    predicted_days_ensemble_raw: Optional[int] = None
    predicted_yield_kg_m2: Optional[float]
    confidence_score: Optional[float]
    model_version: Optional[str]
    created_at: datetime


class WeatherResponse(BaseModel):
    sehir: Optional[str]
    il: Optional[str]
    ulke: Optional[str]
    koordinatlar: Dict[str, Any]
    guncel: Dict[str, Any]
    tahmin: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None


class DiseaseRiskRequest(BaseModel):
    greenhouse_id: uuid.UUID
    avg_humidity_last_7d: Optional[float] = Field(
        None, ge=0, le=100, description="Son 7 günlük ortalama nem (%)"
    )
    avg_temp_last_7d: Optional[float] = Field(
        None, ge=-10, le=60, description="Son 7 günlük ortalama sıcaklık (°C)"
    )
    disease_prob_from_vision: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Görüntü analizinden gelen hastalık olasılığı (Vision servisi)",
    )


class DiseaseRiskResponse(BaseModel):
    greenhouse_id: uuid.UUID
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: str = Field(..., description="low | medium | high")
    recommendation: str
    confidence_score: float
    model_version: str


def _verify_greenhouse_owner(
    greenhouse_id: uuid.UUID, user: User, db: Session
) -> Greenhouse:
    gh = (
        db.query(Greenhouse)
        .filter(
            Greenhouse.id == greenhouse_id,
            Greenhouse.user_id == user.id,
        )
        .first()
    )
    if not gh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sera bulunamadı veya bu seraya erişim yetkiniz yok.",
        )
    return gh


def _run_and_persist_harvest(
    request: HarvestPredictionRequest,
    current_user: User,
    db: Session,
    *,
    force_ensemble: bool | None = None,
) -> tuple[HarvestPrediction, dict]:
    gh = _verify_greenhouse_owner(request.greenhouse_id, current_user, db)
    use_ensemble = request.use_ensemble if force_ensemble is None else force_ensemble

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
        planting_date=request.planting_date,
        greenhouse_id=str(gh.id),
        use_ensemble=use_ensemble,
    )

    pred = HarvestPrediction(
        greenhouse_id=gh.id,
        gdd_accumulated=0.0,
        days_since_planting=0,
        predicted_harvest_date=prediction_result["predicted_harvest_date"],
        predicted_days_remaining=prediction_result["predicted_days_remaining"],
        predicted_yield_kg_m2=prediction_result["predicted_yield_kg_m2"],
        confidence_score=prediction_result["confidence_score"],
        model_version=prediction_result["model_version"],
        raw_features={
            "planting_date": prediction_result.get("planting_date"),
            "details": prediction_result.get("details") or {},
            "use_ensemble": use_ensemble,
        },
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    HARVEST_PREDICTIONS_TOTAL.inc()
    return pred, prediction_result


@router.post(
    "/harvest",
    response_model=HarvestPredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hasat Tarihi ve Rekolte Tahmini",
    description=(
        "Mobil / genel istemciler için ana hasat endpoint'i. "
        "Varsayılan olarak XGBoost+LSTM ensemble + calibration kullanır; "
        "artefact yoksa XGBoost veya legacy modele düşer."
    ),
)
def create_harvest_prediction(
    request: HarvestPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pred, result = _run_and_persist_harvest(request, current_user, db)
    return HarvestPredictionResponse(
        prediction_id=pred.id,
        greenhouse_id=pred.greenhouse_id,
        predicted_harvest_date=pred.predicted_harvest_date,
        predicted_days_remaining=pred.predicted_days_remaining,
        predicted_yield_kg_m2=pred.predicted_yield_kg_m2,
        confidence_score=pred.confidence_score,
        model_version=pred.model_version,
        created_at=pred.created_at,
        details=result.get("details") or {},
    )


@router.post(
    "/harvest/ensemble",
    response_model=EnsembleHarvestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ensemble Hasat Tahmini (XGBoost + LSTM)",
    description=(
        "48 timestep LSTM olgunluk trendi + XGBoost ağırlıklı average ve "
        "isotonic calibration. Mobil detay ekranı için XGB/LSTM kırılımlarını döner."
    ),
)
def create_ensemble_harvest_prediction(
    request: HarvestPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request.use_ensemble = True
    pred, result = _run_and_persist_harvest(
        request, current_user, db, force_ensemble=True
    )
    details = result.get("details") or {}
    planting = request.planting_date or date.today()
    return EnsembleHarvestResponse(
        prediction_id=pred.id,
        greenhouse_id=pred.greenhouse_id,
        planting_date=planting,
        predicted_harvest_date=pred.predicted_harvest_date,
        predicted_days_remaining=pred.predicted_days_remaining,
        predicted_days_xgb=details.get("predicted_days_xgb"),
        predicted_days_lstm=details.get("predicted_days_lstm"),
        predicted_days_ensemble_raw=details.get("predicted_days_ensemble_raw"),
        predicted_yield_kg_m2=pred.predicted_yield_kg_m2,
        confidence_score=pred.confidence_score,
        model_version=pred.model_version,
        created_at=pred.created_at,
    )


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Şehir Hava Durumu (Open-Meteo)",
    description=(
        "Geocoding ile şehir koordinata çevrilir, ardından 7 günlük forecast alınır. "
        "Mobil uygulamalar için JWT korumalıdır."
    ),
)
def get_city_weather(
    city: str = Query(default="İstanbul", min_length=2, description="Şehir adı"),
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        report = predict_weather(city=city)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hava durumu servisine ulaşılamadı: {exc}",
        ) from exc

    return WeatherResponse(
        sehir=report.get("sehir"),
        il=report.get("il"),
        ulke=report.get("ulke"),
        koordinatlar=report.get("koordinatlar") or {},
        guncel=report.get("guncel") or {},
        tahmin=report.get("tahmin") or [],
        summary=report.get("summary"),
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
    """Bir seranın geçmiş hasat tahminlerini getirir."""
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
            predicted_yield_kg_m2=p.predicted_yield_kg_m2,
            confidence_score=p.confidence_score,
            model_version=p.model_version,
            created_at=p.created_at,
            details=(p.raw_features or {}).get("details")
            if isinstance(p.raw_features, dict)
            else None,
        )
        for p in predictions
    ]
