"""Facade and prop modulation sets (world C): hall cladding, plinths, doors, plaster, large-panel joints, brick,
trailer curtains, container corrugation, box-body panels.

Unlike the ground sets these are NOT calibrated albedo: BaseColor is a neutral modulation map with linear mean
luminance 0.5 (kind "modulation_set"); the engine multiplies it by 2 x the manifest colour of each material
(hall_wall_silver, trailer_curtain_blue, ...), so one set serves every colour variant. UV = mesh TEXCOORD_0 in
metres (u along the wall / body, v up; buildings_mesh.py, life_props.py). Dimensions are WORKING_VALUE typical
Polish products unless stated:
  - trapezoidal sheet T35-ish: 0.25 m pitch, 35 mm rib (manufacturers' T35 sheets have ~207-250 mm pitch);
  - sandwich panel walls laid horizontally, 1.0 m modules, micro-lined face, shadow-gap joints;
  - sectional door: 0.5 m sections with a mid-panel M-rib;
  - wielka płyta: 3.0 x 2.8 m panels with sealed joints (docs/WORLD_GENERATION.md, facade_kit.py);
  - brick 250 x 65 mm, 10 mm joints (PN-EN 771-1 format NF);
  - curtainsider tarpaulin: irregular vertical folds 0.25-0.6 m, sag between straps;
  - ISO container side: trapezoidal corrugation, 0.278 m pitch (WORKING_VALUE from photos, not a standard).
"""
from __future__ import annotations

import numpy as np

from pbrkit import Ctx, SurfaceSet, noise, voronoi, edge_dist, sstep, hash01, blur, calibrate, LUM

MOD_MEAN = 0.5


def _finish(name, c, lum, h, rough, eid, joint, tint=(1.0, 1.0, 1.0), ao_k=0.6, metal=None, extra=None):
    alb = np.clip(lum, 0, None)[..., None] * np.array(tint, np.float32)
    if extra is not None:
        alb = extra(alb)
    alb, _ = calibrate(alb.astype(np.float32), MOD_MEAN)
    return SurfaceSet(name, c, alb.astype(np.float32), h.astype(np.float32), np.clip(rough, 0.05, 1).astype(np.float32),
                      eid.astype(np.float32), np.clip(joint, 0, 1).astype(np.float32), metal=metal, ao_k=ao_k)


def _streaks(c, k, amount):
    """Vertical rain / dirt streaks (run-off): noise stretched along v, darker, broken into runs."""
    s = noise(c, k, 0.05, 1.5, beta=0.9, aniso=1.0 / 6.0)    # aniso < 1 stretches features along v (vertical)
    runs = sstep(0.4, 1.8, s)
    return 1 - amount * runs


def sandwich_ribbed(n=2048):
    """Horizontal sandwich panels 1.0 m, micro-lined face (ribs every 0.1 m), shadow-gap joints. Tile 6 x 6 m."""
    L = 6.0
    c = Ctx(n, n, L, L, seed=501)
    X, Y = c.xy()
    v = (L - Y)                                              # metres up (row 0 = top)
    pv = v % 1.0
    pid = np.floor(v / 1.0).astype(int)
    dj = np.minimum(pv, 1.0 - pv)
    joint = sstep(0.009, 0.004, dj)
    rib = 0.5 + 0.5 * np.cos(2 * np.pi * (v / 0.1))
    h = -0.6e-3 * rib - 6e-3 * joint
    pan = hash01(pid, 7)
    lum = (1.0 + 0.035 * (pan - 0.5) - 0.06 * rib + 0.02 * noise(c, 3, 0.2, 3.0)) * (1 - 0.55 * joint)
    lum *= _streaks(c, 4, 0.10)
    lum *= 1 - 0.06 * sstep(0.5, 2.0, noise(c, 5, 0.3, 4.0, beta=1.2))
    rough = 0.48 + 0.10 * sstep(0.5, 2.0, noise(c, 6, 0.2, 2.0)) + 0.15 * joint
    return _finish("sandwich_ribbed", c, lum, h, rough, pan, joint)


