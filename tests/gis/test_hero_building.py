"""Hero building override (ADR 0070): spec of the fire station JRG2, asset freshness, budgets, atlas layout.

Unit tests run without raw data; output tests read the generated files of the last build_world.py run."""

from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pytest

from conftest import REGION_DIR, REGION_ID, REPO

OVERRIDE = "andersa-jrg2-fire-station-hero"
ASSET = "fire_station_jrg2"
LANDMARK = REPO / "art-source" / "world" / "landmarks" / ASSET


def _override():
    from roads import pipeline
    return next(o for o in pipeline.load_overrides(REGION_ID) if o.get("id") == OVERRIDE)


def _rings(buildings_fc):
    from roads import pipeline
    reg = pipeline.load_region(REGION_ID)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    return {f["id"]: [[x - ox, y - oy] for x, y in f["geometry"]["coordinates"][0][0]] for f in buildings_fc["features"]}


def _qa():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json missing: run roads/build_world.py")
    return json.loads(p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------ units
def test_override_targets_fire_station_buildings(buildings_fc):
    o = _override()
    assert o["kind"] == "hero_building" and o["asset"] == ASSET and o["osm_way"] == 211035271
    by_id = {f["id"]: f["properties"] for f in buildings_fc["features"]}
    assert all(b in by_id for b in o["buildings"])
    assert by_id[o["buildings"][0]]["function"] == "straż pożarna"


def test_spec_is_deterministic_and_follows_the_ground(buildings_fc):
    from streetscape import hero_building as HB
    o, rings = _override(), _rings(buildings_fc)

    def slope(e, n):
        return 131.0 + 0.01 * e

    a = HB.build_spec(REGION_ID, o, rings, slope)
    b = HB.build_spec(REGION_ID, o, rings, slope)
    assert HB._sha(a) == HB._sha(b)
    dims = a["dims"]
    assert a["anchor"][:2] == [round(v, 3) for v in dims["axis"]["origin_en"]]
    # floor = median ground under the main footprint + the authored offset
    zs = [slope(x, y) for x, y in rings[o["buildings"][0]]]
    assert a["anchor"][2] == pytest.approx(float(np.median(zs)) + dims["floor_above_ground_m"], abs=2e-3)
    bay = dims["fence"]["bay"]
    for ln in a["ground"]["fence"]:
        for p, q in zip(ln[:-1], ln[1:]):
            assert 0.2 < math.hypot(q[0] - p[0], q[1] - p[1]) <= bay + 1e-3
            assert p[2] == pytest.approx(slope(p[0], p[1]), abs=2e-3)
    assert len(a["ground"]["thuja"]) == dims["thuja"]["count"]
    hs = [t[3] for t in a["ground"]["thuja"]]
    assert min(hs) >= dims["thuja"]["h"][0] and max(hs) <= dims["thuja"]["h"][1] and len(set(hs)) > 10
    # a different ground gives a different spec (the asset must be rebuilt)
    assert HB._sha(HB.build_spec(REGION_ID, o, rings, lambda e, n: 130.0)) != HB._sha(a)


def test_dims_fit_the_bdot_footprint(buildings_fc):
    """The authored blocks (garage, wing, hall) cover the BDOT footprint of the main building within 1.5 m."""
    import shapely
    o, rings = _override(), _rings(buildings_fc)
    d = json.loads((LANDMARK / "dims.json").read_text(encoding="utf-8"))
    A = np.array(d["axis"]["origin_en"])
    U = np.array(d["axis"]["u"])
    U = U / np.hypot(*U)
    V = np.array([-U[1], U[0]])

    def rect(u, v):
        return shapely.Polygon([A + U * a + V * b for a, b in ((u[0], v[0]), (u[1], v[0]), (u[1], v[1]), (u[0], v[1]))])
    m = d["middle"]
    blocks = shapely.union_all([rect(d["garage"]["u"], d["garage"]["v"]), rect(m["u"], [m["v_sw"], m["v_ne"]]),
                                rect(d["hall"]["u"], d["hall"]["v"])]).buffer(0.05).buffer(-0.05)      # dissolve the shared edges
    foot = shapely.Polygon(rings[o["buildings"][0]])
    assert blocks.symmetric_difference(foot).area < 0.08 * foot.area
    assert shapely.hausdorff_distance(blocks.exterior, foot.exterior, densify=0.02) < 2.0
    out = shapely.Polygon([A + U * a + V * b for a, b in d["outbuilding"]["ring_uv"]])
    assert out.symmetric_difference(shapely.Polygon(rings[o["buildings"][1]])).area < 0.05 * out.area


def test_atlas_layout_rects_inside_tile_and_disjoint():
    lay = json.loads((LANDMARK / "atlas_layout.json").read_text(encoding="utf-8"))["atlas"]
    W, H = lay["tile_m"]
    rects = {k: (v["u"][0], v["v"][0], v["u"][1], v["v"][1]) for k, v in lay.items() if isinstance(v, dict) and "u" in v}
    for k in ("plaster", "roof", "fascia", "plinth"):
        rects[k] = (0.0, lay[k]["v0"], W, lay[k]["v0"] + lay[k]["h"])
    for k, (u0, v0, u1, v1) in rects.items():
        assert 0 <= u0 < u1 <= W and 0 <= v0 < v1 <= H, k
    keys = sorted(rects)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            ra, rb = rects[a], rects[b]
            overlap = min(ra[2], rb[2]) - max(ra[0], rb[0]) > 1e-6 and min(ra[3], rb[3]) - max(ra[1], rb[1]) > 1e-6
            assert not overlap, (a, b)
    for k in ("plaster", "roof"):
        m0, m1 = lay[k]["mid"]
        assert 0 < m0 < m1 < lay[k]["h"]


def test_materials_registered():
    from streetscape import materials as MT
    assert MT.M["fire_station"]["texture_set"] == "fire_station"
    assert MT.M["fire_station_alpha"]["alpha_cutoff"] == 0.5 and MT.M["fire_station_alpha"]["texture"] == "fire_station_alpha"
    spec = json.loads((REPO / "art-source" / "world" / "materials" / "materials_spec.json").read_text(encoding="utf-8"))
    s = spec["sets"]["fire_station"]
    assert s["tile_m"] == [14.0, 14.0] and "polyhaven" in s["source"]
    assert (REPO / "art-source" / "world" / "textures" / "fire_station_alpha.png").exists()


def test_instance_lod_policy():
    from roads import build_world as BW
    assert BW.instance_ends("landmark_fire_station_jrg2", 3)[0] == [150.0, 450.0, 20000.0]


def test_hero_landmark_mechanism_is_shared():
    """One table per mechanism for every hero asset (ADR 0067 viaduct + ADR 0070 fire station): LOD ends, atlas flag."""
    from roads import build_world as BW
    assert BW.instance_ends("landmark_viaduct_biezenstwa_0", 3)[0] == [90.0, 300.0, 20000.0]
    assert BW.instance_ends("landmark_chimney", 2)[0] == [650.0, 20000.0]
    cs = (REPO / "game/Assets/_Project/World/Import/InstanceImporter.cs").read_text(encoding="utf-8")
    for prefix, ends in BW.HERO_LOD_ENDS.items():      # mirror in InstanceImporter.Policy
        assert f'proto.StartsWith("{prefix}")) e = new[] {{ {ends[0]:.0f}f, {ends[1]:.0f}f, {ends[2]:.0f}f }}' in cs, prefix
    spec = json.loads((REPO / "art-source" / "world" / "materials" / "materials_spec.json").read_text(encoding="utf-8"))
    assert spec["sets"]["fire_station"].get("atlas") is True and spec["sets"]["viaduct_concrete"].get("atlas") is True
    pbr = (REPO / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf-8")
    assert pbr.count('SetVector("_Tile"') == 1      # set_tile || atlas, one place


def test_fence_cut_covers_the_authored_fence_and_opening(buildings_fc):
    import shapely
    from streetscape import hero_building as HB
    o, rings = _override(), _rings(buildings_fc)
    spec = HB.build_spec(REGION_ID, o, rings, lambda e, n: 131.0)
    cut = shapely.union_all(HB.fence_cut([{"spec": spec}]))
    g = spec["ground"]
    for ln in g["fence"] + [g["gate"]]:
        assert shapely.LineString([p[:2] for p in ln]).within(cut.buffer(0.05))
    # continuous along the street front: lines + gate opening leave no gap for the generic fence
    a, b = g["fence"][0][0][:2], g["fence"][-1][-1][:2]
    front = shapely.LineString([a, b])
    assert front.difference(cut.buffer(0.3)).length < 0.5



# ------------------------------------------------------------------------------------------ outputs
def test_asset_matches_spec_and_budget():
    from streetscape import hero_building as HB
    sp = HB.spec_path(REGION_ID, ASSET)
    _, glb, meta_p = HB.asset_paths(ASSET)
    if not (sp.exists() and glb.exists() and meta_p.exists()):
        pytest.skip("asset or spec missing: run roads/build_world.py with Blender")
    spec = json.loads(sp.read_text(encoding="utf-8"))
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    assert meta["spec_sha256"] == HB._sha(spec), "asset built from another spec: rebuild with make_fire_station.py"
    assert meta["glb_sha256"] == hashlib.sha256(glb.read_bytes()).hexdigest()
    t = meta["tris"]
    assert t[0] <= 15000 and t[1] <= 0.5 * t[0] and t[2] <= 400, t
    assert meta["prototype"] == "landmark_fire_station_jrg2"
    assert set(meta["materials"]) == {"fire_station", "fire_station_alpha", "fire_station_thuja_shell"}
    assert t[1] <= 2828, "r7 must retain the original Low geometry budget"


def test_world_uses_the_asset():
    qa = _qa()
    hb = qa.get("hero_buildings")
    if hb is None:
        pytest.skip("streetscape_qa.json predates hero buildings: run roads/build_world.py")
    assert hb["stale"] == [], hb["stale"]
    ap = [a for a in hb["applied"] if a["id"] == OVERRIDE]
    assert len(ap) == 1 and ap[0]["prototype"] == "landmark_fire_station_jrg2"
    assert ap[0]["fence_collision_boxes"] > 20
    assert qa["buildings"]["typologies"].get("hero_asset") == 2
    cams = json.loads((REGION_DIR / "generated" / "control_cameras.json").read_text(encoding="utf-8"))["cameras"]
    ids = {c["id"] for c in cams}
    assert {"fire_station_route", "fire_station_abeam", "fire_station_ref7197", "fire_station_above"} <= ids
    cam = next(c for c in cams if c["id"] == "fire_station_abeam")
    a = ap[0]["anchor"]
    assert 30 < math.hypot(cam["pos"][0] - a[0], cam["pos"][1] - a[1]) < 90      # the route passes ~52 m from the facade
