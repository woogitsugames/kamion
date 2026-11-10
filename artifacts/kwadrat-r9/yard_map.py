"""Orthophoto crop with the generated point instances drawn on it (yard audit, ADR 0071 r10).
uv run --project tools/worldgen python artifacts/kwadrat-r9/yard_map.py XMIN YMIN XMAX YMAX out.jpg [--scale 2.5]
Coordinates EPSG:2180. Colours: red = cars/vans, yellow = trailers/tractors, cyan = lamps, magenta = signs/plates,
white = everything else; label = prototype (shortened)."""
import argparse, glob, json, math
from pathlib import Path
import yaml
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
REPO = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument("box", nargs=4, type=float); ap.add_argument("out"); ap.add_argument("--scale", type=float, default=2.5)
ap.add_argument("--region", default="bialystok-industrial-c"); ap.add_argument("--nolabel", action="store_true")
a = ap.parse_args()
xmin, ymin, xmax, ymax = a.box
R = REPO / "Data" / "Regions" / a.region
reg = json.loads((R / "terrain.json").read_text(encoding="utf-8"))
X0, Y1 = reg["bbox"][0], reg["bbox"][3]
org = yaml.safe_load((R / "region.yaml").read_text(encoding="utf-8"))["origin"]
im = Image.open(REPO / "Data/raw/derived" / a.region / "ortho_0p25m.tif").convert("RGB")
c = im.crop((int((xmin - X0) * 4), int((Y1 - ymax) * 4), int((xmax - X0) * 4), int((Y1 - ymin) * 4)))
c = c.resize((int(c.width * a.scale), int(c.height * a.scale)), Image.LANCZOS)
k = 4 * a.scale
d = ImageDraw.Draw(c)
P = lambda x, y: ((x - xmin) * k, (ymax - y) * k)
for g in range(int(xmin // 10 * 10), int(xmax) + 1, 10):
    d.line([P(g, ymin), P(g, ymax)], fill=(255, 255, 255), width=1); d.text(P(g, ymax), str(g % 1000), fill=(255, 255, 0))
for g in range(int(ymin // 10 * 10), int(ymax) + 1, 10):
    d.line([P(xmin, g), P(xmax, g)], fill=(255, 255, 255), width=1); d.text(P(xmin, g), str(g % 1000), fill=(255, 255, 0))
n = {}
for f in glob.glob(str(REPO / "Data/raw/derived" / a.region / "world" / "instances_*.json")):
    for it in json.loads(Path(f).read_text(encoding="utf-8"))["instances"]:
        x, y = it["e"] + org["x"], it["n"] + org["y"]
        if not (xmin < x < xmax and ymin < y < ymax) or it["p"].startswith("tree_"):
            continue
        p = it["p"]; n[p] = n.get(p, 0) + 1
        col = (255, 60, 60) if p.startswith(("car_", "van_")) else (255, 230, 0) if p.startswith(("trailer", "tractor", "container")) \
            else (0, 255, 255) if p.startswith("lamp") else (255, 0, 255) if p.startswith(("plate_", "sign_", "board_")) else (255, 255, 255)
        u, v = P(x, y)
        yaw = it.get("yaw", 0.0)
        L = 13.6 if p.startswith("trailer") else 4.5 if p.startswith(("car_", "van_")) else 6.0 if p.startswith(("tractor", "barrier", "container")) else 1.5
        # prototype +y is "forward"; yaw about up, counter-clockwise from north (see streetscape.furniture.Placer)
        dx, dy = -math.sin(yaw) * L, math.cos(yaw) * L
        d.line([(u, v), P(x + dx, y + dy)], fill=col, width=3)
        d.ellipse([u - 4, v - 4, u + 4, v + 4], outline=col, width=2)
        if not a.nolabel and not p.startswith(("car_", "van_")):
            d.text((u + 6, v - 6), p[:18], fill=col)
c.save(a.out, quality=88)
print(a.out, c.size, dict(sorted(n.items())))
