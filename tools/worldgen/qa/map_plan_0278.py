"""ADR 0278 (D63 "najpierw przejezdne"): plan of the next tiles after d67-full + the ring of ADR 0231 - Bialystok further
(S8 west, the 40 t transit corridor C <-> Dojlidy, DK19 south, DK65 east, DK8/DK19 north, centre) and an assessment of
the Podlasie corridors (Monki -> Grajewo, Tykocin -> Zambrow) - on the 2048 m lattice of ADR 0203.

    uv run --project tools/worldgen python tools/worldgen/qa/map_plan_0278.py                  # inputs in git -> plan json
    uv run --project tools/worldgen python tools/worldgen/qa/map_plan_0278.py --png            # + control render
    uv run --project tools/worldgen python tools/worldgen/qa/map_plan_0278.py --print-regions  # regions.py entries (first 3)
    uv run --project tools/worldgen python tools/worldgen/qa/map_plan_0278.py --init-regions   # authored files (missing only)
    ... --extract <raw dir>          # OSM API 0.6 answers (gzip) -> Data/Plans/map-plan-0278/osm_plan_extract.json + manifest
    ... --gugik <index json>         # GUGiK sheet index rows -> docs/reports/map/map_plan_0278_gugik.json
    ... --budget-snapshot            # Data/Regions/*/generated (built tiles) -> docs/reports/map/map_plan_0278_budget.json

Inputs in git (the plan stage is deterministic: no network, no clock, no Data/raw):
  Data/Plans/map-plan-0278/osm_plan_extract.json  OSM (ODbL): per candidate tile the truck-target counts and points
      (categories only - no names of firms or brands), place names, building counts; major road ways of the window;
      per lattice cell lengths of the route relations DK8 (with S8), DK19, DK65, DW671, DW678.
  docs/reports/map/map_plan_0278_gugik.json        GUGiK sheet index (NMT, ORTO, NMPT) per candidate tile vs the
      manifests of Data/SourceManifests (= what lies on the lead's disk).
  docs/reports/map/map_plan_0278_budget.json       triangle / chunk / memory figures of the built tiles (snapshot of
      generated/*, so a later regeneration does not change the plan; refresh with --budget-snapshot).
  Data/Admin/powiaty_prg.geojson                   powiat polygons (PRG, EPSG:2180).
  Data/Regions/<built>/roads.graph.json            boundary nodes of the built neighbours (seams).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, box, shape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import regions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
ADR = "0278"
PLANS = REPO / "Data" / "Plans" / "map-plan-0278"
EXTRACT = PLANS / "osm_plan_extract.json"
MANIFEST = REPO / "Data" / "SourceManifests" / "osm-api06-map-plan-0278.json"
GUGIK = REPO / "docs" / "reports" / "map" / "map_plan_0278_gugik.json"
BUDGET = REPO / "docs" / "reports" / "map" / "map_plan_0278_budget.json"
PLAN = REPO / "docs" / "reports" / "map" / "map_plan_0278.json"
PNG = REPO / "docs" / "reports" / "map" / "map_plan_0278.png"
PRG = REPO / "Data" / "Admin" / "powiaty_prg.geojson"
REG = REPO / "Data" / "Regions"
MAN_DIR = REPO / "Data" / "SourceManifests"
C = regions.REGIONS["bialystok-industrial-c"]
X0, Y0 = C.bbox[0], C.bbox[1]
T = regions.TILE_SIZE_M
GENERIC_UA = "osm-research-client/1.0"
EXTRA_POWIAT_MIN_SHARE = 0.0       # ADR 0219: every powiat the tile overlaps (powiaty.powiaty_for_bbox)
API = "https://api.openstreetmap.org/api/0.6"

# Tiles of the ring of ADR 0231 (PR #115; owner: part of d67-full). Not in main when this ADR was written, so listed
# here: the plan must not propose them (and no candidate may overlap them).
RING_0231 = {
    "dk65-monki-02": (-10, 9), "dk65-monki-03": (-10, 10), "dk65-monki-04": (-11, 10), "dk65-monki-05": (-11, 11),
    "dk65-monki-06": (-12, 11), "dk65-monki-07": (-12, 12), "monki-e": (-12, 13), "monki": (-13, 13),
    "dw671-tykocin-02": (-9, 6), "dw671-tykocin-03": (-10, 6), "dw671-tykocin-04": (-10, 5), "dw671-tykocin-05": (-11, 5),
    "dw671-tykocin-06": (-11, 4), "dw671-tykocin-07": (-12, 4), "dw671-tykocin-08": (-12, 3), "dw671-tykocin-09": (-13, 3),
    "tykocin": (-13, 2), "dw671-jasionowka-01": (-8, 9),
}

# Candidate tiles (lattice i, j) for which the OSM API 0.6 map call was made, the id the plan gives them and the group
# (corridor) they serve. Ids = names of OSM place=* nodes inside the tile (no firm names).
CANDIDATES: dict[str, dict] = {
    "bialystok-porosly":       {"ij": (-3, -1), "group": "s8-zachod"},
    "dk8-s8-jeroniki":         {"ij": (-4, -1), "group": "s8-zachod"},
    "bialystok-bacieczki":     {"ij": (-2, -1), "group": "s8-zachod"},
    "bialystok-dojlidy-gorne": {"ij": (2, -3), "group": "dk19-poludnie"},
    "bialystok-krywlany":      {"ij": (0, -3), "group": "g10-c-dojlidy"},
    "bialystok-mickiewicza":   {"ij": (1, -2), "group": "g10-c-dojlidy"},
    "bialystok-skorupy":       {"ij": (2, -2), "group": "g10-c-dojlidy"},
    "bialystok-pieczurki":     {"ij": (2, -1), "group": "g10-c-dojlidy"},
    "bialystok-bojary":        {"ij": (1, -1), "group": "g10-c-dojlidy"},
    "bialystok-wygoda":        {"ij": (1, 0), "group": "g10-c-dojlidy"},
    "bialystok-centrum":       {"ij": (0, -1), "group": "centrum"},
    "bialystok-piaski":        {"ij": (0, -2), "group": "centrum"},
    "bialystok-antoniuk":      {"ij": (-1, -1), "group": "centrum"},
    "bialystok-bagnowka":      {"ij": (2, 0), "group": "dk65-wschod"},
    "dk8-dk19-pn-01":          {"ij": (0, 1), "group": "dk8-dk19-polnoc"},
    "dk8-dk19-jurowce":        {"ij": (0, 2), "group": "dk8-dk19-polnoc"},
    "dk8-sochonie":            {"ij": (0, 3), "group": "dk8-dk19-polnoc"},
    "dk8-woroszyly":           {"ij": (0, 4), "group": "dk8-dk19-polnoc"},
    "bialystok-pietrasze":     {"ij": (1, 1), "group": "dk8-dk19-polnoc"},
    "wasilkow":                {"ij": (1, 2), "group": "dk8-dk19-polnoc"},
    "dk19-jakimy":             {"ij": (1, 3), "group": "dk8-dk19-polnoc"},
}
# map calls made for calibration only (built tiles: OSM building count vs buildings.geojson of the pipeline)
CALIBRATION = {"bialystok-industrial-c": (0, 0), "bialystok-maczka": (-1, 0), "dk65-05": (-5, 3)}
# town tiles at the end of the Podlasie corridors (targets of the route assessment, not tiles of this plan)
TOWNS = {"grajewo": (-24, 25), "zambrow": (-29, -11)}

# Order of the plan (D63: drivable first). Hand-ordered from the metrics of the plan json (reasons in ADR 0278); the plan
# stage records for every tile the seams over which it touches a built tile, a ring tile or an earlier tile.
ORDER: list[tuple[str, str]] = [
    ("bialystok-porosly", "DK8 Kleeberga (40 t in the 2018 city plan) from the S edge of bialystok-knyszynska towards the S8; largest industrial area of all candidates"),
    ("dk8-s8-jeroniki", "DK8 -> S8 junction, seam with dk65-01 (S8 + slip roads): closes the loop S8 - Kleeberga - Szosa Knyszynska and joins C (Maczka/Kleeberga) to the S8 towards Warsaw"),
    ("bialystok-dojlidy-gorne", "Kuronia (the >3.5 t transit since 2025-12, research G10) from the E edge of Dojlidy to DK19 south; second highest count of halls >= 1000 m2"),
    ("bialystok-krywlany", "Ciolkowskiego DW678 + Dywizjonu 303 at the W edge of Dojlidy (the Dojlidy route starts there); first tile of the truck route C <-> Dojlidy"),
    ("bialystok-mickiewicza", "DK19 Branickiego / rondo Meyera / Ciolkowskiego DW678; seams with Dojlidy (N edge) and krywlany"),
    ("bialystok-bojary", "DK19/DK65 Andersa - Sosabowskiego - DK19 Piastowska, 26 ha industrial; truck route C <-> Dojlidy"),
    ("bialystok-wygoda", "corner tile: Andersa leaves C through it (66 m of the route) - closes C <-> Dojlidy; dense housing = highest budget risk"),
    ("bialystok-skorupy", "Ciolkowskiego / Sulika (DK65) / DK19 south, 49 ha industrial; second link to Dojlidy-Gorne"),
    ("bialystok-pieczurki", "DK65 Sulika, 22 ha industrial; start of the DK65 exit east (Bobrowniki)"),
    ("dk8-dk19-pn-01", "DK8/DK19 north of C (N edge of C); few targets, cheap, start of the north exits"),
    ("dk8-dk19-jurowce", "DK8/DK19 north, 16 ha industrial (Jurowce)"),
    ("dk8-sochonie", "DK8 north towards Augustow, 14 ha industrial; DK19 turns east here"),
    ("bialystok-bacieczki", "fills the hole S of bialystok-kleeberga between Kleeberga and the centre (DW669 / DW676)"),
    ("bialystok-centrum", "S edge of C: Al. Tysiaclecia DW675 to the station area; for trucks the centre is the 3.5 t zone of the 2018 city plan (G10)"),
]
DEFINE_FIRST = 3

# Control route of the defined tiles (authored route_endpoints.json): entry edge + the tile it comes from, exit edge +
# the tile it goes to, road refs of the exit. Direction = inbound (S8 -> Kleeberga; Dojlidy -> DK19 is outbound south).
THROUGH = {
    "dk8-s8-jeroniki": {"entry": ("N", "dk65-01"), "exit": ("E", "bialystok-porosly"), "refs": ("S8", "8")},
    "bialystok-porosly": {"entry": ("W", "dk8-s8-jeroniki"), "exit": ("N", "bialystok-knyszynska"), "refs": ("8",)},
    "bialystok-dojlidy-gorne": {"entry": ("W", "bialystok-dojlidy"), "exit": ("E", None), "refs": ("19",),
                                "entry_ways": (236885860, 275244659)},
}
DRIVING_ORDER = ("dk8-s8-jeroniki", "bialystok-porosly", "bialystok-dojlidy-gorne")
TITLES = {
    "bialystok-porosly": "Białystok — DK8 Kleeberga na południe od ronda Kresowian w stronę S8, strefa przemysłowa (Porosły)",
    "dk8-s8-jeroniki": "DK8 → S8 — węzeł na południe od dk65-01, łącznik ekspresówki z Kleeberga (Jeroniki, Sienkiewicze)",
    "bialystok-dojlidy-gorne": "Białystok — Kuronia na wschód od Dojlid do DK19 (Dojlidy Górne, Zagórki)",
}
# NMT survey year of each defined tile = the year of the built neighbour on the seam of its through road (ADR 0209)
PINS = {
    "dk8-s8-jeroniki": ("2025", "The S8 seam is shared with dk65-01, built from NMT 2025 (gugik-nmt-2025-dk65-01); the same series keeps the terrain of that edge identical."),
    "bialystok-porosly": ("2022", "The DK8 Kleeberga seam is shared with bialystok-knyszynska, built from NMT 2022 (gugik-nmt-2022-bialystok-knyszynska); the seam with dk8-s8-jeroniki (2025) then joins two series - seam taper of ADR 0275 or a common re-pin when the lead re-ingests knyszynska."),
    "bialystok-dojlidy-gorne": ("2025", "The Kuronia seam is shared with bialystok-dojlidy, built from NMT 2025 (gugik-nmt-2025-bialystok-dojlidy)."),
}

CAT_SHOP = ("supermarket", "mall", "doityourself", "wholesale", "department_store", "trade")
MAJOR = ("motorway", "trunk", "primary", "secondary", "tertiary", "motorway_link", "trunk_link", "primary_link",
         "secondary_link", "tertiary_link")
TAGS_KEPT = ("highway", "ref", "name", "oneway", "junction", "lanes", "maxspeed", "maxweight", "maxaxleload", "hgv",
             "bridge", "tunnel", "layer")
ROUTE_RELATIONS = {"8": 7843418, "19": 122101, "65": 336069, "671": 2324549, "678": 2324829}
TARGET_CATS = ("hall_1000m2", "warehouse", "works", "fuel", "fuel_hgv", "truck_parking", "services", "retail_delivery")


def tile_bbox(i: int, j: int) -> tuple[float, float, float, float]:
    return (X0 + T * i, Y0 + T * j, X0 + T * (i + 1), Y0 + T * (j + 1))


def ij_of(x: float, y: float) -> tuple[int, int]:
    return int(math.floor((x - X0) / T)), int(math.floor((y - Y0) / T))


def _tr() -> Transformer:
    return Transformer.from_crs("EPSG:4326", regions.WORK_CRS, always_xy=True)


def refs(tags: dict) -> list[str]:
    return [r.strip() for r in (tags.get("ref") or "").split(";") if r.strip()]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def built_regions() -> dict[str, tuple[int, int]]:
    """Regions of regions.py as lattice indices, without the tiles this plan defines (they are candidates)."""
    out = {}
    for r in regions.REGIONS.values():
        i, j = (r.bbox[0] - X0) / T, (r.bbox[1] - Y0) / T
        # ADR 0288 (D82) registered the loop tiles after this plan: they stay the plan's "podlasie" corridor, not "built";
        # ADR 0315 (s8-north-s24) built the plan cells (0,1)..(0,4) = dk8-dk19-pn-01 / -jurowce / dk8-sochonie /
        # dk8-woroszyly under the ids dk8-wasilkow-01..03 / dk8-korycin-01: same cells, the plan stays as committed
        if (i == int(i) and j == int(j) and r.id not in CANDIDATES and r.id not in RING_0231
                and "ADR 0288" not in r.status and "s8-north-s24" not in r.status):
            out[r.id] = (int(i), int(j))
    return out


# ---------------------------------------------------------------------------------------------- extract (needs raw)
def _maxweight(t: dict) -> float | None:
    v = t.get("maxweight")
    try:
        return float(v.replace("t", "").strip()) if v else None
    except ValueError:
        return None


def _categories(t: dict, area: float | None) -> list[str]:
    """Truck targets by category (ADR 0278 table "Kategorie celów"); OSM tags only, names never read."""
    out = []
    b = t.get("building")
    if b in ("industrial", "warehouse", "manufacture") and area is not None and area >= 1000.0:
        out.append("hall_1000m2")
    if b == "warehouse" or t.get("industrial") in ("warehouse", "logistics"):
        out.append("warehouse")
    if t.get("man_made") == "works":
        out.append("works")
    if t.get("amenity") == "fuel":
        out.append("fuel")
        if t.get("fuel:HGV_diesel") == "yes" or t.get("hgv") in ("yes", "designated"):
            out.append("fuel_hgv")
    if t.get("amenity") == "parking" and (t.get("hgv") in ("yes", "designated") or t.get("parking") == "truck"):
        out.append("truck_parking")
    if t.get("highway") in ("services", "rest_area"):
        out.append("services")
    if t.get("shop") in CAT_SHOP:
        out.append("retail_delivery")
    return out


def _tile_counts(elements: list[dict], bb, tr) -> tuple[dict, list[dict], list[str]]:
    nodes = {e["id"]: e for e in elements if e["type"] == "node"}
    tb = box(*bb)
    c: dict[str, float] = defaultdict(float)
    targets, places = [], set()

    def xy(n):
        return tr.transform(n["lon"], n["lat"])

    for n in nodes.values():
        t = n.get("tags")
        if not t:
            continue
        x, y = xy(n)
        if not tb.contains(Point(x, y)):
            continue
        if t.get("place") in ("city", "town", "village", "hamlet", "suburb", "quarter", "neighbourhood") and t.get("name"):
            places.add(f"{t['name']} ({t['place']})")
        for cat in _categories(t, None):
            c[cat] += 1
            targets.append({"cat": cat, "osm": f"n{n['id']}", "x": round(x, 1), "y": round(y, 1)})
    for w in (e for e in elements if e["type"] == "way"):
        t = w.get("tags") or {}
        pts = [xy(nodes[k]) for k in w["nodes"] if k in nodes]
        if len(pts) < 2:
            continue
        hw = t.get("highway")
        if hw in MAJOR:
            ln = LineString(pts).intersection(tb).length / 1000.0
            c[f"km_{hw.replace('_link', '')}"] += ln
            if t.get("hgv") in ("no", "destination", "delivery") or (_maxweight(t) or 99) < 40:
                c["km_major_hgv_restricted"] += ln
        if w["nodes"][0] != w["nodes"][-1] or len(pts) < 4:
            continue
        pg = Polygon(pts)
        if not pg.is_valid:
            pg = pg.buffer(0)
        if t.get("landuse") == "industrial":
            c["industrial_ha"] += pg.intersection(tb).area / 1e4
        if t.get("landuse") == "commercial":
            c["commercial_ha"] += pg.intersection(tb).area / 1e4
        cen = pg.representative_point()
        if not tb.contains(cen):
            continue
        if t.get("building"):
            c["buildings"] += 1
        for cat in _categories(t, pg.area):
            c[cat] += 1
            targets.append({"cat": cat, "osm": f"w{w['id']}", "x": round(cen.x, 1), "y": round(cen.y, 1),
                            "area_m2": round(pg.area)})
    out = {}
    for k, v in sorted(c.items()):
        out[k] = round(v, 2) if (k.startswith("km_") or k.endswith("_ha")) else int(v)
    return out, sorted(targets, key=lambda d: (d["cat"], d["osm"])), sorted(places)


def _read_raw(p: Path) -> tuple[dict, str, int]:
    """Raw API answer (stored gzip-compressed outside git): parsed json, SHA256 and size of the answer itself."""
    b = gzip.decompress(p.read_bytes()) if p.suffix == ".gz" else p.read_bytes()
    return json.loads(b), hashlib.sha256(b).hexdigest(), len(b)


def build_extract(raw: Path) -> tuple[dict, dict]:
    """OSM API 0.6 answers (outside git) -> the extract kept in git + its manifest."""
    tr = _tr()
    by_tile: dict[tuple[int, int], list[Path]] = defaultdict(list)
    for f in sorted((raw / "map").glob("t_*.json*")):
        m = re.match(r"t_(-?\d+)_(-?\d+)([a-d]*)\.json", f.name)
        by_tile[(int(m[1]), int(m[2]))].append(f)
    named = {**{k: v["ij"] for k, v in CANDIDATES.items()}, **CALIBRATION, **TOWNS}
    inv = {tuple(v): k for k, v in named.items()}
    tiles, ways, sources = {}, {}, []
    window = box(*tile_bbox(-5, -4)[:2], *tile_bbox(3, 5)[2:])
    for ij in sorted(by_tile):
        elements, seen = [], set()
        for f in sorted(by_tile[ij]):
            d, sha, size = _read_raw(f)
            q = re.match(r"t_-?\d+_-?\d+([a-d]*)\.json", f.name)[1] or "-"
            sources.append({"file": f.name.removesuffix(".gz"), "sha256": sha, "bytes": size,
                            "request": f"{API}/map.json?bbox=<lattice tile {ij[0]},{ij[1]} in EPSG:4326; quadrant {q}>",
                            "timestamp": d.get("timestamp")})
            for e in d["elements"]:
                k = (e["type"], e["id"])
                if k not in seen:
                    seen.add(k)
                    elements.append(e)
        tid = inv[ij]
        counts, targets, places = _tile_counts(elements, tile_bbox(*ij), tr)
        tiles[tid] = {"ij": list(ij), "counts": counts, "targets": targets, "places": places,
                      "role": "candidate" if tid in CANDIDATES else "calibration" if tid in CALIBRATION else "town"}
        nodes = {e["id"]: e for e in elements if e["type"] == "node"}
        for w in (e for e in elements if e["type"] == "way"):
            t = w.get("tags") or {}
            if t.get("highway") not in MAJOR or w["id"] in ways:
                continue
            ll = [[nodes[k]["lon"], nodes[k]["lat"]] for k in w["nodes"] if k in nodes]
            if len(ll) != len(w["nodes"]) or len(ll) < 2:
                continue
            if not LineString([tr.transform(*p) for p in ll]).intersects(window):
                continue
            ways[w["id"]] = {"id": w["id"], "tags": {k: t[k] for k in TAGS_KEPT if k in t}, "lonlat": ll}
    rel = {}
    for ref, rid in ROUTE_RELATIONS.items():
        f = next(raw.glob(f"relfull_{rid}.json*"))
        d, sha, size = _read_raw(f)
        sources.append({"file": f.name.removesuffix(".gz"), "sha256": sha, "bytes": size,
                        "request": f"{API}/relation/{rid}/full.json", "timestamp": d.get("timestamp")})
        nodes = {e["id"]: (e["lon"], e["lat"]) for e in d["elements"] if e["type"] == "node"}
        cells: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for e in d["elements"]:
            if e["type"] != "way":
                continue
            t = e.get("tags", {})
            pts = [tr.transform(*nodes[k]) for k in e["nodes"] if k in nodes]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                i, j = ij_of((x1 + x2) / 2, (y1 + y2) / 2)
                if -40 <= i <= 20 and -20 <= j <= 70:
                    cells[f"{i},{j}"][f"{t.get('highway')}|{t.get('ref')}"] += math.hypot(x2 - x1, y2 - y1)
        rel[ref] = {"osm_relation": rid,
                    "cells": {k: {a: round(b, 1) for a, b in sorted(v.items())} for k, v in sorted(cells.items())}}
    extract = {
        "adr": ADR, "crs_ways": "EPSG:4326 (OSM lon/lat as delivered by the API)", "crs_points": regions.WORK_CRS,
        "license": "ODbL 1.0, © OpenStreetMap contributors",
        "filter": ("tiles: counts and points of truck targets by category (no names, no brands), OSM place names, "
                   "building count (point inside the tile), km of major roads; ways: highway in " + ", ".join(MAJOR) +
                   " intersecting lattice tiles (-5..3, -4..5), tags " + ", ".join(TAGS_KEPT) +
                   "; relations: per lattice cell lengths [m] of the route relations " +
                   ", ".join(f"{k} ({v})" for k, v in ROUTE_RELATIONS.items())),
        "tiles": dict(sorted(tiles.items())), "ways": [ways[k] for k in sorted(ways)], "relations": rel,
    }
    manifest = {
        "id": "osm-api06-map-plan-0278",
        "name": "OpenStreetMap: API 0.6 map calls per lattice tile + full route relations (ADR 0278)",
        "provider": "OpenStreetMap Foundation (api.openstreetmap.org)", "license": "ODbL 1.0",
        "license_url": "https://opendatacommons.org/licenses/odbl/1-0/", "attribution": "© OpenStreetMap contributors",
        "crs": "EPSG:4326 (OSM native); points of the extract reprojected to EPSG:2180 (pyproj, always_xy)",
        "extent": "lattice tiles of ADR 0203 listed in the extract (Bialystok -5..3 x -4..5, towns Grajewo and Zambrow)",
        "accuracy": "volunteered geographic information; tag completeness varies (truck categories are OSM-only, see ADR 0278)",
        "client": {"user_agent": GENERIC_UA, "pacing_s": 1.5, "split_rule": "4 quadrants when the API answers 'too many nodes'"},
        "date": "2026-11-16", "in_git": False,
        "raw_location": "outside git (session scratchpad, gzip); answers listed with the SHA256 of the uncompressed answer",
        "raw_answers": {"sha256": {s["file"]: s["sha256"] for s in sources}},
        "extract_in_git": {"path": EXTRACT.relative_to(REPO).as_posix(), "sha256": None},
        "used_by": ["tools/worldgen/qa/map_plan_0278.py"],
        "not_used": "Overpass (no answer from the session), Geofabrik pbf download (connection reset), Google (forbidden, ADR 0002)",
    }
    return extract, manifest


# ---------------------------------------------------------------------------------------------- seams / routes
def _edge_of(bb, x, y, tol=0.01):
    if abs(x - bb[0]) < tol:
        return "W"
    if abs(x - bb[2]) < tol:
        return "E"
    if abs(y - bb[1]) < tol:
        return "S"
    if abs(y - bb[3]) < tol:
        return "N"
    return None


def _points(g) -> list[Point]:
    if g.is_empty:
        return []
    if g.geom_type == "Point":
        return [g]
    if g.geom_type in ("MultiPoint", "GeometryCollection"):
        return [p for q in g.geoms for p in _points(q)]
    return []


def shared_edge(a, b) -> str | None:
    """Edge of bbox `a` fully shared with bbox `b` (W/E/S/N), None when they are not lattice neighbours."""
    if (a[1], a[3]) == (b[1], b[3]):
        if a[0] == b[2]:
            return "W"
        if a[2] == b[0]:
            return "E"
    if (a[0], a[2]) == (b[0], b[2]):
        if a[1] == b[3]:
            return "S"
        if a[3] == b[1]:
            return "N"
    return None


OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


def graph_crossings(region_id: str, edge: str) -> list[dict] | None:
    """Boundary nodes of a built tile on one of its edges (roads.graph.json, pinned pbf of the pipeline)."""
    p = REG / region_id / "roads.graph.json"
    if not p.exists():
        return None
    bb = regions.get(region_id).bbox
    g = json.loads(p.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in g["nodes"]}
    out = {}
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if _edge_of(bb, n["x"], n["y"]) == edge:
                out[(e["osm_way"], round(n["x"], 1), round(n["y"], 1))] = {
                    "osm_way": e["osm_way"], "x": round(n["x"], 1), "y": round(n["y"], 1),
                    "ref": (e["attrs"].get("ref") or {}).get("v"), "highway": e["attrs"]["highway"]["v"]}
    return [out[k] for k in sorted(out)]


def lines(extract: dict) -> dict[int, LineString]:
    tr = _tr()
    return {w["id"]: LineString([tr.transform(lon, lat) for lon, lat in w["lonlat"]]) for w in extract["ways"]}


def edge_crossings(extract: dict, L: dict, bb, edge: str) -> list[dict]:
    """Crossings of the extract's major roads with one edge of a tile."""
    seg = {"W": LineString([(bb[0], bb[1]), (bb[0], bb[3])]), "E": LineString([(bb[2], bb[1]), (bb[2], bb[3])]),
           "S": LineString([(bb[0], bb[1]), (bb[2], bb[1])]), "N": LineString([(bb[0], bb[3]), (bb[2], bb[3])])}[edge]
    out = []
    for w in extract["ways"]:
        ln = L[w["id"]]
        if not ln.intersects(seg):
            continue
        for p in _points(ln.intersection(seg)):
            out.append({"osm_way": w["id"], "x": round(p.x, 1), "y": round(p.y, 1), "ref": w["tags"].get("ref"),
                        "highway": w["tags"]["highway"]})
    return sorted(out, key=lambda d: (d["x"], d["y"], d["osm_way"]))


