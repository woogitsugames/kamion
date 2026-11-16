"""ADR 0223: railway line 38 (OSM relation 2316318) enabled in dk65-01..04 and dw671-tykocin-01 - real tile sources
(OSM API 0.6 cut-outs in generated/rail_sources.json, no Data/raw) + synthetic checks of the crossing equipment
mapping (Dz.U. 2025 poz. 1105 § 6 ust. 1), authored overrides, G-2 signs and edge-of-tile markers."""

from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import pytest
import shapely
import yaml
from shapely.geometry import LineString, Point

from conftest import REPO

REGIONS_DIR = REPO / "Data" / "Regions"
RAIL_ON = ("dk65-01", "dk65-02", "dk65-03", "dk65-04", "dw671-tykocin-01")
FORBIDDEN = ("knyszyn", "knyszyn-s", "knyszyn-w", "bialystok-knyszynska", "dk65-05", "dk65-06", "dk65-07", "dk65-08",
             "dk65-09", "dk65-10", "dk65-11", "dk65-monki-01")
MANIFEST = REPO / "Data" / "SourceManifests" / "osm-api-0.6-rail-l38.json"

# Measured from the OSM API cut-outs of 2026-11-15 (Plan clipped to the tile, EPSG:2180): track length per tile (m),
# OSM ways, level-crossing nodes -> (equipment, category, equipment_src). Line 38 never enters dk65-05..11, knyszyn*,
# dk65-monki-01 (0 m in their cut-outs, ADR 0223 table).
EXPECTED = {
    "dk65-01": (770.4, {173466803}, {2559254736: ("nieznane", None, "default")}),
    "dk65-02": (1614.1, {173466803}, {2335160489: ("nieznane", None, "default")}),
    "dk65-03": (1688.9, {41533341, 173466803, 406675496}, {}),
    "dk65-04": (1278.7, {406675496}, {2335162693: ("brak", "D", "derived"), 1778182442: ("brak", "D", "derived")}),
    "dw671-tykocin-01": (1096.9, {166369632}, {1778182481: ("nieznane", None, "default")}),
}
# seams between enabled tiles (shared edge) and open ends (neighbour without rail - reported in ADR 0223)
SEAMS = [("dk65-01", "dk65-02", "y", 597247.0), ("dk65-02", "dk65-03", "x", 768779.0),
         ("dk65-03", "dk65-04", "y", 599295.0)]
OPEN_ENDS = {("dk65-01", "x", 770827.0): "bialystok-knyszynska (forbidden, rail off)",
             ("dk65-04", "x", 766731.0): "no region (lattice -6,2)",
             ("dw671-tykocin-01", "x", 758539.0): "no region (lattice -10,7)",
             ("dw671-tykocin-01", "y", 609535.0): "no region (lattice -9,6)"}


def _region(rid):
    return yaml.safe_load((REGIONS_DIR / rid / "region.yaml").read_text(encoding="utf-8"))


def _sources(rid):
    return json.loads((REGIONS_DIR / rid / "generated" / "rail_sources.json").read_text(encoding="utf-8"))


def _road_edges(rid):
    g = json.loads((REGIONS_DIR / rid / "roads.graph.json").read_text(encoding="utf-8"))
    out = []
    for e in g["edges"]:
        if len(e["geometry"]) < 2:
            continue
        a = e["attrs"]
        w = (a.get("width") or {}).get("v") or 3.0 * max(int((a.get("lanes") or {}).get("v") or 2), 1)
        out.append((LineString(e["geometry"]), float(w), bool((a.get("bridge") or {}).get("v")), e["osm_way"]))
    return out


def _plan(rid, with_roads=True):
    from streetscape import rail as RL
    ry = _region(rid)
    bb, o = ry["bbox"], (ry["origin"]["x"], ry["origin"]["y"])
    tile = shapely.box(bb["xmin"] - o[0], bb["ymin"] - o[1], bb["xmax"] - o[0], bb["ymax"] - o[1])
    lines, poly = [], None
    if with_roads:
        ed = [(shapely.affinity.translate(L, -o[0], -o[1]), w, br) for L, w, br, _ in _road_edges(rid)]
        lines = [L for L, _, br in ed if not br]
        poly = shapely.union_all([L.buffer(w / 2, cap_style=2) for L, w, br in ed if not br])
    return RL.Plan(_sources(rid), o, tile, poly, lines), o


