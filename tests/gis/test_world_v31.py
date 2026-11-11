"""World C v3.1: forest HLOD, far facades / storeys, clearance by road class (PTB2022 § 80), walled ramps,
tractor silhouette."""

from __future__ import annotations

import json

import pytest

from conftest import REGION_DIR, REPO

GEN = REGION_DIR / "generated"
WORLD = REPO / "Data" / "raw" / "derived" / "bialystok-industrial-c" / "world"


@pytest.fixture(scope="module")
def qa():
    p = GEN / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json not built")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest():
    return json.loads((GEN / "world_manifest.json").read_text(encoding="utf-8"))


def test_forest_hlod_cells_in_manifest(qa, manifest):
    h = qa["vegetation"]["forest_hlod"]
    assert h["cells"] > 100 and h["cell_m"] == 64.0
    cells = [c for ch in manifest["chunks"] for c in ch.get("forest_cells", [])]
    assert len(cells) == h["cells"]
    assert sum(c["tris"] for c in cells) == h["triangles"]
    assert max(c["tris"] for c in cells) < 2000            # one cheap mesh per 64 m cell
    for prof in ("High", "Low"):
        assert manifest["lod_policy"][prof]["forest_hlod_m"] > 0


def test_forest_trees_reference_their_cell(manifest):
    if not WORLD.exists() or not list(WORLD.glob("instances_*.json")):
        pytest.skip("world instances not built (Data/raw is gitignored)")
    ids = {c["id"] for ch in manifest["chunks"] for c in ch.get("forest_cells", [])}
    n = 0
    for ch in manifest["chunks"]:
        for it in json.loads((REPO / ch["instances"]["file"]).read_text(encoding="utf-8"))["instances"]:
            if "fc" in it:
                assert it["fc"] in ids and it["p"].startswith("tree_") and it.get("fk")
                n += 1
    assert n > 10000


def test_frame_budget_with_forest_hlod(qa):
    """REVIEW r2 #12: the DK8 forest frame was 8.2 M triangles on High; target <= 2 M High, <= 0.6 M Low there."""
    fr = {f["camera"]: f for f in qa["mesh_budget"]["frame_estimate"]}
    dk8 = fr["dk8_dk19_exit"]
    assert dk8["tris_high"] <= 2_000_000, dk8
    assert dk8["tris_low"] <= 600_000, dk8
    assert all(f["tris_high"] <= 2_000_000 for f in fr.values()), {k: f["tris_high"] for k, f in fr.items()}
    assert "forest_hlod" in dk8["by_category_high"]


def test_forest_bakes_present():
    meta = json.loads((REPO / "art-source/world/vegetation/trees_meta.json").read_text(encoding="utf-8"))
    fh = meta["forest_hlod"]
    for mix in ("conifer", "mixed", "broadleaf"):
        for k in ("edge", "canopy"):
            assert (REPO / "art-source/world/vegetation" / fh[mix][k]["png"]).exists()
        assert 8.0 < fh[mix]["edge"]["h_median_m"] < 24.0


def test_clearance_by_road_class_from_regulation():
    """PTB2022 (Dz.U. 2022 poz. 1518) § 80 ust. 1: 5,00 m over A/S, 4,50 m over GP, G, Z, L, D."""
    from roads import standards as S
    assert S.CLEARANCE_BY_CLASS["A"] == S.CLEARANCE_BY_CLASS["S"] == 5.00
    for c in ("GP", "G", "Z", "L", "D"):
        assert S.clearance_height(c) == 4.50
    qa = json.loads((GEN / "roads_qa.json").read_text(encoding="utf-8"))
    assert qa["summary"]["clearance_by_class_m"]["S"] == 5.0


def test_walled_ramps_detected():
    """Andersa ramps (layer=1, no bridge) have no fill in the NMT -> retaining walls, not 1:1.5 embankments."""
    qa = json.loads((GEN / "roads_qa.json").read_text(encoding="utf-8"))
    w = qa["summary"]["walled_ramps"]
    assert w, "no walled ramp found"
    assert any(r["chain"].startswith(("c:w175157461", "c:w228104605", "c:w1101181473", "c:w173956078")) for r in w), w
    for r in w:
        assert r["nmt_fill_max_m"] < r["max_wall_h_m"]


