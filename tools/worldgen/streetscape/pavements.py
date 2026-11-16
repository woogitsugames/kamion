"""Sidewalk surface types and kerb drops at pedestrian crossings (ADR 0237, research R6 pavements-kerbs).

Scope: rules and data only. The kerbs and the roadside footway strips are meshed by roads.meshing; this module
  * lowers kerbs at marked pedestrian crossings (`crossing_drops`): entries for streetscape.plots.apply_drops, added
    to the driveway drops of ADR 0114 by streetscape.stage.plan_plots, so they reach the `side_edit` of pass 2 of
    build_world without a change there. Heights of existing stations only - the number of triangles cannot grow;
  * renames the material of footway triangles at export (`retype_sidewalks` sets `Part.export_mat`) - the parts keep
    `sidewalk_paving` for every QA / fidelity / cull rule keyed on it, and no triangle is added or removed.
    NOT WIRED YET: it needs three small hunks in roads/build_world.py (assemble reads `export_mat` like the
    `bridge_kerb` rename of ADR 0123, WELD, one call before the export), a file owned by budget-fix-s21 (ADR 0221)
    while this was written. The patch is docs/adr/0237-build-world-hook.patch; until the lead applies it, `run` is
    never called and every roadside footway stays grey 20 x 10 blocks.

Both are opt-in per region: an `overrides.yaml` entry `kind: pavement_rules` switches them on (bialystok-industrial-c,
bialystok-dojlidy). A region without it is built exactly as before.

Sidewalk surface of a footway triangle, first match wins (`classify`):
  1. authored `kind: sidewalk_surface` override (polygon_en, or target.osm_way of the carriageway it runs along);
  2. OSM `surface` of a mapped footway within OSM_SNAP_M (only when osm_context.json carries the tag);
  3. BDOT10k OT_SKRP_L `materialnawierzchni` of the footway line ("aleja lub pasaż") within BDOT_SNAP_M;
  4. street class + building typology: a local street (residential / living_street / service) beside blocks of flats
     -> 35 x 35 cm slabs (only with `estate_slabs: true`; WORKING_VALUE, see ESTATE_*);
  5. grey 20 x 10 cm blocks (`sidewalk_paving`, the generator default since ADR 0063).

Override schema (Data/Regions/<id>/overrides.yaml):
  - id: ...
    kind: pavement_rules
    sidewalk_bdot: true              # rule 3
    estate_slabs: false              # rule 4
    crossing_kerb_drops: true        # kerbs lowered at marked pedestrian crossings
    cycle_paver_material: cycle_red  # material of a BDOT10k cycle path laid in blocks (cycle_red | sidewalk_paving)
  - id: ...
    kind: sidewalk_surface
    surface: paving_grey | paving_red | slabs | asphalt
    polygon_en: [[e, n], ...]        # region-local metres; or
    target: {osm_way: [...]}         # carriageway ways: the footway strips of their ribbons
"""

from __future__ import annotations

import re

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon

