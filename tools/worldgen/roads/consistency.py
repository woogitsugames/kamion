"""Road surface consistency QA (ADR 0074, owner bug 2026-11-10 "lane into island").

Checks the generated geometry, not the input data, so it catches every layer that can disagree with another one:

  marking_off_carriageway   a horizontal-marking triangle (lane / edge / centre line, P-8 arrow, P-10, P-13, P-14)
                            whose centroid does not lie on a carriageway surface (asphalt / concrete / paving road
                            material) or lies under a kerb, sidewalk, verge, island fill or yard;
  obstacle_in_lane          a lane band (lane centre +- (lane width / 2 - LANE_INSET_M)) of a chain ribbon covered by
                            a kerb, sidewalk, verge or island, or with no surface at all (hole = island / terrain);
  lane_blind_end            an approach lane that may go straight on (turn:lanes through / none / no tag) runs into
                            a kerb, island or terrain inside the junction before it reaches an outbound lane;
  arrow_no_exit             a P-8 arrow direction (turn:lanes) with no outbound arm in that direction;
  prop_on_carriageway       a ground-standing prop (lamp, sign post, signal pole / mast, power pole, pylon, bollard,
                            bus shelter, bench, bin, gantry footing) whose base lies on a carriageway;
  furniture_in_lane         a fence / guard rail / wall vertex standing inside a lane band;
  prop_through_deck         a ground-standing pole whose shaft pierces a carriageway above its base (viaduct deck);
  kerb_on_carriageway       a kerb top with carriageway under it and all around it (kerb across / along a lane).

Surfaces are looked up in 2D triangle indices (shapely STRtree) with a height window, so a road passing under a
viaduct is not confused with the deck. Every case carries local E/N, WGS84 lat/lon, the chain / junction id, the OSM
ways and whether it lies on the start route (gate3 segments G3-A / G3-B, both carriageways within ROUTE_BAND_M).
Written to Data/Regions/<id>/generated/road_consistency_qa.json by build_world.py; ratchet in
tests/gis/test_road_consistency.py.
"""

from __future__ import annotations

import math

import numpy as np
import shapely

from . import standards as S
from .markings import _lanes_continue, lane_layout

CARRIAGEWAY = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel"}
OBSTACLE = {"curb_concrete": "kerb", "sidewalk_paving": "sidewalk", "verge_grass": "verge_grass",
            "shoulder_gravel": "shoulder", "bridge_concrete": "bridge_kerb"}
DRIVABLE = ["carriageway", "yard", "apron"]     # a lane may run onto a flush yard or a roundabout apron
PAINT = ("lane", "centre", "P-4", "P-7b", "P-8", "P-10", "P-13", "P-14")
GROUND_PROPS = ("lamp_", "sign_post", "signal_pole", "signal_mast", "power_pole", "pylon", "bollard", "bus_shelter",
                "bench", "waste_bin", "gantry_footing")
LANE_INSET_M = 0.45        # lane band = centre +- (lane_w / 2 - inset): a 2.55 m truck in a 3.5 m lane has 0.47 m
STATION_M = 2.0            # lane band sampling along chains
DZ_M = 0.8                 # surface height window (bridges / underpasses are further apart)
KERB_RING_M = 0.30         # a kerb with carriageway all around it at this radius lies inside a carriageway
PROP_INSET_M = 0.20        # a pole base this far inside the carriageway edge is "on the road"
ROUTE_BAND_M = 30.0        # cases within this distance of the start route polyline (both carriageways) are on route
JUNCTION_THROUGH_DEG = 35.0


