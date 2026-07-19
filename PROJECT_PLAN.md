# Salkım AI Genel Plan

## Tamamlanan temel hat

- Temiz klasör mimarisi kuruldu.
- DVC pipeline eklendi: örnek veri üretimi, feature engineering, eğitim.
- MLflow deney kaydı eklendi.
- GDD hesaplayıcı ve deterministik hava mock'u eklendi.
- Open-Meteo canlı istemcisi eklendi.

## Yeni hedef 1: OpenWeatherMap gerçek entegrasyonu

Benim eklediğim parça:

- `ml/prediction/features/openweathermap_client.py`
- `config/params.yaml` içinde `openweathermap` ayarları
- API key güvenliği için `OPENWEATHERMAP_API_KEY` ortam değişkeni

T1 — kullanıcı görevi:

1. OpenWeatherMap hesabından API key al.
2. PowerShell'de key'i ortam değişkeni olarak tanımla:

   ```powershell
   $env:OPENWEATHERMAP_API_KEY="BURAYA_API_KEY"
   ```

3. Gerçek hava entegrasyonunu test et:

   ```powershell
   python -m ml.prediction.features.openweathermap_client
   ```

## Yeni hedef 2: GDD hesaplayıcı productionize

Plan:

- Günlük GDD zaten testli.
- Sonraki üretim katmanı: tarih aralığına göre kümülatif GDD, üst sıcaklık eşiği, eksik/bozuk sıcaklık validasyonu.
- Gerçek hava datasından günlük min-maks üretip kümülatif GDD'ye bağlanacak.

T1 — kullanıcı görevi:

1. Ürün bazlı temel sıcaklık değerlerini netleştir:
   - domates için mevcut değer: `10 C`
   - farklı ürün eklenecekse ürün bazlı eşik listesi çıkar.
2. Gerçek hasat kayıtlarında ekim/hasat tarihi tutarlılığını kontrol et.

## Yeni hedef 3: XGBoost hasat tarihi modeli

Benim eklediğim parça:

- `ml/prediction/training/train_harvest_model.py`
- `config/params.yaml` içinde `harvest_training`
- DVC stage: `train_harvest`
- Model çıktısı: `models/xgboost_harvest_date_model.joblib`
- Metrik çıktısı: `reports/harvest_metrics.json`

T1 — kullanıcı görevi:

1. Paketi kur:

   ```powershell
   python -m pip install xgboost
   ```

2. Pipeline'ı çalıştır:

   ```powershell
   dvc repro train_harvest
   ```

3. Metrikleri kontrol et:

   ```powershell
   dvc metrics show
   ```

## Sonraki kalite adımları

- MLflow model signature ekleme.
- XGBoost ve Random Forest metriklerini ayrı ayrı kıyaslama.
- Gerçek veri geldiğinde sentetik/gerçek veri ayrımını rapora yazma.
- Hasat tarihi inference modülü: `planting_date + predicted_days_to_maturity`.
