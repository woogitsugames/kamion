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
from scipy import ndimage

from . import verge_atlas as VA

LAYER = "banks"
MAT = "verge_tufts"
MATERIALS = {MAT: {"color": [1.0, 1.0, 1.0], "rough": 0.9, "texture": MAT, "alpha_cutoff": 0.5,
                   "vertex_color": True, "shader": "Kamion/World PlotKit"}}
# r5 (fields3-s24, critic wave10-pre 1 / #7 "ten sam sprite w równym rytmie"): the r4 atlas had 16 tufts of ONE growth
# form and the cards stood at a stepped spacing along two lines (gravel edge, slope). Now:
#  - the atlas (streetscape.verge_atlas) holds 16 plants of different growth forms - grass tussocks, bleached stalks,
#    dock, tansy, yarrow, mugwort, chicory, rosettes, clover, flattened dead grass - plus the maize rows of ADR 0334 r3;
#  - a card maps ONE plant, picked by the zone (shoulder edge / slope / ditch bottom) from a weight table, with
#    COLONIES: a forb dominates a stretch of 10-40 m and is rare elsewhere (tansy and mugwort grow in stands);
#  - positions are a thinned Poisson process on the chainage (slots of SLOT_M, kept by a density that is the product
#    of two noises and falls to zero for metres: clusters and real gaps, no step, no restart per mesh station);
#  - shoulder-edge plants spread over a band (onto the gravel and, where the ground is known, up to EDGE_OUT_M
#    behind it) instead of one line; every card has its own scale (SCALE), width, turn and tone.
TEX_W, TEX_H = VA.TEX_W, VA.TEX_H
TEX_M = 4.0                      # metres of sward one texture width stands for
NT = VA.NT                       # plants per atlas row; a card maps one
V_SHORT = VA.V_SHORT             # atlas rows (v from the image bottom): shoulder-edge plants / tall plants
V_TALL = VA.V_TALL
V_PAD = 0.006
GRASS = ("tuft", "tuft_dry", "wisp", "flat_dead", "tussock", "tussock_dry", "stalks")
FORMS_EDGE = (("tuft", 0.34), ("tuft_dry", 0.16), ("rosette", 0.12), ("clover", 0.10), ("flat_dead", 0.10),
              ("wisp", 0.10), ("hawkbit", 0.04), ("yarrow_low", 0.04))
FORMS_SLOPE = (("tussock", 0.30), ("tussock_dry", 0.20), ("stalks", 0.18), ("mugwort", 0.09), ("dock", 0.07),
               ("tansy", 0.06), ("yarrow", 0.06), ("chicory", 0.04))
FORMS_BOTTOM = (("tussock", 0.45), ("stalks", 0.25), ("dock", 0.12), ("tussock_dry", 0.10), ("mugwort", 0.08))
FORMS_BAULK = (("tussock_dry", 0.26), ("tussock", 0.24), ("stalks", 0.22), ("mugwort", 0.12), ("tansy", 0.08),
               ("dock", 0.04), ("yarrow", 0.04))
FORM_H = {"clover": 0.55, "rosette": 0.8, "flat_dead": 0.5, "hawkbit": 0.9, "stalks": 1.25, "mugwort": 1.3,
          "tansy": 1.15, "dock": 1.1, "chicory": 1.2, "yarrow": 1.0}      # relative height of a form (grass = 1)
