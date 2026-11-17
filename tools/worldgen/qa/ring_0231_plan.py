"""ADR 0231 (D63/D64): rough definition of the next ring of tiles past Knyszyn - DK65 to Monki, DW671 to Tykocin and
DW671 north of Knyszyn (towards Jasionowka) - on the 2048 m lattice of ADR 0203.

    uv run --project tools/worldgen python tools/worldgen/qa/ring_0231_plan.py                 # extract -> plan json
    uv run --project tools/worldgen python tools/worldgen/qa/ring_0231_plan.py --png           # + control render
    uv run --project tools/worldgen python tools/worldgen/qa/ring_0231_plan.py --init-regions  # authored files (missing only)
    uv run --project tools/worldgen python tools/worldgen/qa/ring_0231_plan.py --print-regions # regions.py entries
    ... --extract <dir with major.json minor.json admin.json>   # Overpass answers -> Data/Plans/ring-0231/osm_ring_extract.json
    ... --nmt-rows <json>                                       # GUGiK NMT sheet index rows -> ring_0231_nmt_coverage.json

Inputs in git: Data/Plans/ring-0231/osm_ring_extract.json (OSM, ODbL; manifest Data/SourceManifests/
osm-overpass-ring-0231.json) and tools/worldgen/regions.py. The plan stage is deterministic (no clock, no network):
tests/gis/test_ring_0231.py rebuilds it and compares with docs/reports/map/ring_0231_plan.json.

The extract comes from Overpass (2026-11-15), the pipeline builds from the pinned Geofabrik pbf (2026-11-08): OSM way
ids and seam points are compared with the roads.graph.json of the already built neighbour tiles (`existing_seams`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import linemerge, polygonize, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import regions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
EXTRACT = REPO / "Data" / "Plans" / "ring-0231" / "osm_ring_extract.json"
MANIFEST = REPO / "Data" / "SourceManifests" / "osm-overpass-ring-0231.json"
PLAN = REPO / "docs" / "reports" / "map" / "ring_0231_plan.json"
PNG = REPO / "docs" / "reports" / "map" / "ring_0231_plan.png"
NMT = REPO / "docs" / "reports" / "map" / "ring_0231_nmt_coverage.json"
REG = REPO / "Data" / "Regions"
ADR = "0231"
C = regions.REGIONS["bialystok-industrial-c"]
X0, Y0, T = C.bbox[0], C.bbox[1], regions.TILE_SIZE_M
MARGIN_M = T                      # extract keeps OSM elements within one tile of the ring
EXTRA_POWIAT_MIN_SHARE = 0.0      # every powiat the tile touches (was 5 %: tykocin 3.95 % in 2008 then missed its BDOT10k /
                                  # LoD and broke the PRG registry check of ADR 0219; world2-finish 2026-11-17, ADR 0231 §5a)
GENERIC_UA = "research-fetch/1.0"

# corridor -> (road ref, already built region the corridor continues from, tiles in driving order: id, lattice i, j)
CORRIDORS: dict[str, dict] = {
    "dk65-monki": {
        "ref": "65", "frm": "dk65-monki-01", "candidate": "M_dk65_monki",
        "tiles": [("dk65-monki-02", -10, 9), ("dk65-monki-03", -10, 10), ("dk65-monki-04", -11, 10),
                  ("dk65-monki-05", -11, 11), ("dk65-monki-06", -12, 11), ("dk65-monki-07", -12, 12),
                  ("monki-e", -12, 13), ("monki", -13, 13)],
    },
    "dw671-tykocin": {
        "ref": "671", "frm": "dw671-tykocin-01", "candidate": "T_dw671_tykocin",
        "tiles": [("dw671-tykocin-02", -9, 6), ("dw671-tykocin-03", -10, 6), ("dw671-tykocin-04", -10, 5),
                  ("dw671-tykocin-05", -11, 5), ("dw671-tykocin-06", -11, 4), ("dw671-tykocin-07", -12, 4),
                  ("dw671-tykocin-08", -12, 3), ("dw671-tykocin-09", -13, 3), ("tykocin", -13, 2)],
    },
    "dw671-jasionowka": {
        "ref": "671", "frm": "knyszyn", "candidate": "J_dw671_jasionowka",
        "tiles": [("dw671-jasionowka-01", -8, 9)],
    },
}
# regions.py titles (Polish, like the existing entries): road, km of the corridor from the built tile (plan json),
# places = OSM place=town|village nodes inside the tile (not necessarily on the road)
TITLES: dict[str, str] = {
    "dk65-monki-02": "DK65 w stronę Moniek 02 — km 0,0–2,1 za dk65-monki-01, most na Nareśli",
    "dk65-monki-03": "DK65 w stronę Moniek 03 — narożnik kafla, km 2,1–2,5 (w kaflu Czechowizna)",
    "dk65-monki-04": "DK65 w stronę Moniek 04 — km 2,5–5,4 (w kaflu linia kolejowa)",
    "dk65-monki-05": "DK65 w stronę Moniek 05 — narożnik kafla, km 5,4–5,5 (w kaflu Konopczyn, Przytulanka)",
    "dk65-monki-06": "DK65 w stronę Moniek 06 — km 5,5–7,6 (w kaflu Magnusze)",
    "dk65-monki-07": "DK65 w stronę Moniek 07 — km 7,6–9,9, wjazd do Moniek (Białostocka; w kaflu Ciesze)",
    "monki-e": "Mońki wschód — DK65 Białostocka, narożnik kafla km 9,9–10,2 (w kaflu Świerzbienie)",
    "monki": "Mońki — DK65 Białostocka/Ełcka przez miasto, przejazd kolejowy, km 10,2–12,9",
    "dw671-tykocin-02": "DW671 w stronę Tykocina 02 — narożnik kafla (0,1 km), linia kolejowa",
    "dw671-tykocin-03": "DW671 w stronę Tykocina 03 — km 0,1–2,3 (w kaflu Krypno Kościelne, Krypno Wielkie)",
    "dw671-tykocin-04": "DW671 w stronę Tykocina 04 — km 2,3–4,2",
    "dw671-tykocin-05": "DW671 w stronę Tykocina 05 — km 4,2–4,9",
    "dw671-tykocin-06": "DW671 w stronę Tykocina 06 — km 4,9–7,0 (w kaflu Zygmunty)",
    "dw671-tykocin-07": "DW671 w stronę Tykocina 07 — km 7,0–8,0 (w kaflu Morusy)",
    "dw671-tykocin-08": "DW671 w stronę Tykocina 08 — km 8,0–9,7",
    "dw671-tykocin-09": "DW671 w stronę Tykocina 09 — km 9,7–10,8 (w kaflu Tatary)",
    "tykocin": "Tykocin — DW671 przez miasto i most na Narwi, km 10,8–13,3",
    "dw671-jasionowka-01": "DW671 w stronę Jasionówki 01 — Grodzieńska na północ od Knyszyna, km 0,0–2,4",
}
# the DK65 cross-section and lamp rule of dk65-monki-01 (ADR 0212), continued on the rural DK65 of the corridor
DK65_SET = {"lanes": 2, "lane_width": 3.4, "edge_strip": 0.35, "edge_lines": "both"}
TAGS_KEPT = ("highway", "ref", "name", "lanes", "maxspeed", "lit", "surface", "width", "bridge", "tunnel", "layer",
             "junction", "oneway", "maxweight", "hgv", "construction", "proposed")


def tile_bbox(i: int, j: int) -> tuple[float, float, float, float]:
    return (X0 + T * i, Y0 + T * j, X0 + T * (i + 1), Y0 + T * (j + 1))


def ring_tiles() -> list[tuple[str, int, int, str]]:
    return [(tid, i, j, cname) for cname, c in CORRIDORS.items() for tid, i, j in c["tiles"]]


def ring_area():
    return unary_union([box(*tile_bbox(i, j)) for _, i, j, _ in ring_tiles()]).buffer(MARGIN_M, join_style=2)


def _tr(inverse: bool = False) -> Transformer:
    a, b = ("EPSG:2180", "EPSG:4326") if inverse else ("EPSG:4326", regions.WORK_CRS)
    return Transformer.from_crs(a, b, always_xy=True)


def refs(tags: dict) -> list[str]:
    return [r.strip() for r in tags.get("ref", "").split(";") if r.strip()]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------------------------- extract (needs raw)
def build_extract(raw: Path) -> dict:
    """Overpass answers (outside git) -> the small extract kept in git (lon/lat as delivered, EPSG:4326)."""
    tr, area = _tr(), ring_area()
    src, ways, nodes = [], {}, {}

    def line(geom):
        return LineString([tr.transform(p["lon"], p["lat"]) for p in geom])

    for name in ("major", "minor", "admin"):
        p = raw / f"{name}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        src.append({"name": name, "sha256": sha256_file(p), "bytes": p.stat().st_size,
                    "query": (raw / f"{name}.ql").read_text(encoding="utf-8").strip(),
                    "endpoint": (raw / f"{name}.url").read_text(encoding="utf-8").strip(),
                    "fetched_utc": (raw / f"{name}.utc").read_text(encoding="utf-8").strip(),
                    "timestamp_osm_base": d["osm3s"]["timestamp_osm_base"]})
        if name == "admin":
            admin = d
            continue
        for e in d["elements"]:
            t = e.get("tags", {})
            if e["type"] == "way":
                hw = t.get("highway")
                keep = (("highway" in t and ({"65", "671"} & set(refs(t)) or hw in ("construction", "proposed")))
                        or t.get("railway") == "rail" or t.get("waterway") in ("river", "canal"))
                if keep and line(e["geometry"]).intersects(area):
                    ways[e["id"]] = {"id": e["id"], "tags": dict(sorted(t.items())),
                                     "lonlat": [[p["lon"], p["lat"]] for p in e["geometry"]]}
            elif e["type"] == "node" and (t.get("railway") == "level_crossing" or t.get("place") in ("town", "village")):
                if Point(tr.transform(e["lon"], e["lat"])).intersects(area):
                    nodes[e["id"]] = {"id": e["id"], "tags": dict(sorted(t.items())), "lonlat": [e["lon"], e["lat"]]}
    inv, powiaty = _tr(inverse=True), {}
    for e in admin["elements"]:
        t = e["tags"]
        if t.get("admin_level") != "6":
            continue
        lines = [line(m["geometry"]) for m in e["members"] if m["type"] == "way" and m.get("geometry")]
        clip = unary_union(list(polygonize(unary_union(lines)))).intersection(area)
        polys = [clip] if isinstance(clip, Polygon) else list(clip.geoms) if isinstance(clip, MultiPolygon) else []
        powiaty[t["teryt:terc"]] = {
            "name": t["name"], "osm_relation": e["id"],
            "rings_lonlat": [[[round(v, 7) for v in inv.transform(x, y)] for x, y in pg.exterior.coords]
                             for pg in sorted(polys, key=lambda g: -g.area) if pg.area > 1.0]}
    return {"adr": ADR, "crs": "EPSG:4326 (OSM lon/lat as delivered by Overpass)",
            "license": "ODbL 1.0, © OpenStreetMap contributors", "sources": src,
            "filter": ("ways: highway with ref 65 or 671, highway=construction|proposed, railway=rail, waterway=river|canal; "
                       "nodes: railway=level_crossing, place=town|village; kept when within 2048 m of a ring tile. "
                       "powiaty: admin_level=6 relations polygonised and clipped to the same area."),
            "ways": [ways[k] for k in sorted(ways)], "nodes": [nodes[k] for k in sorted(nodes)],
            "powiaty": dict(sorted(powiaty.items()))}


# ---------------------------------------------------------------------------------------------- plan (deterministic)
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
    return []                      # a line along the tile edge is not a crossing


def _shared_edge(a, b) -> str | None:
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


def _graph_crossings(region_id: str, edge: str, bb) -> list[dict] | None:
    """Boundary nodes of an already built tile on one of its edges (roads.graph.json, pbf of the pipeline)."""
    p = REG / region_id / "roads.graph.json"
    if not p.exists():
        return None
    g = json.loads(p.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in g["nodes"]}
    out = {}
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if _edge_of(bb, n["x"], n["y"]) == edge:
                ref = (e["attrs"].get("ref") or {}).get("v")
                out[(e["osm_way"], round(n["x"], 1), round(n["y"], 1))] = {
                    "osm_way": e["osm_way"], "x": round(n["x"], 1), "y": round(n["y"], 1), "ref": ref}
    return [out[k] for k in sorted(out)]


def build_plan(extract: dict) -> dict:
    tr = _tr()
    L = {w["id"]: LineString([tr.transform(lon, lat) for lon, lat in w["lonlat"]]) for w in extract["ways"]}
    W = {w["id"]: w["tags"] for w in extract["ways"]}
    powiat = {k: unary_union([Polygon([tr.transform(lon, lat) for lon, lat in r]) for r in v["rings_lonlat"]])
              for k, v in extract["powiaty"].items()}
    rail = [k for k in sorted(W) if W[k].get("railway") == "rail"]
    water = [k for k in sorted(W) if "waterway" in W[k]]
    constr = [k for k in sorted(W) if W[k].get("highway") in ("construction", "proposed")]
    nodes = [(n, Point(tr.transform(*n["lonlat"]))) for n in extract["nodes"]]
    tiles, seams, existing, corridors = [], [], [], {}
    for cname, c in CORRIDORS.items():
        road = [k for k in sorted(W) if "highway" in W[k] and c["ref"] in refs(W[k])
                and W[k]["highway"] not in ("construction", "proposed")]
        frm = regions.get(c["frm"])
        seq = [(c["frm"], frm.bbox)] + [(tid, tile_bbox(i, j)) for tid, i, j in c["tiles"]]
        km, ctiles = 0.0, []
        for n, (tid, i, j) in enumerate(c["tiles"], start=1):
            bb = tile_bbox(i, j)
            tb = box(*bb)
            prev_id, prev_bb = seq[n - 1]
            nxt = seq[n + 1] if n + 1 < len(seq) else None
            e_in = _shared_edge(bb, prev_bb)
            e_out = _shared_edge(bb, nxt[1]) if nxt else None
            ways, cross, pieces = [], [], []
            for k in road:
                g = L[k].intersection(tb)
                if g.length <= 0:
                    continue
                pieces.append(g)
                ways.append({"osm_way": k, "length_m": round(g.length, 1),
                             "tags": {t: W[k][t] for t in TAGS_KEPT if t in W[k]}})
                for p in _points(L[k].intersection(tb.exterior)):
                    ed = _edge_of(bb, p.x, p.y)
                    if ed:
                        cross.append({"osm_way": k, "edge": ed, "x": round(p.x, 1), "y": round(p.y, 1)})
            cross.sort(key=lambda d: (d["edge"], d["x"], d["y"], d["osm_way"]))
            merged = unary_union(pieces) if pieces else LineString()
            if merged.geom_type == "MultiLineString":
                merged = linemerge(merged)
            single = merged.geom_type == "LineString" and not merged.is_empty
            entry = [d for d in cross if d["edge"] == e_in]
            exit_ = [d for d in cross if d["edge"] == e_out] if e_out else []
            chain = None
            if single:
                co = list(merged.coords)
                if entry and Point(co[-1]).distance(Point(entry[0]["x"], entry[0]["y"])) < Point(co[0]).distance(
                        Point(entry[0]["x"], entry[0]["y"])):
                    co = co[::-1]
                chain = [[round(x, 1), round(y, 1)] for x, y in co]
                ways.sort(key=lambda d: LineString(co).project(L[d["osm_way"]].intersection(tb).centroid))
            else:
                ways.sort(key=lambda d: d["osm_way"])
            thr = unary_union(pieces) if pieces else LineString()
            # features of the through road inside the tile
            bridges = [{"osm_way": d["osm_way"], "length_m": d["length_m"],
                        "over": sorted({W[k].get("name") or W[k]["waterway"] for k in water
                                        if L[k].distance(L[d["osm_way"]].intersection(tb)) < 30.0})}
                       for d in ways if d["tags"].get("bridge")]
            atgrade = unary_union([L[d["osm_way"]].intersection(tb) for d in ways
                                   if not d["tags"].get("bridge") and not d["tags"].get("tunnel")] or [LineString()])
            lcs = []
            for k in rail:
                if W[k].get("bridge") or W[k].get("tunnel"):
                    continue
                for p in _points(L[k].intersection(atgrade)):
                    near = sorted((q.distance(p), nd["id"]) for nd, q in nodes
                                  if nd["tags"].get("railway") == "level_crossing" and q.distance(p) < 5.0)
                    lcs.append({"x": round(p.x, 1), "y": round(p.y, 1), "rail_way": k,
                                "osm_node": near[0][1] if near else None})
            lcs.sort(key=lambda d: (d["x"], d["y"], d["rail_way"]))
            wcross = []
            for k in water:
                for p in _points(L[k].intersection(thr)):
                    wcross.append({"x": round(p.x, 1), "y": round(p.y, 1), "waterway": W[k]["waterway"],
                                   "name": W[k].get("name"), "osm_way": k})
            wcross.sort(key=lambda d: (d["x"], d["y"], d["osm_way"]))
            shares = {k: round(pg.intersection(tb).area / tb.area, 4) for k, pg in sorted(powiat.items())
                      if pg.intersection(tb).area > 0}
            order = sorted(shares, key=lambda k: (-shares[k], k))
            route_share = {k: round(thr.intersection(pg).length / thr.length, 4) for k, pg in sorted(powiat.items())
                           if thr.length > 0 and thr.intersection(pg).length > 0}
            tile = {
                "id": tid, "corridor": cname, "ij": [i, j], "bbox": list(bb),
                "origin": [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2],
                "teryt_powiat": order[0],
                "teryt_powiat_extra": [k for k in order[1:] if shares[k] >= EXTRA_POWIAT_MIN_SHARE],
                "powiat_area_share": shares, "powiat_route_share": route_share,
                "prev": prev_id, "next": nxt[0] if nxt else None,
                "through": {"ref": c["ref"], "length_m": round(thr.length, 1), "single_chain": single,
                            "km_from": round(km / 1000, 2), "km_to": round((km + thr.length) / 1000, 2),
                            "ways": ways, "entry": entry, "exit": exit_,
                            "other_crossings": [d for d in cross if d["edge"] not in (e_in, e_out)], "chain": chain},
                "features": {
                    "bridges": bridges, "level_crossings": lcs, "water_crossings": wcross,
                    "rail_m": round(sum(L[k].intersection(tb).length for k in rail), 1),
                    "construction_m": round(sum(L[k].intersection(tb).length for k in constr), 1),
                    "places": sorted(nd["tags"].get("name", "?") + " (" + nd["tags"]["place"] + ")"
                                     for nd, q in nodes if "place" in nd["tags"] and tb.contains(q)),
                },
            }
            km += thr.length
            tiles.append(tile)
            ctiles.append(tile)
        corridors[cname] = {"ref": c["ref"], "from_region": c["frm"], "tiles": [t["id"] for t in ctiles],
                            "length_m": round(km, 1)}
        # seams inside the ring: exit of a == entry of b (same ways, same points)
        for a, b in zip(ctiles, ctiles[1:]):
            seams.append({"a": a["id"], "b": b["id"], "edge_of_a": _shared_edge(tuple(a["bbox"]), tuple(b["bbox"])),
                          "a_exit": a["through"]["exit"], "b_entry": b["through"]["entry"]})
        # seam with the already built tile: OSM way + point of the neighbour's graph (pinned pbf) vs this extract
        first = ctiles[0]
        e_first = _shared_edge(frm.bbox, tuple(first["bbox"]))
        gc = _graph_crossings(c["frm"], e_first, frm.bbox)
        gref = [d for d in (gc or []) if d["ref"] == c["ref"]]
        existing.append({
            "built": c["frm"], "new": first["id"], "edge_of_built": e_first, "ref": c["ref"],
            "built_graph_ref_crossings": gref, "new_entry": first["through"]["entry"],
            "max_offset_m": (round(max(min(Point(g["x"], g["y"]).distance(Point(d["x"], d["y"])) for g in gref)
                                       for d in first["through"]["entry"]), 2)
                             if gref and first["through"]["entry"] else None),
            "same_ways": (sorted({g["osm_way"] for g in gref}) == sorted({d["osm_way"] for d in first["through"]["entry"]})
                          if gref else None)})
    return {
        "adr": ADR, "crs": regions.WORK_CRS, "tile_size_m": T,
        "lattice": {"x0": X0, "y0": Y0, "anchor_region": C.id, "rule": "x = x0 + 2048*i, y = y0 + 2048*j (ADR 0203)"},
        "source": {"extract": EXTRACT.relative_to(REPO).as_posix(), "manifest": MANIFEST.relative_to(REPO).as_posix(),
                   "timestamp_osm_base": sorted({s["timestamp_osm_base"] for s in extract["sources"]})},
        "rules": {"teryt_powiat": "largest area share of the tile (OSM admin_level=6 polygons)",
                  "teryt_powiat_extra_min_area_share": EXTRA_POWIAT_MIN_SHARE,
                  "note": "WORKING_VALUE threshold; ADR 0214 used BDOT10k land-cover shares, not available here"},
        "corridors": corridors, "tiles": tiles, "seams": seams, "existing_seams": existing,
    }


# ---------------------------------------------------------------------------------------------- authored files
def _rural_dk65_ways(tile: dict) -> list[int]:
    """DK65 ways outside built-up streets: primary, not named (no street name), not a roundabout, two-way."""
    return sorted(d["osm_way"] for d in tile["through"]["ways"]
                  if d["tags"].get("highway") == "primary" and "name" not in d["tags"]
                  and "junction" not in d["tags"] and d["tags"].get("oneway") != "yes")


def overrides_yaml(tile: dict) -> str:
    tid, o = tile["id"], tile["origin"]
    head = (f"# Authored overrides of region {tid} (ADR {ADR}, rough definition: the tile is NOT ingested or built yet).\n"
            f"# Every entry survives a re-import; coordinates are region-local E/N (origin EPSG:2180 {o[0]:.0f}, {o[1]:.0f})\n"
            f"# or EPSG:2180 where the key says so. Source of the targets: OSM via Overpass 2026-11-15\n"
            f"# (Data/Plans/ring-0231/osm_ring_extract.json); the pipeline builds from the pbf of 2026-11-08, so a way id\n"
            f"# that is missing there shows up as overrides_stale in build_world. No lettering, no brands.\n")
    ways = _rural_dk65_ways(tile) if tile["through"]["ref"] == "65" else []
    if not ways:
        why = ("DW671 keeps the BDOT10k width and gets no edge lines, as in dw671-tykocin-01 (ADR 0212, measured there)."
               if tile["through"]["ref"] == "671" else
               "DK65 inside the town: streets with names, kerbs and lighting - no rural cross-section override.")
        return head + f"# {why}\n# Nothing was checked on the orthophoto of this tile: add overrides after the ingest.\noverrides: []\n"
    w = "[" + ", ".join(str(k) for k in ways) + "]"
    return head + f"""overrides:
  - id: dk65-carriageway-width
    target: {{osm_way: {w}}}
    reason: >-
      DK65 towards Monki, rural single carriageway (OSM: highway=primary, lanes=2). WORKING_VALUE: the cross-section
      of dk65-monki-01 / knyszyn-w (ADR 0204/0209/0212: 2 x 3.4 m + 0.35 m edge strips = 7.5 m, solid edge lines on
      both sides) is continued so that the seam keeps one width and one set of lines. NOT measured in this tile
      (no orthophoto in the session that wrote ADR {ADR}); BDOT10k width unknown until build_region runs.
    confidence: low
    verify: "orthophoto 0.1 m cross profiles after the ingest (tool of ADR 0212 - artifacts/knyszyn-edges-0212/tools/linew.py); owner drive"
    set: {{lanes: {DK65_SET['lanes']}, lane_width: {DK65_SET['lane_width']}, edge_strip: {DK65_SET['edge_strip']}, edge_lines: {DK65_SET['edge_lines']}}}
  - id: dk65-fields-unlit
    target: {{osm_way: {w}}}
    reason: >-
      DK65 outside built-up areas (OSM: no street name on these ways, maxspeed=90 where tagged, no `lit` tag).
      WORKING_VALUE: continues dk65-fields-unlit of dk65-monki-01 (orthophoto 2025 there: no lamp columns); the
      lamp rule would light every class G road. NOT checked on the orthophoto of this tile - villages along the
      road may have columns.
    confidence: low
    verify: orthophoto 0.1 m after the ingest
    set: {{lamps: false}}
