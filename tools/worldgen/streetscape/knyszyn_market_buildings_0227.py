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


# ADR 0227 D41 (b): the pavilion's form as data (overrides.yaml `kind: market_pavilion_d41`): owner photo 13 and the
# GUGiK 2025 orthophoto show a tent (pyramid) roof - four triangular planes to one apex - over yellow walls; without
# the entry the former hipped roof with a ridge is built. No sign, lettering or brand in either case.
PAVILION_KIND = 'market_pavilion_d41'
PAVILION_DEFAULT = {'roof': 'hip', 'eave_m': 2.8, 'apex_m': 4.2,      # WORKING_VALUE; no LoD1/LoD2 for this footprint
                    'wall_material': 'plaster_yellow', 'roof_material': 'roof_metal_graphite'}
PAVILION_ROOFS = ('hip', 'tent')
PAVILION_WALLS = ('plaster_yellow', 'plaster_cream', 'plaster_peach')
PAVILION_ROOF_MATS = ('roof_metal_graphite',)
PAVILION_LIMITS = {'eave_m': (2.2, 4.5), 'apex_m': (2.6, 7.0)}


def pavilion_spec(overrides):
    """(spec, override id or None, stale reason or None). One valid entry targeting PAVILION; anything else keeps
    PAVILION_DEFAULT and is reported stale (never raises: a bad entry must not break the region build)."""
    found = [o for o in overrides or [] if isinstance(o, dict) and o.get('kind') == PAVILION_KIND]
    if not found:
        return dict(PAVILION_DEFAULT), None, None
    o = found[0]
    if len(found) != 1:
        return dict(PAVILION_DEFAULT), o.get('id'), 'more than one market_pavilion_d41 entry'
    if o.get('target', {}).get('building') != PAVILION:
        return dict(PAVILION_DEFAULT), o.get('id'), 'target is not the market pavilion footprint'
    spec = dict(PAVILION_DEFAULT)
    st = o.get('set') or {}
    if not isinstance(st, dict) or set(st) - set(PAVILION_DEFAULT):
        return dict(PAVILION_DEFAULT), o.get('id'), 'unknown key'
    for k, v in st.items():
        if k in PAVILION_LIMITS:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not (
                    PAVILION_LIMITS[k][0] <= float(v) <= PAVILION_LIMITS[k][1]):
                return dict(PAVILION_DEFAULT), o.get('id'), f'{k} out of range'
            spec[k] = float(v)
        elif (k, v) not in [('roof', r) for r in PAVILION_ROOFS] + [('wall_material', m) for m in PAVILION_WALLS] + [
                ('roof_material', m) for m in PAVILION_ROOF_MATS]:
            return dict(PAVILION_DEFAULT), o.get('id'), f'{k} not allowed'
        else:
            spec[k] = v
    if spec['apex_m'] - spec['eave_m'] < 0.4:
        return dict(PAVILION_DEFAULT), o.get('id'), 'apex must be at least 0.4 m above the eave'
    return spec, o.get('id'), None


def _heights(bid, props, pavilion=None):
    if bid == PAVILION:
        spec = pavilion or PAVILION_DEFAULT
        return spec['eave_m'], spec['apex_m']
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


def _inset(length, width, tent=False):
    """Run of the hip planes along the long axis; a tent roof (D41) has no ridge: all four planes meet at one apex."""
    return length*.5 if tent else min(width*.5, length*.3)


