import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
phase=sys.argv[1]
rois={'left_upper':(1139,589,1166,610),'left_lower':(1139,669,1166,694),
      'right_upper':(1275,590,1298,610),'right_lower':(1275,670,1298,692)}
rows=[]
for condition in ('Low-overcast','Low-clear','High-overcast','High-clear'):
    for stage in ('before',phase):
        a=np.array(Image.open(ROOT/stage/condition/'fire-station-ref7197.png').convert('RGB'))
        values={}
        for name,(x0,y0,x1,y1) in rois.items():
            pixels=a[y0:y1,x0:x1]
            values[name]={'Y_p50':float(np.median(pixels@np.array([.2126,.7152,.0722]))),
                'RGB_p50':np.median(pixels,axis=(0,1)).tolist()}
        rows.append({'condition':condition,'stage':stage,'values':values})
        print(condition,stage, {k:round(v['Y_p50'],2) for k,v in values.items()})
(ROOT/f'glass-{phase}.json').write_text(json.dumps({'ROIs_native':rois,'rows':rows},indent=2),encoding='utf-8')
