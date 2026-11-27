"""Far-field backdrop generator beyond the 2x2 km region tile (ADR 0085).

Extracts real open GIS data in a ~1-4.5 km ring outside the region bbox:
  - BDOT10k of EVERY powiat the ring bbox overlaps (ADR 0219, `powiaty.powiaty_for_bbox`; was powiat 2061 only):
    OT_PTLZ_A (forests), OT_BUBD_A (buildings), OT_BUWT_P (chimneys, HV pylons, towers), OT_SULN_L (HV lines)
  - GUGiK LoD1 2024 of the same powiaty (<teryt>_lod1_2024.zip): measuredHeight per buildingId
  - OpenStreetMap (podlaskie-261108.osm.pbf): forests, landuse, buildings, chimneys, power lines and towers in the
    lon/lat window of the ring (ADR 0219; was a fixed Białystok window, empty for Knyszyn / Mońki / Tykocin)

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
from roads import profile as RP           # noqa: E402
from terrain_mesh.gltf import GLB, GLTF_AXES  # noqa: E402

import powiaty as PW                       # noqa: E402  (ADR 0219)
from streetscape import forest_chm as FC   # noqa: E402  (ADR 0339 / 0330 addendum)
from streetscape import forest_hlod as FH  # noqa: E402
from streetscape import materials as SM    # noqa: E402

REPO = pipeline.REPO
RING_MAX_M = 4200.0
APRON_EASE_M = 600.0
FORESHORTEN_FREE_M = 140.0
FORESHORTEN_SPAN_M = 520.0
FORESHORTEN_TAU_M = 950.0
# WORKING_VALUE: StreamingSettings defaults: 25 m/s * (8 + 1 + 1) s + 150 m.
# Static exclusion is independent of scene availability, load timing and memory budget.
STREAMING_ROUTE_CLEARANCE_M = 400.0

SECTORS = ("far_north", "far_east", "far_south", "far_west")
# ADR 0330 + addendum (neon-farfield-s24): the ring is foreshortened into <= ~660 m beyond the border.
# True Beer-Lambert extinction over the missing distance (d_true - d_eff) is evaluated per vertex in Kamion/Vegetation
# (_HLOD_EDGE, TEXCOORD_1.x = d_extra) and Kamion/World Surface (_FAR_FACADE, inverse foreshortening) using the exact
# same _KamionHaze parameters as terrain and sky (ADR 0332) for every lighting preset (Clear, Overcast, Dusk, Night).
# The far atlas (forest_hlod.far_atlas) supplies a cool bluish-grey Rayleigh tint across distance bands and lifted sky
# visibility (B channel of _n.png) so distant crowns receive sky SH instead of close-range trunk occlusion. WORKING_VALUE.
HAZE_BETA = 3.912 / 20000.0        # 1/m: Koschmieder for the clear preset's 20 km visibility (LightingPreset)
HAZE_ALBEDO = FH.HAZE_ALBEDO       # (0.20, 0.30, 0.46) cool bluish-grey Rayleigh target (linear)
# curtain material bands by the stand's true distance outside the border: suffix in forest_edge_mixed_far_atlas
HAZE_BANDS = ((0.0, ""), (900.0, "_haze1"), (2000.0, "_haze2"))
MOUND_COL = {"conifer": (0.032, 0.050, 0.030), "mixed": (0.038, 0.058, 0.034), "broadleaf": (0.048, 0.068, 0.038)}
# ADR 0330 addendum (WORKING_VALUE): vertical normal tilt on far-field curtains (bottom, top), as CHM_NORMAL_UP in
# ADR 0339 r2 — distant crown tops take sky SH and sun from above instead of reading as dark vertical walls in shade.
CURTAIN_NORMAL_UP = (0.65, 1.65)
# Base curtain quad height [m] outside the 24 CHM tiles (with CHM_WALL_TOP_FRAC 0.888/0.833/0.766 -> ~18.2/16.2/14.2 m
# median crowns before multi-scale age/clump noise; matches Podlasie CHM median without inflating into 40 m peaks). WORKING_VALUE.
FAR_BASE_H_M = {"conifer": 20.5, "mixed": 19.5, "broadleaf": 18.5}
# ADR 0330 r2 (neon-farfield2-s24): realistic Podlasie crown-top cap [m] (aligned with vegetation.chm_cap_m) so single
# noisy CHM cells or stand multipliers never produce 40 m conical hills on flat terrain. WORKING_VALUE.
FAR_CROWN_CAP_M = {"conifer": 25.5, "mixed": 24.0, "broadleaf": 22.5}
# Max top-edge slope |dz_top / ds| along a curtain strip (~14.5 deg): prevents conical peaks AND trapezoidal UV shear
# (diagonal painterly streaks in crop-1to1-clear). WORKING_VALUE.
FAR_MAX_TOP_SLOPE = 0.26
# High-tier irregular forest base (ADR 0330 r2): horizontal outline wobble [m], undergrowth mantle skirt & individual
# crossed-card edge tree impostors (packed in forest_edge_mixed_far_atlas -> 0 extra draw calls). WORKING_VALUE.
FAR_EDGE_WOBBLE_M = 5.0
FAR_SKIRT_MAX_D_M = 2200.0
LOW_HV_MAX_D_M = 2000.0   # wave 12: Low draws HV towers/spans up to 2.0 km (was 2.2 km) - keeps C Low <= 30k tris with 3 lacing panels
FAR_IMPOSTOR_MAX_D_M = 1500.0
# ADR 0334 r4 (fields4-s24, critic s24 wave 11 pt 10 "prosta krawędź lasu w tle"): the far stand edge read as one
# smooth band - the +-30 % crown wave is rounded off by the slope limit, the curtain ends at full height where the
# outline turns away, and nothing stands above the canopy. Now (High tier): compartments of another age - the height
# steps by 0.62-1.12 x on 70-160 m pieces of the edge (FAR_COMPARTMENT_*; measured CHM heights are left alone), single
# overstorey trees stand 1.12-1.35 x above the curtain top every FAR_EMERGENT_STEP_M, and an open run end rolls off to
# FAR_END_FLOOR over FAR_END_TAPER_M with trees stepping down past it. WORKING_VALUE (render review, edge-* cameras).
FAR_COMPARTMENT_M = 115.0
FAR_COMPARTMENT_H = (0.62, 1.12)
FAR_EMERGENT_STEP_M = (38.0, 70.0)
FAR_EMERGENT_H = (1.12, 1.35)
FAR_END_FLOOR = 0.30
FAR_END_TAPER_M = 26.0
FAR_IMPOSTOR_SPECIES = {
    "conifer": ("tree_pine_0", "tree_pine_1", "tree_spruce_0", "tree_spruce_1", "tree_birch_0", "tree_shrub_0"),
    "broadleaf": ("tree_birch_0", "tree_alder_0", "tree_linden_0", "tree_shrub_0", "tree_shrub_0"),
    "mixed": ("tree_pine_0", "tree_spruce_0", "tree_birch_0", "tree_alder_0", "tree_linden_0", "tree_shrub_0"),
}
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
GIS_CACHE_SCHEMA = "far-field-gis-cache/14"   # 14: power lines as {pts, hv, mv, src, id}, HV/MV clipped at the tile edge (0351)
#                                                12: BDOT10k / LoD1 of every ring powiat, ring OSM window (0219)
BDOT_LAYERS = ("OT_PTLZ_A", "OT_BUBD_A", "OT_BUWT_P", "OT_SULN_L")
OSM_WINDOW_MARGIN_DEG = (0.08, 0.05)   # lon, lat (~5.3 / 5.6 km): a feature is tested by its FIRST node, so the window
#                                        reaches past the ring; for C it contains the old fixed window 23.08-23.30 E,
#                                        53.10-53.24 N (test_qa_tools_0219), i.e. nothing C read before is dropped

def _material_palette(*names: str) -> list[tuple]:
    """Same linear albedos as real tile envelopes; keep hash selection order stable."""
    return [tuple(SM.M[name]["color"][:3]) for name in names]


PALETTE_BLOCK = _material_palette(
    "plaster_cream", "plaster_yellow", "plaster_peach", "plaster_sage",
    "plaster_light", "plaster_grey", "plaster_pastel_blue", "panel_concrete")
PALETTE_BLOCK_GABLE = _material_palette(
    "plaster_accent_terracotta", "plaster_accent_ochre", "plaster_accent_green", "plaster_accent_grey")
PALETTE_HALL = _material_palette(
    "hall_wall_silver", "hall_wall_grey", "hall_wall_white", "hall_wall_ivory", "hall_wall_graphite")
PALETTE_HALL_ACCENT = [
    (0.06, 0.12, 0.21),  # blue fascia
    (0.24, 0.05, 0.04),  # red fascia
    (0.05, 0.14, 0.09),  # green fascia
    (0.09, 0.095, 0.10), # graphite fascia
    (0.44, 0.24, 0.04),  # amber/orange fascia
]
PALETTE_OFFICE = _material_palette("plaster_light", "plaster_grey", "plaster_beige", "plaster_white", "brick_red")
PALETTE_HOUSE = _material_palette("plaster_light", "plaster_beige", "plaster_cream", "plaster_grey")
PALETTE_ROOF_PITCHED = _material_palette("roof_tiles_red", "roof_tiles_brown", "roof_metal_graphite")
COL_PLINTH = (0.17, 0.165, 0.155)
COL_ROOF_FLAT = tuple(SM.M["roof_membrane"]["color"][:3])
COL_PARAPET = (0.20, 0.205, 0.21)
COL_CHIMNEY_CONCRETE = (0.37, 0.36, 0.34)
COL_CHIMNEY_BRICK = (0.23, 0.09, 0.06)
COL_CHIMNEY_RED = (0.38, 0.045, 0.035)
COL_CHIMNEY_WHITE = (0.62, 0.62, 0.60)


def _sha256(path: Path) -> str:
    if path.suffix.lower() in (".json", ".geojson", ".yaml", ".yml", ".py"):
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


def unforeshorten_dist(deff):
    """Inverse of foreshorten_dist (array or scalar); d_eff at / beyond the asymptote maps to RING_MAX_M."""
    deff = np.asarray(deff, dtype=np.float64)
    x = np.clip((deff - FORESHORTEN_FREE_M) / FORESHORTEN_SPAN_M, 0.0, 1.0 - 1e-9)
    d = FORESHORTEN_FREE_M - FORESHORTEN_TAU_M * np.log(1.0 - x)
    return np.where(deff <= FORESHORTEN_FREE_M, deff, np.minimum(d, RING_MAX_M))


def unforeshorten_xy(e_eff, n_eff, half: float = 1024.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Inverse of foreshorten_point for arrays: returns (e_raw, n_raw, d_true)."""
    e = np.asarray(e_eff, dtype=np.float64)
    n = np.asarray(n_eff, dtype=np.float64)
    eb = np.clip(e, -half, half)
    nb = np.clip(n, -half, half)
    de = e - eb
    dn = n - nb
    deff = np.hypot(de, dn)
    dtrue = unforeshorten_dist(deff)
    scale = np.where(deff > 1e-6, dtrue / np.maximum(deff, 1e-6), 1.0)
    return eb + de * scale, nb + dn * scale, dtrue


def extra_dist_eff(e, n, half: float = 1024.0) -> np.ndarray:
    """ADR 0330 addendum: missing optical path (d_true - d_eff) [m] for foreshortened positions (arrays)."""
    e = np.asarray(e, dtype=np.float64)
    n = np.asarray(n, dtype=np.float64)
    de = e - np.clip(e, -half, half)
    dn = n - np.clip(n, -half, half)
    deff = np.hypot(de, dn)
    return np.maximum(unforeshorten_dist(deff) - deff, 0.0)


def haze_share_eff(e, n, half: float = 1024.0):
    """ADR 0330: haze share k of the extra (true - rendered) distance for foreshortened positions (arrays)."""
    return 1.0 - np.exp(-HAZE_BETA * extra_dist_eff(e, n, half))


def haze_band(d_true: float) -> str:
    """Curtain material suffix of a stand at true distance d_true outside the border (ADR 0330)."""
    suf = ""
    for d0, sx in HAZE_BANDS:
        if d_true >= d0:
            suf = sx
    return suf


def strip_curtain_mat(stand_mat: str, pts_eff: np.ndarray, half: float = 1024.0) -> str:
    """far-forest-look-s24 (ADR 0330 addendum 3): haze band of ONE curtain strip by its own median true distance.
    A stand was banded by its centroid only, so the 3-4 km back edge of a stand reaching to the border kept the near
    ("") slot - sharp orange trunks and full-contrast crowns at true kilometres. All bands are slots of the same far atlas
    and submesh, so per-strip banding costs no draw call, vertex or texture. Mix stays the stand's."""
    if not stand_mat.startswith("forest_edge_") or len(pts_eff) == 0:
        return stand_mat
    rest = stand_mat[len("forest_edge_"):]
    mix = rest.split("_", 1)[0]
    _, _, d_true = unforeshorten_xy(pts_eff[:, 0], pts_eff[:, 1], half)
    return f"forest_edge_{mix}{haze_band(float(np.median(d_true)))}"


