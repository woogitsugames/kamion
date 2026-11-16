from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union
from roads import meshing as M, pipeline

@pytest.mark.parametrize("cut", [Polygon([(1,-1),(3,-1),(3,5),(1,5)]), Polygon([(1,-1),(3,-1),(3,1),(2,1),(2,5),(1,5)])])
def test_split_preserves_mesh_attributes_and_partition(cut):
    v=np.array([[0,0,2],[4,0,6],[4,4,14],[0,4,10]],float)
    uv=v[:,:2]*2; uv1=np.column_stack((v[:,0]+v[:,1],v[:,0]-v[:,1]))
    t=np.array([[0,1,2],[0,2,3]])
    b=M.MeshBuf();M._add_patch_surface(b,'road','road_asphalt',v,uv,t,True,'j:test',uv1,{'polygon':cut,'material':'road_paving'})
    geoms={}
    for part in b.parts:
        assert part.src=='j:test' and part.footprint
        assert np.allclose(part.V[:,2],2+part.V[:,0]+2*part.V[:,1])
        assert np.allclose(part.UV,part.V[:,:2]*2)
        assert np.allclose(part.UV1[:,0],part.V[:,0]+part.V[:,1])
        assert np.allclose(part.UV1[:,1],part.V[:,0]-part.V[:,1])
        tris=[]
        for inds in part.T:
            xy=part.V[inds,:2]; cross=np.linalg.det(np.stack((xy[1]-xy[0],xy[2]-xy[0])))
            assert cross>0
            tris.append(Polygon(xy))
        geoms[part.mat]=unary_union(tris)
        assert sum(t.area for t in tris)==pytest.approx(geoms[part.mat].area)
    original=Polygon(v[:,:2]); inside=geoms['road_paving']; outside=geoms['road_asphalt']
    assert inside.symmetric_difference(original.intersection(cut)).area < 1e-8
    assert outside.symmetric_difference(original.difference(cut)).area < 1e-8
    assert inside.intersection(outside).area < 1e-8
    assert unary_union([inside,outside]).symmetric_difference(original).area < 1e-8

def test_no_opt_in_preserves_arrays():
    v=np.array([[0,0,0],[1,0,1],[0,1,2]],float); uv=v[:,:2]; t=np.array([[0,1,2]])
    b=M.MeshBuf();M._add_patch_surface(b,'road','road_asphalt',v,uv,t,True,'j:x',uv,None)
    p=b.parts[0]
    assert np.array_equal(p.V,v) and np.array_equal(p.T,t) and np.array_equal(p.UV,uv) and np.array_equal(p.UV1,uv)

def test_pipeline_validation_and_local_coordinates():
    j=SimpleNamespace(id='j:x',boundary=[(np.array(p),('x',)) for p in [(0,0),(4,0),(4,4),(0,4)]])
    net=SimpleNamespace(overrides_applied=[],overrides_stale=[])
    base={'kind':'junction_surface_patch','id':'ok','junction':'j:x','material':'road_paving','polygon_epsg2180':[[101,201],[103,201],[103,203],[101,203]]}
    invalid={**base,'id':'bad','junction':'j:missing'}
    out=pipeline._junction_surface_patches([base,invalid],(100,200),[j],net)
    assert out['j:x']['polygon'].bounds==(1,1,3,3)
    assert net.overrides_stale==['bad']
    assert net.overrides_applied==[{'id':'ok','targets':['j:x']}]

def test_build_patch_opt_in_does_not_change_collision_or_other_junction(monkeypatch):
    class Flat:
        def __init__(self,j): pass
        def boundary_z(self,j,p,tag): return float(p[0]+p[1])
        def blend(self,p): return float(p[0]+p[1])
    monkeypatch.setattr(M,'PatchHeight',Flat)
    monkeypatch.setattr(M,'_patch_mat',lambda net,j:'road_asphalt')
    monkeypatch.setattr(M,'_patch_on_bridge',lambda j:False)
    monkeypatch.setattr(M,'_patch_uv1',lambda net,j,v,poly:v[:,:2]*3)
    monkeypatch.setattr(M,'build_corner_strips',lambda *a,**kw:None)
    j=SimpleNamespace(id='j:x',boundary=[(np.array(p,float),('end',0,0)) for p in [(0,0),(4,0),(4,4),(0,4)]])
    spec={'polygon':Polygon([(1,-1),(3,-1),(3,5),(1,5)]),'material':'road_paving'}
    before=M.MeshBuf();after=M.MeshBuf()
    M.build_patch(before,None,j,coarse=True)
    M.build_patch(after,None,j,coarse=True,visual_surface_patch=spec)
    assert len(before.parts)==len(after.parts)==1
    a,b=before.parts[0],after.parts[0]
    assert a.mat==b.mat=='collision_asphalt'
    assert np.array_equal(a.V,b.V) and np.array_equal(a.T,b.T) and np.array_equal(a.UV,b.UV)
    base=M.MeshBuf();unmatched=M.MeshBuf()
    M.build_patch(base,None,j)
    M.build_patch(unmatched,None,j,visual_surface_patch={}.get(j.id))
    assert np.array_equal(base.parts[0].V,unmatched.parts[0].V)
    assert np.array_equal(base.parts[0].T,unmatched.parts[0].T)
    assert np.array_equal(base.parts[0].UV1,unmatched.parts[0].UV1)
