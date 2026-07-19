# Salkım AI — MLflow, DVC ve Tahmin Pipeline

Sera domates verimi ve hasat zamanı tahmini için tekrarlanabilir bir MLOps örneği.

## İçerik

- DVC pipeline: örnek veri üretimi, feature engineering, model eğitimi
- MLflow: deney, parametre, metrik ve model artifact kaydı
- GDD hesaplayıcı
- Deterministik hava durumu mock'u
- Open-Meteo canlı hava istemcisi
- OpenWeatherMap gerçek API entegrasyonu
- Random Forest verim modeli
- XGBoost hasat zamanı modeli

## Ana dosyalar

- `config/params.yaml`: pipeline ve model ayarları
- `ml/prediction/features/gdd_calculator.py`: GDD hesaplama
- `ml/prediction/features/weather_api_mock.py`: Open-Meteo + offline mock
- `ml/prediction/features/openweathermap_client.py`: OpenWeatherMap entegrasyonu
- `ml/prediction/features/feature_engineering.py`: feature üretimi
- `ml/prediction/training/train_model.py`: Random Forest verim modeli
- `ml/prediction/training/train_harvest_model.py`: XGBoost hasat zamanı modeli
- `PROJECT_PLAN.md`: genel plan ve T1 kullanıcı görevleri

Kurulum ve çalıştırma adımları için `RUN_COMMANDS.md` dosyasına bak.

Model, rapor, MLflow kayıtları ve işlenmiş veri kaynak kod değildir; pipeline
tarafından yeniden üretildikleri için Git dışında tutulur.
