"""Shared data bundle and geometry helpers for the world validator.

Everything is in region-local metres: E = x - origin.x, N = y - origin.y (EPSG:2180 minus the region.yaml
origin), the same frame as route_start.json / generated QA. Heights stay absolute PL-EVRF2007-NH where the
source data carries them. The bundle is plain dicts/lists so tests can build synthetic worlds without files.

Thresholds without a cited source are WORKING_VALUE and carry a justification in PARAMS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon

REPO_ROOT = Path(__file__).resolve().parents[3]

# WORKING_VALUEs (justification in docs/reports/WORLD-VALIDATOR-2026-11-13-mistral.md):
SKRAJNIA_M = 0.50            # required clearance object-footprint-edge -> carriageway edge (PTB2022 skrajnia is
                             # 0.50 m from the carriageway edge on class G/Z/L/D urban roads; used as floor here)
KERB_ZONE_M = 0.60           # band outside the carriageway edge treated as "on the kerb" (kerb top 0.15 m +
                             # sign lateral offset practice 0.5-1.0 m; ADR-agnostic floor)
OBJ_FOOTPRINT_M = {          # object radius used for overlap tests (conservative, WORKING_VALUE)
    "power_pole": 0.35, "pylon": 0.60, "tree": None, "sign": 0.30, "lamp": 0.30, "signal": 0.35,
    "bus_stop": 1.60, "crossing": 0.30, "bollard": 0.15, "default": 0.30,
}
MIN_OBJ_SEPARATION_M = 0.30  # two distinct ground objects closer than this overlap each other (WORKING_VALUE)
TREE_IN_BUILDING_OVERLAP = 0.50   # crown-area fraction inside a footprint that counts as tree-in-building
BUILDING_ROAD_AREA_M2 = 0.50      # building/carriageway intersection area that counts as building-in-road
GAP_M = 2.0                       # suspicious gap between segments of one linear feature (WORKING_VALUE)
DUPLICATE_PARALLEL_M = 0.50       # two linear features closer than this are duplicates (task M37)
DUPLICATE_RUN_M = 5.0             # minimum parallel run length to report a duplicate (WORKING_VALUE)
BRIDGE_END_EXEMPT_M = 2.5         # barrier-end gap this close to a deck edge is M29's, not a gap (exclusion)
RECOG_DIST_M = 60.0               # sign recognition distance in built-up area at 50 km/h (WORKING_VALUE)
DRIVER_EYE_M = 2.5                # truck driver eye height above the road (control_cameras.json convention)
ROUTE_BAND_M = 60.0               # extension (a): findings within this distance of the G3 route
PROFILE_RMS_MAX_M = 0.50          # road profile vs NMT RMS above which the road floats / is buried (WORKING_VALUE;
                                  # NMT own error is 0.09 m per terrain.json)
TERRAIN_WALL_MAX_M = 0.50         # exposed terrain/"skirt" wall above which it is a visible wall (WORKING_VALUE;
                                  # terrain_walls_qa.json threshold is 0.15 m for detection)
STOREY_H_MIN_M, STOREY_H_MAX_M = 2.50, 6.50   # plausible storey height band for multi-storey buildings,
                             # calibrated on the region: h/storeys p5..p95 = 2.89..7.11 m (halls with storeys=1
                             # are excluded - LoD height of a hall is not storey-based) WORKING_VALUE

PARAMS = {
    "skrajnia_m": SKRAJNIA_M, "kerb_zone_m": KERB_ZONE_M, "min_obj_separation_m": MIN_OBJ_SEPARATION_M,
    "tree_in_building_overlap": TREE_IN_BUILDING_OVERLAP, "building_road_area_m2": BUILDING_ROAD_AREA_M2,
    "gap_m": GAP_M, "duplicate_parallel_m": DUPLICATE_PARALLEL_M, "duplicate_run_m": DUPLICATE_RUN_M,
    "bridge_end_exempt_m": BRIDGE_END_EXEMPT_M, "recog_dist_m": RECOG_DIST_M, "driver_eye_m": DRIVER_EYE_M,
    "route_band_m": ROUTE_BAND_M, "profile_rms_max_m": PROFILE_RMS_MAX_M, "terrain_wall_max_m": TERRAIN_WALL_MAX_M,
    "storey_h_band_m": [STOREY_H_MIN_M, STOREY_H_MAX_M],
}

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}


@dataclass
class Finding:
    category: str
    e: float
    n: float
    id: str
    detail: str = ""
    severity: str = "warn"
    extra: dict = field(default_factory=dict)
    lat: float | None = None
    lon: float | None = None
    chunk: str | None = None
    on_route: bool = False
    dist_route_m: float | None = None

    def key(self) -> tuple:
        return (self.category, round(self.e, 1), round(self.n, 1), self.id)

    def as_dict(self) -> dict:
        d = {"category": self.category, "e": round(self.e, 2), "n": round(self.n, 2), "id": self.id,
             "detail": self.detail, "severity": self.severity, "lat": self.lat, "lon": self.lon,
             "chunk": self.chunk, "on_route": self.on_route, "dist_route_m": self.dist_route_m}
        d.update(self.extra)
        return d


@dataclass
class World:
    """Validator input: generated + source data of one region, local E/N metres."""
    region_id: str
    origin: tuple[float, float]                     # EPSG:2180 anchor (region.yaml)
    edges: list[dict] = field(default_factory=list)       # {id, osm_way, coords: [[e,n]..], width_m, highway,
                                                          #  lanes, bridge, name}
    buildings: list[dict] = field(default_factory=list)   # {id, poly: Polygon, height_m, storeys, height_source,
                                                          #  ground_z, is_roof_only, name}
    points: list[dict] = field(default_factory=list)      # {id, kind, e, n, tags} (osm_context + osm nodes)
    lines: list[dict] = field(default_factory=list)       # {id, source_id, kind, line: LineString}
                                                          # kind in fence/wall/noise_barrier/retaining_wall/
                                                          # sidewalk/footway
    trees: list[dict] = field(default_factory=list)       # {id, e, n, r, conifer}
    signs: list[dict] = field(default_factory=list)       # {id, code, e, n, faces_route_driver, offset_m, src}
    lamps: list[dict] = field(default_factory=list)       # {id, e, n, z, p, row}
    route: list[list[float]] = field(default_factory=list)  # [[e, n] ..] route_start points_en
    chains_qa: list[dict] = field(default_factory=list)   # roads_qa.json chains
    terrain_walls: dict = field(default_factory=dict)     # terrain_walls_qa.json
    consistency_qa: dict = field(default_factory=dict)     # road_consistency_qa.json (existing, not duplicated)
    manifest: dict = field(default_factory=dict)          # world_manifest.json
    overrides: list[dict] = field(default_factory=list)   # overrides.yaml entries

    def to_abs(self, e: float, n: float) -> tuple[float, float]:
        return (e + self.origin[0], n + self.origin[1])


def _edge_width_m(edge_attrs: dict, bdot: dict, highway: str, lanes: int) -> float:
    """Carriageway width for the graph ribbon, mirroring the generator's preference order."""
    from roads import standards as S
    w = edge_attrs.get("width", {})
    if isinstance(w, dict) and w.get("v") and w.get("src") in ("osm", "bdot10k"):
        return float(w["v"])
    if bdot.get("width_m"):
        return float(bdot["width_m"])
    cls = S.OSM_TO_CLASS.get(highway, "D")
    lw = S.LANE_WIDTH.get(cls, (2.5, 2.25))[0]
    n = max(1, int(lanes or 1))
    return n * lw if n > 1 else S.SINGLE_LANE_DEFAULT


