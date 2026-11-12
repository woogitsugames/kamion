"""Road furniture: placement rules (point instances) and linear features (meshed into the chunk GLBs).

Point instances (prototypes in streetscape.props):
  lamps        along GP/G/Z/L/D chains, outer side of one-way carriageways / right side of two-way roads,
               spacing + height by class (standards.LAMP, WORKING_VALUE); OSM highway=street_lamp nodes kept.
  signs        A-7 + C-12 on every roundabout entry; B-20 at OSM highway=stop; A-7 at OSM give_way and on minor
               (Z/L) arms of unsignalised junctions with a higher-class road, D-1 on the major arms there; B-33 at
               the start of every chain with maxspeed != 50 km/h (repeated after each junction, the limit ends
               there); D-6 both sides of unsignalised P-10 crossings; D-15 at bus stops; schematic E-2 boards at
               the start of *_link chains tagged `destination` (green with route shields for numbered roads,
               white for local destinations). Heights: [ZNAKI-Z1] Table 1.11 (standards.SIGN_H_*).
  signals      S-1 heads on every inbound arm of signalised junctions: pole at the right kerb at the stop line;
               approaches with >= 3 lanes also get a cantilever mast over the lanes.
  other        bus shelters (OSM highway=bus_stop, else BDOT10k OT_OIKM_P), lift gates / sliding gates (OSM),
               bollards, benches, bins, power poles (BDOT10k OT_BUWT_P słup energetyczny, OSM power=pole),
               lattice pylons (OSM power=tower).
Linear meshes (layer 'furniture' + 'collision'):
  fences       OSM barrier=fence/yes -> 3D welded panel fence on a concrete plinth; barrier=wall -> prefabricated
               concrete panel fence; cut where they cross a carriageway.
  guard rails  steel W-beam (U-11a family) on bridge caps, on rural medians, and on rural sides where the
               ground falls > GUARDRAIL_EMBANKMENT_H within 4 m of the shoulder.
  noise walls  BDOT10k OT_OIKM_L ekran akustyczny + OSM wall=noise_barrier (ADR 0069): dark absorbing cassettes on a
               concrete plinth, or (authored zones from Mapillary photos) a cassette band with clear panels above.
  walls        BDOT10k OT_BUUO_L ściana oporowa / OSM retaining_wall + pedestrian railing (U-12a) on top.
  wires        BDOT10k OT_SULN_L power lines between the poles (catenary sag).
"""

from __future__ import annotations

import hashlib
import json
import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point

from roads import standards as S
from roads.network import MEDIAN_RURAL, RURAL, URBAN, side_params, side_extent
from roads.geom import dp_keep
from roads.meshing import bridge_cap_w, bridge_style

from . import facade_atlas as FA

# ADR 0102: contact follows the pole axis rather than the lowest point around the footing. Keep collision/terrain
# level selection: overlapping elevated ribbons and small visual holes must not move poles between road levels.
SEATED_POLES = ("lamp_", "signal_mast", "signal_pole", "sign_post", "power_pole", "bollard")
SEAT_R = 0.35                 # m, footing radius probed (WORKING_VALUE)
SEAT_TOL = 0.30              # m, an explicit z this far below the local ground is raised to it (gate 3 tolerance)

RANK = {"A": 0, "S": 1, "GP": 2, "G": 3, "Z": 4, "L": 5, "D": 6}


def _h(key):
    return int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)


def yaw_of(f):
    """Yaw (rad) that turns local +y onto direction f (E, N)."""
    return math.atan2(f[1], f[0]) - math.pi / 2


class SurfaceTop:
    """Exact top of the generated ground meshes (road + paved layers: carriageway, kerb tops, island tops, aprons,
    footways, verges, yards) at plan points. The 1 m raster `zsurf` blends an island top with the carriageway and
    the terrain beside it, which left lamps 0.35 m in the air and C-9 posts on splitter islands buried 0.86 m
    (gate 3 audit). Upward faces only (|n.z| >= 0.5); bridge decks are a separate layer and are not sampled."""
    CELL = 4.0

    def __init__(self, parts, collision=False, layers=("road", "paved")):
        tris = []
        for p in parts:
            if collision:                 # the smooth collision surfaces (4 m stations) the player and the audit stand on
                if p.layer != "collision" or p.mat not in ("collision_asphalt", "collision_curb", "collision_paving",
                                                             "collision_grass"):
                    continue
            elif p.layer not in layers or p.mat.startswith("collision") or p.mat.startswith("marking"):
                continue
            A = p.V[p.T]
            nrm = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0])
            ln = np.linalg.norm(nrm, axis=1)
            ok = (ln > 1e-9) & (np.abs(nrm[:, 2]) >= 0.5 * np.maximum(ln, 1e-12))
            if ok.any():
                tris.append(A[ok])
        self.A = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
        self.grid = {}
        if not len(self.A):
            return
        lo = np.floor(self.A[:, :, :2].min(1) / self.CELL).astype(int)
        hi = np.floor(self.A[:, :, :2].max(1) / self.CELL).astype(int)
        for t, (a, b) in enumerate(zip(lo, hi)):
            for i in range(a[0], b[0] + 1):
                for j in range(a[1], b[1] + 1):
                    self.grid.setdefault((i, j), []).append(t)

    def top(self, e, n, below=None):
        """highest surface at (e, n) (optionally only surfaces <= below), NaN where no ground mesh covers it"""
        ids = self.grid.get((int(math.floor(e / self.CELL)), int(math.floor(n / self.CELL))))
        if not ids:
            return float("nan")
        A = self.A[ids]
        a, b, c = A[:, 0], A[:, 1], A[:, 2]
        d = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
        ok = np.abs(d) > 1e-12
        d = np.where(ok, d, 1.0)
        l1 = ((b[:, 1] - c[:, 1]) * (e - c[:, 0]) + (c[:, 0] - b[:, 0]) * (n - c[:, 1])) / d
        l2 = ((c[:, 1] - a[:, 1]) * (e - c[:, 0]) + (a[:, 0] - c[:, 0]) * (n - c[:, 1])) / d
        l3 = 1.0 - l1 - l2
        eps = -1e-6
        inside = ok & (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
        if not inside.any():
            return float("nan")
        z = l1 * a[:, 2] + l2 * b[:, 2] + l3 * c[:, 2]
        z = z[inside]
        if below is not None:
            z = z[z <= below]
            if not len(z):
                return float("nan")
        return float(z.max())


# footing radius per pole family (m): the part of the footprint that must stand on the surface
FOOT_R = {"lamp_arc_": 0.28, "lamp_old_concrete_": 0.15, "lamp_old_steel_": 0.20, "lamp_": 0.25,
          "signal_mast": 0.30, "signal_pole": 0.10, "sign_post": 0.04, "power_pole": 0.15, "bollard": 0.06}


class Placer:
    def __init__(self, zsurf, zground=None, surf=None, col=None):
        self.col = col                  # SurfaceTop of the collision surfaces (coarser: may lie under the visual top)
        self.zground = zground          # conformed terrain (= the collision under verges and footway edges)
        self.surf = surf                # SurfaceTop of the generated ground meshes (exact kerb / island tops)
        self.items = []
        self.zsurf = zsurf
        self.reseated = 0
        self.seat_log = []
        self.support_moves = []
        self.pts = {}

    def seat(self, proto, p):
        """Visible axis contact and surrounding terrain relief (not a corrected/zeroed QA metric).

        Foundations extend below their axis contact in the prototypes. Sampling the minimum lowered the entire
        lamp into the high bank; sampling the maximum raised it above the ground at its axis. A concrete footing
        may be partly exposed on the downhill face, as in a real installation. Dimensions are WORKING_VALUE.
        """
        r = next((v for k, v in FOOT_R.items() if proto.startswith(k)), SEAT_R)
        e = np.array([p[0], p[0] + r, p[0] - r, p[0], p[0]])
        n = np.array([p[1], p[1], p[1], p[1] + r, p[1] - r])
        zt = self.zground(e, n) if self.zground is not None else self.zsurf(e, n)
        z = []
        for k in range(5):
            m = self.surf.top(float(e[k]), float(n[k])) if self.surf is not None else float("nan")
            # Preserve the level selection of ADR 0076: a visual road/verge may overlap an underpass, or have a
            # small hole where the collision still covers it. Contact uses the centre, but cannot ignore that level.
            if self.col is not None:
                c = self.col.top(float(e[k]), float(n[k]), below=(m + 0.05) if math.isfinite(m) else None)
                if math.isfinite(c) and (not math.isfinite(m) or c < m):
                    m = c
                elif not math.isfinite(c) and math.isfinite(m):
                    m = min(m, float(zt[k]))
            z.append(m if math.isfinite(m) else float(zt[k]))
        return float(z[0]), float(max(z) - min(z))

    def near(self, group, p, r):
        for q in self.pts.get(group, []):
            if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < r * r:
                return True
        return False

    def lamp_support(self, proto, p):
        """Move a lamp at most 1.05 m off a sharp edge, never shorten it by burying its shaft.

        Deterministic local search; carriageway and deck keep-outs still run after placement. Collision is only a
        suitability check, not the visible seating height. Maximum shift/relief are WORKING_VALUE (ADR 0102).
        """
        p = np.asarray(p, float)

        def score(q):
            z, relief = self.seat(proto, q)
            c = self.col.top(float(q[0]), float(q[1]), below=z + 0.05) if self.col is not None else z
            mismatch = abs(z - c) if math.isfinite(c) else 0.0
            return max(relief, mismatch)

        before = score(p)
        if before <= 0.15:
            return p
        best, best_score = p, before
        for radius in (0.35, 0.70, 1.05):
            for a in np.arange(16) * math.pi / 8:
                q = p + radius * np.array([math.cos(a), math.sin(a)])
                s = score(q)
                if s < best_score - 1e-6:
                    best, best_score = q, s
            if best_score <= 0.15:
                break
        if not np.array_equal(best, p):
            self.support_moves.append({"p": proto, "from": p.tolist(), "to": best.tolist(),
                                       "before_m": round(before, 3), "after_m": round(best_score, 3)})
        return best

    def ground_min(self, p, r=None, on_verge=True):
        """lowest surface under a pole footing: centre + 4 points at r (the bilinear surface at a kerb / footway edge
        mixes the footway top with the terrain beside it, which left poles 0.2-0.44 m in the air, gate 3 audit)"""
        r = SEAT_R if r is None else r
        e = np.array([p[0], p[0] + r, p[0] - r, p[0], p[0]])
        n = np.array([p[1], p[1], p[1], p[1] + r, p[1] - r])
        z = np.min(self.zsurf(e, n))
        if self.zground is not None and on_verge:   # verge grass ribbons sit above the terrain collider
            z = min(z, np.min(self.zground(e, n)))
        return float(z)

    def add(self, proto, p, yaw, z=None, sz=1.0, src="", group=None):
        if proto.startswith("lamp_") and z is None and self.surf is not None:
            p = self.lamp_support(proto, p)
        if proto.startswith(SEATED_POLES):
            if self.surf is not None:
                zg, step = self.seat(proto, p)
                if step > 0.05:
                    self.seat_log.append({"p": proto, "e": round(float(p[0]), 1), "n": round(float(p[1]), 1),
                                          "step_m": round(step, 3)})
            else:   # legacy raster seat (no meshes)
                zg = self.ground_min(p, on_verge=not proto.startswith("sign_post"))
            if z is None or z < zg - SEAT_TOL:          # an explicit z above the ground is a bridge deck: kept
                if z is not None:
                    self.reseated += 1
                z = zg
        z = float(self.zsurf(np.array([p[0]]), np.array([p[1]]))[0]) if z is None else z
        it = {"p": proto, "e": round(float(p[0]), 3), "n": round(float(p[1]), 3), "z": round(z, 3),
              "yaw": round(float(yaw), 4), "src": src}
        if sz != 1.0:
            it["sz"] = round(float(sz), 3)
        self.items.append(it)
        if group:
            self.pts.setdefault(group, []).append((p[0], p[1]))
        return z


def side_surface_offset(c, side, s):
    kind, h, w, depth, mat = side_params(c, side, s)
    return kind, h, w, side_extent(kind, h, w, depth, mat)


# ------------------------------------------------------------------------------------------- carriageway check
GROUND_PROPS = ("lamp_", "sign_post", "signal_pole", "signal_mast", "bollard", "waste_bin", "bench", "power_pole",
                "street_cabinet", "bus_shelter", "pylon")


def clear_carriageway(pl, carriage, zsurf, report):
    """Ground-standing props whose base lies on a carriageway (rule placement near junction patches, OSM nodes
    drawn on the road axis) are pushed 0.8 m beyond the nearest carriageway edge; everything stacked on the same
    base (sign plates) moves with it and keeps its height above the base. Overhead items (signal heads on masts,
    gantry boards, booms) are not touched. Lamp / sign counts on the road were reported by the Unity importer."""
    import shapely
    from shapely.geometry import Point
    from shapely.ops import nearest_points
    inner = carriage.buffer(-0.05)
    shapely.prepare(inner)
    groups = {}
    for it in pl.items:
        groups.setdefault((round(it["e"], 2), round(it["n"], 2)), []).append(it)
    moved, left, drop = 0, [], set()
    for (e, n), items in groups.items():
        base = [it for it in items if it["p"].startswith(GROUND_PROPS)]
        if not base or not inner.contains(Point(e, n)):
            continue
        q = nearest_points(carriage.boundary, Point(e, n))[0]
        v = np.array([q.x - e, q.y - n])
        L = float(np.hypot(*v))
        new = np.array([q.x, q.y]) + (v / L if L > 1e-6 else np.array([1.0, 0.0])) * 0.8
        if inner.contains(Point(*new)):
            left.append({"p": base[0]["p"], "at": [round(e, 1), round(n, 1)], "src": base[0].get("src", "")})
            drop.update(id(it) for it in items)      # a pole in the middle of a lane is worse than a missing one
            continue
        z0 = (pl.seat(base[0]["p"], new)[0] if pl.surf is not None else pl.ground_min(new)) \
            if base[0]["p"].startswith(SEATED_POLES) else \
            float(zsurf(np.array([new[0]]), np.array([new[1]]))[0])
        dz = z0 - base[0]["z"]
        for it in items:
            it["e"], it["n"] = round(float(new[0]), 3), round(float(new[1]), 3)
            it["z"] = round(it["z"] + dz, 3)
        moved += 1
    if drop:
        pl.items[:] = [it for it in pl.items if id(it) not in drop]
    report["props_off_carriageway"] = {"moved": moved, "still_on_road": 0, "removed": left[:20]}


def clear_under_decks(pl, parts, report):
    """Ground-standing poles whose shaft would pierce a bridge deck above them are removed with everything stacked
    on the same base (ADR 0076, owner 2026-11-10: "a lamp stands in the middle of the lane" on the Andersa
    viaduct - a 12 m lamp of the road below came up through the deck). Lamps along a road that passes under a
    viaduct are placed by the same rule as anywhere else; under the deck there is no room for the column."""
    # ADR 0117 (REVIEW s10-0110 P1-4): the deck barriers live in the `bridge` layer since ADR 0110 - their rails
    # 0.7-1.1 m above the cap read as "a deck above the pole" and every lamp on the caps of the DK8 Putry decks was
    # removed (p0_lamp_putry_eye). Only the structure counts, not the steel on it.
    deck = SurfaceTop([p for p in parts if p.mat != "barrier_steel"], layers=("bridge",))
    groups = {}
    for it in pl.items:
        groups.setdefault((round(it["e"], 2), round(it["n"], 2)), []).append(it)
    drop, removed = set(), []
    for (e, n), items in groups.items():
        base = [it for it in items if it["p"].startswith(GROUND_PROPS)]
        if not base:
            continue
        b = min(base, key=lambda it: it["z"])
        h = S.ground_prop_height(b["p"])
        r = 0.6
        zs = [deck.top(e + dx, n + dy) for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r))]
        zs = [z for z in zs if math.isfinite(z)]
        if zs and any(b["z"] + 0.5 < z < b["z"] + h + 0.5 for z in zs):
            drop.update(id(it) for it in items)
            removed.append({"p": b["p"], "at": [round(e, 1), round(n, 1)], "base_z": round(b["z"], 2),
                            "deck_z": round(max(zs), 2), "src": b.get("src", "")})
    if drop:
        pl.items[:] = [it for it in pl.items if id(it) not in drop]
    report["poles_under_decks"] = {"removed": len(removed), "items": removed[:40]}


