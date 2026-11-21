"""Bank vegetation geometry of the opt-in water stage (ADR 0213): reed / tall-herb belt ribbons and willow / alder
shrub instances along the shore, placed from Data/Regions/<id>/water_banks.json (streetscape.water_banks, orthophoto).

Reed belt. Common reed (Phragmites australis), reed canary grass, sedges and nettle stand along the Supraśl / Biała in a
belt 2-25 m wide (orthophoto 2024-05-27). Built as ROWS of alpha-clip ribbons that follow the shore (not crossed
cards per tuft): a ribbon is 2 triangles per SEG_M along the bank, with a zig-zag in plan (volume from oblique views)
and a height noise along it; the texture (`water_reeds`, drawn here, no photo) tiles in u and carries the ragged top,
the stems and leaves and a few panicles. Row 0 stands just inside the water line (its foot hidden by the opaque sheet),
the rows behind it are lower (sedge / tall herbs). High: up to ROWS_HIGH rows, Low / Medium: ROWS_LOW rows with
twice the segment length - same rows, fewer triangles. Material `water_reeds` (Kamion/World PlotKit: two-sided foliage
lit by COLOR_0 normals, occlusion at the foot). Layer `banks` / `banks_low`: chunk LOD0 / LOD1 only, no shadows.

Shrubs. Woody crowns of the orthophoto within 18 m of the water (outside forests) -> instances of the existing
procedural prototypes: crowns r < 2.2 m -> `tree_shrub` (grey / purple willow scrub, 2-4 m), larger -> `tree_alder`
(black alder: the riparian tree of the Podlasie lowland rivers). Never closer than 2.5 m to a tree the region already
has, never on a road / building / paved keep-out. Seeded per position (sha1), so nothing else in the region shifts.
All dimensions WORKING_VALUE (no field survey; orthophoto + general botany of Podlasie river valleys).
"""
from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter as ndimage_gauss

TEX_W, TEX_H = 1024, 512           # final texture px (u tiles)
TEX_M = 4.0                        # metres of bank one texture width stands for
SEG_M = 2.0                        # ribbon segment along the bank (High); Low: 2 x
ROWS_HIGH = 4
ROWS_LOW = 2
ROW_GAP_M = 1.5                    # distance between rows (outward)
ROW0_D_M = -0.35                   # row 0 stands in the water margin (foot under the sheet)
HEIGHT_M = (2.2, 2.1, 1.7, 1.4)       # mean top height of row 0 / 1 / 2+ (reed at the water, sedge / herbs behind)
ZIGZAG_M = 0.28
LEAN_M = 0.12
CROSS_DEG = 40.0                   # High: crossed cards at +-40 deg to the bank, CARD_W wide, one pair per sample
CARD_W = 2.6
EDGE_H = 0.75                      # r6/r7: height of a card's side edges (x its middle height)
V_TOP = 0.94                       # r7: every card / ribbon top maps to the texture top - the outline is the ragged
                                   # alpha (opaque coverage 1.0 below v 0.45, 0.5 at v 0.72, 0.1 at v 0.88), never
                                   # the polygon edge (r6: top v = h / 2.5 cut through the opaque part -> solid
                                   # tents on High, solid green triangles on Low)
