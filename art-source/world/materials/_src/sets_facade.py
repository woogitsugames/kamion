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
import sets_roof as RS

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


def sandwich_smooth(n=1024):
    """ADR 0185: flat-faced sandwich panels laid horizontally, courses of 1.15 m (cover width of the common wall
    panel; CC0 photo P11-094: 16 courses on the 18.4 m wall), fine micro-lining, shadow-gap joints. No baked run-off
    streaks (the parapet_runoff layer draws them per building) and no butt joints (material `panel_m`: they are
    physical, every 6 m). Tile 3.45 x 3.45 m = three courses."""
    L = 3.45
    c = Ctx(n, n, L, L, seed=541)
    X, Y = c.xy()
    v = (L - Y)
    pv = v % 1.15
    pid = np.floor(v / 1.15 + 1e-6).astype(int)
    dj = np.minimum(pv, 1.15 - pv)
    joint = sstep(0.010, 0.004, dj)
    rib = 0.5 + 0.5 * np.cos(2 * np.pi * (v / 0.05))                # micro-lining 50 mm, 0.3 mm deep
    h = -0.3e-3 * rib - 6e-3 * joint
    pan = hash01(pid, 11)
    lum = (1.0 + 0.02 * (pan - 0.5) - 0.015 * rib + 0.012 * noise(c, 3, 0.4, 3.0)) * (1 - 0.5 * joint)
    rough = 0.44 + 0.06 * sstep(0.5, 2.0, noise(c, 6, 0.3, 2.0)) + 0.15 * joint
    return _finish("sandwich_smooth", c, lum, h, rough, pan, joint)


def cladding_vertical(n=1024):
    """ADR 0185: flat-faced wall panels laid vertically, 1.0 m cover width, shadow-gap joints (CC0 photo P11-001, the
    office block at Kuronia 3). No baked streaks. Tile 3 x 3 m = three panels."""
    L = 3.0
    c = Ctx(n, n, L, L, seed=542)
    X, Y = c.xy()
    pu = X % 1.0
    pid = np.floor(X / 1.0 + 1e-6).astype(int)
    dj = np.minimum(pu, 1.0 - pu)
    joint = sstep(0.010, 0.004, dj)
    rib = 0.5 + 0.5 * np.cos(2 * np.pi * (X / 0.05))
    h = -0.3e-3 * rib - 6e-3 * joint
    pan = hash01(pid, 13)
    lum = (1.0 + 0.025 * (pan - 0.5) - 0.015 * rib + 0.012 * noise(c, 3, 0.4, 3.0)) * (1 - 0.5 * joint)
    rough = 0.44 + 0.06 * sstep(0.5, 2.0, noise(c, 6, 0.3, 2.0)) + 0.15 * joint
    return _finish("cladding_vertical", c, lum, h, rough, pan, joint)


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


