"""ADR 0352 addendum (garden-trees-s24 / agy-garden-var-s24): the small garden trees of the plot kit - a young broadleaf
tree (crown radius below plantings.LIB_MIN_R_M, 3.2-6.4 m) and the orchard tree (apple / plum / pear, 2.7-6.2 m) - as a
forking stem, visible 3D scaffold limbs and asymmetric CLUMPS of foliage on them, instead of whole-crown cards crossed
on the axis or symmetric "lollipops".

Why:
- Critic s24 build 10: crossed whole-crown cards were a ball on a stick with a dark wedge in sunlight.
- Critic s24 day 27: `vase` and `lean` young trees still read as a straight stick + round crown without visible boughs
  below the foliage, and neighboring trees repeated one size, upright angle and green hue.

Here:
1. Both `young_tree` and `orchard_tree` fork visibly BELOW the crown into 3D crossed-strip scaffold limbs (`_strip`),
   with species-dependent first-branch height (`birch` / `ash` highest, `linden` medium, `maple` / `chestnut` spreading)
   and asymmetric multi-level foliage clumps (`v_lo` crops the painted stem base of crown sprites).
2. Per-instance variation without extra draw calls: full 360 deg yaw, whole-tree 3D tilt up to +-4 deg, 4 distinct
   crown forms per type, per-tree ADR-0352 brightness/hue tint via `TEXCOORD_1` (`WorldPlotKit.shader`), and
   per-instance scale 0.7-1.3 applied at placement (`plantings.garden_trees` / `plots`).
3. Normals radiate from the crown centre (flattened, biased upward); occlusion falls softly towards the foot of each
   clump. No dark core anywhere. All proportions WORKING_VALUE (refs: owner photos P05 / P08 / P12 in docs/05)."""
from __future__ import annotations

import math

import numpy as np

from . import plot_kit as PK
from .facade_kit import hfloat

YOUNG_H_MAX_M = 6.5           # garden_tree(): below this height the full variant is the clump tree
YOUNG_FORMS = ("forked", "lean", "broad", "tiered")
ORCHARD_FORMS = ("open", "flat", "upright", "leaning")
MAX_TILT_DEG = 4.0

# Species habit for young broadleaf trees: fork height fraction of cb, limb spread factor, whether a slender
# central leader continues above the fork, and bottom crop v_lo of the species' crown sprite.
_SPECIES_YOUNG = {
    "birch":    dict(fork_k=0.92, spread=0.92, leader=True,  v_lo=(0.02, 0.06), bark="concrete", twig="trunk"),
    "ash":      dict(fork_k=0.88, spread=0.96, leader=False, v_lo=(0.02, 0.06), bark="trunk",    twig="trunk"),
    "linden":   dict(fork_k=0.84, spread=0.98, leader=False, v_lo=(0.02, 0.06), bark="trunk",    twig="trunk"),
    "maple":    dict(fork_k=0.78, spread=1.05, leader=False, v_lo=(0.02, 0.06), bark="trunk",    twig="trunk"),
    "chestnut": dict(fork_k=0.76, spread=1.06, leader=False, v_lo=(0.02, 0.06), bark="trunk",    twig="trunk"),
}


def _fol(n, occ=1.0):
    n = np.asarray(n, float)
    n = n / max(float(np.linalg.norm(n)), 1e-9) * min(max(float(occ), 0.05), 1.0)
    return [n[0] * 0.5 + 0.5, n[1] * 0.5 + 0.5, n[2] * 0.5 + 0.5, 1.0]


def _unit(v):
    v = np.asarray(v, float)
    return v / max(float(np.linalg.norm(v)), 1e-9)


def _dir(az, tilt):
    """Unit vector leaning `tilt` rad from the vertical towards azimuth az."""
    return np.array([math.cos(az) * math.sin(tilt), math.sin(az) * math.sin(tilt), math.cos(tilt)])


def _tree_uv1(key, bright_amp=0.11, hue_amp=0.05):
    """ADR 0352 per-tree albedo variation packed into TEXCOORD_1: (brightness_mul, 0.5 - hue_shift).
    gltf.py flips v -> 1 - v, so WorldPlotKit.shader reads uv1.x = brightness and uv1.y = 0.5 + hue_shift."""
    br = 1.0 + bright_amp * (hfloat(key, "tbr") * 2.0 - 1.0)
    hu = hue_amp * (hfloat(key, "thu") * 2.0 - 1.0)
    return (round(br, 4), round(0.5 - hu, 4))