def trapezoid_sheet(n=1024):
    """Trapezoidal sheet, vertical ribs 0.25 m pitch, 35 mm deep. Tile 2 x 2 m."""
    L = 2.0
    c = Ctx(n, n, L, L, seed=502)
    X, Y = c.xy()
    p = 0.25
    u = X % p
    # profile: crest 0.06 m, webs 0.035 m, trough 0.12 m (WORKING_VALUE)
    crest, web = 0.06, 0.035
    t0 = (p - crest - 2 * web)
    hprof = np.where(u < t0, 0.0,
             np.where(u < t0 + web, (u - t0) / web,
             np.where(u < t0 + web + crest, 1.0, 1.0 - (u - t0 - web - crest) / web)))
    h = 0.035 * hprof
    shade = np.where((u >= t0) & (u < t0 + web), 0.92, np.where(u >= t0 + web + crest, 1.04, 1.0))
    lum = shade * (1 + 0.02 * noise(c, 3, 0.1, 1.0))
    lum *= _streaks(c, 4, 0.08)
    trough = (hprof < 0.05).astype(np.float32)
    lum *= 1 - 0.05 * trough * sstep(0.0, 1.5, noise(c, 5, 0.2, 1.0))
    rough = 0.45 + 0.08 * trough + 0.05 * noise(c, 6, 0.1, 1.0)
    return _finish("trapezoid_sheet", c, lum, h, rough, np.floor(X / p) / 8.0, trough * 0.3, ao_k=0.15)


def concrete_precast(n=2048):
    """Precast plinth / wall panels: 6 m bays (joint at u = 0), formwork ties, pores, soiled bottom. Tile 6 x 3 m."""
    Lx, Ly = 6.0, 3.0
    c = Ctx(n, n // 2, Lx, Ly, seed=503)
    X, Y = c.xy()
    v = Ly - Y
    du = np.minimum(X, Lx - X)
    joint = sstep(0.012, 0.006, du)
    sand = noise(c, 1, c.px * 2, 0.006, beta=0.5)
    mid = noise(c, 2, 0.03, 0.8, beta=1.0)
    pores_n = noise(c, 3, c.px * 1.5, 0.004, beta=0.2)
    thr = np.quantile(pores_n, 0.996)
    pores = sstep(thr, thr + 0.6, pores_n)
    ties = np.zeros_like(X)
    for tx in (0.75, 2.25, 3.75, 5.25):
        for ty in (0.5, 1.5, 2.5):
            ties = np.maximum(ties, sstep(0.014, 0.008, np.hypot(X - tx, v - ty)))
    lum = (1 + 0.05 * sand + 0.06 * mid - 0.4 * pores) * (1 - 0.5 * joint) * (1 - 0.25 * ties)
    lum *= _streaks(c, 4, 0.12)
    h = 0.1e-3 * sand + 0.3e-3 * mid - 1.2e-3 * pores - 8e-3 * joint - 3e-3 * ties
    rough = 0.85 + 0.05 * noise(c, 6, 0.1, 1.0)
    return _finish("concrete_precast", c, lum, h, rough, np.floor(X / Lx), joint, tint=(1.0, 0.99, 0.965))


def sectional_door(n=1024):
    """Sectional door leaves 0.5 m high with a mid-panel M-rib and stucco grain. Tile 3 x 3 m."""
    L = 3.0
    c = Ctx(n, n, L, L, seed=504)
    X, Y = c.xy()
    v = L - Y
    pv = v % 0.5
    dj = np.minimum(pv, 0.5 - pv)
    joint = sstep(0.008, 0.003, dj)
    mrib = sstep(0.012, 0.004, np.abs(pv - 0.25))
    stucco = noise(c, 1, c.px * 2, 0.01, beta=0.4)
    h = -5e-3 * joint - 1.5e-3 * mrib + 0.15e-3 * stucco
    lum = (1 + 0.03 * stucco + 0.02 * noise(c, 2, 0.2, 2.0)) * (1 - 0.5 * joint) * (1 - 0.08 * mrib)
    lum *= _streaks(c, 3, 0.06)
    lum *= 1 - 0.18 * sstep(0.6, 0.0, v) * (0.6 + 0.4 * sstep(-1, 1, noise(c, 4, 0.05, 0.5)))  # scuffed bottom
    rough = 0.42 + 0.1 * joint
    return _finish("sectional_door", c, lum, h, rough, np.floor(v / 0.5) / 6.0, joint, ao_k=0.4)


def plaster(n=1024):
    """Thin-coat silicate / mineral plaster (grain 1.5 mm) with trowel clouds and streaks. Tile 2 x 2 m."""
    L = 2.0
    c = Ctx(n, n, L, L, seed=505)
    grain = noise(c, 1, c.px * 2, 0.004, beta=0.3)
    cloud = noise(c, 2, 0.1, 1.5, beta=1.2)
    h = 0.4e-3 * grain + 0.3e-3 * cloud
    lum = (1 + 0.05 * grain + 0.04 * cloud) * _streaks(c, 3, 0.07)
    rough = 0.9 + 0.03 * grain
    return _finish("plaster", c, lum, h, rough, np.zeros_like(grain), np.zeros_like(grain), ao_k=0.8)


def large_panel_joints(n=2048):
    """Wielka płyta: 3.0 x 2.8 m panels, 20 mm sealed joints, panel tone variation, exposed-aggregate grain.
    Tile 6 x 5.6 m."""
    Lx, Ly = 6.0, 5.6
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=506)
    X, Y = c.xy()
    v = Ly - Y
    du = np.minimum(X % 3.0, 3.0 - X % 3.0)
    dv = np.minimum(v % 2.8, 2.8 - v % 2.8)
    dj = np.minimum(du, dv)
    joint = sstep(0.012, 0.007, dj)
    pid = np.floor(X / 3.0).astype(int) * 5 + np.floor(v / 2.8).astype(int)
    tone = hash01(pid, 3)
    grain = noise(c, 1, c.px * 2, 0.008, beta=0.4)
    lum = (1 + 0.07 * (tone - 0.5) + 0.05 * grain + 0.04 * noise(c, 2, 0.2, 2.5)) * (1 - 0.55 * joint)
    lum *= _streaks(c, 3, 0.12)
    # sealant runs darker below horizontal joints (water)
    lum *= 1 - 0.08 * sstep(0.25, 0.0, (v % 2.8)) * sstep(-0.5, 1.0, noise(c, 4, 0.2, 1.0))
    h = -6e-3 * joint + 0.3e-3 * grain
    rough = 0.88 + 0.04 * grain
    return _finish("large_panel_joints", c, lum, h, rough, tone, joint)


