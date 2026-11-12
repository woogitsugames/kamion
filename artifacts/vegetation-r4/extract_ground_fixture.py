"""Read one10MB GLB's1m terrain nodes; no world generation or geometry tests.

The stage samples its conformed zc grid bilinearly. Each LOD0 primitive begins
with129x129 of those nodes, rounded to1mm. Skirts and merged verge vertices
follow them and are excluded only after validating the complete grid layout.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REGION=ROOT/'Data/Regions/bialystok-industrial-c'
DEST=ROOT/'tests/gis/fixtures/berberis_0109_ground_c.json'
parser=argparse.ArgumentParser()
parser.add_argument('--verify',action='store_true')
args=parser.parse_args()
path=ROOT/'Data/raw/derived/bialystok-industrial-c/world/chunk_6_6.glb'
data=path.read_bytes()
magic,version,length=struct.unpack_from('<4sII',data)
if magic!=b'glTF' or version!=2 or length!=len(data): raise ValueError('Invalid GLB')
doc=binary=None
cursor=12
while cursor<len(data):
    count,kind=struct.unpack_from('<I4s',data,cursor)
    cursor+=8
    if kind==b'JSON': doc=json.loads(data[cursor:cursor+count])
    elif kind==b'BIN\0': binary=memoryview(data)[cursor:cursor+count]
    cursor+=count
if doc is None or binary is None: raise ValueError('Missing GLB chunks')
nodes=[(i,n) for i,n in enumerate(doc['nodes']) if n.get('name')=='terrain_lod0']
if len(nodes)!=1: raise ValueError('Expected one1m terrain node')
ni,node=nodes[0]
if any(k in node for k in ('matrix','translation','rotation','scale')) or any(ni in n.get('children',[]) for n in doc['nodes']):
    raise ValueError('Nonidentity terrain ancestry needs explicit handling')
origin=json.loads((REGION/'generated/world_manifest.json').read_text())['origin_epsg2180']
plan=next(p for p in yaml.safe_load((REGION/'overrides.yaml').read_text(encoding='utf-8'))['overrides'] if p.get('id')=='biezenstwa-plantings')
beds=[]
for index,bed in enumerate(plan['beds']):
    es=[p[0]-origin['x'] for p in bed['ring']]
    ns=[p[1]-origin['y'] for p in bed['ring']]
    beds.append(dict(index=index,anchor_epsg2180=bed['ring'][0],x0=math.floor(min(es))-2,y0=math.floor(min(ns))-2,
                     x1=math.ceil(max(es))+2,y1=math.ceil(max(ns))+2))
points={}
digest=hashlib.sha256()
primitives=doc['meshes'][node['mesh']]['primitives']
if len(primitives)!=4 or node.get('extras',{}).get('spacing_m')!=1:
    raise ValueError('Unexpected1m terrain subdivision contract')
for primitive in primitives:
    value=doc['accessors'][primitive['attributes']['POSITION']]
    view=doc['bufferViews'][value['bufferView']]
    if value['componentType']!=5126 or value['type']!='VEC3' or value.get('sparse') or view.get('byteStride',12)!=12:
        raise ValueError('Unsupported terrain position accessor')
    grid_count=129*129
    if value['count']<grid_count+4*129: raise ValueError('Grid/skirt prefix is incomplete')
    offset=view.get('byteOffset',0)+value.get('byteOffset',0)
    buf=binary[offset:offset+grid_count*12]
    digest.update(buf)
    first_x,_,first_n=struct.unpack_from('<fff',buf)
    for station,(x,z,n) in enumerate(struct.iter_unpack('<fff',buf)):
        e=-x  # glTF(-E,U,N), no node transforms
        j,i=divmod(station,129)
        if abs(e-(-first_x+i))>.0001 or abs(n-(first_n-j))>.0001:
            raise ValueError('LOD0 prefix is not the full regular129x129 grid')
        if not any(b['x0']<=e<=b['x1'] and b['y0']<=n<=b['y1'] for b in beds): continue
        ie,jn=round(e),round(n)
        if abs(ie-e)>.0005 or abs(jn-n)>.0005: raise ValueError('Terrain is not on the expected integer1m local grid')
        key=(ie,jn)
        if key in points and abs(points[key]-float(z))>.0001: raise ValueError('Shared grid nodes disagree')
        points[key]=float(z)
for bed in beds:
    bed['heights_m']=[[round(points[(e,n)],3) for e in range(bed['x0'],bed['x1']+1)]
                      for n in range(bed['y0'],bed['y1']+1)]
fixture=dict(version=1,source_glb=str(path.relative_to(ROOT)),source_glb_sha256=hashlib.sha256(data).hexdigest(),
             terrain_positions_sha256=digest.hexdigest(),source_node='terrain_lod0',spacing_m=1.,height_quantization_m=.001,
             origin_epsg2180=origin,beds=beds,
             note='Frozen WorldC conformed1m terrain nodes, not raw NMT. Rows increase north, columns east. Bilinear reconstruction approximates the producer zground to exported1mm quantization; not a4m collider or runtime PhysX test.')
if args.verify:
    expected=json.loads(DEST.read_text(encoding='utf-8'))
    fields=('version','terrain_positions_sha256','spacing_m','origin_epsg2180','beds')
    differences=[k for k in fields if fixture[k]!=expected[k]]
    result=dict(source_fixture=str(DEST.relative_to(ROOT)),current_glb_sha256=fixture['source_glb_sha256'],
                expected_source_glb_sha256=expected['source_glb_sha256'],differences=differences,pass_ground_not_changed=not differences,
                note='Single chunk1m terrain positions and all frozen sample grids compared; source GLB whole hash may differ due to hedges.')
    (HERE/'ground-fixture-d-proof.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if differences: raise SystemExit('Ground fixture changed: '+str(differences))
    print('D conformed ground matches frozen C1m fixture')
else:
    if DEST.exists(): raise SystemExit('Fixture exists; no implicit overwrite')
    snapshot=json.loads((HERE/'snapshot-candidate-c/sha256.json').read_text())
    if snapshot['files'][str(path.relative_to(ROOT))]!=fixture['source_glb_sha256']: raise ValueError('Input is not the frozen C source GLB')
    fixture['source_snapshot_sha']=snapshot['source_sha']
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(fixture,indent=2)+'\n',encoding='utf-8')
    print('Frozen C ground fixture:',len(beds),'beds,',sum(len(b['heights_m'])*len(b['heights_m'][0]) for b in beds),'nodes')