def concrete_blocks_split(n=1024):
    """ADR 0159: split-face concrete blocks of the ramp retaining walls (Mapillary 810525063224609 / 209622370971977,
    reference only): courses 0.5 m, blocks 1.0 m, half-bond, dark recessed joints ~25 mm, rough broken face with a
    per-block tone. Block size read off the photos against the 3.0 m screen (WORKING_VALUE +-0.1 m). Tile 2 x 1 m."""
    Lx, Ly = 2.0, 1.0
    c = Ctx(n, n // 2, Lx, Ly, seed=1590)
    X, Y = c.xy()
    v = Ly - Y
    course, blk = 0.5, 1.0
    row = np.floor(v / course).astype(int)
    xs = (X + (row % 2) * blk / 2) % Lx
    col = np.floor(xs / blk).astype(int)
    du = np.minimum(xs % blk, blk - xs % blk)
    dv = np.minimum(v % course, course - v % course)
    d = np.minimum(du, dv)
    joint = sstep(0.022, 0.008, d)                          # 1 in the joint
    bevel = sstep(0.07, 0.02, d) * (1 - joint)              # the broken face rolls into the joint
    bid = row * 5 + col
    t = hash01(bid, 1)
    rock = noise(c, 3, 0.05, 0.25, beta=1.1)                 # split face: lumps of 5-15 cm
    grain = noise(c, 4, c.px * 2, 0.02, beta=0.4)
    lum = (1 + 0.20 * (t - 0.5) + 0.10 * rock + 0.05 * grain) * (1 - 0.18 * bevel) * (1 - joint) + joint * 0.42
    h = (9e-3 * rock + 0.6e-3 * grain) * (1 - joint) - 14e-3 * joint - 5e-3 * bevel
    rough = 0.90 + 0.05 * joint
    return _finish("concrete_blocks_split", c, lum, h, rough, t, joint, ao_k=0.9)


def concrete_panels_wall(n=1024):
    """ADR 0159 after4: precast facing panels of a reinforced-earth retaining wall (ramps of the Biezenstwa viaduct;
    Mapillary 751431972202262 / 1259231227807789, reference only): smooth light concrete panels in vertical columns,
    every second column shifted by half a panel, so the horizontal joints step from column to column; open joints
    ~20 mm, per-panel tone, faint run-off. Panel 1.5 x 1.5 m read off the photo against the 0.75 m W-beam and the
    1.1 m railing (WORKING_VALUE +-0.2 m; the real panels are cruciform - the stepped joints are what reads from
    the road). Tile 3 x 3 m."""
    L = 3.0
    c = Ctx(n, n, L, L, seed=1594)
    X, Y = c.xy()
    v = L - Y
    pw = ph = 1.5
    col = np.floor(X / pw).astype(int)
    vs = (v + (col % 2) * ph / 2) % L
    row = np.floor(vs / ph).astype(int)
    du = np.minimum(X % pw, pw - X % pw)
    dv = np.minimum(vs % ph, ph - vs % ph)
    d = np.minimum(du, dv)
    joint = sstep(0.014, 0.006, d)                          # 1 in the joint
    arris = sstep(0.035, 0.014, d) * (1 - joint)            # chamfered panel edge
    tone = hash01(col * 7 + row, 2)
    grain = noise(c, 1, c.px * 2, 0.01, beta=0.4)
    cloud = noise(c, 2, 0.3, 2.0)
    lum = (1 + 0.06 * (tone - 0.5) + 0.03 * grain + 0.035 * cloud) * (1 - 0.10 * arris) * (1 - joint) + joint * 0.38
    lum *= _streaks(c, 3, 0.07)
    h = -8e-3 * joint - 2e-3 * arris + 0.2e-3 * grain
    rough = 0.82 + 0.04 * grain + 0.08 * joint
    return _finish("concrete_panels_wall", c, lum, h, rough, tone, joint)


def retaining_wall_cast(n=2048):
    """ADR 0338: cast-in-place reinforced-concrete retaining wall of a road cutting (mur oporowy żelbetowy,
    roads/tunnels.py WALL_MAT; critic s24 build #5 pkt 8: the ~150 m of the DK8 cutting under rondo Szymańskiego
    read as one clean plate). Smooth formwork face with faint panel seams and tie holes; expansion joints
    (dylatacje) every 6.0 m, 30 mm wide, recessed 10 mm with dark elastic sealant; weep holes (odwodnienie)
    at mid-bay 0.35 m above the footing with a wet stain running down; damp dirty band at the foot; scattered
    chips and stains. Run-off streaks from the top edge are NOT baked (the wall top height varies along the
    cutting) - the shader's _RUNOFF layer draws them from TEXCOORD_1 = (u m, 1 + metres below the top).
    Tile 12 x 8 m: two dylatacje per tile, and 8 m in v covers the tallest cutting wall (measured 6.7 m,
    chunk_3_4 of bialystok-kleeberga) so v never wraps. u along the wall, v up from the footing (UV0 metres)."""
    Lx, Ly = 12.0, 8.0
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=1638)
    X, Y = c.xy()
    v = Ly - Y                                   # metres up from the footing
    # dylatacje every 6 m (u = 0 and 6 in the 12 m tile), 30 mm wide, recessed, dark sealant
    du6 = np.minimum(X % 6.0, 6.0 - X % 6.0)
    dil = sstep(0.015, 0.006, du6)
    # formwork panel seams (vertical every 2.4 m, horizontal every 2.0 m), very faint; tie holes on a
    # 1.2 x 2.0 m grid, 24 mm, some with a rust halo
    fu = np.minimum(X % 2.4, 2.4 - X % 2.4)
    fh = np.minimum(v % 2.0, 2.0 - v % 2.0)
    form = np.maximum(sstep(0.004, 0.0015, fu) * 0.45, sstep(0.004, 0.0015, fh) * 0.30)
    dtx = np.minimum(X % 1.2, 1.2 - X % 1.2)
    dty = np.minimum(v % 2.0, 2.0 - v % 2.0)
    tie = sstep(0.012, 0.005, np.hypot(dtx, dty))
    rust = sstep(0.05, 0.012, np.hypot(dtx, dty)) * (1 - tie) * hash01(np.floor(X / 1.2).astype(int) * 3 +
                                                                        np.floor(v / 2.0).astype(int), 9)
    joint = np.maximum(np.maximum(dil, form), tie)
    # weep holes at mid-bay (u = 3 and 9), 0.35 m above the footing, with a wet stain running down to the foot
    du_w = np.minimum((X - 3.0) % 12.0, (3.0 - X) % 12.0)
    du_w = np.minimum(du_w, np.minimum((X - 9.0) % 12.0, (9.0 - X) % 12.0))
    weep = sstep(0.030, 0.012, np.hypot(du_w, v - 0.35))
    wet = (1 - sstep(0.06, 0.22, du_w)) * sstep(0.42, 0.05, v)          # damp halo + streak under the weep
    # damp dirty band at the foot (also drawn by the shader _SPLASH on top of this)
    foot = sstep(0.75, 0.03, v) * (0.7 + 0.3 * noise(c, 7, 0.15, 1.2, beta=1.0))
    # chips / ubytki: a few Voronoi cells per tile, dark, slightly deep
    d1, d2, idx, _, _ = voronoi(c, 5, 0.45, jitter=1.0)
    chip_cell = (hash01(idx, 6) < 0.10) & (d1 < 0.055)
    chip = chip_cell.astype(np.float32)
    # per-6 m bay tone (between dylatacje) - the pour lot reads as a bay
    bay = hash01(np.floor(X / 6.0).astype(int), 8)
    grain = noise(c, 1, c.px * 2, 0.012, beta=0.4)
    cloud = noise(c, 2, 0.25, 2.5, beta=1.1)
    pores_n = noise(c, 3, c.px * 1.5, 0.005, beta=0.2)
    pores = sstep(np.quantile(pores_n, 0.997), np.quantile(pores_n, 0.997) + 0.5, pores_n)
    lum = (1 + 0.05 * (bay - 0.5) + 0.035 * grain + 0.05 * cloud) * (1 - 0.55 * joint) \
        * (1 - 0.35 * dil) * (1 - 0.5 * tie) * (1 - 0.30 * chip) * (1 - 0.55 * pores)
    lum *= 1 - 0.30 * wet - 0.42 * foot * (0.6 + 0.4 * wet)
    lum *= 1 - 0.12 * rust
    lum *= _streaks(c, 4, 0.06)
    h = (-10e-3 * dil - 3e-3 * form - 5e-3 * tie - 6e-3 * chip - 1.5e-3 * pores - 4e-3 * wet
         + 0.25e-3 * grain + 0.4e-3 * cloud)
    rough = 0.86 + 0.05 * joint + 0.10 * wet + 0.08 * foot + 0.06 * chip + 0.03 * grain
    eid = (np.floor(X / 6.0) % 8).astype(np.float32) / 8.0
    return _finish("retaining_wall_cast", c, lum, h, rough, eid, joint, ao_k=0.7)


