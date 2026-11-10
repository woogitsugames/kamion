"""World lighting / atmosphere metrics (ADR 0080): sky structure and gradient, tonal range, grass variation.

Per image (Rec.709 luma on sRGB values, %):
  p10 / p50 / p90      whole frame
  sky_top / sky_hor    mean luma of the sky pixels in the upper and the lowest third of the sky region
  sky_sigma            luma std-dev of the sky after removing the vertical gradient (cloud structure; 0 = flat dome)
  sky_sat              median HSV saturation of the sky (%)
  grass_sat / grass_sigma   green-hue pixels below the horizon: median saturation, luma std-dev at 16 px blocks (patches)
Sky mask: pixels connected to the top edge that are bright and low-chroma or blue (simple flood by rows; good enough for
street-level frames, same code for renders and photos).

usage:
  uv run --project tools/worldgen python scripts/light-metrics.py frames <dir> [<dir> ...] [--json out.json]
  uv run --project tools/worldgen python scripts/light-metrics.py scan <photo dir> [...] [--top 12]   # overcast candidates
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SKIP = ("cab-", "truck-", "trailer-", "hedge_")
EXT = (".png", ".jpg", ".jpeg")


def load(p: Path, width=640):
    im = Image.open(p).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.BILINEAR)
    return np.asarray(im, np.float32) / 255.0


def luma(a):
    return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) * 100.0


def sky_mask(a):
    y = luma(a)
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0)
    blue = (a[..., 2] >= a[..., 0]) & (a[..., 2] >= a[..., 1] - 0.02)
    cand = ((y > 55) & (sat < 0.16)) | ((y > 35) & blue & (sat < 0.75))
    h, w = y.shape
    m = np.zeros_like(cand)
    alive = np.ones(w, bool)
    for r in range(int(h * 0.75)):
        alive &= cand[r]
        # let a column re-join when its neighbours are sky (lamp posts, wires)
        if r % 4 == 0:
            nb = np.convolve(alive.astype(np.float32), np.ones(9) / 9, mode="same") > 0.6
            alive |= nb & cand[r]
        m[r] = alive
        if alive.mean() < 0.02:
            break
    return m


def stats(p: Path):
    a = load(p)
    y = luma(a)
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0) * 100
    out = {"p10": float(np.percentile(y, 10)), "p50": float(np.percentile(y, 50)), "p90": float(np.percentile(y, 90)),
           "clip": float((y > 98).mean() * 100)}
    m = sky_mask(a)
    out["sky_px"] = float(m.mean() * 100)
    if m.mean() > 0.04:
        rows = np.where(m.any(1))[0]
        r0, r1 = rows[0], rows[-1]
        third = max(1, (r1 - r0) // 3)
        top = y[r0:r0 + third][m[r0:r0 + third]]
        hor = y[r1 - third:r1 + 1][m[r1 - third:r1 + 1]]
        out["sky_top"], out["sky_hor"] = float(top.mean()), float(hor.mean())
        # structure: residual after the per-row mean (vertical gradient) is removed
        res = []
        for r in range(r0, r1 + 1):
            if m[r].sum() > 20:
                v = y[r][m[r]]
                res.append(v - v.mean())
        # plus the row-mean curve's departure from a straight line (banded layers)
        out["sky_sigma"] = float(np.concatenate(res).std()) if res else 0.0
        out["sky_sat"] = float(np.median(sat[m]))
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hue = (np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) + 360) % 360
    gm = (hue > 55) & (hue < 165) & (g >= r) & (g >= b) & ((mx - mn) > 0.04)
    gm[: int(a.shape[0] * 0.45)] = False
    out["grass_px"] = float(gm.mean() * 100)
    if gm.sum() > 600:
        out["grass_sat"] = float(np.median(sat[gm]))
        h, w = y.shape
        bl = []
        for by in range(0, h - 15, 16):
            for bx in range(0, w - 15, 16):
                k = gm[by:by + 16, bx:bx + 16]
                if k.mean() > 0.9:
                    bl.append(y[by:by + 16, bx:bx + 16].mean())
        out["grass_sigma"] = float(np.std(bl)) if len(bl) > 8 else float("nan")
    return out


def frames(dirs, out_json):
    res = []
    keys = ["p10", "p50", "p90", "clip", "sky_top", "sky_hor", "sky_sigma", "sky_sat", "grass_sat", "grass_sigma"]
    for d in dirs:
        d = Path(d)
        fr = {}
        for p in sorted(d.iterdir()):
            if p.suffix.lower() not in EXT or p.name.startswith(SKIP) or p.stem.endswith("_mask") or "envcube" in p.stem:
                continue
            fr[p.stem] = stats(p)
        mean = {}
        for k in keys:
            v = [f[k] for f in fr.values() if k in f and f[k] == f[k]]
            mean[k] = round(float(np.mean(v)), 2) if v else None
        res.append({"dir": str(d), "n": len(fr), "mean": mean, "frames": {k: {a: round(b, 2) for a, b in v.items()} for k, v in fr.items()}})
        print(f"{d}: n={len(fr)} " + " ".join(f"{k}={mean[k]}" for k in keys))
    if out_json:
        Path(out_json).write_text(json.dumps(res, indent=1))


def scan(dirs, top):
    rows = []
    for d in dirs:
        for p in sorted(Path(d).rglob("*")):
            if p.suffix.lower() not in EXT:
                continue
            try:
                s = stats(p)
            except Exception:
                continue
            if s.get("sky_px", 0) < 12 or "sky_sat" not in s:
                continue
            # overcast: grey sky (low chroma), no deep blue
            if s["sky_sat"] < 9:
                rows.append((s["sky_sigma"], p, s))
    rows.sort(key=lambda t: -t[0])
    print(f"overcast candidates: {len(rows)}")
    for sg, p, s in rows[:top]:
        print(f"{p} sky_px={s['sky_px']:.0f} top={s['sky_top']:.0f} hor={s['sky_hor']:.0f} sigma={sg:.1f} sat={s['sky_sat']:.1f} "
              f"p10={s['p10']:.0f} p50={s['p50']:.0f} p90={s['p90']:.0f} grass_sat={s.get('grass_sat', float('nan')):.0f}")
    if rows:
        for k in ("p10", "p50", "p90", "sky_top", "sky_hor", "sky_sigma", "sky_sat"):
            print(f"  median {k} = {np.median([r[2][k] for r in rows]):.1f}")
        gs = [r[2]["grass_sat"] for r in rows if "grass_sat" in r[2] and r[2]["grass_px"] > 3]
        gg = [r[2]["grass_sigma"] for r in rows if r[2].get("grass_sigma") == r[2].get("grass_sigma") and "grass_sigma" in r[2]]
        if gs:
            print(f"  median grass_sat = {np.median(gs):.1f} (n={len(gs)}), grass_sigma = {np.median(gg) if gg else float('nan'):.1f} (n={len(gg)})")


if __name__ == "__main__":
    args = sys.argv[1:]
    mode, args = args[0], args[1:]
    opt = {}
    for flag in ("--json", "--top"):
        if flag in args:
            i = args.index(flag)
            opt[flag] = args[i + 1]
            args = args[:i] + args[i + 2:]
    if mode == "frames":
        frames(args, opt.get("--json"))
    else:
        scan(args, int(opt.get("--top", 12)))