class RingChm:
    """ADR 0330 addendum / ADR 0339: canopy height models (forest_chm.png) of neighbouring tiles overlapping the
    far-field ring (the 24 route tiles with committed CHMs). Deterministic, zero network, opt-in by existing files."""

    def __init__(self, entries: list[tuple[str, FC.Chm]]):
        self.entries = entries
        self.tiles = [cid for cid, _ in entries]
        self.n_chm_verts = 0
        self.n_total_verts = 0

    @classmethod
    def for_region(cls, region_id: str, ox: float, oy: float, ring_max_m: float = RING_MAX_M,
                   root: Path | None = None) -> "RingChm":
        from regions import REGIONS
        rbox = (ox - ring_max_m, oy - ring_max_m, ox + ring_max_m, oy + ring_max_m)
        entries = []
        for cid, reg in sorted(REGIONS.items()):
            if cid == region_id:
                continue
            x0, y0, x1, y1 = reg.bbox
            if x1 <= rbox[0] or x0 >= rbox[2] or y1 <= rbox[1] or y0 >= rbox[3]:
                continue
            chm = FC.load(cid, (ox, oy), root=root)
            if chm is not None:
                entries.append((cid, chm))
        return cls(entries)

    def sample_heights(self, e_raw: np.ndarray, n_raw: np.ndarray, mix: str) -> tuple[np.ndarray, np.ndarray]:
        """Return (h_quad_raw [m], has_chm [bool]) at true ring coordinates (e_raw, n_raw)."""
        k = len(e_raw)
        h_out = np.zeros(k, dtype=np.float64)
        has = np.zeros(k, dtype=bool)
        if not self.entries or k == 0:
            return h_out, has
        P = np.column_stack([e_raw, n_raw])
        top_frac = FH.CHM_WALL_TOP_FRAC.get(mix, 0.833)
        cap_m = FAR_CROWN_CAP_M.get(mix, 24.0)
        for _, chm in self.entries:
            top, dom, ins = chm.cell_top(P)
            if not ins.any():
                continue
            _, stand, _, _ = chm.sample(P)
            ok = ins & (~has) & (dom >= FH.CHM_TRUST_M)
            if ok.any():
                # ADR 0330 r2: 0.62*dom (was 0.78) preserves real +-30% CHM crown dips while capping LIDAR outliers
                h_crown = np.clip(np.maximum(top[ok], 0.62 * dom[ok]), 4.5, cap_m)
                h_out[ok] = h_crown / top_frac
                has[ok] = True
            edge_ok = ins & (~has) & (stand >= FH.CHM_TRUST_M)
            if edge_ok.any():
                h_crown = np.clip(0.55 * stand[edge_ok], 4.5, cap_m)
                h_out[edge_ok] = h_crown / top_frac
                has[edge_ok] = True
        return h_out, has

    def stats(self) -> dict:
        return {
            "chm_tiles": list(self.tiles),
            "chm_vertices": int(self.n_chm_verts),
            "total_curtain_vertices": int(self.n_total_verts),
            "chm_share": round(self.n_chm_verts / max(self.n_total_verts, 1), 4),
        }


def _stand_rng(coords) -> np.random.Generator:
    """Deterministic per-stand generator (first vertex, rounded) - variation that survives a rebuild."""
    c = np.round(np.asarray(coords, dtype=np.float64)[0], 0)
    h = hashlib.sha1(f"{c[0]:.0f},{c[1]:.0f}".encode()).hexdigest()
    return np.random.default_rng(int(h[:12], 16))


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


def sector_regions(half: float = 1024.0) -> dict:
    """The four sectors of sector_of() as polygons (outside the tile; same partition, edges shared)."""
    B = 1.0e6
    return {"far_north": box(-half - 320.0, half, B, B),
            "far_east": box(half, -B, B, half),
            "far_south": box(-B, -B, half, -half),
            "far_west": shapely.union_all([box(-B, -half, -half, half), box(-B, half, -half - 320.0, B)])}


def split_by_sector(poly, half: float = 1024.0, min_area: float = 60.0) -> list:
    """[(sector name, polygon)]: poly cut along the sector borders (ADR 0308). A stand used to go whole to the sector
    of its centroid: a forest wrapping a tile corner was drawn with the east sector although half of it lay north of
    the tile - inside the neighbour tile whose open seam hides only the NORTH sector. Its mounds and curtains then
    stood in the driven tile (owner s24, DK65 km 19.5; drive review s24 # 1, 2, 4, 5, 6)."""
    out = []
    for name, reg in sector_regions(half).items():
        piece = shapely.make_valid(poly.intersection(reg))
        for g in getattr(piece, "geoms", [piece]):
            if g.geom_type == "Polygon" and g.area >= min_area:
                out.append((name, g))
    return out


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
    def from_region(cls, region_id: str, half: float = 1024.0, step_m: float = 16.0,
                    out_root: Path | None = None) -> "BorderElevation":
        world = Path(out_root) if out_root is not None else REPO / "Data" / "raw" / "derived" / region_id / "world"
        npy = world / "terrain_conformed.npy"
        if npy.exists():
            zc = np.load(npy)
        else:
            tm = json.loads((pipeline.REGIONS / region_id / "terrain.json").read_text(encoding="utf-8"))
            zc = RP.load_heightfield(tm, REPO, (0.0, 0.0)).z

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


def streaming_building_exclusion(ox: float, oy: float) -> tuple[shapely.Geometry, dict]:
    """Reserve real tiles and driving corridors in both source and render space.

    Registered tiles own their buildings even before import/loading. Routes are in
    each tile's local XZ coordinates; translate to this backdrop's local EN frame.
    Apply at mesh generation, after the GIS cache, so route/registry edits take
    effect without re-extracting BDOT/OSM. Never infer a corridor from fixed C exits.
    """
    from regions import REGIONS

    parts = []
    inputs = {}
    registry = REPO / "tools/worldgen/regions.py"
    if registry.exists():
        inputs["tools/worldgen/regions.py"] = _sha256(registry)
    for region_id, reg in sorted(REGIONS.items()):
        x0, y0, x1, y1 = reg.bbox
        parts.append(box(x0 - ox, y0 - oy, x1 - ox, y1 - oy))
        route_path = REPO / "Data/Regions" / region_id / "route_start.json"
        if not route_path.exists():
            continue  # Planned tiles still reserve their complete bbox.
        route = json.loads(route_path.read_text(encoding="utf-8"))
        points = route["points_en"]
        if len(points) < 2:
            raise ValueError(f"{route_path}: route needs at least two points")
        dx, dy = reg.origin[0] - ox, reg.origin[1] - oy
        line = LineString([(float(e) + dx, float(n) + dy) for e, n in points])
        # GEOS round buffers are inscribed polygons. Inflate by the chord error
        # so even a footprint near a cap/join cannot enter the promised 400 m.
        segments = 16
        radius = STREAMING_ROUTE_CLEARANCE_M / math.cos(math.pi / (4 * segments))
        parts.append(line.buffer(radius, quad_segs=segments))
        inputs[route_path.relative_to(REPO).as_posix()] = _sha256(route_path)
    exclusion = shapely.union_all(parts)
    shapely.prepare(exclusion)
    return exclusion, inputs


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


def _bdot_layer_file(teryt: str, layer: str) -> Path | None:
    """Extracted BDOT10k GeoPackage of one layer of one powiat (Data/raw/gugik/bdot10k-<t>/gpkg/...<t>__<layer>.gpkg),
    extracted from the manifest's ZIP on first use; None when the powiat ships no file for the layer (ADR 0204) or
    the package is not on disk."""
    gdir = REPO / "Data" / "raw" / "gugik" / f"bdot10k-{teryt}" / "gpkg"
    hit = sorted(gdir.glob(f"*BDOT10k.{teryt}__{layer}.gpkg")) if gdir.exists() else []
    if hit:
        return hit[0]
    zips = PW.package_files("bdot10k", teryt) or []
    if not zips or not zips[0].exists():
        return None
    import zipfile as _zf
    with _zf.ZipFile(zips[0]) as zf:
        name = next((n for n in zf.namelist() if n.endswith(f"__{layer}.gpkg")), None)
        if name is None:
            return None
        dest = gdir / Path(name).name
        if not dest.exists():
            gdir.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(name))
    return dest


def ring_sources(ox: float, oy: float) -> dict:
    """ADR 0219: per-powiat BDOT10k layer files and LoD1 ZIPs for the ring bbox, plus what is missing on disk."""
    ring_powiaty = PW.powiaty_for_bbox(PW.ring_bbox((ox, oy), RING_MAX_M))
    bdot = {layer: [] for layer in BDOT_LAYERS}
    lod1, missing = [], []
    for t in ring_powiaty:
        files = {layer: _bdot_layer_file(t, layer) for layer in BDOT_LAYERS}
        if not any(files.values()):
            missing.append(f"bdot10k-{t}")
        for layer, f in files.items():
            if f is not None:
                bdot[layer].append(f)
        lz = PW.package_files("lod1-2024", t)
        if not lz or not lz[0].exists():
            missing.append(f"lod1-2024-{t}")
        else:
            lod1.append(lz[0])
    return {"powiaty": list(ring_powiaty), "bdot": bdot, "lod1": lod1, "missing": missing}


def _read_bdot(pyogrio, files: list, bbox):
    """One dataframe over the ring powiaty: the first powiat's rows as before, later powiaty append only objects
    whose LOKALNYID is new (a feature on a powiat boundary can be in both packages)."""
    if not files:
        return None
    dfs = [pyogrio.read_dataframe(f, bbox=bbox) for f in files]
    if len(dfs) == 1:
        return dfs[0]
    import pandas as pd
    col = lambda df: "LOKALNYID" if "LOKALNYID" in df.columns else ("lokalnyId" if "lokalnyId" in df.columns else None)
    out = [dfs[0]]
    seen = set(dfs[0][col(dfs[0])].astype(str)) if col(dfs[0]) else set()
    for df in dfs[1:]:
        c = col(df)
        if c is not None:
            df = df[~df[c].astype(str).isin(seen)]
            seen |= set(df[c].astype(str))
        out.append(df)
    return pd.concat(out, ignore_index=True)


def osm_lonlat_window(ox: float, oy: float) -> tuple[float, float, float, float]:
    """(lon0, lat0, lon1, lat1) of the ring bbox + OSM_WINDOW_MARGIN_DEG (ADR 0219)."""
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = PW.ring_bbox((ox, oy), RING_MAX_M)
    lon, lat = tr.transform([x0, x1, x0, x1], [y0, y0, y1, y1])
    mx, my = OSM_WINDOW_MARGIN_DEG
    return (round(min(lon) - mx, 4), round(min(lat) - my, 4), round(max(lon) + mx, 4), round(max(lat) + my, 4))


def _merge_lod1(zips: list, audit: dict) -> dict[str, float]:
    """LoD1 heights of every ring powiat; a buildingId already read from an earlier powiat keeps its height."""
    heights: dict[str, float] = {}
    for z in zips:
        a = {}
        h = _extract_lod1_heights(z, a)
        for k, v in h.items():
            heights.setdefault(k, v)
        for k, v in a.items():
            audit[k] = audit.get(k, 0) + v
    if len(zips) > 1:
        audit["usable_ids"] = len(heights)
    return heights


