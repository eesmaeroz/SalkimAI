# Salkım AI Mimari Denetim Raporu

Denetim tarihi: 2026-07-17

## 1. Genel durum

Proje mimarisi genel olarak çalışır durumda.

Başarıyla doğrulanan süreçler:

- Python dosyaları derleniyor.
- Unit testler geçiyor.
- DVC temel pipeline çalışıyor.
- Örnek veri üretimi çalışıyor.
- Feature engineering çalışıyor.
- Random Forest verim modeli eğitiliyor.
- MLflow deney kaydı oluşturuluyor.
- Tahmin/inference çıktısı üretilebiliyor.
- OpenWeatherMap entegrasyonu API key yokken güvenli şekilde duruyor.

Henüz tamamlanmamış süreç:

- XGBoost hasat zamanı modeli çalıştırılamadı; sebep `xgboost` paketinin ortamda kurulu olmaması.

## 2. Mevcut dosya yapısı

```text
salkim_ai/
├── config/
│   └── params.yaml
├── data/
│   ├── raw/
│   │   └── greenhouse_data.csv
│   └── processed/
│       └── greenhouse_features.csv
├── ml/
│   └── prediction/
│       ├── features/
│       │   ├── feature_engineering.py
│       │   ├── gdd_calculator.py
│       │   ├── openweathermap_client.py
│       │   └── weather_api_mock.py
│       ├── inference/
│       │   └── predict.py
│       └── training/
│           ├── train_harvest_model.py
│           └── train_model.py
├── models/
│   └── random_forest_yield_model.joblib
├── reports/
│   ├── feature_report.json
│   ├── metrics.json
│   └── predictions.csv
├── scripts/
│   └── create_sample_data.py
├── tests/
│   └── test_gdd_calculator.py
├── dvc.yaml
├── dvc.lock
├── requirements.txt
├── README.md
├── RUN_COMMANDS.md
├── PROJECT_PLAN.md
└── ARCHITECTURE_AUDIT.md
```

Not: `models/`, `reports/`, `data/raw/*.csv`, `data/processed/*.csv`, `mlflow.db` ve `mlruns/` kaynak kod değildir; DVC/pipeline çıktısı olarak ele alınmalıdır.

## 3. DVC pipeline

### `create_sample_data`

Amaç:

- Sentetik sera verisi üretir.

Komut:

```powershell
python scripts/create_sample_data.py
```

Çıktı:

```text
data/raw/greenhouse_data.csv
```

Durum:

```text
Başarılı
```

### `make_features`

Amaç:

- Ham veriyi okur.
- Eksik hava değerlerini mock veriyle doldurur.
- Tarihleri ve sayısal alanları dönüştürür.
- GDD ve ek feature'ları üretir.

Çıktılar:

```text
data/processed/greenhouse_features.csv
reports/feature_report.json
```

Son test çıktısı:

```text
Feature engineering tamamlandı.
Üretilen satır/sütun: (150, 31)
```

Durum:

```text
Başarılı
```

### `train`

Amaç:

- İşlenmiş veriyle Random Forest verim tahmin modeli eğitir.
- MLflow'a parametre, metrik ve model artifact kaydı atar.

Çıktılar:

```text
models/random_forest_yield_model.joblib
reports/metrics.json
mlflow.db
mlruns/
```

Son metrikler:

```text
MAE: 1.26134
RMSE: 1.62010
R2: 0.45891
```

Durum:

```text
Başarılı
```

Uyarı:

```text
MLflow model signature ve input example eksik.
```

Bu kritik hata değildir; production kalitesi için eklenmelidir.

### `train_harvest`

Amaç:

- XGBoost ile `days_to_maturity` hedefini tahmin eder.
- Hasat tarihi tahmini için temel modeli üretir.

Beklenen çıktılar:

```text
models/xgboost_harvest_date_model.joblib
reports/harvest_metrics.json
```

Son test sonucu:

```text
ModuleNotFoundError: No module named 'xgboost'
```

Durum:

```text
Bloklu
```

Çözüm:

```powershell
python -m pip install xgboost
dvc repro train_harvest
```

## 4. Test sonuçları

### Unit test

Komut:

```powershell
python -m pytest -q
```

Sonuç:

```text
5 passed
```

Kapsanan alanlar:

- Günlük GDD hesabı
- Negatif GDD değerlerinin sıfıra çekilmesi
- Kümülatif GDD
- Ters min/max sıcaklık validasyonu
- Mock hava verisinin deterministik olması

### Compile testi

Komut:

```powershell
python -m compileall ml scripts tests
```

Sonuç:

```text
Başarılı
```

## 5. Inference kontrolü

Komut:

```powershell
python -m ml.prediction.inference.predict
```

Sonuç:

```text
Tahminler kaydedildi: C:\salkim_ai\reports\predictions.csv
```

Durum:

