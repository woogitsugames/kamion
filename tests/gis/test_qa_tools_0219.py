"""ADR 0219 (a): one parser of road-graph node / edge ids for every region; fidelity `node_arm_check` no longer
crashes on tile-boundary cuts (B<edge>:<k>s|e) and gives byte-identical rows for OSM nodes (region C regression).

Pure Python, no Data/raw: reads only Data/Regions/*/{roads.graph.json, route_start.json} and the committed
Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json."""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import roadgraph as RG  # noqa: E402
from fidelity import metrics as Mx  # noqa: E402

REGIONS = REPO / "Data" / "Regions"
GRAPHS = sorted(REGIONS.glob("*/roads.graph.json"))
C = "bialystok-industrial-c"
DOJLIDY = "bialystok-dojlidy"


def _route(rid):
    return json.loads((REGIONS / rid / "route_start.json").read_text(encoding="utf-8"))


def _old_node_arm_check(ctx, node_ids):
    """Verbatim copy of metrics.node_arm_check before ADR 0219 (the reference for the region C regression)."""
    inc = defaultdict(int)
    graph_ways = {int(eid.split(":")[0].lstrip("w")) for eid in ctx.net.sections}
    for w in ctx.osm["ways"]:
        if w["tags"].get("highway") not in Mx.DRIVABLE or w["id"] not in graph_ways:
            continue
        ns = w["nodes"]
        for i, n in enumerate(ns):
            inc[n] += (1 if i in (0, len(ns) - 1) else 2)
    jn = {}
    for j in ctx.g.world.junctions:
        for n in j.nodes:
            jn[n] = j
    out = []
    for n in node_ids:
        nid = int(str(n).lstrip("n"))
        j = jn.get(n) or jn.get(f"n{nid}")
        gen_arms = None
        if j is not None:
            gen_arms = sum(1 for a in j.arms if a.node in (n, f"n{nid}"))
        out.append({"node": n, "osm_degree": inc.get(nid, 0), "gen_arms_at_node": gen_arms,
                    "junction": j.id if j else None})
    return out


def _synthetic_ctx(rid, seed=219):
    """Ctx stub from the committed graph: OSM ways rebuilt from the graph edges (way -> ordered node list), junctions
    on a random subset of the route's OSM nodes with random arm counts. Deterministic (seeded)."""
    g = json.loads((REGIONS / rid / "roads.graph.json").read_text(encoding="utf-8"))
    rnd = random.Random(seed)
    ways = defaultdict(list)
    for e in g["edges"]:
        a, b = e["id"].split(":")[1].split("#")[0].split("-")
        ways[e["osm_way"]] += [int(a), int(b)]
    hw = sorted(Mx.DRIVABLE)
    osm = {"ways": [{"id": w, "tags": {"highway": rnd.choice(hw + ["footway"])}, "nodes": ns}
                    for w, ns in sorted(ways.items())]}
    route_nodes = _route(rid)["graph_nodes"]
    junctions = []
    for k, n in enumerate(route_nodes):
        if n.startswith("n") and rnd.random() < 0.6:
            arms = [SimpleNamespace(node=n if rnd.random() < 0.7 else f"n{k}") for _ in range(rnd.randint(1, 5))]
            junctions.append(SimpleNamespace(id=f"j:{n}", nodes=[n], arms=arms))
    ctx = SimpleNamespace(net=SimpleNamespace(sections={e["id"]: None for e in g["edges"]}), osm=osm,
                          g=SimpleNamespace(world=SimpleNamespace(junctions=junctions)))
    return ctx, route_nodes


