"""Far-field backdrop generator beyond the 2x2 km region tile (ADR 0085).

Extracts real open GIS data in a ~1-4.5 km ring outside the region bbox:
  - BDOT10k (powiat 2061): OT_PTLZ_A (forests), OT_BUBD_A (buildings), OT_BUWT_P (chimneys, HV pylons, towers),
    OT_SULN_L (high-voltage overhead lines)
  - GUGiK LoD1 2024 (2061_lod1_2061.zip): measuredHeight per buildingId
  - OpenStreetMap (podlaskie-261108.osm.pbf): forests, landuse, buildings (incl. powiat 2002 north of the city limit),
    chimneys, power lines and towers

Builds 4 sector nodes (`far_north`, `far_east`, `far_south`, `far_west`), each with at most 2 primitives:
  - Submesh 0 (`far_field_buildings`, Kamion/World Surface + _FAR_FACADE): vertex-coloured (COLOR_0.rgb = linear
    albedo, COLOR_0.a = window mode: 1.0 block/office grid, 0.75 ribbon glazing, 0.0 windowless) and UV1 window
    bays/storeys for residential blocks, offices, industrial halls, pitched-roof houses, tapered red/white-banded
    chimneys, HV lattice pylons, and dark under-canopy forest mounds.
    Industrial cladding (ADR 0121 r5) reserves alpha 0.25 for opaque panels and 0.65 for panels with an upper ribbon;
    these WORKING_VALUE appearance markers use the existing UV1 and do not change measured height or footprint.
  - Submesh 1 (`forest_edge_mixed`, Kamion/Vegetation _HLOD_EDGE): alpha-tested tree-crown silhouette curtains along
    stand edges and stepped interior forest ridges.

Radial perspective foreshortening maps true distance d outside the 2048x2048 m border into d_eff <= 650 m with
proportional vertical/horizontal scaling so the entire 1-4 km ring sits inside Low tier's cameraFarClip (900 m)
and receives natural KamionFogTau aerial perspective.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box, shape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roads import pipeline                # noqa: E402
from terrain_mesh.gltf import GLB, GLTF_AXES  # noqa: E402

from streetscape import forest_hlod as FH  # noqa: E402
from streetscape import materials as SM    # noqa: E402

REPO = pipeline.REPO
RING_MAX_M = 4200.0
APRON_EASE_M = 600.0
FORESHORTEN_FREE_M = 140.0
FORESHORTEN_SPAN_M = 520.0
FORESHORTEN_TAU_M = 950.0

SECTORS = ("far_north", "far_east", "far_south", "far_west")
# ADR 0141 skyline node: the tall ring objects (and far stand-ins of landmark stacks that the region itself draws) live
# in one extra mesh whose vertices carry a flag in TEXCOORD_1.x. Kamion/World Surface (_FAR_FACADE) keeps flagged
# vertices just in front of the camera far plane instead of clipping them, so the Low tier (far clip 900 m) still shows
# the EC chimneys and tower blocks from the middle of the tile. No new material, texture, keyword or vertex channel.
# Flag encoding: ordinary far-field TEXCOORD_1.x is >= 0 (window bay index); a flagged vertex stores -(x + FLAG).
# Unity packs TEXCOORD_1 as float16, so the offset stays small where the window grid needs its precision.
SKYLINE = "far_skyline"
SKYLINE_FLAG_CLAMP = 16.0      # visible at any distance (objects that exist only in the far-field ring)
SKYLINE_FLAG_BEYOND = 4096.0   # visible only beyond the far plane (stand-in for an object the region draws itself)
SKYLINE_MIN_BUILDING_H_M = 24.0   # WORKING_VALUE: >= 8 storeys reads above the tree line from >= 900 m (1.5 deg)
SKYLINE_MIN_CHIMNEY_H_M = 40.0    # WORKING_VALUE
SKYLINE_PROXY_MERGE_M = 25.0      # a ring chimney this close to a region landmark stack is the same object
GIS_CACHE_SCHEMA = "far-field-gis-cache/11"

# Linear RGB albedos calibrated to docs/06 §3 and streetscape/materials.py
PALETTE_BLOCK = [
    (0.52, 0.46, 0.34),  # plaster_cream
    (0.54, 0.46, 0.26),  # plaster_yellow
    (0.52, 0.38, 0.29),  # plaster_peach
    (0.36, 0.42, 0.33),  # plaster_sage
    (0.48, 0.47, 0.44),  # plaster_light
    (0.34, 0.35, 0.35),  # plaster_grey
    (0.34, 0.40, 0.46),  # plaster_pastel_blue
    (0.28, 0.27, 0.25),  # panel_concrete
]
PALETTE_BLOCK_GABLE = [
    (0.40, 0.20, 0.13),  # terracotta accent
    (0.48, 0.35, 0.16),  # ochre accent
    (0.25, 0.32, 0.23),  # green accent
    (0.22, 0.23, 0.24),  # grey accent
]
PALETTE_HALL = [
    (0.38, 0.39, 0.40),  # hall_wall_silver
    (0.25, 0.26, 0.27),  # hall_wall_grey
    (0.50, 0.50, 0.48),  # hall_wall_white
    (0.44, 0.41, 0.35),  # hall_wall_ivory
    (0.11, 0.115, 0.12), # hall_wall_graphite
]
PALETTE_HALL_ACCENT = [
    (0.06, 0.12, 0.21),  # blue fascia
    (0.24, 0.05, 0.04),  # red fascia
    (0.05, 0.14, 0.09),  # green fascia
    (0.09, 0.095, 0.10), # graphite fascia
    (0.44, 0.24, 0.04),  # amber/orange fascia
]
PALETTE_OFFICE = [
    (0.48, 0.47, 0.44),  # plaster_light
    (0.35, 0.36, 0.36),  # plaster_grey
    (0.44, 0.39, 0.31),  # plaster_beige
    (0.54, 0.54, 0.52),  # plaster_white
    (0.23, 0.095, 0.065),# brick_red
]
PALETTE_HOUSE = [
    (0.50, 0.48, 0.44),
    (0.46, 0.41, 0.33),
    (0.52, 0.46, 0.35),
    (0.38, 0.39, 0.38),
]
PALETTE_ROOF_PITCHED = [
    (0.24, 0.085, 0.055), # red clay / metal tile
    (0.14, 0.095, 0.068), # dark brown tile
    (0.10, 0.105, 0.11),  # graphite sheet
]
COL_PLINTH = (0.17, 0.165, 0.155)
COL_ROOF_FLAT = (0.14, 0.14, 0.145)
COL_PARAPET = (0.20, 0.205, 0.21)
COL_CHIMNEY_CONCRETE = (0.37, 0.36, 0.34)
COL_CHIMNEY_BRICK = (0.23, 0.09, 0.06)
COL_CHIMNEY_RED = (0.38, 0.045, 0.035)
COL_CHIMNEY_WHITE = (0.62, 0.62, 0.60)
COL_PYLON_STEEL = (0.27, 0.285, 0.30)


def _sha256(path: Path) -> str:
    if path.suffix.lower() in (".json", ".geojson", ".yaml", ".yml"):
        # ADR 0173: git-tracked text inputs may be checked out with CRLF (worktrees) or LF (main); hash LF content
        return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _hfloat(key: str, salt: str = "") -> float:
    return int(hashlib.sha1((key + ":" + salt).encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF


def _hpick(key: str, seq: list, salt: str = ""):
    idx = int(hashlib.sha1((key + ":" + salt).encode("utf-8")).hexdigest()[:8], 16) % len(seq)
    return seq[idx]


def outside_dist(e: float, n: float, half: float = 1024.0) -> tuple[float, float, float, float, float]:
    """Return (eb, nb, de, dn, d) where (eb, nb) is the nearest point on [-half, +half]^2 and d is distance outside."""
    eb = min(max(float(e), -half), half)
    nb = min(max(float(n), -half), half)
    de = float(e) - eb
    dn = float(n) - nb
    d = math.hypot(de, dn)
    return eb, nb, de, dn, d


def foreshorten_dist(d: float) -> float:
    """Radial perspective foreshortening of distance d outside the region border."""
    if d <= FORESHORTEN_FREE_M:
        return float(d)
    return FORESHORTEN_FREE_M + FORESHORTEN_SPAN_M * (1.0 - math.exp(-(d - FORESHORTEN_FREE_M) / FORESHORTEN_TAU_M))


def foreshorten_scales(d: float) -> tuple[float, float]:
    """Return (s_xy, s_h) horizontal footprint scale and vertical height scale at raw border distance d."""
    if d <= FORESHORTEN_FREE_M:
        return 1.0, 1.0
    deff = foreshorten_dist(d)
    s_xy = min(max((deff + 140.0) / (d + 140.0), 0.32), 1.0)
    s_h = ((deff + 160.0) / (d + 160.0)) ** 0.62
    return s_xy, s_h


def foreshorten_point(e: float, n: float, half: float = 1024.0) -> tuple[float, float, float, float]:
    """Map raw local (e, n) outside [-half, +half]^2 to foreshortened (e_eff, n_eff, d_raw, d_eff)."""
    eb, nb, de, dn, d = outside_dist(e, n, half)
    if d < 1e-6:
        return float(e), float(n), 0.0, 0.0
    deff = foreshorten_dist(d)
    scale = deff / d
    return eb + de * scale, nb + dn * scale, d, deff


def sector_of(e: float, n: float, half: float = 1024.0) -> str:
    """Assign an outside point (e, n) to one of the 4 disjoint sectors aligned to the 4 border exit frustums."""
    if n > half and e >= -half - 320.0:
        return "far_north"
    if e > half or (n <= half and n >= -half and e >= 0.0):
        return "far_east"
    if n < -half and e <= half:
        return "far_south"
    return "far_west"


class BorderElevation:
    """Synchronized apron ground elevation model shared between Python (far_field.py) and Unity (WorldEdgeBuilder)."""

    def __init__(self, half: float, south: list[float], east: list[float], north: list[float], west: list[float]):
        self.half = float(half)
        self.south = np.asarray(south, dtype=np.float64)  # E from -half to +half at N = -half
        self.east = np.asarray(east, dtype=np.float64)    # N from -half to +half at E = +half
        self.north = np.asarray(north, dtype=np.float64)  # E from +half to -half at N = +half
        self.west = np.asarray(west, dtype=np.float64)    # N from +half to -half at E = -half
        n_seg = len(self.south) - 1
        ring = np.concatenate([self.south[:-1], self.east[:-1], self.north[:-1], self.west[:-1]])
        self.mean = float(np.mean(ring))
        # Circular moving average (±6 samples = ±96 m) so road ditches smooth out while local hills/valleys stay faithful
        w = min(6, max(1, len(ring) // 16))
        kernel = np.ones(2 * w + 1, dtype=np.float64) / (2 * w + 1)
        padded = np.concatenate([ring[-w:], ring, ring[:w]])
        sm = np.convolve(padded, kernel, mode="valid")
        self.south_sm = np.append(sm[0:n_seg], sm[n_seg % len(sm)])
        self.east_sm = np.append(sm[n_seg:2 * n_seg], sm[(2 * n_seg) % len(sm)])
        self.north_sm = np.append(sm[2 * n_seg:3 * n_seg], sm[(3 * n_seg) % len(sm)])
        self.west_sm = np.append(sm[3 * n_seg:4 * n_seg], sm[0])

    @classmethod
    def from_region(cls, region_id: str, half: float = 1024.0, step_m: float = 16.0) -> "BorderElevation":
        derived = REPO / "Data" / "raw" / "derived" / region_id
        npy = derived / "world" / "terrain_conformed.npy"
        if npy.exists():
            zc = np.load(npy)
        else:
            r16 = derived / "heightmap_2049.r16"
            tm = json.loads((pipeline.REGIONS / region_id / "terrain.json").read_text(encoding="utf-8"))
            raw = np.fromfile(r16, dtype="<u2").reshape(tm["samples"], tm["samples"])
            zc = tm["z_min_m"] + (raw / 65535.0) * (tm["z_max_m"] - tm["z_min_m"])

        h_rows, w_cols = zc.shape

        def sample_inside(e: float, n: float) -> float:
            # 0.75 m inside the border, matching WorldEdgeBuilder.BuildApron
            ec = min(max(e, -half + 0.75), half - 0.75)
            nc = min(max(n, -half + 0.75), half - 0.75)
            col = min(max((ec + half) / (2 * half) * (w_cols - 1), 0.0), w_cols - 1.0)
            row = min(max((half - nc) / (2 * half) * (h_rows - 1), 0.0), h_rows - 1.0)
            c0, r0 = int(math.floor(col)), int(math.floor(row))
            c1, r1 = min(c0 + 1, w_cols - 1), min(r0 + 1, h_rows - 1)
            fc, fr = col - c0, row - r0
            z00, z10 = float(zc[r0, c0]), float(zc[r0, c1])
            z01, z11 = float(zc[r1, c0]), float(zc[r1, c1])
            return (1 - fr) * ((1 - fc) * z00 + fc * z10) + fr * ((1 - fc) * z01 + fc * z11)

        n_steps = int(round(2 * half / step_m))
        ts = [i / n_steps for i in range(n_steps + 1)]
        south = [round(sample_inside(-half + 2 * half * t, -half), 3) for t in ts]
        east = [round(sample_inside(half, -half + 2 * half * t), 3) for t in ts]
        north = [round(sample_inside(half - 2 * half * t, half), 3) for t in ts]
        west = [round(sample_inside(-half, half - 2 * half * t), 3) for t in ts]
        return cls(half, south, east, north, west)

    def border_z_and_smooth(self, eb: float, nb: float) -> tuple[float, float]:
        h = self.half
        n_seg = len(self.south) - 1

        def interp(arr: np.ndarray, t: float) -> float:
            x = min(max(t, 0.0), 1.0) * n_seg
            i = min(int(math.floor(x)), n_seg - 1)
            f = x - i
            return float(arr[i] * (1.0 - f) + arr[i + 1] * f)

        ds = abs(nb - (-h))
        de = abs(eb - h)
        dn = abs(nb - h)
        dw = abs(eb - (-h))
        m = min(ds, de, dn, dw)
        if m == ds:
            t = (eb + h) / (2 * h)
            return interp(self.south, t), interp(self.south_sm, t)
        if m == de:
            t = (nb + h) / (2 * h)
            return interp(self.east, t), interp(self.east_sm, t)
        if m == dn:
            t = (h - eb) / (2 * h)
            return interp(self.north, t), interp(self.north_sm, t)
        t = (h - nb) / (2 * h)
        return interp(self.west, t), interp(self.west_sm, t)

    def border_z(self, eb: float, nb: float) -> float:
        return self.border_z_and_smooth(eb, nb)[0]

    def z_at_eff(self, e_eff: float, n_eff: float) -> float:
        """Apron ground elevation at foreshortened coordinates (e_eff, n_eff)."""
        eb, nb, _, _, d_eff = outside_dist(e_eff, n_eff, self.half)
        z0, z_sm = self.border_z_and_smooth(eb, nb)
        t1 = min(max(d_eff / 220.0, 0.0), 1.0)
        s1 = t1 * t1 * (3.0 - 2.0 * t1)
        t2 = min(max((d_eff - 220.0) / 1400.0, 0.0), 1.0)
        s2 = t2 * t2 * (3.0 - 2.0 * t2)
        z_near = z0 + (z_sm - 0.15 - z0) * s1
        z_far = z_sm - 0.25 + 0.08 * (self.mean - z_sm)
        return float(z_near + (z_far - z_near) * s2)


# ------------------------------------------------------------------------------------------- GIS extraction
def _parse_poslist(text: str, ox: float, oy: float) -> np.ndarray:
    vals = [float(x) for x in text.split()]
    # GML in EPSG:2180 stores (Northing Y, Easting X) pairs!
    pts = np.array([[vals[i + 1] - ox, vals[i] - oy] for i in range(0, len(vals) - 1, 2)], dtype=np.float64)
    return pts


def _extract_lod1_heights(zip_path: Path, audit: dict | None = None) -> dict[str, float]:
    """Read building-scoped heights from every CityGML member without loading the ZIP in RAM.

    GUGiK stores buildingId as a generic stringAttribute. Older exports may use a
    buildingId element. Prefixes and child order are irrelevant; missing values
    must never borrow the following building's height. Conflicting duplicate IDs
    are excluded rather than silently choosing a height from ZIP ordering.
    """
    stats = {"members": 0, "buildings": 0, "invalid_or_missing": 0,
             "duplicate_records": 0, "conflicting_ids": 0, "usable_ids": 0}
    heights: dict[str, float] = {}
    conflicts: set[str] = set()
    if not zip_path.exists():
        if audit is not None:
            audit.update(stats)
        return heights
    local = lambda tag: tag.rsplit("}", 1)[-1]
    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            if not name.lower().endswith((".gml", ".xml")):
                continue
            stats["members"] += 1
            with zf.open(name) as stream:
                for _, element in ET.iterparse(stream, events=("end",)):
                    if local(element.tag) != "Building":
                        continue
                    stats["buildings"] += 1
                    bid, height = "", None
                    for child in element:
                        tag = local(child.tag)
                        if tag == "buildingId":
                            bid = (child.text or "").strip()
                        elif tag == "stringAttribute" and child.get("name") == "buildingId":
                            bid = next(((v.text or "").strip() for v in child if local(v.tag) == "value"), "")
                        elif tag == "measuredHeight" and child.get("uom", "m") in ("m", "#m", "meter", "metre"):
                            try:
                                height = float(child.text or "")
                            except ValueError:
                                pass
                    if not bid or height is None or not math.isfinite(height) or height <= 0:
                        stats["invalid_or_missing"] += 1
                    elif bid not in conflicts:
                        if bid in heights:
                            stats["duplicate_records"] += 1
                            if heights[bid] != height:
                                conflicts.add(bid)
                                del heights[bid]
                        else:
                            heights[bid] = height
                    element.clear()
    stats["conflicting_ids"] = len(conflicts)
    stats["usable_ids"] = len(heights)
    if audit is not None:
        audit.update(stats)
    return heights


def _road_exit_corridors(half: float = 1024.0) -> shapely.Geometry:
    """Clearance corridors along the 4 main border road exits so forest polygons never block road stubs."""
    stubs = [
        # North exit: al. Tysiąclecia Państwa Polskiego N (E = -856.6, N = +1024, dir = (-0.21, +0.98))
        LineString([(-856.6, half - 20.0), (-876.0, half + 88.0)]).buffer(35.0),
        # East exit: ul. Gen. Władysława Andersa E (E = +1024, N = -980.1, dir = (+0.88, -0.48))
        LineString([(half - 20.0, -980.0), (half + 420.0, -1195.0)]).buffer(42.0),
        # South exit: al. Tysiąclecia Państwa Polskiego S (E = -237.6, N = -1024, dir = (+0.46, -0.89))
        LineString([(-237.6, -half + 20.0), (-40.0, -half - 400.0)]).buffer(42.0),
        # West exit: ul. Gen. Stanisława Maczka W (E = -1024, N = +44.1, dir = (-1.00, -0.09))
        LineString([(-half + 20.0, 44.1), (-half - 620.0, -12.0)]).buffer(36.0),
    ]
    return shapely.union_all(stubs)


def region_building_exclusion(region_id: str, ox: float, oy: float, half: float):
    """Include full region building outlines: they can extend beyond the tile itself."""
    path = REPO / "Data" / "Regions" / region_id / "buildings.geojson"
    parts = [box(-half, -half, half, half)]
    if path.exists():
        features = json.loads(path.read_text(encoding="utf-8"))["features"]
        parts.extend(shapely.affinity.translate(shape(f["geometry"]), xoff=-ox, yoff=-oy)
                     for f in features if not f.get("properties", {}).get("is_roof_only"))
    exclusion = shapely.union_all(parts)
    shapely.prepare(exclusion)
    return exclusion


def building_outside_region(footprint, half: float, exclusion=None) -> bool:
    """Region buildings own the whole boundary-crossing footprint, including contact.

    Check the source geometry before discarding MultiPolygon parts, then the rounded
    LoD rectangle as well: either approximation can otherwise cover a region building.
    """
    exclusion = exclusion if exclusion is not None else box(-half, -half, half, half)
    return not footprint.is_empty and not exclusion.intersects(footprint)


def building_rectangle_outside_region(rect, half: float, exclusion=None) -> bool:
    """The emitted, distance-compressed rectangle must also clear region geometry."""
    points = np.asarray(rect, dtype=np.float64)
    if len(points) < 4 or not building_outside_region(Polygon(points), half, exclusion):
        return False
    cx, cy = points.mean(axis=0)
    ce, cn, distance, _ = foreshorten_point(cx, cy, half)
    scale, _ = foreshorten_scales(distance)
    mapped = (points - [cx, cy]) * scale + [ce, cn]
    return building_outside_region(Polygon(mapped), half, exclusion)


def extract_ring_gis(region_id: str, ox: float, oy: float, half: float = 1024.0) -> dict:
    """Extract and cache real ring features from BDOT10k (gpkg), GUGiK LoD1 2024, and OSM PBF."""
    import pyogrio

    bdot_dir = REPO / "Data" / "raw" / "gugik" / "bdot10k-2061" / "gpkg"
    lod1_zip = REPO / "Data" / "raw" / "gugik" / "lod1-2024-2061" / "2061_lod1_2024.zip"
    osm_pbf = REPO / "Data" / "raw" / "osm" / "podlaskie-261108.osm.pbf"

    bdot_files = {
        "OT_PTLZ_A": bdot_dir / "PL.PZGiK.335.BDOT10k.2061__OT_PTLZ_A.gpkg",
        "OT_BUBD_A": bdot_dir / "PL.PZGiK.335.BDOT10k.2061__OT_BUBD_A.gpkg",
        "OT_BUWT_P": bdot_dir / "PL.PZGiK.335.BDOT10k.2061__OT_BUWT_P.gpkg",
        "OT_SULN_L": bdot_dir / "PL.PZGiK.335.BDOT10k.2061__OT_SULN_L.gpkg",
    }
    sources_sha = {}
    for k, p in bdot_files.items():
        if p.exists():
            sources_sha[f"bdot10k/{p.name}"] = _sha256(p)
    if lod1_zip.exists():
        sources_sha[f"lod1/{lod1_zip.name}"] = _sha256(lod1_zip)
    if osm_pbf.exists():
        sources_sha[f"osm/{osm_pbf.name}"] = _sha256(osm_pbf)
    region_buildings = REPO / "Data" / "Regions" / region_id / "buildings.geojson"
    if region_buildings.exists():
        sources_sha["region/buildings.geojson"] = _sha256(region_buildings)

    cache_path = REPO / "Data" / "raw" / "derived" / region_id / "world" / "far_field_gis_cache.json"
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if (cached.get("sources_sha256") == sources_sha
                    and cached.get("schema") == GIS_CACHE_SCHEMA
                    and cached.get("origin_epsg2180") == [ox, oy]
                    and cached.get("half_m") == half
                    and cached.get("ring_max_m") == RING_MAX_M):
                return cached
        except Exception:
            pass

    t0 = time.time()
    inner_box = box(-half - 8.0, -half - 8.0, half + 8.0, half + 8.0)
    outer_box = box(-RING_MAX_M, -RING_MAX_M, RING_MAX_M, RING_MAX_M)
    ring_zone = outer_box.difference(inner_box)
    forest_ring_zone = ring_zone.difference(_road_exit_corridors(half))
    shapely.prepare(ring_zone)
    shapely.prepare(forest_ring_zone)
    bbox_2180 = (ox - RING_MAX_M, oy - RING_MAX_M, ox + RING_MAX_M, oy + RING_MAX_M)

    lod1_audit = {}
    lod1_h = _extract_lod1_heights(lod1_zip, lod1_audit)

    forests = []
    buildings = []
    building_exclusion = region_building_exclusion(region_id, ox, oy, half)
    boundary_exclusions = {"bdot_source": 0, "bdot_rectangle": 0,
                           "osm_source": 0, "osm_rectangle": 0}
    chimneys = []
    pylons = []
    power_lines = []

    # 1. BDOT10k OT_PTLZ_A (forests)
    if bdot_files["OT_PTLZ_A"].exists():
        df = pyogrio.read_dataframe(bdot_files["OT_PTLZ_A"], bbox=bbox_2180)
        for _, row in df.iterrows():
            geom = shapely.affinity.translate(row.geometry, xoff=-ox, yoff=-oy)
            geom = shapely.make_valid(geom)
            if not forest_ring_zone.intersects(geom):
                continue
            clipped = shapely.intersection(geom, forest_ring_zone)
            cat = str(row.get("KATEGORIA") or row.get("kategoriaLasu") or "").strip()
            mix = FH.MIX_OF_CATEGORY.get(cat, "mixed")
            for g in getattr(clipped, "geoms", [clipped]):
                if g.geom_type == "Polygon" and g.area >= 400.0:
                    gs = g.simplify(3.5, preserve_topology=True)
                    if gs.geom_type == "Polygon" and gs.area >= 300.0:
                        forests.append({"coords": np.round(np.asarray(gs.exterior.coords), 1).tolist(), "mix": mix, "src": "bdot10k"})

    # 2. BDOT10k OT_BUBD_A (buildings) + LoD1 2024 heights
    if bdot_files["OT_BUBD_A"].exists():
        df = pyogrio.read_dataframe(bdot_files["OT_BUBD_A"], bbox=bbox_2180)
        for _, row in df.iterrows():
            geom = shapely.affinity.translate(row.geometry, xoff=-ox, yoff=-oy)
            if not building_outside_region(geom, half, building_exclusion):
                boundary_exclusions["bdot_source"] += 1
                continue
            if geom.geom_type == "MultiPolygon":
                geom = max(geom.geoms, key=lambda g: g.area)
            if geom.geom_type != "Polygon" or geom.area < 45.0:
                continue
            c = geom.centroid
            cx, cy = float(c.x), float(c.y)
            if abs(cx) > RING_MAX_M or abs(cy) > RING_MAX_M or (abs(cx) < half + 4.0 and abs(cy) < half + 4.0):
                continue
            _, _, _, _, d = outside_dist(cx, cy, half)
            if d < 4.0:
                continue
            bid = str(row.get("LOKALNYID") or row.get("lokalnyId") or "").strip()
            func = str(row.get("FUNKCJAOGOLNABUDYNKU") or row.get("funkcjaOgolnaBudynku") or "").strip()
            pfunc = str(row.get("PRZEWAZAJACAFUNKCJABUDYNKU") or row.get("przewazajacaFunkcjaBudynku") or "").strip()
            st_raw = row.get("LICZBAKONDYGNACJI") if "LICZBAKONDYGNACJI" in row else row.get("liczbaKondygnacji")
            storeys = int(float(st_raw)) if st_raw is not None and not (isinstance(st_raw, float) and math.isnan(st_raw)) else None
            h_m = lod1_h.get(bid)
            height_source = "gugik-lod1-measuredHeight" if h_m and h_m > 2.0 else "WORKING_VALUE-bdot-storeys-typology"
            f_str = (pfunc + " " + func).lower()
            if "wielorodzinny" in f_str or "zbiorowego" in f_str or "hotel" in f_str or (storeys and storeys >= 4):
                typ = "block"
            elif any(k in f_str for k in ("przemysł", "magazyn", "produkc", "elektrociepł", "składow", "handlowo", "warsztat")):
                typ = "hall" if geom.area >= 220.0 else "office"
            elif "jednorodzinny" in f_str or "mieszkalny" in f_str:
                typ = "house" if (not storeys or storeys <= 3) and geom.area < 380.0 else "block"
            elif geom.area >= 450.0:
                typ = "hall"
            elif geom.area >= 160.0 or (storeys and storeys >= 2):
                typ = "office"
            else:
                typ = "house"

            if typ == "house" and (d > 480.0 or geom.area < 65.0):
                continue
            if typ == "office" and d > 1500.0 and geom.area < 260.0:
                continue
            if typ == "hall" and d > 2200.0 and geom.area < 550.0:
                continue
            if typ == "block" and d > 2600.0 and geom.area < 240.0 and (storeys or 0) < 5:
                continue

            if not h_m or h_m <= 2.0:
                if typ == "block":
                    st = storeys if storeys and storeys >= 3 else 5
                    h_m = st * 2.9 + 1.5
                elif typ == "hall":
                    h_m = 9.5 if geom.area > 1200 else 7.2
                elif typ == "office":
                    st = storeys if storeys and storeys >= 1 else 3
                    h_m = st * 3.5 + 1.0
                else:
                    st = storeys if storeys and storeys >= 1 else 2
                    h_m = st * 2.8 + 2.5

            rect = geom.minimum_rotated_rectangle
            if rect.geom_type != "Polygon" or rect.area < 30.0:
                continue
            rc = np.round(np.asarray(rect.exterior.coords)[:4], 1).tolist()
            if not building_rectangle_outside_region(rc, half, building_exclusion):
                boundary_exclusions["bdot_rectangle"] += 1
                continue
            buildings.append({
                "id": bid or f"bdot_{len(buildings)}",
                "typ": typ,
                "rect": rc,
                "area": round(float(geom.area), 1),
                "h": round(float(h_m), 2),
                "storeys": storeys,
                "func": pfunc or func,
                "src": "bdot10k+lod1" if height_source == "gugik-lod1-measuredHeight" else "bdot10k",
                "height_source": height_source,
            })

    # 3. BDOT10k OT_BUWT_P (chimneys, HV pylons, towers)
    if bdot_files["OT_BUWT_P"].exists():
        df = pyogrio.read_dataframe(bdot_files["OT_BUWT_P"], bbox=bbox_2180)
        for _, row in df.iterrows():
            c = row.geometry.centroid
            e, n = float(c.x - ox), float(c.y - oy)
            if abs(e) > RING_MAX_M or abs(n) > RING_MAX_M or (abs(e) < half + 4.0 and abs(n) < half + 4.0):
                continue
            bid = str(row.get("LOKALNYID") or row.get("lokalnyId") or "").strip()
            kind = str(row.get("RODZAJ") or row.get("rodzaj") or "").strip()
            h_raw = row.get("WYSOKOSC") if "WYSOKOSC" in row else row.get("wysokosc")
            h_m = float(h_raw) if h_raw is not None and not (isinstance(h_raw, float) and math.isnan(h_raw)) else None
            if kind == "komin":
                if (h_m or 45.0) < 16.0:
                    continue
                chimneys.append({"id": bid or f"ch_{len(chimneys)}", "e": round(e, 1), "n": round(n, 1),
                                 "h": round(float(h_m or 48.0), 1), "src": "bdot10k"})
            elif kind in ("słup energetyczny", "maszt lub wieża telekomunikacyjna", "maszt", "maszt oświetleniowy", "wieża telekomunikacyjna", "wieża ciśnień"):
                if kind in ("maszt oświetleniowy", "maszt") and (h_m or 0) < 22.0:
                    continue
                pylons.append({"id": bid or f"py_{len(pylons)}", "e": round(e, 1), "n": round(n, 1),
                               "h": round(float(h_m or 26.0), 1), "kind": kind, "src": "bdot10k"})

    # 4. BDOT10k OT_SULN_L (overhead power lines -> line directions & additional pylon spans)
    if bdot_files["OT_SULN_L"].exists():
        df = pyogrio.read_dataframe(bdot_files["OT_SULN_L"], bbox=bbox_2180)
        for _, row in df.iterrows():
            geom = shapely.affinity.translate(row.geometry, xoff=-ox, yoff=-oy)
            if not ring_zone.intersects(geom):
                continue
            clipped = shapely.intersection(geom, ring_zone)
            for g in getattr(clipped, "geoms", [clipped]):
                if g.geom_type == "LineString" and g.length >= 60.0:
                    power_lines.append(np.round(np.asarray(g.coords), 1).tolist())

    # 5. OpenStreetMap PBF supplement (critical for North sector outside city limits + additional buildings/forests/towers)
    if osm_pbf.exists():
        import osmium
        from pyproj import Transformer

        tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
        # Existing BDOT building/chimney/pylon spatial grid to avoid duplicates
        bdot_b_pts = np.array([[sum(p[0] for p in b["rect"]) / 4.0, sum(p[1] for p in b["rect"]) / 4.0] for b in buildings]) if buildings else np.zeros((0, 2))
        bdot_f_polys = [Polygon(f["coords"]) for f in forests]
        bdot_f_union = shapely.union_all(bdot_f_polys) if bdot_f_polys else Polygon()
        shapely.prepare(bdot_f_union)

        class RingHandler(osmium.SimpleHandler):
            def node(self, n):
                tags = n.tags
                if not tags:
                    return
                mm = tags.get("man_made")
                pw = tags.get("power")
                if mm != "chimney" and pw != "tower":
                    return
                if not (23.08 <= n.location.lon <= 23.30 and 53.10 <= n.location.lat <= 53.24):
                    return
                x, y = tr.transform(n.location.lon, n.location.lat)
                el, nl = x - ox, y - oy
                if abs(el) > RING_MAX_M or abs(nl) > RING_MAX_M or (abs(el) < half and abs(nl) < half):
                    return
                h_str = tags.get("height", "")
                try:
                    hm = float(h_str.replace("m", "").strip())
                except ValueError:
                    hm = 55.0 if mm == "chimney" else 26.0
                if mm == "chimney":
                    if not any(math.hypot(el - c["e"], nl - c["n"]) < 35.0 for c in chimneys):
                        chimneys.append({"id": f"osm_n{n.id}", "e": round(el, 1), "n": round(nl, 1), "h": round(hm, 1), "src": "osm"})
                elif pw == "tower":
                    if not any(math.hypot(el - p["e"], nl - p["n"]) < 25.0 for p in pylons):
                        pylons.append({"id": f"osm_n{n.id}", "e": round(el, 1), "n": round(nl, 1), "h": round(hm, 1), "kind": "power_tower", "src": "osm"})

            def way(self, w):
                tags = w.tags
                if not tags or tags.get("power") not in ("line", "minor_line"):
                    return
                try:
                    lonlat = [(nd.lon, nd.lat) for nd in w.nodes if nd.location.valid()]
                except Exception:
                    return
                if len(lonlat) < 2:
                    return
                lon0, lat0 = lonlat[0]
                if not (23.08 <= lon0 <= 23.30 and 53.10 <= lat0 <= 53.24):
                    return
                lons, lats = zip(*lonlat)
                xs, ys = tr.transform(lons, lats)
                pts = np.column_stack([np.asarray(xs) - ox, np.asarray(ys) - oy])
                ls = LineString(pts)
                if not ring_zone.intersects(ls):
                    return
                clipped = shapely.intersection(ls, ring_zone)
                for g in getattr(clipped, "geoms", [clipped]):
                    if g.geom_type == "LineString" and g.length >= 60.0:
                        power_lines.append(np.round(np.asarray(g.coords), 1).tolist())

            def area(self, a):
                tags = a.tags
                if not tags:
                    return
                lu = tags.get("landuse")
                nat = tags.get("natural")
                btag = tags.get("building")
                mm = tags.get("man_made")
                if not (lu in ("forest",) or nat in ("wood",) or btag or mm == "chimney"):
                    return
                try:
                    ring = next(iter(a.outer_rings()))
                    lonlat = [(nd.lon, nd.lat) for nd in ring]
                except Exception:
                    return
                if not lonlat:
                    return
                lon0, lat0 = lonlat[0]
                if not (23.08 <= lon0 <= 23.30 and 53.10 <= lat0 <= 53.24):
                    return
                lons, lats = zip(*lonlat)
                xs, ys = tr.transform(lons, lats)
                pts = np.column_stack([np.asarray(xs) - ox, np.asarray(ys) - oy])
                cx, cy = float(pts[:, 0].mean()), float(pts[:, 1].mean())
                if abs(cx) > RING_MAX_M or abs(cy) > RING_MAX_M:
                    return
                if mm == "chimney":
                    if abs(cx) >= half or abs(cy) >= half:
                        if not any(math.hypot(cx - c["e"], cy - c["n"]) < 35.0 for c in chimneys):
                            chimneys.append({"id": f"osm_a{a.id}", "e": round(cx, 1), "n": round(cy, 1), "h": 55.0, "src": "osm"})
                    return
                if lu == "forest" or nat == "wood":
                    poly = shapely.make_valid(Polygon(pts))
                    if not forest_ring_zone.intersects(poly):
                        return
                    clipped = shapely.intersection(poly, forest_ring_zone)
                    if not bdot_f_union.is_empty:
                        clipped = shapely.difference(clipped, bdot_f_union)
                    for g in getattr(clipped, "geoms", [clipped]):
                        if g.geom_type == "Polygon" and g.area >= 600.0:
                            gs = g.simplify(4.0, preserve_topology=True)
                            if gs.geom_type == "Polygon" and gs.area >= 400.0:
                                lt = tags.get("leaf_type", "")
                                mix = "conifer" if "needle" in lt else "broadleaf" if "broad" in lt else "mixed"
                                forests.append({"coords": np.round(np.asarray(gs.exterior.coords), 1).tolist(), "mix": mix, "src": "osm"})
                    return
                if btag:
                    if abs(cx) < half + 4.0 and abs(cy) < half + 4.0:
                        return
                    if len(bdot_b_pts) > 0:
                        dmin = float(np.min(np.hypot(bdot_b_pts[:, 0] - cx, bdot_b_pts[:, 1] - cy)))
                        if dmin < 10.0:
                            return
                    poly = shapely.make_valid(Polygon(pts))
                    if not building_outside_region(poly, half, building_exclusion):
                        boundary_exclusions["osm_source"] += 1
                        return
                    if poly.geom_type == "MultiPolygon":
                        poly = max(poly.geoms, key=lambda g: g.area)
                    if poly.geom_type != "Polygon" or poly.area < 55.0:
                        return
                    _, _, _, _, d = outside_dist(cx, cy, half)
                    if d < 4.0:
                        return
                    lv_s = tags.get("building:levels")
                    h_s = tags.get("height")
                    st = None
                    if lv_s:
                        try:
                            st = int(float(lv_s.split(";")[0].strip()))
                        except ValueError:
                            pass
                    hm = None
                    if h_s:
                        try:
                            hm = float(h_s.replace("m", "").strip())
                        except ValueError:
                            pass
                    if btag in ("apartments", "dormitory", "hotel") or (st and st >= 4):
                        typ = "block"
                    elif btag in ("industrial", "warehouse", "retail", "supermarket", "commercial", "manufacture") or poly.area >= 400.0:
                        typ = "hall" if poly.area >= 220.0 else "office"
                    elif btag in ("office", "public", "school", "hospital", "university", "civic") or poly.area >= 180.0:
                        typ = "office"
                    else:
                        typ = "house"
                    if typ == "house" and d > 650.0:
                        return
                    height_source = "osm-height-tag-UNVERIFIED" if hm and math.isfinite(hm) and hm > 2.0 else "WORKING_VALUE-osm-storeys-typology"
                    if height_source != "osm-height-tag-UNVERIFIED":
                        if typ == "block":
                            hm = (st or 5) * 2.9 + 1.5
                        elif typ == "hall":
                            hm = 9.0 if poly.area > 1000 else 7.0
                        elif typ == "office":
                            hm = (st or 3) * 3.5 + 1.0
                        else:
                            hm = (st or 2) * 2.8 + 2.5
                    rect = poly.minimum_rotated_rectangle
                    if rect.geom_type != "Polygon" or rect.area < 35.0:
                        return
                    rc = np.round(np.asarray(rect.exterior.coords)[:4], 1).tolist()
                    if not building_rectangle_outside_region(rc, half, building_exclusion):
                        boundary_exclusions["osm_rectangle"] += 1
                        return
                    buildings.append({
                        "id": f"osm_a{a.id}",
                        "typ": typ,
                        "rect": rc,
                        "area": round(float(poly.area), 1),
                        "h": round(float(hm), 2),
                        "storeys": st,
                        "func": btag,
                        "src": "osm",
                        "height_source": height_source,
                    })

        RingHandler().apply_file(str(osm_pbf), locations=True)

    data = {
        "schema": GIS_CACHE_SCHEMA,
        "region": region_id,
        "origin_epsg2180": [ox, oy],
        "half_m": half,
        "ring_max_m": RING_MAX_M,
        "sources_sha256": sources_sha,
        "forests": forests,
        "buildings": buildings,
        "lod1_height_audit": lod1_audit,
        "building_height_sources": {
            source: sum(b["height_source"] == source for b in buildings)
            for source in sorted({b["height_source"] for b in buildings})
        },
        "boundary_exclusions": boundary_exclusions,
        "chimneys": chimneys,
        "pylons": pylons,
        "power_lines": power_lines,
    }
    # ADR 0173: no wall-clock time in the cache (byte-identical derived world between two runs); time goes to stdout
    print(f"[far_field] GIS extraction {time.time() - t0:.1f} s")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8", newline="\n")
    return data


# ------------------------------------------------------------------------------------------- mesh accumulator
class SectorBuilder:
    """Accumulates Submesh 0 (far_field_buildings) and Submesh 1 (forest_edge_mixed) for one sector."""

    def __init__(self, name: str, uv1_flag: float = 0.0):
        self.name = name
        self.uv1_flag = float(uv1_flag)   # ADR 0141: TEXCOORD_1.x of submesh 0 becomes -(x + flag); 0 = ordinary geometry
        self.v0, self.n0, self.uv0, self.uv1_0, self.col0, self.t0 = [], [], [], [], [], []
        self.count0 = 0
        self.v1, self.n1, self.uv1, self.t1 = [], [], [], []
        self.count1 = 0

    def add_quad0(self, a, b, c, d, col_rgba, uv1=None, normal=None):
        """CCW quad a-b-c-d seen from outside."""
        va = np.asarray([a, b, c, d], dtype=np.float64)
        e1 = va[1] - va[0]
        e2 = va[3] - va[0]
        L = max(float(np.linalg.norm(e1)), 0.1)
        H = max(float(np.linalg.norm(e2)), 0.1)
        if normal is None:
            fn = np.cross(e1, e2)
            ln = float(np.linalg.norm(fn))
            normal = (fn / ln) if ln > 1e-9 else np.array([0.0, 0.0, 1.0])
        else:
            normal = np.asarray(normal, dtype=np.float64)
        uv = np.array([[0.0, 0.0], [L, 0.0], [L, H], [0.0, H]], dtype=np.float64)
        if uv1 is None:
            uv1_arr = np.full((4, 2), [0.0, -2.0], dtype=np.float64)
        else:
            uv1_arr = np.asarray(uv1, dtype=np.float64)
        if self.uv1_flag:
            uv1_arr = np.column_stack([-(np.maximum(uv1_arr[:, 0], 0.0) + self.uv1_flag), uv1_arr[:, 1]])
        c4 = np.tile(np.asarray(col_rgba, dtype=np.float64), (4, 1))
        n4 = np.tile(normal, (4, 1))
        base = self.count0
        self.v0.append(va)
        self.n0.append(n4)
        self.uv0.append(uv)
        self.uv1_0.append(uv1_arr)
        self.col0.append(c4)
        self.t0.append(np.array([[base, base + 1, base + 2], [base, base + 2, base + 3]], dtype=np.int64))
        self.count0 += 4

    def add_tri0(self, a, b, c, col_rgba, uv1=None, normal=None):
        va = np.asarray([a, b, c], dtype=np.float64)
        if normal is None:
            fn = np.cross(va[1] - va[0], va[2] - va[0])
            ln = float(np.linalg.norm(fn))
            normal = (fn / ln) if ln > 1e-9 else np.array([0.0, 0.0, 1.0])
        else:
            normal = np.asarray(normal, dtype=np.float64)
        uv = va[:, :2].copy()
        uv1_arr = np.full((3, 2), [0.0, -2.0], dtype=np.float64) if uv1 is None else np.asarray(uv1, dtype=np.float64)
        if self.uv1_flag:
            uv1_arr = np.column_stack([-(np.maximum(uv1_arr[:, 0], 0.0) + self.uv1_flag), uv1_arr[:, 1]])
        c3 = np.tile(np.asarray(col_rgba, dtype=np.float64), (3, 1))
        n3 = np.tile(normal, (3, 1))
        base = self.count0
        self.v0.append(va)
        self.n0.append(n3)
        self.uv0.append(uv)
        self.uv1_0.append(uv1_arr)
        self.col0.append(c3)
        self.t0.append(np.array([[base, base + 1, base + 2]], dtype=np.int64))
        self.count0 += 3

    def add_curtain1(self, pts_xy: np.ndarray, z_bot: np.ndarray, z_top: np.ndarray, face_sign: float = 1.0, u_scale: float = 48.0):
        """Add an alpha-tested forest_edge_mixed curtain strip along pts_xy."""
        k = len(pts_xy)
        if k < 2:
            return
        ds = np.hypot(*np.diff(pts_xy, axis=0).T)
        s = np.concatenate([[0.0], np.cumsum(ds)])
        u0 = ((pts_xy[0, 0] + pts_xy[0, 1]) % u_scale) / u_scale
        us = u0 + s / u_scale

        # Compute outward normal in XY + upward tilt 0.48
        tang = np.zeros((k, 2), dtype=np.float64)
        tang[:-1] += np.diff(pts_xy, axis=0)
        tang[1:] += np.diff(pts_xy, axis=0)
        nxy = np.column_stack([tang[:, 1], -tang[:, 0]]) * face_sign
        ln = np.maximum(np.hypot(nxy[:, 0], nxy[:, 1]), 1e-9)
        nxy /= ln[:, None]
        n3 = np.column_stack([nxy, np.full(k, 0.48)])
        n3 /= np.linalg.norm(n3, axis=1)[:, None]

        v_bot = np.column_stack([pts_xy[:, 0], pts_xy[:, 1], z_bot])
        v_top = np.column_stack([pts_xy[:, 0], pts_xy[:, 1], z_top])
        V = np.vstack([v_bot, v_top])
        N = np.vstack([n3, n3])
        uv_bot = np.column_stack([us, np.zeros(k)])
        uv_top = np.column_stack([us, np.ones(k)])
        UV = np.vstack([uv_bot, uv_top])

        base = self.count1
        tris = []
        for i in range(k - 1):
            b0, b1 = base + i, base + i + 1
            t0, t1 = base + k + i, base + k + i + 1
            if face_sign >= 0:
                tris.append([b0, b1, t1])
                tris.append([b0, t1, t0])
            else:
                tris.append([b0, t1, b1])
                tris.append([b0, t0, t1])
        self.v1.append(V)
        self.n1.append(N)
        self.uv1.append(UV)
        self.t1.append(np.asarray(tris, dtype=np.int64))
        self.count1 += 2 * k

    def sort_far_to_near(self):
        """ADR 0141: beyond the far plane the skyline shares (almost) one depth, so the index order decides what is
        in front. Order the faces by distance from the tile centre, farthest first (stable, deterministic)."""
        if self.count0 == 0:
            return
        order = sorted(range(len(self.v0)), key=lambda i: -float(np.hypot(*self.v0[i][:, :2].mean(axis=0))))
        base = 0
        tris = []
        for i in order:
            tris.append(self.t0[i] - int(self.t0[i].min()) + base)
            base += len(self.v0[i])
        for name in ("v0", "n0", "uv0", "uv1_0", "col0"):
            setattr(self, name, [getattr(self, name)[i] for i in order])
        self.t0 = tris

    def primitives(self) -> list[dict]:
        prims = []
        if self.count0 > 0:
            prims.append({
                "mat": "far_field_buildings",
                "V": np.vstack(self.v0),
                "N": np.vstack(self.n0),
                "UV": np.vstack(self.uv0),
                "UV1": np.vstack(self.uv1_0),
                "COL": np.vstack(self.col0),
                "T": np.vstack(self.t0),
            })
        if self.count1 > 0:
            prims.append({
                "mat": "forest_edge_mixed",
                "V": np.vstack(self.v1),
                "N": np.vstack(self.n1),
                "UV": np.vstack(self.uv1),
                "T": np.vstack(self.t1),
            })
        return prims


# ------------------------------------------------------------------------------------------- feature meshing
def _corridor_taper(e: np.ndarray, n: np.ndarray, half: float = 1024.0) -> np.ndarray:
    """Smoothly taper tree curtain height near the 4 road exit axes so stand edges step down naturally."""
    taper = np.ones_like(e, dtype=np.float64)
    # East exit road axis (E > 1024, N ~ -980 - 0.54*(E-1024))
    mask_e = e > half - 10.0
    if np.any(mask_e):
        lat_e = np.abs(n[mask_e] - (-980.0 - 0.54 * (e[mask_e] - half)))
        taper[mask_e] = np.minimum(taper[mask_e], np.clip((lat_e - 30.0) / 50.0, 0.38, 1.0))
    # West exit road axis (E = -1024..-1120, N ~ +44 + 0.09*(E+1024))
    mask_w = (e < -half + 10.0) & (e > -half - 95.0)
    if np.any(mask_w):
        lat_w = np.abs(n[mask_w] - (44.1 + 0.09 * (e[mask_w] + half)))
        taper[mask_w] = np.minimum(taper[mask_w], np.clip((lat_w - 26.0) / 42.0, 0.38, 1.0))
    # South exit road axis (N < -1024, E ~ -238 - 0.52*(N+1024))
    mask_s = n < -half + 10.0
    if np.any(mask_s):
        lat_s = np.abs(e[mask_s] - (-237.6 - 0.52 * (n[mask_s] + half)))
        taper[mask_s] = np.minimum(taper[mask_s], np.clip((lat_s - 30.0) / 50.0, 0.38, 1.0))
    # North exit road axis (N = 1024..1095, E ~ -857 - 0.21*(N-1024); beyond N=1095 full pine height closes the vista)
    mask_n = (n > half - 10.0) & (n < half + 72.0)
    if np.any(mask_n):
        lat_n = np.abs(e[mask_n] - (-856.6 - 0.21 * (n[mask_n] - half)))
        taper[mask_n] = np.minimum(taper[mask_n], np.clip((lat_n - 26.0) / 40.0, 0.38, 1.0))
    return taper


def _crown_height_wave(e: np.ndarray, n: np.ndarray, h_base: float, half: float = 1024.0) -> np.ndarray:
    """Natural non-repeating tree-crown height modulation along a stand edge with road-corridor taper."""
    w = (
        1.0
        + 0.16 * np.sin(0.085 * e + 0.065 * n)
        + 0.11 * np.cos(0.21 * e - 0.17 * n)
        + 0.07 * np.sin(0.43 * e + 0.31 * n)
    )
    return h_base * np.clip(w, 0.72, 1.28) * _corridor_taper(e, n, half)


def _add_forest_stand(sectors: dict[str, SectorBuilder], coords: list, mix: str, elev: BorderElevation, half: float, tier: str):
    pts_raw = np.asarray(coords, dtype=np.float64)
    if len(pts_raw) < 4:
        return
    poly_raw = shapely.make_valid(Polygon(pts_raw))
    if poly_raw.geom_type != "Polygon" or poly_raw.area < 350.0:
        return
    c_raw = np.asarray(poly_raw.centroid.coords[0])
    _, _, _, _, d_cen = outside_dist(c_raw[0], c_raw[1], half)
    if tier == "Low":
        if d_cen > 2300.0 and poly_raw.area < 18000.0:
            return
        if d_cen > 1100.0 and poly_raw.area < 4500.0:
            return
        if poly_raw.area < 1400.0 and d_cen > 350.0:
            return

    # Map polygon vertices through radial foreshortening
    mapped = [foreshorten_point(p[0], p[1], half) for p in pts_raw]
    pts_eff = np.array([[m[0], m[1]] for m in mapped], dtype=np.float64)
    poly_eff = shapely.make_valid(Polygon(pts_eff))
    if poly_eff.geom_type == "MultiPolygon":
        poly_eff = max(poly_eff.geoms, key=lambda g: g.area)
    if poly_eff.geom_type != "Polygon" or poly_eff.area < 60.0:
        return
    if tier == "Low":
        poly_eff = poly_eff.simplify(8.0, preserve_topology=True)
        if poly_eff.geom_type != "Polygon" or poly_eff.area < 60.0:
            return

    ce, cn = float(poly_eff.centroid.x), float(poly_eff.centroid.y)
    sec = sectors[sector_of(ce, cn, half)]
    _, s_h = foreshorten_scales(d_cen)
    h_base = (21.5 if mix == "conifer" else 19.5 if mix == "mixed" else 18.0) * s_h
    h_base = max(h_base, 8.5)

    seg_step = 9.0 if tier == "High" else 28.0
    ext = np.asarray(poly_eff.exterior.coords, dtype=np.float64)
    if not poly_eff.exterior.is_ccw:
        ext = ext[::-1]

    # 1. Outer stand-edge curtain: only keep front-facing edges (dot(n_seg, -rad) >= 0.44) outside the 10.5 m border
    #    band so radial corridor edges never appear at grazing angles as dark parallel walls (forest_hlod.py v3.1 r2).
    run = []

    def flush_run(r_pts):
        if len(r_pts) < 2:
            return
        P = np.asarray(r_pts, dtype=np.float64)
        ds = np.hypot(*np.diff(P, axis=0).T)
        s = np.concatenate([[0.0], np.cumsum(ds)])
        total_s = float(s[-1])
        if total_s < 8.0:
            return
        zg = np.array([elev.z_at_eff(p[0], p[1]) for p in P])
        ht = _crown_height_wave(P[:, 0], P[:, 1], h_base, half)
        # Taper ends of open runs so stand edges step down gently at margins instead of ending in a vertical wall
        if np.hypot(*(P[0] - P[-1])) > 2.0:
            end_taper = np.minimum(np.clip(s / 32.0, 0.30, 1.0), np.clip((total_s - s) / 32.0, 0.30, 1.0))
            ht = ht * end_taper
        sec.add_curtain1(P, zg - 0.5, zg + ht, face_sign=1.0)

    for a, b in zip(ext[:-1], ext[1:]):
        L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
        if L < 0.5:
            continue
        mx, my = 0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1])
        _, _, de, dn, dm = outside_dist(mx, my, half)
        # Outward normal of CCW polygon edge a->b is (dy/L, -dx/L); radial vector from border is (de/dm, dn/dm)
        nx, ny = (b[1] - a[1]) / L, -(b[0] - a[0]) / L
        facing_tile = -(nx * de + ny * dn) / max(dm, 1e-6)
        if dm < 10.5 or facing_tile < 0.44:
            flush_run(run)
            run = []
            continue
        k = max(1, int(math.ceil(L / seg_step)))
        if not run:
            run.append(a)
        for i in range(1, k + 1):
            run.append(a + (b - a) * (i / k))
    flush_run(run)

    # 2. Internal layered ridge curtains facing the region centre so looking across a stand shows depth & layered tree tops
    _, _, de_c, dn_c, dm_c = outside_dist(ce, cn, half)
    to_center = np.array([-de_c, -dn_c], dtype=np.float64) if dm_c > 1.0 else np.array([-ce, -cn], dtype=np.float64)
    tc_len = float(np.hypot(to_center[0], to_center[1]))
    if tc_len > 1e-3:
        u_dir = to_center / tc_len
        v_dir = np.array([-u_dir[1], u_dir[0]])
        bminx, bminy, bmaxx, bmaxy = poly_eff.bounds
        span = max(bmaxx - bminx, bmaxy - bminy)
        rib_spacing = 34.0 if tier == "High" else 76.0
        n_ribs = min(int(span // rib_spacing), 12 if tier == "High" else 3)
        for ri in range(1, n_ribs + 1):
            off = (ri - 0.5 * (n_ribs + 1)) * rib_spacing
            p_mid = np.array([ce, cn]) + u_dir * off
            cut_line = LineString([p_mid - v_dir * span, p_mid + v_dir * span])
            inter = poly_eff.intersection(cut_line)
            for seg in getattr(inter, "geoms", [inter]):
                if seg.geom_type == "LineString" and seg.length >= 22.0:
                    sc = np.asarray(seg.coords, dtype=np.float64)
                    if (sc[-1, 0] - sc[0, 0]) * v_dir[0] + (sc[-1, 1] - sc[0, 1]) * v_dir[1] < 0.0:
                        sc = sc[::-1]
                    L = float(seg.length)
                    ks = max(2, int(math.ceil(L / seg_step)))
                    P = np.array([sc[0] + (sc[-1] - sc[0]) * (i / ks) for i in range(ks + 1)])
                    s = np.linspace(0.0, L, ks + 1)
                    end_taper = np.minimum(np.clip(s / 30.0, 0.30, 1.0), np.clip((L - s) / 30.0, 0.30, 1.0))
                    zg = np.array([elev.z_at_eff(p[0], p[1]) for p in P])
                    ht = _crown_height_wave(P[:, 0] + ri * 17.3, P[:, 1] - ri * 11.7, h_base * 1.08, half) * end_taper
                    sec.add_curtain1(P, zg - 0.5, zg + ht, face_sign=1.0)

    # 3. Sloping dark conifer/mixed under-canopy mound tucked 10 m inside, split into <= 320 m convex-ish cells so
    #    triangle fans never bridge concave bays or road corridors
    inset = poly_eff.buffer(-10.0)
    if inset.is_empty:
        return
    ibminx, ibminy, ibmaxx, ibmaxy = inset.bounds
    cell_step = 320.0
    cells = []
    for gx in np.arange(ibminx, ibmaxx, cell_step):
        for gy in np.arange(ibminy, ibmaxy, cell_step):
            c_piece = inset.intersection(box(gx, gy, gx + cell_step, gy + cell_step))
            if not c_piece.is_empty:
                for g in getattr(c_piece, "geoms", [c_piece]):
                    if g.geom_type == "Polygon" and g.area >= 220.0:
                        cells.append(g)
    for g in cells:
        gs = g.simplify(8.0 if tier == "High" else 14.0, preserve_topology=True)
        if gs.geom_type != "Polygon" or gs.area < 150.0:
            continue
        ring = np.asarray(gs.exterior.coords, dtype=np.float64)[:-1]
        if len(ring) < 3:
            continue
        if not Polygon(ring).exterior.is_ccw:
            ring = ring[::-1]
        c_xy = ring.mean(axis=0)
        z_c = elev.z_at_eff(c_xy[0], c_xy[1])
        h_cap = max(h_base * 0.38, 3.5)
        col_top = (0.028, 0.044, 0.019, 0.0) if mix == "conifer" else (0.034, 0.052, 0.022, 0.0)
        p_apex = [c_xy[0], c_xy[1], z_c + h_cap]
        m = len(ring)
        for i in range(m):
            a = ring[i]
            b = ring[(i + 1) % m]
            za = elev.z_at_eff(a[0], a[1])
            zb = elev.z_at_eff(b[0], b[1])
            pa_bot = [a[0], a[1], za - 0.4]
            pb_bot = [b[0], b[1], zb - 0.4]
            sec.add_tri0(pa_bot, pb_bot, p_apex, col_top, normal=[0.0, 0.0, 1.0])


def _wall_visible_from_tile(a: np.ndarray, c: np.ndarray, half: float = 1024.0) -> bool:
    """Return True if a vertical wall from a to c (outward normal to the right of a->c) can be seen from anywhere inside [-half, +half]^2."""
    dx, dy = float(c[0] - a[0]), float(c[1] - a[1])
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return False
    nx, ny = dy / L, -dx / L  # outward normal of CCW polygon edge a->c
    mx, my = 0.5 * (a[0] + c[0]), 0.5 * (a[1] + c[1])
    for tx in (-half, half):
        for ty in (-half, half):
            if nx * (tx - mx) + ny * (ty - my) > -25.0:
                return True
    return False


def _hall_appearance_class(b: dict) -> str:
    """WORKING_VALUE surface typology from declared use, never measured height.

    Function is GIS data; cladding, colours and glazing below are estimates.
    A large hall-shaped footprint alone does not establish an industrial use.
    """
    function = str(b.get("func") or "").casefold()
    if any(word in function for word in ("elektrociepł", "elektrown", "ciepłown", "kotłown")):
        return "energy"
    if any(word in function for word in (
            "przemysł", "produkc", "magazyn", "składow", "warsztat", "fabryk", "spalarn",
            "industrial", "warehouse", "manufactur", "factory", "storage", "workshop")):
        return "industrial"
    return "other"


def _add_building(sectors: dict[str, SectorBuilder], b: dict, elev: BorderElevation, half: float, tier: str, exclusion=None,
                  skyline: SectorBuilder | None = None):
    rc = np.asarray(b["rect"], dtype=np.float64)
    if len(rc) < 4 or not building_outside_region(Polygon(rc), half, exclusion):
        return
    if not Polygon(rc).exterior.is_ccw:
        rc = rc[::-1]
    cx_raw, cy_raw = float(rc[:, 0].mean()), float(rc[:, 1].mean())
    _, _, _, _, d_raw = outside_dist(cx_raw, cy_raw, half)
    typ = b["typ"]
    area = float(b["area"])
    h_raw = float(b["h"])

    # Tier-specific density pruning so Low stays <= 27k tris total across all 4 sectors (~5-8k per sector)
    if tier == "Low":
        if typ == "house" and (d_raw > 140.0 or area < 120.0):
            return
        if typ == "office" and (d_raw > 360.0 or (d_raw > 180.0 and area < 380.0)):
            return
        if typ == "hall" and (d_raw > 850.0 and area < 1100.0 or (d_raw > 380.0 and area < 520.0)):
            return
        if typ == "block" and (d_raw > 1050.0 and area < 520.0 and h_raw < 22.0 or (d_raw > 580.0 and area < 320.0 and h_raw < 16.0)):
            return
    else:
        if typ == "house" and d_raw > 420.0:
            return
        if typ == "office" and d_raw > 1300.0 and area < 280.0:
            return

    ce, cn, _, _ = foreshorten_point(cx_raw, cy_raw, half)
    s_xy, s_h = foreshorten_scales(d_raw)
    pts = np.array([[ce + (p[0] - cx_raw) * s_xy, cn + (p[1] - cy_raw) * s_xy] for p in rc[:4]], dtype=np.float64)
    if not building_outside_region(Polygon(pts), half, exclusion):
        return
    sec = sectors[sector_of(ce, cn, half)]
    if skyline is not None and h_raw >= SKYLINE_MIN_BUILDING_H_M and typ in ("block", "office", "hall"):
        sec = skyline   # ADR 0141: same geometry, kept visible beyond the camera far plane

    z_ref = elev.z_at_eff(ce, cn)
    z_bot = z_ref - 0.8
    h_eff = max(h_raw * s_h, 3.2)
    z_top = z_ref + h_eff
    bid = str(b["id"])

    edges_raw = [float(np.hypot(rc[(i + 1) % 4, 0] - rc[i, 0], rc[(i + 1) % 4, 1] - rc[i, 1])) for i in range(4)]
    long_idx = 0 if edges_raw[0] >= edges_raw[1] else 1

    if typ == "block":
        wall_rgb = _hpick(bid, PALETTE_BLOCK, "wall")
        gable_rgb = _hpick(bid, PALETTE_BLOCK_GABLE, "gable") if _hfloat(bid, "has_gable") < 0.65 else wall_rgb
        storeys = b.get("storeys") or max(4, int(round((h_raw - 1.2) / 2.85)))
        storeys = max(3, min(storeys, 12))
        z_attic = z_top - (min(0.45 * s_h, h_eff * 0.08) if tier == "High" else 0.0)

        for i in range(4):
            a, c = pts[i], pts[(i + 1) % 4]
            if not _wall_visible_from_tile(a, c, half):
                continue
            L_raw = edges_raw[i]
            is_gable = (i % 2) != (long_idx % 2) and L_raw < 16.5
            rgb = gable_rgb if is_gable else wall_rgb
            if not is_gable and L_raw >= 6.0:
                bays = max(2, int(round(L_raw / 3.0)))
                uv1 = [[0.0, -0.38], [float(bays), -0.38], [float(bays), float(storeys) + 0.15], [0.0, float(storeys) + 0.15]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_attic], [a[0], a[1], z_attic],
                              (*rgb, 1.0), uv1=uv1)
            else:
                if L_raw >= 9.0 and _hfloat(bid, f"gwin_{i}") < 0.45:
                    bays = max(1, int(round(L_raw / 4.5)))
                    uv1 = [[0.0, -0.38], [float(bays), -0.38], [float(bays), float(storeys) + 0.15], [0.0, float(storeys) + 0.15]]
                    sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_attic], [a[0], a[1], z_attic],
                                  (*rgb, 1.0), uv1=uv1)
                else:
                    sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_attic], [a[0], a[1], z_attic],
                                  (*rgb, 0.0))
            if tier == "High":
                sec.add_quad0([a[0], a[1], z_attic], [c[0], c[1], z_attic], [c[0], c[1], z_top], [a[0], a[1], z_top],
                              (*COL_PARAPET, 0.0))

        if tier == "High" or h_eff <= 4.5:
            sec.add_quad0([pts[0, 0], pts[0, 1], z_top], [pts[1, 0], pts[1, 1], z_top],
                          [pts[2, 0], pts[2, 1], z_top], [pts[3, 0], pts[3, 1], z_top],
                          (*COL_ROOF_FLAT, 0.0), normal=[0.0, 0.0, 1.0])

        # Elevator / stairwell penthouse on taller wielka-płyta blocks
        if storeys >= 6 and (tier == "High" or (d_raw < 900.0 and storeys >= 8)):
            u_vec = pts[(long_idx + 1) % 4] - pts[long_idx]
            v_vec = pts[(long_idx + 3) % 4] - pts[long_idx]
            lu = max(float(np.linalg.norm(u_vec)), 1.0)
            lv = max(float(np.linalg.norm(v_vec)), 1.0)
            du, dv = u_vec / lu, v_vec / lv
            pc = pts[long_idx] + u_vec * 0.35 + v_vec * 0.5
            pw = min(2.4 * s_xy, lu * 0.18)
            pd = min(1.8 * s_xy, lv * 0.28)
            ph = max(1.8 * s_h, 1.1)
            p_pts = [
                pc - du * pw - dv * pd,
                pc + du * pw - dv * pd,
                pc + du * pw + dv * pd,
                pc - du * pw + dv * pd,
            ]
            for k in range(4):
                qa, qb = p_pts[k], p_pts[(k + 1) % 4]
                if _wall_visible_from_tile(qa, qb, half):
                    sec.add_quad0([qa[0], qa[1], z_top], [qb[0], qb[1], z_top],
                                  [qb[0], qb[1], z_top + ph], [qa[0], qa[1], z_top + ph], (*wall_rgb, 0.0))
        return

    if typ == "hall":
        appearance = _hall_appearance_class(b)
        industrial = appearance == "industrial"
        panel_hall = industrial and h_raw >= 12.0  # WORKING_VALUE appearance, not a measured facade
        wall_rgb = (0.24, 0.10, 0.07) if appearance == "energy" else _hpick(bid, PALETTE_HALL, "wall")
        # Unknown branding is not a reason for a bright 16%-height coloured stripe.
        acc_rgb = tuple(c * 0.72 for c in wall_rgb) if industrial else _hpick(bid, PALETTE_HALL_ACCENT, "acc")
        use_fascia = tier == "High" or d_raw < 700.0
        fascia_h = min(max(0.35 * s_h, 0.10), h_eff * 0.04) if industrial else max(1.1 * s_h, h_eff * 0.16)
        z_fascia = z_top - fascia_h if use_fascia else z_top
        has_clerestory = panel_hall or _hfloat(bid, "clere") < 0.55

        for i in range(4):
            a, c = pts[i], pts[(i + 1) % 4]
            if not _wall_visible_from_tile(a, c, half):
                continue
            L_raw = edges_raw[i]
            is_long = (i % 2) == (long_idx % 2)
            if is_long and has_clerestory and L_raw >= 16.0:
                bays = max(3, int(round(L_raw / 4.0)))
                # Only the top row is positive: do not invent a storey count.
                # The 4 m source-height module gives an estimated ~1.8 m upper
                # glazing band. Preserve the legacy contract for other halls.
                bottom_v = 1.0 - (z_fascia - z_bot) / max(4.0 * s_h, 0.1) if panel_hall else -1.2
                uv1 = [[0.0, bottom_v], [float(bays), bottom_v], [float(bays), 1.0], [0.0, 1.0]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_fascia], [a[0], a[1], z_fascia],
                              (*wall_rgb, 0.65 if panel_hall else 0.75), uv1=uv1)
            else:
                panel_uv = None
                if panel_hall:
                    # Explicit opaque-cladding payload: 1.2 m wide / 3 m high
                    # source modules, carried in the already-existing UV1.
                    columns = L_raw / 1.2
                    rows = (z_fascia - z_bot) / max(3.0 * s_h, 0.1)
                    panel_uv = [[0.0, 0.0], [columns, 0.0], [columns, rows], [0.0, rows]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_fascia], [a[0], a[1], z_fascia],
                              (*wall_rgb, 0.25 if panel_hall else 0.0), uv1=panel_uv)
            if use_fascia:
                sec.add_quad0([a[0], a[1], z_fascia], [c[0], c[1], z_fascia], [c[0], c[1], z_top], [a[0], a[1], z_top],
                              (*acc_rgb, 0.0))

        if tier == "High" or h_eff <= 4.5:
            sec.add_quad0([pts[0, 0], pts[0, 1], z_top], [pts[1, 0], pts[1, 1], z_top],
                          [pts[2, 0], pts[2, 1], z_top], [pts[3, 0], pts[3, 1], z_top],
                          (*COL_ROOF_FLAT, 0.0), normal=[0.0, 0.0, 1.0])
        return

    if typ == "office":
        wall_rgb = _hpick(bid, PALETTE_OFFICE, "wall")
        storeys = b.get("storeys") or max(2, int(round((h_raw - 0.8) / 3.4)))
        storeys = max(2, min(storeys, 8))
        w_mode = 0.75 if _hfloat(bid, "rib") < 0.4 else 1.0
        for i in range(4):
            a, c = pts[i], pts[(i + 1) % 4]
            if not _wall_visible_from_tile(a, c, half):
                continue
            L_raw = edges_raw[i]
            if L_raw >= 6.0:
                bays = max(2, int(round(L_raw / 3.2)))
                uv1 = [[0.0, -0.25], [float(bays), -0.25], [float(bays), float(storeys)], [0.0, float(storeys)]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_top], [a[0], a[1], z_top],
                              (*wall_rgb, w_mode), uv1=uv1)
            else:
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_top], [a[0], a[1], z_top],
                              (*wall_rgb, 0.0))
        if tier == "High" or h_eff <= 4.5:
            sec.add_quad0([pts[0, 0], pts[0, 1], z_top], [pts[1, 0], pts[1, 1], z_top],
                          [pts[2, 0], pts[2, 1], z_top], [pts[3, 0], pts[3, 1], z_top],
                          (*COL_ROOF_FLAT, 0.0), normal=[0.0, 0.0, 1.0])
        return

    # Single-family house with pitched gable roof
    wall_rgb = _hpick(bid, PALETTE_HOUSE, "wall")
    roof_rgb = _hpick(bid, PALETTE_ROOF_PITCHED, "roof")
    z_eave = z_ref + h_eff * 0.62
    z_ridge = z_ref + h_eff
    a, b_pt, c, d = (pts[(long_idx + k) % 4] for k in range(4))
    m1 = 0.5 * (a + d)
    m2 = 0.5 * (b_pt + c)
    for p0, p1 in ((a, b_pt), (c, d)):
        if _wall_visible_from_tile(p0, p1, half):
            uv1 = [[0.0, -0.2], [3.0, -0.2], [3.0, 1.8], [0.0, 1.8]]
            sec.add_quad0([p0[0], p0[1], z_bot], [p1[0], p1[1], z_bot], [p1[0], p1[1], z_eave], [p0[0], p0[1], z_eave],
                          (*wall_rgb, 1.0), uv1=uv1)
    for p0, p1, m in ((b_pt, c, m2), (d, a, m1)):
        if _wall_visible_from_tile(p0, p1, half):
            sec.add_quad0([p0[0], p0[1], z_bot], [p1[0], p1[1], z_bot], [p1[0], p1[1], z_eave], [p0[0], p0[1], z_eave],
                          (*wall_rgb, 0.0))
            sec.add_tri0([p0[0], p0[1], z_eave], [p1[0], p1[1], z_eave], [m[0], m[1], z_ridge], (*wall_rgb, 0.0))
    sec.add_quad0([a[0], a[1], z_eave], [b_pt[0], b_pt[1], z_eave], [m2[0], m2[1], z_ridge], [m1[0], m1[1], z_ridge],
                  (*roof_rgb, 0.0))
    sec.add_quad0([c[0], c[1], z_eave], [d[0], d[1], z_eave], [m1[0], m1[1], z_ridge], [m2[0], m2[1], z_ridge],
                  (*roof_rgb, 0.0))


def _add_chimney(sectors: dict[str, SectorBuilder], ch: dict, elev: BorderElevation, half: float, tier: str,
                 skyline: SectorBuilder | None = None):
    e_raw, n_raw = float(ch["e"]), float(ch["n"])
    h_raw = float(ch["h"])
    ce, cn, d_raw, _ = foreshorten_point(e_raw, n_raw, half)
    _, s_h = foreshorten_scales(d_raw)
    sec = sectors[sector_of(ce, cn, half)]
    if skyline is not None and h_raw >= SKYLINE_MIN_CHIMNEY_H_M:
        sec = skyline   # ADR 0141
    z_ref = elev.z_at_eff(ce, cn)
    z_bot = z_ref - 1.0
    # Tall chimneys are key skyline landmarks (EC Białystok 113 m / 102 m, Fast/Bacieczki 73 m, etc.)
    h_eff = max(h_raw * (s_h ** 0.78), 18.0)

    sides = 8 if tier == "High" else 6
    r_bot = max(h_raw * 0.042, 2.2) * max(s_h, 0.65)
    r_top = max(h_raw * 0.022, 1.2) * max(s_h, 0.65)

    # Lower 72% shaft (concrete for >45 m, brick for smaller industrial chimneys), upper 28% in 4 red/white bands
    base_col = COL_CHIMNEY_CONCRETE if h_raw >= 45.0 else COL_CHIMNEY_BRICK
    bands = [
        (0.00, 0.72, base_col),
        (0.72, 0.79, COL_CHIMNEY_RED),
        (0.79, 0.86, COL_CHIMNEY_WHITE),
        (0.86, 0.93, COL_CHIMNEY_RED),
        (0.93, 1.00, COL_CHIMNEY_WHITE),
    ]
    angles = [2.0 * math.pi * k / sides for k in range(sides)]
    cs = [(math.cos(a), math.sin(a)) for a in angles]

    for f0, f1, col in bands:
        z0 = z_bot if f0 == 0.0 else z_ref + f0 * h_eff
        z1 = z_ref + f1 * h_eff
        r0 = r_bot + (r_top - r_bot) * f0
        r1 = r_bot + (r_top - r_bot) * f1
        for k in range(sides):
            c0, s0 = cs[k]
            c1, s1 = cs[(k + 1) % sides]
            p00 = [ce + r0 * c0, cn + r0 * s0, z0]
            p10 = [ce + r0 * c1, cn + r0 * s1, z0]
            p11 = [ce + r1 * c1, cn + r1 * s1, z1]
            p01 = [ce + r1 * c0, cn + r1 * s0, z1]
            sec.add_quad0(p00, p10, p11, p01, (*col, 0.0))


def region_landmark_stacks(region_id: str, ox: float, oy: float) -> list[dict]:
    """Landmark chimneys the region itself draws (overrides.yaml kind=landmark; EC Bialystok, ADR 0116). Their hero
    meshes end at the camera far plane, so the skyline carries a plain stand-in that is drawn only beyond it."""
    import yaml

    out = []
    try:
        ov = yaml.safe_load((pipeline.REGIONS / region_id / "overrides.yaml").read_text(encoding="utf-8")) or {}
    except OSError:
        return out
    try:
        cfg = json.loads((pipeline.REGIONS / region_id / "ec_chimneys.json").read_text(encoding="utf-8"))
        stacks = cfg.get("stacks", {}) if cfg.get("enabled") is True else {}
    except (OSError, ValueError):
        stacks = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("kind") == "landmark" and "epsg2180" in node and "height_m" in node:
                yield node
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)

    for o in walk(ov):
        st = stacks.get(str(o.get("osm_way")), {})
        h = float(st.get("height_m", o["height_m"]))
        bounds = [float(x) for x in st.get("band_boundaries_m", [])]
        if len(bounds) < 2:
            bounds = [round(h * f, 2) for f in (0.72, 0.79, 0.86, 0.93, 1.0)]   # generic top marking, as _add_chimney
        out.append({
            "id": str(o["id"]),
            "e": float(o["epsg2180"][0]) - ox,
            "n": float(o["epsg2180"][1]) - oy,
            "h": h,
            "base_d": float(st.get("base_d_m", o.get("base_d_m", 7.5))),
            "top_d": float(st.get("top_d_m", o.get("top_d_m", 4.5))),
            "band_boundaries": bounds,
        })
    return out


def _add_landmark_stack_proxy(skyline: SectorBuilder, st: dict, elev: BorderElevation, tier: str):
    """Plain banded cone with the stack's source height, diameters and band limits, flagged BEYOND: the vertex shader
    clips it wherever the hero mesh is inside the far plane, so the two never overlap."""
    ce, cn, h = st["e"], st["n"], st["h"]
    z_ref = elev.z_at_eff(ce, cn)
    sides = 8 if tier == "High" else 6
    cs = [(math.cos(2.0 * math.pi * k / sides), math.sin(2.0 * math.pi * k / sides)) for k in range(sides)]
    limits = [0.0] + list(st["band_boundaries"])
    prev = skyline.uv1_flag
    skyline.uv1_flag = SKYLINE_FLAG_BEYOND
    try:
        for i in range(len(limits) - 1):
            z0h, z1h = limits[i], limits[i + 1]
            # Bare concrete shaft, then alternating red / white bands starting with red (ec_chimneys.json limits).
            col = COL_CHIMNEY_CONCRETE if i == 0 else (COL_CHIMNEY_RED if i % 2 == 1 else COL_CHIMNEY_WHITE)
            r0 = 0.5 * (st["base_d"] + (st["top_d"] - st["base_d"]) * z0h / h)
            r1 = 0.5 * (st["base_d"] + (st["top_d"] - st["base_d"]) * z1h / h)
            z0 = z_ref - 1.0 if i == 0 else z_ref + z0h
            z1 = z_ref + z1h
            for k in range(sides):
                c0, s0 = cs[k]
                c1, s1 = cs[(k + 1) % sides]
                skyline.add_quad0([ce + r0 * c0, cn + r0 * s0, z0], [ce + r0 * c1, cn + r0 * s1, z0],
                                  [ce + r1 * c1, cn + r1 * s1, z1], [ce + r1 * c0, cn + r1 * s0, z1], (*col, 0.0))
    finally:
        skyline.uv1_flag = prev


def _add_pylon(sectors: dict[str, SectorBuilder], py: dict, elev: BorderElevation, half: float, tier: str, yaw: float = 0.0):
    e_raw, n_raw = float(py["e"]), float(py["n"])
    h_raw = max(float(py.get("h") or 26.0), 22.0)
    ce, cn, d_raw, _ = foreshorten_point(e_raw, n_raw, half)
    if tier == "Low" and d_raw > 2200.0:
        return
    _, s_h = foreshorten_scales(d_raw)
    sec = sectors[sector_of(ce, cn, half)]
    z_ref = elev.z_at_eff(ce, cn)
    z_bot = z_ref - 0.8
    h_eff = max(h_raw * s_h, 14.0)
    z_top = z_ref + h_eff

    ca, sa = math.cos(yaw), math.sin(yaw)
    ux, uy = ca, sa
    vx, vy = -sa, ca
    col = (*COL_PYLON_STEEL, 0.0)

    # Tapered 4-sided lattice mast + 2 double cross-arms
    w_bot = 2.1 * max(s_h, 0.65)
    w_top = 0.55 * max(s_h, 0.65)

    def ring_pts(w: float, z: float):
        return [
            [ce - ux * w - vx * w, cn - uy * w - vy * w, z],
            [ce + ux * w - vx * w, cn + uy * w - vy * w, z],
            [ce + ux * w + vx * w, cn + uy * w + vy * w, z],
            [ce - ux * w + vx * w, cn - uy * w + vy * w, z],
        ]

    # 4 corner legs as 2 crossed tapered fins (double-sided quads so silhouette reads from every angle for 16 tris)
    rb = ring_pts(w_bot, z_bot)
    rt = ring_pts(w_top, z_top)
    for a0, a1, b1, b0 in (
        (rb[0], rb[2], rt[2], rt[0]),
        (rb[2], rb[0], rt[0], rt[2]),
        (rb[1], rb[3], rt[3], rt[1]),
        (rb[3], rb[1], rt[1], rt[3]),
    ):
        sec.add_quad0(a0, a1, b1, b0, col)

    # Two horizontal cross-arms at 70% and 88% height
    for frac, span in ((0.70, 5.2), (0.88, 3.8)):
        za = z_ref + h_eff * frac
        zh = max(0.75 * s_h, 0.45)
        sp = span * max(s_h, 0.65)
        p_l0 = [ce - vx * sp, cn - vy * sp, za]
        p_r0 = [ce + vx * sp, cn + vy * sp, za]
        p_mid = [ce, cn, za + zh]
        sec.add_tri0(p_l0, p_r0, p_mid, col)
        sec.add_tri0(p_r0, p_l0, p_mid, col)


def _corridor_treelines(half: float = 1024.0) -> list[dict]:
    """Horizon pine stands closing the distant DK8 curve in Las Bacieczki/Pietrasze and framing the western exit."""
    return [
        # North exit (al. Tysiąclecia N, E ~ -857, N = +1024, dir = (-0.21, +0.98)): Las Bacieczki/Pietrasze flanks DK8 and closes the curve at N >= 1105 m
        {"coords": [[-1080, 1038], [-896, 1038], [-915, 1185], [-1100, 1185], [-1080, 1038]], "mix": "conifer"},
        {"coords": [[-816, 1038], [-620, 1038], [-640, 1190], [-835, 1190], [-816, 1038]], "mix": "conifer"},
        {"coords": [[-1050, 1105], [-710, 1105], [-730, 1310], [-1075, 1310], [-1050, 1105]], "mix": "conifer"},
        {"coords": [[-1090, 1190], [-680, 1190], [-710, 1480], [-1120, 1480], [-1090, 1190]], "mix": "conifer"},
        {"coords": [[-1140, 1350], [-650, 1350], [-680, 1760], [-1170, 1760], [-1140, 1350]], "mix": "conifer"},
        # West exit (ul. Gen. Stanisława Maczka W, E = -1024, N ~ +44, dir = (-1.00, -0.09)): Las Bacieczki on right, Fasty halls + shelterbelts ahead
        {"coords": [[-1220, -140], [-1040, -140], [-1040, 2], [-1220, -12], [-1220, -140]], "mix": "mixed"},
        {"coords": [[-1220, 84], [-1040, 84], [-1040, 260], [-1220, 250], [-1220, 84]], "mix": "conifer"},
        {"coords": [[-1560, -140], [-1250, -140], [-1250, 160], [-1560, 160], [-1560, -140]], "mix": "conifer"},
        {"coords": [[-1920, -180], [-1520, -180], [-1520, 220], [-1920, 220], [-1920, -180]], "mix": "mixed"},
    ]


def build_apron_masks(gis: dict, elev: BorderElevation, half: float = 1024.0) -> dict:
    """Compute apron vertex ground-mask lookup + border height profile for WorldEdgeBuilder.BuildApron."""
    f_polys = []
    for f in gis["forests"] + _corridor_treelines(half):
        pts = [foreshorten_point(p[0], p[1], half)[:2] for p in f["coords"]]
        if len(pts) >= 3:
            p = shapely.make_valid(Polygon(pts))
            if p.area > 50.0:
                f_polys.append(p.buffer(18.0))
    f_union = shapely.union_all(f_polys) if f_polys else Polygon()
    shapely.prepare(f_union)

    u_polys = []
    for b in gis["buildings"]:
        rc = b["rect"]
        cx, cy = sum(p[0] for p in rc) / 4.0, sum(p[1] for p in rc) / 4.0
        ce, cn, _, _ = foreshorten_point(cx, cy, half)
        u_polys.append(Point(ce, cn).buffer(32.0))
    u_union = shapely.union_all(u_polys) if u_polys else Polygon()
    shapely.prepare(u_union)

    return {
        "schema": "truck-sim-pl/far-field-apron/1",
        "half_m": half,
        "apron_ease_m": APRON_EASE_M,
        "mean_z": round(elev.mean, 3),
        "border_step_m": 16.0,
        "border_z": {
            "south": elev.south.tolist(),
            "east": elev.east.tolist(),
            "north": elev.north.tolist(),
            "west": elev.west.tolist(),
        },
        "_f_union": f_union,
        "_u_union": u_union,
    }


def build_far_field(region_id: str, out_root: Path | None = None) -> dict:
    reg = pipeline.load_region(region_id)
    ox, oy = float(reg["origin"]["x"]), float(reg["origin"]["y"])
    half = float(reg["bbox"]["width_m"]) / 2.0
    out_root = out_root or (REPO / "Data" / "raw" / "derived" / region_id / "world")
    out_root.mkdir(parents=True, exist_ok=True)

    elev = BorderElevation.from_region(region_id, half=half)
    gis = extract_ring_gis(region_id, ox, oy, half=half)
    building_exclusion = region_building_exclusion(region_id, ox, oy, half)

    # Supplement power line pylons along OT_SULN_L spans where point towers were sparse
    extra_pylons = []
    existing_py = [(p["e"], p["n"]) for p in gis["pylons"]]
    for pl in gis["power_lines"]:
        line = LineString(pl)
        L = float(line.length)
        for s in np.arange(90.0, L - 40.0, 210.0):
            pt = line.interpolate(float(s))
            if not any(math.hypot(pt.x - ex, pt.y - en) < 95.0 for ex, en in existing_py):
                p2 = line.interpolate(min(float(s) + 5.0, L))
                yaw = math.atan2(p2.y - pt.y, p2.x - pt.x)
                extra_pylons.append({"id": f"pl_{len(extra_pylons)}", "e": pt.x, "n": pt.y, "h": 27.0, "yaw": yaw})
                existing_py.append((pt.x, pt.y))

    all_materials = {**SM.M, **FH.materials()}
    qa_tiers = {}
    landmark_stacks = region_landmark_stacks(region_id, ox, oy)

    for tier, fn, compact in (("High", "far_field.glb", False), ("Low", "far_field.low.glb", True)):
        sectors = {name: SectorBuilder(name) for name in SECTORS}
        skyline = SectorBuilder(SKYLINE, uv1_flag=SKYLINE_FLAG_CLAMP)

        for f in gis["forests"] + _corridor_treelines(half):
            _add_forest_stand(sectors, f["coords"], f.get("mix", "mixed"), elev, half, tier)

        for b in gis["buildings"]:
            _add_building(sectors, b, elev, half, tier, exclusion=building_exclusion, skyline=skyline)

        for ch in gis["chimneys"]:
            if any(math.hypot(ch["e"] - st["e"], ch["n"] - st["n"]) < SKYLINE_PROXY_MERGE_M for st in landmark_stacks):
                continue   # the region draws this stack (hero mesh); the skyline carries its far stand-in
            _add_chimney(sectors, ch, elev, half, tier, skyline=skyline)
        for st in landmark_stacks:
            _add_landmark_stack_proxy(skyline, st, elev, tier)
        skyline.sort_far_to_near()

        for py in gis["pylons"]:
            _add_pylon(sectors, py, elev, half, tier, yaw=float(py.get("yaw", 0.4)))
        for py in extra_pylons:
            _add_pylon(sectors, py, elev, half, tier, yaw=float(py.get("yaw", 0.0)))

        glb = GLB(all_materials, compact=compact)
        sector_stats = {}
        total_tris = 0
        total_verts = 0
        for name in SECTORS:
            prims = sectors[name].primitives()
            tris = int(sum(len(p["T"]) for p in prims))
            verts = int(sum(len(p["V"]) for p in prims))
            total_tris += tris
            total_verts += verts
            sector_stats[name] = {
                "submeshes": len(prims),
                "triangles": tris,
                "vertices": verts,
                "by_material": {p["mat"]: int(len(p["T"])) for p in prims},
            }
            glb.add_mesh(name, prims, {"layer": "far_field", "sector": name, "tier": tier})
        sky_prims = skyline.primitives()
        sky_tris = int(sum(len(p["T"]) for p in sky_prims))
        total_tris += sky_tris
        total_verts += int(sum(len(p["V"]) for p in sky_prims))
        if sky_prims:
            glb.add_mesh(SKYLINE, sky_prims, {"layer": "far_field", "sector": SKYLINE, "tier": tier})

        data = glb.bytes({
            "region": region_id,
            "layer": "far_field",
            "tier": tier,
            "axes": GLTF_AXES,
            "apron_ease_m": APRON_EASE_M,
            "mean_z": round(elev.mean, 3),
        })
        out_path = out_root / fn
        out_path.write_bytes(data)
        qa_tiers[tier] = {
            "file": f"Data/raw/derived/{region_id}/world/{fn}",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "total_triangles": total_tris,
            "total_vertices": total_verts,
            "sectors": sector_stats,
            "skyline": {
                "node": SKYLINE,
                "submeshes": len(sky_prims),
                "triangles": sky_tris,
                "landmark_stack_proxies": [st["id"] for st in landmark_stacks],
                "min_building_h_m": SKYLINE_MIN_BUILDING_H_M,
                "min_chimney_h_m": SKYLINE_MIN_CHIMNEY_H_M,
            },
        }

    # Write apron JSON (border height profile for WorldEdgeBuilder)
    apron_info = build_apron_masks(gis, elev, half)
    apron_json = {k: v for k, v in apron_info.items() if not k.startswith("_")}
    apron_path = out_root / "far_field_apron.json"
    apron_path.write_text(json.dumps(apron_json, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    # Write SourceManifest in Data/SourceManifests/
    manifest_dir = REPO / "Data" / "SourceManifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    appearance_policy = {
        "schema": "far-field-appearance/1",
        "status": "WORKING_VALUE",
        "not_measured": ["wall_colour", "cladding_modules", "glazing_band", "roof_fascia"],
        "classification": "declared function; height alone does not imply an energy plant",
        "industrial_panel_min_height_m": 12.0,
        "panel_alpha": 0.25,
        "panel_ribbon_alpha": 0.65,
        "source_hall_counts": {
            kind: sum(1 for b in gis["buildings"] if b["typ"] == "hall" and _hall_appearance_class(b) == kind)
            for kind in ("industrial", "energy", "other")
        },
        "source_panel_hall_count": sum(1 for b in gis["buildings"] if b["typ"] == "hall"
                                       and b["h"] >= 12.0 and _hall_appearance_class(b) == "industrial"),
    }
    src_manifest = {
        "schema": "truck-sim-pl/source-manifest/1",
        "id": f"{region_id}-far-field",
        "region": region_id,
        "adr": "0085-far-field-backdrop",
        "appearance_policy": appearance_policy,
        "ring_bounds_local_m": {"inner_half_m": half, "outer_half_m": RING_MAX_M},
        "region_inputs_sha256": {k: v for k, v in gis["sources_sha256"].items() if k.startswith("region/")},
        "lod1_height_audit": gis["lod1_height_audit"],
        "building_height_sources": gis["building_height_sources"],
        "sources": [
            {
                "id": "gugik-bdot10k-2061",
                "provider": "Główny Urząd Geodezji i Kartografii (GUGiK)",
                "dataset": "BDOT10k powiat 2061 (m. Białystok): OT_PTLZ_A, OT_BUBD_A, OT_BUWT_P, OT_SULN_L",
                "license": "Open public data — Art. 40a ust. 2 pkt 1 lit. a Prawa geodezyjnego i kartograficznego (Dz.U. 2020 poz. 276)",
                "files": {k: v for k, v in gis["sources_sha256"].items() if k.startswith("bdot10k/")},
            },
            {
                "id": "gugik-lod1-2024-2061",
                "provider": "Główny Urząd Geodezji i Kartografii (GUGiK)",
                "dataset": "Modele 3D budynków LoD1 (2024) powiat 2061 (m. Białystok)",
                "license": "Open public data — Art. 40a ust. 2 pkt 1 lit. i Prawa geodezyjnego i kartograficznego",
                "files": {k: v for k, v in gis["sources_sha256"].items() if k.startswith("lod1/")},
            },
            {
                "id": "geofabrik-osm-podlaskie-261108",
                "provider": "OpenStreetMap contributors / Geofabrik GmbH",
                "dataset": "podlaskie-261108.osm.pbf (ring outside tile incl. powiat 2002)",
                "license": "ODbL 1.0 (© OpenStreetMap contributors)",
                "files": {k: v for k, v in gis["sources_sha256"].items() if k.startswith("osm/")},
            },
        ],
        "feature_counts": {
            "forest_polygons": len(gis["forests"]),
            "buildings": len(gis["buildings"]),
            "buildings_by_typology": {
                t: sum(1 for b in gis["buildings"] if b["typ"] == t)
                for t in ("block", "hall", "office", "house")
            },
            "chimneys": len(gis["chimneys"]),
            "pylons": len(gis["pylons"]) + len(extra_pylons),
            "power_lines": len(gis["power_lines"]),
        },
    }
    (manifest_dir / f"{region_id}-far-field.manifest.json").write_text(
        json.dumps(src_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    # Write QA report in Data/Regions/<id>/generated/far_field_qa.json
    qa_report = {
        "schema": "truck-sim-pl/far-field-qa/1",
        "region": region_id,
        "feature_counts": src_manifest["feature_counts"],
        "appearance_policy": appearance_policy,
        "boundary_exclusions": gis["boundary_exclusions"],
        "lod1_height_audit": gis["lod1_height_audit"],
        "building_height_sources": gis["building_height_sources"],
        "tiers": qa_tiers,
    }
    gen_dir = pipeline.REGIONS / region_id / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    (gen_dir / "far_field_qa.json").write_text(
        json.dumps(qa_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    wm_path = gen_dir / "world_manifest.json"
    if wm_path.exists():
        wm = json.loads(wm_path.read_text(encoding="utf-8"))
        wm.setdefault("materials", {})["far_field_buildings"] = SM.M["far_field_buildings"]
        wm["far_field"] = qa_tiers
        wm_text = json.dumps(wm, ensure_ascii=False, indent=1, sort_keys=True, allow_nan=False) + "\n"
        if wm_path.read_text(encoding="utf-8") != wm_text:
            wm_path.write_text(wm_text, encoding="utf-8", newline="\n")
    return qa_report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", default="bialystok-industrial-c")
    args = ap.parse_args()
    qa = build_far_field(args.region)
    print(json.dumps(qa, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
