"""ADR 0352 addendum (garden-trees-s24): the small garden trees of the plot kit - a young broadleaf tree (crown radius
below plantings.LIB_MIN_R_M, 4-6.5 m) and the orchard tree (apple / plum / pear, 3.2-6 m) - as a stem, limbs and
CLUMPS of foliage on them, instead of whole-crown cards crossed on the axis.

Why (critic s24 build 10, ADR 0352 "Nie rozwiazane"): three whole-crown cards crossed on one axis are a ball on a stick
from every side, and in sunlight each card is lit by its OWN radial normal - the sector between two cards facing away
from the sun stood in the crown as a dark wedge with straight edges (and each card throws its shadow on the next along
the crossing line). The orchard tree had a dark 4-sided `_core` on top of that.

Here every foliage card is a branch of its own: it starts on the stem or on a limb, leans outward by its own angle,
and is turned about its own axis by its own yaw (some face outward, some stand edgewise like fins), so no two cards
share a line. All cards of one tree shade as ONE volume: the vertex normal is the direction from the crown's centre to
the vertex (flattened, biased upward) - never the card's own plane - and the occlusion (length of the normal) falls
towards the foot of the card, which sits inside the crown. No dark geometry anywhere.

Same material and atlas as the rest of the plot kit (crown cards of ADR 0352 with the species' blades for the broadleaf
trees, `apple_*` / `shrub_a` for the orchard tree): no new draw call, no new texture. Triangles: young tree 20-21
(was 14), orchard tree 40 / 50 (was 46). Shape, scale and proportions come from the tree's seed: three forms each.
All proportions are WORKING_VALUE (no survey of garden trees; refs: owner photos P05 / P08 / P12 in docs/05)."""
from __future__ import annotations

import math

import numpy as np

from . import plot_kit as PK
from .facade_kit import hfloat

YOUNG_H_MAX_M = 6.5           # garden_tree(): below this height the full variant is the clump tree
YOUNG_FORMS = ("vase", "lean", "broad")
ORCHARD_FORMS = ("open", "flat", "upright")
# v of the crown cards from which a branch card is cut: the lowest part of the card holds the painted stem only
_CARD_V0 = {"crown_ovoid": 0.0, "crown_round": 0.0, "crown_birch": 0.0}


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


def _bough(kit, a, b, w, uv=None):
    """A limb as ONE triangle: `w` of the stem at a (vertical base), the point at b. Stands in the vertical plane of
    the limb, so it reads as a tapering bough from the side and vanishes end-on, where the limb is foreshortened."""
    uv = uv or PK.SWATCH["trunk"]
    a, b = np.asarray(a, float), np.asarray(b, float)
    up = np.array([0.0, 0.0, w / 2])
    kit.tris([a - up, a + up, b], [uv] * 3, [(0, 1, 2)])


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


