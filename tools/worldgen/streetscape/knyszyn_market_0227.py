"""Four open market canopies, opt-in data for Knyszyn (ADR 0227).

Roof footprints are supplied as EPSG:2180 polygons by the region override;
they are interpreted as eaves traced from GUGiK 2025 (SOURCED/ESTIMATED),
not survey positions of the supporting posts.  Owner photographs determine
the open structure, dark hipped roofs, counters and photovoltaic panels.
Eave height, pitch, steel section, counter height and post rhythm are
WORKING_VALUE until measured.  Images are reference only, never textures.

No object is emitted without an explicit valid four-canopy override.  Terrain
is sampled in the same local frame as the conformed streetscape.  The module
does not add paving, alter buildings or infer dimensions from an OSM polygon.
"""
from __future__ import annotations

import math

import numpy as np
from shapely.geometry import Polygon

from . import buildings_mesh as BM

REGION = "knyszyn"
KIND = "market_canopies_0227"
ASSET_ID = "knyszyn_market_canopies_0227"
LAYERS = ("buildings", "buildings_low")
EAVE_M = 3.20             # WORKING_VALUE, photo-estimated
RIDGE_RISE_M = .85        # WORKING_VALUE, photo-estimated
POST_HALF_M = .09         # WORKING_VALUE
POST_END_INSET_M = .55    # WORKING_VALUE, eave overhang
POST_SPACING_M = 3.4      # WORKING_VALUE, not surveyed
COUNTER_HEIGHT_M = .88    # WORKING_VALUE
EAVE_INSET_M = .25        # WORKING_VALUE within the 0.5–1 m tracing tolerance
FENCE_HEIGHT_M = 1.40     # WORKING_VALUE from owner photograph, not surveyed
FENCE_BAY_M = 2.50        # WORKING_VALUE
LOW_STRUCTURE_MAT = "hall_flashing"  # existing dark metal; visual QA / budget trial


def _point(xy, z):
    return np.array([float(xy[0]), float(xy[1]), float(z)], dtype=float)


def _rect_frame(raw, origin):
    """Long/short axes and envelope derived from four measured eave corners."""
    points = np.asarray(raw, dtype=float)
    if points.shape != (4, 2) or not np.isfinite(points).all():
        raise ValueError("market canopy requires four finite EPSG:2180 corners")
    poly = Polygon(points - origin)
    if not poly.is_valid or poly.area < 1.0:
        raise ValueError("market canopy eave polygon is invalid")
    rect = poly.minimum_rotated_rectangle
    corners = np.asarray(rect.exterior.coords, dtype=float)[:4]
    edges = np.roll(corners, -1, axis=0) - corners
    lengths = np.linalg.norm(edges, axis=1)
    idx = int(np.argmax(lengths))
    # The measured quadrilaterals are slightly non-rectangular; their minimum
    # rectangles can overlap even though the measured outlines do not.  The
    # modest symmetric inset avoids inventing a larger roof than the trace.
    length = float(lengths[idx]) - 2*EAVE_INSET_M
    width = float(lengths[(idx + 1) % 4]) - 2*EAVE_INSET_M
    if length < 2.0 or width < 1.0 or length <= width:
        raise ValueError("market canopy requires an elongated footprint")
    axis = edges[idx] / lengths[idx]
    across = np.array([-axis[1], axis[0]])
    center = np.asarray(rect.centroid.coords[0], dtype=float)
    return center, axis, across, length, width


def _box(acc, layer, material, center, axis, across, half_length, half_width, z0, z1):
    acc.box(layer, material, _point(center, (z0 + z1) / 2),
            np.r_[axis * half_length, 0.], np.r_[across * half_width, 0.],
            [0., 0., (z1 - z0) / 2], skip=(0,))


def _roof(acc, layer, center, axis, across, length, width, base, solar):
    """Low-hip roof: four outside planes and a visible underside."""
    hl, hw = length / 2., width / 2.
    ridge = max(0., hl - hw)
    corners = [center + axis*a + across*b for a, b in
               ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]
    e = [_point(c, base) for c in corners]
    r0 = _point(center - axis*ridge, base + RIDGE_RISE_M)
    r1 = _point(center + axis*ridge, base + RIDGE_RISE_M)
    acc.quad(layer, "roof_metal_graphite", e[0], e[1], r1, r0)
    acc.add(layer, "roof_metal_graphite", [e[1], e[2], r1], [[0, 1, 2]])
    acc.quad(layer, "roof_metal_graphite", e[2], e[3], r0, r1)
    acc.add(layer, "roof_metal_graphite", [e[3], e[0], r0], [[0, 1, 2]])
    acc.quad(layer, "hall_flashing", e[3], e[2], e[1], e[0])
    if not solar:
        return
    # The two visible rows of panels are visual approximations. High uses
    # separated modules; Low uses one sheet per roof slope with the same bounds.
    span = ridge * .90
    count = 10 if layer == "buildings" else 1
    for side in (-1, 1):
        for i in range(count):
            a0 = -span + 2*span*i/count + .025
            a1 = -span + 2*span*(i+1)/count - .025
            b0, b1 = side*hw*.25, side*hw*.70
            if side < 0:
                b0, b1 = b1, b0
            def p(a, b):
                return _point(center + axis*a + across*b,
                              base + RIDGE_RISE_M*(1-abs(b)/hw) + .018)
            acc.quad(layer, "glass", p(a0,b0), p(a1,b0), p(a1,b1), p(a0,b1))


