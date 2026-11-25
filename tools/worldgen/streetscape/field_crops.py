"""ADR 0334 r3 (fields3-s24, critic s24 wave10-pre 1): crops and baulks that STAND - maize rows and baulk sward as cards.

What was there: every use of the field mosaic is a colour of the terrain shader. Fodder maize in mid-August is 2-2.5 m
tall - a dark green flat patch is not maize ("kukurydzy w rzędach nie widać"), and a baulk 1-2.6 m wide seen across
from the cab is a hair line that the pixel footprint dissolves 40 m out ("pola bez miedz").

What this module does (generator only; material `verge_tufts` of streetscape.verge_flora / verge_atlas - the roadside
cards' material and atlas, layer `banks` = High content of chunk LOD0 / LOD1, no shadow caster, no new material):
  maize   every MAIZE_CARD_ROWS-th row of a maize strip (rows of 0.75 m at the shader's row coordinate, so a card
          stands ON a drawn row) is a run of 3.2 m cards 2.05-2.4 m high, staggered from row to row, plus short cross
          cards between two card rows (they close the corridors seen end-on). From the cab (eye 2.5 m) the first
          rows are a wall of leaves and the next ones show their tassel tops - a canopy; from above the rows read.
          Only within MAIZE_ROAD_RANGE_M of a road (the flat colour is enough beyond; bounds the triangle count).
  baulks  tall grass / stalks / mugwort / tansy cards (the TALL atlas row) along the strip seams that carry a baulk
          (the shader's hasBaulk) and along the block borders, in clumps with gaps (two EPSG:2180 noises), within
          BAULK_ROAD_RANGE_M of a road. Seen across from the cab a baulk is now a low ragged line of sward.
Placement is a pure function of the EPSG:2180 layout (vegetation.field_layout) and the terrain farmland flag, so two
tiles agree at their seam. All sizes and densities WORKING_VALUE.
"""
from __future__ import annotations

import numpy as np

from . import paved as PV
from . import vegetation as VG
from . import verge_atlas as VA
from . import verge_flora as VF

LAYER = VF.LAYER
MAT = VF.MAT
MAIZE_ROW_M = 0.75               # the shader's row period (KamionFieldMosaic: KFBand(rc + 0.375, 0.75, ...))
MAIZE_CARD_ROWS = 3              # a card row every 3rd crop row (2.25 m)
MAIZE_CARD_L = 2 * VA.MAIZE_CELL_M
MAIZE_H = (2.05, 2.40)           # WORKING_VALUE: fodder maize in mid-August, Podlasie
MAIZE_SINK_M = 0.10
MAIZE_ROAD_RANGE_M = 300.0
MAIZE_SEAM_CLEAR_M = 1.6         # off the strip seam (baulk half-width <= 1.3 m + the thinning crop)
MAIZE_BLOCK_CLEAR_M = 2.8        # off the block border (grass strip / field track)
MAIZE_ROAD_CLEAR_M = 5.0
MAIZE_CROSS_SHARE = 0.34         # row cards with a cross card towards the next card row
MAIZE_ZIGZAG_M = 0.40            # card ends this far off the row line, alternately: no card is edge-on to a view along
                                 # the rows (render review r3: from 14 m up the edge-on rows vanished and only the
                                 # cross cards showed - a hedge maze)
MAIZE_OCC = (0.50, 1.0)          # foot (deep in the crop) .. top
BAULK_ROAD_RANGE_M = 110.0
BAULK_BAND_M = 0.5               # candidates this far from the seam line
BAULK_RATE = 1.6                 # plants per metre of baulk where the density is 1
BAULK_BORDER_M = (1.4, 2.2)      # block border: the outer part of its grass strip (clear of a field track's ruts)
BAULK_BORDER_RATE = 0.9
BAULK_DENS_M = (13.0, 41.0)
BAULK_DENS_T = (0.34, 0.66)
BAULK_H = (0.45, 0.95)
BAULK_COLONY_M = 30.0
BAULK_CROSS_SHARE = 0.30
ARABLE_B = 0.985                 # terrain COLOR_0.b at / above this = inside an arable field (flag 1.00)


