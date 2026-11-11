"""Small read-only ray/UV probe of baseline hero geometry at the suspicious wall patch."""
import json
import struct
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
b=(HERE/'baseline-asset/fire_station_jrg2.glb').read_bytes()
length=struct.unpack_from('<I',b,12)[0]
doc=json.loads(b[20:20+length]); start=20+length+8
types={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
def acc(index):
    a=doc['accessors'][index]; view=doc['bufferViews'][a['bufferView']]
    dt=np.dtype(types[a['componentType']]); n=widths[a['type']]
    return np.ndarray((a['count'],n),dt,buffer=b,
        offset=start+view.get('byteOffset',0)+a.get('byteOffset',0),
        strides=(view.get('byteStride',n*dt.itemsize),dt.itemsize)).copy()
anchor=json.loads((HERE/'baseline-asset/fire_station_jrg2_meta.json').read_text())['anchor']
camera=next(c for c in json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/control_cameras.json').read_text())['cameras']
            if c['id']=='fire_station_ref7197')
eye=np.array(camera['pos'])[[0,2,1]]
forward=np.array(camera['look_at'])[[0,2,1]]-eye; forward/=np.linalg.norm(forward)
right=np.cross([0,1,0],forward); right/=np.linalg.norm(right)
up=np.cross(forward,right)
textures={name:np.array(Image.open(HERE/f'baseline-asset/T_fire_station_{name}.png'))
          for name in ('BaseColor','MaskMap','Normal')}
rows=[]
for lod in (0,1):
    node=doc['nodes'][lod]
    meshes=[]
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        if doc['materials'][primitive['material']]['name']!='fire_station': continue
        p=acc(primitive['attributes']['POSITION']); p[:,0]*=-1; p+=np.array(anchor)[[0,2,1]]
        uv=acc(primitive['attributes']['TEXCOORD_0']); uv[:,1]=1-uv[:,1]
        triangles=acc(primitive['indices']).ravel().reshape(-1,3)
        meshes.append((p,uv,triangles))
    for label,px,py in (('patch',975,653),('above',975,617),('left',930,653),('lamp',951,657)):
        tan=np.tan(np.deg2rad(camera['fov_deg'])/2)
        ray=forward+right*(2*(px+.5)/2340-1)*tan*2340/1080+up*(1-2*(py+.5)/1080)*tan
        ray/=np.linalg.norm(ray); best=None
        for p,uv,t in meshes:
            v0=p[t[:,0]]; e1=p[t[:,1]]-v0; e2=p[t[:,2]]-v0
            h=np.cross(ray,e2); det=(e1*h).sum(1); good=np.abs(det)>1e-10
            inv=np.divide(1,det,out=np.zeros_like(det),where=good)
            s=eye-v0; u=(s*h).sum(1)*inv; q=np.cross(s,e1)
            v=(q*ray).sum(1)*inv; distance=(e2*q).sum(1)*inv
            good &= (u>=0)&(v>=0)&(u+v<=1)&(distance>0)
            ids=np.flatnonzero(good)
            if not len(ids): continue
            i=ids[np.argmin(distance[ids])]
            tex=uv[t[i,0]]*(1-u[i]-v[i])+uv[t[i,1]]*u[i]+uv[t[i,2]]*v[i]
            if best is None or distance[i]<best['distance']:
                best={'label':label,'lod':lod,'pixel':[px,py],'distance':float(distance[i]),
                    'position':(eye+ray*distance[i]).tolist(),'uv_metres':tex.tolist()}
                for name,image in textures.items():
                    y=int((1-(tex[1]/14)%1)*image.shape[0])%image.shape[0]
                    x=int((tex[0]/14)%1*image.shape[1])%image.shape[1]
                    best[name]=image[y,x].tolist()
        rows.append(best or {'label':label,'lod':lod,'no_hit':True})
(HERE/'wall-uv-probe.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
for row in rows: print(row)
