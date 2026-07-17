"""
Salkım AI — Image (Görüntü) Modeli

Doküman 5.1: images tablosu
Alanlar: id, plant_id, minio_url, original_filename, captured_at, quality_score, task_id, status
İlişkiler: plant (N:1), analysis (1:1)

Not: plant_id nullable — Faz 1'de kullanıcı henüz bitki kaydı olmadan fotoğraf yükleyebilir.
task_id Celery görev ID'sidir, asenkron polling için kullanılır.
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.models.plant import Plant
    from apps.api.models.analysis import Analysis


class Image(TimestampMixin, Base):
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    plant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("plants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Nullable — Faz 1'de bitki kaydı olmadan fotoğraf yüklenebilir",
    )
    minio_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="MinIO'daki tam dosya yolu (bucket/key)",
    )
    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now(),
        comment="Fotoğrafın çekilme/yüklenme zamanı",
    )
    quality_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Laplacian varyans skoru — <100 ise bulanık (Doküman 2.6)",
    )
    task_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True,
        comment="Celery task ID — asenkron polling için",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        comment="pending | processing | completed | failed",
    )

    # İlişkiler
    plant: Mapped[Optional["Plant"]] = relationship(back_populates="images")
    analysis: Mapped[Optional["Analysis"]] = relationship(
        back_populates="image",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Image(id={self.id}, status={self.status}, filename={self.original_filename})>"