def extract_ring_gis(region_id: str, ox: float, oy: float, half: float = 1024.0) -> dict:
    """Extract and cache real ring features from BDOT10k (gpkg), GUGiK LoD1 2024 (every ring powiat, ADR 0219) and
    OSM PBF."""
    import pyogrio

    osm_pbf = REPO / "Data" / "raw" / "osm" / "podlaskie-261108.osm.pbf"
    src = ring_sources(ox, oy)
    bdot_files = src["bdot"]
    sources_sha = {}
    for layer in BDOT_LAYERS:
        for p in bdot_files[layer]:
            sources_sha[f"bdot10k/{p.name}"] = _sha256(p)
    for z in src["lod1"]:
        sources_sha[f"lod1/{z.name}"] = _sha256(z)
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
                    and cached.get("ring_max_m") == RING_MAX_M
                    and cached.get("powiaty") == src["powiaty"]):
                return cached
        except Exception:
            pass

    t0 = time.time()
    inner_box = box(-half - 8.0, -half - 8.0, half + 8.0, half + 8.0)
    outer_box = box(-RING_MAX_M, -RING_MAX_M, RING_MAX_M, RING_MAX_M)
    ring_zone = outer_box.difference(inner_box)
    forest_ring_zone = ring_zone.difference(_road_exit_corridors(half))
    power_zone = outer_box.difference(box(-half, -half, half, half))   # ADR 0351: HV lines, exact tile edge
    shapely.prepare(ring_zone)
    shapely.prepare(forest_ring_zone)
    shapely.prepare(power_zone)
    bbox_2180 = (ox - RING_MAX_M, oy - RING_MAX_M, ox + RING_MAX_M, oy + RING_MAX_M)

    lod1_audit = {}
    lod1_h = _merge_lod1(src["lod1"], lod1_audit)
    lon0, lat0, lon1, lat1 = osm_lonlat_window(ox, oy)

    forests = []
    buildings = []
    building_exclusion = region_building_exclusion(region_id, ox, oy, half)
    boundary_exclusions = {"bdot_source": 0, "bdot_rectangle": 0,
                           "osm_source": 0, "osm_rectangle": 0}
    chimneys = []
    pylons = []
    power_lines = []

    # 1. BDOT10k OT_PTLZ_A (forests)
    df = _read_bdot(pyogrio, bdot_files["OT_PTLZ_A"], bbox_2180)
    if df is not None:
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
    df = _read_bdot(pyogrio, bdot_files["OT_BUBD_A"], bbox_2180)
    if df is not None:
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
    df = _read_bdot(pyogrio, bdot_files["OT_BUWT_P"], bbox_2180)
    if df is not None:
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

    # 4. BDOT10k OT_SULN_L (overhead power lines). ADR 0351: the voltage class is kept (only HV lines get lattice
    # towers and conductors in the ring) and a HV line is clipped at the tile edge itself, not at the 8 m margin:
    # its piece then starts on the same seam point where the tile hangs its last span (streetscape.furniture
    # power_supports puts a support on the clipped end of the tile's own copy of the line).
    df = _read_bdot(pyogrio, bdot_files["OT_SULN_L"], bbox_2180)
    if df is not None:
        for _, row in df.iterrows():
            geom = shapely.affinity.translate(row.geometry, xoff=-ox, yoff=-oy)
            kind = str(row.get("RODZAJ") or row.get("rodzaj") or "")
            hv = "wysokiego" in kind
            mv = "średniego" in kind
            zone = power_zone if (hv or mv) else ring_zone
            if not zone.intersects(geom):
                continue
            clipped = shapely.intersection(geom, zone)
            lid = str(row.get("LOKALNYID") or row.get("lokalnyId") or "").strip()
            for g in getattr(clipped, "geoms", [clipped]):
                if g.geom_type == "LineString" and g.length >= 60.0:
                    power_lines.append({"pts": np.round(np.asarray(g.coords), 3).tolist(), "hv": hv, "mv": mv,
                                        "src": "bdot10k", "id": lid})

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
                if not (lon0 <= n.location.lon <= lon1 and lat0 <= n.location.lat <= lat1):
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
                # ADR 0351: voltage class (OSM voltage=* in V, ";" between circuits). power=line without voltage is
                # undecided (None): power_plan() keeps it as HV only where >= 2 mapped towers stand on it.
                volts = []
                for v in str(tags.get("voltage", "")).replace(",", ";").split(";"):
                    try:
                        volts.append(float(v.strip()))
                    except ValueError:
                        pass
                hv = False if tags.get("power") == "minor_line" else (max(volts) >= 60000.0 if volts else None)
                mv = hv is False and tags.get("power") == "line" and bool(volts) and 1000.0 <= max(volts) < 60000.0
                try:
                    lonlat = [(nd.lon, nd.lat) for nd in w.nodes if nd.location.valid()]
                except Exception:
                    return
                if len(lonlat) < 2:
                    return
                f_lon, f_lat = lonlat[0]
                if not (lon0 <= f_lon <= lon1 and lat0 <= f_lat <= lat1):
                    return
                lons, lats = zip(*lonlat)
                xs, ys = tr.transform(lons, lats)
                pts = np.column_stack([np.asarray(xs) - ox, np.asarray(ys) - oy])
                ls = LineString(pts)
                zone = ring_zone if (hv is False and not mv) else power_zone
                if not zone.intersects(ls):
                    return
                clipped = shapely.intersection(ls, zone)
                for g in getattr(clipped, "geoms", [clipped]):
                    if g.geom_type == "LineString" and g.length >= 60.0:
                        power_lines.append({"pts": np.round(np.asarray(g.coords), 3).tolist(), "hv": hv, "mv": mv,
                                            "src": "osm", "id": f"osm_w{w.id}"})

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
                f_lon, f_lat = lonlat[0]
                if not (lon0 <= f_lon <= lon1 and lat0 <= f_lat <= lat1):
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
        "powiaty": src["powiaty"],
        "powiaty_missing": src["missing"],
        "osm_lonlat_window": [lon0, lat0, lon1, lat1],
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
        self.v1, self.n1, self.uv1, self.uv1_1, self.t1 = [], [], [], [], []
        self.count1 = 0
        self.mat1 = []         # ADR 0330: curtain material per strip (forest_edge_<mix><haze band>)

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

    def add_curtain1(self, pts_xy: np.ndarray, z_bot: np.ndarray, z_top: np.ndarray, face_sign: float = 1.0, u_scale: float = 48.0,
                     mat: str = "forest_edge_mixed", u_shift: float = 0.0, half: float = 1024.0,
                     v_bot: float = 0.0, v_top: float | None = None):
        """Add an alpha-tested forest_edge_<mix> curtain strip along pts_xy (ADR 0330 + r2: material slot per stand /
        haze band, height-proportional u_scale so distant trees keep natural proportions without horizontal smear,
        optional mantle skirt v_bot=1.0->v_main, sky-tilted normals, TEXCOORD_1.x = d_extra for KamionFogTauExtra)."""
        k = len(pts_xy)
        if k < 2:
            return
        ds = np.hypot(*np.diff(pts_xy, axis=0).T)
        s = np.concatenate([[0.0], np.cumsum(ds)])
        ht_med = float(np.median(np.maximum(z_top - z_bot, 1.0)))
        if v_bot > 0.5:
            # Undergrowth mantle strip (baked 8 m high across 48 m width)
            u_eff = u_scale * float(np.clip(ht_med / 8.0, 0.45, 1.15))
        else:
            # Main forest wall (baked ~21 m high across 48 m width): scale u proportionally to local curtain height
            u_eff = u_scale * float(np.clip(ht_med / 21.0, 0.38, 1.20))
        u0 = ((pts_xy[0, 0] + pts_xy[0, 1]) % max(u_eff, 1.0)) / max(u_eff, 1.0) + u_shift
        us = u0 + s / max(u_eff, 1.0)

        # Outward normal in XY with bottom->top upward tilt (CURTAIN_NORMAL_UP): crown tops take sky SH & sun from above
        tang = np.zeros((k, 2), dtype=np.float64)
        tang[:-1] += np.diff(pts_xy, axis=0)
        tang[1:] += np.diff(pts_xy, axis=0)
        nxy = np.column_stack([tang[:, 1], -tang[:, 0]]) * face_sign
        ln = np.maximum(np.hypot(nxy[:, 0], nxy[:, 1]), 1e-9)
        nxy /= ln[:, None]
        n3b = np.column_stack([nxy, np.full(k, CURTAIN_NORMAL_UP[0])])
        n3b /= np.linalg.norm(n3b, axis=1)[:, None]
        n3t = np.column_stack([nxy, np.full(k, CURTAIN_NORMAL_UP[1])])
        n3t /= np.linalg.norm(n3t, axis=1)[:, None]

        v_bot_arr = np.column_stack([pts_xy[:, 0], pts_xy[:, 1], z_bot])
        v_top_arr = np.column_stack([pts_xy[:, 0], pts_xy[:, 1], z_top])
        V = np.vstack([v_bot_arr, v_top_arr])
        N = np.vstack([n3b, n3t])
        vt = FH.edge_v_main(FH.bake_info()["mixed"]["edge"]) if v_top is None else float(v_top)
        uv_bot = np.column_stack([us, np.full(k, float(v_bot))])
        uv_top = np.column_stack([us, np.full(k, vt)])
        UV = np.vstack([uv_bot, uv_top])
        # ADR 0330 addendum: extra foreshortened distance [m] in TEXCOORD_1.x for shader KamionFogTauExtra
        d_extra = extra_dist_eff(pts_xy[:, 0], pts_xy[:, 1], half)
        # far-forest-look-s24 (ADR 0330 addendum 3): TEXCOORD_1.y = column height [m], the same on the bottom and top
        # vertex of a column. Kamion/Vegetation (_HLOD_EDGE) interpolates (v * H, H) and divides per pixel, so v follows
        # the column height linearly whatever the quad's triangle split: no diagonal crease / sheared crowns where
        # neighbouring columns differ in height (affine v in two triangles of a trapezoid). 0 = plain v (old data).
        col_h = np.maximum(np.asarray(z_top, dtype=np.float64) - np.asarray(z_bot, dtype=np.float64), 0.05)
        uv1_row = np.column_stack([d_extra, col_h])
        UV1 = np.vstack([uv1_row, uv1_row])

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
        self.uv1_1.append(UV1)
        self.t1.append(np.asarray(tris, dtype=np.int64))
        self.mat1.append(mat)
        self.count1 += 2 * k

    def add_tree_impostor1(self, e: float, n: float, z_bot: float, h_m: float, tree_name: str,
                           yaw: float = 0.0, half: float = 1024.0):
        """ADR 0330 r2: crossed two-quad (+) individual tree impostor packed into the same far atlas submesh
        (0 extra draw calls, 4 tris per tree, true-distance KamionFogTauExtra via TEXCOORD_1.x)."""
        u0, v0, u1, v1, aspect, top_frac = FH.far_impostor_uv(tree_name)
        h_quad = max(float(h_m), 2.0) / max(top_frac, 0.35)
        hw = 0.5 * h_quad * aspect
        z0 = float(z_bot) - 0.35
        z1 = z0 + h_quad
        d_ex = float(extra_dist_eff(np.array([e]), np.array([n]), half)[0])
        verts, norms, uvs, tris = [], [], [], []
        base = self.count1
        for qi, ang in enumerate((yaw, yaw + 0.5 * math.pi)):
            ca, sa = math.cos(ang), math.sin(ang)
            rx, ry = ca * hw, sa * hw
            nx, ny = -sa, ca
            nb = np.array([nx, ny, CURTAIN_NORMAL_UP[0]], dtype=np.float64)
            nb /= np.linalg.norm(nb)
            nt = np.array([nx, ny, CURTAIN_NORMAL_UP[1]], dtype=np.float64)
            nt /= np.linalg.norm(nt)
            verts.extend([
                [e - rx, n - ry, z0],
                [e + rx, n + ry, z0],
                [e + rx, n + ry, z1],
                [e - rx, n - ry, z1],
            ])
            norms.extend([nb, nb, nt, nt])
            uvs.extend([[u0, v0], [u1, v0], [u1, v1], [u0, v1]])
            b = base + qi * 4
            tris.extend([[b, b + 1, b + 2], [b, b + 2, b + 3]])
        self.v1.append(np.asarray(verts, dtype=np.float64))
        self.n1.append(np.asarray(norms, dtype=np.float64))
        self.uv1.append(np.asarray(uvs, dtype=np.float64))
        self.uv1_1.append(np.tile([d_ex, 0.0], (8, 1)))
        self.t1.append(np.asarray(tris, dtype=np.int64))
        self.mat1.append("__atlas_raw__")
        self.count1 += 8

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

    def primitives(self, half: float = 1024.0) -> list[dict]:
        prims = []
        if self.count0 > 0:
            V0 = np.vstack(self.v0)
            col = np.vstack(self.col0).copy()
            # ADR 0330 addendum: true-distance aerial perspective for far_field_buildings (mounds, buildings, chimneys)
            # is now applied per vertex in Kamion/World Surface (_FAR_FACADE -> KamionFogTauExtra), matching terrain & sky
            # across Clear, Overcast, LowSun, Dusk and Night without double-hazing or baking clear sky into overcast/night.
            prims.append({
                "mat": "far_field_buildings",
                "V": V0,
                "N": np.vstack(self.n0),
                "UV": np.vstack(self.uv0),
                "UV1": np.vstack(self.uv1_0),
                "COL": col,
                "T": np.vstack(self.t0),
            })
        if self.count1 > 0:
            # farfield-low-s24: ONE curtain primitive (<= 2 submeshes per sector on both tiers); the stand's mix and
            # haze band select a slot of the far atlas (forest_hlod.far_atlas) - v is squeezed into the slot
            base, tris, uvs = 0, [], []
            for i in range(len(self.v1)):
                tris.append(self.t1[i] - int(self.t1[i].min()) + base)
                base += len(self.v1[i])
                mat = self.mat1[i]
                uv = self.uv1[i].copy()
                if mat != "__atlas_raw__":
                    rest = mat[len("forest_edge_"):] if mat.startswith("forest_edge_") else "mixed"
                    mix, suf = (rest.split("_", 1) + [""])[:2]
                    v0, v1 = FH.far_atlas_slot_v(mix, f"_{suf}" if suf else "")
                    uv[:, 1] = v0 + np.clip(uv[:, 1], 0.0, 1.0) * (v1 - v0)
                uvs.append(uv)
            prims.append({
                "mat": FH.FAR_ATLAS_MAT,
                "V": np.vstack(self.v1),
                "N": np.vstack(self.n1),
                "UV": np.vstack(uvs),
                "UV1": np.vstack(self.uv1_1),
                "T": np.vstack(tris),
            })
        return prims


# ------------------------------------------------------------------------------------------- feature meshing
def _corridor_taper(e: np.ndarray, n: np.ndarray, half: float = 1024.0,
                    region_id: str = "bialystok-industrial-c") -> np.ndarray:
    """Smoothly taper tree curtain height near the 4 Białystok-C road exit axes (ADR 0085).
    Other regions (e.g. knyszyn-w, dk65-05) must not receive C's hardcoded exit valleys (ADR 0330 r2)."""
    taper = np.ones_like(e, dtype=np.float64)
    if region_id != "bialystok-industrial-c":
        return taper
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


def _limit_top_slope(pts_xy: np.ndarray, z_bot: np.ndarray, ht: np.ndarray,
                     max_slope: float = FAR_MAX_TOP_SLOPE, min_h: float = 3.0) -> np.ndarray:
    """ADR 0330 r2: clamp |dz_top / ds| along a curtain strip so no vertex jump forms a conical peak or
    a sheared diagonal trapezoid (which caused diagonal painterly streaks at 1:1 in crop-1to1-clear)."""
    k = len(pts_xy)
    if k < 2:
        return np.maximum(ht, min_h)
    ds = np.hypot(*np.diff(pts_xy, axis=0).T)
    z_top = z_bot + np.maximum(ht, min_h)
    # Forward + backward envelope passes pull sudden spikes down gently without raising flat edges into peaks
    for _ in range(2):
        for i in range(k - 1):
            lim = max_slope * max(float(ds[i]), 0.5)
            if z_top[i + 1] > z_top[i] + lim:
                z_top[i + 1] = z_top[i] + lim
        for i in range(k - 2, -1, -1):
            lim = max_slope * max(float(ds[i]), 0.5)
            if z_top[i] > z_top[i + 1] + lim:
                z_top[i] = z_top[i + 1] + lim
    return np.maximum(z_top - z_bot, min_h)


def _crown_height_wave(e: np.ndarray, n: np.ndarray, h_base: float, half: float = 1024.0,
                       rng: np.random.Generator | None = None, mix: str = "mixed",
                       ring_chm: RingChm | None = None, height_mult: float = 1.0,
                       region_id: str = "bialystok-industrial-c") -> np.ndarray:
    """Irregular tree-crown silhouette along a far-field stand edge (ADR 0330 + r2).
    Where a neighbouring tile provides forest_chm.png (the 24 route tiles, ADR 0339), crown tops come from the
    measured canopy height model at the true unforeshortened coordinates (e_raw, n_raw), capped to Podlasie stand
    heights (FAR_CROWN_CAP_M) and NOT re-inflated by stand_scale. Elsewhere, smooth multi-scale deterministic value
    noise (~260 m compartments, ~70 m clumps, ~26 m crowns, +-30% variation) gives an organic skyline without
    single-vertex spikes that caused conical peaks and diagonal UV shear."""
    e = np.asarray(e, dtype=np.float64)
    n = np.asarray(n, dtype=np.float64)
    k = len(e)
    if k == 0:
        return np.zeros(0, dtype=np.float64)
    e_raw, n_raw, d_true = unforeshorten_xy(e, n, half)
    s_h = np.array([foreshorten_scales(float(d))[1] for d in d_true], dtype=np.float64)
    top_frac = FH.CHM_WALL_TOP_FRAC.get(mix, 0.833)
    cap_quad = FAR_CROWN_CAP_M.get(mix, 24.0) / top_frac

    # Smooth multi-scale deterministic value noise on true ring metres (+-30% organic variation, no jagged 9 m spikes)
    n_age = np.array([0.66 + 0.62 * FH._vnoise2(x, y, 260.0, "ff_age") for x, y in zip(e_raw, n_raw)], dtype=np.float64)
    n_clump = np.array([0.80 + 0.40 * FH._vnoise2(x, y, 70.0, "ff_clump") for x, y in zip(e_raw, n_raw)], dtype=np.float64)
    n_fine = np.array([0.88 + 0.24 * FH._vnoise2(x, y, 26.0, "ff_fine") for x, y in zip(e_raw, n_raw)], dtype=np.float64)
    w = n_age * n_clump * n_fine
    if rng is not None and k >= 3:
        r = rng.normal(0.0, 1.0, k)
        r = np.convolve(np.pad(r, 2, mode="edge"), np.array([0.1, 0.2, 0.4, 0.2, 0.1]), mode="valid")
        w = w + 0.10 * r / max(float(np.std(r)), 1e-6)
    h_cls = FAR_BASE_H_M.get(mix, 19.5)
    # ADR 0334 r4: compartments - a piecewise-constant factor per FAR_COMPARTMENT_M cell of a warped lattice (true
    # metres), so the canopy steps where the stand age changes instead of only waving
    wx = np.array([(FH._vnoise2(x, y, 180.0, "ff_cmpx") - 0.5) * 90.0 for x, y in zip(e_raw, n_raw)], dtype=np.float64)
    wy = np.array([(FH._vnoise2(x, y, 180.0, "ff_cmpy") - 0.5) * 90.0 for x, y in zip(e_raw, n_raw)], dtype=np.float64)
    cmp = np.array([FAR_COMPARTMENT_H[0] + (FAR_COMPARTMENT_H[1] - FAR_COMPARTMENT_H[0])
                    * _hfloat(f"{int(np.floor(x / FAR_COMPARTMENT_M))},{int(np.floor(y / FAR_COMPARTMENT_M))}", "ff_cmp")
                    for x, y in zip(e_raw + wx, n_raw + wy)], dtype=np.float64)
    h_noise_raw = np.minimum(h_cls * np.clip(w * cmp, 0.42, 1.32) * height_mult, cap_quad)

    if ring_chm is not None:
        h_chm_raw, has_chm = ring_chm.sample_heights(e_raw, n_raw, mix)
        ring_chm.n_total_verts += k
        ring_chm.n_chm_verts += int(has_chm.sum())
        if has_chm.any():
            # Measured CHM is already true stand height: apply only gentle local jitter, never stand_scale inflation
            jitter = np.array([0.94 + 0.12 * FH._vnoise2(x, y, 22.0, "ff_chm") for x, y in zip(e_raw, n_raw)], dtype=np.float64)
            h_chm_cap = np.minimum(h_chm_raw * jitter, cap_quad)
            h_raw = np.where(has_chm, h_chm_cap, h_noise_raw)
        else:
            h_raw = h_noise_raw
    else:
        h_raw = h_noise_raw

    ht = h_raw * s_h * _corridor_taper(e, n, half, region_id)
    return np.maximum(ht, 3.5 * s_h)


