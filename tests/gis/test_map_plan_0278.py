"""ADR 0278: map plan after d67-full + the ring of ADR 0231 and the rough definition of its first 3 tiles
(bialystok-porosly, dk8-s8-jeroniki, bialystok-dojlidy-gorne). Data in git only (no Data/raw, no network): deterministic
plan, sources and manifest, registry entries, lattice / CRS / overlap with built and ring tiles, order grows over seams,
control routes chained, seams == boundary nodes of the built neighbours' roads.graph.json, authored files (two states:
definition / built), no names of firms in the extract."""
from __future__ import annotations

import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import pytest
import yaml
from pyproj import Transformer
from shapely.geometry import box

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
import map_plan_0278 as MP  # noqa: E402
import regions  # noqa: E402

RDIR = REPO / "Data" / "Regions"
PLAN = json.loads(MP.PLAN.read_text(encoding="utf-8"))
EXTRACT = json.loads(MP.EXTRACT.read_text(encoding="utf-8"))
GUGIK = json.loads(MP.GUGIK.read_text(encoding="utf-8"))
BUDGET = json.loads(MP.BUDGET.read_text(encoding="utf-8"))
NEW = [o["id"] for o in PLAN["order"] if o["define_now"]]
CAND = {t["id"]: t for t in PLAN["candidates"]}


# ----------------------------------------------------------------------------------------------- plan / sources
def test_plan_is_deterministic_and_matches_git():
    assert MP.build_plan(EXTRACT, GUGIK, BUDGET) == PLAN


def test_extract_hash_matches_manifest_and_sources_are_allowed():
    man = json.loads(MP.MANIFEST.read_text(encoding="utf-8"))
    ex = man["extract_in_git"]
    assert ex["path"] == MP.EXTRACT.relative_to(REPO).as_posix()
    assert hashlib.sha256(MP.EXTRACT.read_bytes()).hexdigest() == ex["sha256"]
    assert man["license"] == "ODbL 1.0" and "OpenStreetMap" in man["attribution"]
    assert len(man["raw_answers"]["sha256"]) >= len(EXTRACT["tiles"]) + len(MP.ROUTE_RELATIONS)
    assert all(len(v) == 64 for v in man["raw_answers"]["sha256"].values())
    ua = man["client"]["user_agent"].lower()
    assert "kamion" not in ua and "truck" not in ua and "@" not in ua
    for p in (MP.MANIFEST, MP.EXTRACT, MP.GUGIK):                 # ADR 0002: no Google endpoint in any input
        assert "google." not in p.read_text(encoding="utf-8").lower() and "googleapis" not in p.read_text(encoding="utf-8").lower()
    assert GUGIK["index_services"] and all(u.startswith("https://mapy.geoportal.gov.pl/") for u in GUGIK["index_services"].values())
    assert "nothing downloaded" in GUGIK["method"]


def test_extract_has_categories_not_names():
    """Truck targets are kept as categories + points (no name/brand/operator); place names only from place=* nodes."""
    for tid, t in EXTRACT["tiles"].items():
        for d in t["targets"]:
            assert set(d) <= {"cat", "osm", "x", "y", "area_m2"}, (tid, d)
            assert d["cat"] in MP.TARGET_CATS
        assert all(p.endswith(")") for p in t["places"])
    for w in EXTRACT["ways"]:
        assert set(w["tags"]) <= set(MP.TAGS_KEPT) and "highway" in w["tags"]
        assert not {"brand", "operator"} & set(w["tags"])


def test_budget_snapshot_and_classes():
    ids = {b["id"] for b in BUDGET["tiles"]}
    assert len(ids) >= 21 and ids <= set(MP.built_regions())
    cls = PLAN["budget_classes"]
    assert sum(len(c["tiles"]) for c in cls.values()) == len(BUDGET["tiles"])
    for c in cls.values():
        assert c["median"]["static_tris_high"] > 8e6 and c["median"]["frame_tris_high_max"] > 1e6
    for t in PLAN["candidates"]:
        assert t["budget_estimate"]["status"].startswith("ESTIMATED")