H_GEOM = 1.35                      # polygon height / nominal plant height (the 50 % coverage line sits at ~h)
ZIGZAG_LOW_M = 0.9                 # Low: one continuous ribbon per stretch, deep zig-zag (volume without clumps)
END_H_LOW = 0.5                    # Low: ribbon height at a stretch end (x)
PIECE_N = (2, 5)                   # clump length in samples (x SEG_M), r4
GAP_P = 0.20                       # chance of a one-sample gap after a clump (r5: clumps mostly overlap)
PIECE_OFF_M = 0.6                  # clump offset from its row (+-)
OCC = (0.55, 0.90)                 # foliage occlusion at the foot / top of a ribbon (PlotKit: albedo factor)
SHRUB_MAX_R = 2.2
# ADR 0321 (High cards, WORKING_VALUE): clump density 0.55-1.0 of the samples, pair moved +-0.9 m along / +-0.5 m across,
# card width 0.6-1.15 x CARD_W, the pair turned freely (second card 70-110 deg to the first)
JIT_ALONG_M = 0.9
JIT_ACROSS_M = 0.5
CARD_W_VAR = (0.6, 1.15)
ZZ_AMP_LOW = (0.35, 1.0)           # Low: zig-zag amplitude per sample x ZIGZAG_LOW_M (was a constant: regular teeth)
TREE_KEEP_M = 2.5
# ADR 0324 (High, WORKING_VALUE): a belt is a dense stand of CLUMPS, not one crossed pair per 2 m sample (critic s24
# wave 6 # 3.1: "scattered brown crosses / matches"). CLUMPS_PER_SEG clumps per SEG_M sample of a row, each a star of
# CLUMP_CARDS cards CLUMP_W wide (wider than the clump spacing: neighbours interlock into one mass), every card leaning
# up to CLUMP_LEAN_DEG off the vertical (seen from above a leaning card shows its face, a vertical one is a line).
# Common reed in July-August stands 1.5-2.5 m (rows 0-1: REED_H clamp; sedge / tall herbs behind: HERB_H).
CLUMPS_PER_SEG = 2
CLUMP_CARDS = (3, 3, 2, 2)         # cards per clump of row 0 / 1 / 2 / 3
CLUMP_W = (1.5, 2.3)
CLUMP_LEAN_DEG = 11.0
CLUMP_DENS = (0.82, 1.0)
REED_H = (1.5, 2.5)
HERB_H = (0.9, 1.9)


