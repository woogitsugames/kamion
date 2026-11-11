"""Authored road paint traced on the orthophoto (ADR 0095): lines, arrows, give-way / stop rows and erase zones.

The generator derives markings from OSM tags (lanes, turn:lanes, crossings). Where the tags do not describe what is
painted (the ring of a turbo roundabout, lines across a wide junction plate, the dashed edge of a bay, a lane line
that is solid for part of an edge) the paint is listed in `overrides.yaml` with the evidence, in region-local E/N:

  kind: painted_line   polyline_en: [[E, N], ...]   line: P-1 | P-1e | P-2 | P-4 | P-7a | P-7b | P-12 | P-13 | P-14
                       (optional width_m, dash_m: [dash, gap], smooth: false)
  kind: painted_arrow  at_en: [E, N] (tail of the glyph)  heading_deg (0 = east, counter-clockwise)
                       turns: [through, left, right, slight_left, slight_right]   long: bool
  kind: painted_crossing  line_en: [[E, N], [E, N]] (the walking line across the carriageway, kerb to kerb)
                       crossing: P-10 (bars 0.5 / 0.5 m) | P-11 (two rows of squares)   width_m (default 4.0 / 2.0 clear)
  kind: paint_clear    polygon_en: [[E, N], ...]    generated paint inside is removed (authored paint stays)

All paint is draped on the generated carriageway surface (through_lines._Top); parts off the carriageway are dropped
and counted. A line with fewer than two points or nothing built is reported stale (never silently dropped).
"""

from __future__ import annotations

import math
import zlib

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import LineString, Polygon

from . import standards as S

STEP_M = 1.0
# (width, (dash, gap) or None). P-1e: the wide broken line between a through lane and a lane that leaves / joins
# (0.24 m, 1 m / 1 m as read off the 0.08 m orthophoto on Andersa - same pattern as P-7a; WORKING_VALUE).
LINES = {
    "P-1": (S.LINE_W_NARROW, S.DASH["P-1b"]),
    "P-1a": (S.LINE_W_NARROW, S.DASH["P-1a"]),
    "P-1d": (S.LINE_W_NARROW, S.DASH["P-1d"]),
    "P-1e": (S.LINE_W_WIDE, (1.0, 1.0)),
    "P-2": (S.LINE_W_NARROW, None),
    "P-2b": (S.LINE_W_WIDE, None),
    "P-7a": (S.LINE_W_WIDE, S.DASH["P-7a"]),
    "P-7b": (S.LINE_W_WIDE, None),
    "P-12": (S.P12_W, None),
    "P-14": (S.P14_DEPTH, (S.P14_LEN, S.P14_GAP)),
}
AUTHORED_PREFIX = "AP-"


def _densify(P, smooth=True):
    """Polyline resampled every STEP_M; with >= 3 points a centripetal Catmull-Rom curve through the points."""
    P = np.asarray(P, float)
    if len(P) < 2:
        return P
    if smooth and len(P) >= 3:
        ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
        out = []
        for i in range(1, len(ext) - 2):
            p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
            n = max(2, int(math.ceil(float(np.hypot(*(p2 - p1))) / STEP_M)))
            for u in np.linspace(0.0, 1.0, n, endpoint=False):
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u
                                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
        out.append(P[-1])
        return np.array(out)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    n = max(1, int(math.ceil(s[-1] / STEP_M)))
    u = np.linspace(0.0, s[-1], n + 1)
    return np.column_stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])])


