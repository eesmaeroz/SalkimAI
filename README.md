# 🌿 SalkımAI

Sera domates üreticileri için yapay zeka destekli karar destek platformu.

## Proje Hakkında
SalkımAI; domates görüntülerinden hastalık tespiti, olgunluk analizi ve hasat tarihi tahmini yapan mobil destekli bir AI platformudur.

## Ekip
| İsim | Rol |
|------|-----|
| Esma | V1 — Görüntü İşleme Lead |
| Dilan | V2 — CV & Backend Engineer |
| Arif | T1 — ML/Tahminleme Lead |
| Eren | T2 — Backend & Data Engineer |

## Teknolojiler
- YOLOv8 — Domates tespiti
- EfficientNet-B4 — Hastalık ve olgunluk sınıflandırma
- XGBoost + LSTM — Hasat ve rekolte tahmini
- FastAPI — Backend API
- Docker + Kubernetes — Altyapı
- PostgreSQL + Redis — Veritabanı ve kuyruk
- Flutter — Mobil Uygulama

## Sprint 1 Özeti
| Görev | Durum | Skor |
|-------|-------|------|
| YOLOv8 domates tespit modeli | ✅ Tamamlandı | mAP: 0.941 |
| EfficientNet hastalık modeli | ✅ Tamamlandı | %99.5 accuracy |
| EfficientNet olgunluk modeli | ✅ Tamamlandı | %97.76 accuracy |
| YOLOv8 olgunluk tespiti | ✅ Tamamlandı | mAP: 0.966 |
| FastAPI endpoint | ✅ Tamamlandı | — |
| Docker + Kubernetes altyapısı | ✅ Tamamlandı | — |
| MLflow + feature engineering | ✅ Tamamlandı | — |

## Sprint 1 Belgeleri
Sprint 1 klasöründe aşağıdaki belgeler mevcuttur:
- Daily Scrum Notları
- Sprint Review
- Sprint Retro
- Sprint Board
- Ürün Durumu

## Makine Öğrenmesi & Veri Bilimi (ML)
- DVC pipeline: örnek veri üretimi, feature engineering ve model eğitimi
- MLflow: Random Forest parametreleri, MAE/RMSE/R² metrikleri ve model artifact'i
- GDD (Growing Degree Days) hesaplama
- İnternet gerektirmeyen deterministik hava durumu mock'u
- Open-Meteo canlı istemcisi: önbellek ve otomatik yeniden deneme

Kurulum ve çalıştırma adımları için [RUN_COMMANDS.md](RUN_COMMANDS.md) dosyasına bakın.

## Repo Yapısı
```
SalkımAI/
├── apps/api/       # FastAPI Backend
├── ml/             # Makine Öğrenmesi & Veri Bilimi
├── lib/            # Flutter Mobil Uygulama
├── infra/          # Docker & K8s Altyapısı
├── Sprint1/        # Sprint Belgeleri
└── README.md
```


## Sprint 2 Özeti
| Görev | Durum |
|-------|-------|
| Flutter mobil uygulama | ✅ Tamamlandı |
| XGBoost yield ve maturity modelleri | ✅ Tamamlandı |
| ML pipeline | ✅ Tamamlandı |
| Backend main'e merge | ✅ Tamamlandı |
| Prometheus metrics + Kubernetes | ✅ Tamamlandı |
| API deploy | 🔄 Sprint 3'e taşındı |
| Flutter gerçek API bağlantısı | 🔄 Sprint 3'e taşındı |

## Sprint 2 Belgeleri
Sprint2 klasöründe aşağıdaki belgeler mevcuttur:
- Daily Scrum Notları
- Sprint Review
- Sprint Retro
- Sprint Board
- Ürün Durumu
