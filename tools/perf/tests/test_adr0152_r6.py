"""Integracja r6 (M38): naprzemienność z ADR 0152 i warm-up z metrics.json.

ADR 0152 (docs/adr/0152-fold-flicker-shadows-fps.md, tabela „Wyniki”): A16 SM-A165F, High/30, 150 s,
`campose.py` - klatki naprzemienne head_z / head_x: przed (cam_legacy=1) 15,6 % / 10,6 %, po 0,0 % / 0,0 %.
Dane: kolumny t_s, head_x_mm, head_z_mm z artifacts/fold-flicker/a16cam/{legacy,fixed}/campose.csv (pomiar lidera).
Metryka frame_ms (`alternation_pct`) tych dwóch przebiegów nie rozróżnia (60,5 % vs 63,0 %) - stąd osobna metryka.
"""

import json
from pathlib import Path

import pytest

from perfgate.metrics import campose_alternation, pose_alternation_frac, resolve_warmup

DATA = Path(__file__).parent / "data" / "adr0152"
REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("run,head_z,head_x", [("legacy", 0.156, 0.106), ("fixed", 0.0, 0.0)])
def test_campose_alternation_matches_adr0152(run, head_z, head_x):
    alt = campose_alternation(DATA / f"campose_{run}.csv")
    assert round(alt["head_z_mm"], 3) == head_z
    assert round(alt["head_x_mm"], 3) == head_x


def test_pose_alternation_definition():
    # zygzak +-5 mm: każdy krok zmienia znak -> 100 %; zygzak +-0,5 mm (poniżej progu 2 mm) -> 0 %
    assert pose_alternation_frac([0, 5, 0, 5, 0, 5], 2.0) == 1.0
    assert pose_alternation_frac([0, 0.5, 0, 0.5, 0], 2.0) == 0.0
    # monotoniczny ruch -> 0 %; pojedynczy skok tam i z powrotem -> 1 z 4 przejść
    assert pose_alternation_frac([0, 3, 6, 9, 12], 2.0) == 0.0
    assert pose_alternation_frac([0, 0, 5, 0, 0, 0], 2.0) == pytest.approx(1 / 4)


def test_warmup_defaults_to_metrics_json():
    run = {"metrics": json.loads((REPO / "artifacts/perf-low-r1/diag0/base0/metrics.json").read_text(encoding="utf-8"))}
    assert resolve_warmup(run, None) == 25.0
    assert resolve_warmup(run, 5.0) == 5.0
    assert resolve_warmup({"metrics": None}, None) == 5.0


def test_report_reproduces_metrics_json_base0(tmp_path):
    """perfgate report bez --warmup-s daje te same p50/p95/p99 co metrics.json z device-metrics.ps1."""
    from perfgate.formats import load_run_dir
    from perfgate.metrics import compute_frame_metrics

    d = REPO / "artifacts/perf-low-r1/diag0/base0"
    run = load_run_dir(d)
    fm = compute_frame_metrics(run["frames"], warmup_s=resolve_warmup(run, None), target_fps=30)
    ft = run["metrics"]["frameTime"]
    assert fm.n == ft["samples"]
    assert round(fm.p50_ms, 3) == ft["p50Ms"]
    assert round(fm.p95_ms, 3) == ft["p95Ms"]
    assert round(fm.p99_ms, 3) == ft["p99Ms"]
