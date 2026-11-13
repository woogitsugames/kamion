"""Roundabout / junction plantings the data does not describe (authored override `kind: plantings`,
Data/Regions/<id>/overrides.yaml; review r6 W-N12).

OSM has no barrier=hedge / landuse=flowerbed in tile C, so beds are traced from the GUGiK 2024 orthophoto (0.25 m)
and checked against the CC0 photo of Rondo Pamięci Bieżeństwa (20201102_152339, docs/REFERENCES.md). The override
carries plain geometry in EPSG:2180 plus what grows there; everything else is rule:

  hedges   `beds[].ring` (+ `plant`: berberis_red | privet | hornbeam | thuja, SPECIES): clipped hedge inset `rim_m`
           from the traced bed edge so a lawn rim stays. ADR 0049 addendum (the r6 masses read as solid boxes): a dark
           opaque core (hedge_<sp>, hedge_foliage set), an alpha leaf shell 5 cm outside it (hedge_shell_<sp>, open
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
from shapely.geometry import LineString, Point, Polygon

from terrain_mesh.chunks import CHUNK_M
from . import plots as PLT

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
                         local_top=True),
    "privet": dict(tex="privet", h=(1.2, 1.7), plant=(0.45, 0.65), bulge=0.08, dome=0.12, gap_p=0.10, sigma=0.36,
                   sprig=0.30, sprig_wh=((0.14, 0.24), (0.10, 0.18))),
    "hornbeam": dict(tex="hornbeam", h=(1.4, 2.0), plant=(0.5, 0.7), bulge=0.08, dome=0.10, gap_p=0.09, sigma=0.38,
                     sprig=0.34, sprig_wh=((0.16, 0.28), (0.12, 0.22))),
    "thuja": dict(tex="thuja", h=(1.6, 2.2), plant=(0.6, 0.8), bulge=0.10, dome=0.24, gap_p=0.09, sigma=0.27,
                  sprig=0.40, sprig_wh=((0.12, 0.2), (0.12, 0.2))),
    # ADR 0186: unclipped roadside thicket (dogwood / ninebark / willow scrub grown into one mass, CC0 photo P11-063
    # Mickiewicza / Kuronia): no missing plants (a closed wall, nothing shows through), bushes 1.1-1.7 m apart as
    # 0.4 m lumps of the side, a rounded shoulder and a crown that rises and falls by ~ +-0.4 m, long loose shoots.
    # Hornbeam leaf textures (the largest broadleaf of the hedge set). Height from the bed (`height_m`), else 2.2-3.0 m.
    # WORKING_VALUE (read off the photo, not surveyed).
    # r2 (first render: read as a clipped hedge with a 0.6 m leaf pattern and a dark skirting): leaf tile x 3 (sprays
    # of leaves, no pattern at 60 m), shell down to 4 % of the height, crown relief +-0.5 m, shoots 0.5-1.1 m.
    "thicket": dict(tex="hornbeam", h=(2.2, 3.0), plant=(1.3, 1.9), bulge=0.45, dome=0.50, gap_p=0.0, sigma=0.45,
                    sprig=0.55, sprig_wh=((0.60, 1.20), (0.55, 1.05)), prof="thicket", tile_scale=3.0, foot=0.04,
                    ring_step=0.7, fill=(2.0, 1.1), top_sprigs=0.8),      # a mass 10 x coarser than a clipped hedge: ~70 tris / m2
}
# cross-sections (inset m, height share, bulge share), foot first
PROFILES = {
    # ADR 0186: a grown bush mass - belly at 0.3-0.5 h, shoulder rounded over the upper 0.9 m of the plan
    "thicket": [(0.0, -0.05, 0.3), (-0.10, 0.28, 0.9), (-0.04, 0.52, 1.0), (0.16, 0.74, 0.9), (0.45, 0.89, 0.6),
                (0.90, 1.0, 0.3)],
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


def hedge_mass(buf, poly, zground, key, h=None, src="", plant="berberis_red", stats=None):
    """Clipped hedge over plan polygon `poly` (local metres) standing on zground (review r6 W-N12, ADR 0049 addendum):
    an opaque dark core (interior shade, stems visible at the foot), an alpha leaf shell SHELL_D outside it (silhouette
    and surface broken into leaves, open below SHELL_FOOT so the base reads dark), per-plant lumps and dips along the
    perimeter (thin / missing plants), a lumpy crown and loose shoot cards on the top edge, sides and top."""
    from .hedge_textures import HEDGE_TILE_M
    S = species(plant)
    HEDGE_TILE_M = HEDGE_TILE_M * S.get("tile_scale", 1.0)     # ADR 0186: thicket - sprays of leaves, not a leaf pattern
    core_m, shell_m, sprig_m = hedge_mats(plant)
    h = h if h is not None else S["h"][0] + _h(key, "h") * (S["h"][1] - S["h"][0])
    if S.get("ring_step"):                 # coarse mass: drop the arc vertices of the buffered bed outline
        poly = poly.simplify(0.25)
    R = _ccw_ring(poly.buffer(0), S.get("ring_step", 0.3))
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

    def rings(R0, hh, prof_, sel=slice(None)):
        return [(R0[sel] + N[sel] * (b * bulge[sel] - d * k)[:, None], zg[sel] + f * hh[sel]) for d, f, b in prof_]

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
    core = rings(R - N * 1.3 * SHELL_D, hl - SHELL_D, prof, cs)
    nc = len(core[0][0])
    nt += strip(core, core_m, np.column_stack([np.tile(per[cs], len(core)),
                                               np.concatenate([np.full(nc, f * h) for _, f, _ in prof])]))
    try:
        P2, Tt = _fill(core[-1][0], S.get("fill", (1.0, 0.6))[0])
        zt = zground(P2[:, 0], P2[:, 1])
        z2 = (zt + _local_top_height(P2, top_xy, top_h) - 0.5 * S["dome"] * h - SHELL_D if local_top
              else zt + h * (1.0 - 0.6 * S["dome"]) - SHELL_D)
        z2[:nc] = core[-1][1]
        buf.add("furniture", core_m, np.column_stack([P2, z2]), P2.copy(), Tt, src=src)
        nt += len(Tt)
    except Exception:
        pass
    # shell: open foot; UV in shell tiles with a per-hedge offset / rotation (no aligned repeats between beds)
    sprof = [(0.02, S.get("foot", SHELL_FOOT), 0.6)] + prof[1:]
    shell = rings(R, hl, sprof)
    uo, vo = _h(key, "uo"), _h(key, "vo")
    nt += strip(shell, shell_m, np.column_stack([
        np.tile(per / HEDGE_TILE_M + uo, len(shell)),
        np.concatenate([(z - zg) / HEDGE_TILE_M + vo for _, z in shell])]))
    stop = shell[-1][0]
    try:
        P2, Tt = _fill(stop, S.get("fill", (1.0, 0.6))[1])
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
            sel = np.array([j for j in range(len(P2) - n) if _h(key, "tc", j) < S.get("top_sprigs", 0.45)], int)
            if len(sel):
                a2 = np.array([_h(key, "ta", j) * 6.283 for j in sel])
                nt += _sprig_cards(buf, sprig_m, P2[n:][sel], np.column_stack([np.cos(a2), np.sin(a2)]),
                                   z2[n:][sel], (*key, "top"), S, src, tilt=(0.0, 0.35))
    except Exception:
        pass
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
            # ADR 0123 (D51 B7): authored mound - the bed rises behind a flat rim (kerb + barrier strip), e.g. the
            # crushed-stone embankment around the piers of Rondo Biezenstwa. `mound: {setback_m, slope, max_m}`.
            mound = isl.get("mound")
            if mound and fill != "paving":
                dk = np.sqrt(d2.min(axis=1))
                z += np.clip((dk - float(mound.get("setback_m", 1.5))) * float(mound.get("slope", 0.2)),
                             0.0, float(mound.get("max_m", 0.6)))
            # stones (ADR 0060) / gravel: light crushed-stone bed under the viaduct (ADR 0067)
            mat = {"paving": "sidewalk_paving", "stones": "bed_stones", "gravel": "island_gravel"}.get(fill, "bed_soil")
            V = np.column_stack([P2, z])
            # ADR 0144: island_gravel carries vertex grime / weeds in COLOR_0 (authored island noses, roads.gores);
            # a bed writes zeros so a chunk with only this bed still exports the attribute (no attribute = white)
            buf.add("paved", mat, V, P2.copy(), T, src=f"override:{o['id']}:island{ii}",
                    COL=np.zeros((len(V), 4)) if mat == "island_gravel" else None)
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


# ADR 0154: additive house-front planting using the existing read-only plot kit.
def _garden_groups(buf, half):
    groups = {}
    for part in buf.parts:
        if part.layer not in (PLT.KIT_LAYER, PLT.KIT_LAYER_LOW) or part.mat != 'plot_kit':
            continue
        centers = part.V[part.T].mean(axis=1)
        cells = np.floor(np.column_stack((centers[:, 0] + half, half - centers[:, 1])) / CHUNK_M).astype(int)
        for cell in sorted(set(map(tuple, cells))):
            vertices = part.V[part.T[np.all(cells == cell, axis=1)]].reshape(-1, 3)
            key = (part.layer, *cell)
            lo, hi = (vertices.min(axis=0), vertices.max(axis=0))
            if key in groups:
                lo, hi = (np.minimum(lo, groups[key][0]), np.maximum(hi, groups[key][1]))
            groups[key] = (lo, hi)
    return groups


# ------------------------------------------------------------------------------------------------------------------
# ADR 0163: greenery of the house streets by the G7 measurements (research/g7-street-greenery/README.md, table
# "Parametry dla generatora"; # = row of that table, S / E / W = SOURCED / ESTIMATED / WORKING_VALUE there).
# Corrects ADR 0154 (crowns of the region's tree library scaled to 11-20 m read as stone pines on a bare stem and
# were not drawn on Low at all).
G7 = {
    "hedge_share": 0.40,            # 15 (E, 25-55 %): plots with a hedge >= 1.2 m along the street
    "low_share": 0.25,              # 16 (E): plots with a strip of low shrubs 0.5-1.2 m
    "thuja_of_hedges": 0.70,        # 18 (W): Thuja occidentalis 'Smaragd' / 'Brabant'; the rest broadleaf
    # 19 said 2.0-2.5 m (E, +-0.5 m). ADR 0170 (review s17 0163 P2: the wall barely cleared the fences): re-read on the
    # two photos # 19 cites - G7-P11 thujas stand ~2.3 fence heights (1.5 m picket fence) = ~3.5 m, G7-P12 clipped
    # wall 2.5 m rising to ~3.0 m at the corner (storey line of the house behind). WORKING_VALUE
    "thuja_h_m": (2.4, 3.6),
    "thuja_corner_h_m": 4.0,        # 19: taller on the corners, rounded (was 3.0 m)
    "thuja_w_m": (0.8, 1.2),        # 19
    "hedge_gap_m": (0.3, 0.6),      # 19: 0.3-1.0 m behind the fence line (skin of the hedge, not its axis)
    "broadleaf_h_m": (1.2, 1.5),    # 20 (0.8-1.5 m) cut to the part that counts as a hedge >= 1.2 m (# 15)
    "broadleaf_w_m": (0.5, 0.8),    # 20
    "low_h_m": (0.5, 1.2),          # 16
    "front_cover": 0.80,            # 21 (W): share of the front a hedge covers (the rest: gate, wicket, driveway)
    "crown_w_per_h": {"linden": (0.50, 0.60), "maple": (0.65, 0.75), "chestnut": (0.60, 0.80), "ash": (0.70, 0.80),
                      "birch": (0.40, 0.60), "fruit": (0.75, 0.90)},        # 13 (S, Ebben); fruit: W (not in G7)
    "ceiling_m": {"linden": 24.0, "maple": 22.0, "chestnut": 22.0, "ash": 25.0, "birch": 20.0, "fruit": 8.0},   # 12
    "broadleaf_mix": {"maple": 0.25, "birch": 0.20, "linden": 0.15, "ash": 0.15, "fruit": 0.20, "chestnut": 0.05},  # 11 (W)
    "conifer_share": 0.25,          # 8 (W, 15-40 %): the orthophoto detector finds 11 %, the photos show conifers in >= 9 of 12
    "conifer_mix": {"spruce": 0.65, "thuja": 0.35},     # 9 (W): spruce 50 % + other 15 %, columnar thuja 35 %
    "thuja_column_h_m": (4.0, 6.0),  # 10 (S, Ebben): columnar thuja 4-6 m high, 1-1.8 m wide
    "crown_base_per_h": 0.15,       # 7 (E): oak 3 / 18, maple 3 / 20, linden 1.3 / 7
    "crown_base_min_m": 1.3,        # 7: young trees
    "crown_base_strip_m": 1.6,      # W: a tree on open ground beside the street (no fence of its own); G7: 2.5-4 m only when pruned
}
# habit -> crown card of the plot kit atlas (plot_kit._crown_card): ovate dense / round dense / narrow open (G7 # 14)
HABIT = {"linden": "crown_ovoid", "maple": "crown_round", "chestnut": "crown_round", "ash": "crown_round", "birch": "crown_birch"}
DENSE = {"linden": 1.0, "maple": 1.0, "chestnut": 1.0, "ash": 0.55, "birch": 0.0}      # 14: dense / half-open / open
TREE_H_MIN_M = 4.0
OVATE_SHARE = 0.3                 # share of the round-habit species drawn with the ovate card (W: no two neighbours alike)
FRUIT_R_MAX_M = 2.3               # orchard trees are the small crowns (W)
CARD_STRETCH = (0.80, 1.30)       # a crown card is drawn at most this far off its painted width / height
# plant pitch of a thuja wall: High, Low. Review s17 0170 P2 (the wall was one green box with a flat top; G7-P11 is a
# row of separate columns with round tips): the wall body keeps sparse stations and every plant's tip is one card of
# the thuja sprite's top standing out of the crest (2 triangles a plant). Build 4 drew High as stations per plant (two
# shoulders + a trough per gap, 61 triangles / m): garden fronts High 12 058 -> 27 558 triangles and the stretch_04
# frame over its 2 M cap (test_world_v31 / test_hero_bridge). High now uses the Low design with denser wall stations
# (~14 triangles / m). WORKING_VALUE (G7 # 19: plants 0.8-1.2 m wide)
THUJA_PITCH_M = (1.0, 1.1)
THUJA_WALL_PITCH_M = (2.0, 3.2)   # station pitch of the wall body: High, Low (Low as before ADR 0170); High 1.5 m left stretch_04 84 tris under 2 M
THUJA_TIP_LOW_M = (0.50, 0.60)    # the wall's crest stands this far below the nominal height; the tips rise this far above it + 0.25
# cross-section of a clipped thuja wall per side, foot -> shoulder: (half-thickness factor, height factor, normal out,
# normal up, occlusion); the crest (centre line, full height) closes it. Photos G7-P11 / P12: battered sides, a
# rounded top, a dark foot.
# ADR 0170: one more row at 0.21 h - walls are 2.4-3.6 m now and the 1 m twig row is still drawn about 1 : 1 on High
_THUJA_PROFILE = ((0.84, 0.00, 0.95, 0.05, 0.42), (0.95, 0.21, 0.98, 0.07, 0.62), (1.00, 0.42, 1.00, 0.10, 0.80),
                  (0.97, 0.80, 0.90, 0.35, 0.95),
                  (0.60, 0.955, 0.50, 0.80, 1.0))
# Low: one more row at 0.36 h (review s17 0170 P2: the twig row was stretched ~2.8x over a 3 m wall; now ~1.2x)
_THUJA_PROFILE_LOW = ((0.86, 0.00, 0.95, 0.05, 0.45), (0.99, 0.36, 1.00, 0.08, 0.74), (1.00, 0.70, 1.00, 0.20, 0.90),
                      (0.60, 0.955, 0.50, 0.80, 1.0))


def _fold(v, step, lo, hi, d):
    """next value of a ping-pong walk in [lo, hi]: adjacent stretches of a row mirror at the vertex, so a row that
    does not tile never shows a seam"""
    if not lo <= v + d * step <= hi:
        d = -d
    return min(max(v + d * step, lo), hi), d


def thuja_hedge(kit, a, b, n, zf, h, key, thick=1.0, low=False, raise_ends=(0.0, 0.0)):
    """Clipped thuja wall a -> b (n: unit normal towards the street), G7 # 19, photos G7-P11 / P12: the foliage row of
    the kit atlas (`thuja`, 1 m of twigs in v, drawn 1 : 1 on High), a battered side with a rounded top, stations whose
    height / thickness / axis wander, ends narrowed and capped. raise_ends: extra height (m) at a / b that fades over
    4 m - the taller, rounded corner plants. Returns the length built (m)."""
    L = float(np.hypot(*(b - a)))
    if L < 1.5:
        return 0.0
    t = (b - a) / L
    prof = _THUJA_PROFILE_LOW if low else _THUJA_PROFILE
    npl = max(1, int(round(L / THUJA_PITCH_M[1 if low else 0])))              # plants
    pitch = L / npl
    nw = max(2, int(round(L / THUJA_WALL_PITCH_M[1 if low else 0])))         # stations (s, noise index, kind)
    st = [(L * k / nw, k, "end" if k in (0, nw) else "wall") for k in range(nw + 1)]
    nb = len(st) - 1

    def crest(s):                                            # nominal top of the wall at s, without the per-plant noise
        return h + raise_ends[0] * max(0.0, 1.0 - s / 4.0) ** 0.7 + raise_ends[1] * max(0.0, 1.0 - (L - s) / 4.0) ** 0.7             + 0.07 * math.sin(ph0 + s * 0.8) - THUJA_TIP_LOW_M[0]
    v0, v1 = PLT.PK.row("thuja")
    dv = v1 - v0
    row_m = PLT.PK.ROW_H_M["thuja"]
    ulo, uhi = 0.02, PLT.PK.THUJA_GREEN_U - 0.03             # the live stretch of the row
    ph0, ph1 = PLT.hfloat(key, "tp0") * 6.2832, PLT.hfloat(key, "tp1") * 6.2832
    hb = h - THUJA_TIP_LOW_M[0]                              # the body under the tip cards: its twig row is drawn ~1 : 1
    pts = [(thick / 2 * kw, hb * kh) for kw, kh, *_ in prof] + [(0.0, hb)]
    vs, vv, dd = [0.04], 0.04, 1
    for i in range(1, len(pts)):
        arc = math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        vv, dd = _fold(vv, min(arc / row_m, 0.90), 0.04, 0.96, dd)
        vs.append(vv)
    mp = len(pts)                                            # vertices per side and station
    V, UV, C = [], [], []
    us = [[ulo + (uhi - ulo) * PLT.hfloat(key, "tu", sd), 1] for sd in range(2)]
    s_prev = 0.0
    for k, (s, ip, kind) in enumerate(st):
        endf = 0.62 if kind == "end" else 1.0
        c = a + t * s + n * (0.05 * (PLT.hfloat(key, "to", k) * 2 - 1))
        zz = zf(a + t * s) - 0.03
        # height: the wall's slow wander + the plant's own + a little per shoulder (no flat tops)
        hh = (crest(s) + (0.06 if low else 0.09) * (PLT.hfloat(key, "th", ip) * 2 - 1)) * (0.94 if kind == "end" else 1.0)
        w = thick / 2 * (1.0 + 0.08 * math.sin(ph1 + s * 1.1) + 0.06 * (PLT.hfloat(key, "tw", k) * 2 - 1)) * endf
        dip, og = 0.0, 1.0
        du, s_prev = (s - s_prev) / PLT.PK.KIT_M, s
        for sd, sg in enumerate((1.0, -1.0)):
            if k:
                us[sd][0], us[sd][1] = _fold(us[sd][0], du, ulo, uhi, us[sd][1])
            for i in range(mp):
                if i < len(prof):
                    kw, kh, no, nu, occ = prof[i]
                else:
                    kw, kh, no, nu, occ = 0.0, 1.0, 0.0, 1.0, 1.0
                q = c + n * (sg * w * kw)
                # the dip takes the top of the wall down (shoulder and crest), not its foot
                V.append([q[0], q[1], zz + hh * kh - dip * min(kh / 0.7, 1.0)])
                UV.append([us[sd][0], v0 + dv * vs[i]])
                C.append(PLT._fol([n[0] * sg * no, n[1] * sg * no, nu], occ * og))
    m = 2 * mp
    T = []
    for k in range(nb):
        for sd in range(2):
            b0, b1 = k * m + sd * mp, (k + 1) * m + sd * mp
            for i in range(mp - 1):
                q = (b0 + i, b1 + i, b1 + i + 1, b0 + i + 1)
                T += [(q[0], q[1], q[2]), (q[0], q[2], q[3])] if sd == 0 else [(q[1], q[0], q[3]), (q[1], q[3], q[2])]
    for o, flip in ((0, False), (nb * m, True)):             # end caps: a fan over the two half profiles
        ring = [o + i for i in range(mp)] + [o + mp + i for i in range(mp - 2, -1, -1)]
        for i in range(1, len(ring) - 1):
            T.append((ring[0], ring[i + 1], ring[i]) if not flip else (ring[0], ring[i], ring[i + 1]))
    kit.tris(V, UV, T, C)
    # the plants' tips: the top of a thuja silhouette card per plant, standing in the wall's axis with its cut
    # lower edge inside the body - a scalloped line of round, ragged tips instead of a ruled top (2 triangles a plant)
    for i in range(npl):
        s = (i + 0.5 + 0.2 * (PLT.hfloat(key, "cs", i) - 0.5)) * pitch
        wc = pitch * (1.38 + 0.14 * PLT.hfloat(key, "cw", i))       # the card's column is 0.72 of its width: tips touch
        hc_ = 0.45 + THUJA_TIP_LOW_M[1] + 0.25 * PLT.hfloat(key, "ch", i)
        c = a + t * s + n * (0.10 * (PLT.hfloat(key, "cn", i) * 2 - 1))
        z0 = zf(a + t * s) - 0.03 + crest(s) - 0.45                # the cut edge: 0.45 m under the wall's crest
        u0, u1, sv0, sv1 = PLT.PK.sprite("thuja_a" if PLT.hfloat(key, "cp", i) < 0.5 else "thuja_b")
        if PLT.hfloat(key, "cf", i) < 0.5:
            u0, u1 = u1, u0
        vb = sv1 - (sv1 - sv0) * 0.42                    # the round top of the card (squashed to ~0.75 : 1)
        A, B = c - t * (wc / 2), c + t * (wc / 2)
        kit.quad([[*A, z0], [*B, z0], [*B, z0 + hc_], [*A, z0 + hc_]], [[u0, vb], [u1, vb], [u1, sv1], [u0, sv1]],
                 [PLT._fol([-t[0] * 0.5, -t[1] * 0.5, 0.7], 0.92), PLT._fol([t[0] * 0.5, t[1] * 0.5, 0.7], 0.92),
                  PLT._fol([t[0] * 0.3, t[1] * 0.3, 0.9]), PLT._fol([-t[0] * 0.3, -t[1] * 0.3, 0.9])])
    return L


def plan_house_greenery(rp, report=None):
    """ADR 0163: decide, before plots.build, what grows along the street front of every house plot and take the
    broadleaf garden trees over from plots.build. Shares are quotas over the plots that have a street front (G7 # 15 -
    18), not coin flips: 40 % hedge >= 1.2 m (70 % of them thuja), 25 % a strip of low shrubs, 35 % fence only.
    Low hedges / shrubs go to the see-through fences first (behind a wall nobody sees them)."""
    plots = rp.get("plots", [])
    front = [p for p in plots if any(r["front"] and np.linalg.norm(r["b"] - r["a"]) > 3.0 for r in p["lay"]["runs"])]
    order = sorted(front, key=lambda p: (PLT.hfloat(p["key"], "g7-front"), str(p["id"])))
    n_hedge = int(round(G7["hedge_share"] * len(order)))
    n_low = int(round(G7["low_share"] * len(order)))
    kinds = {p["id"]: "none" for p in plots}
    hedge = order[:n_hedge]
    n_thuja = int(round(G7["thuja_of_hedges"] * n_hedge))
    by_fence = sorted(hedge, key=lambda p: (p["front_style"] in PLT.SEE_THROUGH, PLT.hfloat(p["key"], "g7-hedge"), str(p["id"])))
    for k, p in enumerate(by_fence):                         # opaque fences first: only a thuja shows above them
        kinds[p["id"]] = "thuja" if k < n_thuja else "broadleaf"
    rest = sorted(order[n_hedge:], key=lambda p: (p["front_style"] not in PLT.SEE_THROUGH, PLT.hfloat(p["key"], "g7-low"), str(p["id"])))
    for p in rest[:n_low]:
        kinds[p["id"]] = "low"
    rp["front_green"] = kinds
    rp["garden_trees"] = []
    if report is not None:
        cnt = {k: sum(1 for v in kinds.values() if v == k) for k in ("thuja", "broadleaf", "low", "none")}
        report["garden_plan"] = {"source": "research/g7-street-greenery/README.md (G7 # 15-18)", "plots": len(plots),
                                 "plots_with_front": len(order), **cnt,
                                 "by_plot": {str(p["id"]): kinds[p["id"]] for p in order}}
    return kinds


def _corner_ends(run, runs):
    """(at a, at b): True where another front run of the plot meets this end at an angle - a street corner"""
    out = []
    ta = (run["b"] - run["a"]) / max(np.linalg.norm(run["b"] - run["a"]), 1e-9)
    for end in (run["a"], run["b"]):
        hit = False
        for o in runs:
            if o is run:
                continue
            to = (o["b"] - o["a"]) / max(np.linalg.norm(o["b"] - o["a"]), 1e-9)
            if abs(float(ta @ to)) < 0.75 and min(np.linalg.norm(o["a"] - end), np.linalg.norm(o["b"] - end)) < 2.5:
                hit = True
        out.append(hit)
    return tuple(out)


GROUP_GROW_M = 8.0                # a plot-kit group may grow this far (E / N) past the plot geometry it already holds


def _emit(buf, kit, groups, half, src, rep, strict=True):
    """Add the kit's High / Low variants to the plot layers, merged into the chunk groups the plots already have.
    strict: geometry that would open a new (chunk, layer) group - one more draw call - is not built."""
    high, low = kit.out(), kit.out(low=True)
    outs = [(PLT.KIT_LAYER, high), (PLT.KIT_LAYER_LOW, low)]
    if strict:
        for layer, o in outs:
            if o is None:
                continue
            centers = o[0][o[2]].mean(axis=1)
            cells = set(map(tuple, np.floor(np.column_stack((centers[:, 0] + half, half - centers[:, 1])) / CHUNK_M).astype(int)))
            if any((layer, *cell) not in groups for cell in cells):
                rep["skipped"]["new_renderer_group"] = rep["skipped"].get("new_renderer_group", 0) + 1
                return False
            # ... nor geometry that stretches a group's bounds far beyond the plots it holds: the group would then
            # pass the frustum test of cameras that never saw it (route frames g3b_rondo_put_approach /
            # g3b_ext34_s1658: +1 draw from a tree 90 m off the plots of its chunk)
            tri = o[0][o[2]]
            tc = np.floor(np.column_stack((centers[:, 0] + half, half - centers[:, 1])) / CHUNK_M).astype(int)
            for cell in cells:
                lo, hi = groups[(layer, *cell)]
                V = tri[np.all(tc == cell, axis=1)].reshape(-1, 3)
                if np.any(V[:, :2].min(axis=0) < lo[:2] - GROUP_GROW_M) or np.any(V[:, :2].max(axis=0) > hi[:2] + GROUP_GROW_M):
                    rep["skipped"]["group_bounds_growth"] = rep["skipped"].get("group_bounds_growth", 0) + 1
                    return False
    for layer, o in outs:
        if o is not None:
            buf.add(layer, "plot_kit", o[0], o[1], o[2], src=src, COL=o[3])
            rep["tris_high" if layer == PLT.KIT_LAYER else "tris_low"] += len(o[2])
    return True


def front_gardens(buf, rp, zf, report, half=1024.0):
    """ADR 0163 (replaces the ADR 0154 fronts): the planned front greenery of the house plots (plan_house_greenery) -
    clipped thuja walls 2.0-2.5 m (3 m on corners), low broadleaf hedges, strips of low shrubs - merged into the plots'
    own chunk groups on both chunk variants (High, and Low / Medium: the mass at eye level A16 was missing).
    Gates, wickets, driveways, door zones and the house are keep-outs; nothing is built outside the plot."""
    kinds = rp.get("front_green") or {}
    groups = _garden_groups(buf, half)
    rep = {"source": "research/g7-street-greenery/README.md (G7 # 15-21); positions are rule, not survey",
           "plots": {"thuja": 0, "broadleaf": 0, "low": 0}, "segments": 0, "m": {"thuja": 0.0, "broadleaf": 0.0}, "front_m": 0.0,
           "shrubs": 0, "tris_high": 0, "tris_low": 0, "heights_m": [], "widths_m": [], "list": [], "skipped": {}}
    for plot in rp.get("plots", []):
        kind = kinds.get(plot["id"], "none")
        if kind == "none":
            continue
        key, lay = plot["key"], plot["lay"]
        runs = [x for x in lay["runs"] if x["front"] and np.linalg.norm(x["b"] - x["a"]) > 3.0]
        blocked = [plot["foot"].buffer(1.0)] + list(plot.get("door_zones") or [])
        if plot.get("hard") is not None and not plot["hard"].is_empty:
            blocked.append(plot["hard"].buffer(0.5))
        gates = ([lay["gate"]] if lay.get("gate") is not None else []) + ([lay["wicket"]] if lay.get("wicket") is not None else []) \
            + list(lay.get("wickets") or [])
        for gate in gates:
            m, n = np.asarray(gate["m"]), np.asarray(gate["n"])
            blocked.append(LineString([m - n * 5, m + n * 3]).buffer(gate["w"] / 2 + 0.65, cap_style="flat"))
        forbidden = shapely.union_all(blocked)
        inner = plot["poly"].buffer(-0.08)
        if kind == "thuja":
            h = G7["thuja_h_m"][0] + (G7["thuja_h_m"][1] - G7["thuja_h_m"][0]) * PLT.hfloat(key, "g7-th")
            thick = G7["thuja_w_m"][0] + (G7["thuja_w_m"][1] - G7["thuja_w_m"][0]) * PLT.hfloat(key, "g7-tw")
        elif kind == "broadleaf":
            h = G7["broadleaf_h_m"][0] + (G7["broadleaf_h_m"][1] - G7["broadleaf_h_m"][0]) * PLT.hfloat(key, "g7-bh")
            thick = G7["broadleaf_w_m"][0] + (G7["broadleaf_w_m"][1] - G7["broadleaf_w_m"][0]) * PLT.hfloat(key, "g7-bw")
        else:
            h, thick = 0.0, 0.9
        gap = G7["hedge_gap_m"][0] + (G7["hedge_gap_m"][1] - G7["hedge_gap_m"][0]) * PLT.hfloat(key, "g7-gap")
        off = gap + thick / 2
        kit = PLT.Kit()
        built, front_m = 0.0, 0.0
        for ri, run in enumerate(runs):
            a, b = np.asarray(run["a"], float), np.asarray(run["b"], float)
            normal = np.asarray(run["n"], float)
            L = float(np.linalg.norm(b - a))
            t = (b - a) / L
            front_m += L
            corner = _corner_ends(run, runs)
            e0, e1 = a + t * 0.35 - normal * off, b - t * 0.35 - normal * off
            line = LineString([e0, e1]).difference(forbidden)
            for seg in getattr(line, "geoms", [line]):
                if seg.geom_type != "LineString" or seg.length < (3.0 if kind == "thuja" else 2.0):
                    continue                                 # a 2 m stub of a 2.3 m thuja wall is a green cube
                if not inner.covers(seg.buffer(thick / 2, cap_style="flat")):
                    rep["skipped"]["outside_plot"] = rep["skipped"].get("outside_plot", 0) + 1
                    continue
                q0, q1 = np.asarray(seg.coords[0]), np.asarray(seg.coords[-1])
                hk = (key, "g7", ri, round(float(q0[0]), 2), round(float(q0[1]), 2))
                if kind == "thuja":
                    extra = max(G7["thuja_corner_h_m"] - h, 0.0) * (0.6 + 0.4 * PLT.hfloat(key, "g7-corner"))
                    ends = (extra if corner[0] and np.linalg.norm(q0 - e0) < 0.5 else 0.0,
                            extra if corner[1] and np.linalg.norm(q1 - e1) < 0.5 else 0.0)
                    kit.tag, kit.low = "g7_thuja_hedge", False
                    length = thuja_hedge(kit, q0, q1, normal, zf, h, hk, thick=thick, raise_ends=ends)
                    kit.low = "only"
                    thuja_hedge(kit, q0, q1, normal, zf, h, hk, thick=thick, low=True, raise_ends=ends)
                    kit.low = True
                    rep["m"]["thuja"] += length
                elif kind == "broadleaf":
                    kit.tag = "g7_broadleaf_hedge"
                    length = PLT.hedge(kit, q0, q1, normal, zf, h, hk, thick=thick)
                    rep["m"]["broadleaf"] += length
                else:                                        # forsythia, berberis, spirea: single low shrubs with gaps
                    length = float(np.linalg.norm(q1 - q0))
                    tt = (q1 - q0) / length
                    s, k, n_here = 0.5 + 0.8 * PLT.hfloat(hk, "s0"), 0, 0
                    while s < length - 0.4:
                        k += 1
                        hs = G7["low_h_m"][0] + (G7["low_h_m"][1] - G7["low_h_m"][0]) * PLT.hfloat(hk, "sh", k)
                        r = 0.42 + 0.34 * PLT.hfloat(hk, "sr", k) + 0.15 * hs
                        pnt = q0 + tt * s + normal * (0.25 * (PLT.hfloat(hk, "so", k) - 0.5))
                        s += 2 * r * (0.85 + 1.5 * PLT.hfloat(hk, "sp", k) ** 2)
                        if PLT.hfloat(hk, "sg", k) < 0.12:
                            continue
                        red = PLT.hfloat(hk, "sc", k) < 0.14
                        kit.tag, kit.low = "g7_low_shrub", False
                        PLT.bush(kit, pnt, zf(pnt), r, hs, (hk, "b", k), red=red, cards=4)
                        kit.low = "only"
                        PLT.bush_lite(kit, pnt, zf(pnt), r, hs, (hk, "b", k), red=red)
                        kit.low = True
                        n_here += 1
                    rep["shrubs"] += n_here
                    length = length if n_here else 0.0
                if length:
                    built += length
                    rep["segments"] += 1
        if not built:
            continue
        if not _emit(buf, kit, groups, half, f"plot:{plot['id']}:g7-front", rep):
            continue
        rep["plots"][kind] += 1
        rep["front_m"] += front_m
        if kind != "low":
            rep["heights_m"].append(round(h, 2))
            rep["widths_m"].append(round(thick, 2))
        rep["list"].append({"plot": plot["id"], "kind": kind, "m": round(built, 1), "front_m": round(front_m, 1),
                            "h_m": round(h, 2), "w_m": round(thick, 2)})
    rep["m"] = {k: round(v, 1) for k, v in rep["m"].items()}
    rep["front_m"] = round(rep["front_m"], 1)
    report["garden_fronts"] = rep
    return rep


def tree_dims(r, species, key, in_plot=True):
    """(H, crown base height, crown card name or None for an orchard tree) of a garden tree whose crown radius r the
    orthophoto shows. H = D / (crown width per height of the species, G7 # 13) clamped to the species ceiling (# 12);
    crown base 0.15 H but >= 1.3 m (# 7); H is nudged so the crown card is drawn within CARD_STRETCH of its habit."""
    D = 2.0 * float(r)
    lo, hi = G7["crown_w_per_h"][species]
    H = D / (lo + (hi - lo) * PLT.hfloat(key, "g7-wh"))
    top = G7["ceiling_m"][species]
    H = min(max(H, TREE_H_MIN_M if species != "fruit" else 3.5), top)
    base_min = G7["crown_base_min_m"] if in_plot else G7["crown_base_strip_m"]
    sprite = HABIT.get(species)
    if species in ("maple", "ash", "chestnut") and PLT.hfloat(key, "g7-habit") < OVATE_SHARE:
        sprite = "crown_ovoid"                               # a younger / shaded tree: taller than wide
    cb = max(G7["crown_base_per_h"] * H, base_min)
    if sprite is not None:
        wm, hm = PLT.PK.SPRITE_M[sprite]
        for _ in range(3):
            st = D / max(H - cb, 0.5) / (wm / hm)
            if st > CARD_STRETCH[1]:
                H = min(cb + D / (CARD_STRETCH[1] * wm / hm), top)
            elif st < CARD_STRETCH[0]:
                H = max(cb + D / (CARD_STRETCH[0] * wm / hm), TREE_H_MIN_M)
            cb = max(G7["crown_base_per_h"] * H, base_min)
    return round(H, 2), round(min(cb, 0.45 * H), 2), sprite


def garden_tree(kit, p, z, r, H, cb, species, key, lite=False, cards=3, sprite=None, core=False):
    """A broadleaf garden tree in the plot kit (ADR 0163), habit by species: the stem to the crown base, crossed whole-
    crown cards (the habit's silhouette with its limbs), and - full variant of the dense habits - the crown's dark
    core and leaf sprays lying on its skin, so it is a volume from every side and from above, not a paper cross.
    lite: two stem strips + `cards` crossed cards (8-10 triangles) - Low / Medium and the trees away from the street;
    core (ADR 0170, lite trees near the street): the crown cards darken towards the axis (PLT.card occ_mid, + 2 triangles
    per card) and two shoulder sprays stand in front of them (+ 4) - 10 triangles more than the plain lite tree. No
    separate dark core: build 2 had one and it showed as a box under the cards (review s17 0170 P1)."""
    p = np.asarray(p, float)
    sprite = sprite or HABIT[species]
    hc = H - cb
    a0 = PLT.hfloat(key, "ty") * 6.2832
    lean = (np.array([PLT.hfloat(key, "tlx"), PLT.hfloat(key, "tly")]) - 0.5) * 0.06 * H
    top = p + lean * (cb / H)
    cc = p + lean * (0.5 + 0.5 * cb / H)                      # axis of the crown
    tr = (0.035 + 0.011 * H) * (0.8 if species == "birch" else 1.0)
    bark = PLT.PK.SWATCH["concrete" if species == "birch" else "trunk"]
    zt = z + cb + hc * (0.55 if species == "birch" else 0.22)
    if lite:
        for k in range(2):
            d = np.array([math.cos(a0 + k * 1.5708), math.sin(a0 + k * 1.5708)]) * tr
            kit.quad([[*(p - d), z - 0.1], [*(p + d), z - 0.1], [*(top + d), zt], [*(top - d), zt]], [bark] * 4)
    else:
        kit.box(p, np.array([math.cos(a0), math.sin(a0)]), tr, tr, z - 0.1, zt, bark, top=False, shift=top - p)
    W = 2.0 * r * 1.06
    for i in range(cards):                                   # no card repeats another: width, height and axis differ, so
        wj = 0.90 + 0.20 * PLT.hfloat(key, "cw", i)          # the crown is not a ball from any side (same in full / lite)
        hj = 0.97 + 0.10 * PLT.hfloat(key, "ch", i)
        off = (np.array([PLT.hfloat(key, "cx", i), PLT.hfloat(key, "cy", i)]) - 0.5) * 0.24 * r
        shade = 0.50 + 0.10 * PLT.hfloat(key, "co", i) if lite and core and DENSE[species] > 0.0 else None
        PLT.card(kit, cc + off, z + cb - 0.02 * hc, sprite, W * wj, hc * hj, a0 + 0.4 + i * math.pi / cards, occ_mid=shade)
    dense = DENSE[species]
    occ = 0.86 + 0.14 * PLT.hfloat(key, "to")
    if lite and core and dense > 0.0:
        # review s17 0170 P1 (g7_p07_b: the 4-sided dark core of build 2 hung under the cards as a black box with a
        # straight lower edge; tried next in the offline preview, tools/worldgen/streetscape/preview_kit.py: dark leaf sprays
        # and smaller dark crown cards inside - every dark plane that crosses a lit card shows the straight line of
        # the crossing). No dark geometry in the lite crown: its shaded middle is the occlusion gradient of the crown
        # cards themselves (PLT.card occ_mid). Two lit shoulder sprays as before.
        for i in range(2):
            az = a0 + 0.8 + math.pi * i
            c = cc + np.array([math.cos(az), math.sin(az)]) * r * 0.30
            PLT._skin_card(kit, c, z + cb + hc * 0.30, az, r * 1.05, hc * 0.42, "shrub_a", 0.36 + 0.14 * PLT.hfloat(key, "ut", i), occ,
                           flip=i % 2 == 1)
    if lite or dense <= 0.0:
        return
    # the sprays sit INSIDE the habit's silhouette (the crossed cards own the outline; sprays that reached it gave the
    # crown a flat, boxy skirt): they close the gaps between the cards from oblique views and from above
    PLT._core(kit, cc, z + cb + hc * 0.16, r * 0.46, hc * 0.62, key, sides=4, occ=0.26 * occ, rings=2)
    n_lo, n_hi = (4, 3) if dense >= 1.0 else (3, 2)
    for i in range(n_lo):                                    # lower tier of sprays
        az = a0 + 2 * math.pi * (i + 0.4 * (PLT.hfloat(key, "sj", i) - 0.5)) / n_lo
        c = cc + np.array([math.cos(az), math.sin(az)]) * r * (0.40 + 0.08 * PLT.hfloat(key, "sd", i))
        PLT._skin_card(kit, c, z + cb + hc * (0.13 + 0.06 * PLT.hfloat(key, "sz", i)), az, r * (0.95 + 0.25 * PLT.hfloat(key, "sw", i)),
                       hc * (0.36 + 0.08 * PLT.hfloat(key, "sh", i)), "shrub_a", 0.30 + 0.15 * PLT.hfloat(key, "st", i), occ,
                       flip=PLT.hfloat(key, "sf", i) < 0.5)
    for i in range(n_hi):                                    # upper tier: the shoulders
        az = a0 + 0.8 + 2 * math.pi * i / n_hi
        c = cc + np.array([math.cos(az), math.sin(az)]) * r * 0.24
        PLT._skin_card(kit, c, z + cb + hc * 0.48, az, r * 0.95, hc * 0.34, "shrub_a", 0.42 + 0.14 * PLT.hfloat(key, "ut", i), occ,
                       flip=i % 2 == 1)


def authored_trees(buf, overrides, zf, report, half=1024.0):
    """ADR 0186: grown broadleaf trees of an authored `kind: tree_groups` with `form: kit` - `points_en` rows
    [E, N, height m, crown diameter m] traced from the orthophoto / a photo, meshed as plot-kit garden trees (ADR 0163:
    dense crown of crossed habit cards on every tier), not as instances of the region's tree library, whose crowns
    of 3-6 leaf clumps on a bare stem read as saplings at 10 m (review s19 0179 P1). Species by `species` weights
    (maple / linden / chestnut / ash / birch), drawn per stem; crown base 0.22 H (`crown_base_m` overrides). High:
    full tree, Low / Medium: the near-street lite tree (3 cards + shaded middle). May open a plot-kit group in a
    chunk that has none (one draw call): the trees are authored, they are never left out."""
    rep = {"trees": 0, "tris_high": 0, "tris_low": 0, "skipped": {}, "list": []}
    groups = None
    for o in overrides or []:
        if o.get("kind") != "tree_groups" or o.get("form") != "kit":
            continue
        spw = o.get("species") or {"maple": 1.0}
        if any(s not in HABIT for s in spw):
            raise ValueError(f"tree_groups {o['id']}: form kit knows {sorted(HABIT)}")
        for k, q in enumerate(o.get("points_en", [])):
            if len(q) < 4:
                raise ValueError(f"tree_groups {o['id']}: form kit needs [E, N, height m, crown diameter m]")
            p, H, r = np.asarray(q[:2], float), float(q[2]), float(q[3]) / 2.0
            key = ("authored-tree", o["id"], k)
            sp = PLT._pick_w(sorted(spw.items()), key, "sp")
            cb = float(o.get("crown_base_m", 0.22 * H))
            z = zf(p)
            kit = PLT.Kit()
            kit.tag = "authored_tree"
            kit.low = False
            garden_tree(kit, p, z, r, H, cb, sp, key)
            kit.low = "only"
            garden_tree(kit, p, z, r, H, cb, sp, key, lite=True, cards=3, core=True)
            if groups is None:
                groups = _garden_groups(buf, half)
            _emit(buf, kit, groups, half, f"override:{o['id']}:kit", rep, strict=False)
            rep["trees"] += 1
            rep["list"].append({"id": o["id"], "e": round(float(p[0]), 2), "n": round(float(p[1]), 2), "h_m": H,
                                "crown_m": round(2 * r, 2), "crown_base_m": round(cb, 2), "species": sp})
    report["authored_trees"] = rep
    return rep


STRIP_REACH_M = 6.0              # a crown up to this far outside a plot belongs to a tree of that garden (plots.STREET_STRIP_M)
BEHIND_FENCE_M = 1.0             # ... whose stem stands at least this far inside the fence
MOVE_MAX_M = 7.5                 # a stem is never put further than this from the crown centre the orthophoto shows
TREE_GAP_M = 1.6                 # smallest distance between two stems
CONIFER_R_MAX_M = 3.2            # crowns wider than this stay broadleaf when conifers are topped up to the G7 share
STREET_REACH_M = 10.0            # only crowns this close to a carriageway are claimed: the strip seen from the street


def _tree_room(plot):
    """where a stem may stand in a plot: inside the fence, off the house, the driveway, the door zones and the gate"""
    room = plot["poly"].buffer(-BEHIND_FENCE_M).difference(plot["foot"].buffer(1.8))
    hard = plot.get("hard")
    if hard is not None and not hard.is_empty:
        room = room.difference(hard.buffer(0.35))
    for z in plot.get("door_zones") or []:
        room = room.difference(z.buffer(0.3))
    lay = plot["lay"]
    for g in ([lay["gate"]] if lay.get("gate") is not None else []) + ([lay["wicket"]] if lay.get("wicket") is not None else []) \
            + list(lay.get("wickets") or []):
        m, n = np.asarray(g["m"], float), np.asarray(g["n"], float)
        room = room.difference(LineString([m + n * 1.0, m - n * 8.0]).buffer(g["w"] / 2 + 0.8, cap_style="flat"))
    return room


def claim_street_crowns(rp, rep):
    """ADR 0163, G7 # 1 / # 2: the house streets have NO trees in the road strip, yet 10 crowns per 100 m of axis stand
    within 8 m of it - garden trees whose crowns hang over the fence and the footway. plots.build plants a crown that
    lies in front of a plot where the orthophoto shows its centre (on the verge: a street tree that is not there) or
    drops it (near the carriageway, conifers, small crowns). Here every crown of a tree (r >= 1.25 m) that no plot
    claimed gets its stem: behind the fence of the plot it overhangs (nearest admissible point, at most MOVE_MAX_M
    from the crown centre), or - beside a house without a generated plot - where it is, pushed clear of the roads.
    Returns the plan entries (the recorded street-strip entries of plots.build are moved behind their fence too)."""
    from shapely.ops import nearest_points
    plots = rp.get("plots", [])
    plan = rp.get("garden_trees") or []
    canopy = rp.get("canopy")
    by_id = {p["id"]: p for p in plots}
    rooms = {}
    out, stems = [], []

    def room(pid):
        if pid not in rooms:
            rooms[pid] = _tree_room(by_id[pid])
        return rooms[pid]

    def free(p):
        return all(np.hypot(*(p - q)) >= TREE_GAP_M for q in stems)

    def take(entry, p):
        stems.append(p)
        out.append(dict(entry, p=p))

    def behind_fence(pid, c):
        """the admissible point of the plot nearest to the crown centre c that keeps TREE_GAP_M to the other stems"""
        reg = room(pid) if pid in by_id else None
        if reg is None or reg.is_empty:
            return None, "no_room_behind_fence"
        q = np.asarray(nearest_points(reg, Point(*c))[0].coords[0])
        if np.hypot(*(q - c)) > MOVE_MAX_M:
            return None, "no_room_behind_fence"
        if free(q):
            return q, None
        ring = reg.boundary.intersection(Point(*c).buffer(MOVE_MAX_M))
        cands = []
        for ln in getattr(ring, "geoms", [ring]):
            if ln.geom_type != "LineString":
                continue
            cands += [np.asarray(ln.interpolate(d).coords[0]) for d in np.arange(0.0, ln.length, 0.8)]
        for q in sorted(cands, key=lambda v: float(np.hypot(*(v - c)))):
            if free(q):
                return q, None
        return None, "stem_too_close"
    for t in plan:                                           # stems plots.build placed: in the plot as they are
        if t["in_plot"]:
            stems.append(np.asarray(t["p"], float))
            if not t.get("meshed"):
                out.append(t)
    for t in plan:                                           # its street-strip trees: behind the fence
        if t["in_plot"] or t.get("meshed"):
            continue
        q, why = behind_fence(t["plot"], np.asarray(t["p"], float))
        if q is None:
            rep["skipped"][why] = rep["skipped"].get(why, 0) + 1
            continue
        take(dict(t, in_plot=True, near=True, moved=True), q)
    if canopy is None or not len(canopy) or not plots:
        return out
    seen = {(k["key"][2], k["key"][3]) for k in plan if len(k.get("key", ())) >= 4}
    polys = [p["poly"] for p in plots]
    tree = shapely.STRtree(polys)
    all_plots = shapely.unary_union(polys)
    shapely.prepare(all_plots)
    roads, carriage, bpoly = rp.get("roads_poly"), rp.get("carriage"), rp.get("bpoly")
    for ci in np.argsort(-canopy[:, 2], kind="stable"):
        cx, cy, r, con = float(canopy[ci, 0]), float(canopy[ci, 1]), float(canopy[ci, 2]), canopy[ci, 3] > 0.5
        if r < PLT.PC_R_TREE or (round(cx, 1), round(cy, 1)) in seen:
            continue
        c = np.array([cx, cy])
        pt = Point(cx, cy)
        if all_plots.contains(pt):
            continue                                         # the plot had its say (cap per plot, no free spot)
        if carriage is None or carriage.is_empty or carriage.distance(pt) > STREET_REACH_M:
            continue                                         # not a crown of the street strip (G7 # 2: <= 8-12 m of the axis)
        entry = {"key": ("g7c", round(cx, 1), round(cy, 1)), "r": r, "near": True, "kind": "conifer" if con else "broadleaf",
                 "claimed": True, "luma": float(canopy[ci, 4]) if canopy.shape[1] > 4 else 255.0}
        j = int(tree.nearest(pt))
        if polys[j].distance(pt) <= STRIP_REACH_M:
            pid = plots[j]["id"]
            q, why = behind_fence(pid, c)
            if q is None:
                rep["skipped"][why] = rep["skipped"].get(why, 0) + 1
                continue
            take(dict(entry, plot=pid, in_plot=True, moved=True), q)
            continue
        # a garden without a generated plot: the stem where the crown is, pushed away from the carriageway / footway
        q = c
        if carriage is not None and not carriage.is_empty and carriage.distance(pt) < PLT.STREET_TREE_CW_M + 0.2:
            n0 = np.asarray(nearest_points(carriage, pt)[0].coords[0])
            d = c - n0
            if np.hypot(*d) < 1e-6:
                rep["skipped"]["crown_over_carriageway"] = rep["skipped"].get("crown_over_carriageway", 0) + 1
                continue
            q = n0 + d / np.hypot(*d) * (PLT.STREET_TREE_CW_M + 0.3)
        qp = Point(*q)
        if not free(q):
            rep["skipped"]["stem_too_close"] = rep["skipped"].get("stem_too_close", 0) + 1
            continue
        if (roads is not None and roads.distance(qp) < 0.8) or (bpoly is not None and bpoly.distance(qp) < 1.8) \
                or all_plots.distance(qp) < 0.6 or np.hypot(*(q - c)) > MOVE_MAX_M \
                or (carriage is not None and not carriage.is_empty and carriage.distance(qp) < PLT.STREET_TREE_CW_M):
            rep["skipped"]["no_free_ground"] = rep["skipped"].get("no_free_ground", 0) + 1
            continue
        take(dict(entry, plot=None, in_plot=False, moved=bool(np.hypot(*(q - c)) > 0.05)), q)
    return out


def garden_trees(buf, rp, zf, report, half=1024.0, region_trees=None):
    """ADR 0163: mesh the broadleaf garden trees plots.build recorded from the orthophoto crowns (rp["garden_trees"])
    into the plot kit - on every tier (ADR 0132 r4b drew them as instances of the region's tree library, High / Medium
    only: A16 saw none). Species by the G7 mix (# 11; orchard trees among the small crowns only), size and habit by
    tree_dims. No tree closer than 2.5 m to a tree the region already placed. The kit trees join the plots' existing
    chunk groups: no new draw call."""
    plan = rp.get("garden_trees") or []
    groups = _garden_groups(buf, half)
    rep = {"source": "crowns: GUGiK orthophoto 2024 (plot_canopy.json); habit / height: G7 # 6-7, 11-14",
           "trees": 0, "street_strip": 0, "species": {}, "tris_high": 0, "tris_low": 0, "skipped": {}, "list": []}
    claimed = claim_street_crowns(rp, rep)
    todo = [t for t in claimed if t.get("kind") == "broadleaf"]
    extra_conifers = [t for t in claimed if t.get("kind") == "conifer"]
    # G7 # 8: a quarter of the garden trees are conifers, but the orthophoto detector tells only the darkest ones
    # (11 %). The darkest of the remaining small / medium crowns become spruces and columnar thujas up to that share.
    n_con = sum(1 for t in plan if t.get("kind") == "conifer") + len(extra_conifers)
    need = int(round(G7["conifer_share"] * (len(todo) + n_con))) - n_con
    if need > 0:
        cand = sorted((t for t in todo if t["r"] <= CONIFER_R_MAX_M), key=lambda t: (t.get("luma", 255.0), str(t["key"])))[:need]
        ids = {id(t) for t in cand}
        todo = [t for t in todo if id(t) not in ids]
        n_col = int(round(G7["conifer_mix"]["thuja"] * len(cand)))          # the narrowest crowns are the columns
        narrow = {id(t) for t in sorted(cand, key=lambda t: (t["r"], str(t["key"])))[:n_col]}
        extra_conifers += [dict(t, kind="conifer", converted=True, columnar=id(t) in narrow) for t in cand]
    rep["conifers_converted"] = max(need, 0) and sum(1 for t in extra_conifers if t.get("converted"))
    kd = None
    if region_trees:
        from scipy.spatial import cKDTree
        kd = cKDTree(np.array([[t_["e"], t_["n"]] for t_ in region_trees]))
    small = sum(1 for t in todo if t["r"] < FRUIT_R_MAX_M) / max(len(todo), 1)
    mix = G7["broadleaf_mix"]
    for t in todo:
        p = np.asarray(t["p"], float)
        if kd is not None and kd.query(p)[0] < 2.5:
            rep["skipped"]["region_tree_within_2.5m"] = rep["skipped"].get("region_tree_within_2.5m", 0) + 1
            continue
        r, key = float(t["r"]), t["key"]
        w = dict(mix)
        if r < FRUIT_R_MAX_M and small > 0:                  # orchard trees: all of their share among the small crowns;
            w["fruit"] = min(mix["fruit"] / small, 0.9)      # the other species keep their mix among themselves
            k = (1.0 - w["fruit"]) / (1.0 - mix["fruit"])
            w = {s: (v * k if s != "fruit" else v) for s, v in w.items()}
        else:
            w["fruit"] = 0.0
        sp = PLT._pick_w(sorted(w.items()), key, "g7-sp")
        H, cb, sprite = tree_dims(r, sp, key, in_plot=t["in_plot"])
        z = zf(p)
        kit = PLT.Kit()                                      # one part per tree: a tree that would open a new chunk
        kit.tag = "g7_garden_tree"                           # group is left out alone, not with its whole plot
        if sp == "fruit":
            if t["near"]:
                kit.low = False
                PLT.fruit_tree(kit, p, z, H, key, r=r)
                kit.low = "only"
            PLT.fruit_tree_lite(kit, p, z, H, key, r=r)
        else:
            if t["near"]:
                kit.low = False
                garden_tree(kit, p, z, r, H, cb, sp, key, sprite=sprite)
                kit.low = "only"
            garden_tree(kit, p, z, r, H, cb, sp, key, lite=True, cards=3 if t["near"] else 2, sprite=sprite, core=bool(t["near"]))
        if not _emit(buf, kit, groups, half, f"plot:{t['plot']}:g7-trees", rep):
            continue
        rep["trees"] += 1
        rep["street_strip"] += int(not t["in_plot"])
        rep["species"][sp] = rep["species"].get(sp, 0) + 1
        rep["list"].append({"plot": t["plot"], "e": round(float(p[0]), 2), "n": round(float(p[1]), 2), "r_m": round(r, 2),
                            "species": sp, "h_m": H, "crown_base_m": cb if sp != "fruit" else None,
                            "street_strip": not t["in_plot"], "near": bool(t["near"]), "moved": bool(t.get("moved")),
                            "claimed": bool(t.get("claimed"))})
    rep["conifers"] = [{"e": round(float(t["p"][0]), 2), "n": round(float(t["p"][1]), 2), "r_m": round(float(t["r"]), 2)}
                       for t in plan if t.get("kind") == "conifer"]
    for t in extra_conifers:                                 # spruces whose crowns hang over the fence (G7 # 8-10)
        p, r, key = np.asarray(t["p"], float), float(t["r"]), t["key"]
        if kd is not None and kd.query(p)[0] < 2.5:
            rep["skipped"]["region_tree_within_2.5m"] = rep["skipped"].get("region_tree_within_2.5m", 0) + 1
            continue
        kit = PLT.Kit()
        z = zf(p)
        columnar = bool(t.get("columnar"))
        if columnar:                                         # Thuja occidentalis 'Smaragd' left to grow: a dark column
            kit.tag = "g7_thuja_column"
            lo, hi = G7["thuja_column_h_m"]
            h = lo + (hi - lo) * PLT.hfloat(key, "h")
            rr = (0.26 + 0.07 * h) * (0.9 + 0.3 * PLT.hfloat(key, "w"))
            kit.low = False
            PLT.thuja(kit, p, z, h, rr, key)
            kit.low = "only"
            PLT.thuja_lite(kit, p, z, h, rr, key, core=False)
            kit.low = True
        else:
            kit.tag = "g7_spruce"
            h = min(3.2 + 3.4 * r, 14.0) * (0.9 + 0.2 * PLT.hfloat(key, "h"))
            PLT.spruce(kit, p, z, h, key)
        if _emit(buf, kit, groups, half, f"plot:{t['plot']}:g7-trees", rep):
            rep["conifers"].append({"e": round(float(p[0]), 2), "n": round(float(p[1]), 2), "r_m": round(r, 2), "h_m": round(h, 1),
                                    "kind": "thuja" if columnar else "spruce", "claimed": bool(t.get("claimed")),
                                    "converted": bool(t.get("converted"))})
    rep["claimed_crowns"] = sum(1 for t in rep["list"] if t.get("claimed")) + sum(1 for t in rep["conifers"] if t.get("claimed"))
    rep["moved_behind_fence"] = sum(1 for t in rep["list"] if t.get("moved"))
    report["garden_trees"] = rep
    return rep
