import os
import sys
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from apps.api.celery_worker import celery_app, run_full_analysis_task

app = FastAPI(title="Salkım AI API (Celery Destekli)", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "message": "Salkım API ve Celery bağlantısı hazır!"}


@app.post("/api/v1/images/upload")
async def upload_image(file: UploadFile = File(...)):
    print(f"\n[API] Mobil uygulamadan bir fotoğraf geldi: {file.filename}")
    

    temp_path = os.path.join(PROJECT_ROOT, f"process_{file.filename}")
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
        
    
    task = run_full_analysis_task.delay(temp_path)
    
    
    return {
        "message": "Fotoğraf alındı, analiz arka planda başlatıldı.",
        "task_id": task.id,
        "status": "PENDING"
    }


@app.get("/api/v1/images/{id}/result")
def get_analysis_result(id: str):
    
    task_result = AsyncResult(id, app=celery_app)
    
    if task_result.state == "PENDING":
        return {"task_id": id, "status": "PENDING", "message": "Analiz hala kuyrukta veya işleniyor."}
    
    elif task_result.state == "SUCCESS":
        return {
            "task_id": id,
            "status": "SUCCESS",
            "result": task_result.result 
        }
    
    elif task_result.state == "FAILURE":
        return {
            "task_id": id,
            "status": "FAILURE",
            "message": str(task_result.info) 
        }
        
    return {"task_id": id, "status": task_result.state}
