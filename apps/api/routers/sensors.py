"""
Salkım AI — Sensors (Sensör) Router'ı

Doküman 2.4, 2.5 (TimescaleDB hypertable):
  POST /api/v1/sensors/readings              → Tek veya batch sensör okuması kaydet
  GET  /api/v1/sensors/{greenhouse_id}/readings  → Ham okumalar (zaman aralığı filtresi)
  GET  /api/v1/sensors/{greenhouse_id}/summary   → Saatlik/günlük özet (continuous aggregate)

Tüm endpoint'ler JWT ile korunur.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models.greenhouse import Greenhouse
from apps.api.models.sensor_reading import SensorReading
from apps.api.models.user import User
from apps.api.services.auth import get_current_user

router = APIRouter(tags=["sensors"])


# --- Pydantic Şemaları ---

class SensorReadingIn(BaseModel):
    greenhouse_id: uuid.UUID
    time: Optional[datetime] = Field(
        default=None,
        description="Ölçüm zamanı (UTC). Boş bırakılırsa sunucu zamanı kullanılır.",
    )
    temp_c: Optional[float] = Field(None, ge=-50, le=100, description="Sıcaklık (°C)")
    humidity_pct: Optional[float] = Field(None, ge=0, le=100, description="Nem (%)")
    lux: Optional[float] = Field(None, ge=0, description="Işık yoğunluğu (lux)")


class SensorReadingOut(BaseModel):
    greenhouse_id: uuid.UUID
    time: datetime
    temp_c: Optional[float]
    humidity_pct: Optional[float]
    lux: Optional[float]

    model_config = {"from_attributes": True}


class BatchReadingIn(BaseModel):
    readings: List[SensorReadingIn] = Field(..., min_length=1, max_length=500)


class BatchReadingOut(BaseModel):
    inserted: int
    message: str


class SensorSummaryOut(BaseModel):
    greenhouse_id: uuid.UUID
    bucket: datetime
    avg_temp_c: Optional[float]
    avg_humidity_pct: Optional[float]
    avg_lux: Optional[float]
    min_temp_c: Optional[float]
    max_temp_c: Optional[float]
    reading_count: int


# --- Yardımcı ---

def _verify_greenhouse_owner(greenhouse_id: uuid.UUID, user: User, db: Session) -> Greenhouse:
    """Seranın mevcut kullanıcıya ait olduğunu doğrular."""
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
    "/readings",
    response_model=SensorReadingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Sensör Okuması Kaydet",
)
def create_sensor_reading(
    body: SensorReadingIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tek bir sensör okumasını kaydeder.
    time alanı boş bırakılırsa UTC şimdiki zamanı kullanılır.
    """
    _verify_greenhouse_owner(body.greenhouse_id, user, db)

    reading_time = body.time or datetime.now(timezone.utc)

    record = SensorReading(
        time=reading_time,
        greenhouse_id=body.greenhouse_id,
        temp_c=body.temp_c,
        humidity_pct=body.humidity_pct,
        lux=body.lux,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/readings/batch",
    response_model=BatchReadingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Toplu Sensör Okuması Kaydet",
)
def create_sensor_readings_batch(
    body: BatchReadingIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    IoT cihazlarından gelen toplu sensör okumalarını batch olarak kaydeder.
    Maksimum 500 kayıt.

    Tüm readings'teki greenhouse_id'ler kullanıcıya ait olmalıdır.
    """
    # Benzersiz greenhouse_id'leri doğrula
    greenhouse_ids = {r.greenhouse_id for r in body.readings}
    for gid in greenhouse_ids:
        _verify_greenhouse_owner(gid, user, db)

    now = datetime.now(timezone.utc)
    records = [
        SensorReading(
            time=r.time or now,
            greenhouse_id=r.greenhouse_id,
            temp_c=r.temp_c,
            humidity_pct=r.humidity_pct,
            lux=r.lux,
        )
        for r in body.readings
    ]

    db.add_all(records)
    db.commit()

    return BatchReadingOut(
        inserted=len(records),
        message=f"{len(records)} sensör okuması başarıyla kaydedildi.",
    )


@router.get(
    "/{greenhouse_id}/readings",
    response_model=List[SensorReadingOut],
    summary="Ham Sensör Okumalarını Getir",
)
def get_sensor_readings(
    greenhouse_id: uuid.UUID,
    start: Optional[datetime] = Query(
        default=None,
        description="Başlangıç zamanı (ISO 8601 UTC). Varsayılan: 24 saat önce.",
    ),
    end: Optional[datetime] = Query(
        default=None,
        description="Bitiş zamanı (ISO 8601 UTC). Varsayılan: şimdi.",
    ),
    limit: int = Query(default=500, ge=1, le=5000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Belirtilen zaman aralığındaki ham sensör okumalarını getirir.
    TimescaleDB hypertable üzerinde zaman bazlı partition pruning ile hızlı çalışır.
    """
    _verify_greenhouse_owner(greenhouse_id, user, db)

    now = datetime.now(timezone.utc)
    start = start or (now - timedelta(hours=24))
    end = end or now

    readings = (
        db.query(SensorReading)
        .filter(
            SensorReading.greenhouse_id == greenhouse_id,
            SensorReading.time >= start,
            SensorReading.time <= end,
        )
        .order_by(SensorReading.time.desc())
        .limit(limit)
        .all()
    )

    return readings


@router.get(
    "/{greenhouse_id}/summary",
    response_model=List[SensorSummaryOut],
    summary="Sensör Saatlik/Günlük Özet",
)
def get_sensor_summary(
    greenhouse_id: uuid.UUID,
    bucket_interval: str = Query(
        default="1 hour",
        description="TimescaleDB time_bucket aralığı. Örn: '1 hour', '1 day', '6 hours'",
        pattern=r"^\d+ (minute|minutes|hour|hours|day|days)$",
    ),
    start: Optional[datetime] = Query(
        default=None,
        description="Başlangıç zamanı (UTC). Varsayılan: 7 gün önce.",
    ),
    end: Optional[datetime] = Query(
        default=None,
        description="Bitiş zamanı (UTC). Varsayılan: şimdi.",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    TimescaleDB `time_bucket()` fonksiyonu ile saatlik/günlük agregasyon döndürür.

    Bu endpoint Grafana dashboard ve Flutter sera özeti için tasarlanmıştır.
    TimescaleDB yoksa standart PostgreSQL date_trunc ile fallback çalışır.
    """
    _verify_greenhouse_owner(greenhouse_id, user, db)

    now = datetime.now(timezone.utc)
    start = start or (now - timedelta(days=7))
    end = end or now

    # TimescaleDB time_bucket kullan; yoksa date_trunc fallback
    sql = text(
        """
        SELECT
            time_bucket(:interval, time)             AS bucket,
            :greenhouse_id::uuid                     AS greenhouse_id,
            AVG(temp_c)                              AS avg_temp_c,
            AVG(humidity_pct)                        AS avg_humidity_pct,
            AVG(lux)                                 AS avg_lux,
            MIN(temp_c)                              AS min_temp_c,
            MAX(temp_c)                              AS max_temp_c,
            COUNT(*)                                 AS reading_count
        FROM sensor_readings
        WHERE
            greenhouse_id = :greenhouse_id
            AND time >= :start
            AND time <= :end
        GROUP BY bucket
        ORDER BY bucket DESC
        LIMIT 500
        """
    )

    try:
        rows = db.execute(
            sql,
            {
                "interval": bucket_interval,
                "greenhouse_id": str(greenhouse_id),
                "start": start,
                "end": end,
            },
        ).fetchall()
    except Exception:
        # TimescaleDB time_bucket yoksa date_trunc ile fallback
        sql_fallback = text(
            """
            SELECT
                date_trunc(:trunc_unit, time)            AS bucket,
                :greenhouse_id::uuid                     AS greenhouse_id,
                AVG(temp_c)                              AS avg_temp_c,
                AVG(humidity_pct)                        AS avg_humidity_pct,
                AVG(lux)                                 AS avg_lux,
                MIN(temp_c)                              AS min_temp_c,
                MAX(temp_c)                              AS max_temp_c,
                COUNT(*)::int                            AS reading_count
            FROM sensor_readings
            WHERE
                greenhouse_id = :greenhouse_id
                AND time >= :start
                AND time <= :end
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT 500
            """
        )
        trunc_unit = "hour" if "hour" in bucket_interval else "day"
        rows = db.execute(
            sql_fallback,
            {
                "trunc_unit": trunc_unit,
                "greenhouse_id": str(greenhouse_id),
                "start": start,
                "end": end,
            },
        ).fetchall()

    return [
        SensorSummaryOut(
            greenhouse_id=greenhouse_id,
            bucket=row.bucket,
            avg_temp_c=round(row.avg_temp_c, 2) if row.avg_temp_c is not None else None,
            avg_humidity_pct=round(row.avg_humidity_pct, 2) if row.avg_humidity_pct is not None else None,
            avg_lux=round(row.avg_lux, 2) if row.avg_lux is not None else None,
            min_temp_c=round(row.min_temp_c, 2) if row.min_temp_c is not None else None,
            max_temp_c=round(row.max_temp_c, 2) if row.max_temp_c is not None else None,
            reading_count=int(row.reading_count),
        )
        for row in rows
    ]
