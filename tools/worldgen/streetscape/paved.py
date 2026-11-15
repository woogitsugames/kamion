"""Paved areas outside the road network: depot yards, parking lots, loading aprons, set-back footpaths.

Sources (priority order; a higher source wins where polygons overlap):
  1. authored overrides `paved_areas` (Data/Regions/<id>/overrides.yaml) - polygons the data does not describe
     (`kind: paved_area`, `polygon_epsg2180`). `kind: unpaved_area` (ADR 0161, region-local `polygon_en`) is the
     opposite: ground that the data paves but the orthophoto shows as lawn - nothing of any source is laid inside
     it, the terrain (grass) stays. An unpaved_area that removes nothing is reported stale.
  2. loading-dock aprons generated in front of dock doors (streetscape.buildings)
  3. OSM amenity=parking / area:highway with a `surface` tag
  4. BDOT10k OT_PTPL_A plac (MATERIALNAWIERZCHNI) and OT_KUKO_A parking / fuel station
  5. OSM amenity=parking without surface (asphalt default)
  6. BDOT10k OT_SKRP_L footpaths and cycle paths more than ~2 m from a carriageway (set-back sidewalks)
Everything is cut by the road surface footprint (roads own their kerbs and sidewalks) and by building
footprints. Surfaces sit on a smoothed NMT (sigma PAVED_SMOOTH_M) that is blended into the road edge
heights so yards meet flush service roads without steps; the terrain is then conformed to roads AND
paved areas together. Paving-block surfaces get a concrete edging strip (obrzeże) where they meet soil;
cast concrete and asphalt yards end flush (no kerb, standards.PAVED_EDGING).
"""

from __future__ import annotations

import math

import numpy as np
import shapely
from scipy import ndimage
from shapely.geometry import Polygon

from roads import standards as S

# surface -> material (MATERIALS in build_world)
BDOT_SURFACE = {"kostka prefabrykowana": "yard_paving", "beton": "yard_concrete", "masa bitumiczna": "yard_asphalt",
                "płyty betonowe": "yard_slabs", "grunt naturalny": "yard_gravel", "żwir": "yard_gravel"}
OSM_SURFACE = {"asphalt": "yard_asphalt", "paving_stones": "yard_paving", "concrete": "yard_concrete",
               "concrete:plates": "yard_slabs", "gravel": "yard_gravel", "compacted": "yard_gravel",
               "fine_gravel": "yard_gravel", "unpaved": "yard_gravel", "ground": "yard_gravel", "dirt": "yard_gravel",
               "sett": "yard_paving", "grass_paver": "yard_gravel"}
PATH_SURFACE = {"kostka prefabrykowana": "sidewalk_paving", "masa bitumiczna": "path_asphalt", "beton": "yard_concrete",
                "płyty betonowe": "yard_slabs"}
# paving blocks need an edging restraint; asphalt paths and cycle tracks are laid between concrete edgings too (ADR 0188)
EDGED = {"yard_paving", "yard_behaton", "sidewalk_paving", "cycle_red", "cycle_asphalt", "cycle_asphalt_red"}
CELL = 4.0


def _poly_local(coords, origin):
    ox, oy = origin
    rings = [np.asarray(r, float) - [ox, oy] for r in coords]
    return Polygon(rings[0], rings[1:])


# ADR 0179: BDOT10k OT_KUKO_A "lotnisko lub lądowisko" is the land of an aerodrome (Krywlany: 57 ha of meadow with one
# asphalt runway), not a paved surface - as a yard it became 54 ha of concrete slabs with truck stands. Its real
# surfaces come from OT_PTPL_A or an authored `paved_area`.
KUKO_NOT_A_SURFACE = ("lotnisko lub lądowisko",)


