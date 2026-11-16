"""pytest: routing-graph edge geometry on the generated carriageway axes (ADR 0144 open item).

Run: uv run --project tools/worldgen pytest tools/worldgen/navgraph/tests
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import build_route_graph as brg  # noqa: E402
import measure_axis_offset as mao  # noqa: E402

REGION = "bialystok-industrial-c"
RDIR = os.path.join(brg.REPO, "Data", "Regions", REGION)
AXIS_MAX_OFFSET_M = 0.5   # WORKING_VALUE: max lateral offset of the route line from the carriageway axis


def _region():
    graph = json.load(open(os.path.join(RDIR, "roads.graph.json"), encoding="utf-8"))
    rows = json.load(open(os.path.join(RDIR, "turn_restrictions.json"), encoding="utf-8"))["restrictions"]
    return graph, rows, brg.read_origin(RDIR)


def test_axis_replaces_geometry_but_not_length():
    """Synthetic: an edge with a carriageway axis stores the axis pts (oneway=-1 reversal applied), while
    length_m stays the OSM polyline length (A* cost unchanged); an edge without an axis keeps the OSM axis."""
    nodes = [{"id": "nA", "x": 100.0, "y": 100.0, "osm_node": 1}, {"id": "nB", "x": 200.0, "y": 100.0, "osm_node": 2}]
    edges = [
        {"id": "w10:1-2", "from": "nA", "to": "nB", "geometry": [[100, 100], [200, 100]], "osm_way": 10,
         "attrs": {"highway": {"v": "residential", "src": "osm", "conf": "high"}}},
        {"id": "w11:1-2", "from": "nA", "to": "nB", "geometry": [[100, 100], [200, 100]], "osm_way": 11,
         "attrs": {"highway": {"v": "service", "src": "osm", "conf": "high"}, "oneway": {"v": "-1", "src": "osm", "conf": "high"}}},
    ]
    graph = {"nodes": nodes, "edges": edges}
    axis = [(0.0, 1.5), (50.0, 2.5), (100.0, 1.5)]     # from -> to, 2.5 m off the OSM axis
    t = brg.build(graph, (100.0, 100.0), [], {"w10:1-2": axis, "w11:1-2": axis})
    e0, e1 = t["edges"]
    assert e0["pts"] == [(0.0, 1.5), (50.0, 2.5), (100.0, 1.5)]
    assert e1["pts"] == [(100.0, 1.5), (50.0, 2.5), (0.0, 1.5)]     # oneway=-1: stored in travel direction
    for e in (e0, e1):
        assert abs(e["length"] - 100.0) < 1e-6                       # OSM length, not the axis length
    t_plain = brg.build(graph, (100.0, 100.0), [])
    assert t_plain["edges"][0]["pts"] == [(0.0, 0.0), (100.0, 0.0)]   # fallback: raw OSM axis


def test_region_edges_on_carriageway_axis():
    """Every region edge with an available carriageway axis stores that axis: max lateral offset of the stored
    route line from the axis < AXIS_MAX_OFFSET_M (WORKING_VALUE 0.5 m). Before the change (raw OSM axes) 165 of
    646 edges exceed 0.5 m (max 7.0 m, w606396463:2840742308-2840742310) - measured by measure_axis_offset.py."""
    graph, rows, origin = _region()
    axes = brg.load_carriageway_axes(REGION, graph)
    assert len(axes) >= len(graph["edges"]) * 0.9, "carriageway axes should cover nearly the whole region"
    t = brg.build(graph, origin, rows, axes)
    by_id = {e["id"]: e for e in graph["edges"]}
    checked = 0
    worst = 0.0
    for e in t["edges"]:
        if e["id"] not in axes:
            continue
        mx, _ = mao.edge_offsets(e["pts"], axes[e["id"]])
        worst = max(worst, mx)
        assert mx < AXIS_MAX_OFFSET_M, f"{e['id']}: max offset {mx:.3f} m >= {AXIS_MAX_OFFSET_M} m"
        checked += 1
    assert checked >= len(axes)
    # the A* cost is untouched: same lengths as the OSM-axis build, same node count / edge order
    t_osm = brg.build(graph, origin, rows)
    assert [e["length"] for e in t["edges"]] == [e["length"] for e in t_osm["edges"]]
    assert [e["from"] for e in t["edges"]] == [e["from"] for e in t_osm["edges"]]
    # sanity: the change is real - on the OSM-axis build many covered edges sit well off the carriageway axis
    off = [mao.edge_offsets(e["pts"], axes[by_id[e["id"]]["id"]]) for e in t_osm["edges"] if e["id"] in axes]
    assert sum(1 for mx, _ in off if mx > AXIS_MAX_OFFSET_M) > 100
    assert max(mx for mx, _ in off) > 5.0
    print(f"checked {checked} edges, worst max offset with axis: {worst:.4f} m")


def test_axis_offsets_are_pure_lateral():
    """The axis substitution must not move an edge along its own direction: endpoints of the stored pts stay
    within a few metres of the edge's nodes (fork shifts move stems off the node by design, gore noses most)."""
    graph, rows, origin = _region()
    axes = brg.load_carriageway_axes(REGION, graph)
    t = brg.build(graph, origin, rows, axes)
    node_xy = {i: (n[0], n[1]) for i, n in enumerate(t["nodes"])}
    for e in t["edges"]:
        if e["id"] not in axes:
            continue
        a, b = node_xy[e["from"]], node_xy[e["to"]]
        d0 = math.hypot(e["pts"][0][0] - a[0], e["pts"][0][1] - a[1])
        d1 = math.hypot(e["pts"][-1][0] - b[0], e["pts"][-1][1] - b[1])
        assert d0 < 10.0 and d1 < 10.0, f"{e['id']}: end {d0:.1f} / {d1:.1f} m off its node"


