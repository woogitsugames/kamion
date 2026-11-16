"""Railway track bed and level crossings (ADR 0217): ballast, sleepers, rails in three LoDs + crossing panels and
crossing markers (St Andrew's crosses G-3 / G-4, barriers, lights, bells) as positioned / oriented objects.

Opt-in per region, exactly like the water stage (ADR 0210): `regions.py` Region.rail -> `rail: {enabled: true}` in
region.yaml + Data/Regions/<id>/generated/rail_sources.json, both written by build_region only for regions that opt
in. A region without the key is built exactly as before: no layer gets a part, no material / node / manifest key /
generated file is added (determinism of every existing tile).

Sources (rail_sources.json, small, committed; OSM ODbL):
  ways  railway=rail (gauge, tracks, service, usage, bridge, tunnel, electrified, ref, name);
        railway=disused|abandoned|construction|proposed|razed|narrow_gauge|light_rail|tram and railway=rail with
        disused=yes / abandoned=yes are recorded in `skipped` with the reason, never meshed (ADR 0217 p. 2).
  nodes railway=level_crossing (+ crossing:barrier / crossing:light / crossing:bell / crossing:saltire / supervision);
        railway=crossing (pedestrian / cycle crossing over the track) recorded but not built (no footway mesh).

Numbers. Every dimension below is either cited or WORKING_VALUE (CLAUDE.md rule 3); see ADR 0217 for the sources.
Frame: local E, N, U metres (ADR 0003); the rail profile follows a smoothed ground, pinned to the road surface at
level crossings.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point

from . import rail_textures as RT

SCHEMA = "truck-sim-pl/rail-sources/1"
OUT_SCHEMA = "truck-sim-pl/rail/1"
REPO = Path(__file__).resolve().parents[3]

# ------------------------------------------------------------------------------------------------ dimensions
GAUGE_DEFAULT_MM = 1435.0  # standard gauge; OSM wiki Key:gauge (PL network = 1435 mm except LHS 1520 mm)
RAIL_H = 0.172             # 60E1 rail height 172 mm (EN 13674-1 profile; catalogue moris.eu 60E1: 172 mm)
RAIL_HEAD_W = 0.072        # 60E1 head 72 mm (catalogue figure; head width vs thickness UNVERIFIED in EN 13674-1)
SLEEPER_L = 2.60           # PS-94 prestressed sleeper length 2.6 m (Plastwil / moris.eu PS94/SB/60E1)
SLEEPER_W = 0.30           # WORKING_VALUE (sleeper width at the top)
SLEEPER_H = 0.20           # WORKING_VALUE (visible sleeper body above its bed)
SLEEPER_SPACING = 0.60     # WORKING_VALUE (0.6 m fastening spacing on PS-94, Baztech paper; Id-1 not checked)
SLEEPER_PROUD = 0.05       # WORKING_VALUE: sleeper top above the crib ballast (so LoD0 sleepers read as ribs)
BALLAST_UNDER = 0.30       # WORKING_VALUE (ballast under the sleeper; "zalecana 300 mm" - source not Id-1). Not
#                            geometry: the NMT ground under an existing track IS the ballast surface (see BED_LIFT)
# Visible width of the track band. Measured on the GUGiK orthophoto 2025 (0.1 m) of line 38 at the DW671 crossing,
# 10 cross-sections 40-120 m from the crossing, band = contiguous non-vegetation pixels around the axis
# (artifacts/rail-fix-s21/ortho_measure.py): 3.5-4.5 m, mean 3.9 m (ESTIMATED: grass grows over the toe, pixel 0.1 m).
# Model: crown 2 x (1.30 + BALLAST_SHOULDER) = 3.50 m + 2 x BED_LIFT x BALLAST_SLOPE = 3.86 m where the slope meets the
# conformed ground (FIX 5; the first version stood 0.45 m over the ground and showed 5.65 m of ballast).
BALLAST_SHOULDER = 0.45    # ESTIMATED (orthophoto band 3.9 m; sleeper 2.60 m SOURCED)
BALLAST_SLOPE = 1.5        # WORKING_VALUE (horizontal per vertical, 1:1.5 ballast slope)
BED_LIFT = 0.12            # WORKING_VALUE: ballast top above the ground conformed under the bed (Plan.conform)
SKIRT_M = 0.30             # ballast slope continued this far below the ballast top (0.18 m into the ground)
CONFORM_PAD_M = 0.75       # ground flattened to the bed level this far beyond the crown edge (toe + 0.3 m)
CONFORM_BLEND_M = 3.0      # ... and blended back to the terrain over this distance (WORKING_VALUE)
TRACK_SPACING = 4.00       # WORKING_VALUE (track centre distance on open line; 4.0 m common PL minimum, UNVERIFIED)
TRACK_H = BED_LIFT + SLEEPER_PROUD + RAIL_H           # top of rail above the (smoothed) ground = 0.342 m

# profile
GROUND_SMOOTH_M = 15.0     # WORKING_VALUE: gaussian sigma of the ground under the track (rails cannot follow bumps)
CROSS_BLEND_M = 25.0       # WORKING_VALUE: rail profile blends to the road surface over this distance at a crossing
# LoD steps along the track (m). LoD0 near (<~120 m), LoD1 mid, LoD2 far - switch distances belong to the engine.
LOD_STEP = {0: 5.0, 1: 10.0, 2: 20.0}

# level crossing
PANEL_HALF = SLEEPER_L / 2  # WORKING_VALUE: crossing panels cover the sleeper length on each side of the track axis
PANEL_MARGIN = 0.50         # WORKING_VALUE: panels run this far past the road footprint edge
PANEL_STEP = 0.5            # panel grid along the track (follows the road crown / grade); 2.0 m let the crown poke through (render r2)
PANEL_LIFT = 0.015          # panels / rail heads this much above the sampled road (WORKING_VALUE): the sampler is the 1 m
                            # road_z grid, which clips the crown ridge by up to ~0.01 m (render r4: 0.005 left a notch)
FLANGEWAY = 0.07            # WORKING_VALUE: groove next to the rail head inside the panel field
CROSS_SNAP_M = 8.0          # an OSM level_crossing node within this distance of a rail axis belongs to that track
CROSS_DEDUP_M = 10.0        # a geometric road x rail intersection this close to an OSM node is that node
ROAD_SNAP_M = 15.0          # the road centre line of a crossing must pass within this distance
SIGN_SETBACK = 3.0          # WORKING_VALUE: sign / signal post this far (along the road) before the panel edge
SIGN_LATERAL = 1.0          # WORKING_VALUE: post this far outside the road footprint edge
BARRIER_SETBACK = 2.0       # WORKING_VALUE: barrier post this far before the panel edge
SIGN_ARM_L = 1.20           # WORKING_VALUE: G-3 arm length (regulation drawing not checked)
SIGN_ARM_W = 0.20           # WORKING_VALUE: G-3 arm width
SIGN_ARM_ANGLE = 50.0       # WORKING_VALUE: angle between the arms (deg)
SIGN_BOTTOM_Z = 1.50        # WORKING_VALUE: lower edge of the cross above the road
BARRIERS = ("no", "half", "double_half", "full", "gate", "chain", "yes")
OVERRIDE_KIND = "rail_crossing"      # overrides.yaml: authored facts of one level crossing (Plan._apply_override)
OVERRIDE_KEYS = ("barrier", "light", "light_left", "bell", "saltire", "panel_margin_m", "guide_post",
                 "approach_speed_kmh")
# approach_speed_kmh (ADR 0268): permitted speed on the approaches where the warning sign stands, when the graph has
# no maxspeed tag (attrs.maxspeed.src == "default") - decides the 150-300 m / up-to-100 m rule of the sign distance
# guide_post (ADR 0268): style of the guide posts of the approaches seen on a photo ("red_white"); default U-1a

# Clearance envelope (skrajnia budowli) - simplified cross-section, (lateral m, height above top of rail m).
# UNVERIFIED shape: 4.40 m wide between 0.4 m and 4.0 m above rail, narrowing to the overhead-line zone; replace with
# the exact PN-K-02057 / Id-1 outline when checked. Used for QA (nothing may stand inside) and as a collision outline.
CLEARANCE_PROFILE = [(-1.60, 0.0), (-2.20, 0.40), (-2.20, 4.00), (-1.60, 6.00), (1.60, 6.00), (2.20, 4.00),
                     (2.20, 0.40), (1.60, 0.0)]
CLEARANCE_HALF = max(abs(x) for x, _ in CLEARANCE_PROFILE)

# materials. rail_bed (FIX 3): ONE textured material for the ballast, sleepers and rails of every LoD - the tile
# streetscape.rail_textures.bed() carries crushed stone, the sleepers, fastenings and the rails (colours in the PNG,
# sRGB; `color` 1), so the Low tier (LoD1: ribbon + rail boxes, LoD2: ribbon) reads as a track and the geometric
# sleepers of LoD0 stand on painted ones. UV0 = (0.5 + lateral m / TEX_W_M, along m / TILE_M).
RAIL_MATERIALS = {
    "rail_bed": {"color": [1.0, 1.0, 1.0], "rough": 0.95, "metal": 0.0, "surface": "gravel", "texture": "rail_bed",
                 "note": "ballast + painted sleepers / rails; UV0 = (0.5 + lateral / %.2f m, along / %.2f m)"
                         % (RT.TEX_W_M, RT.SLEEPERS_PER_TILE * SLEEPER_SPACING)},
    "rail_crossing_panel": {"color": [0.16, 0.16, 0.16], "rough": 0.85, "metal": 0.0,
                            "note": "concrete-rubber crossing panels; UV0 = local metres"},
}
BED_MAT = "rail_bed"
TILE_M = RT.SLEEPERS_PER_TILE * SLEEPER_SPACING
LAYERS = ("rail_lod0", "rail_lod1", "rail_lod2", "rail_crossing")
LOW_EXCLUDE = ("rail_lod0",)       # the Low / Medium GLB carries LoD1, LoD2 and the crossing panels only

# OSM tags copied into rail_sources.json (pbf extract and OSM API 0.6 XML extract use the same list; ADR 0217 / 0223)
KEEP_TAGS = ("railway", "gauge", "tracks", "service", "usage", "bridge", "tunnel", "layer", "electrified", "voltage",
             "maxspeed", "railway:track_ref", "ref", "name", "disused", "abandoned", "crossing:barrier",
             "crossing:light", "crossing:bell", "crossing:saltire", "crossing:activation", "supervision")

# ADR 0223: level-crossing equipment / category from the OSM crossing tags. Categories A-F: Dz.U. 2025 poz. 1105
# (rozporządzenie MI z 9.07.2025, in force since 27.08.2025; it replaced Dz.U. 2015 poz. 1744) § 6 ust. 1:
#   A - traffic directed by railway staff, by hand signals or by systems with barriers closing the WHOLE road width and
#       road signals (lit. b); B - automatic systems with road signals and barriers closing the entry (a) or the entry
#       and the exit (b); C - automatic systems with road signals only; D - no crossing systems, road signs only;
#   E - pedestrian crossings (przejścia); F - crossings on internal roads (not inferable from OSM tags alone).
# Signs G-3 / G-4: § 80 ust. 1 (A without barriers, C, D); G-2 on electrified lines: § 81 ust. 1 (A-C on the signal
# mast, D on the G-3 / G-4 post below the cross).
EQUIPMENT = {
    "full": ("rogatki_pelne", "A", "§ 6 ust. 1 pkt 1 lit. b (barriers over the whole road width)"),
    "gate": ("rogatki_pelne", "A", "§ 6 ust. 1 pkt 1 lit. b (gate over the whole road width)"),
    "half": ("polrogatki", "B", "§ 6 ust. 1 pkt 2 lit. a (entry barriers)"),
    "double_half": ("polrogatki_wjazd_wyjazd", "B", "§ 6 ust. 1 pkt 2 lit. b (entry + exit barriers)"),
    "yes": ("rogatki_typ_nieznany", "A|B", "crossing:barrier=yes: barriers of unknown type (§ 6 ust. 1 pkt 1-2)"),
    "chain": ("rogatki_typ_nieznany", "A|F", "crossing:barrier=chain (§ 12 ust. 3 pkt 1: kept-closed barriers)"),
}

SKIP_RAILWAY = ("disused", "abandoned", "construction", "proposed", "razed", "narrow_gauge", "light_rail", "tram",
                "subway", "miniature", "funicular", "monorail", "preserved")


# ------------------------------------------------------------------------------------------------ tags
def _num(v):
    if v is None:
        return None
    m = re.match(r"\s*([0-9]+(?:[.,][0-9]+)?)", str(v))
    return float(m.group(1).replace(",", ".")) if m else None


def classify_way(tags: dict) -> tuple[bool, str, dict]:
    """(keep, reason, attributes) for one OSM way with a `railway` tag."""
    rw = tags.get("railway")
    if rw != "rail":
        return False, f"railway={rw}", {}
    for k in ("disused", "abandoned"):
        if tags.get(k) == "yes":
            return False, f"{k}=yes", {}
    if tags.get("tunnel") in ("yes", "building_passage"):
        return False, "tunnel (not modelled)", {}
    g = _num(str(tags.get("gauge", "")).split(";")[0])
    gauge_src = "osm"
    if g is None or not 600 <= g <= 1700:
        g, gauge_src = GAUGE_DEFAULT_MM, "default"
    tr = _num(tags.get("tracks"))
    n = int(tr) if tr and tr >= 1 else 1
    n = min(n, 6)
    return True, "", {"gauge_mm": g, "gauge_src": gauge_src, "tracks": n,
                      "tracks_src": "osm" if tr and tr >= 1 else "default",
                      "maxspeed_kmh": _num(tags.get("maxspeed")),
                      "service": tags.get("service"), "usage": tags.get("usage"),
                      "bridge": tags.get("bridge") not in (None, "no"),
                      "electrified": tags.get("electrified"), "ref": tags.get("ref"), "name": tags.get("name")}


def classify_node(tags: dict) -> tuple[bool, str, dict]:
    """(keep, reason, attributes) for one OSM node with a `railway` tag."""
    rw = tags.get("railway")
    if rw == "crossing":
        return False, "railway=crossing (pedestrian/cycle crossing; no footway mesh)", {}
    if rw != "level_crossing":
        return False, f"railway={rw}", {}
    bar = tags.get("crossing:barrier")
    if bar not in BARRIERS:
        bar = None                          # unknown / untagged
    yes = ("yes", "true")
    at = {"barrier": bar,
          "light": tags.get("crossing:light") in yes,
          "bell": tags.get("crossing:bell") in yes,
          "saltire": (None if tags.get("crossing:saltire") is None
                      else tags.get("crossing:saltire") in yes),
          "supervision": tags.get("supervision")}
    at.update(crossing_equipment(bar, tags.get("crossing:light")))
    return True, "", at


def crossing_equipment(barrier, light_tag, src="osm") -> dict:
    """ADR 0223: equipment type + category (Dz.U. 2025 poz. 1105 § 6 ust. 1) of a level crossing from
    crossing:barrier and the RAW crossing:light value (None = untagged). Every result carries its provenance:
    `equipment_src` osm (barrier tag read) / derived (inferred from the light tag) / default (nothing tagged) /
    authored_override (overrides.yaml, see Plan._apply_override) and a confidence."""
    light_yes = light_tag in ("yes", "true")
    light_no = light_tag in ("no", "false")
    if barrier in EQUIPMENT:
        eq, cat, basis = EQUIPMENT[barrier]
        return {"equipment": eq, "category": cat, "equipment_src": src,
                "equipment_confidence": "medium" if cat in ("A", "B") else "low", "category_basis": basis}
    if barrier == "no":
        if light_yes:
            return {"equipment": "sygnalizacja_swietlna", "category": "C", "equipment_src": src,
                    "equipment_confidence": "medium", "category_basis": "§ 6 ust. 1 pkt 3 (road signals only)"}
        if light_no:
            return {"equipment": "brak", "category": "D", "equipment_src": src, "equipment_confidence": "medium",
                    "category_basis": "§ 6 ust. 1 pkt 4 (no crossing systems, road signs only)"}
        return {"equipment": "brak_rogatek_swiatla_nieznane", "category": "C|D", "equipment_src": src,
                "equipment_confidence": "low", "category_basis": "no barriers; crossing:light untagged"}
    # barrier untagged
    if light_yes:
        return {"equipment": "sygnalizacja_swietlna_rogatki_nieznane", "category": "A|B|C",
                "equipment_src": "derived" if src == "osm" else src, "equipment_confidence": "low",
                "category_basis": "crossing:light=yes, crossing:barrier untagged"}
    if light_no:
        # A with barriers, B and C all have road signals (§ 6 ust. 1 pkt 1 lit. b, pkt 2, pkt 3), so a crossing
        # without lights is D (or A directed by hand signals - not modelled)
        return {"equipment": "brak", "category": "D", "equipment_src": "derived" if src == "osm" else src,
                "equipment_confidence": "low",
                "category_basis": "crossing:light=no + § 6 ust. 1: A (barriers) / B / C always have road signals"}
    return {"equipment": "nieznane", "category": None, "equipment_src": "default", "equipment_confidence": "low",
            "category_basis": "crossing:barrier and crossing:light untagged: rendered with signs only (as D)"}


# ------------------------------------------------------------------------------------------------ extraction
def extract_osm(bbox, pbf: Path) -> dict:
    import osmium
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    tile = shapely.box(*bbox).buffer(100.0, join_style="mitre")
    keep = KEEP_TAGS
    ways, nodes = [], []
    fp = osmium.FileProcessor(str(pbf)).with_locations().with_filter(osmium.filter.KeyFilter("railway"))
    for obj in fp:
        t = obj.tags
        tags = {k: t.get(k) for k in keep if t.get(k) is not None}
        if obj.is_node():
            if not obj.location.valid():
                continue
            x, y = tr.transform(obj.location.lon, obj.location.lat)
            if tile.contains(Point(x, y)):
                nodes.append({"osm_node": obj.id, "tags": tags, "xy": [round(x, 2), round(y, 2)]})
        elif obj.is_way():
            try:
                pts = [tr.transform(n.location.lon, n.location.lat) for n in obj.nodes]
            except osmium.InvalidLocationError:
                continue
            if len(pts) < 2:
                continue
            g = LineString(pts).intersection(tile)
            for k, part in enumerate(_parts(g)):
                if part.geom_type == "LineString" and part.length >= 1.0:
                    ways.append({"osm_way": obj.id, "part": k, "tags": tags,
                                 "coords": [[round(x, 2), round(y, 2)] for x, y in part.simplify(0.1).coords]})
    ways.sort(key=lambda d: (d["osm_way"], d["part"]))
    nodes.sort(key=lambda d: d["osm_node"])
    return {"ways": ways, "nodes": nodes}


def extract_osm_xml(bbox, xml_paths) -> dict:
    """ADR 0223: the same output as extract_osm, from OSM API 0.6 XML files (`/map?bbox=` cut-outs and
    `/way/<id>/full`), for tiles whose sources were taken from the live API instead of the pbf snapshot. Several files
    are merged (an element present in more than one file must be identical - the newest `version` wins)."""
    import xml.etree.ElementTree as ET
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    tile = shapely.box(*bbox).buffer(100.0, join_style="mitre")
    loc, ntags, wdef = {}, {}, {}
    for path in xml_paths:
        root = ET.parse(path).getroot()
        for n in root.iter("node"):
            i, v = int(n.get("id")), int(n.get("version", 0))
            if i in loc and loc[i][1] >= v:
                continue
            loc[i] = ((float(n.get("lon")), float(n.get("lat"))), v)
            ntags[i] = {c.get("k"): c.get("v") for c in n.iter("tag")}
        for w in root.iter("way"):
            i, v = int(w.get("id")), int(w.get("version", 0))
            if i in wdef and wdef[i][2] >= v:
                continue
            wdef[i] = ([int(c.get("ref")) for c in w.iter("nd")], {c.get("k"): c.get("v") for c in w.iter("tag")}, v)
    ways, nodes = [], []
    for i, t in ntags.items():
        if "railway" not in t:
            continue
        x, y = tr.transform(*loc[i][0])
        if tile.contains(Point(x, y)):
            nodes.append({"osm_node": i, "tags": {k: t[k] for k in KEEP_TAGS if k in t},
                          "xy": [round(x, 2), round(y, 2)]})
    for i, (nds, t, _) in wdef.items():
        if "railway" not in t or any(n not in loc for n in nds) or len(nds) < 2:
            continue
        pts = [tr.transform(*loc[n][0]) for n in nds]
        g = LineString(pts).intersection(tile)
        for k, part in enumerate(_parts(g)):
            if part.geom_type == "LineString" and part.length >= 1.0:
                ways.append({"osm_way": i, "part": k, "tags": {kk: t[kk] for kk in KEEP_TAGS if kk in t},
                             "coords": [[round(x, 2), round(y, 2)] for x, y in part.simplify(0.1).coords]})
    ways.sort(key=lambda d: (d["osm_way"], d["part"]))
    nodes.sort(key=lambda d: d["osm_node"])
    return {"ways": ways, "nodes": nodes}


def extract(region: dict) -> dict:
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from fetch_osm import download
    b = region["bbox"]
    bbox = (b["xmin"], b["ymin"], b["xmax"], b["ymax"])
    pbf = download()
    return {"schema": SCHEMA, "crs": "EPSG:2180", "bbox": list(bbox), "margin_m": 100.0,
            "license": {"osm": "ODbL 1.0, © OpenStreetMap contributors"},
            "provenance": {"source": "osm-pbf", "file": pbf.name,
                           "manifest": "Data/SourceManifests/osm-geofabrik-podlaskie.json"},
            "osm": extract_osm(bbox, pbf)}


def sources_path(region_id: str) -> Path:
    return REPO / "Data" / "Regions" / region_id / "generated" / "rail_sources.json"


def write(region_id: str, data: dict) -> Path:
    p = sources_path(region_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if not p.exists() or p.read_text(encoding="utf-8") != text:
        p.write_text(text, encoding="utf-8", newline="\n")
    return p


def enabled(region: dict) -> bool:
    """The stage runs only for regions that opted in (region.yaml `rail: {enabled: true}`)."""
    r = region.get("rail")
    return bool(isinstance(r, dict) and r.get("enabled"))


def load(region_id: str) -> dict | None:
    p = sources_path(region_id)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _parts(g):
    if g.is_empty:
        return []
    if hasattr(g, "geoms"):
        out = []
        for p in g.geoms:
            out += _parts(p)
        return out
    return [g]


# ------------------------------------------------------------------------------------------------ samplers
def grid_sampler(grid, hf, fallback=None, reach=3):
    """f(E, N) arrays -> bilinear value of a node grid (rows = north->south, like the heightfield); nodes that are not
    finite (road_z off the road = -inf) are filled from the nearest finite node within `reach` nodes, else from
    `fallback(E, N)`."""
    from scipy import ndimage
    g = np.asarray(grid, float)
    bad = ~np.isfinite(g)
    if bad.any() and (~bad).any():
        d, (jj, ii) = ndimage.distance_transform_edt(bad, return_indices=True)
        filled = g[jj, ii]
        filled[d > reach] = np.nan
        g = np.where(bad, filled, g)

    def f(e, n):
        e = np.asarray(e, float)
        n = np.asarray(n, float)
        fi = np.clip(e - hf.x0, 0, g.shape[1] - 1.001)
        fj = np.clip(hf.y1 - n, 0, g.shape[0] - 1.001)
        i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
        a, b = fi - i0, fj - j0
        v = ((1 - a) * (1 - b) * g[j0, i0] + a * (1 - b) * g[j0, i0 + 1] + (1 - a) * b * g[j0 + 1, i0]
             + a * b * g[j0 + 1, i0 + 1])
        if fallback is not None and np.isnan(v).any():
            v = np.where(np.isnan(v), fallback(e, n), v)
        return v
    return f


# ------------------------------------------------------------------------------------------------ geometry helpers
def _heading(v) -> float:
    """Compass heading (deg clockwise from north) of a local (E, N) vector."""
    return round(math.degrees(math.atan2(float(v[0]), float(v[1]))) % 360.0, 2)


def _frame(line: LineString, s):
    s = np.asarray(s, float)
    P = np.array([line.interpolate(x).coords[0] for x in s])
    if len(P) < 2:
        T = np.array([[1.0, 0.0]])
    else:
        T = np.gradient(P, axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    Nl = np.column_stack([-T[:, 1], T[:, 0]])          # left normal
    return P, T, Nl


def _deck_z(road_z_at, x, y):
    """Road surface under a panel / rail vertex: the highest of the point and 4 points PANEL_STEP / 2 around it, so a
    ribbon that is linear between its stations never dips under the crown ridge of the carriageway (render r3: with
    the point sample alone the crown showed through the panels as a notch along the road axis). Raises the deck by
    at most PANEL_STEP / 2 x gradient (5 mm at 2 % cross-fall) over the asphalt."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    h = PANEL_STEP / 2
    z = road_z_at(x, y)
    for dx, dy in ((h, 0.0), (-h, 0.0), (0.0, h), (0.0, -h)):
        z = np.maximum(z, road_z_at(x + dx, y + dy))
    return z


