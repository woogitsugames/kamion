"""Hole test of the parked-vehicle prototypes (REVIEW r7 N-13: "every variant x LOD rendered from 8 directions on a
contrasting background has 0 background pixels inside the silhouette").

Software z-buffer, orthographic, the engine's rules: opaque materials draw front faces only, the glass sheet
(`car_glass_tint`, Cull Off, blended) and the road-film overlays never hide anything. A pixel is a defect when
  see_through : the ray meets no opaque front face and enters or leaves the body through the BACK of an opaque
                panel (first or last surface on the ray; the paving shows through the body), or
  exposed     : the nearest opaque front face is the cabin (`car_interior`) with no glass in front of it.
Rays that cross glass only (in at one window, out at another) are the legitimate view through the greenhouse.

  uv run --project tools/worldgen python tools/worldgen/qa/car_holes_qa.py [--out DIR] [--res 0.025] [--proto NAME]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streetscape import life_cars as LC  # noqa: E402

SEE_THROUGH = ("car_glass_tint",)
OVERLAY = ("car_dirt_",)
AZIMUTHS = [k * 45.0 for k in range(8)]
ELEVATIONS = [8.0, 30.0, 55.0]


def view_basis(az, el):
    a, e = math.radians(az), math.radians(el)
    d = -np.array([math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)])      # view direction
    right = np.cross(d, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, d)
    return right, up, d


def raster(mesh, az, el, res=0.025):
    """-> kind per pixel: 0 background, 1 body, 2 glass only, 3 see_through, 4 exposed."""
    right, up, d = view_basis(az, el)
    prims = [p for p in mesh.out() if not p["mat"].startswith(OVERLAY)]
    allv = np.concatenate([p["V"] for p in prims])
    u, v = allv @ right, allv @ up
    u0, v0 = u.min() - 2 * res, v.min() - 2 * res
    W, H = int((u.max() - u0) / res) + 3, int((v.max() - v0) / res) + 3
    zf = np.full((H, W), np.inf)            # nearest opaque front face
    zg = np.full((H, W), np.inf)            # nearest glass
    zi = np.full((H, W), np.inf)            # nearest opaque front face that is cabin
    zg1 = np.full((H, W), -np.inf)          # farthest glass
    zb0 = np.full((H, W), np.inf)           # nearest / farthest opaque back face
    zb1 = np.full((H, W), -np.inf)
    for p in prims:
        V = p["V"]
        P = np.column_stack([(V @ right - u0) / res, (V @ up - v0) / res, V @ d])
        glass = p["mat"] in SEE_THROUGH
        cabin = p["mat"] == "car_interior"
        for t in p["T"]:
            a, b, c = P[t[0]], P[t[1]], P[t[2]]
            area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(area) < 1e-9:
                continue
            # (right, up) seen along d: right x up = -d, so a triangle whose outward normal faces the eye
            # (counter-clockwise for the viewer) has POSITIVE area here
            front = area > 0
            x0, x1 = int(math.floor(min(a[0], b[0], c[0]))), int(math.ceil(max(a[0], b[0], c[0])))
            y0, y1 = int(math.floor(min(a[1], b[1], c[1]))), int(math.ceil(max(a[1], b[1], c[1])))
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((b[0] - xs) * (c[1] - ys) - (b[1] - ys) * (c[0] - xs)) / area
            w1 = ((c[0] - xs) * (a[1] - ys) - (c[1] - ys) * (a[0] - xs)) / area
            w2 = 1 - w0 - w1
            ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not ins.any():
                continue
            z = w0 * a[2] + w1 * b[2] + w2 * c[2]
            sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
            if glass:
                zg[sl] = np.where(ins, np.minimum(zg[sl], z), zg[sl])
                zg1[sl] = np.where(ins, np.maximum(zg1[sl], z), zg1[sl])
            elif front:
                zf[sl] = np.where(ins, np.minimum(zf[sl], z), zf[sl])
                if cabin:
                    zi[sl] = np.where(ins, np.minimum(zi[sl], z), zi[sl])
            else:
                zb0[sl] = np.where(ins, np.minimum(zb0[sl], z), zb0[sl])
                zb1[sl] = np.where(ins, np.maximum(zb1[sl], z), zb1[sl])
    kind = np.zeros((H, W), np.uint8)
    has_f, has_g = np.isfinite(zf), np.isfinite(zg)
    kind[has_g] = 2
    kind[has_f] = 1
    # linings behind a pane are culled from outside: only the first / last surface on the ray decides
    kind[~has_f & np.isfinite(zb0) & ((zb0 < zg) | (zb1 > zg1))] = 3
    kind[has_f & (zi <= zf + 1e-9) & ~(zg < zf)] = 4
    return kind


def erode(mask, n=1):
    for _ in range(n):
        m = mask.copy()
        m[1:] &= mask[:-1]
        m[:-1] &= mask[1:]
        m[:, 1:] &= mask[:, :-1]
        m[:, :-1] &= mask[:, 1:]
        mask = m
    return mask


def defects(mesh, res=0.025, azimuths=AZIMUTHS, elevations=ELEVATIONS, images=None, tag=""):
    """-> {(az, el): (see_through cm2, exposed cm2)}; only blobs that survive a 1 px erosion count (>= 3 px wide:
    = 75 mm at the default 25 mm pixel;
    thinner seams between abutting panels are below what the test resolves)."""
    out = {}
    for el in elevations:
        for az in azimuths:
            k = raster(mesh, az, el, res)
            st, ex = erode(k == 3), erode(k == 4)
            out[(az, el)] = (float(st.sum()) * res * res * 1e4, float(ex.sum()) * res * res * 1e4)
            if images is not None and (st.any() or ex.any()):
                from PIL import Image
                pal = np.array([[255, 0, 255], [70, 70, 70], [150, 190, 210], [255, 255, 0], [255, 120, 0]], np.uint8)
                Image.fromarray(pal[k][::-1]).save(Path(images) / f"{tag}_az{int(az):03d}_el{int(el):02d}.png")
    return out


def prototypes():
    for b in LC.CARS:
        for c in LC.CAR_COLOURS:
            yield f"car_{b}_{c}", LC.car(b, c)
    for c in LC.VAN_COLOURS:
        yield f"van_{c}", LC.van(c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--res", type=float, default=0.025)
    ap.add_argument("--proto", default=None)
    a = ap.parse_args()
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
    rep, bad = {}, 0
    for name, P in prototypes():
        if a.proto and a.proto not in name:
            continue
        for lod, m in ((0, P[0]), (1, P[1]), (2, P[3])):
            d = defects(m, a.res, images=a.out, tag=f"{name}_lod{lod}")
            st = max(v[0] for v in d.values())
            ex = max(v[1] for v in d.values())
            worst = max(d, key=lambda k: d[k][0] + d[k][1])
            rep[f"{name}.lod{lod}"] = {"see_through_cm2_max": round(st, 1), "exposed_cm2_max": round(ex, 1),
                                      "worst_view_az_el": worst,
                                      "views_with_defect": sum(1 for v in d.values() if v[0] + v[1] > 0)}
            bad += st + ex > 0
            print(f"{name}.lod{lod}: see_through {st:8.1f} cm2  exposed {ex:8.1f} cm2  worst az/el {worst}", flush=True)
    if a.out:
        (Path(a.out) / "car_holes.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(f"{bad} of {len(rep)} meshes with defects")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
