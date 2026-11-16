import json
from pathlib import Path
import numpy as np
import pytest
import yaml
from streetscape import buildings_mesh as BM
from test_buildings_0167 import _build

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'Data/Regions/knyszyn'
ORIGIN=(761611.,612607.)
IDS={
 'bdot:2002917F-3002-5C99-E053-CC2BA8C01CFC':'roof_metal_graphite',
 'bdot:2002917F-3066-5C99-E053-CC2BA8C01CFC':'roof_tiles_red',
 'bdot:2002917F-3078-5C99-E053-CC2BA8C01CFC':'roof_metal_graphite',
 'bdot:2002917F-2E16-5C99-E053-CC2BA8C01CFC':'roof_tiles_red',
}

def test_authored_roofs_keep_triangle_counts_and_other_surfaces():
 fc=json.loads((R/'buildings.geojson').read_text(encoding='utf8'))
 ov=yaml.safe_load((R/'overrides.yaml').read_text(encoding='utf8'))['overrides']
 orig={b['id']:b for b in BM.load(fc,ORIGIN,[]) if b['id'] in IDS}
 edited={b['id']:b for b in BM.load(fc,ORIGIN,ov) if b['id'] in IDS}
 assert set(orig)==set(edited)==set(IDS)
 for bid,mat in IDS.items():
  a=_build(orig[bid]);b=_build(edited[bid])
  for layer in ('buildings','buildings_low'):
   roofs=lambda buf:[p for p in buf.parts if p.layer==layer and p.mat in {x[0] for x in BM.HOUSE_ROOFS}]
   ar,br=roofs(a),roofs(b)
   assert ar and br and mat in {p.mat for p in br}
   assert sum(len(p.T) for p in a.parts if p.layer==layer)==sum(len(p.T) for p in b.parts if p.layer==layer)
  assert [(p.layer,p.mat,len(p.T)) for p in a.parts if p.mat not in ({x[0] for x in BM.HOUSE_ROOFS} | {'hall_flashing','soffit_boards'})]==[(p.layer,p.mat,len(p.T)) for p in b.parts if p.mat not in ({x[0] for x in BM.HOUSE_ROOFS} | {'hall_flashing','soffit_boards'})]

def test_invalid_roof_material_names_building():
 with pytest.raises(ValueError,match='test-house.*unsupported roof_material'):
  BM.house_roof_material({'id':'test-house','ovr':{'roof_material':'not-a-roof'}},'roof_tiles_red')



