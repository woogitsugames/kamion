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
    """A LOD1 office edge has a plinth, a far-facade window zone (UV1 grid) and a coping ledge."""
    import numpy as np
    from streetscape import buildings_mesh as B
    acc = B.Acc()
    B.lod1_wall(acc, "office", "plaster_grey", np.array([0.0, 0.0]), np.array([30.0, 0.0]), np.array([0.0, -1.0]),
                30.0, 99.5, 100.0, 112.0, 0.0, 3, 3.5, 0.45, "office", False)
    mats = {m for (_, m) in acc.d}
    assert {"plinth_dark", "plaster_grey__far_office", "plaster_grey", "hall_flashing"} <= mats
    win = acc.d[("buildings_low", "plaster_grey__far_office")][0]
    assert win[3] is not None and win[3][:, 1].max() == pytest.approx(3.0)      # 3 storeys in UV1 v
    tris = sum(len(it[1]) for items in acc.d.values() for it in items)
    assert tris <= 14


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
