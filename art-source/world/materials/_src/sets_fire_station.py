"""Texture work of the hero fire station JRG2, Andersa 46 (ADR 0070).

`fire_station`        one calibrated atlas (tile 14 x 14 m, mesh UV0 in metres) for every opaque face of the asset:
                      u-periodic bands (pale blue render with a splash zone at the bottom and run-off under the top,
                      blue trapezoidal roof sheet eave -> ridge, blue flashing / fascia, concrete plinth) and
                      one-off elements (sectional garage door, clinker pier, arched / round / plain windows, entrance
                      door, flag, steel, membrane).
                      Bases = CC0 scans from Poly Haven (CC0 1.0, docs/LICENSES.md): "Painted Plaster Wall"
                      (Amal Kumar), "Brick Wall 006" (Jan Burghardt), "Concrete Wall 008" (Charlotte Baglioni /
                      Dario Barresi) used as detail (albedo high-pass), relief and roughness. Colours are set by eye
                      from the CC0 photos of the building (Commons, Rakoon: 7197 May 2021, 20240626 103137) -
                      WORKING_VALUE. No pixels of any reference photo are used.
`fire_station_alpha`  art-source/world/textures/fire_station_alpha.png (RGBA, alpha test): fence bay, sliding gate bay,
                      the lettering "PAŃSTWOWA STRAŻ POŻARNA" and "998" (generic name of the service and the public
                      emergency number as on the facade; no emblem, no logo).

The layout below is the contract with tools/blender/world/landmarks/make_fire_station.py (written to
art-source/world/landmarks/fire_station_jrg2/atlas_layout.json).

    uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only fire_station
    uv run --project tools/worldgen python art-source/world/materials/_src/sets_fire_station.py --alpha --layout
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pbrkit as K  # noqa: E402

REPO = HERE.parents[3]
LANDMARK = REPO / "art-source" / "world" / "landmarks" / "fire_station_jrg2"
CC0 = REPO / "Data" / "raw" / "cc0" / "polyhaven"                                   # not versioned (Data/raw)
URL = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/{a}/{a}_{m}_2k.jpg"
# md5 from https://api.polyhaven.com/files/<asset> (2026-11-10); size_m = asset "dimensions" (Poly Haven API)
SCANS = {
    "painted_plaster_wall": {"size_m": 2.0, "diff": "32f4f4e5ded7d20e55e337004d0d9691",
                             "disp": "b7823671e9faf44796354ef65b1dbe76", "rough": "7cdd5fbbe56f7becb757fc5b52d11d28"},
    "brick_wall_006": {"size_m": 3.0, "diff": "ce58078bffb33ca142240f675060e972",
                       "disp": "87e75e7bcb9a2a5253e608824f4da02d", "rough": "d0339c12ff4ee6f8580f65445f690a60"},
    "concrete_wall_008": {"size_m": 2.71, "diff": "9e834dad5c07a3ba452a2ad0f1454c9f",
                          "disp": "5bb8b340c56eb483f8fdb69b6ff29d6f", "rough": "8b4997c293727d89322a7dbe30ae34ae"},
}

TILE = (14.0, 14.0)
G = 0.05   # gutter


def _r(u0, v0, w, h):
    return {"u": [round(u0, 3), round(u0 + w, 3)], "v": [round(v0, 3), round(v0 + h, 3)]}


# v in metres from the bottom of the image. Bands are periodic along u (14 m).
LAYOUT = {
    "tile_m": list(TILE),
    # real size of the gable openings (measured on the CC0 photo 7197: 27 px/m on the 12 m gable, WORKING_VALUE
    # +-0.2 m); the atlas rects win_arch / win_round hold them scaled (rect size / real size)
    "arch": {"w": 4.7, "spring": 3.3, "rise": 1.3, "trim": 0.24, "col": 1.5667, "row": 1.5, "bar": 0.07},      # r4: 3 lights (2 mullions) as on photo 7197
    "round": {"d": 3.4, "trim": 0.28, "cross": 0.24},
    "plaster": {"v0": 0.0, "h": 4.0, "base_h": 2.6, "mid": [1.2, 2.6]},     # top zone = [base_h, h]
    "roof": {"v0": 4.05, "h": 3.2, "mid": [0.6, 2.8], "rib_pitch": 0.25},
    "fascia": {"v0": 11.45, "h": 0.40},
    "plinth": {"v0": 11.90, "h": 0.60},
    "door": _r(0.05, 7.35, 3.6, 4.0),
    "brick": _r(3.75, 7.35, 1.0, 4.0),
    "win_arch": _r(4.85, 7.35, 3.4, 3.4),
    "win_round": _r(8.35, 7.35, 2.4, 2.4),
    "win_plain": _r(10.85, 7.35, 1.5, 1.5),
    "win_ribbon": _r(10.85, 8.95, 1.2, 0.8),
    "win_small": _r(12.45, 7.35, 0.9, 0.9),
    "door_entry": _r(12.45, 8.35, 1.1, 2.2),
    "flag": _r(8.35, 9.85, 1.6, 1.0),
    "conifer_core": _r(8.35, 10.95, 1.6, 0.4),  # ADR 0116: unused atlas gap, same opaque material
    "steel_galv": _r(10.10, 9.90, 0.9, 1.4),
    "pvc_white": _r(11.20, 9.90, 0.9, 1.4),
    "membrane": _r(0.05, 12.60, 7.9, 1.35),
    "dark": _r(8.15, 12.60, 0.9, 1.35),
    "glass": _r(9.25, 12.60, 0.9, 1.35),
    "ochre": _r(10.35, 12.60, 1.6, 1.35),
    "thuja_far": _r(12.15, 12.60, 1.75, 1.35),     # r4: far-LOD thuja body (LOD1/2 have no leaf shell)
    # linear albedo, WORKING_VALUE read by eye off the CC0 photos (overcast frame 7197 + sunny frame 20240626)
    # ADR0086: common plaster-only x1.15 WORKING_VALUE experiment after the global
    # tint fix. Baseline High ov 105/121/137, Low ov 97/112/130; photo7197 111/126/147.
    # The atlas roof/glass/trim regions keep their prior albedo (separate S10 E work).
    "render_blue_linear": [0.21275, 0.299, 0.41975],
    "roof_blue_linear": [0.024, 0.085, 0.235],        # r6: B -35 % linear (review P1 #3)
    "trim_blue_linear": [0.022, 0.060, 0.22],
    "clinker_linear": [0.27, 0.135, 0.060],          # r7: brown fired brick, WORKING_VALUE; keep scan relief/joints
    # Hero-local intended leaf palette, shared by opaque cores/far foliage and clipped boughs.
    # Retains the previous far-LOD starting palette; lit Low/High calibration remains WORKING_VALUE.
    "foliage_linear": [0.040, 0.068, 0.030],
    "conifer_linear": [0.030, 0.051, 0.0225],  # darker evergreen needles/core; WORKING_VALUE from 7197
    "hall_room_visibility_WORKING_VALUE": [0.65, 1.0],  # opaque glazing proxy: dark room below / sky above
}


def fetch_scan(asset: str, log=print) -> dict | None:
    """Download (once) and verify the CC0 scan maps. None when offline: the region then builds from noise only."""
    out = {}
    d = CC0 / asset
    d.mkdir(parents=True, exist_ok=True)
    for m in ("diff", "disp", "rough"):
        md5 = SCANS[asset][m]
        f = d / f"{asset}_{m}_2k.jpg"
        if not f.exists() or hashlib.md5(f.read_bytes()).hexdigest() != md5:
            try:
                req = urllib.request.Request(URL.format(a=asset, m=m), headers={"User-Agent": "asset-fetch/1.0"})
                data = urllib.request.urlopen(req, timeout=90).read()
            except Exception as e:      # noqa: BLE001
                log(f"  fire_station: cannot fetch {asset}/{m} ({e}); building WITHOUT this CC0 scan")
                return None
            if hashlib.md5(data).hexdigest() != md5:
                log(f"  fire_station: md5 mismatch for {asset}/{m}; building WITHOUT this CC0 scan")
                return None
            f.write_bytes(data)
        out[m] = f
    return out


def _lin(s):
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def _tile(path: Path, c: K.Ctx, size_m: float, shift=(0.0, 0.0), mirror=False) -> np.ndarray:
    """Scan map tiled over the atlas with an integer number of repeats along u (periodic), float32 (ny, nx, 3)."""
    reps = max(1, int(round(c.Lx / size_m)))
    n = int(round(c.nx / reps))
    a = np.asarray(Image.open(path).convert("RGB").resize((n, n), Image.LANCZOS), np.float32) / 255.0
    if mirror:
        a = a[:, ::-1]
    a = np.roll(a, (int(shift[1] * n), int(shift[0] * n)), (0, 1))
    t = np.tile(a, (int(np.ceil(c.ny / n)) + 1, reps, 1))[:c.ny]
    if t.shape[1] != c.nx:
        t = np.asarray(Image.fromarray((t * 255).astype(np.uint8)).resize((c.nx, c.ny), Image.LANCZOS), np.float32) / 255
    return t


def _scan_fields(asset, c, nmask, relief_m, seed_shift=(0.37, 0.61)):
    """(detail, height, rough_delta, chroma) from a scan, two decorrelated tilings mixed by a low-frequency mask.
    detail = luminance high-pass (mean ~1), height in metres (zero mean), rough_delta around 0."""
    sc = fetch_scan(asset)
    if sc is None:
        n1 = K.noise(c, 91, c.px * 2, 0.05, beta=0.5)
        n2 = K.noise(c, 92, 0.1, 1.0, beta=1.0)
        return 1 + 0.04 * n1 + 0.03 * n2, (0.3e-3 * n1).astype(np.float32), np.zeros_like(n1), None, False
    size = SCANS[asset]["size_m"]
    w = K.sstep(-0.4, 0.4, nmask)
    d0 = _lin(_tile(sc["diff"], c, size))
    d1 = _lin(_tile(sc["diff"], c, size, seed_shift, True))
    dif = d0 * (1 - w[..., None]) + d1 * w[..., None]
    lum = dif @ K.LUM
    low = K.blur(lum, 0.40 / c.px)
    detail = np.clip(lum / np.maximum(low, 1e-3), 0.5, 1.6)
    chroma = dif / np.maximum(lum[..., None], 1e-3)
    h = _tile(sc["disp"], c, size)[..., 0] * (1 - w) + _tile(sc["disp"], c, size, seed_shift, True)[..., 0] * w
    h = (h - K.blur(h, 0.25 / c.px))
    h = h / (h.std() + 1e-6) * relief_m
    r = _tile(sc["rough"], c, size)[..., 0] * (1 - w) + _tile(sc["rough"], c, size, seed_shift, True)[..., 0] * w
    return detail, h.astype(np.float32), (r - r.mean()).astype(np.float32), chroma, True


def _box(X, v, r, soft=0.0):
    """Mask of a layout rect (optionally inset by `soft` metres, hard edges)."""
    return (X >= r["u"][0] + soft) & (X < r["u"][1] - soft) & (v >= r["v"][0] + soft) & (v < r["v"][1] - soft)


def _gut(X, v, r, g=0.045):
    """Rect grown by the gutter (so mips / bilinear never pull the neighbour in)."""
    return (X >= r["u"][0] - g) & (X < r["u"][1] + g) & (v >= r["v"][0] - g) & (v < r["v"][1] + g)


def fire_station(nx=2048):
    c = K.Ctx(nx, nx, TILE[0], TILE[1], seed=701)
    X, Y = c.xy()
    v = TILE[1] - Y
    L = LAYOUT
    ss, noise = K.sstep, K.noise
    n_fine = noise(c, 1, c.px * 2, 0.04, beta=0.4)
    n_mid = noise(c, 2, 0.15, 1.2, beta=1.0)
    n_big = noise(c, 3, 1.5, 7.0, beta=1.3)
    n_run = noise(c, 4, 0.03, 0.6, beta=0.8, aniso=12.0)       # narrow along u, long along v (run-off)
    n_mask = noise(c, 5, 2.0, 7.0, beta=1.0)
    n_pat = noise(c, 6, 0.4, 3.0, beta=1.2)

    alb = np.zeros((c.ny, c.nx, 3), np.float32) + 0.2
    h = np.zeros((c.ny, c.nx), np.float32)
    rough = np.full((c.ny, c.nx), 0.8, np.float32)
    metal = np.zeros((c.ny, c.nx), np.float32)
    joint = np.zeros((c.ny, c.nx), np.float32)
    eid = np.zeros((c.ny, c.nx), np.float32)
    sources = []
    room_visibility = np.ones((c.ny, c.nx), np.float32)

    def put(mask, col, r_=None, m_=None):
        nonlocal alb, rough, metal
        alb = np.where(mask[..., None], col, alb)
        if r_ is not None:
            rough = np.where(mask, r_, rough)
        if m_ is not None:
            metal = np.where(mask, m_, metal)

    dirt_col = np.array([0.075, 0.068, 0.055], np.float32)
    green_col = np.array([0.060, 0.085, 0.040], np.float32)

    # ------------------------------------------------------------------ pale blue render band (u periodic)
    P = L["plaster"]
    pv = v - P["v0"]
    in_p = (pv > -0.03) & (pv < P["h"] + 0.03)
    det, hs, rd, _, ok = _scan_fields("painted_plaster_wall", c, n_mask, 0.45e-3)
    sources.append("polyhaven:painted_plaster_wall (CC0)" if ok else "painted_plaster_wall: procedural fallback")
    base = np.array(L["render_blue_linear"], np.float32)
    # r4: the scan detail is damped (0.9 -> 0.5) and the big tone noise halved: photo 7197 shows an even matt paint
    # r6 (review P1 #2): cloudy noise visible from 60 m -> isotropic variation cut 3x+, only run-off / splash stay
    tone = det ** 0.15 * (1 + 0.006 * n_mid + 0.008 * n_big - 0.01 * ss(0.2, 1.4, n_run))
    # repainted areas: slightly different batch of paint on a few big soft patches
    tone *= 1 + 0.006 * ss(0.6, 1.1, n_pat) - 0.006 * ss(0.7, 1.3, -n_pat)
    pcol = base[None, None, :] * tone[..., None]
    # splash zone above the plinth: soil splash + algae on the bottom 0.5 m, stronger in patches
    splash = ss(0.75, 0.0, pv) * (0.6 + 0.4 * ss(-0.5, 0.8, n_big)) * (0.75 + 0.25 * n_mid.clip(-1, 1))
    splash = np.clip(splash, 0, 0.8)
    # run-off under the top edge (flashing / sills above): streaks hanging 0.3-1.1 m below the top
    g_top = P["h"] - pv
    streak = ss(0.25, 1.1, n_run) * np.clip(1 - g_top / (0.5 + 0.4 * ss(-1, 1, n_big)), 0, 1) ** 1.4
    streak += 0.25 * ss(0.10, 0.0, g_top)
    # ADR 0116: discrete runoff below flashing, ending inside the 1 m gable band.
    # Metric authored WORKING_VALUE, not general wall noise. Hashing does not advance old material RNGs.
    drip_pitch = TILE[0] / 18
    drip_cell = np.floor(X / drip_pitch).astype(np.int64)
    drip_centre = (drip_cell + 0.20 + 0.60 * K.hash01(drip_cell, 73)) * drip_pitch
    drip_halfwidth = 0.05 + 0.045 * K.hash01(drip_cell, 79)
    drip_length = 0.40 + 0.50 * K.hash01(drip_cell, 83)
    drip = ss(drip_halfwidth * 1.7, drip_halfwidth, np.abs(X - drip_centre))
    drip *= np.clip(1 - g_top / drip_length, 0, 1) ** 1.2
    drip *= K.hash01(drip_cell, 89) > 0.30
    streak += 0.65 * drip
    streak = np.clip(streak, 0, 0.7) * (pv > P["base_h"])
    # hairline shrinkage cracks, sparse
    crk = ss(0.012, 0.004, np.abs(noise(c, 7, 0.5, 4.0, beta=1.4))) * ss(0.2, 0.9, noise(c, 8, 1.5, 6.0, beta=1.0))
    pcol = pcol * (1 - 0.55 * splash[..., None]) + (0.6 * dirt_col + 0.4 * green_col) * 0.55 * splash[..., None]
    pcol = pcol * (1 - 0.62 * streak[..., None]) + dirt_col * 0.62 * streak[..., None]
    pcol = pcol * (1 - 0.35 * crk[..., None])
    alb = np.where(in_p[..., None], pcol, alb)
    h = np.where(in_p, hs - 0.25e-3 * crk, h)
    rough = np.where(in_p, np.clip(0.90 + 0.25 * rd + 0.04 * splash, 0.75, 0.98), rough)
    render_mask = in_p & (splash < 0.05) & (streak < 0.05)

    # ------------------------------------------------------------------ blue trapezoidal roof sheet (eave at v0)
    R = L["roof"]
    rv = v - R["v0"]
    in_r = (rv > -0.03) & (rv < R["h"] + 0.03)
    ph = (X / R["rib_pitch"]) % 1.0                              # one rib per pitch: crown 40 %, flanks, pan
    crown = ss(0.18, 0.26, ph) * ss(0.74, 0.66, ph)
    prof = 0.035 * crown
    rblue = np.array(L["roof_blue_linear"], np.float32)
    # chalking: crowns fade first. r3: 0.10 -> 0.02 base and a darker chalk tone; the Unity frames (r2) showed a pale
    # lavender roof next to the saturated blue of the CC0 photos (7197, 20240626). WORKING_VALUE by eye.
    chalk = 0.02 + 0.03 * n_big + 0.025 * ss(0.0, 1.0, crown) + 0.015 * n_mid
    rcol = rblue[None, None, :] * (1 + 0.05 * n_mid)[..., None]
    rcol = rcol + (np.array([0.16, 0.22, 0.33], np.float32) - rcol) * np.clip(chalk, 0, 0.12)[..., None]
    # dirt collects in the pans and towards the eave; lap joint of the sheets every 1.0 m (4 ribs) and at mid length
    pan = 1 - crown
    rdirt = pan * (0.06 + 0.22 * ss(1.2, 0.0, rv) + 0.08 * ss(-0.3, 1.0, n_run)) + 0.30 * ss(0.10, 0.0, rv)
    lap_u = ss(0.012, 0.004, np.abs(((X + 0.5) % 1.0) - 0.5) - 0.0)
    lap_v = ss(0.010, 0.003, np.abs(rv - 1.7))
    screws = ss(0.016, 0.008, np.hypot(((X / R["rib_pitch"]) % 1.0 - 0.46) * R["rib_pitch"], ((rv - 0.2) % 0.75) - 0.375))
    rdirt = np.clip(rdirt + 0.30 * lap_v + 0.15 * lap_u * pan, 0, 0.85)
    rcol = rcol * (1 - rdirt[..., None]) + dirt_col * rdirt[..., None]
    rcol = np.where(screws[..., None] > 0.5, np.array([0.25, 0.25, 0.26], np.float32), rcol)
    alb = np.where(in_r[..., None], rcol, alb)
    h = np.where(in_r, prof + 0.002 * screws - 0.0015 * lap_v + 0.0002 * n_fine, h)
    rough = np.where(in_r, np.clip(0.48 + 0.30 * rdirt + 0.5 * np.clip(chalk, 0, 0.12), 0.42, 0.95), rough)   # r3: weathered coil coat ~0.6
    joint = np.where(in_r, np.clip(lap_v + lap_u * pan, 0, 1), joint)

    # ------------------------------------------------------------------ blue flashing / fascia strip
    F = L["fascia"]
    fv = v - F["v0"]
    in_f = (fv > -0.045) & (fv < F["h"] + 0.045)
    tblue = np.array(L["trim_blue_linear"], np.float32)
    fj = ss(0.008, 0.003, np.abs(((X + 0.3) % 2.0) - 1.0) - 0.0)
    fdrip = ss(0.4, 1.2, n_run) * ss(F["h"], 0.0, fv) * 0.4 + 0.3 * ss(0.05, 0.0, fv)
    fcol = tblue[None, None, :] * (1 + 0.06 * n_mid + 0.04 * n_big)[..., None]
    fcol = fcol + (np.array([0.14, 0.20, 0.38], np.float32) - fcol) * np.clip(0.03 + 0.04 * n_big, 0, 0.12)[..., None]
    fcol = fcol * (1 - np.clip(fdrip + 0.5 * fj, 0, 0.8)[..., None] * 0.7)
    alb = np.where(in_f[..., None], fcol, alb)
    h = np.where(in_f, -0.001 * fj + 0.006 * ss(0.03, 0.05, fv) * ss(F["h"] - 0.03, F["h"] - 0.05, fv) * 0.2, h)
    rough = np.where(in_f, 0.6 + 0.2 * fdrip, rough)

    # ------------------------------------------------------------------ concrete plinth strip
    Pl = L["plinth"]
    plv = v - Pl["v0"]
    in_pl = (plv > -0.045) & (plv < Pl["h"] + 0.045)
    cdet, chs, crd, _, ok = _scan_fields("concrete_wall_008", c, n_mask, 0.8e-3)
    sources.append("polyhaven:concrete_wall_008 (CC0)" if ok else "concrete_wall_008: procedural fallback")
    ccol = 0.27 * cdet * (1 + 0.04 * n_mid) * (1 - 0.35 * ss(0.25, 0.0, plv) * (0.6 + 0.4 * n_mid.clip(-1, 1)))
    ccol = ccol[..., None] * np.array([1.02, 1.0, 0.95], np.float32)
    ccol = ccol * (1 - 0.3 * ss(0.3, 1.2, n_run)[..., None] * ss(Pl["h"], 0.2, plv)[..., None])
    alb = np.where(in_pl[..., None], ccol, alb)
    h = np.where(in_pl, chs, h)
    rough = np.where(in_pl, np.clip(0.9 + 0.3 * crd, 0.75, 0.98), rough)

    # ------------------------------------------------------------------ clinker pier
    Bk = L["brick"]
    in_b = _gut(X, v, Bk)
    bdet, bhs, brd, bchroma, ok = _scan_fields("brick_wall_006", c, n_mask, 2.2e-3, (0.21, 0.43))
    sources.append("polyhaven:brick_wall_006 (CC0)" if ok else "brick_wall_006: procedural fallback")
    clk = np.array(L["clinker_linear"], np.float32)
    bcol = clk[None, None, :] * (bdet ** 1.1)[..., None] * (1 + 0.05 * n_mid)[..., None]
    mortar = ss(-0.6, -1.4, bhs / 2.2e-3)                       # deep parts of the scan relief = joints
    bcol = bcol * (1 - mortar[..., None]) + np.array([0.30, 0.29, 0.27], np.float32) * mortar[..., None]
    bv = v - Bk["v"][0]
    bcol = bcol * (1 - 0.45 * (ss(0.6, 0.0, bv) * (0.6 + 0.4 * n_mid.clip(-1, 1)))[..., None])
    alb = np.where(in_b[..., None], bcol, alb)
    h = np.where(in_b, bhs, h)
    rough = np.where(in_b, np.clip(0.82 + 0.3 * brd, 0.6, 0.97), rough)
    joint = np.where(in_b, mortar, joint)

    # ------------------------------------------------------------------ sectional garage door
    D = L["door"]
    in_d = _gut(X, v, D)
    du, dv = X - D["u"][0], v - D["v"][0]
    panel = 0.5
    pj = ss(0.010, 0.004, np.abs((dv % panel) - 0) ) + ss(0.010, 0.004, np.abs((dv % panel) - panel))
    rib = 0.5 + 0.5 * np.cos(2 * np.pi * dv / 0.125)            # shallow horizontal ribbing of the panels
    pid = np.floor(dv / panel)
    dcol = 0.62 * (1 + 0.012 * n_mid + 0.02 * (K.hash01(pid.astype(np.int64), 3) - 0.5))
    grime = ss(0.9, 0.0, dv) * (0.35 + 0.25 * n_mid.clip(-1, 1)) + 0.25 * ss(0.5, 1.4, n_run) * ss(4.0, 2.0, dv)
    grime += 0.5 * pj
    grime = np.clip(grime, 0, 0.85)
    dcolv = dcol[..., None] * np.array([1.0, 1.0, 0.985], np.float32)
    dcolv = dcolv * (1 - 0.6 * grime[..., None]) + dirt_col * 0.6 * grime[..., None]
    dh = 0.0015 * rib - 0.004 * np.clip(pj, 0, 1)
    drough = 0.45 + 0.3 * grime
    # two rows of two slit windows (frames black rubber, acrylic glazing)
    slit = np.zeros_like(X, bool)
    sfr = np.zeros_like(X, bool)
    for zc in (2.05, 2.55):
        for uc in (1.15, 2.45):
            a, b = np.abs(du - uc), np.abs(dv - zc)
            sfr |= (a < 0.36) & (b < 0.13)
            slit |= (a < 0.32) & (b < 0.09)
    dcolv = np.where(sfr[..., None], np.array([0.03, 0.03, 0.03], np.float32), dcolv)
    dcolv = np.where(slit[..., None], np.array([0.035, 0.045, 0.055], np.float32) * (1 + 0.3 * n_big[..., None]), dcolv)
    drough = np.where(slit, 0.12, np.where(sfr, 0.7, drough))
    dh = np.where(slit, -0.006, np.where(sfr, 0.003, dh))
    # side guides and bottom rubber seal, lintel shadow
    seal = dv < 0.05
    guide = (du < 0.06) | (du > 3.54)
    dcolv = np.where(seal[..., None], np.array([0.025, 0.025, 0.025], np.float32), dcolv)
    dcolv = np.where((guide & ~seal)[..., None], np.array([0.33, 0.34, 0.35], np.float32) * (1 - 0.4 * grime[..., None]), dcolv)
    drough = np.where(seal, 0.9, drough)
    alb = np.where(in_d[..., None], dcolv, alb)
    h = np.where(in_d, dh, h)
    rough = np.where(in_d, drough, rough)
    joint = np.where(in_d, np.clip(pj, 0, 1), joint)
    eid = np.where(in_d, (pid % 8) / 8.0, eid)

    # ------------------------------------------------------------------ windows
    glass_col = np.array([0.055, 0.070, 0.090], np.float32)     # r6: was 0.030/0.040/0.052 (read as holes)
    pvc = np.array([0.74, 0.74, 0.72], np.float32)

    def glazing(mask, gu, gv, wpane, hpane, bar=0.06, frame=0.10, wtot=None, htot=None, shape=None, trim=None,
                blind_seed=0, glass=None):
        """Window in a rect: gu/gv = local metres, panes of wpane x hpane, PVC frame, glass with blinds in some."""
        nonlocal alb, h, rough, room_visibility
        inside = shape if shape is not None else np.ones_like(mask)
        fr = np.zeros_like(mask)
        if shape is None:
            edge = np.minimum(np.minimum(gu, wtot - gu), np.minimum(gv, htot - gv))
            fr = edge < frame
        mu = np.abs(((gu + wpane / 2) % wpane) - wpane / 2)
        mv = np.abs(((gv + hpane / 2) % hpane) - hpane / 2)
        bars = (mu < bar / 2) | (mv < bar / 2)
        pane = (np.floor(gu / wpane) * 13 + np.floor(gv / hpane) * 7 + blind_seed).astype(np.int64)
        hsh = K.hash01(pane, 17)
        blind = (hsh > 0.62)[..., None] * np.array([0.30, 0.30, 0.28], np.float32) * (0.75 + 0.25 * np.cos(2 * np.pi * gv / 0.05))[..., None]
        dark_in = (0.6 + 0.8 * K.hash01(pane, 19))[..., None]
        # r6: baked sky gradient - darker towards the sill (ground / interior), brighter at the head (sky)
        gmax = float(gv[mask & inside].max()) if (mask & inside).any() else 1.0
        sky = (0.55 + 0.9 * np.clip(gv / max(gmax, 1e-3), 0, 1) ** 1.3)[..., None]
        if glass is not None:                      # big hall glazing: grey daylight reflection, no blinds (photo 7197)
            # ADR 0116 r1: hall-only sky at the head and dark interior below,
            # as in CC0 7197. WORKING_VALUE until the paired Unity capture.
            sky = (0.43 + 0.57 * np.clip(gv / max(gmax, 1e-3), 0, 1) ** 1.3)[..., None]
            gcol = glass[None, None, :] * sky * (0.85 + 0.3 * K.hash01(pane, 19))[..., None] * (1 + 0.10 * n_big)[..., None]
            # This opaque proxy combines a reflected sky and a recessed room.
            # Store the lower room's ambient visibility in the existing AO channel,
            # excluding frames, so reducing albedo does not hit a bright specular floor.
            low, high = L["hall_room_visibility_WORKING_VALUE"]
            visibility = low+(high-low)*np.clip(gv/max(gmax,1e-3),0,1)**1.3
            cavity_mask = mask & inside & ~(fr | bars)
            if trim is not None:
                cavity_mask &= ~trim[0]
            room_visibility = np.where(cavity_mask,visibility,room_visibility)
        else:                                      # three states: blind / net curtain / dark interior
            curtain = np.array([0.36, 0.36, 0.34], np.float32) * (0.85 + 0.15 * np.cos(2 * np.pi * gu / 0.11))[..., None]
            gcol = np.where((hsh > 0.66)[..., None], blind * 0.75 + glass_col * 0.25,
                            np.where((hsh > 0.36)[..., None], curtain * 0.55 + glass_col * sky * 0.45, glass_col * sky * dark_in))
        col = np.where((fr | bars)[..., None], pvc * (1 - 0.15 * ss(0.3, 0.0, gv)[..., None]), gcol)
        ro = np.where(fr | bars, 0.45, 0.07)
        hh = np.where(fr | bars, 0.0, -0.025)
        if trim is not None:                       # (mask, colour): outer painted band
            col = np.where(trim[0][..., None], trim[1], col)
            ro = np.where(trim[0], 0.55, ro)
            hh = np.where(trim[0], 0.012, hh)
        m = mask & inside
        alb = np.where(m[..., None], col, alb)
        rough = np.where(m, ro, rough)
        h = np.where(m, hh, h)

    # r4: the hall windows read mid grey on the overcast CC0 photo 7197 (sky reflection + light interior), far lighter
    # than the office glazing. Linear albedo WORKING_VALUE by eye.
    # r5: measured on the Unity r4b render (High overcast) the glass was 0.27-0.34 x the wall (linearised sRGB), on the
    # photo 0.45-1.0 x (mean ~0.7): doubled. Still a WORKING_VALUE (one overcast photo).
    hall_glass = np.array([0.0459, 0.0486, 0.05265], np.float32)  # ADR 0116 r1 WORKING_VALUE; office panes unchanged
    # arched window 3.4 x 3.4: segmental arch (rise 1.0 m above the 2.4 m springing), blue trim band 0.16 m
    A = L["win_arch"]
    ga = L["arch"]
    wA, hs_, rise = ga["w"], ga["spring"], ga["rise"]
    au = (X - A["u"][0]) * wA / (A["u"][1] - A["u"][0])             # window metres (the rect holds the window scaled)
    av = (v - A["v"][0]) * (hs_ + rise) / (A["v"][1] - A["v"][0])
    in_a = _gut(X, v, A)
    rad = ((wA / 2) ** 2 + rise ** 2) / (2 * rise)
    darc = np.hypot(au - wA / 2, av - (hs_ + rise - rad))        # distance from the arc centre
    in_shape = ((av <= hs_) | (darc <= rad)) & (au >= 0) & (au <= wA) & (av >= 0)
    trim_m = in_shape & (darc > rad - ga["trim"]) & (av > hs_ + rise - rad)
    # background outside the arch inside the rect = render (so the quad can cover the whole rect)
    glazing(in_a, au, av, ga["col"], ga["row"], bar=ga["bar"], shape=in_shape, trim=(trim_m, tblue * 1.0), blind_seed=3, glass=hall_glass)
    sill_a = in_a & in_shape & (av < 0.06)
    alb = np.where(sill_a[..., None], pvc * 0.8, alb)
    room_visibility = np.where(sill_a,1.0,room_visibility)
    out_a = in_a & ~in_shape
    alb = np.where(out_a[..., None], base * (det ** 0.8)[..., None], alb)
    rough = np.where(out_a, 0.9, rough)
    h = np.where(out_a, hs, h)

    # round window d 2.4 with a cross, blue ring 0.16 m
    Rw = L["win_round"]
    gr = L["round"]
    R0 = gr["d"] / 2
    ksc = gr["d"] / (Rw["u"][1] - Rw["u"][0])
    ru, rv2 = (X - Rw["u"][0]) * ksc - R0, (v - Rw["v"][0]) * ksc - R0
    in_rw = _gut(X, v, Rw)
    rr = np.hypot(ru, rv2)
    in_circ = rr <= R0
    ring = in_circ & (rr > R0 - gr["trim"])
    # r4 (photo 7197): one wide blue vertical post; the horizontal member is a thin white transom
    cross = in_circ & (np.abs(ru) < gr["cross"] / 2)
    glazing(in_rw, ru + R0, rv2 + R0, 9.0, 9.0, shape=in_circ, trim=(ring | cross, tblue), blind_seed=5, glass=hall_glass)
    transom = in_rw & in_circ & ~ring & ~cross & (np.abs(rv2) < 0.035)
    alb = np.where(transom[..., None], pvc, alb)
    room_visibility = np.where(transom,1.0,room_visibility)
    rough = np.where(transom, 0.45, rough)
    h = np.where(transom, 0.0, h)
    out_r = in_rw & ~in_circ
    alb = np.where(out_r[..., None], base * (det ** 0.8)[..., None], alb)
    rough = np.where(out_r, 0.9, rough)
    h = np.where(out_r, hs, h)

    for key, wp, hp, sd in (("win_plain", 0.75, 1.5, 11), ("win_ribbon", 0.6, 0.8, 12), ("win_small", 0.45, 0.9, 13)):
        W = L[key]
        wu, wv = X - W["u"][0], v - W["v"][0]
        glazing(_gut(X, v, W), np.clip(wu, 0, W["u"][1] - W["u"][0] - 1e-3), np.clip(wv, 0, W["v"][1] - W["v"][0] - 1e-3),
                wp, hp, wtot=W["u"][1] - W["u"][0], htot=W["v"][1] - W["v"][0], blind_seed=sd)

    # entrance door: aluminium frame, glazed upper part, kick plate
    E = L["door_entry"]
    eu, ev = X - E["u"][0], v - E["v"][0]
    in_e = _gut(X, v, E)
    efr = (eu < 0.08) | (eu > 1.02) | (ev > 2.12) | (np.abs(ev - 0.9) < 0.04) | (ev < 0.05)
    ecol = np.where((ev > 0.9)[..., None], glass_col, np.array([0.50, 0.51, 0.52], np.float32))
    ecol = np.where(efr[..., None], np.array([0.42, 0.43, 0.44], np.float32), ecol)
    alb = np.where(in_e[..., None], ecol, alb)
    rough = np.where(in_e, np.where((ev > 0.9) & ~efr, 0.07, 0.4), rough)
    h = np.where(in_e, np.where(efr, 0.0, -0.02), h)

    # ------------------------------------------------------------------ swatches
    Fg = L["flag"]
    in_fl = _gut(X, v, Fg)
    fcol2 = np.where((v - Fg["v"][0] > 0.5)[..., None], np.array([0.74, 0.74, 0.72], np.float32), np.array([0.52, 0.035, 0.05], np.float32))
    fcol2 = fcol2 * (1 + 0.06 * np.sin((X - Fg["u"][0]) * 11.0) + 0.02 * n_mid)[..., None]
    alb = np.where(in_fl[..., None], fcol2, alb)
    rough = np.where(in_fl, 0.85, rough)
    h = np.where(in_fl, 0.004 * np.sin((X - Fg["u"][0]) * 11.0), h)

    Sg = L["steel_galv"]
    in_sg = _gut(X, v, Sg)
    alb = np.where(in_sg[..., None], (0.42 * (1 + 0.10 * n_mid + 0.05 * n_fine))[..., None] * np.array([0.98, 1.0, 1.02], np.float32), alb)
    rough = np.where(in_sg, 0.5 + 0.08 * n_mid, rough)
    metal = np.where(in_sg, 0.85, metal)
    h = np.where(in_sg, 0.0, h)

    Pv = L["pvc_white"]
    in_pv = _gut(X, v, Pv)
    alb = np.where(in_pv[..., None], pvc * (1 + 0.03 * n_mid - 0.12 * ss(0.5, 1.5, n_run))[..., None], alb)
    rough = np.where(in_pv, 0.45, rough)
    h = np.where(in_pv, 0.0, h)

    Mb = L["membrane"]
    in_m = _gut(X, v, Mb)
    mseam = ss(0.03, 0.01, np.abs(((v - Mb["v"][0]) % 1.0) - 0.5) - 0.0)
    mcol = 0.11 * (1 + 0.10 * n_mid + 0.08 * n_big + 0.05 * n_fine) * (1 - 0.3 * mseam)
    alb = np.where(in_m[..., None], mcol[..., None] * np.array([1.0, 1.0, 1.03], np.float32), alb)
    rough = np.where(in_m, 0.92, rough)
    h = np.where(in_m, 0.003 * mseam + 0.0004 * n_fine, h)

    Dk = L["dark"]
    in_dk = _gut(X, v, Dk)
    alb = np.where(in_dk[..., None], np.array([0.03, 0.03, 0.032], np.float32) * (1 + 0.15 * n_fine)[..., None], alb)
    rough = np.where(in_dk, 0.75, rough)
    h = np.where(in_dk, 0.0, h)

    Gl = L["glass"]
    in_gl = _gut(X, v, Gl)
    alb = np.where(in_gl[..., None], glass_col * (1 + 0.2 * n_big)[..., None], alb)
    rough = np.where(in_gl, 0.07, rough)
    h = np.where(in_gl, 0.0, h)

    Oc = L["ochre"]
    in_oc = _gut(X, v, Oc)
    ocol = np.array([0.50, 0.33, 0.13], np.float32) * (det ** 0.8 * (1 + 0.04 * n_mid))[..., None]
    ocol = ocol * (1 - 0.4 * (ss(0.3, 1.2, n_run) * ss(Oc["v"][1], Oc["v"][0], v))[..., None])
    alb = np.where(in_oc[..., None], ocol, alb)
    rough = np.where(in_oc, 0.9, rough)
    h = np.where(in_oc, hs, h)

    # far-LOD thuja body: leaf green of the shell texture seen from a distance (core albedo x ~2.5, materials.py
    # hedge_thuja note 'core ~0.4 x leaf'), mottled so the cone is not a flat colour
    Tf = L["thuja_far"]
    in_tf = _gut(X, v, Tf)
    tcol = np.array(L["foliage_linear"], np.float32) * (1 + 0.30 * n_mid + 0.15 * n_big + 0.25 * n_fine).clip(0.4, 1.8)[..., None]
    alb = np.where(in_tf[..., None], tcol, alb)
    rough = np.where(in_tf, 0.9, rough)
    h = np.where(in_tf, 0.004 * n_mid, h)

    # ADR 0116: evergreen inner mass is darker than the thuja shell. Reuse an
    # unused opaque-atlas cell; the hero keeps its existing material slots.
    in_cf = _gut(X, v, L["conifer_core"])
    # Real CC0 needle RGB supplies the clumps; the opaque inter-needle shadow
    # fills the gaps that disappear from alpha cards at road-view mip levels.
    needle = np.array(_conifer_sprite())
    iy, ix = np.nonzero(in_cf)
    rect = L["conifer_core"]
    nx = np.floor((X[iy,ix]-rect["u"][0])/(rect["u"][1]-rect["u"][0])*needle.shape[1]*3).astype(int)%needle.shape[1]
    ny = np.floor((rect["v"][1]-v[iy,ix])/(rect["v"][1]-rect["v"][0])*needle.shape[0]).astype(int)%needle.shape[0]
    covered = needle[ny,nx,3].astype(np.float32)/255
    target = np.array(L["conifer_linear"],np.float32)
    ccol = _lin(needle[ny,nx,:3].astype(np.float32)/255)*covered[:,None]+target*.55*(1-covered[:,None])
    ccol *= target/np.maximum(ccol.mean(0,dtype=np.float64),1e-6)
    alb[iy,ix] = ccol*(1+.12*n_mid[iy,ix])[:,None]
    rough[iy,ix] = .97-.06*covered
    h[iy,ix] = .002*(.6*covered+.4*n_mid[iy,ix])
    sources.append("polyhaven:fir_tree_01 needle RGB (CC0; authored opaque canopy derivative)")

    alb = np.clip(alb, 0.012, 0.9).astype(np.float32)
    s = K.SurfaceSet("fire_station", c, alb, h.astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32),
                     eid.astype(np.float32), np.clip(joint, 0, 1).astype(np.float32), metal=metal.astype(np.float32),
                     ao_scales=(0.01, 0.03, 0.08), ao_k=0.5)
    s.source = "; ".join(sources)
    s.ao_extra = room_visibility
    s.concrete_mean = [round(float(x), 4) for x in alb[render_mask].mean(0)]      # clean render mean (name kept for build_all)
    return s


def _font(px):
    import matplotlib
    p = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf" / "DejaVuSans-Bold.ttf"
    return ImageFont.truetype(str(p), px)


# fire_station_alpha.png layout in UV 0..1 (u right, v up): metres -> uv via the rects below
ALPHA_LAYOUT = {
    "size_px": [2048, 1024],
    "fence_bay": {"u": [0.0, 0.3125], "v": [0.5, 1.0], "size_m": [2.5, 1.6]},      # 640 x 512 px
    "gate_bay": {"u": [0.3125, 0.625], "v": [0.5, 1.0], "size_m": [2.5, 1.6]},
    "swatch_blue": {"u": [0.64, 0.70], "v": [0.55, 0.95]},
    "lettering": {"u": [0.0, 1.0], "v": [0.27, 0.48], "size_m": [7.6, 0.80]},
    "number": {"u": [0.0, 0.24], "v": [0.02, 0.25], "size_m": [1.7, 0.80]},     # r4: digits 0.6 m (photo 7197)
    # r7: disjoint from ALL baseline LOD alpha UVs (548/98/0 triangles); same existing material slot.
    "conifer_bough": {"u": [0.30, 0.43], "v": [0.025, 0.24], "gutter_px": 16},
}
_cb = ALPHA_LAYOUT["conifer_bough"]
_aw, _ah = ALPHA_LAYOUT["size_px"]
_gp = _cb["gutter_px"]
_cb["inner_uv"] = [(int(_cb["u"][0] * _aw) + _gp) / _aw,
                   (int(_cb["v"][0] * _ah) + _gp) / _ah,
                   (int(_cb["u"][1] * _aw) - _gp) / _aw,
                   (int(_cb["v"][1] * _ah) - _gp) / _ah]


def _conifer_sprite(log=print):
    """Hash-pinned CC0 short-needle conifer (not verified Picea), with a procedural clean-clone fallback."""
    manifest = json.loads((LANDMARK / "conifer_source.json").read_text(encoding="utf-8"))
    images = {}
    try:
        for source in manifest["files"]:
            path = REPO / manifest["raw_dir"] / source["file"]
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                request = urllib.request.Request(source["url"], headers={"User-Agent": "kamion-CC0-asset-fetch/1.0"})
                data = urllib.request.urlopen(request, timeout=90).read()
                if hashlib.sha256(data).hexdigest() != source["sha256"]:
                    raise ValueError("conifer source download SHA256 mismatch")
                path.write_bytes(data)
            if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError("conifer source cache SHA256 mismatch")
            images[source["map"]] = Image.open(path).copy()
        crop = tuple(manifest["crop_xyxy"])
        rgb = np.array(images["diff"].convert("RGB").crop(crop))
        alpha = np.array(images["alpha"].convert("RGB").getchannel("R").crop(crop))
        labels, count = ndimage.label(alpha > 32)
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        if not count or sizes.max() < 100:
            raise ValueError("empty conifer twig component")
        keep = ndimage.binary_dilation(labels == sizes.argmax(), iterations=1)
        alpha = np.where(keep, alpha, 0).astype(np.uint8)
        applied = True
    except (OSError, ValueError, KeyError) as error:
        log(f"  fire_station: CC0 conifer unavailable ({error}); deterministic short-needle fallback")
        # Fallback is explicitly procedural, not mislabelled as the scan. No global RNG is consumed.
        im = Image.new("L", (256, 320)); draw = ImageDraw.Draw(im)
        draw.line((128, 319, 128, 8), fill=255, width=4)
        for j in range(8):
            y = 42 + j * 31
            for side in (-1, 1):
                tip = (128 + side * (22 + j * 9), y - 24)
                draw.line((128, y + 10, *tip), fill=255, width=3)
                for k in range(1, 7):
                    t = k / 7; x = 128 + (tip[0] - 128) * t; yy = y + 10 + (tip[1] - y - 10) * t
                    draw.line((x, yy, x + side * 10, yy - 13), fill=255, width=2)
        alpha = np.array(im); rgb = np.full((*alpha.shape, 3), 128, np.uint8); applied = False
    covered = alpha >= 128
    linear = _lin(rgb.astype(np.float32) / 255)
    linear *= np.array(LAYOUT["conifer_linear"], np.float32) / np.maximum(linear[covered].mean(0, dtype=np.float64), 1e-6)
    rgb = np.clip(np.rint(K.srgb_encode(np.clip(linear, 0, 1)) * 255), 0, 255).astype(np.uint8)
    rgba = np.dstack([rgb, alpha]); yy, xx = np.where(alpha > 32)
    rgba = rgba[yy.min():yy.max() + 1, xx.min():xx.max() + 1]
    root_x = float(np.median(np.where(rgba[-3:, :, 3] > 32)[1]))
    half = int(np.ceil(max(root_x, rgba.shape[1] - root_x)))
    centred = Image.new("RGBA", (half * 2, rgba.shape[0]))
    centred.alpha_composite(Image.fromarray(rgba), (round(half - root_x), 0))
    status = {"id": manifest["id"], "applied": applied, "species_status": manifest["species_status"],
              "source_sha256": {f["map"]: f["sha256"] for f in manifest["files"]},
              "intended_mean_rgb_linear_WORKING_VALUE": LAYOUT["conifer_linear"]}
    (LANDMARK / "conifer_foliage_meta.json").write_text(json.dumps(status, indent=1) + "\n", encoding="utf-8")
    return centred


def _conifer_patch():
    """Two sprays share one stem root, one atlas cell and the existing runtime alpha material.

    This is an authored CC0 derivative, not scanned spruce geometry. Content UV removes empty
    thumbnail margins; the 16-pixel outer gutter and bottom-centred branch attachment stay intact.
    """
    r = ALPHA_LAYOUT["conifer_bough"]; W, H = ALPHA_LAYOUT["size_px"]
    x0, x1 = int(r["u"][0] * W), int(r["u"][1] * W)
    y0, y1 = H - int(r["v"][1] * H), H - int(r["v"][0] * H)
    width, height, gap = x1-x0, y1-y0, r["gutter_px"]
    sprite = _conifer_sprite()
    # Retain the current packed single-spray covered mean, so composition is not a palette change.
    reference = sprite.copy(); reference.thumbnail((width-2*gap, height-2*gap), Image.Resampling.LANCZOS)
    ref = np.array(reference); ref_keep = ref[..., 3] >= 128
    target = (_lin(ref[..., :3].astype(np.float64)/255)[ref_keep].mean(0)
              if ref_keep.any() else np.array(LAYOUT["conifer_linear"]))
    canvas = Image.new("RGBA", (1200, 900)); layer = Image.new("RGBA", canvas.size)
    root = (600, 840)
    layer.alpha_composite(sprite, (round(root[0]-sprite.width/2), root[1]-sprite.height))
    for angle in (-26, 26):
        canvas.alpha_composite(layer.rotate(angle, Image.Resampling.BICUBIC, center=root))
    a = np.array(canvas); yy, xx = np.where(a[..., 3] > 32)
    if not len(xx):
        r["inner_uv"] = [(x0+gap)/W, (H-y1+gap)/H, (x1-gap)/W, (H-y0-gap)/H]
        return np.zeros((height, width, 4), np.uint8)
    assert not ((a[0, :, 3] > 32).any() or (a[-1, :, 3] > 32).any()
                or (a[:, 0, 3] > 32).any() or (a[:, -1, 3] > 32).any()), "Clipped root bundle"
    twig = canvas.crop((int(xx.min()), int(yy.min()), int(xx.max())+1, int(yy.max())+1))
    a = np.array(twig); stem = float(np.median(np.where(a[-3:, :, 3] > 32)[1]))
    half = int(np.ceil(max(stem, twig.width-stem)))
    centred = Image.new("RGBA", (half*2, twig.height)); centred.alpha_composite(twig, (round(half-stem), 0))
    # Extra 4 px allow root-centred UV filter padding while retaining the full outer gutter.
    centred.thumbnail((width-2*(gap+4), height-2*gap), Image.Resampling.LANCZOS)
    patch = Image.new("RGBA", (width, height))
    patch.alpha_composite(centred, ((width-centred.width)//2, height-gap-centred.height))
    pa = np.array(patch); covered = pa[..., 3] >= 128
    linear = _lin(pa[..., :3].astype(np.float64)/255)
    if covered.any():
        linear *= target / np.maximum(linear[covered].mean(0), 1e-6)
    pa[..., :3] = np.clip(np.rint(K.srgb_encode(np.clip(linear, 0, 1))*255), 0, 255).astype(np.uint8)
    yy, xx = np.where(pa[..., 3] >= 32); bottom = int(yy.max())
    stem = float(np.median(np.where(pa[bottom-2:bottom+1, :, 3] >= 32)[1]))+.5
    half = int(np.ceil(max(stem-xx.min(), xx.max()+1-stem)+2))
    left, right = int(np.floor(stem-half)), int(np.ceil(stem+half))
    top = max(gap, int(yy.min())-2)
    assert left >= gap and right <= width-gap, "Root-centred UV must preserve outer gutter"
    r["inner_uv"] = [(x0+left)/W, (H-y1+gap)/H, (x0+right)/W, (H-y0-top)/H]
    r["composition"] = "two root-connected sprays, rotations -26/+26 degrees, authored CC0 derivative"
    r["content_alpha32_bbox_px"] = [int(xx.min()), int(yy.min()), int(xx.max())+1, bottom+1]
    empty = pa[..., 3] == 0
    nearest = ndimage.distance_transform_edt(empty, return_distances=False, return_indices=True)
    pa[..., :3][empty] = pa[nearest[0][empty], nearest[1][empty], :3]
    return pa


def alpha_texture(path: Path | None = None):
    """fire_station_alpha.png 2048 x 1024 RGBA (see ALPHA_LAYOUT). Painted blue steel fence: posts are geometry;
    the bay holds top / bottom rails and vertical bars every 0.125 m; the gate bay adds a diagonal brace."""
    W, H = ALPHA_LAYOUT["size_px"]
    rng = np.random.default_rng(702)
    rgb = np.zeros((H, W, 3), np.float32)
    a = np.zeros((H, W), np.float32)
    x = (np.arange(W) + 0.5) / W
    y = 1 - (np.arange(H) + 0.5) / H
    Xg, Yg = np.meshgrid(x, y)
    # r6 (review P1 #7): real fence is dark navy, target ~45/55/85 sRGB in the frame (was trim blue x 0.85: toy blue)
    blue = np.array([0.022, 0.032, 0.075], np.float32)
    n = np.asarray(Image.fromarray(rng.standard_normal((H // 8, W // 8)).astype(np.float32)).resize((W, H), Image.BICUBIC))

    for key in ("fence_bay", "gate_bay"):
        r = ALPHA_LAYOUT[key]
        m = (Xg >= r["u"][0]) & (Xg < r["u"][1]) & (Yg >= r["v"][0]) & (Yg < r["v"][1])
        bu = (Xg - r["u"][0]) / (r["u"][1] - r["u"][0]) * r["size_m"][0]
        bv = (Yg - r["v"][0]) / (r["v"][1] - r["v"][0]) * r["size_m"][1]
        bars = np.abs(((bu + 0.0625) % 0.125) - 0.0625) < 0.011
        on = bars & (bv > 0.12) & (bv < 1.52)
        on |= np.abs(bv - 0.14) < 0.025
        on |= np.abs(bv - 1.36) < 0.025
        if key == "gate_bay":
            on |= np.abs(bv - (0.14 + (bu / 2.5) * 1.22)) < 0.03          # diagonal brace
            on |= (bv < 0.10) & (bv > 0.02)                                # bottom beam of the sliding gate
        on &= (bu > 0.012) & (bu < 2.488)
        a[m & on] = 1
        rgb[m] = blue
    r = ALPHA_LAYOUT["swatch_blue"]
    m = (Xg >= r["u"][0] - 0.01) & (Xg < r["u"][1] + 0.01) & (Yg >= r["v"][0] - 0.03) & (Yg < r["v"][1] + 0.03)
    a[m] = 1
    rgb[m] = blue
    rgb *= (1 + 0.14 * n - 0.30 * (Yg < 0.56) * (Yg > 0.5))[..., None]     # road spray at the foot
    # rust blooms on the fence
    rust = (n > 1.6) & (Yg > 0.5)
    rgb[rust] = np.array([0.16, 0.07, 0.03], np.float32)

    # lettering: bold sans, dark red (as on the facade), slightly faded; rendered at 4x and box filtered
    red = np.array([0.25, 0.030, 0.050], np.float32)     # r4: crimson of photo 7197 (was 0.33: read signal red in Unity)
    for key, text in (("lettering", "PAŃSTWOWA  STRAŻ  POŻARNA"), ("number", "998")):
        r = ALPHA_LAYOUT[key]
        x0, x1 = int(r["u"][0] * W), int(r["u"][1] * W)
        y1, y0 = H - int(r["v"][0] * H), H - int(r["v"][1] * H)
        w4, h4 = (x1 - x0) * 4, (y1 - y0) * 4
        im = Image.new("L", (w4, h4), 0)
        dr = ImageDraw.Draw(im)
        px = int(h4 * 0.62)
        f = _font(px)
        while dr.textlength(text, font=f) > w4 * 0.97 and px > 8:
            px -= 4
            f = _font(px)
        bb = dr.textbbox((0, 0), text, font=f)
        dr.text(((w4 - (bb[2] - bb[0])) / 2 - bb[0], (h4 - (bb[3] - bb[1])) / 2 - bb[1]), text, fill=255, font=f)
        if key == "number":                        # r4: digits 0.6 m tall as on photo 7197. The handset roundel left of
            im = Image.new("L", (w4, h4), 0)       # them on the facade is deliberately NOT drawn (ADR 0070: no emblems /
            dr = ImageDraw.Draw(im)                # pictograms)
            f = _font(int(h4 * 0.98))
            bb = dr.textbbox((0, 0), text, font=f)
            sc = min(1.0, (w4 * 0.96) / (bb[2] - bb[0]), (h4 * 0.76) / (bb[3] - bb[1]))
            f = _font(int(h4 * 0.98 * sc))
            bb = dr.textbbox((0, 0), text, font=f)
            dr.text(((w4 - (bb[2] - bb[0])) / 2 - bb[0], (h4 - (bb[3] - bb[1])) / 2 - bb[1]), text, fill=255, font=f)
        m4 = np.asarray(im, np.float32) / 255
        m1 = m4.reshape(y1 - y0, 4, x1 - x0, 4).mean((1, 3))
        a[y0:y1, x0:x1] = m1
        rgb[y0:y1, x0:x1] = red * (1 + 0.10 * n[y0:y1, x0:x1, None])
    # Append only AFTER every legacy draw/noise operation: no RNG advancement or old pixel changes.
    r = ALPHA_LAYOUT["conifer_bough"]
    x0, x1 = int(r["u"][0] * W), int(r["u"][1] * W)
    y0, y1 = H - int(r["v"][1] * H), H - int(r["v"][0] * H)
    gap = r["gutter_px"]
    pa = _conifer_patch()
    rgb[y0:y1, x0:x1] = _lin(pa[..., :3].astype(np.float32) / 255)
    a[y0:y1, x0:x1] = pa[..., 3].astype(np.float32) / 255
    img = np.dstack([K.srgb_encode(np.clip(rgb, 0, 1)), a])
    path = path or (REPO / "art-source" / "world" / "textures" / "fire_station_alpha.png")
    K.save_png(path, img, "RGBA")
    return path


def write_layout():
    LANDMARK.mkdir(parents=True, exist_ok=True)
    p = LANDMARK / "atlas_layout.json"
    # Recompute from the same pixels as alpha_texture: no stale full-cell UV after a standalone layout build.
    _conifer_patch()
    # Hero-only shell alias: keep the route's procedural texture/palette untouched.
    # The alias receives an A-correct linear multiplier, retaining the same .97 roughness and alpha settings.
    worldgen = str(REPO / "tools" / "worldgen")
    if worldgen not in sys.path:
        sys.path.insert(0, worldgen)
    from streetscape.hedge_textures import shell
    thuja = np.array(shell("thuja"))
    shell_mean = _lin(thuja[..., :3].astype(np.float32) / 255)[thuja[..., 3] >= 128].mean(0, dtype=np.float64)
    LAYOUT["thuja_shell_tint_linear"] = (np.array(LAYOUT["foliage_linear"]) / np.maximum(shell_mean, 1e-6)).tolist()
    text = json.dumps({"atlas": LAYOUT, "alpha": {k: v for k, v in ALPHA_LAYOUT.items()}}, indent=1, sort_keys=True) + "\n"
    if not p.exists() or p.read_text(encoding="utf-8") != text:
        p.write_text(text, encoding="utf-8", newline="\n")
    return p


FIRE_STATION_SETS = {
    "fire_station": dict(fn=fire_station, tile_m=list(TILE), target=0.57, atlas=True,
        uv="mesh_uv0_metres (atlas position in metres; layout in art-source/world/landmarks/fire_station_jrg2/"
           "atlas_layout.json)",
        slots=["fire_station (hero fire station asset, ADR 0070)"],
        note="Atlas 14 x 14 m (2048 x 2048 High, 6.8 mm/texel): pale blue render band with splash zone and run-off, "
             "blue trapezoidal roof sheet, flashing, plinth, sectional door, clinker pier, windows, swatches. Detail / "
             "relief / roughness from CC0 scans (Poly Haven: Painted Plaster Wall, Brick Wall 006, Concrete Wall "
             "008); colours WORKING_VALUE by eye from CC0 photos. albedo_target_mean_lum_linear applies to the "
             "clean render, not the atlas mean."),
}


if __name__ == "__main__":
    if "--alpha" in sys.argv:
        print(alpha_texture())
    if "--layout" in sys.argv:
        print(write_layout())