def _add_forest_stand(sectors: dict[str, SectorBuilder], coords: list, mix: str, elev: BorderElevation, half: float, tier: str,
                      ring_chm: RingChm | None = None, region_id: str = "bialystok-industrial-c"):
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

    _, s_h = foreshorten_scales(d_cen)
    rng = _stand_rng(coords)
    stand_scale = float(rng.uniform(0.86, 1.14))
    h_base = max(FAR_BASE_H_M.get(mix, 19.5) * s_h * stand_scale, 3.5 * s_h)
    mix_ = mix if mix in MOUND_COL else "mixed"
    band = haze_band(d_cen)
    # Cool mound tint subtly aligned with the curtain band (true extinction is done in Kamion/World Surface shader)
    k_mound = 0.06 if band == "" else (0.16 if band == "_haze1" else 0.26)
    mound_raw = tuple(float(c) * float(rng.uniform(0.88, 1.14)) for c in MOUND_COL[mix_])
    mound_col = tuple(mound_raw[i] * (1.0 - k_mound) + HAZE_ALBEDO[i] * k_mound for i in range(3))
    look = {"mat": f"forest_edge_{mix_}{band}", "u_shift": float(rng.uniform(0.0, 1.0)),
            "u_scale": float(rng.uniform(42.0, 54.0)), "rng": rng, "stand_scale": stand_scale,
            "mound": mound_col, "d_cen": d_cen}
    for name, part in split_by_sector(poly_eff, half):          # ADR 0308: every piece in the sector it lies in
        _stand_geometry(sectors[name], part, mix, elev, half, tier, h_base, look,
                        ring_chm=ring_chm, region_id=region_id)


