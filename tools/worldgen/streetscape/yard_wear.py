"""Authored wear of a depot yard (block `wear` of an override `kind: depot_yard`, ADR 0071 r11).

Review 2026-11-10 (A2): the Kwadrat Park yard was one clean paver texture to the horizon. The engine materials already
vary tone, damp hollows and joint dirt (Kamion/World PBR _GRIME, macro map); what a rule cannot know is where the trucks
of THIS yard drive, stand and drip. The override says it in the frame of the hero dock row, so it survives every
regeneration and never depends on hand-edited meshes:

  frame           (u, o) metres: u along the dock wall from its first corner (the wall of the dock row whose building id
                  contains `wear.building`), o out of the wall into the yard
  tracks_uo       [{pts: [[u, o], ...], passes, strength}] driving lines: two wheel paths of rubber / fines per pass
                  (`decal_tyre` bands, the profile, end fades and break-up are in the material)
  patches_uo      [{at: [u, o], size: [L, W], rot_deg, tone: light | dark}] relaid paving (utility repairs): the same
                  blocks in another tone (`decal_yard_patch_*`: the yard's own paving set, so the bond runs through)
  trenches_uo     [{a: [u, o], b: [u, o], w, tone}] relaid cable trenches (a lamp column to the hall)
  oil_per_dock    [min, max] oil / grease stains per dock where tractors stand coupled (fifth wheel, engine, gearbox)
                  and under the trailer axles (`decal_oil`, 4 stain shapes)
  grime_lines_uo  [{pts: [[u, o], ...], w, strength}] dark soil / damp lines seen on the orthophoto (`decal_tyre`)
  grime_edges     true: soil washed against kerbs, edgings and wall feet: soft bands along every edge of the paved
                  yard inside the zone that is not a flush road edge (`decal_tyre`)
  zone_epsg2180   polygon of the yard (default: the first `no_parking_epsg2180` ring)

Everything is hashed from the override id (no RNG state): two builds give the same bytes. Counts go to the streetscape
QA (`furniture.yard_wear`). Lifts: patch 2 mm < grime 3 mm < oil 3.5 mm < paint 6 mm < tyre 8 mm (roads.decals).
"""

from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon

from roads import decals as DC
from roads import standards as S

KIND = "depot_yard"
LIFT_PATCH = 0.002
LIFT_GRIME = 0.003
LIFT_TYRE = 0.008
TRACK_GAUGE = 2.04          # m between the wheel-path centres of a truck / semitrailer (WORKING_VALUE)
# r12 (review 2026-11-11 s9: "ślady opon jak plamy cienia"): a wheel path is the print of a twin tyre - two treads of
# TWIN_TREAD_M with TWIN_GAP_M between them (315/80 R22.5 twins: 0.60 m over both; WORKING_VALUE), drawn as two narrow
# bands with a hard edge (band v inside 0.22..0.78: the material's soft profile starts at 0.44 of its ramp).
TWIN_TREAD_M = 0.26
TWIN_GAP_M = 0.08
TWIN_V = (0.22, 0.78)
# Soil bands use the tyre-scrub band material (dark grey film, same shader path): one draw less per chunk than a
# material of their own, and at the opacities used here (0.3-0.6) a soil film and a rubber film read the same.
GRIME_MAT = "decal_tyre"
PATCH_TONES = {"light": "decal_yard_patch_light", "dark": "decal_yard_patch_dark"}


def hf(*key):
    return DC.hf(*key)


def _smooth(P, it=3):
    """Chaikin corner cutting (keeps the end points)."""
    P = np.asarray(P, float)
    for _ in range(it):
        Q = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            Q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        Q.append(P[-1])
        P = np.array(Q)
    return P


def _resample(P, step):
    ln = LineString(P)
    n = max(2, int(math.ceil(ln.length / step)) + 1)
    return np.array([ln.interpolate(ln.length * k / (n - 1)).coords[0] for k in range(n)])