def collect(src, origin, overrides, docks, roads_poly, buildings_poly, report, truck_zone=None, cycle=None):
    """Return [{id, poly (local), mat, source, parking}] without overlaps, in priority order.

    truck_zone: polygon around halls / dock aprons; block-paved BDOT yards (> 800 m2) touching it are laid
    with I-shaped interlocking blocks (behaton, `yard_behaton`) as Polish truck yards are, while car parks and
    footways keep rectangular blocks.
    cycle: {"cands": cycleways.candidates(...), "bdot_replaced": [...]} (ADR 0188) - cycle tracks built from OSM; they
    come right after the dock aprons (a mapped track is a precise line, a yard is a blob) and the BDOT10k path lines
    that describe the same paths are not laid a second time."""
    cand = []
    for o in overrides:
        if o.get("kind") != "paved_area":
            continue
        ring = np.asarray(o["polygon_epsg2180"], float) - origin
        cand.append((o["id"], Polygon(ring), o["material"], "authored_override", bool(o.get("parking"))))
    for d in docks:
        # the hero depot's apron (ADR 0071 r11): decades of trailers on the bumpers - darker, cracked, soiled concrete
        cand.append((d["id"], d["apron"], "yard_concrete_worn" if d.get("hero") else "yard_concrete", "dock_apron", False))
    cand += list((cycle or {}).get("cands", []))
    bdot_replaced = set((cycle or {}).get("bdot_replaced", []))
    osm_park = [a for a in src["osm"]["areas"] if a["tags"].get("amenity") == "parking" or "area:highway" in a["tags"]]
    for a in osm_park:
        if a["tags"].get("surface") in OSM_SURFACE:
            cand.append((f"osm:{a['osm_type']}/{a['osm_id']}:{a['part']}", _poly_local(a["geometry"]["coordinates"], origin),
                         OSM_SURFACE[a["tags"]["surface"]], "osm", a["tags"].get("amenity") == "parking"))
    for f in src["bdot10k"]["OT_PTPL_A"]:
        m = BDOT_SURFACE.get(f["props"].get("materialnawierzchni"), "yard_asphalt")
        pp = _poly_local(f["geometry"]["coordinates"], origin)
        if m == "yard_paving" and truck_zone is not None and pp.area > 800 and pp.intersects(truck_zone):
            m = "yard_behaton"
        cand.append((f"bdot:{f['id']}", pp, m, "bdot10k_PTPL", False))
    for f in src["bdot10k"]["OT_KUKO_A"]:
        if f["props"].get("rodzaj") in KUKO_NOT_A_SURFACE:
            report.setdefault("kuko_not_paved", []).append(f"bdot:{f['id']}")
            continue
        m = "yard_asphalt" if f["props"].get("rodzaj") == "parking" else "yard_concrete"
        cand.append((f"bdot:{f['id']}", _poly_local(f["geometry"]["coordinates"], origin), m, "bdot10k_KUKO",
                     f["props"].get("rodzaj") == "parking"))
    for a in osm_park:
        if a["tags"].get("surface") not in OSM_SURFACE:
            cand.append((f"osm:{a['osm_type']}/{a['osm_id']}:{a['part']}", _poly_local(a["geometry"]["coordinates"], origin),
                         "yard_asphalt", "osm(default surface)", a["tags"].get("amenity") == "parking"))
    for f in src["bdot10k"]["OT_SKRP_L"]:
        if f["id"] in bdot_replaced:
            continue
        pr = f["props"]
        mat = PATH_SURFACE.get(pr.get("materialnawierzchni"))
        if pr.get("rodzaj") == "droga dla rowerów":
            mat = "cycle_red" if pr.get("materialnawierzchni") != "grunt naturalny" else None
        if not mat:
            continue
        w = float(pr.get("szerokosc") or S.SETBACK_PATH_W)
        ln = shapely.LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        cand.append((f"bdot:{f['id']}", ln.buffer(w / 2, cap_style="flat", join_style="mitre", mitre_limit=2.0),
                     mat, "bdot10k_SKRP", False))
    taken = shapely.union_all([roads_poly.buffer(0.02), buildings_poly]) if buildings_poly is not None else roads_poly
    # ADR 0161: authored lawns. Authored paved areas keep their priority over them (an authored footway may cross
    # an authored lawn); every data source (docks, OSM, BDOT10k) is cut by them.
    unpaved = [(o["id"], shapely.make_valid(Polygon(np.asarray(o["polygon_en"], float) if "polygon_en" in o
                                                    else np.asarray(o["polygon_epsg2180"], float) - origin)))
               for o in overrides if o.get("kind") == "unpaved_area"]
    lawn = shapely.union_all([p for _, p in unpaved]) if unpaved else None
    removed = {cid: 0.0 for cid, _ in unpaved}
    out = []
    for cid, poly, mat, srcname, is_parking in cand:
        poly = shapely.make_valid(poly)
        g = poly.difference(taken)
        if lawn is not None and srcname != "authored_override":
            for uid, up in unpaved:
                removed[uid] += g.intersection(up).area
            g = g.difference(lawn)
        g = g.buffer(-0.05).buffer(0.05)           # drop slivers
        g = _trim_spikes(g)
        parts = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 3.0]
        kept = 0.0
        for k, p in enumerate(parts):
            p = p.simplify(0.05)
            if p.is_empty or p.area <= 3.0 or p.geom_type != "Polygon":
                continue
            out.append({"id": f"{cid}#{k}", "poly": p, "mat": mat, "source": srcname, "parking": is_parking})
            kept += p.area
        if kept:
            taken = shapely.union(taken, poly)
        report.setdefault(srcname, [0, 0.0])
        report[srcname][0] += 1 if kept else 0
        report[srcname][1] = round(report[srcname][1] + kept, 1)
    if unpaved:
        report["unpaved_area"] = {uid: round(a, 1) for uid, a in removed.items()}
        report["unpaved_area_stale"] = sorted(uid for uid, a in removed.items() if a < 1.0)
    return out


