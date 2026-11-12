"""Roundabout / junction plantings the data does not describe (authored override `kind: plantings`,
Data/Regions/<id>/overrides.yaml; review r6 W-N12).

OSM has no barrier=hedge / landuse=flowerbed in tile C, so beds are traced from the GUGiK 2024 orthophoto (0.25 m)
and checked against the CC0 photo of Rondo Pamięci Bieżeństwa (20201102_152339, docs/REFERENCES.md). The override
carries plain geometry in EPSG:2180 plus what grows there; everything else is rule:

  hedges   `beds[].ring` (+ `plant`: berberis_red | privet | hornbeam | thuja, SPECIES): clipped hedge inset `rim_m`
           from the traced bed edge so a lawn rim stays. ADR 0049 addendum (the r6 masses read as solid boxes): a dark
           opaque core (hedge_<sp>, hedge_foliage set; berberis uses a nested alpha leaf layer, ADR 0109), an alpha leaf shell 5 cm outside it (hedge_shell_<sp>, open
           below 14 % of the height so the foot reads dark), one lump / crown per plant along the perimeter with thin or
           missing plants as dips, a lumpy crown, and loose-shoot alpha cards (hedge_sprig_<sp>) on the top edge, the
           upper sides and the top that break the silhouette. Textures: streetscape.hedge_textures.
  osm      barrier=hedge ways (osm_hedges): the same hedge along the line, cut at roads and opened at gates.
  islands  `islands[].at`: the hole of the road footprint (kerb-enclosed island) containing the point is filled up
           to its kerb top: `fill: paving` flush with the kerb top (sidewalk_paving), `fill: soil` 3 cm below it
           (bed_soil) with optional sparse shrubs (`shrubs`, clumps 0.8-1.4 m, 0.5-0.7 m high, never under a deck:
           piers stand there). Before, the island interior was the conformed terrain at road level and the kerb ring
           read as an empty concrete tub.
A target that no longer matches (no island hole at the point) is reported as stale, never silently dropped.
Heights / sizes WORKING_VALUE (typical Białystok roundabout planting, not measured).
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import Point, Polygon

HEDGE_H = (0.5, 0.65)       # m, clipped berberis hedge (review r7 N-4: low 0.5-0.7 m band, CC0 Bieżeństwa photo)
BAND_M = (1.1, 1.4)         # m, width of the clipped band laid along a traced bed (r7 N-4: narrow strip, not the bed)
SOIL_BELOW_KERB = 0.03      # m, bed soil level under the kerb top
SHRUB_R = (0.45, 0.9)        # m, clump radius
ISLAND_MAX_M2 = 2500.0      # roundabout centre islands are holes too


def _h(*key) -> float:
    s = hashlib.blake2b(":".join(str(k) for k in key).encode(), digest_size=8).digest()
    return int.from_bytes(s, "little") / 2.0 ** 64


def _ring_normals(R):
    """outward unit normals per vertex of a CCW ring (average of the two edge normals)"""
    d_prev = R - np.roll(R, 1, 0)
    d_next = np.roll(R, -1, 0) - R
    def nrm(d):
        n = np.column_stack([d[:, 1], -d[:, 0]])
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    n = nrm(d_prev) + nrm(d_next)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def _ccw_ring(poly, step):
    poly = shapely.segmentize(poly, step)
    R = np.asarray(poly.exterior.coords)[:-1]
    a = 0.5 * np.sum(R[:, 0] * np.roll(R[:, 1], -1) - np.roll(R[:, 0], -1) * R[:, 1])
    return R if a > 0 else R[::-1]


def _fill(ring, spacing):
    from roads.meshing import _delaunay_fill
    from roads.geom import ear_clip
    res = _delaunay_fill(ring, spacing)
    if res is not None:
        return res
    return ring.copy(), np.array(ear_clip(ring))


# species presets: tex = hedge_textures species, h = clipped height range (m), plant = plant spacing along the hedge (m),
# bulge = outward lump per plant (m), dome = top relief as a share of h, gap_p = share of thin / missing plants (dips),
# sigma = plant crown width / spacing, sprig = mean spacing of loose shoots on the top edge (m), sprig_wh = shoot card
# width / height ranges (m). Typical Polish clipped hedges (WORKING_VALUE, general horticultural knowledge).
SPECIES = {
    # low roundabout berberis is clipped into a cushion (CC0 Bieżeństwa photo): barrel sides, wide rounded shoulder
    # ADR 0060 (review r7 N-4, "red sofa"): the r7 cushion (barrel sides, 0.4 m shoulder, 0.08 m lump per plant) read
    # as a couch of sausages. The photo shows a low band clipped to a straight, slightly battered side and a flat top
    # with a small rounded arris; shoots grow out lighter (copper) above the cut. Lumps 0.015 m, dome 0.05.
    "berberis_red": dict(tex="berberis", h=HEDGE_H, plant=(0.55, 0.85), bulge=0.025, dome=0.10, gap_p=0.09, sigma=0.5,
                         sprig=0.13, sprig_wh=((0.16, 0.28), (0.10, 0.20)), prof="clipped", band=BAND_M,
                         local_top=True, leaf_core=True, offset_rings=True),
    "privet": dict(tex="privet", h=(1.2, 1.7), plant=(0.45, 0.65), bulge=0.08, dome=0.12, gap_p=0.10, sigma=0.36,
                   sprig=0.30, sprig_wh=((0.14, 0.24), (0.10, 0.18))),
    "hornbeam": dict(tex="hornbeam", h=(1.4, 2.0), plant=(0.5, 0.7), bulge=0.08, dome=0.10, gap_p=0.09, sigma=0.38,
                     sprig=0.34, sprig_wh=((0.16, 0.28), (0.12, 0.22))),
    "thuja": dict(tex="thuja", h=(1.6, 2.2), plant=(0.6, 0.8), bulge=0.10, dome=0.24, gap_p=0.09, sigma=0.27,
                  sprig=0.40, sprig_wh=((0.12, 0.2), (0.12, 0.2))),
}
# cross-sections (inset m, height share, bulge share), foot first
PROFILES = {
    "box": [(-0.04, -0.03, 0.2), (0.0, 0.45, 0.8), (0.05, 0.86, 1.0), (0.14, 0.97, 0.7), (0.24, 1.0, 0.4)],
    "cushion": [(-0.03, -0.03, 0.2), (-0.04, 0.32, 0.8), (0.0, 0.62, 1.0), (0.09, 0.84, 0.9), (0.22, 0.95, 0.6),
                (0.40, 1.0, 0.3)],
    # clipped low band (ADR 0060): straight side with ~6 deg batter, 0.08-0.12 m rounded arris, flat top
    "clipped": [(-0.02, -0.03, 0.3), (0.0, 0.30, 0.6), (0.03, 0.62, 0.8), (0.07, 0.82, 0.8), (0.14, 0.94, 0.6),
                (0.24, 1.0, 0.4)],
}
SHELL_D = 0.05              # m, alpha leaf shell outside the opaque core
SHELL_FOOT = 0.14           # share of h below which the shell is open: dark stems / core at the base


def species(name):
    return SPECIES.get(name or "berberis_red", SPECIES["berberis_red"])


def hedge_mats(sp):
    t = species(sp)["tex"]
    return f"hedge_{t}", f"hedge_shell_{t}", f"hedge_sprig_{t}"


def _plants(per, P, key, S):
    """per-vertex outward bulge (m) and top relief (share of h) from individual clipped plants along the perimeter"""
    s, i = 0.0, 0
    pos, amp, top = [], [], []
    while s < P - 0.2:
        sp = S["plant"][0] + _h(key, "ps", i) * (S["plant"][1] - S["plant"][0])
        pos.append(s)
        gap = _h(key, "gap", i) < S["gap_p"]
        amp.append(-1.2 if gap else 0.35 + 0.65 * _h(key, "pa", i))
        top.append(-1.6 if gap else 0.55 + 0.45 * _h(key, "pt", i))
        s += sp
        i += 1
    pos, amp, top = np.array(pos), np.array(amp), np.array(top)
    ds = np.abs(per[:, None] - pos[None, :])
    ds = np.minimum(ds, P - ds)
    sig = S["sigma"] * (P / max(len(pos), 1))
    w = np.exp(-0.5 * (ds / sig) ** 2)
    return (w * amp).sum(1) * S["bulge"], (w * top).sum(1)


def _sprig_cards(buf, mat, B, N, z, key, S, src, tilt=(0.15, 0.7), share=1.0):
    """loose shoots: double-sided alpha cards rooted 25 % inside the shell, leaning outward (N), random yaw"""
    V, UV, T = [], [], []
    for j in range(len(B)):
        if _h(key, "su", j) > share:
            continue
        w = S["sprig_wh"][0][0] + _h(key, "sw", j) * (S["sprig_wh"][0][1] - S["sprig_wh"][0][0])
        hh = S["sprig_wh"][1][0] + _h(key, "sh", j) * (S["sprig_wh"][1][1] - S["sprig_wh"][1][0])
        th = tilt[0] + _h(key, "st", j) * (tilt[1] - tilt[0])
        n = np.array([N[j][0], N[j][1], 0.0])
        n /= max(np.linalg.norm(n), 1e-9)
        up = np.array([0.0, 0.0, 1.0]) * math.cos(th) + n * math.sin(th)
        t = np.array([-n[1], n[0], 0.0])
        yaw = (_h(key, "sy", j) - 0.5) * 1.4
        a = t * math.cos(yaw) + n * math.sin(yaw)
        a[2] = 0.0
        a /= max(np.linalg.norm(a), 1e-9)
        base = np.array([B[j][0], B[j][1], z[j]]) - up * 0.25 * hh
        q = [base - a * w / 2, base + a * w / 2, base + a * w / 2 + up * hh, base - a * w / 2 + up * hh]
        cell = int(_h(key, "sc", j) * 4) % 4
        u0, v0 = (cell % 2) * 0.5, 0.5 - (cell // 2) * 0.5      # UV v up (image row 0 = top cells)
        flip = _h(key, "sf", j) < 0.5
        us = [u0 + 0.5, u0] if flip else [u0, u0 + 0.5]
        k = len(V)
        V += q
        UV += [(us[0], v0), (us[1], v0), (us[1], v0 + 0.5), (us[0], v0 + 0.5)]
        T += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
    if T:
        buf.add("furniture", mat, np.array(V), np.array(UV), np.array(T), src=src)
    return len(T)


def _crown(P, ph, lam):
    """2-D lumpy relief (-1..1) of the clipped top (plant crowns ~lam apart)"""
    x, y = P[:, 0], P[:, 1]
    r = 0.0
    for k, (ax, ay) in enumerate(((1.0, 0.3), (-0.4, 1.0), (0.7, -0.8))):
        r = r + np.sin((ax * x + ay * y) * 6.283 / (lam * (0.9 + 0.15 * k)) + ph[k])
    return r / 3.0


def _local_top_height(points, boundary, heights):
    """Continuous clipped-plant height, shared by the core and the leaf shell.

    Inverse-distance weights retain local dips and approach the authored edge
    heights without the medial-axis jumps of a nearest-edge lookup. No geometry
    is added; this only replaces the old global median on existing top vertices.
    """
    d2 = ((points[:, None, :] - boundary[None, :, :]) ** 2).sum(-1)
    weights = 1.0 / np.maximum(d2, .01 ** 2)
    return (weights @ heights) / weights.sum(1)


def _offset_ring(poly, inset, count, anchor):
    """Sample a real polygon offset with stable CCW winding and start point.

    Normal displacement can cross itself at the small corners of a traced bed.
    Do not repair such a ring after the fact or silently discard polygon pieces.
    """
    from shapely.geometry import LineString
    offset = poly.buffer(-inset, quad_segs=4)
    if offset.geom_type != "Polygon" or offset.is_empty or not offset.is_valid or len(offset.interiors):
        raise ValueError(f"Hedge offset {inset:.4f} m is not one valid polygon")
    boundary = _ccw_ring(offset, max(offset.length, 1.0))
    line = LineString(np.vstack([boundary, boundary[:1]]))
    start = line.project(Point(anchor))
    at = (start + np.arange(count) * line.length / count) % line.length
    result = shapely.get_coordinates(shapely.line_interpolate_point(line, at))
    if not Polygon(result).is_valid:
        raise ValueError("Sampled hedge offset self-intersects")
    return result


def hedge_mass(buf, poly, zground, key, h=None, src="", plant="berberis_red", stats=None):
    """Clipped hedge over plan polygon `poly` (local metres) standing on zground (review r6 W-N12, ADR 0049 addendum):
    an inner layer (opaque for most species, leaf alpha for berberis), an alpha leaf shell SHELL_D outside it (silhouette
    and surface broken into leaves, open below SHELL_FOOT so the base reads dark), per-plant lumps and dips along the
    perimeter (thin / missing plants), a lumpy crown and loose shoot cards on the top edge, sides and top."""
    from .hedge_textures import HEDGE_TILE_M
    S = species(plant)
    core_m, shell_m, sprig_m = hedge_mats(plant)
    leaf_core = S.get("leaf_core", False)
    core_draw_m = shell_m if leaf_core else core_m
    h = h if h is not None else S["h"][0] + _h(key, "h") * (S["h"][1] - S["h"][0])
    offset_rings = S.get("offset_rings", False)
    R = (_offset_ring(poly, 0.0, max(16, math.ceil(poly.length / 0.3)),
                      np.asarray(poly.exterior.coords)[0]) if offset_rings
         else _ccw_ring(poly.buffer(0), 0.3))
    if len(R) < 3:
        return 0
    N = _ring_normals(R)
    zg = zground(R[:, 0], R[:, 1])
    per = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(np.vstack([R, R[:1]]), axis=0).T))])[:-1]
    P = float(per[-1] + np.hypot(*(R[0] - R[-1])))
    ph = (_h(key, "p1") * 6.283, _h(key, "p2") * 6.283, _h(key, "p3") * 6.283)
    bulge, topm = _plants(per, P, key, S)
    bulge = bulge + 0.015 * np.sin(per / 0.21 + ph[2])
    hl = np.maximum(h * (1.0 + S["dome"] * (topm - 0.8)), 0.45 * h)      # local edge height per vertex
    inr = 2.0 * poly.area / max(poly.length, 1e-6)
    k = min(1.0, 0.8 * inr / max(d for d, _, _ in PROFILES[S.get("prof", "box")]))
    # (inset m, height share, bulge share): clipped = steep sides, rounded shoulder, flat-ish top
    prof = PROFILES[S.get("prof", "box")]
    n = len(R)
    nt = 0

    def rings(R0, hh, prof_, sel=slice(None), inset=0.0):
        if not offset_rings:
            return [(R0[sel] + N[sel] * (b * bulge[sel] - d * k)[:, None], zg[sel] + f * hh[sel]) for d, f, b in prof_]
        result = []
        for d, f, b in prof_:
            base = _offset_ring(poly, inset + d * k, len(R), R[0])[sel]
            normals = _ring_normals(base)
            # Keep small per-plant variation only while the outline stays valid.
            for scale in (1.0, 0.5, 0.0):
                points = base + normals * (scale * b * bulge[sel])[:, None]
                if Polygon(points).is_valid:
                    break
            else:
                raise ValueError("Hedge plant variation self-intersects")
            ground = zground(points[:, 0], points[:, 1])
            result.append((points, ground + f * hh[sel]))
        return result

    def strip(rg, mat, UV):
        n = len(rg[0][0])
        V = np.vstack([np.column_stack([Pp, z]) for Pp, z in rg])
        T = []
        for kk in range(len(rg) - 1):
            b0, b1 = kk * n, (kk + 1) * n
            for i in range(n):
                i1 = (i + 1) % n
                T += [(b0 + i, b0 + i1, b1 + i1), (b0 + i, b1 + i1, b1 + i)]
        buf.add("furniture", mat, V, UV, np.array(T), src=src)
        return len(T)

    # ADR0109: both tops follow the same full-resolution edge field. A flat
    # interior core could previously protrude through a missing-plant dip, and
    # the shell's global median made a sharp ridge next to its undulating edge.
    top_xy, top_z = rings(R, hl, prof)[-1]
    top_h = top_z - zground(top_xy[:, 0], top_xy[:, 1])
    local_top = S.get("local_top", False)  # photo-calibrated roundabout berberis only
    # core: inset and lowered by SHELL_D, dark interior material (modulation set hedge_foliage)
    # (half the perimeter vertices: it only shows through the leaf gaps; 1.3 x SHELL_D keeps the chords inside)
    cs = slice(None, None, 2) if n >= 16 else slice(None)
    core = rings(R - N * 1.3 * SHELL_D, hl - SHELL_D, prof, cs, inset=1.3 * SHELL_D)
    nc = len(core[0][0])
    core_uv = np.column_stack([np.tile(per[cs], len(core)),
                               np.concatenate([np.full(nc, f * h) for _, f, _ in prof])])
    # ADR 0109: leaf-size UV and a separate phase on the inner berberis layer.
    if leaf_core:
        core_uv = core_uv / HEDGE_TILE_M + np.array([0.37, 0.61])
    nt += strip(core, core_draw_m, core_uv)
    try:
        P2, Tt = _fill(core[-1][0], 1.0)
        zt = zground(P2[:, 0], P2[:, 1])
        z2 = (zt + _local_top_height(P2, top_xy, top_h) - 0.5 * S["dome"] * h - SHELL_D if local_top
              else zt + h * (1.0 - 0.6 * S["dome"]) - SHELL_D)
        z2[:nc] = core[-1][1]
        core_top_uv = P2 / HEDGE_TILE_M + np.array([0.37, 0.61]) if leaf_core else P2.copy()
        buf.add("furniture", core_draw_m, np.column_stack([P2, z2]), core_top_uv, Tt, src=src)
        nt += len(Tt)
    except Exception:
        if offset_rings:
            raise  # a photographed bed must not silently lose its inner cap
    # shell: open foot; UV in shell tiles with a per-hedge offset / rotation (no aligned repeats between beds)
    sprof = [(0.02, SHELL_FOOT, 0.6)] + prof[1:]
    shell = rings(R, hl, sprof)
    uo, vo = _h(key, "uo"), _h(key, "vo")
    nt += strip(shell, shell_m, np.column_stack([
        np.tile(per / HEDGE_TILE_M + uo, len(shell)),
        np.concatenate([(z - zg) / HEDGE_TILE_M + vo for _, z in shell])]))
    stop = shell[-1][0]
    try:
        P2, Tt = _fill(stop, 0.6)
        zt = zground(P2[:, 0], P2[:, 1])
        z2 = np.empty(len(P2))
        z2[:n] = shell[-1][1]
        if len(P2) > n:
            inner = P2[n:]
            dmin = np.sqrt(((inner[:, None, :] - stop[None, :, :]) ** 2).sum(-1).min(1))
            lam = 0.65 * (S["plant"][0] + S["plant"][1])
            top = _local_top_height(inner, top_xy, top_h) if local_top else float(np.median(hl))
            z2[n:] = (zt[n:] + top + 0.035 * np.minimum(dmin / 0.5, 1.0)
                      + 0.5 * S["dome"] * h * _crown(inner, ph, lam))
        ang = _h(key, "ua") * 6.283
        c, s_ = math.cos(ang), math.sin(ang)
        UVt = np.column_stack([c * P2[:, 0] - s_ * P2[:, 1], s_ * P2[:, 0] + c * P2[:, 1]]) / HEDGE_TILE_M
        buf.add("furniture", shell_m, np.column_stack([P2, z2]), UVt, Tt, src=src)
        nt += len(Tt)
        if len(P2) > n:            # loose shoots on the crown, ~1.4 per m2 (fill spacing 0.6 m)
            sel = np.array([j for j in range(len(P2) - n) if _h(key, "tc", j) < 0.45], int)
            if len(sel):
                a2 = np.array([_h(key, "ta", j) * 6.283 for j in sel])
                nt += _sprig_cards(buf, sprig_m, P2[n:][sel], np.column_stack([np.cos(a2), np.sin(a2)]),
                                   z2[n:][sel], (*key, "top"), S, src, tilt=(0.0, 0.35))
    except Exception:
        if offset_rings:
            raise  # retain the original failure-tolerant path for other species
    # loose shoots along the top edge (shoulder ring) and a few on the upper sides: ragged silhouette
    idx, s, j = [], 0.0, 0
    while s < P:
        idx.append(int(np.searchsorted(per, s)) % n)
        s += S["sprig"] * (0.5 + _h(key, "ss", j))
        j += 1
    idx = np.array(idx, int)
    # clipped band: edge shoots lean further out (ADR 0060: upright cards read as a dark seam along the arris)
    etilt = (0.5, 1.1) if S.get("prof") == "clipped" else (0.2, 0.8)
    nt += _sprig_cards(buf, sprig_m, shell[-2][0][idx], N[idx], shell[-2][1][idx], (*key, "edge"), S, src, tilt=etilt)
    # clipped band: few shoots on the side (a straight cut face, r7 N-4), cushion / box: 35 %
    nt += _sprig_cards(buf, sprig_m, shell[-3][0][idx] + N[idx] * 0.02, N[idx], shell[-3][1][idx] - 0.12 * h,
                       (*key, "side"), S, src, tilt=(1.0, 1.35), share=0.12 if S.get("prof") == "clipped" else 0.35)
    if stats is not None:
        stats["tris"] = stats.get("tris", 0) + nt
    return 1


def osm_hedges(buf, src, origin, roads_poly, zground, report):
    """OSM barrier=hedge ways -> clipped hedges, cut at the road footprint and opened at every barrier=gate /
    swing_gate / sliding_gate / lift_gate or entrance=* node within 1 m of the line (gap = `width` tag, else 1.2 m
    wicket, 4 m for a sliding or vehicle gate). Species from species / genus tags (berberis, privet, hornbeam, thuja),
    leaf_type=needleleaved -> thuja, else privet (the commonest clipped fence hedge in Polish towns). Width from
    `width`, height from `height`, else the species ranges. Tile C has none (ADR 0049); unit-tested."""
    from shapely.geometry import LineString
    rep = {"ways": 0, "m": 0.0, "gaps": 0, "hedges": 0}
    ways = [f for f in src.get("osm", {}).get("ways", []) if f["tags"].get("barrier") == "hedge"]
    if not ways:
        report["osm_hedges"] = rep
        return rep
    ox, oy = float(origin[0]), float(origin[1])
    gates = []
    for nd in src["osm"].get("nodes", []):
        t = nd["tags"]
        if t.get("barrier") in ("gate", "swing_gate", "sliding_gate", "lift_gate") or t.get("entrance"):
            x, y = nd["geometry"]["coordinates"][:2]
            veh = t.get("barrier") in ("sliding_gate", "lift_gate") or t.get("motor_vehicle") in ("yes", "private", "destination")
            wdt = _num(t.get("width")) or (4.0 if veh else 1.2)
            gates.append(Point(x - ox, y - oy).buffer(wdt / 2))
    cutter = roads_poly.buffer(0.4) if roads_poly is not None else None
    for f in ways:
        t = f["tags"]
        sp = _hedge_species(t)
        line = LineString(np.asarray(f["geometry"]["coordinates"], float)[:, :2] - [ox, oy])
        g = line.difference(cutter) if cutter is not None else line
        for gp in gates:
            if gp.centroid.distance(line) < 1.0:
                g = g.difference(gp)
                rep["gaps"] += 1
        rep["ways"] += 1
        key0 = f"osm:way/{f.get('osm_way')}:{f.get('part', 0)}"
        wdt = _num(t.get("width")) or (0.5 + 0.3 * _h(key0, "w") if sp == "berberis_red" else 0.7 + 0.4 * _h(key0, "w"))
        for pi, part in enumerate(getattr(g, "geoms", [g])):
            if part.geom_type != "LineString" or part.length < 1.0:
                continue
            # clipped square ends at gate posts / kerbs, corners softened (no rounded tongue into the opening)
            poly = part.buffer(wdt / 2, cap_style="flat").buffer(-0.12).buffer(0.12, quad_segs=2)
            rep["hedges"] += hedge_mass(buf, poly, zground, (key0, pi), h=_num(t.get("height")), src=key0, plant=sp)
            rep["m"] += part.length
    rep["m"] = round(rep["m"], 1)
    report["osm_hedges"] = rep
    return rep


def _num(v):
    try:
        return float(str(v).replace(",", ".").split()[0]) if v not in (None, "") else None
    except (ValueError, IndexError):
        return None


def _hedge_species(t):
    s = " ".join(t.get(k, "") for k in ("species", "genus", "species:pl", "taxon")).lower()
    for k, name in (("berber", "berberis_red"), ("ligustr", "privet"), ("carpin", "hornbeam"), ("grab", "hornbeam"),
                    ("thuja", "thuja"), ("żywotn", "thuja")):
        if k in s:
            return name
    return "thuja" if t.get("leaf_type") == "needleleaved" else "privet"


def band_of(poly, width, key=None, step=0.8, end_trim=0.3):
    """Clipped hedge band ~`width` m wide along an elongated bed (ADR 0060, review r7 N-4 / r8 N-22): the bed's centre
    line (mid-points of cross-sections perpendicular to its long axis, smoothed) buffered by width / 2 with rounded
    ends, kept inside the bed; the band runs the full length of the bed like the photo's strips (an inset of the bed
    shortened them into lens shapes). Beds already narrower than the band are returned as they are."""
    from shapely.geometry import LineString
    if 2.0 * poly.area / max(poly.length, 1e-6) <= width * 1.05:
        return poly
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    e = [rect[1] - rect[0], rect[2] - rect[1]]
    ax = e[0] if np.linalg.norm(e[0]) >= np.linalg.norm(e[1]) else e[1]
    L = float(np.linalg.norm(ax))
    ax = ax / L
    nrm = np.array([-ax[1], ax[0]])
    c = np.asarray(poly.centroid.coords[0])
    pts = []
    for t in np.arange(-L / 2, L / 2 + 1e-6, step):
        q = c + ax * t
        cut = LineString([q - nrm * 50.0, q + nrm * 50.0]).intersection(poly)
        if cut.is_empty:
            continue
        seg = max(getattr(cut, "geoms", [cut]), key=lambda g: g.length)
        if seg.length < 0.3:
            continue
        pts.append(np.asarray(seg.centroid.coords[0]))
    if len(pts) < 3:
        return poly
    P = np.array(pts)
    if len(P) >= 5:                                   # 3-point smoothing, ends kept
        P[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4.0
    band = LineString(P).buffer(width / 2.0, quad_segs=4).intersection(poly.buffer(-end_trim))
    band = band.buffer(-0.1).buffer(0.1, quad_segs=3)
    if band.is_empty:
        return poly
    return max(getattr(band, "geoms", [band]), key=lambda q: q.area)


def _island_holes(roads_poly):
    holes = []
    for g in getattr(roads_poly, "geoms", [roads_poly]):
        for r in g.interiors:
            p = Polygon(r)
            if 2.0 < p.area < ISLAND_MAX_M2:
                holes.append(p)
    return holes


def build(buf, overrides, origin, roads_poly, road_parts, zground, deck_mask_at, report):
    from .furniture import SurfaceTop
    rep = {"hedges": 0, "hedge_m2": 0.0, "islands": [], "shrubs": 0, "stale": [], "tris": 0}
    plans = [o for o in overrides if o.get("kind") == "plantings"]
    if not plans:
        report["plantings"] = rep
        return []
    ox, oy = float(origin[0]), float(origin[1])
    holes = _island_holes(roads_poly)
    tree = shapely.STRtree(holes) if holes else None
    kerb = SurfaceTop(road_parts)
    blocked = []
    filled = set()
    for o in plans:
        for bi, bed in enumerate(o.get("beds", [])):
            poly = Polygon(np.asarray(bed["ring"], float) - [ox, oy])
            poly = shapely.make_valid(poly).buffer(-float(bed.get("rim_m", 0.6))).buffer(0.25)
            S_ = species(bed.get("plant", "berberis_red"))
            for gi, g in enumerate(getattr(poly, "geoms", [poly])):
                if g.geom_type != "Polygon" or g.area < 1.0:
                    continue
                key = (o["id"], bi, gi)
                band = bed.get("band_m")
                if band is None and S_.get("band"):
                    band = S_["band"][0] + _h(*key, "band") * (S_["band"][1] - S_["band"][0])
                if band:
                    g = band_of(g, float(band))
                    if g.geom_type != "Polygon" or g.area < 0.5:
                        continue
                rep["hedges"] += hedge_mass(buf, g, zground, key, h=bed.get("height_m"), src=f"override:{o['id']}:bed{bi}",
                                             plant=bed.get("plant", "berberis_red"), stats=rep)
                rep["hedge_m2"] += g.area
                blocked.append(g)
        for ii, isl in enumerate(o.get("islands", [])):
            q = Point(float(isl["at"][0]) - ox, float(isl["at"][1]) - oy)
            hit = [holes[k] for k in (tree.query(q, predicate="within") if tree is not None else [])]
            if not hit:
                near = sorted(((h.distance(q), h) for h in holes if h.distance(q) < 30.0), key=lambda t: t[0])[:5]
                rep["stale"].append({"id": f"{o['id']}:island{ii}", "near_holes": [
                    {"dist_m": round(d, 1), "area_m2": round(h.area, 1),
                     "centroid_epsg2180": [round(h.centroid.x + ox, 1), round(h.centroid.y + oy, 1)]} for d, h in near]})
                continue
            hole = min(hit, key=lambda p: p.area)
            hk = (round(hole.centroid.x, 1), round(hole.centroid.y, 1))
            if hk in filled:                # two points in one island: fill it once (no coplanar duplicate)
                rep["stale"].append(f"{o['id']}:island{ii}:duplicate")
                continue
            filled.add(hk)
            ring = _ccw_ring(hole, 1.0)
            # kerb top just outside the hole edge (the kerb strips of the road layer)
            Nn = _ring_normals(ring)
            zk = np.array([kerb.top(float(x), float(y)) for x, y in ring + Nn * 0.06])
            ok = np.isfinite(zk)
            if ok.sum() < 3:
                rep["stale"].append(f"{o['id']}:island{ii}:no_kerb")
                continue
            zk[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), zk[ok])
            fill = isl.get("fill", "soil")             # paving | soil | stones (ADR 0060: river stones / gravel)
            dz = 0.0 if fill == "paving" else -SOIL_BELOW_KERB
            P2, T = _fill(ring, 1.5)
            # interior heights: inverse-distance mean of the kerb tops (islands are small and near flat)
            d2 = ((P2[:, None, :] - ring[None, :, :]) ** 2).sum(-1) + 1e-6
            w = 1.0 / d2 ** 1.5
            z = (w * zk[None, :]).sum(1) / w.sum(1)
            z[:len(ring)] = zk
            z += dz
            if fill != "paving":            # a mounded centre island: the bed follows the terrain where it is higher
                z = np.maximum(z, zground(P2[:, 0], P2[:, 1]) + 0.05)
            # stones (ADR 0060) / gravel: light crushed-stone bed under the viaduct (ADR 0067)
            mat = {"paving": "sidewalk_paving", "stones": "bed_stones", "gravel": "island_gravel"}.get(fill, "bed_soil")
            V = np.column_stack([P2, z])
            buf.add("paved", mat, V, P2.copy(), T, src=f"override:{o['id']}:island{ii}")
            # Loose beds (soil, river stones, crushed stone) are soft ground for a wheel: collision_grass (low grip, high
            # rolling resistance - same class as yard_gravel in standards.SURFACE_OF); only paved islands are hard.
            # ADR 0082: the owner drove a 40 t combination across the gravel island of Rondo Bieżeństwa with the
            # grip and rolling resistance of block paving.
            buf.add("collision", "collision_paving" if fill == "paving" else "collision_grass", V, P2.copy(), T,
                    src=f"override:{o['id']}:island{ii}")
            n_sh = 0
            if isl.get("shrubs"):
                sp = float(isl.get("shrub_spacing_m", 3.0))
                inner = hole.buffer(-1.0)
                if not inner.is_empty:
                    x0, y0, x1, y1 = inner.bounds
                    for gx in np.arange(x0, x1, sp):
                        for gy in np.arange(y0, y1, sp):
                            k = (o["id"], ii, round(gx, 1), round(gy, 1))
                            if _h(*k, "use") > float(isl.get("shrub_share", 0.45)):
                                continue
                            p = np.array([gx + (_h(*k, "x") - 0.5) * sp * 0.7, gy + (_h(*k, "y") - 0.5) * sp * 0.7])
                            r = SHRUB_R[0] + _h(*k, "r") * (SHRUB_R[1] - SHRUB_R[0])
                            if not inner.contains(Point(*p).buffer(r)) or deck_mask_at(p[0], p[1]):
                                continue
                            blob = Point(*p).buffer(r, quad_segs=4)
                            blob = affinity.scale(blob, 1.0 + 0.4 * _h(*k, "sx"), 1.0, origin=tuple(p))

                            def zbed(e, n, _z=z, _P=P2):
                                d = ((np.column_stack([e, n])[:, None, :] - _P[None, :, :]) ** 2).sum(-1)
                                return _z[np.argmin(d, axis=1)]
                            hedge_mass(buf, blob, zbed, k, h=0.35 + 0.3 * _h(*k, "hh"),
                                       src=f"override:{o['id']}:island{ii}:shrub",
                                       plant=isl["shrubs"] if isinstance(isl.get("shrubs"), str) else "berberis_red",
                                       stats=rep)
                            n_sh += 1
            rep["shrubs"] += n_sh
            rep["islands"].append({"id": f"{o['id']}:island{ii}", "fill": fill, "area_m2": round(hole.area, 1),
                                   "kerb_z": [round(float(zk.min()), 2), round(float(zk.max()), 2)], "shrubs": n_sh})
            if fill != "paving":
                blocked.append(hole)
    rep["hedge_m2"] = round(rep["hedge_m2"], 1)
    report["plantings"] = rep
    return blocked
