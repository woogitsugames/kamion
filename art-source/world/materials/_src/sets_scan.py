"""CC0 surface scans -> mobile PBR sets in the contract of materials_spec.json (ADR 0063, owner decision D40).

Sources: art-source/world/cc0/cc0_manifest.json (Poly Haven, CC0 1.0), raw 2k maps in art-source/world/cc0/_raw/<id>/
(fetched and sha256-verified by cc0_fetch.py). The scan supplies micro-detail and mid-scale structure (aggregate,
grain, pores, stains, block faces, mortar); our generators keep the layout and everything Polish-specific (JOMB plates,
5 m sawn joints, kerb units, large-panel joints, trapezoid ribs), the 16 m crack layer, the 64 m macro variation, the
road wear, patches and oil (docs/06 §3: "skan jako baza, generator jako warstwy").

Processing per scan (all deterministic; fixed seeds):
  1. albedo: sRGB -> linear; partial de-lighting (divide by the scan AO ^ k: the diffuse maps keep some cavity shading
     that the engine adds again from MaskMap.G); low-frequency flattening (log-luminance high-pass at `flat_m`, strength
     `flat_k`: removes shading gradients and the large blotches that would repeat at the tile period - the 64 m macro
     map owns that scale); hue re-balanced to the previous set's mean colour (Podlasie palette, docs/06 §1) keeping the
     scan's own relative colour variation; mean luminance calibrated to the set target (tiling sets) or normalised to
     0.5 per channel (modulation sets, engine albedo = 2 x manifest colour x map).
  2. height: Frankot-Chellappa integration of the scan's OpenGL normal map in metres (texel size from the scan's
     physical dimensions), so the normals the tier writer re-derives from it reproduce the scan normals at every tier
     (Toksvig smoothness keeps working). `nrm_gain` WORKING_VALUE where a scan normal map looked exaggerated.
  3. roughness from the scan; AO = scan AO (multiplied into the height-derived cavity AO of pbrkit.write_set).
  4. element ids (Var.G) for paving: blocks segmented from the displacement map with periodic labelling, so the shader's
     per-element tone jitter breaks the repeat of the scan tile.
  5. isotropic sets (asphalt, gravel): offline texture bombing - the 2 m scan is re-assembled into a 4 m periodic tile
     from 16 jittered patches with random 90-degree rotations / flips and variance-preserving blending (Heitz & Neyret
     2018 "High-performance by-example noise using a histogram-preserving blending operator", formula only), so the
     visible period doubles at zero shader cost.
  6. hybrid sets: the procedural set keeps its layout; the scan (bombed to the set's size and texel) replaces the
     micro relief and modulates albedo / roughness with its high-pass ratio.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numpy.fft import fft2, ifft2, fftfreq
from PIL import Image
from scipy import ndimage

from pbrkit import sstep, Ctx, SurfaceSet, LUM, blur, calibrate, hash01

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CC0 = REPO / "art-source" / "world" / "cc0"
RAW = CC0 / "_raw"
_MAN = None


def manifest() -> dict:
    global _MAN
    if _MAN is None:
        _MAN = json.loads((CC0 / "cc0_manifest.json").read_text(encoding="utf-8"))
    return _MAN


def asset(aid: str) -> dict:
    return next(a for a in manifest()["assets"] if a["id"] == aid)


def available(aid: str) -> bool:
    try:
        a = asset(aid)
    except (StopIteration, FileNotFoundError):
        return False
    return all((RAW / aid / f["url"].rsplit("/", 1)[1]).exists() for f in a["files"])


def _img(aid: str, m: str) -> np.ndarray:
    a = asset(aid)
    f = next(x for x in a["files"] if x["map"] == m)
    p = RAW / aid / f["url"].rsplit("/", 1)[1]
    im = Image.open(p)
    im.load()
    arr = np.asarray(im.convert("RGB" if m in ("Diffuse", "nor_gl") else "L"), np.float32) / 255.0
    return arr


def srgb_decode(s: np.ndarray) -> np.ndarray:
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4).astype(np.float32)


def down(a: np.ndarray, f: int) -> np.ndarray:
    if f == 1:
        return a
    sh = a.shape
    return a.reshape(sh[0] // f, f, sh[1] // f, f, *sh[2:]).mean(axis=(1, 3))


def resample(a: np.ndarray, ny: int, nx: int) -> np.ndarray:
    """Periodic resample to (ny, nx): integer box-down where possible, then wrap-mode cubic zoom for the rest."""
    f = max(1, min(a.shape[0] // ny, a.shape[1] // nx))
    while f > 1 and (a.shape[0] % f or a.shape[1] % f):
        f -= 1
    a = down(a, f)
    if a.shape[:2] == (ny, nx):
        return a.astype(np.float32)
    zy, zx = ny / a.shape[0], nx / a.shape[1]
    if a.ndim == 3:
        return np.stack([ndimage.zoom(a[..., i], (zy, zx), order=3, mode="grid-wrap") for i in range(a.shape[2])], -1)
    return ndimage.zoom(a, (zy, zx), order=3, mode="grid-wrap").astype(np.float32)


def fc_height(nrm01: np.ndarray, px: float, gain: float = 1.0) -> np.ndarray:
    """Frankot-Chellappa: periodic height (m) whose gradients best match an OpenGL tangent normal map (+Y = up the
    image). Row index grows downwards, so dh/drow = +n.y/n.z (pbrkit.normals_from_height convention)."""
    n = nrm01 * 2 - 1
    nz = np.maximum(n[..., 2], 0.2)
    gx = -n[..., 0] / nz * gain          # dh/dx (m/m), x = +column
    gr = n[..., 1] / nz * gain           # dh/drow (m/m)
    ny_, nx_ = gx.shape
    fx = fftfreq(nx_, d=px)[None, :]
    fy = fftfreq(ny_, d=px)[:, None]
    den = 2 * np.pi * (fx ** 2 + fy ** 2)
    den[0, 0] = 1
    H = (-1j * fx * fft2(gx) - 1j * fy * fft2(gr)) / den
    H[0, 0] = 0
    return np.real(ifft2(H)).astype(np.float32)


def flatten(alb: np.ndarray, px: float, wl_m: float, k: float) -> np.ndarray:
    """Remove luminance variation with wavelength > wl_m (log space, wrap), strength k (0..1); keeps the mean."""
    if k <= 0:
        return alb
    lum = np.maximum(alb @ LUM, 1e-4)
    lo = np.exp(ndimage.gaussian_filter(np.log(lum), wl_m / px / 2.5, mode="wrap"))
    g = np.exp(np.log(lum).mean())
    return alb * ((g / lo) ** k)[..., None]


def rebalance_hue(alb: np.ndarray, target_rgb, keep: float = 1.0) -> np.ndarray:
    """Global white balance to target_rgb's chromaticity; local chroma deviations kept with factor `keep`."""
    lum = np.maximum(alb @ LUM, 1e-5)[..., None]
    chroma = alb / lum
    cm = chroma.reshape(-1, 3).mean(0)
    t = np.asarray(target_rgb, np.float32)
    t = t / float(t @ LUM)
    return np.clip(lum * (t + keep * (chroma - cm)), 0, 1).astype(np.float32)


