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
- FastAPI — Backend API
- Docker + Kubernetes — Altyapı
- PostgreSQL + Redis — Veritabanı ve kuyruk

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

## Repo Yapısı
```
SalkımAI/
├── Sprint1/
│   ├── daily_scrum.md
│   ├── sprint_review.md
│   ├── sprint_retro.md
│   ├── sprint_board.png
│   └── urun_durumu.png
└── README.md
```
