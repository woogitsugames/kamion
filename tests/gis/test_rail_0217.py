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
FORBIDDEN = ("knyszyn", "knyszyn-s", "knyszyn-w", "bialystok-knyszynska", "dk65-06", "dk65-07", "dk65-08",
             "dk65-09", "dk65-10", "dk65-11")
RAIL_ON_0223 = ("dk65-01", "dk65-02", "dk65-03", "dk65-04", "dw671-tykocin-01")


# ------------------------------------------------------------------------------------------------ opt-in / regression
def test_stage_is_opt_in_and_off_everywhere():
    import regions
    from streetscape import rail as RL
    on = sorted(r.id for r in regions.REGIONS.values() if r.rail)
    # ADR 0217 enabled nothing; ADR 0223 enables the line-38 tiles (test_rail_dk65_0223.py checks them)
    assert on == sorted(RAIL_ON_0223)
    assert not any(r.rail for r in regions.REGIONS.values() if r.id in FORBIDDEN)
    for rid in sorted(regions.REGIONS):
        d = REGIONS_DIR / rid
        if not (d / "region.yaml").exists() or rid in RAIL_ON_0223:
            continue
        ry = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
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
    assert bw.count("if w.rail is not None:") == 2          # build the meshes; manifest + rail.json
    assert 'manifest["materials"] = {**manifest["materials"], **RL.RAIL_MATERIALS}' in bw
    st = (REPO / "tools" / "worldgen" / "streetscape" / "stage.py").read_text(encoding="utf-8")
    assert st.count('getattr(w, "rail", None) is not None') == 1
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
    # double track: rails and sleepers double, ballast once
    q2 = RL.Plan(_src(tracks=2, node=False), (0.0, 0.0), shapely.box(0, 0, 1000, 1000))
    b3 = MeshBuf()
    q2.build(b3, ground_at, road_z_at, log=lambda *a: None)
    assert _ntris(b3, "rail_lod1") == RL.tri_per_km(1, tracks=2) == 3000


def test_geometry_dimensions():
    from streetscape import rail as RL
    p, buf = _plan(node=False)
    rails = [q for q in buf.parts if q.layer == "rail_lod1" and q.mat == "rail_steel"]
    assert len(rails) == 2
    # far from the crossing: top of rail = ground + TRACK_H, gauge between inner head edges = 1.435 m
    V = np.concatenate([q.V for q in rails])
    far = V[:, 0] < 300
    assert np.allclose(V[far, 2].max(), GROUND + RL.TRACK_H)
    ys = np.unique(np.round(V[far, 1], 4))
    inner = sorted(ys)[1:3]
    assert abs((inner[1] - inner[0]) - 1.435) < 1e-3
    # ballast is a trapezoid: top narrower than the toe, slope 1:1.5
    bal = [q for q in buf.parts if q.layer == "rail_lod0" and q.mat == "rail_ballast"][0]
    Vb = bal.V[bal.V[:, 0] < 300]
    top = Vb[np.isclose(Vb[:, 2], Vb[:, 2].max())]
    low = Vb[np.isclose(Vb[:, 2], Vb[:, 2].min())]
    wt = np.ptp(top[:, 1])
    wl = np.ptp(low[:, 1])
    assert abs(wt - 2 * (RL.SLEEPER_L / 2 + RL.BALLAST_SHOULDER)) < 1e-6
    dz = Vb[:, 2].max() - Vb[:, 2].min()
    assert abs((wl - wt) / 2 - dz * RL.BALLAST_SLOPE) < 1e-6
    # every face of the bed and the rails is CCW seen from outside: top faces point up
    for q in buf.parts:
        if q.mat in ("rail_ballast", "rail_crossing_panel"):
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
    R = np.concatenate([q.V for q in buf.parts if q.layer == "rail_lod0" and q.mat == "rail_steel"])
    inz = (np.abs(R[:, 0] - 500) < 3.0)
    heads = R[inz][np.isclose(R[inz][:, 2], road_z_at(R[inz][:, 0], R[inz][:, 1]) + RL.PANEL_LIFT)]
    assert len(heads) > 0
    # no ballast / sleepers under the panels
    for q in buf.parts:
        if q.mat in ("rail_ballast", "rail_sleeper"):
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