# ------------------------------------------------------------------------------------------------ kerbs: sources
# Research R6 (research/cloud2/pavements-kerbs/manifest.csv on origin/research/cloud2-pavements-kerbs, PR #65;
# review docs/reports/REVIEW-2026-11-15-s21-cloudD-65-pavements-kerbs.md: 5 of 5 quotes checked in the PDFs).
KERB_SOURCES = {
    # kerb reveal ("światło krawężnika") above the carriageway
    "reveal_default_m": {"value": (0.10, 0.12), "status": "SOURCED", "row": "R6-001",
                         "src": "OST D-08.01.01b Ustawienie krawężników betonowych (GDDKiA 2008), pkt 5.5.1"},
    "reveal_exception_m": {"value": (0.06, 0.16), "status": "SOURCED", "row": "R6-002 / R6-003",
                           "src": "OST D-08.01.01b pkt 5.5.1; Dz.U. 2016 poz. 124 § 43 ust. 5 (repealed act: the design "
                                  "basis of streets built before 2022-09-21)"},
    # Dz.U. 2022 poz. 1518 gives NO kerb height of a carriageway (R6-005, negative result confirmed by the review:
    # only § 36 ust. 3 "uskok ... o wysokości dostosowanej do potrzeb osób z niepełnosprawnościami wzroku",
    # § 42 ust. 5 <= 0.05 m, § 45 ust. 4 <= 0.01 m, § 89 ust. 2 >= 0.12 m). WR-D texts were not reachable (R6 README).
    "act_2022_number": {"value": None, "status": "SOURCED (negative)", "row": "R6-005",
                        "src": "Dz.U. 2022 poz. 1518 § 36 ust. 3"},
    "generator_m": {"value": 0.13, "status": "WORKING_VALUE", "row": "R6-001/002",
                    "src": "roads.standards.KERB_HEIGHT: 1 cm above the OST default range, inside 6-16 cm; kept "
                           "(ADR 0237: changing it moves every kerb of every region; needs a visual review)"},
    "crossing_m": {"value": 0.02, "status": "SOURCED for islands / medians, WORKING_VALUE for the outer kerbs",
                   "row": "R6-004",
                   "src": "Dz.U. 2016 poz. 124 § 127 ust. 10: 'Wyniesienie krawężnika wyspy albo pasa dzielącego na "
                          "przejściu dla pieszych nie powinno być większe niż 2 cm' (repealed; the act of 2022 names no "
                          "number, § 36 ust. 3)"},
    "cycle_crossing_m": {"value": 0.01, "status": "SOURCED", "row": "R6-006",
                         "src": "Dz.U. 2022 poz. 1518 § 45 ust. 4 (<= 0.01 m in difficult conditions, otherwise flush)"},
    "driveway_m": {"value": 0.03, "status": "WORKING_VALUE", "row": "R6-015 / R6-011",
                   "src": "streetscape.plots.DROP_H_M; ZDM Białystok guidelines drawing 9: drive-over kerb k1 "
                          "25x12x100 cm, levels 0 -> +3 (unit of the levels not written on the drawing: ESTIMATED cm); "
                          "OST D-08.01.01b zał. 4 lit. g: street kerb 20 x 30 cm laid flat at a gateway (no number)"},
    "ramp_m": {"value": 1.0, "status": "WORKING_VALUE", "row": "R6-009",
               "src": "one precast kerb unit (l = 100 cm, OST D-08.01.01b zał. 3) as the transition piece on either "
                      "side; no source gives the length of the ramp"},
}
CROSSING_KERB_M = KERB_SOURCES["crossing_m"]["value"]
CROSSING_RAMP_M = KERB_SOURCES["ramp_m"]["value"]
CROSSING_MIN_HALF_M = 0.5    # WORKING_VALUE: a flat part shorter than 1 m is not a crossing kerb -> no drop
CROSSING_SNAP_M = 0.5        # node this far outside the carriageway edge still belongs to it (= roads.markings)
SKIP_CROSSING = ("unmarked", "no", "informal")     # = roads.markings: no zebra is painted there either

# ------------------------------------------------------------------------------------------------ sidewalk types
DEFAULT = "paving_grey"
MATERIAL = {
    "paving_grey": "sidewalk_paving",       # 20 x 10 cm grey blocks (R6-022, R6-108: 9 of 31 frames)
    "paving_red": "sidewalk_paving_red",    # the same blocks, red-brown (R6-111: frame F38, Mickiewicza)
    "slabs": "sidewalk_slabs",              # 35 x 35 cm concrete slabs (R6-025; R6-109: 3 of 31 frames)
    "asphalt": "path_asphalt",              # bituminous footway (BDOT10k "masa bitumiczna")
}
SIDEWALK_MATERIALS = tuple(MATERIAL.values())
BDOT_SIDEWALK = {"kostka prefabrykowana": "paving_grey", "płyty betonowe": "slabs", "masa bitumiczna": "asphalt"}
OSM_SIDEWALK = {"paving_stones": "paving_grey", "sett": "paving_grey", "bricks": "paving_grey",
                "asphalt": "asphalt", "concrete:plates": "slabs", "concrete:lanes": "slabs"}
