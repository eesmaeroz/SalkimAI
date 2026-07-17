"""
Salkım AI — Alembic Migration Ortam Konfigürasyonu

Bu dosya Alembic'in model metadata'sını bulmasını sağlar.
DATABASE_URL ortam değişkeninden okunur, yoksa alembic.ini'deki değer kullanılır.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Proje kökünü Python path'ine ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Tüm modelleri import et — metadata'nın dolu olması için zorunlu
from apps.api.models import Base

# Alembic Config nesnesi
config = context.config

# Logging konfigürasyonu
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata — autogenerate için
target_metadata = Base.metadata

# Ortam değişkeninden DB URL'i oku (varsa alembic.ini'yi override eder)
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Offline modda migration — DB bağlantısı olmadan SQL üretir."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online modda migration — DB'ye bağlanarak çalışır."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
