"""Safety contracts for an unintegrated, unapproved marketplace proxy."""
import numpy as np
from shapely.geometry import MultiPoint, Polygon
from streetscape import knyszyn_market_0227 as market


class Buffer:
    def __init__(self): self.parts=[]
    def add(self,layer,mat,vertices,uv,triangles,src,UV1=None):
        self.parts.append((layer,mat,np.asarray(vertices),np.asarray(triangles),src))


def test_shelters_are_four_disjoint_proxies_inside_osm_site():
    placements=market.footprints()
    site=Polygon(market.SITE_EPSG2180)
    assert len(placements)==4
    shapes=[Polygon(corners) for _,corners in placements]
    assert all(site.buffer(-1.).covers(p) for p in shapes)
    assert all(not a.intersects(b) for i,a in enumerate(shapes) for b in shapes[i+1:])


def test_geometry_normals_budget_and_materials():
    origin=np.array([761611.,612607.]); buf=Buffer(); report={}
    result=market.build(buf,"knyszyn",origin,lambda e,n:np.zeros_like(e)+125,report)
    assert result["status"]=="applied" and result["shelters"]==4
    assert result["confidence"]=="PROXY_NOT_APPROVED / WORKING_VALUE"
    assert {p[0] for p in buf.parts}==set(market.LAYERS)
    site=Polygon(np.asarray(market.SITE_EPSG2180)-origin).buffer(1e-6)
    for layer,mat,v,tris,src in buf.parts:
        assert mat in {"plinth_dark","roof_metal_graphite"} and src==market.ASSET_ID
        assert np.isfinite(v).all() and site.covers(MultiPoint(v[:,:2]))
        cross=np.cross(v[tris[:,1]]-v[tris[:,0]],v[tris[:,2]]-v[tris[:,0]])
        assert (np.linalg.norm(cross,axis=1)>1e-9).all()
        if mat=="roof_metal_graphite": assert (cross[:,2]>0).all()
    assert all(sum(len(t) for ly,mat,v,t,src in buf.parts if ly==layer)<=200 for layer in market.LAYERS)


def test_invalid_region_or_height_produces_no_geometry():
    for region,sampler in (("knyszyn-w",lambda e,n:np.zeros_like(e)),
                           ("knyszyn",lambda e,n:np.full_like(e,np.nan))):
        buf=Buffer(); result=market.build(buf,region,[761611,612607],sampler,{})
        assert result["status"]=="skipped" and not buf.parts