class SurfaceIndex:
    """2D triangle index of the ground surfaces with their material class and mean height."""

    def __init__(self, parts):
        polys, cls, zs = [], [], []
        for p in parts:
            if p.layer not in ("road", "bridge", "paved") or len(p.T) == 0:
                continue
            if p.mat in CARRIAGEWAY:
                k = "carriageway"
            elif p.mat in OBSTACLE:
                k = OBSTACLE[p.mat]
            elif p.layer == "paved":
                k = "yard"
            elif p.mat in ("apron_sett",):
                k = "apron"
            else:
                continue                                     # soffits, parapets, piers, barriers: not a top surface
            tri = p.V[p.T]                                   # (m, 3, 3)
            a2 = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                              - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
            keep = a2 > 1e-4                                 # vertical faces (kerb fronts, skirts) have no 2D area
            if not keep.any():
                continue
            tri = tri[keep]
            ring = np.concatenate([tri[:, :, :2], tri[:, :1, :2]], axis=1)
            polys.append(shapely.polygons(ring))
            cls += [k] * len(tri)
            zs.append(tri[:, :, 2].mean(1))
        self.polys = np.concatenate(polys)
        self.cls = np.array(cls)
        self.z = np.concatenate(zs)
        self.tree = shapely.STRtree(self.polys)

    def carriageway_levels(self, P):
        """Per point (E, N): heights of every carriageway surface over / under it (bridge decks included)."""
        P = np.asarray(P, float).reshape(-1, 3)
        out = [[] for _ in range(len(P))]
        if len(P):
            pi, ti = self.tree.query(shapely.points(P[:, :2]), predicate="intersects")
            for a, b in zip(pi.tolist(), ti.tolist()):
                if self.cls[b] == "carriageway":
                    out[a].append(float(self.z[b]))
        return out

    def on_carriageway(self, P):
        """Per point (E, N, U): a carriageway surface lies within DZ_M of it (whatever is drawn on top)."""
        P = np.asarray(P, float).reshape(-1, 3)
        out = np.zeros(len(P), bool)
        if len(P):
            pi, ti = self.tree.query(shapely.points(P[:, :2]), predicate="intersects")
            ok = (self.cls[ti] == "carriageway") & (np.abs(self.z[ti] - P[pi, 2]) < DZ_M)
            out[np.unique(pi[ok])] = True
        return out

    def classify(self, P):
        """Per point (E, N, U): 'carriageway', an obstacle class, or 'none' (no surface = island / terrain).
        An obstacle triangle covering the point wins over carriageway (it is drawn on top of it)."""
        P = np.asarray(P, float).reshape(-1, 3)
        out = np.full(len(P), "none", dtype=object)
        if not len(P):
            return out
        hit = self.tree.query(shapely.points(P[:, :2]), predicate="intersects")
        pi, ti = hit
        ok = np.abs(self.z[ti] - P[pi, 2]) < DZ_M
        pi, ti = pi[ok], ti[ok]
        has_cw = np.zeros(len(P), bool)
        obst = {}
        for a, b in zip(pi.tolist(), ti.tolist()):
            k = self.cls[b]
            if k == "carriageway":
                has_cw[a] = True
            elif k not in ("apron",):
                obst.setdefault(a, k)
        out[has_cw] = "carriageway"
        for a, k in obst.items():
            out[a] = k
        return out


def _route(region_id, pipeline):
    import json
    p = pipeline.REGIONS / region_id / "route_start.json"
    seg = pipeline.REGIONS / region_id / "gate3_segment.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text(encoding="utf-8"))
    P = np.asarray(r["points_en"], float)
    s = np.arange(len(P)) * float(r.get("step_m", 2.0))
    ranges = []
    if seg.exists():
        g = json.loads(seg.read_text(encoding="utf-8"))
        for v in (g.get("segments") or {}).values() if isinstance(g.get("segments"), dict) else (g.get("segments") or []):
            a, b = v.get("s0_m", v.get("s_start_m")), v.get("s1_m", v.get("s_end_m"))
            if a is not None and b is not None:
                ranges.append((float(a), float(b)))
    if not ranges:
        ranges = [(0.0, float(s[-1]))]
    keep = np.zeros(len(P), bool)
    for a, b in ranges:
        keep |= (s >= a) & (s <= b)
    return shapely.LineString(P).buffer(ROUTE_BAND_M), shapely.MultiPoint(P[keep]).buffer(ROUTE_BAND_M), ranges


def _osm_ways(c):
    out = []
    for e, _ in c.edges:
        w = str(e).split(":")[0].lstrip("w")
        if w.isdigit() and int(w) not in out:
            out.append(int(w))
    return out


