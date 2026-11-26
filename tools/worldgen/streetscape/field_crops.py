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
MAIZE_ROAD_RANGE_M = 220.0
MAIZE_SEAM_CLEAR_M = 1.6         # off the strip seam (baulk half-width <= 1.3 m + the thinning crop) - r4b: fallback only
MAIZE_BAULK_GAP_M = 0.25         # r4b: cards this far off the shader's baulk edge (the outer plants lean over it)
MAIZE_BLOCK_CLEAR_M = 2.8        # off the block border (grass strip / field track)
MAIZE_ROAD_CLEAR_M = 5.0
MAIZE_CROSS_SHARE = 0.34         # row cards with a cross card towards the next card row
MAIZE_ZIGZAG_M = 0.40            # card ends this far off the row line, alternately: no card is edge-on to a view along
                                 # the rows (render review r3: from 14 m up the edge-on rows vanished and only the
                                 # cross cards showed - a hedge maze)
MAIZE_OCC = (0.50, 1.0)          # foot (deep in the crop) .. top
# r4 (critic s24 wave 11 "pionowe płaskie ściany bloków", dw671-tykocin-03 edge-north): the stand ended in a flat wall
# of 3.2 m cards - the side of the outermost card row, the cross cards facing out of a cut, and every row stopping on
# one line. Seams WITHOUT a baulk (two strips of one holding, same use) are no longer cleared (they left a 3.2 m
# corridor with the painted rows on the ground). Within MAIZE_EDGE_M of a real stop (a baulk, the block border, a road,
# the end of the card range, the end of the arable ground) a card is split into single-cell cards of uneven height
# (MAIZE_EDGE_H x the stand), thinned towards the stop (MAIZE_EDGE_KEEP), jittered and turned off the row line,
# leaning out; the outermost show the atlas edge cell (single plants, hanging leaves) and a few plants stand in front
# of the line (strays, MAIZE_STRAY_*). No cross cards there. All WORKING_VALUE (render review on the control cameras).
MAIZE_EDGE_M = 4.0               # edge zone: ~2 card rows (~7 crop rows) - through a thinned outer row the next one shows
MAIZE_EDGE_H = (0.70, 1.0)       # height factor at the stop .. MAIZE_EDGE_M inside
MAIZE_EDGE_KEEP = (0.60, 1.0)    # share of edge cards kept at the stop .. inside
MAIZE_EDGE_JITTER_M = 0.22       # off the row line, either way
MAIZE_EDGE_TURN = 0.33           # rad, either way
MAIZE_EDGE_CELL_D_M = 1.4        # closer than this to the stop: mostly the edge cell (single plants)
MAIZE_EDGE_CROSS = 0.22          # edge cards with a short card across (a plant group, not a face)
MAIZE_STRAY_D_M = 1.7            # edge cards this close to the stop put plants in front of the line
MAIZE_STRAY_N = (0.45, 0.12)     # P(>= 1 stray), P(2 strays) per such card
MAIZE_STRAY_OUT_M = (0.3, 1.4)   # metres in front of the line
MAIZE_STRAY_W_M = VA.MAIZE_CELL_M / VA.MAIZE_EDGE_PLANTS
MAIZE_STRAY_H = (1.45, 2.30)
BAULK_ROAD_RANGE_M = 90.0
BAULK_BAND_M = 0.5               # candidates this far from the seam line
BAULK_RATE = 1.6                 # plants per metre of baulk where the density is 1
BAULK_BORDER_M = (1.4, 2.2)      # block border: the outer part of its grass strip (clear of a field track's ruts)
BAULK_BORDER_RATE = 0.9
BAULK_DENS_M = (13.0, 41.0)
BAULK_DENS_T = (0.34, 0.66)
BAULK_H = (0.45, 0.95)
BAULK_COLONY_M = 30.0
BAULK_CROSS_SHARE = 0.30
# Draw-call budget (lead review r3: +3 on a route camera, up to +10 in a field): all cards of a chunk share ONE
# primitive with the roadside sward (same layer, same material), so the cost is one draw per chunk that had no `banks`
# primitive before. A chunk is given one only for at least CHUNK_MIN_TRIS triangles of cards (a wall of maize, a run
# of baulks) - never for a corner of a strip that reaches into it.
CHUNK_MIN_TRIS = 5600              # r4: 4000 -> 5600 (margin cards +40 %: the same chunks earn a primitive as in r3b)
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
        self._dar = None
        self.off = None          # r4c: cells of chunks without a cards primitive (a stop of the stand)

    @property
    def dar(self):
        """r4: metres to the nearest cell that is not arable (or blocked) - the end of the stand where the polygon ends.
        The grid border is not a stop (the neighbouring tile carries on)."""
        if self._dar is None:
            from scipy import ndimage
            ok = self.b >= ARABLE_B
            if self.blocked is not None:
                ok &= ~self.blocked
            if self.off is not None:
                ok &= ~self.off
            self._dar = ndimage.distance_transform_edt(ok).astype(np.float32)
        return self._dar

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


