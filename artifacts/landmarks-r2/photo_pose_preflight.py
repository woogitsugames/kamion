"""Low-cost coordinate/FOV calculation from the CC0 photo metadata, no world build."""
from pathlib import Path
import json
import math
import numpy as np
from pyproj import Transformer

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
lat,lon=53.158496,23.153233
e,n=Transformer.from_crs(4326,2180,always_xy=True).transform(lon,lat)
region=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/terrain.json').read_text())
enc=region['encoding']
q=np.fromfile(ROOT/enc['file'],dtype='<u2').reshape(region['samples'])
x,y=e-region['bbox'][0],region['bbox'][3]-n
i,j=int(x),int(y); dx,dy=x-i,y-j
z=float((q[j,i]*(1-dx)*(1-dy)+q[j,i+1]*dx*(1-dy)+q[j+1,i]*(1-dx)*dy+q[j+1,i+1]*dx*dy)*enc['scale_m_per_unit']+enc['offset_m'])
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
origin=manifest['origin_epsg2180']
print('Origin:',origin)
oe,on=(origin['x'],origin['y']) if isinstance(origin,dict) else origin[:2]
hfov=2*math.atan(36/(2*38))
vfov_qa=2*math.atan(math.tan(hfov/2)/(2340/1080))
result={'source_page':'https://commons.wikimedia.org/wiki/File:7204_May_2021_in_Bia%C5%82ystok.jpg',
        'metadata_gps_lat_lon':[lat,lon],'epsg2180':[e,n],'local_EN':[e-oe,n-on],
        'raw_NMT_ground_EVFR2007_m':z,'eye_height_WORKING_VALUE_m':1.65,
        'source_sensor_WORKING_VALUE_mm':[36,24],'source_35mm_focal_metadata_mm':38,
        'horizontal_fov_deg':math.degrees(hfov),'qa_vertical_fov_for_same_horizontal_deg':math.degrees(vfov_qa),
        'heading_and_pitch_status':'UNVERIFIED; must infer and inspect before using a photo-matched claim'}
(OUT/'photo7204-pose-preflight.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
