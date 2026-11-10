"""Pixel classification on the orthophoto: Lab colour, road-colour model learnt from the generated carriageway
interior, road / vegetation masks, lane-line (bright paint) mask. All thresholds are WORKING_VALUE, tuned by eye on
the overlays (artifacts/fidelity-r9/overlays) and listed in DIFFS / ADR 0075 with their failure modes."""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

# WORKING_VALUE thresholds
CHROMA_W = 2.0            # chroma weight in the road-colour distance (grass / soil separate by chroma)
DIST_MIN, DIST_MAX = 9.0, 16.0
EXG_GREEN = 0.06          # excess-green index above which a pixel is vegetation
PAINT_DL = 22.0           # paint is this much lighter (L*) than the local road colour
CAR_HOLE_M2 = 14.0        # non-road blobs fully inside road and smaller than this are cars / shadows / paint


def rgb2lab(rgb):
    a = np.asarray(rgb, np.float32) / 255.0
    a = np.where(a > 0.04045, ((a + 0.055) / 1.055) ** 2.4, a / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]], np.float32)
    xyz = a @ M.T / np.array([0.95047, 1.0, 1.08883], np.float32)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16
    A = 500 * (f[..., 0] - f[..., 1])
    B = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, A, B], -1)


def exg(rgb):
    a = np.asarray(rgb, np.float32)
    s = a.sum(-1) + 1e-3
    return (2 * a[..., 1] - a[..., 0] - a[..., 2]) / s


def _dist(lab, centers):
    d = None
    for c in centers:
        dd = np.sqrt((lab[..., 0] - c[0]) ** 2 + CHROMA_W * ((lab[..., 1] - c[1]) ** 2 + (lab[..., 2] - c[2]) ** 2))
        d = dd if d is None else np.minimum(d, dd)
    return d


def road_model(lab, sample_mask, k=3, seed_quantiles=(0.2, 0.5, 0.8)):
    """k-means (deterministic init on L* quantiles) on road-interior samples without paint and deep shadow."""
    s = lab[sample_mask]
    if len(s) < 200:
        return None
    L = s[:, 0]
    lo, hi = np.percentile(L, [8, 88])
    s = s[(L >= lo) & (L <= hi)]
    if len(s) > 40000:
        s = s[np.linspace(0, len(s) - 1, 40000).astype(int)]
    cen = np.array([np.median(s[np.abs(s[:, 0] - np.quantile(s[:, 0], q)) < 3], axis=0)
                    if (np.abs(s[:, 0] - np.quantile(s[:, 0], q)) < 3).any() else s.mean(0) for q in seed_quantiles])
    for _ in range(12):
        d = np.stack([np.sqrt(((s - c) ** 2 * [1, CHROMA_W, CHROMA_W]).sum(1)) for c in cen], 1)
        lab_ = d.argmin(1)
        cen = np.array([s[lab_ == i].mean(0) if (lab_ == i).any() else cen[i] for i in range(len(cen))])
    share = np.bincount(lab_, minlength=len(cen)) / len(s)
    cen = cen[share >= 0.12]
    d = _dist(s, cen)
    thr = float(np.clip(2.5 * np.median(d), DIST_MIN, DIST_MAX))
    return {"centers": cen, "thr": thr, "L_med": float(np.median(s[:, 0]))}


def disk(r_px):
    r = max(1, int(round(r_px)))
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def road_mask(rgb, gen_mask, res):
    """(road, green, paint, model) masks for a north-up window. `gen_mask` = generated carriageway raster used
    only to learn the road colour (interior >= 1 m from its edge) and to keep road components touching it."""
    lab = rgb2lab(rgb)
    interior = ndi.binary_erosion(gen_mask, structure=disk(1.0 / res))
    green = exg(rgb) > EXG_GREEN
    model = road_model(lab, interior & ~green)
    if model is None:
        z = np.zeros(gen_mask.shape, bool)
        return z, green, z, None
    d = _dist(lab, model["centers"])
    raw = (d < model["thr"]) & ~green
    paint = (lab[..., 0] > model["L_med"] + PAINT_DL) & (np.abs(lab[..., 1]) < 12) & (np.abs(lab[..., 2]) < 18)
    m = raw | paint
    m = ndi.binary_opening(m, structure=disk(0.3 / res))
    m = ndi.binary_closing(m, structure=disk(0.35 / res))
    # fill small enclosed non-road blobs (cars, shadows, manholes) – never vegetation
    holes = ~m
    lbl, n = ndi.label(holes)
    if n:
        area = ndi.sum(np.ones_like(lbl), lbl, index=np.arange(1, n + 1)) * res * res
        gfrac = ndi.mean(green, lbl, index=np.arange(1, n + 1))
        touch = np.zeros(n + 1, bool)
        for edge in (lbl[0], lbl[-1], lbl[:, 0], lbl[:, -1]):
            touch[np.unique(edge)] = True
        fill = np.zeros(n + 1, bool)
        fill[1:] = (area < CAR_HOLE_M2) & (gfrac < 0.15) & ~touch[1:]
        m |= fill[lbl]
    # keep only components touching the generated interior (drops roofs, yards far from the road)
    lbl, n = ndi.label(m)
    keep = np.zeros(n + 1, bool)
    keep[np.unique(lbl[interior & m])] = True
    keep[0] = False
    m = keep[lbl]
    return m, green, paint & m, dict(model, dist=d)
