"""Same-policy receiver comparison with a separate realtime-off causal reference."""
import json
from pathlib import Path
from PIL import Image
import numpy as np
root=Path(__file__).parent/'shadow'
def load(name):return np.asarray(Image.open(root/name/'clear/stretch-05-docks.png').convert('RGB'),float)
control=load('component-control');candidate=load('glass-kp-normal-08');no_shadow=load('component-realtime-off')
weights=np.array([.2126,.7152,.0722])
rois={'frame_received_shadow':(55,231,63,240),'pane_interior':(70,231,90,240),'broad_triangle':(105,225,140,240),
      'trailer_contact':(50,650,1000,950)}
result={'condition':'Medium clear; same default curve/pipeline; only explicit kp receiver bias differs', 'working_value_m':.08,'rois':{}}
for name,(x0,y0,x1,y1) in rois.items():
    c=control[y0:y1,x0:x1];a=candidate[y0:y1,x0:x1];n=no_shadow[y0:y1,x0:x1]
    result['rois'][name]={'rect_original_px':[x0,y0,x1,y1],
        'control_luma':float((c@weights).mean()),'candidate_luma':float((a@weights).mean()),'realtime_off_luma':float((n@weights).mean()),
        'candidate_received_shadow_depth_vs_realtime_off':float(((n-a)@weights).mean()),
        'candidate_vs_control_absmean_rgb':float(np.abs(a-c).mean()),'candidate_vs_control_absmax_rgb':float(np.abs(a-c).max())}
(root/'glass-acceptance-metrics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
