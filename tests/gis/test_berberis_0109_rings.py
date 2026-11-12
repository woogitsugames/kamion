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
    original_fill=pt._fill
    caps=[]
    def checked_fill(ring,spacing):
        polygon=Polygon(ring)
        assert polygon.is_valid
        vertices,triangles=original_fill(ring,spacing)
        faces=vertices[triangles]
        assert np.linalg.norm(faces[:,[1,2,0]]-faces,axis=2).max()<1.5
        assert all(polygon.buffer(1e-7).covers(Polygon(face)) for face in faces)
        caps.append((vertices,triangles))
        return vertices,triangles
    monkeypatch.setattr(pt,'_fill',checked_fill)
    class Capture:
        def __init__(self): self.parts=[]
        def add(self,layer,material,vertices,uv,triangles,**kwargs):
            self.parts.append((np.asarray(vertices),np.asarray(triangles)))
    poly,key,bed=authored_bed(bed_index)
    buf=Capture()
    pt.hedge_mass(buf,poly,lambda x,y:slope*x+.5*slope*y,key,h=bed.get('height_m'))
    assert len(caps)==2, 'Both inner and outer cap must be emitted'
    # The first and third parts are the two six-ring side strips.
    for vertices,_ in (buf.parts[0],buf.parts[2]):
        rings=vertices[:,:2].reshape(6,-1,2)
        for outer,inner in zip(rings,rings[1:]):
            quads=[]
            for i in range(len(outer)):
                j=(i+1)%len(outer)
                quad=Polygon([outer[i],outer[j],inner[j],inner[i]])
                assert quad.is_valid and quad.area>1e-10, 'Crossed or collapsed side strip'
                quads.append(quad)
            union=shapely.union_all(quads)
            assert abs(sum(q.area for q in quads)-union.area)<1e-7, 'Side quads overlap globally'
            annulus=Polygon(outer).symmetric_difference(Polygon(inner))
            assert union.symmetric_difference(annulus).area<1e-7, 'Side strip leaves its annulus'
    core_rings=buf.parts[0][0][:,:2].reshape(6,-1,2)
    shell_rings=buf.parts[2][0][:,:2].reshape(6,-1,2)
    for core_ring,shell_ring in zip(core_rings,shell_rings):
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
        pt._offset_ring(narrow,.2,20,[0,0])
