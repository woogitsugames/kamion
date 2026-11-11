"""ADR 0094 (buildings r4, review 2026-11-11 s9 0091): balconies that are not boxes and are not moved off the
facades that had them, no door canopy through a low eave, light soffit and short overhang in re-entrant corners,
flat-toned plaster, ridge caps and chimney flashing."""
from __future__ import annotations

import json

import numpy as np
import pytest
from shapely.geometry import Polygon, box

from conftest import REGION_DIR, REPO

GEN = REGION_DIR / "generated"


def _tris(acc, mat, layer="buildings"):
    return sum(len(it[1]) for it in acc.d.get((layer, mat), []))


def _balcony(key, inner):
    from streetscape import buildings_mesh as B
    from streetscape import facade_kit as FK
    acc = B.Acc()
    FK.balcony(acc, np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0]), 5.0, 2.4, 103.0, variant=1,
               key=key, inner=inner)
    return acc


def test_balcony_is_a_slab_with_a_screen_clear_of_it():
    """P1-5: slab 0.15-0.20 m as its own piece, the balustrade infill starts BAL_GAP above it (front and both sides
    from the `balf` cell), handrail top 1.10 m; above the 2nd storey the faces nobody sees from the street are left
    out (20 triangles)."""
    from streetscape import facade_kit as FK
    key = next(k for k in (f"b{i}" for i in range(200))               # a balcony without glazing / laundry / dish
               if FK.hfloat(k, "glz") >= 0.14 and FK.hfloat(k, "line") >= 0.30 and FK.hfloat(k, "dish") >= 0.18)
    acc = _balcony(key, True)
    slab = np.concatenate([it[0] for it in acc.d[("buildings", "balcony_slab")]])
    assert 0.15 <= slab[:, 2].max() - slab[:, 2].min() <= 0.20 and slab[:, 2].max() == pytest.approx(103.0)
    scr = np.concatenate([it[0] for it in acc.d[("buildings", "facade_atlas")]])
    assert scr[:, 2].min() == pytest.approx(103.0 + FK.BAL_GAP) and FK.BAL_GAP >= 0.08
    assert scr[:, 1].min() < -1.0 and scr[:, 1].max() > -0.01          # screens on the sides run back to the wall
    rail = np.concatenate([it[0] for it in acc.d[("buildings", "downpipe")]])
    assert rail[:, 2].max() == pytest.approx(103.0 + 1.10, abs=0.005)
    full = sum(len(it[1]) for v in acc.d.values() for it in v)
    far = _balcony(key, False)
    lean = sum(len(it[1]) for v in far.d.values() for it in v)
    assert full == 42 and lean == 20


def test_dishes_look_at_the_satellite():
    """P1-5: a dish stands on an arm off the rail and every dish faces the same azimuth (south-south-west)."""
    from streetscape import facade_kit as FK
    assert FK.DISH_AZ[1] < -0.9 and -0.35 < FK.DISH_AZ[0] < 0.0 and 0.0 < FK.DISH_FACE[2] < 0.3
    key = next(k for k in (f"d{i}" for i in range(400))
               if FK.hfloat(k, "glz") >= 0.14 and FK.hfloat(k, "line") >= 0.30 and FK.hfloat(k, "dish") < 0.18)
    south = _balcony(key, True)                                        # facade normal (0, -1): sees the southern sky
    assert _tris(south, "downpipe") > 20                               # arm + mast + LNB on top of rails and posts
    from streetscape import buildings_mesh as B
    north = B.Acc()
    FK.balcony(north, np.array([0.0, 0.0]), np.array([-1.0, 0.0]), np.array([0.0, 1.0]), 5.0, 2.4, 103.0, key=key)
    assert _tris(north, "downpipe") == 20                              # no dish on a balcony that faces north