def _post_positions(center, axis, across, length, width):
    count = max(2, int(math.ceil(max(0., length-2*POST_END_INSET_M)/POST_SPACING_M))+1)
    positions = np.linspace(-length/2+POST_END_INSET_M, length/2-POST_END_INSET_M, count)
    transverse = max(0., width/2-.30)
    points = np.asarray([center + axis*along + across*(side*transverse)
                         for side in (-1, 1) for along in positions])
    return positions, transverse, points


def _canopy(acc, center, axis, across, length, width, ground, solar, post_heights):
    base = ground + EAVE_M
    positions, transverse, _ = _post_positions(center, axis, across, length, width)
    count = len(positions)
    for layer in LAYERS:
        structure_mat = LOW_STRUCTURE_MAT if layer == "buildings_low" else "steel_painted"
        _roof(acc, layer, center, axis, across, length, width, base, solar)
        for side_index, side in enumerate((-1, 1)):
            for index, along in enumerate(positions):
                at = center + axis*along + across*(side*transverse)
                _box(acc, layer, structure_mat, at, axis, across,
                     POST_HALF_M, POST_HALF_M, post_heights[side_index*count+index]-.05, base)
            # Continuous dark support beam under the eave.
            at = center + across*(side*transverse)
            _box(acc, layer, structure_mat, at, axis, across,
                 length/2-.25, .065, base-.14, base)
        # Long counters under each roof; simplified but visible from the street.
        for side in (-1, 1):
            at = center + across*(side*width*.19)
            _box(acc, layer, structure_mat, at, axis, across,
                 length/2-.8, .30, ground+COUNTER_HEIGHT_M, ground+COUNTER_HEIGHT_M+.075)
            for along in positions[::2]:
                _box(acc, layer, structure_mat, at+axis*along, axis, across,
                     .035, .035, ground, ground+COUNTER_HEIGHT_M)
    for side_index, side in enumerate((-1, 1)):
        for index, along in enumerate(positions):
            at = center + axis*along + across*(side*transverse)
            _box(acc, "collision", "collision_steel", at, axis, across,
                 POST_HALF_M, POST_HALF_M, post_heights[side_index*count+index]-.05, base)
    return count*2


def _fence_plan(points):
    """Subdivide each explicit segment; never join separate fence polylines."""
    post_points = []
    bays = []
    for a, b in zip(points, points[1:]):
        delta = b-a
        length = float(np.linalg.norm(delta))
        if length < .2:
            raise ValueError("market fence contains a zero-length segment")
        count = max(1, int(math.ceil(length/FENCE_BAY_M)))
        segment = [a + delta*(i/count) for i in range(count+1)]
        if post_points:
            segment_start = len(post_points)-1
            post_points.extend(segment[1:])
        else:
            segment_start = 0
            post_points.extend(segment)
        bays.extend((segment_start+i, segment_start+i+1) for i in range(count))
    return np.asarray(post_points, dtype=float), bays


def _fence(acc, points, heights, bays):
    """Open black panel fence; each input polyline is a separate object."""
    for i, at in enumerate(points):
        # Round-ish square steel posts; no horizontal elements across openings.
        for layer in (*LAYERS, "collision"):
            mat = ("collision_steel" if layer == "collision" else
                   LOW_STRUCTURE_MAT if layer == "buildings_low" else "steel_painted")
            _box(acc, layer, mat, at, np.array([1., 0.]), np.array([0., 1.]),
                 .035, .035, heights[i]-.05, heights[i]+FENCE_HEIGHT_M)
    for ia, ib in bays:
        a, b = points[ia], points[ib]
        d = b-a; length = float(np.linalg.norm(d)); axis = d/length
        across = np.array([-axis[1], axis[0]])
        center = (a+b)/2
        z = (heights[ia]+heights[ib])/2
        # A solid simplified collision per bay; no collider is created in the
        # gap between separate polylines, so the market entrance remains open.
        _box(acc, "collision", "collision_steel", center, axis, across,
             length/2, .025, z-.05, z+FENCE_HEIGHT_M)
        for layer in LAYERS:
            structure_mat = LOW_STRUCTURE_MAT if layer == "buildings_low" else "steel_painted"
            for offset in (.15, FENCE_HEIGHT_M-.15):
                _box(acc, layer, structure_mat, center, axis, across,
                     length/2, .018, z+offset-.018, z+offset+.018)
            if layer == "buildings":
                # Sparse, two-sided wire silhouettes; Low retains posts/rails.
                for j in range(1, 6):
                    f = j/6
                    at = a + d*f
                    zj = heights[ia]*(1-f)+heights[ib]*f
                    p = at-axis*.008; q = at+axis*.008
                    lo1, lo2 = _point(p,zj+.15), _point(q,zj+.15)
                    hi1, hi2 = _point(p,zj+FENCE_HEIGHT_M-.15), _point(q,zj+FENCE_HEIGHT_M-.15)
                    acc.quad(layer, "steel_painted", lo1, lo2, hi2, hi1)
                    acc.quad(layer, "steel_painted", lo2, lo1, hi1, hi2)


