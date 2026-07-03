"""Growing Degree Day (GDD) calculations."""
from __future__ import annotations


def calculate_gdd(
    min_temp_c: float,
    max_temp_c: float,
    base_temp_c: float = 10.0,
    upper_temp_c: float | None = None,
) -> float:
    """
    GDD, yani Growing Degree Days / Büyüme Derece Günü hesaplar.

    Formül:
        GDD = ((min_temp + max_temp) / 2) - base_temp

    Domates için base_temp genellikle 10°C alınır.

    Negatif değerler 0 kabul edilir.
    Çünkü bitki gelişimi için sıcaklık yetersizse negatif büyüme olmaz.

    Parametreler:
        min_temp_c: Günlük minimum sıcaklık
        max_temp_c: Günlük maksimum sıcaklık
        base_temp_c: Bitki taban sıcaklığı
        upper_temp_c: İsteğe bağlı üst sıcaklık sınırı

    Örnek:
        min_temp_c = 18
        max_temp_c = 30
        base_temp_c = 10

        GDD = ((18 + 30) / 2) - 10
        GDD = 24 - 10
        GDD = 14
    """

    if min_temp_c is None or max_temp_c is None:
        raise ValueError("min_temp_c ve max_temp_c boş olamaz.")

    min_temp_c = float(min_temp_c)
    max_temp_c = float(max_temp_c)

    if upper_temp_c is not None:
        max_temp_c = min(max_temp_c, float(upper_temp_c))
        min_temp_c = min(min_temp_c, float(upper_temp_c))

    avg_temp_c = (min_temp_c + max_temp_c) / 2
    gdd = avg_temp_c - float(base_temp_c)

    return max(gdd, 0.0)


def calculate_cumulative_gdd(
    daily_min_temps_c: list[float],
    daily_max_temps_c: list[float],
    base_temp_c: float = 10.0,
) -> float:
    """
    Birden fazla gün için toplam GDD hesaplar.

    Gerçek hava API'sinden günlük sıcaklıklar geldiğinde kullanılabilir.
    """

    if len(daily_min_temps_c) != len(daily_max_temps_c):
        raise ValueError(
            "Minimum ve maksimum sıcaklık listeleri aynı uzunlukta olmalı."
        )

    total_gdd = 0.0

    for min_temp, max_temp in zip(daily_min_temps_c, daily_max_temps_c):
        total_gdd += calculate_gdd(
            min_temp_c=min_temp,
            max_temp_c=max_temp,
            base_temp_c=base_temp_c,
        )

    return total_gdd