COLONY_M = 23.0                  # correlation length of the forb colonies along the road
COLONY_T = 0.55                  # colony noise above this = a stand of one forb
COLONY_BOOST = 10.0              # weight of the stand's forb inside it
FORB_OUTSIDE = 0.20              # weight factor of every forb outside its stands
SLOT_M = 0.15                    # candidate slots along the chainage
RATE_EDGE = 3.4                  # plants per metre where the density is 1 (mean density ~0.35)
RATE_SLOPE = 1.8 
RATE_BOTTOM = 2.3
DENS_M = (14.0, 47.0)            # the two noise periods of the density
DENS_T = (0.32, 0.70)            # smoothstep of the mixed noise: below = bare stretch
SCALE = (0.6, 1.4)               # per-card height scale
EDGE_OUT_M = 0.9                 # shoulder-edge plants up to this far behind the gravel (needs the ground height)
CROSS_SHARE = 0.25               # tall plants with a second card across the first (volume from the side)
TONE = (0.78, 1.04)              # per-card brightness (foliage occlusion scale)
H_EDGE = (0.14, 0.38)
H_SLOPE = (0.22, 0.50)
H_SLOPE_MAX = 0.75               # cap of a slope plant (scale x form)
H_BOTTOM = (0.45, 0.90)
W_CARD = (0.50, 0.95)
EDGE_REACH_M = 0.42              # how far a shoulder-edge tuft may stand on the gravel (from its outer edge)
PATCH_M = 14.0                   # correlation length of the density patches along the road
MIN_DITCH_M = 0.22               # shallower "ditches" (flat verges) get no tall bottom grass
SINK_M = 0.05                    # card foot below the surface
OCC = (0.76, 0.98)             # r4: 0.62 at the foot read as a dark clone on the lighter sward (critic build #8)
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


