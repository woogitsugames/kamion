import numpy as np
import pytest

from perfgate.compare import compare_runs
from perfgate.quality import check_run_quality

from conftest import diag_line, make_rows, write_run_dir


def test_compare_significant_regression_detected():
    rng = np.random.default_rng(7)
    a = rng.normal(33.33, 0.2, 3000)
    b = rng.normal(36.0, 0.2, 3000)  # +2.67 ms p50/p95 — wyraźna regresja
    comps = compare_runs(a, b, target_ms=1000 / 30, boot=4000, seed=42)
    p95 = next(c for c in comps if c.name == "p95_ms")
    assert p95.ci95_lo > 0
    assert p95.verdict == "regression"
    fps = next(c for c in comps if c.name == "mean_fps")
    assert fps.ci95_hi < 0
    assert fps.verdict == "regression"  # spadek FPS to regresja


def test_compare_no_difference():
    rng = np.random.default_rng(11)
    a = rng.normal(33.33, 0.5, 4000)
    b = rng.normal(33.33, 0.5, 4000)
    comps = compare_runs(a, b, target_ms=1000 / 30, boot=4000, seed=42)
    p95 = next(c for c in comps if c.name == "p95_ms")
    assert p95.ci95_lo < 0 < p95.ci95_hi
    assert p95.verdict == "no-significant-difference"


def test_compare_reproducible_same_seed():
    rng = np.random.default_rng(3)
    a = rng.normal(33.33, 1.0, 500)
    b = rng.normal(34.0, 1.0, 500)
    c1 = compare_runs(a, b, 1000 / 30, boot=500, seed=99)
    c2 = compare_runs(a, b, 1000 / 30, boot=500, seed=99)
    assert [c.ci95_lo for c in c1] == [c.ci95_lo for c in c2]


def test_quality_battery_too_low(tmp_path):
    d = write_run_dir(
        tmp_path / "r",
        make_rows([33.333] * 100),
        battery="  level: 30\n  temperature: 280\n",
    )
    from perfgate.formats import load_run_dir

    q = check_run_quality(load_run_dir(d))
    assert not q.valid
    assert any("bateria 30 %" in r for r in q.reasons)


def test_quality_start_temp_too_high(tmp_path):
    d = write_run_dir(
        tmp_path / "r",
        make_rows([33.333] * 100),
        battery="  level: 80\n  temperature: 370\n",
    )
    from perfgate.formats import load_run_dir

    q = check_run_quality(load_run_dir(d))
    assert not q.valid
    assert any("temperatura startowa 37.0" in r for r in q.reasons)


def test_quality_screen_off_or_locked(tmp_path):
    lines = [diag_line(t, fps=0.0) for t in range(0, 61, 5)]
    d = write_run_dir(
        tmp_path / "r",
        make_rows([33.333] * 100),
        diag_lines=lines,
        battery="  level: 80\n  temperature: 280\n",
    )
    from perfgate.formats import load_run_dir

    q = check_run_quality(load_run_dir(d))
    assert not q.valid
    assert any("ekran wyłączony" in r for r in q.reasons)


def test_quality_severe_thermal(tmp_path):
    lines = [diag_line(0, thermal=0), diag_line(50, thermal=3)]
    d = write_run_dir(
        tmp_path / "r",
        make_rows([33.333] * 100),
        diag_lines=lines,
        battery="  level: 80\n  temperature: 280\n",
    )
    from perfgate.formats import load_run_dir

    q = check_run_quality(load_run_dir(d))
    assert not q.valid
    assert any("SEVERE" in r for r in q.reasons)


def test_quality_valid_run(tmp_path):
    lines = [diag_line(t, temp=28.0, thermal=0, fps=30.0) for t in range(0, 91, 5)]
    d = write_run_dir(
        tmp_path / "r",
        make_rows([33.333] * 2700),
        diag_lines=lines,
        battery="  level: 80\n  temperature: 276\n",
    )
    from perfgate.formats import load_run_dir

    q = check_run_quality(load_run_dir(d))
    assert q.valid
    assert q.reasons == []
