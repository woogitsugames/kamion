"""N-2 dark accents metric (review r7 §0 / §10, ADR 0060): per-frame Rec.709 luma (on sRGB values, %) percentiles of the
WorldC control-camera set, mean over the world cameras (cab-* / truck-* excluded, as in the review's 41-camera set).

usage: uv run --project tools/worldgen python scripts/dark-accents.py <render dir> [<render dir> ...] [--json out.json]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SKIP = ("cab-", "truck-", "hedge_")


def luma(a):
    return (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]) * 100.0


def frame_stats(p: Path, width=1024):
    im = Image.open(p).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.BILINEAR)
    a = np.asarray(im, np.float32) / 255.0
    y = luma(a)
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0) * 100
    # grass (D38): green-hue pixels (hue 60-160 deg, G the largest channel, chroma > 0.04) below the horizon half
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hue = (np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) + 360) % 360
    gm = (hue > 60) & (hue < 160) & (g >= r) & (g >= b) & ((mx - mn) > 0.04)
    gm[: int(a.shape[0] * 0.45)] = False
    gsat = float(np.median(sat[gm])) if gm.sum() > 400 else float("nan")
    return {"grass_sat": gsat, "grass_px": float(gm.mean() * 100), "p05": float(np.percentile(y, 5)), "p10": float(np.percentile(y, 10)), "p50": float(np.percentile(y, 50)),
            "lt28": float((y < 28).mean() * 100), "sat50": float(np.median(sat))}


def set_stats(d: Path):
    frames = {}
    for p in sorted(d.glob("*.png")):
        if p.name.startswith(SKIP) or p.stem.endswith("_mask") or "envcube" in p.stem:
            continue
        frames[p.stem] = frame_stats(p)
    keys = ["p05", "p10", "p50", "lt28", "sat50"]
    mean = {k: round(float(np.mean([f[k] for f in frames.values()])), 2) for k in keys}
    gs = [f["grass_sat"] for f in frames.values() if f["grass_sat"] == f["grass_sat"] and f["grass_px"] > 2.0]
    mean["grass_sat"] = round(float(np.mean(gs)), 2) if gs else None
    mean["grass_frames"] = len(gs)
    return {"dir": str(d), "n": len(frames), "mean": mean,
            "p50_min": round(min(f["p50"] for f in frames.values()), 1),
            "p50_max": round(max(f["p50"] for f in frames.values()), 1),
            "frames": {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in frames.items()}}


if __name__ == "__main__":
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        i = args.index("--json")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    res = [set_stats(Path(a)) for a in args]
    for r in res:
        print(f"{r['dir']}: n={r['n']} mean {r['mean']} p50 {r['p50_min']}-{r['p50_max']}")
    if out:
        Path(out).write_text(json.dumps(res, indent=1))
