"""Offline stronger normal variants, heavy lease required; no source/game writes."""
import hashlib, importlib.util, json
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('cab_cc0', ROOT/'tools/blender/truck/interior/cc0_leather.py')
cab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cab)
old = json.loads((HERE/'material-prep/verification.json').read_text(encoding='utf-8'))
if not old['status'].startswith('PASS:') or not all(r['matches'] for r in old['baseline']):
    raise RuntimeError('Missing verified baseline reproduction')
source = ROOT/'art-source/truck/interior/export/textures'
config = json.loads(cab.CONFIG.read_text(encoding='utf-8-sig'))
records=[]
for sigma, tag in ((.3,'hp03'),(.6,'hp06')):
    config['plastic']['normal_highpass_mm']=sigma
    config_path=HERE/f'material-prep/candidate-{tag}.json'
    config_path.write_text(json.dumps(config,indent=2),encoding='utf-8')
    output=HERE/f'material-prep/candidate-{tag}'
    args,_=cab.config_args(output,source/'High/T_Cab_Plastic_Detail.png',config_path,profile='plastic')
    cab.prepare(args)
    for tier in ('High','Medium','Low'):
        detail=output/tier/'T_Cab_Plastic_Detail.png'
        expected=next(r['original_sha256'] for r in old['baseline'] if r['file']==f'{tier}/T_Cab_Plastic_Detail.png')
        if hashlib.sha256(detail.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Detail/alpha changed')
        normal=output/tier/'T_Cab_Plastic_Normal.png'
        values=np.asarray(Image.open(normal).convert('RGB'),dtype=np.float32)/255*2-1
        error=float(np.max(np.abs(np.linalg.norm(values,axis=-1)-1)))
        min_z=float(values[...,2].min())
        if error>.015 or min_z<=0: raise RuntimeError('Invalid normal')
        records.append(dict(variant=tag,sigma_mm=sigma,tier=tier,detail_identical=True,
                            normal_sha256=hashlib.sha256(normal.read_bytes()).hexdigest(),
                            max_unit_length_error_8bit=error,min_normal_z=min_z))
(HERE/'material-prep/fine-verification.json').write_text(json.dumps(dict(status='PASS',scope='Offline only; requires game-image review',working_values=True,rows=records),indent=2),encoding='utf-8')
print('CAB_MATERIAL_FINE_RESULT: OK')