def _stand_geometry(sec: SectorBuilder, poly_eff, mix: str, elev: BorderElevation, half: float, tier: str, h_base: float,
                    look: dict | None = None, ring_chm: RingChm | None = None,
                    region_id: str = "bialystok-industrial-c"):
    """Curtains, irregular undergrowth skirt, edge tree impostors and flat under-canopy shadow base of one stand
    piece (foreshortened coordinates) into sector builder sec (ADR 0330 + r2)."""
    look = look or {"mat": "forest_edge_mixed", "u_shift": 0.0, "u_scale": 48.0, "rng": None,
                    "stand_scale": 1.0, "mound": None, "d_cen": 500.0}
    curtain = {"mat": look["mat"], "u_shift": look["u_shift"], "u_scale": look["u_scale"], "half": half}
    stand_scale = float(look.get("stand_scale", 1.0))
    ce, cn = float(poly_eff.centroid.x), float(poly_eff.centroid.y)
    vm_edge = FH.edge_v_main(FH.bake_info()["mixed"]["edge"])

    seg_step = 9.0 if tier == "High" else 28.0
    ext = np.asarray(poly_eff.exterior.coords, dtype=np.float64)
    if not poly_eff.exterior.is_ccw:
        ext = ext[::-1]

    # 1. Outer stand-edge curtain: front-facing edges (dot(n_seg, -rad) >= 0.48) outside the 10.5 m border band.
    #    ADR 0330 r2: organic wavy outline, gentle smoothstep end roll-off (0.72, never a 0.30 cone), slope-limited
    #    tops (|dz/ds| <= 0.26 -> zero diagonal UV shear), patchy shrub mantle skirt, and individual edge tree impostors.
    run = []

    def _smooth_end_taper(s: np.ndarray, total_s: float) -> np.ndarray:
        taper_len = min(FAR_END_TAPER_M, total_s * 0.30)        # r4: 16 m / 0.52 left a vertical cut at the run end
        if taper_len < 1.0:
            return np.ones_like(s)
        t = np.minimum(np.clip(s / taper_len, 0.0, 1.0), np.clip((total_s - s) / taper_len, 0.0, 1.0))
        sm = np.sqrt(t * t * (3.0 - 2.0 * t))                    # a crown's rounded shoulder, not a cone
        return FAR_END_FLOOR + (1.0 - FAR_END_FLOOR) * sm

    def flush_run(r_pts):
        if len(r_pts) < 2:
            return
        P = np.asarray(r_pts, dtype=np.float64).copy()
        ds = np.hypot(*np.diff(P, axis=0).T)
        s = np.concatenate([[0.0], np.cumsum(ds)])
        total_s = float(s[-1])
        if total_s < 8.0:
            return
        k = len(P)
        # Outward unit normal along the run (CCW exterior -> right of travel is outward)
        tang = np.zeros((k, 2), dtype=np.float64)
        tang[:-1] += np.diff(P, axis=0)
        tang[1:] += np.diff(P, axis=0)
        out_n = np.column_stack([tang[:, 1], -tang[:, 0]])
        out_n /= np.maximum(np.hypot(out_n[:, 0], out_n[:, 1]), 1e-9)[:, None]

        # Organic horizontal outline wobble on High tier so long BDOT edges never read as ruler-straight lines
        e_raw, n_raw, d_true = unforeshorten_xy(P[:, 0], P[:, 1], half)
        s_xy_arr = np.array([foreshorten_scales(float(d))[0] for d in d_true], dtype=np.float64)
        s_h_arr = np.array([foreshorten_scales(float(d))[1] for d in d_true], dtype=np.float64)
        if tier == "High" and k >= 3:
            end_env = np.minimum(np.clip(s / 18.0, 0.0, 1.0), np.clip((total_s - s) / 18.0, 0.0, 1.0))
            wob = np.array([
                (2.0 * FH._vnoise2(x, y, 42.0, "ff_wob1") - 1.0) * FAR_EDGE_WOBBLE_M
                + (2.0 * FH._vnoise2(x, y, 16.0, "ff_wob2") - 1.0) * (0.45 * FAR_EDGE_WOBBLE_M)
                for x, y in zip(e_raw, n_raw)
            ], dtype=np.float64)
            # Only push outward where safely outside the tile border (> 14 m)
            d_eff_now = np.array([outside_dist(p[0], p[1], half)[4] for p in P], dtype=np.float64)
            wob = np.where(d_eff_now > 16.0, wob, np.minimum(wob, 0.0))
            P = P + out_n * (wob * s_xy_arr * end_env)[:, None]

        zg = np.array([elev.z_at_eff(p[0], p[1]) for p in P])
        ht = _crown_height_wave(P[:, 0], P[:, 1], h_base, half, rng=look["rng"], mix=mix,
                                ring_chm=ring_chm, height_mult=stand_scale, region_id=region_id)
        if np.hypot(*(P[0] - P[-1])) > 2.0:
            ht = ht * _smooth_end_taper(s, total_s)
        ht = _limit_top_slope(P, zg - 0.5, ht, max_slope=FAR_MAX_TOP_SLOPE, min_h=3.0)
        run_mat = strip_curtain_mat(look["mat"], P, half)   # far-forest-look-s24: band per strip
        sec.add_curtain1(P, zg - 0.5, zg + ht, face_sign=1.0, **{**curtain, "mat": run_mat})

        # ADR 0330 r2 (High tier): patchy undulating undergrowth / shrub mantle skirt in front of outer stand edge
        d_min_run = float(d_true.min())
        if tier == "High" and d_min_run <= FAR_SKIRT_MAX_D_M and k >= 2:
            # Push skirt 2.5..9.5 m * s_xy in front of outer curtain with irregular wave + patchy gaps (~76% kept)
            sk_off = np.array([
                (2.5 + 7.0 * FH._vnoise2(x, y, 26.0, "ff_skoff")) * sxy
                for x, y, sxy in zip(e_raw, n_raw, s_xy_arr)
            ], dtype=np.float64)
            Ps = P + out_n * sk_off[:, None]
            # Keep skirt strictly outside the tile border (d_eff >= 9.0 m)
            sk_keep = np.array([
                outside_dist(p[0], p[1], half)[4] >= 9.0 and FH._vnoise2(x, y, 34.0, "ff_skkeep") > 0.22
                for p, x, y in zip(Ps, e_raw, n_raw)
            ], dtype=bool)
            # Emit contiguous kept sub-runs of the undergrowth skirt
            i0 = 0
            while i0 < k - 1:
                if not (sk_keep[i0] and sk_keep[i0 + 1]):
                    i0 += 1
                    continue
                i1 = i0 + 1
                while i1 + 1 < k and sk_keep[i1 + 1]:
                    i1 += 1
                sub_p = Ps[i0:i1 + 1]
                sub_er, sub_nr = e_raw[i0:i1 + 1], n_raw[i0:i1 + 1]
                sub_sh = s_h_arr[i0:i1 + 1]
                sub_zg = np.array([elev.z_at_eff(p[0], p[1]) for p in sub_p])
                sub_h = np.array([
                    (3.6 + 5.8 * FH._vnoise2(x, y, 20.0, "ff_skh") * (0.72 + 0.56 * FH._vnoise2(x, y, 9.0, "ff_skh2"))) * sh
                    for x, y, sh in zip(sub_er, sub_nr, sub_sh)
                ], dtype=np.float64)
                sub_h = np.minimum(sub_h, ht[i0:i1 + 1] * 0.56)
                # Slightly varying ground sink breaks horizontal shadow seam at base
                sub_sink = np.array([0.35 + 0.50 * FH._vnoise2(x, y, 14.0, "ff_skz") for x, y in zip(sub_er, sub_nr)])
                sub_h = _limit_top_slope(sub_p, sub_zg - sub_sink, sub_h, max_slope=0.30, min_h=2.0)
                sec.add_curtain1(sub_p, sub_zg - sub_sink, sub_zg + sub_h, face_sign=1.0,
                                 mat=run_mat, u_shift=look["u_shift"] + 0.37, u_scale=look["u_scale"],
                                 half=half, v_bot=1.0, v_top=vm_edge)
                i0 = i1 + 1

        # ADR 0330 r2 (High tier): individual crossed-card tree & shrub impostors in front of forest edges (0..1500 m
        # ring, i.e. 300..1500 m from tile cameras) — packed in the same far atlas (0 extra draw calls).
        if tier == "High" and d_min_run <= FAR_IMPOSTOR_MAX_D_M and total_s >= 12.0:
            species_pool = FAR_IMPOSTOR_SPECIES.get(mix, FAR_IMPOSTOR_SPECIES["mixed"])
            bush_pool = ("tree_shrub_0", "tree_shrub_0", "tree_alder_0", "tree_linden_0", "tree_birch_0")
            # Sample positions: irregular spacing along the edge + soft shrubby corners near open run ends
            sample_s = []
            if np.hypot(*(P[0] - P[-1])) > 2.0:
                sample_s.extend([min(3.5, total_s * 0.15), max(total_s - 3.5, total_s * 0.85)])
            s_cur = 7.0 + 12.0 * _hfloat(f"{P[0, 0]:.0f},{P[0, 1]:.0f}", "imp_s0")
            while s_cur < total_s - 5.0:
                sample_s.append(s_cur)
                s_cur += (18.0 + 16.0 * _hfloat(f"{P[0, 0]:.0f},{P[0, 1]:.0f},{s_cur:.0f}", "imp_step"))
            for s_pos in sample_s:
                idx = int(np.searchsorted(s, s_pos, side="right")) - 1
                idx = min(max(idx, 0), k - 2)
                seg_l = max(float(ds[idx]), 1e-6)
                frac = float(np.clip((s_pos - s[idx]) / seg_l, 0.0, 1.0))
                pt = P[idx] * (1.0 - frac) + P[idx + 1] * frac
                nrm = out_n[idx] * (1.0 - frac) + out_n[idx + 1] * frac
                nlen = float(np.hypot(nrm[0], nrm[1]))
                if nlen > 1e-6:
                    nrm /= nlen
                dt_pt = float(d_true[idx] * (1.0 - frac) + d_true[idx + 1] * frac)
                sxy_pt, sh_pt = foreshorten_scales(dt_pt)
                if dt_pt <= FAR_IMPOSTOR_MAX_D_M:
                    tkey = f"{pt[0]:.1f},{pt[1]:.1f}"
                    h_loc = float(ht[idx] * (1.0 - frac) + ht[idx + 1] * frac)
                    # Always place a low bushy shrub/sapling hugging the forest base (breaks the straight lower edge),
                    # plus an occasional taller pioneer tree stepping further into the field
                    is_end = (s_pos < 5.0 or s_pos > total_s - 5.0)
                    bname = _hpick(tkey, list(bush_pool), "bush")
                    b_out = (1.5 + 6.5 * _hfloat(tkey, "bout")) * sxy_pt
                    b_lat = (2.0 * _hfloat(tkey, "blat") - 1.0) * 6.0 * sxy_pt
                    be = float(pt[0] + nrm[0] * b_out - nrm[1] * b_lat)
                    bn = float(pt[1] + nrm[1] * b_out + nrm[0] * b_lat)
                    if outside_dist(be, bn, half)[4] >= 9.5:
                        if bname == "tree_shrub_0":
                            bh = (2.8 + 3.4 * _hfloat(tkey, "bh")) * sh_pt
                        else:
                            bh = max(min(h_loc * (0.36 + 0.28 * _hfloat(tkey, "bh")), 11.0 * sh_pt), 3.8 * sh_pt)
                        sec.add_tree_impostor1(be, bn, elev.z_at_eff(be, bn), bh, bname,
                                               yaw=_hfloat(tkey, "byaw") * math.pi, half=half)
                    if (not is_end) and _hfloat(tkey, "imp_tall") < 0.42:
                        ck = f"{tkey}:tall"
                        out_d = (5.0 + 15.0 * _hfloat(ck, "out")) * sxy_pt
                        lat_d = (2.0 * _hfloat(ck, "lat") - 1.0) * 8.0 * sxy_pt
                        tx_e = float(pt[0] + nrm[0] * out_d - nrm[1] * lat_d)
                        tx_n = float(pt[1] + nrm[1] * out_d + nrm[0] * lat_d)
                        if outside_dist(tx_e, tx_n, half)[4] >= 10.0:
                            tname = _hpick(ck, list(species_pool), "sp")
                            if tname == "tree_shrub_0":
                                th = (3.0 + 3.2 * _hfloat(ck, "h")) * sh_pt
                            else:
                                th = max(h_loc * (0.54 + 0.36 * _hfloat(ck, "h")), 5.0 * sh_pt)
                            sec.add_tree_impostor1(tx_e, tx_n, elev.z_at_eff(tx_e, tx_n), th, tname,
                                                   yaw=_hfloat(ck, "yaw") * math.pi, half=half)
            # ADR 0334 r4: overstorey trees above the canopy, 2-6 m behind the curtain front
            # overstorey: narrow crowns only (a round linden crown above the canopy read as a floating blob)
            tall_pool = tuple(t for t in species_pool if t.startswith(("tree_pine", "tree_spruce", "tree_birch"))) or ("tree_pine_0",)
            rkey = f"{P[0, 0]:.0f},{P[0, 1]:.0f}"
            s_cur = FAR_EMERGENT_STEP_M[0] * _hfloat(rkey, "em_s0")
            while s_cur < total_s - 6.0:
                ek = f"{rkey},{s_cur:.0f}"
                idx = min(max(int(np.searchsorted(s, s_cur, side="right")) - 1, 0), k - 2)
                frac = float(np.clip((s_cur - s[idx]) / max(float(ds[idx]), 1e-6), 0.0, 1.0))
                pt = P[idx] * (1.0 - frac) + P[idx + 1] * frac
                nrm = out_n[idx] * (1.0 - frac) + out_n[idx + 1] * frac
                nrm = nrm / max(float(np.hypot(nrm[0], nrm[1])), 1e-6)
                dt_pt = float(d_true[idx] * (1.0 - frac) + d_true[idx + 1] * frac)
                if dt_pt <= FAR_IMPOSTOR_MAX_D_M and s_cur > 6.0:
                    sxy_pt, _ = foreshorten_scales(dt_pt)
                    h_loc = float(ht[idx] * (1.0 - frac) + ht[idx + 1] * frac)
                    back = (2.0 + 4.0 * _hfloat(ek, "em_b")) * sxy_pt
                    te, tn = float(pt[0] - nrm[0] * back), float(pt[1] - nrm[1] * back)
                    th = h_loc * (FAR_EMERGENT_H[0] + (FAR_EMERGENT_H[1] - FAR_EMERGENT_H[0]) * _hfloat(ek, "em_h"))
                    sec.add_tree_impostor1(te, tn, elev.z_at_eff(te, tn), th, _hpick(ek, list(tall_pool), "em_sp"),
                                           yaw=_hfloat(ek, "em_y") * math.pi, half=half)
                s_cur += FAR_EMERGENT_STEP_M[0] + (FAR_EMERGENT_STEP_M[1] - FAR_EMERGENT_STEP_M[0]) * _hfloat(ek, "em_st")
            # ADR 0334 r4: an open run end steps down in trees past the curtain (the outline turns away there)
            if np.hypot(*(P[0] - P[-1])) > 2.0:
                for end, (i_a, i_b) in (("a", (1, 0)), ("b", (k - 2, k - 1))):
                    tg = P[i_b] - P[i_a]
                    tg = tg / max(float(np.hypot(tg[0], tg[1])), 1e-6)
                    dt_e = float(d_true[i_b])
                    if dt_e > FAR_IMPOSTOR_MAX_D_M:
                        continue
                    sxy_e, _ = foreshorten_scales(dt_e)
                    h_end = float(np.median(ht))
                    for q, (fwd, hf_) in enumerate(((3.0, 0.72), (8.5, 0.52), (14.0, 0.34))):
                        ek = f"{P[i_b, 0]:.0f},{P[i_b, 1]:.0f}:{end}{q}"
                        if _hfloat(ek, "end_keep") > 0.85:
                            continue
                        f_ = (fwd + 3.0 * _hfloat(ek, "end_f")) * sxy_e
                        lat = (2.0 * _hfloat(ek, "end_l") - 1.0) * 4.0 * sxy_e
                        te = float(P[i_b, 0] + tg[0] * f_ - tg[1] * lat)
                        tn = float(P[i_b, 1] + tg[1] * f_ + tg[0] * lat)
                        if outside_dist(te, tn, half)[4] < 10.0:
                            continue
                        th = max(h_end * hf_ * (0.85 + 0.3 * _hfloat(ek, "end_h")), 3.0)
                        sec.add_tree_impostor1(te, tn, elev.z_at_eff(te, tn), th, _hpick(ek, list(tall_pool), "end_sp"),
                                               yaw=_hfloat(ek, "end_y") * math.pi, half=half)

    for a, b in zip(ext[:-1], ext[1:]):
        L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
        if L < 0.5:
            continue
        mx, my = 0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1])
        _, _, de, dn, dm = outside_dist(mx, my, half)
        # Outward normal of CCW polygon edge a->b is (dy/L, -dx/L); radial vector from border is (de/dm, dn/dm)
        nx, ny = (b[1] - a[1]) / L, -(b[0] - a[0]) / L
        facing_tile = -(nx * de + ny * dn) / max(dm, 1e-6)
        if dm < 10.5 or facing_tile < 0.48:
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
                    end_taper = _smooth_end_taper(s, L)
                    zg = np.array([elev.z_at_eff(p[0], p[1]) for p in P])
                    ht = _crown_height_wave(P[:, 0], P[:, 1], h_base, half, rng=look["rng"], mix=mix,
                                            ring_chm=ring_chm, height_mult=stand_scale * 1.02,
                                            region_id=region_id) * end_taper
                    ht = _limit_top_slope(P, zg - 0.5, ht, max_slope=FAR_MAX_TOP_SLOPE, min_h=3.0)
                    sec.add_curtain1(P, zg - 0.5, zg + ht, face_sign=1.0,
                                     **{**curtain, "mat": strip_curtain_mat(look["mat"], P, half)})

    # 3. Low flat under-canopy shadow base tucked 10 m inside (ADR 0330 r2: capped <= 3.6 m so it never reads as a
    #    green conical hill between curtains)
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
        h_mound_ref = h_base
        if ring_chm is not None:
            cr_e, cr_n, cr_d = unforeshorten_xy(np.array([c_xy[0]]), np.array([c_xy[1]]), half)
            hc, ok = ring_chm.sample_heights(cr_e, cr_n, mix)
            if ok[0]:
                h_mound_ref = float(hc[0]) * foreshorten_scales(float(cr_d[0]))[1]
        h_cap = min(max(h_mound_ref * 0.12, 0.8), 2.2)
        col_top = (0.032, 0.050, 0.030, 0.0) if mix == "conifer" else (0.038, 0.058, 0.034, 0.0)
        if look.get("mound") is not None:      # ADR 0330: per mix (+ broadleaf) and per stand x 0.88-1.14
            col_top = (*look["mound"], 0.0)
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
    # ADR 0318: keep nearby buildings and the skyline; omit small distant
    # envelopes on Low according to their rendered size, rather than source IDs.
    # WORKING_VALUE: below 20 x 10 m after compression these repeated envelopes
    # contribute little to the silhouette, while roofs/fascias remain closed.
    longest_eff = max(np.linalg.norm(rc[(i + 1) % 4] - rc[i]) for i in range(4)) * s_xy
    if tier == "Low" and d_raw > 900.0 and longest_eff < 20.0 and max(h_raw * s_h, 3.2) < 10.0:
        return
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
        z_attic = z_top - min(0.45 * s_h, h_eff * 0.08)

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
            if z_attic < z_top:
                sec.add_quad0([a[0], a[1], z_attic], [c[0], c[1], z_attic], [c[0], c[1], z_top], [a[0], a[1], z_top],
                              (*COL_PARAPET, 0.0))

        # Close roofs on Low too; no open boxes when viewed downhill.
        sec.add_quad0([pts[0, 0], pts[0, 1], z_top], [pts[1, 0], pts[1, 1], z_top],
                      [pts[2, 0], pts[2, 1], z_top], [pts[3, 0], pts[3, 1], z_top],
                      (*COL_ROOF_FLAT, 0.0), normal=[0.0, 0.0, 1.0])

        # Elevator / stairwell penthouse on taller wielka-płyta blocks
        if storeys >= 6 and tier == "High":
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
        use_fascia = True
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

        sec.add_quad0([pts[0, 0], pts[0, 1], z_top], [pts[1, 0], pts[1, 1], z_top],
                      [pts[2, 0], pts[2, 1], z_top], [pts[3, 0], pts[3, 1], z_top],
                      (*COL_ROOF_FLAT, 0.0), normal=[0.0, 0.0, 1.0])
        return

    if typ == "office":
        wall_rgb = _hpick(bid, PALETTE_OFFICE, "wall")
        storeys = b.get("storeys") or max(2, int(round((h_raw - 0.8) / 3.4)))
        storeys = max(2, min(storeys, 8))
        w_mode = 0.75 if _hfloat(bid, "rib") < 0.4 else 1.0
        z_attic = z_top - min(0.4 * s_h, h_eff * 0.08)
        for i in range(4):
            a, c = pts[i], pts[(i + 1) % 4]
            if not _wall_visible_from_tile(a, c, half):
                continue
            L_raw = edges_raw[i]
            if L_raw >= 6.0:
                bays = max(2, int(round(L_raw / 3.2)))
                uv1 = [[0.0, -0.25], [float(bays), -0.25], [float(bays), float(storeys)], [0.0, float(storeys)]]
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_attic], [a[0], a[1], z_attic],
                              (*wall_rgb, w_mode), uv1=uv1)
            else:
                sec.add_quad0([a[0], a[1], z_bot], [c[0], c[1], z_bot], [c[0], c[1], z_attic], [a[0], a[1], z_attic],
                              (*wall_rgb, 0.0))
            sec.add_quad0([a[0], a[1], z_attic], [c[0], c[1], z_attic], [c[0], c[1], z_top], [a[0], a[1], z_top],
                          (*COL_PARAPET, 0.0))
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
            # A backdrop is observed from inside its owning tile. As with
            # building walls, omit faces hidden from every point of that tile.
            if _wall_visible_from_tile(np.asarray(p00[:2]), np.asarray(p10[:2]), half):
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


# ------------------------------------------------------------------------------------------- HV lines (ADR 0351)
# The ring draws lattice towers only where a HV line runs (BDOT10k OT_SULN_L "... wysokiego napięcia", OSM
# power=line voltage >= 60 kV, or an untagged OSM power=line carrying >= 2 mapped towers) and hangs the conductors
# between them. Before ADR 0351 it stood a 27 m tower every 210 m along EVERY ring line (MV and LV included) and
# drew every BDOT10k "słup energetyczny" (mostly concrete MV poles) as a tower - with no conductor at all
# (CRITIC s24 wave 11 # 1: dk65-07 owner02_seam_n_cab; 17 110 unwired far-field towers over 54 tiles).
POWER_KINDS = ("słup energetyczny", "power_tower")
PYLON_H_M = 32.0                 # = streetscape.props.pylon (one tower height in and outside the tile, WORKING_VALUE)
SEAM_TOL_M = 0.5                 # a HV piece end this close to the tile edge is the tile's own seam support
OSM_DUP_M = 25.0                 # an OSM HV line within this of a BDOT10k HV line for >= OSM_DUP_SHARE is the same line
OSM_DUP_SHARE = 0.7
RULE_MERGE_M = 60.0              # a rule angle-point tower this close to a mapped neighbour merges into it (WORKING_VALUE)
# MV lines (BDOT10k "... średniego napięcia", OSM power=line 1-60 kV): concrete poles + 3 conductors of the tile's
# props.power_pole, High only, only up to MV_FAR_MAX_M outside the tile (beyond ~380 m a 12 m pole + 10 mm wires sit
# 600-1200 m from the driver and only formed a grey cage over the forest edge; ADR 0351 addendum).
MV_FAR_MAX_M = 380.0
MV_RULE_MERGE_M = 25.0
MV_MIN_EFF_SEP_M = 28.0
HIGH_HV_MAX_D_M = 3400.0         # beyond 3.4 km radial compression < 2 % and haze hides steel silhouettes (WORKING_VALUE)
FAR_HV_SILHOUETTE_D_M = 800.0    # High switches from open 3D A-frame to crisp open ribbon "A"/"Y" silhouette (WORKING_VALUE)
FAR_HV_SIMPLE_ARMS_D_M = 1500.0  # beyond 1.5 km, 2-tier "Y" arms stay iconic without merging into a grey block (WORKING_VALUE)
FAR_HV_WIRE_FULL_D_M = 450.0     # all 7 conductors near the tile seam; 3 main silhouette wires beyond (WORKING_VALUE)
FAR_HV_WIRE_MAX_D_M = 1050.0     # no opaque HV wire ribbons past ~1.1 km outside border (<0.03 px; WORKING_VALUE)
LOW_HV_WIRE_MAX_D_M = 900.0      # Low tier wire cutoff (WORKING_VALUE)
COL_FAR_CONCRETE = (0.16, 0.158, 0.15)    # x plaster_white of far_field_buildings: 0.36 rendered white (VQA r1)
# Galvanised steel (ADR 0351): the tile's pylon_steel is linear 0.115-0.12; COL_PYLON_STEEL 0.27-0.30 (x plaster_white
# of far_field_buildings) rendered snow white in sun. Per-tower +-12 % brightness / +-3 % warm-cool shift (weathered vs
# newer zinc), vertex colour only: no material, no draw call. WORKING_VALUE, judged on the visual-QA frames.
COL_PYLON_GALV = (0.150, 0.155, 0.160)
COL_FAR_WIRE = (0.055, 0.056, 0.055)   # dark weathered aluminium; WorldSurface.shader softens contrast with distance
# Far conductors are thin opaque ribbons in submesh 0 (<= 2 submeshes/sector, +0 draw calls): ADR 0351 addendum cuts
# width in half (0.30 px HV / 0.24 px MV, capped at 0.085 / 0.040 m half-width so distant wires never swell into 40 cm
# horizontal bars) and encodes (fadeStart_100m, -(100 + fadeEnd_100m)) in TEXCOORD_1 for WorldSurface.shader distance
# fade matching Kamion/World Wire (COLOR_0.a stays 0.0, TEXCOORD_1.x >= 0.0). WORKING_VALUE.
FAR_WIRE_PX_M = 2.0 * math.tan(math.radians(30.0)) / 1080.0
FAR_WIRE_PX_FRAC = 0.42
FAR_MV_WIRE_PX_FRAC = 0.26
FAR_WIRE_VIEW_M = 60.0
FAR_WIRE_MAX_HALF_W = 0.095
FAR_MV_WIRE_MAX_HALF_W = 0.042
FAR_HV_WIRE_FADE_M = (420.0, 1350.0)
FAR_MV_WIRE_FADE_M = (200.0, 480.0)
FAR_WIRE_UV1_SENTINEL = 100.0    # uv1.y = -(100 + fadeEnd_100m) <= -100: disjoint from building facades & skyline (-16)


