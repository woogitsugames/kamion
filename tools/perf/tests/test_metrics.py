import numpy as np
import pytest

from perfgate.metrics import (
    TARGET_MS,
    analyze_diag_series,
    compute_frame_metrics,
    detect_target_fps,
    nearest_rank_percentile,
    percentile,
    sliding_windows,
)

from conftest import diag_line, make_rows


def test_percentile_nearest_rank_matches_powershell():
    # Get-Percentile w device-metrics.ps1: rank = ceil(p*n), sorted[rank-1]
    vals = np.arange(1, 101, dtype=float)  # 1..100
    assert percentile(vals, 0.50) == 50
    assert percentile(vals, 0.95) == 95
    assert percentile(vals, 0.99) == 99
    assert percentile(vals, 1.00) == 100
    # n=3, p=0.95 -> rank=ceil(2.85)=3 -> max
    assert percentile([1.0, 2.0, 3.0], 0.95) == 3.0


def test_mean_fps_and_span():
    rows = make_rows([33.333] * 100, start_t=5.0)
    fm = compute_frame_metrics(rows, warmup_s=0.0, target_fps=30)
    assert fm.n == 100
    # span = t[-1]-t[0] = 99 * 0.033333
    assert fm.span_s == pytest.approx(99 * 0.033333, rel=1e-3)
    assert fm.mean_fps == pytest.approx(100 / fm.span_s, rel=1e-9)


def test_warmup_excludes_early_frames():
    rows = make_rows([1000.0] * 10 + [33.333] * 90, start_t=0.0, dt=1.0)
    fm = compute_frame_metrics(rows, warmup_s=10.0, target_fps=30)
    assert fm.n == 90
    assert fm.max_ms == pytest.approx(33.333)


def test_over_1_5x_and_janky():
    # cel 33.333 ms; 1.5x = 50.0 ms; janky > 66.667 ms
    rows = make_rows([33.333] * 9 + [50.1] + [70.0])
    fm = compute_frame_metrics(rows, warmup_s=0.0, target_fps=30)
    assert fm.over_1_5x_count == 2  # 50.1 i 70.0
    assert fm.over_1_5x_pct == pytest.approx(100 * 2 / 11)
    assert fm.janky_count == 1  # tylko 70.0 > 66.667
    assert fm.janky_pct == pytest.approx(100 / 11)


def test_alternation_exactly_15_6_pct():
    # 1001 klatek -> 1000 granic; 156 granic naprzemiennych = 15.6 %
    # stała część: 845 klatek 33.333 ms (844 granice stałe), potem 156 klatek
    # naprzemiennych 10 / 56.667 ms (każda granica >= 0.5*33.333 = 16.667 ms)
    ft = [33.333] * 845 + [10.0, 56.667] * 78  # 845 + 156 = 1001 klatek, 156 granic alt
    rows = make_rows(ft)
    fm = compute_frame_metrics(rows, warmup_s=0.0, target_fps=30)
    assert fm.n == 1001
    assert fm.alternation_count == 156
    assert fm.alternation_pct == pytest.approx(15.6, abs=1e-9)


def test_alternation_full_pattern_is_100_pct():
    # pełna naprzemienność vsync: 16.667 / 50.001 na przemian -> każda granica
    ft = [16.667, 50.001] * 50
    rows = make_rows(ft)
    fm = compute_frame_metrics(rows, warmup_s=0.0, target_fps=30)
    assert fm.alternation_pct == pytest.approx(100.0)


def test_alternation_steady_is_zero():
    rows = make_rows([33.333 + (i % 3) * 0.01 for i in range(200)])
    fm = compute_frame_metrics(rows, warmup_s=0.0, target_fps=30)
    assert fm.alternation_pct == 0.0


def test_gpu_zero_samples_excluded():
    rows = make_rows([33.333] * 10)
    for i, r in enumerate(rows):
        r.gpu_ms = 0.0 if i < 5 else 20.0 + i
    fm = compute_frame_metrics(rows, warmup_s=0.0, target_fps=30)
    assert fm.gpu_n == 5
    assert fm.gpu_p50_ms == pytest.approx(percentile([20 + i for i in range(5, 10)], 0.5))