BDOT_FOOTWAY_KINDS = ("aleja lub pasaż",)
BDOT_SNAP_M = 3.0            # WORKING_VALUE: 2 m strip behind the kerb + BDOT10k line accuracy (GUGiK: <= 1.5 m class)
OSM_SNAP_M = 3.0             # WORKING_VALUE, as above
# Rule 4. WORKING_VALUE: R6 has no count of slab footways per street type (R6-109: slabs on 3 of 31 frames, none of
# them in an estate; R6 README "płyta chodnikowa ... starsze chodniki ... UNVERIFIED"). Off unless a region asks for it.
ESTATE_CLASSES = ("residential", "living_street", "service")
ESTATE_BLOCK_FUNCS = ("budynek wielorodzinny",)
ESTATE_M = 30.0              # a block of flats within this distance of the footway
ESTATE_MIN_HEIGHT_M = 10.0   # 4 storeys and more (2.8 m storeys, buildings_mesh.STOREY_H): not a terraced house
LAYERS_RULES = ("road",)             # data rules: the footway strips of the road ribbons
LAYERS_OVERRIDE = ("road", "paved")  # authored polygons also reach set-back paths and cycle-path footways
SOURCE_MAT = "sidewalk_paving"
_WAY = re.compile(r"w(\d+)")


def rules_of(overrides) -> dict | None:
    """The region's `pavement_rules` entry, or None (the region is built as before ADR 0237)."""
    for o in overrides or []:
        if o.get("kind") == "pavement_rules":
            return o
    return None


def material_of(surface: str) -> str:
    """Material id of a sidewalk surface type; a material id is passed through."""
    if surface in MATERIAL:
        return MATERIAL[surface]
    if surface in SIDEWALK_MATERIALS or surface in ("cycle_red", "cycle_asphalt"):
        return surface
    raise ValueError(f"unknown sidewalk surface {surface!r} (one of {sorted(MATERIAL)})")


def bdot_cycle_material(overrides, materialnawierzchni):
    """Material of a BDOT10k "droga dla rowerów" line that no OSM way describes (paved.collect), None = not built.
    Without the region's pavement_rules: `cycle_red` for every paved one, as before ADR 0237. With them:
      * blocks -> `cycle_paver_material` of the rules (default cycle_red = red 20 x 10 blocks). bialystok-dojlidy sets
        sidewalk_paving: every cycle track on its frames is grey (R6-110, 7 of 7; ADR 0188), so an unverified one must
        not come out red there;
      * anything else paved -> `cycle_asphalt`, the warm-grey DDR asphalt of ADR 0188 (red asphalt only on the ways
        verified by M65, which are OSM ways with a `kind: cycleway` override)."""
    if materialnawierzchni == "grunt naturalny":
        return None
    r = rules_of(overrides)
    if r is None:
        return "cycle_red"
    if materialnawierzchni == "kostka prefabrykowana":
        return material_of(r["cycle_paver_material"]) if r.get("cycle_paver_material") else "cycle_red"
    return "cycle_asphalt"


def classify(*, override=None, osm_surface=None, bdot_material=None, highway=None, near_blocks=False,
             estate_slabs=False, use_bdot=True):
    """(surface type, provenance) of one piece of roadside footway - the rule of the module docstring."""
    if override:
        return override, "authored_override"
    if osm_surface in OSM_SIDEWALK:
        return OSM_SIDEWALK[osm_surface], "osm_surface"
    if use_bdot and bdot_material in BDOT_SIDEWALK:
        return BDOT_SIDEWALK[bdot_material], "bdot10k_SKRP"
    if estate_slabs and near_blocks and highway in ESTATE_CLASSES:
        return "slabs", "typology(WORKING_VALUE)"
    return DEFAULT, "default"