def _digraph(extract: dict, L: dict, clip=None, truck_costs: bool = False):
    import networkx as nx
    g = nx.DiGraph()
    for w in extract["ways"]:
        t = w["tags"]
        ln = L[w["id"]]
        if clip is not None:
            if not ln.intersects(clip):
                continue
            ln = ln.intersection(clip)
            if ln.geom_type != "LineString" or ln.is_empty:
                parts = [q for q in getattr(ln, "geoms", []) if q.geom_type == "LineString"]
            else:
                parts = [ln]
        else:
            parts = [ln]
        f = 1.0
        if truck_costs:
            if t.get("hgv") in ("no", "destination", "delivery") or (_maxweight(t) or 99) < 40:
                continue
            f = 1.0 if refs(t) else 2.0 if t["highway"].split("_")[0] in ("motorway", "trunk", "primary") else 4.0
        one = t.get("oneway") in ("yes", "1") or t.get("junction") == "roundabout" or t["highway"].startswith("motorway")
        for part in parts:
            co = [(round(x, 2), round(y, 2)) for x, y in part.coords]
            if t.get("oneway") == "-1":
                co = co[::-1]
            for a, b in zip(co, co[1:]):
                d = math.dist(a, b)
                if d == 0:
                    continue
                g.add_edge(a, b, w=d * f, d=d, way=w["id"])
                if not (one or t.get("oneway") == "-1"):
                    g.add_edge(b, a, w=d * f, d=d, way=w["id"])
    return g


