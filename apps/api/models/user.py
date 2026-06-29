"""
Salkım AI — User (Kullanıcı) Modeli

Doküman 5.1: users tablosu
Alanlar: id, phone, name, role, subscription_tier, hashed_password
İlişkiler: greenhouses (1:N)
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.models.greenhouse import Greenhouse


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True,
        comment="Birincil iletişim ve auth alanı",
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="producer",
        server_default="producer",
        comment="producer | consultant | admin",
    )
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        server_default="free",
        comment="free | standard | pro | consultant — Doküman 6.1",
    )

    # İlişkiler
    greenhouses: Mapped[List["Greenhouse"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone={self.phone}, name={self.name})>"