def _local(coords, origin) -> list[list[float]]:
    return [[float(x) - origin[0], float(y) - origin[1]] for x, y in coords]


def load_world(region_id: str) -> World:
    """Build the World bundle from the committed, read-only files of Data/Regions/<region_id>/."""
    import yaml

    import regions
    reg = regions.get(region_id)
    d = REPO_ROOT / "Data" / "Regions" / region_id
    gen = d / "generated"
    ox, oy = reg.origin

    w = World(region_id=region_id, origin=(ox, oy))

    graph = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    for e in graph["edges"]:
        a = e["attrs"]
        w.edges.append({
            "id": e["id"], "osm_way": e.get("osm_way"),
            "coords": _local(e["geometry"], (ox, oy)),
            "width_m": _edge_width_m(a, e.get("bdot10k", {}), a["highway"]["v"], a.get("lanes", {}).get("v")),
            "highway": a["highway"]["v"], "lanes": a.get("lanes", {}).get("v"),
            "bridge": "bridge" in a or "tunnel" in a, "name": a.get("name", {}).get("v"),
        })

    bld = json.loads((d / "buildings.geojson").read_text(encoding="utf-8"))
    for f in bld["features"]:
        p = f["properties"]
        polys = []
        g = f["geometry"]
        rings = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in rings:
            polys.append(Polygon(_local(poly[0], (ox, oy)),
                                 [_local(r, (ox, oy)) for r in poly[1:]] if len(poly) > 1 else None))
        mp = shapely.MultiPolygon([p for p in polys]) if len(polys) > 1 else polys[0]
        w.buildings.append({"id": p.get("id") or f.get("id"), "poly": mp,
                            "height_m": p.get("height_m"), "storeys": p.get("storeys"),
                            "height_source": p.get("height_source"), "ground_z": p.get("ground_z_evrf2007"),
                            "is_roof_only": bool(p.get("is_roof_only")), "name": p.get("name")})

    ctx = json.loads((gen / "osm_context.json").read_text(encoding="utf-8"))
    for p in ctx["points"]:
        x, y = p["x"], p["y"]
        w.points.append({"id": f"osm:node/{p['osm_node']}", "kind": (p.get("kind") or "").split("=")[-1] or "node",
                         "e": x - ox, "n": y - oy, "tags": p})
    for fw in ctx["footways"]:
        w.lines.append({"id": f"osm:way/{fw.get('osm_way')}:part{fw.get('part', 0)}", "source_id": f"osm:way/{fw.get('osm_way')}",
                        "kind": "footway" if fw.get("highway") in ("footway", "path", "cycleway") else "sidewalk",
                        "line": LineString(_local(fw["geometry"], (ox, oy)))})

    src = json.loads((gen / "streetscape_sources.json").read_text(encoding="utf-8"))
    for n in src["osm"]["nodes"]:
        x, y = n["geometry"]["coordinates"]
        t = n.get("tags", {})
        kind = t.get("highway") or t.get("power") or t.get("natural") or "node"
        w.points.append({"id": f"osm:node/{n['osm_node']}", "kind": str(kind), "e": x - ox, "n": y - oy, "tags": t})
    barrier_kind = {"fence": "fence", "wall": "wall", "retaining_wall": "retaining_wall", "yes": "fence",
                    "bollard": "fence", "guard_rail": "barrier", "city_wall": "wall"}
    for wy in src["osm"]["ways"]:
        t = wy.get("tags", {})
        b = t.get("barrier")
        if b in barrier_kind:
            w.lines.append({"id": f"osm:way/{wy.get('osm_way')}", "source_id": f"osm:way/{wy.get('osm_way')}",
                            "kind": barrier_kind[b], "line": LineString(_local(wy["geometry"]["coordinates"], (ox, oy)))})
    bd_map = {  # BDOT10k layer -> validator line/point kind
        "OT_OIKM_L": ("line", "noise_barrier"), "OT_BUUO_L": ("line", "retaining_wall"),
        "OT_OIPR_L": ("line", "tree_row"), "OT_SKRP_L": ("line", "sidewalk"),
        "OT_BUWT_P": ("point", "power_pole"), "OT_OIPR_P": ("point", "tree"), "OT_OIKM_P": ("point", "bus_stop"),
        "OT_SULN_L": ("line", "power_line"),
    }
    for layer, (shape, kind) in bd_map.items():
        for obj in src["bdot10k"].get(layer, []):
            g = obj["geometry"]
            if shape == "line":
                w.lines.append({"id": obj["id"], "source_id": obj["id"].split(":")[0],
                                "kind": kind, "line": LineString(_local(g["coordinates"], (ox, oy)))})
            else:
                x, y = g["coordinates"]
                w.points.append({"id": obj["id"], "kind": kind, "e": x - ox, "n": y - oy, "props": obj.get("props", {})})

    canopy = json.loads((d / "plot_canopy.json").read_text(encoding="utf-8"))
    for i, c in enumerate(canopy.get("crowns", [])):
        w.trees.append({"id": f"canopy:{i}", "e": float(c[0]), "n": float(c[1]), "r": float(c[2]),
                        "conifer": bool(c[3])})

    sqa = json.loads((gen / "streetscape_qa.json").read_text(encoding="utf-8"))
    fum = sqa.get("furniture", {})
    for s in fum.get("route_signs", []):
        w.signs.append({"id": s.get("src", "sign"), "code": s.get("code"), "e": float(s["e"]), "n": float(s["n"]),
                        "faces_route_driver": s.get("faces_route_driver"), "offset_m": s.get("offset_m"),
                        "src": s.get("src")})
    for row_id, row in (fum.get("lamp_rows") or {}).items():
        for it in row.get("items", []):
            if it.get("skipped"):   # integration r6: not built (e.g. 'carriageway', ADR 0146 column 16) - was a false positive
                continue
            at = it["at"]
            w.lamps.append({"id": f"{row_id}:{it.get('k', len(w.lamps))}", "e": float(at[0]), "n": float(at[1]),
                            "z": it.get("z"), "p": it.get("p"), "row": row_id})

    route = json.loads((d / "route_start.json").read_text(encoding="utf-8"))
    w.route = [[float(p[0]), float(p[1])] for p in route["points_en"]]

    w.chains_qa = json.loads((gen / "roads_qa.json").read_text(encoding="utf-8")).get("chains", [])
    w.terrain_walls = json.loads((gen / "terrain_walls_qa.json").read_text(encoding="utf-8"))
    w.consistency_qa = json.loads((gen / "road_consistency_qa.json").read_text(encoding="utf-8"))
    w.manifest = json.loads((gen / "world_manifest.json").read_text(encoding="utf-8"))
    ov = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))
    w.overrides = ov.get("overrides", []) if isinstance(ov, dict) else []
    return w


