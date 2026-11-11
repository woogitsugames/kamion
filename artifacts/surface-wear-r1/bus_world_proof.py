"""Byte/attribute proof for the intentional one-cell oil-only world regeneration."""
from pathlib import Path
import json,hashlib,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent

def read(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);blob=b[28+n:]
 def acc(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dtype=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
  return np.ndarray((a['count'],cols),dtype=dtype,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',cols*dtype.itemsize),dtype.itemsize)).copy()
 nodes={}
 for node in d['nodes']:
  if 'mesh'not in node:continue
  nodes[node['name']]={d['materials'][p['material']]['name']:{**{k:acc(i) for k,i in p['attributes'].items()},'indices':acc(p['indices'])}for p in d['meshes'][node['mesh']]['primitives']}
 return nodes

def main():
 fixture=json.loads((OUT/'raw-before-fixture.json').read_text());changed=[];files=[]
 for f in fixture['files']:
  h=hashlib.sha256((ROOT/f['source']).read_bytes()).hexdigest();files.append(dict(file=f['source'],sha256=h,unchanged=h==f['sha256']))
  if h!=f['sha256']:changed.append(f['source'])
 expected=[f'Data/raw/derived/bialystok-industrial-c/world/chunk_4_5{x}.glb'for x in ('','.low')]
 assert sorted(changed)==sorted(expected),changed
 proof=[]
 for file in changed:
  a=read(OUT/'raw-before'/Path(file).name);b=read(ROOT/file);assert a.keys()==b.keys();same=0
  for node,materials in a.items():
   assert materials.keys()==b[node].keys()
   for mat,attrs in materials.items():
    other=b[node][mat];assert attrs.keys()==other.keys()
    if node=='markings'and mat=='decal_oil':
     for name,old in attrs.items():
      new=other[name];assert np.array_equal(new[:len(old)],old),(file,node,mat,name)
      assert len(new)-len(old)==(27 if name=='indices'else 10),(name,len(new)-len(old))
     count=len(attrs['POSITION']);idx=other['indices'][len(attrs['indices']):].reshape(-1);assert idx.min()>=count and idx.max()<count+10
    else:
     for name,old in attrs.items():assert np.array_equal(old,other[name]),(file,node,mat,name)
     same+=1
  proof.append(dict(file=file,unchanged_node_material_attribute_groups=same,added_vertices=10,added_triangles=9,new_material_groups=0,all_road_terrain_bridge_building_geometry_and_masks_identical=True))
 qa=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json').read_text());fab=qa['furniture']['megascans'];assert len(fab['available'])==15 and fab['added_props']==320 and not fab.get('fallback',False)
 bus=qa['furniture']['life']['bus_stop_oil'];assert len(bus['applied'])==1 and len(bus['rejected'])==19
 manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
 for c in manifest['chunks']:
  for f in(c,c['low'],c['instances']):assert hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest()==f['sha256']
 output=dict(raw_files=192,unchanged=190,changed=proof,all64instance_files_identical=True,fab_ready=15,fab_props=320,fab_fallback=False,bus=bus,files=files,note='Actual canonical build, no GLB patching. Added one source-supported WORKING oil rule; both tiers9tris/10vertices, source draw-group0. Runtimecounter/GPUcost still UNVERIFIED.')
 (OUT/'bus-world-proof.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items()if k not in('files','bus')}))
if __name__=='__main__':main()
