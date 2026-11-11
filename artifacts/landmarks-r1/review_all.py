"""Inventory and inspect every like-for-like camera, at 960 px sheet width."""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'review' / 'after-all'
OUT.mkdir(parents=True, exist_ok=True)
rows = []
for cond in ('Low-overcast', 'Low-clear', 'High-overcast', 'High-clear'):
    before = {p.name: p for p in (ROOT/'before'/cond).glob('*.png')}
    after = {p.name: p for p in (ROOT/'after'/cond).glob('*.png')}
    assert before.keys() == after.keys(), cond
    assert len(before) == 48, (cond, len(before))
    panels = []
    for name in sorted(before):
        a = Image.open(before[name]).convert('RGB')
        b = Image.open(after[name]).convert('RGB')
        aa, bb = np.asarray(a), np.asarray(b)
        delta = np.abs(aa.astype(np.int16)-bb.astype(np.int16))
        changed = delta.max(axis=2) > 5
        rows.append(dict(condition=cond, camera=Path(name).stem,
                         mean_abs=float(delta.mean()), fraction_over_5=float(changed.mean()),
                         exact=bool(not delta.any())))
        panel = Image.new('RGB', (960,246), (24,24,24))
        d = ImageDraw.Draw(panel)
        d.text((8,5), f'{cond} {Path(name).stem} | before / after', fill='white')
        for i, im in enumerate((a,b)):
            im.thumbnail((480,222))
            panel.paste(im,(480*i+(480-im.width)//2,24+(222-im.height)//2))
        panels.append(panel)
    for page in range(0,len(panels),8):
        sheet=Image.new('RGB',(960,246*len(panels[page:page+8])))
        for y,panel in enumerate(panels[page:page+8]): sheet.paste(panel,(0,y*246))
        sheet.save(OUT/f'{cond}-{page//8+1:02d}.jpg',quality=91)
(ROOT/'pixel-diff-all.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Camera conditions:',len(rows))
print('Exact:',sum(r['exact'] for r in rows))
for row in sorted(rows,key=lambda r:r['mean_abs'],reverse=True)[:20]: print(row)
