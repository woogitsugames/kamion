"""ADR 0231: rough definition of the next ring of tiles past Knyszyn (DK65 to Monki, DW671 to Tykocin, DW671 to
Jasionowka). Definition tests only, on data in git (no Data/raw, no network): ids, lattice, size, CRS, no overlap,
seams of the through roads (inside the ring and with the built neighbours), authored files, deterministic plan."""
from __future__ import annotations

import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import pytest
import yaml
from pyproj import Transformer
from shapely.geometry import LineString, box

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
import regions  # noqa: E402
import ring_0231_plan as RP  # noqa: E402

RDIR = REPO / "Data" / "Regions"
PLAN = json.loads(RP.PLAN.read_text(encoding="utf-8"))
EXTRACT = json.loads(RP.EXTRACT.read_text(encoding="utf-8"))
NEW = [t["id"] for t in PLAN["tiles"]]
TILE = {t["id"]: t for t in PLAN["tiles"]}
# the regions defined before ADR 0231 (ADR 0166-0214); none of them may change or be duplicated
OLD = sorted(set(regions.REGIONS) - set(NEW))
SEED_OVERRIDE_IDS = {"dk65-carriageway-width", "dk65-fields-unlit"}   # written by ring_0231_plan.py --init-regions
CROSS_SECTION_KEYS = ("lanes", "lane_width", "edge_strip", "edge_lines", "lamps")


def _sets_for_way(region_id: str, way: int) -> dict:
    """Merged `set` of the authored overrides of a region that target one OSM way (cross-section + lamp keys)."""
    p = RDIR / region_id / "overrides.yaml"
    ov = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("overrides") or [] if p.exists() else []
    out = {}
    for o in ov:
        if way in ((o.get("target") or {}).get("osm_way") or []):
            out.update({k: v for k, v in (o.get("set") or {}).items() if k in CROSS_SECTION_KEYS})
    return out


# ----------------------------------------------------------------------------------------------- plan / sources
def test_plan_is_deterministic_and_matches_git():
    assert RP.build_plan(EXTRACT) == PLAN


def test_extract_hash_matches_manifest():
    man = json.loads(RP.MANIFEST.read_text(encoding="utf-8"))
    ex = man["extract_in_git"]
    assert ex["path"] == RP.EXTRACT.relative_to(REPO).as_posix()
    assert hashlib.sha256(RP.EXTRACT.read_bytes()).hexdigest() == ex["sha256"]
    assert man["license"] == "ODbL 1.0" and "OpenStreetMap" in man["attribution"]
    assert sorted(s["sha256"] for s in EXTRACT["sources"]) == sorted(man["raw_answers"]["sha256"].values())
    for s in EXTRACT["sources"]:                                  # no Google, generic client only
        assert "google" not in s["endpoint"].lower()
    assert "kamion" not in RP.GENERIC_UA.lower() and "truck" not in RP.GENERIC_UA.lower()


WATER_S24 = {"dw671-tykocin-01", "dw671-tykocin-02", "dw671-tykocin-08", "dw671-tykocin-09", "tykocin"}

# ----------------------------------------------------------------------------------------------- registry
def test_new_entries_generated_from_plan():
    assert len(NEW) == len(set(NEW)) == 18
    for t in PLAN["tiles"]:
        r = regions.get(t["id"])
        assert r.id == t["id"]
        assert r.bbox == tuple(t["bbox"]) and r.origin == tuple(t["origin"])
        assert r.teryt_powiat == t["teryt_powiat"] and list(r.teryt_powiat_extra) == t["teryt_powiat_extra"]
        # the status goes verbatim into region.yaml (build_region): it must not say "not built" - whether a tile is
        # built is read from the disk (region.yaml), see test_authored_files_present_and_consistent
        assert r.title == RP.TITLES[r.id] and "ADR 0231" in r.status and "not built" not in r.status
        # ADR 0210 stays opt-in (open point in ADR 0231); water-tykocin-s24 opted in the tiles with surface water
        assert r.water is (r.id in WATER_S24)


def test_ids_unique_and_keys_match():
    assert all(k == r.id for k, r in regions.REGIONS.items())
    titles = [r.title for r in regions.REGIONS.values()]
    assert len(titles) == len(set(titles))


def test_tile_size_lattice_and_origin():
    for rid in NEW:
        r = regions.get(rid)
        assert r.width == r.height == regions.TILE_SIZE_M == 2048.0
        i, j = (r.bbox[0] - RP.X0) / RP.T, (r.bbox[1] - RP.Y0) / RP.T
        assert i == int(i) and j == int(j) and [int(i), int(j)] == TILE[rid]["ij"]
        assert r.origin == ((r.bbox[0] + r.bbox[2]) / 2, (r.bbox[1] + r.bbox[3]) / 2)
        assert all(isinstance(v, float) for v in r.bbox + r.origin)


