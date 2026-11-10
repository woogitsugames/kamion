"""Draw dims.json (blocks, fence, thuja row) over the GUGiK orthophoto crop to check the plan before modelling."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[3]
D = json.loads((REPO / "art-source/world/landmarks/fire_station_jrg2/dims.json").read_text(encoding="utf-8"))
im = Image.open(REPO / "artifacts/firestation-r9/refs/ortho_site_clean.png").convert("RGB")
half, ppm = 90.0, im.width / 180.0
A = np.array(D["axis"]["origin_en"])
U = np.array(D["axis"]["u"])
V = np.array([-U[1], U[0]])
d = ImageDraw.Draw(im)


def px(u, v):
    e, n = A + U * u + V * v
    return ((e - (-235 - half)) * ppm, ((-147 + half) - n) * ppm)


def rect(u, v, col):
    d.line([px(u[0], v[0]), px(u[1], v[0]), px(u[1], v[1]), px(u[0], v[1]), px(u[0], v[0])], fill=col, width=2)


rect(D["garage"]["u"], D["garage"]["v"], (255, 255, 0))
m = D["middle"]
d.line([px(m["u"][0], m["v_sw"]), px(m["u_step"], m["v_sw"]), px(m["u_step"], m["v_sw_recess"]), px(m["u"][1], m["v_sw_recess"])], fill=(0, 255, 0), width=2)
d.line([px(m["u"][0], m["v_ne"]), px(m["u"][1], m["v_ne"])], fill=(0, 255, 0), width=2)
rect(D["tower"]["u"], D["tower"]["v"], (255, 0, 255))
rect(D["hall"]["u"], D["hall"]["v"], (0, 255, 255))
rect(D["canopy"]["u"], D["canopy"]["v"], (255, 128, 0))
r = D["outbuilding"]["ring_uv"]
d.line([px(*p) for p in r + r[:1]], fill=(255, 255, 255), width=2)
for ln in D["fence"]["lines_uv"]:
    d.line([px(*p) for p in ln], fill=(255, 0, 0), width=2)
d.line([px(*p) for p in D["fence"]["gate_parked_uv"]], fill=(255, 120, 120), width=3)
d.line([px(*p) for p in D["thuja"]["row_uv"]], fill=(0, 120, 0), width=3)
for p in D["flagpoles"]["uv"]:
    x, y = px(*p)
    d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(255, 255, 255))
route = json.load(open(REPO / "Data/Regions/bialystok-industrial-c/route_start.json"))
d.line([((e + 325) * ppm, (-57 - n) * ppm) for e, n in route["points_en"]], fill=(255, 60, 60), width=1)
out = REPO / "artifacts/firestation-r9/plan_overlay.jpg"
im.resize((960, 960), Image.LANCZOS).save(out, quality=90)
print(out)
