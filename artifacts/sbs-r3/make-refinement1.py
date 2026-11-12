"""Second SBS probe family: view offsets/pitch for grobin, road-arc offsets for zsolt. Run under heavy."""
from pathlib import Path
import copy,hashlib,json,math,sys
import numpy as np
from shapely.geometry import LineString,Point
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
script_hash=sha(Path(__file__))
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
helper_path=ROOT/'tests/gis/route_corridor.py';helper_hash=sha(helper_path)
sys.path.insert(0,str(ROOT/'tests/gis'));from route_corridor import read_glb,node_triangles,ray_heights
sys.path.insert(0,str(ROOT/'tools/refs'));import sbs_gate3 as sbs
ART=Path(__file__).parent;OUT=ART/'pose-refinement1';REGION=sbs.REGION
world_path=REGION/'generated/world_manifest.json';graph_path=REGION/'roads.graph.json'
camera_path=REGION/'sbs_cameras.json';ref_path=REGION/'sbs_references.json'
world_hash=sha(world_path);graph_hash=sha(graph_path)
source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in (camera_path,ref_path)}
world=read(world_path);baseline=read(ART/'baseline-completed.json')
if baseline.get('world_exit')!=0 or baseline.get('materials_exit')!=0 or world_hash!=baseline['world_manifest_sha256']:raise RuntimeError('Successful completed baseline required')
graph=read(graph_path);cameras=read(camera_path)['cameras'];refs=read(ref_path)['references']
origin=np.array([world['origin_epsg2180']['x'],world['origin_epsg2180']['y']])
edge_ids=['w606396460:5749429982-1847044938','w560802655:1847044938-12620261936','w560802655:12620261936-1946476472']
path_points=[]
for edge_id in edge_ids:
    edge=next(e for e in graph['edges'] if e['id']==edge_id)
    coords=np.array(edge['geometry'],float)-origin
    if path_points and np.linalg.norm(np.array(path_points[-1])-coords[0])>.02:raise RuntimeError('Disconnected authored road path')
    path_points.extend(coords.tolist() if not path_points else coords[1:].tolist())
road=LineString(path_points)
def frame(station):
    if not 0<=station<=road.length:raise ValueError('Outside authored road path')
    p=np.array(road.interpolate(station).coords[0]);a=np.array(road.interpolate(max(0,station-.25)).coords[0]);b=np.array(road.interpolate(min(road.length,station+.25)).coords[0])
    direction=(b-a)/np.linalg.norm(b-a);return p,np.array([-direction[1],direction[0]])
# Thirty bounded attempts; unsafe/missing asphalt cases are retained as rejected metadata, never rendered underground.
settings=[]
settings += [('275528677534382',d,0,h,eye,'view') for d in (-8,-10,-12) for h in (.52,.55) for eye in (1.7,2.2)]
settings += [('837235577143499',d,left,.52,2.2,'view') for d in (-16,-20) for left in (-2,0,2)]
settings += [('3281350541967811',d,left,None,2.2,'road') for d in (-60,-75) for left in (-2,0,2)]
settings += [('297817221966185',d,left,None,2.2,'road') for d in (-60,-75,-90) for left in (0,2)]
assert len(settings)==30
xy=[];prepared=[]
for index,(sid,offset,left,horizon,eye,axis) in enumerate(settings):
    camera=next(c for c in cameras if c['id']==f'sbs-g3-b-{sid}');ref=next(r for r in refs if r['camera']==camera['id'])
    direction=np.array(camera['look_at'])-camera['pos'];horizontal=np.linalg.norm(direction[:2]);heading=math.degrees(math.atan2(direction[0],direction[1]))%360
    pitch=math.degrees(math.atan2(direction[2],horizontal)) if horizon is None else math.degrees(math.atan((2*horizon-1)*math.tan(math.radians(camera['fov_deg']/2))))
    station=road.project(Point(camera['pos'][:2]));centre,left_axis=frame(station)
    old_lateral=float(np.dot(np.array(camera['pos'][:2])-centre,left_axis))
    if axis=='road':
        target_station=station+offset
        centre,left_axis=frame(target_station)
        point=centre+left_axis*(old_lateral+left)
    else:
        unit=direction[:2]/horizontal;point=np.array(camera['pos'][:2])+offset*unit+left*np.array([-unit[1],unit[0]])
        target_station=None
    probe=f'sbs-refine1-{sid}-{index:02d}'
    prepared.append(dict(sid=sid,camera=camera,ref=ref,probe=probe,offset=offset,left=left,horizon=horizon,eye=eye,axis=axis,point=point,heading=heading,pitch=pitch,station=station,target_station=target_station,old_lateral=old_lateral))
    xy.append(point)
# Include the entire chosen road path so every intermediate continuity sample lies in the loaded area.
all_xy=np.vstack([np.array(xy),np.array(path_points)]);lo=all_xy.min(0)-6;hi=all_xy.max(0)+6
triangles=[];loaded=[]
for chunk in world['chunks']:
    b=chunk['bounds_local_m']
    if b['e_max']<lo[0] or b['e_min']>hi[0] or b['n_max']<lo[1] or b['n_min']>hi[1]:continue
    info=chunk['low'];doc,data,binoff=read_glb(ROOT/info['file']);digest=hashlib.sha256(data).hexdigest()
    if digest!=info['sha256']:raise RuntimeError('GLB does not match manifest')
    for node in doc['nodes']:
        if node.get('name')=='road' and any(k in node for k in ('matrix','translation','rotation','scale')):raise RuntimeError('Transformed road node unsupported')
    road_parts=node_triangles(doc,data,binoff,'road')
    if 'road_asphalt' in road_parts:triangles.append(road_parts['road_asphalt'])
    loaded.append({'file':info['file'],'sha256':digest})
