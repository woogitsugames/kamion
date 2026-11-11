"""Source/serialized-material diagnostic only; no render or production writes."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
LUMA=np.array([.2126,.7152,.0722])
def decode(rgb):
    x=np.asarray(rgb,dtype=float)
    return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def stats(rgb):
    a=np.asarray(rgb,dtype=float).reshape(-1,3);lum=a@LUMA
    return {'mean_rgb_linear':a.mean(axis=0).tolist(),'mean_luminance_linear':float(lum.mean()),
            'p10_p50_p90_luminance_linear':np.percentile(lum,[10,50,90]).tolist(),'pixels':len(a)}
pins={}
def load(rel):
    p=ROOT/rel;pins[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return np.asarray(Image.open(p).convert('RGBA'))
def cached_tint(name):
    rel=f'game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_{name}.mat'
    p=ROOT/rel;txt=p.read_text();pins[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    m=re.search(r'_Tint: \{r: ([^,]+), g: ([^,]+), b: ([^,]+)',txt)
    if not m:return None
    encoded=np.array([float(x) for x in m.groups()])
    return {'serialized_srgb':encoded.tolist(),'expected_decoded_GPU_linear':decode(encoded).tolist(),
            'limitation':'COPIED cache before own fresh import; diagnostic only, not a GPU readback'}
spec=json.loads((ROOT/'art-source/world/materials/materials_spec.json').read_text())['sets']
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())['materials']
layout=json.loads((ROOT/'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json').read_text())['atlas']
rgb=np.array(manifest['hedge_thuja']['color']);assert spec['hedge_foliage']['kind']=='modulation_set'
fire_color=np.array(manifest['fire_station']['color']);fire_mean=np.array(spec['fire_station']['albedo']['mean_rgb_linear'])
fire_tint=float(np.clip((fire_color@LUMA)/(fire_mean@LUMA),.4,2.5))
d={'status':'SOURCE_DATA_AND_A_CORRECT_TINT_DIAGNOSTIC_NOT_UNITY_VISUAL_MATCH',
   'expected_tint_contract':{'SetLinearTint':'Color(linear).gamma stored as Color; shader receives intended linear value',
       'near_core_linear_tint':rgb.tolist(),'near_core_albedo_scale':2,'far_atlas_linear_grey_tint':fire_tint,
       'shell_basecolor':'white; URP Lit alpha clip0.5; RGB texture decoded from sRGB'},
   'copied_material_tints':{name:cached_tint(name) for name in ('hedge_thuja','fire_station')},'tiers':{}}
for tier in ('Medium','High'):
    near=load(f'art-source/world/materials/hedge_foliage/{tier}/T_hedge_foliage_BaseColor.png')
    far=load(f'art-source/world/materials/fire_station/{tier}/T_fire_station_BaseColor.png')
    # Same physical inner atlas ROI (0.05m gutter excluded), upper-left PNG origin.
    rect=layout['thuja_far'];tile=layout['tile_m'];hh,ww=far.shape[:2];pad=.05
    box=[int(np.ceil((rect['u'][0]+pad)*ww/tile[0])),int(np.ceil((tile[1]-rect['v'][1]+pad)*hh/tile[1])),
         int(np.floor((rect['u'][1]-pad)*ww/tile[0])),int(np.floor((tile[1]-rect['v'][0]-pad)*hh/tile[1]))]
    x0,y0,x1,y1=box;far_crop=far[y0:y1,x0:x1,:3]
    core=decode(near[:,:,:3]/255)*rgb*2
    far_linear=decode(far_crop/255)*fire_tint
    a,b=stats(core),stats(far_linear)
    d['tiers'][tier]={'near_core_effective_source_albedo':a,'far_effective_source_albedo':b,'far_roi_png_box':box,
                      'far_over_core_mean_luminance_ratio':b['mean_luminance_linear']/a['mean_luminance_linear']}
shell=load('art-source/world/textures/hedge_shell_thuja.png')
keep=shell[:,:,3]>=128;rgb_shell=decode(shell[:,:,:3]/255)
d['shell']={'resolution':[shell.shape[1],shell.shape[0]],'cutoff':.5,'covered_fraction':float(keep.mean()),
            'covered_texel_linear':stats(rgb_shell[keep]),'all_texel_linear_including_dilated_transparency':stats(rgb_shell),
            'coverage_warning':'tile texel coverage, NOT projected screen coverage; opaque core remains behind shell'}
for row in d['tiers'].values():
    row['far_over_covered_shell_mean_luminance_ratio']=row['far_effective_source_albedo']['mean_luminance_linear']/d['shell']['covered_texel_linear']['mean_luminance_linear']
d['source_sha256']=pins
d['limitations']=['No lighting, tone mapping, AO, normals, terrain GI, sampling footprints or ASTC loss included.',
 'No flat source ratio is a measured Low/High screen-color ratio.',
 'Opaque near core and opaque far atlas have different source palettes; transparent shell cannot remove the core silhouette.',
 'A shared intended linear foliage palette is a candidate fix within own atlas/model scope; protected plaster/roof/trim remain frozen.']
(OUT/'foliage-color-audit.json').write_text(json.dumps(d,indent=2))
print(json.dumps({k:{'core_Y':v['near_core_effective_source_albedo']['mean_luminance_linear'],'far_Y':v['far_effective_source_albedo']['mean_luminance_linear'],'far/core':v['far_over_core_mean_luminance_ratio'],'far/shell':v['far_over_covered_shell_mean_luminance_ratio']} for k,v in d['tiers'].items()},indent=2))
print('shell coverage',d['shell']['covered_fraction'],'shell Y',d['shell']['covered_texel_linear']['mean_luminance_linear'])
