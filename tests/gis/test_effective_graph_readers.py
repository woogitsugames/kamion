"""ADR 0274 "Czytniki grafu": every reader of roads.graph.json that walks graph geometry / topology next to the generated
network reads it through roads.pipeline.effective_graph (authored `carriageway_split` applied), the readers that compare
the ingested data with OSM / the orthophoto or only use edge attributes by id keep the ingested graph - and every reader
is classified here, so a new one has to be.

Synthetic 4-arm roundabout (test_compact_roundabout_0218 graph, pure Python) in a temporary region + the Knyszyn data in
git (read only). No Data/raw.
Run: uv run --project tools/worldgen python -m pytest tests/gis/test_effective_graph_readers.py -q
"""
import importlib.util
import json
import math
import re
import struct
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_compact_roundabout_0218 as T18  # noqa: E402
import roadgraph  # noqa: E402
from navgraph import build_route_graph as BRG  # noqa: E402
from roads import carriageway_split as CS  # noqa: E402
from roads import pipeline as PL  # noqa: E402
from validate import common as VC  # noqa: E402

SPLIT_NODE = 7000                    # synthetic OSM id of the present split node (arm 0, +x)
SPLIT = {"id": "syn-split", "kind": "carriageway_split", "node": SPLIT_NODE,
         "set": {"length_m": 25.0, "taper_m": 14.0, "lane_offset_m": 3.0}}
REGION = "syn-split"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NAV = _load("build_nav_map_t", ROOT / "tools" / "ui" / "build_nav_map.py")
MAC = _load("map_audit_cameras_t", ROOT / "scripts" / "map-audit-cameras.py")


def _syn_graph():
    g = T18._graph()
    ren = {"s0": f"n{SPLIT_NODE}"}
    for n in g["nodes"]:
        if n["id"] in ren:
            n["id"] = ren[n["id"]]
            n["osm_node"] = SPLIT_NODE
    for e in g["edges"]:
        e["from"], e["to"] = ren.get(e["from"], e["from"]), ren.get(e["to"], e["to"])
    return g