def test_roof_covering_is_short_in_re_entrant_corners():
    """P1-4: full overhang round the convex outline, OVERHANG_NOTCH inside the notch of an L plan; the soffit takes
    the material the caller names (light boarding), not the graphite flashing."""
    from streetscape import buildings_mesh as B
    from streetscape import roofs as RF
    rect = box(0, 0, 12, 8)
    assert RF.covering(rect).area == pytest.approx(rect.buffer(RF.OVERHANG, join_style="mitre").area, rel=1e-6)
    ell = Polygon([(0, 0), (12, 0), (12, 5), (7, 5), (7, 10), (0, 10)])
    cov = RF.covering(ell)
    full = ell.buffer(RF.OVERHANG, join_style="mitre")
    assert cov.area < full.area - 2.0 and cov.contains(ell.buffer(RF.OVERHANG_NOTCH - 0.01, join_style="mitre"))
    assert not cov.contains(box(7.3, 5.3, 7.45, 5.45)) and RF.OVERHANG_NOTCH < 0.5 * RF.OVERHANG
    r = RF.plan(ell, {"roof_type_lod2": "1030", "height_lod2_2017_m": 8.0, "lod2_eave_rel_m": 3.0}, 6.0, 100.0, lambda s: 0.3)
    acc = B.Acc()
    RF.build(acc, r, ell, "roof_tiles_red", soffit_mat="plinth_dark", fascia_mat="reveal_plaster")
    assert _tris(acc, "plinth_dark") > 0 and _tris(acc, "reveal_plaster") > 0 and _tris(acc, "hall_flashing") == 0
    suv = np.concatenate([it[2] for it in acc.d[("buildings", "plinth_dark")]])
    assert suv[:, 1].min() >= 3.0                                      # above the splash zone of the wall materials


def test_chimney_flashing_follows_the_slope():
    from streetscape import buildings_mesh as B
    from streetscape import facade_kit as FK
    acc = B.Acc()
    FK.chimney(acc, np.array([1.0, 1.0]), np.array([1.0, 0.0]), 5.0, 7.0, apron=lambda q: 5.5 + 0.8 * q[1])
    V = np.concatenate([it[0] for it in acc.d[("buildings", "hall_flashing")] if len(it[1]) == 2 and it[0][:, 2].max() < 6.9])
    assert len(V) == 16
    top = V[V[:, 2] > 5.5 + 0.8 * V[:, 1] + 0.1]
    assert np.allclose(top[:, 2], 5.5 + 0.8 * top[:, 1] + 0.15, atol=1e-6)


def test_r4_palettes_add_no_material():
    """One plinth tone, the four house tones of r3 reweighted, plaster walls with a 1.2 m splash zone."""
    from streetscape import buildings_mesh as B
    from streetscape.materials import M
    assert B.PLINTHS == ["plinth_dark"] and M["plinth_dark"]["color"][0] == pytest.approx(0.20)
    assert set(B.HOUSE_WALLS) == {"plaster_light", "plaster_beige", "plaster_cream", "plaster_grey"}
    assert sum(w in ("plaster_light", "plaster_grey") for w in B.HOUSE_WALLS) * 3 <= len(B.HOUSE_WALLS)
    assert sum(r.startswith("roof_metal") for r in B.ROOFS_PITCHED) * 3 <= len(B.ROOFS_PITCHED)
    for k in ("plaster_grey", "plaster_white", "plaster_cream", "plaster_accent_ochre"):
        assert M[k]["splash_h"] == 1.2 and M[k]["runoff"] and M[k]["set_tile"]
    assert "splash_h" not in M["plaster_grey__far_block"]


def test_plaster_set_is_one_tone():
    """P1-2: the plaster tile carries no paint patches - albedo p05-p95 within 0.025 (r3: 0.060, r10: 0.104)."""
    spec = json.loads((REPO / "art-source" / "world" / "materials" / "materials_spec.json").read_text(encoding="utf-8"))
    alb = spec["sets"]["plaster"]["albedo"]
    assert alb["p95"] - alb["p05"] < 0.025


def test_generated_buildings_report():
    qa = json.loads((GEN / "streetscape_qa.json").read_text(encoding="utf-8"))["buildings"]
    assert qa["house_canopies_under_eave_skipped"] >= 1            # P1-1: low eaves exist in the region
    assert qa["balconies"] >= 2000                                  # P1-3: base rule + sunny side (r3: one side)
