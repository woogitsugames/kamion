"""Prepare 18 C-only gantry pose hypotheses after the r3 world baseline. Run under heavy."""
from pathlib import Path
import copy, hashlib, json, math, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/refs'))
import sbs_gate3 as sbs
OUT=Path(__file__).with_name('gantry-probes')
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline=sbs.read(Path(__file__).with_name('baseline-completed.json'))
world=sbs.REGION/'generated/world_manifest.json'
if baseline['world_exit'] != 0 or sha(world) != baseline['world_manifest_sha256']:
    raise RuntimeError('Need the completed matching r3 world before preparing probes')
camera_path=sbs.REGION/'sbs_cameras.json'; refs_path=sbs.REGION/'sbs_references.json'
source_hashes={str(p.relative_to(ROOT)):sha(p) for p in (camera_path,refs_path)}
cameras=sbs.read(camera_path)['cameras']; refs=sbs.read(refs_path)['references']
origin=sbs.read(world)['origin_epsg2180']; ground=sbs.ground_sampler()
variants={'837235577143499':[0,-12,-16,-20,-28],
          '275528677534382':[0,-12,-16,-20,-28],
          '3281350541967811':[0,-30,-45,-60],
          '297817221966185':[0,-30,-45,-60]}
result=[]; plan=[]
for sid, offsets in variants.items():
    original=next(c for c in cameras if c['id']==f'sbs-g3-b-{sid}')
    ref=next(r for r in refs if r['camera']==original['id'])
    photo=ROOT/ref.get('comparison_photo',ref['photo'])
    if sha(photo)!=ref['comparison_sha256']:
        raise RuntimeError(f'Comparison photo changed: {sid}')
    dx,dn,du=[a-b for a,b in zip(original['look_at'],original['pos'])]
    horizontal=math.hypot(dx,dn)
    for offset in offsets:
        c=copy.deepcopy(original)
        c['id']=f'sbs-probe-gantry-{sid}-b{abs(offset):03d}'
        if offset:
            e=original['pos'][0]+offset*dx/horizontal
            n=original['pos'][1]+offset*dn/horizontal
            u=ground(e+origin['x'],n+origin['y'])+2.2
            c['pos']=[round(e,4),round(n,4),round(u,4)]
            c['look_at']=[round(e+dx,4),round(n+dn,4),round(u+du,4)]
        c['pose_confidence']='C';c['pose_reason']='Diagnostic hypothesis, not a production pose'
        c['note']='Longitudinal offset along original grid view, unchanged yaw/FOV/pitch; NMT+2.2m on ground road, all WORKING_VALUE.'
        result.append(c)
        plan.append({'probe':c['id'],'base_camera':original['id'],'offset_along_view_m':offset,
                     'photo':photo.relative_to(ROOT).as_posix(),
                     'photo_sha256':ref['comparison_sha256'],'author':ref['author'],
                     'license':ref['license'],'page_url':ref['page_url'],
                     'width':1280,'height':round(1280*ref['height']/ref['width']),
                     'pos':c['pos'],'look_at':c['look_at'],'fov_deg':c['fov_deg'],
                     'eye_height_note':'Baseline zero preserves exact original camera; shifted variants use NMT+2.2m. No bridge cameras in this batch.'})
assert len(result)==18 and len({c['id'] for c in result})==18
for relative,expected in source_hashes.items():
    if sha(ROOT/relative)!=expected: raise RuntimeError('Production source changed')
OUT.mkdir(exist_ok=True)
sbs.write(OUT/'cameras.json',{'schema':'kamion/sbs-cameras/1','frame':'E,N,absolute U','cameras':result})
sbs.write(OUT/'plan.json',{'diagnostic_only':True,'all_pose_confidence':'C','baseline':baseline,
    'production_source_sha256':source_hashes,'world_manifest_sha256':sha(world),'probes':plan,
    'acceptance':'Portal plus independent durable road corner; visual and independent review before any production pose. Offsets are hypotheses, no automatic promotion.'})
print('Prepared 18 C-only probes; production sources unchanged')