def _fol(n, occ):
    """PlotKit foliage vertex colours: rgb = unit normal x occlusion x 0.5 + 0.5, a = 1. n (N, 3), occ (N,)."""
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9) * np.clip(occ, 0.05, 1.0)[:, None]
    return np.column_stack([n * 0.5 + 0.5, np.ones(len(n))])


def _quads(A, B, h, lean, uv, nrm, occ0, occ1):
    """Vertical cards from foot points A to B (N, 3), height h (N,), top shifted by lean (N, 2); uv (N, 4) =
    (u0, u1, v0, v1). Returns V (4N, 3), UV (4N, 2), C (4N, 4), T (2N, 3)."""
    n = len(A)
    top = np.column_stack([lean, h])
    V = np.stack([A, B, A + top, B + top], axis=1).reshape(-1, 3)
    UV = np.stack([uv[:, [0, 2]], uv[:, [1, 2]], uv[:, [0, 3]], uv[:, [1, 3]]], axis=1).reshape(-1, 2)
    c0, c1 = _fol(nrm, occ0), _fol(nrm, occ1)
    C = np.stack([c0, c0, c1, c1], axis=1).reshape(-1, 4)
    i = np.arange(n)[:, None] * 4
    T = np.concatenate([i + np.array([0, 1, 3]), i + np.array([0, 3, 2])])
    return V, UV, C, T


class _Ground:
    def __init__(self, col, hf, zc, dist_road, blocked):
        self.b = np.asarray(col)[..., 2]
        self.hf, self.zc, self.dist, self.blocked = hf, zc, dist_road, blocked
        self.H, self.W = self.b.shape

    def ij(self, P):
        i = np.rint(P[:, 0] - self.hf.x0).astype(int)
        j = np.rint(self.hf.y1 - P[:, 1]).astype(int)
        ok = (i >= 1) & (i < self.W - 1) & (j >= 1) & (j < self.H - 1)
        return np.clip(i, 0, self.W - 1), np.clip(j, 0, self.H - 1), ok

    def arable(self, P, road_clear, road_range):
        i, j, ok = self.ij(P)
        ok &= self.b[j, i] >= ARABLE_B
        ok &= (self.dist[j, i] > road_clear) & (self.dist[j, i] < road_range)
        if self.blocked is not None:
            ok &= ~self.blocked[j, i]
        return ok

    def z(self, P):
        return PV.bilinear(self.zc, self.hf, P[:, 0], P[:, 1])


def _row_point(L0, rowc, s, ox, oy):
    """Region-local point at row coordinate rowc (m across the rows, shader `rowc`) and s metres along, in the block
    frame of the representative layout rows L0 (th, sx, sy arrays): fixed point of the wobble (rows are unwarped)."""
    c, sn = np.cos(L0["th"]), np.sin(L0["th"])
    x, y = L0["sx"] + rowc * c - s * sn, L0["sy"] + rowc * sn + s * c
    for _ in range(6):
        d = rowc - VG.field_wobble(x, y)
        x, y = L0["sx"] + d * c - s * sn, L0["sy"] + d * sn + s * c
    return np.column_stack([x - ox, y - oy])


