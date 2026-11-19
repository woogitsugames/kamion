"""ADR 0304: measure the edge-line spacing of a road at a tile seam on the GUGiK orthophoto (WMS HighResolution, 0.1 m).

The road axis is the one the generator builds (both tiles' networks, qa.seams.build_nets); every 0.5 m along
+-`--along` m from the seam a cross profile of brightness is sampled perpendicular to the axis (bilinear, 0.05 m step,
+-6 m). White paint = local brightness peaks above the asphalt median; on each side of the axis the strongest peak
between `--lo` and `--hi` m from the axis is the edge line. Output: per-profile positions, medians, spacing
(axis to axis of the two lines), a straightened strip image with the generator's lines drawn on it.

  uv run --project tools/worldgen python -m tools.worldgen.qa.seam_line_ortho <tile_a> <tile_b> <osm_way> <outdir>
        [--along 30] [--lo 2.4] [--hi 4.2]

The crop is cached in <outdir>/ortho_<x>_<y>.jpg (GUGiK orthophoto, open licence; Data/raw/refs is the place for
copies kept longer). Readings: WORKING_VALUE (+-0.1 m: 1 px).
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from tools.worldgen.qa import seams as Q

WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
RES = 0.1
HALF = 45.0


def fetch(x, y, out: Path, half=HALF, res=RES):
    f = out / f"ortho_{x:.0f}_{y:.0f}.jpg"
    if not f.exists():
        n = int(round(2 * half / res))
        q = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "Raster", "STYLES": "",
             "SRS": "EPSG:2180", "BBOX": f"{x - half},{y - half},{x + half},{y + half}", "WIDTH": n, "HEIGHT": n,
             "FORMAT": "image/jpeg"}
        url = WMS + "?" + urllib.parse.urlencode(q)
        for a in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "worldgen-qa/1.0"})
                data = urllib.request.urlopen(req, timeout=120).read()
                Image.open(io.BytesIO(data)).convert("RGB").save(f, quality=92)
                break
            except Exception as e:  # noqa: BLE001
                print("retry", e, file=sys.stderr)
                time.sleep(3 * (a + 1))
        else:
            raise SystemExit("WMS failed")
    im = np.asarray(Image.open(f).convert("L"), dtype=float)
    return im, (x - half, y + half)          # image origin: upper-left corner (E, N)


def sample(im, ul, pts):
    """Bilinear brightness at EPSG:2180 points (N x 2)."""
    c = (pts[:, 0] - ul[0]) / RES - 0.5
    r = (ul[1] - pts[:, 1]) / RES - 0.5
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    fc, fr = c - c0, r - r0
    h, w = im.shape
    c0, r0 = np.clip(c0, 0, w - 2), np.clip(r0, 0, h - 2)
    return (im[r0, c0] * (1 - fc) * (1 - fr) + im[r0, c0 + 1] * fc * (1 - fr) + im[r0 + 1, c0] * (1 - fc) * fr
            + im[r0 + 1, c0 + 1] * fc * fr)


def measure(a_id, b_id, way, out: Path, along=30.0, lo=2.4, hi=4.2):
    out.mkdir(parents=True, exist_ok=True)
    ta, tb = Q.load_tile(a_id), Q.load_tile(b_id)
    se = Q.shared_edge(ta.bbox, tb.bbox)
    nets = Q.build_nets([ta, tb], [(ta, tb, se)])
    axes = []
    for t in (ta, tb):
        net = nets[t.id]
        o = np.array(t.origin)
        for c in net.chains:
            ways = {net.sec_list[int(i)].edge_id.split(":")[0].lstrip("w") for i in np.unique(c.sec_idx)}
            if str(way) not in ways:
                continue
            for end in (0, -1):
                if Q._on_seam(c.line.p[end] + o, se):
                    axes.append((t, c, end, o))
    if not axes:
        raise SystemExit(f"w{way} does not cross the seam {a_id} | {b_id}")
    seam = axes[0][2] if False else axes[0][1].line.p[axes[0][2]] + axes[0][3]
    im, ul = fetch(float(seam[0]), float(seam[1]), out)
    off = np.arange(-6.0, 6.0001, 0.05)
    rows, strips = [], []
    for t, c, end, o in axes:
        s_end = float(c.line.s[end])
        sgn = 1.0 if end == 0 else -1.0
        hw = float(c.hw[end])
        for d in np.arange(1.0, along + 1e-6, 0.5):
            s = s_end + sgn * d
            if s < 0 or s > c.length:
                continue
            i = c.idx(s)
            p = c.line.point(s) + o
            nrm = c.line.n[i]
            prof = sample(im, ul, p[None, :] + off[:, None] * nrm[None, :])
            strips.append((t.id, d, prof))
            base = np.median(prof[np.abs(off) < hw - 0.6]) if hw > 1 else np.median(prof)
            pk = {}
            for side, sg in (("L", 1.0), ("R", -1.0)):
                m = (sg * off >= lo) & (sg * off <= hi)
                k = np.argmax(prof[m])
                pk[side] = (float(sg * off[m][k]), float(prof[m][k] - base))
            rows.append({"tile": t.id, "d_from_seam_m": round(float(d), 2), "L_m": round(pk["L"][0], 2),
                         "R_m": round(pk["R"][0], 2), "L_contrast": round(pk["L"][1], 1),
                         "R_contrast": round(pk["R"][1], 1), "spacing_m": round(pk["L"][0] + pk["R"][0], 2),
                         "hw_generator_m": round(hw, 3)})
    res = {"pair": [a_id, b_id], "osm_way": int(way), "seam_xy": [round(float(v), 2) for v in seam],
           "wms": WMS, "res_m": RES, "profiles": rows}
    for tid in {r["tile"] for r in rows}:
        rr = [r for r in rows if r["tile"] == tid and min(r["L_contrast"], r["R_contrast"]) >= 15]
        if rr:
            res.setdefault("median", {})[tid] = {
                "n": len(rr), "L_m": float(np.median([r["L_m"] for r in rr])),
                "R_m": float(np.median([r["R_m"] for r in rr])),
                "spacing_m": float(np.median([r["spacing_m"] for r in rr])),
                "spacing_p10_p90": [float(np.percentile([r["spacing_m"] for r in rr], q)) for q in (10, 90)]}
    (out / f"lines_w{way}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    # straightened strip: rows = profiles (tile a far -> seam -> tile b far), 0.05 m/px across, 2 px per 0.5 m
    order = sorted(strips, key=lambda s: (-s[1] if s[0] == a_id else s[1]))
    arr = np.array([s[2] for s in order])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((arr.shape[1] * 3, arr.shape[0] * 6),
                                                                      Image.NEAREST).convert("RGB")
    d = ImageDraw.Draw(img)
    for m in range(-6, 7):
        x = int((m + 6.0) / 0.05 * 3)
        d.line([(x, 0), (x, 10 if m % 5 else 22)], fill=(255, 0, 0), width=2)
    y_seam = sum(1 for s in order if s[0] == a_id) * 6
    d.line([(0, y_seam), (img.size[0], y_seam)], fill=(0, 160, 255), width=2)
    img.save(out / f"strip_w{way}.png")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("way"); ap.add_argument("out")
    ap.add_argument("--along", type=float, default=30.0)
    ap.add_argument("--lo", type=float, default=2.4)
    ap.add_argument("--hi", type=float, default=4.2)
    a = ap.parse_args(argv)
    r = measure(a.a, a.b, a.way.lstrip("w"), Path(a.out), a.along, a.lo, a.hi)
    print(json.dumps(r.get("median"), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
