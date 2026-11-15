"""Knyszyn church landmark, authored from the BDOT footprint and owner references.

Integration: pass ``hero_targets(region, fc)`` to buildings_mesh.load's ``hero``
argument, so its original footprint retains the existing collision and keepout;
after buildings_mesh.build call ``build(buf, region, blds, zsmooth, report)``.
The output is deterministic in the normal buildings and buildings_low layers.

Plan and overall tower height come from BDOT10k / GUGiK LoD2 (2017), as recorded
in buildings.geojson. Individual roof and tower proportions are WORKING_VALUE,
estimated from owner pictures 5–7 and K1-P15/P16; not measured architecture.
No source photograph is used as texture. Requires visual and budget validation.
"""
from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import Polygon

from . import buildings_mesh as BM

REGION = "knyszyn"
BUILDING_ID = "bdot:2002917F-8DAE-5C99-E053-CC2BA8C01CFC"
ASSET_ID = "knyszyn_church_0227"
LAYERS = ("buildings", "buildings_low")


def _heights(props):
    """Read GUGiK heights; the fallback values are WORKING_VALUE."""
    values = (float(props.get("lod2_eave_rel_m") or 5.85),
              float(props.get("height_lod1_2024_m") or 14.24),
              float(props.get("height_lod2_2017_m") or 33.43))
    if not all(math.isfinite(x) for x in values) or not 3 < values[0] < values[1] < values[2]:
        return None
    return values


def hero_targets(region, feature_collection):
    """Opt in only with an unambiguous feature and sensible source heights."""
    if region != REGION:
        return {}
    features = [f for f in feature_collection["features"] if f.get("id") == BUILDING_ID]
    if len(features) != 1 or _heights(features[0].get("properties", {})) is None:
        return {}
    return {BUILDING_ID: ASSET_ID}


def _pt(xy, z):
    return [float(xy[0]), float(xy[1]), float(z)]


def _gable(acc, layer, poly, center, along, normal, length, width, eave, ridge):
    """Two sloping planes clipped to the footprint, with walls up to their edges."""
    a, b = center - along * length / 2, center + along * length / 2
    al, ar, bl, br = a - normal * width / 2, a + normal * width / 2, b - normal * width / 2, b + normal * width / 2

    def roof_z(p):
        d = abs(float(np.dot(p - center, normal)))
        return eave + (ridge - eave) * max(0.0, 1.0 - d / (width / 2))

    # Clip each side separately so no triangle spans the ridge's change in slope.
    for half in (Polygon([al, bl, b, a]), Polygon([br, ar, a, b])):
        clipped = shapely.make_valid(poly.intersection(half))
        for part in getattr(clipped, "geoms", [clipped]):
            if part.geom_type != "Polygon" or part.area < 1e-8:
                continue
            for tri in shapely.constrained_delaunay_triangles(part).geoms:
                points = np.asarray(tri.exterior.coords, float)[:3]
                e0, e1 = points[1] - points[0], points[2] - points[0]
                if e0[0] * e1[1] - e0[1] * e1[0] < 0:
                    points = points[::-1]
                acc.add(layer, "roof_tiles_red", [_pt(p, roof_z(p)) for p in points], [[0, 1, 2]])

    # Where the actual outline falls inside the enclosing rectangle, its roof
    # edge is above eaves. Fill the gap along each exterior segment. Split at
    # the ridge so the top edge follows the two plane equations exactly.
    ring = np.asarray(poly.exterior.coords, float)
    for p, q in zip(ring[:-1], ring[1:]):
        dp, dq = np.dot(p - center, normal), np.dot(q - center, normal)
        segments = [(p, q)]
        if dp * dq < 0:
            mid = p + (q - p) * (dp / (dp - dq))
            segments = [(p, mid), (mid, q)]
        for x, y in segments:
            zx, zy = roof_z(x), roof_z(y)
            if zy > eave + 1e-7:
                acc.add(layer, "plaster_white", [_pt(x, eave), _pt(y, eave), _pt(y, zy)], [[0, 1, 2]])
            if zx > eave + 1e-7:
                acc.add(layer, "plaster_white", [_pt(x, eave), _pt(y, zy), _pt(x, zx)], [[0, 1, 2]])


def _octagon(acc, layer, center, radius, z0, z1, mat):
    ring = [center + radius * np.array([math.cos(math.pi/8 + i*math.pi/4),
                                       math.sin(math.pi/8 + i*math.pi/4)]) for i in range(8)]
    for i in range(8):
        a, b = ring[i], ring[(i+1) % 8]
        acc.quad(layer, mat, _pt(a, z0), _pt(b, z0), _pt(b, z1), _pt(a, z1))
    return ring


def _arch(acc, layer, a, b, z0, height, outward):
    """Dark arched inset, slightly offset from wall to avoid coplanar flicker."""
    d = b - a
    width = float(np.linalg.norm(d))
    if width < 0.1:
        return
    d /= width
    radius = width / 2
    base = a + outward * 0.025
    spring = z0 + height - radius
    verts = [_pt(base, z0), _pt(base + d * width, z0), _pt(base + d * width, spring)]
    for i in range(1, 9):
        angle = math.pi * i / 8
        verts.append(_pt(base + d * (radius + radius * math.cos(angle)), spring + radius * math.sin(angle)))
    # A fan over a convex arched polygon: no extra material and no transparent surface.
    tris = [[0, i, i + 1] for i in range(1, len(verts) - 1)]
    acc.add(layer, "glass", verts, tris)