def roof_metal_tile(n=512):
    """Pressed metal tile sheet (blachodachowka, module 350 mm; ADR 0091): roll pitch 0.20 m, course step 0.35 m
    (dimensions WORKING_VALUE inside the product ranges). u along the eave, v up the slope. Tile 1.4 x 1.4 m
    (7 rolls x 4 courses). Until ADR 0316 this lattice was also the ceramic tile (set `roof_tiles`); a pressed sheet
    IS a perfect lattice, ceramic tiles are not - they have their own sets in sets_roof.py now."""
    L = 1.4
    c = Ctx(n, n, L, L, seed=531)
    X, Y = c.xy()
    v = L - Y
    wave, course = 0.20, 0.35
    pu = (X % wave) / wave
    pv = (v % course) / course                  # 0 = exposed lower edge of a course, 1 = under the next course
    roll = 0.5 - 0.5 * np.cos(2 * np.pi * np.clip(pu * 1.25, 0, 1))      # crest over 80 % of the pitch, flat pan 20 %
    row = np.floor(v / course).astype(int) % 4
    col = np.floor(X / wave).astype(int) % 7
    t = hash01(row * 7 + col, 1)
    grain = noise(c, 1, c.px * 2, 0.01, beta=0.4)
    lichen = sstep(0.6, 2.2, noise(c, 2, 0.02, 0.25, beta=0.8))
    # ADR 0094 (review s9 P2-3 "tile like trapezoid sheet"): the rolls were the strongest feature (relief 22 mm,
    # albedo -14 % in the pans) and the courses the weakest, so a slope read as vertical ribbing. Rolls 12 mm / -6 %,
    # course step 18 mm with a darker shadow line, tone per tile +-10 % and per course +-4 %.
    trow = hash01(row, 4)
    h = 0.012 * roll + 0.018 * (1 - pv) + 0.3e-3 * grain
    shadow = sstep(0.90, 1.0, pv)               # the line under the lower edge of the next course
    lum = ((1 + 0.20 * (t - 0.5) + 0.08 * (trow - 0.5) + 0.05 * grain) * (1 - 0.6 * shadow) * (1 - 0.06 * (1 - roll))
           * (1 - 0.10 * lichen))
    lum *= _streaks(c, 3, 0.08)
    rough = 0.72 + 0.12 * (1 - roll) + 0.1 * lichen
    return _finish("roof_metal_tile", c, lum, h, rough, t, shadow)


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


def barrier_galv(n=1024):
    """Weathered hot-dip galvanised road barrier (ADR 0117): one 4.0 m W-beam element, u along the beam, v = unrolled
    metres across the folded profile from the bottom edge (0.472 m; roads/streetscape furniture.W_PROFILE) in a
    4.0 x 0.5 m tile. Dull zinc patina (no spangle shine left after years), cloudy mottling, splice at u = 0 (lap
    edge shadow + 2 x 4 bolt heads on the flanks), a post bolt in the valley, road spray on the faces that look up
    (flank below each top fold) and along the bottom edge, run-off below bolts, sparse brown rust at the lap and on
    the bottom edge. Pattern read off Mapillary 177786140912399 / 500263111404933 / 454716650857984 (CC BY-SA,
    reference only, no pixels). All dimensions WORKING_VALUE. Posts / spacers sample u 1.3-2.0 (plain sheet)."""
    Lx, Ly = 4.0, 0.5
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=531)
    X, Y = c.xy()
    v = Ly - Y
    # fold lines of the unrolled profile (bottom edge 0 -> top edge 0.472)
    folds = (0.0746, 0.1396, 0.2361, 0.3326, 0.3976)
    valley = 0.2361
    cloud = noise(c, 1, 0.15, 2.0, beta=1.3)
    fine = noise(c, 2, c.px * 2, 0.03, beta=0.4)
    lum = 1.0 + 0.07 * cloud + 0.025 * fine
    # faces looking up collect road dust: the flank below the top edge (v 0.3976-0.472) and below the valley
    # (v 0.1396-0.2361); the bottom edge gets spray
    up = sstep(0.3976, 0.44, v) + sstep(0.1396, 0.19, v) * sstep(0.2361, 0.20, v)
    dirt = np.clip(0.55 * up + 0.9 * sstep(0.06, 0.0, v) + 0.6 * sstep(0.03, 0.0, np.abs(v - valley)), 0, 1)
    dirt *= 0.6 + 0.4 * sstep(-1.0, 1.0, noise(c, 3, 0.05, 0.8, beta=1.0, aniso=4.0))
    # splice: lap 0.32 m, the edge of the upper sheet at u = 0.32 casts a line; bolts in two columns
    du0 = np.minimum(X, Lx - X)
    lap_edge = sstep(0.006, 0.002, np.abs(X - 0.32)) + sstep(0.006, 0.002, du0)
    bolt = np.zeros_like(X)
    for bu in (0.06, 0.26):
        for bv in (0.107, 0.188, 0.284, 0.365):
            bolt = np.maximum(bolt, sstep(0.016, 0.011, np.hypot(X - bu, v - bv)))
    for bu in (0.16, 2.16):                                   # post bolt in the valley (posts every 2 / 4 m)
        bolt = np.maximum(bolt, sstep(0.016, 0.011, np.hypot(X - bu, v - valley)))
    # run-off below bolts and from the lap edge (short dark streaks down the face)
    runs = np.zeros_like(X)
    for bu in (0.06, 0.26, 0.16, 2.16, 0.32):
        w_ = sstep(0.02, 0.004, np.abs(X - bu + 0.006 * noise(c, 4, 0.02, 0.1)))
        runs = np.maximum(runs, w_ * sstep(0.40, 0.05, v) * 0.6)
    rust = sstep(1.5, 2.3, noise(c, 5, 0.02, 0.5, beta=0.7)) * np.clip(
        sstep(0.05, 0.0, v) + 0.7 * sstep(0.05, 0.0, np.abs(X - 0.32)) + 0.6 * sstep(0.05, 0.0, du0), 0, 1)
    rust = np.maximum(rust, 0.5 * bolt * sstep(0.0, 1.5, noise(c, 6, 0.3, 2.0)))
    lum *= (1 - 0.30 * dirt) * (1 - 0.45 * lap_edge) * (1 - 0.22 * runs) * (1 + 0.10 * bolt)
    foldm = np.zeros_like(X)
    for f_ in folds:
        foldm = np.maximum(foldm, sstep(0.006, 0.002, np.abs(v - f_)))
    lum *= 1 + 0.05 * foldm                                    # worn-bright arrises
    h = 2.5e-3 * bolt - 3.0e-3 * sstep(0.0, 0.004, X - 0.32) * sstep(0.34, 0.32, X) + 0.15e-3 * fine

    def tint(alb):
        rc = np.array([0.50, 0.30, 0.17], np.float32)
        brown = np.array([1.0, 0.94, 0.84], np.float32)
        k = np.clip(dirt * 0.8, 0, 1)[..., None]
        alb = alb * (1 - k) + alb * brown * k
        r = np.clip(rust, 0, 1)[..., None]
        return alb * (1 - 0.8 * r) + r * rc * float(alb.mean()) * 0.8
    # ADR 0123 (REVIEW s10-0117 P1-2): zinc is a metal - MaskMap.r carries bare zinc 1, road film / run-off / rust 0
    # (dielectric dirt on top), scaled per material by the manifest key `set_metal`; roughness of the weathered sheet
    # 0.56 (was 0.62; task brief 0.5-0.6, WORKING_VALUE - no gloss measurement), dirt and rust rougher
    rough = 0.56 + 0.14 * dirt + 0.20 * rust - 0.06 * foldm + 0.04 * cloud
    metal = np.clip(1.0 - 0.75 * dirt - 1.0 * rust - 0.5 * runs, 0.0, 1.0)
    return _finish("barrier_galv", c, lum, h, rough, np.zeros_like(X), np.maximum(lap_edge, bolt), extra=tint, ao_k=0.4,
                   metal=metal)


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