# ------------------------------------------------------------------------------------------------ kerb drops
def crossing_drops(net, ctx_points, overrides, stats: dict | None = None) -> list:
    """Kerb drops at the marked pedestrian crossings of the region, as streetscape.plots.apply_drops entries
    [{chain, side, s, half, h, ramp, kerb_only, src}]: both kerbs of the chain the OSM crossing node lies on (the snap
    of roads.markings, so the drop is where the zebra is). apply_drops edits the kerb height of EXISTING stations
    (the footway hangs on the kerb, so it comes down with it); no station is added, so the mesh keeps its triangle
    count. Empty unless the region's pavement_rules ask for `crossing_kerb_drops`.

    The drop with both ramps stays on the chain between its junction trims (as the driveway drops of
    plots.gate_access): the kerb is back at full height where the junction corner strips take over. A crossing
    closer to the trim than one ramp + CROSSING_MIN_HALF_M, inside a junction patch or on a bridge gets no drop
    (counted in `stats`); a crossing near the trim gets a shorter flat part."""
    from roads import standards as S
    r = rules_of(overrides)
    st = stats if stats is not None else {}
    st.update({"crossings": 0, "dropped": 0, "shortened": 0, "skipped_near_junction": 0, "skipped_bridge": 0,
               "skipped_off_chain": 0})
    if not r or not r.get("crossing_kerb_drops"):
        return []
    h = float(r.get("crossing_kerb_m", CROSSING_KERB_M))
    drops = []
    for p in ctx_points:
        if p.get("kind") != "highway=crossing" or p.get("crossing") in SKIP_CROSSING:
            continue
        st["crossings"] += 1
        q = np.array([p["e"], p["n"]], float)
        best = None
        for c in net.chains:
            if c.meta.get("absorbed") or c.line is None:
                continue
            lo, hi = c.line.p.min(0) - 12, c.line.p.max(0) + 12
            if not (lo[0] <= q[0] <= hi[0] and lo[1] <= q[1] <= hi[1]):
                continue
            s, lat = c.line.project(q)
            if abs(lat) <= float(c.hw_at(s)) + CROSSING_SNAP_M and (best is None or abs(lat) < best[2]):
                best = (c, float(s), abs(lat))
        if best is None:
            st["skipped_off_chain"] += 1
            continue
        c, s = best[0], best[1]
        room = min(s - c.t_a, c.length - c.t_b - s) - CROSSING_RAMP_M
        if room < CROSSING_MIN_HALF_M:
            st["skipped_near_junction"] += 1
            continue
        if c.bridge is not None and bool(c.bridge[int(c.idx(s))]):
            st["skipped_bridge"] += 1
            continue
        half = min(S.P10_WIDTH / 2, room)
        st["dropped"] += 1
        st["shortened"] += int(half < S.P10_WIDTH / 2)
        for side in "LR":
            drops.append({"chain": c.id, "side": side, "s": s, "half": half, "h": h, "ramp": CROSSING_RAMP_M,
                          "kerb_only": True, "src": f"crossing:n{p.get('osm_node')}"})
    return drops


# ------------------------------------------------------------------------------------------------ sidewalk zones
class Zones:
    """Everything `retype_sidewalks` needs, in region-local metres."""

    def __init__(self, rules, polys=(), ways=None, bdot=(), osm=(), blocks=(), way_highway=None):
        self.rules = rules or {}
        self.polys = list(polys)                    # [(id, Polygon, surface)]
        self.ways = dict(ways or {})                # {osm way id (int): (id, surface)}
        self.bdot = list(bdot)                      # [(LineString, materialnawierzchni)]
        self.osm = list(osm)                        # [(LineString, surface)]
        self.blocks = list(blocks)                  # [Polygon] blocks of flats
        self.way_highway = dict(way_highway or {})  # {osm way id (int): highway class}