def _drape_polygon(buf, top, pg, src, uv1y=0.35):
    """ADR 0100: a 4-corner shape (zebra bar, P-11 square) is draped as a strip of cells <= 0.35 m, anything else is
    triangulated at 0.5 m; both lifted so the paint plane never dips under the surface (p21_hatch.drape_lift). The
    ADR 0095 version draped 1 m Delaunay triangles at their corners only: dark specks of asphalt through the bars."""
    from .gores import _triangulate
    from . import p21_hatch as H
    n, lost = 0, 0
    for part in getattr(pg, "geoms", [pg]):
        if part.is_empty or part.geom_type != "Polygon" or part.area < 0.01:
            continue
        ring = np.asarray(part.exterior.coords)[:-1]
        if len(ring) == 4 and not part.interiors:
            V, T = H.drape_quad(ring)
        else:
            V, T = _triangulate(part, 0.5)
            if V is None:
                continue
        z, T, nl, _ = H.drape_lift(top, V, T)
        lost += nl
        if not len(T):
            continue
        age = (zlib.crc32(src.encode()) % 1000) / 1000.0 * 0.98
        uv1 = np.column_stack([np.full(len(V), 0.5), np.full(len(V), uv1y + age)])
        buf.add("markings", "marking_white", np.column_stack([V, np.nan_to_num(z) + S.MARKING_LIFT]), V.copy(),
                T, src=src, UV1=uv1)
        n += int(len(T))
    return n, lost


def _p13_row(Q):
    """P-13 give-way triangles along polyline Q; the tips point to the right of the drawing direction (towards the
    approaching driver when Q is drawn from the driver's left to the driver's right)."""
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    tris = []
    x = S.P13_GAP / 2
    while x + S.P13_BASE <= s[-1] + 1e-6:
        pts = []
        for xs in (x, x + S.P13_BASE, x + S.P13_BASE / 2):
            p = np.array([np.interp(xs, s, Q[:, 0]), np.interp(xs, s, Q[:, 1])])
            pts.append(p)
        i = int(np.clip(np.searchsorted(s, x + S.P13_BASE / 2) - 1, 0, len(Q) - 2))
        t = Q[i + 1] - Q[i]
        t /= max(float(np.hypot(*t)), 1e-9)
        right = np.array([t[1], -t[0]])
        tris.append(Polygon([pts[0], pts[1], pts[2] + right * S.P13_H]))
        x += S.P13_BASE + S.P13_GAP
    return tris


def clear_zones(buf, overrides, report, applied):
    polys = []
    for o in overrides:
        if o.get("kind") != "paint_clear":
            continue
        pg = Polygon(np.asarray(o.get("polygon_en") or [], float)) if len(o.get("polygon_en") or []) >= 3 else None
        if pg is None or not pg.is_valid:
            continue
        polys.append((o["id"], pg))
    erased = {}
    for oid, pg in polys:
        shapely.prepare(pg)
        b = pg.bounds
        n = 0
        keep = []
        for p in buf.parts:
            if p.layer == "markings" and len(p.T) and not p.src.startswith((AUTHORED_PREFIX, "P-21@zone:")):
                lo, hi = p.V[:, :2].min(0), p.V[:, :2].max(0)
                if not (hi[0] < b[0] or lo[0] > b[2] or hi[1] < b[1] or lo[1] > b[3]):
                    cen = p.V[p.T].mean(1)
                    drop = shapely.contains_xy(pg, cen[:, 0], cen[:, 1])
                    if drop.any():
                        if p.src.startswith(("P-8", "P-13")):
                            drop[:] = True
                        n += int(drop.sum())
                        p.T = p.T[~drop]
            if len(p.T):
                keep.append(p)
        buf.parts[:] = keep
        erased[oid] = n
        applied.append({"id": oid, "targets": [f"clear@{pg.centroid.x:.0f},{pg.centroid.y:.0f}"]})
    report["paint_clear_tris"] = erased


