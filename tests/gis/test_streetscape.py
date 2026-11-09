"""Streetscape generator (tools/worldgen/streetscape): paved areas, buildings, furniture, vegetation.

Unit tests run without raw data; output tests read the generated files of the last
`build_world.py --region bialystok-industrial-c` run (instances are in gitignored Data/raw -> skipped).
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest
import shapely
from shapely.geometry import Polygon

from conftest import REGION_DIR, REGION_ID, REPO

WORLD = REPO / "Data" / "raw" / "derived" / REGION_ID / "world"


# ------------------------------------------------------------------------------------------ units
def test_paved_triangulation_covers_polygon():
    from streetscape import paved as PV
    poly = Polygon([(0, 0), (37.3, 2.1), (41.0, 25.5), (12.2, 31.0), (-3.0, 14.0)],
                   [[(10, 10), (15, 10), (15, 14), (10, 14)]])
    T = PV.triangulate(poly)
    a = 0.5 * np.abs((T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) -
                     (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0]))
    assert abs(a.sum() - poly.area) < 1e-3 * poly.area
    edge = np.max(np.linalg.norm(np.diff(np.concatenate([T, T[:, :1]], axis=1), axis=1), axis=2))
    assert edge <= PV.CELL * math.sqrt(2) + 1e-6          # follows the ground every <= 4 m


def test_wall_openings_are_holes():
    """Wall area = full rectangle minus the openings (openings are real holes, not decals)."""
    from streetscape import buildings_mesh as BM
    acc = BM.Acc()
    ops = [(2.0, 3.5, 1.0, 2.5, 0.15, "window", "glass"), (5.0, 8.0, 0.0, 3.0, 0.25, "dock", "dock_door")]
    BM.wall_with_openings(acc, "buildings", "hall_wall_grey", np.array([0.0, 0.0]), np.array([1.0, 0.0]),
                          np.array([0.0, -1.0]), 10.0, 0.0, 6.0, ops)
    V, T, _ = acc.d[("buildings", "hall_wall_grey")][0]
    area = 0.0
    for (V_, T_, _) in acc.d[("buildings", "hall_wall_grey")]:
        a, b, c = V_[T_[:, 0]], V_[T_[:, 1]], V_[T_[:, 2]]
        area += 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()
        n = np.cross(b - a, c - a)
        assert (n[:, 1] < 0).all()                         # every wall triangle faces outward (-N here)
    assert abs(area - (60.0 - 1.5 * 1.5 - 3.0 * 3.0)) < 1e-6
    assert ("buildings", "dock_door") in acc.d and ("buildings", "glass") in acc.d


def test_sign_heights_from_regulation():
    from roads import standards as S
    assert S.SIGN_H_MIN == 2.00 and S.SIGN_H_SIDEWALK == 2.20 and S.SIGN_H_OVERHEAD == 5.00   # Tabl. 1.11


def test_sign_faces_shapes_and_determinism():
    from streetscape import signs as SG
    for code in ("A-7", "B-20", "C-12", "D-1", "D-6", "D-15", "B-33_70"):
        shape, im = SG.face(code)
        a = np.asarray(im)[..., 3]
        assert a[256, 256] == 255                          # centre opaque
        assert a[2, 2] == 0                                # corner transparent (plate outline is the shape)
        assert SG.png_bytes(im) == SG.png_bytes(SG.face(code)[1])
    _, a7 = SG.face("A-7")
    rgb = np.asarray(a7)[..., :3].astype(int)
    assert tuple(rgb[180, 256]) == SG.YELLOW                # A-7: yellow field
    assert tuple(rgb[60, 256]) == SG.RED                    # red border at the top edge


# ------------------------------------------------------------------------------------------ outputs
@pytest.fixture(scope="module")
def qa():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json not generated")
    return json.loads(p.read_text(encoding="utf-8"))


def test_hero_warehouse_has_docks(qa):
    b = qa["buildings"]
    assert any("9962cca0" in f for f in b["dock_facades"]), "Kwadrat Park override (overrides.yaml) not applied"
    assert b["docks"] >= 10


def test_paved_sources_used(qa):
    src = qa["paved_m2_by_source"]
    assert src["bdot10k_PTPL"][1] > 50_000                   # depot yards etc. are not lawn any more
    assert src["dock_apron"][0] >= 1
    mats = qa["paved_m2_by_material"]
    assert {"yard_paving", "yard_concrete", "yard_asphalt"} <= set(mats)


def test_furniture_counts(qa):
    f = qa["furniture"]
    assert f["lamps"]["rule"] > 100
    assert f["signal_approaches"] > 0
    assert f["junction_signs"].get("C-12", 0) == f["junction_signs"].get("A-7", 0) or \
        f["junction_signs"].get("A-7", 0) > f["junction_signs"].get("C-12", 0)
    assert f["noise_barriers_m"] > 500                      # BDOT10k OT_OIKM_L (Andersa)
    assert f["guardrails_m"]["bridge"] > 0


def test_budget_table_present(qa):
    mb = qa["mesh_budget"]
    assert len(mb["per_chunk"]) == 64
    ids = {f["camera"] for f in mb["frame_estimate"]}
    assert {"stretch_01", "stretch_02", "stretch_03", "stretch_04"} <= ids
    for f in mb["frame_estimate"]:
        assert f["tris_low"] < f["tris_high"]


def test_instances_reference_existing_prototypes():
    if not WORLD.exists() or not list(WORLD.glob("instances_*.json")):
        pytest.skip("world instances not built (Data/raw is gitignored)")
    props = json.loads((REPO / "art-source/world/props/props_meta.json").read_text(encoding="utf-8"))["prototypes"]
    trees = json.loads((REPO / "art-source/world/vegetation/trees_meta.json").read_text(encoding="utf-8"))["trees"]
    man = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    n = 0
    for ch in man["chunks"]:
        data = json.loads((REPO / ch["instances"]["file"]).read_text(encoding="utf-8"))
        b = ch["bounds_local_m"]
        for it in data["instances"]:
            if it["p"].startswith("tree_"):
                assert f"{it['p']}_{it['v']}" in trees
            else:
                assert it["p"] in props, it["p"]
            assert b["e_min"] - 0.01 <= it["e"] <= b["e_max"] + 0.01 or b["e_min"] <= -1024 or b["e_max"] >= 1024
            assert 100.0 < it["z"] < 200.0
            n += 1
    assert n > 1000
