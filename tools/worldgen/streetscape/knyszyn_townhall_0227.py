"""Knyszyn town hall and cultural centre, authored from their two BDOT footprints.

``hero_targets(region, fc)`` must be merged into buildings_mesh.load's hero map;
``build(buf, region, blds, zsmooth, report)`` then adds the visible replacement.
The original buildings_mesh code retains each footprint for collision and masks.

Plan, LoD1 heights and LoD2 eaves are from GUGiK/BDOT. Architecture and facade
rhythm are estimated from owner reference images 1–4: white render, yellow window
surrounds, brown plinth, red hipped roof, dormers and four-column loggia. Exact
positions and dimensions of openings, dormers, steps and columns are WORKING_VALUE.
No photograph, emblem, text or brand is included as an asset or a texture.
Requires visual comparison and a per-camera budget check before acceptance.
"""
from __future__ import annotations

import math

import numpy as np

from . import buildings_mesh as BM

REGION = "knyszyn"
OFFICE = "bdot:2002917F-46DC-5C99-E053-CC2BA8C01CFC"
CULTURE = "bdot:2002917F-4817-5C99-E053-CC2BA8C01CFC"
IDS = (OFFICE, CULTURE)
ASSET_ID = "knyszyn_townhall_0227"
LAYERS = ("buildings", "buildings_low")


def _heights(props):
    try:
        eave = float(props.get("lod2_eave_rel_m") or 8.5)
        top = float(props.get("height_lod1_2024_m") or 12.0)
    except (TypeError, ValueError):
        return None
    return (eave, top) if math.isfinite(eave) and math.isfinite(top) and 4 < eave < top else None


def hero_targets(region, feature_collection):
    """All-or-nothing: avoid dropping either original when a source is missing."""
    if region != REGION:
        return {}
    features = [f for f in feature_collection["features"] if f.get("id") in IDS]
    if len(features) != 2 or {f["id"] for f in features} != set(IDS):
        return {}
    if any(_heights(f.get("properties", {})) is None for f in features):
        return {}
    return {bid: ASSET_ID for bid in IDS}


def _pt(xy, z):
    return [float(xy[0]), float(xy[1]), float(z)]


def _frame(poly):
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords, float)[:4]
    edges = np.roll(rect, -1, axis=0) - rect
    k = int(np.argmax(np.linalg.norm(edges, axis=1)))
    axis = edges[k] / np.linalg.norm(edges[k])
    return (np.asarray(poly.minimum_rotated_rectangle.centroid.coords[0], float), axis,
            np.array([-axis[1], axis[0]]), float(np.linalg.norm(edges[k])),
            float(np.linalg.norm(edges[(k+1) % 4])))


def _face(acc, layer, mat, center, axis, normal, width, z0, z1, offset):
    """Vertical CCW face viewed from normal, with a small depth separation."""
    p = center + normal * offset
    # axis must point with its right-hand normal towards the viewer.
    if np.dot(np.array([axis[1], -axis[0]]), normal) < 0:
        axis = -axis
    a, b = p - axis * width / 2, p + axis * width / 2
    acc.quad(layer, mat, _pt(a, z0), _pt(b, z0), _pt(b, z1), _pt(a, z1))


def _hip_roof(acc, layer, center, axis, normal, length, width, eave, ridge):
    # A four-slope roof; ridge ends inset by half-width (WORKING_VALUE).
    a, b = center - axis * length / 2, center + axis * length / 2
    al, ar, bl, br = a-normal*width/2, a+normal*width/2, b-normal*width/2, b+normal*width/2
    inset = min(width * .5, length * .3)
    ra, rb = a + axis * inset, b - axis * inset
    # Normal direction is always +90° to axis in this helper.
    acc.quad(layer, "roof_tiles_red", _pt(al,eave), _pt(bl,eave), _pt(rb,ridge), _pt(ra,ridge))
    acc.quad(layer, "roof_tiles_red", _pt(br,eave), _pt(ar,eave), _pt(ra,ridge), _pt(rb,ridge))
    acc.add(layer, "roof_tiles_red", [_pt(ar,eave), _pt(al,eave), _pt(ra,ridge),
                                      _pt(bl,eave), _pt(br,eave), _pt(rb,ridge)], [[0,1,2],[3,4,5]])