def plan(overrides, origin=(0.0, 0.0), src=None, ctx=None, buildings=None, graph=None) -> Zones | None:
    """Zones of a region from its git data, or None when the region has no `pavement_rules`.
    src: streetscape_sources.json, ctx: osm_context.json, buildings: buildings.geojson, graph: roads.graph.json."""
    rules = rules_of(overrides)
    if rules is None:
        return None
    o = np.asarray(origin, float)
    polys, ways = [], {}
    for ov in overrides:
        if ov.get("kind") != "sidewalk_surface":
            continue
        material_of(ov["surface"])                  # fail on a typo before anything is built
        if "polygon_en" in ov:
            polys.append((ov["id"], shapely.make_valid(Polygon(np.asarray(ov["polygon_en"], float))), ov["surface"]))
        elif "polygon_epsg2180" in ov:
            polys.append((ov["id"], shapely.make_valid(Polygon(np.asarray(ov["polygon_epsg2180"], float) - o)),
                          ov["surface"]))
        for wid in (ov.get("target") or {}).get("osm_way", []):
            ways[int(wid)] = (ov["id"], ov["surface"])
    bdot, osm, blocks, way_hw = [], [], [], {}
    if src is not None and rules.get("sidewalk_bdot", True):
        for f in src["bdot10k"].get("OT_SKRP_L", []):
            pr = f["props"]
            if pr.get("rodzaj") in BDOT_FOOTWAY_KINDS and pr.get("materialnawierzchni") in BDOT_SIDEWALK:
                bdot.append((LineString(np.asarray(f["geometry"]["coordinates"], float) - o), pr["materialnawierzchni"]))
    if ctx is not None:
        for f in ctx.get("footways", []):
            if f.get("highway") in ("footway", "path") and f.get("surface") in OSM_SIDEWALK:
                osm.append((LineString(np.asarray(f["geometry"], float) - o), f["surface"]))
    if buildings is not None and rules.get("estate_slabs"):
        for f in buildings["features"]:
            p = f["properties"]
            if p.get("function") in ESTATE_BLOCK_FUNCS and (p.get("height_m") or 0.0) >= ESTATE_MIN_HEIGHT_M:
                g = shapely.geometry.shape(f["geometry"])
                blocks.append(shapely.affinity.translate(g, -o[0], -o[1]))
    if graph is not None:
        for e in graph["edges"]:
            way_hw[int(e["osm_way"])] = e["attrs"]["highway"]["v"]
    return Zones(rules, polys, ways, bdot, osm, blocks, way_hw)


def _nearest(lines, pts, dmax):
    """Index of the nearest line within dmax for every point, -1 where there is none."""
    out = np.full(len(pts), -1)
    if not lines or not len(pts):
        return out
    tree = shapely.STRtree(lines)
    ip, il = tree.query_nearest(pts, max_distance=dmax, all_matches=False)
    out[ip] = il
    return out


def surface_types(cen, way, zones: Zones, layer="road"):
    """Surface type and provenance of footway triangles with centroids `cen` (n, 2) that belong to carriageway OSM
    way `way` (int or None). Returns (types (n,) of str, provenance (n,) of str, {override id: triangles})."""
    n = len(cen)
    typ = np.full(n, DEFAULT, dtype=object)
    prov = np.full(n, "default", dtype=object)
    hits = {}
    pts = shapely.points(np.asarray(cen, float).reshape(-1, 2))
    r = zones.rules
    if layer in LAYERS_RULES:
        if r.get("estate_slabs") and zones.blocks and zones.way_highway.get(way) in ESTATE_CLASSES:
            near = _nearest(zones.blocks, pts, ESTATE_M) >= 0
            typ[near], prov[near] = "slabs", "typology(WORKING_VALUE)"
        if r.get("sidewalk_bdot", True):
            k = _nearest([ln for ln, _ in zones.bdot], pts, BDOT_SNAP_M)
            for i in np.flatnonzero(k >= 0):
                typ[i], prov[i] = BDOT_SIDEWALK[zones.bdot[k[i]][1]], "bdot10k_SKRP"
        k = _nearest([ln for ln, _ in zones.osm], pts, OSM_SNAP_M)
        for i in np.flatnonzero(k >= 0):
            typ[i], prov[i] = OSM_SIDEWALK[zones.osm[k[i]][1]], "osm_surface"
        if way in zones.ways:
            oid, surf = zones.ways[way]
            typ[:], prov[:] = surf, "authored_override"
            hits[oid] = n
    for oid, poly, surf in zones.polys:
        inside = shapely.contains(poly, pts)
        if inside.any():
            typ[inside], prov[inside] = surf, "authored_override"
            hits[oid] = hits.get(oid, 0) + int(inside.sum())
    return typ, prov, hits


