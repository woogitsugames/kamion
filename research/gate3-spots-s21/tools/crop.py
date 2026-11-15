"""crop.py src out x0 y0 x1 y1 (fractions 0..1) [width]"""
import sys
from PIL import Image
im = Image.open(sys.argv[1])
W, H = im.size
x0, y0, x1, y1 = [float(v) for v in sys.argv[3:7]]
c = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
w = int(sys.argv[7]) if len(sys.argv) > 7 else 960
c = c.resize((w, round(c.size[1] * w / c.size[0])))
c.convert('RGB').save(sys.argv[2], quality=88)
print(c.size)
