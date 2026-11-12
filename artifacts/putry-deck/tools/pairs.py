"""ADR 0133: photo | before | after sheets (<= 960 px wide) for the Putry-deck G3-B frames."""
import json, sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path('C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/putry-deck')
MAIN = Path('C:/Users/matma/Documents/Claude/kamion')
A = ROOT / 'artifacts/putry-deck'
refs = {r['camera']: r for r in json.load(open(ROOT / 'Data/Regions/bialystok-industrial-c/sbs_references.json'))['references']}
out = A / 'pairs'; out.mkdir(exist_ok=True)
W = 960 // 2


def tile(path, label, h):
    if not Path(path).exists():
        im = Image.new('RGB', (W, h), (60, 0, 0))
    else:
        im = Image.open(path).convert('RGB')
        im = im.resize((W, int(im.height * W / im.width)))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 14], fill=(0, 0, 0)); d.text((3, 1), label, fill=(255, 220, 120))
    return im


for light in sys.argv[1:] or ['overcast', 'clear']:
    for b in sorted((A / f'before/Low-{light}').glob('sbs-*.png')):
        cam = b.stem; r = refs[cam]
        photo = MAIN / r['comparison_photo']
        a = A / f'after/Low-{light}/{cam}.png'
        t = [tile(photo, f"PHOTO {r['source_id']} {r['author']} {r['captured_at'][:10]} {r['license']}", 360),
             tile(b, f'BEFORE main Low-{light}', 360), tile(a, f'AFTER ADR0133 Low-{light}', 360)]
        h = max(x.height for x in t)
        sheet = Image.new('RGB', (W * 2, h * 2), (20, 20, 20))
        sheet.paste(t[0], (0, 0)); sheet.paste(t[1], (W, 0)); sheet.paste(t[2], (W, h)); sheet.paste(t[0], (0, h))
        sheet.save(out / f'{cam[9:]}-Low-{light}.jpg', quality=88)
