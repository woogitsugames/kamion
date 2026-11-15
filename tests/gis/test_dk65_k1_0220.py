"""ADR 0220: DK65 cross-section elements from research K1 in dk65-01 ... dk65-05.

1. route chainage (km trasy of docs/reports/map/dk65_route_plan.json) -> region-local x/z and side (roads.route_km),
   checked against the K1 sample points and the OSM bus stops K1 names;
2. generator: `edge_line_spacing` (measured line-to-line distance of override edge lines, class < GP) and
   `kind: edge_line_dashed` (authored broken span of an edge line) on a synthetic straight road;
3. region data: the K1 elements written as overrides in dk65-01 ... dk65-05, the resulting line spacing in the built
   network = 6.2 m +- tolerance, seams unchanged, nothing stale.
No Data/raw needed (roads.graph.json, overrides.yaml and the route plan are in git)."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from roads import markings as MK  # noqa: E402
from roads import network  # noqa: E402
from roads import standards as S  # noqa: E402
from roads.meshing import MeshBuf  # noqa: E402
from roads.route_km import RouteKm, km_to_region, tile_of_km  # noqa: E402

REG = ROOT / "Data" / "Regions"
TILES = ["dk65-01", "dk65-02", "dk65-03", "dk65-04", "dk65-05"]
K1 = ROOT / "research" / "dk65-knyszyn-refs"
SPACING = 6.2          # K1 median (n = 14 in dk65-01 ... 05, 25 on the whole corridor)
TOL = 0.05             # generator vs authored value
K1_TOL = 0.25          # K1 per-point reading +-0.2 m per line


# ------------------------------------------------------------------------------------------------ 1. chainage
@pytest.fixture(scope="module")
def route():
    return RouteKm.from_plan()


def test_route_length_matches_plan(route):
    plan = json.loads((ROOT / "docs/reports/map/dk65_route_plan.json").read_text(encoding="utf-8"))
    assert route.length_km == pytest.approx(plan["variants"]["A_old_road"]["length_km"], abs=0.002)


def test_km_points_match_k1_samples(route):
    pts = json.loads((K1 / "data" / "km_points.json").read_text(encoding="utf-8"))
    assert len(pts) >= 20
    for p in pts:
        x, y = route.point(p["km"])
        assert abs(x - p["x"]) < 0.15 and abs(y - p["y"]) < 0.15, p["km"]


def test_tiles_of_k1_points(route):
    pts = {round(p["km"], 2): p["tile"] for p in json.loads((K1 / "data" / "km_points.json").read_text(encoding="utf-8"))}
    for km in (8.8, 9.0, 10.0, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0):
        assert tile_of_km(km) == pts[km], km


def test_tile_seams_are_plan_km(route):
    plan = json.loads((ROOT / "docs/reports/map/dk65_route_plan.json").read_text(encoding="utf-8"))
    tiles = {tuple(t["ij"]): t for t in plan["variants"]["A_old_road"]["tiles"]}
    for tid, ij in (("dk65-02", (-4, 1)), ("dk65-04", (-5, 2))):
        t = tiles[ij]
        q = km_to_region(tid, t["km_in"] + 0.01, route=route)
        assert q["inside"], tid
        q = km_to_region(tid, t["km_in"] - 0.01, route=route)
        assert not q["inside"], tid


def test_side_convention_with_osm_bus_stops(route):
    # K1: "przystanek Dobrzyniewo Duże km 12,99 L (node 14067837805)", "przystanek km 14,48 P (node 11243685568)"
    km, lat = route.locate(768561.99, 599987.33)
    assert km == pytest.approx(12.99, abs=0.01) and lat > 0
    km, lat = route.locate(768323.77, 601461.29)
    assert km == pytest.approx(14.48, abs=0.01) and lat < 0


def test_km_to_region_offset_and_frame(route):
    a = km_to_region("dk65-04", 13.0, "L", 5.0, route=route)
    b = km_to_region("dk65-04", 13.0, None, route=route)
    tx, tz = a["tangent_en"]
    d = np.array([a["x"] - b["x"], a["z"] - b["z"]])
    assert np.hypot(*d) == pytest.approx(5.0, abs=1e-3)
    assert tx * d[1] - tz * d[0] > 0           # left of the direction of growing km
    p = km_to_region("dk65-04", 13.0, "P", 5.0, route=route)
    assert p["sign"] == -1.0 and a["sign"] == 1.0
    ox, oy = 767755.0, 600319.0                 # dk65-04 origin (region.yaml)
    x, y = route.point(13.0)
    assert (b["x"], b["z"]) == pytest.approx((x - ox, y - oy), abs=1e-3)


# ------------------------------------------------------------------------------------ 2. generator (synthetic)
ORIGIN = (700000.0, 600000.0)


def _straight(width=7.6, spacing=SPACING, extra=()):
    ox, oy = ORIGIN
    g = {"nodes": [{"id": "a", "x": ox, "y": oy}, {"id": "b", "x": ox + 200.0, "y": oy}],
         "edges": [{"id": "e", "from": "a", "to": "b", "osm_way": 1, "geometry": [[ox, oy], [ox + 200.0, oy]],
                    "attrs": {"highway": {"v": "secondary"}, "oneway": {"v": "no"}, "lanes": {"v": 2},
                              "maxspeed": {"v": 90}}}]}
    st = {"width": width, "edge_lines": "both"}
    if spacing is not None:
        st["edge_line_spacing"] = spacing
    ov = [{"id": "x", "target": {"osm_way": 1}, "set": st}, *extra]
    net = network.load(g, ORIGIN, ov)
    for c in net.chains:
        c.z = np.zeros(len(c.line.s))
        c.e = np.zeros(len(c.line.s))
    net.authored = ov
    return net


def test_spacing_sets_line_positions():
    net = _straight(7.6)
    sec = net.sections["e"]
    assert sec.edge_line_spacing == SPACING and sec.provenance["edge_line_spacing"] == "authored_override:x"
    lats = sorted(float(lat) for lat, _ in MK.edge_lines(sec, sec.width / 2, 1))
    assert lats == pytest.approx([-SPACING / 2, SPACING / 2])
    # 6.9 m (D65 / ADR 0215) -> the same lines, 0.35 m of asphalt outside them
    sec = _straight(6.9).sections["e"]
    assert sorted(float(lat) for lat, _ in MK.edge_lines(sec, sec.width / 2, 1)) == pytest.approx([-3.1, 3.1])


def test_spacing_never_leaves_the_carriageway():
    sec = _straight(6.0).sections["e"]
    lats = sorted(float(lat) for lat, _ in MK.edge_lines(sec, sec.width / 2, 1))
    assert lats == pytest.approx([-(3.0 - MK.EDGE_LINE_MIN_INSET), 3.0 - MK.EDGE_LINE_MIN_INSET])
    # BDOT 6.5 m (Fasty): 6.2 m fits (line axis 0.15 m inside the edge)
    sec = _straight(6.5).sections["e"]
    assert sorted(float(lat) for lat, _ in MK.edge_lines(sec, sec.width / 2, 1)) == pytest.approx([-3.1, 3.1])


def test_without_spacing_rule_unchanged():
    sec = _straight(7.6, spacing=None).sections["e"]
    lats = sorted(float(lat) for lat, _ in MK.edge_lines(sec, sec.width / 2, 1))
    assert lats == pytest.approx([-(3.8 - S.EDGE_LINE_INSET_MINOR), 3.8 - S.EDGE_LINE_INSET_MINOR])


def _paint(net):
    buf, rep = MeshBuf(), {}
    MK._build_markings(buf, net, [], [], rep)
    return buf, rep


def _edge_parts(buf, side):
    """[(x0, x1)] of the edge-line parts on one side (+1 north = left of a->b, -1 south)."""
    out = []
    for p in buf.parts:
        if not p.src.startswith("P-7b@"):
            continue
        y = float(p.V[:, 1].mean())
        if np.sign(y) == side and abs(abs(y) - SPACING / 2) < 0.1:
            out.append((float(p.V[:, 0].min()), float(p.V[:, 0].max())))
    return sorted(out)


def test_dashed_span_breaks_one_side_only():
    span = {"id": "bay", "kind": "edge_line_dashed", "line_en": [[60.0, 0.5], [100.0, 0.3]], "side": "left",
            "dash_m": [1.0, 1.0]}
    net = _straight(7.6, extra=[span])
    buf, rep = _paint(net)
    assert rep["edge_line_dashed"]["stale"] == [] and len(rep["edge_line_dashed"]["applied"]) == 1
    left, right = _edge_parts(buf, 1), _edge_parts(buf, -1)
    assert len(right) == 1 and right[0][1] - right[0][0] > 190          # right side: one solid line
    dashes = [d for d in left if 60.0 - 0.01 <= d[0] and d[1] <= 100.0 + 0.01]
    assert len(dashes) == 20 and all(d[1] - d[0] == pytest.approx(1.0, abs=0.02) for d in dashes)
    solid = [d for d in left if d not in dashes]
    assert len(solid) == 2 and solid[0][1] == pytest.approx(60.0, abs=0.01) and solid[1][0] == pytest.approx(100.0, abs=0.01)
    assert rep["markings"]["P-7a edge line span (authored)"] == 1


def test_dashed_span_side_follows_its_own_direction():
    # the same bay traced from east to west: "left" is then the south side of the a->b road
    span = {"id": "bay", "kind": "edge_line_dashed", "line_en": [[100.0, 0.0], [60.0, 0.0]], "side": "left",
            "line": "P-7a"}
    buf, _ = _paint(_straight(7.6, extra=[span]))
    assert len(_edge_parts(buf, 1)) == 1 and len(_edge_parts(buf, -1)) == 2 + 20


def test_dashed_span_off_the_road_is_stale():
    span = {"id": "far", "kind": "edge_line_dashed", "line_en": [[60.0, 30.0], [100.0, 30.0]], "side": "left"}
    net = _straight(7.6, extra=[span])
    buf, rep = _paint(net)
    assert rep["edge_line_dashed"]["stale"] == ["far"] and "far" in net.overrides_stale
    assert len(_edge_parts(buf, 1)) == 1


# --------------------------------------------------------------------------------------------- 3. region data
@pytest.fixture(scope="module")
def nets():
    from roads import pipeline
    out = {}
    for t in TILES:
        net, graph, ov, _ = pipeline.build_network(t)
        net.authored = ov
        out[t] = (net, graph, ov)
    return out


def _route_edges(t):
    r = json.loads((REG / t / "route_start.json").read_text(encoding="utf-8"))
    return sorted(set(r["edge"]))


def test_generated_blocks_match_the_table():
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "tools/worldgen/qa/dk65_k1_elements.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout


def test_route_edge_line_spacing_is_k1_median(nets):
    """Every route section with override edge lines: lines SPACING apart (+-TOL), except way 234919333 (dk65-01, seam
    with bialystok-knyszynska at 6.0 m: unchanged, ADR 0220 Otwarte) and the Supraśl bridge (no K1 / strip reading)."""
    checked = 0
    for t, (net, _, _) in nets.items():
        assert net.overrides_stale == [], (t, net.overrides_stale)
        for eid in _route_edges(t):
            sec = net.sections[eid]
            el = MK.edge_lines(sec, sec.width / 2, 1)
            if len(el) != 2:
                continue
            sp = abs(float(el[0][0]) - float(el[1][0]))
            way = int(eid.split(":")[0][1:])
            if way in (234919333, 41533342):
                assert sec.edge_line_spacing is None
                continue
            assert sp == pytest.approx(SPACING, abs=TOL), (t, eid, sp)
            checked += 1
    assert checked >= 20


def test_k1_spacing_readings_within_tolerance():
    import csv
    rows = [r for r in csv.DictReader((K1 / "manifest.csv").open(encoding="utf-8"))
            if r["kafel"] in TILES and r["parametr"].startswith("rozstaw linii")]
    assert len(rows) == 14
    for r in rows:
        assert abs(float(r["wartość"]) - SPACING) <= K1_TOL, r["id"]


def test_dashed_spans_land_on_the_route(nets):
    for t, (net, _, ov) in nets.items():
        rep = {}
        spans = MK.edge_dashed_spans(net, ov, rep)
        want = [o["id"] for o in ov if o.get("kind") == "edge_line_dashed"]
        assert rep["edge_line_dashed"]["stale"] == [], t
        assert sorted({a["id"] for a in rep["edge_line_dashed"]["applied"]}) == sorted(want)
        route_chains = {c.id for c in net.chains if {x for x, _ in c.edges} & set(_route_edges(t))}
        assert {a["chain"] for a in rep["edge_line_dashed"]["applied"]} <= route_chains, t
        for lst in spans.values():
            for lo, hi, sign, d, g, oid in lst:
                assert hi - lo > 5.0 and (d, g) == (1.0, 1.0), oid


def test_dashed_span_sides_follow_k1():
    """side 'left' / 'right' in the data = K1 L / P (both measured in the direction of growing km)."""
    tab = json.loads((ROOT / "docs/reports/map/dk65_k1_elements.json").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in tab["dashed"]}
    n = 0
    for t in TILES:
        ov = yaml.safe_load((REG / t / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
        for o in ov:
            if o.get("kind") == "edge_line_dashed":
                e = by_id[o["id"]]
                assert o["side"] == {"L": "left", "P": "right"}[e["side"]]
                a = km_to_region(t, e["km"][0])
                assert o["line_en"][0] == pytest.approx([a["x"], a["z"]], abs=0.01)
                n += 1
    assert n == len(tab["dashed"]) == 11


def test_bus_bays_are_beside_the_carriageway_on_the_k1_side():
    from shapely.geometry import Point, Polygon
    route = RouteKm.from_plan()
    tab = json.loads((ROOT / "docs/reports/map/dk65_k1_elements.json").read_text(encoding="utf-8"))
    stops = {"dk65-04": (768561.99, 599987.33), "dk65-05": (768323.77, 601461.29)}   # OSM platforms 14067837805, 11243685568
    assert len(tab["bays"]) == 2
    for b in tab["bays"]:
        ov = yaml.safe_load((REG / b["tile"] / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
        o = next(o for o in ov if o["id"] == b["id"])
        assert o["kind"] == "paved_area" and o["material"] == "yard_asphalt" and not o.get("parking")
        pg = Polygon(o["polygon_epsg2180"])
        assert pg.is_valid and 100.0 < pg.area < 400.0, (b["id"], pg.area)
        assert not pg.contains(Point(*route.point(sum(b["km"]) / 2)))      # not on the axis
        km_s, lat_s = route.locate(*stops[b["tile"]])
        assert b["km"][0] < km_s < b["km"][1]
        c = pg.centroid
        _, lat_c = route.locate(c.x, c.y)
        assert np.sign(lat_c) == np.sign(lat_s) == (1 if b["side"] == "L" else -1)
