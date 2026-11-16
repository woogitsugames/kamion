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
import shapely
from shapely.geometry import Polygon, MultiPoint

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


def _facade(poly, target, major_axis):
    """Longest real exterior edge parallel to the wing and facing its courtyard.

    BM.load normalises each exterior to counter-clockwise, so the right-hand
    edge normal points out of the building. Do not place openings against the
    minimum rotated rectangle: concave BDOT outlines can lie metres inside it.
    """
    ring = np.asarray(poly.exterior.coords, float)
    choices = []
    for a, b in zip(ring[:-1], ring[1:]):
        d = b-a
        length = float(np.linalg.norm(d))
        if length < 3.0:
            continue
        tangent = d/length
        out = np.array([tangent[1], -tangent[0]])
        if abs(float(tangent @ major_axis)) < .95 or float((target-(a+b)/2) @ out) <= 0:
            continue
        choices.append((length, (a+b)/2, tangent, out))
    return max(choices, key=lambda item: item[0]) if choices else None


def _edges(poly, target, major_axis, *, parallel=True, omit=None):
    """Actual visible wall segments, with outward normal and positive length."""
    ring = np.asarray(poly.exterior.coords, float)
    out = []
    for a, b in zip(ring[:-1], ring[1:]):
        d = b-a; length = float(np.linalg.norm(d))
        if length < 1.75:
            continue
        tangent = d/length
        normal = np.array([tangent[1], -tangent[0]])
        align = abs(float(tangent @ major_axis))
        if (align < .95 if parallel else align > .20):
            continue
        center = (a+b)/2
        if float((target-center) @ normal) <= 0:
            continue
        if omit is not None and np.linalg.norm(center-omit) < .05:
            continue
        out.append((a, b, tangent, normal, length))
    return out


def _window_plan(poly, target, major_axis, n, omit=None, parallel=True):
    """Spread axes along the visible source-edge chain, then snap to an actual wall.

    Openings cannot cross a short/stepped BDOT edge or overlap a neighbouring axis.
    The returned tangent and outward normal belong to the edge itself.
    """
    edges = _edges(poly, target, major_axis, parallel=parallel, omit=omit)
    if not edges:
        return []
    center = np.asarray(poly.centroid.coords[0], float)
    direction = major_axis if parallel else np.array([-major_axis[1], major_axis[0]])
    bounds = [(float((a-center)@direction), float((b-center)@direction)) for a,b,*_ in edges]
    low = min(min(q) for q in bounds); high = max(max(q) for q in bounds)
    wanted = np.linspace(low+.82, high-.82, n) if high-low > 1.64 else []
    result = []
    for u in wanted:
        options = []
        for (a,b,tan,normal,length),(ua,ub) in zip(edges,bounds):
            if abs(ub-ua) < 1e-8:
                continue
            frac = float(np.clip((u-ua)/(ub-ua), .80/length, 1.-.80/length))
            p = a+(b-a)*frac
            if any(np.linalg.norm(p-old[0]) < 1.70 for old in result):
                continue
            options.append((abs(float((p-center)@direction)-u),p,tan,normal))
        if options:
            _,p,tan,normal = min(options, key=lambda v:v[0])
            result.append((p,tan,normal))
    return result


def _culture_wall(acc, layer, a, b, z, eave, facade_center, facade_len, low=False):
    """A real wall with a two-level portico cut-out, never a panel behind columns."""
    center=(a+b)/2
    base = z-.15 if low else z+.55
    if np.linalg.norm(center-facade_center) >= .05:
        acc.quad(layer,"plaster_white",_pt(a,base),_pt(b,base),_pt(b,eave),_pt(a,eave))
        return
    t=(b-a)/np.linalg.norm(b-a)
    half=min(4.7,(facade_len-1.)/2)
    left,right=center-t*half,center+t*half
    top=min(z+7.7,eave-.45)
    if low:
        acc.quad(layer,"plaster_white",_pt(a,base),_pt(b,base),_pt(b,z+.55),_pt(a,z+.55))
    acc.quad(layer,"plaster_white",_pt(a,z+.55),_pt(left,z+.55),_pt(left,eave),_pt(a,eave))
    acc.quad(layer,"plaster_white",_pt(right,z+.55),_pt(b,z+.55),_pt(b,eave),_pt(right,eave))
    acc.quad(layer,"plaster_white",_pt(left,top),_pt(right,top),_pt(right,eave),_pt(left,eave))