def clear_level_carriageways(pl, parts, report):
    """Ground-standing props whose base stands on a carriageway at its own level are removed with everything
    stacked on them (ADR 0076). clear_carriageway works on the 2D footprint of the ground roads only: a lamp of
    one deck carriageway placed 0.6 m beyond its edge landed in the lane of the carriageway laid abreast of it,
    and a ground lamp at a junction corner under another ribbon stayed (consistency.prop_on_carriageway: 2).
    Same criterion as that check: carriageway under the base and under 4 points PROP_INSET_M around it, within
    DZ_M of the base height, nothing else (kerb, sidewalk, island) on top."""
    from roads import consistency as CQ
    idx = CQ.SurfaceIndex(parts)
    groups = {}
    for it in pl.items:
        groups.setdefault((round(it["e"], 2), round(it["n"], 2)), []).append(it)
    ring = [(0.0, 0.0), (CQ.PROP_INSET_M, 0.0), (-CQ.PROP_INSET_M, 0.0), (0.0, CQ.PROP_INSET_M), (0.0, -CQ.PROP_INSET_M)]
    drop, removed = set(), []
    for (e, n), items in groups.items():
        base = [it for it in items if it["p"].startswith(CQ.GROUND_PROPS)]
        if not base:
            continue
        b = min(base, key=lambda it: it["z"])
        lab = idx.classify(np.array([[e + dx, n + dy, b["z"]] for dx, dy in ring]))
        if all(x == "carriageway" for x in lab):
            drop.update(id(it) for it in items)
            removed.append({"p": b["p"], "at": [round(e, 1), round(n, 1)], "src": b.get("src", "")})
    if drop:
        pl.items[:] = [it for it in pl.items if id(it) not in drop]
    report["props_on_level_carriageway"] = {"removed": len(removed), "items": removed[:40]}


# ------------------------------------------------------------------------------------------- authored lamp rows
CONSOLE_OUT_M = 0.30       # WORKING_VALUE: column axis outside the deck fascia on a console (ADR 0133)
CAP_IN_M = 0.35            # deck-top sample this far inside the fascia edge (cap top = console top)


def lamp_rows(pl, parts, path, report):
    """Authored lamp rows (ADR 0133, `<region>/lamp_rows.json`, survives every regeneration): positions measured
    on the GUGiK 0.08 m orthophoto replace the rule lamps of the named chains within `within_m` of the row.
    Runs after the carriageway / island / deck clearing passes: the row is authored, and a column on a console in
    the gap between two decks stands above the ground roads under it (clear_carriageway would push it away).
    A point within `deck_snap_m` of a bridge deck goes on a console at the nearest deck edge (fascia), on the
    cap-top height, arms across the road (+y toward the deck); otherwise it is a ground column on the terrain."""
    import json
    from pathlib import Path
    from shapely.ops import nearest_points
    from roads import consistency as CQ
    path = Path(path)
    if not path.exists():
        return
    rows = json.loads(path.read_text(encoding="utf-8")).get("rows", [])
    tops = [p for p in parts if p.layer == "bridge" and p.mat not in ("barrier_steel", "noise_glass")
            and not p.src.endswith(":parapet")]
    deck = SurfaceTop(tops, layers=("bridge",))
    idx = CQ.SurfaceIndex(parts)
    out = {}
    for row in rows:
        P = np.asarray(row["points_en"], float)
        line = LineString(P)
        sup = row.get("suppress_rule_lamps", {})
        pre = tuple(f"rule:c:w{w}:" for w in sup.get("osm_way", []))
        zone = line.buffer(float(sup.get("within_m", 0.0)))
        groups = {}
        for it in pl.items:
            groups.setdefault((round(it["e"], 2), round(it["n"], 2)), []).append(it)
        drop, removed = set(), 0
        for (e, n), items in groups.items():
            b = [it for it in items if it["p"].startswith("lamp_") and it.get("src", "").startswith(pre)] if pre else []
            if b and zone.contains(Point(e, n)):
                drop.update(id(it) for it in items)
                removed += 1
        if drop:
            pl.items[:] = [it for it in pl.items if id(it) not in drop]
        # deck plan footprint near the row (upward faces of the bridge layer)
        box = line.buffer(row.get("deck_snap_m", 2.6) + 2.0)
        A = deck.A
        if len(A):
            x0, y0, x1, y1 = box.bounds
            lo, hi = A[:, :, :2].min(1), A[:, :, :2].max(1)
            cand = A[(hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 1] >= y0) & (lo[:, 1] <= y1)]
            polys = shapely.polygons(np.concatenate([cand[:, :, :2], cand[:, :1, :2]], axis=1)) if len(cand) else []
            polys = [g for g in polys if g.intersects(box)]
            foot = shapely.union_all(polys).buffer(0.02).buffer(-0.02) if polys else None
        else:
            foot = None
        placed = []
        for k, p in enumerate(P):
            t = P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]
            t = t / np.linalg.norm(t)
            nrm = np.array([-t[1], t[0]])
            q, z, proto, u = p, None, row["proto"], nrm
            if foot is not None and not foot.is_empty:
                inside = foot.contains(Point(*p))
                a, _ = nearest_points(foot.boundary if inside else foot, Point(*p))
                edge = np.array([a.x, a.y])
                d = float(np.hypot(*(edge - p)))
                if not inside and d <= float(row.get("deck_snap_m", 2.6)):
                    u = (edge - p) / max(d, 1e-9)                 # toward the deck, across the road
                    u = u if abs(float(u @ nrm)) > 0.7 else nrm * np.sign(float((edge - p) @ nrm) or 1.0)
                    zc = deck.top(*(edge + u * CAP_IN_M))
                    if math.isfinite(zc):
                        q, z, proto = edge - u * CONSOLE_OUT_M, float(zc), row["proto_console"]
                elif inside:
                    zc = deck.top(*p)
                    z = float(zc) if math.isfinite(zc) else None
            lab = idx.classify(np.array([[q[0], q[1], z if z is not None else float(pl.seat(proto, q)[0])]]))[0]
            if lab == "carriageway":
                placed.append({"k": k, "at": [round(float(q[0]), 1), round(float(q[1]), 1)], "skipped": "carriageway"})
                continue
            zb = pl.add(proto, q, yaw_of(u), z=z, src=f"authored:{row['id']}:{k}", group="lamp")
            placed.append({"k": k, "p": proto, "at": [round(float(q[0]), 2), round(float(q[1]), 2)], "z": round(zb, 2),
                           "shift_m": round(float(np.hypot(*(np.asarray(q) - p))), 2)})
        out[row["id"]] = {"rule_lamps_removed": removed, "placed": sum(1 for x in placed if "p" in x),
                          "console": sum(1 for x in placed if x.get("p") == row["proto_console"]), "items": placed}
    report["lamp_rows"] = out


NARROW_ISLAND_R = 1.0      # WORKING_VALUE: carriageway within this distance on two opposite sides = separation < ~2 m


def clear_narrow_islands(pl, parts, net, report):
    """No lamp on a separation narrower than ~2 m (ADR 0093, REVIEW 0076 #7: a lamp on the needle tip of an island
    at E -774.5 N 77.5, luminaire over the lane). A rule-placed lamp with carriageway within NARROW_ISLAND_R on two
    opposite sides is moved to the other edge of its own carriageway (the outer side of a ramp) when that spot is
    clear, otherwise removed with everything stacked on it."""
    from roads import consistency as CQ
    idx = CQ.SurfaceIndex(parts)
    ang = np.arange(8) * (math.pi / 4)
    ring = np.column_stack([np.cos(ang), np.sin(ang)]) * NARROW_ISLAND_R
    chains = {c.id: c for c in net.chains}

    def narrow(e, n, z):
        lab = idx.classify(np.array([[e + dx, n + dy, z] for dx, dy in ring]))
        return any(lab[k] == "carriageway" and lab[k + 4] == "carriageway" for k in range(4))

    groups = {}
    for it in pl.items:
        groups.setdefault((round(it["e"], 2), round(it["n"], 2)), []).append(it)
    drop, moved, removed, add = set(), [], [], []
    for (e, n), items in groups.items():
        base = [it for it in items if it["p"].startswith("lamp_")]
        if not base:
            continue
        b = min(base, key=lambda it: it["z"])
        if not narrow(e, n, b["z"]):
            continue
        drop.update(id(it) for it in items)
        c = chains.get(b.get("src", "")[5:]) if b.get("src", "").startswith("rule:") else None
        q = None
        # first choice: the outer edge of the carriageway on the far side of the island (a ramp beside the main
        # carriageway keeps its lamps on its outer edge), then the other edge of the lamp's own carriageway
        tries = []
        if c is not None:
            s_own, lat_own = c.line.project(np.array([e, n]))
            best = None
            for c2 in net.chains:
                if c2 is c or c2.meta.get("absorbed") or c2.roundabout:
                    continue
                lo, hi = c2.line.p.min(0) - 12, c2.line.p.max(0) + 12
                if not (lo[0] <= e <= hi[0] and lo[1] <= n <= hi[1]):
                    continue
                s2, lat2 = c2.line.project(np.array([e, n]))
                if not (0.0 < s2 < c2.length):
                    continue
                gap = abs(lat2) - float(c2.hw_at(s2))
                if -0.2 < gap < 2 * NARROW_ISLAND_R and (best is None or gap < best[0]):
                    best = (gap, c2, float(s2), -1.0 if lat2 > 0 else 1.0)
            if best is not None:
                tries.append(best[1:])
            tries.append((c, float(np.clip(s_own, 0.0, c.length)), -1.0 if lat_own > 0 else 1.0))
        for c, s, sgn in tries:
            if q is not None:
                break
            if not bool(c.bridge[c.idx(s)]):
                kind, h, w, ext = side_surface_offset(c, "L" if sgn > 0 else "R", s)
                if kind != MEDIAN_RURAL:
                    hw = float(c.hw_at(s))
                    off = hw + (S.KERB_TOP_W + S.LAMP_OFFSET if kind == URBAN else ext + 0.8)
                    q = np.asarray(c.line.offset_point(s, sgn * off), float).reshape(-1)[:2]
                    zq = float(c.crossfall_z(s, sgn * hw))
                    lab = idx.classify(np.array([[q[0], q[1], zq]] + [[q[0] + dx * 0.25, q[1] + dy * 0.25, zq]
                                                                    for dx, dy in ring[::2]]))
                    if any(x == "carriageway" for x in lab) or narrow(q[0], q[1], zq) or pl.near("lamp", q, 8.0):
                        q = None
                    else:
                        t, nn = c.line.frame(s)
                        add.append((b["p"], q, yaw_of(-np.asarray(nn) * sgn), b.get("src", "")))
        (moved if q is not None else removed).append({"p": b["p"], "from": [round(e, 1), round(n, 1)],
                                                      "to": None if q is None else [round(float(q[0]), 1), round(float(q[1]), 1)],
                                                      "src": b.get("src", "")})
    if drop:
        pl.items[:] = [it for it in pl.items if id(it) not in drop]
    for proto, q, yaw, src in add:
        pl.add(proto, q, yaw, src=src, group="lamp")
    report["lamps_on_narrow_islands"] = {"moved": len(moved), "removed": len(removed), "radius_m": NARROW_ISLAND_R,
                                         "items": (moved + removed)[:60]}


# ------------------------------------------------------------------------------------------- lamps
def lamps(pl, net, osm_nodes, origin, report):
    n0 = 0
    for nd in osm_nodes:
        if nd["tags"].get("highway") == "street_lamp":
            x, y = np.asarray(nd["geometry"]["coordinates"]) - origin
            pl.add("lamp_10m", (x, y), 0.0, src=f"osm:node/{nd['osm_node']}", group="lamp")
            n0 += 1
    n = 0
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout:
            continue
        sec = c.section(c.length / 2, net.sec_list)
        if sec.cls not in S.LAMP or sec.highway in ("service",) and c.length < 60:
            continue
        spec = S.LAMP[sec.cls]
        # older side-street family (critic R2 #10): one family per street (hash of the chain), never on G/GP;
        # residential streets 65 % old (spun-concrete poles dominate), other L/D roads 30 % (grey steel)
        proto = f"lamp_{int(spec['h'])}m"
        if sec.cls in ("L", "D", "Z") and sec.highway not in ("primary", "secondary", "trunk"):
            u = _h(c.id + ":lampfamily") % 100
            res = sec.highway in ("residential", "living_street")
            if u < (65 if res else 30):
                proto = "lamp_old_concrete_9m" if (res and u < 50) or (not res and u < 8) else "lamp_old_steel_8m"
        oneway = sec.oneway
        sides = ["R"] if (oneway and (c.dirn > 0).mean() >= 0.5) or not oneway else ["L"]
        s0, s1 = c.t_a + 4, c.length - c.t_b - 4
        if s1 - s0 < spec["spacing"] * 0.6:
            continue
        for side in sides:
            sgn = 1.0 if side == "L" else -1.0
            for s in np.arange(s0 + (_h(c.id) % 7), s1, spec["spacing"]):
                kind, h, w, ext = side_surface_offset(c, side, s)
                if kind == MEDIAN_RURAL:
                    continue
                hw = float(c.hw_at(s))
                off = hw + (S.KERB_TOP_W + S.LAMP_OFFSET if kind == URBAN else ext + 0.8)
                p = c.line.offset_point(s, sgn * off)
                if pl.near("lamp", p, spec["spacing"] * 0.45):
                    continue
                t, nn = c.line.frame(s)
                face = -nn * sgn                       # bracket toward the road
                z = None
                if c.bridge[c.idx(s)]:
                    z = float(c.crossfall_z(s, sgn * hw)) + S.BRIDGE_KERB_H
                    # ADR 0117: on a narrow cap (bridge_style cap_w < 1.3 m) the barrier stands 0.7 m behind the kerb
                    # face - the pole goes behind it, at the cap edge (0.6 m would put it in the barrier line)
                    cw = bridge_cap_w(c)
                    p = c.line.offset_point(s, sgn * (hw + S.KERB_TOP_W + (0.6 if cw >= 1.3 else cw - 0.12)))
                pl.add(proto if z is None else f"lamp_{int(spec['h'])}m", p, yaw_of(face), z=z, src=f"rule:{c.id}",
                       group="lamp")
                n += 1
    report["lamps"] = {"osm": n0, "rule": n,
                       "support_adjustments": pl.support_moves,
                       "by_family": {k: sum(1 for it in pl.items if it["p"] == k) for k in
                                     sorted({it["p"] for it in pl.items if it["p"].startswith("lamp_")})}}


def bridge_median_lamps(pl, net, report):
    """ADR 0123 (REVIEW s10-0117 P2-1, RING-B): bridge_style `lamps: {side: median, spacing_m, anchor_en}` - the lamps
    of a twin-deck viaduct stand between the decks with two arms (orthophoto of the Andersa viaduct over Rondo
    Biezenstwa: twin-arm columns in the gap every ~32 m; Mapillary 454716650857984 / 2948595898752384 from the deck),
    not one per deck on the outer cap as the one-way rule of lamps() puts them. The rule lamps standing on those decks
    are removed and twin lamps (two `lamp_<h>m` back to back on one base: no new prototype, no extra draw call) are set
    on the inner cap edge of the first deck, at stations spacing_m apart through the point of the deck edge nearest
    to anchor_en (a column read off the orthophoto)."""
    groups = {}
    for c in net.chains:
        if c.meta.get("absorbed") or c.bridge is None or not c.bridge.any():
            continue
        st = bridge_style(c).get("lamps")
        if isinstance(st, dict) and st.get("side") == "median":
            groups.setdefault(json.dumps(st, sort_keys=True), []).append(c)
    out = {"removed": 0, "placed": 0}
    for key, chains in sorted(groups.items()):
        st = json.loads(key)
        chains = sorted(chains, key=lambda c: c.id)
        lead = chains[0]
        srcs = {f"rule:{c.id}" for c in chains}

        def on_deck(it):
            for c in chains:
                if it.get("src") == f"rule:{c.id}":
                    s_, _ = c.line.project(np.array([it["e"], it["n"]]))
                    return bool(c.bridge[c.idx(float(s_))])
            return False
        drop = [it for it in pl.items if it["p"].startswith("lamp_") and it.get("src") in srcs and on_deck(it)]
        if drop:
            ids = {id(it) for it in drop}
            pl.items[:] = [it for it in pl.items if id(it) not in ids]
            gone = {(round(it["e"], 3), round(it["n"], 3)) for it in drop}
            pl.pts["lamp"] = [q for q in pl.pts.get("lamp", []) if (round(float(q[0]), 3), round(float(q[1]), 3)) not in gone]
            out["removed"] += len(drop)
        # the median is on the side of the other deck
        sm = lead.length / 2
        if len(chains) > 1:
            other = np.asarray(chains[1].line.point(chains[1].length / 2), float)
            sm, _ = lead.line.project(other)
            t, nn = lead.line.frame(float(sm))
            sgn = 1.0 if float(np.dot(other - np.asarray(lead.line.point(float(sm)), float), nn)) > 0 else -1.0
        else:
            sgn = 1.0
        sec = lead.section(lead.length / 2, net.sec_list)
        h = int(S.LAMP.get(sec.cls, S.LAMP["GP"])["h"])
        spacing = float(st.get("spacing_m") or S.LAMP.get(sec.cls, S.LAMP["GP"])["spacing"])
        s0 = lead.t_a + 4.0
        if st.get("anchor_en"):
            s0, _ = lead.line.project(np.asarray(st["anchor_en"], float))
        s_lo, s_hi = lead.t_a + 4.0, lead.length - lead.t_b - 4.0
        k0 = int(math.floor((s_lo - s0) / spacing))
        cw = bridge_cap_w(lead)
        for k in range(k0, int((s_hi - s0) / spacing) + 2):
            sx = float(s0 + k * spacing)
            if not (s_lo <= sx <= s_hi) or not lead.bridge[lead.idx(sx)]:
                continue
            hw = float(lead.hw_at(sx))
            p_ = lead.line.offset_point(sx, sgn * (hw + S.KERB_TOP_W + cw - 0.12))
            t, nn = lead.line.frame(sx)
            z = float(lead.crossfall_z(sx, sgn * hw)) + S.BRIDGE_KERB_H
            for f_ in (-1.0, 1.0):
                pl.add(f"lamp_{h}m", p_, yaw_of(np.asarray(nn) * sgn * f_), z=z, src=f"rule:median:{lead.id}", group="lamp")
            out["placed"] += 1
    report["bridge_median_lamps"] = out


