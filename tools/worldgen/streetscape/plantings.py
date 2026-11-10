"""Roundabout / junction plantings the data does not describe (authored override `kind: plantings`,
Data/Regions/<id>/overrides.yaml; review r6 W-N12).

OSM has no barrier=hedge / landuse=flowerbed in tile C, so beds are traced from the GUGiK 2024 orthophoto (0.25 m)
and checked against the CC0 photo of Rondo Pamięci Bieżeństwa (20201102_152339, docs/REFERENCES.md). The override
carries plain geometry in EPSG:2180 plus what grows there; everything else is rule:

  hedges   `beds[].ring`: clipped hedge mass (Berberis thunbergii 'Atropurpurea' type, dark red) inset `rim_m` from
           the traced bed edge so a lawn rim stays, height 0.6-0.8 m with a gentle wavy top, battered and rounded
           sides (3 rings: foot, shoulder, top edge), top triangulated with interior points. UV0 metres (u along the
           perimeter / plan x, v up / plan y) for the hedge_foliage modulation set.
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

HEDGE_H = (0.6, 0.8)        # m, clipped berberis hedge (review r6: 0.6-0.8 m)
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


def hedge_mass(buf, poly, zground, key, h=None, src=""):
    """Closed hedge volume over plan polygon `poly` (local metres) standing on zground."""
    h = h if h is not None else HEDGE_H[0] + _h(key, "h") * (HEDGE_H[1] - HEDGE_H[0])
    R = _ccw_ring(poly.buffer(0), 0.5)
    if len(R) < 3:
        return 0
    N = _ring_normals(R)
    zg = zground(R[:, 0], R[:, 1])
    per = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(np.vstack([R, R[:1]]), axis=0).T))])[:-1]
    ph1, ph2, ph3 = _h(key, "p1") * 6.283, _h(key, "p2") * 6.283, _h(key, "p3") * 6.283
    # lumpy outline (clipped shrubs bulge between the cuts) and a wavy top: no straight slab edges
    R = R + N * (0.05 * np.sin(per / 0.9 + ph3) + 0.03 * np.sin(per / 0.37 + ph1))[:, None]
    wave = 0.05 * np.sin(per / 3.1 + ph1) + 0.03 * np.sin(per / 1.1 + ph2)
    # rounded cross-section (foot slightly outside: foliage overhangs the soil); insets shrink on narrow beds
    inr = 2.0 * poly.area / max(poly.length, 1e-6)
    k = min(1.0, 0.8 * inr / 0.24)
    prof = [(-0.04, -0.03, 0.0), (0.0, 0.45, 0.5), (0.05, 0.86, 0.85), (0.14, 0.97, 1.0), (0.24, 1.0, 1.0)]   # clipped: steep sides, flat top
    rings = [(R - N * (d * k), zg + f * h + w * wave) for d, f, w in prof]
    V = np.vstack([np.column_stack([P, z]) for P, z in rings])
    n = len(R)
    T = []
    for kk in range(len(rings) - 1):
        b0, b1 = kk * n, (kk + 1) * n
        for i in range(n):
            i1 = (i + 1) % n
            T += [(b0 + i, b0 + i1, b1 + i1), (b0 + i, b1 + i1, b1 + i)]
    vs = np.concatenate([np.full(n, f * h + 0.35 * d) for d, f, _ in prof])
    UV = np.column_stack([np.tile(per, len(rings)), vs])
    buf.add("furniture", "hedge_berberis", V, UV, np.array(T), src=src)
    # top: triangulated inner polygon at the top-edge heights + a soft crown inside
    top = rings[-1][0]
    try:
        P2, Tt = _fill(top, 1.2)
    except Exception:
        return 1
    zt = zground(P2[:, 0], P2[:, 1])
    ztop = np.empty(len(P2))
    ztop[:n] = rings[-1][1]
    if len(P2) > n:
        inner = P2[n:]
        ztop[n:] = zt[n:] + h + 0.04 + 0.04 * np.sin(inner[:, 0] * 1.7 + ph1) * np.cos(inner[:, 1] * 1.3 + ph2)
    buf.add("furniture", "hedge_berberis", np.column_stack([P2, ztop]), P2.copy(), Tt, src=src)
    return 1


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
    rep = {"hedges": 0, "hedge_m2": 0.0, "islands": [], "shrubs": 0, "stale": []}
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
            for gi, g in enumerate(getattr(poly, "geoms", [poly])):
                if g.geom_type != "Polygon" or g.area < 1.0:
                    continue
                key = (o["id"], bi, gi)
                rep["hedges"] += hedge_mass(buf, g, zground, key, h=bed.get("height_m"), src=f"override:{o['id']}:bed{bi}")
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
            fill = isl.get("fill", "soil")
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
            mat = "sidewalk_paving" if fill == "paving" else "bed_soil"
            V = np.column_stack([P2, z])
            buf.add("paved", mat, V, P2.copy(), T, src=f"override:{o['id']}:island{ii}")
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
                                       src=f"override:{o['id']}:island{ii}:shrub")
                            n_sh += 1
            rep["shrubs"] += n_sh
            rep["islands"].append({"id": f"{o['id']}:island{ii}", "fill": fill, "area_m2": round(hole.area, 1),
                                   "kerb_z": [round(float(zk.min()), 2), round(float(zk.max()), 2)], "shrubs": n_sh})
            if fill != "paving":
                blocked.append(hole)
    rep["hedge_m2"] = round(rep["hedge_m2"], 1)
    report["plantings"] = rep
    return blocked