def test_no_overlap_and_no_duplicate_with_existing_tiles():
    allr = list(regions.REGIONS.values())
    for a, b in combinations(allr, 2):
        assert a.bbox != b.bbox, (a.id, b.id)
        assert box(*a.bbox).intersection(box(*b.bbox)).area == 0.0, (a.id, b.id)
    # ADR 0212 tiles (dk65-monki-01, dw671-tykocin-01) and Knyszyn are the starting points, not part of the ring
    assert not {"dk65-monki-01", "dw671-tykocin-01", "knyszyn", "knyszyn-w", "knyszyn-s"} & set(NEW)


def test_existing_entries_unchanged():
    """Every region built before ADR 0231 still has the bbox / origin / powiat recorded in its region.yaml."""
    n = 0
    for rid in OLD:
        p = RDIR / rid / "region.yaml"
        if not p.exists():
            continue
        y = yaml.safe_load(p.read_text(encoding="utf-8"))
        r = regions.get(rid)
        assert r.bbox == (y["bbox"]["xmin"], y["bbox"]["ymin"], y["bbox"]["xmax"], y["bbox"]["ymax"]), rid
        assert r.origin == (y["origin"]["x"], y["origin"]["y"]) and r.teryt_powiat == str(y["teryt_powiat"]), rid
        n += 1
    assert n >= 20 and len(OLD) >= 21      # ADR 0278 (#150) adds 3 defined-only tiles to regions.REGIONS


def test_crs_and_location():
    assert regions.WORK_CRS == "EPSG:2180" and PLAN["crs"] == "EPSG:2180"
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    for rid in NEW:
        r = regions.get(rid)
        lon, lat = tr.transform(*r.origin)
        assert 22.6 < lon < 23.0 and 53.15 < lat < 53.47, rid       # inside the Overpass query bbox
    # town nodes of OSM fall into the tiles named after them
    towns = {n["tags"]["name"]: n for n in EXTRACT["nodes"] if n["tags"].get("place") == "town"}
    tr2 = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    for name, rid in (("Mońki", "monki"), ("Tykocin", "tykocin")):
        x, y = tr2.transform(*towns[name]["lonlat"])
        b = regions.get(rid).bbox
        assert b[0] <= x <= b[2] and b[1] <= y <= b[3], name


# ----------------------------------------------------------------------------------------------- through roads
def test_through_road_is_one_chain_per_tile():
    for t in PLAN["tiles"]:
        th = t["through"]
        assert th["single_chain"] and th["length_m"] > 50.0, t["id"]
        assert len(th["entry"]) == 1, t["id"]
        assert len(th["exit"]) == (1 if t["next"] else 0), t["id"]
        if not t["next"]:                                          # end of the ring: the road leaves by another edge
            assert len(th["other_crossings"]) == 1, t["id"]
        else:
            assert th["other_crossings"] == [], t["id"]
        ch = LineString(th["chain"])
        e = th["entry"][0]
        assert ch.coords[0] == (e["x"], e["y"])
        ends = th["exit"] or th["other_crossings"]
        assert ch.coords[-1] == (ends[0]["x"], ends[0]["y"])


def test_seams_inside_ring_continuous():
    assert len(PLAN["seams"]) == sum(len(c["tiles"]) - 1 for c in PLAN["corridors"].values())
    for s in PLAN["seams"]:
        a, b = regions.get(s["a"]), regions.get(s["b"])
        assert RP._shared_edge(a.bbox, b.bbox) == s["edge_of_a"]
        assert s["a_exit"] and len(s["a_exit"]) == len(s["b_entry"]) == 1
        x, y = s["a_exit"][0], s["b_entry"][0]
        assert (x["osm_way"], x["x"], x["y"]) == (y["osm_way"], y["x"], y["y"]), s


def test_seams_with_built_tiles_match_their_graph():
    """Entry of the first ring tile = boundary node of the same OSM way in the built neighbour's roads.graph.json."""
    want = {"dk65-monki": ("dk65-monki-01", "W"), "dw671-tykocin": ("dw671-tykocin-01", "S"),
            "dw671-jasionowka": ("knyszyn", "N")}
    for cname, (built, edge) in want.items():
        first = regions.get(PLAN["corridors"][cname]["tiles"][0])
        b = regions.get(built)
        assert RP._shared_edge(b.bbox, first.bbox) == edge
        g = [d for d in RP._graph_crossings(built, edge, b.bbox) if d["ref"] == RP.CORRIDORS[cname]["ref"]]
        e = TILE[first.id]["through"]["entry"]
        assert len(g) == len(e) == 1, cname
        assert g[0]["osm_way"] == e[0]["osm_way"], cname
        assert abs(g[0]["x"] - e[0]["x"]) < 0.5 and abs(g[0]["y"] - e[0]["y"]) < 0.5, cname


