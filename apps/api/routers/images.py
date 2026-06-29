"""
Salkım AI — Images (Görüntü) Router'ı

Doküman 2.4:
  POST /api/v1/images/upload       → Görüntü yükle, analiz kuyruğuna ekle
  GET  /api/v1/images/{id}/result  → Analiz sonucunu getir (DB'den — Redis değil!)

Tüm endpoint'ler JWT ile korunur: Depends(get_current_user)
"""

import os
import uuid
import tempfile
from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.database import get_db
from apps.api.models.user import User
from apps.api.models.image import Image
from apps.api.models.analysis import Analysis
from apps.api.services.auth import get_current_user
from apps.api.celery_worker import run_full_analysis_task

router = APIRouter(tags=["images"])


# --- Pydantic Şemaları ---

class UploadResponse(BaseModel):
    message: str
    image_id: str
    task_id: str
    status: str


class TomatoResult(BaseModel):
    tomato_id: int
    ripeness_class_id: int
    disease_class_id: int


class AnalysisResult(BaseModel):
    image_id: str
    status: str
    message: Optional[str] = None
    total_tomatoes: Optional[int] = None
    maturity_class: Optional[str] = None
    disease_class: Optional[str] = None
    disease_prob: Optional[float] = None
    model_version: Optional[str] = None
    minio_url: Optional[str] = None
    raw_results: Optional[list] = None


# --- Endpoint'ler ---

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Görüntü Yükle ve Analiz Başlat",
)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kullanıcıdan gelen fotoğrafı alır, DB'de kayıt oluşturur
    ve Celery worker'a analiz görevi gönderir.

    Akış:
      1. Dosyayı geçici dizine yaz
      2. DB'de images kaydı oluştur (status=pending)
      3. Celery task'ına image_id ve geçici path ver
      4. Client'a image_id döndür
    """
    print(f"\n[API] Kullanıcı {user.phone} fotoğraf yükledi: {file.filename}")

    # 1. Dosyayı geçici dizine yaz
    file_content = await file.read()
    temp_dir = tempfile.mkdtemp(prefix="salkim_")
    safe_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(temp_dir, safe_filename)

    with open(temp_path, "wb") as buffer:
        buffer.write(file_content)

    # 2. DB'de images kaydı oluştur
    image_record = Image(
        original_filename=file.filename,
        status="pending",
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)

    # 3. Celery task'ını başlat — image_id ve geçici path gönder
    task = run_full_analysis_task.delay(
        str(image_record.id),
        temp_path,
        file.filename,
    )

    # 4. Task ID'yi image kaydına yaz
    image_record.task_id = task.id
    image_record.status = "processing"
    db.commit()

    return UploadResponse(
        message="Fotoğraf alındı, analiz arka planda başlatıldı.",
        image_id=str(image_record.id),
        task_id=task.id,
        status="processing",
    )


@router.get(
    "/{image_id}/result",
    response_model=AnalysisResult,
    summary="Analiz Sonucunu Getir",
)
def get_analysis_result(
    image_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analiz sonucunu PostgreSQL'den getirir.

    ÖNCEKİ (HATALI): AsyncResult(id, app=celery_app) → Redis'ten oku (1 gün sonra kaybolur)
    YENİ (DOĞRU): DB'den oku → kalıcı, ölçeklenebilir, güvenilir
    """
    # Image kaydını bul
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Görüntü bulunamadı.",
        )

    # Durum kontrolü
    if image.status == "pending":
        return AnalysisResult(
            image_id=str(image.id),
            status="pending",
            message="Analiz henüz kuyruğa eklenmedi.",
        )

    if image.status == "processing":
        return AnalysisResult(
            image_id=str(image.id),
            status="processing",
            message="Analiz devam ediyor...",
        )

    if image.status == "failed":
        return AnalysisResult(
            image_id=str(image.id),
            status="failed",
            message="Analiz sırasında bir hata oluştu.",
        )

    # status == "completed" → Analiz sonucunu getir
    analysis = db.query(Analysis).filter(Analysis.image_id == image_id).first()
    if not analysis:
        return AnalysisResult(
            image_id=str(image.id),
            status="completed",
            message="Analiz tamamlandı ancak sonuç bulunamadı.",
        )

    return AnalysisResult(
        image_id=str(image.id),
        status="completed",
        total_tomatoes=analysis.total_tomatoes,
        maturity_class=analysis.maturity_class,
        disease_class=analysis.disease_class,
        disease_prob=analysis.disease_prob,
        model_version=analysis.model_version,
        minio_url=image.minio_url,
        raw_results=analysis.raw_results,
    )