def test_far_facade_materials_cover_palettes():
    from streetscape import buildings_mesh as B
    from streetscape.materials import FAR_GRID, M
    for w in B.BLOCK_WALLS + ["panel_concrete"]:
        assert f"{w}__far_block" in M
    for w in B.OFFICE_WALLS:
        assert f"{w}__far_office" in M and f"{w}__far_ribbon" in M
    assert set(FAR_GRID) == {"block", "office", "ribbon"}


def test_storeys_from_bdot_when_plausible():
    from streetscape.buildings_mesh import storey_plan
    n, sh, zb = storey_plan("office", 41.81, {"storeys": 11})
    assert n == 11 and 3.4 < sh < 3.9
    n, sh, _ = storey_plan("block", 31.6, {"storeys": 4})       # implausible (7 m per storey): derived
    assert n >= 9 and sh == 2.8


def test_lod1_wall_is_not_a_box_face():
    """A LOD1 office edge has a plinth, a far-facade window zone (storey rows of the facade_far set, ADR 0081) and a
    coping ledge."""
    import numpy as np
    from streetscape import buildings_mesh as B
    from streetscape import facade_atlas as FA
    acc = B.Acc()
    B.lod1_wall(acc, "office", "plaster_grey", np.array([0.0, 0.0]), np.array([30.0, 0.0]), np.array([0.0, -1.0]),
                30.0, 99.5, 100.0, 112.0, 0.0, 3, 3.5, 0.45, "office", False, fkey="t:0")
    mats = {m for (_, m) in acc.d}
    assert mats == {"plinth_dark", "plaster_grey__far_office", "hall_flashing"}       # the plain wall rides on the far set
    win = acc.d[("buildings_low", "plaster_grey__far_office")]
    uv = np.concatenate([it[2] for it in win])
    assert all(it[3] is None for it in win)                                   # no UV1 grid any more
    assert uv[:, 0].min() >= 0
    assert uv[:, 1].min() >= FA.FAR_PLAIN_V[0] and uv[:, 1].max() <= FA.FAR_M[1]
    z = np.concatenate([it[0][:, 2] for it in win])
    assert z.max() == pytest.approx(112.0)                                    # the attic band rides on the last chunk
    tris = sum(len(it[1]) for items in acc.d.values() for it in items)
    assert tris <= 18


