from pathlib import Path
import importlib.util,json,hashlib
ROOT=Path.cwd();ART=ROOT/'artifacts/car-paint-r1';spec=importlib.util.spec_from_file_location('metrics',ART/'metrics.py');metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
conditions=['Low-clear','Low-overcast','High-clear','High-overcast'];contract=json.loads((ART/'r4-baseline-camera-contract.json').read_text());ids=set(contract['expected_camera_ids']);assert len(ids)==92
fields=['cameraParents','vehicleHierarchy','regionRoots','view','projection','pixelRect','targetWidth','targetHeight','pixelWidth','pixelHeight','fov','aspect','near','far','pipelineScale','upscalingFilter','fsrSharpness','fsrOverride','post','glassFast','giRect','regionState']
carids={c['id'] for c in json.loads((ART/'car_cams.json').read_text())['cameras']};route59=set(metrics.stats(ART/'before'/'Low-clear'))-carids;assert len(route59)==59
allrows=[];budget={};rois={}
for cond in conditions:
 before=ART/'r4-before'/cond;after=ART/'r4-final'/cond
 assert {p.stem for p in after.glob('*.png')}==ids=={p.stem for p in before.glob('*.png')}
 sa=metrics.stats(before);sb=metrics.stats(after);assert set(sa)==set(sb)==ids
 delta={id:{key:sb[id][key]-sa[id][key] for key in sa[id]} for id in sorted(ids)}
 budget[cond]=dict(camera_count=92,route59=sorted(route59),all92_min={key:min(d[key] for d in delta.values()) for key in ('total_draws_est','total_triangles_k_rounded')},all92_max={key:max(d[key] for d in delta.values()) for key in ('total_draws_est','total_triangles_k_rounded')},route59_min={key:min(delta[id][key] for id in route59) for key in ('total_draws_est','total_triangles_k_rounded')},route59_max={key:max(delta[id][key] for id in route59) for key in ('total_draws_est','total_triangles_k_rounded')},per_camera=delta,stats_byte_exact=(before/'stats.txt').read_bytes()==(after/'stats.txt').read_bytes())
 rois[cond]=dict(before=metrics.measure(before),after=metrics.measure(after))
 for camera in sorted(ids):
  b=json.loads((before/'poses'/f'{camera}-begin.json').read_text());a=json.loads((after/'poses'/f'{camera}-begin.json').read_text());end=json.loads((after/'poses'/f'{camera}-end.json').read_text())
  diff=[f for f in fields if a[f]!=b[f]];within=[f for f in fields if a[f]!=end[f]];assert not diff and not within,(cond,camera,diff,within)
  assert len(a['plateMaterials'])==1;p=a['plateMaterials'][0]
  assert p['localCorners'] and p['version']==1 and not p['motionVectors'] and p['shader']=='Kamion/World Car Plate'
  allrows.append(dict(condition=cond,camera=camera,pose_diff=diff,within_frame_diff=within,plate_keyword=True,motion_vectors=False))
 assert budget[cond]['all92_max']['total_draws_est']<=0 and budget[cond]['all92_max']['total_triangles_k_rounded']<=0
out=dict(frames=368,paired_historical_r3_frames=368,camera_registry_exact=92,all_camera_vehicle_region_projection_pipeline_fields_exact=True,all_loaded_plate_bindings_enabled_motion_disabled=True,rows=allrows,note='Actual packet/state and CPU culling estimates. PNG output dimensions do not establish internal pipeline resolution. No phone/GPU-time claim.')
(ART/'r4-final-validation.json').write_text(json.dumps(out,indent=2)+'\n');(ART/'r4-final-budget.json').write_text(json.dumps(budget,indent=2)+'\n');(ART/'r4-final-owner-rois.json').write_text(json.dumps(rois,indent=2)+'\n')
print('PASS368 paired poses/bindings;4x92 CPU estimates nonincrease')
for cond,b in budget.items():print(cond,b['all92_min'],b['all92_max'],'byteexact',b['stats_byte_exact'])
for cond,r in rois.items():print(cond,{name:(r['before']['r10b_black_05'][name]['display_luma_mean'],r['after']['r10b_black_05'][name]['display_luma_mean']) for name in ['door','hood']})
