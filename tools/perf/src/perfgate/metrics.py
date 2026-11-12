"""Metryki bramki wydajności — jedna definicja, używana wszędzie (M38).

Konwencje (udokumentowane też w tools/perf/README.md):
- Percentyle: nearest-rank, tak jak `Get-Percentile` w scripts/device-metrics.ps1:
  rank = ceil(p * n) (min 1), wartość = sorted[rank-1]. NIE interpolacja liniowa.
- Jednostki: frame_ms/cpu_main_ms/gpu_ms w milisekundach, t_s w sekundach.
- GPU/CPU main: próbki 0.000 („sterownik nie raportuje") są odrzucane,
  jak w device-metrics.ps1.
- Cel klatki (target): 1000/30 = 33.333 ms lub 1000/60 = 16.667 ms.
- Skoki czasu klatki (pole `alternation_*`, nazwa historyczna z M38): klatka i (i >= 1)
  liczy się, gdy |frame_ms[i] - frame_ms[i-1]| >= 0.5 * target_ms; alternation_pct =
  100 * liczba takich i / (n - 1). To NIE jest naprzemienność z ADR 0152 (integracja r6:
  M38 twierdził, że ADR 0152 nie ma w repo - jest, docs/adr/0152-fold-flicker-shadows-fps.md).
  Na pomiarach A16 z ADR 0152 ta metryka daje 60,5 % (błąd) vs 63,0 % (po poprawce) - nie
  odróżnia ich.
- Naprzemienność ADR 0152 (`pose_alternation_frac`, port artifacts/fold-flicker/campose.py):
  szereg pozy kamery (diag/campose.csv) po warm-up 25 s od pierwszej próbki; d = różnice
  kolejnych próbek; klatka naprzemienna, gdy d[k] * d[k+1] < 0 i oba |d| > próg (2 mm dla
  head/eye, 0,05° dla pitch/yaw); frac = liczba / max(1, len(d) - 1). A16 legacy head_z
  15,6 % / head_x 10,6 %, po poprawce 0,0 % (ADR 0152, tabela „Wyniki”).
- Janky frame (definicja lokalna; gfxinfo w tych zrzutach nie raportuje
  własnej liczby): frame_ms > 2 * target_ms (pominięte >= 2 pełne vsynci).
- Okna przesuwne: szerokość window_s, krok stride_s; okno ważne gdy ma
  >= min_frames klatek i rozpiętość czasu >= 1 s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .formats import FrameRow

TARGET_MS = {30: 1000.0 / 30.0, 60: 1000.0 / 60.0}
DEFAULT_TARGET_FPS = 30


def nearest_rank_percentile(sorted_vals: np.ndarray, p: float) -> float:
    """nearest-rank: rank = ceil(p*n), min 1 (identycznie jak Get-Percentile)."""
    n = len(sorted_vals)
    if n == 0:
        raise ValueError("nearest_rank_percentile: pusta tablica")
    rank = max(1, math.ceil(p * n))
    return float(sorted_vals[min(rank, n) - 1])


def percentile(vals, p: float) -> float:
    a = np.sort(np.asarray(vals, dtype=float))
    return nearest_rank_percentile(a, p)


def lin_slope(x: np.ndarray, y: np.ndarray) -> float:
    """Nachylenie prostej najmniejszych kwadratów y = a*x + b (jednostka y/x)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2 or float(np.ptp(x)) == 0.0:
        return 0.0
    xm = x.mean()
    ym = y.mean()
    denom = float(((x - xm) ** 2).sum())
    if denom == 0.0:
        return 0.0
    return float(((x - xm) * (y - ym)).sum() / denom)


@dataclass
class FrameMetrics:
    n: int
    span_s: float
    mean_fps: float
    mean_frame_ms: float
    harmonic_fps: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    target_fps: int
    target_ms: float
    pacing_mad_ms: float
    pacing_rms_ms: float
    over_1_5x_pct: float
    over_1_5x_count: int
    janky_count: int
    janky_pct: float
    alternation_pct: float
    alternation_count: int
    gpu_p50_ms: float | None
    gpu_p95_ms: float | None
    gpu_p99_ms: float | None
    gpu_n: int
    cpu_p50_ms: float | None
    cpu_p95_ms: float | None
    cpu_p99_ms: float | None
    cpu_n: int