def _baulk_sides(L):
    """(lower, upper) seam of the strip carries a baulk - the shader's hasBaulk (own strip or own neighbour)."""
    zero = np.zeros(L["fid"].shape)
    bid = L["bid"].astype(np.float64)
    own = VG._u01(VG._h32(L["fid"].astype(np.float64), zero, 931)) < VG.FIELD_OWN_SHARE_SHADER
    lo = VG._h32(bid, L["k"] - 1.0, 929)
    hi = VG._h32(bid, L["k"] + 1.0, 929)
    own_lo = VG._u01(VG._h32(lo.astype(np.float64), zero, 931)) < VG.FIELD_OWN_SHARE_SHADER
    own_hi = VG._u01(VG._h32(hi.astype(np.float64), zero, 931)) < VG.FIELD_OWN_SHARE_SHADER
    return own | own_lo, own | own_hi


def baulk_clear(Lq, Q, origin):
    """r4b: (lower, upper) seam clearance, m: the shader's baulk half-width at Q (KamionFieldMosaic: bw per strip edge
    from hash 947, swelling with the 5 m noise; the 1.7 m wiggle +-0.3 m is left out) + MAIZE_BAULK_GAP_M. r4a used
    MAIZE_SEAM_CLEAR_M everywhere - a 1-1.6 m strip of maize painted on the ground without cards beside every baulk
    (dw671-tykocin-03 edge-north: the corridor stayed). origin None: MAIZE_SEAM_CLEAR_M."""
    if origin is None:
        return np.full(len(Q), MAIZE_SEAM_CLEAR_M), np.full(len(Q), MAIZE_SEAM_CLEAR_M)
    bid = Lq["bid"].astype(np.float64)
    n5 = VG._kf_noise(Q[:, 0] + origin[0], Q[:, 1] + origin[1], 5.0, 951)
    out = []
    for ke in (Lq["k"], Lq["k"] + 1.0):
        bw = VG.FIELD_BAULK_W[0] + VG.FIELD_BAULK_W[1] * VG._u01(VG._h32(bid, ke, 947))
        out.append(np.maximum(0.5 * bw * (0.55 + 0.9 * n5), 0.12) + MAIZE_BAULK_GAP_M)
    return out[0], out[1]