def brick(n=1024):
    """Brick NF 250 x 65 mm, 10 mm recessed mortar joints, stretcher bond; per-brick tone. Tile 1.04 x 1.2 m."""
    Lx, Ly = 1.04, 1.2
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=507)
    X, Y = c.xy()
    v = Ly - Y
    course = 0.075
    row = np.floor(v / course).astype(int)
    xs = (X + (row % 2) * 0.13) % Lx
    col = np.floor(xs / 0.26).astype(int)
    du = np.minimum(xs % 0.26, 0.26 - xs % 0.26)
    dv = np.minimum(v % course, course - v % course)
    mort = sstep(0.0065, 0.004, np.minimum(du, dv))
    bid = row * 7 + col
    t = hash01(bid, 1)
    grain = noise(c, 1, c.px * 2, 0.006, beta=0.4)
    lum = (1 + 0.22 * (t - 0.5) + 0.06 * grain) * (1 - mort) + mort * 1.55
    h = -4e-3 * mort + 0.25e-3 * grain
    rough = 0.85 + 0.08 * mort
    def col_var(alb):
        burn = hash01(bid, 2)[..., None]
        return alb * (1 + np.array([0.06, -0.02, -0.05], np.float32) * (burn - 0.5) * 2) * (1 - mort[..., None]) + \
            alb * mort[..., None] * np.array([0.9, 0.95, 1.0], np.float32)
    return _finish("brick", c, lum, h, rough, t, mort, extra=col_var)