def through_route(extract: dict, L: dict, bb, spec: dict, prev_exit: dict | None) -> dict:
    """Control route of a defined tile: entry crossing (from the built neighbour / previous tile) to an exit crossing of
    the given refs; shortest path over the major roads clipped to the tile, oneway respected."""
    import networkx as nx
    e_in, frm = spec["entry"]
    e_out, to = spec["exit"]
    cin, cout = edge_crossings(extract, L, bb, e_in), edge_crossings(extract, L, bb, e_out)
    if prev_exit is not None:
        cand_in = [d for d in cin if d["osm_way"] == prev_exit["osm_way"] and d["x"] == prev_exit["x"] and d["y"] == prev_exit["y"]]
    elif "entry_ways" in spec:
        cand_in = [d for d in cin if d["osm_way"] in spec["entry_ways"]]
    else:
        cand_in = [d for d in cin if set(refs(d)) & set(spec["refs"])]
    cand_out = [d for d in cout if set(refs(d)) & set(spec["refs"])]
    g = _digraph(extract, L, clip=box(*bb))

    def node_at(p):
        return min(g.nodes, key=lambda n: ((n[0] - p["x"]) ** 2 + (n[1] - p["y"]) ** 2, n))

    best = None
    for a in cand_in:
        for b in cand_out:
            try:
                path = nx.shortest_path(g, node_at(a), node_at(b), weight="w")
            except nx.NetworkXNoPath:
                continue
            ln = sum(g[u][v]["d"] for u, v in zip(path, path[1:]))
            if best is None or (ln, a["osm_way"], b["osm_way"]) < best[0]:
                best = ((ln, a["osm_way"], b["osm_way"]), a, b, path)
    if best is None:
        return {"found": False, "entry_candidates": cand_in, "exit_candidates": cand_out}
    (ln, _, _), a, b, path = best
    seq = []
    for u, v in zip(path, path[1:]):
        if not seq or seq[-1] != g[u][v]["way"]:
            seq.append(g[u][v]["way"])
    return {"found": True, "entry": a, "exit": b, "length_m": round(ln, 1), "ways": seq, "from": frm, "to": to,
            "edge_in": e_in, "edge_out": e_out, "chain": [[round(x, 1), round(y, 1)] for x, y in path]}


