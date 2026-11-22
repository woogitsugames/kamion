"""Roadside sward of kerbless (rural) road sides (ADR 0324; critic s24 wave 6 # 2.5, 3.3, 3.5).

What was there: the ground shoulder is a clean gravel strip with a ruler edge, the ditch one dark `verge_grass`
texture from the shoulder to the field (a different material than the meadow behind it: a straight tone step along the
ditch crown, ADR 0321 "otwarte"), no blade of grass standing anywhere.

What this module does (generator only, no shader change):
  1. sections(parts): finds every kerbless side strip in the road mesh buffer - the `shoulder_gravel` part and the
     `verge_grass` parts of the ditch that follow it (roads.network.side_profile RURAL: front slope, bottom, back
     slope) - and returns its cross-section per station.
  2. tag_for_terrain(): the ditch grass parts get the ":vg" source suffix, so build_world.merge_verge_into_terrain
     makes them part of the terrain primitives (ADR 0110 mechanism): the ditch is drawn by the terrain grass shader
     with the ground masks of its nodes - the same sward as the field, a soft transition, no material step.
  3. ditch_colours(): ground masks along the ditch bottom: damp, mossy-dark patches (G), bare wet soil spots (A), rank
     unmown grass on the slopes (B) - broken up by a smooth noise along the road, never one band.
  4. build(): standing grass as alpha-clip cards (material `verge_tufts`, Kamion/World PlotKit, layer `banks` = High
     content, chunk LOD0 / LOD1, no shadow): short tufts creeping from the ditch crown onto the gravel (the shoulder
     edge stops being a ruler line and its width varies), medium tufts on the slopes, tall grass / sedge 0.45-0.9 m in
     the damp bottom. Most cards stand ACROSS the road: a driver looks along the road and sees their faces.
All sizes and densities WORKING_VALUE (no survey; Mapillary DK65 / DW671 frames of Data/raw/mapillary viewed only).
Deterministic: every draw is a sha1 of the part source, the station and a salt.
"""
from __future__ import annotations

import hashlib
import io
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

LAYER = "banks"
MAT = "verge_tufts"
MATERIALS = {MAT: {"color": [1.0, 1.0, 1.0], "rough": 0.9, "texture": MAT, "alpha_cutoff": 0.5,
                   "vertex_color": True, "shader": "Kamion/World PlotKit"}}
TEX_W, TEX_H = 1024, 512
TEX_M = 2.0                      # metres of sward one texture width stands for
NT = 4                           # tufts per atlas row (r2); a card maps 1 or 2 whole tufts
TUFT_H = (1.0, 0.72, 0.9, 0.6)   # relative height of the tufts of a row
V_SHORT = (0.0, 0.5)             # atlas rows (v from the image bottom): short turf / tall grass with seed heads
V_TALL = (0.5, 1.0)
V_PAD = 0.012
STEP_EDGE_M = (0.40, 0.85)       # spacing of the shoulder-edge tufts along the road
STEP_SLOPE_M = (1.1, 2.6)
STEP_BOTTOM_M = (0.45, 0.95)
H_EDGE = (0.14, 0.38)
H_SLOPE = (0.22, 0.50)
H_BOTTOM = (0.45, 0.90)
W_CARD = (0.55, 1.10)
EDGE_REACH_M = 0.42              # how far a shoulder-edge tuft may stand on the gravel (from its outer edge)
PATCH_M = 14.0                   # correlation length of the density patches along the road
MIN_DITCH_M = 0.22               # shallower "ditches" (flat verges) get no tall bottom grass
SINK_M = 0.05                    # card foot below the surface
OCC = (0.62, 0.96)
NODE_R_M = 0.9                   # ground-mask nodes painted around the ditch bottom line