def curtain_folds(n=2048):
    """Curtainsider tarpaulin: irregular vertical folds, sag between buckle straps (every ~1.2 m along u),
    road grime on the lower third. Tile 4.8 x 2.7 m (u along the trailer, v up)."""
    Lx, Ly = 4.8, 2.7
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=508)
    X, Y = c.xy()
    v = Ly - Y
    # folds: sum of sines with wavering phase (periodic in u: integer cycles over Lx)
    ph = noise(c, 1, 0.8, 4.0, beta=1.2, aniso=0.3) * 0.18
    f = (0.55 * np.sin(2 * np.pi * (X / Lx * 13 + ph)) + 0.30 * np.sin(2 * np.pi * (X / Lx * 7 - ph * 0.7)) +
         0.15 * np.sin(2 * np.pi * (X / Lx * 23 + ph * 1.3)))
    sag_amp = sstep(0.0, 1.0, np.sin(np.pi * v / Ly))                # tarp tensioned at rails, loose mid-height
    strap = np.minimum(X % 1.2, 1.2 - X % 1.2)
    near = sstep(0.25, 0.0, strap)
    h = 0.012 * f * sag_amp * (1 - 0.7 * near) + 0.0006 * noise(c, 2, 0.05, 0.4)
    lum = 1 + 0.10 * f * sag_amp + 0.03 * noise(c, 3, 0.1, 1.5)
    grime = sstep(1.1, 0.0, v) * (0.6 + 0.4 * sstep(-1, 1, noise(c, 4, 0.1, 1.0)))
    lum *= 1 - 0.22 * grime
    lum *= _streaks(c, 5, 0.06)
    rough = 0.62 + 0.1 * grime
    return _finish("curtain_folds", c, lum, h, rough, np.zeros_like(X), grime * 0.5, ao_k=0.35)


def container_corrugation(n=1024):
    """ISO container side: trapezoidal corrugation (0.278 m pitch), dents and rust spots. Tile 2.78 x 2.6 m."""
    Lx, Ly = 2.78, 2.6
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=509)
    X, Y = c.xy()
    v = Ly - Y
    p = 0.278
    u = X % p
    prof = np.clip(np.abs((u / p) * 2 - 1) * 1.6 - 0.3, 0, 1)
    dent = sstep(1.6, 2.4, noise(c, 1, 0.2, 1.0))
    h = 0.036 * prof - 0.006 * dent
    lum = (1 + 0.05 * (prof - 0.5) + 0.03 * noise(c, 2, 0.1, 1.5)) * _streaks(c, 3, 0.10)
    rust = sstep(1.4, 2.2, noise(c, 4, 0.02, 0.4, beta=0.7)) * (0.4 + 0.6 * sstep(1.0, 0.0, v))
    def tint(alb):
        rc = np.array([0.55, 0.30, 0.18], np.float32)
        return alb * (1 - rust[..., None] * 0.7) + rust[..., None] * rc * alb.mean()
    rough = 0.6 + 0.2 * rust
    return _finish("container_corrugation", c, lum, h, rough, np.floor(X / p) / 10.0, rust, extra=tint, ao_k=0.2)


def box_panel(n=1024):
    """Box / reefer body: GRP-skinned panels with vertical seam profiles every 1.2 m, road film on the lower
    part. Tile 4.8 x 2.7 m."""
    Lx, Ly = 4.8, 2.7
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=510)
    X, Y = c.xy()
    v = Ly - Y
    du = np.minimum(X % 1.2, 1.2 - X % 1.2)
    seam = sstep(0.012, 0.004, du)
    h = 1.5e-3 * seam + 0.1e-3 * noise(c, 1, 0.01, 0.2)
    lum = (1 + 0.02 * noise(c, 2, 0.2, 2.0)) * (1 - 0.15 * seam) * _streaks(c, 3, 0.09)
    lum *= 1 - 0.18 * sstep(0.9, 0.0, v)
    rough = 0.4 + 0.1 * sstep(0.9, 0.0, v)
    return _finish("box_panel", c, lum, h, rough, np.zeros_like(X), seam, ao_k=0.3)


