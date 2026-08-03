Sprint 3 Retrospective — Salkım Projesi

Tarih: 1 Ağustos 2026 Katılımcılar: V1 (Esma), V2 (Dilan), T1 (Arif), T2 (Eren)

İyi Gidenler 👍
Backend başarıyla Railway'e production ortamına taşındı (PostgreSQL, Redis, Celery worker, MinIO)
Flutter uygulaması artık mock veri değil, gerçek canlı API ile çalışıyor
Görüntü analiz pipeline'ı (upload → YOLO → EfficientNet → sonuç) uçtan uca canlı ortamda test edildi ve doğrulandı
Olgunluk modelindeki bilinen bir doğruluk sorunu (yeşil domateslere "red" tahmini) tespit edilip düzeltilmiş modelle production'da güncellendi
Hasat tahmini (Tahminlemeler) ekranı UI tarafında tamamlandı
Ekip, deployment sürecinde ortaya çıkan zincirleme altyapı sorunlarını (DB, auth, worker, dosya depolama) sistematik şekilde çözdü
Proje, kurulumdan production'a uzanan tam bir döngüyü başarıyla tamamlayarak teslime hazır hale geldi
Geliştirilmesi Gerekenler 👎
Deployment süreci beklenenden çok daha uzun sürdü (yaklaşık 4 saat); her çözülen sorun bir sonrakini ortaya çıkardı
FastAPI ile Celery worker'ın ayrı konteynerler olduğu ve dosya paylaşamadığı geç fark edildi — bu, mimari planlamanın deployment öncesi daha net yapılması gerektiğini gösterdi
Model dosyaları GitHub üzerinden yönetilirken (web arayüzünden yeniden adlandırma sırasında) bir dosya bozulması yaşandı; büyük binary dosyalarla git-lfs kullanılmadığı için riskli
Hastalık sınıflandırma modelinin doğruluğu proje teslimine kadar tam olarak iyileştirilemedi
Kullanıcı girişi (login) ekranı gerçek bir auth akışına sahip değil, test kullanıcısı sabit kodlanmış durumda kaldı
Ekipten sadece bir kişinin Railway'e erişimi vardı; bir sorun çıktığında tek nokta bağımlılığı riski oluştu
Aksiyon Maddeleri 🎯

(Bu proje kapsamındaki son sprint olduğundan, aşağıdaki maddeler projenin teslim sonrası olası devamı için not edilmiştir.)

Büyük model dosyaları için Git LFS kullanımına geçilmesi önerilir
Hastalık modeli doğruluğunun artırılması önerilir
Flutter'a gerçek kullanıcı girişi (login) ekranı eklenmesi önerilir
Geçmiş İşlemler ekranının backend'e bağlanması önerilir
Ekip üyelerine Railway erişim yetkisi verilerek tek nokta bağımlılığının azaltılması önerilir
Genel Değerlendirme

Sprint 3, projenin son ve en kritik dönüm noktası oldu: sistem artık gerçek kullanıcılar tarafından erişilebilir, uçtan uca çalışan bir production ortamında teslim edilmeye hazır. 
Deployment süreci zorlu geçti ama bu süreçte edinilen deneyim (konteyner mimarisi, servisler arası iletişim, dosya paylaşımı) ekibin altyapı bilgisini önemli ölçüde artırdı. 
Projenin bu haliyle temel hedefleri (görüntüden domates tespiti, olgunluk/hastalık sınıflandırması, hasat tahmini ve mobil erişim) başarıyla karşılanmıştır.
