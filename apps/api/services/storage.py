"""
Salkım AI — MinIO (S3-Uyumlu) Nesne Depolama Servisi

Doküman 3.1, 5.2: Ham görüntüler ve işlenmiş çıktılar MinIO/S3 üzerinde saklanacak.

Bucket'lar:
  - raw-images    : Kullanıcıdan gelen orijinal fotoğraflar
  - processed     : İşlenmiş çıktılar (kırpılan domates görselleri vb.)
"""

import os
import io
import logging
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

# --- Konfigürasyon ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "salkim_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "salkim_password_minio")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Bucket isimleri
BUCKET_RAW_IMAGES = "raw-images"
BUCKET_PROCESSED = "processed"

_client: Minio | None = None


def get_minio_client() -> Minio:
    """MinIO istemcisini döndürür (lazy singleton)."""
    global _client
    if _client is None:
        _client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
    return _client


def ensure_buckets() -> None:
    """
    Gerekli bucket'ların var olduğunu garanti eder.
    Uygulama başlangıcında ve Celery worker başlangıcında çağrılır.
    """
    client = get_minio_client()
    for bucket_name in [BUCKET_RAW_IMAGES, BUCKET_PROCESSED]:
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                logger.info(f"MinIO bucket oluşturuldu: {bucket_name}")
            else:
                logger.info(f"MinIO bucket zaten mevcut: {bucket_name}")
        except S3Error as e:
            logger.error(f"MinIO bucket hatası ({bucket_name}): {e}")
            raise


def upload_image(
    bucket: str,
    object_name: str,
    data: bytes,
    content_type: str = "image/jpeg",
) -> str:
    """
    Görüntüyü MinIO'ya yükler.

    Args:
        bucket: Hedef bucket adı (BUCKET_RAW_IMAGES veya BUCKET_PROCESSED)
        object_name: MinIO'daki dosya adı (ör: "user123/img_20240101.jpg")
        data: Dosya içeriği (bytes)
        content_type: MIME tipi

    Returns:
        MinIO içindeki tam yol: "bucket/object_name"
    """
    client = get_minio_client()
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    logger.info(f"MinIO'ya yüklendi: {bucket}/{object_name} ({len(data)} bytes)")
    return f"{bucket}/{object_name}"


def upload_file(
    bucket: str,
    object_name: str,
    file_path: str,
    content_type: str = "image/jpeg",
) -> str:
    """
    Yerel dosyayı MinIO'ya yükler.

    Args:
        bucket: Hedef bucket adı
        object_name: MinIO'daki dosya adı
        file_path: Yerel dosya yolu
        content_type: MIME tipi

    Returns:
        MinIO içindeki tam yol: "bucket/object_name"
    """
    client = get_minio_client()
    client.fput_object(
        bucket_name=bucket,
        object_name=object_name,
        file_path=file_path,
        content_type=content_type,
    )
    file_size = os.path.getsize(file_path)
    logger.info(f"MinIO'ya yüklendi: {bucket}/{object_name} ({file_size} bytes)")
    return f"{bucket}/{object_name}"


def get_presigned_url(
    bucket: str,
    object_name: str,
    expires: timedelta = timedelta(hours=1),
) -> str:
    """
    Geçici erişim URL'i üretir (varsayılan 1 saat).
    Mobil uygulama bu URL ile fotoğrafı doğrudan indirebilir.
    """
    client = get_minio_client()
    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=expires,
    )
    return url


def delete_object(bucket: str, object_name: str) -> None:
    """MinIO'dan nesne siler."""
    client = get_minio_client()
    client.remove_object(bucket_name=bucket, object_name=object_name)
    logger.info(f"MinIO'dan silindi: {bucket}/{object_name}")