class Scan:
    """One scan, loaded at its native 2k, in metres."""

    def __init__(self, aid: str):
        a = asset(aid)
        self.id = aid
        self.L = [d / 1000.0 for d in a["dimensions_mm"]]           # x, y metres
        dif = _img(aid, "Diffuse")
        self.ny, self.nx = dif.shape[:2]
        self.px = self.L[0] / self.nx
        self.alb = srgb_decode(dif)
        self.nrm = _img(aid, "nor_gl")
        self.rough = _img(aid, "Rough")
        self.ao = _img(aid, "AO")
        self.disp = _img(aid, "Displacement")


def prepare(sc: Scan, *, ao_k=0.5, flat_m=1.0, flat_k=0.8, nrm_gain=1.0):
    """De-lit, flattened linear albedo and metric height at the scan's own texel size."""
    alb = sc.alb / np.maximum(0.25, sc.ao ** ao_k)[..., None]
    alb = flatten(alb, sc.px, flat_m, flat_k)
    h = fc_height(sc.nrm, sc.px, nrm_gain)
    # long-wave warps of the integrated height (> 1.5 x flat_m) belong to the macro layers, not to a repeating tile
    h = h - ndimage.gaussian_filter(h, 1.5 * flat_m / sc.px / 2.5, mode="wrap")
    return np.clip(alb, 0, 1).astype(np.float32), h