def _dormer(acc, layer, center, axis, out, eave, rise):
    """Modest white dormer with a red gable, standing on the roof plane."""
    z0 = eave + rise * .25
    # Half axes in E,N,Z. The roof plane rises inward; this box partly intersects it.
    acc.box(layer, "plaster_white", _pt(center, z0+.5), np.r_[axis*.70, 0],
            np.r_[out*.65, 0], [0, 0, .65], skip=(0,))
    _face(acc, layer, "glass", center, axis, out, .75, z0+.27, z0+1.12, .656)
    front, back = center+out*.65, center-out*.65
    a, b, c, d = front-axis*.8, front+axis*.8, back+axis*.8, back-axis*.8
    peak0, peak1 = front, back
    # Roof is above the white box; normals checked independently of axis sign.
    za, zp = z0+1.15, z0+1.53
    faces = [[_pt(a,za), _pt(d,za), _pt(peak1,zp), _pt(peak0,zp)],
             [_pt(c,za), _pt(b,za), _pt(peak0,zp), _pt(peak1,zp)]]
    if axis[0]*out[1] - axis[1]*out[0] < 0:
        faces = [f[::-1] for f in faces]
    for face in faces:
        acc.quad(layer, "roof_tiles_red", *face)


def build(buf, region, blds, zsmooth, report):
    result = {"id": ASSET_ID, "status": "skipped", "sources": list(IDS)}
    report[ASSET_ID] = result
    if region != REGION:
        return result
    selected = {b["id"]: b for b in blds if b["id"] in IDS}
    if set(selected) != set(IDS) or any(b["ovr"].get("hero_asset") != ASSET_ID for b in selected.values()):
        result["reason"] = "both hero targets required; refusing overlap with generic buildings"
        return result
    bases = []
    for b in selected.values():
        ring = np.asarray(b["poly"].exterior.coords, float)
        bases.append(float(np.median(np.asarray(zsmooth(ring[:,0], ring[:,1]), float))))
    if any(not math.isfinite(v) for v in bases) or any(_heights(b["props"]) is None for b in selected.values()):
        result["reason"] = "invalid height data"
        return result
    z = float(np.median(bases))
    acc = BM.Acc()
    frames = {bid: _frame(selected[bid]["poly"]) for bid in IDS}
    for bid in IDS:
        b = selected[bid]
        poly = b["poly"]
        ring = np.asarray(poly.exterior.coords, float)
        center, axis, normal, length, width = frames[bid]
        eave_h, top_h = _heights(b["props"])
        eave, top = z+eave_h, z+top_h
        # Office fronts the park; cultural wing's portico faces the office / courtyard.
        target = np.array([760943.5-761611, 612382.3-612607]) if bid == OFFICE else frames[OFFICE][0]
        out = normal if np.dot(target-center, normal) >= 0 else -normal
        front = center + out*width/2
        for layer in LAYERS:
            for a, c in zip(ring[:-1], ring[1:]):
                acc.quad(layer, "plinth_dark", _pt(a,z-.15), _pt(c,z-.15), _pt(c,z+.55), _pt(a,z+.55))
                acc.quad(layer, "plaster_white", _pt(a,z+.55), _pt(c,z+.55), _pt(c,eave), _pt(a,eave))
            _hip_roof(acc, layer, center, axis, normal, length, width, eave, top)
            # Office face has nine window axes; culture wing is interrupted by its colonnade.
            count = 9 if bid == OFFICE else 5
            for j in range(count):
                u = (j-(count-1)/2)*min(3.6, (length-4)/max(1,count-1))
                p = front + axis*u
                for z0 in (z+1.0, z+4.55):
                    _face(acc, layer, "plaster_cream", p, axis, out, 1.55, z0, z0+2.5, .035)
                    _face(acc, layer, "glass", p, axis, out, 1.16, z0+.15, z0+2.32, .055)
            n_dormer = 8 if bid == OFFICE else 5
            for j in range(n_dormer):
                u = (j-(n_dormer-1)/2)*min(3.7, (length-7)/max(1,n_dormer-1))
                _dormer(acc, layer, front+axis*u-out*(width*.19), axis, out, eave, top-eave)
        if bid == CULTURE:
            # Four full-height cream columns and two storeys of recessed loggia; no signs or emblems.
            for layer in LAYERS:
                for u in (-6., -2., 2., 6.):
                    p = front+axis*u+out*.45
                    acc.box(layer, "plaster_cream", _pt(p,z+4.2), np.r_[axis*.25,0], np.r_[out*.25,0], [0,0,4.2], skip=(0,))
                p = front+out*.55
                acc.box(layer, "plaster_white", _pt(p,z+4.0), np.r_[axis*7.0,0], np.r_[out*.50,0], [0,0,.12], skip=(0,))
                acc.box(layer, "plinth_dark", _pt(p+out*.9,z+.24), np.r_[axis*3.0,0], np.r_[out*.9,0], [0,0,.24], skip=(0,))
    acc.flush(buf, ASSET_ID)
    result.update(status="applied", confidence={"footprints": "SOURCED BDOT10k", "heights": "SOURCED GUGiK",
                                                 "facades_and_details": "ESTIMATED / WORKING_VALUE"},
                  floors=2, roof="red hipped with gabled dormers", column_count=4)
    return result