def resolve_warmup(run: dict | None, override: float | None) -> float:
    """Warm-up [s]: jawny argument, inaczej frameTime.warmupSeconds z metrics.json pomiaru (ta sama
    liczba, z którą device-metrics.ps1 policzył metrics.json - integracja r6: domyślne 5 s dawało dla
    perf-low-r1/diag0/base0 p95 33,52 zamiast 33,469 z metrics.json), inaczej 5 s jak w ps1."""
    if override is not None:
        return float(override)
    mj = (run or {}).get("metrics") or {}
    w = (mj.get("frameTime") or {}).get("warmupSeconds")
    return float(w) if isinstance(w, (int, float)) else 5.0


CAMPOSE_THRESHOLDS = {"head_x_mm": 2.0, "head_z_mm": 2.0, "eye_x_mm": 2.0, "eye_y_mm": 2.0, "eye_z_mm": 2.0,
                      "pitch_deg": 0.05, "yaw_deg": 0.05}


def pose_alternation_frac(values, thr: float) -> float:
    """ADR 0152 (campose.py): udział klatek, w których krok pozy zmienia znak, oba kroki > thr."""
    v = list(values)
    d = [b - a for a, b in zip(v, v[1:])]
    alt = sum(1 for a, b in zip(d, d[1:]) if a * b < 0 and abs(a) > thr and abs(b) > thr)
    return alt / max(1, len(d) - 1)


def campose_alternation(path, warmup_s: float = 25.0) -> dict:
    """diag/campose.csv (ADR 0152) -> {kolumna: frac} dla kolumn z CAMPOSE_THRESHOLDS obecnych w pliku.
    Warm-up liczony od pierwszej próbki (t_s - t0 >= warmup_s), jak w campose.py."""
    import csv

    with open(path, newline="", encoding="utf-8") as f:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
    if not rows:
        return {}
    t0 = rows[0]["t_s"]
    rows = [r for r in rows if r["t_s"] - t0 >= warmup_s]
    return {c: pose_alternation_frac([r[c] for r in rows], thr)
            for c, thr in CAMPOSE_THRESHOLDS.items() if c in rows[0]}


def compute_frame_metrics(
    rows: list[FrameRow],
    warmup_s: float = 5.0,
    target_fps: int = DEFAULT_TARGET_FPS,
) -> FrameMetrics:
    """Metryki z frametimes.csv po odcięciu warm-up (jak device-metrics.ps1)."""
    if target_fps not in TARGET_MS:
        raise ValueError(f"target_fps musi być 30 lub 60, dostano {target_fps}")
    target_ms = TARGET_MS[target_fps]
    kept = [r for r in rows if r.t_s >= warmup_s]
    if not kept:
        kept = list(rows)
    t = np.array([r.t_s for r in kept], dtype=float)
    ft = np.array([r.frame_ms for r in kept], dtype=float)
    gpu = np.array([r.gpu_ms for r in kept if r.gpu_ms > 0], dtype=float)
    cpu = np.array([r.cpu_main_ms for r in kept if r.cpu_main_ms > 0], dtype=float)
    n = len(ft)
    span = float(t[-1] - t[0]) if n > 1 else 0.0
    srt = np.sort(ft)
    dev = np.abs(ft - target_ms)
    alt = np.abs(np.diff(ft)) >= 0.5 * target_ms
    over = ft > 1.5 * target_ms
    janky = ft > 2.0 * target_ms
    return FrameMetrics(
        n=n,
        span_s=span,
        mean_fps=(n / span) if span > 0 else float("nan"),
        mean_frame_ms=float(ft.mean()),
        harmonic_fps=(1000.0 / float(ft.mean())) if ft.mean() > 0 else float("nan"),
        p50_ms=nearest_rank_percentile(srt, 0.50),
        p95_ms=nearest_rank_percentile(srt, 0.95),
        p99_ms=nearest_rank_percentile(srt, 0.99),
        max_ms=float(ft.max()),
        target_fps=target_fps,
        target_ms=target_ms,
        pacing_mad_ms=float(dev.mean()),
        pacing_rms_ms=float(np.sqrt((dev**2).mean())),
        over_1_5x_count=int(over.sum()),
        over_1_5x_pct=100.0 * float(over.mean()),
        janky_count=int(janky.sum()),
        janky_pct=100.0 * float(janky.mean()),
        alternation_count=int(alt.sum()),
        alternation_pct=100.0 * float(alt.sum() / (n - 1)) if n > 1 else 0.0,
        gpu_p50_ms=percentile(gpu, 0.50) if len(gpu) else None,
        gpu_p95_ms=percentile(gpu, 0.95) if len(gpu) else None,
        gpu_p99_ms=percentile(gpu, 0.99) if len(gpu) else None,
        gpu_n=int(len(gpu)),
        cpu_p50_ms=percentile(cpu, 0.50) if len(cpu) else None,
        cpu_p95_ms=percentile(cpu, 0.95) if len(cpu) else None,
        cpu_p99_ms=percentile(cpu, 0.99) if len(cpu) else None,
        cpu_n=int(len(cpu)),
    )


