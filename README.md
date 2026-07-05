# Salkım AI — MLflow, DVC ve Feature Engineering

Sera domates verimi tahmini için tekrarlanabilir bir MLOps örneğidir.

## İçerik

- DVC pipeline: örnek veri üretimi, feature engineering ve model eğitimi
- MLflow: Random Forest parametreleri, MAE/RMSE/R² metrikleri ve model artifact'i
- GDD (Growing Degree Days) hesaplama
- İnternet gerektirmeyen deterministik hava durumu mock'u
- Open-Meteo canlı istemcisi: önbellek ve otomatik yeniden deneme

Canlı hava istemcisi Düzce koordinatlarını (`40.8991, 31.1888`) kullanır ve
mevcut sıcaklık/nem, saatlik sıcaklık ve günlük min–maks sıcaklık/hava kodunu
getirir. Eğitim pipeline'ı tekrarlanabilirlik için varsayılan olarak mock veriyi
kullanır.

Kurulum ve çalıştırma adımları için [RUN_COMMANDS.md](RUN_COMMANDS.md) dosyasına
bakın.
