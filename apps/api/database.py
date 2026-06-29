"""
Salkım AI — Veritabanı Bağlantı Yönetimi

SQLAlchemy engine, session factory ve FastAPI dependency injection.
DATABASE_URL ortam değişkeninden okunur.
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from apps.api.models import Base

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