SPIKE_OPEN_M = 0.5          # = half the terrain grid (1 m): a tip narrower than one cell has no terrain node under it
SPIKE_MAX_M2 = 2.0


def _trim_spikes(g):
    """Cut the acute tips a road / building outline leaves on a paved area (ADR 0093). A tip narrower than the 1 m
    terrain grid gets no conformed node, so it stood 0.28-0.35 m proud of the ground (terrain_walls skirt:yard_*:
    every remaining case was such a tip, and their number moved with every change of the road footprint). Only tips
    are cut (morphological opening, mitre joins keep straight edges and corners); a cut that would split the area
    is not made, so part numbering (ids `<source>#<k>`) is unchanged."""
    if g.is_empty:
        return g
    opened = g.buffer(-SPIKE_OPEN_M, join_style="mitre").buffer(SPIKE_OPEN_M, join_style="mitre")
    rest = g.difference(opened)
    spikes = [sp.buffer(0.01) for sp in getattr(rest, "geoms", [rest])
              if not sp.is_empty and sp.geom_type == "Polygon" and 1e-4 <= sp.area <= SPIKE_MAX_M2]
    if not spikes:
        return g
    nparts = len(getattr(g, "geoms", [g]))
    t = g.difference(shapely.union_all(spikes))
    if not t.is_empty and len(getattr(t, "geoms", [t])) == nparts:
        return t
    for sp in spikes:                              # some cut would split the area: take the others one by one
        t = g.difference(sp)
        if not t.is_empty and len(getattr(t, "geoms", [t])) == nparts:
            g = t
    return g


def road_footprint_polygon(parts, bounds=None):
    """Union of ground road surface triangles (carriageways, kerbs, sidewalks, junction patches)."""
    tris = [p.V[p.T][:, :, :2] for p in parts if p.footprint]
    if not tris:
        return Polygon()
    T = np.concatenate(tris)
    if bounds is not None:
        x0, y0, x1, y1 = bounds
        mn, mx = T.min(1), T.max(1)
        T = T[(mx[:, 0] >= x0) & (mn[:, 0] <= x1) & (mx[:, 1] >= y0) & (mn[:, 1] <= y1)]
    polys = shapely.polygons(np.concatenate([T, T[:, :1]], axis=1))
    polys = polys[shapely.area(polys) > 1e-4]
    return shapely.make_valid(shapely.union_all(polys, grid_size=0.01))