@pytest.mark.parametrize("path", GRAPHS, ids=[p.parent.name for p in GRAPHS])
def test_every_node_and_edge_id_of_every_region_parses(path):
    g = json.loads(path.read_text(encoding="utf-8"))
    edges = {e["id"].split("#")[0] for e in g["edges"]}
    for n in g["nodes"]:
        ref = RG.parse_node_id(n["id"])
        if ref.kind == "osm":
            assert n.get("osm_node") == ref.osm_node and not n.get("boundary")
        else:                                   # a tile cut: flagged, no OSM node, on an existing clipped edge
            assert n.get("boundary") is True and "osm_node" not in n and ref.osm_node is None
            assert f"w{ref.osm_way}:{ref.way_nodes[0]}-{ref.way_nodes[1]}" in edges
    for e in g["edges"]:
        assert RG.edge_osm_way(e["id"]) == e["osm_way"]
    route = _route(path.parent.name)
    ids = {n["id"] for n in g["nodes"]}
    assert all(RG.parse_node_id(n).id in ids for n in route["graph_nodes"])
    assert all(RG.edge_osm_way(e) for e in route["edge"])


def test_minted_ids_round_trip():
    eid = "w443103344:4419538590-4419538591"
    b = RG.boundary_node_id(eid, 0, "s")
    assert b == f"B{eid}:0s"
    r = RG.parse_node_id(b)
    assert (r.kind, r.osm_way, r.way_nodes, r.piece, r.end) == ("boundary", 443103344, (4419538590, 4419538591), 0, "s")
    assert RG.parse_node_id(RG.osm_node_id(1882887381)).osm_node == 1882887381
    assert RG.edge_osm_way(eid + "#2") == 443103344


@pytest.mark.parametrize("bad", ["", "n", "nn12", "w12", "12", "Bw1:2-3", "Bw1:2-3:0x", "n12a"])
def test_unknown_node_formats_fail_loudly(bad):
    with pytest.raises(ValueError):
        RG.parse_node_id(bad)


@pytest.mark.parametrize("bad", ["ww12:1-2", "w12", "12:1-2", "Bw1:2-3:0s", "w1:2"])
def test_unknown_edge_formats_fail_loudly(bad):
    """lstrip('w') used to accept 'ww12:...' as way 12; the parser does not."""
    with pytest.raises(ValueError):
        RG.edge_osm_way(bad)


def test_region_c_route_nodes_parse_exactly_as_before():
    nodes = _route(C)["graph_nodes"]
    assert nodes and all(RG.parse_node_id(n).kind == "osm" for n in nodes)
    assert [RG.parse_node_id(n).osm_node for n in nodes] == [int(n.lstrip("n")) for n in nodes]
    committed = json.loads((REGIONS / C / "generated" / "fidelity_qa.json").read_text(encoding="utf-8"))
    assert [r["node"] for r in committed["route_node_arms"]] == nodes
    assert all("skipped" not in r for r in committed["route_node_arms"])


@pytest.mark.parametrize("seed", [1, 219, 2026])
def test_region_c_node_arm_check_identical_to_old_code(seed):
    ctx, nodes = _synthetic_ctx(C, seed)
    assert Mx.node_arm_check(ctx, nodes) == _old_node_arm_check(ctx, nodes)


def test_dojlidy_boundary_route_nodes_are_skipped_not_crashing():
    ctx, nodes = _synthetic_ctx(DOJLIDY)
    assert any(n.startswith("B") for n in nodes)
    with pytest.raises(ValueError):            # the bug: int('w443103344:...') after lstrip('n')
        _old_node_arm_check(ctx, nodes)
    rows = Mx.node_arm_check(ctx, nodes)
    assert [r["node"] for r in rows] == nodes
    skipped = [r for r in rows if r.get("skipped")]
    assert [r["node"] for r in skipped] == [n for n in nodes if n.startswith("B")]
    assert all(r["skipped"] == "tile_boundary" and r["osm_degree"] is None and r["osm_way"] for r in skipped)
    osm_nodes = [n for n in nodes if n.startswith("n")]
    assert [r for r in rows if not r.get("skipped")] == _old_node_arm_check(ctx, osm_nodes)


@pytest.mark.parametrize("rid", sorted(p.parent.name for p in GRAPHS))
def test_node_arm_check_runs_for_every_region(rid):
    ctx, nodes = _synthetic_ctx(rid)
    rows = Mx.node_arm_check(ctx, nodes)
    assert len(rows) == len(nodes)
    assert sum(1 for r in rows if r.get("skipped")) == sum(1 for n in nodes if n.startswith("B"))
