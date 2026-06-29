import os
import sys
from celery import Celery


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from ml.vision.inference import full_analysis


REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")


celery_app = Celery(
    "salkim_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True
)


@celery_app.task(name="tasks.run_full_analysis")
def run_full_analysis_task(image_path):
    print(f"[CELERY] Arka planda analiz görevi başladı: {image_path}")
    
   
    result = full_analysis(image_path)
    
    
    if os.path.exists(image_path):
        os.remove(image_path)
        
    print(f"[CELERY] Arka plan görevi başarıyla tamamlandı!")
    return result