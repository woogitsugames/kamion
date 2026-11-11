"""Native-pixel detail crops for later landmark review; never alter the refs junction."""
from pathlib import Path
import json
import hashlib
from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parent/'chimney-photo-details'
OUT.mkdir(exist_ok=True)
ROOT=OUT.parents[2]
path=ROOT/'Data/raw/refs/commons/cmFile_20200711_073128_Elektrociep_ownia_Bia_ystok.jpg.jpg'
im=Image.open(path).convert('RGB')
# Bounding boxes measured on the 960 x 540 preview, then scaled to native pixels.
regions={'left_stack':(719,75,762,207),'right_stack':(890,0,941,202)}
proof={'source':path.relative_to(ROOT).as_posix(),'source_size':im.size,
       'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'preview_basis':[960,540],'regions':{}}
for name,box in regions.items():
    native=tuple(round(v*im.width/960) for v in box)
    crop=im.crop(native)
    # Keep the native crop if already small; no invented detail by upscaling.
    crop.thumbnail((960,960))
    crop.save(OUT/(name+'.png'))
    proof['regions'][name]={'native_box':native,'output_size':crop.size}
(OUT/'source.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps(proof,indent=2))
