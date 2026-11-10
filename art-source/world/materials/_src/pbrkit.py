"""Small numpy toolkit for tileable PBR surface sets (world C ground materials).

Everything here is periodic by construction (FFT noise, periodic KD-tree Voronoi, wrap-mode filters), so every
texture tiles without seams. Units: metres. Arrays are indexed [row, col]; col = +u (east), row grows downwards,
i.e. against +v. Normal maps are tangent space, OpenGL convention (+Y = +v), which is what Unity and glTF expect.

Output packing (URP Lit conventions):
  BaseColor  sRGB RGB (alpha only for decals)
  Normal     linear RGB, OpenGL (+Y)
  MaskMap    R metallic, G occlusion, B detail mask, A smoothness
  Var        R height (0..1 over the set's height range), G per-element random id, B joint/crack mask (water, dirt,
             weeds), A convexity / edge wear
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.fft import fft2, ifft2, fftfreq
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
TIERS = {"High": 1, "Medium": 2, "Low": 4}   # downsample factor from the generation resolution


# ----------------------------------------------------------------------------------------------- basic fields
@dataclass
class Ctx:
    nx: int
    ny: int
    Lx: float
    Ly: float
    seed: int
    _xy: tuple | None = field(default=None, repr=False)

    @property
    def px(self) -> float:
        return self.Lx / self.nx

    def xy(self):
        """Pixel-centre coordinates in metres (x east, y = metres from the top row, growing downwards)."""
        if self._xy is None:
            x = (np.arange(self.nx, dtype=np.float32) + 0.5) * (self.Lx / self.nx)
            y = (np.arange(self.ny, dtype=np.float32) + 0.5) * (self.Ly / self.ny)
            self._xy = np.meshgrid(x, y)
        return self._xy

    def rng(self, k: int) -> np.random.Generator:
        return np.random.default_rng(self.seed * 1000 + k)


def noise(c: Ctx, k: int, wl_min: float, wl_max: float, beta: float = 1.0, aniso: float = 1.0) -> np.ndarray:
    """Periodic band-limited noise (zero mean, unit std). Wavelengths in metres; beta = spectral slope of the
    amplitude (1 = pink). aniso > 1 stretches features along x (e.g. broom texture)."""
    w = c.rng(k).standard_normal((c.ny, c.nx)).astype(np.float32)
    fx = fftfreq(c.nx, d=c.Lx / c.nx)       # cycles per metre
    fy = fftfreq(c.ny, d=c.Ly / c.ny)
    FX, FY = np.meshgrid(fx, fy)
    f = np.sqrt((FX * aniso) ** 2 + FY ** 2)
    f[0, 0] = 1e-6
    fmin, fmax = 1.0 / wl_max, 1.0 / wl_min
    amp = f ** (-beta) * (1 - np.exp(-(f / fmin) ** 4)) * np.exp(-(f / fmax) ** 4)
    amp[0, 0] = 0
    r = np.real(ifft2(fft2(w) * amp)).astype(np.float32)
    return (r - r.mean()) / (r.std() + 1e-9)


def blur(a: np.ndarray, sigma_px: float) -> np.ndarray:
    return ndimage.gaussian_filter(a, sigma_px, mode="wrap")


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _mix64(h):
    h = (h ^ (h >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    h = (h ^ (h >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return h ^ (h >> np.uint64(31))


def hash01(*ints) -> np.ndarray:
    """Deterministic per-element random in [0,1) from integer arrays (each input fully mixed: SplitMix64)."""
    with np.errstate(over="ignore"):
        h = np.full(np.broadcast(*ints).shape, 0x2545F4914F6CDD1D, np.uint64)
        for i, a in enumerate(ints):
            x = np.asarray(a).astype(np.int64).astype(np.uint64) + np.uint64((0x9E3779B97F4A7C15 * (i + 1)) % 2**64)
            h = _mix64(h ^ _mix64(x))
    return ((h >> np.uint64(11)).astype(np.float64) / float(2**53)).astype(np.float32)


def voronoi(c: Ctx, k: int, cell: float, jitter: float = 1.0, warp=None, cell_y: float | None = None):
    """Periodic Voronoi. Returns d1, d2 (metres), index of nearest and second-nearest site, and n sites.
    warp = (wx, wy) offsets in metres added to the lookup position."""
    cy = cell_y or cell
    mx, my = max(1, round(c.Lx / cell)), max(1, round(c.Ly / cy))
    r = c.rng(k)
    gx, gy = np.meshgrid(np.arange(mx), np.arange(my))
    pts = np.stack([(gx.ravel() + 0.5 + (r.random(mx * my) - 0.5) * jitter) * (c.Lx / mx),
                    (gy.ravel() + 0.5 + (r.random(mx * my) - 0.5) * jitter) * (c.Ly / my)], 1)
    pts[:, 0] %= c.Lx
    pts[:, 1] %= c.Ly
    tree = cKDTree(pts, boxsize=[c.Lx, c.Ly])
    X, Y = c.xy()
    if warp is not None:
        X = (X + warp[0]) % c.Lx
        Y = (Y + warp[1]) % c.Ly
    d, i = tree.query(np.stack([X.ravel(), Y.ravel()], 1), k=2, workers=-1)
    sh = (c.ny, c.nx)
    return d[:, 0].reshape(sh).astype(np.float32), d[:, 1].reshape(sh).astype(np.float32), \
        i[:, 0].reshape(sh), i[:, 1].reshape(sh), mx * my


def edge_dist(d1, d2):
    """Approximate distance to the Voronoi edge (exact for equal-distance bisectors in the far field)."""
    return 0.5 * (d2 - d1)


def ao_from_height(h: np.ndarray, px: float, scales_m=(0.004, 0.015, 0.05), k: float = 1.0) -> np.ndarray:
    """Cheap cavity occlusion: how far a pixel lies below the local mean height at several radii."""
    occ = np.zeros_like(h)
    for s in scales_m:
        sp = max(0.6, s / px)
        occ += np.maximum(0, blur(h, sp) - h) / s
    return np.clip(1 - k * occ, 0, 1)


# --------------------------------------------------------------------------------------------- tier writer
def srgb_encode(lin: np.ndarray) -> np.ndarray:
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)


def down(a: np.ndarray, f: int) -> np.ndarray:
    if f == 1:
        return a
    sh = a.shape
    a = a.reshape(sh[0] // f, f, sh[1] // f, f, *sh[2:])
    return a.mean(axis=(1, 3))


def normals_from_height(h: np.ndarray, px: float) -> np.ndarray:
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / (2 * px)
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / (2 * px)    # d/drow; v = -row
    n = np.stack([-dx, dy, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def calibrate(albedo: np.ndarray, target_mean: float, weight: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """Scale linear albedo so its (optionally weighted) mean luminance hits the target."""
    lum = albedo @ LUM
    m = float((lum * weight).sum() / weight.sum()) if weight is not None else float(lum.mean())
    a = np.clip(albedo * (target_mean / m), 0, 1)
    return a, {}


def albedo_stats(albedo: np.ndarray, weight=None) -> dict:
    lum = albedo @ LUM
    if weight is not None:
        sel = weight.ravel() > 0.5
        v = lum.ravel()[sel]
    else:
        v = lum.ravel()
    rgb = albedo.reshape(-1, 3)[sel] if weight is not None else albedo.reshape(-1, 3)
    return {"mean_lum_linear": round(float(v.mean()), 4), "p05": round(float(np.percentile(v, 5)), 4),
            "p95": round(float(np.percentile(v, 95)), 4),
            "mean_rgb_linear": [round(float(x), 4) for x in rgb.mean(0)]}


def hf_ratio(lum: np.ndarray) -> float:
    """Share of luminance variance above half Nyquist (shimmer risk under minification)."""
    F = np.abs(fft2(lum - lum.mean())) ** 2
    fy = np.abs(fftfreq(lum.shape[0]))[:, None]
    fx = np.abs(fftfreq(lum.shape[1]))[None, :]
    hi = (np.maximum(fx, fy) > 0.25)
    return round(float(F[hi].sum() / (F.sum() + 1e-12)), 4)


def save_png(path: Path, arr01: np.ndarray, mode: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.clip(np.rint(arr01 * 255), 0, 255).astype(np.uint8)
    Image.fromarray(a, mode).save(path, compress_level=7)


@dataclass
class SurfaceSet:
    """Hi-res physical fields of one set (generation resolution = High tier)."""
    name: str
    c: Ctx
    albedo: np.ndarray               # (ny, nx, 3) linear
    height: np.ndarray               # metres
    rough: np.ndarray                # perceptual roughness 0..1
    elem_id: np.ndarray              # 0..1
    joint: np.ndarray                # 0..1
    detail_mask: np.ndarray | None = None
    metal: np.ndarray | None = None
    alpha: np.ndarray | None = None  # decals only
    ao_scales: tuple = (0.004, 0.015, 0.05)
    ao_k: float = 1.0
    extra_albedo: dict = field(default_factory=dict)   # variant name -> albedo (e.g. late_autumn)
    ao_extra: np.ndarray | None = None   # scan AO (CC0 sets, ADR 0063): multiplied into the height-derived cavity AO
    scan_info: dict | None = None        # provenance of a scan-based set (written into materials_spec.json)
    aa_tiers: bool = False           # Gaussian low-pass (sigma 0.6 x factor) before each tier's box downsample: fine
                                     # periodic relief (perforation) vanishes instead of aliasing into big dimples


def write_set(s: SurfaceSet, out_root: Path, tiers=("High", "Medium", "Low")) -> dict:
    out = out_root / s.name
    c = s.c
    # anti-shimmer prefilter: remove energy right at Nyquist (single-texel speckle flickers under motion even
    # with mips, because the base level is sampled at ~1:1 right in front of the cab)
    s.albedo = np.stack([blur(s.albedo[..., i], 0.55) for i in range(3)], -1)
    s.height = blur(s.height, 0.55)
    h = s.height
    hmin, hmax = float(h.min()), float(h.max())
    n_hi = normals_from_height(h, c.px)
    slope2_hi = (n_hi[..., 0] / n_hi[..., 2]) ** 2 + (n_hi[..., 1] / n_hi[..., 2]) ** 2
    sx_hi, sy_hi = n_hi[..., 0] / n_hi[..., 2], n_hi[..., 1] / n_hi[..., 2]
    ao_hi = ao_from_height(h, c.px, s.ao_scales, s.ao_k)
    if s.ao_extra is not None:
        ao_hi = ao_hi * s.ao_extra
    conv = np.clip(0.5 + (h - blur(h, max(0.6, 0.01 / c.px))) / max(1e-4, (hmax - hmin)) * 4, 0, 1)
    info = {"files": {}, "height_range_m": [round(hmin, 5), round(hmax, 5)]}
    for t in tiers:
        f = TIERS[t]
        ny, nx = c.ny // f, c.nx // f
        if min(nx, ny) < 64:
            continue
        px = c.px * f
        alb = down(s.albedo, f)
        hh = down(blur(h, 0.6 * f) if (s.aa_tiers and f > 1) else h, f)
        nrm = normals_from_height(hh, px)
        # Toksvig-style: slope variance lost by the downsample goes into roughness, so far surfaces don't sparkle
        var = down(slope2_hi, f) - down(sx_hi, f) ** 2 - down(sy_hi, f) ** 2
        alpha = down(s.rough, f) ** 2
        rough = np.sqrt(np.sqrt(alpha ** 2 + 2 * np.maximum(var, 0)))
        rough = np.clip(rough, 0.02, 1)
        ao = down(blur(ao_hi, 0.6 * f) if (s.aa_tiers and f > 1) else ao_hi, f)
        metal = down(s.metal, f) if s.metal is not None else np.zeros_like(ao)
        dmask = down(s.detail_mask, f) if s.detail_mask is not None else np.ones_like(ao)
        d = out / t
        base = f"T_{s.name}"
        if s.alpha is not None:
            save_png(d / f"{base}_BaseColor.png",
                     np.dstack([srgb_encode(alb), down(s.alpha, f)]), "RGBA")
        else:
            save_png(d / f"{base}_BaseColor.png", srgb_encode(alb), "RGB")
        for vn, va in s.extra_albedo.items():
            save_png(d / f"{base}_BaseColor_{vn}.png", srgb_encode(down(va, f)), "RGB")
        save_png(d / f"{base}_Normal.png", nrm * 0.5 + 0.5, "RGB")
        save_png(d / f"{base}_MaskMap.png", np.dstack([metal, ao, dmask, 1 - rough]), "RGBA")
        hn = (hh - hmin) / max(1e-9, hmax - hmin)
        idd = s.elem_id[::f, ::f]                        # ids must not be averaged
        save_png(d / f"{base}_Var.png", np.dstack([hn, idd, down(s.joint, f), down(conv, f)]), "RGBA")
        files = sorted(p.name for p in d.glob("*.png"))
        size = sum((d / p).stat().st_size for p in files)
        info["files"][t] = {"res": [nx, ny], "texel_mm": round(px * 1000, 2), "dir": f"{s.name}/{t}",
                            "png_bytes": size, "files": files,
                            "smoothness_mean": round(float(1 - rough.mean()), 3)}
    w = s.alpha if s.alpha is not None else None
    info["albedo"] = albedo_stats(s.albedo, w)
    info["hf_ratio_albedo"] = hf_ratio(s.albedo @ LUM)
    info["ao_mean"] = round(float(ao_hi.mean()), 3)
    return info


def tileable_crop_blend(img: np.ndarray) -> np.ndarray:
    """Make a zero-mean detail image tileable: blend it with a half-period shifted copy under a window,
    variance-preserving (the blend of two independent noises would otherwise lose contrast at the seam)."""
    n0, n1 = img.shape
    wy = np.sin(np.pi * (np.arange(n0) + 0.5) / n0) ** 2
    wx = np.sin(np.pi * (np.arange(n1) + 0.5) / n1) ** 2
    w = np.sqrt(np.outer(wy, wx))
    b = np.roll(img, (n0 // 2, n1 // 2), (0, 1))
    return (img * w + b * (1 - w)) / np.sqrt(w ** 2 + (1 - w) ** 2)


def dump_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