def test_far_plan_is_shared_by_both_lods():
    """LOD0 cells and LOD1 rows come from one plan: chunks cover every storey once, rows stay inside their group,
    balcony offsets are even (balconies stack), and a LOD0 block wall opens exactly the cells of its rows."""
    from streetscape import buildings_mesh as B
    from streetscape import facade_atlas as FA
    groups = FA.far_groups("block", 11, balcony=True)
    plan = FA.far_plan(groups, "b:3")
    assert sum(n for _, n, *_ in plan) == 11 and [p[0] for p in plan] == sorted(p[0] for p in plan)
    for s0, n, g, r0, off in plan:
        assert r0 + n <= len(FA.FAR_ROWS[g]) and (g != "balcony" or off % 2 == 0)
    ops = B.facade_openings("block", 40.0, 100.0, 100.0 + 1.0 + 5 * 2.8 + 0.6, 5, "b:3", False, False,
                            {"balcony": True, "basement": True}, sh=2.8, zbase=1.0)
    plan = FA.far_plan(FA.far_groups("block", 5, balcony=True), "b:3")
    n = int((40.0 - 1.0) // 3.0)
    want = sum(1 for s in range(5) for i in range(n) if FA.far_entry(*FA.far_storey(plan, s), i)[0] == "bal")
    assert want > 0 and sum(1 for o in ops if o[5] == "bdoor") == want
    assert all(isinstance(o[6], tuple) and o[6][0] == "atlas" for o in ops)   # every opening is an atlas cell


def test_facade_atlas_layout():
    from streetscape import facade_atlas as FA
    rects = sorted(FA.CELLS.values())
    for u0, v0, w, h in rects:
        assert u0 >= FA.GUTTER - 1e-6 and u0 + w <= FA.ATLAS_M[0] - FA.GUTTER + 1e-6
        assert v0 >= FA.GUTTER - 1e-6 and v0 + h <= FA.ATLAS_M[1] - FA.GUTTER + 1e-6
    for i, a in enumerate(rects):                                            # no two cells overlap (gutter between)
        for b in rects[i + 1:]:
            assert (a[0] + a[2] + FA.GUTTER <= b[0] + 1e-6 or b[0] + b[2] + FA.GUTTER <= a[0] + 1e-6 or
                    a[1] + a[3] + FA.GUTTER <= b[1] + 1e-6 or b[1] + b[3] + FA.GUTTER <= a[1] + 1e-6)
    for st, nv in FA.FENCE_VARIANTS.items():
        for v in range(nv):
            u0, v0, w, h = FA.fence_uv(st, v)
            assert 0 <= u0 and u0 + w <= FA.FENCE_M[0] + 1e-6 and v0 + h <= FA.FENCE_M[1] + 1e-6


def test_concrete_fence_steps_with_the_ground():
    """Prefabricated fence: level 2 m bays between posts, stepping with the terrain; two faces per bay."""
    import numpy as np
    from shapely.geometry import LineString
    from streetscape import furniture as F

    class Buf:
        def __init__(self):
            self.parts = []

        def add(self, layer, mat, V, UV, T, src=""):
            self.parts.append((layer, mat, np.asarray(V), np.asarray(UV), np.asarray(T)))
    lin = F.Lin(Buf(), lambda x, y: 100.0 + 0.1 * np.asarray(x))              # 10 % slope along x
    nb = F.concrete_fence(lin, LineString([(0, 0), (20, 0)]), "t", "t")
    assert nb == 10
    layer, mat, V, UV, T = lin.buf.parts[0]
    assert (layer, mat) == ("furniture", "concrete_fence")
    face = V[:8 * 0 + 4]                                                      # first face of bay 0: level
    assert np.ptp(face[:2, 2]) == pytest.approx(0.0) and np.ptp(face[:, 2]) == pytest.approx(F.S.CONCRETE_FENCE_H)
    assert len(T) == nb * 6 + (nb + 1) * 10
    assert lin.buf.parts[1][0] == "collision"


def test_tractor_silhouette_budget():
    from streetscape import life_props as LP
    m0, m1, _ = LP.tractor("blue")
    p0 = m0.out()
    t0 = sum(len(p["T"]) for p in p0)
    t1 = sum(len(p["T"]) for p in m1.out())
    assert 600 < t0 <= 1500 and t1 <= 320
    V = [v for p in p0 for v in p["V"]]
    import numpy as np
    V = np.array(V)
    assert V[:, 2].max() == pytest.approx(LP.TRACTOR["H"], abs=0.01)   # roof deflector top
    assert {"rim", "tyre", "car_glass", "car_trim"} <= {p["mat"] for p in p0}


def test_dock_lod1_silhouette_is_cheap_and_complete():
    """HANDOVER pkt 7: build_dock_lod1 draws the shelter, leveller and wheel guides on LOD1 at < 40 % of LOD0, in at
    most 3 materials (one draw each per chunk); gutter + downpipe share one LOD1 material."""
    import numpy as np
    from streetscape import buildings_mesh as BM
    from streetscape import facade_kit as FK
    acc = BM.Acc()
    a, d, n = np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0])
    BM.build_dock(acc, "buildings", a, d, n, 10.0, 100.0, 7)
    BM.build_dock_lod1(acc, a, d, n, 10.0, 100.0, 7)
    FK.gutter(acc, a, np.array([30.0, 0.0]), n, 108.0)
    FK.downpipe(acc, a, d, n, 5.0, 100.4, 107.9, hopper=True)
    tris = {}
    for (layer, mat), items in acc.d.items():
        tris.setdefault(layer, {})[mat] = sum(len(it[1]) for it in items)
    l0, l1 = tris["buildings"], tris["buildings_low"]
    for m in ("hall_flashing", "paint_yellow", "downpipe"):
        assert l1.get(m), m
    assert set(l1) == {"hall_flashing", "paint_yellow", "downpipe"}, set(l1)
    assert sum(l1.values()) < 0.4 * sum(l0.values())


# ------------------------------------------------------------------------------------------- ADR 0091 (buildings r3)
def _kf(salt):
    return 0.9