def noise_cassette(n=1024):
    """Absorbing noise-barrier cassettes (ekran akustyczny, aluminium/steel kasety): 4.0 m bays between HEB posts
    (vertical gap at u = 0, the post covers it), horizontal elements 0.5 m high with a lip joint, perforated road
    face (round holes 10 mm on a staggered 25 mm grid, relief only: normal map / AO, never albedo, and low-passed per
    tier so Medium / Low carry no aliased dimples - review r6 W-N2), per-cassette tone (fading, replaced
    elements), road-spray grime on the lowest 0.4-0.7 m and run-off streaks below every joint. v = metres above
    the top of the 0.5 m concrete plinth (furniture.noise_barriers UV). Element size WORKING_VALUE (typical Polish
    products: 3.96-4.96 x 0.5 m; BDOT10k OT_OIKM_L carries no type). Tile 4 x 4 m."""
    L = 4.0
    c = Ctx(n, n, L, L, seed=512)
    X, Y = c.xy()
    v = L - Y
    pv = v % 0.5
    row = np.floor(v / 0.5).astype(int)
    dj = np.minimum(pv, 0.5 - pv)
    joint = sstep(0.010, 0.004, dj)
    lip = sstep(0.03, 0.012, np.abs(pv - 0.035)) * (1 - joint)          # pressed lip just above each joint
    du = np.minimum(X, L - X)
    gap = sstep(0.02, 0.008, du)                                          # bay end (behind the post flange)
    # perforation: holes d = 10 mm (8-12 mm class) on a 25 mm staggered grid (rows offset by half a pitch)
    P_ = 0.025
    prow = np.floor(v / P_)
    hu = (X + 0.5 * P_ * (prow % 2)) % P_ - 0.5 * P_
    hv = v % P_ - 0.5 * P_
    slots = sstep(0.0058, 0.0042, np.hypot(hu, hv)) * (1 - joint)
    tone = hash01(row, 11)
    tone = 0.08 * (tone - 0.5) + 0.08 * (tone > 0.9)                       # ~10 % visibly newer elements
    lum = (1.0 + tone + 0.025 * noise(c, 2, 0.1, 2.0)) * (1 - 0.5 * joint) * (1 + 0.06 * lip) * (1 - 0.6 * gap)
    # run-off: streaks start at every joint and fade downward within the element, plus long streaks from the cap
    s = noise(c, 3, 0.04, 1.2, beta=0.9, aniso=1.0 / 8.0)
    under = sstep(0.0, 0.25, 0.5 - pv)                                    # strongest right under a joint
    lum *= 1 - 0.10 * sstep(0.5, 1.8, s) * under
    lum *= _streaks(c, 4, 0.08)
    # road spray on the lowest part: a soft gradient (strongest at the plinth, gone by ~0.9 m), broken up by fine
    # droplet noise and stretched spray fans; no hard blobs (r5 W-N3: one-scale stains read as a pattern)
    fan = noise(c, 5, 0.08, 1.0, beta=1.0, aniso=3.0)
    top = 0.75 + 0.15 * fan
    splash = sstep(top, 0.0, v) ** 1.5
    drops = sstep(-0.5, 1.5, noise(c, 6, c.px * 2, 0.03, beta=0.3))
    splash = np.clip(splash * (0.75 + 0.25 * drops), 0, 1)
    lum *= 1 - 0.32 * splash
    lum *= 1 - 0.05 * sstep(0.5, 2.0, noise(c, 7, 0.3, 3.0, beta=1.2))     # cloudy weathering
    h = -6e-3 * joint + 1.2e-3 * lip - 0.6e-3 * slots - 8e-3 * gap
    rough = 0.55 + 0.12 * splash + 0.1 * joint + 0.05 * noise(c, 8, 0.1, 1.0)

    def grime(a):
        brown = np.array([1.0, 0.93, 0.80], np.float32)                   # road dust is warm grey-brown
        k = np.clip(splash, 0, 1)[..., None]
        return a * (1 - k) + a * brown * k
    st = _finish("noise_cassette", c, lum, h, rough, tone + 0.5, np.maximum(joint, gap), extra=grime, ao_k=0.5)
    st.aa_tiers = True
    return st


