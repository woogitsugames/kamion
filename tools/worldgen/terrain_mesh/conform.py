"""Conform the 1 m NMT grid to the generated roads.

1. Rasterise every ground-level road triangle (carriageway, kerb tops, sidewalks, junction patches;
   not bridges, not vertical flanges) onto the terrain nodes -> road height + footprint mask.
2. Inside the footprint the terrain is pushed TERRAIN_UNDER_ROAD below the road surface (no z-fighting,
   nothing pokes through; the road flanges hide the step).
3. Outside, every node takes the height of its nearest footprint node (exact Euclidean distance
   transform) and is clamped into the embankment cone around it: a BERM_W flat strip at the road edge,
   then 1 : EMBANKMENT_SLOPE cut or fill until it meets the NMT again.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from roads import standards as S   # tools/worldgen is on sys.path (build_world.py / tests/gis)


def rasterise(parts, hf, big=6.0):
    """Max road height per terrain node for footprint parts. Returns (road_z with -inf, mask)."""
    H, W = hf.z.shape
    road = np.full((H, W), -np.inf)
    tris = []
    for p in parts:
        if not p.footprint:
            continue
        tris.append(p.V[p.T])
    if not tris:
        return road, np.zeros((H, W), bool)
    T = np.concatenate(tris)                     # (m, 3, 3) E, N, U
    fi = T[:, :, 0] - hf.x0                      # column (fractional)
    fj = hf.y1 - T[:, :, 1]                      # row
    i0 = np.floor(fi.min(1)).astype(int)
    i1 = np.ceil(fi.max(1)).astype(int)
    j0 = np.floor(fj.min(1)).astype(int)
    j1 = np.ceil(fj.max(1)).astype(int)
    span = np.maximum(i1 - i0, j1 - j0)

    def fill(sel, ext):
        if not sel.any():
            return
        ax, ay = fi[sel, 0], fj[sel, 0]
        bx, by = fi[sel, 1], fj[sel, 1]
        cx, cy = fi[sel, 2], fj[sel, 2]
        az, bz, cz = T[sel, 0, 2], T[sel, 1, 2], T[sel, 2, 2]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        ok = np.abs(den) > 1e-12
        den = np.where(ok, den, 1.0)
        for di in range(ext + 1):
            for dj in range(ext + 1):
                px = i0[sel] + di
                py = j0[sel] + dj
                w1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
                w2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
                w3 = 1 - w1 - w2
                inside = ok & (w1 >= -1e-6) & (w2 >= -1e-6) & (w3 >= -1e-6) & (px >= 0) & (py >= 0) & \
                    (px < W) & (py < H)
                if not inside.any():
                    continue
                z = w1 * az + w2 * bz + w3 * cz
                np.maximum.at(road, (py[inside], px[inside]), z[inside])

    lo = -1
    for ext in (1, 2, 3, 5, 8, 16, 32):
        fill((span > lo) & (span <= ext), ext)
        lo = ext
    for k in np.where(span > 32)[0]:            # few big triangles: evaluate their bbox at once
        px, py = np.meshgrid(np.arange(max(i0[k], 0), min(i1[k], W - 1) + 1),
                             np.arange(max(j0[k], 0), min(j1[k], H - 1) + 1))
        (ax, bx, cx), (ay, by, cy) = fi[k], fj[k]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
        w2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
        w3 = 1 - w1 - w2
        ins = (w1 >= -1e-6) & (w2 >= -1e-6) & (w3 >= -1e-6)
        z = w1 * T[k, 0, 2] + w2 * T[k, 1, 2] + w3 * T[k, 2, 2]
        np.maximum.at(road, (py[ins], px[ins]), z[ins])
    return road, np.isfinite(road)


def clean_under_bridges(nmt, deck, deck_mask, thickness, iters=400):
    """NMT under some viaducts contains the deck itself (ALS ground filter kept it: e.g. Andersa over
    Rondo Bieżeństwa shows 'ground' at deck level). Nodes under a deck whose NMT is within the deck
    thickness (physically impossible for ground) are replaced by a harmonic fill from the surrounding
    valid ground. Returns (cleaned grid, mask of replaced nodes)."""
    near = ndimage.binary_dilation(deck_mask, iterations=2)
    top = ndimage.maximum_filter(np.where(deck_mask, deck, -np.inf), size=5)
    bad = near & np.isfinite(top) & (nmt > top - thickness - 0.3)
    out = nmt.copy()
    if not bad.any():
        return out, bad
    lab, _ = ndimage.label(bad)
    for sl in ndimage.find_objects(lab):
        sl = tuple(slice(max(0, s.start - 3), s.stop + 3) for s in sl)
        sub = out[sl].copy()
        m = bad[sl]
        _, (jj, ii) = ndimage.distance_transform_edt(m, return_indices=True)
        sub[m] = sub[jj[m], ii[m]]
        for _ in range(iters):
            p = np.pad(sub, 1, mode="edge")
            avg = 0.25 * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:])
            sub[m] = avg[m]
        out[sl] = sub
    return out, bad


def clamp_under_decks(z, deck, deck_mask, thickness, ground_mask):
    """Terrain under a deck stays >= 0.3 m below the soffit (except where a ground road runs)."""
    top = ndimage.maximum_filter(np.where(deck_mask, deck, -np.inf), size=3)
    under = np.isfinite(top) & ~ground_mask
    return np.where(under, np.minimum(z, top - thickness - 0.3), z)


def tidy(z, road, mask, dist, close_m=7, iters=150):
    """Visual cleanup after conform (visual review 2026-11-09, items 8):
    1. narrow enclosed strips (medians, splitter islands, gaps between a road and a yard, closed by
       `close_m` m) get a harmonic surface spanning the adjacent road edges (no lumps in medians);
    2. the slope band 1.5-12 m from the road is smoothed (sigma 1.2 m) to remove the faceted
       EDT-cone creases, never rising above the unsmoothed value next to the road."""
    closed = ndimage.binary_closing(mask, iterations=close_m) & ~mask
    out = z.copy()
    if closed.any():
        lab, _ = ndimage.label(closed)
        edge = ndimage.binary_dilation(closed) & mask
        for sl in ndimage.find_objects(lab):
            sl = tuple(slice(max(0, s.start - 2), s.stop + 2) for s in sl)
            sub = out[sl].copy()
            m = closed[sl]
            e = edge[sl]
            if not e.any():
                continue
            sub[e] = road[sl][e] - 0.03
            _, (jj, ii) = ndimage.distance_transform_edt(~e, return_indices=True)
            sub[m] = sub[jj[m], ii[m]]
            for _ in range(iters):
                p = np.pad(sub, 1, mode="edge")
                avg = 0.25 * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:])
                sub[m] = avg[m]
            out[sl] = np.where(m, sub, out[sl])
    band = (~mask) & ~closed & (dist > 1.5) & (dist < 12.0)
    sm = ndimage.gaussian_filter(out, 1.2)
    out = np.where(band, sm, out)
    return out


SOFT_UNDER = 0.04          # m: terrain just under grass verges / island grass (WORKING_VALUE)
SOFT_CLEAR_CELLS = 2       # ... only where no hard surface (carriageway, kerb, paving) is within this many nodes


def conform(hf, road, mask, soft=None):
    """soft (optional bool grid): footprint nodes covered only by grass verge strips. Those that are at least
    SOFT_CLEAR_CELLS nodes from any hard surface get the terrain SOFT_UNDER under the grass instead of
    TERRAIN_UNDER_ROAD: the coarse terrain grid (1-2 m) used to dip 0.35 m inside narrow kerbed islands and behind
    verges and showed the strips' vertical flanges as green walls / "troughs" (REVIEW r3 W3, r4 W-H5)."""
    nmt = hf.z
    out = nmt.copy()
    if not mask.any():
        return out, np.zeros_like(nmt)
    d, (jj, ii) = ndimage.distance_transform_edt(~mask, return_indices=True)
    zedge = road[jj, ii]
    k = 1.0 / S.EMBANKMENT_SLOPE
    run = np.maximum(0.0, d - S.BERM_W) * k
    lo = zedge - 0.03 - run
    hi = zedge - 0.03 + run
    out = np.clip(nmt, lo, hi)
    out[mask] = road[mask] - S.TERRAIN_UNDER_ROAD
    if soft is not None and soft.any():
        hard = mask & ~soft
        relax = soft & ~ndimage.binary_dilation(hard, iterations=SOFT_CLEAR_CELLS)
        out[relax] = road[relax] - SOFT_UNDER
    return out, d


