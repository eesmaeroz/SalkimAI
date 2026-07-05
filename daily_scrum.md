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
- Tüm modeller Google Drive'a kaydedildi

**Bir sonraki sprintte yapacaklarım:**
- TFLite export — mobil için model küçültme
- V2 ile pipeline entegrasyon testi

**Engel var mı:**
- Yok

---

### V2 (Dilan) — CV & Backend Engineer
**Yaptıklarım:**
- EfficientNet eğitim altyapısı kuruldu
- Backend mimarisi hazırlandı

**Bir sonraki sprintte yapacaklarım:**
- EfficientNet fine-tune (Roboflow dataseti)
- TorchServe kurulumu
- TFLite export

**Engel var mı:**
- Yok

---

### T1 (Arif) — ML/Tahminleme Lead
**Yaptıklarım:**
- MLflow + DVC kurulumu tamamlandı
- Feature engineering modülü yazıldı
- GDD hesaplayıcı tamamlandı
- Hava API mock'u hazırlandı
- XGBoost/LSTM model prototipi oluşturuldu

**Bir sonraki sprintte yapacaklarım:**
- OpenWeatherMap API gerçek entegrasyonu
- XGBoost hasat tahmini modeli eğitimi

**Engel var mı:**
- Yok

---

### T2 (Eren) — Backend & Data Engineer
**Yaptıklarım:**
- Docker Compose kuruldu (PostgreSQL, Redis, FastAPI, Celery)
- FastAPI endpoint'leri hazırlandı
- 3 model Docker'a entegre edildi
- E2E entegrasyon testi tamamlandı
- Kubernetes API deployment tamamlandı
- Redis deployment tamamlandı
- Celery worker entegrasyonu sağlandı
- Secrets.yaml oluşturuldu

**Bir sonraki sprintte yapacaklarım:**
- FCM push bildirim servisi
- TimescaleDB sensör pipeline'ı

**Engel var mı:**
- Yok
