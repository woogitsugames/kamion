"""Authored small-park objects for Rynek, Knyszyn (ADR 0227).

Use ``build(buf, region, origin, overrides, zsmooth, report)`` after the paved
area plan is known. All anchors are EPSG:2180.  The obelisk point corresponds
to OSM node 3047587676 (SOURCED point; identification with the photograph is
ESTIMATED). The king, flagpole, benches and lamps are ESTIMATED from owner
photographs and GUGiK orthophoto. Sizes and individual details are WORKING_VALUE.

These are deliberately simple low-cost meshes, not scans or derived textures.
The statue and the bird on the obelisk are PROXY shapes requiring visual review;
the wording on both plaques is omitted. Lamps do not yet emit dynamic light.
Collision uses simple low-detail boxes, separate from the visual LOD layers.
Do not claim photo or device acceptance from the tests.
"""
from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

from . import buildings_mesh as BM

REGION = "knyszyn"
ASSET_ID = "knyszyn_park_props_0227"
LAYERS = ("buildings", "buildings_low")
OBELISK = (760936.66, 612395.45)   # SOURCED OSM node/3047587676, identity ESTIMATED
KING = (760959.0, 612427.0)         # ESTIMATED from GUGiK orthophoto
FLAG = (760963.0, 612424.0)         # ESTIMATED, photo 8 / ortho
# ESTIMATED from the 2025 orthophoto and photographs 1 and 8; the axis points
# from the king toward the town-hall parking, not toward the fountain.
KING_FORWARD = np.array([.58, .815], dtype=float)
KING_FORWARD /= np.linalg.norm(KING_FORWARD)
KING_TANGENT = np.array([KING_FORWARD[1], -KING_FORWARD[0]])
KING_BLOCK_DISTANCE_M = 2.0         # WORKING_VALUE, photo 8
KING_PLAZA_EPSG2180 = ((760955.5, 612433.2), (760964.8, 612428.25),
                       (760959.0, 612417.65), (760951.75, 612423.8))
# Candidate positions near, but outside, paths and central paving. Each is checked
# against the authored path polygons at build time and is skipped if obstructing.
BENCHES = ((760925., 612355.), (760930., 612365.), (760910., 612375.),
           (760945., 612375.), (760970., 612385.), (760970., 612395.),
           (760915., 612400.), (760915., 612410.))
LAMPS = ((760922.5, 612350.), (760895., 612372.5), (760957.5, 612382.5),
         (760982.5, 612392.5), (760940., 612422.5))


def _p(xy, z):
    return [float(xy[0]), float(xy[1]), float(z)]


def _box(acc, layer, mat, xy, z0, z1, hx, hy, axis=(1., 0.)):
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    n = np.array([-a[1], a[0]])
    acc.box(layer, mat, _p(xy, (z0+z1)/2), np.r_[a*hx, 0.], np.r_[n*hy, 0.],
            [0., 0., (z1-z0)/2], skip=(0,))


def _frustum(acc, layer, mat, center, z0, z1, bottom, top):
    """Tapered square stone, closed at top; dimensions are full widths."""
    c = np.asarray(center, float)
    corners = np.array([[-1,-1], [1,-1], [1,1], [-1,1]], float)
    lo = [c + q * bottom / 2 for q in corners]
    hi = [c + q * top / 2 for q in corners]
    for i in range(4):
        j = (i+1) % 4
        acc.quad(layer, mat, _p(lo[i],z0), _p(lo[j],z0), _p(hi[j],z1), _p(hi[i],z1))
    acc.quad(layer, mat, *[_p(p,z1) for p in hi])


