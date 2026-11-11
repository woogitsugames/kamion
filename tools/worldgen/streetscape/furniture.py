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
import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point

from roads import standards as S
from roads.network import MEDIAN_RURAL, RURAL, URBAN, side_params, side_extent

from . import facade_atlas as FA

# ADR 0102: visible foundations follow the render surface at the pole axis. The coarser collision surface is
# deliberately NOT a height reference for art: it can lie a metre below a kerb/embankment edge.
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
FOOT_R = {"lamp_arc_": 0.28, "lamp_old_concrete_": 0.12, "lamp_old_steel_": 0.20, "lamp_": 0.25,
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
            z.append(m if math.isfinite(m) else float(zt[k]))
        return float(z[0]), float(max(z) - min(z))

    def near(self, group, p, r):
        for q in self.pts.get(group, []):
            if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < r * r:
                return True
        return False

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
    deck = SurfaceTop(parts, layers=("bridge",))
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
                    p = c.line.offset_point(s, sgn * (hw + S.KERB_TOP_W + 0.6))
                pl.add(proto if z is None else f"lamp_{int(spec['h'])}m", p, yaw_of(face), z=z, src=f"rule:{c.id}",
                       group="lamp")
                n += 1
    report["lamps"] = {"osm": n0, "rule": n,
                       "by_family": {k: sum(1 for it in pl.items if it["p"] == k) for k in
                                     sorted({it["p"] for it in pl.items if it["p"].startswith("lamp_")})}}


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

    def posts(self, mat, P, spacing, w, d, h, zb=None, src=""):
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
        for q, z, ground, t in zip(Q, Z, self.z(Q), dd):
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


def panel_fence(lin, line, col, key, flexible=False):
    """ADR 0102: rigid, level bays step with the plot boundary; only tagged flexible mesh sags.

    Keep corners and place posts at every bay boundary. Concrete plinth follows the ground below each level bay,
    rather than a long sloping ribbon through the post centres. No extra materials or layers.
    """
    P = [np.asarray(line.coords[0], float)]
    for a, b in zip(np.asarray(line.coords)[:-1], np.asarray(line.coords)[1:]):
        n = max(1, int(math.ceil(np.linalg.norm(b - a) / S.FENCE_PANEL_W)))
        P.extend(a + (b - a) * k / n for k in range(1, n + 1))
    P = np.asarray(P)
    Z = lin.z(P)
    bases = np.maximum(Z[:-1], Z[1:])
    post_base = np.maximum(np.r_[bases[0], bases], np.r_[bases, bases[-1]])
    for i, base in enumerate(bases):
        Q = P[i:i + 2]
        low = Z[i:i + 2] - 0.2
        top = np.full(2, base + S.FENCE_PLINTH_H)
        lin.slab("concrete_plinth", Q, low, top, 0.05, key)
        if flexible:
            Q = np.array([Q[0], Q.mean(axis=0), Q[1]])
            bottom = np.full(3, base + S.FENCE_PLINTH_H)
            upper = base + S.FENCE_H - np.array([0, 0.045, 0])  # 4.5 cm, WORKING_VALUE
        else:
            bottom, upper = top, np.full(2, base + S.FENCE_H)
        lin.ribbon(f"{col}_mesh", Q, bottom, upper, 0, key, both=True, collision="collision_fence")
    lin.posts(col, P, None, 0.06, 0.04, S.FENCE_H + 0.05, zb=post_base, src=key)


def fences(lin, src, origin, roads_poly, report):
    n = {"panel_m": 0.0, "concrete_m": 0.0, "retaining_m": 0.0}
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
                col = ["fence_green", "fence_anthracite", "fence_galv"][_h(key) % 3]
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


def guardrail(lin, P, Z, key):
    """Steel W-beam on posts (top GUARDRAIL_H), Z = ground/surface height along P."""
    lin.posts("barrier_post", P, S.GUARDRAIL_POST_SPACING, 0.1, 0.05, S.GUARDRAIL_H - 0.05, zb=Z, src=key)
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    # W profile (two bulges toward the road side, +nrm): 5 points of the 0.31 m high beam
    prof = [(0.0, -0.31), (0.05, -0.24), (0.0, -0.155), (0.05, -0.07), (0.0, 0.0)]
    rows = []
    for o, dz in prof:
        rows.append(np.column_stack([P + nrm * (0.08 + o), Z + S.GUARDRAIL_H + dz]))
    n = len(P)
    V = np.concatenate(rows)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    UV = np.column_stack([np.tile(s, len(rows)), np.repeat(np.arange(len(rows)) * 0.08, n)])
    T = []
    for r in range(len(rows) - 1):
        a, b = r * n, (r + 1) * n
        T += [(a + k, a + k + 1, b + k + 1) for k in range(n - 1)] + [(a + k, b + k + 1, b + k) for k in range(n - 1)]
    T = np.array(T)
    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    lin.buf.add("furniture", "barrier_steel", V, UV, T[:, [0, 2, 1]], src=key)
    lin.buf.add("collision", "collision_steel", V, UV, np.concatenate([T, T[:, [0, 2, 1]]]), src=key)


def guardrails(lin, net, zground, report):
    m = {"bridge": 0.0, "median": 0.0, "embankment": 0.0}
    drops, runs = [], []
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
            kinds = np.array([side_params(c, side, s)[0] for s in ss])
            ext = np.array([side_extent(*side_params(c, side, s)) for s in ss])
            zg = c.crossfall_z(ss, sgn * hw)
            want = np.zeros(len(ss), int)            # 1 bridge, 2 median, 3 embankment
            off = np.zeros(len(ss))
            zb = zg.copy()
            # bridges: rail on the cap, 0.5 m behind the kerb
            want[br] = 1
            off[br] = hw[br] + S.KERB_TOP_W + 0.5
            zb[br] = zg[br] + S.BRIDGE_KERB_H
            med = (kinds == MEDIAN_RURAL) & ~br
            want[med] = 2
            off[med] = hw[med] + S.PAVED_SHOULDER_MEDIAN + S.GUARDRAIL_OFFSET
            zb[med] = zg[med] - 0.02
            rur = (kinds == RURAL) & ~br
            if rur.any():
                # embankment height = road edge minus the ground at the toe of the fill slope: berm 1 m +
                # slope 1:1.5 of a 2 m fill + 1 m = profile end + 5 m (the old probe at +2 m only ever saw
                # the berm, so the rule never fired); take the lowest of three probes (5, 7, 9 m)
                drop = np.full(len(ss), -1e9)            # zground = natural ground (NMT), not the conformed terrain
                for extra in (5.0, 7.0, 9.0):
                    P_out = c.line.offset_point(ss, sgn * (hw + ext + extra))
                    drop = np.maximum(drop, zg - zground(P_out[:, 0], P_out[:, 1]))
                drops.append(float(drop[rur].max()))
                emb = rur & (drop > S.GUARDRAIL_EMBANKMENT_H)
                # extend 12 m each way (approach), close small gaps
                from scipy import ndimage
                emb = ndimage.binary_dilation(emb, iterations=12) & rur
                want[emb] = 3
                off[emb] = hw[emb] + S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET
                zb[emb] = zg[emb] - S.CROSSFALL * S.PAVED_SHOULDER
            # runs
            k = 0
            while k < len(ss):
                if want[k] == 0:
                    k += 1
                    continue
                kk = k
                while kk + 1 < len(ss) and want[kk + 1] == want[k]:
                    kk += 1
                if kk - k >= 8:
                    sl = slice(k, kk + 1)
                    P = c.line.offset_point(ss[sl], sgn * off[sl])
                    if sgn > 0:                          # beam faces the road: road is on the right of travel
                        P, Zr = P[::-1], zb[sl][::-1]
                    else:
                        Zr = zb[sl]
                    guardrail(lin, P, Zr, f"{c.id}:{side}:{['', 'bridge', 'median', 'embankment'][want[k]]}")
                    if want[k] == 3:
                        runs.append({"chain": c.id, "side": side, "s": [round(float(ss[k]), 1), round(float(ss[kk]), 1)],
                                     "max_drop_m": round(float(drop[sl].max()), 2),
                                     "at": [round(float(v), 1) for v in c.line.offset_point(ss[(k + kk) // 2], 0.0)]})
                    m[["", "bridge", "median", "embankment"][want[k]]] += kk - k
                k = kk + 1
    report["guardrails_m"] = {k: round(v) for k, v in m.items()}
    d = np.array(drops) if drops else np.zeros(1)
    report["embankment_check"] = {"rural_sides": len(drops), "max_drop_m": round(float(d.max()), 2),
                                  "p95_drop_m": round(float(np.percentile(d, 95)), 2),
                                  "threshold_m": S.GUARDRAIL_EMBANKMENT_H, "runs": runs,
                                  "ground": "NMT (decks removed) at the profile end + 5 / 7 / 9 m"}


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
    lin.ribbon("collision_fence", P, Z - 0.2, Z + H, 0.0, key, both=False)
    lin.buf.parts[-1].layer = "collision"
    lin.posts(st["post_mat"], P, S.NOISE_BARRIER_POST, 0.16, 0.16, H + 0.1, src=key)


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
                noise_wall(lin, P[sl], Z[sl], st, H, key)
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
        h, sep = (23.0, 5.0) if hv else (11.7, 0.8)
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
            for o in (-sep, 0.0, sep):
                QQ = Q + nn * o
                V = np.concatenate([np.column_stack([QQ, Z - WIRE_HALF_W]), np.column_stack([QQ, Z + WIRE_HALF_W])])
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
