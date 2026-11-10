"""Cross-tier consistency of buildings (r4 W-H4): the Low tier draws `buildings_lod1` for chunks away from the route and
High draws `buildings` (LOD0). A tier switch may change detail, never the building: same footprint, same type, same
colour. Helpers shared by tests/gis/test_world_tiers.py and the QA print-out (`python tests/gis/tier_consistency.py`).

Footprint: union of the up-facing triangles (roofs, |n_z| > 0.7) per LOD, split into buildings (polygons of the union).
Colour: area-weighted mean of the facade colours (walls, |n_z| < 0.3) seen from the street, as linear RGB from the
manifest materials. LOD0 glazing and frames are part of what the eye averages, so they stay in; LOD1 far materials
are the base colour mixed with their glass colour by the window coverage of the far-facade window grid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from route_corridor import node_triangles, read_glb  # noqa: E402

LOD0, LOD1 = "buildings", "buildings_lod1"
LUM = np.array([0.2126, 0.7152, 0.0722])


def material_rgb(mats: dict, name: str) -> np.ndarray:
    m = mats.get(name) or {}
    c = np.asarray(m.get("color", [0.5, 0.5, 0.5]), float)[:3]
    g = m.get("window_grid")
    if g and "glass_color" in m:
        # window coverage of one storey bay: width fraction x height fraction (sill .. head, fractions of a storey)
        cov = float(np.clip(g.get("win_w", 0.5) * (g.get("head", 0.7) - g.get("sill", 0.25)), 0.0, 1.0))
        c = (1.0 - cov) * c + cov * np.asarray(m["glass_color"], float)[:3]
    return c


def _tri_geo(T):
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    n = np.cross(e1, e2)
    a = 0.5 * np.linalg.norm(n, axis=1)
    nz = np.abs(n[:, 2]) / np.maximum(2 * a, 1e-12)
    return a, nz


CELL = 1.0


def _raster(T, x0, y0, nx, ny):
    """boolean (ny, nx) mask of 1 m cells whose centre lies in one of the triangles (XY)"""
    m = np.zeros((ny, nx), bool)
    A, B, C = T[:, 0, :2], T[:, 1, :2], T[:, 2, :2]
    lo = np.floor((np.minimum(np.minimum(A, B), C) - [x0, y0]) / CELL).astype(int)
    hi = np.ceil((np.maximum(np.maximum(A, B), C) - [x0, y0]) / CELL).astype(int)
    for k in range(len(T)):
        i0, j0 = max(lo[k, 0], 0), max(lo[k, 1], 0)
        i1, j1 = min(hi[k, 0], nx), min(hi[k, 1], ny)
        if i1 <= i0 or j1 <= j0:
            continue
        gx, gy = np.meshgrid(x0 + (np.arange(i0, i1) + 0.5) * CELL, y0 + (np.arange(j0, j1) + 0.5) * CELL)
        P = np.stack([gx, gy], -1)
        v0, v1, v2 = C[k] - A[k], B[k] - A[k], P - A[k]
        d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
        d20, d21 = v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-12:
            continue
        u = (d11 * d20 - d01 * d21) / den
        v = (d00 * d21 - d01 * d20) / den
        m[j0:j1, i0:i1] |= (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6)
    return m


def lod_parts(doc, data, binoff, node, mats):
    """(roof triangles (k,3,3), wall centroids XY (k,2), wall areas (k,), wall rgb (k,3))"""
    tris = node_triangles(doc, data, binoff, node)
    roofs, cen, area, rgb = [], [], [], []
    for mat, T in tris.items():
        a, nz = _tri_geo(T)
        roofs.append(T[(nz > 0.7) & (a > 0.5)])
        w = (nz < 0.3) & (a > 1e-4)
        if w.any():
            cen.append(T[w].mean(1)[:, :2])
            area.append(a[w])
            rgb.append(np.repeat(material_rgb(mats, mat)[None], int(w.sum()), 0))
    if not cen:
        return None, None, None, None
    return np.concatenate(roofs), np.concatenate(cen), np.concatenate(area), np.concatenate(rgb)


def region_parts(world: Path, mats: dict):
    """LOD0 / LOD1 parts of every chunk GLB merged (a building cut by a chunk edge is compared as a whole)."""
    acc = {LOD0: [], LOD1: []}
    for g in sorted(world.glob("chunk_*.glb")):
        if g.name.endswith(".low.glb"):
            continue
        doc, data, binoff = read_glb(g)
        names = {n["name"] for n in doc["nodes"]}
        for nd in acc:
            if nd in names:
                part = lod_parts(doc, data, binoff, nd, mats)
                if part[0] is not None:
                    acc[nd].append(part)
    return [tuple(np.concatenate([p[i] for p in acc[nd]]) for i in range(4)) for nd in (LOD0, LOD1)]


def compare_region(world: Path, mats: dict, min_area=60.0):
    """Per building (connected LOD0 roof cells >= min_area m2): footprint IoU with LOD1 and the mean facade colour of
    each LOD (walls within 2 m of that footprint)."""
    from scipy import ndimage
    (R0, c0, a0, r0), (R1, c1, a1, r1) = region_parts(world, mats)
    allp = np.concatenate([R0.reshape(-1, 3), R1.reshape(-1, 3)])[:, :2]
    x0, y0 = allp.min(0) - 4
    nx, ny = (np.ceil((allp.max(0) + 4 - [x0, y0]) / CELL)).astype(int)
    m0, m1 = _raster(R0, x0, y0, nx, ny), _raster(R1, x0, y0, nx, ny)
    m0 = ndimage.binary_closing(m0, iterations=1)
    m1 = ndimage.binary_closing(m1, iterations=1)
    lab, n = ndimage.label(m0)
    grown = ndimage.grey_dilation(lab, size=5)          # walls stand on the footprint edge: +2 cells

    def cells(c):
        i = np.clip(((c[:, 0] - x0) / CELL).astype(int), 0, nx - 1)
        j = np.clip(((c[:, 1] - y0) / CELL).astype(int), 0, ny - 1)
        return grown[j, i]

    w0, w1 = cells(c0), cells(c1)
    out = []
    for k in range(1, n + 1):
        b = lab == k
        if b.sum() * CELL * CELL < min_area:
            continue
        near = ndimage.binary_dilation(b, iterations=2)

        b1 = m1 & near
        iou = (b & b1).sum() / max((b | b1).sum(), 1)
        core = ndimage.binary_erosion(b, iterations=2)       # drops 1-2 m door canopies / dock shelters of LOD0
        if not core.any():
            core = b
        cover = (core & m1).sum() / core.sum()
        jj, ii = np.nonzero(b)
        at = [round(float(x0 + (ii.mean() + 0.5) * CELL), 1), round(float(y0 + (jj.mean() + 0.5) * CELL), 1)]
        s0, s1 = w0 == k, w1 == k
        if not s0.any() or not s1.any():
            out.append(dict(at=at, area=float(b.sum()), iou=round(float(iou), 3), cover=round(float(cover), 3), rgb0=None, rgb1=None))
            continue
        col0 = (r0[s0] * a0[s0, None]).sum(0) / a0[s0].sum()
        col1 = (r1[s1] * a1[s1, None]).sum(0) / a1[s1].sum()
        out.append(dict(at=at, area=float(b.sum()), iou=round(float(iou), 3), cover=round(float(cover), 3),
                        rgb0=col0.round(4).tolist(), rgb1=col1.round(4).tolist()))
    return out


def colour_delta(c0, c1):
    """(luminance ratio LOD1/LOD0, chromaticity distance) - chromaticity = rgb / sum, so a darker copy of the same
    colour has distance 0 and green vs grey does not."""
    c0, c1 = np.asarray(c0), np.asarray(c1)
    l0, l1 = float(c0 @ LUM), float(c1 @ LUM)
    ch0, ch1 = c0 / max(c0.sum(), 1e-9), c1 / max(c1.sum(), 1e-9)
    return l1 / max(l0, 1e-9), float(np.abs(ch0 - ch1).max())


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    mats = json.loads((repo / "Data/Regions/bialystok-industrial-c/generated/world_manifest.json")
                      .read_text(encoding="utf-8"))["materials"]
    rows = compare_region(repo / "Data/raw/derived/bialystok-industrial-c/world", mats)
    for b in rows:
        if b["rgb0"] is not None:
            b["lum_ratio"], b["chroma_d"] = colour_delta(b["rgb0"], b["rgb1"])
    ok = [r for r in rows if r["rgb0"] is not None]
    print(f"buildings {len(rows)}  iou p05 {np.percentile([r['iou'] for r in rows], 5):.3f}  "
          f"lum_ratio p05/p95 {np.percentile([r['lum_ratio'] for r in ok], 5):.2f}/"
          f"{np.percentile([r['lum_ratio'] for r in ok], 95):.2f}  chroma_d p95 "
          f"{np.percentile([r['chroma_d'] for r in ok], 95):.3f}")
    for r in sorted(ok, key=lambda r: -r["chroma_d"])[:5]:
        print("colour", r)
    for r in sorted(ok, key=lambda r: abs(np.log(r["lum_ratio"])))[-5:]:
        print("lum", r)
    for r in sorted(rows, key=lambda r: r["cover"])[:12]:
        print("cover", r)
