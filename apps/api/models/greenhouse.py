"""
Salkım AI — Greenhouse (Sera) Modeli

Doküman 5.1: greenhouses tablosu
Alanlar: id, user_id, name, area_m2, variety, location_lat, location_lng
İlişkiler: user (N:1), plants (1:N), harvests (1:N)
"""

import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.models.user import User
    from apps.api.models.plant import Plant
    from apps.api.models.harvest import Harvest


class Greenhouse(TimestampMixin, Base):
    __tablename__ = "greenhouses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    area_m2: Mapped[float] = mapped_column(
        Float, nullable=True,
        comment="Sera alanı (metrekare)",
    )
    variety: Mapped[str] = mapped_column(
        String(100), nullable=True,
        comment="Domates çeşidi",
    )
    location_lat: Mapped[float] = mapped_column(
        Float, nullable=True,
    )
    location_lng: Mapped[float] = mapped_column(
        Float, nullable=True,
    )

    # İlişkiler
    user: Mapped["User"] = relationship(back_populates="greenhouses")
    plants: Mapped[List["Plant"]] = relationship(
        back_populates="greenhouse",
        cascade="all, delete-orphan",
    )
    harvests: Mapped[List["Harvest"]] = relationship(
        back_populates="greenhouse",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Greenhouse(id={self.id}, name={self.name})>"