def _tilt_tree(kit, start_idx, pivot, key, max_deg=MAX_TILT_DEG):
    """Rotate all geometry and foliage normals added to `kit` since `start_idx` around `pivot` by up to +-max_deg."""
    ang = (hfloat(key, "tlt") * 2.0 - 1.0) * math.radians(max_deg)
    if abs(ang) < 1e-4:
        return
    az = hfloat(key, "taz") * 6.2832
    ux, uy = -math.sin(az), math.cos(az)
    c, s = math.cos(ang), math.sin(ang)
    oc = 1.0 - c
    R = np.array([
        [c + ux * ux * oc, ux * uy * oc, uy * s],
        [ux * uy * oc, c + uy * uy * oc, -ux * s],
        [-uy * s, ux * s, c],
    ], float)
    piv = np.asarray(pivot, float)
    for idx in range(start_idx, len(kit.V)):
        kit.V[idx] = piv + (kit.V[idx] - piv) @ R.T
        C = kit.C[idx]
        fol = C[:, 3] > 0.5
        if fol.any():
            n = (C[fol, :3] * 2.0 - 1.0) @ R.T
            C[fol, :3] = np.clip(n * 0.5 + 0.5, 0.0, 1.0)


def _stem(kit, a, b, ra, rb, a0, sides=3, uv=None):
    """Tapered open prism from 3D point a to b (2 * sides triangles), bark swatch, flat shaded."""
    uv = uv or PK.SWATCH["trunk"]
    a, b = np.asarray(a, float), np.asarray(b, float)
    ax = _unit(b - a)
    e1 = _unit(np.cross(ax, [0.0, 0.0, 1.0]) if abs(ax[2]) < 0.95 else np.cross(ax, [1.0, 0.0, 0.0]))
    e2 = np.cross(ax, e1)
    ring = [e1 * math.cos(a0 + 2 * math.pi * k / sides) + e2 * math.sin(a0 + 2 * math.pi * k / sides) for k in range(sides)]
    for k in range(sides):
        d0, d1 = ring[k], ring[(k + 1) % sides]
        kit.quad([a + d1 * ra, a + d0 * ra, b + d0 * rb, b + d1 * rb], [uv] * 4)


def _strip(kit, a, b, wa, wb, yaw, uv=None):
    """A limb as two crossed tapered strips (4 triangles): seen from every side."""
    uv = uv or PK.SWATCH["trunk"]
    a, b = np.asarray(a, float), np.asarray(b, float)
    ax = _unit(b - a)
    e1 = _unit(np.cross(ax, [0.0, 0.0, 1.0]) if abs(ax[2]) < 0.95 else np.cross(ax, [1.0, 0.0, 0.0]))
    e2 = np.cross(ax, e1)
    for k in range(2):
        d = e1 * math.cos(yaw + k * 1.5708) + e2 * math.sin(yaw + k * 1.5708)
        kit.quad([a - d * wa, a + d * wa, b + d * wb, b - d * wb], [uv] * 4)


def _clump(kit, foot, axis, yaw, W, H, sprite, centre, occ=(0.78, 1.0), flip=False, v_lo=0.0, squash=0.50, up=0.58,
           twist=0.45, foot_w=0.48):
    """One foliage card as a branch clump: its foot (middle of the lower edge) at 3D `foot`, growing along unit `axis`
    for H, W wide at the tip. Normals radiate from `centre` (flattened, biased upward) so the whole crown shades as
    one volume; occlusion softens toward the foot inside the crown."""
    u0, u1, v0, v1 = PK.sprite(sprite)
    v0 = v0 + (v1 - v0) * v_lo
    if flip:
        u0, u1 = u1, u0
    foot, axis, centre = np.asarray(foot, float), _unit(axis), np.asarray(centre, float)
    h = np.array([axis[0], axis[1], 0.0])
    if np.linalg.norm(h) < 1e-3:
        h = np.array([1.0, 0.0, 0.0])
    side0 = _unit(np.cross([0.0, 0.0, 1.0], h))
    side1 = np.cross(axis, side0)
    lo = (side0 * math.cos(yaw - twist / 2) + side1 * math.sin(yaw - twist / 2)) * (W * foot_w / 2)
    hi = (side0 * math.cos(yaw + twist / 2) + side1 * math.sin(yaw + twist / 2)) * (W / 2)
    P = [foot - lo, foot + lo, foot + hi + axis * H, foot - hi + axis * H]
    C = []
    for q, o in zip(P, (occ[0], occ[0], occ[1], occ[1])):
        n = (q - centre) * np.array([1.0, 1.0, squash])
        n = _unit(n) + np.array([0.0, 0.0, up])
        C.append(_fol(n, o))
    kit.quad(P, [[u0, v0], [u1, v0], [u1, v1], [u0, v1]], C)