def car_grime(n=1024, lower_film=True):
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
    result = _finish("car_grime", c, lum, h, rough, np.zeros_like(X), np.zeros_like(X), extra=tint, ao_k=0.2)
    if not lower_film:
        # Preserve the LEGACY calibration gain. Recalibrating the clean map would
        # alter upper dust/peel pixels unrelated to the removed lower film.
        legacy_raw = tint(lum[..., None] * np.ones(3, np.float32)).astype(np.float32)
        gain = MOD_MEAN / float((legacy_raw @ LUM).mean())
        clean_lum = (1 + 0.01 * peel) * (1 - 0.07 * runs * belt) * (1 + 0.05 * dust)
        clean_raw = clean_lum[..., None] * np.ones(3, np.float32)
        kd = dust[..., None] * 0.5
        clean_raw = clean_raw * (1 - kd) + clean_raw * np.array([1.0, 0.97, 0.90], np.float32) * kd
        # Keep the legacy repeat-boundary padding: the writer's periodic Gaussian
        # otherwise carries the changed bottom film into the unchanged top rows.
        # Native paint UV/Tile ranges are audited separately; mip filtering is not
        # claimed identical merely because point coordinates miss this gutter.
        clean_region = v >= 0.05
        result.albedo = np.where(((film > 0) & clean_region)[..., None],
                                 np.clip(clean_raw.astype(np.float32) * gain, 0, 1), result.albedo)
        result.rough = np.where(clean_region, np.clip(0.32 + 0.15 * dust, 0.05, 1).astype(np.float32), result.rough)
        # Clean-only Mask.R payload: exactly the film removed here. Seven car
        # paint materials have MetallicScale0 and a separate CarPaint metal model.
        result.metal = np.where(clean_region, film, 0).astype(np.float32)
    return result


def parapet_runoff(nx=1024, ny=160, seed=521):
    """Run-off streaks under the parapet coping of industrial halls (zacieki pod attyką). Not a tiling facade set
    but a layer in "wall-top space": u = metres along the wall (periodic, 24 m), v = metres below the bottom of the
    attic fascia (row 0 = right under the coping / fascia, row ny-1 = 4 m down; the shader clamps v and fades it
    out). Physical story (photo look of 1970s-2000s Białystok halls, WORKING_VALUE, no measured data): rain water
    with roof dust and soot runs off the coping drip edge, collects at the sheet joints (every 2-3 m) and at
    sagging spots, and leaves
      - a dirty band right under the drip edge (5-35 cm, uneven),
      - a strong long streak below most coping joints (0.6-3.8 m, tapering, slightly meandering, broken),
      - many faint fine drip lines in between (0.2-1.2 m),
      - a few broad soft smudges (sagging coping, 0.3-1.2 m wide),
      - rust-brown streaks below some fixings (steel coping fasteners), shorter.
    Channels (linear, RGB): R soot / dirt run-off amount 0..1, G rust amount 0..1, B 0 (reserved).
    The shader scales R per wall by the macro map and per building by TEXCOORD_1.y (streak length scale)."""
    Lx, Ly = 24.0, 4.0
    c = Ctx(nx, ny, Lx, Ly, seed=seed)
    X, Y = c.xy()                                   # Y = metres below the top (row 0 = top)
    rng = c.rng(1)
    soot = np.zeros_like(X)
    rust = np.zeros_like(X)

    def wrapdx(x0):
        return (X - x0 + Lx / 2) % Lx - Lx / 2

    def streak(x0, w, length, inten, meander, start=0.0, wobble_k=0):
        """Tapering vertical run: gaussian across (sigma w), fades over length, meanders with depth, broken into
        runs by stretched noise (kept periodic via the shared noise fields)."""
        ph = rng.uniform(0, 2 * np.pi)
        f = rng.uniform(1.2, 3.5)
        dx = wrapdx(x0 + meander * np.sin(f * Y + ph) + rng.uniform(-0.02, 0.02) * Y)
        sig = w * (1.0 + 0.6 * np.clip(Y / max(length, 1e-3), 0, 1.5))           # widens a little going down
        across = np.exp(-0.5 * (dx / sig) ** 2)
        t = (Y - start) / max(length, 1e-3)
        along = np.where(t < 0, 0.0, (1 - sstep(0.15, 1.0, t)) * (1 - 0.35 * t))
        return np.clip(inten * across * along, 0, None)

    breaker = sstep(-0.9, 0.8, noise(c, 2, 0.08, 1.2, beta=0.8, aniso=1.0 / 10.0))   # broken runs (vertical)
    # joints of the coping sheets: 2.0-3.0 m apart (periodic over 24 m)
    xs, x = [], 0.0
    while x < Lx - 1.0:
        xs.append(x)
        x += rng.uniform(2.0, 3.0)
    for xj in xs:
        if rng.random() < 0.78:
            # v2 (REVIEW r6 / G3 wires-streaks-v2): the 2.5-6 cm runs of v1 were below one texel on Low (94 mm) and
            # below one screen pixel from the road at 25-80 m, so the layer read as clean sheet; joint streaks are now
            # 5-14 cm (a run spreads on ribbed cladding: it follows 1-3 ribs) and longer (lognormal median 2.0 m)
            L = float(np.clip(rng.lognormal(np.log(2.0), 0.45), 0.8, 3.7))
            soot += streak(xj, rng.uniform(0.05, 0.14), L, rng.uniform(0.5, 0.95), rng.uniform(0.005, 0.03))
            if rng.random() < 0.45:                                          # twin run beside the joint
                soot += streak(xj + rng.uniform(-0.25, 0.25), rng.uniform(0.012, 0.03), 0.6 * L, rng.uniform(0.2, 0.5), 0.01)
        if rng.random() < 0.22:                                              # rusty fastener below the joint
            xr = xj + rng.uniform(-0.6, 0.6)
            rust += streak(xr, rng.uniform(0.025, 0.06), rng.uniform(0.4, 1.4), rng.uniform(0.4, 0.8), 0.006, start=0.02)
    # fine drip lines everywhere along the drip edge (~3 per metre)
    for _ in range(int(1.5 * Lx)):
        soot += streak(rng.uniform(0, Lx), rng.uniform(0.012, 0.03), rng.uniform(0.3, 1.4), rng.uniform(0.1, 0.3), 0.004)
    # broad smudges below sagging coping
    for _ in range(6):
        soot += streak(rng.uniform(0, Lx), rng.uniform(0.2, 0.55), rng.uniform(0.8, 2.8), rng.uniform(0.15, 0.35), 0.05)
    soot *= 0.55 + 0.45 * breaker
    # dirty band under the drip edge: uneven depth along the wall, soft lower edge
    bd = 0.05 + 0.30 * sstep(-1.2, 1.6, noise(c, 3, 0.6, 8.0, beta=1.0, aniso=1.0))   # depth varies along u
    band = (1 - sstep(0.05 * bd, 1.4 * bd, Y)) ** 1.5 * (0.22 + 0.3 * sstep(-1.0, 1.5, noise(c, 4, 0.1, 3.0)))
    soot = soot + band
    soot = 1 - np.exp(-1.25 * soot)                                          # soft saturation of overlaps
    rust = 1 - np.exp(-1.6 * rust * (0.6 + 0.4 * breaker))
    # nothing reaches the clamp row: fade the last 0.4 m so the clamped sample is 0
    fade = 1 - sstep(Ly - 0.4, Ly - 0.05, Y)
    out = np.dstack([soot * fade, rust * fade, np.zeros_like(X)]).astype(np.float32)
    return c, out


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