def _maize(g, origin, rep):
    ox, oy = origin
    step = 3.0
    gx, gy = np.meshgrid(np.arange(g.hf.x0 + 1.0, g.hf.x0 + g.W - 1.0, step), np.arange(g.hf.y1 - g.H + 2.0, g.hf.y1 - 1.0, step))
    P = np.column_stack([gx.ravel(), gy.ravel()])
    P = P[g.arable(P, MAIZE_ROAD_CLEAR_M, MAIZE_ROAD_RANGE_M)]
    out = []
    n_row = n_cross = 0
    if not len(P):
        return out, n_row, n_cross
    L = VG.field_layout(P[:, 0] + ox, P[:, 1] + oy)
    mz = VG.field_use(L, True) == VG.FIELD_USES.index("maize")
    if not mz.any():
        return out, n_row, n_cross
    P = P[mz]
    L = {k: v[mz] for k, v in L.items()}
    c, sn = np.cos(L["th"]), np.sin(L["th"])
    rx, ry = P[:, 0] + ox - L["sx"], P[:, 1] + oy - L["sy"]
    rowc = rx * c + ry * sn + L["wob"]
    along = -rx * sn + ry * c
    pitch = MAIZE_ROW_M * MAIZE_CARD_ROWS
    m_idx, s_idx, rep_i = [], [], []
    for fid in np.unique(L["fid"]):
        q = np.nonzero(L["fid"] == fid)[0]
        m0, m1 = int(np.floor(rowc[q].min() / pitch)) - 1, int(np.ceil(rowc[q].max() / pitch)) + 1
        j0 = int(np.floor(along[q].min() / MAIZE_CARD_L)) - 1
        j1 = int(np.ceil(along[q].max() / MAIZE_CARD_L)) + 1
        mm, jj = np.meshgrid(np.arange(m0, m1 + 1), np.arange(j0, j1 + 1))
        m_idx.append(mm.ravel())
        s_idx.append(jj.ravel())
        rep_i.append(np.full(mm.size, q[0]))
    m_idx, s_idx, rep_i = np.concatenate(m_idx), np.concatenate(s_idx), np.concatenate(rep_i)
    L0 = {k: L[k][rep_i] for k in ("th", "sx", "sy")}
    fid0, bid0 = L["fid"][rep_i], L["bid"][rep_i].astype(np.float64)
    key_a = bid0 * 8191.0 + m_idx
    stag = VG._u01(VG._h32(key_a, np.zeros(len(key_a)), 1041))          # rows are staggered
    rc = m_idx * pitch
    sc = (s_idx + stag) * MAIZE_CARD_L

    def valid(Q):
        ok = g.arable(Q, MAIZE_ROAD_CLEAR_M, MAIZE_ROAD_RANGE_M + 2 * MAIZE_CARD_L)
        Lq = VG.field_layout(Q[:, 0] + ox, Q[:, 1] + oy)
        ok &= Lq["fid"] == fid0
        ok &= np.minimum(Lq["across"], Lq["w"] - Lq["across"]) > MAIZE_SEAM_CLEAR_M
        ok &= Lq["block_edge"] > MAIZE_BLOCK_CLEAR_M
        return ok, Lq

    zz = np.where((s_idx + m_idx) % 2 == 0, MAIZE_ZIGZAG_M, -MAIZE_ZIGZAG_M)
    half = float(np.sqrt((0.5 * MAIZE_CARD_L) ** 2 - MAIZE_ZIGZAG_M ** 2))
    A = _row_point(L0, rc - zz, sc - half, ox, oy)
    B = _row_point(L0, rc + zz, sc + half, ox, oy)
    okA, LA = valid(A)
    okB, LB = valid(B)
    ok = okA & okB
    hk = VG._h32(key_a, s_idx.astype(np.float64), 1043)
    u1, u2, u3, u4 = (VG._u01(VG._h32(hk.astype(np.float64), np.full(len(hk), float(q)), 1045)) for q in range(4))
    dirv = np.column_stack([np.cos(L0["th"]), np.sin(L0["th"])])

    def emit(A_, B_, sel, cells, tag):
        n = int(sel.sum())
        if not n:
            return 0
        a3 = np.column_stack([A_[sel], g.z(A_[sel]) - MAIZE_SINK_M])
        b3 = np.column_stack([B_[sel], g.z(B_[sel]) - MAIZE_SINK_M])
        h = MAIZE_H[0] + (MAIZE_H[1] - MAIZE_H[0]) * u1[sel] + MAIZE_SINK_M
        lean = dirv[sel] * ((u2[sel] - 0.5) * 0.22)[:, None]
        c0 = np.floor(u3[sel] * (VA.N_MAIZE - cells + 1)) / VA.N_MAIZE
        ua, ub = c0, c0 + cells / VA.N_MAIZE
        flip = u4[sel] < 0.5
        uv = np.column_stack([np.where(flip, ub, ua), np.where(flip, ua, ub),
                              np.full(n, VA.V_MAIZE[0] + 0.004), np.full(n, VA.V_MAIZE[1] - 0.004)])
        nrm = np.column_stack([dirv[sel] * (np.where(flip, -0.3, 0.3))[:, None], np.ones(n)])
        tone = 0.86 + 0.18 * u2[sel]
        V, UV, C, T = _quads(a3, b3, h, lean, uv, nrm, MAIZE_OCC[0] * tone, MAIZE_OCC[1] * tone)
        out.append((V, UV, C, T, tag))
        return n

    n_row = emit(A, B, ok, 2, "maize")
    # cross cards: from this card row towards the next, at the middle of the card
    cs = ok & (u4 < MAIZE_CROSS_SHARE)
    if cs.any():
        off = (u1 - 0.5) * 0.8 * MAIZE_CARD_L
        A2 = _row_point(L0, rc + 0.15, sc + off, ox, oy)
        B2 = _row_point(L0, rc + pitch - 0.15, sc + off, ox, oy)
        ok2 = cs & valid(A2)[0] & valid(B2)[0]
        n_cross = emit(A2, B2, ok2, 1, "maize_cross")
    rep["maize"] = {"strips": int(len(np.unique(L["fid"]))), "row_cards": n_row, "cross_cards": n_cross,
                    "card_row_pitch_m": pitch, "height_m": list(MAIZE_H)}
    return out, n_row, n_cross


