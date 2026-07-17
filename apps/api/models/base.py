"""
Salkım AI — SQLAlchemy ORM Base ve Ortak Mixin'ler

Tüm modellerin miras aldığı DeclarativeBase ve
created_at/updated_at otomatik timestamp mixin'i.
"""

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Tüm ORM modellerinin temel sınıfı."""
    pass


class TimestampMixin:
    """created_at ve updated_at alanlarını otomatik ekleyen mixin."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
