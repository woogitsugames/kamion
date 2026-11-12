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
            for i in range(len(outer)):
                j=(i+1)%len(outer)
                quad=Polygon([outer[i],outer[j],inner[j],inner[i]])
                assert quad.is_valid and quad.area>1e-10, 'Crossed or collapsed side strip'


def test_offset_refuses_disconnected_or_empty_geometry_instead_of_dropping_a_piece():
    from shapely.geometry import box
    narrow=box(0,0,4,.2)
    with pytest.raises(ValueError,match='not one valid polygon'):
        pt._offset_ring(narrow,.2,20,[0,0])