# ------------------------------------------------------------------------------------------- heights
def rasterize_polys(polys, hf):
    from rasterio import features
    from rasterio.transform import Affine
    H, W = hf.z.shape
    tr = Affine(1.0, 0, hf.x0 - 0.5, 0, -1.0, hf.y1 + 0.5)
    shapes = [(p, 1) for p in polys if not p.is_empty]
    if not shapes:
        return np.zeros((H, W), bool)
    return features.rasterize(shapes, out_shape=(H, W), transform=tr, all_touched=True).astype(bool)


def paved_heights(hf, road_z, road_mask, pmask):
    """Smoothed NMT inside paved areas, blended into the adjacent road heights (flush joins)."""
    sm = ndimage.gaussian_filter(hf.z, S.PAVED_SMOOTH_M)
    delta = np.where(road_mask, road_z - sm, 0.0)
    d, (jj, ii) = ndimage.distance_transform_edt(~road_mask, return_indices=True)
    w = np.clip(1.0 - d / S.PAVED_BLEND_M, 0.0, 1.0)
    z = sm + delta[jj, ii] * w
    return np.where(pmask, z, np.nan)


def bilinear(grid, hf, e, n):
    fi = np.clip(e - hf.x0, 0, grid.shape[1] - 1.001)
    fj = np.clip(hf.y1 - n, 0, grid.shape[0] - 1.001)
    i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
    a, b = fi - i0, fj - j0
    g = grid
    return ((1 - a) * (1 - b) * g[j0, i0] + a * (1 - b) * g[j0, i0 + 1] + (1 - a) * b * g[j0 + 1, i0] +
            a * b * g[j0 + 1, i0 + 1])


# ------------------------------------------------------------------------------------------- mesh
def triangulate(poly, cell=CELL):
    """Triangles (m, 3, 2) covering the polygon, split on a world-aligned grid so the surface can
    follow the ground (vertices at least every `cell` metres)."""
    x0, y0, x1, y1 = poly.bounds
    gx = np.arange(math.floor(x0 / cell) * cell, x1, cell)
    gy = np.arange(math.floor(y0 / cell) * cell, y1, cell)
    X, Y = np.meshgrid(gx, gy)
    boxes = shapely.box(X.ravel(), Y.ravel(), X.ravel() + cell, Y.ravel() + cell)
    shapely.prepare(poly)
    inside = shapely.contains(poly, boxes)
    out = []
    for b in boxes[inside]:
        bx0, by0, bx1, by1 = b.bounds
        out.append([[bx0, by0], [bx1, by0], [bx1, by1]])
        out.append([[bx0, by0], [bx1, by1], [bx0, by1]])
    edge = boxes[~inside]
    edge = edge[shapely.intersects(poly, edge)]
    pieces = shapely.intersection(poly, edge)
    for pc in pieces:
        for g in getattr(pc, "geoms", [pc]):
            if g.geom_type != "Polygon" or g.area < 1e-4:
                continue
            tri = shapely.constrained_delaunay_triangles(g)
            for t in tri.geoms:
                c = np.asarray(t.exterior.coords)[:3]
                out.append(c.tolist())
    T = np.asarray(out, float).reshape(-1, 3, 2)
    # CCW
    cr = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
    T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
    return T[np.abs(cr) > 1e-6]


def dominant_angle(poly):
    r = poly.minimum_rotated_rectangle
    c = np.asarray(r.exterior.coords)
    d = np.diff(c, axis=0)
    k = int(np.argmax(np.hypot(d[:, 0], d[:, 1])))
    return math.atan2(d[k, 1], d[k, 0])