# ------------------------------------------------------------------------------------------------------ bombing
def _rot(a: np.ndarray, k: int, flip: bool) -> np.ndarray:
    a = np.rot90(a, k, axes=(0, 1))
    return a[:, ::-1] if flip else a


def bomb(fields: dict, src_n: int, out_shape, cells, seed: int, vp=("alb", "h")) -> dict:
    """Re-assemble periodic square fields (src_n px) into a periodic tile of out_shape = (ny, nx) px from
    cells = (cy, cx) jittered patches, each a random crop of the source with a random 90-degree rotation / flip, blended
    under cos^2 windows. Fields named in `vp` use variance-preserving blending (mean + sum w (f - mean) / sqrt(sum
    w^2)); others a plain weighted mean. Source and output share the texel size (resample first)."""
    if isinstance(out_shape, int):
        out_shape = (out_shape, out_shape)
    if isinstance(cells, int):
        cells = (cells, cells)
    ny, nx = out_shape
    cells = (max(2, cells[0]), max(2, cells[1]))     # a window must never wrap onto itself
    rng = np.random.default_rng(seed)
    ry_, rx_ = np.arange(ny), np.arange(nx)
    cly, clx = ny / cells[0], nx / cells[1]
    acc = {k: 0.0 for k in fields}
    wsum = np.zeros((ny, nx), np.float32)
    w2 = np.zeros((ny, nx), np.float32)
    means = {k: v.reshape(-1, *v.shape[2:]).mean(0) for k, v in fields.items()}
    for cy in range(cells[0]):
        for cx in range(cells[1]):
            py = int((cy + 0.5 + (rng.random() - 0.5) * 0.6) * cly)
            px_ = int((cx + 0.5 + (rng.random() - 0.5) * 0.6) * clx)
            k = int(rng.integers(4))
            flip = bool(rng.integers(2))
            oy, ox = int(rng.integers(src_n)), int(rng.integers(src_n))
            # offsets from the patch centre, unwrapped inside the window: the patch is continuous across the tile edge
            dy = (ry_ - py + ny // 2) % ny - ny // 2
            dx = (rx_ - px_ + nx // 2) % nx - nx // 2
            r = np.maximum(np.abs(dy)[:, None] / cly, np.abs(dx)[None, :] / clx)
            w = (np.cos(np.clip(r, 0, 1) * np.pi / 2) ** 2).astype(np.float32) + 1e-6
            wsum += w
            w2 += w * w
            iy, ix = np.ix_((dy + oy) % src_n, (dx + ox) % src_n)
            for name, f in fields.items():
                t = _rot(f, k, flip)[iy, ix]
                wf = w[..., None] if t.ndim == 3 else w
                if name in vp:
                    acc[name] = acc[name] + wf * (t - means[name])
                else:
                    acc[name] = acc[name] + wf * t
    out = {}
    for name in fields:
        d = np.sqrt(w2) if name in vp else wsum
        d = d[..., None] if fields[name].ndim == 3 else d
        out[name] = ((means[name] if name in vp else 0) + acc[name] / d).astype(np.float32)
    return out


# -------------------------------------------------------------------------------------------- element segmentation
def periodic_labels(solid: np.ndarray) -> np.ndarray:
    """Connected components of a periodic boolean image (components touching opposite borders are merged)."""
    lab, n = ndimage.label(solid)
    parent = np.arange(n + 1)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b in ((lab[:, 0], lab[:, -1]), (lab[0, :], lab[-1, :])):
        for x, y in zip(a, b):
            if x and y:
                rx, ry = find(x), find(y)
                if rx != ry:
                    parent[ry] = rx
    roots = np.array([find(i) for i in range(n + 1)])
    return roots[lab]


def segment_blocks(disp: np.ndarray, px: float, joint_quantile: float, close_px: int = 1):
    """Paver / brick faces from a displacement map: joints = lowest `joint_quantile` of the high-passed height.
    Returns (element id 0..1 per pixel incl. joints = nearest face, joint mask 0..1, number of faces)."""
    hp = disp - ndimage.gaussian_filter(disp, 0.08 / px, mode="wrap")
    thr = np.quantile(hp, joint_quantile)
    joint = hp < thr
    joint = ndimage.binary_closing(joint, iterations=close_px) if close_px else joint
    lab = periodic_labels(~joint)
    sizes = np.bincount(lab.ravel())
    small = sizes < max(30, 0.15 * np.median(sizes[1:][sizes[1:] > 0]))
    lab[small[lab]] = 0
    idx = ndimage.distance_transform_edt(lab == 0, return_distances=False, return_indices=True)
    lab = lab[idx[0], idx[1]]
    eid = hash01(lab, 913).astype(np.float32)
    # Var.B (dirt / moss in joints) from the deepest part only: the labelling threshold is generous on purpose
    jm = ndimage.gaussian_filter((hp < np.quantile(hp, joint_quantile * 0.4)).astype(np.float32), 0.6, mode="wrap")
    return eid, jm, int(len(np.unique(lab)))


def course_period(lum: np.ndarray, axis: int, px: float, lo_m: float, hi_m: float) -> float:
    """Dominant period (m) of a periodic pattern along an axis from the autocorrelation of row/column means."""
    prof = lum.mean(axis=1 - axis)
    prof = prof - prof.mean()
    ac = np.real(ifft2(np.abs(fft2(prof[None, :])) ** 2))[0]
    lags = np.arange(len(ac))
    sel = (lags * px >= lo_m) & (lags * px <= hi_m)
    return float(lags[sel][np.argmax(ac[sel])] * px)


# ----------------------------------------------------------------------------------------------- set builders
def soft_ao(ao: np.ndarray, gamma: float = 0.4) -> np.ndarray:
    """Scan AO as a gentle multiplier of the height-derived cavity AO: normalised to its 90th percentile (open surface
    = 1) and softened, because the diffuse map was already de-lit by it and the engine adds ambient occlusion again
    (a raw multiply darkened the overcast asphalt by 3 sRGB levels and gravel AO to 0.6)."""
    a = np.clip(ao / max(1e-3, float(np.percentile(ao, 90))), 0.05, 1.0)
    return (a ** gamma).astype(np.float32)


def _cavity(h: np.ndarray, px: float) -> np.ndarray:
    c = ndimage.gaussian_filter(h, 0.01 / px, mode="wrap") - h
    return np.clip(c / (np.std(c) * 3 + 1e-9), 0, 1).astype(np.float32)


def tiling_from_scan(name: str, aid: str, *, target: float, hue, out_L: float, out_n: int, seed: int,
                     bomb_cells: int = 0, ao_k=0.5, flat_m=1.0, flat_k=0.8, nrm_gain=1.0, hue_keep=0.6,
                     rough_scale=1.0, rough_add=0.0, ao_gamma=0.4, segment: dict | None = None, period_fix: dict | None = None,
                     modulation=False, hf_keep=1.0, hf_sigma_m=0.004, joint_dark=0.0):
    """A tiling (calibrated) or modulation set from one scan. out_L = tile size (m); bomb_cells > 0 re-assembles the
    scan (resampled to the output texel) into the out_L tile.
    ADR 0091: hf_keep < 1 scales the albedo and height detail finer than hf_sigma_m (the grain 'pepper' of a render
    seen from the street); joint_dark darkens the mortar joints of a brick scan."""
    sc = Scan(aid)
    alb, h = prepare(sc, ao_k=ao_k, flat_m=flat_m, flat_k=flat_k, nrm_gain=nrm_gain)
    rough = np.clip(sc.rough * rough_scale + rough_add, 0.05, 1).astype(np.float32)
    ao = sc.ao
    info = {"source": aid, "source_dimensions_m": [round(x, 3) for x in sc.L]}
    Lx = Ly = out_L
    if period_fix:
        # scale the scan so its element period matches the Polish standard size (NF brick course 75 mm, holland row
        # 103 mm, sidewalk slab 350 mm): one entry = uniform scale, two entries (axis 0 = vertical, 1 = horizontal) =
        # per-axis scale (bond length and course height of a brick differ from the scan's proportions)
        lum = alb @ LUM
        sc_xy = [1.0, 1.0]
        meas = []
        for e in period_fix:
            p = course_period(lum, e["axis"], sc.px, *e["search_m"])
            meas.append(round(p, 4))
            f = e["period_m"] / p
            if len(period_fix) == 1:
                sc_xy = [f, f]
            else:
                sc_xy[1 - e["axis"]] = f          # axis 0 = profile along rows (vertical) -> scales y
        Lx, Ly = sc.L[0] * sc_xy[0], sc.L[1] * sc_xy[1]
        info["measured_period_m"] = meas
        info["scale_to_standard_xy"] = [round(x, 4) for x in sc_xy]
    if bomb_cells:
        src_n = int(round(sc.L[0] / (out_L / out_n)))            # source px at the output texel size
        src_n -= src_n % 4
        f = {"alb": resample(alb, src_n, src_n), "h": resample(h, src_n, src_n), "rough": resample(rough, src_n, src_n),
             "ao": resample(ao, src_n, src_n)}
        b = bomb(f, src_n, (out_n, out_n), bomb_cells, seed)
        alb, h, rough, ao = b["alb"], b["h"], b["rough"], b["ao"]
        nx = ny = out_n
        eid = hash01(np.zeros(alb.shape[:2], np.int64), seed)  # no elements
        joint = _cavity(h, out_L / out_n)
        info["bombing"] = {"cells": bomb_cells, "patch_m": round(sc.L[0], 3), "tile_m": out_L}
    else:
        nx, ny = out_n, int(round(out_n * Ly / Lx)) // 4 * 4
        if segment:
            eid, joint, nel = segment_blocks(sc.disp, sc.px, segment["joint_quantile"], segment.get("close_px", 0))
            info["elements_per_tile"] = nel
            eid = eid[(np.arange(ny) * sc.ny // ny)[:, None], (np.arange(nx) * sc.nx // nx)[None, :]]
            joint = resample(joint, ny, nx)
        else:
            joint = None
        alb, h, rough, ao = (resample(x, ny, nx) for x in (alb, h, rough, ao))
        if joint is None:
            joint = _cavity(h, Lx / nx)
            eid = np.zeros((ny, nx), np.float32)
    c = Ctx(nx, ny, Lx, Ly, seed=seed)
    if hf_keep < 1.0:
        sg = hf_sigma_m / (Lx / nx)
        low = np.stack([ndimage.gaussian_filter(alb[..., i], sg, mode="wrap") for i in range(3)], -1)
        alb = (low + hf_keep * (alb - low)).astype(np.float32)
        lowh = ndimage.gaussian_filter(h, sg, mode="wrap")
        h = (lowh + hf_keep * (h - lowh)).astype(np.float32)
    alb = rebalance_hue(alb, hue, hue_keep)
    if joint_dark:
        # mortar of a brick scan = the texels less red than the mean (cyan side of the neutralised map; the scan's
        # joints are nearly flush, a height cavity mask misses them); darkened, hue kept (so it stays grey under the tint)
        lum = np.maximum(alb @ LUM, 1e-4)
        jm = sstep(0.04, 0.22, ((alb[..., 1] + alb[..., 2]) * 0.5 - alb[..., 0]) / lum)
        jm = ndimage.gaussian_filter(jm.astype(np.float32), 0.7, mode="wrap")[..., None]
        alb = (alb * (1.0 - joint_dark * jm)).astype(np.float32)
        joint = np.maximum(joint, jm[..., 0])
    if modulation:
        m = alb.reshape(-1, 3).mean(0)
        alb = np.clip(alb * (0.5 / m), 0, 1).astype(np.float32)
    else:
        alb, _ = calibrate(alb, target)
    s = SurfaceSet(name, c, alb.astype(np.float32), h.astype(np.float32), rough, eid.astype(np.float32),
                   joint.astype(np.float32), ao_extra=soft_ao(ao, ao_gamma))
    s.scan_info = info
    return s


def scan_detail(aid: str, c: Ctx, seed: int, *, cells: int | None = None, ao_k=0.5, flat_m=0.6, flat_k=0.9,
                nrm_gain=1.0, notch_ribs=False):
    """The scan bombed to an arbitrary (Lx, Ly, nx, ny) set: returns high-pass albedo ratio (mean 1), micro height
    (m), roughness ratio (mean 1) and AO, all at the set's resolution."""
    sc = Scan(aid)
    alb, h = prepare(sc, ao_k=ao_k, flat_m=flat_m, flat_k=flat_k, nrm_gain=nrm_gain)
    lum = np.maximum(alb @ LUM, 1e-4)
    if notch_ribs:
        # corrugated sheet: remove the rib pattern (energy on the f_y = 0 axis = vertical stripes), keep the weathering
        def notch(a):
            F = fft2(a)
            F[0:2, 1:] = 0
            F[-1:, 1:] = 0
            return np.real(ifft2(F)).astype(np.float32)
        lum = np.exp(notch(np.log(lum)))
        h = notch(h)
    ratio = lum / np.exp(np.log(lum).mean())
    rr = sc.rough / max(1e-3, float(sc.rough.mean()))
    src_n = int(round(sc.L[0] / c.px))
    src_n -= src_n % 4
    f = {"ratio": resample(ratio, src_n, src_n), "h": resample(h, src_n, src_n), "rr": resample(rr, src_n, src_n),
         "ao": resample(sc.ao, src_n, src_n)}
    cells = cells or (max(1, int(round(c.Ly / (sc.L[1] * 0.5)))), max(1, int(round(c.Lx / (sc.L[0] * 0.5)))))
    out = bomb(f, src_n, (c.ny, c.nx), cells, seed, vp=("ratio", "h", "rr"))
    out["ratio"] = np.maximum(out["ratio"], 0.05)
    out["rr"] = np.maximum(out["rr"], 0.1)
    return out


def hybrid(s: SurfaceSet, aid: str, seed: int, *, alb_k=1.0, h_k=1.0, rough_k=0.6, ao_k_mix=0.6, target=None,
           weight=None, **kw) -> SurfaceSet:
    """Procedural layout + scan micro-detail: albedo x ratio^alb_k, height + scan micro relief, roughness x ratio,
    AO from the scan. Re-calibrates the albedo mean (tiling sets) or keeps the modulation mean at 0.5."""
    d = scan_detail(aid, s.c, seed, **kw)
    ratio = d["ratio"] ** alb_k
    # the procedural micro noise is replaced, not doubled: its own finest octave is taken out first
    base = np.stack([ndimage.gaussian_filter(s.albedo[..., i], 1.2, mode="wrap") for i in range(3)], -1)
    keep = s.joint[..., None] if s.joint is not None else 0
    alb = (base * ratio[..., None]) * (1 - keep) + s.albedo * keep
    if target is not None:
        alb, _ = calibrate(alb, target, weight=weight)
    else:
        m = alb.reshape(-1, 3).mean(0)
        alb = alb * (s.albedo.reshape(-1, 3).mean(0) / np.maximum(m, 1e-4))
    s.albedo = np.clip(alb, 0, 1).astype(np.float32)
    s.height = (s.height + h_k * (d["h"] - d["h"].mean())).astype(np.float32)
    s.rough = np.clip(s.rough * (1 + rough_k * (d["rr"] - 1)), 0.05, 1).astype(np.float32)
    s.ao_extra = soft_ao(d["ao"], 0.4 * ao_k_mix)
    s.scan_info = {"source": aid, "mode": "hybrid (procedural layout + scan micro-detail)"}
    return s


# ------------------------------------------------------------------------------------------------ registry
# Previous (procedural) set means: the scans are white-balanced to them so the calibrated palette (D37 paint/asphalt
# contrast, review r8 asphalt 102-106 sRGB) does not move; the scan keeps its own relative colour variation.
HUE_ASPHALT_WORN = [0.0803, 0.0796, 0.0789]
HUE_ASPHALT_SMA = [0.0751, 0.0746, 0.0740]
HUE_ASPHALT_PATCH = [0.0624, 0.0619, 0.0614]
HUE_BEHATON = [0.2237, 0.2222, 0.2141]
HUE_PAVING = [0.2567, 0.2547, 0.2455]
HUE_GRAVEL = [0.2172, 0.1982, 0.1681]
NEUTRAL = [1.0, 1.0, 1.0]


def _jomb():
    import sets_other as O
    s = O.concrete_jomb()
    return hybrid(s, "concrete_floor_worn_001", 6303, target=0.27, weight=s.detail_mask, alb_k=1.6, h_k=0.8)


def _cast():
    import sets_other as O
    return hybrid(O.concrete_cast(), "brushed_concrete", 6304, target=0.30, alb_k=0.8, h_k=0.8)


def _kerb():
    import sets_other as O
    return hybrid(O.kerb(), "concrete_floor_worn_001", 6305, target=0.28, alb_k=1.6, h_k=0.8)


def _precast():
    import sets_facade as F
    return hybrid(F.concrete_precast(), "concrete_floor_worn_001", 6306, alb_k=1.6, h_k=0.8)


def _panel():
    import sets_facade as F
    return hybrid(F.large_panel_joints(), "concrete_floor_worn_001", 6307, alb_k=1.6, h_k=0.8)


def _trapezoid():
    import sets_facade as F
    return hybrid(F.trapezoid_sheet(), "corrugated_iron_03", 6308, alb_k=1.0, h_k=0.25, rough_k=0.5, notch_ribs=True,
                  flat_m=0.4, flat_k=0.9)


SCAN_SETS = {
    # tiling sets straight from a scan
    "asphalt_worn": (["asphalt_04"], lambda: tiling_from_scan(
        "asphalt_worn", "asphalt_04", target=0.08, hue=HUE_ASPHALT_WORN, out_L=4.04, out_n=2048, seed=6311,
        flat_m=0.35, flat_k=0.95, hue_keep=0.5, ao_gamma=0.0, rough_add=-0.03)),   # r8 asphalt level 100-106 sRGB (Low ov)
    "asphalt_sma_fresh": (["asphalt_pit_lane"], lambda: tiling_from_scan(
        "asphalt_sma_fresh", "asphalt_pit_lane", target=0.075, hue=HUE_ASPHALT_SMA, out_L=4.0, out_n=2048, seed=6312,
        bomb_cells=4, flat_m=0.6, flat_k=0.85, hue_keep=0.4, rough_add=-0.15)),
    "asphalt_patch": (["clean_asphalt"], lambda: tiling_from_scan(
        "asphalt_patch", "clean_asphalt", target=0.062, hue=HUE_ASPHALT_PATCH, out_L=4.0, out_n=2048, seed=6313,
        bomb_cells=4, flat_m=0.6, flat_k=0.85, hue_keep=0.5)),
    "gravel_compacted": (["gravel_floor_02"], lambda: tiling_from_scan(
        "gravel_compacted", "gravel_floor_02", target=0.20, hue=HUE_GRAVEL, out_L=4.0, out_n=2048, seed=6314,
        bomb_cells=4, flat_m=0.6, flat_k=0.8, hue_keep=0.8, rough_add=0.35, ao_k=0.3)),
    "behaton_i_grey": (["concrete_pavers"], lambda: tiling_from_scan(
        "behaton_i_grey", "concrete_pavers", target=0.23, hue=HUE_BEHATON, out_L=1.92, out_n=1024, seed=6315,
        flat_m=1.2, flat_k=0.5, hue_keep=0.6, segment={"joint_quantile": 0.22})),
    "paving_20x10_grey": (["pavement_04"], lambda: tiling_from_scan(
        "paving_20x10_grey", "pavement_04", target=0.26, hue=HUE_PAVING, out_L=3.1, out_n=1024, seed=6316,
        flat_m=1.2, flat_k=0.5, hue_keep=0.6, segment={"joint_quantile": 0.20},
        period_fix=[{"axis": 0, "search_m": (0.08, 0.2), "period_m": 0.1035}])),
    "sidewalk_slab_35": (["concrete_pavement_02"], lambda: tiling_from_scan(
        "sidewalk_slab_35", "concrete_pavement_02", target=0.27, hue=HUE_PAVING, out_L=1.8, out_n=1024, seed=6317,
        flat_m=1.5, flat_k=0.4, hue_keep=0.6, segment={"joint_quantile": 0.16},
        period_fix=[{"axis": 0, "search_m": (0.2, 0.45), "period_m": 0.353}])),
    # modulation sets (engine albedo = 2 x manifest colour x map)
    "plaster": (["painted_plaster_wall"], lambda: tiling_from_scan(
        "plaster", "painted_plaster_wall", target=0.5, hue=NEUTRAL, out_L=2.0, out_n=1024, seed=6318,
        # ADR 0094 (review s9 P1-2): the scan is a weathered, repainted wall - its cream / white paint patches of
        # 0.1-0.5 m read on a light facade as paint dabbed on with a sponge. Tone variation coarser than ~0.04 m is
        # flattened by 95 % (was: coarser than 0.5 m by 85 %; r1 of this ADR 0.12 m / 92 % still showed 7-10 cm dabs of
        # +-4 % linear) and the local hue shifts are removed; a rendered facade is
        # one tone, its variation comes from the splash zone and the run-off streaks (shader), not from the tile
        flat_m=0.04, flat_k=0.95, hue_keep=0.0, modulation=True, hf_keep=0.22, hf_sigma_m=0.03, nrm_gain=0.3, ao_gamma=0.15)),   # ADR 0091
    "brick": (["red_brick"], lambda: tiling_from_scan(
        "brick", "red_brick", target=0.5, hue=NEUTRAL, out_L=1.4, out_n=1024, seed=6319,
        flat_m=0.4, flat_k=0.8, hue_keep=1.0, modulation=True, joint_dark=0.35,   # ADR 0091 darker joints
        period_fix=[{"axis": 0, "search_m": (0.05, 0.10), "period_m": 0.075}])),
    "bark_pine": (["pine_bark"], lambda: tiling_from_scan(
        "bark_pine", "pine_bark", target=0.5, hue=NEUTRAL, out_L=2.0, out_n=1024, seed=6320,
        flat_m=0.8, flat_k=0.5, hue_keep=1.0, modulation=True)),
    # hybrids: procedural layout + scan micro-detail
    "concrete_slab_3x1.5": (["concrete_floor_worn_001"], _jomb),
    "concrete_cast_5m_joints": (["brushed_concrete"], _cast),
    "kerb_concrete_1m": (["concrete_floor_worn_001"], _kerb),
    "concrete_precast": (["concrete_floor_worn_001"], _precast),
    "large_panel_joints": (["concrete_floor_worn_001"], _panel),
    "trapezoid_sheet": (["corrugated_iron_03"], _trapezoid),
}

# sets that exist only as scans (no procedural twin): spec metadata
SCAN_ONLY_META = {
    "sidewalk_slab_35": dict(kind="tiling_set", target=0.27, uv="world_xy_planar",
                             slots=["(not assigned yet) sidewalk slabs 35x35 cm, older footways"],
                             note="Square concrete sidewalk slabs (plyty chodnikowe 35x35x5), scan scaled from ~0.30 m "
                                  "to 0.35 m slabs (WORKING_VALUE). Var.G = slab id from the scan's displacement."),
    "bark_pine": dict(kind="modulation_set", target=0.5, uv="mesh_uv0_metres (u around, v up)",
                      slots=["(not assigned) tree trunks - vegetation is the world-builder's scope (ADR 0060)"],
                      note="Plated pine bark, neutral modulation map (mean 0.5 per channel); colour from the manifest."),
}


def build(name: str) -> SurfaceSet | None:
    """Scan-based set, or None when its scans are not fetched (build_all then falls back to the procedural set)."""
    if name not in SCAN_SETS:
        return None
    ids, fn = SCAN_SETS[name]
    if not all(available(i) for i in ids):
        return None
    s = fn()
    info = dict(s.scan_info or {})
    info["assets"] = [{"id": i, "page": asset(i)["page"], "authors": asset(i)["authors"], "license": asset(i)["license"]}
                      for i in ids]
    s.scan_info = info
    return s