def _wall_window(poly, target, wanted_outward, width=1.5):
    """Place a window on the nearest sufficiently long, outward-facing footprint edge.

    BM.load orients the exterior CCW, so the right normal of an edge faces out.
    The centre is clamped to keep the whole opening on the same wall segment.
    """
    ring = np.asarray(poly.exterior.coords, float)
    candidates = []
    for p, q in zip(ring[:-1], ring[1:]):
        edge = q - p
        length = float(np.linalg.norm(edge))
        if length < width + 0.1:
            continue
        tangent = edge / length
        outward = np.array([tangent[1], -tangent[0]])
        if float(np.dot(outward, wanted_outward)) < .5:
            continue
        u = float(np.clip(np.dot(target - p, tangent), width / 2, length - width / 2))
        middle = p + tangent * u
        candidates.append((float(np.linalg.norm(target - middle)), middle, tangent, outward))
    if not candidates:
        return None
    _, middle, tangent, outward = min(candidates, key=lambda v: v[0])
    return middle - tangent * width / 2, middle + tangent * width / 2, outward


def build(buf, region, blds, zsmooth, report):
    """Build the replacement. `blds` are BM.load's local-E/N polygons.

    Return a QA entry. No-op for another region or missing source footprint.
    Call only with the matching `hero_targets` map applied to BM.load.
    """
    result = {"id": ASSET_ID, "status": "skipped", "source": BUILDING_ID}
    report[ASSET_ID] = result
    if region != REGION:
        return result
    matches = [b for b in blds if b["id"] == BUILDING_ID]
    if len(matches) != 1:
        result["reason"] = "source footprint missing or ambiguous"
        return result
    b = matches[0]
    if b["ovr"].get("hero_asset") != ASSET_ID:
        result["reason"] = "hero target was not installed; refusing to overlap the generic building"
        return result
    poly = b["poly"]
    ring = np.asarray(poly.exterior.coords, float)
    z = float(np.median(np.asarray(zsmooth(ring[:, 0], ring[:, 1]), float)))
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords, float)[:4]
    edges = np.roll(rect, -1, axis=0) - rect
    i = int(np.argmax(np.linalg.norm(edges, axis=1)))
    along = edges[i] / np.linalg.norm(edges[i])
    if along[0] > 0:  # front / tower is the north-west end (photo + orthophoto)
        along = -along
    normal = np.array([-along[1], along[0]])
    length = float(np.linalg.norm(edges[i])); width = float(np.linalg.norm(edges[(i+1) % 4]))
    center = np.asarray(poly.minimum_rotated_rectangle.centroid.coords[0], float)
    # GUGiK LoD2 roof/eave data, while the subdivisions and tower dimensions are photographic estimates.
    heights = _heights(b["props"])
    if heights is None or not math.isfinite(z):
        result["reason"] = "inconsistent source heights"
        return result
    eave, ridge, tip = (z + h for h in heights)
    tower = center + along * (length / 2 - 4.6)
    acc = BM.Acc()
    # The measured outline is used for walls and collision. Roof is an estimated simplified gable.
    for layer in LAYERS:
        for a, c in zip(ring[:-1], ring[1:]):
            acc.quad(layer, "plaster_white", _pt(a, z - .3), _pt(c, z - .3), _pt(c, eave), _pt(a, eave))
        _gable(acc, layer, poly, center, along, normal, length, width, eave, ridge)
        # Tower rises from the front end; LoD2 overall height anchors the distinctive red spire.
        acc.box(layer, "plaster_white", _pt(tower, z + 10.0), np.r_[along * 3.25, 0],
                np.r_[normal * 3.25, 0], [0, 0, 10.0], skip=(0,))
        lower, upper = z + 20.0, z + 25.2
        ring8 = _octagon(acc, layer, tower, 3.05, lower, upper, "plaster_white")
        for k in range(8):
            a, c = ring8[k], ring8[(k+1) % 8]
            outward = (a + c) / 2 - tower; outward /= np.linalg.norm(outward)
            _arch(acc, layer, a * .66 + c * .34, a * .34 + c * .66, lower + 1.1, 3.2, outward)
            # Triangle winding of the cone faces points outward.
            acc.add(layer, "roof_tiles_red", [_pt(a, upper), _pt(c, upper), _pt(tower, tip)], [[0, 1, 2]])
        # Tall rounded side windows repeat along both long faces (positions WORKING_VALUE).
        for s in (-1, 1):
            out = normal * s
            for t in (-.25, .02, .29):
                mid = center + along * (length * t) + out * (width / 2 + .03)
                opening = _wall_window(poly, mid, out)
                if opening is not None:
                    a, c, wall_outward = opening
                    _arch(acc, layer, a, c, z + 1.8, 3.3, wall_outward)
    # Dark low-tier window material is already present in these building chunks.
    low_glass = acc.d.pop(("buildings_low", "glass"), [])
    if low_glass:
        acc.d.setdefault(("buildings_low", "plinth_dark"), []).extend(low_glass)
    low_white = acc.d.pop(("buildings_low", "plaster_white"), [])
    if low_white:
        acc.d.setdefault(("buildings_low", "plaster_light"), []).extend(low_white)
    acc.flush(buf, ASSET_ID)
    result.update(status="applied", height_lod2_m=round(tip-z, 2), eave_m=round(eave-z, 2),
                  height_source="GUGiK LoD2 2017", proportions="WORKING_VALUE", bounds_local=list(poly.bounds))
    return result
