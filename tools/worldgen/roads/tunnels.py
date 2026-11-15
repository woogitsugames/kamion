"""ADR 0211: cut-and-cover tunnel under an at-grade junction + retaining walls of the cutting.

OSM `tunnel=yes` on a road that runs in a cutting below an at-grade junction (rondo prof. Szymańskiego over the DK8
cutting, region bialystok-kleeberga): ADR 0206 only kept the terrain open (keep_tunnel_cut), so the island and the
pavements of the roundabout were a hole down to the cutting and the ring decks were one-sided from below. Here:

* **slab** - footprint F = convex hull of the tunnel carriageways (portal to portal, out to the back of the walls):
  closed concrete box (top face hidden 0.15 m under the ground, soffit at the road + a constant clearance, portal
  faces at both ends) in the `bridge` layer, so it casts shadows and occludes the baked sky / sun of the ground lighting
  (WorldSkyBake: bridge = solid) - the road under it is dark on every tier, also beyond the realtime shadow distance;
* **ground on the slab** - the 1 m terrain cells over F and behind the walls are re-emitted as a grass cover
  (bridge layer, `verge_grass`, src `tunnel:cover`; own primitive - merged into the terrain it was undone by the
  importer's terrain band, see _emit_cover) on the planes of the conformed terrain triangles; the terrain nodes
  under it go down;
* **walls** - tunnel walls (outer + a central wall between the carriageways, floor to soffit) and retaining walls of
  the open cutting beyond the portals (outer sides, wherever the bank behind is >= WALL_MIN_H above the footing):
  precast panels, coping, steel railing on top, collision wall (`collision_fence`), a footing strip from the side
  profile to the wall face;
* the ring decks over F lose their soffit / fascia / parapet / abutment / pier pieces (the slab carries them), the
  instances standing in the tunnel (lamps, trees, boards, signals) are dropped.

Regions without such a road (C, Dojlidy: only `building_passage`) get None from `plan` and are unchanged.
Values marked WORKING_VALUE are rules, not survey."""

from __future__ import annotations

import json
import math

import numpy as np
import shapely
from shapely.geometry import Polygon

from . import meshing as M
from .network import side_params, side_profile

SKIP_HW = ("service", "living_street", "footway", "path", "cycleway", "pedestrian", "steps", "track")
CLEARANCE_M = 4.70      # skrajnia pionowa drogi publicznej (rozporządzenie MI 24.06.2022, Dz.U. 2022 poz. 1518, § 31) UNVERIFIED paragraph
SOFFIT_MAX_M = 5.00     # soffit above the road when the cover allows it (+0.30 for signs / lights) WORKING_VALUE
SLAB_MIN_T = 0.80       # slab + ground cover over the soffit, WORKING_VALUE
WALL_GAP_M = 0.30       # wall face behind the outer end of the side profile, WORKING_VALUE
WALL_T = 0.50           # coping width (wall thickness at the top), WORKING_VALUE
COVER_M = 3.0           # grass cover behind the wall face (hides the terrain step of the 1 m grid)
NET_M = 3.0             # net under the conformed ground this far around the slab footprint (terrain LOD slits)
WALL_MIN_H = 1.0       # open-cut retaining wall where the bank behind is at least this high, WORKING_VALUE
WALL_BANK_LAT = (1.0, 4.0)   # bank height sampled this far behind the wall face (m)
WALL_MIN_RUN_M = 10.0
LOW_LOD_BAND_M = 4.5    # terrain LOD >= 2 (4 m grid; terrain_lod2 = terrain collision) held down to here behind the face
FLOOR_DROP_M = 0.35     # terrain under the cut / slab: road - this (as ADR 0206)
GROUP_M = 40.0          # tunnel runs whose middles are this close form one structure
RAIL_H = 1.10           # railing on the coping / portal edge (bridge parapet height class) WORKING_VALUE
STEP_M = 2.0
WALL_MAT = "ramp_wall_panels"


# --------------------------------------------------------------------------------------------- plan
def tunnel_edge_ids(graph: dict) -> set:
    return {e["id"] for e in graph["edges"]
            if str(e["attrs"].get("tunnel", {}).get("v", "no")) not in ("no", "building_passage")
            and e["attrs"]["highway"]["v"] not in SKIP_HW}


def _runs(net, eids):
    out = []
    for c in net.chains:
        if c.meta.get("absorbed") or c.sec_idx is None:
            continue
        tun = np.array([net.sec_list[int(k)].edge_id in eids for k in c.sec_idx])
        if not tun.any():
            continue
        idx = np.where(tun)[0]
        for r in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1):
            sa, sb = float(c.line.s[r[0]]), float(c.line.s[r[-1]])
            if sb - sa >= 8.0:
                out.append({"c": c, "sa": sa, "sb": sb})
    return out


def _side_info(c, side, s):
    kind, kh, wd, depth, mat = side_params(c, side, s)
    prof = side_profile(kind, kh, wd, depth, mat)
    return float(prof[-1][2]), float(prof[-1][1])        # outer extent u_end, top dz at the outer end


def plan(w, graph: dict):
    """Tunnel structures of the region (None when it has no tunnel road)."""
    eids = tunnel_edge_ids(graph)
    if not eids:
        return None
    runs = _runs(w.net, eids)
    if not runs:
        return None
    for r in runs:
        c = r["c"]
        sm = 0.5 * (r["sa"] + r["sb"])
        r["mid"] = c.line.point(sm)
    groups = []
    for r in runs:
        for g in groups:
            if min(np.hypot(*(r["mid"] - q["mid"])) for q in g["runs"]) < GROUP_M:
                g["runs"].append(r)
                break
        else:
            groups.append({"runs": [r]})
    for gi, g in enumerate(groups):
        g["id"] = f"tunnel{gi}"
        for r in g["runs"]:
            c = r["c"]
            sm = 0.5 * (r["sa"] + r["sb"])
            _, nn = c.line.frame(sm)
            r["inner"] = {}
            for side, sgn in (("L", 1.0), ("R", -1.0)):
                others = [q for q in g["runs"] if q is not r]
                r["inner"][side] = any(float(np.dot(q["mid"] - r["mid"], nn * sgn)) > 1.0 for q in others)
        # footprint: hull of the run strips out to the back of the outer walls
        pts = []
        for r in g["runs"]:
            c = r["c"]
            for s in np.linspace(r["sa"], r["sb"], max(2, int((r["sb"] - r["sa"]) / STEP_M) + 1)):
                p = c.line.point(s)
                _, nn = c.line.frame(s)
                hw = float(c.hw_at(s))
                for side, sgn in (("L", 1.0), ("R", -1.0)):
                    u, _ = _side_info(c, side, s)
                    lat = hw + u + WALL_GAP_M + (0.0 if r["inner"][side] else WALL_T)
                    pts.append(p + nn * sgn * lat)
        g["F"] = shapely.convex_hull(shapely.MultiPoint(np.array(pts)))
        # group axis (for portal edges)
        ts = []
        for r in g["runs"]:
            t, _ = r["c"].line.frame(0.5 * (r["sa"] + r["sb"]))
            ts.append(t if not ts or float(np.dot(t, ts[0])) >= 0 else -t)
        d = np.mean(ts, axis=0)
        g["axis"] = d / np.linalg.norm(d)
    return groups


