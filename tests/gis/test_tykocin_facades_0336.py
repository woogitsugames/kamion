"""ADR 0336 (neon-tykocin-facades-s24): small-town Podlasie facades in Tykocin — muntined white/brown window
joinery, lintels/surrounds, slope-safe 38–60 cm plinths (plaster + fieldstone, LOD1 house plinths), deterministic
roof material & pitch diversity, and gable roof dormers (lukarny)."""
import json
from pathlib import Path

import numpy as np
import pytest
import shapely

from roads import pipeline
from streetscape import buildings_mesh as BM
from streetscape import facade_atlas as FA
from streetscape import facade_kit as FK
from streetscape import roofs as RF
from streetscape import typology as TY
from test_buildings_0167 import _Buf, _HF, _build

ROOT = Path(__file__).resolve().parents[2]
TYK_DIR = ROOT / "Data/Regions/tykocin"
TYK_ORIGIN = (751371.0, 600319.0)


@pytest.fixture(scope="module")
def tyk_blds():
    fc = json.loads((TYK_DIR / "buildings.geojson").read_text(encoding="utf8"))
    ovs = pipeline.load_overrides("tykocin")
    return {b["id"]: b for b in BM.load(fc, TYK_ORIGIN, ovs)}


@pytest.fixture(scope="module")
def tyk_built(tyk_blds):
    """Build a deterministic sample of Rynek + street buildings in Tykocin on a flat heightfield."""
    rynek = [b for b in tyk_blds.values()
             if 250 <= b["poly"].centroid.x <= 550 and -250 <= b["poly"].centroid.y <= 50]
    buf = _Buf()
    rep = {}
    BM.build(buf, rynek, _HF, lambda e, n: 100.0, None, None, rep)
    return rynek, buf, rep


def test_tykocin_override_enables_small_town_flag(tyk_blds):
    assert len(tyk_blds) > 500
    assert all(b.get("small_town") is True for b in tyk_blds.values())
    # Regions without the facade_rules small_town override keep small_town=False (bit-identical)
    fc_c = json.loads((ROOT / "Data/Regions/bialystok-industrial-c/buildings.geojson").read_text(encoding="utf8"))
    b_c = BM.load(fc_c, (772650.0, 602950.0), pipeline.load_overrides("bialystok-industrial-c"))
    assert all(not b.get("small_town") for b in b_c)


def test_small_town_pitched_1130_office():
    # Rynek town building coded 1130 with measured LoD2 rise >= 1.5 m gets a gable roof in small_town mode
    p = {"function": "commercial", "height_m": 8.0, "height_source": "lod2",
         "height_lod2_2017_m": 8.0, "lod2_eave_rel_m": 4.0, "roof_type_lod2": "1130", "storeys": 2}
    assert TY.roof_shape("office", p, {}, small_town=False) == (None, None)
    assert TY.roof_shape("office", p, {}, small_town=True) == ("gable", "lod2_rise")