def retype_sidewalks(parts: list, zones: Zones | None) -> dict:
    """Give the footway triangles of `parts` (a MeshBuf.parts list, edited in place) their surface type.

    A part of material `sidewalk_paving` whose triangles get another type is split: the triangles of each type move
    to a new part that shares the vertex arrays and carries `export_mat` (the material written to the GLB). `mat`
    stays `sidewalk_paving` on every part. Triangles are neither added nor removed (report: tris_in == tris_out)."""
    from roads.meshing import Part
    rep = {"enabled": zones is not None, "tris_in": 0, "tris_out": 0, "tris_by_material": {}, "m2_by_material": {},
           "tris_by_provenance": {}, "overrides_applied": [], "overrides_stale": []}
    if zones is None:
        return rep
    new, hits_all = [], {}
    for p in parts:
        if p.mat != SOURCE_MAT or p.layer not in LAYERS_OVERRIDE or getattr(p, "export_mat", None):
            continue
        tri = p.V[p.T]
        cen = tri.mean(axis=1)[:, :2]
        area = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
        m = _WAY.search(str(p.src))
        typ, prov, hits = surface_types(cen, int(m.group(1)) if m else None, zones, p.layer)
        for k, v in hits.items():
            hits_all[k] = hits_all.get(k, 0) + v
        rep["tris_in"] += len(p.T)
        mats = np.array([MATERIAL[t] for t in typ], dtype=object)
        for pv in sorted(set(prov)):
            rep["tris_by_provenance"][pv] = rep["tris_by_provenance"].get(pv, 0) + int((prov == pv).sum())
        T0 = p.T
        for mat in sorted(set(mats)):
            sel = mats == mat
            rep["tris_by_material"][mat] = rep["tris_by_material"].get(mat, 0) + int(sel.sum())
            rep["m2_by_material"][mat] = rep["m2_by_material"].get(mat, 0.0) + float(area[sel].sum())
            if mat == SOURCE_MAT:
                continue
            q = Part(p.layer, p.mat, p.V, p.UV, T0[sel], p.footprint, p.src, p.UV1, p.COL)
            q.export_mat = mat
            new.append(q)
        p.T = T0[mats == SOURCE_MAT]
        rep["tris_out"] += len(p.T)
    rep["tris_out"] += sum(len(q.T) for q in new)
    parts[:] = [p for p in parts if len(p.T)] + new
    rep["m2_by_material"] = {k: round(v, 1) for k, v in sorted(rep["m2_by_material"].items())}
    ids = [oid for oid, _, _ in zones.polys] + [oid for oid, _ in zones.ways.values()]
    rep["overrides_applied"] = sorted({i for i in ids if hits_all.get(i)})
    rep["overrides_stale"] = sorted({i for i in ids if not hits_all.get(i)})
    return rep


def run(w, region_id: str, log=lambda *a: None) -> dict:
    """build_world hook: plan the zones of the region from its git data and retype the footways of w.buf."""
    import json

    from roads import pipeline
    from streetscape import sources as SRC
    overrides = pipeline.load_overrides(region_id)
    if rules_of(overrides) is None:
        return {"enabled": False}
    rdir = pipeline.REGIONS / region_id

    def _json(path):
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    zones = plan(overrides, w.origin, SRC.load(region_id), _json(rdir / "generated" / "osm_context.json"),
                 _json(rdir / "buildings.geojson"), _json(rdir / "roads.graph.json"))
    rep = retype_sidewalks(w.buf.parts, zones)
    log("sidewalk surfaces (ADR 0237):", rep["m2_by_material"], "stale", rep["overrides_stale"])
    if rep["tris_in"] != rep["tris_out"]:
        raise RuntimeError(f"sidewalk retype changed the triangle count: {rep['tris_in']} -> {rep['tris_out']}")
    return rep
