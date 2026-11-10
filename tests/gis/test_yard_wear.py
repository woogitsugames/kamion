"""ADR 0071 r11 (review 2026-11-10): paving scale, authored yard wear, dock trailers, barrier island, weathered hall.

Run: uv run --project tools/worldgen pytest tests/gis/test_yard_wear.py -q
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest
import shapely
from shapely.geometry import Point, Polygon

from conftest import REGION_DIR, REPO

from roads import pipeline
from roads.meshing import MeshBuf
from streetscape import depot_yard as DY
from streetscape import life as LF
from streetscape import life_props as LP
from streetscape import materials as SM
from streetscape import yard_wear as YW

WORLD = REPO / "Data" / "raw" / "derived" / REGION_DIR.name / "world"
SPEC = REPO / "art-source" / "world" / "materials" / "materials_spec.json"


def test_paving_sets_have_real_block_sizes():
    """Review A1: behaton rendered as 0.4-0.5 m blocks. The scan sets carry their physical size (tile_m) and element
    count; the importer (WorldPbrMaterials: `source.elements_per_tile` -> `_Tile` = tile_m) must sample them at that
    size. Real blocks: behaton ~0.033 m2 (200 x 165 mm), holland 20 x 10 = 0.02 m2."""
    sets = json.loads(SPEC.read_text(encoding="utf-8"))["sets"]
    want = {"behaton_i_grey": (0.026, 0.040), "paving_20x10_grey": (0.017, 0.026)}
    for name, (lo, hi) in want.items():
        s = sets[name]
        n = s.get("source", {}).get("elements_per_tile")
        if n is None:
            pytest.skip(f"{name}: procedural set (no scan), 4 m tile by construction")
        area = s["tile_m"][0] * s["tile_m"][1] / n
        assert lo <= area <= hi, f"{name}: {area:.4f} m2 per element at tile {s['tile_m']}"
    cs = (REPO / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf-8")
    assert 'esrc.Get("elements_per_tile") != null' in cs and 'mat.SetVector("_Tile", tile)' in cs


def _yard():
    """Synthetic yard: dock wall along +x at y = 0 (the yard is at y < 0: outward normal of p -> q = (0, -1))."""
    yard = Polygon([(0, 0), (120, 0), (120, -45), (0, -45)])
    apron = Polygon([(4, 0), (56, 0), (56, -18), (4, -18)])
    paved = [{"id": "a", "poly": apron, "mat": "yard_concrete_worn", "source": "dock_apron"},
             {"id": "b", "poly": yard.difference(apron), "mat": "yard_behaton", "source": "bdot"}]
    docks = [{"id": "bdot:9962cca0:docks0", "edge": ((0.0, 0.0), (120.0, 0.0)), "yard_z": 0.0,
              "docks": [{"u": 8.0 + 4.0 * k, "num": 1 + k} for k in range(11)]}]
    return yard, paved, docks


def _wear():
    return {"id": "y", "kind": "depot_yard", "no_parking_epsg2180": [[[0, 0], [120, 0], [120, -45], [0, -45]]],
            "wear": {"building": "9962cca0",
                     "tracks_uo": [{"pts": [[100, 43], [60, 30], [20, 26], [8, 30]], "passes": 2}],
                     "grime_lines_uo": [{"pts": [[47, 39], [90, 34]], "w": 1.4}],
                     "patches_uo": [{"at": [70, 25], "size": [6, 4], "rot_deg": 10, "tone": "light"},
                                    {"at": [30, 5], "size": [3, 2], "tone": "dark"}],          # on the apron: refused
                     "trenches_uo": [{"a": [50, 40], "b": [52, 20], "w": 0.9, "tone": "dark"}],
                     "oil_per_dock": [2, 5], "grime_edges": True}}


def test_yard_wear_synthetic():
    yard, paved, docks = _yard()
    buf, rep = MeshBuf(), {}

    def zsurf(e, n):
        return 0.01 * np.asarray(e, float)                    # a yard falling 1 %

    YW.apply(buf, [_wear()], (0.0, 0.0), docks, paved, Polygon(), zsurf, rep)
    r = rep["yard_wear"]
    c = r["applied"][0]
    assert c["track_bands"] == 4 and c["patches"] == 1 and c["trenches"] == 1
    assert 22 <= c["oil"] <= 55 and c["grime_bands"] >= 8
    assert r["stale"] == ["y:wear:patch1:off_the_block_paving"]
    mats = {p.mat for p in buf.parts}
    assert mats == {"decal_tyre", "decal_oil", "decal_yard_patch_light", "decal_yard_patch_dark"}
    assert mats <= set(SM.M) and all(SM.M[m].get("decal") for m in mats)
    for p in buf.parts:
        assert p.layer == "markings"
        # every decal lies inside the yard, 2-8 mm over the surface, and faces up
        assert shapely.contains_xy(yard.buffer(0.3), p.V[:, 0], p.V[:, 1]).all(), p.src
        lift = p.V[:, 2] - zsurf(p.V[:, 0], p.V[:, 1])
        assert 0.0015 <= lift.min() and lift.max() <= 0.0085, (p.src, lift.min(), lift.max())
        a, b, cc = p.V[p.T[:, 0]], p.V[p.T[:, 1]], p.V[p.T[:, 2]]
        assert (np.cross(b - a, cc - a)[:, 2] > 0).all(), p.src
        if p.mat == "decal_tyre":            # band contract of Kamion/World PBR _DECAL_TYRE
            assert p.UV1 is not None and np.ptp(p.UV1[:, 0]) < 1e-9 and p.UV[:, 0].max() == pytest.approx(p.UV1[0, 0])
            assert set(np.round(p.UV[:, 1], 6)) == {0.0, 1.0} and 0.3 <= p.UV1[0, 1] <= 1.5
    # deterministic
    buf2 = MeshBuf()
    YW.apply(buf2, [_wear()], (0.0, 0.0), docks, paved, Polygon(), zsurf, {})
    assert len(buf2.parts) == len(buf.parts) and all(np.array_equal(a.V, b.V) for a, b in zip(buf.parts, buf2.parts))
    # an override without the dock row is reported, not dropped
    rep3 = {}
    YW.apply(MeshBuf(), [_wear()], (0.0, 0.0), [], paved, Polygon(), zsurf, rep3)
    assert rep3["yard_wear"]["stale"] == ["y:wear:no_dock_row"]


class _Placer:
    def __init__(self):
        self.items = []

    def add(self, proto, p, yaw, z=None, sz=1.0, src="", group=None):
        self.items.append({"p": proto, "e": float(p[0]), "n": float(p[1]), "z": z, "yaw": float(yaw), "src": src})
        return 0.0


def test_authored_dock_trailers():
    yard, paved, docks = _yard()
    row = [{"dock": 1, "proto": "trailer_curtain_1", "yaw_deg": 1.0, "off_m": 0.1, "lat_m": -0.05},
           {"dock": 3, "proto": "trailer_reefer_0"}, {"dock": 99, "proto": "trailer_box_0"}, {"dock": 5, "proto": "car_x"}]
    o = {"id": "y", "kind": "depot_yard", "dock_trailers": {"building": "9962cca0", "row": row}}
    assert DY.dock_trailers([o]) == {"9962cca0": row}
    pl, rep = _Placer(), {}
    sp = LF.Space(shapely.union_all([p["poly"] for p in paved]), Polygon(), Polygon(), None)
    LF.dock_trailers(pl, docks, sp, rep, authored=DY.dock_trailers([o]))
    assert [i["p"] for i in pl.items] == ["trailer_curtain_1", "trailer_reefer_0"] and rep["dock_trailers"] == 2
    assert len(rep["dock_trailers_authored_stale"]) == 2
    a, b = pl.items
    assert (a["e"], a["n"]) == pytest.approx((8.0 - 0.05, -0.55)) and (b["e"], b["n"]) == pytest.approx((16.0, -0.45))
    # +y of the prototype (toward the kingpin) points out of the wall, turned by the authored angle
    assert a["yaw"] - b["yaw"] == pytest.approx(math.radians(1.0))
    f = np.array([-math.sin(b["yaw"]), math.cos(b["yaw"])])
    assert f == pytest.approx([0.0, -1.0], abs=1e-9)


def _tris(m):
    return sum(len(np.concatenate(t)) for _, t, _ in m.prims.values())


def test_trailer_detail_and_budget():
    """Review A4: landing gear, mudguards, side markers, pallet box, spare wheel, road film - within the LOD budget."""
    for kind in ("curtain", "box", "reefer"):
        l0, l1, col = LP.trailer(kind, "grey")
        # the detail costs one extra submesh (draw) on LOD0 - the road film - and none on LOD1
        assert any(k.startswith("car_dirt_") for k in l0.prims) and not any(k.startswith("car_dirt_") for k in l1.prims)
        known = {"trailer_alu", "trailer_chassis", "trailer_doors", "trailer_strap", "trailer_front", "trailer_front_dark",
                 "trailer_box_white", "trailer_curtain_grey", "coupling_red", "coupling_yellow", "car_trim", "car_light_head",
                 "car_light_tail", "reflector_red", "plate_pl", "tyre", "rim", "reefer_unit", "reefer_grille"}
        assert {k for k in l0.prims if not k.startswith("car_dirt_")} <= known, set(l0.prims) - known
        assert set(l1.prims) <= known, set(l1.prims) - known
        assert _tris(l0) <= 2600 and _tris(l1) <= 260, (kind, _tris(l0), _tris(l1))
        # landing legs: slim (<= 0.12 m) telescopic legs with a sand shoe on the ground
        V = np.concatenate(l1.prims["trailer_chassis"][0])
        leg = V[(np.abs(V[:, 1] - 11.525) < 0.15) & (V[:, 2] < 0.05)]
        assert len(leg) and np.ptp(leg[:, 1]) <= 0.29
    cs = LP.contact_spec("trailer_curtain_0")
    assert cs["axles"][3] == pytest.approx(11.525)            # the landing gear gets a contact core
    for name in ("container_40_3", "gatehouse", "barrier_base"):
        s = LP.contact_spec(name)
        assert s is not None and s["strength"][0] == 1.0 and s["axles"] == [LP.NO_AXLE] * 4
    assert LP.contact_spec("pallet_load") is None


def test_barrier_rest_post_reaches_the_lane():
    """The housing stands on a raised island (gate.ISLAND_H): the rest post across the lane is founded below it."""
    from streetscape import gate as GT
    base, base1, _ = LP.barrier_base()
    for m in (base, base1):
        V = np.concatenate(m.prims["steel_galv"][0])
        post = V[np.abs(V[:, 0] - (LP.BOOM_L - 0.25)) < 0.05]
        assert post[:, 2].min() <= -GT.ISLAND_H - 0.1


def test_island_synthetic():
    from streetscape import gate as GT

    class Lin:
        buf = MeshBuf()

    d = np.arange(0.0, 6.5, 0.5)
    P_e = np.column_stack([d, np.full(len(d), 1.0)])
    P_x = np.column_stack([d, np.full(len(d), -1.0)])
    poly, zt = GT._island(Lin, P_e, P_x, 10.0, "t")
    assert zt == pytest.approx(10.0 + GT.ISLAND_H) and 9.0 < poly.area < 12.01
    mats = {p.mat for p in Lin.buf.parts}
    assert mats == {"curb_concrete", "sidewalk_paving", "collision_curb"}
    for p in Lin.buf.parts:
        a, b, c = p.V[p.T[:, 0]], p.V[p.T[:, 1]], p.V[p.T[:, 2]]
        nrm = np.cross(b - a, c - a)
        if p.mat == "sidewalk_paving":
            assert (nrm[:, 2] > 0).all() and np.allclose(p.V[:, 2], zt)
        elif p.mat == "curb_concrete" and np.ptp(p.V[:, 2]) > 0.1:        # kerb face looks out of the island
            mid = p.V[:, :2].mean(axis=0)
            assert (nrm[:, :2] @ (mid - np.array([3.0, 0.0])) > 0).all()
    # a median narrower than two kerbs gets no island
    assert GT._island(Lin, P_e * [1, 0.2], P_x * [1, 0.2], 10.0, "t") == (None, None)


def test_hero_wall_is_weathered():
    assert SM.M["kp_wall"].get("weather") is True
    src = (REPO / "tools/blender/world/landmarks/make_depot.py").read_text(encoding="utf-8")
    assert "run_top=z1" in src and "UVRunoff" in src


# ------------------------------------------------------------------------------------------------ built region
def _instances():
    if not WORLD.exists() or not list(WORLD.glob("instances_*.json")):
        pytest.skip("world not built: run roads/build_world.py")
    out = []
    for f in sorted(WORLD.glob("instances_*.json")):
        out += json.loads(f.read_text(encoding="utf-8"))["instances"]
    return out


def test_region_yard_wear_and_island():
    inst = _instances()
    qa = json.loads((REGION_DIR / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))["furniture"]
    if "yard_wear" not in qa:
        pytest.skip("world built before ADR 0071 r11")
    ov = next(o for o in pipeline.load_overrides(REGION_DIR.name) if o.get("id") == "kwadrat-park-yard")
    w = qa["yard_wear"]
    assert w["stale"] == [], w["stale"]
    c = w["applied"][0]
    assert c["patches"] == len(ov["wear"]["patches_uo"]) and c["trenches"] == len(ov["wear"]["trenches_uo"])
    assert c["track_bands"] >= 2 * sum(t["passes"] for t in ov["wear"]["tracks_uo"])
    assert c["oil"] >= 11 * ov["wear"]["oil_per_dock"][0] * 0.7 and c["grime_bands"] >= 10
    assert c["tris"] < 6000                                   # the whole wear layer of the yard
    assert qa["life"]["dock_trailers_authored_stale"] == []
    docks = sorted(i["p"] for i in inst if "life:dock" in i.get("src", "") and "9962cca0" in i["src"])
    assert docks == sorted(r["proto"] for r in ov["dock_trailers"]["row"])
    assert len({p.rsplit("_", 1)[0] + p for p in docks}) >= 6     # kinds / colours differ along the row
    g = qa["gates"]["applied"][0]
    assert g["island_m2"] > 6.0 and not [s for s in qa["gates"]["stale"] if "island" in s]
    bases = [i for i in inst if i["p"] == "barrier_base"]
    assert len(bases) == 2 and abs(bases[0]["z"] - bases[1]["z"]) < 1e-6      # both housings on the island top
