"""ADR 0214: simplified expressway construction sites beside a drivable road (override `kind: construction_site`).

Owner D64/D65: the S19 works between Dobrzyniewo Duże and Knyszyn run beside the old DK65, which stays open with no
diversion; the sites are reproduced simplified. One override per region lists the OSM construction axes
(`highway=construction|proposed`, copied into the override with their way ids by tools/worldgen/qa/construction_sites.py,
so the site survives a re-import and does not depend on later OSM edits) and how wide the stripped corridor is.

What the stage makes of it (all WORKING_VALUE, read off the owner's frames of DK65, 2026-07-27/28, no survey):
- ground: the corridor (axis buffer, minus `keep_off_m` from every built road footprint) is bare sand in the terrain
  colour (channel A of the ground masks, the same sand as BDOT10k "nieużytki" / authored forest clearings), no trees;
- platform: the corridor is raised `platform_m` (sand formation of the future carriageway) with a 1:`slope` batter;
- heaps: elongated rounded spoil heaps (seeded by the override id, so a rebuild is identical), shaped into the terrain
  heightfield - they come with the terrain mesh, its LODs and its collider, no extra draw call;
- fence: temporary mesh fence on concrete feet (3.5 m bays, 2.0 m) along the corridor edge that faces a road
  (within `fence.max_m` of it), in runs with gaps (site gates), covering roughly `fence.share` of that edge.
Machines, temporary signs and the yellow temporary markings are not modelled.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
import shapely.ops
from scipy import ndimage
from shapely.geometry import LineString, Polygon

KIND = "construction_site"
DEFAULTS = {"half_width_m": 30.0, "keep_off_m": 4.0, "platform_m": 0.6, "slope": 2.0,
            "heaps_per_ha": 1.2, "heap_h_m": [1.2, 3.2],
            "fence": {"max_m": 45.0, "share": 0.45, "run_m": [25.0, 70.0], "gap_m": [8.0, 30.0]}}
FENCE_BAY_M = 3.5           # temporary fence panel 3.5 m x 2.0 m on concrete feet (common hire type), WORKING_VALUE
FENCE_H_M = 2.0
FOOT = (0.62, 0.20, 0.13)   # concrete foot length / width / height, WORKING_VALUE


def _seed(*parts) -> int:
    return int(hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def _cfg(o):
    c = {**DEFAULTS, **{k: v for k, v in o.items() if k in DEFAULTS}}
    c["fence"] = {**DEFAULTS["fence"], **(o.get("fence") or {})}
    return c


def plan(overrides, origin, roads_poly, report, tile=None):
    """-> list of sites {id, poly (region-local), cfg, tile}. The corridor never covers a built road (+ keep_off_m).
    `tile`: region-local tile box; heaps stay inside it (a heap cut by the tile edge would be a cliff at the seam).
    A region without the override gets no report entry (no-op for every other region)."""
    out = []
    if not any(o.get("kind") == KIND for o in overrides or []):
        return out
    rep = report.setdefault("construction_sites", {})
    org = np.asarray(origin, float)
    for o in overrides or []:
        if o.get("kind") != KIND:
            continue
        cfg = _cfg(o)
        parts = []
        for ax in o.get("axes") or []:
            line = LineString(np.asarray(ax["line_epsg2180"], float) - org)
            if line.length < 1.0:
                continue
            parts.append(line.buffer(float(ax.get("half_width_m", cfg["half_width_m"])), cap_style="flat", join_style="round"))
        for ring in o.get("polygons_epsg2180") or []:
            parts.append(Polygon(np.asarray(ring, float) - org))
        if not parts:
            rep[o["id"]] = {"area_m2": 0.0, "stale": True}
            continue
        poly = shapely.union_all(parts)
        if roads_poly is not None and not roads_poly.is_empty:
            poly = poly.difference(roads_poly.buffer(float(cfg["keep_off_m"])))
        poly = poly.buffer(-0.5).buffer(0.5)                     # no slivers between two roads
        out.append({"id": o["id"], "poly": poly, "cfg": cfg, "tile": tile})
        rep[o["id"]] = {"area_m2": round(poly.area), "axes": len(o.get("axes") or []), "stale": poly.area < 1.0}
    return out


def _grid_en(hf):
    H, W = hf.z.shape
    return hf.x0 + np.arange(W), hf.y1 - np.arange(H)


def shape_terrain(zc, mask, hf, sites, rasterize, report):
    """Raise the platform and the spoil heaps into the conformed terrain `zc` (1 m grid) outside the road / paved
    `mask`. Returns (zc, site_mask)."""
    if not sites:
        return zc, np.zeros(zc.shape, bool)
    rep = report.setdefault("construction_sites", {})
    east, north = _grid_en(hf)
    free = ~mask
    # distance (m) from the road / paved footprint: everything fades in over 2-5 m so no step forms at a verge
    d_mask = ndimage.distance_transform_edt(free)
    fade = np.clip((d_mask - 2.0) / 3.0, 0.0, 1.0)
    site_mask = np.zeros(zc.shape, bool)
    dz = np.zeros(zc.shape, float)
    for s in sites:
        m = rasterize([s["poly"]], hf)
        if not m.any():
            continue
        site_mask |= m
        cfg = s["cfg"]
        d_in = ndimage.distance_transform_edt(m)                     # metres from the site edge, inside
        run = max(float(cfg["platform_m"]) * float(cfg["slope"]), 1.0)
        dz = np.maximum(dz, float(cfg["platform_m"]) * np.clip((d_in - 0.5) / run, 0.0, 1.0))
        # spoil heaps: elongated rounded mounds, centres >= their half-width + 2 m inside the site edge
        rng = np.random.default_rng(_seed("heaps", s["id"]))
        n = int(round(s["poly"].area / 1e4 * float(cfg["heaps_per_ha"])))
        h0, h1 = cfg["heap_h_m"]
        js, is_ = np.nonzero(m)
        placed, tries = [], 0
        while len(placed) < n and tries < 40 * max(n, 1) and len(js):
            tries += 1
            k = rng.integers(len(js))
            j, i = int(js[k]), int(is_[k])
            h = float(rng.uniform(h0, h1))
            b = h * float(rng.uniform(2.0, 2.8))                     # half-width: flanks ~ 30-35 deg at the steepest
            a = b * float(rng.uniform(1.3, 3.0))                     # half-length
            if s.get("tile") is not None:
                x0, y0, x1, y1 = s["tile"].bounds
                e_, n_ = hf.x0 + i, hf.y1 - j
                if not (x0 + a + 2.0 < e_ < x1 - a - 2.0 and y0 + a + 2.0 < n_ < y1 - a - 2.0):
                    continue
            if d_in[j, i] < b + 2.0 or any(math.hypot(i - pi, j - pj) < (a + pa) * 0.8 for pi, pj, pa in placed):
                continue
            placed.append((i, j, a))
            th = float(rng.uniform(0, math.pi))
            r = int(math.ceil(a)) + 1
            j0, j1, i0, i1 = max(j - r, 0), min(j + r + 1, zc.shape[0]), max(i - r, 0), min(i + r + 1, zc.shape[1])
            yy, xx = np.mgrid[j0:j1, i0:i1]
            u = (xx - i) * math.cos(th) - (yy - j) * math.sin(th)
            v = (xx - i) * math.sin(th) + (yy - j) * math.cos(th)
            q = np.clip(1.0 - (u / a) ** 2 - (v / b) ** 2, 0.0, 1.0)
            bump = h * q ** 0.75 * (0.92 + 0.08 * np.cos(3.0 * np.arctan2(v, u) + th))
            dz[j0:j1, i0:i1] = np.maximum(dz[j0:j1, i0:i1], np.where(m[j0:j1, i0:i1], bump + float(cfg["platform_m"]), 0.0))
        rep.setdefault(s["id"], {})["heaps"] = len(placed)
    dz = ndimage.gaussian_filter(dz, 0.7) * fade * free
    rep["max_raise_m"] = round(float(dz.max()), 2)
    return zc + dz, site_mask


def ground_colour(col, site_mask, hf):
    """Sand (channel A) on the stripped corridor, no forest floor (G), slightly patchy so it does not read as a decal."""
    if not site_mask.any():
        return col
    east, north = _grid_en(hf)
    w = ndimage.gaussian_filter(site_mask.astype(np.float32), 1.2)
    E, N = np.meshgrid(east, north)
    patch = 0.88 + 0.12 * np.sin(E * 0.37 + np.sin(N * 0.11) * 3.0) * np.sin(N * 0.29 + np.sin(E * 0.07) * 2.0)
    col = col.copy()
    col[..., 3] = np.maximum(col[..., 3], (w * patch).astype(np.float32))
    col[..., 1] = col[..., 1] * (1.0 - w)
    return col


def fences(lin, sites, roads_poly, report):
    """Temporary mesh fence (galvanised, concrete feet) on the corridor edge facing a road."""
    if not sites:
        return
    rep = report.setdefault("construction_sites", {})
    total = 0.0
    for s in sites:
        cfg = s["cfg"]["fence"]
        if float(cfg.get("share", 0)) <= 0 or roads_poly is None or roads_poly.is_empty:
            continue
        near = roads_poly.buffer(float(cfg["max_m"]))
        rng = np.random.default_rng(_seed("fence", s["id"]))
        geoms = getattr(s["poly"], "geoms", [s["poly"]])
        L = 0.0
        for g in geoms:
            for ring in [g.exterior, *g.interiors]:
                edge = shapely.intersection(LineString(ring.coords), near)
                for part in getattr(edge, "geoms", [edge]):
                    if part.is_empty or part.geom_type != "LineString" or part.length < 8.0:
                        continue
                    pos = float(rng.uniform(0, cfg["gap_m"][1]))
                    while pos < part.length - 6.0:
                        run = float(rng.uniform(*cfg["run_m"]))
                        if rng.uniform() < float(cfg["share"]):
                            seg = shapely.ops.substring(part, pos, min(pos + run, part.length))
                            if seg.length >= 6.0:
                                L += _fence_run(lin, seg, f"{s['id']}:fence:{round(pos)}")
                        pos += run + float(rng.uniform(*cfg["gap_m"]))
        rep.setdefault(s["id"], {})["fence_m"] = round(L)
        total += L
    rep["fence_m"] = round(total)


def _fence_run(lin, seg, key):
    """Bays of 3.5 m: concrete foot at every joint, two 0.04 m tubes per joint, mesh ribbon 0.05-2.0 m above ground."""
    n = max(1, int(round(seg.length / FENCE_BAY_M)))
    P = np.array([seg.interpolate(seg.length * k / n).coords[0] for k in range(n + 1)])
    Z = lin.z(P)
    lin.ribbon("fence_galv_mesh", P, Z + 0.05, Z + FENCE_H_M, src=key, collision="collision_fence")
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    fl, fw, fh = FOOT
    for q, z, t in zip(P, Z, nrm):
        foot = np.array([q - t * fl / 2, q + t * fl / 2])
        lin.slab("concrete_plinth", foot, np.full(2, z - 0.05), np.full(2, z + fh), fw, src=key)
    lin.posts("fence_galv", P, None, .04, .04, FENCE_H_M + .02, zb=Z, src=key)
    return seg.length