def build_meshes(buf, paved, zgrid, hf, walls=None, roads_poly=None):
    """Paved surface parts (layer 'paved', footprint) + edging / flange strips + collision."""
    for item in paved:
        poly, mat = item["poly"], item["mat"]
        T2 = triangulate(poly)
        if not len(T2):
            continue
        P = T2.reshape(-1, 2)
        q = np.round(P * 1000).astype(np.int64)
        u, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
        P = P[first]
        Z = bilinear(np.nan_to_num(zgrid, nan=np.nanmean(zgrid[np.isfinite(zgrid)]) if np.isfinite(zgrid).any() else 0),
                     hf, P[:, 0], P[:, 1])
        V = np.column_stack([P, Z + S.PAVED_LIFT])
        T = inv.ravel().reshape(-1, 3)
        a = dominant_angle(poly)
        ca, sa = math.cos(-a), math.sin(-a)
        UV = np.column_stack([P[:, 0] * ca - P[:, 1] * sa, P[:, 0] * sa + P[:, 1] * ca])
        pts = shapely.points(P)
        dedge = shapely.distance(pts, poly.exterior)
        dwall = shapely.distance(pts, walls) if walls is not None and not walls.is_empty else np.full(len(P), 50.0)
        UV1 = np.column_stack([np.minimum(dedge, 50.0), np.minimum(dwall, 50.0)])
        buf.add(item.get("layer", "paved"), mat, V, UV, T, footprint=True, src=item["id"], UV1=UV1)      # layer: ADR 0114
        buf.add("collision", "collision_" + S.SURFACE_OF.get(mat, "asphalt"), V, UV, T, src=item["id"])
        _edges(buf, item, zgrid, hf, roads_poly)


EDGE_TOL_XY_M = 0.002       # ADR 0221: an edge vertex may be dropped when it lies this close to the chord in plan
EDGE_NORMAL_COS = 0.9998    # normals of neighbouring edge samples more than ~1 deg apart = the outline turns there
EDGE_TOL_Z_M = 0.005        # ... and this close in height (edging top is 30 mm proud, the skirt 300 mm deep) WORKING_VALUE


def _edge_keep(P, Z, skip, nout=None):
    """Indices of the edge vertices that carry shape (Douglas-Peucker in plan and in height, ADR 0221). Vertices where
    the built / skipped state changes are always kept, so every remaining segment is built or skipped as a whole.
    nout: outward normals of the dense vertices; where a kept vertex has a normal that differs from its dense
    neighbours (a corner: the normal there is the bisector) the neighbours stay too, so the edging keeps its full
    width and the skirt its batter right up to the corner instead of tapering along the whole side."""
    n = len(P)
    Q = np.column_stack([P * (EDGE_TOL_Z_M / EDGE_TOL_XY_M), Z])
    must = np.zeros(n, bool)
    must[[0, n - 1]] = True
    must[1:-1] = skip[1:] != skip[:-1]
    if n > 3 and float(np.hypot(*(P[0] - P[-1]))) < 1e-6:      # closed ring: one more anchor, far from the start
        must[int(np.argmax(np.hypot(*(P - P[0]).T)))] = True
    anchors = np.flatnonzero(must)
    keep = must.copy()
    stack = [(int(a), int(b)) for a, b in zip(anchors[:-1], anchors[1:])]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        ab = Q[b] - Q[a]
        L2 = float(ab @ ab)
        w = Q[a + 1:b] - Q[a]
        if L2 < 1e-12:
            d = np.linalg.norm(w, axis=1)
        else:
            tpar = np.clip(w @ ab / L2, 0.0, 1.0)
            d = np.linalg.norm(w - np.outer(tpar, ab), axis=1)
        k = int(np.argmax(d))
        if d[k] > EDGE_TOL_Z_M:
            keep[a + 1 + k] = True
            stack += [(a, a + 1 + k), (a + 1 + k, b)]
    if nout is not None and n > 2:
        turn = np.einsum("ij,ij->i", nout[1:], nout[:-1]) < EDGE_NORMAL_COS      # dense segment k: normals k, k+1 differ
        for i in np.flatnonzero(keep):
            if i > 0 and turn[i - 1]:
                keep[i - 1] = True
            if i < n - 1 and turn[i]:
                keep[i + 1] = True
    return np.flatnonzero(keep)


