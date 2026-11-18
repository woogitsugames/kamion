"""Wood siding from the CC0 scan raw_plank_wall (owner decision D-17.11, ADR 0287): processing, wiring, fetch mode.

Synthetic fields only (no download needed); the spec test reads materials_spec.json as built by build_all.py.
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
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

import pbrkit as K  # noqa: E402
import sets_scan as S  # noqa: E402
import cc0_fetch as CF  # noqa: E402
from streetscape import materials as MT  # noqa: E402

SPEC = REPO / "art-source" / "world" / "materials" / "materials_spec.json"


def _boards(px=0.002, n=512, pitch=0.1, seed=0):
    """Horizontal boards `pitch` tall with random tones (x0.4..x1.0), fine grain and 2 mm dark joints."""
    rng = np.random.default_rng(seed)
    y = np.arange(n) * px
    row = (y // pitch).astype(int)
    tone = rng.uniform(0.4, 1.0, row.max() + 1)[row][:, None]
    grain = 1 + 0.08 * np.sin(2 * np.pi * y / 0.007)[:, None] * np.ones((1, n))
    joint = ((y % pitch) < 0.002)[:, None] * np.ones((1, n))
    lum = 0.3 * tone * grain * (1 - 0.6 * joint)
    return np.repeat(lum[..., None], 3, -1).astype(np.float32), joint.astype(bool)


def test_flatten_boards_equalises_boards_keeps_joints_and_grain():
    alb, joint = _boards()
    px = 0.002
    out = S.flatten_boards(alb, px, 0.015, 0.08, 1.0)
    lum0, lum1 = alb @ K.LUM, out @ K.LUM
    assert S.board_tone_cv(lum1, px) < 0.3 * S.board_tone_cv(lum0, px)
    # joints stay darker than the board faces
    assert lum1[joint].mean() < 0.75 * lum1[~joint].mean()
    # grain (7 mm, far below the 15 mm filter) keeps most of its relative amplitude
    face = ~joint[:, 0]
    rel = lambda l: np.std(l[face, 0] / np.convolve(l[face, 0], np.ones(9) / 9, "same"))
    assert rel(lum1) > 0.7 * rel(lum0)
    # geometric mean kept
    assert abs(np.log(lum1).mean() - np.log(lum0).mean()) < 0.02


def test_flatten_boards_hi_knee_compresses_only_splashes():
    alb, _ = _boards()
    alb[100:110, 200:240] *= 2.0                           # a paint splash on one board
    out = S.flatten_boards(alb, 0.002, 0.015, 0.08, 1.0, hi_knee=1.3)
    ref = S.flatten_boards(alb, 0.002, 0.015, 0.08, 1.0)
    l, r = out @ K.LUM, ref @ K.LUM
    assert l[100:110, 200:240].mean() < 0.9 * r[100:110, 200:240].mean()
    assert np.allclose(l[300:400, :100], r[300:400, :100], rtol=0.02)


def test_wood_planks_use_wood_siding_at_real_scale():
    for k in ("wood_planks", "wood_planks_green"):
        m = MT.M[k]
        assert m["texture_set"] == "wood_siding" and m["set_tile"] is True and m["tint_linear"] is True, k
    ids, _ = S.SCAN_SETS["wood_siding"]
    assert ids == ["raw_plank_wall"]
    meta = S.SCAN_ONLY_META["wood_siding"]
    assert meta["kind"] == "modulation_set" and set(meta["slots"]) == {"wood_planks", "wood_planks_green"}
    assert meta["uv"].startswith("mesh_uv0")
    assert CF.SELECTION["raw_plank_wall"][0] == ["wood_siding"]


def test_wood_siding_spec_entry():
    sets = json.loads(SPEC.read_text(encoding="utf-8"))["sets"]
    if "wood_siding" not in sets:
        pytest.skip("wood_siding not built (cc0_fetch.py + build_all.py --only wood_siding)")
    s = sets["wood_siding"]
    assert s["kind"] == "modulation_set" and s["tile_m"] == [1.87, 1.87]
    assert abs(s["albedo"]["mean_lum_linear"] - 0.5) < 0.01
    assert s["source"]["assets"][0]["id"] == "raw_plank_wall"
    before, after = s["source"]["board_tone_cv_before_after"]
    assert after < 0.5 * before


def test_resolve_only_keeps_recorded_assets(monkeypatch):
    """--resolve --only <id> queries just that asset; the recorded entries stay byte-identical."""
    old = {"assets": [{"id": "red_brick", "files": [{"map": "Diffuse", "sha256": "x" * 64}], "marker": 1}]}
    calls = []

    class R:
        def __init__(self, d):
            self.d = d

        def json(self):
            return self.d

    def fake_get(url, headers=None, timeout=None):
        calls.append(url)
        aid = url.rsplit("/", 1)[1]
        if "/info/" in url:
            return R({"name": aid, "authors": {"A": "All"}, "dimensions": [1870.0, 1870.0], "date_published": 1})
        return R({m: {"2k": {"jpg": {"url": f"https://dl.polyhaven.org/{aid}_{m}.jpg", "md5": "m", "size": 1}}}
                  for m in CF.MAPS})

    monkeypatch.setattr(CF.requests, "get", fake_get)
    monkeypatch.setattr(CF, "SELECTION", {"red_brick": (["brick"], "b"), "raw_plank_wall": (["wood_siding"], "w")})
    man = CF.resolve(old, {"raw_plank_wall"})
    assert all("raw_plank_wall" in c for c in calls)
    assert man["assets"][0] is old["assets"][0]
    assert man["assets"][1]["id"] == "raw_plank_wall" and man["assets"][1]["dimensions_mm"] == [1870.0, 1870.0]


def test_wood_planks_long_boards_not_floor():
    """knyszyn-r24 (ADR 0289 'Recenzja s24'): the scan's short staggered boards read as a floor from the street; the
    material samples the 1.87 m scan stretched along the wall (boards >= 3x longer) and with a ~0.13 m board pitch."""
    pitch_scan, tile_scan = 0.093, 1.87
    for k in ("wood_planks", "wood_planks_green"):
        tu, tv = MT.M[k]["set_tile_m"]
        assert tu / tile_scan >= 3.0, k                          # boards (and butt-joint spacing) >= 3x the scan's
        assert 0.12 <= pitch_scan * tv / tile_scan <= 0.18, k    # board pitch in the usual siding range (WORKING_VALUE)
