"""Offline preview of plot-kit plants (ADR 0170 follow-up): a small software rasteriser that mimics Kamion/World PlotKit
(albedo = atlas * occlusion, normal from COLOR_0, alpha test 0.5, two-sided) - for judging SHAPE and OUTLINE before a
world build; the real check is the Unity render. Usage: uv run --project tools/worldgen python tools/worldgen/streetscape/preview_kit.py <out_dir>"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import plantings as PG  # noqa: E402
from streetscape import plot_kit as PK  # noqa: E402
from streetscape import plots as PLT  # noqa: E402

ATLAS = np.asarray(PK.atlas(), np.float32) / 255.0
SUN = np.array([0.45, -0.55, 0.70])
SUN = SUN / np.linalg.norm(SUN)


def render(kit, eye, at, fov=62.0, size=(900, 560), low=True, sky=(0.42, 0.60, 0.86)):
    W, H = size
    img = np.zeros((H, W, 3), np.float32)
    img[:] = sky
    img[H // 2 + 40:] = (0.30, 0.38, 0.20)
    zb = np.full((H, W), 1e9, np.float32)
    eye, at = np.asarray(eye, float), np.asarray(at, float)
    f = at - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    fl = (W / 2) / math.tan(math.radians(fov) / 2)
    for V, UV, T, C, L in zip(kit.V, kit.UV, kit.T, kit.C, kit.L):
        if (low and L is False) or (not low and L == "only"):
            continue
        d = V - eye
        cam = np.stack([d @ r, d @ u, d @ f], 1)
        for tri in T:
            p = cam[tri]
            if (p[:, 2] < 0.15).any():
                continue
            sx = W / 2 + p[:, 0] / p[:, 2] * fl
            sy = H / 2 - p[:, 1] / p[:, 2] * fl
            x0, x1 = int(max(math.floor(sx.min()), 0)), int(min(math.ceil(sx.max()), W - 1))
            y0, y1 = int(max(math.floor(sy.min()), 0)), int(min(math.ceil(sy.max()), H - 1))
            if x0 > x1 or y0 > y1:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
            if abs(den) < 1e-9:
                continue
            w0 = ((sy[1] - sy[2]) * (xs - sx[2]) + (sx[2] - sx[1]) * (ys - sy[2])) / den
            w1 = ((sy[2] - sy[0]) * (xs - sx[2]) + (sx[0] - sx[2]) * (ys - sy[2])) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            iz = w0 / p[0, 2] + w1 / p[1, 2] + w2 / p[2, 2]
            z = 1 / np.maximum(iz, 1e-9)
            b = np.stack([w0 / p[0, 2], w1 / p[1, 2], w2 / p[2, 2]], -1) * z[..., None]
            uv = b @ UV[tri]
            col = b @ C[tri]
            tx = np.clip((uv[..., 0] * PK.N).astype(int), 0, PK.N - 1)
            ty = np.clip(((1 - uv[..., 1]) * PK.N).astype(int), 0, PK.N - 1)
            tex = ATLAS[ty, tx]
            fol = col[..., 3] > 0.5
            n = col[..., :3] * 2 - 1
            nl = np.linalg.norm(n, axis=-1, keepdims=True)
            occ = np.clip(nl, 0, 1)
            n = n / np.maximum(nl, 1e-3)
            lam = np.clip(n @ SUN, 0, 1)[..., None]
            lit = 0.38 * np.array([0.8, 0.9, 1.0]) * (0.6 + 0.4 * n[..., 2:3]) + 0.85 * lam
            alb = np.where(fol[..., None], tex[..., :3] * occ, tex[..., :3] * col[..., :3] * 2)
            shade = np.where(fol[..., None], alb * lit, alb * 0.8)
            ok = inside & (tex[..., 3] >= 0.5) & (z < zb[y0:y1 + 1, x0:x1 + 1])
            sub = img[y0:y1 + 1, x0:x1 + 1]
            sub[ok] = shade[ok]
            zb[y0:y1 + 1, x0:x1 + 1][ok] = z[ok]
    out = np.clip(img, 0, 1) ** (1 / 2.2) if False else np.clip(img * 1.9, 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8))


def row(ims):
    sheet = Image.new("RGB", (sum(i.width for i in ims) + 4 * (len(ims) - 1), max(i.height for i in ims)), (20, 20, 20))
    x = 0
    for i in ims:
        sheet.paste(i, (x, 0))
        x += i.width + 4
    return sheet


def crown(key="t", species="maple", r=2.25, H=6.66, cb=1.3, low=True):
    kit = PLT.Kit()
    if not low:
        kit.low = False
        PG.garden_tree(kit, (0, 0), 0.0, r, H, cb, species, key, sprite=PG.HABIT[species])
        kit.low = "only"
    PG.garden_tree(kit, (0, 0), 0.0, r, H, cb, species, key, lite=True, cards=3, sprite=PG.HABIT[species], core=True)
    return kit


def hedge(low, h=3.0, L=16.0, key="h"):
    kit = PLT.Kit()
    PG.thuja_hedge(kit, np.array([0.0, 0.0]), np.array([L, 0.0]), np.array([0.0, -1.0]), lambda q: 0.0, h, key, thick=1.0, low=low,
                   raise_ends=(0.6, 0.0))
    return kit


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    S = (620, 520)
    for sp, key in (("maple", "t"), ("linden", "u"), ("ash", "w")):
        k = crown(key, sp)
        ims = [render(k, (4.4 * math.cos(a), 4.4 * math.sin(a), 1.7), (0, 0, 3.6), size=S) for a in (0.3, 2.2, 4.3)]
        ims.append(render(k, (14 * math.cos(1.0), 14 * math.sin(1.0), 1.7), (0, 0, 3.4), size=S))
        row(ims).save(out / f"crown_{sp}_low.jpg", quality=88)
        print(sp, "tris low", sum(len(t) for t, l in zip(k.T, k.L) if l is not False))
    for low in (True, False):
        k = hedge(low)
        ims = [render(k, (-3.0, -5.0, 1.7), (9.0, 0, 1.6), size=S, low=low), render(k, (8.0, -9.0, 1.7), (8.0, 0, 1.5), size=S, low=low),
               render(k, (5.0, -2.2, 1.7), (9.0, 0, 2.0), size=S, low=low)]
        row(ims).save(out / f"thuja_{'low' if low else 'high'}.jpg", quality=88)
        print("thuja", "low" if low else "high", "tris", sum(len(t) for t in k.T), "per m", sum(len(t) for t in k.T) / 16.0)
    for nm in ("spruce_a", "spruce_b", "thuja_a"):
        u0, u1, v0, v1 = PK.sprite(nm)
        a = PK.atlas().crop((int(u0 * PK.N), int((1 - v1) * PK.N), int(u1 * PK.N), int((1 - v0) * PK.N)))
        bg = Image.new("RGBA", a.size, (150, 185, 225, 255))
        bg.alpha_composite(a)
        bg.convert("RGB").save(out / f"sprite_{nm}.jpg", quality=90)
    k = PLT.Kit()
    PLT.spruce(k, np.array([0.0, 0.0]), 0.0, 9.0, "s")
    row([render(k, (12 * math.cos(a), 12 * math.sin(a), 1.7), (0, 0, 4.5), size=(420, 520)) for a in (0.2, 1.3)]).save(out / "spruce.jpg", quality=88)