# ----------------------------------------------------------------------------------------------- registry
def test_new_entries_generated_from_plan():
    assert NEW == ["bialystok-porosly", "dk8-s8-jeroniki", "bialystok-dojlidy-gorne"] and MP.DEFINE_FIRST == 3
    for rid in NEW:
        r, t = regions.get(rid), CAND[rid]
        assert r.bbox == tuple(t["bbox"]) and r.origin == tuple(t["origin"])
        assert r.teryt_powiat == t["teryt_powiat"] and list(r.teryt_powiat_extra) == t["teryt_powiat_extra"]
        assert r.title == MP.TITLES[rid] and "ADR 0278" in r.status and "not built" not in r.status
        assert r.water is False and r.rail is False
    assert regions.get("bialystok-porosly").powiaty == ("2002", "2061")
    assert regions.get("bialystok-dojlidy-gorne").powiaty == ("2061", "2002")        # 0.4 % in 2002: ADR 0219 rule
    import powiaty as PW
    for rid in NEW:
        assert PW.powiaty_for_bbox(regions.get(rid).bbox) == regions.get(rid).powiaty


def test_ids_unique_and_titles_unique():
    assert all(k == r.id for k, r in regions.REGIONS.items())
    titles = [r.title for r in regions.REGIONS.values()]
    assert len(titles) == len(set(titles))


def test_tile_size_lattice_and_origin():
    for rid in NEW:
        r = regions.get(rid)
        assert r.width == r.height == regions.TILE_SIZE_M == 2048.0
        i, j = (r.bbox[0] - MP.X0) / MP.T, (r.bbox[1] - MP.Y0) / MP.T
        assert i == int(i) and j == int(j) and [int(i), int(j)] == CAND[rid]["ij"]
        assert r.origin == ((r.bbox[0] + r.bbox[2]) / 2, (r.bbox[1] + r.bbox[3]) / 2)
        assert all(isinstance(v, float) for v in r.bbox + r.origin)


def test_no_overlap_with_built_ring_or_each_other():
    allr = list(regions.REGIONS.values())
    for a, b in combinations(allr, 2):
        assert a.bbox != b.bbox, (a.id, b.id)
        assert box(*a.bbox).intersection(box(*b.bbox)).area == 0.0, (a.id, b.id)
    taken = set(MP.built_regions().values()) | set(MP.RING_0231.values())
    cells = [tuple(t["ij"]) for t in PLAN["candidates"]]
    assert len(cells) == len(set(cells)) and not set(cells) & taken
    assert not set(NEW) & set(MP.RING_0231)


def test_existing_entries_unchanged():
    """Every region built before ADR 0278 still has the bbox / origin / powiat of its region.yaml."""
    n = 0
    for rid in sorted(set(regions.REGIONS) - set(NEW)):
        p = RDIR / rid / "region.yaml"
        if not p.exists():
            continue
        y = yaml.safe_load(p.read_text(encoding="utf-8"))
        r = regions.get(rid)
        assert r.bbox == (y["bbox"]["xmin"], y["bbox"]["ymin"], y["bbox"]["xmax"], y["bbox"]["ymax"]), rid
        assert r.origin == (y["origin"]["x"], y["origin"]["y"]) and r.teryt_powiat == str(y["teryt_powiat"]), rid
        n += 1
    assert n >= 21


def test_crs_and_location():
    assert regions.WORK_CRS == "EPSG:2180" and PLAN["crs"] == "EPSG:2180"
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    for rid in NEW:
        lon, lat = tr.transform(*regions.get(rid).origin)
        assert 22.95 < lon < 23.30 and 53.05 < lat < 53.20, rid           # Białystok and its western edge
    want = {"bialystok-porosly": "Porosły", "dk8-s8-jeroniki": "Jeroniki", "bialystok-dojlidy-gorne": "Dojlidy Górne"}
    for rid, name in want.items():
        assert any(p.startswith(name + " (") for p in CAND[rid]["places"]), rid


