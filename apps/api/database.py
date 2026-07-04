"""
Salkım AI — Veritabanı Bağlantı Yönetimi

SQLAlchemy engine, session factory ve FastAPI dependency injection.
DATABASE_URL ortam değişkeninden okunur.
"""

import logging
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from apps.api.models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://salkim_user:salkim_password@localhost:5432/salkim_db",
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Depends ile kullanılacak DB session dependency.
    
    Kullanım:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Uygulama başlangıcında tabloları oluşturur.
    Prodüksiyonda Alembic migration tercih edilir;
    bu fonksiyon geliştirme kolaylığı içindir.
    """
    Base.metadata.create_all(bind=engine)
    _ensure_timescaledb_hypertable()


def _ensure_timescaledb_hypertable() -> None:
    """
    sensor_readings tablosunu TimescaleDB hypertable'a dönüştürür.

    - TimescaleDB eklentisi yüklü değilse sessizce geçer (geliştirme ortamı).
    - create_hypertable() idempotent: tablo zaten hypertable ise hata vermez
      (if_not_exists => TRUE).
    - Partition aralığı: 1 ay (chunk_time_interval => INTERVAL '1 month').
    """
    with engine.connect() as conn:
        # TimescaleDB eklentisi kurulu mu kontrol et
        result = conn.execute(
            text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'timescaledb'")
        )
        if result.scalar() == 0:
            logger.warning(
                "⚠️  TimescaleDB eklentisi bulunamadı — "
                "sensor_readings normal PostgreSQL tablosu olarak kalacak."
            )
            return

        # Hypertable dönüşümü (idempotent)
        conn.execute(
            text(
                """
                SELECT create_hypertable(
                    'sensor_readings',
                    'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 month'
                )
                """
            )
        )
        conn.commit()
        logger.info("✅ sensor_readings TimescaleDB hypertable olarak hazır.")

