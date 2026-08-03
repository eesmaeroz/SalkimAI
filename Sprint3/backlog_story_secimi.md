# Backlog Düzeni ve Story Seçimi — Sprint 3

## Ürün Backlog'u (Tüm Görevler)

| # | Görev                               | Öncelik | Sprint |
|---|-------------------------------------|---------|--------|
| 1 | YOLOv8 domates tespit modeli eğitimi | Yüksek | Sprint 1 ✅ |
| 2 | EfficientNet hastalık sınıflandırma modeli | Yüksek | Sprint 1 ✅ |
| 3 | EfficientNet olgunluk modeli eğitimi | Yüksek | Sprint 1 ✅ |
| 4 | YOLOv8 olgunluk tespiti (Roboflow) | Yüksek | Sprint 1 ✅ |
| 5 | Görüntü işleme pipeline birleştirilmesi | Yüksek | Sprint 1 ✅ |
| 6 | FastAPI endpoint kurulumu | Yüksek | Sprint 1 ✅ |
| 7 | Docker + Kubernetes altyapısı | Yüksek | Sprint 1 ✅ |
| 8 | MLflow + feature engineering | Orta | Sprint 1 ✅ |
| 9 | TFLite export — mobil model | Orta | Sprint 2 |
| 10 | EfficientNet fine-tune (Roboflow) | Orta | Sprint 2 |
| 11 | OpenWeatherMap gerçek entegrasyonu | Orta | Sprint 2 |
| 12 | XGBoost hasat tahmini modeli eğitimi | Orta | Sprint 2 |
| 13 | FCM push bildirim servisi | Düşük | Sprint 2 |
| 14 | Flutter mobil uygulama | Yüksek | Sprint 2 |
| 15 | TimescaleDB sensör pipeline'ı | Düşük | Sprint 3 |
| 16 | Railway'e production deployment (PostgreSQL, Redis, Celery, MinIO) | Yüksek | Sprint 3 ✅ |
| 17 | bcrypt / Celery worker konfigürasyon sorunlarının çözümü | Yüksek | Sprint 3 ✅ |
| 18 | FastAPI ↔ Celery worker arası MinIO tabanlı dosya paylaşımı mimarisi | Yüksek | Sprint 3 ✅ |
| 19 | Görüntü analiz pipeline'ının uçtan uca canlı ortamda test edilmesi | Yüksek | Sprint 3 ✅ |
| 20 | Flutter uygulamasının canlı API'ye bağlanması | Yüksek | Sprint 3 ✅ |
| 21 | Hasat tahmini (Tahminlemeler) ekranının Flutter tarafında UI entegrasyonu | Yüksek | Sprint 3 ✅ |
| 22 | Olgunluk (ripeness) modelinin güncellenmiş versiyonla değiştirilmesi | Yüksek | Sprint 3 ✅ |
| 23 | Güncellenen olgunluk modelinin doğruluk testi | Orta | Sprint 3 |
| 24 | Hastalık modeli doğruluğunun iyileştirilmesi | Orta | Sprint 3 |
| 25 | Kullanıcı girişi (login) ekranı — gerçek kullanıcı auth akışı | Orta | Sprint 3 |
| 26 | Geçmiş İşlemler ekranının backend'e bağlanması | Orta | Sprint 3 |
| 27 | Model performans/hız iyileştirmeleri | Düşük | Sprint 3 |
| 28 | Ekip üyelerine Railway erişim yetkilendirmesi | Düşük | Sprint 3 |

---

## Sprint 3 Story Seçimi

Sprint 3 için **backend'in production ortamına taşınması ve uçtan uca canlı entegrasyonun tamamlanması** hedeflendi. Seçim kriterleri:

- Sprint 1-2'de geliştirilen backend ve mobil uygulamanın artık gerçek bir sunucuda, kalıcı ve erişilebilir şekilde çalışması önceliklendirildi
- Yerel ortamda (ngrok vb.) çalışan geçici kurulum yerine, kalıcı bir cloud altyapısı (Railway: PostgreSQL, Redis, Celery worker, MinIO) kuruldu
- Deployment sürecinde ortaya çıkan mimari sorunlar (ayrı konteynerler arası dosya paylaşımı, worker konfigürasyonu) çözülerek sistem stabil hale getirildi
- Flutter uygulaması mock veriden çıkarılıp gerçek API'ye bağlandı, gerçek fotoğraflarla uçtan uca test edildi
- Model iyileştirme ve kullanıcı deneyimi (login, geçmiş işlemler) çalışmaları bir sonraki spring'e/devam eden işe bırakıldı

### Sprint 3'te Seçilen ve Tamamlanan Storyler
- Railway'e production deployment (PostgreSQL, Redis, Celery worker, MinIO)
- bcrypt / Celery worker konfigürasyon sorunlarının çözümü
- FastAPI ↔ Celery worker arası MinIO tabanlı dosya paylaşımı mimarisi
- Görüntü analiz pipeline'ının uçtan uca canlı ortamda test edilmesi
- Flutter uygulamasının canlı API'ye bağlanması
- Hasat tahmini (Tahminlemeler) ekranının Flutter tarafında UI entegrasyonu
- Olgunluk (ripeness) modelinin güncellenmiş versiyonla değiştirilmesi

### Devam Eden / Sprint 4'e Bırakılan Storyler
- Güncellenen olgunluk modelinin kapsamlı doğruluk testi
- Hastalık modeli doğruluğunun iyileştirilmesi
- Kullanıcı girişi (login) ekranı — gerçek kullanıcı auth akışı
- Geçmiş İşlemler ekranının backend'e bağlanması
- Model performans/hız iyileştirmeleri
- Ekip üyelerine Railway erişim yetkilendirmesi