# ----------------------------------------------------------------------------------------------- order / routes / seams
def test_order_grows_over_numbered_road_seams():
    o = PLAN["order"]
    assert 10 <= len(o) <= 20 and len({x["id"] for x in o}) == len(o)
    assert [x["n"] for x in o] == list(range(1, len(o) + 1))
    for x in o:
        assert x["connected_via"], x["id"]                          # touches a built / ring / earlier tile over a road
        assert x["id"] in CAND and x["why"]
    assert [x["id"] for x in o if x["define_now"]] == NEW


def test_control_routes_found_and_chained():
    d = PLAN["defined"]
    assert set(d) == set(NEW) and all(r["found"] for r in d.values())
    # dk8-s8-jeroniki ends where bialystok-porosly starts: same OSM way, same point
    a, b = d["dk8-s8-jeroniki"]["exit"], d["bialystok-porosly"]["entry"]
    assert (a["osm_way"], a["x"], a["y"]) == (b["osm_way"], b["x"], b["y"])
    for rid, r in d.items():
        bb = regions.get(rid).bbox
        assert MP._edge_of(bb, r["entry"]["x"], r["entry"]["y"]) == r["edge_in"]
        assert MP._edge_of(bb, r["exit"]["x"], r["exit"]["y"]) == r["edge_out"]
        assert r["chain"][0] != r["chain"][-1] and 1000.0 < r["length_m"] < 4000.0
    assert set(MP.refs(d["bialystok-porosly"]["exit"])) == {"8", "65"}
    assert "19" in MP.refs(d["bialystok-dojlidy-gorne"]["exit"])


def test_seams_with_built_tiles_match_their_graph():
    """Every major road crossing a shared edge (extract, OSM 2026-11-16) is a boundary node of the same OSM way in the
    built neighbour's roads.graph.json (pinned pbf 2026-11-08) within 0.5 m, and vice versa."""
    want = {("bialystok-porosly", "bialystok-knyszynska"), ("dk8-s8-jeroniki", "dk65-01"),
            ("bialystok-dojlidy-gorne", "bialystok-dojlidy")}
    got = {(s["new"], s["built"]) for s in PLAN["seams_defined"]}
    assert want <= got
    for s in PLAN["seams_defined"]:
        assert s["crossings"], s
        for c in s["crossings"]:
            assert c["graph_offset_m"] is not None and c["graph_offset_m"] < 0.5, (s["new"], s["built"], c)
        assert {c["osm_way"] for c in s["crossings"] if c["highway"] in MP.MAJOR} == set(s["built_graph_major_ways"]), s
    # the control routes enter / leave built tiles on boundary nodes of their graphs
    for rid, key, built in (("dk8-s8-jeroniki", "entry", "dk65-01"), ("bialystok-porosly", "exit", "bialystok-knyszynska"),
                            ("bialystok-dojlidy-gorne", "entry", "bialystok-dojlidy")):
        p = PLAN["defined"][rid][key]
        e = MP.shared_edge(regions.get(built).bbox, regions.get(rid).bbox)
        g = MP.graph_crossings(built, e)
        assert any(q["osm_way"] == p["osm_way"] and abs(q["x"] - p["x"]) < 0.5 and abs(q["y"] - p["y"]) < 0.5 for q in g), rid


