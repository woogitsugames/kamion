"""Crop with pixel rulers (coordinates of the 1280-wide image). usage: zoom.py img x0 y0 x1 y1 scale out [step]"""
import sys
from PIL import Image, ImageDraw
img, x0, y0, x1, y1, s, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
step = int(sys.argv[8]) if len(sys.argv) > 8 else 10
im = Image.open(img).convert('RGB')
if im.width != 1280:
    im = im.resize((1280, round(im.height * 1280 / im.width)))
c = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * s, (y1 - y0) * s), Image.NEAREST)
d = ImageDraw.Draw(c)
for x in range(x0 - x0 % step, x1, step):
    X = (x - x0) * s; big = x % (step * 5) == 0
    d.line([(X, 0), (X, 14 if big else 6)], fill='red')
    if big: d.text((X + 2, 14), str(x), fill='red')
for y in range(y0 - y0 % step, y1, step):
    Y = (y - y0) * s; big = y % (step * 5) == 0
    d.line([(0, Y), (14 if big else 6, Y)], fill='cyan')
    if big: d.text((16, Y - 5), str(y), fill='cyan')
c.save(out)
