"""ADR0101 helper: overlay material masks (magenta renders) on a baseline frame, with a 20 px tick grid (960 view)."""
import sys
from PIL import Image, ImageDraw
import numpy as np
COLS = {'bridge_concrete': (255, 0, 0), 'bridge_soffit': (0, 255, 255), 'noise_panel_dark': (255, 255, 0), 'kp_wall': (255, 0, 255),
        'barrier_steel': (0, 255, 0), 'marking_white': (0, 0, 255)}
def overlay(cam, cond, out, mats=COLS):
    base = np.asarray(Image.open(f'baseline/{cond}/{cam}.png').convert('RGB').resize((960, 443)), int)
    o = base.copy()
    for m, c in mats.items():
        try:
            a = np.asarray(Image.open(f'masks/{m}/{cam}_mask.png').convert('RGB').resize((960, 443), Image.NEAREST), int)
        except FileNotFoundError:
            continue
        mk = (a[..., 0] > 235) & (a[..., 1] < 25) & (a[..., 2] > 235)
        o[mk] = (o[mk] * 0.3 + np.array(c) * 0.7).astype(int)
    im = Image.fromarray(o.astype(np.uint8)); d = ImageDraw.Draw(im)
    for x in range(0, 960, 20): d.line([(x, 0), (x, 10 if x % 100 == 0 else 4)], fill=(255, 0, 0))
    for y in range(0, 443, 20): d.line([(0, y), (10 if y % 100 == 0 else 4, y)], fill=(255, 0, 0))
    im.save(out)
if __name__ == '__main__':
    overlay(sys.argv[1], sys.argv[2], sys.argv[3])
