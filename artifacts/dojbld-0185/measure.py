"""Measurements behind the ADR numbers: hall corner height in frame P11-094 (photo vs render, both scaled to 960x540)
and wall tones in P11-001 (block vs white hall). usage: measure.py <render dir>"""
import sys
import numpy as np
from PIL import Image
P = "C:/Users/matma/Documents/Claude/kamion/research/_incoming/mistral-p11-dojlidy-photos-v2/files/"
R = sys.argv[1]
def load(p):
    return np.asarray(Image.open(p).convert("RGB").resize((960, 540), Image.LANCZOS), float)
def col(im, x, w=3):
    return im[:, x - w:x + w + 1].mean(axis=1)            # (540, 3)
def edges(im, x, y0, y1):
    c = col(im, x).mean(axis=1)
    g = np.abs(np.diff(c))
    ys = [int(y) for y in np.argsort(g[y0:y1])[::-1][:6] + y0]
    return sorted(ys), [round(float(g[y]), 1) for y in sorted(ys)]
ph, rd = load(P + "P11-094.jpg"), load(R + "/photo-P11-094.png")
for name, im, x in (("photo", ph, 215), ("render", rd, 225)):
    print(name, "x", x, "strongest vertical luminance steps (y, step):", *edges(im, x, 0, 420))
    c = col(im, x).mean(axis=1)
    print("   profile every 20 px:", [int(v) for v in c[0:420:20]])
ph, rd = load(P + "P11-001.jpg"), load(R + "/photo-P11-001.png")
def patch(im, x0, y0, x1, y1):
    return [int(v) for v in im[y0:y1, x0:x1].reshape(-1, 3).mean(axis=0)]
print("P11-001 photo: block gable", patch(ph, 215, 260, 245, 290), "block long wall", patch(ph, 300, 215, 360, 228), "white hall", patch(ph, 760, 235, 830, 262), "sky", patch(ph, 500, 60, 600, 120))
print("P11-001 render: block gable", patch(rd, 100, 215, 180, 300), "block long wall", patch(rd, 250, 215, 320, 228), "white hall", patch(rd, 760, 250, 820, 290), "sky", patch(rd, 500, 60, 600, 120))

# --- P11-094: wall of the hall just right of the NE corner (photo x 230, renders x 240 of 960): row of the roof
# edge (first row darker than 0.8 x the sky above) and of the bottom of the light cladding (first row below the
# roof + 100 darker than 0.7 x the wall median). The ground row is read off the printed profile (+-5 px).
def wall_rows(path, x):
    im = load(path).mean(axis=2)
    c = im[:, x - 2:x + 3].mean(axis=1)
    sky = c[:5].mean()
    roof = int(np.argmax(c < 0.8 * sky))
    wall = float(np.median(c[roof + 20:roof + 200]))
    bot = roof + 100 + int(np.argmax(c[roof + 100:] < 0.7 * wall))
    return roof, bot, [int(v) for v in c[bot - 10:bot + 60:5]]
B = "C:/Users/matma/Documents/Claude/kamion/artifacts/dojlidy-vis-0179/Low-overcast-photo/photo-P11-094.png"
for name, path, x in (("photo", P + "P11-094.jpg", 230), ("0179", B, 240), ("render", R + "/photo-P11-094.png", 240)):
    roof, bot, prof = wall_rows(path, x)
    print(f"P11-094 {name:6} x {x}: roof row {roof}, cladding bottom row {bot}, cladding {bot - roof} px; profile from bottom-10 step 5: {prof}")