def _hip(acc, layer, poly, center, axis, normal, length, width, eave, ridge, tent=False, mat='roof_metal_graphite'):
    """Four roof planes clipped to the BDOT footprint; upward-facing triangles."""
    a, b = center-axis*length/2, center+axis*length/2
    al, ar, bl, br = a-normal*width/2, a+normal*width/2, b-normal*width/2, b+normal*width/2
    inset = _inset(length, width, tent)
    ra, rb = a+axis*inset, b-axis*inset
    if tent:
        faces = [[_pt(al,eave),_pt(bl,eave),_pt(ra,ridge)], [_pt(br,eave),_pt(ar,eave),_pt(ra,ridge)]]
    else:
        faces = [[_pt(al,eave),_pt(bl,eave),_pt(rb,ridge),_pt(ra,ridge)],
                 [_pt(br,eave),_pt(ar,eave),_pt(ra,ridge),_pt(rb,ridge)]]
    faces += [
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
                acc.add(layer,mat,np.column_stack((xy,zz)),[[0,1,2]])


def _roof_at(p, center, axis, normal, length, width, eave, ridge, tent=False):
    u, v = float((p-center) @ axis), float((p-center) @ normal)
    inset = _inset(length, width, tent)
    fraction = max(0., min(1., (length/2-abs(u))/inset,
                              (width/2-abs(v))/(width/2)))
    return eave + (ridge-eave)*fraction


def _roof_boundary_fill(acc, layer, ring, center, axis, normal, length, width, eave, ridge, tent=False,
                        wall='plaster_yellow'):
    """Close gaps where a concave BDOT boundary intersects sloping roof planes."""
    for a, b in zip(ring[:-1], ring[1:]):
        steps = max(1, int(math.ceil(float(np.linalg.norm(b-a)))))
        for j in range(steps):
            p = a+(b-a)*(j/steps); q = a+(b-a)*((j+1)/steps)
            hp = _roof_at(p,center,axis,normal,length,width,eave,ridge,tent)
            hq = _roof_at(q,center,axis,normal,length,width,eave,ridge,tent)
            if max(hp,hq)-eave <= 1e-6:
                continue
            # The footprint has CCW winding, so this face points outwards.
            verts=[_pt(p,eave),_pt(q,eave),_pt(q,hq),_pt(p,hp)]
            tris=[]
            if hq-eave > 1e-6: tris.append([0,1,2])
            if hp-eave > 1e-6: tris.append([0,2,3])
            acc.add(layer,wall,verts,tris)


def _front_edges(poly, target, axis):
    return KT._edges(poly, target, axis)


def build(buf, region, blds, zsmooth, report, overrides=None):
    result = {'id': ASSET_ID, 'status': 'skipped', 'sources': list(IDS)}
    if region != REGION:  # ADR 0227: other regions get no QA entry (no diff in their streetscape_qa.json)
        return result
    report[ASSET_ID] = result
    pav, pav_id, pav_stale = pavilion_spec(overrides)
    if pav_id is not None:
        result['pavilion_override'] = pav_id
    if pav_stale:
        result['pavilion_override_stale'] = pav_stale
    selected = {b['id']:b for b in blds if b['id'] in IDS}
    if set(selected) != set(IDS) or any(b['ovr'].get('hero_asset') != ASSET_ID for b in selected.values()):
        result['reason'] = 'both hero targets required; generic buildings remain'
        return result
    prepared = {}
    for bid,b in selected.items():
        ring = np.asarray(b['poly'].exterior.coords,float)
        z = float(np.median(np.asarray(zsmooth(ring[:,0],ring[:,1]),float)))
        h = _heights(bid,b['props'],pav)
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
                    wall=pav['wall_material']
                else:
                    # Generic red storefront toward the south; no emblems or lettering.
                    wall='brick_red' if (a[1]+c[1])/2 < center[1] else 'plaster_peach'
                acc.quad(layer,wall,_pt(a,z-.15),_pt(c,z-.15),_pt(c,eave),_pt(a,eave))
            tent = bid == PAVILION and pav['roof'] == 'tent'
            _hip(acc,layer,poly,center,axis,normal,length,width,eave,ridge,tent,
                 pav['roof_material'] if bid == PAVILION else 'roof_metal_graphite')
            if bid == PAVILION:
                _roof_boundary_fill(acc,layer,ring,center,axis,normal,length,width,eave,ridge,tent,pav['wall_material'])
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
                  pavilion_height_m=pav['apex_m'], pavilion_roof=pav['roof'], pavilion_eave_m=pav['eave_m'],
                  spruce='OPEN: use existing vegetation system')
    return result