"""


def sources_authored(tile: dict, cover: dict) -> str:
    c = cover["tiles"][tile["id"]]
    days = ", ".join(c["by_year"]["2022"]["days"])
    return json.dumps({
        "provenance": f"authored_override (ADR {ADR}, mechanism of ADR 0209/0212): source pins of region {tile['id']}, read by ingest.py and build_region.py",
        "pins": {"nmt_year": "2022"},
        "reason": (f"Every tile of the ring and its built neighbours (knyszyn, knyszyn-w, dk65-monki-01, dw671-tykocin-01, "
                   f"dk65-11) use the NMT 2022 series, so shared edges get the same samples. GUGiK sheet index "
                   f"(SkorowidzNMT, queried {cover['queried_utc'][:10]}): the 2022 series (flight days {days}) fully covers this "
                   f"tile; without the pin ingest.py would take {', '.join(c['default_day']) or 'none'} here and the survey year would "
                   f"change from tile to tile. See docs/reports/map/ring_0231_nmt_coverage.json."),
        "verify": "none (move together with the pins of the neighbours)",
    }, indent=1, ensure_ascii=False) + "\n"


def route_endpoints(tile: dict) -> str | None:
    th = tile["through"]
    ends = th["exit"] or th["other_crossings"]
    if not th["entry"] or not ends:
        return None
    a, b = th["entry"][0], ends[-1 if not th["exit"] else 0]
    nxt = f"seam with {tile['next']}" if tile["next"] else "end of the ring (next lattice tile not defined)"
    road = ("DK" if th["ref"] == "65" else "DW") + th["ref"]
    return json.dumps({
        "provenance": f"authored_override (ADR {ADR}): control route for cameras/QA = {road} inside this tile, continuing the route of {tile['prev']}",
        "description": (f"{road} from the {a['edge']} tile edge (seam with {tile['prev']}, OSM way {a['osm_way']}) to the "
                        f"{b['edge']} tile edge (OSM way {b['osm_way']}; {nxt}). Points from the Overpass extract of 2026-11-15; "
                        f"build_world snaps them to the nearest graph node."),
        "start_epsg2180": [a["x"], a["y"]],
        "end_epsg2180": [b["x"], b["y"]],
        "confidence": "medium (OSM 2026-11-15 vs the pinned pbf 2026-11-08: re-check after build_region that both are graph boundary nodes)",
    }, indent=1, ensure_ascii=False) + "\n"


def graph_filter() -> str:
    src = json.loads((REG / "dk65-monki-01" / "graph_filter.authored.json").read_text(encoding="utf-8"))
    return json.dumps({
        "provenance": f"authored_override (ADR 0204, reused by ADR 0209/0212 and ADR {ADR}): ways left out of the drivable road graph of this region",
        "drop_service": src["drop_service"], "drop_osm_ways": [],
        "reason": ("Same rule as every built tile of powiat moniecki (knyszyn, knyszyn-w, knyszyn-s, dk65-monki-01, "
                   "dw671-tykocin-01): OSM maps house driveways as highway=service + service=driveway; as graph junctions "
                   "closer than ~15 m they left holes in the carriageway (ADR 0204). Not re-checked for this tile."),
        "verify": "none (generator limitation; revisit when junctions closer than ~15 m are supported)",
    }, indent=1, ensure_ascii=False) + "\n"


def init_regions(plan: dict, cover: dict) -> list[str]:
    written = []
    for t in plan["tiles"]:
        d = REG / t["id"]
        d.mkdir(parents=True, exist_ok=True)
        files = {"overrides.yaml": overrides_yaml(t), "sources.authored.json": sources_authored(t, cover),
                 "route_endpoints.json": route_endpoints(t), "graph_filter.authored.json": graph_filter()}
        for name, text in files.items():
            if text is not None and not (d / name).exists():     # authored files: never overwritten
                (d / name).write_text(text, encoding="utf-8", newline="\n")
                written.append(f"{t['id']}/{name}")
    return written


def print_regions(plan: dict, titles: dict) -> str:
    out = []
    for t in plan["tiles"]:
        bb, o = t["bbox"], t["origin"]
        extra = (f"\n        teryt_powiat_extra=({', '.join(repr(k) for k in t['teryt_powiat_extra'])},),"
                 if t["teryt_powiat_extra"] else "")
        out.append(f'''    "{t['id']}": Region(
        id="{t['id']}",
        title="{titles.get(t['id'], t['id'])}",
        candidate="{CORRIDORS[t['corridor']]['candidate']}",
        bbox=({bb[0]}, {bb[1]}, {bb[2]}, {bb[3]}),
        origin=({o[0]}, {o[1]}),
        teryt_powiat="{t['teryt_powiat']}",{extra}
        status="WORKING_ASSUMPTION (ADR {ADR}, owner D63/D64; tile = lattice ({t['ij'][0]},{t['ij'][1]}) of the ADR 0203 plan)",
    ),''')
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------- NMT coverage
def nmt_coverage(rows: list[dict], queried_utc: str) -> dict:
    """Per tile: NMT 1 m ARC/INFO EVRF2007 series that fully cover it, by survey year (ingest.pick_latest logic)."""
    import ingest
    base = lambda r: (r.get("char_przestrz") == "1.00 m" and r.get("format", "").startswith("ARC/INFO")  # noqa: E731
                      and r.get("uklad_h") == "PL-EVRF2007-NH")
    out = {}
    for tid, i, j, _ in ring_tiles():
        bb, by = tile_bbox(i, j), {}
        for yr in sorted({r["akt_rok"] for r in rows if base(r)}):
            got = ingest.pick_latest(rows, bb, lambda r, yr=yr: base(r) and r.get("akt_rok") == yr, key="akt_rok")
            if got:
                by[yr] = {"days": sorted({r["akt_data"] for r in got})}
                if yr == "2022":                                   # the pinned year: sheets listed
                    by[yr]["sheets"] = sorted(r["godlo"] for r in got)
        out[tid] = {"by_year": by, "default_day": sorted({r["akt_data"] for r in ingest.pick_latest(rows, bb, base)})}
    return {"adr": ADR, "queried_utc": queried_utc, "product": "NMT 1.00 m, ARC/INFO ASCII GRID, PL-EVRF2007-NH",
            "index_service": "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NumerycznyModelTerenuEVRF2007/WFS/Skorowidze",
            "note": ("by_year: survey years whose sheets fully cover the tile when the flight days of one year are joined "
                     "(ingest.pick_latest key=akt_rok, the path taken with a pin); default_day: the single flight day "
                     "ingest.py takes without a pin."),
            "tiles": out}


def fetch_nmt_rows() -> tuple[list[dict], str]:
    """GUGiK sheet index for the bbox of the ring (one WFS request per survey-year layer; generic User-Agent)."""
    import datetime
    import gugik_index as gi
    gi.USER_AGENT = GENERIC_UA
    b = ring_area().bounds
    sheets = gi.query("NMT", b)
    rows = gi.summarise(sheets)
    for row, sh in zip(rows, sheets):
        row["ring"] = [[round(x, 2), round(y, 2)] for x, y in sh.ring]
    return rows, datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------------------------- control render
def render(plan: dict, extract: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    tr = _tr()
    fig, ax = plt.subplots(figsize=(11, 15), dpi=110)
    new_ids = {t["id"] for t in plan["tiles"]}
    for k, v in extract["powiaty"].items():
        for r in v["rings_lonlat"]:
            xs, ys = zip(*[tr.transform(lon, lat) for lon, lat in r])
            ax.fill(xs, ys, color="#f3efe4" if k == "2008" else "#e6eef3", zorder=0)
    for w in extract["ways"]:
        t = w["tags"]
        xs, ys = zip(*[tr.transform(lon, lat) for lon, lat in w["lonlat"]])
        if "waterway" in t:
            ax.plot(xs, ys, color="#5b9bd5", lw=1.4 if t["waterway"] == "river" else 0.5, zorder=1)
        elif t.get("railway"):
            ax.plot(xs, ys, color="#333333", lw=0.9, ls=(0, (6, 3)), zorder=2)
        elif t.get("highway") in ("construction", "proposed"):
            ax.plot(xs, ys, color="#b58900", lw=0.8, ls=":", zorder=2)
        elif "65" in refs(t):
            ax.plot(xs, ys, color="#c0392b", lw=2.2, zorder=4)
        elif "671" in refs(t):
            ax.plot(xs, ys, color="#d68910", lw=2.0, zorder=4)
    for r in regions.REGIONS.values():
        if r.id in new_ids or r.bbox[0] > 765000:
            continue
        ax.add_patch(Rectangle(r.bbox[:2], T, T, fc="#bdbdbd", ec="#555555", lw=0.8, alpha=0.55, zorder=3))
        ax.text(r.origin[0], r.origin[1], r.id, ha="center", va="center", fontsize=6.5, color="#222222", zorder=6)
    col = {"dk65-monki": "#c0392b", "dw671-tykocin": "#d68910", "dw671-jasionowka": "#7d3c98"}
    for t in plan["tiles"]:
        bb = t["bbox"]
        ax.add_patch(Rectangle(bb[:2], T, T, fc=col[t["corridor"]], ec=col[t["corridor"]], lw=1.4, alpha=0.16, zorder=3))
        ax.add_patch(Rectangle(bb[:2], T, T, fc="none", ec=col[t["corridor"]], lw=1.4, zorder=5))
        ax.text(bb[0] + 60, bb[3] - 80, f"{t['id']}\n({t['ij'][0]},{t['ij'][1]}) {t['through']['length_m']:.0f} m",
                ha="left", va="top", fontsize=6.5, color="#111111", zorder=6)
        for d in t["features"]["level_crossings"]:
            ax.plot(d["x"], d["y"], marker="x", color="black", ms=7, mew=1.6, zorder=7)
        for d in t["through"]["entry"] + t["through"]["exit"] + t["through"]["other_crossings"]:
            ax.plot(d["x"], d["y"], marker="o", mfc="white", mec="black", ms=4, mew=0.8, zorder=7)
    for n in extract["nodes"]:
        if n["tags"].get("place") == "town":
            x, y = tr.transform(*n["lonlat"])
            ax.plot(x, y, marker="*", color="#111111", ms=11, zorder=8)
            ax.text(x + 150, y + 150, n["tags"]["name"], fontsize=10, fontweight="bold", zorder=8)
    b = ring_area().bounds
    ax.set_xlim(b[0] - 500, max(b[2], 765200) + 500)
    ax.set_ylim(b[1] - 500, b[3] + 500)
    ax.set_aspect("equal")
    ax.set_xlabel("EPSG:2180 x (east) [m]")
    ax.set_ylabel("EPSG:2180 y (north) [m]")
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.tick_params(labelsize=7)
    ax.set_title(f"ADR {ADR}: next ring of tiles (rough definition). Red DK65, orange DW671, dashed rail, blue water,\n"
                 "grey = tiles already built, x = level crossing on the through road, o = seam / edge crossing.\n"
                 "Data: © OpenStreetMap contributors (ODbL), Overpass 2026-11-15. North up, 1 tile = 2048 m.", fontsize=8)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", metavar="RAW_DIR", help="rebuild the extract from Overpass answers (outside git)")
    ap.add_argument("--nmt-rows", metavar="JSON", help="NMT index rows {utc, rows} (else: --nmt-fetch)")
    ap.add_argument("--nmt-fetch", action="store_true", help="query the GUGiK NMT sheet index (network)")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--init-regions", action="store_true", help="write missing authored files of the new tiles")
    ap.add_argument("--print-regions", action="store_true")
    a = ap.parse_args()
    if a.extract:
        EXTRACT.parent.mkdir(parents=True, exist_ok=True)
        EXTRACT.write_text(dump(build_extract(Path(a.extract))), encoding="utf-8", newline="\n")
        print("extract", EXTRACT, sha256_file(EXTRACT))
    if a.nmt_rows or a.nmt_fetch:
        if a.nmt_rows:
            d = json.loads(Path(a.nmt_rows).read_text(encoding="utf-8"))
            rows, utc = d["rows"], d["utc"]
        else:
            rows, utc = fetch_nmt_rows()
        NMT.write_text(dump(nmt_coverage(rows, utc)), encoding="utf-8", newline="\n")
        print("nmt", NMT)
    extract = json.loads(EXTRACT.read_text(encoding="utf-8"))
    plan = build_plan(extract)
    PLAN.write_text(dump(plan), encoding="utf-8", newline="\n")
    for c, v in plan["corridors"].items():
        print(c, v["length_m"], "m", len(v["tiles"]), "tiles")
    for t in plan["tiles"]:
        th = t["through"]
        print(f"  {t['id']:22s} {tuple(t['ij'])!s:10s} {th['length_m']:7.1f} m chain={th['single_chain']} "
              f"in={len(th['entry'])} out={len(th['exit'])} other={len(th['other_crossings'])} powiat={t['powiat_area_share']}")
    for s in plan["existing_seams"]:
        print("  seam", s["built"], "->", s["new"], "offset", s["max_offset_m"], "same ways", s["same_ways"])
    if a.init_regions:
        print("written:", init_regions(plan, json.loads(NMT.read_text(encoding="utf-8"))))
    if a.print_regions:
        print(print_regions(plan, TITLES))
    if a.png:
        render(plan, extract, PNG)
        print("png", PNG)


if __name__ == "__main__":
    main()