def _clump(kit, foot, axis, yaw, W, H, sprite, centre, occ=(0.78, 1.0), flip=False, v_lo=0.0, squash=0.6, up=0.45,
           twist=0.9, foot_w=0.34):
    """One foliage card as a branch: its foot (middle of the lower edge) at 3D `foot`, growing along unit `axis` for H,
    W wide at the tip. Two things keep it from being a paper rectangle:
    * the foot edge is only `foot_w` of W wide - the painted crown is squeezed towards the foot into the junction of a
      branch (no straight lower edge of foliage; the widest part of the clump moves up to the middle of the card);
    * the tip edge is turned about the axis by `twist` rad against the foot edge (yaw: 0 = facing away from the tree's
      axis, pi / 2 = edgewise): the two triangles of the quad lie in different planes, so no view sees the whole
      clump edge-on (a flat card seen edge-on stuck out of the crown as a dark blade - offline preview r1).
    Normals: from `centre` (the crown's centre) to each vertex, z * squash, + `up` - the whole crown shades as one
    volume whatever the card's plane. occ = (foot, tip)."""
    u0, u1, v0, v1 = PK.sprite(sprite)
    v0 = v0 + (v1 - v0) * v_lo
    if flip:
        u0, u1 = u1, u0
    foot, axis, centre = np.asarray(foot, float), _unit(axis), np.asarray(centre, float)
    h = np.array([axis[0], axis[1], 0.0])
    if np.linalg.norm(h) < 1e-3:
        h = np.array([1.0, 0.0, 0.0])
    side0 = _unit(np.cross([0.0, 0.0, 1.0], h))            # horizontal, across the lean: the card faces outward
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
    """A young broadleaf garden tree (linden / maple / ash / chestnut / birch; crown radius r < 1.6 m, H 4-6.5 m): a
    3-sided stem that runs into the crown, 3 lower lobes that start at the stem and lean OUTWARD (the bowl of the
    crown; each one a scaled crown card of the species - its painted limb is the branch), 2-3 upper lobes that stand
    further out between them and lean back INWARD (the dome), and three boughs from the stem into the lower lobes.
    Every lobe faces away from the axis (+- its own yaw and twist), so none is seen flat-on as a blade by a viewer on
    the ground, and none crosses another on the axis. 19-21 triangles. Forms by seed: `vase` (upswept lower lobes
    carry most of the crown), `lean` (the crown's mass off the stem, one heavy lobe), `broad` (low wide lobes, flat
    top)."""
    p = np.asarray(p, float)
    form = form_of(key, YOUNG_FORMS)
    birch = species == "birch"
    hc = H - cb
    a0 = hfloat(key, "ty") * 6.2832
    bark = PK.SWATCH["concrete" if birch else "trunk"]
    wm, hm = PK.SPRITE_M[sprite]
    v_lo = _CARD_V0[sprite]
    asp = wm / (hm * (1.0 - v_lo))
    lean = (np.array([hfloat(key, "tlx"), hfloat(key, "tly")]) - 0.5) * (0.10 if form == "lean" else 0.05) * H
    foot3 = np.array([p[0], p[1], z - 0.1])
    zt = z + cb + hc * {"vase": 0.40, "lean": 0.36, "broad": 0.30}[form]       # the stem ends this far up the crown
    top3 = np.array([*(p + lean * (zt - z) / H), zt])
    tr = (0.040 + 0.012 * H) * (0.8 if birch else 1.0)
    _stem(kit, foot3, top3, tr, tr * 0.55, a0, uv=bark)
    stem_at = lambda zz: foot3 + (top3 - foot3) * ((min(zz, zt) - foot3[2]) / (top3[2] - foot3[2]))   # noqa: E731
    off = np.zeros(2)
    if form == "lean":                                       # the crown's mass sits off the stem
        az_l = hfloat(key, "la") * 6.2832
        off = np.array([math.cos(az_l), math.sin(az_l)]) * 0.18 * r
    centre = np.array([*(p + lean * 0.6 + off), z + cb + hc * 0.50])
    lvl = 0.90 + 0.10 * hfloat(key, "tl")
    r_env = r * 1.06
    slim = 0.72 if birch else 1.0
    n_up = 3
    n_bough = 3 if hfloat(key, "nb") < 0.6 else 2
    # ---- lower lobes: from the stem outward
    t_lo, t_hi = {"vase": (0.06, 0.22), "lean": (0.04, 0.30), "broad": (0.20, 0.42)}[form]
    k_h = {"vase": (0.74, 0.92), "lean": (0.62, 0.90), "broad": (0.52, 0.70)}[form]
    boughs = []
    for i in range(3):
        az = a0 + 2 * math.pi * (i + 0.5 * (hfloat(key, "ba", i) - 0.5)) / 3
        zb = z + cb + hc * (-0.08 + 0.26 * ((i + hfloat(key, "bs", i)) / 3))
        rho = r * (0.38 + 0.18 * hfloat(key, "br", i)) * slim
        tilt = (t_lo + (t_hi - t_lo) * hfloat(key, "bt", i)) * slim
        if form == "lean":                                   # the lobe on the heavy side reaches further
            tilt *= 1.0 + 0.35 * max(float(np.dot([math.cos(az), math.sin(az)], off)) / (0.18 * r), 0.0)
        ax = _dir(az, tilt)
        Hc = (z + cb + hc * (k_h[0] + (k_h[1] - k_h[0]) * hfloat(key, "bl", i)) - zb) / ax[2]
        f3 = stem_at(zb) + np.array([*(ax[:2] / max(np.linalg.norm(ax[:2]), 1e-6) * rho + off * 0.6), 0.0])
        f3[2] = zb
        # the lobe's tip stays inside the crown radius the orthophoto shows
        tip = math.hypot(*(f3[:2] + ax[:2] * Hc - p))
        Hc *= min(1.0, r_env * 0.96 / max(tip, 1e-6))
        Wc = min(max(Hc * asp * (1.15 + 0.30 * hfloat(key, "bw", i)), 1.05 * r), 1.45 * r_env) * slim
        _clump(kit, f3, ax, 0.5 * (hfloat(key, "by", i) - 0.5), Wc, Hc, sprite, centre,
               occ=(min(lvl * (0.80 + 0.10 * hfloat(key, "bo", i)) * (1.1 if birch else 1.0), 0.97), lvl * (0.94 + 0.06 * hfloat(key, "bp", i))),
               flip=hfloat(key, "bf", i) < 0.5, v_lo=v_lo, twist=(0.45 + 0.35 * hfloat(key, "bx", i)) * (1 if hfloat(key, "bz", i) < 0.5 else -1), foot_w=0.6)
        boughs.append((stem_at(max(zb - 0.16 * hc - 0.5 * rho, z + cb * 0.6)), f3 + ax * Hc * 0.30))
    # ---- upper lobes: between the lower ones, further out, leaning back over the stem
    for j in range(n_up):
        az = a0 + math.pi / 3 + 2 * math.pi * (j + 0.5 * (hfloat(key, "ua", j) - 0.5)) / n_up 
        d = np.array([math.cos(az), math.sin(az)])
        zb = z + cb + hc * ({"vase": 0.34, "lean": 0.28, "broad": 0.24}[form] + 0.16 * hfloat(key, "us", j))
        rad = r * (0.22 + 0.16 * hfloat(key, "ur", j)) * slim * (1.3 if form == "broad" else 1.0)
        tilt = -(0.18 + 0.30 * hfloat(key, "ut", j)) * (1.25 if form == "broad" else 1.0)
        ax = _dir(az, tilt)
        Hc = (z + H * (1.0 - 0.07 * hfloat(key, "uh", j) * (1 + j)) - zb) / ax[2]
        Wc = min(Hc * asp * (1.15 + 0.30 * hfloat(key, "uw", j)) * (1.25 if form == "broad" else 1.0), 1.6 * r_env) * slim
        f3 = np.array([*(top3[:2] + off + d * rad), zb])
        _clump(kit, f3, ax, 0.6 * (hfloat(key, "uy", j) - 0.5), Wc, Hc, sprite, centre,
               occ=(lvl * (0.84 + 0.08 * hfloat(key, "uo", j)), lvl), flip=hfloat(key, "uf", j) < 0.5, v_lo=v_lo,
               twist=(0.4 + 0.3 * hfloat(key, "ux", j)) * (1 if j % 2 else -1), foot_w=0.62)
    for a, b in boughs[:n_bough]:
        _bough(kit, a, b, tr * 1.5, uv=bark)
    return form


