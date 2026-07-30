"""
Salkım AI — Celery Worker (Refactored)

ÖNCEKİ AKIŞ (Hatalı):
  1. full_analysis(image_path) çağır
  2. Sonucu return et → Redis'e gider, 1 gün sonra kaybolur
  3. Dosyayı sil → DB'ye hiçbir şey yazılmıyor!

YENİ AKIŞ (Doğru):
  1. FastAPI dosyayı zaten MinIO "raw-images" bucket'ına yüklemiş durumda
  2. Worker dosyayı MinIO'dan indirir (ayrı konteyner olduğu için)
  3. full_analysis(image_path) çağır
  4. Sonucu PostgreSQL analyses tablosuna yaz
  5. images tablosundaki kaydı güncelle (minio_url, status=completed)
  6. Geçici dosyayı sil
  7. Sonucu return et
"""

import os
import sys
import logging
import time
from datetime import datetime, timezone

from celery import Celery
from sqlalchemy.orm import Session

# --- Path ayarı ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from ml.vision.inference import full_analysis
from apps.api.database import SessionLocal
from apps.api.models.image import Image
from apps.api.models.analysis import Analysis
from apps.api.services.storage import (
    upload_file,
    download_file,
    ensure_buckets,
    BUCKET_RAW_IMAGES,
)
from apps.api.services.metrics import (
    CELERY_TASK_DURATION,
    CELERY_TASK_FAILURES,
    DISEASE_RISK_DETECTIONS,
)

logger = logging.getLogger(__name__)

# --- Celery Konfigürasyonu ---
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "salkim_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,  # Redis result 1 gün (artık sadece yedek, asıl veri DB'de)
    worker_hijack_root_logger=False,
)

@celery_app.task(name="tasks.run_full_analysis", bind=True, max_retries=2)
def run_full_analysis_task(self, image_id: str, image_path: str, original_filename: str):
    """
    Görüntü analiz pipeline'ı — MinIO + ML Inference + DB Persistence

    Args:
        image_id: PostgreSQL images tablosundaki UUID (string)
        image_path: MinIO object adı (FastAPI zaten yükledi)
        original_filename: Orijinal dosya adı
    """
    db: Session = SessionLocal()
    start_time = time.time()
    local_image_path = None

    try:
        # 0. MinIO bucket'larını garanti et
        ensure_buckets()

        # 1. Fotoğrafı MinIO'dan indir (FastAPI zaten yükledi, image_path artık MinIO object adı)
        minio_object_name = image_path
        local_temp_dir = f"/tmp/salkim_worker_{image_id}"
        os.makedirs(local_temp_dir, exist_ok=True)
        local_image_path = os.path.join(local_temp_dir, original_filename)
        download_file(
            bucket=BUCKET_RAW_IMAGES,
            object_name=minio_object_name,
            file_path=local_image_path,
        )
        minio_url = f"{BUCKET_RAW_IMAGES}/{minio_object_name}"
        image_path = local_image_path
        logger.info(f"[CELERY] MinIO'dan indirildi: {minio_url}")

        # 2. ML inference çalıştır
        logger.info(f"[CELERY] ML analizi başlatılıyor: {image_path}")
        result = full_analysis(image_path)
        logger.info(f"[CELERY] ML analizi tamamlandı: {result['total_tomatoes']} domates tespit edildi")

        # 3. Analiz sonucunu DB'ye yaz
        analysis_record = Analysis(
            image_id=image_id,
            total_tomatoes=result.get("total_tomatoes", 0),
            raw_results=result.get("results", []),
            model_version="v1.0.0-efficientnet-b4",
            processed_at=datetime.now(timezone.utc),
        )

        # Eğer domates tespit edildiyse baskın sınıfları hesapla
        tomatoes = result.get("results", [])
        if tomatoes:
            # Baskın olgunluk sınıfı (en sık görülen)
            ripeness_classes = [t.get("ripeness_class_id", 0) for t in tomatoes]
            dominant_ripeness = max(set(ripeness_classes), key=ripeness_classes.count)
            ripeness_map = {0: "green", 1: "turning", 2: "red"}
            analysis_record.maturity_class = ripeness_map.get(dominant_ripeness, f"class_{dominant_ripeness}")
            analysis_record.maturity_score = ripeness_classes.count(dominant_ripeness) / len(ripeness_classes)

            # Baskın hastalık sınıfı
            disease_classes = [t.get("disease_class_id", 0) for t in tomatoes]
            dominant_disease = max(set(disease_classes), key=disease_classes.count)
            disease_map = {0: "healthy", 1: "early_blight", 2: "late_blight", 3: "pest", 4: "mosaic"}
            analysis_record.disease_class = disease_map.get(dominant_disease, f"class_{dominant_disease}")
            analysis_record.disease_prob = disease_classes.count(dominant_disease) / len(disease_classes)

            # Prometheus metrik güncelle
            risk_level = "low"
            if analysis_record.disease_prob > 0.70:
                risk_level = "high"
            elif analysis_record.disease_prob > 0.40:
                risk_level = "medium"
            DISEASE_RISK_DETECTIONS.labels(risk_level=risk_level, disease_class=analysis_record.disease_class).inc()

        db.add(analysis_record)

        # 4. Image kaydını güncelle
        image_record = db.query(Image).filter(Image.id == image_id).first()
        if image_record:
            image_record.minio_url = minio_url
            image_record.status = "completed"

        db.commit()
        logger.info(f"[CELERY] DB'ye yazıldı: analysis_id={analysis_record.id}")

        # 5. Geçici dosyayı sil
        if os.path.exists(image_path):
            os.remove(image_path)
            temp_dir = os.path.dirname(image_path)
            if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)

        logger.info(f"[CELERY] Görev başarıyla tamamlandı: image_id={image_id}")
        return {
            "image_id": image_id,
            "status": "completed",
            "total_tomatoes": result.get("total_tomatoes", 0),
        }

    except Exception as exc:
        logger.error(f"[CELERY] Görev hatası: {exc}", exc_info=True)
        CELERY_TASK_FAILURES.labels(task_name="run_full_analysis", error_type=type(exc).__name__).inc()

        # Hata durumunda image status'u güncelle
        try:
            image_record = db.query(Image).filter(Image.id == image_id).first()
            if image_record:
                image_record.status = "failed"
            db.commit()
        except Exception:
            db.rollback()

        # Geçici dosyayı temizle
        if local_image_path and os.path.exists(local_image_path):
            os.remove(local_image_path)

        raise self.retry(exc=exc, countdown=30)

    finally:
        db.close()
        duration = time.time() - start_time
        CELERY_TASK_DURATION.labels(task_name="run_full_analysis").observe(duration)