# ------------------------------------------------------------------------------------------------ opt-in
def test_rail_enabled_only_on_line38_tiles():
    import regions
    from streetscape import rail as RL
    assert sorted(r.id for r in regions.REGIONS.values() if r.rail) == sorted(RAIL_ON)
    assert not any(r.rail for r in regions.REGIONS.values() if r.id in FORBIDDEN)
    for rid in RAIL_ON:
        d = REGIONS_DIR / rid
        text = (d / "region.yaml").read_text(encoding="utf-8")
        ry = yaml.safe_load(text)
        assert RL.enabled(ry)
        assert ry["rail"]["sources"] == f"Data/Regions/{rid}/generated/rail_sources.json"
        # region.yaml exactly as build_region dumps it (the key is appended last) and its hash in build_manifest
        assert yaml.safe_dump(ry, allow_unicode=True, sort_keys=False, width=120) == text
        assert list(ry)[-1] == "rail"
        bm = json.loads((d / "build_manifest.json").read_text(encoding="utf-8"))
        assert bm["sha256"]["region.yaml"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    for rid in FORBIDDEN:
        d = REGIONS_DIR / rid
        if (d / "region.yaml").exists():
            assert not RL.enabled(_region(rid))
            assert not (d / "generated" / "rail_sources.json").exists()


def test_sources_schema_and_provenance():
    from streetscape import rail as RL
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for k in ("url", "sha256", "retrieved_utc"):
        assert all(k in f for f in man["files"].values())
    assert man["license"] == "ODbL 1.0" and "EPSG:2180" in man["crs"] and man["in_git"] is False
    for rid in RAIL_ON:
        s = _sources(rid)
        ry = _region(rid)
        assert s["schema"] == RL.SCHEMA and s["crs"] == "EPSG:2180" and "ODbL" in s["license"]["osm"]
        assert s["bbox"] == [ry["bbox"][k] for k in ("xmin", "ymin", "xmax", "ymax")]
        pv = s["provenance"]
        if pv["source"] == "osm-pbf":         # regenerated by build_region from Data/raw (lead): pbf is canonical
            continue
        assert pv["source"] == "osm-api-0.6" and pv["route_relation"].startswith("osm:relation/2316318")
        for f in pv["files"]:
            assert man["files"][f["file"]]["sha256"] == f["sha256"]
            assert f["url"].startswith("https://api.openstreetmap.org/api/0.6/")
        # tags limited to the shared keep-list, coordinates in the tile + 100 m
        box = shapely.box(*s["bbox"]).buffer(100.5, join_style="mitre")
        for w in s["osm"]["ways"]:
            assert set(w["tags"]) <= set(RL.KEEP_TAGS)
            assert all(box.contains(Point(c)) for c in w["coords"])
        for n in s["osm"]["nodes"]:
            assert set(n["tags"]) <= set(RL.KEEP_TAGS) and box.contains(Point(n["xy"]))


# ------------------------------------------------------------------------------------------------ real tiles
@pytest.mark.parametrize("rid", RAIL_ON)
def test_line38_tracks_per_tile(rid):
    length, ways, _ = EXPECTED[rid]
    p, _ = _plan(rid, with_roads=False)
    assert {int(t.id.split("/")[1].split(":")[0]) for t in p.tracks} == ways
    assert abs(sum(t.line.length for t in p.tracks) - length) < 1.0
    for t in p.tracks:
        assert t.a["ref"] == "38" and t.a["usage"] == "main" and t.a["gauge_mm"] == 1435.0
        assert t.a["electrified"] == "contact_line" and t.a["maxspeed_kmh"] == 100.0
        assert t.a["tracks"] == 1 and t.a["tracks_src"] == "default"     # `tracks` not tagged: single track default
    assert not [s for s in p.report["skipped"] if s["why"].startswith("railway=rail")]


@pytest.mark.parametrize("rid", RAIL_ON)
def test_level_crossings_equipment_per_tile(rid):
    _, _, crossings = EXPECTED[rid]
    p, _ = _plan(rid)
    got = {int(c["src"].split("/")[1]): (c["equipment"], c["category"], c["equipment_src"])
           for c in p.crossings if c["source"] == "osm"}
    assert got == crossings
    # every ground road x rail intersection of the road graph is an OSM level crossing (no geometry-only crossing)
    assert not [c for c in p.crossings if c["source"] == "geometry"]
    for c in p.crossings:
        assert c["electrified"]
        assert p.sign_code(c) == "G-3"              # no barriers tagged, single track (§ 80 ust. 1)


@pytest.mark.parametrize("rid", RAIL_ON)
def test_track_bed_clear_of_roads_outside_crossings(rid):
    """The ballast footprint (axis +- half crown) does not overlap a ground carriageway except at a level crossing;
    road bridges over the line (dk65-02: S8) are grade separated and excluded."""
    p, o = _plan(rid, with_roads=False)
    bed = shapely.union_all([t.line.buffer(t.half_top, cap_style=2) for t in p.tracks if not t.a["bridge"]])
    roads = [(shapely.affinity.translate(L, -o[0], -o[1]), w) for L, w, br, _ in _road_edges(rid) if not br]
    hits = bed.intersection(shapely.union_all([L.buffer(w / 2, cap_style=2) for L, w in roads]))
    xs = shapely.union_all([Point(np.asarray(n["xy"]) - o).buffer(15.0) for n in _sources(rid)["osm"]["nodes"]
                            if n["tags"].get("railway") == "level_crossing"] or [shapely.Polygon()])
    assert hits.difference(xs).area < 0.5, hits.difference(xs).bounds


@pytest.mark.parametrize("a,b,axis,v", SEAMS)
def test_track_continuous_across_seams(a, b, axis, v):
    ends = {}
    for rid in (a, b):
        p, o = _plan(rid, with_roads=False)
        k = 0 if axis == "x" else 1
        pts = [np.asarray(t.line.coords[i]) + o for t in p.tracks for i in (0, -1)]
        ends[rid] = [q for q in pts if abs(q[k] - v) < 1e-6]
    assert len(ends[a]) == len(ends[b]) == 1
    assert np.linalg.norm(ends[a][0] - ends[b][0]) <= 0.1


def test_open_track_ends_are_documented():
    """Every track end on a tile edge is either a seam with an enabled neighbour or a documented open end."""
    found = set()
    for rid in RAIL_ON:
        p, o = _plan(rid, with_roads=False)
        bb = _region(rid)["bbox"]
        for t in p.tracks:
            for i in (0, -1):
                q = np.asarray(t.line.coords[i]) + o
                for axis, k, edge in (("x", 0, bb["xmin"]), ("x", 0, bb["xmax"]), ("y", 1, bb["ymin"]),
                                      ("y", 1, bb["ymax"])):
                    if abs(q[k] - edge) < 1e-6:
                        found.add((rid, axis, edge))
    seam = {(a, ax, v) for a, _, ax, v in SEAMS} | {(b, ax, v) for _, b, ax, v in SEAMS}
    assert found - seam == set(OPEN_ENDS)


def test_tile_meshes_and_budget():
    """Real tile geometry on a flat ground / road: triangles per LoD stay at the closed form (ADR 0217) + panels."""
    from roads.meshing import MeshBuf
    from streetscape import rail as RL

    def flat(z):
        return lambda e, n: np.full(np.shape(e), z) + 0.0 * np.asarray(n)
    tot = {k: 0 for k in RL.LAYERS}
    km = 0.0
    for rid in RAIL_ON:
        p, _ = _plan(rid)
        buf = MeshBuf()
        tris = p.build(buf, flat(100.0), flat(100.0), log=lambda *a: None)
        L = sum(t.line.length for t in p.tracks) / 1000.0
        km += L
        for k in tot:
            tot[k] += tris[k]
        # + the PANEL_STEP (0.5 m) stations of every crossing zone (rail-fix-s21: the bed follows the road crown there)
        zone = sum(math.ceil((c["zone"][1] - c["zone"][0]) / RL.PANEL_STEP) for c in p.crossings)
        assert tris["rail_lod1"] <= RL.tri_per_km(1) * L * 1.05 + 40 * len(p.tracks) + 12 * zone
        assert tris["rail_lod2"] <= RL.tri_per_km(2) * L * 1.05 + 10 * len(p.tracks) + 4 * zone
        assert abs(tris["rail_lod0"] - RL.tri_per_km(0) * L) <= 0.03 * RL.tri_per_km(0) * L + 300
        assert all(m["kind"] in ("sign", "light", "barrier", "bell") for m in p.report["markers"])
        assert p.report["clearance"]["min_marker_distance_m"] is None or \
            p.report["clearance"]["min_marker_distance_m"] > RL.CLEARANCE_HALF
    assert abs(km - sum(v[0] for v in EXPECTED.values()) / 1000.0) < 0.005
    assert tot["rail_crossing"] > 0


def test_edge_crossing_markers_stay_in_tile():
    """dk65-04: the Białostocka crossing lies 0.5 m inside the west edge - the outer approach markers are listed in
    markers_outside_tile, never placed in the neighbour's far field."""
    from roads.meshing import MeshBuf
    p, _ = _plan("dk65-04")
    p.build(MeshBuf(), lambda e, n: np.zeros(np.shape(e)), lambda e, n: np.zeros(np.shape(e)), log=lambda *a: None)
    tile = p.tile_local
    assert all(tile.contains(Point(m["e"], m["n"])) for m in p.report["markers"])
    out = p.report.get("markers_outside_tile", [])
    assert out and all(m["crossing"] == next(i for i, c in enumerate(p.crossings) if c["src"].endswith("2335162693"))
                       for m in out)


# ------------------------------------------------------------------------------------------------ synthetic
@pytest.mark.parametrize("barrier,light,equipment,category,src", [
    ("full", None, "rogatki_pelne", "A", "osm"),
    ("gate", None, "rogatki_pelne", "A", "osm"),
    ("half", "yes", "polrogatki", "B", "osm"),
    ("double_half", "yes", "polrogatki_wjazd_wyjazd", "B", "osm"),
    ("no", "yes", "sygnalizacja_swietlna", "C", "osm"),
    ("no", "no", "brak", "D", "osm"),
    ("no", None, "brak_rogatek_swiatla_nieznane", "C|D", "osm"),
    (None, "yes", "sygnalizacja_swietlna_rogatki_nieznane", "A|B|C", "derived"),
    (None, "no", "brak", "D", "derived"),
    (None, None, "nieznane", None, "default"),
])
def test_equipment_mapping(barrier, light, equipment, category, src):
    from streetscape import rail as RL
    tags = {"railway": "level_crossing"}
    if barrier:
        tags["crossing:barrier"] = barrier
    if light:
        tags["crossing:light"] = light
    ok, _, a = RL.classify_node(tags)
    assert ok
    assert (a["equipment"], a["category"], a["equipment_src"]) == (equipment, category, src)
    assert a["equipment_confidence"] in ("low", "medium") and a["category_basis"]


def _syn(electrified=None, barrier=None, light=None, node_xy=(500.0, 500.0), tile=None, overrides=()):
    from streetscape import rail as RL
    tags = {"railway": "rail", **({"electrified": electrified} if electrified else {})}
    ntags = {"railway": "level_crossing", **({"crossing:barrier": barrier} if barrier else {}),
             **({"crossing:light": light} if light else {})}
    src = {"osm": {"ways": [{"osm_way": 10, "part": 0, "tags": tags, "coords": [[0.0, 500.0], [1000.0, 500.0]]}],
                   "nodes": [{"osm_node": 1, "tags": ntags, "xy": list(node_xy)}]}}
    x = node_xy[0]
    road = LineString([(x, 0.0), (x, 1000.0)])
    return RL.Plan(src, (0.0, 0.0), tile, road.buffer(3.5, cap_style=2), [road], overrides=overrides)


def _build(p):
    from roads.meshing import MeshBuf
    p.build(MeshBuf(), lambda e, n: np.full(np.shape(e), 100.0), lambda e, n: np.full(np.shape(e), 100.0),
            log=lambda *a: None)
    return p


def test_g2_sign_on_electrified_line():
    p = _build(_syn(electrified="contact_line"))
    g2 = [m for m in p.report["markers"] if m.get("code") == "G-2"]
    g3 = [m for m in p.report["markers"] if m.get("code") == "G-3"]
    assert len(g2) == len(g3) == 2 and all(m["mount"] == "below_cross" for m in g2)
    assert {(m["e"], m["n"]) for m in g2} == {(m["e"], m["n"]) for m in g3}          # on the G-3 post
    p = _build(_syn(electrified="contact_line", barrier="half", light="yes"))
    assert [m["mount"] for m in p.report["markers"] if m.get("code") == "G-2"] == ["signal_mast"] * 2
    assert not [m for m in _build(_syn()).report["markers"] if m.get("code") == "G-2"]
    assert not [m for m in _build(_syn(electrified="no")).report["markers"] if m.get("code") == "G-2"]


def test_authored_override_sets_equipment():
    ov = [{"id": "x1", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"barrier": "half", "light": True},
           "reason": "test", "confidence": "high", "source": "owner photo"},
          {"id": "x2", "kind": "rail_crossing", "target": {"osm_node": 999}, "set": {"barrier": "full"}},
          {"id": "road", "target": {"edge": "w1:2-3"}, "set": {"width": 6.0}}]          # road override: ignored
    p = _build(_syn(overrides=ov))
    c = p.crossings[0]
    assert (c["barrier"], c["light"], c["equipment"], c["category"]) == ("half", True, "polrogatki", "B")
    assert c["equipment_src"] == "authored_override" and c["equipment_confidence"] == "high" and c["override"] == "x1"
    assert p.report["overrides_applied"] == [{"id": "x1", "target": "osm:node/1"}]
    assert p.report["overrides_stale"] == ["x2"]
    assert len([m for m in p.report["markers"] if m["kind"] == "barrier"]) == 2
    assert not [m for m in p.report["markers"] if m.get("code") == "G-3"]
    # light-only override keeps the OSM barrier tag (none) -> derived from the authored light
    p = _build(_syn(overrides=[{"id": "x3", "kind": "rail_crossing", "target": {"osm_node": 1},
                                "set": {"light": False}}]))
    assert (p.crossings[0]["equipment"], p.crossings[0]["category"]) == ("brak", "D")
    with pytest.raises(ValueError):
        _syn(overrides=[{"id": "bad", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"colour": 1}}])
    with pytest.raises(ValueError):
        _syn(overrides=[{"id": "bad", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"barrier": "x"}}])