# --------------------------------------------------------------------------------------------- helpers
class Grid:
    """Terrain node grid of the heightfield: node (j, i) at local (x0 + i, y1 - j)."""

    def __init__(self, hf, zc):
        self.x0, self.y1 = hf.x0, hf.y1
        self.z = zc
        self.H, self.W = zc.shape

    def ij(self, x, y):
        return np.rint(np.asarray(x) - self.x0).astype(int), np.rint(self.y1 - np.asarray(y)).astype(int)

    def bilinear(self, x, y, z=None):
        z = self.z if z is None else z
        fi = np.clip(np.asarray(x, float) - self.x0, 0, self.W - 1.001)
        fj = np.clip(self.y1 - np.asarray(y, float), 0, self.H - 1.001)
        i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
        a, b = fi - i0, fj - j0
        return ((1 - a) * (1 - b) * z[j0, i0] + a * (1 - b) * z[j0, i0 + 1] + (1 - a) * b * z[j0 + 1, i0]
                + a * b * z[j0 + 1, i0 + 1])

    def plane(self, x, y, z=None):
        """Height on the terrain TRIANGLES (diagonal NW-SE of every cell, terrain_mesh.chunks.grid_mesh)."""
        z = self.z if z is None else z
        fi = np.clip(np.asarray(x, float) - self.x0, 0, self.W - 1.001)
        fj = np.clip(self.y1 - np.asarray(y, float), 0, self.H - 1.001)
        i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
        a, b = fi - i0, fj - j0                      # a: +E, b: -N (row)
        za, zb_, zd, ze = z[j0, i0], z[j0, i0 + 1], z[j0 + 1, i0], z[j0 + 1, i0 + 1]
        # tri a-d-e (b >= a) / a-e-b (a > b)
        lower = b >= a
        z1 = za + b * (zd - za) + a * (ze - zd)
        z2 = za + a * (zb_ - za) + b * (ze - zb_)
        return np.where(lower, z1, z2)


def _poly_mask(poly, grid, buffer=0.0):
    """Nodes inside the polygon (node centres)."""
    if buffer:
        poly = poly.buffer(buffer)
    x0, y0, x1, y1 = poly.bounds
    i0, j1 = grid.ij(x0, y0)
    i1, j0 = grid.ij(x1, y1)
    i0, i1 = max(0, i0 - 1), min(grid.W - 1, i1 + 1)
    j0, j1 = max(0, j0 - 1), min(grid.H - 1, j1 + 1)
    m = np.zeros((grid.H, grid.W), bool)
    I, J = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
    X, Y = grid.x0 + I, grid.y1 - J
    m[j0:j1 + 1, i0:i1 + 1] = shapely.contains_xy(poly, X, Y)
    return m


def _strip_poly(c, ss, lat0, lat1, sgn):
    """Polygon of the band lat0..lat1 (absolute lateral distances per station, side sgn) along the stations ss."""
    ss = np.asarray(ss, float)
    P = c.line.point(ss)
    _, N = c.line.frame(ss)
    a = P + N * sgn * np.broadcast_to(np.asarray(lat0, float), ss.shape)[:, None]
    b = P + N * sgn * np.broadcast_to(np.asarray(lat1, float), ss.shape)[:, None]
    ring = np.concatenate([a, b[::-1]])
    return shapely.make_valid(Polygon(ring)).buffer(0)


DEBUG: dict = {}          # geometry of the last build() for dev QA scripts (not part of the stats)