def corridor_route(extract: dict, L: dict, start: tuple[float, float], end: tuple[float, float]) -> dict:
    """Truck route between two points over the extract: numbered roads preferred (cost x1 with ref, x2 trunk/primary
    without ref, x4 others; WORKING_VALUE), ways with hgv=no or maxweight < 40 t left out; tiles visited in order."""
    import networkx as nx
    g = _digraph(extract, L, truck_costs=True)

    def near(p, r=40.0):     # both carriageways of a dual road: every graph node within r of the point
        return sorted(n for n in g.nodes if (n[0] - p[0]) ** 2 + (n[1] - p[1]) ** 2 <= r * r)

    best = None
    for a in near(start):
        for b in near(end):
            try:
                c, p = nx.single_source_dijkstra(g, a, b, weight="w")
            except nx.NetworkXNoPath:
                continue
            if best is None or (c, a, b) < best[0]:
                best = ((c, a, b), p)
    if best is None:
        return {"start": list(start), "end": list(end), "found": False}
    path = best[1]
    cells: list[list] = []
    for u, v in zip(path, path[1:]):
        c = list(ij_of((u[0] + v[0]) / 2, (u[1] + v[1]) / 2))
        if not cells or cells[-1][0] != c:
            cells.append([c, 0.0])
        cells[-1][1] += g[u][v]["d"]
    return {"start": [round(start[0], 1), round(start[1], 1)], "end": [round(end[0], 1), round(end[1], 1)],
            "length_m": round(sum(c[1] for c in cells), 1),
            "tiles": [{"ij": c, "length_m": round(m, 1)} for c, m in cells]}


