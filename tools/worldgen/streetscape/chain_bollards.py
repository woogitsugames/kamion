"""ADR 0183: red-white blocking posts with two chains ("słupki biało-czerwone z łańcuchem") and their authored rows.

What the owner's photo P11-063 shows (Dojlidy, Kuronia; research/_incoming/mistral-p11-dojlidy-photos-v2/files):
a row of slim round steel posts in red-white bands along the edge of a paved area, two chains from post to post
(one under the cap, one at mid height), both hanging in a shallow arc, painted in long red and white stretches.

Prototypes (library street_props.glb, ONE material `chain_bollard` = one alpha-clip atlas, so a row is one instanced
draw per prototype and LOD):
  bollard_rw_chain   a post at the origin + the two chains of one bay, running along local +x to the next post
  bollard_rw         the post alone (closes a row; rows with `chain: false`)
LOD0 = 10-sided post, eyelets, chains as crossed alpha cards with a link texture; LOD1 = 5-sided post, each chain one
narrow opaque strip. Collision: one low box per bay.

Placement: override `kind: chain_bollards` in Data/Regions/<id>/overrides.yaml (authored, survives every regeneration):
  - id: <unique>
    kind: chain_bollards
    line_epsg2180: [[x, y], ...]          # one row; or  lines: [{line_epsg2180: [...]}, ...]  for several
    chain: true                            # false = posts only
    reason / sources / confidence / verify # as every override
The row is walked from its first point with posts exactly BAY_M apart (chord), all on the authored line; the last post
may pass the end of the line by less than BAY_M / 2 (the mesh of a bay has one length). A gap = two rows.

Dimensions: nothing in research G5 (ZDM standard 2018) covers this post, so every number below is WORKING_VALUE read
from P11-063 (proportions against the post height) or a common tube / chain class, and says so.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

from . import furniture_textures as FT
from . import props as PP

KIND = "chain_bollards"
MAT = "chain_bollard"
PROTO_BAY = "bollard_rw_chain"
PROTO_POST = "bollard_rw"

# ------------------------------------------------------------------------------------------------ dimensions
POST_D_M = 0.0603       # WORKING_VALUE: the galvanised Ø60.3 mm tube of the ZDM U-12a posts (research G5-010); P11-063
#                         shows a post ~1/16 of its height wide (4-5 px of 72) = 0.06 m, no closer reading possible
POST_H_M = 1.00         # WORKING_VALUE: height above the paving. P11-063 has no object of known size at the row; the
#                         bay / height ratio below is measured, the absolute scale is not
POST_BURIED_M = 0.15    # mesh below the origin (uneven ground), not the real foundation depth
CAP_RISE_M = 0.012      # shallow domed cap, WORKING_VALUE
BAY_M = 2.00            # WORKING_VALUE: P11-063, four posts at x 630 / 750 / 858 / 965 px, 75 -> 63 px tall; with a
#                         phone lens of ~66 deg across 1600 px (f = 1230 px, ASSUMED) the row is 16-20 m away and
#                         3 bays measure 5.9 m -> 1.98 m per bay. Bay / post height = 2.0 holds for any focal length
#                         within +-10 %
# bands from the ground up (z0, z1, red?) - P11-063, post 2 of the crop at 4x: white 30 px, red 60, white 70, red 60,
# white 60 of 280 px from the top
BANDS = ((0.00, 0.22, False), (0.22, 0.43, True), (0.43, 0.68, False), (0.68, 0.89, True), (0.89, 1.00, False))
CHAIN_Z_M = (0.94, 0.46)   # eyelet heights of the upper / lower chain (P11-063: 0.95 and 0.46 of the post), WORKING_VALUE
CHAIN_SAG_M = (0.18, 0.16)  # mid-span sag (P11-063: 50 and 45 px of a 280 px post), WORKING_VALUE
# Chain: 6 mm long-link steel chain class, pitch 42 mm, outer width 24 mm. UNVERIFIED (catalogue values from memory,
# no document in the repository); in the photo the chain is 1-2 px wide, which only bounds it to 2-4 cm.
LINK_WIRE_M = 0.006
LINK_PITCH_M = 0.042
LINK_W_M = 0.024
CARD_W_M = 0.028           # LOD0 card (link width + alpha margin)
STRIP_W_M = 0.012          # LOD1 opaque strip = mean covered width of the link pattern
EYELET_M = (0.014, 0.008, 0.020)
# colour of the chain along a bay (start fraction -> red?), upper / lower. P11-063: red and white stretches of about
# 1-2 m that do not line up with the posts; one fixed pattern per bay is WORKING_VALUE
CHAIN_PAINT = (((0.0, True), (0.5, False)), ((0.0, False), (0.25, True)))

# ------------------------------------------------------------------------------------------------ atlas layout
ATLAS = (256, 512)                      # px (u, v); v up: v = 0 at the ground / chain link centre
PITCHES_PER_V = 16                      # chain columns: the atlas height is 16 link pitches (wraps)
_PX = 1.0 / ATLAS[0]
U_POST = (2 * _PX, 110 * _PX)           # post wrap, 112 px
U_STEEL = 120 * _PX                     # bare galvanised steel (eyelets), centre of a 16 px column
U_LINK = {True: (128 * _PX, 160 * _PX), False: (160 * _PX, 192 * _PX)}       # red / white link cards (alpha)
U_STRIP = {True: (194 * _PX, 222 * _PX), False: (226 * _PX, 254 * _PX)}      # red / white opaque strips (LOD1)

WHITE_SRGB = (224, 223, 216)            # weathered white foil, WORKING_VALUE
RED_SRGB = (176, 24, 22)                # RAL 3020 (FT.RAL3020_SRGB) darkened by weathering, WORKING_VALUE
STEEL_SRGB = (150, 153, 152)
RUST_SRGB = (132, 80, 48)
FILM_SRGB = (140, 132, 118)


# ------------------------------------------------------------------------------------------------ geometry
def catenary(L, sag, n):
    """(x, dz, slope, s) at n + 1 points of a level span L with mid-span sag: dz <= 0 below the supports, s = arc
    length from mid-span."""
    lo, hi = 1e-3, 1e4
    for _ in range(200):
        a = math.sqrt(lo * hi)
        if a * (math.cosh(L / (2 * a)) - 1) > sag:
            lo = a
        else:
            hi = a
    x = np.linspace(0.0, L, n + 1)
    t = (x - L / 2) / a
    return x, a * (np.cosh(t) - 1) - sag, np.sinh(t), a * np.sinh(t)


def _post(m, seg, eyelets):
    r = POST_D_M / 2
    a = np.linspace(0, 2 * math.pi, seg + 1)
    ring = np.column_stack([np.cos(a), np.sin(a), np.zeros(seg + 1)]) * r
    u = U_POST[0] + a / (2 * math.pi) * (U_POST[1] - U_POST[0])
    n = seg + 1
    V = np.concatenate([ring + [0, 0, -POST_BURIED_M], ring + [0, 0, POST_H_M]])
    UV = np.column_stack([np.tile(u, 2), np.repeat([0.002, 0.998], n)])
    T = [(i, i + 1, n + i + 1) for i in range(seg)] + [(i, n + i + 1, n + i) for i in range(seg)]
    m.add(MAT, V, T, UV)
    cap = np.concatenate([[[0, 0, POST_H_M + CAP_RISE_M]], ring[:-1] + [0, 0, POST_H_M]])
    m.add(MAT, cap, [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)],
          np.column_stack([np.full(seg + 1, sum(U_POST) / 2), np.full(seg + 1, 0.996)]))
    if eyelets:
        hx, hy, hz = (v / 2 for v in EYELET_M)
        for z in CHAIN_Z_M:
            for sx in (-1, 1):
                c = np.array([sx * (r + hx - 0.002), 0, z])
                P = [c + [kx * hx, ky * hy, kz * hz] for kz in (-1, 1) for ky in (-1, 1) for kx in (-1, 1)]
                for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
                    m.add(MAT, [P[i] for i in f], [(0, 1, 2), (0, 2, 3)], np.tile([U_STEEL, 0.5], (4, 1)))


def _chains(m, n, lod0):
    r = POST_D_M / 2
    x0 = r + EYELET_M[0] - 0.002
    L = BAY_M - 2 * x0
    vscale = 1.0 / (PITCHES_PER_V * LINK_PITCH_M)
    for z_att, sag, paint in zip(CHAIN_Z_M, CHAIN_SAG_M, CHAIN_PAINT):
        x, dz, slope, s = catenary(L, sag, n)
        P = np.column_stack([x0 + x, np.zeros(n + 1), z_att + dz])
        tl = np.sqrt(1 + slope ** 2)
        up = np.column_stack([-slope / tl, np.zeros(n + 1), 1 / tl])        # in the chain plane, across the chain
        side = np.array([0.0, 1.0, 0.0])
        v = s * vscale
        for j in range(n):
            f = (j + 0.5) / n
            red = [c for f0, c in paint if f >= f0][-1]
            u0, u1 = (U_LINK if lod0 else U_STRIP)[red]
            u0, u1 = u0 + _PX, u1 - _PX
            w = (CARD_W_M if lod0 else STRIP_W_M) / 2
            cards = ((up, 0.0), (np.tile(side, (n + 1, 1)), 1.0 / PITCHES_PER_V)) if lod0 else ((up, 0.0),)
            for d, dv in cards:
                m.add(MAT, [P[j] - d[j] * w, P[j] + d[j] * w, P[j + 1] + d[j + 1] * w, P[j + 1] - d[j + 1] * w],
                      [(0, 1, 2), (0, 2, 3)],
                      [[u0, v[j] + dv], [u1, v[j] + dv], [u1, v[j + 1] + dv], [u0, v[j + 1] + dv]])


def bay():
    """Post at the origin + both chains to the next post at local x = BAY_M (that post is the next instance)."""
    m, l1, col = PP.Mesh(), PP.Mesh(), PP.Mesh()
    _post(m, 10, True)
    _chains(m, 8, True)
    _post(l1, 5, False)
    _chains(l1, 4, False)
    col.box("collision_steel", [BAY_M / 2, 0, POST_H_M / 2], BAY_M / 2 + 0.04, 0.04, POST_H_M / 2)
    return m, l1, col


def post():
    m, l1, col = PP.Mesh(), PP.Mesh(), PP.Mesh()
    _post(m, 10, True)
    _post(l1, 5, False)
    col.tube("collision_steel", [0, 0, 0], [0, 0, POST_H_M], 0.04, None, 6)
    return m, l1, col


def prototypes():
    return {PROTO_BAY: bay(), PROTO_POST: post()}


# ------------------------------------------------------------------------------------------------ texture
def _noise(rng, shape, sigma):
    f = gaussian_filter(rng.random(shape), sigma, mode="wrap")
    return (f - f.mean()) / max(1e-9, f.std())


def _post_texture(rng, w, h):
    z = ((1 - (np.arange(h) + 0.5) / h) * POST_H_M)[:, None]
    ang = ((np.arange(w) + 0.5) / w * 2 * math.pi)[None, :]
    white, red = np.array(WHITE_SRGB, float), np.array(RED_SRGB, float)
    # foil edges are cut by hand: each band boundary wanders a few mm around the post
    wob = 0.004 * np.sin(ang * 2 + 1.3) + 0.0025 * np.sin(ang * 5 + 0.4)
    is_red = np.zeros((h, w), bool)
    for k, (z0, z1, r) in enumerate(BANDS):
        if r:
            is_red |= (z >= z0 + wob * math.cos(k)) & (z < z1 + wob * math.sin(k + 1.0))
    rgb = np.where(is_red[..., None], red, white)
    rgb = rgb * (1 + 0.025 * _noise(rng, (h, w), 1.2))[..., None]
    rgb = rgb * (1 + 0.05 * np.cos(ang - 2.2))[..., None]                   # one side bleached by the sun
    # road film at the foot, heavier on one side (splash comes from the carriageway side)
    film = np.clip(1 - z / 0.22, 0, 1) ** 1.5 * (0.5 + 0.5 * np.sin(ang / 2 + 0.6) ** 2) * 0.6
    film = film * np.clip(1 + 0.35 * _noise(rng, (h, w), 3.0), 0.3, 1.5)
    rgb = rgb * (1 - film[..., None]) + np.array(FILM_SRGB, float) * film[..., None]
    # chips down to the zinc: bumper height and the foil edges, not all over
    steel = np.array(STEEL_SRGB, float)
    edges = [b[0] for b in BANDS[1:]]
    for k in range(16):
        zc = rng.choice(edges) + rng.normal(0, 0.012) if k < 9 else rng.uniform(0.30, 0.62)
        ac = rng.uniform(0, 2 * math.pi)
        rz, ra = rng.uniform(0.002, 0.007), rng.uniform(0.05, 0.22)
        da = np.abs((ang - ac + math.pi) % (2 * math.pi) - math.pi)
        mk = np.clip(1.4 - np.sqrt(((z - zc) / rz) ** 2 + (da / ra) ** 2), 0, 1)
        mk = np.clip(mk * 3, 0, 1)[..., None]
        rgb = rgb * (1 - mk) + (steel * (0.85 if k % 3 else 0.7)) * mk
    # rust runs under the four eyelets (chain direction = angle 0 and pi)
    rust = np.array(RUST_SRGB, float)
    for zc in CHAIN_Z_M:
        for ac in (0.0, math.pi):
            da = np.abs((ang - ac + math.pi) % (2 * math.pi) - math.pi)
            below = zc - z
            mk = np.exp(-(da / 0.16) ** 2) * np.clip(below / 0.01, 0, 1) * np.clip(1 - below / 0.11, 0, 1) * 0.38
            rgb = rgb * (1 - mk[..., None]) + rust * mk[..., None]
    rgb = rgb * np.where(z > POST_H_M - 0.012, 0.9, 1.0)[..., None]         # shaded cap edge
    return rgb


def _link_texture(base, w, h, ss=4):
    """Alpha card of the chain seen across: links lying in the card plane (rings) alternate with links seen on edge
    (bars). Supersampled, straight (non-premultiplied) colour with the paint colour under the transparent texels."""
    W, H = w * ss, h * ss
    x = (((np.arange(W) + 0.5) / W - 0.5) * CARD_W_M)[None, :]
    y = ((1 - (np.arange(H) + 0.5) / H) * PITCHES_PER_V * LINK_PITCH_M)[:, None]
    t, d = LINK_PITCH_M, LINK_WIRE_M
    half = (t + 2 * d) / 2                                  # outer half length of a link
    rc = (LINK_W_M - d) / 2                                 # centre-line radius of the round ends
    yf = (y + t) % (2 * t) - t                              # to the nearest in-plane link centre
    ye = y % (2 * t) - t                                    # to the nearest on-edge link centre
    ring = np.abs(np.hypot(x, np.maximum(np.abs(yf) - (half - d / 2 - rc), 0)) - rc) / (d / 2)
    bar = np.hypot(x, np.maximum(np.abs(ye) - (half - d / 2), 0)) / (d / 2)
    a = ((ring <= 1) | (bar <= 1)).astype(float)
    dist = np.where(bar <= 1, bar, ring)
    shade = np.where(bar <= 1, 0.86, 1.0) * (1 - 0.38 * np.clip(dist, 0, 1) ** 2)       # round wire
    worn = np.clip((np.abs(yf) - (half - 2.2 * d)) / d, 0, 1) * (ring <= 1) * (bar > 1)   # paint rubbed off in the crowns
    rgb = np.asarray(base, float) * shade[..., None]
    rgb = rgb * (1 - 0.6 * worn[..., None]) + np.array(STEEL_SRGB, float) * 0.8 * (0.6 * worn[..., None])
    rgb = (rgb * a[..., None]).reshape(h, ss, w, ss, 3).sum((1, 3))
    asum = a.reshape(h, ss, w, ss).sum((1, 3))
    rgb = np.where(asum[..., None] > 0, rgb / np.maximum(asum, 1)[..., None], np.asarray(base, float) * 0.8)
    return rgb, asum / (ss * ss)


def texture():
    """The `chain_bollard` atlas (RGBA, sRGB): post wrap, bare steel, red / white link cards, red / white strips."""
    rng = np.random.default_rng(183)
    w, h = ATLAS
    im = np.zeros((h, w, 4))
    im[..., 3] = 255
    im[:, :112, :3] = _post_texture(rng, 112, h)
    im[:, 112:128, :3] = np.array(STEEL_SRGB, float) * (1 + 0.04 * _noise(rng, (h, 16), 1.5))[..., None]
    y = ((1 - (np.arange(h) + 0.5) / h) * PITCHES_PER_V)[:, None]
    for red in (True, False):
        base = RED_SRGB if red else WHITE_SRGB
        c0 = int(round(U_LINK[red][0] * w))
        rgb, a = _link_texture(base, 32, h)
        im[:, c0:c0 + 32, :3] = rgb
        im[:, c0:c0 + 32, 3] = a * 255
        c1 = int(round(U_STRIP[red][0] * w)) - 2
        strip = np.asarray(base, float) * (0.74 + 0.10 * np.cos(2 * math.pi * y))      # link rhythm, no alpha
        im[:, c1:c1 + 32, :3] = np.broadcast_to(strip[:, None, :] if strip.ndim == 2 else strip, (h, 32, 3))
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8), "RGBA")


def textures():
    return {MAT: texture()}


# ------------------------------------------------------------------------------------------------ placement
def walk(P, bay=BAY_M):
    """Post positions of a row along the polyline P: the first point, then every next post exactly `bay` (chord) from
    the previous one on the line ahead of it. Past the last crossing: one more post toward the end point when at
    least bay / 2 of line is left (it passes the end by < bay / 2); a line shorter than bay / 2 gives one bay anyway."""
    P = np.asarray(P, float)
    if len(P) < 2:
        return P.copy()
    out = [P[0]]
    seg, t0 = 0, 0.0
    while True:
        cur, hit = out[-1], None
        for k in range(seg, len(P) - 1):
            a, d = P[k], P[k + 1] - P[k]
            dd = float(d @ d)
            if dd < 1e-12:
                continue
            f = a - cur
            b, c = 2 * float(f @ d), float(f @ f) - bay * bay
            disc = b * b - 4 * dd * c
            if disc < 0:
                continue
            lo = t0 + 1e-9 if k == seg else 0.0
            for t in sorted(((-b - math.sqrt(disc)) / (2 * dd), (-b + math.sqrt(disc)) / (2 * dd))):
                if lo <= t <= 1.0 + 1e-12:
                    hit = (k, min(t, 1.0))
                    break
            if hit:
                break
        if hit is None:
            rest = P[-1] - cur
            d = float(np.hypot(*rest))
            if d >= bay / 2 or len(out) == 1:
                u = rest / d if d > 1e-9 else (P[-1] - P[-2]) / np.hypot(*(P[-1] - P[-2]))
                out.append(cur + u * bay)
            return np.array(out)
        seg, t0 = hit
        out.append(P[seg] + t0 * (P[seg + 1] - P[seg]))


def lines_of(o, origin):
    """Local (E, N) polylines of one override: `line_epsg2180` or `lines: [{line_epsg2180}]`."""
    raw = [o["line_epsg2180"]] if o.get("line_epsg2180") else [ln.get("line_epsg2180") for ln in o.get("lines", [])]
    return [np.asarray(r, float) - np.asarray(origin, float) if r else None for r in raw]


def apply(pl, overrides, origin, report):
    """Places the rows of every `kind: chain_bollards` override. Each bay instance stands at its post (origin on the
    ground there, Placer seat) with local +x toward the next post; the bay is level, so the chain meets the next post
    `step` higher or lower than its eyelet where the ground rises - reported per row (max_step_m)."""
    rep = {"applied": [], "stale": []}
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        chain = bool(o.get("chain", True))
        lines = lines_of(o, origin)
        if not lines:
            rep["stale"].append(f"{o.get('id')}: no line_epsg2180")
        for li, P in enumerate(lines):
            if P is None or P.ndim != 2 or len(P) < 2 or P.shape[1] != 2 or not np.isfinite(P).all():
                rep["stale"].append(f"{o.get('id')}:{li}: needs >= 2 [x, y] points")
                continue
            Q = walk(P)
            zs = []
            for k, q in enumerate(Q):
                last = k == len(Q) - 1
                d = Q[k] - Q[k - 1] if last else Q[k + 1] - Q[k]
                proto = PROTO_BAY if chain and not last else PROTO_POST
                zs.append(pl.add(proto, q, math.atan2(d[1], d[0]), src=f"override:{o['id']}:{li}:{k}", group=KIND))
            rep["applied"].append({
                "id": o["id"], "line": li, "posts": len(Q), "bays": len(Q) - 1 if chain else 0,
                "length_m": round(float(np.hypot(*np.diff(P, axis=0).T).sum()), 2),
                "end_shift_m": round(float(np.hypot(*(Q[-1] - P[-1]))), 2),
                "max_step_m": round(float(np.max(np.abs(np.diff(zs)))) if len(zs) > 1 else 0.0, 3)})
    if rep["applied"] or rep["stale"]:
        report["chain_bollards"] = rep
    return rep
