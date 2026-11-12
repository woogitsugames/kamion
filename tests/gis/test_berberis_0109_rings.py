"""Photographed bed caps must not fall back to metre-long crossing triangles."""
from pathlib import Path

import numpy as np
import pytest
import shapely
import yaml
from shapely.geometry import Polygon

from streetscape import plantings as pt

ROOT=Path(__file__).resolve().parents[2]
REGION=ROOT/'Data/Regions/bialystok-industrial-c'


def authored_bed(index):
    plans=yaml.safe_load((REGION/'overrides.yaml').read_text(encoding='utf-8'))['overrides']
    plan=next(p for p in plans if p.get('id')=='biezenstwa-plantings')
    bed=plan['beds'][index]
    # Translation cannot change polygon validity; use local coordinates here.
    ring=np.asarray(bed['ring'],float)
    poly=Polygon(ring-ring[0])
    poly=shapely.make_valid(poly).buffer(-float(bed.get('rim_m',.6))).buffer(.25)
    key=(plan['id'],index,0)
    preset=pt.species(bed.get('plant','berberis_red'))
    width=preset['band'][0]+pt._h(*key,'band')*(preset['band'][1]-preset['band'][0])
    return pt.band_of(poly,width),key,bed


@pytest.mark.parametrize('bed_index',range(4))
@pytest.mark.parametrize('slope',[0.,.03])
def test_authored_berberis_has_valid_local_caps_and_uncrossed_strips(monkeypatch,bed_index,slope):
    from roads import geom
    # A valid Delaunay result may contain boundary vertices only on a narrow bed.
    # It must never use the invalid-ring ear-clipping escape route again.
    monkeypatch.setattr(geom,'ear_clip',lambda *args: pytest.fail('Authored hedge used ear_clip fallback'))
    original_fill=pt._hedge_cap
    caps=[]
    def checked_fill(ring,spacing):
        polygon=Polygon(ring)
        assert polygon.is_valid
        vertices,triangles=original_fill(ring,spacing)
        faces=vertices[triangles]
        assert np.linalg.norm(faces[:,[1,2,0]]-faces,axis=2).max()<1.5
        assert all(polygon.buffer(1e-7).covers(Polygon(face)) for face in faces)
        union=shapely.union_all(shapely.polygons(faces))
        assert union.symmetric_difference(polygon).area<1e-7
        assert abs(shapely.area(shapely.polygons(faces)).sum()-union.area)<1e-7
        caps.append((vertices,triangles))
        return vertices,triangles
    monkeypatch.setattr(pt,'_hedge_cap',checked_fill)
    original_annulus=pt._annulus_triangles
    def checked_annulus(lower,upper):
        triangles=original_annulus(lower,upper)
        points=np.vstack([lower,upper])
        faces=shapely.polygons(points[triangles])
        target=Polygon(lower).symmetric_difference(Polygon(upper))
        union=shapely.union_all(faces)
        assert all(target.buffer(1e-7).covers(face) for face in faces)
        assert abs(shapely.area(faces).sum()-union.area)<1e-7
        assert union.symmetric_difference(target).area<1e-7
        a,b,c=(points[triangles[:,i]] for i in range(3))
        signed=(b[:,0]-a[:,0])*(c[:,1]-a[:,1])-(b[:,1]-a[:,1])*(c[:,0]-a[:,0])
        assert (signed<0).all() if Polygon(upper).area>Polygon(lower).area else (signed>0).all()
        return triangles
    monkeypatch.setattr(pt,'_annulus_triangles',checked_annulus)
    original_strip=pt._hedge_ring_strip
    ring_sets=[]
    def checked_strip(rings,zground,tile,phase=(0.,0.)):
        ring_sets.append(rings)
        vertices,uv,triangles=original_strip(rings,zground,tile,phase)
        boundary={tuple(p) for xy,z in rings for p in np.column_stack([xy,z])}
        assert all(tuple(p) in boundary for p in vertices), 'Boundary height was changed'
        period=min(Polygon(xy).length/tile for xy,z in rings)
        assert np.ptp(uv[triangles][:,:,0],axis=1).max()<period/2, 'UV wraps through a whole hedge'
        return vertices,uv,triangles
    monkeypatch.setattr(pt,'_hedge_ring_strip',checked_strip)
    class Capture:
        def __init__(self): self.parts=[]
        def add(self,layer,material,vertices,uv,triangles,**kwargs):
            self.parts.append((np.asarray(vertices),np.asarray(triangles)))
    poly,key,bed=authored_bed(bed_index)
    buf=Capture()
    pt.hedge_mass(buf,poly,lambda x,y:slope*x+.5*slope*y,key,h=bed.get('height_m'))
    assert len(caps)==2, 'Both inner and outer cap must be emitted'
    assert len(ring_sets)==2
    for (core_ring,_),(shell_ring,_) in zip(*ring_sets):
        assert Polygon(shell_ring).buffer(1e-7).covers(Polygon(core_ring)), 'Inner ring leaves the shell'
    # Compare the actual triangulated cap, not the interpolated boundary field.
    # Both flat and sloping ground use exactly the same shell geometry as export.
    core=buf.parts[1][0]
    shell_vertices,shell_indices=buf.parts[3]
    triangles=shell_vertices[shell_indices]
    a,b,c=(triangles[:,i,:2] for i in range(3))
    ab,ac=b-a,c-a
    ap=core[:,None,:2]-a[None,:,:]
    cross=lambda x,y:x[...,0]*y[...,1]-x[...,1]*y[...,0]
    den=cross(ab,ac)
    valid=abs(den)>1e-10
    w1=cross(ap,ac)/np.where(valid,den,1)
    w2=cross(ab,ap)/np.where(valid,den,1)
    w0=1-w1-w2
    inside=valid & (w0>=-1e-7) & (w1>=-1e-7) & (w2>=-1e-7)
    height=w0*triangles[:,0,2]+w1*triangles[:,1,2]+w2*triangles[:,2,2]
    shell_top=np.where(inside,height,-np.inf).max(axis=1)
    assert np.isfinite(shell_top).all(), 'Inner cap leaves the shell footprint'
    assert np.max(core[:,2]-shell_top)<=.005, 'Inner cap protrudes through the triangulated shell'