def test_sliding_windows_worst():
    # 60 s po 30 FPS (33.333 ms), w środku 10 s katastrofy (100 ms co druga klatka)
    ft = []
    t = 0.0
    for i in range(1800):
        if 25.0 <= t < 35.0:
            ft.append(100.0 if i % 2 == 0 else 16.667)
        else:
            ft.append(33.333)
        t += ft[-1] / 1000.0
    rows = make_rows(ft)
    wa = sliding_windows(rows, warmup_s=0.0, target_fps=30, window_s=10.0, stride_s=1.0)
    assert wa.worst_p95 is not None
    # wiele okien zahacza o region 25-35 s i ma p95 = 100 ms; pierwsze z nich wygrywa
    assert 15.0 <= wa.worst_p95.t_start_s <= 25.0
    assert wa.worst_p95.p95_ms == pytest.approx(100.0)
    assert wa.worst_fps.fps < 20.0
    assert wa.worst_alternation.alternation_pct == pytest.approx(100.0)


def test_throttling_detected_at_120s():
    from perfgate.formats import parse_logcat
    import tempfile, pathlib

    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "diag-logcat.txt"
        lines = [diag_line(t, temp=30.0 + t / 100, thermal=2 if t >= 120 else 0) for t in range(0, 181, 5)]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _, diags = parse_logcat(p)
    therm = analyze_diag_series(diags)
    assert therm.throttle_t_s == pytest.approx(120.0)
    assert "thermal status 2" in therm.throttle_reason
    assert therm.max_thermal_status == 2


def test_throttling_via_scale_drop():
    from perfgate.formats import parse_logcat
    import tempfile, pathlib

    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "diag-logcat.txt"
        lines = [
            diag_line(t, scale=0.75 if t < 60 else 0.70, thermal=0) for t in range(0, 121, 5)
        ]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _, diags = parse_logcat(p)
    therm = analyze_diag_series(diags)
    assert therm.throttle_t_s == pytest.approx(60.0)
    assert "skala renderu" in therm.throttle_reason


def test_thermal_trend_slope():
    from perfgate.formats import parse_logcat
    import tempfile, pathlib

    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "diag-logcat.txt"
        lines = [diag_line(t, temp=30.0 + 0.01 * t) for t in range(0, 301, 5)]  # +0.6 °C/min
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _, diags = parse_logcat(p)
    therm = analyze_diag_series(diags)
    assert therm.temp_slope_c_per_min == pytest.approx(0.6, abs=0.01)
    assert therm.temp_start_c == pytest.approx(30.0)
    assert therm.temp_end_c == pytest.approx(33.0, abs=0.01)


def test_pss_leak_detection():
    from perfgate.formats import parse_logcat
    import tempfile, pathlib

    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "diag-logcat.txt"
        # 800 -> 950 MB w 300 s = +30 MB/min -> wyciek
        lines = [diag_line(t, pss=800 + t / 10.0) for t in range(0, 301, 5)]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _, diags = parse_logcat(p)
    therm = analyze_diag_series(diags)
    assert therm.pss_min_mb == pytest.approx(800.0)
    assert therm.pss_max_mb == pytest.approx(830.0, abs=0.5)
    assert therm.pss_slope_mb_per_min == pytest.approx(6.0, abs=0.1)  # 0.1 MB/s * 60
    assert therm.pss_leak_suspected

    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "diag-logcat.txt"
        lines = [diag_line(t, pss=900 + (t % 10)) for t in range(0, 301, 5)]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _, diags = parse_logcat(p)
    therm = analyze_diag_series(diags)
    assert not therm.pss_leak_suspected


def test_detect_target_fps_from_summary():
    assert detect_target_fps({"summary": {"targetFps": 60}}) == 60
    assert detect_target_fps({"summary": {"targetFps": 240}}) == 30  # uncapped -> domyślny 30
    assert detect_target_fps({}, override=60) == 60


def test_target_ms_values():
    assert TARGET_MS[30] == pytest.approx(33.3333, abs=1e-3)
    assert TARGET_MS[60] == pytest.approx(16.6667, abs=1e-3)
