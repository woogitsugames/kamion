"""Native PNG ROI/stats diagnostics. ROI locations must be checked in the fresh baseline.

Usage: python metrics.py before [after-r1]
No GPU-time/device claim is inferred from renderer counters.
"""
import json
import re
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
# Initial semantic locations from the unchanged r10 camera. Recheck before first measurement.
ROIS={'r10b_black_05':{'door':(980,590,1100,660),'hood_legacy_mixed':(1400,470,1520,525),'hood':(1450,560,1580,630),
                     'road':(1700,940,1850,1020),'sky':(1700,20,1800,90)}}

def measure(path):
    out={}
    for camera,rois in ROIS.items():
        p=path/f'{camera}.png'
        if not p.exists(): continue
        image=Image.open(p).convert('RGB')
        assert image.size==(2340,1080),(str(p),image.size)
        a=np.asarray(image,dtype=float)
        out[camera]={}
        for name,box in rois.items():
            x0,y0,x1,y1=box
            rgb=a[y0:y1,x0:x1]
            lum=rgb@np.array([.2126,.7152,.0722])
            out[camera][name]=dict(box=list(box),rgb_mean=rgb.mean((0,1)).tolist(),
                rgb_median=np.median(rgb.reshape(-1,3),axis=0).tolist(),
                display_luma_mean=float(lum.mean()),display_luma_p05=float(np.percentile(lum,5)),
                display_luma_p95=float(np.percentile(lum,95)),fraction_any250=float(np.any(rgb>=250,axis=2).mean()))
    return out

def stats(path):
    p=path/'stats.txt'
    if not p.exists(): return {}
    result={}
    pattern=r'^  (.+) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k, cells (\d+), forest HLOD cells (\d+)'
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        match=re.match(pattern,line)
        if match:
            result[match[1]]=dict(zip(('draws','instances','triangles_k_rounded','cells','forest_hlod_cells'),map(int,match.groups()[1:])))
    return result

def main():
    conditions=('Low-clear','Low-overcast','High-clear','High-overcast')
    result={'note':'PNG native display RGB/luma; fixed ROI comparison, not linear photometry. Stats CPU estimates with rounded thousands of triangles; no GPU/device proof.','rounds':{}}
    for tag in sys.argv[1:]:
        result['rounds'][tag]={c:dict(roi=measure(ROOT/tag/c),stats=stats(ROOT/tag/c)) for c in conditions}
    if len(sys.argv)>2:
        a,b=sys.argv[1:3]
        result['stats_delta']={}
        for condition in conditions:
            sa=result['rounds'][a][condition]['stats']; sb=result['rounds'][b][condition]['stats']
            assert sa.keys()==sb.keys(),f'Camera registries differ: {condition}'
            delta={k:{f:sb[k][f]-sa[k][f] for f in sa[k]} for k in sa}
            result['stats_delta'][condition]=dict(camera_count=len(delta),per_camera=delta,
                min={f:min((d[f] for d in delta.values()),default=0) for f in ('draws','triangles_k_rounded')},
                max={f:max((d[f] for d in delta.values()),default=0) for f in ('draws','triangles_k_rounded')})
    out=ROOT/('metrics-'+'-vs-'.join(sys.argv[1:])+'.json')
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(out)

if __name__=='__main__': main()
