"""
Salkım AI — Plant (Bitki) Modeli

Doküman 5.1: plants tablosu
Alanlar: id, greenhouse_id, row_num, planted_at
İlişkiler: greenhouse (N:1), images (1:N)
"""

import uuid
from datetime import date
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Integer, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.models.greenhouse import Greenhouse
    from apps.api.models.image import Image


class Plant(TimestampMixin, Base):
    __tablename__ = "plants"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    greenhouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("greenhouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_num: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Sera içindeki sıra numarası",
    )
    planted_at: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="Ekim tarihi",
    )

    # İlişkiler
    greenhouse: Mapped["Greenhouse"] = relationship(back_populates="plants")
    images: Mapped[List["Image"]] = relationship(
        back_populates="plant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Plant(id={self.id}, row_num={self.row_num})>"