# ----------------------------------------------------------------------------------------------- authored files
@pytest.mark.parametrize("rid", ["bialystok-porosly", "dk8-s8-jeroniki", "bialystok-dojlidy-gorne"])
def test_authored_files_present_and_consistent(rid):
    d = RDIR / rid
    src = json.loads((d / "sources.authored.json").read_text(encoding="utf-8"))
    pin = MP.PINS[rid][0]
    assert src["pins"] == {"nmt_year": pin} and "authored_override" in src["provenance"]
    assert pin in GUGIK["tiles"][rid]["nmt_years_full_cover"]                  # the pinned series covers the tile
    neighbour = {"bialystok-porosly": "bialystok-knyszynska", "dk8-s8-jeroniki": "dk65-01",
                 "bialystok-dojlidy-gorne": "bialystok-dojlidy"}[rid]
    assert (REPO / "Data" / "SourceManifests" / f"gugik-nmt-{pin}-{neighbour}.json").exists()   # same series as the seam
    rt = json.loads((d / "route_endpoints.json").read_text(encoding="utf-8"))
    r = PLAN["defined"][rid]
    assert rt["start_epsg2180"] == [r["entry"]["x"], r["entry"]["y"]] and rt["end_epsg2180"] == [r["exit"]["x"], r["exit"]["y"]]
    assert "authored_override" in rt["provenance"]
    ov = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    for o in ov:
        need = {"id", "reason", "confidence", "verify"} | (set() if o.get("kind") == "facade_rules" else {"target"})   # facade_rules = region-wide opt-in, no target (props-fix-s24)
        assert need <= set(o), (rid, o.get("id"))
    built = (d / "region.yaml").exists()
    if not built:
        assert ov == []                                                         # definition: nothing measured yet
        assert not any((d / f).exists() for f in ("roads.graph.json", "terrain.json", "buildings.geojson",
                                                  "build_manifest.json", "route_start.json", "generated"))
        return
    # built by the lead: region.yaml written by build_region from the regions.py entry; authored files survived
    y = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    reg = regions.get(rid)
    assert y["id"] == rid and y["title"] == reg.title and y["status"] == reg.status
    assert reg.bbox == (y["bbox"]["xmin"], y["bbox"]["ymin"], y["bbox"]["xmax"], y["bbox"]["ymax"])
    assert reg.origin == (y["origin"]["x"], y["origin"]["y"]) and isinstance(y["origin"]["z"], float)
    assert y["crs"]["horizontal"].startswith("EPSG:2180") and "EVRF2007" in y["crs"]["vertical"]
    assert [str(x) for x in y.get("teryt_powiat_extra", [])] == list(reg.teryt_powiat_extra)
    ids = [x["id"] for x in y["sources"]]
    assert f"gugik-nmt-{pin}-{rid}" in ids                                      # the authored pin was honoured
    for k in reg.powiaty:
        assert {f"gugik-bdot10k-{k}", f"gugik-lod1-2024-{k}", f"gugik-lod2-2017-{k}"} <= set(ids)
    assert (d / "roads.graph.json").exists() and (d / "build_manifest.json").exists()


def test_built_plan_tiles_are_in_the_region_catalog():
    """After build_region + export-route.py the start-menu catalog needs the tile (ADR 0229 / 0267). Vacuous before."""
    cat = json.loads((REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json").read_text("utf-8"))
    ids = {r["id"] for r in cat["regions"]}
    missing = [rid for rid in NEW if (RDIR / rid / "route_start.json").exists() and rid not in ids]
    assert not missing, f"add to region_catalog.json and run scripts/export-region-catalog.py: {missing}"


# ----------------------------------------------------------------------------------------------- data cost / podlasie
def test_gugik_cost_per_candidate():
    for tid, g in GUGIK["tiles"].items():
        assert tid in CAND
        assert g["nmt_default"]["sheets"] and g["orto_0p25"]["sheets"], tid
        n = g["nmt_default"]
        assert n["on_disk"] + n["to_download"] == len(n["sheets"])
        assert "ESTIMATED" in n["size_status"]
        assert set(g["powiat_datasets_in_manifests"]) == set(CAND[tid]["powiat_area_share"])
        for ok in g["powiat_datasets_in_manifests"].values():
            assert all(ok.values())                                             # 2002 / 2061 already on the lead's disk


def test_podlasie_assessment_from_relations():
    p = PLAN["podlasie"]
    ring = {tuple(v) for v in MP.RING_0231.values()}
    for k in ("monki_grajewo_dk65", "tykocin_to_s8_dw671", "s8_tykocin_junction_to_zambrow", "s8_bialystok_to_tykocin_junction"):
        assert p[k]["tiles"] == len(p[k]["cells"]) > 0 and p[k]["status"].startswith("ESTIMATED")
        assert not {tuple(c["ij"]) for c in p[k]["cells"]} & ring
    assert [-24, 25] in [c["ij"] for c in p["monki_grajewo_dk65"]["cells"]]       # ends in the Grajewo town tile
    assert all(all(x.startswith("motorway") for x in c["kinds"]) for c in p["s8_tykocin_junction_to_zambrow"]["cells"])