# ---------------------------------------------------------------------------------------------- plan (deterministic)
def powiat_shares(bb) -> dict[str, float]:
    d = json.loads(PRG.read_text(encoding="utf-8"))
    tb = box(*bb)
    out = {}
    for f in d["features"]:
        a = shape(f["geometry"]).intersection(tb).area
        if a > 0:
            out[f["properties"]["teryt"]] = round(a / tb.area, 4)
    return dict(sorted(out.items()))


def class_of_built(b: dict) -> str:
    """Budget class of a built tile: city = powiat 2061 or a town centre (knyszyn); suburban = >= 250 buildings
    (buildings.geojson); rural = fewer."""
    if b["teryt_powiat"] == "2061" or b["id"] == "knyszyn":
        return "miasto"
    return "podmiejski" if b["buildings"] >= 250 else "zamiejski"


BUDGET_KEYS = ("static_tris_high", "static_tris_low", "frame_tris_high_median", "frame_tris_high_max",
               "frame_tris_low_median", "frame_tris_low_max", "glb_mb", "world_memory_low_mb", "world_memory_high_mb")


def budget_classes(budget: dict) -> dict:
    out = {}
    for cls in ("miasto", "podmiejski", "zamiejski"):
        rows = [b for b in budget["tiles"] if class_of_built(b) == cls]
        med = {}
        for k in BUDGET_KEYS:
            vals = [b[k] for b in rows if b.get(k) is not None]
            med[k] = round(statistics.median(vals), 1) if vals else None
        out[cls] = {"tiles": sorted(b["id"] for b in rows), "median": med}
    city = [b for b in budget["tiles"] if class_of_built(b) == "miasto"]
    xs = [b["buildings"] for b in city]
    mx = statistics.mean(xs)
    fit = {}
    for k in ("static_tris_high", "frame_tris_high_max", "frame_tris_low_max", "glb_mb"):
        ys = [b[k] for b in city]
        my = statistics.mean(ys)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        fit[k] = {"slope_per_building": round(slope, 3), "intercept": round(my - slope * mx, 1)}
    out["miasto"]["fit_vs_buildings"] = fit
    out["miasto"]["fit_range_buildings"] = [min(xs), max(xs)]
    return out


def build_plan(extract: dict, gugik: dict, budget: dict) -> dict:
    L = lines(extract)
    built = built_regions()
    classes = budget_classes(budget)
    everyone = {**built, **RING_0231, **{t: tuple(v["ij"]) for t, v in CANDIDATES.items()}}
    tiles = []
    for tid in sorted(CANDIDATES):
        ij = tuple(CANDIDATES[tid]["ij"])
        bb = tile_bbox(*ij)
        x = extract["tiles"][tid]
        sh = powiat_shares(bb)
        pw = sorted(sh, key=lambda k: (-sh[k], k))
        k = x["counts"]
        nb = k.get("buildings", 0)
        cls = "miasto" if pw[0] == "2061" else ("podmiejski" if nb >= 250 else "zamiejski")
        est = {"class": cls, "status": "ESTIMATED (median of the built tiles of the class)", **classes[cls]["median"]}
        if cls == "miasto":
            lo, hi = classes["miasto"]["fit_range_buildings"]
            est["by_buildings"] = {kk: round(v["intercept"] + v["slope_per_building"] * nb, 1)
                                   for kk, v in classes["miasto"]["fit_vs_buildings"].items()}
            est["by_buildings_extrapolated"] = not (lo <= nb <= hi)
        score = (k.get("hall_1000m2", 0) + k.get("warehouse", 0) + k.get("works", 0) + 2 * k.get("fuel_hgv", 0)
                 + 2 * k.get("truck_parking", 0) + k.get("industrial_ha", 0) / 10.0)
        neigh = []
        for nid, nij in sorted(everyone.items()):
            if nid == tid:
                continue
            e = shared_edge(bb, tile_bbox(*nij))
            if e is None:
                continue
            cr = [d for d in edge_crossings(extract, L, bb, e)
                  if d["ref"] or d["highway"].split("_")[0] in ("motorway", "trunk", "primary")]
            kind = "built" if nid in built else "ring_0231" if nid in RING_0231 else "candidate"
            neigh.append({"id": nid, "kind": kind, "edge": e, "numbered_crossings": len(cr),
                          "refs": sorted({d["ref"] or d["highway"] for d in cr})})
        tiles.append({
            "id": tid, "group": CANDIDATES[tid]["group"], "ij": list(ij), "bbox": list(bb),
            "origin": [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2], "teryt_powiat": pw[0],
            "teryt_powiat_extra": [p for p in pw[1:] if sh[p] > EXTRA_POWIAT_MIN_SHARE], "powiat_area_share": sh,
            "places": x["places"], "counts": k, "target_score": round(score, 1), "budget_estimate": est,
            "data": gugik["tiles"].get(tid), "neighbours": neigh,
        })
    by_id = {t["id"]: t for t in tiles}
    have = set(built) | set(RING_0231)
    order = []
    for n, (tid, why) in enumerate(ORDER, start=1):
        via = [d for d in by_id[tid]["neighbours"] if d["id"] in have and d["numbered_crossings"] > 0]
        order.append({"n": n, "id": tid, "why": why, "define_now": n <= DEFINE_FIRST,
                      "connected_via": [f"{d['id']} ({d['edge']}: {', '.join(d['refs'])})" for d in via]})
        have.add(tid)
    defined, prev = {}, {}
    for tid in DRIVING_ORDER:
        spec = THROUGH[tid]
        r = through_route(extract, L, tile_bbox(*CANDIDATES[tid]["ij"]), spec, prev.get(spec["entry"][1]))
        defined[tid] = r
        if r["found"]:
            prev[tid] = r["exit"]
    seams = []
    for tid in sorted(defined):
        bb = tile_bbox(*CANDIDATES[tid]["ij"])
        for nid, nij in sorted(built.items()):
            e = shared_edge(bb, tile_bbox(*nij))
            if e is None:
                continue
            g = graph_crossings(nid, OPPOSITE[e]) or []
            pairs = []
            for d in edge_crossings(extract, L, bb, e):
                cand = [q for q in g if q["osm_way"] == d["osm_way"]]
                best = min(cand, key=lambda q: math.dist((q["x"], q["y"]), (d["x"], d["y"])), default=None)
                pairs.append({**d, "graph_offset_m": round(math.dist((best["x"], best["y"]), (d["x"], d["y"])), 2)
                              if best else None})
            seams.append({"new": tid, "built": nid, "edge_of_new": e, "crossings": pairs,
                          "built_graph_major_ways": sorted({q["osm_way"] for q in g if q["highway"] in MAJOR})})
    dg = defined["bialystok-dojlidy-gorne"]
    routes = {
        "s8-to-kleeberga": corridor_route(extract, L, (769312.0, 595199.0), (772300.0, 595199.0)),
        "c-to-dojlidy-g10": corridor_route(extract, L, (779019.0, 595250.0), (779019.0, 590258.0)),
        "dojlidy-to-dk19-south": corridor_route(extract, L, (781067.0, 590366.0),
                                                (dg["exit"]["x"], dg["exit"]["y"]) if dg["found"] else (783115.0, 589000.0)),
    }
    return {
        "adr": ADR, "crs": regions.WORK_CRS, "tile_size_m": T,
        "lattice": {"x0": X0, "y0": Y0, "anchor_region": C.id, "rule": "x = x0 + 2048*i, y = y0 + 2048*j (ADR 0203)"},
        "source": {"extract": EXTRACT.relative_to(REPO).as_posix(), "manifest": MANIFEST.relative_to(REPO).as_posix(),
                   "gugik": GUGIK.relative_to(REPO).as_posix(), "budget": BUDGET.relative_to(REPO).as_posix(),
                   "powiaty": PRG.relative_to(REPO).as_posix()},
        "built": {k: list(v) for k, v in sorted(built.items())},
        "ring_0231": {k: list(v) for k, v in sorted(RING_0231.items())},
        "budget_classes": classes, "candidates": tiles, "order": order, "defined": defined, "seams_defined": seams,
        "corridor_routes": routes, "podlasie": podlasie(extract, classes),
        "rules": {
            "target_score": "halls >= 1000 m2 + warehouses + works + 2 x fuel_hgv + 2 x truck_parking + industrial ha / 10 (WORKING_VALUE weights)",
            "budget_class": "city = largest powiat share 2061; else suburban >= 250 OSM buildings, rural fewer (built tiles: buildings.geojson)",
            "teryt_powiat": "largest area share of the tile in PRG powiaty (Data/Admin/powiaty_prg.geojson); every other overlapped powiat in teryt_powiat_extra (ADR 0219, tools/worldgen/powiaty.py)",
        },
    }