def _h(*key):
    return int(hashlib.sha1(":".join(str(k) for k in key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _vnoise(key, s, period):
    """Smooth value noise in 0..1 along a chainage (hash lattice, cosine interpolation)."""
    x = s / period
    i = math.floor(x)
    f = x - i
    f = 0.5 - 0.5 * math.cos(math.pi * f)
    return _h(key, "vn", i) * (1.0 - f) + _h(key, "vn", i + 1) * f


# ------------------------------------------------------------------------------------------------ texture
def texture(seed=324):
    S = 2
    W, H = TEX_W * S, TEX_H * S
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # sRGB, around the calibrated terrain grass (linear 0.08 / 0.105 / 0.038 = sRGB 80 / 91 / 55)
    greens = [np.array(c) for c in ((84, 98, 52), (72, 90, 50), (98, 106, 58), (66, 84, 46))]
    dry = np.array([142, 130, 86])
    dark = np.array([42, 52, 30])
    head = np.array([150, 138, 96])

    def col(c, k=None):
        k = rng.random() if k is None else k
        return tuple(int(x) for x in np.clip(c * (0.82 + 0.34 * k), 0, 255)) + (255,)

    def stroke(pts, w0, w1, c):
        for xo in (-W, 0, W):
            q = [(x + xo, y) for x, y in pts]
            for i in range(len(q) - 1):
                w = w0 + (w1 - w0) * i / max(len(q) - 2, 1)
                d.line([q[i], q[i + 1]], fill=c, width=max(1, int(round(w))))

    def blades(y_foot, row_h, n, hmin, hmax, w0, base_share, heads):
        # r2: NT discrete tufts per row with clear gaps between them - a card spans whole tufts (build: u on the
        # tuft grid), so its side edges lie in transparent texels and the silhouette is the tuft, not a rectangle
        cw = W / NT
        for _ in range(n):
            k = int(rng.integers(0, NT))
            off = float(np.clip(rng.normal(0, 0.14), -0.30, 0.30))          # foot offset in the cell (x cell width)
            x = (k + 0.5 + off) * cw
            env = max(0.25, 1.0 - (abs(off) / 0.32) ** 2 * 0.55) * TUFT_H[k % len(TUFT_H)]
            h = (hmin + (hmax - hmin) * rng.random() ** 1.6) * row_h * env
            lean = off * 1.6 + rng.normal(0, 0.10)                           # blades fan out of the tuft
            bend = rng.normal(0, 0.16)
            reach = abs(lean) * h + abs(bend) * h
            if abs(off) * cw + reach > 0.47 * cw:                             # keep the blade inside its cell
                sc = max(0.25, (0.47 * cw - abs(off) * cw) / max(reach, 1e-6))
                lean, bend = lean * sc, bend * sc
            c = dry if rng.random() < 0.10 else greens[int(rng.integers(0, len(greens)))]
            if rng.random() < base_share:
                c = dark * rng.uniform(0.9, 1.6)
            pts = [(x + (lean * t + bend * t * t) * h, y_foot - h * t) for t in np.linspace(0, 1, 7)]
            stroke(pts, w0 * S, 0.9 * S, col(c))
            if heads and h > 0.62 * row_h and rng.random() < heads:
                tx, ty = pts[-1]
                L = rng.uniform(0.06, 0.12) * row_h
                for q in range(14):                       # a loose panicle: short side strokes along the tip
                    t = q / 13.0
                    sx, sy = tx - (lean + 2 * bend) * L * t * 0.3, ty + L * t
                    a = rng.uniform(-1.0, 1.0)
                    stroke([(sx, sy), (sx + math.sin(a) * L * 0.22, sy - abs(math.cos(a)) * L * 0.10)],
                           2.2 * S, 1.0 * S, col(head))

    rh = H // 2
    # tall row: image rows 0 .. rh (v 0.5 .. 1), foot at y = rh
    blades(rh - 2, rh, 900, 0.06, 0.26, 4.5, 0.55, 0.0)
    blades(rh - 2, rh, 1100, 0.22, 0.70, 3.6, 0.12, 0.0)
    blades(rh - 2, rh, 520, 0.50, 0.99, 3.0, 0.03, 0.30)
    # short row: image rows rh .. H (v 0 .. 0.5), foot at y = H
    blades(H - 2, rh, 1100, 0.08, 0.34, 4.5, 0.45, 0.0)
    blades(H - 2, rh, 1100, 0.25, 0.75, 3.8, 0.10, 0.0)
    blades(H - 2, rh, 380, 0.55, 0.99, 3.0, 0.03, 0.06)
    im = im.resize((TEX_W, TEX_H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    m = a[..., 3] > 8
    a[~m, :3] = a[m][:, :3].mean(0)
    nz = ndimage.gaussian_filter(np.random.default_rng(seed + 1).random((TEX_H, TEX_W)), 0.8)
    a[..., :3] *= (0.88 + 0.24 * (nz - nz.min()) / max(float(nz.max() - nz.min()), 1e-6))[..., None]
    # the foot of each row is darker (inside the sward)
    y = np.arange(TEX_H)
    vrow = 1.0 - ((y % (TEX_H // 2)) + 0.5) / (TEX_H // 2)
    a[..., :3] *= (0.66 + 0.34 * np.clip(vrow / 0.5, 0, 1))[:, None, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def export_textures(tex_dir):
    tex_dir = Path(tex_dir)
    tex_dir.mkdir(parents=True, exist_ok=True)
    b = io.BytesIO()
    texture().save(b, format="PNG", optimize=False)
    p = tex_dir / f"{MAT}.png"
    if not p.exists() or p.read_bytes() != b.getvalue():
        p.write_bytes(b.getvalue())


# ------------------------------------------------------------------------------------------------ sections
def sections(parts):
    """Kerbless side strips of the road mesh: [{src, X (n, k, 3) cross-section points per station from the inner
    gravel edge outward, seg (n - 1,) bool: the strip is drawn between stations i and i + 1, ditch: bool,
    grass: [Part] the verge_grass parts of the ditch}]. X columns: 0 gravel inner, 1 gravel outer, then - with a
    ditch - 2 bottom inner, 3 bottom outer, 4 crown behind the ditch."""
    out = []
    n_parts = len(parts)
    for i, p in enumerate(parts):
        if p.layer != "road" or p.mat != "shoulder_gravel" or len(p.V) < 4 or len(p.V) % 2:
            continue
        n = len(p.V) // 2
        cols = [p.V[0::2], p.V[1::2]]
        grass = []
        for k in range(1, 4):
            if i + k >= n_parts:
                break
            q = parts[i + k]
            if q.layer != "road" or q.mat != "verge_grass" or q.src.split(":vg")[0] != p.src or len(q.V) != len(p.V):
                break
            cols.append(q.V[1::2])
            grass.append(q)
        # r3: the outer skirt / flange of the back slope (4th verge part of the strip) goes to the terrain with the
        # ditch - left as `verge_grass` it stayed a dark band behind the ditch crown (r2 bv_side_ditch)
        skirt = []
        if len(grass) == 3 and i + 4 < n_parts:
            q = parts[i + 4]
            if q.layer == "road" and q.mat == "verge_grass" and q.src.split(":vg")[0] == p.src and len(q.V) == len(p.V):
                skirt = [q]
        seg = np.zeros(max(n - 1, 0), bool)
        if len(p.T):
            seg[np.clip(np.asarray(p.T).min(1) // 2, 0, n - 2)] = True
        ditch = len(cols) == 5
        if ditch and len(grass[1].T):                    # the bottom must be drawn too
            sb = np.zeros(n - 1, bool)
            sb[np.clip(np.asarray(grass[1].T).min(1) // 2, 0, n - 2)] = True
            seg_b = sb
        else:
            seg_b = np.zeros(n - 1, bool)
        out.append({"src": p.src, "X": np.stack(cols, axis=1), "seg": seg, "seg_bottom": seg_b, "ditch": ditch,
                    "grass": (grass + skirt) if ditch else []})
    return out


def tag_for_terrain(secs):
    """The ditch grass parts become terrain (see the module docstring, 2.). Returns the number of parts tagged."""
    n = 0
    for s in secs:
        for q in s["grass"]:
            if not q.src.endswith(":vg"):
                q.src = q.src + ":vg"
                n += 1
    return n


def ditch_colours(col, hf, secs, report=None):
    """Ground masks (R road distance, G forest floor = dark damp litter / moss, B unmown, A bare soil) along the
    ditch bottoms. col: (H, W, 4) on the 1 m terrain grid of `hf`."""
    if col is None or not secs:
        return col
    c = np.array(col, dtype=np.float32, copy=True)
    H, W = c.shape[:2]
    damp = np.zeros((H, W), np.float32)
    soil = np.zeros((H, W), np.float32)
    rank = np.zeros((H, W), np.float32)
    npts = 0
    for s in secs:
        if not s["ditch"]:
            continue
        X = s["X"]
        depth = X[:, 1, 2] - X[:, 2, 2]
        mid = 0.5 * (X[:, 2, :2] + X[:, 3, :2])
        ch = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(mid, axis=0).T))])
        for k in range(len(mid) - 1):
            if not s["seg_bottom"][k] or min(depth[k], depth[k + 1]) < MIN_DITCH_M:
                continue
            L = max(float(ch[k + 1] - ch[k]), 1e-6)
            for t in np.arange(0.0, 1.0, min(1.0, 0.5 / L)):
                q = mid[k] * (1 - t) + mid[k + 1] * t
                sc = ch[k] + t * L
                dv = _vnoise(s["src"], sc, PATCH_M)
                sv = _vnoise(s["src"] + ":soil", sc, 5.0)
                i0, j0 = q[0] - hf.x0, hf.y1 - q[1]
                for dj in (-1, 0, 1):
                    for di in (-1, 0, 1):
                        i, j = int(round(i0)) + di, int(round(j0)) + dj
                        if not (0 <= i < W and 0 <= j < H):
                            continue
                        r = math.hypot(i - i0, j - j0)
                        if r > NODE_R_M + 0.6:
                            continue
                        w = max(0.0, 1.0 - r / (NODE_R_M + 0.6))
                        damp[j, i] = max(damp[j, i], w * (0.10 + 0.28 * max(0.0, dv - 0.25) / 0.75))
                        soil[j, i] = max(soil[j, i], w * (0.42 if sv > 0.72 else 0.0))
                        rank[j, i] = max(rank[j, i], w * 0.55)
                npts += 1
    damp = ndimage.gaussian_filter(damp, 0.8)        # r2: no per-node triangles of dark ground
    soil = ndimage.gaussian_filter(soil, 0.6)
    c[..., 1] = np.maximum(c[..., 1], damp)
    c[..., 3] = np.maximum(c[..., 3], soil)
    c[..., 2] = np.where(c[..., 2] <= 0.80, np.maximum(c[..., 2], rank * 0.9), c[..., 2])     # > 0.8 = field flag
    if report is not None:
        report["ditch_mask_samples"] = npts
    return c


# ------------------------------------------------------------------------------------------------ geometry
def _fol(nrm, occ):
    n = np.asarray(nrm, float)
    n = n / max(float(np.linalg.norm(n)), 1e-9) * min(max(float(occ), 0.05), 1.0)
    return [n[0] * 0.5 + 0.5, n[1] * 0.5 + 0.5, n[2] * 0.5 + 0.5, 1.0]


class _Sec:
    """Cross-section sampler of one strip: position at (station index + fraction, metres from the inner gravel edge)."""

    def __init__(self, X):
        self.X = X
        d = np.hypot(*np.diff(X[:, :, :2], axis=1).transpose(2, 0, 1))      # (n, k - 1) plan widths
        self.u = np.concatenate([np.zeros((len(X), 1)), np.cumsum(d, axis=1)], axis=1)
        mid = X[:, 1, :2]
        self.ch = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(mid, axis=0).T))])

    def at(self, k, t, lat):
        """Point at station k + t (0 <= t <= 1), `lat` metres from the inner gravel edge along the cross-section."""
        out = []
        for kk in (k, k + 1):
            u, X = self.u[kk], self.X[kk]
            lt = min(max(lat, 0.0), float(u[-1]))
            j = int(min(np.searchsorted(u, lt, side="right") - 1, len(u) - 2))
            w = (lt - u[j]) / max(float(u[j + 1] - u[j]), 1e-6)
            out.append(X[j] * (1 - w) + X[j + 1] * w)
        return out[0] * (1 - t) + out[1] * t

    def frame(self, k):
        """Unit (along, outward) plan vectors of segment k."""
        a = self.X[k + 1, 1, :2] - self.X[k, 1, :2]
        a = a / max(float(np.hypot(*a)), 1e-9)
        o = self.X[k, 1, :2] - self.X[k, 0, :2]
        if float(np.hypot(*o)) < 1e-6:
            o = np.array([a[1], -a[0]])
        o = o - a * float(o @ a)
        o = o / max(float(np.hypot(*o)), 1e-9)
        return a, o


def _card(sec, k, t, lat, ang, w, h, vrow, key, V, UV, C, T):
    """One vertical card centred at (k + t, lat), turned `ang` rad from the outward direction, w wide, h high; its
    two feet follow the cross-section."""
    a, o = sec.frame(k)
    ca, sa = math.cos(ang), math.sin(ang)
    ctr = sec.at(k, t, lat)
    feet = []
    for sg in (-1.0, 1.0):
        p = sec.at(k, t, lat + sg * ca * w / 2)
        xy = ctr[:2] + (o * ca + a * sa) * (sg * w / 2)
        feet.append([xy[0], xy[1], p[2] - SINK_M])
    lean = (o * (-sa) + a * ca) * (h * 0.18 * (2.0 * _h(*key, "ln") - 1.0))
    nt = 2 if w > 0.8 else 1
    u0 = int(_h(*key, "u") * NT) / NT
    if _h(*key, "um") < 0.5:         # mirrored
        u0, nt = u0 + nt / NT, -nt
    n0 = len(V)
    V += [feet[0], feet[1], [feet[0][0] + lean[0], feet[0][1] + lean[1], feet[0][2] + h + SINK_M],
          [feet[1][0] + lean[0], feet[1][1] + lean[1], feet[1][2] + h + SINK_M]]
    v0, v1 = vrow[0] + V_PAD, vrow[1] - V_PAD
    UV += [[u0, v0], [u0 + nt / NT, v0], [u0, v1], [u0 + nt / NT, v1]]
    nrm = (o[0] * 0.25, o[1] * 0.25, 1.0)
    C += [_fol(nrm, OCC[0])] * 2 + [_fol(nrm, OCC[1])] * 2
    T += [(n0, n0 + 1, n0 + 3), (n0, n0 + 3, n0 + 2)]


def build(buf, secs, report=None, layer=LAYER):
    """Grass cards of every kerbless side strip (see the module docstring, 4.). Returns the triangle count."""
    ntri = 0
    ncard = {"edge": 0, "slope": 0, "bottom": 0}
    for s in secs:
        X = s["X"]
        if len(X) < 2 or not s["seg"].any():
            continue
        sec = _Sec(X)
        V, UV, C, T = [], [], [], []
        src = s["src"]
        for k in range(len(X) - 1):
            if not s["seg"][k]:
                continue
            L = float(sec.ch[k + 1] - sec.ch[k])
            if L < 0.2:
                continue
            ug = float(min(sec.u[k][1], sec.u[k + 1][1]))               # gravel width
            # ---- shoulder edge: short tufts, patchy, some standing on the gravel
            x = _h(src, k, "e0") * STEP_EDGE_M[0]
            q = 0
            while x < L:
                key = (src, k, "e", q)
                sc = sec.ch[k] + x
                dens = _vnoise(src + ":e", sc, PATCH_M)
                if _h(*key, "k") < 0.30 + 0.65 * dens and ug > 0.15:
                    reach = EDGE_REACH_M * (0.3 + 0.7 * _vnoise(src + ":r", sc, 6.0))
                    lat = ug + (_h(*key, "l") ** 1.5) * 0.30 - _h(*key, "g") * min(reach, 0.6 * ug)
                    across = _h(*key, "o") < 0.88
                    ang = ((_h(*key, "a") - 0.5) * 1.1) if across else (math.pi / 2 + (_h(*key, "a") - 0.5) * 0.7)
                    w = W_CARD[0] + (W_CARD[1] - W_CARD[0]) * _h(*key, "w")
                    if across:
                        w = min(w, 0.8)
                    h = H_EDGE[0] + (H_EDGE[1] - H_EDGE[0]) * _h(*key, "h") * (0.5 + 0.5 * dens)
                    _card(sec, k, x / L, lat, ang, w, h, V_SHORT, key, V, UV, C, T)
                    ncard["edge"] += 1
                x += STEP_EDGE_M[0] + (STEP_EDGE_M[1] - STEP_EDGE_M[0]) * _h(*key, "s")
                q += 1
            if not s["ditch"]:
                continue
            ub0 = float(max(sec.u[k][2], sec.u[k + 1][2]))
            ub1 = float(min(sec.u[k][3], sec.u[k + 1][3]))
            uc = float(min(sec.u[k][4], sec.u[k + 1][4]))
            depth = float(min(X[k, 1, 2] - X[k, 2, 2], X[k + 1, 1, 2] - X[k + 1, 2, 2]))
            # ---- slopes: medium tufts, sparse
            x = _h(src, k, "s0") * STEP_SLOPE_M[0]
            q = 0
            while x < L:
                key = (src, k, "s", q)
                front = _h(*key, "f") < 0.5
                lo, hi = (ug + 0.15, ub0) if front else (ub1, uc - 0.1)
                if hi - lo > 0.25:
                    lat = lo + (hi - lo) * _h(*key, "l")
                    ang = (_h(*key, "a") - 0.5) * 1.6
                    h = H_SLOPE[0] + (H_SLOPE[1] - H_SLOPE[0]) * _h(*key, "h")
                    _card(sec, k, x / L, lat, ang, min(W_CARD[1], 0.9), h, V_TALL, key, V, UV, C, T)
                    ncard["slope"] += 1
                x += STEP_SLOPE_M[0] + (STEP_SLOPE_M[1] - STEP_SLOPE_M[0]) * _h(*key, "s")
                q += 1
            # ---- bottom: tall grass / sedge in the damp patches
            if depth < MIN_DITCH_M or not s["seg_bottom"][k] or ub1 - ub0 < 0.05:
                continue
            x = _h(src, k, "b0") * STEP_BOTTOM_M[0]
            q = 0
            while x < L:
                key = (src, k, "b", q)
                sc = sec.ch[k] + x
                dens = _vnoise(src, sc, PATCH_M)
                if _h(*key, "k") < 0.35 + 0.65 * dens:
                    lat = ub0 + (ub1 - ub0) * (0.2 + 0.6 * _h(*key, "l"))
                    h = (H_BOTTOM[0] + (H_BOTTOM[1] - H_BOTTOM[0]) * _h(*key, "h")) * (0.75 + 0.35 * dens)
                    w = W_CARD[0] + (W_CARD[1] - W_CARD[0]) * _h(*key, "w")
                    _card(sec, k, x / L, lat, (_h(*key, "a") - 0.5) * 0.9, w, h, V_TALL, key, V, UV, C, T)
                    ncard["bottom"] += 1
                    if _h(*key, "x") < 0.30:              # a second card along the ditch: volume from the side
                        _card(sec, k, x / L, lat, math.pi / 2 + (_h(*key, "b") - 0.5) * 0.8, w, h * 0.9, V_TALL,
                              key + ("x",), V, UV, C, T)
                        ncard["bottom"] += 1
                x += STEP_BOTTOM_M[0] + (STEP_BOTTOM_M[1] - STEP_BOTTOM_M[0]) * _h(*key, "s")
                q += 1
        if T:
            buf.add(layer, MAT, np.asarray(V), np.asarray(UV), np.asarray(T), src="verge_flora:" + src,
                    COL=np.asarray(C))
            ntri += len(T)
    if report is not None:
        report["verge_flora"] = {"sections": len(secs), "cards": ncard, "triangles": ntri}
    return ntri