def car_grime(n=1024):
    """Parked-car paint film: road spray on the sills and bumpers (v < 0.55 m, warm grey-brown, strongest at the
    bottom edge), dust film and pollen on horizontal-ish upper surfaces, rain runs below the belt line and the roof
    edge, faint orange peel. u = metres along the body, v = metres above the ground (life_props car/van UV).
    Polish cars outside a car wash cycle: WORKING_VALUE look, no measured data. Tile 5 x 2.5 m."""
    Lx, Ly = 5.0, 2.5
    c = Ctx(n, n // 2, Lx, Ly, seed=513)
    X, Y = c.xy()
    v = Ly - Y
    fan = noise(c, 1, 0.1, 1.2, beta=1.0, aniso=4.0)
    film = sstep(0.62 + 0.1 * fan, 0.15, v) ** 1.3
    drops = sstep(-0.6, 1.6, noise(c, 2, c.px * 2, 0.02, beta=0.3))
    film = np.clip(film * (0.7 + 0.3 * drops), 0, 1)
    runs = sstep(0.6, 1.8, noise(c, 3, 0.02, 0.6, beta=0.9, aniso=1.0 / 10.0))
    belt = sstep(1.0, 0.75, v) * sstep(0.35, 0.6, v)
    peel = noise(c, 4, c.px * 2, 0.01, beta=0.4)
    dust = sstep(1.1, 1.5, v) * (0.5 + 0.5 * sstep(-1, 1, noise(c, 5, 0.05, 0.8)))
    lum = (1 + 0.01 * peel) * (1 - 0.30 * film) * (1 - 0.07 * runs * belt) * (1 + 0.05 * dust)
    h = 0.03e-3 * peel
    rough = 0.32 + 0.35 * film + 0.15 * dust

    def tint(a):
        k = np.clip(film, 0, 1)[..., None]
        kd = np.clip(dust, 0, 1)[..., None] * 0.5
        a = a * (1 - k) + a * np.array([1.0, 0.92, 0.78], np.float32) * k
        return a * (1 - kd) + a * np.array([1.0, 0.97, 0.90], np.float32) * kd
    return _finish("car_grime", c, lum, h, rough, np.zeros_like(X), np.zeros_like(X), extra=tint, ao_k=0.2)


def concrete_fence_panel(n=1024):
    """Prefabricated concrete panel fence (plot walls, OSM barrier=wall): 2.0 m bays between posts (u = 0, 2 under the
    post), 0.5 m panels stacked 4 high with a shallow V joint, cast face with fine pores and sparse air holes, per-panel
    tone (different casts), road spray on the lowest ~0.6 m and run-off below every joint. Smooth plain panels (no stone
    relief: not visible on any reference). v = metres above the slab base (0.2 m below ground). Tile 4 x 2 m.
    Review r6 W-N2: the set was referenced but missing, the fallback detail map shimmered into large dimples on Low."""
    Lx, Ly = 4.0, 2.0
    c = Ctx(n, n // 2, Lx, Ly, seed=533)
    X, Y = c.xy()
    v = Ly - Y
    pv = v % 0.5
    row = np.floor(v / 0.5).astype(int)
    bay = np.floor(X / 2.0).astype(int)
    dj = np.minimum(pv, 0.5 - pv)
    joint = sstep(0.012, 0.004, dj)
    du = np.minimum(X % 2.0, 2.0 - X % 2.0)
    gap = sstep(0.03, 0.012, du)
    tone = hash01(row * 7 + bay, 13)
    pores = noise(c, 1, 0.004, 0.03, beta=0.5)
    holes = sstep(2.2, 3.2, -noise(c, 2, 0.004, 0.012, beta=0.2))
    lum = (1.0 + 0.07 * (tone - 0.5) + 0.02 * pores) * (1 - 0.35 * joint) * (1 - 0.5 * gap) * (1 - 0.25 * holes)
    s = noise(c, 3, 0.04, 1.0, beta=0.9, aniso=1.0 / 8.0)
    under = sstep(0.0, 0.3, 0.5 - pv)
    lum *= 1 - 0.08 * sstep(0.5, 1.8, s) * under
    lum *= _streaks(c, 4, 0.06)
    fan = noise(c, 5, 0.08, 1.0, beta=1.0, aniso=3.0)
    splash = sstep(0.8 + 0.15 * fan, 0.2, v) ** 1.5
    lum *= 1 - 0.25 * splash
    lum *= 1 - 0.05 * sstep(0.5, 2.0, noise(c, 7, 0.3, 3.0, beta=1.2))
    h = -4e-3 * joint - 6e-3 * gap - 0.6e-3 * holes + 0.15e-3 * pores
    rough = 0.85 + 0.08 * splash

    def grime(a):
        k = np.clip(splash, 0, 1)[..., None]
        return a * (1 - k) + a * np.array([1.0, 0.94, 0.82], np.float32) * k
    st = _finish("concrete_fence_panel", c, lum, h, rough, tone, np.maximum(joint, gap), extra=grime, ao_k=0.5)
    st.aa_tiers = True
    return st


def hedge_foliage(n=512):
    """Clipped hedge face (Berberis thunbergii 'Atropurpurea' type, the red roundabout hedges of the CC0 Bieżeństwa
    photo): leaf clusters 15-60 mm on a 1-3 cm leaf scale, dark gaps between them, sparse lighter tips on the cut
    surface, a few deeper holes where the hedge is thin. Modulation map (mean 0.5) tinted by the manifest colour.
    u = metres along the hedge, v = metres over the cross-section (streetscape.plantings). Tile 1.5 x 1.5 m.
    WORKING_VALUE look (no measured scan)."""
    L = 1.5
    c = Ctx(n, n, L, L, seed=531)
    leaves = noise(c, 1, 0.012, 0.06, beta=0.6)
    clumps = noise(c, 2, 0.08, 0.35, beta=1.0)
    holes = sstep(1.3, 2.4, -noise(c, 3, 0.15, 0.6, beta=1.0))
    gaps = sstep(0.2, -0.9, leaves + 0.6 * clumps)                      # shadowed voids between clusters
    tips = sstep(1.0, 2.2, leaves) * sstep(-0.2, 0.8, clumps)
    lum = (1.0 + 0.10 * clumps + 0.10 * tips) * (1 - 0.55 * gaps) * (1 - 0.6 * holes)
    h = 0.02 * (0.5 * leaves + clumps) - 0.05 * holes
    rough = 0.75 + 0.15 * gaps
    def tint(a):                                                         # tips greener-brown, voids neutral
        k = np.clip(tips, 0, 1)[..., None] * 0.35
        return a * (1 - k) + a * np.array([0.85, 1.25, 0.9], np.float32) * k
    return _finish("hedge_foliage", c, lum, h, rough, np.zeros_like(lum), np.clip(gaps + holes, 0, 1), extra=tint,
                   ao_k=1.0)


def soil_bed(n=512):
    """Planting bed on a traffic island: dark loam with pine-bark mulch chips (20-60 mm), a few pale stones, leaf
    litter in patches. Modulation map tinted by the manifest colour (bed_soil). u, v = plan metres. Tile 2 x 2 m.
    WORKING_VALUE look."""
    L = 2.0
    c = Ctx(n, n, L, L, seed=532)
    d1, d2, i1, _, nsites = voronoi(c, 1, 0.035, 1.0)
    chip = hash01(i1, 5)
    crack = sstep(0.006, 0.0015, d2 - d1)
    clods = noise(c, 2, 0.05, 0.4, beta=1.0)
    stones = (hash01(i1, 7) > 0.992).astype(np.float32) * sstep(0.004, 0.012, d2 - d1)
    litter = sstep(0.6, 1.6, noise(c, 3, 0.1, 0.8, beta=1.0))
    lum = (0.9 + 0.18 * chip * sstep(-1.0, 1.0, clods) + 0.15 * clods) * (1 - 0.18 * crack) * (1 + 0.35 * stones) * (1 + 0.2 * litter)
    h = 0.006 * chip + 0.01 * clods - 0.006 * crack
    rough = 0.85 + 0.1 * crack
    def tint(a):
        k = np.clip(stones, 0, 1)[..., None]
        a = a * (1 - k) + a * np.array([1.0, 1.1, 1.2], np.float32) * k
        kl = np.clip(litter, 0, 1)[..., None] * 0.5
        return a * (1 - kl) + a * np.array([1.1, 0.95, 0.7], np.float32) * kl
    return _finish("soil_bed", c, lum, h, rough, chip, crack, extra=tint, ao_k=0.8)


FACADE_SETS = {
    "sandwich_ribbed": dict(fn=sandwich_ribbed, tile_m=[6.0, 6.0],
        slots=["hall_wall_grey", "hall_wall_silver", "hall_wall_white", "hall_wall_ivory", "booth_panel"],
        note="Horizontal sandwich panels 1.0 m, micro-lined face, shadow-gap joints, run-off streaks."),
    "trapezoid_sheet": dict(fn=trapezoid_sheet, tile_m=[2.0, 2.0],
        slots=["hall_wall_graphite", "hall_wall_accent_*", "balcony_panel"],
        note="Trapezoidal sheet, vertical ribs 0.25 m pitch, 35 mm deep (T35-like, WORKING_VALUE)."),
    "concrete_precast": dict(fn=concrete_precast, tile_m=[6.0, 3.0], slots=["hall_plinth"],
        note="Precast plinth panels, 6 m bays, formwork ties, pores, run-off."),
    "sectional_door": dict(fn=sectional_door, tile_m=[3.0, 3.0], slots=["dock_door", "garage_door"],
        note="Sectional door leaves 0.5 m with a mid-panel rib, stucco grain, scuffed bottom."),
    "plaster": dict(fn=plaster, tile_m=[2.0, 2.0], slots=["plaster_*"],
        note="Thin-coat plaster grain with trowel clouds and streaks."),
    "large_panel_joints": dict(fn=large_panel_joints, tile_m=[6.0, 5.6], slots=["panel_concrete"],
        note="Large-panel block: 3.0 x 2.8 m panels, sealed joints, per-panel tone."),
    "brick": dict(fn=brick, tile_m=[1.04, 1.2], slots=["brick_red", "chimney_brick"],
        note="Brick NF 250 x 65 mm, 10 mm mortar, stretcher bond, per-brick tone."),
    "curtain_folds": dict(fn=curtain_folds, tile_m=[4.8, 2.7], slots=["trailer_curtain_*"],
        note="Curtainsider tarpaulin folds, sag between straps, grime on the lower third."),
    "container_corrugation": dict(fn=container_corrugation, tile_m=[2.78, 2.6], slots=["container_*"],
        note="Container side corrugation 0.278 m pitch, dents, rust spots."),
    "noise_cassette": dict(fn=noise_cassette, tile_m=[4.0, 4.0], slots=["noise_panel"],
        note="Absorbing noise-barrier cassettes 4.0 x 0.5 m, perforated face, joint lips, splash grime, run-off."),
    "concrete_fence_panel": dict(fn=concrete_fence_panel, tile_m=[4.0, 2.0], slots=["concrete_fence"],
        note="Prefab concrete panel fence: 2 m bays, 0.5 m panels, pores, joints, splash grime, run-off."),
    "hedge_foliage": dict(fn=hedge_foliage, tile_m=[1.5, 1.5], slots=["hedge_berberis"],
        note="Clipped red berberis hedge face: leaf clusters, dark voids, thin holes (u along, v over the section)."),
    "soil_bed": dict(fn=soil_bed, tile_m=[2.0, 2.0], slots=["bed_soil"],
        note="Island planting bed: loam with bark mulch chips, a few stones, leaf litter (u, v plan metres)."),
    "car_grime": dict(fn=car_grime, tile_m=[5.0, 2.5], slots=["car_paint_*"],
        note="Parked-car paint film: road spray on sills, dust on top, rain runs (u along body, v = height)."),
    "box_panel": dict(fn=box_panel, tile_m=[4.8, 2.7], slots=["trailer_box_white"],
        note="Box body panels with seam profiles every 1.2 m, road film low down."),
}
