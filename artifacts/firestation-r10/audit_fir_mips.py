"""CPU alpha-filter diagnostic only, not Unity's coverage-preserving/ASTC mip chain."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'shape-candidates'
old=Image.open(ROOT/'art-source/world/textures/fire_station_alpha.png').getchannel('A')
new=Image.open(OUT/'fire_station_alpha-fir-proxy.png').getchannel('A')
layout=json.loads((ROOT/'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json').read_text())['alpha']
proof=json.loads((OUT/'fir-alpha-proxy-proof.json').read_text());region=proof['candidate_atlas_region_uv']
def mask(box,w,h):
    u=(np.arange(w)+.5)/w;v=1-(np.arange(h)+.5)/h
    x0,v0,x1,v1=box
    return (u[None,:]>=x0)&(u[None,:]<x1)&(v[:,None]>=v0)&(v[:,None]<v1)
rows=[]
for label,filter in [('BOX',Image.Resampling.BOX),('LANCZOS',Image.Resampling.LANCZOS)]:
    for level in range(8):
        size=(old.width>>level,old.height>>level)
        a=np.array(old.resize(size,filter),dtype=float)/255;b=np.array(new.resize(size,filter),dtype=float)/255
        m=mask(region,*size);cell=b[m]
        row={'filter':label,'mip':level,'size':size,'new_cell_samples':int(m.sum()),
             'new_cell_alpha_mean':float(cell.mean()) if len(cell) else None,
             'new_cell_alpha_max':float(cell.max()) if len(cell) else None,
             'new_cell_covered_samples_cutoff_0_5':int(np.sum(cell>=.5)),
             'new_cell_coverage_cutoff_0_5':float(np.mean(cell>=.5)) if len(cell) else None,
             'old_regions':{}}
        for name in ('fence_bay','gate_bay','swatch_blue','lettering','number'):
            r=layout[name];mm=mask([r['u'][0],r['v'][0],r['u'][1],r['v'][1]],*size)
            delta=np.abs(a[mm]-b[mm])
            row['old_regions'][name]={'samples':int(mm.sum()),'alpha_changed_samples':int(np.sum(delta>1e-9)),
                                     'max_alpha_difference':float(delta.max()) if len(delta) else None}
        rows.append(row)
report={'status':'CPU_FILTER_DIAGNOSTIC_ONLY_NOT_UNITY_COVERAGE_PRESERVING_OR_ASTC_MIPS',
        'global_alpha_import_settings':'UNCHANGED; no production PNG/settings edited',
        'limitations':['Global Unity alpha-coverage preservation may rescale alpha in old regions; CPU table cannot prove actual imported mip parity.',
                       'New cell needle survival is a risk indicator, not temporal shimmer measurement or runtime silhouette PASS.'],
        'rows':rows}
(OUT/'fir-mip-diagnostic.json').write_text(json.dumps(report,indent=2))
for row in rows:
    print(row['filter'],row['mip'],'coverage',row['new_cell_coverage_cutoff_0_5'],'max',row['new_cell_alpha_max'],
          'old_alpha_changed',sum(x['alpha_changed_samples'] for x in row['old_regions'].values()))
