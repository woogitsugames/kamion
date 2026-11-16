"""ADR 0220: straightened orthophoto strip along the DK65 route (variant A chainage), GUGiK WMS HighResolution 0.1 m.

    uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/strip.py KM_A KM_B OUTDIR [half_w=12]

For every 0.1 m of route chainage s and lateral t in [-half_w, +half_w] (t > 0 = left "L", direction of growing km)
the orthophoto is sampled at P(s) + t * N(s), N = left normal of the chord P(s-10 m) -> P(s+10 m) (smooth across the
OSM vertices). Output: OUTDIR/strip_<a>_<b>.npz (gray uint8 [s, t], rows = s, row 0 = KM_A, column 0 = t = +half_w
i.e. LEFT side on the left of the image when the image is shown with growing km UP), JPG sheets of 100 m each
(route bottom -> top, L on the left, 1 m ticks every 10 px) and the WMS tiles cached in OUTDIR/wms/.
Sources: GUGiK ortofotomapa (WMS HighResolution), open data; generic User-Agent.
"""
import io
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads.route_km import RouteKm  # noqa: E402

WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
UA = {"User-Agent": "research-client/1.0 (generic)"}
RES = 0.1
CHUNK_M = 80.0


def getmap(x0, y0, x1, y1, cache: Path):
    f = cache / f"{x0:.0f}_{y0:.0f}_{x1:.0f}_{y1:.0f}.png"
    if f.exists():
        return np.asarray(Image.open(f).convert("L"))
    w, h = int(round((x1 - x0) / RES)), int(round((y1 - y0) / RES))
    p = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "Raster", "STYLES": "",
         "SRS": "EPSG:2180", "BBOX": f"{x0},{y0},{x1},{y1}", "WIDTH": w, "HEIGHT": h, "FORMAT": "image/png"}
    for a in range(5):
        try:
            r = requests.get(WMS, params=p, headers=UA, timeout=180)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                im = Image.open(io.BytesIO(r.content)).convert("L")
                im.save(f)
                return np.asarray(im)
            print("bad", r.status_code, r.text[:200], file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print("retry", e, file=sys.stderr)
        time.sleep(4 * (a + 1))
    raise SystemExit("wms fail")


def main():
    ka, kb, out = float(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])
    half = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0
    out.mkdir(parents=True, exist_ok=True)
    cache = out / "wms"
    cache.mkdir(exist_ok=True)
    r = RouteKm.from_plan()
    s = np.arange(ka * 1000.0, kb * 1000.0, RES)
    t = np.arange(half, -half - 1e-9, -RES)            # column 0 = +half (L)
    P = np.array([[*r.point(v / 1000.0)] for v in s])
    A = np.array([[*r.point(max(v - 10.0, 0.0) / 1000.0)] for v in s])
    B = np.array([[*r.point((v + 10.0) / 1000.0)] for v in s])
    T = B - A
    T /= np.hypot(*T.T)[:, None]
    N = np.column_stack([-T[:, 1], T[:, 0]])
    X = P[:, 0:1] + t[None, :] * N[:, 0:1]
    Y = P[:, 1:2] + t[None, :] * N[:, 1:2]
    G = np.zeros(X.shape, np.uint8)
    rows_per = int(CHUNK_M / RES)
    for i0 in range(0, len(s), rows_per):
        sl = slice(i0, i0 + rows_per)
        x0, x1 = math.floor(X[sl].min() - 2), math.ceil(X[sl].max() + 2)
        y0, y1 = math.floor(Y[sl].min() - 2), math.ceil(Y[sl].max() + 2)
        img = getmap(x0, y0, x1, y1, cache).astype(float)
        col = (X[sl] - x0) / RES - 0.5
        row = (y1 - Y[sl]) / RES - 0.5
        G[sl] = np.clip(ndimage.map_coordinates(img, [row, col], order=1, mode="nearest"), 0, 255).astype(np.uint8)
        time.sleep(0.3)
    tag = f"{ka:06.2f}_{kb:06.2f}"
    np.savez_compressed(out / f"strip_{tag}.npz", g=G, s0=ka * 1000.0, res=RES, half=half)
    # sheets: 100 m, growing km upwards, L on the left
    for j0 in range(0, len(s), int(100 / RES)):
        piece = G[j0:j0 + int(100 / RES)][::-1]
        im = Image.fromarray(piece).convert("RGB")
        d = ImageDraw.Draw(im)
        W = im.size[0]
        for m in range(-int(half), int(half) + 1):
            px = int(round((half - m) / RES))
            d.line([(px, 0), (px, 6 if m % 5 else 14)], fill=(255, 0, 0))
        for k in range(0, piece.shape[0], 100):
            d.line([(0, piece.shape[0] - 1 - k), (8, piece.shape[0] - 1 - k)], fill=(0, 255, 255))
        km0 = (s[j0]) / 1000.0
        d.text((W - 70, piece.shape[0] - 14), f"{km0:.2f}", fill=(255, 255, 0))
        im.save(out / f"sheet_{km0:06.2f}.jpg", quality=85)
    meta = {"km_a": ka, "km_b": kb, "res_m": RES, "half_w_m": half, "wms": WMS, "rows": int(G.shape[0])}
    (out / f"strip_{tag}.json").write_text(json.dumps(meta, indent=1))
    print("ok", G.shape)


if __name__ == "__main__":
    main()
