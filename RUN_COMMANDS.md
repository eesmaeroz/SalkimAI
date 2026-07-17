# Çalıştırma komutları

```powershell
# Sanal ortam ve bağımlılıklar
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Tüm DVC pipeline'ı: veri -> feature engineering -> eğitim + MLflow kaydı
dvc repro

# Open-Meteo canlı API kontrolü
python -m ml.prediction.features.weather_api_mock

# Testler
python -m pytest -q

# MLflow arayüzü (http://127.0.0.1:5000)
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```