def _face(acc, layer, mat, center, axis, normal, width, z0, z1, offset):
    """Vertical CCW face viewed from normal, with a small depth separation."""
    p = center + normal * offset
    # axis must point with its right-hand normal towards the viewer.
    if np.dot(np.array([axis[1], -axis[0]]), normal) < 0:
        axis = -axis
    a, b = p - axis * width / 2, p + axis * width / 2
    acc.quad(layer, mat, _pt(a, z0), _pt(b, z0), _pt(b, z1), _pt(a, z1))


def _hip_roof(acc, layer, footprint, center, axis, normal, length, width, eave, ridge):
    """Four roof planes, clipped to the real polygon, including its concavities."""
    a, b = center - axis * length / 2, center + axis * length / 2
    al, ar, bl, br = a-normal*width/2, a+normal*width/2, b-normal*width/2, b+normal*width/2
    inset = min(width * .5, length * .3)
    ra, rb = a + axis * inset, b - axis * inset
    faces = [[_pt(al,eave), _pt(bl,eave), _pt(rb,ridge), _pt(ra,ridge)],
             [_pt(br,eave), _pt(ar,eave), _pt(ra,ridge), _pt(rb,ridge)],
             [_pt(ar,eave), _pt(al,eave), _pt(ra,ridge)],
             [_pt(bl,eave), _pt(br,eave), _pt(rb,ridge)]]
    for face in faces:
        xyz = np.asarray(face, float)
        # z = ax+by+c interpolates the original plane after clipping.
        coeff = np.linalg.solve(np.c_[xyz[:3, :2], np.ones(3)], xyz[:3, 2])
        clipped = shapely.intersection(Polygon(xyz[:, :2]), footprint)
        for part in getattr(clipped, "geoms", [clipped]):
            if part.geom_type != "Polygon" or part.is_empty or part.area < 1e-8:
                continue
            for triangle in shapely.constrained_delaunay_triangles(part).geoms:
                xy = np.asarray(triangle.exterior.coords, float)[:3]
                d1, d2 = xy[1]-xy[0], xy[2]-xy[0]
                signed_area2 = d1[0]*d2[1]-d1[1]*d2[0]
                if abs(signed_area2) < 1e-9:
                    continue
                if signed_area2 < 0:
                    xy = xy[::-1]
                zz = np.c_[xy, np.ones(3)] @ coeff
                acc.add(layer, "roof_tiles_red", np.column_stack((xy, zz)), [[0, 1, 2]])


def _culture_roof_height(poly, xy, eave, ridge):
    """ESTIMATED roof profile, meeting every actual BDOT boundary at the eave."""
    return eave + (ridge-eave)*min(poly.boundary.distance(shapely.Point(*xy))/4.0, 1.0)


def _culture_roof_triangles(poly, eave, ridge):
    """Tessellated pitched roof within the concave footprint; no detached eaves."""
    boundary = shapely.segmentize(poly.boundary, 3.0)
    points = list(boundary.coords)
    triangles = []
    x0, y0, x1, y1 = poly.bounds
    for x in np.arange(x0+1.5, x1, 3.0):
        for y in np.arange(y0+1.5, y1, 3.0):
            if poly.contains(shapely.Point(x, y)):
                points.append((x, y))
    for triangle in shapely.delaunay_triangles(MultiPoint(points)).geoms:
        clipped = triangle.intersection(poly)
        for piece in getattr(clipped, "geoms", [clipped]):
            if piece.geom_type != "Polygon" or piece.area < 1e-8:
                continue
            for tri in shapely.constrained_delaunay_triangles(piece).geoms:
                xy = np.asarray(tri.exterior.coords, float)[:3]
                a,b=xy[1]-xy[0],xy[2]-xy[0]
                signed=a[0]*b[1]-a[1]*b[0]
                if abs(signed)<1e-9:
                    continue
                if signed<0:
                    xy=xy[::-1]
                heights=[_culture_roof_height(poly,p,eave,ridge) for p in xy]
                triangles.append(np.column_stack((xy,heights)))
    return triangles