# --------------------------------------------------------------------------------------------- build
def build(w, region_id: str, zc: np.ndarray, rmask: np.ndarray, instances: list, graph: dict, log=print):
    """Slab, walls, ground cover; edits zc in place. Returns (stats, low_cut) - low_cut = (mask, zfloor) for the
    terrain LODs >= 2 (None when nothing was built). Empty stats for a region without tunnel roads."""
    groups = plan(w, graph)
    if not groups:
        return {}, None
    grid = Grid(w.hf, zc)
    zc0 = zc.copy()
    from terrain_mesh import conform as CF
    run_chains = tuple({r["c"].id for g in groups for r in g["runs"]})
    oz, other_mask = CF.rasterise([p for p in w.buf.parts if p.layer == "road" and p.footprint
                                   and not p.src.startswith(run_chains)], w.hf)
    deck_parts = [p for p in w.buf.parts if p.layer == "bridge" and not p.src.endswith(":parapet")]
    for p in deck_parts:
        p.footprint = True
    deck, deck_mask = CF.rasterise(deck_parts, w.hf)
    for p in deck_parts:
        p.footprint = False
    # ground over the slab: the NMT (LiDAR ground class) runs through the structure at the level of the cut and the
    # conform only follows the roads, so the island / verges on the slab are interpolated from what stands at grade
    # around and on it: ring decks, at-grade roads and junction plates, the banks of the cut
    zc_placed = zc0.copy()            # the ground the streetscape placed its instances on
    zc0 = _upper_ground(groups, grid, zc0, oz, other_mask, deck, deck_mask)
    # Other roads / paved areas at grade beside the cut (collectors on the bank top, ADR 0211 r1: 341 lane obstacles
    # + 185 markings on grass) keep their own conformed terrain: outside the slab their cells are not re-emitted;
    # on the slab (junction plates, ring) the ground stays under them like the terrain did (roads.consistency skips
    # the `tunnel` parts: terrain-equivalent, not a road surface).
    from scipy.ndimage import binary_dilation
    pv = [p for p in w.buf.parts if p.layer in ("paved", "plot_ground") and len(p.T)]
    for p in pv:
        p._fp, p.footprint = p.footprint, True
    pz_, pmask_ = CF.rasterise(pv, w.hf)
    for p in pv:
        p.footprint = p._fp
        del p._fp
    occ = other_mask | pmask_ | deck_mask
    occ_z = np.where(other_mask, oz, -np.inf)
    occ_z = np.maximum(occ_z, np.where(deck_mask, deck, -np.inf))
    occ_z = np.maximum(occ_z, np.where(pmask_, pz_, -np.inf))
    occ_d = binary_dilation(occ, iterations=1)
    cell_occ = np.zeros_like(occ_d)
    cell_occ[:-1, :-1] = occ_d[:-1, :-1] | occ_d[1:, :-1] | occ_d[:-1, 1:] | occ_d[1:, 1:]
    zocc = np.where(binary_dilation(occ, iterations=1),
                    np.maximum(occ_z, np.maximum(np.roll(occ_z, 1, 0), np.roll(occ_z, 1, 1))), -np.inf)

    def under_other(V2, z):
        fi, fj = grid.ij(V2[:, 0], V2[:, 1])
        fi, fj = np.clip(fi, 0, grid.W - 1), np.clip(fj, 0, grid.H - 1)
        zo = zocc[fj, fi]
        on_slab = shapely.contains_xy(Fu, V2[:, 0], V2[:, 1])
        return np.where(np.isfinite(zo) & on_slab, np.minimum(z, zo - 0.9), z)

    Fu = shapely.union_all([g["F"] for g in groups]).buffer(0.5)


    buf = w.buf
    stats = {"groups": []}
    lower = np.full(zc.shape, np.inf)          # per node: max allowed height (terrain held down)
    low_mask = np.zeros(zc.shape, bool)        # LOD >= 2 band
    cover_cells = np.zeros(zc.shape, bool)     # cell (j, i) = square with NW node (j, i)
    clip_polys = []                            # where the re-emitted ground is visible
    col_polys = []                             # grass collision over the slab / behind walls
    blend = []                                 # (polygon of the wall-top blend, line, wall-top function)
    walls_out = []
    corridor = []                              # floor of the cut between the outer walls (+ the slab footprints)
    near_face = np.zeros(zc.shape, bool)       # cover cells next to a wall face: never left to other surfaces
    for g in groups:
        F = g["F"]
        runs = g["runs"]

        def zroad(q, runs=runs):
            best = -np.inf
            for r in runs:
                c = r["c"]
                s, _lat = c.line.project(q)
                s = min(max(s, r["sa"] - 20.0), r["sb"] + 20.0)
                hw = float(c.hw_at(s))
                best = max(best, float(np.max(c.crossfall_z(np.array([s, s]), np.array([-hw, hw])))))
            return best

        # constant clearance over the whole structure: what the thinnest cover allows, in [CLEARANCE, SOFFIT_MAX]
        Fi = F.buffer(-1.0)
        xs, ys = np.meshgrid(np.arange(F.bounds[0], F.bounds[2], 2.0), np.arange(F.bounds[1], F.bounds[3], 2.0))
        inside = shapely.contains_xy(Fi, xs, ys)
        qs = np.column_stack([xs[inside], ys[inside]])
        zr = np.array([zroad(q) for q in qs])
        cover = grid.plane(qs[:, 0], qs[:, 1], zc0) - zr
        clear = float(np.clip(np.percentile(cover, 5) - SLAB_MIN_T, CLEARANCE_M, SOFFIT_MAX_M))
        deficit = int((cover < clear + SLAB_MIN_T - 0.05).sum())
        gst = {"id": g["id"], "ways": sorted({str(e).split(":")[0] for r in runs for e, _ in r["c"].edges}),
               "runs": [{"chain": r["c"].id, "s": [round(r["sa"], 1), round(r["sb"], 1)]} for r in runs],
               "footprint_m2": round(F.area), "clearance_m": round(clear, 2),
               "cover_m": [round(float(cover.min()), 2), round(float(np.median(cover)), 2)],
               "thin_cover_nodes": deficit}
        g["clear"] = clear
        g["zroad"] = zroad

        # ---- walls along every run side (tunnel + open cut on outer sides)
        for r in runs:
            c = r["c"]
            for side, sgn in (("L", 1.0), ("R", -1.0)):
                inner = r["inner"][side]
                s0, s1 = (r["sa"], r["sb"]) if inner else (max(c.t_a, r["sa"] - 400.0), min(c.length - c.t_b, r["sb"] + 400.0))
                ss = np.arange(s0, s1 + 1e-6, STEP_M)
                if len(ss) < 2:
                    continue
                P = c.line.point(ss)
                _, N = c.line.frame(ss)
                hw = c.hw_at(ss)
                info = [_side_info(c, side, s) for s in ss]
                u_end = np.array([a for a, _ in info])
                top_dz = np.array([b for _, b in info])
                lat_w = hw + u_end + WALL_GAP_M
                # a wall does not jog where the side profile changes (kerb 0.15 m <-> verge 2.85 m): never closer
                # than the profile allows, steps eased over ~10 m (running max 6 m, then mean 4 m)
                from scipy.ndimage import maximum_filter1d, uniform_filter1d
                lat_w = uniform_filter1d(maximum_filter1d(lat_w, 7, mode="nearest"), 5, mode="nearest")
                zedge = c.crossfall_z(ss, sgn * hw)
                zfoot = zedge + top_dz
                face = P + N * sgn * lat_w[:, None]
                # stations within 1 m of the portal plane keep the open-cut top (the portal face hides the step)
                probe = face - N * sgn * 1.5          # toward the own road: lateral position safely inside F
                in_F = shapely.contains_xy(F.buffer(-1.0), probe[:, 0], probe[:, 1])
                # bank behind the wall face (natural / conformed terrain)
                bank = np.max([grid.bilinear(*(P + N * sgn * (lat_w + d)[:, None]).T, zc0)
                               for d in np.linspace(*WALL_BANK_LAT, 4)], axis=0)
                # other roads at the face (a slip road joining the cut): no wall there
                fi, fj = grid.ij(face[:, 0], face[:, 1])
                ok = (fi >= 0) & (fi < grid.W) & (fj >= 0) & (fj < grid.H)
                other = np.zeros(len(ss), bool)
                if ok.any():
                    # only a road down in the cut (joining it) stops the wall; a path on the bank top does not
                    other[ok] = other_mask[fj[ok], fi[ok]] & (oz[fj[ok], fi[ok]] < zfoot[ok] + 1.5)
                want = in_F | ((bank - zfoot >= WALL_MIN_H) & ~other)
                if inner:
                    want = in_F.copy()
                else:
                    # a short dip of the bank (<= 14 m) does not break the wall; a road at the face does
                    idx = np.where(want)[0]
                    for a_, b_ in zip(idx[:-1], idx[1:]):
                        if 1 < b_ - a_ <= int(14.0 / STEP_M) + 1 and not other[a_:b_].any():
                            want[a_:b_] = True
                    gaps = []
                    idx = np.where(want)[0]
                    for a_, b_ in zip(idx[:-1], idx[1:]):
                        if b_ - a_ > 1:
                            gaps.append([round(float(ss[a_]), 1), round(float(ss[b_]), 1),
                                         int(other[a_:b_].sum()), round(float(np.min(bank[a_:b_] - zfoot[a_:b_])), 2)])
                    gst.setdefault("wall_gaps", []).append({"chain": c.id, "side": side, "gaps": gaps})
                idx = np.where(want)[0]
                for run in (np.split(idx, np.where(np.diff(idx) > 1)[0] + 1) if len(idx) else []):
                    if len(run) < 2 or ss[run[-1]] - ss[run[0]] < WALL_MIN_RUN_M:
                        continue
                    sl = slice(run[0], run[-1] + 1)
                    if not inner:      # the open cut between the walls (closed over the median below)
                        corridor.append(_strip_poly(c, ss[sl], -(hw[sl] + 4.0), lat_w[sl] - 0.05, sgn))
                    walls_out.append(_build_wall(buf, g, c, side, sgn, ss[sl], P[sl], N[sl], hw[sl], u_end[sl],
                                                 lat_w[sl], zfoot[sl], bank[sl], in_F[sl], inner, grid, zc0, lower,
                                                 low_mask, cover_cells, clip_polys, col_polys, blend, near_face))
        # ---- slab
        # railing mask: roads AT GRADE only (the tunnel carriageways below do not count: r3 had no railing over the lanes)
        _build_slab(buf, g, grid, zc0, lower, cover_cells, clip_polys, col_polys, other_mask | deck_mask)
        stats["groups"].append(gst)

    # ---- ground on the slab / behind the walls (terrain-merged grass), terrain held down under it
    in_slab = np.zeros_like(cover_cells)
    for g in groups:
        _mark_cells(in_slab, grid, g["F"].buffer(0.5))
    excluded = cover_cells & cell_occ & ~in_slab & ~near_face
    cover_cells &= ~excluded
    K = shapely.union_all(clip_polys).buffer(0) if clip_polys else None
    gtris = _emit_cover(buf, grid, zc0, cover_cells, K, blend)
    # interior nodes of the cover: all four incident cells covered
    cc = cover_cells
    interior = np.zeros_like(cc)
    interior[1:, 1:] = cc[1:, 1:] & cc[:-1, :-1] & cc[1:, :-1] & cc[:-1, 1:]
    # the whole cut between the outer walls goes to its floor: the conform lifted nodes there to at-grade surfaces
    # nearby (junction plates, crossings at the portals: r1 had a grass wall across both portals)
    cut_m = np.zeros_like(interior)
    if corridor:
        CU = shapely.union_all(corridor + [g["F"] for g in groups]).buffer(0)
        DEBUG["cut_raw"] = CU                 # dev QA (artifacts/tunnel-0211/dev_qa.py): the cut between the wall faces
        # Net under the conformed ground around the cover (the cells left to other surfaces and a ring to
        # NET_M beyond the cover): the conformed terrain planes - 3 cm. Invisible under the 1 m terrain; the 2 m / 4 m
        # terrain LODs (Low tier near terrain = 2 m grid, min-filtered next to roads) carry the lowered nodes 1-4 m
        # further out and opened slits down to the floor between the cover and the pavements beside it (dev QA B).
        net_poly = shapely.union_all([K] + [g["F"].buffer(NET_M) for g in groups]).difference(CU.buffer(0.3)).buffer(0)
        net_cells = np.zeros_like(cover_cells)
        _mark_cells(net_cells, grid, net_poly.buffer(0.75))
        net_cells &= ~cover_cells
        gtris += _emit_cover(buf, grid, zc0, net_cells, net_poly, [], adjust=lambda V2, z: z - 0.03)
        CU = CU.buffer(5.0).buffer(-5.0)
        cut_m = _poly_mask(CU, grid)
    floor_all = _floor_field(groups, grid, interior | low_mask | cut_m)
    lower = np.where(interior | cut_m, np.minimum(lower, floor_all), lower)
    sel = zc > lower
    drop = zc[sel] - lower[sel]
    zc[sel] = lower[sel]
    low_z = np.where(low_mask, np.minimum(zc, floor_all), zc)
    # grass collision on the slab / behind the walls (terrain collision is held down there)
    if col_polys:
        _emit_cover_collision(buf, grid, zc0, shapely.union_all(col_polys).buffer(0), blend)
    stats["walls"] = walls_out
    stats["terrain"] = {"nodes_lowered": int(sel.sum()), "max_drop_m": round(float(drop.max()) if drop.size else 0.0, 2),
                        "cover_cells": int(cover_cells.sum()), "cover_cells_left_to_other_surfaces": int(excluded.sum()),
                        "cover_tris": gtris, "cut_nodes": int(cut_m.sum()), "low_lod_nodes": int(low_mask.sum())}
    stats["inside"] = _dress_inside(w, groups)
    stats["culled"] = _cull(w, groups, instances, lambda x, y: float(grid.plane(x, y, zc0) - grid.plane(x, y, zc_placed)),
                            lambda x, y: bool(deck_mask[grid.ij(x, y)[1], grid.ij(x, y)[0]]))
    return stats, (low_mask, low_z)


