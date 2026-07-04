# Sprint 1 Review — Salkım Projesi

**Tarih:** 4 Temmuz 2026  
**Sprint Süresi:** 1 Hafta  
**Katılımcılar:** V1 (Esma), V2 (Dilan), T1 (Arif), T2 (Eren)

---

## Tamamlanan İşler

### Görüntü İşleme (Esma - V1)
- YOLOv8 domates tespit modeli eğitildi — mAP@0.5: 0.941
- EfficientNet-B4 hastalık sınıflandırma modeli — %99.5 accuracy
- EfficientNet-B4 olgunluk modeli — %97.76 accuracy
- YOLOv8 olgunluk tespiti modeli (Roboflow) — mAP@0.5: 0.966
- full_analysis() pipeline'ı — 3 model tek fonksiyonda birleştirildi
- Tüm modeller Google Drive'a kaydedildi

### Backend (Eren - T2)
- Docker Compose kuruldu (PostgreSQL, Redis, FastAPI, Celery)
- FastAPI endpoint'leri hazırlandı
- 3 model Docker'a entegre edildi
- E2E entegrasyon testi tamamlandı

### CV & Backend (Dilan - V2)
- EfficientNet eğitim altyapısı kuruldu
- Backend mimarisi hazırlandı

---

## Tamamlanamayan İşler
- T1 (Arif): Tahminleme modeli — Sprint 2'ye taşındı
- TFLite export — Sprint 2'ye taşındı
- FCM push bildirim — Sprint 2'ye taşındı

---

## Sprint Hedefi Değerlendirmesi
Görüntü işleme pipeline'ı ve backend altyapısı başarıyla tamamlandı. Model doğrulukları hedef değerlerin üzerinde çıktı.
