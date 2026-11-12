"""Fifteen bounded C controls on the refreshed world. Execute only under heavy."""
from pathlib import Path
import copy,hashlib,json,math,sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ART=Path(__file__).parent;OUT=ART/'controlled-poses'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
REGION=ROOT/'Data/Regions/bialystok-industrial-c'
paths={'world':REGION/'generated/world_manifest.json','materials':ROOT/'art-source/world/materials/materials_spec.json',
       'cameras':REGION/'sbs_cameras.json','references':REGION/'sbs_references.json',
       'road_graph':REGION/'roads.graph.json','helper':ROOT/'tests/gis/route_corridor.py',
       'meshing':ROOT/'tools/worldgen/roads/meshing.py','script':Path(__file__).resolve(),
       'prior_plan':ROOT/'artifacts/sbs-r3/pose-refinement1/plan.json'}
bindings={key:sha(path) for key,path in paths.items()}
baseline=read(ART/'baseline-completed.json')
if baseline.get('world_exit')!=0 or baseline.get('materials_exit')!=0:raise RuntimeError('Completed successful r4 baseline required')
if baseline.get('fallback_true') is not False:raise RuntimeError('Baseline must explicitly prove no fallback')
if bindings['world']!=baseline['world_manifest_sha256'] or bindings['materials']!=baseline['materials_spec_sha256']:
    raise RuntimeError('Baseline bytes changed')
world=read(paths['world']);prior=read(paths['prior_plan'])
old_world=read(ROOT/'artifacts/sbs-r3/evidence/inputs/world_manifest.json')
if world['origin_epsg2180']!=old_world['origin_epsg2180']:raise RuntimeError('Local coordinate origin changed')
for filename,key in [('sbs_cameras.json','cameras'),('sbs_references.json','references')]:
    relative='Data/Regions/bialystok-industrial-c/'+filename
    if prior['production_source_sha256'][relative]!=bindings[key]:raise RuntimeError('Production pose/reference changed; rebase diagnostic recipe')
sys.path.insert(0,str(ROOT/'tests/gis'))
from route_corridor import read_glb,node_triangles,ray_heights
sys.path.insert(0,str(ROOT/'tools/refs'))
import sbs_gate3 as sbs
test=np.array([[[0.,0.,0.],[2.,0.,2.],[0.,2.,4.]]])
assert abs(ray_heights(test,.25,.25)[0]-.75)<1e-9 and np.isnan(ray_heights(test,3.,3.)[0])
cameras={c['id']:c for c in read(paths['cameras'])['cameras']}
refs={r['camera']:r for r in read(paths['references'])['references']}
settings=[]


def add(sid,prior_index,horizons,eye,translations=(0.,)):
    camera=copy.deepcopy(cameras['sbs-g3-b-'+sid])
    previous=None
    if prior_index is not None:
        previous=next(p for p in prior['probes'] if p['probe']==f'sbs-refine1-{sid}-{prior_index:02d}')
        for key in ('pos','look_at','fov_deg'):camera[key]=previous[key]
    for translation in translations:
        for horizon in horizons:
            settings.append({'sid':sid,'camera':copy.deepcopy(camera),'prior_probe':previous['probe'] if previous else None,
                             'horizon':horizon,'eye':eye,'translation':translation})


add('3281350541967811',21,(None,.74,.77),2.2)
add('297817221966185',26,(None,.74,.77),2.2)
add('275528677534382',4,(None,),1.7)
add('275528677534382',4,(.55,),1.7,(1.,))  # -10m control -> -9m hypothesis; original view axis.
add('837235577143499',12,(None,),2.2)
add('1801374876712141',None,(None,.54,.57),2.2)
add('494288258686575',None,(None,.72,.75),1.7)
assert len(settings)==15
for index,item in enumerate(settings):
    c=item['camera'];direction=np.array(c['look_at'],float)-c['pos']
    unit=direction[:2]/np.linalg.norm(direction[:2])
    item.update(probe=f'sbs-r4pose-{item["sid"]}-{index:02d}',unit=unit,
                point=np.array(c['pos'][:2],float)+item['translation']*unit,
                heading=math.degrees(math.atan2(direction[0],direction[1]))%360,
                pitch=math.degrees(math.atan2(direction[2],np.linalg.norm(direction[:2]))))
points=np.array([p for item in settings for p in (item['camera']['pos'][:2],item['point'])])
lo=points.min(0)-3;hi=points.max(0)+3
carriageway={'road_asphalt','road_asphalt_new','road_concrete','road_paving','road_sett','road_gravel'}
layers=[];loaded=[]
for chunk in world['chunks']:
    b=chunk['bounds_local_m']
    if b['e_max']<lo[0] or b['e_min']>hi[0] or b['n_max']<lo[1] or b['n_min']>hi[1]:continue
    info=chunk['low'];doc,data,offset=read_glb(ROOT/info['file'])
    if hashlib.sha256(data).hexdigest()!=info['sha256']:raise RuntimeError('GLB differs from manifest')
    loaded.append({'file':info['file'],'sha256':info['sha256']})
    for node_name in ('road','bridge','road_collision'):
        for node in doc['nodes']:
            if node.get('name')==node_name and any(k in node for k in ('matrix','translation','rotation','scale')):
                raise RuntimeError('Transformed road/bridge node unsupported')
        for material,triangles in node_triangles(doc,data,offset,node_name).items():
            layers.append({'node':node_name,'material':material,'triangles':triangles,
                           'minimum':triangles[:,:,:2].min(1),'maximum':triangles[:,:,:2].max(1),
                           'chunk':Path(info['file']).stem,'visible_carriageway':node_name in ('road','bridge') and material in carriageway})
