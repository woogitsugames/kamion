"""Two Knyszyn marketplace buildings, generated from their BDOT footprints.

Integrate ``hero_targets(region, fc)`` into BM.load's hero map, then call
``build(buf, region, blds, zsmooth, report)`` after generic building geometry.
The measured footprints stay available to BM.load for collision and keepouts.
BDOT footprints and the long building's GUGiK LoD heights are SOURCED. Matching
the pavilion and the shop building to the owner's photos is ESTIMATED. Pavilion
height, openings, facade colour divisions and roof form are WORKING_VALUE.
Neither owner images nor text, logos or brands are used as assets or textures.
"""
from __future__ import annotations

import math
import numpy as np
import shapely
from shapely.geometry import Polygon
from . import buildings_mesh as BM
from . import knyszyn_townhall_0227 as KT

REGION = 'knyszyn'
SHOP = 'bdot:2002917F-465A-5C99-E053-CC2BA8C01CFC'
PAVILION = 'bdot:de62e5a9-3c83-4023-9e77-03b8844df001'
IDS = (SHOP, PAVILION)
ASSET_ID = 'knyszyn_market_buildings_0227'
LAYERS = ('buildings', 'buildings_low')


def _heights(bid, props):
    if bid == PAVILION:
        return 2.8, 4.2  # WORKING_VALUE; no measured LoD1/LoD2 for this footprint.
    try:
        eave = float(props['lod2_eave_rel_m'])
        ridge = float(props['height_lod1_2024_m'])
    except (KeyError, ValueError, TypeError):
        return None
    if not (math.isfinite(eave) and math.isfinite(ridge) and 2 < eave < ridge < 12):
        return None
    return eave, ridge


def hero_targets(region, feature_collection):
    if region != REGION:
        return {}
    fs = [f for f in feature_collection.get('features', []) if f.get('id') in IDS]
    if len(fs) != 2 or {f.get('id') for f in fs} != set(IDS):
        return {}
    if any(_heights(f['id'], f.get('properties', {})) is None for f in fs):
        return {}
    return {bid: ASSET_ID for bid in IDS}


def _pt(xy, z):
    return [float(xy[0]), float(xy[1]), float(z)]


def _hip(acc, layer, poly, center, axis, normal, length, width, eave, ridge):
    """Four roof planes clipped to the BDOT footprint; upward-facing triangles."""
    a, b = center-axis*length/2, center+axis*length/2
    al, ar, bl, br = a-normal*width/2, a+normal*width/2, b-normal*width/2, b+normal*width/2
    inset = min(width*.5, length*.3)
    ra, rb = a+axis*inset, b-axis*inset
    faces = [[_pt(al,eave),_pt(bl,eave),_pt(rb,ridge),_pt(ra,ridge)],
             [_pt(br,eave),_pt(ar,eave),_pt(ra,ridge),_pt(rb,ridge)],
             [_pt(ar,eave),_pt(al,eave),_pt(ra,ridge)],
             [_pt(bl,eave),_pt(br,eave),_pt(rb,ridge)]]
    for face in faces:
        xyz = np.asarray(face,float)
        coeff = np.linalg.solve(np.c_[xyz[:3,:2],np.ones(3)],xyz[:3,2])
        clipped = shapely.intersection(Polygon(xyz[:,:2]),poly)
        for piece in getattr(clipped,'geoms',[clipped]):
            if piece.geom_type != 'Polygon' or piece.is_empty or piece.area < 1e-8:
                continue
            for tri in shapely.constrained_delaunay_triangles(piece).geoms:
                xy = np.asarray(tri.exterior.coords,float)[:3]
                d1, d2 = xy[1]-xy[0], xy[2]-xy[0]
                cross = d1[0]*d2[1]-d1[1]*d2[0]
                if abs(cross) < 1e-9:
                    continue
                if cross < 0:
                    xy = xy[::-1]
                zz = np.c_[xy,np.ones(3)] @ coeff
                acc.add(layer,'roof_metal_graphite',np.column_stack((xy,zz)),[[0,1,2]])


def _roof_at(p, center, axis, normal, length, width, eave, ridge):
    u, v = float((p-center) @ axis), float((p-center) @ normal)
    inset = min(width*.5, length*.3)
    fraction = max(0., min(1., (length/2-abs(u))/inset,
                              (width/2-abs(v))/(width/2)))
    return eave + (ridge-eave)*fraction


