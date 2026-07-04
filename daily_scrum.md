# Daily Scrum Notları — Salkım Projesi

## Sprint 1 — Gün 1 (4 Temmuz 2026)

### V1 (Esma) — Görüntü İşleme Lead
**Yaptıklarım:**
- YOLOv8 domates tespit modeli eğitildi (mAP: 0.941)
- EfficientNet hastalık sınıflandırma modeli eğitildi (%99.5 accuracy)
- EfficientNet olgunluk modeli eğitildi (%97.76 accuracy)
- Roboflow'dan 542 fotoğraflık dataset indirildi
- YOLOv8 olgunluk modeli eğitildi (mAP: 0.966)
- full_analysis() pipeline'ı birleştirildi
- Tüm modeller Drive'a kaydedildi

**Bir sonraki sprintte yapacaklarım:**
- TFLite export — mobil için model küçültme
- V2 ile pipeline entegrasyon testi

**Engel var mı:**
- Yok

---

### V2 — CV & Backend Engineer
**Yaptıklarım:**
- EfficientNet eğitim altyapısı kuruldu
- Backend mimarisi hazırlandı

**Bir sonraki sprintte yapacaklarım:**
- EfficientNet fine-tune (Roboflow dataseti)
- TorchServe kurulumu
- TFLite export

**Engel var mı:**
- Yok

---------------------------------------------------------------

### T1 — ML/Tahminleme Lead
**Yaptıklarım:**
- Henüz başlanmadı

**Bir sonraki sprintte yapacaklarım:**
- OpenWeatherMap API entegrasyonu
- GDD hesaplayıcı
- XGBoost hasat tahmini modeli

**Engel var mı:**
- Yok

---

### T2 — Backend & Data Engineer
**Yaptıklarım:**
- Docker Compose kuruldu (PostgreSQL, Redis, FastAPI, Celery)
- FastAPI endpoint'leri hazırlandı (görsel yükleme + sonuç sorgulama)
- YOLOv8, olgunluk ve hastalık modelleri Docker'a entegre edildi
- E2E entegrasyon testi yapıldı — fotoğraf → Redis → Celery → JSON sonuç

**Bir sonraki sprintte yapacaklarım:**
- Kubernetes manifest'leri
- FCM push bildirim servisi

**Engel var mı:**
- Yok