# ------------------------------------------------------------------------------------------- signs
def sign_assembly(pl, p, face, plates, src, z=None, sidewalk=False):
    """Post + plates stacked from the lower edge (Table 1.11: >= 2.00 m, 2.20 m on a sidewalk)."""
    import streetscape.signs as SG
    yaw = yaw_of(face)
    zb = pl.add("sign_post", p, yaw, z=z, sz=1.0, src=src)
    zc = zb + (S.SIGN_H_SIDEWALK if sidewalk else S.SIGN_H_MIN)
    centres = []
    for code in reversed(plates):              # plates listed top first
        shape, _ = SG.face(code)
        size = S.SIGN_SIZE[shape] * (math.sqrt(3) / 2 if shape == "triangle" else 1.0)
        centres.append((code, zc + size / 2, shape))
        zc += size + 0.05
    pl.items[-1]["sz"] = round(zc - zb + 0.05, 3)
    for code, zcen, shape in centres:
        if shape == "triangle":                  # inverted triangle: centroid 1/3 from the top edge
            h = S.SIGN_SIZE["triangle"] * math.sqrt(3) / 2
            zcen = zcen - h / 2 + 2 * h / 3
        pl.add(f"plate_{code}", p, yaw, z=zcen, src=src)
    return [c for c, _, _ in centres]


def junction_signs(pl, net, juncs, ctx_points, report, codes):
    cnt = {}

    def put(arm, plates, src, extra=None):
        d = arm.chain.t_a if arm.end == "a" else arm.chain.t_b
        d = d + 3.0
        if d > arm.L - 2:
            return
        c = arm.chain
        s = float(arm.s(d))
        side = "L" if arm.end == "a" else "R"         # right of inbound traffic = left of outward direction
        kind, h, w, ext = side_surface_offset(c, side, s)
        off = S.KERB_TOP_W + S.SIGN_LATERAL if kind != RURAL else ext + 0.5
        p = arm.gutter(d, +1, extra=off if extra is None else extra)
        face = arm.direction(d)
        if pl.near("sign", p, 1.5):
            return
        z = None
        if c.bridge[c.idx(s)]:
            return
        for cd in sign_assembly(pl, p, face, plates, src, z=z, sidewalk=w > 0.5):
            codes.add(cd)
            cnt[cd] = cnt.get(cd, 0) + 1
        pl.pts.setdefault("sign", []).append((p[0], p[1]))

    pts = {}
    for q in ctx_points:
        pts.setdefault(q["kind"], []).append(np.array([q["e"], q["n"]]))
    for j in juncs:
        inb = [a for a in j.arms if a.inbound_dirn() >= 0 and not a.is_ring()]
        if j.roundabout:
            for a in inb:
                put(a, ["A-7", "C-12"], f"rule:roundabout:{j.id}")
            continue
        if j.signalized:
            continue
        ranks = [RANK[a.cls(net.sec_list)] for a in j.arms]
        best = min(ranks)
        ctr = j.center if j.center is not None else np.mean([net.nodes[n]["xy"] for n in j.nodes], axis=0)
        stop = any(np.hypot(*(q - ctr)) < 25 for q in pts.get("highway=stop", []))
        give = any(np.hypot(*(q - ctr)) < 25 for q in pts.get("highway=give_way", []))
        for a in inb:
            r = RANK[a.cls(net.sec_list)]
            if r > best and a.cls(net.sec_list) in ("Z", "L", "G") or (r > best and (stop or give) and r < 6):
                put(a, ["B-20" if stop else "A-7"], f"rule:minor:{j.id}")
            elif r == best and best <= RANK["Z"] and max(ranks) > best and max(ranks) < 6:
                put(a, ["D-1"], f"rule:major:{j.id}")
    report["junction_signs"] = cnt


def speed_signs(pl, net, report, codes):
    n = 0
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout or c.length < 80:
            continue
        dirs = [1] if (c.dirn > 0).mean() >= 0.5 else [-1] if (c.dirn < 0).mean() >= 0.5 else [1, -1]
        for dn in dirs:
            s = (c.t_a + S.SPEED_SIGN_AFTER_JUNCTION) if dn > 0 else (c.length - c.t_b - S.SPEED_SIGN_AFTER_JUNCTION)
            if not (0 < s < c.length) or c.bridge[c.idx(s)]:
                continue
            # the limit of the section the sign stands on (a chain spans several OSM ways: MA-007 showed 90 where
            # the way under the sign has maxspeed=70)
            v = c.section(s, net.sec_list).maxspeed
            if not v or int(v) == 50:
                continue
            side = "R" if dn > 0 else "L"
            sgn = -1.0 if side == "R" else 1.0
            kind, h, w, ext = side_surface_offset(c, side, s)
            off = float(c.hw_at(s)) + (S.KERB_TOP_W + S.SIGN_LATERAL if kind != RURAL else ext + 0.5)
            p = c.line.offset_point(s, sgn * off)
            t, _ = c.line.frame(s)
            code = f"B-33_{int(v)}"
            sign_assembly(pl, p, -t * dn, [code], f"rule:maxspeed:{c.id}", sidewalk=w > 0.5)
            codes.add(code)
            n += 1
    report["speed_signs"] = n


def nearest_chain(net, p, maxd=25.0):
    best = None
    for c in net.chains:
        lo, hi = c.line.p.min(0) - maxd, c.line.p.max(0) + maxd
        if not (lo[0] <= p[0] <= hi[0] and lo[1] <= p[1] <= hi[1]):
            continue
        s, lat = c.line.project(np.asarray(p, float))
        d = abs(lat) - float(c.hw_at(s))
        if d < maxd and (best is None or d < best[0]):
            best = (d, c, s, lat)
    return best


def crossing_signs(pl, net, ctx_points, report, codes):
    n = 0
    for q in ctx_points:
        if q["kind"] != "highway=crossing" or q.get("crossing") in ("unmarked", "no", "traffic_signals") \
                or q.get("crossing") == "uncontrolled" and False:
            continue
        hit = nearest_chain(net, (q["e"], q["n"]), 3.0)
        if not hit:
            continue
        _, c, s, _ = hit
        if c.roundabout or c.bridge[c.idx(s)]:
            continue
        hw = float(c.hw_at(s))
        t, _ = c.line.frame(s)
        dirs = [1] if (c.dirn > 0).mean() >= 0.5 else [-1] if (c.dirn < 0).mean() >= 0.5 else [1, -1]
        for dn in dirs:
            side = "R" if dn > 0 else "L"
            sgn = -1.0 if side == "R" else 1.0
            ss = s - dn * (S.P10_WIDTH / 2 + 0.5)
            kind, h, w, ext = side_surface_offset(c, side, ss)
            p = c.line.offset_point(ss, sgn * (hw + S.KERB_TOP_W + S.SIGN_LATERAL))
            if pl.near("sign", p, 1.0):
                continue
            sign_assembly(pl, p, -t * dn, ["D-6"], f"osm:node/{q['osm_node']}", sidewalk=w > 0.5)
            pl.pts.setdefault("sign", []).append((p[0], p[1]))
            codes.add("D-6")
            n += 1
    report["crossing_signs"] = n


def direction_boards(pl, net, graph_attrs, report, boards):
    """Schematic E-2 boards at the start of *_link chains with a destination tag."""
    import streetscape.signs as SG
    n = 0
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        sec = c.section(c.t_a + 1, net.sec_list)
        if not sec.highway.endswith("_link") or not sec.oneway:
            continue
        a = graph_attrs.get(sec.edge_id, {})
        dest = (a.get("destination") or {}).get("v")
        if not dest:
            continue
        ref = (a.get("ref") or {}).get("v") or ""
        fwd = (c.dirn > 0).mean() >= 0.5
        s = c.t_a + 6 if fwd else c.length - c.t_b - 6
        if not (0 < s < c.length):
            continue
        dn = 1 if fwd else -1
        sgn = -1.0 if fwd else 1.0
        hw = float(c.hw_at(s))
        side = "R" if fwd else "L"
        kind, h, w, ext = side_surface_offset(c, side, s)
        p = c.line.offset_point(s, sgn * (hw + (S.KERB_TOP_W + 1.2 if kind != RURAL else ext + 1.0)))
        t, _ = c.line.frame(s)
        key = f"E-2_{_h(dest + ref) % 100000:05d}"
        refs = [r.strip() for r in ref.split(";") if r.strip()]
        if key not in boards:
            im, wm, hm = SG.direction_board(dest.split(";"), refs, green=bool(refs))
            boards[key] = (round(wm, 3), round(hm, 3), im)
        wm, hm, _ = boards[key]
        z = pl.add("sign_post", p - t * dn * 0 + np.array([0, 0]), yaw_of(-t * dn), sz=S.SIGN_H_MIN + hm,
                   src=f"rule:destination:{c.id}")
        pl.add(f"board_{key}", p, yaw_of(-t * dn), z=z + S.SIGN_H_MIN + hm / 2, src=f"rule:destination:{c.id}")
        n += 1
    report["direction_boards"] = n


# ------------------------------------------------------------------------------------------- signals
def signals(pl, net, juncs, report):
    n = 0
    for j in juncs:
        emerg = getattr(j, "emergency_signals", False)
        if not (j.signalized or emerg):
            continue
        for k, a in enumerate(j.arms):
            if a.inbound_dirn() < 0 or a.is_ring():
                continue
            if emerg and a.cls(net.sec_list) in ("D",):
                continue                    # emergency signals face the main road, not the fire-station exit

            d = (a.chain.t_a if a.end == "a" else a.chain.t_b) + 1.0
            if d > a.L - 1:
                continue
            c = a.chain
            s = float(a.s(d))
            if c.bridge[c.idx(s)]:
                continue
            side = "L" if a.end == "a" else "R"
            kind, h, w, ext = side_surface_offset(c, side, s)
            p = a.gutter(d, +1, extra=S.KERB_TOP_W + 0.6)
            face = a.direction(d)
            lit = "red" if (_h(j.id) + k) % 2 == 0 else "green"
            if emerg:
                lit = "off"                 # traffic_signals=emergency: dark at rest (ADR 0074)
            sec = c.section(s, net.sec_list)
            lanes_in = sec.lanes if sec.oneway else max(1, sec.lanes_fwd if a.end == "b" else sec.lanes_bwd)
            right = np.array([face[1], -face[0]])                # from the right kerb toward the carriageway
            if lanes_in >= S.SIGNAL_CANTILEVER_LANES and not emerg:
                z = pl.add("signal_mast", p, yaw_of(right), src=f"rule:signal:{j.id}")
                head = p + right * 5.0
                pl.add(f"signal_head_{lit}", head, yaw_of(face), z=z + S.SIGNAL_MAST_H - 1.25, src=f"rule:signal:{j.id}")
            else:
                z = pl.add("signal_pole", p, yaw_of(face), src=f"rule:signal:{j.id}")
            pl.add(f"signal_head_{lit}", p + face * 0.15, yaw_of(face), z=z + 2.9, src=f"rule:signal:{j.id}")
            # repeater on the left (median kerb) of one-way approaches with >= 2 lanes, as on the Andersa / Maczka
            # photos (S-1 repeated on the left side; Dz.U. 2019 poz. 2311 zał. 3 - paragraph UNVERIFIED, not re-read)
            if sec.oneway and lanes_in >= 2:
                pL = a.gutter(d, -1, extra=S.KERB_TOP_W + 0.6)
                zl = pl.add("signal_pole", pL, yaw_of(face), src=f"rule:signal:{j.id}:left")
                pl.add(f"signal_head_{lit}", pL + face * 0.15, yaw_of(face), z=zl + 2.9, src=f"rule:signal:{j.id}:left")
                rep_left = report.setdefault("signal_repeaters_left", 0)
                report["signal_repeaters_left"] = rep_left + 1
            n += 1
    report["signal_approaches"] = n


# ------------------------------------------------------------------------------------------- misc points
def misc_points(pl, net, src, origin, report, codes):
    cnt = {}
    # JSON-safe source metadata only. Actual road/whole-footprint validation happens before decal emission.
    report["bus_stop_wear_candidates"] = [
        {"osm_node": nd["osm_node"], "ref": nd["tags"].get("ref"), "bus": nd["tags"].get("bus"),
         "local_en": (np.asarray(nd["geometry"]["coordinates"], float) - origin).tolist(),
         "half_m": (src["bbox"][2] - src["bbox"][0]) * .5}
        for nd in src["osm"]["nodes"] if nd["tags"].get("public_transport") == "stop_position"
    ]
    stops = [np.asarray(nd["geometry"]["coordinates"]) - origin for nd in src["osm"]["nodes"]
             if nd["tags"].get("highway") == "bus_stop"]
    for f in src["bdot10k"]["OT_OIKM_P"]:
        q = np.asarray(f["geometry"]["coordinates"]) - origin
        if all(np.hypot(*(q - s)) > 30 for s in stops):
            stops.append(q)
    for q in stops:
        hit = nearest_chain(net, q, 20.0)
        if not hit:
            continue
        _, c, s, lat = hit
        sgn = 1.0 if lat > 0 else -1.0
        side = "L" if sgn > 0 else "R"
        kind, h, w, ext = side_surface_offset(c, side, s)
        hw = float(c.hw_at(s))
        t, nn = c.line.frame(s)
        p = c.line.offset_point(s, sgn * (hw + max(ext, 2.2) + 1.0))
        pl.add("bus_shelter", p, yaw_of(-nn * sgn), src="bus_stop")
        pb = c.line.offset_point(s + (2.9 if hash(round(float(s), 1)) % 2 else -2.9), sgn * (hw + max(ext, 2.2) + 0.4))
        pl.add("waste_bin", pb, yaw_of(-nn * sgn), src="bus_stop:bin")
        dn = -1 if side == "L" else 1          # traffic on this side travels +s on the right side
        ps = c.line.offset_point(s + dn * 4.0, sgn * (hw + S.KERB_TOP_W + 0.6))
        sign_assembly(pl, ps, -t * dn, ["D-15"], "bus_stop", sidewalk=True)
        codes.add("D-15")
        cnt["bus_stop"] = cnt.get("bus_stop", 0) + 1
    for nd in src["osm"]["nodes"]:
        t = nd["tags"]
        q = np.asarray(nd["geometry"]["coordinates"]) - origin
        proto = None
        if t.get("barrier") == "lift_gate":
            proto = "lift_gate"
        elif t.get("barrier") in ("gate", "sliding_gate", "swing_gate"):
            proto = "sliding_gate"
        elif t.get("barrier") == "cycle_barrier" or t.get("bollard") == "hoop":
            proto = "bollard_hoop"
        elif t.get("barrier") == "bollard":
            proto = "bollard"
        elif t.get("amenity") == "bench":
            proto = "bench"
        elif t.get("amenity") == "waste_basket":
            proto = "waste_bin"
        elif t.get("man_made") == "street_cabinet":
            proto = "street_cabinet"
        elif t.get("power") == "tower":
            proto = "pylon"
        elif t.get("power") == "pole":
            proto = "power_pole"
        if not proto:
            continue
        yaw = 0.0
        p = q
        if proto in ("lift_gate", "sliding_gate"):
            hit = nearest_chain(net, q, 6.0)
            if hit:
                _, c, s, lat = hit
                tt, nn = c.line.frame(s)
                hw = float(c.hw_at(s))
                if proto == "lift_gate":
                    p = c.line.offset_point(s, -(hw + 0.5))           # post at the right edge, boom across
                    yaw = math.atan2(nn[1], nn[0])                    # local +x -> chain left normal
                else:
                    p = c.line.offset_point(s, 0.0)
                    yaw = math.atan2(nn[1], nn[0])
        if pl.near(proto, p, 3.0):
            continue
        pl.add(proto, p, yaw, src=f"osm:node/{nd['osm_node']}", group=proto)
        cnt[proto] = cnt.get(proto, 0) + 1
    for f in src["bdot10k"]["OT_BUWT_P"]:
        if f["props"].get("rodzaj") != "słup energetyczny":
            continue
        q = np.asarray(f["geometry"]["coordinates"]) - origin
        if pl.near("power_pole", q, 4.0) or pl.near("pylon", q, 8.0):
            continue
        pl.add("power_pole", q, (_h(f["id"]) % 360) * math.pi / 180, src=f"bdot:{f['id']}", group="power_pole")
        cnt["power_pole"] = cnt.get("power_pole", 0) + 1
    report["points"] = cnt


