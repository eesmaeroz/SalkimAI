"""
Salkım AI — Harvest (Hasat) Modeli

Doküman 5.1: harvests tablosu
Alanlar: id, greenhouse_id, harvested_at, weight_kg, quality_grade
İlişkiler: greenhouse (N:1)
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, TimestampMixin

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.api.models.greenhouse import Greenhouse


class Harvest(TimestampMixin, Base):
    __tablename__ = "harvests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    greenhouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("greenhouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    harvested_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(),
        comment="Hasat tarihi",
    )
    weight_kg: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Hasat miktarı (kg)",
    )
    quality_grade: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="Kalite notu: A/B/C veya 1-5 ölçeği",
    )

    # İlişkiler
    greenhouse: Mapped["Greenhouse"] = relationship(back_populates="harvests")

    def __repr__(self) -> str:
        return f"<Harvest(id={self.id}, kg={self.weight_kg}, grade={self.quality_grade})>"
