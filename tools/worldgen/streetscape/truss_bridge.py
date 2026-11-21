"""Through bowstring-truss road bridge: authored override `kind: truss_bridge` (ADR 0320).

The generic bridge of roads.meshing (flat deck, railing, round piers every 30 m by rule) stays as the *deck*: the
carriageway, kerbs, caps, W-beam barriers, soffit and the road collision are untouched, so physics, the route corridor,
the water clearance (ADR 0318) and the B-16 / B-18 posts (ADR 0307) do not move. This rule adds what makes the object
recognisable and removes the two generic parts that contradict it:

  - removed: the generic deck-edge railing (`<chain>:parapet`) and the rule piers / abutments (skipped in build_world);
  - added:   per truss span two steel trusses with a parabolic top chord standing just outside the caps, verticals and
             diagonals as laced members, gusset plates, top lateral bracing where the headroom allows it, portal knee
             braces, cantilevered footways outside the trusses with a picket railing, striped end boards, concrete
             piers with an ice-breaker on the upstream side at the span joints, abutments.

Layers: LOD0 -> `buildings`, LOD1 -> `buildings_low` (solid members, no lacing / pickets / brackets), collision boxes
for the chords, verticals and piers. Everything is generated from the chain geometry and the override; no texture,
lettering or emblem is used.

Sources (reference only, nothing copied): Wikimedia Commons "Tykocin Most drogowy 01-09" (Zala, CC BY-SA 4.0,
Data/raw/refs/tykocin-bridge-commons) for the type, the member pattern and the colours; GUGiK orthophoto 2024 (0.25 m)
for the span lengths. Every number of the override that is not measured there is a WORKING_VALUE (see ADR 0320).
"""
from __future__ import annotations

import math

import numpy as np

from roads import meshing as M
from . import buildings_mesh as BM
from . import hero_bridge as HB

KIND = "truss_bridge"
LAYERS = ("buildings", "buildings_low")
STEEL, RAIL, PICKET, CONC, BOARD = "truss_steel", "truss_rail_blue", "truss_picket", "viaduct_concrete", "hazard_stripes"

# Metres. WORKING_VALUE unless the override says otherwise (proportions read off the Commons photos against the
# generated deck; no drawings of the object are available).
DEFAULTS = {
    "panel_m": 4.25,            # target panel length (main span: 12 panels on photo 05)
    "rise_ratio": 0.153,        # top chord rise / span (photo 05: about 1 : 6.5)
    "truss_out_m": 0.30,        # truss centre line outside the outer edge of the cap
    "chord_w_m": 0.46, "chord_d_m": 0.44,          # top chord box
    "bottom_w_m": 0.36, "bottom_top_m": 0.12, "bottom_d_m": 0.95,
    "web_w_m": 0.30, "web_d_m": 0.36, "flange_m": 0.07, "lace_w_m": 0.05,
    "end_gap_m": 0.35,          # truss end short of the pier centre line
    "headroom_m": 4.30,         # lowest bracing member above the carriageway: B-16 "3,7 m" + 0.5 m (znak = skrajnia
                                # - 0,5 m, Dz.U. 2003 nr 220 poz. 2181 zal. 1 pkt 3.2.17) + 0.1 m
    "strut_d_m": 0.50,
    "footway_w_m": 1.55,        # clear footway outside the truss
    "slab_t_m": 0.18, "fascia_h_m": 0.40,
    "rail_h_m": 1.10, "rail_post_m": 2.0, "picket_m": 0.20,
    "pier_t_m": 1.20, "pier_cap_h_m": 0.80, "bearing_m": 0.15,
    "pile_m": 0.45, "pile_show_m": 2.0,
    "icebreaker_m": 4.5,
    "board_w_m": 0.50, "board_h_m": 1.50,
}


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _member(acc, layer, mat, a, b, side, w, d, skip=(4, 5)):
    """Box member from a to b; `side` = unit vector across the member (width w), depth d in the third direction."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = _unit(b - a)
    side = _unit(np.asarray(side, float) - u * float(np.dot(side, u)))
    e = np.cross(u, side)
    acc.box(layer, mat, (a + b) / 2, (b - a) / 2, side * w / 2, e * d / 2, skip=skip)


def _plate(acc, layer, mat, pts, both=True):
    """Flat polygon (fan), optionally with both windings."""
    V = np.asarray(pts, float)
    T = [[0, i, i + 1] for i in range(1, len(V) - 1)]
    acc.add(layer, mat, V, T)
    if both:
        acc.add(layer, mat, V, [t[::-1] for t in T])


def _laced(acc, a, b, side, w, d, prm):
    """LOD0 laced member: two flanges and one zigzag of flat bars in the middle plane (seen from both sides)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    u = (b - a) / L
    side = _unit(np.asarray(side, float) - u * float(np.dot(side, u)))
    e = np.cross(u, side)
    f = prm["flange_m"]
    for sg in (-1.0, 1.0):
        off = e * sg * (d / 2 - f / 2)
        acc.box("buildings", STEEL, (a + b) / 2 + off, (b - a) / 2, side * w / 2, e * f / 2, skip=(4, 5))
    n = max(2, int(round(L / (d * 1.15))))
    hw = u * prm["lace_w_m"] / 2
    reach = d / 2 - f
    for i in range(n):
        p = a + u * (L * i / n) + e * reach * (1 if i % 2 == 0 else -1)
        q = a + u * (L * (i + 1) / n) + e * reach * (-1 if i % 2 == 0 else 1)
        _plate(acc, "buildings", STEEL, [p - hw, p + hw, q + hw, q - hw])