if not layers:raise RuntimeError('No source geometry loaded')
hit_cache={}


def hits(point):
    key=tuple(np.round(point,4))
    if key not in hit_cache:
        result=[]
        for layer in layers:
            keep=np.all(layer['minimum']<=point+1e-6,axis=1)&np.all(layer['maximum']>=point-1e-6,axis=1)
            values=ray_heights(layer['triangles'][keep],*point)
            for value in np.unique(np.round(values[np.isfinite(values)],6)):
                result.append({'u_m':float(value),'node':layer['node'],'material':layer['material'],
                               'chunk':layer['chunk'],'visible_carriageway':layer['visible_carriageway']})
        hit_cache[key]=result
    return hit_cache[key]


result=[];rows=[];rejected=[]
for item in settings:
    camera=item['camera'];target=camera['pos'][2]-item['eye'];trace=[];reason=None;chosen=None
    count=max(1,math.ceil(abs(item['translation'])/.5))
    for fraction in np.linspace(0,1,count+1):
        point=np.array(camera['pos'][:2])+item['translation']*fraction*item['unit']
        observed=hits(point)
        candidates=[h for h in observed if h['visible_carriageway'] and abs(h['u_m']-target)<=1.]
        trace.append({'en':point.tolist(),'hits':observed})
        if not candidates:reason='No matching visible carriageway; collision/terrain is not a fallback';break
        levels=sorted({round(h['u_m'],2) for h in candidates})
        if levels[-1]-levels[0]>.15:reason='Ambiguous visible carriageway levels';break
        chosen=min(candidates,key=lambda h:abs(h['u_m']-target))
        if trace[:-1] and abs(chosen['u_m']-target)>.3:reason='Visible surface discontinuity over 0.5m sample';break
        target=chosen['u_m'];trace[-1]['selected']=chosen
    if reason:
        rejected.append({'probe':item['probe'],'base_camera':'sbs-g3-b-'+item['sid'],'reason':reason,'surface_trace':trace})
        continue
    pitch=item['pitch'] if item['horizon'] is None else math.degrees(math.atan((2*item['horizon']-1)*math.tan(math.radians(camera['fov_deg']/2))))
    horizon=.5+math.tan(math.radians(pitch))/(2*math.tan(math.radians(camera['fov_deg']/2)))
    e,n=item['point'];u=target+item['eye']
    new=copy.deepcopy(camera);new['id']=item['probe'];new['pos']=[round(float(e),4),round(float(n),4),round(u,4)]
    new['look_at']=sbs.pose(float(e),float(n),u,item['heading'],pitch)
    new['pose_confidence']='C';new['pose_reason']='Controlled diagnostic only; no production approval'
    new['note']='Visible road/bridge carriageway, nominal eye and authored pitch WORKING_VALUE; no collision/terrain fallback.'
    ref=refs['sbs-g3-b-'+item['sid']];photo=ROOT/ref.get('comparison_photo',ref['photo'])
    if sha(photo)!=ref['comparison_sha256']:raise RuntimeError('Comparison photo changed')
    result.append(new)
    rows.append({'probe':new['id'],'base_camera':ref['camera'],'prior_probe':item['prior_probe'],
                 'photo':photo.relative_to(ROOT).as_posix(),'photo_sha256':ref['comparison_sha256'],
                 'author':ref['author'],'license':ref['license'],'page_url':ref['page_url'],
                 'width':1280,'height':round(1280*ref['height']/ref['width']),
                 'translation_axis':'view','offset_m':item['translation'],'left_delta_m':0,
                 'nominal_eye_m':item['eye'],'horizon_y_fraction':horizon,'pos':new['pos'],'look_at':new['look_at'],
                 'fov_deg':new['fov_deg'],'surface_trace':trace,'selected_surface':chosen,
                 'u_delta_from_source_m':round(new['pos'][2]-camera['pos'][2],6),'control':item['horizon'] is None})
for key,path in paths.items():
    if sha(path)!=bindings[key]:raise RuntimeError('Preparation input changed: '+key)
for chunk in loaded:
    if sha(ROOT/chunk['file'])!=chunk['sha256']:raise RuntimeError('Loaded mesh changed')
OUT.mkdir(exist_ok=True)
sbs.write(OUT/'cameras.json',{'schema':'kamion/sbs-cameras/1','frame':'E,N,absolute U','cameras':result})
sbs.write(OUT/'plan.json',{'diagnostic_only':True,'all_pose_confidence':'C','attempted_count':15,
    'accepted_for_render_count':len(rows),'probes':rows,'rejected':rejected,
    'world_manifest_sha256':bindings['world'],'materials_spec_sha256':bindings['materials'],
    'road_graph_sha256':bindings['road_graph'],'probe_cameras_sha256':sha(OUT/'cameras.json'),
    'production_source_sha256':{paths[k].relative_to(ROOT).as_posix():bindings[k] for k in ('cameras','references')},
    'preparation_sources_sha256':{paths[k].relative_to(ROOT).as_posix():v for k,v in bindings.items()},
    'verified_low_chunks':loaded,'note':'C only. Controls and pitch variants use the same refreshed visible surface at fixed XY. Bridge node is sampled separately from collision.'})
if not result:raise RuntimeError('All hypotheses rejected; cameras and rejection plan preserved for inspection')
print(f'Prepared {len(rows)}/15 C controls; rejected {len(rejected)}; visible road+bridge sampled, production unchanged')