def orchard_tree(kit, p, z, h, key, r=None):
    """An orchard / garden tree (apple, plum, pear, cherry: 3.2-6 m). A short thick stem that forks low into 3-4
    scaffold limbs (crossed tapered strips, seen from every side), on every limb a spray of twigs and leaves (`apple_*`
    card whose painted twig fan starts on the limb), a dense clump at its end and a smaller one across it on the inner
    side (`shrub_a`), and a looser top over the fork. No core. 40 / 50 triangles (3 / 4 limbs; was 46). Forms by seed: `open` (open-centre, wide limbs - the pruned apple), `flat`
    (low, wider than tall, limbs near the horizontal - an old plum), `upright` (pear: steep limbs, taller top)."""
    p = np.asarray(p, float)
    R = float(r) if r is not None else h * (0.36 + 0.10 * hfloat(key, "fr"))
    R = min(max(R, 1.0), 0.62 * h)
    form = form_of(key, ORCHARD_FORMS)
    a0 = hfloat(key, "fy") * 6.2832
    lvl = 0.86 + 0.14 * hfloat(key, "fo")
    fork = h * ({"open": 0.24, "flat": 0.22, "upright": 0.28}[form] + 0.07 * hfloat(key, "ff"))
    zc0 = z + max(h - 1.9 * R, fork * 0.85)                  # underside of the crown
    hc = z + h - zc0
    tr = 0.060 + 0.024 * h / 3.4
    lean = (np.array([hfloat(key, "flx"), hfloat(key, "fly")]) - 0.5) * 0.5
    top2 = p + lean * fork / max(h, 1.0)
    foot3, fork3 = np.array([p[0], p[1], z - 0.1]), np.array([top2[0], top2[1], z + fork])
    _stem(kit, foot3, fork3, tr, tr * 0.78, a0)
    centre = np.array([*(top2 + lean * 0.3), zc0 + hc * 0.45])
    n_l = 4 if hfloat(key, "nl") < 0.55 else 3
    t_lo, t_hi = {"open": (0.70, 1.00), "flat": (0.90, 1.22), "upright": (0.40, 0.70)}[form]
    spr = ("apple_a", "apple_b")
    s0 = int(hfloat(key, "fa") * 2)
    for i in range(n_l):
        az = a0 + 0.3 + 2 * math.pi * (i + 0.55 * (hfloat(key, "fl", i) - 0.5)) / n_l
        tilt = t_lo + (t_hi - t_lo) * hfloat(key, "ft", i)
        ax = _dir(az, tilt)
        reach = R * (0.52 + 0.20 * hfloat(key, "fd", i))     # horizontal reach of the limb's end
        L = reach / max(math.sin(tilt), 0.3)
        zmax = z + h - 0.30 * hc
        if fork3[2] + ax[2] * L > zmax:
            L = (zmax - fork3[2]) / ax[2]
        end = fork3 + ax * L
        _strip(kit, fork3 - np.array([0.0, 0.0, 0.06]), end, tr * 0.62, tr * 0.22, a0 + i)
        # spray: its twig fan starts on the limb at 0.45 of its length; the card rises steeper than the limb and is
        # turned edgewise-ish (the fan of twigs is seen from the side, like the limb's own branching)
        f3 = fork3 + ax * L * (0.48 + 0.14 * hfloat(key, "sp", i))
        ax_s = _unit(ax * 0.40 + np.array([0.0, 0.0, 0.85]))
        Hs = min((z + h - f3[2]) / ax_s[2] * (0.80 + 0.18 * hfloat(key, "sh", i)), 1.25 * R)
        wm, hm = PK.SPRITE_M[spr[(s0 + i) % 2]]
        Ws = min(Hs * wm / hm * (1.0 + 0.25 * hfloat(key, "sw", i)), 1.7 * R)
        yaw = 0.7 * (hfloat(key, "sy", i) - 0.5)
        _clump(kit, f3, ax_s, yaw, Ws, Hs, spr[(s0 + i) % 2], centre, occ=(lvl * 0.84, lvl), flip=hfloat(key, "sf", i) < 0.5,
               foot_w=0.30, twist=0.5)
        # dense clump at the limb's end, facing outward, hanging a little below the limb
        Wk = R * (1.05 + 0.30 * hfloat(key, "kw", i))
        Hk = Wk * 0.85 * (0.9 + 0.25 * hfloat(key, "kh", i))
        ax_k = _dir(az, 0.25 + 0.35 * hfloat(key, "kt", i))
        fk = end - ax_k * Hk * (0.30 + 0.12 * hfloat(key, "kd", i))
        fk[2] = max(fk[2], zc0 - 0.04 * hc)
        if fk[2] + ax_k[2] * Hk > z + h:
            Hk = (z + h - fk[2]) / ax_k[2]
        _clump(kit, fk, ax_k, 0.5 * (hfloat(key, "ky", i) - 0.5), Wk, Hk, "shrub_a", centre,
               occ=(lvl * (0.82 + 0.10 * hfloat(key, "ko", i)), lvl), flip=hfloat(key, "kf", i) < 0.5, foot_w=0.55, twist=0.7)
        # a second, smaller clump on the limb's inner side, turned across the first one: the limb keeps its volume
        # from the views in which the spray and the end clump are seen edgewise
        Wi = R * (0.80 + 0.25 * hfloat(key, "iw", i))
        Hi = min(Wi * 0.85, (z + h - end[2]) + 0.35 * hc)
        fi = fork3 + ax * L * 0.72 + np.array([0.0, 0.0, 0.02 * hc])
        _clump(kit, fi, _dir(az + 3.1416, 0.10 + 0.25 * hfloat(key, "it", i)), (1.1 if i % 2 else -1.1) + 0.4 * (hfloat(key, "iy", i) - 0.5),
               Wi, Hi, "shrub_a", centre, occ=(lvl * 0.80, lvl * 0.97), flip=hfloat(key, "if", i) < 0.5, foot_w=0.55, twist=0.6)
    # the top over the fork: two cards of different size, yawed apart, leaning to opposite sides
    zt0 = zc0 + hc * {"open": 0.42, "flat": 0.40, "upright": 0.30}[form]
    for j in range(2):
        az = a0 + 1.0 + j * (2.4 + 1.2 * hfloat(key, "ta")) + 0.3
        ax_t = _dir(az, 0.12 + 0.22 * hfloat(key, "tt", j))
        Ht = (z + h - zt0) / ax_t[2] * (1.0 if j == 0 else 0.84)
        Wt = min(R * (1.25 - 0.25 * j) * (0.9 + 0.25 * hfloat(key, "tw", j)), Ht * 1.5)
        ft = np.array([*(centre[:2] + ax_t[:2] * 0.10 * R), zt0])
        _clump(kit, ft, ax_t, 0.2 + 1.3 * j + 0.4 * (hfloat(key, "tz", j) - 0.5), Wt, Ht, "shrub_a" if j == 0 else spr[s0], centre,
               occ=(lvl * 0.86, lvl), flip=j == 1, foot_w=0.5)
    return form
