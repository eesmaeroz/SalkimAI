# SalkımAI - KVKK & GDPR Uyumluluk Kontrol Listesi

Bu doküman, SalkımAI platformunun 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) ve Avrupa Birliği Genel Veri Koruma Tüzüğü (GDPR) kapsamında alınan teknik ve idari tedbirlerini özetlemektedir. (Plan Faz 3, Gün 26)

## 1. Veri Sınıflandırması ve Anonimleştirme
SalkımAI sistemine yüklenen veriler iki temel kategoriye ayrılır:
* **Kişisel Veriler:** Kullanıcının telefon numarası, ad-soyad bilgisi, fatura bilgileri, coğrafi lokasyonu (Sera koordinatları).
* **Araştırma Verileri:** Yüklenen bitki fotoğrafları, hastalık skorları, olgunluk değerleri.

**Tedbirler:**
- Araştırma verileri (fotoğraflar), makine öğrenmesi modellerimizin (YOLO, EfficientNet, vb.) eğitilmesi amacıyla **anonimleştirilerek** (kullanıcı kimliğinden bağımsız kalarak) saklanır.
- Kullanıcıların açık rızası olmadan kişisel veriler 3. taraflarla paylaşılmaz.

## 2. Unutulma Hakkı (Right to be Forgotten)
Kullanıcıların kendi verilerini tamamen silme hakkı sistem altyapısına entegre edilmiştir.

**Teknik İmplementasyon:**
- `/api/v1/auth/me` endpoint'i kullanılarak gönderilen HTTP `DELETE` istekleri, kimliği doğrulanmış (JWT Token sahibi) kullanıcının tüm kişisel bilgilerini PostgreSQL veritabanından kalıcı olarak siler (`204 No Content`).
- Kullanıcının "owner_id / user_id" ile ilişkilendirilmiş seraları (greenhouses), ekin kayıtları (plants) ve sensor verileri (sensor_readings) **Cascading Delete (Zincirleme Silme)** kuralı gereği otomatik olarak temizlenir.
- Görüntü dosyaları (MinIO üzerindeki object'ler) anonimleştirilmiş (kimliksizleştirilmiş) olarak araştırma klasörlerinde tutulabilir, ancak kullanıcıyla olan ilişkisi kesilir.

## 3. Erişim Kısıtlaması ve Loglama (Data Access Logging)
**Veritabanı (PostgreSQL / TimescaleDB):**
- Doğrudan veritabanı erişimleri dış internete kapalıdır. Sadece Kubernetes cluster içindeki internal servisler veya VPN tüneli üzerinden güvenilir admin hesapları erişim sağlayabilir.
- Veritabanı sorguları ORM (SQLAlchemy) üzerinden parametrize edilerek yürütülür, bu da olası SQL Injection (SQLi) ataklarını engeller.

**Dosya Depolama (MinIO):**
- Object Storage üzerindeki bucket'lar (kovalar) dışarıdan direkt erişime (public read) kapalıdır.
- Kullanıcıların kendi seralarına ait görüntülere erişimi, FastAPI üzerinden yetkilendirilmiş (Auth token ile) Presigned URL'ler yardımıyla gerçekleşir.

## 4. İletişim Güvenliği
- Kullanıcı cihazı (Flutter Mobile App) ile API arasındaki tüm iletişim **TLS/SSL (HTTPS)** protokolü üzerinden şifrelenir.
- Ingress katmanında (Nginx Ingress) Let's Encrypt (cert-manager) aracılığıyla sağlanan 2048-bit şifreleme anahtarları kullanılır. Rate limiting (Örn. saniyede 10 istek) aktif edilerek olası Brute-Force ataklarına karşı önlem alınmıştır.

---
*Not: Bu kontrol listesi teknik uyumluluğu belgeler. Hukuki açıdan tam geçerlilik için şirket avukatları tarafından hazırlanmış "Aydınlatma Metni" ve "Açık Rıza Beyanı" dokümanlarının mobil uygulamaya yerleştirilmesi gereklidir.*