def _roof_boundary_fill(acc, layer, ring, center, axis, normal, length, width, eave, ridge):
    """Close gaps where a concave BDOT boundary intersects sloping roof planes."""
    for a, b in zip(ring[:-1], ring[1:]):
        steps = max(1, int(math.ceil(float(np.linalg.norm(b-a)))))
        for j in range(steps):
            p = a+(b-a)*(j/steps); q = a+(b-a)*((j+1)/steps)
            hp = _roof_at(p,center,axis,normal,length,width,eave,ridge)
            hq = _roof_at(q,center,axis,normal,length,width,eave,ridge)
            if max(hp,hq)-eave <= 1e-6:
                continue
            # The footprint has CCW winding, so this face points outwards.
            verts=[_pt(p,eave),_pt(q,eave),_pt(q,hq),_pt(p,hp)]
            tris=[]
            if hq-eave > 1e-6: tris.append([0,1,2])
            if hp-eave > 1e-6: tris.append([0,2,3])
            acc.add(layer,'plaster_yellow',verts,tris)


def _front_edges(poly, target, axis):
    return KT._edges(poly, target, axis)


def build(buf, region, blds, zsmooth, report):
    result = {'id': ASSET_ID, 'status': 'skipped', 'sources': list(IDS)}
    report[ASSET_ID] = result
    if region != REGION:
        return result
    selected = {b['id']:b for b in blds if b['id'] in IDS}
    if set(selected) != set(IDS) or any(b['ovr'].get('hero_asset') != ASSET_ID for b in selected.values()):
        result['reason'] = 'both hero targets required; generic buildings remain'
        return result
    prepared = {}
    for bid,b in selected.items():
        ring = np.asarray(b['poly'].exterior.coords,float)
        z = float(np.median(np.asarray(zsmooth(ring[:,0],ring[:,1]),float)))
        h = _heights(bid,b['props'])
        if h is None or not math.isfinite(z):
            result['reason'] = 'invalid source height'; return result
        prepared[bid] = (ring,z,h,KT._frame(b['poly']))
    acc = BM.Acc()
    for bid,b in selected.items():
        poly=b['poly']; ring,z,(eh,rh),(center,axis,normal,length,width)=prepared[bid]
        eave,ridge=z+eh,z+rh
        for layer in LAYERS:
            low=layer=='buildings_low'
            # Wall divisions and the yellow pavilion are ESTIMATED from the photos.
            for a,c in zip(ring[:-1],ring[1:]):
                if bid == PAVILION:
                    wall='plaster_yellow'
                else:
                    # Generic red storefront toward the south; no emblems or lettering.
                    wall='brick_red' if (a[1]+c[1])/2 < center[1] else 'plaster_peach'
                acc.quad(layer,wall,_pt(a,z-.15),_pt(c,z-.15),_pt(c,eave),_pt(a,eave))
            _hip(acc,layer,poly,center,axis,normal,length,width,eave,ridge)
            if bid == PAVILION:
                _roof_boundary_fill(acc,layer,ring,center,axis,normal,length,width,eave,ridge)
            # Openings face the sheltered market; positions and dimensions WORKING_VALUE.
            target = center + np.array([25.,0.])
            edges = _front_edges(poly,target,axis)
            for a,c,tangent,out,edge_len in edges:
                count=max(1,int((edge_len-1.)//4.5))
                for t in np.linspace(.5/count,1-.5/count,count):
                    p=a+(c-a)*t
                    KT._face(acc,layer,'plinth_dark' if low else 'glass',p,tangent,out,
                             1.35 if bid == SHOP else 1.6,z+.9,min(z+2.45,eave-.2),.04)
    acc.flush(buf,ASSET_ID)
    result.update(status='applied', confidence={'footprints':'SOURCED BDOT10k',
                  'long_building_height':'SOURCED GUGiK LoD1 / LoD2',
                  'photo_identification':'ESTIMATED',
                  'pavilion_height_facades_openings_and_roofs':'WORKING_VALUE'},
                  pavilion_height_m=4.2, spruce='OPEN: use existing vegetation system')
    return result