def _smooth(v, t):
    x = np.clip((v - t[0]) / (t[1] - t[0]), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _baulks(g, origin, rep):
    ox, oy = origin
    gx, gy = np.meshgrid(np.arange(g.hf.x0 + 1.0, g.hf.x0 + g.W - 1.0, 1.0), np.arange(g.hf.y1 - g.H + 2.0, g.hf.y1 - 1.0, 1.0))
    P = np.column_stack([gx.ravel(), gy.ravel()])
    P = P[g.arable(P, VG.FIELD_ROAD_M, BAULK_ROAD_RANGE_M)]
    if not len(P):
        return []
    ax, ay = P[:, 0] + ox, P[:, 1] + oy
    L = VG.field_layout(ax, ay)
    e = np.minimum(L["across"], L["w"] - L["across"])
    up = L["across"] >= 0.5 * L["w"]
    zero = np.zeros(len(P))
    bid = L["bid"].astype(np.float64)
    own = VG._u01(VG._h32(L["fid"].astype(np.float64), zero, 931)) < VG.FIELD_OWN_SHARE_SHADER
    fid_n = VG._h32(bid, L["k"] + np.where(up, 1.0, -1.0), 929)
    own_n = VG._u01(VG._h32(fid_n.astype(np.float64), zero, 931)) < VG.FIELD_OWN_SHARE_SHADER
    seam = (e < BAULK_BAND_M) & (own | own_n) & (L["block_edge"] > 3.0)
    border = (L["block_edge"] >= BAULK_BORDER_M[0]) & (L["block_edge"] < BAULK_BORDER_M[1])
    dens = _smooth(0.6 * VG._kf_noise(ax, ay, BAULK_DENS_M[0], 1051) + 0.4 * VG._kf_noise(ax, ay, BAULK_DENS_M[1], 1053),
                   BAULK_DENS_T)
    ci, cj = np.floor(ax), np.floor(ay)
    u = VG._u01(VG._h32(ci, cj, 1055))
    # a 1 m cell of the 2 x BAULK_BAND_M wide band = 1 m of baulk
    keep = (seam & (u < dens * BAULK_RATE)) | (border & ~seam & (u < dens * BAULK_BORDER_RATE))
    if not keep.any():
        return []
    P, ci, cj, ax, ay, dens = P[keep], ci[keep], cj[keep], ax[keep], ay[keep], dens[keep]
    hv = [VG._u01(VG._h32(ci, cj, 1057 + 2 * q)) for q in range(8)]
    P = P + (np.column_stack([hv[0], hv[1]]) - 0.5) * 0.9
    names = [n for n, _ in VF.FORMS_BAULK]
    wts = np.array([w for _, w in VF.FORMS_BAULK])
    forb = np.array([n not in VF.GRASS for n in names])
    # colonies: one forb dominates a BAULK_COLONY_M cell where the colony noise is high
    col_on = VG._kf_noise(ax, ay, BAULK_COLONY_M, 1075) > 0.58
    kx, ky = np.floor(ax / BAULK_COLONY_M), np.floor(ay / BAULK_COLONY_M)
    dom = np.nonzero(forb)[0][(VG._u01(VG._h32(kx, ky, 1077)) * forb.sum()).astype(int) % max(int(forb.sum()), 1)]
    W = np.tile(wts, (len(P), 1)) * np.where(forb, VF.FORB_OUTSIDE, 1.0)[None, :]
    W[col_on, dom[col_on]] = wts[dom[col_on]] * VF.COLONY_BOOST
    cum = np.cumsum(W, axis=1)
    pick = np.minimum((cum < (hv[2] * cum[:, -1])[:, None]).sum(1), len(names) - 1)
    fh = np.array([VF.FORM_H.get(n, 1.0) for n in names])[pick]
    sc = VF.SCALE[0] + (VF.SCALE[1] - VF.SCALE[0]) * hv[3]
    h = np.clip((BAULK_H[0] + (BAULK_H[1] - BAULK_H[0]) * hv[4]) * sc * fh * (0.8 + 0.3 * dens), 0.30, 1.30)
    w = (VF.W_CARD[0] + (VF.W_CARD[1] - VF.W_CARD[0]) * hv[5]) * (0.8 + 0.25 * sc)
    ang = hv[6] * np.pi
    uvt = np.array([VF.form_uv(n) for n in names])[pick]
    flip = hv[7] < 0.5
    uv = np.column_stack([np.where(flip, uvt[:, 1], uvt[:, 0]), np.where(flip, uvt[:, 0], uvt[:, 1]), uvt[:, 2], uvt[:, 3]])
    out = []

    def emit(sel, turn, hs):
        n = int(sel.sum())
        if not n:
            return 0
        d = np.column_stack([np.cos(ang[sel] + turn), np.sin(ang[sel] + turn)]) * (0.5 * w[sel])[:, None]
        A, B = P[sel] - d, P[sel] + d
        a3 = np.column_stack([A, g.z(A) - VF.SINK_M])
        b3 = np.column_stack([B, g.z(B) - VF.SINK_M])
        lean = np.column_stack([-d[:, 1], d[:, 0]]) / np.maximum(0.5 * w[sel], 1e-6)[:, None] * (h[sel] * 0.16 * (2.0 * hv[1][sel] - 1.0))[:, None]
        nrm = np.column_stack([np.zeros((n, 2)), np.ones(n)])
        tone = VF.TONE[0] + (VF.TONE[1] - VF.TONE[0]) * hv[0][sel]
        out.append(_quads(a3, b3, h[sel] * hs + VF.SINK_M, lean, uv[sel], nrm, VF.OCC[0] * tone, VF.OCC[1] * tone) + ("baulk",))
        return n

    allc = np.ones(len(P), bool)
    n1 = emit(allc, 0.0, 1.0)
    n2 = emit(hv[3] * 7.0 % 1.0 < BAULK_CROSS_SHARE, np.pi / 2, 0.92)
    forms = {n: int((pick == i).sum()) for i, n in enumerate(names)}
    rep["baulk_sward"] = {"plants": n1, "cross_cards": n2, "forms": forms, "road_range_m": BAULK_ROAD_RANGE_M}
    return out


def build(buf, col, hf, zc, origin, dist_road, blocked, report=None, enabled=True, layer=LAYER):
    """Maize row cards and baulk sward cards into `buf` (see the module docstring). col: (H, W, 4) terrain ground
    masks on the 1 m grid of hf (farmland flag in B), zc: terrain height, dist_road: metres to the nearest road /
    yard cell, blocked: bool grid (roads, buildings + margin) or None. Returns the triangle count."""
    rep = {}
    ntri = 0
    if enabled and col is not None and (np.asarray(col)[..., 2] >= ARABLE_B).any():
        g = _Ground(col, hf, zc, dist_road, blocked)
        parts, _, _ = _maize(g, origin, rep)
        parts += _baulks(g, origin, rep)
        for tag in ("maize", "maize_cross", "baulk"):
            sel = [p for p in parts if p[4] == tag]
            if not sel:
                continue
            nv = 0
            V, UV, C, T = [], [], [], []
            for v_, uv_, c_, t_, _ in sel:
                V.append(v_)
                UV.append(uv_)
                C.append(c_)
                T.append(t_ + nv)
                nv += len(v_)
            T = np.concatenate(T)
            buf.add(layer, MAT, np.concatenate(V), np.concatenate(UV), T, src="field_crops:" + tag, COL=np.concatenate(C))
            ntri += len(T)
    rep["triangles"] = ntri
    if report is not None:
        report["field_crops"] = rep
    return ntri
