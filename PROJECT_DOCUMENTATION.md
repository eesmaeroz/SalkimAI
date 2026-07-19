# Salkım AI Proje Dokümanı

Son güncelleme: 2026-07-19

## 1. Amaç

Salkım AI, sera domates üretimi için verim ve hasat zamanı tahmini yapan makine öğrenmesi tabanlı bir prototiptir.

Proje amatör düzeyde takip edilebilir olacak kadar sade, ama yazılım uzmanı gözüyle sürdürülebilir olacak kadar modüler tasarlanmıştır.

Ana hedefler:

- Sera verilerinden verim tahmini üretmek.
- Ekim tarihinden ve çevresel koşullardan hasat zamanını tahmin etmek.
- Deneyleri MLflow ile kayıt altına almak.
- Veri/model çıktılarını DVC ile tekrar üretilebilir hale getirmek.
- Gerçek hava API entegrasyonuna hazır bir altyapı kurmak.

## 2. Güncel mimari

```text
salkim_ai/
├── config/
│   ├── params.yaml
│   └── schema.yaml
├── data/
│   ├── raw/
│   └── processed/
├── ml/
│   └── prediction/
│       ├── features/
│       │   ├── feature_engineering.py
│       │   ├── gdd_calculator.py
│       │   ├── openweathermap_client.py
│       │   └── weather_provider.py
│       ├── training/
│       │   ├── train_model.py
│       │   └── train_harvest_model.py
│       └── inference/
│           ├── predict.py
│           └── predict_harvest_date.py
├── scripts/
│   └── create_sample_data.py
├── tests/
│   ├── test_gdd_calculator.py
│   ├── test_feature_engineering.py
│   ├── test_openweathermap_client.py
│   └── test_predict_harvest_date.py
├── dvc.yaml
├── dvc.lock
├── requirements.txt
├── README.md
├── RUN_COMMANDS.md
└── PROJECT_DOCUMENTATION.md
```

## 3. Klasör sorumlulukları

### `config/`

Projenin ayar ve şema merkezidir.

- `params.yaml`: pipeline, model, MLflow ve hava API ayarları
- `schema.yaml`: ham veri için zorunlu kolonlar, opsiyonel kolonlar ve üretilen feature listesi

### `data/`

Veri katmanıdır.

- `data/raw/`: ham veri
- `data/processed/`: feature engineering sonrası işlenmiş veri

Bu klasörlerdeki CSV çıktıları Git yerine DVC tarafından yönetilmelidir.

### `ml/prediction/features/`

Feature engineering ve hava verisi katmanıdır.

- `gdd_calculator.py`: günlük ve kümülatif GDD hesaplama
- `weather_provider.py`: deterministik offline hava verisi ve Open-Meteo JSON istemcisi
- `openweathermap_client.py`: gerçek OpenWeatherMap istemcisi
- `feature_engineering.py`: ham veriden model feature’ları üretme

### `ml/prediction/training/`

Model eğitim katmanıdır.

- `train_model.py`: Random Forest verim tahmini
- `train_harvest_model.py`: XGBoost hasat/olgunlaşma süresi tahmini

Her iki eğitim dosyası da MLflow’a parametre, metrik, model, signature ve input example kaydeder.

### `ml/prediction/inference/`

Tahmin üretme katmanıdır.

- `predict.py`: verim tahmini üretir
- `predict_harvest_date.py`: tahmini olgunlaşma süresini hasat tarihine çevirir

### `scripts/`

Yardımcı script katmanıdır.

- `create_sample_data.py`: gerçek veri yokken sentetik sera verisi üretir

### `tests/`

Test katmanıdır.

Mevcut test sayısı:

```text
10
```

## 4. Veri akışı

```text
scripts/create_sample_data.py
        ↓
data/raw/greenhouse_data.csv
        ↓
ml/prediction/features/feature_engineering.py
        ↓
data/processed/greenhouse_features.csv
        ↓
Random Forest verim modeli
        ↓
reports/predictions.csv

data/processed/greenhouse_features.csv
        ↓
XGBoost hasat modeli
        ↓
reports/harvest_predictions.csv
```

## 5. DVC pipeline

### `create_sample_data`

Sentetik ham veri üretir.

Çıktı:

```text
data/raw/greenhouse_data.csv
```

### `make_features`

Ham veriyi temizler, şemaya göre doğrular, hava verisi eksiklerini doldurur ve yeni feature’lar üretir.

Çıktılar:

```text
data/processed/greenhouse_features.csv
reports/feature_report.json
```

Son doğrulanan çıktı:

```text
Generated rows/columns: (150, 32)
weather_provider: mock
missing_values_after_processing: 0
```

### `train`

Random Forest verim modeli eğitir.

Çıktılar:

```text
models/random_forest_yield_model.joblib
reports/metrics.json
```

Son metrikler:

```text
MAE: 1.28652
RMSE: 1.63932
R2: 0.44599
```

### `train_harvest`

XGBoost ile `days_to_maturity` hedefini tahmin eder.

Çıktılar:

```text
models/xgboost_harvest_date_model.joblib
reports/harvest_metrics.json
```

Son metrikler:

```text
MAE_days: 3.78070
RMSE_days: 4.72927
R2: 0.85511
```

### `predict_harvest`

XGBoost modelinin tahmin ettiği gün sayısını hasat tarihine çevirir.

Çıktı:

```text
reports/harvest_predictions.csv
```

## 6. Giderilen eksikler

### XGBoost eksikliği giderildi

Önceki durum:

```text
ModuleNotFoundError: No module named 'xgboost'
```

Güncel durum:

```text
xgboost 3.2.0 kuruldu
train_harvest başarılı çalıştı
harvest_metrics.json oluştu
```

### Hasat tarihi inference modülü eklendi

Eklenen dosya:

```text
ml/prediction/inference/predict_harvest_date.py
```

Mantık:

```text
predicted_harvest_date = planting_date + predicted_days_to_maturity
```

### MLflow signature eksikliği giderildi

Random Forest ve XGBoost model kayıtlarına eklendi:

- `signature`
- `input_example`

Not: MLflow integer kolonlarda missing value olasılığı için uyarı verebilir. Bu çalışmayı engellemez.

### Gerçek/sentetik veri ayrımı eklendi

Eklenen kolon:

```text
data_source
```

Sentetik veri:

```text
data_source = synthetic
```

Gerçek veri bu kolonu içermezse feature engineering otomatik şunu verir:

```text
data_source = real
```

### Veri şeması config seviyesine çıkarıldı

Eklenen dosya:

```text
config/schema.yaml
```

Artık zorunlu kolonlar ve tipler doğrudan Python kodunun içine gömülü değildir.

### OpenWeatherMap provider seçimi eklendi

`params.yaml` içinde:

```yaml
feature_engineering:
  weather_provider: mock
```

Desteklenen değerler:

```text
mock
openweathermap
none
```

Varsayılan `mock` bırakıldı. Bunun sebebi DVC pipeline’ın API key olmadan da tekrar üretilebilir kalmasıdır.

### Test kapsamı genişletildi

Önceki test sayısı:

```text
5
```

Güncel test sayısı:

```text
10
```

Yeni testlenen alanlar:

- Feature engineering kolon validasyonu
- `data_source` otomatik doldurma
- Feature üretimi
- OpenWeatherMap API key zorunluluğu
- Hasat inference model dosyası yokken güvenli hata

## 7. Güncel doğrulama sonuçları

### Unit test

```text
10 passed
```

### Compile testi

```text
Başarılı
```

### DVC temel pipeline

```text
create_sample_data: başarılı
make_features: başarılı
train: başarılı
```

### XGBoost hasat pipeline

```text
train_harvest: başarılı
predict_harvest: başarılı
```

### Inference

```text
Random Forest prediction: başarılı
Harvest date prediction: başarılı
```

## 8. Hava durumu katmanı

### Mock provider

Varsayılan provider’dır.

Avantajı:

- API key gerekmez
- İnternet gerekmez
- DVC pipeline tekrar üretilebilir kalır

### OpenWeatherMap provider

Gerçek hava verisi entegrasyonu için hazırdır.

API key ortam değişkeninden okunur:

```powershell
$env:OPENWEATHERMAP_API_KEY="BURAYA_API_KEY"
```

Test:

```powershell
python -m ml.prediction.features.openweathermap_client
```

Feature engineering içinde canlı provider denemesi:

```yaml
feature_engineering:
  weather_provider: openweathermap
```

Sonra:

```powershell
dvc repro make_features
```

### Open-Meteo JSON provider

Open-Meteo için SDK yerine doğrudan JSON endpoint kullanılır. Bu yapı senin verdiğin örnekteki `current` ve `hourly` formatıyla uyumludur.

Kullanılan alanlar:

```text
current.temperature_2m
current.relative_humidity_2m
current.wind_speed_10m
hourly.temperature_2m
hourly.relative_humidity_2m
hourly.wind_speed_10m
daily.temperature_2m_max
daily.temperature_2m_min
daily.weather_code
```

Canlı test:

```powershell
python -m ml.prediction.features.weather_provider
```

Feature engineering içinde Open-Meteo kullanmak için:

```yaml
feature_engineering:
  weather_provider: openmeteo
```

Son canlı test sonucu:

```text
Open-Meteo current/hourly/daily JSON verisi başarıyla alındı.
```

## 9. Kalan işler

Kritik kod/mimari eksiği kalmadı.

Kalan işler daha çok production ve dış sistem tarafındadır:

1. OpenWeatherMap API key ile gerçek canlı API testi yapılmalı.
2. DVC remote storage yapılandırılmalı.
3. Gerçek veri kalite raporu eklenmeli.
4. Model karşılaştırma raporu eklenmeli.
5. Training smoke testleri daha da genişletilmeli.
6. MLflow integer schema uyarısı için input örnekleri daha gerçekçi hale getirilmeli.

## 10. Çalıştırma komutları

Tüm temel pipeline:

```powershell
dvc repro
dvc metrics show
```

Random Forest verim tahmini:

```powershell
python -m ml.prediction.inference.predict
```

XGBoost hasat modeli:

```powershell
dvc repro train_harvest
```

Hasat tarihi tahmini:

```powershell
dvc repro predict_harvest
```

OpenWeatherMap gerçek API testi:

```powershell
$env:OPENWEATHERMAP_API_KEY="BURAYA_API_KEY"
python -m ml.prediction.features.openweathermap_client
```

MLflow UI:

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Tarayıcı:

```text
http://127.0.0.1:5000
```

## 11. Genel değerlendirme

Proje artık şu ana hatları başarıyla çalıştırıyor:

```text
sentetik veri üretimi
→ schema validasyonu
→ feature engineering
→ Random Forest verim modeli
→ MLflow kayıt
→ verim inference
→ XGBoost hasat modeli
→ hasat tarihi inference
```

Bu noktada proje araştırma/prototip seviyesinden daha düzenli bir MLOps prototipine geçmiş durumda.

Bir sonraki gerçek sıçrama, koddan çok veri ve deployment tarafında olacak:

```text
gerçek veri
gerçek API key
DVC remote
model karşılaştırma
deployment stratejisi
```
