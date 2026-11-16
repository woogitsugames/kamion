"""Dry splash-pad detailing at Rynek, Knyszyn, ADR 0227.

Integrate with ``build(buf, region, origin, overrides, zsurf, report)`` after the
authored `rynek-fountain-plate-0227` surface and its conformed height exist.
The plate geometry and location come exclusively from that override; no basin,
collision geometry or opaque proxy water is created. A dark, flush border and
small nozzle openings approximate owner photos 4–5. Their layout and dimensions
are WORKING_VALUE, not a survey. K1-124 describes the plate and drainage.

There is no approved animated jet / spray material in this generator. Jets are
OPEN in every season, including the default summer. The dry state is a WIP, not
an artistic acceptance. An eventual transparent animated effect needs its own
mobile rendering/overdraw budget, season and on/off policy, and visual QA.
"""
from __future__ import annotations

import numpy as np
import shapely
from shapely.geometry import Point, Polygon

from . import buildings_mesh as BM

REGION = "knyszyn"
ASSET_ID = "knyszyn_fountain_0227"
PLATE_ID = "rynek-fountain-plate-0227"
BORDER_M = .15                 # WORKING_VALUE, owner photo 4
NOZZLE_RADIUS_M = .055         # WORKING_VALUE; not measured on photo
OFFSET_M = .018                # near-flush offset to avoid Z-fighting, not a rim wall


def _triangles(poly):
    """A valid set of upward-facing planar triangles, including polygons with holes."""
    for item in getattr(poly, "geoms", [poly]):
        if item.geom_type != "Polygon" or item.is_empty or item.area < 1e-9:
            continue
        for triangle in shapely.constrained_delaunay_triangles(item).geoms:
            p = np.asarray(triangle.exterior.coords, float)[:3]
            a, b = p[1]-p[0], p[2]-p[0]
            det = a[0]*b[1]-a[1]*b[0]
            if abs(det) < 1e-10:
                continue
            yield p if det > 0 else p[::-1]


def build(buf, region, origin, overrides, zsurf, report):
    result = {"id":ASSET_ID, "status":"skipped", "water_jets":"OPEN",
              "summer_behavior":"dry; dynamic jets not implemented", "other_seasons":"dry; policy OPEN",
              "source":"GUGiK K1-124 and owner photos 4–5", "layout":"ESTIMATED / WORKING_VALUE",
              "basin":False, "collision":False}
    if region != REGION:  # ADR 0227: other regions get no QA entry (no diff in their streetscape_qa.json)
        return result
    report[ASSET_ID] = result
    candidates = [o for o in overrides if o.get("id") == PLATE_ID and o.get("kind") == "paved_area"]
    if len(candidates) != 1:
        result["reason"] = "missing or ambiguous authored fountain plate"
        return result
    origin = np.asarray(origin, float)
    if origin.shape != (2,) or not np.isfinite(origin).all():
        result["reason"] = "invalid region origin"
        return result
    raw = np.asarray(candidates[0].get("polygon_epsg2180", []), float)
    if raw.ndim != 2 or raw.shape[1] != 2 or len(raw) < 3 or not np.isfinite(raw).all():
        result["reason"] = "invalid fountain plate coordinates"
        return result
    plate = Polygon(raw-origin)
    if not plate.is_valid or plate.area < 8.0:
        result["reason"] = "invalid or implausibly small fountain plate"
        return result
    inner = plate.buffer(-BORDER_M, join_style="mitre")
    if inner.is_empty or inner.geom_type != "Polygon":
        result["reason"] = "plate cannot accept a flush border"
        return result
    border = plate.difference(inner)
    rectangle = np.asarray(plate.minimum_rotated_rectangle.exterior.coords, float)[:4]
    edges = np.roll(rectangle, -1, axis=0)-rectangle
    k = int(np.argmax(np.linalg.norm(edges, axis=1)))
    along = edges[k]/np.linalg.norm(edges[k])
    across = np.array([-along[1], along[0]])
    length = float(np.linalg.norm(edges[k])); width = float(np.linalg.norm(edges[(k+1)%4]))
    center = np.asarray(plate.centroid.coords[0], float)
    nozzles = []
    # 3x3 is intentionally a working layout; the exact nozzle count is not surveyed.
    for u in (-.30,0.,.30):
        for v in (-.30,0.,.30):
            disc = Point(center+along*(u*length)+across*(v*width)).buffer(NOZZLE_RADIUS_M, quad_segs=2)
            if inner.covers(disc):
                nozzles.append(disc)
    geometry = [("plinth_dark", border)] + [("plinth_dark", p) for p in nozzles]
    triangles = [(mat, xy) for mat, polygon in geometry for xy in _triangles(polygon)]
    if not triangles:
        result["reason"] = "no valid border geometry"
        return result
    # Stage height follows the conformed paved surface, including the terrain blend.
    samples = np.concatenate([xy for _, xy in triangles])
    heights = np.asarray(zsurf(samples[:,0], samples[:,1]), float).reshape(-1)
    if len(heights) != len(samples) or not np.isfinite(heights).all():
        result["reason"] = "non-finite or incomplete paved surface heights"
        return result
    acc = BM.Acc()
    for i, (mat, xy) in enumerate(triangles):
        z = heights[3*i:3*i+3] + OFFSET_M
        acc.add("paved", mat, np.column_stack((xy,z)), [[0,1,2]])
    acc.flush(buf, ASSET_ID)
    result.update(status="applied", nozzle_count=len(nozzles), triangles=len(triangles),
                  border_width_m=BORDER_M, surface_offset_m=OFFSET_M, material_count=1)
    return result