# ------------------------------------------------------------------------------------------- linear
class Lin:
    def __init__(self, buf, zsurf):
        self.buf, self.zsurf = buf, zsurf

    def z(self, P):
        return self.zsurf(P[:, 0], P[:, 1])

    def dens(self, line, step):
        L = line.length
        n = max(1, int(math.ceil(L / step)))
        P = np.array([line.interpolate(L * k / n).coords[0] for k in range(n + 1)])
        return P

    def ribbon(self, mat, P, zb, zt, offset=0.0, src="", both=True, collision=None):
        """Vertical strip along P from zb to zt (arrays), both faces."""
        d = np.gradient(P, axis=0)
        d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
        nrm = np.column_stack([-d[:, 1], d[:, 0]])
        Q = P + nrm * offset
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
        n = len(Q)
        V = np.concatenate([np.column_stack([Q, zb]), np.column_stack([Q, zt])])
        UV = np.column_stack([np.tile(s, 2), np.concatenate([zb - zb, zt - zb])])
        T = [(k, k + 1, n + k + 1) for k in range(n - 1)] + [(k, n + k + 1, n + k) for k in range(n - 1)]
        T = np.array(T)
        self.buf.add("furniture", mat, V, UV, T, src=src)
        if both:
            self.buf.add("furniture", mat, V, UV, T[:, [0, 2, 1]], src=src)
        if collision:
            self.buf.add("collision", collision, V, UV, np.concatenate([T, T[:, [0, 2, 1]]]), src=src)

    def slab(self, mat, P, zb, zt, thick, src="", collision=None):
        # right face (offset -t/2) keeps the ribbon winding (faces right), the left face is flipped; the top faces up
        # only (nobody sees its underside). Before v3 both sides had the same winding -> see-through from one side.
        self.ribbon(mat, P, zb, zt, -thick / 2, src, both=False, collision=None)
        self.ribbon(mat, P[::-1], zb[::-1] if np.ndim(zb) else zb, zt[::-1] if np.ndim(zt) else zt, -thick / 2, src,
                    both=False, collision=None)
        d = np.gradient(P, axis=0)
        d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
        nrm = np.column_stack([-d[:, 1], d[:, 0]])
        A, B = P - nrm * thick / 2, P + nrm * thick / 2
        n = len(P)
        V = np.concatenate([np.column_stack([A, zt]), np.column_stack([B, zt])])
        T = np.array([(k, k + 1, n + k + 1) for k in range(n - 1)] + [(k, n + k + 1, n + k) for k in range(n - 1)])
        self.buf.add("furniture", mat, V, V[:, :2], T, src=src)
        if collision:
            self.ribbon(collision, P, zb, zt, 0.0, src, both=False, collision=None)
            self.buf.parts[-1].layer = "collision"

    def posts(self, mat, P, spacing, w, d, h, zb=None, src="", ground_feet=False):
        line = LineString(P)
        L = line.length
        ss = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))]) if spacing is None else np.arange(0, L + 1e-6, spacing)
        Q = np.asarray(P) if spacing is None else np.array([line.interpolate(s).coords[0] for s in ss])
        if len(Q) < 1:
            return
        Z = self.z(Q) if zb is None else np.interp(ss, np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))]), zb)
        dd = np.gradient(Q, axis=0) if len(Q) > 1 else np.array([[1.0, 0.0]])
        dd /= np.maximum(np.hypot(dd[:, 0], dd[:, 1]), 1e-9)[:, None]
        Vs, Ts = [], []
        for q, z, ground, t in zip(Q, Z, self.z(Q) if ground_feet else Z, dd):
            nn = np.array([-t[1], t[0]])
            c = [q[0], q[1], (ground - 0.3 + z + h) / 2]
            hx, hy, hz = t * w / 2, nn * d / 2, (z + h - ground + 0.3) / 2
            P8 = [np.array(c) + np.append(sx * hx + sy * hy, sz * hz) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
            faces = [(4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
            base = len(Vs)
            Vs += P8
            for f in faces:
                Ts += [(base + f[0], base + f[1], base + f[2]), (base + f[0], base + f[2], base + f[3])]
        V = np.array(Vs)
        self.buf.add("furniture", mat, V, V[:, :2], np.array(Ts), src=src)


def cut_by(line, poly):
    if poly is None or poly.is_empty:
        return [line]
    g = line.difference(poly)
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "LineString" and p.length > 1.0]


def concrete_fence(lin, line, key, style_key):
    """Prefabricated concrete fence (ADR 0081, typical plot fence of the Bialystok industrial area): bays of
    S.CONCRETE_FENCE_POST between H-posts; every bay is level and steps at the posts with the ground (the plates are
    cast flat, nobody rakes them), four stacked 0.5 m plates or one framed panel per bay from the fence_concrete atlas
    (UV0 = atlas metres, facade_atlas.fence_uv), a different cast on the two faces, posts 12 x 14 cm standing 8 cm
    above the plates. One fence = one style; sprayed / painted-over bays stay rare (1 in ~7). Returns the bay count."""
    L = line.length
    nb = max(1, int(round(L / S.CONCRETE_FENCE_POST)))
    Q = np.array([line.interpolate(L * k / nb).coords[0] for k in range(nb + 1)])
    Zg = lin.z(Q)
    style = "frame" if _h(style_key + ":style") % 10 < 3 else "plate"
    nv = FA.FENCE_VARIANTS[style]
    marked = {"plate": (1, 5, 6), "frame": (3,)}[style]
    H, T2 = S.CONCRETE_FENCE_H, 0.025
    Vs, UVs, Ts, Cv = [], [], [], []

    def quad(P4, uv):
        b = len(Vs)
        Vs.extend(P4)
        UVs.extend(uv)
        Ts.extend([(b, b + 1, b + 2), (b, b + 2, b + 3)])

    pu, pv, pw, ph = FA.fence_post_uv()
    tops = []
    for i in range(nb):
        q0, q1 = Q[i], Q[i + 1]
        t = (q1 - q0) / max(np.hypot(*(q1 - q0)), 1e-6)
        nn = np.array([-t[1], t[0]])
        zb = min(Zg[i], Zg[i + 1]) - 0.05
        zt = zb + H
        tops.append(zt)
        for side in (1, -1):
            v_ = (_h(f"{key}:{i}:{side}") >> 3) % nv
            if v_ in marked and _h(f"{key}:{i}:{side}:m") % 7:
                v_ = [x for x in range(nv) if x not in marked][_h(f"{key}:{i}:{side}:p") % (nv - len(marked))]
            u0, v0, w, h = FA.fence_uv(style, v_)
            o = nn * T2 * side
            A_, B_ = (q0, q1) if side < 0 else (q1, q0)             # CCW seen from the side the face looks at
            quad([[A_[0] + o[0], A_[1] + o[1], zb], [B_[0] + o[0], B_[1] + o[1], zb],
                  [B_[0] + o[0], B_[1] + o[1], zt], [A_[0] + o[0], A_[1] + o[1], zt]],
                 [[u0, v0], [u0 + w, v0], [u0 + w, v0 + h], [u0, v0 + h]])
        o = nn * T2                                                    # top edge of the upper plate
        quad([[q0[0] - o[0], q0[1] - o[1], zt], [q1[0] - o[0], q1[1] - o[1], zt],
              [q1[0] + o[0], q1[1] + o[1], zt], [q0[0] + o[0], q0[1] + o[1], zt]],
             [[pu + 0.02, pv + 0.1], [pu + 0.02, pv + 1.9], [pu + 0.07, pv + 1.9], [pu + 0.07, pv + 0.1]])
        Cv.append([[q0[0], q0[1], zb - 0.3], [q1[0], q1[1], zb - 0.3], [q1[0], q1[1], zt], [q0[0], q0[1], zt]])
    for i in range(nb + 1):                                            # H-posts
        q = Q[i]
        t = Q[min(i + 1, nb)] - Q[max(i - 1, 0)]
        t = t / max(np.hypot(*t), 1e-6)
        nn = np.array([-t[1], t[0]])
        z0 = Zg[i] - 0.3
        z1 = max(tops[max(i - 1, 0)], tops[min(i, nb - 1)]) + 0.08
        hx, hy = t * 0.06, nn * 0.07
        c = [q + sx * hx + sy * hy for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        vv = ph * min(1.0, (z1 - z0) / 2.4)
        for j in range(4):
            a_, b_ = c[j], c[(j + 1) % 4]
            uu = pu + 0.02 + 0.07 * j
            quad([[a_[0], a_[1], z0], [b_[0], b_[1], z0], [b_[0], b_[1], z1], [a_[0], a_[1], z1]],
                 [[uu, pv], [uu + 0.06, pv], [uu + 0.06, pv + vv], [uu, pv + vv]])
        quad([[c[0][0], c[0][1], z1], [c[1][0], c[1][1], z1], [c[2][0], c[2][1], z1], [c[3][0], c[3][1], z1]],
             [[pu + 0.05, pv + 1.0], [pu + 0.15, pv + 1.0], [pu + 0.15, pv + 1.1], [pu + 0.05, pv + 1.1]])
    T = np.array(Ts)
    lin.buf.add("furniture", "concrete_fence", np.array(Vs, float), np.array(UVs, float), T, src=key)
    CV = np.array(Cv, float).reshape(-1, 3)
    CT = np.array([(4 * k + j[0], 4 * k + j[1], 4 * k + j[2]) for k in range(nb) for j in ((0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2))])
    lin.buf.add("collision", "collision_fence", CV, CV[:, :2], CT, src=key)
    return nb


class PanelPlinthDetail:
    """Furniture-only COLOR_0 contract; no new material, and no changes to Lin/barrier helpers.

    B=64/255, A=128/255 mark our concrete boards. R is a per-bay scan phase;
    G encodes height above the sampled ground + 0.25 m. UNorm8 survives mobile mesh packing.
    Unmarked concrete (gates/noise walls) keeps the old shader path.
    """
    def __init__(self, lin, phase):
        self.lin, self.phase = lin, phase

    def add(self, layer, mat, V, UV, T, **kwargs):
        assert layer == "furniture" and mat == "concrete_plinth"
        V = np.asarray(V, float)
        colors = np.empty((len(V), 4))
        colors[:, 0] = self.phase
        colors[:, 1] = np.clip(V[:, 2] - self.lin.z(V[:, :2]) + 0.25, 0, 1)
        colors[:, 2] = 64 / 255
        colors[:, 3] = 128 / 255
        self.lin.buf.add(layer, mat, V, UV, T, COL=colors, **kwargs)


def panel_fence(lin, line, col, key, flexible=False):
    """ADR0120: standard support spacing, low stepped boards and grade-following mesh.

    Splitting a board on a bank must not create another steel post. The continuous mesh is supported
    at the original <=2.5 m stations; its lower edge sits behind the stepped concrete. Dimensions,
    the occasional 12–25 mm bow and the 8 mm board joints are WORKING_VALUE.
    """
    P = [np.asarray(line.coords[0], float)]
    for a, b in zip(np.asarray(line.coords)[:-1], np.asarray(line.coords)[1:]):
        count = max(1, int(math.ceil(np.linalg.norm(b-a) / S.FENCE_PANEL_W)))
        P.extend(a + (b-a)*j/count for j in range(1, count+1))
    P = np.asarray(P)
    Z = lin.z(P)
    for i, ends in enumerate(zip(P[:-1], P[1:])):
        a, b = ends
        direction = b-a
        length = np.linalg.norm(direction)
        if length < 1e-6:
            continue
        direction /= length
        lateral = np.array([-direction[1], direction[0]])
        boards = [a]

        def split(p, q, depth=0):
            sample = np.array([p, (p+q)/2, q])
            if depth < 10 and np.ptp(lin.z(sample)) > 0.25:
                mid = (p+q)/2
                split(p, mid, depth+1); split(mid, q, depth+1)
            else:
                boards.append(q)

        split(a, b)
        boards = np.asarray(boards)
        ground = lin.z(boards)
        levels = np.maximum(ground[:-1], ground[1:]) + S.FENCE_PLINTH_H
        lowest_concrete = float('inf')
        for j, level in enumerate(levels):
            segment = boards[j:j+2]
            inset = min(0.008, np.linalg.norm(segment[1]-segment[0])*.1)
            board = segment + np.array([direction*inset, -direction*inset])
            low = lin.z(board)-.2
            lowest_concrete = min(lowest_concrete, float(np.min(low)))
            top = np.full(2, level)
            detail = PanelPlinthDetail(lin, (_h(f"{key}:concrete:{i}:{j}") % 256)/255)
            Lin(detail, lin.zsurf).slab("concrete_plinth", board, low, top, .05, key)
            # Closed prefab ends make the small joints readable without a new material.
            for end in (0,1):
                q = board[end]
                v = np.array([[*(q-lateral*.025),low[end]], [*(q+lateral*.025),low[end]],
                              [*(q+lateral*.025),level], [*(q-lateral*.025),level]])
                triangles = [(0,1,2),(0,2,3)] if end else [(0,2,1),(0,3,2)]
                detail.add("furniture", "concrete_plinth", v,
                           np.array([[0,0],[.05,0],[.05,level-low[end]],[0,level-low[end]]]), triangles, src=key)

        stations = np.linalg.norm(boards-a, axis=1)/length
        bottom = np.r_[levels[0], np.minimum(levels[:-1], levels[1:]), levels[-1]]
        seed = _h(f"{key}:bay:{i}")
        bow = (0.012 + (seed % 14) * 0.001) * (1 if seed & 16 else -1)
        if flexible or seed % 4 == 0:
            expanded = np.unique(np.r_[stations, .5])
            bottom = np.interp(expanded, stations, bottom)
            stations = expanded
            offset = np.sin(stations*np.pi)*bow
        else:
            offset = np.zeros(len(stations))
        Q = a + (b-a)*stations[:,None] + lateral*offset[:,None]
        upper = np.interp(stations, [0,1], Z[i:i+2]+S.FENCE_H)
        if flexible:
            upper -= np.sin(stations*np.pi)*.045
        upper = np.maximum(upper, bottom+.4)
        n = len(Q)
        V = np.concatenate([np.column_stack([Q,bottom]), np.column_stack([Q,upper])])
        s = np.r_[0,np.cumsum(np.linalg.norm(np.diff(Q,axis=0),axis=1))]
        # Horizontal wires retain their physical height; the ground does not shear the texture grid.
        UV = np.column_stack([np.tile(s,2),V[:,2]-math.floor(Z[i])])
        T = np.array([(k,k+1,n+k+1) for k in range(n-1)]+[(k,n+k+1,n+k) for k in range(n-1)])
        # Collision retains every original station, independently of render simplification.
        collision = V.copy()
        collision[:n,2] = lin.z(Q)-.1
        lin.buf.add("collision","collision_fence",collision,UV,np.concatenate([T,T[:,[0,2,1]]]),src=key)
        # The concrete/terrain hides the wire's lower boundary. Avoid tessellating the visible
        # wire at every short concrete step, while keeping its world-height UV pattern.
        # Preserve the detailed shape on unusual cross-slopes where this would deepen the bounds.
        indices = ([0,int(np.flatnonzero(np.isclose(stations,.5))[0]),len(Q)-1]
                   if flexible or seed % 4 == 0 else [0,len(Q)-1])
        probe_s = np.linspace(0,1,max(2,int(math.ceil(length/.25))+1))
        probe_q = np.column_stack([np.interp(probe_s,stations[indices],Q[indices,axis]) for axis in (0,1)])
        render_floor = float(min(np.min(ground),np.min(lin.z(probe_q))))-.1
        upper_error = np.max(np.abs(np.interp(stations,stations[indices],upper[indices])-upper))
        # Preserve a raised upper boundary over local terrain humps. Only the flexible mesh's
        # shallow sine-to-chord difference is allowed (under 1 cm, WORKING_VALUE pending renders).
        upper_tolerance = .01 if flexible else 1e-6
        if len(Q) > len(indices) and render_floor >= lowest_concrete and upper_error <= upper_tolerance:
            reduced_q, reduced_top = Q[indices], upper[indices]
            count = len(reduced_q)
            V = np.concatenate([np.column_stack([reduced_q,np.full(count,render_floor)]),
                                np.column_stack([reduced_q,reduced_top])])
            s = np.r_[0,np.cumsum(np.linalg.norm(np.diff(reduced_q,axis=0),axis=1))]
            UV = np.column_stack([np.tile(s,2),V[:,2]-math.floor(Z[i])])
            T = np.array([(k,k+1,count+k+1) for k in range(count-1)]+
                         [(k,count+k+1,count+k) for k in range(count-1)])
        lin.buf.add("furniture",f"{col}_mesh",V,UV,T,src=key)
        lin.buf.add("furniture",f"{col}_mesh",V,UV,T[:,[0,2,1]],src=key)
    lin.posts(col,P,None,.06,.04,S.FENCE_H+.05,zb=Z,src=key,ground_feet=True)


FENCE_COLOURS = ("fence_green", "fence_anthracite", "fence_galv")


def fence_styles(overrides):
    """kind: fence_style -> {osm way id: panel fence colour} (authored: the colour of an OSM fence is not in the data,
    the rule hashes it; ADR 0129)."""
    out = {}
    for o in overrides or []:
        if o.get("kind") != "fence_style":
            continue
        col = f"fence_{o['colour']}"
        if col not in FENCE_COLOURS:
            raise ValueError(f"override {o.get('id')}: fence colour {o['colour']!r}, expected one of "
                             f"{[c[6:] for c in FENCE_COLOURS]}")
        for w in o["osm_way"]:
            out[int(w)] = col
    return out


def fences(lin, src, origin, roads_poly, report, styles=None):
    """styles: {osm way id: colour material} of the authored fence_style overrides (fence_styles)."""
    n = {"panel_m": 0.0, "concrete_m": 0.0, "retaining_m": 0.0}
    styles = styles or {}
    seen = set()
    cutter = roads_poly.buffer(0.3) if roads_poly is not None else None
    for f in src["osm"]["ways"]:
        b = f["tags"].get("barrier")
        if b not in ("fence", "yes", "wall", "retaining_wall") or is_noise_wall(f["tags"]):
            continue                         # noise walls: noise_barriers() (ADR 0069)
        line = LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        key = f"osm:way/{f['osm_way']}:{f['part']}"
        for part in cut_by(line, cutter):
            P = lin.dens(part, 2.0)              # 2 m: the Low terrain band is 2 m, posts sample the ground themselves
            Z = lin.z(P)
            if b in ("fence", "yes"):
                col = FENCE_COLOURS[_h(key) % 3]
                if int(f["osm_way"]) in styles:
                    col = styles[int(f["osm_way"])]
                    seen.add(int(f["osm_way"]))
                panel_fence(lin, part, col, key, flexible=f["tags"].get("fence_type") in ("chain_link", "wire"))
                n["panel_m"] += part.length
            elif b == "wall":
                cc = np.asarray(part.simplify(0.15).coords)            # bays run corner to corner
                for si in range(len(cc) - 1):
                    if np.hypot(*(cc[si + 1] - cc[si])) >= 0.8:
                        n["concrete_bays"] = n.get("concrete_bays", 0) + concrete_fence(
                            lin, LineString([cc[si], cc[si + 1]]), f"{key}:{si}", key)
                n["concrete_m"] += part.length
            else:
                retaining(lin, P, key)
                n["retaining_m"] += part.length
    for f in src["bdot10k"]["OT_BUUO_L"]:
        line = LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        for part in cut_by(line, cutter):
            retaining(lin, lin.dens(part, 1.0), f"bdot:{f['id']}")
            n["retaining_m"] += part.length
    report["fences"] = {k: round(v) for k, v in n.items()}
    if styles:      # a styled way that is no longer in the data is reported, never silently dropped
        report["fences"]["styled_ways"] = sorted(seen)
        report["fences"]["style_stale"] = sorted(set(styles) - seen)


def retaining(lin, P, key):
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    za, zb = lin.z(P + nrm * 2.0), lin.z(P - nrm * 2.0)
    top = np.maximum(za, zb) + 0.15
    bot = np.minimum(za, zb) - 0.4
    top = np.maximum(top, bot + 1.0)
    lin.slab("concrete_wall", P, bot, top, 0.35, key, collision="collision_fence")
    hi = np.where((za > zb)[:, None], nrm, -nrm)
    rail = P + hi * 0.0
    lin.posts("steel_galv", rail, 2.0, 0.05, 0.05, S.RAILING_H, zb=top, src=key + ":railing")
    for zr in (S.RAILING_H - 0.05, 0.55):
        lin.slab("steel_galv", rail, top + zr - 0.03, top + zr + 0.03, 0.05, key + ":railing")


# ADR 0117 (REVIEW s10-0110 P1-1): the W-beam as the folded sheet it is - 310 mm high, 83 mm deep, two flat crests and
# a valley (the "A" guide rail of the SP-05 family; depth/height from the review table, fold positions WORKING_VALUE).
# (offset towards the road from the back plane of the beam, height below its top edge). Every facet has its own
# vertices: the exporter smooths normals inside a part, so shared rows shaded the beam as one tube.
W_PROFILE = ((0.020, 0.0), (0.083, -0.040), (0.083, -0.105), (0.0, -0.155), (0.083, -0.205), (0.083, -0.270),
             (0.020, -0.310))
W_BACK = 0.05               # m: back plane (valley) of the beam in front of the post line P -> crest face at 0.133
#                             (0.13 before: the collision face and the swept-path clearance stay where they were)
POST_FRONT = -0.05          # m: road-side flange of the post behind P; the spacer fills POST_FRONT .. W_BACK (0.10 m)
POST_C = (0.10, 0.055)      # ground post: C / sigma 100 x 55 (web across the road, flanges along it), WORKING_VALUE
POST_C_DECK = (0.12, 0.064)  # deck post (heavier section on a foot plate, Mapillary 454716650857984), WORKING_VALUE
# UV0 of the `barrier_galv` set (4.0 x 0.5 m tile, u along the beam, v = unrolled metres across the profile from the
# bottom edge): posts / spacers / plates sample the plain sheet between the splices
POST_U0 = 1.3
RAIL_DP_M = 0.02            # Douglas-Peucker tolerance of the beams (ADR 0110: 0.01; 0117: 6 facets instead of 4 strips)


def _w_unrolled():
    v = [0.0]
    pr = W_PROFILE[::-1]
    for (o0, z0), (o1, z1) in zip(pr[:-1], pr[1:]):
        v.append(v[-1] + math.hypot(o1 - o0, z1 - z0))
    return v[::-1]            # per W_PROFILE point, top edge first


def _quads(lin, layer, mat, quads, src, both=True):
    """Flat-shaded quad soup: quads = [(4 points CCW seen from the front, 4 uv)]."""
    V, UV, T = [], [], []
    for pts, uv in quads:
        b = len(V)
        V += [np.asarray(q, float) for q in pts]
        UV += list(uv)
        T += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        if both:
            b = len(V)
            V += [np.asarray(q, float) for q in pts]
            UV += list(uv)
            T += [(b, b + 2, b + 1), (b, b + 3, b + 2)]
    if V:
        lin.buf.add(layer, mat, np.array(V), np.array(UV, float), np.array(T), src=src)


def _rail_posts(lin, Q, Zq, Tq, top, deck, key):
    """C posts at Q (n, 2) with the open side downstream, a spacer block between post and beam, and on a deck a foot
    plate. `top` = top of the W-beam above Zq per post; deck posts carry on to BRIDGE_BARRIER_H (upper beam)."""
    quads, flanges = [], []
    dep, fl = POST_C_DECK if deck else POST_C
    f, bk = POST_FRONT, POST_FRONT - dep

    def uv(u0, u1, h):
        h = min(h, 0.44)
        return ((POST_U0 + u0, 0.02), (POST_U0 + u1, 0.02), (POST_U0 + u1, 0.02 + h), (POST_U0 + u0, 0.02 + h))

    def frame(q, t):
        nn = np.array([-t[1], t[0]])                  # towards the road (beam side)
        return lambda o, a, zz: np.append(q + nn * o + t * a, zz)

    for q, z, t, tp in zip(Q, Zq, Tq, top):
        P3 = frame(q, t)
        z0 = z if deck else z - 0.3                    # ground posts are driven in
        z1 = z + (S.BRIDGE_BARRIER_H if deck else tp - 0.03)
        h = z1 - z0
        # road-side flange, web, back flange (thin sheet, drawn from both sides)
        # web from both sides; the flanges only from outside (ADR 0117 budget: 8 triangles per post)
        quads.append(([P3(f, -fl / 2, z0), P3(bk, -fl / 2, z0), P3(bk, -fl / 2, z1), P3(f, -fl / 2, z1)],
                      uv(0.1, 0.1 + dep, h)))
        flanges.append(([P3(f, fl / 2, z0), P3(f, -fl / 2, z0), P3(f, -fl / 2, z1), P3(f, fl / 2, z1)], uv(0.0, fl, h)))
        flanges.append(([P3(bk, -fl / 2, z0), P3(bk, fl / 2, z0), P3(bk, fl / 2, z1), P3(bk, -fl / 2, z1)],
                        uv(0.3, 0.3 + fl, h)))
    _quads(lin, "furniture", POST_MAT, quads, key, both=True)
    solid = flanges
    u = POST_U0 + 0.5
    for q, z, t, tp in zip(Q, Zq, Tq, top):
        P3 = frame(q, t)
        # spacer ("przekladka"): block between the post flange and the valley of the beam; top + the two sides
        a_, zs0, zs1 = 0.045, z + tp - 0.235, z + tp - 0.075
        for sg in (1.0, -1.0):
            pts = [P3(POST_FRONT, sg * a_, zs0), P3(W_BACK, sg * a_, zs0), P3(W_BACK, sg * a_, zs1),
                   P3(POST_FRONT, sg * a_, zs1)]
            solid.append((pts if sg > 0 else pts[::-1], ((u, 0.20), (u + 0.1, 0.20), (u + 0.1, 0.36), (u, 0.36))))
        # ADR 0144 (REVIEW s14-0123 P1-1): no foot plate under a deck post - the up-facing galvanised quad mirrored
        # the sky and read as a white square on the cap / paving (p0_kerb_merge_eye); 2 triangles per post saved
    _quads(lin, "furniture", POST_MAT, solid, key, both=False)


def _stations(P, Z, top, spacing, lo, hi):
    """Post stations every ~`spacing` along P[lo:hi + 1] (both ends included): points, foot z, tangents, beam top."""
    Pp = P[lo:hi + 1]
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Pp, axis=0).T))])
    L = float(s[-1])
    n = max(1, int(round(L / spacing)))
    u = np.linspace(0.0, L, n + 1)
    Q = np.column_stack([np.interp(u, s, Pp[:, 0]), np.interp(u, s, Pp[:, 1])])
    d = np.gradient(Pp, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    Tq = np.column_stack([np.interp(u, s, d[:, 0]), np.interp(u, s, d[:, 1])])
    Tq /= np.maximum(np.hypot(Tq[:, 0], Tq[:, 1]), 1e-9)[:, None]
    return Q, np.interp(u, s, Z[lo:hi + 1]), Tq, np.interp(u, s, top[lo:hi + 1])


def guardrail(lin, P, Z, key, tall=None, term=(False, False), term_tall=(False, False)):
    """Steel W-beam on posts (top GUARDRAIL_H), Z = ground/surface height along P (points ~1 m apart). P is the post
    line; the road is on its LEFT normal side (beam face W_BACK + 0.083 in front of it).

    ADR 0110: `tall` (bool per point) = deck barrier of the Andersa viaducts. `term` = (start, end): the beam is
    turned down to the ground over GUARDRAIL_TERMINAL_M at that end (a free end on the ground).
    ADR 0117: folded W profile with hard arrises (W_PROFILE), C posts with a spacer behind the beam (the beam hangs on
    the face of the post, not on its top), ground posts every GUARDRAIL_POST_SPACING_GROUND; deck runs: heavier posts
    on foot plates every GUARDRAIL_POST_SPACING with a box beam above the W-beam (Mapillary 454716650857984: low
    W-beam + upper beam on short posts; the handrail with horizontal bars at the deck edge is a separate railing -
    hero asset / roads.meshing.build_bridge_extras).
    ADR 0144: `term_tall` = (start, end): that end of a DECK run is free (no other rail carries on from it,
    _mark_free_deck_ends) - it is turned down like a ground end instead of stopping in the air."""
    n = len(P)
    tall = np.zeros(n, bool) if tall is None else np.asarray(tall, bool)
    first = len(lin.buf.parts)
    top = np.full(n, S.GUARDRAIL_H)
    tl = int(S.GUARDRAIL_TERMINAL_M)
    lo, hi = 0, n
    if n > 2 * tl + 4:
        if term[0] and (term_tall[0] or not tall[:tl + 1].any()):
            top[:tl + 1] = np.linspace(0.33, S.GUARDRAIL_H, tl + 1)
            lo = tl
        if term[1] and (term_tall[1] or not tall[-tl - 1:].any()):
            top[-tl - 1:] = np.linspace(S.GUARDRAIL_H, 0.33, tl + 1)
            hi = n - tl
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    s_all = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    # posts: one family per run of low / tall points (shared boundary point belongs to the tall run)
    k = lo
    while k < hi:
        kk = k
        while kk + 1 < hi and tall[kk + 1] == tall[k]:
            kk += 1
        if kk > k:
            deck = bool(tall[k])
            Q, Zq, Tq, tq = _stations(P, Z, top, S.GUARDRAIL_POST_SPACING if deck else S.GUARDRAIL_POST_SPACING_GROUND,
                                      k, kk)
            if not deck and k > lo and tall[k - 1]:
                Q, Zq, Tq, tq = Q[1:], Zq[1:], Tq[1:], tq[1:]          # the boundary post is the deck post
            if len(Q):
                _rail_posts(lin, Q, Zq, Tq, tq, deck, key)
            if deck:
                # upper box beam (100 x 80) on the road face of the posts; at an end where the W-beam carries on
                # along the ground it slopes down behind the W-beam over 2 m instead of stopping in the air
                zt = np.full(kk - k + 1, S.BRIDGE_BARRIER_H)
                if kk - k >= 6:                       # every end (also a run end: no beam stopping in the air)
                    zt[:3] = np.linspace(S.GUARDRAIL_H - 0.02, S.BRIDGE_BARRIER_H, 3)
                    zt[-3:] = np.linspace(S.BRIDGE_BARRIER_H, S.GUARDRAIL_H - 0.02, 3)
                kp = dp_keep(np.column_stack([P[k:kk + 1], Z[k:kk + 1] + zt]), RAIL_DP_M)
                Pt, zz, nt, st = P[k:kk + 1][kp], (Z[k:kk + 1] + zt)[kp], nrm[k:kk + 1][kp], s_all[k:kk + 1][kp]
                box = ((POST_FRONT, 0.0), (POST_FRONT + 0.08, 0.0), (POST_FRONT + 0.08, -0.10), (POST_FRONT, -0.10))
                uvv = (0.40, 0.46, 0.34, 0.42)
                for (o0, z0), (o1, z1), v0 in list(zip(box, box[1:] + box[:1], uvv))[:2] + [(box[3], box[0], uvv[3])]:
                    A = np.column_stack([Pt + nt * o0, zz + z0])
                    B = np.column_stack([Pt + nt * o1, zz + z1])
                    m_ = len(Pt)
                    V = np.concatenate([A, B])
                    UV = np.column_stack([np.tile(st, 2), np.repeat([v0, v0 + 0.06], m_)])
                    T = [(i, i + 1, m_ + i + 1) for i in range(m_ - 1)] + [(i, m_ + i + 1, m_ + i) for i in range(m_ - 1)]
                    lin.buf.add("furniture", "barrier_steel", V, UV, np.array(T), src=key)
        k = kk + 1
    # ADR 0110: the beam keeps only the points a 1 cm Douglas-Peucker needs (it was meshed every metre: 16 triangles
    # per metre also on straights; the posts above keep their spacing)
    kp = dp_keep(np.column_stack([P, Z + top]), RAIL_DP_M)
    P, Z, top, nrm, s = P[kp], Z[kp], top[kp], nrm[kp], s_all[kp]
    n = len(P)
    vv = _w_unrolled()
    rows, uvr = [], []
    for (o0, z0), (o1, z1), v0, v1 in zip(W_PROFILE[:-1], W_PROFILE[1:], vv[:-1], vv[1:]):
        rows.append(np.column_stack([P + nrm * (W_BACK + o0), Z + top + z0]))
        rows.append(np.column_stack([P + nrm * (W_BACK + o1), Z + top + z1]))
        uvr += [v0, v1]
    V = np.concatenate(rows)
    UV = np.column_stack([np.tile(s, len(rows)), np.repeat(uvr, n)])
    T = []
    for r in range(0, len(rows), 2):
        a, b = r * n, (r + 1) * n
        T += [(a + k, a + k + 1, b + k + 1) for k in range(n - 1)] + [(a + k, b + k + 1, b + k) for k in range(n - 1)]
    T = np.array(T)
    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    # back of the sheet: two facets (top edge - valley - bottom edge); the folds are a road-side thing (budget)
    bi = [0, 5, 6, 11]
    Vb = np.concatenate([rows[i] for i in bi])
    UVb = np.column_stack([np.tile(s, 4), np.repeat([uvr[i] for i in bi], n)])
    Tb = []
    for r in (0, 2):
        a, b = r * n, (r + 1) * n
        Tb += [(a + k, b + k + 1, a + k + 1) for k in range(n - 1)] + [(a + k, b + k, b + k + 1) for k in range(n - 1)]
    lin.buf.add("furniture", "barrier_steel", Vb, UVb, np.array(Tb), src=key)
    if tall.any() or key.endswith(":structure"):
        # ADR 0110: a run on a deck, and a run beside a viaduct, belong to the bridge mesh of their chunk (drawn with
        # the deck; one barrier_steel primitive for both), not to the furniture mesh (fences, hedges: its bounds grew
        # by the viaduct and 8 more draws entered frames beside it)
        for prt in lin.buf.parts[first:]:
            if prt.layer == "furniture":
                prt.layer = "bridge"
    # collision: the road face of the beam only (top edge - crests - bottom edge), where it was before ADR 0117
    cr = [0, 1, 3, 7, 9, 11]
    Vc = np.concatenate([rows[i] for i in cr])
    Tc = []
    for r in range(len(cr) - 1):
        a, b = r * n, (r + 1) * n
        Tc += [(a + k, a + k + 1, b + k + 1) for k in range(n - 1)] + [(a + k, b + k + 1, b + k) for k in range(n - 1)]
    Tc = np.array(Tc)
    lin.buf.add("collision", "collision_steel", Vc, Vc[:, :2], np.concatenate([Tc, Tc[:, [0, 2, 1]]]), src=key)


# ADR 0110: posts share the material of the beam (galvanised steel both): one draw call per furniture chunk instead of two
# (the decks of the hero viaduct got barriers in three chunks that had none; draw budget of the A16)
POST_MAT = "barrier_steel"
GUARDRAIL_DEDUP_M = 1.0     # ADR 0100 (REVIEW s10-0095 P1-10): a run within this of an already built rail is not built twice
GUARDRAIL_DEDUP_GROUND_M = 2.5   # ADR 0110 (REVIEW s10-0100 P1-6): ground runs - one rail per separator also when the
#                                  two edges that want it are 1-2.5 m apart (decks keep 1 m: two decks, two rails)
GUARDRAIL_MIN_RUN = 8       # points (1 m apart) of a run left after the dedup; shorter leftovers are dropped


RAIL_DIP_M = 8             # ADR 0144: points (1 m) - a dip of an authored rail shorter than this is bridged
RAIL_DIP_MIN = 0.25         # ... when it is deeper than this below the line between its shoulders


def _bridge_dips(Z):
    """Foot heights with short dips (< RAIL_DIP_M points, > RAIL_DIP_MIN deep) replaced by the straight line between
    their shoulders; a dip at an end of the run is levelled to its one shoulder."""
    Z = np.asarray(Z, float).copy()
    n = len(Z)
    i = 0
    while i < n:
        best = None
        for j in range(min(n - 1, i + RAIL_DIP_M), i + 1, -1):
            line = np.linspace(Z[i], Z[j], j - i + 1)
            if (line[1:-1] - Z[i + 1:j] > RAIL_DIP_MIN).any() and (Z[i + 1:j] <= line[1:-1] + 1e-9).all():
                best = (j, line)
                break
        if best:
            Z[i:best[0] + 1] = best[1]
            i = best[0]
        else:
            i += 1
    h = RAIL_DIP_M // 2
    if n > 2 * RAIL_DIP_M:          # ends: a sudden drop over the last / first few points of a run that was level before
        if (Z[n - h - 1] - Z[n - h:] > RAIL_DIP_MIN).any() and abs(Z[n - h - 1] - Z[n - 2 * h - 1]) < 0.15:
            Z[n - h:] = np.maximum(Z[n - h:], Z[n - h - 1])
        if (Z[h] - Z[:h] > RAIL_DIP_MIN).any() and abs(Z[h] - Z[2 * h]) < 0.15:
            Z[:h] = np.maximum(Z[:h], Z[h])
    return Z


GUARDRAIL_JOIN_M = 4.0      # ADR 0117: a run cut by the dedup is led onto the rail that cut it when that is this close
GUARDRAIL_JOIN_BLEND = 8    # points (1 m) over which the cut end swings onto the other rail


def _dedup_guardrail(lin, P, Z, key, built, m, tall=None, term=(True, True)):
    """Build the parts of run P that are not within the dedup distance of a rail built before (two chains / a chain
    and an authored rail on the same separator crossed and overlapped at E -782 and on the viaduct approaches).

    ADR 0117 (REVIEW s10-0110 P1-6, p0_kerb_merge_eye): a cut end used to stop in the air beside the other rail,
    which itself dived into the ground 2 m further (two runs at two angles, two posts side by side). Now the cut
    end swings onto the nearest point of the rail that cut it (GUARDRAIL_JOIN_M) and, when runs are queued
    (`lin.rail_queue`, guardrails()), the end of that rail it lands on loses its turned-down terminal: one rail."""
    from shapely.geometry import LineString, Point
    from shapely.ops import nearest_points
    P = np.array(P, float)
    keep = np.ones(len(P), bool)
    tall = np.zeros(len(P), bool) if tall is None else np.asarray(tall, bool)
    allb = None
    if built:
        near = shapely.union_all([b.buffer(GUARDRAIL_DEDUP_M) for b in built])
        far = shapely.union_all([b.buffer(GUARDRAIL_DEDUP_GROUND_M) for b in built])
        allb = shapely.union_all(built)
        shapely.prepare(near)
        shapely.prepare(far)
        keep = ~np.where(tall, shapely.contains_xy(near, P[:, 0], P[:, 1]), shapely.contains_xy(far, P[:, 0], P[:, 1]))
    queue = getattr(lin, "rail_queue", None)

    def join(Ps, end):
        """Swing end `end` (0 / -1) of segment Ps onto the rail that cut it; True when joined."""
        q = nearest_points(allb, Point(Ps[end]))[0]
        q = np.array([q.x, q.y])
        dv = q - Ps[end]
        if float(np.hypot(*dv)) > GUARDRAIL_JOIN_M or len(Ps) < GUARDRAIL_JOIN_BLEND + 2:
            return False
        u = np.linspace(1.0, 0.0, GUARDRAIL_JOIN_BLEND + 1)[:-1]
        w = u * u * (3 - 2 * u)
        idx = np.arange(GUARDRAIL_JOIN_BLEND) if end == 0 else len(Ps) - 1 - np.arange(GUARDRAIL_JOIN_BLEND)
        Ps[idx] += dv[None, :] * w[:, None]
        m["joined_ends"] = m.get("joined_ends", 0) + 1
        if queue:
            for it in queue:                       # the rail it lands on: no turned-down terminal at that end
                for e_ in (0, -1):
                    if float(np.hypot(*(it["P"][e_] - q))) < 6.0:
                        t_ = list(it["term"])
                        t_[e_] = False
                        it["term"] = tuple(t_)
        return True

    k = 0
    while k < len(P):
        if not keep[k]:
            k += 1
            continue
        kk = k
        while kk + 1 < len(P) and keep[kk + 1]:
            kk += 1
        if kk - k + 1 >= GUARDRAIL_MIN_RUN:
            Ps = P[k:kk + 1].copy()
            # a cut made by the dedup is not a free end (the other rail carries on there)
            t0, t1 = term[0] and k == 0, term[1] and kk == len(P) - 1
            if allb is not None:
                if k > 0:
                    join(Ps, 0)
                if kk < len(P) - 1:
                    join(Ps, -1)
            it = {"P": Ps, "Z": Z[k:kk + 1], "key": key, "tall": tall[k:kk + 1], "term": (t0, t1)}
            if queue is not None:
                queue.append(it)
            else:
                guardrail(lin, it["P"], it["Z"], key, it["tall"], it["term"])
            built.append(LineString(Ps))
        else:
            m["dedup_dropped_pts"] = m.get("dedup_dropped_pts", 0) + (kk - k + 1)
        k = kk + 1
    m["dedup_skipped_pts"] = m.get("dedup_skipped_pts", 0) + int((~keep).sum())


def _join_free_ends(queue, m):
    """ADR 0117 (p0_kerb_merge_eye): an end of a run that stops within GUARDRAIL_JOIN_M of ANOTHER rail (a deck
    barrier starting 2 m beside the separator rail of the gore, two rails of one nose) swings onto it: the rails meet
    in a V / Y as on the orthophoto (E -781 N 76.5) instead of ending side by side. The end loses its terminal."""
    from shapely.geometry import LineString, Point
    from shapely.ops import nearest_points
    lines = [LineString(it["P"]) for it in queue]
    for i, it in enumerate(queue):
        Ps = it["P"]
        if len(Ps) < GUARDRAIL_JOIN_BLEND + 4:
            continue
        for end in (0, -1):
            # ADR 0123 (p0_kerb_merge_eye): the end of a DECK barrier stays on its cap - the barrier of the ramp deck
            # (E -750 N 77.4) was swung 2.5 m across the gap onto the barrier of the DK8 deck beside it (zigzag, a post
            # left alone, a beam end in the air). Ground rails still come to it.
            if it["tall"] is not None and bool(np.asarray(it["tall"])[end]):
                continue
            if end in it.get("nojoin", ()):
                continue
            pe = Point(Ps[end])
            # rails at the same level only (a deck rail passes over a ground rail without meeting it)
            others = []
            for j, l in enumerate(lines):
                if j == i or l.distance(pe) > GUARDRAIL_JOIN_M:
                    continue
                Pj = queue[j]["P"]
                kj = int(np.argmin(np.hypot(Pj[:, 0] - Ps[end][0], Pj[:, 1] - Ps[end][1])))
                if abs(float(queue[j]["Z"][kj]) - float(it["Z"][end])) < 1.0:
                    others.append(l)
            if not others:
                continue
            allb = shapely.union_all(others)
            d = allb.distance(pe)
            if not (0.3 < d <= GUARDRAIL_JOIN_M):
                continue
            q = nearest_points(allb, pe)[0]
            dv = np.array([q.x, q.y]) - Ps[end]
            u = np.linspace(1.0, 0.0, GUARDRAIL_JOIN_BLEND + 1)[:-1]
            w = u * u * (3 - 2 * u)
            idx = np.arange(GUARDRAIL_JOIN_BLEND) if end == 0 else len(Ps) - 1 - np.arange(GUARDRAIL_JOIN_BLEND)
            Ps[idx] += dv[None, :] * w[:, None]
            t_ = list(it["term"])
            t_[end] = False
            it["term"] = tuple(t_)
            m["joined_free_ends"] = m.get("joined_free_ends", 0) + 1
        lines[i] = LineString(Ps)


RAIL_CONTINUE_M = 2.5       # ADR 0144: a deck run end with another rail end this close (and within RAIL_CONTINUE_DZ) carries on
RAIL_CONTINUE_DZ = 0.8


def _mark_free_deck_ends(queue, m=None):
    """ADR 0144 (REVIEW s14-0123 P1-1, "koniec tasmy wisi bez zakonczenia"): it["term_tall"] = (start, end), True where
    a DECK end of a run has no other rail end within RAIL_CONTINUE_M at its level - that end gets a turned-down
    terminal. Ends that another run continues (next chain of the same deck, a ground rail led onto it) stay as they
    are, as do ends whose terminal was cancelled (authored `free_ends`, joins)."""
    ends = []
    for i, it in enumerate(queue):
        for e_ in (0, -1):
            ends.append((i, np.asarray(it["P"][e_], float), float(it["Z"][e_])))
    for i, it in enumerate(queue):
        tl = it.get("tall")
        flags = []
        for e_ in (0, -1):
            free = False
            if tl is not None and len(tl) and bool(np.asarray(tl)[e_]) and it["term"][0 if e_ == 0 else 1]:
                p, z = np.asarray(it["P"][e_], float), float(it["Z"][e_])
                free = not any(j != i and float(np.hypot(*(q - p))) <= RAIL_CONTINUE_M and abs(zq - z) <= RAIL_CONTINUE_DZ
                               for j, q, zq in ends)
            flags.append(free)
        it["term_tall"] = tuple(flags)
        if m is not None:
            m["deck_free_ends"] = m.get("deck_free_ends", 0) + int(sum(flags))


def _flush_rails(lin, m=None):
    queue = getattr(lin, "rail_queue", None) or []
    if queue and m is not None:
        _join_free_ends(queue, m)
    _mark_free_deck_ends(queue, m)
    for it in queue:
        guardrail(lin, it["P"], it["Z"], it["key"], it["tall"], it["term"], it.get("term_tall", (False, False)))
    lin.rail_queue = None
    lin.rail_runs = [{"key": it["key"], "P": np.asarray(it["P"], float), "Z": np.asarray(it["Z"], float),
                      "tall": np.zeros(len(it["P"]), bool) if it["tall"] is None else np.asarray(it["tall"], bool),
                      "term": tuple(it["term"]), "term_tall": tuple(it.get("term_tall", (False, False)))} for it in queue]
    return [bool(np.all(it["tall"])) for it in queue]


PARAPET_BARRIER_MIN_M = 1.0   # ADR 0144: no generic deck balustrade within this of a road barrier (W-beam + upper beam)


def drop_parapets_at_barriers(buf, runs, m=None):
    """ADR 0144 (REVIEW s14-0123 P1-1): the generic balustrade of a deck edge (roads.meshing.build_bridge_extras, src
    "<chain>:parapet", 0.15 m in from the cap edge) and the road barrier of the same cap (posts 0.2-0.4 m in from that
    edge) are two rail systems 0.1-0.3 m apart: on p0_kerb_merge_eye the W-beam ran through the balustrade posts for
    ~10 m. One system per edge: where a deck barrier (W-beam + upper box beam at BRIDGE_BARRIER_H - a barrier-railing)
    runs within PARAPET_BARRIER_MIN_M, the balustrade triangles are dropped. Hero viaducts carry their authored
    railing in the asset (measured off photos, e.g. Mapillary 454716650857984) and are not touched. Returns the
    number of triangles removed."""
    from scipy.spatial import cKDTree
    pts = []
    for r in runs:
        tl = np.asarray(r["tall"], bool)
        if tl.sum() < 2:
            continue
        P3 = np.column_stack([r["P"], r["Z"]])[tl]
        # runs are sampled every ~1 m: densify to 0.25 m so the distance to the polyline is right to a few cm
        u = np.linspace(0.0, len(P3) - 1.0, 4 * (len(P3) - 1) + 1)
        pts.append(np.column_stack([np.interp(u, np.arange(len(P3)), P3[:, d]) for d in range(3)]))
    if not pts:
        return 0
    A = np.concatenate(pts)
    tree = cKDTree(A[:, :2])
    removed = 0
    for p in buf.parts:
        if p.layer != "bridge" or not p.src.endswith(":parapet") or not len(p.T):
            continue
        cen = p.V[p.T].mean(1)
        d, k = tree.query(cen[:, :2])
        near = (d < PARAPET_BARRIER_MIN_M) & (np.abs(cen[:, 2] - A[k, 2]) < 2.5)
        if near.any():
            removed += int(near.sum())
            p.T = p.T[~near]
    if m is not None:
        m["parapet_tris_dropped"] = removed
    return removed


STRUCT_GUARD_GAP_M = 8.0     # WORKING_VALUE (ADR 0110): a ground carriageway edge this close to a viaduct / walled ramp
STRUCT_GUARD_MIN_H = 1.0     # ... standing at least this high above it gets a barrier on that side


def _structures(net):
    """[(chain id, deck polygon, KD-tree of deck axis points, their heights)] of bridges and walled ramps."""
    from scipy.spatial import cKDTree
    from shapely.geometry import LineString
    out = []
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        msk = np.asarray(c.bridge, bool).copy()
        wl = c.meta.get("walled")
        if wl is not None:
            msk |= np.asarray(wl, bool)
        idx = np.where(msk)[0]
        if len(idx) < 3:
            continue
        for run in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1):
            if len(run) < 3:
                continue
            pts = c.line.p[run]
            half = float(np.max(c.hw[run])) + S.KERB_TOP_W + bridge_cap_w(c)
            out.append((c.id, LineString(pts).buffer(half, cap_style="flat"), cKDTree(pts),
                        np.asarray(c.crossfall_z(c.line.s[run], 0.0), float)))
    return out