def build(buf, region, origin, overrides, zsurf, report):
    """Emit the four roofs only for one explicit region override.

    Expected override: ``kind: market_canopies_0227``, ``canopies`` is a list
    of four mappings with unique ``id``, ``polygon_epsg2180`` (four corners)
    and optional ``solar_panels`` boolean.  Optional ``fences`` is a list of
    ``{id, points_epsg2180}`` open polylines; gaps between them remain open.
    Refuse malformed and ambiguous inputs before emitting any geometry.
    """
    result = {"id": ASSET_ID, "status": "skipped", "canopies": [], "fences": [],
              "footprints": "GUGiK 2025 eaves: SOURCED/ESTIMATED",
              "details": "WORKING_VALUE; owner photos; visual QA OPEN"}
    if region != REGION:  # ADR 0227: other regions get no QA entry (no diff in their streetscape_qa.json)
        return result
    report[ASSET_ID] = result
    candidates = [o for o in overrides if o.get("kind") == KIND]
    if not candidates:
        result["reason"] = "no authored market canopy override"
        return result
    if len(candidates) != 1:
        raise ValueError("exactly one market canopy override is required")
    origin = np.asarray(origin, dtype=float)
    if origin.shape != (2,) or not np.isfinite(origin).all():
        raise ValueError("invalid region origin")
    objects = candidates[0].get("canopies")
    if not isinstance(objects, list) or len(objects) != 4:
        raise ValueError("exactly four market canopies are required")
    ids = [o.get("id") for o in objects if isinstance(o, dict)]
    if len(ids) != 4 or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != 4:
        raise ValueError("market canopy ids must be distinct non-empty strings")
    parsed = []
    for obj in objects:
        solar = obj.get("solar_panels", False)
        if not isinstance(solar, bool):
            raise ValueError("solar_panels must be boolean")
        center, axis, across, length, width = _rect_frame(obj.get("polygon_epsg2180"), origin)
        ground = float(np.asarray(zsurf(np.array([center[0]]), np.array([center[1]]))).ravel()[0])
        if not math.isfinite(ground):
            raise ValueError("market canopy terrain sample is not finite")
        _, _, post_points = _post_positions(center, axis, across, length, width)
        post_heights = np.asarray(zsurf(post_points[:, 0], post_points[:, 1]), dtype=float).reshape(-1)
        if (len(post_heights) != len(post_points) or not np.isfinite(post_heights).all()
                or np.any(post_heights > ground + EAVE_M - 1.5)):
            raise ValueError("market canopy post ground samples are invalid")
        parsed.append((obj["id"], center, axis, across, length, width, ground, solar, post_heights))
    fences = candidates[0].get("fences", [])
    if not isinstance(fences, list):
        raise ValueError("market fences must be a list")
    fence_ids = [f.get("id") for f in fences if isinstance(f, dict)]
    if len(fence_ids) != len(fences) or any(not isinstance(i, str) or not i for i in fence_ids) or len(set(fence_ids)) != len(fence_ids):
        raise ValueError("market fence ids must be distinct non-empty strings")
    fence_plans = []
    for fence in fences:
        raw = np.asarray(fence.get("points_epsg2180"), dtype=float)
        if raw.ndim != 2 or raw.shape[1:] != (2,) or len(raw) < 2 or not np.isfinite(raw).all():
            raise ValueError("market fence requires at least two finite points")
        if np.linalg.norm(raw[0]-raw[-1]) < .2:
            raise ValueError("market fence must be open; declare gates as separate polylines")
        points, bays = _fence_plan(raw-origin)
        heights = np.asarray(zsurf(points[:,0], points[:,1]), dtype=float).reshape(-1)
        if len(heights) != len(points) or not np.isfinite(heights).all():
            raise ValueError("market fence ground samples are invalid")
        fence_plans.append((fence["id"], points, heights, bays))
    for oid, center, axis, across, length, width, ground, solar, post_heights in parsed:
        acc = BM.Acc()
        posts = _canopy(acc, center, axis, across, length, width, ground, solar, post_heights)
        acc.flush(buf, f"{ASSET_ID}:{oid}")
        result["canopies"].append({"id": oid, "eave_length_m": round(length, 2),
                                   "eave_width_m": round(width, 2), "posts": posts,
                                   "solar_panels": solar})
    for oid, points, heights, bays in fence_plans:
        acc = BM.Acc()
        _fence(acc, points, heights, bays)
        acc.flush(buf, f"{ASSET_ID}:fence:{oid}")
        result["fences"].append({"id": oid, "posts": len(points), "bays": len(bays)})
    result["status"] = "applied"
    return result
