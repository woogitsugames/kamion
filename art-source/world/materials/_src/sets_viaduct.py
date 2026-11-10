"""Texture work of the hero viaduct at Rondo Bieżeństwa (ADR 0067).

`viaduct_concrete`  one calibrated strip atlas (tile 24 x 12 m, mesh UV0 in metres) for every concrete and painted
                    face of the asset: red cornice band, the unrolled half cross-section of the box girder (edge beam,
                    cantilever soffit, sloped web, bottom flange), the unrolled column and the abutment wall.
                    Base = CC0 scan "Concrete Wall 008" (Poly Haven, CC0 1.0; photo Charlotte Baglioni, processing
                    Dario Barresi; docs/LICENSES.md) used as high-pass detail (albedo), relief and roughness;
                    the generator adds what belongs to *this* structure: pour joints, formwork panel lines, tie holes,
                    drain outlets with lime / rust tails, drips below the cornice joints, soot on the bottom flange,
                    leak streaks under the expansion joints, faded paint. No pixels of the Mapillary references are
                    used (ADR 0065): they only told us what to draw.
`viaduct_steel.png` alpha-tested railing infill + galvanised steel swatch (art-source/world/textures, versioned).

The layout below is the contract with tools/blender/world/landmarks/make_viaduct.py (written to
art-source/world/landmarks/viaduct_biezenstwa/atlas_layout.json).

    uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only viaduct_concrete
    uv run --project tools/worldgen python art-source/world/materials/_src/sets_viaduct.py --railing --layout
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pbrkit as K  # noqa: E402

REPO = HERE.parents[3]
LANDMARK = REPO / "art-source" / "world" / "landmarks" / "viaduct_biezenstwa"
SCAN_DIR = REPO / "Data" / "raw" / "cc0" / "polyhaven" / "concrete_wall_008"      # not versioned (Data/raw)
SCAN_URL = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/concrete_wall_008/concrete_wall_008_{m}_2k.jpg"
# md5 from https://api.polyhaven.com/files/concrete_wall_008 (2026-11-10)
SCAN = {"diff": "9e834dad5c07a3ba452a2ad0f1454c9f", "disp": "5bb8b340c56eb483f8fdb69b6ff29d6f",
        "rough": "8b4997c293727d89322a7dbe30ae34ae"}
SCAN_SIZE_M = 2.71            # asset "dimensions" 2710 mm (Poly Haven API)

TILE = (24.0, 12.0)
# v in metres from the bottom of the image; u along. Bands keep >= 5 cm gutters filled with their own edge colour.
LAYOUT = {
    "tile_m": list(TILE),
    "cornice": {"v0": 0.06, "h": 0.57},                       # v0 = bottom edge of the red plate
    "girder": {"v0": 0.76, "lip": 0.08, "beam": 0.14, "cant": 2.212, "web": 1.535, "bottom": 2.0},
    "pier": {"v0": 6.90, "front_c": 0.38, "back_c": 2.04, "stripe_w": 0.40, "perimeter": 3.32, "u_max": 8.0},
    "wall": {"v0": 10.65, "period": 1.30, "u_max": 8.0},
    "swatch_dark": {"u": [9.1, 9.9], "v": [7.1, 7.9]},        # elastomer bearings, expansion joint rubber
    "swatch_plain": {"u": [11.2, 13.8], "v": [7.1, 9.6]},     # bearing plinths, footings, pipe hangers' pads
    "u_shift": {"left": 0.0, "right": 11.0, "deck": 5.0},     # per side / per deck so features never line up
    "albedo_concrete": 0.36, "paint_red_linear": [0.36, 0.060, 0.065],
}
CONCRETE = 0.36               # WORKING_VALUE: weathered structural concrete (PCC 0.2-0.35 soiled .. 0.35+ clean,
                              # arXiv:2409.12242 p. 7; the deck underside is sheltered and stays light)


def fetch_scan(log=print) -> dict | None:
    """Download (once) and verify the CC0 scan maps. None when offline: the set then builds from noise only."""
    out = {}
    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    for m, md5 in SCAN.items():
        f = SCAN_DIR / f"concrete_wall_008_{m}_2k.jpg"
        if not f.exists() or hashlib.md5(f.read_bytes()).hexdigest() != md5:
            try:
                req = urllib.request.Request(SCAN_URL.format(m=m), headers={"User-Agent": "asset-fetch/1.0"})
                data = urllib.request.urlopen(req, timeout=60).read()
            except Exception as e:      # noqa: BLE001
                log(f"  viaduct_concrete: cannot fetch {m} ({e}); building WITHOUT the CC0 scan base")
                return None
            if hashlib.md5(data).hexdigest() != md5:
                log(f"  viaduct_concrete: md5 mismatch for {m}; building WITHOUT the CC0 scan base")
                return None
            f.write_bytes(data)
        out[m] = f
    return out


def _tile_scan(path: Path, c: K.Ctx, mirror=False, shift=(0.0, 0.0)) -> np.ndarray:
    """Scan map resampled to the atlas texel and tiled at 24/9 = 2.667 m (1.6 % under its real 2.71 m) so the
    24 m strip stays periodic along u. Returns float32 (ny, nx) in 0..1 (first channel for grey maps)."""
    reps = int(round(c.Lx / SCAN_SIZE_M))
    n = int(round(c.nx / reps))
    im = Image.open(path).convert("RGB").resize((n, n), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255.0
    if mirror:
        a = a[:, ::-1]
    a = np.roll(a, (int(shift[1] * n), int(shift[0] * n)), (0, 1))
    ry = int(np.ceil(c.ny / n)) + 1
    t = np.tile(a, (ry, reps, 1))[:c.ny]
    if t.shape[1] != c.nx:
        t = np.asarray(Image.fromarray((t * 255).astype(np.uint8)).resize((c.nx, c.ny), Image.LANCZOS), np.float32) / 255
    return t


def _lin(s):
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def _streaks(X, g, items, seedn):
    """Run-off streaks: items = [(u0, width, length, strength)], g = metres below the source line (>= 0)."""
    out = np.zeros_like(X)
    for u0, wd, ln, k in items:
        du = np.abs(((X - u0 + TILE[0] / 2) % TILE[0]) - TILE[0] / 2)
        wob = 1.0 + 0.35 * seedn
        out += k * np.exp(-(du / (wd * wob)) ** 2) * np.clip(1 - g / ln, 0, 1) ** 1.5 * (g >= 0)
    return out


def viaduct_concrete(nx=4096):
    c = K.Ctx(nx, nx // 2, TILE[0], TILE[1], seed=671)
    X, Y = c.xy()
    v = TILE[1] - Y
    L = LAYOUT
    sstep, noise = K.sstep, K.noise
    n_fine = noise(c, 1, c.px * 2, 0.03, beta=0.4)
    n_mid = noise(c, 2, 0.15, 1.2, beta=1.0)
    n_big = noise(c, 3, 1.5, 9.0, beta=1.3)
    n_str = noise(c, 4, 0.02, 0.5, beta=0.8, aniso=0.08)      # streaky across u (run-off direction = v)
    n_mask = noise(c, 5, 2.5, 8.0, beta=1.0)

    # ---- base concrete: scan detail (two decorrelated tilings) or noise fallback
    scan = fetch_scan()
    if scan:
        wmix = sstep(-0.4, 0.4, n_mask)[..., None]
        d0 = _tile_scan(scan["diff"], c)
        d1 = _tile_scan(scan["diff"], c, mirror=True, shift=(0.37, 0.61))
        dif = _lin(d0 * (1 - wmix) + d1 * wmix)
        lum = dif @ K.LUM
        low = K.blur(lum, 0.45 / c.px)
        detail = np.clip(lum / np.maximum(low, 1e-3), 0.6, 1.5)             # high-pass (< ~0.5 m) of the scan
        chroma = dif.reshape(-1, 3).mean(0)
        chroma = chroma / (chroma @ K.LUM)
        chroma = 0.25 * chroma + 0.75 * np.array([1.035, 0.995, 0.925], np.float32)   # scan is yellow-olive; the
        # reference frames show a warm light grey (hue by eye, WORKING_VALUE)
        chroma = chroma / (chroma @ K.LUM)
        w1 = wmix[..., 0]
        hs = _tile_scan(scan["disp"], c)[..., 0] * (1 - w1) + _tile_scan(scan["disp"], c, True, (0.37, 0.61))[..., 0] * w1
        hs = (hs - K.blur(hs, 0.3 / c.px)) * 6e-3                           # +-~1.5 mm relief, WORKING_VALUE
        rs = _tile_scan(scan["rough"], c)[..., 0] * (1 - w1) + _tile_scan(scan["rough"], c, True, (0.37, 0.61))[..., 0] * w1
        rough = np.clip(0.88 + 0.5 * (rs - rs.mean()), 0.7, 0.97)
        source = "polyhaven:concrete_wall_008 (CC0)"
    else:
        detail = 1 + 0.05 * n_fine + 0.03 * n_mid
        chroma = np.array([1.03, 0.995, 0.93], np.float32)
        hs = 0.25e-3 * n_fine + 0.4e-3 * n_mid
        rough = np.full_like(X, 0.88)
        source = "procedural fallback (scan not available)"
    tone = detail * (1 + 0.035 * n_mid + 0.05 * n_big)
    h = hs.astype(np.float32)
    dirt = np.zeros_like(X)        # dark soiling 0..1
    lime = np.zeros_like(X)        # efflorescence 0..1
    rust = np.zeros_like(X)
    joint = np.zeros_like(X)
    red = np.zeros_like(X)

    # ---- girder band (unrolled half section)
    G = L["girder"]
    g = v - G["v0"]
    g_beam0, g_cant0 = G["lip"], G["lip"] + G["beam"]
    g_web0 = g_cant0 + G["cant"]
    g_bot0 = g_web0 + G["web"]
    g_end = g_bot0 + G["bottom"]
    in_g = (g > -0.05) & (g < g_end + 0.06)
    # pours: construction joints across the section, each pour its own tone
    pours = np.array([0.0, 5.9, 12.2, 17.8, 24.0])
    pid = np.searchsorted(pours, X, side="right") - 1
    ptone = np.array([1.0, 0.955, 1.03, 0.975])[np.clip(pid, 0, 3)]
    dj = np.min(np.abs(X[..., None] - pours[None, None, :]), axis=-1)
    cj = sstep(0.012, 0.004, dj) * in_g
    tone = np.where(in_g, tone * ptone, tone)
    joint = np.maximum(joint, cj)
    h -= 2.5e-3 * cj
    lime += 0.5 * sstep(0.10, 0.0, dj) * sstep(g_web0 - 0.2, g_web0 + 0.5, g) * sstep(g_end, g_bot0, g) * (0.5 + 0.5 * n_str) * in_g
    # formwork plywood: 2.5 x 1.25 m sheets on the soffits and the web
    fu = np.abs(((X + 0.6) % 2.5) - 1.25)
    fv = np.abs(((g - g_cant0) % 1.25) - 0.625)
    fw = (sstep(1.25 - 0.006, 1.25 - 0.002, fu) + sstep(0.625 - 0.006, 0.625 - 0.002, fv)) * (g > g_cant0) * in_g
    fw = np.clip(fw, 0, 1)
    tone *= 1 - 0.10 * fw
    h -= 0.8e-3 * fw
    sheet = (np.floor((X + 0.6) / 2.5) * 7 + np.floor((g - g_cant0) / 1.25)).astype(np.int64)
    tone = np.where((g > g_cant0) & in_g, tone * (0.975 + 0.05 * K.hash01(sheet, 3)), tone)
    # tie holes on the web
    tie = np.zeros_like(X)
    for gy in (g_web0 + 0.35, g_web0 + 1.10):
        tie = np.maximum(tie, sstep(0.022, 0.012, np.hypot(((X + 0.6) % 1.25) - 0.625, g - gy)))
    tone *= 1 - 0.45 * tie
    h -= 4e-3 * tie
    # edge beam: drip nose shadow line, run-off below the cornice plate joints (plates 3 m)
    lipz = (g < g_beam0) & in_g
    tone = np.where(lipz, tone * 0.72, tone)
    cj_plate = [(0.4 + 3.0 * k + 0.3 * float(K.hash01(np.int64(k), 11)), 0.035, 0.5 + 0.5 * float(K.hash01(np.int64(k), 12)),
                 0.35 + 0.4 * float(K.hash01(np.int64(k), 13))) for k in range(8)]
    dirt += _streaks(X, g - g_beam0, cj_plate, n_str) * in_g * (g < g_cant0 + 0.5)
    dirt += 0.18 * sstep(g_cant0 + 0.02, g_beam0, g) * (0.6 + 0.4 * n_mid) * in_g * (g >= g_beam0)      # dusty beam face
    # drain outlets through the cantilever (sączki) with lime / rust tails running to the web
    for k, u0 in enumerate((2.9, 9.1, 14.8, 21.2)):
        gy = g_cant0 + 1.05 + 0.2 * k % 0.5
        du = ((X - u0 + 12) % 24) - 12
        r_ = np.hypot(du, g - gy)
        hole = sstep(0.035, 0.022, r_) * in_g
        tone *= 1 - 0.8 * hole
        h -= 6e-3 * hole
        tail = np.exp(-(du / (0.05 + 0.04 * (g - gy).clip(0))) ** 2) * sstep(0, 0.05, g - gy) * np.clip(1 - (g - gy) / 1.3, 0, 1)
        lime += 0.55 * tail * in_g * (0.6 + 0.4 * n_str)
        rust += 0.35 * np.exp(-(r_ / 0.09) ** 2) * in_g
        dirt += 0.25 * tail * in_g * sstep(0.2, 1.0, n_mid)
    # dust line in the re-entrant corners, soot under the bottom flange (traffic below), darker towards the centre
    dirt += 0.22 * (np.exp(-((g - g_web0) / 0.10) ** 2) + np.exp(-((g - g_bot0) / 0.08) ** 2)) * in_g
    soot = sstep(g_bot0 - 0.3, g_end, g) * (0.45 + 0.35 * sstep(-0.6, 0.8, n_big) + 0.2 * n_mid)
    dirt += 0.30 * np.clip(soot, 0, 1) * in_g

    # ---- cornice band: faded red paint on precast plates
    Cn = L["cornice"]
    cv = v - Cn["v0"]
    in_c = v < G["v0"] - 0.10
    red = np.where(in_c, 1.0, red)
    pj = np.abs(((X - 0.4) % 3.0) - 1.5)
    pjm = sstep(1.5 - 0.010, 1.5 - 0.004, pj) * in_c
    joint = np.maximum(joint, pjm)
    h -= 3e-3 * pjm
    plate = np.floor((X - 0.4) / 3.0).astype(np.int64)
    fade = 0.04 + 0.10 * sstep(0.1, 0.55, cv) + 0.08 * K.hash01(plate, 21) + 0.05 * n_mid      # chalking, sun from above
    grime_c = 0.30 * sstep(0.12, 0.0, cv) * (0.5 + 0.5 * n_str) + 0.5 * _streaks(X, Cn["h"] - cv, [(u0 + 1.5, 0.03, 0.45, 0.5) for u0, *_ in cj_plate], n_str)
    chip = sstep(1.9, 2.6, noise(c, 7, 0.01, 0.12, beta=0.6)) * sstep(0.10, 0.0, np.minimum(cv, Cn["h"] - cv)) * in_c

    # ---- pier band: u = metres below the column head
    P = L["pier"]
    pv = v - P["v0"]
    in_p = (v > P["v0"] - 0.08) & (v < L["wall"]["v0"] - 0.04) & (X < P["u_max"] + 0.3)
    for cen in (P["front_c"], P["back_c"]):
        st = sstep(P["stripe_w"] / 2 + 0.004, P["stripe_w"] / 2 - 0.004, np.abs(pv - cen)) * in_p
        red = np.maximum(red, st)
        edge = np.exp(-((np.abs(pv - cen) - P["stripe_w"] / 2) / 0.012) ** 2) * in_p
        h -= 0.012 * st                                           # the stripe sits in a 12 mm recess
        dirt += 0.35 * edge
    headrun = [(P["v0"] + 0.15 + 0.41 * k, 0.03 + 0.02 * (k % 3), 0.8 + 0.5 * (k % 4), 0.25 + 0.1 * (k % 3)) for k in range(8)]
    for v0_, wd, ln, k_ in headrun:                              # streaks run along u here (down the column)
        dirt += k_ * np.exp(-((v - v0_) / wd) ** 2) * np.clip(1 - X / ln, 0, 1) ** 1.3 * in_p
    dirt += 0.28 * sstep(0.35, 0.0, X) * (0.6 + 0.4 * n_mid) * in_p
    lifts = sstep(0.006, 0.002, np.abs((X % 2.0) - 1.0) - 0.994) * in_p        # pour lifts every 2 m
    tone *= 1 - 0.12 * lifts
    h -= 1.2e-3 * lifts

    # ---- abutment wall band: leaking expansion joint above
    Wb = L["wall"]
    in_w = (v > Wb["v0"] - 0.05) & (X < Wb["u_max"] + 0.3)
    wrun = [(Wb["v0"] + 0.12 + 0.19 * k, 0.025 + 0.03 * ((k * 5) % 3), 1.2 + 0.9 * ((k * 3) % 4), 0.3 + 0.12 * (k % 3)) for k in range(7)]
    for v0_, wd, ln, k_ in wrun:
        s_ = k_ * np.exp(-((v - v0_) / wd) ** 2) * np.clip(1 - X / ln, 0, 1) ** 1.2 * in_w
        dirt += s_
        lime += 0.5 * s_ * sstep(0.0, 0.8, n_mid)
    dirt += 0.35 * sstep(0.5, 0.0, X) * (0.55 + 0.45 * n_mid) * in_w

    # ---- swatches
    sd, sp_ = L["swatch_dark"], L["swatch_plain"]
    m_dark = (X > sd["u"][0] - 0.3) & (X < sd["u"][1] + 0.3) & (v > sd["v"][0] - 0.2) & (v < sd["v"][1] + 0.2)

    # ---- compose
    dirt = np.clip(dirt, 0, 0.85)
    lime = np.clip(lime, 0, 0.6)
    conc = CONCRETE * tone
    conc = conc / float(conc[in_g].mean()) * CONCRETE
    alb = conc[..., None] * chroma[None, None, :]
    dirt_col = np.array([0.060, 0.055, 0.048], np.float32)
    alb = alb * (1 - dirt[..., None]) + dirt_col * dirt[..., None]
    alb = alb * (1 - lime[..., None]) + np.array([0.62, 0.61, 0.58], np.float32) * lime[..., None]
    alb = alb * (1 - rust[..., None]) + np.array([0.20, 0.085, 0.035], np.float32) * rust[..., None]
    paint = np.array(L["paint_red_linear"], np.float32)
    pcol = paint[None, None, :] * (detail * (1 + 0.04 * n_mid))[..., None]
    pcol = pcol + (np.array([0.55, 0.42, 0.42], np.float32) - pcol) * np.where(in_c, fade, 0.12)[..., None]      # chalky pink
    pcol = pcol * (1 - np.where(in_c, grime_c, dirt)[..., None] * 0.8)
    pcol = pcol * (1 - 0.6 * joint[..., None])
    pcol = np.where((chip > 0.5)[..., None], alb, pcol)
    alb = np.where(red[..., None] > 0.5, pcol, alb)
    alb = np.where(m_dark[..., None], np.array([0.035, 0.035, 0.036], np.float32) * (1 + 0.15 * n_fine)[..., None], alb)
    rough = np.where(red > 0.5, 0.72, rough) + 0.05 * dirt
    rough = np.where(m_dark, 0.8, rough)
    alb = np.clip(alb, 0.01, 0.9).astype(np.float32)
    s = K.SurfaceSet("viaduct_concrete", c, alb, h.astype(np.float32), np.clip(rough, 0.3, 1).astype(np.float32),
                     (pid / 4.0).astype(np.float32), np.clip(joint, 0, 1).astype(np.float32), ao_k=0.6)
    s.source = source
    s.concrete_mean = [round(float(x), 4) for x in alb[in_g & (dirt < 0.05) & (lime < 0.05)].mean(0)]
    return s


def railing_texture(path: Path | None = None):
    """viaduct_steel.png 512 x 256 RGBA: left 3/4 = one 2.0 x 1.0 m railing bay (u 0..0.75, v 0..1: bottom rail,
    vertical bars every 0.125 m, mid flat, alpha elsewhere), right 1/4 = opaque weathered galvanised steel."""
    W, H = 512, 256
    rng = np.random.default_rng(672)
    a = np.zeros((H, W), np.float32)
    lum = np.full((H, W), 0.42, np.float32)
    x = (np.arange(W) + 0.5) / W
    y = 1 - (np.arange(H) + 0.5) / H
    Xg, Yg = np.meshgrid(x, y)
    ub = Xg / 0.75 * 2.0                                  # metres along the bay
    bay = Xg < 0.75 - 1.0 / W
    bars = np.abs(((ub + 0.0625) % 0.125) - 0.0625) < 0.0085
    a[bay & bars & (Yg > 0.10) & (Yg < 0.97)] = 1
    a[bay & (np.abs(Yg - 0.10) < 0.022)] = 1              # bottom rail
    a[bay & (np.abs(Yg - 0.955) < 0.02)] = 1              # top flat under the handrail
    a[~bay & (Xg > 0.75 + 2.0 / W)] = 1
    n = rng.standard_normal((H // 8, W // 8)).astype(np.float32)
    n = np.asarray(Image.fromarray(n).resize((W, H), Image.BICUBIC))
    lum = lum * (1 + 0.10 * n) * (1 - 0.25 * (Yg < 0.16) * bay)          # road spray at the foot
    lum = np.clip(lum + 0.02 * rng.standard_normal((H, W)), 0.05, 0.8)
    rgb = np.dstack([lum * 0.98, lum, lum * 1.03])
    img = np.dstack([K.srgb_encode(rgb), a])
    path = path or (REPO / "art-source" / "world" / "textures" / "viaduct_steel.png")
    K.save_png(path, img, "RGBA")
    return path


def write_layout():
    LANDMARK.mkdir(parents=True, exist_ok=True)
    p = LANDMARK / "atlas_layout.json"
    text = json.dumps(LAYOUT, indent=1, sort_keys=True) + "\n"
    if not p.exists() or p.read_text(encoding="utf-8") != text:
        p.write_text(text, encoding="utf-8", newline="\n")
    return p


VIADUCT_SETS = {
    "viaduct_concrete": dict(fn=viaduct_concrete, tile_m=list(TILE), target=CONCRETE,
        uv="mesh_uv0_metres (u along the bridge, v = band position; layout in art-source/world/landmarks/"
           "viaduct_biezenstwa/atlas_layout.json)",
        slots=["viaduct_concrete (hero viaduct asset, ADR 0067)"],
        note="Strip atlas 24 x 12 m (4096 x 2048 High): red cornice band, unrolled box-girder half section, "
             "unrolled column, abutment wall, swatches. Base detail / relief / roughness from the CC0 scan "
             "'Concrete Wall 008' (Poly Haven); pours, formwork, drains, drips, soot, leak streaks generated. "
             "albedo_target_mean_lum_linear applies to the clean concrete of the girder band, not the atlas mean."),
}


if __name__ == "__main__":
    if "--layout" in sys.argv:
        print(write_layout())
    if "--railing" in sys.argv:
        print(railing_texture())