def _h(*key):
    return int(hashlib.sha1(":".join(str(k) for k in key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


# ------------------------------------------------------------------------------------------------ texture
def texture(seed=213):
    """RGBA sRGB, TEX_W x TEX_H, tiles in u; v = 0 at the image bottom is the foot of the belt."""
    S = 2
    W, H = TEX_W * S, TEX_H * S
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    px_m = W / TEX_M
    # palette (sRGB): fresh reed leaf, blue-green reed, olive sedge, last year's straw stems, dark base, panicle
    # r4: darker, greyer (a reed bed seen from 20-200 m is olive-grey, never lime: orthophoto belt ~95/105/80)
    # ADR 0324: July stand (Commons Tykocin_Most_drogowy_01 / 05: green-fawn wall with purple-brown panicles) -
    # greener leaf than the r4 olive-grey, last year's straw only as a minor share
    fresh = np.array([86, 112, 50])
    blue = np.array([78, 102, 64])
    olive = np.array([104, 112, 58])
    straw = np.array([156, 144, 100])
    dark = np.array([40, 50, 28])
    pan = np.array([122, 94, 82])

    def col(c, k):
        c = np.clip(c * (0.85 + 0.3 * k), 0, 255)
        return tuple(int(x) for x in c) + (255,)

    def stroke(pts, w0, w1, c):
        for x_off in (-W, 0, W):
            q = [(x + x_off, y) for x, y in pts]
            n = len(q)
            for i in range(n - 1):
                w = w0 + (w1 - w0) * i / max(n - 2, 1)
                d.line([q[i], q[i + 1]], fill=c, width=max(1, int(round(w))))

    # dense dark base (litter, stems in shade): the belt reads as a mass, not single blades
    for _ in range(1400):
        x = rng.uniform(0, W)
        h = rng.uniform(0.10, 0.40) * H
        lean = rng.normal(0, 0.12)
        pts = [(x + lean * h * t * t, H - h * t) for t in np.linspace(0, 1, 6)]
        stroke(pts, 6 * S, 1.5 * S, col(dark * rng.uniform(0.8, 1.5), rng.random()))
    # stems with leaves
    for k in range(700):
        x = rng.uniform(0, W)
        tall = rng.random()
        h = (0.30 + 0.68 * tall ** 1.3) * H          # ragged top: few stems reach the full height
        lean = rng.normal(0, 0.07)
        dry = rng.random() < 0.10
        base = straw if dry else (fresh, blue, olive)[int(rng.integers(0, 3))]
        c = col(base, rng.random())
        pts = [(x + lean * h * t * t, H - h * t) for t in np.linspace(0, 1, 8)]
        stroke(pts, 3.0 * S, 1.1 * S, c)
        if not dry:
            # leaves: broad blades leaving the stem upward, arching and drooping (Phragmites), 3-7 per stem
            for j in range(int(rng.integers(3, 8))):
                t0 = rng.uniform(0.15, 0.9)
                x0, y0 = x + lean * h * t0 * t0, H - h * t0
                side = rng.choice([-1, 1])
                L = rng.uniform(0.12, 0.34) * H
                ang = math.radians(rng.uniform(20, 65))
                droop = rng.uniform(0.3, 1.2)
                lp = []
                for t in np.linspace(0, 1, 8):
                    lp.append((x0 + side * math.sin(ang) * L * t,
                               y0 - math.cos(ang) * L * t + droop * L * t * t))
                stroke(lp, 4.5 * S, 1.0 * S, col(base * rng.uniform(0.8, 1.15), rng.random()))
        if (not dry and tall > 0.62 and rng.random() < 0.42) or (dry and tall > 0.4 and rng.random() < 0.45):
            # panicle: a narrow plume hanging to one side from the stem top (purple-brown; old ones grey-straw)
            tx, ty = pts[-1]
            pc = straw * 1.05 if dry else pan
            side = rng.choice([-1, 1])
            Lp = rng.uniform(0.07, 0.13) * H
            for q in range(34):
                t = q / 33.0
                sx, sy = tx + side * 0.25 * Lp * t, ty + 0.85 * Lp * t                 # rachis bending down
                a = side * rng.uniform(0.2, 1.1)
                Ls = rng.uniform(0.15, 0.35) * Lp * (1.0 - 0.6 * t)
                stroke([(sx, sy), (sx + math.sin(a) * Ls, sy + math.cos(a) * Ls * 0.6)],
                       1.8 * S, 0.8 * S, col(pc * rng.uniform(0.8, 1.15), rng.random()))
    im = im.resize((TEX_W, TEX_H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    # premultiplied-style edge fix: transparent texels take the mean colour of the belt (no dark fringe in mips)
    m = a[..., 3] > 8
    mean = a[m][:, :3].mean(0)
    a[~m, :3] = mean
    # texel-scale value noise (leaf sheen / spots): the flat drawn strokes must not read as vector art
    nz = ndimage_gauss(np.random.default_rng(seed + 1).random((TEX_H, TEX_W)), 0.8)
    a[..., :3] *= (0.86 + 0.28 * (nz - nz.min()) / max(float(nz.max() - nz.min()), 1e-6))[..., None]
    # vertical darkening toward the foot (inside the belt), ~0.6 at v = 0
    v = 1.0 - (np.arange(TEX_H) + 0.5) / TEX_H
    a[..., :3] *= (0.62 + 0.38 * np.clip(v / 0.55, 0, 1))[:, None, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def textures():
    return {"water_reeds": texture()}


# ------------------------------------------------------------------------------------------------ geometry
def _fol(nrm, occ):
    n = np.asarray(nrm, float)
    n = n / max(float(np.linalg.norm(n)), 1e-9) * min(max(float(occ), 0.05), 1.0)
    return [n[0] * 0.5 + 0.5, n[1] * 0.5 + 0.5, n[2] * 0.5 + 0.5, 1.0]


def _runs(doc):
    for r in doc.get("runs", []):
        a = np.asarray(r, float).reshape(-1, 5)
        if len(a) >= 3:
            yield a


def build(buf, doc, zground, zlevel, keep_out, rep, layer="banks", low=False):
    """Reed ribbons of every belt run. zground(e, n) / zlevel(e, n): terrain and water level (nan off the water);
    keep_out: shapely geometry (roads / paved / buildings) no ribbon vertex may enter."""
    import shapely
    rows_max = ROWS_LOW if low else ROWS_HIGH
    step = 2 if low else 1                       # doc samples are SEG_M apart; Low takes every second one
    shapely.prepare(keep_out)
    ntri = 0
    nrib = 0
    for ri, a in enumerate(_runs(doc)):
        a = a[::step] if len(a[::step]) >= 2 else a
        P, Nm, wd = a[:, :2], a[:, 2:4], a[:, 4]
        T_ = np.gradient(P, axis=0)
        T_ /= np.maximum(np.linalg.norm(T_, axis=1, keepdims=True), 1e-9)
        key0 = f"{P[0, 0]:.1f}:{P[0, 1]:.1f}"
        for row in range(rows_max):
            dist = ROW0_D_M + row * ROW_GAP_M
            on = wd >= dist + 0.8 if row else wd >= 1.5
            if on.sum() < 2:
                continue
            # contiguous stretches of this row
            idx = np.nonzero(on)[0]
            splits = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
            for sp0 in splits:
                if len(sp0) < 2:
                    continue
                # r4: a belt is a chain of clumps, not a hedge: pieces of PIECE_N samples with small gaps, each with
                # its own offset from the shore and height (the rows no longer read as parallel walls)
                pieces, a_ = [], 0
                while a_ < len(sp0) - 1:
                    ln = int(PIECE_N[0] + _h(key0, row, int(sp0[a_]), "pl") * (PIECE_N[1] - PIECE_N[0] + 1))
                    if low:
                        ln = len(sp0)                  # r7: Low = one ribbon per stretch (2-3 sample clumps tapering
                                                       # to nothing were 8-12 m triangles)
                    b_ = min(a_ + ln, len(sp0) - 1)
                    pieces.append(sp0[a_:b_ + 1])
                    a_ = b_ + (1 if _h(key0, row, int(sp0[a_]), "gap") < GAP_P else 0)
                for pi_, sp in enumerate(pieces):
                    if len(sp) < 2:
                        continue
                    pk = (key0, row, int(sp[0]))
                    k = np.arange(len(sp))
                    jit = np.array([_h(key0, row, int(i), "z") for i in sp]) - 0.5
                    amp = np.array([ZZ_AMP_LOW[0] + (ZZ_AMP_LOW[1] - ZZ_AMP_LOW[0]) * _h(key0, row, int(i), "za") for i in sp])                         if low else 1.0
                    zz = np.where((k + row) % 2 == 0, 1.0, -1.0) * amp * (ZIGZAG_LOW_M if low else ZIGZAG_M) + jit * 0.25 + (_h(*pk, "off") - 0.5) * 2 * PIECE_OFF_M
                    Q = P[sp] + Nm[sp] * (dist + zz)[:, None] + T_[sp] * ((np.array([_h(key0, row, int(i), "t") for i in sp]) - 0.5) * 0.4)[:, None]
                    inside = shapely.contains_xy(keep_out, Q[:, 0], Q[:, 1])
                    if inside.all():
                        continue
                    hm = HEIGHT_M[min(row, len(HEIGHT_M) - 1)] * (0.75 + 0.45 * _h(*pk, "ph"))
                    hn = np.array([_h(key0, row, int(i), "h") for i in sp])
                    h = hm * (0.70 + 0.45 * hn)            # r5: ragged top along the clump (max ~1.4 x row height)
                    h[0] *= END_H_LOW if low else 0.15  # High: a clump thins out at both ends (cards: min 0.6 hm)
                    h[-1] *= END_H_LOW if low else 0.15
                    h[inside] = 0.0
                    # r5: a run on a shore that the sheet covers (OSM channel buffers, islands): water 2 m out AND
                    # 2 m in -> no reed standing in open water
                    wet = np.isfinite(np.asarray(zlevel(*(Q + Nm[sp] * 2.0).T), float)) &                         np.isfinite(np.asarray(zlevel(*(Q - Nm[sp] * 2.0).T), float))
                    h[wet] = 0.0
                    zg = np.asarray(zground(Q[:, 0], Q[:, 1]), float)
                    zl = np.asarray(zlevel(Q[:, 0], Q[:, 1]), float)
                    foot = np.where(np.isfinite(zl) & (zg < zl - 0.25), zl - 0.25, zg) - 0.12
                    top = foot + h * H_GEOM
                    lean = -Nm[sp] * LEAN_M * (1.0 if row == 0 else -0.5)       # row 0 leans over the water
                    nrm = np.column_stack([-Nm[sp] * 0.6, np.full(len(sp), 0.6)])
                    s_ = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
                    u = _h(*pk, "u") + s_ / TEX_M
                    if not low:
                        # ADR 0324 (High): dense interlocking clumps (see CLUMPS_PER_SEG); r5-r7 / ADR 0321 stood one
                        # crossed pair per sample = single crosses from above and from the bridge deck
                        Vc, UVc, Cc, Tc = [], [], [], []
                        dens = CLUMP_DENS[0] + (CLUMP_DENS[1] - CLUMP_DENS[0]) * _h(*pk, "dn")
                        ncard = CLUMP_CARDS[min(row, len(CLUMP_CARDS) - 1)]
                        hlo, hhi = REED_H if row < 2 else HERB_H
                        tanl = math.tan(math.radians(CLUMP_LEAN_DEG))
                        for i_ in range(len(sp)):
                            j_ = min(i_ + 1, len(sp) - 1)
                            for sub in range(CLUMPS_PER_SEG if j_ > i_ else 1):
                                f_ = sub / CLUMPS_PER_SEG
                                hh = h[i_] * (1.0 - f_) + h[j_] * f_
                                if h[i_] <= 0.0 or (sub and h[j_] <= 0.0):     # keep-out / open-water samples
                                    continue
                                kk = (key0, row, int(sp[i_]), sub)
                                if _h(*kk, "sk") > dens:
                                    continue
                                t_, nn_ = T_[sp[i_]], Nm[sp[i_]]
                                M0 = (Q[i_] * (1.0 - f_) + Q[j_] * f_ + t_ * (_h(*kk, "ja") - 0.5) * 0.7
                                      + nn_ * (_h(*kk, "jc") - 0.5) * 2 * JIT_ACROSS_M)
                                if shapely.contains_xy(keep_out, M0[0], M0[1]):
                                    continue
                                zg0 = float(np.asarray(zground(M0[0:1], M0[1:2]), float).ravel()[0])
                                zl0 = float(np.asarray(zlevel(M0[0:1], M0[1:2]), float).ravel()[0])
                                ft = (zl0 - 0.25 if (math.isfinite(zl0) and zg0 < zl0 - 0.25) else zg0) - 0.12
                                hc = float(np.clip(max(hh, 0.7 * hm), hlo, hhi)) * H_GEOM
                                a0 = _h(*kk, "a0") * math.pi
                                for c_ in range(ncard):
                                    ang = a0 + c_ * math.pi / ncard + (_h(*kk, "aj", c_) - 0.5) * 0.5
                                    cw = CLUMP_W[0] + (CLUMP_W[1] - CLUMP_W[0]) * _h(*kk, "cw", c_)
                                    dv = np.array([math.cos(ang), math.sin(ang)])
                                    pv = np.array([-dv[1], dv[0]])
                                    ctr = M0 + pv * (_h(*kk, "co", c_) - 0.5) * 0.5
                                    A, B = ctr - dv * (cw / 2), ctr + dv * (cw / 2)
                                    hk = hc * (0.82 + 0.30 * _h(*kk, "ch", c_))
                                    ln_ = pv * (hk * tanl * (2.0 * _h(*kk, "cl", c_) - 1.0)) + lean[i_]
                                    if shapely.contains_xy(keep_out, [A[0], B[0], A[0] + ln_[0], B[0] + ln_[0]],
                                                           [A[1], B[1], A[1] + ln_[1], B[1] + ln_[1]]).any():
                                        continue
                                    u0 = _h(*kk, "cu", c_)
                                    n0 = len(Vc)
                                    Vc += [[*A, ft], [*B, ft], [*(A + ln_), ft + hk], [*(B + ln_), ft + hk]]
                                    UVc += [[u0, 0.0], [u0 + cw / TEX_M, 0.0], [u0, V_TOP], [u0 + cw / TEX_M, V_TOP]]
                                    Cc += [_fol(nrm[i_], OCC[0])] * 2 + [_fol(nrm[i_], OCC[1])] * 2
                                    Tc += [(n0, n0 + 1, n0 + 3), (n0, n0 + 3, n0 + 2)]
                        if Tc:
                            buf.add(layer, "water_reeds", np.asarray(Vc), np.asarray(UVc), np.asarray(Tc),
                                    src=f"water:reeds:{ri}:{row}:{pi_}", COL=np.asarray(Cc))
                            ntri += len(Tc)
                            nrib += 1
                        continue
                    V = np.zeros((2 * len(sp), 3))
                    V[0::2, :2], V[0::2, 2] = Q, foot
                    V[1::2, :2], V[1::2, 2] = Q + lean, top
                    UV = np.zeros((2 * len(sp), 2))
                    UV[0::2, 0] = UV[1::2, 0] = u
                    UV[0::2, 1] = 0.0
                    UV[1::2, 1] = V_TOP                           # r7: the whole texture height on every ribbon
                    C = np.zeros((2 * len(sp), 4))
                    for i_ in range(len(sp)):
                        C[2 * i_] = _fol(nrm[i_], OCC[0])
                        C[2 * i_ + 1] = _fol(nrm[i_], OCC[1])
                    Tr = []
                    for i_ in range(len(sp) - 1):
                        if h[i_] <= 0 and h[i_ + 1] <= 0:
                            continue
                        a2, b2, c2, d2 = 2 * i_, 2 * i_ + 2, 2 * i_ + 3, 2 * i_ + 1
                        Tr += [(a2, b2, c2), (a2, c2, d2)]
                    if not Tr:
                        continue
                    buf.add(layer, "water_reeds", V, UV, np.asarray(Tr), src=f"water:reeds:{ri}:{row}:{pi_}", COL=C)
                    ntri += len(Tr)
                    nrib += 1
    rep[layer] = {"ribbons": nrib, "triangles": ntri}
    return ntri


def shrubs(doc, zground, trees, blocked_fn, rep):
    """Willow scrub / alder instances from the bank crowns (see the module docstring)."""
    out = []
    have = np.array([[t["e"], t["n"]] for t in trees]) if trees else np.zeros((0, 2))
    from scipy.spatial import cKDTree
    kd = cKDTree(have) if len(have) else None
    skipped = {"near_tree": 0, "blocked": 0}
    for e, n, r in doc.get("crowns", []):
        if kd is not None and kd.query([e, n])[0] < TREE_KEEP_M:
            skipped["near_tree"] += 1
            continue
        if blocked_fn(e, n):
            skipped["blocked"] += 1
            continue
        key = f"{e:.2f}:{n:.2f}"
        if r < SHRUB_MAX_R:
            p, h = "tree_shrub", float(np.clip(1.6 * r + 0.8 + 0.8 * _h(key, "h"), 2.0, 4.5))
        else:
            p, h = "tree_alder", float(np.clip(3.2 * r + 2.0 * _h(key, "h"), 8.0, 16.0))
        z = float(np.asarray(zground(np.array([e]), np.array([n]))).ravel()[0])
        out.append({"p": p, "v": int(_h(key, "v") * 3) % 3, "e": round(float(e), 2), "n": round(float(n), 2),
                    "z": round(z, 2), "h": round(h, 1), "yaw": round(_h(key, "y") * 6.2832, 3),
                    "lean": round(_h(key, "l") * 0.06, 3), "src": "water_banks:crown"})
    rep["bank_shrubs"] = {"tree_shrub": sum(1 for t in out if t["p"] == "tree_shrub"),
                          "tree_alder": sum(1 for t in out if t["p"] == "tree_alder"), "skipped": skipped}
    return out