def paint(buf, overrides, report, applied, stale):
    from .through_lines import _Top, _line
    from .markings import arrow_glyph
    top = None
    rep = []
    for o in overrides:
        kind = o.get("kind")
        if kind not in ("painted_line", "painted_arrow", "painted_crossing"):
            continue
        if top is None:
            top = _Top(buf.parts)
        n = lost = 0
        if kind == "painted_line":
            P = np.asarray(o.get("polyline_en") or [], float)
            name = str(o.get("line", "P-2"))
            if P.ndim != 2 or len(P) < 2 or (name not in LINES and name != "P-13"):
                stale.append(o["id"])
                rep.append({"id": o["id"], "built": False, "note": "polyline_en needs >= 2 points and a known line"})
                continue
            Q = _densify(P, bool(o.get("smooth", True)))
            src = f"{AUTHORED_PREFIX}{name}@{o['id']}"
            if name == "P-13":
                for tri in _p13_row(Q):
                    a, b = _drape_polygon(buf, top, tri, src, 2.0)
                    n += a
                    lost += b
            else:
                w, pat = LINES[name]
                w = float(o.get("width_m", w))
                if "dash_m" in o:
                    pat = tuple(float(v) for v in o["dash_m"]) if o["dash_m"] else None
                total = float(np.sum(np.hypot(*np.diff(Q, axis=0).T)))
                n = _line(buf, top, Q, w, pat, src, None)
                lost = 0 if n else 1
                rep.append({"id": o["id"], "built": bool(n), "line": name, "len_m": round(total, 1), "tris": n})
                (applied.append({"id": o["id"], "targets": [f"line@{Q[0][0]:.0f},{Q[0][1]:.0f}"]}) if n
                 else stale.append(o["id"]))
                continue
        elif kind == "painted_crossing":
            L = np.asarray(o.get("line_en") or [], float)
            if L.shape != (2, 2) or float(np.hypot(*(L[1] - L[0]))) < 1.0:
                stale.append(o["id"])
                rep.append({"id": o["id"], "built": False, "note": "line_en needs two points >= 1 m apart"})
                continue
            t = (L[1] - L[0]) / float(np.hypot(*(L[1] - L[0])))
            nrm = np.array([-t[1], t[0]])
            length = float(np.hypot(*(L[1] - L[0])))
            name = str(o.get("crossing", "P-10"))
            shapes = []
            if name == "P-11":
                clear = float(o.get("width_m", S.P11_CLEAR))
                x = S.P11_GAP / 2
                while x + S.P11_SQUARE <= length + 1e-6:
                    for sg in (-1.0, 1.0):
                        c0 = L[0] + t * (x + S.P11_SQUARE / 2) + nrm * sg * (clear + S.P11_SQUARE) / 2
                        h = S.P11_SQUARE / 2
                        shapes.append(Polygon([c0 - t * h - nrm * h, c0 + t * h - nrm * h, c0 + t * h + nrm * h, c0 - t * h + nrm * h]))
                    x += S.P11_SQUARE + S.P11_GAP
            else:
                wd = float(o.get("width_m", S.P10_WIDTH)) / 2
                x = S.P10_GAP / 2
                while x + S.P10_STRIPE <= length + 1e-6:
                    c0 = L[0] + t * (x + S.P10_STRIPE / 2)
                    h = S.P10_STRIPE / 2
                    shapes.append(Polygon([c0 - t * h - nrm * wd, c0 + t * h - nrm * wd, c0 + t * h + nrm * wd, c0 - t * h + nrm * wd]))
                    x += S.P10_STRIPE + S.P10_GAP
            for g in shapes:
                a_, b_ = _drape_polygon(buf, top, g, f"{AUTHORED_PREFIX}{name}@{o['id']}", 2.0)
                n += a_
                lost += b_
        else:
            at = np.asarray(o.get("at_en") or [], float)
            if at.shape != (2,):
                stale.append(o["id"])
                rep.append({"id": o["id"], "built": False, "note": "at_en missing"})
                continue
            g = arrow_glyph(list(o.get("turns") or ["through"]), bool(o.get("long", False)))
            g = affinity.translate(affinity.rotate(g, float(o.get("heading_deg", 0.0)), origin=(0, 0)), at[0], at[1])
            n, lost = _drape_polygon(buf, top, g, f"{AUTHORED_PREFIX}P-8@{o['id']}", 2.0)
        rep.append({"id": o["id"], "built": bool(n), "kind": kind, "tris": n, "tris_off_carriageway": lost})
        if n:
            applied.append({"id": o["id"], "targets": [kind]})
        else:
            stale.append(o["id"])
    report["authored_paint"] = rep