def _floor_field(groups, grid, need):
    """Floor height on the nodes `need`: nearest run axis road height - FLOOR_DROP (inf elsewhere)."""
    from scipy.spatial import cKDTree
    P, Z = [], []
    for g in groups:
        for r in g["runs"]:
            c = r["c"]
            ss = np.arange(max(0.0, r["sa"] - 420.0), min(c.length, r["sb"] + 420.0), 1.0)
            P.append(c.line.point(ss))
            Z.append(c.zc(ss))
    out = np.full((grid.H, grid.W), np.inf)
    jj, ii = np.where(need)
    if not len(jj):
        return out
    _d, k = cKDTree(np.concatenate(P)).query(np.column_stack([grid.x0 + ii, grid.y1 - jj]))
    out[jj, ii] = np.concatenate(Z)[k] - FLOOR_DROP_M
    return out


UPPER_MIN_M = 3.0       # a road / deck this high over the tunnel road counts as "at grade" (slab ground samples)
UPPER_TERRAIN_M = 4.5   # terrain samples: only this high (bank tops; the conformed slope of the cut is lower)


def _upper_ground(groups, grid, zc0, oz, omask, deck, dmask):
    """Copy of zc0 with the nodes of every footprint F replaced by the ground at grade over the slab: linear
    interpolation (nearest outside the hull) of the samples within F + 8 m that stand >= UPPER_MIN_M over the tunnel
    road - ring decks (surface - 0.25), other roads / junction plates (surface - 0.08), conformed terrain (banks).
    Never below zc0."""
    from scipy.interpolate import griddata
    out = zc0.copy()
    for g in groups:
        F = g["F"]
        near = _poly_mask(F.buffer(8.0), grid)
        fin = _poly_mask(F.buffer(1.5), grid)      # every node of a cell that touches F (cover planes at the portal edge)
        jj, ii = np.where(near)
        zr = _floor_field([g], grid, near)[jj, ii] + FLOOR_DROP_M
        cand = np.where(dmask[jj, ii], deck[jj, ii] - 0.25,
                        np.where(omask[jj, ii], oz[jj, ii] - 0.08, zc0[jj, ii]))
        is_t = ~dmask[jj, ii] & ~omask[jj, ii]         # terrain: only the bank tops, not the slope of the cut
        ok = np.isfinite(cand) & (cand - zr >= np.where(is_t, UPPER_TERRAIN_M, UPPER_MIN_M))
        if ok.sum() < 3:
            continue
        P = np.column_stack([ii[ok], jj[ok]]).astype(float)
        fj, fi = np.where(fin)
        Q = np.column_stack([fi, fj]).astype(float)
        z = griddata(P, cand[ok], Q, method="linear")
        bad = ~np.isfinite(z)
        if bad.any():
            z[bad] = griddata(P, cand[ok], Q[bad], method="nearest")
        # never thinner than clearance + slab over the road axis (all surfaces at grade here stand 5.75-6.2 m above)
        zmin = _floor_field([g], grid, fin)[fj, fi] + FLOOR_DROP_M + CLEARANCE_M + SLAB_MIN_T
        # only nodes below grade are filled: a node already at grade keeps its conformed height (oz / deck are per-node
        # maxima incl. kerb tops and caps and would put grass slivers above the asphalt)
        zr_f = zmin - CLEARANCE_M - SLAB_MIN_T
        low = out[fj, fi] < zmin              # below clearance + slab: not at grade (cut level or the conformed slope)
        out[fj[low], fi[low]] = np.maximum(z[low], zmin[low])
        g["upper_samples"] = int(ok.sum())
    return out