def form_of(key, forms):
    return forms[int(hfloat(key, "form") * len(forms)) % len(forms)]


def young_tree(kit, p, z, r, H, cb, species, sprite, key):
    """A young broadleaf garden tree (linden / maple / ash / chestnut / birch; r < 1.6 m, 3.2-6.4 m):
    a trunk that forks clearly BELOW the foliage into 2-3 crossed-strip 3D boughs (visible under the crown from
    every angle), carrying 5-6 irregular asymmetric foliage clumps (cropped crown sprites + accent clumps, no symmetric
    lollipop ball and no central pole). Four forms: `forked`, `lean`, `broad`, `tiered`."""
    p = np.asarray(p, float)
    form = form_of(key, YOUNG_FORMS)
    st = _SPECIES_YOUNG.get(species, _SPECIES_YOUNG["linden"])
    birch = species == "birch"
    hc = max(H - cb, 0.8)
    a0 = hfloat(key, "ty") * 6.2832
    bark = PK.SWATCH[st["bark"]]
    twig_uv = PK.SWATCH[st["twig"]]
    wm, hm = PK.SPRITE_M[sprite]
    tr = (0.044 + 0.012 * H) * (0.82 if birch else 1.0)
    lvl = 0.88 + 0.12 * hfloat(key, "tl")

    base_idx = len(kit.V)
    prev_uv1 = kit.uv1
    kit.uv1 = _tree_uv1(key)
    try:
        # ---- Trunk up to fork (below crown base so scaffold limbs are exposed underneath)
        fork_k = st["fork_k"] * (0.88 if form == "broad" else 1.0)
        z_fork = z + max(cb * fork_k, 0.90)
        jog = np.array([hfloat(key, "jlx") - 0.5, hfloat(key, "jly") - 0.5]) * (0.28 * r if form == "lean" else 0.16 * r)
        foot3 = np.array([p[0], p[1], z - 0.1])
        fork3 = np.array([p[0] + jog[0], p[1] + jog[1], z_fork])
        _stem(kit, foot3, fork3, tr, tr * 0.70, a0, uv=bark)

        # Heavy side offset gives every crown a distinct asymmetric centre of mass
        az_dom = a0 + hfloat(key, "da") * 2.0
        off = np.array([math.cos(az_dom), math.sin(az_dom)]) * r * (0.24 if form == "lean" else 0.14)
        centre = np.array([*(p + jog + off * 0.65), z + cb + hc * 0.42])
        r_env = r * 1.02

        # Optional curved leader for birch and tiered forms (higher branch tiers along the stem)
        has_leader = st["leader"] or form == "tiered"
        if has_leader:
            z_lead = z + cb + hc * (0.64 if birch else 0.48)
            lead_xy = fork3[:2] + off * (0.85 if birch else 0.65) + np.array([math.cos(az_dom + 1.2), math.sin(az_dom + 1.2)]) * 0.12 * r
            lead3 = np.array([lead_xy[0], lead_xy[1], z_lead])
            _stem(kit, fork3 - np.array([0.0, 0.0, 0.04]), lead3, tr * 0.65, tr * 0.25, a0 + 0.7, uv=bark)
        else:
            lead3 = fork3

        # ---- 3D crossed-strip scaffold boughs at irregular azimuths and staggered heights
        gaps = [0.0, 1.85 + 0.55 * hfloat(key, "ag", 0), 3.90 + 0.65 * hfloat(key, "ag", 1)]
        t_range = {"forked": (0.42, 0.68), "lean": (0.36, 0.72), "broad": (0.56, 0.84), "tiered": (0.38, 0.66)}[form]

        for i, dg in enumerate(gaps):
            az = a0 + dg + 0.25 * (hfloat(key, "ba", i) - 0.5)
            # Stagger branch start up the leader when present, or around the fork
            f_stem = (0.10 + 0.30 * i + 0.12 * hfloat(key, "bs", i)) if has_leader else (0.0 if i == 0 else 0.08 * hfloat(key, "bs", i))
            b_start = fork3 + (lead3 - fork3) * min(f_stem, 0.72) - np.array([0.0, 0.0, 0.04])
            tilt = t_range[0] + (t_range[1] - t_range[0]) * hfloat(key, "bt", i)
            if birch:
                tilt *= 0.68
            ax = _dir(az, tilt)
            reach = r * st["spread"] * (0.38 + 0.22 * hfloat(key, "br", i))
            if i == 0 and form == "lean":
                reach *= 1.15
            L = reach / max(math.sin(tilt), 0.35)
            max_z = z + cb + hc * (0.42 if i == 0 else 0.54)
            if b_start[2] + ax[2] * L > max_z:
                L = max((max_z - b_start[2]) / max(ax[2], 0.15), 0.25 * r)
            b_end = b_start + ax * L
            _strip(kit, b_start, b_end, tr * (0.58 if i == 0 else 0.48), tr * 0.20, a0 + i * 0.9, uv=twig_uv)

            # Foliage lobe starts on the mid-bough so the proximal bare limb shows below while avoiding floating gaps.
            # High twist (0.65-0.95 rad) keeps every quad 3D from all azimuths (no thin edge-on blades).
            v_lo = st["v_lo"][0] + (st["v_lo"][1] - st["v_lo"][0]) * hfloat(key, "vl", i)
            attach = 0.38 if i == 0 else (0.42 + 0.12 * hfloat(key, "at", i))
            f3 = b_start + ax * (L * attach)
            if i == 0:
                f3[2] = min(max(f3[2], z + cb + 0.02), z + cb + 0.14)
            else:
                f3[2] = max(f3[2], z + cb + hc * (0.04 + 0.10 * hfloat(key, "lh", i)))

            lobe_tilt = tilt * (0.34 if birch else 0.48) + 0.10 * (hfloat(key, "lt", i) - 0.4)
            ax_l = _dir(az + 0.18 * (hfloat(key, "la", i) - 0.5), lobe_tilt)
            top_frac = 0.72 + 0.24 * hfloat(key, "bl", i)
            if i == 1:
                top_frac = min(top_frac + 0.06, 1.00)
            elif i == 0 and form in ("forked", "broad"):
                top_frac *= 0.86
            Hc = max((z + cb + hc * top_frac - f3[2]) / max(ax_l[2], 0.45), 0.44 * hc)
            tip_r = math.hypot(*(f3[:2] + ax_l[:2] * Hc - p))
            Hc *= min(1.0, r_env * 0.88 / max(tip_r, 1e-6))
            asp = wm / (hm * (1.0 - v_lo))
            w_scale = (1.22 + 0.26 * hfloat(key, "bw", i)) * (1.18 if birch else 1.0)
            Wc = min(max(Hc * asp * w_scale, 1.08 * r), 1.44 * r_env)
            use_sp = sprite if (birch or i < 2 or hfloat(key, "sp", i) < 0.55) else "shrub_a"
            use_vlo = v_lo if use_sp == sprite else 0.0
            _clump(kit, f3, ax_l, 0.45 * (hfloat(key, "by", i) - 0.5), Wc, Hc, use_sp, centre,
                   occ=(min(lvl * (0.76 + 0.10 * hfloat(key, "bo", i)), 0.95), lvl * (0.94 + 0.06 * hfloat(key, "bp", i))),
                   flip=hfloat(key, "bf", i) < 0.5, v_lo=use_vlo,
                   twist=(0.65 + 0.30 * hfloat(key, "bx", i)) * (1 if i % 2 else -1),
                   foot_w=0.58 if use_sp == sprite else 0.62)

        # ---- 3 upper / offset crown clusters (always 3 upper + 3 lower = 6 lobes, rotated across lower ones)
        for j in range(3):
            az = az_dom + 1.05 * (j - 1) + 0.45 * (hfloat(key, "ua", j) - 0.5)
            d = np.array([math.cos(az), math.sin(az)])
            zb = z + cb + hc * (0.20 + 0.15 * hfloat(key, "us", j) + (0.06 * j if birch else 0.0))
            rad = r * (0.14 + 0.14 * hfloat(key, "ur", j)) * (0.75 if birch else 1.0)
            base_xy = (lead3[:2] if has_leader else fork3[:2]) + off * 0.32 + d * rad
            tilt_u = 0.06 + 0.18 * hfloat(key, "ut", j)
            ax_u = _dir(az + (math.pi if hfloat(key, "ui", j) < 0.5 else 0.0), tilt_u)
            top_z = z + H * (1.00 - 0.10 * j * hfloat(key, "uh", j))
            Hc = max((top_z - zb) / max(ax_u[2], 0.5), 0.38 * hc)
            use_sp = sprite if (birch or j == 0) else ("apple_b" if hfloat(key, "ua2", j) < 0.40 else "shrub_a")
            v_lo_u = st["v_lo"][0] if use_sp == sprite else (0.20 if use_sp == "apple_b" else 0.0)
            uw, uh = PK.SPRITE_M[use_sp]
            uasp = uw / (uh * (1.0 - v_lo_u))
            Wc = min(max(Hc * uasp * (1.16 + 0.24 * hfloat(key, "uw", j)), 1.02 * r), 1.44 * r_env)
            _clump(kit, np.array([base_xy[0], base_xy[1], zb]), ax_u,
                   0.75 + 0.50 * (hfloat(key, "uy", j) - 0.5) + (0.8 if j == 1 else 0.0),
                   Wc, Hc, use_sp, centre,
                   occ=(lvl * (0.82 + 0.08 * hfloat(key, "uo", j)), lvl),
                   flip=hfloat(key, "uf", j) < 0.5, v_lo=v_lo_u,
                   twist=(0.65 + 0.30 * hfloat(key, "ux", j)) * (1 if j % 2 else -1), foot_w=0.58)

        _tilt_tree(kit, base_idx, (p[0], p[1], z), key, max_deg=MAX_TILT_DEG)
    finally:
        kit.uv1 = prev_uv1
    return form