def test_offset_refuses_disconnected_or_empty_geometry_instead_of_dropping_a_piece():
    from shapely.geometry import box
    narrow=box(0,0,4,.2)
    with pytest.raises(ValueError,match='not one valid polygon'):
        pt._offset_ring(narrow,.2,step=.45,anchor=np.array([0.,0.]))


def test_offset_refuses_holes_instead_of_filling_them():
    polygon=Polygon([(0,0),(5,0),(5,5),(0,5)],holes=[[(1,1),(1,2),(2,2),(2,1)]])
    with pytest.raises(ValueError,match='not one valid polygon'):
        pt._offset_ring(polygon,0.)


def test_annulus_refuses_crossing_outlines():
    lower=np.array([[0.,0.],[2.,0.],[2.,2.],[0.,2.]])
    with pytest.raises(ValueError,match='not strictly nested'):
        pt._annulus_triangles(lower,lower+[1.,0.])


def test_cap_samples_on_an_internal_edge_split_both_neighbours_without_a_crack():
    ring=np.array([[0.,0.],[2.,0.],[2.,2.],[0.,2.]])
    points,triangles=pt._hedge_cap(ring,.5)
    assert len(points)>len(ring)
    polygons=shapely.polygons(points[triangles])
    union=shapely.union_all(polygons)
    assert abs(shapely.area(polygons).sum()-4.)<1e-9
    assert union.symmetric_difference(Polygon(ring)).area<1e-9
    for face in triangles:
        for i,j in zip(face,np.roll(face,-1)):
            a,b=points[i],points[j]
            for k,p in enumerate(points):
                if k in (i,j): continue
                delta=b-a
                cross=delta[0]*(p-a)[1]-delta[1]*(p-a)[0]
                station=np.dot(p-a,delta)/np.dot(delta,delta)
                assert not (abs(cross)<1e-10 and 1e-9<station<1.-1e-9), 'Unsplit T junction'
