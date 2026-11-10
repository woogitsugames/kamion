"""CC0 scan materials (ADR 0063): manifest / licence contract, spec provenance and the processing maths.

The processing tests use synthetic fields only (no download needed). The spec tests read
art-source/world/materials/materials_spec.json as built by build_all.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "art-source" / "world" / "materials" / "_src"
sys.path.insert(0, str(SRC))

import pbrkit as K  # noqa: E402
import sets_scan as S  # noqa: E402

MAN = REPO / "art-source" / "world" / "cc0" / "cc0_manifest.json"
SPEC = REPO / "art-source" / "world" / "materials" / "materials_spec.json"
LICENSES = REPO / "docs" / "LICENSES.md"


@pytest.fixture(scope="module")
def man():
    return json.loads(MAN.read_text(encoding="utf-8"))


def test_manifest_is_cc0_and_pinned(man):
    """Only Poly Haven / ambientCG, CC0 1.0, every file pinned by sha256 (D40), every asset in docs/LICENSES.md."""
    lic = LICENSES.read_text(encoding="utf-8")
    assert man["assets"], "empty manifest"
    for a in man["assets"]:
        assert a["source"] in ("polyhaven", "ambientcg"), a["id"]
        assert a["license"] == "CC0 1.0", a["id"]
        assert a["license_page"] in ("https://polyhaven.com/license", "https://docs.ambientcg.com/license/")
        assert a["page"].startswith(("https://polyhaven.com/a/", "https://ambientcg.com/")), a["id"]
        assert a["authors"], a["id"]
        assert len(a["dimensions_mm"]) == 2 and min(a["dimensions_mm"]) > 300, a["id"]
        for f in a["files"]:
            assert len(f["sha256"]) == 64, (a["id"], f["map"])
            assert f["url"].startswith(("https://dl.polyhaven.org/", "https://ambientcg.com/")), f["url"]
            assert "google" not in f["url"].lower()
        assert f"`{a['id']}`" in lic, f"{a['id']} missing in docs/LICENSES.md"


def test_scan_sets_in_spec_keep_calibration(man):
    """Every set built from a scan names its assets; calibrated sets hit their albedo target (the D37 paint/asphalt
    contrast and the r8 asphalt level rest on asphalt_worn = 0.08)."""
    sets = json.loads(SPEC.read_text(encoding="utf-8"))["sets"]
    ids = {a["id"] for a in man["assets"]}
    # CC0 scan sets (ADR 0063) carry a dict source; hero atlases (viaduct_concrete, ADR 0067) a free-text source
    scanned = {k: v for k, v in sets.items() if isinstance(v.get("source"), dict)}
    if not scanned:
        pytest.skip("spec built without scans (build_all.py --procedural or scans not fetched)")
    for name, s in scanned.items():
        assert {x["id"] for x in s["source"]["assets"]} <= ids, name
        t = s.get("albedo_target_mean_lum_linear")
        if s["kind"] == "tiling_set" and t:
            assert abs(s["albedo"]["mean_lum_linear"] / t - 1) < 0.03, (name, s["albedo"]["mean_lum_linear"], t)
        if s["kind"] == "modulation_set":
            assert abs(s["albedo"]["mean_lum_linear"] - 0.5) < 0.01, name
    if "asphalt_worn" in scanned:
        assert abs(sets["asphalt_worn"]["albedo"]["mean_lum_linear"] - 0.08) < 0.002


def _periodic_height(n=256, L=2.0, seed=3):
    c = K.Ctx(n, n, L, L, seed=seed)
    return c, (K.noise(c, 1, 0.04, 0.5) * 1.5e-3).astype(np.float32)


def test_frankot_chellappa_round_trip():
    """Height integrated from the normals reproduces those normals (what the tier writer re-derives)."""
    c, h = _periodic_height()
    n01 = K.normals_from_height(h, c.px) * 0.5 + 0.5
    h2 = S.fc_height(n01, c.px)
    n2 = K.normals_from_height(h2, c.px) * 0.5 + 0.5
    assert np.abs(n2 - n01)[..., :2].mean() < 0.02   # central differences vs spectral inverse near Nyquist
    assert np.corrcoef(h.ravel(), h2.ravel())[0, 1] > 0.98


def test_bombing_is_periodic_and_keeps_contrast():
    """The re-assembled tile wraps without a seam and the variance-preserving blend keeps the source contrast."""
    c, h = _periodic_height(n=128, L=1.0)
    rng = np.random.default_rng(0)
    alb = np.clip(0.2 + 0.05 * rng.standard_normal((128, 128, 3)), 0, 1).astype(np.float32)
    out = S.bomb({"alb": alb, "h": h}, 128, (256, 256), 4, seed=7)
    a = out["alb"] @ K.LUM
    inner = np.abs(np.diff(a, axis=1)).mean()
    seam = np.abs(a[:, 0] - a[:, -1]).mean()
    assert seam < 1.5 * inner
    assert 0.8 < a.std() / (alb @ K.LUM).std() < 1.25
    assert abs(a.mean() - (alb @ K.LUM).mean()) < 0.01


def test_periodic_labels_merge_across_edges():
    solid = np.zeros((20, 20), bool)
    solid[5:10, :3] = True      # one block split by the tile edge
    solid[5:10, -3:] = True
    solid[14:18, 8:12] = True   # a second block
    lab = S.periodic_labels(solid)
    assert lab[6, 0] == lab[6, -1] != 0
    assert len(np.unique(lab[solid])) == 2


def test_hue_rebalance_and_flatten():
    rng = np.random.default_rng(1)
    alb = np.clip(np.array([0.12, 0.09, 0.06]) * (1 + 0.2 * rng.standard_normal((64, 64, 1))), 0, 1).astype(np.float32)
    out = S.rebalance_hue(alb, [0.08, 0.08, 0.079], keep=0.5)
    m = out.reshape(-1, 3).mean(0)
    assert abs(m[0] / m[1] - 1) < 0.03 and abs(m[2] / m[1] - 0.99) < 0.03
    grad = alb * (1 + 0.4 * np.sin(2 * np.pi * np.arange(64) / 64))[None, :, None].astype(np.float32)   # 0.64 m wave
    flat = S.flatten(grad, 0.01, 0.2, 1.0)
    cols = (flat @ K.LUM).mean(0)
    assert cols.std() / cols.mean() < 0.35 * ((grad @ K.LUM).mean(0).std() / (grad @ K.LUM).mean(0).mean())
