# Çalıştırma Komutları

## 1. Sanal ortam

Python 3.10 önerilir.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

XGBoost ayrı kurulacaksa:

```powershell
python -m pip install xgboost
```

## 2. Temel pipeline

```powershell
dvc repro
dvc metrics show
```

## 3. OpenWeatherMap gerçek API testi

API key'i koda yazma. PowerShell oturumunda ortam değişkeni olarak ver:

```powershell
$env:OPENWEATHERMAP_API_KEY="BURAYA_API_KEY"
python -m ml.prediction.features.openweathermap_client
```

## 3.1 Open-Meteo gerçek API testi

Open-Meteo API key istemez. Şehir adı geocoding ile koordinata çevrilir,
ardından 7 günlük forecast alınır.

```powershell
python -m ml.prediction.features.weather_provider
```

Şehir değiştirmek için `config/params.yaml`:

```yaml
weather:
  city: Konya
  timezone: Europe/Istanbul
  forecast_days: 7
```

Feature engineering içinde Open-Meteo kullanmak için:

```yaml
feature_engineering:
  weather_provider: openmeteo
```

Sonra:

```powershell
dvc repro make_features
```

## 4. XGBoost hasat zamanı modeli

```powershell
dvc repro train_harvest
dvc repro predict_harvest
dvc metrics show
```

## 4.1 LSTM + Ensemble hasat modeli

TensorFlow kurulu olmalı (`requirements.txt` içinde).

```powershell
dvc repro make_sequences
dvc repro train_lstm
dvc repro train_ensemble
dvc repro predict_harvest_ensemble
dvc metrics show
```

Öneri: üretim hasat tahmini için ensemble çıktısını kullanın
(`reports/ensemble_harvest_predictions.csv`).

Etiketsiz yeni ekim satırları için `harvest_date` / `days_to_maturity` olmadan
CSV verip tahmin scriptlerine path geçebilirsiniz; feature engineering inference
modunda çalışır.

## 5. MLflow UI

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Tarayıcıda:

```text
http://127.0.0.1:5000
```
