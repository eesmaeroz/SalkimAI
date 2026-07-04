"""
Salkım AI — Özel Prometheus Metrikleri

Bu modül, uygulamanın iş mantığına özgü metrikleri tanımlar.
Örneğin model inference süreleri, tespit edilen hastalık sayıları vb.
"""

from prometheus_client import Counter, Histogram

# Celery Task Metrikleri
CELERY_TASK_DURATION = Histogram(
    "celery_task_duration_seconds",
    "Celery task çalışma süresi (saniye)",
    ["task_name"],
    buckets=[1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float("inf")]
)

CELERY_TASK_FAILURES = Counter(
    "celery_task_failures_total",
    "Celery task hata sayısı",
    ["task_name", "error_type"]
)

# İş Mantığı (Business) Metrikleri
DISEASE_RISK_DETECTIONS = Counter(
    "disease_risk_detections_total",
    "Tespit edilen hastalık riskleri (risk seviyesine göre)",
    ["risk_level", "disease_class"]
)

HARVEST_PREDICTIONS_TOTAL = Counter(
    "harvest_predictions_total",
    "Yapılan hasat tahmini sayısı"
)
