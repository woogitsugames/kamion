"""Authored small-park objects for Rynek, Knyszyn (ADR 0227).

Use ``build(buf, region, origin, overrides, zsmooth, report)`` after the paved
area plan is known. All anchors are EPSG:2180.  The obelisk point corresponds
to OSM node 3047587676 (SOURCED point; identification with the photograph is
ESTIMATED). The king, flagpole, benches and lamps are ESTIMATED from owner
photographs and GUGiK orthophoto. Sizes and individual details are WORKING_VALUE.

These are deliberately simple low-cost meshes, not scans or derived textures.
The statue is a PROXY requiring visual review; the eagle on the obelisk and the
wording on both plaques are omitted. Lamps do not yet emit dynamic light.
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


def _king(acc, layer, at, z):
    # Stylised proxy, not a scan or a reconstruction of the artwork. The front
    # faces the separate sundial block (-N). Dimensions are WORKING_VALUE.
    _box(acc,layer,"plinth_grey",at,z,z+.18,1.05,.9)
    _box(acc,layer,"plinth_grey",at,z+.18,z+1.05,.86,.73)
    body = np.asarray(at, float)
    bronze = "steel_painted"
    # The open silhouette is intentionally human: wide tapered cloak, a
    # narrower neck and head, and arms visible at either side of the torso.
    _frustum(acc,layer,bronze,body,z+1.05,z+2.64,1.26,.90)
    _box(acc,layer,bronze,body,z+2.54,z+2.77,.45,.25)       # shoulders
    for side in (-1, 1):
        c = [body[0]+side*.46, body[1]-.22, z+2.15]
        acc.box(layer,bronze,c,[.10,0,0],[0,.12,0],[-side*.055,0,.42],skip=(0,))
    _box(acc,layer,bronze,body,z+2.72,z+2.84,.10,.10)     # neck
    _box(acc,layer,bronze,body,z+2.82,z+3.18,.19,.17)     # head
    _box(acc,layer,bronze,body,z+3.16,z+3.25,.22,.19)     # crown band
    # The narrow raised points make the crown readable even on the cheap LOD.
    # Keep the top at the earlier proxy's height; no emblem or lettering.
    for x in (-.15, 0., .15):
        _box(acc,layer,bronze,body+[x,0.],z+3.25,z+3.39,.04,.16)
    if layer == "buildings":
        # Small projecting beard and hands add depth in the close High view.
        _box(acc,layer,bronze,body+[0.,-.18],z+2.78,z+3.02,.12,.045)
        for side in (-1, 1):
            _box(acc,layer,bronze,body+[side*.51,-.23],z+1.72,z+1.88,.105,.13)
    # Separate sundial/plaque block on paving in front of figure, blank.
    p=np.asarray(at)+[0.,-2.0]
    _box(acc,layer,"plinth_grey",p,z,z+.75,.65,.40)
    _box(acc,layer,"steel_painted",p+[0.,-.406],z+.22,z+.55,.45,.012)


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
            "king_silhouette":"PROXY_NOT_APPROVED","eagle":"omitted","lighting":"no dynamic emission",
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

    for xy, fn in ((OBELISK,_obelisk),(KING,_king),(FLAG,_flagpole)):
        p=np.asarray(xy,float)-origin; z=ground(p)
        if not math.isfinite(z):
            result["refused"].append({"at":list(xy),"reason":"non-finite terrain"}); continue
        for layer in LAYERS: fn(acc,layer,p,z)
        if fn is _obelisk:
            # Main stone shaft only; the low decorative steps remain traversable.
            _box(acc,"collision","collision_building",p,z-.1,z+3.2,.73,.73)
        elif fn is _king:
            _box(acc,"collision","collision_building",p,z-.1,z+3.39,1.05,.90)
            _box(acc,"collision","collision_building",p+[0.,-2.],z-.1,z+.75,.65,.40)
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
    acc.flush(buf,ASSET_ID)
    result.update(status="applied" if acc.d else "skipped", confidence={"obelisk_point":"SOURCED OSM; identity ESTIMATED",
                  "king_and_pole":"ESTIMATED", "dimensions":"WORKING_VALUE"})
    return result