def _culture_roof_sample(triangles, xy):
    """Interpolate the emitted triangles, not the analytical profile between vertices."""
    for tri in triangles:
        if Polygon(tri[:,:2]).buffer(1e-7).covers(shapely.Point(*xy)):
            coeff=np.linalg.solve(np.column_stack((tri[:,:2],np.ones(3))),tri[:,2])
            return float(np.r_[xy,1.] @ coeff)
    return None


def _culture_dormer_placement(poly, triangles, front, axis, out, width, u, ridge):
    """WORKING_VALUE: place the front lower on the photographed roof slope."""
    center = front + axis*u - out*(width*.12)
    outline = Polygon([center + axis*a + out*n
                       for a, n in [(-.8,-.65),(.8,-.65),(.8,.65),(-.8,.65)]])
    if not poly.covers(outline):
        return None
    # Base sampled at the front, rather than under the centre on the rising slope.
    roof_base = _culture_roof_sample(triangles, center+out*.55)
    if roof_base is None:
        return None
    scale = min(1.0, (ridge - roof_base + .15 - .08) / 1.20)
    if scale < .35:
        return None
    return center, roof_base, scale


def _dormer(acc, layer, center, axis, out, eave, rise, window_material="glass", roof_base=None, scale=1.0):
    """Modest white dormer with a red gable, standing on the roof plane."""
    z0 = eave + rise * .25 if roof_base is None else roof_base-.15
    # Half axes in E,N,Z. The roof plane rises inward; this box partly intersects it.
    acc.box(layer, "plaster_white", _pt(center, z0+.40*scale), np.r_[axis*.57, 0],
            np.r_[out*.55, 0], [0, 0, .50*scale], skip=(0, 1))
    _face(acc, layer, window_material, center, axis, out, .64, z0+.20*scale, z0+.88*scale, .556)
    # WORKING_VALUE: white glazing bars, sharing the plaster material; Low retains the vertical bar.
    _face(acc, layer, "plaster_white", center, axis, out, .045, z0+.20*scale, z0+.88*scale, .565)
    if layer != "buildings_low":
        _face(acc, layer, "plaster_white", center, axis, out, .64, z0+.52*scale, z0+.56*scale, .566)
    # An overhanging red front makes the gable visible from the courtyard.
    front, back = center+out*.63, center-out*.55
    a, b, c, d = front-axis*.65, front+axis*.65, back+axis*.65, back-axis*.65
    peak0, peak1 = front, back
    # Roof is above the white box; normals checked independently of axis sign.
    za, zp = z0+.90*scale, z0+1.20*scale
    faces = [[_pt(a,za), _pt(d,za), _pt(peak1,zp), _pt(peak0,zp)],
             [_pt(c,za), _pt(b,za), _pt(peak0,zp), _pt(peak1,zp)]]
    if axis[0]*out[1] - axis[1]*out[0] < 0:
        faces = [f[::-1] for f in faces]
    for face in faces:
        acc.quad(layer, "roof_tiles_red", *face)
    gable = np.asarray([_pt(a,za), _pt(b,za), _pt(peak0,zp)], float)
    if np.dot(np.cross(gable[1]-gable[0], gable[2]-gable[0])[:2], out) < 0:
        gable = gable[::-1]
    acc.add(layer, "roof_tiles_red", gable, [[0,1,2]])