def test_house_roof_heights_come_from_lod2():
    """Gable over a rectangle: ridge = LoD2 height, eave = LoD2 eave; without LoD2 the LoD1 height sits at
    K_LOD1 of the rise (measured on the region's 229 LoD2 houses)."""
    from shapely.geometry import box
    from streetscape import roofs as RF
    fp = box(0, 0, 12, 8)
    r = RF.plan(fp, {"roof_type_lod2": "1030", "height_lod2_2017_m": 7.0, "lod2_eave_rel_m": 3.2}, 5.3, 100.0, _kf)
    assert r.kind == "gable" and r.source == "lod2"
    assert r.zeave == pytest.approx(103.2) and r.zridge == pytest.approx(107.0)
    assert abs(float(r.eu[0])) == pytest.approx(1.0)                  # ridge along the long side
    assert float(r.z([6.0, 4.0])) == pytest.approx(107.0) and float(r.z([6.0, 0.0])) == pytest.approx(103.2)
    r1 = RF.plan(fp, {"roof_type_lod2": None}, 6.0, 100.0, _kf)
    assert r1.source == "lod1"
    assert (106.0 - r1.zeave) / (r1.zridge - r1.zeave) == pytest.approx(RF.K_LOD1, abs=0.01)
    assert RF.plan(fp, {"roof_type_lod2": "1000"}, 4.0, 100.0, _kf) is None           # LoD2 says flat


def test_house_roof_profiles_and_kinds():
    """Gable end = three profile points (eave, ridge, eave); hip walls stay at the eave; a mono-pitch half rises
    towards its party wall; an L-shaped footprint keeps its plan and no wall drops below the eave."""
    import numpy as np
    from shapely.geometry import Polygon, box
    from streetscape import roofs as RF
    fp = box(0, 0, 12, 8)
    g = RF.plan(fp, {"roof_type_lod2": "1030", "height_lod2_2017_m": 7.0, "lod2_eave_rel_m": 3.2}, 5.3, 100.0, _kf)
    end = g.profile([12, 0], [12, 8])
    assert len(end) == 3 and end[1][0] == pytest.approx(4.0) and end[1][1] == pytest.approx(107.0)
    assert [round(z, 2) for _, z in g.profile([0, 0], [12, 0])] == [103.2, 103.2]
    h = RF.plan(box(0, 0, 9, 8.5), {"roof_type_lod2": "1040", "height_lod2_2017_m": 7.0, "lod2_eave_rel_m": 3.5}, 5.5,
                100.0, _kf)
    assert h.kind == "hip"
    for a, b in (([0, 0], [9, 0]), ([9, 0], [9, 8.5])):
        zs = [z for _, z in h.profile(a, b)]
        assert max(zs) - min(zs) < 0.35                                # hip: eave all round (ridge stub 0.25 m)
    half = box(0, 0, 8, 12)
    m = RF.plan(half, {"roof_type_lod2": "1010", "height_lod2_2017_m": 11.0, "lod2_eave_rel_m": 5.0}, 7.9, 100.0, _kf,
                others=[box(8, 0, 16, 12)])
    assert m.kind == "mono" and float(m.z([7.9, 6.0])) > float(m.z([0.1, 6.0])) + 3.0     # high at the party wall
    assert RF.plan(half, {"roof_type_lod2": "1010"}, 7.9, 100.0, _kf).kind == "gable"      # no neighbour: gable
    ell = Polygon([(0, 0), (12, 0), (12, 5), (7, 5), (7, 9), (0, 9)])
    r = RF.plan(ell, {"roof_type_lod2": "1130", "height_lod2_2017_m": 8.0, "lod2_eave_rel_m": 3.4}, 6.0, 100.0, _kf)
    c = np.asarray(ell.exterior.coords)
    assert all(z >= r.zeave - 1e-6 for a, b in zip(c, c[1:]) for _, z in r.profile(a, b))