def podlasie(extract: dict, classes: dict) -> dict:
    """Corridor assessment from the route relations: lattice cells crossed (>= 50 m of road), km, kinds of road."""
    rel = extract["relations"]

    ring = set(RING_0231.values())

    def cells(ref, pred, motorway_only=False):
        """Road length per cell; a motorway is mapped as two carriageways, so its length is halved."""
        out = []
        for k, v in rel[ref]["cells"].items():
            i, j = map(int, k.split(","))
            if (i, j) in ring:
                continue
            vv = {a: b for a, b in v.items() if a.startswith("motorway")} if motorway_only else v
            m = sum(b / 2 if a.startswith("motorway") else b for a, b in vv.items())
            if pred(i, j) and m >= 50.0:
                out.append({"ij": [i, j], "length_m": round(m, 1), "kinds": sorted(vv)})
        return sorted(out, key=lambda d: (d["ij"][1], -d["ij"][0]))

    z = classes["zamiejski"]["median"]

    def summary(lst):
        return {"tiles": len(lst), "road_km": round(sum(d["length_m"] for d in lst) / 1000, 1),
                "estimate_glb_mb": round(len(lst) * z["glb_mb"]),
                "estimate_world_memory_low_mb_per_tile": z["world_memory_low_mb"],
                "status": "ESTIMATED (rural median of the built tiles; town tiles cost more)", "cells": lst}

    return {
        "monki_grajewo_dk65": {**summary(cells("65", lambda i, j: (i, j) != (-13, 13) and i >= -24 and 13 <= j <= 25)),
                               "town": "grajewo", "town_counts": extract["tiles"]["grajewo"]["counts"]},
        "tykocin_to_s8_dw671": summary(cells("671", lambda i, j: i in (-13, -14) and -2 <= j <= 1)),
        "s8_tykocin_junction_to_zambrow": {**summary(cells("8", lambda i, j: -29 <= i <= -15 and -11 <= j <= -2, True)),
                                           "town": "zambrow", "town_counts": extract["tiles"]["zambrow"]["counts"]},
        "s8_bialystok_to_tykocin_junction": summary(cells("8", lambda i, j: -14 <= i <= -5 and -2 <= j <= 0, True)),
    }