def _edge_dist(g, Q, Lq, origin=None):
    """r4: metres from region-local points Q (layout Lq) to the nearest STOP of the card stand: a seam with a baulk
    (minus its clearance, baulk_clear), the block border, the road clearance, the end of the card range, the end of
    the arable ground. Negative = no card here. A seam without a baulk is not a stop (the crop runs on)."""
    lo, hi = _baulk_sides(Lq)
    a, w = Lq["across"], Lq["w"]
    c_lo, c_hi = baulk_clear(Lq, Q, origin)
    d = np.minimum(np.where(lo, a - c_lo, np.inf), np.where(hi, w - a - c_hi, np.inf))
    d = np.minimum(d, Lq["block_edge"] - MAIZE_BLOCK_CLEAR_M)
    i, j, ok = g.ij(Q)
    dr = g.dist[j, i]
    d = np.minimum(d, np.minimum(dr - MAIZE_ROAD_CLEAR_M, MAIZE_ROAD_RANGE_M - dr))
    d = np.minimum(d, g.dar[j, i] - 0.75)
    return np.where(ok, d, -1.0)


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

    def valid(Q, fids=None):
        """(inside the stand, distance to its nearest stop) at region-local points Q of the strips `fids`."""
        i, j, ok = g.ij(Q)
        ok &= g.b[j, i] >= ARABLE_B
        if g.blocked is not None:
            ok &= ~g.blocked[j, i]
        Lq = VG.field_layout(Q[:, 0] + ox, Q[:, 1] + oy)
        ok &= Lq["fid"] == (fid0 if fids is None else fids)
        de = _edge_dist(g, Q, Lq, origin)
        return ok & (de > 0.0), de

    zz = np.where((s_idx + m_idx) % 2 == 0, MAIZE_ZIGZAG_M, -MAIZE_ZIGZAG_M)
    half = float(np.sqrt((0.5 * MAIZE_CARD_L) ** 2 - MAIZE_ZIGZAG_M ** 2))
    A = _row_point(L0, rc - zz, sc - half, ox, oy)
    B = _row_point(L0, rc + zz, sc + half, ox, oy)
    okA, deA = valid(A)
    okB, deB = valid(B)
    ok = okA & okB
    de = np.minimum(deA, deB)
    edge = ok & (de < MAIZE_EDGE_M)
    hk = VG._h32(key_a, s_idx.astype(np.float64), 1043)
    u1, u2, u3, u4 = (VG._u01(VG._h32(hk.astype(np.float64), np.full(len(hk), float(q)), 1045)) for q in range(4))
    dirv = np.column_stack([np.cos(L0["th"]), np.sin(L0["th"])])        # across the rows

    def put(A_, B_, h, lean, uv, nrm, occ0, occ1, tag):
        n = len(A_)
        if not n:
            return 0
        a3 = np.column_stack([A_, g.z(A_) - MAIZE_SINK_M])
        b3 = np.column_stack([B_, g.z(B_) - MAIZE_SINK_M])
        V, UV, C, T = _quads(a3, b3, h + MAIZE_SINK_M, lean, uv, nrm, occ0, occ1)
        out.append((V, UV, C, T, tag))
        return n

    def emit(A_, B_, sel, cells, tag):
        n = int(sel.sum())
        if not n:
            return 0
        h = MAIZE_H[0] + (MAIZE_H[1] - MAIZE_H[0]) * u1[sel]
        lean = dirv[sel] * ((u2[sel] - 0.5) * 0.22)[:, None]
        uv, flip = _cell_uv(u3[sel], u4[sel], cells)
        nrm = np.column_stack([dirv[sel] * (np.where(flip, -0.3, 0.3))[:, None], np.ones(n)])
        tone = 0.86 + 0.18 * u2[sel]
        return put(A_[sel], B_[sel], h, lean, uv, nrm, MAIZE_OCC[0] * tone, MAIZE_OCC[1] * tone, tag)

    n_row = emit(A, B, ok & ~edge, 2, "maize")
    # cross cards: from this card row towards the next, at the middle of the card - not near a stop, where they are
    # the faces of the cut seen from outside
    cs = ok & ~edge & (u4 < MAIZE_CROSS_SHARE)
    if cs.any():
        off = (u1 - 0.5) * 0.8 * MAIZE_CARD_L
        A2 = _row_point(L0, rc + 0.15, sc + off, ox, oy)
        B2 = _row_point(L0, rc + pitch - 0.15, sc + off, ox, oy)
        vA2, dA2 = valid(A2)
        vB2, dB2 = valid(B2)
        ok2 = cs & vA2 & vB2 & (np.minimum(dA2, dB2) > MAIZE_EDGE_M)
        n_cross = emit(A2, B2, ok2, 1, "maize_cross")
    n_edge, n_stray = _maize_edge(g, A[edge], B[edge], hk[edge], dirv[edge], fid0[edge], valid, put)
    rep["maize"] = {"strips": int(len(np.unique(L["fid"]))), "row_cards": n_row, "cross_cards": n_cross,
                    "edge_cards": n_edge, "strays": n_stray, "edge_zone_m": MAIZE_EDGE_M,
                    "card_row_pitch_m": pitch, "height_m": list(MAIZE_H)}
    return out, n_row, n_cross


def _cell_uv(u_cell, u_flip, cells, edge_cell=None):
    """(N, 4) uv of `cells` consecutive WALL cells of the maize row (or the edge cell where edge_cell), flip flags."""
    c0 = np.floor(u_cell * (VA.N_MAIZE_WALL - cells + 1)) / VA.N_MAIZE
    if edge_cell is not None:
        c0 = np.where(edge_cell, VA.MAIZE_EDGE_CELL / VA.N_MAIZE, c0)
    ua, ub = c0, c0 + cells / VA.N_MAIZE
    flip = u_flip < 0.5
    n = len(c0)
    return np.column_stack([np.where(flip, ub, ua), np.where(flip, ua, ub),
                            np.full(n, VA.V_MAIZE[0] + 0.004), np.full(n, VA.V_MAIZE[1] - 0.004)]), flip