def _beside_structure(c, ss, sgn, hw, zg, structs):
    """Stations of chain c whose edge on side sgn runs beside (not under) a viaduct / walled ramp of another chain."""
    E = c.line.offset_point(ss, sgn * (hw + 0.75))
    Eo = c.line.offset_point(ss, sgn * (hw + 4.75))
    res = np.zeros(len(ss), bool)
    lo, hi = E.min(0) - 15.0, E.max(0) + 15.0
    for cid, poly, tree, z in structs:
        if cid == c.id:
            continue
        b = poly.bounds
        if b[0] > hi[0] or b[2] < lo[0] or b[1] > hi[1] or b[3] < lo[1]:
            continue
        d0 = shapely.distance(poly, shapely.points(E))
        d1 = shapely.distance(poly, shapely.points(Eo))
        cand = (d0 > 1.0) & (d0 < STRUCT_GUARD_GAP_M) & (d1 < d0 - 1.0)
        if not cand.any():
            continue
        _, k = tree.query(E[cand])
        ok = z[k] - zg[cand] > STRUCT_GUARD_MIN_H
        res[np.where(cand)[0][ok]] = True
    return res


def guardrails(lin, net, zground, report):
    from scipy import ndimage
    m = {"bridge": 0.0, "median": 0.0, "embankment": 0.0, "structure": 0.0}
    names = ["", "bridge", "median", "embankment", "structure"]
    built = []
    drops, runs = [], []
    structs = _structures(net)
    # ADR 0117: authored rails are built FIRST (they are traced; the rule runs give way and join them); runs are
    # queued so that a later join can still cancel the turned-down terminal of the rail it lands on
    lin.rail_queue = []
    # ADR 0100: authored guardrails on kerbed separators traced on the orthophoto (`kind: guardrail`, polyline_en in
    # region-local E/N, drawn with the road on the RIGHT of the drawing direction = the face of the W-beam)
    m["authored"] = 0.0
    surf_top = None
    for o in getattr(net, "authored", None) or []:
        if o.get("kind") != "guardrail":
            continue
        Q = np.asarray(o.get("polyline_en") or [], float)
        if Q.ndim != 2 or len(Q) < 2:
            net.overrides_stale.append(o["id"])
            continue
        sq = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
        u = np.linspace(0.0, sq[-1], max(2, int(np.ceil(sq[-1])) + 1))
        P = np.column_stack([np.interp(u, sq, Q[:, 0]), np.interp(u, sq, Q[:, 1])])
        Z = lin.z(P)
        if not np.isfinite(Z).all():
            net.overrides_stale.append(o["id"])
            continue
        # ADR 0144: an authored rail stands on the exact top of the surface under it (island paving, kerb top), not on
        # the 1 m raster that blends an island top with the carriageway beside it (the rails of dk8-ramp-split-island
        # stood 0.65 m into the paving: beam top 0.10 m above it), and it does not dive into a short dip of the ground
        # (the 3 m of grass between the island end and the deck joint: the beam end hung 0.75 m low beside the deck
        # barrier it leads to) - dips shorter than RAIL_DIP_M are bridged at the height of their shoulders.
        if surf_top is None:
            surf_top = SurfaceTop(lin.buf.parts)
        zt = np.array([surf_top.top(float(e_), float(n_)) for e_, n_ in P])
        Z = np.where(np.isfinite(zt), np.maximum(Z, zt), Z)
        Z = _bridge_dips(Z)
        # ADR 0123: authored rails are not deduplicated against each other (two traced rails of one separator, 1.5 m
        # apart: the second was cut away by the 2.5 m ground rule) - only the rule runs give way to them
        own = []
        _dedup_guardrail(lin, P, Z, f"authored:{o['id']}", own, m)
        # ADR 0123 b4: `free_ends: [start, end]` (drawing order), False = that end stays where it was traced, without
        # a turned-down terminal (the east end of dk8-ramp-split-barrier-n stops at the expansion joint of the ramp
        # deck: _join_free_ends swung its last 8 m onto the OTHER rail of the separator, 1.4 m away)
        fe = o.get("free_ends")
        mine = [it for it in lin.rail_queue if it["key"] == f"authored:{o['id']}"]
        if fe and mine:
            for it, e_, keep_ in ((mine[0], 0, fe[0]), (mine[-1], -1, fe[1])):
                if not keep_:
                    it.setdefault("nojoin", set()).add(e_)
                    t_ = list(it["term"])
                    t_[e_] = False
                    it["term"] = tuple(t_)
        built.extend(own)
        net.overrides_applied.append({"id": o["id"], "targets": [f"guardrail@{P[0][0]:.0f},{P[0][1]:.0f}"]})
        m["authored"] += float(sq[-1])
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        s0, s1 = c.t_a, c.length - c.t_b
        if s1 - s0 < 10:
            continue
        ss = np.arange(s0, s1, 1.0)
        hw = c.hw_at(ss)
        br = c.bridge[c.idx(ss)]
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            prm = [side_params(c, side, s) for s in ss]
            kinds = np.array([p[0] for p in prm])
            kh = np.array([p[1] for p in prm])
            kw = np.array([p[2] for p in prm])
            kmat = np.array([p[4] for p in prm])
            ext = np.array([side_extent(*p) for p in prm])
            zg = c.crossfall_z(ss, sgn * hw)
            want = np.zeros(len(ss), int)            # 1 bridge, 2 median, 3 embankment, 4 beside a structure
            off = np.zeros(len(ss))
            zb = zg.copy()
            # bridges: barrier-railing on the cap, BRIDGE_BARRIER_EDGE_M in from its outer edge (ADR 0110: the
            # orthophoto of the Biezenstwa decks has it 0.2-0.4 m from the deck edge, 0.8-1.0 m behind the kerb)
            want[br] = 1
            # ADR 0117: the post line keeps BRIDGE_BARRIER_EDGE_M to the cap edge on a 1.5 m cap; on a narrower cap
            # (bridge_style cap_w, Biezenstwa 1.0 m) the beam face stands BRIDGE_BARRIER_FACE_M behind the kerb face
            # (Mapillary 454716650857984: edge line -> face ~1.25 m, kerb -> face ~0.7 m) but never closer than
            # BRIDGE_BARRIER_EDGE_MIN_M to the cap edge
            # ADR 0123: on a narrow cap the face distance rules (0.42 m: the post line may stand further than
            # BRIDGE_BARRIER_EDGE_M from the cap edge); the 1.5 m caps keep BRIDGE_BARRIER_EDGE_M as before
            edge = kw[br] + S.KERB_TOP_W - (S.BRIDGE_BARRIER_FACE_M + W_BACK + 0.083)
            edge = np.where(kw[br] < 1.3, np.maximum(edge, S.BRIDGE_BARRIER_EDGE_MIN_M),
                            np.clip(edge, S.BRIDGE_BARRIER_EDGE_MIN_M, S.BRIDGE_BARRIER_EDGE_M))
            off[br] = hw[br] + S.KERB_TOP_W + kw[br] - edge
            zb[br] = zg[br] + S.BRIDGE_KERB_H
            med = (kinds == MEDIAN_RURAL) & ~br
            want[med] = 2
            off[med] = hw[med] + S.PAVED_SHOULDER_MEDIAN + S.GUARDRAIL_OFFSET
            zb[med] = zg[med] - 0.02
            rur = (kinds == RURAL) & ~br
            drop = np.full(len(ss), -1e9)
            if rur.any():
                # embankment height = road edge minus the ground at the toe of the fill slope: berm 1 m +
                # slope 1:1.5 of a 2 m fill + 1 m = profile end + 5 m (the old probe at +2 m only ever saw
                # the berm, so the rule never fired); take the lowest of three probes (5, 7, 9 m)
                for extra in (5.0, 7.0, 9.0):          # zground = natural ground (NMT), not the conformed terrain
                    P_out = c.line.offset_point(ss, sgn * (hw + ext + extra))
                    drop = np.maximum(drop, zg - zground(P_out[:, 0], P_out[:, 1]))
                drops.append(float(drop[rur].max()))
                emb = rur & (drop > S.GUARDRAIL_EMBANKMENT_H)
                # extend 12 m each way (approach), close small gaps
                emb = ndimage.binary_dilation(emb, iterations=12) & rur
                want[emb] = 3
                off[emb] = hw[emb] + S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET
                zb[emb] = zg[emb] - S.CROSSFALL * S.PAVED_SHOULDER
            # ADR 0110 (gate-3 side-by-side #4b): W-beam along a ground carriageway that runs beside a viaduct or a
            # walled ramp, on the side facing it (Mapillary 500263111404933, 1259231227807789, 751431972202262: the
            # links at Rondo Biezenstwa). Rural edge: behind the paved shoulder; kerbed edge without a sidewalk:
            # GUARDRAIL_OFFSET behind the kerb. WORKING rule.
            if structs:
                kerbed = (kinds == URBAN) & (kw < 0.05) & (kh > 0.05) & (kmat == 0)
                bs = _beside_structure(c, ss, sgn, hw, zg, structs) & (want == 0) & ~br & (rur | kerbed)
                bs = ndimage.binary_closing(bs, iterations=6) & (want == 0) & ~br & (rur | kerbed)
                want[bs] = 4
                off[bs] = np.where(rur[bs], hw[bs] + S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET,
                                   hw[bs] + S.KERB_TOP_W + S.GUARDRAIL_OFFSET)
                zb[bs] = np.where(rur[bs], zg[bs] - S.CROSSFALL * S.PAVED_SHOULDER, zg[bs] + kh[bs])
            # runs: ONE rail per contiguous stretch that wants a barrier, whatever the rule (ADR 0110: the bridge
            # rail, the approach embankment rail and the median rail were separate runs at different offsets and
            # crossed / doubled where they met, REVIEW s10-0100 P1-6); the offset and the foot height blend over 9 m
            k = 0
            while k < len(ss):
                if want[k] == 0:
                    k += 1
                    continue
                kk = k
                while kk + 1 < len(ss) and want[kk + 1] != 0:
                    kk += 1
                if kk - k >= 8:
                    sl = slice(k, kk + 1)
                    o_, z_ = off[sl].copy(), zb[sl].copy()
                    if len(set(want[sl].tolist())) > 1:
                        o_ = ndimage.uniform_filter1d(o_, 9, mode="nearest")
                        z_ = ndimage.uniform_filter1d(z_, 9, mode="nearest")
                    elif len(o_) > 5 and float(np.abs(np.diff(o_)).max()) > 0.2:
                        # ADR 0144 (p0_kerb_merge_eye): one rule, but the cap width steps between two stations (deck stub
                        # at a junction mouth) - the post line jumped 0.5 m sideways within 1 m (zigzag); eased over 5 m
                        o_ = ndimage.uniform_filter1d(o_, 5, mode="nearest")
                    P = c.line.offset_point(ss[sl], sgn * o_)
                    tall = want[sl] == 1
                    if sgn > 0:                          # beam faces the road: road is on the right of travel
                        P, z_, tall = P[::-1], z_[::-1], tall[::-1]
                    kind = names[int(np.bincount(want[sl]).argmax())]
                    _dedup_guardrail(lin, P, z_, f"{c.id}:{side}:{kind}", built, m, tall)
                    w3 = want[sl] == 3
                    if w3.any():
                        runs.append({"chain": c.id, "side": side, "s": [round(float(ss[k]), 1), round(float(ss[kk]), 1)],
                                     "max_drop_m": round(float(drop[sl][w3].max()), 2),
                                     "at": [round(float(v), 1) for v in c.line.offset_point(ss[(k + kk) // 2], 0.0)]})
                    for q in (1, 2, 3, 4):
                        m[names[q]] += float((want[sl] == q).sum())
                k = kk + 1
    deck_flags = _flush_rails(lin, m)
    drop_parapets_at_barriers(lin.buf, lin.rail_runs, m)
    report["guardrails_m"] = {k: round(v) for k, v in m.items()}
    # ADR 0144: every built run (1 m points: E, N, foot z, deck flag) for tests/gis/test_guardrail_overlap.py
    report["guardrail_runs"] = [{"key": r["key"], "term": [bool(x) for x in r["term"]],
                                 "term_tall": [bool(x) for x in r["term_tall"]],
                                 "pts": [[round(float(a), 2), round(float(b), 2), round(float(z_), 2), int(t_)]
                                         for (a, b), z_, t_ in zip(r["P"], r["Z"], r["tall"])]} for r in lin.rail_runs]
    # pier_guardrails (after the bridge supports exist) dedups against the GROUND rails (deck rails pass overhead)
    net.guardrail_built = [b for b, dk in zip(built, deck_flags) if not dk] if len(deck_flags) == len(built) else built
    d = np.array(drops) if drops else np.zeros(1)
    report["embankment_check"] = {"rural_sides": len(drops), "max_drop_m": round(float(d.max()), 2),
                                  "p95_drop_m": round(float(np.percentile(d, 95)), 2),
                                  "threshold_m": S.GUARDRAIL_EMBANKMENT_H, "runs": runs,
                                  "ground": "NMT (decks removed) at the profile end + 5 / 7 / 9 m"}


PIER_GUARD_GAP_M = 4.5       # WORKING_VALUE (ADR 0117, REVIEW s10-0110 P1-7): pier axis this close to a carriageway edge
PIER_GUARD_REACH_M = 8.0     # ... gets a W-beam reaching this far past it both ways (+ the turned-down terminals)
PIER_R_M = 0.5               # half size of a pier across (hero column 0.8 x 1.0 m, generic cylinder r 0.6 m)


def pier_guardrails(lin, net, piers, parts, report):
    """ADR 0117: W-beam between a ground carriageway and a viaduct pier standing closer than PIER_GUARD_GAP_M to its
    edge (Mapillary 177786140912399: W-beam in front of a pier of the Biezenstwa viaduct at the roundabout kerb).
    `piers` = (n, 2) pier axes: hero spec columns + the generic cylinders (roads.meshing.build_bridge_supports), so
    it runs after them, not in guardrails(). The edge is the outline of the ground asphalt (chains, junction plates and
    roundabout rings alike), the post line GUARDRAIL_OFFSET behind the kerb (closer when the pier leaves no room);
    runs are deduplicated against the rails built before. WORKING rule."""
    from scipy.spatial import cKDTree
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import substring, unary_union
    piers = np.asarray(piers, float).reshape(-1, 2)
    m = {}
    total, hits = 0.0, []
    built = getattr(net, "guardrail_built", None)
    if built is None:
        built = net.guardrail_built = []
    reach = PIER_GUARD_REACH_M + S.GUARDRAIL_TERMINAL_M
    tri, kerb = [], []
    for p in parts:
        if p.layer != "road" or not len(p.T):
            continue
        # ADR 0123: the truck apron of a roundabout is driven on too - the edge beside a pier on the centre island is
        # the inner kerb of the apron (Mapillary 177786140912399: W-beam right behind the island kerb), not the
        # asphalt 2.5 m further out (the run stood on the apron or was not built at all)
        if (p.mat.startswith("road_asphalt") or p.mat == "apron_sett") and not p.src.endswith(":vg"):
            tri.append(p.V[p.T])
        elif p.mat == "curb_concrete":
            kerb.append(p.V[:, :2])
    if len(piers) and tri:
        A = np.concatenate(tri)
        cen = A[:, :, :2].mean(1)
        ktree = cKDTree(np.concatenate(kerb)) if kerb else None
        for i, q in enumerate(piers):
            sel = np.hypot(cen[:, 0] - q[0], cen[:, 1] - q[1]) < PIER_GUARD_GAP_M + reach + 6.0
            if not sel.any():
                continue
            loc = A[sel]
            U = unary_union([Polygon(t[:, :2]).buffer(0.03) for t in loc]).buffer(-0.03)
            pq = Point(q)
            dq = float(U.distance(pq))
            if dq <= 0.0 or dq > PIER_GUARD_GAP_M:
                continue
            rings = []
            for g in getattr(U, "geoms", [U]):
                rings += [g.exterior] + list(g.interiors)
            ring = min(rings, key=lambda r: r.distance(pq))
            off = min(S.KERB_TOP_W + S.GUARDRAIL_OFFSET, dq - PIER_R_M - 0.35)
            if off < 0.3 or ring.length < 2 * reach + 2:
                continue
            # start the ring opposite the pier so the stretch beside it does not cross the seam
            C = np.asarray(ring.coords)[:-1]
            k0 = int(np.argmax(np.hypot(C[:, 0] - q[0], C[:, 1] - q[1])))
            line = LineString(np.vstack([C[k0:], C[:k0 + 1]]))
            s0 = line.project(pq)
            seg = substring(line, max(s0 - reach, 0.0), min(s0 + reach, line.length)).simplify(0.05)
            n = max(2, int(round(seg.length)) + 1)
            P = np.array([seg.interpolate(t).coords[0] for t in np.linspace(0.0, seg.length, n)])
            if len(P) < 2 * S.GUARDRAIL_TERMINAL_M + 6:
                continue
            d = np.gradient(P, axis=0)
            d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
            nrm = np.column_stack([-d[:, 1], d[:, 0]])
            j = int(np.argmin(np.hypot(P[:, 0] - q[0], P[:, 1] - q[1])))
            sg = 1.0 if float((q - P[j]) @ nrm[j]) > 0 else -1.0
            E = P + nrm * sg * off
            # foot height: nearest asphalt vertex + kerb (when a kerb runs along this edge)
            V3 = loc.reshape(-1, 3)
            _, kk = cKDTree(V3[:, :2]).query(P)
            z = V3[kk, 2]
            if ktree is not None:
                dk, _ = ktree.query(P)
                z = z + np.where(dk < 0.6, S.KERB_HEIGHT, -0.02)
            z = np.convolve(np.pad(z, 2, mode="edge"), np.ones(5) / 5, mode="valid")
            if sg > 0:                       # guardrail(): the road is on the LEFT of the post line
                E, z = E[::-1], z[::-1]
            n0 = len(built)
            _dedup_guardrail(lin, E, z, f"pier{i}:structure", built, m)
            got = sum(b_.length for b_ in built[n0:])
            total += got
            for b_ in built[n0:]:              # ADR 0144: QA list of every built run (tests/gis/test_guardrail_overlap.py)
                C_ = np.asarray(b_.coords)
                kz = np.argmin(np.hypot(E[None, :, 0] - C_[:, None, 0], E[None, :, 1] - C_[:, None, 1]), axis=1)
                report.setdefault("guardrail_runs", []).append({
                    "key": f"pier{i}:structure", "term": [True, True], "term_tall": [False, False],
                    "pts": [[round(float(a), 2), round(float(b), 2), round(float(z[k_]), 2), 0] for (a, b), k_ in zip(C_, kz)]})
            if got > 0:
                hits.append({"pier": [round(float(q[0]), 1), round(float(q[1]), 1)], "edge_m": round(dq, 2),
                             "offset_m": round(off, 2), "built_m": round(got, 1)})
    report.setdefault("guardrails_m", {})["pier"] = round(total)
    report["guardrails_pier"] = {"piers": int(len(piers)), "gap_m": PIER_GUARD_GAP_M, "built_m": round(total, 1),
                                 "runs": hits, **{k: int(v) for k, v in m.items()}}


def is_noise_wall(tags):
    """OSM barrier=wall + wall=noise_barrier (19 ways in tile C) is a noise barrier, not a plot fence."""
    return tags.get("barrier") == "noise_barrier" or (tags.get("barrier") == "wall" and tags.get("wall") == "noise_barrier")


# Noise-barrier styles (ADR 0069, Mapillary references p37/p38/p40 2018-2024, CC BY-SA, reference only; heights read off
# the photos against the 0.15 m kerb and the 2.5 m car, WORKING_VALUE):
#   solid    dark absorbing cassettes from a 0.5 m concrete plinth to the top (2018 photo at g3b_eye_s1482)
#   glazed   light concrete plinth to 0.6 m, dark cassette band to `band_m` (p38 1.0 m, p40 1.6 m), clear panels above,
#            green-grey steel posts every 4 m, a top rail (p38 / p40 2024)
NOISE_STYLES = {
    "solid": {"plinth_m": 0.5, "band_m": None, "post_mat": "noise_post", "panel": "noise_panel_dark"},
    "glazed": {"plinth_m": 0.6, "band_m": 1.0, "post_mat": "noise_post", "panel": "noise_panel_dark"},
}
NOISE_DEFAULT_STYLE = "solid"
NOISE_POST_W = 0.22
NOISE_DEDUP_M = 4.0          # an OSM way within this of a BDOT10k barrier is the same object (BDOT geometry kept)


def _noise_style_overrides(overrides, origin):
    """kind: noise_barrier_style -> [(Point zone (local), radius, style dict, id)], kind: noise_barrier -> lines."""
    zones, lines = [], []
    for o in overrides or []:
        if o.get("kind") == "noise_barrier_style":
            for z in o.get("zones", []):
                c = np.asarray(z["center_epsg2180"], float) - origin
                st = dict(NOISE_STYLES[z.get("style", NOISE_DEFAULT_STYLE)])
                if "band_m" in z:
                    st["band_m"] = float(z["band_m"])
                if "height_m" in z:                        # ADR 0127: authored barrier height inside the zone
                    st["height_m"] = float(z["height_m"])
                st["name"] = z.get("style", NOISE_DEFAULT_STYLE)
                zones.append((c, float(z.get("radius_m", 30.0)), st, o["id"]))
        elif o.get("kind") == "noise_barrier":
            P = np.asarray(o["line_epsg2180"], float) - origin
            lines.append((LineString(P), o.get("style", NOISE_DEFAULT_STYLE), float(o.get("height_m", S.NOISE_BARRIER_H)),
                          f"override:{o['id']}"))
    return zones, lines


def _noise_runs(P, zones, default):
    """Split the densified polyline P into runs of one style: (slice, style). Zones are circles; later zones win."""
    names = []
    for p in P:
        st = default
        for c, r, s, _ in zones:
            if np.hypot(*(p - c)) <= r:
                st = s
        names.append(st)
    runs, k = [], 0
    while k < len(P):
        kk = k
        while kk + 1 < len(P) and names[kk + 1] is names[k]:
            kk += 1
        runs.append((slice(k, min(kk + 2, len(P))), names[k]))      # overlap one vertex: no gap at the style joint
        k = kk + 1
    return [(sl, st) for sl, st in runs if sl.stop - sl.start >= 2]


def noise_wall(lin, P, Z, st, H, key):
    """One noise-barrier run along P (densified, Z = ground). Collision: one wall ribbon to the top."""
    zp = Z + st["plinth_m"]
    lin.slab("concrete_plinth", P, Z - 0.4, zp, 0.2, key)
    if st["band_m"] is None:                                   # solid absorbing cassettes to the top
        lin.slab(st["panel"], P, zp, Z + H, 0.12, key)
    else:
        zb = Z + max(st["band_m"], st["plinth_m"] + 0.2)
        lin.slab(st["panel"], P, zp, zb, 0.12, key)
        # clear panel, one double-sided sheet (alpha blended). Kamion/World Car Glass dust mask as on the viaduct
        # screens (roads.meshing): u = 0, v = 1 at the foot -> -0.25 at the top
        lin.ribbon("noise_glass", P, zb, Z + H, 0.0, key, both=True)
        for prt in lin.buf.parts[-2:]:
            k = len(prt.V) // 2
            prt.UV = np.column_stack([np.zeros(2 * k), np.concatenate([np.ones(k), np.full(k, -0.25)])])
        lin.slab(st["post_mat"], P, Z + H - 0.08, Z + H, 0.10, key + ":rail")        # top rail
        if Z is not None and H - (zb - Z).max() > 2.0:      # ADR 0125: panel joint rail at mid height of the glazing
            zm = (zb + Z + H) / 2                           # (frames read at distance where the clear sheet does not)
            lin.slab(st["post_mat"], P, zm - 0.04, zm + 0.04, 0.08, key + ":rail")
    lin.ribbon("collision_fence", P, Z - 0.2, Z + H, 0.0, key, both=False)
    lin.buf.parts[-1].layer = "collision"
    # ADR 0127: posts NOISE_POST_W wide (HEB 200 class; 0.16 m read as fence wire at 80 m on Low), WORKING_VALUE
    lin.posts(st["post_mat"], P, S.NOISE_BARRIER_POST, NOISE_POST_W, NOISE_POST_W, H + 0.1, src=key)


def noise_barriers(lin, src, origin, roads_poly, report, overrides=None, pl=None):
    """BDOT10k OT_OIKM_L + OSM barrier=wall/wall=noise_barrier (parts > NOISE_DEDUP_M from BDOT) + authored lines,
    styled by authored zones (kind: noise_barrier_style, Mapillary image ids as provenance), default `solid`."""
    L = {"bdot": 0.0, "osm": 0.0, "override": 0.0}
    by_style = {}
    cutter = roads_poly.buffer(0.2) if roads_poly is not None else None
    zones, extra = _noise_style_overrides(overrides, np.asarray(origin, float))
    default = dict(NOISE_STYLES[NOISE_DEFAULT_STYLE], name=NOISE_DEFAULT_STYLE)
    bdot = [LineString(np.asarray(f["geometry"]["coordinates"], float) - origin) for f in src["bdot10k"]["OT_OIKM_L"]]
    feats = [(ln, f"bdot:{f['id']}", "bdot", S.NOISE_BARRIER_H) for ln, f in zip(bdot, src["bdot10k"]["OT_OIKM_L"])]
    near_bdot = shapely.union_all([b.buffer(NOISE_DEDUP_M) for b in bdot]) if bdot else None
    for f in src["osm"]["ways"]:
        if not is_noise_wall(f["tags"]):
            continue
        ln = LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        for part in cut_by(ln, near_bdot):
            if part.length > 6.0:
                feats.append((part, f"osm:way/{f['osm_way']}:{f['part']}", "osm", S.NOISE_BARRIER_H))
    for ln, style, H, key in extra:
        feats.append((ln, key, "override", H))
    used_zones = set()
    walls = []
    for line, key, kind, H in feats:
        for part in cut_by(line, cutter):
            walls.append(part)
            P = lin.dens(part, 2.0)
            Z = lin.z(P)
            for sl, st in _noise_runs(P, zones, default):
                noise_wall(lin, P[sl], Z[sl], st, st.get("height_m", H), key)
                seg = float(np.sum(np.hypot(*np.diff(P[sl], axis=0).T)))
                by_style[st["name"]] = by_style.get(st["name"], 0.0) + seg
            for c, r, s, oid in zones:
                if part.distance(shapely.Point(c)) <= r:
                    used_zones.add(oid)
            L[kind] += part.length
    report["noise_barriers_m"] = round(sum(L.values()))
    report["noise_barriers"] = {"m_by_source": {k: round(v) for k, v in L.items()},
                                "m_by_style": {k: round(v) for k, v in by_style.items()},
                                "zones_stale": sorted({z[3] for z in zones} - used_zones)}
    if pl is not None:
        report["noise_barriers"]["signs_moved_off_wall"] = _signs_off_walls(pl, walls, roads_poly)


SIGN_WALL_CLEAR_M = 0.9     # sign post in front of a noise barrier, road side (map audit MA-007 / MA-021, WORKING_VALUE)


def _signs_off_walls(pl, walls, roads_poly):
    """Sign assemblies placed by rule before the barriers existed can stand in a barrier (map audit MA-007 / MA-021:
    the B-33 plate cut by the panels). Moves the whole assembly (same src) to the road side of the wall,
    SIGN_WALL_CLEAR_M in front of it, never onto the carriageway. Returns the moved assembly sources."""
    if not walls or roads_poly is None:
        return []
    tree = shapely.STRtree(walls)
    rb = roads_poly.boundary
    moved = {}
    for it in pl.items:
        if not it["p"].startswith("sign_post") or it["src"] in moved:
            continue
        q = shapely.Point(it["e"], it["n"])
        near = tree.query(q, predicate="dwithin", distance=SIGN_WALL_CLEAR_M)
        if not len(near):
            continue
        w = min((walls[i] for i in near), key=q.distance)
        on_w = np.array(w.interpolate(w.project(q)).coords[0])
        kerb = np.array(rb.interpolate(rb.project(shapely.Point(*on_w))).coords[0])
        to_road = kerb - on_w
        gap = float(np.hypot(*to_road))
        if gap < 1e-3:
            continue
        d = min(SIGN_WALL_CLEAR_M, max(0.0, gap - 0.5))
        target = on_w + to_road / gap * d
        moved[it["src"]] = target - np.array([it["e"], it["n"]])
    for it in pl.items:
        v = moved.get(it["src"])
        if v is None:
            continue
        e0, n0 = it["e"], it["n"]
        e1, n1 = e0 + v[0], n0 + v[1]
        dz = float(pl.zsurf(np.array([e1]), np.array([n1]))[0] - pl.zsurf(np.array([e0]), np.array([n0]))[0])
        it["e"], it["n"], it["z"] = round(float(e1), 3), round(float(n1), 3), round(it["z"] + dz, 3)
    return sorted(moved)


WIRE_HALF_W = 0.012          # m; conductor ~24 mm incl. sag ripple (WORKING_VALUE, AFL-6 70-120 mm2 class)


# Supports of BDOT10k power lines (OT_SULN_L). The line vertices are the angle points; BDOT / OSM poles (OT_BUWT_P,
# power=pole/tower) cover only part of them (tile C: 44 of 74 vertices without a pole within 10 m), so conductors hung
# in the air (REVIEW r4 W-H2). Every angle point gets a support unless a mapped one stands within SUPPORT_SNAP_M (the
# span then ends on that pole), and straight runs get intermediate supports every <= span max. WORKING_VALUE: typical
# MV overhead line spans 60-100 m on concrete poles, HV 110 kV 250-400 m on lattice towers (no source in repo).
SUPPORT_SNAP_M = {"power_pole": 10.0, "pylon": 15.0}
SPAN_MAX_M = {"power_pole": 80.0, "pylon": 350.0}


def _nearest_support(pl, q, r):
    best, bd = None, r * r
    for g in ("power_pole", "pylon"):
        for p in pl.pts.get(g, []):
            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
            if d < bd:
                best, bd = np.array([p[0], p[1]], float), d
    return best


def power_supports(pl, P, hv, key, roads_poly, report):
    """Support points of one line (E, N): angle points + intermediate supports, snapped to mapped poles; adds the
    missing supports as instances. Returns the support polyline."""
    proto = "pylon" if hv else "power_pole"
    span = SPAN_MAX_M[proto]
    pts = [P[0]]
    for a, b in zip(P, P[1:]):
        L = float(np.hypot(*(b - a)))
        k = max(1, int(math.ceil(L / span)))
        pts += [a + (b - a) * (i / k) for i in range(1, k + 1)]
    out = []
    for i, q in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        d = d / max(np.linalg.norm(d), 1e-9)
        snap = _nearest_support(pl, q, SUPPORT_SNAP_M[proto])
        if snap is not None:
            out.append(snap)
            for it in pl.items:                        # mapped pole: turn its cross-arm across the line
                if it["p"] in ("power_pole", "pylon") and abs(it["e"] - snap[0]) < 2e-3 and abs(it["n"] - snap[1]) < 2e-3:
                    it["yaw"] = round(float(yaw_of(d)), 4)
            continue
        if roads_poly is not None and roads_poly.contains(Point(float(q[0]), float(q[1]))):
            continue                                   # never on a carriageway: the span runs on to the next support
        pl.add(proto, q, yaw_of(d), src=f"rule:power_support:{key}", group=proto)   # arms (local x) across the line
        report["supports_added"] = report.get("supports_added", 0) + 1
        out.append(np.asarray(q, float))
    return np.array(out)


WIRE_SAG_RATIO = 0.015       # mid-span sag / span of a level span (WORKING_VALUE: MV / HV lines at ~15-20 C, no source)
WIRE_SAMPLE_M = 5.0          # max chord length of the sampled catenary (REVIEW r6 W-P0: <= 5 m, no zigzags)


def catenary_span(L, za, zb, sag_ratio=WIRE_SAG_RATIO, step=WIRE_SAMPLE_M):
    """Conductor between supports at heights za (x = 0) and zb (x = L): a catenary z = c (cosh((x - x0) / c) -
    cosh(x0 / c)) + za whose parameter c gives a level span the sag sag_ratio * L (c = L^2 / (8 sag), the parabola
    limit; exact enough for sag / span < 5 %) and whose vertex x0 makes it pass through zb (closed form). Sampled at
    equal arc length, every <= step m of conductor (chords <= step also on steep spans). Returns (t = x / L, z, dz/dx)."""
    sag = max(sag_ratio * L, 1e-3)
    c = L * L / (8.0 * sag)
    x0 = L / 2.0 - c * math.asinh((zb - za) / (2.0 * c * math.sinh(L / (2.0 * c))))
    s0 = math.sinh(-x0 / c)
    arc = c * (math.sinh((L - x0) / c) - s0)               # conductor length between the supports
    k = max(2, int(math.ceil(arc / step - 1e-9)))
    x = x0 + c * np.arcsinh(s0 + np.linspace(0.0, arc, k + 1) / c)
    x[0], x[-1] = 0.0, L
    z = za + c * (np.cosh((x - x0) / c) - math.cosh(x0 / c))
    z[-1] = zb                                   # exact end (float round-off only)
    return x / L, z, np.sinh((x - x0) / c)


def _max_turn_deg(xz):
    """Largest direction change (deg) between neighbouring segments of a polyline (n, 2|3)."""
    d = np.diff(np.asarray(xz, float), axis=0)
    if len(d) < 2:
        return 0.0
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return float(np.degrees(np.arccos(np.clip((d[1:] * d[:-1]).sum(1), -1.0, 1.0))).max())


def power_lines(lin, src, origin, report, pl=None, roads_poly=None):
    n = 0
    sup_rep = {}
    if roads_poly is not None:
        from shapely.prepared import prep
        roads_poly = prep(roads_poly.buffer(1.0))
    for f in src["bdot10k"]["OT_SULN_L"]:
        hv = "wysokiego" in (f["props"].get("rodzaj") or "")
        P = np.asarray(f["geometry"]["coordinates"], float) - origin
        if len(P) < 2:
            continue
        if pl is not None:
            P = power_supports(pl, P, hv, f["id"], roads_poly, sup_rep)
            if len(P) < 2:
                continue
        # attachment points (lateral offset, height above ground). HV (ADR 0127): the six phase conductors hang
        # under the arm tips of streetscape.props.pylon (three levels, both sides) + the earth wire on the peak;
        # the old three wires at 23 m, +-5 m met no arm of the tower. MV: three conductors on the pole cross-arm.
        if hv:
            from . import props as PR
            hang = [(sx * PR.PYLON_ARM_L, za - PR.PYLON_INSULATOR_M) for za in PR.PYLON_ARM_Z for sx in (-1.0, 1.0)]
            hang.append((0.0, 32.0))
        else:
            hang = [(o, 11.7) for o in (-0.8, 0.0, 0.8)]
        h = max(z for _, z in hang)
        for a, b in zip(P, P[1:]):
            L = float(np.hypot(*(b - a)))
            if L < 5:
                continue
            za, zb = lin.z(a[None])[0] + h, lin.z(b[None])[0] + h
            t, Z, dz = catenary_span(L, za, zb)
            Q = a + (b - a) * t[:, None]
            dvec = (b - a) / L
            nn = np.array([-dvec[1], dvec[0]])
            # analytic 3D tangent of the catenary per sample (engine ribbon, ADR 0022 / REVIEW r6 W-P0)
            tan = np.column_stack([np.repeat(dvec[None], len(t), 0), dz])
            tan /= np.linalg.norm(tan, axis=1, keepdims=True)
            turn = _max_turn_deg(np.column_stack([t * L, Z]))
            report["wire_max_turn_deg"] = round(max(report.get("wire_max_turn_deg", 0.0), turn), 3)
            report["wire_max_seg_m"] = round(max(report.get("wire_max_seg_m", 0.0),
                                                 float(np.max(np.hypot(np.diff(t * L), np.diff(Z))))), 3)
            for o, zh in hang:
                QQ = Q + nn * o
                Zw = Z - (h - zh)
                V = np.concatenate([np.column_stack([QQ, Zw - WIRE_HALF_W]), np.column_stack([QQ, Zw + WIRE_HALF_W])])
                m = len(QQ)
                T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
                # layer "wires": the engine re-expands each ribbon towards the camera to >= 1 px with coverage alpha
                # (Kamion/World Wire): UV0 = (side -1/+1, physical half width m), COLOR_0 = tangent * 0.5 + 0.5
                uv = np.column_stack([np.repeat([-1.0, 1.0], m), np.full(2 * m, WIRE_HALF_W)])
                col = np.concatenate([tan, tan]) * 0.5 + 0.5
                col = np.column_stack([col, np.ones(2 * m)])
                lin.buf.add("wires", "wire", V, uv, T, src=f"bdot:{f['id']}", COL=col)
        n += 1
    report["power_lines"] = n
    report["power_supports_added"] = sup_rep.get("supports_added", 0)