if not triangles:raise RuntimeError('No rendered asphalt triangles')
triangles=np.concatenate(triangles);minimum=triangles[:,:,:2].min(1);maximum=triangles[:,:,:2].max(1);height_cache={}
def heights(point):
    key=tuple(np.round(point,4))
    if key not in height_cache:
        keep=np.all(minimum<=point+1e-6,axis=1)&np.all(maximum>=point-1e-6,axis=1)
        z=ray_heights(triangles[keep],*point);height_cache[key]=np.unique(np.round(z[np.isfinite(z)],6)).tolist()
    return height_cache[key]
result=[];rows=[];rejected=[]
for item in prepared:
    c=item['camera'];target=c['pos'][2]-2.2;trace=[];reason=None
    if item['axis']=='road':
        stations=np.linspace(item['station'],item['target_station'],max(2,math.ceil(abs(item['offset'])/2.5)+1))
        for s in stations:
            centre,left_axis=frame(float(s));point=centre+left_axis*(item['old_lateral']+item['left']);levels=heights(point)
            if not levels:reason='No rendered asphalt on road-profile sample';break
            chosen=min(levels,key=lambda z:abs(z-target))
            if abs(chosen-target)>1.0:reason='Surface continuity exceeds1m per <=2.5m step';break
            target=chosen;trace.append({'station_m':float(s),'en':point.tolist(),'levels_u_m':levels,'chosen_u_m':chosen})
    else:
        levels=heights(item['point'])
        if not levels:reason='No rendered asphalt at view-offset point'
        else:
            chosen=min(levels,key=lambda z:abs(z-target))
            if abs(chosen-target)>1.0:reason='Asphalt differs from baseline road level by more than1m'
            else:target=chosen;trace=[{'en':item['point'].tolist(),'levels_u_m':levels,'chosen_u_m':chosen}]
    if reason:
        rejected.append({'probe':item['probe'],'camera':c['id'],'reason':reason,'en':item['point'].tolist()});continue
    photo=ROOT/item['ref'].get('comparison_photo',item['ref']['photo'])
    if sha(photo)!=item['ref']['comparison_sha256']:raise RuntimeError('Photo changed')
    e,n=item['point'];u=target+item['eye'];camera=copy.deepcopy(c);camera['id']=item['probe'];camera['pos']=[round(float(e),4),round(float(n),4),round(u,4)];camera['look_at']=sbs.pose(float(e),float(n),u,item['heading'],item['pitch']);camera['pose_confidence']='C';camera['pose_reason']='Diagnostic refinement only; no production approval';camera['note']='Road-asphalt height with explicit nominal eye; preserved source yaw/FOV; changed pitch only where authored. WORKING_VALUE.'
    actual_h=.5+math.tan(math.radians(item['pitch']))/(2*math.tan(math.radians(c['fov_deg']/2)))
    result.append(camera);r=item['ref'];rows.append({'probe':camera['id'],'base_camera':c['id'],'offset_m':item['offset'],'translation_axis':item['axis'],'left_delta_m':item['left'],'nominal_eye_m':item['eye'],'horizon_y_fraction':actual_h,'photo':photo.relative_to(ROOT).as_posix(),'photo_sha256':r['comparison_sha256'],'author':r['author'],'license':r['license'],'page_url':r['page_url'],'width':1280,'height':round(1280*r['height']/r['width']),'pos':camera['pos'],'look_at':camera['look_at'],'fov_deg':camera['fov_deg'],'road_station_m':item['target_station'],'baseline_road_station_m':item['station'],'baseline_left_of_road_m':item['old_lateral'],'surface_trace':trace})
if not result:raise RuntimeError('All refinement attempts rejected; inspect metadata')
for relative,digest in source_hashes.items():
    if sha(ROOT/relative)!=digest:raise RuntimeError('Production source changed')
if sha(world_path)!=world_hash or sha(graph_path)!=graph_hash or sha(helper_path)!=helper_hash or sha(Path(__file__))!=script_hash:raise RuntimeError('Preparation inputs changed')
for chunk in loaded:
    if sha(ROOT/chunk['file'])!=chunk['sha256']:raise RuntimeError('Loaded GLB changed')
OUT.mkdir(exist_ok=True);sbs.write(OUT/'cameras.json',{'schema':'kamion/sbs-cameras/1','frame':'E,N,absolute U','cameras':result})
sbs.write(OUT/'plan.json',{'diagnostic_only':True,'all_pose_confidence':'C','attempted_count':30,'accepted_for_render_count':len(rows),'rejected':rejected,'preparation_script_sha256':script_hash,'probe_cameras_sha256':sha(OUT/'cameras.json'),'production_source_sha256':source_hashes,'world_manifest_sha256':world_hash,'road_graph_sha256':graph_hash,'helper_sha256':helper_hash,'road_path':{'edge_ids':edge_ids,'local_en':path_points,'length_m':road.length},'verified_low_chunks':loaded,'probes':rows,'note':'Road continuity only selects diagnostic model height, not photographic pose. Every candidate remains C; no production writes.'})
print(f'Prepared {len(rows)}/30 C refinements; rejected{len(rejected)}; actual Low asphalt sampled; production sources unchanged')
