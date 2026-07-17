"""
Salkım AI — HarvestPrediction (Hasat Tahmini) Modeli

Faz 2 (Gün 15–17) — T2 görevi: Tahminleme servis API

Bu tablo, Arif'in (T1) XGBoost + LSTM ensemble modelinin
ürettiği hasat tahminlerini kalıcı olarak depolar.

Her sera için birden fazla tahmin kaydı olabilir
(zamanla tahmin kalibrasyonu yapılır — Faz 3).
"""

import uuid
from datetime import date, datetime
from typing import Optional, Any

from sqlalchemy import Float, String, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import Base, TimestampMixin


class HarvestPrediction(TimestampMixin, Base):
    """
    XGBoost + LSTM ensemble modelinden üretilen hasat tahmini.

    Doküman 2.4:
      POST /api/v1/predictions/harvest → bu tabloya yazılır
      GET  /api/v1/greenhouses/{id}/dashboard → buradan okunur
    """

    __tablename__ = "harvest_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    greenhouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("greenhouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tahmin yapılan sera",
    )

    # --- Tahmin girdileri (Feature snapshot) ---
    gdd_accumulated: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Birikimli GDD (Growing Degree Days) — T1 feature",
    )
    days_since_planting: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Ekim tarihinden bu yana geçen gün sayısı",
    )
    avg_temp_last_7d: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Son 7 günlük ortalama sıcaklık (°C)",
    )
    avg_humidity_last_7d: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Son 7 günlük ortalama nem (%)",
    )
    current_maturity_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Görüntü analizinden gelen güncel olgunluk skoru (0-1)",
    )

    # --- Tahmin çıktıları ---
    predicted_harvest_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Tahmin edilen hasat tarihi",
    )
    predicted_days_remaining: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Hasata kalan tahmini gün sayısı",
    )
    predicted_yield_kg_m2: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Tahmini Rekolte kg/m2",
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Model güven skoru (0-1)",
    )

    # --- Model meta ---
    model_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Doküman 2.7: XGBoost+LSTM ensemble versiyonu",
    )
    raw_features: Mapped[Optional[Any]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Modele verilen tüm feature değerleri (debug + kalibrasyon için)",
    )

    def __repr__(self) -> str:
        return (
            f"<HarvestPrediction(greenhouse={self.greenhouse_id}, "
            f"harvest={self.predicted_harvest_date}, "
            f"days_left={self.predicted_days_remaining})>"
        )