def test_markers_outside_tile_dropped():
    p = _build(_syn(node_xy=(1.0, 500.0), tile=shapely.box(0, 0, 1000, 1000)))
    assert p.report["markers"] and p.report["markers_outside_tile"]
    assert all(m["e"] >= 0 for m in p.report["markers"])
    assert any("tile edge" in w["why"] for w in p.report["warnings"])


def test_xml_extract_matches_schema(tmp_path):
    """extract_osm_xml: way clipped to tile + 100 m, keep-list tags, newest version wins, crossing node kept."""
    from streetscape import rail as RL
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    pts = [tr.transform(x, 600000.0) for x in (499000.0, 500500.0, 502000.0)]
    (lo1, la1), (lo2, la2), (lo3, la3) = pts
    xml = ('<osm version="0.6">'
           f'<node id="1" version="1" lat="{la1:.7f}" lon="{lo1:.7f}"/>'
           f'<node id="2" version="1" lat="{la2:.7f}" lon="{lo2:.7f}"><tag k="railway" v="level_crossing"/>'
           '<tag k="crossing:light" v="no"/><tag k="note" v="x"/></node>'
           f'<node id="3" version="1" lat="{la3:.7f}" lon="{lo3:.7f}"/>'
           '<way id="7" version="1"><nd ref="1"/><nd ref="2"/><nd ref="3"/><tag k="railway" v="rail"/>'
           '<tag k="maxspeed" v="100"/><tag k="wikidata" v="Q1"/></way></osm>')
    f = tmp_path / "a.osm"
    f.write_text(xml, encoding="utf-8")
    out = RL.extract_osm_xml((500000.0, 599000.0, 501000.0, 601000.0), [f])
    assert len(out["ways"]) == 1 and out["ways"][0]["tags"] == {"railway": "rail", "maxspeed": "100"}
    xs = [c[0] for c in out["ways"][0]["coords"]]
    assert abs(min(xs) - 499900.0) < 0.05 and abs(max(xs) - 501100.0) < 0.05
    assert [n["osm_node"] for n in out["nodes"]] == [2]
    assert out["nodes"][0]["tags"] == {"railway": "level_crossing", "crossing:light": "no"}
