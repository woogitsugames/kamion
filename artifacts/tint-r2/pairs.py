"""ADR0101: before/after pairs at 960 px (top = A, bottom = B), labelled; optional crop box in 960-view coords."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
def pair(a_dir, b_dir, cond, cam, out, box=None, la='baseline', lb='r1'):
    ims = []
    for d, lab in ((a_dir, la), (b_dir, lb)):
        im = Image.open(Path(d) / cond / f'{cam}.png').convert('RGB')
        if box:
            s = im.width / 960; im = im.crop(tuple(round(v * s) for v in box))
        im = im.resize((960, round(960 * im.height / im.width)))
        ImageDraw.Draw(im).text((8, 6), f'{lab} {cond} {cam}', fill=(255, 255, 0))
        ims.append(im)
    o = Image.new('RGB', (960, ims[0].height + ims[1].height))
    o.paste(ims[0], (0, 0)); o.paste(ims[1], (0, ims[0].height))
    Path(out).parent.mkdir(parents=True, exist_ok=True); o.save(out, quality=88)
if __name__ == '__main__':
    a, b, cond, cam, out = sys.argv[1:6]
    box = tuple(int(v) for v in sys.argv[6].split(',')) if len(sys.argv) > 6 else None
    pair(a, b, cond, cam, out, box, *(sys.argv[7:9] if len(sys.argv) > 8 else ()))