def test_every_ref_road_crossing_between_any_two_defined_tiles_is_on_both_sides():
    """DK65/DW671 crossings of every shared edge between two regions (new-new and new-old) from the extract: none is
    lost at a seam the plan does not list (e.g. dw671-jasionowka-01 touches dk65-monki-01 on x = 760587)."""
    tr = RP._tr()
    roads = [LineString([tr.transform(*p) for p in w["lonlat"]]) for w in EXTRACT["ways"]
             if "highway" in w["tags"] and {"65", "671"} & set(RP.refs(w["tags"]))
             and w["tags"]["highway"] not in ("construction", "proposed")]
    listed = {(s["a"], s["b"]) for s in PLAN["seams"]} | {(s["built"], s["new"]) for s in PLAN["existing_seams"]}
    # ADR 0288: the loop S8 <-> DW671 <-> Tykocin closes on the ring here - DW671 leaves `tykocin` westwards into
    # dw671-jezewo-03 (defined after the ring plan; docs/reports/map/s8_loop_plan.json)
    listed |= {("tykocin", "dw671-jezewo-03")}
    for a, b in combinations(regions.REGIONS.values(), 2):
        if a.id not in NEW and b.id not in NEW:
            continue
        edge = RP._shared_edge(a.bbox, b.bbox)
        if edge is None:
            continue
        line = box(*a.bbox).intersection(box(*b.bbox))
        hits = [p for r in roads for p in RP._points(r.intersection(line))]
        if (a.id, b.id) in listed or (b.id, a.id) in listed:
            assert len(hits) == 1, (a.id, b.id, hits)
        else:
            assert hits == [], (a.id, b.id, [(p.x, p.y) for p in hits])