def build(buf, region, blds, zsmooth, report):
    result = {"id": ASSET_ID, "status": "skipped", "sources": list(IDS)}
    if region != REGION:  # ADR 0227: other regions get no QA entry (no diff in their streetscape_qa.json)
        return result
    report[ASSET_ID] = result
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
    facades = {}
    plans = {}
    entrances = {}
    for bid in IDS:
        target = np.array([760943.5-761611, 612382.3-612607]) if bid == OFFICE else frames[OFFICE][0]
        facades[bid] = _facade(selected[bid]["poly"], target, frames[bid][1])
        if facades[bid] is None:
            result["reason"] = "no suitable source footprint facade"
            return result
        poly=selected[bid]["poly"]; c,axis,*_ = frames[bid]
        omit=facades[bid][1] if bid == CULTURE else None
        # Both long exterior sides receive windows; a short end facing the park is detailed too.
        plan = _window_plan(poly,target,axis,9 if bid==OFFICE else 6,omit=omit)
        # ESTIMATED positions: use two existing axes on the courtyard-facing wall.
        if bid == OFFICE:
            entrances[bid] = [plan[i] for i in (2, 7)] if len(plan) >= 8 else []
        plan += _window_plan(poly,2*c-target,axis,9 if bid==OFFICE else 6)
        park=np.array([760943.5-761611, 612382.3-612607])
        plan += _window_plan(poly,park,axis,2,parallel=False)
        plans[bid]=plan
    for bid in IDS:
        b = selected[bid]
        poly = b["poly"]
        ring = np.asarray(poly.exterior.coords, float)
        center, axis, normal, length, width = frames[bid]
        eave_h, top_h = _heights(b["props"])
        eave, top = z+eave_h, z+top_h
        culture_roof = _culture_roof_triangles(poly, eave, top) if bid == CULTURE else None
        # Unlike the roof's bounding rectangle, each facade is an actual BDOT exterior edge.
        facade_len, front, face_axis, out = facades[bid]
        for layer in LAYERS:
            low = layer == "buildings_low"
            for a, c in zip(ring[:-1], ring[1:]):
                if not low:
                    acc.quad(layer, "plinth_dark", _pt(a,z-.15), _pt(c,z-.15), _pt(c,z+.55), _pt(a,z+.55))
                if bid == CULTURE:
                    _culture_wall(acc,layer,a,c,z,eave,front,facade_len,low=low)
                else:
                    base = z-.15 if low else z+.55
                    acc.quad(layer, "plaster_white", _pt(a,base), _pt(c,base), _pt(c,eave), _pt(a,eave))
            if bid == CULTURE:
                for triangle in culture_roof:
                    acc.add(layer,"roof_tiles_red",triangle,[[0,1,2]])
            else:
                _hip_roof(acc, layer, poly, center, axis, normal, length, width, eave, top)
            # Each axis is projected to its own BDOT wall, including split wall runs.
            for p,window_axis,window_out in plans[bid]:
                for z0 in (z+1.0, z+4.55):
                    if bid == OFFICE and z0 == z+1.0 and any(np.linalg.norm(p-q[0]) < .1 for q in entrances[bid]):
                        continue
                    if low:
                        _face(acc, layer, "plinth_dark", p, window_axis, window_out, 1.16, z0+.15, z0+2.32, .035)
                    else:
                        _face(acc, layer, "plaster_cream", p, window_axis, window_out, 1.55, z0, z0+2.5, .035)
                        _face(acc, layer, "glass", p, window_axis, window_out, 1.16, z0+.15, z0+2.32, .055)
                        # Existing white plaster material forms simple white window mullions.
                        _face(acc, layer, "plaster_white", p, window_axis, window_out, .065, z0+.15, z0+2.32, .065)
                        _face(acc, layer, "plaster_white", p, window_axis, window_out, 1.16, z0+1.58, z0+1.64, .065)
            if bid == OFFICE:
                # ESTIMATED doors and three tile steps; Low reuses existing materials.
                for p, tangent, outward in entrances[bid]:
                    _face(acc, layer, "plinth_dark", p, tangent, outward, 1.35, z+.55, z+3.15, .045)
                    for step in range(3):
                        depth = .45*(3-step)
                        center_step = p+outward*(depth/2+.04)
                        height = .55*(step+1)/3
                        acc.box(layer, "plinth_dark" if low else "roof_tiles_red", _pt(center_step,z+height/2),
                                np.r_[tangent*1.2,0], np.r_[outward*depth/2,0], [0,0,height/2], skip=(0,))
            n_dormer = (4 if bid == OFFICE else 3) if low else (8 if bid == OFFICE else 5)
            for j in range(n_dormer):
                u = (j-(n_dormer-1)/2)*min(3.7, (facade_len-3)/max(1,n_dormer-1))
                if bid == CULTURE:
                    placement = _culture_dormer_placement(poly, culture_roof, front, face_axis, out, width, u, top)
                    if placement is not None:
                        dormer_center, roof_base, scale = placement
                        _dormer(acc, layer, dormer_center, face_axis, out, eave, top-eave,
                                window_material="plinth_dark" if low else "glass", roof_base=roof_base, scale=scale)
                    continue
                dormer_center = front+face_axis*u-out*(width*.19)
                outline = Polygon([dormer_center + face_axis*a + out*n
                                   for a, n in [(-.8,-.65),(.8,-.65),(.8,.65),(-.8,.65)]])
                if poly.covers(outline):
                    _dormer(acc, layer, dormer_center, face_axis, out, eave, top-eave,
                            window_material="plinth_dark" if low else "glass")
        if bid == CULTURE:
            # Four full-height cream columns and two storeys of recessed loggia; no signs or emblems.
            for layer in LAYERS:
                low = layer == "buildings_low"
                half_portico = min(4.7, (facade_len-1.0)/2)
                # Back wall is recessed 1.2 m behind the opening; both floor openings remain dark.
                back = front-out*1.2
                _face(acc,layer,"plinth_dark",back,face_axis,out,2*half_portico,z+.55,z+7.7,0.)
                for u in np.linspace(-half_portico+.3, half_portico-.3, 4):
                    p = front+face_axis*u+out*.12
                    acc.box(layer, "plaster_white" if low else "plaster_cream", _pt(p,z+4.2), np.r_[face_axis*.25,0], np.r_[out*.25,0], [0,0,4.2], skip=(0,))
                p = front-out*.5
                acc.box(layer, "plaster_white", _pt(p,z+4.0), np.r_[face_axis*half_portico,0], np.r_[out*.70,0], [0,0,.12], skip=(0,))
                # Gallery railing: slim bars and continuous upper rail, using the existing dark material.
                rail=front-out*.12
                acc.box(layer,"plinth_dark",_pt(rail,z+5.0),np.r_[face_axis*half_portico,0],np.r_[out*.025,0],[0,0,.025],skip=(0,))
                if not low:
                    for u in np.linspace(-half_portico+.15,half_portico-.15,13):
                        acc.box(layer,"plinth_dark",_pt(rail+face_axis*u,z+4.5),np.r_[face_axis*.02,0],np.r_[out*.025,0],[0,0,.5],skip=(0,))
                acc.box(layer, "plinth_dark", _pt(p+out*.9,z+.24), np.r_[face_axis*min(3.,half_portico),0], np.r_[out*.9,0], [0,0,.24], skip=(0,))
    acc.flush(buf, ASSET_ID)
    result.update(status="applied", confidence={"footprints": "SOURCED BDOT10k", "heights": "SOURCED GUGiK",
                                                 "facades_and_details": "ESTIMATED / WORKING_VALUE"},
                  floors=2, roof="red hipped with gabled dormers", column_count=4,
                  window_axes={k:len(v) for k,v in plans.items()}, portico_recess_m=1.2)
    return result