def _maize_edge(g, A, B, hk, dirv, fid0, valid, put):
    """r4: the margin of the stand (see MAIZE_EDGE_*). Each 2-cell row card within MAIZE_EDGE_M of a stop becomes two
    single-cell cards (kept by a share falling towards the stop, lower towards it, jittered off the row and turned,
    leaning out of the stand), the outermost mostly with the atlas edge cell; plants in front of the line (strays)
    stand alone or crossed, turned anyhow. Returns (edge cards, stray plants)."""
    n0 = len(A)
    if not n0:
        return 0, 0
    M = 0.5 * (A + B)
    n_edge = n_stray = 0
    for Aa, Bb, side in ((A, M, 0.0), (M, B, 1.0)):
        hs = VG._h32(hk.astype(np.float64), np.full(n0, 2.0 + side), 1047)
        v = [VG._u01(VG._h32(hs.astype(np.float64), np.full(n0, float(q)), 1049)) for q in range(10)]
        C = 0.5 * (Aa + Bb)
        ok, de = valid(C, fid0)
        t = np.clip(de / MAIZE_EDGE_M, 0.0, 1.0)
        keep = ok & (v[0] < MAIZE_EDGE_KEEP[0] + (MAIZE_EDGE_KEEP[1] - MAIZE_EDGE_KEEP[0]) * t)
        if not keep.any():
            continue
        Aa, Bb, C, de, t, dv, hs, fk = Aa[keep], Bb[keep], C[keep], de[keep], t[keep], dirv[keep], hs[keep], fid0[keep]
        v = [x[keep] for x in v]
        n = len(C)
        # outward: down the gradient of the distance to the stop (central differences, 0.6 m)
        ex, ey = np.array([0.6, 0.0]), np.array([0.0, 0.6])
        gxd = valid(C + ex, fk)[1] - valid(C - ex, fk)[1]
        gyd = valid(C + ey, fk)[1] - valid(C - ey, fk)[1]
        out_v = -np.column_stack([gxd, gyd])
        ol = np.linalg.norm(out_v, axis=1, keepdims=True)
        out_v = np.where(ol > 1e-6, out_v / np.maximum(ol, 1e-6), dv)
        # the card: jittered off the row, turned about its middle
        jit = dv * ((v[1] - 0.5) * 2.0 * MAIZE_EDGE_JITTER_M)[:, None]
        ang = (v[2] - 0.5) * 2.0 * MAIZE_EDGE_TURN
        hv = 0.5 * (Bb - Aa)
        ca, sa = np.cos(ang), np.sin(ang)
        hv = np.column_stack([hv[:, 0] * ca - hv[:, 1] * sa, hv[:, 0] * sa + hv[:, 1] * ca])
        C2 = C + jit
        h = (MAIZE_H[0] + (MAIZE_H[1] - MAIZE_H[0]) * v[3]) * (MAIZE_EDGE_H[0] + (MAIZE_EDGE_H[1] - MAIZE_EDGE_H[0]) * t) \
            * (0.90 + 0.16 * v[4])
        lean = out_v * ((0.10 + 0.32 * (1.0 - t)) * v[5])[:, None] + dv * ((v[6] - 0.5) * 0.20)[:, None]
        uv, _ = _cell_uv(v[7], v[8], 1, edge_cell=(de < MAIZE_EDGE_CELL_D_M) & (v[9] < 0.75))
        nrm = np.column_stack([out_v * 0.45, np.ones(n)])
        tone = 0.88 + 0.18 * v[4]
        occ0 = (MAIZE_OCC[0] + 0.16 * (1.0 - t)) * tone          # the margin is lit down to the foot
        n_edge += put(C2 - hv, C2 + hv, h, lean, uv, nrm, occ0, MAIZE_OCC[1] * tone, "maize_edge")
        # a short card across the row: a plant group seen from the side, not a face
        xs = v[2] < MAIZE_EDGE_CROSS
        if xs.any():
            k = int(xs.sum())
            a2 = ang[xs] + np.pi / 2 + (v[6][xs] - 0.5) * 0.8
            hl = 0.5 * VA.MAIZE_CELL_M * (0.55 + 0.4 * v[1][xs])
            d2 = np.column_stack([np.cos(a2), np.sin(a2)]) * hl[:, None]
            Cx = C2[xs] + dv[xs] * ((v[5][xs] - 0.5) * 0.6)[:, None]
            uvx, _ = _cell_uv(v[8][xs], v[7][xs], 1, edge_cell=np.ones(k, bool))
            n_edge += put(Cx - d2, Cx + d2, h[xs] * (0.85 + 0.12 * v[9][xs]), lean[xs] * 0.7, uvx,
                          np.column_stack([out_v[xs] * 0.45, np.ones(k)]), occ0[xs], MAIZE_OCC[1] * tone[xs], "maize_edge")
        # strays in front of the line
        for q in range(2):
            hq = VG._h32(hs.astype(np.float64), np.full(n, 20.0 + q), 1051)
            w = [VG._u01(VG._h32(hq.astype(np.float64), np.full(n, float(r)), 1053)) for r in range(8)]
            sel = (de < MAIZE_STRAY_D_M) & (w[0] < MAIZE_STRAY_N[q])
            if not sel.any():
                continue
            outd = MAIZE_STRAY_OUT_M[0] + (MAIZE_STRAY_OUT_M[1] - MAIZE_STRAY_OUT_M[0]) * w[1][sel]
            alongd = (w[2][sel] - 0.5) * VA.MAIZE_CELL_M
            tv = np.column_stack([-dv[sel, 1], dv[sel, 0]])
            S = C[sel] + out_v[sel] * outd[:, None] + tv * alongd[:, None]
            i, j, okS = g.ij(S)
            okS &= g.dist[j, i] > MAIZE_ROAD_CLEAR_M - 1.5
            if g.blocked is not None:
                okS &= ~g.blocked[j, i]
            okS &= g.b[j, i] >= 0.5                                # on the field or its grass margin, not a yard
            if not okS.any():
                continue
            S = S[okS]
            ws = [x[sel][okS] for x in w]
            ov = out_v[sel][okS]
            m = len(S)
            a3 = ws[3] * np.pi
            hw = 0.5 * MAIZE_STRAY_W_M * (0.9 + 0.3 * ws[4])
            dd = np.column_stack([np.cos(a3), np.sin(a3)]) * hw[:, None]
            pl = np.floor(ws[5] * VA.MAIZE_EDGE_PLANTS).clip(0, VA.MAIZE_EDGE_PLANTS - 1)
            u0 = (VA.MAIZE_EDGE_CELL + pl / VA.MAIZE_EDGE_PLANTS) / VA.N_MAIZE
            u1_ = u0 + 1.0 / (VA.MAIZE_EDGE_PLANTS * VA.N_MAIZE)
            fl = ws[6] < 0.5
            uvs = np.column_stack([np.where(fl, u1_, u0), np.where(fl, u0, u1_),
                                   np.full(m, VA.V_MAIZE[0] + 0.004), np.full(m, VA.V_MAIZE[1] - 0.004)])
            # the card spans the atlas height (MAIZE_H_M); the painted plants are 1.55-2.3 m of it
            hS = (MAIZE_STRAY_H[0] + (MAIZE_STRAY_H[1] - MAIZE_STRAY_H[0]) * ws[7]) * (VA.MAIZE_H_M / 2.30)
            leanS = ov * (0.08 + 0.30 * ws[2])[:, None]
            nrmS = np.column_stack([ov * 0.3, np.ones(m)])
            occS = np.full(m, MAIZE_OCC[0] + 0.22)
            n_stray += put(S - dd, S + dd, hS, leanS, uvs, nrmS, occS, np.full(m, MAIZE_OCC[1]), "maize_edge")
            cr = ws[4] < 0.35                                       # crossed: seen from every side
            if cr.any():
                dd2 = np.column_stack([-dd[cr, 1], dd[cr, 0]])
                put(S[cr] - dd2, S[cr] + dd2, hS[cr], leanS[cr], uvs[cr][:, [1, 0, 2, 3]], nrmS[cr], occS[cr],
                    np.full(int(cr.sum()), MAIZE_OCC[1]), "maize_edge")
    return n_edge, n_stray


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


