"""Lossy labelled QA thumbnails; original PNG evidence remains untouched."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

OUT=Path(__file__).parent
stage=sys.argv[1] if len(sys.argv)>1 else 'before'
assert stage.replace('-','').isalnum()
packet=json.loads((OUT/'cameras.json').read_text(encoding='utf-8-sig'))
ids=[c['id'] for c in packet['cameras'] if c['id'].startswith(('life3_','sheet_far_','g_r4_'))]
ids+=['g_current_black_wheel_02','g_current_black_lod_05','r10_wheel_02','r10_front_04']
ids=list(dict.fromkeys(ids))
for condition in ('Low-clear','Low-overcast','High-clear','High-overcast'):
    dest=OUT/f'{stage}-focus'/condition
    dest.mkdir(parents=True,exist_ok=True)
    for name in ids:
        source=OUT/stage/condition/f'{name}.png'
        assert source.is_file(),source
        with Image.open(source) as frame:
            thumb=ImageOps.contain(frame.convert('RGB'),(960,900))
        canvas=Image.new('RGB',(960,thumb.height+30),'#252525')
        canvas.paste(thumb,((960-thumb.width)//2,30))
        ImageDraw.Draw(canvas).text((5,7),f'{stage} | {condition} | {name}',fill='white')
        canvas.save(dest/f'{name}.jpg',quality=92)
    new=[name for name in ids if name.startswith(('life3_','sheet_far_'))]
    grid=Image.new('RGB',(960,540),'#252525')
    draw=ImageDraw.Draw(grid)
    for index,name in enumerate(new):
        with Image.open(OUT/stage/condition/f'{name}.png') as frame:
            thumb=ImageOps.contain(frame.convert('RGB'),(320,148))
        x=index%3*320; y=index//3*180
        draw.text((x+3,y+3),name,fill='white')
        grid.paste(thumb,(x,y+24))
    grid.save(dest/'new-cameras.jpg',quality=92)
print(json.dumps(dict(stage=stage,individual_frames=len(ids)*4,conditions=4)))
