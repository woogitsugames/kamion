"""Read-only native photo details: do not confuse lighting spread with paint wear."""
from pathlib import Path
from PIL import Image
import json
import hashlib

ROOT=Path(__file__).resolve().parent
path=ROOT/'reference7204-original.jpg'
im=Image.open(path).convert('RGB')
out=ROOT/'underdeck-photo-details'; out.mkdir(exist_ok=True)
regions={'front_piers':(118,323,182,420),'mid_pier':(222,325,266,409),'rear_pier':(318,328,360,408)}
meta={'source_file':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_size':im.size,
      'preview_basis':[960,640],'license':'CC0','author':'Rakoon','regions':{}}
for name,box in regions.items():
    native=tuple(round(v*im.width/960) for v in box)
    crop=im.crop(native); crop.thumbnail((960,960)); crop.save(out/(name+'.png'))
    meta['regions'][name]={'native_box':native,'output_size':crop.size}
(out/'source.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(meta['source_size'])