@dataclass
class WindowStat:
    t_start_s: float
    t_end_s: float
    n: int
    fps: float
    p95_ms: float
    over_1_5x_pct: float
    alternation_pct: float


@dataclass
class WindowAnalysis:
    window_s: float
    stride_s: float
    windows: list[WindowStat] = field(default_factory=list)
    worst_p95: WindowStat | None = None
    worst_fps: WindowStat | None = None
    worst_alternation: WindowStat | None = None


def sliding_windows(
    rows: list[FrameRow],
    warmup_s: float = 5.0,
    target_fps: int = DEFAULT_TARGET_FPS,
    window_s: float = 10.0,
    stride_s: float = 1.0,
    min_frames: int = 5,
) -> WindowAnalysis:
    """Okna przesuwne po t_s; najgorsze okno wg p95, wg FPS i wg naprzemienności."""
    target_ms = TARGET_MS[target_fps]
    kept = [r for r in rows if r.t_s >= warmup_s] or list(rows)
    t = np.array([r.t_s for r in kept], dtype=float)
    ft = np.array([r.frame_ms for r in kept], dtype=float)
    if len(ft) == 0:
        return WindowAnalysis(window_s=window_s, stride_s=stride_s)
    t0, t1 = float(t[0]), float(t[-1])
    windows: list[WindowStat] = []
    start = t0
    while start + window_s <= t1 + 1e-9:
        end = start + window_s
        m = (t >= start - 1e-9) & (t < end - 1e-9)
        n = int(m.sum())
        if n >= min_frames and float(t[m][-1] - t[m][0]) >= 1.0:
            wft = ft[m]
            span = float(t[m][-1] - t[m][0])
            alt = np.abs(np.diff(wft)) >= 0.5 * target_ms
            windows.append(
                WindowStat(
                    t_start_s=float(start),
                    t_end_s=float(end),
                    n=n,
                    fps=n / span if span > 0 else float("nan"),
                    p95_ms=nearest_rank_percentile(np.sort(wft), 0.95),
                    over_1_5x_pct=100.0 * float((wft > 1.5 * target_ms).mean()),
                    alternation_pct=100.0 * float(alt.sum() / (n - 1)) if n > 1 else 0.0,
                )
            )
        start += stride_s
    worst_p95 = max(windows, key=lambda w: w.p95_ms) if windows else None
    worst_fps = min(windows, key=lambda w: w.fps) if windows else None
    worst_alt = max(windows, key=lambda w: w.alternation_pct) if windows else None
    return WindowAnalysis(
        window_s=window_s,
        stride_s=stride_s,
        windows=windows,
        worst_p95=worst_p95,
        worst_fps=worst_fps,
        worst_alternation=worst_alt,
    )


@dataclass
class ThermalSeries:
    t_s: np.ndarray
    temp_c: np.ndarray
    thermal_status: np.ndarray
    headroom: np.ndarray
    pss_mb: np.ndarray
    scale: np.ndarray
    fps: np.ndarray


@dataclass
class ThermalAnalysis:
    n: int
    temp_start_c: float | None
    temp_end_c: float | None
    temp_max_c: float | None
    temp_slope_c_per_min: float
    throttle_t_s: float | None
    throttle_reason: str | None
    max_thermal_status: int | None
    pss_min_mb: float | None
    pss_max_mb: float | None
    pss_slope_mb_per_min: float
    pss_leak_suspected: bool
    scale_min: float | None
    scale_drop_t_s: float | None


THERMAL_STATUS_NAMES = {
    0: "NONE",
    1: "LIGHT",
    2: "MODERATE",
    3: "SEVERE",
    4: "CRITICAL",
    5: "EMERGENCY",
    6: "SHUTDOWN",
}

THROTTLE_STATUS_THRESHOLD = 2  # MODERATE i wyżej (Android ThermalService)
PSS_LEAK_SLOPE_MB_PER_MIN = 0.5  # WORKING_VALUE — patrz README
PSS_LEAK_MIN_SPAN_S = 300.0