def _density(src, zone, sc):
    v = 0.6 * _vnoise(src + ":d1" + zone, sc, DENS_M[0]) + 0.4 * _vnoise(src + ":d2" + zone, sc, DENS_M[1])
    t = min(max((v - DENS_T[0]) / (DENS_T[1] - DENS_T[0]), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def pick_form(table, src, sc, u):
    """Growth form of a plant at chainage sc (u: its own uniform draw): the table weights, bent by the forb colonies."""
    w = [x for _, x in table]
    forbs = [i for i, (n, _) in enumerate(table) if n not in GRASS]
    if forbs:
        g = _vnoise(src + ":col", sc, COLONY_M)
        dom = forbs[int(_h(src, "colf", math.floor(sc / COLONY_M + 0.5)) * len(forbs)) % len(forbs)] if g > COLONY_T else -1
        w = [x * ((COLONY_BOOST if i == dom else FORB_OUTSIDE) if i in forbs else 1.0) for i, x in enumerate(w)]
    c, tot = 0.0, sum(w)
    for (n, _), x in zip(table, w):
        c += x
        if u * tot <= c:
            return n
    return table[-1][0]


def form_uv(form):
    """(u0, u1, v0, v1) of a growth form in the atlas."""
    if form in VA.SHORT_FORMS:
        k, vrow = VA.SHORT_FORMS.index(form), V_SHORT
    else:
        k, vrow = VA.TALL_FORMS.index(form), V_TALL
    return k / NT, (k + 1) / NT, vrow[0] + V_PAD, vrow[1] - V_PAD


# ------------------------------------------------------------------------------------------------ texture
def texture(seed=334):
    return VA.texture(seed)


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


def _card(sec, k, t, lat, ang, w, h, form, key, V, UV, C, T, zfn=None):
    """One vertical card centred at (k + t, lat), turned `ang` rad from the outward direction, w wide, h high; its
    two feet follow the cross-section - or, behind its outer edge, the ground zfn(e, n) (r5)."""
    a, o = sec.frame(k)
    ca, sa = math.cos(ang), math.sin(ang)
    umax = float(min(sec.u[k][-1], sec.u[k + 1][-1]))
    out = max(lat - umax, 0.0) if zfn is not None else 0.0
    ctr = sec.at(k, t, lat)
    cxy = ctr[:2] + o * out
    feet = []
    for sg in (-1.0, 1.0):
        xy = cxy + (o * ca + a * sa) * (sg * w / 2)
        if out > 0.0:
            z = float(zfn(xy[0], xy[1]))
        else:
            z = sec.at(k, t, lat + sg * ca * w / 2)[2]
        feet.append([xy[0], xy[1], z - SINK_M])
    lean = (o * (-sa) + a * ca) * (h * 0.18 * (2.0 * _h(*key, "ln") - 1.0))
    u0, u1, v0, v1 = form_uv(form)
    if _h(*key, "um") < 0.5:         # mirrored
        u0, u1 = u1, u0
    n0 = len(V)
    V += [feet[0], feet[1], [feet[0][0] + lean[0], feet[0][1] + lean[1], feet[0][2] + h + SINK_M],
          [feet[1][0] + lean[0], feet[1][1] + lean[1], feet[1][2] + h + SINK_M]]
    UV += [[u0, v0], [u1, v0], [u0, v1], [u1, v1]]
    nrm = (o[0] * 0.25, o[1] * 0.25, 1.0)
    tone = TONE[0] + (TONE[1] - TONE[0]) * _h(*key, "tn")
    C += [_fol(nrm, OCC[0] * tone)] * 2 + [_fol(nrm, OCC[1] * tone)] * 2
    T += [(n0, n0 + 1, n0 + 3), (n0, n0 + 3, n0 + 2)]


def _slots(ch0, ch1, src, zone):
    """Candidate positions (chainage, slot index) of one zone between two chainages: one jittered point per SLOT_M
    slot of the GLOBAL chainage - the scatter does not know the mesh stations."""
    q = int(math.floor(ch0 / SLOT_M))
    while q * SLOT_M < ch1:
        sc = (q + _h(src, zone, q, "j")) * SLOT_M
        if ch0 <= sc < ch1:
            yield sc, q
        q += 1


def _scale(key):
    """Per-card height scale SCALE[0] .. SCALE[1], most plants near 1."""
    u = _h(*key, "sc")
    return SCALE[0] + (SCALE[1] - SCALE[0]) * (0.5 + 0.5 * math.copysign(abs(2.0 * u - 1.0) ** 1.4, u - 0.5))


def _turn(key, spread):
    """Card turn from the outward direction: mostly across the road (the driver sees faces), any angle for the rest."""
    if _h(*key, "o") < 0.72:
        return (_h(*key, "a") - 0.5) * 2.0 * spread
    return _h(*key, "a") * math.pi


def build(buf, secs, report=None, layer=LAYER, zfn=None, keepout=None):
    """Grass / forb cards of every kerbless side strip (see the module docstring, 4.; scatter r5). zfn(e, n): terrain
    height - lets the shoulder-edge plants of a flat verge stand behind the gravel. keepout: shapely geometry (plan)
    where no card stands - the paved driveway crossings over the verge / ditch (axis-driveway-s24: tall forbs stood on
    the paving and read as sticks in the mirror). Returns the triangle count."""
    import shapely
    ntri = 0
    ncard = {"edge": 0, "slope": 0, "bottom": 0}
    skipped = 0
    if keepout is not None and not keepout.is_empty:
        shapely.prepare(keepout)
    else:
        keepout = None
    forms = {}
    for s in secs:
        X = s["X"]
        if len(X) < 2 or not s["seg"].any():
            continue
        sec = _Sec(X)
        V, UV, C, T = [], [], [], []
        src = s["src"]

        def put(zone, k, x, L, lat, ang, w, h, form, key):
            nonlocal skipped
            if keepout is not None:
                p_ = sec.at(k, x / L, lat)
                if shapely.intersects_xy(keepout, float(p_[0]), float(p_[1])):
                    skipped += 1
                    return
            _card(sec, k, x / L, lat, ang, w, h, form, key, V, UV, C, T, zfn=zfn)
            ncard[zone] += 1
            forms[form] = forms.get(form, 0) + 1
            if form in VA.TALL_FORMS and _h(*key, "x") < CROSS_SHARE:
                _card(sec, k, x / L, lat, ang + math.pi / 2 + (_h(*key, "b") - 0.5) * 0.8, w, h * 0.92, form,
                      key + ("x",), V, UV, C, T, zfn=zfn)
                ncard[zone] += 1

        for k in range(len(X) - 1):
            if not s["seg"][k]:
                continue
            ch0, ch1 = float(sec.ch[k]), float(sec.ch[k + 1])
            L = ch1 - ch0
            if L < 0.2:
                continue
            ug = float(min(sec.u[k][1], sec.u[k + 1][1]))               # gravel width
            # ---- shoulder edge: low plants in a band over the gravel edge
            if ug > 0.15:
                behind = EDGE_OUT_M if (zfn is not None or s["ditch"]) else 0.0
                if s["ditch"]:
                    behind = min(behind, max(float(min(sec.u[k][2], sec.u[k + 1][2])) - ug - 0.1, 0.0))
                for sc, q in _slots(ch0, ch1, src, "e"):
                    key = (src, "e", q)
                    dens = _density(src, "e", sc)
                    if _h(*key, "k") >= dens * RATE_EDGE * SLOT_M:
                        continue
                    reach = min(EDGE_REACH_M * (0.3 + 0.7 * _vnoise(src + ":r", sc, 6.0)), 0.6 * ug)
                    v = _h(*key, "l")
                    lat = ug - reach * (1.0 - v / 0.4) if v < 0.4 else ug + behind * ((v - 0.4) / 0.6) ** 1.3
                    form = pick_form(FORMS_EDGE, src, sc, _h(*key, "f"))
                    sc_ = _scale(key)
                    h = (H_EDGE[0] + (H_EDGE[1] - H_EDGE[0]) * _h(*key, "h") * (0.5 + 0.5 * dens)) * sc_ * FORM_H.get(form, 1.0)
                    h = min(max(h, H_EDGE[0]), H_EDGE[1] * 1.15)
                    w = (W_CARD[0] + (0.75 - W_CARD[0]) * _h(*key, "w")) * (0.8 + 0.25 * sc_)
                    put("edge", k, sc - ch0, L, lat, _turn(key, 1.1), w, h, form, key)
            if not s["ditch"]:
                continue
            ub0 = float(max(sec.u[k][2], sec.u[k + 1][2]))
            ub1 = float(min(sec.u[k][3], sec.u[k + 1][3]))
            uc = float(min(sec.u[k][4], sec.u[k + 1][4]))
            depth = float(min(X[k, 1, 2] - X[k, 2, 2], X[k + 1, 1, 2] - X[k + 1, 2, 2]))
            # ---- slopes: medium plants in groups, stands of forbs
            for sc, q in _slots(ch0, ch1, src, "s"):
                key = (src, "s", q)
                dens = _density(src, "s", sc)
                if _h(*key, "k") >= dens * RATE_SLOPE * SLOT_M:
                    continue
                front = _h(*key, "f") < 0.5
                lo, hi = (ug + 0.15, ub0) if front else (ub1, uc - 0.1)
                if hi - lo <= 0.25:
                    continue
                lat = lo + (hi - lo) * _h(*key, "l")
                form = pick_form(FORMS_SLOPE, src, sc, _h(*key, "fm"))
                sc_ = _scale(key)
                h = (H_SLOPE[0] + (H_SLOPE[1] - H_SLOPE[0]) * _h(*key, "h")) * sc_ * (0.85 + 0.4 * dens) * FORM_H.get(form, 1.0)
                h = min(max(h, H_SLOPE[0]), H_SLOPE_MAX)
                w = (W_CARD[0] + (W_CARD[1] - W_CARD[0]) * _h(*key, "w")) * (0.8 + 0.25 * sc_)
                put("slope", k, sc - ch0, L, lat, _turn(key, 0.8), w, h, form, key)
            # ---- bottom: tall grass / sedge / dock in the damp patches
            if depth < MIN_DITCH_M or not s["seg_bottom"][k] or ub1 - ub0 < 0.05:
                continue
            for sc, q in _slots(ch0, ch1, src, "b"):
                key = (src, "b", q)
                dens = 0.25 + 0.75 * _density(src, "b", sc)
                if _h(*key, "k") >= dens * RATE_BOTTOM * SLOT_M * 0.6:
                    continue
                lat = ub0 + (ub1 - ub0) * (0.2 + 0.6 * _h(*key, "l"))
                form = pick_form(FORMS_BOTTOM, src, sc, _h(*key, "fm"))
                h = (H_BOTTOM[0] + (H_BOTTOM[1] - H_BOTTOM[0]) * _h(*key, "h")) * (0.75 + 0.35 * dens)
                w = W_CARD[0] + (W_CARD[1] - W_CARD[0]) * _h(*key, "w")
                put("bottom", k, sc - ch0, L, lat, _turn(key, 0.45), w, h, form, key)
        if T:
            buf.add(layer, MAT, np.asarray(V), np.asarray(UV), np.asarray(T), src="verge_flora:" + src,
                    COL=np.asarray(C))
            ntri += len(T)
    if report is not None:
        report["verge_flora"] = {"sections": len(secs), "cards": ncard, "triangles": ntri, "keepout_skipped": skipped,
                                 "forms": dict(sorted(forms.items()))}
    return ntri
