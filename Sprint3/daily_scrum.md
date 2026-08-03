# Daily Scrum Notları — Salkım Projesi Sprint 3

---

## Gün 1 — 30 Temmuz 2026

### Esma (V1)
**Yaptıklarım:** Backend'in Railway'e production deployment süreci başlatıldı — PostgreSQL, Redis ve MinIO servisleri kuruldu, FastAPI servisine bağlandı
**Engel:** bcrypt/passlib sürüm uyumsuzluğu ve Celery worker'ın ayrı servis olarak deploy edilmemesi nedeniyle kullanıcı kaydı ve görüntü analizi başlarda başarısız oldu; sırayla çözüldü

### Dilan (V2)
**Yaptıklarım:** Mevcut olgunluk (ripeness) modelinin yeşil domateslerde yanlış sınıflandırma yaptığı fark edildi (özellikle iri, "beefsteak" tipi domateslerde "red" tahmini veriyordu). Bu hatayı düzeltmek için eğitim verisi gözden geçirildi, ek yeşil/dönüşen domates örnekleri veri setine eklendi, model mimarisi (EfficientNet-B4, 3 sınıf: green/turning/red) yeniden eğitime alındı
**Engel:** Yok

### Arif (T1)
**Yaptıklarım:** Flutter tarafında hasat tahmini (Tahminlemeler) ekranı için UI tasarımı yapıldı — "Hasat Tahmini" ve "Hastalık Riski" olmak üzere iki sekmeli yapı kuruldu. Sera ortam verisi giriş formu (ortalama/min/max sıcaklık, nem, CO2, ışık şiddeti, fotoperiyot, sulama) geliştirildi
**Engel:** Backend'in henüz canlı olmaması nedeniyle ekran mock veriyle test edildi

### Eren (T2)
**Yaptıklarım:** Geçmiş İşlemler ekranı için liste görünümü ve navigasyon akışı tasarlandı; ana ekrana "Tahminlemeler" ve "Geçmiş İşlemler" butonları eklendi
**Engel:** Yok

---

## Gün 2 — 31 Temmuz 2026

### Esma (V1)
**Yaptıklarım:** FastAPI ve Celery worker'ın Railway'de ayrı konteynerler olarak çalıştığı tespit edildi; dosya paylaşımı MinIO üzerinden yeniden kurgulandı (`images.py`, `storage.py`, `celery_worker.py` güncellendi). Görüntü analiz pipeline'ı (upload → YOLO → EfficientNet → sonuç) uçtan uca canlı ortamda başarıyla test edildi
**Engel:** Worker'ın yüksek concurrency ile bellek taşırıp sürekli çökmesi; `--pool=solo` ile çözüldü

### Dilan (V2)
**Yaptıklarım:** Güncellenmiş olgunluk modelinin eğitimi tamamlandı (`salkim_efficientnet_mega.pth`), yerel testlerde önceki modele göre yeşil/dönüşen domateslerde belirgin doğruluk artışı gözlendi. Model dosyası teslim için hazırlandı
**Engel:** Yok

### Arif (T1)
**Yaptıklarım:** Tahminlemeler ekranındaki hasat tahmini formu tamamlandı; "Hasat Tahmini İste" butonuna basıldığında sonuç kartı (tahmini hasat tarihi, kalan gün, beklenen verim kg/m², model güven skoru) gösterilecek şekilde UI kuruldu
**Engel:** Yok

### Eren (T2)
**Yaptıklarım:** Ana ekran ve analiz sonucu ekranları arasındaki geçişler test edildi, buton hizalama ve renk tutarlılığı gibi küçük UI düzeltmeleri yapıldı
**Engel:** Yok

---

## Gün 3 — 1 Ağustos 2026

### Esma (V1)
**Yaptıklarım:** Flutter uygulaması mock veriden çıkarılıp canlı Railway API'sine bağlandı; auth, upload ve sonuç polling akışı `result_screen.dart` içine entegre edildi. Emülatör ve Chrome üzerinde gerçek fotoğraflarla uçtan uca test edildi. Dilan'ın yeni olgunluk modeli `salkım_ripeness.pth` olarak production'a alındı
**Engel:** Yerel geliştirme ortamında disk alanı ve CORS ile ilgili küçük engeller yaşandı, çözüldü

### Dilan (V2)
**Yaptıklarım:** Yeni olgunluk modelinin production ortamında gerçek fotoğraflarla doğrulama testleri yapıldı; sonuçlar yerel test sonuçlarıyla tutarlı çıktı. Hastalık sınıflandırma modelinin doğruluğunu artırmak için bir sonraki iyileştirme planı üzerinde çalışmaya başlandı
**Engel:** Yok

### Arif (T1)
**Yaptıklarım:** Tahminlemeler ekranı canlı API ile entegrasyon için hazır hale getirildi; sensör/hasat tahmin endpoint'lerine bağlanacak servis katmanı taslağı hazırlandı
**Engel:** Backend tarafında tahmin endpoint'lerinin (`/predictions/harvest`, `/predictions/disease-risk`) canlı ortamda testi bekleniyor

### Eren (T2)
**Yaptıklarım:** Sprint 3 board'u (GitHub Projects) güncellendi, tamamlanan işler "Done" sütununa taşındı; Sprint 3 dokümantasyonu (backlog, daily scrum) için ekip notları derlendi
**Engel:** Yok