def build(buf, col, hf, zc, origin, dist_road, blocked, report=None, enabled=True, layer=LAYER, chunk_fn=None):
    """Maize row cards and baulk sward cards into `buf` (see the module docstring). col: (H, W, 4) terrain ground
    masks on the 1 m grid of hf (farmland flag in B), zc: terrain height, dist_road: metres to the nearest road /
    yard cell, blocked: bool grid (roads, buildings + margin) or None. Returns the triangle count."""
    rep = {}
    ntri = 0
    keep = None
    if enabled and col is not None and (np.asarray(col)[..., 2] >= ARABLE_B).any():
        g = _Ground(col, hf, zc, dist_road, blocked)
        parts, _, _ = _maize(g, origin, rep)
        parts += _baulks(g, origin, rep)
        if chunk_fn is not None:
            # r4c (render review r4a, knyszyn-w f3_maize_chase): a chunk without its own primitive lost its cards along
            # the chunk border - a ruled vertical cut through the stand. The chunk rule is decided on this first pass;
            # the dropped chunks then count as the end of the arable ground (_Ground.dar) and the stand is generated
            # again, so it ends there with the ragged margin. The keep set stays the one of the first pass.
            _add_parts(buf, parts, layer)
            keep = prune_sparse_chunks(buf, chunk_fn, layer, dry=True)
            buf.parts = [q for q in buf.parts if not q.src.startswith("field_crops:")]
            n = g.b.shape
            xs = g.hf.x0 + np.arange(n[1], dtype=np.float64)
            ys = g.hf.y1 - np.arange(n[0], dtype=np.float64)
            ci, cj = chunk_fn(*np.meshgrid(xs, ys))
            kk = np.asarray(ci).astype(np.int64) * 4096 + np.asarray(cj)
            g.off = ~np.isin(kk, list(keep))
            g._dar = None
            rep2 = {}
            parts, _, _ = _maize(g, origin, rep2)
            parts += _baulks(g, origin, rep2)
            rep.update(rep2)
        ntri = _add_parts(buf, parts, layer)
    if chunk_fn is not None:
        rep["chunks"] = prune_sparse_chunks(buf, chunk_fn, layer, keep=keep)
        ntri = int(sum(len(q.T) for q in buf.parts if q.layer == layer and q.mat == MAT and q.src.startswith("field_crops:")))
    rep["triangles"] = ntri
    if report is not None:
        report["field_crops"] = rep
    return ntri


