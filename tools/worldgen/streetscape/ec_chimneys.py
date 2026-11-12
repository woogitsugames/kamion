"""EC Białystok hero assets, ADR 0116 r3. No changes to life/furniture generators.

Only the two named landmark overrides opt in through their region's own config.
The generic chimney stays as a fallback whenever spec, config or GLB is stale.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
REGION = 'bialystok-industrial-c'
SCHEMA = 'truck-sim-pl/ec-chimney-spec/1'


def config():
    path = REPO/'Data/Regions'/REGION/'ec_chimneys.json'
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if value.get('enabled') is True else None
    except (OSError, ValueError):
        return None


def entry(o, cfg):
    if not cfg or o.get('kind') != 'landmark':
        return None
    return cfg.get('stacks', {}).get(str(o.get('osm_way')))


def source_override(o):
    return {key: o.get(key) for key in ('id','kind','osm_way','epsg2180','height_m','base_d_m','top_d_m')}


def valid_dimensions(d, o):
    """Bad authored values preserve the existing fallback instead of exporting NaNs."""
    try:
        if d['asset'] not in ('ec_chimney_single','ec_chimney_multi'):
            return False
        if float(o['height_m']) != 120 or float(d['height_m']) != 120:
            return False
        numeric = [d['base_d_m'],d['top_d_m'],d['paint_start_m'],*d['band_boundaries_m'],*d['galleries_m']]
        if not all(math.isfinite(float(v)) for v in numeric):
            return False
        if not (4 <= d['top_d_m'] <= 9 and 6 <= d['base_d_m'] <= 10):
            return False
        b = d['band_boundaries_m']
        return (b[0] == d['paint_start_m'] and b[-1] == 120 and
                all(a < b for a,b in zip(b,b[1:])) and 0 < b[0] < 120 and
                d['outlets'] in (1,3) and all(0 < g < 119 for g in d['galleries_m']))
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def make_spec(o, d, cfg, origin, zground):
    if not valid_dimensions(d,o):
        return None
    x,y=o['epsg2180']; ox,oy=origin
    anchor=[round(x-ox,3),round(y-oy,3),round(float(zground(x-ox,y-oy)),3)]
    return dict(schema=SCHEMA,builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                id=o['id'],asset=d['asset'],region=REGION,osm_way=o['osm_way'],
                source_override=source_override(o),configuration=cfg,buildings=[],footprints={},dims={},
                anchor=anchor,ground=dict(fence=[],gate=[],flagpoles=[],thuja=[],spruce=[]),
                chimney=d,lod_ends_m=[650.,20000.],
                confidence=cfg['confidence'])


def active(o, origin):
    """Used after hero planning. Never suppress a generic instance on config alone."""
    from . import hero_building as HB
    cfg=config(); d=entry(o,cfg)
    if not d or not valid_dimensions(d,o):
        return None
    try:
        spec=json.loads(HB.spec_path(REGION,d['asset']).read_text(encoding='utf-8'))
        x,y=o['epsg2180']
        if (spec.get('schema')!=SCHEMA or spec.get('configuration')!=cfg or
            spec.get('builder_sha256')!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest() or
            spec.get('source_override')!=source_override(o) or
            spec.get('anchor',[])[:2]!=[round(x-origin[0],3),round(y-origin[1],3)]):
            return None
        meta,why=HB._asset_meta(d['asset'],HB._sha(spec))
        return meta if why=='ok' else None
    except (OSError,ValueError,KeyError,TypeError):
        return None


def annulus(mesh,mat,z,inner,outer,seg):
    a=np.arange(seg+1)*2*math.pi/seg
    ring=np.column_stack([np.cos(a),np.sin(a)])
    V=np.column_stack([np.concatenate([ring*inner,ring*outer]),np.full(2*(seg+1),z)])
    n=seg+1
    T=[t for i in range(seg) for t in ((i,n+i,n+i+1),(i,n+i+1,i+1))]
    mesh.add(mat,V,T,np.zeros((len(V),2)))


def disk(mesh,mat,z,radius,seg,centre=(0.,0.)):
    a=np.arange(seg+1)*2*math.pi/seg
    ring=np.column_stack([np.cos(a)*radius+centre[0],np.sin(a)*radius+centre[1],np.full(seg+1,z)])
    V=np.vstack([[centre[0],centre[1],z],ring])
    mesh.add(mat,V,[(0,k+1,k+2) for k in range(seg)])


def meshes(d):
    from .props import Mesh
    out=[]
    H=d['height_m']
    radius=lambda z:(d['base_d_m']+(d['top_d_m']-d['base_d_m'])*max(0,z)/H)/2
    for lod,seg in enumerate((20,12)):
        m=Mesh()
        bounds=[-1.,*d['band_boundaries_m']]
        shaft_top=116.8 if d['outlets']==3 else H
        for k,(a,b) in enumerate(zip(bounds,bounds[1:])):
            if a>=shaft_top:
                continue
            b=min(b,shaft_top)
            # White lower body; upper bands alternate red/white with a red top.
            mat='chimney_white' if k==0 or k%2==0 else 'chimney_red'
            m.tube(mat,[0,0,a],[0,0,b],radius(a),radius(b),seg,cap=False)
        dark='chimney_concrete'
        if d['outlets']==3:
            # Three separate flues, not a single tapered capped cone. Dimensions
            # of the head remain WORKING_VALUE; total height remains exactly120m.
            disk(m,'chimney_red',shaft_top,radius(shaft_top),seg)
            for k in range(3):
                a=math.radians(30+120*k)
                x,y=1.8*math.cos(a),1.8*math.sin(a)
                m.tube('chimney_red',[x,y,shaft_top],[x,y,H],.78,.78,8 if lod==0 else 6,cap=False)
                disk(m,dark,H-.4,.64,8 if lod==0 else 6,(x,y))
        else:
            annulus(m,'chimney_red',H,radius(H)-.22,radius(H)+.10,seg)
            disk(m,dark,H-.7,radius(H)-.22,12)
        # The photograph's galleries are pale painted structures. Reuse this
        # existing material on both LODs; no fourth material or new shader path.
        gallery_mat='chimney_white'
        gallery_seg=8
        for z in d['galleries_m']:
            outer=radius(z)+.75
            annulus(m,gallery_mat,z,radius(z),outer,gallery_seg)
            # A horizontal one-sided annulus vanished from below on LOD1.
            # The 0.25m outer fascia is a WORKING_VALUE, visible on both LODs.
            m.tube(gallery_mat,[0,0,z-.25],[0,0,z],outer,outer,gallery_seg,cap=False)
            if lod==0:
                # Thin rails, open centre. Low keeps the silhouette with one annulus.
                for zz in (z+.5,z+1.):
                    for k in range(gallery_seg):
                        a,b=2*math.pi*k/gallery_seg,2*math.pi*(k+1)/gallery_seg
                        m.tube(gallery_mat,[outer*math.cos(a),outer*math.sin(a),zz],
                               [outer*math.cos(b),outer*math.sin(b),zz],.028,None,3,cap=False)
                for k in range(0,gallery_seg,2):
                    a=2*math.pi*k/gallery_seg
                    m.tube(gallery_mat,[outer*math.cos(a),outer*math.sin(a),z],
                           [outer*math.cos(a),outer*math.sin(a),z+1.],.028,None,3,cap=False)
        out.append(m.out())
    return out


def build_asset(spec):
    from terrain_mesh.gltf import GLB
    from .materials import M
    from .export import crease_normals
    from . import hero_building as HB
    prims=meshes(spec['chimney'])
    asset=spec['asset']; proto='landmark_'+asset
    glb=GLB(M)
    for k,lod in enumerate(prims):
        glb.add_mesh(proto+('.lod1' if k else ''),crease_normals(lod))
    payload=glb.bytes(dict(adr='0116 r3',spec_sha256=HB._sha(spec)))
    folder,gpath,mpath=HB.asset_paths(asset)
    folder.mkdir(parents=True,exist_ok=True)
    gpath.write_bytes(payload)
    tris=[sum(len(p['T']) for p in lod) for lod in prims]
    meta=dict(prototype=proto,spec_sha256=HB._sha(spec),glb_sha256=hashlib.sha256(payload).hexdigest(),
              tris=[*tris,tris[-1]],materials=sorted({p['mat'] for lod in prims for p in lod}),
              materials_per_lod=[sorted({p['mat'] for p in lod}) for lod in prims],
              lod_nodes=2,confidence=spec['confidence'])
    mpath.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    return meta


def plan(region_id,overrides,origin,zground,report,log):
    from . import hero_building as HB
    if region_id!=REGION:
        return []
    cfg=config()
    if not cfg:
        return []
    out=[]
    rep=report.setdefault('hero_buildings',dict(applied=[],stale=[]))
    for o in overrides:
        d=entry(o,cfg)
        if not d:
            continue
        spec=make_spec(o,d,cfg,origin,zground)
        if spec is None:
            rep['stale'].append(dict(id=o['id'],why='Invalid EC configuration; generic chimney retained'))
            continue
        HB.write_spec(region_id,spec)
        sha=HB._sha(spec)
        meta,why=HB._asset_meta(d['asset'],sha)
        if meta is None and why!='glb_changed':
            meta=build_asset(spec)
        if meta is None:
            rep['stale'].append(dict(id=o['id'],why='Changed EC GLB; generic chimney retained'))
            continue
        out.append(dict(override=o,spec=spec,meta=meta,sha=sha))
        log('EC chimney hero ready:',d['asset'],meta['tris'])
    return out