def log_whitewash(n=1024):
    """ADR 0305: limewashed hewn-log wall of an old Podlasie house (Dom Klattow, Knyszyn - owner photos, reference
    only): ten courses of squared logs 0.20-0.24 m high (WORKING_VALUE: the photos show 9-10 courses on a ~2.0 m
    wall), wavering caulked joints that read as thin darker lines, drying shakes along the grain, brush clouds of
    the limewash, a soiled / flaking band on the two bottom logs and faint run-off under the joints.
    u along the wall, v up from the top of the plinth. Tile 4.0 x 2.2 m (one tile = the whole wall height)."""
    Lx, Ly = 4.0, 2.2
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=3051)
    X, Y = c.xy()
    v = Ly - Y
    heights = np.array([0.23, 0.21, 0.24, 0.20, 0.22, 0.23, 0.21, 0.24, 0.20, 0.22])
    tops = np.cumsum(heights)                                    # joint j lies at tops[j] (the last one = tile edge)
    wob = 0.006 * noise(c, 1, 0.8, 4.0, beta=1.2, aniso=0.5) + 0.0012 * noise(c, 2, 0.08, 0.5, beta=1.0)
    vv = (v + wob) % Ly
    row = np.searchsorted(tops, vv, side="right") % len(heights)
    lo = np.concatenate([[0.0], tops[:-1]])[row]
    hi = tops[row]
    dj = np.minimum(vv - lo, hi - vv)                            # distance to the nearest joint line, m
    jw = 0.003 + 0.0025 * sstep(-1.0, 1.5, noise(c, 3, 0.3, 2.0, aniso=3.0))      # half width of the open joint
    joint = sstep(jw + 0.003, jw * 0.4, dj)
    arris = sstep(0.030, 0.006, dj) * (1 - joint)                # hewn edge rolling into the joint
    tone = hash01(row, 11)
    grain = noise(c, 4, c.px * 2, 0.02, beta=0.5, aniso=8.0)     # wood fibre under the wash, along the log
    adze = noise(c, 5, 0.04, 0.3, beta=1.0, aniso=2.5)           # hewing facets
    brush = noise(c, 6, 0.01, 0.12, beta=0.7, aniso=0.6)         # limewash brush strokes
    cloud = noise(c, 7, 0.4, 3.0, beta=1.3)
    sh = noise(c, 8, 0.004, 0.6, beta=0.9, aniso=14.0)           # shakes: long thin cracks along the grain
    shake = sstep(2.35, 2.9, np.abs(sh) * (0.75 + 0.5 * sstep(-0.5, 1.5, noise(c, 9, 0.5, 2.5)))) * (1 - joint)
    # limewash worn off low down (rain splash) and in patches where it flakes: grey wood shows through
    low = sstep(0.50, 0.05, v)
    flake_n = noise(c, 10, 0.03, 0.5, beta=1.1, aniso=1.8)
    flake = sstep(1.55 - 1.1 * low, 2.3 - 1.1 * low, flake_n) * (0.35 + 0.65 * low)
    under = sstep(0.07, 0.0, hi - vv) * 0.0 + sstep(0.09, 0.0, vv - lo) * sstep(-0.2, 1.2, noise(c, 12, 0.05, 0.6))
    lum = (1 + 0.05 * (tone - 0.5) + 0.018 * grain + 0.025 * adze + 0.02 * brush + 0.035 * cloud)
    lum *= (1 - 0.07 * arris) * (1 - 0.06 * under) * (1 - 0.10 * low * (0.6 + 0.4 * sstep(-1, 1, cloud)))
    lum = lum * (1 - 0.30 * flake) * (1 - 0.45 * shake)
    lum = lum * (1 - joint) + joint * 0.50
    lum *= _streaks(c, 13, 0.05)
    h = (1.5e-3 * adze + 0.4e-3 * grain + 0.25e-3 * brush - 0.5e-3 * flake) * (1 - joint) \
        - 9e-3 * joint - 4e-3 * arris - 2.5e-3 * shake
    rough = 0.90 + 0.04 * flake + 0.05 * joint

    def tint(alb):
        # joints, shakes and bare patches are warm grey wood / old caulk, the wash itself stays neutral
        k = np.clip(joint + 0.8 * flake + 0.8 * shake, 0, 1)[..., None]
        return alb * (1 - k) + alb * np.array([1.05, 0.98, 0.86], np.float32) * k
    return _finish("log_whitewash", c, lum, h, rough, tone, joint, extra=tint, ao_k=0.9)