def galv_colour(key: str) -> tuple:
    f = 0.88 + 0.24 * _hfloat(key, "galv")
    w = 0.06 * (_hfloat(key, "galv-hue") - 0.5)
    r, g, b = COL_PYLON_GALV
    return (r * f * (1.0 + w), g * f, b * f * (1.0 - w))


def _arm_levels() -> list[tuple[float, float]]:
    """(cross-arm height, conductor height) as fractions of the tower height (streetscape.props.pylon layout)."""
    from streetscape import props as PR
    return [(za / PYLON_H_M, (za - PR.PYLON_INSULATOR_M) / PYLON_H_M) for za in PR.PYLON_ARM_Z]


def _arm_len() -> float:
    from streetscape import props as PR
    return PR.PYLON_ARM_L


def _pylon_scale(s_h: float) -> float:
    """Proportional silhouette scale for far-field HV towers (ADR 0351 addendum: was max(s_h, 0.65) which made distant
    2-3 km towers stubby and wide enough to overlap into a grey mesh band)."""
    return max(float(s_h), 0.38)


def _hv_min_eff_sep(d_raw: float, tier: str) -> float:
    """Minimum foreshortened XY separation [m] between any two drawn far-field HV towers (ADR 0351 addendum).
    Prevents radial foreshortening from crushing 2-4 km spans into 1.6-15 m overlapping grey mesh bands."""
    if tier == "Low":
        return min(45.0 + 0.060 * max(float(d_raw) - 350.0, 0.0), 170.0)
    return min(45.0 + 0.045 * max(float(d_raw) - 450.0, 0.0), 140.0)


def _select_far_hv(plan: dict, half: float, tier: str) -> tuple[list[dict], list[tuple[dict, dict]]]:
    """Density LOD for far-field HV towers & spans in foreshortened render space (ADR 0351 addendum).
    Walks connected line chains near-to-far (seam anchors first), enforces _hv_min_eff_sep globally across all chains
    so neither receding spans nor parallel lines stack into a grey band, and re-links consecutive kept supports."""
    max_d = LOW_HV_MAX_D_M if tier == "Low" else HIGH_HV_MAX_D_M
    nodes: dict[int, dict] = {}
    adj: dict[int, list[int]] = {}
    for a, b in plan["spans"]:
        ia, ib = id(a), id(b)
        nodes[ia] = a
        nodes[ib] = b
        adj.setdefault(ia, []).append(ib)
        adj.setdefault(ib, []).append(ia)
    if not nodes:
        return [], []

    eff_cache: dict[int, tuple[float, float, float, float]] = {
        k: foreshorten_point(float(n["e"]), float(n["n"]), half) for k, n in nodes.items()
    }
    visited_edges: set[tuple[int, int]] = set()
    chains: list[list[int]] = []

    def ekey(u: int, v: int) -> tuple[int, int]:
        return (u, v) if u < v else (v, u)

    starts = [k for k, nbs in adj.items() if len(nbs) != 2 or nodes[k].get("seam")]
    starts.sort(key=lambda k: (0 if nodes[k].get("seam") else 1, eff_cache[k][2], float(nodes[k]["e"]), float(nodes[k]["n"])))
    for s in starts:
        for nb in adj[s]:
            ek = ekey(s, nb)
            if ek in visited_edges:
                continue
            chain = [s, nb]
            visited_edges.add(ek)
            cur = nb
            while len(adj[cur]) == 2 and not nodes[cur].get("seam"):
                nxt = adj[cur][0] if adj[cur][1] == chain[-2] else adj[cur][1]
                ek2 = ekey(cur, nxt)
                if ek2 in visited_edges:
                    break
                visited_edges.add(ek2)
                chain.append(nxt)
                cur = nxt
            chains.append(chain)
    # Any closed cycles without degree!=2 vertices
    for u in sorted(adj, key=lambda k: (eff_cache[k][2], float(nodes[k]["e"]), float(nodes[k]["n"]))):
        for v in adj[u]:
            ek = ekey(u, v)
            if ek in visited_edges:
                continue
            chain = [u, v]
            visited_edges.add(ek)
            cur = v
            while True:
                nxt = next((x for x in adj[cur] if ekey(cur, x) not in visited_edges), None)
                if nxt is None:
                    break
                visited_edges.add(ekey(cur, nxt))
                chain.append(nxt)
                cur = nxt
            chains.append(chain)

    for ch in chains:
        if eff_cache[ch[-1]][2] < eff_cache[ch[0]][2]:
            ch.reverse()
    chains.sort(key=lambda ch: (0 if nodes[ch[0]].get("seam") else 1, eff_cache[ch[0]][2]))

    kept_ids: set[int] = set()
    kept_eff: list[tuple[float, float]] = []
    render_spans: list[tuple[dict, dict]] = []
    for ch in chains:
        chain_kept: list[int] = []
        for k in ch:
            n = nodes[k]
            ce, cn, dr, _ = eff_cache[k]
            if n.get("seam"):
                kept_ids.add(k)
                chain_kept.append(k)
                continue
            if dr > max_d:
                continue
            if k in kept_ids:
                chain_kept.append(k)
                continue
            req = _hv_min_eff_sep(dr, tier)
            if all(math.hypot(ce - oe, cn - on) >= req for oe, on in kept_eff):
                kept_ids.add(k)
                kept_eff.append((ce, cn))
                chain_kept.append(k)
        for u, v in zip(chain_kept, chain_kept[1:]):
            render_spans.append((nodes[u], nodes[v]))

    # Keep deterministic order matching plan["pylons"]
    render_pylons = [p for p in plan["pylons"] if id(p) in kept_ids and not p.get("seam")]
    return render_pylons, render_spans


def _select_far_mv(plan: dict, half: float) -> tuple[list[dict], list[tuple[dict, dict]]]:
    """Thin far-field MV poles in foreshortened space so dense rural MV lines don't pack into a fence over trees."""
    kept_ids: set[int] = set()
    kept_eff: list[tuple[float, float]] = []
    all_nodes: dict[int, dict] = {}
    for a, b in plan["mv_spans"]:
        all_nodes[id(a)] = a
        all_nodes[id(b)] = b
    order = sorted(all_nodes, key=lambda k: (0 if all_nodes[k].get("seam") else 1,
                                             outside_dist(float(all_nodes[k]["e"]), float(all_nodes[k]["n"]), half)[4]))
    for k in order:
        n = all_nodes[k]
        if n.get("seam"):
            kept_ids.add(k)
            continue
        ce, cn, dr, _ = foreshorten_point(float(n["e"]), float(n["n"]), half)
        if dr > MV_FAR_MAX_M:
            continue
        if all(math.hypot(ce - oe, cn - on) >= MV_MIN_EFF_SEP_M for oe, on in kept_eff):
            kept_ids.add(k)
            kept_eff.append((ce, cn))
    poles = [p for p in plan["mv_poles"] if id(p) in kept_ids]
    spans = [(a, b) for a, b in plan["mv_spans"] if id(a) in kept_ids and id(b) in kept_ids]
    return poles, spans


def _add_pylon(sectors: dict[str, SectorBuilder], py: dict, elev: BorderElevation, half: float, tier: str,
               yaw: float = 0.0, arms: bool = True):
    """Far-field HV tower or plain lattice mast (ADR 0351 + addendum).
    - Near High (<= FAR_HV_SILHOUETTE_D_M): open tapered 3D A-frame matching props.pylon (foot -> waist -> spire peak,
      3 slender cross-arms, light lower X-diagonals, NO heavy horizontal ring bars that blurred into a grey mesh).
    - Far High (> FAR_HV_SILHOUETTE_D_M) and Low: iconic open vertical "A"/"Y" silhouette (splayed legs closing to a
      sharp peak, 1 open lower X-brace, 2-3 slender Y-braced cross-arms; ~22-28 tris vs 222 tris before)."""
    e_raw, n_raw = float(py["e"]), float(py["n"])
    h_raw = max(float(py.get("h") or 26.0), 22.0)
    ce, cn, d_raw, _ = foreshorten_point(e_raw, n_raw, half)
    if tier == "Low" and d_raw > LOW_HV_MAX_D_M:
        return
    if tier == "High" and d_raw > HIGH_HV_MAX_D_M:
        return
    _, s_h = foreshorten_scales(d_raw)
    sec = sectors[sector_of(ce, cn, half)]
    z_ref = elev.z_at_eff(ce, cn)
    z_bot = z_ref - 0.8
    h_eff = max(h_raw * s_h, 11.5)
    z_top = z_ref + h_eff

    ca, sa = math.cos(yaw), math.sin(yaw)
    ux, uy = ca, sa
    vx, vy = -sa, ca
    col = (*galv_colour(str(py.get("id") or f"{e_raw:.1f},{n_raw:.1f}")), 0.0)
    scale = _pylon_scale(s_h)
    arm_l = _arm_len()

    # Tapered Polish "A"-frame profile matching streetscape.props.pylon_half_width (wide splayed foot -> narrow waist
    # under the lowest cross-arm -> sharp lightning-rod spire peak instead of a blunt box top).
    w_bot = 2.15 * scale
    w_waist = 0.72 * scale
    w_peak = 0.06 * scale
    z_waist = z_ref + h_eff * 0.60

    def ring_pts(w: float, z: float):
        return [
            [ce - ux * w - vx * w, cn - uy * w - vy * w, z],
            [ce + ux * w - vx * w, cn + uy * w - vy * w, z],
            [ce + ux * w + vx * w, cn + uy * w + vy * w, z],
            [ce - ux * w + vx * w, cn - uy * w + vy * w, z],
        ]

    # Far horizon (> 800 m on High) and Low: crisp open vertical "A"/"Y" ribbon silhouette facing the owning tile.
    # Only 2 outer splayed A-legs + 1 delicate internal X + Y-braced cross-arms -> wide open sky gap inside the "A",
    # zero horizontal grid rings, ~22-28 tris instead of 222.
    if tier == "Low" or d_raw > FAR_HV_SILHOUETTE_D_M:
        view = np.array([-ce, -cn, 0.0])
        vlen = float(np.linalg.norm(view))
        view = view / vlen if vlen > 1e-6 else np.array([0.0, -1.0, 0.0])
        side = np.array([-view[1], view[0], 0.0])

        def ribbon(a, b, radius):
            a, b = np.asarray(a, float), np.asarray(b, float)
            axis = b - a
            alen = float(np.linalg.norm(axis))
            if alen < 1e-6:
                return
            axis /= alen
            width = np.cross(axis, view)
            wlen = float(np.linalg.norm(width))
            if wlen < 1e-8:
                width = np.cross(axis, np.array([0.0, 0.0, 1.0]))
                wlen = float(np.linalg.norm(width))
            width *= radius / max(wlen, 1e-8)
            sec.add_quad0(a - width, a + width, b + width, b - width, col)

        sx_v, sy_v = float(side[0]), float(side[1])
        foot_l = [ce - sx_v * w_bot, cn - sy_v * w_bot, z_bot]
        foot_r = [ce + sx_v * w_bot, cn + sy_v * w_bot, z_bot]
        waist_l = [ce - sx_v * w_waist, cn - sy_v * w_waist, z_waist]
        waist_r = [ce + sx_v * w_waist, cn + sy_v * w_waist, z_waist]
        peak = [ce, cn, z_top]

        # Open "A"-frame silhouette: splayed lower legs -> slender upper spire closing to sharp peak
        r_leg = (0.16 if d_raw > 1400.0 else 0.14) * scale
        ribbon(foot_l, waist_l, r_leg)
        ribbon(foot_r, waist_r, r_leg)
        ribbon(waist_l, peak, r_leg * 0.85)
        ribbon(waist_r, peak, r_leg * 0.85)
        # Single delicate internal X-brace in the lower "A" cavity (no horizontal grid bars)
        mid_f = 0.08
        ml = [foot_l[0] + (waist_l[0] - foot_l[0]) * mid_f, foot_l[1] + (waist_l[1] - foot_l[1]) * mid_f,
              z_bot + (z_waist - z_bot) * mid_f]
        mr = [foot_r[0] + (waist_r[0] - foot_r[0]) * mid_f, foot_r[1] + (waist_r[1] - foot_r[1]) * mid_f,
              z_bot + (z_waist - z_bot) * mid_f]
        ribbon(ml, waist_r, 0.065 * scale)
        ribbon(mr, waist_l, 0.065 * scale)

        if arms:
            levels = _arm_levels()
            # Keep true cross-arm azimuth while wired; beyond wire range ensure edge-on towers still show a "Y" head
            ax, ay = vx, vy
            arm_proj = abs(vx * sx_v + vy * sy_v)
            if d_raw > FAR_HV_WIRE_MAX_D_M and arm_proj < 0.55:
                ax, ay = sx_v, sy_v
            if tier == "Low":
                use_levels = [(levels[0][0], 1.0), (levels[2][0], 0.78)]
            elif d_raw > FAR_HV_SIMPLE_ARMS_D_M:
                use_levels = [(levels[0][0], 1.0), (levels[2][0], 0.78)]
            else:
                use_levels = [(levels[0][0], 1.0), (levels[1][0], 0.94), (levels[2][0], 0.82)]
            for frac, w_mul in use_levels:
                za = z_ref + h_eff * frac
                sp = arm_l * scale * w_mul
                left = [ce - ax * sp, cn - ay * sp, za]
                right = [ce + ax * sp, cn + ay * sp, za]
                top = [ce, cn, za + max(1.15 * s_h, 0.55)]
                # Angled Y-ties + slender chord (thinner than vertical legs so arms never dominate as horizontal bars)
                ribbon(left, right, 0.085 * scale)
                ribbon(left, top, 0.065 * scale)
                ribbon(top, right, 0.065 * scale)
        return

    # Near-ring High (<= 800 m outside border): open 3D tapered A-frame matching props.pylon without horizontal rings.
    def member(a, b, radius):
        a, b = np.asarray(a, float), np.asarray(b, float)
        axis = b - a
        alen = float(np.linalg.norm(axis))
        if alen < 1e-6:
            return
        axis /= alen
        ref = np.array([0., 0., 1.]) if abs(axis[2]) < 0.9 else np.array([1., 0., 0.])
        u = np.cross(axis, ref)
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        angles = np.arange(3) * (2.0 * math.pi / 3.0)
        offsets = radius * (np.cos(angles)[:, None] * u + np.sin(angles)[:, None] * v)
        for k in range(3):
            q = (k + 1) % 3
            sec.add_quad0(a + offsets[k], a + offsets[q], b + offsets[q], b + offsets[k], col)

    rb = ring_pts(w_bot, z_bot)
    rw = ring_pts(w_waist, z_waist)
    rt = ring_pts(w_peak, z_top)
    for a, b, c in zip(rb, rw, rt):
        member(a, b, 0.115 * scale)
        member(b, c, 0.095 * scale)
    # Two light diagonal lacing panels on the lower A-shaft (no horizontal ring bars -> open lattice, never a grid)
    z_mid = 0.5 * (z_bot + z_waist)
    rm = ring_pts(0.5 * (w_bot + w_waist), z_mid)
    for panel, (lower, upper) in enumerate(((rb, rm), (rm, rw))):
        for k in range(4):
            q = (k + 1) % 4
            a, b = (k, q) if (panel + k) % 2 == 0 else (q, k)
            member(lower[a], upper[b], 0.055 * scale)
    if arms:
        for frac, _ in _arm_levels():
            za = z_ref + h_eff * frac
            sp = arm_l * scale
            left = [ce - vx * sp, cn - vy * sp, za]
            right = [ce + vx * sp, cn + vy * sp, za]
            top = [ce, cn, za + max(1.05 * s_h, 0.50)]
            member(left, right, 0.095 * scale)
            member(left, top, 0.065 * scale)
            member(top, right, 0.065 * scale)


