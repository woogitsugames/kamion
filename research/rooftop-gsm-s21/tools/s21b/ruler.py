"""Wycinek z linijką: python3 -I ruler.py in.jpg out.jpg x0 y0 x1 y1 scale step"""
import sys
from PIL import Image, ImageDraw
fn, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1, sc, st = map(int, sys.argv[3:9])
im = Image.open(fn).crop((x0, y0, x1, y1))
im = im.resize((im.width * sc, im.height * sc), Image.LANCZOS)
d = ImageDraw.Draw(im)
for y in range(y0 - y0 % st + st, y1, st):
    yy = (y - y0) * sc
    d.line([(0, yy), (25, yy)], fill=(255, 0, 0), width=2)
    d.text((28, yy - 6), str(y), fill=(255, 0, 0))
    d.line([(im.width - 25, yy), (im.width, yy)], fill=(255, 0, 0), width=2)
for x in range(x0 - x0 % st + st, x1, st * 2):
    xx = (x - x0) * sc
    d.line([(xx, 0), (xx, 20)], fill=(255, 0, 0), width=2)
    d.text((xx + 2, 22), str(x), fill=(255, 0, 0))
im.save(out, quality=90)
print(im.size)
