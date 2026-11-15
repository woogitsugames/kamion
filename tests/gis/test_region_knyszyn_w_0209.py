"""ADR 0209: region knyszyn-w (lattice tile (-9,8) of the ADR 0203 plan, west of `knyszyn`).

Seam with `knyszyn` (x = 760587): the same roads cross on both sides at the same points, DK65 keeps the measured
cross-section, the terrain columns are identical (authored NMT year pin). Plus the route, the cameras and the
unlit rural DK65."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGIONS = REPO / "Data" / "Regions"
SEAM_X = 760587.0


def _graph(region_id):
    p = REGIONS / region_id / "roads.graph.json"
    if not p.exists():
        pytest.skip(f"{p} missing: run build_region.py")
    return json.loads(p.read_text(encoding="utf-8"))


def _seam_crossings(region_id):
    g = _graph(region_id)
    nodes = {n["id"]: n for n in g["nodes"]}
    out = {}
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if abs(n["x"] - SEAM_X) < 0.01:
                out.setdefault(e["osm_way"], []).append((round(n["y"], 1), e))
    return out


def test_tile_on_the_adr0203_lattice():
    import regions
    c = regions.get("bialystok-industrial-c")
    r = regions.get("knyszyn-w")
    i, j = -9, 8
    assert r.bbox == (c.bbox[0] + 2048 * i, c.bbox[1] + 2048 * j, c.bbox[0] + 2048 * (i + 1), c.bbox[1] + 2048 * (j + 1))
    assert r.origin == ((r.bbox[0] + r.bbox[2]) / 2, (r.bbox[1] + r.bbox[3]) / 2)
    assert r.teryt_powiat == "2008"
    assert r.bbox[2] == regions.get("knyszyn").bbox[0]


def test_same_roads_cross_the_seam_at_the_same_points():
    w, k = _seam_crossings("knyszyn-w"), _seam_crossings("knyszyn")
    assert set(w) == set(k)
    assert len(w) >= 10
    for way in w:
        yw = sorted({y for y, _ in w[way]})
        yk = sorted({y for y, _ in k[way]})
        assert yw == yk, way
        aw, ak = w[way][0][1]["attrs"], k[way][0][1]["attrs"]
        for key in ("highway", "lanes", "oneway"):
            assert aw.get(key, {}).get("v") == ak.get(key, {}).get("v"), (way, key)


def _dk65_override(region_id):
    ov = yaml.safe_load((REGIONS / region_id / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    return next(o for o in ov if o["id"] == "dk65-carriageway-width")


def test_dk65_cross_section_same_on_both_sides():
    w, k = _dk65_override("knyszyn-w"), _dk65_override("knyszyn")
    assert w["set"] == k["set"] == {"lanes": 2, "lane_width": 3.4, "edge_strip": 0.35}
    assert 232511646 in w["target"]["osm_way"] and 232511646 in k["target"]["osm_way"]


def test_terrain_seam_columns_identical():
    import regions
    assert regions.source_pins("knyszyn-w") == {"nmt_year": "2022"}
    assert regions.source_pins("bialystok-industrial-c") == {}
    cols = []
    for rid, col in (("knyszyn-w", -1), ("knyszyn", 0)):
        t = json.loads((REGIONS / rid / "terrain.json").read_text(encoding="utf-8"))
        assert t["source_manifest"] == f"gugik-nmt-2022-{rid}"
        f = REPO / t["encoding"]["file"]
        if not f.exists():
            pytest.skip(f"{f} missing (not in git): run build_region.py")
        a = np.fromfile(f, "<u2").reshape(2049, 2049).astype(float)
        cols.append(t["encoding"]["offset_m"] + a[:, col] * t["encoding"]["scale_m_per_unit"])
    assert np.abs(cols[0] - cols[1]).max() < 0.002


def test_route_on_dk65_from_the_seam_to_the_north_edge():
    p = REGIONS / "knyszyn-w" / "route_start.json"
    if not p.exists():
        pytest.skip("route_start.json missing: run scripts/export-route.py")
    route = json.loads(p.read_text(encoding="utf-8"))
    g = _graph("knyszyn-w")
    edges = {e["id"]: e for e in g["edges"]}
    ways = {edges[e]["osm_way"] for e in route["edge"] if e in edges}
    assert ways == {232511646, 232511647}
    o = yaml.safe_load((REGIONS / "knyszyn-w" / "region.yaml").read_text(encoding="utf-8"))["origin"]
    (e0, n0), (e1, n1) = route["points_en"][0][:2], route["points_en"][-1][:2]
    assert math.hypot(e0 + o["x"] - SEAM_X, n0 + o["y"] - 612073.7) < 2.0
    assert abs(n1 + o["y"] - 613631.0) < 2.0


def test_control_cameras():
    p = REGIONS / "knyszyn-w" / "generated" / "control_cameras.json"
    if not p.exists():
        pytest.skip("control_cameras.json missing: run roads/build_world.py")
    ids = [c["id"] for c in json.loads(p.read_text(encoding="utf-8"))["cameras"]]
    assert len(ids) == len(set(ids))
    for i in ("dk65_seam_east_out", "dk65_goniadzka", "dk65_fields_nw", "goniadzka_above", "tykocka_dw671_out"):
        assert i in ids, i
    assert sum(1 for i in ids if i.startswith("route_s")) >= 3


def test_dk65_width_applied_and_no_stale_overrides():
    from roads import pipeline
    net, graph, overrides, _ = pipeline.build_network("knyszyn-w")
    assert not net.overrides_stale
    secs = [s for s in net.sec_list if s.highway == "primary"]
    assert secs and all(s.lanes == 2 and abs(s.width - 7.5) < 1e-6 for s in secs)