def test_house_roof_mesh_covers_footprint_with_overhang():
    """The covering spans the footprint plus the overhang on both LODs and the collision, the soffit / fascia are
    LOD0 only, and the eaves (gutter lines) are the two long sides of a gable."""
    import numpy as np
    from shapely.geometry import box
    from streetscape import buildings_mesh as B
    from streetscape import roofs as RF
    fp = box(0, 0, 12, 8)
    r = RF.plan(fp, {"roof_type_lod2": "1030", "height_lod2_2017_m": 7.0, "lod2_eave_rel_m": 3.2}, 5.3, 100.0, _kf)
    acc = B.Acc()
    eaves = RF.build(acc, r, fp, "roof_tiles_red")
    assert len(eaves) == 2 and all(abs(float(np.hypot(*(b - a))) - 13.0) < 0.2 for a, b, _ in eaves)

    def area(layer, mat):
        s = 0.0
        for V, T, *_ in acc.d[(layer, mat)]:
            p = V[T]
            e1, e2 = p[:, 1, :2] - p[:, 0, :2], p[:, 2, :2] - p[:, 0, :2]
            s += 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum()
        return s
    want = (12 + 2 * RF.OVERHANG) * (8 + 2 * RF.OVERHANG)
    for layer in ("buildings", "buildings_low"):
        assert area(layer, "roof_tiles_red") == pytest.approx(want, rel=0.01)
    assert area("collision", "collision_building") == pytest.approx(want, rel=0.01)
    assert ("buildings", "hall_flashing") in acc.d and ("buildings_low", "hall_flashing") not in acc.d
    V = np.concatenate([it[0] for it in acc.d[("buildings", "roof_tiles_red")]])
    assert V[:, 2].max() == pytest.approx(107.0 + RF.T_TOP, abs=0.01)
    uv = np.concatenate([it[2] for it in acc.d[("buildings", "roof_tiles_red")]])
    assert uv[:, 1].min() >= -1e-6 and uv[:, 1].max() == pytest.approx((4 + RF.OVERHANG + 0.05) * r.sl, abs=0.02)


def test_attic_window_sits_in_the_gable():
    """A 2-storey house whose eave is one storey high gets its upper window in the gable end, inside the wall
    column that rises as a rectangle."""
    from streetscape import buildings_mesh as B
    prof = [(0.0, 103.3), (4.0, 107.0), (8.0, 103.3)]
    aw = B.attic_window(prof, 103.3, 100.0, 0.3, 2.9, 2, "h:1")
    assert aw is not None
    ua, ub, va, vb = aw["op"][:4]
    assert ua > aw["u0"] and ub < aw["u1"] and vb < aw["zband"] and va >= 103.3 + 0.5
    assert 0.5 * (ua + ub) == pytest.approx(4.0)
    assert B.attic_window([(0.0, 103.3), (8.0, 103.3)], 103.3, 100.0, 0.3, 2.9, 2, "h:1") is None   # eave wall


def test_block_balconies_face_the_sun_and_have_a_rail():
    """Balcony rail geometry (ADR 0091): 12 triangles of handrail on top of the balustrade card."""
    import numpy as np
    from streetscape import buildings_mesh as B
    from streetscape import facade_kit as FK
    acc = B.Acc()
    FK.balcony(acc, np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0]), 5.0, 2.4, 103.0, key="glz-free-1")
    rail = sum(len(it[1]) for it in acc.d[("buildings", "downpipe")])
    assert rail >= 12
    z = np.concatenate([it[0][:, 2] for it in acc.d[("buildings", "downpipe")]])
    assert z.max() >= 103.0 + 1.09 - 0.01                                        # handrail top (a dish bracket may sit higher)
    assert float(B.BALCONY_SUN[1]) < 0 and float(B.BALCONY_SUN[0]) < 0          # south-south-west


def test_r3_materials():
    """Plinth variants carry the splash zone, pitched roofs the roof_tiles set at its own tile, brick the macro drift;
    tint_linear stays scoped to the building envelope (ADR 0086 is a separate task)."""
    from streetscape.materials import M
    for k in ("plinth_dark", "plinth_grey"):
        assert M[k]["splash_h"] == 0.5 and M[k]["tint_linear"] and "runoff" not in M[k]
    for k in ("roof_tiles_red", "roof_tiles_brown", "roof_metal_graphite"):
        assert M[k]["texture_set"] == "roof_tiles" and M[k]["set_tile"]
    assert M["brick_red"]["macro"][1] > 0.06
    r, g, b = M["brick_red"]["color"]
    assert r / b < 0.26 / 0.07                                                   # less saturated than r10
    assert not M["concrete_fence"].get("tint_linear") and not M["yard_paving"].get("tint_linear")
    spec = json.loads((REPO / "art-source" / "world" / "materials" / "materials_spec.json").read_text(encoding="utf-8"))
    assert spec["sets"]["roof_tiles"]["kind"] == "modulation_set"
    pl = spec["sets"]["plaster"]                    # r10: albedo p05-p95 0.447-0.551, relief -3.2..+2.5 mm ('pepper')
    assert pl["albedo"]["p95"] - pl["albedo"]["p05"] < 0.07
    assert pl["height_range_m"][1] - pl["height_range_m"][0] < 0.5 * 0.0057
    assert M["plaster_grey"]["set_tile"] and M["plinth_dark"]["set_tile"]
