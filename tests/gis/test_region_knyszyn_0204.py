"""ADR 0204: regions knyszyn / knyszyn-s (lattice tiles (-8,8) and (-8,7) of the ADR 0203 plan).

Checks the things that broke on the first run of a region outside Białystok: the tile lattice and seam points,
the per-region graph filter (house driveways), the route via point (DK65 to the roundabout, not the shortest
street), the DK65 width override, a powiat whose BDOT10k archive lacks a class file, unlit rural roads."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGIONS = REPO / "Data" / "Regions"


def _graph(region_id):
    p = REGIONS / region_id / "roads.graph.json"
    if not p.exists():
        pytest.skip(f"{p} missing: run build_region.py")
    return json.loads(p.read_text(encoding="utf-8"))


def test_tiles_on_the_adr0203_lattice():
    import regions
    c = regions.get("bialystok-industrial-c")
    for rid, (i, j) in {"knyszyn": (-8, 8), "knyszyn-s": (-8, 7)}.items():
        r = regions.get(rid)
        assert r.bbox == (c.bbox[0] + 2048 * i, c.bbox[1] + 2048 * j, c.bbox[0] + 2048 * (i + 1), c.bbox[1] + 2048 * (j + 1))
        assert r.origin == ((r.bbox[0] + r.bbox[2]) / 2, (r.bbox[1] + r.bbox[3]) / 2)
        assert r.teryt_powiat == "2008"


def test_osm_extract_bbox_covers_knyszyn():
    import osm_extract
    from pyproj import Transformer
    import regions
    t = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = osm_extract.BBOX_WGS84
    for rid in ("knyszyn", "knyszyn-s", "bialystok-industrial-c", "bialystok-dojlidy"):
        b = regions.get(rid).bbox
        for x, y in ((b[0], b[1]), (b[2], b[3])):
            lon, lat = t.transform(x, y)
            assert x0 < lon < x1 and y0 < lat < y1, rid


def test_seam_between_the_two_tiles_is_one_point():
    """DK65 leaves knyszyn-s through its north edge exactly where it enters knyszyn (ADR 0203 seam 760986, 611583)."""
    ends = []
    for rid in ("knyszyn", "knyszyn-s"):
        g = _graph(rid)
        prim = {e["from"] for e in g["edges"] if e["attrs"]["highway"]["v"] == "primary"} | \
               {e["to"] for e in g["edges"] if e["attrs"]["highway"]["v"] == "primary"}
        on_edge = [n for n in g["nodes"] if n["id"] in prim and abs(n["y"] - 611583.0) < 0.01]
        assert len(on_edge) == 1, rid
        ends.append(on_edge[0])
    assert math.hypot(ends[0]["x"] - ends[1]["x"], ends[0]["y"] - ends[1]["y"]) < 0.05
    assert abs(ends[0]["x"] - 760986.0) < 1.0


@pytest.mark.parametrize("region_id", ["knyszyn", "knyszyn-s"])
def test_graph_filter_drops_driveways(region_id):
    gf = json.loads((REGIONS / region_id / "graph_filter.authored.json").read_text(encoding="utf-8"))
    assert gf["drop_service"] == ["driveway"]
    g = _graph(region_id)
    assert not [e["id"] for e in g["edges"] if e["attrs"].get("service", {}).get("v") == "driveway"]


def test_graph_filter_is_per_region():
    """Regions without the authored filter keep their driveways (region C output must not change)."""
    assert not (REGIONS / "bialystok-industrial-c" / "graph_filter.authored.json").exists()
    g = _graph("bialystok-industrial-c")
    assert any(e["attrs"].get("service", {}).get("v") == "driveway" for e in g["edges"])


def test_route_follows_dk65_to_the_roundabout():
    p = REGIONS / "knyszyn" / "route_start.json"
    if not p.exists():
        pytest.skip("route_start.json missing: run scripts/export-route.py")
    route = json.loads(p.read_text(encoding="utf-8"))
    g = _graph("knyszyn")
    edges = {e["id"]: e for e in g["edges"]}
    on = [edges[e] for e in dict.fromkeys(route["edge"]) if e in edges]
    names = [e["attrs"].get("name", {}).get("v") for e in on]
    assert "Południowa" not in names                       # the shortest path, not the truck route
    assert any(e["attrs"].get("junction", {}).get("v") == "roundabout" for e in on)
    assert "Obozowa" in names and "Tykocka" in names


@pytest.mark.parametrize("region_id", ["knyszyn", "knyszyn-s"])
def test_dk65_width_measured(region_id):
    q = REGIONS / region_id / "generated" / "roads_qa.json"
    if not q.exists():
        pytest.skip("roads_qa.json missing: run roads/build_world.py")
    from roads import pipeline
    net, graph, overrides, _ = pipeline.build_network(region_id)
    assert "dk65-carriageway-width" not in net.overrides_stale
    secs = [s for s in net.sec_list if s.highway == "primary" and not s.oneway]
    assert secs
    for s in secs:
        assert s.lanes == 2 and abs(s.width - 7.5) < 1e-6, (s.edge_id, s.width)


def test_missing_bdot_class_file_is_an_empty_layer():
    import zipfile
    from streetscape import sources as SS
    z = REPO / "Data/raw/gugik/bdot10k-2008/2008_GPKG.zip"
    if not z.exists():
        pytest.skip("BDOT10k 2008 not ingested")
    with zipfile.ZipFile(z) as zf:
        assert not any("__OT_OIKM_L.gpkg" in n for n in zf.namelist())
    src = json.loads((REGIONS / "knyszyn" / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
    assert src["bdot10k"]["OT_OIKM_L"] == []
    assert "OT_OIKM_L" in SS.BDOT_LAYERS


def test_rural_tile_has_no_rule_lamps():
    q = REGIONS / "knyszyn-s" / "generated" / "streetscape_qa.json"
    if not q.exists():
        pytest.skip("streetscape_qa.json missing: run roads/build_world.py")
    txt = q.read_text(encoding="utf-8")
    rep = json.loads(txt)

    def find(o, key):
        if isinstance(o, dict):
            if key in o and isinstance(o[key], dict) and "rule" in o[key]:
                return o[key]
            for v in o.values():
                r = find(v, key)
                if r is not None:
                    return r
        return None
    lamps = find(rep, "lamps")
    assert lamps is not None and lamps["rule"] == 0 and lamps["osm"] == 0


@pytest.mark.parametrize("region_id,place_ids", [
    ("knyszyn", ["rynek_fountain", "rondo_dk65_from_south", "dk65_inlet_south", "dk65_outlet_nw"]),
    ("knyszyn-s", ["construction_from_dk65", "dk65_seam_east", "dk65_seam_north"]),
])
def test_control_cameras(region_id, place_ids):
    p = REGIONS / region_id / "generated" / "control_cameras.json"
    if not p.exists():
        pytest.skip("control_cameras.json missing: run roads/build_world.py")
    ids = [c["id"] for c in json.loads(p.read_text(encoding="utf-8"))["cameras"]]
    assert len(ids) == len(set(ids))
    for i in place_ids:
        assert i in ids, i
    assert sum(1 for i in ids if i.startswith("route_s")) >= 3