@pytest.fixture
def region(tmp_path, monkeypatch):
    """A temporary repo root with Data/Regions/syn-split; every reader's REPO / REGIONS points there."""
    rdir = tmp_path / "Data" / "Regions" / REGION
    rdir.mkdir(parents=True)
    (rdir / "roads.graph.json").write_text(json.dumps(_syn_graph()), encoding="utf-8")
    (rdir / "overrides.yaml").write_text(yaml.safe_dump({"overrides": [SPLIT]}), encoding="utf-8")
    (rdir / "region.yaml").write_text("id: syn-split\norigin:\n  x: 0.0\n  y: 0.0\n", encoding="utf-8")
    (rdir / "buildings.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding="utf-8")
    raw = _syn_graph()
    path = [f"n{SPLIT_NODE}", "e0"]        # ingested ids, as scripts/export-route.py writes them
    (rdir / "route_start.json").write_text(json.dumps({
        "points_en": [[60.0, 0.0], [30.0, 0.0]], "edge": [raw["edges"][0]["id"]] * 2, "maxspeed_kmh": [50, 50],
        "graph_nodes": path}), encoding="utf-8")
    monkeypatch.setattr(PL, "REGIONS", tmp_path / "Data" / "Regions")
    monkeypatch.setattr(BRG, "REPO", str(tmp_path))
    monkeypatch.setattr(NAV, "REPO", str(tmp_path))
    return rdir


def _arm_lanes(graph):
    """The two one-way edges of arm 0 (the carriageways the split separates), (from -> to geometry)."""
    feed = {T18.FEED_WAY, T18.FEED_WAY + 1}
    return [e for e in graph["edges"] if e["osm_way"] in feed]


def _lat_at(pts, x):
    """|y| of a polyline (along +x) at station x."""
    P = np.asarray(pts, float)
    P = P[np.argsort(P[:, 0])]
    return abs(float(np.interp(x, P[:, 0], P[:, 1])))


SPLIT_X = T18.SPLIT_R + 25.0         # the new split node on the +x arm
MID_X = T18.SPLIT_R + 5.0            # inside the separated stretch, past the taper


def test_effective_graph_reports_applied_and_stale(region):
    applied, stale = [], []
    g = PL.effective_graph(REGION, applied=applied, stale=stale)
    assert [a["id"] for a in applied] == ["syn-split"] and stale == []
    assert CS.node_aliases(g) == {f"n{SPLIT_NODE}": f"n{SPLIT_NODE}s"}
    raw = json.loads((region / "roads.graph.json").read_text(encoding="utf-8"))
    assert CS.node_aliases(raw) == {} and f"n{SPLIT_NODE}" in {n["id"] for n in raw["nodes"]}, "file untouched"
    bad = dict(SPLIT, node=123)
    (region / "overrides.yaml").write_text(yaml.safe_dump({"overrides": [bad]}), encoding="utf-8")
    applied, stale = [], []
    assert PL.effective_graph(REGION, applied=applied, stale=stale)["nodes"] == raw["nodes"] and stale == ["syn-split"]


def test_navgraph_routes_on_the_separated_carriageways(region, tmp_path):
    g = BRG.load_graph(REGION)
    ids = sorted(n["id"] for n in g["nodes"])
    assert f"n{SPLIT_NODE}s" in ids and f"n{SPLIT_NODE}" not in ids
    rows = [{"id": 1, "restriction": "no_u_turn", "from_way": T18.FEED_WAY, "via_node": SPLIT_NODE,
             "to_way": T18.FEED_WAY + 1}]
    t = BRG.build(g, (0.0, 0.0), rows, {})
    node = t["nodes"][ids.index(f"n{SPLIT_NODE}s")]
    assert math.hypot(node[0], node[1]) == pytest.approx(SPLIT_X, abs=0.05)
    lanes = [e for e in t["edges"] if e["osm_way"] in (T18.FEED_WAY, T18.FEED_WAY + 1)]
    assert len(lanes) == 2
    for e in lanes:
        assert _lat_at(e["pts"], MID_X) == pytest.approx(3.0, abs=0.05)
    # node and edge geometry agree (raw: the one-way edges start 25 m from where KRTG put their node)
    for e in t["edges"]:
        a, b = t["nodes"][e["from"]], t["nodes"][e["to"]]
        assert math.hypot(a[0] - e["pts"][0][0], a[1] - e["pts"][0][1]) < 0.05
        assert math.hypot(b[0] - e["pts"][-1][0], b[1] - e["pts"][-1][1]) < 0.05
    # the OSM via node of the moved split node maps onto the new node: the restriction is not lost
    assert t["unmapped_restrictions"] == [] and t["restrictions"]
    # main(): the routing bytes are written from the effective graph (no carriageway axes: synthetic heights)
    out = tmp_path / "nav"
    assert BRG.main(["--region", REGION, "--out-dir", str(out), "--no-carriageway-axis"]) == 0
    data = (out / f"{REGION}_route.bytes").read_bytes()
    assert BRG.serialize(BRG.build(g, (0.0, 0.0), [], {})) == data


def test_navgraph_main_is_deterministic(region, tmp_path):
    for k in ("a", "b"):
        BRG.main(["--region", REGION, "--out-dir", str(tmp_path / k), "--no-carriageway-axis"])
    assert (tmp_path / "a" / f"{REGION}_route.bytes").read_bytes() == (tmp_path / "b" / f"{REGION}_route.bytes").read_bytes()


def _knav_roads(data):
    """[(class, flags, pts)] of a KNAV v1 file (tools/ui/build_nav_map.py)."""
    assert data[:4] == b"KNAV"
    o = 4 + 2 + 16
    (nn,) = struct.unpack_from("<H", data, o)
    o += 2
    for _ in range(nn):
        (ln,) = struct.unpack_from("<H", data, o)
        o += 2 + ln
    (nr,) = struct.unpack_from("<H", data, o)
    o += 2
    roads = []
    for _ in range(nr):
        cls, fl, _w, _nm, npt = struct.unpack_from("<BBfHH", data, o)
        o += struct.calcsize("<BBfHH")
        pts = [struct.unpack_from("<ff", data, o + 8 * i) for i in range(npt)]
        o += 8 * npt
        roads.append((cls, fl, pts))
    return roads


def test_nav_map_draws_the_separated_carriageways(region, tmp_path):
    out = tmp_path / "knav"
    assert NAV.main(["--region", REGION, "--out-dir", str(out)]) == 0
    roads = _knav_roads((out / f"{REGION}.bytes").read_bytes())
    oneway_arm0 = [p for c, fl, p in roads if fl & 1 and max(x for x, _ in p) > SPLIT_X - 1]
    assert len(oneway_arm0) == 2
    assert sorted(round(_lat_at(p, MID_X), 1) for p in oneway_arm0) == [3.0, 3.0]


def test_audit_cameras_walk_the_effective_graph(region):
    graph, route = MAC.graph_and_route(REGION, region)
    assert route["graph_nodes"][0] == f"n{SPLIT_NODE}s"
    g = roadgraph.to_digraph(graph)
    u, v = route["graph_nodes"]
    e = next(x for x in graph["edges"] if x["id"] == g[u][v]["id"])
    assert _lat_at(e["geometry"], MID_X) == pytest.approx(3.0, abs=0.05)


def test_validator_ribbons_follow_the_separated_carriageways(region):
    edges = VC.graph_edges(REGION, (0.0, 0.0))
    arm = [e for e in edges if e["osm_way"] in (T18.FEED_WAY, T18.FEED_WAY + 1)]
    assert len(arm) == 2 and all(_lat_at(e["coords"], MID_X) == pytest.approx(3.0, abs=0.05) for e in arm)
    two = next(e for e in edges if e["osm_way"] == T18.ARM_WAY)
    assert min(x for x, _ in two["coords"]) == pytest.approx(SPLIT_X, abs=0.05), "two-way ribbon ends at the new split"


# ------------------------------------------------------------------ Knyszyn (git data, read only)
KN = "knyszyn"
KN_SPLITS = ("n4898926854", "n3047667219")


def test_knyszyn_route_graph_has_the_dk65_splits_and_consistent_geometry():
    raw = json.loads((PL.REGIONS / KN / "roads.graph.json").read_text(encoding="utf-8"))
    g = BRG.load_graph(KN)
    assert {CS.node_aliases(g)[k] for k in KN_SPLITS} == {k + "s" for k in KN_SPLITS}
    assert CS.node_aliases(raw) == {}
    axes = BRG.load_carriageway_axes(KN, g)
    t = BRG.build(g, BRG.read_origin(str(PL.REGIONS / KN)), [], axes)
    gaps = []
    for e in t["edges"]:
        a, b = t["nodes"][e["from"]], t["nodes"][e["to"]]
        gaps.append(max(math.hypot(a[0] - e["pts"][0][0], a[1] - e["pts"][0][1]),
                        math.hypot(b[0] - e["pts"][-1][0], b[1] - e["pts"][-1][1])))
    # measured 16.11: raw graph 26.99 m on 6 edges (the KRTG node stays at the OSM split, the axis starts at the new one)
    assert max(gaps) < 1.0


def test_knyszyn_route_start_translates_onto_the_effective_graph():
    graph, route = MAC.graph_and_route(KN, PL.REGIONS / KN)
    g = roadgraph.to_digraph(graph)
    path = route["graph_nodes"]
    assert "n4898926854s" in path and not set(KN_SPLITS) & set(path)
    assert all(g.has_edge(u, v) for u, v in zip(path, path[1:])), "route_start graph_nodes form a path"


# ------------------------------------------------------------------ every reader classified
EFFECTIVE = {   # walk graph geometry / topology next to the generated network -> pipeline.effective_graph
    "scripts/export-route.py", "scripts/map-audit-cameras.py", "tools/ui/build_nav_map.py",
    "tools/worldgen/navgraph/build_route_graph.py", "tools/worldgen/streaming/route_links.py", "tools/worldgen/navgraph/measure_axis_offset.py",
    "tools/worldgen/roads/build_world.py",            # route_polyline (control cameras, route QA)
    "tools/worldgen/roads/pipeline.py", "tools/worldgen/streetscape/water_banks.py", "tools/worldgen/validate/common.py",
}
RAW_OK = {      # ingested graph on purpose (reason in ADR 0274 "Czytniki grafu")
    "tools/worldgen/roads/seam_taper.py": "neighbour ends at the shared tile edge (ADR 0275): a split never sits on a seam",
    "tools/worldgen/roads/seam_p2a.py": "neighbour P-2a approaches at the shared tile edge (seams-fix-s23, ADR 0289): the same plain network as seam_taper",
    "tools/worldgen/qa/seams.py": "seam QA of neighbour tiles: boundary ends, ids unchanged",
    "tools/worldgen/qa/ring_0231_plan.py": "plan of the ring tiles: boundary nodes of built neighbours (ADR 0231)",
    "tools/worldgen/streaming/link_seams.py": "boundary nodes / end edges at tile seams: ids and seam ends unchanged",
    "tools/worldgen/roads/build_world.py": "graph_name (names by edge id) and tunnels (edge ids): ids unchanged",
    "tools/worldgen/streetscape/stage.py": "edge attrs by id + sign_gantry before_node (authored ingested node ids)",
    "tools/worldgen/streetscape/pavements.py": "osm_way -> highway only",
    "tools/worldgen/roads/tunnels.py": "graph_of: tunnel edge ids",
    "tools/worldgen/fidelity/run.py": "compares with OSM; input hashes",
    "tools/worldgen/fidelity/inputs.py": "hashes the ingested graph file (fidelity input hashes, ADR 0245)",
    "tools/worldgen/qa/typology_budget.py": "road mask from OSM axes for regions C/Dojlidy (no split), ADR 0238",
    "tools/worldgen/qa/lane_width_audit.py": "OSM tags (lanes, width) of route edges by id for the audit table (ADR 0301)",
    "tools/worldgen/qa/ortho_lane_fit.py": "raw OSM way geometry per edge id: the measured offset is relative to the ingested way (ADR 0301)",
    "tools/worldgen/qa/ortho_sidewalks.py": "orthophoto profiles across the ingested graph axis per edge id (measured sidewalk extent relative to the OSM axis), ADR 0349",
    "tools/worldgen/qa_report.py": "source data QA against orthophoto / BDOT10k",
    "tools/worldgen/qa/roundabout_ortho.py": "orthophoto probe on the OSM axes (the evidence for the override)",
    "tools/worldgen/qa/ortho_xsec.py": "orthophoto cross-sections of the OSM axes",
    "tools/worldgen/qa/s8_xsec_overrides.py": "lists the S8 ways (OSM id, lanes) and their OSM axis spacing to write their overrides, ADR 0288 (S8 never split)",
    "tools/worldgen/qa/edge_closures_check.py": "port of WorldEdgeBuilder.ReadExits, which reads the ingested roads.graph.json (boundary nodes + edges as imported), ADR 0292",
    "tools/worldgen/qa/seam_z.py": "boundary nodes (position, id) shared by two tiles; heights from the GLBs, ADR 0292",
    "tools/worldgen/qa/s8_seam_z.py":"S8 boundary nodes (position, way) shared by two tiles; heights from the GLBs, ADR 0288 s24",
    "tools/worldgen/qa/s8_median_gap.py": "S8 median gap on the plain network of seam_taper (same as qa/seams.py), ADR 0288 s24",
    "tools/worldgen/qa/seam_section.py": "route edges at region seams: far ends, ids unchanged",
    "tools/worldgen/qa/map_plan_0278.py": "plan of new tiles: boundary nodes of built neighbours (ADR 0278), ids unchanged",
    "tools/worldgen/qa/dk8_north_plan.py": "2D control render of built tiles (edge centrelines + class only, ADR 0315); no split override on these tiles",
    # D81 tiles wygoda / bojary / mickiewicza have no carriageway_split override: file graph == effective graph
    "tools/worldgen/qa/dk19_place_cameras.py": "D81 tiles (no split): street names of route edges",
    "tools/worldgen/qa/dk19_route_check.py": "D81 tiles (no split): hgv / maxweight attrs + truck route on the graphs",
    "tools/worldgen/qa/dk19_route_vias.py": "D81 tiles (no split): graph nodes of the truck route as vias",
    "tools/worldgen/qa/dk19_seam_nodes.py": "boundary nodes of the D81 tiles and neighbours: ids unchanged",
    "tools/worldgen/qa/dk19_xsec_overrides.py": "D81 tiles (no split): OSM ways + graph widths for the ortho overrides",
    "tools/worldgen/qa/dk19_xsec_summary.py": "orthophoto stations grouped by OSM street / lanes",
    "tools/worldgen/qa/knyszyn_s_kerb_step.py": "split node id of the authored override + its OSM way end: GLB probe only",
    "tools/worldgen/qa/median_lamp_row.py": "OSM axes of the opposite carriageway by name",
    "tools/worldgen/qa/junction_lane_widths.py": "research on the OSM source",
    "tools/worldgen/qa/junction_lane_stations.py": "research on the OSM source",
    "tools/worldgen/qa/depot_ortho.py": "orthophoto probe (region C, no split)",
    "tools/worldgen/qa/region_landmarks.py": "OSM source audit",
    "tools/worldgen/qa/lamp_family_audit.py": "attrs by street (docstring only)",
    "tools/worldgen/photolist/build_photo_list.py": "photo list map of region C (no split), OSM reference",
    "tools/worldgen/photolist/photo_cameras.py": "Mapillary pose snap to OSM way (region C, no split)",
    "tools/worldgen/build_region.py": "writes the ingested graph",
    "tools/refs/veg0163_cameras.py": "one-off reference cameras, region C (no split)",
    "scripts/map-audit-near.py": "one-off audit, region C (no split)",
    "scripts/export-region-catalog.py": "route_start graph_nodes are ingested ids (export-route contract)",
    "scripts/gate3-segment.py": "route_start points + ingested node ids (region putry, no split)",
}
READ = re.compile(r"""["'/]roads\.graph\.json["']""")     # the file name as a path literal (not prose)


def _readers():
    out = set()
    for base in ("scripts", "tools"):
        for p in (ROOT / base).rglob("*.py"):
            rel = p.relative_to(ROOT).as_posix()
            if "/.venv/" in rel or "/tests/" in rel:
                continue
            if READ.search(p.read_text(encoding="utf-8", errors="replace")):
                out.add(rel)
    return out


def test_every_graph_reader_is_classified():
    readers = _readers()
    assert readers, "pattern finds the readers"
    missing = readers - EFFECTIVE - set(RAW_OK)
    assert not missing, f"new roads.graph.json readers: classify them in ADR 0274 'Czytniki grafu' and here: {missing}"


@pytest.mark.parametrize("rel", sorted(EFFECTIVE))
def test_effective_readers_use_the_one_loader(rel):
    src = (ROOT / rel).read_text(encoding="utf-8")
    assert "effective_graph" in src or "load_graph(" in src
    assert "CS.apply(" not in src or rel.endswith("pipeline.py"), "no own copy of the override logic"
