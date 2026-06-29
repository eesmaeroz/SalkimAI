"""
Salkım AI — Analysis (Analiz) Modeli

Doküman 5.1 + 2.6: analyses tablosu
Alanlar: id, image_id (UNIQUE), maturity_class, maturity_score,
         disease_class, disease_prob, total_tomatoes, raw_results (JSON),
         model_version, processed_at
İlişkiler: image (1:1)

Bu tablo Celery worker'ın inference sonrasında yazdığı
kalıcı sonuçları depolar. Redis result backend'inden BAĞIMSIZ.
"""

import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, TimestampMixin

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.api.models.image import Image


class Analysis(TimestampMixin, Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Her görüntüye en fazla bir analiz (1:1)",
    )
    maturity_class: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Baskın olgunluk sınıfı: green/turning/pink/red/overripe",
    )
    maturity_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Olgunluk güven skoru (0-1)",
    )
    disease_class: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Baskın hastalık sınıfı: healthy/early_blight/late_blight/pest/mosaic",
    )
    disease_prob: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Hastalık olasılık skoru (0-1)",
    )
    total_tomatoes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="YOLO tarafından tespit edilen toplam domates sayısı",
    )
    raw_results: Mapped[Optional[Any]] = mapped_column(
        JSONB, nullable=True,
        comment="Her domates için detaylı analiz JSON'ı",
    )
    model_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Doküman 2.7: Model versiyonu, geriye dönük debugging için",
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True,
        comment="Analiz tamamlanma zamanı",
    )

    # İlişkiler
    image: Mapped["Image"] = relationship(back_populates="analysis")

    def __repr__(self) -> str:
        return (
            f"<Analysis(id={self.id}, maturity={self.maturity_class}, "
            f"disease={self.disease_class}, tomatoes={self.total_tomatoes})>"
        )