def band(buf, mat, C, w, zsurf, lift, strength, src, v=(0.0, 1.0)):
    """Soft band decal along the polyline C (n, 2) of width w (scalar or per point): UV0 = (metres along, 0..1 across),
    UV1 = (length, strength), faces up. v = range of the across coordinate on the two edges: (0, 1) = soft edges,
    a narrower range cuts the soft ramp of the material (hard edge). Returns the number of triangles."""
    C = np.asarray(C, float)
    if len(C) < 2:
        return 0
    t = np.gradient(C, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nn = np.column_stack([-t[:, 1], t[:, 0]])
    w = np.broadcast_to(np.asarray(w, float), (len(C),))[:, None]
    A, B = C - nn * w / 2, C + nn * w / 2
    V2 = np.vstack([A, B])
    Z = zsurf(V2[:, 0], V2[:, 1]) + lift
    m = len(C)
    ss = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
    # A = right edge, B = left edge of the travel direction: (A_i, A_i+1, B_i+1) is CCW seen from above
    T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
    uv = np.column_stack([np.tile(ss, 2), np.repeat([float(v[0]), float(v[1])], m)])
    uv1 = np.column_stack([np.full(2 * m, ss[-1]), np.full(2 * m, strength)])
    buf.add("markings", mat, np.column_stack([V2, Z]), uv, T, src=src, UV1=uv1)
    return len(T)


def _runs(C, ok, min_pts=4):
    """Consecutive runs of C where ok is True."""
    out, cur = [], []
    for p, k in zip(C, ok):
        if k:
            cur.append(p)
        else:
            if len(cur) >= min_pts:
                out.append(np.array(cur))
            cur = []
    if len(cur) >= min_pts:
        out.append(np.array(cur))
    return out


def _straights(P, max_turn_deg=25.0):
    """Split a polyline at its corners: a band offset to one side would fold over itself round a corner."""
    out, cur = [], [P[0]]
    for k in range(1, len(P)):
        cur.append(P[k])
        if k < len(P) - 1:
            a, b = P[k] - P[k - 1], P[k + 1] - P[k]
            den = float(np.hypot(*a) * np.hypot(*b))
            if den > 1e-9 and math.degrees(math.acos(max(-1.0, min(1.0, float(a @ b) / den)))) > max_turn_deg:
                out.append(cur)
                cur = [P[k]]
    out.append(cur)
    return [LineString(c) for c in out if len(c) >= 2]


def _quad_grid(buf, mat, c, ax, L, W, zsurf, lift, src, inside=None):
    """Rectangle centred at c, long axis ax (unit), L x W, subdivided every ~2 m to follow the yard surface. Planar
    material (no UV needed; UV0 = local metres). Returns False when a corner leaves `inside`."""
    ay = np.array([-ax[1], ax[0]])
    nu, nv = max(1, int(math.ceil(L / 2.0))), max(1, int(math.ceil(W / 2.0)))
    U, Vv = np.meshgrid(np.linspace(-L / 2, L / 2, nu + 1), np.linspace(-W / 2, W / 2, nv + 1))
    P = c[None, :] + U.ravel()[:, None] * ax[None, :] + Vv.ravel()[:, None] * ay[None, :]
    if inside is not None and not inside.contains(Polygon([P[0], P[nu], P[-1], P[-nu - 1]])):
        return False
    T = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            T += [(a, a + 1, a + nu + 2), (a, a + nu + 2, a + nu + 1)]
    Z = zsurf(P[:, 0], P[:, 1]) + lift
    buf.add("markings", mat, np.column_stack([P, Z]), np.column_stack([U.ravel() + L / 2, Vv.ravel() + W / 2]), np.array(T), src=src)
    return True


def normalize_asphalt_patch_uvs(buf, style=None):
    """ADR0118: normalise only decorative asphalt repairs, before chunk clipping.

    Positions, indices, normals, paint and yard wear are untouched. Complete-patch UVs survive clipping so a chunk
    border cannot become a false repair seam. The opt-in material block also enables the matching shader branch.
    """
    if style is None:
        from .materials import M
        style = M.get("decal_patch", {}).get("asphalt_patch_seam", {})
    counts = {"normalised": 0, "invalid_uv": 0}
    if not style or float(style.get("width_m", 0)) <= 0:
        return counts
    for part in buf.parts:
        if part.layer != "markings" or part.mat != "decal_patch":
            continue
        uv = part.UV
        if uv.ndim != 2 or uv.shape[1] != 2 or not len(uv) or not np.isfinite(uv).all():
            counts["invalid_uv"] += 1
            continue
        lo, hi = uv.min(axis=0), uv.max(axis=0)
        span = hi - lo
        if np.any(span < 1e-6):
            counts["invalid_uv"] += 1
            continue
        part.UV = (uv - lo) / span
        counts["normalised"] += 1
    return counts


def mark_fresh_road_paint(buf, enabled=None):
    """Encode actual fresh-road support in paint UV1.y (+4), preserving its fractional age and geometry.

    Samples must agree at every vertex, edge midpoint and triangle centroid. Heights disambiguate an overpass;
    coplanar old/fresh overlaps remain conservative old/unknown. No field is extrapolated beyond a road triangle.
    """
    if enabled is None:
        from .materials import M
        enabled = M.get("marking_white", {}).get("paint", {}).get("fresh_surface_from_road", False)
    counts = {"fresh_parts": 0, "fresh_vertices": 0, "old_or_unknown_parts": 0}
    if not enabled:
        return counts
    from .furniture import SurfaceTop
    fresh = SurfaceTop([p for p in buf.parts if p.mat == "road_asphalt_new"], layers=("road",))
    old = SurfaceTop([p for p in buf.parts if p.mat == "road_asphalt"], layers=("road",))
    known = {}

    def supported(point):
        key = tuple(float(x) for x in point)
        if key not in known:
            e, n, z = key
            f = fresh.top(e, n, below=z + 0.035)
            o = old.top(e, n, below=z + 0.035)
            known[key] = math.isfinite(f) and abs(f - z) <= 0.035 and not (
                math.isfinite(o) and abs(o - z) <= 0.035)
        return known[key]

    for part in buf.parts:
        if part.layer != "markings" or part.mat != "marking_white" or part.UV1 is None:
            continue
        ex = part.UV1[:, 1]
        encoded = ((ex >= 4.0) & (ex < 5.0)) | ((ex >= 6.0) & (ex < 7.0))
        base = np.where(encoded, ex - 4.0, ex)
        if not np.all(((base >= 0.0) & (base < 1.0)) | ((base >= 2.0) & (base < 3.0))):
            counts["old_or_unknown_parts"] += 1
            continue # e.g. (-1,5) is a no-data sentinel, not an encoded fresh mark
        valid = all(supported(p) for p in part.V)
        if valid:
            for a, b, c in part.V[part.T]:
                if not all(supported(p) for p in ((a+b)/2, (b+c)/2, (c+a)/2, (a+b+c)/3)):
                    valid = False
                    break
        target = base + 4.0 if valid else base
        if not np.array_equal(ex, target):
            part.UV1 = part.UV1.copy()
            part.UV1[:, 1] = target
        if valid:
            counts["fresh_parts"] += 1
            counts["fresh_vertices"] += len(part.V)
        else:
            counts["old_or_unknown_parts"] += 1
    return counts


def mark_traffic_oil_strength(buf, scale=None):
    """Oil UV1.x was unused. Positive values scale only the traffic-stop stains, not yard/gate/bus oil."""
    if scale is None:
        from .materials import M
        scale = M.get("decal_oil", {}).get("traffic_opacity_scale", 0.0)
    count = 0
    if float(scale) <= 0:
        return count
    for part in buf.parts:
        if part.mat != "decal_oil" or not part.src.startswith("oil:") or part.UV1 is None:
            continue
        part.UV1 = part.UV1.copy()
        part.UV1[:, 0] = float(scale)
        count += 1
    return count


def apply(buf, overrides, origin, docks, paved, roads_poly, zsurf, report):
    rep = {"applied": [], "stale": []}
    o_ = np.asarray(origin, float)
    for o in overrides:
        if o.get("kind") != KIND or not o.get("wear"):
            continue
        wr = o["wear"]
        oid = o["id"]
        row = next((d for d in docks if str(wr.get("building", "")) and str(wr["building"]) in d["id"]), None)
        if row is None:
            rep["stale"].append(f"{oid}:wear:no_dock_row")
            continue
        p, q = (np.asarray(x, float) for x in row["edge"])
        du = (q - p) / np.linalg.norm(q - p)
        nout = np.array([du[1], -du[0]])

        def xy(uo):
            uo = np.asarray(uo, float)
            if uo.ndim == 1:
                return p + uo[0] * du + uo[1] * nout
            return p[None, :] + uo[:, 0:1] * du[None, :] + uo[:, 1:2] * nout[None, :]

        ring = wr.get("zone_epsg2180") or (o.get("no_parking_epsg2180") or [None])[0]
        zone = Polygon(np.asarray(ring, float) - o_) if ring is not None else None
        yard_items = [it for it in paved if it["mat"].startswith("yard_") and (zone is None or it["poly"].intersects(zone))]
        if not yard_items:
            rep["stale"].append(f"{oid}:wear:no_paved_area")
            continue
        yard = shapely.union_all([it["poly"] for it in yard_items]).buffer(0.02, join_style="mitre")
        drivable = shapely.union_all([yard, roads_poly]).buffer(0.2)
        blocks = shapely.union_all([it["poly"] for it in yard_items if it["mat"] == "yard_behaton"]).buffer(-0.3)
        shapely.prepare(drivable)
        cnt = {"id": oid, "track_bands": 0, "patches": 0, "trenches": 0, "oil": 0, "grime_bands": 0, "tris": 0}

        # ---- driving lines
        for ti, tr in enumerate(wr.get("tracks_uo", [])):
            C0 = _resample(_smooth(xy(np.asarray(tr["pts"], float))), 3.0)     # the yard is level within ~0.1 m
            t = np.gradient(C0, axis=0)
            t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
            nn = np.column_stack([-t[:, 1], t[:, 0]])
            for k in range(int(tr.get("passes", 2))):
                key = (oid, "track", ti, k)
                drift = (hf(*key, "j") - 0.5) * 1.1 + 0.5 * np.sin(np.linspace(0, math.pi * (1 + 2 * hf(*key, "f")), len(C0)) + 6.28 * hf(*key, "ph"))
                # 0.35-0.85 of the dock scrub opacity: a driving line is a faint darkening, not a skid mark
                strength = float(tr.get("strength", 1.0)) * (0.35 + 0.5 * hf(*key, "s"))
                for wx in (-1.0, 1.0):
                    for tw in (-1.0, 1.0):                           # the two treads of the twin tyre
                        C = C0 + nn * (wx * TRACK_GAUGE / 2 + tw * (TWIN_TREAD_M + TWIN_GAP_M) / 2 + drift)[:, None]
                        ok = shapely.contains_xy(drivable, C[:, 0], C[:, 1])
                        for ri, run in enumerate(_runs(C, ok)):
                            # the hard edge shows 1 / 0.56 of the band's peak: keep the peak opacity of r11
                            cnt["tris"] += band(buf, "decal_tyre", run, TWIN_TREAD_M, zsurf, LIFT_TYRE,
                                                min(strength * (0.9 + 0.2 * hf(*key, wx, tw, "t")), 1.5),
                                                f"wear:{oid}:track{ti}:{k}:{int(wx)}:{int(tw)}:{ri}", v=TWIN_V)
                            cnt["track_bands"] += 1

        # ---- dark soil / damp lines read off the orthophoto
        for gi, gl in enumerate(wr.get("grime_lines_uo", [])):
            C = _resample(_smooth(xy(np.asarray(gl["pts"], float))), 3.0)
            ok = shapely.contains_xy(drivable, C[:, 0], C[:, 1])
            for ri, run in enumerate(_runs(C, ok)):
                wv = float(gl.get("w", 1.2)) * (0.75 + 0.5 * np.array([hf(oid, "gl", gi, ri, k // 2) for k in range(len(run))]))
                cnt["tris"] += band(buf, GRIME_MAT, run, wv, zsurf, LIFT_GRIME, float(gl.get("strength", 1.0)),
                                    f"wear:{oid}:grime_line{gi}:{ri}")
                cnt["grime_bands"] += 1

        # ---- relaid paving
        for pi, pt in enumerate(wr.get("patches_uo", [])):
            c = xy(np.asarray(pt["at"], float))
            a = math.radians(float(pt.get("rot_deg", 0.0)))
            ax = du * math.cos(a) + nout * math.sin(a)
            if _quad_grid(buf, PATCH_TONES[pt.get("tone", "light")], c, ax, float(pt["size"][0]), float(pt["size"][1]), zsurf,
                          LIFT_PATCH, f"wear:{oid}:patch{pi}", inside=blocks):
                cnt["patches"] += 1
            else:
                rep["stale"].append(f"{oid}:wear:patch{pi}:off_the_block_paving")
        for ti, tr in enumerate(wr.get("trenches_uo", [])):
            a, b = xy(np.asarray(tr["a"], float)), xy(np.asarray(tr["b"], float))
            L = float(np.hypot(*(b - a)))
            if _quad_grid(buf, PATCH_TONES[tr.get("tone", "light")], (a + b) / 2, (b - a) / L, L, float(tr.get("w", 0.9)), zsurf,
                          LIFT_PATCH, f"wear:{oid}:trench{ti}", inside=blocks):
                cnt["trenches"] += 1
            else:
                rep["stale"].append(f"{oid}:wear:trench{ti}:off_the_block_paving")

        # ---- oil and grease where vehicles stand at the docks
        lo, hi = wr.get("oil_per_dock", [0, 0])

        def z_oil(V2):
            return zsurf(V2[:, 0], V2[:, 1]) + DC.LIFT_OIL

        for dock in row["docks"]:
            key = (oid, "oil", dock["num"])
            n = int(lo) + int(hf(*key, "n") * (int(hi) - int(lo) + 1))
            for k in range(n):
                r_ = hf(*key, k, "where")
                # distances from the wall: trailer axle hubs 3.5-6.1 m, fifth wheel ~12.9 m, tractor engine / gearbox
                # 14.5-17.5 m (13.6 m trailer on the bumpers; WORKING_VALUE)
                if r_ < 0.25:
                    oo, lat, rad = 3.5 + hf(*key, k, "o") * 2.6, (1.0 if hf(*key, k, "sx") < 0.5 else -1.0) * (0.75 + 0.3 * hf(*key, k, "l")), 0.14 + 0.2 * hf(*key, k, "r")
                elif r_ < 0.45:
                    oo, lat, rad = 12.6 + hf(*key, k, "o") * 0.8, (hf(*key, k, "l") - 0.5) * 0.5, 0.18 + 0.22 * hf(*key, k, "r")
                else:
                    oo, lat, rad = 14.5 + hf(*key, k, "o") * 3.0, (hf(*key, k, "l") - 0.5) * 1.1, 0.2 + 0.45 * hf(*key, k, "r") ** 2
                P0 = xy(np.array([dock["u"] + lat, 0.45 + oo]))
                if not yard.contains(Point(*P0).buffer(rad * 1.9)):
                    continue
                DC.stain(buf, P0, z_oil, rad, (*key, k), f"wear:{oid}:oil:{dock['num']}:{k}")
                cnt["oil"] += 1

        # ---- soil washed against the edges of the yard (kerbs, edgings, wall feet)
        if wr.get("grime_edges"):
            # the zone (no-parking ring) stops short of the dock wall: the wall foot and the apron belong to the yard
            lim = shapely.union_all([zone, LineString([p, q])]).convex_hull.buffer(3.0) if zone is not None else yard
            flush = roads_poly.buffer(0.8)
            for gi, g in enumerate(getattr(yard, "geoms", [yard])):
                for ri, rg in enumerate([g.exterior] + list(g.interiors)):
                    ln = LineString(rg.coords).intersection(lim).difference(flush)
                    pieces = []
                    for piece in getattr(ln, "geoms", [ln]):
                        if piece.geom_type == "LineString":
                            pieces += _straights(np.asarray(piece.coords))
                    for li, piece in enumerate(pieces):
                        if piece.length < 5.0:
                            continue
                        s0 = 0.0
                        k = 0
                        while s0 < piece.length - 4.0:
                            key = (oid, "grime", gi, ri, li, k)
                            seg = min(piece.length - s0, 7.0 + 9.0 * hf(*key, "len"))
                            k += 1
                            if hf(*key, "skip") < 0.12 or seg < 5.0:
                                s0 += seg
                                continue
                            w = 0.7 + 1.0 * hf(*key, "w") ** 2
                            C = np.array([piece.interpolate(s).coords[0] for s in np.linspace(s0, s0 + seg, max(5, int(seg / 2.5) + 1))])
                            t = np.gradient(C, axis=0)
                            t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
                            nn = np.column_stack([-t[:, 1], t[:, 0]])
                            mid = C[len(C) // 2]
                            sgn = 1.0 if yard.contains(Point(*(mid + nn[len(C) // 2] * 0.4))) else -1.0
                            C = C + nn * sgn * (w / 2 + 0.03)
                            if sgn < 0:
                                C = C[::-1]
                            ok = shapely.contains_xy(yard, C[:, 0], C[:, 1])
                            for run in _runs(C, ok, 5):
                                cnt["tris"] += band(buf, GRIME_MAT, run, w, zsurf, LIFT_GRIME, 0.6 + 0.8 * hf(*key, "s"),
                                                    f"wear:{oid}:grime:{gi}:{ri}:{li}:{k}")
                                cnt["grime_bands"] += 1
                            s0 += seg
        rep["applied"].append(cnt)
    patch_uv = normalize_asphalt_patch_uvs(buf)
    if patch_uv["normalised"] or patch_uv["invalid_uv"]:
        rep["asphalt_patch_uv"] = patch_uv
    paint_surface = mark_fresh_road_paint(buf)
    if paint_surface["fresh_parts"] or paint_surface["old_or_unknown_parts"]:
        rep["paint_surface"] = paint_surface
    traffic_oil = mark_traffic_oil_strength(buf)
    if traffic_oil:
        rep["traffic_oil_parts"] = traffic_oil
    report["yard_wear"] = rep
    return rep
