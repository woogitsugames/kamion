import json
from pathlib import Path
import numpy as np
from PIL import Image
from measure import measure

root=Path(__file__).parent
result={'validated_engine_sha':'9e7e0b45','measurements':{}}
for phase in ['before','after']:
    result['measurements'][phase]={}
    for condition in ['Low-clear','Low-overcast','High-clear','High-overcast']:
        d=root/phase/condition
        value=measure(d)
        (d/'measurements.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
        result['measurements'][phase][condition]=value
(root/'final-metrics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')

# Real bridge source centre, normal to its long axis; map is north-up, 1m texels.
repo=root.parents[1]
bridge=json.loads((repo/'Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_biezenstwa.spec.json').read_text())
bake=json.loads((repo/'artifacts/bake-r8/maps/bialystok-industrial-c_bake.json').read_text())
image=np.asarray(Image.open(repo/'artifacts/bake-r8/maps/bialystok-industrial-c_vis.png').convert('L'),float)/255
origin=np.array(bake['origin_local']);centre=np.array(bridge['centre'][:2]);normal=np.array([.475,.88])
points=[]
for offset in [-30,0,10,30]:
    point=centre+normal*offset;xy=((point-origin)/bake['texel_m']).astype(int)
    vis=float(image[image.shape[0]-1-xy[1],xy[0]])
    points.append({'offset_m':offset,'local_EN':point.round(3).tolist(),'sky_visibility':vis,
                   'ambient_factor_at_ground_model':vis+(1-vis)*.3})
gi={'source':'fresh canonical WorldSkyBake output; no new AO algorithm claimed','texel_m':bake['texel_m'],
    'points':points,'confidence':bridge['confidence'],'ambient_model':'WorldGI bounce0.3, ground/up-facing receiver; runtime screenshots separately reviewed'}
(root/'bridge-ambient-proof.json').write_text(json.dumps(gi,indent=2),encoding='utf-8')
for condition in result['measurements']['after']:
    a=result['measurements']['before'][condition];b=result['measurements']['after'][condition]
    print(condition,'asphalt',a['driver-andersa-to-putry']['asphalt_near']['rgb_mean'],'->',b['driver-andersa-to-putry']['asphalt_near']['rgb_mean'],
          'gable',a['r10_house_2']['sunlit_gable']['rgb_mean'],'->',b['r10_house_2']['sunlit_gable']['rgb_mean'],
          'sky hf3',a['r10_block_3']['sky']['hf_rms_srgb_levels']['3'],'->',b['r10_block_3']['sky']['hf_rms_srgb_levels']['3'])
