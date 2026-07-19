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

Open-Meteo API key istemez ve JSON endpoint üzerinden çalışır.

```powershell
python -m ml.prediction.features.weather_provider
```

Feature engineering içinde Open-Meteo kullanmak için `config/params.yaml` içinde:

```yaml
feature_engineering:
  weather_provider: openmeteo
```

Sonra:

```powershell
dvc repro make_features
```

## 4. XGBoost hasat zamanı modeli

Önce `xgboost` kurulu olmalı.

```powershell
dvc repro train_harvest
dvc metrics show
```

## 5. MLflow UI

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

Tarayıcıda:

```text
http://127.0.0.1:5000
```