# ---------------------------------------------------------------------------------------------- gugik / budget inputs
def _manifest_urls() -> dict[str, int | None]:
    out = {}
    for p in sorted(MAN_DIR.glob("gugik-*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for f in d.get("files", []) or []:
            if isinstance(f, dict) and f.get("url"):
                out[f["url"]] = f.get("size_bytes")
    return out


def build_gugik(index: dict) -> dict:
    """Sheets ingest.py would take for each candidate tile (its selection rules), split into on the lead's disk (URL in
    a manifest of Data/SourceManifests) and to download. Sizes: ORTO from the index (wlk_pliku_mb); NMT from the
    manifests when on disk, else the median NMT sheet of the manifests (ESTIMATED; the index has no size)."""
    import gugik_index as gi
    import ingest
    on_disk = _manifest_urls()
    nmt_sizes = sorted(v for k, v in on_disk.items() if "/NMT/" in k and v)
    nmt_med = statistics.median(nmt_sizes) / 1e6
    P = index["products"]
    out = {}
    for tid in sorted(CANDIDATES):
        bb = tile_bbox(*CANDIDATES[tid]["ij"])
        tb = box(*bb)

        def here(rows):
            return [r for r in rows if r.get("ring") and Polygon(r["ring"]).intersection(tb).area > 1.0]

        nmt_rows = here(P["NMT"])
        base = lambda r: (r.get("char_przestrz") == "1.00 m" and r.get("format", "").startswith("ARC/INFO")  # noqa: E731
                          and r.get("uklad_h") == "PL-EVRF2007-NH")
        nmt = ingest.pick_latest(nmt_rows, bb, base)
        years = {}
        for yr in sorted({r["akt_rok"] for r in nmt_rows if base(r)}):
            got = ingest.pick_latest(nmt_rows, bb, lambda r, yr=yr: base(r) and r.get("akt_rok") == yr, key="akt_rok")
            if got:
                years[yr] = sorted({r["godlo"] for r in got})
        orto_rows = here(P["ORTO"])
        orto = ingest.pick_latest(orto_rows, bb, lambda r: r.get("piksel") == "0.25" and r.get("kolor") == "RGB"
                                  and r.get("uklad_xy") == "PL-1992")
        o10c = [r for r in orto_rows if r.get("piksel") == "0.1" and r.get("kolor") == "RGB" and r.get("uklad_xy") == "PL-1992"]
        o10 = []
        for yr in sorted({r["akt_rok"] for r in o10c}, reverse=True):
            s = [r for r in o10c if r["akt_rok"] == yr]
            if ingest.covers(s, bb) > 0.9999:
                o10 = sorted(s, key=lambda r: r["url_do_pobrania"])
                break
        nmpt = ingest.pick_latest(here(P["NMPT"]), bb, lambda r: r.get("uklad_h") == "PL-EVRF2007-NH")

        def cost(rows, size):
            new = [r for r in rows if r["url_do_pobrania"] not in on_disk]
            return {"sheets": sorted(f"{r['godlo']} {r['akt_data']}" for r in rows), "on_disk": len(rows) - len(new),
                    "to_download": len(new), "to_download_mb": round(sum(size(r) for r in new), 1)}

        orto_mb = lambda r: float(r.get("wlk_pliku_mb") or 0)  # noqa: E731
        sh = powiat_shares(bb)
        out[tid] = {
            "nmt_default": {**cost(nmt, lambda r: nmt_med), "akt_data": sorted({r["akt_data"] for r in nmt}),
                            "size_status": f"ESTIMATED {nmt_med:.1f} MB per sheet (median of {len(nmt_sizes)} NMT sheets in the manifests)"},
            "nmt_years_full_cover": years,
            "orto_0p25": {**cost(orto, orto_mb), "akt_data": sorted({r["akt_data"] for r in orto})},
            "orto_0p10_optin": {**cost(o10, orto_mb), "akt_rok": o10[0]["akt_rok"] if o10 else None},
            "nmpt_optin": {"sheets": len(nmpt), "akt_data": sorted({r["akt_data"] for r in nmpt})},
            "powiat_datasets_in_manifests": {
                t: {i: (MAN_DIR / f"{i}.json").exists()
                    for i in (f"gugik-bdot10k-{t}", f"gugik-lod1-2024-{t}", f"gugik-lod2-2017-{t}")} for t in sh},
        }
    return {"adr": ADR, "queried_utc": index["queried_utc"], "bbox_epsg2180": index["bbox_epsg2180"],
            "index_services": {k: gi.INDEX_SERVICES[k][0] for k in sorted(P)},
            "method": ("WFS 1.0.0 GetFeature per product-year layer over the bbox (tools/worldgen/gugik_index.py, generic "
                       "User-Agent, nothing downloaded); selection = ingest.pick_latest on the sheets intersecting each tile"),
            "tiles": out}


# WORLD_MEMORY [MB] Low / High of the built tiles: import logs cited in ADR 0229 (Low) and ADR 0234 par. 7 (High, only
# where measured), as tabulated by tools/worldgen/streaming/tile_graph.py on origin/streaming-0235 (not in main).
WORLD_MEMORY = {
    "bialystok-industrial-c": (124.2, 267.0), "bialystok-dojlidy": (99.6, 214.9), "bialystok-maczka": (153.2, 420.4),
    "bialystok-kleeberga": (156.7, 356.8), "bialystok-knyszynska": (116.0, 260.2), "dk65-01": (68.2, 165.9),
    "dk65-02": (60.2, None), "dk65-03": (50.5, None), "dk65-04": (76.1, None), "dk65-05": (75.5, None),
    "dk65-06": (59.0, None), "dk65-07": (59.1, None), "dk65-08": (55.5, None), "dk65-09": (51.4, None),
    "dk65-10": (49.0, None), "dk65-11": (48.2, None), "knyszyn-s": (40.8, None), "knyszyn": (95.5, None),
    "knyszyn-w": (54.0, None), "dk65-monki-01": (46.6, None), "dw671-tykocin-01": (45.7, None),
}


def build_budget_snapshot() -> dict:
    rows = []
    for rid in sorted(built_regions()):
        d = REG / rid
        q = d / "generated" / "streetscape_qa.json"
        if not q.exists():
            continue
        mb = json.loads(q.read_text(encoding="utf-8"))["mesh_budget"]
        fe = mb["frame_estimate"]
        wmp = d / "generated" / "world_manifest.json"
        wm = json.loads(wmp.read_text(encoding="utf-8"))
        th, tl = [f["tris_high"] for f in fe], [f["tris_low"] for f in fe]
        mem = WORLD_MEMORY.get(rid, (None, None))
        rows.append({
            "id": rid, "teryt_powiat": regions.get(rid).teryt_powiat,
            "buildings": len(json.loads((d / "buildings.geojson").read_text(encoding="utf-8"))["features"]),
            "static_tris_high": sum(c["tris_high_static"] for c in mb["per_chunk"]),
            "static_tris_low": sum(c["tris_low_static"] for c in mb["per_chunk"]),
            "cameras": len(fe), "frame_tris_high_median": statistics.median(th), "frame_tris_high_max": max(th),
            "frame_tris_low_median": statistics.median(tl), "frame_tris_low_max": max(tl),
            "glb_mb": round(sum(c.get("bytes", 0) for c in wm["chunks"]) / 1e6, 1),
            "world_memory_low_mb": mem[0], "world_memory_high_mb": mem[1],
            "inputs_sha256": {f"{rid}/generated/streetscape_qa.json": sha256_file(q),
                              f"{rid}/generated/world_manifest.json": sha256_file(wmp)},
        })
    return {"adr": ADR,
            "note": ("snapshot of generated/* of the built tiles; static = all chunks of the tile (tris_*_static), frame = "
                     "mesh_budget.frame_estimate cameras (1.6 km / 120 deg wedge, no occlusion); glb = chunk bytes of "
                     "world_manifest.json; WORLD_MEMORY from the import logs cited in ADR 0229/0234 (High only where measured)"),
            "tiles": rows}


# ---------------------------------------------------------------------------------------------- authored files
def overrides_yaml(tid: str) -> str:
    bb = tile_bbox(*CANDIDATES[tid]["ij"])
    ox, oy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    return (f"# Authored overrides of region {tid} (ADR {ADR}, rough definition: the tile is NOT ingested or built yet).\n"
            f"# Every entry survives a re-import; coordinates are region-local E/N (origin EPSG:2180 {ox:.0f}, {oy:.0f})\n"
            f"# or EPSG:2180 where the key says so. Nothing was checked on the orthophoto of this tile, and the built\n"
            f"# neighbours carry no cross-section override on the ways crossing the shared edges, so the generator rules\n"
            f"# apply (D63: drivable first). Open (ADR {ADR}): lamp policy (LED like bialystok-knyszynska?) - lead / owner.\n"
            f"overrides: []\n")


def sources_authored(tid: str, gugik: dict) -> str:
    g = gugik["tiles"][tid]
    pin, why = PINS[tid]
    return json.dumps({
        "provenance": f"authored_override (ADR {ADR}, mechanism of ADR 0209/0212): source pins of region {tid}, read by ingest.py and build_region.py",
        "pins": {"nmt_year": pin},
        "reason": (f"{why} GUGiK sheet index (SkorowidzNMT, queried {gugik['queried_utc'][:10]}): the {pin} series fully covers "
                   f"this tile (sheets {', '.join(g['nmt_years_full_cover'][pin])}); without the pin ingest.py would take the "
                   f"flight day {', '.join(g['nmt_default']['akt_data'])}. See docs/reports/map/map_plan_0278_gugik.json."),
        "verify": "none (move together with the pin of the neighbour named in the reason)",
    }, indent=1, ensure_ascii=False) + "\n"


def route_endpoints(tid: str, r: dict) -> str:
    a, b = r["entry"], r["exit"]
    to = r["to"] or "the next lattice tile (not defined)"
    return json.dumps({
        "provenance": f"authored_override (ADR {ADR}): control route for cameras/QA = the through road of this tile",
        "description": (f"From the {r['edge_in']} tile edge (seam with {r['from']}, OSM way {a['osm_way']}) to the {r['edge_out']} "
                        f"tile edge (OSM way {b['osm_way']}, ref {b['ref']}; seam with {to}); {r['length_m']:.0f} m over the OSM ways "
                        f"{', '.join(str(w) for w in r['ways'])}. Points from the OSM API 0.6 extract of 2026-11-16 "
                        f"(Data/Plans/map-plan-0278/); build_world snaps them to the nearest graph node."),
        "start_epsg2180": [a["x"], a["y"]],
        "end_epsg2180": [b["x"], b["y"]],
        "confidence": "medium (OSM 2026-11-16 vs the pinned pbf 2026-11-08: re-check after build_region that both are graph boundary nodes)",
    }, indent=1, ensure_ascii=False) + "\n"


def init_regions(plan: dict, gugik: dict) -> list[str]:
    written = []
    for tid, r in sorted(plan["defined"].items()):
        d = REG / tid
        d.mkdir(parents=True, exist_ok=True)
        files = {"overrides.yaml": overrides_yaml(tid), "sources.authored.json": sources_authored(tid, gugik),
                 "route_endpoints.json": route_endpoints(tid, r) if r["found"] else None}
        for name, text in files.items():
            if text is not None and not (d / name).exists():     # authored files: never overwritten
                (d / name).write_text(text, encoding="utf-8", newline="\n")
                written.append(f"{tid}/{name}")
    return written


def print_regions(plan: dict) -> str:
    by = {t["id"]: t for t in plan["candidates"]}
    out = []
    for o in plan["order"][:DEFINE_FIRST]:
        t = by[o["id"]]
        i, j = t["ij"]
        extra = ("\n        teryt_powiat_extra=(" + "".join(f'"{p}", ' for p in t["teryt_powiat_extra"]).rstrip() + "),"
                 if t["teryt_powiat_extra"] else "")
        out.append(f'''    "{t['id']}": Region(
        id="{t['id']}",
        title="{TITLES[t['id']]}",
        candidate="P_{t['group'].replace('-', '_')}",
        bbox=({t['bbox'][0]}, {t['bbox'][1]}, {t['bbox'][2]}, {t['bbox'][3]}),
        origin=({t['origin'][0]}, {t['origin'][1]}),
        teryt_powiat="{t['teryt_powiat']}",{extra}
        status="WORKING_ASSUMPTION (ADR {ADR}, owner D63; tile = lattice ({i},{j}) of the ADR 0203 plan)",
    ),''')
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------- control render
def render(plan: dict, extract: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    L = lines(extract)
    fig, ax = plt.subplots(figsize=(12, 13), dpi=110)
    order = {o["id"]: o["n"] for o in plan["order"]}
    for rid, (i, j) in plan["built"].items():
        b = tile_bbox(i, j)
        ax.add_patch(Rectangle(b[:2], T, T, fc="#d9d9d9", ec="#7f7f7f", lw=0.6))
        ax.text(b[0] + 60, b[1] + 80, rid.replace("bialystok-", "b-"), fontsize=6.5, color="#404040", clip_on=True)
    for t in plan["candidates"]:
        b = tuple(t["bbox"])
        n = order.get(t["id"])
        fc = "#f4a261" if n and n <= DEFINE_FIRST else "#ffe8c2" if n else "#ffffff"
        ax.add_patch(Rectangle(b[:2], T, T, fc=fc, ec="#b5651d", lw=0.8, alpha=0.9))
        k = t["counts"]
        ax.text(b[0] + 60, b[3] - 230, f"{str(n) + '. ' if n else ''}{t['id'].replace('bialystok-', 'b-')}", fontsize=6.5,
                weight="bold", clip_on=True)
        ax.text(b[0] + 60, b[3] - 470, f"H{k.get('hall_1000m2', 0)} M{k.get('warehouse', 0)} Z{k.get('works', 0)} "
                f"{k.get('industrial_ha', 0):.0f} ha", fontsize=6, clip_on=True)
        ax.text(b[0] + 60, b[3] - 690, f"bud. {k.get('buildings', 0)}, {t['budget_estimate']['class']}", fontsize=6, clip_on=True)
    for w in extract["ways"]:
        hw = w["tags"]["highway"]
        if hw.startswith("tertiary"):
            continue
        x, y = L[w["id"]].xy
        col = "#c0392b" if hw.startswith("motorway") else "#e67e22" if hw.startswith("trunk") else "#2c3e50"
        ax.plot(x, y, color=col, lw=1.2 if hw.startswith(("motorway", "trunk")) else 0.5)
    for r in plan["defined"].values():
        if r["found"]:
            xs, ys = zip(*r["chain"])
            ax.plot(xs, ys, color="#1f77b4", lw=3.5, alpha=0.55)
    colours = {"hall_1000m2": "#6a3d9a", "warehouse": "#33a02c", "works": "#b15928", "fuel_hgv": "#e31a1c",
               "truck_parking": "#1f78b4"}
    for t in plan["candidates"]:
        for d in extract["tiles"][t["id"]]["targets"]:
            if d["cat"] in colours:
                ax.plot(d["x"], d["y"], ".", ms=3, color=colours[d["cat"]])
    xs = [t["bbox"][0] for t in plan["candidates"]]
    ys = [t["bbox"][1] for t in plan["candidates"]]
    ax.set_xlim(min(xs) - T - 300, max(xs) + T + 300)
    ax.set_ylim(min(ys) - 300, max(ys) + T + 300)
    ax.set_aspect("equal")
    ax.set_title(f"ADR {ADR}: zbudowane (szare), definicje 1-{DEFINE_FIRST} (pomarańczowe), kolejka 4-{len(ORDER)} (jasne), "
                 "pozostali kandydaci (białe); trasy kontrolne (niebieskie)\nH = hale >= 1000 m2 (fiolet), M = magazyny (ziel.), "
                 "Z = zakłady (brąz), paliwo HGV (czerw.), ha = landuse=industrial; drogi: S (czerw.), krajowe/trunk (pomar.)",
                 fontsize=8)
    ax.set_xlabel("EPSG:2180 x [m]")
    ax.set_ylabel("EPSG:2180 y [m]")
    fig.tight_layout()
    fig.savefig(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", type=Path, help="raw dir with map/t_*.json[.gz] and relfull_*.json[.gz]")
    ap.add_argument("--gugik", type=Path, help="GUGiK index json (products NMT/ORTO/NMPT, rows with ring)")
    ap.add_argument("--budget-snapshot", action="store_true")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--print-regions", action="store_true")
    ap.add_argument("--init-regions", action="store_true")
    a = ap.parse_args()
    if a.extract:
        ex, man = build_extract(a.extract)
        PLANS.mkdir(parents=True, exist_ok=True)
        EXTRACT.write_text(dump(ex), encoding="utf-8", newline="\n")
        man["extract_in_git"]["sha256"] = sha256_file(EXTRACT)
        MANIFEST.write_text(dump(man), encoding="utf-8", newline="\n")
        print("extract", EXTRACT.relative_to(REPO), len(ex["ways"]), "ways")
    if a.gugik:
        GUGIK.write_text(dump(build_gugik(json.loads(a.gugik.read_text(encoding="utf-8")))), encoding="utf-8", newline="\n")
        print("gugik", GUGIK.relative_to(REPO))
    if a.budget_snapshot:
        BUDGET.write_text(dump(build_budget_snapshot()), encoding="utf-8", newline="\n")
        print("budget", BUDGET.relative_to(REPO))
    ex = json.loads(EXTRACT.read_text(encoding="utf-8"))
    gg = json.loads(GUGIK.read_text(encoding="utf-8"))
    bu = json.loads(BUDGET.read_text(encoding="utf-8"))
    plan = build_plan(ex, gg, bu)
    PLAN.write_text(dump(plan), encoding="utf-8", newline="\n")
    print("plan", PLAN.relative_to(REPO), [o["id"] for o in plan["order"]])
    if a.png:
        render(plan, ex, PNG)
        print("png", PNG.relative_to(REPO))
    if a.print_regions:
        print(print_regions(plan))
    if a.init_regions:
        print("written", init_regions(plan, gg))


if __name__ == "__main__":
    main()
