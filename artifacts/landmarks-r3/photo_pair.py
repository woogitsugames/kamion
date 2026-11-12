"""960px evidence, full-height CC BY photo; no pose warp or colour adjustment."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
phase=sys.argv[1]
source=ROOT/'Data/raw/refs/commons/cmFile_20200711_073128_Elektrociep_ownia_Bia_ystok.jpg.jpg'
photo=Image.open(source).convert('RGB')
assert photo.size==(3840,2160)
target=OUT/'review'/('photo-'+phase)
target.mkdir(parents=True,exist_ok=True)
records=[]
boxes=dict(multi=[2876,300,3048,828],single=[3560,0,3764,808])
for condition in ['Low-overcast','Low-clear','High-overcast','High-clear']:
    path=OUT/phase/condition/'ec-ref073128.png'
    if not path.exists():
        continue
    render=Image.open(path).convert('RGB')
    assert render.size==(2340,1080)
    crop=render.crop((210,0,2130,1080))
    sheet=Image.new('RGB',(960,322),(24,24,24))
    draw=ImageDraw.Draw(sheet)
    draw.text((8,4),f'Rakoon CC BY3.0 | {phase} {condition} | photo / render central1920x1080',fill='white')
    draw.text((8,20),'POSE WORKING_VALUE: two-shaft resection; not surveyed; no roll/distortion correction',fill=(255,208,128))
    sheet.paste(photo.resize((480,270)),(0,46))
    sheet.paste(crop.resize((480,270)),(480,46))
    full=target/f'{condition}-ec-ref073128.jpg'; sheet.save(full,quality=93)
    # Matching angular windows, with render enlarged2x explicitly for inspection.
    # No independent translation/scale of either shaft is used.
    matching=crop.resize(photo.size)
    close=Image.new('RGB',(960,850),(24,24,24))
    draw=ImageDraw.Draw(close)
    draw.text((8,4),f'Rakoon CC BY3.0 | {phase} {condition} | fixed photo windows',fill='white')
    draw.text((8,20),'multi: photo / render2x | single: photo / render2x | pose and head dimensions WORKING_VALUE',fill=(255,208,128))
    for i,(key,box) in enumerate(boxes.items()):
        a=photo.crop(box); b=matching.crop(box)
        for k,image in enumerate((a,b)):
            close.paste(image,(i*480+k*240+(240-image.width)//2,42))
    detail=target/f'{condition}-heads.jpg'; close.save(detail,quality=93)
    records.append(dict(condition=condition,pair=str(full.relative_to(OUT)),detail=str(detail.relative_to(OUT)),
                        width_px=960,render_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
result=dict(author='Rakoon',license='CC BY3.0',license_url='https://creativecommons.org/licenses/by/3.0/',
            source_page='https://commons.wikimedia.org/wiki/File:20200711_073128_Elektrociep%C5%82ownia_Bia%C5%82ystok.jpg',
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            source_status='Existing resized3840x2160 reference; original4608x2592 not locally verified',
            changes='Full-photo resizing, fixed-window detail crops; central horizontal render crop and explicit2x enlargement. No colour changes or pose warping.',
            render_crop=[210,0,2130,1080],photo_detail_boxes=boxes,phase=phase,pairs=records)
(target/'source.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Saved',len(records),'full pairs and',len(records),'detail pairs to',target)