def _mark_cells(cover_cells, grid, poly):
    """Cells (NW node index) whose centre lies in poly."""
    x0, y0, x1, y1 = poly.bounds
    i0, j1 = grid.ij(x0, y0)
    i1, j0 = grid.ij(x1, y1)
    i0, i1, j0, j1 = max(0, i0 - 1), min(grid.W - 2, i1 + 1), max(0, j0 - 1), min(grid.H - 2, j1 + 1)
    I, J = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
    X, Y = grid.x0 + I + 0.5, grid.y1 - J - 0.5
    cover_cells[j0:j1 + 1, i0:i1 + 1] |= shapely.contains_xy(poly, X, Y)


def _build_wall(buf, g, c, side, sgn, ss, P, N, hw, u_end, lat_w, zfoot, bank, in_F, inner, grid, zc0, lower,
                low_mask, cover_cells, clip_polys, col_polys, blend, near_face):
    src = f"{g['id']}:{c.id}:{side}:wall"
    zr = c.zc(ss)
    soffit = zr + g["clear"]
    # wall top: soffit in the tunnel, smoothed bank outside (running max 9 m, mean 5 m), never below footing + MIN_H
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    btop = uniform_filter1d(maximum_filter1d(bank, 5, mode="nearest"), 3, mode="nearest")
    # in the tunnel the wall runs 0.3 m up into the slab (the soffit follows the higher carriageway edge + crossfall)
    top = np.where(in_F, soffit + 0.3, np.maximum(btop, zfoot + WALL_MIN_H))
    face = P + N * sgn * lat_w[:, None]
    bot = zfoot - 0.40
    A = np.column_stack([face, bot])
    B = np.column_stack([face, top])

    def strip(layer, mat, A_, B_, suffix):
        # meshing._strip faces right of the station direction (-N); a face looking at the road (-N * sgn) is
        # reversed on the right side
        M._strip(buf, layer, mat, A_, B_, src + suffix, both=False)
        if sgn < 0:
            buf.parts[-1].T = buf.parts[-1].T[:, [0, 2, 1]]

    strip("bridge", WALL_MAT, A, B, "")
    # back face (0.3 m behind, hidden in the ground): the wall casts its realtime shadow onto the road when the sun is
    # behind it (single-sided faces are culled in the shadow pass) - the banks are terrain, which casts none
    back = np.column_stack([P + N * sgn * (lat_w + 0.3)[:, None], bot])
    backt = np.column_stack([P + N * sgn * (lat_w + 0.3)[:, None], top])
    M._strip(buf, "bridge", WALL_MAT, back, backt, src + ":back", both=False)
    if sgn > 0:
        buf.parts[-1].T = buf.parts[-1].T[:, [0, 2, 1]]
    strip("collision", "collision_fence", A, B, ":col")
    # footing strip from the side profile end to the face (hides the terrain step in front of the wall)
    a0 = P + N * sgn * (hw + u_end)[:, None]
    V = np.concatenate([np.column_stack([a0, zfoot])[:, None, :], np.column_stack([face, zfoot])[:, None, :]],
                       axis=1).reshape(-1, 3)
    T = M.grid_tris(len(ss), 2, flip=(sgn < 0))          # up-facing
    buf.add("bridge", "bridge_concrete", V, V[:, :2], T, src=src + ":footing")
    # terrain in front of the face and under the footing: below the footing
    # (to 1.2 m BEHIND the face: a node there left on the bank made grass pyramids in front of the wall, r2)
    band = _strip_poly(c, ss, hw + u_end - 0.6, lat_w + 1.2, sgn)
    _mark_cells(near_face, grid, _strip_poly(c, ss, lat_w - 1.0, lat_w + 2.4, sgn))
    m = _poly_mask(band, grid)
    # per node: footing height of the nearest station - 0.15
    jj, ii = np.where(m)
    if len(jj):
        X = np.column_stack([grid.x0 + ii, grid.y1 - jj])
        k = np.argmin(((X[:, None, :] - P[None, :, :]) ** 2).sum(-1), axis=1)
        lower[jj, ii] = np.minimum(lower[jj, ii], zfoot[k] - 0.15)
    # LOD >= 2 band (terrain collision) and the cover behind the face
    lowb = _strip_poly(c, ss, hw + u_end - 0.6, lat_w + LOW_LOD_BAND_M, sgn)
    low_mask |= _poly_mask(lowb, grid)
    cov = _strip_poly(c, ss, lat_w - 1.0, lat_w + COVER_M, sgn)
    _mark_cells(cover_cells, grid, cov)
    clip_polys.append(_strip_poly(c, ss, lat_w + (0.0 if inner else WALL_T), lat_w + COVER_M + 3.0, sgn))
    col_polys.append(_strip_poly(c, ss, lat_w, lat_w + LOW_LOD_BAND_M + 4.0, sgn))
    rail_m = 0.0
    if inner:
        # end faces of the central wall at both portals: half the gap to the other carriageway's wall face each
        for k, dirn in ((0, -1.0), (len(ss) - 1, 1.0)):
            gap = 1e9
            for r2 in g["runs"]:
                if r2["c"] is c:
                    continue
                s2, l2 = r2["c"].line.project(face[k])
                u2, _ = _side_info(r2["c"], "L" if l2 > 0 else "R", s2)
                gap = min(gap, abs(l2) - float(r2["c"].hw_at(s2)) - u2 - WALL_GAP_M)
            if not (0.05 < gap < 30.0):
                continue
            q0, q1 = face[k], face[k] + N[k] * sgn * (gap / 2 + 0.05)
            Vc = np.array([[*q0, bot[k]], [*q1, bot[k]], [*q1, top[k]], [*q0, top[k]]])
            Tc = np.array([[0, 1, 2], [0, 2, 3]])
            tq = np.array([N[k][1], -N[k][0]])
            nrm = np.cross(np.append(q1 - q0, 0.0), [0.0, 0.0, 1.0])[:2]
            if float(np.dot(nrm, tq * dirn)) < 0:
                Tc = Tc[:, [0, 2, 1]]
            buf.add("bridge", WALL_MAT, Vc, np.column_stack([[0.0, gap / 2, gap / 2, 0.0], Vc[:, 2] - bot[k]]),
                    Tc, src=src + ":end")
    if not inner:
        out = ~in_F
        idx = np.where(out)[0]
        for run in (np.split(idx, np.where(np.diff(idx) > 1)[0] + 1) if len(idx) else []):
            if len(run) < 2:
                continue
            sl = slice(run[0], run[-1] + 1)
            fc, tp, nn = face[sl], top[sl], N[sl]
            # coping: top + front lip
            back = fc + nn * sgn * WALL_T
            ct = np.column_stack([fc - nn * sgn * 0.02, tp + 0.05])
            cb = np.column_stack([back, tp + 0.05])
            V = np.concatenate([ct[:, None, :], cb[:, None, :]], axis=1).reshape(-1, 3)
            buf.add("bridge", "bridge_concrete", V, V[:, :2], M.grid_tris(len(fc), 2, flip=(sgn < 0)), src=src + ":coping")
            lip_b = np.column_stack([fc - nn * sgn * 0.02, tp - 0.25])
            strip("bridge", "bridge_concrete", lip_b, ct, ":coping")
            # back face of the coping down into the ground cover
            bb = np.column_stack([back, tp - 0.30])
            M._strip(buf, "bridge", "bridge_concrete", bb, cb, src + ":coping", both=False)
            if sgn > 0:                                   # faces away from the road (+N * sgn)
                buf.parts[-1].T = buf.parts[-1].T[:, [0, 2, 1]]
            # end caps where the wall stops in the open cutting (not at the portal)
            for k, dirn in ((run[0], -1.0), (run[-1], 1.0)):
                nb = k + int(dirn)
                if 0 <= nb < len(ss) and in_F[nb]:
                    continue
                q0, q1 = face[k], face[k] + N[k] * sgn * WALL_T
                Vc = np.array([[*q0, bot[k]], [*q1, bot[k]], [*q1, top[k] + 0.05], [*q0, top[k] + 0.05]])
                Tc = np.array([[0, 1, 2], [0, 2, 3]])
                # normal of (q1 - q0) x up points along -t * sgn ... want +t * dirn
                tq = np.array([N[k][1], -N[k][0]])          # tangent t (N = left normal of t)
                nrm = np.cross(np.append(q1 - q0, 0.0), [0.0, 0.0, 1.0])[:2]
                if float(np.dot(nrm, tq * dirn)) < 0:
                    Tc = Tc[:, [0, 2, 1]]
                buf.add("bridge", WALL_MAT, Vc, np.column_stack([[0.0, WALL_T, WALL_T, 0.0], Vc[:, 2] - bot[k]]),
                        Tc, src=src + ":end")
            # railing where the drop is a fall hazard
            hz = (tp - (zfoot[sl])) >= 1.0
            if hz.sum() >= 2:
                rail_m += _railing(buf, fc + nn * sgn * 0.25, tp + 0.05, hz, src + ":rail")
            blend.append((fc, back, tp + 0.05, nn * sgn))
    return {"chain": c.id, "side": side, "inner": inner, "s": [round(float(ss[0]), 1), round(float(ss[-1]), 1)],
            "len_m": round(float(ss[-1] - ss[0]), 1), "tunnel_m": round(float(in_F.sum() * STEP_M), 1),
            "h_max_m": round(float((top - zfoot).max()), 2), "rail_m": round(rail_m, 1),
            "lat_w_m": [round(float(lat_w.min()), 2), round(float(lat_w.max()), 2)]}