class _Cases:
    def __init__(self, origin, route):
        from pyproj import Transformer
        self.tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
        self.origin = origin
        self.route = route
        self.items = []
        self._seen = set()

    def add(self, kind, xy, detail, chain=None, junction=None, osm_ways=None, cell=2.0):
        x, y = float(xy[0]), float(xy[1])
        key = (kind, chain or junction, int(x // cell), int(y // cell), detail.get("what"))
        if key in self._seen:
            return
        self._seen.add(key)
        lon, lat = self.tr.transform(x + self.origin[0], y + self.origin[1])
        on_route = False
        if self.route is not None:
            on_route = bool(self.route[1].contains(shapely.Point(x, y)))
        self.items.append({"kind": kind, "e": round(x, 2), "n": round(y, 2), "lat": round(lat, 7),
                           "lon": round(lon, 7), "chain": chain, "junction": junction,
                           "osm_ways": osm_ways or [], "on_route": on_route, **detail})


def _lane_bands(c, secs, s):
    """[(lane index left->right in travel dir, travel sign, lat centre, half band, turns)] at station s."""
    sec = c.section(s, secs)
    if sec.lanes < 1:
        return []
    hw = float(c.hw_at(s))
    dirn = int(c.dirn[c.idx(s)]) or 1
    _, _, cen = lane_layout(sec, hw, dirn)
    hb = max(0.3, sec.lane_w / 2 - LANE_INSET_M)
    out = []
    if sec.oneway:
        for i, lat in enumerate(cen["fwd"]):
            tl = sec.turn_fwd if dirn > 0 else (sec.turn_bwd or sec.turn_fwd)
            out.append((i, dirn, lat, hb, tl[i] if tl and len(tl) == len(cen["fwd"]) else None))
    else:
        for i, lat in enumerate(cen["fwd"]):
            tl = sec.turn_fwd
            out.append((i, 1, lat, hb, tl[i] if tl and len(tl) == len(cen["fwd"]) else None))
        for i, lat in enumerate(cen["bwd"]):
            tl = sec.turn_bwd
            out.append((i, -1, lat, hb, tl[i] if tl and len(tl) == len(cen["bwd"]) else None))
    return out


def _turns(tag):
    if not tag:
        return {"through"}
    t = {x for x in str(tag).split(";") if x and x != "none"}
    return t or {"through"}


def check(w, instances, region_id, pipeline, report_extra=None):
    secs = w.net.sec_list
    idx = SurfaceIndex(w.buf.parts)
    route = _route(region_id, pipeline)
    cases = _Cases(w.origin, route)
    chains = [c for c in w.net.chains if not c.meta.get("absorbed") and len(c.line.p) >= 2]
    stats = {"marking_tris": 0, "lane_samples": 0, "approach_lanes": 0, "props_checked": 0}

    # ---- 1. markings on something that is not carriageway
    for p in w.buf.parts:
        if p.layer != "markings" or len(p.T) == 0:
            continue
        kind = p.src.split("@")[0]
        if kind.split("-P-2a")[0] not in PAINT:
            continue                                         # yard stall lines, oil, patches, drains: not road paint
        cen = p.V[p.T].mean(1)
        cen[:, 2] -= S.MARKING_LIFT
        stats["marking_tris"] += len(cen)
        lab = idx.classify(cen)
        bad = np.nonzero(lab != "carriageway")[0]
        cid = p.src.split("@", 1)[1] if "@" in p.src else p.src
        c = next((x for x in chains if x.id == cid), None)
        for b in bad.tolist():
            cases.add("marking_off_carriageway", cen[b], {"what": kind, "surface": str(lab[b])}, chain=cid,
                      osm_ways=_osm_ways(c) if c else None, cell=3.0)

    # ---- 2. lane bands of chain ribbons
    lane_poly = []
    for c in chains:
        s0, s1 = c.t_a + 0.5, c.length - c.t_b - 0.5
        if s1 - s0 < 1.0:
            continue
        ss = np.arange(s0, s1 + 1e-6, STATION_M)
        P, meta = [], []
        for s in ss:
            lim = float(c.hw_at(s)) - 0.15
            for li, trav, lat, hb, tl in _lane_bands(c, secs, s):
                for off in (-hb, 0.0, hb):
                    if abs(lat + off) > lim:      # lane gain / drop taper: the lane is still forming, not an obstacle
                        stats["lane_samples_in_taper"] = stats.get("lane_samples_in_taper", 0) + 1
                        continue
                    q = c.line.offset_point(s, lat + off)
                    P.append([q[0], q[1], float(c.crossfall_z(s, lat + off))])
                    meta.append((s, li, trav))
        if not P:
            continue
        P = np.array(P)
        stats["lane_samples"] += len(P)
        lab = idx.classify(P)
        for b in np.nonzero(~np.isin(lab, DRIVABLE))[0].tolist():
            s, li, trav = meta[b]
            cases.add("obstacle_in_lane", P[b], {"what": str(lab[b]), "lane": li, "s": round(float(s), 1)},
                      chain=c.id, osm_ways=_osm_ways(c))
        # lane band polygons for furniture / prop checks
        for li_key in {(m[1], m[2]) for m in meta}:
            pts_l, pts_r = [], []
            for s in ss:
                for li, trav, lat, hb, tl in _lane_bands(c, secs, s):
                    if (li, trav) == li_key:
                        lim = float(c.hw_at(s)) - 0.15
                        pts_l.append(c.line.offset_point(s, min(lat + hb, lim)))
                        pts_r.append(c.line.offset_point(s, max(lat - hb, -lim)))
            if len(pts_l) >= 2:
                lane_poly.append((shapely.Polygon(np.vstack([pts_l, pts_r[::-1]])).buffer(0), c,
                                  float(np.mean([c.zc(s) for s in ss]))))

    # ---- 3. approach lanes through junction patches + arrows vs. arms
    for j in w.junctions:
        if j.roundabout:
            continue
        arms = list(enumerate(j.arms))
        for i, a in arms:
            if a.is_ring() or a.chain.meta.get("absorbed"):
                continue
            inb = a.inbound_dirn()
            if inb < 0:
                continue
            t = float(j.trims.get(i, 0.0))
            s_end = float(a.s(t + 0.6))
            c = a.chain
            d_in = -a.direction(t)                      # travel direction into the junction
            bands = [b for b in _lane_bands(c, secs, s_end) if b[1] == (1 if a.end == "b" else -1)]
            if not bands:
                continue
            # outbound arms and their heading change (left +)
            outs = []
            for k, b in arms:
                if k == i or b.inbound_dirn() > 0:
                    continue
                d_out = b.direction(float(j.trims.get(k, 0.0)))
                ang = math.degrees(math.atan2(d_in[0] * d_out[1] - d_in[1] * d_out[0], float(np.dot(d_in, d_out))))
                outs.append((ang, k, b))
            has = {"through": any(abs(x[0]) <= JUNCTION_THROUGH_DEG for x in outs),
                   "slight_left": any(5 <= x[0] <= 75 for x in outs), "slight_right": any(-75 <= x[0] <= -5 for x in outs),
                   "left": any(35 <= x[0] <= 160 for x in outs), "right": any(-160 <= x[0] <= -35 for x in outs)}
            passes = _lanes_continue(c, a.end, j, secs)     # same turn:lanes continue: arrows belong further on
            for li, trav, lat, hb, tl in bands:
                stats["approach_lanes"] += 1
                turns = _turns(tl)
                p0 = c.line.offset_point(s_end, lat)
                for tn in turns & set(has):
                    if not has[tn] and tl and not passes:
                        cases.add("arrow_no_exit", p0, {"what": tn, "lane": li, "turn_lanes": tl}, chain=c.id,
                                  junction=j.id, osm_ways=_osm_ways(c))
                if "through" not in turns or not has["through"]:
                    continue
                # straight on: march along the inbound direction until we are on an outbound ribbon past its trim
                th = [x for x in outs if abs(x[0]) <= JUNCTION_THROUGH_DEG]
                # the continuation of the same OSM way first (a side road running parallel is not "straight on")
                way_in = str(c.section(s_end, secs).edge_id).split(":")[0]
                same = [x for x in th
                        if str(x[2].chain.section(x[2].s(1.0), secs).edge_id).split(":")[0] == way_in]
                # otherwise only a road of the same kind straight ahead (a service road / living street meeting a
                # link at a shallow angle is not a lane that continues into it)
                hw_in = c.section(s_end, secs).highway
                same_kind = [x for x in th if x[2].chain.section(x[2].s(1.0), secs).highway == hw_in]
                if not (same or same_kind):
                    continue
                best = min(same or same_kind, key=lambda x: abs(x[0]))
                tgt, k_t = best[2], best[1]
                # diverge (lanes of the branches add up to the approach lanes): lanes are dealt out from the left,
                # as network.align_forks lays the branches out
                fan = sorted([x for x in outs if abs(x[0]) <= 60.0], key=lambda x: -x[0])
                fan_l = [[b for b in _lane_bands(x[2].chain, secs, float(x[2].s(float(j.trims.get(x[1], 0.0)) + 3.0)))
                          if b[1] == (1 if x[2].end == "a" else -1)] for x in fan]
                forced = None
                if len(fan) >= 2 and sum(len(f) for f in fan_l) == len(bands):
                    k = li
                    for x, fl in zip(fan, fan_l):
                        if k < len(fl):
                            tgt, k_t = x[2], x[1]
                            forced = sorted(fl, key=lambda b: b[0])[k][2]
                            break
                        k -= len(fl)
                tt = float(j.trims.get(k_t, 0.0))
                q_end = tgt.chain.line.point(tgt.s(tt + 3.0))
                dist = float(np.dot(q_end - p0, d_in))
                if dist <= 0 or dist > 120:
                    continue
                # target lateral: keep the same offset from the inbound centreline, bent towards the outbound arm
                d_out = tgt.direction(tt)
                n_in = np.array([-d_in[1], d_in[0]])
                n_out = np.array([-d_out[1], d_out[0]])
                lat_in = float(np.dot(p0 - c.line.point(s_end), n_in))
                c_out = tgt.chain.line.point(tgt.s(tt + 3.0))
                # outbound lane with the same index from the right edge (lanes keep to the right through a junction)
                ob = [b for b in _lane_bands(tgt.chain, secs, float(tgt.s(tt + 3.0)))
                      if b[1] == (1 if tgt.end == "a" else -1)]
                nl_in, nl_out = len(bands), len(ob)
                k_r = nl_in - 1 - li
                if forced is not None:
                    q1 = tgt.chain.line.offset_point(tgt.s(tt + 3.0), forced)
                elif nl_out and k_r < nl_out:
                    lat_o = sorted(ob, key=lambda b: b[0])[nl_out - 1 - k_r][2]
                    q1 = tgt.chain.line.offset_point(tgt.s(tt + 3.0), lat_o)
                else:
                    q1 = c_out + n_out * lat_in
                n = max(4, int(dist / 0.5))
                u = np.linspace(0.0, 1.0, n + 1)
                L = max(dist, 1.0)
                m0, m1 = d_in * L, d_out * L
                h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
                path = h00[:, None] * p0 + h10[:, None] * m0 + h01[:, None] * q1 + h11[:, None] * m1
                tang = np.gradient(path, axis=0)
                tang /= np.maximum(np.linalg.norm(tang, axis=1), 1e-9)[:, None]
                nrm = np.column_stack([-tang[:, 1], tang[:, 0]])
                z0, z1 = float(c.crossfall_z(s_end, lat)), float(tgt.chain.zc(tgt.s(tt + 3.0)))
                zz = z0 + (z1 - z0) * u
                hb2 = min(hb, 0.9)
                PP = np.concatenate([np.column_stack([path + nrm * o, zz]) for o in (-hb2, 0.0, hb2)])
                lab = idx.classify(PP)
                bad = np.nonzero(~np.isin(lab, DRIVABLE))[0]
                if len(bad):
                    b = int(bad[0])
                    cases.add("lane_blind_end", PP[b], {"what": str(lab[b]), "lane": li, "turn_lanes": tl,
                                                        "lanes_in": nl_in, "lanes_out": nl_out,
                                                        "to_chain": tgt.chain.id,
                                                        "dist_from_stop_m": round(float(u[b % len(u)] * dist), 1)},
                              chain=c.id, junction=j.id, osm_ways=_osm_ways(c), cell=6.0)

    # ---- 4. props standing on the carriageway, furniture inside lanes
    pts, names = [], []
    for it in instances:
        if it["p"].startswith(GROUND_PROPS):
            pts.append([it["e"], it["n"], it["z"]])
            names.append(it)
    if pts:
        P = np.array(pts, float)
        stats["props_checked"] = len(P)
        ring = [np.array([PROP_INSET_M, 0.0]), np.array([-PROP_INSET_M, 0.0]), np.array([0.0, PROP_INSET_M]),
                np.array([0.0, -PROP_INSET_M])]
        labs = [idx.classify(np.column_stack([P[:, :2] + o, P[:, 2]])) for o in ring]
        on = np.all(np.array([lb == "carriageway" for lb in labs]), axis=0)
        for b in np.nonzero(on)[0].tolist():
            it = names[b]
            cases.add("prop_on_carriageway", P[b], {"what": it["p"], "src": it.get("src")}, cell=0.5)
        # a pole whose shaft pierces a carriageway above its base (a lamp of the road below coming up through a
        # viaduct deck: owner 2026-11-10 "lamp in the middle of the lane"), ADR 0076
        ring5 = [np.array([0.0, 0.0])] + ring
        for b, it in enumerate(names):
            h = S.ground_prop_height(it["p"])
            lv = idx.carriageway_levels(np.column_stack([P[b, :2] + np.array(ring5), np.full(5, P[b, 2])]))
            hit = [z for zs in lv for z in zs if P[b, 2] + 0.5 < z < P[b, 2] + h]
            if hit:
                cases.add("prop_through_deck", P[b], {"what": it["p"], "src": it.get("src"),
                                                      "deck_dz_m": round(min(hit) - float(P[b, 2]), 2)}, cell=0.5)

    # ---- 5. kerbs lying inside a carriageway (owner 2026-11-10 "kerbs in the middle of the road"; MA-001 / MA-002):
    #         a kerb-top triangle with carriageway under it and all around it (ring of KERB_RING_M). A kerb at the
    #         edge of a ribbon / patch, or a narrow raised separator between two carriageways, has no carriageway
    #         on at least one side.
    ang = np.linspace(0.0, 2 * math.pi, 8, endpoint=False)
    ring8 = np.column_stack([np.cos(ang), np.sin(ang)]) * KERB_RING_M
    for p in w.buf.parts:
        if p.layer not in ("road", "bridge") or p.mat != "curb_concrete" or len(p.T) == 0:
            continue
        tri = p.V[p.T]
        a2 = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                          - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
        cen = tri[a2 > 1e-4].mean(1)
        if not len(cen):
            continue
        stats["kerb_tris"] = stats.get("kerb_tris", 0) + len(cen)
        inside = idx.on_carriageway(cen)
        for o in ring8:
            if not inside.any():
                break
            q = cen.copy()
            q[:, :2] += o
            inside &= idx.on_carriageway(q)
        owner = p.src.split(":L")[0].split(":R")[0]
        c = next((x for x in chains if x.id == owner), None)
        for b in np.nonzero(inside)[0].tolist():
            cases.add("kerb_on_carriageway", cen[b], {"what": "kerb", "src": p.src}, chain=c.id if c else None,
                      junction=owner if owner.startswith("j:") else None, osm_ways=_osm_ways(c) if c else None,
                      cell=4.0)

    if lane_poly:
        tree = shapely.STRtree([lp[0] for lp in lane_poly])
        V = []
        for p in w.buf.parts:
            if p.layer != "furniture" or len(p.V) == 0:
                continue
            V.append(p.V[::max(1, len(p.V) // 4000)])
        if V:
            V = np.concatenate(V)
            pi, li = tree.query(shapely.points(V[:, :2]), predicate="within")
            for a, b in zip(pi.tolist(), li.tolist()):
                poly, c, zc = lane_poly[b]
                s, _ = c.line.project(V[a, :2])
                if -0.3 < V[a, 2] - float(c.zc(s)) < 4.5:
                    cases.add("furniture_in_lane", V[a], {"what": "furniture"}, chain=c.id, osm_ways=_osm_ways(c),
                              cell=4.0)

    items = sorted(cases.items, key=lambda x: (not x["on_route"], x["kind"], x["e"], x["n"]))
    by_kind, on_route = {}, {}
    for x in items:
        by_kind[x["kind"]] = by_kind.get(x["kind"], 0) + 1
        if x["on_route"]:
            on_route[x["kind"]] = on_route.get(x["kind"], 0) + 1
    out = {"schema": "truck-sim-pl/road-consistency-qa/1", "region": region_id,
           "frame": "e, n = local metres (EPSG:2180 minus region origin); lat, lon = WGS84",
           "route_segments_s_m": route[2] if route else None, "route_band_m": ROUTE_BAND_M,
           "params": {"kerb_ring_m": KERB_RING_M, "lane_inset_m": LANE_INSET_M, "station_m": STATION_M, "dz_m": DZ_M,
                      "prop_inset_m": PROP_INSET_M, "through_deg": JUNCTION_THROUGH_DEG},
           "stats": stats, "count": len(items), "by_kind": dict(sorted(by_kind.items())),
           "on_route": dict(sorted(on_route.items())), "cases": items}
    if report_extra:
        out.update(report_extra)
    return out