PERTURBATIONS = (0.0, 1e-14, -1e-14, 1e-13, -1e-13, 1e-12, -1e-12, 1e-9, -1e-9)


def test_axis_span_slice_is_stable_on_float_noise():
    """D35 regression (synthetic): a span boundary that IS a sample (the chain end, an interior vertex) is kept no
    matter on which side of the sample float noise puts raw_span * k. The old rule (no tolerance) flipped on +-1e-14:
    that alone moved one axis end by a 0.5 m sampling step between Windows and Linux (D31)."""
    import numpy as np
    n = 61
    s = np.cumsum(np.r_[0.0, np.full(n - 1, 0.4958)])          # 0.5 m-ish sampling like roads.pipeline
    end, mid = float(s[-1]), float(s[30])
    for d in PERTURBATIONS:
        assert brg.axis_span_slice(s, 0.0 + d, end + d) == (0, n)          # whole chain, both ends inclusive
        assert brg.axis_span_slice(s, 0.0 + d, mid + d) == (0, 31)         # interior vertex kept on the first span
        assert brg.axis_span_slice(s, mid + d, end + d) == (30, n)         # ... and on the next one (shared vertex)
    # Non-boundary values are cut as before (no sample within eps): 0.2 m off a sample changes nothing.
    assert brg.axis_span_slice(s, float(s[3]) + 0.2, float(s[10]) - 0.2) == (4, 10)
    # The old rule was unstable exactly here (documents the D31 cause; not used by the pipeline any more).
    assert int(np.searchsorted(s, end - 1e-14, side="right")) == n - 1
    assert int(np.searchsorted(s, end, side="right")) == n


def test_region_axis_slices_stable_under_perturbation():
    """D35 (region C): every edge span cut out of every chain gives the same sample range when its boundaries are
    shifted by +-1e-14 ... +-1e-9 m, and a span that ends at the chain end keeps the chain's last sample."""
    import numpy as np
    graph, _, _ = _region()
    sys.path.insert(0, os.path.join(brg.REPO, "tools", "worldgen"))
    from roads import pipeline
    net, _, _, _ = pipeline.build_network(REGION, graph)
    spans = ends = 0
    for c in net.chains:
        if c.line is None:
            continue
        k = c.length / max(c.raw_spans[-1][1], 1e-9)
        s = c.line.s
        last = c.raw_spans[-1][1]
        for s0, s1, eid, _rev in c.raw_spans:
            ref = brg.axis_span_slice(s, s0 * k, s1 * k)
            for d in PERTURBATIONS[1:]:
                assert brg.axis_span_slice(s, s0 * k + d, s1 * k + d) == ref, (eid, d)
            if s0 == 0.0:
                assert ref[0] == 0, eid
            if s1 == last:
                assert ref[1] == len(s), eid
                ends += 1
            spans += 1
    assert spans > 500 and ends > 100