def carriageway_polygons(w: World) -> list[tuple[dict, Polygon]]:
    """(edge, ribbon polygon) per graph edge; ribbons are the drivable carriageway (width/2 each side)."""
    out = []
    for e in w.edges:
        if len(e["coords"]) < 2:
            continue
        line = LineString(e["coords"])
        out.append((e, line.buffer(max(e["width_m"], 0.5) / 2.0, cap_style=2)))  # 2 = flat caps
    return out


def bridge_polygons(w: World) -> list[Polygon]:
    return [p for e, p in carriageway_polygons(w) if e.get("bridge")]


def finalize(w: World, findings: list[Finding]) -> list[Finding]:
    """Add WGS84 lat/lon, chunk tile, route distance; sort errors first, then on-route, then category/E/N."""
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    chunks = [(c["id"], Polygon([(c["bounds_local_m"]["e_min"], c["bounds_local_m"]["n_min"]),
                                 (c["bounds_local_m"]["e_max"], c["bounds_local_m"]["n_min"]),
                                 (c["bounds_local_m"]["e_max"], c["bounds_local_m"]["n_max"]),
                                 (c["bounds_local_m"]["e_min"], c["bounds_local_m"]["n_max"])]))
              for c in w.manifest.get("chunks", [])]
    route_line = LineString(w.route) if len(w.route) >= 2 else None
    for f in findings:
        ax, ay = w.to_abs(f.e, f.n)
        f.lon, f.lat = tr.transform(ax, ay)
        f.chunk = next((cid for cid, poly in chunks if poly.covers(Point(f.e, f.n))), None)
        if route_line is not None:
            f.dist_route_m = round(float(route_line.distance(Point(f.e, f.n))), 1)
            f.on_route = f.dist_route_m <= ROUTE_BAND_M
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 3), not f.on_route,
                                 f.dist_route_m if f.dist_route_m is not None else 1e9, f.category, f.e, f.n))
    return findings


def summarize(findings: list[Finding]) -> dict:
    by_cat, by_sev, on_route = {}, {}, {}
    for f in findings:
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
        by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        if f.on_route:
            on_route[f.category] = on_route.get(f.category, 0) + 1
    return {"count": len(findings), "by_category": dict(sorted(by_cat.items())),
            "by_severity": dict(sorted(by_sev.items())), "on_route_by_category": dict(sorted(on_route.items()))}


def route_ranking(findings: list[Finding], band_m: float = ROUTE_BAND_M, top: int = 50) -> list[dict]:
    """Extension (a): findings visible from the cab within +-band_m of the G3 route, ranked by importance."""
    sel = [f for f in findings if f.dist_route_m is not None and f.dist_route_m <= band_m]
    sel.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 3), f.dist_route_m, f.category))
    return [f.as_dict() for f in sel[:top]]
