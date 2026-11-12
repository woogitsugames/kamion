"""Read-only raw GLB footprint inventory; no generator/source edits."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def glb(path):
    b=path.read_bytes();length=struct.unpack_from('<I',b,12)[0]
    d=json.loads(b[20:20+length]);blob=b[28+length:]
    def acc(i):
        a=d['accessors'][i];v=d['bufferViews'][a['bufferView']]
        dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
        cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        assert 'byteStride' not in v
        return np.frombuffer(blob,dtype=dtype,count=a['count']*cols,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,cols)
    return d,acc

def main():
    manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
    components=[];paint=[];stops=[]
    for ch in manifest['chunks']:
        path=ROOT/ch['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==ch['sha256']
        d,acc=glb(path)
        for node in d['nodes']:
            if node.get('name')!='markings':continue
            for p in d['meshes'][node['mesh']]['primitives']:
                mat=d['materials'][p['material']]['name']
                if mat not in ('decal_patch','decal_oil','decal_tyre','marking_white','marking_yellow'):continue
                xyz=acc(p['attributes']['POSITION']).astype(float);enu=xyz[:,[0,2,1]];enu[:,0]*=-1
                ix=acc(p['indices']).reshape(-1,3)
                area=np.linalg.norm(np.cross(enu[ix[:,1]]-enu[ix[:,0]],enu[ix[:,2]]-enu[ix[:,0]]),axis=1)*.5
                uv=acc(p['attributes']['TEXCOORD_1']) if 'TEXCOORD_1' in p['attributes'] else None
                if mat.startswith('marking_'):
                    half=np.all(np.abs(uv[ix,0]-.5)<1e-5,axis=1) if uv is not None else np.zeros(len(ix),bool)
                    paint.append(dict(chunk=ch['id'],material=mat,area_m2=float(area.sum()),constant_half_area_m2=float(area[half].sum()),uv1_present=uv is not None));continue
                parent=np.arange(len(enu))
                def find(a):
                    while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
                    return a
                for a,b,c in ix:
                    r=find(a);parent[find(b)]=r;parent[find(c)]=r
                roots=np.array([find(i) for i in range(len(enu))]);groups={}
                for j,r in enumerate(roots):groups.setdefault(int(r),[]).append(j)
                for r,ids in groups.items():
                    pts=enu[ids];tri=roots[ix[:,0]]==r;ar=float(area[tri].sum())
                    if ar<.005:continue
                    ctr=np.average(enu[ix[tri]].mean(axis=1),axis=0,weights=area[tri])
                    components.append(dict(chunk=ch['id'],material=mat,center_enu=ctr.tolist(),bounds_enu=[pts.min(axis=0).tolist(),pts.max(axis=0).tolist()],area_m2=ar,triangles=int(tri.sum()),source=ch['file'],source_sha256=ch['sha256']))
        inst=json.loads((ROOT/ch['instances']['file']).read_text())
        stops.extend(dict(chunk=ch['id'],center_enu=[i['e'],i['n'],i['z']],source=i.get('src'),yaw=i.get('yaw')) for i in inst['instances'] if i['p']=='bus_shelter')
    for stop in stops:
        oil=[x for x in components if x['material']=='decal_oil']
        nearest=sorted(oil,key=lambda x:np.linalg.norm(np.array(x['center_enu'][:2])-stop['center_enu'][:2]))[:3]
        stop['nearest_oil']=[dict(component=components.index(x),distance_m=float(np.linalg.norm(np.array(x['center_enu'][:2])-stop['center_enu'][:2])),same_chunk=x['chunk']==stop['chunk']) for x in nearest]
    packet=dict(note='Raw source footprints only; spatial proximity is NOT bus-stop oil attribution or actual image visibility. Connected components identify geometry, not generator source IDs (not exported in GLB). Areas m2 are not pixels.',components=components,paint=paint,bus_shelters=stops)
    (OUT/'source-field-inventory.json').write_text(json.dumps(packet,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(components={m:sum(x['material']==m for x in components) for m in ('decal_patch','decal_oil','decal_tyre')},paint_area_m2=sum(x['area_m2'] for x in paint),paint_half_area_m2=sum(x['constant_half_area_m2'] for x in paint),bus_shelters=len(stops))))
if __name__=='__main__':main()
