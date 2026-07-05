# Daily Scrum Notları — Salkım Projesi

-----------------------------

## Gün 1 — 27 Haziran 2026

### Esma (V1)
**Yaptıklarım:** Google Colab kurulumu, Kaggle API bağlantısı, domates dataseti araştırması
**Engel:** Kaggle GPU kotası doluydu, Colab'a geçildi

### Dilan (V2)
**Yaptıklarım:** EfficientNet mimarisi araştırması, backend mimarisi planlandı

### Arif (T1)
**Yaptıklarım:** MLflow kurulumu, proje klasör yapısı oluşturuldu

### Eren (T2)
**Yaptıklarım:** Docker Compose dosyası oluşturuldu, PostgreSQL ve Redis ayağa kaldırıldı

---

## Gün 2 — 28 Haziran 2026

### Esma (V1)
**Yaptıklarım:** 895 fotoğraflık domates dataseti indirildi, XML annotation'lar YOLO formatına çevrildi, train/val split yapıldı

### Dilan (V2)
**Yaptıklarım:** EfficientNet-B4 eğitim altyapısı kuruldu, PlantVillage dataseti araştırıldı

### Arif (T1)
**Yaptıklarım:** DVC kurulumu, feature engineering modülü yazılmaya başlandı

### Eren (T2)
**Yaptıklarım:** FastAPI iskelet kuruldu, temel endpoint'ler yazıldı

---

## Gün 3 — 29 Haziran 2026

### Esma (V1)
**Yaptıklarım:** YOLOv8n baseline eğitimi başlatıldı, 30 epoch tamamlandı, mAP@0.5: 0.941 elde edildi

### Dilan (V2)
**Yaptıklarım:** PlantVillage dataseti indirildi, 5 sınıf belirlendi (healthy, early_blight, late_blight, mite_damage, mosaic_virus)

### Arif (T1)
**Yaptıklarım:** GDD hesaplayıcı tamamlandı, hava API mock'u yazıldı

### Eren (T2)
**Yaptıklarım:** Celery + Redis entegrasyonu tamamlandı, async task şablonu oluşturuldu

---

## Gün 4 — 30 Haziran 2026

### Esma (V1)
**Yaptıklarım:** YOLOv8 modeli test edildi, 9 domates tespiti başarıyla gerçekleşti, model Drive'a kaydedildi

### Dilan (V2)
**Yaptıklarım:** EfficientNet-B4 transfer learning başlatıldı, 5237 fotoğraf ile eğitim yapıldı, %99.5 accuracy elde edildi

### Arif (T1)
**Yaptıklarım:** XGBoost model prototipi oluşturuldu, LSTM mimarisi planlandı

### Eren (T2)
**Yaptıklarım:** 3 model Docker katmanına entegre edildi, E2E entegrasyon testi yapıldı

---

## Gün 5 — 1 Temmuz 2026

### Esma (V1)
**Yaptıklarım:** Olgunluk modeli için dataset arandı, fruits ripeness dataseti indirildi (ripe/unripe/overripe)

### Dilan (V2)
**Yaptıklarım:** Hastalık modeli Drive'a kaydedildi, backend mimarisi güncellendi

### Arif (T1)
**Yaptıklarım:** LSTM zaman serisi modeli yazıldı, validation loss yakınsadı

### Eren (T2)
**Yaptıklarım:** Kubernetes API deployment tamamlandı, Redis deployment hazırlandı

---

## Gün 6 — 2 Temmuz 2026

### Esma (V1)
**Yaptıklarım:** EfficientNet olgunluk modeli eğitildi (%97.76 accuracy), model Drive'a kaydedildi

### Dilan (V2)
**Yaptıklarım:** TorchServe araştırması yapıldı, model handler yazımına başlandı

### Arif (T1)
**Yaptıklarım:** XGBoost + LSTM ensemble planlandı, feature pipeline tamamlandı

### Eren (T2)
**Yaptıklarım:** Celery worker deployment, secrets.yaml oluşturuldu

---

## Gün 7 — 3 Temmuz 2026

### Esma (V1)
**Yaptıklarım:** Roboflow'dan 542 fotoğraflık domates ripeness dataseti indirildi, YOLOv8 olgunluk modeli eğitildi (mAP: 0.966)

### Dilan (V2)
**Yaptıklarım:** EfficientNet fine-tune altyapısı hazırlandı, Roboflow dataseti fork'landı

### Arif (T1)
**Yaptıklarım:** Tüm Faz 1 görevleri tamamlandı, model prototipi çalışır durumda

### Eren (T2)
**Yaptıklarım:** Docker Compose güncellendi, tüm servisler test edildi

---

## Gün 8 — 4 Temmuz 2026

### Esma (V1)
**Yaptıklarım:** full_analysis() pipeline'ı birleştirildi, 3 model tek fonksiyonda çalışır hale getirildi, sprint board ve belgeler hazırlandı

### Dilan (V2)
**Yaptıklarım:** Backend mimarisi sprint 1 için tamamlandı

### Arif (T1)
**Yaptıklarım:** Sprint 1 Faz 1 görevleri tamamlandı

### Eren (T2)
**Yaptıklarım:** Tüm Kubernetes manifest'leri hazırlandı, sprint 1 backend altyapısı tamamlandı