def _railing(buf, line, z, keep, src):
    """Steel railing (handrail + mid rail + posts every 2 m) along a 2-D polyline at height z (top of the base)."""
    idx = np.where(keep)[0]
    total = 0.0
    for run in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1):
        if len(run) < 2:
            continue
        L = line[run]
        Z = z[run]
        d = np.gradient(L, axis=0)
        d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
        nrm = np.column_stack([-d[:, 1], d[:, 0]])
        for z0, z1, th in ((RAIL_H - 0.10, RAIL_H, 0.06), (0.45, 0.60, 0.04)):
            o = np.column_stack([L, Z])
            i = np.column_stack([L - nrm * th, Z])
            for a, b in (((i, z0), (i, z1)), ((i, z1), (o, z1)), ((o, z1), (o, z0)), ((o, z0), (i, z0))):
                A, B = a[0].copy(), b[0].copy()
                A[:, 2] += a[1]
                B[:, 2] += b[1]
                V = np.concatenate([A[:, None, :], B[:, None, :]], axis=1).reshape(-1, 3)
                for flip in (False, True):
                    buf.add("bridge", "barrier_steel", V, V[:, :2], M.grid_tris(len(L), 2, flip=flip), src=src)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(L, axis=0).T))])
        total += float(s[-1])
        for sp in np.arange(0.0, s[-1] + 1e-6, 2.0):
            p = np.array([np.interp(sp, s, L[:, 0]), np.interp(sp, s, L[:, 1])])
            k = min(int(np.searchsorted(s, sp)), len(L) - 1)
            M.box(buf, "bridge", "barrier_steel", p, d[k], 0.04, 0.03, float(np.interp(sp, s, Z)),
                  float(np.interp(sp, s, Z)) + RAIL_H, src)
    return total


