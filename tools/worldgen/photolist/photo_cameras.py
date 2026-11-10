"""Game cameras at the poses of chosen Mapillary reference photos (ADR 0065 / ADR 0069) + game-vs-photo montages.

Cameras (gate3-camera schema, read by scripts/visual-qa.ps1 -Gate3 <json>):
    uv run --project tools/worldgen python tools/worldgen/photolist/photo_cameras.py cameras \
        --out artifacts/street-r9/photo_cameras.json
Montage (photo | game render(s)), every tile scaled so the sheet is <= 960 px wide:
    uv run --project tools/worldgen python tools/worldgen/photolist/photo_cameras.py montage \
        --renders <dir>[,<dir2>] --labels before,after --out artifacts/street-r9/montage

Pose = the photo's own lat/lon/compass_angle from Data/raw/mapillary/<region>/manifest.jsonl (not the photo-list
point), E,N = EPSG:2180 minus the region origin. U = NMT (Data/raw/derived/<id>/heightmap_2049.r16) + 1.7 m and the
camera is re-seated on the road collision by the importer (seat "road", Gate3Cameras.HeightAboveRoad photo_match).
Horizontal FOV per contributor's camera is a WORKING_VALUE read off the photos (wide dashcam vs phone), converted to
the vertical FOV Unity wants for a 4:3 frame. Photos are references only (CC BY-SA 4.0, no pixels in the build).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer

REPO = Path(__file__).resolve().parents[3]
REGION = "bialystok-industrial-c"
OX, OY = 777995.0, 596223.0
TO_PL = Transformer.from_crs(4326, 2180, always_xy=True)

# point -> Mapillary image id (montage labels in artifacts/refs/mapillary/<region>/points/pNN.jpg); the ones that show
# the ADR 0069 furniture best (noise walls p37/p38/p43, gantry p37/p40, arrows/zebras p40/p42, guard rail + tree groups
# p26/p30/p55, signal mast arms p45/p47).
PHOTOS = {
    "p26": "1666299510882315", "p30": "316642919857450", "p37": "995780104564541", "p38": "1911352299378570",
    "p40": "1783751488818497", "p42": "1523897771888181", "p43": "494288258686575", "p45": "1026342955666337",
    "p47": "1050297706629492", "p55": "2895327727389806",
}
HFOV = {"richlv": 100.0, "kino": 78.0, "grobin": 90.0, "strudel": 72.0, "szurek": 70.0}   # WORKING_VALUE (deg)
ASPECT = 4 / 3


def manifest(region=REGION):
    m = {}
    p = REPO / "Data/raw/mapillary" / region / "manifest.jsonl"
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            m[r["id"]] = r
    return m


class Heights:
    def __init__(self, region=REGION):
        reg = REPO / "Data/Regions" / region
        terr = json.loads((reg / "terrain.json").read_text(encoding="utf-8"))
        self.ok = False
        hm = REPO / "Data/raw/derived" / region / "heightmap_2049.r16"
        if hm.exists():
            enc = terr["encoding"]
            self.n = int(terr["samples"][0])
            raw = np.fromfile(hm, "<u2").reshape(self.n, self.n)
            self.bbox = terr["bbox"]
            self.h = float(enc["offset_m"]) + raw.astype(np.float64) * float(enc["scale_m_per_unit"])
            self.ok = True

    def z(self, x, y):
        if not self.ok:
            return 140.0
        x0, y0, x1, y1 = self.bbox
        u = (x - x0) / (x1 - x0) * (self.n - 1)
        v = (y1 - y) / (y1 - y0) * (self.n - 1)
        i, j = int(np.clip(v, 0, self.n - 2)), int(np.clip(u, 0, self.n - 2))
        fv, fu = v - i, u - j
        h = self.h
        return float((h[i, j] * (1 - fu) + h[i, j + 1] * fu) * (1 - fv) + (h[i + 1, j] * (1 - fu) + h[i + 1, j + 1] * fu) * fv)


def cameras(out):
    m = manifest()
    H = Heights()
    cams = []
    for pid, img in PHOTOS.items():
        r = m[img]
        x, y = TO_PL.transform(r["lon"], r["lat"])
        e, n = x - OX, y - OY
        az = math.radians(r["compass_angle"])
        z = H.z(x, y) + 1.7
        hf = HFOV.get(r["author"], 75.0)
        vf = math.degrees(2 * math.atan(math.tan(math.radians(hf / 2)) / ASPECT))
        cams.append({"id": f"ph_{pid}", "type": "persp", "kind": "photo_match", "seat": "road",
                     "pos": [round(e, 3), round(n, 3), round(z, 3)],
                     "look_at": [round(e + 40 * math.sin(az), 3), round(n + 40 * math.cos(az), 3), round(z - 0.6, 3)],
                     "fov_deg": round(vf, 1), "mapillary_id": img, "author": r["author"], "captured_at": r["captured_at"],
                     "note": f"pose of Mapillary {img} ({r['author']}, {r['captured_at']}, CC BY-SA 4.0, reference only); "
                             f"hfov {hf} deg WORKING_VALUE"})
    doc = {"schema": "truck-sim-pl/gate3-cameras/1", "region": REGION,
           "frame": "local E,N,U (EPSG:2180 minus region origin; U = NMT + 1.7 m, re-seated on the road collision)",
           "heightmap_available": H.ok, "cameras": cams}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"{len(cams)} cameras -> {out} (heightmap {'yes' if H.ok else 'NO'})")


def _fit(im, w, h):
    """Centre-crop to w:h then resize."""
    sw, sh = im.size
    a = w / h
    if sw / sh > a:
        nw = int(sh * a)
        im = im.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:
        nh = int(sw / a)
        im = im.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    return im.resize((w, h), Image.LANCZOS)


def montage(render_dirs, labels, out, tile_w=300):
    m = manifest()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tile_h = int(tile_w / ASPECT)
    ncol = 1 + len(render_dirs)
    for pid, img in PHOTOS.items():
        tiles = [("Mapillary " + img[-6:] + " " + m[img]["captured_at"], Image.open(REPO / "Data/raw/mapillary" / REGION / m[img]["file"]))]
        for d, lab in zip(render_dirs, labels):
            f = Path(d) / f"ph_{pid}.png"
            if not f.exists():
                f = Path(d) / f"ph-{pid}.png"
            tiles.append((lab, Image.open(f) if f.exists() else Image.new("RGB", (4, 3), (40, 0, 0))))
        sheet = Image.new("RGB", (tile_w * ncol, tile_h + 16), (10, 10, 10))
        dr = ImageDraw.Draw(sheet)
        for k, (lab, im) in enumerate(tiles):
            sheet.paste(_fit(im.convert("RGB"), tile_w, tile_h), (k * tile_w, 16))
            dr.text((k * tile_w + 3, 2), f"{pid} {lab}", fill=(255, 255, 0))
        sheet.save(out / f"{pid}.jpg", quality=88)
    print("montages ->", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["cameras", "montage"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--renders", default="")
    ap.add_argument("--labels", default="")
    ap.add_argument("--tile", type=int, default=300)
    a = ap.parse_args()
    if a.cmd == "cameras":
        cameras(a.out)
    else:
        dirs = [d for d in a.renders.split(",") if d]
        labs = a.labels.split(",") if a.labels else [Path(d).name for d in dirs]
        montage(dirs, labs, a.out, a.tile)
