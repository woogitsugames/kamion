"""Porównanie dwóch przebiegów (przed/po, telefon A vs B) — bootstrap.

Metoda (udokumentowana też w README): dla każdej metryki M bierzemy różnicę
d = M(B) - M(A). Rozkład d szacujemy bootstrapem na poziomie klatek: B razy
losujemy ze zwracaniem n_A próbek z przebiegu A i n_B z B (ziarno stałe,
wynik powtarzalny), liczymy d_b. 95 % przedział ufności = percentyle
[2.5, 97.5] rozkładu d_b.

Założenia: klatki w obrębie przebiegu traktujemy jako i.i.d. (narusza to
drift termiczny i autokorelacja — dlatego raport pokazuje też okna 10 s).
Dla metryk czasowych (p95, p99, max) regresja = d > 0; dla FPS — spadek.
„Brak regresji” = górna granica CI (dla czasu) <= 0, czyli liczba, nie wrażenie.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .metrics import percentile

TIME_METRICS = ("p50_ms", "p95_ms", "p99_ms", "max_ms", "gpu_p95_ms", "pacing_mad_ms")
PCT_METRICS = ("over_1_5x_pct", "janky_pct", "alternation_pct")
FPS_METRICS = ("mean_fps",)


@dataclass
class MetricComparison:
    name: str
    a: float | None
    b: float | None
    diff: float | None
    ci95_lo: float | None
    ci95_hi: float | None
    verdict: str  # "regression" | "improvement" | "no-significant-difference" | "no-data"


def _metric_from_frames(ft: np.ndarray, name: str, target_ms: float) -> float:
    if name == "p50_ms":
        return percentile(ft, 0.50)
    if name == "p95_ms":
        return percentile(ft, 0.95)
    if name == "p99_ms":
        return percentile(ft, 0.99)
    if name == "max_ms":
        return float(ft.max())
    if name == "mean_fps":
        return 1000.0 / float(ft.mean())
    if name == "pacing_mad_ms":
        return float(np.abs(ft - target_ms).mean())
    if name == "over_1_5x_pct":
        return 100.0 * float((ft > 1.5 * target_ms).mean())
    if name == "janky_pct":
        return 100.0 * float((ft > 2.0 * target_ms).mean())
    if name == "alternation_pct":
        if len(ft) < 2:
            return 0.0
        return 100.0 * float((np.abs(np.diff(ft)) >= 0.5 * target_ms).sum() / (len(ft) - 1))
    raise ValueError(f"nieznana metryka: {name}")


def _gpu_metric(gpu: np.ndarray, name: str) -> float:
    if name == "gpu_p95_ms":
        return percentile(gpu, 0.95)
    raise ValueError(f"nieznana metryka GPU: {name}")


def compare_runs(
    ft_a: np.ndarray,
    ft_b: np.ndarray,
    target_ms: float,
    gpu_a: np.ndarray | None = None,
    gpu_b: np.ndarray | None = None,
    boot: int = 20000,
    seed: int = 20261113,
    metrics: tuple[str, ...] | None = None,
) -> list[MetricComparison]:
    """Bootstrapowe CI różnicy metryk między przebiegem A (baza) i B."""
    rng = np.random.default_rng(seed)
    ft_a = np.asarray(ft_a, dtype=float)
    ft_b = np.asarray(ft_b, dtype=float)
    names = metrics or tuple(dict.fromkeys(FPS_METRICS + TIME_METRICS + PCT_METRICS))
    results: list[MetricComparison] = []
    for name in names:
        if name == "gpu_p95_ms":
            if gpu_a is None or gpu_b is None or not len(gpu_a) or not len(gpu_b):
                results.append(MetricComparison(name, None, None, None, None, None, "no-data"))
                continue
            a_val = _gpu_metric(gpu_a, name)
            b_val = _gpu_metric(gpu_b, name)
            diffs = np.empty(boot)
            for i in range(boot):
                ra = gpu_a[rng.integers(0, len(gpu_a), len(gpu_a))]
                rb = gpu_b[rng.integers(0, len(gpu_b), len(gpu_b))]
                diffs[i] = _gpu_metric(rb, name) - _gpu_metric(ra, name)
        else:
            a_val = _metric_from_frames(ft_a, name, target_ms)
            b_val = _metric_from_frames(ft_b, name, target_ms)
            diffs = np.empty(boot)
            for i in range(boot):
                ra = ft_a[rng.integers(0, len(ft_a), len(ft_a))]
                rb = ft_b[rng.integers(0, len(ft_b), len(ft_b))]
                diffs[i] = _metric_from_frames(rb, name, target_ms) - _metric_from_frames(
                    ra, name, target_ms
                )
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        is_time = name in TIME_METRICS or name == "gpu_p95_ms" or name in PCT_METRICS
        if lo > 0:
            verdict = "regression" if is_time else "improvement"
        elif hi < 0:
            verdict = "improvement" if is_time else "regression"
        else:
            verdict = "no-significant-difference"
        results.append(
            MetricComparison(
                name=name,
                a=a_val,
                b=b_val,
                diff=b_val - a_val,
                ci95_lo=float(lo),
                ci95_hi=float(hi),
                verdict=verdict,
            )
        )
    return results