def analyze_diag_series(diags) -> ThermalAnalysis:
    """Trend termiczny, moment throttlingu, PSS min/max/trend z linii [DIAG]."""
    if not diags:
        return ThermalAnalysis(
            n=0, temp_start_c=None, temp_end_c=None, temp_max_c=None,
            temp_slope_c_per_min=0.0, throttle_t_s=None, throttle_reason=None,
            max_thermal_status=None, pss_min_mb=None, pss_max_mb=None,
            pss_slope_mb_per_min=0.0, pss_leak_suspected=False,
            scale_min=None, scale_drop_t_s=None,
        )
    t = np.array([d.t_s for d in diags], dtype=float)
    temp = np.array([d.get_float("temp") for d in diags], dtype=float)
    temp = np.where(np.isnan(temp), np.nan, temp)
    therm = np.array(
        [d.get_float("thermal") if d.get_float("thermal") is not None else np.nan for d in diags],
        dtype=float,
    )
    head = np.array(
        [d.get_float("headroom") if d.get_float("headroom") is not None else np.nan for d in diags],
        dtype=float,
    )
    pss = np.array(
        [d.get_float("pss") if d.get_float("pss") is not None else np.nan for d in diags],
        dtype=float,
    )
    scale = np.array(
        [d.get_float("scale") if d.get_float("scale") is not None else np.nan for d in diags],
        dtype=float,
    )
    fps = np.array(
        [d.get_float("fps") if d.get_float("fps") is not None else np.nan for d in diags],
        dtype=float,
    )

    temp_ok = temp[~np.isnan(temp)]
    temp_slope = lin_slope(t[~np.isnan(temp)], temp[~np.isnan(temp)]) * 60.0 if len(temp_ok) >= 2 else 0.0

    throttle_t: float | None = None
    throttle_reason: str | None = None
    ok_therm = ~np.isnan(therm)
    if ok_therm.any():
        bad = np.where(ok_therm & (therm >= THROTTLE_STATUS_THRESHOLD))[0]
        if len(bad):
            i = int(bad[0])
            throttle_t = float(t[i])
            throttle_reason = (
                f"thermal status {int(therm[i])} "
                f"({THERMAL_STATUS_NAMES.get(int(therm[i]), '?')}) od t={throttle_t:.0f} s"
            )
    scale_ok = ~np.isnan(scale)
    scale_drop_t: float | None = None
    if scale_ok.any():
        base = float(scale[scale_ok][0])
        if base > 0:
            dropped = np.where(scale_ok & (scale <= 0.95 * base))[0]
            if len(dropped):
                i = int(dropped[0])
                scale_drop_t = float(t[i])
                if throttle_t is None:
                    throttle_t = float(t[i])
                    throttle_reason = (
                        f"adaptacyjna skala renderu {float(scale[i]):.2f} <= 0.95 x startowa "
                        f"{base:.2f} od t={throttle_t:.0f} s"
                    )

    pss_ok = pss[~np.isnan(pss)]
    pss_slope = lin_slope(t[~np.isnan(pss)], pss[~np.isnan(pss)]) * 60.0 if len(pss_ok) >= 2 else 0.0
    span_s = float(t[-1] - t[0]) if len(t) > 1 else 0.0
    leak = bool(pss_slope > PSS_LEAK_SLOPE_MB_PER_MIN and span_s >= PSS_LEAK_MIN_SPAN_S)

    therm_ok = therm[~np.isnan(therm)]
    return ThermalAnalysis(
        n=len(diags),
        temp_start_c=float(temp_ok[0]) if len(temp_ok) else None,
        temp_end_c=float(temp_ok[-1]) if len(temp_ok) else None,
        temp_max_c=float(temp_ok.max()) if len(temp_ok) else None,
        temp_slope_c_per_min=float(temp_slope),
        throttle_t_s=throttle_t,
        throttle_reason=throttle_reason,
        max_thermal_status=int(therm_ok.max()) if len(therm_ok) else None,
        pss_min_mb=float(pss_ok.min()) if len(pss_ok) else None,
        pss_max_mb=float(pss_ok.max()) if len(pss_ok) else None,
        pss_slope_mb_per_min=float(pss_slope),
        pss_leak_suspected=leak,
        scale_min=float(scale[scale_ok].min()) if scale_ok.any() else None,
        scale_drop_t_s=scale_drop_t,
    )


def detect_target_fps(run: dict, override: int | None = None) -> int:
    """Cel FPS: --target-fps, inaczej targetFps z summary.json gdy 30/60, inaczej 30."""
    if override is not None:
        return override
    summary = run.get("summary")
    if isinstance(summary, dict):
        tf = summary.get("targetFps")
        if tf in (30, 60):
            return int(tf)
    return DEFAULT_TARGET_FPS