def _obelisk(acc, layer, at, z):
    # Three low dark steps, light tapered monument and a blank dark plaque.
    for inset, z0, z1 in ((0.,0.,.15),(.24,.15,.30),(.48,.30,.45)):
        _box(acc,layer,"plinth_grey",at,z+z0,z+z1,2.1-inset,1.65-inset)
    _frustum(acc,layer,"plaster_light",at,z+.45,z+3.2,1.45,.74)
    # South-west-facing unlettered plaque; not a political symbol or text.
    xy = np.asarray(at) + np.array([-.08,-.68])
    _box(acc,layer,"steel_painted",xy,z+1.35,z+2.1,.25,.035)
    # WORKING_VALUE: a tiny non-heraldic bird silhouette, visible on both sides.
    c=np.asarray(at,float)
    v=np.asarray([_p(c+[-.32,0.],z+3.35), _p(c+[0.,0.],z+3.26),
                  _p(c+[0.,0.],z+3.48), _p(c+[.32,0.],z+3.35)],float)
    acc.add(layer,"steel_painted",v,[[0,1,2],[2,1,3],[2,1,0],[3,1,2]])


def _king(acc, layer, at, z):
    # Stylised proxy, not a scan or a reconstruction of the artwork. The front
    # faces the separate sundial block towards the town hall (ESTIMATED).
    _box(acc,layer,"plinth_grey",at,z,z+.18,1.05,.9,KING_TANGENT)
    _box(acc,layer,"plinth_grey",at,z+.18,z+1.05,.86,.73,KING_TANGENT)
    body = np.asarray(at, float)
    def pos(x, forward): return body + KING_TANGENT*x + KING_FORWARD*forward
    bronze = "steel_painted"
    # The open silhouette is intentionally human: wide tapered cloak, a
    # narrower neck and head, and arms visible at either side of the torso.
    _frustum(acc,layer,bronze,body,z+1.05,z+2.64,1.00,.58)
    _box(acc,layer,bronze,body,z+2.49,z+2.73,.34,.21,KING_TANGENT)  # shoulders
    for side in (-1, 1):
        c = pos(side*.36,.22)
        acc.box(layer,bronze,_p(c,z+2.15),np.r_[KING_TANGENT*.10,0],
                np.r_[KING_FORWARD*.09,0],np.r_[-side*KING_TANGENT*.055,.42],skip=(0,))
    _box(acc,layer,bronze,body,z+2.72,z+2.84,.10,.10,KING_TANGENT)  # neck
    _box(acc,layer,bronze,body,z+2.82,z+3.18,.19,.17,KING_TANGENT)  # head
    _box(acc,layer,bronze,body,z+3.16,z+3.25,.22,.19,KING_TANGENT)  # crown band
    # The narrow raised points make the crown readable even on the cheap LOD.
    # Keep the top at the earlier proxy's height; no emblem or lettering.
    for x in (-.15, 0., .15):
        _box(acc,layer,bronze,pos(x,0),z+3.25,z+3.39,.04,.16,KING_TANGENT)
    if layer == "buildings":
        # Small projecting beard and hands add depth in the close High view.
        _box(acc,layer,bronze,pos(0,.18),z+2.75,z+3.02,.12,.045,KING_TANGENT)
        for side in (-1, 1):
            _box(acc,layer,bronze,pos(side*.39,.23),z+1.72,z+1.88,.09,.10,KING_TANGENT)
    # Separate sundial/plaque block on paving in front of figure, blank.
    p=body+KING_FORWARD*KING_BLOCK_DISTANCE_M
    _box(acc,layer,"plinth_grey",p,z,z+.75,.65,.40,KING_TANGENT)
    _box(acc,layer,"steel_painted",p+KING_FORWARD*.406,z+.22,z+.55,.45,.012,KING_TANGENT)
    # WORKING_VALUE: blank octagonal sundial and small gnomon, not text or an emblem.
    vertices=[_p(p,z+.758)]+[_p(p+np.array([math.cos(a),math.sin(a)])*.29,z+.758)
                             for a in (2*math.pi*i/8 for i in range(8))]
    acc.add(layer,"steel_painted",vertices,[[0,i+1,(i+1)%8+1] for i in range(8)])
    tri=np.asarray([_p(p-KING_FORWARD*.15,z+.762),_p(p+KING_FORWARD*.15,z+.762),
                    _p(p,z+.96)],float)
    acc.add(layer,"steel_painted",tri,[[0,1,2],[2,1,0]])