def _stations(length, step, extra=()):
    n = max(1, int(math.ceil(length / step - 1e-9)))
    s = np.linspace(0.0, length, n + 1)
    if extra:
        s = np.unique(np.concatenate([s, np.clip(np.asarray(extra, float), 0, length)]))
        s = s[np.concatenate([[True], np.diff(s) > 1e-3])]
    return s


def _ribbon(P, Nl, Z, lat, dz):
    """Vertices / triangles of a strip ribbon: lateral offsets `lat` (k), heights Z + dz (k) per station; returns
    V (n*k, 3), T, UV (lateral, along)."""
    n, k = len(P), len(lat)
    lat = np.asarray(lat, float)
    dz = np.asarray(dz, float)
    V = (P[:, None, :] + Nl[:, None, :] * lat[None, :, None]).reshape(-1, 2)
    Zv = (Z[:, None] + dz[None, :]).reshape(-1)
    along = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    UV = np.column_stack([np.tile(lat, n), np.repeat(along, k)])
    r, c = np.meshgrid(np.arange(n - 1), np.arange(k - 1), indexing="ij")
    a = (r * k + c).ravel()
    b = ((r + 1) * k + c).ravel()
    cc = ((r + 1) * k + c + 1).ravel()
    d = (r * k + c + 1).ravel()
    # lateral grows to the LEFT (Nl), stations forward: (a, cc, d) and (a, b, cc) are CCW seen from above / outside
    T = np.concatenate([np.column_stack([a, cc, d]), np.column_stack([a, b, cc])])
    return np.column_stack([V, Zv]), UV, T


