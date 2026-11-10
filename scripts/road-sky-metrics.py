"""Road / sky / dark-tone metrics for overcast frames (ADR 0080 r11), same code for renders and street-level photos.

Per image (sRGB 8-bit, image resized to 640 px wide):
  sky       mean RGB of the sky mask (light-metrics.sky_mask)
  road      median RGB of the asphalt-like pixels (low chroma, below the horizon) in the road box
            (x 0.30-0.70, y 0.62-0.92 of the frame; --box to change)
  lt16/lt24 share of pixels with luma below 16 / 24 (crushed blacks)
  veg       10th percentile and median luma of the vegetation pixels (green or dark low-chroma pixels touching the sky band)
Photos: only overcast candidates are kept (sky share >= 12 %, sky saturation < 9 %), as in light-metrics scan.

usage:
  uv run --project tools/worldgen python scripts/road-sky-metrics.py photos <dir> [...]
  uv run --project tools/worldgen python scripts/road-sky-metrics.py frames <dir> [...] [--only id,id]
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("lm", Path(__file__).with_name("light-metrics.py"))
lm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lm)

BOX = (0.30, 0.62, 0.70, 0.92)


def measure(p: Path):
    a = lm.load(p)
    h, w, _ = a.shape
    y = lm.luma(a) * 2.55
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0)
    m = lm.sky_mask(a)
    out = {"sky_px": float(m.mean() * 100), "lt16": float((y < 16).mean() * 100), "lt24": float((y < 24).mean() * 100)}
    if m.mean() > 0.04:
        out["sky"] = a[m].mean(0) * 255
        out["sky_sat"] = float(np.median(sat[m]) * 100)
        # vegetation against the sky: non-sky pixels within 24 rows below a sky pixel of the same column, green or dark
        below = np.zeros_like(m)
        for s in range(1, 25):
            below[s:] |= m[:-s]
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        veg = below & ~m & (((g >= r) & (g >= b) & (mx - mn > 0.03)) | (y < 70)) & (y < 150)
        if veg.sum() > 400:
            out["veg_p10"], out["veg_p50"] = float(np.percentile(y[veg], 10)), float(np.percentile(y[veg], 50))
    x0, y0, x1, y1 = BOX
    box = a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].reshape(-1, 3)
    bs = sat[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].reshape(-1)
    by = y[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)].reshape(-1)
    k = (bs < 0.14) & (by < 200)      # asphalt-like: grey, not paint
    if k.mean() > 0.5:
        out["road"] = np.median(box[k], 0) * 255
        out["road_px"] = float(k.mean() * 100)
    return out


def fmt(v):
    return "/".join(f"{x:.0f}" for x in v)


def report(rows, title):
    print(f"{title}: n={len(rows)}")
    def med(key):
        v = [r[key] for r in rows if key in r]
        return (np.median(np.array(v), 0), len(v)) if v else (None, 0)
    for key in ("sky", "road"):
        v, n = med(key)
        if v is not None:
            print(f"  median {key} RGB {fmt(v)} (mean {np.mean(v):.0f}, B-R {v[2] - v[0]:+.0f}, n={n})")
            q = np.array([np.mean(r[key]) for r in rows if key in r])
            print(f"    {key} mean level p25/p50/p75 = {np.percentile(q, 25):.0f}/{np.percentile(q, 50):.0f}/{np.percentile(q, 75):.0f}")
    both = [(np.mean(r["road"]), np.mean(r["sky"])) for r in rows if "road" in r and "sky" in r]
    if both:
        d = np.array([s - r for r, s in both])
        print(f"  sky - road level: p25/p50/p75 = {np.percentile(d, 25):.0f}/{np.percentile(d, 50):.0f}/{np.percentile(d, 75):.0f} (n={len(d)})")
    for key in ("lt16", "lt24", "veg_p10", "veg_p50"):
        v, n = med(key)
        if v is not None:
            q = [r[key] for r in rows if key in r]
            print(f"  {key}: p25/p50/p75 = {np.percentile(q, 25):.1f}/{v:.1f}/{np.percentile(q, 75):.1f} (mean {np.mean(q):.1f}, n={n})")


if __name__ == "__main__":
    args = sys.argv[1:]
    mode, args = args[0], args[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = args[i + 1].split(","); args = args[:i] + args[i + 2:]
    if "--box" in args:
        i = args.index("--box"); BOX = tuple(float(x) for x in args[i + 1].split(",")); args = args[:i] + args[i + 2:]
    for d in args:
        rows = []
        files = sorted(Path(d).rglob("*")) if mode == "photos" else sorted(Path(d).iterdir())
        for p in files:
            if p.suffix.lower() not in lm.EXT or p.stem.endswith("_mask") or "envcube" in p.stem:
                continue
            if mode == "frames" and (p.name.startswith(lm.SKIP) or (only and p.stem not in only)):
                continue
            try:
                s = measure(p)
            except Exception:
                continue
            if mode == "photos" and (s["sky_px"] < 12 or s.get("sky_sat", 99) >= 9):
                continue
            rows.append(s)
            if mode == "frames":
                print(f"  {p.stem[:30]:30s} sky {fmt(s['sky']) if 'sky' in s else '-':12s} road {fmt(s['road']) if 'road' in s else '-':12s} "
                      f"lt16 {s['lt16']:.1f} lt24 {s['lt24']:.1f} veg {s.get('veg_p10', float('nan')):.0f}/{s.get('veg_p50', float('nan')):.0f}")
        report(rows, d)