def _strip(acc, layer, mat, nodes, side, w, dz, faces=(0, 1, 2, 3)):
    """Swept box through `nodes` (N x 3) with shared sections: +-side * w/2 across, +-dz vertically (dz per node).
    faces: 0 top, 1 bottom, 2 +side, 3 -side."""
    P = np.asarray(nodes, float)
    dz = np.broadcast_to(np.asarray(dz, float), (len(P),))
    up = np.array([0.0, 0.0, 1.0])
    c = [[P[i] + side * sx * w / 2 + up * sz * dz[i] for i in range(len(P))] for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    quads = {0: (3, 2), 1: (1, 0), 2: (2, 1), 3: (0, 3)}
    probe = np.cross(P[1] - P[0], side)          # orientation of (along x side) against up
    flip = probe[2] < 0
    for i in range(len(P) - 1):
        for fk in faces:
            j, k = quads[fk]
            q = [c[j][i], c[k][i], c[k][i + 1], c[j][i + 1]]
            if not flip:
                q = q[::-1]
            acc.quad(layer, mat, *q)


class _Deck:
    """Stations of the bridge run measured from one end (x = 0 at `first`), both cap edges."""

    def __init__(self, c, sa, sb, south_first):
        self.c, self.sa, self.sb = c, sa, sb
        ya, yb = c.line.point(sa)[1], c.line.point(sb)[1]
        self.rev = (ya > yb) if south_first else (ya < yb)
        self.L = sb - sa

    def at(self, x):
        s = self.sb - x if self.rev else self.sa + x
        st = HB._station(self.c, float(min(max(s, self.sa), self.sb)))
        t = np.array([st["t"][0], st["t"][1], 0.0]) * (-1.0 if self.rev else 1.0)
        l, r = np.array(st["l"], float), np.array(st["r"], float)
        if self.rev:
            l, r = r, l
        n = _unit(np.array([l[0] - r[0], l[1] - r[1], 0.0]))
        return {"t": t, "n": n, "l": l, "r": r, "c": np.array(st["c"], float),
                "hw": float(np.linalg.norm((l - r)[:2]) / 2)}

    def edge(self, x, sgn, out=0.0, dz=0.0):
        """Point `out` metres outside the cap edge of side sgn (+1 left of x, -1 right), dz above the cap top."""
        st = self.at(x)
        p = (st["l"] if sgn > 0 else st["r"]).copy()
        p[:2] += st["n"][:2] * sgn * out
        p[2] += dz
        return p


def chains_for(net, overrides) -> dict:
    """{chain id: override} of the elevated chains a truss_bridge override targets."""
    out = {}
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        ways = {str(x) for x in o.get("osm_ways", [])}
        for c in HB._chains(net, ways):
            out[c.id] = o
    return out


def span_layout(o, length):
    """[(x0, x1, truss, panels, rise)] of the spans scaled to the generated run length."""
    prm = {**DEFAULTS, **(o.get("set") or {})}
    spans = o["spans"]
    k = length / sum(float(s["length_m"]) for s in spans)
    out, x = [], 0.0
    for s in spans:
        L = float(s["length_m"]) * k
        panels = int(s.get("panels") or max(4, round(L / prm["panel_m"])))
        rise = float(s.get("rise_m") or L * prm["rise_ratio"])
        out.append((x, x + L, bool(s.get("truss", True)), panels, rise))
        x += L
    return out, k


def _truss(acc, dk, x0, x1, panels, rise, sgn, prm, portal_ends):
    """One truss of one span on side sgn. Returns (top nodes, bottom nodes, xs, top chord half depths)."""
    xs = np.linspace(x0 + prm["end_gap_m"], x1 - prm["end_gap_m"], panels + 1)
    L = xs[-1] - xs[0]
    st0 = dk.at(xs[0])
    side = st0["n"] * sgn                       # outward
    base = [dk.edge(x, sgn, prm["truss_out_m"]) for x in xs]
    bz = prm["bottom_top_m"] - prm["bottom_d_m"] / 2
    bot = np.array([p + [0, 0, bz] for p in base])
    h = np.array([4.0 * rise * (x - xs[0]) * (xs[-1] - x) / L ** 2 for x in xs])
    cd = prm["chord_d_m"]
    top = np.array([p + [0, 0, prm["bottom_top_m"] + hh + cd / 2] for p, hh in zip(base, h)])
    # top chord: section deeper where it runs steep, so the plate stays `chord_d_m` thick square to its axis
    slope = np.gradient(top[:, 2], xs)
    dzt = cd / 2 * np.sqrt(1.0 + slope ** 2)
    for layer in LAYERS:
        _strip(acc, layer, STEEL, top, side, prm["chord_w_m"], dzt)
        _strip(acc, layer, STEEL, bot, side, prm["bottom_w_m"], prm["bottom_d_m"] / 2)
    ww, wd = prm["web_w_m"], prm["web_d_m"]
    webs = []
    for k in range(1, panels):
        webs.append((bot[k] + [0, 0, prm["bottom_d_m"] / 2], top[k] - [0, 0, dzt[k] * 0.6], wd))
    for i in range(1, panels - 1):               # Pratt: diagonals fall towards mid-span
        left = i < panels / 2.0
        a, b = (top[i], bot[i + 1]) if left else (top[i + 1], bot[i])
        webs.append((a - [0, 0, dzt[i] * 0.5], b + [0, 0, prm["bottom_d_m"] / 2], wd * 0.8))
    for a, b, d in webs:
        _laced(acc, a, b, side, ww, d, prm)
        _member(acc, "buildings_low", STEEL, a, b, side, ww * 0.8, d * 0.55)
    # gusset plates on both faces of every panel point (LOD0)
    for k in range(1, panels):
        t = _unit(top[min(k + 1, panels)] - top[k - 1])
        for face in (-1.0, 1.0):
            off = side * face * (prm["chord_w_m"] / 2 + 0.012)
            c0 = top[k] + off
            pts = [c0 - t * 0.55 + [0, 0, dzt[k]], c0 + t * 0.55 + [0, 0, dzt[k]],
                   c0 + t * 0.42 - [0, 0, 0.62], c0 - t * 0.42 - [0, 0, 0.62]]
            _plate(acc, "buildings", STEEL, _facing(pts, side * face), both=False)
            off = side * face * (prm["bottom_w_m"] / 2 + 0.012)
            c0 = bot[k] + off + [0, 0, prm["bottom_d_m"] / 2]
            tb = _unit(bot[min(k + 1, panels)] - bot[k - 1])
            pts = [c0 - tb * 0.50 - [0, 0, 0.10], c0 + tb * 0.50 - [0, 0, 0.10],
                   c0 + tb * 0.34 + [0, 0, 0.55], c0 - tb * 0.34 + [0, 0, 0.55]]
            _plate(acc, "buildings", STEEL, _facing(pts, side * face), both=False)
    # striped boards at the foot of the end rakers that face the approaching traffic
    for end, k in ((0, 0), (1, panels)):
        if not portal_ends[end]:
            continue
        t = dk.at(xs[k])["t"] * (1.0 if end == 0 else -1.0)         # into the span
        c0 = base[k] - side * (prm["chord_w_m"] / 2 + 0.05) + t * 0.25 + [0, 0, 0.25]
        a = c0 - side * prm["board_w_m"] / 2
        b = c0 + side * prm["board_w_m"] / 2
        up = np.array([0, 0, prm["board_h_m"]])
        q = _facing([a, b, b + up, a + up], -t)                     # looks out of the span
        back = _facing([p + t * 0.02 for p in q], t)
        for layer in LAYERS:
            acc.quad(layer, BOARD, *q)
            acc.quad(layer, STEEL, *back)
    return top, bot, xs, dzt


def _facing(pts, normal):
    """The polygon with the winding whose normal looks along `normal`."""
    p = [np.asarray(x, float) for x in pts]
    return p if float(np.dot(np.cross(p[1] - p[0], p[2] - p[0]), normal)) > 0 else p[::-1]


def _bracing(acc, dk, tl, tr, xs, dzl, prm):
    """Top lateral system between the two top chords where the headroom allows: lattice struts, X laterals, portal
    knee braces at the first and the last strut. Returns the panel points that got a strut."""
    ok = []
    for k in range(1, len(xs) - 1):
        road = dk.at(xs[k])["c"][2]
        low = min(tl[k][2], tr[k][2]) - dzl[k] - prm["strut_d_m"]
        if low - road >= prm["headroom_m"]:
            ok.append(k)
    up = np.array([0.0, 0.0, 1.0])
    for k in ok:
        a, b = tl[k], tr[k]
        u = _unit(b - a)
        inset = u * prm["chord_w_m"] / 2
        a, b = a + inset, b - inset
        d = prm["strut_d_m"]
        hi_a, hi_b = a + up * (dzl[k] - 0.07), b + up * (dzl[k] - 0.07)
        lo_a, lo_b = hi_a - up * d, hi_b - up * d
        along = np.cross(u, up)
        _member(acc, "buildings", STEEL, hi_a, hi_b, along, 0.16, 0.12)
        _member(acc, "buildings", STEEL, lo_a, lo_b, along, 0.16, 0.12)
        n = max(4, int(round(np.linalg.norm(b - a) / (d * 1.1))))
        hw = u * 0.03
        for i in range(n):
            p = hi_a + (hi_b - hi_a) * (i / n) - up * (0.0 if i % 2 == 0 else d)
            q = hi_a + (hi_b - hi_a) * ((i + 1) / n) - up * (d if i % 2 == 0 else 0.0)
            _plate(acc, "buildings", STEEL, [p - hw, p + hw, q + hw, q - hw])
        _member(acc, "buildings_low", STEEL, (hi_a + lo_a) / 2, (hi_b + lo_b) / 2, along, 0.14, d * 0.7)
    for k0, k1 in zip(ok[:-1], ok[1:]):
        if k1 != k0 + 1:
            continue
        for a, b in ((tl[k0], tr[k1]), (tr[k0], tl[k1])):
            u = _unit(b - a)
            _member(acc, "buildings", STEEL, a + u * 0.3, b - u * 0.3, np.cross(u, up), 0.10, 0.10)
    if ok:
        for k in (ok[0], ok[-1]):                # portal: knee braces from the verticals to the strut
            for a, b in ((tl[k], tr[k]), (tr[k], tl[k])):
                u = _unit(b - a)
                top_in = a + u * 1.25 + up * (dzl[k] - 0.07 - prm["strut_d_m"])
                foot = a + u * (prm["chord_w_m"] / 2) + up * (dzl[k] - 0.07 - prm["strut_d_m"] - 1.05)
                for layer in LAYERS:
                    _member(acc, layer, STEEL, foot, top_in, np.cross(u, up), 0.14, 0.12)
    return ok


def _footway(acc, dk, sgn, prm, spans):
    """Cantilevered footway slab outside the cap with a blue edge beam and a picket railing along the whole run."""
    out_w = prm["truss_out_m"] * 2 + prm["footway_w_m"]
    xs = np.unique(np.concatenate([np.arange(0.0, dk.L, 4.0), [dk.L]] + [[a, b] for a, b, *_ in spans]))
    side = dk.at(0.0)["n"] * sgn
    mid = np.array([dk.edge(x, sgn, out_w / 2, 0.05 - prm["slab_t_m"] / 2) for x in xs])
    for layer in LAYERS:
        _strip(acc, layer, CONC, mid, side, out_w, prm["slab_t_m"] / 2, faces=(0, 1))
    fz = 0.05 - prm["fascia_h_m"] / 2
    fas = np.array([dk.edge(x, sgn, out_w - 0.04, fz) for x in xs])
    for layer in LAYERS:
        _strip(acc, layer, RAIL, fas, side, 0.08, prm["fascia_h_m"] / 2, faces=(1, 2, 3))
    # railing: top and bottom rail, posts, pickets
    r_out = out_w - 0.10
    top = np.array([dk.edge(x, sgn, r_out, 0.05 + prm["rail_h_m"]) for x in xs])
    low = np.array([dk.edge(x, sgn, r_out, 0.05 + 0.14) for x in xs])
    _strip(acc, "buildings", RAIL, top, side, 0.07, 0.03)
    _strip(acc, "buildings_low", RAIL, top, side, 0.07, 0.04, faces=(0, 2, 3))
    _strip(acc, "buildings", RAIL, low, side, 0.05, 0.025, faces=(0, 2, 3))
    up = np.array([0.0, 0.0, 1.0])
    for j, x in enumerate(np.arange(0.0, dk.L + 1e-6, prm["rail_post_m"])):
        p = dk.edge(min(x, dk.L), sgn, r_out, 0.05)
        _member(acc, "buildings", RAIL, p, p + up * (prm["rail_h_m"] + 0.04), side, 0.07, 0.07)
        if j % 2 == 0:
            _member(acc, "buildings_low", RAIL, p, p + up * prm["rail_h_m"], side, 0.08, 0.08)
    nx = int(dk.L / prm["picket_m"])
    V, T = [], []
    for j in range(1, nx):
        x = j * prm["picket_m"]
        if abs(x / prm["rail_post_m"] - round(x / prm["rail_post_m"])) < 1e-6:
            continue
        st = dk.at(x)
        p = dk.edge(x, sgn, r_out, 0.05 + 0.165)
        hw = st["t"] * 0.016
        b = len(V)
        V += [p - hw, p + hw, p + hw + up * (prm["rail_h_m"] - 0.20), p - hw + up * (prm["rail_h_m"] - 0.20)]
        T += [[b, b + 1, b + 2], [b, b + 2, b + 3], [b, b + 2, b + 1], [b, b + 3, b + 2]]
    acc.add("buildings", PICKET, np.array(V), T)
    # cantilever brackets under the slab at the panel points of the truss spans (LOD0)
    for x0, x1, truss, panels, _ in spans:
        if not truss:
            continue
        for x in np.linspace(x0 + prm["end_gap_m"], x1 - prm["end_gap_m"], panels + 1):
            a = dk.edge(x, sgn, prm["truss_out_m"] + prm["bottom_w_m"] / 2, 0.05 - prm["slab_t_m"])
            b = dk.edge(x, sgn, out_w - 0.10, 0.05 - prm["slab_t_m"])
            c = a + [0, 0, -(prm["bottom_d_m"] - prm["bottom_top_m"] - 0.15)]
            _plate(acc, "buildings", STEEL, [a, b, c])


def _pier(acc, buf, dk, x, prm, zground, upstream_sign, src, abutment=False):
    """Concrete pier under a span joint (or an abutment wall at a bridge end)."""
    st = dk.at(x)
    t, n, c = st["t"], st["n"], st["c"]
    half = st["hw"] + prm["truss_out_m"] + prm["bottom_w_m"] / 2 + 0.25
    cap_top = min(st["l"][2], st["r"][2]) + prm["bottom_top_m"] - prm["bottom_d_m"] - prm["bearing_m"]
    probes = [c[:2] + n[:2] * f * half for f in (-1.0, -0.5, 0.0, 0.5, 1.0)]
    zg = min(float(zground(q[0], q[1])) for q in probes)
    up = np.array([0.0, 0.0, 1.0])
    ht = prm["pier_t_m"] / 2
    if abutment:
        halfa = half + prm["footway_w_m"] + 0.5
        for layer in LAYERS:
            acc.box(layer, CONC, [c[0], c[1], (cap_top + zg - 1.0) / 2], t * 0.6, n * halfa,
                    up * (cap_top - zg + 1.0) / 2, skip=(0,))
        M.box(buf, "collision", "collision_building", c[:2], t[:2], 0.6, halfa, zg - 1.0, cap_top, src + ":abutment")
        return {"x": round(float(x), 1), "kind": "abutment", "top": round(cap_top, 2), "ground": round(zg, 2)}
    capb = cap_top - prm["pier_cap_h_m"]
    wall_bot = min(zg + prm["pile_show_m"], capb - 0.3)
    for layer in LAYERS:
        acc.box(layer, CONC, [c[0], c[1], (cap_top + capb) / 2], t * (ht + 0.15), n * (half + 0.2),
                up * (cap_top - capb) / 2)
        acc.box(layer, CONC, [c[0], c[1], (capb + wall_bot) / 2], t * ht, n * half, up * (capb - wall_bot) / 2,
                skip=(1,))
    npile = 5
    for i in range(npile):
        f = -1.0 + 2.0 * i / (npile - 1)
        for row in (-1.0, 1.0):
            q = c + n * f * (half - 0.35) + t * row * (ht - 0.28)
            acc.box("buildings", CONC, [q[0], q[1], (wall_bot + zg - 1.0) / 2], t * prm["pile_m"] / 2,
                    n * prm["pile_m"] / 2, up * (wall_bot - zg + 1.0) / 2, skip=(0, 1))
    acc.box("buildings_low", CONC, [c[0], c[1], (wall_bot + zg - 1.0) / 2], t * ht * 0.8, n * (half - 0.2),
            up * (wall_bot - zg + 1.0) / 2, skip=(0, 1))
    # ice-breaker: sloped concrete wedge on the upstream side
    u = n * upstream_sign
    a0 = c + u * half
    w2 = t * (ht * 0.75)
    hi = np.array([a0[0], a0[1], capb])
    lo = np.array([a0[0], a0[1], zg - 1.0])
    toe = lo + u * prm["icebreaker_m"]
    for layer in LAYERS:
        for sg in (-1.0, 1.0):
            _plate(acc, layer, CONC, _facing([hi + w2 * sg, lo + w2 * sg, toe + w2 * sg], t * sg), both=False)
        acc.quad(layer, CONC, *_facing([hi - w2, hi + w2, toe + w2, toe - w2], up))
    M.box(buf, "collision", "collision_building", c[:2], t[:2], ht, half, zg - 1.0, cap_top, src + ":pier")
    return {"x": round(float(x), 1), "kind": "pier", "top": round(cap_top, 2), "ground": round(zg, 2)}


def apply(w, overrides, zground, log=lambda *a: None) -> dict:
    """Build every truss bridge of the region. Returns the QA report (also stored in w.stats["truss_bridges"])."""
    rep = w.stats.setdefault("truss_bridges", [])
    targets = chains_for(w.net, overrides)
    seen = set()
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        chains = [c for c in w.net.chains if targets.get(c.id) is o]
        if not chains:
            w.net.overrides_stale.append(o["id"])
            rep.append({"id": o["id"], "status": "stale", "why": "no elevated chain on the target ways"})
            continue
        prm = {**DEFAULTS, **(o.get("set") or {})}
        for c in chains:
            if c.id in seen:
                continue
            seen.add(c.id)
            sa, sb = HB._run(c)
            dk = _Deck(c, sa, sb, o.get("first_span_at", "south") == "south")
            spans, scale = span_layout(o, dk.L)
            acc = BM.Acc()
            src = f"truss:{o['id']}"
            removed = 0
            keep = []
            for p in w.buf.parts:
                if p.src == c.id + ":parapet":
                    removed += len(p.T)
                else:
                    keep.append(p)
            w.buf.parts = keep
            east = dk.at(0.0)["n"][0]                         # > 0: the left side (sgn +1) looks east
            ups = (1.0 if east > 0 else -1.0) * (1.0 if o.get("upstream", "east") == "east" else -1.0)
            info = []
            ntruss = [i for i, s in enumerate(spans) if s[2]]
            for i, (x0, x1, truss, panels, rise) in enumerate(spans):
                if not truss:
                    continue
                ends = (i == ntruss[0], i == ntruss[-1])
                tops = {}
                for sgn in (1.0, -1.0):
                    top, bot, xs, dzt = _truss(acc, dk, x0, x1, panels, rise, sgn, prm, ends)
                    tops[sgn] = top
                    for k in range(panels):                   # collision: bottom chord and 1 m of the web above it
                        a, b = bot[k], bot[k + 1]
                        mid = (a + b) / 2
                        M.box(w.buf, "collision", "collision_steel", mid[:2], _unit((b - a)[:2]),
                              float(np.linalg.norm((b - a)[:2])) / 2, prm["bottom_w_m"] / 2,
                              mid[2] - prm["bottom_d_m"] / 2, mid[2] + prm["bottom_d_m"] / 2 + 1.0, src + ":chord")
                braced = _bracing(acc, dk, tops[1.0], tops[-1.0], xs, dzt, prm)
                info.append({"x0": round(x0, 1), "x1": round(x1, 1), "length_m": round(x1 - x0, 2), "panels": panels,
                             "rise_m": round(rise, 2), "braced_panel_points": braced})
            for sgn in (1.0, -1.0):
                _footway(acc, dk, sgn, prm, spans)
            piers = [_pier(acc, w.buf, dk, 0.0, prm, zground, ups, src, abutment=True)]
            for x0, x1, *_ in spans[:-1]:
                piers.append(_pier(acc, w.buf, dk, x1, prm, zground, ups, src))
            piers.append(_pier(acc, w.buf, dk, dk.L, prm, zground, ups, src, abutment=True))
            tris = {}
            for (layer, mat), items in acc.d.items():
                tris[layer] = tris.get(layer, 0) + int(sum(len(it[1]) for it in items))
            acc.flush(w.buf, src)
            w.net.overrides_applied.append({"id": o["id"], "targets": [f"w{x}" for x in o.get("osm_ways", [])]})
            w.bridges.append({"chain": c.id, "span_m": round(dk.L, 1), "piers": len(piers) - 2, "confidence": "medium",
                              "note": f"truss_bridge override {o['id']}: spans from the orthophoto, piers at span joints"})
            rep.append({"id": o["id"], "status": "applied", "chain": c.id, "run_m": round(dk.L, 2),
                        "span_scale": round(scale, 4), "spans": info, "piers": piers, "tris": tris,
                        "generic_parapet_tris_removed": removed, "confidence": o.get("confidence", "WORKING_VALUE")})
            log("truss bridge", o["id"], "chain", c.id, "run", round(dk.L, 1), "tris", tris)
    return {"truss_bridges": rep}