def test_small_town_joinery_consistency_and_no_office_d(tyk_blds, tyk_built):
    _, buf, rep = tyk_built
    st = rep["small_town"]
    assert st["buildings"] > 30
    assert st["joinery_white"] > 0 and st["joinery_brown"] > 0
    # Every Rynek house and 1-2 storey / pitched town office uses house window cells (never dark office_d)
    b = next(x for x in tyk_blds.values()
             if x["typ"] == "office" and x["poly"].area > 120 and 300 < x["poly"].centroid.x < 460
             and -160 < x["poly"].centroid.y < -30)
    out = _build(b)
    mats_l1 = {p.mat for p in out.parts if p.layer == "buildings_low"}
    assert not any(m.endswith("__far_office_d") for m in mats_l1)
    assert "facade_atlas" in {p.mat for p in out.parts if p.layer == "buildings"}
    # Consistent joinery per house: all house window UVs on one building belong to either white (0,2) or brown (1,3)
    h = next(x for x in tyk_blds.values()
             if x["typ"] == "house" and not x["ovr"] and x["poly"].area > 90
             and 250 < x["poly"].centroid.x < 550 and -250 < x["poly"].centroid.y < 50)
    white_boxes = [FA.cell("house", i) for i in (0, 2)]
    brown_boxes = [FA.cell("house", i) for i in (1, 3)]

    def _in_boxes(u, v, boxes):
        return any(u0 - 1e-3 <= u <= u0 + w + 1e-3 and v0 - 1e-3 <= v <= v0 + h_ + 1e-3
                   for u0, v0, w, h_ in boxes)

    hout = _build(h)
    uvs = [p.UV for p in hout.parts if p.layer == "buildings" and p.mat == "facade_atlas"]
    assert uvs
    has_w = has_b = False
    for uv in uvs:
        # Check face centroids of house window quads
        for k in range(0, len(uv), 4):
            uc, vc = float(np.mean(uv[k:k + 4, 0])), float(np.mean(uv[k:k + 4, 1]))
            if _in_boxes(uc, vc, white_boxes):
                has_w = True
            if _in_boxes(uc, vc, brown_boxes):
                has_b = True
    assert has_w ^ has_b, "a small-town house must use one joinery palette (white OR brown), not mix both"


def test_plinths_stone_and_lod1_and_lintel_trim(tyk_built):
    _, buf, rep = tyk_built
    st = rep["small_town"]
    assert st["window_trim_tris"] > 0
    assert st["stone_plinths"] > 0
    mats_l0 = {p.mat for p in buf.parts if p.layer == "buildings"}
    mats_l1 = {p.mat for p in buf.parts if p.layer == "buildings_low"}
    assert "fieldstone_plinth" in mats_l0
    assert "plinth_dark" in mats_l0 and "plinth_dark" in mats_l1
    assert "reveal_plaster" in mats_l0


def test_roof_diversity_pitch_and_dormers(tyk_blds, tyk_built):
    _, _, rep = tyk_built
    rmats = rep["small_town"]["roof_materials"]
    assert len(rmats) >= 4, f"expected >= 4 roof materials on Rynek sample, got {rmats}"
    assert rep["small_town"]["dormers"] > 0

    # Deterministic pitch variation on LoD1 roofs
    poly = shapely.box(0, 0, 12, 8)
    pitches = set()
    for i in range(15):
        r = RF.plan(poly, {}, 7.5, 0.0, lambda s, i=i: FK.hfloat(f"h{i}", s), shape="gable", pitch_var=True)
        pitches.add(round(float(np.degrees(np.arctan2(r.zridge - r.zeave, 4.0))), 1))
    assert len(pitches) >= 5, f"expected pitch diversity on LoD1 gables, got {pitches}"

    # Dormer geometry stays inside footprint, clears chimneys, and has valid non-degenerate faces
    r = RF.plan(poly, {"height_lod2_2017_m": 7.6, "lod2_eave_rel_m": 4.0, "roof_type_lod2": "1030"},
                7.6, 0.0, lambda s: FK.hfloat("dormer_test", s), shape="gable", pitch_var=True)
    chims = RF.chimney_spots(r, poly, lambda s: FK.hfloat("dormer_test", s), 1)
    # Use a deterministic key_float that passes DORMER_SHARE
    spots = RF.dormer_spots(r, poly, lambda s: 0.1 if s == "dormer" else FK.hfloat("dormer_test", s),
                            chimneys=chims, max_n=2)
    assert len(spots) >= 1
    for sp in spots:
        assert poly.contains(shapely.Point(*sp["p"]))
        mid = sp["p"] - sp["out"] * (0.5 * sp["depth"])
        for cp in chims:
            assert float(np.hypot(*(mid - cp))) >= 1.7
        acc = BM.Acc()
        tris = FK.dormer(acc, sp, "plaster_cream", "roof_tiles_red", "reveal_plaster", 0)
        assert 20 <= tris <= 48
        # Every triangle must have positive area (non-degenerate)
        for (_, _), items in acc.d.items():
            for V, T, *_ in items:
                cross = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
                assert np.all(np.linalg.norm(cross, axis=1) > 1e-6)