def _edges(buf, item, zgrid, hf, roads_poly=None):
    """Outer edge: concrete edging strip (paving blocks) or flush flange (concrete / asphalt)."""
    poly, mat = item["poly"], item["mat"]
    edged = mat in EDGED and item.get("edging", True)      # ADR 0114: plot driveways end flush (no extra material)
    for ring in [poly.exterior, *poly.interiors]:
        c = np.asarray(ring.coords)
        if len(c) < 3:
            continue
        if not ring.is_ccw ^ (ring is not poly.exterior):
            c = c[::-1]                           # exterior CCW, holes CW: outward normal on the right
        seg = np.diff(c, axis=0)
        L = np.hypot(seg[:, 0], seg[:, 1])
        # densify every 2 m to follow the ground
        pts = [c[0]]
        for k in range(len(seg)):
            nsub = max(1, int(math.ceil(L[k] / 2.0)))
            for t in range(1, nsub + 1):
                pts.append(c[k] + seg[k] * t / nsub)
        P = np.asarray(pts)
        if len(P) < 3:
            continue
        d = np.gradient(P, axis=0)
        d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
        nout = np.column_stack([d[:, 1], -d[:, 0]])        # right of travel = outside for CCW ring
        zf = np.nan_to_num(zgrid, nan=0.0)
        Z = bilinear(zf, hf, P[:, 0], P[:, 1]) + S.PAVED_LIFT
        n = len(P)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        if edged:
            ew, eh = S.EDGING_W, S.EDGING_H
            A = np.column_stack([P, Z + eh])
            B = np.column_stack([P + nout * ew, Z + eh])
            C = np.column_stack([P + nout * ew, Z - S.PAVED_FLANGE])
            D = np.column_stack([P, Z])
            rows = [D, A, B, C]
        else:
            rows = [np.column_stack([P, Z]), np.column_stack([P + nout * (S.PAVED_FLANGE * S.EMBANKMENT_SLOPE), Z - S.PAVED_FLANGE])]   # battered skirt (W-H5)
        # no edging / flange where the area meets a road surface (the road owns that edge)
        if roads_poly is not None and not roads_poly.is_empty:
            mid = 0.5 * (P[1:] + P[:-1])
            skip = shapely.distance(shapely.points(mid), roads_poly) < 0.6
        else:
            skip = np.zeros(n - 1, bool)
        # ADR 0188: no edging / flange either where the area abuts its sibling strip (cycle track | footway of one
        # segregated path: one flush edging between them is laid by cycleways.paint)
        if item.get("skip_edge") is not None:
            skip |= shapely.distance(shapely.points(0.5 * (P[1:] + P[:-1])), item["skip_edge"]) < 0.3
        # ADR 0221: the 2 m samples are needed only where the ground bends; on a straight edge over smoothed ground
        # they were 6 triangles every 2 m for nothing (77 k triangles in one view of region C)
        keep = _edge_keep(P, Z, skip, nout)
        rows = [r_[keep] for r_ in rows]
        skip = skip[keep[:-1]]
        s, n = s[keep], len(keep)
        V = np.concatenate(rows)
        UV = np.column_stack([np.tile(s, len(rows)), np.repeat(np.arange(len(rows)) * 0.1, n)])
        T = []
        for r in range(len(rows) - 1):
            a0 = r * n
            b0 = (r + 1) * n
            for k in range(n - 1):
                if skip[k]:
                    continue
                T.append((a0 + k, b0 + k + 1, a0 + k + 1))      # faces to the right of travel (outward)
                T.append((a0 + k, b0 + k, b0 + k + 1))
        if T:
            buf.add(item.get("layer", "paved"), "curb_concrete" if edged else mat, V, UV, np.asarray(T), src=item["id"] + ":edge")