def _add_parts(buf, parts, layer):
    ntri = 0
    if True:
        for tag in ("maize", "maize_cross", "maize_edge", "baulk"):
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
    return ntri


SWARD_MIN_TRIS = 60              # roadside sward alone earns the chunk its primitive from this many triangles


def prune_sparse_chunks(buf, chunk_fn, layer=LAYER, keep=None, dry=False):
    """The draw-call rule (CHUNK_MIN_TRIS): the exporter gives every chunk ONE `banks` primitive of material
    `verge_tufts`, split by triangle centroid. A chunk keeps it if its roadside sward has >= SWARD_MIN_TRIS triangles
    or all its cards together >= CHUNK_MIN_TRIS; otherwise its triangles are removed - with the whole card (4
    vertices), so no half card is left on the other side of a chunk border. Returns the tally. r4c: dry -> only the
    keep set (chunk keys); keep -> apply that set instead of deciding again."""
    parts = [q for q in buf.parts if q.layer == layer and q.mat == MAT and len(q.T)]
    keys, total, sward = [], {}, {}
    for q in parts:
        T = np.asarray(q.T)
        cen = np.asarray(q.V)[T].mean(1)
        ci, cj = chunk_fn(cen[:, 0], cen[:, 1])
        k = np.asarray(ci).astype(np.int64) * 4096 + np.asarray(cj)
        keys.append(k)
        uk, cnt = np.unique(k, return_counts=True)
        for kk, c in zip(uk.tolist(), cnt.tolist()):
            total[kk] = total.get(kk, 0) + c
            if q.src.startswith("verge_flora:"):
                sward[kk] = sward.get(kk, 0) + c
    if keep is None:
        keep = {k for k, c in total.items() if sward.get(k, 0) >= SWARD_MIN_TRIS or c >= CHUNK_MIN_TRIS}
    if dry:
        return keep
    keep = keep & set(total)
    dropped = 0
    for q, k in zip(parts, keys):
        T = np.asarray(q.T)
        bad = ~np.isin(k, list(keep))
        if not bad.any():
            continue
        card = T.min(1) // 4
        gone = np.isin(card, np.unique(card[bad]))
        dropped += int(gone.sum())
        q.T = T[~gone]
    return {"with_cards": len(keep), "dropped": len(total) - len(keep), "dropped_triangles": dropped,
            "min_triangles": CHUNK_MIN_TRIS, "sward_min_triangles": SWARD_MIN_TRIS}