def _build_slab(buf, g, grid, zc0, lower, cover_cells, clip_polys, col_polys, rmask, adjust=None):
    F = g["F"]
    src = g["id"] + ":slab"
    zroad, clear = g["zroad"], g["clear"]
    # 2 m grid over F (clipped), heights: top = min of the ground over the cell - 0.15, soffit = road + clearance
    tris = _clip_grid(F, 2.0, F.bounds)
    if not len(tris):
        return
    flat = tris.reshape(-1, 2)
    uniq, inv = np.unique(np.round(flat, 3), axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    zr = np.array([zroad(q) for q in uniq])
    ztop = np.min([grid.plane(uniq[:, 0] + dx, uniq[:, 1] + dy, zc0) for dx in (-1.0, 0.0, 1.0)
                   for dy in (-1.0, 0.0, 1.0)], axis=0) - 0.15
    if adjust is not None:                       # under a deck / junction plate: out of the surface window
        ztop = adjust(uniq, ztop + 0.05) - 0.05
    zsof = zr + clear
    ztop = np.maximum(ztop, zsof + 0.3)
    T = inv.reshape(-1, 3)
    Vt = np.column_stack([uniq, ztop])
    buf.add("bridge", "bridge_concrete", Vt, uniq, T, src=src + ":top")
    Vs = np.column_stack([uniq, zsof])
    buf.add("bridge", "bridge_soffit", Vs, uniq, T[:, [0, 2, 1]], src=src + ":soffit")
    # portal faces: boundary edges of F across the axis, soffit -> ground at the edge, facing out
    ring = np.asarray(F.exterior.coords)
    if shapely.Polygon(ring).exterior.is_ccw is False:
        ring = ring[::-1]
    portal_m = 0.0
    for a, b in zip(ring[:-1], ring[1:]):
        e = b - a
        L = float(np.hypot(*e))
        if L < 0.5:
            continue
        nout = np.array([e[1], -e[0]]) / L            # outward for a CCW ring
        if abs(float(np.dot(nout, g["axis"]))) < 0.6:
            continue
        n = max(2, int(L / 1.0) + 1)
        Q = a + np.outer(np.linspace(0, 1, n), e)
        zr_ = np.array([zroad(q) for q in Q])
        zg = grid.plane(Q[:, 0], Q[:, 1], zc0)
        A = np.column_stack([Q, zr_ + clear])
        B = np.column_stack([Q, np.maximum(zg, zr_ + clear + 0.3)])
        # meshing._strip faces right of a->b = outward on a CCW ring
        M._strip(buf, "bridge", "bridge_concrete", A, B, src + ":portal", both=False)
        portal_m += L
        # railing on the portal edge (0.3 m in), not across a road surface
        inl = Q - nout * 0.3
        fi, fj = grid.ij(inl[:, 0], inl[:, 1])
        ok = (fi >= 0) & (fi < grid.W) & (fj >= 0) & (fj < grid.H)
        keep = np.zeros(len(Q), bool)
        keep[ok] = ~rmask[fj[ok], fi[ok]]
        _railing(buf, inl, grid.plane(inl[:, 0], inl[:, 1], zc0), keep, src + ":rail")
    g["portal_m"] = portal_m
    _mark_cells(cover_cells, grid, F.buffer(-0.01))
    clip_polys.append(F)
    col_polys.append(F)


def _clip_grid(poly, step, bounds):
    """Triangles (k, 3, 2) of a square grid (NW-SE diagonal) clipped to poly."""
    x0, y0, x1, y1 = bounds
    x0, y0 = math.floor(x0 / step) * step, math.floor(y0 / step) * step
    out = []
    for x in np.arange(x0, x1 + step, step):
        for y in np.arange(y0, y1 + step, step):
            nw, ne, sw, se = (x, y + step), (x + step, y + step), (x, y), (x + step, y)
            for tri in ((nw, sw, se), (nw, se, ne)):
                out += _clip_tri(np.array(tri, float), poly)
    return np.array(out).reshape(-1, 3, 2) if out else np.zeros((0, 3, 2))


def _clip_tri(tri, poly):
    t = Polygon(tri)
    if poly.contains(t):
        return [tri]
    if not poly.intersects(t):
        return []
    x = poly.intersection(t)
    out = []
    for gm in getattr(x, "geoms", [x]):
        if gm.geom_type != "Polygon" or gm.area < 1e-4:
            continue
        ring = np.asarray(gm.exterior.coords)[:-1]
        # fan from the first vertex (the clip of a triangle by a convex-ish region is convex in practice)
        if not Polygon(ring).exterior.is_ccw:
            ring = ring[::-1]
        for k in range(1, len(ring) - 1):
            out.append(np.array([ring[0], ring[k], ring[k + 1]]))
    return out


def _cover_heights(V2, grid, zc0, blend):
    """Ground heights of the cover: the plane of the conformed terrain, blended to the wall top behind a coping."""
    z = grid.plane(V2[:, 0], V2[:, 1], zc0)
    for fc, back, tp, nn in blend:
        # nearest coping station within 2.5 m behind the face
        from scipy.spatial import cKDTree
        tree = cKDTree(back)
        d, k = tree.query(V2, distance_upper_bound=3.5)
        hit = np.isfinite(d)
        if not hit.any():
            continue
        kk = k[hit]
        along = ((V2[hit] - back[kk]) * nn[kk]).sum(1)          # metres behind the coping back edge
        on = along > -0.6
        tgt = tp[kk] - 0.02
        near = np.clip(1.0 - along / 2.0, 0.0, 1.0) * on                       # meets the coping (up or down)
        fill = np.clip((COVER_M - WALL_T - 0.5 - along) / 1.0, 0.0, 1.0) * on   # the cut slope behind the wall filled
        zh = z[hit]
        z1 = zh + near * (tgt - zh)
        z[hit] = np.maximum(z1, zh + fill * np.maximum(tgt - zh, 0.0))
    return z


def _emit_cover(buf, grid, zc0, cover_cells, K, blend, adjust=None):
    if K is None or not cover_cells.any():
        return 0
    J, I = np.where(cover_cells)
    tris = []
    for j, i in zip(J, I):
        x, y = grid.x0 + i, grid.y1 - j
        a, b, d, e = (x, y), (x + 1, y), (x, y - 1), (x + 1, y - 1)
        for tri in ((a, d, e), (a, e, b)):
            tris += _clip_tri(np.array(tri, float), K)
    if not tris:
        return 0
    T2 = np.array(tris)
    flat = T2.reshape(-1, 2)
    uniq, inv = np.unique(np.round(flat, 4), axis=0, return_inverse=True)
    z = _cover_heights(uniq, grid, zc0, blend)
    if adjust is not None:
        z = adjust(uniq, z)
    V = np.column_stack([uniq, z])
    T = inv.reshape(-1, 3)
    # CCW from above
    a, b, c = V[T[:, 0], :2], V[T[:, 1], :2], V[T[:, 2], :2]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T = np.where((cr < 0)[:, None], T[:, [0, 2, 1]], T)
    # Own primitive (bridge layer: drawn in every LOD ring, like the grass fill of a bridge median), NOT merged into the
    # terrain primitives: the Unity importer rebuilds the near terrain from the grid nodes of the terrain primitive
    # (WorldMeshBake.TerrainBandData: highest vertex per node, triangles dropped), so merged cover vertices on grid
    # nodes lifted the lowered terrain back up - a one-cell cliff across both portals and pyramids in front of the
    # walls (r1-r3).
    buf.add("bridge", "verge_grass", V, uniq, T, src="tunnel:cover")
    return int(len(T))


def _emit_cover_collision(buf, grid, zc0, poly, blend):
    tris = _clip_grid(poly, 2.0, poly.bounds)
    if not len(tris):
        return
    flat = tris.reshape(-1, 2)
    uniq, inv = np.unique(np.round(flat, 3), axis=0, return_inverse=True)
    z = _cover_heights(uniq, grid, zc0, blend)
    V = np.column_stack([uniq, z])
    T = inv.reshape(-1, 3)
    a, b, c = V[T[:, 0], :2], V[T[:, 1], :2], V[T[:, 2], :2]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T = np.where((cr < 0)[:, None], T[:, [0, 2, 1]], T)
    buf.add("collision", "collision_grass", V, uniq, T, src="tunnel:cover:col")


GUARD_SUFFIX = (":structure", ":embankment", ":median", ":approach")    # keys of streetscape.furniture.guardrails runs
INSIDE_SIDE_MAT = "shoulder_gravel"    # WORKING_VALUE: nothing grows under the slab


def _dress_inside(w, groups):
    """Side strips and road barriers of the tunnel carriageways under the slab (r5).

    * the rural side profile (gravel shoulder + grass verge with a ditch) keeps its shape but its grass rows become
      gravel between the portals (r4: a grass verge ran through the 77 m under the slab);
    * rule runs of W-beam on a tunnel carriageway (streetscape.furniture.guardrails: "beside a structure" fired on the
      ring decks over the cut and left an 8 m stub with two turned-down terminals between the tunnel walls, r4) are
      dropped inside the structure together with their collision - the tunnel walls are the restraint there.
    Only parts of the tunnel chains inside F and below the soffit are touched."""
    import dataclasses
    rep = {"side_grass_to_gravel_tris": 0, "guardrail_tris": 0, "guardrail_collision_tris": 0}
    new = []
    for g in groups:
        Fb = g["F"].buffer(0.5)
        run_ids = tuple(r["c"].id + ":" for r in g["runs"])
        for p in w.buf.parts:
            if not len(p.T) or not p.src.startswith(run_ids):
                continue
            grass = p.layer == "road" and p.mat == "verge_grass" and not p.src.endswith(":vg")
            rail = p.layer in ("bridge", "furniture", "collision") and p.src.endswith(GUARD_SUFFIX)
            if not (grass or rail):
                continue
            cen = p.V[p.T].mean(1)
            m = shapely.contains_xy(Fb, cen[:, 0], cen[:, 1])
            for k in np.where(m)[0]:
                m[k] = cen[k, 2] < g["zroad"](tuple(cen[k, :2])) + g["clear"] - 0.1
            if not m.any():
                continue
            if grass:
                new.append(dataclasses.replace(p, mat=INSIDE_SIDE_MAT, T=p.T[m], src=p.src + ":tunnel"))
                rep["side_grass_to_gravel_tris"] += int(m.sum())
            else:
                rep["guardrail_collision_tris" if p.layer == "collision" else "guardrail_tris"] += int(m.sum())
            p.T = p.T[~m]
    w.buf.parts[:] = [p for p in w.buf.parts if len(p.T)] + new
    return rep


TRIM_SUFFIX = (":soffit", ":fascia", ":parapet", ":abutment", ":pier", ":screen")
CULL_PROTO = ("lamp_", "tree_", "board_", "signal_", "sign_post", "plate_")


def _cull(w, groups, instances, lift=None, under_deck=None):
    """Pieces of the ring decks and instances that the slab replaces or that would pierce it."""
    rep = {"deck_tris": 0, "instances": {}}
    Fs = [g["F"] for g in groups]
    U = shapely.union_all(Fs).buffer(0.5)
    # surfaces that the streetscape laid on the cut-level ground inside the structure (paved yards, cycle paths,
    # plot ground, verges of other roads and their collision; r1: yard_asphalt / cycle_red 1.6-3.9 m over the tunnel
    # road): their triangles below the soffit go (lifting only the inside vertices made curtains at the portals, r2)
    rep["dropped_surface_tris"] = 0
    run_ids = tuple(r["c"].id for g in groups for r in g["runs"])
    Fl = [(g["F"].buffer(1.0), g) for g in groups]
    if lift is not None:
        for p in w.buf.parts:
            if (p.layer not in ("paved", "plot_ground", "collision", "road") or p.src.startswith(run_ids)
                    or p.src.startswith("tunnel") or not len(p.V)):
                continue
            for Fb, g in Fl:
                m = shapely.contains_xy(Fb, p.V[:, 0], p.V[:, 1])
                if not m.any():
                    continue
                idx = np.where(m)[0]
                zs = np.array([g["zroad"](tuple(p.V[k, :2])) for k in idx]) + g["clear"]
                bad_v = np.zeros(len(p.V), bool)
                bad_v[idx[p.V[idx, 2] < zs - 0.1]] = True
                bt = bad_v[p.T].any(axis=1)
                if bt.any():
                    rep["dropped_surface_tris"] += int(bt.sum())
                    p.T = p.T[~bt]
    keep_parts = []
    for p in w.buf.parts:
        if p.layer == "bridge" and not p.src.startswith("tunnel") and p.src.endswith(TRIM_SUFFIX):
            cen = p.V[p.T].mean(1)
            inside = shapely.contains_xy(U, cen[:, 0], cen[:, 1])
            if inside.any():
                rep["deck_tris"] += int(inside.sum())
                if inside.all():
                    continue
                p.T = p.T[~inside]
        if len(p.T):
            keep_parts.append(p)
    w.buf.parts[:] = keep_parts
    keep = []
    rep["lifted"] = {}
    for it in instances:
        hit = False
        for g in groups:
            q = (float(it["e"]), float(it["n"]))
            if not g["F"].buffer(0.5).contains(shapely.Point(q)):
                continue
            soffit = g["zroad"](q) + g["clear"]
            if it.get("z", -1e9) >= soffit - 0.2:
                break
            # inside the structure below the soffit. Placed for a tunnel carriageway (src names its chain) or standing on
            # one / its shoulder: it belongs to the tunnel road (tall ones would pierce the slab: dropped). Else
            # (island, verges of the junction) it was placed on the cut-level ground of the conform and is lifted by
            # the ground difference (plates / heads keep their offset over their post); under a ring deck: dropped.
            run_ids = tuple(r["c"].id for r in g["runs"])
            in_road = any(rid in str(it.get("src", "")) for rid in run_ids)
            for r in g["runs"]:
                s, lat = r["c"].line.project(q)
                side = "L" if lat > 0 else "R"
                u, _ = _side_info(r["c"], side, s)
                if r["sa"] - 1.0 <= s <= r["sb"] + 1.0 and abs(lat) <= float(r["c"].hw_at(s)) + u + WALL_GAP_M:
                    in_road = True
            k = it["p"].split("_")[0]
            if in_road:
                if it["p"].startswith(CULL_PROTO):
                    hit = True
                    rep["instances"][k] = rep["instances"].get(k, 0) + 1
            elif under_deck is not None and under_deck(*q):
                hit = True
                rep.setdefault("under_deck", {})[k] = rep.setdefault("under_deck", {}).get(k, 0) + 1
            elif lift is not None:
                it["z"] = round(float(it["z"]) + lift(*q), 3)
                rep["lifted"][k] = rep["lifted"].get(k, 0) + 1
            break
        if not hit:
            keep.append(it)
    instances[:] = keep
    return rep


def graph_of(region_dir) -> dict:
    return json.loads((region_dir / "roads.graph.json").read_text(encoding="utf-8"))
