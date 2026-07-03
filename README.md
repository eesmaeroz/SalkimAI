# Salkım AI
# Salkım T1 - MLflow + DVC + Feature Engineering Altyapısı

Bu proje, sera domates verimi tahmini için T1 tahminleme modülünün MLOps altyapısını hazırlar.

## Amaç

Bu sistemde amaç, sera verilerinden `yield_kg_per_m2` değerini tahmin etmektir.

## Kullanılan yapılar

- DVC ile veri ve pipeline versiyonlama
- MLflow ile deney takibi
- GDD hesaplama
- Hava API mock modülü
- Feature engineering
- Random Forest Regressor modeli
- MAE, RMSE, R² değerlendirme metrikleri

## Klasör yapısı

```text
salkim_mlops_project/
│
├── config/
│   └── params.yaml
│
├── data/
│   ├── raw/
│   └── processed/
│
├── ml/
│   └── prediction/
│       ├── features/
│       ├── training/
│       └── inference/
│
├── scripts/
├── tests/
├── dvc.yaml
├── requirements.txt
└── README.md