# ----------------------------------------------------------------------------------------------- authored files
@pytest.mark.parametrize("rid", NEW)
def test_authored_files_present_and_consistent(rid):
    d, t = RDIR / rid, TILE[rid]
    src = json.loads((d / "sources.authored.json").read_text(encoding="utf-8"))
    assert src["pins"] == {"nmt_year": "2022"} and "authored_override" in src["provenance"]
    gf = json.loads((d / "graph_filter.authored.json").read_text(encoding="utf-8"))
    ref = json.loads((RDIR / "dk65-monki-01" / "graph_filter.authored.json").read_text(encoding="utf-8"))
    assert gf["drop_service"] == ref["drop_service"] and gf["drop_osm_ways"] == []
    rt = json.loads((d / "route_endpoints.json").read_text(encoding="utf-8"))
    e = t["through"]["entry"][0]
    ends = t["through"]["exit"] or t["through"]["other_crossings"]
    assert rt["start_epsg2180"] == [e["x"], e["y"]] and rt["end_epsg2180"] == [ends[0]["x"], ends[0]["y"]]
    ov = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    built = (d / "region.yaml").exists()
    # Region-wide rule overrides (e.g. ADR 0196/0336 facade_rules, ADR 0185 building_rules, ADR 0216 lamp_policy)
    # apply to the whole tile via explicit rule flags instead of per-feature `target` + `set`.
    # ADR 0349: `pavement_rules` (kerb drops / tactile paving / driveway colour, opt-in per tile) is region-wide too.
    region_rule_kinds = {"facade_rules", "building_rules", "lamp_policy", "pavement_rules"}
    meta_keys = {"id", "kind", "reason", "confidence", "verify", "sources", "status_note"}
    for o in ov:
        if o.get("kind") in region_rule_kinds:
            assert {"id", "kind", "reason", "confidence", "verify"} <= set(o), (rid, o.get("id"))
            assert set(o) - meta_keys, (rid, o.get("id"))
        elif o.get("kind") == "sidewalk_surface":
            # ADR 0237: an explicit surface applies to a polygon or to the sidewalks of selected OSM ways.
            assert {"id", "surface", "reason", "confidence", "verify"} <= set(o), (rid, o.get("id"))
            assert o.get("polygon_en") or o.get("polygon_epsg2180") or (o.get("target") or {}).get("osm_way"), o["id"]
        else:
            assert {"id", "target", "reason", "confidence", "verify", "set"} <= set(o), (rid, o.get("id"))
        if o["id"] in SEED_OVERRIDE_IDS and not built:
            assert o["confidence"] == "low"                       # nothing measured in these tiles before the ingest
        assert o["confidence"] in ("low", "medium", "high")
    seed = [o for o in ov if o["id"] in SEED_OVERRIDE_IDS]       # the definition overrides; later ones may target more
    for o in seed:
        assert set(o["target"]["osm_way"]) <= {w["osm_way"] for w in t["through"]["ways"]}
    if t["through"]["ref"] == "671":
        assert seed == []                                         # DW671: BDOT10k width, no edge lines (ADR 0212)
    if not built:
        # definition only: no product of build_region is committed half-way
        assert ov == seed
        assert not any((d / f).exists() for f in ("roads.graph.json", "terrain.json", "buildings.geojson",
                                                  "build_manifest.json", "route_start.json", "generated"))
        return
    # built by the lead (build_region wrote region.yaml from the regions.py entry; the authored files above survived)
    y = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    r = regions.get(rid)
    assert y["id"] == rid and y["title"] == r.title and y["status"] == r.status and "not built" not in y["status"]
    assert r.bbox == (y["bbox"]["xmin"], y["bbox"]["ymin"], y["bbox"]["xmax"], y["bbox"]["ymax"])
    assert (y["bbox"]["width_m"], y["bbox"]["height_m"]) == (2048, 2048)
    assert r.origin == (y["origin"]["x"], y["origin"]["y"]) and isinstance(y["origin"]["z"], float)
    assert y["crs"]["horizontal"].startswith("EPSG:2180") and "EVRF2007" in y["crs"]["vertical"]
    assert str(y["teryt_powiat"]) == r.teryt_powiat
    assert [str(x) for x in y.get("teryt_powiat_extra", [])] == list(r.teryt_powiat_extra)
    ids = [x["id"] for x in y["sources"]]
    assert f"gugik-nmt-2022-{rid}" in ids                         # the authored pin was honoured (ADR 0209)
    for k in [r.teryt_powiat, *r.teryt_powiat_extra]:
        assert {f"gugik-bdot10k-{k}", f"gugik-lod1-2024-{k}", f"gugik-lod2-2017-{k}"} <= set(ids)
    for x in y["sources"]:                                        # every source: manifest in git with the pinned hash
        assert (REPO / x["manifest"]).exists() and len(x["manifest_sha256"]) == 64, (rid, x["id"])
    assert (d / "roads.graph.json").exists() and (d / "build_manifest.json").exists()


def test_built_ring_tiles_are_in_the_region_catalog():
    """After build_region + export-route.py of a ring tile, the start-menu catalog needs its entry (id + label by hand,
    then scripts/export-region-catalog.py - ADR 0229 / 0267). Vacuous while no ring tile has a route_start.json."""
    cat = json.loads((REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json").read_text("utf-8"))
    ids = {r["id"] for r in cat["regions"]}
    missing = [rid for rid in NEW if (RDIR / rid / "route_start.json").exists() and rid not in ids]
    assert not missing, f"add to region_catalog.json and run scripts/export-region-catalog.py: {missing}"


def test_nmt_2022_covers_every_ring_tile():
    cov = json.loads(RP.NMT.read_text(encoding="utf-8"))["tiles"]
    assert sorted(cov) == sorted(NEW)
    for rid in NEW:
        assert cov[rid]["by_year"]["2022"]["sheets"], rid
    for rid in ("dk65-monki-01", "dw671-tykocin-01"):            # the built neighbours use the same series
        assert json.loads((RDIR / rid / "sources.authored.json").read_text(encoding="utf-8"))["pins"]["nmt_year"] == "2022"
    assert (REPO / "Data" / "SourceManifests" / "gugik-nmt-2022-knyszyn.json").exists()   # knyszyn: 2022 without a pin


def test_dk65_cross_section_same_on_both_sides_of_every_seam():
    pairs = [(s["a"], s["b"], s["a_exit"][0]["osm_way"]) for s in PLAN["seams"]]
    pairs += [(s["built"], s["new"], s["new_entry"][0]["osm_way"]) for s in PLAN["existing_seams"]]
    for a, b, way in pairs:
        assert _sets_for_way(a, way) == _sets_for_way(b, way), (a, b, way)
    # DK65 continues the set of dk65-monki-01 (ADR 0212) on its rural ways
    assert _sets_for_way("dk65-monki-02", 98070954) == {**RP.DK65_SET, "lamps": False}
