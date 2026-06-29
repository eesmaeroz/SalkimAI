"""
Salkım AI — FastAPI Ana Sunucu (Refactored)

Düzeltilen sorunlar:
  1. CORS: allow_origins=["*"] + allow_credentials=True birlikte kullanılamaz
  2. Auth: Endpoint'ler korumasızdı → JWT Depends eklendi (router'lara taşındı)
  3. Result: Redis AsyncResult → DB sorgusu (router'a taşındı)
  4. Upload: Diske yazma → MinIO + DB (router'a taşındı)
  5. Startup: DB tabloları ve MinIO bucket'ları oluşturuluyor
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Path ayarı ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from apps.api.database import create_tables
from apps.api.services.storage import ensure_buckets
from apps.api.routers.auth import router as auth_router
from apps.api.routers.images import router as images_router

logger = logging.getLogger(__name__)


# --- Uygulama Yaşam Döngüsü ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama başlangıcında:
      1. DB tablolarını oluştur (Alembic yoksa fallback)
      2. MinIO bucket'larını oluştur
    """
    logger.info("🚀 Salkım AI API başlatılıyor...")

    # DB tablolarını oluştur
    try:
        create_tables()
        logger.info("✅ Veritabanı tabloları hazır.")
    except Exception as e:
        logger.error(f"❌ DB tabloları oluşturulamadı: {e}")

    # MinIO bucket'larını oluştur
    try:
        ensure_buckets()
        logger.info("✅ MinIO bucket'ları hazır.")
    except Exception as e:
        logger.warning(f"⚠️ MinIO bucket'ları oluşturulamadı (MinIO henüz hazır olmayabilir): {e}")

    yield

    logger.info("🛑 Salkım AI API kapatılıyor...")


# --- FastAPI Uygulama Tanımı ---
app = FastAPI(
    title="Salkım AI API",
    description=(
        "Sera domatesi analiz platformu — Görüntü işleme, hastalık tespiti "
        "ve hasat tahmini API'si. JWT ile korunur."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# --- CORS Ayarları ---
# ÖNCEKİ (HATALI):
#   allow_origins=["*"], allow_credentials=True
#   → Modern tarayıcılar bu kombinasyonu reddeder!
#
# YENİ (DOĞRU):
#   Geliştirme ortamı: Belirli origin'ler + credentials=True
#   Veya: Herkese açık (credentials=False)

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8080,http://localhost:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Router'ları Bağla ---
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(images_router, prefix="/api/v1/images")


# --- Health Check (Korumasız — Monitoring için) ---
@app.get("/api/v1/health", tags=["health"])
def health_check():
    """
    Sistem sağlık kontrolü.
    Auth gerektirmez — Prometheus/Grafana monitoring için açık.
    """
    return {
        "status": "healthy",
        "message": "Salkım AI API çalışıyor.",
        "version": "1.0.0",
    }
