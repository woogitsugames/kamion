"""Inspect the complete measured baseline inventory, one full PNG in RAM."""
import json
from pathlib import Path

from PIL import Image,ImageDraw

root=Path(__file__).resolve().parent
baseline=json.loads((root/'baseline-result.json').read_text(encoding='utf-8-sig'))
details={c['id']+'.png' for c in json.loads((root/'cameras.json').read_text(encoding='utf-8-sig'))['cameras']}
known={p.name for p in (root.parent/'landmarks-r2/before/Low-overcast').glob('*.png')}
assert known and details
out=root/'review/baseline'; out.mkdir(parents=True,exist_ok=True)
records=[]
for condition,names in baseline['camera_inventories'].items():
    assert set(names)>=(known|details),(condition,(known|details)-set(names))
    files={p.name:p for p in (root/'before'/condition).glob('*.png')}
    assert set(names)==files.keys()
    for i,name in enumerate(sorted(names)):
        page,tile=divmod(i,16)
        if tile==0:
            sheet=Image.new('RGB',(960,246*((min(16,len(names)-i)+1)//2)),(24,24,24))
        x,y=(tile%2)*480,(tile//2)*246
        ImageDraw.Draw(sheet).text((x+5,y+4),condition+' '+Path(name).stem,fill='white')
        with Image.open(files[name]) as original:
            image=original.convert('RGB'); image.thumbnail((480,222))
            sheet.paste(image,(x+(480-image.width)//2,y+24))
        if tile==15 or i==len(names)-1:
            target=out/f'{condition}-{page+1:02d}.jpg'
            sheet.save(target,quality=92)
            records.append(str(target.relative_to(root)))
(root/'baseline-inventory-verified.json').write_text(json.dumps(dict(complete=True,known_r2_cameras_retained=True,all_13_detail_cameras_present=True,
    counts={k:len(v) for k,v in baseline['camera_inventories'].items()},sheets=records),indent=2),encoding='utf-8')
print('Baseline sheets:',len(records))