def _flagpole(acc, layer, at, z):
    # Alternating diagonal bands, geometry only. Height is WORKING_VALUE.
    r, seg, rows, h = .065, 12, 28, 7.0
    c=np.asarray(at,float)
    for j in range(rows):
        z0,z1=z+h*j/rows,z+h*(j+1)/rows
        for i in range(seg):
            a=2*math.pi*i/seg; b=2*math.pi*(i+1)/seg
            p=c+r*np.array([math.cos(a),math.sin(a)])
            q=c+r*np.array([math.cos(b),math.sin(b)])
            mat = "paint_white_reflective" if (j+i//3)%2 == 0 else "brick_red"
            acc.quad(layer,mat,_p(p,z0),_p(q,z0),_p(q,z1),_p(p,z1))


def _bench(acc, layer, at, z, tangent, toward):
    # Five brown wooden slats and dark legs, back and armrests; dimensions WORKING_VALUE.
    t=np.asarray(tangent,float); n=np.asarray(toward,float); c=np.asarray(at,float)
    for i in range(4):
        xy=c+n*(-.24+i*.15)
        _box(acc,layer,"bench_wood",xy,z+.42,z+.47,.91,.055,t)
    for i in range(3):
        xy=c-n*.28
        _box(acc,layer,"bench_wood",xy,z+.56+i*.14,z+.64+i*.14,.91,.04,t)
    for side in (-1,1):
        xy=c+t*(side*.72)
        _box(acc,layer,"steel_painted",xy,z,z+.9,.035,.30,t)


def _lamp(acc, layer, at, z):
    # Park pole in the photos: black shaft, pale cylindrical lantern and black cap.
    _box(acc,layer,"steel_painted",at,z,z+3.5,.045,.045)
    _box(acc,layer,"plaster_white",at,z+3.5,z+3.88,.17,.17)
    _box(acc,layer,"steel_painted",at,z+3.88,z+3.95,.22,.22)


def _paved(overrides, origin):
    rings = [Polygon(np.asarray(o["polygon_epsg2180"],float)-origin) for o in overrides
             if o.get("kind")=="paved_area" and "polygon_epsg2180" in o and
             (o.get("id", "").startswith("rynek-path-") or
              o.get("id", "").startswith("rynek-central") or
              o.get("id", "").startswith("rynek-king-plaza") or
              o.get("id", "").startswith("rynek-fountain"))]
    return shapely.union_all(rings) if rings else None


def _footprint(center, tangent, toward, half_length, half_depth):
    return Polygon([center+tangent*a+toward*b for a,b in
                    [(-half_length,-half_depth),(half_length,-half_depth),
                     (half_length,half_depth),(-half_length,half_depth)]])


def build(buf, region, origin, overrides, zsmooth, report):
    """Build props; candidate benches/lamps stay clear of authored path polygons.

    `zsmooth` samples height for arrays of local E,N positions.  If authored paths
    are absent, benches/lamps are skipped rather than placed at unverified sites.
    """
    result={"id":ASSET_ID,"status":"skipped","source_point":"OSM node/3047587676",
            "king_silhouette":"PROXY_NOT_APPROVED","eagle":"PROXY_NOT_APPROVED","lighting":"no dynamic emission",
            "benches":[],"lamps":[],"refused":[]}
    report[ASSET_ID]=result
    if region != REGION:
        return result
    origin=np.asarray(origin,float)
    if origin.shape != (2,) or not np.isfinite(origin).all():
        result["reason"]="invalid region origin"; return result
    paved=_paved(overrides,origin)
    tree_points = [Point(xy[:2]) for o in overrides if o.get("kind")=="tree_groups"
                   and o.get("id", "").startswith("rynek-park-") for xy in o.get("points_en",[])]
    acc=BM.Acc()

    def ground(p):
        return float(np.asarray(zsmooth(np.array([p[0]]),np.array([p[1]]))).ravel()[0])

    result["king_plaza"] = "authored_paved_area" if any(o.get("id") == "rynek-king-plaza-0227" for o in overrides) else "missing_override"
    for xy, fn in ((OBELISK,_obelisk),(KING,_king),(FLAG,_flagpole)):
        p=np.asarray(xy,float)-origin; z=ground(p)
        if not math.isfinite(z):
            result["refused"].append({"at":list(xy),"reason":"non-finite terrain"}); continue
        for layer in LAYERS: fn(acc,layer,p,z)
        if fn is _obelisk:
            # Main stone shaft only; the low decorative steps remain traversable.
            _box(acc,"collision","collision_building",p,z-.1,z+3.2,.73,.73)
        elif fn is _king:
            _box(acc,"collision","collision_building",p,z-.1,z+3.39,1.05,.90,KING_TANGENT)
            _box(acc,"collision","collision_building",p+KING_FORWARD*KING_BLOCK_DISTANCE_M,
                 z-.1,z+.75,.65,.40,KING_TANGENT)
        else:
            _box(acc,"collision","collision_steel",p,z-.1,z+7.,.065,.065)
    for kind, candidates in (("benches",BENCHES),("lamps",LAMPS)):
        for xy in candidates:
            p=np.asarray(xy,float)-origin
            if paved is None:
                result["refused"].append({"at":list(xy),"reason":"park path polygons missing"}); continue
            point=Point(p); d=float(point.distance(paved))
            if not 1.2 <= d <= 5.0:
                result["refused"].append({"at":list(xy),"reason":"not sufficiently clear of path", "distance_m":round(d,2)}); continue
            nearest=nearest_points(point,paved)[1]
            toward=np.array(nearest.coords[0])-p; toward/=np.linalg.norm(toward)
            tangent=np.array([-toward[1],toward[0]])
            footprint=_footprint(p,tangent,toward,.91 if kind=="benches" else .22,
                                 .34 if kind=="benches" else .22)
            if footprint.intersects(paved.buffer(.10)):
                result["refused"].append({"at":list(xy),"reason":"object overlaps path clearance"}); continue
            if any(point.distance(tree)<2.0 for tree in tree_points):
                result["refused"].append({"at":list(xy),"reason":"too close to authored tree"}); continue
            z=ground(p)
            if not math.isfinite(z):
                result["refused"].append({"at":list(xy),"reason":"non-finite terrain"}); continue
            for layer in LAYERS:
                if kind=="benches": _bench(acc,layer,p,z,tangent,toward)
                else: _lamp(acc,layer,p,z)
            if kind=="benches":
                _box(acc,"collision","collision_steel",p,z-.1,z+.9,.91,.30,tangent)
            else:
                _box(acc,"collision","collision_steel",p,z-.1,z+3.95,.08,.08)
            result[kind].append({"at_epsg2180":list(xy),"distance_to_path_m":round(d,2),"confidence":"ESTIMATED"})
    # Low reuses materials already present in this chunk; High keeps the authored palette.
    for old, new in {"bench_wood": "wood_planks", "paint_white_reflective": "plaster_light",
                     "plaster_white": "plaster_light",
                     "plinth_grey": "plaster_grey", "steel_painted": "plinth_dark"}.items():
        parts = acc.d.pop(("buildings_low", old), [])
        if parts:
            acc.d.setdefault(("buildings_low", new), []).extend(parts)
    acc.flush(buf,ASSET_ID)
    result.update(status="applied" if acc.d else "skipped", confidence={"obelisk_point":"SOURCED OSM; identity ESTIMATED",
                  "king_and_pole":"ESTIMATED", "dimensions":"WORKING_VALUE"})
    return result
