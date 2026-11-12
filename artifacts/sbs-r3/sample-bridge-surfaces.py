"""Read-only road surface samples for SBS bridge hypotheses. Run after r3 baseline, under heavy."""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/gis'))
from route_corridor import read_glb,node_triangles,ray_heights
ART=Path(__file__).parent
REGION=ROOT/'Data/Regions/bialystok-industrial-c'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest_path=REGION/'generated/world_manifest.json'
baseline=read(ART/'baseline-completed.json')
manifest_hash=sha(manifest_path)
if baseline['world_exit']!=0 or manifest_hash!=baseline['world_manifest_sha256']:
    raise RuntimeError('Need matching completed r3 baseline')
# Check the helper coordinate and miss contracts before reading real geometry.
test=np.array([[[0.,0.,0.],[2.,0.,2.],[0.,2.,4.]]])
assert abs(ray_heights(test,.25,.25)[0]-.75)<1e-9
assert np.isnan(ray_heights(test,3.,3.)[0])
manifest=read(manifest_path)
camera_path=REGION/'sbs_cameras.json';camera_hash=sha(camera_path)
cameras=read(camera_path)['cameras'];points=[]
for sid, offsets, nominal_eye in [('494288258686575',[-30,-15,0,15,30],1.7),
                                 ('1801374876712141',[0,10,15,20,30],2.2)]:
    c=next(c for c in cameras if c['id']==f'sbs-g3-b-{sid}')
    dx,dn=np.array(c['look_at'][:2])-c['pos'][:2];length=math.hypot(dx,dn)
    lateral_offsets=(-4,0,4) if sid.startswith('494') else (0,)
    for along in offsets:
        for lateral in lateral_offsets:
            e=c['pos'][0]+along*dx/length-lateral*dn/length
            n=c['pos'][1]+along*dn/length+lateral*dx/length
            points.append({'camera':c['id'],'along_view_m':along,'left_m':lateral,
                           'e':float(e),'n':float(n),'baseline_road_target_u':c['pos'][2]-nominal_eye,
                           'nominal_eye_m':nominal_eye,'hits':[]})
intrinsics_path=REGION/'sbs_intrinsics.json'
meta=read(intrinsics_path)['images']['494288258686575']
lon,lat=meta['geometry']['coordinates']
x,y=Transformer.from_crs(4326,2180,always_xy=True).transform(lon,lat)
origin=manifest['origin_epsg2180']
points.append({'camera':'sbs-g3-b-494288258686575','hypothesis':'original GPS, not SfM',
    'e':x-origin['x'],'n':y-origin['y'],'baseline_road_target_u':141.888-1.7,
    'nominal_eye_m':1.7,'hits':[]})
loaded=[]
for chunk in manifest['chunks']:
    b=chunk['bounds_local_m']
    relevant=[p for p in points if b['e_min']-1e-6<=p['e']<=b['e_max']+1e-6 and b['n_min']-1e-6<=p['n']<=b['n_max']+1e-6]
    if not relevant:continue
    info=chunk['low'];path=ROOT/info['file'];doc,data,offset=read_glb(path)
    digest=hashlib.sha256(data).hexdigest()
    if digest!=info['sha256']:raise RuntimeError(f'GLB does not match manifest: {path.name}')
    loaded.append({'file':info['file'],'sha256':digest})
    for node_name,allowed in [('road',{'road_asphalt'}),('road_collision',{'collision_asphalt'})]:
        for node in doc['nodes']:
            if node.get('name')==node_name and any(k in node for k in ('matrix','translation','rotation','scale')):
                raise RuntimeError('Unsupported transformed world node')
        for material,tris in node_triangles(doc,data,offset,node_name).items():
            if material not in allowed:continue
            for p in relevant:
                heights=ray_heights(tris,p['e'],p['n'])
                heights=np.unique(np.round(heights[np.isfinite(heights)],6))
                for height in heights:
                    p['hits'].append({'u_m':float(height),'node':node_name,'material':material,'chunk':chunk['id']})
for p in points:
    elevations=sorted({h['u_m'] for h in p['hits']})
    p['road_surface_u_m']=elevations
    nearest=min(elevations,key=lambda z:abs(z-p['baseline_road_target_u'])) if elevations else None
    p['nearest_to_old_road_target_u']=nearest
    p['target_difference_m']=None if nearest is None else nearest-p['baseline_road_target_u']
    p['note']='No automatic pose choice. Multiple levels may exist; closest to old height is a diagnostic, not proof of the photographed deck.'
if sha(manifest_path)!=manifest_hash or sha(camera_path)!=camera_hash:
    raise RuntimeError('Inputs changed during surface diagnostic')
result={'world_manifest_sha256':manifest_hash,'production_cameras_sha256':camera_hash,
        'intrinsics_sha256':sha(intrinsics_path),'helper_sha256':sha(ROOT/'tests/gis/route_corridor.py'),
        'coordinate_contract':'Exporter glTF (-E,U,N), helper converts to local(E,N,absolute U).',
        'scope':'Actual matching Low GLB road_asphalt and collision_asphalt only. No terrain, kerb, photo pose approval or world write.',
        'sample_count':len(points),'verified_chunks':loaded,'samples':points}
(ART/'bridge-surface-survey.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(f'Sampled {len(points)} hypotheses in {len(loaded)} matching Low chunks; production sources unchanged')
