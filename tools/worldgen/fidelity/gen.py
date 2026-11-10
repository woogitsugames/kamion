"""Generated road model as seen from above: carriageway mask, separations (islands / medians), lane layout
per chain section, arrows (P-8) and stop / give-way lines, read from the in-memory generator (roads.pipeline +
roads.markings) so that every finding points at the generator function that produced it.

Coordinates: region-local metres (E = x - origin.x, N = y - origin.y); EPSG:2180 = local + origin.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from roads import markings as MK  # noqa: E402
from roads import pipeline  # noqa: E402

CARRIAGEWAY_MATS = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel",
                    "apron_sett"}


@dataclass
class Generated:
    world: object
    origin: tuple
    tris: np.ndarray                      # (m, 3, 2) carriageway triangles (local), ground + bridge decks
    tri_layer: np.ndarray                 # "road" / "bridge"
    tri_mat: np.ndarray
    arrows: list = field(default_factory=list)       # {chain, s, lat, trav, turns, xy, heading}
    transverse: list = field(default_factory=list)   # {kind, chain, xy}
    mk_report: dict = field(default_factory=dict)


def build(region_id: str) -> Generated:
    w = pipeline.build(region_id)
    arrows, trans = [], []
    last = {"turns": None}
    orig_glyph, orig_poly, orig_cross = MK.arrow_glyph, MK.polygon_mark, MK.strip_cross

    def glyph(turns, long):
        last["turns"] = list(turns)
        return orig_glyph(turns, long)

    def poly(buf, c, poly_xy, origin_s, lat0, fwd, left, kind):
        n0 = len(buf.parts)
        orig_poly(buf, c, poly_xy, origin_s, lat0, fwd, left, kind)
        xy = c.line.offset_point(float(origin_s), float(lat0))
        t, _ = c.line.frame(float(origin_s))
        rec = {"chain": c.id, "s": float(origin_s), "lat": float(lat0), "trav": float(fwd), "xy": xy.tolist(),
               "heading": (t * fwd).tolist(), "emitted": len(buf.parts) > n0}
        if kind == "P-8":
            rec["turns"] = last["turns"]
            arrows.append(rec)
        else:
            trans.append(dict(rec, kind=kind))

    def cross(buf, c, s_mid, depth, lat0, lat1):
        orig_cross(buf, c, s_mid, depth, lat0, lat1)
        xy = c.line.offset_point(float(s_mid), 0.5 * (float(lat0) + float(lat1)))
        trans.append({"kind": "P-14", "chain": c.id, "s": float(s_mid), "lat0": float(lat0), "lat1": float(lat1),
                      "xy": xy.tolist()})

    MK.arrow_glyph, MK.polygon_mark, MK.strip_cross = glyph, poly, cross
    try:
        rep = {}
        MK.build_markings(w.buf, w.net, w.junctions, w.ctx["points"], rep)
    finally:
        MK.arrow_glyph, MK.polygon_mark, MK.strip_cross = orig_glyph, orig_poly, orig_cross
    mark, walk = {}, []
    for p in w.buf.parts:
        if p.layer == "markings" and len(p.T):
            kind = p.src.split("@")[0]
            mark.setdefault(kind, []).append(p.V[p.T][:, :, :2])
        elif p.layer in ("road", "bridge") and p.mat in ("sidewalk_paving", "curb_concrete"):
            walk.append(p.V[p.T][:, :, :2])
    tris, lay, mat = [], [], []
    for p in w.buf.parts:
        if p.layer not in ("road", "bridge") or p.mat not in CARRIAGEWAY_MATS:
            continue
        t = p.V[p.T][:, :, :2]
        tris.append(t)
        lay += [p.layer] * len(t)
        mat += [p.mat] * len(t)
    g = Generated(world=w, origin=w.origin, tris=np.concatenate(tris), tri_layer=np.array(lay),
                  tri_mat=np.array(mat), arrows=arrows, transverse=trans, mk_report=rep)
    g.mark_tris = {k: np.concatenate(v) for k, v in mark.items()}
    g.walk_tris = np.concatenate(walk) if walk else np.zeros((0, 3, 2))
    return g


def rasterize(tris: np.ndarray, x0: float, y1: float, res: float, shape) -> np.ndarray:
    """Boolean mask of triangles (local metres) on a north-up grid with top-left corner (x0, y1)."""
    import shapely
    from rasterio import features
    from rasterio.transform import from_origin
    if len(tris) == 0:
        return np.zeros(shape, bool)
    h, w = shape
    xmin, xmax = x0, x0 + w * res
    ymin, ymax = y1 - h * res, y1
    lo, hi = tris.min(1), tris.max(1)
    keep = (hi[:, 0] >= xmin) & (lo[:, 0] <= xmax) & (hi[:, 1] >= ymin) & (lo[:, 1] <= ymax)
    t = tris[keep]
    if len(t) == 0:
        return np.zeros(shape, bool)
    rings = np.concatenate([t, t[:, :1]], axis=1)
    polys = shapely.polygons(rings)
    m = features.rasterize(((g, 1) for g in polys), out_shape=shape, transform=from_origin(x0, y1, res, res),
                           fill=0, dtype="uint8", all_touched=False)
    return m.astype(bool)
