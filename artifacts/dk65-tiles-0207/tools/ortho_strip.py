"""ADR 0207: straightened orthophoto strip along the DK65 route of a tile + automatic asphalt-width estimate.

Usage (repo root):
  uv run --project tools/worldgen python artifacts/dk65-tiles-0207/tools/ortho_strip.py --region dk65-02 [--plan <plan.json>]

Reads Data/raw/derived/<id>/ortho_0p25m.tif (GUGiK ortho 0.25 m; QA reference only, never a texture) and the route
polyline (Data/Regions/<id>/route_start.json if present, else variant A polyline of the ADR 0203 plan clipped to the
tile). Writes artifacts/dk65-tiles-0207/<id>/ortho/strip_<s0>.jpg (120 m chunks, travel left->right, +-15 m, 2x) and
width.json (per-station asphalt width estimate: grow from the axis over asphalt-grey or white-paint pixels, gaps
<= 0.5 m; median per 50 m over stations not rejected as shadow/vegetation). Reading accuracy ~ +-0.3 m (WORKING_VALUE).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts" / "dk65-tiles-0207"
PLAN = ROOT / "docs" / "reports" / "map" / "dk65_route_plan.json"


def resample(pl, step):
    pl = np.asarray(pl, float)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pl, axis=0).T))]
    s = np.arange(0, d[-1], step)
    x = np.interp(s, d, pl[:, 0]); y = np.interp(s, d, pl[:, 1])
    return s, np.c_[x, y]


def clip_to_bbox(pl, bb, margin=0.0):
    pl = np.asarray(pl, float)
    inside = (pl[:, 0] >= bb[0] - margin) & (pl[:, 0] <= bb[2] + margin) & (pl[:, 1] >= bb[1] - margin) & (pl[:, 1] <= bb[3] + margin)
    idx = np.where(inside)[0]
    if len(idx) == 0:
        return pl[:0]
    lo, hi = max(idx[0] - 1, 0), min(idx[-1] + 2, len(pl))
    return pl[lo:hi]


def route_polyline(region, bb, plan_path):
    rs = ROOT / "Data" / "Regions" / region / "route_start.json"
    if rs.exists():
        r = json.loads(rs.read_text(encoding="utf-8"))
        for k in ("polyline_epsg2180", "polyline", "points_epsg2180"):
            if k in r:
                return np.asarray(r[k], float)[:, :2], "route_start.json"
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    pl = plan["variants"]["A_old_road"]["polyline"]
    return clip_to_bbox(pl, bb, 30.0), "plan A polyline"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--plan", default=str(PLAN))
    ap.add_argument("--half", type=float, default=15.0)
    ap.add_argument("--chunk", type=float, default=120.0)
    a = ap.parse_args()
    reg = json.loads((ROOT / "Data" / "Regions" / a.region / "ortho.json").read_text(encoding="utf-8"))
    bb = reg["bounds"]
    pl, src = route_polyline(a.region, bb, a.plan)
    ds = rasterio.open(ROOT / reg["file"])
    img = ds.read()[:3].transpose(1, 2, 0)
    inv = ~ds.transform
    s, P = resample(pl, 0.25)
    # tangent / normal (normal points to the LEFT of travel)
    t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    nrm = np.c_[-t[:, 1], t[:, 0]]
    lat = np.arange(a.half, -a.half - 1e-6, -0.25)  # row 0 = left side (+half)
    X = P[:, 0][None, :] + lat[:, None] * nrm[:, 0][None, :]
    Y = P[:, 1][None, :] + lat[:, None] * nrm[:, 1][None, :]
    c, r = inv * (X, Y)
    from scipy.ndimage import map_coordinates
    strip = np.stack([map_coordinates(img[:, :, b].astype(float), [r - 0.5, c - 0.5], order=1, mode="nearest") for b in range(3)], axis=-1).clip(0, 255).astype(np.uint8)
    inb = (X >= bb[0]) & (X <= bb[2]) & (Y >= bb[1]) & (Y <= bb[3])
    strip[~inb] = 0
    od = OUT / a.region / "ortho"; od.mkdir(parents=True, exist_ok=True)
    # --- width estimate per 1 m station
    f = strip.astype(float)
    lum = f.mean(axis=2); sat = f.max(axis=2) - f.min(axis=2)
    ic = len(lat) // 2
    res = []
    for k in range(0, strip.shape[1], 4):
        if not inb[ic, k]:
            continue
        col_l, col_s = lum[:, k], sat[:, k]
        core = np.r_[ic - 8:ic - 2, ic + 3:ic + 9]
        ref = np.median(col_l[core]); rs_ = np.median(col_s[core])
        if rs_ > 28 or ref < 45:     # vegetation / deep shadow on the axis
            res.append((s[k], None, None)); continue
        road = ((np.abs(col_l - ref) < 32) & (col_s < 26)) | ((col_l > ref + 40) & (col_s < 30))

        def grow(sign):
            i, gap, last = ic, 0, ic
            while 0 <= i + sign < len(lat):
                i += sign
                if road[i]:
                    last, gap = i, 0
                else:
                    gap += 1
                    if gap > 2:
                        break
            return abs(lat[last]) + 0.125
        res.append((s[k], round(grow(-1), 2), round(grow(1), 2)))  # grow(-1): towards row 0 = left
    rows = []
    for s0 in np.arange(0, s[-1], 50.0):
        w = [l + r_ for (ss, l, r_) in res if l is not None and s0 <= ss < s0 + 50 and l < 9 and r_ < 9]
        lw = [l for (ss, l, r_) in res if l is not None and s0 <= ss < s0 + 50 and l < 9]
        rw = [r_ for (ss, l, r_) in res if l is not None and s0 <= ss < s0 + 50 and r_ < 9]
        rows.append({"s0": float(s0), "n": len(w), "width_med": round(float(np.median(w)), 2) if w else None,
                     "p25": round(float(np.percentile(w, 25)), 2) if w else None, "p75": round(float(np.percentile(w, 75)), 2) if w else None,
                     "left_med": round(float(np.median(lw)), 2) if lw else None, "right_med": round(float(np.median(rw)), 2) if rw else None})
    xy_every_50 = [[round(float(v), 1) for v in P[int(min(i, len(P) - 1))]] for i in np.arange(0, len(P), 200)]
    (od / "width.json").write_text(json.dumps({"region": a.region, "route_source": src, "length_m": round(float(s[-1]), 1),
        "method": "grow from axis over asphalt-grey/white-paint pixels, gap<=0.5 m; 0.25 m/px; +-0.3 m", "per_50m": rows,
        "xy_every_50m": xy_every_50}, indent=1), encoding="utf-8")
    # --- strips: chunk images, 2x, scale ticks every 1 m on a ruler, axis marked
    for s0 in np.arange(0, s[-1], a.chunk):
        k0, k1 = int(s0 / 0.25), int(min(s[-1], s0 + a.chunk) / 0.25)
        im = Image.fromarray(strip[:, k0:k1]).resize(((k1 - k0) * 2, len(lat) * 2), Image.NEAREST)
        W, H = im.size
        canvas = Image.new("RGB", (W, H + 40), (255, 255, 255)); canvas.paste(im, (0, 20))
        d = ImageDraw.Draw(canvas)
        for m in range(-int(a.half), int(a.half) + 1):
            yy = 20 + int((a.half - m) / 0.25 * 2)
            d.line([(0, yy), (6 if m % 5 else 14, yy)], fill=(255, 0, 0))
        for m in range(0, int(k1 - k0) // 4 + 1, 10):
            d.text((m * 8, 2), f"{int(s0 + m)}", fill=(0, 0, 0))
        d.text((4, H + 22), f"{a.region} s {int(s0)}-{int(s0 + a.chunk)} m; left=row top; ticks 1 m (long 5 m); 0.25 m/px x2; GUGiK orto 2024", fill=(0, 0, 0))
        canvas.save(od / f"strip_{int(s0):04d}.jpg", quality=90)
    print(json.dumps(rows))


if __name__ == "__main__":
    main()


def xsec(region, plan=str(PLAN), chunk=50.0, half=12.0):
    """Median lateral colour profile per `chunk` m (rows) -> artifacts/.../ortho/xsec.jpg + peaks in xsec.json.
    Columns: lateral offset -half..+half m (left of travel = left of image), 0.25 m/px x8; ruler every 1 m.
    Peaks = white paint (lum local max >= 18 above the profile median within +-1.5 m)."""
    reg = json.loads((ROOT / "Data" / "Regions" / region / "ortho.json").read_text(encoding="utf-8"))
    bb = reg["bounds"]
    pl, src = route_polyline(region, bb, plan)
    ds = rasterio.open(ROOT / reg["file"])
    img = ds.read()[:3].transpose(1, 2, 0)
    inv = ~ds.transform
    s, P = resample(pl, 0.5)
    t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    nrm = np.c_[-t[:, 1], t[:, 0]]
    lat = np.arange(half, -half - 1e-6, -0.25)
    X = P[:, 0][None, :] + lat[:, None] * nrm[:, 0][None, :]
    Y = P[:, 1][None, :] + lat[:, None] * nrm[:, 1][None, :]
    c, r = inv * (X, Y)
    inb = (X >= bb[0]) & (X <= bb[2]) & (Y >= bb[1]) & (Y <= bb[3])
    from scipy.ndimage import map_coordinates  # bilinear: nearest sampling of a straight diagonal road aliases into stripes
    strip = np.stack([map_coordinates(img[:, :, b].astype(float), [r - 0.5, c - 0.5], order=1, mode="nearest") for b in range(3)], axis=-1)
    rows, out = [], []
    for s0 in np.arange(0, s[-1], chunk):
        m = (s >= s0) & (s < s0 + chunk) & inb[len(lat) // 2]
        if m.sum() < 10:
            continue
        sub = strip[:, m]
        lum = sub.mean(axis=2)
        # reject shadowed stations (axis darker than 70) before the median
        ok = np.median(lum[len(lat) // 2 - 6:len(lat) // 2 + 7], axis=0) > 70
        if ok.sum() < 10:
            ok[:] = True
        prof = np.median(sub[:, ok], axis=1)  # (lat,3)
        rows.append(prof)
        L = prof.mean(axis=1)
        base = np.array([np.median(L[max(0, i - 6):i + 7]) for i in range(len(L))])
        pk = [round(float(-lat[i]), 2) for i in range(1, len(L) - 1) if L[i] >= L[i - 1] and L[i] >= L[i + 1] and L[i] - base[i] >= 18]
        out.append({"s0": float(s0), "stations": int(ok.sum()), "paint_peaks_m_right_positive": pk})
    if not rows:
        return
    A = np.stack(rows).clip(0, 255).astype(np.uint8)  # (chunks, lat, 3)
    im = Image.fromarray(A).resize((A.shape[1] * 8, A.shape[0] * 14), Image.NEAREST)
    W, H = im.size
    canvas = Image.new("RGB", (W + 60, H + 30), (255, 255, 255)); canvas.paste(im, (60, 20))
    d = ImageDraw.Draw(canvas)
    for mm in range(-int(half), int(half) + 1):
        xx = 60 + int((half + mm) / 0.25 * 8)
        d.line([(xx, 10), (xx, 20 if mm % 5 else 4)], fill=(255, 0, 0)); d.text((xx - 4, H + 20), str(mm), fill=(0, 0, 0))
    for k, o in enumerate(out):
        d.text((2, 20 + k * 14), f"{int(o['s0'])}", fill=(0, 0, 0))
    canvas.save(ROOT / "artifacts" / "dk65-tiles-0207" / region / "ortho" / "xsec.jpg", quality=92)
    (ROOT / "artifacts" / "dk65-tiles-0207" / region / "ortho" / "xsec.json").write_text(json.dumps(
        {"region": region, "route_source": src, "chunk_m": chunk, "offset_sign": "+ = right of travel", "rows": out}, indent=1), encoding="utf-8")
