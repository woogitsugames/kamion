"""Authored paved aprons (ADR 0100, REVIEW s10-0095 P0-2 / P1-5): re-surface part of the generated carriageway.

  kind: paved_apron   polygon_en: [[E, N], ...]   surface: sett | paving | concrete | asphalt (default sett)

The generator builds a plate of asphalt wherever OSM lines meet; the orthophoto shows sett / paving there (the bay
of Andersa s 1040-1080, the plaza beside the crossover of Putry N). Every carriageway triangle of the road layer is
clipped against the polygon analytically: pieces inside move to a part with the apron material, pieces outside stay;
height, UV, UV1 and colour are interpolated barycentrically, so the surface does not move by a millimetre (no step,
no seam in the collision mesh, which is built separately and is untouched). UV of the apron = plan metres (the sett
textures are world-scaled). Nothing re-surfaced = overrides_stale.
"""

from __future__ import annotations

import numpy as np
import shapely
from shapely.geometry import Polygon

CARRIAGEWAY = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel"}
SURFACES = {"sett": "road_sett", "paving": "road_paving", "concrete": "road_concrete", "asphalt": "road_asphalt"}


def _bary(tri, P):
    a, b, c = tri
    v0, v1, v2 = b - a, c - a, P - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-12:
        return np.tile([1 / 3, 1 / 3, 1 / 3], (len(P), 1))
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.column_stack([1 - v - w, v, w])


def _tris_of(geom):
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty or g.geom_type != "Polygon" or g.area < 1e-5:
            continue
        for t in getattr(shapely.constrained_delaunay_triangles(g), "geoms", []):
            out.append(np.asarray(t.exterior.coords)[:3])
    return out


class _Acc:
    def __init__(self):
        self.V, self.UV, self.UV1, self.COL, self.T = [], [], [], [], []

    def add(self, p, k, P2):
        """triangle P2 (3, 2) cut from triangle k of part p"""
        tri = p.V[p.T[k]][:, :2]
        w = _bary(tri, P2)
        idx = p.T[k]
        n = sum(len(v) for v in self.V)
        self.V.append(np.column_stack([P2, w @ p.V[idx][:, 2]]))
        self.UV.append(w @ p.UV[idx])
        self.UV1.append(None if p.UV1 is None else w @ p.UV1[idx])
        self.COL.append(None if p.COL is None else w @ p.COL[idx])
        a, b, c = P2
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        self.T.append([n, n + 1, n + 2] if cr > 0 else [n, n + 2, n + 1])

    def arrays(self):
        V = np.vstack(self.V)
        UV = np.vstack(self.UV)
        UV1 = None if any(u is None for u in self.UV1) else np.vstack(self.UV1)
        COL = None if any(c is None for c in self.COL) else np.vstack(self.COL)
        return V, UV, UV1, COL, np.asarray(self.T, np.int64)


def apply(buf, overrides, report, applied, stale):
    from .meshing import Part
    rep = []
    for o in overrides:
        if o.get("kind") != "paved_apron":
            continue
        P = np.asarray(o.get("polygon_en") or [], float)
        pg = Polygon(P) if P.ndim == 2 and len(P) >= 3 else None
        if pg is None or not pg.is_valid or pg.area < 1.0:
            stale.append(o["id"])
            rep.append({"id": o["id"], "built": False, "note": "polygon_en invalid / < 1 m2"})
            continue
        mat = SURFACES.get(str(o.get("surface", "sett")), "road_sett")
        shapely.prepare(pg)
        bx = pg.bounds
        area = 0.0
        new_parts = []
        for p in buf.parts:
            if p.layer != "road" or p.mat not in CARRIAGEWAY or p.mat == mat or not len(p.T):
                continue
            lo, hi = p.V[:, :2].min(0), p.V[:, :2].max(0)
            if hi[0] < bx[0] or lo[0] > bx[2] or hi[1] < bx[1] or lo[1] > bx[3]:
                continue
            tri2 = p.V[p.T][:, :, :2]
            tl, th = tri2.min(1), tri2.max(1)
            near = ~((th[:, 0] < bx[0]) | (tl[:, 0] > bx[2]) | (th[:, 1] < bx[1]) | (tl[:, 1] > bx[3]))
            if not near.any():
                continue
            ins = shapely.contains_xy(pg, tri2[..., 0].ravel(), tri2[..., 1].ravel()).reshape(-1, 3)
            full = near & ins.all(1)
            # a triangle with all corners inside can still cross a concave notch: test the polygon too
            cand = np.where(near & ~full)[0]
            inside, outside = _Acc(), _Acc()
            drop = np.zeros(len(p.T), bool)
            for k in np.where(full)[0]:
                tp = Polygon(tri2[k])
                if tp.area < 1e-8 or tp.within(pg):
                    inside.add(p, k, tri2[k])
                    drop[k] = True
                else:
                    cand = np.append(cand, k)
            for k in cand:
                tp = Polygon(tri2[k])
                if tp.area < 1e-8 or not tp.intersects(pg):
                    continue
                cut = tp.intersection(pg)
                if cut.area < 1e-4:
                    continue
                for t in _tris_of(cut):
                    inside.add(p, k, t)
                for t in _tris_of(tp.difference(pg)):
                    outside.add(p, k, t)
                drop[k] = True
            if not drop.any():
                continue
            p.T = p.T[~drop]
            if outside.V:
                V, UV, UV1, COL, T = outside.arrays()
                new_parts.append(Part(p.layer, p.mat, V, UV, T, p.footprint, p.src, UV1, COL))
            if inside.V:
                V, UV, UV1, COL, T = inside.arrays()
                a = V[T][:, :, :2]
                u, v = a[:, 1] - a[:, 0], a[:, 2] - a[:, 0]
                area += float(np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]).sum() / 2)
                new_parts.append(Part(p.layer, mat, V, V[:, :2].copy(), T, p.footprint, f"apron:{o['id']}", UV1, COL))
        buf.parts[:] = [p for p in buf.parts if len(p.T)] + new_parts
        if area > 0.5:
            applied.append({"id": o["id"], "targets": [f"apron@{pg.centroid.x:.0f},{pg.centroid.y:.0f}"]})
        else:
            stale.append(o["id"])
        rep.append({"id": o["id"], "built": area > 0.5, "mat": mat, "area_m2": round(area, 1),
                    "polygon_m2": round(float(pg.area), 1)})
    report["paved_aprons"] = rep
