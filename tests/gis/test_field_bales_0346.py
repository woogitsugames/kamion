"""ADR 0346: round straw and wrapped silage bales on rural fields of the ADR 0334 mosaic.

Light unit tests (geometry budget, outward winding, shared single-material atlas, UV quadrant isolation,
deterministic tile-independent placement, rural-only gating, mosaic-use alignment).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from streetscape import export as EX  # noqa: E402
from streetscape import field_bales as FB  # noqa: E402
from streetscape import materials as MT  # noqa: E402
from streetscape import props as PP  # noqa: E402
from streetscape import vegetation as VG  # noqa: E402

ORIGIN = (759563.0, 612607.0)  # knyszyn-w


class _Hf:
    def __init__(self, n=1200, x0=-600.0, y1=600.0, z=120.0):
        self.z = np.full((n, n), z, np.float64)
        self.x0, self.y1 = x0, y1


def _sq(h, origin=ORIGIN):
    ox, oy = origin
    return [[[ox - h, oy - h], [ox + h, oy - h], [ox + h, oy + h], [ox - h, oy + h], [ox - h, oy - h]]]


def _src(rodzaj, h=600.0):
    return {"bdot10k": {"OT_PTTR_A": [{"id": "t", "geometry": {"type": "Polygon", "coordinates": _sq(h)},
                                       "props": {"rodzaj": rodzaj}}], "OT_PTNZ_A": []}, "osm": {"areas": []}}


def _tris(mesh):
    return sum(len(p["T"]) for p in mesh.out())


def test_both_prototypes_share_one_material_and_meet_triangle_budget():
    protos = FB.build_prototypes()
    assert set(protos) == {FB.PROTO_STRAW, FB.PROTO_SILAGE}
    assert FB.MAT in MT.M and MT.M[FB.MAT]["texture"] == FB.ATLAS_NAME
    for name, (lod0, lod1, col) in protos.items():
        p0, p1 = lod0.out(), lod1.out()
        assert {p["mat"] for p in p0} == {FB.MAT}, name
        assert {p["mat"] for p in p1} == {FB.MAT}, name
        assert len(p0) == 1 and len(p1) == 1                    # single submesh = 1 draw per active (proto, lod)
        t0, t1 = _tris(lod0), _tris(lod1)
        assert 120 <= t0 <= 300, (name, t0)
        assert 40 <= t1 <= 80, (name, t1)
        assert col is not None and _tris(col) <= 40


def test_dimensions_ground_contact_and_outward_winding():
    protos = FB.build_prototypes()
    dims = {FB.PROTO_STRAW: (FB.STRAW_D_M, FB.STRAW_L_M), FB.PROTO_SILAGE: (FB.SILAGE_D_M, FB.SILAGE_L_M)}
    for name, (d_m, l_m) in dims.items():
        assert 1.20 <= d_m <= 1.50 and 1.15 <= l_m <= 1.25
        for lod_idx, mesh in enumerate(protos[name][:2]):
            p = mesh.out()[0]
            V, T = p["V"], p["T"]
            assert V[:, 0].min() == pytest.approx(-l_m / 2, abs=0.04)
            assert V[:, 0].max() == pytest.approx(l_m / 2, abs=0.04)
            assert V[:, 2].min() < 0.0                          # sunk slightly into ground (never floats)
            assert d_m * 0.90 <= (V[:, 2].max() - V[:, 2].min()) <= d_m * 1.08
            # Every triangle face normal points outward from the bale centre
            ctr = np.array([0.0, 0.0, d_m * 0.5 - FB.SINK_M])
            C = V[T]
            fn = np.cross(C[:, 1] - C[:, 0], C[:, 2] - C[:, 0])
            fc = C.mean(axis=1) - ctr
            dots = np.sum(fn * fc, axis=1)
            assert (dots > 0.0).all(), (name, lod_idx, float(dots.min()))


def test_uv_stays_inside_own_atlas_quadrant_with_padding():
    protos = FB.build_prototypes()
    pad = FB.ATLAS_PAD_PX / FB.ATLAS_SIZE - 1e-6
    for name, (u_lo, u_hi) in ((FB.PROTO_STRAW, (0.0, 0.5)), (FB.PROTO_SILAGE, (0.5, 1.0))):
        for mesh in protos[name][:2]:
            uv = mesh.out()[0]["UV"]
            assert uv[:, 0].min() >= u_lo + pad and uv[:, 0].max() <= u_hi - pad, name
            assert uv[:, 1].min() >= pad and uv[:, 1].max() <= 1.0 - pad, name


def test_atlas_is_deterministic_512_srgb_and_in_export_textures():
    im1, im2 = FB.atlas_image(), FB.atlas_image()
    assert im1.size == (512, 512) and im1.mode == "RGB"
    assert np.array_equal(np.asarray(im1), np.asarray(im2))
    # Straw side (top-left) is golden-warm (R > G > B), silage side (top-right) is bright off-white/sage (L > straw)
    arr = np.asarray(im1, np.float64)
    straw = arr[24:232, 24:232].mean(axis=(0, 1))
    silage = arr[24:232, 280:488].mean(axis=(0, 1))
    assert straw[0] > straw[1] > straw[2] + 25.0, straw
    assert silage.mean() > straw.mean() + 35.0 and silage.max() < 235.0, silage
    assert FB.ATLAS_NAME in FB.textures()


def test_straw_and_silage_placement_matches_mosaic_uses_and_is_tile_independent():
    hf = _Hf()
    arable = FB.plan_bales(_src("uprawa na gruntach ornych"), ORIGIN, hf)
    grass = FB.plan_bales(_src("roślinność trawiasta"), ORIGIN, hf)
    assert arable and grass
    assert {b["p"] for b in arable} == {FB.PROTO_STRAW}
    assert {b["p"] for b in grass} == {FB.PROTO_SILAGE}
    # Deterministic
    assert arable == FB.plan_bales(_src("uprawa na gruntach ornych"), ORIGIN, hf)
    assert grass == FB.plan_bales(_src("roślinność trawiasta"), ORIGIN, hf)
    # Every bale stands on an allowed mosaic use and clear of baulks
    for items, is_ar, allowed in (
        (arable, True, {"stubble_baled", "stubble"}),
        (grass, False, {"meadow_mown", "meadow_hay"}),
    ):
        P = np.array([[b["e"], b["n"]] for b in items])
        L = VG.field_layout(P[:, 0] + ORIGIN[0], P[:, 1] + ORIGIN[1])
        u = VG.field_use(L, is_ar)
        names = {VG.FIELD_USES[int(v)] for v in u}
        assert names <= allowed, names
        e = np.minimum(L["across"], L["w"] - L["across"])
        assert (e >= FB.STRIP_EDGE_CLEAR_M - 0.05).all()
        assert (L["block_edge"] >= FB.BLOCK_EDGE_CLEAR_M - 0.05).all()
    # Both placement patterns (row + edge) occur across a large sample
    all_tags = {b["src"].split(":")[1] for b in arable + grass}
    assert all_tags == {"row", "edge"}
    # Tile-seam invariance: overlapping tile places the exact same bales in the shared interior
    hf2 = _Hf(x0=-200.0, y1=1000.0)
    arable2 = FB.plan_bales(_src("uprawa na gruntach ornych", h=1200.0), ORIGIN, hf2)
    inner = lambda b: -170 < b["e"] < 570 and -170 < b["n"] < 570
    a = sorted((b["e"], b["n"], b["p"], b["yaw"]) for b in arable if inner(b))
    b = sorted((b["e"], b["n"], b["p"], b["yaw"]) for b in arable2 if inner(b))
    assert a and a == b


def test_rural_only_gating_and_dynamic_prototype_registration():
    hf = _Hf(n=400, x0=-200.0, y1=200.0)
    rep = {}
    items = FB.place(_src("uprawa na gruntach ornych", h=200.0), ORIGIN, hf, hf.z, None, rep, enabled=False)
    assert items == []
    assert rep["field_bales"]["enabled"] is False and rep["field_bales"]["straw"] == 0
    assert FB.prototypes() == {}
    # Re-enable on rural tile -> prototypes registered
    hf_big = _Hf()
    items_on = FB.place(_src("uprawa na gruntach ornych"), ORIGIN, hf_big, hf_big.z, None, rep, enabled=True)
    assert items_on and FB.PROTO_STRAW in FB.prototypes()
    FB.PROTOS.clear()


def test_clearance_from_roads_trees_and_steep_slopes():
    hf = _Hf()
    blocked = np.zeros((1200, 1200), bool)
    blocked[550:650, :] = True                                  # road band across the middle
    zc = hf.z.copy()
    zc[:, :400] = np.arange(400)[None, :] * 0.35                # 35 % slope on the west third
    trees = [{"e": 100.0, "n": 100.0}]
    rep = {}
    items = FB.place(_src("uprawa na gruntach ornych"), ORIGIN, hf, zc, blocked, rep, trees=trees, enabled=True)
    assert items
    for b in items:
        assert b["e"] >= -200.0 - 2.0                           # west steep slope skipped
        assert abs(b["n"]) >= 50.0 + FB.ROAD_CLEAR_M - 1.5      # clear of road band
        assert math.hypot(b["e"] - 100.0, b["n"] - 100.0) >= FB.TREE_CLEAR_M - 0.1
    FB.PROTOS.clear()


def test_lod_policy_matches_unity_importer():
    from roads import build_world as BW
    cs = (ROOT / "game/Assets/_Project/World/Import/InstanceImporter.cs").read_text(encoding="utf-8")
    for name in (FB.PROTO_STRAW, FB.PROTO_SILAGE):
        ends, fixed = BW.instance_ends(name, 2)
        assert ends == [35.0, 340.0] and not fixed
    assert 'proto.StartsWith("bale_")' in cs and "new[] { 35f, 340f }" in cs