```text
Başarılı
```

## 6. Hava durumu entegrasyonları

### Offline mock

Kullanım:

- Test ve DVC pipeline tekrar üretilebilirliği için kullanılır.

Durum:

```text
Başarılı
```

### Open-Meteo

Kullanım:

- API key gerektirmeyen canlı hava verisi testleri için kullanılır.

Durum:

```text
Kod mevcut
```

Not:

- Daha önce `urllib3` / `requests-cache` çevresinde paket uyumsuzluğu yaşandı.
- `requirements.txt` içinde `urllib3==2.7.0` sabitlendi.

### OpenWeatherMap

Kullanım:

- Production gerçek hava verisi entegrasyonu için eklendi.

Güvenlik:

- API key config dosyasına veya koda yazılmaz.
- `OPENWEATHERMAP_API_KEY` ortam değişkeninden okunur.

API key yokken sonuç:

```text
ValueError: OpenWeatherMap API key is empty.
```

Durum:

```text
Kod doğru şekilde güvenli hata veriyor.
Gerçek API testi için kullanıcı API key tanımlamalı.
```

Test komutu:

```powershell
$env:OPENWEATHERMAP_API_KEY="BURAYA_API_KEY"
python -m ml.prediction.features.openweathermap_client
```

## 7. Eksikler ve önerilen iyileştirmeler

### Kritik eksik

1. XGBoost paketi kurulu değil.

   Etki:

   - `train_harvest` stage çalışmıyor.
   - `reports/harvest_metrics.json` oluşmuyor.
   - `dvc metrics show` bu metrik dosyası için uyarı veriyor.

   Çözüm:

   ```powershell
   python -m pip install xgboost
   dvc repro train_harvest
   ```

### Orta öncelikli eksikler

1. MLflow model signature eksik.

   Çözüm:

   - `mlflow.models.infer_signature` ile signature eklenmeli.
   - `input_example` verilerek model artifact daha production uyumlu kaydedilmeli.

2. Hasat tarihi inference modülü eksik.

   Mevcut model `days_to_maturity` tahmin edecek şekilde hazırlandı.
   Sonraki adım:

   ```text
   predicted_harvest_date = planting_date + predicted_days_to_maturity
   ```

3. OpenWeatherMap çıktısı henüz feature engineering'e bağlanmadı.

   Mevcut durum:

   - API client hazır.
   - Pipeline hâlâ tekrar üretilebilirlik için mock veriyi kullanıyor.

   Sonraki adım:

   - Config ile `weather_provider: mock | openmeteo | openweathermap` seçimi eklenebilir.

4. Gerçek veri / sentetik veri ayrımı raporlanmıyor.

   Çözüm:

   - `data_source` kolonu veya ayrı metadata raporu eklenmeli.

### Düşük öncelikli temizlik

1. Bazı Python docstring ve README görüntülerinde terminal encoding kaynaklı Türkçe karakter bozulması görünebilir.

   Etki:

   - Kod çalışmasını bozmaz.
   - Okunabilirliği azaltır.

2. `dvc.lock` son pipeline çalıştırmasıyla güncellendi; commit edilecekse Git'e eklenmeli.

## 8. Kullanıcı T1 görevleri

1. XGBoost kurulumu:

   ```powershell
   python -m pip install xgboost
   ```

2. Hasat modelini çalıştır:

   ```powershell
   dvc repro train_harvest
   dvc metrics show
   ```

3. OpenWeatherMap API key tanımla:

   ```powershell
   $env:OPENWEATHERMAP_API_KEY="BURAYA_API_KEY"
   ```

4. OpenWeatherMap gerçek API testini çalıştır:

   ```powershell
   python -m ml.prediction.features.openweathermap_client
   ```

5. Gerçek veri geldiğinde zorunlu kolonları kontrol et:

   ```text
   greenhouse_id
   crop_type
   variety
   planting_date
   harvest_date
   days_to_maturity
   avg_temperature_C
   min_temperature_C
   max_temperature_C
   humidity_percent
   co2_ppm
   light_intensity_lux
   photoperiod_hours
   irrigation_mm
   fertilizer_N_kg_ha
   fertilizer_P_kg_ha
   fertilizer_K_kg_ha
   pest_severity
   soil_pH
   yield_kg_per_m2
   ```

## 9. Genel sonuç

Mimari çekirdeği çalışıyor.

Şu an güvenilir çalışan hat:

```text
sample data → feature engineering → Random Forest training → MLflow → inference
```

Hazır ama paket/API bekleyen hat:

```text
OpenWeatherMap gerçek hava verisi
XGBoost hasat zamanı modeli
```

Bir sonraki en mantıklı adım:

```text
xgboost kurulumu → dvc repro train_harvest → MLflow signature ekleme → OpenWeatherMap'i feature engineering'e provider seçimiyle bağlama
```
