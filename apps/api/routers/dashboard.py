"""
Salkım AI — Dashboard Router'ı

Doküman 2.4:
  GET /api/v1/greenhouses/{id}/dashboard → Sera özet dashboard verisi

Flutter uygulamasının ana ekranı için tek endpoint'ten tüm özet verisi:
  - Son sensör okumaları
  - Aktif hasat tahmini
  - Son görüntü analiz sonucu
  - Hastalık risk durumu

JWT ile korunur.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models.analysis import Analysis
from apps.api.models.greenhouse import Greenhouse
from apps.api.models.image import Image
from apps.api.models.prediction import HarvestPrediction
from apps.api.models.sensor_reading import SensorReading
from apps.api.models.user import User
from apps.api.services.auth import get_current_user

router = APIRouter(tags=["dashboard"])


# --- Pydantic Şemaları ---

class LatestSensorData(BaseModel):
    time: Optional[datetime] = None
    temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    lux: Optional[float] = None
    is_stale: bool = False  # Son okuma >1 saat önceyse True


class LatestAnalysisData(BaseModel):
    image_id: Optional[str] = None
    maturity_class: Optional[str] = None
    maturity_score: Optional[float] = None
    disease_class: Optional[str] = None
    disease_prob: Optional[float] = None
    total_tomatoes: Optional[int] = None
    analyzed_at: Optional[datetime] = None


class HarvestForecast(BaseModel):
    predicted_harvest_date: Optional[str] = None  # ISO date string
    predicted_days_remaining: Optional[int] = None
    confidence_score: Optional[float] = None
    forecasted_at: Optional[datetime] = None


class DashboardResponse(BaseModel):
    greenhouse_id: uuid.UUID
    greenhouse_name: str
    generated_at: datetime

    # Sensör durumu
    latest_sensor: LatestSensorData

    # Son görüntü analizi
    latest_analysis: LatestAnalysisData

    # Hasat tahmini
    harvest_forecast: HarvestForecast

    # Uyarılar
    alerts: list[str]


# --- Endpoint ---

@router.get(
    "/{greenhouse_id}/dashboard",
    response_model=DashboardResponse,
    summary="Sera Dashboard Verisi",
)
def get_greenhouse_dashboard(
    greenhouse_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sera için tüm özet bilgisini tek sorguda döndürür.

    Flutter uygulamasının ana ekranı bu endpoint'i kullanır.
    Farklı veri kaynaklarını (sensör, analiz, tahmin) birleştirir.
    """
    # Sera sahiplik kontrolü
    greenhouse = db.query(Greenhouse).filter(
        Greenhouse.id == greenhouse_id,
        Greenhouse.user_id == user.id,
    ).first()

    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sera bulunamadı veya bu seraya erişim yetkiniz yok.",
        )

    now = datetime.now(timezone.utc)
    alerts: list[str] = []

    # --- 1. En son sensör okuması ---
    latest_sensor_record = (
        db.query(SensorReading)
        .filter(SensorReading.greenhouse_id == greenhouse_id)
        .order_by(SensorReading.time.desc())
        .first()
    )

    if latest_sensor_record:
        # Saat bilgisi naive ise UTC varsay
        sensor_time = latest_sensor_record.time
        if sensor_time.tzinfo is None:
            sensor_time = sensor_time.replace(tzinfo=timezone.utc)

        is_stale = (now - sensor_time) > timedelta(hours=1)
        if is_stale:
            alerts.append("⚠️ Sensör verisi 1 saatten eski — cihaz bağlantısını kontrol edin.")

        latest_sensor = LatestSensorData(
            time=sensor_time,
            temp_c=latest_sensor_record.temp_c,
            humidity_pct=latest_sensor_record.humidity_pct,
            lux=latest_sensor_record.lux,
            is_stale=is_stale,
        )

        # Sıcaklık uyarısı
        if latest_sensor_record.temp_c is not None:
            if latest_sensor_record.temp_c > 35:
                alerts.append("🌡️ Sera sıcaklığı kritik seviyede yüksek (>35°C).")
            elif latest_sensor_record.temp_c < 10:
                alerts.append("🌡️ Sera sıcaklığı düşük (<10°C) — bitki strese girebilir.")

        # Nem uyarısı
        if latest_sensor_record.humidity_pct is not None and latest_sensor_record.humidity_pct > 85:
            alerts.append("💧 Yüksek nem (%85+) — fungal hastalık riski artmış.")
    else:
        latest_sensor = LatestSensorData()
        alerts.append("📡 Sensör verisi bulunamadı — cihaz kurulumunu kontrol edin.")

    # --- 2. En son görüntü analizi ---
    latest_image = (
        db.query(Image)
        .filter(
            Image.status == "completed",
        )
        .order_by(Image.captured_at.desc())
        .first()
    )

    latest_analysis_data = LatestAnalysisData()
    if latest_image:
        analysis = (
            db.query(Analysis)
            .filter(Analysis.image_id == latest_image.id)
            .first()
        )
        if analysis:
            latest_analysis_data = LatestAnalysisData(
                image_id=str(latest_image.id),
                maturity_class=analysis.maturity_class,
                maturity_score=analysis.maturity_score,
                disease_class=analysis.disease_class,
                disease_prob=analysis.disease_prob,
                total_tomatoes=analysis.total_tomatoes,
                analyzed_at=analysis.processed_at,
            )

            # Hastalık uyarısı
            if analysis.disease_prob is not None and analysis.disease_prob > 0.70:
                alerts.append(
                    f"🔴 Yüksek hastalık riski! "
                    f"{analysis.disease_class} olasılığı: %{int(analysis.disease_prob * 100)}"
                )
            elif analysis.disease_prob is not None and analysis.disease_prob > 0.40:
                alerts.append(
                    f"🟡 Orta hastalık riski. "
                    f"{analysis.disease_class} belirtileri izleniyor."
                )

    # --- 3. En son hasat tahmini ---
    latest_prediction = (
        db.query(HarvestPrediction)
        .filter(HarvestPrediction.greenhouse_id == greenhouse_id)
        .order_by(HarvestPrediction.created_at.desc())
        .first()
    )

    if latest_prediction:
        harvest_forecast = HarvestForecast(
            predicted_harvest_date=(
                latest_prediction.predicted_harvest_date.isoformat()
                if latest_prediction.predicted_harvest_date
                else None
            ),
            predicted_days_remaining=latest_prediction.predicted_days_remaining,
            confidence_score=latest_prediction.confidence_score,
            forecasted_at=latest_prediction.created_at,
        )

        # Hasat yaklaşıyor uyarısı
        if latest_prediction.predicted_days_remaining is not None:
            if latest_prediction.predicted_days_remaining <= 3:
                alerts.append("🍅 Hasat zamanı yaklaştı! 3 gün veya daha az kaldı.")
            elif latest_prediction.predicted_days_remaining <= 7:
                alerts.append("🍅 Hasata 1 haftadan az kaldı.")
    else:
        harvest_forecast = HarvestForecast()

    return DashboardResponse(
        greenhouse_id=greenhouse_id,
        greenhouse_name=greenhouse.name,
        generated_at=now,
        latest_sensor=latest_sensor,
        latest_analysis=latest_analysis_data,
        harvest_forecast=harvest_forecast,
        alerts=alerts,
    )