def orchard_tree(kit, p, z, h, key, r=None):
    """An orchard / garden tree (apple, plum, pear, cherry: 2.7-6.2 m). A short thick stem that forks low into 3-4
    staggered scaffold limbs (crossed tapered strips, seen from every side), on every limb a spray of twigs and leaves
    (`apple_*`), a dense clump at its end and a smaller one across it on the inner side (`shrub_a`), and an uneven
    top. No core. 40 / 50 triangles (3 / 4 limbs). Four forms: `open`, `flat`, `upright`, `leaning`."""
    p = np.asarray(p, float)
    R = float(r) if r is not None else h * (0.36 + 0.10 * hfloat(key, "fr"))
    R = min(max(R, 1.0), 0.62 * h)
    R_fol = max(R, 1.25)
    form = form_of(key, ORCHARD_FORMS)
    a0 = hfloat(key, "fy") * 6.2832
    lvl = 0.86 + 0.14 * hfloat(key, "fo")
    fork = h * ({"open": 0.24, "flat": 0.22, "upright": 0.28, "leaning": 0.25}[form] + 0.07 * hfloat(key, "ff"))
    zc0 = z + max(h - 1.9 * R, fork * 0.85)
    hc = z + h - zc0
    tr = 0.060 + 0.024 * h / 3.4
    lean = (np.array([hfloat(key, "flx"), hfloat(key, "fly")]) - 0.5) * (0.75 if form == "leaning" else 0.50)
    top2 = p + lean * fork / max(h, 1.0)
    foot3, fork3 = np.array([p[0], p[1], z - 0.1]), np.array([top2[0], top2[1], z + fork])

    base_idx = len(kit.V)
    prev_uv1 = kit.uv1
    kit.uv1 = _tree_uv1(key)
    try:
        _stem(kit, foot3, fork3, tr, tr * 0.78, a0)
        centre = np.array([*(top2 + lean * 0.35), zc0 + hc * 0.45])
        n_l = 4 if hfloat(key, "nl") < 0.55 else 3
        t_lo, t_hi = {"open": (0.68, 1.00), "flat": (0.88, 1.22), "upright": (0.44, 0.76), "leaning": (0.62, 1.06)}[form]
        spr = ("apple_a", "apple_b")
        s0 = int(hfloat(key, "fa") * 2)
        for i in range(n_l):
            az = a0 + 0.3 + 2 * math.pi * (i + 0.65 * (hfloat(key, "fl", i) - 0.5)) / n_l
            tilt = t_lo + (t_hi - t_lo) * hfloat(key, "ft", i)
            if form == "leaning" and i == 0:
                tilt += 0.18
            ax = _dir(az, tilt)
            reach = R * (0.52 + 0.24 * hfloat(key, "fd", i))
            L = reach / max(math.sin(tilt), 0.3)
            zmax = z + h - (0.38 if form == "upright" else 0.30) * hc
            if fork3[2] + ax[2] * L > zmax:
                L = max((zmax - fork3[2]) / max(ax[2], 0.2), 0.3 * R)
            limb_base = fork3 + np.array([0.0, 0.0, (-0.06 + 0.09 * hfloat(key, "fb", i)) * h])
            end = limb_base + ax * L
            _strip(kit, limb_base - np.array([0.0, 0.0, 0.05]), end, tr * 0.62, tr * 0.22, a0 + i)
            # spray: starts lower in `upright` so limbs aren't bare vertical poles
            sp_frac = (0.36 if form == "upright" else 0.48) + 0.14 * hfloat(key, "sp", i)
            f3 = limb_base + ax * (L * sp_frac)
            ax_s = _unit(ax * 0.42 + np.array([0.0, 0.0, 0.85]))
            Hs = min((z + h - f3[2]) / ax_s[2] * (0.78 + 0.20 * hfloat(key, "sh", i)), 1.25 * R_fol)
            wm, hm = PK.SPRITE_M[spr[(s0 + i) % 2]]
            Ws = min(Hs * wm / hm * (1.0 + 0.25 * hfloat(key, "sw", i)), 1.7 * R_fol)
            yaw = 0.7 * (hfloat(key, "sy", i) - 0.5)
            _clump(kit, f3, ax_s, yaw, Ws, Hs, spr[(s0 + i) % 2], centre, occ=(lvl * 0.84, lvl), flip=hfloat(key, "sf", i) < 0.5,
                   foot_w=0.30, twist=0.5)
            # dense clump at the limb's end
            Wk = R_fol * (1.02 + 0.32 * hfloat(key, "kw", i))
            Hk = Wk * 0.85 * (0.88 + 0.25 * hfloat(key, "kh", i))
            ax_k = _dir(az, 0.25 + 0.35 * hfloat(key, "kt", i))
            fk = end - ax_k * Hk * (0.30 + 0.12 * hfloat(key, "kd", i))
            fk[2] = max(fk[2], zc0 - 0.04 * hc)
            if fk[2] + ax_k[2] * Hk > z + h:
                Hk = (z + h - fk[2]) / ax_k[2]
            _clump(kit, fk, ax_k, 0.5 * (hfloat(key, "ky", i) - 0.5), Wk, Hk, "shrub_a", centre,
                   occ=(lvl * (0.82 + 0.10 * hfloat(key, "ko", i)), lvl), flip=hfloat(key, "kf", i) < 0.5, foot_w=0.55, twist=0.7)
            # second clump on the limb's inner side
            Wi = R_fol * (0.78 + 0.26 * hfloat(key, "iw", i))
            Hi = min(Wi * 0.85, (z + h - end[2]) + 0.35 * hc)
            fi = limb_base + ax * (L * 0.70) + np.array([0.0, 0.0, 0.02 * hc])
            _clump(kit, fi, _dir(az + 3.1416, 0.10 + 0.25 * hfloat(key, "it", i)), (1.1 if i % 2 else -1.1) + 0.4 * (hfloat(key, "iy", i) - 0.5),
                   Wi, Hi, "shrub_a", centre, occ=(lvl * 0.80, lvl * 0.97), flip=hfloat(key, "if", i) < 0.5, foot_w=0.55, twist=0.6)
        # top over the fork: two uneven cards, leaning to opposite sides
        zt0 = zc0 + hc * {"open": 0.42, "flat": 0.40, "upright": 0.32, "leaning": 0.36}[form]
        for j in range(2):
            az = a0 + 1.0 + j * (2.4 + 1.2 * hfloat(key, "ta")) + 0.3
            ax_t = _dir(az, 0.12 + 0.24 * hfloat(key, "tt", j))
            Ht = (z + h - zt0) / ax_t[2] * (1.0 if j == 0 else 0.78)
            Wt = min(R_fol * (1.22 - 0.24 * j) * (0.9 + 0.25 * hfloat(key, "tw", j)), Ht * 1.5)
            ft = np.array([*(centre[:2] + ax_t[:2] * 0.12 * R), zt0])
            _clump(kit, ft, ax_t, 0.2 + 1.3 * j + 0.4 * (hfloat(key, "tz", j) - 0.5), Wt, Ht, "shrub_a" if j == 0 else spr[s0], centre,
                   occ=(lvl * 0.86, lvl), flip=j == 1, foot_w=0.5)

        _tilt_tree(kit, base_idx, (p[0], p[1], z), key, max_deg=MAX_TILT_DEG)
    finally:
        kit.uv1 = prev_uv1
    return form
