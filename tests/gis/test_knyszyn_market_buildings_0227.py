"""Opt-in marketplace buildings: measured BDOT boundaries, not visual approval."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from streetscape import buildings_mesh as BM
from streetscape import knyszyn_market_buildings_0227 as market

ROOT = Path(__file__).resolve().parents[2]

class Buffer:
    def __init__(self): self.parts=[]
    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer,mat,np.asarray(vertices),np.asarray(triangles),src))

def fc():
    d=json.loads((ROOT/'Data/Regions/knyszyn/buildings.geojson').read_text(encoding='utf-8'))
    d['features']=[f for f in d['features'] if f['id'] in market.IDS]
    return d

def test_hero_targets_are_all_or_nothing():
    d=fc()
    assert market.hero_targets('knyszyn',d)=={k:market.ASSET_ID for k in market.IDS}
    assert market.hero_targets('other',d)=={}
    assert market.hero_targets('knyszyn',{'features':d['features'][:1]})=={}
    dup={'features':d['features']+[d['features'][0]]}
    assert market.hero_targets('knyszyn',dup)=={}

def test_both_buildings_use_source_footprints_and_keep_existing_collision():
    d=fc(); hero=market.hero_targets('knyszyn',d)
    blds=BM.load(d,[761611,612607],[],hero=hero)
    assert {b['id'] for b in blds}==set(market.IDS)
    assert all(b['ovr']['hero_asset']==market.ASSET_ID for b in blds)
    buf,report=Buffer(),{}
    result=market.build(buf,'knyszyn',blds,lambda e,n:np.zeros_like(e)+127.0,report)
    assert result['status']=='applied'
    assert result['confidence']['footprints']=='SOURCED BDOT10k'
    assert result['confidence']['pavilion_height_facades_openings_and_roofs']=='WORKING_VALUE'
    assert {p[0] for p in buf.parts}==set(market.LAYERS)
    assert 'plaster_yellow' in {p[1] for p in buf.parts}
    assert 'roof_metal_graphite' in {p[1] for p in buf.parts}
    for layer,mat,vertices,triangles,src in buf.parts:
        assert np.isfinite(vertices).all()
        assert triangles.min()>=0 and triangles.max()<len(vertices)
        assert src==market.ASSET_ID
    # Roof projected polygons lie inside measured source footprints and face up.
    polys=[b['poly'] for b in blds]
    for layer,mat,v,tris,src in buf.parts:
        if mat!='roof_metal_graphite': continue
        for t in tris:
            q=v[t]; projected=Polygon(q[:,:2])
            assert any(projected.difference(p.buffer(1e-7)).area<1e-7 for p in polys)
            assert np.cross(q[1]-q[0],q[2]-q[0])[2]>0

def test_no_build_without_hero_override():
    d=fc(); blds=BM.load(d,[761611,612607],[])
    buf=Buffer()
    assert market.build(buf,'knyszyn',blds,lambda e,n:np.zeros_like(e),{})['status']=='skipped'
    assert not buf.parts


def test_pavilion_concave_eaves_are_closed():
    d=fc(); blds=BM.load(d,[761611,612607],[])
    pavilion=next(b for b in blds if b['id']==market.PAVILION)
    poly=pavilion['poly']; center,axis,normal,length,width=market.KT._frame(poly)
    ring=np.asarray(poly.exterior.coords,float)
    acc=BM.Acc()
    market._roof_boundary_fill(acc,'buildings',ring,center,axis,normal,length,width,2.8,4.2)
    buf=Buffer(); acc.flush(buf,'test')
    assert buf.parts, 'concave notch needs a wall above the eaves'
    for layer,mat,vertices,triangles,src in buf.parts:
        assert mat=='plaster_yellow'
        for t in triangles:
            q=vertices[t]
            assert np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0])) > 1e-8
            assert np.isclose(q[:,2].min(),2.8)
            assert q[:,2].max() <= 4.2
