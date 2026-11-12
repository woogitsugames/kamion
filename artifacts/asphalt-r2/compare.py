"""Compare every captured camera; preserve instance counters separately from mesh counters."""
import argparse
import csv
import json
import re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

def counters(path):
    rows = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'([^:]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
        if m:
            rows[m[1]] = dict(zip(('objects','draws','shadow_draws','tris_k'), map(int,m.groups()[1:])))
        m = re.match(r'  (.+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k, cells (\d+), forest HLOD cells (\d+)', line)
        if m:
            rows[m[1]].update(zip(('instance_draws','instances','instance_tris_k','cells','forest_cells'),map(int,m.groups()[1:])))
    return rows

def thumb(path, size):
    im = Image.open(path).convert('RGB')
    im.thumbnail(size)
    return im

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', default='baseline')
    ap.add_argument('--after', default='candidate')
    a = ap.parse_args()
    rows = []
    pages = OUT / f'comparison-{a.after}-960'
    pages.mkdir(exist_ok=True)
    for tier in ('Low','High'):
        for lighting in ('overcast','clear'):
            condition = f'{tier}-{lighting}'
            bdir, adir = OUT/a.before/condition, OUT/a.after/condition
            bc, ac = counters(bdir/'stats.txt'), counters(adir/'stats.txt')
            assert set(bc) == set(ac), f'Counter scope mismatch {condition}'
            bfiles = {p.name for p in bdir.glob('*.png') if not p.stem.endswith(('_mask','_envcube'))}
            afiles = {p.name for p in adir.glob('*.png') if not p.stem.endswith(('_mask','_envcube'))}
            assert bfiles == afiles, f'Image scope mismatch {condition}'
            contact = None
            for index, name in enumerate(sorted(bfiles)):
                camera = Path(name).stem
                b, c = Image.open(bdir/name).convert('RGB'), Image.open(adir/name).convert('RGB')
                ba, ca = np.asarray(b,dtype=float), np.asarray(c,dtype=float)
                assert ba.shape == ca.shape
                delta = ca-ba
                row = dict(condition=condition,camera=camera,rmse_rgb=float(np.sqrt((delta*delta).mean())),
                           changed_pixels_gt_2=float((np.max(abs(delta),axis=2)>2).mean()))
                for key, value in bc[camera].items():
                    row[f'before_{key}'] = value
                    row[f'after_{key}'] = ac[camera][key]
                    row[f'delta_{key}'] = ac[camera][key]-value
                rows.append(row)
                # All frames appear in before/after contact pages, with larger detail pairs for wear and sbs.
                if index%12 == 0:
                    contact = Image.new('RGB',(960,720),'#202020')
                x,y = index%2*480, (index%12)//2*120
                contact.paste(thumb(bdir/name,(240,100)),(x,y+18))
                contact.paste(thumb(adir/name,(240,100)),(x+240,y+18))
                ImageDraw.Draw(contact).text((x+3,y+2),camera[:58],fill='white')
                if index%12 == 11 or index == len(bfiles)-1:
                    contact.save(pages/f'{condition}-contact-{index//12:02}.jpg')
                if camera.startswith(('d_wear_','sbs-', 'asphalt_')):
                    pair = Image.new('RGB',(960,250),'#202020')
                    pair.paste(thumb(bdir/name,(480,225)),(0,24))
                    pair.paste(thumb(adir/name,(480,225)),(480,24))
                    ImageDraw.Draw(pair).text((4,4),f'{camera} | BEFORE ({a.before}) / AFTER ({a.after})',fill='white')
                    pair.save(pages/f'{condition}-{camera}.jpg')
    with (OUT/f'counters-{a.after}.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary = dict(rows=len(rows), conditions=sorted({r['condition'] for r in rows}),
                   cameras=len({r['camera'] for r in rows}),
                   max_abs_counter_delta={k:max(abs(r[k]) for r in rows) for k in rows[0] if k.startswith('delta_')},
                   note='CPU visibility/LOD estimates, rounded triangles in thousands. Not GPU or phone measurements.')
    (OUT/f'comparison-{a.after}.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()

