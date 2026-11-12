"""ortho_crop.py E,N,half,name[,grid_m] ... [--mark E,N ...]: GUGiK orthophoto window (HR 0.08 m cells where cached, else the
0.25 m sheet) around region-local points, north up, metre grid with labels, optional red marks -> artifacts/biezenstwa-island/ortho/<name>.jpg"""
import sys, os
sys.path.insert(0, "tools/worldgen")
import numpy as np
from PIL import Image, ImageDraw
from roads import pipeline
from fidelity import ortho as O
reg = pipeline.load_region("bialystok-industrial-c")
ox, oy = reg["origin"]["x"], reg["origin"]["y"]
ort = O.Ortho(reg)
args = [a for a in sys.argv[1:] if not a.startswith("--")]
marks = []
if "--mark" in sys.argv:
    i = sys.argv.index("--mark")
    marks = [tuple(float(v) for v in a.split(",")) for a in sys.argv[i + 1:]]
    args = [a for a in sys.argv[1:i]]
os.makedirs("artifacts/biezenstwa-island/ortho", exist_ok=True)
for a in args:
    f = a.split(",")
    e, n, h, name = float(f[0]), float(f[1]), float(f[2]), f[3]
    g = float(f[4]) if len(f) > 4 else 5.0
    res = 2 * h / 900.0
    img, src = ort.window((ox + e - h, oy + n - h, ox + e + h, oy + n + h), res)
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    px = lambda E, N: ((E - (e - h)) / res, ((n + h) - N) / res)
    k = np.ceil((e - h) / g) * g
    while k < e + h:
        x = px(k, 0)[0]; d.line([(x, 0), (x, im.height)], fill=(255, 255, 0), width=1); d.text((x + 2, 2), f"{k:.0f}", fill=(255, 255, 0)); k += g
    k = np.ceil((n - h) / g) * g
    while k < n + h:
        y = px(0, k)[1]; d.line([(0, y), (im.width, y)], fill=(255, 255, 0), width=1); d.text((2, y + 2), f"{k:.0f}", fill=(255, 255, 0)); k += g
    for m in marks:
        x, y = px(m[0], m[1]); d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 0, 0), width=2)
    im.save(f"artifacts/biezenstwa-island/ortho/{name}.jpg", quality=90)
    print(name, src, im.size)
