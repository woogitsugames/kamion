"""Conform the 1 m NMT grid to the generated roads.

1. Rasterise every ground-level road triangle (carriageway, kerb tops, sidewalks, junction patches;
   not bridges, not vertical flanges) onto the terrain nodes -> road height + footprint mask.
2. Inside the footprint the terrain is pushed TERRAIN_UNDER_ROAD below the road surface (no z-fighting,
   nothing pokes through; the road flanges hide the step).
3. Outside, the nearest footprint node seeds the edge height. With a vector footprint,
   distances use the continuous outline in the roadside band and edge heights are interpolated.
   The terrain is clamped into the embankment cone: a BERM_W flat strip at the road edge,
   then 1 : EMBANKMENT_SLOPE cut or fill until it meets the NMT again. The raster-only
   metric remains available for callers without a footprint.
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


TERRAIN_UNDER_WALLED = 0.15   # m: ground kept under the surface of a walled ramp (fill, no soffit), c-p1-s23, WORKING_VALUE


def clamp_under_decks(z, deck, deck_mask, thickness, ground_mask):
    """Terrain under a deck stays >= 0.3 m below the soffit (except where a ground road runs)."""
    top = ndimage.maximum_filter(np.where(deck_mask, deck, -np.inf), size=3)
    under = np.isfinite(top) & ~ground_mask
    return np.where(under, np.minimum(z, top - thickness - 0.3), z)


def level_under_walled(z, fill, keep):
    """c-p2-s23 (REVIEW s23 c-p1 P2, g3b_ext34_s1482): ground inside the outline of a walled ramp (`fill`: nodes
    between the two wall lines + margin, build_world.walled_fill_mask) never stands above the nearest ground node
    outside it. The fill is hidden under the deck, but a node kept just under the ramp surface made the terrain
    triangles that cross the wall line climb through the wall face and its painted band (0.3-0.45 m above the
    wall foot at E -387 N -104). Nodes of `keep` (ground roads / paved) are not moved. Returns (z, nodes lowered)."""
    fill = np.asarray(fill, bool) & ~np.asarray(keep, bool)
    if not fill.any() or fill.all():
        return z, 0
    _, (jj, ii) = ndimage.distance_transform_edt(fill, return_indices=True)
    out = np.where(fill, np.minimum(z, z[jj, ii]), z)
    return out, int((out < z - 1e-6).sum())


def tidy(z, road, mask, dist, close_m=7, iters=150, smooth_slopes=True):
    """Visual cleanup after conform (visual review 2026-11-09, items 8):
    1. narrow enclosed strips (medians, splitter islands, gaps between a road and a yard, closed by
       `close_m` m) get a harmonic surface spanning the adjacent road edges (no lumps in medians);
    2. the slope band 1.5-12 m from the road is smoothed (sigma 1.2 m) to remove the faceted
       EDT-cone creases. Set smooth_slopes=False after continuous-outline conform:
       filtering that profile again mixes buried road nodes into the batter and
       reintroduces the raster edge, with a hard step at the band limits."""
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
    if smooth_slopes:
        band = (~mask) & ~closed & (dist > 1.5) & (dist < 12.0)
        sm = ndimage.gaussian_filter(out, 1.2)
        out = np.where(band, sm, out)
    return out


SOFT_UNDER = 0.04          # m: terrain just under grass verges / island grass (WORKING_VALUE)
SOFT_CLEAR_CELLS = 2       # ... only where no hard surface (carriageway, kerb, paving) is within this many nodes
FLOOR_STEP_M = 0.2         # ADR 0321: sample spacing on the verge triangles for the cell floor (WORKING_VALUE)
FLOOR_OUTSIDE_DROP_M = 0.20  # ADR 0321: max lowering of a node outside the footprint by the floor (WORKING_VALUE)
FLOOR_SKIRT_NZ = 0.35      # ADR 0330: faces steeper than ~70 deg (the buried skirt of a strip) are not a floor
# ADR 0330 (banks2-s24): behind a generated rural ditch the NMT still carries the REAL ditch (LIDAR, 1 m grid), usually
# 1-3 m further out than the rule profile (knyszyn-w E 120 N 795: generated ditch at 1-3 m from the shoulder, NMT trench
# 0.5-0.9 m deep at 4-6 m). Sampled on the diagonal 1 m grid that second trench reads as a row of hummocks / a sawtooth
# behind the back slope (bv_side_ditch). The generated ditch stands for the real one: in a band behind it the NMT
# trenches narrower than DITCH_RELIEF_CLOSE_M are filled (grey closing) and the micro-relief smoothed. WORKING_VALUE.
DITCH_RELIEF_DEPTH_M = 0.25     # seed: soft nodes whose verge floor lies this far below the road join height (a ditch)
DITCH_RELIEF_CLOSE_M = 5        # closing window (nodes = m): trenches narrower than this are filled
DITCH_RELIEF_SIGMA_M = 1.0      # gaussian smoothing of the filled surface
DITCH_RELIEF_BAND_M = (5.0, 9.0)  # full weight to 5 m from the ditch nodes, faded out at 9 m


def rasterise_floor(parts, hf, step=FLOOR_STEP_M):
    """ADR 0321: lowest surface height of the footprint parts within the four grid cells around every terrain node
    (+inf where none). A terrain triangle lies in the cells around each of its three nodes, so terrain nodes kept at
    floor - SOFT_UNDER can never interpolate above the surface between the nodes. `road - SOFT_UNDER` on the node
    alone did not hold in a rural ditch (1 : 1.5 slopes, 0.4 m flat bottom): a 1.41 m grid diagonal across the
    concave creases sat up to 0.24 m above the bottom, and the terrain cut through the back slope in a sawtooth of
    lighter grass (vqa-wave5 dk65-fields-nw, dk65-goniadzka). Samples: triangle vertices + a barycentric lattice at
    `step` m (min error on a 1 : 1.5 face ~0.1 m, inside the SOFT_UNDER + lattice slack)."""
    H, W = hf.z.shape
    floor = np.full((H, W), np.inf)
    tris = [p.V[p.T] for p in parts if p.footprint and len(p.T)]
    if not tris:
        return floor
    T = np.concatenate(tris)
    # ADR 0330: the vertical skirt under the outer edge of a strip is buried by design; as a floor it pulled every node
    # beside the ditch crown down by FLOOR_OUTSIDE_DROP_M (trough + exposed skirt = a ridge along the back slope)
    cr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nz = np.abs(cr[:, 2]) / np.maximum(np.linalg.norm(cr, axis=1), 1e-12)
    T = T[nz >= FLOOR_SKIRT_NZ]
    if not len(T):
        return floor
    ext = np.max(np.linalg.norm(T[:, [1, 2, 0], :2] - T[:, :, :2], axis=2), axis=1)
    nseg = np.clip(np.ceil(ext / step).astype(int), 1, 400)
    for k in np.unique(nseg):
        sel = T[nseg == k]
        a, b = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        keep = (a + b) <= k
        wa, wb = a[keep] / k, b[keep] / k
        wc = 1.0 - wa - wb
        for c0 in range(0, len(sel), max(1, 400000 // len(wa))):
            S_ = sel[c0:c0 + max(1, 400000 // len(wa))]
            P = (wa[None, :, None] * S_[:, None, 0, :] + wb[None, :, None] * S_[:, None, 1, :]
                 + wc[None, :, None] * S_[:, None, 2, :]).reshape(-1, 3)
            fi = P[:, 0] - hf.x0
            fj = hf.y1 - P[:, 1]
            i0 = np.floor(fi).astype(int)
            j0 = np.floor(fj).astype(int)
            for di in (0, 1):
                for dj in (0, 1):
                    ii, jj = i0 + di, j0 + dj
                    ok = (ii >= 0) & (jj >= 0) & (ii < W) & (jj < H)
                    np.minimum.at(floor, (jj[ok], ii[ok]), P[ok, 2])
    return floor


def ditch_relief(nmt, mask, soft, road, soft_floor):
    """ADR 0330: NMT with the trenches behind generated rural ditches filled and smoothed (see DITCH_RELIEF_*).
    Seeds are the soft (verge-only) nodes whose verge floor lies DITCH_RELIEF_DEPTH_M below the road join height; the
    surface is replaced within DITCH_RELIEF_BAND_M of them. A grey closing only fills concave features narrower than
    the window (an embankment toe or a field edge step is unchanged). Returns (nmt, nodes changed > 5 cm)."""
    if soft is None or soft_floor is None:
        return nmt, 0
    with np.errstate(invalid="ignore"):
        seed = soft & np.isfinite(soft_floor) & np.isfinite(road) & (road - soft_floor > DITCH_RELIEF_DEPTH_M)
    if not seed.any():
        return nmt, 0
    b0, b1 = DITCH_RELIEF_BAND_M
    d = ndimage.distance_transform_edt(~seed)
    w = np.clip((b1 - d) / (b1 - b0), 0.0, 1.0)
    w[mask] = 0.0          # under the footprint the road / verge height wins anyway (conform)
    sm = ndimage.gaussian_filter(ndimage.grey_closing(nmt, size=(DITCH_RELIEF_CLOSE_M, DITCH_RELIEF_CLOSE_M)),
                                 DITCH_RELIEF_SIGMA_M)
    out = nmt + w * (sm - nmt)
    return out, int((np.abs(out - nmt) > 0.05).sum())


def edge_distances(hf, mask, raster_dist, footprint, band_m=16.0):
    """Sub-cell distances to the actual surface outline, only in the roadside band.

    EDT measures from *grid nodes* inside the road. On a diagonal this moves the
    apparent edge by up to a cell at every row, imprinting teeth into the batter.
    Index individual outline segments, so querying a long road is still local.
    The far terrain keeps the inexpensive EDT and the road mask is never changed.
    """
    import shapely

    if footprint.is_empty:
        return raster_dist
    lines = shapely.get_parts(footprint.boundary)
    segments = []
    for line in lines:
        xy = shapely.get_coordinates(line)
        segments.extend(np.stack([xy[:-1], xy[1:]], axis=1))
    if not segments:
        return raster_dist
    tree = shapely.STRtree(shapely.linestrings(np.asarray(segments)))
    jj, ii = np.where(~mask & (raster_dist <= band_m))
    out = raster_dist.copy()
    for start in range(0, len(ii), 65536):
        j, i = jj[start:start + 65536], ii[start:start + 65536]
        points = shapely.points(hf.x0 + i, hf.y1 - j)
        _, distances = tree.query_nearest(points, all_matches=False, return_distance=True)
        # Fade back to the raster metric outside the visible batter to avoid a
        # discontinuity at the end of this band (WORKING_VALUE: last 4 metres).
        weight = np.clip((band_m - raster_dist[j, i]) / 4.0, 0.0, 1.0)
        out[j, i] += weight * (distances - out[j, i])
    return out


def conform(hf, road, mask, soft=None, footprint=None, soft_floor=None):
    """soft (optional bool grid): footprint nodes covered only by grass verge strips. Those that are at least
    SOFT_CLEAR_CELLS nodes from any hard surface get the terrain SOFT_UNDER under the grass instead of
    TERRAIN_UNDER_ROAD: the coarse terrain grid (1-2 m) used to dip 0.35 m inside narrow kerbed islands and behind
    verges and showed the strips' vertical flanges as green walls / "troughs" (REVIEW r3 W3, r4 W-H5)."""
    nmt = hf.z
    out = nmt.copy()
    if not mask.any():
        return out, np.zeros_like(nmt)
    # ADR 0330: one ditch per side - the NMT trench behind the generated ditch is filled (only with a floor, i.e. the
    # world build; tests / previews without soft_floor see the bare NMT as before)
    nmt, _ = ditch_relief(nmt, mask, soft, road, soft_floor)
    d, (jj, ii) = ndimage.distance_transform_edt(~mask, return_indices=True)
    zedge = road[jj, ii]
    if footprint is not None and not footprint.is_empty:
        d = edge_distances(hf, mask, d, footprint)
        # Interpolate the nearest-node height extension too: changing which
        # road node is closest must not create a vertical ridge along the slope.
        sm_edge = ndimage.gaussian_filter(zedge, 0.8)
        weight = np.where(mask, 0.0, np.clip((16.0 - d) / 4.0, 0.0, 1.0))
        zedge += weight * (sm_edge - zedge)
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
    if soft_floor is not None:
        # ADR 0321: no node (soft, hard or just outside the footprint) above the lowest verge surface in the four
        # cells around it: the terrain triangles stay under the ditch creases. Outside the footprint this reaches
        # one cell beyond the back slope only, where the battered skirt of the strip (FLANGE_DEPTH) covers the dip;
        # there the drop is capped at FLOOR_OUTSIDE_DROP_M (an uncapped 0.4-0.6 m trough showed beyond the ditch top
        # edge, knyszyn-w E 122 N 787; residual poke <= 0.4 cm in tests/gis/test_ditch_floor_0321.py)
        low = np.minimum(out, soft_floor - SOFT_UNDER)
        out = np.where(mask, low, np.maximum(low, out - FLOOR_OUTSIDE_DROP_M))
    return out, d


WALL_MAX = 0.15            # m: visible vertical step between a ground surface edge and the terrain (REVIEW r4 W-H5)
WALL_STEEP_NZ = 0.26       # |normal.z| below this = "vertical" face (steeper than ~75 deg)
WALL_SKIP_MATS = ("curb_concrete", "edging_concrete", "bridge_concrete", "bridge_soffit", "apron_sett", "apron_paving_light",
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