def _keep_segments(T, k, seg_ok):
    """Drop the triangles of ribbon segments (station i -> i+1) where seg_ok[i] is False."""
    seg = T.min(axis=1) // k
    return T[seg_ok[seg]]


# ------------------------------------------------------------------------------------------------ plan
class Track:
    def __init__(self, src: dict, origin, attrs: dict):
        self.id = f"osm:way/{src['osm_way']}:{src['part']}"
        self.line = LineString(np.asarray(src["coords"], float) - np.asarray(origin, float))
        self.a = attrs
        n = attrs["tracks"]
        self.offsets = [(k - (n - 1) / 2.0) * TRACK_SPACING for k in range(n)]
        self.gauge = attrs["gauge_mm"] / 1000.0
        self.zones = []          # [(s_a, s_b, crossing index)]

    @property
    def half_top(self):
        return max(abs(o) for o in self.offsets) + SLEEPER_L / 2 + BALLAST_SHOULDER

    def rail_lats(self):
        """Lateral centre of every rail head (2 per track)."""
        h = self.gauge / 2 + RAIL_HEAD_W / 2
        return sorted(o + sgn * h for o in self.offsets for sgn in (-1, 1))


class Plan:
    """Rail tracks and level crossings of one region in local metres (E, N)."""

    def __init__(self, src: dict, origin, tile_local=None, road_poly=None, road_lines=(), overrides=()):
        self.origin = np.asarray(origin, float)
        self.tile_local = tile_local
        self.overrides = [dict(o) for o in (overrides or ()) if o.get("kind") == OVERRIDE_KIND]
        self.ground_grid = None      # smoothed ground the profile stands on (set by conform(); build_world samples it)
        self._conform_mask = None
        self.road_poly = road_poly if road_poly is not None else shapely.Polygon()
        self.road_lines = list(road_lines)
        self.report = {"tracks": [], "skipped": [], "crossings": [], "markers": [], "warnings": []}
        osm = src.get("osm", src)
        self.tracks = []
        for wsrc in osm.get("ways", []):
            keep, why, at = classify_way(wsrc.get("tags", {}))
            sid = f"osm:way/{wsrc['osm_way']}:{wsrc.get('part', 0)}"
            if not keep:
                if wsrc.get("tags", {}).get("railway") is not None:
                    self.report["skipped"].append({"src": sid, "why": why})
                continue
            wsrc = {**wsrc, "part": wsrc.get("part", 0)}
            t = Track(wsrc, origin, at)
            if tile_local is not None:
                g = t.line.intersection(tile_local)
                if g.is_empty:
                    continue
                if g.geom_type != "LineString":
                    g = max(_parts(g), key=lambda q: q.length)
                t.line = g
            self.tracks.append(t)
            self.report["tracks"].append({"src": t.id, "length_m": round(t.line.length, 1), **at})
        self.nodes = []
        for nd in osm.get("nodes", []):
            keep, why, at = classify_node(nd.get("tags", {}))
            sid = f"osm:node/{nd['osm_node']}"
            if not keep:
                self.report["skipped"].append({"src": sid, "why": why})
                continue
            self.nodes.append({"src": sid, "p": np.asarray(nd["xy"], float) - self.origin, **at,
                               "_light_tag": nd.get("tags", {}).get("crossing:light")})
        self.crossings = self._find_crossings()
        for o in self.overrides:
            if not o.pop("_used", False):
                # ADR 0223: a target that is gone from the sources is reported, never dropped silently
                self.report.setdefault("overrides_stale", []).append(o.get("id"))
                self.report["warnings"].append({"src": f"override:{o.get('id')}", "why": "rail_crossing override "
                                                "matches no level crossing of this region"})

    def _apply_override(self, c):
        """Authored facts of one crossing (overrides.yaml `kind: rail_crossing`, survives every regeneration):
        target {osm_node: id} or {near_epsg2180: [x, y], radius_m}; set {barrier, light, light_left, bell, saltire,
        panel_margin_m}. OSM stays the default; the override wins and is named in rail.json."""
        for o in self.overrides:
            tg = o.get("target") or {}
            hit = False
            if tg.get("osm_node") is not None:
                ids = tg["osm_node"] if isinstance(tg["osm_node"], list) else [tg["osm_node"]]
                hit = c["src"] in {f"osm:node/{i}" for i in ids}
            elif tg.get("near_epsg2180") is not None:
                q = np.asarray(tg["near_epsg2180"], float) - self.origin
                hit = float(np.linalg.norm(q - np.asarray(c["p"], float))) <= float(tg.get("radius_m", 15.0))
            if not hit:
                continue
            st = o.get("set") or {}
            bad = sorted(set(st) - set(OVERRIDE_KEYS))
            if bad:
                raise ValueError(f"override {o.get('id')}: unknown rail_crossing keys {bad}")
            if "barrier" in st and st["barrier"] not in BARRIERS + (None,):
                raise ValueError(f"override {o.get('id')}: barrier {st['barrier']!r} not in {BARRIERS}")
            c = {**c, **st, "override": o.get("id")}
            # ADR 0223: equipment / category (Dz.U. 2025 poz. 1105 § 6 ust. 1) follow the authored facts
            light_tag = ("yes" if st["light"] else "no") if "light" in st else c.get("_light_tag")
            c.update(crossing_equipment(c["barrier"], light_tag, src="authored_override"))
            c["equipment_src"] = "authored_override"
            c["equipment_confidence"] = o.get("confidence", "medium")
            o["_used"] = True
            self.report.setdefault("overrides_applied", []).append({"id": o.get("id"), "target": c["src"]})
        return c

    # -------------------------------------------------------------------------------------------- crossings
    def _find_crossings(self):
        out = []
        used = set()
        for nd in self.nodes:
            best = None
            for ti, t in enumerate(self.tracks):
                d = t.line.distance(Point(nd["p"]))
                if d <= CROSS_SNAP_M and (best is None or d < best[0]):
                    best = (d, ti)
            if best is None:
                self.report["warnings"].append({"src": nd["src"], "why": "level_crossing node far from any rail"})
                continue
            out.append({**nd, "track": best[1], "source": "osm"})
        # geometric intersections of the rail axis with ground road centre lines without an OSM node
        for ti, t in enumerate(self.tracks):
            if t.a["bridge"]:
                continue
            for rl in self.road_lines:
                for q in _parts(t.line.intersection(rl)):
                    pts = [q] if q.geom_type == "Point" else [Point(c) for c in getattr(q, "coords", [])]
                    for pt in pts:
                        p = np.asarray(pt.coords[0], float)
                        if any(np.linalg.norm(c["p"] - p) < CROSS_DEDUP_M for c in out):
                            continue
                        key = (ti, round(p[0], 1), round(p[1], 1))
                        if key in used:
                            continue
                        used.add(key)
                        out.append({"src": "geometry", "p": p, "track": ti, "source": "geometry", "barrier": None,
                                    "light": False, "bell": False, "saltire": None, "supervision": None,
                                    **crossing_equipment(None, None)})
                        self.report["warnings"].append({"src": f"geometry {p.round(1).tolist()}",
                                                        "why": "road x rail without OSM level_crossing node: "
                                                               "barrier unknown, signed as category D"})
        out.sort(key=lambda c: (round(float(c["p"][0]), 1), round(float(c["p"][1]), 1)))
        res = []
        for c in out:
            c = self._apply_override(c)
            pm = float(c.get("panel_margin_m", PANEL_MARGIN))
            t = self.tracks[c["track"]]
            s_c = t.line.project(Point(c["p"]))
            pc = np.asarray(t.line.interpolate(s_c).coords[0])
            _, T, _ = _frame(t.line, [max(0, s_c - 1), min(t.line.length, s_c + 1)])
            tdir = T.mean(0)
            tdir /= np.linalg.norm(tdir)
            # road at the crossing: nearest ground road centre line
            rdir, rl_best = None, None
            for rl in self.road_lines:
                d = rl.distance(Point(pc))
                if d <= ROAD_SNAP_M and (rl_best is None or d < rl_best[0]):
                    rl_best = (d, rl)
            if rl_best is not None:
                rl = rl_best[1]
                sr = rl.project(Point(pc))
                a_ = np.asarray(rl.interpolate(max(0, sr - 2)).coords[0])
                b_ = np.asarray(rl.interpolate(min(rl.length, sr + 2)).coords[0])
                rdir = (b_ - a_) / max(np.linalg.norm(b_ - a_), 1e-9)
            else:
                rdir = np.array([-tdir[1], tdir[0]])        # no road line: assume square crossing
                self.report["warnings"].append({"src": c["src"], "why": "no road centre line near the crossing"})
            sin_t = max(abs(float(tdir[0] * rdir[1] - tdir[1] * rdir[0])), 0.2)    # >= ~11.5 deg (very skew crossings clamped)
            # panel zone along the track = the road footprint (+ margin) on the track axis around the crossing
            zone = None
            if not self.road_poly.is_empty:
                pieces = _parts(t.line.intersection(self.road_poly.buffer(pm)))
                pieces = [q for q in pieces if q.geom_type == "LineString"]
                if pieces:
                    q = min(pieces, key=lambda q: q.distance(Point(pc)))
                    if q.distance(Point(pc)) < 2.0:
                        ss = sorted(t.line.project(Point(xy)) for xy in q.coords)
                        zone = (ss[0], ss[-1])
            if zone is None:
                zone = (s_c - 4.0 / sin_t, s_c + 4.0 / sin_t)    # WORKING_VALUE: 7 m road + margins
            zone = (max(0.0, zone[0]), min(t.line.length, zone[1]))
            road_w = max((zone[1] - zone[0] - 2 * pm) * sin_t, 3.0)
            # the whole bundle crossing this road: tracks of all rail ways whose axis passes the crossing
            n_tracks = sum(tt.a["tracks"] for tt in self.tracks if tt.line.distance(Point(pc)) <= CROSS_SNAP_M
                           + TRACK_SPACING * (tt.a["tracks"] - 1) / 2)
            electrified = any(tt.a.get("electrified") not in (None, "no") for tt in self.tracks
                              if tt.line.distance(Point(pc)) <= CROSS_SNAP_M + TRACK_SPACING * (tt.a["tracks"] - 1) / 2)
            ci = len(res)
            t.zones.append((zone[0], zone[1], ci))
            res.append({**c, "p": pc, "s": s_c, "tdir": tdir, "rdir": rdir, "sin": sin_t, "zone": zone,
                        "road_w": road_w, "n_tracks": int(max(n_tracks, t.a["tracks"])), "electrified": electrified,
                        "half_track": max(abs(o) for o in t.offsets) + PANEL_HALF})
        return res

    def sign_code(self, c) -> str | None:
        """G-3 (single track) / G-4 (multiple tracks) where the crossing has no barriers (Dz.U. 2025 poz. 1105 § 80 ust. 1:
        A without barriers, C, D); an explicit OSM crossing:saltire overrides."""
        show = c["barrier"] in (None, "no") if c["saltire"] is None else c["saltire"]
        if not show:
            return None
        return "G-3" if c["n_tracks"] <= 1 else "G-4"

    # -------------------------------------------------------------------------------------------- profile
    def _tor(self, t: Track, P, s, ground_at, road_z_at):
        """Top of rail at the stations: smoothed ground + TRACK_H; linear on bridges; pinned to the road surface
        (+ PANEL_LIFT) inside a crossing zone and blended over CROSS_BLEND_M outside it."""
        z = ground_at(P[:, 0], P[:, 1]) + TRACK_H
        if t.a["bridge"]:
            z = np.interp(s, [s[0], s[-1]], [z[0], z[-1]])
        for (sa, sb, ci) in t.zones:
            c = self.crossings[ci]
            zr = float(road_z_at(np.array([c["p"][0]]), np.array([c["p"][1]]))[0]) + PANEL_LIFT
            d = np.maximum(np.maximum(sa - s, s - sb), 0.0)
            wgt = np.clip(1.0 - d / CROSS_BLEND_M, 0.0, 1.0)
            z = (1 - wgt) * z + wgt * zr
            inz = (s >= sa - 1e-6) & (s <= sb + 1e-6)
            if inz.any():
                z[inz] = _deck_z(road_z_at, P[inz, 0], P[inz, 1]) + PANEL_LIFT
        return z

    # -------------------------------------------------------------------------------------------- meshes
    def build(self, buf, ground_at, road_z_at, log=print):
        """Add the track bed (rail_lod0/1/2) and the crossing panels (rail_crossing) to `buf`; fill the report
        (triangles per LoD, crossings, markers, clearance)."""
        tris = {k: 0 for k in LAYERS}
        for t in self.tracks:
            L = t.line.length
            for lod in (0, 1, 2):
                extra = []
                for (sa, sb, _) in t.zones:
                    extra += [sa, sb] + list(np.arange(sa, sb, PANEL_STEP))
                s = _stations(L, LOD_STEP[lod], extra)
                P, _, Nl = _frame(t.line, s)
                tor = self._tor(t, P, s, ground_at, road_z_at)
                mid = 0.5 * (s[:-1] + s[1:])
                in_zone = np.zeros(len(mid), bool)
                for (sa, sb, _) in t.zones:
                    in_zone |= (mid > sa) & (mid < sb)
                layer = f"rail_lod{lod}"
                tris[layer] += self._ballast(buf, layer, t, P, Nl, tor, ~in_zone, lod)
                if lod <= 1:
                    tris[layer] += self._rails(buf, layer, t, P, Nl, s, tor, road_z_at)
                if lod == 0:
                    tris[layer] += self._sleepers(buf, layer, t, ground_at, road_z_at)
        for ci, c in enumerate(self.crossings):
            n = self._panels(buf, ci, c, road_z_at)
            tris["rail_crossing"] += n
            code = self.sign_code(c)
            self.report["crossings"].append({
                "id": ci, "src": c["src"], "source": c["source"],
                "e": round(float(c["p"][0]), 2), "n": round(float(c["p"][1]), 2),
                "z_road": round(float(road_z_at(np.array([c["p"][0]]), np.array([c["p"][1]]))[0]), 3),
                "track_heading_deg": _heading(c["tdir"]), "road_heading_deg": _heading(c["rdir"]),
                "tracks": c["n_tracks"], "barrier": c["barrier"], "light": c["light"], "bell": c["bell"],
                "equipment": c.get("equipment"), "category": c.get("category"),
                "equipment_src": c.get("equipment_src"), "equipment_confidence": c.get("equipment_confidence"),
                "category_basis": c.get("category_basis"), "override": c.get("override"),
                "electrified": c.get("electrified", False),
                "sign": code, "road_width_m": round(c["road_w"], 2),
                "panel_zone_m": [round(c["zone"][0], 2), round(c["zone"][1], 2)], "panel_triangles": n})
            self.report["markers"] += self.markers(ci, c, road_z_at, self.report.setdefault("markers_outside_tile", []))
            if any(m["crossing"] == ci for m in self.report.get("markers_outside_tile", [])):
                self.report["warnings"].append({"src": c["src"], "why": "crossing on the tile edge: markers of the "
                                                "outer approach dropped (markers_outside_tile)"})
        self.report["triangles"] = tris
        km = sum(t.line.length for t in self.tracks) / 1000.0
        self.report["track_km"] = round(km, 3)
        self.report["clearance"] = {"profile_m": [list(p) for p in CLEARANCE_PROFILE],
                                    "frame": "(lateral from track axis, height above top of rail)",
                                    "status": "UNVERIFIED simplified structure gauge (ADR 0217)",
                                    "min_marker_distance_m": self.min_marker_clearance()}
        log("rail", {"tracks": len(self.tracks), "km": round(km, 2), "crossings": len(self.crossings),
                     "markers": len(self.report["markers"]), "triangles": tris})
        return tris

    def _ballast(self, buf, layer, t, P, Nl, tor, seg_ok, lod):
        """Bed ribbons with the UVs of the rail_bed tile: one top strip per track (u is measured from that track's
        axis, so every track gets its painted sleepers and rails) + the two slopes (LoD0 / LoD1) or the top strips
        widened to where the slope meets the ground (LoD2)."""
        top = -(RAIL_H + SLEEPER_PROUD)                      # TOR -> ballast top
        bt = t.half_top
        offs = sorted(t.offsets)
        mids = [0.5 * (a + b) for a, b in zip(offs[:-1], offs[1:])]
        edge = bt if lod < 2 else bt + BED_LIFT * BALLAST_SLOPE
        bounds = [-edge] + mids + [edge]
        strips = [(bounds[k], bounds[k + 1], offs[k], top, top) for k in range(len(offs))]
        if lod < 2:
            toe = bt + SKIRT_M * BALLAST_SLOPE
            strips = ([(-toe, -bt, offs[0], top - SKIRT_M, top)] + strips + [(bt, toe, offs[-1], top, top - SKIRT_M)])
        n = 0
        for l0, l1, axis, z0, z1 in strips:
            V, UV, T = _ribbon(P, Nl, tor, [l0, l1], [z0, z1])
            T = _keep_segments(T, 2, seg_ok)
            UV = np.column_stack([0.5 + (UV[:, 0] - axis) / RT.TEX_W_M, UV[:, 1] / TILE_M])
            buf.add(layer, BED_MAT, V, UV, T, src=f"rail:{t.id}:ballast")
            n += len(T)
        return int(n)

    def _rails(self, buf, layer, t, P, Nl, s, tor, road_z_at):
        n = 0
        hw = RAIL_HEAD_W / 2
        for c in t.rail_lats():
            # top, outer and inner faces as one 4-edge ribbon: (c-hw, low) (c-hw, top) (c+hw, top) (c+hw, low)
            lat = [c - hw, c - hw, c + hw, c + hw]
            dz = [-RAIL_H, 0.0, 0.0, -RAIL_H]
            V, UV, T = _ribbon(P, Nl, tor, lat, dz)
            # inside crossing zones the heads sit on the road surface at their own position (crown / cross-fall)
            if t.zones:
                Pk = V[:, :2]
                sk = np.repeat(s, 4)
                inz = np.zeros(len(sk), bool)
                for (sa, sb, _) in t.zones:
                    inz |= (sk >= sa - 1e-6) & (sk <= sb + 1e-6)
                if inz.any():
                    top = _deck_z(road_z_at, Pk[inz, 0], Pk[inz, 1]) + PANEL_LIFT
                    V[inz, 2] = top + np.tile(dz, len(s))[inz]
            # the rail samples its own painted rail in the rail_bed tile (always the 1435 mm one): polished running
            # band on the top face, rust on the sides -> the whole track is ONE material (1 draw per chunk and LoD)
            UV = np.column_stack([np.tile(RT.rail_u(c > min(t.offsets, key=lambda o: abs(o - c))), len(s)),
                                  UV[:, 1] / TILE_M])
            buf.add(layer, BED_MAT, V, UV, T, src=f"rail:{t.id}:rail")
            n += len(T)
        return int(n)

    def _sleepers(self, buf, layer, t, ground_at, road_z_at):
        L = t.line.length
        s = np.arange(SLEEPER_SPACING / 2, L, SLEEPER_SPACING)
        keep = np.ones(len(s), bool)
        for (sa, sb, _) in t.zones:
            keep &= ~((s > sa - SLEEPER_W) & (s < sb + SLEEPER_W))
        s = s[keep]
        if not len(s):
            return 0
        P, T_, Nl = _frame(t.line, s)
        tor = self._tor(t, P, s, ground_at, road_z_at)
        top = tor - RAIL_H
        low = top - SLEEPER_PROUD
        hl, hw = SLEEPER_L / 2, SLEEPER_W / 2
        Vs, Ts, UVs = [], [], []
        base = 0
        for o in t.offsets:
            c = P + Nl * o
            # 8 vertices: top (back-left, back-right, front-right, front-left) + the same at the crib level
            corners = [(-hw, -hl), (-hw, hl), (hw, hl), (hw, -hl)]
            V = np.zeros((len(s), 8, 3))
            for k, (da, dl) in enumerate(corners):
                xy = c + T_ * da + Nl * dl
                V[:, k, :2] = xy
                V[:, k + 4, :2] = xy
                V[:, k, 2] = top
                V[:, k + 4, 2] = low
            # faces (CCW from outside): top facing up, back facing -T, front facing +T  -> 6 triangles
            loc = np.array([[0, 2, 1], [0, 3, 2], [4, 1, 5], [4, 0, 1], [3, 6, 2], [3, 7, 6]])
            idx = (np.arange(len(s)) * 8)[:, None, None] + loc[None]
            # UVs on the rail_bed tile: the top lies on its painted sleeper (u from the track axis, v = station),
            # the two side faces repeat the outermost concrete rows
            uv = np.zeros((len(s), 8, 2))
            for k, (da, dl) in enumerate(corners):
                uv[:, k, 0] = uv[:, k + 4, 0] = 0.5 + dl / RT.TEX_W_M
                uv[:, k, 1] = (s + 0.8 * da) / TILE_M
                uv[:, k + 4, 1] = (s + 0.7 * da) / TILE_M
            Vs.append(V.reshape(-1, 3))
            UVs.append(uv.reshape(-1, 2))
            Ts.append(idx.reshape(-1, 3) + base)
            base += len(s) * 8
        V = np.concatenate(Vs)
        T = np.concatenate(Ts)
        buf.add(layer, BED_MAT, V, np.concatenate(UVs), T, src=f"rail:{t.id}:sleepers")
        return int(len(T))

    def _panels(self, buf, ci, c, road_z_at):
        """Crossing panels across the whole bundle, split at every rail head (head + flangeway gap)."""
        t = self.tracks[c["track"]]
        sa, sb = c["zone"]
        s = _stations(sb - sa, PANEL_STEP) + sa
        P, _, Nl = _frame(t.line, s)
        W = max(abs(o) for o in t.offsets) + PANEL_HALF
        cuts = []
        for r in t.rail_lats():
            cuts.append((r - RAIL_HEAD_W / 2 - FLANGEWAY, r + RAIL_HEAD_W / 2))
        edges = [-W]
        for a, b in cuts:
            edges += [a, b]
        edges.append(W)
        n = 0
        for k in range(0, len(edges), 2):
            l0, l1 = edges[k], edges[k + 1]
            if l1 - l0 < 0.05:
                continue
            V, UV, T = _ribbon(P, Nl, np.zeros(len(s)), [l0, l1], [0.0, 0.0])
            V[:, 2] = _deck_z(road_z_at, V[:, 0], V[:, 1]) + PANEL_LIFT
            UV = V[:, :2].copy()
            buf.add("rail_crossing", "rail_crossing_panel", V, UV, T, src=f"rail:crossing:{ci}")
            n += len(T)
        return int(n)

    # -------------------------------------------------------------------------------------------- markers
    def markers(self, ci, c, road_z_at, outside=None):
        """Positioned / oriented crossing objects for the engine (prefabs): one per approach for signs and lights,
        barriers by crossing:barrier, one bell. heading_deg = compass direction the face / boom points to.
        ADR 0223: a crossing on the tile edge (dk65-04 Białostocka, 0.5 m inside) must not put a device into the far
        field of the neighbour (no road there, height clamped) - markers outside the tile are appended to `outside`
        (rail.json markers_outside_tile) and never returned, so rail.json and the instances (rail_props.place) agree."""
        out = []
        for m in self._markers_all(ci, c, road_z_at):
            if self.tile_local is not None and not self.tile_local.contains(Point(m["e"], m["n"])):
                if outside is not None:
                    outside.append(m)
                continue
            out.append(m)
        return out

    def _markers_all(self, ci, c, road_z_at):
        out = []
        pc, r = c["p"], c["rdir"]
        dtrack = c["half_track"] / c["sin"]                  # crossing centre -> outer panel edge, along the road
        half_road = c["road_w"] / 2
        code = self.sign_code(c)

        def z_at(p):
            return round(float(road_z_at(np.array([p[0]]), np.array([p[1]]))[0]), 3)

        def mk(kind, p, heading, approach, **kw):
            return {"crossing": ci, "kind": kind, "approach": approach, "e": round(float(p[0]), 2),
                    "n": round(float(p[1]), 2), "z": z_at(p), "heading_deg": heading, **kw}
        for a in (1, -1):
            drive = a * r                                     # travel direction of this approach (towards the rails)
            right = np.array([drive[1], -drive[0]])
            face = _heading(-drive)                           # signs face the oncoming driver
            post = pc - drive * (dtrack + SIGN_SETBACK) + right * (half_road + SIGN_LATERAL)
            if code:
                out.append(mk("sign", post, face, a, code=code, arm_l_m=SIGN_ARM_L, arm_w_m=SIGN_ARM_W,
                              arm_angle_deg=SIGN_ARM_ANGLE, bottom_z_m=SIGN_BOTTOM_Z))
            if c["light"]:
                out.append(mk("light", post, face, a, side="right"))
            if c.get("light_left"):          # repeater on the left verge (authored: seen on photos of the crossing)
                out.append(mk("light", pc - drive * (dtrack + SIGN_SETBACK) - right * (half_road + SIGN_LATERAL),
                              face, a, side="left"))
            if c.get("electrified") and (code or c["light"]):
                # ADR 0223: G-2 "sieć pod napięciem" (Dz.U. 2025 poz. 1105 § 81 ust. 1): kat. D below the G-3 / G-4
                # on its post (pkt 2), kat. A-C on the mast of the road signal below the lamp heads (pkt 1)
                out.append(mk("sign", post, face, a, code="G-2", mount="below_cross" if code else "signal_mast"))
            bar = c["barrier"]
            if bar in ("half", "double_half", "full", "gate", "yes"):
                boom_head = _heading(-right)                  # boom extends from the right verge to the left
                entry = pc - drive * (dtrack + BARRIER_SETBACK) + right * (half_road + 0.5)
                full = bar in ("full", "gate")
                out.append(mk("barrier", entry, boom_head, a, role="entry", type=bar,
                              boom_len_m=round((c["road_w"] if full else half_road) + 0.5, 2)))
                if bar == "double_half":
                    # second half-barrier of this side of the track: on the LEFT verge, closing the opposite lane
                    # (the exit lane of the other approach), as on Mapillary 1832769196903759 (booms on both verges
                    # before the rails). s22: it stood on the far side at the left verge = exactly on the other
                    # approach's entry barrier, so 4 markers gave 2 visible booms (render r1).
                    ex = pc - drive * (dtrack + BARRIER_SETBACK) - right * (half_road + 0.5)
                    out.append(mk("barrier", ex, _heading(right), a, role="exit", type=bar,
                                  boom_len_m=round(half_road + 0.5, 2)))
        if c["bell"]:
            right = np.array([r[1], -r[0]])
            out.append(mk("bell", pc - r * (dtrack + SIGN_SETBACK) + right * (half_road + SIGN_LATERAL),
                          _heading(-r), 1))
        return out

    def min_marker_clearance(self):
        """Smallest distance of a marker to any track axis bundle edge (track axis +/- outer offset); must exceed
        CLEARANCE_HALF."""
        if not self.report["markers"]:
            return None
        best = math.inf
        for m in self.report["markers"]:
            p = Point(m["e"], m["n"])
            for t in self.tracks:
                d = t.line.distance(p) - max(abs(o) for o in t.offsets)
                best = min(best, d)
        return round(best, 2)

    def footprint(self):
        """Track bed + clearance footprint (local polygons) for vegetation / collision QA."""
        return [t.line.buffer(max(t.half_top + 1.0, max(abs(o) for o in t.offsets) + CLEARANCE_HALF), cap_style=2)
                for t in self.tracks]

    def blocked(self, hf):
        from streetscape import paved as PV
        return PV.rasterize_polys(self.footprint(), hf)

    # -------------------------------------------------------------------------------------------- terrain (FIX 5)
    def conform(self, zc, keep, hf, road_z_at, log=print):
        """Ground under the track bed (opt-in stage only, like water.carve): the 1 m terrain nodes within the crown
        + CONFORM_PAD_M take the bed level (ballast top - BED_LIFT = top of rail - TRACK_H) and blend back to the
        terrain over CONFORM_BLEND_M; nodes of `keep` (roads, paved areas, buildings) are never touched. The bed then
        shows crown + 2 x BED_LIFT x slope of ballast (3.86 m for one track) instead of a 5.65 m apron on the grass,
        and neither floats over hollows nor is buried by bumps. Returns the new grid; keeps the smoothed ground the
        profile stands on (self.ground_grid) for build()."""
        from scipy import ndimage
        self.ground_grid = ndimage.gaussian_filter(np.asarray(zc, float), GROUND_SMOOTH_M)
        ground_at = grid_sampler(self.ground_grid, hf)
        out = np.array(zc, float, copy=True)
        keep = ndimage.binary_dilation(np.asarray(keep, bool), iterations=1)
        self._conform_mask = np.zeros(out.shape, bool)
        moved = []
        for t in self.tracks:
            if t.a["bridge"]:
                continue
            core = t.half_top + CONFORM_PAD_M
            reach = core + CONFORM_BLEND_M
            x0, y0, x1, y1 = t.line.buffer(reach).bounds
            i0, i1 = max(int(np.floor(x0 - hf.x0)), 0), min(int(np.ceil(x1 - hf.x0)), out.shape[1] - 1)
            j0, j1 = max(int(np.floor(hf.y1 - y1)), 0), min(int(np.ceil(hf.y1 - y0)), out.shape[0] - 1)
            if i1 < i0 or j1 < j0:
                continue
            jj, ii = np.mgrid[j0:j1 + 1, i0:i1 + 1]
            jj, ii = jj.ravel(), ii.ravel()
            pts = shapely.points(hf.x0 + ii, hf.y1 - jj)
            d = shapely.distance(t.line, pts)
            near = d <= reach
            if not near.any():
                continue
            jn, in_, d = jj[near], ii[near], d[near]
            s = shapely.line_locate_point(t.line, pts[near])
            P = np.array([t.line.interpolate(float(x)).coords[0] for x in s])
            bed = self._tor(t, P, s, ground_at, road_z_at) - TRACK_H
            wgt = np.clip(1.0 - (d - core) / CONFORM_BLEND_M, 0.0, 1.0)
            wgt = wgt * wgt * (3 - 2 * wgt)
            ok = ~keep[jn, in_]
            z_old = out[jn, in_]
            z_new = np.where(ok, wgt * bed + (1 - wgt) * z_old, z_old)
            out[jn, in_] = z_new
            full = ok & (d <= core)
            self._conform_mask[jn[full], in_[full]] = True
            dz = (z_new - z_old)[ok & (wgt > 0)]
            if len(dz):
                moved.append(dz)
        if moved:
            dz = np.concatenate(moved)
            self.report["conform"] = {"nodes": int(len(dz)), "cut_max_m": round(float(max(-dz.min(), 0.0)), 3),
                                      "fill_max_m": round(float(max(dz.max(), 0.0)), 3),
                                      "abs_p95_m": round(float(np.percentile(np.abs(dz), 95)), 3)}
            log("rail terrain conform", self.report["conform"])
        return out

    def lod_mask(self):
        """Bed nodes for the coarse terrain LoDs (min-filtered like the road footprint: never above the ballast)."""
        return self._conform_mask

    def bed_qa(self, terrain_at, ground_at, road_z_at, step=2.0):
        """Per-station check of the whole length (rail.json `bed_qa`): ballast top minus the final terrain at the
        crown edges (must stay > 0: not buried) and at the slope toes (terrain minus the skirt bottom must stay > 0:
        no gap under the bed). Stations inside crossing panels are skipped."""
        up, toe_gap, n = [], [], 0
        for t in self.tracks:
            if t.a["bridge"]:
                continue
            s = np.arange(0.0, t.line.length + 1e-6, step)
            P, _, Nl = _frame(t.line, s)
            inz = np.zeros(len(s), bool)
            for (sa, sb, _) in t.zones:
                inz |= (s >= sa - 1.0) & (s <= sb + 1.0)
            top = self._tor(t, P, s, ground_at, road_z_at) - RAIL_H - SLEEPER_PROUD
            for sgn in (-1, 1):
                a = P + Nl * sgn * t.half_top
                b = P + Nl * sgn * (t.half_top + SKIRT_M * BALLAST_SLOPE)
                up.append((top - terrain_at(a[:, 0], a[:, 1]))[~inz])
                toe_gap.append((terrain_at(b[:, 0], b[:, 1]) - (top - SKIRT_M))[~inz])
            n += int((~inz).sum())
        if not n:
            return None
        up, toe_gap = np.concatenate(up), np.concatenate(toe_gap)
        half = self.tracks[0].half_top
        qa = {"stations": n, "step_m": step,
              "crown_edge_above_terrain_m": {"min": round(float(up.min()), 3), "p50": round(float(np.median(up)), 3),
                                             "max": round(float(up.max()), 3)},
              "toe_buried_m": {"min": round(float(toe_gap.min()), 3), "p50": round(float(np.median(toe_gap)), 3),
                               "max": round(float(toe_gap.max()), 3)},
              "buried_crown_stations": int((up <= 0).sum()), "open_toe_stations": int((toe_gap <= 0).sum()),
              "visible_width_m": {"model": round(2 * (half + BED_LIFT * BALLAST_SLOPE), 2),
                                  "p50": round(float(2 * half + 2 * np.median(np.clip(up, 0, SKIRT_M)) * BALLAST_SLOPE), 2),
                                  "orthophoto_m": [3.5, 4.5], "status": "ESTIMATED (GUGiK 0.1 m 2025, n = 10)"}}
        self.report["bed_qa"] = qa
        return qa

    @staticmethod
    def export_textures(tex_dir):
        """rail_bed.png next to the region's other generated textures (only regions with the rail stage)."""
        import io
        tex_dir.mkdir(parents=True, exist_ok=True)
        for k, im in RT.textures().items():
            b = io.BytesIO()
            im.save(b, "PNG", optimize=False)
            p = tex_dir / f"{k}.png"
            if not p.exists() or p.read_bytes() != b.getvalue():
                p.write_bytes(b.getvalue())

    def out_json(self, region_id: str) -> dict:
        return {"schema": OUT_SCHEMA, "region": region_id, "frame": "local E,N,U (U absolute EVRF2007)",
                "heading": "compass degrees clockwise from north (Unity: Y rotation)",
                **{k: v for k, v in self.report.items()}}


def tri_per_km(lod: int, tracks: int = 1) -> float:
    """Closed-form triangle budget of plain track (no crossings) per km - ADR 0217 formula (bed = 2 slopes + one
    top strip per track): LoD0 = 1000/5 * (4 + 2n + 6*2n) + 1000/0.6 * 6n ; LoD1 = 1000/10 * (4 + 2n + 6*2n) ;
    LoD2 = 1000/20 * 2n."""
    seg = 1000.0 / LOD_STEP[lod]
    if lod == 2:
        return seg * 2 * tracks
    v = seg * (4 + 2 * tracks + 6 * 2 * tracks)
    if lod == 0:
        v += 1000.0 / SLEEPER_SPACING * 6 * tracks
    return v


def tri_per_crossing(road_w: float, tracks: int = 1, sin_t: float = 1.0, margin: float = PANEL_MARGIN) -> int:
    """Panel triangles of one crossing: ceil(zone / PANEL_STEP) segments x (2n + 1) strips x 2."""
    zone = road_w / sin_t + 2 * margin
    return int(math.ceil(zone / PANEL_STEP - 1e-9)) * (2 * tracks + 1) * 2
