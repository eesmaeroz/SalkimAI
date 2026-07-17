"""
Salkım AI — SensorReading (Sensör Okuması) Modeli

Doküman 5.1 + 2.5:
  sensor_readings (time TIMESTAMPTZ, greenhouse_id FK, temp_c, humidity_pct, lux)
  TimescaleDB hypertable: partition by time (1 month chunks)

TimescaleDB Notu:
  - Bu tablo ORM ile oluşturulur (normal PostgreSQL tablosu olarak)
  - Hypertable dönüşümü startup'ta raw SQL ile yapılır:
      SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);
  - PRIMARY KEY: (time, greenhouse_id) — TimescaleDB chunk partition uyumlu
"""

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index, text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import Base


class SensorReading(Base):
    """
    Sera sensör okuması.

    TimescaleDB hypertable olarak tasarlandığından TimestampMixin kullanılmaz.
    Partition key olarak `time` alanı kullanılır.
    """

    __tablename__ = "sensor_readings"

    # TimescaleDB hypertable: PRIMARY KEY zaman sütununu içermeli
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=text("NOW()"),
        comment="Ölçüm zamanı (UTC) — TimescaleDB partition key",
    )
    greenhouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("greenhouses.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Sera FK — composite PK parçası",
    )
    temp_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Sıcaklık (Celsius)",
    )
    humidity_pct: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Nem oranı (yüzde, 0–100)",
    )
    lux: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Işık yoğunluğu (lux)",
    )

    # TimescaleDB üzerinde zaman + sera bazlı sorgular için index
    __table_args__ = (
        Index("ix_sensor_readings_greenhouse_time", "greenhouse_id", "time"),
    )

    def __repr__(self) -> str:
        return (
            f"<SensorReading(greenhouse={self.greenhouse_id}, "
            f"time={self.time}, temp={self.temp_c}°C, hum={self.humidity_pct}%)>"
        )
