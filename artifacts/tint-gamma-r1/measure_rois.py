"""ADR0086 fixed screen ROIs. Coordinates are in a 960px-wide view; statistics read full PNG pixels.
These are appearance/exposure comparisons, not measurements of absolute physical albedo.
"""
import csv,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
ROIS=[
 ('asphalt','driver-andersa-to-putry',(450,360,530,410)),
 ('pavers','kwadrat-park-gate',(760,350,850,405)),
 ('fire_plaster','fire-station-ref7197',(445,201,478,228)),
 ('curtain_dock3','stretch-05-docks',(280,185,305,215)),
 ('hall_panel','stretch-05-docks',(210,83,240,94)),
 ('screen_cassette','route-putry-entry-signs',(830,165,915,205)),
 ('bridge_soffit','photo-biezenstwa-ground',(440,225,520,235)),
 ('sky_control','driver-andersa-to-putry',(560,25,720,90)),
]
def measure(stage):
 rows=[]
 for directory in sorted((ROOT/stage).glob('*')):
  if not directory.is_dir():continue
  for name,camera,box in ROIS:
   path=directory/(camera+'.png')
   if not path.exists():continue
   with Image.open(path) as im:
    scale=im.width/960;crop=im.convert('RGB').crop(tuple(round(x*scale) for x in box));a=np.asarray(crop,dtype=float)
   mean=a.mean(axis=(0,1));lum=a@np.array([.2126,.7152,.0722])
   rows.append({'stage':stage,'condition':directory.name,'roi':name,'camera':camera,'roi_960':box,'mean_rgb':mean.tolist(),'mean_srgb':float(mean.mean()),'median_luma':float(np.median(lum)),'p10_luma':float(np.percentile(lum,10)),'p90_luma':float(np.percentile(lum,90)),'clip_250_fraction':float(np.any(a>=250,axis=2).mean())})
 (ROOT/(stage+'-roi.json')).write_text(json.dumps(rows,indent=2)+'\n')
 return rows
if __name__=='__main__':
 for stage in sys.argv[1:] or ['before']:
  for r in measure(stage):print(stage,r['condition'],r['roi'],'/'.join(str(round(x,1)) for x in r['mean_rgb']))