def fieldstone(n=1024):
    """ADR 0305: fieldstone footing (podmurowka z kamienia polnego) of an old log house: rounded glacial boulders
    0.15-0.30 m bedded in sandy lime mortar, per-stone tone and hue (grey, pink, rusty and dark granites), a damp,
    mossy foot. u along the wall, v up. Tile 2.4 x 0.6 m (one tile = the footing height). WORKING_VALUE sizes read off
    the owner photos of Dom Klattow (reference only).
    Round 3 (klattow-r3-s24): the first version read as crazy paving - light flat stones cut by thin black lines in
    the sun (the sqrt dome had a vertical flank at every joint, so the normal map drew a hard shadow line) and as
    dark stones in pale mortar in the shade (stone edges and the damp foot were darker than the mortar in the albedo).
    Now: a smooth dome with no cusp, bed joints 2-4 cm wide and only a little recessed, mortar darker than the mean
    stone and lighter than the dark ones, stone tone 0.53-1.03 x with a few dark boulders, so neither reading wins."""
    Lx, Ly = 2.4, 0.6
    c = Ctx(n, n // 4, Lx, Ly, seed=3052)
    X, Y = c.xy()
    v = Ly - Y
    warp = (0.02 * noise(c, 1, 0.1, 0.6), 0.015 * noise(c, 2, 0.1, 0.6))
    d1, d2, i1, _, _ = voronoi(c, 3, 0.22, 0.85, warp=warp, cell_y=0.19)
    e = edge_dist(d1, d2) + 0.004 * noise(c, 8, 0.01, 0.06)      # ragged stone outlines
    mort = sstep(0.022, 0.009, e)
    dome = sstep(0.0, 0.075, e)                                  # rounded boulder face, flat-topped, no cusp at the joint
    t = hash01(i1, 1)
    hue = hash01(i1, 2)
    dark = sstep(0.82, 0.90, hash01(i1, 3))                      # a few dark (basalt-grey / wet) boulders
    speck = noise(c, 4, c.px * 2, 0.012, beta=0.3)               # granite crystals
    lump = noise(c, 5, 0.03, 0.2, beta=1.1)
    sand = noise(c, 9, c.px * 2, 0.02, beta=0.6)
    damp = sstep(0.30, 0.0, v) * (0.6 + 0.4 * sstep(-1, 1, noise(c, 6, 0.1, 0.8)))
    stone = (0.78 + 0.50 * (t - 0.5) + 0.07 * speck + 0.07 * lump) * (1 - 0.30 * dark)
    lum = stone * (1 - mort) + mort * (0.56 + 0.05 * sand)
    lum *= 1 - 0.18 * damp
    h = (0.016 * dome + 2e-3 * lump + 0.4e-3 * speck) * (1 - mort) + (-2e-3 + 0.6e-3 * sand) * mort
    rough = 0.84 + 0.08 * mort + 0.05 * damp

    def tint(alb):
        m = mort[..., None]
        warm = np.array([1.16, 0.96, 0.80], np.float32)          # pink / rusty granite
        cool = np.array([0.94, 1.00, 1.07], np.float32)          # grey-blue granite
        k = sstep(0.50, 0.90, hue)[..., None]
        k2 = sstep(0.25, 0.0, hue)[..., None]
        stone_c = alb * (1 + (warm - 1) * k + (cool - 1) * k2)
        moss = (damp * sstep(0.2, 1.4, noise(c, 7, 0.02, 0.2)))[..., None] * 0.5
        out = stone_c * (1 - m) + alb * m * np.array([1.04, 0.99, 0.90], np.float32)      # sandy lime mortar
        return out * (1 - moss) + out * np.array([0.80, 1.05, 0.62], np.float32) * moss
    return _finish("fieldstone", c, lum, h, rough, t, mort, extra=tint, ao_k=0.5)


SHINGLE_ROWS = 7              # courses of the 1.5 m wood_shingles tile = streetscape.knyszyn_lamus_0305.SHINGLE_COURSE


def wood_shingles(n=1024):
    """ADR 0305: split wooden shingles (gont) of the timber granary by the presbytery of Knyszyn (owner photo
    klattow-02, reference only): courses with 0.214 m exposure (the photo shows ~29 courses on the ~6.2 m slope),
    shingles 0.09-0.15 m wide with staggered joints, weathered silver-grey, darker butt ends and gaps, fibre along
    the slope. u along the eave, v up the slope. Tile 1.5 x 1.5 m (SHINGLE_ROWS courses). WORKING_VALUE sizes.
    Round 3 (klattow-r3-s24): the course is geometry on the lamus (every course a strip proud at its butt), so v = 0
    of the tile is a butt line; the band under the next course (pv -> 1) carries the cast shadow, wider and softer
    than in the first version, whose 0.15 m courses on a flat quad read as an even grey sheet."""
    L = 1.5
    c = Ctx(n, n, L, L, seed=3053)
    X, Y = c.xy()
    v = L - Y
    course = L / SHINGLE_ROWS
    warp = 0.004 * noise(c, 1, 0.1, 0.8, beta=1.0, aniso=3.0)
    vv = (v + warp) % L
    row = np.floor(vv / course).astype(int) % SHINGLE_ROWS
    pv = (vv % course) / course                 # 0 = exposed butt edge of a course, 1 = under the next course
    rng = c.rng(2)
    sid = np.zeros(X.shape, np.int64)
    du = np.zeros(X.shape, np.float32)
    for r in range(SHINGLE_ROWS):
        w = rng.uniform(0.09, 0.15, 40)
        w = w[: int(np.searchsorted(np.cumsum(w), L)) + 1]
        edges = np.concatenate([[0.0], np.cumsum(w * (L / w.sum()))]) + rng.uniform(0, 0.05)
        xs = (X - edges[0]) % L
        k = np.clip(np.searchsorted(edges - edges[0], xs, side="right") - 1, 0, len(w) - 1)
        lo, hi = (edges - edges[0])[k], (edges - edges[0])[k + 1]
        sel = row == r
        sid[sel] = (r * 64 + k)[sel]
        du[sel] = np.minimum(xs - lo, hi - xs)[sel]
    gap = sstep(0.0040, 0.0012, du)
    t = hash01(sid, 1)
    cup = hash01(sid, 2)
    drop = (hash01(sid, 3) - 0.5) * 0.10        # butts not on one line: each shingle hangs up to 1 cm lower / higher
    butt = sstep(0.07, 0.0, pv + drop)          # dark, weathered end grain of the butt
    under = sstep(0.80, 0.97, pv - drop)         # cast shadow of the next course
    fibre = noise(c, 3, c.px * 2, 0.012, beta=0.5, aniso=0.12)
    cloud = noise(c, 4, 0.3, 1.5, beta=1.2)
    lich = sstep(0.9, 2.2, noise(c, 5, 0.02, 0.2, beta=0.9))
    lum = (1 + 0.34 * (t - 0.5) + 0.14 * fibre + 0.07 * cloud) * (1 - 0.30 * butt) * (1 - 0.68 * under) * (1 - 0.6 * gap)
    lum *= 1 - 0.05 * lich
    h = 0.012 * (1 - pv) + 0.003 * (cup - 0.5) * 2 + 0.6e-3 * fibre - 6e-3 * gap
    rough = 0.86 + 0.06 * gap + 0.05 * lich

    def tint(alb):
        k = (lich * 0.3)[..., None]
        warm = (sstep(0.7, 1.0, t) * 0.5)[..., None]             # a few younger, browner shingles
        out = alb * (1 - warm) + alb * np.array([1.12, 0.98, 0.82], np.float32) * warm
        return out * (1 - k) + out * np.array([0.92, 1.04, 0.86], np.float32) * k
    return _finish("wood_shingles", c, lum, h, rough, t, np.maximum(gap, under), extra=tint, ao_k=0.8)


# joints between board rows as fractions of the tile height - the measured rows of wood_siding
# (streetscape.buildings_mesh.WOOD_JOINT_V), so every wood_planks* UV rule (one board row per trim board, runs,
# vertical gable boarding) fits this set too
_BOARD_JOINT_V = (0.0317, 0.0815, 0.1343, 0.1870, 0.2388, 0.2876, 0.3394, 0.3940, 0.4438, 0.4966, 0.5484, 0.6001,
                  0.6499, 0.7061, 0.7622, 0.8188, 0.8745, 0.9224, 0.9761)


def boards_painted(n=2048):
    """ADR 0305: boards under old opaque paint (white gable boarding, barge and fascia boards of Dom Klattow - owner
    photos, reference only): 19 rows on the 6.0 x 2.6 m tile at the joints of wood_siding, thin shadow joints, a
    little grain and hairline cracks showing through the paint, faint tone from board to board. The scan
    wood_siding under a white tint read as grey weathered wood (round 1 of ADR 0305). u along the boards, v across."""
    Lx, Ly = 6.0, 2.6
    c = Ctx(n, int(n * Ly / Lx) // 4 * 4, Lx, Ly, seed=3054)
    X, Y = c.xy()
    v = Ly - Y
    J = np.array(_BOARD_JOINT_V) * Ly
    wob = 0.0012 * noise(c, 1, 0.5, 4.0, beta=1.0, aniso=4.0)
    vv = (v + wob) % Ly
    k = np.searchsorted(J, vv, side="right")                     # 0..19; 0 and 19 are the same board (wraps)
    row = k % len(J)
    lo = np.where(k == 0, J[-1] - Ly, J[np.clip(k - 1, 0, len(J) - 1)])
    hi = np.where(k == len(J), J[0] + Ly, J[np.clip(k, 0, len(J) - 1)])
    dj = np.minimum(vv - lo, hi - vv)
    joint = sstep(0.0042, 0.0015, dj)
    arris = sstep(0.014, 0.004, dj) * (1 - joint)
    tone = hash01(row, 3)
    grain = noise(c, 2, c.px * 2, 0.02, beta=0.6, aniso=10.0)
    crack_n = noise(c, 3, 0.004, 0.5, beta=0.9, aniso=16.0)
    crack = sstep(2.5, 3.0, np.abs(crack_n)) * (1 - joint)
    cloud = noise(c, 4, 0.3, 2.5, beta=1.2)
    chalk = noise(c, 5, 0.01, 0.1, beta=0.6)
    lum = (1 + 0.035 * (tone - 0.5) + 0.02 * grain + 0.03 * cloud + 0.012 * chalk) * (1 - 0.05 * arris) * (1 - 0.35 * crack)
    lum = lum * (1 - joint) + joint * 0.42
    h = (0.35e-3 * grain + 0.15e-3 * chalk) * (1 - joint) - 5e-3 * joint - 1.5e-3 * arris - 1.2e-3 * crack
    rough = 0.82 + 0.06 * joint + 0.04 * crack

    def tint(alb):
        kk = np.clip(joint + crack, 0, 1)[..., None]
        return alb * (1 - kk) + alb * np.array([1.04, 0.98, 0.88], np.float32) * kk
    return _finish("boards_painted", c, lum, h, rough, tone, joint, extra=tint, ao_k=0.8)


FACADE_SETS = {
    "sandwich_ribbed": dict(fn=sandwich_ribbed, tile_m=[6.0, 6.0],
        slots=["hall_wall_grey", "hall_wall_silver", "hall_wall_white", "hall_wall_ivory", "booth_panel"],
        note="Horizontal sandwich panels 1.0 m, micro-lined face, shadow-gap joints, run-off streaks."),
    "sandwich_smooth": dict(fn=sandwich_smooth, tile_m=[3.45, 3.45], slots=["hall_wall_smooth"],
        note="Flat-faced horizontal sandwich panels, courses 1.15 m, micro-lining, shadow-gap joints, no baked streaks (ADR 0185)."),
    "cladding_vertical": dict(fn=cladding_vertical, tile_m=[3.0, 3.0], slots=["cladding_vertical_grey"],
        note="Flat-faced vertical wall panels 1.0 m, micro-lining, shadow-gap joints, no baked streaks (ADR 0185)."),
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
    "concrete_blocks_split": dict(fn=concrete_blocks_split, tile_m=[2.0, 1.0], slots=["ramp_wall_blocks"],
        note="Split-face concrete blocks 1.0 x 0.5 m, half-bond, dark recessed joints (ramp retaining walls, ADR 0159)."),
    "concrete_panels_wall": dict(fn=concrete_panels_wall, tile_m=[3.0, 3.0], slots=["ramp_wall_panels"],
        note="Precast facing panels 1.5 x 1.5 m in columns shifted by half a panel, open joints (Biezenstwa ramp walls, ADR 0159)."),
    "retaining_wall_cast": dict(fn=retaining_wall_cast, tile_m=[12.0, 8.0], slots=["retaining_wall"],
        note="ADR 0338: cast-in-place cutting retaining wall (roads/tunnels.py): dylatacje every 6 m, weep-hole stains, "
             "damp foot band, formwork seams + tie holes, chips. Tile 12 x 8 m; run-off streaks from the top come from "
             "the shader _RUNOFF layer (TEXCOORD_1), not from this map."),
    "roof_metal_tile": dict(fn=roof_metal_tile, tile_m=[1.4, 1.4], slots=["roof_metal_*"],
        note="Pressed metal tile sheet, roll pitch 0.20 m, course step 0.35 m (u along the eave, v up the slope)."),
    "curtain_folds": dict(fn=curtain_folds, tile_m=[4.8, 2.7], slots=["trailer_curtain_*"],
        note="Curtainsider tarpaulin folds, sag between straps, grime on the lower third."),
    "container_corrugation": dict(fn=container_corrugation, tile_m=[2.78, 2.6], slots=["container_*"],
        note="Container side corrugation 0.278 m pitch, dents, rust spots."),
    "barrier_galv": dict(fn=barrier_galv, tile_m=[4.0, 0.5], slots=["barrier_steel"],
        note="Weathered galvanised W-beam element 4.0 m (ADR 0117): u along, v unrolled across the folded profile "
             "(0.472 m); splice bolts, lap edge, road dust on up-facing flanks, bottom-edge spray, sparse rust."),
    "noise_cassette": dict(fn=noise_cassette, tile_m=[4.0, 4.0], slots=["noise_panel"],
        note="Absorbing noise-barrier cassettes 4.0 x 0.5 m, perforated face, joint lips, splash grime, run-off."),
    "concrete_fence_panel": dict(fn=concrete_fence_panel, tile_m=[4.0, 2.0], slots=["concrete_fence"],
        note="Prefab concrete panel fence: 2 m bays, 0.5 m panels, pores, joints, splash grime, run-off."),
    "hedge_foliage": dict(fn=hedge_foliage, tile_m=[1.5, 1.5], slots=["hedge_berberis"],
        note="Clipped red berberis hedge face: leaf clusters, dark voids, thin holes (u along, v over the section)."),
    "soil_bed": dict(fn=soil_bed, tile_m=[2.0, 2.0], slots=["bed_soil"],
        note="Island planting bed: loam with bark mulch chips, a few stones, leaf litter (u, v plan metres)."),
    "car_grime_clean": dict(fn=lambda: car_grime(lower_film=False), tile_m=[5.0, 2.5],
        slots=["car_paint_silver", "car_paint_grey", "car_paint_black", "car_paint_white", "car_paint_white2", "car_paint_blue", "car_paint_red"],
        note="R4 clean lower shell; original upper dust/runs/peel and calibration retained. Road deposition is instance-driven."),
    "car_grime": dict(fn=car_grime, tile_m=[5.0, 2.5], slots=["car_paint_*"],
        note="Parked-car paint film: road spray on sills, dust on top, rain runs (u along body, v = height)."),
    "box_panel": dict(fn=box_panel, tile_m=[4.8, 2.7], slots=["trailer_box_white"],
        note="Box body panels with seam profiles every 1.2 m, road film low down."),
    "log_whitewash": dict(fn=log_whitewash, tile_m=[4.0, 2.2], slots=["log_wall_*"],
        note="ADR 0305: limewashed hewn-log wall, ten courses 0.20-0.24 m, caulked joints, shakes, worn foot "
             "(u along the wall, v up from the plinth; one tile = the wall height)."),
    "fieldstone": dict(fn=fieldstone, tile_m=[2.4, 0.6], slots=["fieldstone_plinth"],
        note="ADR 0305: fieldstone footing of a log house, boulders 0.15-0.30 m in lime mortar, damp mossy foot."),
    "wood_shingles": dict(fn=wood_shingles, tile_m=[1.5, 1.5], slots=["roof_shingles_*"],
        note="ADR 0305: split wooden shingles (gont), courses 0.15 m, shingles 0.07-0.12 m, weathered silver-grey."),
    "boards_painted": dict(fn=boards_painted, tile_m=[6.0, 2.6], slots=["wood_planks_white"],
        note="ADR 0305: boards under old opaque paint, 19 rows at the joints of wood_siding (u along the boards)."),
}
# ADR 0316: ceramic / cement roof tiles (esowka, karpiowka, zakladkowa) live in sets_roof.py
FACADE_SETS.update(RS.ROOF_SETS)
roof_tiles, roof_tiles_old, roof_karpiowka, roof_zakladkowa = RS.roof_tiles, RS.roof_tiles_old, RS.roof_karpiowka, RS.roof_zakladkowa
