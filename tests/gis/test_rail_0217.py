"""ADR 0217: railway track bed + level crossings - opt-in per region, synthetic OSM data only (no Data/raw)."""

from __future__ import annotations

import json

import numpy as np
import pytest
import shapely
import yaml
from shapely.geometry import LineString

from conftest import REPO

REGIONS_DIR = REPO / "Data" / "Regions"
ENABLED = ["dw671-tykocin-01"]          # rail-fix-s21: line 38 + the DW671 level crossing
FORBIDDEN = ("knyszyn", "knyszyn-s", "knyszyn-w", "bialystok-knyszynska", "dk65-06", "dk65-07", "dk65-08",
             "dk65-09", "dk65-10", "dk65-11")


# ------------------------------------------------------------------------------------------------ opt-in / regression
def test_stage_is_opt_in_and_off_everywhere():
    import regions
    from streetscape import rail as RL
    on = sorted(r.id for r in regions.REGIONS.values() if r.rail)
    assert on == ENABLED                               # ADR 0217: the stage is on only where the lead enabled it
    assert not any(r.rail for r in regions.REGIONS.values() if r.id in FORBIDDEN)
    for rid in sorted(regions.REGIONS):
        d = REGIONS_DIR / rid
        if not (d / "region.yaml").exists():
            continue
        ry = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
        if rid in ENABLED:
            assert RL.enabled(ry) and (d / "generated" / "rail_sources.json").exists()
            man = json.loads((d / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
            assert set(RL.RAIL_MATERIALS) <= set(man["materials"]) and man["rail"]["crossings"] >= 1
            assert all(k in man["nodes"] for k in RL.LAYERS)
            continue
        assert "rail" not in ry and not RL.enabled(ry)
        assert not (d / "generated" / "rail_sources.json").exists()
        assert not (d / "generated" / "rail.json").exists()
        mp = d / "generated" / "world_manifest.json"
        if mp.exists():
            man = json.loads(mp.read_text(encoding="utf-8"))
            assert not any(k.startswith("rail") for k in man.get("materials", {}))
            assert not any(k.startswith("rail") for k in man.get("nodes", {}))
            assert "rail" not in man


def test_stage_hooks_guarded():
    """Without a plan (w.rail is None) build_world / stage add nothing: every rail hook is behind the guard."""
    bw = (REPO / "tools" / "worldgen" / "roads" / "build_world.py").read_text(encoding="utf-8")
    assert "if RL.enabled(w.region):" in bw
    assert bw.count("if w.rail is not None:") == 3          # build the meshes; rail_bed.png; manifest + rail.json
    assert "if w.rail is not None and w.rail.lod_mask() is not None:" in bw
    assert 'manifest["materials"] = {**manifest["materials"], **RL.RAIL_MATERIALS}' in bw
    st = (REPO / "tools" / "worldgen" / "streetscape" / "stage.py").read_text(encoding="utf-8")
    assert st.count('getattr(w, "rail", None) is not None') == 3      # terrain conform; crossing devices; no trees
    pr = (REPO / "tools" / "worldgen" / "streetscape" / "props.py").read_text(encoding="utf-8")
    assert "P.update(RP.prototypes())" in pr                 # registered prototypes only (empty without the stage)
    br = (REPO / "tools" / "worldgen" / "build_region.py").read_text(encoding="utf-8")
    assert 'if getattr(region, "rail", False):' in br


def test_layers_empty_without_plan_change_nothing():
    """The rail layers / nodes exist in build_world, but with no parts the chunk GLBs and manifest are unchanged."""
    from roads import build_world as BW
    from roads.meshing import MeshBuf
    for layer in ("rail_lod0", "rail_lod1", "rail_lod2", "rail_crossing"):
        assert layer in BW.LAYERS
    assert BW.assemble(MeshBuf().parts, BW.LAYERS, 1024.0) == {}
    assert not any(k.startswith("rail") for k in BW.MATERIALS)      # only added to the manifest by the rail stage


# ------------------------------------------------------------------------------------------------ tags
def test_classify_way():
    from streetscape import rail as RL
    ok, _, a = RL.classify_way({"railway": "rail"})
    assert ok and a["gauge_mm"] == 1435.0 and a["gauge_src"] == "default" and a["tracks"] == 1
    ok, _, a = RL.classify_way({"railway": "rail", "gauge": "1520", "tracks": "2", "usage": "main"})
    assert ok and a["gauge_mm"] == 1520.0 and a["tracks"] == 2 and a["usage"] == "main"
    ok, _, a = RL.classify_way({"railway": "rail", "gauge": "1435;1520", "service": "siding"})
    assert ok and a["gauge_mm"] == 1435.0 and a["service"] == "siding"
    for t in ({"railway": "disused"}, {"railway": "abandoned"}, {"railway": "construction"},
              {"railway": "rail", "disused": "yes"}, {"railway": "rail", "tunnel": "yes"}):
        ok, why, _ = RL.classify_way(t)
        assert not ok and why


def test_classify_node():
    from streetscape import rail as RL
    ok, _, a = RL.classify_node({"railway": "level_crossing", "crossing:barrier": "half", "crossing:light": "yes",
                                 "crossing:bell": "yes"})
    assert ok and a["barrier"] == "half" and a["light"] and a["bell"]
    ok, why, _ = RL.classify_node({"railway": "crossing"})
    assert not ok and "pedestrian" in why
    ok, _, a = RL.classify_node({"railway": "level_crossing", "crossing:barrier": "weird"})
    assert ok and a["barrier"] is None


# ------------------------------------------------------------------------------------------------ synthetic scene
GROUND = 100.0
ROAD_Z = 100.8          # road on a small embankment: the rail profile must climb to it at the crossing


def ground_at(e, n):
    return np.full(np.shape(e), GROUND) + 0.0 * np.asarray(n)


def road_z_at(e, n):
    """Road along N (x = 500) with a 2 % cross-fall to the east: panel heights must follow it."""
    return ROAD_Z - 0.02 * (np.asarray(e, float) - 500.0) + 0.0 * np.asarray(n)


def _src(tracks=1, barrier=None, light=False, bell=False, node=True, extra_ways=()):
    ways = [{"osm_way": 10, "part": 0, "tags": {"railway": "rail", **({"tracks": str(tracks)} if tracks > 1 else {})},
             "coords": [[0.0, 500.0], [1000.0, 500.0]]}]
    ways += list(extra_ways)
    nodes = []
    if node:
        tags = {"railway": "level_crossing"}
        if barrier:
            tags["crossing:barrier"] = barrier
        if light:
            tags["crossing:light"] = "yes"
        if bell:
            tags["crossing:bell"] = "yes"
        nodes.append({"osm_node": 1, "tags": tags, "xy": [500.0, 500.0]})
    nodes.append({"osm_node": 2, "tags": {"railway": "crossing"}, "xy": [800.0, 500.0]})
    return {"osm": {"ways": ways, "nodes": nodes}}


def _plan(**kw):
    from roads.meshing import MeshBuf
    from streetscape import rail as RL
    road_line = LineString([(500.0, 0.0), (500.0, 1000.0)])
    road_poly = road_line.buffer(3.5, cap_style=2)                  # 7 m carriageway
    p = RL.Plan(_src(**kw), (0.0, 0.0), shapely.box(0, 0, 1000, 1000), road_poly, [road_line])
    buf = MeshBuf()
    p.build(buf, ground_at, road_z_at, log=lambda *a: None)
    return p, buf


def _ntris(buf, layer):
    return sum(len(q.T) for q in buf.parts if q.layer == layer)


def test_triangles_per_lod_match_formula():
    from streetscape import rail as RL
    p, buf = _plan(node=False)       # no OSM node: the road x rail intersection is still found (geometry)
    assert len(p.crossings) == 1 and p.crossings[0]["source"] == "geometry"
    # plain 1 km single track without the crossing: compare with a plan without road
    from roads.meshing import MeshBuf
    q = RL.Plan(_src(node=False), (0.0, 0.0), shapely.box(0, 0, 1000, 1000))
    b2 = MeshBuf()
    q.build(b2, ground_at, road_z_at, log=lambda *a: None)
    assert not q.crossings
    t0, t1, t2 = (_ntris(b2, f"rail_lod{k}") for k in (0, 1, 2))
    # 1000 m: 200 / 100 / 50 segments; 1667 sleepers (0.3, 0.9, ... 999.9 m)
    assert t1 == RL.tri_per_km(1) == 1800
    assert t2 == RL.tri_per_km(2) == 100
    assert t0 == 200 * 18 + 1667 * 6
    assert abs(t0 - RL.tri_per_km(0)) <= 6
    assert t0 > t1 > t2
    # double track: rails and sleepers double; the bed has one top strip per track (own sleepers / rails in the tile)
    q2 = RL.Plan(_src(tracks=2, node=False), (0.0, 0.0), shapely.box(0, 0, 1000, 1000))
    b3 = MeshBuf()
    q2.build(b3, ground_at, road_z_at, log=lambda *a: None)
    assert _ntris(b3, "rail_lod1") == RL.tri_per_km(1, tracks=2) == 3200
    assert _ntris(b3, "rail_lod2") == RL.tri_per_km(2, tracks=2) == 200


def test_geometry_dimensions():
    from streetscape import rail as RL
    p, buf = _plan(node=False)
    rails = [q for q in buf.parts if q.layer == "rail_lod1" and q.src.endswith(":rail")]
    assert len(rails) == 2
    # far from the crossing: top of rail = ground + TRACK_H, gauge between inner head edges = 1.435 m
    V = np.concatenate([q.V for q in rails])
    far = V[:, 0] < 300
    assert np.allclose(V[far, 2].max(), GROUND + RL.TRACK_H)
    ys = np.unique(np.round(V[far, 1], 4))
    inner = sorted(ys)[1:3]
    assert abs((inner[1] - inner[0]) - 1.435) < 1e-3
    # ballast is a trapezoid: top narrower than the toe, slope 1:1.5
    bal = np.concatenate([q.V for q in buf.parts if q.layer == "rail_lod0" and q.src.endswith(":ballast")])
    Vb = bal[bal[:, 0] < 300]
    top = Vb[np.isclose(Vb[:, 2], Vb[:, 2].max())]
    low = Vb[np.isclose(Vb[:, 2], Vb[:, 2].min())]
    wt = np.ptp(top[:, 1])
    wl = np.ptp(low[:, 1])
    assert abs(wt - 2 * (RL.SLEEPER_L / 2 + RL.BALLAST_SHOULDER)) < 1e-6
    dz = Vb[:, 2].max() - Vb[:, 2].min()
    assert abs((wl - wt) / 2 - dz * RL.BALLAST_SLOPE) < 1e-6
    # FIX 5: the ballast top is BED_LIFT over the (conformed) ground, the skirt ends below it
    assert abs(Vb[:, 2].max() - (GROUND + RL.BED_LIFT)) < 1e-9 and Vb[:, 2].min() < GROUND
    assert 3.5 <= wt + 2 * RL.BED_LIFT * RL.BALLAST_SLOPE <= 4.5          # visible band = orthophoto 3.5-4.5 m
    # every face of the bed and the rails is CCW seen from outside: top faces point up
    for q in buf.parts:
        if q.src.endswith(":ballast") or q.mat == "rail_crossing_panel":
            a, b, c = q.V[q.T[:, 0]], q.V[q.T[:, 1]], q.V[q.T[:, 2]]
            assert np.all(np.cross(b - a, c - a)[:, 2] > 0)


def test_panels_at_road_height_and_rails_flush():
    from streetscape import rail as RL
    p, buf = _plan(barrier=None)
    panels = [q for q in buf.parts if q.layer == "rail_crossing"]
    assert panels and all(q.mat == "rail_crossing_panel" for q in panels)
    V = np.concatenate([q.V for q in panels])
    assert np.allclose(V[:, 2], road_z_at(V[:, 0], V[:, 1]) + RL.PANEL_LIFT)
    # panels span the road (7 m) + margins along the track, the sleeper length across it
    assert np.ptp(V[:, 0]) >= 7.0 + 2 * RL.PANEL_MARGIN - 1e-6
    assert abs(np.ptp(V[:, 1]) - RL.SLEEPER_L) < 1e-6
    assert _ntris(buf, "rail_crossing") == RL.tri_per_crossing(7.0, 1)
    # rail heads inside the panel zone are flush with the panels
    R = np.concatenate([q.V for q in buf.parts if q.layer == "rail_lod0" and q.src.endswith(":rail")])
    inz = (np.abs(R[:, 0] - 500) < 3.0)
    heads = R[inz][np.isclose(R[inz][:, 2], road_z_at(R[inz][:, 0], R[inz][:, 1]) + RL.PANEL_LIFT)]
    assert len(heads) > 0
    # no ballast / sleepers under the panels
    for q in buf.parts:
        if q.mat == "rail_bed" and not q.src.endswith(":rail"):
            cen = q.V[q.T].mean(1)
            assert not np.any(np.abs(cen[:, 0] - 500) < 3.0)
    # profile climbs smoothly to the road: 0.8 m over the 25 m blend, untouched beyond it
    c = p.report["crossings"][0]
    assert abs(c["z_road"] - ROAD_Z) < 1e-6


@pytest.mark.parametrize("tracks,code", [(1, "G-3"), (2, "G-4")])
def test_sign_g3_vs_g4(tracks, code):
    p, _ = _plan(tracks=tracks, barrier="no")
    signs = [m for m in p.report["markers"] if m["kind"] == "sign"]
    assert len(signs) == 2 and {m["code"] for m in signs} == {code}
    # one per approach, facing the oncoming driver (road along N: headings 180 and 0)
    assert sorted(m["heading_deg"] for m in signs) == [0.0, 180.0]
    # driver's right: approaching northbound (from the south) the post stands east of the road
    north = [m for m in signs if m["heading_deg"] == 180.0][0]
    assert north["n"] < 500 and north["e"] > 503.5
    # nothing stands inside the clearance envelope
    from streetscape import rail as RL
    assert p.report["clearance"]["min_marker_distance_m"] > RL.CLEARANCE_HALF


def test_two_ways_make_g4():
    second = {"osm_way": 11, "part": 0, "tags": {"railway": "rail"}, "coords": [[0.0, 504.0], [1000.0, 504.0]]}
    p, _ = _plan(extra_ways=[second])
    assert p.crossings[0]["n_tracks"] == 2
    assert {m["code"] for m in p.report["markers"] if m["kind"] == "sign"} == {"G-4"}


@pytest.mark.parametrize("barrier,n_booms,sign", [("no", 0, True), (None, 0, True), ("half", 2, False),
                                                   ("double_half", 4, False), ("full", 2, False)])
def test_barrier_types(barrier, n_booms, sign):
    p, _ = _plan(barrier=barrier)
    booms = [m for m in p.report["markers"] if m["kind"] == "barrier"]
    assert len(booms) == n_booms
    assert any(m["kind"] == "sign" for m in p.report["markers"]) is sign
    if barrier == "half":
        assert all(abs(m["boom_len_m"] - 4.0) < 1e-6 for m in booms)          # half of 7 m + 0.5
    if barrier == "full":
        assert all(abs(m["boom_len_m"] - 7.5) < 1e-6 for m in booms)
    if barrier == "double_half":
        assert sorted(m["role"] for m in booms) == ["entry", "entry", "exit", "exit"]


def test_lights_bell_and_pedestrian_skip():
    p, _ = _plan(barrier="half", light=True, bell=True)
    kinds = [m["kind"] for m in p.report["markers"]]
    assert kinds.count("light") == 2 and kinds.count("bell") == 1
    assert any("pedestrian" in s["why"] for s in p.report["skipped"])
    assert len(p.crossings) == 1                  # OSM node + the road line intersection deduplicated


def test_disused_not_meshed():
    from roads.meshing import MeshBuf
    from streetscape import rail as RL
    src = {"osm": {"ways": [{"osm_way": 5, "part": 0, "tags": {"railway": "abandoned"},
                             "coords": [[0, 0], [100, 0]]}], "nodes": []}}
    p = RL.Plan(src, (0.0, 0.0))
    buf = MeshBuf()
    p.build(buf, ground_at, road_z_at, log=lambda *a: None)
    assert not buf.parts and p.report["skipped"][0]["why"] == "railway=abandoned"


def test_footprint_blocks_vegetation():
    from streetscape import rail as RL
    p, _ = _plan()
    fp = shapely.union_all(p.footprint())
    assert fp.contains(shapely.Point(200, 500 + RL.CLEARANCE_HALF - 0.1))
    assert not fp.contains(shapely.Point(200, 520))


def test_grid_sampler_fills_off_road():
    from streetscape import rail as RL

    class HF:
        x0 = 0.0
        y1 = 9.0
    g = np.full((10, 10), -np.inf)
    g[:, 4:6] = 5.0
    f = RL.grid_sampler(g, HF(), fallback=lambda e, n: np.full(np.shape(e), 1.0))
    assert np.allclose(f(np.array([4.5]), np.array([5.0])), 5.0)
    assert np.allclose(f(np.array([6.5]), np.array([5.0])), 5.0)     # within reach: nearest road node
    assert np.allclose(f(np.array([9.0]), np.array([5.0])), 1.0)     # beyond reach: fallback


# ------------------------------------------------------------------------------------------------ rail-fix-s21
def test_bed_uvs_address_the_tile():
    """FIX 3: every bed vertex maps into the rail_bed tile - u from its own track axis, v = station / tile length;
    LoD0 sleepers lie on the painted ones."""
    from streetscape import rail as RL
    from streetscape import rail_textures as RT
    p, buf = _plan(node=False, tracks=2)
    assert set(RL.RAIL_MATERIALS) == {"rail_bed", "rail_crossing_panel"}       # the whole track = one material
    for q in buf.parts:                                      # rails sample the painted rail: head on top, rust below
        if q.src.endswith(":rail"):
            lat_m = (q.UV[:, 0] - 0.5) * RT.TEX_W_M
            assert np.all(np.abs(np.abs(lat_m) - (1.435 / 2 + 0.036)) <= 0.075)
            top = np.isclose(q.V[:, 2], q.V[:, 2].max())
            assert np.all(np.abs(np.abs(lat_m[top]) - (1.435 / 2 + 0.036)) < 0.036)
    assert RL.RAIL_MATERIALS["rail_bed"]["texture"] == "rail_bed"
    for q in buf.parts:
        if q.mat != "rail_bed":
            continue
        assert q.UV[:, 0].min() >= 0.0 and q.UV[:, 0].max() <= 1.0
    tops = [q for q in buf.parts if q.layer == "rail_lod1" and q.src.endswith(":ballast")]
    assert len(tops) == 4                                    # 2 slopes + one top strip per track
    # the strip of the +2 m track: its axis (y = 502) is u = 0.5
    V = np.concatenate([q.V for q in tops])
    UV = np.concatenate([q.UV for q in tops])
    on_top = np.isclose(V[:, 2], V[:, 2].max())
    k = on_top & (V[:, 1] > 500.5)
    assert np.allclose(UV[k, 0], 0.5 + (V[k, 1] - 502.0) / RT.TEX_W_M)
    assert np.allclose(UV[k, 1], V[k, 0] / RL.TILE_M)
    sl = [q for q in buf.parts if q.src.endswith(":sleepers")][0]
    topv = np.isclose(sl.V[:, 2], sl.V[:, 2].max())
    # sleeper centres at 0.3 + 0.6 k m: v of a top vertex, in sleeper pitches, stays within the painted sleeper
    ph = (sl.UV[topv, 1] * RL.TILE_M / RL.SLEEPER_SPACING) % 1.0
    assert np.all(np.abs(ph - 0.5) <= RL.SLEEPER_W / 2 / RL.SLEEPER_SPACING + 1e-6)


def test_bed_texture():
    from streetscape import rail_textures as RT
    im = RT.bed()
    assert im.size == (RT.W_PX, RT.H_PX) and im.mode == "RGB"
    a = np.asarray(im).astype(float)
    px = RT.TEX_W_M / RT.W_PX
    col = lambda lat: int((lat + RT.TEX_W_M / 2) / px)
    # four sleepers per tile: bright concrete rows on the axis, dark ballast between them
    axis = a[:, col(0.3), :].mean(1)
    rows = (np.arange(RT.H_PX) + 0.5) / RT.H_PX * RT.SLEEPERS_PER_TILE
    on = np.abs(rows % 1.0 - 0.5) < 0.15
    off = np.abs(rows % 1.0 - 0.5) > 0.40
    assert axis[on].mean() > 1.5 * axis[off].mean()
    # ballast: brown (R > G > B) and darker than the game asphalt (road_asphalt 0.081 linear = sRGB 80)
    bal = a[:, col(1.45):col(1.65), :].reshape(-1, 3).mean(0)
    assert bal[0] > bal[1] > bal[2] and bal.mean() < 80
    assert RT.bed().tobytes() == im.tobytes()                # deterministic


def test_override_sets_barriers_and_margin():
    from roads.meshing import MeshBuf
    from streetscape import rail as RL
    road_line = LineString([(500.0, 0.0), (500.0, 1000.0)])
    road_poly = road_line.buffer(3.5, cap_style=2)
    ov = [{"id": "x1", "kind": "rail_crossing", "target": {"osm_node": 1},
           "set": {"barrier": "double_half", "light": True, "light_left": True, "panel_margin_m": 1.5}},
          {"id": "other", "kind": "paved_area"},
          {"id": "lost", "kind": "rail_crossing", "target": {"osm_node": 999}, "set": {"barrier": "full"}}]
    p = RL.Plan(_src(), (0.0, 0.0), shapely.box(0, 0, 1000, 1000), road_poly, [road_line], overrides=ov)
    buf = MeshBuf()
    p.build(buf, ground_at, road_z_at, log=lambda *a: None)
    c = p.report["crossings"][0]
    assert c["barrier"] == "double_half" and c["light"] and c["override"] == "x1" and c["sign"] is None
    kinds = [m["kind"] for m in p.report["markers"]]
    assert kinds.count("barrier") == 4 and kinds.count("light") == 4 and kinds.count("sign") == 0
    assert sorted(m["side"] for m in p.report["markers"] if m["kind"] == "light") == ["left", "left", "right", "right"]
    V = np.concatenate([q.V for q in buf.parts if q.layer == "rail_crossing"])
    assert np.ptp(V[:, 0]) >= 7.0 + 2 * 1.5 - 1e-6           # panels 1.5 m past the road edges
    assert abs(c["road_width_m"] - 7.0) < 1e-6               # ... without widening the road
    assert any("lost" in w["src"] for w in p.report["warnings"])
    assert "_used" not in ov[0]                              # the caller's override list is not modified
    # near_epsg2180 target + unknown key
    p2 = RL.Plan(_src(), (0.0, 0.0), shapely.box(0, 0, 1000, 1000), road_poly, [road_line],
                 overrides=[{"id": "x2", "kind": "rail_crossing", "target": {"near_epsg2180": [503.0, 498.0]},
                             "set": {"barrier": "half"}}])
    assert p2.crossings[0]["barrier"] == "half"
    with pytest.raises(ValueError):
        RL.Plan(_src(), (0.0, 0.0), shapely.box(0, 0, 1000, 1000), road_poly, [road_line],
                overrides=[{"id": "bad", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"booms": 3}}])


def test_tykocin_crossing_override_is_authored():
    ov = yaml.safe_load((REGIONS_DIR / "dw671-tykocin-01" / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    o = [x for x in ov if x.get("kind") == "rail_crossing"]
    assert len(o) == 1 and o[0]["target"] == {"osm_node": 1778182481}
    assert o[0]["set"]["barrier"] == "double_half" and o[0]["set"]["light"] is True
    assert o[0]["confidence"] in ("low", "medium", "high") and any("gugik" in s for s in o[0]["sources"])
    assert not any("google" in str(v).lower() for v in o[0].values() if not isinstance(v, dict)) or "no Google" in str(o[0])
    rj = REGIONS_DIR / "dw671-tykocin-01" / "generated" / "rail.json"
    if rj.exists():
        r = json.loads(rj.read_text(encoding="utf-8"))
        c = r["crossings"][0]
        assert c["override"] == "rail-crossing-dw671-line38" and c["barrier"] == "double_half"
        assert sum(m["kind"] == "barrier" for m in r["markers"]) == 4
        qa = r["bed_qa"]
        assert qa["buried_crown_stations"] == 0 and qa["open_toe_stations"] == 0
        assert 3.5 <= qa["visible_width_m"]["p50"] <= 4.5


class _HF:
    x0 = 0.0
    y1 = 199.0
    z = None


def test_conform_levels_ground_under_the_bed():
    """FIX 5: bumpy ground is levelled to the bed under the crown, blended outside, roads untouched; the bed QA then
    finds neither a buried crown nor an open toe."""
    from scipy import ndimage
    from streetscape import rail as RL
    rng = np.random.default_rng(1)
    zc = 100.0 + 0.4 * ndimage.gaussian_filter(rng.normal(0, 1, (200, 200)), 3) / 0.1
    assert np.ptp(zc) > 0.5
    src = {"osm": {"ways": [{"osm_way": 1, "part": 0, "tags": {"railway": "rail"},
                             "coords": [[10.0, 100.0], [190.0, 100.0]]}], "nodes": []}}
    p = RL.Plan(src, (0.0, 0.0), shapely.box(0, 0, 199, 199))
    keep = np.zeros(zc.shape, bool)
    keep[:, 100:104] = True                                   # a "road" across the track
    hf = _HF()
    road = lambda e, n: np.full(np.shape(e), 100.0)
    out = p.conform(zc, keep, hf, road, log=lambda *a: None)
    assert np.array_equal(out[keep], zc[keep])                # roads / paved nodes never move
    far = np.ones(zc.shape, bool)
    far[int(99 - 8):int(99 + 9), :] = False
    assert np.array_equal(out[far], zc[far])                  # nothing beyond the blend
    ground = RL.grid_sampler(p.ground_grid, hf)
    # under the crown (rows N = 99..101 -> j = 98..100), away from the road: terrain == the bed level, i.e. the
    # smoothed ground on the track axis (the bed is level across the track)
    j, i = np.mgrid[98:101, 20:90]
    assert np.allclose(out[j, i], ground(hf.x0 + i, np.full(i.shape, 100.0)), atol=1e-9)
    assert p.lod_mask()[99, 50] and not p.lod_mask()[99, 101] and not p.lod_mask()[80, 50]
    assert p.report["conform"]["nodes"] > 0
    # QA over the whole length on open ground (the kept "road" strip above is not a crossing of this plan)
    out = p.conform(zc, np.zeros(zc.shape, bool), hf, road, log=lambda *a: None)
    qa = p.bed_qa(RL.grid_sampler(out, hf), ground, road)
    assert qa["buried_crown_stations"] == 0 and qa["open_toe_stations"] == 0
    assert abs(qa["crown_edge_above_terrain_m"]["p50"] - RL.BED_LIFT) < 0.02
    assert 3.5 <= qa["visible_width_m"]["model"] <= 4.5
    # without the conform the same bed is buried by the bumps somewhere: the QA sees it
    qa0 = RL.Plan(src, (0.0, 0.0), shapely.box(0, 0, 199, 199)).bed_qa(RL.grid_sampler(zc, hf), ground, road)
    assert qa0["buried_crown_stations"] > 0


class _Placer:
    def __init__(self):
        self.items = []

    def add(self, proto, p, yaw, z=None, sz=1.0, src="", group=None):
        self.items.append({"p": proto, "e": p[0], "n": p[1], "yaw": yaw, "src": src})


def test_crossing_devices_are_instances():
    """FIX 4: markers -> prototypes + instances (the generator is the spawner); registered only by the rail stage."""
    from streetscape import rail_props as RP
    from streetscape.materials import M
    RP.PROTOS.clear()
    assert RP.prototypes() == {}
    # unprotected single-track crossing: two G-3 crosses, facing the drivers
    p, _ = _plan(barrier="no")
    pl, rep = _Placer(), {}
    assert RP.place(pl, p, road_z_at, rep) == 2
    assert rep["rail_crossing_devices"] == {"rail_saltire_g3": 2} and set(RP.prototypes()) == {"rail_saltire_g3"}
    north = [it for it in pl.items if it["n"] < 500][0]     # northbound driver: the face looks south (yaw: +y -> -N)
    assert abs(np.cos(north["yaw"] + np.pi / 2) - 0.0) < 1e-6 and np.sin(north["yaw"] + np.pi / 2) < -0.99
    lod0, lod1, col = RP.prototypes()["rail_saltire_g3"]
    mats = {q["mat"] for q in lod0.out()}
    assert {"paint_white_reflective", "paint_ral3020"} <= mats and mats <= set(M) and col is not None
    V = np.concatenate([q["V"] for q in lod0.out() if q["mat"] == "paint_white_reflective"])
    assert V[:, 2].min() > 1.50 and np.ptp(V[:, 0]) > 1.0 and np.ptp(V[:, 0]) > np.ptp(V[:, 2])   # wide cross, clear of 1.5 m
    g4 = RP.saltire("G-4")[0]
    g3 = RP.saltire("G-3")[0]
    assert sum(len(q["T"]) for q in g4.out()) > sum(len(q["T"]) for q in g3.out())
    # double half-barriers + lights + bell: 4 raised booms, 2 signals (one with the bell); no cross
    p, _ = _plan(barrier="double_half", light=True, bell=True)
    pl, rep = _Placer(), {}
    RP.place(pl, p, road_z_at, rep)
    assert rep["rail_crossing_devices"] == {"rail_barrier_040": 4, "rail_signal": 1, "rail_signal_bell": 1}
    assert "rail_saltire_g3" not in RP.prototypes()         # the registry holds this region's prototypes only
    boom, _, bcol = RP.prototypes()["rail_barrier_040"]
    Vb = np.concatenate([q["V"] for q in boom.out() if q["mat"] in ("paint_ral3020", "paint_white_reflective")])
    assert Vb[:, 2].max() > RP.BOOM_PIVOT_Z_M + 3.9          # boom raised: the crossing is open, nothing over the lanes
    assert Vb[:, 1].max() < 0.6
    Vc = np.concatenate([q["V"] for q in bcol.out()])
    assert Vc[:, 2].max() <= RP.DRIVE_M[2] + 1e-6            # collision = the drive cabinet only
    assert all(q["mat"] in M for pr in RP.prototypes().values() for q in pr[0].out())
    RP.PROTOS.clear()
