"""Artifact-only hall-glass candidate; verify all other atlas pixels remain exact."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'art-source/world/materials/_src/sets_fire_station.py'
text=source.read_text(encoding='utf-8')
changes={
    'sky = (0.90 + 0.06 * np.clip(gv / max(gmax, 1e-3), 0, 1) ** 1.3)[..., None]':
    'sky = (0.43 + 0.57 * np.clip(gv / max(gmax, 1e-3), 0, 1) ** 1.3)[..., None]',
    'hall_glass = np.array([0.0612, 0.0648, 0.0702], np.float32)':
    'hall_glass = np.array([0.0459, 0.0486, 0.05265], np.float32)'}
candidate=text
for before,after in changes.items():
    assert candidate.count(before)==1
    candidate=candidate.replace(before,after)
arrays=[]
for code in (text,candidate):
    ns={'__file__':str(source),'__name__':'landmarks_glass_cpu_candidate'}
    exec(compile(code,str(source),'exec'),ns)
    surface=ns['fire_station'](512)
    arrays.append(surface.albedo.copy())
allowed=np.zeros(arrays[0].shape[:2],bool)
for key in ('win_arch','win_round'):
    r=ns['LAYOUT'][key]
    x0,x1=[int(np.floor(v/14*512)) for v in r['u']]
    y0,y1=[int(np.floor((14-v)/14*512)) for v in r['v'][::-1]]
    allowed[max(0,y0-1):y1+2,max(0,x0-1):x1+2]=True
assert np.array_equal(arrays[0][~allowed],arrays[1][~allowed])
out=Path(__file__).parent/'glass-candidate'
out.mkdir(exist_ok=True)
sheet=Image.new('RGB',(960,280),(25,25,25))
for index,array in enumerate(arrays):
    encoded=np.clip(np.rint(ns['K'].srgb_encode(array)*255),0,255).astype('uint8')
    image=Image.fromarray(encoded)
    image.save(out/('before.png' if index==0 else 'candidate.png'))
    # Enlarge only the arch tile for inspecting the encoded CPU gradient.
    r=ns['LAYOUT']['win_arch']
    crop=image.crop((round(r['u'][0]/14*512),round((14-r['v'][1])/14*512),
        round(r['u'][1]/14*512),round((14-r['v'][0])/14*512)))
    crop.thumbnail((450,250))
    crop=crop.resize((250,250),Image.Resampling.NEAREST)
    sheet.paste(crop,(index*480+110,28))
    ImageDraw.Draw(sheet).text((index*480+12,8),'CPU atlas before' if index==0 else 'CPU candidate; NOT Unity',fill='white')
sheet.save(out/'comparison.jpg',quality=95)
proof={'artifact_only':True,'resolution':512,'outside_arch_and_round_rects_exact':True,
    'changed_pixels':int(np.any(arrays[0]!=arrays[1],axis=2).sum()),
    'source_changes':changes,'rendered_colour_and_budget':'UNVERIFIED'}
(out/'proof.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items() if k!='source_changes'}))
