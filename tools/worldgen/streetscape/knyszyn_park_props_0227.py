"""Authored small-park objects for Rynek, Knyszyn (ADR 0227).

Use ``build(buf, region, origin, overrides, zsmooth, report)`` after the paved
area plan is known. All anchors are EPSG:2180.  The obelisk point corresponds
to OSM node 3047587676 (SOURCED point; identification with the photograph is
ESTIMATED). The king, flagpole, benches and lamps are ESTIMATED from owner
photographs and GUGiK orthophoto. Sizes and individual details are WORKING_VALUE.

These are deliberately simple low-cost meshes, not scans or derived textures.
ADR 0320: the king is a lathed figure (proportions from owner photos 1 / 8) in
patinated bronze on a granite block instead of the six-sided grey proxy.
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
from . import monument_kit as MK

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
    v2=v.copy(); v2[:,:2]=np.column_stack((-(v[:,1]-c[1]),v[:,0]-c[0]))+c
    acc.add(layer,"steel_painted",v2,[[0,1,2],[2,1,3],[2,1,0],[3,1,2]])


# ADR 0320: figure sizes read off owner photos 1 and 8 against the people / the plinth (no survey): figure about
# 3.2 m on a 1.05 m plinth, 1.25 m wide and 1.05 m deep at the hem, a broad cloak hanging from the shoulders, small
# head with a crown. WORKING_VALUE. (z above the plinth top, half width, half depth, 0, forward offset, section power)
KING_PLINTH_H = 1.05
KING_RINGS = ((0.00, .625, .525, 0., .00, 3.2), (0.06, .630, .530, 0., .00, 3.2), (0.60, .605, .500, 0., .00, 3.0),
              (1.20, .570, .455, 0., -.01, 2.8), (1.80, .530, .400, 0., -.02, 2.6), (2.20, .500, .350, 0., -.03, 2.5),
              (2.42, .500, .335, 0., -.03, 2.4), (2.52, .470, .300, 0., -.03, 2.3), (2.62, .380, .255, 0., -.03, 2.2),
              (2.70, .240, .205, 0., -.02, 2.0), (2.76, .150, .150, 0., -.01, 2.0), (2.82, .135, .145, 0., .00, 2.0),
              (2.90, .150, .170, 0., .01, 2.0), (3.00, .158, .172, 0., .01, 2.0), (3.07, .150, .160, 0., .00, 2.0),
              (3.07, .172, .180, 0., .00, 2.0), (3.13, .178, .186, 0., .00, 2.0))
KING_CROWN_M = 0.13
KING_H = KING_PLINTH_H + 0.04 + KING_RINGS[-1][0] + KING_CROWN_M          # top of the crown points (LOD0)


def _king(acc, layer, at, z):
    # Stylised figure, not a scan or a reconstruction of the artwork: silhouette and proportions only (owner photos
    # 1 / 8, ADR 0320). The front faces the separate sundial block towards the town hall (ESTIMATED).
    low = layer == "buildings_low"
    stone = "monument_granite"
    _box(acc,layer,stone,at,z,z+.18,1.05,.9,KING_TANGENT)
    _box(acc,layer,stone,at,z+.18,z+KING_PLINTH_H,.86,.73,KING_TANGENT)
    if not low:      # chamfered top course of the block: a 4 cm set-back line under the figure
        _box(acc,layer,stone,at,z+KING_PLINTH_H,z+KING_PLINTH_H+.04,.80,.67,KING_TANGENT)
    body = np.asarray(at, float)
    def pos(x, forward): return body + KING_TANGENT*x + KING_FORWARD*forward
    bronze = "monument_bronze"
    base = [body[0], body[1], z + KING_PLINTH_H + (0. if low else .04)]
    rings = MK.thin(KING_RINGS) if low else KING_RINGS
    MK.lathe(acc, layer, bronze, base, KING_FORWARD, rings, sides=8 if low else 16)
    top = base[2] + KING_RINGS[-1][0]
    # crown: points on the band (flat, both sides) and the low cap inside it
    npts = 6 if low else 10
    tip = top + KING_CROWN_M
    for i in range(npts):
        a = 2*math.pi*(i+.5)/npts
        c, s = math.cos(a), math.sin(a)
        p0 = pos(.176*math.cos(a-.17), .184*math.sin(a-.17)); p1 = pos(.176*math.cos(a+.17), .184*math.sin(a+.17))
        p2 = pos(.19*c, .198*s)
        tri = [_p(p0, top-.01), _p(p1, top-.01), _p(p2, tip)]
        acc.add(layer, bronze, tri, [[0,1,2],[2,1,0]])
    if not low:
        MK.sphere(acc, layer, bronze, [base[0], base[1], top-.005], .15, sides=8, stacks=4, squash=.45)
        # fur collar roll and the two edges of the open cloak down the front (photo 8)
        f3 = np.r_[KING_FORWARD, 0.]; t3 = np.r_[KING_TANGENT, 0.]
        o3 = np.asarray(base, float)
        def surf(x, zz, lift=.012):
            # point on the front of the body at lateral x and height zz (linear between rings)
            zs = [r[0] for r in KING_RINGS]
            rx = float(np.interp(zz, zs, [r[1] for r in KING_RINGS])); ry = float(np.interp(zz, zs, [r[2] for r in KING_RINGS]))
            off = float(np.interp(zz, zs, [r[4] for r in KING_RINGS])); pw = float(np.interp(zz, zs, [r[5] for r in KING_RINGS]))
            y = ry * max(0., 1. - abs(x/rx)**pw)**(1./pw)
            return o3 + t3*x + f3*(y+off+lift) + np.array([0., 0., zz])
        for side in (-1, 1):
            MK.limb(acc, layer, bronze, [surf(side*.10, zz) for zz in (.08, .7, 1.4, 2.0, 2.38)],
                    [.035, .034, .032, .03, .028], sides=5)
            # chain of office: from the shoulders to the chest (no emblem)
            MK.limb(acc, layer, bronze, [surf(side*.36, 2.40, .02), surf(side*.20, 2.12, .02), surf(0., 1.96, .02)],
                    [.022, .022, .022], sides=4)
        MK.sphere(acc, layer, bronze, surf(0., 1.90, .03), .06, sides=6, stacks=3, squash=.6)
    # Separate sundial/plaque block on paving in front of figure, blank.
    p=body+KING_FORWARD*KING_BLOCK_DISTANCE_M
    _box(acc,layer,"monument_granite",p,z,z+.75,.65,.40,KING_TANGENT)
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
    r, rows, h = .065, 28, 7.0
    seg = 8 if layer == "buildings_low" else 12
    sector_width = seg // 4
    c=np.asarray(at,float)
    for j in range(rows):
        z0,z1=z+h*j/rows,z+h*(j+1)/rows
        for i in range(seg):
            a=2*math.pi*i/seg; b=2*math.pi*(i+1)/seg
            p=c+r*np.array([math.cos(a),math.sin(a)])
            q=c+r*np.array([math.cos(b),math.sin(b)])
            mat = "paint_white_reflective" if (j+i//sector_width)%2 == 0 else "brick_red"
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
    if region != REGION:  # ADR 0227: other regions get no QA entry (no diff in their streetscape_qa.json)
        return result
    report[ASSET_ID] = result
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
            _box(acc,"collision","collision_building",p,z-.1,z+KING_H,1.05,.90,KING_TANGENT)
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
                     "plinth_grey": "plaster_grey", "steel_painted": "plinth_dark",
                     "monument_granite": "plaster_grey", "monument_bronze": "plinth_dark"}.items():
        parts = acc.d.pop(("buildings_low", old), [])
        if parts:
            acc.d.setdefault(("buildings_low", new), []).extend(parts)
    acc.flush(buf,ASSET_ID)
    result.update(status="applied" if acc.d else "skipped", confidence={"obelisk_point":"SOURCED OSM; identity ESTIMATED",
                  "king_and_pole":"ESTIMATED", "dimensions":"WORKING_VALUE"})
    return result