def _on_seam(p, half: float) -> bool:
    return abs(max(abs(float(p[0])), abs(float(p[1]))) - half) < SEAM_TOL_M


def _line_supports(ls: LineString, towers: list[dict], tower_xy: np.ndarray, half: float, cls: str = "pylon",
                   merge_m: float = RULE_MERGE_M) -> list[dict]:
    """Supports of one HV piece in order along it - the rule of streetscape.furniture.power_supports (ADR 0351):
    mapped towers within the pylon snap radius of the line at their projection, angle points / ends (snapped to a
    mapped tower, else a rule tower; an end on the tile edge is the tile's seam support), gaps over the span maximum
    subdivided."""
    from streetscape import furniture as FU
    snap_r, span = FU.SUPPORT_SNAP_M[cls], FU.SPAN_MAX_M[cls]
    cand = []
    if len(tower_xy):
        d = shapely.distance(ls, shapely.points(tower_xy))
        for i in np.flatnonzero(d <= snap_r):
            cand.append((float(ls.project(Point(*tower_xy[i]))), tower_xy[i].copy(), "tower", towers[i]))
    for v in np.asarray(ls.coords, float):
        if _on_seam(v, half):
            cand.append((float(ls.project(Point(*v))), v.copy(), "seam", None))
            continue
        if len(tower_xy):
            dd = np.hypot(*(tower_xy - v).T)
            i = int(np.argmin(dd))
            if dd[i] <= snap_r:
                cand.append((float(ls.project(Point(*tower_xy[i]))), tower_xy[i].copy(), "tower", towers[i]))
                continue
        cand.append((float(ls.project(Point(*v))), v.copy(), "rule", None))
    rank = {"seam": 0, "tower": 1, "rule": 2}
    cand.sort(key=lambda c: (c[0], rank[c[2]]))
    seq = []
    for c in cand:
        if seq and np.hypot(*(c[1] - seq[-1][1])) < 1.0:
            if rank[c[2]] < rank[seq[-1][2]]:
                seq[-1] = c
            continue
        if c[2] == "tower" and any(t is c[3] for *_, t in seq):
            continue
        seq.append(c)
    # A BDOT10k angle point a few tens of metres from a mapped tower is the same tower (vertex digitised off it):
    # no second tower beside it (dk65-07 ring: 28 m / 44 m "spans" before this). Seam ends are kept.
    keep = []
    for i, c in enumerate(seq):
        if c[2] == "rule" and any(0 <= j < len(seq) and seq[j][2] == "tower"
                                  and np.hypot(*(seq[j][1] - c[1])) < merge_m for j in (i - 1, i + 1)):
            continue
        keep.append(c)
    seq = keep
    full = [seq[0]]
    for a, b in zip(seq, seq[1:]):
        gap = b[0] - a[0]
        k = max(1, int(math.ceil(gap / span - 1e-9)))
        for i in range(1, k):
            g = ls.interpolate(a[0] + gap * i / k)
            full.append((a[0] + gap * i / k, np.array([g.x, g.y]), "rule", None))
        full.append(b)
    out = []
    pts = [c[1] for c in full]
    for i, (_, q, kind, tw) in enumerate(full):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        out.append({"e": float(q[0]), "n": float(q[1]), "kind": kind, "tower": tw,
                    "yaw": math.atan2(float(d[1]), float(d[0]))})
    return out


def power_plan(gis: dict, half: float = 1024.0, region_id: str | None = None) -> dict:
    """Far-field HV towers, conductor spans and other masts from the ring GIS (ADR 0351). Pure, no mesh."""
    lines = [pl for pl in gis.get("power_lines", []) if isinstance(pl, dict)]
    towers = [p for p in gis["pylons"] if p.get("kind") in POWER_KINDS]
    masts = [p for p in gis["pylons"] if p.get("kind") not in POWER_KINDS]
    tower_xy = np.array([[p["e"], p["n"]] for p in towers], float).reshape(-1, 2)
    stats = {"lines": len(lines), "lines_hv_bdot": 0, "lines_hv_osm": 0, "lines_not_hv": 0,
             "osm_hv_duplicates_of_bdot": 0, "osm_untagged_dropped": 0}
    bdot_hv = [LineString(pl["pts"]) for pl in lines if pl["hv"] is True and pl["src"] == "bdot10k"]
    bdot_union = shapely.union_all(bdot_hv) if bdot_hv else None
    hv, mv = [], []
    mv_zone = box(-half - MV_FAR_MAX_M, -half - MV_FAR_MAX_M, half + MV_FAR_MAX_M, half + MV_FAR_MAX_M)
    for pl in lines:
        if pl["hv"] is False:
            stats["lines_not_hv"] += 1
            if pl.get("mv"):
                g = shapely.intersection(LineString(pl["pts"]), mv_zone)
                mv += [x for x in getattr(g, "geoms", [g]) if x.geom_type == "LineString" and x.length >= 20.0]
            continue
        ls = LineString(pl["pts"])
        if pl["src"] != "bdot10k":
            if bdot_union is not None:
                s = shapely.points([ls.interpolate(x).coords[0] for x in np.arange(0.0, ls.length + 1e-6, 20.0)])
                if float(np.mean(shapely.distance(bdot_union, s) < OSM_DUP_M)) >= OSM_DUP_SHARE:
                    stats["osm_hv_duplicates_of_bdot"] += 1
                    continue
            if pl["hv"] is None:
                from streetscape import furniture as FU
                on = int(np.sum(shapely.distance(ls, shapely.points(tower_xy)) <= FU.SUPPORT_SNAP_M["pylon"])) \
                    if len(tower_xy) else 0
                if on < 2:
                    stats["osm_untagged_dropped"] += 1
                    continue
            stats["lines_hv_osm"] += 1
        else:
            stats["lines_hv_bdot"] += 1
        hv.append(ls)

    supports, spans, used = {}, [], set()

    def key(s):
        if s["kind"] == "tower":
            return ("t", id(s["tower"]))
        return ("p", round(s["e"] * 2.0), round(s["n"] * 2.0))   # 0.5 m: line pieces sharing an end share it

    for ls in hv:
        seq = _line_supports(ls, towers, tower_xy, half)
        for s in seq:
            k = key(s)
            if k not in supports:
                tw = s["tower"]
                supports[k] = {"id": (tw.get("id") if tw else None) or f"hv_{s['e']:.1f}_{s['n']:.1f}",
                               "e": round(s["e"], 3), "n": round(s["n"], 3), "h": PYLON_H_M, "yaw": s["yaw"],
                               "seam": s["kind"] == "seam", "mapped": s["kind"] == "tower"}
            if s["tower"] is not None:
                used.add(id(s["tower"]))
        for a, b in zip(seq, seq[1:]):
            ka, kb = key(a), key(b)
            if ka != kb and math.hypot(a["e"] - b["e"], a["n"] - b["n"]) >= 5.0:
                spans.append((supports[ka], supports[kb]))
    wired = {id(x) for ab in spans for x in ab}
    # wave 12: a support whose only neighbours are < 5 m away has no span - drawing it would be an unwired tower
    draw = [s for s in supports.values() if not s["seam"] and id(s) in wired]
    stats["pylons_dropped_unwired"] = sum(1 for s in supports.values() if not s["seam"] and id(s) not in wired)
    # MV (High only, <= MV_FAR_MAX_M out): poles at the BDOT10k "słup energetyczny" left over by the HV lines
    poles_left = [p for p in towers if id(p) not in used and p.get("kind") == "słup energetyczny"]
    pole_xy = np.array([[p["e"], p["n"]] for p in poles_left], float).reshape(-1, 2)
    mv_sup, mv_spans = {}, []
    for ls in mv:
        seq = _line_supports(ls, poles_left, pole_xy, half, cls="power_pole", merge_m=MV_RULE_MERGE_M)
        for s in seq:
            k = key(s)
            if k not in mv_sup:
                mv_sup[k] = {"id": f"mv_{s['e']:.1f}_{s['n']:.1f}", "e": round(s["e"], 3), "n": round(s["n"], 3),
                             "yaw": s["yaw"], "seam": s["kind"] == "seam", "mapped": s["kind"] == "tower"}
            if s["tower"] is not None:
                used.add(id(s["tower"]))
        for a, b in zip(seq, seq[1:]):
            ka, kb = key(a), key(b)
            if ka != kb and math.hypot(a["e"] - b["e"], a["n"] - b["n"]) >= 5.0:
                mv_spans.append((mv_sup[ka], mv_sup[kb]))
    mv_poles = [s for s in mv_sup.values() if not s["seam"]]
    dropped = {}
    for p in towers:
        if id(p) not in used:
            dropped[p.get("kind")] = dropped.get(p.get("kind"), 0) + 1
    stats.update({
        "pylons": len(draw),
        "pylons_mapped": sum(s["mapped"] for s in draw),
        "pylons_rule": sum(not s["mapped"] for s in draw),
        "seam_supports": sum(s["seam"] for s in supports.values()),
        "spans": len(spans),
        "unwired_power_pylons": sum(id(s) not in wired for s in draw),
        "dropped_towers_off_hv_lines": dict(sorted(dropped.items())),
        "masts": len(masts),
        "mv_lines_near": len(mv),
        "mv_poles": len(mv_poles),
        "mv_spans": len(mv_spans),
        "mv_seam_supports": sum(s["seam"] for s in mv_sup.values()),
    })
    return {"pylons": draw, "spans": spans, "masts": masts, "mv_poles": mv_poles, "mv_spans": mv_spans,
            "stats": stats}


def _add_pole(sectors: dict[str, SectorBuilder], s: dict, elev: BorderElevation, half: float):
    """MV concrete pole of the tile (props.power_pole: 12 m, cross-arm 0.9 m below the top), foreshortened (ADR 0351)."""
    from roads import standards as S
    ce, cn, d_raw, _ = foreshorten_point(float(s["e"]), float(s["n"]), half)
    _, s_h = foreshorten_scales(d_raw)
    sec = sectors[sector_of(ce, cn, half)]
    z0 = elev.z_at_eff(ce, cn) - 0.5
    H = S.GROUND_PROP_H["power_pole"] * s_h
    yaw = float(s["yaw"])
    u = np.array([math.cos(yaw), math.sin(yaw)])
    v = np.array([-u[1], u[0]])
    k = max(s_h, 0.65)
    col = (*COL_FAR_CONCRETE, 0.0)
    rb, rt = 0.16 * k, 0.09 * k
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        p0 = [ce + (a[0] * u[0] + a[1] * v[0]) * rb, cn + (a[0] * u[1] + a[1] * v[1]) * rb, z0]
        p1 = [ce + (b[0] * u[0] + b[1] * v[0]) * rb, cn + (b[0] * u[1] + b[1] * v[1]) * rb, z0]
        p2 = [ce + (b[0] * u[0] + b[1] * v[0]) * rt, cn + (b[0] * u[1] + b[1] * v[1]) * rt, z0 + 0.5 + H]
        p3 = [ce + (a[0] * u[0] + a[1] * v[0]) * rt, cn + (a[0] * u[1] + a[1] * v[1]) * rt, z0 + 0.5 + H]
        sec.add_quad0(p0, p1, p2, p3, col)
    za = z0 + 0.5 + H - 0.5 * s_h
    arm = 0.9 * k
    w = 0.05 * k
    for sgn in (1.0, -1.0):          # two faces of the galvanised cross-arm, across the line
        a = [ce - v[0] * arm, cn - v[1] * arm, za - w]
        b = [ce + v[0] * arm, cn + v[1] * arm, za - w]
        c = [ce + v[0] * arm, cn + v[1] * arm, za + w]
        d = [ce - v[0] * arm, cn - v[1] * arm, za + w]
        off = u * w * sgn
        quad = [[q[0] + off[0], q[1] + off[1], q[2]] for q in (a, b, c, d)]
        if sgn < 0:
            quad = quad[::-1]
        sec.add_quad0(*quad, (*galv_colour(s["id"]), 0.0))