WALL_MAX = 0.15            # m: visible vertical step between a ground surface edge and the terrain (REVIEW r4 W-H5)
WALL_STEEP_NZ = 0.26       # |normal.z| below this = "vertical" face (steeper than ~75 deg)
WALL_SKIP_MATS = ("curb_concrete", "edging_concrete", "bridge_concrete", "bridge_soffit", "apron_sett",
                  # ADR 0092: the gate closure line (panel fence on a plinth, steel posts) lives in the paved layer
                  # (streetscape.gate._closure) - fence faces are not terrain walls
                  "concrete_plinth", "fence_anthracite", "fence_anthracite_mesh", "paint_yellow")


GRASS_STEEP_NZ = 0.80     # grass faces steeper than ~1:1.33 (1:1.5 = n.z 0.83) count as walls too
GRASS_MATS = ("verge_grass", "shoulder_gravel")
SLIVER_M2 = 0.02          # exposed skirt face below this per source = sub-pixel sliver (~0.13 x 0.15 m; WORKING_VALUE)


def terrain_walls(parts, zc, hf, thresh=WALL_MAX, mask=None):
    """QA "vertical terrain wall > 0.15 m" (REVIEW r4 W-H5):
    a) steep faces (|n.z| < 0.26) of ground-level surfaces (road / paved layers: skirts, flanges) whose vertex stands
       more than `thresh` above the conformed terrain, unless the plan position is covered by other ground surfaces
       (all 4 surrounding nodes in the footprint `mask`: the skirt is buried under a neighbouring strip);
    b) grass / gravel faces steeper than ~1:1.33 with a vertical extent > `thresh` (squeezed ditch slopes).
    Kerb faces and edgings are real vertical faces and are skipped. Terrain sampled bilinearly (1 m grid)."""
    from streetscape.paved import bilinear    # local import: streetscape imports this module
    hs, where, by, area, slivers = [], [], {}, {}, [0]

    def covered(P):
        if mask is None:
            return np.zeros(len(P), bool)
        fi = np.clip(P[:, 0] - hf.x0, 0, mask.shape[1] - 1.001)
        fj = np.clip(hf.y1 - P[:, 1], 0, mask.shape[0] - 1.001)
        i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
        return mask[j0, i0] & mask[j0, i0 + 1] & mask[j0 + 1, i0] & mask[j0 + 1, i0 + 1]

    vg = {"steep_grass": 0, "skirt": 0, "max_m": 0.0, "worst": []}

    def note(p, P, h, kind):
        if p.src.endswith(":vg"):
            # ADR 0110: grass strips behind kerbs (roads.meshing._emit_verge) are exported inside the terrain mesh;
            # they are counted on their own ("verge_strips"; ratchet in tests/gis/test_junctions_r4.py), not as walls
            # of the road profile
            vg[kind] += len(h)
            if len(h) and float(np.max(h)) > vg["max_m"]:
                k_ = int(np.argmax(h))
                vg["max_m"] = float(np.max(h))
                vg["worst"] = [kind, p.src, round(float(P[k_][0]), 1), round(float(P[k_][1]), 1)]
            return
        hs.append(h)
        key = f"{kind}:j:{p.mat}" if p.src.startswith('j:') else f"{kind}:{p.mat}"
        by[key] = by.get(key, 0) + len(h)
        where.extend((kind, p.src, p.mat, float(q[0]), float(q[1]), float(v)) for q, v in zip(P, h))

    for p in parts:
        if p.layer not in ("road", "paved") or p.mat in WALL_SKIP_MATS or p.mat.startswith("collision"):
            continue
        V, T = p.V, p.T
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        nrm = np.cross(b - a, c - a)
        ln = np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
        nz = np.abs(nrm[:, 2]) / ln
        # a face thinner than the threshold (2 * area / longest edge) cannot show a wall taller than it: slivers
        # whose 3 vertices lie on one gutter / boundary line (Delaunay junction fills along a straight 50-200 m
        # gutter: "steep" normal, 1-2 cm wide, hidden behind the kerb face) are not walls (ADR 0033 v3.5.2)
        lmax = np.max(np.stack([np.linalg.norm(b - a, axis=1), np.linalg.norm(c - b, axis=1),
                                np.linalg.norm(a - c, axis=1)]), axis=0)
        thin = ln / np.maximum(lmax, 1e-9) < thresh
        slivers[0] += int(((nz < WALL_STEEP_NZ) & thin).sum())
        steep = (nz < WALL_STEEP_NZ) & ~thin
        if steep.any():
            P = V[np.unique(T[steep])]
            h = P[:, 2] - bilinear(zc, hf, P[:, 0], P[:, 1])
            k = (h > thresh) & ~covered(P)
            if k.any():
                note(p, P[k], h[k], "skirt")
                # exposed face area of the flagged faces (the part above the terrain), per source: separates real
                # walls from sub-pixel slivers (a vertex 0.2 m up on a 2 cm wide face)
                Ts = T[steep]
                A3 = V[Ts]
                hv = np.maximum(0.0, A3[:, :, 2] - bilinear(zc, hf, A3[:, :, 0].ravel(), A3[:, :, 1].ravel()).reshape(-1, 3))
                dz = np.maximum(A3[:, :, 2].max(1) - A3[:, :, 2].min(1), 1e-6)
                fa = 0.5 * ln[steep] * np.minimum(1.0, hv.mean(1) / dz)
                run = np.hypot(*(A3[:, :, :2].max(1) - A3[:, :, :2].min(1)).T)
                flag = (hv > thresh).any(1)
                if flag.any() and not p.src.endswith(":vg"):
                    key = p.src.split(":corner")[0]
                    r = area.setdefault(key, {"src": key, "mat": p.mat, "points": 0, "exposed_m2": 0.0, "run_m": 0.0,
                                              "max_h": 0.0, "e": float(P[k][0, 0]), "n": float(P[k][0, 1])})
                    r["points"] += int(k.sum())
                    r["exposed_m2"] += float(fa[flag].sum())
                    r["run_m"] += float(run[flag].sum())
                    r["max_h"] = max(r["max_h"], float(h[k].max()))
        if p.mat in GRASS_MATS:
            g = (nz >= WALL_STEEP_NZ) & (nz < GRASS_STEEP_NZ)
            if g.any():
                Tz = V[T[g]][:, :, 2]
                ext = Tz.max(1) - Tz.min(1)
                k = ext > thresh
                if k.any():
                    note(p, V[T[g][k]].mean(1), ext[k], "steep_grass")
    vg["max_m"] = round(vg["max_m"], 3)
    if not hs:
        return {"thresh_m": thresh, "count": 0, "max_m": 0.0, "p99_m": 0.0, "by_source": {}, "worst": [],
                "skirt_area": [], "thin_steep_faces_skipped": slivers[0], "verge_strips": vg}
    h = np.concatenate(hs)
    where.sort(key=lambda t: -t[5])
    rows = sorted(area.values(), key=lambda r: -r["exposed_m2"])
    for r in rows:
        r.update({k: round(r[k], 3) for k in ("exposed_m2", "run_m", "max_h")}, e=round(r["e"], 1), n=round(r["n"], 1),
                 visible=r["exposed_m2"] >= SLIVER_M2)
    return {"thresh_m": thresh, "count": int(len(h)), "max_m": round(float(h.max()), 3),
            "p99_m": round(float(np.percentile(h, 99)), 3), "by_source": by,
            "sliver_m2": SLIVER_M2, "skirt_area": rows, "thin_steep_faces_skipped": slivers[0], "verge_strips": vg,
            "worst": [{"kind": kd, "src": s, "mat": m, "e": round(e, 1), "n": round(n, 1), "h": round(v, 3)}
                      for kd, s, m, e, n, v in where[:30]]}