def _add_span(sectors: dict[str, SectorBuilder], a: dict, b: dict, elev: BorderElevation, half: float, tier: str,
              mv: bool = False):
    """Conductors of one span between two supports (far towers / poles or the tile's seam support) as thin opaque
    ribbons in submesh 0 (ADR 0351 + addendum).
    - Distance LOD: HV High draws all 7 conductors up to FAR_HV_WIRE_FULL_D_M (seam continuity), 3 main conductors up
      to FAR_HV_WIRE_MAX_D_M, and 0 beyond (a 24 mm cable at >1.4 km is <0.03 px; prevents horizon horizontal mesh).
    - Width: thinner (0.30 px HV / 0.24 px MV, capped) and gently tapered with true distance.
    - Shader fade: TEXCOORD_1 = (fadeStart/100, -(100 + fadeEnd/100)) with COLOR_0.a = 0.0; WorldSurface.shader
      (_FAR_FACADE) softens contrast with coverage + true distance like Kamion/World Wire."""
    from streetscape import furniture as FU
    from roads import standards as S
    ends = []
    d_raws = []
    for s in (a, b):
        ce, cn, d_raw, _ = foreshorten_point(float(s["e"]), float(s["n"]), half)
        if tier == "Low" and (mv or d_raw > LOW_HV_WIRE_MAX_D_M):
            return
        d_raws.append(d_raw)
        _, s_h = foreshorten_scales(d_raw)
        if mv:
            s_h = 1.0 if s.get("seam") else s_h
            ends.append((np.array([ce, cn]), elev.z_at_eff(ce, cn), S.GROUND_PROP_H["power_pole"] * s_h,
                         1.0 if s.get("seam") else _pylon_scale(s_h)))
            continue
        h_eff = PYLON_H_M if s.get("seam") else max(float(s.get("h") or PYLON_H_M) * s_h, 11.5)
        ends.append((np.array([ce, cn]), elev.z_at_eff(ce, cn), h_eff, 1.0 if s.get("seam") else _pylon_scale(s_h)))
    d_min, d_max = min(d_raws), max(d_raws)
    d_mid = 0.5 * (d_min + d_max)
    if mv:
        if d_min > MV_FAR_MAX_M:
            return
    elif tier == "High":
        if d_min > FAR_HV_WIRE_MAX_D_M or d_max > FAR_HV_WIRE_MAX_D_M + 350.0:
            return
    (pa, za0, ha, ka), (pb, zb0, hb, kb) = ends
    L = float(np.hypot(*(pb - pa)))
    if L < 5.0:
        return
    dvec = (pb - pa) / L
    nn = np.array([-dvec[1], dvec[0]])
    mid = (pa + pb) / 2.0
    sec = sectors[sector_of(float(mid[0]), float(mid[1]), half)]
    to_tile = -mid / max(float(np.linalg.norm(mid)), 1e-9)
    normal = np.array([to_tile[0], to_tile[1], 0.0])
    arm_l = _arm_len()
    levels = _arm_levels()
    if mv:
        hmv = S.GROUND_PROP_H["power_pole"]
        hang = [(o, (hmv - 0.3) / hmv) for o in (-0.8, 0.0, 0.8)]
        nseg = min(max(int(math.ceil(L / 22.0)), 3), 5)
        px_frac, max_hw = FAR_MV_WIRE_PX_FRAC, FAR_MV_WIRE_MAX_HALF_W
        f0, f1 = FAR_MV_WIRE_FADE_M
    elif tier == "Low":
        hang = [(sx * arm_l, levels[0][1]) for sx in (-1.0, 1.0)]
        nseg = min(max(int(math.ceil(L / 90.0)), 3), 4)
        px_frac, max_hw = FAR_WIRE_PX_FRAC, FAR_WIRE_MAX_HALF_W
        f0, f1 = FAR_HV_WIRE_FADE_M
    else:
        if d_mid <= FAR_HV_WIRE_FULL_D_M:
            hang = [(sx * arm_l, zf) for _, zf in levels for sx in (-1.0, 1.0)] + [(0.0, 1.0)]
        else:
            # Mid far-field (450..1050 m): 3 main silhouette lines (lowest outer pair + earth) instead of 7 stacked bars
            hang = [(-arm_l, levels[0][1]), (arm_l, levels[0][1]), (0.0, 1.0)]
        nseg = min(max(int(math.ceil(L / 18.0)), 5), 18)
        px_frac, max_hw = FAR_WIRE_PX_FRAC, FAR_WIRE_MAX_HALF_W
        f0, f1 = FAR_HV_WIRE_FADE_M
    col = (*COL_FAR_WIRE, 0.0)
    wire_uv1 = np.full((4, 2), [f0 / 100.0, -(FAR_WIRE_UV1_SENTINEL + f1 / 100.0)], dtype=np.float64)
    for o, zf in hang:
        za, zb = za0 + ha * zf, zb0 + hb * zf
        t, Z, _ = FU.catenary_span(L, za, zb, step=L / nseg)
        Q = pa[None] + (pb - pa)[None] * t[:, None] + nn[None] * (o * (ka * (1.0 - t) + kb * t))[:, None]
        d_out = np.array([outside_dist(float(q[0]), float(q[1]), half)[4] for q in Q])
        d_true = unforeshorten_dist(d_out)
        taper = np.clip(1.0 - 0.50 * np.maximum(d_true - f0, 0.0) / max(f1 - f0, 1.0), 0.45, 1.0)
        hw = np.clip(0.5 * px_frac * FAR_WIRE_PX_M * (d_out + FAR_WIRE_VIEW_M) * taper, FU.WIRE_HALF_W, max_hw)
        for i in range(len(Q) - 1):
            b0 = [Q[i, 0], Q[i, 1], Z[i] - hw[i]]
            b1 = [Q[i + 1, 0], Q[i + 1, 1], Z[i + 1] - hw[i + 1]]
            t1 = [Q[i + 1, 0], Q[i + 1, 1], Z[i + 1] + hw[i + 1]]
            t0 = [Q[i, 0], Q[i, 1], Z[i] + hw[i]]
            f = np.cross(np.subtract(b1, b0), np.subtract(t0, b0))
            if float(np.dot(f, normal)) >= 0.0:
                sec.add_quad0(b0, b1, t1, t0, col, uv1=wire_uv1, normal=normal)
            else:
                sec.add_quad0(b1, b0, t0, t1, col, uv1=wire_uv1, normal=normal)


def _corridor_treelines(half: float = 1024.0, region_id: str = "bialystok-industrial-c") -> list[dict]:
    """Horizon pine stands closing the distant DK8 curve in Las Bacieczki/Pietrasze and framing the western exit
    of bialystok-industrial-c ONLY (ADR 0085 / ADR 0330 r2: never injected into other regions)."""
    if region_id != "bialystok-industrial-c":
        return []
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


def build_apron_masks(gis: dict, elev: BorderElevation, half: float = 1024.0,
                      region_id: str = "bialystok-industrial-c") -> dict:
    """Compute apron vertex ground-mask lookup + border height profile for WorldEdgeBuilder.BuildApron."""
    f_polys = []
    for f in gis["forests"] + _corridor_treelines(half, region_id):
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

    elev = BorderElevation.from_region(region_id, half=half, out_root=out_root)
    gis = extract_ring_gis(region_id, ox, oy, half=half)
    building_exclusion = region_building_exclusion(region_id, ox, oy, half)
    stream_exclusion, stream_inputs = streaming_building_exclusion(ox, oy)
    building_exclusion = shapely.union_all([building_exclusion, stream_exclusion])
    shapely.prepare(building_exclusion)
    source_building_count = len(gis["buildings"])
    # Also filter apron building masks; a rejected proxy must leave no urban scar.
    render_buildings = [b for b in gis["buildings"]
                        if building_rectangle_outside_region(b["rect"], half, building_exclusion)]
    streaming_policy = {
        "schema": "far-field-building-ownership/1",
        "route_clearance_m": STREAMING_ROUTE_CLEARANCE_M,
        "status": "WORKING_VALUE",
        "reserve_all_registered_tiles": True,
        "check_source_and_compressed_footprint": True,
        "source_buildings": source_building_count,
        "retained_buildings": len(render_buildings),
        "excluded_buildings": source_building_count - len(render_buildings),
        "inputs_sha256": stream_inputs,
    }

    # ADR 0351: HV towers + conductor spans (replaces a 27 m tower every 210 m along every ring line, unwired)
    plan = power_plan(gis, half, region_id)

    all_materials = {**SM.M, **FH.materials()}
    FH.far_atlas()                     # ADR 0330 / farfield-low-s24: curtain atlas (no-op when up to date)
    ring_chm = RingChm.for_region(region_id, ox, oy, RING_MAX_M)
    qa_tiers = {}
    landmark_stacks = region_landmark_stacks(region_id, ox, oy)

    for tier, fn, compact in (("High", "far_field.glb", False), ("Low", "far_field.low.glb", True)):
        sectors = {name: SectorBuilder(name) for name in SECTORS}
        skyline = SectorBuilder(SKYLINE, uv1_flag=SKYLINE_FLAG_CLAMP)
        chm_arg = ring_chm if tier == "High" else RingChm(ring_chm.entries)

        for f in gis["forests"] + _corridor_treelines(half, region_id):
            _add_forest_stand(sectors, f["coords"], f.get("mix", "mixed"), elev, half, tier,
                              ring_chm=chm_arg, region_id=region_id)

        for b in render_buildings:
            _add_building(sectors, b, elev, half, tier, exclusion=building_exclusion, skyline=skyline)

        for ch in gis["chimneys"]:
            if any(math.hypot(ch["e"] - st["e"], ch["n"] - st["n"]) < SKYLINE_PROXY_MERGE_M for st in landmark_stacks):
                continue   # the region draws this stack (hero mesh); the skyline carries its far stand-in
            _add_chimney(sectors, ch, elev, half, tier, skyline=skyline)
        for st in landmark_stacks:
            _add_landmark_stack_proxy(skyline, st, elev, tier)
        skyline.sort_far_to_near()

        hv_pylons, hv_spans = _select_far_hv(plan, half, tier)
        for py in hv_pylons:
            _add_pylon(sectors, py, elev, half, tier, yaw=float(py["yaw"]))
        for py in plan["masts"]:
            _add_pylon(sectors, py, elev, half, tier, yaw=float(py.get("yaw", 0.4)), arms=False)
        for a, b in hv_spans:
            _add_span(sectors, a, b, elev, half, tier)
        if tier == "High":
            mv_poles, mv_spans = _select_far_mv(plan, half)
            for s in mv_poles:
                _add_pole(sectors, s, elev, half)
            for a, b in mv_spans:
                _add_span(sectors, a, b, elev, half, tier, mv=True)

        glb = GLB(all_materials, compact=compact)
        sector_stats = {}
        total_tris = 0
        total_verts = 0
        for name in SECTORS:
            prims = sectors[name].primitives(half)
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
        sky_prims = skyline.primitives(half)
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
    apron_info = build_apron_masks({**gis, "buildings": render_buildings}, elev, half, region_id)
    apron_json = {k: v for k, v in apron_info.items() if not k.startswith("_")}
    apron_path = out_root / "far_field_apron.json"
    apron_path.write_text(json.dumps(apron_json, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    # Write SourceManifest in Data/SourceManifests/
    manifest_dir = REPO / "Data" / "SourceManifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    appearance_policy = {
        "schema": "far-field-appearance/2",
        "closed_roofs_all_tiers": True,
        "windowless_roof_fascia_all_tiers": True,
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
        "streaming_building_policy": streaming_policy,
        "ring_bounds_local_m": {"inner_half_m": half, "outer_half_m": RING_MAX_M},
        "region_inputs_sha256": {k: v for k, v in gis["sources_sha256"].items() if k.startswith("region/")},
        "lod1_height_audit": gis["lod1_height_audit"],
        "building_height_sources": gis["building_height_sources"],
        "ring_powiaty": gis["powiaty"],                    # ADR 0219: every powiat the ring bbox overlaps
        "ring_powiaty_missing": gis["powiaty_missing"],    # packages not on disk (ring part from OSM only)
        "osm_lonlat_window": gis["osm_lonlat_window"],
        "sources": [
            {
                "id": "gugik-bdot10k-" + "+".join(gis["powiaty"]),
                "provider": "Główny Urząd Geodezji i Kartografii (GUGiK)",
                "dataset": "BDOT10k powiaty " + ", ".join(gis["powiaty"]) + ": OT_PTLZ_A, OT_BUBD_A, OT_BUWT_P, OT_SULN_L",
                "license": "Open public data — Art. 40a ust. 2 pkt 1 lit. a Prawa geodezyjnego i kartograficznego (Dz.U. 2020 poz. 276)",
                "files": {k: v for k, v in gis["sources_sha256"].items() if k.startswith("bdot10k/")},
            },
            {
                "id": "gugik-lod1-2024-" + "+".join(gis["powiaty"]),
                "provider": "Główny Urząd Geodezji i Kartografii (GUGiK)",
                "dataset": "Modele 3D budynków LoD1 (2024) powiaty " + ", ".join(gis["powiaty"]),
                "license": "Open public data — Art. 40a ust. 2 pkt 1 lit. i Prawa geodezyjnego i kartograficznego",
                "files": {k: v for k, v in gis["sources_sha256"].items() if k.startswith("lod1/")},
            },
            {
                "id": "geofabrik-osm-podlaskie-261108",
                "provider": "OpenStreetMap contributors / Geofabrik GmbH",
                "dataset": "podlaskie-261108.osm.pbf (ring outside the tile, lon/lat window osm_lonlat_window)",
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
            "pylons": len(plan["pylons"]) + len(plan["masts"]),
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
        "power_plan": plan["stats"],
        "forest_chm_ring": ring_chm.stats(),
        "appearance_policy": appearance_policy,
        "streaming_building_policy": streaming_policy,
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
        wm["materials"][FH.FAR_ATLAS_MAT] = FH.materials()[FH.FAR_ATLAS_MAT]      # farfield-low-s24
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
